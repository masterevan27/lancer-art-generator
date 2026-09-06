"""A figure already wearing a helmet does not also carry one.

A rolled pilot came out in a sealed tactical helmet with a smoked visor - and
with a scarred pilot helmet held in the crook of one elbow. Two helmets, one
head. The Gear bullet reads as a pilot between sorties, which is exactly why it
is in the table; it only breaks when the head it belongs on is already covered.

'helmet' is deliberately not 'hardtech'. Hard tech is the whole modern register
- headsets, visor bands, ear implants - and none of those fight a helmet held
under an arm. The flag marks the narrower case: a helmet actually worn on the
head. A cap, a headset or a brow visor still reaches the carried helmet, which
is a pairing that reads well and would be lost to the wider flag.

Gear is the table that yields, the same way it yields to a Weapon that occupies
the hands: Headgear precedes Gear in REQUIRED_TABLES, and the helmet on the
head is the more defining object.
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

HELMET = "{Subject} {wear} a sealed flight helmet. || hardtech helmet"
VISOR = "{Subject} {wear} a slim visor band across the brow. || hardtech"
BARE = "{Subject} {is_are} bare-headed."
CARRIED_HELMET = "a scarred pilot helmet in the crook of one elbow || hands helmet"


def _helmet_tables():
    """The shared fixture plus the three bullets these tests need.

    Built here rather than written into fixtures/tables-minimal.md on purpose.
    That file is the shared fixture for fifty-odd modules and the baseline for
    fixtures/roll-snapshot.json, which asserts that five named seeds still roll
    exactly what they rolled when it was captured. Adding a bullet to a table
    changes its pool, so every one of those seeds draws differently and the
    snapshot fails - not because anything regressed, but because the fixture it
    was captured from is gone. Keeping the additions in memory leaves that
    guard measuring what it was written to measure.

    The pool needs all three: a worn helmet to trigger the filter, a carried
    one for it to drop, and a hardtech bullet that is NOT a helmet, so a filter
    keyed on 'hardtech' instead of 'helmet' cannot pass this suite.
    """
    tables = gen.parse_tables(FIXTURE_TABLES)
    tables["Headgear"] = [
        BARE if b.startswith("{Subject} {is_are} bare-headed") else b
        for b in tables["Headgear"]]
    tables["Headgear"] = [
        HELMET if "sealed flight helmet" in b else b
        for b in tables["Headgear"]] + [VISOR]
    tables["Gear"] = tables["Gear"] + [CARRIED_HELMET]
    return tables


TABLES = _helmet_tables()


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


def carried_helmets(tables):
    """Every string a 'helmet' Gear bullet can appear as in a rolled NPC.

    Gear bullets carry '{possessive}' and roll_npc() substitutes it before
    storing the value, so comparing a rolled Gear against the raw bullet does
    not reliably match. rendered() expands the source side across every pronoun
    set, which makes the comparisons below plain set membership - the same
    trick test_headgear_register.py uses on Headgear.
    """
    out = set()
    for bullet in bullets_for(tables, "Gear"):
        if "helmet" in gen.split_flags(bullet)[1]:
            out |= rendered(tables, "Gear", bullet)
    return out


def worn_helmets(tables):
    """Every string a 'helmet' Headgear bullet can appear as in a rolled NPC."""
    out = set()
    for bullet in bullets_for(tables, "Headgear"):
        if "helmet" in gen.split_flags(bullet)[1]:
            out |= rendered(tables, "Headgear", bullet)
    return out


class TestTheRollIsGated(unittest.TestCase):
    def test_a_worn_helmet_never_rolls_a_carried_one(self):
        carried = carried_helmets(TABLES)
        self.assertTrue(carried, "fixture needs a carried helmet to avoid")
        for seed in range(400):
            npc = roll(seed, Headgear=HELMET)
            self.assertNotIn(
                npc["Gear"], carried,
                "seed %d: a helmeted figure is carrying a second helmet" % seed)

    def test_a_bare_head_still_reaches_the_carried_helmet(self):
        """The other half of the gate. Filtering it for everyone would pass the
        test above by making the bullet dead content."""
        carried = carried_helmets(TABLES)
        reached = sum(
            roll(seed, Headgear=BARE)["Gear"] in carried for seed in range(400))
        self.assertTrue(reached, "a bare head never reached the carried helmet")

    def test_other_hard_tech_still_reaches_the_carried_helmet(self):
        """Keyed on 'helmet', not 'hardtech'. A brow visor leaves the crown
        free, and a helmet under the arm beside it reads fine."""
        carried = carried_helmets(TABLES)
        reached = sum(
            roll(seed, Headgear=VISOR)["Gear"] in carried for seed in range(400))
        self.assertTrue(reached, "a visor band lost the carried helmet too")

    def test_a_gated_roll_still_has_somewhere_to_go(self):
        """Variety, not just legality: a helmeted figure must reach more than
        one Gear, or the gate has replaced a clash with a uniform."""
        seen = {roll(seed, Headgear=HELMET)["Gear"] for seed in range(400)}
        self.assertGreater(len(seen), 1)

    def test_the_flag_never_reaches_a_prompt(self):
        for seed in range(200):
            npc = roll(seed)
            self.assertNotIn("helmet ||", npc["Gear"])
            for prompt in gen.build_prompts(npc):
                self.assertNotIn("|| helmet", prompt)


class TestTheFilterRunsBothWays(unittest.TestCase):
    """Headgear is rolled first, so normally the Gear yields. When the Gear is
    the pinned one, the Headgear has to yield instead - the same shape the
    Age/Build and Role/Outfit pairings already use, and for the same reason:
    an explicit or pinned choice should not collide with a random draw.
    """

    def test_headgear_stays_a_one_click_reroll(self):
        """Headgear must NOT gain a cascade edge, which is why the filter has
        to run both ways at all. It is one of the traits the import GUI
        re-rolls on a single click with no confirmation dialog, and an edge
        from it would silently move the Gear too."""
        self.assertNotIn("Headgear", gen.TRAIT_DEPENDENTS)
        self.assertEqual(gen.trait_cascade("Headgear"), ("Headgear",))

    def test_a_pinned_carried_helmet_is_never_rolled_a_worn_one(self):
        worn = worn_helmets(TABLES)
        self.assertTrue(worn, "fixture needs a worn helmet to avoid")
        for seed in range(400):
            npc = roll(seed, Gear=CARRIED_HELMET)
            self.assertNotIn(
                npc["Headgear"], worn,
                "seed %d: a carried helmet rolled a worn one over it" % seed)

    def test_rerolling_headgear_from_raw_never_lands_on_a_helmet(self):
        """The path that direction exists for. reroll_from_raw() pins every
        other trait - the carried Gear among them - and frees the Headgear, so
        the roller's own filter is what runs, with no rebuilt copy to drift."""
        carried = carried_helmets(TABLES)
        worn = worn_helmets(TABLES)
        for seed in range(200):
            npc = roll(seed, Headgear=BARE, Gear=CARRIED_HELMET)
            self.assertIn(npc["Gear"], carried, "seed %d: setup failed" % seed)
            value = gen.reroll_trait(TABLES, npc, "Headgear", random.Random(seed))
            self.assertNotIn(
                value, worn,
                "seed %d: re-rolled a helmet on over a carried one" % seed)
            self.assertIn(
                npc["Gear"], carried,
                "seed %d: a one-click Headgear re-roll moved the Gear" % seed)

    def test_an_ordinary_gear_still_reaches_a_worn_helmet(self):
        """The other half. Yielding for every Gear would make the worn helmets
        unreachable rather than merely unpaired."""
        worn = worn_helmets(TABLES)
        reached = sum(
            roll(seed, Gear="a canvas tool roll at the hip")["Headgear"] in worn
            for seed in range(400))
        self.assertTrue(reached)

    def test_naming_both_by_hand_is_honoured_rather_than_refused(self):
        """The deliberate asymmetry with Age/Build and Role/Outfit, which both
        raise when forced into contradiction. Two helmets contradict nothing -
        both clauses are true and only the render is ugly - so someone naming
        both with --set-trait is overriding an aesthetic default on purpose."""
        npc = roll(0, Headgear=HELMET, Gear=CARRIED_HELMET)
        self.assertIn(npc["Headgear"], worn_helmets(TABLES))
        self.assertIn(npc["Gear"], carried_helmets(TABLES))


