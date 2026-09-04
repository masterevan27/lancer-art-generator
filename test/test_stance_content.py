"""Stance is token-only, and the token is cut to a transparent PNG.

The portrait takes its pose from Backdrop; Stance reaches only the token,
which renders on flat white so ComfyUI's RMBG pass can cut it out. A bullet
naming a ledge, a wall, machinery or the weather therefore describes something
that must not be in the image at all - and cannot be argued away by the
template's trailing "no environment", because generation runs at CFG 1.0 with
no negative prompt. A positive noun beats a trailing negative. The only fix is
not to say the word, and this test is what keeps it unsaid.
"""
import re
import unittest

from test.helpers import REPO, load_generator, bullets_for

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")

# Word -> why it cannot appear. Matched on word boundaries, so "background"
# does not trip "ground" and "wound" does not trip "wind".
BANNED = {
    "ledge": "scenery the token cannot show",
    "machinery": "scenery the token cannot show",
    "wall": "scenery the token cannot show",
    "ground": "scenery the token cannot show",
    "floor": "scenery the token cannot show",
    "chair": "furniture the token cannot show",
    "bench": "furniture the token cannot show",
    "seat": "furniture the token cannot show",
    "rain": "weather the token cannot show",
    "snow": "weather the token cannot show",
    "wind": "weather the token cannot show",
    "heat": "weather the token cannot show",
    "weather": "an environmental assertion the token cannot show",
}


class TestStanceContent(unittest.TestCase):
    def test_no_stance_bullet_names_anything_but_the_body(self):
        for bullet in bullets_for(LIVE, "Stance"):
            text = gen.split_flags(bullet)[0].lower()
            for word, why in BANNED.items():
                with self.subTest(bullet=bullet, word=word):
                    self.assertIsNone(
                        re.search(r"\b%s\b" % word, text),
                        "Stance bullet names %r - %s: %s" % (word, why, bullet))

    def test_the_stance_pool_is_not_empty(self):
        """A vacuous pass if the table were ever renamed out from under this."""
        self.assertGreater(len(bullets_for(LIVE, "Stance")), 30)


if __name__ == "__main__":
    unittest.main()
