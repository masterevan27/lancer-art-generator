#!/usr/bin/env python3
"""The roll and the prompt builder for generate-spaceship.py.

This is the front half of that script - everything from loading the tables to
handing back the two finished prompt strings - written as its own module so it
could be authored beside the render half without the two colliding in one
file. It is meant to be folded into generate-spaceship.py verbatim; nothing
here has a __main__ and nothing here knows about ComfyUI.

The shape is the one docs/superpowers/specs/2026-09-06-spaceship-generator-
design.md §1 fixes: a new entry point that loads generate-npc.py BY PATH for
the parser, the theme machinery and the light machinery, imports ship_policy
normally, and changes not one line of either. generate-npc.py is 4,544 lines
under ~50 test files and its four source-readable constants are regex-parsed
out of the file text by a sibling GUI; an extraction that touched any of that
to share a parser would be trading fifty green tests for a feature that has
not shipped. The churn guard is a test (§8.12) rather than a refactor.

What ships have that people do not, and where each one lives:

    the type/size matrix        ship_policy.py, already written and tested
    the hull's grid footprint   the render half (design §4)
    no pronouns at all          ship_fields() below, nine lines where the NPC
                                file has pronoun_fields() plus five variant
                                tables

Stdlib only, same as every other generator here.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _load_art():
    """Import generate-art.py.

    The idiom is generate-npc.py:77-97's, for the reason it gives: the hyphen
    keeps the file off the normal import path, and renaming it would
    invalidate every README, docstring and shell history that names it.
    Registered in sys.modules before exec_module because @dataclass resolves
    annotations through sys.modules[cls.__module__].

    The one addition is the reuse guard, and it is load-bearing rather than an
    optimisation. _load_npc() below runs generate-npc.py's body, which runs
    ITS OWN copy of this loader under this same module name - so whichever of
    the two ran second would replace sys.modules["lancer_generate_art"] with a
    fresh module object, and `art.Entry` and `npc.art.Entry` would be two
    different classes with the same name and the same fields. Nothing would
    crash; an isinstance check somewhere downstream would simply start
    answering False. One module, loaded once, is the whole cure - and calling
    _load_npc() first (as the module body does) is what makes the guard fire.
    """
    name = "lancer_generate_art"
    loaded = sys.modules.get(name)
    if loaded is not None:
        return loaded
    path = SCRIPT_DIR / "generate-art.py"
    if not path.exists():
        raise SystemExit("generate-art.py not found next to this script (%s)"
                         % SCRIPT_DIR)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_npc():
    """Import generate-npc.py, and through it generate-art.py.

    generate-3d.py:34-57 already does exactly this, for DEFAULT_MANIFEST - one
    generator consuming another's module by path is live precedent in this
    repo rather than a new idea. Importing it is safe: its main() sits behind
    an `if __name__ == "__main__"` guard, so nothing runs on import beyond a
    few hundred microseconds of module body.
    """
    path = SCRIPT_DIR / "generate-npc.py"
    if not path.exists():
        raise SystemExit("generate-npc.py not found next to this script (%s)"
                         % SCRIPT_DIR)
    name = "lancer_generate_npc"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    # Registered before the body runs, same reason as above.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# npc first, so _load_art()'s guard finds the module generate-npc.py itself is
# holding rather than minting a second one. See _load_art().
npc = _load_npc()
art = _load_art()

import ship_policy as sp        # noqa: E402  - after the by-path loads above

# The borrowed surface, bound to module-level aliases so every use site is one
# grep away and an NPC-side rename fails in test/test_shared_surface.py rather
# than at render time. Design §1 pins the list at nineteen names; two more are
# bound here and both are named in the tables file's own "flags that still
# need a reader" table as obligations on this script:
#
#   filter_by_mil       '## Ship type' carries civ/mil and '## Faction',
#                       '## Detail' and '## Markings' are filtered on it.
#                       Without it a battleship rolls a courier line's yellow
#                       diamonds and a passenger boarding sleeve. The design's
#                       §1 list was written before that content existed; the
#                       tables file says outright it "must be added to it".
#   split_hair_colour   NOT borrowed - listed here only to say so. Ships have
#                       no analogue and flags_for() never reaches its branch.
#
# Everything else this module touches off npc.* goes through one of these
# names. Nothing is called as npc.something inline.
parse_tables = npc.parse_tables
variant_table = npc.variant_table
heading_for = npc.heading_for
split_flags = npc.split_flags
split_backdrop = npc.split_backdrop
split_faction = npc.split_faction
flags_for = npc.flags_for
themes_of = npc.themes_of
filter_by_theme = npc.filter_by_theme
apply_theme_share = npc.apply_theme_share
filter_by_mil = npc.filter_by_mil
THEME_SHARE = npc.THEME_SHARE
has_light_source = npc.has_light_source
light_hues = npc.light_hues
glow_hue_families = npc.glow_hue_families
filter_by_hue = npc.filter_by_hue
estimate_tokens = npc.estimate_tokens
TOKEN_LIMIT = npc.TOKEN_LIMIT
CHARS_PER_TOKEN = npc.CHARS_PER_TOKEN


# --------------------------------------------------------------------------
# Source-readable constants
#
# These four are LITERAL TOP-LEVEL ASSIGNMENTS AT COLUMN 0 and have to stay
# that way. The import GUI does not import this file - it reads the source
# text and regex-parses them with '^NAME\s*='-anchored patterns
# (lib/overrideTables.js:17-46), the same way it already reads generate-npc.py
# (:125, :168, :3329, :3415). Indent one of these into a class, build it from
# a loop, or wrap it in a function, and the parse misses silently: the GUI's
# trait dropdowns come back empty with no error anywhere.
# --------------------------------------------------------------------------

# Tables the prompt templates below require, in the order the roller draws
# them. Anything else in the markdown file is ignored.
#
# The ORDER is load-bearing in four places and every one of them reads a flag
# off an EARLIER table on the assumption it has already been rolled:
#
#   Ship type before Size      - sizes_for() is what makes a five-hex patrol
#                                boat unrollable, and it needs the slug.
#   Ship type and Size before  - filter_by_ship_policy() takes both, and the
#     the four equipment            EQUIPMENT_POLICY row is keyed on the slug.
#     tables
#   Ship type and Size before  - '## Hull' bullets carry a slug and a band and
#     Hull                        are filtered on both; nothing else keeps a
#                                 one-hex courier off a fleet carrier's
#                                 silhouette.
#   Backdrop before Glow       - a scene that commits to a colour of light is
#     colour and Glow             what filter_by_hue() matches the shade
#     placement                   against, and the placement's prop gates read
#                                 the scene's own flags.
#
# Reorder this list without reading those four and the filter each one
# describes goes quietly dead.
REQUIRED_TABLES = [
    "Name prefixes", "Ship names", "Theme", "Ship type", "Size", "Faction",
    "Hull", "Detail", "Weapon", "Shield generator", "Launch catapult",
    "Command bridge", "Markings", "Condition", "Backdrop", "Weather",
    "Glow colour", "Glow placement",
]

# The five tables a rolled Theme gates, and five only. Stated in the tables
# file's own header and pinned by test/test_ship_theme.py.
#
# Everything else describes the hull's numbers, its wear or its light rather
# than the visual world it comes from. '## Markings' is deliberately absent
# for the '## Gear' reason the NPC file gives: hazard chevrons and stencilled
# hull numbers are nobody's house style. And a '@tag' on a SINGLE-segment
# table - Size, Condition, Glow colour, Ship names - would not merely fail to
# theme anything: split_flags() would find no '||' and ship the literal text
# '|| @cyberpunk' to the image model and into the dossier.
THEMED_TABLES = ("Hull", "Detail", "Weapon", "Command bridge", "Backdrop")

# Which traits a re-roll of one trait invalidates: "re-roll this and these
# stop being answers the roller could have given". Same contract as
# generate-npc.py:168 - a pinned re-roll only filters in one direction, so a
# freed trait has to free its dependents with it or they keep values the new
# roll could not have produced.
#
# Every key in RAW_REROLLABLE_TRAITS must appear, '()' for a leaf, or
# trait_cascade() raises on it.
TRAIT_DEPENDENTS = {
    # Selection by theme rather than by a flag read, which is why this one
    # edge points at a whole tuple. Derived from THEMED_TABLES rather than
    # typed out, so a table themed next month cascades the day it is added.
    "Theme": THEMED_TABLES,

    # The widest edge in the map, and the one that earns the roll order. The
    # slug keys EQUIPMENT_POLICY, so all four equipment tables are filtered on
    # it; sizes_for() gates Size; '## Hull' bullets carry the slug and are
    # filtered on it; and the bullet's own civ/mil register is what
    # filter_by_mil() reads for Faction, Detail and Markings. A freed Ship
    # type that kept its Launch catapult is the brief's own prohibition
    # arriving through the one path that skips the lock.
    "Ship type": ("Size", "Faction", "Hull", "Detail", "Weapon",
                  "Shield generator", "Launch catapult", "Command bridge",
                  "Markings"),

    # The band is the second half of every hardware filter - filter_by_size()
    # is a hard floor and ceiling, and LIGHT_CAP is read off it - and it is
    # half of the Hull filter too. Backdrop is here for the 'max-' cap the
    # scene table carries: an enclosed commercial berth is a room a five-hex
    # hull does not fit inside, which is the same sentence about a different
    # kind of object.
    "Size": ("Hull", "Weapon", "Shield generator", "Launch catapult",
             "Command bridge", "Backdrop"),

    # Markings is filtered on the same civ/mil register Faction is, but the
    # register comes from '## Ship type' rather than from here, so this edge
    # is about content and not about a flag: the Faction visual and the
    # Markings bullet both describe painted-on identity, and a new operator
    # whose old stencilling is still on the hull reads as a mistake.
    "Faction": ("Markings",),

    # The silhouette gates the fittings that sit on it. Detail is masts,
    # docking arms and solar wings, which hang off the shape the Hull bullet
    # just described; Command bridge is the same argument one register up,
    # since a bridge is silhouette rather than payload.
    "Hull": ("Detail", "Command bridge"),
    "Detail": (),

    # All three equipment tables below carry the same edge, and it is
    # filter_by_gates() in ship_policy.py: a '## Glow placement' bullet
    # flagged 'armed' lights gun muzzles, 'shielded' lights a shield
    # envelope, 'deck' lights a flight deck, and each is true only of a ship
    # whose roll for that table came back fitted. Re-roll the Weapon to the
    # 'none' bullet with the placement pinned and the glow gathers at the
    # muzzles of guns that are no longer drawn - which routes around the
    # policy lock in the one direction the lock cannot see.
    "Weapon": ("Glow placement",),

    # Shield generator carries a second edge on top of that one, and it is the
    # ship's version of the NPC's 'Backdrop -> Glow colour'. A shield emitter
    # is deliberately authored with glow/lit/readout vocabulary so that
    # has_light_source() reads it, and it is the commonest fitted light on a
    # hull - so re-rolling it to the 'none' bullet can take away the only
    # thing that motivated a saturated colour being named at all.
    "Shield generator": ("Glow colour", "Glow placement"),
    "Launch catapult": ("Glow placement",),
    "Command bridge": (),
    "Markings": (),
    "Condition": (),

    # The scene gates all three: Weather is printed only against a 'weather'
    # flag on this bullet, the glow colour is matched against a hue the scene
    # commits to, and the placement's prop gates are matched flag-for-flag
    # against this bullet's own flag segment.
    "Backdrop": ("Weather", "Glow colour", "Glow placement"),
    "Weather": (),
    "Glow colour": (),
    "Glow placement": (),
    "Ship names": (),
    "Name prefixes": (),
}

# Which traits --reroll-trait can re-roll from an entry that recorded no raw
# bullets. Ships have carried rawTraits from their first manifest entry, so in
# practice RAW_REROLLABLE_TRAITS below always wins and nothing ever reads this
# - it is written out as a literal multi-line tuple naming the same sixteen
# anyway, and NOT as an alias and NOT as (), because the GUI's parser wants
# bullet-shaped content between the parens and an empty tuple would make it
# hide every re-roll button in the dialog on a parse quirk rather than on a
# decision anybody made.
REROLLABLE_TRAITS = (
    "Theme", "Ship type", "Size", "Faction", "Hull", "Detail", "Weapon",
    "Shield generator", "Launch catapult", "Command bridge", "Markings",
    "Condition", "Backdrop", "Weather", "Glow colour", "Glow placement",
)

# Which traits --reroll-trait can re-roll from an entry that DID record its
# raw bullets - which is every table but the two halves of the name.
#
# Bound to REQUIRED_TABLES rather than to a second copy of the sixteen names,
# so a table added to the roller becomes re-rollable the day it is added
# rather than the day somebody remembers this line. The two exclusions are the
# name: the ship's folder and its manifest id are both derived from it, so
# re-rolling one would not be a change in place.
RAW_REROLLABLE_TRAITS = tuple(t for t in REQUIRED_TABLES
                              if t not in ("Name prefixes", "Ship names"))


# --------------------------------------------------------------------------
# Duplicated and adapted from generate-npc.py
#
# Each of these closes over an NPC module global and so cannot be borrowed.
# They are short; the bodies are the originals' with the ship list, the ship
# map or the ship vocabulary substituted.
# --------------------------------------------------------------------------

def check_tables(tables, path, repeated=()):
    """generate-npc.py:1271-1282, reading this file's REQUIRED_TABLES."""
    for name in repeated:
        print("! %s: '## %s' appears more than once; the blocks are merged, so "
              "any bullet listed twice rolls twice as often" % (path.name, name),
              file=sys.stderr)

    missing = [name for name in REQUIRED_TABLES if name not in tables]
    if missing:
        raise SystemExit(
            "%s is missing the table(s) the prompt templates need: %s"
            % (path.name, ", ".join(missing))
        )


