import unittest

from test.helpers import load_generator

gen = load_generator()

POOL = [
    "grey coveralls",                      # neutral
    "a work apron",                        # neutral
    "lacquered plate || civ @alpha",       # alpha
    "a neon jacket || civ @beta",          # beta
    "a hybrid rig || @alpha @beta",        # both
]


class TestFilterByTheme(unittest.TestCase):
    def test_opens_own_tagged_bullets_and_all_neutral_ones(self):
        got = gen.filter_by_theme(POOL, "alpha", "Outfit")
        self.assertIn("grey coveralls", got)
        self.assertIn("a work apron", got)
        self.assertIn("lacquered plate || civ @alpha", got)

    def test_excludes_other_themes(self):
        got = gen.filter_by_theme(POOL, "alpha", "Outfit")
        self.assertNotIn("a neon jacket || civ @beta", got)

    def test_multi_tagged_bullets_are_reachable_from_either_theme(self):
        both = "a hybrid rig || @alpha @beta"
        self.assertIn(both, gen.filter_by_theme(POOL, "alpha", "Outfit"))
        self.assertIn(both, gen.filter_by_theme(POOL, "beta", "Outfit"))

    def test_no_theme_leaves_the_pool_untouched(self):
        self.assertEqual(gen.filter_by_theme(POOL, None, "Outfit"), POOL)

    def test_never_filters_the_pool_to_nothing(self):
        only_foreign = ["a neon jacket || @beta", "a chrome visor || @beta"]
        self.assertEqual(
            gen.filter_by_theme(only_foreign, "alpha", "Outfit"), only_foreign)

    def test_works_on_backdrop_three_segment_bullets(self):
        pool = [
            "A shot || A plain scene.",
            "A shot || A temple courtyard. || weather @alpha",
            "A shot || A neon street. || weather @beta",
        ]
        got = gen.filter_by_theme(pool, "alpha", "Backdrop")
        self.assertEqual(len(got), 2)
        self.assertNotIn("A shot || A neon street. || weather @beta", got)


if __name__ == "__main__":
    unittest.main()
