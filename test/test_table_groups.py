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
