"""No rolled NPC may lose its prompt tail to Krea 2's token ceiling.

A truncated prompt loses whatever comes last, which in both templates is the
palette instruction, the flat-white background rule and the closing style tags
- the parts that make a token cut out cleanly. That makes over-limit prompts a
silent quality bug rather than a loud failure, which is why it gets a test.

The p99 rather than the max: one pathological bullet combination should be
fixed by shortening that bullet, not by holding the whole suite red. The max is
reported in the failure message so it is visible either way.
"""
import unittest

from test.helpers import REPO, load_generator
from test.prompt_budget import measure, percentile

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")
RESULTS = measure(LIVE, count=1500, seed=0)


class TestPromptBudget(unittest.TestCase):
    def test_p99_is_under_the_token_limit(self):
        for name, values in RESULTS.items():
            with self.subTest(prompt=name):
                p99 = percentile(values, 99)
                self.assertLess(
                    p99, gen.TOKEN_LIMIT,
                    "%s prompt p99 is %d against a limit of %d (max %d, %.1f%% "
                    "of rolls over) - the tail is being truncated"
                    % (name, p99, gen.TOKEN_LIMIT, max(values),
                       100.0 * sum(1 for v in values if v > gen.TOKEN_LIMIT)
                       / len(values)))

    def test_the_measurement_is_not_vacuous(self):
        """A silently empty sample would make the check above pass on nothing."""
        self.assertEqual(len(RESULTS["token"]), 1500)
        self.assertGreater(min(RESULTS["token"]), 200)
