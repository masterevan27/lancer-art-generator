"""A cargo ship has no flight deck, and a carrier always does.

The brief this suite holds the generator to: "non-combat ships like cargo
ships, should have minimal shielding and weapons (if any) and no launch
catapults. combat ships depending on their type and size may have some or many
of the previously described features."

That sentence has two halves and they fail differently, which is why this file
is shaped the way it is.

The FORBIDDING half needs a hard filter. A freighter with a catapult is not an
odd pairing that a fallback could be forgiven for producing - it is the exact
thing the brief rules out, and the fallback would hand it over on precisely
the rolls where the pool ran thin. So the 'none' policy and the size floor do
not fall back, and this file's job - like test_role_lock.py's - is to hold the
margin that makes not falling back safe, because the function no longer checks
it for itself. What makes it affordable, and what the first class below
asserts directly, is that NOTHING is always a legal answer for ship equipment:
three of the four tables carry a 'none' bullet, so a hard filter never has to
choose between a wrong ship and an IndexError. The fourth is '## Command
bridge', which is in ALWAYS_FITTED_TABLES - every hull has somewhere to be
flown from - and the classes below hold the different margin THAT needs: the
locks must never hand it a blank, and no cell may be given the 'none' policy.

The PERMITTING half needs the opposite guard. "may have some or many" is easy
to satisfy by accident with a policy that quietly forbids everything - a cap
one band too low, a min-flag on every bullet in a table - and nothing fails
when it happens; the ships just come out bare. So most classes here assert
reachability first and legality second, in that order, for the reason
test_role_lock.py states: an assertion about what never happens passes on an
empty set. The sharpest form of it is the rule that a cell may reach zero real
answers or two, never exactly one: one real answer is not a constraint, it is
a uniform, and every render of that type shows the same mount.

Rolls against a fixture built in this file rather than against
fixtures/tables-minimal.md. That file is the baseline for roll-snapshot.json
and has no ship tables at all; more to the point, the assertions below are
about what the SIZE and MIL FLAGS do, so the fixture has to carry a bullet at
every band of every table, and civilian and military hardware at each, or it
would prove nothing about the filters it is testing.

The live-tables class skips itself until prompts/spaceship-generator-tables.md
exists. Delete that skip the day it lands - a skipping guard is a guard that is
not guarding, and the staleness modes it covers (a type slug reworded out from
under SHIP_TYPES, a size band the table and the matrix disagree about, a
policy pointing at a pool the file cannot fill) are exactly the ones that go
silent otherwise.
"""
import contextlib
import io
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import ship_policy as sp                                  # noqa: E402

LIVE_TABLES = REPO / "prompts" / "spaceship-generator-tables.md"

# The fixture. One bullet per band per table, civilian and military hardware
# at each, because the filters under test are exactly the things that sort
# them. Every bullet is one physical line, flags included, the way
# parse_tables() requires and the way a wrapped bullet in the real file would
# not be.
NO_WEAPON = "|| none"
PD_TURRETS = ("a pair of stubby point-defence turrets set either side of the "
              "dorsal spine || civ")
CARGO_DRUMS = ("a pair of squat point-defence drums ranked over the cargo "
               "racks || civ")
AUTOCANNON = ("a single autocannon mount bolted above the crew block "
              "|| civ max-medium")
GUN_BLISTERS = ("a pair of small gun blisters set into the hull shoulders "
                "|| mil min-small")
TURRET_RING = ("a light turret ring seated flush in the dorsal plating "
               "|| mil min-small")
BATTERIES = ("rows of turret batteries stepped along both flanks "
             "|| mil min-medium")
LANCE = ("a spinal lance running the full length of the hull "
         "|| mil min-huge")

NO_SHIELD = "|| none"
CIV_DEFLECTOR = ("a squat civilian deflector housing clamped to the dorsal "
                 "hull || civ")
DEBRIS_ARRAY = ("a debris-deflection array ringed around the cargo section "
                "|| civ")
SHIELD_VANES = ("paired shield vanes swept back from the shoulders of the hull "
                "|| mil min-medium")
SHIELD_BELT = ("a belt of armoured emitter blisters down each flank "
               "|| mil min-medium")
EMITTER_RING = ("a ring of heavy shield emitters banding the prow "
                "|| mil min-large")

NO_CATAPULT = "|| none"
# Two rail-tier catapults rather than one, for the reason test_weapon_role.py
# gives for stocking two blades: "a carrier always has a flight deck" is only
# measurably different from "a carrier always has THE flight deck" if there is
# more than one for it to reach.
CATAPULT_RAIL = ("a single short catapult rail recessed into the dorsal "
                 "plating || mil min-large")
CATAPULT_PAIR = ("a pair of angled catapult rails flanking the dorsal spine "
                 "|| mil min-large")
# The deck tier, and the reason it carries a ceiling as well as a floor: a
# huge battleship's 'light' cap resolves to the min-large tier, so a floor
# alone would hand it a full launch deck. 'max-large' says the HULL may not be
# bigger than a large one, which a carrier reaches at three hexes and a
# five-hex battleship cannot reach at all.
LAUNCH_DECK = ("an open launch deck cut clean through the hull "
               "|| mil min-large max-large")
FLIGHT_DECKS = ("twin open flight decks running most of the hull's length "
                "|| mil min-huge")

# No 'none' bullet: '## Command bridge' is in ALWAYS_FITTED_TABLES. The
# fixture states that the same way the tables file does, by not having one.
FLUSH_BLISTER = "a low flush bridge blister set into the dorsal line"
BOW_CANOPY = "a low armoured canopy sunk into the bow"
CIV_GALLERY = ("a wraparound bridge gallery ringing the forward hull "
               "|| civ min-medium")
BRIDGE_TOWER = ("a tiered bridge tower rising aft of the midline "
                "|| mil min-medium")
BRIDGE_SPIRE = ("a cathedral bridge spire crowned with spotlit statuary "
                "|| mil min-large")

# parse_tables() returns {heading: [bullets]}, so a dict literal is the same
# shape a parsed file would hand over - no tempfile needed, and no chance of
# the fixture drifting from what the assertions below assume it contains.
TABLES = {
    "Weapon": [NO_WEAPON, PD_TURRETS, CARGO_DRUMS, AUTOCANNON, GUN_BLISTERS,
               TURRET_RING, BATTERIES, LANCE],
    "Shield generator": [NO_SHIELD, CIV_DEFLECTOR, DEBRIS_ARRAY, SHIELD_VANES,
                         SHIELD_BELT, EMITTER_RING],
    "Launch catapult": [NO_CATAPULT, CATAPULT_RAIL, CATAPULT_PAIR,
                        LAUNCH_DECK, FLIGHT_DECKS],
    "Command bridge": [FLUSH_BLISTER, BOW_CANOPY, CIV_GALLERY, BRIDGE_TOWER,
                       BRIDGE_SPIRE],
}

