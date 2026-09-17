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


class TestRolling(GateCase):
    def test_a_gated_table_rolls_only_when_an_earlier_value_opens_it(self):
        extra = self.load()
        seen = set()
        for seed in range(200):
            rolled = gen.roll_extra(extra, random.Random(seed))
            man = rolled["Styles"] in ("Rugged dockworker", "Sharp-suited broker")
            self.assertEqual("Men's Attributes" in rolled, man)
            self.assertEqual("Jewellery" in rolled, not man)
            self.assertEqual("Scars" in rolled, rolled.get("Men's Attributes") == "heavy stubble")
            seen.add(tuple(rolled))
        self.assertIn(("Styles", "Men's Attributes", "Scars"), seen)
        self.assertIn(("Styles", "Men's Attributes"), seen)
        self.assertIn(("Styles", "Jewellery"), seen)

    def test_tags_open_tables_in_another_file(self):
        opener = self.write("a.md", "## S\n- a #m\n")
        gated = self.write("b.json", {"G": {"when": ["m"], "rows": [{"value": "b"}]}})
        self.assertEqual(gen.roll_extra(gen.load_extra_tables([opener, gated]), random.Random(0)),
                         {"S": "a", "G": "b"})

    def test_a_tag_no_loaded_table_carries_leaves_the_gate_shut(self):
        extra = gen.load_extra_tables([self.write("a.md", "## G (when: m)\n- b\n")])
        self.assertEqual(gen.roll_extra(extra, random.Random(1)), {})

    def test_an_unticked_opener_opens_nothing(self):
        self.assertEqual(gen.roll_extra(self.load(only=["Men's Attributes"]), random.Random(0)), {})

    def test_values_never_carry_their_tags(self):
        for seed in range(20):
            rolled = gen.roll_extra(self.load(), random.Random(seed))
            self.assertFalse(any("#" in value for value in rolled.values()), rolled)

    def test_a_set_without_gates_rolls_exactly_as_before(self):
        plain = {"a": [("x", 1), ("y", 2)], "b": [("z", 1), ("w", 1)]}
        path = self.write("plain.json", {name: [{"value": v, "weight": w} for v, w in rows]
                                         for name, rows in plain.items()})
        extra = gen.load_extra_tables([path])
        for seed in range(20):
            rng = random.Random(seed)
            expected = {name: rng.choices([v for v, _ in rows], [w for _, w in rows])[0]
                        for name, rows in plain.items()}
            self.assertEqual(gen.roll_extra(extra, random.Random(seed)), expected)
            self.assertEqual(gen.roll_extra(dict(plain), random.Random(seed)), expected)


class TestFixedGatedValues(GateCase):
    def test_a_fixed_gated_value_narrows_its_single_random_opener(self):
        extra = self.load(values={"Men's Attributes": "broad shoulders"})
        self.assertEqual(extra["Styles"], [("Rugged dockworker", 2), ("Sharp-suited broker", 1)])
        for seed in range(30):
            self.assertEqual(gen.roll_extra(extra, random.Random(seed))["Men's Attributes"],
                             "broad shoulders")

    def test_narrowing_follows_a_chain(self):
        extra = self.load(values={"Scars": "a burn scar across one cheek"})
        self.assertEqual(extra["Men's Attributes"], [("heavy stubble", 1)])
        self.assertEqual([v for v, _ in extra["Styles"]], ["Rugged dockworker", "Sharp-suited broker"])
        for seed in range(10):
            self.assertIn("Scars", gen.roll_extra(extra, random.Random(seed)))

    def test_a_fixed_opener_that_opens_the_gate_is_enough(self):
        extra = self.load(values={"Styles": "Sharp-suited broker", "Men's Attributes": "broad shoulders"})
        self.assertEqual(gen.roll_extra(extra, random.Random(0))["Men's Attributes"], "broad shoulders")

    def test_impossible_selections_are_refused(self):
        styles = self.write("styles.md", STYLES_MD)
        two = self.write("two.md", "## A\n- a #m\n\n## B\n- b #m\n\n## G (when: m)\n- g\n")
        cases = [
            (dict(values={"Styles": "Elegant courtesan", "Men's Attributes": "broad shoulders"}),
             [styles],
             "extra table 'Men's Attributes' has a fixed value but 'Styles' is fixed to "
             "'Elegant courtesan', which is not #man"),
            (dict(only=["Men's Attributes"], values={"Men's Attributes": "broad shoulders"}),
             [styles],
             "extra table 'Men's Attributes' has a fixed value but nothing selected can open it "
             "(when: man)"),
            (dict(values={"Men's Attributes": "broad shoulders", "Jewellery": "a thin gold circlet"}),
             [styles],
             "extra table 'Jewellery' has a fixed value but 'Styles' is already limited to #man "
             "by 'Men's Attributes'"),
            (dict(values={"G": "g"}), [two],
             "extra table 'G' has a fixed value but 'A' and 'B' could each open it (when: m); "
             "fix or untick all but one"),
        ]
        for kwargs, paths, message in cases:
            with self.subTest(message=message):
                self.refused(message, paths, **kwargs)

    def test_fixing_one_of_several_openers_is_enough(self):
        two = self.write("two.md", "## A\n- a #m\n- c\n\n## B\n- b #m\n\n## G (when: m)\n- g\n")
        extra = gen.load_extra_tables([two], values={"A": "a", "G": "g"})
        self.assertEqual(extra["B"], [("b", 1)])
        self.assertEqual(gen.roll_extra(extra, random.Random(0))["G"], "g")


class TestCli(GateCase):
    def run_main(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = gen.main(["--tables", str(FIXTURE_TABLES), "--dry-run", "--seed", "5",
                             "--out", self.tmp.name] + list(argv))
        return code, out.getvalue()

    def test_a_fixed_gated_value_reaches_the_prompt_and_its_shut_sibling_does_not(self):
        styles = str(self.write("styles.md", STYLES_MD))
        code, out = self.run_main("--extra-tables", styles, "--count", "3",
                                  "--extra-value", "Men's Attributes=broad shoulders")
        self.assertEqual(code, 0)
        self.assertEqual(out.lower().count("broad shoulders"), 6)
        self.assertNotIn("gold circlet", out.lower())
        self.assertNotIn("#man", out.lower())

    def test_an_impossible_selection_is_a_clean_exit(self):
        styles = str(self.write("styles.md", STYLES_MD))
        with self.assertRaises(SystemExit) as ctx:
            self.run_main("--extra-tables", styles, "--extra-table", "Men's Attributes",
                          "--extra-value", "Men's Attributes=broad shoulders")
        self.assertIn("nothing selected can open it", str(ctx.exception))
