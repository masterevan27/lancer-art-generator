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
