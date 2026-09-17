"""Secret prompts: fill-in-the-blank templates for Secret-mode NPCs.

The file format (spec 2), the generator wiring (spec 3) and the content
rules are tested here; the module under test is secret_prompts.py, loaded
as an ordinary import, and generate-npc.py through test.helpers.
"""
import contextlib
import io
import json
import random
import re
import tempfile
import unittest
from pathlib import Path

import secret_prompts as sp
from test.helpers import FIXTURE_TABLES, load_generator, manifest_entry

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)

TABLES_MD = """## Poses

- x2 kneeling upright with knees spread
- lying on her back with legs raised

## Clothing

- completely nude

## Lighting

- soft candlelight
"""

PROMPTS_MD = """# Test prompts
tables: tables.md

## Kneeling
weight: 3
pin: Pronouns = she/her

### portrait
A portrait of {npc:identity}, with {npc:hair}.
{npc:Subject} {npc:is_are} {secret:Poses}, {secret:Clothing}.
{secret:Lighting}.

### token
A full-body figure of {npc:identity}, {secret:Poses}, {secret:Clothing},
against an empty plain white background.

## Plain

### portrait
{{Literal}} braces and {npc:name}

### token
Token of {npc:name}.
"""


class Workspace:
    """A temp folder shaped like prompts/: secret-tables/ beside secret-prompts/."""

    def __init__(self, case, prompts=PROMPTS_MD, tables=TABLES_MD):
        self.tmp = tempfile.TemporaryDirectory()
        case.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.tables_dir = self.root / "secret-tables"
        self.prompts_dir = self.root / "secret-prompts"
        self.tables_dir.mkdir()
        self.prompts_dir.mkdir()
        self.tables = self.write_tables("tables.md", tables)
        self.prompts = self.write_prompts("x.md", prompts)
        self.config = self.root / "config.json"
        self.config.write_text(json.dumps({"secretImagesDir": str(self.root / "private")}), encoding="utf-8")

    def write_tables(self, name, text):
        path = self.tables_dir / name
        path.write_text(text, encoding="utf-8")
        return path

    def write_prompts(self, name, text):
        path = self.prompts_dir / name
        path.write_text(text, encoding="utf-8")
        return path

    def load(self, *paths):
        return sp.load(list(paths) or [self.prompts], None, TABLES, gen.REQUIRED_TABLES, gen.load_extra_tables)


