"""Role gates dress register on Outfit and Faction.

A rolled dockworker came out in a gold-embroidered robe with a Karrakin
brocade-and-heraldry clause on top of it. The civ/mil split does not catch
that: it distinguishes "not a uniform" from "a uniform" and says nothing about
workaday versus ceremonial.

The two tables consume the flag differently and the tests are split to match.
On Outfit a 'dressy' bullet is dropped for a 'plain' Role. On Faction it is
not - the affiliation stays reachable and only its visual segment is
suppressed, because a dockworker employed by the Baronies is good flavour
while a dockworker dressed as a baron is the bug.

See docs/superpowers/specs/2026-09-04-role-dress-register-design.md.
"""
import random
import unittest

from test.helpers import FIXTURE_TABLES, REPO, bullets_for, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")


def roll(seed, **overrides):
    return gen.roll_npc(TABLES, random.Random(seed), overrides or None)


def dressy_outfits(tables):
    return {gen.split_flags(b)[0] for b in bullets_for(tables, "Outfit")
            if "dressy" in gen.split_flags(b)[1]}


class TestThePolicyTable(unittest.TestCase):
    def test_every_policy_key_is_a_real_role_category(self):
        """A typo'd category would silently gate nobody."""
        categories = set(gen.ROLE_CATEGORIES.values()) | {gen.UNCATEGORIZED_ROLE}
        for key in gen.DRESS_POLICY:
            self.assertIn(key, categories, "%r is not a ROLE_CATEGORIES value" % key)

    def test_laborers_and_technicians_are_the_plain_ones(self):
        self.assertEqual(gen.dress_policy_for("Laborers"), "plain")
        self.assertEqual(gen.dress_policy_for("Technicians"), "plain")

    def test_an_entitled_category_is_not_plain(self):
        """Officials is the case the gate must not break - fine dress is
        correct for a corporate liaison or a colonial administrator."""
        for category in ("Officials", "Criminals", "Civilians", "Pilots"):
            self.assertEqual(gen.dress_policy_for(category), "any")

    def test_an_unknown_category_is_unconstrained(self):
        self.assertEqual(gen.dress_policy_for(gen.UNCATEGORIZED_ROLE), "any")
        self.assertEqual(gen.dress_policy_for(None), "any")


class TestOutfitIsGated(unittest.TestCase):
    def test_a_plain_role_never_rolls_a_dressy_outfit(self):
        dressy = dressy_outfits(TABLES)
        self.assertTrue(dressy, "fixture needs a dressy outfit to avoid")
        checked = 0
        for seed in range(400):
            npc = roll(seed)
            if gen.dress_policy_for(gen.ROLE_CATEGORIES.get(npc["Role"])) != "plain":
                continue
            checked += 1
            self.assertNotIn(
                npc["Outfit"], dressy,
                "seed %d: %r rolled a ceremonial outfit" % (seed, npc["Role"]))
        self.assertTrue(checked, "no plain Role was rolled; the test checked nothing")

    def test_an_entitled_role_still_reaches_dressy_outfits(self):
        """The other half of the gate, and the one a blanket ban would break.

        Without this, filtering everything for everyone would pass the test
        above while making the ceremonial outfits dead content.
        """
        dressy = dressy_outfits(TABLES)
        reached = 0
        for seed in range(400):
            npc = roll(seed)
            if gen.dress_policy_for(gen.ROLE_CATEGORIES.get(npc["Role"])) == "plain":
                continue
            if npc["Outfit"] in dressy:
                reached += 1
        self.assertTrue(reached, "no non-plain Role ever reached a dressy outfit")

    def test_the_pool_is_never_filtered_to_nothing(self):
        """The starvation guard. Cannot trigger on today's content, but the
        theme filter narrows the same pool first once Phase 4 lands."""
        options = ["a robe || civ dressy", "a kimono || civ dressy"]
        self.assertEqual(gen.filter_by_dress(options, "plain"), options)

    def test_filtering_drops_only_the_dressy_ones(self):
        options = ["grey coveralls", "a robe || civ dressy", "a work jacket || civ"]
        self.assertEqual(
            gen.filter_by_dress(options, "plain"),
            ["grey coveralls", "a work jacket || civ"])

    def test_a_non_plain_policy_filters_nothing(self):
        options = ["grey coveralls", "a robe || civ dressy"]
        self.assertEqual(gen.filter_by_dress(options, "any"), options)


class TestFactionKeepsItsNameAndLosesItsVisual(unittest.TestCase):
    def _prompts_for(self, role, faction):
        npc = roll(0, **{"Role": role, "Faction": faction})
        return npc, gen.build_prompts(npc)

    def test_a_plain_role_gets_the_name_but_not_the_brocade(self):
        npc, (portrait, token) = self._prompts_for(
            "a dockworker", "Baronies || heavy brocade and gold braid || dressy")
        self.assertNotIn("heavy brocade", portrait)
        self.assertNotIn("heavy brocade", token)
        # The affiliation itself survives for the dossier.
        self.assertEqual(gen.split_faction(npc["Faction"])[0], "Baronies")

    def test_a_non_plain_role_is_unchanged(self):
        _, (portrait, _) = self._prompts_for(
            "a colonial administrator", "Baronies || heavy brocade and gold braid || dressy")
        self.assertIn("heavy brocade", portrait)

    def test_suppressing_the_visual_leaves_no_doubled_comma(self):
        """build_prompts() drops the whole clause rather than leaving the
        comma that separated it - the same path the two non-affiliations,
        which carry no visual at all, already take."""
        _, (portrait, token) = self._prompts_for(
            "a dockworker", "Baronies || heavy brocade and gold braid || dressy")
        for prompt in (portrait, token):
            self.assertNotIn(", ,", prompt)
            self.assertNotIn(",,", prompt)

    def test_an_undressy_faction_visual_survives_a_plain_role(self):
        """Only 'dressy' factions are suppressed. IPS-Northstar's salt-stained
        canvas reads correctly on a dockworker and must not be lost."""
        _, (portrait, _) = self._prompts_for(
            "a dockworker", "Unaligned || unaligned and freelance")
        self.assertIn("unaligned and freelance", portrait)