# A '## Glow placement' stand-in, for the gate filter. Ungated bullets are
# most of it, the way they are most of the real table.
GLOW_FLANK = "runs the length of the hull seams along the flank"
GLOW_STERN = "burns deep in the engine housings at the stern"
GLOW_MUZZLES = ("gathers at the muzzles of the ship's guns as they charge "
                "|| combat armed")
GLOW_ENVELOPE = ("stands off the plating as a thin skin of light across the "
                 "whole shield envelope || combat shielded")
GLOW_DECK = ("lines the approach markings painted down the middle of the "
             "flight deck || deck")
GLOW_PLACEMENTS = [GLOW_FLANK, GLOW_STERN, GLOW_MUZZLES, GLOW_ENVELOPE,
                   GLOW_DECK]

# Every (type, size) pair the matrix can actually produce - the size bands are
# the type's own, so this is the whole space of legal ships and not a cross
# product with impossible corners in it.
EVERY_SHIP = [(t, size) for t in sp.SHIP_TYPES for size in sp.sizes_for(t)]


def text_of(bullet):
    return sp.split_flags(bullet)[0]


def roll(ship_type, size, seed):
    return sp.roll_equipment(TABLES, ship_type, size, random.Random(seed))


def rolls(ship_type, size, n=400):
    return [roll(ship_type, size, seed) for seed in range(n)]


@contextlib.contextmanager
def quiet():
    """Swallow the stderr line a deliberately malformed pool prints.

    Several tests below hand the filter a table that is missing something on
    purpose, to prove what it does when it narrows to nothing. The warning is
    the correct behaviour and is asserted where it matters; printing it during
    a green run just trains a reader to ignore stderr.
    """
    with contextlib.redirect_stderr(io.StringIO()):
        yield


def real_answers(pool):
    """The distinct pieces of hardware in a pool, ignoring 'nothing at all'."""
    return {text_of(b) for b in pool} - {sp.NO_EQUIPMENT}


class TestNothingIsAlwaysAnAnswer(unittest.TestCase):
    """The invariant that lets every other filter here run hard.

    filter_by_role_lock() in generate-npc.py may return nothing only because a
    fifty-bullet Gear pool cannot realistically empty, and test_role_lock.py
    carries that margin. This file's equivalent is stronger and simpler: the
    'none' bullet is a legal roll for three of the four tables, so a hard
    filter always has somewhere to land. The fourth carries the ALWAYS_FITTED
    exemption instead, and the class below holds ITS margin. Asserted before
    anything else because every class after this leans on both.
    """

    def test_every_equipment_table_carries_a_none_bullet(self):
        for name in sp.EQUIPMENT_TABLES:
            if name in sp.ALWAYS_FITTED_TABLES:
                continue
            with self.subTest(table=name):
                empty = [b for b in TABLES[name]
                         if "none" in sp.split_flags(b)[1]]
                self.assertTrue(empty, "'## %s' has no 'none' bullet" % name)

    def test_an_always_fitted_table_carries_no_none_bullet(self):
        """The converse, so the exemption cannot rot into a table that has
        both an empty bullet and a claim that it never rolls one."""
        for name in sp.ALWAYS_FITTED_TABLES:
            empty = [b for b in TABLES[name]
                     if "none" in sp.split_flags(b)[1]]
            with self.subTest(table=name):
                self.assertFalse(empty)

    def test_the_none_bullet_carries_no_prose(self):
        """NO_EQUIPMENT is the empty string, and the sentence builders drop an
        empty clause. A 'none' bullet that said "no weapons" in words would
        print "The hull carries no weapons." on every freighter instead - and
        at CFG 1.0 with no negative prompt, naming the gun is how the render
        gets one."""
        for name in sp.EQUIPMENT_TABLES:
            for bullet in TABLES[name]:
                if "none" in sp.split_flags(bullet)[1]:
                    with self.subTest(table=name):
                        self.assertEqual(text_of(bullet), sp.NO_EQUIPMENT)

    def test_the_none_bullet_carries_no_size_flag_that_narrows_it(self):
        """It has to survive the size filter at every band, or a hull would be
        left with an empty pool at the one moment the fallback matters."""
        for name in sp.EQUIPMENT_TABLES:
            for bullet in TABLES[name]:
                if "none" in sp.split_flags(bullet)[1]:
                    with self.subTest(table=name):
                        self.assertEqual(sp.size_bounds(bullet),
                                         (0, len(sp.SIZE_ORDER) - 1))

    def test_no_pool_is_ever_empty(self):
        """rng.choice([]) is an IndexError, and it would arrive on one roll in
        however many rather than at import - the failure mode this whole
        invariant exists to keep out of a render run."""
        for ship_type, size in EVERY_SHIP:
            for name in sp.EQUIPMENT_TABLES:
                with self.subTest(type=ship_type, size=size, table=name):
                    pool = sp.filter_by_ship_policy(
                        TABLES[name], ship_type, size, name)
                    self.assertTrue(pool)


class TestTheAlwaysFittedTables(unittest.TestCase):
    """'## Command bridge' has no empty bullet, and must never be handed one.

    Two critics wanted the bridge table given a 'none' bullet to satisfy the
    four-table invariant, and the table's own note refuses: a bridge is
    silhouette, and a hull with nowhere to be flown from is an unfinished
    drawing rather than a stealthier ship. The exemption is the code side of
    that argument, and these are the assertions that make it safe.
    """

    def test_no_cell_gives_an_always_fitted_table_the_none_policy(self):
        for table in sp.ALWAYS_FITTED_TABLES:
            for ship_type, row in sp.EQUIPMENT_POLICY.items():
                with self.subTest(type=ship_type, table=table):
                    self.assertNotEqual(row[table], "none")

    def test_the_default_policy_is_not_none_either(self):
        """A type this file has never heard of falls through to the defaults,
        and 'none' there would give it no bridge at all."""
        for table in sp.ALWAYS_FITTED_TABLES:
            with self.subTest(table=table):
                self.assertNotEqual(sp.policy_for("not-a-ship-type", table),
                                    "none")

    def test_the_locks_never_hand_an_always_fitted_table_a_blank(self):
        """The size filter narrowing to nothing is the one path that would,
        and it yields to the whole table here instead - the only place in
        ship_policy.py a hard filter re-admits what it removed."""
        with quiet():
            pool = sp.filter_by_ship_policy(
                [BRIDGE_SPIRE], "patrol", "small", "Command bridge")
        self.assertEqual(pool, [BRIDGE_SPIRE])
        self.assertNotIn(sp.NO_EQUIPMENT, [text_of(b) for b in pool])

    def test_a_none_policy_on_such_a_table_degrades_rather_than_blanking(self):
        """Forbidden by the first test in this class, so this is about the
        edit that adds one anyway: it must come out as 'any', not as a hull
        with no bridge."""
        row = sp.EQUIPMENT_POLICY["cargo"]
        original = row["Command bridge"]
        row["Command bridge"] = "none"
        try:
            with quiet():
                pool = sp.filter_by_ship_policy(
                    TABLES["Command bridge"], "cargo", "large",
                    "Command bridge")
        finally:
            row["Command bridge"] = original
        self.assertGreater(len(real_answers(pool)), 1)

    def test_every_ship_rolls_a_bridge(self):
        for ship_type, size in EVERY_SHIP:
            for i, ship in enumerate(rolls(ship_type, size, 120)):
                with self.subTest(type=ship_type, size=size, seed=i):
                    self.assertTrue(ship["Command bridge"])


