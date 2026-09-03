"""Hair colour rolls independently of cut and lands inside the cut phrase."""
import random
import unittest

from test.helpers import FIXTURE_TABLES, REPO, bullets_for, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")


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
        """A roll completes, and its Hair comes back with no brace left in it.

        Weaker than it looks, and worth saying so. roll_npc()'s placeholder
        loop catches format()'s KeyError and re-raises SystemExit, so a
        surviving '{colour}' aborts the roll before the assertion below can
        see it - what this really pins is that 200 rolls from the fixture all
        resolve rather than exiting. The inverse property, that a live Hair
        bullet still *carries* a slot to resolve, fails silently and is
        guarded separately by TestTheLiveHairBulletsKeepTheirSlot.
        """
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


class TestTheLiveHairBulletsKeepTheirSlot(unittest.TestCase):
    """Every live '## Hair' bullet still carries a '{colour}' slot.

    The actual guard on the 68-bullet hand-edit that split colour out of the
    cut, and the one failure in this feature that raises nothing: a bullet
    that lost its slot rolls a head with no colour at all, ships a prompt that
    leaves the shade to the image model, and passes every other test in the
    suite. That is the state the split existed to end, so it gets a test of
    its own rather than being inferred from a fixture roll.

    Walks the per-pronoun variant keys as well as the base table - see
    helpers.table_keys(). Half the live Hair bullets sit in 'Hair (she) +' and
    'Hair (he) +', and checking LIVE["Hair"] alone would miss them.
    """

    def test_every_live_hair_bullet_carries_a_colour_slot(self):
        bullets = bullets_for(LIVE, "Hair")
        self.assertTrue(bullets, "live file has no Hair bullets to check")
        for bullet in bullets:
            self.assertIn(
                "{colour}", bullet,
                "this '## Hair' bullet has no '{colour}' slot, so it would "
                "roll colourless hair and nothing would raise: %r" % bullet)


if __name__ == "__main__":
    unittest.main()
