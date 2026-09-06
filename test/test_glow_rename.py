"""The Accent -> Glow colour rename must not break stored manifest entries.

All 135 entries in .generated-npcs.json store the trait under 'Accent', and
--regen-manifest rebuilds an NPC from that stored dict rather than re-rolling.
A bare rename would raise KeyError in build_prompts() for every one of them.
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

from test.helpers import FIXTURE_TABLES, REPO, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)


class TestLegacyTraitNames(unittest.TestCase):
    def test_a_stored_accent_becomes_a_glow_colour(self):
        migrated = gen.migrate_traits({"Accent": "amber", "Role": "a dockworker"})
        self.assertEqual(migrated["Glow colour"], "amber")
        self.assertNotIn("Accent", migrated)

    def test_an_entry_already_using_the_new_name_is_untouched(self):
        migrated = gen.migrate_traits({"Glow colour": "teal-green"})
        self.assertEqual(migrated["Glow colour"], "teal-green")

    def test_a_new_name_present_alongside_the_old_one_wins(self):
        """Belt and braces: never clobber a current value with a stale one."""
        migrated = gen.migrate_traits({"Accent": "amber", "Glow colour": "teal-green"})
        self.assertEqual(migrated["Glow colour"], "teal-green")

    def test_the_input_dict_is_not_mutated(self):
        original = {"Accent": "amber"}
        gen.migrate_traits(original)
        self.assertEqual(original, {"Accent": "amber"})

    def test_the_table_is_named_glow_colour_in_required_tables(self):
        self.assertIn("Glow colour", gen.REQUIRED_TABLES)
        self.assertNotIn("Accent", gen.REQUIRED_TABLES)


class TestFactionShapeMigration(unittest.TestCase):
    """A manifest entry rolled before Task 7 stored Faction as a single
    segment - the whole value was the visual clause, with no '||' anywhere
    in it, because that split didn't exist yet. migrate_traits() has to
    recognize that shape and restore it, the same job it already does for a
    renamed key, or regenerate_one()'s promise of an identical prompt breaks
    silently for every entry rolled before the split.

    A genuinely pre-split entry predates the Accent -> Glow colour rename
    too, since that rename shipped earlier in the same branch - so these
    fixtures store 'Accent', not 'Glow colour', the same as every one of the
    135 real entries in .generated-npcs.json. See TestSetTraitFactionIsLeftAlone
    below for the shape that must NOT be repaired.
    """

    def _stored_traits(self, faction):
        """A traits dict shaped like one stored manifest entry, Faction aside."""
        return {
            "name": "Test Person",
            "Callsigns": "Ghost",
            "Pronouns": "she/her/her/woman",
            "Role": "a mercenary squad lead",
            "Faction": faction,
            "Age": "in her thirties",
            "Height": "of average height",
            "Build": "lean and wiry",
            "Skin": "pale skin",
            "Hair": "a short black crop",
            "Eyes": "grey eyes",
            "Feature": "a scar across one cheek",
            "Demeanor": "a flat stare",
            "Outfit": "grey coveralls",
            "Headgear": "{Subject} {is_are} bare-headed.",
            "Weapon": "",
            "Gear": "a canvas tool roll at the hip",
            "Accent": "teal-green",
            "Backdrop": "A half-body character portrait || Behind {object} is a plain wall.",
            "Stance": "standing squarely",
        }

    def test_a_single_segment_faction_still_reaches_the_clothing_sentence(self):
        """The pre-Task-7 shape: the whole value WAS the visual clause, which
        the old template dropped straight into the clothing sentence between
        {outfit} and the clause about the frame, with {faction} substituted
        raw. Regeneration has to still place that same faction clause in that
        same position - the clothing clause itself has since taken the
        possessive determiner, so only its own wording has moved on.
        """
        old_faction = "in IPS-Northstar workwear, riveted and salt-stained"
        npc = gen.migrate_traits(self._stored_traits(old_faction))
        npc["_pronouns"] = gen.pronoun_fields(npc["Pronouns"])
        npc["_young"] = False
        portrait, token = gen.build_prompts(npc)
        possessive = npc["_pronouns"]["possessive"]
        expected = "wearing %s, %s, %s clothing following the shape of %s frame." % (
            npc["Outfit"], old_faction, possessive, possessive)
        for prompt in (portrait, token):
            self.assertIn(expected, prompt)

    def test_the_migrated_value_still_carries_no_flags(self):
        """The old shape never carried flags either - filter_by_mil() only
        ever ran on the un-rolled pool, and a stored entry is a finished
        roll - so the migration shouldn't invent any.
        """
        npc = gen.migrate_traits(self._stored_traits("unaligned and freelance"))
        self.assertEqual(gen.split_faction(npc["Faction"])[2], ())

    def test_an_already_split_faction_is_left_alone(self):
        """A '||' anywhere in the stored value means this entry was rolled
        after Task 7 and needs no help - migrating it again would double up
        the visual clause.
        """
        npc = gen.migrate_traits(
            self._stored_traits("Harrison Armory || sharply pressed || mil"))
        self.assertEqual(npc["Faction"], "Harrison Armory || sharply pressed || mil")


class TestSetTraitFactionIsLeftAlone(unittest.TestCase):
    """`--set-trait Faction="Harrison Armory"` is accepted today and stores
    exactly that bare shape - no '||' anywhere - in a manifest entry that
    already uses the current 'Glow colour' key, since it was rolled after
    both the rename and the Faction split landed. The absence of '||' alone
    cannot tell this apart from a genuine pre-split entry; only the missing
    'Accent' key can. migrate_traits() must leave a bare Faction alone when
    the entry has no 'Accent' key, rather than doubling it into a fabricated
    visual clause it never had.
    """

    def test_a_bare_faction_with_no_accent_key_is_not_repaired(self):
        migrated = gen.migrate_traits({
            "Glow colour": "teal-green",
            "Faction": "Harrison Armory",
        })
        self.assertEqual(migrated["Faction"], "Harrison Armory")

    def test_a_bare_faction_with_no_glow_colour_or_accent_is_not_repaired(self):
        """Same gate, for an entry that predates Glow colour/Accent both -
        impossible in practice (Glow colour is a REQUIRED_TABLES entry every
        roll writes), but the gate should fail closed either way."""
        migrated = gen.migrate_traits({"Faction": "Harrison Armory"})
        self.assertEqual(migrated["Faction"], "Harrison Armory")


class TestRawTraitsGetTheRenameToo(unittest.TestCase):
    """rename_legacy_traits() - the one job of migrate_traits()'s three that
    also applies to a stored rawTraits dict.

    A raw bullet is unrendered text: the Faction repair recognises a
    rendered value with no '||', and the Headgear backfill invents a
    rendered sentence, so neither belongs on rawTraits. But a key
    LEGACY_TRAIT_NAMES has renamed is exactly as stale there as it is in
    traits - Accent -> Glow colour predates this branch, and the next rename
    would otherwise leave a re-roll pinning a raw bullet under a key nothing
    reads any more, silently rolling that trait free with only the
    "recorded no raw bullet for" warning to notice.
    """

    def test_a_stored_accent_becomes_a_glow_colour(self):
        renamed = gen.rename_legacy_traits(
            {"Accent": "amber || none", "Role": "a dockworker || civ"})
        self.assertEqual(renamed["Glow colour"], "amber || none")
        self.assertNotIn("Accent", renamed)

    def test_an_entry_already_using_the_new_name_is_untouched(self):
        renamed = gen.rename_legacy_traits({"Glow colour": "teal-green || none"})
        self.assertEqual(renamed["Glow colour"], "teal-green || none")

    def test_a_new_name_present_alongside_the_old_one_wins(self):
        renamed = gen.rename_legacy_traits(
            {"Accent": "amber || none", "Glow colour": "teal-green || none"})
        self.assertEqual(renamed["Glow colour"], "teal-green || none")

    def test_the_input_dict_is_not_mutated(self):
        original = {"Accent": "amber || none"}
        gen.rename_legacy_traits(original)
        self.assertEqual(original, {"Accent": "amber || none"})

    def test_migrate_traits_and_rename_legacy_traits_agree(self):
        """Whichever of the two a caller reaches for, a legacy key comes out
        under the same current name - they share one rename rather than two
        that could drift apart."""
        raw = {"Accent": "amber || none"}
        self.assertEqual(gen.rename_legacy_traits(raw)["Glow colour"],
                         gen.migrate_traits(raw)["Glow colour"])


class TestAStoredAccentRawBulletSurvivesARegen(unittest.TestCase):
    """End to end: a manifest entry whose rawTraits still says 'Accent'
    (every one of them does, until the next --regen-manifest run touches
    it) gets read back, re-rolled, and re-saved with the raw bullet under
    'Glow colour' instead - not carried forward under the name nothing else
    in the file still reads.
    """

    def test_the_resaved_rawTraits_uses_the_current_name(self):
        npc = gen.roll_npc(TABLES, random.Random(1), None)
        raw = dict(npc["_raw"])
        glow = raw.pop("Glow colour")
        raw["Accent"] = glow
        entry = {
            "id": "accent-regen-1",
            "seed": 1,
            "workflow": str(REPO / "workflows" / "api" / "Lancer_Scene_Workflow_v1.json"),
            "traits": {k: v for k, v in npc.items() if not k.startswith("_")},
            "rawTraits": raw,
            "young": npc["_young"],
            "outfit_notac": npc["_outfit_notac"],
            "files": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            folder_path = str(Path(tmp) / "out" / "accent-regen")
            manifest_path.write_text(
                json.dumps({folder_path: entry}), encoding="utf-8")
            args = types.SimpleNamespace(
                regen_manifest=manifest_path, regen_id="accent-regen-1",
                reroll_trait="Eyes", new_seed=None, tables=FIXTURE_TABLES,
                no_portrait=True, no_token=True, server=None,
                overrides={}, release=[])
            stub_comfy = types.SimpleNamespace(base="stub://nowhere")
            stderr = io.StringIO()
            with mock.patch.object(gen.art, "find_server", return_value=stub_comfy):
                with contextlib.redirect_stderr(stderr):
                    gen.regenerate_one(args)
            # The load-time symptom the finding names: an un-renamed key is
            # indistinguishable from a table this NPC never recorded a raw
            # bullet for, so Glow colour would print this warning and roll
            # free instead of staying pinned. A value-equality check alone
            # cannot tell "pinned" from "coincidentally re-rolled to the same
            # bullet", so the warning's absence is the assertion that
            # actually discriminates the fix from the bug.
            self.assertNotIn(
                "Glow colour", stderr.getvalue(),
                "a legacy 'Accent' raw bullet was not recognised as Glow "
                "colour's, so it rolled free instead of staying pinned:\n%s"
                % stderr.getvalue())
            saved = json.loads(manifest_path.read_text(encoding="utf-8"))
            saved_raw = saved[folder_path]["rawTraits"]
            self.assertNotIn("Accent", saved_raw,
                             "a legacy 'Accent' raw bullet was carried forward "
                             "under its old name across a regen")
            self.assertEqual(saved_raw["Glow colour"], glow,
                             "the raw bullet's own value should survive the "
                             "rename untouched")


if __name__ == "__main__":
    unittest.main()
