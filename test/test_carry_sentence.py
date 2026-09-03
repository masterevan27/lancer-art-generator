"""The one sentence that renders both the Weapon and the Gear.

All four combinations are reachable in real rolls - the weighted empty Weapon
entry and the 'nogear' Backdrop both produce the no-weapon rows - so all four
are pinned here, including the spacing and punctuation an omitted slot invites.
"""
import unittest

from test.helpers import load_generator

gen = load_generator()

FIELDS = {"Subject": "She", "carry": "carries"}


class TestCarrySentence(unittest.TestCase):
    def test_both(self):
        self.assertEqual(
            gen.carry_sentence(FIELDS, "a katana", "a data-slate"),
            "She carries a katana and a data-slate. ")

    def test_weapon_only(self):
        self.assertEqual(
            gen.carry_sentence(FIELDS, "a katana", ""),
            "She carries a katana. ")

    def test_gear_only(self):
        self.assertEqual(
            gen.carry_sentence(FIELDS, "", "a data-slate"),
            "She carries a data-slate. ")

    def test_neither_renders_nothing(self):
        self.assertEqual(gen.carry_sentence(FIELDS, "", ""), "")

    def test_no_prompt_ever_shows_a_doubled_space_or_stray_and(self):
        import random
        from test.helpers import FIXTURE_TABLES
        tables = gen.parse_tables(FIXTURE_TABLES)
        for seed in range(200):
            npc = gen.roll_npc(tables, random.Random(seed))
            for text in gen.build_prompts(npc):
                self.assertNotIn("  ", text, "seed %d: doubled space" % seed)
                self.assertNotIn("carries  ", text)
                self.assertNotIn("carries and", text)
                self.assertNotIn(" . ", text, "seed %d: orphaned period" % seed)


class TestNogear(unittest.TestCase):
    """A 'nogear' backdrop already put a weapon in the subject's hands.

    Its two effects are deliberately asymmetric, so both are pinned: the
    portrait drops the weapon because the scene contradicts it, the token keeps
    it because the token has no scene at all - just flat white and a Stance.
    """

    def setUp(self):
        import random
        from test.helpers import FIXTURE_TABLES
        self.random = random
        self.tables = gen.parse_tables(FIXTURE_TABLES)
        self.nogear = next(
            b for b in self.tables["Backdrop"]
            if "nogear" in gen.split_backdrop(b)[2])

    def _roll(self, seed):
        return gen.roll_npc(self.tables, self.random.Random(seed),
                            {"Backdrop": self.nogear})

    def test_the_portrait_omits_an_armed_npcs_weapon(self):
        # Pins the whole-sentence suppression, not just the weapon half: the
        # spec settles this the other way from a looser earlier draft - the
        # scene already put something in the subject's hands, so the equipment
        # is dropped right along with the weapon rather than surviving it.
        for seed in range(100):
            npc = self._roll(seed)
            portrait, _ = gen.build_prompts(npc)
            if npc["Weapon"]:
                self.assertNotIn(
                    npc["Weapon"], portrait,
                    "seed %d: a nogear scene still named the weapon" % seed)
            if npc["Gear"]:
                self.assertNotIn(
                    npc["Gear"], portrait,
                    "seed %d: a nogear scene still named the gear" % seed)

    def test_the_token_still_names_it(self):
        for seed in range(100):
            npc = self._roll(seed)
            if not npc["Weapon"]:
                continue
            _, token = gen.build_prompts(npc)
            self.assertIn(
                npc["Weapon"], token,
                "seed %d: the token dropped the weapon, but it has no scene "
                "to contradict it" % seed)
            return
        self.fail("no armed NPC in 100 rolls - the check asserted nothing")

    def test_no_hands_gear_survives_a_nogear_scene(self):
        held = {gen.split_flags(b)[0]
                for b in gen.variant_table(self.tables, "Gear", "she")
                if "hands" in gen.split_flags(b)[1]}
        self.assertTrue(held, "fixture Gear has no hands bullet")
        for seed in range(100):
            self.assertNotIn(
                self._roll(seed)["Gear"], held,
                "seed %d: a nogear scene left hands-occupying gear" % seed)


if __name__ == "__main__":
    unittest.main()
