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
nothing outside the target's cascade moves, and that npc["_raw"] still
describes the NPC afterwards rather than the one it replaced.

The free set is that cascade rather than the single trait, which is the
correction the whole branch is for: pinning filters in one direction, so a
kept trait was never re-checked against the value that had just replaced its
gate. Two classes at the end are about nothing else - one sweeps every
re-rollable trait against every contradiction that was measured, and the other
reproduces each of those contradictions on demand, so the first cannot pass by
reading the wrong flag.
"""
import contextlib
import io
import json
import random
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

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

    def test_no_raw_refusal_blames_the_lossy_manifest(self):
        """The reasons are printed verbatim, so each has to be true on the
        path that prints it.

        Most entries in UNREROLLABLE_REASONS say some version of "the manifest
        stores it with its flags already stripped", which is exactly the
        complaint raw bullets answer - the bullet is right there. So a table
        refused on this path with one of those reasons would be telling its
        owner something false about their own entry, and is far likelier to
        be a table wrongly left out of the derived set than a reason wrongly
        worded. The check that makes someone look.
        """
        for name in set(gen.REQUIRED_TABLES) - set(gen.RAW_REROLLABLE_TRAITS):
            self.assertNotIn(
                "manifest stores", gen.UNREROLLABLE_REASONS[name],
                "%r is refused even with raw bullets, so its reason cannot be "
                "that the manifest threw the flags away" % name)

    def test_it_refuses_only_what_raw_bullets_cannot_help_with(self):
        """Named one by one, so widening this set later has to argue with a
        test - each of the three is refused for a reason that survives having
        the bullets: two are the name the folder and manifest id derive from,
        and one takes the name with it.

        Theme was the fourth until re-rolls started cascading. It was held out
        because reroll_trait() had one free variable to offer and Theme needs
        twelve, which is an objection to the mechanism rather than to the
        trait; the mechanism now offers a cascade, so the objection is spent.
        """
        refused = set(gen.REQUIRED_TABLES) - set(gen.RAW_REROLLABLE_TRAITS)
        self.assertEqual(refused, {"Given names", "Family names", "Pronouns"})
        for name in refused:
            self.assertIn(name, gen.UNREROLLABLE_REASONS)

    def test_it_is_strictly_wider_than_the_legacy_set(self):
        """The point of the whole change. Anything the lossy path can re-roll
        the raw path can too, and then eleven more."""
        self.assertTrue(
            set(gen.REROLLABLE_TRAITS) < set(gen.RAW_REROLLABLE_TRAITS))

    def test_theme_is_offered_only_where_the_bullets_are(self):
        """The seam moved: Theme is a raw-path trait, not a refused one.

        An entry with raw bullets cascades it. An entry without them still
        cannot, and gets §4.2's refusal below rather than a partial cascade.
        """
        self.assertIn("Theme", gen.RAW_REROLLABLE_TRAITS)
        self.assertNotIn("Theme", gen.REROLLABLE_TRAITS)

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

    def test_nothing_outside_the_cascade_moves(self):
        """Every trait the cascade does not name is byte-identical, the name
        included.

        'name' is asserted rather than pinned: roll_npc() rebuilds it from the
        Given names and Family names this pins, so a re-roll that changed it
        would mean the pinning had failed rather than that the name needs
        handling of its own.

        The allowed set is the target's cascade, taken from the module under
        test. That would be circular if the question were "is the cascade
        right?" - it is not; test_trait_cascades.py pins every cascade against
        the design doc by hand. The question here is whether the wiring honours
        whatever cascade it was given, and nothing outside it moves. A cascade
        widened by accident fails there, loudly, rather than being absorbed
        here.

        Hair used to be named as a special case for a Hair colour re-roll - the
        colour is substituted into the cut and its tail appended, so one raw
        bullet renders into two traits. It needs no case of its own now: the
        map carries that coupling as an edge, so the cascade already contains
        it.
        """
        moved = 0
        for name in gen.RAW_REROLLABLE_TRAITS:
            allowed = set(gen.trait_cascade(name))
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

    def test_a_one_click_trait_still_moves_nothing_but_itself(self):
        """The eleven that re-rolled cleanly before must be untouched by this.

        Swept over REROLLABLE_TRAITS - the set the promise is about - rather
        than over the traits that happen to have no dependents today. Those two
        were the same list until Build was found in both, and the earlier
        version of this test filtered on `not in TRAIT_DEPENDENTS`, which
        excluded exactly the trait that had broken. A test whose selector
        removes its own counter-example cannot fail.

        The assertion above cannot stand in for this one either: it takes the
        cascade as its allowed set, so a cascade widened by accident widens the
        assertion with it. This one names the answer.
        """
        self.assertEqual(len(gen.REROLLABLE_TRAITS), 11)
        for name in gen.REROLLABLE_TRAITS:
            for seed in self.SEEDS:
                npc = raw_npc_for(seed)
                before = {k: npc[k] for k in list(gen.REQUIRED_TABLES) + ["name"]}
                gen.reroll_trait(TABLES, npc, name, random.Random(seed + 500))
                changed = {k for k in before if npc[k] != before[k]}
                self.assertTrue(
                    changed <= {name},
                    "seed %d: re-rolling %s fires on one click with no "
                    "confirmation, and it also moved %s"
                    % (seed, name, sorted(changed - {name})))

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
        # 400 rather than the 1200 this started at: TestTheMapIsCompleteOnLiveTables
        # (test_trait_cascades.py) and TestTheThemeCascade.SEEDS below already
        # drive this exact pair - a soldier's Role against a re-rolled
        # Outfit - to zero contradictions on their own seeds, so the marginal
        # seeds past 400 here were buying confidence two other sweeps already
        # supply. Each pass is two live rolls - the entry, then the re-roll
        # that pins it.
        for seed in range(400):
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

    def test_a_rerolled_scene_placement_never_lands_on_an_unlit_backdrop(self):
        """The pinned-path twin of TestGatesThatDoRebuild's case above.

        Both halves of the reason roll_npc() pastes a forced value over its
        draw need a test on this path, or half the rationale is only an
        argument. The Stance case below covers the pinned Weapon and Gear;
        this covers the pinned Backdrop, which the Glow placement filter reads
        - left to the npc.update() at the end of the roll, that filter keyed
        off the backdrop this roll discarded and washed light across a scene
        that casts none.
        """
        scene = {text for b in bullets_for(TABLES, "Glow placement")
                 if "scene" in gen.split_flags(b)[1]
                 for text in rendered(TABLES, "Glow placement", b)}
        self.assertTrue(scene, "fixture needs a 'scene' placement to avoid")
        checked = 0
        for seed in range(300):
            npc = raw_npc_for(seed)
            # The Backdrop is pinned, so reading it before the re-roll reads
            # the same bullet the filter has to honour.
            if gen.has_light_source(gen.split_backdrop(npc["Backdrop"])[1]):
                continue
            checked += 1
            gen.reroll_trait(TABLES, npc, "Glow placement",
                             random.Random(seed + 900))
            self.assertNotIn(
                npc["Glow placement"], scene,
                "seed %d: re-rolled a 'scene' placement onto a backdrop that "
                "casts no light of its own" % seed)
        self.assertTrue(checked, "no unlit backdrop was rolled - this test "
                        "checked nothing")

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


class TestTheThemeCascade(unittest.TestCase):
    """Re-rolling Theme, which is the twelve-trait case the design doc is about.

    Everything here runs on the fixture, which carries a theme tag on all seven
    themed tables and two themes to move between - so none of it is vacuous
    there, and the live sweeps below are spent on the contradictions the
    fixture is too small to reach.
    """

    # This is a deterministic-property check on the fixture - every kept
    # trait survives byte-identical, full stop, not "usually" - so depth here
    # buys confidence against a regression rather than reaching a rare flag
    # combination the way the live sweeps do. 400 catches the same class of
    # failure 1200 did (this started at 1200, the same arithmetic the live
    # civ/mil sweep above once used, before it was retargeted too) at a third
    # of the cost.
    SEEDS = range(400)

    def kept(self):
        """The traits a Theme cascade must not touch, derived the way the
        caller derives them - REQUIRED_TABLES minus the cascade - plus 'name',
        which is not a table but is the thing a user most notices moving."""
        return [name for name in gen.REQUIRED_TABLES
                if name not in gen.THEME_CASCADE] + ["name"]

    def test_every_kept_trait_survives_byte_identical(self):
        for seed in self.SEEDS:
            npc = raw_npc_for(seed)
            before = {k: npc[k] for k in self.kept()}
            gen.reroll_trait(TABLES, npc, "Theme", random.Random(seed + 700))
            for key in self.kept():
                self.assertEqual(npc[key], before[key],
                                 "seed %d: the cascade moved %r, which it keeps"
                                 % (seed, key))

    def test_it_never_produces_the_theme_it_started_from(self):
        """§8.3. The button says 'new theme'; landing back on the old one
        spends twelve traits and a render to say the same thing again."""
        self.assertGreater(len(set(TABLES["Theme"])), 1,
                           "a single-theme fixture could not fail this")
        # Fewer seeds than the sweep above: draw_different_theme() is where
        # this property lives and test_trait_cascades.py exhausts it there,
        # once per theme in the table. This is the integration half - that
        # reroll_trait() actually routes the Theme draw through it.
        for seed in range(400):
            npc = raw_npc_for(seed)
            was = npc["Theme"]
            self.assertNotEqual(
                gen.reroll_trait(TABLES, npc, "Theme", random.Random(seed + 700)),
                was, "seed %d: re-rolled %r back onto itself" % (seed, was))

    def test_every_rerolled_bullet_is_legal_under_the_new_theme(self):
        """§8.4, asked of filter_by_theme() rather than of the tables file.

        The bullet is looked for in the filtered pool rather than passed to
        the filter on its own, because every filter in the roller ends in
        `or options` - hand one a single illegal bullet and it hands that
        bullet straight back rather than an empty list. Filtering the pool the
        roller would have offered and asking whether the bullet is still in it
        asks the same question without tripping the safety valve.
        """
        for seed in range(200):
            npc = raw_npc_for(seed)
            gen.reroll_trait(TABLES, npc, "Theme", random.Random(seed + 700))
            subject = npc["Pronouns"].split("/")[0]
            for name in gen.THEMED_TABLES:
                legal = gen.filter_by_theme(
                    gen.variant_table(TABLES, name, subject), npc["Theme"], name)
                self.assertIn(
                    npc["_raw"][name], legal,
                    "seed %d: %s kept %r, which is tagged for another theme"
                    % (seed, name, npc["_raw"][name]))

    def test_the_theme_filter_drops_something_from_every_themed_table(self):
        """Per table rather than summed, which is the difference between a
        guard and a total.

        The sweep above makes seven membership assertions per seed, one per
        themed table. A table whose fixture bullets carry no '@' tag makes its
        own assertion vacuous - every bullet is then reachable under every
        theme, so it holds whatever the cascade did - and a summed count would
        never notice, because the six tagged tables carry it.

        "Under some theme" rather than "under every theme": a tagged bullet is
        legitimately kept under its own theme, and the fixture's Hair colour
        has exactly one tagged bullet, so requiring a drop under both themes
        would fail on content that is correct. What has to exist is a bullet
        the filter can refuse somewhere, which is what makes a seed landing on
        the other theme a real test.
        """
        for name in gen.THEMED_TABLES:
            pool = gen.variant_table(TABLES, name, "she")
            droppable = any(
                len(gen.filter_by_theme(pool, theme, name)) < len(pool)
                for theme in set(TABLES["Theme"]))
            self.assertTrue(
                droppable,
                "no %s bullet in the fixture is tagged for a theme it can be "
                "filtered out of, so the legality sweep above asserts nothing "
                "about %s" % (name, name))

    def test_the_recomputed_flags_travel_with_the_cascade(self):
        """'young' and 'outfit_notac' are written back to the manifest by
        regenerate_one(), so they have to describe the NPC the cascade produced
        rather than the one it replaced.

        Read off the new raw bullets, which is where roll_npc() read them. A
        stale '_outfit_notac' would be the worse of the two: it is what a LATER
        Headgear re-roll on the lossy path trusts, so a wrong one outlives the
        run that wrote it.
        """
        for seed in range(200):
            npc = raw_npc_for(seed)
            gen.reroll_trait(TABLES, npc, "Theme", random.Random(seed + 700))
            self.assertEqual(npc["_young"],
                             "young" in gen.flags_for("Age", npc["_raw"]["Age"]))
            self.assertEqual(
                npc["_outfit_notac"],
                "notac" in gen.flags_for("Outfit", npc["_raw"]["Outfit"]))


def flags_of(npc, name):
    """The flags on the bullet this NPC's `name` actually came from.

    Read off npc["_raw"], which is the same string the roller's own filters
    read, rather than reverse-mapped from the rendered trait. Not a second
    definition of any of them: 'hands' is test_hands.py's flag, 'civ'/'mil' is
    the pair filter_by_mil() splits on in test_faction.py, and this reads those
    exact flags one step earlier - off the bullet instead of off the text it
    renders to. The rendered-text form those modules use exists because they
    predate raw bullets and had nothing else to compare against.
    """
    return gen.flags_for(name, npc["_raw"][name])


def unlit(npc):
    """The Backdrop casts no light of its own - roll_npc()'s own test."""
    return not gen.has_light_source(gen.split_backdrop(npc["Backdrop"])[1])


