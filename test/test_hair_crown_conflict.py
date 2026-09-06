"""Hair gathered up on the crown does not go under a wide-brimmed hat either.

A rolled Union inspector came back wearing "a wide woven hat, thin red-framed
glasses catching the light and a long-stemmed pipe held between her lips" over
"a messy dark topknot, one side shaved close beneath it", and the render did
what it did for the flight helmet before it: put the topknot through the hat.

The Hair bullet was flagged 'updo' the whole time. What it lacked was anything
to collide WITH. 'updo' drops Headgear flagged 'helmet', and a sedge hat is
emphatically not one - the tables file calls soft goods "deliberately
unflagged" so a kimono can still reach a straw hat, and calls 'helmet' "the
bullets where the head is actually inside a helmet". Both of those readings
are right and neither one covers this hat.

So the vocabulary gained a third register rather than stretching either of the
two it had. 'crown' marks headgear that SITS ON the top of the skull without
enclosing it - a wide brim, a tall hat, anything whose volume is where an updo
already is. It reads as:

  helmet   the head is inside it        -> drops updos, drops carried helmets
  crown    it sits on top of the head   -> drops updos ONLY
  (none)   it leaves the crown free     -> drops nothing

That middle row is the whole point of a separate flag. Reusing 'helmet' would
have fixed the topknot and broken something else: the Gear filter reads
'helmet' too, so a straw hat would have stopped an NPC carrying a flight
helmet under one arm, which is a pairing nobody complained about. 'crown' is
read by the updo filter and by nothing else.

It is likewise NOT 'hardtech'. A woven hat is exactly what an elaborate or
traditional outfit should reach, and 'notac' drops 'hardtech' Headgear; a hat
tagged that way would vanish from the kimonos it belongs on.
"""
import contextlib
import io
import random
import sys
import unittest

from test.helpers import (
    FIXTURE_TABLES, REPO, bullets_for, load_generator, rendered)

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")

UPDO = "a high, tight {colour} topknot || updo"
FLAT = "a short {colour} crop"
HAT = "{Subject} {wear} a wide woven sedge hat. || crown"
HELMET = "{Subject} {wear} a sealed flight helmet. || hardtech helmet"
VISOR = "{Subject} {wear} a slim visor band across the brow. || hardtech"
BARE = "{Subject} {is_are} bare-headed."
CARRIED_HELMET = "a flight helmet held under one arm || hands helmet"


def _crown_tables():
    """The shared fixture plus the bullets these tests need.

    Built in memory rather than written into fixtures/tables-minimal.md, for
    the reason test_helmet_conflict.py gives: that file is the baseline for
    fixtures/roll-snapshot.json, and adding a bullet to a table changes every
    seed's draw from it.

    The pool needs a brimmed hat to drop, an updo to drop it, a flat cut to
    measure the other half of the gate, a hardtech bullet that is NOT a hat so
    a filter keyed on 'hardtech' cannot pass this suite, and a carried helmet
    so the Gear filter's indifference to 'crown' is measurable.
    """
    tables = gen.parse_tables(FIXTURE_TABLES)
    tables["Hair"] = tables["Hair"] + [UPDO, FLAT]
    tables["Headgear"] = [
        HELMET if "sealed flight helmet" in b else b
        for b in tables["Headgear"]] + [HAT, VISOR]
    tables["Gear"] = tables["Gear"] + [CARRIED_HELMET]
    return tables


TABLES = _crown_tables()


def roll(seed, **overrides):
    return gen.roll_npc(TABLES, random.Random(seed), overrides or None)


@contextlib.contextmanager
def _quiet_stderr():
    captured, before = io.StringIO(), sys.stderr
    sys.stderr = captured
    try:
        yield captured
    finally:
        sys.stderr = before


def _rendered_where(tables, table, flag):
    """Every string a bullet carrying `flag` can appear as in a rolled NPC."""
    out = set()
    for bullet in bullets_for(tables, table):
        if flag in gen.flags_for(table, bullet):
            out |= rendered(tables, table, bullet)
    return out


def crowning_hats(tables):
    return _rendered_where(tables, "Headgear", "crown")


def updo_cuts(tables):
    return _rendered_where(tables, "Hair", "updo")


