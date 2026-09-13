# NPC 3D pipeline: turning a generated NPC into a rigged, printable model

> **Status:** designed 2026-09-04; since implemented as `generate-3d.py`
> (usage in `docs/generate-3d.md`), so read this as the design record, not a
> work order. Every capability claim
> in §2 was measured on this machine during a feasibility probe on 2026-09-04,
> not estimated — the probe queued real jobs against the live ComfyUI on
> `127.0.0.1:8000` and inspected the results in Blender 5.2.1 LTS. §7.1 is the
> one structural risk that the probe did *not* settle and is the part of this
> document most worth reading before starting work.

## 1. Problem

`generate-npc.py` produces, per NPC, a 1024x1024 portrait and a 1024x1280
full-body token with a real alpha cut-out, plus a dossier recording every
rolled trait and both prompts verbatim. 160 NPCs sit in
`.generated-npcs.json` today.

Those NPCs exist only as 2D art. The campaign wants three further things from
the same characters, and none of them are reachable from a PNG:

- a **rigged, animatable** character,
- a **3D-printable** mini,
- **Foundry VTT** assets that show the same person from any angle.

### Goals

- One NPC in the manifest goes in; a rigged GLB, a printable STL, a clothed
  shell and a set of turnaround renders come out.
- Works on the **existing back catalogue**, not only on NPCs generated after
  this lands.
- `generate-npc.py`'s behaviour, CLI and output layout are unchanged.
- A 3D failure never damages or blocks art generation.
- No compiled CUDA extensions, because this machine cannot build them (§2.2).

### Non-goals

- Texturing the rigged character. Geometry first; see §7.3.
- Faces of portrait quality. Reconstruction cannot deliver them (§2.3) and
  nothing in this design pretends otherwise.
- Multi-person scenes, video, or mocap, though SAM3DBody supports all three.
- Replacing the 2D pipeline. This is additive.

## 2. What the probe established

This section is evidence, not intent. It exists so the next person does not
repeat the investigation.

### 2.1 No custom nodes are needed

The installed ComfyUI already registers a full native 3D node set:
`EmptyLatentHunyuan3Dv2`, `Hunyuan3Dv2Conditioning`,
`Hunyuan3Dv2ConditioningMultiView`, `VAEDecodeHunyuan3D`, `VoxelToMesh`,
`RemeshMesh`, `DecimateMesh`, `FillHoles`, `WeldVertices`, `UnwrapMesh`,
`SaveGLB`, the `SAM3DBody_*` family, `BuildPoseFile`, and `EmptyTrellis2LatentStructure`.

**No custom node pack is installed or required.** This is the single most
important practical finding: the usual image-to-3D packs are the flakiest part
of any such pipeline on Windows, and this design avoids them entirely.

### 2.2 Why compiled extensions are off the table

The ComfyUI venv at `G:\Documents\ComfyUI\.venv` runs **Python 3.12.11, torch
2.11.0+cu130**, and the machine has **no MSVC build tools**. `pip index
versions` finds no distribution for `nvdiffrast`, `diff-gaussian-rasterization`,
`torchmcubes` or `pytorch3d`. All four would need a source build.

This is survivable because those deps are used mostly for texture baking, and
Blender does UV unwrap and texture projection natively. Any future change to
this pipeline must respect the same constraint.

### 2.3 Hunyuan3D gives a good clothed body and a broken head

Model: `hunyuan3d-dit-v2-mv_fp16.safetensors` (4.59 GB, from
`Comfy-Org/hunyuan3D_2.0_repackaged`, in `models/checkpoints`). Bundles
conditioner + model + vae, so `ImageOnlyCheckpointLoader` alone loads it.

Run against `Jules Sokolova Token.png` single-view, `octree_resolution` 256,
`surface net` at threshold 0.6:

| Measure | Value |
|---|---|
| Faces | 264,224 |
| Watertight | No |
| Euler number | 3950 (−1225 for the body alone) |
| Components | 10,895 — but 83.5% of faces in one |
| Sub-20-face specks | 10,878, carrying 16% of faces |
| UVs | None |

