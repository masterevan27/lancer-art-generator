"""Spec §10's theme-visibility check, and a floor under the mechanism.

What this file does *not* assert is the interesting part. The obvious
assertion - every theme clears THEME_SHARE in every table - is false, and
provably so: `python -m test.theme_visibility --tables
test/fixtures/tables-themed.md` reports scav/Outfit at 0.36 against a target
of 0.60. That is not a bug in apply_theme_share(). It is filter_by_mil() and
apply_gear_policy() narrowing the pool *after* the weighting was computed, so
the share a roll actually draws at is not the share that was targeted.

So the assertions here split the claim in two:

  - apply_theme_share() keeps its real contract, measured where it applies:
    on the pool, before the later filters touch it.
  - the realized share never *collapses*, which is what broken weighting
    would look like - a floor, not the target.

The gap between those two is the thing spec §12 leaves as an open dial, and
the reason the instrument exists rather than a bare threshold test.

**What these tests do and do not protect**, established by neutering each
filter in turn rather than assumed:

  - Stubbing `apply_theme_share()` to `return options` fails three of them.
    That is the function this file guards.
  - Stubbing `filter_by_theme()` to `return options` leaves every test here
    green. That is not a gap - it is `apply_theme_share()` being a partial
    theme filter in its own right: it rebuilds the pool as
    `tagged * n + neutral`, so a bullet in neither list is dropped whether or
    not the exclusion gate ran. Visibility therefore survives the gate's
    removal; *cohesion* does not, and that is what
    test_theme_roll.test_no_npc_carries_a_foreign_theme is for. Do not
    "strengthen" these tests to cover it - they would be duplicating a check
    that already exists, on a property they do not measure.
"""
import random
import unittest

from test.helpers import REPO, load_generator, own_texts
from test.theme_visibility import measure, measure_cell

gen = load_generator()

THEMED_FIXTURE = REPO / "test" / "fixtures" / "tables-themed.md"
TABLES = gen.parse_tables(THEMED_FIXTURE)
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")

# One sample, shared by every test below - 800 rolls per theme across three
# themes is the expensive part of this file, and none of these tests mutate it.
RESULTS = measure(TABLES, count=800, seed=0)

# An unweighted themed roll lands near tagged/pool - about 0.04 for a
# one-bullet theme in a 24-bullet table, and 0.21 for a five-bullet one
# (both measured with apply_theme_share() stubbed out). The real spread under
# the later filters runs 0.36 to 0.76, so this floor sits between the two:
# it separates "skewed by a filter that runs afterwards" from "not weighted at
# all" without encoding the skew as if it were the target.
COLLAPSE_FLOOR = 0.25


class TestThemeShareContract(unittest.TestCase):
    """apply_theme_share() delivers its target on the pool it is handed."""

    def test_every_theme_clears_the_target_on_its_own_pool(self):
        for name in gen.THEMED_TABLES:
            for theme in sorted(set(TABLES["Theme"])):
                pool = gen.apply_theme_share(
                    gen.filter_by_theme(TABLES[name], theme, name), theme, name)
                tagged = sum(
                    1 for b in pool
                    if theme in gen.themes_of(gen.flags_for(name, b)))
                self.assertGreaterEqual(
                    tagged / len(pool), gen.THEME_SHARE,
                    "%s/%s: weighted pool holds %.3f of its own bullets, "
                    "below THEME_SHARE" % (theme, name, tagged / len(pool)))


class TestRealizedVisibility(unittest.TestCase):
    """What a rolled NPC actually gets, once every filter has run."""

    def test_no_theme_collapses_in_a_table_it_has_content_for(self):
        for theme, row in RESULTS.items():
            for name, cell in row.items():
                if not cell.tagged:
                    continue
                self.assertGreater(
                    cell.share, COLLAPSE_FLOOR,
                    "%s/%s: realized share %.3f is at collapse level - "
                    "apply_theme_share() is probably not weighting this pool "
                    "at all, rather than merely being skewed by a filter that "
                    "runs after it" % (theme, name, cell.share))

    def test_the_thin_theme_is_visible_at_all(self):
        """One tagged bullet against a 15-bullet neutral floor must still show.

        The whole reason apply_theme_share() exists. Without it a single scav
        bullet would come up about 1 roll in 24; the floor here is far above
        that but well under the target, so it fails on a broken mechanism
        rather than on the known civ/mil skew.
        """
        scav = RESULTS["scav"]
        thin = [(name, c) for name, c in scav.items() if c.tagged == 1]
        self.assertTrue(thin, "fixture must carry a single-bullet theme")
        for name, cell in thin:
            self.assertGreater(
                cell.share, 0.30,
                "scav/%s: a one-bullet theme rolled its own bullet only "
                "%.3f of the time" % (name, cell.share))

    def test_realized_share_is_measurably_below_the_pool_target(self):
        """Pin the gap the docs now describe, so it cannot silently close.

        If a later phase reorders the filters so weighting runs last, this
        fails - which is the point. The gap is a documented consequence of the
        current order, and a change to it should require changing this test
        and the docstring that explains it, not slip through green.
        """
        below = [(theme, name, c.share)
                 for theme, row in RESULTS.items()
                 for name, c in row.items()
                 if c.tagged and c.share < gen.THEME_SHARE]
        self.assertTrue(
            below,
            "no table fell below THEME_SHARE - if the filter order changed so "
            "that apply_theme_share() runs last, update this test and the "
            "'target on the pre-narrowing pool' wording in apply_theme_share's "
            "docstring and docs/generate-npc.md")


class TestMeasurementItself(unittest.TestCase):
    """The instrument has to be trustworthy before its numbers mean anything."""

    def test_an_untagged_theme_measures_zero(self):
        cell = measure_cell(TABLES, "Outfit", "cyberpunk", [])
        self.assertEqual(cell.tagged, 0)
        self.assertEqual(cell.share, 0.0)

    def test_tagged_counts_bullets_not_rendered_pronoun_variants(self):
        """Headgear bullets carry {Subject}/{wear}, so each renders two ways.

        Counting rendered texts would report twice the content that exists and
        make the tagged/pool ratio in the report incoherent.
        """
        cell = RESULTS["gundam"]["Headgear"]
        bullets = sum(
            1 for b in TABLES["Headgear"]
            if "gundam" in gen.themes_of(gen.flags_for("Headgear", b)))
        self.assertEqual(cell.tagged, bullets)
        self.assertGreater(
            len(own_texts(TABLES, "Headgear", "gundam")), cell.tagged,
            "fixture Headgear must use pronoun placeholders for this to bite")

    def test_hits_never_exceed_rolls(self):
        for theme, row in RESULTS.items():
            for name, cell in row.items():
                self.assertLessEqual(cell.hits, cell.rolls, "%s/%s" % (theme, name))

    def test_the_live_tables_measure_zero_until_they_are_tagged(self):
        """The pre-tagging baseline, and a second guard on Phase 1 inertness.

        Delete or invert this when the tagging pass begins - like
        test_theme_inert.py, a green run here stops meaning anything the moment
        content carries tags, and a stale copy would mask real regressions.
        """
        results = measure(LIVE, count=5, seed=0)
        tagged = sum(c.tagged for row in results.values() for c in row.values())
        self.assertEqual(
            tagged, 0,
            "live tables now carry theme tags - tagging has begun, so update "
            "test_theme_visibility.test_the_live_tables_measure_zero_until_"
            "they_are_tagged and delete test/test_theme_inert.py")


if __name__ == "__main__":
    unittest.main()