# Every contradiction a re-roll was measured to leave behind, as (what it is,
# which trait's re-roll stranded it, is this NPC holding it).
#
# Each predicate is the roller's own filter turned into a question about the
# pair it decides between, rather than a call to the filter itself. The filters
# all end in `or options` - a safety valve so no pool is ever narrowed to
# nothing - so handing one a single illegal bullet returns that bullet rather
# than an empty list, and a check written that way reports zero contradictions
# against any implementation at all. That mistake was made once while writing
# this; it is recorded here because the resulting test looks more principled
# than the working one.
#
# The counts these were measured at are in the guard below, not here: a number
# in a comment goes stale silently, and one in a test does not.
# The fourth field is the case the pairing is about - the NPC is on the narrow
# side of the filter, whether or not it went wrong. A sweep that never reached
# it would report zero contradictions for a reason that has nothing to do with
# the cascade, so it is counted rather than assumed.
CONTRADICTIONS = (
    ("Faction on the wrong side of the civ/mil line", "Role",
     lambda n: ("civ" if "mil" in flags_of(n, "Role") else "mil")
     in flags_of(n, "Faction"),
     lambda n: "mil" in flags_of(n, "Role")),
    ("Outfit on the wrong side of the civ/mil line", "Role",
     lambda n: ("civ" if "mil" in flags_of(n, "Role") else "mil")
     in flags_of(n, "Outfit"),
     lambda n: "mil" in flags_of(n, "Role")),
    ("a hands-free Stance around a full hand", "Gear",
     lambda n: "hands" in flags_of(n, "Weapon") + flags_of(n, "Gear")
     and "hands" in flags_of(n, "Stance"),
     lambda n: "hands" in flags_of(n, "Weapon") + flags_of(n, "Gear")),
    ("a 'scene' Glow placement on a backdrop that casts no light", "Backdrop",
     lambda n: unlit(n) and "scene" in flags_of(n, "Glow placement"),
     unlit),
    ("hardtech Headgear over a 'notac' Outfit", "Outfit",
     lambda n: n["_outfit_notac"] and "hardtech" in flags_of(n, "Headgear"),
     lambda n: n["_outfit_notac"]),
    ("an 'older' Hair colour on a teenager", "Age",
     lambda n: n["_young"] and "older" in flags_of(n, "Hair colour"),
     lambda n: n["_young"]),
    ("a hands-occupying Gear in a 'nogear' scene", "Backdrop",
     lambda n: "nogear" in gen.split_backdrop(n["Backdrop"])[2]
     and "hands" in flags_of(n, "Gear"),
     lambda n: "nogear" in gen.split_backdrop(n["Backdrop"])[2]),
)