class TestTheFilterInIsolation(unittest.TestCase):
    """filter_by_ship_policy() directly, before any rolling."""

    def test_none_returns_the_none_bullet_and_nothing_else(self):
        pool = sp.filter_by_ship_policy(
            TABLES["Launch catapult"], "cargo", "huge", "Launch catapult")
        self.assertEqual(pool, [NO_CATAPULT])

    def test_none_does_not_fall_back_to_the_whole_pool(self):
        """The hard lock. If this ever grows an 'or options' the way the
        preference filters have one, the brief's flat prohibition turns into a
        preference that loses whenever the pool runs thin."""
        pool = sp.filter_by_ship_policy(
            [CATAPULT_RAIL, FLIGHT_DECKS], "cargo", "huge", "Launch catapult")
        self.assertEqual([text_of(b) for b in pool], [sp.NO_EQUIPMENT])

    def test_none_synthesises_nothing_when_the_table_has_no_none_bullet(self):
        """A tables file missing its 'none' bullet is an authoring error, and
        the answer to it is still an unfitted ship - never the real pool."""
        pool = sp.filter_by_ship_policy(
            [CATAPULT_RAIL], "support", "large", "Launch catapult")
        self.assertEqual(pool, [sp.NO_EQUIPMENT])

    def test_the_size_floor_is_hard(self):
        """A one-hex boat cannot mount a kilometre-long lance, and the pool
        being thin afterwards is not a reason to hand it one."""
        with quiet():
            pool = sp.filter_by_ship_policy(
                [LANCE, NO_WEAPON], "destroyer", "small", "Weapon")
        self.assertNotIn(LANCE, pool)

    def test_the_size_floor_does_not_fall_back_either(self):
        pool = sp.filter_by_ship_policy(
            [LANCE, BATTERIES], "destroyer", "small", "Weapon")
        self.assertEqual([text_of(b) for b in pool], [sp.NO_EQUIPMENT])

    def test_a_bullets_own_ceiling_keeps_it_off_a_larger_hull(self):
        """'max-medium' is the other half of the vocabulary: a single
        autocannon mount on a five-hex hull reads as a mistake rather than
        as armament."""
        pool = sp.filter_by_ship_policy(
            TABLES["Weapon"], "cargo", "huge", "Weapon")
        self.assertNotIn(AUTOCANNON, pool)

    def test_a_ceiling_keeps_deck_scale_hardware_off_a_bigger_hull_too(self):
        """The same flag doing the load-bearing work in the matrix: a launch
        DECK is 'max-large', so a large carrier reaches it and a huge
        battleship - whose 'light' cap resolves to the min-large tier - does
        not. A floor alone could not have said that."""
        carrier = sp.filter_by_ship_policy(
            TABLES["Launch catapult"], "carrier", "large", "Launch catapult")
        battleship = sp.filter_by_ship_policy(
            TABLES["Launch catapult"], "battleship", "huge", "Launch catapult")
        self.assertIn(LAUNCH_DECK, carrier)
        self.assertNotIn(LAUNCH_DECK, battleship)

    def test_an_unflagged_bullet_reaches_every_hull(self):
        """The neutral pool, and the reason a hard size filter cannot starve
        one. Same property the theme tags rely on in generate-npc.py."""
        for ship_type, size in EVERY_SHIP:
            with self.subTest(type=ship_type, size=size):
                pool = sp.filter_by_ship_policy(
                    TABLES["Command bridge"], ship_type, size,
                    "Command bridge")
                self.assertIn(FLUSH_BLISTER, pool)

    def test_light_caps_below_the_hull(self):
        """A medium stealth hull rolls one-hex guns. A cap equal to the hull
        would make 'light' a synonym for 'any' - the quietest way for a policy
        row to stop meaning anything."""
        pool = sp.filter_by_ship_policy(
            TABLES["Weapon"], "stealth", "medium", "Weapon")
        self.assertNotIn(BATTERIES, pool)
        self.assertIn(PD_TURRETS, pool)

    def test_heavy_excludes_the_none_bullet(self):
        pool = sp.filter_by_ship_policy(
            TABLES["Launch catapult"], "carrier", "huge", "Launch catapult")
        self.assertNotIn(NO_CATAPULT, pool)
        self.assertTrue(pool)

    def test_heavy_drops_civilian_grade_hardware(self):
        """A commissioned warship is issued its hardware. Without this the
        'civ' flag was decorative outside the 'minimal' tier, and a destroyer
        could roll the small afterthought turret while a fleet carrier rolled
        a merchant's wraparound gallery for a bridge."""
        guns = sp.filter_by_ship_policy(
            TABLES["Weapon"], "destroyer", "medium", "Weapon")
        bridge = sp.filter_by_ship_policy(
            TABLES["Command bridge"], "carrier", "large", "Command bridge")
        self.assertNotIn(PD_TURRETS, guns)
        self.assertIn(BATTERIES, guns)
        self.assertNotIn(CIV_GALLERY, bridge)

    def test_the_military_preference_yields_rather_than_pinning_a_cell(self):
        """A PREFERENCE, and MIL_PREFERENCE_FLOOR is where it stops. A band
        with one military bullet keeps its civilian ones: a slightly civilian
        gun is a far smaller failure than every ship of a type carrying the
        identical mount."""
        pool = sp.filter_by_ship_policy(
            [BATTERIES, PD_TURRETS, CARGO_DRUMS], "cruiser", "medium",
            "Weapon")
        self.assertEqual(len(real_answers(pool)), 3)

    def test_the_any_policy_leaves_civilian_hardware_reachable(self):
        """Only 'heavy' and 'minimal' read the mil/civ split, and in opposite
        directions. 'any' leaves the civ bullets in - a screening destroyer's
        shielding
        is whatever it was refitted with, and the type row says 'any' for
        exactly that reason."""
        pool = sp.filter_by_ship_policy(
            TABLES["Shield generator"], "destroyer", "medium",
            "Shield generator")
        self.assertIn(CIV_DEFLECTOR, pool)

    def test_minimal_keeps_civ_hardware_and_nothing_military(self):
        pool = sp.filter_by_ship_policy(
            TABLES["Weapon"], "cargo", "huge", "Weapon")
        for bullet in pool:
            with self.subTest(bullet=bullet):
                self.assertNotIn("mil", sp.split_flags(bullet)[1])

    def test_minimal_weights_toward_nothing(self):
        """"(if any)" is a weighting, not a prohibition - the same knob
        CIVILIAN_UNARMED_COPIES is on the NPC side."""
        pool = sp.filter_by_ship_policy(
            TABLES["Weapon"], "cargo", "huge", "Weapon")
        empty = [b for b in pool if "none" in sp.split_flags(b)[1]]
        self.assertGreater(len(empty), len(pool) - len(empty))

    def test_minimal_falls_back_rather_than_rolling_nothing(self):
        """A PREFERENCE, unlike the two locks above. A table with no civ-grade
        bullets yet is an unfinished table, and filter_by_dress() makes the
        same trade for the same reason: an odd render beats a crash."""
        with quiet():
            pool = sp.filter_by_ship_policy(
                [BATTERIES], "cargo", "huge", "Weapon")
        self.assertEqual(pool, [BATTERIES])


