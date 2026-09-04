"""Re-rolling one trait of an already-rolled NPC, and refusing the rest.

The manifest is a lossy record of a roll: roll_npc() strips a bullet's flags
before storing it, so an entry carries "a colonial administrator" rather than
"a colonial administrator || mil". A trait whose filters need another trait's
flags therefore cannot be re-rolled correctly from an entry, and is refused
with the reason rather than silently producing a contradiction - a civilian in
a service uniform, or hands in pockets around a rifle.

What makes the refusals worth testing at all is that they are the feature. The
easy implementation re-rolls anything and is wrong roughly as often as the
flags matter.
"""
import random
import unittest

from test.helpers import FIXTURE_TABLES, REPO, bullets_for, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")


def npc_for(seed=0):
    return gen.roll_npc(TABLES, random.Random(seed), None)


class TestWhatIsRerollable(unittest.TestCase):
    def test_every_rerollable_trait_is_a_real_table(self):
        for name in gen.REROLLABLE_TRAITS:
            self.assertIn(name, gen.REQUIRED_TABLES,
                          "%r is not a table the script rolls" % name)

    def test_every_required_table_is_either_rerollable_or_explained(self):
        """No table may fall through both lists.

        A table added to REQUIRED_TABLES later would otherwise be refused with
        the generic "not a trait this script rolls", which is both wrong and
        unhelpful. This is the check that makes someone decide.
        """
        for name in gen.REQUIRED_TABLES:
            self.assertTrue(
                name in gen.REROLLABLE_TRAITS or name in gen.UNREROLLABLE_REASONS,
                "%r is neither re-rollable nor given a reason it is not" % name)

    def test_the_two_lists_do_not_overlap(self):
        overlap = set(gen.REROLLABLE_TRAITS) & set(gen.UNREROLLABLE_REASONS)
        self.assertEqual(overlap, set())

    def test_the_traits_whose_gates_need_stripped_flags_are_refused(self):
        """The specific point of the split, named one by one so a later edit
        that quietly adds one of these has to argue with a test."""
        for name in ("Outfit", "Weapon", "Gear", "Stance", "Faction", "Age", "Role"):
            self.assertIn(name, gen.UNREROLLABLE_REASONS)
            self.assertNotIn(name, gen.REROLLABLE_TRAITS)

    def test_refusing_names_the_trait_and_the_reason(self):
        npc = npc_for()
        with self.assertRaises(SystemExit) as caught:
            gen.reroll_trait(TABLES, npc, "Outfit", random.Random(0))
        message = str(caught.exception)
        self.assertIn("Outfit", message)
        self.assertIn("mil", message)
        self.assertIn("Hair", message, "the message should list what IS re-rollable")

    def test_an_unknown_table_is_refused_too(self):
        npc = npc_for()
        with self.assertRaises(SystemExit):
            gen.reroll_trait(TABLES, npc, "Not A Table", random.Random(0))


class TestRerolling(unittest.TestCase):
    def test_nothing_but_the_named_trait_changes(self):
        """Asserted as "nothing else moved", not as "Eyes moved".

        A re-roll draws from the whole table and may legitimately land on the
        value it already had - which is a property of a re-roll, not a bug, and
        asserting the trait always changes would make this test fail on a small
        table for the wrong reason. That it CAN change is a separate test.
        """
        npc = npc_for()
        before = dict(npc)
        gen.reroll_trait(TABLES, npc, "Eyes", random.Random(3))
        changed = [k for k in before if npc[k] != before[k]]
        self.assertTrue(set(changed) <= {"Eyes"},
                        "re-rolling Eyes also moved %s" % (set(changed) - {"Eyes"}))

    def test_a_reroll_can_actually_change_the_trait(self):
        """The counterpart to the above: a no-op that never changed anything
        would pass every other test in this class."""
        npc = npc_for()
        original = npc["Eyes"]
        moved = any(
            gen.reroll_trait(TABLES, dict(npc), "Eyes", random.Random(seed)) != original
            for seed in range(60))
        self.assertTrue(moved, "no seed produced a different Eyes value")

    def test_the_new_value_comes_from_the_table(self):
        npc = npc_for()
        gen.reroll_trait(TABLES, npc, "Eyes", random.Random(3))
        self.assertIn(npc["Eyes"], bullets_for(TABLES, "Eyes"))

    def test_it_is_repeatable_for_one_seed(self):
        """The GUI hands the entry's own seed back, so the same reroll of the
        same NPC has to produce the same answer rather than drifting."""
        a, b = npc_for(), npc_for()
        gen.reroll_trait(TABLES, a, "Eyes", random.Random(11))
        gen.reroll_trait(TABLES, b, "Eyes", random.Random(11))
        self.assertEqual(a["Eyes"], b["Eyes"])

    def test_no_flag_segment_survives_into_the_value(self):
        npc = npc_for()
        for _ in range(30):
            gen.reroll_trait(TABLES, npc, "Headgear", random.Random(_))
            self.assertNotIn("||", npc["Headgear"])

    def test_pronoun_placeholders_are_substituted(self):
        npc = npc_for()
        for seed in range(40):
            gen.reroll_trait(TABLES, npc, "Build", random.Random(seed))
            self.assertNotIn("{", npc["Build"])


