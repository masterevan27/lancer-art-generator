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
