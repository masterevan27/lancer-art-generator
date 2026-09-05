# Texturing the reconstruction: the reference image's own colours on the mesh

> **Status:** designed 2026-09-05, not yet implemented. §2 is evidence gathered
> on this machine on 2026-09-05 against the live ComfyUI on `127.0.0.1:8000`
> and against a real catalogue reconstruction (Jules Sokolova); it is separated
> from intent on purpose. §4.2 is the one assumption the evidence does *not*
> settle, it is cheap to settle, and §8.1 exists to settle it before anything
> else is built. §7.2 is a quality compromise accepted deliberately for v1.

## 1. Problem

`generate-3d.py` turns an NPC into a shell GLB, a printable STL and four
turnaround renders. Every one of them is **grey**. There is no colour anywhere
in the pipeline: `grep -i 'material\|texture\|color'` across all four
`blender/*.py` modules returns zero hits, and `docs/generate-3d.md` says so
outright under *Still true* — *"The rigged character has no texture. Texture
baking wanted dependencies that cannot be built on this machine."*

The information is not missing. Every reconstruction is built from
`3d/apose_square.png`, a 1323x1323 render of that exact character with their
rolled skin, hair, eyes, outfit, headgear and glow colour already resolved and
painted. The pipeline reads that image for geometry and throws its colour away.

This matters more than "the model would look nicer". The reference carries a
large part of its detail **as paint, not as form** — unit patches, a stencilled
number, a hazard triangle, a belt, boot laces, wear and grime. Geometry
reconstruction cannot recover those at any resolution, and does not need to:
projecting the colour back puts them on the model directly. So this is also a
partial answer to the separate question of lost detail, which is why it is
being done first.

### Goals

- The **front** of the model carries the reference image's own pixels, not an
  interpretation of them.
- The **back** carries something plausible and stylistically consistent.
- Works on the **existing back catalogue** without rebuilding geometry: an NPC
  with a `3d/` folder from last week can be textured with one stage.
- A texture failure never damages the untextured deliverables that ship today.
- No new Python dependency. The system interpreter has none and gets none
  (§2.4).

### Non-goals

- **Replacing the geometry generator.** Trellis 2 is a live candidate for the
  *detail* problem and is out of scope here; see §3.1 for why it is the wrong
  tool for *this* problem.
- **Correct colour inside concavities.** Accepted limit for v1, §7.2.
- **A textured STL.** A print has no colour; `Print.stl` is unchanged.
- **Faces of portrait quality.** Projection puts the reference's face pixels on
  a soft mesh. It improves the read considerably and does not fix the geometry.

## 2. What was established

Evidence, not intent. Recorded so the next person does not repeat it.

### 2.1 The native texture nodes exist; the models for them do not

`GET /object_info` on the live ComfyUI returns 2076 node classes, including a
complete texture path — `UnwrapMesh`, `BakeTextureFromVoxel`,
`ApplyTextureToMesh`, `PaintMesh`, `MeshTextureToImage`, `RenderUVAtlas` — and
the full **Trellis 2** stack (`Trellis2Conditioning`, `Trellis2ShapeStage`,
`Trellis2TextureStage`, `Trellis2UpsampleStage`, `VaeDecodeStructureTrellis2`,
`VaeDecodeTextureTrellis`), which generates textured meshes natively.

`CheckpointLoaderSimple`'s enum lists 34 checkpoints. Exactly one is a 3D
model: `hunyuan3d-dit-v2-mv_fp16.safetensors`. **No Trellis 2 checkpoint is on
disk.** The native texture nodes that consume `VOXEL` colours
(`PaintMesh`, `BakeTextureFromVoxel`) are therefore unreachable, because the
only producer of coloured voxels here is the Trellis decode.

### 2.2 Qwen-Image-Edit 2509 is installed, and it is the registration mechanism

`UNETLoader` offers `qwen_image_edit_2509_fp8_e4m3fn.safetensors`; `CLIPLoader`
offers `qwen_2.5_vl_7b_fp8_scaled.safetensors`; and
`TextEncodeQwenImageEditPlus` is present, taking **three** reference-image
slots.

This matters beyond "a generator is available". The hard part of adding a back
view is **registration** — an independently generated back view is a different
render and will not line up with the mesh's silhouette. The usual fix is
structural conditioning, and it is not available here: **`ControlNetLoader`'s
enum is empty**, zero models on disk.

An *edit* model removes the need for one. Given a render of the shell's own
180-degree view as the image being edited, the output is aligned to that mesh
by construction, because it is that image with paint on it.

### 2.3 Nothing between reconstruction and export rotates the shell