class TestTheRollIsGated(unittest.TestCase):
    def test_an_updo_never_rolls_a_brimmed_hat_over_it(self):
        hats = crowning_hats(TABLES)
        self.assertTrue(hats, "fixture needs a crowning hat to avoid")
        for seed in range(400):
            npc = roll(seed, Hair=UPDO)
            self.assertNotIn(
                npc["Headgear"], hats,
                "seed %d: a wide brim went on over hair gathered at the crown"
                % seed)

    def test_a_flat_cut_still_reaches_a_brimmed_hat(self):
        """The other half of the gate. Dropping the hats for everyone would
        pass the test above by making them dead content."""
        hats = crowning_hats(TABLES)
        reached = sum(
            roll(seed, Hair=FLAT)["Headgear"] in hats for seed in range(400))
        self.assertTrue(reached, "a flat cut never reached a brimmed hat")

    def test_an_updo_still_reaches_other_hard_tech(self):
        """'crown' widened what an updo avoids; it must not have widened it to
        the whole hardtech register. A brow visor leaves the crown free."""
        reached = sum(
            roll(seed, Hair=UPDO)["Headgear"] == "She wears a slim visor band "
            "across the brow." for seed in range(400))
        self.assertTrue(reached, "an updo lost the brow visor too")

    def test_a_gated_roll_still_has_somewhere_to_go(self):
        seen = {roll(seed, Hair=UPDO)["Headgear"] for seed in range(400)}
        self.assertGreater(len(seen), 1)

    def test_the_flag_never_reaches_a_prompt(self):
        for seed in range(200):
            npc = roll(seed, Headgear=HAT)
            self.assertNotIn("crown", npc["Headgear"])
            self.assertNotIn("||", npc["Headgear"])
            for prompt in gen.build_prompts(npc):
                self.assertNotIn("|| crown", prompt)


class TestCrownIsNotHelmet(unittest.TestCase):
    """The reason this is a new flag rather than 'helmet' on the hats.

    'helmet' is read by two filters: the updo one and the carried-helmet one.
    'crown' must be read by the first and ignored by the second, or a straw
    hat starts confiscating the flight helmet under someone's arm.
    """

    def test_a_brimmed_hat_still_reaches_a_carried_helmet(self):
        carried = _rendered_where(TABLES, "Gear", "helmet")
        self.assertTrue(carried, "fixture needs a carried helmet")
        reached = sum(
            roll(seed, Headgear=HAT)["Gear"] in carried for seed in range(400))
        self.assertTrue(
            reached,
            "a woven hat dropped the carried helmets - 'crown' leaked into "
            "the Gear filter, which is exactly what a separate flag avoids")

    def test_a_worn_helmet_still_drops_a_carried_helmet(self):
        """The Gear filter itself is untouched and still reads 'helmet'."""
        carried = _rendered_where(TABLES, "Gear", "helmet")
        for seed in range(200):
            npc = roll(seed, Headgear=HELMET)
            self.assertNotIn(npc["Gear"], carried, "seed %d" % seed)

    def test_a_worn_helmet_still_drops_an_updo(self):
        """The original pairing keeps working. 'crown' widened the filter; it
        did not replace what it already caught."""
        updos = updo_cuts(TABLES)
        for seed in range(200):
            npc = roll(seed, Headgear=HELMET)
            self.assertNotIn(npc["Hair"], updos, "seed %d" % seed)


class TestTheFilterRunsBothWays(unittest.TestCase):
    def test_a_pinned_hat_is_never_rolled_an_updo_under_it(self):
        updos = updo_cuts(TABLES)
        self.assertTrue(updos, "fixture needs an updo to avoid")
        for seed in range(400):
            npc = roll(seed, Headgear=HAT)
            self.assertNotIn(
                npc["Hair"], updos,
                "seed %d: a brimmed hat rolled a topknot under it" % seed)

    def test_rerolling_hair_from_raw_never_lands_on_an_updo(self):
        updos = updo_cuts(TABLES)
        for seed in range(200):
            npc = roll(seed, Hair=FLAT, Headgear=HAT)
            value = gen.reroll_trait(TABLES, npc, "Hair", random.Random(seed))
            self.assertNotIn(
                value, updos,
                "seed %d: re-rolled a topknot under a brimmed hat" % seed)

    def test_rerolling_headgear_from_raw_never_lands_on_a_hat(self):
        hats = crowning_hats(TABLES)
        for seed in range(200):
            npc = roll(seed, Hair=UPDO, Headgear=BARE)
            value = gen.reroll_trait(
                TABLES, npc, "Headgear", random.Random(seed))
            self.assertNotIn(
                value, hats,
                "seed %d: re-rolled a brimmed hat over a topknot" % seed)

    def test_an_ordinary_headgear_still_reaches_an_updo(self):
        updos = updo_cuts(TABLES)
        reached = sum(
            roll(seed, Headgear=BARE)["Hair"] in updos for seed in range(400))
        self.assertTrue(reached)

    def test_naming_both_by_hand_is_honoured_rather_than_refused(self):
        """The same asymmetry every other pairing here has. Both clauses are
        true of the figure and only the render is ugly, so --set-trait naming
        both is an aesthetic override made on purpose."""
        npc = roll(0, Hair=UPDO, Headgear=HAT)
        self.assertIn(npc["Hair"], updo_cuts(TABLES))
        self.assertIn(npc["Headgear"], crowning_hats(TABLES))


