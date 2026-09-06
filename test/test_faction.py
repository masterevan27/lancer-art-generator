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
        # Derived rather than hardcoded: the fixture rolls its own Pronouns, so
        # pinning "their" here would hold the test hostage to any reweight or
        # change in RNG consumption upstream of the Pronouns roll.
        possessive = npc["_pronouns"]["possessive"]
        for prompt in (portrait, token):
            self.assertNotIn(", ,", prompt)
            self.assertNotIn(",  ", prompt)
            self.assertIn(
                "wearing %s, %s clothing following the shape of %s frame."
                % (npc["Outfit"], possessive, possessive), prompt)


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


class TestUnaffiliatedRoles(unittest.TestCase):
    """A Role whose own words say it works for nobody may not roll an employer.

    "Laborers / a freelance salvager / House Clawthorne" is the pairing that
    prompted this: the Role bullet says freelance and the dossier prints the
    Faction under "Affiliation", so the same sheet says both that this person
    works for nobody and that they work for a noble house.

    It is not something the civ/mil split could have caught, which is the
    argument for a filter of its own rather than a flag on the existing pair.
    House Clawthorne is 'mil' and does get dropped for a civilian Role - and
    then Smith-Shimano Corpro, which is 'civ', lands on the freelancer just as
    wrongly.
    """

    LIVE = None

    @classmethod
    def setUpClass(cls):
        cls.LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")

    def test_the_set_names_live_role_bullets(self):
        """A Role reworded since would leave the set naming nobody, and a
        filter keyed on a string nothing rolls is a silent no-op."""
        roles = {gen.split_flags(b)[0] for b in self.LIVE["Role"]}
        self.assertTrue(gen.UNAFFILIATED_ROLES)
        for role in gen.UNAFFILIATED_ROLES:
            self.assertIn(role, roles,
                          "UNAFFILIATED_ROLES names %r, which the Role table "
                          "does not offer" % role)

    def test_the_pool_it_narrows_to_cannot_empty(self):
        """The one guard a hard filter needs, the same one test_role_lock.py
        and test_backdrop_role.py keep over theirs: this does not fall back to
        the whole pool, so an empty result would be an empty roll."""
        flagged = [b for b in self.LIVE["Faction"]
                   if "unaffiliated" in gen.split_faction(b)[2]]
        self.assertGreaterEqual(
            len(set(flagged)), 2,
            "'## Faction' must keep its non-affiliations flagged "
            "'unaffiliated' - they are all an unaffiliated Role can roll")

    def test_every_unaffiliated_bullet_has_an_empty_visual(self):
        """The flag and the empty visual are two records of one fact.

        A bullet flagged 'unaffiliated' that carried a livery would put an
        employer's insignia on the clothing sentence of an NPC the dossier
        calls unaligned.
        """
        for bullet in self.LIVE["Faction"]:
            if "unaffiliated" not in gen.split_faction(bullet)[2]:
                continue
            self.assertEqual(
                gen.split_faction(bullet)[1], "",
                "a non-affiliation has no livery to show: %r" % bullet)

    def test_a_freelancer_never_rolls_an_employer(self):
        checked = 0
        for seed in range(1500):
            npc = gen.roll_npc(self.LIVE, random.Random(seed))
            if npc["Role"] not in gen.UNAFFILIATED_ROLES:
                continue
            checked += 1
            self.assertIn(
                "unaffiliated", gen.split_faction(npc["_raw"]["Faction"])[2],
                "seed %d: %r came out affiliated to %r"
                % (seed, npc["Role"], npc["Faction"]))
        self.assertTrue(checked, "no unaffiliated Role was rolled")

    def test_everyone_else_still_reaches_the_whole_table(self):
        """A filter that narrowed every Role would be a much larger change
        than the one intended, and would pass the test above."""
        seen = set()
        for seed in range(1500):
            npc = gen.roll_npc(self.LIVE, random.Random(seed))
            if npc["Role"] in gen.UNAFFILIATED_ROLES:
                continue
            seen.add(gen.split_faction(npc["_raw"]["Faction"])[0])
        names = {gen.split_faction(b)[0] for b in self.LIVE["Faction"]}
        self.assertEqual(seen, names,
                         "these affiliations became unreachable: %s"
                         % sorted(names - seen))


if __name__ == "__main__":
    unittest.main()
