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


def bullets_for(tables, name):
    """A table's bullets, including its per-pronoun variant tables."""
    return [bullet for key in table_keys(tables, name) for bullet in tables[key]]


def core_of(name, bullet):
    """A bullet reduced to the part that survives into the rolled NPC.

    Flags come off - Backdrop keeps them in a third segment, every other table
    in a second - so a rolled value and the source bullet it came from compare
    equal even for the tables roll_npc() strips flags from. Backdrop keeps both
    its shot and its scene, since two scenes can share a shot phrase.
    """
    gen = load_generator()
    if name == "Backdrop":
        shot, scene, _ = gen.split_backdrop(bullet)
        return "%s || %s" % (shot, scene)
    return gen.split_flags(bullet)[0]


def pronoun_sets(tables):
    """Every pronoun field-set a roll from `tables` can produce."""
    gen = load_generator()
    return [gen.pronoun_fields(p) for p in tables["Pronouns"]]


def rendered(tables, name, bullet):
    """Every string one bullet can appear as once an NPC is rolled.

    roll_npc() substitutes pronoun placeholders into every value it returns, so
    "{Subject} {wear} a wide woven hat." comes back as "She wears a wide woven
    hat." Expanding the source side against all pronoun sets is what lets a
    comparison against a rolled value be a plain set membership test.
    """
    core = core_of(name, bullet)
    if "{" not in core:
        return {core}
    return {core.format(**fields) for fields in pronoun_sets(tables)}


def _partition_by_theme(tables, name, theme):
    """(texts of `name` tagged with `theme`, texts reachable under it).

    One pass, because both callers below need the same two piles and the tag
    read is the expensive part. "Reachable" is untagged-or-tagged-with-`theme`.
    """
    gen = load_generator()
    own, other, neutral = set(), set(), set()
    for bullet in bullets_for(tables, name):
        tags = gen.themes_of(gen.flags_for(name, bullet))
        texts = rendered(tables, name, bullet)
        if not tags:
            neutral |= texts
        elif theme in tags:
            own |= texts
        else:
            other |= texts
    return own, other, neutral


def own_texts(tables, name, theme):
    """Rendered texts of `name`'s bullets that carry `theme`'s own tag.

    What the visibility measurement counts: a rolled value in this set came
    from the theme rather than from the neutral floor.
    """
    own, _, _ = _partition_by_theme(tables, name, theme)
    return own


def foreign_texts(tables, name, theme):
    """Rendered texts of `name` that belong to a theme other than `theme`.

    A text reachable under this theme as well - untagged, or tagged with this
    theme too - is subtracted back out, so a table that happens to repeat the
    same wording under two themes cannot produce a false failure.
    """
    own, other, neutral = _partition_by_theme(tables, name, theme)
    return other - own - neutral
