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
#
# ---------------------------------------------------------------------------
# FOLD NOTE - read before merging this into generate-spaceship.py
# ---------------------------------------------------------------------------
# This file is the render/output/CLI half of generate-spaceship.py, written
# separately from the roller/prompt-builder half (_ship_roll.py) so the two
# could be authored in parallel. It is a working module on its own: it imports
# the four names the other half exports and nothing else of it.
#
# When the two are folded into one generate-spaceship.py:
#   * keep ONE copy of the bootstrap block (_load_art/_load_npc, `art`, `npc`,
#     `import ship_policy as sp`) and ONE copy of the borrowed-surface aliases;
#   * delete the `from _ship_roll import ...` line - those four names become
#     definitions in the same module;
#   * REQUIRED_TABLES must survive as a literal top-level assignment at column
#     0 (the import GUI regex-parses it out of the source text), which is why
#     it is imported here rather than re-declared: the other half declares it
#     in the shape lib/overrideTables.js matches, and two copies could drift;
#   * TRAIT_DEPENDENTS, PLAN_FRAMING and trait_cascade() are declared HERE. If
#     the other half also declares them, keep exactly one copy and diff the two
#     first - a silently-merged pair of near-identical dependency maps is the
#     one merge error neither test suite would catch.
# ---------------------------------------------------------------------------

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


def _load_module(filename, name):
    """Import a hyphenated sibling script by file location.

    The hyphen keeps generate-art.py and generate-npc.py off the normal import
    path, and renaming either would invalidate every README, docstring and
    shell history that names them - so load them the way they load each other.
    Identical to generate-npc.py:77-97 and generate-3d.py:1452, register-then-
    exec included: @dataclass resolves annotations through
    sys.modules[cls.__module__], so the module has to be in sys.modules before
    its body runs, not after.
    """
    path = SCRIPT_DIR / filename
    if not path.exists():
        raise SystemExit("%s not found next to this script (%s)" % (filename, SCRIPT_DIR))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


art = _load_module("generate-art.py", "lancer_generate_art")
npc = _load_module("generate-npc.py", "lancer_generate_npc")

import ship_policy as sp  # noqa: E402  - after the by-path loads, on purpose

# The borrowed surface, bound once here so every use site is one grep away and
# so an NPC-side rename fails at import rather than three hundred lines into a
# render. test/test_shared_surface.py pins this list by name; nothing else off
# `npc` may be referenced, because everything else on it is about a person.
parse_tables = npc.parse_tables
variant_table = npc.variant_table          # ships pass the SIZE BAND as the key
heading_for = npc.heading_for              # ... and so does its inverse
split_flags = npc.split_flags
split_backdrop = npc.split_backdrop
split_faction = npc.split_faction
estimate_tokens = npc.estimate_tokens
TOKEN_LIMIT = npc.TOKEN_LIMIT
CHARS_PER_TOKEN = npc.CHARS_PER_TOKEN
Knobs = npc.Knobs
entry_for = npc.entry_for
fetch = npc.fetch
_safe = npc._safe
next_run_folder = npc.next_run_folder
asset_folder = npc.npc_folder              # <root>/<category>/<Name>/, suffixed

# The roller/prompt half. roll_ship() has roll_npc()'s signature and contract
# (an ordered draw over REQUIRED_TABLES, a `probe` that records each table's
# filtered pool and is otherwise inert, forced overrides replacing the draw,
# raw bullets under '_raw'); build_ship_prompts() returns the (portrait, token)
# pair build_prompts() does. Its fourth export, ship_fields(), is
# pronoun_fields()' replacement and is consumed inside build_ship_prompts() -
# nothing on this side of the file has a use for it, so it is not imported
# here rather than imported and left unreferenced.
from _ship_roll import (  # noqa: E402
    REQUIRED_TABLES,
    build_ship_prompts,
    roll_ship,
)


# ---------------------------------------------------------------------------
# Token sizing
# ---------------------------------------------------------------------------

