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

### Pacing a batch: `--pause` and `--pause-3d`

`--pause` (default 2 s) is the gap after each ordinary ComfyUI job - the
A-pose render and the background cut. `--pause-3d` (default 15 s) is the gap
after each *reconstruction* job, and between one NPC and the next.

They are separate because the two reconstructions are not the same weight as
a render: Hunyuan3D holds a 3072-token latent through a 256^3 octree decode
and SAM3DBody runs a DINOv3 backbone at batch 64, and ComfyUI reports a job
finished when its last node returns, not when the VRAM it held has been given
back. Queueing the next reconstruction into that window is what makes a long
unattended batch OOM on a machine that builds any single NPC without
complaint. The between-NPC gap covers the batch's tightest moment for the
same reason from the other side - the previous NPC's last act is a headless
Blender assembly, which competes with ComfyUI for the same machine.

Neither costs anything on a single-NPC run driven by hand: the between-NPC
sleep is skipped before the first NPC and for every skipped one. Lower them
on a machine with headroom (`--pause-3d 0`), raise them if a batch still
falls over.

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

Measured on a real reconstruction (Lucia Vos): 63.8 MB of deliverables per
NPC — `Shell.glb` 33.4 MB, `Print.stl` 29.2 MB, the four 768px turnaround
PNGs 1.2 MB combined — plus 22.7 MB of intermediates (`apose.png`,
`_shell.glb`, `_base.glb`) that this tool does **not** clean up, for
**86.5 MB per NPC**, or **139.4 MB with `--rig`** (the rigged GLB adds
another ~53 MB). Across a 160-NPC batch that is roughly **13.8 GB**, or
**22.3 GB with `--rig`** — plan storage against these figures, not the
spec's original 20-40 MB estimate, which measured only the deliverables and
undercounted them besides. No ignore rules are needed: NPC folders live under
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

This is a verdict on *this configuration* of proximity-based weight
transfer, not on the technique itself. The base→shell nearest-surface
correspondence measured on the real pair is a median gap of 0.090 m, a p90
of 0.159 m and a max of 0.244 m on a 1.571 m figure — the jacket sits 9 to
16 cm proud of the body it is draped over. `npc_rig.py`'s
`transfer_weights()` uses `vert_mapping='POLYINTERP_NEAREST'`, which maps
each shell vertex onto the nearest *face*, not the nearest *bone region*;
across a 9-16 cm gap near the armpit, a sleeve vertex's nearest base face is
routinely on the torso rather than the upper arm, which is the textbook
cause of exactly the shoulder tearing measured above. Untried knobs worth a
look before writing this approach off entirely: a normal-projected or
ray-projected vertex mapping (which would follow the surface outward from
the body rather than by raw Euclidean distance), or transferring onto a
shrink-wrapped proxy mesh pulled in against the body first so the gap that
is confusing `POLYINTERP_NEAREST` is mostly gone before the transfer runs.

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

### Measured: the checkpoint is being driven off-label

`Util_Image_to_Mesh_Hunyuan3D_v1.json` loads `hunyuan3d-dit-v2-mv_fp16` - the
**multi-view** checkpoint - and conditions it through the single-view
`Hunyuan3Dv2Conditioning` node. ComfyUI ships
`Hunyuan3Dv2ConditioningMultiView` (front / left / back / right) and it is
present on this install.

Swapping that one node, with the same `apose.png` and the same seed
(Jules Sokolova, 3958386534):

| | single-view node | multi-view node, `front` only |
|---|---|---|
| Components in the raw shell | **9** (two at 49.6% / 50.2% of area - torn halves) | **1** (100%) |
| Surface area surviving the 0.004 remesh | 0.4% | ~100% |
| `Shell.glb` | 159 KB | **31.9 MB** |
| `Print.stl` | 146 KB | **26.7 MB** |
| Turnarounds | blank frames with specks | a clean, closed, printable figure |

So the torn double-shell is the node mismatch, not the reconstruction being
hard. Fixing it is a one-node edit and does not need new views.

What one view still cannot do is complete the figure: the multi-view result is
a clean torso from shoulders to mid-thigh with **no head, no hands and no
feet**. The model is asking for the views it was trained on.

A second run that also square-padded the input in-graph (`EmptyImage` +
`ImageCompositeMasked`, 1024x1280 -> 1280x1280, so `crop: "center"` stops
trimming) came out **worse**, not better - 3.60 units of surface area against
6.99, and a sheared, lopsided torso. Hunyuan3D wants the subject filling the
frame; do not pad it. Ruled out, do not retry.

- **The single-view shell can fail completely, not just fragment the head.**
  Measured on Jules Sokolova (`run1/Pilots`): the Hunyuan3D shell came back as
  nine components whose two largest were 49.6% and 50.2% of the surface area -
  two overlapping, torn half-figures rather than one body - and no amount of
  cleanup downstream recovers a figure from that. The assembly now refuses it
  (see below) instead of shipping the crumbs.
- **Faces are not good.** Hunyuan3D fragments the head; at token and mini
  scale it reads acceptably, in close-up it does not. The real fix is
  multi-view conditioning, which needs consistent left/back/right views and is
  a design problem of its own. Note that
  `Util_Image_to_Mesh_Hunyuan3D_v1.json` already loads the **multi-view**
  checkpoint (`hunyuan3d-dit-v2-mv_fp16`) but drives it through the
  single-view `Hunyuan3Dv2Conditioning` node; ComfyUI ships
  `Hunyuan3Dv2ConditioningMultiView` (front / left / back / right) and it is
  present on this install.
- **A destroyed shell used to pass every check.** The manifold check asks
  whether every edge has two faces, and a scatter of small closed fragments
  answers yes. At `--voxel 0.004` the Jules shell went into the remesh with
  99,057 polygons over 0.836 units of area and came out with 1,468 polygons
  over 0.003 units - manifold, correctly bounded, and blank in every
  turnaround. `clean_shell()` now measures surface area across the remesh and
  raises when more than half of it is gone, and `assemble_npc.py` refuses a
  shell that is still in more than one appreciable part.
- **Turnaround lighting used to be fixed in world space**, so angles 180 and
  270 rendered as black silhouettes on transparent - half of every turnaround
  set was unreadable. The key and fill now swing with the camera.
- **The rigged character has no texture.** Texture baking wanted dependencies
  that cannot be built on this machine.
- **Rigging ships off, and was measured on exactly one NPC.** `--rig
  --bind transfer` yields a rig that reports as complete but tears visibly
  under a shoulder rotation; `--rig --bind auto` yields nothing. Neither is
  the fix — spec §7.1's armature-retargeting fallback is. See
  [Rigging](#rigging) above for the numbers and don't trust this section's
  confidence past the one NPC it was measured on.
