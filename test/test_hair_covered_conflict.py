"""The other half of the one-head-one-volume rule.

'updo' keeps a helmet off hair gathered on the crown. This suite covers the
clash from the opposite direction: three live Hair bullets name something
*worn* as part of the cut - "a wrapped headscarf with a few {colour} strands
escaping at the temple", "a long {colour} ponytail pulled through the back of
a worn cap", "twin high {colour} ponytails held back by the band of a chunky
headset". Headgear rolls independently of Hair, so before 'covered' those
bullets put a second object on the same head: 94 rolls in 3000 paired one with
worn headgear and 16 with a worn helmet.

The difference from 'updo', and the thing most of these tests exist to pin
down, is how wide the gate is. 'updo' drops only `helmet` and hands back sixty
other bullets, because a bun under a brow visor reads fine. 'covered' has
nothing to hand back: a headscarf leaves no room for a felt hat or even a
hairband, so the Headgear pool is cut to the single bullet flagged `bare`.
A filter keyed on `helmet` would pass a suite that only ever tested helmets,
so the fixture below deliberately makes the *soft hat* the thing that has to
be dropped.

It is still not a lock in the ROLE_LOCKS sense - a tables file with no `bare`
bullet gets the whole pool back rather than an empty roll.
"""
import contextlib
import io
import random
import re
import sys
import unittest

from test.helpers import (
    FIXTURE_TABLES, REPO, bullets_for, load_generator, rendered)

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")

COVERED = "a wrapped {colour} headscarf, a few strands loose at the temple || covered"
UNCOVERED = "a short {colour} crop"
UPDO = "a high, tight {colour} topknot || updo"
BARE = "{Subject} {is_are} bare-headed. || bare"
HAT = "{Subject} {wear} a wide woven hat."
HELMET = "{Subject} {wear} a sealed flight helmet. || hardtech helmet"


def _covered_tables():
    """The shared fixture plus the bullets these tests need.

    Built in memory rather than written into fixtures/tables-minimal.md, for
    the reason test_helmet_conflict.py spells out at length: that file is the
    baseline for fixtures/roll-snapshot.json, and adding a bullet to a table
    changes every seed's draw from it.

    The Headgear pool needs all three registers separated. The bare bullet is
    what 'covered' filters down to and carries the flag that names it. The
    woven hat is the load-bearing one: it is worn, it is soft, and it is not a
    helmet, so a filter keyed on 'helmet' rather than on the absence of 'bare'
    fails here and nowhere else. The helmet is kept so the two pairings can be
    shown not to have collapsed into each other.

    The fixture's woven hat carries an '@alpha' theme tag, which would gate it
    behind a Theme roll and make "the hat was reachable" depend on something
    this suite is not testing. It is replaced rather than added to.
    """
    tables = gen.parse_tables(FIXTURE_TABLES)
    tables["Hair"] = tables["Hair"] + [COVERED, UNCOVERED, UPDO]
    tables["Headgear"] = [
        BARE if "bare-headed" in b else
        HAT if "woven hat" in b else
        HELMET if "sealed flight helmet" in b else b
        for b in tables["Headgear"]]
    return tables


TABLES = _covered_tables()


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


def covered_cuts(tables):
    """Every string a 'covered' Hair bullet can appear as in a rolled NPC."""
    out = set()
    for bullet in bullets_for(tables, "Hair"):
        if "covered" in gen.split_flags(bullet)[1]:
            out |= rendered(tables, "Hair", bullet)
    return out


def worn_headgear(tables):
    """Every string a Headgear bullet that is NOT bare can appear as.

    The complement of the flag rather than a list of helmets - that is exactly
    the register 'covered' has to keep out, and building it this way means a
    bullet added to the fixture is covered by these tests automatically.
    """
    out = set()
    for bullet in bullets_for(tables, "Headgear"):
        if "bare" not in gen.split_flags(bullet)[1]:
            out |= rendered(tables, "Headgear", bullet)
    return out


def bare_headgear(tables):
    out = set()
    for bullet in bullets_for(tables, "Headgear"):
        if "bare" in gen.split_flags(bullet)[1]:
            out |= rendered(tables, "Headgear", bullet)
    return out