class TestNoCascadeLeavesAContradiction(unittest.TestCase):
    """The defect the cascade was built to close, over every trait at once.

    A pinned re-roll filters in one direction. The freed trait is drawn against
    everything pinned, but a pinned trait is never drawn, so no filter ever
    re-checks it against the value that just changed - and the entry comes back
    holding a pairing the roller could not have produced. Freeing the target's
    cascade instead re-draws every trait a filter would have had to reject, so
    there is nothing left to be stranded.

    Run against the live tables. The fixture carries one 'civ' Outfit and no
    'mil' one, two Roles and neither in WEAPON_POLICY, so half of this would be
    vacuous there - and it is the half that catches a colonial administrator
    under a marine corps banner. The guard below is what keeps the other half
    honest.
    """

    # Every target, so a contradiction nobody has thought of has somewhere to
    # show up - the two that started this were both found by a sweep rather
    # than by reasoning. 80 seeds against 22 targets is one of the more
    # expensive tests in the suite, at about a second; the depth that would
    # catch a rare pair is bought in the guard below instead, where it can be
    # spent on the one target that pair actually comes from.
    SEEDS = 80

    def test_no_reroll_strands_any_of_them(self):
        found = []
        # Not a vacuity guard bolted on afterwards: at this seed count each
        # case has to be shown reachable IN THIS SWEEP, or "no contradictions"
        # could mean "no NPC on the narrow side of the filter". The guard class
        # below proves the predicates are live, which is a different claim -
        # it runs 400 seeds against one target apiece.
        reached = {label: 0 for label, _, _, _ in CONTRADICTIONS}
        for target in gen.RAW_REROLLABLE_TRAITS:
            for seed in range(self.SEEDS):
                npc = gen.roll_npc(LIVE, random.Random(seed), None)
                gen.reroll_trait(LIVE, npc, target, random.Random(seed + 900))
                for label, _, contradicts, in_the_case in CONTRADICTIONS:
                    reached[label] += bool(in_the_case(npc))
                    if contradicts(npc):
                        found.append("re-rolling %s, seed %d: %s"
                                     % (target, seed, label))
        self.assertEqual(found, [], "\n".join(found))
        for label, count in reached.items():
            self.assertTrue(
                count, "no NPC in the sweep was even in the case %r describes, "
                "so it was never asked" % label)

    def test_a_fresh_roll_holds_none_of_them_either(self):
        """The baseline the sweep above is only meaningful against.

        These are pairings the roller's filters exist to prevent, so an
        untouched roll must not produce one. If this fails, a predicate is
        wrong rather than the cascade - and the sweep above is measuring the
        tables file rather than the wiring.
        """
        for seed in range(400):
            npc = gen.roll_npc(LIVE, random.Random(seed), None)
            for label, _, contradicts, _ in CONTRADICTIONS:
                self.assertFalse(contradicts(npc),
                                 "seed %d: a fresh roll produced %s"
                                 % (seed, label))


