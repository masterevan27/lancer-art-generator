"""Hair colour rolls independently of cut and lands inside the cut phrase."""
import random
import unittest

from test.helpers import FIXTURE_TABLES, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)


def roll(seed, **overrides):
    return gen.roll_npc(TABLES, random.Random(seed), overrides or None)


class TestSplitHairColour(unittest.TestCase):
    def test_flat_colour_has_no_tail_and_no_flags(self):
        self.assertEqual(gen.split_hair_colour("black"), ("black", "", ()))

    def test_tail_is_the_second_segment(self):
        self.assertEqual(
            gen.split_hair_colour("silver-white || fading to green at the tips"),
            ("silver-white", "fading to green at the tips", ()))

    def test_flags_are_the_third_segment(self):
        self.assertEqual(
            gen.split_hair_colour("greying || || older"),
            ("greying", "", ("older",)))

    def test_tail_and_flags_together(self):
        self.assertEqual(
            gen.split_hair_colour("sandy || going white at the temples || older"),
            ("sandy", "going white at the temples", ("older",)))


class TestHairColourRoll(unittest.TestCase):
    def test_no_rolled_hair_keeps_an_unresolved_slot(self):
        """The guard on Task 7's 68-bullet hand-edit."""
        for seed in range(200):
            self.assertNotIn("{", roll(seed)["Hair"])

    def test_the_tail_is_appended_after_the_cut(self):
        npc = roll(0, **{"Hair": "a short {colour} crop",
                         "Hair colour": "silver-white || fading to green at the tips"})
        self.assertEqual(
            npc["Hair"], "a short silver-white crop, fading to green at the tips")

    def test_a_flat_colour_appends_nothing(self):
        npc = roll(0, **{"Hair": "a short {colour} crop", "Hair colour": "black"})
        self.assertEqual(npc["Hair"], "a short black crop")

    def test_older_never_lands_on_a_young_age(self):
        """Mirrors the figure/young pairing exactly."""
        older = {gen.split_hair_colour(b)[0] for b in TABLES["Hair colour"]
                 if "older" in gen.split_hair_colour(b)[2]}
        self.assertTrue(older, "fixture must carry an 'older' colour")
        for seed in range(300):
            npc = roll(seed)
            if npc["_young"]:
                self.assertNotIn(
                    npc["Hair colour"], older,
                    "seed %d: an 'older' colour landed on a young NPC" % seed)

    def test_hair_colour_is_themed(self):
        self.assertIn("Hair colour", gen.THEMED_TABLES)


if __name__ == "__main__":
    unittest.main()
