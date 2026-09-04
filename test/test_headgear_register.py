"""An Outfit flagged 'notac' does not pair with 'hardtech' Headgear.

A rolled corporate liaison came out in an elaborate floral kimono with a sealed
flight helmet over it - dressed for a reception from the neck down and for a
cockpit from the neck up. 'notac' already means "do not pair this with tactical
gear" and already gates Weapon and Gear; it had simply never reached the third
thing an NPC wears.

'hardtech' is deliberately not 'mil'. Half the clash is technical rather than
military - a cybernetic ear implant and a mechanical diagnostic rig fight a
kimono and neither is army kit - and Headgear is not in filter_by_mil().

See docs/superpowers/specs/2026-09-04-headgear-outfit-register-design.md.
"""
import contextlib
import io
import random
import sys
import unittest

from test.helpers import (
    FIXTURE_TABLES, REPO, bullets_for, load_generator, rendered)

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")

KIMONO = "an elaborate floral kimono || civ notac dressy"


def roll(seed, **overrides):
    return gen.roll_npc(TABLES, random.Random(seed), overrides or None)


@contextlib.contextmanager
def _quiet_stderr():
    """Capture the generator's warnings instead of printing them mid-suite.

    reroll_trait() reports a missing outfit register on stderr, which is the
    behaviour under test in one case and noise in the others.
    """
    captured, before = io.StringIO(), sys.stderr
    sys.stderr = captured
    try:
        yield captured
    finally:
        sys.stderr = before


def hardtech_headgear(tables):
    """Every string a 'hardtech' bullet can appear as in a rolled NPC.

    Headgear bullets are full sentences carrying '{Subject}' and '{wear}', and
    roll_npc() substitutes those before storing the value - so comparing a
    rolled Headgear against the raw bullet never matches. rendered() expands
    the source side across every pronoun set, which is what makes the
    comparisons below plain set membership.
    """
    out = set()
    for bullet in bullets_for(tables, "Headgear"):
        if "hardtech" in gen.split_flags(bullet)[1]:
            out |= rendered(tables, "Headgear", bullet)
    return out


class TestTheFilter(unittest.TestCase):
    def test_it_drops_only_the_hardtech_ones(self):
        options = ["bare-headed.", "a helmet. || hardtech", "a straw hat. || @alpha"]
        self.assertEqual(
            gen.filter_by_hardtech(options, True),
            ["bare-headed.", "a straw hat. || @alpha"])

    def test_an_untac_outfit_filters_nothing(self):
        options = ["bare-headed.", "a helmet. || hardtech"]
        self.assertEqual(gen.filter_by_hardtech(options, False), options)

    def test_the_pool_is_never_filtered_to_nothing(self):
        """The starvation guard. It cannot fire on today's content - no
        Headgear bullet carries a theme tag, so filter_by_theme() never narrows
        this pool first - but Phase 4 will change that."""
        options = ["a helmet. || hardtech", "a visor rig. || hardtech"]
        self.assertEqual(gen.filter_by_hardtech(options, True), options)


class TestTheRollIsGated(unittest.TestCase):
    def test_a_notac_outfit_never_rolls_hardtech_headgear(self):
        hardtech = hardtech_headgear(TABLES)
        self.assertTrue(hardtech, "fixture needs a hardtech bullet to avoid")
        for seed in range(400):
            npc = roll(seed, Outfit=KIMONO)
            self.assertNotIn(
                npc["Headgear"], hardtech,
                "seed %d: a kimono rolled hard tech on its head" % seed)

    def test_an_ordinary_outfit_still_reaches_hardtech_headgear(self):
        """The other half of the gate. Filtering it for everyone would pass the
        test above while making 39 live bullets dead content."""
        hardtech = hardtech_headgear(TABLES)
        reached = 0
        for seed in range(400):
            npc = roll(seed, Outfit="grey coveralls")
            if npc["Headgear"] in hardtech:
                reached += 1
        self.assertTrue(reached, "no ordinary outfit ever reached hard tech")

    def test_a_gated_roll_still_has_somewhere_to_go(self):
        """Variety, not just legality: a kimono must reach more than one
        headgear, or the gate has replaced a clash with a uniform."""
        seen = {roll(seed, Outfit=KIMONO)["Headgear"] for seed in range(400)}
        self.assertGreater(len(seen), 1)

    def test_the_flag_never_reaches_a_prompt(self):
        for seed in range(200):
            npc = roll(seed)
            self.assertNotIn("hardtech", npc["Headgear"])
            for prompt in gen.build_prompts(npc):
                self.assertNotIn("hardtech", prompt)


