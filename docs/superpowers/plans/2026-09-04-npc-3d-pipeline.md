# NPC 3D Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn any NPC already in `.generated-npcs.json` into a rigged GLB, a printable STL, a cleaned clothed shell and four turnaround renders, without changing `generate-npc.py`.

**Architecture:** A new entry point `generate-3d.py` loads `generate-npc.py` by path (the same hyphen trick `generate-npc.py` already uses on `generate-art.py`) and reuses its pure functions rather than duplicating them. It re-renders each NPC's token in a forced A-pose, feeds that one image to two checked-in ComfyUI workflows — Hunyuan3D for a clothed shell, SAM3DBody for a rigged A-pose body — and hands both GLBs to a headless Blender script that cleans, aligns, binds and exports. Three phases, each independently useful: Stages 0–1 (two GLBs on disk), Stage 2 without rigging (STL, shell, turnarounds), then the rigging bridge.

**Tech Stack:** Python 3 standard library only, no new dependencies. ComfyUI's native 3D nodes over HTTP (no custom node packs — spec §2.1). Blender 5.2.1 LTS headless at `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`. Tests are `unittest`, run as `python -m unittest discover -s test -t .`.

**Spec:** [`docs/superpowers/specs/2026-09-04-npc-3d-pipeline-design.md`](../specs/2026-09-04-npc-3d-pipeline-design.md)

## Global Constraints

- **`generate-npc.py` gains nothing and loses nothing.** No new flag, no changed default, no relaxed guard. In particular the `--regen-manifest replaces the roll entirely; drop --set-trait` error and `Stance`'s absence from `REROLLABLE_TRAITS` both stay exactly as they are (spec §4.2). `generate-3d.py` imports it; it never edits it.
- **`generate-art.py` gains nothing either.** Its `Comfy`, `build_job`, `build_post_job`, `locate_slots`, `locate_post_slots`, `image_ref`, `find_server`, `load_manifest` and `save_manifest` are consumed as-is.
- **No compiled CUDA extensions, ever.** `nvdiffrast`, `diff-gaussian-rasterization`, `torchmcubes` and `pytorch3d` cannot be built on this machine (spec §2.2). Nothing here may add a dependency needing a C or CUDA compiler. Both tools and the whole suite must run on a stock Python 3 with no `pip install`.
- **No custom ComfyUI node packs.** Every node named below is already registered natively (spec §2.1), verified against the live `/object_info` on 2026-09-04.
- **A 3D failure never damages art.** Per-NPC isolation: one NPC's exception is logged to stderr and the batch continues (spec §8). Nothing in `generate-3d.py` writes to `.generated-npcs.json`.
- **Dynamic combo inputs serialise as dotted keys, never nested objects** (spec §2.6). This bites `BuildPoseFile.format`, `RemeshMesh.sign_mode` and `DecimateMesh.placement_mode`. A nested dict validates and *then* fails at execution with `missing 1 required positional argument`.
- **Exact model filenames**, confirmed present on the live server:
  - `hunyuan3d-dit-v2-mv_fp16.safetensors` — in `ImageOnlyCheckpointLoader`'s `ckpt_name` list
  - `sam_3d_body_dinov3_bf16.safetensors` — in `SAM3DBody_Loader`'s `model_file` list
- **Blender's render engine enum is `BLENDER_EEVEE`**, not `BLENDER_EEVEE_NEXT` (spec §2.5). Confirmed: it is the only non-Cycles identifier in 5.2.1.
- **Blender STL export is `bpy.ops.wm.stl_export`** (the 4.2+ operator). Confirmed present.
- **Tests must not require a GPU or a running ComfyUI.** Tests needing the live server or Blender `skipUnless` themselves out when it is absent, and the default suite still passes.
- **House commit style:** `feat:` / `docs:` / `fix:` subject, then prose paragraphs explaining the reasoning — no bullet lists. Every commit message ends with:

  ```
  Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
  Claude-Session: <this session's URL>
  ```

---

## File Structure

| File | Responsibility |
|---|---|
| `generate-3d.py` | New entry point. CLI, manifest selection, the A-pose npc rebuild, the three stage drivers, the `## 3D` dossier section. Everything that talks to ComfyUI or shells out to Blender. |
| `workflows/api/Util_Image_to_Mesh_Hunyuan3D_v1.json` | New. Image → clothed shell GLB. Checked in so a run reproduces. |
| `workflows/api/Util_Image_to_RiggedBody_SAM3D_v1.json` | New. Image → rigged A-pose body GLB. |
| `blender/assemble_npc.py` | New. The headless entry point: argv parsing and orchestration only. |
| `blender/npc_mesh.py` | New. Import, rest-pose, scale/centre alignment, shell cleanup, manifoldness, GLB/STL export. |
| `blender/npc_render.py` | New. Turnaround camera, lighting and orbit renders. |
| `blender/npc_rig.py` | New in Phase 3. Weight transfer, armature bind, and the weight/bone assertions. |
| `test/helpers.py` | Gains `load_3d()` and `manifest_entry()`. Modify only; nothing existing changes. |
| `test/workflow_schema.py` | New. `expected_inputs()`, which walks a node's dynamic combos to the full dotted required set. |
| `test/fixtures/3d/make_fixtures.py` | New. Blender script that regenerates the two fixture GLBs. Run by hand, not by the suite. |
| `test/fixtures/3d/base.glb`, `test/fixtures/3d/shell.glb` | New, committed. A tiny rigged body and a tiny unit-scaled shell with a speck, so the Blender stage is testable without a GPU or a model. |
| `test/test_apose_stance.py` | New. Spec §10's first three bullets. |
| `test/test_3d_workflows.py` | New. Spec §10's fourth bullet, live and offline halves. |
| `test/test_3d_cli.py` | New. Selection, skip/overwrite, dry-run, the dossier section. |
| `test/test_3d_assembly.py` | New. Spec §10's fifth bullet — the Blender stage against the fixtures. |
| `docs/generate-3d.md` | New. The prose reference, matching `docs/generate-npc.md`. |
| `README.md` | One paragraph and the new command. |

---

# Phase 1 — Stages 0 and 1

Ends with `apose.png`, `_base.glb` and `_shell.glb` on disk for a real NPC, and no Blender work. Proves the A-pose approach.

---

### Task 1: `APOSE_STANCE` and the A-pose npc rebuild

**Files:**
- Create: `generate-3d.py`
- Modify: `test/helpers.py` (imports at `:6-9`; append after `load_generator()` at `:26`)
- Test: `test/test_apose_stance.py` (create)

**Interfaces:**
- Consumes: `generate-npc.py`'s `migrate_traits(traits) -> dict`, `pronoun_fields(pronouns) -> dict`, `build_prompts(npc) -> (portrait, token)`, `roll_npc(tables, rng, overrides=None, unarmed=False) -> dict`, `parse_tables(path) -> dict`.
- Produces:
  - `APOSE_STANCE: str` — a Stance-shaped predicate, lowercase, no trailing period.
  - `apose_npc(entry) -> dict` — a full npc dict (with `_pronouns`, `_young`, `_outfit_notac`), Stance forced and both hands emptied.
  - `apose_prompt(entry) -> str` — the token prompt for that npc.
  - `test.helpers.load_3d() -> module`
  - `test.helpers.manifest_entry(seed=0, overrides=None) -> dict`

- [ ] **Step 1: Add the two test helpers**

In `test/helpers.py`, extend the import block so `manifest_entry` can roll:

```python
import importlib.util
import random
import sys
from pathlib import Path
```

Then append after `load_generator()`:

```python
_cached_3d = None


def load_3d():
    """The generate-3d.py module object, loaded once per process.

    Same by-path load as load_generator(), for the same reason: the hyphen
    keeps generate-3d.py off the normal import path.
    """
    global _cached_3d
    if _cached_3d is None:
        spec = importlib.util.spec_from_file_location("gen3d", REPO / "generate-3d.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["gen3d"] = module
        spec.loader.exec_module(module)
        _cached_3d = module
    return _cached_3d


def manifest_entry(seed=0, overrides=None):
    """One .generated-npcs.json entry, rolled from the fixture tables.

    The 3D tools read manifest entries, not rolled npc dicts, so a test that
    handed them a dict straight out of roll_npc() would be testing a shape
    that never reaches them. This reproduces exactly the keys generate-npc.py's
    roll path writes, minus the render results, which nothing in the 3D
    rebuild reads.
    """
    gen = load_generator()
    tables = gen.parse_tables(FIXTURE_TABLES)
    npc = gen.roll_npc(tables, random.Random(seed), overrides or {})
    return {
        "id": "npc-test-%d" % seed,
        "kind": "npc",
        "name": npc["name"],
        "callsign": npc["Callsigns"],
        "seed": seed,
        "traits": {k: v for k, v in npc.items() if not k.startswith("_")},
        "young": npc["_young"],
        "outfit_notac": npc["_outfit_notac"],
    }
```

- [ ] **Step 2: Write the failing test**

Create `test/test_apose_stance.py`:

```python
"""Stage 0 renders the token again in a forced A-pose.

Skin-weight transfer is proximity-based, so the Hunyuan3D shell and the
SAM3DBody base have to be in the same pose or the shoulders smear. The base
is always A-pose; this is what puts the shell there too, by re-rendering the
source image rather than correcting for the mismatch afterwards.

Nothing here goes near --regen-manifest. Stage 0 is a different tool
rendering a different image, and both of that path's guards - the --set-trait
refusal and Stance's absence from REROLLABLE_TRAITS - stay exactly as they are.
"""
import unittest

from test.helpers import load_3d, load_generator, manifest_entry

gen = load_generator()
d3 = load_3d()

# A stance nothing else would produce, so "the forced stance replaced it" and
# "the roll happened to agree" cannot be confused.
CROUCH = "crouched low and coiled, weight braced forward on one arm"
ARMED = {"Weapon": "a heavy service rifle held in both hands",
         "Gear": "a bulky tool case"}


class TestAposeStance(unittest.TestCase):
    def test_the_stance_reaches_the_token_prompt(self):
        self.assertIn(d3.APOSE_STANCE, d3.apose_prompt(manifest_entry(1)))

    def test_the_rolled_stance_does_not(self):
        entry = manifest_entry(1, {"Stance": CROUCH})
        self.assertNotIn("crouched low", d3.apose_prompt(entry))

    def test_the_stance_describes_a_neutral_standing_pose(self):
        for phrase in ("standing straight", "arms held slightly away",
                       "palms forward", "feet shoulder-width apart"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, d3.APOSE_STANCE)

    def test_the_stance_reads_as_a_stance_bullet(self):
        """It substitutes into '{Subject} {is_are} {stance}, both feet...'.

        A leading capital or a trailing period would produce 'She is Standing.
        , both feet in frame', so both are banned - exactly as they are for
        every bullet in the live Stance table.
        """
        self.assertFalse(d3.APOSE_STANCE.endswith("."))
        self.assertTrue(d3.APOSE_STANCE[0].islower())

    def test_both_hands_are_emptied(self):
        """An NPC holding a carbine in both hands cannot hold an A-pose."""
        npc = d3.apose_npc(manifest_entry(2, ARMED))
        self.assertEqual(npc["Weapon"], "")
        self.assertEqual(npc["Gear"], "")

    def test_no_carry_sentence_survives_into_the_prompt(self):
        prompt = d3.apose_prompt(manifest_entry(2, ARMED))
        self.assertNotIn("service rifle", prompt)
        self.assertNotIn("tool case", prompt)

    def test_the_manifest_entry_is_not_mutated(self):
        """The caller still needs it for the dossier and the log line."""
        entry = manifest_entry(3, {"Stance": CROUCH})
        d3.apose_npc(entry)
        self.assertEqual(entry["traits"]["Stance"], CROUCH)

    def test_a_pre_weapon_entry_round_trips(self):
        """Entries written before '## Weapon' existed carry no Weapon key.

        build_prompts() has a .get shim for exactly this; the rebuild must not
        defeat it with a KeyError of its own.
        """
        entry = manifest_entry(4)
        del entry["traits"]["Weapon"]
        self.assertIn(d3.APOSE_STANCE, d3.apose_prompt(entry))

    def test_an_entry_with_no_height_round_trips(self):
        """Same, for entries written before '## Height' existed."""
        entry = manifest_entry(5)
        del entry["traits"]["Height"]
        self.assertIn(d3.APOSE_STANCE, d3.apose_prompt(entry))

    def test_an_entry_with_no_young_flag_round_trips(self):
        entry = manifest_entry(6)
        del entry["young"]
        self.assertIn(d3.APOSE_STANCE, d3.apose_prompt(entry))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run it to verify it fails**

Run: `python -m unittest test.test_apose_stance -v`
Expected: FAIL — `SystemExit` / `FileNotFoundError` for `generate-3d.py`, which does not exist yet.

- [ ] **Step 4: Write `generate-3d.py` far enough to pass**

Only the module load, the constant and the rebuild. The CLI arrives in Task 3.

```python
#!/usr/bin/env python3
"""Turn a generated NPC into a rigged GLB, a printable STL and turnarounds.

Reads .generated-npcs.json, so the whole existing back catalogue is eligible.
Four stages per NPC: re-render the token in a forced A-pose, reconstruct a
clothed shell and a rigged body from that one image, assemble them in headless
Blender, and write the results into the NPC's own folder.

A separate command rather than a flag on generate-npc.py: reconstruction is
slow and failure-prone, and it must never be able to break art generation.

    python generate-3d.py --filter Sokolova
    python generate-3d.py --id npc-jules-sokolova-40213 --stage apose
"""
import importlib.util
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _load_npc_generator():
    """Import generate-npc.py, and through it generate-art.py.

    The same by-path load generate-npc.py uses on generate-art.py, for the
    same reason: the hyphen keeps it off the normal import path, and renaming
    it would invalidate every README, docstring and shell history that names
    it. Importing it is safe - its main() sits behind an
    `if __name__ == "__main__"` guard, so nothing runs on import.
    """
    path = SCRIPT_DIR / "generate-npc.py"
    if not path.exists():
        raise SystemExit("generate-npc.py not found next to this script (%s)" % SCRIPT_DIR)
    name = "lancer_generate_npc"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    # Registered before the body runs: generate-npc.py's own @dataclass use
    # resolves annotations through sys.modules[cls.__module__].
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


npc_gen = _load_npc_generator()
art = npc_gen.art

# The Stance every 3D source render is forced into.
#
# Written as an ordinary Stance bullet - lowercase, no trailing period - so it
# composes with the token template's "{Subject} {is_are} {stance}, both feet in
# frame" exactly as a rolled bullet does. A module constant here rather than a
# bullet in the tables file because no ROLLED NPC should ever get it: it is a
# reconstruction jig, not a pose anyone wants art of.
#
# A-pose is not a preference. The SAM3DBody base always comes out in A-pose
# (spec §2.4), the Hunyuan3D shell inherits the pose of its source image, and
# proximity-based weight transfer across a mismatch smears the shoulders. It
# also improves the reconstruction on its own, by separating the limbs from the
# torso so the arms do not fuse to the body.
APOSE_STANCE = (
    "standing straight and squarely facing the viewer, arms held slightly away "
    "from the sides with the palms forward, feet shoulder-width apart"
)


def apose_npc(entry):
    """The npc dict for one manifest entry, re-posed for reconstruction.

    Rebuilt the way regenerate_one() rebuilds it - migrate_traits(),
    pronoun_fields(), the recorded 'young' flag, the Height backfill - and then
    changed in exactly two ways: the Stance is replaced, and both hands are
    emptied.

    Emptying the hands is not optional. carry_sentence() puts the Weapon and
    the Gear in the subject's hands, and an NPC holding a carbine in both hands
    cannot hold an A-pose; the prompt would assert both at once and the model
    would resolve it by rendering neither. roll_npc() already filters Stance
    against occupied hands for the same reason - this is that rule reached from
    the other side, since here the stance is fixed and the equipment is what
    has to give.

    Gear goes with the Weapon rather than being kept: the Gear table is
    equipment held in a hand or slung over a shoulder, so it occupies a hand as
    readily as a weapon does.

    The entry is not mutated - the caller still needs it for the dossier and
    the log line.
    """
    npc = npc_gen.migrate_traits(entry["traits"])
    npc["_pronouns"] = npc_gen.pronoun_fields(npc["Pronouns"])
    npc["_young"] = entry.get("young", False)
    npc["_outfit_notac"] = entry.get("outfit_notac")
    if "Height" not in npc:
        # Written before '## Height' existed. build_prompts() has no shim for
        # this one, unlike Weapon, so supply what regenerate_one() supplies.
        npc["Height"] = "of average height"
    npc["Stance"] = APOSE_STANCE
    npc["Weapon"] = ""
    npc["Gear"] = ""
    return npc


