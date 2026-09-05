"""rawTraits: the unstripped bullet behind every trait, persisted so a later
override can put back what the stored roll already threw away.

roll_npc() strips a bullet's flag segment ('|| mil') before storing a trait,
so a manifest's "traits" is a lossy record - a stored Role has lost the 'mil'
that Faction, Outfit and Weapon filter on. npc["_raw"] keeps the whole bullet,
unstripped, for every table that was rolled or forced by an override; this
module only tests that it can be fed back in and reproduce exactly the render
it came from. That is the invariant --reroll-trait and a Theme cascade will
later be built on - this task only persists and reloads the dict, it does not
consume it.

The render rule from a raw bullet back to its trait is not a simple strip:
Hair substitutes a '{colour}' slot and appends a tail after _raw already
captured the bullet, Hair colour splits three segments of its own, and
Backdrop and Faction keep all three segments whole in traits. Re-deriving that
rule here would be a second copy of roll_npc()'s render logic that silently
rots the moment the original changes, so the round-trip test below never
compares a raw bullet against a trait directly - it feeds _raw back through
roll_npc() itself and compares the two *results*, which is the only
assertion any later consumer of _raw actually needs to hold.
"""
import random
import unittest

from test.helpers import FIXTURE_TABLES, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)

# Enough seeds to trust an absence of contradictions rather than assume one -
# see TestRoundTrip's docstring - while staying fast enough to run on every
# invocation of the suite.
SEEDS = range(200)


class TestRoundTrip(unittest.TestCase):
    """Feeding _raw back as a complete override set reproduces the roll it
    came from, trait for trait, under a different seed.

    Pinning every trait at once forces roll_npc()'s "both forced" contradiction
    guards (the Role/Outfit 'dressy' check and the Age/Build 'figure' check
    near the end of roll_npc()) to evaluate a pairing that was never actually
    contradictory - a legitimately rolled NPC cannot hold both flags at once.
    That should mean
    the guards never fire here, but the fixture is small and flag combinations
    are not evenly distributed, so many seeds are run rather than trusting the
    reasoning once. A guard firing on real output would be a genuine bug in
    this invariant, not a bug in the test.
    """

    def test_raw_traits_round_trip_through_roll_npc(self):
        for seed in SEEDS:
            npc = gen.roll_npc(TABLES, random.Random(seed), None)
            again = gen.roll_npc(
                TABLES, random.Random(seed + 1_000_000), dict(npc["_raw"]))
            for key in list(gen.REQUIRED_TABLES) + ["name"]:
                self.assertEqual(
                    again[key], npc[key],
                    "seed %d: %r did not round-trip through _raw" % (seed, key))


class TestCoverage(unittest.TestCase):
    def test_raw_covers_every_required_table_and_nothing_else(self):
        for seed in SEEDS:
            npc = gen.roll_npc(TABLES, random.Random(seed), None)
            self.assertEqual(set(npc["_raw"]), set(gen.REQUIRED_TABLES))

    def test_name_is_an_override_but_not_a_raw_trait(self):
        npc = gen.roll_npc(TABLES, random.Random(0), None)
        self.assertNotIn("name", npc["_raw"])


class TestWhatTheWriterStores(unittest.TestCase):
    """Builds the two dicts with the same expressions the fresh-roll and
    regen writers use for "traits" and "rawTraits", rather than extracting a
    helper out of either manifest literal just to make it unit-testable - the
    literal has exactly one caller. This covers that every stored trait has a
    raw bullet behind it; the writers' own lines - the manifest dict literal
    in main()'s per-NPC roll loop, and the equivalent lines in
    regenerate_one() - are otherwise exercised end-to-end only, by hand or by
    a CLI-level test (see test_reroll_trait.py's TestTheCascadeReport and its
    neighbours).
    """

    def test_every_stored_trait_except_name_is_a_key_of_raw(self):
        for seed in SEEDS:
            npc = gen.roll_npc(TABLES, random.Random(seed), None)
            traits = {k: v for k, v in npc.items() if not k.startswith("_")}
            raw = dict(npc["_raw"])
            for key in traits:
                if key == "name":
                    continue
                self.assertIn(
                    key, raw, "seed %d: %r missing from rawTraits" % (seed, key))
