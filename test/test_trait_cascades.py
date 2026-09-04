"""The trait dependency map, the closures derived from it, and the theme draw.

Every list this module checks against is written out literally, which is
deliberate and worth defending: the module under test derives its cascades from
TRAIT_DEPENDENTS, so a test that derived its expectation from the same map
would agree with any map at all, including a wrong one. The point of these
assertions is to pin what the design doc claims by hand - twelve traits
re-rolled, thirteen kept - against what the map computes, so that the two
disagreeing is a failure rather than a silent drift.

The one property test that does derive both sides is the THEMED_TABLES
membership check, and it earns it: what it asserts is not a particular list but
the invariant that a table added to THEMED_TABLES next month cascades without
an edit here, which cannot be stated any other way.
"""
import contextlib
import io
import random
import unittest

from test.helpers import FIXTURE_TABLES, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)

# Cascade design doc §3, "What re-rolls" - the twelve, typed out from the doc
# rather than computed. In REQUIRED_TABLES order, which is the order
# trait_cascade() promises to return.
THEME_CASCADE_FROM_THE_DOC = (
    "Theme", "Hair", "Hair colour", "Feature", "Outfit", "Headgear", "Weapon",
    "Gear", "Backdrop", "Glow placement", "Weather", "Stance",
)

# The same section's "Kept - thirteen" list, in REQUIRED_TABLES order.
THEME_KEEP_SET_FROM_THE_DOC = (
    "Given names", "Family names", "Callsigns", "Pronouns", "Age", "Build",
    "Height", "Skin", "Eyes", "Demeanor", "Role", "Faction", "Glow colour",
)


class TestTheDependencyMap(unittest.TestCase):
    """The map itself, before anything is derived from it."""

    def test_every_name_in_the_map_is_a_real_table(self):
        """A typo in an edge would otherwise be a cascade that silently shrinks.

        trait_cascade() filters its result through REQUIRED_TABLES, so a
        misspelled dependent is not an error - it is a trait that quietly stops
        being re-rolled, which is exactly the class of failure this whole
        feature exists to prevent. Checked on both ends of every edge.
        """
        for source, dependents in gen.TRAIT_DEPENDENTS.items():
            self.assertIn(source, gen.REQUIRED_TABLES,
                          "%r is not a table the roller rolls" % source)
            for dependent in dependents:
                self.assertIn(
                    dependent, gen.REQUIRED_TABLES,
                    "%r depends on %r, which is not a table the roller rolls"
                    % (source, dependent))

    def test_no_trait_is_listed_as_its_own_dependent(self):
        """Harmless to the closure, but it would mean the map is being misread.

        An edge means "re-rolling this invalidates that". A self-edge says a
        trait invalidates itself, which is true of every trait and so carries
        no information; finding one means somebody wrote the reflexive part of
        the closure into the data instead of into trait_cascade().
        """
        for source, dependents in gen.TRAIT_DEPENDENTS.items():
            self.assertNotIn(source, dependents,
                             "%r lists itself as its own dependent" % source)


