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
import contextlib
import io
import json
import random
import tempfile
import unittest
from pathlib import Path

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


def raw_npc(tables=LIVE, seed=0):
    """A freshly rolled NPC, which by construction has its raw bullets."""
    return gen.roll_npc(tables, random.Random(seed), None)


class ChoicesDescribeTheCurrentNpc(unittest.TestCase):
    def test_the_value_the_npc_is_wearing_is_always_allowed(self):
        # The tightest invariant in the file. Whatever it has on was legal
        # when it was rolled and nothing has changed since, so a pin that
        # reports it as ruled out is reporting on the wrong NPC.
        for seed in range(8):
            npc = raw_npc(seed=seed)
            for trait in gen.RAW_REROLLABLE_TRAITS:
                with self.subTest(seed=seed, trait=trait):
                    choices = gen.trait_choices(LIVE, npc, trait)
                    current = [c for c in choices if c["current"]]
                    self.assertEqual(len(current), 1, "exactly one current value")
                    self.assertTrue(current[0]["allowed"])
                    self.assertEqual(current[0]["conflicts"], [])

    def test_current_marks_the_stored_raw_bullet(self):
        npc = raw_npc(seed=1)
        choices = gen.trait_choices(LIVE, npc, "Outfit")
        current = next(c for c in choices if c["current"])
        self.assertEqual(current["value"], npc["_raw"]["Outfit"])

    def test_every_bullet_in_the_table_is_offered_once(self):
        # Once, not once per point of weight: variant_table() repeats a
        # heavier bullet to make rng.choice() favour it, which is the right
        # shape for a draw and the wrong one for a list somebody reads.
        npc = raw_npc(seed=2)
        subject = npc["Pronouns"].split("/")[0].strip().lower()
        expected = list(dict.fromkeys(gen.variant_table(LIVE, "Outfit", subject)))
        got = [c["value"] for c in gen.trait_choices(LIVE, npc, "Outfit")]
        self.assertEqual(got, expected)

    def test_a_weighted_bullet_is_offered_only_once(self):
        npc = raw_npc(seed=2)
        for trait in gen.RAW_REROLLABLE_TRAITS:
            values = [c["value"] for c in gen.trait_choices(LIVE, npc, trait)]
            with self.subTest(trait=trait):
                self.assertEqual(len(values), len(set(values)))

    def test_nothing_is_dropped_for_being_illegal(self):
        # The picker greys ruled-out values rather than hiding them, so this
        # function must report them rather than filter them.
        npc = raw_npc(seed=3)
        choices = gen.trait_choices(LIVE, npc, "Headgear")
        self.assertTrue(any(not c["allowed"] for c in choices),
                        "live Headgear has bullets some NPC cannot wear")


class ConflictsNameTheTraitThatWouldBreak(unittest.TestCase):
    def test_a_backdrop_that_forbids_gear_conflicts_with_a_hands_gear(self):
        # The correction the probe exists to expose: roll_npc() re-rolls a
        # 'hands' Gear under a 'nogear' scene, but a PINNED Gear is pasted
        # back over that correction, so the clash survives into the render.
        npc = next(n for n in (raw_npc(seed=s) for s in range(60))
                   if "hands" in gen.split_flags(n["_raw"]["Gear"])[1])
        choices = gen.trait_choices(LIVE, npc, "Backdrop")
        nogear = [c for c in choices
                  if "nogear" in gen.split_backdrop(c["value"])[2]]
        self.assertTrue(nogear, "the live tables have 'nogear' backdrops")
        for c in nogear:
            with self.subTest(value=c["value"][:40]):
                self.assertIn("Gear", c["conflicts"])

    def test_backdrop_never_reports_a_weather_conflict(self):
        # Backdrop -> Weather is a freshness edge, not a filter one: nothing
        # narrows the Weather pool, so a kept Weather is never illegal, only
        # newly hidden or newly shown.
        for seed in range(6):
            npc = raw_npc(seed=seed)
            for c in gen.trait_choices(LIVE, npc, "Backdrop"):
                with self.subTest(seed=seed):
                    self.assertNotIn("Weather", c["conflicts"])

    def test_a_pair_the_roller_refuses_outright_is_reported_as_a_conflict(self):
        # Two pairings are not filtered but refused: a 'young' Age with a
        # 'figure' Build, and a 'plain' Role with a 'dressy' Outfit. roll_npc()
        # raises for those instead of returning a narrower pool, because a
        # pool filter cannot catch a pair that was both forced - which is every
        # pair a fully pinned query makes. If they were not caught, the query
        # would crash on the exact candidates it most needs to warn about.
        npc = next(n for n in (raw_npc(seed=s) for s in range(80))
                   if "figure" in gen.split_flags(n["_raw"]["Build"])[1])
        young = [c for c in gen.trait_choices(LIVE, npc, "Age")
                 if "young" in gen.split_flags(c["value"])[1]]
        self.assertTrue(young, "the live Age table has 'young' bullets")
        for c in young:
            with self.subTest(value=c["value"][:40]):
                self.assertIn("Build", c["conflicts"])

    def test_the_refusal_names_the_trait_that_caused_it(self):
        # Age gates Build and Hair colour. A 'figure' Build is what a 'young'
        # Age collides with, so naming Hair colour as well would send the user
        # to re-roll a shade that was never the problem.
        npc = next(n for n in (raw_npc(seed=s) for s in range(80))
                   if "figure" in gen.split_flags(n["_raw"]["Build"])[1])
        for c in gen.trait_choices(LIVE, npc, "Age"):
            if "young" in gen.split_flags(c["value"])[1]:
                with self.subTest(value=c["value"][:40]):
                    self.assertEqual(c["conflicts"], ["Build"])

    def test_a_trait_with_no_dependents_reports_no_conflicts(self):
        npc = raw_npc(seed=4)
        for trait in ("Faction", "Glow colour", "Demeanor"):
            with self.subTest(trait=trait):
                self.assertTrue(
                    all(c["conflicts"] == []
                        for c in gen.trait_choices(LIVE, npc, trait)))

    def test_conflicts_only_ever_name_direct_dependents(self):
        npc = raw_npc(seed=5)
        for trait in gen.RAW_REROLLABLE_TRAITS:
            allowed = set(gen.TRAIT_DEPENDENTS.get(trait, ()))
            for c in gen.trait_choices(LIVE, npc, trait):
                with self.subTest(trait=trait):
                    self.assertTrue(set(c["conflicts"]) <= allowed)


