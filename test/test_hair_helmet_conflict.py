"""Hair gathered up on the crown does not go under a helmet.

A rolled dockworker came back in a streamlined flight helmet with "sandy blonde
hair swept up into a high bun, secured with ornamental pins and a trailing
ribbon" in the same sentence, and the render did the only thing it could with
both: it put the bun through the helmet. The clauses are not merely ugly
together the way two helmets are - they describe two objects occupying the same
volume, and every seed that pairs them produces the same artefact.

'updo' marks the narrow case: a cut whose mass sits ON TOP OF the skull - a
topknot, a high ponytail, space buns, a crowned bun, a hard ornament pinned at
the crown. A braid pinned close to the head, a low bun, a chin-length bob and
hair merely "pinned up off the collar" all leave the crown flat, and those are
exactly what someone puts a helmet on over. Flagging them would cost the
pairing for no gain.

It is gated against 'helmet' rather than 'hardtech', for the same reason the
carried-helmet filter is: hard tech is the whole modern head register, and a
headset, a brow visor or an ear implant leaves the crown free. A topknot above
a comms earpiece reads fine and stays reachable.

Headgear is the table that yields on a fresh roll, because Hair precedes it in
REQUIRED_TABLES. The filter runs both ways, so a pinned helmet drops the updos
from the Hair pool instead - neither trait gains a TRAIT_DEPENDENTS edge, and
both stay one-click re-rollable.
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
HELMET = "{Subject} {wear} a sealed flight helmet. || hardtech helmet"
VISOR = "{Subject} {wear} a slim visor band across the brow. || hardtech"
BARE = "{Subject} {is_are} bare-headed."


def _hair_tables():
    """The shared fixture plus the bullets these tests need.

    Built in memory rather than written into fixtures/tables-minimal.md, for
    the reason test_helmet_conflict.py spells out at length: that file is the
    baseline for fixtures/roll-snapshot.json, and adding a bullet to a table
    changes every seed's draw from it.

    The pool needs all four: an updo to trigger the filter, a worn helmet for
    it to drop, a flat cut so the other half of the gate is measurable, and a
    hardtech bullet that is NOT a helmet, so a filter keyed on 'hardtech'
    instead of 'helmet' cannot pass this suite.
    """
    tables = gen.parse_tables(FIXTURE_TABLES)
    tables["Hair"] = tables["Hair"] + [UPDO, FLAT]
    tables["Headgear"] = [
        HELMET if "sealed flight helmet" in b else b
        for b in tables["Headgear"]] + [VISOR]
    return tables


TABLES = _hair_tables()


def roll(seed, **overrides):
    return gen.roll_npc(TABLES, random.Random(seed), overrides or None)


@contextlib.contextmanager
def _quiet_stderr():
    """Capture the generator's warnings instead of printing them mid-suite."""
    captured, before = io.StringIO(), sys.stderr
    sys.stderr = captured
    try:
        yield captured
    finally:
        sys.stderr = before


def updo_cuts(tables):
    """Every string an 'updo' Hair bullet can appear as in a rolled NPC.

    A Hair bullet carries a '{colour}' slot that roll_npc() fills from the
    rolled colour, appending that colour's tail after the whole phrase, so
    comparing a rolled Hair against the raw bullet never matches. rendered()
    expands the source side across every colour and pronoun set, which makes
    the comparisons below plain set membership.
    """
    out = set()
    for bullet in bullets_for(tables, "Hair"):
        if "updo" in gen.split_flags(bullet)[1]:
            out |= rendered(tables, "Hair", bullet)
    return out


def worn_helmets(tables):
    """Every string a 'helmet' Headgear bullet can appear as in a rolled NPC."""
    out = set()
    for bullet in bullets_for(tables, "Headgear"):
        if "helmet" in gen.split_flags(bullet)[1]:
            out |= rendered(tables, "Headgear", bullet)
    return out