Visually the body is **good**: correct proportions and pose, with the jacket,
trousers, boots and slung carbine all reconstructed as distinct geometry, and a
plausibly inferred back. The painterly, halftone-shaded house style did **not**
confuse the model, which was the main risk going in.

The **head fails**. The helmet-and-loose-hair region fragments into the
speck components and reads as a beak in profile. There is no usable face.

### 2.4 SAM3DBody gives a production-quality rig and a useless pose

Model: `sam_3d_body_dinov3_bf16.safetensors` (2.64 GB, from
`Comfy-Org/sam-3d-body`, in `models/detection`; an int8 build exists at
1.86 GB). Runs in **5 seconds**, no OOM, on a 12 GB RTX 3080.

`BuildPoseFile` with `format=glb`, `mesh_style=body_mesh` exports, verified by
import into Blender:

| Measure | Value |
|---|---|
| Bones | 127, one root, bound via an Armature modifier |
| Vertex groups | 127 — full skin weighting |
| Geometry | 18,439 verts / 36,874 faces |
| Shape keys | 73 face morphs |
| Non-manifold edges | **0 of 55,311** |
| Scale | 1.73 m tall, A-pose |

That is a clean, watertight, fully-rigged human at true real-world scale.

The **predicted pose is unusable** — the figure comes out crouched and
contorted with the fingers splayed into long spikes. Neither flattening the
alpha onto white nor disabling `run_hand_refinement` changed it, so it is the
pose estimator misreading stylised painterly art, not an input defect.

This does not matter, because setting `armature.data.pose_position = 'REST'`
discards the animation track and leaves the clean A-pose body. Rendering in
rest position confirmed a textbook A-pose mesh with correct anatomy, real
hands and a real face. **The predicted pose was never the valuable part** — a
rigged character wants a neutral bind pose anyway.

### 2.5 Blender is ready

`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`, **5.2.1 LTS**,
Python 3.13.13. Headless `--background --python` verified working, with GLTF
import/export, FBX export, STL export, Smart UV, Remesh, Decimate and
**Rigify** all present. Note the render engine enum is `BLENDER_EEVEE`, not
`BLENDER_EEVEE_NEXT`.

### 2.6 Dynamic combo inputs serialise as dotted keys

New-schema nodes (`COMFY_DYNAMICCOMBO_V3`) do **not** take a nested object in
API-format JSON. Nested inputs are flattened with dot-joined parent ids:

```json
"format": "glb",
"format.mesh_style": "body_mesh",
"format.mesh_style.bone_vis": "off",
"format.mesh_style.shader": "default",
"format.bone_smooth_window": 0
```

Passing a nested dict validates but fails at execution with
`missing 1 required positional argument`. Resolve the full required set by
walking `/object_info` rather than by trial and error.

## 3. Architecture

A new entry point, **`generate-3d.py`**, standing in the same relation to
`generate-art.py` that `generate-npc.py` does: it imports the ComfyUI plumbing
rather than duplicating it, and it is a separate command rather than a flag
because a slow, failure-prone reconstruction stage should not be able to break
art generation.

It reads `.generated-npcs.json` and operates on manifest entries by `id`, so
the entire existing catalogue is eligible.

Four stages per NPC:

```
manifest entry
  │
  ├─ Stage 0  rebuild npc dict, force A-pose Stance, build_prompts(),
  │           queue existing token workflow + RMBG      →  3d/apose.png
  │
  ├─ Stage 1a apose.png → Hunyuan3D                     →  3d/_shell.glb
  ├─ Stage 1b apose.png → SAM3DBody → BuildPoseFile     →  3d/_base.glb
  │
  ├─ Stage 2  Blender headless: rest-pose the base, clean the shell,
  │           transfer weights, bind, export
  │
  └─ Stage 3  deliverables into <NPC folder>/3d/ + a `## 3D` dossier section
