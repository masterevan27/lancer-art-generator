"""A Build bullet describes a silhouette, in the idiom the rest of its table uses.

`Build (she)` already has a settled way of saying how heavy a bust is: the
compound adjective. `small-busted`, `full-busted`, `tailored close through the
bust`. One bullet broke that pattern and reached for a bare anatomical noun
with an intensifier in front of it - "extremely large breasts".

That construction is the register of pornographic prompt text, and Krea
answers it in kind: it pulls the pose, the framing and the rendering toward
that register all at once, which fights both the bullet's own "athletic and
fit" and the restrained painterly house style the templates spend their whole
tail asserting. It also tends to distort proportion rather than describe a
shape, because there is no silhouette in the phrase for the model to draw.

The table's own comment already draws this line - "bust, hips, waist, curves"
is how it names what a 'figure' bullet is allowed to describe. This pins that
the bullets keep to it.
"""
import unittest

from test.helpers import REPO, load_generator

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")
BUILD_TABLES = {name: bullets for name, bullets in LIVE.items()
                if name.startswith("Build")}

# Bare anatomical nouns. The '-busted' and 'through the bust' forms these
# replace are silhouette descriptions; these are body-part nouns, which is the
# distinction that matters to the text encoder.
BARE_ANATOMY = ("breasts", "boobs", "tits")


class TestBuildIdiom(unittest.TestCase):
    def test_the_tables_are_not_silently_empty(self):
        """A renamed heading would make every check below pass on nothing."""
        self.assertIn("Build (she)", BUILD_TABLES)
        for name, bullets in BUILD_TABLES.items():
            with self.subTest(table=name):
                self.assertGreater(len(bullets), 3)

    def test_no_build_bullet_names_bare_anatomy(self):
        for name, bullets in BUILD_TABLES.items():
            for bullet in bullets:
                text = gen.split_flags(bullet)[0].lower()
                for word in BARE_ANATOMY:
                    with self.subTest(table=name, bullet=bullet, word=word):
                        self.assertNotIn(
                            word, text,
                            "this build names a body part where the rest of the "
                            "table names a silhouette; use the '-busted' "
                            "compound: %r" % bullet)

    def test_the_heavy_busted_build_survives_in_the_table_s_own_idiom(self):
        """Rewording it must not quietly delete the range it covered.

        The pool has to keep a build at the heavy end, or the reword becomes a
        content change disguised as a style fix.
        """
        texts = [gen.split_flags(b)[0].lower() for b in BUILD_TABLES["Build (she)"]]
        self.assertTrue(
            any("full-busted" in t and t != "slender but full-busted, with a clearly defined waist"
                for t in texts),
            "no heavy-busted build left in the pool: %r" % texts)


if __name__ == "__main__":
    unittest.main()
