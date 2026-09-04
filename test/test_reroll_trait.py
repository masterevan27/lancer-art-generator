"""Re-rolling one trait of an already-rolled NPC, and refusing the rest.

There are two paths, and this module tests both.

An entry written before rawTraits existed is a lossy record of its roll:
roll_npc() strips a bullet's flags before storing it, so the entry carries "a
colonial administrator" rather than "a colonial administrator || mil". A trait
whose filters need another trait's flags therefore cannot be re-rolled
correctly from it, and is refused with the reason rather than silently
producing a contradiction - a civilian in a service uniform, or hands in
pockets around a rifle. What makes those refusals worth testing at all is that
they are the feature. The easy implementation re-rolls anything and is wrong
roughly as often as the flags matter.

An entry that recorded its raw bullets has no such problem, and re-rolls
almost anything: reroll_from_raw() pins every other bullet back into a fresh
roll_npc() with its flags intact, so the filters are the roller's own rather
than a second copy written out here. What is worth testing on that path is
the opposite of the refusals - that the filters really do rebuild, that
nothing but the named trait moves, and that npc["_raw"] still describes the
NPC afterwards rather than the one it replaced.
"""
import random
import unittest

from test.helpers import (FIXTURE_TABLES, REPO, bullets_for, load_generator,
                          rendered)
# The definition of "occupies a hand" belongs to the module that already owns
# it - a second one here would be a second thing to keep in step with the
# tables file, and the flag it reads is the whole subject of that module.
from test.test_hands import texts_with_hands

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")


def npc_for(seed=0):
    """A stored entry that recorded no raw bullets - the legacy shape.

    Every case built on this one is about the hand-written filter rebuilds,
    which are what an entry written before rawTraits existed still gets.
    roll_npc() now publishes npc["_raw"] on every roll and reroll_trait()
    prefers it, so a plain roll handed to reroll_trait() would take the pinned
    path instead and none of these cases would cover what they were written
    for. raw_npc_for() below is the fixture for that path.
    """
    npc = gen.roll_npc(TABLES, random.Random(seed), None)
    npc.pop("_raw")
    return npc


def raw_npc_for(seed=0):
    """A stored entry that recorded its raw bullets, loaded back.

    regenerate_one() puts entry["rawTraits"] back under npc["_raw"], which is
    the key roll_npc() already published it under - so a fresh roll is that
    entry, with no round trip through JSON needed to make the shape honest.
    """
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


class TestWhatIsRerollableFromRaw(unittest.TestCase):
    def test_every_raw_rerollable_trait_is_a_real_table(self):
        for name in gen.RAW_REROLLABLE_TRAITS:
            self.assertIn(name, gen.REQUIRED_TABLES,
                          "%r is not a table the script rolls" % name)

    def test_every_required_table_is_either_raw_rerollable_or_explained(self):
        """The same check the legacy set gets, for the same reason: a table
        added to REQUIRED_TABLES must land in one list or the other rather
        than falling through to "not a trait this script rolls"."""
        for name in gen.REQUIRED_TABLES:
            self.assertTrue(
                name in gen.RAW_REROLLABLE_TRAITS or name in gen.UNREROLLABLE_REASONS,
                "%r is neither re-rollable from raw nor given a reason it is not"
                % name)

    def test_it_refuses_only_what_raw_bullets_cannot_help_with(self):
        """Named one by one, so widening this set later has to argue with a
        test - each of the four is refused for a reason that survives having
        the bullets: two are the name the folder and manifest id derive from,
        one takes the name with it, and one needs a cascade rather than a
        re-roll in place."""
        refused = set(gen.REQUIRED_TABLES) - set(gen.RAW_REROLLABLE_TRAITS)
        self.assertEqual(
            refused, {"Given names", "Family names", "Pronouns", "Theme"})
        for name in refused:
            self.assertIn(name, gen.UNREROLLABLE_REASONS)

    def test_it_is_strictly_wider_than_the_legacy_set(self):
        """The point of the whole change. Anything the lossy path can re-roll
        the raw path can too, and then ten more."""
        self.assertTrue(
            set(gen.REROLLABLE_TRAITS) < set(gen.RAW_REROLLABLE_TRAITS))

    def test_theme_is_still_refused_on_both_paths(self):
        """Theme is the deliberate seam with the cascade that comes next: it
        gates seven appearance tables, so it is not a one-free-variable
        re-roll and raw bullets do not make it one."""
        for npc in (npc_for(), raw_npc_for()):
            with self.assertRaises(SystemExit) as caught:
                gen.reroll_trait(TABLES, npc, "Theme", random.Random(0))
            self.assertIn("seven appearance tables", str(caught.exception))

    def test_the_refusal_names_the_set_that_applies(self):
        """An entry with raw bullets and one without offer different sets, and
        printing the shorter one to the owner of the longer would be a lie
        about their own NPC."""
        messages = {}
        for label, npc in (("legacy", npc_for()), ("raw", raw_npc_for())):
            with self.assertRaises(SystemExit) as caught:
                gen.reroll_trait(TABLES, npc, "Pronouns", random.Random(0))
            messages[label] = str(caught.exception)
        self.assertIn("Stance", messages["raw"],
                      "an entry with raw bullets can re-roll Stance")
        self.assertNotIn("Stance", messages["legacy"],
                         "an entry without them cannot, and must not be told it can")

    def test_an_unknown_table_is_refused_on_the_raw_path_too(self):
        with self.assertRaises(SystemExit):
            gen.reroll_trait(TABLES, raw_npc_for(), "Not A Table", random.Random(0))