def apose_prompt(entry):
    """The token prompt Stage 0 renders. The portrait half is discarded."""
    return npc_gen.build_prompts(apose_npc(entry))[1]
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `python -m unittest test.test_apose_stance -v`
Expected: PASS, 10 tests.

- [ ] **Step 6: Run the whole suite — nothing existing may move**

Run: `python -m unittest discover -s test -t .`
Expected: PASS. The count grows by 10 from the current 217; no failures.

- [ ] **Step 7: Commit**

```bash
git add generate-3d.py test/helpers.py test/test_apose_stance.py
git commit -m "feat: the A-pose npc rebuild the 3D pipeline renders from"
```

---

### Task 2: The two ComfyUI workflows, and a schema test that outlives them

**Files:**
- Create: `workflows/api/Util_Image_to_Mesh_Hunyuan3D_v1.json`
- Create: `workflows/api/Util_Image_to_RiggedBody_SAM3D_v1.json`
- Create: `test/workflow_schema.py`
- Test: `test/test_3d_workflows.py` (create)

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces:
  - Two API-format graphs, each with exactly one `LoadImage` and one `SaveGLB`.
  - `test.workflow_schema.expected_inputs(required, values, prefix="") -> list[str]`
  - `test.workflow_schema.object_info(class_type, base=..., timeout=15) -> dict | None`
  - `test.workflow_schema.server_is_up(base=..., timeout=2.0) -> bool`

- [ ] **Step 1: Write the Hunyuan3D workflow**

Every value below was read off the live `/object_info` on 2026-09-04. `sign_mode` is a `COMFY_DYNAMICCOMBO_V3`, so its children are dotted (spec §2.6) — the same trap `BuildPoseFile` sets, reached a node earlier.

`drop_small_components` at `0.02` removes the 10,878 sub-20-face specks of spec §2.3 in-graph; `fix_poles` and `project_back` are what push the result toward printable.

Create `workflows/api/Util_Image_to_Mesh_Hunyuan3D_v1.json`:

```json
{
  "1": {
    "class_type": "LoadImage",
    "_meta": {"title": "A-pose source (patched by generate-3d.py)"},
    "inputs": {"image": "apose.png [output]"}
  },
  "2": {
    "class_type": "ImageOnlyCheckpointLoader",
    "_meta": {"title": "Hunyuan3D v2 mv"},
    "inputs": {"ckpt_name": "hunyuan3d-dit-v2-mv_fp16.safetensors"}
  },
  "3": {
    "class_type": "CLIPVisionEncode",
    "inputs": {"clip_vision": ["2", 1], "image": ["1", 0], "crop": "center"}
  },
  "4": {
    "class_type": "Hunyuan3Dv2Conditioning",
    "inputs": {"clip_vision_output": ["3", 0]}
  },
  "5": {
    "class_type": "EmptyLatentHunyuan3Dv2",
    "inputs": {"resolution": 3072, "batch_size": 1}
  },
  "6": {
    "class_type": "KSampler",
    "inputs": {
      "model": ["2", 0],
      "seed": 0,
      "steps": 50,
      "cfg": 5.0,
      "sampler_name": "euler",
      "scheduler": "normal",
      "positive": ["4", 0],
      "negative": ["4", 1],
      "latent_image": ["5", 0],
      "denoise": 1.0
    }
  },
  "7": {
    "class_type": "VAEDecodeHunyuan3D",
    "inputs": {"samples": ["6", 0], "vae": ["2", 2], "num_chunks": 8000, "octree_resolution": 256}
  },
  "8": {
    "class_type": "VoxelToMesh",
    "inputs": {"voxel": ["7", 0], "algorithm": "surface net", "threshold": 0.6}
  },
  "9": {
    "class_type": "RemeshMesh",
    "_meta": {"title": "Remesh - drops the specks, closes the surface"},
    "inputs": {
      "mesh": ["8", 0],
      "resolution": 512,
      "sign_mode": "udf",
      "sign_mode.qef": false,
      "sign_mode.drop_inverted_components": true,
      "sign_mode.drop_enclosed_components": true,
      "band": 1.0,
      "project_back": 1.0,
      "fix_poles": true,
      "smooth_iters": 2,
      "drop_small_components": 0.02,
      "precluster_max_verts": 20000000
    }
  },
  "10": {
    "class_type": "DecimateMesh",
    "inputs": {"mesh": ["9", 0], "target_face_count": 200000, "placement_mode": "midpoint"}
  },
  "11": {
    "class_type": "SaveGLB",
    "inputs": {"mesh": ["10", 0], "filename_prefix": "3d/shell"}
  }
}
```

- [ ] **Step 2: Write the SAM3DBody workflow**

`format` nests three levels deep, and every level flattens. `camera_translation` is `off` because the bind position is the whole point — `absolute` would bake the estimator's camera depth into the root translation. `track_index` is `0` rather than the default `-1` because a token holds exactly one figure, and a second detected "person" would export as a second armature for the Blender stage to guess between.

`sam3d_body_model` is nominally optional, but `body_mesh` needs the model, so it is linked.

Create `workflows/api/Util_Image_to_RiggedBody_SAM3D_v1.json`:

```json
{
  "1": {
    "class_type": "LoadImage",
    "_meta": {"title": "A-pose source (patched by generate-3d.py)"},
    "inputs": {"image": "apose.png [output]"}
  },
  "2": {
    "class_type": "SAM3DBody_Loader",
    "inputs": {"model_file": "sam_3d_body_dinov3_bf16.safetensors"}
  },
  "3": {
    "class_type": "SAM3DBody_Predict",
    "inputs": {
      "sam3d_body_model": ["2", 0],
      "image": ["1", 0],
      "run_hand_refinement": true,
      "fov": 0.0,
      "batch_size": 64
    }
  },
  "4": {
    "class_type": "BuildPoseFile",
    "_meta": {"title": "127-bone body mesh - the pose is discarded in Blender"},
    "inputs": {
      "pose_data": ["3", 0],
      "sam3d_body_model": ["2", 0],
      "format": "glb",
      "format.mesh_style": "body_mesh",
      "format.mesh_style.bone_vis": "off",
      "format.mesh_style.shader": "default",
      "format.bone_smooth_window": 0,
      "fps": 24.0,
      "camera_translation": "off",
      "track_index": 0
    }
  },
  "5": {
    "class_type": "SaveGLB",
    "inputs": {"mesh": ["4", 0], "filename_prefix": "3d/base"}
  }
}
```

- [ ] **Step 3: Write the schema walker**

Create `test/workflow_schema.py`:

```python
"""What inputs a ComfyUI node actually requires, dotted children included.

New-schema nodes (COMFY_DYNAMICCOMBO_V3) do not take a nested object in
API-format JSON. Choosing an option pulls that option's own required inputs
into the SAME flat inputs dict under a dot-joined name - so BuildPoseFile with
format=glb and mesh_style=body_mesh requires 'format.mesh_style.bone_vis' as a
top-level key. Passing a nested dict validates and then fails at execution
with 'missing 1 required positional argument', which is a long way from the
mistake.

This walks the option tree the way the server does, so the test built on it
fails the moment a ComfyUI update adds, renames or re-nests a child input -
the likeliest thing about these two workflows to rot.
"""
import json
import urllib.request

DEFAULT_BASE = "http://127.0.0.1:8000"


def object_info(class_type, base=DEFAULT_BASE, timeout=15):
    """One node's schema, or None when the server is not there.

    Per-node rather than the whole /object_info: the full document is large
    enough that reading it has been seen to reset the connection.
    """
    try:
        url = "%s/object_info/%s" % (base.rstrip("/"), class_type)
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")).get(class_type)
    except Exception:
        return None


def server_is_up(base=DEFAULT_BASE, timeout=2.0):
    try:
        urllib.request.urlopen(base.rstrip("/") + "/system_stats", timeout=timeout)
        return True
    except Exception:
        return False


def expected_inputs(required, values, prefix=""):
    """Every input key `required` demands, given the values already chosen.

    `values` is the node's own flat inputs dict from the workflow JSON - the
    walk is value-directed because which children exist depends on which
    option was picked.
    """
    out = []
    for name, definition in required.items():
        key = prefix + name
        out.append(key)
        if definition[0] != "COMFY_DYNAMICCOMBO_V3":
            continue
        meta = definition[1] if len(definition) > 1 else {}
        chosen = values.get(key)
        for option in meta.get("options", []):
            if option["key"] == chosen:
                out += expected_inputs(
                    option.get("inputs", {}).get("required", {}), values, key + ".")
                break
    return out
```

- [ ] **Step 4: Write the test**

Create `test/test_3d_workflows.py`:

```python
"""The two 3D workflows are checked in, so they can rot silently.

Half of this runs anywhere: the graph is internally consistent, and the node
set is the one the design chose. The other half needs a live ComfyUI and is
where the real value is - it re-derives the required input set from
/object_info and fails when a model is renamed, a combo option disappears, or
a dynamic combo grows a child. Skipped, not failed, when no server answers.
"""
import json
import unittest

from test.helpers import REPO
from test.workflow_schema import expected_inputs, object_info, server_is_up

MESH = REPO / "workflows" / "api" / "Util_Image_to_Mesh_Hunyuan3D_v1.json"
RIG = REPO / "workflows" / "api" / "Util_Image_to_RiggedBody_SAM3D_v1.json"
GRAPHS = {"mesh": json.loads(MESH.read_text(encoding="utf-8")),
          "rig": json.loads(RIG.read_text(encoding="utf-8"))}


def links(node):
    """The ["node_id", slot] references in one node's inputs."""
    return [v for v in node["inputs"].values()
            if isinstance(v, list) and len(v) == 2 and isinstance(v[0], str)]


def node_named(graph, class_type):
    return next(d for d in graph.values() if d["class_type"] == class_type)


class TestGraphShape(unittest.TestCase):
    def test_every_link_points_at_a_real_node(self):
        for label, graph in GRAPHS.items():
            for nid, node in graph.items():
                for ref in links(node):
                    with self.subTest(graph=label, node=nid, ref=ref):
                        self.assertIn(ref[0], graph)

    def test_each_graph_has_exactly_one_load_image(self):
        """generate-3d.py finds it by class_type to patch the source in."""
        for label, graph in GRAPHS.items():
            loads = [n for n, d in graph.items() if d["class_type"] == "LoadImage"]
            with self.subTest(graph=label):
                self.assertEqual(len(loads), 1)

    def test_each_graph_has_exactly_one_save_glb(self):
        for label, graph in GRAPHS.items():
            saves = [n for n, d in graph.items() if d["class_type"] == "SaveGLB"]
            with self.subTest(graph=label):
                self.assertEqual(len(saves), 1)

    def test_no_input_is_a_nested_object(self):
        """The §2.6 trap: a dict here validates and then fails at execution."""
        for label, graph in GRAPHS.items():
            for nid, node in graph.items():
                for key, value in node["inputs"].items():
                    with self.subTest(graph=label, node=nid, key=key):
                        self.assertNotIsInstance(value, dict)

    def test_the_dotted_pose_keys_are_present(self):
        pose = node_named(GRAPHS["rig"], "BuildPoseFile")["inputs"]
        for key, value in (("format", "glb"),
                           ("format.mesh_style", "body_mesh"),
                           ("format.mesh_style.bone_vis", "off"),
                           ("format.mesh_style.shader", "default")):
            with self.subTest(key=key):
                self.assertEqual(pose[key], value)

    def test_the_pose_is_exported_at_the_bind_position(self):
        """'absolute' would bake the estimator's camera depth into the root."""
        self.assertEqual(
            node_named(GRAPHS["rig"], "BuildPoseFile")["inputs"]["camera_translation"],
            "off")

    def test_one_figure_only(self):
        """A second detected person would export a second armature."""
        self.assertEqual(
            node_named(GRAPHS["rig"], "BuildPoseFile")["inputs"]["track_index"], 0)

    def test_the_specks_are_dropped_in_graph(self):
        """Spec §2.3 measured 10,878 sub-20-face components on one token."""
        remesh = node_named(GRAPHS["mesh"], "RemeshMesh")["inputs"]
        self.assertGreater(remesh["drop_small_components"], 0)

    def test_no_custom_node_pack_is_required(self):
        """Spec §2.1. Every class_type here ships with ComfyUI."""
        native = {
            "LoadImage", "SaveGLB", "KSampler", "ImageOnlyCheckpointLoader",
            "CLIPVisionEncode", "Hunyuan3Dv2Conditioning", "EmptyLatentHunyuan3Dv2",
            "VAEDecodeHunyuan3D", "VoxelToMesh", "RemeshMesh", "DecimateMesh",
            "SAM3DBody_Loader", "SAM3DBody_Predict", "BuildPoseFile",
        }
        for label, graph in GRAPHS.items():
            for nid, node in graph.items():
                with self.subTest(graph=label, node=nid):
                    self.assertIn(node["class_type"], native)


@unittest.skipUnless(server_is_up(), "no ComfyUI on 127.0.0.1:8000")
class TestAgainstLiveObjectInfo(unittest.TestCase):
    def test_every_node_class_is_registered(self):
        for label, graph in GRAPHS.items():
            for nid, node in graph.items():
                with self.subTest(graph=label, node=nid):
                    self.assertIsNotNone(object_info(node["class_type"]),
                                         "%s is not registered" % node["class_type"])

    def test_the_inputs_are_exactly_what_the_server_requires(self):
        """Missing keys fail at execution; stale ones mean a schema moved."""
        for label, graph in GRAPHS.items():
            for nid, node in graph.items():
                info = object_info(node["class_type"])
                if info is None:
                    continue
                wanted = expected_inputs(info["input"]["required"], node["inputs"])
                optional = list((info["input"].get("optional") or {}).keys())
                given = set(node["inputs"])
                with self.subTest(graph=label, node=nid, direction="missing"):
                    self.assertEqual(sorted(set(wanted) - given), [])
                with self.subTest(graph=label, node=nid, direction="unknown"):
                    self.assertEqual(sorted(given - set(wanted) - set(optional)), [])

    def test_every_combo_value_is_still_on_offer(self):
        """Catches a renamed checkpoint or a dropped sampler."""
        for label, graph in GRAPHS.items():
            for nid, node in graph.items():
                info = object_info(node["class_type"])
                if info is None:
                    continue
                for key, definition in info["input"]["required"].items():
                    kind = definition[0]
                    meta = definition[1] if len(definition) > 1 else {}
                    options = kind if isinstance(kind, list) else (
                        meta.get("options") if kind == "COMBO" else None)
                    value = node["inputs"].get(key)
                    if not options or isinstance(value, list) or value is None:
                        continue
                    with self.subTest(graph=label, node=nid, key=key):
                        self.assertIn(value, options)

    def test_the_models_this_design_measured_are_installed(self):
        """Spec §2.3 and §2.4 name these exactly; nothing else was measured."""
        pairs = (("ImageOnlyCheckpointLoader", "ckpt_name",
                  "hunyuan3d-dit-v2-mv_fp16.safetensors"),
                 ("SAM3DBody_Loader", "model_file",
                  "sam_3d_body_dinov3_bf16.safetensors"))
        for class_type, key, name in pairs:
            definition = object_info(class_type)["input"]["required"][key]
            options = (definition[0] if isinstance(definition[0], list)
                       else definition[1]["options"])
            with self.subTest(model=name):
                self.assertIn(name, options)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 5: Run it**

Run: `python -m unittest test.test_3d_workflows -v`
Expected: PASS. With ComfyUI up, `TestAgainstLiveObjectInfo` adds 4 tests; with it down, those 4 report as skipped.

If `test_the_inputs_are_exactly_what_the_server_requires` fails, the workflow JSON is wrong, not the test — read the key list in the failure and fix the JSON.

- [ ] **Step 6: Sanity-check the walker against the hand-read case**

Not a test — confirms the walker agrees with what was read off the server by hand.

Run:
```bash
python -c "
import json
from test.workflow_schema import expected_inputs, object_info
g = json.load(open('workflows/api/Util_Image_to_RiggedBody_SAM3D_v1.json'))
print(sorted(expected_inputs(object_info('BuildPoseFile')['input']['required'], g['4']['inputs'])))
"
```
Expected: `['camera_translation', 'format', 'format.bone_smooth_window', 'format.mesh_style', 'format.mesh_style.bone_vis', 'format.mesh_style.shader', 'fps', 'pose_data', 'track_index']`

- [ ] **Step 7: Commit**

```bash
git add workflows/api/Util_Image_to_Mesh_Hunyuan3D_v1.json \
        workflows/api/Util_Image_to_RiggedBody_SAM3D_v1.json \
        test/workflow_schema.py test/test_3d_workflows.py