class TestTheContradictionChecksCanFail(unittest.TestCase):
    """Every check above, run against the mechanism the cascade replaced.

    Without this the sweep is seven predicates that might be reading the wrong
    flag, passing on every NPC ever rolled. So each one is re-run with the free
    set the re-roll used to take - the single named trait, no dependents - on
    the one trait whose re-roll stranded it, and has to fire. What it is
    measuring is the defect itself, still reproducible on demand.

    Asserted as "at least once" rather than at the count it was measured at.
    The counts over 400 seeds were 134, 111, 30, 34, 17, 5 and 24 in the order
    the table lists them, and they are worth knowing - but they are properties
    of today's tables file, and pinning them would turn a new Faction bullet
    into a failing test that said nothing about the cascade.
    """

    SEEDS = 400

    def test_each_one_fires_when_only_the_named_trait_is_freed(self):
        targets = sorted({target for _, target, _, _ in CONTRADICTIONS})
        counts = {label: 0 for label, _, _, _ in CONTRADICTIONS}
        for target in targets:
            for seed in range(self.SEEDS):
                npc = gen.roll_npc(LIVE, random.Random(seed), None)
                gen.reroll_from_raw(LIVE, npc, (target,), random.Random(seed + 900))
                for label, stranded_by, contradicts, _ in CONTRADICTIONS:
                    if stranded_by == target and contradicts(npc):
                        counts[label] += 1
        for label, count in counts.items():
            self.assertTrue(
                count, "%r never appeared in %d single-trait re-rolls, so the "
                "check for it in the cascade sweep proves nothing"
                % (label, self.SEEDS))