class TestTheRollIsGated(unittest.TestCase):
    def test_an_updo_never_rolls_a_helmet_over_it(self):
        worn = worn_helmets(TABLES)
        self.assertTrue(worn, "fixture needs a worn helmet to avoid")
        for seed in range(400):
            npc = roll(seed, Hair=UPDO)
            self.assertNotIn(
                npc["Headgear"], worn,
                "seed %d: a helmet went on over hair gathered at the crown"
                % seed)

    def test_a_flat_cut_still_reaches_a_helmet(self):
        """The other half of the gate. Filtering the helmets out for everyone
        would pass the test above by making them dead content."""
        worn = worn_helmets(TABLES)
        reached = sum(
            roll(seed, Hair=FLAT)["Headgear"] in worn for seed in range(400))
        self.assertTrue(reached, "a flat cut never reached a helmet")

    def test_an_updo_still_reaches_other_hard_tech(self):
        """Keyed on 'helmet', not 'hardtech'. A brow visor or a headset leaves
        the crown free, and a topknot above one reads fine."""
        reached = sum(
            roll(seed, Hair=UPDO)["Headgear"] == "She wears a slim visor band "
            "across the brow." for seed in range(400))
        self.assertTrue(reached, "an updo lost the brow visor too")

    def test_a_gated_roll_still_has_somewhere_to_go(self):
        """Variety, not just legality: an updo must reach more than one
        Headgear, or the gate has replaced a clash with a uniform."""
        seen = {roll(seed, Hair=UPDO)["Headgear"] for seed in range(400)}
        self.assertGreater(len(seen), 1)

    def test_the_flag_never_reaches_a_prompt(self):
        for seed in range(200):
            npc = roll(seed, Hair=UPDO)
            self.assertNotIn("updo", npc["Hair"])
            self.assertNotIn("||", npc["Hair"])
            for prompt in gen.build_prompts(npc):
                self.assertNotIn("updo", prompt)


class TestTheFilterRunsBothWays(unittest.TestCase):
    """Hair is rolled first, so normally the Headgear yields. When the Headgear
    is the pinned one, the Hair has to yield instead - the same shape the
    Age/Build, Role/Outfit and Headgear/Gear pairings already use, and for the
    same reason: a pinned choice must not collide with a random draw.
    """

    def test_neither_trait_gains_a_cascade_edge(self):
        """Both are traits the import GUI re-rolls on a single click with no
        confirmation dialog, which is why the filter has to run both ways at
        all - an edge either way would silently move a second trait."""
        for name in ("Hair", "Headgear"):
            with self.subTest(trait=name):
                self.assertNotIn(name, gen.TRAIT_DEPENDENTS)
                self.assertEqual(gen.trait_cascade(name), (name,))

    def test_a_pinned_helmet_is_never_rolled_an_updo_under_it(self):
        updos = updo_cuts(TABLES)
        self.assertTrue(updos, "fixture needs an updo to avoid")
        for seed in range(400):
            npc = roll(seed, Headgear=HELMET)
            self.assertNotIn(
                npc["Hair"], updos,
                "seed %d: a helmet rolled a topknot under it" % seed)

    def test_rerolling_hair_from_raw_never_lands_on_an_updo(self):
        """The path that direction exists for. reroll_from_raw() pins every
        other trait - the worn Headgear among them - and frees the Hair, so the
        roller's own filter is what runs, with no rebuilt copy to drift."""
        updos = updo_cuts(TABLES)
        worn = worn_helmets(TABLES)
        for seed in range(200):
            npc = roll(seed, Hair=FLAT, Headgear=HELMET)
            self.assertIn(npc["Headgear"], worn, "seed %d: setup failed" % seed)
            value = gen.reroll_trait(TABLES, npc, "Hair", random.Random(seed))
            self.assertNotIn(
                value, updos,
                "seed %d: re-rolled a topknot under a helmet" % seed)
            self.assertIn(
                npc["Headgear"], worn,
                "seed %d: a one-click Hair re-roll moved the Headgear" % seed)

    def test_rerolling_headgear_from_raw_never_lands_on_a_helmet(self):
        """The forward direction through the same path: the updo is pinned and
        the Headgear is free, so the helmets are what give way."""
        worn = worn_helmets(TABLES)
        for seed in range(200):
            npc = roll(seed, Hair=UPDO, Headgear=BARE)
            value = gen.reroll_trait(TABLES, npc, "Headgear", random.Random(seed))
            self.assertNotIn(
                value, worn,
                "seed %d: re-rolled a helmet over a topknot" % seed)

    def test_an_ordinary_headgear_still_reaches_an_updo(self):
        """The other half. Yielding for every Headgear would make the updos
        unreachable rather than merely unpaired."""
        updos = updo_cuts(TABLES)
        reached = sum(
            roll(seed, Headgear=BARE)["Hair"] in updos for seed in range(400))
        self.assertTrue(reached)

    def test_naming_both_by_hand_is_honoured_rather_than_refused(self):
        """The same asymmetry with Age/Build and Role/Outfit that the
        carried-helmet pairing has, and for the same reason. Both clauses are
        true of the figure and only the render is ugly, so someone naming both
        with --set-trait is overriding an aesthetic default on purpose."""
        npc = roll(0, Hair=UPDO, Headgear=HELMET)
        self.assertIn(npc["Hair"], updo_cuts(TABLES))
        self.assertIn(npc["Headgear"], worn_helmets(TABLES))