class TestTheLiveTable(unittest.TestCase):
    def test_a_notac_outfit_keeps_a_varied_live_pool(self):
        """The live numbers the spec commits to, asserted as floors rather than
        equalities so adding a bullet does not fail the suite."""
        pool = [b for b in bullets_for(LIVE, "Headgear")
                if "hardtech" not in gen.split_flags(b)[1]]
        self.assertGreaterEqual(len(pool), 25)

    def test_the_traditional_register_survives_the_gate(self):
        """The point of gating on 'notac' rather than banning headgear: a
        kimono should still reach a kabuto."""
        pool = " ".join(b for b in bullets_for(LIVE, "Headgear")
                        if "hardtech" not in gen.split_flags(b)[1])
        for wanted in ("kabuto", "lacquered", "straw hat"):
            self.assertIn(wanted, pool)

    def test_every_sealed_helmet_is_flagged(self):
        """A spot-check on the classification itself. These four are the least
        arguable members of the set; if one is unflagged, the table edit was
        incomplete."""
        hardtech = " ".join(b for b in bullets_for(LIVE, "Headgear")
                            if "hardtech" in gen.split_flags(b)[1])
        for wanted in ("full flight helmet", "night-vision helmet",
                       "sealed tactical helmet", "respirator mask"):
            self.assertIn(wanted, hardtech)

    def test_no_headgear_bullet_carries_civ_or_mil(self):
        """Headgear is not in filter_by_mil(), so those flags would be inert
        and misleading. The spec rejects them by name."""
        for bullet in bullets_for(LIVE, "Headgear"):
            flags = gen.split_flags(bullet)[1]
            self.assertNotIn("civ", flags)
            self.assertNotIn("mil", flags)


class TestTheRegisterIsRecorded(unittest.TestCase):
    def test_a_roll_records_the_outfits_register(self):
        self.assertTrue(roll(0, Outfit=KIMONO)["_outfit_notac"])
        self.assertFalse(roll(0, Outfit="grey coveralls")["_outfit_notac"])

    def test_headgear_is_still_rerollable(self):
        """The whole reason the key exists. Gating a trait on another trait's
        flag is exactly what puts it in UNREROLLABLE_REASONS, and the import
        GUI builds its Re-roll buttons from this tuple."""
        self.assertIn("Headgear", gen.REROLLABLE_TRAITS)
        self.assertNotIn("Headgear", gen.UNREROLLABLE_REASONS)


class TestTheRerollRespectsIt(unittest.TestCase):
    def _entry_npc(self, register):
        """A stored entry with a recorded register and no raw bullets.

        '_outfit_notac' is the manifest key that exists *because* the entry is
        a lossy record of the roll, so the cases below are all about the entry
        shape that has one - written before rawTraits existed. Dropping _raw
        is what makes it that shape: reroll_trait() prefers raw bullets when
        they are there, and a raw re-roll reads the pinned Outfit's own
        'notac' flag and never consults this key at all, so leaving _raw in
        would quietly turn every case here into a test of the other path.
        """
        npc = roll(0, Outfit=KIMONO)
        npc.pop("_raw")
        npc["_outfit_notac"] = register
        return npc

    def test_a_recorded_notac_outfit_never_rerolls_into_hardtech(self):
        hardtech = hardtech_headgear(TABLES)
        npc = self._entry_npc(True)
        for seed in range(200):
            value = gen.reroll_trait(TABLES, npc, "Headgear", random.Random(seed))
            self.assertNotIn(value, hardtech, "seed %d" % seed)

    def test_a_recorded_plain_outfit_still_reaches_hardtech(self):
        hardtech = hardtech_headgear(TABLES)
        npc = self._entry_npc(False)
        reached = sum(
            gen.reroll_trait(TABLES, npc, "Headgear", random.Random(seed)) in hardtech
            for seed in range(200))
        self.assertTrue(reached)

    def test_an_entry_predating_the_key_rerolls_unrestricted(self):
        """None is 'not recorded', which is not the same as False. It must
        behave as it did before this change rather than silently claiming the
        outfit was plain."""
        hardtech = hardtech_headgear(TABLES)
        npc = self._entry_npc(None)
        with _quiet_stderr():
            reached = sum(
                gen.reroll_trait(TABLES, npc, "Headgear", random.Random(seed)) in hardtech
                for seed in range(200))
        self.assertTrue(reached)

    def test_an_entry_predating_the_key_says_so(self):
        npc = self._entry_npc(None)
        with _quiet_stderr() as err:
            gen.reroll_trait(TABLES, npc, "Headgear", random.Random(0))
        self.assertIn("no recorded outfit register", err.getvalue())

    def test_a_recorded_register_warns_about_nothing(self):
        npc = self._entry_npc(True)
        with _quiet_stderr() as err:
            gen.reroll_trait(TABLES, npc, "Headgear", random.Random(0))
        self.assertEqual(err.getvalue(), "")

    def test_rerolling_something_else_is_unaffected(self):
        npc = self._entry_npc(True)
        before = dict(npc)
        gen.reroll_trait(TABLES, npc, "Eyes", random.Random(0))
        self.assertEqual(npc["Headgear"], before["Headgear"])


if __name__ == "__main__":
    unittest.main()
