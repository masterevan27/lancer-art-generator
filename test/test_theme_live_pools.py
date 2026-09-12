"""No theme may starve a live table it gates.

This file was test_theme_inert.py, whose job was the opposite one: while no
bullet carried an '@' tag, both theme filters had to be provable no-ops, and it
walked every live table asserting exactly that. Tagging has since begun, so the
no-op claim is false by design - the filters are now *supposed* to narrow the
pool - and that file's own docstring asked for its deletion at this point.

What did not stop mattering is the walk. filter_by_theme() and
apply_theme_share() are unit-tested against small synthetic pools in
test_theme_filter.py and test_theme_share.py; nothing else runs them over the
real content, where the pool shapes are set by whoever is authoring bullets
rather than by a fixture. So the walk stays and the assertions turn from "the
pool is unchanged" into "the pool is still worth rolling from" - which is the
guarantee test_theme_roll.test_every_themed_table_still_yields_a_value defers
to for anything beyond its own crash check.

Every test below walks not just THEMED_TABLES' base keys ('Hair', 'Outfit',
...) but every variant key that variant_table() can hand to a live roll ('Hair
(she) +', 'Outfit (she) +', ...) - see keys() below and helpers.table_keys().
The base `name` is still what gets passed to flags_for() / filter_by_theme() /
apply_theme_share(), even when the pool came from a variant key: those
functions branch on `name` to decide the bullet's '||' shape (Backdrop keeps
flags in a third segment, everything else in the second), and a variant shares
its base table's shape, not its own key's.
"""
import random
import unittest

from test.helpers import REPO, load_generator, table_keys

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")
THEMES = sorted(set(LIVE["Theme"]))

# How much of a table a theme is allowed to lose. A theme keeps every untagged
# bullet - the neutral floor - and drops only bullets tagged for some *other*
# theme, so a pool can shrink no further than the neutral content beneath it.
# Measured across the live file the worst case currently keeps 0.90 of its
# table, so this floor sits far below anything authored today: it fires when
# one theme has been tagged so heavily into a table that the others are left
# rolling from scraps, not on ordinary authoring.
POOL_FLOOR = 0.5

# And how far ABOVE THEME_SHARE a pool the roller actually draws from may sit.
# apply_theme_share duplicates a theme's own bullets until they hold
# THEME_SHARE of the pool *as it reaches that function*, and the drop filters
# that run after it take tagged and neutral bullets at different rates, so the
# realized figure drifts either side of the target - that drift is measured,
# not asserted, by `python -m test.theme_visibility`.
#
# What this ceiling is for is the other failure: duplication sized against a
# pool bigger than the one the copies land in. The group draw site did exactly
# that - the share was taken over the parent pool and every referenced group's
# members as one union, and the members were then split back out leaving all
# the copies behind - and the live Outfit pool read 0.80+ against a 0.60
# target, 192 copies of one bullet in 230 entries. Nothing anywhere asserted an
# upper bound, so the suite stayed green through it.
#
# 0.20 rather than the 0.15 the first draft of this ceiling used, because 0.15
# leaves no margin at all: measured across every theme at 20 seeds, the worst
# pool today is Outfit at exactly 0.750, where the 'dressy' and 'notac' drops
# take neutral bullets after the duplication step. 0.15 would pass on that
# number and fail on the next tagged Outfit bullet somebody writes. The same
# sweep on the union-sized code read 0.896, so 0.20 still catches the bug this
# exists for, with room on both sides of it.
SHARE_CEILING = 0.20

# Weapon is the one table whose later filters re-concentrate the pool rather
# than merely thin it. apply_weapon_policy restricts a mil Role to bullets
# flagged 'sidearm', and a theme that tags weapons tags armed ones, so the
# tagged share climbs after the duplication step instead of drifting around
# it. Worst measured across every theme at 80 seeds: 0.872. This is a
# regression ceiling for that table, not a figure it should be approaching -
# if it ever needs raising again, measure first and say what moved.
WEAPON_CEILING = 0.90


def keys(name):
    """Every live table key base name `name` reaches - see helpers.table_keys."""
    return table_keys(LIVE, name)


def pool_for(name, key, theme):
    """The bullets a roll of `theme` actually draws `key` from.

    Both filters, in the order roll_npc() applies them, so this measures what
    the generator sees rather than either function alone.
    """
    return gen.apply_theme_share(
        gen.filter_by_theme(LIVE[key], theme, name), theme, name)