class TestTheRegisterIsRecorded(unittest.TestCase):
    def test_a_roll_records_whether_the_gear_is_a_helmet(self):
        self.assertTrue(roll(0, Gear=CARRIED_HELMET)["_gear_helmet"])
        self.assertFalse(roll(0, Gear="a canvas tool roll at the hip")["_gear_helmet"])

    def test_headgear_is_still_rerollable(self):
        """The whole reason the key exists. Gating Headgear on the Gear roll's
        flag is what would otherwise put it in UNREROLLABLE_REASONS, and the
        import GUI builds its Re-roll buttons from this tuple."""
        self.assertIn("Headgear", gen.REROLLABLE_TRAITS)
        self.assertNotIn("Headgear", gen.UNREROLLABLE_REASONS)


class TestTheLegacyRerollRespectsIt(unittest.TestCase):
    """The lossy path: an entry with no raw bullets to pin.

    Gear itself is in UNREROLLABLE_REASONS, so this path never re-rolls the
    Gear - the only way back into the clash is re-rolling the HEADGEAR onto a
    helmet while the stored Gear is already a carried one. That is what the
    recorded register is for, exactly as '_outfit_notac' is for the register
    the same re-roll needs from the Outfit.
    """

    def _entry_npc(self, register, gear=CARRIED_HELMET):
        npc = roll(0, Gear=gear)
        npc.pop("_raw")
        npc["_gear_helmet"] = register
        return npc

    def test_a_recorded_carried_helmet_never_rerolls_into_a_worn_one(self):
        worn = worn_helmets(TABLES)
        self.assertTrue(worn, "fixture needs a worn helmet to avoid")
        npc = self._entry_npc(True)
        for seed in range(200):
            value = gen.reroll_trait(TABLES, npc, "Headgear", random.Random(seed))
            self.assertNotIn(value, worn, "seed %d" % seed)

    def test_recorded_ordinary_gear_still_reaches_a_worn_helmet(self):
        worn = worn_helmets(TABLES)
        npc = self._entry_npc(False, gear="a canvas tool roll at the hip")
        reached = sum(
            gen.reroll_trait(TABLES, npc, "Headgear", random.Random(seed)) in worn
            for seed in range(200))
        self.assertTrue(reached)

    def test_an_entry_predating_the_key_rerolls_unrestricted(self):
        """None is 'not recorded', which is not the same as False. It must
        behave as it did before this change rather than silently claiming the
        gear was helmetless."""
        worn = worn_helmets(TABLES)
        npc = self._entry_npc(None)
        with _quiet_stderr():
            reached = sum(
                gen.reroll_trait(TABLES, npc, "Headgear", random.Random(seed)) in worn
                for seed in range(200))
        self.assertTrue(reached)

    def test_an_entry_predating_the_key_says_so(self):
        npc = self._entry_npc(None)
        with _quiet_stderr() as err:
            gen.reroll_trait(TABLES, npc, "Headgear", random.Random(0))
        self.assertIn("no recorded gear register", err.getvalue())

    def test_a_recorded_register_warns_about_nothing(self):
        npc = self._entry_npc(True)
        with _quiet_stderr() as err:
            gen.reroll_trait(TABLES, npc, "Headgear", random.Random(0))
        self.assertEqual(err.getvalue(), "")


