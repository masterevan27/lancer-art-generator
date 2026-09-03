import unittest

from test.helpers import FIXTURE_TABLES, load_generator


class TestHarness(unittest.TestCase):
    def test_generator_loads(self):
        gen = load_generator()
        self.assertTrue(hasattr(gen, "roll_npc"))

    def test_fixture_has_every_required_table(self):
        gen = load_generator()
        tables = gen.parse_tables(FIXTURE_TABLES)
        missing = [t for t in gen.REQUIRED_TABLES if t not in tables]
        self.assertEqual(missing, [], "fixture is missing required tables")

    def test_fixture_rolls_an_npc(self):
        import random
        gen = load_generator()
        tables = gen.parse_tables(FIXTURE_TABLES)
        npc = gen.roll_npc(tables, random.Random(0))
        self.assertEqual(npc["name"], "Test Subject")


if __name__ == "__main__":
    unittest.main()