def trait_cascade(name):
    """`name` plus every trait a re-roll of it invalidates, transitively.

    generate-npc.py:305-362 against this file's map, and copied rather than
    parameterised for the reason design §1 gives: that one closes over
    TRAIT_DEPENDENTS and orders by REQUIRED_TABLES, both module globals.

    Written as a worklist over a `seen` set rather than as a recursive walk,
    because the map is not promised to be acyclic and this must not depend on
    it. The NPC map held a cycle until recently and lost it for a reason about
    button behaviour rather than about graph shape, so the next filter audited
    in both directions will put one back. Nothing is enqueued twice, so the
    walk terminates on a cycle rather than recurring forever - do not replace
    this with a recursion that assumes a DAG.

    Ordered by REQUIRED_TABLES rather than by discovery order, so a cascade
    can never disagree with the order the roller draws in.

    An unknown name raises rather than closing to an empty tuple. The
    REQUIRED_TABLES filter below would otherwise swallow a misspelling and
    hand back (), and a caller feeds this straight to the re-roll path as its
    free set - so a typo would pin every trait and re-roll nothing, reporting
    a re-roll that changed the ship not at all.
    """
    if name not in REQUIRED_TABLES:
        raise ValueError("%r is not a table the roller rolls" % name)
    seen = {name}
    pending = [name]
    while pending:
        for dependent in TRAIT_DEPENDENTS.get(pending.pop(), ()):
            if dependent not in seen:
                seen.add(dependent)
                pending.append(dependent)
    return tuple(trait for trait in REQUIRED_TABLES if trait in seen)