# Portrait: one size for every hull. Deliberately landscape where the NPC's is
# square (generate-npc.py:1109) - a ship in a scene is a landscape composition,
# and every '## Backdrop' bullet in the tables file is written as one.
PORTRAIT_SIZE = (1216, 832)          # 3:2, 1.01 MP, both dims a multiple of 64

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
    """
    gw, gh = TOKEN_GRID[band]
    px = TOKEN_PX_PER_HEX[band]
    w, h = gw * px, gh * px
    if w * h > max_px:
        scale = (max_px / (w * h)) ** 0.5
        w, h = (max(64, int(v * scale) // 64 * 64) for v in (w, h))
    return w, h


# The token prompt's {plan} slot: the hull's proportions, asserted in words as
# well as in the latent's aspect.
#
# At CFG 1.0 the latent shape alone does not stop the model anchoring the hull
# at portrait scale and cropping the stern - the same failure generate-npc.py
# :1148-1155 documents for the NPC token's feet, where "full body" lost to the
# detail the rest of the prompt asked for and the boots went off the bottom.
#
# {plan} states FRAMING only. Scale is the rolled '## Size' bullet's job - it
# names the number ("about forty metres bow to stern") - and keeping the two
# apart is why a Size bullet is not allowed to say "huge".
PLAN_FRAMING = {
    "small": "the whole hull roughly as long as it is wide across the wings",
    "medium": "a lean hull about twice as long as it is wide",
    "large": "a long hull about half again as long as it is broad",
    "huge": "a vast hull filling the frame bow to stern, half again as long "
            "as it is broad",
}


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


# ---------------------------------------------------------------------------
# The dependency map, and what a re-roll of one trait takes with it
# ---------------------------------------------------------------------------

# Which traits a re-roll of each one invalidates. Every key of
# RAW_REROLLABLE_TRAITS must appear - '()' for a leaf - or trait_cascade()
# raises on it, which is deliberate: a missing key would close to an empty
# tuple and pin the whole ship, reporting a re-roll that changed nothing.
#
# Declared as a literal top-level assignment at column 0 because the import
# GUI's lib/overrideTables.js regex-parses this file's SOURCE TEXT with a
# ^TRAIT_DEPENDENTS\s*=\s*\{ ... newline-} pattern. Building it from a
# comprehension would be equivalent Python and invisible to the GUI.
#
# Four edges here are wider than the design doc's §3(c) lists, and every one
# of them is a filter roll_ship() actually runs that the doc was written
# before: '## Hull' bullets carry the type slug and are filtered on it, the
# scene table carries 'max-' size caps so a five-hex hull cannot roll an
# enclosed berth, and ship_policy.filter_by_gates() gates a '## Glow
# placement' on whether the Weapon/Launch catapult it lights came back fitted
# at all. A map narrower than the filters is the failure this map exists to
# prevent: re-roll the Weapon to the 'none' bullet with a pinned placement and
# the glow gathers at the muzzles of guns that are no longer drawn - which
# routes around the policy lock in the one direction the lock cannot see.
TRAIT_DEPENDENTS = {
    # Selection by theme rather than by a flag read, which is why this one
    # edge points at a whole tuple.
    "Theme": ("Hull", "Detail", "Weapon", "Command bridge", "Backdrop"),
    # The widest edge in the map, and the one that earns the roll order. The
    # slug keys EQUIPMENT_POLICY, so all four equipment tables are filtered on
    # it; sizes_for() gates Size; '## Hull' bullets carry the slug; and the
    # bullet's own civ/mil register is what filter_by_mil() reads for Faction,
    # Detail and Markings. A freed Ship type that kept its Launch catapult is
    # the brief's own prohibition arriving through the one path that skips
    # the lock.
    "Ship type": ("Size", "Faction", "Hull", "Detail", "Weapon",
                  "Shield generator", "Launch catapult", "Command bridge",
                  "Markings"),
    # The band is the second half of every hardware filter - filter_by_size()
    # is a hard floor and ceiling, LIGHT_CAP is read off it - and half of the
    # Hull filter too. Backdrop is here for the 'max-' cap the scene table
    # carries: an enclosed commercial berth is a room a five-hex hull does not
    # fit inside.
    "Size": ("Hull", "Weapon", "Shield generator", "Launch catapult",
             "Command bridge", "Backdrop"),
    # Not a flag edge but a content one: the Faction visual and the Markings
    # bullet both describe painted-on identity, and a new operator whose old
    # stencilling is still on the hull reads as a mistake.
    "Faction": ("Markings",),
    # The silhouette gates the fittings that sit on it - Detail hangs off the
    # shape the Hull bullet just described, and a bridge is silhouette rather
    # than payload.
    "Hull": ("Detail", "Command bridge"),
    "Detail": (),
    "Weapon": ("Glow placement",),
    # Shield generator carries a second edge on top of the gate, and it is the
    # ship's version of the NPC's 'Backdrop -> Glow colour'. A shield emitter
    # is authored with glow/lit/readout vocabulary so has_light_source() reads
    # it, and it is the commonest fitted light on a hull - so re-rolling it to
    # the 'none' bullet can take away the only thing that motivated a
    # saturated colour being named at all.
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


def trait_cascade(name):
    """`name` plus every trait a re-roll of it invalidates, transitively.

    generate-npc.py:305-362 with the ship map substituted. Copied rather than
    borrowed because that one closes over the NPC module's own
    TRAIT_DEPENDENTS and orders by the NPC REQUIRED_TABLES; there is nothing
    else in it to parameterise.

    Written as a worklist over a `seen` set rather than as a recursive walk,
    because the map is not promised to be acyclic and this must not depend on
    it - the NPC map held a cycle until recently (Age/Build, filtered in both
    directions), and the next filter audited both ways here will put one back.
    Nothing is enqueued twice, so the walk terminates on a cycle rather than
    recurring forever. Do not replace it with a recursion that assumes a DAG.

    Ordered by REQUIRED_TABLES rather than by discovery order, so a cascade can
    never disagree with the order the roller draws in.

    An unknown name raises rather than closing to (). A caller hands the result
    straight to reroll_from_raw() as its free set, so a typo would pin every
    trait and re-roll nothing - a silent no-op wearing the name of a re-roll,
    which is the exact failure this map exists to prevent.
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