class TestTaggingIsActuallyPresent(unittest.TestCase):
    """Everything below would pass vacuously on a wholly untagged file.

    That was this file's previous life, and the reason it is worth one
    assertion: with no tag anywhere the filters are no-ops, every pool keeps
    its full size, and the starvation tests below would report green while
    measuring nothing.

    Deliberately a floor of one tag across the whole file rather than a check
    that every theme in the Theme table has content of its own. Tagging is a
    pass in progress - 'tactical' currently carries no tagged bullet anywhere
    and 'corporate' carries one - and a per-theme assertion would turn an
    authoring queue into a red suite. The instrument for watching that queue
    drain is `python -m test.theme_visibility`, which reports the per-theme
    grid without failing on the thin end of it.
    """

    def test_the_live_tables_carry_theme_tags(self):
        tagged = sum(
            1 for name in gen.THEMED_TABLES for key in keys(name)
            for bullet in LIVE[key]
            if gen.themes_of(gen.flags_for(name, bullet)))
        self.assertGreater(
            tagged, 0,
            "no live bullet carries an '@' tag - either tagging was reverted "
            "or flags_for()/themes_of() stopped reading it, and every "
            "starvation check in this file is passing on nothing")


class TestNoThemeStarvesALiveTable(unittest.TestCase):
    def test_no_theme_empties_a_pool(self):
        """The hard floor. An empty pool is a crash, not a thin roll."""
        for name in gen.THEMED_TABLES:
            for key in keys(name):
                for theme in THEMES:
                    with self.subTest(table=key, theme=theme):
                        self.assertTrue(
                            pool_for(name, key, theme),
                            "%s is empty under theme %r" % (key, theme))

    def test_no_theme_drops_a_pool_below_the_floor(self):
        """The variety floor, and the guarantee this file exists for.

        Distinct bullets rather than pool length: apply_theme_share() reaches
        its target by repeating tagged bullets, so a pool can grow past its
        table's size while offering fewer different things to roll.
        """
        for name in gen.THEMED_TABLES:
            for key in keys(name):
                base = len(set(LIVE[key]))
                for theme in THEMES:
                    distinct = len(set(pool_for(name, key, theme)))
                    with self.subTest(table=key, theme=theme):
                        self.assertGreaterEqual(
                            distinct / base, POOL_FLOOR,
                            "%s offers only %d of its %d bullets under theme "
                            "%r - other themes have taken so much of this "
                            "table that %r is rolling from what is left"
                            % (key, distinct, base, theme, theme))


class TestNoThemeOverwhelmsALiveTable(unittest.TestCase):
    """The ceiling to go with the floor above, and the only one anywhere.

    Measured off `probe`, not off pool_for(): the pools above are what the two
    theme functions produce in isolation, and the whole class of bug this
    catches lives in what roll_npc() does with them afterwards. probe[name] is
    the list the roller is about to choose from, group members resolved and
    every later filter applied, which is the only pool a reader of an NPC
    could be misled by.

    Deterministic - a fixed seed per roll and every theme forced in turn, so a
    failure here is content or code moving, never a sample coming up short.
    """

    SEEDS = 20

    def pools(self, theme, seed):
        probe = {}
        gen.roll_npc(LIVE, random.Random(seed), {"Theme": theme}, probe=probe)
        return probe

    def test_no_recorded_pool_sits_far_above_the_target_share(self):
        for theme in THEMES:
            for seed in range(self.SEEDS):
                probe = self.pools(theme, seed)
                for name in gen.THEMED_TABLES:
                    pool = probe[name]
                    tagged = sum(1 for b in pool
                                 if theme in gen.themes_of(gen.flags_for(name, b)))
                    share = tagged / len(pool)
                    ceiling = (WEAPON_CEILING if name == "Weapon"
                               else gen.THEME_SHARE + SHARE_CEILING)
                    with self.subTest(table=name, theme=theme, seed=seed):
                        self.assertLessEqual(
                            share, ceiling,
                            "%s under theme %r draws from a pool that is "
                            "%.3f tagged against a target of %.2f - %d of %d "
                            "entries. Something is sizing the theme share "
                            "against a bigger pool than the one it lands in."
                            % (name, theme, share, gen.THEME_SHARE,
                               tagged, len(pool)))


if __name__ == "__main__":
    unittest.main()
