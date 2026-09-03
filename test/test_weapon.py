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

    def test_an_armed_npc_is_possible(self):
        """The other direction of the same guarantee: the pool isn't starved.

        Nothing else pins this outside the mil path -
        test_a_mil_role_is_never_unarmed only covers a mil Role. A regression
        that collapsed the non-mil Weapon pool down to the empty entry would
        otherwise leave the whole suite green.
        """
        self.assertTrue(
            any(roll(s)["Weapon"] != "" for s in range(100)),
            "no roll in 100 came up armed - the weapon pool has been starved")

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

    def test_a_mil_role_in_a_notac_outfit_is_still_armed(self):
        """The guarantee outranks 'notac', which is only a preference.

        Every 'sidearm' bullet is also flagged 'mil', so a 'notac' Outfit's
        mil-strip run *before* apply_weapon_policy() empties the armed pool
        and the policy's own 'or options' fallback then hands back the whole
        table, weighted empty entry and all - measured at 210 unarmed rolls
        in 300 against the live tables. roll_npc() runs the policy first for
        exactly this reason; this pins the order.

        Both traits are forced rather than rolled because the fixture's only
        'notac' Outfit is also flagged 'civ', which filter_by_mil() drops for
        a mil Role - so no pure roll reaches this pairing. An override still
        reaches the mechanism: roll_npc() resolves a forced Outfit before the
        Weapon roll precisely so its flags gate the pools that follow.
        """
        mil = "a Union marine soldier || mil"
        notac = next(b for b in TABLES["Outfit"]
                     if "notac" in gen.split_flags(b)[1])
        for seed in range(300):
            npc = roll(seed, Role=mil, Outfit=notac)
            self.assertNotEqual(
                npc["Weapon"], "",
                "seed %d: a mil Role in a notac outfit rolled unarmed" % seed)

    def test_the_weapon_keeps_no_flag_segment(self):
        for seed in range(100):
            self.assertNotIn("||", roll(seed)["Weapon"])

    def test_weapon_is_themed_and_gear_is_not(self):
        self.assertIn("Weapon", gen.THEMED_TABLES)
        self.assertNotIn("Gear", gen.THEMED_TABLES)


class TestCivilianWeaponPolicy(unittest.TestCase):
    """Seven Roles reached apply_weapon_policy with no policy at all.

    WEAPON_POLICY only named Officials and Criminals, so a dockworker, a
    maintenance technician or a data courier rolled the raw pool - measured at
    65% armed against the live tables, because Weapon deliberately sits
    outside the civ/mil filter and a civilian can reach every military bullet
    in it.
    """

    def unarmed_share(self, options):
        unarmed = [x for x in options if "weapon" not in gen.split_flags(x)[1]]
        return len(unarmed) / len(options)

    def test_an_uncategorised_civilian_role_gets_the_civilian_tier(self):
        """The default, not another hardcoded bucket - so a Role added to the
        table later is covered without also needing a ROLE_CATEGORIES entry."""
        biased = gen.apply_weapon_policy(TABLES["Weapon"], None, False)
        self.assertGreater(self.unarmed_share(biased), 0.6)

    def test_a_named_civilian_category_gets_it_too(self):
        biased = gen.apply_weapon_policy(TABLES["Weapon"], "Laborers", False)
        self.assertGreater(self.unarmed_share(biased), 0.6)

    def test_the_civilian_tier_leaves_armed_rolls_reachable(self):
        """Two-thirds unarmed, not always unarmed."""
        biased = gen.apply_weapon_policy(TABLES["Weapon"], "Laborers", False)
        self.assertLess(self.unarmed_share(biased), 0.95)

    def test_criminals_keep_their_armed_bias(self):
        biased = gen.apply_weapon_policy(TABLES["Weapon"], "Criminals", False)
        self.assertLess(self.unarmed_share(biased),
                        self.unarmed_share(TABLES["Weapon"]))

    def test_officials_keep_their_restriction(self):
        biased = gen.apply_weapon_policy(TABLES["Weapon"], "Officials", False)
        self.assertGreater(self.unarmed_share(biased), 0.6)

    def test_a_mil_role_is_unaffected_by_the_civilian_default(self):
        """The mil branch returns before policy is consulted."""
        armed = gen.apply_weapon_policy(TABLES["Weapon"], None, True)
        self.assertEqual(self.unarmed_share(armed), 0.0)


if __name__ == "__main__":
    unittest.main()
