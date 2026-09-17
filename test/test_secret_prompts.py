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


if __name__ == "__main__":
    unittest.main()