class TestTheLiveTable(unittest.TestCase):
    def test_every_worn_helmet_is_flagged(self):
        """A spot-check on the classification itself. These are the least
        arguable members of the set; if one is unflagged, the table edit was
        incomplete."""
        flagged = " ".join(b for b in bullets_for(LIVE, "Headgear")
                           if "helmet" in gen.split_flags(b)[1])
        for wanted in ("sealed tactical helmet", "night-vision helmet",
                       "open-face crash helmet", "sleek pilot's helmet",
                       "scuffed recon helmet", "domed flight helmet",
                       "full flight helmet", "composite ballistic helmet",
                       "sleek angular powered helmet", "kabuto"):
            self.assertIn(wanted, flagged, "%r is not flagged 'helmet'" % wanted)

    def test_nothing_worn_beside_the_head_is_flagged(self):
        """The narrow reading the design picked. A headset, a cap or a brow
        visor leaves the crown free and keeps the carried helmet reachable."""
        flagged = " ".join(b for b in bullets_for(LIVE, "Headgear")
                           if "helmet" in gen.split_flags(b)[1])
        for unwanted in ("ball cap", "hairband", "sunglasses", "ushanka",
                         "headphones", "straw hat", "welding visor"):
            self.assertNotIn(unwanted, flagged,
                             "%r is not a worn helmet" % unwanted)

    def test_the_carried_helmet_is_flagged(self):
        flagged = [b for b in bullets_for(LIVE, "Gear")
                   if "helmet" in gen.split_flags(b)[1]]
        self.assertTrue(flagged, "no Gear bullet carries the 'helmet' flag")
        for bullet in flagged:
            self.assertIn("helmet", bullet)

    def test_a_helmeted_figure_keeps_a_varied_gear_pool(self):
        """The starvation guard against the live content rather than the
        fixture: one flagged bullet out of a table this size can never empty
        it, and this asserts the floor rather than the exact count so adding a
        bullet does not fail the suite."""
        pool = [b for b in bullets_for(LIVE, "Gear")
                if "helmet" not in gen.split_flags(b)[1]]
        self.assertGreaterEqual(len(pool), 25)

    def test_no_gear_bullet_carries_hardtech(self):
        """'hardtech' gates Headgear only. On a Gear bullet it would be inert
        and would read as though the notac filter covered this clash."""
        for bullet in bullets_for(LIVE, "Gear"):
            self.assertNotIn("hardtech", gen.split_flags(bullet)[1])


if __name__ == "__main__":
    unittest.main()
