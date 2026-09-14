"""Scientists are a Role category, drawn toward the lab without being locked in.

Eleven scientist Roles were added to the Role table with no ROLE_CATEGORIES
entry, and nothing failed: an unmapped Role files under 'Other' with a warning
and falls through every bucket-keyed rule - dress, weapons, occupation scenes.
The first class holds that gap shut for every Role, not just these.

The rest hold the two halves of ROLE_PREFERENCES and the 'lab' gate: a
scientist usually gets the lab coat and sometimes the laboratory, nobody else
gets the laboratory, and a bar owner may still roll the coat.
"""
import random
import unittest

from test.helpers import REPO, bullets_for, load_generator

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")
ROLES = [gen.split_flags(b)[0] for b in bullets_for(LIVE, "Role")]
SCIENTIST = "a systems biologist"
LAB_SCENE = "spacecraft laboratory"


class TestEveryRoleIsCategorized(unittest.TestCase):
    def test_no_live_role_falls_through_to_other(self):
        missing = [r for r in ROLES if r not in gen.ROLE_CATEGORIES]
        self.assertEqual(missing, [],
                         "these Roles have no ROLE_CATEGORIES entry and roll "
                         "under %r with no dress, weapon or scene rules"
                         % gen.UNCATEGORIZED_ROLE)

    def test_the_scientists_bucket_is_populated(self):
        scientists = [r for r in ROLES
                      if gen.ROLE_CATEGORIES.get(r) == "Scientists"]
        self.assertGreaterEqual(len(scientists), 10)
        self.assertIn("Scientists", gen.BACKDROP_ROLES["deskwork"])


class TestThePreference(unittest.TestCase):
    POOL = ["a lab coat || civ lab"] + ["plain clothes %d" % i
                                        for i in range(30)]

    def test_another_category_gets_the_pool_back_untouched(self):
        for category in ("Civilians", "Soldiers", None):
            self.assertIs(
                gen.apply_role_preference(self.POOL, category, "Outfit"),
                self.POOL)

    def test_a_table_with_no_share_is_untouched(self):
        self.assertIs(
            gen.apply_role_preference(self.POOL, "Scientists", "Headgear"),
            self.POOL)

    def test_a_scientist_reaches_the_share_and_loses_nothing(self):
        weighted = gen.apply_role_preference(self.POOL, "Scientists", "Outfit")
        self.assertEqual(set(weighted), set(self.POOL))
        share = weighted.count(self.POOL[0]) / len(weighted)
        self.assertGreaterEqual(
            share, gen.ROLE_PREFERENCES["Scientists"][1]["Outfit"])


class TestLiveRolls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scientists = [gen.roll_npc(LIVE, random.Random(s),
                                       {"Role": SCIENTIST})
                          for s in range(600)]
        cls.natural = [gen.roll_npc(LIVE, random.Random(s))
                       for s in range(1500)]

    def test_a_scientist_usually_wears_the_lab_coat(self):
        share = sum("lab coat" in n["Outfit"]
                    for n in self.scientists) / len(self.scientists)
        self.assertGreater(share, 0.3)

    def test_a_scientist_sometimes_stands_in_the_lab(self):
        share = sum(LAB_SCENE in n["Backdrop"]
                    for n in self.scientists) / len(self.scientists)
        self.assertGreater(share, 0.15)

    def test_nobody_else_reaches_the_lab(self):
        for npc in self.natural:
            if LAB_SCENE in npc["Backdrop"]:
                self.assertEqual(
                    gen.ROLE_CATEGORIES.get(npc["Role"]), "Scientists",
                    "%r rolled the laboratory" % npc["Role"])

    def test_the_lab_coat_is_still_open_to_other_civilians(self):
        """A preference, not a lock."""
        self.assertTrue(any(
            "lab coat" in n["Outfit"] for n in self.natural
            if gen.ROLE_CATEGORIES.get(n["Role"]) != "Scientists"))


if __name__ == "__main__":
    unittest.main()