Read from the code, not measured. `npc_mesh.clean_shell` (`npc_mesh.py:328`) is
drop-specks -> **uniform scale** -> weld -> fill-holes. `npc_mesh.align_to`
(`npc_mesh.py:161`) **translates only**, and its docstring says why the base
must never move. There is no rotation in the path.

The consequence is the whole design: the shell sits in final world space at
Hunyuan3D's own orientation, so `npc_render.frame_camera(shell, 0)` — the
existing, already-tested turnaround camera — looks straight down the axis the
reconstruction was conditioned from. Confirmed empirically: `Jules Sokolova
Turnaround_000.png` is a front-facing A-pose.

**The projection camera is not new code.** It is `frame_camera` with one
changed constant (§4.2).

### 2.4 `apose_square.png` keeps its alpha

`square_apose()` composites the subject over a uniform backdrop so no rectangle
seam remains for Hunyuan3D to reconstruct as a slab. It would have been
reasonable for that to produce an opaque image. It does not: read back through
the script's own `_png_read`, `apose_square.png` (1323x1323) still carries a
real alpha channel with values across the full range.

So the single file the reconstruction actually saw provides **both** the
seam-free colour and the subject mask. §4.3 uses the second for edge validity.

### 2.5 The interpreter has no imaging libraries, and will not get any

`PIL`, `numpy`, `trimesh`, `xatlas`, `cv2` and `scipy` all fail to import in
the system Python. This is the standing constraint from the original 3D spec
(no dependency needing a compiler), and it is why `generate-3d.py` reads and
writes PNG by hand.

It is not a constraint on this work, because **all pixel handling here happens
inside Blender**, which ships its own interpreter with `numpy` and the whole of
`bpy`. No system-Python dependency is added.

## 3. Approaches considered

### 3.1 Trellis 2 (rejected for this problem)

Download the Trellis 2 checkpoints and switch generators; texture comes out
natively, jointly with geometry, and is coherent all the way round.

Rejected on three grounds. **Fidelity**: the goal is *this character's colours
from this reference image*, and Trellis re-imagines the character from that
image — more internally coherent, measurably less faithful. Half of what this
design produces is the reference's literal pixels, which no generator can beat
on faithfulness. **Risk**: it replaces the geometry generator and invalidates
everything `generate-3d.py` has measured — `octree_resolution` 384 (512 OOMs at
25.9 GB), the squaring fix, `--voxel` 0.013's clearance from the remesh cliff,
the parsed height correction. **Cost**: multi-gigabyte downloads and a
re-tuning pass, on a machine already shown to be VRAM-constrained.

None of this rules it out for the *detail* problem, where Hunyuan3D genuinely
struggles. That is a separate experiment judged on geometry.

### 3.2 Front projection only (the fallback, kept as a flag)

Project `apose_square.png` and wrap silhouette colours around the back. Zero
ComfyUI, instant, deterministic. The front is exact; the back is the right
palette with no detail.

Not mirroring. Mirroring the front across the sagittal plane would put an open
jacket and a visible tank top on the character's *back*, which is obviously
wrong in a way edge-wrap is not.

Kept as `--no-back-view` (§5.2): it is the graceful path when ComfyUI is
unavailable, and it is genuinely adequate at 32 mm print scale.

### 3.3 Front + one generated back view (chosen)

§3.2 plus a back view generated by editing the shell's own 180-degree render
(§2.2), blended by facing angle. Chosen because it is §3.2 with one more input
— the projector takes N views and front-only is N=1 — so it is not a fork in
the road, and because it keeps the tuned Hunyuan3D geometry untouched.

Four views (adding both sides) was considered and dropped: for an A-pose the
sides are mostly arm edges already covered, so it roughly doubles generation
cost for two more blend seams.

## 4. Design

### 4.1 A new `texture` stage

`STAGES` becomes `("apose", "mesh", "assemble", "texture")`.

Its own stage rather than part of `assemble`, for three reasons. It needs a
**ComfyUI round trip in the middle of Blender work**, and `assemble` is
deliberately one offline headless run with no network. It lets an NPC built
before this landed be textured with `--stage texture` alone, reading
`Shell.glb` and `apose_square.png` off disk rather than rebuilding geometry.
And it contains failure the way `--rig` already does (§5.3).

| Step | Where | In | Out |
|---|---|---|---|
| A | Blender | `Shell.glb` | `3d/_back_render.png` |
| B | ComfyUI | `_back_render.png`, `apose_square.png`, portrait | `3d/back.png` |
| C | Blender | shell + both images | `Texture.png`, re-exported `Shell.glb` |

Two Blender launches per NPC. Step A could later be folded into `assemble`,
which already has the shell in a session; keeping it separate is what makes the
back-catalogue case need no special handling.

