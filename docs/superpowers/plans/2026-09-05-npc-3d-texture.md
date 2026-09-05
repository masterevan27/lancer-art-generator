# NPC 3D Texturing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Project the reference A-pose image's own pixels onto the reconstructed shell and bake them to a texture atlas, so `Shell.glb` and `Rigged.glb` ship in colour instead of grey.

**Architecture:** A fourth stage, `texture`, runs after `assemble`. It launches Blender twice: once to render the shell's own 180-degree view, and once to unwrap the shell, project the front reference image and the back view onto it through two cameras, blend them by surface normal, and bake the result to a PNG atlas. Between the two launches, ComfyUI edits the back render into a painted back view with Qwen-Image-Edit 2509. All pixel handling happens inside Blender, which ships its own `numpy`; the system interpreter gains no dependency.

**Tech Stack:** Python 3 standard library only (system side), `bpy` / Blender 5.2 LTS (mesh, projection, bake), ComfyUI API-format JSON workflows (back view), `unittest`.

**Spec:** `docs/superpowers/specs/2026-09-05-npc-3d-texture-design.md`

## Global Constraints

- **No new system-Python dependency.** `PIL`, `numpy`, `trimesh`, `xatlas`, `cv2`, `scipy` are all absent from the system interpreter and stay absent (spec §2.5). PNG is read and written by hand through the existing `_png_read` / `_png_write` in `generate-3d.py`. Anything needing an array lives inside Blender.
- **Never damage an untextured deliverable.** A texture failure records the error, prints to stderr, and leaves `Shell.glb`, `Print.stl` and the turnarounds exactly as `assemble` left them (spec §5.3). The bake and the re-export go to underscore-prefixed temporaries and are moved into place with `os.replace` only after the whole stage succeeded.
- **`Print.stl` is never touched.** A print has no colour (spec §5.1).
- **Blender operator availability:** `bpy.ops.uv.project_from_view` requires a `VIEW_3D` area and **does not work under `--background`**. Per-view UVs are computed in Python with `bpy_extras.object_utils.world_to_camera_view`, which handles orthographic cameras correctly. Do not reach for the operator.
- **Baking is Cycles-only.** `bpy.ops.object.bake` does not exist for EEVEE. The bake step sets `scene.render.engine = 'CYCLES'` with the CPU device and 1 sample — the same "no GL context needed" trade `test_3d_assembly.py` already relies on.
- **Addressing nodes:** the existing `node_of()` helper requires exactly one node of a class. The back-view graph has **three** `LoadImage` nodes and **two** `TextEncodeQwenImageEditPlus` nodes, so `node_of()` cannot address them. They are reached by following links from the unique `KSampler`, via `backview_slots()` (Task 6).
- **Tests never require ComfyUI, a GPU, or a model download** (spec §6). Live-server checks are `@unittest.skipUnless(server_is_up())`, Blender checks are `@unittest.skipUnless(BLENDER)`.
- Run tests with `python -m unittest discover -s test -t . -v` from the repo root, or a single case with `python -m unittest test.test_3d_texture.TestBake.test_name -v`.

## Correction to the spec: the front camera margin is 1.06, not 1.12

Spec §4.2 states that `square_apose()` squares the subject on `max(subject_w, subject_h) * 1.12` and concludes the projection camera is `frame_camera` with `margin=1.12`. The code says otherwise:

```python
APOSE_MARGIN = 0.06     # generate-3d.py:410
side = int(max(subject_w, subject_h) * (1 + margin))   # generate-3d.py:513
```

`APOSE_MARGIN` has been `0.06` since the commit that introduced it (`5216678 fix: the two clips cutting heads and feet off every reconstruction`); it has never been `0.12`. The subject therefore occupies `1 / 1.06` of the square, and the matching camera margin is **1.06**.

The spec's *reasoning* is correct and is what this plan implements — the two framings are the same rule stated with different constants, so the camera must use the constant `square_apose()` actually used. The plan removes the possibility of this drifting again: `generate-3d.py` derives `FRONT_MARGIN = 1 + APOSE_MARGIN` and passes it to Blender as `--front-margin`, so the Blender side never restates the number, and a test asserts the derivation holds.

## File structure

| File | Responsibility |
|---|---|
| `blender/npc_texture.py` | **new.** The library: projection cameras, per-view UVs, the atlas unwrap, the blend material, the bake, the finished material. No argparse, no I/O policy. Mirrors `npc_mesh.py` / `npc_render.py`. |
| `blender/texture_npc.py` | **new.** The headless entry point, invoked twice per NPC with `--step back` and `--step bake`. Argparse plus a `LANCER3D` JSON report line. Mirrors `assemble_npc.py`. |
| `blender/probe_projection.py` | **new, then deleted in Task 9.** The §8.1 registration probe. Does not ship. |
| `workflows/api/Util_BackView_QwenEdit_v1.json` | **new.** The Qwen-Image-Edit 2509 back-view graph. |
| `generate-3d.py` | **modified.** `STAGES` gains `texture`; the texture flags; `stage_texture()`; the back-view job builder; the dossier gains the texture file and the back-view workflow. |
| `blender/npc_render.py` | **unmodified.** `frame_camera()` is reused as-is; its margin is already a parameter. |
| `blender/npc_mesh.py` | **unmodified.** `import_glb`, `join`, `export_glb` are reused as-is. |
| `test/test_3d_texture.py` | **new.** Real Blender over `test/fixtures/3d/shell.glb`. Skipped when Blender is absent. |
| `test/test_3d_cli.py` | **modified.** Stage selection, the flags, the command builder, the containment. |
| `test/test_3d_workflows.py` | **modified.** The back-view graph's shape and its live-server schema check. |
| `docs/generate-3d.md` | **modified.** A Texturing section, the new outputs, and §7's limits. |

---

### Task 1: The registration probe (disposable)

Spec §8.1. Nothing else in this plan is worth building if the reference image and the reconstruction do not line up, and this answers that in an hour. **This code does not ship** — Task 9 deletes it.

**Files:**
- Create: `blender/probe_projection.py`
- Test: none. The output is a render a human looks at.

**Interfaces:**
- Consumes: `npc_mesh.clear_scene`, `npc_mesh.import_glb`, `npc_mesh.join`, `npc_render.frame_camera`, `npc_render.turnaround` (all existing).
- Produces: nothing any later task imports. Its finding — whether bounds-matching registers well enough — gates Tasks 2-8 and is quoted by Task 9's docs.

- [ ] **Step 1: Write the probe**

Create `blender/probe_projection.py`:

```python
"""DISPOSABLE. Spec §8.1: does bounds-matching actually register?

Samples apose_square.png per VERTEX through the projection camera and writes
it to a colour attribute, then renders a turnaround of the result. No unwrap,
no bake, no ComfyUI - the only question is whether the reference's pixels land
on the right parts of the mesh.

    "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" \\
        --background --factory-startup --python blender/probe_projection.py -- \\
        "<3d/Jules Sokolova Shell.glb>" "<3d/apose_square.png>" "<outdir>"

Delete this file once §4.3 replaces it. It is committed only so the answer is
reproducible by whoever doubts it later.
"""
import os
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import npc_mesh   # noqa: E402
import npc_render  # noqa: E402

# 1 + generate-3d.py's APOSE_MARGIN (0.06). Hardcoded here because this file is
# disposable and takes no argument it does not need; the shipping code derives
# it instead (Task 4).
FRONT_MARGIN = 1.06


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    shell_path, image_path, outdir = Path(argv[0]), Path(argv[1]), Path(argv[2])
    outdir.mkdir(parents=True, exist_ok=True)

    npc_mesh.clear_scene()
    shell = npc_mesh.join(npc_mesh.import_glb(shell_path), "shell")

    # The camera's frame is square only if the render is: view_frame(), which
    # world_to_camera_view calls, reads the scene's aspect. This must come
    # first or every UV is stretched along one axis.
    scene = bpy.context.scene
    scene.render.resolution_x = scene.render.resolution_y = 1024

    image = bpy.data.images.load(str(image_path))
    width, height = image.size
    pixels = list(image.pixels)   # RGBA floats, bottom row first

    camera = npc_render.frame_camera(shell, 0, FRONT_MARGIN)
    mesh = shell.data
    colours = mesh.color_attributes.new("probe", 'FLOAT_COLOR', 'POINT')
    for i, vertex in enumerate(mesh.vertices):
        uv = world_to_camera_view(scene, camera, shell.matrix_world @ vertex.co)
        x = min(max(int(uv.x * width), 0), width - 1)
        y = min(max(int(uv.y * height), 0), height - 1)
        base = (y * width + x) * 4
        colours.data[i].color = pixels[base:base + 4]
    bpy.data.objects.remove(camera, do_unlink=True)

    material = bpy.data.materials.new("probe")
    material.use_nodes = True
    tree = material.node_tree
    attribute = tree.nodes.new("ShaderNodeVertexColor")
    attribute.layer_name = "probe"
    emission = tree.nodes.new("ShaderNodeEmission")
    tree.links.new(attribute.outputs["Color"], emission.inputs["Color"])
    output = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL')
    tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    shell.data.materials.clear()
    shell.data.materials.append(material)

    npc_render.turnaround(shell, outdir, "Probe", angles=(0, 180),
                          size=1024, engine='CYCLES', samples=1)
    print("LANCER3D probe wrote %s" % outdir)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it against the real reconstruction**

There is one on disk already. From the repo root:

```bash
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
  --background --factory-startup --python blender/probe_projection.py -- \
  "output/LancerNPCs/run1/Pilots/Jules Sokolova/3d/Jules Sokolova Shell.glb" \
  "output/LancerNPCs/run1/Pilots/Jules Sokolova/3d/apose_square.png" \
  "output/_3dprobe"
```

Expected: exits 0, writes `output/_3dprobe/Probe Turnaround_000.png` and `..._180.png`.

- [ ] **Step 3: Look at it, and decide**

Open `Probe Turnaround_000.png` beside `output/LancerNPCs/run1/Pilots/Jules Sokolova/3d/apose_square.png`.

The question is registration, not quality. Check, in order:

1. Do the eyes land on the head's eyes, rather than on the forehead or the chin?
2. Do the jacket's patches and any stencilled number land on the jacket, at roughly the right height?
3. Do the boots' colours stop at the boots, rather than running up the shins or stopping short?

**PASS** — the features land within roughly their own body part. Vertical drift of a couple of centimetres on a 1.75 m figure is expected and is what the atlas resolution of Task 3 smooths over. Continue to Task 2.

**PARTIAL** — features land on the right body part but consistently shifted along one axis. This is a framing constant, not a broken idea: re-run with `FRONT_MARGIN` set to 1.00 and to 1.12 to bracket it, and take whichever registers. Record the winning value. Task 4 must then set `FRONT_MARGIN` in `generate-3d.py` to that number with a comment saying it was **measured** rather than derived, and its test asserts the measured value instead of the derivation.

**FAIL** — the projection is scrambled, or features land on unrelated body parts. Do not continue: spec §7.1's risk has materialised, the reconstruction does not correspond to its source image, and §4.3 cannot be rescued by a constant. Stop and report this, with both PNGs.

- [ ] **Step 4: Commit the probe and the finding**

```bash
git add blender/probe_projection.py
git commit -m "probe: does the reference image register with the reconstruction (spec 8.1)"
```

Record the verdict and the margin used in the commit message body — Task 9 quotes it in the docs, and the probe file is gone by then.

---

### Task 2: The projection camera and per-view UVs

The half of §4.3 that decides *where on the image* each vertex samples. Split from the bake because it is what the probe just validated, everything else is built on it, and it is testable without a bake.

**Files:**
- Create: `blender/npc_texture.py`
- Create: `test/test_3d_texture.py`

**Interfaces:**
- Consumes: `npc_render.frame_camera(obj, angle_deg, margin=1.25)`, `npc_mesh.import_glb(path)`, `npc_mesh.join(objects, name)`.
- Produces:
  - `npc_texture.BACK_MARGIN` (float, `1.25`)
  - `npc_texture.BACK_RENDER_PX` (int, `1024`)
  - `npc_texture.square_render(size)` -> the scene
  - `npc_texture.projection_camera(obj, angle_deg, margin)` -> camera object
  - `npc_texture.project_uvs(obj, camera, name)` -> the UV layer's name (str)

- [ ] **Step 1: Write the failing test**

Create `test/test_3d_texture.py`:

```python
"""Projection, unwrap and bake, against the committed fixture shell.

Real Blender, no GPU and no ComfyUI: the fixture cylinder stands in for a
reconstruction, and everything the texture stage promises about it - a UV
layer exists, the atlas is written at the size asked for, the material is
assigned, the exported GLB carries the image - is a property of any mesh.

Skipped rather than failed when Blender is not installed, exactly as
test_3d_assembly.py is.
"""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from test.helpers import REPO, load_3d

d3 = load_3d()
FIXTURES = REPO / "test" / "fixtures" / "3d"
SHELL = FIXTURES / "shell.glb"
TEXTURE_SCRIPT = REPO / "blender" / "texture_npc.py"
STEM = "Fixture Figure"


def blender_or_none():
    try:
        return d3.find_blender()
    except SystemExit:
        return None


BLENDER = blender_or_none()


def write_test_png(path, size, rgba):
    """A flat `size` x `size` RGBA PNG, through generate-3d.py's own writer."""
    d3._png_write(path, size, size,
                  [bytearray(bytes(rgba) * size) for _ in range(size)])


def run_blender(script, *args):
    """One headless run of an arbitrary --python script. -> (report, proc)."""
    proc = subprocess.run(
        [str(BLENDER), "--background", "--factory-startup",
         "--python", str(script), "--"] + [str(a) for a in args],
        capture_output=True, text=True, timeout=600)
    line = next((l for l in proc.stdout.splitlines()
                 if l.startswith("LANCER3D ")), None)
    if line is None:
        raise AssertionError(
            "no LANCER3D report line.\nstdout:\n%s\nstderr:\n%s"
            % (proc.stdout[-3000:], proc.stderr[-3000:]))
    return json.loads(line[len("LANCER3D "):]), proc


# A throwaway --python script, written into the temp dir at run time. The
# projection has no CLI of its own - texture_npc.py's steps are 'back' and
# 'bake', not 'project' - so this is how the UV layer alone gets exercised.
PROJECT_PROBE = '''
import os, sys, json
sys.path.insert(0, %r)
import bpy
import npc_mesh, npc_texture
argv = sys.argv[sys.argv.index("--") + 1:]
npc_mesh.clear_scene()
shell = npc_mesh.join(npc_mesh.import_glb(argv[0]), "shell")
npc_texture.square_render(256)
camera = npc_texture.projection_camera(shell, 0, 1.06)
name = npc_texture.project_uvs(shell, camera, "proj_front")
uvs = [tuple(loop.uv) for loop in shell.data.uv_layers[name].data]
xs = [u for u, v in uvs]
ys = [v for u, v in uvs]
print("LANCER3D " + json.dumps({
    "layer": name,
    "layers": [l.name for l in shell.data.uv_layers],
    "loops": len(uvs),
    "min_x": min(xs), "max_x": max(xs),
    "min_y": min(ys), "max_y": max(ys),
}))
'''


@unittest.skipUnless(BLENDER, "Blender not installed")
class TestProjectedUVs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        script = Path(cls._tmp.name) / "project_probe.py"
        script.write_text(PROJECT_PROBE % str(REPO / "blender"),
                          encoding="utf-8")
        cls.report, cls.proc = run_blender(script, SHELL)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_it_exits_cleanly(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr[-3000:])

    def test_a_uv_layer_is_created_under_the_asked_for_name(self):
        self.assertEqual(self.report["layer"], "proj_front")
        self.assertIn("proj_front", self.report["layers"])

    def test_every_loop_gets_a_uv(self):
        self.assertGreater(self.report["loops"], 0)

    def test_the_subject_lands_inside_the_frame(self):
        """A margin above 1.0 leaves the figure inside 0..1 with room spare."""
        self.assertGreaterEqual(self.report["min_x"], 0.0)
        self.assertLessEqual(self.report["max_x"], 1.0)
        self.assertGreaterEqual(self.report["min_y"], 0.0)
        self.assertLessEqual(self.report["max_y"], 1.0)

    def test_the_subject_fills_most_of_the_frame(self):
        """Bounds-matching, not an arbitrary camera: the fixture is a 1.0-tall
        cylinder and a margin of 1.06 must put it across ~94% of the frame."""
        self.assertGreater(self.report["max_y"] - self.report["min_y"], 0.9)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m unittest test.test_3d_texture -v`
Expected: FAIL — `no LANCER3D report line`, with `ModuleNotFoundError: No module named 'npc_texture'` in the captured stderr.

(If the whole class is *skipped*, Blender is not installed. This task cannot be verified without it — run it on a machine that has Blender rather than moving on.)

- [ ] **Step 3: Write the module**

Create `blender/npc_texture.py`:

```python
"""Projecting a reference image onto a reconstruction, and baking the result.

The shell sits in final world space at Hunyuan3D's own orientation - nothing
between reconstruction and export rotates it (spec §2.3) - so the camera that
looks at the front of the mesh is the same camera the reference image was
framed by, and the reference's pixels can be projected straight back on.

Per-view UVs are computed here in Python rather than with
bpy.ops.uv.project_from_view. That operator needs a VIEW_3D area and its poll
fails under --background, which is the only way this module is ever run.
world_to_camera_view() does the same arithmetic, handles orthographic cameras
explicitly, and works headless.
"""
import bpy
from bpy_extras.object_utils import world_to_camera_view

