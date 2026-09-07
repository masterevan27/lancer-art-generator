"""The ship CLI's argument surface.

The import GUI builds argv for this script by hand, so every flag it emits has
to parse and every refusal has to be a refusal rather than a silently dropped
argument.
"""
import unittest
from pathlib import Path

from test.helpers import load_ship_generator

ship = load_ship_generator()


class TestOutRoot(unittest.TestCase):
    """--out-root picks the tree run folders are numbered under."""

    def test_out_root_is_parsed_as_a_path(self):
        self.assertEqual(ship.parse_args(["--out-root", "D:/ships"]).out_root,
                         Path("D:/ships"))

    def test_absent_out_root_is_none(self):
        self.assertIsNone(ship.parse_args([]).out_root)

    def test_explicit_out_wins_over_out_root(self):
        args = ship.parse_args(["--out-root", "D:/ships", "--out", "D:/one-run"])
        self.assertEqual(args.out, Path("D:/one-run"))