### 4.2 The projection camera, and the one open assumption

`frame_camera(obj, angle)` builds an orthographic camera at
`ortho_scale = max(obj.dimensions) * 1.25` about the **bounding-box centre**.
`square_apose()` squares the subject on `max(subject_w, subject_h) * 1.12`
about the **subject's alpha bounds**.

These are the same rule — *the subject's own bounds, squared on the longer
side* — stated with different constants. The projection camera is therefore
`frame_camera` with `margin=1.12`, and the front camera and the reference image
frame the subject identically.

**This is bounds-matching, not a calibrated camera.** Hunyuan3D is not a
renderer and guarantees no metric correspondence between input pixel and output
vertex. If a reconstruction comes back with a different aspect ratio than its
source, residual misalignment remains that no framing constant can remove.

Nothing in §2 settles how large that residual is. §8.1 settles it in an hour,
before any of §4.3 is built.

### 4.3 Projection and bake — `blender/npc_texture.py`

1. **Atlas UVs.** Smart UV Project over the shell. This is the deliverable's
   UV layer.
2. **Per-view UVs.** One additional UV layer per view, from project-from-view
   at that view's camera: `proj_front` at `frame_camera(shell, 0, 1.12)`,
   `proj_back` at `frame_camera(shell, 180)` at the default margin.

   The two margins differ on purpose. The front's is fixed at 1.12 because it
   must match a reference image this pipeline did not frame (§4.2). The back's
   is free, because step A renders that image at the same camera the
   projection samples it with - so any margin works as long as the two agree,
   and the default is what `frame_camera` already ships.
3. **Blend.** With the front camera at -Y looking +Y, a surface's facing is its
   world normal's Y component alone. A dead-front surface faces the camera, so
   its normal is `(0, -1, 0)` and `Ny = -1`; a dead-back surface has `Ny = +1`.
   So `t = 0.5 + 0.5 * Ny` runs 0 at dead-front to 1 at dead-back;
   smoothstepped, that is the front->back mix factor.

   `t` rather than the obvious `max(0, +-Ny)` because the latter's weights both
   reach zero at the silhouette, which is exactly where a naive blend tears.
   `t` is smooth and never degenerate.
4. **Edge validity.** Each view's weight is multiplied by its own sampled
   alpha (§2.4). Where the mesh silhouette overshoots the image's, the texel
   falls to the other view instead of sampling backdrop grey.
5. **Bake** to `<Name> Texture.png` at `--texture-size` (default 2048), assign
   as the Principled base colour, re-export.

Resolution rationale for 2048: the shell is roughly 1.9 m^2 of surface, so a
2048^2 atlas is about 0.7 mm/texel against the reference's own ~1.3 mm/px. The
atlas is finer than the source, which is the right side of the trade. Vertex
colours were considered and rejected on the same arithmetic: ~81,000 vertices
over that area is ~5 mm between samples, roughly 4x coarser than the reference,
which would blur precisely the patches and stencils that motivate the work.
They survive only as the §8.1 probe.

### 4.4 The back view — `workflows/api/Util_BackView_QwenEdit_v1.json`

`TextEncodeQwenImageEditPlus` with three reference slots:

1. `_back_render.png` — the image being edited, which is what makes the result
   registered to the mesh (§2.2).