class TestTheRegistersAreRecorded(unittest.TestCase):
    def test_a_roll_records_whether_the_hair_is_an_updo(self):
        self.assertTrue(roll(0, Hair=UPDO)["_hair_updo"])
        self.assertFalse(roll(0, Hair=FLAT)["_hair_updo"])

    def test_a_roll_records_whether_the_headgear_is_a_helmet(self):
        self.assertTrue(roll(0, Headgear=HELMET)["_headgear_helmet"])
        self.assertFalse(roll(0, Headgear=BARE)["_headgear_helmet"])

    def test_both_traits_are_still_rerollable(self):
        """The whole reason the keys exist. Gating either on the other's flag
        is what would otherwise put it in UNREROLLABLE_REASONS, and the import
        GUI builds its Re-roll buttons from this tuple."""
        for name in ("Hair", "Headgear"):
            with self.subTest(trait=name):
                self.assertIn(name, gen.REROLLABLE_TRAITS)
                self.assertNotIn(name, gen.UNREROLLABLE_REASONS)


class TestTheLegacyRerollRespectsIt(unittest.TestCase):
    """The lossy path: an entry with no raw bullets to pin.

    Both traits are re-rollable from such an entry, so the clash is reachable
    from either side - a Headgear re-rolled onto a helmet above a stored updo,
    or a Hair re-rolled onto an updo beneath a stored helmet. Each direction
    needs the other trait's register recorded, exactly as '_gear_helmet' is
    recorded for the carried-helmet pairing.
    """

    def _entry_npc(self, key, register, **overrides):
        npc = roll(0, **overrides)
        npc.pop("_raw")
        npc[key] = register
        return npc

    def test_a_recorded_updo_never_rerolls_a_helmet_over_it(self):
        worn = worn_helmets(TABLES)
        self.assertTrue(worn, "fixture needs a worn helmet to avoid")
        npc = self._entry_npc("_hair_updo", True, Hair=UPDO)
        for seed in range(200):
            value = gen.reroll_trait(TABLES, npc, "Headgear", random.Random(seed))
            self.assertNotIn(value, worn, "seed %d" % seed)

    def test_a_recorded_flat_cut_still_reaches_a_helmet(self):
        worn = worn_helmets(TABLES)
        npc = self._entry_npc("_hair_updo", False, Hair=FLAT)
        reached = sum(
            gen.reroll_trait(TABLES, npc, "Headgear", random.Random(seed)) in worn
            for seed in range(200))
        self.assertTrue(reached)

    def test_a_recorded_helmet_never_rerolls_an_updo_under_it(self):
        updos = updo_cuts(TABLES)
        npc = self._entry_npc("_headgear_helmet", True, Headgear=HELMET)
        for seed in range(200):
            value = gen.reroll_trait(TABLES, npc, "Hair", random.Random(seed))
            self.assertNotIn(value, updos, "seed %d" % seed)

    def test_recorded_ordinary_headgear_still_reaches_an_updo(self):
        updos = updo_cuts(TABLES)
        npc = self._entry_npc("_headgear_helmet", False, Headgear=BARE)
        reached = sum(
            gen.reroll_trait(TABLES, npc, "Hair", random.Random(seed)) in updos
            for seed in range(200))
        self.assertTrue(reached)

    def test_an_entry_predating_the_hair_key_rerolls_unrestricted(self):
        """None is 'not recorded', which is not the same as False. It must
        behave as it did before this change rather than silently claiming the
        hair lay flat."""
        worn = worn_helmets(TABLES)
        npc = self._entry_npc("_hair_updo", None, Hair=UPDO)
        with _quiet_stderr():
            reached = sum(
                gen.reroll_trait(TABLES, npc, "Headgear", random.Random(seed))
                in worn for seed in range(200))
        self.assertTrue(reached)

    def test_an_entry_predating_the_headgear_key_rerolls_unrestricted(self):
        updos = updo_cuts(TABLES)
        npc = self._entry_npc("_headgear_helmet", None, Headgear=HELMET)
        with _quiet_stderr():
            reached = sum(
                gen.reroll_trait(TABLES, npc, "Hair", random.Random(seed))
                in updos for seed in range(200))
        self.assertTrue(reached)

    def test_an_entry_predating_the_hair_key_says_so(self):
        npc = self._entry_npc("_hair_updo", None, Hair=UPDO)
        with _quiet_stderr() as err:
            gen.reroll_trait(TABLES, npc, "Headgear", random.Random(0))
        self.assertIn("no recorded hair register", err.getvalue())

    def test_an_entry_predating_the_headgear_key_says_so(self):
        npc = self._entry_npc("_headgear_helmet", None, Headgear=HELMET)
        with _quiet_stderr() as err:
            gen.reroll_trait(TABLES, npc, "Hair", random.Random(0))
        self.assertIn("no recorded headgear register", err.getvalue())

    def test_recorded_registers_warn_about_nothing(self):
        for key, trait, overrides in (
                ("_hair_updo", "Headgear", {"Hair": UPDO}),
                ("_headgear_helmet", "Hair", {"Headgear": HELMET})):
            with self.subTest(trait=trait):
                npc = self._entry_npc(key, True, **overrides)
                with _quiet_stderr() as err:
                    gen.reroll_trait(TABLES, npc, trait, random.Random(0))
                self.assertEqual(err.getvalue(), "")


