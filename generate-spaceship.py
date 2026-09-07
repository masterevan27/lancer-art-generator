#!/usr/bin/env python3
"""Roll random spaceships and generate their Foundry portrait + token art.

Companion to generate-npc.py, which does the same thing for people. That file
is 4,544 lines covered by ~50 test files and is not touched by any of this:
the shared machinery - the markdown table parser, the theme filters, the glow
subsystem, the ComfyUI Knobs/Entry adapters and the output-path helpers - is
borrowed off it by loading it by path, the way generate-3d.py already loads it
for DEFAULT_MANIFEST. What a hull is ALLOWED to carry lives in ship_policy.py,
which imports normally because its name has no hyphen in it.

A ship lands in its own folder, nested under a category folder for its rolled
Ship type (see SHIP_FOLDERS), under a fresh numbered run folder in the output
root - by default ComfyUI's own output tree, exactly as the NPC script does,
so a batch can be looked over before any of it is decided worth keeping:

    <root>/run1/Cruisers/ISV Vespertine/ISV Vespertine Portrait.png   1216x832
    <root>/run1/Cruisers/ISV Vespertine/ISV Vespertine Token.png      transparent
    <root>/run1/Cruisers/ISV Vespertine/ISV Vespertine.md             the dossier

The two-level <Category>/<Name> nesting is load-bearing rather than tidy: the
import GUI recovers a ship's Foundry folder as basename(dirname(folder)), so a
flat run1/<Name> would file every ship under a category called "run1".

Unlike an NPC, a ship's TOKEN is not one size. Foundry draws it across the
number of grid hexes its rolled Size band claims - one for a patrol boat, five
for a fleet carrier - so the token's canvas, its aspect and the framing
language in its prompt all vary per ship, and the manifest carries the grid
width and height as integers for the importer to set token.width/height from.
See TOKEN_GRID and token_size().

Stdlib only, same as generate-art.py. Run with --dry-run first.

Examples:
  python generate-spaceship.py --dry-run
  python generate-spaceship.py                          # one ship
  python generate-spaceship.py --count 5 --seed 1234    # reproducible batch
  python generate-spaceship.py --ship-type carrier --size huge
  python generate-spaceship.py --theme salvage --name "ISV Vespertine"
  python generate-spaceship.py --ship-catalogue         # types and legal sizes

  # Re-render one already-rolled ship exactly, or with a fresh seed - the
  # traits (and so the prompt) come from the manifest either way, not a roll:
  python generate-spaceship.py --regen-manifest .generated-npcs.json \\
      --regen-id ship-isv-vespertine-1234
  python generate-spaceship.py --regen-manifest .generated-npcs.json \\
      --regen-id ship-isv-vespertine-1234 --reroll-trait Hull

  # Ask which values one trait could take on that ship (JSON on stdout, no
  # render), then pin the one you want and re-render with everything else kept:
  python generate-spaceship.py --regen-manifest .generated-npcs.json \\
      --regen-id ship-isv-vespertine-1234 --trait-choices Weapon
  python generate-spaceship.py --regen-manifest .generated-npcs.json \\
      --regen-id ship-isv-vespertine-1234 \\
      --set-trait Weapon="a spinal lance ... || mil min-huge" --release Size
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import random
import string
import sys
import time
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

# Bound only by the render/output half below. asset_folder is npc_folder under
# a name that does not say NPC; the rest are used verbatim. The design's list
# is nineteen names; these six take this file's total to twenty-five, and
# test/test_shared_surface.py pins all of them.
Knobs = npc.Knobs
entry_for = npc.entry_for
fetch = npc.fetch
_safe = npc._safe
next_run_folder = npc.next_run_folder
asset_folder = npc.npc_folder              # <root>/<category>/<Name>/, suffixed


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

def sentence_case(text):
    """`text` with its first character upper-cased and nothing else touched.

    Not str.capitalize(), which lower-cases the remainder: 'a Karrakin hull'
    would come back 'A karrakin hull' with the house name flattened, and the
    live tables carry Karrakin, Chartered, Unaligned, Free and Trader. This is
    the same slice-upper that ship_fields() already builds its 'Ship' key with.

    The clauses this is applied to are bullets, and a bullet is authored to sit
    mid-sentence; the templates then join several of them with a full stop.
    Nothing capitalized them, so every prompt carried about two lowercase
    sentence-starts. The NPC templates never hit this, because every clause of
    theirs opens with a {Subject} that pronoun_fields() capitalizes
    (generate-npc.py:1727) - a hull has no pronoun, so the capital has to be
    put on here.
    """
    return text[:1].upper() + text[1:]


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

    The TEXT still has to come from ship["Weather"], not from this same
    split - _raw is read for the flag alone. roll_ship()'s '{}' pass runs
    after _raw is recorded, so a bullet carrying a ship placeholder (none do
    in the live tables today, which is why this went unnoticed) would ship
    its brace text straight into the prompt if the raw bullet's own text were
    returned here instead of the substituted trait.
    """
    if "weather" not in split_backdrop(ship["Backdrop"])[2]:
        return ""
    flags = split_flags(ship["_raw"]["Weather"])[1]
    return "" if "clear" in flags else ship["Weather"]


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

    # In both templates {faction_line} sits directly after {detail}'s full
    # stop, or after armament_line's or bridge_line's if either is present -
    # never after a comma - so whenever it is non-empty it always opens a new
    # sentence. sentence_case("") is a no-op, so the empty case (no faction
    # visual) is unaffected.
    fields["faction_line"] = sentence_case(faction_line(ship))

    # Both already written and tested in ship_policy.py, and both return ''
    # rather than an empty clause - which is the whole of how an unarmed cargo
    # ship's prompt omits the armament sentence instead of printing "The hull
    # carries .". They are separate sentences because a bridge is not carried:
    # it is silhouette, and the renderer treats a tiered bridge tower as hull
    # shape rather than as fitted equipment.
    fields["armament_line"] = sp.armament_sentence(ship)

    # bridge_sentence() returns "<bullet>. " and the bullet is authored lower
    # case to sit mid-sentence. It always follows either the armament
    # sentence's full stop or {detail}'s, so it always starts a sentence.
    fields["bridge_line"] = sentence_case(sp.bridge_sentence(ship))

    # Markings follows bridge_line's full stop - unless a faction visual sits
    # between them, which ends in ", " and leaves Markings mid-sentence. The
    # two unaffiliated Faction bullets have empty visuals, so faction_line
    # cannot be relied on either way and the branch is real.
    fields["markings"] = (ship["Markings"] if fields["faction_line"]
                          else sentence_case(ship["Markings"]))

    # {plan} opens the token's closing tag block, straight after "...an empty
    # plain white void. ". Half of every occurrence of this defect was here,
    # and the first write-up of the bug missed it.
    fields["plan"] = sentence_case(PLAN_FRAMING[band])

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

# ---------------------------------------------------------------------------
# Token sizing
# ---------------------------------------------------------------------------

# Token: the Foundry grid footprint, and the canvas that matches its aspect.
#
# The WIDTH column is never typed here - it is read out of
# ship_policy.SIZE_BANDS below, so the number Foundry sets token.width from and
# the number this file shapes a latent to cannot drift apart. Only the HEIGHT
# is a decision of this file's, because a hex count says nothing about how deep
# a hull is: a five-hex carrier is long, not square, and a 5x5 token would give
# it four hexes of empty margin fore and aft on the map.
TOKEN_GRID_HEIGHT = {"small": 1, "medium": 1, "large": 2, "huge": 3}
TOKEN_GRID = {band: (sp.hexes_for(band), TOKEN_GRID_HEIGHT[band])
              for band in sp.SIZE_ORDER}

# Pixels per hex, DECLINING as the hull grows. A bigger token is displayed
# bigger on the map, but the VRAM budget is finite and a naive 512px x 5 hexes
# = 2560 would have cost 5x the NPC token to render. These four numbers are
# all multiples of 64, which is what makes every canvas below one too.
TOKEN_PX_PER_HEX = {"small": 1024, "medium": 768, "large": 576, "huge": 384}

#   band    grid    canvas       MP     vs the NPC token (1024x1280)
#   small   1 x 1   1024 x 1024  1.05   0.80x
#   medium  2 x 1   1536 x  768  1.18   0.90x
#   large   3 x 2   1728 x 1152  1.99   1.52x
#   huge    5 x 3   1920 x 1152  2.21   1.69x
MAX_TOKEN_PX = 2_400_000             # --max-token-px default


def token_size(band, max_px=MAX_TOKEN_PX):
    """(width, height) for a token of this hull band, snapped to 64 and clamped.

    Canvas aspect equals grid aspect exactly in every band, so Foundry
    stretching the image into the token rectangle introduces no distortion -
    which is the whole reason the height is a grid count rather than a taste
    call about composition.

    The clamp preserves aspect and re-snaps both dimensions to 64 rather than
    truncating one: the latent needs the multiple, and an off-aspect token is
    the failure the aspect match exists to prevent. Floored at 64 because a
    dimension of 0 is not a smaller image, it is a ComfyUI validation error.

    Scaling both raw dimensions by the same factor and THEN independently
    flooring each to its own nearest 64 does not actually keep that promise:
    two independent roundings to a 64px grid can drift the ratio by several
    percent, and for the 3:2 'large' band it did - 1728x1152 clamped to a
    million pixels came back 1216x768, aspect 1.583 against a target of 1.5.
    The fix treats (gw, gh) as the unit instead of trying to hit it after the
    fact: since TOKEN_GRID's width and height are small integers, w=64*gw*m
    and h=64*gh*m are BOTH exact multiples of 64 for every integer m, and
    their ratio is gw/gh exactly, whatever m is. So the clamp finds the
    largest m whose (64*gw*m, 64*gh*m) canvas still fits the budget, floored
    at 1 - which is comfortably at or above the 64px floor for every band,
    since gw and gh are never less than 1.
    """
    gw, gh = TOKEN_GRID[band]
    px = TOKEN_PX_PER_HEX[band]
    w, h = gw * px, gh * px
    if w * h > max_px:
        unit = 64 * 64 * gw * gh
        m = max(1, int((max_px / unit) ** 0.5))
        w, h = 64 * gw * m, 64 * gh * m
    return w, h


def token_metadata(band, max_px=MAX_TOKEN_PX):
    """The five size fields a manifest entry carries, as ints.

    Written from one place because the render path, the regen path and the
    --dry-run --json report all need the same five numbers and the importer
    trusts them: gridWidth/gridHeight go straight onto a Foundry token, and a
    disagreement between what was rendered and what was recorded shows up as a
    token stretched across the wrong number of hexes rather than as an error.
    """
    grid_w, grid_h = TOKEN_GRID[band]
    width, height = token_size(band, max_px)
    return {
        "sizeBand": band,
        "hexes": sp.hexes_for(band),
        "gridWidth": grid_w,
        "gridHeight": grid_h,
        "tokenWidth": width,
        "tokenHeight": height,
    }


