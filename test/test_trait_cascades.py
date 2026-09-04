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
from unittest import mock

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

# The other cascades worth pinning by hand, in REQUIRED_TABLES order. Written
# out for the same reason the twelve are: each one is a claim about which
# filters read which flags, and computing it from the map would make it agree
# with any map at all. Every trait that has dependents is here, so an edge
# added or dropped shows up as a named failure rather than as a cascade that
# quietly changed size.
#
# Age and Backdrop are the two that grew after the roller's filter chain was
# audited edge by edge: Age gates Hair colour's 'older' shades and reaches the
# cut through them, and a 'nogear' Backdrop's Gear correction is undone by the
# override paste that runs after it. Both were measured on the live tables
# before being added - 3 and 23 contradictions in 400 re-rolls, against none at
# all on a fresh roll.
#
# Build is absent, and its absence is the claim rather than an omission. The
# 'young'/'figure' pairing runs both ways in roll_npc(), so a map recording
# filters alone would carry both directions - but neither direction prevents a
# measured contradiction, and Build is one of the eleven traits the cascade
# spec's §5 promises keep firing on one click. The width therefore goes on
# Age's side, which promises nothing, and Build closes to itself. The class
# below asserts that for all eleven rather than for Build alone.
EXPECTED_CASCADES = {
    "Theme": THEME_CASCADE_FROM_THE_DOC,
    "Age": ("Age", "Build", "Hair", "Hair colour"),
    "Hair colour": ("Hair", "Hair colour"),
    "Role": ("Role", "Faction", "Outfit", "Headgear", "Weapon", "Gear", "Stance"),
    "Outfit": ("Outfit", "Headgear", "Weapon", "Gear", "Stance"),
    "Weapon": ("Weapon", "Gear", "Stance"),
    "Gear": ("Gear", "Stance"),
    "Backdrop": ("Gear", "Backdrop", "Glow placement", "Weather", "Stance"),
}


class PoolRecorder(random.Random):
    """A Random that keeps every pool roll_npc() drew from.

    roll_npc() reaches for randomness in exactly one shape - rng.choice(pool) -
    so recording the argument records the set of bullets the roller considered
    legal at that moment, after every filter that applies to it has run. That
    is the only way to ask "could the roller have produced this value here?"
    without writing a second copy of the filter chain in the test, which would
    be a copy that drifts.
    """

    def __init__(self, seed):
        super().__init__(seed)
        self.pools = []

    def choice(self, seq):
        self.pools.append(list(seq))
        return super().choice(seq)