git commit -m "feat: the two checked-in 3D workflows, and a schema test that outlives them"
```

---

### Task 3: The CLI, the manifest selection and the dossier section

**Files:**
- Modify: `generate-3d.py` (append after `apose_prompt()`)
- Test: `test/test_3d_cli.py` (create)

**Interfaces:**
- Consumes: `apose_npc`, `apose_prompt`, `APOSE_STANCE` from Task 1. `art.load_manifest(path) -> dict`, `art.parse_set(spec)`, `npc_gen.DEFAULT_MANIFEST`, `npc_gen.GENDER_WORKFLOWS`, `npc_gen.role_category(npc) -> str`, `art._slug(text) -> str`, `npc_gen._safe(name) -> str`.
- Produces:
  - `STAGES = ("apose", "mesh", "assemble")`
  - `DEFAULT_BLENDER: Path`
  - `find_blender(explicit=None) -> Path`
  - `select_entries(manifest, args) -> list[tuple[str, dict]]`
  - `npc_3d_folder(folder_path) -> Path`
  - `should_skip(folder3d, args) -> bool`
  - `dossier_3d_section(files, workflows, stance) -> str`
  - `append_dossier_3d(path, files, workflows, stance) -> None`
  - `parse_args(argv=None) -> argparse.Namespace` — carries `steps`, `cfg`, `sampler`, `scheduler`, `set`, `workflow`, `gender_workflows`, `rmbg`, `timeout`, `pause`, `overwrite`, `stage`, so `npc_gen.Knobs` and `npc_gen.resolve_recorded_workflow` accept it unchanged
  - `main(argv=None) -> int`

- [ ] **Step 1: Write the failing test**

Create `test/test_3d_cli.py`:

```python
"""Selection, skipping and the dossier section - everything before ComfyUI.

Nothing here queues a job. These are the parts of generate-3d.py that decide
WHICH NPCs get built and WHAT gets recorded afterwards, and they are the parts
a --dry-run has to get right for the run that follows to be worth starting.
"""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from test.helpers import load_3d, manifest_entry

d3 = load_3d()


def manifest_of(*entries):
    """A .generated-npcs.json-shaped dict, keyed by folder path as the real one is."""
    return {"/npcs/%s" % e["name"]: e for e in entries}


class TestSelection(unittest.TestCase):
    def setUp(self):
        self.a = manifest_entry(11)
        self.b = manifest_entry(12)
        self.manifest = manifest_of(self.a, self.b)

    def args(self, argv):
        return d3.parse_args(argv)

    def test_everything_by_default(self):
        picked = d3.select_entries(self.manifest, self.args([]))
        self.assertEqual(len(picked), 2)

    def test_id_picks_exactly_one(self):
        picked = d3.select_entries(self.manifest, self.args(["--id", self.a["id"]]))
        self.assertEqual([e["id"] for _, e in picked], [self.a["id"]])

    def test_an_unknown_id_is_an_error_not_an_empty_run(self):
        """Silently building nothing is the worst answer to a typo'd id."""
        with self.assertRaises(SystemExit):
            d3.select_entries(self.manifest, self.args(["--id", "npc-nobody-0"]))

    def test_filter_matches_the_name(self):
        picked = d3.select_entries(self.manifest, self.args(["--filter", self.a["name"]]))
        self.assertEqual([e["id"] for _, e in picked], [self.a["id"]])

    def test_exclude_removes_it_again(self):
        picked = d3.select_entries(
            self.manifest, self.args(["--exclude", self.a["name"]]))
        self.assertNotIn(self.a["id"], [e["id"] for _, e in picked])

    def test_filter_matches_the_folder_path(self):
        """Spec §8 asks for --filter by category, and the path carries it."""
        manifest = {"/npcs/Crew/one": self.a, "/npcs/Officers/two": self.b}
        picked = d3.select_entries(manifest, self.args(["--filter", "Officers"]))
        self.assertEqual([e["id"] for _, e in picked], [self.b["id"]])

    def test_limit_caps_the_batch(self):
        picked = d3.select_entries(self.manifest, self.args(["--limit", "1"]))
        self.assertEqual(len(picked), 1)

    def test_selection_is_ordered(self):
        """Two runs of the same --limit must pick the same NPCs."""
        first = d3.select_entries(self.manifest, self.args(["--limit", "1"]))
        second = d3.select_entries(self.manifest, self.args(["--limit", "1"]))
        self.assertEqual([k for k, _ in first], [k for k, _ in second])

    def test_non_npc_manifest_rows_are_ignored(self):
        """The manifest is a plain dict; a hand-added row need not be an NPC."""
        manifest = dict(self.manifest, note="a stray string", other={"kind": "mech"})
        picked = d3.select_entries(manifest, self.args([]))
        self.assertEqual(len(picked), 2)


class TestStageFlag(unittest.TestCase):
    def test_all_stages_by_default(self):
        self.assertEqual(list(d3.parse_args([]).stage), list(d3.STAGES))

    def test_one_stage_in_isolation(self):
        self.assertEqual(d3.parse_args(["--stage", "apose"]).stage, ["apose"])

    def test_stages_accumulate(self):
        args = d3.parse_args(["--stage", "apose", "--stage", "mesh"])
        self.assertEqual(args.stage, ["apose", "mesh"])

    def test_an_unknown_stage_is_refused(self):
        with self.assertRaises(SystemExit):
            d3.parse_args(["--stage", "texture"])


class TestSkipping(unittest.TestCase):
    def test_a_fresh_npc_is_not_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(d3.should_skip(Path(tmp) / "3d", d3.parse_args([])))

    def test_an_existing_3d_folder_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "3d"
            folder.mkdir()
            (folder / "apose.png").write_bytes(b"")
            self.assertTrue(d3.should_skip(folder, d3.parse_args([])))

    def test_overwrite_builds_it_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "3d"
            folder.mkdir()
            (folder / "apose.png").write_bytes(b"")
            self.assertFalse(d3.should_skip(folder, d3.parse_args(["--overwrite"])))

    def test_an_empty_3d_folder_is_not_skipped(self):
        """A folder left behind by a crashed run holds nothing worth keeping."""
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "3d"
            folder.mkdir()
            self.assertFalse(d3.should_skip(folder, d3.parse_args([])))


class TestDossierSection(unittest.TestCase):
    FILES = ["Jules Sokolova Rigged.glb", "Jules Sokolova Print.stl"]
    WORKFLOWS = ["workflows/api/Util_Image_to_Mesh_Hunyuan3D_v1.json",
                 "workflows/api/Util_Image_to_RiggedBody_SAM3D_v1.json"]

    def section(self):
        return d3.dossier_3d_section(self.FILES, self.WORKFLOWS, d3.APOSE_STANCE)

    def test_it_lists_every_file(self):
        text = self.section()
        for name in self.FILES:
            with self.subTest(name=name):
                self.assertIn(name, text)

    def test_it_names_both_workflows(self):
        text = self.section()
        for path in self.WORKFLOWS:
            with self.subTest(path=path):
                self.assertIn(Path(path).name, text)

    def test_it_records_the_stance(self):
        """Spec §6.1: the dossier keeps recording everything needed to reproduce."""
        self.assertIn(d3.APOSE_STANCE, self.section())

    def test_appending_twice_leaves_one_section(self):
        """A re-run with --overwrite must replace the section, not stack one."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Jules Sokolova.md"
            path.write_text("# Jules Sokolova\n\n## Art\n\n- `x.png`\n", encoding="utf-8")
            for _ in range(2):
                d3.append_dossier_3d(path, self.FILES, self.WORKFLOWS, d3.APOSE_STANCE)
            self.assertEqual(path.read_text(encoding="utf-8").count("\n## 3D\n"), 1)

    def test_the_existing_dossier_survives(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Jules Sokolova.md"
            path.write_text("# Jules Sokolova\n\n## Art\n\n- `x.png`\n", encoding="utf-8")
            d3.append_dossier_3d(path, self.FILES, self.WORKFLOWS, d3.APOSE_STANCE)
            text = path.read_text(encoding="utf-8")
            self.assertIn("## Art", text)
            self.assertIn("- `x.png`", text)


class TestDryRun(unittest.TestCase):
    def test_it_prints_the_apose_prompt_and_queues_nothing(self):
        entry = manifest_entry(21)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(manifest_of(entry)), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = d3.main(["--manifest", str(path), "--dry-run"])
        self.assertEqual(code, 0)
        output = buffer.getvalue()
        self.assertIn(entry["name"], output)
        self.assertIn(d3.APOSE_STANCE, output)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m unittest test.test_3d_cli -v`
Expected: FAIL with `AttributeError: module 'gen3d' has no attribute 'parse_args'`.

- [ ] **Step 3: Add the CLI, the selection and the dossier section**

Append to `generate-3d.py`. Add `argparse`, `os`, `re` and `time` to the import block at the top:

```python
import argparse
import importlib.util
import os
import re
import sys
import time
from pathlib import Path
```

Then, after `apose_prompt()`:

```python
# --------------------------------------------------------------------------
# Paths and the stages
# --------------------------------------------------------------------------

MESH_WORKFLOW = art.WORKFLOW_DIR / "Util_Image_to_Mesh_Hunyuan3D_v1.json"
RIG_WORKFLOW = art.WORKFLOW_DIR / "Util_Image_to_RiggedBody_SAM3D_v1.json"
ASSEMBLE_SCRIPT = SCRIPT_DIR / "blender" / "assemble_npc.py"

# Named rather than numbered, so `--stage mesh` says what it does. The order
# is the dependency order: mesh needs apose's PNG, assemble needs mesh's GLBs.
STAGES = ("apose", "mesh", "assemble")

# Where Blender 5.2 LTS installs by default on this machine. LANCER_BLENDER
# overrides it, so a different install or a different version needs no edit.
DEFAULT_BLENDER = Path(
    os.environ.get("LANCER_BLENDER")
    or r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")


def find_blender(explicit=None):
    """The Blender executable, or a SystemExit naming what to set."""
    path = Path(explicit) if explicit else DEFAULT_BLENDER
    if not path.exists():
        raise SystemExit(
            "Blender not found: %s\n"
            "  pass --blender PATH, or set LANCER_BLENDER" % path)
    return path


def npc_3d_folder(folder_path):
    """The 3d/ subfolder inside one NPC's own folder.

    Beside the portrait and the token rather than in a tree of its own, so an
    NPC folder stays self-contained - and so the ignore rules that already
    cover output/ and ComfyUI's own output directory cover this too, with no
    new rule to write (spec §7.4).
    """
    return Path(folder_path) / "3d"


def should_skip(folder, args):
    """True when this NPC already has 3D output and --overwrite was not given.

    An EMPTY 3d/ folder does not count: it is what a crashed run leaves
    behind, and skipping on it would make every such NPC permanently
    unbuildable without --overwrite.
    """
    return folder.exists() and any(folder.iterdir()) and not args.overwrite


def select_entries(manifest, args):
    """The (folder_path, entry) pairs this run will build, in a stable order.

    Rows without a 'traits' dict are skipped rather than rejected: the
    manifest is a plain JSON object and nothing stops a hand-added row, but
    the whole 3D rebuild starts from traits.
    """
    pairs = sorted((k, v) for k, v in manifest.items()
                   if isinstance(v, dict) and isinstance(v.get("traits"), dict))

    if args.id:
        wanted = set(args.id)
        pairs = [(k, v) for k, v in pairs if v.get("id") in wanted]
        found = {v.get("id") for _, v in pairs}
        # An unknown id is a typo, and a typo that silently builds nothing is
        # indistinguishable from a run that had nothing to do.
        missing = sorted(wanted - found)
        if missing:
            raise SystemExit("no manifest entry with id %s" % ", ".join(missing))

    def text(folder_path, entry):
        """What --filter and --exclude match against.

        Name, callsign AND the folder path - the path is what carries the role
        category (output/LancerNPCs/run3/Crew/jules-sokolova), so `--filter
        Crew` selects by category without the entry having to store one. Spec
        §8 asks for name or category; this gives both from what is already
        there.
        """
        return "%s %s %s" % (folder_path, entry.get("name", ""),
                             entry.get("callsign", ""))

    if args.filter:
        rx = re.compile(args.filter, re.I)
        pairs = [(k, v) for k, v in pairs if rx.search(text(k, v))]
    if args.exclude:
        rx = re.compile(args.exclude, re.I)
        pairs = [(k, v) for k, v in pairs if not rx.search(text(k, v))]
    if args.limit:
        pairs = pairs[:args.limit]
    return pairs


# --------------------------------------------------------------------------
# The dossier's 3D section
# --------------------------------------------------------------------------

DOSSIER_MARKER = "\n## 3D\n"


def dossier_3d_section(files, workflows, stance):
    """The '## 3D' block: what was built, and everything needed to rebuild it.

    The dossier's existing property is that it records enough to reproduce its
    own output - the seed, the tables, both prompts verbatim. The 3D output is
    reproduced from the two workflow graphs and the forced stance instead, so
    those are what this records.
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
    lines += ["| A-pose stance | %s |" % stance, ""]
    return "\n".join(lines)


def append_dossier_3d(path, files, workflows, stance):
    """Add or REPLACE the dossier's '## 3D' section.

    Replace, because a --overwrite re-run would otherwise stack a second
    section under the first and the dossier would stop describing what is
    actually on disk - which is the only thing it is for.
    """
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    cut = text.find(DOSSIER_MARKER)
    if cut != -1:
        text = text[:cut]
    body = dossier_3d_section(files, workflows, stance)
    path.write_text("%s\n\n%s" % (text.rstrip("\n"), body), encoding="utf-8")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description=__doc__.split("\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Manifest: %s" % npc_gen.DEFAULT_MANIFEST,
    )

    pick = p.add_argument_group("which NPCs")
    pick.add_argument("--manifest", type=Path, default=npc_gen.DEFAULT_MANIFEST,
                      help="the NPC run log to read (default: %(default)s)")
    pick.add_argument("--id", action="append", default=[], metavar="ID",
                      help="build one entry by its manifest \"id\" (repeatable)")
    pick.add_argument("--filter", metavar="REGEX",
                      help="build only NPCs whose name, callsign or folder path "
                           "matches - the path carries the role category")
    pick.add_argument("--exclude", metavar="REGEX",
                      help="skip NPCs matching the same three")
    pick.add_argument("--limit", type=int, metavar="N", help="stop after N NPCs")
    pick.add_argument("--overwrite", action="store_true",
                      help="rebuild an NPC that already has a 3d/ folder")

    stage = p.add_argument_group("which stages")
    stage.add_argument("--stage", action="append", choices=STAGES, default=None,
                       help="run one stage in isolation while iterating "
                            "(repeatable; default: all of %s)" % ", ".join(STAGES))
    stage.add_argument("--blender", type=Path, default=None,
                       help="the Blender executable (default: %s)" % DEFAULT_BLENDER)

    gen = p.add_argument_group("the A-pose render")
    gen.add_argument("--workflow", type=Path, default=art.DEFAULT_WORKFLOW,
                     help="fallback generation workflow, for an entry that records none")
    gen.add_argument("--workflow-woman", type=Path, metavar="PATH",
                     default=npc_gen.GENDER_WORKFLOWS["woman"],
                     help="same, for NPCs who read as women")
    gen.add_argument("--rmbg", type=Path, default=art.POST_ALIASES["rmbg"],
                     help="background-removal workflow (default: %(default)s)")
    gen.add_argument("--steps", type=int, help="override sampler steps")
    gen.add_argument("--cfg", type=float, help="override CFG")
    gen.add_argument("--sampler", help="override sampler_name")
    gen.add_argument("--scheduler", help="override scheduler")
    gen.add_argument("--set", action="append", default=[], metavar="NODE.input=value",
                     help="patch any workflow input, as in generate-art.py")

    run = p.add_argument_group("run mode")
    run.add_argument("--server", help="ComfyUI address, e.g. 127.0.0.1:8000")
    run.add_argument("--dry-run", action="store_true",
                     help="print the NPCs and their A-pose prompts, queue nothing")
    run.add_argument("--timeout", type=float, default=1800,
                     help="per-job timeout in seconds (default: %(default)s)")
    run.add_argument("--pause", type=float, default=2.0,
                     help="seconds to sleep after each ComfyUI job (default: %(default)s)")

    args = p.parse_args(argv)

    if args.stage is None:
        args.stage = list(STAGES)
    if args.limit is not None and args.limit < 1:
        p.error("--limit must be at least 1")

    try:
        args.set = [art.parse_set(spec) for spec in args.set]
    except ValueError as exc:
        p.error(str(exc))

    # resolve_recorded_workflow() and workflow_for() read this off the args
    # object, so the same shape generate-npc.py builds has to be here too.
    args.gender_workflows = dict(npc_gen.GENDER_WORKFLOWS, woman=args.workflow_woman)
    return args


