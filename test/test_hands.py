"""No NPC holds more things than they have hands.

Weapon and Gear roll independently and both can carry the 'hands' flag, so
without a filter an NPC can end up with a parasol in one hand and a katana
raised in both. Weapon is rolled first and Gear yields, because the weapon is
the more theme-defining object.
"""
import random
import unittest

from test.helpers import FIXTURE_TABLES, bullets_for, load_generator, rendered

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)


def roll(seed, **overrides):
    return gen.roll_npc(TABLES, random.Random(seed), overrides or None)


def texts_with_hands(name):
    """Flag-stripped texts of `name`'s bullets that occupy a hand."""
    return {gen.split_flags(b)[0] for b in bullets_for(TABLES, name)
            if "hands" in gen.split_flags(b)[1]}


class TestHands(unittest.TestCase):
    def test_weapon_and_gear_never_both_occupy_hands(self):
        armed = texts_with_hands("Weapon")
        held = texts_with_hands("Gear")
        for seed in range(300):
            npc = roll(seed)
            self.assertFalse(
                npc["Weapon"] in armed and npc["Gear"] in held,
                "seed %d: %r and %r both need hands"
                % (seed, npc["Weapon"], npc["Gear"]))

    def test_the_check_can_actually_fail(self):
        """Both pools must really carry hands bullets, or the test is vacuous."""
        self.assertTrue(texts_with_hands("Weapon"), "fixture Weapon has no hands bullet")
        self.assertTrue(texts_with_hands("Gear"), "fixture Gear has no hands bullet")

    def test_gear_yields_when_the_rolled_weapon_takes_the_hands(self):
        """When a roll's Weapon lands on a hands bullet, Gear must not.

        The brief's original version forced a two-handed Weapon via
        roll_npc(..., {"Weapon": bullet}) and asserted only npc["Gear"]. Both
        are wrong: overrides apply via npc.update() at the very end, long
        after the roll loop the weapon_hands filter lives in, so a forced
        Weapon never reaches the filter - and assertTrue(npc["Gear"]) passes
        trivially, since the fixture's Gear pool is never empty regardless of
        any filter. This rolls normally across a range of seeds instead, and
        only inspects the ones where the Weapon that actually got rolled
        occupies hands - the real mechanism the filter has to defend.
        """
        armed = texts_with_hands("Weapon")
        held = texts_with_hands("Gear")
        checked = 0
        for seed in range(300):
            npc = roll(seed)
            if npc["Weapon"] not in armed:
                continue
            checked += 1
            self.assertTrue(npc["Gear"], "seed %d: Gear pool starved by a "
                             "rolled two-handed weapon" % seed)
            self.assertNotIn(npc["Gear"], held,
                              "seed %d: Weapon took the hands but Gear is "
                              "still %r, a hands bullet" % (seed, npc["Gear"]))
        # Guard against vacuity: if no seed in the range ever rolled a hands
        # weapon, the two assertions above never ran and this test would be
        # green whether or not the filter exists at all.
        self.assertTrue(checked, "no seed in range(300) rolled a hands "
                         "Weapon - this test checked nothing")


class TestStanceReadsBothTables(unittest.TestCase):
    """Stance is filtered against Weapon and Gear together, not Gear alone.

    Every 'gun' bullet lives in Weapon after the split, so a filter reading
    only gear_flags would make gun stances unreachable rather than merely
    mis-filtered - a silent, total loss.
    """

    def _stance_texts(self, flag):
        """Rendered (pronoun-substituted) texts of Stance bullets carrying `flag`.

        npc["Stance"] comes back with any '{possessive}'-style placeholder
        already substituted (see roll_npc()'s final loop), so comparing it
        against the raw bullet text - which still reads
        '{possessive} weapon raised...' - never matches. rendered() expands
        the source side against every pronoun set the fixture can roll, the
        same trick test/helpers.py uses everywhere else a rolled value is
        checked against its source bullet.
        """
        texts = set()
        for b in bullets_for(TABLES, "Stance"):
            if flag in gen.split_flags(b)[1]:
                texts |= rendered(TABLES, "Stance", b)
        return texts

    def test_a_gun_stance_is_still_reachable(self):
        gun_stances = self._stance_texts("gun")
        self.assertTrue(gun_stances, "fixture Stance has no 'gun' pose to reach")
        self.assertTrue(
            any(roll(s)["Stance"] in gun_stances for s in range(300)),
            "no roll in 300 reached a gun stance - the Stance filter is "
            "probably still reading gear_flags alone, and every 'gun' bullet "
            "now lives in Weapon")

    def test_a_gun_stance_needs_a_gun(self):
        gun_stances = self._stance_texts("gun")
        for seed in range(300):
            npc = roll(seed)
            if npc["Stance"] in gun_stances:
                self.assertTrue(
                    npc["Weapon"],
                    "seed %d: a gun pose with no weapon" % seed)

    def test_a_hands_free_stance_is_not_paired_with_full_hands(self):
        # free_stances has to be rendered (pronoun-substituted), same as
        # _stance_texts above and for the same reason: the fixture's own
        # 'hands'-flagged bullet reads '{possessive} hands in {possessive}
        # pockets', and npc["Stance"] never comes back with the placeholder
        # still in it. Comparing against the raw bullet text here would make
        # the `if` below never fire and the test pass while checking nothing.
        free_stances = self._stance_texts("hands")
        armed = texts_with_hands("Weapon")
        held = texts_with_hands("Gear")
        checked = 0
        for seed in range(300):
            npc = roll(seed)
            if npc["Stance"] in free_stances:
                checked += 1
                self.assertNotIn(npc["Weapon"], armed, "seed %d" % seed)
                self.assertNotIn(npc["Gear"], held, "seed %d" % seed)
        self.assertTrue(checked, "no seed in range(300) rolled a hands-free "
                         "stance - this test checked nothing")


if __name__ == "__main__":
    unittest.main()