class TestTheBriefsForbiddingHalf(unittest.TestCase):
    """The rolls the user's sentence rules out, over every seed and size."""

    def test_no_non_combat_ship_ever_rolls_a_catapult(self):
        for ship_type in ("cargo", "support", "smuggler"):
            for size in sp.sizes_for(ship_type):
                for i, ship in enumerate(rolls(ship_type, size)):
                    with self.subTest(type=ship_type, size=size, seed=i):
                        self.assertEqual(ship["Launch catapult"],
                                         sp.NO_EQUIPMENT)

    def test_no_ship_outside_the_two_capital_types_rolls_a_catapult(self):
        """The wider statement, so a type added later has to argue its way in
        rather than inherit a deck by default - which is what
        DEFAULT_EQUIPMENT_POLICY's 'none' for this column is for."""
        for ship_type, size in EVERY_SHIP:
            if ship_type in ("carrier", "battleship"):
                continue
            for i, ship in enumerate(rolls(ship_type, size, 120)):
                with self.subTest(type=ship_type, size=size, seed=i):
                    self.assertEqual(ship["Launch catapult"], sp.NO_EQUIPMENT)

    def test_a_cargo_ship_is_never_armed_beyond_civilian_grade(self):
        """The brief's own example. Size does not buy a licence: the five-hex
        band is the largest hull in the tables and rolls the same point-defence
        turrets a two-hex one does."""
        for size in sp.sizes_for("cargo"):
            for i, ship in enumerate(rolls("cargo", size)):
                with self.subTest(size=size, seed=i):
                    self.assertIn(ship["Weapon"],
                                  (sp.NO_EQUIPMENT, text_of(PD_TURRETS),
                                   text_of(CARGO_DRUMS), text_of(AUTOCANNON)))
                    self.assertIn(ship["Shield generator"],
                                  (sp.NO_EQUIPMENT, text_of(CIV_DEFLECTOR),
                                   text_of(DEBRIS_ARRAY)))

    def test_a_cargo_ship_is_usually_carrying_nothing_at_all(self):
        """"minimal ... (if any)" - not merely capped. The floor is stated as a
        share of rolls rather than a probability anyone should read off it: the
        fixture holds two civ weapons and the live table will hold several, so
        what is being asserted is that MINIMAL_NONE_COPIES is still stacking
        the empty bullet, not this number."""
        bare = sum(not ship["Weapon"] for ship in rolls("cargo", "large"))
        self.assertGreater(bare, 200)

    def test_no_small_hull_ever_rolls_capital_scale_hardware(self):
        for ship_type, size in EVERY_SHIP:
            if size != "small":
                continue
            for i, ship in enumerate(rolls(ship_type, size, 200)):
                with self.subTest(type=ship_type, seed=i):
                    self.assertNotEqual(ship["Weapon"], text_of(LANCE))
                    self.assertNotEqual(ship["Launch catapult"],
                                        text_of(FLIGHT_DECKS))
                    self.assertNotEqual(ship["Command bridge"],
                                        text_of(BRIDGE_SPIRE))

    def test_no_hull_rolls_hardware_its_band_cannot_carry(self):
        """The general form, checked against the bullets' own flags rather
        than against a list of names, so a fixture bullet added later is
        covered without an edit here."""
        by_text = {text_of(b): b
                   for name in sp.EQUIPMENT_TABLES for b in TABLES[name]}
        for ship_type, size in EVERY_SHIP:
            hull = sp.size_rank(size)
            for i, ship in enumerate(rolls(ship_type, size, 120)):
                for name, rolled in ship.items():
                    floor, ceiling = sp.size_bounds(by_text[rolled])
                    with self.subTest(type=ship_type, size=size, table=name,
                                      seed=i):
                        self.assertLessEqual(floor, hull)
                        self.assertGreaterEqual(ceiling, hull)

    def test_a_stealth_hull_keeps_its_silhouette(self):
        """The user's own spec for the type: shields unrestricted, but the
        guns and the bridge both capped, so nothing tall or bulky breaks the
        low profile the whole ship is for."""
        for size in sp.sizes_for("stealth"):
            for i, ship in enumerate(rolls("stealth", size)):
                with self.subTest(size=size, seed=i):
                    self.assertNotEqual(ship["Command bridge"],
                                        text_of(BRIDGE_TOWER))
                    self.assertNotEqual(ship["Command bridge"],
                                        text_of(BRIDGE_SPIRE))
                    self.assertNotEqual(ship["Weapon"], text_of(BATTERIES))


