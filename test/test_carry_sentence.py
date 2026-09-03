"""The one sentence that renders both the Weapon and the Gear.

Only the Weapon side has a weighted empty entry - the live `## Gear` table has
none - so a full roll can reach "both" (normal) and "gear only" (the empty
Weapon entry rolled), but never "weapon only" or "neither": both would need an
empty Gear, and a 'nogear' Backdrop does not produce one either - it never
calls carry_sentence() with an empty weapon, it blanks the portrait's whole
sentence at the render site instead (see TestNogear below). "Weapon only" and
"neither" are unit cases rather than something a full roll reaches; they are
still worth pinning directly, including the spacing and punctuation an
omitted slot invites.
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
    """A 'nogear' backdrop already put something in the subject's hands.

    Three effects, pinned here: the portrait drops the WHOLE merged carry
    sentence, weapon and gear alike, because the scene contradicts anything
    held in a hand; the token keeps it in full, since the token has no scene
    at all - just flat white and a Stance - for anything to contradict; and,
    at roll time (reaching both prompts), Gear is restricted to bullets that
    leave the hands free, the same 'notac' civ-only narrowing the loop's own
    Gear roll applies included.
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

    def test_notac_still_screens_mil_gear_after_a_nogear_reroll(self):
        # The nogear re-roll rebuilds its own Gear pool from scratch, so it
        # can silently walk back onto ground the loop's own 'notac' filter
        # (see roll_npc()'s Gear branch) already screened out - exactly the
        # "kimono carrying a tactical assault pack" pairing that filter
        # exists to stop.
        notac_outfit = next(
            b for b in self.tables["Outfit"]
            if "notac" in gen.split_flags(b)[1])
        mil_gear = {gen.split_flags(b)[0]
                    for b in gen.variant_table(self.tables, "Gear", "she")
                    if "mil" in gen.split_flags(b)[1]}
        self.assertTrue(mil_gear, "fixture Gear has no mil bullet")
        for seed in range(100):
            npc = gen.roll_npc(
                self.tables, self.random.Random(seed),
                {"Backdrop": self.nogear, "Outfit": notac_outfit})
            self.assertNotIn(
                npc["Gear"], mil_gear,
                "seed %d: a notac outfit's nogear re-roll still landed on "
                "military-issue gear" % seed)


if __name__ == "__main__":
    unittest.main()