class TestTheEdgeThatIsDeliberatelyMissing(unittest.TestCase):
    """Why TRAIT_DEPENDENTS has Age -> Build and not Build -> Age.

    roll_npc() runs the 'young'/'figure' pairing in both directions, so a map
    that recorded filters alone would carry both edges - and the obvious
    reading of "record every filter" is what put one there in the first place.
    Build is one of the eleven traits that fire on one click with no dialog, so
    an edge from it turns a build re-roll into a silent change of age and hair.

    That is only acceptable if the edge guards nothing, so this measures it
    rather than arguing it: with the narrowest free set there is - the single
    trait, no dependents at all - the pairing never appears in either
    direction, because roll_npc() has already filtered it. Freeing Build, the
    pinned Age's 'young' narrows the Build pool inside the loop; freeing Age, a
    pinned 'figure' Build narrows the Age pool through the forced_figure
    branch. Both halves are swept, since an argument about symmetry is worth
    exactly as much as the half of it nobody checked.

    Measured against the live tables - the fixture has one 'figure' Build and
    the sweep would spend most of its seeds on NPCs the pairing cannot reach.
    """

    SEEDS = 250

    def test_the_pairing_never_appears_with_either_trait_freed_alone(self):
        figures = teenagers = 0
        for name in ("Build", "Age"):
            for seed in range(self.SEEDS):
                npc = gen.roll_npc(LIVE, random.Random(seed), None)
                gen.reroll_from_raw(LIVE, npc, (name,), random.Random(seed + 900))
                figure = "figure" in flags_of(npc, "Build")
                young = "young" in flags_of(npc, "Age")
                figures += figure
                teenagers += young
                self.assertFalse(
                    figure and young,
                    "seed %d: freeing %s alone put an adult woman's build on a "
                    "teenager - the Build -> Age edge was dropped on the "
                    "grounds that this cannot happen" % (seed, name))
        self.assertTrue(figures, "no 'figure' Build in the sweep")
        self.assertTrue(teenagers, "no 'young' Age in the sweep")