def main(argv=None):
    args = parse_args(argv)

    if not args.manifest.exists():
        raise SystemExit("Manifest not found: %s" % args.manifest)
    manifest = art.load_manifest(args.manifest)
    picked = select_entries(manifest, args)
    if not picked:
        print("nothing selected")
        return 0

    if args.dry_run:
        for folder_path, entry in picked:
            print("\n%s  \"%s\"  -> %s"
                  % (entry["name"], entry.get("callsign", ""),
                     npc_3d_folder(folder_path)))
            print("  stages: %s" % ", ".join(args.stage))
            print("  A-pose token prompt:\n%s" % apose_prompt(entry))
        return 0

    raise SystemExit("stages are not wired up yet - see Task 4")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m unittest test.test_3d_cli -v`
Expected: PASS, 21 tests.

- [ ] **Step 5: Try it by hand against the real manifest**

Run: `python generate-3d.py --limit 2 --dry-run`
Expected: two NPCs printed with their A-pose token prompts, each prompt containing `arms held slightly away from the sides`, none containing a weapon or gear clause. Nothing is queued.

- [ ] **Step 6: Run the whole suite**

Run: `python -m unittest discover -s test -t .`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add generate-3d.py test/test_3d_cli.py
git commit -m "feat: generate-3d.py's CLI, manifest selection and dossier section"
```

---

### Task 4: Stage 0 — the A-pose render

**Files:**
- Modify: `generate-3d.py` (new functions before `parse_args()`; `main()` body)
- Test: `test/test_3d_cli.py` (append one class)

**Interfaces:**
- Consumes: `apose_npc`, `should_skip`, `npc_3d_folder` from Tasks 1 and 3. From `generate-npc.py`: `Knobs(args, size, output_prefix)`, `entry_for(category, slug, stage, prompt) -> art.Entry`, `fetch(comfy, image, target) -> Path`, `resolve_recorded_workflow(entry, npc, args) -> Path`, `role_category(npc) -> str`, `TOKEN_SIZE`, `COMFY_PREFIX`. From `generate-art.py`: `find_server`, `load_api_workflow`, `locate_slots`, `locate_post_slots`, `build_job`, `build_post_job`, `image_ref`, `Comfy.images`.
- Produces:
  - `_multipart(fields, field_name, filename, blob) -> (content_type, body)`
  - `upload_image(comfy, path, subfolder="lancer3d") -> str` — a `LoadImage`-shaped `"sub/name.png [input]"` reference
  - `stage_apose(comfy, args, entry, folder) -> Path` — writes and returns `<folder>/apose.png`

- [ ] **Step 1: Write the failing test**

Append to `test/test_3d_cli.py`, before the `if __name__` block:

```python
class TestMultipart(unittest.TestCase):
    """The upload body is built by hand, so it is worth checking by hand.

    ComfyUI's /upload/image takes multipart/form-data and the standard library
    has no builder for it. Splitting the body construction out from the POST
    is what makes it checkable without a server.
    """

    def body(self):
        return d3._multipart({"type": "input", "subfolder": "lancer3d"},
                             "image", "apose.png", b"\x89PNG\r\n\x1a\n")

    def test_the_boundary_is_declared_and_used(self):
        content_type, body = self.body()
        self.assertTrue(content_type.startswith("multipart/form-data; boundary="))
        boundary = content_type.split("boundary=")[1]
        self.assertIn(boundary.encode(), body)

    def test_it_ends_with_the_closing_boundary(self):
        content_type, body = self.body()
        boundary = content_type.split("boundary=")[1]
        self.assertTrue(body.endswith(("--%s--\r\n" % boundary).encode()))

    def test_every_field_is_present(self):
        _, body = self.body()
        for token in (b'name="type"', b'input', b'name="subfolder"', b'lancer3d',
                      b'name="image"', b'filename="apose.png"'):
            with self.subTest(token=token):
                self.assertIn(token, body)

    def test_the_binary_payload_is_not_mangled(self):
        _, body = self.body()
        self.assertIn(b"\x89PNG\r\n\x1a\n", body)

    def test_the_boundary_does_not_occur_in_the_payload(self):
        """A collision would truncate the upload silently."""
        content_type, _ = self.body()
        boundary = content_type.split("boundary=")[1]
        self.assertNotIn(boundary.encode(), b"\x89PNG\r\n\x1a\n")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m unittest test.test_3d_cli.TestMultipart -v`
Expected: FAIL — `AttributeError: module 'gen3d' has no attribute '_multipart'`.

- [ ] **Step 3: Implement the upload and Stage 0**

Add `json` and `uuid` to `generate-3d.py`'s imports, plus `urllib.request`:

```python
import argparse
import importlib.util
import json
import os
import re
import sys
import time
import urllib.request
import uuid
from pathlib import Path
```

Insert before `parse_args()`:

```python
# --------------------------------------------------------------------------
# Stage 0: the A-pose source render
# --------------------------------------------------------------------------


def _multipart(fields, field_name, filename, blob):
    """A multipart/form-data (content_type, body) for one file plus fields.

    The standard library has no builder for this and ComfyUI's /upload/image
    wants nothing else. Kept separate from the POST so it can be checked
    without a server.
    """
    boundary = "----lancer3d%s" % uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        parts.append(
            ('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n'
             % (boundary, name, value)).encode("utf-8"))
    parts.append(
        ('--%s\r\nContent-Disposition: form-data; name="%s"; filename="%s"\r\n'
         'Content-Type: image/png\r\n\r\n' % (boundary, field_name, filename)).encode("utf-8"))
    parts.append(blob)
    parts.append(("\r\n--%s--\r\n" % boundary).encode("utf-8"))
    return "multipart/form-data; boundary=%s" % boundary, b"".join(parts)


def upload_image(comfy, path, subfolder="lancer3d"):
    """Put one PNG in ComfyUI's input folder; return its LoadImage reference.

    Stage 1 could reference the Stage 0 output where it already sits on the
    server, with image_ref() - but only inside one run. `--stage mesh` on its
    own, which is the whole point of the flag, has nothing but the file on
    disk. Uploading is the one path that works both ways, so it is the only
    path taken.
    """
    content_type, body = _multipart(
        {"type": "input", "subfolder": subfolder, "overwrite": "true"},
        "image", path.name, path.read_bytes())
    request = urllib.request.Request(
        comfy.base + "/upload/image", data=body, headers={"Content-Type": content_type})
    with urllib.request.urlopen(request, timeout=120) as resp:
        info = json.loads(resp.read().decode("utf-8"))
    sub = info.get("subfolder", "")
    name = "%s/%s" % (sub, info["name"]) if sub else info["name"]
    return "%s [input]" % name.replace("\\", "/")


def stage_apose(comfy, args, entry, folder):
    """Render this NPC's token again in the A-pose, cut out. -> <folder>/apose.png

    Renders through the entry's OWN recorded workflow and its own seed, so the
    figure is the same person the token shows - only the pose and the empty
    hands differ. The portrait half of build_prompts() is discarded; nothing
    downstream has a use for a backdrop.
    """
    npc = apose_npc(entry)
    prompt = npc_gen.build_prompts(npc)[1]
    category = npc_gen.role_category(npc)
    slug = art._slug(npc["name"])
    seed = entry["seed"]
    knobs = npc_gen.Knobs(args, npc_gen.TOKEN_SIZE, npc_gen.COMFY_PREFIX)

    workflow_path = npc_gen.resolve_recorded_workflow(entry, npc, args)
    template = art.load_api_workflow(workflow_path)
    try:
        slots = art.locate_slots(template)
    except art.WorkflowError as exc:
        raise SystemExit("%s: %s" % (workflow_path.name, exc))

    job = art.build_job(template, slots,
                        npc_gen.entry_for(category, slug, "apose", prompt), seed, knobs)
    images = art.Comfy.images(comfy.wait(comfy.queue(job), timeout=args.timeout))
    if not images:
        raise RuntimeError("the A-pose render produced no image")
    time.sleep(args.pause)

    if not args.rmbg.exists():
        raise SystemExit("Background-removal workflow not found: %s" % args.rmbg)
    post = art.load_api_workflow(args.rmbg)
    try:
        post_slots = art.locate_post_slots(post)
    except art.WorkflowError as exc:
        raise SystemExit("%s: %s" % (args.rmbg.name, exc))

    prefix = "%s/%s/%s/apose_rmbg" % (npc_gen.COMFY_PREFIX, category, slug)
    cut_job = art.build_post_job(
        post, post_slots, art.image_ref(images[0]), prefix, seed, knobs)
    cut = art.Comfy.images(comfy.wait(comfy.queue(cut_job), timeout=args.timeout))
    if not cut:
        raise RuntimeError("background removal produced no image")
    time.sleep(args.pause)

    return npc_gen.fetch(comfy, cut[0], folder / "apose.png")
```

- [ ] **Step 4: Wire Stage 0 into `main()`**

Replace `main()`'s trailing `raise SystemExit("stages are not wired up yet ...")` with the batch loop. `stage_mesh` and `stage_assemble` land in Tasks 5 and 8; until then the loop runs `apose` only and says so.

```python
    comfy = art.find_server(args.server)
    print("ComfyUI: %s" % comfy.base)

    done = failed = skipped = 0
    started = time.time()
    for folder_path, entry in picked:
        folder = npc_3d_folder(folder_path)
        if should_skip(folder, args):
            print("skip %s (3d/ exists; --overwrite to rebuild)" % entry["name"])
            skipped += 1
            continue

        print("\n%s  \"%s\"  -> %s" % (entry["name"], entry.get("callsign", ""), folder))
        folder.mkdir(parents=True, exist_ok=True)
        try:
            apose = None
            if "apose" in args.stage:
                print("    A-pose render ...", flush=True)
                apose = stage_apose(comfy, args, entry, folder)
                print("      -> %s" % apose.name)
            else:
                apose = folder / "apose.png"
                if not apose.exists():
                    raise RuntimeError(
                        "no apose.png in %s - run --stage apose first" % folder)
        except KeyboardInterrupt:
            print("\ninterrupted - cancelling the running job")
            comfy.cancel_all()
            return 130
        except Exception as exc:
            # Per-NPC isolation, spec §8: one bad reconstruction must not take
            # the rest of a 160-NPC batch with it.
            failed += 1
            print("    ! %s" % exc, file=sys.stderr)
            continue
        done += 1

    print("\ndone: %d built, %d skipped, %d failed, %.1f min"
          % (done, skipped, failed, (time.time() - started) / 60))
    return 1 if failed else 0
```

- [ ] **Step 5: Run the tests**

Run: `python -m unittest test.test_3d_cli -v`
Expected: PASS, 26 tests.

- [ ] **Step 6: Run Stage 0 for real on one NPC**

Pick an id from the live manifest:

```bash
python -c "
import json
m = json.load(open('.generated-npcs.json'))
print(next(v['id'] for v in m.values() if isinstance(v, dict) and 'traits' in v))
"
python generate-3d.py --id <that-id> --stage apose --overwrite
```

Expected: a `3d/apose.png` in that NPC's folder — 1024x1280, transparent background, the figure standing squarely with arms out and empty hands. Open it. If the figure is still holding something, or is not square to the camera, `APOSE_STANCE` needs rewording before Task 5 is worth running: every reconstruction downstream inherits this image.

- [ ] **Step 7: Run the whole suite and commit**

Run: `python -m unittest discover -s test -t .`
Expected: PASS.

```bash
git add generate-3d.py test/test_3d_cli.py
git commit -m "feat: stage 0, the A-pose source render every reconstruction starts from"
```

---

### Task 5: Stage 1 — the two meshes

