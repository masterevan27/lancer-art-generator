# generate-3d.py

Turns an NPC that already exists in `.generated-npcs.json` into a printable
mini, a cleaned 3D shell and a set of turnaround renders. It reads the
manifest, so the whole back catalogue is eligible, not just NPCs rolled after
this landed.

It is a separate command rather than a flag on `generate-npc.py` because
reconstruction is slow and failure-prone, and it must never be able to break
art generation. It imports `generate-npc.py` and reuses its functions; it does
not modify it, and it never writes to the manifest.

## Requirements

- A running ComfyUI (the same one `generate-npc.py` uses; probed on ports
  8000-8015). No custom node packs - every 3D node used ships with ComfyUI.
- Two models: `hunyuan3d-dit-v2-mv_fp16.safetensors` in `models/checkpoints`
  and `sam_3d_body_dinov3_bf16.safetensors` in `models/detection`.
- Blender 5.2 LTS. Set `LANCER_BLENDER` or pass `--blender` if it is not at
  the default install path.

## Usage

```
python generate-3d.py --filter Sokolova
python generate-3d.py --id npc-jules-sokolova-40213
python generate-3d.py --limit 5 --dry-run
python generate-3d.py --id npc-... --stage apose      # iterate on one stage
```

An NPC that already has a `3d/` folder is skipped unless `--overwrite`. One
NPC's failure is logged and the batch continues.

## The stages

| Stage | What it does | Output |
|---|---|---|
| `apose` | Re-renders the NPC's token in a forced A-pose with empty hands, and cuts out the background | `3d/apose.png` |
| `mesh` | That one image through Hunyuan3D (clothed shell) and SAM3DBody (rigged body) | `3d/_shell.glb`, `3d/_base.glb` |
| `assemble` | Headless Blender: rest-pose the base, clean the shell, align, export | the deliverables below |

### Why the A-pose re-render

Skin-weight transfer is proximity-based. The SAM3DBody base always comes out
in A-pose; the Hunyuan3D shell inherits the pose of its source image, which is
the token's rolled Stance - arms down. Transferring across that mismatch
smears the shoulders. Re-rendering the source in A-pose removes the mismatch by
construction rather than correcting for it afterwards.

The stance is `APOSE_STANCE` in `generate-3d.py`, not a bullet in the tables
file: no rolled NPC should ever get it. Both hands are emptied at the same
time, because an NPC holding a carbine in both hands cannot hold an A-pose -
the same rule `roll_npc()` already applies when it filters Stance against
occupied hands.

The consequence is that the 3D model's pose does not match the NPC's portrait.
For a rigged character that is correct; a static print mini is posed afterwards
in Blender.

### Why `--voxel` defaults to 0.004, not 0

`blender/assemble_npc.py` cleans the reconstructed shell and refuses to export
a mesh with non-manifold edges - one that would not print - unless `--voxel`
is raised above its own default of `0.0` to force a closed remesh. That
script's default is correct for *it*: it is a general-purpose tool with its
own tests, and 0 is the right value to leave untouched rather than never
running.

`generate-3d.py` passes `--voxel` through explicitly instead of leaving it at
that default, because the default fails on real data. Run by hand against a
real catalogue NPC's Stage 0/1 output: at `--voxel 0.0` the cleaned shell had
3 non-manifold edges and `assemble_npc.py` correctly exited 1 rather than
write an unprintable STL; at `--voxel 0.004` the same shell came out with 0
non-manifold edges and 0 components dropped, in a few seconds. The committed
test fixtures are clean enough to pass at 0, which is why the hermetic suite
alone would never have caught this - only a real reconstruction did. `0.004`
is `generate-3d.py`'s own default, passed on the command line like any other
option; `--voxel 0` (or any other value) still works if a particular mesh
wants it, and raising it further is the right move if a mesh still reports
non-manifold edges.

## Outputs

Written into `<NPC folder>/3d/`, beside the portrait and the token:

| File | What it is |
|---|---|
| `<Name> Shell.glb` | Clothed mesh, cleaned, unrigged |
| `<Name> Print.stl` | Manifold single body, scaled to 32 mm |
| `<Name> Turnaround_{000,090,180,270}.png` | Orbit renders |

A `## 3D` section is appended to the NPC's dossier listing them, along with
the two workflow files and the A-pose stance text - so the dossier keeps
recording everything needed to reproduce its own output. Re-running replaces
that section rather than stacking a second one.

Roughly 20-40 MB per NPC. No ignore rules are needed: NPC folders live under
`output/`, which is already ignored, or under ComfyUI's own output directory
outside the repo, and `3d/` inherits both.

## Known limits

- **Faces are not good.** Hunyuan3D fragments the head; at token and mini
  scale it reads acceptably, in close-up it does not. The real fix is
  multi-view conditioning, which needs consistent left/back/right views and is
  a design problem of its own.
- **The rigged character has no texture.** Texture baking wanted dependencies
  that cannot be built on this machine.
