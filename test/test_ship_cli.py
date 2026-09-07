"""The ship CLI's argument surface.

The import GUI builds argv for this script by hand, so every flag it emits has
to parse and every refusal has to be a refusal rather than a silently dropped
argument.
"""
import tempfile
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

    def test_out_root_actually_redirects_the_computed_out(self):
        """The behaviour --out-root exists for, and the gap the three tests
        above leave open: they only pin the argparse-level parsing of the
        flag itself, never whether it reaches default_root() and
        next_run_folder() to actually move where a fresh run folder lands.
        With --out absent, parse_args() computes args.out as
        next_run_folder(default_root(args)) - default_root() prefers
        args.out_root over DEFAULT_OUTPUT_ROOT - so a --out-root of its own
        should redirect the computed run folder under it rather than under
        the module's own output tree.

        A fresh temp dir, so next_run_folder()'s "first N whose folder
        doesn't already exist" lands on run1 deterministically and creates
        nothing real on disk - next_run_folder() only stats candidate paths,
        it does not create them.
        """
        with tempfile.TemporaryDirectory() as tmp:
            args = ship.parse_args(["--out-root", tmp])
            self.assertEqual(args.out, Path(tmp) / "run1")
