"""Extra JSON tables and disabled default tables.

The markdown tables file is the generator's only roll source, and every one of
its tables has a fixed slot in the prompt templates. Two things sit outside
that: a private set of tables a user keeps in their own JSON files, rolled by
weight and appended to the prompt as one extra sentence; and a switch that
takes a default table's clause OUT of the prompt when a private table already
covers the same ground - a Stance table of their own, say.

Disabling is prompt-only on purpose. The roll still draws the trait, so every
pool filter that reads it (Weapon gates Stance, Backdrop gates Gear) runs
exactly as before and a seed still reproduces the same NPC; only the sentence
is dropped. That is what lets the byte-for-byte promise below hold: an NPC
with nothing disabled and no extra tables renders the prompt it always did.
"""
import contextlib
import io
import json
import random
import tempfile
import unittest
from pathlib import Path

from test.helpers import FIXTURE_TABLES, load_generator, manifest_entry

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)

SET_A = {
    "partner_archetypes": [
        {"value": "tall muscular bodybuilder type", "weight": 1},
        {"value": "average build everyman", "weight": 1},
    ],
    "camera_framing": [
        {"value": "low angle looking up", "weight": 3},
        {"value": "eye level medium shot"},
    ],
}
SET_B = {
    "lighting_mood": [
        {"value": "harsh overhead fluorescent light", "weight": 2},
    ],
}
# The same two tables as SET_A, in the tables file's own markdown format.
SET_A_MD = """# Private tables

Prose between headings is ignored, as it is in the main file.

## partner_archetypes

- tall muscular bodybuilder type
- average build everyman

## camera_framing

- x3 low angle looking up
- eye level medium shot
"""


def write_set(folder, name, data):
    path = Path(folder) / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def roll(seed=3, extra=None, disabled=()):
    npc = gen.roll_npc(TABLES, random.Random(seed), None)
    if extra is not None:
        npc["_extra"] = dict(extra)
    if disabled:
        npc["_disabled"] = tuple(disabled)
    return npc