import npc_render

# The back view's framing. Free, unlike the front's - step 'back' renders the
# image at this camera and step 'bake' samples it at the same one, so any
# value works as long as the two agree. Both read this constant, so they
# cannot disagree; npc_render.frame_camera's own default is where the number
# came from.
BACK_MARGIN = 1.25

# The back render's size in pixels. Square, because a projection camera's
# frame is square only when the render is - see square_render().
BACK_RENDER_PX = 1024


def square_render(size):
    """Make the scene's render square at `size`. Returns the scene.

    Load-bearing, not tidiness. Camera.view_frame(), which world_to_camera_view
    calls, derives the frame's aspect from the scene's render resolution. A
    non-square render gives a non-square frame and stretches every projected UV
    along one axis - silently, and only visibly once the texture is on the
    model.
    """
    scene = bpy.context.scene
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    return scene


def projection_camera(obj, angle_deg, margin):
    """The camera a view is both rendered at and sampled through.

    npc_render.frame_camera unchanged - it already takes the margin as a
    parameter, and spec §4.2's whole point is that the projection camera is
    not new code. Wrapped only so callers name what they are doing.
    """
    return npc_render.frame_camera(obj, angle_deg, margin)


def project_uvs(obj, camera, name):
    """Write one UV layer holding `obj`'s screen position in `camera`.

    Per LOOP, because a UV layer is indexed by loop - but computed per vertex
    and shared, since the projection depends only on the vertex position and
    world_to_camera_view is the expensive part of this loop. A dense shell has
    roughly six loops per vertex.

    Returns the layer's name.
    """
    scene = bpy.context.scene
    bpy.context.view_layer.update()
    mesh = obj.data
    layer = mesh.uv_layers.get(name) or mesh.uv_layers.new(name=name)

    matrix = obj.matrix_world
    projected = [None] * len(mesh.vertices)
    for index, vertex in enumerate(mesh.vertices):
        position = world_to_camera_view(scene, camera, matrix @ vertex.co)
        projected[index] = (position.x, position.y)

    data = layer.data
    for loop in mesh.loops:
        data[loop.index].uv = projected[loop.vertex_index]
    return layer.name
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m unittest test.test_3d_texture -v`
Expected: PASS, 5 tests.

- [ ] **Step 5: Commit**

```bash
git add blender/npc_texture.py test/test_3d_texture.py
git commit -m "feat: project a camera's view onto a mesh as a UV layer"
```

---

### Task 3: The atlas unwrap, the projection material, and the bake

§8.2 step 1's Blender half: unwrap, project, bake, export. At the end of this task a grey fixture GLB comes out coloured.

**Files:**
- Modify: `blender/npc_texture.py`
- Create: `blender/texture_npc.py`
- Modify: `test/test_3d_texture.py`

**Interfaces:**
- Consumes: `npc_texture.square_render`, `projection_camera`, `project_uvs` (Task 2); `npc_mesh.clear_scene`, `import_glb`, `join`, `export_glb`; `npc_render.setup`, `aim_lights`, `ENGINES`.
- Produces:
  - `npc_texture.atlas_uvs(obj, name="atlas")` -> island count (int)
  - `npc_texture.load_view(path)` -> `bpy.types.Image`
  - `npc_texture.projection_material(obj, front, back=None)` -> `bpy.types.Material`
  - `npc_texture.bake_atlas(obj, size, path, samples=1, margin_px=8)` -> `bpy.types.Image`
  - `npc_texture.finish_material(obj, image, keep="atlas")` -> None
  - `npc_texture.render_back(obj, path, size=BACK_RENDER_PX, engine, samples)` -> None
  - `blender/texture_npc.py` CLI: `SHELL OUTDIR --stem NAME --step {back,bake} [--front PATH --front-margin FLOAT] [--back PATH] [--size INT] [--samples INT] [--render-engine E] [--render-samples INT]`, reporting `LANCER3D {"step","files","texture","shell","size","islands","views","faces"}` for `bake` and `{"step","files","render","size"}` for `back`.

- [ ] **Step 1: Confirm `smart_project` runs headless**

The whole task rests on this operator and its poll has historically wanted a 3D view. Thirty seconds now, or a confusing failure later.

```bash
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
  --background --factory-startup --python-expr \
  "import bpy; bpy.ops.mesh.primitive_cylinder_add(); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); print('SMART', bpy.ops.uv.smart_project(angle_limit=1.15192)); bpy.ops.object.mode_set(mode='OBJECT'); print('LAYERS', [l.name for l in bpy.context.object.data.uv_layers])"
```

Expected: `SMART {'FINISHED'}` and a non-empty `LAYERS`.

If it raises a poll error instead, replace the `bpy.ops.uv.smart_project(...)` call in `atlas_uvs()` below with:

```python
        bpy.ops.uv.seams_from_islands()
        bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.002)
```

and say so in that function's docstring. Nothing else in this task changes.

- [ ] **Step 2: Write the failing tests**

Append to `test/test_3d_texture.py`, after `TestProjectedUVs` and before the `if __name__` block:

```python
def glb_document(path):
    """The JSON chunk of a binary glTF, as a dict.

    Parsed by hand rather than re-imported through Blender: the promise is
    that a consumer opening this file finds a texture in it, and the 12-byte
    header plus chunk table is small enough to read without a dependency.
    """
    data = path.read_bytes()
    if data[:4] != b"glTF":
        raise AssertionError("%s is not a binary glTF" % path)
    length = int.from_bytes(data[12:16], "little")
    if data[16:20] != b"JSON":
        raise AssertionError("%s's first chunk is not JSON" % path)
    return json.loads(data[20:20 + length].decode("utf-8"))


def glb_holds_an_image(path):
    document = glb_document(path)
    return bool(document.get("images")) and bool(document.get("materials"))


@unittest.skipUnless(BLENDER, "Blender not installed")
class TestBake(unittest.TestCase):
    """One front-only bake - the --no-back-view path, end to end in Blender."""

    SIZE = 64          # small on purpose: this is a Cycles bake in test time
    RED = (220, 30, 30, 255)

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.outdir = Path(cls._tmp.name)
        cls.front = cls.outdir / "apose_square.png"
        write_test_png(cls.front, 128, cls.RED)
        cls.report, cls.proc = run_blender(
            TEXTURE_SCRIPT, SHELL, cls.outdir, "--stem", STEM,
            "--step", "bake", "--front", cls.front,
            "--front-margin", "1.06", "--size", cls.SIZE)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def texture_path(self):
        return self.outdir / ("_%s Texture.png" % STEM)

    def test_it_exits_cleanly(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr[-3000:])

    def test_the_texture_is_written(self):
        self.assertTrue(self.texture_path().exists(),
                        sorted(p.name for p in self.outdir.iterdir()))
        self.assertGreater(self.texture_path().stat().st_size, 0)

    def test_the_texture_is_the_size_that_was_asked_for(self):
        width, height, _ = d3._png_read(self.texture_path())
        self.assertEqual((width, height), (self.SIZE, self.SIZE))

    def test_the_reference_colour_survives_the_bake(self):
        """Not 'a texture exists' - the RIGHT pixels, in colour.

        A flat red source must bake to a red atlas. Anything that inverts the
        colour management - a tone-mapped view transform, a linear buffer
        saved as sRGB - shows up here and nowhere else.
        """
        _, _, rows = d3._png_read(self.texture_path())
        opaque = [(row[x * 4], row[x * 4 + 1], row[x * 4 + 2])
                  for row in rows for x in range(self.SIZE)
                  if row[x * 4 + 3] > 16]
        self.assertTrue(opaque, "the atlas is entirely transparent")
        strong = [rgb for rgb in opaque
                  if rgb[0] > 150 and rgb[1] < 110 and rgb[2] < 110]
        self.assertGreater(
            len(strong), len(opaque) * 0.5,
            "most opaque texels should carry the source red, got %r"
            % (opaque[:5],))

    def test_the_shell_is_re_exported(self):
        path = self.outdir / ("_%s Shell.glb" % STEM)
        self.assertTrue(path.exists())
        self.assertGreater(path.stat().st_size, 0)

    def test_the_exported_glb_embeds_a_material_and_an_image(self):
        self.assertTrue(glb_holds_an_image(self.outdir / ("_%s Shell.glb" % STEM)))

    def test_the_exported_glb_carries_exactly_one_uv_set(self):
        """The projection layers are working data and must not ship."""
        document = glb_document(self.outdir / ("_%s Shell.glb" % STEM))
        for mesh in document["meshes"]:
            for primitive in mesh["primitives"]:
                attributes = [k for k in primitive["attributes"]
                              if k.startswith("TEXCOORD")]
                with self.subTest(attributes=attributes):
                    self.assertEqual(attributes, ["TEXCOORD_0"])

    def test_the_report_names_both_temporaries(self):
        """generate-3d.py moves exactly these into place; it must not guess."""
        self.assertEqual(self.report["texture"], "_%s Texture.png" % STEM)
        self.assertEqual(self.report["shell"], "_%s Shell.glb" % STEM)

    def test_the_report_says_which_views_were_used(self):
        self.assertEqual(self.report["views"], ["front"])

    def test_the_atlas_unwrap_produced_islands(self):
        self.assertGreater(self.report["islands"], 0)

    def test_nothing_unprefixed_is_written(self):
        """This stage rewrites a deliverable. Nothing lands under a
        deliverable's name until generate-3d.py moves it there."""
        self.assertEqual(
            sorted(p.name for p in self.outdir.iterdir()
                   if not p.name.startswith("_")
                   and p.name != "apose_square.png"),
            [])
```

- [ ] **Step 3: Run them to verify they fail**

Run: `python -m unittest test.test_3d_texture.TestBake -v`
Expected: FAIL with `no LANCER3D report line` — `blender/texture_npc.py` does not exist, and Blender exits non-zero on a missing `--python` file.

- [ ] **Step 4: Add the unwrap, the material and the bake to `npc_texture.py`**

Append to `blender/npc_texture.py`:

```python
def _activate(obj):
    """Make `obj` the one selected, active object. Mirrors npc_mesh._activate."""
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def atlas_uvs(obj, name="atlas"):
    """Smart UV Project into a layer of its own. Returns the island count.

    This layer is the DELIVERABLE's UV layer - the one the baked atlas is
    addressed by, and the only one that survives finish_material(). The
    projection layers are working data.

    Made the active layer, because bpy.ops.object.bake writes through
    whichever layer is active, not through whichever the material's image node
    happens to prefer.
    """
    mesh = obj.data
    existing = mesh.uv_layers.get(name)
    if existing:
        mesh.uv_layers.remove(existing)
    layer = mesh.uv_layers.new(name=name)
    mesh.uv_layers.active = layer

    _activate(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.002)
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')

    # Reported rather than asserted on: spec §7.3 records that whether this
    # packs well on a 162k-face open shell is unquantified, and a number in
    # every run's report is how it stops being unquantified.
    return _uv_islands(obj, layer.name)


def _uv_islands(obj, layer_name):
    """How many connected pieces `layer_name` cuts the mesh into."""
    import bmesh
    mesh = bmesh.new()
    mesh.from_mesh(obj.data)
    mesh.faces.ensure_lookup_table()
    layer = mesh.loops.layers.uv.get(layer_name)
    if layer is None:
        mesh.free()
        return 0
    seen, islands = set(), 0
    for face in mesh.faces:
        if face.index in seen:
            continue
        islands += 1
        seen.add(face.index)
        stack = [face]
        while stack:
            current = stack.pop()
            for loop in current.loops:
                uv = loop[layer].uv
                for other in loop.edge.link_faces:
                    if other.index in seen:
                        continue
                    # Same island only when the shared edge is not a UV seam:
                    # some loop of `other` sits on this loop's UV corner.
                    if any((l[layer].uv - uv).length < 1e-6
                           for l in other.loops):
                        seen.add(other.index)
                        stack.append(other)
    mesh.free()
    return islands


def load_view(path):
    """One view's image, tagged sRGB - it is colour, not data."""
    image = bpy.data.images.load(str(path))
    image.colorspace_settings.name = 'sRGB'
    return image


def projection_material(obj, front, back=None):
    """A material whose emission is the views, blended by facing angle.

    Emission rather than a Principled BSDF: the bake must return the source
    pixels, not the source pixels lit by something. An EMIT bake has no light
    transport at all, which makes the result independent of the world, the
    lamps and the sample count.

    The blend is spec §4.3 step 3. With the front camera at -Y looking +Y, a
    surface's facing is its world normal's Y component alone: a dead-front
    surface has Ny = -1 and a dead-back surface Ny = +1, so

        t = 0.5 + 0.5 * Ny

    runs 0 at dead-front to 1 at dead-back. Smoothstepped, that is the mix.
    Deliberately not max(0, +-Ny), whose weights BOTH reach zero at the
    silhouette - which is exactly where a naive blend tears.

    Each side's weight is then multiplied by its own sampled alpha (§4.3 step
    4), so where the mesh's silhouette overshoots the image's, the texel falls
    to the other view instead of sampling backdrop. The alpha term is remapped
    to 0.001..1.0 rather than 0..1, so a texel outside BOTH images still
    resolves to its geometric mix instead of dividing by zero and going black.

    With no back view, t is unused and the front is emitted directly: spec
    §3.2's fallback is this function with one view, not a second code path.
    """
    material = bpy.data.materials.new("projection")
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    output = tree.nodes.new("ShaderNodeOutputMaterial")
    emission = tree.nodes.new("ShaderNodeEmission")
    tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])

    def view(image, uv_layer):
        uv = tree.nodes.new("ShaderNodeUVMap")
        uv.uv_map = uv_layer
        texture = tree.nodes.new("ShaderNodeTexImage")
        texture.image = image
        texture.extension = 'EXTEND'
        texture.interpolation = 'Linear'
        tree.links.new(uv.outputs["UV"], texture.inputs["Vector"])
        return texture

    front_texture = view(front, "proj_front")
    obj.data.materials.clear()
    obj.data.materials.append(material)
    if back is None:
        tree.links.new(front_texture.outputs["Color"], emission.inputs["Color"])
        return material

    back_texture = view(back, "proj_back")

    def maths(operation, a=None, b=None, value_a=None, value_b=None,
              value_c=None):
        node = tree.nodes.new("ShaderNodeMath")
        node.operation = operation
        for index, value in ((0, value_a), (1, value_b), (2, value_c)):
            if value is not None:
                node.inputs[index].default_value = value
        for index, socket in ((0, a), (1, b)):
            if socket is not None:
                tree.links.new(socket, node.inputs[index])
        return node

    geometry = tree.nodes.new("ShaderNodeNewGeometry")
    split = tree.nodes.new("ShaderNodeSeparateXYZ")
    tree.links.new(geometry.outputs["Normal"], split.inputs["Vector"])

    # t = smoothstep(0, 1, 0.5 + 0.5 * Ny)
    half = maths('MULTIPLY_ADD', a=split.outputs["Y"],
                 value_b=0.5, value_c=0.5)
    t = maths('SMOOTHSTEP', a=half.outputs["Value"],
              value_b=0.0, value_c=1.0)
    one_minus_t = maths('SUBTRACT', value_a=1.0, b=t.outputs["Value"])

    def weight(geometric, alpha):
        floored = maths('MULTIPLY_ADD', a=alpha, value_b=0.999, value_c=0.001)
        return maths('MULTIPLY', a=geometric, b=floored.outputs["Value"])

    front_weight = weight(one_minus_t.outputs["Value"],
                          front_texture.outputs["Alpha"])
    back_weight = weight(t.outputs["Value"], back_texture.outputs["Alpha"])
    total = maths('ADD', a=front_weight.outputs["Value"],
                  b=back_weight.outputs["Value"])

    def scaled(texture, weight_node):
        share = maths('DIVIDE', a=weight_node.outputs["Value"],
                      b=total.outputs["Value"])
        node = tree.nodes.new("ShaderNodeVectorMath")
        node.operation = 'SCALE'
        tree.links.new(texture.outputs["Color"], node.inputs[0])
        tree.links.new(share.outputs["Value"], node.inputs["Scale"])
        return node

    added = tree.nodes.new("ShaderNodeVectorMath")
    added.operation = 'ADD'
    tree.links.new(scaled(front_texture, front_weight).outputs["Vector"],
                   added.inputs[0])
    tree.links.new(scaled(back_texture, back_weight).outputs["Vector"],
                   added.inputs[1])
    tree.links.new(added.outputs["Vector"], emission.inputs["Color"])
    return material