class TestTokens(unittest.TestCase):
    def test_literal_text_and_both_slot_kinds(self):
        self.assertEqual(sp.tokens("A {npc:hair} and {secret:Poses}!"),
                         [("text", "A "), ("npc", "hair"), ("text", " and "), ("secret", "Poses"), ("text", "!")])

    def test_doubled_braces_are_literal(self):
        self.assertEqual(sp.tokens("{{x}} {npc:name}"), [("text", "{x} "), ("npc", "name")])

    def test_names_are_stripped(self):
        self.assertEqual(sp.tokens("{secret: Kneeling Poses }"), [("secret", "Kneeling Poses")])

    def test_stray_and_unknown_braces_are_errors(self):
        for bad in ("a { b", "a } b", "{foo}", "{npc:}", "{secret:x", "{npc:{secret:y}}"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                sp.tokens(bad)

    def test_slots_are_ordered_and_unique(self):
        self.assertEqual(sp.slots("{secret:B} {npc:hair} {secret:A} {secret:B} {npc:hair}"),
                         (["hair"], ["B", "A"]))


class TestParseFile(unittest.TestCase):
    def test_happy_path(self):
        ws = Workspace(self)
        tables, line, templates = sp.parse_file(ws.prompts)
        self.assertEqual(tables, ["tables.md"])
        self.assertEqual(line, 2)
        self.assertEqual([t["name"] for t in templates], ["Kneeling", "Plain"])
        kneeling, plain = templates
        self.assertEqual(kneeling["weight"], 3.0)
        self.assertEqual(kneeling["pin_text"], {"Pronouns": "she/her"})
        self.assertEqual(kneeling["line"], 4)
        self.assertEqual(kneeling["file"], "x.md")
        self.assertEqual(kneeling["secret_slots"], ["Poses", "Clothing", "Lighting"])
        self.assertEqual(kneeling["npc_slots"], ["identity", "hair", "Subject", "is_are"])
        self.assertEqual(plain["weight"], 1.0)
        self.assertEqual(plain["pin_text"], {})
        self.assertEqual(plain["portrait"], "{{Literal}} braces and {npc:name}")

    def test_lines_join_with_single_spaces(self):
        ws = Workspace(self)
        kneeling = sp.parse_file(ws.prompts)[2][0]
        self.assertEqual(kneeling["portrait"],
                         "A portrait of {npc:identity}, with {npc:hair}. "
                         "{npc:Subject} {npc:is_are} {secret:Poses}, {secret:Clothing}. {secret:Lighting}.")
        self.assertEqual(kneeling["token"],
                         "A full-body figure of {npc:identity}, {secret:Poses}, {secret:Clothing}, "
                         "against an empty plain white background.")

    def test_slot_lines_are_recorded_for_error_messages(self):
        ws = Workspace(self)
        kneeling = sp.parse_file(ws.prompts)[2][0]
        self.assertEqual(kneeling["slot_lines"]["Lighting"], 11)
        self.assertEqual(kneeling["slot_lines"]["hair"], 9)

    def assertError(self, text, pattern, name="bad.md"):
        ws = Workspace(self)
        path = ws.write_prompts(name, text)
        with self.assertRaisesRegex(ValueError, pattern):
            sp.parse_file(path)

    def test_every_syntax_error_names_file_template_and_line(self):
        cases = [
            ("stray line\n## A\n### portrait\nx\n### token\ny\n", r"^bad\.md, line 1: "),
            ("## A\nnonsense\n### portrait\nx\n### token\ny\n", r"^bad\.md, 'A', line 2: "),
            ("## A\nweight: nope\n### portrait\nx\n### token\ny\n", r"^bad\.md, 'A', line 2: .*weight"),
            ("## A\nweight: 0\n### portrait\nx\n### token\ny\n", r"^bad\.md, 'A', line 2: .*weight"),
            ("## A\nweight: 1\nweight: 2\n### portrait\nx\n### token\ny\n", r"^bad\.md, 'A', line 3: .*weight"),
            ("## A\npin: nonsense\n### portrait\nx\n### token\ny\n", r"^bad\.md, 'A', line 2: .*pin"),
            ("## A\npin: Age = a\npin: Age = b\n### portrait\nx\n### token\ny\n", r"^bad\.md, 'A', line 3: .*Age"),
            ("## A\n### portrait\nx\n", r"^bad\.md, 'A', line 1: .*token"),
            ("## A\n### token\nx\n", r"^bad\.md, 'A', line 1: .*portrait"),
            ("## A\n### portrait\nx\n### portrait\ny\n### token\nz\n", r"^bad\.md, 'A', line 4: .*portrait"),
            ("## A\n### portrait\nx\n### token\ny\n### other\nz\n", r"^bad\.md, 'A', line 6: .*other"),
            ("## A\n### portrait\na { b\n### token\ny\n", r"^bad\.md, 'A', line 3: .*brace"),
            ("## A\n### portrait\n{foo}\n### token\ny\n", r"^bad\.md, 'A', line 3: .*\{foo\}"),
            ("## A\n### portrait\n{npc:nope}\n### token\ny\n", r"^bad\.md, 'A', line 3: .*npc:nope"),
            ("## A\n### portrait\nx\n### token\ny\n## A\n### portrait\nx\n### token\ny\n", r"^bad\.md, 'A', line 6: .*already"),
            ("##   \n### portrait\nx\n### token\ny\n", r"^bad\.md, line 1: .*name"),
            ("tables: a.md\ntables: b.md\n## A\n### portrait\nx\n### token\ny\n", r"^bad\.md, line 2: .*tables"),
            ("## A\ntables: a.md\n### portrait\nx\n### token\ny\n", r"^bad\.md, 'A', line 2: "),
            ("## A\n### portrait\n\n### token\ny\n", r"^bad\.md, 'A', line 2: .*empty"),
        ]
        for text, pattern in cases:
            with self.subTest(text=text):
                self.assertError(text, pattern)

    def test_a_title_line_is_ignored_anywhere(self):
        ws = Workspace(self)
        path = ws.write_prompts("t.md", "# Title\n## A\n# another title\n### portrait\nx\n### token\ny\n")
        self.assertEqual(sp.parse_file(path)[2][0]["portrait"], "x")

    def test_a_file_with_no_templates_is_an_error(self):
        self.assertError("# Just a title\n", r"^bad\.md, line 1: .*no templates")


class TestLoad(unittest.TestCase):
    def test_happy_path_resolves_tables_and_pins(self):
        ws = Workspace(self)
        templates = ws.load()
        self.assertEqual(list(templates), ["Kneeling", "Plain"])
        kneeling = templates["Kneeling"]
        self.assertEqual(kneeling["tables"], [str(ws.tables.resolve())])
        self.assertEqual(kneeling["pins"], {"Pronouns": "she/her/her/woman"})
        self.assertEqual(kneeling["path"], ws.prompts.resolve())

    def test_tables_dir_override_and_default(self):
        ws = Workspace(self)
        elsewhere = ws.root / "elsewhere"
        elsewhere.mkdir()
        (elsewhere / "tables.md").write_text(TABLES_MD, encoding="utf-8")
        templates = sp.load([ws.prompts], elsewhere, TABLES, gen.REQUIRED_TABLES, gen.load_extra_tables)
        self.assertEqual(templates["Kneeling"]["tables"], [str((elsewhere / "tables.md").resolve())])

    def test_a_pin_resolves_to_the_raw_bullet_with_its_flags(self):
        ws = Workspace(self)
        path = ws.write_prompts("p.md", "## A\npin: Build = full-figured through the hips\n"
                                        "### portrait\nx\n### token\ny\n")
        self.assertEqual(sp.load([path], None, TABLES, gen.REQUIRED_TABLES, gen.load_extra_tables)["A"]["pins"],
                         {"Build": "full-figured through the hips || figure"})

    def assertLoadError(self, ws, text, pattern, name="bad.md", tables_dir=None):
        path = ws.write_prompts(name, text)
        with self.assertRaisesRegex(ValueError, pattern):
            sp.load([path], tables_dir, TABLES, gen.REQUIRED_TABLES, gen.load_extra_tables)

    def test_context_errors_name_file_template_and_line(self):
        ws = Workspace(self)
        ok = "### portrait\nx\n### token\ny\n"
        cases = [
            ("tables: tables.md\n## A\n### portrait\n{secret:Nope}\n### token\ny\n", r"^bad\.md, 'A', line 4: .*Nope"),
            ("## A\n### portrait\n{secret:Poses}\n### token\ny\n", r"^bad\.md, 'A', line 3: .*tables:"),
            ("tables: missing.md\n## A\n" + ok, r"^bad\.md, line 1: .*missing\.md"),
            ("tables: ../x.md\n## A\n" + ok, r"^bad\.md, line 1: .*escapes"),
            ("## A\npin: Nope = x\n" + ok, r"^bad\.md, 'A', line 2: .*Nope"),
            ("## A\npin: Build = not offered\n" + ok, r"^bad\.md, 'A', line 2: .*not offered"),
            ("## A\npin: Pronouns = he/him\n" + ok, r"^bad\.md, 'A', line 2: .*he/him"),
            ("## A\npin: Age = in {possessive} late teens\n" + ok, r"^bad\.md, 'A', line 2: .*adults only"),
        ]
        for text, pattern in cases:
            with self.subTest(text=text):
                self.assertLoadError(ws, text, pattern)

    def test_a_duplicate_name_across_files_is_an_error_and_nothing_loads(self):
        ws = Workspace(self)
        other = ws.write_prompts("y.md", "## Plain\n### portrait\nx\n### token\ny\n")
        with self.assertRaisesRegex(ValueError, r"^y\.md, 'Plain', line 1: .*x\.md"):
            ws.load(ws.prompts, other)

    def test_a_missing_or_unreadable_tables_file_names_the_prompts_file(self):
        ws = Workspace(self)
        ws.write_tables("broken.json", "{")
        self.assertLoadError(ws, "tables: broken.json\n## A\n### portrait\nx\n### token\ny\n",
                             r"^bad\.md, line 1: .*broken\.json")

    def test_a_backdrop_pin_keeps_its_shot_and_scene(self):
        ws = Workspace(self)
        path = ws.write_prompts("p.md", "## A\npin: Backdrop = A half-body character portrait || "
                                        "Behind {object}, a hangar\n### portrait\nx\n### token\ny\n")
        npc_tables = dict(TABLES, Backdrop=["A half-body character portrait || Behind {object}, a hangar || nogear"])
        self.assertEqual(sp.load([path], None, npc_tables, gen.REQUIRED_TABLES, gen.load_extra_tables)["A"]["pins"],
                         {"Backdrop": "A half-body character portrait || Behind {object}, a hangar || nogear"})

    def test_a_pin_ambiguous_across_variants_is_an_error(self):
        ws = Workspace(self)
        path = ws.write_prompts("p.md", "## A\npin: Hair = long hair\n### portrait\nx\n### token\ny\n")
        npc_tables = dict(TABLES, **{"Hair (she)": ["long hair || a"], "Hair (they)": ["long hair || b"]})
        with self.assertRaisesRegex(ValueError, r"more than one bullet.*long hair \|\| a.*long hair \|\| b"):
            sp.load([path], None, npc_tables, gen.REQUIRED_TABLES, gen.load_extra_tables)

    def test_a_pin_matching_identical_bullets_across_variants_still_resolves(self):
        ws = Workspace(self)
        path = ws.write_prompts("p.md", "## A\npin: Hair = long hair\n### portrait\nx\n### token\ny\n")
        npc_tables = dict(TABLES, **{"Hair (she)": ["long hair || a"], "Hair (they)": ["long hair || a"]})
        self.assertEqual(sp.load([path], None, npc_tables, gen.REQUIRED_TABLES, gen.load_extra_tables)["A"]["pins"],
                         {"Hair": "long hair || a"})


class TestListing(unittest.TestCase):
    def test_listing_reports_each_file_and_marks_broken_ones(self):
        ws = Workspace(self)
        broken = ws.write_prompts("broken.md", "## A\n### portrait\n{npc:nope}\n### token\ny\n")
        data = sp.listing([ws.prompts, broken], None, TABLES, gen.REQUIRED_TABLES, gen.load_extra_tables)
        self.assertEqual(data["dir"], str(ws.prompts_dir.resolve()))
        self.assertEqual([f["file"] for f in data["files"]], ["x.md", "broken.md"])
        self.assertEqual(data["files"][0]["templates"][0], {
            "name": "Kneeling", "weight": 3.0, "pins": {"Pronouns": "she/her"},
            "npcSlots": ["identity", "hair", "Subject", "is_are"],
            "secretSlots": ["Poses", "Clothing", "Lighting"]})
        self.assertNotIn("templates", data["files"][1])
        self.assertRegex(data["files"][1]["error"], r"^broken\.md, 'A', line 3: ")
        json.dumps(data)

    def test_a_cross_file_duplicate_marks_the_later_file(self):
        ws = Workspace(self)
        other = ws.write_prompts("y.md", "## Plain\n### portrait\nx\n### token\ny\n")
        data = sp.listing([ws.prompts, other], None, TABLES, gen.REQUIRED_TABLES, gen.load_extra_tables)
        self.assertIn("templates", data["files"][0])
        self.assertRegex(data["files"][1]["error"], r"^y\.md, 'Plain', line 1: .*x\.md")


FIELDS = dict(gen.pronoun_fields("she/her/her/woman"), identity="a dockworker, a mature adult woman in her thirties",
              hair="a long silver braid", name="Test Subject")
EXTRA = {"Poses": "kneeling upright with knees spread", "Clothing": "completely nude", "Lighting": "soft candlelight"}


class TestFill(unittest.TestCase):
    def test_fills_both_slot_kinds_and_tidies(self):
        text = ("A portrait of {npc:identity}, with {npc:hair}. {npc:Subject} {npc:is_are} {secret:Poses}, "
                "{secret:Clothing}. {secret:Lighting}.")
        self.assertEqual(sp.fill(text, FIELDS, EXTRA),
                         "A portrait of a dockworker, a mature adult woman in her thirties, with a long silver braid. "
                         "She is kneeling upright with knees spread, completely nude. Soft candlelight.")

    def test_a_value_starting_a_sentence_is_capitalised(self):
        self.assertEqual(sp.fill("{secret:Lighting}. {secret:Clothing}! {secret:Poses}? {npc:hair}", FIELDS, EXTRA),
                         "Soft candlelight. Completely nude! Kneeling upright with knees spread? A long silver braid.")
        self.assertEqual(sp.fill("with {npc:hair}", FIELDS, EXTRA), "with a long silver braid.")

    def test_whitespace_collapses(self):
        self.assertEqual(sp.fill("A  portrait\tof   {npc:hair} ,  here .", FIELDS, EXTRA),
                         "A portrait of a long silver braid, here.")

    def test_punctuation_repairs(self):
        self.assertEqual(sp.tidy("one ,. two .. three,. four"), "one. two. three. four.")
        self.assertEqual(sp.tidy("ends with a digit 7"), "ends with a digit 7")
        self.assertEqual(sp.tidy("  padded  "), "padded.")
        self.assertEqual(sp.tidy(""), "")

    def test_values_are_otherwise_verbatim(self):
        self.assertEqual(sp.fill("{secret:Poses}", FIELDS, {"Poses": "Kneeling, ALL caps kept"}),
                         "Kneeling, ALL caps kept.")

    def test_literal_braces_survive(self):
        self.assertEqual(sp.fill("{{Literal}} braces and {npc:name}", FIELDS, EXTRA), "{Literal} braces and Test Subject.")

    def test_a_missing_value_names_the_slot(self):
        with self.assertRaisesRegex(ValueError, "secret:Nope"):
            sp.fill("{secret:Nope}", FIELDS, EXTRA)
        with self.assertRaisesRegex(ValueError, "npc:nope"):
            sp.fill("{npc:nope}", FIELDS, EXTRA)


class TestParts(unittest.TestCase):
    TEXT = "A portrait of {npc:identity}, with {npc:hair}. {secret:Poses}, {secret:Clothing}. {secret:Poses}."

    def test_parts_join_to_the_filled_prompt(self):
        parts = sp.parts(self.TEXT, FIELDS, EXTRA)
        self.assertEqual("".join(p["text"] for p in parts), sp.fill(self.TEXT, FIELDS, EXTRA))

    def test_slot_parts_carry_ids_sources_and_values(self):
        parts = sp.parts(self.TEXT, FIELDS, EXTRA)
        ids = [p["id"] for p in parts]
        self.assertEqual([i for i in ids if not i.startswith("text:")],
                         ["npc:identity", "npc:hair", "secret:Poses", "secret:Clothing", "secret:Poses:2"])
        by_id = {p["id"]: p for p in parts}
        self.assertEqual(by_id["npc:identity"]["sources"], ["Role", "Age", "Pronouns"])
        self.assertEqual(by_id["npc:hair"]["sources"], ["Hair", "Hair colour"])
        self.assertEqual(by_id["secret:Poses"]["sources"], ["Poses"])
        self.assertEqual(by_id["secret:Poses"]["value"], "Kneeling upright with knees spread")
        self.assertEqual(by_id["secret:Poses:2"]["value"], "Kneeling upright with knees spread")
        for part in parts:
            if part["id"].startswith("text:"):
                self.assertEqual(part["sources"], [])
        self.assertEqual(len(set(ids)), len(ids))

    def test_tidy_edits_land_on_the_parts_not_between_them(self):
        parts = sp.parts("{secret:Poses} ,  {npc:hair}", FIELDS, EXTRA)
        self.assertEqual("".join(p["text"] for p in parts), "Kneeling upright with knees spread, a long silver braid.")
        self.assertEqual(parts[-1]["sources"], ["Hair", "Hair colour"])


class TestChoose(unittest.TestCase):
    def setUp(self):
        self.ws = Workspace(self)
        self.templates = self.ws.load()

    def test_a_name_is_looked_up(self):
        self.assertEqual(sp.choose(self.templates, "Plain", 1)["name"], "Plain")

    def test_an_unknown_name_lists_the_choices(self):
        with self.assertRaisesRegex(ValueError, "Kneeling, Plain"):
            sp.choose(self.templates, "Nope", 1)

    def test_random_is_weighted_and_reproducible_per_seed(self):
        picks = [sp.choose(self.templates, "random", seed)["name"] for seed in range(200)]
        self.assertEqual(picks, [sp.choose(self.templates, "random", seed)["name"] for seed in range(200)])
        self.assertGreater(picks.count("Kneeling"), 120)
        self.assertGreater(picks.count("Plain"), 15)

    def test_random_draws_from_its_own_stream(self):
        self.assertEqual(sp.choose(self.templates, "random", 7)["name"],
                         sp.choose(self.templates, "random", "7")["name"])
        expected = random.Random("7:secret-prompt").choices(["Kneeling", "Plain"], [3.0, 1.0])[0]
        self.assertEqual(sp.choose(self.templates, "random", 7)["name"], expected)

    def test_random_with_no_templates_loaded_is_an_error(self):
        with self.assertRaisesRegex(ValueError, "loaded: none"):
            sp.choose({}, "random", 1)


class TestPins(unittest.TestCase):
    def setUp(self):
        self.template = Workspace(self).load()["Kneeling"]

    def test_a_non_pronoun_pin_accepts_an_agreeing_override_and_refuses_a_disagreeing_one(self):
        ws = Workspace(self)
        path = ws.write_prompts("p.md", "## A\npin: Build = full-figured through the hips\n"
                                        "### portrait\nx\n### token\ny\n")
        template = sp.load([path], None, TABLES, gen.REQUIRED_TABLES, gen.load_extra_tables)["A"]
        merged = sp.merge_pins(template, {"Build": "full-figured through the hips || figure"})
        self.assertEqual(merged["Build"], "full-figured through the hips || figure")
        with self.assertRaisesRegex(ValueError, r"full-figured through the hips.*lean and wiry|"
                                                 r"lean and wiry.*full-figured through the hips"):
            sp.merge_pins(template, {"Build": "lean and wiry"})

    def test_pins_merge_into_the_overrides(self):
        merged = sp.merge_pins(self.template, {"Role": "a dockworker"})
        self.assertEqual(merged, {"Role": "a dockworker", "Pronouns": "she/her/her/woman"})

    def test_an_agreeing_override_is_fine(self):
        merged = sp.merge_pins(self.template, {"Pronouns": "she/her/her/woman"})
        self.assertEqual(merged["Pronouns"], "she/her/her/woman")

    def test_a_disagreeing_override_names_both_values(self):
        with self.assertRaisesRegex(ValueError, r"she/her.*they/them/their/person|they/them/their/person.*she/her"):
            sp.merge_pins(self.template, {"Pronouns": "they/them/their/person"})

    def test_the_caller_dict_is_not_mutated(self):
        overrides = {}
        sp.merge_pins(self.template, overrides)
        self.assertEqual(overrides, {})


class TestSnapshot(unittest.TestCase):
    def test_snapshot_holds_the_text_and_the_tables(self):
        ws = Workspace(self)
        snap = sp.snapshot(ws.load()["Kneeling"])
        self.assertEqual(set(snap), {"file", "name", "portrait", "token", "tables"})
        self.assertEqual(snap["file"], "x.md")
        self.assertEqual(snap["name"], "Kneeling")
        self.assertIn("{secret:Poses}", snap["portrait"])
        self.assertEqual(snap["tables"], [str(ws.tables.resolve())])
        self.assertEqual(sp.snapshot_secret_slots(snap), ["Poses", "Clothing", "Lighting"])
        json.dumps(snap)


class TestFlags(unittest.TestCase):
    def setUp(self):
        self.ws = Workspace(self)
        self.secret = ["--secret", "--secret-config", str(self.ws.config)]

    def parse(self, *argv):
        return gen.parse_args(["--tables", str(FIXTURE_TABLES), "--dry-run"] + list(argv))

    def assertRefused(self, pattern, *argv):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit):
            self.parse(*argv)
        self.assertRegex(err.getvalue(), pattern)

    def test_the_flags_parse(self):
        args = self.parse(*self.secret, "--secret-prompts", str(self.ws.prompts), "--secret-prompt", "random",
                          "--secret-tables-dir", str(self.ws.tables_dir))
        self.assertEqual(args.secret_prompts, [self.ws.prompts])
        self.assertEqual(args.secret_prompt, "random")
        self.assertEqual(args.secret_tables_dir, self.ws.tables_dir)
        self.assertFalse(args.list_secret_prompts)
        listing = self.parse(*self.secret, "--secret-prompts", str(self.ws.prompts), "--list-secret-prompts")
        self.assertTrue(listing.list_secret_prompts)

    def test_secret_is_required(self):
        self.assertRefused("--secret", "--secret-prompts", str(self.ws.prompts), "--secret-prompt", "random")
        self.assertRefused("--secret", "--secret-prompts", str(self.ws.prompts), "--list-secret-prompts")

    def test_the_pair_requires_each_other(self):
        self.assertRefused("--secret-prompt", *self.secret, "--secret-prompts", str(self.ws.prompts))
        self.assertRefused("--secret-prompts", *self.secret, "--secret-prompt", "random")

    def test_listing_requires_the_files(self):
        self.assertRefused("--secret-prompts", *self.secret, "--list-secret-prompts")

    def test_refused_combinations(self):
        base = self.secret + ["--secret-prompts", str(self.ws.prompts), "--secret-prompt", "Plain"]
        for flag in (["--prompt-layout", "{}"], ["--disable-table", "Stance"],
                     ["--extra-tables", str(self.ws.tables)], ["--extra-table", "Poses"],
                     ["--extra-target", "Poses=portrait"]):
            with self.subTest(flag=flag[0]):
                self.assertRefused(re.escape(flag[0]), *base, *flag)

    def test_extra_value_stays_allowed(self):
        args = self.parse(*self.secret, "--secret-prompts", str(self.ws.prompts), "--secret-prompt", "Plain",
                          "--extra-value", "Poses=completely nude")
        self.assertEqual(args.extra_value, ["Poses=completely nude"])

    def test_refused_on_regeneration(self):
        self.assertRefused("--secret-prompt", *self.secret, "--regen-manifest", str(self.ws.root / "private" / "manifest.json"),
                           "--regen-id", "x", "--secret-prompts", str(self.ws.prompts), "--secret-prompt", "Plain")


