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

from test.helpers import FIXTURE_TABLES, REPO, load_generator

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


class TestFactionPigment(unittest.TestCase):
    """Faction colour is pigment; the glow colour is light. They coexist.

    A green-and-gold Harrison uniform lit by a red instrument glow is
    coherent - but the closing line's claim that the glow is "the only
    saturated color in the frame" stops being true, so it softens to "the only
    other saturated color". Factions asserting pigment carry '|| palette'.
    """

    def test_a_pigment_faction_softens_the_exclusivity_claim(self):
        npc = gen.roll_npc(TABLES, random.Random(0), {
            "Faction": "Harrison Armory || in imperial green and gold || mil palette",
            "Glow colour": "amber",
            "Gear": "an old-fashioned lantern glowing warm, carried in one hand",
        })
        portrait, token = gen.build_prompts(npc)
        for prompt in (portrait, token):
            self.assertIn("only other saturated color", prompt)

    def test_a_plain_faction_keeps_the_exclusive_claim(self):
        npc = gen.roll_npc(TABLES, random.Random(0), {
            "Faction": "Unaligned || || civ",
            "Glow colour": "amber",
            "Gear": "an old-fashioned lantern glowing warm, carried in one hand",
        })
        portrait, token = gen.build_prompts(npc)
        for prompt in (portrait, token):
            self.assertIn("only saturated color", prompt)
            self.assertNotIn("only other saturated color", prompt)

    def test_a_pigment_faction_with_no_glow_drops_the_no_stray_colour_claim(self):
        """'no stray saturated color' contradicts a uniform that has one.

        equipped_glow's has_light_source() call reads Weapon, Gear, Outfit,
        Headgear, Feature and Eyes (generate-npc.py, LIGHT_SOURCE_WORDS), so
        all six are pinned here to glow-free fixture values - the fixture's
        Outfit table has a "neon techwear jacket" bullet that would otherwise
        flip has_light_source() true by seed and falsify the very claim this
        test checks. portrait_glow adds one more source on top of those six -
        has_light_source(scene), the rolled Backdrop - so Backdrop is pinned
        too, to a glow-free bullet with no 'nogear' flag, closing that window
        for both prompts rather than just the token half.
        """
        npc = gen.roll_npc(TABLES, random.Random(0), {
            "Faction": "Harrison Armory || in imperial green and gold || mil palette",
            "Gear": "a canvas tool roll at the hip",
            "Weapon": "a service pistol worn openly at the thigh",
            "Outfit": "grey coveralls",
            "Headgear": "{Subject} {is_are} bare-headed.",
            "Feature": "a scar across one cheek",
            "Eyes": "grey eyes",
            "Backdrop": "A half-body character portrait || Behind {object} is a plain wall.",
        })
        portrait, token = gen.build_prompts(npc)
        for prompt in (portrait, token):
            self.assertNotIn("no stray saturated color", prompt)
            self.assertIn("Keep the rest of the palette restrained", prompt)

    def test_every_pigment_faction_actually_names_a_colour(self):
        """A 'palette' flag on a bullet with no colour in it would soften the
        closing line for nothing."""
        live = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")
        checked = 0
        for bullet in live["Faction"]:
            _, visual, flags = gen.split_faction(bullet)
            if "palette" not in flags:
                continue
            checked += 1
            with self.subTest(bullet=bullet):
                self.assertIn(" in ", visual,
                              "a palette faction must name its colours: %s" % bullet)
        # A vacuous pass if 'palette' were ever dropped from every bullet -
        # the loop above would then assert nothing and the test would pass on
        # nothing checked, the same shape test_stance_armed.py and
        # test_stance_content.py guard their own pools against.
        self.assertGreaterEqual(checked, 5,
                                 "expected at least 5 palette-flagged Faction bullets")


if __name__ == "__main__":
    unittest.main()
