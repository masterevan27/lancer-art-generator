"""Pinning one trait of an already-rolled NPC to a chosen value.

The question this file is really about is "which values could this trait
take", and the answer has to come from roll_npc()'s own pool or it is not an
answer at all - a second filter chain written out here would agree with the
roller on the day it was written and drift from it silently afterwards. So
roll_npc() records the pool it already computes, and everything below reads
that recording.

The recording has to be inert, which is the first class here and the one the
rest depends on: a probed roll and an unprobed roll at the same seed are the
same NPC. If that ever stops being true, every legality answer in this file is
being computed against a roll that never happened.
"""
import random
import unittest

from test.helpers import FIXTURE_TABLES, REPO, load_generator

gen = load_generator()

TABLES = gen.parse_tables(FIXTURE_TABLES)
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")


class ProbeIsInert(unittest.TestCase):
    def test_a_probed_roll_is_the_same_npc_as_an_unprobed_one(self):
        for seed in range(25):
            with self.subTest(seed=seed):
                plain = gen.roll_npc(LIVE, random.Random(seed), None)
                probed = gen.roll_npc(LIVE, random.Random(seed), None, probe={})
                self.assertEqual(plain, probed)

    def test_the_probe_is_untouched_when_none_is_passed(self):
        # The default has to stay None rather than {}, or every caller shares
        # one dict and the pools accumulate across rolls.
        self.assertIsNone(
            gen.roll_npc.__defaults__[-1],
            "roll_npc's probe default must be None, not a shared dict")


class ProbeCoversTheTables(unittest.TestCase):
    def test_every_required_table_but_pronouns_is_recorded(self):
        probe = {}
        gen.roll_npc(LIVE, random.Random(3), None, probe=probe)
        missing = [t for t in gen.REQUIRED_TABLES
                   if t != "Pronouns" and t not in probe]
        self.assertEqual(missing, [], "unrecorded tables have no legal values")

    def test_every_recorded_pool_is_non_empty(self):
        probe = {}
        gen.roll_npc(LIVE, random.Random(4), None, probe=probe)
        empty = sorted(t for t, pool in probe.items() if not pool)
        self.assertEqual(empty, [])

    def test_the_rolled_value_is_in_its_own_recorded_pool(self):
        # The pool is what the draw came from, so this is the tightest
        # statement that the record is of the right list.
        for seed in range(10):
            probe = {}
            npc = gen.roll_npc(LIVE, random.Random(seed), None, probe=probe)
            for table, pool in probe.items():
                with self.subTest(seed=seed, table=table):
                    self.assertIn(npc["_raw"][table], pool)


if __name__ == "__main__":
    unittest.main()