# ---------------------------------------------------------------------------
# Paths, names and the manifest
# ---------------------------------------------------------------------------

DEFAULT_TABLES = SCRIPT_DIR / "prompts" / "spaceship-generator-tables.md"

# Ships share the NPCs' manifest on purpose. The import GUI groups manifest
# items by item["kind"] generically and its CATEGORY_LABELS already carries
# 'spaceship': 'Spaceships', so a kind:"spaceship" entry in this one file
# appears in the grid with no server change at all. A second manifest would
# need a new config key, a merge in its loader, and matching changes to its
# sort and delete paths - three edits to a GUI this generator is supposed to
# reach without any.
#
# Keys are absolute folder paths and the two trees are disjoint
# (.../LancerNPCs/... against .../LancerSpaceships/...), so a collision is not
# reachable. --manifest remains available for anyone who wants them separated;
# note that art.load_manifest/save_manifest rewrite the whole file, so a ship
# batch running concurrently with an NPC batch clobbers it. generate-npc.py
# already has that race with itself and the GUI serialises jobs.
DEFAULT_MANIFEST = SCRIPT_DIR / ".generated-npcs.json"

COMFY_PREFIX = "LancerSpaceships"
_OUTPUT_ROOT = os.environ.get("COMFYUI_OUTPUT_DIR")
DEFAULT_OUTPUT_ROOT = (Path(_OUTPUT_ROOT) if _OUTPUT_ROOT else SCRIPT_DIR / "output") / COMFY_PREFIX

# The folder a ship's type files it under, pluralised for parity with the NPC
# script's Pilots/Soldiers. Lives here rather than in ship_policy.py, which is
# a settled module with 683 lines of passing tests and no business knowing
# about directories. A test pins set(SHIP_FOLDERS) == set(sp.SHIP_TYPES), so a
# type added there without a folder here fails at test time rather than filing
# a carrier under "Other".
SHIP_FOLDERS = {
    "carrier": "Carriers",
    "battleship": "Battleships",
    "cruiser": "Cruisers",
    "destroyer": "Destroyers",
    "patrol": "Patrol boats",
    "stealth": "Stealth ships",
    "recon": "Reconnaissance ships",
    "smuggler": "Smuggler ships",
    "cargo": "Cargo ships",
    "support": "Support ships",
}
UNCATEGORIZED_SHIP = "Other"        # mirrors UNCATEGORIZED_ROLE, generate-npc.py:758

# A hull code is a serial, and a table of serials is the wrong shape - it would
# be a hundred bullets that differ by nothing an author can make a judgement
# about. Rolled in code instead, from a stream of its own so that adding or
# removing a letter here cannot shift the ship's own roll.
HULL_CODE_LETTERS = string.ascii_uppercase


def hull_code(rng):
    """A stencilled hull registry code - 'IST-4471'.

    Populates the manifest's `callsign`, which the GUI grid prints as an
    item's subtitle. The shape is three letters and four digits because that
    is what the '## Markings' bullets describe being stencilled on a hull, and
    the dossier quotes it the way an NPC's callsign is quoted.
    """
    letters = "".join(rng.choice(HULL_CODE_LETTERS) for _ in range(3))
    return "%s-%04d" % (letters, rng.randint(1, 9999))


def ship_id(name, seed):
    """The manifest id for a ship, deterministic from its name and seed.

    Deterministic so an --overwrite rerun of the same ship reuses it rather
    than minting a new one - this is what the Foundry importer keys its
    "already imported" tracking on. The 'ship-' prefix is what guarantees no
    collision with an 'npc-' id in the shared manifest.

    Lower-cased, and generate-npc.py's ids are not. art._slug() preserves case
    ("npc-Nadia-Okonkwo-1234"), which is fine for a value only ever compared
    against itself - but the id also travels through a GUI URL and a Foundry
    folder key, and two of those are places a stray case fold turns "already
    imported" into "import it again". Folding it once, here, is cheaper than
    trusting every consumer not to. The design doc's own example id is
    lower-case for the same reason; the sentence beside it naming art._slug is
    what disagrees, and this is the half of that pair worth keeping.
    """
    return "ship-%s-%d" % (art._slug(name).lower(), seed)


def ship_type_of(ship):
    """The sp.SHIP_TYPES slug this ship's rolled '## Ship type' bullet carries.

    Read off the RAW bullet, never off the rendered trait. The rendered text is
    one of about two phrasings per slug with its flags already stripped, so
    keying on it would be ROLE_CATEGORIES' exact-text keying applied to a table
    that deliberately does not have one sentence per type - ship_policy.py:200
    -207 explains at length why the slug is a flag instead.
    """
    return sp.ship_type_of(ship["_raw"]["Ship type"])


def band_of(ship):
    """The sp.SIZE_BANDS band this ship's rolled '## Size' bullet carries.

    Off the raw bullet for the same reason as above: the Size table's prose
    names the number ("about forty metres bow to stern, a two-crew hull") and
    the band is a flag on it, so the rendered trait has no band left in it.
    """
    return sp.size_of(ship["_raw"]["Size"])


def type_name_of(ship):
    """'Cruiser' for a display line, without needing the raw bullet to be there.

    ship_type_of() is the strict reading and every filter uses it; this is the
    lenient one, for the two banner lines and the dossier header. A regen from
    a hand-edited entry that lost its rawTraits still has a name, a seed and a
    folder, and refusing to print a heading over it would be the one thing in
    this file that turned a degraded entry into a traceback.
    """
    raw = ship.get("_raw", {}).get("Ship type")
    slug = sp.ship_type_of(raw) if raw else None
    return sp.SHIP_TYPES[slug]["name"] if slug in sp.SHIP_TYPES else "ship"


def ship_category(ship):
    """The folder this ship's type sorts into, warning once for an unmapped one."""
    slug = ship_type_of(ship)
    category = SHIP_FOLDERS.get(slug)
    if category is None:
        print("! ship type %r has no entry in SHIP_FOLDERS - filing under %r"
              % (slug, UNCATEGORIZED_SHIP), file=sys.stderr)
        category = UNCATEGORIZED_SHIP
    return category


