"""The Accent -> Glow colour rename must not break stored manifest entries.

All 135 entries in .generated-npcs.json store the trait under 'Accent', and
--regen-manifest rebuilds an NPC from that stored dict rather than re-rolling.
A bare rename would raise KeyError in build_prompts() for every one of them.
"""
import unittest

from test.helpers import load_generator

gen = load_generator()


class TestLegacyTraitNames(unittest.TestCase):
    def test_a_stored_accent_becomes_a_glow_colour(self):
        migrated = gen.migrate_traits({"Accent": "amber", "Role": "a dockworker"})
        self.assertEqual(migrated["Glow colour"], "amber")
        self.assertNotIn("Accent", migrated)

    def test_an_entry_already_using_the_new_name_is_untouched(self):
        migrated = gen.migrate_traits({"Glow colour": "teal-green"})
        self.assertEqual(migrated["Glow colour"], "teal-green")

    def test_a_new_name_present_alongside_the_old_one_wins(self):
        """Belt and braces: never clobber a current value with a stale one."""
        migrated = gen.migrate_traits({"Accent": "amber", "Glow colour": "teal-green"})
        self.assertEqual(migrated["Glow colour"], "teal-green")

    def test_the_input_dict_is_not_mutated(self):
        original = {"Accent": "amber"}
        gen.migrate_traits(original)
        self.assertEqual(original, {"Accent": "amber"})

    def test_the_table_is_named_glow_colour_in_required_tables(self):
        self.assertIn("Glow colour", gen.REQUIRED_TABLES)
        self.assertNotIn("Accent", gen.REQUIRED_TABLES)


if __name__ == "__main__":
    unittest.main()
