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