class TestRerollingFromRaw(unittest.TestCase):
    """The pinned path: a fresh roll with one free variable.

    Every case here sweeps the whole re-rollable set rather than one favourite
    trait, because the point of the path is that it is generic - a trait that
    needed a hand-written branch before now goes through the same three lines
    as every other, and a sweep is what notices when one of them doesn't.
    """

    SEEDS = range(12)

    def test_a_trait_the_lossy_path_refuses_now_rerolls(self):
        self.assertNotIn("Outfit", gen.REROLLABLE_TRAITS)
        outfits = {text for b in bullets_for(TABLES, "Outfit")
                   for text in rendered(TABLES, "Outfit", b)}
        npc = raw_npc_for()
        value = gen.reroll_trait(TABLES, npc, "Outfit", random.Random(4))
        self.assertIn(value, outfits)
        self.assertEqual(value, npc["Outfit"], "the return value is the new trait")

    def test_only_the_named_trait_moves(self):
        """Every other trait byte-identical, the name included.

        'name' is asserted rather than pinned: roll_npc() rebuilds it from the
        Given names and Family names this pins, so a re-roll that changed it
        would mean the pinning had failed rather than that the name needs
        handling of its own.

        Hair is the one legitimate second mover, and only when Hair colour is
        the target: the colour is substituted into the cut and its tail
        appended to the whole phrase, so one raw bullet renders into two
        traits. That is the same coupling the lossy path refuses Hair colour
        over - here it resolves correctly instead of being refused.
        """
        moved = 0
        for name in gen.RAW_REROLLABLE_TRAITS:
            allowed = {name} | ({"Hair"} if name == "Hair colour" else set())
            for seed in self.SEEDS:
                npc = raw_npc_for(seed)
                before = {k: npc[k] for k in list(gen.REQUIRED_TABLES) + ["name"]}
                gen.reroll_trait(TABLES, npc, name, random.Random(seed + 500))
                changed = {k for k in before if npc[k] != before[k]}
                self.assertTrue(
                    changed <= allowed,
                    "seed %d: re-rolling %s also moved %s"
                    % (seed, name, sorted(changed - allowed)))
                moved += name in changed
        # A re-roll may legitimately land on the value it already had, so no
        # single case can assert the target changed - but across the whole
        # sweep a path that changed nothing at all would pass every assertion
        # above while doing nothing.
        self.assertTrue(moved, "no re-roll in the sweep changed its target")

    def test_the_rerolled_npc_still_builds_its_prompts(self):
        """The copy-back replaces the dict wholesale, so everything
        build_prompts() reads beside the traits - '_pronouns', '_young', the
        name - has to come back with it. regenerate_one() renders straight
        after the re-roll, and the failure mode this catches is a KeyError in
        the middle of that rather than a wrong word in a prompt.
        """
        npc = raw_npc_for()
        gen.reroll_trait(TABLES, npc, "Backdrop", random.Random(5))
        portrait, token = gen.build_prompts(npc)
        self.assertTrue(npc["name"])
        self.assertNotIn("{", portrait)
        self.assertNotIn("{", token)

    def test_it_is_repeatable_for_one_seed(self):
        a, b = raw_npc_for(), raw_npc_for()
        gen.reroll_trait(TABLES, a, "Outfit", random.Random(11))
        gen.reroll_trait(TABLES, b, "Outfit", random.Random(11))
        self.assertEqual(a["Outfit"], b["Outfit"])

    def test_no_flag_segment_survives_into_the_new_value(self):
        """A pinned bullet arrives carrying its flags on purpose, so every one
        of them has to come back off before the value reaches a prompt.

        Three tables are excluded because a plain roll leaves a '||' in them
        too: Backdrop keeps its scene, Faction its visual signature, and
        Weather its own flag segment, which weather_sentence() reads to decide
        whether the sentence appears at all. Their splitters run downstream,
        so a re-roll that stripped them here would be the bug rather than the
        fix.
        """
        for name in gen.RAW_REROLLABLE_TRAITS:
            if name in ("Backdrop", "Faction", "Weather"):
                continue
            for seed in self.SEEDS:
                npc = raw_npc_for(seed)
                value = gen.reroll_trait(TABLES, npc, name, random.Random(seed + 500))
                self.assertNotIn("||", value, "%s, seed %d" % (name, seed))
                self.assertNotIn("{", value, "%s, seed %d" % (name, seed))


