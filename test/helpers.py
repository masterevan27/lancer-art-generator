"""Shared test helpers.

generate-npc.py has a hyphen in its name, so `import generate-npc` is a syntax
error. Load it by path instead - the same trick the module's own docstring
describes for generate-art.py.
"""
import importlib.util
import random
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


_cached_3d = None


def load_3d():
    """The generate-3d.py module object, loaded once per process.

    Same by-path load as load_generator(), for the same reason: the hyphen
    keeps generate-3d.py off the normal import path.
    """
    global _cached_3d
    if _cached_3d is None:
        spec = importlib.util.spec_from_file_location("gen3d", REPO / "generate-3d.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["gen3d"] = module
        spec.loader.exec_module(module)
        _cached_3d = module
    return _cached_3d


def manifest_entry(seed=0, overrides=None):
    """One .generated-npcs.json entry, rolled from the fixture tables.

    The 3D tools read manifest entries, not rolled npc dicts, so a test that
    handed them a dict straight out of roll_npc() would be testing a shape
    that never reaches them. This reproduces exactly the keys generate-npc.py's
    roll path writes, minus the render results, which nothing in the 3D
    rebuild reads.

    The fixture's 'Given names' and 'Family names' tables hold exactly one
    entry each, so every seed rolls the same "Test Subject" - fine for a
    caller that only ever holds one entry at a time, but a test that packs
    two different seeds into one manifest dict keyed by name (as the real
    .generated-npcs.json is keyed by folder path, which embeds the name) would
    silently collapse them into a single row. The seed is folded into the
    name here, once, rather than in every such caller - unless the caller
    forced its own "name" via `overrides`, in which case that choice wins.
    """
    gen = load_generator()
    tables = gen.parse_tables(FIXTURE_TABLES)
    npc = gen.roll_npc(tables, random.Random(seed), overrides or {})
    if not (overrides or {}).get("name"):
        npc["name"] = "%s %d" % (npc["name"], seed)
    return {
        "id": "npc-test-%d" % seed,
        "kind": "npc",
        "name": npc["name"],
        "callsign": npc["Callsigns"],
        "seed": seed,
        "traits": {k: v for k, v in npc.items() if not k.startswith("_")},
        "young": npc["_young"],
        "outfit_notac": npc["_outfit_notac"],
        "gear_helmet": npc["_gear_helmet"],
        "hair_updo": npc["_hair_updo"],
        "headgear_helmet": npc["_headgear_helmet"],
    }


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


def colour_forms(tables, core):
    """`core` with its '{colour}' slot filled, once per Hair colour bullet.

    A Hair bullet's colour is rolled from a table of its own, so the strings
    one cut can appear as are the cross product of the cut and every colour -
    and where a colour carries a tail, roll_npc() appends that tail after the
    whole cut phrase, so the tail form is a second string the same pair
    produces. Both are reproduced here rather than the slot being stripped,
    because the comparisons these feed are set membership against a rolled
    value: a form this misses is a form the cohesion checks stop covering.

    Drawn through bullets_for() rather than tables["Hair colour"], because
    roll_npc() rolls the colour through variant_table(), which is generic over
    every table and picks up a 'Hair colour (she) +' the moment one is
    authored - the live file already uses that idiom for Hair itself. Reading
    the base key alone would under-produce silently, and in the direction that
    shrinks the banned sets the cohesion tests are built from.

    Returns the slot untouched when the tables carry no '## Hair colour' at
    all, rather than raising - not every caller's fixture has one, and
    table_keys() answers an absent table with an empty list. Nothing can be
    rolled from such a file either (roll_npc() would fail on the missing key
    long before), so an unfilled slot is the truthful answer: no colour exists
    for that cut to appear in.
    """
    gen = load_generator()
    out = set()
    for bullet in bullets_for(tables, "Hair colour"):
        base, tail, _ = gen.split_hair_colour(bullet)
        filled = core.replace("{colour}", base)
        out.add("%s, %s" % (filled, tail) if tail else filled)
    return out or {core}


def rendered(tables, name, bullet):
    """Every string one bullet can appear as once an NPC is rolled.

    roll_npc() substitutes pronoun placeholders into every value it returns, so
    "{Subject} {wear} a wide woven hat." comes back as "She wears a wide woven
    hat." Expanding the source side against all pronoun sets is what lets a
    comparison against a rolled value be a plain set membership test.

    The colour slot is expanded first, in that same order: roll_npc() resolves
    '{colour}' before its pronoun pass, so a tail carrying a placeholder of its
    own is still rendered.
    """
    core = core_of(name, bullet)
    if "{" not in core:
        return {core}
    cores = colour_forms(tables, core) if "{colour}" in core else {core}
    out = set()
    for text in cores:
        if "{colour}" in text:
            # No '## Hair colour' to fill it - see colour_forms(). Handing the
            # slot to str.format below would only turn a missing table into a
            # KeyError about pronouns.
            out.add(text)
        elif "{" not in text:
            out.add(text)
        else:
            out |= {text.format(**fields) for fields in pronoun_sets(tables)}
    return out


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
