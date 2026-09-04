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
| `<Name> Rigged.glb` | Clothed shell, bound to the base's 127-bone armature — only with `--rig`, and only if the bind fully succeeded (see [Rigging](#rigging)) |

A `## 3D` section is appended to the NPC's dossier listing them, along with
the two workflow files and the A-pose stance text - so the dossier keeps
recording everything needed to reproduce its own output. Re-running replaces
that section rather than stacking a second one.

Roughly 20-40 MB per NPC. No ignore rules are needed: NPC folders live under
`output/`, which is already ignored, or under ComfyUI's own output directory
outside the repo, and `3d/` inherits both.

## Rigging

Rigging is **off by default**. Pass `--rig` to also bind the cleaned shell to
the SAM3DBody base's 127-bone armature and export `<Name> Rigged.glb`. It
defaults off because it was measured on one real reconstruction and neither
available method survived contact with it.

### What was measured

ComfyUI became unavailable partway through this project, and the instance
that remains does not have the SAM3DBody model installed, so a broader sample
was not possible. **The evidence below is a single NPC** — Lucia Vos, a
127-bone SAM3DBody base against a 100k+ vertex Hunyuan3D shell (292,296
shell vertices in total) — measured once and independently reproduced by a
reviewer. Read the numbers as one real data point, not as a survey.

Two bind modes exist, chosen with `--bind`:

- **`transfer` (default when `--rig` is given)** copies the base's own 127
  vertex groups onto the shell by proximity, interpolated across the nearest
  face. On the Lucia Vos reconstruction this produced a *complete* rig: 0 of
  292,296 vertices unweighted, normalised weights, a real `Rigged.glb`
  written. But a controlled stress test — rotating one shoulder bone 30°,
  measuring edge stretch mesh-wide, with the base body's own native skin as
  the control — found severe tearing. The native rig held 0 of 55,311 edges
  beyond 2× their rest length (worst case 1.69×); the transferred shell had
  1,981 of 584,580 edges beyond 2×, 1,286 beyond 5×, and 1,024 beyond 10×,
  with the worst five between 64× and 72× — a 3 mm rest edge stretching to
  23–24 cm. The rig *completes* without error and *looks* fine in a bind-pose
  screenshot; only posing it exposes the tearing, which is exactly the
  failure mode this stage's own vertex-weight assertion cannot catch, because
  every vertex genuinely does carry a weight — just not a trustworthy one.
- **`auto`** solves for the bones directly with Blender's bone-heat
  weighting, ignoring the base's weights entirely. On the same
  reconstruction it failed completely: Blender's bone-heat solver errored and
  left 292,296 of 292,296 vertices unweighted. The stage's own assertion
  caught this correctly and refused to write a file — no `Rigged.glb`, no
  silent bad output — but it is not a usable fallback as it stands.

### The verdict

Neither bind mode is trustworthy for an unattended batch. `transfer` ships a
rig that looks complete by every check this stage runs and only reveals its
damage once someone poses it; `auto` does not ship a rig at all. That is why
`--rig` is opt-in rather than on-by-default: a print mini, a clean shell and
four turnarounds are unaffected by any of this and should not wait on it.

Spec §7.1 named a deeper fallback for exactly this outcome: retargeting an
existing armature to the shell — deforming a rig that is already known-good
to fit the new mesh — rather than transferring weights onto the shell from a
different mesh's rig. That is a design change, not a parameter, and needs its
own spec before it is built. It is the live next step for rigging in this
pipeline.

### Mechanics, for whoever picks this up

The shell is bound to the armature the SAM3DBody base brings with it. Before
writing the file the stage asserts that the armature has deform bones and
that every shell vertex carries a non-zero weight in at least one of them — a
necessary check, proven above to not be a sufficient one. A mesh that fails
this assertion is not written at all.

A rigging failure does not fail the NPC. The shell, the STL and the
turnarounds are already on disk and are unaffected by it — only the rigged
GLB depends on the bind. Passing `--rig` and having it fail costs nothing
else in the run; the summary line counts it as "without a rig" rather than
as a failure.

The pose the rig is in is the A-pose bind position, not the pose SAM3DBody
predicted. The prediction is unusable on this house style — the figure comes
out crouched with the fingers splayed — and was never the valuable part: a
rigged character wants a neutral bind pose, which is what the rest position
already is.

## Known limits

- **Faces are not good.** Hunyuan3D fragments the head; at token and mini
  scale it reads acceptably, in close-up it does not. The real fix is
  multi-view conditioning, which needs consistent left/back/right views and is
  a design problem of its own.
- **The rigged character has no texture.** Texture baking wanted dependencies
  that cannot be built on this machine.
- **Rigging ships off, and was measured on exactly one NPC.** `--rig
  --bind transfer` yields a rig that reports as complete but tears visibly
  under a shoulder rotation; `--rig --bind auto` yields nothing. Neither is
  the fix — spec §7.1's armature-retargeting fallback is. See
  [Rigging](#rigging) above for the numbers and don't trust this section's
  confidence past the one NPC it was measured on.