class TestTheRollIsGated(unittest.TestCase):
    def test_a_covered_cut_never_rolls_headgear_over_it(self):
        worn = worn_headgear(TABLES)
        self.assertTrue(worn, "fixture needs worn headgear to avoid")
        for seed in range(400):
            npc = roll(seed, Hair=COVERED)
            self.assertNotIn(
                npc["Headgear"], worn,
                "seed %d: headgear went on over hair that already names a "
                "covering" % seed)

    def test_a_covered_cut_drops_the_soft_hat_too(self):
        """The test that separates this filter from 'updo'.

        A woven hat is worn, soft, and not a helmet. Keying this pairing on
        'helmet' - the obvious thing to reach for, since the sibling filter
        does - would leave a felt hat sitting on top of a headscarf, and every
        other assertion in this class would still pass.
        """
        hats = rendered(TABLES, "Headgear", HAT)
        self.assertTrue(hats)
        for seed in range(400):
            self.assertNotIn(roll(seed, Hair=COVERED)["Headgear"], hats,
                             "seed %d: a soft hat over a headscarf" % seed)

    def test_a_covered_cut_still_rolls_something(self):
        """The pool is narrowed to one bullet, not to none."""
        bare = bare_headgear(TABLES)
        for seed in range(200):
            self.assertIn(roll(seed, Hair=COVERED)["Headgear"], bare)

    def test_an_uncovered_cut_still_reaches_worn_headgear(self):
        """The other half of the gate. Filtering headgear out for everyone
        would pass the tests above by making the whole table dead content."""
        worn = worn_headgear(TABLES)
        reached = sum(roll(seed, Hair=UNCOVERED)["Headgear"] in worn
                      for seed in range(400))
        self.assertTrue(reached, "an uncovered cut never reached headgear")

    def test_the_two_pairings_have_not_collapsed_into_each_other(self):
        """'updo' must still hand back everything that is not a helmet.

        Widening it to 'covered's gate would be a silent regression: a topknot
        under a brow visor is fine and is content the tables are meant to
        reach.
        """
        reached = sum(roll(seed, Hair=UPDO)["Headgear"] in rendered(
            TABLES, "Headgear", HAT) for seed in range(400))
        self.assertTrue(reached, "an updo lost the soft hat as well")

    def test_the_flag_never_reaches_a_prompt(self):
        for seed in range(200):
            npc = roll(seed, Hair=COVERED)
            self.assertNotIn("covered", npc["Hair"])
            self.assertNotIn("||", npc["Hair"])
            self.assertNotIn("bare ", npc["Headgear"])
            self.assertNotIn("||", npc["Headgear"])
            for prompt in gen.build_prompts(npc):
                self.assertNotIn("|| covered", prompt)
                self.assertNotIn("|| bare", prompt)


class TestTheHeadgearClauseGivesWay(unittest.TestCase):
    """Forcing the bare bullet is only half the fix.

    That bullet has prose of its own - "{Subject} {is_are} bare-headed." - so
    winning the pool for it would put "a wrapped headscarf" and "She is
    bare-headed." in the same prompt, and a render told both does not get to
    pick the sensible one. The hair phrase IS the headgear for these bullets,
    so the headgear clause is what vanishes.

    This contradiction is older than the flag: on the bare bullet's x6 weight
    a covered cut already rolled it about a third of the time and read just as
    badly. Forcing it turned an occasional collision into a certainty, which
    is how it was noticed.
    """

    def test_a_covered_cut_prints_no_headgear_clause(self):
        for seed in range(50):
            npc = roll(seed, Hair=COVERED)
            for prompt in gen.build_prompts(npc):
                self.assertNotIn("bare-headed", prompt, "seed %d" % seed)

    def test_an_uncovered_cut_still_prints_one(self):
        """The clause is load-bearing for everyone else - 'bare-headed' is a
        real instruction, not filler."""
        npc = roll(0, Hair=UNCOVERED, Headgear=BARE)
        self.assertTrue(
            any("bare-headed" in p for p in gen.build_prompts(npc)))

    def test_a_worn_hat_still_prints(self):
        npc = roll(0, Hair=UNCOVERED, Headgear=HAT)
        self.assertTrue(any("woven hat" in p for p in gen.build_prompts(npc)))

    def test_the_vanished_clause_leaves_no_doubled_space(self):
        """Why the slot is pre-formatted with its trailing space rather than
        left bare in the template - the same reason faction_line is."""
        for seed in range(50):
            for prompt in gen.build_prompts(roll(seed, Hair=COVERED)):
                self.assertNotIn("  ", prompt, "seed %d" % seed)

    def test_the_sentence_either_side_still_joins_up(self):
        """One space, one sentence break, whichever pronoun set rolled."""
        for seed in range(20):
            for prompt in gen.build_prompts(roll(seed, Hair=COVERED)):
                self.assertRegex(
                    prompt, r"frame\. (His|Her|Their) face carries")

    def test_an_entry_predating_the_register_still_prints_it(self):
        """None is 'not recorded'. The honest answer is the behaviour that
        shipped before the flag, not a fabricated suppression."""
        npc = roll(0, Hair=COVERED)
        npc["_hair_covered"] = None
        self.assertTrue(
            any("bare-headed" in p for p in gen.build_prompts(npc)))

    def test_the_helper_is_shared_rather_than_restated(self):
        """generate-3d.py builds its back-view prompt from its own template
        and has to reach the same answer; a second copy of the rule is a
        second thing to keep in step."""
        self.assertTrue(callable(gen.headgear_line))
        self.assertEqual(gen.headgear_line({"_hair_covered": True}), "")
        self.assertEqual(
            gen.headgear_line({"_hair_covered": False, "Headgear": "X."}),
            "X. ")