class TestTheCascadeReport(unittest.TestCase):
    """What --reroll-trait actually prints, which is spec §6's half of this.

    Somebody who re-rolls Theme expecting a new palette gets a new outfit,
    weapon, hair and scene, so the run enumerates rather than summarising. That
    is a requirement rather than a nicety, and it lives in regenerate_one(),
    which renders - so it was nearly left untested on the grounds of needing
    ComfyUI. It does not: the prints all happen before the workflow is
    resolved, so a temp manifest and a stub args reach every one of them and
    then die on a workflow that is deliberately not there. Untested is a
    choice; untestable was wrong.
    """

    def report_for(self, trait, with_raw=True):
        """stdout from regenerating one entry with `trait` re-rolled."""
        npc = gen.roll_npc(TABLES, random.Random(4), None)
        entry = {
            "id": "report-1",
            "seed": 4,
            "workflow": "workflows/no-such-workflow.json",
            "traits": {k: v for k, v in npc.items() if not k.startswith("_")},
            "rawTraits": dict(npc["_raw"]),
            "young": npc["_young"],
            "outfit_notac": npc["_outfit_notac"],
            "files": [],
        }
        if not with_raw:
            entry.pop("rawTraits")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps({"out/report": entry}), encoding="utf-8")
            args = types.SimpleNamespace(
                regen_manifest=path, regen_id="report-1", reroll_trait=trait,
                tables=FIXTURE_TABLES, new_seed=None)
            out = io.StringIO()
            # The workflow is named but absent, which is as far as this can go
            # without a ComfyUI to render through - every print under test has
            # already happened by then.
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(
                    io.StringIO()):
                with self.assertRaises(SystemExit):
                    gen.regenerate_one(args)
        return [line for line in out.getvalue().splitlines()
                if line.startswith("re-rolled ") or line.startswith("  with ")]

    def test_a_cascade_names_every_trait_that_travelled(self):
        lines = self.report_for("Theme")
        self.assertTrue(lines[0].startswith("re-rolled Theme: "))
        named = [line.split(":")[0].strip()[len("with "):] for line in lines[1:]]
        self.assertEqual(
            named, [t for t in gen.THEME_CASCADE if t != "Theme"],
            "the report should name the other eleven, in the cascade's order")

    def test_each_line_shows_what_the_trait_was_and_is(self):
        """A bare list of names would satisfy the test above and tell the
        reader nothing about what changed."""
        for line in self.report_for("Theme"):
            self.assertIn(" -> ", line, line)

    def test_a_one_click_trait_still_prints_one_line(self):
        """The other half of the promise: no cascade, no cascade report."""
        self.assertEqual(len(self.report_for("Eyes")), 1)

    def test_the_lossy_path_prints_one_line_too(self):
        """It re-rolls the one trait it was asked for, so there is nothing to
        enumerate - and printing a cascade there would describe traits that
        did not move."""
        self.assertEqual(len(self.report_for("Hair", with_raw=False)), 1)