class TestTheLiveTable(unittest.TestCase):
    def _flagged(self):
        return " ".join(b for b in bullets_for(LIVE, "Hair")
                        if "updo" in gen.split_flags(b)[1])

    def test_the_reported_bullet_is_flagged(self):
        """The hairstyle that produced the report: a high bun with ornamental
        pins and a trailing ribbon, rendered through a flight helmet."""
        self.assertIn("secured with ornamental pins and a trailing ribbon",
                      self._flagged())

    def test_every_tall_gathered_cut_is_flagged(self):
        """The rest of the set the flag was widened to cover. These sit on top
        of the skull, so a helmet has nowhere to go."""
        flagged = self._flagged()
        for wanted in ("high, tight", "messy", "topknot", "twin space buns",
                       "high ponytail bound near the crown",
                       "twin high", "floral hairpin ornament",
                       "dangling metal pins gathered at the crown",
                       "loose bun already falling apart"):
            with self.subTest(phrase=wanted):
                self.assertIn(wanted, flagged,
                              "%r is not flagged 'updo'" % wanted)

    def test_every_swept_up_bullet_is_flagged(self):
        """The construction rather than the list. 'swept up' says the mass has
        been moved onto the crown and left there, which is the whole of what
        'updo' means, so no bullet can carry the phrase and stay unflagged.
        The enumeration above missed 'a loose bun already falling apart' on the
        first pass and a rolled civilian wore a pilot's helmet through it; a
        rule catches the next one at the moment it is written instead.

        'swept back' and 'swept across' are deliberately not matched - those
        move hair off the face, not onto the top of the head, and the neat low
        bun is 'swept back'."""
        for bullet in bullets_for(LIVE, "Hair"):
            text, flags = gen.split_flags(bullet)
            if "swept up" not in text:
                continue
            with self.subTest(bullet=text):
                self.assertIn("updo", flags,
                              "%r is swept up and not flagged 'updo'" % text)

    def test_nothing_that_lies_flat_is_flagged(self):
        """The narrow reading the design picked. A braid pinned close to the
        head, a low bun or a bob leaves the crown free, and those are exactly
        the cuts someone puts a helmet on over."""
        flagged = self._flagged()
        for unwanted in ("close-cropped", "shaved head", "neat low bun",
                         "pinned close to the head", "bob", "chin-length",
                         "pinned up off the collar", "headscarf"):
            with self.subTest(phrase=unwanted):
                self.assertNotIn(unwanted, flagged,
                                 "%r lies flat and should not be 'updo'"
                                 % unwanted)

    def test_an_updo_keeps_a_varied_headgear_pool(self):
        """The starvation guard against the live content rather than the
        fixture: the flagged helmets are a small fraction of the table, and
        this asserts the floor rather than an exact count so adding a bullet
        does not fail the suite."""
        pool = [b for b in bullets_for(LIVE, "Headgear")
                if "helmet" not in gen.split_flags(b)[1]]
        self.assertGreaterEqual(len(pool), 50)

    def test_a_helmet_keeps_a_varied_hair_pool(self):
        pool = [b for b in bullets_for(LIVE, "Hair")
                if "updo" not in gen.split_flags(b)[1]]
        self.assertGreaterEqual(len(pool), 40)

    def test_no_other_table_carries_updo(self):
        """'updo' gates Hair only. Anywhere else it would be inert and would
        read as though something were filtering on it."""
        for name in gen.REQUIRED_TABLES:
            if name == "Hair":
                continue
            for bullet in bullets_for(LIVE, name):
                self.assertNotIn("updo", gen.flags_for(name, bullet),
                                 "%s carries an inert 'updo' flag" % name)


if __name__ == "__main__":
    unittest.main()