def pools_by_table(npc):
    """Each table's final option pool for this exact NPC, keyed by table name.

    Re-runs the roller with every one of the NPC's own raw bullets pinned. Each
    draw still happens - a forced value replaces the drawn one after the pool
    has been built, not before - so each recorded pool is narrowed by exactly
    the values this NPC actually has, which is the question being asked.

    Pools are attributed to tables by content rather than by call order: a pool
    belongs to the one table whose bullets contain all of it. Attribution by
    counting calls would be a restatement of roll_npc()'s own loop, and would
    go quietly wrong the first time a draw is added or moved. Ambiguity raises
    rather than guessing, so a fixture that ever gave two tables the same
    bullet fails loudly instead of being mis-attributed - and it raises a real
    exception rather than asserting, because a bare `assert` is compiled out
    under `python -O` and this guard is the only thing standing between a
    mis-attributed pool and a completeness check that silently measures the
    wrong table.

    Later pools overwrite earlier ones for the same table, which matters for
    exactly one table: a 'nogear' Backdrop makes roll_npc() draw Gear a second
    time, from a pool with the hands-occupying bullets removed. That second
    pool is the one that decided the value, so it is the one to judge against.

    Pronouns and Theme are absent from the result by design. Both are drawn
    only when they were not forced, so pinning them skips the draw entirely -
    and neither is filtered by anything, so there is no pool to check.
    """
    rng = PoolRecorder(0)
    gen.roll_npc(TABLES, rng, dict(npc["_raw"]))
    subject = npc["Pronouns"].split("/")[0]
    reachable = {name: set(gen.variant_table(TABLES, name, subject))
                 for name in gen.REQUIRED_TABLES}

    out = {}
    for pool in rng.pools:
        # Stance is the one table whose pool holds (bullet, flags) pairs, so
        # that roll_npc() still has the raw line in hand when it picks one.
        bullets = [x[0] if isinstance(x, tuple) else x for x in pool]
        owners = [name for name in gen.REQUIRED_TABLES
                  if set(bullets) <= reachable[name]]
        if len(owners) != 1:
            raise RuntimeError(
                "pool %r could belong to any of %r - the fixture has given two "
                "tables the same bullet, so this attribution is no longer sound"
                % (bullets, owners))
        out[owners[0]] = bullets
    return out


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

    def test_a_name_that_is_not_a_table_raises(self):
        """An empty cascade would be a re-roll that changed nothing.

        The closure filters its result through REQUIRED_TABLES, so a
        misspelled name would otherwise close to () - and a caller hands the
        cascade straight to reroll_from_raw() as its free set, where an empty
        free set pins every trait and re-rolls none of them. The CLI would then
        print a re-roll and the render would come back identical, which is the
        silent no-op this whole feature exists to prevent.
        """
        with self.assertRaises(ValueError):
            gen.trait_cascade("Not A Table")

    def test_every_one_click_trait_closes_to_itself(self):
        """The eleven the lossy path re-rolls must each cascade to just itself.

        This is a promise made outside this file. The cascade spec's §5 says
        the eleven non-cascading buttons keep firing on one click, and the
        import GUI reads REROLLABLE_TRAITS out of the generator to draw them -
        so an edge added from any of the eleven turns a one-click button into a
        silent multi-trait re-roll, with no dialog and nothing in the GUI to
        notice it.

        Derived from REROLLABLE_TRAITS rather than listed, because the failure
        it guards against is a future map edit rather than today's map. Build
        is the one this was written for: it is one of the eleven AND a filter
        that roll_npc() runs in both directions, so the obvious map has an edge
        from it and the obvious map is wrong here. Nothing else in the suite
        can catch that - a test of what the cascade moves takes the cascade as
        its allowed set, so a widened cascade widens the assertion with it.
        """
        for name in gen.REROLLABLE_TRAITS:
            self.assertEqual(
                gen.trait_cascade(name), (name,),
                "%r re-rolls on one click with no confirmation, so its cascade "
                "has to be itself alone" % name)

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

    def test_every_cascade_with_dependents_is_the_one_expected(self):
        """The map's other claims, pinned by hand the way Theme's twelve are.

        Iterated over the literal table rather than over TRAIT_DEPENDENTS, so
        an edge added for a source that is not listed there is a failure too -
        a new cascade nobody wrote down is exactly the drift these literals
        exist to catch.
        """
        for name, expected in EXPECTED_CASCADES.items():
            self.assertEqual(gen.trait_cascade(name), expected,
                             "%s's cascade is not the one expected" % name)

    def test_the_expected_table_covers_every_trait_with_dependents(self):
        """Otherwise a whole cascade could change with nothing pinning it."""
        self.assertEqual(sorted(EXPECTED_CASCADES), sorted(gen.TRAIT_DEPENDENTS))

    def test_the_closure_terminates_on_a_cycle(self):
        """A recursive walk would recur forever; this stops one being written.

        The map held a real cycle until Build -> Age was dropped - Age depends
        on Build for the 'young'/'figure' pairing, which roll_npc() filters in
        both directions - and it was dropped for a reason about button
        behaviour rather than about graph shape, so the next filter audited in
        both directions puts one back. Asserting against today's data would
        therefore have made this test disappear exactly when the property it
        guards became untested.

        So the cycle is patched in rather than found. Both ends are checked,
        since a walk can terminate from one and not the other, and both are
        asserted to reach the same members - a cycle that terminated by
        dropping half of them on one pass would still be wrong. A timeout is
        not needed to make the failure legible: the walk either returns or the
        run never gets here.
        """
        cyclic = dict(gen.TRAIT_DEPENDENTS, **{"Build": ("Age",)})
        with mock.patch.object(gen, "TRAIT_DEPENDENTS", cyclic):
            both = ("Age", "Build", "Hair", "Hair colour")
            self.assertEqual(gen.trait_cascade("Age"), both)
            self.assertEqual(gen.trait_cascade("Build"), both)
        # And the patch really did put a cycle there, rather than testing the
        # map as it stands.
        self.assertNotIn("Build", gen.TRAIT_DEPENDENTS)
        self.assertEqual(gen.trait_cascade("Build"), ("Build",))

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