class TestHairKeepsItsColour(unittest.TestCase):
    """Hair is the trait this was asked for, and the fiddly one.

    roll_npc() substitutes the colour into the cut and appends the colour's
    trailing clause to the whole phrase, storing only the bare base under
    'Hair colour'. A new cut therefore has to be re-filled from the stored
    base, and the tail recovered from the table by that base - otherwise
    re-rolling someone's haircut silently changes their hair colour, or drops
    a gradient they had.
    """

    def test_the_new_cut_carries_the_stored_colour(self):
        npc = npc_for()
        colour = npc["Hair colour"]
        for seed in range(30):
            gen.reroll_trait(TABLES, npc, "Hair", random.Random(seed))
            self.assertIn(colour, npc["Hair"])
            self.assertEqual(npc["Hair colour"], colour, "the colour must not move")

    def test_no_colour_slot_is_left_unfilled(self):
        npc = npc_for()
        for seed in range(30):
            gen.reroll_trait(TABLES, npc, "Hair", random.Random(seed))
            self.assertNotIn("{colour}", npc["Hair"])

    def test_a_gradient_tail_is_recovered_rather_than_dropped(self):
        gradients = [b for b in bullets_for(LIVE, "Hair colour")
                     if gen.split_hair_colour(b)[1]]
        self.assertTrue(gradients, "the live table should carry a gradient")
        base, tail, _ = gen.split_hair_colour(gradients[0])
        self.assertEqual(gen.hair_colour_tail(LIVE, "she", base), tail)

    def test_a_flat_colour_recovers_no_tail(self):
        self.assertEqual(gen.hair_colour_tail(LIVE, "she", "black"), "")

    def test_an_unknown_colour_recovers_no_tail(self):
        """A stored colour the table no longer carries must not raise - the
        tables file is edited freely and an old entry can name a deleted
        shade."""
        self.assertEqual(gen.hair_colour_tail(LIVE, "she", "not a colour"), "")


class TestGatesThatDoRebuild(unittest.TestCase):
    def test_a_young_npc_never_rerolls_into_a_figure_build(self):
        """'young' is the one flag the manifest already stores separately, so
        this filter genuinely rebuilds."""
        npc = npc_for()
        npc["_young"] = True
        figures = {gen.split_flags(b)[0] for b in bullets_for(TABLES, "Build")
                   if "figure" in gen.split_flags(b)[1]}
        if not figures:
            self.skipTest("fixture has no 'figure' build to avoid")
        for seed in range(60):
            gen.reroll_trait(TABLES, npc, "Build", random.Random(seed))
            self.assertNotIn(npc["Build"], figures)

    def test_a_scene_placement_never_rerolls_onto_an_unlit_backdrop(self):
        """The stored Backdrop keeps its scene segment, so this one rebuilds too."""
        scene = {gen.split_flags(b)[0]
                 for b in bullets_for(TABLES, "Glow placement")
                 if "scene" in gen.split_flags(b)[1]}
        self.assertTrue(scene, "fixture needs a 'scene' placement")
        checked = 0
        for seed in range(200):
            npc = npc_for(seed)
            if gen.has_light_source(gen.split_backdrop(npc["Backdrop"])[1]):
                continue
            checked += 1
            gen.reroll_trait(TABLES, npc, "Glow placement", random.Random(seed))
            # Compare on the unrendered form: the value has had its pronouns
            # substituted, so strip back to what the flag set contains.
            self.assertFalse(
                any(npc["Glow placement"].startswith(s.split("{")[0]) for s in scene),
                "seed %d: re-rolled a 'scene' placement onto an unlit backdrop" % seed)
        self.assertTrue(checked, "no unlit backdrop was rolled; the test checked nothing")


if __name__ == "__main__":
    unittest.main()
