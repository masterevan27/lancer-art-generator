"""Secret prompts: fill-in-the-blank templates for Secret-mode NPCs.

The file format (spec 2), the generator wiring (spec 3) and the content
rules are tested here; the module under test is secret_prompts.py, loaded
as an ordinary import, and generate-npc.py through test.helpers.
"""
import contextlib
import io
import json
import random
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


if __name__ == "__main__":
    unittest.main()
