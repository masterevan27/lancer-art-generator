"""A theme tag is only read on the tables THEMED_TABLES names.

The permanent successor to test_theme_inert.py. That file asserts the live
tables carry no '@' tag *at all*, which stops being true - and stops being a
test - the moment Phase 4 starts tagging; it is deleted then. This file's
assertion is inverted, and so holds both before and after that pass: a tag may
appear on a gated table, and nowhere else. Without it, deleting the inert file
would leave the repository with nothing at all to say about where tags may
legally go.

The failure it guards is not hypothetical. Only the gated tables have their
'||' segment stripped before the value is rendered - roll_npc() splits Hair,
Feature, Headgear, Outfit and Gear, and split_backdrop() unpacks Backdrop.
Skin, Eyes, Demeanor, Accent and Height are interpolated verbatim by
build_prompts(), so '- chrome-inlaid irises || @cyberpunk' under '## Eyes'
ships the literal text '|| @cyberpunk' to Krea and into the dossier. That is
the same failure this branch already had to fix once, for Hair, Feature and
Headgear.
"""
import unittest

from test.helpers import REPO, load_generator, table_keys

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")


class TestThemeTagPlacement(unittest.TestCase):
    def test_no_ungated_table_carries_a_theme_tag(self):
        """'@' tags belong only on the six tables a rolled Theme gates.

        Scoped to REQUIRED_TABLES and their per-pronoun variants - the tables
        the generator actually rolls from. A '## Heading' the script never
        reads (the prose section at the top of the tables file parses as one)
        can hold whatever it likes; a tag there reaches no prompt.
        """
        for name in gen.REQUIRED_TABLES:
            if name in gen.THEMED_TABLES:
                continue
            for key in table_keys(LIVE, name):
                for bullet in LIVE[key]:
                    self.assertEqual(
                        gen.themes_of(gen.flags_for(name, bullet)), frozenset(),
                        "'## %s' is not one of the tables a Theme gates (%s), "
                        "so nothing strips its '||' segment: the tag would be "
                        "rendered into the Krea prompt and the dossier as "
                        "literal text. Move the bullet, or drop the tag. "
                        "Offending bullet: %r"
                        % (key, ", ".join(gen.THEMED_TABLES), bullet[:80]))

    def test_the_gated_tables_are_all_reachable(self):
        """Every name in THEMED_TABLES must exist in the live file.

        Cheap, and it is what keeps the test above honest: a THEMED_TABLES
        entry misspelled into a table that does not exist would silently
        widen the set this file exempts.
        """
        for name in gen.THEMED_TABLES:
            self.assertIn(name, LIVE, "THEMED_TABLES names %r, which the live "
                                      "tables file has no '## %s' for" % (name, name))


if __name__ == "__main__":
    unittest.main()
