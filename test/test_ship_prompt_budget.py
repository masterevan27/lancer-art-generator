"""No ship prompt is truncated by the model's token limit.

p99 rather than max, for the reason test/test_prompt_budget.py:23-32 gives: the
tail is one unlucky pairing of the two longest bullets in the file, and holding
the max under the limit would cost more content than the one truncated render
is worth.
"""
import unittest

from test import ship_prompt_budget
from test.helpers import load_ship_generator

ship = load_ship_generator()
TABLES = ship.parse_tables(ship.DEFAULT_TABLES)
RESULTS = ship_prompt_budget.measure(ship, TABLES, count=1500, seed=0)


def p99(values):
    return sorted(values)[int(len(values) * 0.99)]


class TestPromptBudget(unittest.TestCase):
    def test_the_sample_is_not_vacuous(self):
        self.assertEqual(len(RESULTS), 1500)
        self.assertGreater(min(min(r) for r in RESULTS), 200)

    def test_portrait_p99_is_under_the_limit(self):
        self.assertLess(p99([r[0] for r in RESULTS]), ship.TOKEN_LIMIT)

    def test_token_p99_is_under_the_limit(self):
        self.assertLess(p99([r[1] for r in RESULTS]), ship.TOKEN_LIMIT)