def write_ship_dossier(path, ship, seed, prompts, images, callsign, band, max_px=MAX_TOKEN_PX):
    """The <Name>.md that travels with the art, mirroring write_dossier().

    Nothing in the import GUI reads it - it is recorded in `files`/`dossier`
    and copied into Foundry beside the images - so this is for the person who
    opens the folder in six months and wants to know what the ship was. Which
    is why the grid footprint is spelled out in hexes here even though the
    manifest already carries it as integers: a human reading "3 x 2 hexes"
    learns something the entry's gridWidth/gridHeight only tell a program.
    """
    portrait_prompt, token_prompt = prompts
    grid_w, grid_h = TOKEN_GRID[band]
    # Off the rendered traits rather than off _raw, so a regen from an entry
    # that lost its raw bullets still writes a dossier. Both tables keep their
    # segments in the stored trait - roll_ship() strips the flag segment off
    # every OTHER table but leaves Backdrop and Faction whole, exactly as
    # roll_npc() does, because both are read segment-wise at prompt-build time.
    shot, scene, backdrop_flags = split_backdrop(ship["Backdrop"])
    operator, livery, _faction_flags = split_faction(ship["Faction"])
    traits = [
        ("Hull code", callsign),
        ("Registry prefix", ship.get("Name prefixes") or "-"),
        ("Ship name", ship.get("Ship names", "-")),
        # .get rather than [...] throughout the optional rows, so regenerating
        # a ship from an entry written before a table existed still writes a
        # dossier rather than raising - the same allowance write_dossier()
        # makes for an NPC that predates Theme.
        ("Theme", ship.get("Theme", "-")),
        ("Ship type", ship["Ship type"]),
        ("Size", ship["Size"]),
        ("Size band", band),
        ("Grid footprint", "%d x %d hexes" % (grid_w, grid_h)),
        # Split rather than printed whole: the stored trait is the three-
        # segment bullet, and a row reading "Union Administrative Department ||
        # a plain white departmental seal ... || mil palette" would put the
        # tables file's own syntax in front of a reader.
        ("Affiliation", operator),
        ("Livery", livery or "none - unaffiliated"),
        ("Hull", ship["Hull"]),
        ("Detail", ship["Detail"]),
        ("Weapon", ship.get("Weapon", "") or "unarmed"),
        ("Shield generator", ship.get("Shield generator", "") or "none fitted"),
        ("Launch catapult", ship.get("Launch catapult", "") or "none fitted"),
        ("Command bridge", ship.get("Command bridge", "-")),
        ("Markings", ship.get("Markings", "-")),
        ("Condition", ship.get("Condition", "-")),
        ("Portrait shot", shot),
        ("Portrait scene", scene),
        ("Portrait weather", ship.get("Weather", "-") if "weather" in backdrop_flags
         else "none - the rolled scene is in vacuum or under cover"),
        ("Glow colour", ship.get("Glow colour", "-")),
        ("Glow placement", ship.get("Glow placement", "-")),
    ]

    lines = [
        "# %s" % ship["name"],
        "",
        '"%s" - %s, %s.' % (callsign, type_name_of(ship), operator),
        "",
        "Rolled by `generate-spaceship.py` on %s with `--seed %d`. Re-rolling with"
        % (time.strftime("%Y-%m-%d"), seed),
        "that seed and the same tables file reproduces this ship exactly.",
        "",
        "## Traits",
        "",
        "| | |",
        "|---|---|",
    ]
    lines += ["| %s | %s |" % (label, value) for label, value in traits]
    lines += [
        "",
        "## Art",
        "",
    ]
    lines += ["- `%s`" % name for name in images] or ["- _(none generated)_"]
    lines += [
        "",
        "### Portrait prompt",
        "",
        "```",
        portrait_prompt,
        "```",
        "",
        "### Token prompt",
        "",
        "```",
        token_prompt,
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


# Why each refusal is a refusal, printed verbatim so the answer to "why not the
# ship's name" is in the error rather than in this file.
UNREROLLABLE_REASONS = {
    "Ship names": "the ship's folder and manifest id are derived from its "
                  "name, so re-rolling it would not be a change in place",
    "Name prefixes": "it is half the ship's name, and the folder and manifest "
                     "id are derived from that, so re-rolling it would not be "
                     "a change in place",
    # Unreachable for anything this script has ever written - every ship entry
    # carries rawTraits from the first one - and kept anyway, because a
    # hand-edited or hand-merged manifest is not unreachable, and an entry
    # with nothing to pin has to be refused with the cure named rather than
    # re-roll the whole ship under the name of one trait.
    "_no_raw": "this entry predates rawTraits and recorded no raw bullets, so "
               "there is nothing to pin the rest of the ship to - re-roll the "
               "ship to record them",
}


def variant_key(ship):
    """The key variant_table()/heading_for() take for THIS ship.

    variant_table() takes a caller-supplied string; the NPC script hands it a
    pronoun subject so '## Hair (she)' replaces '## Hair'. Ships have no
    pronouns and hand it the SIZE BAND instead, so '## Hull (huge)' replaces
    and '## Command bridge (small) +' adds. No code change on that side - only
    a different key - and the tables file, not this script, decides which
    traits are band-varying.
    """
    return band_of(ship)


def reroll_from_raw(tables, ship, free, rng, pinned=None):
    """Re-draw the traits in `free`, with every other raw bullet pinned.

    generate-npc.py:3494-3543 against roll_ship(). A re-roll is a fresh roll
    with one free variable and a Theme cascade is the same operation with six,
    so the free set is a parameter and neither end knows about the other.

    Pinning raw bullets is the designed use of the override path, not a trick:
    every pinned trait arrives carrying the flags its dependents filter on - a
    pinned '## Ship type' still carries its slug, which is what
    filter_by_ship_policy() keys the whole equipment matrix off - so every
    freed trait is drawn by the ordinary roller under the ordinary filters and
    there is no second copy of the filter chain here to drift from the one in
    roll_ship().

    `pinned` is for the one trait in a cascade whose new value is chosen rather
    than drawn: merged over the overrides after the free set has been
    subtracted, so a trait can be freed - releasing everything downstream - and
    still arrive at a value the caller picked.

    The result replaces `ship` wholesale, '_raw' included, because the fresh
    roll's _raw holds the bullets this ship now actually has. Keeping the old
    one would leave the regen writer persisting rawTraits that describe
    equipment the ship no longer carries. Cleared and updated rather than
    rebound, because regenerate_one() holds the reference.
    """
    # A table this entry has no bullet for cannot be pinned, so it rolls free
    # and the trait changes without having been asked for. Warn and proceed,
    # which is the settled answer to a stored entry that predates a table:
    # refusing would break the promise that a stored ship keeps regenerating,
    # and pinning a fabricated value would be worse than either. Anything in
    # `free` is excluded - it was asked for, so it re-rolling is the request.
    unrecorded = [trait for trait in REQUIRED_TABLES
                  if trait not in ship["_raw"] and trait not in free]
    if unrecorded:
        print("! this entry recorded no raw bullet for: %s (written before "
              "that table existed) - a trait with nothing to pin re-rolls "
              "along with the one you named instead of being kept. Re-roll "
              "the ship to record it." % ", ".join(unrecorded), file=sys.stderr)

    overrides = {trait: bullet for trait, bullet in ship["_raw"].items()
                 if trait not in free}
    overrides.update(pinned or {})
    fresh = roll_ship(tables, rng, overrides)
    ship.clear()
    ship.update(fresh)


def draw_different_theme(tables, current, rng):
    """A theme from the table that is not `current`.

    generate-npc.py:3456-3492, verbatim in shape. A Theme re-roll that draws
    the theme it already had spends six traits and a render producing a
    differently-painted version of the same idea, which is not what the button
    says it does.

    Excluding the current theme and drawing once conditions the same weighted
    distribution on the same event that rejection sampling would, so there is
    no retry loop here to look for - and unlike a retry loop this cannot spin
    forever on a file that offers a single theme. Weighting survives the
    exclusion because parse_tables() expands 'x2 salvage' into two copies in a
    flat list, so dropping one theme's copies leaves every other theme in its
    original proportion.
    """
    others = [theme for theme in tables["Theme"] if theme != current]
    if not others:
        print("! the tables file offers only one theme (%r), so the re-roll "
              "keeps it - the themed tables will draw again within it rather "
              "than under a new one" % current, file=sys.stderr)
        return current
    return rng.choice(others)


def reroll_ship_trait(tables, ship, name, rng):
    """Re-roll one trait of an already-rolled ship in place, and return it.

    Much shorter than generate-npc.py:3566-3810, and the missing half is the
    point: that function's second path rebuilds by hand the filters a
    flag-stripped legacy entry can still support. No ship entry has ever been
    written without its raw bullets, so there is no such path here - only the
    refusal for a hand-edited entry that lost them.

    The free set is the target's CASCADE rather than the target alone. Pinning
    filters in one direction only: the freed trait is drawn against everything
    pinned, but a pinned trait is never re-drawn, so nothing re-checks it
    against the value that just changed. Freeing 'Ship type' alone would leave
    a cargo hauler's kept launch catapult exactly where the policy matrix
    forbids one. A trait nothing depends on closes to itself, so the ten leaves
    take the identical path and still move nothing but themselves.
    """
    raw = ship.get("_raw")
    if not raw:
        raise SystemExit(
            "--reroll-trait %s: cannot re-roll from this entry, because %s.\n"
            "Re-rollable once the ship is re-rolled: %s"
            % (name, UNREROLLABLE_REASONS["_no_raw"], ", ".join(RAW_REROLLABLE_TRAITS)))

    if name not in RAW_REROLLABLE_TRAITS:
        reason = UNREROLLABLE_REASONS.get(
            name, "it is not a trait this script rolls")
        raise SystemExit(
            "--reroll-trait %s: cannot re-roll that one on its own, because "
            "%s.\nRe-rollable: %s"
            % (name, reason, ", ".join(RAW_REROLLABLE_TRAITS)))

    # Theme's new value is chosen rather than drawn, and it is the only one -
    # see draw_different_theme(). It still travels in the free set, so the five
    # themed tables and their dependents draw again under the NEW theme
    # instead of staying pinned to bullets tagged for the old one.
    pinned = None
    if name == "Theme":
        pinned = {"Theme": draw_different_theme(tables, ship["Theme"], rng)}
    reroll_from_raw(tables, ship, trait_cascade(name), rng, pinned)
    return ship[name]


def trait_choices(tables, ship, name):
    """Which bullets `name` could take on this ship, and what each would cost.

    generate-npc.py:3811-3939 against roll_ship(), with the pronoun subject
    replaced by the size band. Two questions per bullet, running in opposite
    directions.

    Upstream: could the roller have produced this bullet for this table, given
    the traits above it? That is `probe[name]` from a roll with the whole ship
    pinned - the pool roll_ship() filtered, read back rather than recomputed.
    One roll answers it for the entire table at once, because a table's pool is
    built from the traits ABOVE it and those are pinned regardless of which
    candidate is being asked about. Recomputing instead would be a second copy
    of the policy matrix, and its failure mode is the silent one: the GUI
    offers a spinal lance on a courier and the render is the first thing that
    disagrees.

    Downstream: if this bullet replaced the current one, would any trait BELOW
    it be left holding a value the roller would no longer offer? Here the
    cascade is deliberately NOT run - keeping the dependents is the point - so
    the contradiction is reported instead of avoided.

    Weather is exempt from the downstream pass for the reason the NPC version
    exempts it: nothing narrows the Weather pool. The Backdrop's 'weather' flag
    is read at prompt-build time and decides only whether the rolled Weather is
    RENDERED, so a kept Weather is never illegal, only newly hidden or newly
    shown, and checking it would report every Backdrop in the table as
    conflicting.

    Nothing is dropped. Both answers ride on the entry and the caller decides:
    the picker this feeds greys ruled-out values and still lets them be chosen,
    which mirrors --set-trait's own behaviour of bypassing the roll pool. This
    function describes the pool; it does not enforce it.

    The rng is fixed rather than passed in. Every roll here is fully pinned, so
    nothing is actually drawn and the seed cannot reach the result - but a
    caller handing in a live rng would have its stream silently consumed by a
    query, a bug that would only ever surface as an unrelated ship changing.
    """
    key = variant_key(ship)
    raw = dict(ship["_raw"])

    baseline = {}
    roll_ship(tables, random.Random(0), raw, probe=baseline)
    pool = set(baseline.get(name, ()))

    dependents = [d for d in TRAIT_DEPENDENTS.get(name, ()) if d != "Weather"]

    # Deduplicated, order preserved. variant_table() repeats a bullet once per
    # point of weight, because that is how the roller makes a heavier bullet
    # more likely - fine for rng.choice(), wrong for a list somebody reads: an
    # 'x8 ' empty Name prefixes bullet would appear eight times in the picker.
    # Weight is not lost, it is just not this function's subject; what a
    # bullet's odds are is what --trait-odds answers.
    candidates = list(dict.fromkeys(variant_table(tables, name, key)))

    out = []
    for bullet in candidates:
        current = bullet == raw.get(name)
        # The value it already has cannot contradict what it is already
        # carrying, and skipping it here is not an optimisation - running the
        # check would compare the ship against itself and could only ever
        # report a conflict that predates this feature.
        if dependents and not current:
            forced = dict(raw, **{name: bullet})
            after = {}
            try:
                roll_ship(tables, random.Random(0), forced, probe=after)
            except SystemExit:
                # A pairing the roller refuses outright rather than filters -
                # an unsatisfiable (type, band) forced from both ends is the
                # reachable one. That refusal is a conflict of the hardest
                # kind, so it is reported as one, and which dependent caused
                # it is asked of the roller rather than parsed out of its
                # message: free one at a time and see which one makes the
                # refusal go away.
                conflicts = []
                for d in dependents:
                    if d not in raw:
                        continue
                    trial = dict(forced)
                    del trial[d]
                    try:
                        roll_ship(tables, random.Random(0), trial, probe={})
                    except SystemExit:
                        continue    # still refused, so freeing d is not the cure
                    conflicts.append(d)
                # Refused however we free them one at a time means more than
                # one is implicated. Naming them all is the honest answer, and
                # releasing them all is the remedy that actually works.
                conflicts = conflicts or [d for d in dependents if d in raw]
            else:
                conflicts = [d for d in dependents
                             if d in raw and raw[d] not in after.get(d, ())]
        else:
            conflicts = []

        # What --release <conflicts> would actually free. Reported rather than
        # left to the caller to derive, so the picker can name what moves
        # without a copy of trait_cascade() in JavaScript.
        releases = set()
        for d in conflicts:
            releases |= set(trait_cascade(d))
        releases -= {name}

        out.append({
            "value": bullet,
            "heading": heading_for(tables, name, key, bullet),
            "allowed": bullet in pool,
            "current": current,
            "conflicts": conflicts,
            "releases": sorted(releases),
        })
    return out


def ship_trait_odds(tables, samples, rng):
    """Each bullet's chance of being rolled, as {heading: {bullet: fraction}}.

    generate-npc.py:1323-1359 against roll_ship(). Sampled, not computed: the
    alternative - propagating a distribution through EQUIPMENT_POLICY,
    LIGHT_CAP, filter_by_size and the theme share analytically - would be a
    second implementation of the filter chain sitting beside the first, and its
    failure mode is the silent one. Nothing crashes; the numbers are simply
    wrong.

    The number is unconditional: the fraction of rolled ships that end up with
    this bullet under this heading. A per-band variant family therefore splits
    its total across its headings rather than each heading summing to 1 - a
    '## Hull (huge)' bullet is reachable only by a five-hex ship, so those rows
    sum to the share of ships that are five-hex. That is the honest answer.

    And 'Weather' sums to 1 though most ships show none: it is always rolled,
    and the prompt builder then drops it unless the Backdrop is flagged
    'weather'. Reporting the joint probability instead would read 0% for every
    bullet flagged 'clear', which opts out of rendering by design - so the
    number stays a roll frequency and the caveat belongs in whatever displays
    it.
    """
    counts = {key: {bullet: 0 for bullet in bullets}
              for key, bullets in tables.items()}
    for _ in range(samples):
        ship = roll_ship(tables, rng)
        key = variant_key(ship)
        for name, bullet in ship["_raw"].items():
            counts[heading_for(tables, name, key, bullet)][bullet] += 1
    return {key: {bullet: n / samples for bullet, n in bullets.items()}
            for key, bullets in counts.items()
            if any(k == key or key.startswith(k + " (") for k in REQUIRED_TABLES)}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def default_root(args=None):
    """The tree run folders are numbered under.

    --out-root before the environment before the module default, because the
    GUI configures a root per kind and the ship tree is not the NPC tree.
    """
    if args is not None and args.out_root:
        return args.out_root
    return DEFAULT_OUTPUT_ROOT


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description=__doc__.split("\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Tables: %s" % DEFAULT_TABLES,
    )

    roll = p.add_argument_group("the roll")
    roll.add_argument("--count", type=int, default=1, help="how many ships to roll (default 1)")
    roll.add_argument("--seed", type=int,
                      help="base seed; ship N uses seed+N, so a run is reproducible")
    roll.add_argument("--tables", type=Path, default=DEFAULT_TABLES,
                      help="roll-tables markdown (default: %(default)s)")
    roll.add_argument("--name", help="force the ship's name instead of rolling one")
    # --ship-type is the name the GUI emits and --type the one the design doc
    # uses; both are here rather than one of them being right, because the
    # cost of an alias is a line and the cost of guessing wrong is a spawn
    # shape that exits 2 with the job log as the only evidence.
    roll.add_argument("--ship-type", "--type", dest="ship_type",
                      choices=list(sp.SHIP_TYPE_ORDER), metavar="SLUG",
                      help="roll only this kind of ship (%s); the size bands it "
                           "may take are its own - see --ship-catalogue"
                           % ", ".join(sp.SHIP_TYPE_ORDER))
    roll.add_argument("--size", choices=list(sp.SIZE_ORDER), metavar="BAND",
                      help="roll only hulls of this band (%s); the Foundry token "
                           "spans %s hexes respectively"
                           % (", ".join(sp.SIZE_ORDER),
                              "/".join(str(sp.hexes_for(b)) for b in sp.SIZE_ORDER)))
    roll.add_argument("--theme", metavar="NAME",
                      help="force the rolled Theme, pinning the whole visual "
                           "world to one look (same as --set-trait Theme=NAME)")
    roll.add_argument("--set-trait", action="append", default=[], metavar="Table=value",
                      help="force one rolled trait to a verbatim bullet, flags "
                           "included, e.g. --set-trait Condition='freshly yard-"
                           "fresh, paint unfaded' (repeatable; table names are "
                           "the markdown headings)")

    gen = p.add_argument_group("generation")
    gen.add_argument("--workflow", type=Path, default=art.DEFAULT_WORKFLOW,
                     help="API-format generation workflow (default: %(default)s)")
    gen.add_argument("--rmbg", type=Path, default=art.POST_ALIASES["rmbg"],
                     help="background-removal workflow for the token")
    gen.add_argument("--rmbg-res", type=int, default=1536, metavar="N",
                     help="RMBG-2.0's square inference resolution (default: "
                          "%(default)s). Patched onto the post workflow rather "
                          "than shipped as a second graph. The packaged one "
                          "says 1024, which is lossless on the NPC token's 4:5 "
                          "and squashes a five-hex carrier's 5:3 by 1.67x - "
                          "antenna masts and catapult rails are exactly what a "
                          "squashed mask drops, and they come back cut off the "
                          "token")
    gen.add_argument("--no-portrait", action="store_true", help="token only")
    gen.add_argument("--no-token", action="store_true", help="portrait only")
    gen.add_argument("--keep-raw-token", action="store_true",
                     help="also save the token's opaque pre-RMBG render")
    gen.add_argument("--steps", type=int, help="override sampler steps")
    gen.add_argument("--cfg", type=float, help="override CFG")
    gen.add_argument("--sampler", help="override sampler_name")
    gen.add_argument("--scheduler", help="override scheduler")
    gen.add_argument("--set", action="append", default=[], metavar="NODE.input=value",
                     help="patch any workflow input, as in generate-art.py")
    gen.add_argument("--max-token-px", type=int, default=MAX_TOKEN_PX, metavar="N",
                     help="pixel ceiling for a token canvas (default: %(default)s). "
                          "A band over it is scaled down with its aspect kept and "
                          "both dimensions re-snapped to 64, so the Foundry "
                          "footprint is unchanged and only the render is cheaper")

    out = p.add_argument_group("output")
    out.add_argument("--out", type=Path, default=None,
                     help="root to write ship folders into (default: a fresh runN "
                          "folder under %s, so a batch can be reviewed before any "
                          "of it is moved into Foundry by hand; passed explicitly, "
                          "the path is used as-is with no runN folder inserted)"
                          % DEFAULT_OUTPUT_ROOT)
    out.add_argument("--out-root", type=Path, default=None, metavar="DIR",
                     help="tree to number run folders under; --out names one "
                          "run folder and wins over this. The import GUI "
                          "passes it from config.spaceshipOutputRoot.")
    out.add_argument("--overwrite", action="store_true",
                     help="reuse an existing folder of the same name instead of suffixing it")
    out.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST,
                     help="run log of every ship rolled, shared with the NPCs "
                          "so both kinds appear in one import grid (default: "
                          "%(default)s)")

    regen = p.add_argument_group("regenerate one ship from a manifest entry")
    regen.add_argument("--regen-manifest", type=Path, metavar="PATH",
                       help="skip rolling entirely and reload one ship's traits from "
                            "this manifest instead (requires --regen-id); the entry's "
                            "own folder is reused and overwritten in place, and the "
                            "manifest is updated with the new seed/files when it's done")
    regen.add_argument("--regen-id", metavar="ID",
                       help="the manifest entry's \"id\" to regenerate (requires --regen-manifest)")
    regen.add_argument("--new-seed", type=int, metavar="N",
                       help="seed for the re-render (default: the entry's original seed, "
                            "which reproduces the image exactly); every rolled trait comes "
                            "from the entry either way, so a different seed renders the "
                            "same ship with new noise instead of a new roll")
    regen.add_argument("--reroll-trait", metavar="TABLE",
                       help="re-roll ONE trait of the regenerated ship - and everything "
                            "that trait invalidates - instead of reproducing it. "
                            "--reroll-trait Markings restencils an existing hull and "
                            "nothing else; --reroll-trait 'Ship type' redraws what the "
                            "ship IS, eight traits of it, because the type gates the "
                            "size and every piece of equipment. Every trait that goes "
                            "with it is named on the way past. Re-rollable: "
                            + ", ".join(RAW_REROLLABLE_TRAITS))
    regen.add_argument("--trait-choices", metavar="TABLE",
                       help="print, as JSON on stdout, which values TABLE could take on "
                            "this ship given its other traits - each with whether the "
                            "roller would have offered it ('allowed') and which kept "
                            "traits it would leave contradicting it ('conflicts'). "
                            "Renders nothing and contacts no server. Requires --regen-id.")
    regen.add_argument("--release", metavar="A,B",
                       help="with --set-trait, traits to re-roll instead of keeping - "
                            "meant for the ones --trait-choices reports as conflicting. "
                            "Each name expands to its whole cascade, so releasing Size "
                            "also re-rolls the Hull and the four equipment tables it gates.")
    regen.add_argument("--apply-only", action="store_true",
                       help="with --reroll-trait or --set-trait: apply the edit to the "
                            "manifest entry and stop. Renders nothing, contacts no "
                            "ComfyUI server, and does not touch the entry's seed, files, "
                            "portrait, token or dossier - only its traits, rawTraits, the "
                            "re-derived grid footprint and an artStale marker saying the "
                            "stored art no longer matches. Prints the updated traits as "
                            "JSON on stdout. Meant for staging several edits before one "
                            "render.")

    run = p.add_argument_group("run mode")
    run.add_argument("--ship-catalogue", action="store_true",
                     help="print the ship types, the size bands each may roll and "
                            "the Foundry grid footprint of each band, as JSON on "
                            "stdout, then exit - no roll, no images, nothing "
                            "written. Read by the Import GUI's create form")
    run.add_argument("--trait-odds", type=int, nargs="?", const=20000, metavar="N",
                     help="roll N ships (default 20000) and print each bullet's "
                          "chance of being rolled as JSON, then exit - no images, "
                          "no manifest, nothing written. Sampled through the real "
                          "roller, so every filter is accounted for: a launch "
                          "catapult reads near zero because only carriers and the "
                          "largest battleships can reach one at all")
    run.add_argument("--server", help="ComfyUI address, e.g. 127.0.0.1:8000")
    run.add_argument("--dry-run", action="store_true",
                     help="roll and print the ships and their prompts, queue nothing")
    run.add_argument("--json", action="store_true",
                     help="with --dry-run: put the rolled ships on stdout as JSON and "
                          "every human-readable line on stderr, so stdout parses whole")
    run.add_argument("--timeout", type=float, default=1800, help="per-job timeout in seconds")
    run.add_argument("--pause", type=float, default=2.0,
                     help="seconds to sleep after each ComfyUI job (portrait, token, "
                          "background removal), so a batch doesn't queue jobs back-to-back "
                          "faster than the server can keep up (default: %(default)s)")

    args = p.parse_args(argv)

    # --pronouns and --unarmed are deliberately absent rather than accepted and
    # ignored. A ship has neither, and a silent no-op would hide a GUI that is
    # still emitting the NPC flag set for a kind:"spaceship" job - argparse's
    # exit 2 on stderr is what makes that visible on the first run.

    if args.no_portrait and args.no_token:
        p.error("--no-portrait and --no-token together leave nothing to generate")

    if args.json and not args.dry_run:
        p.error("--json describes what --dry-run would produce; it has no output of its own")

    if bool(args.regen_manifest) != bool(args.regen_id):
        p.error("--regen-manifest and --regen-id must be given together")
    if args.regen_manifest:
        # --set-trait is deliberately NOT in this list. "Replaces the roll
        # entirely" is still true of every flag that is: each of them would be
        # asking for a different ship. Naming one trait's value while
        # reproducing the rest is the opposite request, and reroll_from_raw()
        # has a `pinned` parameter for exactly it.
        conflicting = [
            flag for flag, given in (
                ("--count", args.count != 1), ("--seed", args.seed is not None),
                ("--name", bool(args.name)), ("--ship-type", bool(args.ship_type)),
                ("--size", bool(args.size)), ("--theme", bool(args.theme)),
            ) if given
        ]
        if conflicting:
            p.error("--regen-manifest replaces the roll entirely; drop %s" % ", ".join(conflicting))
    elif args.new_seed is not None:
        p.error("--new-seed only makes sense with --regen-manifest")

    if args.count < 1:
        p.error("--count must be at least 1")
    if args.name and args.count > 1:
        p.error("--name only makes sense with a single ship")

    # Checked here rather than left to the roller's reverse gate, because this
    # pair is knowable without the tables file and the gate's answer is a
    # fallback with a warning - the right trade for a bullet the user pinned
    # by hand, the wrong one for two flags that simply cannot both be honoured.
    # 'patrol' and 'huge' is not a narrow pool, it is a contradiction.
    if args.ship_type and args.size and args.size not in sp.sizes_for(args.ship_type):
        p.error("--ship-type %s only comes in %s; --size %s is not one of them"
                % (args.ship_type, ", ".join(sp.sizes_for(args.ship_type)), args.size))

    try:
        args.set = [art.parse_set(spec) for spec in args.set]
    except ValueError as exc:
        p.error(str(exc))

    overrides = {}
    for spec in args.set_trait:
        table, sep, value = spec.partition("=")
        if not sep or not table.strip():
            p.error("--set-trait: expected Table=value, got %r" % spec)
        table = table.strip()
        # A repeated table used to last-wins silently, which reads as though
        # both values took effect when only the final one did.
        if table in overrides:
            p.error("--set-trait %s given twice (%r then %r); pass it once"
                    % (table, overrides[table], value.strip()))
        overrides[table] = value.strip()

    # Each sugar flag against its own --set-trait, so the two paths cannot
    # quietly disagree about the same table. --theme merges into the overrides
    # because a theme IS a bullet; --ship-type and --size do not, because they
    # name a flag rather than a bullet and have to be resolved against the
    # tables file - see resolve_forced_bullets().
    if args.theme:
        if "Theme" in overrides:
            p.error("--theme and --set-trait Theme= set the same thing; use one")
        overrides["Theme"] = args.theme
    if args.ship_type and "Ship type" in overrides:
        p.error("--ship-type and --set-trait 'Ship type'= set the same thing; use one")
    if args.size and "Size" in overrides:
        p.error("--size and --set-trait Size= set the same thing; use one")
    args.overrides = overrides

    # Below args.overrides, because all of these read it.
    if args.trait_choices:
        if not args.regen_manifest:
            p.error("--trait-choices needs --regen-manifest and --regen-id")
        if args.reroll_trait:
            p.error("--trait-choices only reports; drop --reroll-trait")
        if args.overrides:
            p.error("--trait-choices only reports; drop --set-trait")

    if args.reroll_trait and args.overrides:
        p.error("--reroll-trait draws a new value and --set-trait names one; use one")

    # --trait-choices before the edit flags, because it is refused above for
    # carrying either of them: checking "nothing to apply" first would answer
    # --trait-choices --apply-only with a complaint about the missing edit flag
    # that adding one would not fix.
    if args.apply_only:
        if not args.regen_manifest:
            p.error("--apply-only needs --regen-manifest and --regen-id")
        if args.trait_choices:
            p.error("--trait-choices only reports; drop --apply-only")
        if not args.reroll_trait and not args.overrides:
            p.error("--apply-only needs --reroll-trait or --set-trait; it has nothing to apply")

    args.release = [n.strip() for n in (args.release or "").split(",") if n.strip()]
    if args.release:
        if not args.overrides:
            p.error("--release only makes sense with --set-trait")
        # Only what the set trait actually gates. Releasing anything else is a
        # re-roll wearing a disguise, and --reroll-trait is the flag for that.
        # Checked against the direct dependents rather than the transitive
        # closure: --release Size is legal under --set-trait 'Ship type' and
        # brings its own cascade with it at the point of use, but --release
        # Hull is not, because it is Size that gates the hull and Size that
        # should have been released.
        releasable = set()
        for table in args.overrides:
            releasable |= set(TRAIT_DEPENDENTS.get(table, ()))
        stray = [n for n in args.release if n not in releasable]
        if stray:
            p.error(
                "--release %s: not gated by %s. Releasable here: %s"
                % (", ".join(stray), ", ".join(sorted(args.overrides)),
                   ", ".join(sorted(releasable)) or "nothing"))

    # --trait-odds and --ship-catalogue join --regen-manifest in not needing an
    # output root: they render nothing. Picking a run folder is harmless in
    # itself (the path is only computed, not created), but it would make a
    # read-only query depend on the output root existing and being readable,
    # which it has no business caring about.
    if (args.out is None and not args.regen_manifest and not args.trait_odds
            and not args.ship_catalogue):
        args.out = next_run_folder(default_root(args))

    return args


