"""Measure how visible a rolled Theme actually is, per theme and per table.

Spec §10 asks for this directly: "measure the actual share of tagged bullets
per themed roll against THEME_SHARE, per table, including for the thin themes."
It is the one listed verification Phase 1 could not implement, because with no
bullet tagged the answer is 0% everywhere and says nothing.

It is not a test, and it is deliberately not named test_*, because there is no
threshold to assert yet - the number it reports is a property of the *content*,
which is authored later. It is an instrument: run it before tagging to get the
zero baseline, run it during tagging to see each theme come up.

Why a measurement is needed at all, rather than trusting THEME_SHARE:
apply_theme_share() computes its multiplier and then filter_by_mil() and
apply_weapon_policy() narrow the pool further, so the share a roll actually draws
at is not the share that was targeted. Measured on realistic pool shapes the
realized figure ran 0.72 and 0.83 against a nominal 0.60. Which direction it
moves depends on how the tags correlate with the civ/mil split, so it cannot be
derived - only measured.

    python -m test.theme_visibility                     # live tables
    python -m test.theme_visibility --count 2000
    python -m test.theme_visibility --tables test/fixtures/tables-themed.md

Reading the output: `tagged/pool` is how much content that theme has in that
table, and `share` is how often a rolled NPC of that theme actually got one of
those bullets rather than a neutral one. A `share` of 0.00 with `tagged` of 0
means unauthored, not broken - that is the normal state of a thin theme, and
the column to watch as content lands.
"""
import argparse
import collections
import random
import sys
from pathlib import Path

from test.helpers import (
    REPO, bullets_for, core_of, load_generator, own_texts)

LIVE_TABLES = REPO / "prompts" / "npc-generator-tables.md"

Cell = collections.namedtuple("Cell", "pool tagged rolls hits share")


def measure_cell(tables, name, theme, rolled):
    """One theme's realized share for one table, over pre-rolled NPCs.

    `tagged` counts *bullets*, not the rendered strings own_texts() returns -
    a "{Subject} {wear} ..." bullet expands to one string per pronoun set, so
    counting texts would report a Headgear table as carrying twice the content
    it does and make the tagged/pool ratio beside it incoherent.
    """
    gen = load_generator()
    own = own_texts(tables, name, theme)
    bullets = bullets_for(tables, name)
    tagged = sum(1 for b in bullets
                 if theme in gen.themes_of(gen.flags_for(name, b)))
    hits = sum(1 for npc in rolled if core_of(name, npc[name]) in own)
    return Cell(len(bullets), tagged, len(rolled),
                hits, hits / len(rolled) if rolled else 0.0)


def measure(tables, count=500, seed=0, themes=None):
    """{theme: {table: Cell}} over `count` forced rolls per theme.

    Rolls are forced to each theme in turn rather than sampled from the Theme
    table, so a thin theme gets the same sample size as a fat one - the whole
    point is to see whether a *rare* theme is visible when it does come up.
    """
    gen = load_generator()
    themes = themes or sorted(set(tables["Theme"]))
    out = {}
    for theme in themes:
        rng = random.Random(seed)
        rolled = [gen.roll_npc(tables, rng, {"Theme": theme})
                  for _ in range(count)]
        out[theme] = {name: measure_cell(tables, name, theme, rolled)
                      for name in gen.THEMED_TABLES}
    return out


def report(results, target, stream=sys.stdout):
    """Print the grid, and return the cells that have content but miss target.

    Only a cell with tagged content can miss - an unauthored one is reported
    as a blank rather than a failure, since 0.00 of nothing is not a defect.
    """
    gen = load_generator()
    shortfalls = []
    width = max(len(t) for t in results) if results else 5
    header = "%-*s  %s" % (width, "theme",
                           "  ".join("%-22s" % n for n in gen.THEMED_TABLES))
    print(header, file=stream)
    print("-" * len(header), file=stream)
    for theme, row in sorted(results.items()):
        cells = []
        for name in gen.THEMED_TABLES:
            c = row[name]
            if not c.tagged:
                cells.append("%-22s" % "     -  (untagged)")
                continue
            # Three decimals, because a share of 0.599 displayed as "0.60"
            # next to a "!" reads as a contradiction rather than a near miss.
            flag = " " if c.share >= target else "!"
            cells.append("%-22s" % ("%.3f %s %d/%d tagged"
                                    % (c.share, flag, c.tagged, c.pool)))
            if c.share < target:
                shortfalls.append((theme, name, c))
        print("%-*s  %s" % (width, theme, "  ".join(cells)), file=stream)
    print(file=stream)
    print("target THEME_SHARE = %.2f   '!' marks a table whose tagged bullets "
          "lose more often than that" % target, file=stream)
    return shortfalls


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Measure realized theme visibility per theme and table.")
    p.add_argument("--tables", type=Path, default=LIVE_TABLES,
                   help="tables file to measure (default: the live one)")
    p.add_argument("--count", type=int, default=500,
                   help="NPCs rolled per theme (default: 500)")
    p.add_argument("--seed", type=int, default=0, help="base RNG seed")
    args = p.parse_args(argv)

    gen = load_generator()
    tables = gen.parse_tables(args.tables)
    print("%s   %d NPCs per theme\n" % (args.tables, args.count))
    results = measure(tables, count=args.count, seed=args.seed)
    shortfalls = report(results, gen.THEME_SHARE)

    total_tagged = sum(c.tagged for row in results.values() for c in row.values())
    if not total_tagged:
        print("\nNothing tagged - every theme opens the whole neutral pool. "
              "That was the pre-tagging baseline; now it means the tags have "
              "gone, which test/test_theme_visibility.py pins against.")
    elif shortfalls:
        print("\n%d table(s) below target: %s" % (
            len(shortfalls),
            ", ".join("%s/%s" % (t, n) for t, n, _ in shortfalls)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
