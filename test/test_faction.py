"""Faction carries a name for the dossier and a visual for the prompt.

The single-segment form put a garment CATEGORY - "corporate wear", "service
dress" - into the prompt directly after Outfit's specific garment description,
where the vaguer clause simply lost. Deleting the Faction line from a prompt
changed the render not at all. Splitting it lets the dossier keep the
affiliation name while the prompt gets a signature written to describe what
Outfit does not: fabric, tailoring, insignia, patina.

Three segments, the same shape Backdrop and Hair colour use - and for the same
reason: two of them are prose and only the third is flags.
"""
import random
import unittest

from test.helpers import FIXTURE_TABLES, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)


class TestSplitFaction(unittest.TestCase):
    def test_all_three_segments(self):
        name, visual, flags = gen.split_faction(
            "Harrison Armory || sharply pressed, high collar || mil palette")
        self.assertEqual(name, "Harrison Armory")
        self.assertEqual(visual, "sharply pressed, high collar")
        self.assertEqual(flags, ("mil", "palette"))

    def test_an_empty_visual_segment(self):
        name, visual, flags = gen.split_faction("Unaligned || || civ")
        self.assertEqual(name, "Unaligned")
        self.assertEqual(visual, "")
        self.assertEqual(flags, ("civ",))

    def test_a_bare_name_has_no_visual_and_no_flags(self):
        self.assertEqual(gen.split_faction("Unregistered"), ("Unregistered", "", ()))


class TestFactionFlags(unittest.TestCase):
    def test_flags_for_reads_the_third_segment(self):
        """Reading the second blindly would take the visual prose for flags."""
        flags = gen.flags_for("Faction", "Harrison Armory || sharply pressed || mil")
        self.assertEqual(flags, ("mil",))

    def test_the_civ_mil_filter_still_works_on_three_segments(self):
        options = [
            "Unaligned || || civ",
            "Harrison Armory || sharply pressed || mil",
        ]
        self.assertEqual(gen.filter_by_mil(options, True, "Faction"),
                         ["Harrison Armory || sharply pressed || mil"])
        self.assertEqual(gen.filter_by_mil(options, False, "Faction"),
                         ["Unaligned || || civ"])

    def test_visual_prose_containing_a_flag_word_is_not_read_as_a_flag(self):
        """The trap split_flags() would fall into: partition('||') returns
        every word after the first separator, so a visual mentioning 'civil'
        or 'military' would leak into the flag tuple."""
        flags = gen.flags_for(
            "Faction", "Colonial militia || mismatched military surplus || mil")
        self.assertEqual(flags, ("mil",))


class TestFactionInOutput(unittest.TestCase):
    def test_the_dossier_gets_the_name_and_the_prompt_gets_the_visual(self):
        npc = gen.roll_npc(TABLES, random.Random(0),
                           {"Faction": "Harrison Armory || sharply pressed || mil"})
        self.assertEqual(gen.split_faction(npc["Faction"])[0], "Harrison Armory")
        portrait, token = gen.build_prompts(npc)
        for prompt in (portrait, token):
            self.assertIn("sharply pressed", prompt)
            self.assertNotIn("Harrison Armory", prompt)

    def test_an_empty_visual_leaves_no_orphaned_comma(self):
        npc = gen.roll_npc(TABLES, random.Random(0),
                           {"Faction": "Unaligned || || civ"})
        portrait, token = gen.build_prompts(npc)
        for prompt in (portrait, token):
            self.assertNotIn(", ,", prompt)
            self.assertNotIn(",  ", prompt)
            self.assertIn("the clothing following the shape of that frame", prompt)


if __name__ == "__main__":
    unittest.main()