class TestRawStaysHonest(unittest.TestCase):
    """npc["_raw"] must still describe this NPC after the re-roll.

    reroll_from_raw() replaces the dict wholesale for exactly this reason: the
    fresh roll builds a new _raw holding the bullets it actually drew, and
    keeping the old one would leave the regen writer persisting rawTraits that
    describe a bullet the NPC no longer has - traits and rawTraits silently
    disagreeing, which is the risk both specs single out.

    Asserted as a round trip rather than per key, the same way the collection
    half is: the render rule from a raw bullet back to its trait is not a
    simple strip - Hair fills a '{colour}' slot and gains a tail, Hair colour
    splits three segments of its own, Backdrop and Faction keep all three -
    so a per-key strip assertion would be a second copy of roll_npc()'s
    render rules, wrong for four tables and rotting quietly for the rest.
    """

    def test_the_new_raw_reproduces_the_new_traits(self):
        for name in gen.RAW_REROLLABLE_TRAITS:
            for seed in range(6):
                npc = raw_npc_for(seed)
                gen.reroll_trait(TABLES, npc, name, random.Random(seed + 900))
                again = gen.roll_npc(
                    TABLES, random.Random(seed + 1_000_000), dict(npc["_raw"]))
                for key in list(gen.REQUIRED_TABLES) + ["name"]:
                    self.assertEqual(
                        again[key], npc[key],
                        "re-rolled %s, seed %d: %r no longer round-trips "
                        "through _raw" % (name, seed, key))

    def test_raw_still_covers_every_table_afterwards(self):
        npc = raw_npc_for()
        gen.reroll_trait(TABLES, npc, "Outfit", random.Random(1))
        self.assertEqual(set(npc["_raw"]), set(gen.REQUIRED_TABLES))