# The tables the rolled '## Ship type' bullet's civ/mil register filters.
#
# Not the equipment tables, which carry civ/mil too: those are read by
# filter_by_ship_policy(), which uses the flag for the 'minimal' and 'heavy'
# tiers rather than for a flat split, and running filter_by_mil() over them as
# well would take the 'none' bullet out of a civilian hull's pool.
MIL_TABLES = ("Faction", "Detail", "Markings")

# The prop gates a '## Glow placement' bullet may name, and what the rolled
# '## Backdrop' has to say for each to be true of it.
#
# The NPC version of this pair (generate-npc.py:625-699) matches a REGEX over
# the scene's prose, because an NPC backdrop's props - a wall, a ground, a
# skyline of signage - are things the sentence mentions in passing and nobody
# was going to flag twenty scenes by hand. The ship table was authored the
# other way round: every '## Backdrop' bullet already carries its own flag
# segment naming what is in the frame, so this matches FLAG AGAINST FLAG and
# has no patterns at all. That is the tables file's instruction and it is the
# better half of the trade - a regex over "a wall of white peaks" is the exact
# false positive the NPC gate's own comments are about.
#
# A placement carrying none of these is ungated and true of every scene, which
# is most of the table and is what keeps the filter from starving.
PLACEMENT_REQUIRES = ("atmosphere", "combat", "debris", "dock", "hull",
                      "interior", "planetlight", "vacuum")

# The mirror: a placement flag whose named scene flag must NOT be present.
#
# One entry, and it is a claim about motion rather than about a prop. A glow
# that "burns deep in the engine housings and throws hard light forward" is a
# ship under power; a ship in a berth is moored, its drives cold, and lighting
# them inside an enclosed dock is both wrong and a fire. 'dock' is the flag
# that says moored, so it is the flag this reads.
PLACEMENT_FORBIDS = {"under-way": "dock"}


def filter_by_placement_prop(options, scene_flags):
    """Placements whose named prop the rolled Backdrop actually has.

    generate-npc.py:671-699 with the regex pair swapped for the flag pair
    above. A preference with the usual fallback: the ungated bullets keep the
    light on the hull itself and always qualify - eight of the sixteen in the
    live table - so the pool never empties in practice.
    """
    def ok(bullet):
        for flag in split_flags(bullet)[1]:
            if flag in PLACEMENT_REQUIRES and flag not in scene_flags:
                return False
            denied = PLACEMENT_FORBIDS.get(flag)
            if denied is not None and denied in scene_flags:
                return False
        return True

    kept = [x for x in options if ok(x)]
    return kept or options