def print_ship_catalogue(args):
    """--ship-catalogue: the create form's whole vocabulary, as JSON on stdout.

    Everything a "new spaceship" dialog needs to build itself without a copy of
    the policy matrix in JavaScript: which types exist, which bands each may
    take, and what each band costs in grid hexes and canvas pixels. Derived
    from ship_policy.SHIP_TYPES and SIZE_BANDS rather than listed, so a type
    added there appears in the form the same day.

    Themes come from the tables file when it is readable and are an empty list
    when it is not, with a note on stderr. A missing tables file is a real
    situation on a fresh checkout, and a create form that opens with no theme
    picker is a better answer than one that will not open at all - the roll
    itself refuses loudly enough for both of them.
    """
    themes = []
    if args.tables.exists():
        tables = parse_tables(args.tables)
        themes = sorted(set(tables.get("Theme", [])))
    else:
        print("! tables file not found (%s) - the catalogue's theme list is "
              "empty; types and sizes are read from ship_policy.py and are "
              "unaffected" % args.tables, file=sys.stderr)

    json.dump({
        "types": [
            {"slug": slug,
             "name": sp.SHIP_TYPES[slug]["name"],
             "sizes": list(sp.sizes_for(slug)),
             "folder": SHIP_FOLDERS.get(slug, UNCATEGORIZED_SHIP)}
            for slug in sp.SHIP_TYPE_ORDER
        ],
        "sizes": [
            dict(token_metadata(band, args.max_token_px),
                 gloss=sp.SIZE_BANDS[band]["gloss"])
            for band in sp.SIZE_ORDER
        ],
        "themes": themes,
    }, sys.stdout)
    return 0