class TestTraitCascade(unittest.TestCase):
    """The closure trait_cascade() derives from that map."""

    def test_the_theme_cascade_is_the_twelve_the_doc_names(self):
        """The fact the whole approach rests on.

        The design doc names twelve traits by hand; the map is meant to derive
        that list rather than restate it. If this fails, the map and the doc
        have parted company and one of them is wrong - the map is not to be
        adjusted until which one is settled.
        """
        self.assertEqual(gen.trait_cascade("Theme"), THEME_CASCADE_FROM_THE_DOC)

    def test_THEME_CASCADE_is_bound_to_that_closure(self):
        """The name the doc and the import GUI both refer to.

        The GUI's server reads THEME_CASCADE out of this file by name, so the
        binding is part of the contract and not an implementation detail.
        """
        self.assertEqual(gen.THEME_CASCADE, THEME_CASCADE_FROM_THE_DOC)

    def test_the_keep_set_is_the_thirteen_the_doc_names(self):
        """The other half of §3's table, which is what the GUI dialog lists.

        Derived here the way the caller derives it - REQUIRED_TABLES minus the
        cascade - so that a trait falling out of the cascade shows up as a
        trait wrongly kept rather than merely as a shorter list.
        """
        kept = tuple(name for name in gen.REQUIRED_TABLES
                     if name not in gen.THEME_CASCADE)
        self.assertEqual(kept, THEME_KEEP_SET_FROM_THE_DOC)

    def test_the_two_halves_account_for_every_table(self):
        """Twelve and thirteen, and nothing rolled that is in neither.

        Guards the pair of literal lists above against being edited out of step
        with REQUIRED_TABLES: a table added to the roller and to neither list
        would leave both tests above green while the GUI's dialog silently
        stopped mentioning it.
        """
        self.assertEqual(
            sorted(THEME_CASCADE_FROM_THE_DOC + THEME_KEEP_SET_FROM_THE_DOC),
            sorted(gen.REQUIRED_TABLES))

    def test_every_themed_table_is_in_the_theme_cascade(self):
        """The property that makes a future themed table free.

        filter_by_theme() selects a themed table's bullets by the rolled theme,
        so a themed table kept across a new theme holds a bullet the roll could
        not have produced. Deriving both sides is the point here: this must
        hold for whatever THEMED_TABLES contains next month, not only for the
        seven it contains today.
        """
        for name in gen.THEMED_TABLES:
            self.assertIn(name, gen.THEME_CASCADE)

    def test_every_cascade_is_well_formed(self):
        """Subset of the rolled tables, contains its own trait, no duplicates.

        Run over every table rather than over the ones with dependents, since
        the same three properties are what let a caller hand any cascade
        straight to reroll_from_raw() as its free set.
        """
        for name in gen.REQUIRED_TABLES:
            cascade = gen.trait_cascade(name)
            self.assertIn(name, cascade,
                          "%s's cascade does not re-roll %s itself" % (name, name))
            self.assertEqual(len(cascade), len(set(cascade)),
                             "%s's cascade repeats a trait: %r" % (name, cascade))
            for trait in cascade:
                self.assertIn(trait, gen.REQUIRED_TABLES,
                              "%s's cascade names %r, which is not rolled"
                              % (name, trait))

    def test_every_cascade_follows_the_rollers_own_order(self):
        """A cascade that disagreed with REQUIRED_TABLES would read as a bug.

        Nothing downstream depends on the order for correctness - the free set
        is a membership test - but the cascade is printed by the CLI and listed
        by the GUI dialog, and two orderings of the same twelve traits look
        like two different answers.
        """
        for name in gen.REQUIRED_TABLES:
            cascade = gen.trait_cascade(name)
            self.assertEqual(
                list(cascade),
                sorted(cascade, key=gen.REQUIRED_TABLES.index),
                "%s's cascade is not in REQUIRED_TABLES order: %r"
                % (name, cascade))

    def test_a_trait_with_no_dependents_closes_to_itself(self):
        """What leaves the traits that already re-roll cleanly alone.

        Height, Skin, Eyes and the rest gate nothing, so routing them through a
        cascade has to be a no-op or Task 4 would widen eleven working re-rolls
        into eleven multi-trait ones.
        """
        for name in gen.REQUIRED_TABLES:
            if name not in gen.TRAIT_DEPENDENTS:
                self.assertEqual(gen.trait_cascade(name), (name,))

    def test_that_check_is_not_vacuous(self):
        """The fixture-guard shape: prove there are dependency-free traits.

        If every table gained a dependent the test above would pass while
        checking nothing at all.
        """
        free = [name for name in gen.REQUIRED_TABLES
                if name not in gen.TRAIT_DEPENDENTS]
        self.assertTrue(free, "every table has dependents, so the no-dependents "
                              "case above asserts nothing")

    def test_the_closure_terminates_on_the_age_build_cycle(self):
        """Age depends on Build and Build on Age, and that is not a defect.

        The 'young'/'figure' pairing is filtered in both directions by
        roll_npc(), so both directions are edges and the map is not a DAG. A
        closure written as a recursive walk would recur forever here; this test
        is what stops one from being written. Both ends are checked, since a
        walk can terminate from one and not the other.
        """
        self.assertEqual(gen.trait_cascade("Age"), ("Age", "Build"))
        self.assertEqual(gen.trait_cascade("Build"), ("Age", "Build"))

    def test_the_transitive_step_actually_runs(self):
        """A cascade two hops deep, so 'transitive' is more than a word.

        Role names only Faction, Outfit and Weapon in the map. Headgear, Gear
        and Stance are in its cascade only because the new Outfit and Weapon
        pull them in - which is the reach a direct-dependents-only closure
        would lose, handing back a Stance posed around the replaced rifle.
        """
        self.assertEqual(
            gen.trait_cascade("Role"),
            ("Role", "Faction", "Outfit", "Headgear", "Weapon", "Gear", "Stance"))
        self.assertNotIn("Headgear", gen.TRAIT_DEPENDENTS["Role"])
        self.assertNotIn("Stance", gen.TRAIT_DEPENDENTS["Role"])


