"""The token template must not assert a pose - {stance} does that.

'standing at full height' was doing two jobs: asserting the framing (whole
body in shot, right proportions) and asserting a pose. Only the framing was
wanted. With a crouching Stance rolled the prompt claimed both standing and
crouching at once, and the model resolved that by rendering two figures - one
standing, one crouched on the platform the pose's 'raised ledge' implied.
"""
import random
import unittest

from test.helpers import FIXTURE_TABLES, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)


class TestTokenTemplatePose(unittest.TestCase):
    def test_the_template_makes_no_standing_claim(self):
        self.assertNotIn("standing at full height", gen.TOKEN_TEMPLATE)

    def test_the_template_does_not_claim_the_boots_are_planted(self):
        """False for every kneeling, sitting and crouching bullet in Stance."""
        self.assertNotIn("both boots planted", gen.TOKEN_TEMPLATE)

    def test_the_template_does_not_claim_the_arms_are_free(self):
        """Contradicts any pose braced on an arm."""
        self.assertNotIn("arms free", gen.TOKEN_TEMPLATE)

    def test_the_framing_assertion_survives(self):
        """Dropping the pose claim must not drop the full-body framing with it."""
        for phrase in ("whole figure in frame",
                       "to the soles of {possessive} feet",
                       "clear empty space above and below",
                       "seven to eight heads tall"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, gen.TOKEN_TEMPLATE)

    def test_the_framing_sentence_names_no_footwear(self):
        """It used to say "plain modern boots, no leg wraps or puttees", which
        is false for anyone barefoot, sandalled or in a sealed suit's integral
        feet. Faction and Outfit now describe dress specifically enough that
        the puttee drift the clause fought no longer happens, so the framing
        asserts only that the feet are in shot."""
        for phrase in ("boots", "puttees", "leg wraps"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, gen.TOKEN_TEMPLATE)

    def test_a_crouching_stance_produces_no_contradiction(self):
        npc = gen.roll_npc(TABLES, random.Random(0),
                           {"Stance": "crouched low and coiled, "
                                      "weight braced forward on one arm"})
        _, token = gen.build_prompts(npc)
        self.assertIn("crouched low and coiled", token)
        self.assertNotIn("standing at full height", token)


if __name__ == "__main__":
    unittest.main()