class TestTheFilterRunsBothWays(unittest.TestCase):
    """Hair is rolled first, so normally the Headgear yields. When the Headgear
    is the pinned one, the Hair has to yield instead - the same shape the
    updo/helmet pairing uses, and for the same reason: an edge either way would
    put one of the two traits into TRAIT_DEPENDENTS and cost it its one-click
    re-roll button in the import GUI.
    """

    def test_a_pinned_soft_hat_drops_the_covered_cuts(self):
        covered = covered_cuts(TABLES)
        self.assertTrue(covered)
        for seed in range(400):
            self.assertNotIn(roll(seed, Headgear=HAT)["Hair"], covered,
                             "seed %d" % seed)

    def test_a_pinned_helmet_drops_them_as_well(self):
        covered = covered_cuts(TABLES)
        for seed in range(400):
            self.assertNotIn(roll(seed, Headgear=HELMET)["Hair"], covered,
                             "seed %d" % seed)

    def test_pinned_bare_headgear_still_reaches_a_covered_cut(self):
        covered = covered_cuts(TABLES)
        reached = sum(roll(seed, Headgear=BARE)["Hair"] in covered
                      for seed in range(400))
        self.assertTrue(reached, "bare headgear lost the covered cuts")

    def test_a_pinned_hat_leaves_a_varied_hair_pool(self):
        seen = {roll(seed, Headgear=HAT)["Hair"] for seed in range(400)}
        self.assertGreater(len(seen), 1)

    def test_forcing_both_by_hand_is_honoured(self):
        """Not refused, the same way two helmets and a bun-in-a-helmet are
        not. Naming both with --set-trait is an aesthetic override made on
        purpose, which is what --set-trait is for."""
        npc = roll(0, Hair=COVERED, Headgear=HAT)
        self.assertIn(npc["Hair"], covered_cuts(TABLES))
        self.assertIn(npc["Headgear"], rendered(TABLES, "Headgear", HAT))


class TestTheRegistersAreRecorded(unittest.TestCase):
    def test_a_roll_records_whether_the_hair_is_covered(self):
        self.assertTrue(roll(0, Hair=COVERED)["_hair_covered"])
        self.assertFalse(roll(0, Hair=UNCOVERED)["_hair_covered"])

    def test_a_roll_records_whether_the_headgear_is_bare(self):
        self.assertTrue(roll(0, Headgear=BARE)["_headgear_bare"])
        self.assertFalse(roll(0, Headgear=HAT)["_headgear_bare"])

    def test_the_helmet_register_does_not_answer_this_question(self):
        """Why this pairing needs its own two keys rather than borrowing the
        updo/helmet pair. A soft hat is worn and is not a helmet, so
        '_headgear_helmet' is False for exactly the case 'covered' must keep
        out, and a Hair re-roll reading it would call a headscarf under a felt
        hat clean."""
        npc = roll(0, Headgear=HAT)
        self.assertFalse(npc["_headgear_helmet"])
        self.assertFalse(npc["_headgear_bare"])

    def test_both_traits_are_still_rerollable(self):
        for name in ("Hair", "Headgear"):
            with self.subTest(trait=name):
                self.assertIn(name, gen.REROLLABLE_TRAITS)
                self.assertNotIn(name, gen.UNREROLLABLE_REASONS)