def check_tables(tables, path, repeated=()):
    """Refuse a tables file the prompt templates cannot be built from.

    generate-npc.py:1271-1282 with this module's REQUIRED_TABLES, which is the
    single line that made a copy necessary - that one reads its own module
    global.
    """
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


# Which traits --reroll-trait accepts. Ships have recorded their raw bullets
# since their first entry ever written, so unlike the NPC script there is no
# lossy fallback path and no shorter list for entries that predate it - both
# names below hold the same sixteen traits.
#
# REROLLABLE_TRAITS is spelled out as a literal multi-line tuple rather than
# aliased to the line below it, and that is not redundancy. The import GUI's
# lib/overrideTables.js reads this file's source text and needs bullet-shaped
# content between the parens; an alias, or an empty tuple, would parse to
# nothing and the GUI would hide every re-roll button on this generator on
# what is really a regex quirk.
REROLLABLE_TRAITS = (
    "Theme", "Ship type", "Size", "Faction", "Hull", "Detail", "Weapon",
    "Shield generator", "Launch catapult", "Command bridge", "Markings",
    "Condition", "Backdrop", "Weather", "Glow colour", "Glow placement",
)

# Derived from REQUIRED_TABLES by exclusion rather than written out, so a table
# added there next month is re-rollable the day it is added rather than the day
# somebody remembers this line. The two it excludes are refused for a reason
# raw bullets do not touch: both halves of the name decide the ship's folder
# and its manifest id, so re-rolling either is not a change in place.
RAW_REROLLABLE_TRAITS = tuple(
    name for name in REQUIRED_TABLES
    if name not in ("Name prefixes", "Ship names"))

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


def default_root():
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
    # --out is generate-npc.py's spelling and --out-root the one the GUI's ship
    # job builder uses; aliased for the same reason --ship-type is.
    out.add_argument("--out", "--out-root", dest="out", type=Path, default=None,
                     help="root to write ship folders into (default: a fresh runN "
                          "folder under %s, so a batch can be reviewed before any "
                          "of it is moved into Foundry by hand; passed explicitly, "
                          "the path is used as-is with no runN folder inserted)"
                          % DEFAULT_OUTPUT_ROOT)
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
        args.out = next_run_folder(default_root())

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