**Files:**
- Modify: `generate-3d.py` (new functions after `stage_apose()`; `main()`'s loop)
- Test: `test/test_3d_cli.py` (append two classes)

**Interfaces:**
- Consumes: `upload_image`, `MESH_WORKFLOW`, `RIG_WORKFLOW` from Tasks 3 and 4. `npc_gen.fetch(comfy, image, target) -> Path`, `art.load_api_workflow`, `art.WorkflowError`.
- Produces:
  - `node_of(graph, class_type) -> str`
  - `build_mesh_job(template, ref, prefix, seed=None) -> dict`
  - `mesh_outputs(record, suffix=".glb") -> list[dict]`
  - `stage_mesh(comfy, args, entry, folder, apose_png) -> (shell_path, base_path)` writing `<folder>/_shell.glb` and `<folder>/_base.glb`

- [ ] **Step 1: Write the failing test**

Append to `test/test_3d_cli.py`, before the `if __name__` block:

```python
class TestMeshJob(unittest.TestCase):
    """Patching the two graphs, without a server."""

    def setUp(self):
        self.template = json.loads(
            (d3.MESH_WORKFLOW).read_text(encoding="utf-8"))

    def test_the_source_image_is_patched_in(self):
        job = d3.build_mesh_job(self.template, "lancer3d/apose.png [input]", "3d/x")
        load = job[d3.node_of(job, "LoadImage")]
        self.assertEqual(load["inputs"]["image"], "lancer3d/apose.png [input]")

    def test_the_output_prefix_is_patched_in(self):
        job = d3.build_mesh_job(self.template, "a.png [input]", "LancerNPCs/Crew/jules/shell")
        save = job[d3.node_of(job, "SaveGLB")]
        self.assertEqual(save["inputs"]["filename_prefix"], "LancerNPCs/Crew/jules/shell")

    def test_the_template_on_disk_is_not_mutated(self):
        """One template is patched once per NPC across a 160-NPC batch."""
        before = json.dumps(self.template, sort_keys=True)
        d3.build_mesh_job(self.template, "a.png [input]", "3d/x")
        self.assertEqual(json.dumps(self.template, sort_keys=True), before)

    def test_the_seed_reaches_every_sampler(self):
        job = d3.build_mesh_job(self.template, "a.png [input]", "3d/x", seed=4242)
        seeds = [n["inputs"]["seed"] for n in job.values()
                 if n["class_type"] == "KSampler"]
        self.assertEqual(seeds, [4242])

    def test_node_of_refuses_an_ambiguous_graph(self):
        graph = {"1": {"class_type": "LoadImage", "inputs": {}},
                 "2": {"class_type": "LoadImage", "inputs": {}}}
        with self.assertRaises(d3.art.WorkflowError):
            d3.node_of(graph, "LoadImage")

    def test_node_of_refuses_a_missing_node(self):
        with self.assertRaises(d3.art.WorkflowError):
            d3.node_of({}, "SaveGLB")


class TestMeshOutputs(unittest.TestCase):
    """SaveGLB does not report under "images", and its key has moved before.

    Reading every list of file dicts in the record, rather than one hardcoded
    UI key, is what stops a ComfyUI rename turning into "the job produced no
    .glb" on a job that produced one.
    """

    def test_it_finds_a_glb_under_any_key(self):
        for key in ("3d", "result", "images", "gltf"):
            record = {"outputs": {"5": {key: [
                {"filename": "base_00001_.glb", "subfolder": "3d", "type": "output"}]}}}
            with self.subTest(key=key):
                found = d3.mesh_outputs(record)
                self.assertEqual([f["filename"] for f in found], ["base_00001_.glb"])

    def test_it_ignores_a_png_beside_the_glb(self):
        record = {"outputs": {"5": {"images": [
            {"filename": "preview.png"}, {"filename": "base.glb"}]}}}
        self.assertEqual([f["filename"] for f in d3.mesh_outputs(record)], ["base.glb"])

    def test_it_survives_a_record_with_no_outputs(self):
        self.assertEqual(d3.mesh_outputs({}), [])

    def test_it_survives_scalar_output_values(self):
        record = {"outputs": {"5": {"text": "done", "count": 3}}}
        self.assertEqual(d3.mesh_outputs(record), [])
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m unittest test.test_3d_cli.TestMeshJob test.test_3d_cli.TestMeshOutputs -v`
Expected: FAIL — `AttributeError: module 'gen3d' has no attribute 'build_mesh_job'`.

- [ ] **Step 3: Implement Stage 1**

Append to `generate-3d.py` after `stage_apose()`:

```python
# --------------------------------------------------------------------------
# Stage 1: the two meshes
# --------------------------------------------------------------------------


def node_of(graph, class_type):
    """The one node of that class_type, or a WorkflowError naming the count.

    Both 3D graphs are checked in beside this script, so addressing their
    nodes by class rather than by id survives a re-export from the ComfyUI
    editor - which renumbers every node - while still failing loudly if
    someone adds a second LoadImage.
    """
    found = [n for n, d in graph.items() if d.get("class_type") == class_type]
    if len(found) != 1:
        raise art.WorkflowError(
            "expected exactly one %s node, found %d" % (class_type, len(found)))
    return found[0]


def build_mesh_job(template, ref, prefix, seed=None):
    """One queueable image -> mesh job. The template is left untouched."""
    graph = json.loads(json.dumps(template))
    graph[node_of(graph, "LoadImage")]["inputs"]["image"] = ref
    graph[node_of(graph, "SaveGLB")]["inputs"]["filename_prefix"] = prefix
    if seed is not None:
        for node in graph.values():
            if node.get("class_type") == "KSampler":
                node["inputs"]["seed"] = seed
    return graph


def mesh_outputs(record, suffix=".glb"):
    """Every saved file in a history record whose filename ends in `suffix`.

    Comfy.images() reads the "images" key, which is right for an image node
    and wrong for SaveGLB - a 3D save reports under a UI key of its own, and
    which key that is has changed between ComfyUI versions. Walking every list
    of file dicts in the record costs nothing and makes a rename upstream a
    non-event, where a hardcoded key would turn "the key moved" into "the job
    produced no .glb".
    """
    out = []
    for node_output in record.get("outputs", {}).values():
        for value in node_output.values():
            if not isinstance(value, list):
                continue
            for item in value:
                if (isinstance(item, dict)
                        and str(item.get("filename", "")).endswith(suffix)):
                    out.append(item)
    return out


def stage_mesh(comfy, args, entry, folder, apose_png):
    """Reconstruct a clothed shell and a rigged body from one A-pose image.

    Two jobs from one source, deliberately: the Hunyuan3D shell has the
    clothing and the silhouette but a fragmented head and no rig (spec §2.3),
    and the SAM3DBody base has a clean 127-bone rig and a real face but no
    clothes (spec §2.4). Neither is the deliverable; Stage 2 is where they
    become one.

    Both files are underscore-prefixed because they are intermediates - the
    named deliverables of §6.1 land beside them.
    """
    npc = apose_npc(entry)
    category = npc_gen.role_category(npc)
    slug = art._slug(npc["name"])
    ref = upload_image(comfy, apose_png)

    written = []
    for workflow, label, target in (
            (MESH_WORKFLOW, "shell", folder / "_shell.glb"),
            (RIG_WORKFLOW, "base", folder / "_base.glb")):
        if not workflow.exists():
            raise SystemExit("Workflow not found: %s" % workflow)
        print("    %s ..." % label, flush=True)
        template = art.load_api_workflow(workflow)
        prefix = "%s/%s/%s/%s" % (npc_gen.COMFY_PREFIX, category, slug, label)
        job = build_mesh_job(template, ref, prefix, entry["seed"])
        record = comfy.wait(comfy.queue(job), timeout=args.timeout)
        files = mesh_outputs(record)
        if not files:
            raise RuntimeError("the %s job produced no .glb" % label)
        written.append(npc_gen.fetch(comfy, files[0], target))
        print("      -> %s" % target.name)
        time.sleep(args.pause)

    return tuple(written)
```

- [ ] **Step 4: Wire Stage 1 into `main()`'s loop**

In `main()`, inside the `try:` and directly after the `apose` block:

```python
            shell = folder / "_shell.glb"
            base = folder / "_base.glb"
            if "mesh" in args.stage:
                shell, base = stage_mesh(comfy, args, entry, folder, apose)
            elif "assemble" in args.stage and not (shell.exists() and base.exists()):
                raise RuntimeError(
                    "no _shell.glb / _base.glb in %s - run --stage mesh first" % folder)
```

- [ ] **Step 5: Run the tests**

Run: `python -m unittest test.test_3d_cli -v`
Expected: PASS, 36 tests.

- [ ] **Step 6: Run Stages 0 and 1 for real on one NPC**

```bash
python generate-3d.py --id <the-same-id> --stage apose --stage mesh --overwrite
```

Expected: `apose.png`, `_shell.glb` and `_base.glb` in that NPC's `3d/` folder. The SAM3DBody job should take about 5 seconds (spec §2.4); the Hunyuan3D job is the slow one.

Confirm both GLBs are real, not empty:

```bash
python -c "
from pathlib import Path
import sys
for p in sorted(Path(sys.argv[1]).glob('*.glb')):
    print(p.name, p.stat().st_size)
" "<npc folder>/3d"
```
Expected: two files, both well over 100 KB.

- [ ] **Step 7: Run the whole suite and commit**

Run: `python -m unittest discover -s test -t .`
Expected: PASS.

```bash
git add generate-3d.py test/test_3d_cli.py
git commit -m "feat: stage 1, the Hunyuan3D shell and the SAM3DBody rigged base"
```

**Phase 1 is complete here.** Two GLBs on disk for any NPC in the back catalogue, no Blender involved.

---

# Phase 2 — Stage 2 without rigging

Delivers the printing and VTT goals in full: a cleaned shell, a manifold 32 mm STL and four turnaround renders. Nothing here depends on the unproven weight transfer of spec §7.1.

---

### Task 6: The Blender fixtures, the mesh module, and the STL

**Files:**
- Create: `blender/npc_mesh.py`
- Create: `blender/assemble_npc.py`
- Create: `test/fixtures/3d/make_fixtures.py`
- Create (generated, committed): `test/fixtures/3d/base.glb`, `test/fixtures/3d/shell.glb`
- Test: `test/test_3d_assembly.py` (create)

**Interfaces:**
- Consumes: nothing from Phase 1. This task runs entirely inside Blender and against fixtures.
- Produces:
  - `blender/npc_mesh.py`: `clear_scene()`, `import_glb(path, guess_bind_pose=True) -> list`, `armature_of(objects)`, `meshes_of(objects) -> list`, `rest_pose(armature)`, `join(objects, name) -> obj`, `height_of(obj) -> float`, `apply_transforms(obj)`, `fit_to_height(obj, target_z)`, `world_bounds(obj) -> (Vector, Vector)`, `align_to(obj, reference)`, `drop_to_floor(obj)`, `keep_largest_component(obj) -> int`, `weld(obj, distance=0.0005)`, `fill_holes(obj)`, `remesh(obj, voxel_size)`, `non_manifold_edges(obj) -> int`, `clean_shell(obj, weld_distance=0.0005, voxel_size=0.0) -> int`, `export_glb(objects, path)`, `export_stl(obj, path, height_mm)`
  - `blender/assemble_npc.py`: `parse_argv(argv) -> Namespace`, `main() -> None`, and the `LANCER3D {json}` report line on stdout. Phase 2's report keys are `files`, `shell_height_m`, `components_dropped`, `non_manifold`, `rigged`.

- [ ] **Step 1: Write the fixture generator and run it**

The Blender stage has to be testable without a GPU, a ComfyUI or a 4.6 GB model (spec §10). Two tiny GLBs standing in for the real pair do that, and building them from a script means the next person can regenerate them rather than reverse-engineer them.

Create `test/fixtures/3d/make_fixtures.py`:

```python
"""Regenerate the two fixture GLBs the Blender stage is tested against.

Not run by the test suite - the outputs are committed. Run it by hand when
the assembly's expectations change:

    "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" \\
        --background --factory-startup --python test/fixtures/3d/make_fixtures.py

base.glb  stands in for the SAM3DBody export: a rigged figure at real-world
          scale in metres, with an animation track to be discarded. Three
          bones, not 127 - the assembly does not care how many there are, only
          that they exist and carry weights.
shell.glb stands in for the Hunyuan3D export: unit-scaled, unrigged, wider
          than the body it wraps (a jacket), and carrying one detached speck,
          which is the thing spec §2.3 measured 10,878 of.
"""
import math
import sys
from pathlib import Path

import bpy

OUT = Path(__file__).resolve().parent
BODY_HEIGHT_M = 1.73


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def cylinder(name, radius, depth, location=(0, 0, 0), vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.active_object
    obj.name = name
    return obj


def make_base():
    reset()
    body = cylinder("body", 0.15, BODY_HEIGHT_M, (0, 0, BODY_HEIGHT_M / 2))

    bpy.ops.object.armature_add(location=(0, 0, 0))
    armature = bpy.context.active_object
    armature.name = "rig"
    bpy.ops.object.mode_set(mode='EDIT')
    bones = armature.data.edit_bones
    root = bones[0]
    root.name = "hips"
    root.head, root.tail = (0, 0, 0), (0, 0, BODY_HEIGHT_M / 3)
    spine = bones.new("spine")
    spine.head, spine.tail = root.tail, (0, 0, 2 * BODY_HEIGHT_M / 3)
    spine.parent = root
    head = bones.new("head")
    head.head, head.tail = spine.tail, (0, 0, BODY_HEIGHT_M)
    head.parent = spine
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')

    # An animation track, so 'discard the predicted pose' has something to
    # discard - the real base always carries one (spec §2.4).
    bpy.ops.object.mode_set(mode='POSE')
    bone = armature.pose.bones["spine"]
    bone.rotation_mode = 'XYZ'
    bone.rotation_euler = (math.radians(55), 0, 0)
    bone.keyframe_insert("rotation_euler", frame=1)
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(OUT / "base.glb"),
                              export_format='GLB', use_selection=True)


def make_shell():
    reset()
    # Unit-scaled, as Hunyuan3D's output is: a whole metre shorter than the
    # base, so the assembly's scale normalisation is genuinely exercised.
    jacket = cylinder("jacket", 0.20, 1.0, (0, 0, 0.5))
    speck = cylinder("speck", 0.01, 0.02, (0.6, 0, 0.5), vertices=6)

    bpy.ops.object.select_all(action='DESELECT')
    jacket.select_set(True)
    speck.select_set(True)
    bpy.context.view_layer.objects.active = jacket
    bpy.ops.object.join()          # one object, two loose parts

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(OUT / "shell.glb"),
                              export_format='GLB', use_selection=True)


if __name__ == "__main__":
    make_base()
    make_shell()
    for name in ("base.glb", "shell.glb"):
        print("wrote %s (%d bytes)" % (name, (OUT / name).stat().st_size),
              file=sys.stderr)
```

Run:
```bash
mkdir -p test/fixtures/3d
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
    --background --factory-startup --python test/fixtures/3d/make_fixtures.py
```
Expected: `wrote base.glb (...)` and `wrote shell.glb (...)`, both a few KB.

- [ ] **Step 2: Write the failing test**

Create `test/test_3d_assembly.py`:

```python
"""The Blender assembly, against two committed fixture GLBs.

No GPU, no ComfyUI and no 4.6 GB model: the fixtures stand in for the real
pair, and everything the assembly promises about them - one component, closed
surface, real-world scale in, millimetres out - is a property of any pair, not
of these two.

Skipped rather than failed when Blender is not installed, so the suite still
passes on a machine that only ever runs the 2D generator.
"""
import json
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

from test.helpers import REPO, load_3d

d3 = load_3d()
FIXTURES = REPO / "test" / "fixtures" / "3d"
BASE = FIXTURES / "base.glb"
SHELL = FIXTURES / "shell.glb"
SCRIPT = REPO / "blender" / "assemble_npc.py"
STEM = "Fixture Figure"


def blender_or_none():
    try:
        return d3.find_blender()
    except SystemExit:
        return None


BLENDER = blender_or_none()


def stl_triangles(path):
    """Triangle count from a binary STL header, checked against the file size.

    Parsed by hand rather than with a library: the whole point of the STL is
    that a slicer can read it, and the format's 84-byte header plus 50 bytes
    per triangle is small enough to check without adding a dependency.
    """
    data = path.read_bytes()
    if len(data) < 84:
        return 0
    count = struct.unpack("<I", data[80:84])[0]
    return count if len(data) == 84 + count * 50 else -1


def run_assembly(outdir, *extra):
    proc = subprocess.run(
        [str(BLENDER), "--background", "--factory-startup", "--python", str(SCRIPT),
         "--", str(BASE), str(SHELL), str(outdir), "--stem", STEM] + list(extra),
        capture_output=True, text=True, timeout=600)
    line = next((l for l in proc.stdout.splitlines() if l.startswith("LANCER3D ")), None)
    if line is None:
        raise AssertionError(
            "no LANCER3D report line.\nstdout:\n%s\nstderr:\n%s"
            % (proc.stdout[-3000:], proc.stderr[-3000:]))
    return json.loads(line[len("LANCER3D "):]), proc


@unittest.skipUnless(BLENDER, "Blender not installed")
class TestAssembly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.outdir = Path(cls._tmp.name)
        # No --no-render yet: turnarounds arrive in the next task, and this
        # call grows the flag there.
        cls.report, cls.proc = run_assembly(cls.outdir)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_it_exits_cleanly(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr[-3000:])

    def test_the_shell_is_written(self):
        path = self.outdir / ("%s Shell.glb" % STEM)
        self.assertTrue(path.exists())
        self.assertGreater(path.stat().st_size, 0)

    def test_the_stl_is_written(self):
        path = self.outdir / ("%s Print.stl" % STEM)
        self.assertTrue(path.exists())
        self.assertGreater(path.stat().st_size, 0)

    def test_the_stl_is_a_well_formed_binary_stl(self):
        self.assertGreater(stl_triangles(self.outdir / ("%s Print.stl" % STEM)), 0)

    def test_the_speck_is_dropped(self):
        """The fixture shell carries exactly one detached part."""
        self.assertEqual(self.report["components_dropped"], 1)

    def test_the_surface_is_closed(self):
        """Spec §6 step 7: a stage that cannot promise this fails loudly."""
        self.assertEqual(self.report["non_manifold"], 0)

    def test_the_shell_is_scaled_to_the_base(self):
        """The fixture shell arrives unit-scaled; the base is 1.73 m."""
        self.assertAlmostEqual(self.report["shell_height_m"], 1.73, places=2)

    def test_the_report_says_it_is_unrigged(self):
        self.assertFalse(self.report["rigged"])

    def test_every_reported_file_is_on_disk(self):
        for name in self.report["files"]:
            with self.subTest(name=name):
                self.assertTrue((self.outdir / name).exists())


@unittest.skipUnless(BLENDER, "Blender not installed")
class TestAssemblyFailsLoudly(unittest.TestCase):
    def test_a_missing_input_is_a_non_zero_exit(self):
        """Quietly writing nothing is the one thing this must never do."""
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [str(BLENDER), "--background", "--factory-startup", "--python",
                 str(SCRIPT), "--", str(FIXTURES / "nope.glb"), str(SHELL), tmp,
                 "--stem", STEM],
                capture_output=True, text=True, timeout=600)
        self.assertNotEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run it to verify it fails**

Run: `python -m unittest test.test_3d_assembly -v`
Expected: FAIL — the `--python` target `blender/assemble_npc.py` does not exist, so no `LANCER3D` line is printed and `run_assembly` raises.

- [ ] **Step 4: Write the mesh module**

Create `blender/npc_mesh.py`:

```python
"""Mesh work for the NPC assembly: import, align, clean, export.

Runs inside Blender's own Python. bpy and bmesh are available; nothing else
is, and nothing else may be - spec §2.2 rules out any dependency that needs a
compiler, and Blender's interpreter has no site-packages of ours anyway.

Every operator name here is the Blender 5.2 spelling. Two are easy to get
wrong from memory: the STL exporter is `wm.stl_export` (the 4.2+ operator,
not `export_mesh.stl`), and the render engine enum is `BLENDER_EEVEE`, not
`BLENDER_EEVEE_NEXT`.
"""
import bmesh
import bpy
from mathutils import Vector


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_glb(path, guess_bind_pose=True):
    """Import one GLB and return only the objects it added.

    guess_bind_pose=False for the SAM3DBody base. The importer's default is to
    reconstruct a bind pose from the animation's first frame, and that frame is
    exactly the crouched, spike-fingered prediction spec §2.4 measured - so
    guessing from it would bake the bad pose into the rest position, where
    pose_position='REST' could no longer discard it.
    """
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path), guess_original_bind_pose=guess_bind_pose)
    added = [o for o in bpy.data.objects if o not in before]
    if not added:
        raise RuntimeError("%s imported nothing" % path)
    return added