def print_trait_choices(args):
    """--trait-choices: which values one trait could take, as JSON.

    Prints to stdout and nothing else, because the caller parses stdout whole -
    the same contract --trait-odds and --ship-catalogue keep. Anything
    diagnostic goes to stderr.
    """
    manifest = art.load_manifest(args.regen_manifest)
    _, entry = find_regen_entry(manifest, args.regen_id, args.regen_manifest)
    ship = ship_from_entry(entry, args.regen_id, warn=False)

    # Pinning is what makes a chosen value mean anything, and an entry with no
    # raw bullets has nothing to pin: its stored traits lost their flags on the
    # way in, so the filters this query reports on cannot run against them.
    # Refused with the cure named, the way reroll_ship_trait() names it.
    raw = ship.get("_raw")
    if not raw:
        raise SystemExit(
            "--trait-choices %s: %s." % (args.trait_choices,
                                         UNREROLLABLE_REASONS["_no_raw"]))

    # The same list --reroll-trait would use, so a trait the GUI is told it
    # cannot choose is a trait it is also told it cannot re-roll. Offering one
    # without the other would be worse than neither.
    if args.trait_choices not in RAW_REROLLABLE_TRAITS:
        reason = UNREROLLABLE_REASONS.get(
            args.trait_choices, "it is not a trait this script rolls")
        raise SystemExit(
            "--trait-choices %s: cannot choose that one, because %s.\n"
            "Choosable: %s"
            % (args.trait_choices, reason, ", ".join(RAW_REROLLABLE_TRAITS)))

    if not args.tables.exists():
        raise SystemExit("--trait-choices needs the tables file: %s" % args.tables)
    tables = parse_tables(args.tables)
    check_tables(tables, args.tables, getattr(parse_tables, "repeated", ()))

    json.dump({
        "trait": args.trait_choices,
        "current": raw.get(args.trait_choices),
        "dependents": list(TRAIT_DEPENDENTS.get(args.trait_choices, ())),
        "choices": trait_choices(tables, ship, args.trait_choices),
    }, sys.stdout)
    return 0


# ---------------------------------------------------------------------------
# Workflows
# ---------------------------------------------------------------------------


def load_workflow(args):
    """The one generation template every ship goes through, validated.

    Ships have a single workflow where NPCs have two - GENDER_WORKFLOWS,
    workflow_for() and --workflow-woman are all dropped - so this collapses
    generate-npc.py's load_workflows() to one load and one slot check.

    A missing EmptyLatentImage is an ERROR here where the NPC script prints a
    warning and carries on. That difference is deliberate and it is the whole
    of §4's risk: an NPC token is always 1024x1280 so falling back to the
    workflow's own size costs nothing, whereas a five-hex carrier silently
    rendered at 1024x1280 is a token Foundry then stretches across five hexes
    of map. That is not a cosmetic degradation, it is an unusable asset that
    looks like a successful run.
    """
    if not args.workflow.exists():
        raise SystemExit("Workflow not found: %s" % args.workflow)
    template = art.load_api_workflow(args.workflow)
    try:
        slots = art.locate_slots(template)
    except art.WorkflowError as exc:
        raise SystemExit("%s: %s" % (args.workflow.name, exc))
    if not slots.latent:
        raise SystemExit(
            "%s has no EmptyLatentImage wired to its sampler, so every token "
            "would render at the workflow's own size regardless of the hull's "
            "size band - a five-hex carrier at one hex. Fix the workflow or "
            "pass --workflow." % args.workflow.name)
    return template, slots


def load_post_workflow(args):
    """The background-removal template, with RMBG's inference resolution raised.

    Patched here rather than shipped as a second graph, so the repository keeps
    one RMBG workflow. RMBG-2.0 resizes its input to a square process_res,
    infers the mask and resizes the mask back: at the NPC token's 4:5 the
    packaged 1024 is nearly lossless, at the huge band's 5:3 it squashes by
    1.67x, and thin high-frequency structure - antenna masts, sensor booms,
    catapult rails, wingtip stencilling - is exactly what a squashed inference
    drops from a mask. It comes back cut off the token.

    setdefault on "inputs" rather than [...], because a hand-authored graph
    with an inputs-less node is a KeyError here and a confusing one: the node
    it names is the right node.
    """
    if not args.rmbg.exists():
        raise SystemExit("Background-removal workflow not found: %s" % args.rmbg)
    post_template = art.load_api_workflow(args.rmbg)
    for node in post_template.values():
        if node.get("class_type") == "RMBG":
            node.setdefault("inputs", {})["process_res"] = args.rmbg_res
    try:
        post_slots = art.locate_post_slots(post_template)
    except art.WorkflowError as exc:
        raise SystemExit("%s: %s" % (args.rmbg.name, exc))
    return post_template, post_slots