class TestFiltersThatRebuildFromRaw(unittest.TestCase):
    """The two contradictions the raw bullets were collected to prevent.

    Both are filters that read another trait's flag segment, which is exactly
    what a stored entry threw away - so both are refusals on the lossy path
    and guarantees on this one.
    """

    def _texts_flagged(self, tables, name, flag):
        return {text for b in bullets_for(tables, name)
                if flag in gen.flags_for(name, b)
                for text in rendered(tables, name, b)}

    def test_a_rerolled_outfit_never_crosses_the_civ_mil_line(self):
        """Measured against the live tables: the fixture carries one 'civ'
        outfit and no 'mil' one, so half of this sweep would be vacuous there
        - and it is the half that catches a soldier put back in plain
        clothes.
        """
        civ = self._texts_flagged(LIVE, "Outfit", "civ")
        mil = self._texts_flagged(LIVE, "Outfit", "mil")
        self.assertTrue(civ and mil, "the live Outfit table needs both sides")
        soldiers = civilians = 0
        # Each pass is two live rolls - the entry, then the re-roll that pins
        # it - so this is the few thousand rolls the spec asks for, at about
        # three quarters of a second.
        for seed in range(1200):
            npc = gen.roll_npc(LIVE, random.Random(seed), None)
            gen.reroll_trait(LIVE, npc, "Outfit", random.Random(seed + 900))
            # Read off the pinned bullet, which is where the flag lives and
            # what the roller itself read - the rendered Role has lost it.
            if "mil" in gen.split_flags(npc["_raw"]["Role"])[1]:
                soldiers += 1
                self.assertNotIn(npc["Outfit"], civ,
                                 "seed %d: a soldier re-rolled into plain "
                                 "civilian dress" % seed)
            else:
                civilians += 1
                self.assertNotIn(npc["Outfit"], mil,
                                 "seed %d: a civilian re-rolled into a "
                                 "service uniform" % seed)
        self.assertTrue(soldiers, "no 'mil' Role was rolled in the sweep")
        self.assertTrue(civilians, "no civilian Role was rolled in the sweep")

    def test_a_rerolled_stance_never_frees_a_hand_that_is_full(self):
        armed = texts_with_hands("Weapon")
        held = texts_with_hands("Gear")
        free_poses = {text for b in bullets_for(TABLES, "Stance")
                      if "hands" in gen.split_flags(b)[1]
                      for text in rendered(TABLES, "Stance", b)}
        self.assertTrue(free_poses, "fixture needs a hands-free pose to avoid")
        checked = 0
        for seed in range(300):
            npc = raw_npc_for(seed)
            gen.reroll_trait(TABLES, npc, "Stance", random.Random(seed + 900))
            if npc["Weapon"] not in armed and npc["Gear"] not in held:
                continue
            checked += 1
            self.assertNotIn(
                npc["Stance"], free_poses,
                "seed %d: hands in pockets around %r / %r"
                % (seed, npc["Weapon"], npc["Gear"]))
        self.assertTrue(checked, "no seed rolled a Weapon or Gear that occupies "
                        "a hand - this test checked nothing")


class TestTheLossyPathIsUntouched(unittest.TestCase):
    def test_an_entry_without_raw_rerolls_exactly_the_eleven(self):
        """The fallback is kept, not replaced, so it still answers exactly as
        it did: eleven traits re-rolled and the rest refused with their own
        reason, verbatim."""
        self.assertEqual(len(gen.REROLLABLE_TRAITS), 11)
        for name in gen.REQUIRED_TABLES:
            npc = npc_for()
            if name in gen.REROLLABLE_TRAITS:
                self.assertEqual(
                    gen.reroll_trait(TABLES, npc, name, random.Random(2)),
                    npc[name])
            else:
                with self.assertRaises(SystemExit) as caught:
                    gen.reroll_trait(TABLES, npc, name, random.Random(2))
                self.assertIn(gen.UNREROLLABLE_REASONS[name],
                              str(caught.exception))

    def test_a_lossy_reroll_invents_no_raw_bullets(self):
        """Absent means "not recorded", and must stay that way through a
        re-roll: the regen writer only persists rawTraits when npc["_raw"] is
        set, so fabricating one here would claim a provenance the entry never
        had."""
        npc = npc_for()
        gen.reroll_trait(TABLES, npc, "Eyes", random.Random(1))
        self.assertNotIn("_raw", npc)


if __name__ == "__main__":
    unittest.main()