class TestForcingAContradiction(unittest.TestCase):
    DRESSY = "an elaborate floral kimono || civ notac dressy"

    def test_forcing_a_dressy_outfit_keeps_the_role_roll_off_plain(self):
        """The Age/Build precedent: an explicit choice should not collide with
        a randomly rolled dockworker and abort the run."""
        for seed in range(120):
            npc = roll(seed, **{"Outfit": self.DRESSY})
            self.assertNotEqual(
                gen.dress_policy_for(gen.ROLE_CATEGORIES.get(npc["Role"])), "plain",
                "seed %d: a forced ceremonial outfit landed on %r" % (seed, npc["Role"]))

    def test_forcing_a_plain_role_still_rolls_a_plain_outfit(self):
        dressy = dressy_outfits(TABLES)
        for seed in range(120):
            npc = roll(seed, **{"Role": "a dockworker"})
            self.assertNotIn(npc["Outfit"], dressy)

    def test_forcing_both_into_a_contradiction_is_an_error(self):
        with self.assertRaises(SystemExit) as caught:
            roll(0, **{"Role": "a dockworker", "Outfit": self.DRESSY})
        message = str(caught.exception)
        self.assertIn("Role", message)
        self.assertIn("Outfit", message)

    def test_forcing_a_compatible_pair_is_fine(self):
        npc = roll(0, **{"Role": "a colonial administrator", "Outfit": self.DRESSY})
        self.assertEqual(npc["Outfit"], "an elaborate floral kimono")


class TestTheLiveTables(unittest.TestCase):
    def test_the_live_file_actually_carries_the_flag(self):
        self.assertTrue(dressy_outfits(LIVE),
                        "no live Outfit bullet is flagged 'dressy'")

    def test_the_reported_robe_is_flagged(self):
        """The bullet that started this, named so a later edit cannot quietly
        un-flag the one case that was actually reported."""
        robe = [b for b in bullets_for(LIVE, "Outfit")
                if "gold embroidered trim" in b]
        self.assertEqual(len(robe), 1, "expected exactly one gold-trim robe")
        self.assertIn("dressy", gen.split_flags(robe[0])[1])

    def test_every_dressy_outfit_is_still_reachable_by_someone(self):
        """A flag that bars a bullet from everyone is a typo, not a gate.

        Every live 'dressy' Outfit is also 'civ', so it is already barred from
        every mil Role; if it were ALSO barred from every civilian one it would
        be dead content nothing could roll.
        """
        for bullet in bullets_for(LIVE, "Outfit"):
            flags = gen.split_flags(bullet)[1]
            if "dressy" not in flags:
                continue
            self.assertNotIn(
                "mil", flags,
                "a 'dressy' bullet flagged 'mil' is reachable by no one: a mil "
                "Role is never plain-gated but this bullet is dropped for "
                "civilians, and vice versa: %r" % bullet)

    def test_no_ragged_outfit_was_swept_up_by_the_flag(self):
        """'dressy' is not 'notac'. A dockworker in ragged cloth bindings or a
        travel-worn robe is entirely plausible - several read as poorer than
        the default coveralls - and flagging those would bar them for no
        reason. Named individually because the two flags coincide on more than
        half the bullets and a bulk edit is the likely mistake.
        """
        ragged = ["ragged wrapped cloth bindings", "pilgrim's robes",
                  "a tattered dark robe", "travel-worn robe", "haori-style jacket"]
        for bullet in bullets_for(LIVE, "Outfit"):
            for phrase in ragged:
                if phrase in bullet:
                    self.assertNotIn(
                        "dressy", gen.split_flags(bullet)[1],
                        "this reads as poor or worn, not fine: %r" % bullet)

    def test_the_two_named_factions_are_flagged(self):
        flagged = {gen.split_faction(b)[0] for b in bullets_for(LIVE, "Faction")
                   if "dressy" in gen.split_faction(b)[2]}
        self.assertIn("Karrakin Trade Baronies", flagged)
        self.assertIn("Smith-Shimano Corpro", flagged)

    def test_the_workwear_factions_are_not_flagged(self):
        """Issued and worn thin, riveted and salt-stained, mismatched surplus -
        all read correctly on a dockworker and must keep their visuals."""
        flagged = {gen.split_faction(b)[0] for b in bullets_for(LIVE, "Faction")
                   if "dressy" in gen.split_faction(b)[2]}
        for name in ("IPS-Northstar", "Colonial militia", "Unaligned", "Unregistered"):
            self.assertNotIn(name, flagged)

    def test_a_plain_role_keeps_a_workable_outfit_pool(self):
        """The starvation guard should not be what is holding this up."""
        for subject in ("she", "he"):
            options = gen.variant_table(LIVE, "Outfit", subject)
            civilian = gen.filter_by_mil(options, False, "Outfit")
            plain = gen.filter_by_dress(civilian, "plain")
            self.assertGreater(len(plain), 30,
                               "a plain %s Role has only %d outfits left"
                               % (subject, len(plain)))


if __name__ == "__main__":
    unittest.main()