class TestTheRegenWriterActuallyRuns(unittest.TestCase):
    """The manifest write regenerate_one() does after a raw re-roll, driven
    for real rather than rebuilt inline.

    test_raw_traits.py's TestWhatTheWriterStores rebuilds the writers' dict
    comprehensions by hand, which proves the SHAPE is right but never once
    calls `entry["rawTraits"] = dict(npc["_raw"])` itself - deleting that
    line would leave that test, and every other test in the suite, green.
    This drives regenerate_one() past it instead, the way
    TestTheCascadeReport above does, but far enough that art.save_manifest()
    actually runs: both --no-portrait and --no-token skip the render
    entirely, a packaged workflow file that exists on disk lets
    resolve_recorded_workflow() and locate_slots() succeed for real instead
    of raising, and find_server() is stubbed rather than left to fail on no
    ComfyUI listening - the one piece of the pipeline this harness cannot
    reach without a running server.
    """

    # Seed 1: the one hand-checked seed in a small sweep where re-rolling
    # Eyes actually changes the bullet ('dark eyes, steady and unreadable' ->
    # 'grey eyes'). A seed where the reroll happens to land back on the same
    # value would pass this test whether or not the writer line exists, since
    # the entry's ORIGINAL rawTraits (seeded into it below, pre-reroll)
    # would then equal the post-reroll one it should have been overwritten
    # with - the exact way a too-weak assertion could rot silently.
    SEED = 1

    def test_a_raw_reroll_persists_the_rerolled_rawTraits_to_the_manifest(self):
        npc = gen.roll_npc(TABLES, random.Random(self.SEED), None)
        entry = {
            "id": "writer-check-1",
            "seed": self.SEED,
            "workflow": str(REPO / "workflows" / "api" / "Lancer_Scene_Workflow_v1.json"),
            "traits": {k: v for k, v in npc.items() if not k.startswith("_")},
            "rawTraits": dict(npc["_raw"]),
            "young": npc["_young"],
            "outfit_notac": npc["_outfit_notac"],
            "files": [],
        }

        # Computed independently of regenerate_one(), against a fresh copy of
        # the same roll, so the assertion below is not just "some value was
        # written" but "the value the reroll actually produced was written" -
        # the distinction that catches the writer line being deleted even
        # though the entry already carries a (now stale) rawTraits of its own.
        expected = gen.roll_npc(TABLES, random.Random(self.SEED), None)
        gen.reroll_trait(TABLES, expected, "Eyes", random.Random(entry["seed"]))
        expected_raw = dict(expected["_raw"])
        self.assertNotEqual(
            expected_raw, entry["rawTraits"],
            "seed %d's Eyes reroll landed back on its old value, so this "
            "seed cannot tell a persisted reroll from a stale one - pick a "
            "different SEED" % self.SEED)

        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            # Inside the temp dir, so folder.mkdir() further down leaves
            # nothing behind once the test exits.
            folder_path = str(Path(tmp) / "out" / "writer-check")
            manifest_path.write_text(
                json.dumps({folder_path: entry}), encoding="utf-8")
            args = types.SimpleNamespace(
                regen_manifest=manifest_path, regen_id="writer-check-1",
                reroll_trait="Eyes", new_seed=None, tables=FIXTURE_TABLES,
                no_portrait=True, no_token=True, server=None)
            stub_comfy = types.SimpleNamespace(base="stub://nowhere")
            with mock.patch.object(gen.art, "find_server", return_value=stub_comfy):
                result = gen.regenerate_one(args)
            self.assertEqual(
                result, 0,
                "the regen should have completed with both stages skipped, "
                "not hit a code path this stub does not cover")
            saved = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(
                saved[folder_path].get("rawTraits"), expected_raw,
                "regenerate_one() re-rolled Eyes but did not persist the "
                "resulting rawTraits back to the manifest")