class TestTheBriefsPermittingHalf(unittest.TestCase):
    """"may have some or many" - the half that fails silently by producing
    bare ships, so every assertion here is a reachability one."""

    def test_every_carrier_rolls_a_catapult(self):
        for size in sp.sizes_for("carrier"):
            for i, ship in enumerate(rolls("carrier", size)):
                with self.subTest(size=size, seed=i):
                    self.assertTrue(
                        ship["Launch catapult"],
                        "a carrier came back with no flight deck")

    def test_a_carrier_is_always_shielded_and_always_has_a_bridge(self):
        for size in sp.sizes_for("carrier"):
            for ship in rolls("carrier", size, 200):
                self.assertTrue(ship["Shield generator"])
                self.assertTrue(ship["Command bridge"])

    def test_a_warship_is_always_armed(self):
        for ship_type in ("battleship", "cruiser", "destroyer"):
            for size in sp.sizes_for(ship_type):
                for i, ship in enumerate(rolls(ship_type, size, 200)):
                    with self.subTest(type=ship_type, size=size, seed=i):
                        self.assertTrue(ship["Weapon"])

    def test_only_the_largest_battleship_reaches_a_catapult(self):
        """The 'plausibly the largest battleships' clause, which is a LIGHT_CAP
        consequence rather than a row of its own - so it is worth pinning, or a
        later change to that dial moves it without anything failing. The rail
        tier is reachable; the deck tier is not, at either band."""
        huge = {s["Launch catapult"] for s in rolls("battleship", "huge", 200)}
        large = {s["Launch catapult"] for s in rolls("battleship", "large", 200)}
        self.assertIn(text_of(CATAPULT_RAIL), huge)
        self.assertIn(text_of(CATAPULT_PAIR), huge)
        self.assertNotIn(text_of(FLIGHT_DECKS), huge,
                         "a full flight deck is a carrier's, not a "
                         "battleship's")
        self.assertNotIn(text_of(LAUNCH_DECK), huge,
                         "a launch deck is a deck, whatever its floor says")
        self.assertEqual(large, {sp.NO_EQUIPMENT})

    def test_a_carrier_still_reaches_the_deck_tier(self):
        """The other side of that ceiling: what keeps a battleship off a deck
        must not keep a carrier off one, or the cap has just deleted the
        hardware the type exists for."""
        large = {s["Launch catapult"] for s in rolls("carrier", "large", 200)}
        huge = {s["Launch catapult"] for s in rolls("carrier", "huge", 200)}
        self.assertIn(text_of(LAUNCH_DECK), large)
        self.assertIn(text_of(FLIGHT_DECKS), huge)

    def test_a_patrol_boat_is_armed_but_only_lightly(self):
        """"small hulls, small guns" - reachability first, then the cap."""
        armed = {s["Weapon"] for s in rolls("patrol", "small")}
        self.assertTrue(armed - {sp.NO_EQUIPMENT},
                        "a patrol boat is a warship; it reached no weapon at "
                        "all")
        self.assertNotIn(text_of(BATTERIES), armed)
        self.assertNotIn(text_of(LANCE), armed)

    def test_a_stealth_ship_still_reaches_real_shielding(self):
        """'any' on one column of a type whose other columns are capped. If
        the cap ever leaks across columns this is what catches it."""
        shielded = {s["Shield generator"] for s in rolls("stealth", "medium")}
        self.assertIn(text_of(SHIELD_VANES), shielded)

    def test_a_cruiser_reaches_the_capital_band(self):
        """Cruiser is the one combat type with three bands, because the
        cathedral hull is a cruiser at that scale and the tables' best capital
        bullet is unrollable without it."""
        self.assertIn("huge", sp.sizes_for("cruiser"))
        armed = {s["Weapon"] for s in rolls("cruiser", "huge", 200)}
        self.assertIn(text_of(LANCE), armed)

    def test_no_cell_is_pinned_to_exactly_one_piece_of_hardware(self):
        """A policy that leaves a table one REAL bullet has replaced a
        constraint with a uniform, and every render of that type will show it.

        Zero real answers is legal and two or more is legal; exactly one is
        not. The zero cases are intended rather than accidental - the 'none'
        policy, and a 'light' cap that leaves a hull under the floor of every
        real bullet in the table, which is how a three-hex battleship ends up
        with no catapult while a five-hex one may roll a rail - so they are
        asserted to be that shape rather than skipped.
        """
        for ship_type, size in EVERY_SHIP:
            for name in sp.EQUIPMENT_TABLES:
                pool = sp.filter_by_ship_policy(
                    TABLES[name], ship_type, size, name)
                real = real_answers(pool)
                with self.subTest(type=ship_type, size=size, table=name):
                    self.assertNotEqual(
                        len(real), 1,
                        "this cell is pinned to one piece of hardware; only "
                        "'nothing at all' is allowed to be the single answer")
                    if not real:
                        self.assertEqual(
                            {text_of(b) for b in pool}, {sp.NO_EQUIPMENT})
                        continue
                    seen = {s[name] for s in rolls(ship_type, size, 200)}
                    self.assertGreater(len(seen), 1)


class TestTheEquipmentGates(unittest.TestCase):
    """The light lands on hardware the ship actually rolled.

    PLACEMENT_REQUIRES in generate-npc.py gates a glow placement against a
    prop in the scene; this gates it against the four rolls that just
    happened. Without it '## Glow placement' can light a flight deck on a
    grain freighter, which walks straight around the 'none' lock through a
    table the lock never sees - the one hole in the matrix that a policy row
    cannot close.
    """

    def test_a_gate_flag_needs_the_matching_roll(self):
        bare = {"Weapon": "", "Shield generator": "", "Launch catapult": "",
                "Command bridge": FLUSH_BLISTER}
        pool = sp.filter_by_gates(GLOW_PLACEMENTS, bare)
        self.assertEqual(pool, [GLOW_FLANK, GLOW_STERN])

    def test_a_satisfied_gate_keeps_its_bullet(self):
        fitted = {"Weapon": text_of(BATTERIES),
                  "Shield generator": text_of(SHIELD_VANES),
                  "Launch catapult": text_of(FLIGHT_DECKS)}
        pool = sp.filter_by_gates(GLOW_PLACEMENTS, fitted)
        self.assertEqual(pool, GLOW_PLACEMENTS)

    def test_a_gate_reads_one_roll_and_not_the_others(self):
        armed_only = {"Weapon": text_of(BATTERIES), "Shield generator": "",
                      "Launch catapult": ""}
        pool = sp.filter_by_gates(GLOW_PLACEMENTS, armed_only)
        self.assertIn(GLOW_MUZZLES, pool)
        self.assertNotIn(GLOW_ENVELOPE, pool)
        self.assertNotIn(GLOW_DECK, pool)

    def test_no_freighter_ever_lights_a_flight_deck(self):
        """End to end, which is the only form of this that proves anything:
        the gate has to hold against the rolls the matrix actually produces,
        not against a dict written to make it pass."""
        for ship_type, size in EVERY_SHIP:
            if ship_type in ("carrier", "battleship"):
                continue
            for i, ship in enumerate(rolls(ship_type, size, 60)):
                pool = sp.filter_by_gates(GLOW_PLACEMENTS, ship)
                with self.subTest(type=ship_type, size=size, seed=i):
                    self.assertNotIn(GLOW_DECK, pool)

    def test_a_carrier_reaches_the_deck_placement(self):
        reached = set()
        for ship in rolls("carrier", "huge", 60):
            reached |= set(sp.filter_by_gates(GLOW_PLACEMENTS, ship))
        self.assertIn(GLOW_DECK, reached)

    def test_an_ungated_placement_survives_every_ship(self):
        """The neutral pool again, one table over. It is what lets this filter
        be hard without ever going dark."""
        for ship_type, size in EVERY_SHIP:
            for ship in rolls(ship_type, size, 40):
                pool = sp.filter_by_gates(GLOW_PLACEMENTS, ship)
                with self.subTest(type=ship_type, size=size):
                    self.assertIn(GLOW_FLANK, pool)
                    self.assertTrue(pool)

    def test_an_all_gated_table_falls_back_rather_than_going_dark(self):
        """A PREFERENCE, and deliberately the opposite trade from the size
        filter's: the glow is the frame's one saturated colour, so a slightly
        wrong placement beats no light at all."""
        bare = {"Weapon": "", "Shield generator": "", "Launch catapult": ""}
        with quiet():
            pool = sp.filter_by_gates([GLOW_DECK, GLOW_MUZZLES], bare)
        self.assertEqual(pool, [GLOW_DECK, GLOW_MUZZLES])

    def test_the_gate_vocabulary_is_derived_from_the_tables(self):
        """The flags a placement bullet may carry are named once, in
        EQUIPMENT_GATES, so the tables file's note can quote them and a
        misspelling here cannot silently ungate a bullet."""
        self.assertEqual(set(sp.EQUIPMENT_GATES), set(sp.EQUIPMENT_TABLES)
                         - set(sp.ALWAYS_FITTED_TABLES))
        self.assertEqual(sorted(sp.EQUIPMENT_GATES.values()),
                         list(sp.EQUIPMENT_GATE_FLAGS))