# --------------------------------------------------------------------------
# The reverse-direction gates
#
# Two of them, and each exists for the reason roll_npc()'s forced_figure
# (:1787) and forced_carried_helmet (:1817) exist: the pinned trait is rolled
# LATER than the trait it has to constrain, so the constraint has to run
# backwards up the order.
#
# Both are PREFERENCES with a fallback and a note on stderr, matching
# filter_by_affiliation's trade (:1443-1451): the pool is small and
# GUI-editable, and a --set-trait that is silently refused is worse than one
# that is warned about.
# --------------------------------------------------------------------------

def filter_backdrop_by_size(options, band):
    """'## Backdrop' bullets whose size flags admit a hull of band `band`.

    sp.filter_by_size() is what this should be, and the tables file's own
    "flags that still need a reader" table says to call it here - but it
    cannot be called on this table. That function reads a bullet's flags
    through ship_policy's split_flags(), which is the TWO-segment splitter,
    and '## Backdrop' is one of the two three-segment tables: partitioning
    'SHOT || SCENE || flags' on the first '||' hands back the entire scene
    sentence as the flag tuple, so every noun in it is tested as a size flag
    and a berth's 'max-medium' is never found. flags_for() in generate-npc.py
    exists for exactly this asymmetry, and ship_policy.py's own docstring says
    to add a seam rather than teach split_flags about a third segment - but
    ship_policy.py is not this work's to edit, so the seam is here.

    Hard with no fallback, matching the function it stands in for: a
    'max-medium' scene is an enclosed commercial berth, and a five-hex hull
    does not fit inside a room. Safe to run hard for the same reason - two of
    the twenty-six live bullets carry a ceiling and the other twenty-four are
    neutral, so the pool cannot empty.
    """
    hull = sp.size_rank(band)
    kept = []
    for bullet in options:
        flags = split_backdrop(bullet)[2]
        floor, ceiling = 0, len(sp.SIZE_ORDER) - 1
        for rank, name in enumerate(sp.SIZE_ORDER):
            if sp.SIZE_BANDS[name]["min"] in flags:
                floor = max(floor, rank)
            if sp.SIZE_BANDS[name]["max"] in flags:
                ceiling = min(ceiling, rank)
        if floor <= hull <= ceiling:
            kept.append(bullet)
    return kept


def filter_by_forced_band(options, band):
    """'## Ship type' bullets whose slug may roll `band`.

    Without this, --set-trait Size="four kilometres end to end || huge hex5"
    against a randomly rolled patrol boat is unsatisfiable: sizes_for('patrol')
    is ('small',) and the Size branch of the loop would have nothing legal to
    draw from.
    """
    if band is None:
        return options
    kept = [x for x in options
            if sp.ship_type_of(x) is not None
            and band in sp.sizes_for(sp.ship_type_of(x))]
    if not kept:
        print("! no '## Ship type' bullet may roll a %s hull, so the forced "
              "Size will be paired with whatever type comes up. Check the "
              "band flags on '## Ship type'." % band, file=sys.stderr)
        return options
    return kept


def bands_with_catapult(tables, ship_type):
    """The bands of `ship_type` whose policy leaves a catapult reachable.

    Asked of the matrix rather than answered from a list of type names,
    because the answer is not a row of EQUIPMENT_POLICY - it is that row
    crossed with LIGHT_CAP and with the catapult bullets' own 'max-' ceilings.
    A battleship's cell is 'light', which at three hexes caps hardware at
    medium and so reaches no catapult at all, and at five hexes caps at large
    and reaches the recessed rail alone. Hardcoding ("carrier", "battleship")
    would be right today and would silently stop being right the first time
    somebody edits a cap.

    Non-empty prose is the test, because the 'none' bullet's prose is
    NO_EQUIPMENT - "has one" and "is truthy" are the same question, which is
    gates_for()'s argument in ship_policy.py.
    """
    bands = []
    for band in sp.sizes_for(ship_type):
        pool = sp.filter_by_ship_policy(
            tables["Launch catapult"], ship_type, band, "Launch catapult")
        if any(split_flags(x)[0] != sp.NO_EQUIPMENT for x in pool):
            bands.append(band)
    return tuple(bands)


def filter_by_forced_catapult(options, tables):
    """'## Ship type' bullets that may carry a launch catapult at all.

    Without this the hard 'none' lock discards the user's own --set-trait in
    silence: nine of the ten types have policy 'none' for that table, so a
    pinned flight deck paired with a randomly rolled freighter comes back as
    the empty bullet and the ship renders with no deck and no complaint.
    """
    kept = [x for x in options
            if sp.ship_type_of(x) is not None
            and bands_with_catapult(tables, sp.ship_type_of(x))]
    if not kept:
        print("! no '## Ship type' bullet may carry a launch catapult, so the "
              "forced Launch catapult will be overruled by the policy lock. "
              "Check EQUIPMENT_POLICY's catapult column.", file=sys.stderr)
        return options
    return kept


# --------------------------------------------------------------------------
# The roll
# --------------------------------------------------------------------------

def ship_fields(ship):
    """The subject fields both prompt templates substitute.

    pronoun_fields() (generate-npc.py:1714) with the pronouns taken out, which
    is the whole of it: a hull is an 'it', so there is one grammatical number,
    one verb form and no variant tables. Five keys where the NPC file has
    nine, and none of them is rolled for.

    Split out of roll_ship() for the reason pronoun_fields() is: --regen-manifest
    rebuilds a ship from its stored traits and has to get the same fields back
    without re-rolling anything, so this reads only keys the manifest carries.
    """
    return {
        "ship": ship["Ship type"],
        "Ship": ship["Ship type"][:1].upper() + ship["Ship type"][1:],
        "name": ship.get("name", ""),
        "size": ship["Size"],
        "is_are": "is",
    }