class TestTheMapIsComplete(unittest.TestCase):
    """Does the map cover the dependencies roll_npc() actually has?

    Every test above reads TRAIT_DEPENDENTS, so none of them can tell whether
    the map is missing an edge - they would agree with an incomplete map as
    readily as with a complete one. This one asks the roller instead, and never
    looks at the map except to get a cascade out of it.

    The question a cascade has to answer is: after re-rolling `target` and
    everything the map says goes with it, is every KEPT trait still a value the
    roller would draw for it? A missing edge is exactly a kept trait that is
    now illegal - the civ Faction on a mil Role, 138 times in 400, that started
    all of this. So: re-roll the cascade, re-run the roller with the result
    pinned while recording the pool it offers each table, and assert every kept
    bullet is in its own pool. Nothing here knows what the filters are; a
    hand-written list of known contradictions would only ever catch the ones
    somebody had already thought of, which is how the two edges below were
    missed in the first place.

    WHAT IT CANNOT SEE, stated plainly so it is not mistaken for a proof. This
    catches a dependency that narrows a POOL, and only when the fixture reaches
    the case. Deleting each of the map's twenty-three edges in turn, it catches
    eleven. The misses are not bad luck; three kinds are structural:

    - Dependencies that never narrow a pool. Backdrop -> Weather is read at
      prompt-build time by weather_sentence(), and Hair colour -> Hair is a
      '{colour}' substitution rather than a filter. No pool moves, so no kept
      value can fall outside one.
    - Dependencies that run backwards. Build -> Age, and Age -> Build, fire
      only in roll_npc()'s forced-value branches, which narrow an EARLIER
      table's pool; this harness pins every trait, so those branches never run.
    - Filters carrying an 'or options' fallback that the minimal fixture never
      drives to the narrow case. This is the largest group at eight, and it is
      not the Weapon edges alone: Theme -> Hair, Headgear and Weapon (the
      theme filter and its share weighting), Outfit -> Headgear, Weapon and
      Gear (the 'notac' strip and 'hardtech'), Role -> Weapon (the weapon
      policy), and Weapon -> Stance (the carried-flags filter). Naming them is
      the point of the paragraph: a limits statement that is vague about its
      own limits invites the reader to trust it further than it goes.

    What is worth saying for it is the measurement that motivated it: run
    against the map as it stood before roll_npc()'s filter chain was audited by
    hand, it independently finds both of the edges that audit found - Age ->
    Hair colour and Backdrop -> Gear. It is a real check on the class of
    dependency this feature is about, not a proof of completeness.
    """

    # Enough rolls to reach the fixture's flagged bullets - a 'young' Age, a
    # 'nogear' Backdrop, a two-handed Weapon, a theme that actually changes -
    # without making the suite slow. Each seed costs three rolls per target,
    # and the whole class runs in about four tenths of a second. Raising it
    # buys very little: at 120 the count above goes from eleven to twelve, and
    # the rest are the structural misses, which no number of seeds reaches.
    SEEDS = 60

    def test_no_kept_trait_is_left_outside_its_own_pool(self):
        for target in gen.REQUIRED_TABLES:
            cascade = gen.trait_cascade(target)
            for seed in range(self.SEEDS):
                npc = gen.roll_npc(TABLES, random.Random(seed))
                gen.reroll_from_raw(TABLES, npc, cascade,
                                    random.Random(seed + 9000))
                for name, pool in pools_by_table(npc).items():
                    if name in cascade:
                        continue
                    self.assertIn(
                        npc["_raw"][name], pool,
                        "re-rolling %s (cascade %r) left %s holding %r, which "
                        "the roller would not now draw - the map is missing an "
                        "edge from something in that cascade to %s"
                        % (target, cascade, name, npc["_raw"][name], name))

    def test_a_fresh_roll_is_already_consistent(self):
        """The baseline the check above is only meaningful against.

        Every trait of an untouched roll must sit in its own pool, since the
        roller drew it from there. If this fails, pools_by_table() is
        mis-attributing or the pinned re-run is not reproducing the NPC, and
        the test above is measuring the harness rather than the map.
        """
        for seed in range(20):
            npc = gen.roll_npc(TABLES, random.Random(seed))
            for name, pool in pools_by_table(npc).items():
                self.assertIn(npc["_raw"][name], pool,
                              "seed %d: a freshly rolled %s is not in its own "
                              "pool" % (seed, name))

    def test_the_recorder_sees_every_table_it_should(self):
        """Guards the check above against going vacuous by seeing nothing.

        A pool that stopped being recorded - a draw moved behind a condition,
        say - would silently drop that table from the loop above rather than
        fail. Pronouns and Theme are the two genuine absences: pinning either
        skips its draw, and neither is filtered by anything.
        """
        seen = set(pools_by_table(gen.roll_npc(TABLES, random.Random(0))))
        self.assertEqual(sorted(seen),
                         sorted(set(gen.REQUIRED_TABLES) - {"Pronouns", "Theme"}))


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