```

## 4. Stage 0: the A-pose source render

### 4.1 Why a re-render is necessary

Skin-weight transfer is proximity-based: Blender's Data Transfer maps shell
vertices to nearby body vertices. The SAM3DBody base is in **A-pose**; the
Hunyuan3D shell inherits the token's **rolled stance**, arms down at the sides.
Transferring across that mismatch produces garbage at the shoulders and arms.

Three ways out were considered:

- **Fix the pose prediction.** Rejected: the estimator already failed on this
  house style (§2.4) and would fail unpredictably per-NPC.
- **Retarget an armature to the shell in Blender.** Rejected for now: most
  robust, most code, hardest to debug headlessly. Retained as the §7.1
  fallback.
- **Render the 3D source image in A-pose.** Chosen. It removes the mismatch by
  construction rather than correcting for it, reuses machinery that already
  exists, and costs one extra image per NPC.

A-pose also improves the Hunyuan3D reconstruction independently, by separating
the limbs from the torso so the arms do not fuse to the body.

The accepted tradeoff: the 3D model's pose will not match the NPC's portrait.
For a rigged character that is correct. For a static print mini it is posed
afterwards in Blender.

### 4.2 How, without touching `generate-npc.py`

`--set-trait` is deliberately refused on the regen path — the parser errors
with *"--regen-manifest replaces the roll entirely; drop --set-trait"* — and
`Stance` is not in `REROLLABLE_TRAITS`. **Neither guard is weakened.** Both
say something true about `--regen-manifest`'s contract, and Stage 0 is not
regeneration; it is a different tool rendering a different image.

Instead `generate-3d.py` uses the pure functions directly, the way
`test/helpers.py` already loads the hyphenated module:

1. Read the manifest entry; rebuild the npc dict from its stored `traits`.
2. `npc["Stance"] = APOSE_STANCE` — a module constant in `generate-3d.py`.
3. `build_prompts(npc)` — already a pure `npc → (portrait, token)` function.
4. Queue the token prompt through the entry's own recorded `workflow`, then
   the existing RMBG pass.

`APOSE_STANCE` must read as an ordinary Stance bullet so it composes with the
surrounding prompt grammar — roughly *"standing straight and squarely facing
the viewer, arms held slightly away from the sides with the palms forward,
feet shoulder-width apart"*.

Carried weapons are a known wrinkle: an NPC holding a carbine in both hands
cannot hold an A-pose. Stage 0 therefore also forces the unarmed carry path,
matching how `roll_npc()` already filters stances against occupied hands.

## 5. Stage 1: the two meshes

Two new API-format workflows in `workflows/api/`, named to match the existing
`Util_*` / `Lancer_*` convention:

- **`Util_Image_to_Mesh_Hunyuan3D_v1.json`** —
  `ImageOnlyCheckpointLoader → CLIPVisionEncode → Hunyuan3Dv2Conditioning →
  EmptyLatentHunyuan3Dv2 → KSampler → VAEDecodeHunyuan3D → VoxelToMesh →
  RemeshMesh → DecimateMesh → SaveGLB`.
  `RemeshMesh`'s `drop_small_components` removes the §2.3 specks in-graph;
  `fix_poles` and `project_back` are what make the result approach printable.
- **`Util_Image_to_RiggedBody_SAM3D_v1.json`** —
  `SAM3DBody_Loader → SAM3DBody_Predict → BuildPoseFile → SaveGLB`, with the
  dotted dynamic-combo keys of §2.6.

Both are checked in so a run is reproducible, exactly as the existing
workflows are.

## 6. Stage 2: Blender assembly

One headless script, `blender/assemble_npc.py`, invoked as
`blender --background --factory-startup --python ... -- <base.glb> <shell.glb> <outdir>`.

1. Import both GLBs.
2. `armature.data.pose_position = 'REST'` and `animation_data_clear()` on the
   base — discard the §2.4 pose.
3. Normalise: the base is in metres, Z-up; the shell is unit-scaled. Align by
   scaling the shell to the base's height and centring both.
4. Clean the shell: keep the largest component, weld, fill holes, remesh.
5. `DATA_TRANSFER` modifier, `VGROUP_WEIGHTS`, nearest-face-interpolated, from
   base to shell; then bind the shell to the armature.
6. Export the four deliverables of §6.1.
7. **Assert before writing**: bone count > 0, every shell vertex carries at
   least one non-zero weight, and the STL reports zero non-manifold edges.
   A stage that cannot meet these fails loudly rather than emitting a quietly
   broken mesh.

### 6.1 Outputs

Into `<NPC folder>/3d/`, beside the existing portrait and token, keeping an
NPC folder self-contained as it is today:

| File | What it is |
|---|---|
| `<Name> Rigged.glb` | Clothed shell, weighted to the 127-bone armature |
| `<Name> Print.stl` | Manifold body, scaled to 32 mm |
| `<Name> Shell.glb` | Clothed mesh, cleaned, unrigged |
| `<Name> Turnaround_{000,090,180,270}.png` | Orbit renders |

A `## 3D` section is appended to the existing dossier listing these files, the
two workflow files used, and the `APOSE_STANCE` text — so the dossier keeps its
present property of recording everything needed to reproduce the output.