class TestAnIncompleteRaw(unittest.TestCase):
    """rawTraits written before a table joined the roll.

    The two lists move at different speeds on purpose: RAW_REROLLABLE_TRAITS
    is derived from REQUIRED_TABLES and admits a new table the day it is
    added, while an entry's rawTraits is a record of the day it was written.
    So a table can be re-rollable for an entry that has no bullet for it, and
    the unpinned trait then rolls free - changing something nobody asked to
    change. Warned about rather than refused, which is what migrate_traits()
    does for a Headgear and regenerate_one() for a Height.
    """

    def _reroll_quietly(self, npc, name):
        with contextlib.redirect_stderr(io.StringIO()) as err:
            gen.reroll_trait(TABLES, npc, name, random.Random(0))
        return err.getvalue()

    def test_it_names_the_table_that_will_roll_free(self):
        npc = raw_npc_for()
        del npc["_raw"]["Weather"]
        warning = self._reroll_quietly(npc, "Eyes")
        self.assertIn("Weather", warning)
        self.assertIn("Re-roll the NPC", warning,
                      "the warning should say how to stop getting it")

    def test_a_complete_raw_warns_about_nothing(self):
        """The counterpart, so the warning stays a signal: an ordinary entry
        must not print it on every re-roll."""
        self.assertEqual(self._reroll_quietly(raw_npc_for(), "Eyes"), "")

    def test_the_trait_being_rerolled_is_not_warned_about(self):
        """Re-rolling the very table the entry has no bullet for is not a
        surprise - it is the request. Warning there would train the user to
        ignore the message in the case that matters."""
        npc = raw_npc_for()
        del npc["_raw"]["Weather"]
        self.assertEqual(self._reroll_quietly(npc, "Weather"), "")


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

    def test_a_theme_reroll_is_refused_with_the_spec_message(self):
        """§8.6, and the one refusal the design doc writes out itself.

        A cascade needs the Role's 'mil' flag to re-roll the Outfit and Weapon
        under it, and this entry threw that flag away before it was stored. The
        refusal is the whole point: the alternative is a partial cascade, which
        is precisely the set of contradictions this design exists to avoid, and
        it would arrive silently. So the message has to carry three things -
        why, how to stop being refused, and what can still be re-rolled today.
        """
        with self.assertRaises(SystemExit) as caught:
            gen.reroll_trait(TABLES, npc_for(), "Theme", random.Random(0))
        message = str(caught.exception)
        # The whole reason, not a substring of it. §4.2's sentence names three
        # traits and one flag, and it is those specifics that tell the reader
        # what was lost; a rewording that dropped the Outfit and Weapon and
        # kept "before raw bullets were recorded" would still be a message,
        # but it would no longer be the one the spec wrote.
        self.assertEqual(
            gen.UNREROLLABLE_REASONS["Theme"],
            "this NPC was generated before raw bullets were recorded, so its "
            "Role's 'mil' flag is gone and a themed re-roll of its Outfit "
            "and Weapon could contradict it")
        self.assertIn(gen.UNREROLLABLE_REASONS["Theme"], message)
        self.assertIn("Re-roll the NPC to record them, or re-roll a single "
                      "trait from: ", message)
        for name in gen.REROLLABLE_TRAITS:
            self.assertIn(name, message,
                          "the refusal should still offer %r" % name)

    def test_that_refusal_does_not_blame_the_script(self):
        """The reasons were rewritten when the cascade landed, and this is what
        keeps them rewritten.

        'the manifest stores Role with its flags already stripped' was a claim
        about the format. The format records them now, so printed today it
        would send the owner of a modern NPC looking for a limitation that has
        been fixed, instead of at the one-line cure. Every reason reachable
        only from the lossy path has to talk about the entry.
        """
        for name, reason in gen.UNREROLLABLE_REASONS.items():
            if name in gen.RAW_REROLLABLE_TRAITS:
                self.assertNotIn("the manifest stores", reason,
                                 "%r is re-rollable given raw bullets, so its "
                                 "refusal is about this entry rather than about "
                                 "the manifest format" % name)

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
