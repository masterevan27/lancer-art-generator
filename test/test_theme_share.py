import unittest

from test.helpers import load_generator

gen = load_generator()


def build(tagged, neutral):
    return (["t%d || @alpha" % i for i in range(tagged)]
            + ["n%d" % i for i in range(neutral)])


def share_of(pool, theme="alpha", name="Outfit"):
    hits = sum(1 for x in pool if theme in gen.themes_of(gen.flags_for(name, x)))
    return hits / len(pool)


class TestApplyThemeShare(unittest.TestCase):
    def test_thin_theme_still_reaches_the_target_share(self):
        # 11 tagged against 60 neutral - the @grimdark case.
        out = gen.apply_theme_share(build(11, 60), "alpha", "Outfit")
        self.assertGreaterEqual(share_of(out), gen.THEME_SHARE)

    def test_fat_theme_also_reaches_it(self):
        # 56 tagged against 60 neutral - the @gundam case.
        out = gen.apply_theme_share(build(56, 60), "alpha", "Outfit")
        self.assertGreaterEqual(share_of(out), gen.THEME_SHARE)

    def test_every_neutral_bullet_stays_reachable(self):
        out = gen.apply_theme_share(build(3, 20), "alpha", "Outfit")
        for i in range(20):
            self.assertIn("n%d" % i, out)

    def test_every_tagged_bullet_stays_reachable(self):
        out = gen.apply_theme_share(build(3, 20), "alpha", "Outfit")
        for i in range(3):
            self.assertIn("t%d || @alpha" % i, out)

    def test_no_theme_leaves_the_pool_untouched(self):
        pool = build(3, 20)
        self.assertEqual(gen.apply_theme_share(pool, None, "Outfit"), pool)

    def test_no_tagged_bullets_leaves_the_pool_untouched(self):
        pool = ["n0", "n1", "n2"]
        self.assertEqual(gen.apply_theme_share(pool, "alpha", "Outfit"), pool)

    def test_no_neutral_bullets_leaves_the_pool_untouched(self):
        pool = ["t0 || @alpha", "t1 || @alpha"]
        self.assertEqual(gen.apply_theme_share(pool, "alpha", "Outfit"), pool)


if __name__ == "__main__":
    unittest.main()