class TestTheRegisterIsRecorded(unittest.TestCase):
    def test_a_roll_records_whether_the_headgear_crowns(self):
        self.assertTrue(roll(0, Headgear=HAT)["_headgear_crown"])
        self.assertFalse(roll(0, Headgear=BARE)["_headgear_crown"])

    def test_a_helmet_is_not_recorded_as_a_crown(self):
        """The two registers are independent. A helmet encloses rather than
        crowns, and the manifest keeps them apart so a re-roll can tell which
        filter it is honouring."""
        npc = roll(0, Headgear=HELMET)
        self.assertTrue(npc["_headgear_helmet"])
        self.assertFalse(npc["_headgear_crown"])

    def test_both_traits_are_still_rerollable(self):
        for name in ("Hair", "Headgear"):
            with self.subTest(trait=name):
                self.assertIn(name, gen.REROLLABLE_TRAITS)
                self.assertNotIn(name, gen.UNREROLLABLE_REASONS)


class TestTheLegacyRerollRespectsIt(unittest.TestCase):
    """The lossy path: an entry with no raw bullets to pin."""

    def _entry_npc(self, key, register, **overrides):
        npc = roll(0, **overrides)
        npc.pop("_raw")
        npc[key] = register
        return npc

    def test_a_recorded_crown_never_rerolls_an_updo_under_it(self):
        updos = updo_cuts(TABLES)
        npc = self._entry_npc("_headgear_crown", True, Headgear=HAT)
        for seed in range(200):
            value = gen.reroll_trait(TABLES, npc, "Hair", random.Random(seed))
            self.assertNotIn(value, updos, "seed %d" % seed)

    def test_a_recorded_updo_never_rerolls_a_hat_over_it(self):
        hats = crowning_hats(TABLES)
        npc = self._entry_npc("_hair_updo", True, Hair=UPDO)
        for seed in range(200):
            value = gen.reroll_trait(
                TABLES, npc, "Headgear", random.Random(seed))
            self.assertNotIn(value, hats, "seed %d" % seed)

    def test_recorded_ordinary_headgear_still_reaches_an_updo(self):
        updos = updo_cuts(TABLES)
        npc = self._entry_npc("_headgear_crown", False, Headgear=BARE)
        reached = sum(
            gen.reroll_trait(TABLES, npc, "Hair", random.Random(seed)) in updos
            for seed in range(200))
        self.assertTrue(reached)

    def test_an_entry_predating_the_crown_key_rerolls_unrestricted(self):
        """None is 'not recorded', which is not the same as False. An entry
        generated before this flag existed must behave as it did then rather
        than silently claim the hat was flat."""
        updos = updo_cuts(TABLES)
        npc = self._entry_npc("_headgear_crown", None, Headgear=HAT)
        npc["_headgear_helmet"] = False
        with _quiet_stderr():
            reached = sum(
                gen.reroll_trait(TABLES, npc, "Hair", random.Random(seed))
                in updos for seed in range(200))
        self.assertTrue(reached)

    def test_an_entry_predating_the_crown_key_says_so(self):
        npc = self._entry_npc("_headgear_crown", None, Headgear=HAT)
        npc["_headgear_helmet"] = False
        with _quiet_stderr() as err:
            gen.reroll_trait(TABLES, npc, "Hair", random.Random(0))
        self.assertIn("no recorded headgear register", err.getvalue())

    def test_a_recorded_register_warns_about_nothing(self):
        npc = self._entry_npc("_headgear_crown", True, Headgear=HAT)
        with _quiet_stderr() as err:
            gen.reroll_trait(TABLES, npc, "Hair", random.Random(0))
        self.assertEqual(err.getvalue(), "")


