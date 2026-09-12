"""Group references: '- => Name' in a rolled table is one slot that resolves
from '## Name'. See docs/superpowers/specs/2026-09-12-table-groups-design.md.
"""
import random
import unittest
from pathlib import Path

from test.helpers import FIXTURE_TABLES, REPO, load_generator

gen = load_generator()
GROUPS_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "tables-groups.md"


class TestReferenceHelpers(unittest.TestCase):
    def test_a_reference_names_its_target_with_flags_aside(self):
        self.assertEqual(gen.reference_target("=> Flight suits"), "Flight suits")
        self.assertEqual(gen.reference_target("=> Flight suits || @gundam"), "Flight suits")
        self.assertEqual(gen.reference_target("=>  Black dresses (gundam)  "), "Black dresses (gundam)")
        self.assertTrue(gen.is_reference("=> Flight suits"))

    def test_an_ordinary_bullet_is_not_a_reference(self):
        for bullet in ["a jacket", "a jacket || civ", "=>", "=> ", " => x", "a => b", "{Subject} {wear} a hat."]:
            with self.subTest(bullet=bullet):
                self.assertIsNone(gen.reference_target(bullet))
                self.assertFalse(gen.is_reference(bullet))

    def test_references_in_reads_the_base_table_and_its_variants_once_each(self):
        tables = {
            "Outfit": ["a jacket", "=> Flight suits", "=> Flight suits", "=> Robes || @neosamurai"],
            "Outfit (she) +": ["=> Crop tops"],
            "Outfit (he) +": ["a vest"],
            "Flight suits": ["a flight suit"], "Robes": ["a robe"], "Crop tops": ["a crop top"],
        }
        self.assertEqual(gen.references_in(tables, "Outfit"), {
            "Flight suits": "=> Flight suits",
            "Robes": "=> Robes || @neosamurai",
            "Crop tops": "=> Crop tops",
        })
        self.assertEqual(gen.references_in(tables, "Flight suits"), {})

    def test_group_headings_are_the_target_and_its_present_variants(self):
        tables = {"Flight suits": ["a"], "Flight suits (she) +": ["b"], "Flight suits (gundam)": ["c"]}
        self.assertEqual(gen.group_headings(tables, "Flight suits", "she"),
                         ["Flight suits", "Flight suits (she) +"])
        self.assertEqual(gen.group_headings(tables, "Flight suits", "he"), ["Flight suits"])
        self.assertEqual(gen.group_headings(tables, "Flight suits (gundam)", "she"),
                         ["Flight suits (gundam)"])

    def test_group_tables_is_every_referenced_heading_with_its_variants(self):
        tables = {
            "Outfit": ["=> Flight suits"], "Outfit (she) +": ["=> Crop tops"],
            "Flight suits": ["a"], "Flight suits (she) +": ["b"], "Flight suits (he)": ["c"],
            "Crop tops": ["d"], "Unreferenced": ["e"],
        }
        self.assertEqual(gen.group_tables(tables),
                         {"Flight suits", "Flight suits (she) +", "Flight suits (he)", "Crop tops"})


def fixture_tables():
    """A fresh copy of the minimal fixture, so a test can add groups to it."""
    return {k: list(v) for k, v in gen.parse_tables(FIXTURE_TABLES).items()}


class TestCheckGroupReferences(unittest.TestCase):
    def check(self, tables):
        return gen.check_group_references(tables)

    def test_a_well_formed_file_has_no_complaints(self):
        tables = fixture_tables()
        tables["Outfit"] += ["=> Plates", "=> Neon (beta) || @beta"]
        tables["Outfit (she) +"] = ["=> Crop tops"]
        tables["Plates"] = ["lacquered plate", "scuffed plate || mil"]
        tables["Plates (she) +"] = ["a fitted plate"]
        tables["Neon (beta)"] = ["a neon jacket", "a neon visor jacket"]
        tables["Crop tops"] = ["a crop top || civ"]
        self.assertEqual(self.check(tables), [])

    def test_a_missing_target_is_named(self):
        tables = fixture_tables()
        tables["Outfit"].append("=> Nowhere")
        [problem] = self.check(tables)
        self.assertIn("Nowhere", problem)
        self.assertIn("Outfit", problem)

    def test_a_rolled_table_or_its_variant_cannot_be_a_group(self):
        for target in ["Headgear", "Build (she)", "Outfit (she) +"]:
            tables = fixture_tables()
            tables.setdefault(target, ["x"])
            tables["Outfit"].append("=> " + target)
            with self.subTest(target=target):
                self.assertTrue(any("rolled table" in p for p in self.check(tables)), self.check(tables))

    def test_a_reference_carries_no_behavioural_flags(self):
        tables = fixture_tables()
        tables["Plates"] = ["a plate"]
        tables["Outfit"].append("=> Plates || civ @alpha")
        [problem] = self.check(tables)
        self.assertIn("civ", problem)
        self.assertNotIn("@alpha", problem.split("carries flags")[1].split(";")[0])

    def test_one_reference_per_group_per_table(self):
        tables = fixture_tables()
        tables["Plates"] = ["a plate"]
        tables["Outfit"] += ["=> Plates", "=> Plates || @alpha"]
        self.assertTrue(any("more than once" in p for p in self.check(tables)))
        # An xN weight is N copies of ONE text, which is fine.
        tables["Outfit"] = [b for b in tables["Outfit"] if b != "=> Plates || @alpha"] + ["=> Plates"]
        self.assertEqual(self.check(tables), [])

    def test_a_group_cannot_reference_a_group(self):
        tables = fixture_tables()
        tables["Outfit"].append("=> Plates")
        tables["Plates"] = ["a plate", "=> Heavy plates"]
        tables["Heavy plates"] = ["a heavy plate"]
        self.assertTrue(any("one level" in p for p in self.check(tables)))

    def test_a_themed_groups_members_carry_no_tags(self):
        tables = fixture_tables()
        tables["Outfit"].append("=> Neon (beta) || @beta")
        tables["Neon (beta)"] = ["a neon jacket", "a neon visor || @beta"]
        [problem] = self.check(tables)
        self.assertIn("a neon visor", problem)
        # A neutral group's members may be tagged; the tag then filters inside the group.
        tables["Outfit"][-1] = "=> Neon (beta)"
        self.assertEqual(self.check(tables), [])

    def test_a_reference_lives_only_in_a_rolled_table_the_main_draw_handles(self):
        for name in ["Pronouns", "Theme", "Stance", "Animation"]:
            tables = fixture_tables()
            tables["Plates"] = ["a plate"]
            tables.setdefault(name, []).append("=> Plates")
            with self.subTest(name=name):
                self.assertTrue(any("only read in" in p for p in self.check(tables)))

    def test_check_tables_refuses_a_malformed_file_with_every_problem_listed(self):
        tables = fixture_tables()
        tables["Outfit"] += ["=> Nowhere", "=> Headgear"]
        with self.assertRaises(SystemExit) as cm:
            gen.check_tables(tables, Path("tables.md"))
        self.assertIn("Nowhere", str(cm.exception))
        self.assertIn("Headgear", str(cm.exception))
