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

You select an **NPC**, not an image file - the whole rebuild starts from a
manifest entry, and the image it reconstructs from is one this tool renders
for itself (see [Input](#input-one-image-and-this-tool-renders-it)).

```
# one NPC by manifest id - the unambiguous form
python generate-3d.py --id npc-jules-sokolova-40213

# by name, callsign or role category - a case-insensitive regex
python generate-3d.py --filter Sokolova
python generate-3d.py --filter Crew

# preview what a batch would build, without building any of it
python generate-3d.py --limit 5 --dry-run

# the whole catalogue except the pilots
python generate-3d.py --exclude Pilots

# rebuild an NPC that already has a 3d/ folder
python generate-3d.py --id npc-jules-sokolova-40213 --overwrite

# iterate: render the A-pose, look at it, then reconstruct from it
python generate-3d.py --id npc-... --stage apose
python generate-3d.py --id npc-... --stage mesh --stage assemble

# skip the render entirely: reconstruct from an A-pose you already have
python generate-3d.py --id npc-... --image apose.png
python generate-3d.py --id npc-... --image render.png --remove-bg

# opt in to rigging - off by default, and read Rigging below before you do
python generate-3d.py --id npc-... --rig

# a long unattended batch on a machine with VRAM headroom
python generate-3d.py --limit 40 --pause-3d 0
```

`--id` and `--stage` are both repeatable. An unknown `--id` is a hard error
rather than a run that quietly builds nothing.

`--filter` and `--exclude` match against the folder path, the name and the
callsign together, so `--filter Crew` selects a whole role category off the
path (`output/LancerNPCs/run3/Crew/...`) without the manifest entry needing
to store one.

An NPC that already has a non-empty `3d/` folder is skipped unless
`--overwrite`. That skip only applies when all three stages are running: a
narrowed `--stage` means you are deliberately iterating, so leftover output
from an earlier stage does not skip the NPC. One NPC's failure is logged and
the batch continues.

### Input: one image, rendered here or supplied by you

**One image, not several.** Stage `apose` renders the NPC's token again in a
forced A-pose, cuts the background, and squares the result; that single
square PNG is what conditions *both* reconstructions - Hunyuan3D for the
clothed shell and SAM3DBody for the rigged body. `--image` puts your own
image in that one slot instead.

There is no way to hand it several images, and no evidence that doing so
would help: four perfectly registered orthographic views produced exactly the
same result as one (probe A against probe F under
[Known limits](#known-limits)). The reason that comparison proved nothing is
that both were being clipped in-graph by a node that has since been removed -
so multi-view input is **untested**, not ruled out.

#### Specifying a specific image: `--image`

`--image PATH` reconstructs from an A-pose you already have instead of
rendering one. Nothing is generated - no prompt, no seed, no token render -
so this is also the fastest way in: one already-cut-out PNG straight to a
finished GLB and STL.

```
# an A-pose that already has its background removed
python generate-3d.py --id npc-... --image path/to/apose.png

# one that still has a background - cut it out first, through --rmbg
python generate-3d.py --id npc-... --image path/to/render.png --remove-bg
```

The image is **copied** to `<NPC folder>/3d/apose.png`; your file is not
touched. Copying rather than reading it in place is deliberate - everything
downstream (`apose_square.png` beside it, the already-has-output skip, the
dossier's 3D section) treats `3d/` as the record of what the reconstruction
was built from, and a path that only ever existed in one shell history is not
that record.

Four things follow from that, all of them checked before any job is queued:

- **It implies skipping stage `apose`.** The default becomes `mesh` and
  `assemble`. Naming `--stage apose` alongside `--image` is refused: one
  supplies the A-pose, the other renders one. A narrower `--stage mesh` is
  still honoured if you want to stop before assembly.
- **It only ever means one NPC.** One image is one person. If the selection
  resolves to more than one, the run is refused rather than giving forty NPCs
  the same body - narrow it with `--id`.
- **It will not clobber a render you already have.** An existing
  `3d/apose.png` stops the run unless you pass `--overwrite`.
- **A fully opaque image is refused**, naming `--remove-bg`. An image with no
  transparent pixel anywhere still has its background, and that failure is
  otherwise silent: the mesh comes back looking like a successful run with a
  flat slab standing behind the figure.

`--remove-bg` uploads your image, runs the same background-removal workflow
stage `apose` uses (`--rmbg`), and lands *that* result as `apose.png`. It is
allowed on an already-cut-out image too, for when you do not trust the alpha
you have. Without it, no ComfyUI job runs before the mesh stage at all.

You can still do it by hand - the stages hand work to each other as plain
files, so putting your own PNG at `<NPC folder>/3d/apose.png` and running
`--stage mesh --stage assemble` works exactly as it always did, with none of
the checks above.

Match what the pipeline expects of that file:

- **8-bit RGBA, non-interlaced.** `square_apose()` reads and writes PNG by
  hand (spec 2.2 - no dependency needing a compiler, and Pillow is not
  installed), so that one shape is all the codec understands. Anything else
  raises `is not 8-bit RGBA non-interlaced` rather than being converted.
- **A real alpha cutout, and no background of your own.** The subject's alpha
  bounds are what the square gets built around. Do not pre-pad the image or
  leave a backdrop in it - a seam between your backdrop and the added margin
  is a rectangle, and Hunyuan3D reconstructs one as a flat slab standing
  behind the figure. Give it the figure on transparency and let
  `square_apose()` rebuild the whole canvas.
- **A full standing figure**, ideally in an A-pose with empty hands. The pose
  is not cosmetic - the weight transfer is proximity-based, and a pose
  mismatch between shell and base smears the shoulders. See
  [Why the A-pose re-render](#why-the-a-pose-re-render).

What lands beside it is `3d/apose_square.png`: the squared, recomposited
image the reconstruction actually saw. It is the first thing worth looking at
when a shell comes out wrong.

### Pacing a batch: `--pause` and `--pause-3d`

`--pause` (default 2 s) is the gap after each ordinary ComfyUI job - the
A-pose render and the background cut. `--pause-3d` (default 15 s) is the gap
after each *reconstruction* job, and between one NPC and the next.

They are separate because the two reconstructions are not the same weight as
a render: Hunyuan3D holds a 3072-token latent through a 384^3 octree decode
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
| — | `--image` replaces this stage with an A-pose you supply, cutting it out first only if `--remove-bg` | `3d/apose.png` |
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

### Why the A-pose is squared before it is uploaded

`CLIPVisionEncode` uses `crop: "center"`, which scales the short side to the
vision tower's resolution and centre-crops the long one. `apose.png` is
1024x1280 with the figure filling y 13..1265, so the crop kept rows 128..1151
and threw away **115 pixels off the top of the subject and 113 off the bottom**
- 9% at each end, about six inches of a five-foot-nine figure.

The model reconstructed exactly what it was shown. The helmet came back sliced
flat across the crown, and the trouser legs ended in flat stumps with no boots
at all - both clean planar cuts, which is the signature.

`square_apose()` in `generate-3d.py` crops to the subject's alpha bounds,
composites it over a uniform backdrop and centres it on a square with 6%
margin, and Stage 1 uploads that instead of the raw A-pose. `crop: "center"`
then has nothing to remove. The squared image is kept on disk as
`3d/apose_square.png` - it is what the reconstruction actually saw, and the
first thing worth looking at when a shell comes out wrong.

Two details are load-bearing:

- **The whole canvas is rebuilt, not just the padding.** A first attempt padded
  the 1024x1280 out to a square and left the source's own faintly textured
  backdrop in the middle. The seam between the two is a rectangle, and
  Hunyuan3D reconstructed it as **a flat slab standing behind the figure**.
  rmbg has already produced an exact alpha cutout, so the subject is
  composited over one flat colour everywhere and no edge remains to be
  mistaken for geometry.
- **The crop is tight to the SUBJECT, so it happens in Python.** Core ComfyUI
  can pad to a fixed size (`EmptyImage` + `ImageCompositeMasked`) but cannot
  measure a mask's bounds, and spec 2.1 rules out a custom node pack. PNG is
  read and written by hand for the same reason spec 2.2 gives - no dependency
  that needs a compiler, and Pillow is not installed. rmbg output is always
  8-bit RGBA and never interlaced, so that one shape is all the codec
  understands; anything else raises.

There is a real cost. Showing a whole standing figure inside a square leaves
the subject at ~54% of the frame width where the uncropped 4:5 gave it 66%, so
the model has less to work with and the surface comes back thinner and more
open (1,355 boundary edges against 555). That is what `octree_resolution` and
`--voxel` below are tuned around, and it is plainly the better trade: a
complete figure with a softer surface beats a detailed torso with no head.

### `octree_resolution` is the detail lever, and 384 is its ceiling here

`VAEDecodeHunyuan3D.octree_resolution` is the SDF grid the mesh is extracted
from, and it - not the input image's pixel count - is what controls geometric
detail. Upscaling the A-pose does nothing: `CLIPVisionEncode` resizes to the
vision tower's native resolution first and the extra pixels are discarded.

Measured on the squared Jules A-pose:

| `octree_resolution` | result |
|---|---|
| 256 (was the default) | 30,083 triangles, 44 s |
| **384** | **119,921 triangles, 73 s** |
| 512 | **OOM** - `VoxelToMesh` tried to allocate 25.9 GB |

384 ships. The allocation goes as the cube of the resolution, so 512 is not
reachable on this machine and probably not on any machine this project will
run on.

### Scale: the NPC's own height, not the estimate of it

SAM3DBody infers metric height from one image with no scale reference in it,
and it guesses low. On Jules Sokolova it returned **1.5065 m** — 4'11" — for
an NPC whose rolled `## Height` reads *"a solid five foot nine or so"*, which
is **1.753 m**. A 25 cm error, and an invisible one: the estimate is
self-consistent, so the rig, the shell and the turnarounds all agreed with
each other and all described the wrong person.

`generate-3d.py` now reads the height out of the NPC's own Height bullet and
passes it as `--real-height-m`. The **base** is what gets rescaled, before the
shell is touched, so the frame the shell is fitted and aligned to is already
the right size and every metre after that is a real metre. The armature
carries the scale — the glTF importer parents a skinned mesh to its armature —
which keeps base and shell in the correspondence a weight transfer needs.

The bullet is **parsed**, not looked up in a table of the twelve current ones.
A manifest entry stores the bullet as it was when rolled, and this tool's whole
premise is that the back catalogue is eligible, so a since-reworded bullet must
not quietly stop resolving. Every bullet in both Height tables states its
height in words, including the hedges — *"just a few inches under six feet"* is
5'9", *"close to six and a half feet"* is 6'5". A bullet that names no number
at all (`of average height`, the legacy backfill) falls back to the estimate
with a warning rather than failing the NPC over a refinement.
`test_every_height_bullet_in_the_tables_parses` fails loudly if a bullet stops
resolving.

### The mini scales with the character

`--print-height-mm` (32 mm) is now the height of a **nominal** figure,
`--nominal-height-m` (1.8288 m, six feet). Each mini is scaled in proportion to
its own character, so Jules at 5'9" prints **30.67 mm** and someone at 6'5"
prints 35.7 mm. A 5'0" pilot and a 6'6" trooper used to come off the plate
identical, which is right for a mini printed alone and wrong for the squad this
catalogue exists to produce.

Without `--real-height-m` the old behaviour stands: exactly `--print-height-mm`,
every time. That is deliberate — with no known height the only alternative is
to scale by the estimator's noise, which is worse than uniform.

### Why `--voxel` defaults to 0.013, and why lowering it is the wrong move

`--voxel` applies to the **printable copy only**. The GLB and the turnarounds
keep the full ~162,000-face detail mesh; only the STL is remeshed, because
only the print needs a closed single body and the remesh is what costs the
detail (162,058 faces in, 39,488 out at 0.010; roughly 27,000 at the 0.013
that now ships).

It is in real metres. `clean_shell()` fits the shell to the base's height
before anything measures a distance, so `--weld` and `--voxel` both mean what
they say. They did not always: the fit used to happen *after* the clean, and
Hunyuan3D normalises to roughly two units for a 1.5 m person, so both numbers
were quietly a third smaller than documented.

`assemble_npc.py`'s own default of `0.0` is left alone - it is a
general-purpose tool with its own tests - but it refuses to write an STL from
a real reconstruction, which is never closed on arrival. `generate-3d.py`
passes a working value explicitly. Measured on a real catalogue shell (Jules
Sokolova), as the fraction of the detail mesh's surface area surviving:

| `--voxel` | area kept | print faces |
|---|---|---|
| 0.004 | 32.2% | — |
| 0.008 | 38.9% | 48,734 |
| **0.013** | **~67%** | **~27,000** |
| 0.030 | 60.1% | 6,350 |

A **finer** voxel is worse, not better, and the cliff is sheer. An earlier
revision defaulted to 0.010 on the strength of a 92.7% reading; that was taken
against the pre-squaring shell, which was denser and much less open, and it
does not survive the squared one.
Blender's voxel remesh converts through an OpenVDB volume whose narrow band is
a fixed number of *voxels*, so its real width shrinks with the voxel size; on
a surface that still has open boundary, a band too thin to bridge the holes
lets the volume leak and returns a scatter of small closed fragments. That
result is manifold and correctly bounded and is not a figure. So when a shell
comes back destroyed or non-manifold, **raise** `--voxel`. 0.013 ships rather
than the finer 0.008 to keep a step of clearance from the cliff; ~27,000 faces
is already far more than a 32 mm mini can resolve.

`npc_mesh.printable_copy()` measures surface area across the remesh and
refuses anything that loses more than half of it, so this failure is loud
instead of arriving as four blank PNGs.

## Outputs

Written into `<NPC folder>/3d/`, beside the portrait and the token:

| File | What it is |
|---|---|
| `<Name> Shell.glb` | Clothed mesh, cleaned, unrigged - the full-detail one |
| `<Name> Print.stl` | Manifold single body, voxel-remeshed, scaled to 32 mm |
| `<Name> Turnaround_{000,090,180,270}.png` | Orbit renders |
| `<Name> Rigged.glb` | Clothed shell, bound to the base's 127-bone armature — only with `--rig`, and only if the bind fully succeeded (see [Rigging](#rigging)) |

A `## 3D` section is appended to the NPC's dossier listing them, along with
the two workflow files and the A-pose stance text - so the dossier keeps
recording everything needed to reproduce its own output. Re-running replaces
that section rather than stacking a second one.

Measured on Jules Sokolova: `Shell.glb` 13.8 MB (162,056 faces), `Print.stl`
4.0 MB (39,488 faces), the four 640px turnarounds 0.8 MB combined — about
**19 MB of deliverables**, plus ~22 MB of intermediates (`apose.png`,
`_shell.glb`, `_base.glb`) this tool does **not** clean up, for roughly
**41 MB per NPC** or **6.6 GB across a 160-NPC batch**. The STL there was
remeshed at `--voxel` 0.010; the default has since moved to 0.013, which is a
coarser print mesh (~27,000 faces), so treat these as a ceiling rather than
as the current figure.

An earlier revision of this section quoted 86.5 MB per NPC and 13.8 GB per
batch, measured on Lucia Vos before the `RemeshMesh` clip was found. Those
numbers described a `Shell.glb` and an STL that were the *same* remeshed mesh;
splitting them and dropping the in-graph remesh changed both. No ignore rules
are needed: NPC folders live under
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

### Measured: `RemeshMesh` was clipping every reconstruction to a half-unit box

This was the root cause of everything below it, and it took two phases of
chasing symptoms to find. Straight off `VoxelToMesh` a real shell spanned
y −0.978..0.986 — a whole figure, head and hands and feet. After `RemeshMesh`
it spanned exactly y −0.503..0.504, flat-cut at both ends. The head, the
forearms and everything below mid-thigh were being sliced off in-graph.

Nine reconstructions of the same NPC, one variable at a time, all with the
same seed (3958386534):

| Probe | Setup | Result |
|---|---|---|
| A | four perfectly registered orthographic views | torso, y ±0.503 |
| C | front + back only (no left/right ambiguity) | torso, y ±0.504 |
| F | single-view conditioning node | torso, y ±0.50 |
| G | `CLIPVisionEncode crop: "none"` | torso, y ±0.50 |
| **H** | **`RemeshMesh` bypassed, one view** | **whole figure, y −0.978..0.986** |

`RemeshMesh` is out of the graph. `DecimateMesh` now takes `VoxelToMesh`
directly. The speck dropping it was there for (`drop_small_components: 0.02`,
spec §2.3) happens in `npc_mesh.drop_small_components()` instead, by surface
area — 895 specks off one real shell, one component left, 91.5% of the
vertices retained. If the node is ever reinstated, prove it does not clip
first: `test_nothing_remeshes_between_the_voxels_and_the_save` guards it.

### Measured: the checkpoint was being driven off-label

`Util_Image_to_Mesh_Hunyuan3D_v1.json` loads `hunyuan3d-dit-v2-mv_fp16` — the
**multi-view** checkpoint — and used to condition it through the single-view
`Hunyuan3Dv2Conditioning` node. It now uses
`Hunyuan3Dv2ConditioningMultiView` with `front` alone. Same image, same seed:

| | single-view node | multi-view node, `front` only |
|---|---|---|
| Components in the raw shell | **9** (two at 49.6% / 50.2% of area — torn halves) | **1** (100%) |
| Surface area surviving the remesh | 0.4% | ~100% |

This is a real improvement and it stays, but note what it is *not*: with
`RemeshMesh` still in the graph both variants were clipped to a torso, so the
node swap fixed the tearing and not the truncation. The two are independent.

### Not measured: whether extra views would help

Four registered views produced exactly the same clipped torso as one, so this
project has **no evidence either way** on multi-view input. The obvious next
experiment — Qwen-Image-Edit 2509 is installed, with the full UNET / text
encoder / VAE stack and `TextEncodeQwenImageEditPlus` taking three reference
images — is worth doing only after the single-view pipeline has been measured
across several NPCs, since the reason for wanting it has gone away.

An earlier revision of this file claimed square-padding the input was "ruled
out, do not retry", on the strength of one padded run coming out worse than
one unpadded run. Both runs were clipped by `RemeshMesh`, so the comparison
measured nothing. It is **untested**, not ruled out.

### Fixed along the way

- **A destroyed shell used to pass every check.** The manifold check asks
  whether every edge has two faces, and a scatter of small closed fragments
  answers yes: 99,057 polygons over 0.836 units of area went into a remesh and
  1,468 polygons over 0.003 units came out, manifold, correctly bounded, and
  blank in every turnaround. `printable_copy()` now measures surface area
  across the remesh and refuses anything that loses more than half of it.
- **`keep_largest_component` deleted half of every torn shell**, silently —
  50.4% of the surface area on the Jules reconstruction. It drops specks by
  area now, and the assembly refuses a print mesh still in more than one
  appreciable part rather than resolving it by deletion.
- **Turnaround lighting was fixed in world space**, so angles 180 and 270
  rendered as black silhouettes on transparent — half of every turnaround set
  was unreadable. The key and fill swing with the camera now.
- **`frame_camera` aimed at the object origin**, not the bounding-box centre,
  so a mesh whose origin was not at its centre rendered cropped and shoved
  against the edge of frame.

### Still true

- **Faces are soft.** Hunyuan3D does not resolve a head well. It is present,
  with hands and feet, now that nothing clips it — but at close range it
  reads as a blob. Multi-view conditioning is the plausible fix and is
  untested; see above.
- **The rigged character has no texture.** Texture baking wanted dependencies
  that cannot be built on this machine.
- **Rigging ships off, and was measured on exactly one NPC.** `--rig
  --bind transfer` yields a rig that reports as complete but tears visibly
  under a shoulder rotation; `--rig --bind auto` yields nothing. Neither is
  the fix — spec §7.1's armature-retargeting fallback is. See
  [Rigging](#rigging) above for the numbers and don't trust this section's
  confidence past the one NPC it was measured on.