def armature_of(objects):
    return next((o for o in objects if o.type == 'ARMATURE'), None)


def meshes_of(objects):
    return [o for o in objects if o.type == 'MESH']


def rest_pose(armature):
    """Discard the predicted pose, leaving the A-pose bind position.

    Spec §2.4: the prediction fails on this house style and was never the
    valuable part - a rigged character wants a neutral bind pose, which is
    what the rest position already is.
    """
    armature.data.pose_position = 'REST'
    for obj in [armature] + list(armature.children):
        if obj.animation_data:
            obj.animation_data_clear()
    bpy.context.view_layer.update()


def _activate(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def join(objects, name):
    """Join every mesh in `objects` into one object called `name`."""
    meshes = meshes_of(objects)
    if not meshes:
        raise RuntimeError("nothing to join - no mesh among %d objects" % len(objects))
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active
    joined.name = name
    return joined


def apply_transforms(obj):
    _activate(obj)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def height_of(obj):
    """The object's Z extent. glTF is Y-up; the importer converts to Z-up."""
    bpy.context.view_layer.update()
    return obj.dimensions.z


def fit_to_height(obj, target_z):
    """Scale uniformly so the Z extent is `target_z`."""
    current = height_of(obj)
    if current <= 0:
        raise RuntimeError("%s has no height to scale" % obj.name)
    factor = target_z / current
    obj.scale = [component * factor for component in obj.scale]
    apply_transforms(obj)


def world_bounds(obj):
    """The (min, max) corners of the object's world-space bounding box."""
    bpy.context.view_layer.update()
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    low = Vector((min(c.x for c in corners), min(c.y for c in corners),
                  min(c.z for c in corners)))
    high = Vector((max(c.x for c in corners), max(c.y for c in corners),
                   max(c.z for c in corners)))
    return low, high


def align_to(obj, reference):
    """Move `obj` so its footprint centre and its floor match `reference`'s.

    ONLY `obj` moves, and that is the point. The base's mesh and its armature
    are already in correspondence; applying a transform to the mesh alone would
    break it, and the symptom - a rig that animates a figure standing somewhere
    else - looks nothing like its cause. So the base defines the coordinate
    frame and is never touched, and the shell is what comes to meet it.

    Two figures standing on the same floor, centred on the same axis, at the
    same height, are in correspondence closely enough for a proximity transfer.
    """
    low, high = world_bounds(obj)
    ref_low, ref_high = world_bounds(reference)
    obj.location.x += ((ref_low.x + ref_high.x) - (low.x + high.x)) / 2
    obj.location.y += ((ref_low.y + ref_high.y) - (low.y + high.y)) / 2
    obj.location.z += ref_low.z - low.z
    apply_transforms(obj)


def drop_to_floor(obj):
    """Centre X and Y on the world origin, and put the lowest point on Z=0.

    For the STL copy only. A print wants its model sitting on the build plate
    at the origin; nothing else here does, and nothing else may use this - see
    align_to() for why the base must not be moved.
    """
    low, high = world_bounds(obj)
    obj.location.x -= (low.x + high.x) / 2
    obj.location.y -= (low.y + high.y) / 2
    obj.location.z -= low.z
    apply_transforms(obj)


def _components(bm):
    """One set of vertex indices per connected component."""
    seen = set()
    groups = []
    for vert in bm.verts:
        if vert.index in seen:
            continue
        stack, group = [vert], set()
        while stack:
            current = stack.pop()
            if current.index in group:
                continue
            group.add(current.index)
            for edge in current.link_edges:
                other = edge.other_vert(current)
                if other.index not in group:
                    stack.append(other)
        seen |= group
        groups.append(group)
    return groups


def keep_largest_component(obj):
    """Delete every loose part but the biggest. Returns how many were dropped.

    Spec §2.3 measured 10,895 components on a raw reconstruction with 83.5% of
    the faces in one of them. RemeshMesh's drop_small_components removes most
    of that in-graph; this is the backstop for whatever survives, and it is why
    the STL can promise a single body.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    groups = _components(bm)
    if len(groups) > 1:
        biggest = max(groups, key=len)
        doomed = [v for v in bm.verts if v.index not in biggest]
        bmesh.ops.delete(bm, geom=doomed, context='VERTS')
        bm.to_mesh(obj.data)
        obj.data.update()
    bm.free()
    return max(len(groups) - 1, 0)


def weld(obj, distance=0.0005):
    """Merge vertices closer than `distance`, in metres."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=distance)
    bm.to_mesh(obj.data)
    obj.data.update()
    bm.free()


def fill_holes(obj):
    """Cap every boundary loop. sides=0 means no size limit."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=0)
    bm.to_mesh(obj.data)
    obj.data.update()
    bm.free()


def remesh(obj, voxel_size):
    """Voxel remesh: the last resort that guarantees a closed surface."""
    modifier = obj.modifiers.new("remesh", 'REMESH')
    modifier.mode = 'VOXEL'
    modifier.voxel_size = voxel_size
    _activate(obj)
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def non_manifold_edges(obj):
    """Edges bounded by anything other than exactly two faces."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    count = sum(1 for edge in bm.edges if len(edge.link_faces) != 2)
    bm.free()
    return count


def clean_shell(obj, weld_distance=0.0005, voxel_size=0.0):
    """Largest part only, welded, capped, optionally remeshed. Returns drops.

    In that order: dropping the specks first means the weld and the hole fill
    are not asked to reason about 10,000 stray triangles, and the remesh - when
    it is asked for at all - runs on a surface that is already nearly closed.
    """
    dropped = keep_largest_component(obj)
    weld(obj, weld_distance)
    fill_holes(obj)
    if voxel_size > 0:
        remesh(obj, voxel_size)
    return dropped


def export_glb(objects, path):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format='GLB', use_selection=True,
        export_animations=False)


def export_stl(obj, path, height_mm):
    """Export a copy of `obj` scaled so its height is `height_mm`.

    STL carries no units and every slicer reads it as millimetres, so scaling
    the copy to 32 Blender units and exporting at global_scale 1.0 is what
    makes it come off the printer 32 mm tall.

    A copy, because the same object is still wanted at real-world scale for the
    GLB and the turnarounds, and transform_apply is destructive.
    """
    copy = obj.copy()
    copy.data = obj.data.copy()
    bpy.context.collection.objects.link(copy)
    try:
        fit_to_height(copy, height_mm)
        drop_to_floor(copy)
        _activate(copy)
        bpy.ops.wm.stl_export(
            filepath=str(path), export_selected_objects=True,
            global_scale=1.0, apply_modifiers=True, ascii_format=False)
    finally:
        bpy.data.objects.remove(copy, do_unlink=True)
```

- [ ] **Step 5: Write the assembly entry point**

Create `blender/assemble_npc.py`:

```python
"""Assemble one NPC's two reconstructions into the deliverables.

Invoked headless by generate-3d.py:

    blender --background --factory-startup --python blender/assemble_npc.py -- \\
        <base.glb> <shell.glb> <outdir> --stem "<Name>"

Reports on stdout as a single machine-readable line:

    LANCER3D {"files": [...], "non_manifold": 0, ...}

A line rather than prose, because two callers read it - generate-3d.py, which
turns it into a dossier section, and the test suite, which asserts on it - and
neither should be parsing English. Blender writes a great deal else to stdout;
the prefix is what makes the report findable in it.
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Blender does not put a --python script's own directory on sys.path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import npc_mesh  # noqa: E402  (must follow the sys.path line)


def parse_argv(argv):
    p = argparse.ArgumentParser(prog="assemble_npc.py")
    p.add_argument("base", type=Path, help="the SAM3DBody rigged body GLB")
    p.add_argument("shell", type=Path, help="the Hunyuan3D clothed shell GLB")
    p.add_argument("outdir", type=Path, help="where the deliverables are written")
    p.add_argument("--stem", required=True, help="the NPC's filename stem")
    p.add_argument("--print-height-mm", type=float, default=32.0,
                   help="mini height in millimetres (default: %(default)s)")
    p.add_argument("--weld", type=float, default=0.0005,
                   help="weld distance in metres (default: %(default)s)")
    p.add_argument("--voxel", type=float, default=0.0,
                   help="voxel remesh size in metres; 0 disables (default: %(default)s)")
    return p.parse_args(argv)


def script_argv():
    """Everything after Blender's own '--' separator."""
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def main():
    args = parse_argv(script_argv())
    for path in (args.base, args.shell):
        if not path.exists():
            raise SystemExit("not found: %s" % path)
    args.outdir.mkdir(parents=True, exist_ok=True)

    npc_mesh.clear_scene()

    # The base first: it is the only thing that knows what real-world scale is.
    base_objects = npc_mesh.import_glb(args.base, guess_bind_pose=False)
    armature = npc_mesh.armature_of(base_objects)
    if armature is None:
        raise SystemExit("%s has no armature - not a SAM3DBody body_mesh export"
                         % args.base.name)
    npc_mesh.rest_pose(armature)
    body = npc_mesh.join(base_objects, "base_body")
    body_height = npc_mesh.height_of(body)
    if body_height <= 0:
        raise SystemExit("the base has no height")

    # The base is never transformed - it defines the frame, and moving its mesh
    # out from under its armature is the one way to break a rig invisibly. The
    # shell is what gets scaled and moved.
    shell_objects = npc_mesh.import_glb(args.shell)
    shell = npc_mesh.join(shell_objects, "shell")
    dropped = npc_mesh.clean_shell(shell, args.weld, args.voxel)
    npc_mesh.fit_to_height(shell, body_height)
    npc_mesh.align_to(shell, body)

    non_manifold = npc_mesh.non_manifold_edges(shell)
    if non_manifold:
        # Spec §6 step 7. A slicer given a leaking mesh produces a mini with
        # holes in it, hours later, with no warning - so this fails here.
        raise SystemExit(
            "the cleaned shell has %d non-manifold edges; it would not print. "
            "Raise --voxel to force a closed remesh." % non_manifold)

    files = []
    shell_glb = args.outdir / ("%s Shell.glb" % args.stem)
    npc_mesh.export_glb([shell], shell_glb)
    files.append(shell_glb.name)

    print_stl = args.outdir / ("%s Print.stl" % args.stem)
    npc_mesh.export_stl(shell, print_stl, args.print_height_mm)
    files.append(print_stl.name)

    print("LANCER3D " + json.dumps({
        "files": files,
        "shell_height_m": round(npc_mesh.height_of(shell), 4),
        "components_dropped": dropped,
        "non_manifold": non_manifold,
        "rigged": False,
    }))


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `python -m unittest test.test_3d_assembly -v`
Expected: PASS, 10 tests.

A `SystemExit` inside a Blender `--python` script exits non-zero, which is what `TestAssemblyFailsLoudly` relies on. If that test fails, the script is swallowing the exit — check that `main()` is not wrapped in a bare `except`.

- [ ] **Step 7: Run the whole suite and commit**

Run: `python -m unittest discover -s test -t .`
Expected: PASS.

```bash
git add blender/npc_mesh.py blender/assemble_npc.py \
        test/fixtures/3d/make_fixtures.py test/fixtures/3d/base.glb \
        test/fixtures/3d/shell.glb test/test_3d_assembly.py
git commit -m "feat: the Blender assembly, the cleaned shell and the 32mm print STL"
```

---

### Task 7: The turnaround renders

**Files:**
- Create: `blender/npc_render.py`
- Modify: `blender/assemble_npc.py` (`parse_argv()`, `main()`)
- Test: `test/test_3d_assembly.py` (append one class)

**Interfaces:**
- Consumes: `npc_mesh.height_of(obj)` from Task 6.
- Produces:
  - `npc_render.setup(engine, size, samples)` — world, light and render settings
  - `npc_render.frame_camera(obj, angle_deg, margin=1.25) -> bpy.types.Object`
  - `npc_render.turnaround(obj, outdir, stem, angles=(0, 90, 180, 270), size=768, engine='BLENDER_EEVEE', samples=16) -> list[str]`
  - `assemble_npc.py` gains `--no-render`, `--turnaround-size`, `--engine`, `--samples`; its report gains no new keys — the PNGs join `files`.

- [ ] **Step 1: Write the failing test**

Append to `test/test_3d_assembly.py`, before the `if __name__` block:

```python
@unittest.skipUnless(BLENDER, "Blender not installed")
class TestTurnarounds(unittest.TestCase):
    """Rendered on CPU Cycles at 64px, so no GPU and no display is needed.

    The engine is a flag precisely so this test can pick the one that always
    works headless. A real run uses EEVEE, which is far faster and needs the
    GPU that is there anyway.
    """

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.outdir = Path(cls._tmp.name)
        cls.report, cls.proc = run_assembly(
            cls.outdir, "--engine", "CYCLES", "--samples", "1",
            "--turnaround-size", "64")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_it_exits_cleanly(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr[-3000:])

    def test_all_four_angles_are_rendered(self):
        for angle in ("000", "090", "180", "270"):
            path = self.outdir / ("%s Turnaround_%s.png" % (STEM, angle))
            with self.subTest(angle=angle):
                self.assertTrue(path.exists(), "missing %s" % path.name)
                self.assertGreater(path.stat().st_size, 0)

    def test_they_are_real_pngs(self):
        path = self.outdir / ("%s Turnaround_000.png" % STEM)
        self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_they_are_listed_in_the_report(self):
        names = [n for n in self.report["files"] if n.endswith(".png")]
        self.assertEqual(len(names), 4)

    def test_no_render_skips_them(self):
        """--no-render is what makes iterating on the mesh work bearable.

        Its own run rather than a peek at TestAssembly's report: a test that
        reads another class's state passes or fails on class ordering, and
        fails outright when run alone.
        """
        with tempfile.TemporaryDirectory() as tmp:
            report, _ = run_assembly(Path(tmp), "--no-render")
        self.assertEqual([n for n in report["files"] if n.endswith(".png")], [])
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m unittest test.test_3d_assembly.TestTurnarounds -v`
Expected: FAIL — `assemble_npc.py: error: unrecognized arguments: --engine CYCLES`.

- [ ] **Step 3: Write the render module**

Create `blender/npc_render.py`:

```python
"""Orbit renders of one assembled NPC, for the Foundry VTT side of the goal.

Four views of the same person from four angles is what a token cannot give
you, and it is the cheapest useful thing to do with a mesh once it exists.

The engine is a parameter, not a constant. EEVEE is what a real run wants -
it is an order of magnitude faster and the GPU is there - but it needs a GL
context, which a test should not have to assume. Cycles on the CPU at one
sample always works headless, and for a 64-pixel smoke test that is the right
trade.

Blender 5.2's engine enum is BLENDER_EEVEE. It is NOT BLENDER_EEVEE_NEXT,
which is the 4.x spelling and will raise on assignment here.
"""
import math

import bpy
from mathutils import Vector

ENGINES = ("BLENDER_EEVEE", "CYCLES")


def setup(engine, size, samples):
    scene = bpy.context.scene
    if engine not in ENGINES:
        raise ValueError("unknown engine %r - expected one of %s" % (engine, ENGINES))
    scene.render.engine = engine
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = True
    if engine == 'CYCLES':
        scene.cycles.samples = samples
    else:
        scene.eevee.taa_render_samples = samples

    world = bpy.data.worlds.new("turnaround")
    world.use_nodes = False
    world.color = (0.05, 0.05, 0.06)
    scene.world = world

    light_data = bpy.data.lights.new("key", type='SUN')
    light_data.energy = 4.0
    light = bpy.data.objects.new("key", light_data)
    light.rotation_euler = (math.radians(55), 0, math.radians(35))
    bpy.context.collection.objects.link(light)
    return scene


def frame_camera(obj, angle_deg, margin=1.25):
    """An orthographic camera looking level at `obj` from `angle_deg` around Z.

    Orthographic rather than perspective: four views meant to be compared
    should not each apply their own foreshortening, and a token-scale render
    gains nothing from a lens.
    """
    bpy.context.view_layer.update()
    size = max(obj.dimensions)
    centre = obj.matrix_world.translation + Vector((0, 0, obj.dimensions.z / 2))

    data = bpy.data.cameras.new("turnaround")
    data.type = 'ORTHO'
    data.ortho_scale = size * margin
    camera = bpy.data.objects.new("turnaround", data)
    bpy.context.collection.objects.link(camera)

    radians = math.radians(angle_deg)
    distance = size * 3
    camera.location = centre + Vector(
        (math.sin(radians) * distance, -math.cos(radians) * distance, 0))
    # Level with the middle of the figure, turned to face it: X 90 degrees
    # stands the camera up out of its default top-down rest orientation, Z
    # swings it around the subject.
    camera.rotation_euler = (math.radians(90), 0, radians)
    bpy.context.scene.camera = camera
    return camera


def turnaround(obj, outdir, stem, angles=(0, 90, 180, 270), size=768,
               engine='BLENDER_EEVEE', samples=16):
    """Render `obj` from each angle. Returns the filenames written."""
    setup(engine, size, samples)
    written = []
    for angle in angles:
        camera = frame_camera(obj, angle)
        name = "%s Turnaround_%03d.png" % (stem, angle)
        bpy.context.scene.render.filepath = str(outdir / name)
        bpy.ops.render.render(write_still=True)
        written.append(name)
        bpy.data.objects.remove(camera, do_unlink=True)
    return written
```

