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
        """Dropping the pose claim must not drop the full-body framing with it.

        'no leg wraps or puttees' was listed here too, as though it were a
        fourth framing assertion. It never was - it is a wardrobe veto, and it
        is now deliberately gone; test_token_fidelity.py pins its absence and
        says why.
        """
        for phrase in ("whole figure in frame",
                       "to the soles of {possessive} shoes",
                       "clear empty space above and below",
                       "seven to eight heads tall"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, gen.TOKEN_TEMPLATE)

    def test_the_framing_asserts_a_scale_and_not_only_a_ratio(self):
        """"seven to eight heads tall" is a ratio, and a head too big for the
        canvas satisfies it - which is exactly what came back, correct
        proportions cropped at the shins. The scale has to be stated too."""
        self.assertIn("the head drawn small in frame", gen.TOKEN_TEMPLATE)

    def test_the_closing_tag_block_names_the_shot_distance(self):
        """The tag block is the position a diffusion model weights hardest,
        and it named the composition without ever naming the distance."""
        self.assertIn("Full-length wide shot", gen.TOKEN_TEMPLATE)
        self.assertIn("the whole figure clear of the frame edge",
                      gen.TOKEN_TEMPLATE)

    def test_the_shot_distance_leads_the_closing_tags(self):
        """Ahead of "centered composition", not buried after the style words.

        Anchored on the end of the background sentence, which is what the tag
        block opens after. That sentence used to end "no environment." and now
        ends "plain white void." - the negations it was built from are gone,
        for the reason TOKEN_TEMPLATE's comment gives. Only the anchor moved.
        """
        tags = gen.TOKEN_TEMPLATE[gen.TOKEN_TEMPLATE.index("plain white void."):]
        self.assertLess(tags.index("Full-length wide shot"),
                        tags.index("centered composition"))

    def test_the_portrait_keeps_its_own_framing(self):
        """The full-length tags belong to the token alone - the portrait is a
        deliberately close shot and must not inherit them."""
        self.assertNotIn("Full-length wide shot", gen.PORTRAIT_TEMPLATE)

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