class TestThePromptOmitsWhatIsNotThere(unittest.TestCase):
    """An unfitted ship says nothing, rather than saying nothing at length."""

    def test_an_unarmed_ship_has_no_armament_sentence(self):
        bare = {"Weapon": "", "Shield generator": "",
                "Launch catapult": "", "Command bridge": FLUSH_BLISTER}
        self.assertEqual(sp.armament_sentence(bare), "")

    def test_a_partly_fitted_ship_names_only_what_it_has(self):
        """The failure this replaces: "The hull carries , and ." - three empty
        slots punctuated as though they were full."""
        ship = {"Weapon": text_of(PD_TURRETS), "Shield generator": "",
                "Launch catapult": ""}
        sentence = sp.armament_sentence(ship)
        self.assertTrue(sentence.startswith("The hull carries a pair"))
        self.assertNotIn(" ,", sentence)
        self.assertNotIn("  ", sentence)
        self.assertNotIn("and .", sentence)

    def test_three_items_are_joined_as_a_list(self):
        """carry_sentence()'s join switched the whole separator on finding a
        compound bullet, which gave 'A and B and C' here on every plain
        warship roll and a comma list with no conjunction on a compound one.
        Ship bullets are compound far more often than NPC gear is, so the list
        commas stay and only the last connector moves."""
        self.assertEqual(sp.join_clause(["A", "B", "C"]), "A, B and C")
        self.assertEqual(sp.join_clause(["A", "B"]), "A and B")
        self.assertEqual(sp.join_clause(["A"]), "A")

    def test_a_compound_item_takes_an_oxford_comma(self):
        """The one case where the extra comma is doing work rather than
        decorating: without it, 'four turret batteries and a pair of torpedo
        tubes and a shield ring' is an unpunctuated run-on."""
        ship = {"Weapon": "four turret batteries and a pair of torpedo tubes",
                "Shield generator": "a shield ring",
                "Launch catapult": "a single rail"}
        sentence = sp.armament_sentence(ship)
        self.assertIn("torpedo tubes, a shield ring, and a single rail",
                      sentence)
        self.assertNotIn("tubes and a shield ring", sentence)

    def test_a_flush_hull_has_no_bridge_sentence(self):
        self.assertEqual(sp.bridge_sentence({"Command bridge": ""}), "")

    def test_no_rolled_ship_ever_prints_an_empty_clause(self):
        for ship_type, size in EVERY_SHIP:
            for i, ship in enumerate(rolls(ship_type, size, 120)):
                text = sp.armament_sentence(ship) + sp.bridge_sentence(ship)
                with self.subTest(type=ship_type, size=size, seed=i):
                    self.assertNotIn(" ,", text)
                    self.assertNotIn("  ", text)
                    self.assertNotIn(". .", text)
                    self.assertNotIn("carries .", text)

    def test_a_flag_never_reaches_a_prompt(self):
        for ship_type, size in EVERY_SHIP:
            for ship in rolls(ship_type, size, 60):
                text = sp.armament_sentence(ship) + sp.bridge_sentence(ship)
                self.assertNotIn("||", text)
                for flag in ("mil", "civ", "min-huge", "max-medium", "none",
                             "armed", "shielded", "deck"):
                    self.assertNotIn(" %s." % flag, text)


class TestTheMatrixIsWellFormed(unittest.TestCase):
    """The ways a 10x4 table of strings goes wrong without anything failing."""

    def test_every_ship_type_has_a_policy_row(self):
        self.assertEqual(set(sp.EQUIPMENT_POLICY), set(sp.SHIP_TYPES))

    def test_every_row_covers_every_equipment_table(self):
        for ship_type, row in sp.EQUIPMENT_POLICY.items():
            with self.subTest(type=ship_type):
                self.assertEqual(set(row), set(sp.EQUIPMENT_TABLES))

    def test_every_cell_names_a_policy_the_filter_implements(self):
        """A typo'd policy is not an error anywhere in filter_by_ship_policy() -
        it falls through to the 'any' tail and quietly unrestricts the cell."""
        for ship_type, row in sp.EQUIPMENT_POLICY.items():
            for table, policy in row.items():
                with self.subTest(type=ship_type, table=table):
                    self.assertIn(policy, sp.POLICIES)

    def test_the_defaults_cover_every_column(self):
        self.assertEqual(set(sp.DEFAULT_EQUIPMENT_POLICY),
                         set(sp.EQUIPMENT_TABLES))
        for policy in sp.DEFAULT_EQUIPMENT_POLICY.values():
            self.assertIn(policy, sp.POLICIES)

    def test_an_unlisted_type_gets_no_catapult(self):
        """The direction an accident has to fail in. generate-npc.py's
        DEFAULT_WEAPON_POLICY exists because seven Roles fell through an
        unlisted policy and came out armed; the equivalent slip here would put
        a flight deck on something that should not have one."""
        with quiet():
            policy = sp.policy_for("dreadnought-that-does-not-exist-yet",
                                   "Launch catapult")
        self.assertEqual(policy, "none")

    def test_the_brief_is_pinned_cell_by_cell(self):
        """The cells the user named in words. A later author is free to argue
        with any of them - but not to change one by accident."""
        wanted = {
            ("cargo", "Weapon"): "minimal",
            ("cargo", "Shield generator"): "minimal",
            ("cargo", "Launch catapult"): "none",
            ("support", "Launch catapult"): "none",
            ("smuggler", "Launch catapult"): "none",
            ("carrier", "Launch catapult"): "heavy",
            ("battleship", "Launch catapult"): "light",
            ("patrol", "Weapon"): "light",
            ("stealth", "Weapon"): "light",
            ("stealth", "Shield generator"): "any",
            ("stealth", "Command bridge"): "light",
        }
        for (ship_type, table), policy in wanted.items():
            with self.subTest(type=ship_type, table=table):
                self.assertEqual(sp.EQUIPMENT_POLICY[ship_type][table], policy)

    def test_every_type_can_roll_at_least_one_size(self):
        for ship_type, spec in sp.SHIP_TYPES.items():
            with self.subTest(type=ship_type):
                self.assertTrue(spec["sizes"])
                for band in spec["sizes"]:
                    self.assertIn(band, sp.SIZE_BANDS)

    def test_every_types_bands_are_contiguous_and_in_order(self):
        """A gap in a type's bands - small and large but not medium - is not a
        design, it is a typo, and it would show up only as a hull bullet that
        never rolls."""
        for ship_type, spec in sp.SHIP_TYPES.items():
            ranks = [sp.size_rank(b) for b in spec["sizes"]]
            with self.subTest(type=ship_type):
                self.assertEqual(ranks, sorted(ranks))
                self.assertEqual(ranks, list(range(ranks[0], ranks[-1] + 1)))

    def test_every_type_has_a_display_name(self):
        for ship_type, spec in sp.SHIP_TYPES.items():
            with self.subTest(type=ship_type):
                self.assertTrue(spec["name"].strip())

    def test_the_size_bands_agree_with_their_ordering(self):
        self.assertEqual(set(sp.SIZE_ORDER), set(sp.SIZE_BANDS))
        widths = [sp.SIZE_BANDS[b]["hexes"] for b in sp.SIZE_ORDER]
        self.assertEqual(widths, sorted(widths))
        self.assertEqual(widths, [1, 2, 3, 5])
        for band in sp.SIZE_ORDER:
            self.assertEqual(sp.hexes_for(band), sp.SIZE_BANDS[band]["hexes"])

    def test_every_band_has_a_light_cap_at_or_below_itself(self):
        """A cap above the hull would be a no-op; a cap the ordering does not
        know is a silent 'small' via size_rank()."""
        self.assertEqual(set(sp.LIGHT_CAP), set(sp.SIZE_ORDER))
        for band, cap in sp.LIGHT_CAP.items():
            with self.subTest(band=band):
                self.assertIn(cap, sp.SIZE_ORDER)
                self.assertLessEqual(sp.size_rank(cap), sp.size_rank(band))

    def test_the_flag_vocabulary_is_derived_and_not_typed_twice(self):
        for band in sp.SIZE_ORDER:
            with self.subTest(band=band):
                self.assertEqual(sp.SIZE_BANDS[band]["min"], "min-" + band)
                self.assertEqual(sp.SIZE_BANDS[band]["max"], "max-" + band)
                self.assertEqual(sp.SIZE_BANDS[band]["hex"],
                                 "hex%d" % sp.SIZE_BANDS[band]["hexes"])

    def test_the_exempt_tables_are_tables(self):
        """Both exemption lists are read by tests rather than by the filter, so
        a typo in one of them silently switches an invariant off instead of
        failing."""
        for name in sp.ALWAYS_FITTED_TABLES + sp.NEUTRAL_POOL_EXEMPT:
            with self.subTest(table=name):
                self.assertIn(name, sp.EQUIPMENT_TABLES)

    def test_an_always_fitted_table_is_never_neutral_pool_exempt(self):
        """The neutral pool and the 'none' bullet are the two things that keep
        a hard filter from emptying a table. A table may give up one of them.
        Giving up both leaves the filter with nothing to land on."""
        self.assertFalse(set(sp.ALWAYS_FITTED_TABLES)
                         & set(sp.NEUTRAL_POOL_EXEMPT))