def roll_ship(tables, rng, overrides=None, probe=None):
    """One ship as a flat dict of trait -> rolled text.

    roll_npc()'s architecture rather than its code, per design §1: an ordered
    draw over REQUIRED_TABLES, a per-table hook that narrows the pool, `probe`
    recording, a forced override replacing the draw at its own table, raw
    bullets collected at the moment of the draw, a flag strip, and a '{}'
    substitution pass. What it does not reuse is roll_npc()'s twenty-five
    in-loop pairings, which are wardrobe and anatomy and have no hull analogue.

    `probe`, when a dict is passed, is filled with the fully-filtered pool this
    function computed for each table. It is a read-out of work already being
    done rather than a second computation: every filter below narrows
    `options` and the draw comes off the end of it, so the list recorded here
    is by construction the set of bullets this table could have produced given
    the traits above it. That is what lets the --trait-choices query promise
    not to drift - there is nothing for it to drift from.

    Recording consumes no randomness and changes no value, so a probed roll
    and an unprobed roll at the same seed are the same ship.

    Theme is the one table with no entry in the loop: like Pronouns in the NPC
    roller it is drawn first, because the pools it gates cannot be drawn
    before the thing that selects between them.
    """
    # Theme first, for the reason above. Not gated on Ship type: a freighter
    # should be as likely to look neosamurai as a destroyer is, so nothing
    # here reads the type.
    theme = (overrides or {}).get("Theme") or rng.choice(tables["Theme"])
    # No filter runs on Theme - it is the thing the others are filtered by -
    # so its pool is the whole table. Recorded anyway, so a caller asking
    # "what could Theme be" gets a list rather than a KeyError.
    if probe is not None:
        probe["Theme"] = list(tables["Theme"])

    # The two reverse gates, computed before the loop because each constrains
    # a table that is rolled EARLIER than the pinned one. See the pair of
    # filters above for what each is worth.
    forced_size = (overrides or {}).get("Size")
    forced_band = sp.size_of(forced_size) if forced_size is not None else None
    forced_catapult = (overrides or {}).get("Launch catapult")
    forced_deck = (forced_catapult is not None
                   and split_flags(forced_catapult)[0] != sp.NO_EQUIPMENT)

    ship = {"Theme": theme}

    # The bullets exactly as the file spells them, flags and all, collected at
    # the moment each is drawn. ship[name] cannot serve: the strip block below
    # takes the flag segment off nearly every table, so a rendered Weapon no
    # longer matches any line in the file and two bullets differing only in
    # flags collapse into one.
    #
    # Two consumers want it. --trait-odds counts raw bullets, because a count
    # has to key on something the tables file actually contains; and a re-roll
    # pins every trait but one back into a fresh roll, which only works if the
    # pinned values still carry the flags the filters read.
    #
    # '_'-prefixed so the manifest writer's `not k.startswith("_")` filter
    # keeps it out of the traits dict.
    raw = {"Theme": theme}

    ship_type = None            # the SHIP_TYPES slug, known from '## Ship type'
    band = None                 # the SIZE_BANDS band, known from '## Size'
    mil = False                 # the type bullet's own civ/mil register
    scene = ""                  # the Backdrop's middle segment
    scene_flags = ()            # and its flag segment, for the placement gates

    for name in REQUIRED_TABLES:
        if name == "Theme":
            continue

        # Per-BAND variants where the NPC file has per-pronoun ones:
        # '## Hull (huge)' replaces, '## Command bridge (small) +' adds.
        # variant_table() takes a caller-supplied key and does not care what
        # it means, so this needs no change on that side - only a different
        # string. Empty until '## Size' is rolled, which is right: the three
        # tables drawn before it are the two halves of the name and the type,
        # and none of them can sensibly vary by a band nothing has picked yet.
        options = variant_table(tables, name, band or "")

        # ---- the hard gates, which run FIRST ----
        #
        # Policy before theme, and the ordering is load-bearing.
        # filter_by_ship_policy() is hard and can return a one-element pool;
        # filter_by_theme() is soft and ends `kept or options`. Running theme
        # first hands policy a pre-narrowed pool and raises the odds of
        # starving a hard filter; running policy first means the theme
        # filter's own fallback can only ever re-widen to a policy-legal set.
        if name == "Ship type":
            options = filter_by_forced_band(options, forced_band)
            if forced_deck:
                options = filter_by_forced_catapult(options, tables)

        elif name == "Size":
            # The TYPE gates the SIZE. sizes_for() is the whitelist and it is
            # a hard filter: falling back would hand over exactly what it kept
            # away, which is filter_by_size()'s own argument one table over.
            #
            # Design §3(a) draws a band uniformly first and then filters the
            # bullets to it, which makes each band equiprobable whatever the
            # table's bullet counts are. This filters in one step instead, for
            # two reasons: it keeps `probe[name]` equal to the pool the draw
            # actually comes off - the invariant --trait-choices depends on,
            # and which a band drawn behind the probe's back would break by
            # reporting a perfectly legal medium Size on a cruiser as
            # disallowed - and it consumes one draw per table like every other
            # branch. The live '## Size' table carries four bullets in each of
            # the four bands, so the two are the same distribution today; the
            # honest guard against that drifting is a test on the counts, not
            # a second draw.
            legal = [x for x in options if sp.size_of(x) in sp.sizes_for(ship_type)]
            if not legal:
                raise SystemExit(
                    "no '## Size' bullet carries a band %s may roll (%s). Add "
                    "one, or check the band flags on '## Size'."
                    % (ship_type, ", ".join(sp.sizes_for(ship_type))))
            options = legal

            # The second half of reverse gate (b2). Narrowing '## Ship type'
            # to the two types that may carry a catapult is not enough on its
            # own: a battleship's cell is 'light', which caps hardware one
            # band below the hull, so at three hexes it reaches no catapult
            # at all and only the five-hex hull reaches the recessed rail.
            # Without this the gate hands back a large battleship half the
            # time and the pinned flight deck is a deck the matrix says that
            # hull cannot have. A preference, like the type half.
            if forced_deck:
                decked = [x for x in options
                          if sp.size_of(x) in bands_with_catapult(tables, ship_type)]
                if decked:
                    options = decked
                else:
                    print("! no band a %s may roll leaves a launch catapult "
                          "reachable, so the forced Launch catapult will be "
                          "overruled by the policy lock." % ship_type,
                          file=sys.stderr)

        elif name == "Hull":
            # The silhouette has to belong to this hull twice over - to the
            # type and to the band - because a '## Hull' bullet is the one
            # place the ship's shape is actually described. Nothing else keeps
            # a one-hex courier off a fleet carrier's slab, and a soft
            # fallback here would produce precisely that.
            #
            # Hard with no fallback, and an empty pool is a SystemExit rather
            # than an IndexError out of rng.choice(): the fix is a bullet in
            # the tables file and the message is where to say so.
            fits = [x for x in options
                    if ship_type in split_flags(x)[1] and band in split_flags(x)[1]]
            if not fits:
                raise SystemExit(
                    "no '## Hull' bullet is flagged for a %s at %s. Every legal "
                    "(type, size) pair needs at least one - two untagged, if "
                    "the pair is to be reachable under every theme."
                    % (ship_type, band))
            options = fits

        elif name in sp.EQUIPMENT_TABLES:
            options = sp.filter_by_ship_policy(options, ship_type, band, name)

        elif name == "Backdrop":
            # The scene table carries 'max-' ceilings of its own: an enclosed
            # commercial berth is a room, and a five-hex hull does not fit
            # inside it. Not sp.filter_by_size() itself - see the seam above
            # for why a three-segment table cannot be handed to it.
            options = filter_backdrop_by_size(options, band)

        elif name == "Glow colour":
            # A scene that commits to a colour of light - "lit crimson", "a
            # cooling wreck still glowing dull red" - is what the shade has to
            # agree with, or the frame is asked for two contradictory light
            # sources at once. Fed from the scene alone, which is the
            # measurement filter_by_hue()'s own docstring records.
            options = filter_by_hue(options, light_hues(scene))

        elif name == "Glow placement":
            # Two gates, and they answer different questions. The prop gate
            # asks whether the SCENE has the thing the placement lights - a
            # debris field, a planet below, a hull moored alongside. The
            # equipment gate asks whether the SHIP does: a lit flight deck on
            # a grain freighter routes around the catapult lock in the one
            # direction the lock cannot see.
            options = filter_by_placement_prop(options, scene_flags)
            options = sp.filter_by_gates(options, ship)

        # ---- the soft gates ----
        #
        # Theme first and register second, matching roll_npc():1905-1914. The
        # order costs the realized theme share whatever the two filters
        # correlate by, which apply_theme_share()'s docstring measures and
        # deliberately leaves as it is.
        if name in THEMED_TABLES:
            options = filter_by_theme(options, theme, name)
            options = apply_theme_share(options, theme, name)

        if name in MIL_TABLES:
            # Keyed on the '## Ship type' bullet's own civ/mil flag rather
            # than on the slug, because the register and the type are
            # genuinely different questions: a survey ship is 'civ' and a
            # reconnaissance ship of the same slug is 'mil'.
            options = filter_by_mil(options, mil, name)

        # After the last filter and before the draw: this is the only line in
        # the function where `options` is exactly what the roller is about to
        # choose from, which is what makes it the honest answer to "what could
        # this table have produced for this ship".
        if probe is not None:
            probe[name] = list(options)
        value = rng.choice(options)

        # A forced value replaces the draw here, at the moment its own table
        # is rolled, rather than at the ship.update(overrides) further down -
        # so every filter that reads an earlier trait reads the bullet this
        # ship actually keeps rather than the one the roll discarded. A pinned
        # Ship type that arrived late would be invisible to the whole
        # equipment matrix, which is the entire mechanism.
        forced = (overrides or {}).get(name)
        if forced is not None:
            value = forced

        # Recorded after the forced value has replaced the draw, so _raw
        # describes the ship rather than the bullet it discarded, and before
        # anything below reads a flag off it.
        raw[name] = value

        # The flags the later tables read, taken here because this is the last
        # place they are guaranteed to exist - a forced bullet skips every
        # filter above and would otherwise arrive at the strip block with
        # nobody having looked at it.
        if name == "Ship type":
            ship_type = sp.ship_type_of(value)
            if ship_type is None:
                raise SystemExit(
                    "'## Ship type' bullet %r carries no SHIP_TYPES slug, so "
                    "there is no EQUIPMENT_POLICY row to roll its hardware "
                    "from. Add one of: %s"
                    % (value, ", ".join(sp.SHIP_TYPE_ORDER)))
            mil = "mil" in split_flags(value)[1]
        elif name == "Size":
            # Read off the value rather than off a band chosen earlier,
            # because a --set-trait Size can have replaced the draw one line
            # up and every hardware filter below keys on this.
            band = sp.size_of(value)
        elif name == "Backdrop":
            _, scene, scene_flags = split_backdrop(value)

        # Whatever is left of a bullet is rendered straight into a prompt and
        # a dossier, so the flag segment comes off - except on the two
        # three-segment tables, whose second segment is prose the prompt
        # builder splits for itself. Doing it here rather than in a block at
        # the end is what lets sp.armament_sentence() and sp.filter_by_gates()
        # be handed `ship` directly: both test a bullet for emptiness, and the
        # 'none' bullet is only empty once its flags are gone.
        ship[name] = value if name in ("Backdrop", "Faction") else split_flags(value)[0]

    ship.update(overrides or {})

    # The loop pastes each forced trait over its own draw already, so this
    # picks up only the overrides that are not tables at all - and filters
    # them out, because REQUIRED_TABLES is the authority on which is which.
    # 'name' is the one that arrives that way, from --name.
    raw.update({k: v for k, v in (overrides or {}).items() if k in REQUIRED_TABLES})
    ship["_raw"] = raw

    # A late override skipped the loop's strip, so re-run it on the tables
    # that can carry flags. Same fix, same reason, as generate-npc.py:2420-2440.
    for name in REQUIRED_TABLES:
        if name not in ("Backdrop", "Faction"):
            ship[name] = split_flags(ship[name])[0]

    if "name" not in ship:
        # '## Name prefixes' carries one weighted empty bullet written
        # '|| none', because 'x60 ' with nothing after it does not parse as a
        # weight - the bullet regex's trailing \s*$ eats the space the weight
        # regex needs, and the entry ships as one option whose literal text is
        # 'x60'. The strip above has already turned it into ''. strip() here
        # is what turns "  Vespertine" back into "Vespertine".
        ship["name"] = ("%s %s" % (ship["Name prefixes"], ship["Ship names"])).strip()

    # A bullet may carry a placeholder of its own so that it agrees with the
    # rolled hull rather than hardcoding a phrasing. No pronouns exist here,
    # so the key set is ship_fields()'s five and nothing else, and a stray
    # '{object}' copied over from the NPC file is a hard failure naming the
    # table and the option rather than a literal brace shipped to the model.
    fields = ship_fields(ship)
    for key, value in ship.items():
        if isinstance(value, str) and "{" in value:
            try:
                ship[key] = value.format(**fields)
            except (KeyError, IndexError, ValueError) as exc:
                raise SystemExit(
                    "table %r, option %r: %s is not a ship placeholder. "
                    "Available: %s" % (key, value, exc, ", ".join(fields)))
    return ship