- [ ] **Step 4: Wire it into the assembly**

In `blender/assemble_npc.py`, add to the imports:

```python
import npc_mesh  # noqa: E402  (must follow the sys.path line)
import npc_render  # noqa: E402
```

Add to `parse_argv()`:

```python
    p.add_argument("--no-render", action="store_true",
                   help="skip the turnarounds, for iterating on the mesh work")
    p.add_argument("--turnaround-size", type=int, default=768,
                   help="turnaround render size in pixels (default: %(default)s)")
    p.add_argument("--engine", default="BLENDER_EEVEE", choices=npc_render.ENGINES,
                   help="render engine (default: %(default)s); CYCLES needs no "
                        "GL context and is what the tests use")
    p.add_argument("--samples", type=int, default=16,
                   help="render samples (default: %(default)s)")
```

And in `main()`, between the STL export and the report:

```python
    if not args.no_render:
        files += npc_render.turnaround(
            shell, args.outdir, args.stem, size=args.turnaround_size,
            engine=args.engine, samples=args.samples)
```

Now that the flag exists, the two Task 6 test classes should stop paying for renders they do not check. In `test/test_3d_assembly.py`:

- `TestAssembly.setUpClass` becomes `run_assembly(cls.outdir, "--no-render")`, and the comment about the flag arriving later comes out.
- `TestAssemblyFailsLoudly`'s subprocess argument list gains `"--no-render"` after `STEM`.

- [ ] **Step 5: Run the tests**

Run: `python -m unittest test.test_3d_assembly -v`
Expected: PASS, 15 tests. The Cycles renders are 64 pixels at one sample, so the class should finish in seconds.

- [ ] **Step 6: Look at a real turnaround**

Render the fixture at a size you can actually see:

```bash
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
  --background --factory-startup --python blender/assemble_npc.py -- \
  test/fixtures/3d/base.glb test/fixtures/3d/shell.glb /tmp/turn \
  --stem "Fixture" --turnaround-size 512
```
Expected: four 512px PNGs of a cylinder, transparent background, the figure upright and fully in frame in all four. If it is cropped or lying on its side, `frame_camera`'s rotation is wrong — fix it here, where the subject is a cylinder and the answer is obvious.

- [ ] **Step 7: Commit**

```bash
git add blender/npc_render.py blender/assemble_npc.py test/test_3d_assembly.py
git commit -m "feat: turnaround renders, the Foundry half of the 3D goal"
```

---

### Task 8: Wire Stage 2 in, and document the tool

