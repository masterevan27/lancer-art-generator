"""No ship prompt is truncated by the model's token limit.

p99 AND max are both asserted here, unlike test/test_prompt_budget.py:23-32,
which holds the NPC file to p99 alone. That file's reasoning - the tail is one
unlucky pairing of the two longest bullets, and holding the max under the
limit would cost more content than the one truncated render is worth - does
not transfer: over 1500 sampled ships, 0 are ever over TOKEN_LIMIT, so holding
max costs nothing here. And the cost of NOT holding it was real on this branch:
a tuned TOKEN_TEMPLATE once put max at 513 with 2 of 800 ships over, while p99
stayed at 499 and this suite stayed green throughout. Truncation cuts a
prompt's TAIL, which is where the closing framing language (palette, flat-white
background) lives - exactly what a p99-only assertion is blind to.
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

    def test_no_prompt_exceeds_the_limit(self):
        portrait_over = sum(1 for r in RESULTS if r[0] > ship.TOKEN_LIMIT)
        token_over = sum(1 for r in RESULTS if r[1] > ship.TOKEN_LIMIT)
        self.assertEqual(portrait_over, 0,
                         "%d/%d portrait prompts over the %d-token limit"
                         % (portrait_over, len(RESULTS), ship.TOKEN_LIMIT))
        self.assertEqual(token_over, 0,
                         "%d/%d token prompts over the %d-token limit"
                         % (token_over, len(RESULTS), ship.TOKEN_LIMIT))