# --------------------------------------------------------------------------
# Prompts
#
# Style register is the painterly one the mech catalogue uses, not the
# cel-shaded equipment register, and the slot order follows the fixed order of
# all 65 mech blocks: silhouette, framing, style clause, distinguishing
# feature, mounted systems, glow, plan, background, closing tag block.
# --------------------------------------------------------------------------

# Portrait: one size for every hull. Deliberately landscape where the NPC's is
# square (generate-npc.py:1109) - a ship in a scene is a landscape
# composition, and every '## Backdrop' bullet in the file is written as one.
PORTRAIT_SIZE = (1216, 832)          # 3:2, 1.01 MP, both dims a multiple of 64

# What the token prompt says about the hull's proportions, per band. It states
# FRAMING; scale is {size}'s job - the rolled '## Size' bullet, which names a
# number in metres. Keeping the two apart is why no '## Size' bullet is
# allowed to say "huge": a phrase that describes a look instead of stating a
# figure is the part the model was measured ignoring.
PLAN_FRAMING = {
    "small": "the whole hull roughly as long as it is wide across the wings",
    "medium": "a lean hull about twice as long as it is wide",
    "large": "a long hull about half again as long as it is broad",
    "huge": "a vast hull filling the frame bow to stern, half again as long "
            "as it is broad",
}

