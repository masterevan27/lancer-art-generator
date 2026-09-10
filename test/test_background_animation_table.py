"""The ## Background Animation table and animate-portrait.py --background.

The scene-side twin of test_animation_table.py. The table lives in
scene-and-spaceship-tables.md rather than the NPC file because scene motion
is not an NPC trait, and its readers are `--background --roll` and, later,
the import GUI's background panel.

What these check that the portrait tests cannot: the bullets are
subject-free. A background has nobody in it, and a clause about a character
is an invitation for Wan to draw one into an empty frame.
"""
import contextlib
import io
import json
import re
import tempfile
import unittest
from pathlib import Path

from test.helpers import load_animate

REPO = Path(__file__).resolve().parent.parent
LIVE_TABLES = REPO / "prompts" / "scene-and-spaceship-tables.md"

ap = load_animate()

FIXTURE = """# Tables

## Backdrop
- a ruined megacity street, hollowed towers and haze

## Background Animation
- x2 dust drifts across the street. the camera is locked off and does not move.
- neon signage flickers in the haze. the camera is locked off and does not move.
<!-- - a disabled bullet the GUI has switched off -->

## Spaceships
- not a motion prompt, and never reached
"""

# Anything that puts a person in an empty frame. Word boundaries, so
# "shed", "theirs" in a longer word and "hero" in "atmosphere" do not trip.
SUBJECTS = re.compile(
    r"\b(character|person|people|figure|pilot|he|she|they|him|her|his|their|"
    r"face|hair|eyes|smile|blink)\b", re.I)


def write(text):
    path = Path(tempfile.mkdtemp()) / "tables.md"
    path.write_text(text, encoding="utf-8")
    return path


def shipped():
    return set(ap.load_descriptions(LIVE_TABLES, ap.BACKGROUND_TABLE))


class TestLoadDescriptions(unittest.TestCase):
    def test_reads_only_the_background_animation_table(self):
        found = ap.load_descriptions(write(FIXTURE), ap.BACKGROUND_TABLE)
        self.assertNotIn("a ruined megacity street, hollowed towers and haze", found)
        self.assertNotIn("not a motion prompt, and never reached", found)
        self.assertIn(
            "neon signage flickers in the haze. the camera is locked off and "
            "does not move.", found)

    def test_a_weight_repeats_the_bullet_the_way_the_generator_does(self):
        found = ap.load_descriptions(write(FIXTURE), ap.BACKGROUND_TABLE)
        self.assertEqual(found.count(
            "dust drifts across the street. the camera is locked off and "
            "does not move."), 2)

    def test_a_commented_out_bullet_is_not_offered(self):
        found = ap.load_descriptions(write(FIXTURE), ap.BACKGROUND_TABLE)
        self.assertFalse(any("disabled" in d for d in found))

    def test_a_file_without_the_table_is_an_error_that_names_it(self):
        with self.assertRaises(SystemExit) as caught:
            ap.load_descriptions(write("## Backdrop\n- a street\n"),
                                 ap.BACKGROUND_TABLE)
        self.assertIn("Background Animation", str(caught.exception))

    def test_the_portrait_table_is_still_the_default_heading(self):
        """The new argument must not have moved the portrait path."""
        self.assertEqual(ap.load_descriptions(write(FIXTURE), "Backdrop"),
                         ["a ruined megacity street, hollowed towers and haze"])


class TestShippedTable(unittest.TestCase):
    def test_the_scene_tables_carry_the_table(self):
        self.assertGreaterEqual(len(shipped()), 10)

    def test_the_npc_tables_do_not_carry_it(self):
        """One table, one home. Two copies would drift."""
        with self.assertRaises(SystemExit):
            ap.load_descriptions(ap.DEFAULT_TABLES, ap.BACKGROUND_TABLE)

    def test_every_bullet_nails_the_camera_down(self):
        for text in shipped():
            with self.subTest(text=text[:40]):
                self.assertIn("camera", text.lower())

    def test_no_bullet_puts_a_person_in_the_frame(self):
        for text in shipped():
            found = SUBJECTS.search(text)
            with self.subTest(text=text[:40]):
                self.assertIsNone(
                    found, "names a subject: %r" % (found and found.group(0)))

    def test_every_bullet_is_plain_prose(self):
        """No `||` flag segment and no @theme tag: nothing reads them here,
        and either would reach the text encoder verbatim."""
        for text in shipped():
            with self.subTest(text=text[:40]):
                self.assertNotIn("||", text)
                self.assertNotIn("@", text)
                self.assertTrue(text.strip())


class TestRollWithTheFlag(unittest.TestCase):
    def test_a_dry_run_rolls_the_background_table(self):
        tables = write(FIXTURE)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            ap.main(["bg.png", "--background", "--dry-run", "--roll",
                     "--seed", "7", "--tables", str(tables)])
        printed = out.getvalue()
        graph = json.loads(printed[printed.index("{"):])
        i2v = graph[ap._node(graph, "WanImageToVideo")]["inputs"]
        positive = graph[i2v["positive"][0]]["inputs"]["text"]
        self.assertIn(positive,
                      ap.load_descriptions(tables, ap.BACKGROUND_TABLE))

    def test_the_shipped_table_rolls_without_an_argument(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            ap.main(["bg.png", "--background", "--dry-run", "--roll",
                     "--seed", "11"])
        printed = out.getvalue()
        graph = json.loads(printed[printed.index("{"):])
        i2v = graph[ap._node(graph, "WanImageToVideo")]["inputs"]
        self.assertIn(graph[i2v["positive"][0]]["inputs"]["text"], shipped())


class TestDefaultScenePrompt(unittest.TestCase):
    """The still to animate when you do not have one yet.

    --background takes an image, and the answer to "which image?" for someone
    starting cold is a checked-in prompt they can render with generate-art.py.
    It lives in the scene prompt file so the existing parser finds it and
    --only can name it, rather than as a second copy inside this script.
    """

    SCENES = REPO / "prompts" / "scene-background-art-prompts.md"
    NAME = "Default Animated Background"

    def entry(self):
        found = [e for e in ap.art.parse_prompts(self.SCENES) if e.name == self.NAME]
        self.assertEqual(len(found), 1, "expected one %r section" % self.NAME)
        return found[0]

    def test_the_scene_file_carries_a_default_section(self):
        self.assertTrue(self.entry().prompt.strip())

    def test_it_is_written_in_the_campaign_house_style(self):
        """Same linework and palette as the portraits it will sit behind."""
        text = self.entry().prompt.lower()
        for marker in ("linework", "halftone", "teal", "olive"):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_it_is_a_wide_shot_rather_than_a_portrait(self):
        text = self.entry().prompt.lower()
        self.assertIn("wide", text)

    def test_it_gives_the_animation_something_to_move(self):
        """A still with no smoke, cloud or lights in it animates into a
        still. The default has to hand the Wan pass something to work on."""
        text = self.entry().prompt.lower()
        movable = [w for w in ("smoke", "cloud", "dust", "lights", "haze")
                   if w in text]
        self.assertGreaterEqual(len(movable), 3, "only found %s" % movable)


if __name__ == "__main__":
    unittest.main()
