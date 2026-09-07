"""Measure ship prompt lengths. An instrument, not a test - see test/prompt_budget.py."""
import contextlib
import io
import random


def measure(ship, tables, count=1500, seed=0):
    """[(portrait_tokens, token_tokens)] over `count` rolled ships.

    stderr is swallowed because build_ship_prompts warns on every prompt over
    the limit, and the point of this instrument is to count those rather than
    to print fifteen hundred of them.
    """
    results = []
    with contextlib.redirect_stderr(io.StringIO()):
        for n in range(count):
            rolled = ship.roll_ship(tables, random.Random(seed + n))
            portrait, token = ship.build_ship_prompts(rolled)
            results.append((ship.estimate_tokens(portrait),
                            ship.estimate_tokens(token)))
    return results