2. `apose_square.png` — the character's colours, materials and wear.
3. The NPC's **portrait**, when it is rear-facing. Several rolled portraits are
   composed "seen from behind" (Jules Sokolova's is), and where that is true
   the slot carries real evidence about the character's back. Omitted, not
   faked, when it is not.

The prompt reuses `apose_prompt(entry)` (`generate-3d.py:174`), which already
builds a full A-pose description from the entry's rolled traits, with its
stance clause replaced by a rear-facing one. Reused rather than restated: a
second description of the same character is a second thing to keep in step
with the tables, and `APOSE_STANCE` is already the precedent for a stance that
belongs to this tool rather than to the roll tables.

Nodes are addressed through the existing `node_of()` helper — by class, not by
id — so a re-export from the ComfyUI editor survives, and a second node of an
addressed class fails loudly.

## 5. Interface

### 5.1 Outputs

| File | Change |
|---|---|
| `<Name> Texture.png` | **new** — the baked atlas |
| `<Name> Shell.glb` | gains UVs, a Principled material, the packed texture |
| `<Name> Rigged.glb` | same, when `--rig` |
| `<Name> Print.stl` | **unchanged** — a print has no colour |
| `3d/_back_render.png`, `3d/back.png` | new intermediates, kept like `_shell.glb` |

The dossier's `## 3D` section gains the texture file and the new workflow, so
it keeps recording everything needed to reproduce its own output.

### 5.2 Flags

- `--texture` / `--no-texture` — **on by default.** Unlike `--rig`, which ships
  off because both bind modes were measured as broken, this is the point of the
  exercise. `--no-texture` restores today's behaviour exactly.
- `--texture-size` (2048).
- `--no-back-view` — §3.2's front-only path. No ComfyUI job runs.
- `--back-image PATH` — supply a back view instead of generating one, mirroring
  `--image`'s existing design and its checks.

### 5.3 Failure containment

A texture failure records `texture_error` in the assembly report, prints to
stderr, and leaves every untextured deliverable intact — the same containment
`--rig` uses, and for the same reason: the untextured shell is what ships
today and is worth more than nothing.

One thing rigging did not need: this stage **rewrites an existing
deliverable**. So the bake and export go to a temporary, and `Shell.glb` is
replaced only once the whole stage has succeeded. A crash mid-bake must not
leave a corrupt file where a good one was.

## 6. Testing

Following the three files already present, and adding one.

- `test_3d_workflows.py` — the new graph has exactly one of each addressed node
  class, and the job builder patches the image slots and the prompt it claims
  to.
- `test_3d_cli.py` — `--stage texture` is selectable; `texture` runs without
  `mesh`; `--no-back-view` queues no ComfyUI job; `--back-image` alongside
  `--no-back-view` is refused; `--no-texture` reproduces today's output list.
- `test_3d_texture.py` (**new**) — real Blender over the committed
  `test/fixtures/3d/shell.glb`: a UV layer is created, `Texture.png` is written
  at the requested size, a material is assigned, and the exported GLB embeds
  the image. Skipped when Blender is absent, like `test_3d_assembly.py`.

No test requires ComfyUI, a GPU, or a model download.

## 7. Risks and accepted limits

### 7.1 Registration is bounds-matching (open until §8.1)

§4.2. The one assumption the evidence does not settle. Mitigated by settling it
first, and cheaply.

### 7.2 Concavities get the wrong colour — accepted for v1

Project-from-view ignores depth. A texel that faces the front camera but is
**occluded** from it — under the jacket flap, under the chin, between the legs,
inside the collar — samples whatever front pixel sits at that screen position,
which belongs to the surface in front of it.

Normal-weighting handles the front/back split correctly. It does not handle
this. Doing so properly means per-texel ray-cast visibility, which is a
significantly larger piece of work.

Shipped as a documented limit, with the artifact measured rather than
estimated once there is something to measure. The refinement is additive: a
visibility term multiplies into the same weights §4.3 already computes.

### 7.3 Unquantified: Smart UV Project on an open 162k-face shell

The shell is not closed — the docs record 1,355 boundary edges — and dense.
Smart UV Project will produce many islands. Whether the packing is efficient
enough at 2048^2, and whether island seams are visible on the deliverable, is
not known. Fallback if it is poor: raise `--texture-size`, or unwrap the
printable (welded, closed) copy and transfer.

### 7.4 Unquantified: VRAM headroom for Qwen-Image-Edit

This machine OOMed a `VoxelToMesh` at 25.9 GB. Qwen-Image-Edit 2509 at fp8 is
large, and it runs after two reconstructions in the same batch.
`generate-3d.py` already has `--pause-3d` for exactly this class of problem
(ComfyUI reports a job done before its VRAM is freed), so the mitigation
exists; whether it is needed here is not known.

### 7.5 The generated back will not agree with the front in detail

A Qwen back view will not place the jacket's seams, the hair's fall or the
wear pattern where a real turn of the character would. The blend is smooth, so
this reads as a soft transition rather than a seam, but the back is a
plausible invention and the documentation must not imply otherwise.

## 8. Order of work

### 8.1 First, and disposable: the registration probe

Before any of §4.3, sample `apose_square.png` per **vertex** through the §4.2
camera and write it to a colour attribute. Roughly twenty lines, no unwrap, no
bake, no ComfyUI.

Its only purpose is to answer §4.2's open question by eye and by number: render
a turnaround of the vertex-coloured shell and compare it against the reference.
If the eyes land on the eyes and the jacket patches land on the jacket, the
framing is right and the rest of the design is sound.

**This code does not ship.** §4.3 replaces it.

### 8.2 Then

1. `--no-back-view` end to end: unwrap, project one view, bake, export.
   Deliverable, testable, and useful on its own.
2. The Qwen workflow and the two-view blend.
3. Rigged GLB carries the texture.
4. Docs: `docs/generate-3d.md` gains a Texturing section and §7's limits.