class TestTheLegacyRerollRespectsIt(unittest.TestCase):
    """The lossy path: an entry with no raw bullets to pin. Both traits are
    re-rollable from such an entry, so the clash is reachable from either
    side and each direction needs the other trait's register recorded.
    """

    def _entry_npc(self, key, register, **overrides):
        npc = roll(0, **overrides)
        npc.pop("_raw")
        npc[key] = register
        return npc

    def test_recorded_covered_hair_never_rerolls_headgear_over_it(self):
        worn = worn_headgear(TABLES)
        npc = self._entry_npc("_hair_covered", True, Hair=COVERED)
        for seed in range(200):
            value = gen.reroll_trait(TABLES, npc, "Headgear", random.Random(seed))
            self.assertNotIn(value, worn, "seed %d" % seed)

    def test_recorded_uncovered_hair_still_reaches_headgear(self):
        worn = worn_headgear(TABLES)
        npc = self._entry_npc("_hair_covered", False, Hair=UNCOVERED)
        reached = sum(
            gen.reroll_trait(TABLES, npc, "Headgear", random.Random(seed)) in worn
            for seed in range(200))
        self.assertTrue(reached)

    def test_recorded_worn_headgear_never_rerolls_a_covered_cut(self):
        covered = covered_cuts(TABLES)
        npc = self._entry_npc("_headgear_bare", False, Headgear=HAT)
        for seed in range(200):
            value = gen.reroll_trait(TABLES, npc, "Hair", random.Random(seed))
            self.assertNotIn(value, covered, "seed %d" % seed)

    def test_recorded_bare_headgear_still_reaches_a_covered_cut(self):
        covered = covered_cuts(TABLES)
        npc = self._entry_npc("_headgear_bare", True, Headgear=BARE)
        reached = sum(
            gen.reroll_trait(TABLES, npc, "Hair", random.Random(seed)) in covered
            for seed in range(200))
        self.assertTrue(reached)

    def test_an_entry_predating_the_hair_key_rerolls_unrestricted(self):
        """None is 'not recorded', which is not the same as False. It behaves
        as it did before this change rather than fabricating an answer."""
        worn = worn_headgear(TABLES)
        npc = self._entry_npc("_hair_covered", None, Hair=COVERED)
        with _quiet_stderr():
            reached = sum(
                gen.reroll_trait(TABLES, npc, "Headgear", random.Random(seed))
                in worn for seed in range(200))
        self.assertTrue(reached)

    def test_an_entry_predating_the_headgear_key_rerolls_unrestricted(self):
        covered = covered_cuts(TABLES)
        npc = self._entry_npc("_headgear_bare", None, Headgear=HAT)
        with _quiet_stderr():
            reached = sum(
                gen.reroll_trait(TABLES, npc, "Hair", random.Random(seed))
                in covered for seed in range(200))
        self.assertTrue(reached)

    def test_an_entry_predating_the_hair_key_says_so(self):
        npc = self._entry_npc("_hair_covered", None, Hair=COVERED)
        with _quiet_stderr() as err:
            gen.reroll_trait(TABLES, npc, "Headgear", random.Random(0))
        self.assertIn("no recorded hair covering", err.getvalue())

    def test_an_entry_predating_the_headgear_key_says_so(self):
        npc = self._entry_npc("_headgear_bare", None, Headgear=HAT)
        with _quiet_stderr() as err:
            gen.reroll_trait(TABLES, npc, "Hair", random.Random(0))
        self.assertIn("no recorded headgear register", err.getvalue())

    def test_recorded_registers_warn_about_nothing(self):
        for key, trait, overrides in (
                ("_hair_covered", "Headgear", {"Hair": COVERED}),
                ("_headgear_bare", "Hair", {"Headgear": HAT})):
            with self.subTest(trait=trait):
                npc = self._entry_npc(key, True, **overrides)
                with _quiet_stderr() as err:
                    gen.reroll_trait(TABLES, npc, trait, random.Random(0))
                self.assertEqual(err.getvalue(), "")


class TestTheManifestRoundTrip(unittest.TestCase):
    def test_the_keys_survive_a_write_and_read(self):
        npc = roll(0, Hair=COVERED)
        entry = {}
        for key, name in (("hair_covered", "_hair_covered"),
                          ("headgear_bare", "_headgear_bare")):
            entry[key] = npc[name]
        back = {}
        back["_hair_covered"] = entry.get("hair_covered")
        back["_headgear_bare"] = entry.get("headgear_bare")
        self.assertTrue(back["_hair_covered"])
        self.assertTrue(back["_headgear_bare"])

    def test_an_absent_key_reads_back_as_none_not_false(self):
        self.assertIsNone({}.get("hair_covered"))


