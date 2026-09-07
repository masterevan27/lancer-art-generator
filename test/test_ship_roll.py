"""The user's hard constraint, asserted through the roller rather than the filter.

    "non-combat ships like cargo ships, should have minimal shielding and
     weapons (if any) and no launch catapults. combat ships depending on their
     type and size may have some or many of the previously described features."

test_ship_policy.py holds that against filter_by_ship_policy directly. This
file holds it against roll_ship, which is the only thing that proves the roller
reaches the filter at all - a roller that forgot the policy call would leave
that whole file green.

Reachability is asserted before legality, for test_role_lock.py's reason: an
assertion about what never happens passes on an empty set.
"""
import random
import unittest

from test.helpers import load_ship_generator

ship = load_ship_generator()
sp = ship.sp
TABLES = ship.parse_tables(ship.DEFAULT_TABLES)

NO_CATAPULT_TYPES = ("cargo", "support", "smuggler")


def roll_many(count, seed=0, overrides=None):
    return [ship.roll_ship(TABLES, random.Random(seed + n), overrides)
            for n in range(count)]


class TestDeterminism(unittest.TestCase):
    def test_the_same_seed_gives_the_same_ship(self):
        self.assertEqual(ship.roll_ship(TABLES, random.Random(7)),
                         ship.roll_ship(TABLES, random.Random(7)))

    def test_a_probe_changes_nothing(self):
        """The guarantee that makes trait_choices safe to call read-only."""
        plain = ship.roll_ship(TABLES, random.Random(7))
        probed = ship.roll_ship(TABLES, random.Random(7), probe={})
        self.assertEqual(plain, probed)


class TestTheRollIsClean(unittest.TestCase):
    def test_no_flag_segment_or_placeholder_survives(self):
        # Backdrop and Faction are the two three-segment tables
        # (generate-spaceship.py:876-882): roll_ship() deliberately keeps
        # their full "text || text || flags" string intact under these two
        # keys, because build_ship_prompts() and write_ship_dossier() re-split
        # them for themselves downstream (split_backdrop()/split_faction()).
        # generate-npc.py's own roll_npc() does the same for its identically-
        # shaped Backdrop/Faction fields - this is shared, tested precedent
        # (test/helpers.py's core_of()), not a gap in the strip. Every other
        # table's flags come off in the loop, so "||" is checked everywhere
        # else; "{" is still checked everywhere, since the '{}' substitution
        # pass runs over every key with no exception for these two.
        #
        # Backdrop and Faction are not just excused from the "no ||" check -
        # they are held to a stronger, positive one: exactly two separators,
        # matching their three segments exactly, every time over 200 seeds.
        # A blanket skip would also pass a Backdrop that kept a stray FOURTH
        # segment; this would not.
        for rolled in roll_many(200):
            for name, value in rolled.items():
                if name.startswith("_"):
                    continue
                with self.subTest(trait=name):
                    if name in ("Backdrop", "Faction"):
                        self.assertEqual(value.count("||"), 2)
                    else:
                        self.assertNotIn("||", value)
                    self.assertNotIn("{", value)

    def test_every_required_table_is_a_key_of_both_dicts(self):
        rolled = ship.roll_ship(TABLES, random.Random(1))
        for name in ship.REQUIRED_TABLES:
            with self.subTest(trait=name):
                self.assertIn(name, rolled)
                self.assertIn(name, rolled["_raw"])


class TestTheEquipmentPolicyThroughTheRoller(unittest.TestCase):
    def test_no_hauler_ever_gets_a_launch_catapult(self):
        seen = {t: 0 for t in NO_CATAPULT_TYPES}
        for rolled in roll_many(200):
            slug = ship.ship_type_of(rolled)
            if slug not in NO_CATAPULT_TYPES:
                continue
            seen[slug] += 1
            self.assertEqual(
                rolled["Launch catapult"], sp.NO_EQUIPMENT,
                "%s rolled a launch catapult: %r"
                % (slug, rolled["Launch catapult"]))
        for slug, n in seen.items():
            self.assertGreater(
                n, 0, "no %s ever rolled - the assertion is vacuous" % slug)

    def test_every_carrier_gets_one(self):
        carriers = 0
        for rolled in roll_many(400):
            if ship.ship_type_of(rolled) != "carrier":
                continue
            carriers += 1
            self.assertNotEqual(rolled["Launch catapult"], sp.NO_EQUIPMENT)
        self.assertGreater(carriers, 0, "no carrier ever rolled")

    def test_a_forced_hauler_still_cannot_get_one(self):
        for slug in NO_CATAPULT_TYPES:
            bullet = next(b for b in TABLES["Ship type"]
                          if slug in ship.split_flags(b)[1])
            for rolled in roll_many(40, seed=1000,
                                    overrides={"Ship type": bullet}):
                with self.subTest(slug=slug):
                    self.assertEqual(rolled["Launch catapult"], sp.NO_EQUIPMENT)


class TestTheReverseGates(unittest.TestCase):
    def test_a_huge_hull_is_never_a_patrol_boat(self):
        seen = 0
        for rolled in roll_many(300):
            if sp.size_of(rolled["_raw"]["Size"]) == "huge":
                seen += 1
                self.assertNotEqual(ship.ship_type_of(rolled), "patrol")
        self.assertGreater(seen, 0, "no huge hull was ever rolled - the "
                                    "assertion is vacuous")

    def test_a_fitted_catapult_means_carrier_or_battleship(self):
        seen = 0
        for rolled in roll_many(300):
            if rolled["Launch catapult"] != sp.NO_EQUIPMENT:
                seen += 1
                self.assertIn(ship.ship_type_of(rolled),
                              ("carrier", "battleship"))
        self.assertGreater(seen, 0, "no fitted launch catapult was ever "
                                    "rolled - the assertion is vacuous")


class TestTokenSizeMatchesTheRolledBand(unittest.TestCase):
    def test_every_ships_metadata_matches_hexes_for_its_band(self):
        for rolled in roll_many(200):
            band = sp.size_of(rolled["_raw"]["Size"])
            meta = ship.token_metadata(band)
            with self.subTest(band=band):
                self.assertEqual(meta["gridWidth"], sp.hexes_for(band))
                self.assertEqual(meta["hexes"], sp.hexes_for(band))


class TestTraitCascade(unittest.TestCase):
    def test_it_is_ordered_by_required_tables(self):
        cascade = ship.trait_cascade("Ship type")
        order = [ship.REQUIRED_TABLES.index(t) for t in cascade]
        self.assertEqual(order, sorted(order))

    def test_an_unknown_name_raises_rather_than_closing_to_empty(self):
        with self.assertRaises(ValueError):
            ship.trait_cascade("Hairstyle")