PORTRAIT_TEMPLATE = (
    "{shot} of {ship}, {size}, rendered in a detailed painterly illustration "
    "style with fine grain texture, clean linework and halftone dot shading "
    "worked into the shadows, moody cinematic lighting. The hull is {hull}, "
    "{detail}. {armament_line}{bridge_line}{faction_line}{markings}, "
    "{condition}. "
    "{backdrop} {weather_line}{glow_line} "
    "Shallow depth of field, high detail, atmospheric sci-fi vessel "
    "illustration, painterly brushwork with heavy grain and dense halftone "
    "screentone worked into every shadow."
)

# The token asserts FRAMING three times, in the three places that move it, for
# the reason generate-npc.py:1148-1155 gives about the NPC token's feet: at
# CFG 1.0 "the whole hull in frame" alone loses to the detail the rest of the
# prompt asks for, and the stern is the first thing cropped. Once in the
# opening sentence (whole hull, margin on all four sides), once as {plan} (the
# aspect the latent is already shaped to), and once opening the closing tag
# block, which is the position a diffusion model weights hardest.
#
# The background sentence is positive-only, deliberately. The NPC token's "no
# texture, no gradient, no shadow, no environment" was removed because every
# flattening word in it has a direct contradiction in the same prompt's
# grain/halftone tail, and scoping is what a diffusion text encoder is worst
# at (generate-npc.py:1156-1169). It exists for the RMBG pass, not for style.
TOKEN_TEMPLATE = (
    "A top-down orthographic illustration of {ship}, {size}, seen from "
    "directly above with the bow toward the top of the frame, the whole hull "
    "in frame from bow to stern and wingtip to wingtip with clear empty space "
    "on all four sides, rendered in a detailed painterly illustration style "
    "with fine grain texture, clean linework and halftone dot shading worked "
    "into the shadows, moody cinematic lighting on the hull. "
    "The hull is {hull}, {detail}. {armament_line}{bridge_line}"
    "{faction_line}{markings}, {condition}. "
    "{glow_line} Around the hull the background is an empty plain white void. "
    "{plan}, a single vessel centered in frame and clear of the frame edge, "
    "dramatic lighting, high detail, isolated vehicle illustration, clean "
    "silhouette, painterly brushwork with heavy grain and dense halftone "
    "screentone worked into every shadow."
)

# The forms the closing palette line takes. Two dimensions, the same two the
# NPC file's four constants have: whether anything rolled for this ship could
# cast a glow, and whether the roll asserts pigment of its own. Pigment and
# light are different things and coexist happily - a Karrakin hull in crimson
# and gold lit by a blue drive glow reads correctly - but the line's claim
# that the glow is the ONLY saturated colour stops being true when the paint
# has one, so {other} softens it. Four constants and one slot rather than
# eight constants.
#
# GLOW_NONE and GLOW_NONE_PIGMENT are the NPC file's wording (:1225-1233)
# character for character, since neither mentions a subject - but COPIED
# rather than aliased off npc.*. The borrowed surface is a closed list that
# test_shared_surface.py pins, and a ship prompt should not silently reword
# itself the day somebody retunes the NPC palette line.
GLOW_PORTRAIT = (
    "A faint {glow} glow {placement}. Keep the palette restrained - greys, "
    "olive drab and rust - with {glow} the only {other}saturated color in the "
    "frame."
)
GLOW_TOKEN = (
    "Keep the palette restrained - greys, olive drab and rust - with a single "
    "{glow} glow the only {other}saturated color."
)
GLOW_NONE = (
    "Keep the palette restrained - greys, olive drab and rust, with no stray "
    "saturated color."
)
GLOW_NONE_PIGMENT = (
    "Keep the rest of the palette restrained - greys, olive drab and rust."
)


