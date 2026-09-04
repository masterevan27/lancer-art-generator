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
                 str(SCRIPT), "--", str(garbage), str(SHELL), tmp, "--stem", STEM],
                capture_output=True, text=True, timeout=600)
        self.assertEqual(proc.returncode, 1)
        self.assertFalse(
            any(l.startswith("LANCER3D ") for l in proc.stdout.splitlines()))


if __name__ == "__main__":
    unittest.main()