class ReleasesIsTheCascadeClosure(unittest.TestCase):
    def test_releases_covers_every_conflict(self):
        npc = raw_npc(seed=6)
        for trait in gen.RAW_REROLLABLE_TRAITS:
            for c in gen.trait_choices(LIVE, npc, trait):
                with self.subTest(trait=trait):
                    self.assertTrue(set(c["conflicts"]) <= set(c["releases"]))

    def test_releases_is_the_closure_of_the_conflicts(self):
        # Freeing a conflicting trait re-rolls it, and anything gated by it
        # then has to move too - otherwise the contradiction reappears one
        # level down, which is the whole reason the flag expands.
        npc = raw_npc(seed=7)
        for trait in gen.RAW_REROLLABLE_TRAITS:
            for c in gen.trait_choices(LIVE, npc, trait):
                expected = set()
                for d in c["conflicts"]:
                    expected |= set(gen.trait_cascade(d))
                expected -= {trait}
                with self.subTest(trait=trait, value=c["value"][:30]):
                    self.assertEqual(set(c["releases"]), expected)

    def test_releases_is_empty_when_conflicts_is(self):
        npc = raw_npc(seed=8)
        for trait in gen.RAW_REROLLABLE_TRAITS:
            for c in gen.trait_choices(LIVE, npc, trait):
                if not c["conflicts"]:
                    with self.subTest(trait=trait):
                        self.assertEqual(c["releases"], [])


LIVE_TABLES_PATH = REPO / "prompts" / "npc-generator-tables.md"


def manifest_with(npc, path, seed=0, drop_raw=False):
    """A one-entry manifest file on disk, as regenerate_one() reads it."""
    entry = {
        "id": "npc-test-%d" % seed,
        "kind": "npc",
        "name": npc["name"],
        "callsign": npc["Callsigns"],
        "seed": seed,
        "traits": {k: v for k, v in npc.items() if not k.startswith("_")},
        "young": npc["_young"],
        "outfit_notac": npc["_outfit_notac"],
        "gear_helmet": npc["_gear_helmet"],
        "rawTraits": {} if drop_raw else npc["_raw"],
    }
    path.write_text(json.dumps({"npcs/test": entry}), encoding="utf-8")
    return path