# ---------------------------------------------------------------------------
# Regeneration
# ---------------------------------------------------------------------------


def find_regen_entry(manifest, regen_id, manifest_path):
    """The (folder path, entry) pair for one id, or a refusal naming it.

    Matches on id alone rather than on id and kind. The manifest holds NPCs and
    ships together and their ids are prefixed 'npc-' and 'ship-', so a
    collision is unreachable; refusing a kind:"npc" entry here instead would
    turn a GUI that mixed up two jobs into a puzzle about the manifest.
    """
    folder_path, entry = next(
        ((k, v) for k, v in manifest.items() if isinstance(v, dict) and v.get("id") == regen_id),
        (None, None),
    )
    if entry is None:
        raise SystemExit("--regen-id %r: no such entry in %s" % (regen_id, manifest_path))
    return folder_path, entry


def ship_from_entry(entry, regen_id, warn=True):
    """A manifest entry rebuilt into the dict roll_ship() would have produced.

    Lifted out of regenerate_one() so --trait-choices reads an entry the same
    way a regen does. Two reconstructions would drift, and the direction they
    would drift in is the worst one available: a query answering about a
    slightly different ship than the one the regen is about to render.

    Much shorter than npc_from_entry(), and the missing part is the seven
    derived booleans that file reloads. Ships publish none: every ship pairing
    is rebuildable from rawTraits, because ship_policy filters on the bullets'
    own flags rather than on a value with its flags already stripped. That is
    the whole reason 'young'/'outfit_notac'/'gear_helmet' exist over there and
    nothing like them exists here.

    `warn` is off for the query, which is a read-only question a GUI may ask
    many times over. The migration notices belong on the run that actually
    writes something - and the query prints JSON to stdout, so a stray line
    would corrupt it besides.
    """
    ship = dict(entry["traits"])
    if "rawTraits" in entry:
        # No default: absent is 'not recorded', which reroll_ship_trait() and
        # print_trait_choices() both distinguish from a recorded empty dict. A
        # plain regen never looks at _raw, so it is neither needed nor degraded
        # by its absence - the refusal belongs where the raw bullets are
        # actually needed.
        ship["_raw"] = dict(entry["rawTraits"])
    if warn:
        missing = [t for t in REQUIRED_TABLES if t not in ship]
        if missing:
            print("! %s has no recorded %s (written before that table existed) - "
                  "regenerating without it; re-roll instead of regenerating to "
                  "pick it up." % (regen_id, ", ".join(missing)), file=sys.stderr)
    return ship


def persist_traits(entry, ship):
    """Write the rolled ship's traits and raw bullets back onto its entry.

    Shared by the render path and --apply-only so the two cannot drift. The
    NPC script has this same function and a persist_flags() beside it, and
    writing one without the other is what left its set-trait entries holding
    new flags over old bullets; ships have no derived flag registers at all,
    so this is the whole of the write.
    """
    entry["traits"] = {k: v for k, v in ship.items() if not k.startswith("_")}
    # Only when _raw is actually known. An entry loaded with no rawTraits
    # leaves ship["_raw"] unset, and this regen never had raw bullets to begin
    # with - writing some in now would invent a provenance the entry never had.
    if ship.get("_raw") is not None:
        entry["rawTraits"] = dict(ship["_raw"])


def persist_size(entry, ship, max_px=MAX_TOKEN_PX):
    """Re-derive the five grid/canvas fields from the ship's CURRENT Size.

    Called after either edit path, not only after a Size edit, because Size is
    re-rolled transitively: --reroll-trait 'Ship type' redraws the band through
    the cascade, and --set-trait 'Ship type'= --release Size does the same on
    purpose. Deriving from the trait that is actually in the entry now means
    the recorded footprint cannot describe the band the ship used to have.

    Silently skipped for an entry whose _raw lost its Size bullet: the band
    lives in that bullet's flags and there is nothing honest to derive from the
    rendered prose, so the stored footprint stays as it was rather than being
    replaced with a guessed 'small'. reroll_from_raw() has already warned about
    the missing bullet by the time this runs.
    """
    if not ship.get("_raw", {}).get("Size"):
        return
    entry.update(token_metadata(band_of(ship), max_px))


def band_for_regen(ship, entry, regen_id):
    """The size band a regen should render at: the current bullet, else the entry.

    Off the raw Size bullet whenever there is one, so a --reroll-trait or a
    --set-trait that moved the band renders the NEW footprint rather than the
    stored one - which is the whole point of re-deriving the size fields after
    an edit.

    The entry's recorded sizeBand is the fallback rather than an assumption of
    'small', because an entry that lost its raw bullets still knows what it was
    rendered at, and re-rendering a stored carrier at one hex would be a worse
    answer than any error message. A recorded band this script does not know is
    the one case that has to guess, and it guesses loudly.
    """
    raw_size = ship.get("_raw", {}).get("Size")
    if raw_size:
        return sp.size_of(raw_size)
    band = entry.get("sizeBand")
    if band in TOKEN_GRID:
        return band
    print("! %s records no usable size band (%r) - rendering its token at %r. "
          "Re-roll the ship to record its Size bullet."
          % (regen_id, band, sp.SIZE_ORDER[0]), file=sys.stderr)
    return sp.SIZE_ORDER[0]