def bake_atlas(obj, size, path, samples=1, margin_px=8):
    """Bake the projection material's emission to a PNG. Returns the image.

    CYCLES because bpy.ops.object.bake does not exist for EEVEE, and CPU
    because a headless run cannot assume a GL context - the same trade
    npc_render's engine parameter documents.

    view_transform 'Standard' is load-bearing. Blender's default is a tone
    map, and save_render() applies it: without this, a bake of a flat #DC1E1E
    comes back visibly washed out and nothing in the pipeline would say why.
    """
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.render.bake.margin = margin_px
    scene.render.bake.use_clear = True
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '8'

    image = bpy.data.images.new("atlas", size, size, alpha=True)
    tree = obj.data.materials[0].node_tree
    target = tree.nodes.new("ShaderNodeTexImage")
    target.image = image
    # The bake writes into whichever image node is ACTIVE and reads through
    # whichever UV layer is active. Both are set explicitly; neither defaults
    # to what this needs.
    for node in tree.nodes:
        node.select = False
    target.select = True
    tree.nodes.active = target

    _activate(obj)
    bpy.ops.object.bake(type='EMIT', use_clear=True, margin=margin_px)

    image.save_render(filepath=str(path), scene=scene)
    return image


def finish_material(obj, image, keep="atlas"):
    """Replace the projection rig with a plain textured Principled.

    The deliverable must not carry the rig: three UV layers and a node graph
    referencing two source PNGs that live in the NPC's 3d/ folder would export
    as a GLB with dangling image references and ambiguous texture coordinates.
    What ships is one UV layer, one material, one image.
    """
    mesh = obj.data
    for layer in [l for l in mesh.uv_layers if l.name != keep]:
        mesh.uv_layers.remove(layer)
    mesh.uv_layers.active = mesh.uv_layers[keep]

    material = bpy.data.materials.new("textured")
    material.use_nodes = True
    tree = material.node_tree
    principled = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    texture = tree.nodes.new("ShaderNodeTexImage")
    texture.image = image
    tree.links.new(texture.outputs["Color"], principled.inputs["Base Color"])
    mesh.materials.clear()
    mesh.materials.append(material)


def render_back(obj, path, size=BACK_RENDER_PX, engine='BLENDER_EEVEE',
                samples=16):
    """Render `obj`'s 180-degree view - the image ComfyUI edits into a back.

    Rendered at BACK_MARGIN, which the bake step also samples at, so the
    generated back view is registered to the mesh by construction (spec §2.2)
    and the projection that reads it back needs no calibration.

    Lit through npc_render's own key and fill rather than flat: the edit model
    is given the shell's form to paint onto, and a silhouette carries none.
    """
    _, lights = npc_render.setup(engine, size, samples)
    npc_render.aim_lights(lights, 180)
    camera = projection_camera(obj, 180, BACK_MARGIN)
    try:
        bpy.context.scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
    finally:
        bpy.data.objects.remove(camera, do_unlink=True)
```

- [ ] **Step 5: Write the headless entry point**

Create `blender/texture_npc.py`:

```python
"""Texture one assembled NPC's shell from its own reference image.

Invoked headless by generate-3d.py, twice per NPC:

    blender --background --factory-startup --python blender/texture_npc.py -- \\
        <Shell.glb> <outdir> --stem "<Name>" --step back

    blender --background --factory-startup --python blender/texture_npc.py -- \\
        <Shell.glb> <outdir> --stem "<Name>" --step bake \\
        --front <apose_square.png> --front-margin 1.06 [--back <back.png>]

Two launches because a ComfyUI round trip sits between them (spec §4.1), and
`assemble` is deliberately one offline run with no network.

Reports on stdout as a single machine-readable line, the same contract
assemble_npc.py has and for the same two readers:

    LANCER3D {"step": "bake", "files": [...], ...}

Everything it writes is underscore-prefixed. This stage REWRITES an existing
deliverable, unlike rigging, so the caller moves the temporaries into place
only once the whole stage has succeeded - a crash mid-bake must not leave a
corrupt Shell.glb where a good one was (spec §5.3).
"""
import argparse
import json
import os
import sys
import traceback
from pathlib import Path

# Blender does not put a --python script's own directory on sys.path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import npc_mesh  # noqa: E402  (must follow the sys.path line)
import npc_render  # noqa: E402
import npc_texture  # noqa: E402


def parse_argv(argv):
    p = argparse.ArgumentParser(prog="texture_npc.py")
    p.add_argument("shell", type=Path, help="the assembled Shell.glb")
    p.add_argument("outdir", type=Path, help="where the results are written")
    p.add_argument("--stem", required=True, help="the NPC's filename stem")
    p.add_argument("--step", required=True, choices=("back", "bake"),
                   help="'back' renders the shell's 180-degree view for "
                        "ComfyUI to edit; 'bake' projects and bakes")
    p.add_argument("--front", type=Path, default=None,
                   help="the reference image - apose_square.png (step bake)")
    p.add_argument("--front-margin", type=float, default=None,
                   help="the front camera's ortho margin. Passed in rather "
                        "than restated here: it must equal square_apose()'s "
                        "own 1 + APOSE_MARGIN, and one definition of that "
                        "number is the only way it stays true")
    p.add_argument("--back", type=Path, default=None,
                   help="the painted back view (step bake). Without it the "
                        "front is projected alone - spec §3.2's fallback")
    p.add_argument("--size", type=int, default=2048,
                   help="atlas size in pixels (default: %(default)s)")
    p.add_argument("--samples", type=int, default=1,
                   help="Cycles samples for the bake (default: %(default)s); "
                        "an EMIT bake has no light transport, so 1 is exact")
    p.add_argument("--render-engine", default="BLENDER_EEVEE",
                   choices=npc_render.ENGINES,
                   help="engine for the back render (default: %(default)s); "
                        "CYCLES needs no GL context and is what tests use")
    p.add_argument("--render-samples", type=int, default=16,
                   help="samples for the back render (default: %(default)s)")
    return p.parse_args(argv)


def script_argv():
    """Everything after Blender's own '--' separator."""
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def load_shell(path):
    npc_mesh.clear_scene()
    return npc_mesh.join(npc_mesh.import_glb(path), "shell")


def step_back(args):
    shell = load_shell(args.shell)
    name = "_back_render.png"
    npc_texture.render_back(shell, args.outdir / name,
                            engine=args.render_engine,
                            samples=args.render_samples)
    return {"files": [name], "render": name,
            "size": npc_texture.BACK_RENDER_PX}


def step_bake(args):
    if args.front is None or args.front_margin is None:
        raise SystemExit("--step bake needs --front and --front-margin")
    for path in (args.front, args.back):
        if path is not None and not path.exists():
            raise SystemExit("not found: %s" % path)

    shell = load_shell(args.shell)
    # Square first: the projection cameras' frames take their aspect from the
    # render resolution, and a non-square one stretches every UV.
    npc_texture.square_render(args.size)

    front = npc_texture.load_view(args.front)
    camera = npc_texture.projection_camera(shell, 0, args.front_margin)
    npc_texture.project_uvs(shell, camera, "proj_front")
    bpy.data.objects.remove(camera, do_unlink=True)

    back = None
    views = ["front"]
    if args.back is not None:
        back = npc_texture.load_view(args.back)
        camera = npc_texture.projection_camera(
            shell, 180, npc_texture.BACK_MARGIN)
        npc_texture.project_uvs(shell, camera, "proj_back")
        bpy.data.objects.remove(camera, do_unlink=True)
        views.append("back")

    islands = npc_texture.atlas_uvs(shell)
    npc_texture.projection_material(shell, front, back)

    texture_name = "_%s Texture.png" % args.stem
    image = npc_texture.bake_atlas(shell, args.size, args.outdir / texture_name,
                                   samples=args.samples)
    npc_texture.finish_material(shell, image)

    shell_name = "_%s Shell.glb" % args.stem
    npc_mesh.export_glb([shell], args.outdir / shell_name)

    return {
        "files": [texture_name, shell_name],
        "texture": texture_name,
        "shell": shell_name,
        "size": args.size,
        "islands": islands,
        "views": views,
        "faces": len(shell.data.polygons),
    }


def main():
    args = parse_argv(script_argv())
    if not args.shell.exists():
        raise SystemExit("not found: %s" % args.shell)
    args.outdir.mkdir(parents=True, exist_ok=True)

    report = step_back(args) if args.step == "back" else step_bake(args)
    report["step"] = args.step
    print("LANCER3D " + json.dumps(report))


if __name__ == "__main__":
    # A --python script's own uncaught exception does not make Blender exit
    # non-zero - only SystemExit does. The same backstop assemble_npc.py has,
    # and it matters more here: the caller decides whether to overwrite a good
    # Shell.glb based on this process's return code.
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        sys.exit(1)
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python -m unittest test.test_3d_texture -v`
Expected: PASS, 16 tests.

Two failures are worth naming in advance:

- `test_the_reference_colour_survives_the_bake` failing with washed-out values means the view transform is being applied — confirm `scene.view_settings.view_transform = 'Standard'` is set *before* `save_render`.
- Everything transparent means the atlas UVs did not reach the bake — confirm `mesh.uv_layers.active` is the atlas layer at bake time, and that `atlas_uvs()` ran after `project_uvs()`, not before.

- [ ] **Step 7: Commit**

```bash
git add blender/npc_texture.py blender/texture_npc.py test/test_3d_texture.py
git commit -m "feat: unwrap, project one view and bake it to a texture atlas"
```

---

### Task 4: The `texture` stage, front-only

§8.2 step 1's Python half. After this task `python generate-3d.py --id ... --stage texture --no-back-view` produces a coloured `Shell.glb` with no ComfyUI involvement at all.

**Files:**
- Modify: `generate-3d.py`
- Modify: `test/test_3d_cli.py`

**Interfaces:**
- Consumes: `blender/texture_npc.py`'s CLI and report (Task 3); `square_apose`, `find_blender`, `parse_report`, `node_of`, `append_dossier_3d` (existing).
- Produces:
  - `FRONT_MARGIN` (float, `1 + APOSE_MARGIN`), `TEXTURE_SCRIPT` (Path), `BACKVIEW_WORKFLOW` (Path)
  - `STAGES == ("apose", "mesh", "assemble", "texture")`
  - `texture_command(blender, args, folder, stem, shell, step, front=None, back=None)` -> list[str]
  - `run_texture_step(args, folder, stem, shell, step, front=None, back=None)` -> dict
  - `reference_image(folder)` -> Path
  - `stage_texture(comfy, args, subject, folder, stem, entry=None, portrait=None)` -> dict
  - `generate_back_view(...)` — a placeholder that raises until Task 7
  - `dossier_3d_section(files, workflows, stance, back_stance=None)`
  - `args.texture` (bool, default True), `args.texture_size` (int, 2048), `args.back_view` (bool, default True), `args.back_image` (Path|None)

- [ ] **Step 1: Write the failing tests**

Append to `test/test_3d_cli.py`:

```python
class TestTextureFlags(unittest.TestCase):
    def test_texture_is_a_stage(self):
        self.assertEqual(d3.STAGES, ("apose", "mesh", "assemble", "texture"))

    def test_all_four_stages_by_default(self):
        self.assertEqual(d3.parse_args([]).stage, list(d3.STAGES))

    def test_texture_runs_in_isolation(self):
        self.assertEqual(d3.parse_args(["--stage", "texture"]).stage, ["texture"])

    def test_texturing_is_on_by_default(self):
        """Unlike --rig. This is the point of the exercise, not an experiment."""
        self.assertTrue(d3.parse_args([]).texture)

    def test_no_texture_turns_it_off(self):
        self.assertFalse(d3.parse_args(["--no-texture"]).texture)

    def test_no_texture_leaves_the_stage_list_alone(self):
        """should_skip() compares the stage set against STAGES. Dropping
        'texture' from it would quietly stop a --no-texture batch skipping
        NPCs that already have a 3d/ folder."""
        self.assertEqual(d3.parse_args(["--no-texture"]).stage, list(d3.STAGES))

    def test_no_texture_with_stage_texture_is_refused(self):
        with self.assertRaises(SystemExit):
            d3.parse_args(["--stage", "texture", "--no-texture"])

    def test_the_atlas_defaults_to_2048(self):
        self.assertEqual(d3.parse_args([]).texture_size, 2048)

    def test_the_atlas_size_is_settable(self):
        self.assertEqual(d3.parse_args(["--texture-size", "4096"]).texture_size,
                         4096)

    def test_the_back_view_is_on_by_default(self):
        self.assertTrue(d3.parse_args([]).back_view)

    def test_no_back_view_turns_it_off(self):
        self.assertFalse(d3.parse_args(["--no-back-view"]).back_view)


class TestFrontMargin(unittest.TestCase):
    def test_it_is_squared_aposes_own_margin(self):
        """Spec §4.2 says 1.12; square_apose() has always used 1.06. The two
        framings are the same rule, so the camera takes the constant the image
        was actually built with - derived, never restated."""
        self.assertAlmostEqual(d3.FRONT_MARGIN, 1 + d3.APOSE_MARGIN)

    def test_it_reaches_the_blender_command(self):
        command = d3.texture_command(
            Path("blender.exe"), d3.parse_args([]), Path("/3d"), "Name",
            Path("/3d/Name Shell.glb"), "bake", front=Path("/3d/sq.png"))
        self.assertEqual(command[command.index("--front-margin") + 1],
                         str(d3.FRONT_MARGIN))


class TestTextureCommand(unittest.TestCase):
    def setUp(self):
        self.args = d3.parse_args([])
        self.shell = Path("/3d/Name Shell.glb")

    def build(self, step, **kwargs):
        return d3.texture_command(Path("blender.exe"), self.args, Path("/3d"),
                                  "Name", self.shell, step, **kwargs)

    def test_the_back_step_names_the_script_and_the_step(self):
        command = self.build("back")
        self.assertIn(str(d3.TEXTURE_SCRIPT), command)
        self.assertEqual(command[command.index("--step") + 1], "back")

    def test_the_back_step_passes_no_front(self):
        self.assertNotIn("--front", self.build("back"))

    def test_the_bake_step_passes_the_front_and_the_size(self):
        command = self.build("bake", front=Path("/3d/sq.png"))
        self.assertEqual(command[command.index("--front") + 1],
                         str(Path("/3d/sq.png")))
        self.assertEqual(command[command.index("--size") + 1], "2048")

    def test_the_bake_step_omits_back_when_there_is_none(self):
        self.assertNotIn("--back", self.build("bake", front=Path("/3d/sq.png")))

    def test_the_bake_step_passes_back_when_there_is_one(self):
        command = self.build("bake", front=Path("/3d/sq.png"),
                             back=Path("/3d/back.png"))
        self.assertEqual(command[command.index("--back") + 1],
                         str(Path("/3d/back.png")))

    def test_the_stem_reaches_the_command_unsplit(self):
        """A two-word name must arrive as one argv element, not two."""
        command = d3.texture_command(
            Path("blender.exe"), self.args, Path("/3d"), "Jules Sokolova",
            self.shell, "back")
        self.assertIn("Jules Sokolova", command)


class TestTextureDossier(unittest.TestCase):
    def test_the_texture_file_is_listed(self):
        body = d3.dossier_3d_section(
            ["Name Shell.glb", "Name Texture.png"], [Path("A.json")], "standing")
        self.assertIn("- `3d/Name Texture.png`", body)

    def test_a_back_stance_is_recorded_when_there_was_one(self):
        body = d3.dossier_3d_section(
            ["Name Shell.glb"], [Path("A.json")], "standing",
            back_stance="back to the viewer")
        self.assertIn("back to the viewer", body)

    def test_no_back_row_without_a_back_view(self):
        body = d3.dossier_3d_section(
            ["Name Shell.glb"], [Path("A.json")], "standing")
        self.assertNotIn("Back-view stance", body)


