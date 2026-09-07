"""--apply-only parity and the manifest entry shape, for ships.

Modelled on test/test_apply_only.py, the NPC equivalent written for commit
8e78e07. Driven through regenerate_one() rather than by rebuilding the
writer's dicts inline, for the reason test_reroll_trait.py's
TestTheRegenWriterActuallyRuns gives: a test that reconstructs the writer's
dict comprehensions by hand proves the shape is right and would stay green if
the writer were deleted - which is exactly how the NPC --set-trait gate
rotted unnoticed (generate-npc.py:4273 gated `traits`/`rawTraits` on
`rerolled is not None`, which is never true on a --set-trait path).
generate-spaceship.py's regenerate_one() writes persist_traits()/
persist_size() unconditionally on both edit paths (see its own comment at
:2579-2585), and TestSetTraitPersists below is the ship-side test that would
have caught the NPC bug had it existed there too.

Run against test/fixtures/ship-tables-minimal.md rather than the live tables,
the same choice test_apply_only.py makes for the NPC fixture: fast, and the
fixture's small pools make "another legal value for this trait" easy to find
deterministically.
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

from test.helpers import REPO, load_ship_generator
from test.helpers import manifest_entry as npc_manifest_entry

ship = load_ship_generator()
sp = ship.sp

FIXTURE_TABLES = Path(__file__).resolve().parent / "fixtures" / "ship-tables-minimal.md"
TABLES = ship.parse_tables(FIXTURE_TABLES)

# A packaged workflow that exists on disk, so load_workflow() succeeds for
# real on the render path instead of raising before the writer is reached -
# the same file test_reroll_trait.py's harness uses for the NPC side.
WORKFLOW = REPO / "workflows" / "api" / "Lancer_Scene_Workflow_v1.json"


class TestShipFolders(unittest.TestCase):
    """SHIP_FOLDERS is a complete, filesystem-safe map of every ship type -
    a type added to ship_policy.py without a folder here would file its
    ships under 'Other' with no test noticing."""

    def test_covers_exactly_the_ship_types(self):
        self.assertEqual(set(ship.SHIP_FOLDERS), set(sp.SHIP_TYPES))

    def test_every_folder_name_is_non_empty_and_safe_stable(self):
        for slug, folder in ship.SHIP_FOLDERS.items():
            with self.subTest(slug=slug):
                self.assertTrue(folder.strip(), "%r has an empty folder" % slug)
                self.assertEqual(
                    ship._safe(folder), folder,
                    "%r is not stable under _safe() - it would be written "
                    "under a different name than SHIP_FOLDERS names" % folder)


class TestTheFolderIsTwoLevels(unittest.TestCase):
    """<out>/<Category>/<Name>, so basename(dirname(folder)) recovers the
    category the way the GUI's server.js:1570 does. A flat <out>/<Name>
    layout would file every ship under a category called after the run
    folder, which is exactly the failure the module docstring warns about.

    Calls asset_folder() and ship_category() directly - these ARE the two
    production functions the fresh-roll writer composes for this field, not
    a restatement of them.
    """

    def test_the_category_is_recoverable_from_the_folder(self):
        rolled = ship.roll_ship(TABLES, random.Random(3))
        category = ship.ship_category(rolled)
        with tempfile.TemporaryDirectory() as tmp:
            folder = ship.asset_folder(Path(tmp), rolled["name"], category, False)
            self.assertEqual(Path(folder).parent.name, category)
            self.assertEqual(Path(folder).name, ship._safe(rolled["name"]))


class StagedEditHarness(unittest.TestCase):
    """One ship manifest entry on disk, driven through the real regenerate_one().

    Both render stages are skipped (--no-portrait and --no-token together are
    refused by parse_args, but regenerate_one() itself is happy with them,
    which is what makes the writer reachable without a running ComfyUI), and
    find_server() is stubbed for the same reason test_apply_only.py's harness
    stubs it - the one piece of the pipeline no harness reaches without a
    server listening. --apply-only exits before either matters.
    """

    SEED = 1

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.ship = ship.roll_ship(TABLES, random.Random(self.SEED))
        self.manifest_path = Path(self.dir.name) / "manifest.json"
        # Inside the temp dir, so the dossier write and folder.mkdir() on the
        # render path leave nothing behind once the test exits.
        self.folder_path = str(Path(self.dir.name) / "out" / "staged")
        band = sp.size_of(self.ship["_raw"]["Size"])
        self.entry = dict(
            {
                "id": ship.ship_id(self.ship["name"], self.SEED),
                "kind": "spaceship",
                "name": self.ship["name"],
                "callsign": "TST-0001",
                "seed": self.SEED,
                "traits": {k: v for k, v in self.ship.items()
                          if not k.startswith("_")},
                "rawTraits": dict(self.ship["_raw"]),
                "shipType": sp.ship_type_of(self.ship["_raw"]["Ship type"]),
                "dossier": "%s.md" % ship._safe(self.ship["name"]),
                # The art half of the entry, filled in rather than left out:
                # what --apply-only must NOT touch cannot be asserted on keys
                # that were never there.
                "portrait": "Test Portrait.png",
                "portraitPrompt": "the stored portrait prompt",
                "token": "Test Token.png",
                "tokenPrompt": "the stored token prompt",
                "files": ["Test Portrait.png", "Test Token.png", "Test.md"],
            },
            **ship.token_metadata(band),
        )
        self.manifest_path.write_text(
            json.dumps({self.folder_path: self.entry}), encoding="utf-8")

    def saved(self):
        """The entry as it now stands on disk, read back through the real
        art.load_manifest() rather than a bare json.loads() - every call
        exercises the same round trip the writer's save_manifest() has to
        survive."""
        return ship.art.load_manifest(self.manifest_path)[self.folder_path]

    def regen(self, **overrides):
        """regenerate_one() over that entry. Returns (code, stdout, stderr)."""
        args = dict(
            regen_manifest=self.manifest_path, regen_id=self.entry["id"],
            reroll_trait=None, overrides={}, release=[], new_seed=None,
            tables=FIXTURE_TABLES, workflow=WORKFLOW,
            no_portrait=True, no_token=True, server=None, apply_only=False,
            max_token_px=ship.MAX_TOKEN_PX)
        args.update(overrides)
        out, err = io.StringIO(), io.StringIO()
        stub_comfy = types.SimpleNamespace(base="stub://nowhere")
        with mock.patch.object(ship.art, "find_server", return_value=stub_comfy):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = ship.regenerate_one(types.SimpleNamespace(**args))
        return code, out.getvalue(), err.getvalue()

    def other_value_for(self, trait, ship_dict=None):
        """A raw bullet `trait` could take that is not the one it is wearing,
        and that leaves no dependent trait contradicted - read out of
        trait_choices() rather than named here, the same reason
        test_apply_only.py's version gives: a value hardcoded from the
        fixture stops being the OTHER value the moment somebody edits it."""
        choices = ship.trait_choices(TABLES, ship_dict or self.ship, trait)
        return next(c["value"] for c in choices
                    if c["allowed"] and not c["current"] and not c["conflicts"])


class TestEntryShape(StagedEditHarness):
    """The keys a written entry carries, and the two contracts the GUI's
    importer trusts without checking: the id's shape, and that the five size
    fields are ints rather than strings a JS `+` would silently concatenate.
    """

    REQUIRED_KEYS = ("id", "kind", "name", "callsign", "seed", "traits",
                     "rawTraits", "files", "portrait", "token",
                     "portraitPrompt", "tokenPrompt", "dossier", "when",
                     "sizeBand", "hexes", "gridWidth", "gridHeight",
                     "tokenWidth", "tokenHeight")
    SIZE_FIELDS = ("hexes", "gridWidth", "gridHeight", "tokenWidth", "tokenHeight")

    def test_a_written_entry_carries_every_required_key(self):
        code, _, _ = self.regen()
        self.assertEqual(code, 0, "the regen should complete with both "
                                  "render stages skipped")
        saved = self.saved()
        for key in self.REQUIRED_KEYS:
            with self.subTest(key=key):
                self.assertIn(key, saved)
        self.assertEqual(saved["kind"], "spaceship")

    def test_the_id_matches_the_ships_id_shape(self):
        self.regen()
        self.assertRegex(self.saved()["id"], r"^ship-[a-z0-9-]+-\d+$")

    def test_the_five_size_fields_are_ints(self):
        self.regen()
        saved = self.saved()
        for key in self.SIZE_FIELDS:
            with self.subTest(key=key):
                self.assertIsInstance(saved[key], int)


class TestSetTraitPersists(StagedEditHarness):
    """The D3-shaped regression, on the ship side: --set-trait's pin has to
    reach the manifest. generate-npc.py:4273-4280 gates that write on
    `rerolled is not None`, which a --set-trait path never sets - a pin
    renders and is never persisted. This is the test that would have caught
    that bug here, had ships shared the gate; they do not (see the writer's
    own comment at :2579-2585), and this is what proves it.

    Detail is the trait exercised throughout: TRAIT_DEPENDENTS["Detail"] is
    (), so trait_choices() never has to reason about a downstream conflict
    and "allowed, not current" is the whole of what makes a candidate usable.
    """

    def test_a_pinned_trait_is_persisted_to_the_manifest(self):
        value = self.other_value_for("Detail")
        code, _, _ = self.regen(overrides={"Detail": value})
        self.assertEqual(code, 0)
        saved = self.saved()
        self.assertEqual(
            saved["rawTraits"]["Detail"], value,
            "regenerate_one() pinned Detail but did not persist the raw "
            "bullet back to the manifest")
        self.assertEqual(saved["traits"]["Detail"], ship.split_flags(value)[0])
        self.assertNotEqual(
            saved["traits"]["Detail"], self.entry["traits"]["Detail"],
            "the pin landed back on the stored value, so this assertion "
            "cannot tell a persisted write from a stale one")

    def test_apply_only_persists_the_pin_too(self):
        value = self.other_value_for("Detail")
        code, _, _ = self.regen(apply_only=True, overrides={"Detail": value})
        self.assertEqual(code, 0)
        saved = self.saved()
        self.assertEqual(saved["rawTraits"]["Detail"], value)
        self.assertEqual(saved["traits"]["Detail"], ship.split_flags(value)[0])

    def test_a_plain_regen_still_rewrites_nothing(self):
        """The other half of the writer's own gate reasoning: a regen that
        edits no trait reproduces the entry exactly."""
        self.regen()
        saved = self.saved()
        self.assertEqual(saved["traits"], self.entry["traits"])
        self.assertEqual(saved["rawTraits"], self.entry["rawTraits"])


class TestApplyOnlyContract(StagedEditHarness):
    """--apply-only: the write without the render, and its three promises -
    no server contact, JSON-only stdout, and artStale POPPED (not set False)
    by the render that follows - parity with generate-npc.py commit 8e78e07.
    """

    def test_it_never_contacts_a_server(self):
        value = self.other_value_for("Detail")
        args = dict(
            regen_manifest=self.manifest_path, regen_id=self.entry["id"],
            reroll_trait=None, overrides={"Detail": value}, release=[],
            new_seed=None, tables=FIXTURE_TABLES, workflow=WORKFLOW,
            # Both stages asked for, so a run that reached the render half
            # would try to render rather than skipping past it.
            no_portrait=False, no_token=False, server=None, apply_only=True,
            max_token_px=ship.MAX_TOKEN_PX)

        def boom(*a, **kw):
            raise AssertionError("--apply-only contacted a ComfyUI server")

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(ship.art, "find_server", boom):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = ship.regenerate_one(types.SimpleNamespace(**args))
        self.assertEqual(code, 0)
        self.assertEqual(self.saved()["rawTraits"]["Detail"], value)

    def test_it_sets_artstale_true(self):
        value = self.other_value_for("Detail")
        self.regen(apply_only=True, overrides={"Detail": value})
        self.assertIs(self.saved()["artStale"], True,
                      "a staged edit leaves art that no longer matches")

    def test_a_real_render_pops_artstale_rather_than_setting_it_false(self):
        value = self.other_value_for("Detail")
        self.regen(apply_only=True, overrides={"Detail": value})
        self.assertIn("artStale", self.saved())
        self.regen()   # a plain regen: the real (skipped-stage) render path
        self.assertNotIn(
            "artStale", self.saved(),
            "artStale should be popped, not set to False - an entry that "
            "never staged anything must come back looking exactly as it did")

    def test_stdout_is_pure_json_diagnostics_go_to_stderr(self):
        code, out, err = self.regen(apply_only=True, reroll_trait="Command bridge")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["id"], self.entry["id"])
        self.assertIs(payload["artStale"], True)
        self.assertEqual(payload["traits"], self.saved()["traits"])
        self.assertEqual(payload["rawTraits"], self.saved()["rawTraits"])
        self.assertIn("re-rolled Command bridge", err)
        self.assertNotIn("re-rolled", out)

    def test_it_does_not_touch_the_art_keys(self):
        """The entry's seed describes the noise of the STORED image and its
        files describe images on disk. A staged edit makes neither, so it
        claims neither."""
        value = self.other_value_for("Detail")
        self.regen(apply_only=True, overrides={"Detail": value})
        saved = self.saved()
        for key in ("seed", "files", "portrait", "token",
                   "portraitPrompt", "tokenPrompt"):
            self.assertEqual(saved[key], self.entry[key], key)


class TestSizeReDerivation(StagedEditHarness):
    """sizeBand/gridWidth/gridHeight/tokenWidth/tokenHeight are re-derived
    from the CURRENT '## Size' trait after an edit, not carried over from
    what the entry had before it - persist_size()'s whole reason to exist.

    Seed 2 rather than the harness default: it rolls a 'stealth' hull, one of
    the fixture's multi-band types (small, medium), so a --set-trait Size=
    has somewhere else to land. Seed 1's patrol boat has only one legal band
    and could not exercise a real change.
    """

    SEED = 2

    def test_a_set_trait_size_change_updates_every_derived_field(self):
        old_band = sp.size_of(self.ship["_raw"]["Size"])
        slug = sp.ship_type_of(self.ship["_raw"]["Ship type"])
        target = next(b for b in TABLES["Size"]
                      if sp.size_of(b) != old_band and sp.size_of(b) in sp.sizes_for(slug))
        new_band = sp.size_of(target)
        self.assertNotEqual(
            old_band, new_band,
            "the fixture needs two legal bands for %r to exercise this" % slug)

        code, _, _ = self.regen(apply_only=True, overrides={"Size": target})
        self.assertEqual(code, 0)
        saved = self.saved()
        expected = ship.token_metadata(new_band)
        for key, value in expected.items():
            with self.subTest(key=key):
                self.assertEqual(saved[key], value)
        # And genuinely different from the stored entry, so this could not
        # pass on a persist_size() that never ran at all.
        self.assertNotEqual(saved["gridWidth"], self.entry["gridWidth"])
        self.assertNotEqual(saved["sizeBand"], self.entry["sizeBand"])


class TestManifestRoundTrip(StagedEditHarness):
    """Ships share .generated-npcs.json with NPCs (kind:"spaceship" beside
    kind:"npc"), and a ship regen must not disturb an NPC entry sitting in
    the same file. Driven through a real regen rather than a bare
    save/load, so this is the writer's own round trip, not a re-statement of
    art.save_manifest()/load_manifest()'s contract.
    """

    def setUp(self):
        super().setUp()
        self.npc_folder_path = str(Path(self.dir.name) / "out" / "Pilots" / "Windward")
        self.npc_entry = npc_manifest_entry(seed=9)
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        manifest[self.npc_folder_path] = self.npc_entry
        self.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    def test_a_ship_regen_leaves_the_npc_entry_untouched(self):
        value = self.other_value_for("Detail")
        code, _, _ = self.regen(apply_only=True, overrides={"Detail": value})
        self.assertEqual(code, 0)
        loaded = ship.art.load_manifest(self.manifest_path)
        self.assertEqual(set(loaded), {self.folder_path, self.npc_folder_path})
        self.assertEqual(loaded[self.npc_folder_path], self.npc_entry)
        self.assertEqual(loaded[self.folder_path]["kind"], "spaceship")
        self.assertEqual(loaded[self.folder_path]["rawTraits"]["Detail"], value)


if __name__ == "__main__":
    unittest.main()