def regenerate_one(args):
    """Re-render one ship's portrait and/or token from a stored manifest entry.

    Skips roll_ship and the tables file entirely unless an edit flag asks for
    them - every trait comes from the entry exactly as it was originally
    rolled, so the prompt reproduces identically regardless of --new-seed. The
    entry's own folder is reused and overwritten in place (same filenames),
    unlike a fresh roll's asset_folder(), which suffixes rather than collides.
    """
    manifest = art.load_manifest(args.regen_manifest)
    folder_path, entry = find_regen_entry(manifest, args.regen_id, args.regen_manifest)
    ship = ship_from_entry(entry, args.regen_id)

    # --apply-only's caller parses stdout whole, the same contract
    # print_trait_choices() keeps. The re-roll, cascade, set and release
    # reports below are diagnostics, so they go to stderr in that mode - and
    # the GUI surfaces them, since "with Weapon: ... -> ..." is exactly what a
    # user needs to see after clicking Re-roll.
    say = (lambda *a: print(*a, file=sys.stderr)) if args.apply_only else print

    # One trait re-rolled - and everything a filter would have had to reject
    # alongside it. Everything else reproduced. Seeded from the entry's own
    # seed so the same re-roll of the same ship is repeatable, unless
    # --new-seed asks for a different draw.
    rerolled = None
    if args.reroll_trait:
        if not args.tables.exists():
            raise SystemExit("--reroll-trait needs the tables file: %s" % args.tables)
        tables = parse_tables(args.tables)
        check_tables(tables, args.tables, getattr(parse_tables, "repeated", ()))
        # Snapshot before the re-roll replaces the dict wholesale, and every
        # trait rather than the named one: eight of them can move on a
        # 'Ship type' re-roll and the old values are gone once roll_ship() has
        # run.
        before = {k: v for k, v in ship.items() if not k.startswith("_")}
        rerolled = reroll_ship_trait(
            tables, ship, args.reroll_trait,
            random.Random(args.new_seed if args.new_seed is not None else entry["seed"]))
        say("re-rolled %s: %r -> %r"
            % (args.reroll_trait, before.get(args.reroll_trait), rerolled))
        # Enumerated rather than summarised: somebody who re-rolls 'Ship type'
        # expecting a different silhouette gets a new size, faction, four
        # pieces of equipment and a new set of markings, and "and 7 others"
        # would let them find that out from the render. Every trait that
        # travelled is named even where it came back unchanged - a cascade
        # re-draws it either way, and printing only the movers would make an
        # unlucky run look like a smaller change than it was.
        for trait in trait_cascade(args.reroll_trait):
            if trait != args.reroll_trait:
                say("  with %s: %r -> %r" % (trait, before.get(trait), ship.get(trait)))

    # One trait pinned to a chosen value, everything else reproduced - the
    # mirror of the block above, which draws a value instead of taking one.
    if args.overrides:
        if not args.tables.exists():
            raise SystemExit("--set-trait needs the tables file: %s" % args.tables)
        tables = parse_tables(args.tables)
        check_tables(tables, args.tables, getattr(parse_tables, "repeated", ()))
        if not ship.get("_raw"):
            raise SystemExit(
                "--set-trait on a regen needs the entry's raw bullets, so the "
                "rest of the ship has something to be pinned to. Re-roll the "
                "ship to record them.")

        # The same list --reroll-trait accepts, and refused for the same
        # reasons - naming a value rather than drawing one does not make the
        # ship's name any safer to change under a folder and a manifest id
        # derived from it. A table that is not rolled at all is refused here
        # too, rather than passed to roll_ship() where an override for a table
        # it has never heard of is silently dropped: a typo would otherwise
        # regenerate the ship unchanged and report success.
        unsettable = [t for t in args.overrides if t not in RAW_REROLLABLE_TRAITS]
        if unsettable:
            reasons = "; ".join(
                "%s: %s" % (t, UNREROLLABLE_REASONS.get(
                    t, "it is not a trait this script rolls"))
                for t in unsettable)
            raise SystemExit(
                "--set-trait %s: cannot set that on a regen (%s).\nSettable: %s"
                % (", ".join(unsettable), reasons, ", ".join(RAW_REROLLABLE_TRAITS)))

        # free=set() pins every stored bullet; `pinned` swaps the named ones.
        # Re-running roll_ship() rather than assigning ship[table] directly is
        # the point: the '{...}' fill, the flag stripping and _raw all
        # recompute, and _raw ends up describing the ship about to be rendered
        # rather than the one it replaced.
        #
        # A released trait travels as its whole cascade. Freeing the bare name
        # would redraw it and leave everything it gates pinned to bullets
        # chosen for the value that just went - the same contradiction one
        # level down, which is what trait_cascade() exists to close.
        free = set()
        for name in args.release:
            free |= set(trait_cascade(name))
        before = {k: v for k, v in ship.items() if not k.startswith("_")}
        reroll_from_raw(
            tables, ship, free,
            random.Random(args.new_seed if args.new_seed is not None else entry["seed"]),
            dict(args.overrides))
        for table in args.overrides:
            say("set %s: %r -> %r" % (table, before.get(table), ship.get(table)))
        # Named rather than counted, for the same reason the re-roll cascade
        # above names its own: a release reaches further than the trait the
        # user typed, and finding that out from the render is the failure this
        # report exists to prevent.
        for trait in sorted(free):
            if trait not in args.overrides:
                say("  with %s: %r -> %r" % (trait, before.get(trait), ship.get(trait)))

    # The staged-edit exit. Everything above this line is the roll: the entry
    # loaded, one trait re-rolled or pinned, `ship` replaced wholesale.
    # Everything below it needs a ComfyUI server - art.find_server() is
    # contacted even when both stages are skipped - a workflow, and the
    # prompt/file locals the writer at the tail reads, so the cut is here and
    # that writer is shared rather than duplicated.
    if args.apply_only:
        persist_traits(entry, ship)
        # The one thing this exit writes that the NPC version has no analogue
        # for. A staged --set-trait Size= changes the Foundry footprint, and
        # leaving gridWidth describing the old band until the render would
        # give the GUI a preview at the wrong number of hexes - which is
        # exactly the staleness artStale is meant to be the only instance of.
        persist_size(entry, ship, args.max_token_px)
        entry["artStale"] = True
        entry["when"] = time.strftime("%Y-%m-%d %H:%M:%S")
        manifest[folder_path] = entry
        art.save_manifest(args.regen_manifest, manifest)
        json.dump({
            "id": args.regen_id,
            "traits": entry["traits"],
            "rawTraits": entry.get("rawTraits"),
            "artStale": True,
            "sizeBand": entry.get("sizeBand"),
            "gridWidth": entry.get("gridWidth"),
            "gridHeight": entry.get("gridHeight"),
            "tokenWidth": entry.get("tokenWidth"),
            "tokenHeight": entry.get("tokenHeight"),
        }, sys.stdout)
        return 0

    seed = args.new_seed if args.new_seed is not None else entry["seed"]
    prompts = build_ship_prompts(ship)
    portrait_prompt, token_prompt = prompts
    band = band_for_regen(ship, entry, args.regen_id)
    tok_size = token_size(band, args.max_token_px)
    # The entry's own shipType when the raw bullet is gone: the folder is being
    # reused in place anyway, so `category` here only shapes the ComfyUI
    # filename prefix, and taking the recorded slug keeps that prefix matching
    # the one the original render used.
    category = (ship_category(ship) if ship.get("_raw", {}).get("Ship type")
                else SHIP_FOLDERS.get(entry.get("shipType"), UNCATEGORIZED_SHIP))
    callsign = entry.get("callsign", "-")
    folder = Path(folder_path)
    stem = _safe(ship["name"])
    slug = art._slug(ship["name"])

    print("regenerating %s  \"%s\"  seed=%d  %s (%dx%d hexes) -> %s"
          % (ship["name"], callsign, seed, band,
             TOKEN_GRID[band][0], TOKEN_GRID[band][1], folder))

    template, slots = load_workflow(args)
    post_template = post_slots = None
    if not args.no_token:
        post_template, post_slots = load_post_workflow(args)

    comfy = art.find_server(args.server)
    print("ComfyUI: %s" % comfy.base)

    def render(prompt, stage, size):
        knobs = Knobs(args, size, COMFY_PREFIX)
        job = art.build_job(template, slots, entry_for(category, slug, stage, prompt), seed, knobs)
        record = comfy.wait(comfy.queue(job), timeout=args.timeout)
        images = comfy.images(record)
        if not images:
            raise RuntimeError("the %s job produced no image" % stage)
        return images

    def remove_background(image):
        # The token's real size, not a constant. build_post_job() reads nothing
        # off the knobs it is handed, so this is inert today - which is exactly
        # why the NPC script gets away with passing its fixed TOKEN_SIZE here.
        # Passing the real one costs nothing and means the day a post workflow
        # does read a size, the five-hex carrier is not the thing that finds
        # out.
        knobs = Knobs(args, tok_size, COMFY_PREFIX)
        prefix = "%s/%s/%s/token_rmbg" % (COMFY_PREFIX, category, slug)
        job = art.build_post_job(
            post_template, post_slots, art.image_ref(image), prefix, seed, knobs)
        record = comfy.wait(comfy.queue(job), timeout=args.timeout)
        images = comfy.images(record)
        if not images:
            raise RuntimeError("background removal produced no image")
        return images[0]

    folder.mkdir(parents=True, exist_ok=True)
    written = list(entry.get("files", []))
    portrait_file = entry.get("portrait")
    token_file = entry.get("token")

    try:
        if not args.no_portrait:
            print("    portrait ...", flush=True)
            image = render(portrait_prompt, "portrait", PORTRAIT_SIZE)[0]
            portrait_file = fetch(comfy, image, folder / ("%s Portrait.png" % stem)).name
            if portrait_file not in written:
                written.append(portrait_file)
            print("      -> %s" % portrait_file)
            time.sleep(args.pause)

        if not args.no_token:
            print("    token %dx%d ..." % tok_size, flush=True)
            raw = render(token_prompt, "token", tok_size)[0]
            if args.keep_raw_token:
                raw_file = fetch(comfy, raw, folder / ("%s Token (raw).png" % stem)).name
                if raw_file not in written:
                    written.append(raw_file)
            time.sleep(args.pause)
            print("      + background removal", flush=True)
            cut = remove_background(raw)
            token_file = fetch(comfy, cut, folder / ("%s Token.png" % stem)).name
            if token_file not in written:
                written.append(token_file)
            print("      -> %s" % token_file)
            time.sleep(args.pause)
    except KeyboardInterrupt:
        print("\ninterrupted - cancelling the running job")
        comfy.cancel_all()
        return 130

    dossier = folder / ("%s.md" % stem)
    write_ship_dossier(dossier, ship, seed, prompts, written, callsign, band, args.max_token_px)
    if dossier.name not in written:
        written.append(dossier.name)

    entry["seed"] = seed
    entry["files"] = written
    entry["portrait"] = portrait_file
    entry["portraitPrompt"] = portrait_prompt
    entry["token"] = token_file
    entry["tokenPrompt"] = token_prompt
    # Unconditionally, unlike generate-npc.py:4273-4280, which writes them only
    # when `rerolled is not None`. That gate is a bug over there: `rerolled` is
    # assigned on the --reroll-trait path alone, so a --set-trait regen renders
    # the new value and never persists it, and the GUI's /api/set-trait shows
    # the old traits after a successful set. Writing on both paths costs a
    # manifest key rewrite on a plain regen - where the values are identical -
    # and cannot leave traits and rawTraits describing different ships.
    persist_traits(entry, ship)
    persist_size(entry, ship, args.max_token_px)
    entry["when"] = time.strftime("%Y-%m-%d %H:%M:%S")
    # A real render brings the art back in line with the traits. Popped rather
    # than set False so an entry that never staged anything stays identical to
    # what earlier versions wrote. Popped even for --no-portrait/--no-token: a
    # partial render is the user explicitly asking for one stage, and leaving
    # the marker up would nag about art they chose not to remake.
    entry.pop("artStale", None)
    manifest[folder_path] = entry
    art.save_manifest(args.regen_manifest, manifest)

    print("done: %s" % folder)
    return 0


# ---------------------------------------------------------------------------
# The roll -> render run
# ---------------------------------------------------------------------------


def resolve_forced_bullets(tables, args, seed):
    """--ship-type / --size as the verbatim bullets roll_ship() takes overrides in.

    Both flags name a FLAG - a SHIP_TYPES slug, a SIZE_BANDS band - and
    roll_ship()'s override path takes bullets, because a pinned bullet is what
    carries the flags its dependents filter on. Resolving here rather than
    adding a second forcing channel to the roller keeps one mechanism: a
    --size huge resolved to a Size bullet trips the roller's own forced-band
    reverse gate and narrows '## Ship type' to slugs that reach five hexes,
    which is exactly what a hand-written --set-trait Size= already does.

    Drawn per ship rather than once for the batch, so `--count 5 --ship-type
    carrier` gets the table's several phrasings of "carrier" instead of the
    same sentence five times.

    The draw runs on a stream of its own, seeded from a string rather than from
    seed+N. Sharing the roll's own rng would make the ship a caller of
    --ship-type rolled differently from the same ship rolled without it even
    where the type came out the same; a nearby integer seed would collide with
    another ship's roll stream in a large batch. A string cannot do either.
    """
    forced = {}
    picker = random.Random("%d/forced" % seed)
    for flag, table, matches in (
            (args.ship_type, "Ship type",
             lambda b, want: sp.ship_type_of(b) == want),
            (args.size, "Size",
             lambda b, want: sp.size_of(b) == want)):
        if not flag:
            continue
        pool = [b for b in tables.get(table, []) if matches(b, flag)]
        if not pool:
            raise SystemExit(
                "no '## %s' bullet in %s carries %r. The tables file and "
                "ship_policy.py disagree about what exists; --ship-catalogue "
                "lists what this script believes in."
                % (table, args.tables.name, flag))
        forced[table] = picker.choice(pool)
    return forced


def dry_run_report(args, rolled):
    """--dry-run: what would be rolled and rendered, human-readable on stdout.

    Mirrors generate-npc.py's, plus the two things a ship has and an NPC does
    not: the size band with its grid footprint, and a token canvas that differs
    per ship. Both are printed next to the prompt they shaped, because the
    failure this report exists to catch is a five-hex carrier whose token
    prompt says "half again as long as it is broad" over a 1024x1024 latent.
    """
    for seed, ship, callsign, prompts in rolled:
        portrait_prompt, token_prompt = prompts
        band = band_of(ship)
        grid_w, grid_h = TOKEN_GRID[band]
        print("\n  %s  \"%s\"  (seed %d)" % (ship["name"], callsign, seed))
        print("    %s, %s" % (type_name_of(ship), split_faction(ship["Faction"])[0]))
        print("    %s hull, %d x %d hexes" % (band, grid_w, grid_h))
        print("    -> %s" % asset_folder(args.out, ship["name"],
                                         ship_category(ship), args.overwrite))
        print("    workflow %s" % args.workflow.name)
        if not args.no_portrait:
            print("    portrait %dx%d ~%d tok:"
                  % (PORTRAIT_SIZE + (estimate_tokens(portrait_prompt),)))
            print("        %s" % portrait_prompt)
        if not args.no_token:
            print("    token    %dx%d ~%d tok:"
                  % (token_size(band, args.max_token_px)
                     + (estimate_tokens(token_prompt),)))
            print("        %s" % token_prompt)
    stages = (0 if args.no_portrait else 1) + (0 if args.no_token else 2)
    print("\ndry run OK - %d job(s) would be queued" % (len(rolled) * stages))
    return 0