class TestTextureContainment(unittest.TestCase):
    """Spec §5.3: a texture failure costs the texture and nothing else."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self._tmp.name)
        self.shell = self.folder / "Name Shell.glb"
        self.shell.write_bytes(b"the good shell")
        (self.folder / "apose_square.png").write_bytes(b"not really a png")
        self.args = d3.parse_args(["--no-back-view"])

    def tearDown(self):
        self._tmp.cleanup()

    def test_a_failed_bake_leaves_the_shell_untouched(self):
        with mock.patch.object(d3, "run_texture_step",
                               side_effect=RuntimeError("bake exploded")):
            with self.assertRaises(RuntimeError):
                d3.stage_texture(None, self.args, None, self.folder, "Name")
        self.assertEqual(self.shell.read_bytes(), b"the good shell")

    def test_a_crash_after_a_partial_write_leaves_the_shell_untouched(self):
        def half_done(*a, **k):
            (self.folder / "_Name Texture.png").write_bytes(b"partial")
            raise RuntimeError("died during export")

        with mock.patch.object(d3, "run_texture_step", side_effect=half_done):
            with self.assertRaises(RuntimeError):
                d3.stage_texture(None, self.args, None, self.folder, "Name")
        self.assertEqual(self.shell.read_bytes(), b"the good shell")
        self.assertFalse((self.folder / "Name Texture.png").exists())

    def test_a_successful_bake_moves_both_temporaries_into_place(self):
        def succeed(*a, **k):
            (self.folder / "_Name Texture.png").write_bytes(b"the atlas")
            (self.folder / "_Name Shell.glb").write_bytes(b"the textured shell")
            return {"step": "bake", "texture": "_Name Texture.png",
                    "shell": "_Name Shell.glb", "size": 2048, "islands": 12,
                    "views": ["front"], "rigged": None,
                    "files": ["_Name Texture.png", "_Name Shell.glb"]}

        with mock.patch.object(d3, "run_texture_step", side_effect=succeed):
            report = d3.stage_texture(None, self.args, None, self.folder, "Name")
        self.assertEqual(self.shell.read_bytes(), b"the textured shell")
        self.assertEqual((self.folder / "Name Texture.png").read_bytes(),
                         b"the atlas")
        self.assertEqual(report["files"], ["Name Texture.png"])
        self.assertFalse((self.folder / "_Name Shell.glb").exists())

    def test_no_back_view_queues_no_comfyui_job(self):
        """comfy is None here: touching it at all is an AttributeError."""
        def succeed(*a, **k):
            (self.folder / "_Name Texture.png").write_bytes(b"a")
            (self.folder / "_Name Shell.glb").write_bytes(b"b")
            return {"texture": "_Name Texture.png", "shell": "_Name Shell.glb",
                    "views": ["front"], "files": []}

        with mock.patch.object(d3, "run_texture_step", side_effect=succeed):
            d3.stage_texture(None, self.args, None, self.folder, "Name")

    def test_a_missing_shell_names_the_stage_to_run(self):
        self.shell.unlink()
        with self.assertRaises(RuntimeError) as caught:
            d3.stage_texture(None, self.args, None, self.folder, "Name")
        self.assertIn("assemble", str(caught.exception))


class TestReferenceImage(unittest.TestCase):
    """The back-catalogue case: --stage texture on a folder built last week."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_an_existing_square_is_used_as_is(self):
        square = self.folder / "apose_square.png"
        square.write_bytes(b"already squared")
        self.assertEqual(d3.reference_image(self.folder), square)

    def test_it_is_rebuilt_from_apose_when_absent(self):
        """A pure function of apose.png - requiring --stage mesh to have run
        in this working copy would defeat the whole back-catalogue case."""
        with mock.patch.object(d3, "square_apose", return_value=800) as squared:
            (self.folder / "apose.png").write_bytes(b"a cutout")
            result = d3.reference_image(self.folder)
        squared.assert_called_once()
        self.assertEqual(result, self.folder / "apose_square.png")

    def test_neither_is_a_clear_failure(self):
        with self.assertRaises(RuntimeError) as caught:
            d3.reference_image(self.folder)
        self.assertIn("apose", str(caught.exception))


class TestTexturePreflight(unittest.TestCase):
    def test_the_texture_stage_checks_blender(self):
        args = d3.parse_args(["--stage", "texture"])
        args.blender = Path("nowhere/blender.exe")
        with self.assertRaises(SystemExit):
            d3.preflight(args)

    def test_no_texture_checks_nothing_it_will_not_open(self):
        d3.preflight(d3.parse_args(["--no-texture", "--stage", "apose"]))
```

- [ ] **Step 2: Run them to verify they fail**

Run: `python -m unittest test.test_3d_cli -v`
Expected: FAIL — `AttributeError: module 'gen3d' has no attribute 'FRONT_MARGIN'`, and `TestTextureFlags.test_texture_is_a_stage` failing on the three-element `STAGES`.

- [ ] **Step 3: Add the constants**

Replace the block at `generate-3d.py:230-236`:

```python
MESH_WORKFLOW = art.WORKFLOW_DIR / "Util_Image_to_Mesh_Hunyuan3D_v1.json"
RIG_WORKFLOW = art.WORKFLOW_DIR / "Util_Image_to_RiggedBody_SAM3D_v1.json"
BACKVIEW_WORKFLOW = art.WORKFLOW_DIR / "Util_BackView_QwenEdit_v1.json"
ASSEMBLE_SCRIPT = SCRIPT_DIR / "blender" / "assemble_npc.py"
TEXTURE_SCRIPT = SCRIPT_DIR / "blender" / "texture_npc.py"

# Named rather than numbered, so `--stage mesh` says what it does. The order
# is the dependency order: mesh needs apose's PNG, assemble needs mesh's GLBs,
# texture needs assemble's Shell.glb and mesh's apose_square.png.
STAGES = ("apose", "mesh", "assemble", "texture")
```

And add `FRONT_MARGIN` directly under `APOSE_MARGIN` (`generate-3d.py:410`), so the two are read together:

```python
APOSE_MARGIN = 0.06     # breathing room around the subject, as a fraction

# The projection camera's ortho margin, for texturing (spec §4.2).
#
# square_apose() squares the subject on max(w, h) * (1 + APOSE_MARGIN);
# frame_camera() sets ortho_scale to max(dimensions) * margin. They are the
# same rule - the subject's own bounds, squared on the longer side - so the
# camera that samples apose_square.png must use the constant that image was
# built with, and DERIVING it is the only way that stays true when
# APOSE_MARGIN moves.
#
# The design doc (§4.2) says 1.12. That is an error in the doc: APOSE_MARGIN
# has been 0.06 since it was introduced, never 0.12, so the matching margin is
# 1.06.
FRONT_MARGIN = 1 + APOSE_MARGIN
```

- [ ] **Step 4: Extend the dossier section**

Replace `dossier_3d_section` and `append_dossier_3d` (`generate-3d.py:342-382`):

```python
def dossier_3d_section(files, workflows, stance, back_stance=None):
    """The '## 3D' block: what was built, and everything needed to rebuild it.

    The dossier's existing property is that it records enough to reproduce its
    own output - the seed, the tables, both prompts verbatim. The 3D output is
    reproduced from the workflow graphs and the forced stances instead, so
    those are what this records. The back-view stance appears only when a back
    view was actually generated: recording a prompt that never ran would
    describe a file that is not there.
    """
    lines = [
        "## 3D",
        "",
        "Built by `generate-3d.py` on %s." % time.strftime("%Y-%m-%d"),
        "",
    ]
    lines += ["- `3d/%s`" % name for name in files] or ["- _(none built)_"]
    lines += [
        "",
        "### Reproduced by",
        "",
        "| | |",
        "|---|---|",
    ]
    lines += ["| Workflow | `%s` |" % Path(w).name for w in workflows]
    lines += ["| A-pose stance | %s |" % stance]
    if back_stance:
        lines += ["| Back-view stance | %s |" % back_stance]
    lines += [""]
    return "\n".join(lines)


def append_dossier_3d(path, files, workflows, stance, back_stance=None):
    """Add or REPLACE the dossier's '## 3D' section.

    Replace, because a --overwrite re-run would otherwise stack a second
    section under the first and the dossier would stop describing what is
    actually on disk - which is the only thing it is for.
    """
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    cut = text.find(DOSSIER_MARKER)
    if cut != -1:
        text = text[:cut]
    body = dossier_3d_section(files, workflows, stance, back_stance)
    path.write_text("%s\n\n%s" % (text.rstrip("\n"), body), encoding="utf-8")
```

- [ ] **Step 5: Add the stage**

Insert a new section immediately after `stage_assemble()` (`generate-3d.py:953`):

```python
# --------------------------------------------------------------------------
# Stage 3: texturing
# --------------------------------------------------------------------------


def texture_command(blender, args, folder, stem, shell, step,
                    front=None, back=None):
    """The full argv for one headless texture run.

    Split out from run_texture_step() for the same reason assemble_command()
    is split out: an unrecognised flag on the far side of Blender's '--'
    separator is argparse's problem inside the script, minutes later.
    """
    command = [
        str(blender), "--background", "--factory-startup",
        "--python", str(TEXTURE_SCRIPT), "--",
        str(shell), str(folder), "--stem", stem, "--step", step,
    ]
    if step == "bake":
        command += ["--front", str(front),
                    "--front-margin", str(FRONT_MARGIN),
                    "--size", str(args.texture_size)]
        if back is not None:
            command += ["--back", str(back)]
    return command


def run_texture_step(args, folder, stem, shell, step, front=None, back=None):
    """One headless Blender launch. Returns its report.

    A seam of its own so the containment tests can fail the Blender half
    without a Blender.
    """
    blender = find_blender(args.blender)
    if not TEXTURE_SCRIPT.exists():
        raise SystemExit("texture script not found: %s" % TEXTURE_SCRIPT)
    command = texture_command(blender, args, folder, stem, shell, step,
                              front, back)
    proc = subprocess.run(command, capture_output=True, text=True,
                          timeout=args.timeout)
    if proc.returncode != 0:
        raise RuntimeError("Blender texturing (%s) failed (%d):\n%s"
                           % (step, proc.returncode, proc.stderr[-2000:]))
    return parse_report(proc.stdout)


def reference_image(folder):
    """The squared A-pose the reconstruction actually saw.

    Rebuilt from apose.png when absent rather than refused: it is a pure
    function of apose.png, and requiring --stage mesh to have run in THIS
    working copy would defeat the back-catalogue case that is the whole reason
    texture is a stage of its own (spec §4.1).
    """
    square = folder / "apose_square.png"
    if square.exists():
        return square
    apose = folder / "apose.png"
    if not apose.exists():
        raise RuntimeError(
            "no apose_square.png or apose.png in %s - texturing needs the "
            "image the reconstruction was built from" % folder)
    square_apose(apose, square)
    return square


def stage_texture(comfy, args, subject, folder, stem, entry=None,
                  portrait=None):
    """Project the reference image onto the shell and bake it. -> the report.

    Reads Shell.glb and apose_square.png off disk rather than rebuilding
    geometry, so an NPC whose 3d/ folder predates this stage can be textured
    with `--stage texture` alone.

    Nothing is moved into place until every step has succeeded. This stage
    REWRITES a deliverable, which is the one thing rigging never had to do,
    and a crash mid-bake must not leave a corrupt Shell.glb where a good one
    was (spec §5.3).
    """
    shell = folder / ("%s Shell.glb" % stem)
    if not shell.exists():
        raise RuntimeError(
            "no %s in %s - run --stage assemble first" % (shell.name, folder))
    front = reference_image(folder)

    back = None
    back_stance = None
    if args.back_image is not None:
        back = args.back_image
        print("    back view supplied: %s" % back.name, flush=True)
    elif args.back_view:
        back, back_stance = generate_back_view(
            comfy, args, subject, folder, shell, stem, entry, portrait)

    print("    baking a %dpx atlas ..." % args.texture_size, flush=True)
    report = run_texture_step(args, folder, stem, shell, "bake", front, back)

    # Everything above wrote only underscore-prefixed files. This is the one
    # point at which a good deliverable is replaced, and os.replace is atomic
    # on the same filesystem on every platform this runs on.
    texture = folder / ("%s Texture.png" % stem)
    os.replace(folder / report["texture"], texture)
    os.replace(folder / report["shell"], shell)

    report["files"] = [texture.name]
    report["back_stance"] = back_stance
    print("      -> %s (%d UV islands, %s)"
          % (texture.name, report.get("islands", 0),
             " + ".join(report.get("views", []))))
    return report


def generate_back_view(comfy, args, subject, folder, shell, stem, entry,
                       portrait):
    """Render the shell's 180-degree view and have ComfyUI paint it.

    Filled in by Task 7. Until then the generated back view is unreachable and
    --no-back-view is the only supported route.
    """
    raise RuntimeError("the generated back view is not implemented yet - "
                       "pass --no-back-view")
```

- [ ] **Step 6: Add the flags**

In the "which stages" group, after `--bind` (`generate-3d.py:1008`):

```python
    stage.add_argument("--texture", dest="texture", action="store_true",
                       default=True,
                       help="project the A-pose reference onto the shell and "
                            "bake it (the default). Unlike --rig this is ON: "
                            "it is the point of the exercise, not an "
                            "experiment")
    stage.add_argument("--no-texture", dest="texture", action="store_false",
                       help="skip texturing entirely, restoring the grey "
                            "deliverables this tool used to produce")
    stage.add_argument("--texture-size", type=int, default=2048,
                       metavar="PIXELS",
                       help="baked atlas size (default: %(default)s). The "
                            "shell is ~1.9 m2, so 2048 is ~0.7 mm/texel "
                            "against the reference's own ~1.3 mm/px")
    stage.add_argument("--no-back-view", dest="back_view",
                       action="store_false", default=True,
                       help="do not generate a back view: project the front "
                            "alone and wrap its silhouette colours around. No "
                            "ComfyUI job runs, and the result is exact in "
                            "front and plausible behind")
    stage.add_argument("--back-image", type=Path, default=None, metavar="PATH",
                       help="a back view you already have, instead of "
                            "generating one. It must be a render of the "
                            "shell's own 180-degree view - anything else will "
                            "not register")
```

- [ ] **Step 7: Add the validation**

`args.stage` is `None` until it is resolved, so capture whether it was given explicitly. Replace the block at `generate-3d.py:1066-1073`:

```python
    explicit_stage = args.stage is not None
    if args.stage is None:
        # --image supplies what stage apose exists to produce, so the default
        # set drops it. Named stages are left exactly as given: `--image X
        # --stage mesh` is a caller deliberately stopping before assembly.
        args.stage = [s for s in STAGES if s != "apose"] if args.image \
            else list(STAGES)
    elif args.image and "apose" in args.stage:
        p.error("--image supplies the A-pose and --stage apose renders one - "
                "pass only one of them")

    # --no-texture does NOT edit args.stage. should_skip() compares the stage
    # set against STAGES to decide whether the caller has narrowed the run,
    # and dropping 'texture' here would quietly stop a --no-texture batch
    # skipping NPCs that already have a 3d/ folder.
    if explicit_stage and not args.texture and "texture" in args.stage:
        p.error("--stage texture asks for the texture stage and --no-texture "
                "suppresses it - pass only one of them")
    if args.back_image is not None:
        if not args.back_image.exists():
            p.error("--back-image not found: %s" % args.back_image)
        if not args.back_view:
            p.error("--back-image supplies a back view and --no-back-view "
                    "asks for none - pass only one of them")
        if not args.texture:
            p.error("--back-image is only used by the texture stage, which "
                    "--no-texture switches off")
```

Extend `preflight` (`generate-3d.py:1134`):

```python
    if "texture" in args.stage and args.texture:
        find_blender(args.blender)
        if not TEXTURE_SCRIPT.exists():
            raise SystemExit("texture script not found: %s" % TEXTURE_SCRIPT)
        if args.back_view and args.back_image is None \
                and not BACKVIEW_WORKFLOW.exists():
            raise SystemExit("Workflow not found: %s" % BACKVIEW_WORKFLOW)
```

- [ ] **Step 8: Rework `main()`'s tail**

The dossier is now written after texturing, not inside the assemble branch. Replace `main()`'s body from `if "assemble" in args.stage:` through the `print("    ! no dossier ...")` line:

```python
            stem = npc_gen._safe(subject.name)
            built = []
            workflows = [MESH_WORKFLOW, RIG_WORKFLOW]
            back_stance = None

            if "assemble" in args.stage:
                print("    assembling ...", flush=True)
                if subject.height is None:
                    print("    ! %s - using SAM3DBody's estimate"
                          % ("no --height-m given" if entry is None
                             else "%s names no height" % subject.name),
                          file=sys.stderr)
                report = stage_assemble(args, folder, stem, base, shell,
                                        subject.height)
                built = list(report["files"])
                for name in built:
                    print("      -> %s" % name)
                if report.get("rig_error"):
                    warned += 1

            if "texture" in args.stage and args.texture:
                # Contained exactly as rigging is (spec §5.3) and for the same
                # reason: the untextured shell, the STL and the turnarounds
                # are already correct and already on disk, and throwing the
                # NPC away because the texture failed would be the opposite of
                # containment. This is deliberately NOT the per-NPC handler
                # below - that one counts the NPC as failed, and an NPC with
                # every grey deliverable intact did not fail.
                try:
                    print("    texturing ...", flush=True)
                    textured = stage_texture(
                        comfy, args, subject, folder, stem, entry,
                        (folder_path / ("%s Portrait.png" % stem))
                        if folder_path else None)
                    built += textured["files"]
                    back_stance = textured.get("back_stance")
                    if back_stance:
                        workflows = workflows + [BACKVIEW_WORKFLOW]
                except (Exception, SystemExit) as exc:
                    warned += 1
                    print("    ! texturing failed: %s" % exc, file=sys.stderr)

            # A standalone run tracks nothing by design: there is no NPC whose
            # dossier this belongs in, and inventing one would put a record of
            # an experiment into the campaign's own notes.
            if folder_path is not None and built:
                dossier = folder_path / ("%s.md" % stem)
                if dossier.exists():
                    append_dossier_3d(dossier, built, workflows,
                                      APOSE_STANCE, back_stance)
                else:
                    # Not an error: an NPC folder moved by hand into Foundry
                    # keeps its art and loses nothing by having no dossier.
                    print("    ! no dossier at %s - skipping the 3D section"
                          % dossier.name, file=sys.stderr)