class TestTheLiveTable(unittest.TestCase):
    def _covered(self):
        return " ".join(b for b in bullets_for(LIVE, "Hair")
                        if "covered" in gen.split_flags(b)[1])

    def test_every_bullet_that_names_a_worn_thing_is_flagged(self):
        """The three that produced the report. Each names an object worn on
        the head as part of the hair phrase."""
        covered = self._covered()
        for wanted in ("headscarf", "worn cap", "chunky headset"):
            with self.subTest(phrase=wanted):
                self.assertIn(wanted, covered,
                              "%r is not flagged 'covered'" % wanted)

    def test_no_hair_bullet_names_a_worn_thing_unflagged(self):
        """The rule rather than the list, the same shape as the 'swept up'
        audit next door. A Hair bullet naming any of these has put an object
        on the head and must say so; the enumeration above only catches what
        its author already thought of.

        'headband' and 'hairband' are deliberately absent - those are Headgear
        bullets, and as *hair* they would be ornaments rather than coverings.

        Matched on word boundaries, not substrings: the first draft of this
        test read 'hat' out of "t*hat*" and 'cap' out of "es*cap*ing" and
        failed three innocent bullets.
        """
        for bullet in bullets_for(LIVE, "Hair"):
            text, flags = gen.split_flags(bullet)
            named = [w for w in ("headscarf", "cap", "hood", "headset",
                                 "helmet", "hat", "bandana", "visor")
                     if re.search(r"\b%s\b" % w, text.lower())]
            if not named:
                continue
            with self.subTest(bullet=text):
                self.assertIn("covered", flags,
                              "%r names %s and is not flagged 'covered'"
                              % (text, named))

    def test_hair_ornaments_are_not_flagged(self):
        """The narrow reading. A clip, a pin, a ribbon, a flower or a
        mechanical binder is part of the hairstyle and leaves the head free
        for a hat - flagging those would cost the pairing for nothing."""
        covered = self._covered()
        for unwanted in ("floral hairpin", "trailing ribbon", "metal clip",
                         "ornamental clips", "mechanical binder",
                         "frayed cord"):
            with self.subTest(phrase=unwanted):
                self.assertNotIn(unwanted, covered,
                                 "%r is an ornament, not a covering"
                                 % unwanted)

    def test_exactly_one_live_headgear_bullet_is_bare(self):
        """'covered' narrows the pool to this bullet, so a second one would
        silently double what a covered cut can roll, and none at all would
        hand back the whole table and undo the filter.

        Counted distinct: parse_tables() expands an 'xN' weight into N copies,
        so the pool holds six of this one bullet.
        """
        flagged = {b for b in bullets_for(LIVE, "Headgear")
                   if "bare" in gen.split_flags(b)[1]}
        self.assertEqual(len(flagged), 1, flagged)
        self.assertIn("bare-headed", flagged.pop())

    def test_the_bare_bullet_keeps_its_weight(self):
        """It carries an 'x6' that sets how often anyone is bare-headed at
        all. A flag appended past the weight must not have disturbed it."""
        flagged = [b for b in bullets_for(LIVE, "Headgear")
                   if "bare" in gen.split_flags(b)[1]]
        self.assertEqual(len(flagged), 6,
                         "the x6 weight on the bare bullet did not expand")

    def test_a_covered_cut_keeps_a_varied_hair_pool(self):
        pool = [b for b in bullets_for(LIVE, "Hair")
                if "covered" not in gen.split_flags(b)[1]]
        self.assertGreaterEqual(len(pool), 60)

    def test_no_other_table_carries_these_flags(self):
        """'covered' gates Hair and 'bare' marks Headgear. Anywhere else
        either would be inert and would read as though something filtered
        on it."""
        for name in gen.REQUIRED_TABLES:
            for bullet in bullets_for(LIVE, name):
                flags = gen.flags_for(name, bullet)
                if name != "Hair":
                    self.assertNotIn("covered", flags,
                                     "%s carries an inert 'covered'" % name)
                if name != "Headgear":
                    self.assertNotIn("bare", flags,
                                     "%s carries an inert 'bare'" % name)


class TestTheLiveRollIsClean(unittest.TestCase):
    def test_no_seed_pairs_a_covered_cut_with_worn_headgear(self):
        """The measurement the report rests on, against the live tables rather
        than the fixture. 94 rolls in 3000 hit this before the change."""
        clashes = []
        for seed in range(1500):
            npc = gen.roll_npc(LIVE, random.Random(seed))
            if npc["_hair_covered"] and not npc["_headgear_bare"]:
                clashes.append((seed, npc["Hair"], npc["Headgear"]))
        self.assertEqual(clashes, [])

    def test_covered_cuts_still_roll_at_all(self):
        """Zero clashes would also be the result of the three bullets having
        become unreachable."""
        reached = sum(gen.roll_npc(LIVE, random.Random(seed))["_hair_covered"]
                      for seed in range(1500))
        self.assertTrue(reached, "no covered cut was reachable at all")


if __name__ == "__main__":
    unittest.main()