class TestTheLiveTable(unittest.TestCase):
    def _flagged(self):
        return " ".join(b for b in bullets_for(LIVE, "Headgear")
                        if "crown" in gen.flags_for("Headgear", b))

    def test_the_reported_bullet_is_flagged(self):
        """The headgear that produced the report: the wide woven hat with the
        red-framed glasses and the long-stemmed pipe."""
        self.assertIn("thin red-framed glasses catching the light",
                      self._flagged())

    def test_every_wide_brim_is_flagged(self):
        """The rest of the set. Each of these puts a brim across the top of
        the skull, which is where an updo already is."""
        flagged = self._flagged()
        for wanted in ("wide woven sedge hat",
                       "pale cloth wrapped loosely over the lower face",
                       "small curved horns and hanging tassels",
                       "small hanging bells and a tattered red ribbon",
                       "bristling with jagged spikes at the crown",
                       "over a patterned cloth headband"):
            with self.subTest(phrase=wanted):
                self.assertIn(wanted, flagged,
                              "%r is not flagged 'crown'" % wanted)

    def test_nothing_close_fitting_is_flagged(self):
        """The narrow reading. A bandana, a headband or a hood follows the
        skull rather than sitting above it, and an updo under one is fine."""
        flagged = self._flagged()
        for unwanted in ("bare-headed", "headset", "earpiece", "visor band"):
            with self.subTest(phrase=unwanted):
                self.assertNotIn(unwanted, flagged,
                                 "%r lies close and should not be 'crown'"
                                 % unwanted)

    def test_no_crowning_hat_is_also_a_helmet(self):
        """The registers are exclusive by construction. A bullet carrying both
        would work, but it means one of the two readings is wrong."""
        for bullet in bullets_for(LIVE, "Headgear"):
            flags = gen.flags_for("Headgear", bullet)
            if "crown" not in flags:
                continue
            with self.subTest(bullet=bullet):
                self.assertNotIn("helmet", flags)

    def test_the_soft_hats_are_not_hardtech(self):
        """'crown' is a claim about VOLUME, and 'hardtech' one about REGISTER.
        They are orthogonal on purpose - a rig clamped over the crown is
        honestly both - so this asserts the narrow thing that is actually
        true rather than that the two never co-occur.

        A woven or lacquered hat is what a kimono should reach, and 'notac'
        drops 'hardtech' Headgear. Tagging one of these would delete it from
        exactly the elaborate and traditional outfits it belongs on.
        """
        for wanted in ("wide woven sedge hat", "wide straw hat",
                       "lacquered hat", "tricorn hat", "ceremonial hat",
                       "ushanka-style fur hat", "ball cap",
                       "peaked officer's cap"):
            matches = [b for b in bullets_for(LIVE, "Headgear") if wanted in b]
            with self.subTest(phrase=wanted):
                self.assertTrue(matches, "%r matched no bullet" % wanted)
                for bullet in matches:
                    flags = gen.flags_for("Headgear", bullet)
                    self.assertIn("crown", flags,
                                  "%r is not flagged 'crown'" % wanted)
                    self.assertNotIn("hardtech", flags,
                                     "%r is soft goods and must stay "
                                     "reachable under 'notac'" % wanted)

    def test_an_updo_keeps_a_varied_headgear_pool(self):
        """The starvation guard against live content: 'crown' takes bullets
        out of an updo's pool on top of what 'helmet' already took."""
        pool = [b for b in bullets_for(LIVE, "Headgear")
                if not {"helmet", "crown"} & set(gen.flags_for("Headgear", b))]
        self.assertGreaterEqual(len(pool), 40)

    def test_no_other_table_carries_crown(self):
        """'crown' gates Headgear only. Anywhere else it is inert and reads as
        though something were filtering on it."""
        for name in gen.REQUIRED_TABLES:
            if name == "Headgear":
                continue
            for bullet in bullets_for(LIVE, name):
                self.assertNotIn("crown", gen.flags_for(name, bullet),
                                 "%s carries an inert 'crown' flag" % name)


if __name__ == "__main__":
    unittest.main()