```

`warned` now counts two kinds of warning, so the summary line must stop claiming they are all rigging:

```python
    # warned counts contained failures - a rig that did not bind, a texture
    # that did not bake. Either way the NPC's grey deliverables shipped, which
    # is why it is not counted as failed.
    rig_note = " (%d with a warning)" % warned if warned else ""
```

- [ ] **Step 9: Let the texture stage run without `apose.png`**

`main()` currently refuses any run that is not `--stage apose` and has no `apose.png`:

```python
            else:
                apose = folder / "apose.png"
                if not apose.exists():
                    raise RuntimeError(
                        "no apose.png in %s - run --stage apose first" % folder)
```

For `--stage texture` that is a coupling to a file the stage does not use — `reference_image()` needs `apose_square.png`, and only falls back to `apose.png`. Leaving this would half-undo the back-catalogue case. Narrow it:

```python
            else:
                apose = folder / "apose.png"
                # The texture stage reads apose_square.png, and rebuilds it
                # from apose.png only if it has to (reference_image). A run
                # that is texturing an already-squared folder has no use for
                # apose.png, so requiring it here would refuse a folder that
                # is perfectly texturable.
                needs_apose = any(s in args.stage for s in ("mesh", "assemble"))
                if needs_apose and not apose.exists():
                    raise RuntimeError(
                        "no apose.png in %s - run --stage apose first" % folder)
```

- [ ] **Step 10: Update the existing four-stage assertions**

Two tests in `test_3d_cli.py` enumerate the stages and now describe a set that no longer exists. They are correct tests of a rule that has not changed, so update the data, not the assertion:

- `TestSkipping.test_all_three_stages_explicitly_still_skip` (`test_3d_cli.py:138`) passes `--stage apose --stage mesh --stage assemble` and expects `should_skip` to be True. With four stages that set is now *narrowed*, so it correctly returns False. Add `--stage texture` to the argv and rename the method to `test_all_four_stages_explicitly_still_skip`.
- Anything asserting `len(d3.STAGES) == 3` or listing the three names — `grep -n "assemble\"\]" test/test_3d_cli.py` finds them.

```bash
grep -n "apose\", \"mesh\", \"assemble\"\|three stages\|three_stages" test/test_3d_cli.py
```

- [ ] **Step 11: Run the tests to verify they pass**

Run: `python -m unittest test.test_3d_cli -v`
Expected: PASS — the whole file, not just the new classes. `TestStageFlag`, `TestSkipping`, `TestRunSummary` and `TestStandalone` all read `STAGES` or `main()`'s tail and must still pass with four stages.

- [ ] **Step 12: Run it for real, front-only**

```bash
python generate-3d.py --id npc-jules-sokolova-40213 --stage texture --no-back-view
```

Expected: `-> Jules Sokolova Texture.png (N UV islands, front)`, and `3d/Jules Sokolova Shell.glb` grows.

Open the GLB and confirm it is coloured and that the front reads as the reference image. **Record the UV island count and the file sizes** — Task 9's docs quote them, and spec §7.3 asks for exactly this number.

- [ ] **Step 13: Commit**

```bash
git add generate-3d.py test/test_3d_cli.py
git commit -m "feat: a texture stage, projecting the A-pose reference front-only"
```

---

### Task 5: The back render, and a back view you supply

Step A of §4.1's table, plus `--back-image`. Separate from Task 6 because it needs no ComfyUI and no new workflow: after this task `--back-image` gives a full two-view bake with a back view made any way at all, which is also how Task 7's blend gets exercised without a GPU.

**Files:**
- Modify: `generate-3d.py`
- Modify: `test/test_3d_texture.py`
- Modify: `test/test_3d_cli.py`

**Interfaces:**
- Consumes: `npc_texture.render_back` and `texture_npc.py --step back` (Task 3); `run_texture_step`, `stage_texture` (Task 4).
- Produces: `check_image` also validating `args.back_image`; `stage_texture` honouring it; `3d/_back_render.png` on disk.

- [ ] **Step 1: Write the failing tests**

Append to `test/test_3d_texture.py`:

```python
@unittest.skipUnless(BLENDER, "Blender not installed")
class TestBackRender(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.outdir = Path(cls._tmp.name)
        cls.report, cls.proc = run_blender(
            TEXTURE_SCRIPT, SHELL, cls.outdir, "--stem", STEM,
            "--step", "back", "--render-engine", "CYCLES",
            "--render-samples", "1")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_it_exits_cleanly(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr[-3000:])

    def test_the_back_render_is_written(self):
        path = self.outdir / "_back_render.png"
        self.assertTrue(path.exists(),
                        sorted(p.name for p in self.outdir.iterdir()))
        self.assertGreater(path.stat().st_size, 0)

    def test_it_is_square_and_the_size_the_module_declares(self):
        width, height, _ = d3._png_read(self.outdir / "_back_render.png")
        self.assertEqual(width, height)
        self.assertEqual(width, 1024)

    def test_it_keeps_its_alpha(self):
        """film_transparent, so the silhouette is a usable mask - and so
        _png_read, which only accepts RGBA, can read it back at all."""
        width, _, rows = d3._png_read(self.outdir / "_back_render.png")
        alphas = {row[x * 4 + 3] for row in rows for x in range(0, width, 8)}
        self.assertIn(0, alphas)
        self.assertTrue(any(a > 200 for a in alphas))

    def test_the_report_names_it(self):
        self.assertEqual(self.report["render"], "_back_render.png")
        self.assertEqual(self.report["step"], "back")


@unittest.skipUnless(BLENDER, "Blender not installed")
class TestTwoViewBake(unittest.TestCase):
    """A bake with both views wired up. The blend's exact shape is Task 7's;
    this is that both images reach the atlas at all."""

    SIZE = 64

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.outdir = Path(cls._tmp.name)
        front = cls.outdir / "front.png"
        back = cls.outdir / "back.png"
        write_test_png(front, 128, (220, 30, 30, 255))
        write_test_png(back, 128, (30, 30, 220, 255))
        cls.report, cls.proc = run_blender(
            TEXTURE_SCRIPT, SHELL, cls.outdir, "--stem", STEM,
            "--step", "bake", "--front", front, "--front-margin", "1.06",
            "--back", back, "--size", cls.SIZE)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_it_exits_cleanly(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr[-3000:])

    def test_the_report_lists_both_views(self):
        self.assertEqual(self.report["views"], ["front", "back"])

    def test_both_source_colours_reach_the_atlas(self):
        """A red front and a blue back on a cylinder: the atlas must carry
        both, or the blend collapsed to one view."""
        _, _, rows = d3._png_read(self.outdir / ("_%s Texture.png" % STEM))
        texels = [(row[x * 4], row[x * 4 + 1], row[x * 4 + 2])
                  for row in rows for x in range(self.SIZE)
                  if row[x * 4 + 3] > 16]
        self.assertTrue(any(r > b + 40 for r, _, b in texels), "no red texels")
        self.assertTrue(any(b > r + 40 for r, _, b in texels), "no blue texels")

    def test_neither_view_swamps_the_other(self):
        """A smooth blend, not a hard switch: on a symmetric cylinder the two
        must come out comparable in area."""
        _, _, rows = d3._png_read(self.outdir / ("_%s Texture.png" % STEM))
        texels = [(row[x * 4], row[x * 4 + 2]) for row in rows
                  for x in range(self.SIZE) if row[x * 4 + 3] > 16]
        red = sum(1 for r, b in texels if r > b)
        blue = len(texels) - red
        self.assertGreater(min(red, blue), len(texels) * 0.2)
```

Append to `test/test_3d_cli.py`:

```python
class TestBackImageFlag(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self._tmp.name)
        self.back = self.folder / "back.png"
        self.back.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 32)
        self.shell = self.folder / "Name Shell.glb"
        self.shell.write_bytes(b"shell")
        (self.folder / "apose_square.png").write_bytes(b"square")

    def tearDown(self):
        self._tmp.cleanup()

    def test_no_back_image_by_default(self):
        self.assertIsNone(d3.parse_args([]).back_image)

    def test_the_path_is_read_onto_the_args(self):
        self.assertEqual(
            d3.parse_args(["--back-image", str(self.back)]).back_image,
            self.back)

    def test_a_missing_back_image_fails_at_parse_time(self):
        with self.assertRaises(SystemExit):
            d3.parse_args(["--back-image", str(self.folder / "nope.png")])

    def test_back_image_with_no_back_view_is_refused(self):
        with self.assertRaises(SystemExit):
            d3.parse_args(["--back-image", str(self.back), "--no-back-view"])

    def test_back_image_with_no_texture_is_refused(self):
        with self.assertRaises(SystemExit):
            d3.parse_args(["--back-image", str(self.back), "--no-texture"])

    def test_a_non_png_is_refused_before_the_gpu_sees_it(self):
        junk = self.folder / "junk.png"
        junk.write_bytes(b"this is not a png at all")
        args = d3.parse_args(["--back-image", str(junk)])
        with self.assertRaises(SystemExit):
            d3.check_image(args, [self.folder])

    def test_an_opaque_rgb_png_is_accepted(self):
        """Unlike --image. A generated back view is very often opaque RGB,
        which _png_read refuses by design and Blender loads without
        complaint."""
        args = d3.parse_args(["--back-image", str(self.back)])
        d3.check_image(args, [self.folder])

    def test_two_npcs_and_one_back_image_is_refused(self):
        args = d3.parse_args(["--back-image", str(self.back)])
        with self.assertRaises(SystemExit):
            d3.check_image(args, [self.folder, self.folder])

    def test_a_supplied_back_view_reaches_the_bake_and_queues_nothing(self):
        args = d3.parse_args(["--back-image", str(self.back)])
        seen = {}

        def record(a, folder, stem, shell, step, front=None, back=None):
            seen["step"], seen["back"] = step, back
            (folder / "_Name Texture.png").write_bytes(b"a")
            (folder / "_Name Shell.glb").write_bytes(b"b")
            return {"texture": "_Name Texture.png", "shell": "_Name Shell.glb",
                    "views": ["front", "back"], "files": []}

        with mock.patch.object(d3, "run_texture_step", side_effect=record):
            d3.stage_texture(None, args, None, self.folder, "Name")
        self.assertEqual(seen["step"], "bake")
        self.assertEqual(seen["back"], self.back)
```

- [ ] **Step 2: Run them to verify they fail**

Run: `python -m unittest test.test_3d_cli.TestBackImageFlag test.test_3d_texture -v`
Expected: `TestBackImageFlag` fails on `check_image` not knowing about `back_image`. `TestBackRender` and `TestTwoViewBake` should already **pass** — both paths were written in Task 3. If they do not, fix `texture_npc.py` or `npc_texture.py` here rather than deferring; they are this task's real subject.

- [ ] **Step 3: Teach `check_image` about `--back-image`**

`check_image` already runs once, before the per-NPC loop, for exactly this class of mistake. Extend it (`generate-3d.py:668`) — the early `if not args.image: return` guard has to move down, because a `--back-image` run may have no `--image` at all:

```python
def check_image(args, folders):
    """A SystemExit naming why --image or --back-image cannot be used.

    Every one of these is cheap to check and expensive to discover later: a
    reconstruction takes minutes on the GPU and answers a wrong input with a
    plausible-looking wrong mesh rather than an error. Checked once here,
    against the run's target folders, rather than inside the per-NPC loop that
    catches SystemExit and turns a global mistake into one failure per NPC.
    """
    if args.back_image is not None:
        if len(folders) != 1:
            raise SystemExit(
                "--back-image is one person's back view, but %d NPCs are "
                "selected - narrow the run with --id" % len(folders))
        # Deliberately NOT _png_read: a generated back view is very often an
        # opaque RGB PNG, which that reader refuses by design, and Blender
        # loads any PNG it is handed. The signature is the whole check.
        if args.back_image.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            raise SystemExit("--back-image is not a PNG: %s" % args.back_image)

    if not args.image:
        return

    if len(folders) != 1:
        raise SystemExit(
            "--image is one person's A-pose, but %d NPCs are selected - "
            "narrow the run with --id, or reconstruct the image on its own "
            "with --out DIR" % len(folders))
    ...
```

The rest of the function is unchanged, from its `# Broad on purpose:` comment onward.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest test.test_3d_cli test.test_3d_texture -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add generate-3d.py test/test_3d_cli.py test/test_3d_texture.py
git commit -m "feat: render the shell's back view, and accept one you supply"
```

---

### Task 6: The Qwen back-view workflow

§4.4. The graph, and the job builder that patches its three image slots and its prompt.

**Files:**
- Create: `workflows/api/Util_BackView_QwenEdit_v1.json`
- Modify: `generate-3d.py`
- Modify: `test/test_3d_workflows.py`
- Modify: `test/test_3d_cli.py`

**Interfaces:**
- Consumes: `art.load_api_workflow`, `art.WorkflowError`, `node_of`, `apose_npc`, `npc_gen.build_prompts`, `npc_gen.split_backdrop` (all existing).
- Produces:
  - `BACKVIEW_STANCE` (str), `REAR_FACING_PHRASES` (tuple)
  - `backview_npc(entry)` -> dict, `backview_prompt(entry)` -> str
  - `rear_facing(entry)` -> bool
  - `backview_slots(graph)` -> `{"encode": id, "image1": id, "image2": id, "image3": id|None, "save": id}`
  - `build_backview_job(template, refs, prompt, prefix, seed=None)` -> graph dict, where `refs` is `(back_render_ref, apose_ref, portrait_ref_or_None)`

- [ ] **Step 1: Capture the live schema, and build the graph from ComfyUI's own template**

This is the one place in the plan where a graph is written from evidence rather than from the design doc, because a wrong input key validates and then fails at execution — `test_no_input_is_a_nested_object` exists because that already happened once on this project.

With ComfyUI running on `127.0.0.1:8000`:

```bash
python -c "
import json, urllib.request
info = json.loads(urllib.request.urlopen('http://127.0.0.1:8000/object_info', timeout=60).read())
for name in ('TextEncodeQwenImageEditPlus','UNETLoader','CLIPLoader','VAELoader',
             'ModelSamplingAuraFlow','CFGNorm','KSampler','EmptySD3LatentImage',
             'VAEEncode','VAEDecode','SaveImage','LoadImage'):
    node = info.get(name)
    print('==', name, '' if node else 'MISSING')
    if not node:
        continue
    for section in ('required','optional'):
        for key, value in (node['input'].get(section) or {}).items():
            print('   %-8s %-24s %s' % (section, key, str(value)[:150]))
"
```

Then open the ComfyUI editor, load its bundled **Qwen-Image-Edit 2509** template, set the three `LoadImage` nodes and every model name to what the schema above actually offers, and export it as **API format** to `workflows/api/Util_BackView_QwenEdit_v1.json`.

Reconcile the exported graph against these requirements before continuing:

1. Exactly one `KSampler`. The job builder reaches everything else through it.
2. Exactly one `SaveImage`, patched through `node_of()`.
3. The positive `TextEncodeQwenImageEditPlus` — the one linked to `KSampler.positive` — has `image1`, `image2` and `image3` inputs, each a `["<node id>", 0]` link to a **distinct** `LoadImage`.
4. `image1` is the image being **edited**: the back render. This is what makes the output registered to the mesh (spec §2.2), so it must be the slot the model treats as the edit target.
5. `_meta.title` on the three `LoadImage` nodes reads `back render (patched)`, `A-pose reference (patched)` and `portrait (patched, optional)`, in that order. Titles are documentation only — the code addresses them by link, never by title.
6. Every `class_type` in the graph ships with ComfyUI. No custom node pack — the same constraint `test_no_custom_node_pack_is_required` enforces on the other two graphs.

If `/object_info` lists `image3` as **required** rather than optional, note that in the graph's `_meta` and change `build_backview_job` below to point `image3` at the A-pose `LoadImage` when there is no portrait, instead of deleting the input — and change `test_no_portrait_drops_the_slot_and_its_node` to assert that instead.

- [ ] **Step 2: Write the failing tests**

In `test/test_3d_workflows.py`, extend the header:

```python
from test.helpers import REPO, load_3d
from test.workflow_schema import (
    dynamic_combo_choices, expected_inputs, object_info, server_is_up)

d3 = load_3d()

