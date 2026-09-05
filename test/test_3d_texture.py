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


if __name__ == "__main__":
    unittest.main()