## 7. Risks

### 7.1 Weight transfer is unproven

**This is the one structural risk the probe did not settle.** A-pose alignment
removes the reason to expect failure, but no transfer has been run on this
data. Transferring weights onto a bulky jacket whose silhouette departs from
the body underneath may still smear at the shoulders and skirt hem.

Containment: only `Rigged.glb` depends on it. The STL, the shell and the
turnarounds are unaffected. If it fails, the fallbacks in order are a Surface
Deform bind instead of direct weighting, then §4.1's armature retargeting.

This is why §9 sequences the rigging bridge last and separately.

### 7.2 Faces will not be good

§2.3's head fragmentation is the known weak point, and A-pose does not address
it. `Hunyuan3Dv2ConditioningMultiView` is installed and is the real fix, but
generating consistent left/back/right views is its own design problem — the
existing Krea i2i workflow or `SV3D_Conditioning` — and is deliberately out of
scope here. At token and mini scale the head reads acceptably; in close-up it
does not.

### 7.3 No texture on the rigged character

Texture baking is the part that wanted the unbuildable deps of §2.2. Blender
can project the A-pose render onto the mesh, but that is a further stage and
is not designed here.

### 7.4 Disk

Roughly 20–40 MB per NPC across four files. Across 160 NPCs that is several
gigabytes. No ignore-rule work is needed: NPC folders live either under the
repo's `output/`, which is already ignored, or under ComfyUI's own output
directory outside the repo entirely. A `3d/` subfolder inherits both.

## 8. Error handling and CLI

Conventions follow `generate-art.py` and `generate-npc.py` so the tool feels
like the others: `--dry-run`, `--server` with the 8000–8015 probe, `--filter`
by name or category, `--overwrite`, and a `--stage` flag to run one stage in
isolation while iterating.

Per-NPC isolation: a failure logs and continues to the next NPC, never aborts
a batch. An NPC with an existing `3d/` folder is skipped unless `--overwrite`.

## 9. Sequencing

The spec covers the whole pipeline; the implementation plan should land it in
three independently useful pieces.

1. **Stages 0–1.** A-pose render plus both meshes. Ends with two GLBs on disk
   and no Blender work. Independently useful: proves the A-pose approach.
2. **Stage 2 without rigging.** Cleanup, STL, shell, turnarounds. Delivers the
   printing and VTT goals in full.
3. **The rigging bridge.** Weight transfer, `Rigged.glb`, and step 7 of §6's
   assertions. Judged on its own against §7.1.

## 10. Testing

The suite is 217 tests using `test/helpers.py`'s `load_generator()` to import
the hyphenated module; `test_token_pose.py` and `test_stance_content.py` are
the nearest existing neighbours and the new stance work belongs beside them.

- `APOSE_STANCE` reaches the built token prompt, and the prompt describes a
  neutral standing pose.
- Stage 0 forces the unarmed carry path (§4.2), so no A-pose NPC is described
  holding a two-handed weapon.
- A manifest entry round-trips to an npc dict that `build_prompts()` accepts,
  including pre-Weapon entries — the `.get` shim at `build_prompts()` exists
  for exactly this.
- Both workflow JSONs validate against a live `/object_info`, including the
  dotted dynamic-combo keys of §2.6, which are the likeliest thing to rot on a
  ComfyUI update.
- The Blender stage asserts bones, weights and manifoldness against a small
  committed fixture, so it is testable without a GPU.