MESH = REPO / "workflows" / "api" / "Util_Image_to_Mesh_Hunyuan3D_v1.json"
RIG = REPO / "workflows" / "api" / "Util_Image_to_RiggedBody_SAM3D_v1.json"
BACKVIEW = REPO / "workflows" / "api" / "Util_BackView_QwenEdit_v1.json"
GRAPHS = {"mesh": json.loads(MESH.read_text(encoding="utf-8")),
          "rig": json.loads(RIG.read_text(encoding="utf-8")),
          "backview": json.loads(BACKVIEW.read_text(encoding="utf-8"))}

# The two reconstruction graphs. Three of TestGraphShape's checks are about
# image-to-mesh specifically - one LoadImage, one SaveGLB, a native node set
# that does not include the Qwen stack - and the back view answers to none of
# them. It gets TestBackViewGraph instead.
MESH_GRAPHS = {k: v for k, v in GRAPHS.items() if k in ("mesh", "rig")}
```

Then change three methods of `TestGraphShape` to iterate `MESH_GRAPHS.items()` rather than `GRAPHS.items()`: `test_each_graph_has_exactly_one_load_image`, `test_each_graph_has_exactly_one_save_glb`, and `test_no_custom_node_pack_is_required`. Leave every other method on `GRAPHS`, so the back view is still checked for dangling links, nested-object inputs and live schema agreement.

Add:

```python
class TestBackViewGraph(unittest.TestCase):
    """§4.4. Three LoadImage nodes and two encoders, so node_of() cannot
    address them - which is why generate-3d.py follows links from KSampler."""

    graph = GRAPHS["backview"]

    def test_exactly_one_ksampler(self):
        """The anchor everything else is reached from."""
        samplers = [n for n, d in self.graph.items()
                    if d["class_type"] == "KSampler"]
        self.assertEqual(len(samplers), 1)

    def test_exactly_one_save_image(self):
        saves = [n for n, d in self.graph.items()
                 if d["class_type"] == "SaveImage"]
        self.assertEqual(len(saves), 1)

    def test_three_load_image_nodes(self):
        loads = [n for n, d in self.graph.items()
                 if d["class_type"] == "LoadImage"]
        self.assertEqual(len(loads), 3)

    def test_the_slots_resolve(self):
        slots = d3.backview_slots(self.graph)
        for key in ("encode", "image1", "image2", "image3", "save"):
            with self.subTest(key=key):
                self.assertIn(slots[key], self.graph)

    def test_every_image_slot_is_a_distinct_load_image(self):
        slots = d3.backview_slots(self.graph)
        ids = [slots["image1"], slots["image2"], slots["image3"]]
        self.assertEqual(len(set(ids)), 3)
        for node_id in ids:
            with self.subTest(node=node_id):
                self.assertEqual(self.graph[node_id]["class_type"], "LoadImage")

    def test_the_encoder_is_the_positive_conditioning(self):
        slots = d3.backview_slots(self.graph)
        sampler = next(d for d in self.graph.values()
                       if d["class_type"] == "KSampler")
        self.assertEqual(sampler["inputs"]["positive"][0], slots["encode"])

    def test_the_negative_is_a_different_node(self):
        """Two TextEncodeQwenImageEditPlus nodes is the whole reason node_of()
        cannot be used here. If that ever stops being true, the simpler helper
        should come back."""
        sampler = next(d for d in self.graph.values()
                       if d["class_type"] == "KSampler")
        self.assertNotEqual(sampler["inputs"]["positive"][0],
                            sampler["inputs"]["negative"][0])

    def test_no_custom_node_pack_is_required(self):
        """Spec §2.1 and §2.2: everything here ships with ComfyUI."""
        for nid, node in self.graph.items():
            with self.subTest(node=nid):
                self.assertNotIn(".", node["class_type"])
```

And append to `test/test_3d_cli.py`:

```python
class TestBackViewPrompt(unittest.TestCase):
    def setUp(self):
        self.entry = manifest_entry(21)

    def test_the_stance_is_replaced_not_appended(self):
        prompt = d3.backview_prompt(self.entry)
        self.assertIn(d3.BACKVIEW_STANCE, prompt)
        self.assertNotIn(d3.APOSE_STANCE, prompt)

    def test_the_hands_are_still_empty(self):
        """backview_npc builds on apose_npc, which empties them - a figure
        holding a carbine cannot hold a back-facing A-pose either."""
        npc = d3.backview_npc(self.entry)
        self.assertEqual(npc["Weapon"], "")
        self.assertEqual(npc["Gear"], "")

    def test_the_stance_composes_as_a_bullet(self):
        """Lowercase, no trailing period, no pronoun placeholders - the
        template supplies '{Subject} {is_are} {stance}, both feet in frame'."""
        self.assertEqual(d3.BACKVIEW_STANCE[0], d3.BACKVIEW_STANCE[0].lower())
        self.assertFalse(d3.BACKVIEW_STANCE.endswith("."))
        self.assertNotIn("{", d3.BACKVIEW_STANCE)

    def test_the_rest_of_the_character_is_unchanged(self):
        apose = d3.apose_npc(self.entry)
        back = d3.backview_npc(self.entry)
        for key in ("Outfit", "Headgear", "Hair", "Glow colour"):
            if key in apose:
                with self.subTest(key=key):
                    self.assertEqual(apose[key], back[key])


class TestRearFacing(unittest.TestCase):
    def entry_with(self, backdrop):
        entry = manifest_entry(22)
        entry["traits"]["Backdrop"] = backdrop
        return entry

    def test_a_seen_from_behind_shot_is_rear_facing(self):
        self.assertTrue(d3.rear_facing(self.entry_with(
            "A character portrait seen from behind || She is on a roof.")))

    def test_a_rear_view_shot_is_rear_facing(self):
        self.assertTrue(d3.rear_facing(self.entry_with(
            "A dynamic, three-quarter rear-view character portrait || "
            "She glances back.")))

    def test_a_back_to_the_viewer_scene_is_rear_facing(self):
        self.assertTrue(d3.rear_facing(self.entry_with(
            "A dramatic low-angle character portrait || She stands, her back "
            "to the viewer, in the rain.")))

    def test_a_plain_portrait_is_not(self):
        self.assertFalse(d3.rear_facing(self.entry_with(
            "A half-body character portrait || She is in a corridor.")))

    def test_a_scene_that_merely_mentions_something_behind_her_is_not(self):
        """'behind {object}' describes the BACKDROP, not the camera. This is
        why the phrase list cannot just be 'behind'."""
        self.assertFalse(d3.rear_facing(self.entry_with(
            "A character portrait || She stands squared to the viewer, a ship "
            "descending directly behind her.")))

    def test_an_entry_with_no_backdrop_is_not(self):
        entry = manifest_entry(23)
        entry["traits"].pop("Backdrop", None)
        self.assertFalse(d3.rear_facing(entry))

    def test_a_standalone_run_has_no_entry_and_is_not(self):
        self.assertFalse(d3.rear_facing(None))

    def test_the_live_tables_contain_both_kinds(self):
        """Guards the phrase list against the tables being reworded: if a
        rewrite made every Backdrop read the same way to this, the third
        reference slot would silently stop being used - or start being used on
        front-facing portraits."""
        from test.helpers import load_generator
        gen = load_generator()
        tables = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")
        verdicts = {d3.rear_facing({"traits": {"Backdrop": b}})
                    for b in tables["Backdrop"]}
        self.assertEqual(verdicts, {True, False})


class TestBackViewJob(unittest.TestCase):
    def setUp(self):
        self.template = json.loads(
            d3.BACKVIEW_WORKFLOW.read_text(encoding="utf-8"))

    def build(self, portrait="p.png [input]"):
        return d3.build_backview_job(
            self.template, ("back.png [input]", "sq.png [input]", portrait),
            "a back view of her", "LancerNPCs/Crew/x/back", 7)

    def test_each_image_slot_is_patched(self):
        job = self.build()
        slots = d3.backview_slots(job)
        self.assertEqual(job[slots["image1"]]["inputs"]["image"],
                         "back.png [input]")
        self.assertEqual(job[slots["image2"]]["inputs"]["image"],
                         "sq.png [input]")
        self.assertEqual(job[slots["image3"]]["inputs"]["image"],
                         "p.png [input]")

    def test_the_prompt_is_patched(self):
        job = self.build()
        self.assertEqual(
            job[d3.backview_slots(job)["encode"]]["inputs"]["prompt"],
            "a back view of her")

    def test_the_output_prefix_is_patched(self):
        job = self.build()
        self.assertEqual(
            job[d3.node_of(job, "SaveImage")]["inputs"]["filename_prefix"],
            "LancerNPCs/Crew/x/back")

    def test_the_seed_reaches_the_sampler(self):
        sampler = next(d for d in self.build().values()
                       if d["class_type"] == "KSampler")
        self.assertEqual(sampler["inputs"]["seed"], 7)

    def test_no_portrait_drops_the_slot_and_its_node(self):
        """§4.4: the portrait is OMITTED when it is not rear-facing, not faked
        with a front view the model would read as the thing to copy."""
        job = self.build(portrait=None)
        slots = d3.backview_slots(job)
        self.assertIsNone(slots["image3"])
        self.assertNotIn("image3", job[slots["encode"]]["inputs"])
        loads = [n for n, d in job.items() if d["class_type"] == "LoadImage"]
        self.assertEqual(len(loads), 2)

    def test_the_template_on_disk_is_not_mutated(self):
        before = json.dumps(self.template, sort_keys=True)
        self.build()
        self.assertEqual(json.dumps(self.template, sort_keys=True), before)

    def test_a_graph_with_two_ksamplers_is_refused(self):
        graph = json.loads(json.dumps(self.template))
        sampler = next(n for n, d in graph.items()
                       if d["class_type"] == "KSampler")
        graph["9999"] = json.loads(json.dumps(graph[sampler]))
        with self.assertRaises(d3.art.WorkflowError):
            d3.backview_slots(graph)
```

- [ ] **Step 3: Run them to verify they fail**

Run: `python -m unittest test.test_3d_workflows test.test_3d_cli.TestBackViewPrompt test.test_3d_cli.TestRearFacing test.test_3d_cli.TestBackViewJob -v`
Expected: FAIL — `AttributeError: module 'gen3d' has no attribute 'backview_slots'`, and a `FileNotFoundError` at import if Step 1 was skipped.

- [ ] **Step 4: Write the stance and the rear-facing detection**

Add after `apose_npc()` (`generate-3d.py:110`):

```python
# The Stance the back view is rendered in. Spec §4.4.
#
# Written as an ordinary Stance bullet for the same reason APOSE_STANCE is -
# lowercase, no trailing period, no pronoun placeholders - so it composes with
# the token template's "{Subject} {is_are} {stance}, both feet in frame"
# exactly as a rolled bullet does.
#
# It describes the SAME jig from the other side: everything that made the
# A-pose a good reconstruction source - limbs clear of the torso, both feet in
# frame, squarely on to the camera - still holds, and only the facing changes.
BACKVIEW_STANCE = (
    "standing straight with the back squarely to the viewer and the face "
    "turned fully away, seen from directly behind, arms held slightly away "
    "from the sides with the palms facing backward, feet shoulder-width apart"
)


def backview_npc(entry):
    """apose_npc(), turned around.

    Built ON apose_npc rather than beside it so the two descriptions cannot
    drift: the emptied hands, the Height backfill and the migrate_traits pass
    are all decisions that belong to reconstruction, not to which way the
    figure faces, and restating them here would be a second thing to keep in
    step with the tables (§4.4).
    """
    npc = apose_npc(entry)
    npc["Stance"] = BACKVIEW_STANCE
    return npc


def backview_prompt(entry):
    """The token prompt the back view is edited toward."""
    return npc_gen.build_prompts(backview_npc(entry))[1]


# The Backdrop phrases that mean the rolled portrait shows the character's
# back. Read off the live tables, which compose a rear shot three ways: a
# "seen from behind" shot phrase, a "rear-view" one, and a scene that puts the
# subject's "back to the viewer" under a front-ish shot.
#
# Deliberately NOT a bare "behind": half the Backdrop table describes
# something standing behind the subject, which says nothing about the camera.
REAR_FACING_PHRASES = ("seen from behind", "rear-view", "rear view",
                       "back to the viewer")


def rear_facing(entry):
    """True when this NPC's rolled portrait is composed from behind.

    Where it is, the portrait is real evidence about the character's back -
    the fall of the hair, the print across the jacket, what is slung over the
    shoulders - and §4.4 gives it the third reference slot. Where it is not,
    the slot is omitted rather than filled with a front view, which the edit
    model would read as the thing to reproduce.
    """
    backdrop = (entry.get("traits") or {}).get("Backdrop", "") if entry else ""
    if not backdrop:
        return False
    shot, scene, _ = npc_gen.split_backdrop(backdrop)
    text = ("%s || %s" % (shot, scene)).lower()
    return any(phrase in text for phrase in REAR_FACING_PHRASES)
```

- [ ] **Step 5: Write the graph helpers**

Add beside `build_mesh_job` (`generate-3d.py:770`):

```python
def backview_slots(graph):
    """Where build_backview_job patches, found by following links.

    NOT node_of(). The back-view graph has three LoadImage nodes and two
    TextEncodeQwenImageEditPlus nodes - a positive and a negative - so
    addressing either class by class_type finds three or two and raises. The
    unique node is KSampler, and everything else hangs off it: its 'positive'
    input names the encoder, and the encoder's image1/2/3 inputs name the
    three loaders.

    This keeps the property node_of() exists for - a re-export from the
    ComfyUI editor renumbers every node and this still resolves - while
    failing just as loudly on a graph that is not the shape this code expects.
    """
    samplers = [n for n, d in graph.items()
                if d.get("class_type") == "KSampler"]
    if len(samplers) != 1:
        raise art.WorkflowError(
            "expected exactly one KSampler node, found %d" % len(samplers))
    positive = graph[samplers[0]]["inputs"].get("positive")
    if not isinstance(positive, list) or positive[0] not in graph:
        raise art.WorkflowError("the KSampler's positive input is not a link")
    encode = positive[0]

    slots = {"encode": encode, "save": node_of(graph, "SaveImage")}
    for key in ("image1", "image2", "image3"):
        ref = graph[encode]["inputs"].get(key)
        if ref is None:
            slots[key] = None
            continue
        if not isinstance(ref, list) or ref[0] not in graph:
            raise art.WorkflowError("%s.%s is not a link" % (encode, key))
        if graph[ref[0]]["class_type"] != "LoadImage":
            raise art.WorkflowError(
                "%s.%s points at a %s, not a LoadImage"
                % (encode, key, graph[ref[0]]["class_type"]))
        slots[key] = ref[0]
    if slots["image1"] is None or slots["image2"] is None:
        raise art.WorkflowError(
            "the back-view encoder needs image1 (the render being edited) and "
            "image2 (the A-pose reference)")
    return slots


def build_backview_job(template, refs, prompt, prefix, seed=None):
    """One queueable back-view job. The template is left untouched.

    `refs` is (back render, A-pose reference, portrait or None), in the slot
    order §4.4 fixes: the render being EDITED first, because that is what makes
    the result registered to the mesh; then the character's colours; then the
    optional rear-facing portrait.
    """
    graph = json.loads(json.dumps(template))
    slots = backview_slots(graph)
    back_ref, apose_ref, portrait_ref = refs

    graph[slots["image1"]]["inputs"]["image"] = back_ref
    graph[slots["image2"]]["inputs"]["image"] = apose_ref
    graph[slots["encode"]]["inputs"]["prompt"] = prompt
    graph[slots["save"]]["inputs"]["filename_prefix"] = prefix

    if portrait_ref is not None and slots["image3"] is not None:
        graph[slots["image3"]]["inputs"]["image"] = portrait_ref
    elif slots["image3"] is not None:
        # Omitted, not faked (§4.4). The input goes, and so does the loader it
        # was the only reference to - a node left dangling in an API-format
        # graph is executed anyway, and would load whatever placeholder the
        # template shipped with.
        orphan = slots["image3"]
        del graph[slots["encode"]]["inputs"]["image3"]
        if not any(isinstance(v, list) and v and v[0] == orphan
                   for node in graph.values()
                   for v in node["inputs"].values()):
            del graph[orphan]

    if seed is not None:
        for node in graph.values():
            if node.get("class_type") == "KSampler":
                node["inputs"]["seed"] = seed
    return graph
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python -m unittest test.test_3d_workflows test.test_3d_cli -v`
Expected: PASS. `TestAgainstLiveObjectInfo` now covers the back-view graph too and runs whenever the server is up — if it reports a missing or unknown input, fix the graph, not the test.

- [ ] **Step 7: Commit**

```bash
git add workflows/api/Util_BackView_QwenEdit_v1.json generate-3d.py \
        test/test_3d_workflows.py test/test_3d_cli.py