def dry_run_json(args, rolled):
    """--dry-run --json: the same run as a machine-readable object on stdout.

    Exists because the create path in the GUI learns what a run produced by
    diffing manifest folder keys, which is only possible after the render - so
    a preview needs a channel of its own. Every human-readable line has already
    gone to stderr by the time this is called; stdout carries this and nothing
    else.
    """
    ships = []
    for seed, ship, callsign, (portrait_prompt, token_prompt) in rolled:
        band = band_of(ship)
        ships.append(dict(
            {
                "name": ship["name"],
                "callsign": callsign,
                "seed": seed,
                "id": ship_id(ship["name"], seed),
                "shipType": ship_type_of(ship),
            },
            **token_metadata(band, args.max_token_px),
            **{
                "folder": str(asset_folder(args.out, ship["name"],
                                           ship_category(ship), args.overwrite)),
                "traits": {k: v for k, v in ship.items() if not k.startswith("_")},
                "rawTraits": dict(ship["_raw"]),
                "portraitPrompt": portrait_prompt,
                "portraitTokens": estimate_tokens(portrait_prompt),
                "tokenPrompt": token_prompt,
                "tokenTokens": estimate_tokens(token_prompt),
            }))
    json.dump({"ships": ships}, sys.stdout)
    return 0


def manifest_entry(ship, seed, callsign, band, args, written,
                   portrait_file, portrait_prompt, token_file, token_prompt):
    """One .generated-npcs.json entry for a finished ship.

    Shares the file with the NPCs, so `kind` is what tells them apart and the
    GUI groups on it. Everything its item view reads is here: id, kind, name,
    callsign, traits, seed, when, portrait, token, portraitPrompt, tokenPrompt,
    rawTraits - and its manifest reader SKIPS any entry without an `id`, which
    is why that is written first and unconditionally.

    The five size fields are integers in GRID UNITS for gridWidth/gridHeight
    and pixels for tokenWidth/tokenHeight, and the distinction is the one thing
    a reader of this entry has to get right: Foundry's token.width is a hex
    count, not a pixel count, and a 1728 in it would draw a cruiser across a
    map the size of a continent.

    Ship entries deliberately carry NONE of the NPC's derived booleans. Every
    ship pairing is rebuildable from rawTraits, because ship_policy filters on
    the bullets' own flags rather than on a flag-stripped value.
    """
    return dict(
        {
            # First and unconditional, because the GUI's manifest reader SKIPS
            # any entry without one - a ship missing this key would render, be
            # written, and never appear in the grid.
            "id": ship_id(ship["name"], seed),
            "kind": "spaceship",
            "name": ship["name"],
            "callsign": callsign,
            "seed": seed,
            "tables": str(args.tables),
            "workflow": str(args.workflow),
            "traits": {k: v for k, v in ship.items() if not k.startswith("_")},
            # _raw is dropped by the comprehension above along with every other
            # '_'-prefixed key, so it has to be written out explicitly here to
            # survive at all. It is the bullets traits was built from, flags
            # and all - traits alone has already lost the type slug off a Ship
            # type and the band off a Size, which the whole equipment matrix
            # filters on, so a --reroll-trait against a stored ship needs this
            # to see what its sibling traits actually require.
            "rawTraits": dict(ship["_raw"]),
            "shipType": ship_type_of(ship),
        },
        **token_metadata(band, args.max_token_px),
        **{
            "files": written,
            "portrait": portrait_file,
            "portraitPrompt": portrait_prompt,
            "token": token_file,
            "tokenPrompt": token_prompt,
            "dossier": "%s.md" % _safe(ship["name"]),
            "when": time.strftime("%Y-%m-%d %H:%M:%S"),
        })


def main(argv=None):
    args = parse_args(argv)

    # Before anything that reads the tables for real. This mode answers out of
    # ship_policy.py and exits.
    if args.ship_catalogue:
        return print_ship_catalogue(args)

    # Before regenerate_one(), which renders. This mode only reports.
    if args.trait_choices:
        return print_trait_choices(args)

    if args.regen_manifest:
        return regenerate_one(args)

    if not args.tables.exists():
        raise SystemExit("Tables file not found: %s" % args.tables)
    tables = parse_tables(args.tables)
    check_tables(tables, args.tables, getattr(parse_tables, "repeated", ()))

    # Before anything that prints, seeds or picks a folder. The caller parses
    # stdout whole, so one stray line of the run banner below would break it.
    if args.trait_odds:
        rng = random.Random(args.seed) if args.seed is not None else random.Random()
        json.dump({"samples": args.trait_odds,
                   "tables": ship_trait_odds(tables, args.trait_odds, rng)},
                  sys.stdout)
        return 0

    unknown = [t for t in args.overrides if t not in REQUIRED_TABLES and t != "name"]
    if unknown:
        raise SystemExit(
            "--set-trait: unknown table(s) %s. Known: %s"
            % (", ".join(unknown), ", ".join(REQUIRED_TABLES))
        )

    # Same check, same shape, for the mistake generate-npc.py:4423-4437
    # describes: a forced Theme the table doesn't offer used to resolve in
    # silence to an all-neutral roll. The empty string is the sharper case - it
    # is falsy, so the roller rolls a real theme and filters every themed pool
    # with it, and then the override pass pastes the empty value back over the
    # record. The dossier would report no theme for a ship that was themed,
    # contradicting the line it prints promising this seed reproduces it.
    if "Theme" in args.overrides:
        known = sorted(set(tables["Theme"]))
        if args.overrides["Theme"] not in known:
            raise SystemExit(
                "--theme %r: no such theme in the Theme table. Available: %s"
                % (args.overrides["Theme"], ", ".join(known))
            )

    # --dry-run --json puts the whole human report on stderr, because its
    # caller parses stdout whole. `out` is every print below that is not JSON.
    out = (lambda *a, **k: print(*a, file=sys.stderr, **k)) if args.json else print

    base_seed = args.seed if args.seed is not None else random.randint(0, 2 ** 32 - 1)

    rolled = []
    for n in range(args.count):
        seed = base_seed + n
        overrides = dict(args.overrides)
        overrides.update(resolve_forced_bullets(tables, args, seed))
        if args.name:
            overrides["name"] = args.name
        ship = roll_ship(tables, random.Random(seed), overrides)
        # A hull code is a serial rather than a table roll, so it comes from a
        # stream of its own for the reason resolve_forced_bullets() gives about
        # its own: a code drawn off the ship's rng would make every trait after
        # it move if the code's shape ever changed. Taken off the ship dict
        # first, so that a roller half which decides to roll one itself wins
        # over this one rather than silently disagreeing with it.
        callsign = ship.get("callsign") or hull_code(random.Random("%d/hull" % seed))
        rolled.append((seed, ship, callsign, build_ship_prompts(ship)))

    out("%s: %d tables, %d ship(s) rolled from base seed %d"
        % (args.tables.name, len(tables), args.count, base_seed))
    out("output root: %s" % args.out)

    if args.dry_run:
        if args.json:
            return dry_run_json(args, rolled)
        return dry_run_report(args, rolled)

    template, slots = load_workflow(args)
    post_template = post_slots = None
    if not args.no_token:
        post_template, post_slots = load_post_workflow(args)

    comfy = art.find_server(args.server)
    print("ComfyUI: %s" % comfy.base)
    manifest = art.load_manifest(args.manifest)

    def render(prompt, category, slug, stage, size, seed):
        """Queue one text -> image job and return the images it produced."""
        knobs = Knobs(args, size, COMFY_PREFIX)
        job = art.build_job(template, slots, entry_for(category, slug, stage, prompt), seed, knobs)
        record = comfy.wait(comfy.queue(job), timeout=args.timeout)
        images = comfy.images(record)
        if not images:
            raise RuntimeError("the %s job produced no image" % stage)
        return images

    def remove_background(image, category, slug, size, seed):
        knobs = Knobs(args, size, COMFY_PREFIX)
        prefix = "%s/%s/%s/token_rmbg" % (COMFY_PREFIX, category, slug)
        job = art.build_post_job(
            post_template, post_slots, art.image_ref(image), prefix, seed, knobs)
        record = comfy.wait(comfy.queue(job), timeout=args.timeout)
        images = comfy.images(record)
        if not images:
            raise RuntimeError("background removal produced no image")
        return images[0]

    done = failed = 0
    started = time.time()

    for index, (seed, ship, callsign, prompts) in enumerate(rolled, 1):
        portrait_prompt, token_prompt = prompts
        band = band_of(ship)
        tok_size = token_size(band, args.max_token_px)
        category = ship_category(ship)
        folder = asset_folder(args.out, ship["name"], category, args.overwrite)
        slug = art._slug(ship["name"])
        stem = _safe(ship["name"])
        tag = "[%d/%d]" % (index, len(rolled))

        print("\n%s %s  \"%s\"  seed=%d" % (tag, ship["name"], callsign, seed))
        print("    %s, %s" % (type_name_of(ship), split_faction(ship["Faction"])[0]))
        print("    %s hull, %d x %d hexes" % ((band,) + TOKEN_GRID[band]))

        written = []
        portrait_file = token_file = None
        try:
            folder.mkdir(parents=True, exist_ok=True)

            if not args.no_portrait:
                print("    portrait ...", flush=True)
                image = render(portrait_prompt, category, slug, "portrait",
                               PORTRAIT_SIZE, seed)[0]
                portrait_file = fetch(comfy, image, folder / ("%s Portrait.png" % stem)).name
                written.append(portrait_file)
                print("      -> %s" % written[-1])
                time.sleep(args.pause)

            if not args.no_token:
                print("    token %dx%d ..." % tok_size, flush=True)
                raw = render(token_prompt, category, slug, "token", tok_size, seed)[0]
                if args.keep_raw_token:
                    written.append(
                        fetch(comfy, raw, folder / ("%s Token (raw).png" % stem)).name)
                time.sleep(args.pause)
                print("      + background removal", flush=True)
                cut = remove_background(raw, category, slug, tok_size, seed)
                token_file = fetch(comfy, cut, folder / ("%s Token.png" % stem)).name
                written.append(token_file)
                print("      -> %s" % written[-1])
                time.sleep(args.pause)

        except KeyboardInterrupt:
            print("\ninterrupted - cancelling the running job and clearing the queue")
            comfy.cancel_all()
            art.save_manifest(args.manifest, manifest)
            return 130
        except Exception as exc:
            failed += 1
            print("    ! %s" % exc, file=sys.stderr)
            continue

        dossier = folder / ("%s.md" % stem)
        write_ship_dossier(dossier, ship, seed, prompts, written, callsign, band,
                           args.max_token_px)
        written.append(dossier.name)
        print("    -> %s" % folder)

        done += 1
        manifest[str(folder)] = manifest_entry(
            ship, seed, callsign, band, args, written,
            portrait_file, portrait_prompt, token_file, token_prompt)
        art.save_manifest(args.manifest, manifest)

    print("\n%d ship(s) in %.1fs%s"
          % (done, time.time() - started, ", %d failed" % failed if failed else ""))
    print("manifest: %s" % args.manifest)
    return 1 if failed and not done else 0


if __name__ == "__main__":
    sys.exit(main())