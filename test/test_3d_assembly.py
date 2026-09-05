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
        cls.report, cls.proc = run_assembly(cls.outdir, "--no-render")

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
                 "--stem", STEM, "--no-render"],
                capture_output=True, text=True, timeout=600)
        self.assertNotEqual(proc.returncode, 0)

    def test_an_unanticipated_crash_is_a_non_zero_exit(self):
        """A failure this script never saw coming must still fail loudly.

        A malformed GLB is not one of the explicit SystemExit checks in
        assemble_npc.py - it makes npc_mesh.import_glb() raise a plain
        RuntimeError out of bpy.ops.import_scene.gltf() itself. On this
        Blender build an uncaught Python exception inside a --python script
        does NOT make Blender's own process exit non-zero, so this is the
        one path that would otherwise read as success (spec §6 step 7) to a
        caller that only checks the return code, as Task 8 does.
        """
        with tempfile.TemporaryDirectory() as tmp:
            garbage = Path(tmp) / "garbage.glb"
            garbage.write_bytes(b"not a real glb")
            proc = subprocess.run(
                [str(BLENDER), "--background", "--factory-startup", "--python",
                 str(SCRIPT), "--", str(garbage), str(SHELL), tmp, "--stem", STEM,
                 "--no-render"],
                capture_output=True, text=True, timeout=600)
        self.assertEqual(proc.returncode, 1)
        self.assertFalse(
            any(l.startswith("LANCER3D ") for l in proc.stdout.splitlines()))


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


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(BLENDER, "Blender not installed")
class TestRealHeight(unittest.TestCase):
    """--real-height-m overrides SAM3DBody's estimate, and the mini follows.

    The fixture base is 1.73 m. Asking for 1.90 must move the shell, because
    the shell is fitted to the base and the base is what gets rescaled - if
    only one of them moved, the two would no longer be in the correspondence
    a weight transfer depends on.
    """

    def test_the_shell_takes_the_given_height(self):
        with tempfile.TemporaryDirectory() as tmp:
            report, proc = run_assembly(Path(tmp), "--no-render",
                                        "--real-height-m", "1.90")
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
        self.assertAlmostEqual(report["shell_height_m"], 1.90, places=2)

    def test_the_estimate_is_still_reported(self):
        """Recorded, not discarded: it is the only way to see how far off the
        reconstruction's own guess was."""
        with tempfile.TemporaryDirectory() as tmp:
            report, _ = run_assembly(Path(tmp), "--no-render",
                                     "--real-height-m", "1.90")
        self.assertAlmostEqual(report["estimated_height_m"], 1.73, places=2)

    def test_a_shorter_npc_gets_a_shorter_mini(self):
        """Spec: --print-height-mm is the height of a --nominal-height-m
        figure, so a squad keeps its relative heights on the plate."""
        with tempfile.TemporaryDirectory() as tmp:
            report, _ = run_assembly(Path(tmp), "--no-render",
                                     "--real-height-m", "1.524",       # 5'0"
                                     "--nominal-height-m", "1.8288")   # 6'0"
        self.assertAlmostEqual(report["print_height_mm"], 32.0 * 1.524 / 1.8288, places=1)

    def test_without_the_flag_the_mini_is_exactly_the_asked_for_height(self):
        with tempfile.TemporaryDirectory() as tmp:
            report, _ = run_assembly(Path(tmp), "--no-render")
        self.assertAlmostEqual(report["print_height_mm"], 32.0, places=2)
        self.assertAlmostEqual(report["shell_height_m"], 1.73, places=2)