git commit -m "feat: a Qwen-Image-Edit back view, registered to the shell's own render"
```

---

### Task 7: Wire the generated back view into the stage

§4.1's steps A → B → C, joined up. After this task the default path — no flags — produces a two-view texture.

**Files:**
- Modify: `generate-3d.py`
- Modify: `test/test_3d_cli.py`

**Interfaces:**
- Consumes: `run_texture_step`, `reference_image` (Task 4); `build_backview_job`, `backview_prompt`, `rear_facing`, `BACKVIEW_STANCE`, `BACKVIEW_WORKFLOW` (Task 6); `upload_image`, `npc_gen.fetch`, `art.Comfy.images`, `art.load_api_workflow` (existing).
- Produces: `generate_back_view(comfy, args, subject, folder, shell, stem, entry, portrait)` -> `(Path, str)` — the back view and the stance that produced it. Replaces Task 4's placeholder.

- [ ] **Step 1: Write the failing tests**

Append to `test/test_3d_cli.py`:

```python
class TestGeneratedBackView(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self._tmp.name)
        (self.folder / "Name Shell.glb").write_bytes(b"shell")
        (self.folder / "apose_square.png").write_bytes(b"square")
        self.entry = manifest_entry(31)
        self.args = d3.parse_args([])
        self.subject = d3.subject_of(self.entry, self.args)

    def tearDown(self):
        self._tmp.cleanup()

    def run_stage(self, portrait=None, rear=False):
        """stage_texture with every outside edge mocked. -> (report, calls)."""
        calls = {"steps": [], "uploads": [], "jobs": []}
        self.entry["traits"]["Backdrop"] = (
            "A character portrait seen from behind || She is on a roof."
            if rear else "A half-body character portrait || She is inside.")

        def texture_step(a, folder, stem, shell, step, front=None, back=None):
            calls["steps"].append((step, front, back))
            if step == "back":
                (folder / "_back_render.png").write_bytes(b"render")
                return {"step": "back", "render": "_back_render.png",
                        "files": ["_back_render.png"]}
            (folder / "_Name Texture.png").write_bytes(b"atlas")
            (folder / "_Name Shell.glb").write_bytes(b"textured")
            return {"step": "bake", "texture": "_Name Texture.png",
                    "shell": "_Name Shell.glb", "views": ["front", "back"],
                    "islands": 9, "files": []}

        def upload(comfy, path, subfolder="lancer3d"):
            calls["uploads"].append(Path(path).name)
            return "%s [input]" % Path(path).name

        def fetch(comfy, image, target):
            Path(target).write_bytes(b"back view")
            return Path(target)

        def job(template, refs, prompt, prefix, seed=None):
            calls["jobs"].append({"refs": refs, "prompt": prompt,
                                  "prefix": prefix, "seed": seed})
            return {}

        comfy = mock.MagicMock()
        comfy.wait.return_value = {"outputs": {}}
        with mock.patch.object(d3, "run_texture_step", side_effect=texture_step), \
             mock.patch.object(d3, "upload_image", side_effect=upload), \
             mock.patch.object(d3.npc_gen, "fetch", side_effect=fetch), \
             mock.patch.object(d3.art.Comfy, "images",
                               return_value=[{"filename": "back_0001.png"}]), \
             mock.patch.object(d3, "build_backview_job", side_effect=job), \
             mock.patch.object(d3.time, "sleep"):
            report = d3.stage_texture(comfy, self.args, self.subject,
                                      self.folder, "Name", self.entry, portrait)
        return report, calls

    def test_the_back_render_runs_before_the_bake(self):
        _, calls = self.run_stage()
        self.assertEqual([step for step, _, _ in calls["steps"]],
                         ["back", "bake"])

    def test_the_generated_back_reaches_the_bake(self):
        _, calls = self.run_stage()
        bake = next(c for c in calls["steps"] if c[0] == "bake")
        self.assertEqual(Path(bake[2]).name, "back.png")

    def test_the_render_and_the_reference_are_both_uploaded(self):
        _, calls = self.run_stage()
        self.assertIn("_back_render.png", calls["uploads"])
        self.assertIn("apose_square.png", calls["uploads"])

    def test_the_render_is_the_first_slot(self):
        """§4.4: image1 is the image being EDITED, and that is what makes the
        result registered to the mesh."""
        _, calls = self.run_stage()
        self.assertEqual(calls["jobs"][0]["refs"][0], "_back_render.png [input]")

    def test_the_prompt_is_the_backview_prompt(self):
        _, calls = self.run_stage()
        self.assertEqual(calls["jobs"][0]["prompt"],
                         d3.backview_prompt(self.entry))

    def test_the_entrys_own_seed_is_used(self):
        _, calls = self.run_stage()
        self.assertEqual(calls["jobs"][0]["seed"], self.subject.seed)

    def test_a_rear_facing_portrait_is_uploaded_as_the_third_slot(self):
        portrait = self.folder / "Name Portrait.png"
        portrait.write_bytes(b"portrait")
        _, calls = self.run_stage(portrait=portrait, rear=True)
        self.assertIn("Name Portrait.png", calls["uploads"])
        self.assertIsNotNone(calls["jobs"][0]["refs"][2])

    def test_a_front_facing_portrait_is_not_used(self):
        portrait = self.folder / "Name Portrait.png"
        portrait.write_bytes(b"portrait")
        _, calls = self.run_stage(portrait=portrait, rear=False)
        self.assertNotIn("Name Portrait.png", calls["uploads"])
        self.assertIsNone(calls["jobs"][0]["refs"][2])

    def test_a_missing_portrait_file_is_not_an_error(self):
        """An NPC folder moved by hand into Foundry keeps its 3d/ and may have
        left the portrait behind. The slot is optional anyway."""
        _, calls = self.run_stage(portrait=self.folder / "gone.png", rear=True)
        self.assertIsNone(calls["jobs"][0]["refs"][2])

    def test_the_stance_is_reported_for_the_dossier(self):
        report, _ = self.run_stage()
        self.assertEqual(report["back_stance"], d3.BACKVIEW_STANCE)

    def test_the_intermediates_are_kept_on_disk(self):
        """Like _shell.glb: they are what you look at when a back comes out
        wrong."""
        self.run_stage()
        self.assertTrue((self.folder / "back.png").exists())
        self.assertTrue((self.folder / "_back_render.png").exists())

    def test_a_job_that_produces_no_image_is_a_clear_failure(self):
        with mock.patch.object(d3, "run_texture_step",
                               side_effect=lambda *a, **k: (
                                   (self.folder / "_back_render.png")
                                   .write_bytes(b"r")
                                   or {"render": "_back_render.png"})), \
             mock.patch.object(d3, "upload_image", return_value="x [input]"), \
             mock.patch.object(d3.art.Comfy, "images", return_value=[]), \
             mock.patch.object(d3.time, "sleep"):
            with self.assertRaises(RuntimeError) as caught:
                d3.stage_texture(mock.MagicMock(), self.args, self.subject,
                                 self.folder, "Name", self.entry)
        self.assertIn("no image", str(caught.exception))
```

- [ ] **Step 2: Run them to verify they fail**

Run: `python -m unittest test.test_3d_cli.TestGeneratedBackView -v`
Expected: FAIL with `RuntimeError: the generated back view is not implemented yet - pass --no-back-view`.

- [ ] **Step 3: Implement `generate_back_view`**

Replace Task 4's placeholder in `generate-3d.py`:

```python
def generate_back_view(comfy, args, subject, folder, shell, stem, entry,
                       portrait):
    """Render the shell's 180-degree view and have ComfyUI paint it.

    -> (the back view's path, the stance that produced it).

    The registration is structural, not prompted. What ComfyUI is given is a
    render of THIS mesh at the camera the bake will sample the result with, so
    whatever comes back lines up with the silhouette by construction - which
    is the only reason this works with ControlNetLoader's enum empty (§2.2).
    """
    print("    back render ...", flush=True)
    run_texture_step(args, folder, stem, shell, "back")
    render = folder / "_back_render.png"
    if not render.exists():
        raise RuntimeError("the back render produced no image")

    if not BACKVIEW_WORKFLOW.exists():
        raise SystemExit("Workflow not found: %s" % BACKVIEW_WORKFLOW)
    template = art.load_api_workflow(BACKVIEW_WORKFLOW)

    refs = [upload_image(comfy, render),
            upload_image(comfy, reference_image(folder)),
            None]
    # The portrait is evidence only when it was composed from behind (§4.4). A
    # missing file is not an error: an NPC folder moved by hand keeps its 3d/
    # and may have left the portrait behind, and the slot is optional.
    if entry is not None and portrait is not None and portrait.exists() \
            and rear_facing(entry):
        print("      portrait is rear-facing - using it as a third reference")
        refs[2] = upload_image(comfy, portrait)

    # A standalone --out run has no traits to build a prompt from, the same
    # gap that makes --out require --image. The stance alone is what is left
    # that is true about the figure.
    prompt = (backview_prompt(entry) if entry is not None
              else "the same figure seen from directly behind, %s"
                   % BACKVIEW_STANCE)
    prefix = "%s/%s/%s/back" % (npc_gen.COMFY_PREFIX,
                                subject.category, subject.slug)
    job = build_backview_job(template, tuple(refs), prompt, prefix,
                             subject.seed)

    print("    back view ...", flush=True)
    images = art.Comfy.images(comfy.wait(comfy.queue(job),
                                         timeout=args.timeout))
    if not images:
        raise RuntimeError("the back-view job produced no image")
    # --pause-3d, not --pause: Qwen-Image-Edit 2509 at fp8 is large and this
    # runs after two reconstructions in the same batch, which is exactly the
    # window spec §7.4 flags.
    time.sleep(args.pause_3d)

    back = npc_gen.fetch(comfy, images[0], folder / "back.png")
    print("      -> %s" % back.name)
    return back, BACKVIEW_STANCE
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest test.test_3d_cli -v`
Expected: PASS.

- [ ] **Step 5: Run it for real, both views**

```bash
python generate-3d.py --id npc-jules-sokolova-40213 --stage texture
```

Expected: `back render ...`, `back view ...`, then `-> Jules Sokolova Texture.png (N UV islands, front + back)`.

Open the GLB and turn it round. The front should read as the reference; the back should be plausible, and the transition should be a soft gradient rather than a hard seam.

If the machine OOMs here, that is spec §7.4 materialising and `--pause-3d 45` is the lever. **Record whether it was needed** — Task 9's docs say so either way.

- [ ] **Step 6: Commit**

```bash
git add generate-3d.py test/test_3d_cli.py
git commit -m "feat: generate the back view and blend it with the front"
```

---

### Task 8: The rigged GLB carries the texture

§8.2 step 3. `--rig` exports `Rigged.glb` inside `assemble`, which runs *before* `texture` — so as things stand a rigged export is written grey and never revisited.

**Files:**
- Modify: `blender/texture_npc.py`
- Modify: `generate-3d.py`
- Modify: `test/fixtures/3d/make_fixtures.py`
- Create: `test/fixtures/3d/rigged.glb`
- Modify: `test/test_3d_texture.py`
- Modify: `test/test_3d_cli.py`

**Interfaces:**
- Consumes: `npc_texture.finish_material` (Task 3); `npc_mesh.import_glb`, `armature_of`, `meshes_of`, `join`, `export_glb`.
- Produces: `texture_npc.py --rigged PATH` on `--step bake`, adding `"rigged"` to the report; `texture_command` passing it; `stage_texture` moving `_<stem> Rigged.glb` into place when it is there; a `rigged.glb` fixture.

- [ ] **Step 1: Add a rigged fixture**

The UV transfer below is loop-for-loop, so the test needs a rigged GLB that is genuinely the *same mesh* as `shell.glb`. `base.glb` is not — it is a 16-vertex cylinder, while `shell.glb` is that plus a 6-vertex speck, so their loop counts differ and pairing them would exercise the mismatch guard rather than the transfer.

This is what `make_fixtures.py` exists for. Add to `test/fixtures/3d/make_fixtures.py`, and extend its module docstring with a line for the new file:

```python
def make_rigged():
    """Stands in for the Rigged.glb `assemble --rig` writes.

    The SAME mesh as shell.glb - same cylinders, same order - bound to a
    small armature. That sameness is the point: assemble exports Shell.glb
    and Rigged.glb from one object, so the texture stage transfers the atlas
    UVs loop for loop, and a fixture that merely resembled the shell would
    test the mismatch guard instead of the transfer.
    """
    reset()
    jacket = cylinder("jacket", 0.20, 1.0, (0, 0, 0.5))
    speck = cylinder("speck", 0.01, 0.02, (0.6, 0, 0.5), vertices=6)

    bpy.ops.object.select_all(action='DESELECT')
    jacket.select_set(True)
    speck.select_set(True)
    bpy.context.view_layer.objects.active = jacket
    bpy.ops.object.join()

    bpy.ops.object.armature_add(location=(0, 0, 0))
    armature = bpy.context.active_object
    armature.name = "rig"
    bpy.ops.object.mode_set(mode='EDIT')
    root = armature.data.edit_bones[0]
    root.name = "hips"
    root.head, root.tail = (0, 0, 0), (0, 0, 1.0)
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')
    jacket.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(OUT / "rigged.glb"),
                              export_format='GLB', use_selection=True,
                              export_texcoords=False)
```

and call it from `__main__`, adding `"rigged.glb"` to the size-report loop. Then regenerate:

```bash
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
  --background --factory-startup --python test/fixtures/3d/make_fixtures.py
```

Expected: `wrote rigged.glb (N bytes)` on stderr, and `base.glb`/`shell.glb` unchanged in content.

- [ ] **Step 2: Write the failing tests**

Append to `test/test_3d_texture.py`:

```python
RIGGED = FIXTURES / "rigged.glb"


@unittest.skipUnless(BLENDER, "Blender not installed")
class TestRiggedCarriesTheTexture(unittest.TestCase):
    """rigged.glb is shell.glb's own mesh, bound - which is the relationship
    assemble --rig produces, and the one the loop-for-loop transfer needs."""

    SIZE = 64

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.outdir = Path(cls._tmp.name)
        front = cls.outdir / "front.png"
        write_test_png(front, 128, (220, 30, 30, 255))
        cls.report, cls.proc = run_blender(
            TEXTURE_SCRIPT, SHELL, cls.outdir, "--stem", STEM,
            "--step", "bake", "--front", front, "--front-margin", "1.06",
            "--size", cls.SIZE, "--rigged", RIGGED)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def rigged_path(self):
        return self.outdir / ("_%s Rigged.glb" % STEM)

    def test_it_exits_cleanly(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr[-3000:])

    def test_the_rigged_glb_is_re_exported(self):
        self.assertTrue(self.rigged_path().exists(),
                        sorted(p.name for p in self.outdir.iterdir()))

    def test_it_carries_the_texture(self):
        self.assertTrue(glb_holds_an_image(self.rigged_path()))

    def test_it_is_still_rigged(self):
        """A texture that costs the armature is not a win."""
        self.assertTrue(glb_document(self.rigged_path()).get("skins"))

    def test_the_report_names_it(self):
        self.assertEqual(self.report["rigged"], "_%s Rigged.glb" % STEM)

    def test_the_plain_shell_is_still_written(self):
        self.assertTrue((self.outdir / ("_%s Shell.glb" % STEM)).exists())


@unittest.skipUnless(BLENDER, "Blender not installed")
class TestRiggedMismatchIsRefused(unittest.TestCase):
    """A --rigged GLB that is not the same mesh must fail loudly, not
    silently texture the figure with someone else's unwrap."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.outdir = Path(cls._tmp.name)
        front = cls.outdir / "front.png"
        write_test_png(front, 64, (220, 30, 30, 255))
        # A deliberately wrong pairing: the base fixture as the SHELL, and the
        # shell fixture as the rigged copy. Different loop counts.
        cls.proc = subprocess.run(
            [str(BLENDER), "--background", "--factory-startup", "--python",
             str(TEXTURE_SCRIPT), "--", str(FIXTURES / "base.glb"),
             str(cls.outdir), "--stem", STEM, "--step", "bake",
             "--front", str(front), "--front-margin", "1.06", "--size", "32",
             "--rigged", str(SHELL)],
            capture_output=True, text=True, timeout=600)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_it_exits_non_zero(self):
        self.assertNotEqual(self.proc.returncode, 0)

    def test_it_says_which_two_did_not_match(self):
        self.assertIn("loops", self.proc.stderr + self.proc.stdout)
```

Add to `test/test_3d_cli.py`'s `TestTextureCommand`:

```python
    def test_a_rigged_glb_is_passed_when_rig_is_on_and_it_exists(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        folder = Path(tmp.name)
        (folder / "Name Rigged.glb").write_bytes(b"rigged")
        command = d3.texture_command(
            Path("blender.exe"), d3.parse_args(["--rig"]), folder, "Name",
            folder / "Name Shell.glb", "bake", front=folder / "sq.png")
        self.assertEqual(command[command.index("--rigged") + 1],
                         str(folder / "Name Rigged.glb"))

    def test_no_rigged_glb_without_rig(self):
        self.assertNotIn("--rigged", self.build("bake", front=Path("/3d/sq.png")))

    def test_no_rigged_glb_when_rig_was_asked_for_but_the_bind_failed(self):
        """--rig writes no Rigged.glb when the bind left vertices unweighted.
        Passing a path to a file that is not there would fail the whole
        texture stage over a rig that already failed on its own."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        folder = Path(tmp.name)
        command = d3.texture_command(
            Path("blender.exe"), d3.parse_args(["--rig"]), folder, "Name",
            folder / "Name Shell.glb", "bake", front=folder / "sq.png")
        self.assertNotIn("--rigged", command)
