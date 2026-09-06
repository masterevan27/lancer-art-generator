"""The token must read as the same artist's work, and the same person, as the portrait.

The two shots are generated from separate templates, and the token's had
drifted: it dropped the facial-structure clause the portrait asserts, dropped
'high detail', and called itself an illustration where the portrait calls
itself a portrait. Rendered, that came back as a flat cel-shaded figure with a
generic anime face beside a painterly, halftoned, structurally-modelled
portrait of nominally the same NPC.

The token can never match the portrait's face *resolution* - it is a full-body
shot at seven to eight heads tall, so the head lands in roughly a third of the
pixels the half-body portrait gives it, and no wording closes that. What the
wording can do is stop the token asking for a different rendering.
"""
import random
import unittest

from test.helpers import FIXTURE_TABLES, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)


def both_prompts(seed=0, overrides=None):
    npc = gen.roll_npc(TABLES, random.Random(seed), overrides)
    return npc, gen.build_prompts(npc)


class TestFacialStructureParity(unittest.TestCase):
    """The portrait says what the face is built like; the token said nothing.

    Whichever FACE clause the roll earns, both shots must make the same claim -
    otherwise the model is free to model bone structure in one image and not in
    the other, which is exactly what 'the same character' cannot survive.
    """

    def test_both_prompts_assert_the_same_facial_structure(self):
        for seed in range(8):
            npc, (portrait, token) = both_prompts(seed)
            face = gen.FACE[npc["_young"]]
            with self.subTest(seed=seed):
                self.assertIn(face, portrait)
                self.assertIn(face, token)


class TestRenderingParity(unittest.TestCase):
    def test_both_prompts_ask_for_high_detail(self):
        """'high detail' sat in the portrait tail only."""
        _, (portrait, token) = both_prompts()
        self.assertIn("high detail", portrait)
        self.assertIn("high detail", token)


class TestNoNegatedWardrobe(unittest.TestCase):
    """A negation inside a positive prompt conditions on the thing it forbids.

    'no leg wraps or puttees' was carried as though it were a framing
    assertion. It is not: it is a wardrobe veto, and Krea's text encoder
    handles the two content words far more reliably than the 'no' in front of
    them. A generated token wearing the prompt verbatim came back with grey
    ankle wraps over its boots.
    """

    def test_the_token_template_does_not_name_leg_wraps(self):
        self.assertNotIn("puttees", gen.TOKEN_TEMPLATE)
        self.assertNotIn("leg wraps", gen.TOKEN_TEMPLATE)


# The clothing clause's possessive is pinned by test_clothing_possessive.py,
# which landed on main while this branch sat unrebased and covers it across all
# three pronoun forms, both templates, and the mid-sentence capitalisation trap.
# The duplicate assertions that used to sit here have been dropped in its favour.


class TestFullFigureIsPossessive(unittest.TestCase):
    """'She is facing the viewer, the whole figure in frame' reads as two entities."""

    def test_the_framing_clause_is_tied_to_the_subject(self):
        npc, (_, token) = both_prompts()
        self.assertIn("%s whole figure in frame" % npc["_pronouns"]["possessive"], token)
        self.assertNotIn("the whole figure in frame", token)


class TestNothingFlattensTheFigure(unittest.TestCase):
    """The token told the model to be flat and painterly in the same breath.

    Its background sentence read "a solid flat plain white, no texture, no
    gradient, no shadow, no environment", two sentences before a tail asking
    for "fine grain texture", "heavy grain" and "dense halftone screentone
    worked into every shadow". Every one of those four flattening words has a
    direct contradiction in the same prompt.

    The scoping - "The background ALONE is" - is what a diffusion text encoder
    is worst at, and this is the same failure as the leg-wraps veto one class
    up: the encoder takes the content words and largely drops the qualifier.
    So the model had to choose, and which way it fell varied by roll. That is
    the variance behind "some tokens come out right": tokens that picked the
    style tail look painterly, tokens that picked the flattening words come
    back cel-shaded with no grain and no halftone.

    The portrait carries none of these words and never drifts this way.

    The background must still read as empty and plain for the background
    removal pass, so what replaces them says that positively rather than as
    four negations that were not achieving it anyway - every generated token
    background is faintly mottled grey, not the flat white this asked for.
    """

    # Words that describe RENDERING, not content. Naming a thing the prompt
    # does not want ('no environment') is a different and survivable claim
    # from naming a quality the style tail spends its length asking for.
    FLATTENING = ("no texture", "no gradient", "no shadow", "flat plain white")

    def test_the_token_never_asks_for_the_opposite_of_its_own_style(self):
        _, (_, token) = both_prompts()
        for phrase in self.FLATTENING:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, token)

    def test_the_portrait_never_carried_these_either(self):
        """Pins the asymmetry that made the token the only shot that drifted."""
        _, (portrait, _) = both_prompts()
        for phrase in self.FLATTENING:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, portrait)

    def test_the_background_is_still_asserted_plain_white_and_empty(self):
        """The cutout pass depends on this; dropping the negations must not
        drop the requirement they were a bad way of expressing."""
        _, (_, token) = both_prompts()
        self.assertIn("white", token)
        self.assertIn("background", token)

    def test_the_style_tail_survives_in_both(self):
        _, (portrait, token) = both_prompts()
        for name, text in (("portrait", portrait), ("token", token)):
            with self.subTest(prompt=name):
                self.assertIn("heavy grain", text)
                self.assertIn("halftone screentone worked into every shadow", text)


if __name__ == "__main__":
    unittest.main()
