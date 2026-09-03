"""The Weapon roll: every NPC gets one, and a mil Role is never unarmed."""
import random
import unittest

from test.helpers import FIXTURE_TABLES, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)


def roll(seed, **overrides):
    return gen.roll_npc(TABLES, random.Random(seed), overrides or None)


class TestWeaponRoll(unittest.TestCase):
    def test_every_npc_has_a_weapon_key(self):
        for seed in range(50):
            self.assertIn("Weapon", roll(seed))

    def test_an_unarmed_npc_is_possible(self):
        """The weighted empty entry has to be reachable."""
        self.assertTrue(
            any(roll(s)["Weapon"] == "" for s in range(100)),
            "no roll in 100 came up unarmed - the empty entry is unreachable")

    def test_a_mil_role_is_never_unarmed(self):
        """apply_weapon_policy restricts a mil pool to 'sidearm' bullets.

        The empty entry is not one, so the guarantee gets stronger after the
        split rather than weaker - this pins that.
        """
        mil = "a Union marine soldier || mil"
        for seed in range(100):
            npc = roll(seed, Role=mil)
            self.assertNotEqual(
                npc["Weapon"], "",
                "seed %d: a mil Role rolled unarmed" % seed)

    def test_the_weapon_keeps_no_flag_segment(self):
        for seed in range(100):
            self.assertNotIn("||", roll(seed)["Weapon"])

    def test_weapon_is_themed_and_gear_is_not(self):
        self.assertIn("Weapon", gen.THEMED_TABLES)
        self.assertNotIn("Gear", gen.THEMED_TABLES)


if __name__ == "__main__":
    unittest.main()