class TestLoadExtraTables(unittest.TestCase):
    def test_fixed_values_narrow_only_the_selected_table(self):
        extra = gen.load_extra_tables([self.a], values={"camera_framing": "eye level medium shot"})
        self.assertEqual(extra["camera_framing"], [("eye level medium shot", 1)])
        self.assertEqual(len(extra["partner_archetypes"]), 2)
        for seed in range(10):
            self.assertEqual(gen.roll_extra(extra, random.Random(seed))["camera_framing"], "eye level medium shot")

    def test_fixed_values_reject_unknown_or_unselected_tables_and_values(self):
        for only, values in [(None, {"missing": "value"}),
                             (["partner_archetypes"], {"camera_framing": "eye level medium shot"}),
                             (None, {"camera_framing": "not offered"})]:
            with self.assertRaises(ValueError):
                gen.load_extra_tables([self.a], only, values=values)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.a = write_set(self.tmp.name, "a.json", SET_A)
        self.b = write_set(self.tmp.name, "b.json", SET_B)

    def test_every_table_in_every_file_loads_in_file_order(self):
        extra = gen.load_extra_tables([self.a, self.b])
        self.assertEqual(list(extra), ["partner_archetypes", "camera_framing", "lighting_mood"])
        self.assertEqual(extra["partner_archetypes"],
                         [("tall muscular bodybuilder type", 1), ("average build everyman", 1)])

    def test_a_missing_weight_counts_as_one(self):
        extra = gen.load_extra_tables([self.a])
        self.assertEqual(extra["camera_framing"][1], ("eye level medium shot", 1))

    def test_only_narrows_to_the_named_tables_and_keeps_file_order(self):
        extra = gen.load_extra_tables([self.a, self.b], only=["lighting_mood", "partner_archetypes"])
        self.assertEqual(list(extra), ["partner_archetypes", "lighting_mood"])

    def test_naming_a_table_no_file_holds_is_refused(self):
        with self.assertRaisesRegex(ValueError, "no_such_table"):
            gen.load_extra_tables([self.a], only=["no_such_table"])

    def test_a_name_that_collides_with_a_default_table_is_refused(self):
        clash = write_set(self.tmp.name, "clash.json", {"Stance": [{"value": "x", "weight": 1}]})
        with self.assertRaisesRegex(ValueError, "Stance"):
            gen.load_extra_tables([clash])

    def test_the_same_table_in_two_files_is_refused(self):
        again = write_set(self.tmp.name, "again.json", {"lighting_mood": [{"value": "y"}]})
        with self.assertRaisesRegex(ValueError, "lighting_mood"):
            gen.load_extra_tables([self.b, again])

    def test_malformed_files_name_the_file_and_the_problem(self):
        cases = {
            "list.json": [1, 2],
            "empty-table.json": {"t": []},
            "bad-row.json": {"t": ["just a string"]},
            "blank-value.json": {"t": [{"value": "   ", "weight": 1}]},
            "zero-weight.json": {"t": [{"value": "v", "weight": 0}]},
            "text-weight.json": {"t": [{"value": "v", "weight": "heavy"}]},
            "blank-name.json": {"  ": [{"value": "v"}]},
        }
        for name, data in cases.items():
            path = write_set(self.tmp.name, name, data)
            with self.subTest(file=name):
                with self.assertRaisesRegex(ValueError, name):
                    gen.load_extra_tables([path])

    def test_a_file_that_is_not_json_names_itself(self):
        path = Path(self.tmp.name) / "broken.json"
        path.write_text("{not json", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "broken.json"):
            gen.load_extra_tables([path])

    def test_a_missing_file_names_itself(self):
        with self.assertRaisesRegex(ValueError, "missing.json"):
            gen.load_extra_tables([Path(self.tmp.name) / "missing.json"])

    def test_a_markdown_file_loads_the_same_as_its_json_twin(self):
        md = Path(self.tmp.name) / "a.md"
        md.write_text(SET_A_MD, encoding="utf-8")
        self.assertEqual(gen.load_extra_tables([md]), gen.load_extra_tables([self.a]))
        self.assertEqual(gen.load_extra_tables([md])["camera_framing"],
                         [("low angle looking up", 3), ("eye level medium shot", 1)])

    def test_a_markdown_bullet_is_taken_whole(self):
        md = Path(self.tmp.name) / "flags.md"
        md.write_text("## t\n\n- a value || flag\n", encoding="utf-8")
        self.assertEqual(gen.load_extra_tables([md])["t"], [("a value || flag", 1)])

    def test_a_markdown_file_with_no_tables_is_refused_by_name(self):
        md = Path(self.tmp.name) / "prose.md"
        md.write_text("# Nothing here\n\nJust prose.\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "prose.md"):
            gen.load_extra_tables([md])

    def test_markdown_and_json_files_mix_in_one_run(self):
        md = Path(self.tmp.name) / "b.md"
        md.write_text("## lighting_mood\n\n- x2 harsh overhead fluorescent light\n", encoding="utf-8")
        self.assertEqual(gen.load_extra_tables([self.a, md]), gen.load_extra_tables([self.a, self.b]))

    def test_any_other_extension_is_refused(self):
        other = Path(self.tmp.name) / "tables.txt"
        other.write_text("## t\n- v\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "tables.txt"):
            gen.load_extra_tables([other])


class TestRollExtra(unittest.TestCase):
    def test_one_value_per_table_in_table_order(self):
        extra = {"a": [("a1", 1)], "b": [("b1", 1), ("b2", 1)]}
        rolled = gen.roll_extra(extra, random.Random(1))
        self.assertEqual(list(rolled), ["a", "b"])
        self.assertEqual(rolled["a"], "a1")
        self.assertIn(rolled["b"], ("b1", "b2"))

    def test_the_same_seed_rolls_the_same_values(self):
        extra = {"b": [("b1", 1), ("b2", 1), ("b3", 1)]}
        first = [gen.roll_extra(extra, random.Random(s))["b"] for s in range(50)]
        again = [gen.roll_extra(extra, random.Random(s))["b"] for s in range(50)]
        self.assertEqual(first, again)
        self.assertGreater(len(set(first)), 1)

    def test_weight_is_honoured(self):
        extra = {"b": [("rare", 1), ("common", 1000)]}
        rolled = [gen.roll_extra(extra, random.Random(s))["b"] for s in range(200)]
        self.assertGreater(rolled.count("common"), 190)

    def test_an_empty_set_rolls_nothing(self):
        self.assertEqual(gen.roll_extra({}, random.Random(1)), {})


class TestExtraSentence(unittest.TestCase):
    def test_no_extra_means_no_change_to_the_prompt(self):
        plain = gen.build_prompts(roll())
        with_keys = gen.build_prompts(roll(extra={}, disabled=()))
        self.assertEqual(plain, with_keys)

    def test_values_are_appended_as_one_sentence_in_both_prompts(self):
        npc = roll(extra={"a": "tall muscular bodybuilder type", "b": "low angle looking up"})
        for prompt in gen.build_prompts(npc):
            self.assertIn("Tall muscular bodybuilder type, low angle looking up. ", prompt)

    def test_the_sentence_follows_the_carry_line_and_precedes_the_scene(self):
        npc = roll(extra={"a": "low angle looking up"})
        portrait, token = gen.build_prompts(npc)
        scene = gen.split_backdrop(npc["Backdrop"])[1]
        self.assertLess(portrait.index("Low angle looking up."), portrait.index(scene))
        self.assertLess(portrait.index("face carries"), portrait.index("Low angle looking up."))
        self.assertLess(token.index("Low angle looking up."), token.index("both feet in frame"))

    def test_a_value_that_already_ends_in_a_period_is_not_doubled(self):
        npc = roll(extra={"a": "low angle looking up."})
        self.assertIn("Low angle looking up. ", gen.build_prompts(npc)[0])
        self.assertNotIn("up.. ", gen.build_prompts(npc)[0])


class TestDisabledTables(unittest.TestCase):
    def test_nothing_disabled_renders_the_figure_sentence_exactly(self):
        """The byte-for-byte pin: the rebuilt list IS the template's sentence."""
        for seed in range(40):
            npc = roll(seed=seed)
            fields = dict(npc["_pronouns"], height=npc["Height"], build=npc["Build"],
                          face=gen.FACE[npc["_young"]], skin=npc["Skin"], hair=npc["Hair"],
                          eyes=npc["Eyes"], feature=npc["Feature"], outfit=npc["Outfit"],
                          traits=gen.GENDER_TRAITS.get(npc["_pronouns"]["gender"], ""),
                          faction_line="a visual, ")
            self.assertEqual(gen.figure_sentence(fields, ()),
                             gen.FIGURE_SENTENCE.format(**fields))

    def test_the_disableable_set_is_the_descriptive_tables(self):
        for name in gen.DISABLEABLE_TABLES:
            self.assertIn(name, gen.REQUIRED_TABLES)
        for structural in ("Given names", "Family names", "Callsigns", "Pronouns",
                           "Theme", "Age", "Role", "Backdrop", "Glow placement",
                           "Hair colour"):
            self.assertNotIn(structural, gen.DISABLEABLE_TABLES)
        for name in ("Stance", "Weapon", "Gear", "Outfit", "Height", "Demeanor"):
            self.assertIn(name, gen.DISABLEABLE_TABLES)

    def assertClean(self, prompt):
        for bad in (", ,", ",,", "  ", " .", ", and ,", "and , ", " , "):
            self.assertNotIn(bad, prompt, prompt)

    def test_disabling_changes_the_prompt_not_the_roll(self):
        plain, off = roll(), roll(disabled=("Stance",))
        self.assertEqual({k: v for k, v in plain.items() if not k.startswith("_")},
                         {k: v for k, v in off.items() if not k.startswith("_")})
        self.assertNotEqual(gen.build_prompts(plain), gen.build_prompts(off))

    def test_stance_leaves_the_token(self):
        npc = roll(disabled=("Stance",))
        portrait, token = gen.build_prompts(npc)
        self.assertNotIn(npc["Stance"], token)
        self.assertNotIn("both feet in frame", token)
        self.assertEqual(portrait, gen.build_prompts(roll())[0])
        self.assertClean(token)

    def test_each_descriptive_table_drops_its_own_clause(self):
        for name in gen.DISABLEABLE_TABLES:
            npc = roll(seed=7, disabled=(name,))
            value = npc[name]
            if name == "Faction":
                value = gen.split_faction(npc[name])[1]
            if name == "Weather":
                value = gen.split_flags(npc[name])[0]
            if not value:
                continue
            with self.subTest(table=name):
                for prompt in gen.build_prompts(npc):
                    self.assertNotIn(value, prompt)
                    self.assertClean(prompt)

    def test_outfit_takes_the_wearing_clause_and_the_faction_visual_with_it(self):
        npc = roll(disabled=("Outfit",))
        for prompt in gen.build_prompts(npc):
            self.assertNotIn("wearing", prompt)
            self.assertNotIn("clothing following", prompt)
            self.assertNotIn(gen.split_faction(npc["Faction"])[1], prompt)
            self.assertClean(prompt)

    def test_the_figure_list_closes_up_around_a_gap(self):
        npc = roll(disabled=("Build",))
        portrait = gen.build_prompts(npc)[0]
        subject = npc["_pronouns"]["Subject"]
        self.assertIn("%s %s %s, " % (subject, npc["_pronouns"]["is_are"], npc["Height"]), portrait)
        self.assertClean(portrait)

    def test_every_figure_table_off_leaves_only_the_wearing_clause(self):
        npc = roll(disabled=("Height", "Build", "Skin", "Hair", "Eyes", "Feature"))
        portrait = gen.build_prompts(npc)[0]
        fields = npc["_pronouns"]
        self.assertIn("%s %s wearing %s" % (fields["Subject"], fields["is_are"], npc["Outfit"]), portrait)
        self.assertClean(portrait)

    def test_every_figure_table_and_outfit_off_drops_the_sentence(self):
        npc = roll(disabled=("Height", "Build", "Skin", "Hair", "Eyes", "Feature", "Outfit",
                             "Headgear"))
        portrait = gen.build_prompts(npc)[0]
        fields = npc["_pronouns"]
        self.assertNotIn("%s %s ," % (fields["Subject"], fields["is_are"]), portrait)
        self.assertNotIn("lighting. %s %s wearing" % (fields["Subject"], fields["is_are"]), portrait)
        self.assertIn("lighting. %s face carries" % fields["Possessive"], portrait)
        self.assertClean(portrait)

    def test_weapon_and_gear_off_drop_the_carry_sentence(self):
        npc = roll(disabled=("Weapon", "Gear"))
        for prompt in gen.build_prompts(npc):
            self.assertNotIn("carries", prompt.split("face carries")[1])
            self.assertClean(prompt)

    def test_glow_colour_off_falls_back_to_the_no_glow_palette_line(self):
        npc = roll(disabled=("Glow colour",))
        for prompt in gen.build_prompts(npc):
            self.assertNotIn(npc["Glow colour"], prompt)
            self.assertIn("Keep the", prompt)
            self.assertClean(prompt)

    def test_all_disableable_tables_off_at_once_still_renders_cleanly(self):
        for seed in range(30):
            npc = roll(seed=seed, disabled=tuple(gen.DISABLEABLE_TABLES))
            for prompt in gen.build_prompts(npc):
                self.assertClean(prompt)
                self.assertIn(npc["Role"], prompt)


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.a = write_set(self.tmp.name, "a.json", SET_A)

    def run_main(self, *extra_argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = gen.main(["--tables", str(FIXTURE_TABLES), "--dry-run", "--seed", "5",
                             "--out", self.tmp.name] + list(extra_argv))
        return code, out.getvalue()

    def test_extra_tables_reach_the_dry_run_prompts(self):
        code, out = self.run_main("--extra-tables", str(self.a))
        self.assertEqual(code, 0)
        self.assertTrue(any(v["value"] in out.lower() for v in SET_A["partner_archetypes"]), out)
        self.assertTrue(any(v["value"] in out.lower() for v in SET_A["camera_framing"]), out)

    def test_extra_table_narrows_the_set(self):
        code, out = self.run_main("--extra-tables", str(self.a), "--extra-table", "camera_framing")
        self.assertEqual(code, 0)
        self.assertFalse(any(v["value"] in out.lower() for v in SET_A["partner_archetypes"]), out)

    def test_extra_value_reaches_every_dry_run_prompt(self):
        code, out = self.run_main("--extra-tables", str(self.a), "--count", "3",
                                  "--extra-value", "camera_framing=eye level medium shot")
        self.assertEqual(code, 0)
        self.assertEqual(out.lower().count("eye level medium shot"), 6)
        self.assertNotIn("low angle looking up", out.lower())

    def test_extra_value_refuses_invalid_cli_choices(self):
        for choice in ("missing separator", "camera_framing=", "camera_framing=not offered"):
            with self.subTest(choice=choice), self.assertRaises(SystemExit):
                self.run_main("--extra-tables", str(self.a), "--extra-value", choice)

    def test_extra_tables_do_not_move_the_base_roll(self):
        _, plain = self.run_main()
        _, with_extra = self.run_main("--extra-tables", str(self.a))
        name = plain.splitlines()[3]
        self.assertEqual(name, with_extra.splitlines()[3])

    def test_disable_table_drops_the_clause(self):
        _, plain = self.run_main()
        _, off = self.run_main("--disable-table", "Stance")
        self.assertIn("both feet in frame", plain)
        self.assertNotIn("both feet in frame", off)

    def test_disable_table_refuses_a_structural_or_unknown_table(self):
        for name in ("Role", "Nope"):
            with self.subTest(table=name):
                with self.assertRaises(SystemExit) as caught:
                    self.run_main("--disable-table", name)
                self.assertIn(name, str(caught.exception))
                self.assertIn("Stance", str(caught.exception))

    def test_a_bad_extra_file_is_a_clean_exit_not_a_traceback(self):
        bad = Path(self.tmp.name) / "bad.json"
        bad.write_text("{", encoding="utf-8")
        with self.assertRaises(SystemExit) as caught:
            self.run_main("--extra-tables", str(bad))
        self.assertIn("bad.json", str(caught.exception))


class TestManifestRoundTrip(unittest.TestCase):
    def test_persist_writes_extra_and_disabled_only_when_present(self):
        npc = roll()
        entry = {}
        gen.persist_traits(entry, npc)
        self.assertNotIn("extraTraits", entry)
        self.assertNotIn("disabledTables", entry)
        npc = roll(extra={"a": "v"}, disabled=("Stance",))
        gen.persist_traits(entry, npc)
        self.assertEqual(entry["extraTraits"], {"a": "v"})
        self.assertEqual(entry["disabledTables"], ["Stance"])
        self.assertNotIn("_extra", entry["traits"])

    def test_npc_from_entry_restores_them(self):
        entry = manifest_entry(seed=2)
        entry["extraTraits"] = {"a": "v"}
        entry["disabledTables"] = ["Stance", "Weapon"]
        npc = gen.npc_from_entry(entry, entry["id"], warn=False)
        self.assertEqual(npc["_extra"], {"a": "v"})
        self.assertEqual(npc["_disabled"], ("Stance", "Weapon"))
        token = gen.build_prompts(npc)[1]
        self.assertIn("V. ", token)
        self.assertNotIn("both feet in frame", token)

    def test_a_legacy_entry_has_neither(self):
        npc = gen.npc_from_entry(manifest_entry(seed=2), "x", warn=False)
        self.assertEqual(npc.get("_extra"), {})
        self.assertEqual(npc.get("_disabled"), ())

    def test_a_raw_reroll_keeps_them(self):
        npc = roll(extra={"a": "v"}, disabled=("Stance",))
        gen.reroll_from_raw(TABLES, npc, {"Hair"}, random.Random(9))
        self.assertEqual(npc["_extra"], {"a": "v"})
        self.assertEqual(npc["_disabled"], ("Stance",))


class TestDossier(unittest.TestCase):
    def test_extra_traits_and_disabled_marks_are_written(self):
        npc = roll(extra={"camera_framing": "low angle looking up"}, disabled=("Stance",))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.md"
            gen.write_dossier(path, npc, 1, gen.build_prompts(npc), [])
            text = path.read_text(encoding="utf-8")
        self.assertIn("| camera_framing | low angle looking up |", text)
        self.assertIn("| Token stance | %s (disabled) |" % npc["Stance"], text)


if __name__ == "__main__":
    unittest.main()