class TraitChoicesCommand(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.npc = raw_npc(seed=0)
        self.manifest = manifest_with(self.npc, Path(self.dir.name) / "m.json")

    def run_cli(self, *extra, manifest=None):
        # --tables explicitly: the NPC in the manifest was rolled from LIVE,
        # so the query has to read the same file, and leaning on the default
        # would make this test depend on the working directory.
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            gen.main(["--regen-manifest", str(manifest or self.manifest),
                      "--regen-id", "npc-test-0",
                      "--tables", str(LIVE_TABLES_PATH),
                      *extra])
        return out.getvalue()

    def test_it_prints_json_and_renders_nothing(self):
        got = json.loads(self.run_cli("--trait-choices", "Outfit"))
        self.assertEqual(got["trait"], "Outfit")
        self.assertEqual(got["current"], self.npc["_raw"]["Outfit"])
        self.assertEqual(got["dependents"], ["Headgear", "Weapon", "Gear"])
        self.assertTrue(got["choices"])

    def test_every_choice_carries_the_documented_keys(self):
        got = json.loads(self.run_cli("--trait-choices", "Outfit"))
        for choice in got["choices"]:
            self.assertEqual(
                sorted(choice),
                ["allowed", "conflicts", "current", "heading", "releases", "value"])

    def test_stdout_is_json_and_nothing_else(self):
        # The GUI parses stdout whole, so one stray banner line breaks it -
        # the same constraint --trait-odds already documents.
        json.loads(self.run_cli("--trait-choices", "Hair"))

    def test_the_flags_stay_on_the_value(self):
        # --set-trait takes its bullet verbatim and the downstream filters read
        # those flags, so stripping them anywhere on this path is a real bug.
        got = json.loads(self.run_cli("--trait-choices", "Outfit"))
        self.assertTrue(any("||" in c["value"] for c in got["choices"]))

    def test_an_unrerollable_trait_is_refused(self):
        with self.assertRaises(SystemExit) as caught:
            self.run_cli("--trait-choices", "Pronouns")
        self.assertIn("Pronouns", str(caught.exception))

    def test_an_entry_without_raw_bullets_is_refused(self):
        legacy = manifest_with(
            self.npc, Path(self.dir.name) / "legacy.json", drop_raw=True)
        with self.assertRaises(SystemExit) as caught:
            self.run_cli("--trait-choices", "Outfit", manifest=legacy)
        self.assertIn("re-roll", str(caught.exception).lower())

    def test_it_refuses_to_run_alongside_a_reroll(self):
        with self.assertRaises(SystemExit):
            self.run_cli("--trait-choices", "Hair", "--reroll-trait", "Hair")


class SetTraitOnARegen(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.npc = raw_npc(seed=0)
        self.manifest = manifest_with(self.npc, Path(self.dir.name) / "m.json")
        self.entry = json.loads(self.manifest.read_text())["npcs/test"]

    def pinned(self, table, value, release=None):
        """regenerate_one()'s roll half, without the render half."""
        npc = gen.npc_from_entry(self.entry, "npc-test-0", warn=False)
        free = set()
        for name in (release or ()):
            free |= set(gen.trait_cascade(name))
        gen.reroll_from_raw(LIVE, npc, free, random.Random(1), {table: value})
        return npc

    def other_value_for(self, trait):
        choices = gen.trait_choices(LIVE, self.npc, trait)
        return next(c for c in choices
                    if c["allowed"] and not c["current"] and not c["conflicts"])

    def test_only_the_named_trait_moves(self):
        pick = self.other_value_for("Demeanor")
        after = self.pinned("Demeanor", pick["value"])
        moved = [t for t in gen.REQUIRED_TABLES
                 if self.npc["_raw"].get(t) != after["_raw"].get(t)]
        self.assertEqual(moved, ["Demeanor"])

    def test_the_named_trait_actually_takes_the_value(self):
        pick = self.other_value_for("Demeanor")
        after = self.pinned("Demeanor", pick["value"])
        self.assertEqual(after["_raw"]["Demeanor"], pick["value"])

    def test_the_pin_is_exactly_a_roll_with_that_bullet_forced(self):
        # The one risk both specs single out is rawTraits describing bullets
        # the NPC no longer carries, and this is the tightest way to rule it
        # out: the pinned result is compared against roll_npc() handed the same
        # overrides directly. Nothing is poked by hand, so _raw, the rendered
        # traits, _young, _outfit_notac, _gear_helmet and the '{colour}' fill
        # all recompute together or the comparison fails.
        #
        # Comparing raw against rendered field by field would NOT work and is
        # worth saying so: a raw bullet legitimately keeps its pronoun
        # placeholders ('{Subject} {wear} a rolled bandana') exactly as it
        # keeps '{colour}', and those are filled at render.
        pick = self.other_value_for("Outfit")
        after = self.pinned("Outfit", pick["value"])
        expected = gen.roll_npc(
            LIVE, random.Random(1),
            dict(self.npc["_raw"], Outfit=pick["value"]))
        self.assertEqual(after, expected)

    def test_releasing_a_trait_frees_its_whole_cascade(self):
        # Freeing Outfit alone would redraw it while Headgear, Weapon and Gear
        # stayed pinned to bullets chosen for the outfit that is now gone.
        pick = next(c for c in gen.trait_choices(LIVE, self.npc, "Theme")
                    if c["conflicts"])
        after = self.pinned("Theme", pick["value"], release=pick["conflicts"])
        untouched = [t for t in gen.REQUIRED_TABLES
                     if t not in pick["releases"] and t != "Theme"]
        for trait in untouched:
            with self.subTest(trait=trait):
                self.assertEqual(self.npc["_raw"].get(trait),
                                 after["_raw"].get(trait))

    def test_releasing_nothing_keeps_every_other_trait(self):
        pick = next(c for c in gen.trait_choices(LIVE, self.npc, "Theme")
                    if c["conflicts"])
        after = self.pinned("Theme", pick["value"])
        for trait in gen.REQUIRED_TABLES:
            if trait == "Theme":
                continue
            with self.subTest(trait=trait):
                self.assertEqual(self.npc["_raw"].get(trait),
                                 after["_raw"].get(trait))


class SetTraitRefusesWhatRerollRefuses(unittest.TestCase):
    """The pin accepts exactly the traits --reroll-trait does, and no more.

    Naming a value rather than drawing one does not make Pronouns safer to
    change under an NPC whose every appearance bullet was drawn for the old
    subject, and the two halves of the name decide the folder and the manifest
    id. A table this script does not roll is refused for a different reason
    that matters just as much: roll_npc() silently ignores an override for a
    table it has never heard of, so a typo would regenerate the NPC unchanged
    and report success.
    """

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.npc = raw_npc(seed=0)
        self.manifest = manifest_with(self.npc, Path(self.dir.name) / "m.json")

    def run_cli(self, *extra):
        return gen.main(["--regen-manifest", str(self.manifest),
                         "--regen-id", "npc-test-0",
                         "--tables", str(LIVE_TABLES_PATH), *extra])

    def test_pronouns_cannot_be_pinned(self):
        with self.assertRaises(SystemExit) as caught:
            self.run_cli("--set-trait", "Pronouns=she/her/her/woman")
        self.assertIn("Pronouns", str(caught.exception))

    def test_the_halves_of_the_name_cannot_be_pinned(self):
        for trait in ("Given names", "Family names"):
            with self.subTest(trait=trait):
                with self.assertRaises(SystemExit):
                    self.run_cli("--set-trait", "%s=Nobody" % trait)

    def test_a_table_this_script_does_not_roll_is_refused(self):
        with self.assertRaises(SystemExit) as caught:
            self.run_cli("--set-trait", "Ouftit=a typo")
        self.assertIn("Ouftit", str(caught.exception))

    def test_the_refusal_offers_the_list_that_does_work(self):
        with self.assertRaises(SystemExit) as caught:
            self.run_cli("--set-trait", "Pronouns=she/her/her/woman")
        self.assertIn("Outfit", str(caught.exception))


class SetTraitArgumentRules(unittest.TestCase):
    def parse(self, *argv):
        return gen.parse_args(list(argv))

    def test_set_trait_is_allowed_with_regen(self):
        args = self.parse("--regen-manifest", "m.json", "--regen-id", "x",
                          "--set-trait", "Hair=a bob")
        self.assertEqual(args.overrides, {"Hair": "a bob"})

    def test_set_trait_and_reroll_trait_together_are_refused(self):
        with self.assertRaises(SystemExit):
            self.parse("--regen-manifest", "m.json", "--regen-id", "x",
                       "--set-trait", "Hair=a bob", "--reroll-trait", "Hair")

    def test_release_without_set_trait_is_refused(self):
        with self.assertRaises(SystemExit):
            self.parse("--regen-manifest", "m.json", "--regen-id", "x",
                       "--release", "Headgear")

    def test_release_of_a_non_dependent_is_refused(self):
        with self.assertRaises(SystemExit):
            self.parse("--regen-manifest", "m.json", "--regen-id", "x",
                       "--set-trait", "Demeanor=a scowl",
                       "--release", "Backdrop")

    def test_release_of_a_real_dependent_is_accepted(self):
        args = self.parse("--regen-manifest", "m.json", "--regen-id", "x",
                          "--set-trait", "Outfit=a kimono",
                          "--release", "Headgear,Gear")
        self.assertEqual(args.release, ["Headgear", "Gear"])

    def test_count_and_name_are_still_refused_with_regen(self):
        # --set-trait leaving the conflict list must not take the rest with it.
        for flag, value in (("--name", "Someone"), ("--seed", "3"),
                            ("--pronouns", "she/her")):
            with self.subTest(flag=flag):
                with self.assertRaises(SystemExit):
                    self.parse("--regen-manifest", "m.json", "--regen-id", "x",
                               flag, value)


if __name__ == "__main__":
    unittest.main()
