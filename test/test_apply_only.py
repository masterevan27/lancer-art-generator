"""Applying a trait edit to a manifest entry, with and without a render.

Two things are tested here and they are the same thing seen from two sides.

The first is that a PIN is written back at all. --reroll-trait's result has
been persisted since the day it landed; --set-trait's was not, because the
writer at the tail of regenerate_one() gated `traits`/`rawTraits` on the
re-roll's return value and nothing else. Everything else the writer touches -
the seed, the prompts, and the seven derived flag registers a filter reads -
was written unconditionally, so a pinned entry came out of a regen holding the
NEW roll's flags over the OLD roll's bullets. npc_from_entry() reloads those
flags to rebuild the filters the NEXT roll runs against, so the damage is not
that the manifest is stale: it is that the manifest lies, and keeps lying to
every edit made after it.

The second is --apply-only, which exists because that write is the only part
of a regen a user editing traits actually wants. Renders take minutes and the
GUI refuses a second one while the first runs, so trying three haircuts used
to cost the better part of an hour. --apply-only stops at the write, marks the
entry artStale, and prints the result as JSON - so several edits can be stacked
in seconds and one deliberate render made at the end. The entry is the
accumulator; there is no staging state anywhere.

Driven through regenerate_one() rather than rebuilt inline, for the reason
test_reroll_trait.py's TestTheRegenWriterActuallyRuns gives: a test that
reconstructs the writer's dict comprehensions by hand proves the shape is
right and would stay green if the writer were deleted, which is exactly how
the --set-trait gate rotted unnoticed in the first place.
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

from test.helpers import FIXTURE_TABLES, REPO, load_generator, rendered

gen = load_generator()

TABLES = gen.parse_tables(FIXTURE_TABLES)

# A packaged workflow that exists on disk, so resolve_recorded_workflow() and
# locate_slots() succeed for real on the render path instead of raising before
# the writer is reached.
WORKFLOW = REPO / "workflows" / "api" / "Lancer_Scene_Workflow_v1.json"

SEED = 1


class StagedEditHarness(unittest.TestCase):
    """One manifest entry on disk, driven through the real regenerate_one().

    Both render stages are skipped (--no-portrait and --no-token together are
    refused by parse_args, but regenerate_one() itself is happy with them and
    that is what makes the writer reachable), and find_server() is stubbed -
    the one piece of the pipeline no harness reaches without a ComfyUI
    listening. --apply-only returns before all of it, which is its own test
    below.
    """

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.npc = gen.roll_npc(TABLES, random.Random(SEED), None)
        self.manifest_path = Path(self.dir.name) / "manifest.json"
        # Inside the temp dir, so the dossier write and folder.mkdir() on the
        # render path leave nothing behind once the test exits.
        self.folder_path = str(Path(self.dir.name) / "out" / "staged")
        self.entry = {
            "id": "staged-1",
            "kind": "npc",
            "name": self.npc["name"],
            "callsign": self.npc["Callsigns"],
            "seed": SEED,
            "workflow": str(WORKFLOW),
            "traits": {k: v for k, v in self.npc.items() if not k.startswith("_")},
            "rawTraits": dict(self.npc["_raw"]),
            "young": self.npc["_young"],
            "outfit_notac": self.npc["_outfit_notac"],
            "gear_helmet": self.npc["_gear_helmet"],
            # The art half of the entry, filled in rather than left out: what
            # --apply-only must NOT touch cannot be asserted on keys that were
            # never there.
            "portrait": "Test Portrait.png",
            "portraitPrompt": "the stored portrait prompt",
            "token": "Test Token.png",
            "tokenPrompt": "the stored token prompt",
            "files": ["Test Portrait.png", "Test Token.png", "Test.md"],
        }
        self.manifest_path.write_text(
            json.dumps({self.folder_path: self.entry}), encoding="utf-8")

    def saved(self):
        """The entry as it now stands on disk."""
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))[self.folder_path]

    def regen(self, **overrides):
        """regenerate_one() over that entry. Returns (code, stdout, stderr)."""
        args = dict(
            regen_manifest=self.manifest_path, regen_id="staged-1",
            reroll_trait=None, overrides={}, release=[], new_seed=None,
            tables=FIXTURE_TABLES, no_portrait=True, no_token=True,
            server=None, apply_only=False)
        args.update(overrides)
        out, err = io.StringIO(), io.StringIO()
        stub_comfy = types.SimpleNamespace(base="stub://nowhere")
        with mock.patch.object(gen.art, "find_server", return_value=stub_comfy):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = gen.regenerate_one(types.SimpleNamespace(**args))
        return code, out.getvalue(), err.getvalue()

    def other_value_for(self, trait, npc=None):
        """A raw bullet `trait` could take that is not the one it is wearing.

        Read out of trait_choices() rather than named here: a value hardcoded
        from the fixture stops being the OTHER value the moment somebody
        authors a bullet, and a pin that lands back on the stored value cannot
        tell a persisted write from a stale one - the same trap
        TestTheRegenWriterActuallyRuns picks its seed to avoid.
        """
        choices = gen.trait_choices(TABLES, npc or self.npc, trait)
        return next(c["value"] for c in choices
                    if c["allowed"] and not c["current"] and not c["conflicts"])


class APinIsPersisted(StagedEditHarness):
    """The D3 regression: --set-trait on a regen, through the writer."""

    def test_a_pinned_trait_is_persisted_to_the_manifest(self):
        value = self.other_value_for("Outfit")
        code, _, _ = self.regen(overrides={"Outfit": value})
        self.assertEqual(code, 0, "the regen should have completed with both "
                                  "stages skipped")
        saved = self.saved()
        self.assertEqual(
            saved["rawTraits"]["Outfit"], value,
            "regenerate_one() pinned Outfit but did not persist the raw "
            "bullet back to the manifest")
        self.assertIn(
            saved["traits"]["Outfit"], rendered(TABLES, "Outfit", value),
            "the rendered trait should describe the bullet that was pinned")
        self.assertNotEqual(
            saved["traits"]["Outfit"], self.entry["traits"]["Outfit"],
            "the pin landed back on the stored value, so this assertion "
            "cannot tell a persisted write from a stale one")

    def test_a_pin_leaves_the_entry_self_consistent(self):
        """The sharper form, and the one the corruption is really about.

        Asserting entry["outfit_notac"] against npc_from_entry()'s
        npc["_outfit_notac"] would prove nothing - npc_from_entry() reads that
        key straight off the entry, so the two agree whatever was written. The
        question is whether the entry's flags describe the entry's own
        bullets, so both halves are compared against the same pin computed
        independently of regenerate_one().
        """
        value = self.other_value_for("Outfit")
        expected = gen.roll_npc(TABLES, random.Random(SEED), None)
        gen.reroll_from_raw(TABLES, expected, set(), random.Random(SEED),
                            {"Outfit": value})
        self.regen(overrides={"Outfit": value})
        saved = self.saved()
        self.assertEqual(
            saved["outfit_notac"], expected["_outfit_notac"],
            "the flag register should describe the pinned outfit")
        self.assertEqual(
            saved["traits"],
            {k: v for k, v in expected.items() if not k.startswith("_")},
            "the entry's traits should describe the same roll its flags do")

    def test_a_plain_regen_still_rewrites_nothing(self):
        """The other half of the gate. A regen that edits no trait reproduces
        the entry, and rewriting traits it did not touch would just churn the
        manifest - which is why the gate exists rather than being deleted."""
        self.regen()
        saved = self.saved()
        self.assertEqual(saved["traits"], self.entry["traits"])
        self.assertEqual(saved["rawTraits"], self.entry["rawTraits"])


class ApplyOnly(StagedEditHarness):
    """--apply-only: the write without the render."""

    def test_it_writes_the_traits_and_never_contacts_a_server(self):
        value = self.other_value_for("Outfit")
        out, err = io.StringIO(), io.StringIO()
        args = types.SimpleNamespace(
            regen_manifest=self.manifest_path, regen_id="staged-1",
            reroll_trait=None, overrides={"Outfit": value}, release=[],
            new_seed=None, tables=FIXTURE_TABLES,
            # Both stages asked for, so a run that reached the render half
            # would try to render rather than skipping past it.
            no_portrait=False, no_token=False, server=None, apply_only=True)
        # Not a stub: an exception. find_server() being reached at all is the
        # failure, and a stub would let the run continue past it and fail
        # somewhere less legible.
        def boom(*a, **kw):
            raise AssertionError("--apply-only contacted a ComfyUI server")
        with mock.patch.object(gen.art, "find_server", boom):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = gen.regenerate_one(args)
        self.assertEqual(code, 0)
        saved = self.saved()
        self.assertEqual(saved["rawTraits"]["Outfit"], value)
        self.assertIs(saved["artStale"], True,
                      "a staged edit leaves art that no longer matches")

    def test_it_does_not_touch_the_art_keys(self):
        """The entry's seed describes the noise of the STORED image and its
        files describe images on disk. A staged edit makes neither, so it
        claims neither."""
        value = self.other_value_for("Outfit")
        self.regen(apply_only=True, overrides={"Outfit": value})
        saved = self.saved()
        for key in ("seed", "files", "portrait", "token",
                    "portraitPrompt", "tokenPrompt"):
            self.assertEqual(saved[key], self.entry[key], key)

    def test_it_prints_only_json_on_stdout(self):
        """The GUI parses stdout whole, the same contract --trait-choices and
        --trait-odds keep. A cascade report on stdout would break that parse
        for every re-roll that moves more than one trait - which is every
        re-roll of a trait that gates others."""
        code, out, err = self.regen(apply_only=True, reroll_trait="Theme")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["id"], "staged-1")
        self.assertIs(payload["artStale"], True)
        self.assertEqual(payload["traits"], self.saved()["traits"])
        self.assertEqual(payload["rawTraits"], self.saved()["rawTraits"])
        self.assertIn("re-rolled Theme", err)
        self.assertIn("  with ", err,
                      "the cascade report belongs on stderr, where the GUI "
                      "can show it without it reaching the JSON parse")
        self.assertNotIn("with ", out)

    def test_edits_accumulate(self):
        """The user's stated intent, at the generator level: pin one trait,
        re-roll another, pin a third, and render once at the end.

        The three are chosen for disjoint cascades - trait_cascade('Eyes') and
        trait_cascade('Feature') reach nothing else - so anything the later
        edits take with them is a bug rather than the design working.
        """
        outfit = self.other_value_for("Outfit")
        self.regen(apply_only=True, overrides={"Outfit": outfit})
        _, _, err = self.regen(apply_only=True, reroll_trait="Eyes")
        self.assertIn("re-rolled Eyes", err)
        # Against the entry as it now stands, not the NPC this test rolled:
        # two edits have landed since, and asking the stale one which values
        # are open would be asking about a different NPC.
        current = gen.npc_from_entry(self.saved(), "staged-1", warn=False)
        feature = self.other_value_for("Feature", npc=current)
        self.regen(apply_only=True, overrides={"Feature": feature})

        saved = self.saved()
        self.assertEqual(saved["rawTraits"]["Outfit"], outfit,
                         "the first pin did not survive the two edits after it")
        self.assertEqual(saved["rawTraits"]["Feature"], feature)
        self.assertIn(saved["traits"]["Outfit"], rendered(TABLES, "Outfit", outfit))
        self.assertIn(saved["traits"]["Feature"], rendered(TABLES, "Feature", feature))

    def test_a_real_render_clears_the_marker(self):
        """artStale says the stored art no longer matches the stored traits, so
        a render is what ends it. Popped rather than set False, so an entry
        that never staged anything is written exactly as before."""
        value = self.other_value_for("Outfit")
        self.regen(apply_only=True, overrides={"Outfit": value})
        self.assertIs(self.saved()["artStale"], True)
        self.regen()
        self.assertNotIn("artStale", self.saved())


class ApplyOnlyNeedsAnEdit(unittest.TestCase):
    """parse_args' refusals. Every one of them describes a run that would
    otherwise write nothing and report success."""

    def parse(self, *argv):
        """The refusal argparse printed, so a test can read what it said."""
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit):
                gen.parse_args(list(argv))
        return err.getvalue()

    def test_apply_only_alone_is_refused(self):
        self.assertIn(
            "nothing to apply",
            self.parse("--regen-manifest", "m.json", "--regen-id", "x",
                       "--apply-only"))

    def test_apply_only_without_a_regen_is_refused(self):
        self.assertIn(
            "--regen-manifest",
            self.parse("--apply-only", "--reroll-trait", "Outfit"))

    def test_apply_only_with_trait_choices_is_refused(self):
        """And refused by name. --trait-choices carries no edit flag - it is
        refused above for carrying one - so a message about the missing edit
        flag would send the reader off to add one, which is not the cure."""
        self.assertIn(
            "drop --apply-only",
            self.parse("--regen-manifest", "m.json", "--regen-id", "x",
                       "--trait-choices", "Outfit", "--apply-only"))

    def test_apply_only_with_an_edit_is_accepted(self):
        """The negative cases above would all pass against a flag that refused
        everything."""
        args = gen.parse_args([
            "--regen-manifest", "m.json", "--regen-id", "x",
            "--reroll-trait", "Outfit", "--apply-only"])
        self.assertTrue(args.apply_only)

    def test_apply_only_does_not_need_the_render_stages_turned_off(self):
        """--apply-only exits before any render decision is read, so making
        the user also type --no-portrait --no-token would be asking them to
        turn off something that was never going to happen - and those two
        together are refused anyway."""
        args = gen.parse_args([
            "--regen-manifest", "m.json", "--regen-id", "x",
            "--set-trait", "Outfit=a kimono", "--apply-only"])
        self.assertTrue(args.apply_only)
        self.assertFalse(args.no_portrait)
        self.assertFalse(args.no_token)


if __name__ == "__main__":
    unittest.main()
