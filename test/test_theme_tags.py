import unittest

from test.helpers import load_generator

gen = load_generator()


class TestThemesOf(unittest.TestCase):
    def test_no_flags_means_no_themes(self):
        self.assertEqual(gen.themes_of(()), frozenset())

    def test_behavioural_flags_are_not_themes(self):
        self.assertEqual(gen.themes_of(("hands", "gun", "mil")), frozenset())

    def test_strips_the_at_prefix(self):
        self.assertEqual(gen.themes_of(("@alpha",)), frozenset({"alpha"}))

    def test_reads_several_and_ignores_behavioural_flags(self):
        self.assertEqual(
            gen.themes_of(("civ", "@alpha", "notac", "@beta")),
            frozenset({"alpha", "beta"}),
        )

    def test_a_bare_at_is_not_a_theme(self):
        self.assertEqual(gen.themes_of(("@",)), frozenset())


class TestFlagsFor(unittest.TestCase):
    def test_two_segment_table(self):
        self.assertEqual(
            gen.flags_for("Outfit", "lacquered plate || civ @alpha"),
            ("civ", "@alpha"),
        )

    def test_backdrop_reads_its_third_segment(self):
        self.assertEqual(
            gen.flags_for("Backdrop", "A shot || A scene. || weather @alpha"),
            ("weather", "@alpha"),
        )

    def test_backdrop_without_flags_has_none(self):
        # Two segments only: the scene must never be mistaken for flags.
        self.assertEqual(
            gen.flags_for("Backdrop", "A shot || A scene with an @ in it."),
            (),
        )

    def test_unflagged_bullet_of_any_table(self):
        self.assertEqual(gen.flags_for("Outfit", "grey coveralls"), ())


if __name__ == "__main__":
    unittest.main()