class TestDifferentThemeDraw(unittest.TestCase):
    """The theme a Theme re-roll draws, which has to differ from the old one."""

    def draw(self, tables, current, seed):
        return gen.draw_different_theme(tables, current, random.Random(seed))

    def test_the_fixture_offers_more_than_one_theme(self):
        """Without this the never-repeats test below could not fail."""
        self.assertGreater(len(set(TABLES["Theme"])), 1)

    def test_it_never_returns_the_theme_it_was_given(self):
        for theme in set(TABLES["Theme"]):
            for seed in range(200):
                self.assertNotEqual(self.draw(TABLES, theme, seed), theme)

    def test_it_can_return_any_of_the_others(self):
        """Not merely 'not the old one' - every remaining theme stays reachable.

        A draw that always handed back the first surviving bullet would pass
        the test above and quietly make a third theme unrollable.
        """
        tables = {"Theme": ["alpha", "beta", "gamma"]}
        drawn = {self.draw(tables, "alpha", seed) for seed in range(50)}
        self.assertEqual(drawn, {"beta", "gamma"})

    def test_it_keeps_the_weighting_of_the_themes_that_remain(self):
        """Excluding a theme must not flatten the others into a uniform draw.

        parse_tables() expands 'x2 alpha' into two copies in a flat list, so
        dropping one theme's copies has to leave the rest in their original
        proportion - the property that makes excluding the old theme
        distribution-equivalent to drawing until it differs.
        """
        tables = {"Theme": ["alpha", "beta", "beta", "beta", "gamma"]}
        drawn = [self.draw(tables, "alpha", seed) for seed in range(600)]
        share = drawn.count("beta") / len(drawn)
        self.assertGreater(share, 0.60, "beta should draw about three times in four")
        self.assertLess(share, 0.90)

    def test_a_single_theme_table_keeps_its_theme_and_says_so(self):
        """No different theme exists, so the re-roll proceeds within this one.

        Refusing instead would be wrong: the seven themed tables still draw
        again inside that theme, and so do the four traits downstream of them,
        so the re-roll does change the NPC. The notice is what stops the
        unchanged Theme row being read as a failed draw.
        """
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            drawn = self.draw({"Theme": ["solo"]}, "solo", 0)
        self.assertEqual(drawn, "solo")
        self.assertIn("only one theme", stderr.getvalue())

    def test_a_multi_theme_draw_says_nothing(self):
        """The notice fires on the single-theme case only.

        A warning printed on every Theme re-roll would train the reader to skip
        the one that carries information.
        """
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            self.draw(TABLES, "alpha", 0)
        self.assertEqual(stderr.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
