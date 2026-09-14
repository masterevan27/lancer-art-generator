"""Headgear flagged 'mil' is uniform, and a civilian Role never wears it.

Headgear joined filter_by_mil() for the handful of bullets that are part of an
issued uniform - a stiff peaked officer's cap on a dockworker reads as costume.
Rolls the live tables rather than a fixture, because the bullet under test is a
live one and the claim is about the real Role table's 'mil' flags.
"""
import contextlib
import copy
import io
import random
import unittest

from test.helpers import REPO, bullets_for, load_generator

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")

CAP = "peaked officer's cap"
MIL_ROLES = {gen.split_flags(b)[0] for b in bullets_for(LIVE, "Role")
             if "mil" in gen.split_flags(b)[1]}


class TestTheOfficersCap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rolls = [gen.roll_npc(LIVE, random.Random(seed))
                     for seed in range(3000)]

    def test_every_officers_cap_is_flagged_mil(self):
        caps = [b for b in bullets_for(LIVE, "Headgear") if CAP in b]
        self.assertTrue(caps, "no officer's cap bullet left - reworded?")
        for cap in caps:
            self.assertIn("mil", gen.split_flags(cap)[1], cap)

    def test_the_cap_is_reachable_by_the_military(self):
        """Without this the assertion below passes on nothing."""
        self.assertTrue(any(CAP in n["Headgear"] for n in self.rolls
                            if n["Role"] in MIL_ROLES))

    def test_no_civilian_wears_the_cap(self):
        for npc in self.rolls:
            if CAP in npc["Headgear"]:
                self.assertIn(npc["Role"], MIL_ROLES,
                              "%r wears the officer's cap" % npc["Role"])

    def test_a_legacy_headgear_re_roll_keeps_it_off_civilians(self):
        """The no-raw-bullets path reads the stored Role's 'mil' flag back off
        the Role table, since the stored Role has had it stripped."""
        civilians = [n for n in self.rolls if n["Role"] not in MIL_ROLES][:30]
        soldiers = [n for n in self.rolls if n["Role"] in MIL_ROLES][:30]
        worn_by_soldier = False
        with contextlib.redirect_stderr(io.StringIO()):
            for group, is_mil in ((civilians, False), (soldiers, True)):
                for seed, npc in enumerate(group):
                    npc = copy.deepcopy(npc)
                    npc.pop("_raw", None)
                    for i in range(30):
                        gen.reroll_trait(LIVE, npc, "Headgear",
                                         random.Random(seed * 1000 + i))
                        if not is_mil:
                            self.assertNotIn(CAP, npc["Headgear"])
                        elif CAP in npc["Headgear"]:
                            worn_by_soldier = True
        self.assertTrue(worn_by_soldier,
                        "the legacy path never gave a soldier the cap, so the "
                        "civilian half of this test proves little")


if __name__ == "__main__":
    unittest.main()
