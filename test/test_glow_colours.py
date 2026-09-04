"""Glow colours name a hue, never a light-emitting phenomenon.

Both templates wrap the rolled value as a glow - "A faint {glow} glow falls
across one side of her face", "a single {glow} glow the only saturated color".
So 'electric blue' renders as "electric blue glow" and the model draws actual
arcing electricity; 'neon cyan' pulls neon tubing into frame the same way. The
intent was only ever to name a shade.
"""
import re
import unittest

from test.helpers import REPO, load_generator, bullets_for

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")

# Words that name a light SOURCE rather than a shade. Anything here will be
# read as an instruction to draw the thing, not to tint the light.
PHENOMENA = ("electric", "neon", "laser", "plasma", "fluorescent", "led",
             "strobe", "flame", "spark")


class TestGlowColours(unittest.TestCase):
    def test_no_glow_colour_names_a_light_source(self):
        for bullet in bullets_for(LIVE, "Glow colour"):
            text = gen.split_flags(bullet)[0].lower()
            for word in PHENOMENA:
                with self.subTest(bullet=bullet, word=word):
                    self.assertIsNone(
                        re.search(r"\b%s\b" % word, text),
                        "Glow colour %r names a light source, not a hue - it "
                        "will be rendered rather than used as a tint" % bullet)

    def test_the_pool_is_not_empty(self):
        self.assertGreaterEqual(len(bullets_for(LIVE, "Glow colour")), 10)


if __name__ == "__main__":
    unittest.main()
