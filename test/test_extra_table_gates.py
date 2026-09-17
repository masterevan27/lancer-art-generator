"""Tag gates on private extra tables.

A bullet's trailing '#tag's say which gated tables its value opens; a
'## Name (when: tag, tag)' heading makes a table that rolls only when a value
rolled or fixed earlier carries one of those tags. See
docs/superpowers/specs/2026-09-16-secret-table-gates-design.md.
"""
import contextlib
import io
import json
import random
import tempfile
import unittest
from pathlib import Path

from test.helpers import FIXTURE_TABLES, load_generator

gen = load_generator()

STYLES_MD = """## Styles
- x2 Rugged dockworker #man
- x1 Sharp-suited broker #Man
- x2 Elegant courtesan #woman #noble

## Men's Attributes (when: man)
- heavy stubble #scarred
- broad shoulders

## Scars (when: scarred)
- a burn scar across one cheek

## Jewellery (when: woman, noble)
- a thin gold circlet
"""


class GateCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, name, content):
        path = Path(self.tmp.name) / name
        text = content if isinstance(content, str) else json.dumps(content)
        path.write_text(text, encoding="utf-8")
        return path

    def load(self, text=STYLES_MD, **kwargs):
        return gen.load_extra_tables([self.write("styles.md", text)], **kwargs)

    def refused(self, message, *args, **kwargs):
        with self.assertRaises(ValueError) as ctx:
            gen.load_extra_tables(*args, **kwargs)
        self.assertEqual(str(ctx.exception), message)


class TestParsing(GateCase):
    def test_trailing_tags_are_split_off_and_lower_cased(self):
        self.assertEqual(gen.split_extra_tags("Rugged dockworker #man #Noble"),
                         ("Rugged dockworker", ("man", "noble")))
        self.assertEqual(gen.split_extra_tags("a #3 jersey worn loose"), ("a #3 jersey worn loose", ()))
        self.assertEqual(gen.split_extra_tags("#man"), ("#man", ()))
        self.assertEqual(gen.split_extra_tags("a value#man"), ("a value#man", ()))
        self.assertEqual(gen.split_extra_tags("a #x #x"), ("a", ("x",)))

    def test_a_when_suffix_is_split_off_the_heading(self):
        self.assertEqual(gen.split_extra_heading("Men's Attributes (when: man, Noble)"),
                         ("Men's Attributes", ("man", "noble")))
        self.assertEqual(gen.split_extra_heading("Styles"), ("Styles", None))
        for heading, message in [
            ("T (when: )", "table 'T' has an empty (when:)"),
            ("T (when: a, )", "table 'T' has an empty entry in (when:)"),
            ("T (when: a b)", "table 'T': 'a b' is not a tag (letters, digits, - and _)"),
        ]:
            with self.subTest(heading=heading), self.assertRaises(ValueError) as ctx:
                gen.split_extra_heading(heading)
            self.assertEqual(str(ctx.exception), message)

    def test_markdown_values_names_gates_and_tags(self):
        extra = self.load()
        self.assertIsInstance(extra, dict)
        self.assertEqual(list(extra), ["Styles", "Men's Attributes", "Scars", "Jewellery"])
        self.assertEqual(extra["Styles"], [("Rugged dockworker", 2), ("Sharp-suited broker", 1),
                                           ("Elegant courtesan", 2)])
        self.assertEqual(extra.when, {"Men's Attributes": ("man",), "Scars": ("scarred",),
                                      "Jewellery": ("woman", "noble")})
        self.assertEqual(extra.tags["Styles"]["Elegant courtesan"], ("woman", "noble"))
        self.assertEqual(extra.tags["Men's Attributes"], {"heavy stubble": ("scarred",)})
        self.assertNotIn("Scars", extra.tags)

    def test_the_same_bullet_with_different_tags_is_one_row(self):
        extra = self.load("## T\n- a #x\n- x2 a #y\n")
        self.assertEqual(extra["T"], [("a", 3)])
        self.assertEqual(extra.tags["T"]["a"], ("x", "y"))

    def test_a_repeated_heading_must_agree_about_its_gate(self):
        self.refused("styles.md: table 'G' is repeated with a different (when:)",
                     [self.write("styles.md", "## T\n- a #x\n\n## G (when: x)\n- b\n\n## G\n- c\n")])
        extra = self.load("## T\n- a #x\n\n## G (when: x)\n- b\n\n## G (when: x)\n- c\n")
        self.assertEqual(extra["G"], [("b", 1), ("c", 1)])

    def test_a_bad_heading_names_the_file(self):
        self.refused("styles.md: table 'T' has an empty (when:)",
                     [self.write("styles.md", "## T (when:)\n- a\n")])

    def test_json_rows_carry_tags_and_tables_carry_gates(self):
        path = self.write("set.json", {
            "Styles": [{"value": "Rugged dockworker", "weight": 2, "tags": ["Man"]}],
            "Men's Attributes": {"when": ["man"], "rows": [{"value": "heavy stubble"}]},
        })
        extra = gen.load_extra_tables([path])
        self.assertEqual(extra["Men's Attributes"], [("heavy stubble", 1)])
        self.assertEqual(extra.when, {"Men's Attributes": ("man",)})
        self.assertEqual(extra.tags, {"Styles": {"Rugged dockworker": ("man",)}})

    def test_json_gate_and_tag_errors_name_the_file(self):
        for data in [
            {"T": {"when": [], "rows": [{"value": "a"}]}},
            {"T": {"when": ["a b"], "rows": [{"value": "a"}]}},
            {"T": {"when": ["a"], "rows": []}},
            {"T": [{"value": "a", "tags": "man"}]},
            {"T": [{"value": "a", "tags": ["no spaces"]}]},
        ]:
            with self.subTest(data=data), self.assertRaisesRegex(ValueError, "^bad.json: "):
                gen.load_extra_tables([self.write("bad.json", data)])

    def test_the_markdown_file_matches_its_json_twin(self):
        md = self.load("## S\n- x2 a #m\n\n## G (when: m)\n- b\n")
        js = gen.load_extra_tables([self.write("twin.json", {
            "S": [{"value": "a", "weight": 2, "tags": ["m"]}],
            "G": {"when": ["m"], "rows": [{"value": "b"}]},
        })])
        self.assertEqual((md, md.when, md.tags), (js, js.when, js.tags))


class TestOrder(GateCase):
    def test_a_gate_above_its_opener_is_refused(self):
        self.refused("styles.md: gated table 'G' comes before 'S', the table that opens it (when: m)",
                     [self.write("styles.md", "## G (when: m)\n- b\n\n## S\n- a #m\n")])

    def test_order_runs_across_files_in_argument_order(self):
        gated = self.write("a.md", "## G (when: m)\n- b\n")
        opener = self.write("b.md", "## S\n- a #m\n")
        self.assertEqual(list(gen.load_extra_tables([opener, gated])), ["S", "G"])
        self.refused("a.md: gated table 'G' comes before 'S', the table that opens it (when: m)",
                     [gated, opener])

    def test_order_is_checked_before_only_narrows(self):
        with self.assertRaisesRegex(ValueError, "comes before"):
            self.load("## G (when: m)\n- b\n\n## S\n- a #m\n", only=["S"])

    def test_only_keeps_the_gates_of_the_tables_it_keeps(self):
        extra = self.load(only=["Styles", "Scars"])
        self.assertEqual(extra.when, {"Scars": ("scarred",)})
        self.assertEqual(list(extra.tags), ["Styles"])