class TestAdultsOnly(unittest.TestCase):
    YOUNG = "in {possessive} late teens || young"

    def test_a_plain_roll_can_be_young(self):
        self.assertTrue(any(gen.roll_npc(TABLES, random.Random(s), None)["_young"] for s in range(60)))

    def test_adults_only_never_rolls_young(self):
        for seed in range(60):
            self.assertFalse(gen.roll_npc(TABLES, random.Random(seed), None, adults_only=True)["_young"])

    def test_adults_only_does_not_move_other_tables(self):
        """With no young bullet to drop, the filtered pool is the pool: same seed, same NPC."""
        tables = dict(TABLES, Age=["in {possessive} thirties"])
        for seed in range(20):
            plain = gen.roll_npc(tables, random.Random(seed), None)
            adult = gen.roll_npc(tables, random.Random(seed), None, adults_only=True)
            self.assertEqual({k: v for k, v in plain.items() if not k.startswith("_")},
                             {k: v for k, v in adult.items() if not k.startswith("_")})

    def test_a_forced_young_age_is_refused(self):
        with self.assertRaisesRegex(SystemExit, "adults only"):
            gen.roll_npc(TABLES, random.Random(1), {"Age": self.YOUNG}, adults_only=True)

    def test_a_pool_of_only_young_ages_is_refused(self):
        tables = dict(TABLES, Age=[self.YOUNG])
        with self.assertRaisesRegex(SystemExit, "adults only"):
            gen.roll_npc(tables, random.Random(1), None, adults_only=True)

    def test_a_raw_reroll_keeps_the_snapshot_and_the_rule(self):
        npc = gen.roll_npc(TABLES, random.Random(3), None, adults_only=True)
        npc["_secret_prompt"] = {"file": "x.md", "name": "T", "portrait": "p", "token": "t", "tables": []}
        for seed in range(30):
            gen.reroll_from_raw(TABLES, npc, {"Age"}, random.Random(seed))
            self.assertFalse(npc["_young"])
            self.assertEqual(npc["_secret_prompt"]["name"], "T")
        with self.assertRaisesRegex(SystemExit, "adults only"):
            gen.reroll_from_raw(TABLES, npc, {"Age"}, random.Random(1), {"Age": self.YOUNG})


if __name__ == "__main__":
    unittest.main()
