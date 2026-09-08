"""The ## Animation table and animate-portrait.py's --roll over it.

The table is the one non-rolled table in npc-generator-tables.md: the NPC
generator ignores it (nothing in REQUIRED_TABLES names it), and its readers
are animate-portrait.py's --roll and the import GUI's animated-portrait
panel, which offer its bullets as the positive prompt for a Wan render.
"""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from test.helpers import load_animate

REPO = Path(__file__).resolve().parent.parent
LIVE_TABLES = REPO / "prompts" / "npc-generator-tables.md"

ap = load_animate()

FIXTURE = """# Tables

## Hair
- cropped short

## Animation
- x2 the wind stirs her hair. the camera does not move.
- smoke drifts past behind him. the camera does not move.
<!-- - a disabled bullet the GUI has switched off -->

## Prompt templates
- not a description, and never reached
"""


def write(text):
    path = Path(tempfile.mkdtemp()) / "tables.md"
    path.write_text(text, encoding="utf-8")
    return path


class TestLoadDescriptions(unittest.TestCase):
    def test_reads_only_the_animation_table(self):
        found = ap.load_descriptions(write(FIXTURE))
        self.assertNotIn("cropped short", found)
        self.assertNotIn("not a description, and never reached", found)
        self.assertIn("smoke drifts past behind him. the camera does not move.", found)

    def test_a_weight_repeats_the_bullet_the_way_the_generator_does(self):
        found = ap.load_descriptions(write(FIXTURE))
        self.assertEqual(
            found.count("the wind stirs her hair. the camera does not move."), 2)

    def test_a_commented_out_bullet_is_not_offered(self):
        found = ap.load_descriptions(write(FIXTURE))
        self.assertFalse(any("disabled" in d for d in found))

    def test_a_file_without_the_table_is_an_error_that_names_it(self):
        with self.assertRaises(SystemExit) as caught:
            ap.load_descriptions(write("## Hair\n- cropped\n"))
        self.assertIn("Animation", str(caught.exception))

    def test_the_shipped_tables_carry_the_table(self):
        found = ap.load_descriptions(LIVE_TABLES)
        self.assertGreaterEqual(len(set(found)), 11)

    def test_every_shipped_description_is_plain_prose(self):
        """No `||` flag segment and no @theme tag: nothing reads them here,
        and either would reach the text encoder verbatim."""
        for text in set(ap.load_descriptions(LIVE_TABLES)):
            with self.subTest(text=text[:40]):
                self.assertNotIn("||", text)
                self.assertNotIn("@", text)
                self.assertTrue(text.strip())

    def test_every_shipped_description_nails_the_camera_down(self):
        """The one clause docs/animate-portrait.md calls load-bearing: Wan
        invents a dolly-in given the chance."""
        for text in set(ap.load_descriptions(LIVE_TABLES)):
            with self.subTest(text=text[:40]):
                self.assertIn("camera", text.lower())


class TestRollDescription(unittest.TestCase):
    def test_a_seed_picks_the_same_description_twice(self):
        pool = ["a", "b", "c", "d", "e"]
        self.assertEqual(ap.roll_description(pool, 7), ap.roll_description(pool, 7))

    def test_the_pick_is_from_the_pool(self):
        pool = ["a", "b", "c"]
        self.assertIn(ap.roll_description(pool, 3), pool)

    def test_an_empty_pool_is_an_error(self):
        with self.assertRaises(SystemExit):
            ap.roll_description([], 1)


class TestRollFlag(unittest.TestCase):
    def test_roll_is_off_by_default(self):
        self.assertFalse(ap.parse_args(["p.png"]).roll)

    def test_roll_and_describe_together_are_refused(self):
        with self.assertRaises(SystemExit):
            ap.parse_args(["p.png", "--roll", "-d", "she waves"])

    def test_tables_defaults_to_the_shipped_file(self):
        self.assertEqual(Path(ap.parse_args(["p.png"]).tables), LIVE_TABLES)

    def test_a_dry_run_with_roll_uses_a_table_entry_as_the_prompt(self):
        tables = write(FIXTURE)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            ap.main(["p.png", "--dry-run", "--roll", "--seed", "7",
                     "--tables", str(tables)])
        printed = out.getvalue()
        graph = json.loads(printed[printed.index("{"):])
        i2v = graph[ap._node(graph, "WanImageToVideo")]["inputs"]
        positive = graph[i2v["positive"][0]]["inputs"]["text"]
        self.assertIn(positive, ap.load_descriptions(tables))
        self.assertIn(positive, printed)