```

- [ ] **Step 3: Run them to verify they fail**

Run: `python -m unittest test.test_3d_texture.TestRiggedCarriesTheTexture test.test_3d_cli.TestTextureCommand -v`
Expected: FAIL — `unrecognized arguments: --rigged`, so no report line, and `ValueError: '--rigged' is not in list` from the command tests.

- [ ] **Step 4: Add `--rigged` to the bake step**

In `blender/texture_npc.py`, add the argument to `parse_argv`:

```python
    p.add_argument("--rigged", type=Path, default=None,
                   help="also re-export this rigged GLB with the baked "
                        "texture (step bake). It is assembled BEFORE this "
                        "stage runs, so without this it would ship grey")
```

And extend `step_bake`, after `npc_mesh.export_glb([shell], args.outdir / shell_name)`:

```python
    rigged_name = None
    if args.rigged is not None and args.rigged.exists():
        # A second import into the same scene, not a re-use of `shell`: the
        # rigged export is a DIFFERENT object - it carries vertex groups and
        # an armature modifier the plain shell does not - and re-deriving it
        # from this one would mean redoing the bind that assemble already did.
        # Its UVs and its material are what change, and finish_material() is
        # exactly that change.
        objects = npc_mesh.import_glb(args.rigged)
        armature = npc_mesh.armature_of(objects)
        meshes = npc_mesh.meshes_of(objects)
        if armature is None or not meshes:
            raise SystemExit(
                "%s has no armature or no mesh - not a Rigged.glb"
                % args.rigged.name)
        rigged = npc_mesh.join(meshes, "rigged_shell")
        # The bind is per vertex, and the rigged mesh is the same vertices in
        # the same order as the shell it was bound from, so the atlas UVs
        # transfer loop for loop. Asserted rather than assumed: a mismatch
        # would silently texture the figure with someone else's unwrap.
        if len(rigged.data.loops) != len(shell.data.loops):
            raise SystemExit(
                "%s has %d loops and the shell has %d - they are not the same "
                "mesh, so the atlas cannot be transferred"
                % (args.rigged.name, len(rigged.data.loops),
                   len(shell.data.loops)))
        atlas = (rigged.data.uv_layers.get("atlas")
                 or rigged.data.uv_layers.new(name="atlas"))
        source = shell.data.uv_layers["atlas"].data
        for index, loop in enumerate(atlas.data):
            loop.uv = source[index].uv
        npc_texture.finish_material(rigged, image)
        rigged_name = "_%s Rigged.glb" % args.stem
        npc_mesh.export_glb([armature, rigged], args.outdir / rigged_name)
```

and change the returned report:

```python
    files = [texture_name, shell_name]
    if rigged_name:
        files.append(rigged_name)
    return {
        "files": files,
        "texture": texture_name,
        "shell": shell_name,
        "rigged": rigged_name,
        "size": args.size,
        "islands": islands,
        "views": views,
        "faces": len(shell.data.polygons),
    }
```

- [ ] **Step 5: Pass it from `generate-3d.py`**

In `texture_command`, inside the `if step == "bake":` block, after the `--size` arguments:

```python
        # Only when it is actually there: --rig writes no Rigged.glb when the
        # bind left vertices unweighted, and naming a missing file would fail
        # the texture stage over a rig that already failed on its own.
        rigged = folder / ("%s Rigged.glb" % stem)
        if args.rig and rigged.exists():
            command += ["--rigged", str(rigged)]
```

In `stage_texture`, after the two existing `os.replace` calls and before `report["files"]` is set:

```python
    if report.get("rigged"):
        rigged = folder / ("%s Rigged.glb" % stem)
        os.replace(folder / report["rigged"], rigged)
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python -m unittest test.test_3d_texture test.test_3d_cli -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add blender/texture_npc.py generate-3d.py test/test_3d_texture.py test/test_3d_cli.py
git add test/fixtures/3d/make_fixtures.py test/fixtures/3d/rigged.glb
git commit -m "feat: the rigged GLB carries the baked texture too"
```

---

### Task 9: Documentation, and delete the probe

§8.2 step 4. The probe has done its job; the docs have to record what it found and what this stage does not do.

**Files:**
- Delete: `blender/probe_projection.py`
- Modify: `docs/generate-3d.md`
- Modify: `docs/superpowers/specs/2026-09-05-npc-3d-texture-design.md`

**Interfaces:**
- Consumes: the measurements taken in Tasks 1, 4 and 7 — the probe's verdict and margin, the UV island count, the atlas file size, and whether `--pause-3d` had to be raised.
- Produces: nothing any task consumes.

- [ ] **Step 1: Delete the probe**

```bash
git rm blender/probe_projection.py
```

It stays in the history at Task 1's commit, which is where §8.1 said it belongs.

- [ ] **Step 2: Correct the spec's margin**

The spec is the record of a design and stays as written, except where it states a fact about the code that is wrong. In `docs/superpowers/specs/2026-09-05-npc-3d-texture-design.md` §4.2, change `* 1.12` to `* 1.06` and `margin=1.12` to `margin=1.06`, and add after that paragraph:

```markdown
> **Corrected during implementation (2026-09-05):** this section originally
> said 1.12. `APOSE_MARGIN` is, and has always been, `0.06`, so the matching
> camera margin is 1.06. The reasoning was right and the constant was not;
> `generate-3d.py` now derives `FRONT_MARGIN = 1 + APOSE_MARGIN` so the two
> cannot disagree again.
```

- [ ] **Step 3: Update the Outputs section**

In `docs/generate-3d.md`, extend the `## Outputs` table with the new file and correct the shell's row:

```markdown
| `<Name> Texture.png` | The baked colour atlas, projected from the A-pose reference |
| `<Name> Shell.glb` | Clothed mesh, cleaned, unrigged - the full-detail one, with UVs, a Principled material and the texture packed in |
```

And extend the intermediates sentence so `3d/_back_render.png` and `3d/back.png` are named alongside `apose.png`, `_shell.glb` and `_base.glb` — they are kept for the same reason: they are what you look at when a back comes out wrong.

- [ ] **Step 4: Write the Texturing section**

Add after `## Rigging` and before `## Known limits`:

```markdown
## Texturing

Every reconstruction used to come out grey. It no longer does: the `texture`
stage projects the reference image the shell was built from back onto the
shell, and bakes it to an atlas.

The reference is not an interpretation of the character - it is the render
that produced the geometry, with the rolled skin, hair, eyes, outfit, headgear
and glow colour already resolved and painted. Much of what a reconstruction
loses is carried there as *paint rather than form*: unit patches, a stencilled
number, a hazard triangle, boot laces, wear. Geometry cannot recover those at
any resolution. Projection puts them on the model directly.

```bash
# the default - a front projected from the reference, plus a generated back
python generate-3d.py --id npc-jules-sokolova-40213 --stage texture

# no ComfyUI at all: the front is exact, the back is the right palette
python generate-3d.py --id npc-jules-sokolova-40213 --stage texture --no-back-view

# a back view you made yourself, instead of a generated one
python generate-3d.py --id npc-jules-sokolova-40213 --stage texture \
    --back-image back.png

# back to grey
python generate-3d.py --filter Crew --no-texture
```

`texture` is a stage of its own rather than part of `assemble`, for three
reasons: it needs a ComfyUI round trip in the middle of Blender work and
`assemble` is deliberately one offline run with no network; an NPC built
before this landed can be textured with `--stage texture` alone, reading
`Shell.glb` and `apose_square.png` off disk; and a texture failure is
contained the way a rigging failure is - it costs the texture and nothing
else, and every grey deliverable stays exactly as it was.

### How the front registers

Nothing between reconstruction and export rotates the shell - `clean_shell`
scales, `align_to` translates - so the shell sits in world space at
Hunyuan3D's own orientation and `frame_camera(shell, 0)` looks straight down
the axis the reconstruction was conditioned from. The projection camera is
`frame_camera` with one changed constant.

That constant is `FRONT_MARGIN`, and it is **derived, not chosen**:
`square_apose()` squares the subject on `max(w, h) * (1 + APOSE_MARGIN)` and
`frame_camera` sets `ortho_scale` to `max(dimensions) * margin`. They are the
same rule - the subject's own bounds, squared on the longer side - so the
camera must use the constant the image was built with. Change `APOSE_MARGIN`
and the camera follows.

This is bounds-matching, not a calibrated camera: Hunyuan3D is not a renderer
and guarantees no metric correspondence between input pixel and output vertex.

<!-- MEASUREMENT: replace with Task 1's finding - what the probe showed, at
     what margin, and how far off registration was. -->

### How the back is invented

An independently generated back view would not line up with the mesh. The
usual fix is structural conditioning and it is not available here:
`ControlNetLoader`'s enum is empty, no models on disk. So the back view is not
generated from scratch. The shell's own 180-degree view is *rendered*, and
Qwen-Image-Edit 2509 paints that render. The output is registered to the mesh
by construction, because it is that image with paint on it.

Three references go in: the render being edited, `apose_square.png` for the
character's colours and materials, and - only when the rolled portrait is
composed from behind - the portrait, which is then real evidence about the
character's back. The prompt is the NPC's own A-pose prompt with its stance
clause replaced, so there is one description of the character rather than two
to keep in step.

### The blend

With the front camera at -Y looking +Y, a surface's facing is its world
normal's Y component alone. `t = 0.5 + 0.5 * Ny` runs 0 at dead-front to 1 at
dead-back; smoothstepped, that is the mix. Deliberately not `max(0, ±Ny)`,
whose weights both reach zero at the silhouette - which is exactly where a
naive blend tears.

Each view's weight is then multiplied by its own sampled alpha, so where the
mesh's silhouette overshoots the image's, the texel falls to the other view
instead of sampling backdrop grey.

Not mirroring. Mirroring the front across the sagittal plane would put an open
jacket and a visible tank top on the character's *back*, which is wrong in a
way edge-wrap is not.

### Resolution

`--texture-size` defaults to 2048. The shell is roughly 1.9 m² of surface, so
a 2048² atlas is about 0.7 mm/texel against the reference's own ~1.3 mm/px -
the atlas is finer than its source, which is the right side of the trade.

Vertex colours were considered and rejected on the same arithmetic: ~81,000
vertices over that area is ~5 mm between samples, roughly 4× coarser than the
reference, which would blur precisely the patches and stencils that motivate
the work.

<!-- MEASUREMENT: replace with Task 4's and Task 7's numbers - UV island count
     on the real shell, Texture.png size, Shell.glb size before and after,
     and whether --pause-3d had to be raised for the Qwen job. -->
```

- [ ] **Step 5: Add the limits**

Under `## Known limits`, add three subsections. None of these is a hedge — each is a thing that was decided rather than overlooked.

```markdown
### Accepted: concavities get the wrong colour

Project-from-view ignores depth. A texel that faces the front camera but is
**occluded** from it - under the jacket flap, under the chin, between the
legs, inside the collar - samples whatever front pixel sits at that screen
position, which belongs to the surface in front of it.

Normal-weighting handles the front/back split correctly. It does not handle
this. Doing so properly means per-texel ray-cast visibility, which is a
significantly larger piece of work. The refinement is additive when it comes:
a visibility term multiplies into the same weights the blend already computes.

### The generated back does not agree with the front in detail

A Qwen back view will not place the jacket's seams, the hair's fall or the
wear pattern where a real turn of the character would. The blend is smooth, so
it reads as a soft transition rather than a seam - but the back is a plausible
invention, and nothing about it is evidence of what the character's back is
actually like. The front is the reference's own pixels. The back is not.

### Unquantified: Smart UV Project on an open 162k-face shell

The shell is not closed - 1,355 boundary edges - and dense, so the unwrap
produces many islands. Whether the packing is efficient enough at 2048², and
whether island seams are visible on the deliverable, is reported rather than
assumed: the island count is printed on every run. If it turns out poor, the
levers are a larger `--texture-size`, or unwrapping the printable (welded,
closed) copy and transferring.
```

And in `### Still true`, replace the texture bullet — it is no longer true:

```markdown
- **~~The rigged character has no texture.~~** Fixed - see
  [Texturing](#texturing). `Shell.glb` and, with `--rig`, `Rigged.glb` now
  carry a baked atlas projected from the A-pose reference. `Print.stl` does
  not, and will not: a print has no colour.
```

- [ ] **Step 6: Fill in every measurement placeholder**

A doc that ships with a placeholder in it is a doc that stops being trusted.

```bash
grep -n "MEASUREMENT" docs/generate-3d.md
```

Expected: no output. Replace each marker with the real numbers recorded in Tasks 1, 4 and 7 before running this.

- [ ] **Step 7: Run the whole suite**

Run: `python -m unittest discover -s test -t . -v`
Expected: PASS, with the Blender and live-ComfyUI classes skipped or passing depending on the machine. Nothing in `test_apose_stance.py`, `test_token_pose.py` or the trait tests should have moved — if one did, the stance work in Task 6 reached further than it should have.

- [ ] **Step 8: Commit**

```bash
git add -A docs/ blender/
git commit -m "docs: texturing, its limits, and the corrected framing constant"
```

---

## Self-review

Run through this before starting Task 1, and again after Task 9.

**Spec coverage**

| Spec section | Where it is implemented |
|---|---|
| §4.1 the `texture` stage, two Blender launches | Tasks 3, 4, 5, 7 |
| §4.2 the projection camera and its margin | Task 2, with the 1.12→1.06 correction stated up front and asserted in Task 4 |
| §4.3.1 atlas UVs | Task 3 (`atlas_uvs`) |
| §4.3.2 per-view UVs at each camera | Task 2 (`project_uvs`), Task 3 (`BACK_MARGIN` shared by both steps) |
| §4.3.3 the normal blend | Task 3 (`projection_material`) |
| §4.3.4 edge validity from alpha | Task 3 (`projection_material`'s weight terms) |
| §4.3.5 bake, assign, re-export | Task 3 (`bake_atlas`, `finish_material`) |
| §4.4 the Qwen back-view graph | Task 6 |
| §5.1 outputs and the dossier | Task 4 (dossier), Task 9 (docs) |
| §5.2 the four flags | Task 4 (`--texture`, `--no-texture`, `--texture-size`, `--no-back-view`), Task 5 (`--back-image`) |
| §5.3 failure containment and the atomic replace | Task 4 |
| §6 the three test files | Tasks 2-8 throughout |
| §7.1-§7.5 risks and limits | Task 1 (settles §7.1), Task 9 (documents the rest) |
| §8.1 the probe | Task 1 |
| §8.2 the order of work | Tasks 4 (step 1), 6-7 (step 2), 8 (step 3), 9 (step 4) |

**Two things the spec asked for that this plan does differently, and why**

1. **§4.2's margin is 1.06, not 1.12.** The spec's arithmetic did not match `APOSE_MARGIN`. The reasoning is kept; the constant is derived so it cannot drift again. Task 1's probe can still overrule the derivation with a measurement, and says how.
2. **§4.4 says the back-view graph is addressed through `node_of()`.** It cannot be: that helper requires exactly one node of a class, and the graph has three `LoadImage` nodes and two `TextEncodeQwenImageEditPlus` nodes. Task 6 uses `backview_slots()`, which follows links from the unique `KSampler` instead — keeping the property `node_of()` exists for (a re-export renumbers every node and this still resolves) and keeping the loud failure on an unexpected shape.

**Naming consistency check**

- `FRONT_MARGIN` — defined Task 4, consumed by `texture_command` (Task 4) and asserted in `TestFrontMargin`.
- `BACK_MARGIN` — defined Task 2, consumed by `render_back` (Task 3) and `step_bake` (Task 3). One definition, both steps.
- `run_texture_step(args, folder, stem, shell, step, front=None, back=None)` — defined Task 4, mocked with that exact signature in Tasks 4, 5 and 7.
- `stage_texture(comfy, args, subject, folder, stem, entry=None, portrait=None)` — defined Task 4, called from `main()` (Task 4) and tested in Tasks 4, 5 and 7 with that arity.
- `generate_back_view(comfy, args, subject, folder, shell, stem, entry, portrait)` — placeholder Task 4, implemented Task 7, same eight parameters.
- The report keys `texture`, `shell`, `rigged`, `views`, `islands`, `size`, `faces`, `render`, `step` — produced by `texture_npc.py` (Tasks 3, 8), consumed by `stage_texture` (Tasks 4, 8).
- `write_test_png`, `run_blender`, `glb_document`, `glb_holds_an_image` — defined once in `test/test_3d_texture.py` (Tasks 2, 3), used by every later class in that file.