def weather_sentence(ship):
    """The weather sentence this ship's portrait gets, or '' for none.

    generate-npc.py:2701-2715, unchanged but for the name of the thing in the
    frame. Weather is portrait-only: the token renders on flat white so it can
    be cut out, and drifting snow would only give RMBG more to cut. It reaches
    only the '## Backdrop' entries flagged 'weather', since nothing drifts
    through hard vacuum, and a '## Weather' bullet flagged 'clear' opts out in
    turn - that flag is the dial for how often a scene that COULD have weather
    comes up with nothing in it.

    The one change is where the 'clear' flag is read from. The NPC roller
    never strips '## Weather', so its version splits npc["Weather"] here; this
    one strips every two-segment table so the dossier and the manifest carry
    prose rather than flags, and reads the flag off the raw bullet instead.
    Splitting the stripped value would find no '||', return an empty flag
    tuple, and print "hard vacuum, nothing at all between the hull and the
    stars" into a portrait of a hull on a rain-swept hardstand - which is
    exactly what it did before this line said _raw.
    """
    if "weather" not in split_backdrop(ship["Backdrop"])[2]:
        return ""
    text, flags = split_flags(ship["_raw"]["Weather"])
    return "" if "clear" in flags else text


def faction_line(ship):
    """The Faction's visual signature with its trailing comma-space, or ''.

    Pre-formatted rather than a bare slot for the reason the NPC file's is
    (:2671-2699): str.format is single-pass and a clause that has to be able
    to vanish cannot be a bare slot, or the two non-affiliations leave a
    doubled comma in the middle of the sentence.

    A 'dressy' Faction keeps its NAME - the dossier and the GUI still print
    the affiliation - and loses only the visual, when the hull's own register
    is civilian. Heraldic quartering and a house banner on a chartered bulk
    hauler is what that costs; barring the faction outright would throw away
    the good flavour to fix the bad render. The NPC version keys this on
    dress_policy_for(role_category(npc)); ships have no dress policy, so the
    'civ' register off '## Ship type' is the analogue - a working hull.
    Nothing in the live '## Faction' table carries 'dressy' yet; the flag is
    in the file's declared vocabulary and this is its reader.
    """
    _, visual, flags = split_faction(ship["Faction"])
    if "dressy" in flags and "mil" not in split_flags(ship["_raw"]["Ship type"])[1]:
        visual = ""
    return "%s, " % visual if visual else ""


def build_ship_prompts(ship):
    """The portrait and token prompt text for one rolled ship."""
    _, scene, _ = split_backdrop(ship["Backdrop"])
    band = sp.size_of(ship["_raw"]["Size"])

    fields = ship_fields(ship)
    fields.update({
        "hull": ship["Hull"],
        "detail": ship["Detail"],
        "markings": ship["Markings"],
        "condition": ship["Condition"],
        "glow": ship["Glow colour"],
        "placement": ship["Glow placement"],
        "backdrop": scene,
        "shot": split_backdrop(ship["Backdrop"])[0],
        "plan": PLAN_FRAMING[band],
    })

    weather = weather_sentence(ship)
    fields["weather_line"] = weather + " " if weather else ""
    fields["faction_line"] = faction_line(ship)

    # Both already written and tested in ship_policy.py, and both return ''
    # rather than an empty clause - which is the whole of how an unarmed cargo
    # ship's prompt omits the armament sentence instead of printing "The hull
    # carries .". They are separate sentences because a bridge is not carried:
    # it is silhouette, and the renderer treats a tiered bridge tower as hull
    # shape rather than as fitted equipment.
    fields["armament_line"] = sp.armament_sentence(ship)
    fields["bridge_line"] = sp.bridge_sentence(ship)

    # A Faction flagged 'palette' asserts pigment of its own, and so does a
    # '## Hull' bullet flagged the same way - eleven of them describe a coat
    # that is already a saturated colour, and without this the closing line
    # tells the model the glow is the only saturated thing in a frame it has
    # just painted imperial green. Read off _raw because the strip block took
    # both flag segments off; ships have carried rawTraits since their first
    # manifest entry, so this is available on the regen path too.
    pigment = ("palette" in split_faction(ship["Faction"])[2]
               or "palette" in split_flags(ship["_raw"]["Hull"])[1])
    fields["other"] = "other " if pigment else ""
    none_line = GLOW_NONE_PIGMENT if pigment else GLOW_NONE

    # The glow colour only belongs in a prompt when something rolled for this
    # ship would actually cast it. Fitted sources apply to both shots; the
    # scene's own light - a welding arc, a burning wreck, a nebula lit from
    # within - reaches only the portrait, since the token has no backdrop at
    # all, just flat white.
    equipped_glow = has_light_source(
        ship["Weapon"], ship["Shield generator"], ship["Launch catapult"],
        ship["Command bridge"], ship["Detail"], ship["Hull"])
    portrait_glow = equipped_glow or has_light_source(scene)

    portrait_fields = dict(
        fields,
        glow_line=(GLOW_PORTRAIT if portrait_glow else none_line).format(**fields))
    token_fields = dict(
        fields,
        glow_line=(GLOW_TOKEN if equipped_glow else none_line).format(**fields))

    prompts = (PORTRAIT_TEMPLATE.format(**portrait_fields),
               TOKEN_TEMPLATE.format(**token_fields))

    for label, text in zip(("portrait", "token"), prompts):
        n = estimate_tokens(text)
        if n > TOKEN_LIMIT:
            print("! %s prompt is about %d tokens, over Krea 2's %d-token limit "
                  "- the tail will be truncated. Shorten the longest bullet it "
                  "rolled; '## Hull' is charged in both images and is where the "
                  "trim is cheapest." % (label, n, TOKEN_LIMIT), file=sys.stderr)

    return prompts