**Files:**
- Modify: `generate-3d.py` (new `stage_assemble()`; `main()`'s loop)
- Create: `docs/generate-3d.md`
- Modify: `README.md`
- Test: `test/test_3d_cli.py` (append one class)

**Interfaces:**
- Consumes: `find_blender`, `ASSEMBLE_SCRIPT`, `append_dossier_3d`, `MESH_WORKFLOW`, `RIG_WORKFLOW`, `APOSE_STANCE` from Tasks 1 and 3; the `LANCER3D` report contract from Tasks 6 and 7.
- Produces:
  - `parse_report(stdout) -> dict` — raises `RuntimeError` when no report line is present
  - `stage_assemble(args, folder, stem, base, shell) -> dict` — the whole report, not just the filenames. Phase 3 adds keys to it (`bones`, `unweighted`, `rig_error`) and this is what lets it do that without changing a signature.

- [ ] **Step 1: Write the failing test**

Append to `test/test_3d_cli.py`, before the `if __name__` block:

```python
class TestReportParsing(unittest.TestCase):
    """Blender writes a lot to stdout; the report is one line inside it."""

    def test_it_finds_the_report_among_the_noise(self):
        stdout = ("Blender 5.2.1 LTS\n"
                  'LANCER3D {"files": ["a.glb"], "non_manifold": 0}\n'
                  "Blender quit\n")
        self.assertEqual(d3.parse_report(stdout)["files"], ["a.glb"])

    def test_the_last_report_wins(self):
        """Defensive: one run, one report - but never silently read a stale one."""
        stdout = ('LANCER3D {"files": ["old.glb"]}\n'
                  'LANCER3D {"files": ["new.glb"]}\n')
        self.assertEqual(d3.parse_report(stdout)["files"], ["new.glb"])

    def test_no_report_is_an_error(self):
        with self.assertRaises(RuntimeError):
            d3.parse_report("Blender quit\n")

    def test_a_malformed_report_is_an_error(self):
        with self.assertRaises(RuntimeError):
            d3.parse_report("LANCER3D not json\n")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m unittest test.test_3d_cli.TestReportParsing -v`
Expected: FAIL — `AttributeError: module 'gen3d' has no attribute 'parse_report'`.

- [ ] **Step 3: Implement Stage 2's driver**

Add `subprocess` to `generate-3d.py`'s imports, and append after `stage_mesh()`:

```python
# --------------------------------------------------------------------------
# Stage 2: Blender assembly
# --------------------------------------------------------------------------

REPORT_PREFIX = "LANCER3D "


def parse_report(stdout):
    """The assembly's machine-readable line, out of everything Blender printed.

    An absent or unparseable report is an error rather than an empty dict: it
    means the script died somewhere after the argument check, and continuing
    would write a dossier claiming files that are not there.
    """
    lines = [l for l in stdout.splitlines() if l.startswith(REPORT_PREFIX)]
    if not lines:
        raise RuntimeError("the Blender assembly printed no report line")
    try:
        return json.loads(lines[-1][len(REPORT_PREFIX):])
    except ValueError as exc:
        raise RuntimeError("the Blender assembly's report was not JSON: %s" % exc)


def stage_assemble(args, folder, stem, base, shell):
    """Run headless Blender over the two GLBs. Returns the assembly's report.

    The whole report rather than just report["files"], because the caller has
    to be able to say more about a run than which files came out of it - and
    because Phase 3 adds keys to it.

    Blender's own stderr is only surfaced when it fails: a successful run
    prints several screens of startup noise that would bury a 160-NPC batch's
    actual progress.
    """
    blender = find_blender(args.blender)
    if not ASSEMBLE_SCRIPT.exists():
        raise SystemExit("assembly script not found: %s" % ASSEMBLE_SCRIPT)

    command = [
        str(blender), "--background", "--factory-startup",
        "--python", str(ASSEMBLE_SCRIPT), "--",
        str(base), str(shell), str(folder), "--stem", stem,
    ]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout)
    if proc.returncode != 0:
        raise RuntimeError("Blender assembly failed (%d):\n%s"
                           % (proc.returncode, proc.stderr[-2000:]))
    report = parse_report(proc.stdout)
    print("      %d component(s) dropped, %d non-manifold edge(s)"
          % (report.get("components_dropped", 0), report.get("non_manifold", 0)))
    return report
```

- [ ] **Step 4: Wire Stage 2 into `main()`'s loop**

In `main()`, after the `mesh` block and before `done += 1`:

```python
            if "assemble" in args.stage:
                print("    assembling ...", flush=True)
                stem = npc_gen._safe(entry["name"])
                report = stage_assemble(args, folder, stem, base, shell)
                built = report["files"]
                for name in built:
                    print("      -> %s" % name)

                dossier = Path(folder_path) / ("%s.md" % stem)
                if dossier.exists():
                    append_dossier_3d(dossier, built,
                                      [MESH_WORKFLOW, RIG_WORKFLOW], APOSE_STANCE)
                else:
                    # Not an error: an NPC folder moved by hand into Foundry
                    # keeps its art and loses nothing by having no dossier.
                    print("    ! no dossier at %s - skipping the 3D section"
                          % dossier.name, file=sys.stderr)
```

- [ ] **Step 5: Run the tests, then the tool end to end**

Run: `python -m unittest discover -s test -t .`
Expected: PASS.

Then, on the NPC used in Tasks 4 and 5:

```bash
python generate-3d.py --id <that-id> --overwrite
```
Expected in that NPC's `3d/`: `apose.png`, `_base.glb`, `_shell.glb`, `<Name> Shell.glb`, `<Name> Print.stl` and four `<Name> Turnaround_*.png`. The dossier gains a `## 3D` section listing them.

Open the STL in a slicer or in Blender and confirm it is one closed body at 32 mm. Open the turnarounds and confirm the same person is recognisable from all four angles — the head will be poor (spec §7.2), the silhouette should not be.

- [ ] **Step 6: Write the tool's documentation**

Create `docs/generate-3d.md`, matching the shape of `docs/generate-npc.md`:

````markdown
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
````

- [ ] **Step 7: Add it to the README and commit**

In `README.md`, beside the existing tool sections, add:

````markdown
### `generate-3d.py`

Turns an NPC already in `.generated-npcs.json` into a printable 32 mm STL, a
cleaned 3D shell and four turnaround renders, by re-rendering its token in a
forced A-pose and reconstructing from that. Needs a running ComfyUI and
Blender 5.2. See [docs/generate-3d.md](docs/generate-3d.md).

```
python generate-3d.py --filter Sokolova
```
````

Run: `python -m unittest discover -s test -t .`
Expected: PASS.

```bash
git add generate-3d.py docs/generate-3d.md README.md test/test_3d_cli.py
git commit -m "feat: wire the Blender assembly into generate-3d.py, and document the tool"
```

**Phase 2 is complete here.** The printing and VTT goals are delivered in full, and nothing so far depends on the unproven weight transfer.

---

# Phase 3 — The rigging bridge

Spec §7.1 is the one structural risk the feasibility probe did not settle: no weight transfer has been run on this data. A-pose alignment removes the reason to expect failure, but a bulky jacket whose silhouette departs from the body underneath may still smear at the shoulders and the skirt hem.

Sequenced last and separately for exactly that reason. Everything Phase 2 delivers is already on disk and unaffected by anything here.

**One deviation from the spec, flagged:** §7.1 names a Surface Deform bind as the first fallback. Surface Deform is a Blender modifier with no glTF equivalent, so a shell bound that way cannot be exported as a rigged GLB at all — only baked, per frame, which is a different deliverable. The fallback implemented here instead is Blender's automatic bone-heat weighting (`ARMATURE_AUTO`) straight from the armature, which produces a genuinely rigged, exportable GLB and is immune to the specific failure mode direct transfer has, because it never has to decide which base vertex a jacket sleeve corresponds to. Both are built in Task 9, selected by `--bind`, and Task 10 measures which one this data actually wants.

---

### Task 9: Weight transfer, the bind, and the assertions

**Files:**
- Create: `blender/npc_rig.py`
- Modify: `blender/assemble_npc.py` (`parse_argv()`, imports, `main()`)
- Test: `test/test_3d_assembly.py` (append two classes)

**Interfaces:**
- Consumes: `npc_mesh.export_glb(objects, path)` from Task 6, and the `armature`, `body` and `shell` objects `assemble_npc.main()` already holds. `npc_rig` keeps its own `_activate` rather than importing `npc_mesh`'s — the two modules stay independent, and it is three lines.
- Produces:
  - `npc_rig.BINDS = ("transfer", "auto")`
  - `npc_rig.deform_bones(armature) -> list[str]`
  - `npc_rig.transfer_weights(source, target) -> None`
  - `npc_rig.auto_weights(target, armature) -> None`
  - `npc_rig.bind(target, armature) -> None`
  - `npc_rig.unweighted_vertices(obj, bone_names) -> int`
  - `assemble_npc.py` gains `--rig` and `--bind`; the report gains `bones`, `unweighted` and, on failure, `rig_error`, and `rigged` becomes true when a `Rigged.glb` was actually written.

- [ ] **Step 1: Write the failing test**

Append to `test/test_3d_assembly.py`, before the `if __name__` block:

```python
def glb_json_chunk(path):
    """The JSON chunk of a binary glTF, parsed.

    Read by hand rather than by importing it back into Blender: what matters
    is what is IN the file a Foundry or a game engine would load, and a
    re-import would let Blender paper over something the file does not
    actually carry.
    """
    data = path.read_bytes()
    magic, _, _ = struct.unpack("<4sII", data[:12])
    assert magic == b"glTF", "not a binary glTF: %s" % path.name
    length, kind = struct.unpack("<II", data[12:20])
    assert kind == 0x4E4F534A, "first chunk is not JSON"
    return json.loads(data[20:20 + length].decode("utf-8"))


@unittest.skipUnless(BLENDER, "Blender not installed")
class TestRigging(unittest.TestCase):
    """Spec §6 step 7, against the fixture pair.

    The fixture shell is a wider cylinder around a narrower one, which is the
    shape of the real problem in miniature: a garment whose silhouette departs
    from the body it wraps.
    """

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.outdir = Path(cls._tmp.name)
        cls.report, cls.proc = run_assembly(cls.outdir, "--rig", "--no-render")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_it_exits_cleanly(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr[-3000:])

    def test_it_reports_success(self):
        self.assertTrue(self.report["rigged"], self.report.get("rig_error"))

    def test_the_armature_has_deform_bones(self):
        """The fixture rig has three; the real one has 127."""
        self.assertGreater(self.report["bones"], 0)

    def test_every_shell_vertex_carries_a_weight(self):
        """The assertion spec §6 step 7 demands, reported as a number."""
        self.assertEqual(self.report["unweighted"], 0)

    def test_the_rigged_glb_is_written(self):
        path = self.outdir / ("%s Rigged.glb" % STEM)
        self.assertTrue(path.exists())
        self.assertGreater(path.stat().st_size, 0)

    def test_the_rigged_glb_actually_carries_a_skin(self):
        """A GLB with an armature beside the mesh is not a rigged GLB."""
        chunk = glb_json_chunk(self.outdir / ("%s Rigged.glb" % STEM))
        self.assertTrue(chunk.get("skins"), "no skins in the exported glTF")
        skinned = [m for m in chunk.get("nodes", []) if "skin" in m]
        self.assertTrue(skinned, "no node references a skin")

    def test_the_unrigged_shell_is_still_unrigged(self):
        """Spec §6.1 lists Shell.glb as the unrigged one; it must stay that way."""
        chunk = glb_json_chunk(self.outdir / ("%s Shell.glb" % STEM))
        self.assertFalse(chunk.get("skins"))

    def test_the_print_stl_is_unaffected(self):
        """Spec §7.1: only Rigged.glb may depend on the transfer."""
        self.assertGreater(stl_triangles(self.outdir / ("%s Print.stl" % STEM)), 0)


@unittest.skipUnless(BLENDER, "Blender not installed")
class TestAutomaticWeightsFallback(unittest.TestCase):
    """The §7.1 fallback, built now so choosing it later costs nothing."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.outdir = Path(cls._tmp.name)
        cls.report, cls.proc = run_assembly(
            cls.outdir, "--rig", "--bind", "auto", "--no-render")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_it_also_produces_a_skinned_glb(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr[-3000:])
        self.assertTrue(self.report["rigged"], self.report.get("rig_error"))
        chunk = glb_json_chunk(self.outdir / ("%s Rigged.glb" % STEM))
        self.assertTrue(chunk.get("skins"))

    def test_it_leaves_no_vertex_unweighted(self):
        self.assertEqual(self.report["unweighted"], 0)
```

`json` and `struct` are already imported at the top of the module from Task 6.

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m unittest test.test_3d_assembly.TestRigging -v`
Expected: FAIL — `assemble_npc.py: error: unrecognized arguments: --rig`.

- [ ] **Step 3: Write the rigging module**

Create `blender/npc_rig.py`:

```python
"""Binding the clothed shell to the base's armature.

This is spec §7.1 - the one part of the design the feasibility probe did not
settle. A-pose alignment removes the reason to expect failure, but nothing has
proven the transfer works on a bulky jacket whose silhouette departs from the
body underneath.

Two ways to bind, because that risk is real:

'transfer' is the design's choice - copy the base's own 127 vertex groups onto
the shell by proximity. It inherits SAM3DBody's actual skinning, which was
built for a human body and is better than anything derived from scratch.

'auto' is Blender's bone-heat weighting straight from the armature, ignoring
the base mesh's weights entirely. It cannot smear in the way transfer can,
because it never has to decide which base vertex a sleeve corresponds to - it
solves for the bones directly. Worse skinning where transfer works; a real
answer where transfer does not.

Note this is NOT the Surface Deform fallback the spec names. Surface Deform
has no glTF equivalent, so a shell bound that way cannot be exported as a
rigged GLB at all - only baked per frame, which is a different deliverable.
Automatic weights produce a genuinely rigged, exportable file, which is what
the goal actually asks for.
"""
import bpy

BINDS = ("transfer", "auto")


def deform_bones(armature):
    """The names of the bones that can actually deform a mesh."""
    return [bone.name for bone in armature.data.bones if bone.use_deform]


def _activate(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def transfer_weights(source, target):
    """Copy `source`'s vertex groups onto `target` by proximity.

    POLYINTERP_NEAREST - the nearest face, interpolated across it - rather
    than NEAREST vertex. The base is about 18k verts and the shell up to 200k,
    so a vertex-to-vertex mapping would quantise the shell's weights onto
    whichever body vertex happened to be closest and band the result at every
    joint. Interpolating across the nearest face is what lets a sleeve pick up
    a blend of the upper arm's weights rather than exactly one of them.

    datalayout_transfer() runs first and is not optional: the modifier writes
    into vertex groups that must already exist on the destination, and creates
    none of them itself. Without it the modifier applies cleanly and transfers
    nothing, which is the quiet failure this whole stage is built to avoid.
    """
    modifier = target.modifiers.new("weights", 'DATA_TRANSFER')
    modifier.object = source
    modifier.use_object_transform = True
    modifier.use_vert_data = True
    modifier.data_types_verts = {'VGROUP_WEIGHTS'}
    modifier.vert_mapping = 'POLYINTERP_NEAREST'
    modifier.layers_vgroup_select_src = 'ALL'
    modifier.layers_vgroup_select_dst = 'NAME'
    _activate(target)
    bpy.ops.object.datalayout_transfer(modifier=modifier.name)
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def bind(target, armature):
    """Parent `target` to `armature`, deforming through its vertex groups."""
    target.parent = armature
    target.matrix_parent_inverse = armature.matrix_world.inverted()
    modifier = target.modifiers.new("armature", 'ARMATURE')
    modifier.object = armature
    modifier.use_vertex_groups = True


def auto_weights(target, armature):
    """Bone-heat weighting straight from the armature, and parent in one step.

    parent_set does both the weighting and the Armature modifier, so this does
    not call bind() afterwards.
    """
    bpy.ops.object.select_all(action='DESELECT')
    target.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')


def unweighted_vertices(obj, bone_names):
    """Vertices carrying no non-zero weight in any deform group.

    Group membership with a zero weight is not weighting - a vertex like that
    still does not move with the skeleton - so the weight is checked, not just
    the membership.
    """
    wanted = {i for i, group in enumerate(obj.vertex_groups)
              if group.name in bone_names}
    if not wanted:
        return len(obj.data.vertices)
    return sum(
        1 for vert in obj.data.vertices
        if not any(g.group in wanted and g.weight > 0 for g in vert.groups))
```

- [ ] **Step 4: Wire rigging into the assembly**

In `blender/assemble_npc.py`, add the import beside the other two:

```python
import npc_mesh  # noqa: E402  (must follow the sys.path line)
import npc_render  # noqa: E402
import npc_rig  # noqa: E402
```

Add to `parse_argv()`:

```python
    p.add_argument("--rig", action="store_true",
                   help="also bind the shell to the base's armature and export "
                        "a rigged GLB (spec §7.1 - the unproven half)")
    p.add_argument("--bind", default="transfer", choices=npc_rig.BINDS,
                   help="how to weight the shell: 'transfer' copies the base's "
                        "own vertex groups by proximity, 'auto' solves for the "
                        "bones directly (default: %(default)s)")
```

In `main()`, after the STL export and BEFORE the turnaround block — the render should see the shell in whatever state it ends in, and the STL must be on disk before anything that can fail:

```python
    rigged = False
    rig_error = None
    bones = 0
    unweighted = None
    if args.rig:
        bone_names = npc_rig.deform_bones(armature)
        bones = len(bone_names)
        if not bones:
            rig_error = "the base armature has no deform bones"
        else:
            if args.bind == "transfer":
                npc_rig.transfer_weights(body, shell)
                npc_rig.bind(shell, armature)
            else:
                npc_rig.auto_weights(shell, armature)
            unweighted = npc_rig.unweighted_vertices(shell, set(bone_names))
            if unweighted:
                # Spec §6 step 7. Emitting a mesh where part of the figure
                # does not follow the skeleton is worse than emitting none:
                # the failure only shows up once someone animates it.
                rig_error = (
                    "%d of %d shell vertices carry no weight - the bind did not "
                    "reach the whole mesh. Try --bind auto."
                    % (unweighted, len(shell.data.vertices)))
            else:
                rigged_glb = args.outdir / ("%s Rigged.glb" % args.stem)
                npc_mesh.export_glb([armature, shell], rigged_glb)
                files.append(rigged_glb.name)
                rigged = True

        if rig_error:
            # Not a SystemExit: spec §7.1's containment is that only
            # Rigged.glb depends on this. The shell, the STL and the
            # turnarounds are already correct and already on disk, and
            # throwing them away because the rigging failed would be the
            # opposite of containment. Loud, and recorded, and no file.
            print("! rigging failed: %s" % rig_error, file=sys.stderr)
```

Extend the report dict at the end of `main()`:

```python
    print("LANCER3D " + json.dumps({
        "files": files,
        "shell_height_m": round(npc_mesh.height_of(shell), 4),
        "components_dropped": dropped,
        "non_manifold": non_manifold,
        "rigged": rigged,
        "bones": bones,
        "unweighted": unweighted,
        "rig_error": rig_error,
    }))
```

- [ ] **Step 5: Run the tests**

Run: `python -m unittest test.test_3d_assembly -v`
Expected: PASS, 25 tests.

If `test_every_shell_vertex_carries_a_weight` fails on the fixture, the transfer is not reaching the mesh at all — check that `datalayout_transfer` ran before `modifier_apply`, which is the one ordering that silently transfers nothing.

- [ ] **Step 6: Confirm both binds on the fixture, side by side**

```bash
for mode in transfer auto; do
  "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
    --background --factory-startup --python blender/assemble_npc.py -- \
    test/fixtures/3d/base.glb test/fixtures/3d/shell.glb "/tmp/rig-$mode" \
    --stem "Fixture" --rig --bind "$mode" --no-render 2>/dev/null \
    | grep LANCER3D
done
```
Expected: two report lines, both `"rigged": true` and `"unweighted": 0`.

- [ ] **Step 7: Commit**

```bash
git add blender/npc_rig.py blender/assemble_npc.py test/test_3d_assembly.py
git commit -m "feat: bind the clothed shell to the base armature, with the assertions that gate it"
```

---

### Task 10: Turn rigging on, measure it on real NPCs, and record the verdict

**Files:**
- Modify: `generate-3d.py` (`parse_args()`, `stage_assemble()`, `main()`)
- Modify: `docs/generate-3d.md`
- Test: `test/test_3d_cli.py` (append one class)

**Interfaces:**
- Consumes: `stage_assemble(args, folder, stem, base, shell) -> dict` from Task 8, and the `rigged` / `bones` / `unweighted` / `rig_error` report keys from Task 9.
- Produces: `--no-rig` and `--bind` on `generate-3d.py`, both passed through to the Blender script; a `warned` count in the run summary.

- [ ] **Step 1: Write the failing test**

Append to `test/test_3d_cli.py`, before the `if __name__` block:

```python
class TestRigFlags(unittest.TestCase):
    def test_rigging_is_on_by_default(self):
        """It is the headline deliverable; opting out is the exceptional case."""
        self.assertFalse(d3.parse_args([]).no_rig)

    def test_no_rig_turns_it_off(self):
        self.assertTrue(d3.parse_args(["--no-rig"]).no_rig)

    def test_the_bind_mode_defaults_to_transfer(self):
        self.assertEqual(d3.parse_args([]).bind, "transfer")

    def test_an_unknown_bind_mode_is_refused(self):
        with self.assertRaises(SystemExit):
            d3.parse_args(["--bind", "magic"])

    def test_the_flags_reach_the_blender_command(self):
        args = d3.parse_args(["--bind", "auto"])
        command = d3.assemble_command("/blender.exe", args, Path("/out"), "Jules",
                                      Path("/b.glb"), Path("/s.glb"))
        self.assertIn("--rig", command)
        self.assertIn("--bind", command)
        self.assertIn("auto", command)

    def test_no_rig_omits_the_flag(self):
        args = d3.parse_args(["--no-rig"])
        command = d3.assemble_command("/blender.exe", args, Path("/out"), "Jules",
                                      Path("/b.glb"), Path("/s.glb"))
        self.assertNotIn("--rig", command)

    def test_the_stem_reaches_the_command_unsplit(self):
        """A name with a space must arrive as one argv element, not two."""
        args = d3.parse_args([])
        command = d3.assemble_command("/blender.exe", args, Path("/out"),
                                      "Jules Sokolova", Path("/b.glb"), Path("/s.glb"))
        self.assertIn("Jules Sokolova", command)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m unittest test.test_3d_cli.TestRigFlags -v`
Expected: FAIL — `AttributeError: 'Namespace' object has no attribute 'no_rig'`.

- [ ] **Step 3: Add the flags and split the command out**

In `generate-3d.py`'s `parse_args()`, in the `stage` group:

```python
    stage.add_argument("--no-rig", action="store_true",
                       help="skip the weight transfer and the rigged GLB; the "
                            "shell, the STL and the turnarounds are unaffected")
    stage.add_argument("--bind", default="transfer", choices=("transfer", "auto"),
                       help="how to weight the shell: 'transfer' copies the "
                            "base's own vertex groups by proximity, 'auto' "
                            "solves for the bones directly (default: %(default)s)")
```

Replace the command construction inside `stage_assemble()` with a function of its own, so the flag plumbing is checkable without launching Blender:

```python
def assemble_command(blender, args, folder, stem, base, shell):
    """The full argv for one headless assembly run.

    Split out from stage_assemble() because getting a flag to the far side of
    Blender's '--' separator is exactly the kind of thing that fails silently -
    an unrecognised flag after '--' is argparse's problem inside the script,
    600 seconds later.
    """
    command = [
        str(blender), "--background", "--factory-startup",
        "--python", str(ASSEMBLE_SCRIPT), "--",
        str(base), str(shell), str(folder), "--stem", stem,
    ]
    if not args.no_rig:
        command += ["--rig", "--bind", args.bind]
    return command
```

And in `stage_assemble()`:

```python
    proc = subprocess.run(assemble_command(blender, args, folder, stem, base, shell),
                          capture_output=True, text=True, timeout=args.timeout)
```

- [ ] **Step 4: Surface the rigging outcome in the run**

In `stage_assemble()`, after the `components dropped` line:

```python
    if report.get("rig_error"):
        print("    ! rigging failed: %s" % report["rig_error"], file=sys.stderr)
    elif report.get("rigged"):
        print("      rigged: %d bones, every vertex weighted" % report["bones"])
```

In `main()`, count it. Beside `done = failed = skipped = 0` add `warned = 0`, and in the assemble block:

```python
                if report.get("rig_error"):
                    warned += 1
```

and extend the summary line:

```python
    print("\ndone: %d built (%d without a rig), %d skipped, %d failed, %.1f min"
          % (done, warned, skipped, failed, (time.time() - started) / 60))
```

- [ ] **Step 5: Run the tests, then measure the risk on real data**

Run: `python -m unittest discover -s test -t .`
Expected: PASS.

This is the step spec §7.1 exists for. Build five real NPCs with varied silhouettes — pick a heavy coat, a flight suit, a robe and two ordinary ones:

```bash
python generate-3d.py --limit 5 --overwrite
```

Then for each, open `<Name> Rigged.glb` in Blender, select the shell, enter Pose Mode on the armature, and rotate a shoulder bone 45 degrees. Look at the sleeve.

Record the outcome:

- **Every NPC weighted, sleeves follow the arm.** `--bind transfer` stays the default. Go to Step 6.
- **Some NPCs report `rig_error`, or the sleeves smear.** Re-run those with `--bind auto` and compare. If `auto` is better, change the `--bind` default to `auto` in both `generate-3d.py` and `blender/assemble_npc.py`, and say why in `docs/generate-3d.md`.
- **Neither works.** Then §7.1's deeper fallback is live: retargeting an armature to the shell rather than transferring onto it. That is a design change, not a plan step — write it up as a new spec, and in the meantime ship with `--no-rig` as the documented default. Phase 2's deliverables are unaffected either way, which is the whole reason this phase is last.

- [ ] **Step 6: Document the rigging, and what was measured**

Add to `docs/generate-3d.md`, after the Outputs table (extending the table first):

```markdown
| `<Name> Rigged.glb` | Clothed shell, weighted to the base's 127-bone armature |
```

and a new section before "Known limits":

```markdown
## Rigging

The shell is bound to the armature the SAM3DBody base brings with it. Two
methods, chosen with `--bind`:

- `transfer` (default) copies the base's own 127 vertex groups onto the shell
  by proximity, interpolated across the nearest face. It inherits skinning
  built for a human body, which is better than anything derived from scratch.
- `auto` solves for the bones directly with Blender's bone-heat weighting,
  ignoring the base's weights. Worse where `transfer` works; a real answer
  where it does not, because it never has to decide which base vertex a jacket
  sleeve corresponds to.

Before writing the file the stage asserts that the armature has deform bones
and that every shell vertex carries a non-zero weight in at least one of them.
A mesh that fails is not written: a figure whose coat does not follow its
shoulder only reveals itself once someone animates it, which is far too late.

A rigging failure does not fail the NPC. The shell, the STL and the
turnarounds are already on disk and are unaffected by it - only the rigged GLB
depends on the transfer. `--no-rig` skips the whole thing.

The pose the rig is in is the A-pose bind position, not the pose SAM3DBody
predicted. The prediction is unusable on this house style - the figure comes
out crouched with the fingers splayed - and was never the valuable part: a
rigged character wants a neutral bind pose, which is what the rest position
already is.
```

Add to "Known limits":

```markdown
- **The rigging was measured on five NPCs, not on all 160.** A garment whose
  silhouette departs sharply from the body underneath is the case to watch; if
  a sleeve smears at the shoulder, try `--bind auto` for that NPC.
```

Replace that last sentence with whatever Step 5 actually measured if it differed.

- [ ] **Step 7: Run the whole suite and commit**

Run: `python -m unittest discover -s test -t .`
Expected: PASS.

```bash
git add generate-3d.py docs/generate-3d.md test/test_3d_cli.py
git commit -m "feat: turn rigging on by default, and record what it does to real NPCs"
```

**Phase 3 is complete here**, and with it the plan: one NPC id in, and a rigged GLB, a printable STL, a cleaned shell and four turnarounds out.

---

## What this plan does not build

Named so the next person does not go looking for them:

- **Texture on the rigged character** (spec §7.3). Baking wanted the dependencies §2.2 rules out. Blender can project the A-pose render onto the mesh, but that is a further stage and is not designed.
- **Good faces** (spec §7.2). `Hunyuan3Dv2ConditioningMultiView` is installed and is the real fix, but generating consistent left/back/right views is its own design problem.
- **Multi-person scenes, video or mocap.** SAM3DBody supports all three; nothing here uses them, and `track_index` is pinned to a single figure.
- **Any change to the 2D pipeline.** This is additive throughout.
