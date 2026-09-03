import unittest

from test.helpers import REPO, load_generator

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")
THEMES = sorted(set(LIVE["Theme"]))


def table_keys(name):
    """Every live table key that base name `name` actually reaches.

    `variant_table()` does not roll from the base table alone: for a female
    subject it swaps in 'Hair (she)' wholesale if that key exists, and
    otherwise appends 'Hair (she) +' to the base pool. Either way, content
    sitting only in a variant key is content the generator can genuinely
    deal to a rolled NPC, so a test that checks only LIVE[name] is blind to
    roughly half of this file's appearance bullets. Deriving the key list
    from LIVE itself - rather than hardcoding '(she)'/'(he)' - means a
    variant added next month (a new pronoun, a new '+' table) is covered
    automatically, with no edit to this file required.
    """
    return [k for k in LIVE if k == name or k.startswith(name + " (")]


class TestUntaggedTablesAreUnaffected(unittest.TestCase):
    """Until Phase 4 tags content, both theme filters must be no-ops.

    DELETE THIS FILE when Phase 4 begins - once bullets carry '@' tags these
    filters are *supposed* to narrow the pool, and this becomes a false alarm
    rather than a regression detector.

    Every test below walks not just THEMED_TABLES' base keys ('Hair',
    'Outfit', ...) but every variant key that variant_table() can hand to a
    live roll ('Hair (she) +', 'Outfit (she) +', ...) - see table_keys()
    above. The base `name` is still what gets passed to flags_for() /
    filter_by_theme() / apply_theme_share(), even when the pool came from a
    variant key: those functions branch on `name` to decide the bullet's
    '||' shape (Backdrop keeps flags in a third segment, everything else in
    the second), and a variant shares its base table's shape, not its own
    key's.
    """

    def test_the_live_tables_carry_no_theme_tags_yet(self):
        for name in gen.THEMED_TABLES:
            for key in table_keys(name):
                for bullet in LIVE[key]:
                    self.assertEqual(
                        gen.themes_of(gen.flags_for(name, bullet)), frozenset(),
                        "%s is already tagged: %r - Phase 4 has started, "
                        "delete test/test_theme_inert.py"
                        % (key, bullet[:60]))

    def test_filter_by_theme_is_a_no_op(self):
        for name in gen.THEMED_TABLES:
            for key in table_keys(name):
                for theme in THEMES:
                    self.assertEqual(
                        gen.filter_by_theme(LIVE[key], theme, name), LIVE[key],
                        "%s changed under theme %r" % (key, theme))

    def test_apply_theme_share_is_a_no_op(self):
        for name in gen.THEMED_TABLES:
            for key in table_keys(name):
                for theme in THEMES:
                    self.assertEqual(
                        gen.apply_theme_share(LIVE[key], theme, name), LIVE[key],
                        "%s changed under theme %r" % (key, theme))

    def test_every_theme_still_rolls_a_full_pool(self):
        """No theme may starve any table it gates."""
        for name in gen.THEMED_TABLES:
            for key in table_keys(name):
                for theme in THEMES:
                    pool = gen.apply_theme_share(
                        gen.filter_by_theme(LIVE[key], theme, name), theme, name)
                    self.assertEqual(
                        len(pool), len(LIVE[key]),
                        "%s pool size changed under theme %r" % (key, theme))


if __name__ == "__main__":
    unittest.main()
