"""Shared test helpers.

generate-npc.py has a hyphen in its name, so `import generate-npc` is a syntax
error. Load it by path instead - the same trick the module's own docstring
describes for generate-art.py.
"""
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURE_TABLES = Path(__file__).resolve().parent / "fixtures" / "tables-minimal.md"

_cached = None


def load_generator():
    """The generate-npc.py module object, loaded once per process."""
    global _cached
    if _cached is None:
        spec = importlib.util.spec_from_file_location(
            "gennpc", REPO / "generate-npc.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["gennpc"] = module
        spec.loader.exec_module(module)
        _cached = module
    return _cached


def table_keys(tables, name):
    """Every key in `tables` that base table `name` actually reaches.

    `variant_table()` does not roll from the base table alone: for a female
    subject it swaps in 'Hair (she)' wholesale if that key exists, and
    otherwise appends 'Hair (she) +' to the base pool. Either way, content
    sitting only in a variant key is content the generator can genuinely deal
    to a rolled NPC, so a test that checks only tables[name] is blind to
    roughly half of the live file's appearance bullets. Deriving the key list
    from `tables` itself - rather than hardcoding '(she)'/'(he)' - means a
    variant added next month (a new pronoun, a new '+' table) is covered
    automatically, with no edit to the tests required.

    Lives here rather than in one test module because two files need it and
    one of them - test_theme_inert.py - is scheduled for deletion when Phase 4
    starts tagging bullets. A permanent test importing from a doomed one would
    go with it.
    """
    return [k for k in tables if k == name or k.startswith(name + " (")]
