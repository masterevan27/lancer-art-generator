"""Measure generated prompt length against Krea 2's token ceiling.

Not a test, and deliberately not named test_*: the number it reports is a
property of the content, and the content changes every time a bullet is
authored. It is the instrument the budget test reads, and a report you can run
by hand when a long bullet lands.

    python -m test.prompt_budget
    python -m test.prompt_budget --count 5000
"""
import argparse
import contextlib
import io
import random
import sys
from pathlib import Path

from test.helpers import REPO, load_generator

LIVE_TABLES = REPO / "prompts" / "npc-generator-tables.md"


def measure(tables, count=1500, seed=0):
    """Estimated token counts for both prompts over `count` rolled NPCs.

    build_prompts() writes an over-limit warning to stderr per prompt, which
    would bury a test run in noise, so it is swallowed here - the counts this
    returns are what callers judge, not the warnings.
    """
    gen = load_generator()
    out = {"portrait": [], "token": []}
    with contextlib.redirect_stderr(io.StringIO()):
        for n in range(count):
            npc = gen.roll_npc(tables, random.Random(seed + n))
            portrait, token = gen.build_prompts(npc)
            out["portrait"].append(gen.estimate_tokens(portrait))
            out["token"].append(gen.estimate_tokens(token))
    return out


def percentile(values, q):
    """The q-th percentile (0-100) by nearest rank, on a copy."""
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(len(ordered) * q / 100.0))
    return ordered[idx]


def main(argv=None):
    p = argparse.ArgumentParser(description="Measure prompt length vs TOKEN_LIMIT.")
    p.add_argument("--tables", type=Path, default=LIVE_TABLES)
    p.add_argument("--count", type=int, default=1500)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args(argv)

    gen = load_generator()
    tables = gen.parse_tables(args.tables)
    results = measure(tables, count=args.count, seed=args.seed)
    print("%s   %d rolls   limit %d\n" % (args.tables, args.count, gen.TOKEN_LIMIT))
    for name, values in results.items():
        over = sum(1 for v in values if v > gen.TOKEN_LIMIT)
        print("%-9s mean %4d  p50 %4d  p90 %4d  p99 %4d  max %4d   over: %5.1f%%" % (
            name, sum(values) // len(values), percentile(values, 50),
            percentile(values, 90), percentile(values, 99), max(values),
            100.0 * over / len(values)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