class TestTheLiveTables(unittest.TestCase):
    """The ways this matrix goes stale silently once the tables land: a type
    slug or size flag the file no longer carries (the policy stops applying to
    anything), a band whitelist stated twice and drifting, and a policy
    pointing at a pool the file cannot fill (the ship comes out bare and
    nothing says so)."""

    @classmethod
    def setUpClass(cls):
        if not LIVE_TABLES.exists():
            raise unittest.SkipTest(
                "%s does not exist yet - delete this skip when it lands"
                % LIVE_TABLES.name)
        from test.helpers import load_generator
        cls.tables = load_generator().parse_tables(LIVE_TABLES)

    def test_every_equipment_table_exists(self):
        for name in sp.EQUIPMENT_TABLES:
            with self.subTest(table=name):
                self.assertIn(name, self.tables)

    def test_every_equipment_table_carries_a_none_bullet(self):
        for name in sp.EQUIPMENT_TABLES:
            if name in sp.ALWAYS_FITTED_TABLES:
                continue
            empty = [b for b in self.tables[name]
                     if "none" in sp.split_flags(b)[1]]
            with self.subTest(table=name):
                self.assertTrue(
                    empty,
                    "'## %s' has no bullet flagged 'none'. Every hard filter "
                    "in ship_policy.py lands on that bullet when it narrows; "
                    "without it they fall through to a synthesised blank and "
                    "the table's own wording is lost." % name)

    def test_an_always_fitted_table_carries_no_none_bullet(self):
        for name in sp.ALWAYS_FITTED_TABLES:
            empty = [b for b in self.tables[name]
                     if "none" in sp.split_flags(b)[1]]
            with self.subTest(table=name):
                self.assertFalse(
                    empty,
                    "'## %s' is in ALWAYS_FITTED_TABLES - every hull has one "
                    "of these - so an empty bullet here is a ship with no "
                    "bridge at all, which is an unfinished drawing rather "
                    "than a stealthier ship." % name)

    def test_every_equipment_table_carries_neutral_bullets(self):
        """The margin that makes the size filter safe to run hard - this
        file's answer to test_role_lock.py's 'the live pool survives every
        role'. It fails long before a roll actually comes back bare.

        '## Launch catapult' is exempt and NEUTRAL_POOL_EXEMPT says why: a
        catapult is a deck, and demanding three size-neutral ones would be
        demanding three catapults that fit on a courier."""
        for name in sp.EQUIPMENT_TABLES:
            if name in sp.NEUTRAL_POOL_EXEMPT:
                continue
            neutral = [b for b in self.tables[name]
                       if sp.size_bounds(b) == (0, len(sp.SIZE_ORDER) - 1)
                       and "none" not in sp.split_flags(b)[1]]
            with self.subTest(table=name):
                self.assertGreaterEqual(
                    len(neutral), 3,
                    "only %d bullets in '## %s' carry no size flag - size "
                    "flags have been applied far too widely, and small hulls "
                    "are being starved" % (len(neutral), name))

    def test_every_size_flag_in_the_file_is_one_this_module_reads(self):
        """An unrecognized flag is ignored rather than reported, everywhere in
        both generators - so 'min-massive' does not restrict anything, it just
        does nothing."""
        known = set()
        for band in sp.SIZE_ORDER:
            known |= {sp.SIZE_BANDS[band]["min"], sp.SIZE_BANDS[band]["max"]}
        for name in sp.EQUIPMENT_TABLES:
            for bullet in self.tables[name]:
                for flag in sp.split_flags(bullet)[1]:
                    if not (flag.startswith("min-") or flag.startswith("max-")):
                        continue
                    with self.subTest(table=name, flag=flag):
                        self.assertIn(flag, known)

    def test_every_type_slug_is_carried_by_a_live_ship_type_bullet(self):
        live = set()
        for bullet in self.tables["Ship type"]:
            live |= set(sp.split_flags(bullet)[1])
        for slug in sp.SHIP_TYPES:
            with self.subTest(slug=slug):
                self.assertIn(
                    slug, live,
                    "SHIP_TYPES defines %r but no '## Ship type' bullet "
                    "carries it - the row is unreachable" % slug)

    def test_every_ship_type_bullet_carries_exactly_one_slug(self):
        for bullet in self.tables["Ship type"]:
            slugs = [f for f in sp.split_flags(bullet)[1] if f in sp.SHIP_TYPES]
            with self.subTest(bullet=bullet):
                self.assertEqual(
                    len(slugs), 1,
                    "a '## Ship type' bullet must carry one and only one type "
                    "slug; ship_type_of() takes the first it finds and the "
                    "rest go silently unread")

    def test_every_ship_type_bullets_bands_match_the_matrix(self):
        """The whitelist is stated twice - in the bullet's flags, where an
        author reads it, and in SHIP_TYPES, where the filter reads it - and
        nothing compared them. A disagreement makes one of the two a lie, and
        the lie shows up as a (type, size) pair with no hull bullet, or as an
        equipment cell nobody reasoned about."""
        for bullet in self.tables["Ship type"]:
            slug = sp.ship_type_of(bullet)
            if slug is None:
                continue
            with self.subTest(slug=slug):
                self.assertEqual(
                    sp.bands_of(bullet), tuple(sp.sizes_for(slug)),
                    "'## Ship type' says %r may roll %s; SHIP_TYPES says %s"
                    % (slug, list(sp.bands_of(bullet)),
                       list(sp.sizes_for(slug))))

    def test_every_size_bullet_names_one_band_and_the_right_hex_width(self):
        """The Size table states the same fact a third way, as a hex count for
        the VTT. Nothing in this module reads a hex flag to make a decision,
        which is exactly why it needs checking: a bullet saying 'large hex2'
        is wrong on a map and right everywhere else."""
        seen = set()
        for bullet in self.tables["Size"]:
            flags = sp.split_flags(bullet)[1]
            bands = [f for f in flags if f in sp.SIZE_BANDS]
            with self.subTest(bullet=bullet):
                self.assertEqual(len(bands), 1,
                                 "a '## Size' bullet needs exactly one band "
                                 "flag; size_of() reads the first and ignores "
                                 "the rest")
                seen.add(bands[0])
                hexes = [f for f in flags if f.startswith("hex")]
                for flag in hexes:
                    self.assertEqual(flag, sp.SIZE_BANDS[bands[0]]["hex"])
        for band in sp.SIZE_ORDER:
            with self.subTest(band=band):
                self.assertIn(band, seen,
                              "no '## Size' bullet carries %r, so no ship can "
                              "ever roll that band" % band)

    def test_every_heavy_cell_has_something_to_roll(self):
        """'heavy' promises the ship always has one. Against a table that
        cannot supply it at that band, the promise degrades to a stderr line
        nobody reads during a render run. Two rather than one, because one
        answer is a uniform."""
        for ship_type, row in sp.EQUIPMENT_POLICY.items():
            for table, policy in row.items():
                if policy != "heavy":
                    continue
                for size in sp.sizes_for(ship_type):
                    pool = sp.filter_by_ship_policy(
                        self.tables[table], ship_type, size, table)
                    fitted = [b for b in pool
                              if "none" not in sp.split_flags(b)[1]]
                    with self.subTest(type=ship_type, size=size, table=table):
                        self.assertGreaterEqual(
                            len(fitted), 2,
                            "a %s %s has %d '## %s' bullets to choose from"
                            % (size, ship_type, len(fitted), table))

    def test_every_minimal_cell_has_civilian_hardware_to_roll(self):
        """The other silent degradation: 'minimal' with no 'civ' bullets in
        range falls back to the whole table, which is how a freighter ends up
        with a naval gun."""
        for ship_type, row in sp.EQUIPMENT_POLICY.items():
            for table, policy in row.items():
                if policy != "minimal":
                    continue
                for size in sp.sizes_for(ship_type):
                    pool = sp.filter_by_ship_policy(
                        self.tables[table], ship_type, size, table)
                    for bullet in pool:
                        with self.subTest(type=ship_type, size=size,
                                          table=table):
                            self.assertNotIn("mil", sp.split_flags(bullet)[1])

    def test_every_minimal_cell_reaches_real_hardware(self):
        """"minimal" is not "none". A civ tier that is empty above the medium
        band renders every large freighter in the campaign unshielded and
        every armed one carrying the identical mount, and neither of those
        fails anything else in this file: the pool is legal, it is just one
        bullet deep."""
        for ship_type, row in sp.EQUIPMENT_POLICY.items():
            for table, policy in row.items():
                if policy != "minimal":
                    continue
                for size in sp.sizes_for(ship_type):
                    pool = sp.filter_by_ship_policy(
                        self.tables[table], ship_type, size, table)
                    with self.subTest(type=ship_type, size=size, table=table):
                        self.assertGreaterEqual(
                            len({sp.split_flags(b)[0] for b in pool}
                                - {sp.NO_EQUIPMENT}), 2,
                            "a %s %s has fewer than two civ-grade '## %s' "
                            "bullets in range - 'minimal' has collapsed into "
                            "'always the same one' or 'never any'"
                            % (size, ship_type, table))

    def test_no_live_cell_is_pinned_to_one_piece_of_hardware(self):
        """The fixture's rule, against real content: zero real answers or two,
        never exactly one."""
        for ship_type, size in EVERY_SHIP:
            for table in sp.EQUIPMENT_TABLES:
                pool = sp.filter_by_ship_policy(
                    self.tables[table], ship_type, size, table)
                real = {sp.split_flags(b)[0] for b in pool} - {sp.NO_EQUIPMENT}
                with self.subTest(type=ship_type, size=size, table=table):
                    self.assertNotEqual(
                        len(real), 1,
                        "every %s %s rolls the same '## %s' entry: %r"
                        % (size, ship_type, table, sorted(real)))

    def test_no_live_roll_puts_capital_hardware_on_a_small_hull(self):
        """The end-to-end form of the whole file, against real content."""
        for ship_type, size in EVERY_SHIP:
            for seed in range(60):
                ship = sp.roll_equipment(
                    self.tables, ship_type, size, random.Random(seed))
                hull = sp.size_rank(size)
                for table, rolled in ship.items():
                    if not rolled:
                        continue
                    source = next(b for b in self.tables[table]
                                  if sp.split_flags(b)[0] == rolled)
                    floor, ceiling = sp.size_bounds(source)
                    with self.subTest(type=ship_type, size=size, table=table,
                                      seed=seed):
                        self.assertLessEqual(floor, hull)
                        self.assertGreaterEqual(ceiling, hull)

    def test_no_live_glow_placement_is_left_without_a_pool(self):
        """The gate filter against the real placement table, if it has landed
        yet. Three is not a magic number - it is the point below which a whole
        type's renders start showing the same light in the same place."""
        if "Glow placement" not in self.tables:
            self.skipTest("'## Glow placement' has not landed yet")
        for ship_type, size in EVERY_SHIP:
            for seed in range(40):
                ship = sp.roll_equipment(
                    self.tables, ship_type, size, random.Random(seed))
                pool = sp.filter_by_gates(self.tables["Glow placement"], ship)
                with self.subTest(type=ship_type, size=size, seed=seed):
                    self.assertGreaterEqual(len(set(pool)), 3)


if __name__ == "__main__":
    unittest.main()
