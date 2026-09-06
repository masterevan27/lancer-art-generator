#!/usr/bin/env python3
"""Roll random human NPCs and generate their Foundry portrait + token art.

Companion to generate-art.py. That script walks an authored art-prompt markdown
file and renders every prompt in it; this one has no authored corpus - it rolls
a person out of the tables in

    prompts/npc-generator-tables.md

composes a matched pair of prompts in the campaign's house style, and renders
both through a ComfyUI workflow - the one generate-art.py uses, unless the NPC's
gender selects its own (see GENDER_WORKFLOWS). All the ComfyUI plumbing - server
discovery, workflow slot detection, job building, the RMBG post pass - is
imported from generate-art.py rather than reimplemented.

Each NPC lands in its own folder, nested under a category folder for their
rolled Role (see ROLE_CATEGORIES), under a fresh numbered run folder in the
output root - by default ComfyUI's own output tree, *not* the Foundry token
root, so a batch can be looked over before any of it is decided worth keeping:

    <root>/run1/Soldiers/Nadia Okonkwo/Nadia Okonkwo Portrait.png   1024x1024, opaque
    <root>/run1/Soldiers/Nadia Okonkwo/Nadia Okonkwo Token.png      transparent, RMBG'd
    <root>/run1/Soldiers/Nadia Okonkwo/Nadia Okonkwo.md             the rolled dossier

Each invocation gets the next unused runN folder (run1, run2, ...) under the
output root, so successive batches never collide. Moving a keeper into the
live Foundry token tree is a manual step - pass --out to point a run straight
at it instead, if that's ever wanted.

The portrait deliberately skips background removal - it wants its blurred
backdrop - so the two images take different paths through the same workflow
rather than sharing one --post chain.

Stdlib only, same as generate-art.py. Run with --dry-run first.

Examples:
  python generate-npc.py --dry-run
  python generate-npc.py                        # one NPC
  python generate-npc.py --count 5
  python generate-npc.py --seed 1234            # reproducible roll
  python generate-npc.py --count 5 --pronouns she   # women only
  python generate-npc.py --workflow-woman "$(pwd)/wf.json"   # override their default
  python generate-npc.py --name "Ivo Karras" --set-trait Role="a smuggler"

  # Re-render one already-rolled NPC exactly, or with a fresh seed - the
  # traits (and so the prompt) come from the manifest either way, not a roll:
  python generate-npc.py --regen-manifest .generated-npcs.json --regen-id npc-Nadia-Okonkwo-1234
  python generate-npc.py --regen-manifest .generated-npcs.json --regen-id npc-Nadia-Okonkwo-1234 \\
      --new-seed 5678 --no-token

  # Ask which values one trait could take on that NPC (JSON on stdout, no
  # render), then pin the one you want and re-render with everything else kept:
  python generate-npc.py --regen-manifest .generated-npcs.json --regen-id npc-Nadia-Okonkwo-1234 \\
      --trait-choices Outfit
  python generate-npc.py --regen-manifest .generated-npcs.json --regen-id npc-Nadia-Okonkwo-1234 \\
      --set-trait Outfit="an elaborate floral kimono ... || civ notac" --release Headgear
"""

from __future__ import annotations

import argparse
import functools
import importlib.util
import json
import math
import os
import random
import re
import sys
import time
import urllib.parse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _load_generator():
    """Import generate-art.py.

    The hyphen keeps it off the normal import path, and renaming it would
    invalidate every README, docstring and shell history that names it, so
    load it by file location instead.
    """
    path = SCRIPT_DIR / "generate-art.py"
    if not path.exists():
        raise SystemExit("generate-art.py not found next to this script (%s)" % SCRIPT_DIR)
    name = "lancer_generate_art"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    # @dataclass resolves annotations through sys.modules[cls.__module__], so
    # the module has to be registered before its body runs, not after.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


art = _load_generator()

DEFAULT_TABLES = SCRIPT_DIR / "prompts" / "npc-generator-tables.md"
DEFAULT_MANIFEST = SCRIPT_DIR / ".generated-npcs.json"

# Where ComfyUI's own output folder collects the raw renders, and also this
# script's default staging root - a review copy lands here under its own
# runN folder rather than going straight into the Foundry token tree, so a
# batch can be eyeballed before any of it is promoted there by hand.
COMFY_PREFIX = "LancerNPCs"
# ComfyUI's output folder. Set COMFYUI_OUTPUT_DIR to point at a ComfyUI
# install elsewhere; otherwise fall back to an output/ folder beside this
# script, so a fresh clone works without configuration.
_OUTPUT_ROOT = os.environ.get("COMFYUI_OUTPUT_DIR")
DEFAULT_OUTPUT_ROOT = (Path(_OUTPUT_ROOT) if _OUTPUT_ROOT else SCRIPT_DIR / "output") / COMFY_PREFIX

# Tables the prompt templates below require. Anything else in the markdown file
# is ignored, so extra tables can be added for reference without breaking this.
#
# The ORDER is load-bearing in five places, and roll_npc() reads each flag off
# the earlier table on the assumption that it has already been rolled: Age
# before Build ('figure'), Age before Hair colour ('older'), Role before
# Faction, Outfit and Weapon, Outfit before Weapon and Gear (the 'notac'
# strip), and Weapon before Gear and Stance (the 'hands' collision with Gear,
# and the 'none' flag that gates Stance alongside 'gun'). Each is explained at
# its own use site in roll_npc() rather than restated here; reorder this list
# without reading those five comments and the filter each one describes goes
# quietly dead.
REQUIRED_TABLES = [
    "Given names", "Family names", "Callsigns", "Pronouns", "Theme", "Age",
    "Build", "Height", "Skin", "Hair", "Hair colour", "Eyes", "Feature",
    "Demeanor", "Role",
    "Faction", "Outfit", "Headgear", "Weapon", "Gear", "Glow colour", "Backdrop",
    "Glow placement", "Weather", "Stance",
]

# The tables a rolled Theme gates. Everything else - names, age, build, height,
# skin, eyes, glow colour, weather, stance - describes the person or the moment
# rather than the visual world they come from, and stays untouched by theme.
# Gear is deliberately absent: what is left of it after the Weapon split is
# data-slates, tool bags and thermoses, which no theme owns. Weapon is here
# because armament is the most theme-defining object a figure carries. Hair
# colour is here beside the cut: a theme that owns a silhouette owns its
# palette too, and a colour tagged for one theme should be as unreachable from
# another as a hairstyle is.
THEMED_TABLES = ("Hair", "Hair colour", "Feature", "Outfit", "Headgear",
                 "Weapon", "Backdrop")

# Which traits a re-roll of one trait invalidates: "re-roll this and these stop
# being answers the roller could have given". The map exists because a pinned
# re-roll only filters in one direction. reroll_from_raw() pins every trait but
# the target and lets roll_npc() draw the rest, so the freed trait is filtered
# against everything pinned - but a pinned trait is never drawn, so not one
# filter runs on it, and nothing re-checks it against the value that just
# changed. Free the Role alone and the kept Faction lands on the wrong side of
# the civ/mil split 138 times in 400 on the live tables: a colonial
# administrator flying a marine corps banner, which is precisely the pairing
# filter_by_mil() exists to stop, arriving through the one path that skips it.
# The cure is to free the dependents along with the target, and this is the
# list of them.
#
# The reason differs per edge and each one is named below, because those
# reasons are what a later reader has to check this map against. A filter that
# moves, or a flag that stops being read, leaves an edge here asserting a
# constraint the roller no longer applies, and the map cannot notice that by
# itself.
TRAIT_DEPENDENTS = {
    # Selection by theme rather than a flag read, which is why this single
    # edge points at a whole tuple: filter_by_theme() and apply_theme_share()
    # choose each of these tables' bullets by the rolled theme, so under a new
    # theme the old bullets are ones the roll could not have produced. Derived
    # from THEMED_TABLES rather than typed out, so a table tagged for theming
    # next month cascades the day it is added rather than the day somebody
    # remembers this line - the same property REQUIRED_TABLES buys elsewhere
    # in this file.
    "Theme": THEMED_TABLES,

    # All three read Role's 'mil' flag: Faction and Outfit through
    # filter_by_mil(), Weapon through apply_weapon_policy(), which also reads
    # the rolled Role's ROLE_CATEGORIES entry to decide what a soldier is
    # guaranteed to be carrying. Outfit reads Role a second way as well,
    # through filter_by_dress() and the policy dress_policy_for() derives from
    # that same category - a dockworker is not entitled to a ceremonial robe.
    "Role": ("Faction", "Outfit", "Weapon"),

    # All three read Outfit's 'notac'. Weapon and Gear lose their
    # military-issue bullets to it, so a kimono carries neither a service rifle
    # nor a tactical assault pack; Headgear is filtered on its own 'hardtech'
    # flag by filter_by_hardtech(), keyed on that same outfit register.
    "Outfit": ("Headgear", "Weapon", "Gear"),

    # Headgear is deliberately NOT here, though it gates Gear's 'helmet' flag
    # exactly the way Outfit gates its 'notac' one. It is one of the eleven
    # traits the import GUI re-rolls on a single click with no confirmation
    # dialog, and an edge from it would turn that button into a silent
    # two-trait re-roll - the failure test_every_one_click_trait_closes_to_
    # itself() exists to catch, and the reason Build is absent from this map
    # too. The pairing is resolved the way Build's is instead: roll_npc() runs
    # the filter in BOTH directions, so a Headgear re-roll that pins the Gear
    # drops the worn helmets from its own pool rather than redrawing the Gear.

    # Gear reads the Weapon's 'hands' - a weapon that occupies them rules out
    # equipment that needs one - and Stance reads its 'hands', 'gun' and 'none'
    # flags, since a pose that aims a firearm needs the roll to have actually
    # produced one.
    "Weapon": ("Gear", "Stance"),

    # The other half of the combined carried-flags filter Stance runs on:
    # roll_npc() concatenates the Weapon's flags with the Gear's, so a new
    # thermos filling a hand invalidates a hands-in-pockets pose exactly as a
    # new rifle does.
    "Gear": ("Stance",),

    # Weather is a different KIND of edge from its twenty-two neighbours, and
    # the difference is worth stating so a later reader does not go looking for
    # the filter it does not have. Nothing narrows the Weather pool: the
    # Backdrop's 'weather' flag is read at prompt-build time by
    # weather_sentence(), which decides only whether the rolled Weather is
    # RENDERED. So a Weather kept across a new Backdrop is never illegal, only
    # newly hidden or newly visible - a freshness edge rather than a
    # contradiction one. It is here because the design doc's §3 table asks for
    # it and because it errs in the safe direction: re-drawing a trait the new
    # scene is about to show for the first time beats carrying the old scene's
    # weather under a new sky.
    #
    # Glow placement is the contradiction edge of the pair. It is filtered on
    # whether the Backdrop's scene has a light source at all, via
    # has_light_source(split_backdrop(...)), since a placement flagged 'scene'
    # asserts the environment is what casts the light. Keep it across a new
    # Backdrop and it describes a scene that is gone.
    #
    # Gear is the third, and it is here for an ordering reason rather than a
    # flag-filter one, which is why it is worth spelling out. A 'nogear'
    # backdrop has already filled the subject's hands, so roll_npc() corrects
    # for it by re-rolling a 'hands' Gear onto a bullet that leaves them free -
    # the one place in that function where a dependency runs backwards, since
    # Gear is drawn before Backdrop. That correction runs BEFORE
    # npc.update(overrides), so a pinned Gear is pasted straight back over it
    # and survives a scene that forbids it: 23 times in 400 on the live tables
    # with Backdrop freed alone, against none at all on a fresh roll. A pinned
    # Gear therefore cannot be trusted across a new Backdrop the way the
    # correction inside the roller can - it has to be re-rolled with it.
    "Backdrop": ("Weather", "Glow placement", "Gear"),

    # The cut carries a '{colour}' slot that roll_npc() fills from the rolled
    # colour, and that colour's tail is appended after the whole cut phrase. A
    # new colour therefore has to redraw the cut: the old one's slot was filled
    # and closed over a shade the NPC is no longer in, so there is nowhere left
    # to put the new one. That is the refusal UNREROLLABLE_REASONS already
    # spells out for Hair colour, restated here as an edge.
    "Hair colour": ("Hair",),

    # Build. An Age flagged 'young' is a teenager, so it drops the Build
    # bullets flagged 'figure', which describe an adult woman's.
    #
    # The pairing runs both ways in roll_npc() - a forced 'figure' Build drops
    # the 'young' Age bullets through the forced_figure branch - but only ONE
    # direction is an edge here, and the asymmetry is deliberate rather than an
    # oversight. Neither direction is preventing a measured contradiction: free
    # either trait alone and the pinned one already narrows its pool, inside
    # the loop for a freed Build and through forced_figure for a freed Age. So
    # both edges would only be buying width, and width is not free in the same
    # amount on both sides.
    #
    # Age is not one of the eleven traits an entry without raw bullets can
    # re-roll, so nothing outside this map is promised anything about the size
    # of its cascade, and too wide is the safe way to be wrong - a cascade one
    # trait too wide re-draws something that would have been fine, one trait
    # too narrow ships a contradiction. Build IS one of the eleven, and the
    # cascade spec's §5 promises those keep firing on one click: an edge from
    # Build would make a one-click button silently change the NPC's age and
    # hair, which is the "user expected a smaller change" risk §6 names, spent
    # on an edge that guards nothing. So the width goes on Age's side, where it
    # costs nothing, and Build closes to itself. A test derived from
    # REROLLABLE_TRAITS holds that promise for all eleven.
    #
    # Hair colour is the same 'young' flag read one table over: an 'older'
    # shade - greying, salt-and-pepper - asserts an age the Age clause earlier
    # in the same prompt would contradict, so a young Age drops those bullets
    # exactly as it drops the 'figure' builds. Freeing Age alone strands one 3
    # times in 400 on the live tables, against none at all on a fresh roll. It
    # reaches Hair transitively from here, through the '{colour}' edge above,
    # which is right: a cut that closed over a greying shade cannot keep it
    # once the NPC is a teenager.
    "Age": ("Build", "Hair colour"),
}


def trait_cascade(name):
    """`name` plus every trait a re-roll of it invalidates, transitively.

    The closure of TRAIT_DEPENDENTS from `name`, `name` included - so a trait
    nothing depends on closes to just itself, which is what leaves the eleven
    traits that already re-roll cleanly untouched by any of this.

    Transitive because the invalidation is: a new Role redraws the Outfit, the
    new Outfit redraws Headgear, Weapon and Gear, and the new Weapon and Gear
    redraw the Stance. Stopping at the direct dependents would hand back a
    figure posed around the rifle that was replaced two steps earlier.

    Written as a worklist over a `seen` set rather than as a recursive walk,
    because the map is not promised to be acyclic and this must not depend on
    it. It held a cycle until recently - Age depended on Build and Build on
    Age, the 'young'/'figure' pairing roll_npc() filters in both directions -
    and Build's half was dropped for a reason about button behaviour rather
    than about graph shape, so the next filter audited in both directions will
    put one back. Nothing is enqueued twice, so the walk terminates on a cycle
    rather than recurring forever; the test for that patches a cycle into the
    map rather than relying on today's data, and do not replace this with a
    recursion that assumes a DAG.

    Ordered by REQUIRED_TABLES rather than by discovery order, so a cascade can
    never disagree with the order the roller draws in, and so the same cascade
    reads the same way in the CLI's report as in the GUI's dialog.

    An unknown name raises rather than closing to an empty tuple. The
    REQUIRED_TABLES filter below would otherwise swallow a misspelling and hand
    back (), and a caller hands this straight to reroll_from_raw() as its free
    set - so a typo would pin every trait and re-roll nothing, reporting a
    re-roll that changed the NPC not at all. A silent no-op wearing the name of
    a re-roll is the exact failure class this map exists to prevent, so it is
    an error here rather than a puzzle at the other end.
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


# The twelve traits a Theme re-roll has to draw again: Theme, the seven themed
# tables, and then Gear, Stance, Glow placement and Weather, which arrive
# transitively - through the new Outfit and Weapon, and through the new
# Backdrop. The design doc names all twelve by hand; this is bound to the
# closure rather than to a copy of that list, because a derivation that comes
# out agreeing with the doc is worth more than a second copy of the doc that
# can drift the first time THEMED_TABLES changes.
#
# The name is kept because two things outside this line refer to it: the design
# doc, and the import GUI's server, which reads THEME_CASCADE out of this file
# by name over the same read-the-source route it already uses for
# REROLLABLE_TRAITS.
THEME_CASCADE = trait_cascade("Theme")

# Krea 2 conditions on at most 512 tokens and silently truncates the rest, so a
# prompt that runs long loses its tail - which is where the palette, the flat
# white background and the closing style tags live. Measured against ComfyUI's
# own Qwen2 tokenizer over 9000 generated prompts, this file averages 4.8
# characters per token; the estimate is deliberately pessimistic at 4.5 so the
# warning fires before the server actually truncates.
TOKEN_LIMIT = 512
CHARS_PER_TOKEN = 4.5

# Rolls --trait-odds takes when no count is given. Chosen for the precision it
# buys rather than the time it costs: at 20,000 the standard error near p=0.1
# is about 0.2 percentage points, which holds still when the answer is shown
# as a whole percentage. A further decimal place would need roughly 100 times
# as many rolls, and a digit that flickers between runs is worse than no digit.
# About six seconds on the live tables file.
DEFAULT_ODDS_SAMPLES = 20000


def estimate_tokens(text):
    return int(len(text) / CHARS_PER_TOKEN)


# Words a rolled Weapon, Gear, Outfit, Headgear, Feature, Eyes or
# Backdrop-scene bullet already uses when it describes something that would
# actually cast colored light - a lit instrument panel, a glowing seam, a
# neon sign, a muzzle flash.
# The glow-colour sentences below only fire when at least one rolled bullet
# matches, so the "faint {glow} glow" they describe always has something in
# frame to have cast it, rather than landing on a scene with no light source
# at all (a mech hangar in shadow, a dropship bay door against a plain sky).
# Deliberately excludes plain daylight/dusk words like "sun" or "sunlit" -
# natural light doesn't motivate an arbitrary saturated glow color either.
LIGHT_SOURCE_WORDS = re.compile(
    r"\b(glow\w*|lit|lighting|lights?|neon|lanterns?|beacons?|readouts?|"
    r"monitors?|displays?|screens?|flames?|embers?|burning|instruments?|"
    r"holographic|holograms?|headlamps?|glaring)\b|muzzle flash",
    re.IGNORECASE,
)


def has_light_source(*texts):
    return any(LIGHT_SOURCE_WORDS.search(text) for text in texts)


# What the prompt asserts about the subject's age, in the two highest-signal
# positions it has: the opening phrase, and the face clause. Both templates used
# to hardcode the adult form, which is why an Age bullet reading "in her late
# teens" still rendered a woman in her thirties - the opening phrase won. An Age
# bullet flagged 'young' swaps in the other pair instead.
MATURITY = {
    False: "a fully grown adult",
    True: "a young",
}
FACE = {
    False: "with mature adult facial structure - grown brow, cheekbones and jaw",
    # Kept shorter than the adult form on purpose: it is the longest single
    # clause either template can take, and the Age bullet has already said the
    # same thing once. At the old length one roll in six thousand tipped the
    # prompt over Krea 2's 512-token ceiling.
    True: "with a young face, the brow and jaw not yet fully grown",
}

# Traits asserted for every NPC of a given gender rather than left to a roll,
# for the same reason MATURITY and FACE are asserted rather than inferred from
# the Age bullet: one bullet in a pool of thirty does not move the render often
# enough to matter, and the painterly style otherwise drifts androgynous. Keyed
# on the noun the Pronouns bullet supplies, so a fourth pronoun set opts in by
# naming its gender here. Unlike the 'figure' builds, this clause is not gated
# on the Age flag: it describes a face and a bearing rather than an adult
# figure, so it applies to every woman the tables roll. Keep it that way -
# anything naming bust, hips or waist belongs in a 'figure' Build bullet, which
# a young NPC cannot roll.
GENDER_TRAITS = {"woman": "full lips, feminine posture, "}

# The coarse folder each rolled Role lands in - <root>/<category>/<Name>/ - so
# that "a mercenary sniper" and "a close-quarters blade specialist" end up
# together under Soldiers rather than each getting their own one-NPC folder,
# which is what grouping on the raw Role text would do. Keyed on the exact
# bullet text from the Role table, so a new bullet added to the tables file
# needs an entry here too; one that's missing falls into UNCATEGORIZED_ROLE
# rather than failing the run, with a warning printed so it doesn't go unnoticed.
ROLE_CATEGORIES = {
    "a mech pilot": "Pilots",
    "a starship pilot": "Pilots",
    "an elite mercenary pilot": "Pilots",
    "a chief mechanic": "Technicians",
    "a maintenance technician": "Technicians",
    "a dockworker": "Laborers",
    "a freelance salvager": "Laborers",
    "a corporate liaison officer": "Officials",
    "a Union inspector": "Officials",
    "a colonial administrator": "Officials",
    "a field medic": "Support",
    "a comms and sensors operator": "Support",
    "a smuggler": "Criminals",
    "a pirate": "Criminals",
    "a Union marine soldier": "Soldiers",
    "a mercenary squad lead": "Soldiers",
    "a security officer": "Soldiers",
    "a mercenary sniper": "Soldiers",
    "a close-quarters blade specialist": "Soldiers",
    "a bar owner and information broker": "Civilians",
    "a data courier": "Civilians",
    "a scavenger-priest of a local machine cult": "Civilians",
}
UNCATEGORIZED_ROLE = "Other"

# The Weapon-roll policy each ROLE_CATEGORIES bucket gets, layered on top of
# the mil/civ split - see apply_weapon_policy().
WEAPON_POLICY = {
    "Officials": "restricted",
    "Criminals": "armed_bias",
}

# Whether a Role's work admits ceremonial or finely-made dress, layered on top
# of the civ/mil split the same way WEAPON_POLICY is - see filter_by_dress().
#
# Keyed on the ROLE_CATEGORIES bucket rather than on a per-Role flag, for the
# reason MECH_ACCESS is: that mapping already encodes which job an occupation
# is, and a second flag on '## Role' would restate it and then drift from it.
# The 22 Role bullets need no edit at all.
#
# Only two categories are 'plain', and that is not an oversight. Pilots,
# Soldiers and Support are entirely 'mil' Roles, and filter_by_mil() already
# drops every 'civ' bullet from their pool - which is every ceremonial outfit
# in the table - so they are barred already. Officials is the case this gate
# must NOT break: fine dress is correct for a corporate liaison or a colonial
# administrator. Criminals keeps it because a pirate in finery is a genre
# staple, and Civilians because it holds the scavenger-priest, for whom robes
# are the point.
DRESS_POLICY = {
    "Laborers": "plain",       # dockworker, freelance salvager
    "Technicians": "plain",    # chief mechanic, maintenance technician
}

# What every other category gets. A default rather than six more entries, so a
# Role category added later is covered without a second edit here - the same
# reasoning DEFAULT_WEAPON_POLICY carries, and the lesson that file learned
# when seven civilian Roles fell through an unlisted policy.
DEFAULT_DRESS_POLICY = "any"


# What a non-mil Role gets when WEAPON_POLICY names no policy for it. It used
# to be "none at all", which meant seven civilian Roles - dockworker, chief
# mechanic, maintenance technician, freelance salvager, bar owner, data
# courier, scavenger-priest - rolled the raw pool and came out armed 65% of
# the time. Weapon sits outside the civ/mil filter by design (a civilian may
# carry a military-issue weapon), so nothing else was holding them back.
# A default rather than seven more WEAPON_POLICY entries, so a civilian Role
# added to the Role table later is covered without a second edit here.
DEFAULT_WEAPON_POLICY = "civilian"

# How many extra copies of the unarmed bullets the civilian tier stacks into
# the pool. The live table is 86 weighted entries, 30 of them unarmed; three
# extra copies makes it 176 with 120 unarmed, or 68%. This is the dial for how
# armed ordinary civilians feel - raise it for a quieter setting.
CIVILIAN_UNARMED_COPIES = 3

# Gear bullets that belong to one occupation and no other. A flag named here
# locks its bullet to the Role bullets listed against it: a rolled Role not in
# that set never sees the bullet at all, and no other filter re-admits it.
#
# This is the one hard exclusion in the file. Every other filter here is a
# preference that falls back to the whole pool rather than roll nothing -
# 'notac', 'dressy', 'hardtech', the civ/mil split - because each of those is
# answering "does this pairing read badly", and a slightly odd pairing beats a
# crash. A lock answers a different question: this object means something
# about the person carrying it, and handing it to anyone else is not an odd
# pairing but a wrong one. Gear's neutral pool is fifty-odd bullets deep, so
# there is no realistic way to empty it; test_role_lock.py holds that.
#
# Keyed on exact Role bullet text, not on a ROLE_CATEGORIES bucket, and that
# is the difference from DRESS_POLICY above. The bucket is right for "what
# kind of work is this" - a question about a whole category, which is why
# restating it per-Role there would only drift. A lock is the opposite: it
# names one job because the item is that job's, and 'Officials' would hand
# the administrator's cane to a corporate liaison and a Union inspector too.
# Because the text has to match exactly, it can go stale silently if a Role
# bullet is reworded - test_role_lock.py checks every name here is still in
# the live Role table, and that every lock flag in the tables is defined here.
#
# Gear only. Weapon has its own Role machinery in apply_weapon_policy(), and
# what a person wears is already handled three other ways; if a lock is ever
# wanted on another table, widen filter_by_role_lock()'s call site rather than
# adding a second mapping.
ROLE_LOCKS = {
    "admin": ("a colonial administrator",),
}

# Trait names that have changed, old -> new. --regen-manifest rebuilds an NPC
# from a stored traits dict rather than re-rolling, so an entry written before
# a rename still carries the old key and would otherwise KeyError in
# build_prompts(). Same situation the npc.get("Weapon", "") and
# npc.get("Theme", "-") reads elsewhere in this file handle inline; factored
# out here because a rename is mechanical and a table of names is easier to
# extend than another scattered .get.
LEGACY_TRAIT_NAMES = {
    "Accent": "Glow colour",
}

# What a stored manifest entry gets for Headgear when it has none at all -
# ten entries predate the Headgear table entirely and would otherwise raise
# KeyError('Headgear') in build_prompts() on regeneration. The most common
# roll by far (weighted x6 against the table's other ~40 entries, each x1 or
# x2) is bare-headed, so that is the truest guess available for an entry that
# recorded no opinion either way.
DEFAULT_HEADGEAR = "{Subject} {is_are} bare-headed."


def rename_legacy_traits(traits):
    """`traits` with every key in LEGACY_TRAIT_NAMES renamed to its current
    heading, values untouched.

    Split out of migrate_traits() because it is the one of that function's
    three jobs that also applies to a stored rawTraits dict. The other two -
    the Faction repair and the Headgear backfill - both recognise or invent a
    RENDERED sentence, and a raw bullet is not one: repairing a raw Faction's
    missing '||' would collide with the '||' that already separates its own
    flag segment, and inventing a raw Headgear bullet would hand
    reroll_from_raw() prose with no flags to filter on. A renamed key,
    though, is exactly as stale in rawTraits as it is in traits - the table
    heading changed, not the shape of what is stored under it - so this much
    of the migration is safe to run on either.
    """
    out = dict(traits)
    for old, new in LEGACY_TRAIT_NAMES.items():
        if old in out:
            value = out.pop(old)
            out.setdefault(new, value)
    return out


def migrate_traits(traits):
    """A stored manifest trait dict brought forward to current table names
    and value shapes.

    Three jobs: rename any trait key listed in LEGACY_TRAIT_NAMES to its
    current heading (see rename_legacy_traits(), which does this job alone
    for rawTraits), repair a Faction value stored before the name/visual
    split existed (a bare string with no '||') into the current
    'name || visual' shape, and backfill a missing Headgear the same way
    regenerate_one() already backfills a missing Height - so a regenerated
    prompt reproduces the original one, or comes as close as a lost trait
    allows.
    """
    # Captured before the rename below pops "Accent" out - see the Faction
    # repair's gate further down, which needs to know whether the key was
    # ever there at all.
    predates_rename = "Accent" in traits
    out = rename_legacy_traits(traits)
    # A stored Faction with no '||' predates split_faction()'s name/visual
    # split: every bullet in the current tables file carries at least one
    # separator, so a bare string can only have been written before the
    # split existed - back when the table's single segment WAS the visual
    # clause, dropped straight into the clothing sentence ("in IPS-Northstar
    # workwear, riveted and salt-stained" was the whole Faction bullet, not
    # a name). Restoring it into BOTH the name and visual segments, not just
    # the visual, means split_faction() returns the same text everywhere the
    # old single-segment value used to reach - the prompt's clothing
    # sentence and the dossier's "Affiliation" row and byline alike - which
    # is what makes regenerate_one()'s promise of an identical prompt
    # actually hold for the entries rolled before this split, this
    # migration's whole reason to exist.
    #
    # Gated on "Accent" rather than just "no '||' in Faction", because that
    # weaker test has a real false positive: `--set-trait
    # Faction="Harrison Armory"` is accepted today and stores exactly that
    # bare shape, so an entry rolled with it AFTER the split would also have
    # no '||' without being a legacy value at all. The Accent rename and the
    # Faction split shipped in the same branch, in that order, so an entry
    # storing "Accent" is old enough to predate both and its bare Faction is
    # genuinely pre-split; an entry already storing "Glow colour" was rolled
    # after the rename landed, and by the time it could roll at all the split
    # had landed too - so its bare Faction, if any, can only be a
    # --set-trait, and rewriting it here would double up a visual clause it
    # never had.
    if predates_rename and "Faction" in out and "||" not in out["Faction"]:
        print("! stored Faction %r has no '||' - assuming this entry "
              "predates Faction's name/visual split and treating the whole "
              "value as the visual signature, so the original prompt "
              "reproduces. If this entry was rolled after that split from a "
              "genuinely bare Faction bullet, this is wrong - check the "
              "regenerated render." % out["Faction"], file=sys.stderr)
        out["Faction"] = "%s || %s" % (out["Faction"], out["Faction"])
    # Same shim as the Height backfill in regenerate_one(), for the same
    # reason: a trait table added after some manifest entries were written
    # leaves those entries with no key for it at all, and build_prompts()
    # reads npc["Headgear"] unconditionally (unlike npc.get("Weapon", "") and
    # npc.get("Theme", "-") elsewhere, a missing Headgear predates the table
    # rather than describing a genuinely headgear-less NPC, so it needs a
    # stand-in rather than an empty string). Warn once, then proceed, so the
    # promise that every stored NPC keeps regenerating stays true instead of
    # a KeyError traceback. Substituted here, not left for roll_npc()'s
    # generic pronoun pass, because that pass never runs on a migrated dict -
    # a stored entry is already-finished prose, and this default has to match
    # that shape to reach build_prompts() usable.
    if "Headgear" not in out:
        print("! stored traits for %r has no Headgear (written before the "
              "Headgear table existed) - defaulting to bare-headed; re-roll "
              "instead of regenerating to pick a real one."
              % out.get("name", "<unnamed>"), file=sys.stderr)
        out["Headgear"] = DEFAULT_HEADGEAR.format(**pronoun_fields(out.get("Pronouns", "")))
    return out


# How much of a themed roll should come from that theme's own bullets rather
# than from the neutral pool. A theme that is merely *opened* is not *visible*:
# with a dozen tagged bullets against a neutral floor of nearly two hundred, a
# themed NPC would roll neutral almost every time and the theme would never be
# seen. Raise it for a stronger house style, lower it for more variety.
THEME_SHARE = 0.6

# Generation workflows chosen by gender rather than by flag, keyed the same way
# GENDER_TRAITS is: women render through their own checkpoint stack, and any
# gender not named here falls through to --workflow. Only the two text-to-image
# stages are gendered - background removal is the same cut either way, so --rmbg
# stays a single workflow.
GENDER_WORKFLOWS = {
    "woman": art.WORKFLOW_DIR / "Lancer_Scene_Workflow_for_girls_v1.json",
}

PORTRAIT_SIZE = (1024, 1024)   # square, straight onto the Foundry actor sheet
TOKEN_SIZE = (1024, 1280)      # tall, so head and boots keep their margin

PORTRAIT_TEMPLATE = (
    "{shot} of {role}, {maturity} {gender} {age}, rendered in a detailed "
    "painterly illustration style with fine grain texture, clean linework and halftone "
    "dot shading worked into the shadows, moody cinematic lighting. {Subject} {is_are} "
    "{height}, {build}, {face}, and {traits}"
    "{skin}, {hair}, {eyes}, and {feature}, wearing {outfit}, {faction_line}{possessive} "
    "clothing following the shape of {possessive} frame. {headgear} "
    "{Possessive} face carries {demeanor}. "
    "{gear_line}{backdrop} {weather_line}{glow_line} "
    "Shallow depth of field, square framing, high detail, atmospheric sci-fi character "
    "portrait, painterly brushwork with heavy grain and dense halftone screentone worked "
    "into every shadow."
)

# The painterly style is asserted twice - once opening, once closing - and not
# four times. Two further restatements used to sit in the middle ("the same
# fine grain and visible brushwork as a close-up portrait", "matching the same
# painterly rendering as the portrait shot"); both existed to stop the token
# drifting from the portrait's look, and the closing tag block already says
# that in the position a diffusion model weights hardest. Removing them bought
# back the headroom the Weapon slot needed - see
# docs/superpowers/specs/2026-09-03-phase-2-structural-splits-design.md §4.
# The opening sentence asserts FRAMING only - the whole body in shot, at
# realistic proportions. It used to open "standing at full height", which also
# asserted a pose, and that fought {stance} on every crouching, kneeling or
# sitting bullet: the prompt claimed both at once and the model answered by
# rendering both, one standing figure and one crouched. The pose is {stance}'s
# job alone. "both boots planted and fully visible" went the same way - it is
# false for every non-standing bullet - and "the arms free" contradicted any
# pose braced on an arm. What replaces them says only what is true of every
# pose in the table: the feet are in frame and the pose is not rigid.
# What that sentence did NOT say was how big to draw the figure, and at CFG
# 1.0 "the whole figure in frame" alone loses to the detail the rest of the
# prompt asks for: the model anchors the head near the top, draws it at
# portrait scale, and runs out of canvas somewhere around the shins - the feet
# the sentence just promised are the first thing cropped. So the framing is
# asserted twice more, in the two places that actually move it. "the head
# drawn small in frame" is the scale instruction the head-count was standing
# in for - seven-to-eight heads tall is a ratio, and a ratio is satisfied just
# as well by a head too big for the canvas. And the closing tag block opens
# with the shot scale, since that block is the position a diffusion model
# weights hardest and it previously named the composition ("Centered
# composition") without naming the distance.
#
# The background sentence went the same way, for a sharper reason: it read "a
# solid flat plain white, no texture, no gradient, no shadow, no environment",
# two sentences before a tail asking for "fine grain texture", "heavy grain"
# and "dense halftone screentone worked into every shadow". Every flattening
# word there has a direct contradiction in the same prompt. "The background
# ALONE is" was meant to scope them, and scoping is what a diffusion text
# encoder is worst at - the same failure as the leg-wraps veto above. So the
# model chose, and which way it fell varied by roll: that is why some tokens
# came back painterly and others cel-shaded with no grain and no halftone,
# while the portrait, which carries none of these words, never drifted. The
# negations were not achieving their own goal either - every generated token
# background is faintly mottled grey rather than flat white. What replaces
# them asserts the same requirement positively, for the background-removal
# pass, without describing how anything is rendered.
TOKEN_TEMPLATE = (
    "A full-body character illustration of {role}, {maturity} {gender} {age}, "
    "rendered in a detailed painterly illustration style with fine grain texture, clean "
    "linework and halftone dot shading worked into the shadows, moody cinematic lighting "
    "on the figure. {Subject} {is_are} "
    "facing the viewer, {possessive} whole figure in frame from the top of "
    "{possessive} head to the soles of {possessive} shoes, the head drawn small "
    "in frame with clear empty space above and below, in realistic adult proportions "
    "roughly seven to eight heads tall. "
    "{Subject} {is_are} {height}, {build}, {face}, and {traits}{skin}, {hair}, {eyes}, "
    "and {feature}, wearing "
    "{outfit}, {faction_line}{possessive} clothing following the shape of "
    "{possessive} frame. {headgear} "
    "{Possessive} face carries {demeanor}. {gear_line}{Subject} {is_are} {stance}, both "
    "feet in frame, the pose natural and unforced. "
    "{glow_line} Behind {object} the background is an empty plain white void. "
    "Full-length wide shot, the whole "
    "figure clear of the frame edge, centered composition, dramatic "
    "lighting, high detail, isolated character illustration, clean silhouette, painterly brushwork "
    "with heavy grain and dense halftone screentone worked into every shadow."
)

# The forms the closing palette line takes. Two dimensions: whether anything
# rolled for this NPC could cast a glow (has_light_source), and whether the
# rolled Faction asserts pigment of its own ('|| palette').
#
# Pigment and light are different things and coexist happily - a green-and-gold
# Harrison uniform lit by a red instrument glow reads correctly - but the
# line's claim that the glow is the ONLY saturated colour stops being true when
# the uniform has one, so {other} softens it. Four constants and one slot
# rather than eight constants.
# {placement} is the rolled '## Glow placement' bullet, which is written as the
# predicate of this sentence and carries its own contrast clause. It used to be
# the fixed phrase "falls across one side of {possessive} face against warm dim
# ambient light on the other", which put the light on the face of every single
# portrait; that phrasing is still in the table, as one weighted bullet among
# ten rather than as the only option.
# What a stored NPC with no rolled placement gets. An entry written before
# '## Glow placement' existed still regenerates through build_prompts(), and
# this is the wording it would have had - the fixed phrase that used to be
# baked into GLOW_PORTRAIT. Deliberately placeholder-free where the original
# read "{possessive} face": a manifest's traits have already had their pronouns
# substituted by the time they are stored, so nothing re-runs the substitution
# on the regen path and a placeholder here would ship a literal brace to the
# image model. Same defensive shape as npc.get("Weapon", "") below.
LEGACY_GLOW_PLACEMENT = (
    "falls across one side of the face against warm dim ambient light on the other"
)

GLOW_PORTRAIT = (
    "A faint {glow} glow {placement}. Keep the palette restrained - greys, "
    "olive drab and rust - with {glow} the only {other}saturated color in the frame."
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


# --------------------------------------------------------------------------
# Roll tables
# --------------------------------------------------------------------------


def parse_tables(md_path):
    """'## Heading' starts a table; each '- item' under it is one option.

    A leading 'xN ' on a bullet repeats it N times, which is how the tables
    express 'common' versus 'rare' without a weights column.
    """
    tables = {}
    seen = []
    current = None

    for line in md_path.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^##\s+(?!#)\s*(.*?)\s*$", line)
        if heading:
            current = heading.group(1)
            if current in tables:
                seen.append(current)
            tables.setdefault(current, [])
            continue

        bullet = re.match(r"^-\s+(.*?)\s*$", line)
        if bullet and current:
            text = bullet.group(1)
            weight = re.match(r"^x(\d+)\s+(.*)$", text)
            count, text = (int(weight.group(1)), weight.group(2)) if weight else (1, text)
            tables[current].extend([text] * count)

    parse_tables.repeated = sorted(set(seen))
    return {name: options for name, options in tables.items() if options}


def check_tables(tables, path, repeated=()):
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


def variant_table(tables, name, subject):
    """The options one pronoun set rolls from, base table plus any variant.

    Two forms, because the two cases genuinely differ. 'Build (she)' is used
    *instead of* 'Build' - the masculine builds should not apply at all.
    'Outfit (she) +' is added *to* 'Outfit', so a woman can still roll every
    neutral option alongside the feminine ones rather than being forced out of
    grey coveralls. Either way the script stays ignorant of which traits are
    gendered; the tables file decides.
    """
    replacement = tables.get("%s (%s)" % (name, subject))
    if replacement is not None:
        return replacement
    return tables[name] + tables.get("%s (%s) +" % (name, subject), [])


def heading_for(tables, name, subject, bullet):
    """Which '## Heading' a rolled bullet actually came from.

    The inverse of variant_table(), and deliberately written in its order: a
    replacement variant is the whole pool, an additive one is searched next,
    and the base table is the fallback. Written the other way round the two
    would disagree the moment either changed.

    A bullet whose text sits in both a base table and its '+' variant is
    attributed to the variant. That is a duplicate in the tables file, which
    is a mistake worth fixing at the source; reporting it under one of its two
    headings is not the worst thing that mistake does.
    """
    replacement = "%s (%s)" % (name, subject)
    if replacement in tables:
        return replacement
    additive = "%s (%s) +" % (name, subject)
    if bullet in tables.get(additive, []):
        return additive
    return name


def trait_odds(tables, samples, rng):
    """Each bullet's chance of being rolled, as {heading: {bullet: fraction}}.

    Sampled, not computed: roll the real roller `samples` times and count what
    comes out. The alternative - propagating a distribution through the filters
    analytically - would be a second implementation of roll_npc()'s filter
    chain sitting beside the first, and its failure mode is the silent one.
    Nothing crashes; the numbers are simply wrong. Sampling cannot disagree
    with the generator because it *is* the generator, and it stays correct
    through every filter added later with no maintenance at all.

    The number is unconditional: the fraction of rolled NPCs that end up with
    this bullet under this heading. Two consequences worth knowing before
    reading the output.

    A variant family splits its total across its headings rather than each
    heading summing to 1 - a 'Build (she)' bullet is reachable only by a
    woman, so those rows sum to the share of NPCs who are women. That is the
    honest unconditional answer.

    And 'Weather' sums to 1 though most NPCs show no weather: it is always
    rolled, and weather_sentence() then drops it unless the Backdrop is
    flagged 'weather'. Reporting the joint probability instead would read 0%
    for every bullet flagged 'clear', which opts out of rendering by design -
    so the number stays a roll frequency and the caveat belongs in whatever
    displays it.
    """
    counts = {key: {bullet: 0 for bullet in bullets}
              for key, bullets in tables.items()}
    for _ in range(samples):
        npc = roll_npc(tables, rng)
        subject = npc["Pronouns"].split("/")[0]
        for name, bullet in npc["_raw"].items():
            counts[heading_for(tables, name, subject, bullet)][bullet] += 1
    return {key: {bullet: n / samples for bullet, n in bullets.items()}
            for key, bullets in counts.items()
            if any(k == key or key.startswith(k + " (") for k in REQUIRED_TABLES)}


def dress_policy_for(category):
    """The dress policy a ROLE_CATEGORIES bucket gets, 'plain' or 'any'."""
    return DRESS_POLICY.get(category, DEFAULT_DRESS_POLICY)


def filter_by_dress(options, policy):
    """Outfit bullets flagged 'dressy', dropped for a role that works with its hands.

    'dressy' reads as ceremonial, formal or finely made - gold thread, lacquer,
    brocade, ornament. It is a third axis, orthogonal to civ/mil and to Theme:
    civ/mil distinguishes "not a uniform" from "a uniform" and says nothing
    about register, which is how a dockworker ended up in a gold-embroidered
    robe with a purple sash.

    Deliberately NOT the same flag as 'notac'. That one means "do not pair this
    with tactical gear" and covers rags as well as finery - a dockworker in
    ragged cloth bindings, a travel-worn robe or a weathered haori is entirely
    plausible, and several of those read as poorer than the default coveralls.
    The two flags disagree on seven of the thirteen bullets that carry 'notac'
    in the base table.

    Faction does not come through here. A 'dressy' Faction stays reachable and
    loses only its visual segment - see build_prompts(). A dockworker employed
    by the Karrakin Trade Baronies is good flavour; a dockworker dressed as a
    baron is the bug.
    """
    if policy != "plain":
        return options
    plain = [x for x in options if "dressy" not in split_flags(x)[1]]
    return plain or options        # never filter the pool down to nothing


def filter_by_role_lock(options, role):
    """Gear bullets locked to an occupation, dropped for every other Role.

    A bullet carrying a flag named in ROLE_LOCKS is that job's and nobody
    else's - a colonial administrator's lacquered cane of office reads as
    ceremony on an administrator and as a walking aid on a dockworker, which
    is not the same object. Anything unflagged is neutral and reachable by
    everyone, which is all but a handful of the table.

    Unlike every other filter in this file this one does NOT fall back to the
    whole pool when it empties, because falling back would hand the locked
    bullet to exactly the Role it was locked away from - the one outcome the
    flag exists to prevent. See the note on ROLE_LOCKS for why the pool cannot
    realistically empty, and test_role_lock.py for the guard that it doesn't.

    Takes the rolled Role's stripped text: ROLE_LOCKS is keyed on the bullet
    as the Role table writes it, and roll_npc() has already split the '|| mil'
    flag off by the time Gear rolls.
    """
    return [x for x in options
            if all(role in ROLE_LOCKS[f]
                   for f in split_flags(x)[1] if f in ROLE_LOCKS)]


def filter_by_hardtech(options, outfit_notac):
    """Headgear flagged 'hardtech', dropped under an Outfit flagged 'notac'.

    'hardtech' is modern technology worn on the head: helmets sealed or open,
    visor and lens rigs, sensor and night-vision hardware, breather masks,
    comms headsets, anything strung with cabling or seated on jacks, and
    powered or cybernetic pieces. Not soft goods, not plain eyewear, and not
    the traditional register - a kimono wants a kabuto above it, and gets one.

    This is the third and last place 'notac' reaches. It already drops 'mil'
    bullets from Weapon and Gear so an elaborate outfit carries neither a
    military rifle nor a tactical pack; it had never reached what the NPC
    wears on their head, which is how a corporate liaison ended up in a floral
    kimono under a sealed flight helmet.

    Deliberately NOT keyed on 'mil'. That flag means "an actual issued
    uniform" on the two tables that carry it, Headgear is not in
    filter_by_mil(), and putting 'mil' on headgear bullets would invite
    someone to wire it in and quietly change what a civilian may wear. It is
    also the wrong word for a third of the set: a cybernetic ear implant, a
    mechanical diagnostic rig and a pair of retro-industrial headphones are
    none of them military and all three fight a kimono.
    """
    if not outfit_notac:
        return options
    soft = [x for x in options if "hardtech" not in split_flags(x)[1]]
    return soft or options         # never filter the pool down to nothing


def filter_by_mil(options, mil, name):
    """Faction/Outfit bullets flagged 'civ' or 'mil', filtered by a military Role.

    A bullet flagged 'civ' reads as plainly civilian dress and is dropped when
    the NPC's Role came up flagged 'mil' - a soldier should not turn up in a
    cropped tank top and cut-offs. One flagged 'mil' reads as an actual issued
    uniform and is dropped for a civilian Role instead, per the brief:
    civilians may carry any gear they like, including military-issue weapons,
    but shouldn't appear in uniform unless they used to serve. An unflagged
    bullet is neutral and reachable either way, the same as an untagged
    Gear/Stance entry - never filtered down to nothing.

    Takes the table name because Faction keeps its flags in a third segment
    while Outfit keeps them in a second - split_flags() on a three-segment
    bullet would return the visual prose as flags.
    """
    exclude = "civ" if mil else "mil"
    plain = [x for x in options if exclude not in flags_for(name, x)]
    return plain or options


def filter_by_theme(options, theme, name):
    """A theme's own bullets plus the neutral pool; other themes' are dropped.

    The neutral pool - every bullet carrying no '@' tag at all - is deliberately
    reachable from every theme. Roughly 45% of this file's appearance bullets
    are the campaign's plain worn-industrial look, and they belong in a
    neosamurai NPC's wardrobe as much as anyone's: a woman in a kimono and a
    woman in grey coveralls are both this setting.

    Never filtered down to nothing, the same as every other filter here: a
    tables file with no tags yet - which is exactly what this ships as - falls
    back to the full pool rather than erroring.
    """
    if not theme:
        return options
    keep = [
        x for x in options
        if not themes_of(flags_for(name, x)) or theme in themes_of(flags_for(name, x))
    ]
    return keep or options


def apply_theme_share(options, theme, name, share=THEME_SHARE):
    """Duplicate the theme's own bullets until they hold `share` of the pool.

    The multiplier is computed from the actual pool sizes rather than fixed, so
    it self-corrects as content is authored: a theme with 56 outfits barely
    needs duplicating, one with 11 needs a lot. A thin theme therefore still
    reads as itself - at the cost of repeating within a run, which its low
    weight in the Theme table already makes uncommon.

    `share` is a target for the pool *as it reaches this function*, not a
    promise about the value finally drawn. roll_npc() calls this first and then
    narrows the result further - filter_by_mil(), the 'notac' filter,
    apply_weapon_policy() - and those later filters drop tagged and neutral
    bullets at different rates, so the realized share drifts by however much
    they correlate with the theme. It drifts BOTH ways, and down is the
    direction that bites: on test/fixtures/tables-themed.md, measured against
    THEME_SHARE at 0.6, the military-leaning gundam theme's Weapon realized
    0.710, while scav's only tagged Outfit is 'civ' and realized 0.328 on that
    table, because filter_by_mil drops that bullet outright for a military
    Role. A theme authored entirely on one side of the civ/mil split is
    invisible to roles on the other side whatever `share` says - see
    `python -m test.theme_visibility --tables test/fixtures/tables-themed.md`
    for current figures rather than trusting these.

    Deliberately left as it is; reordering the filters trades this for a worse
    problem (a theme's tagged weapons re-inflating past WEAPON_POLICY's
    unarmed bias), and that trade is Phase 2's to make with the measurement
    in hand.

    Untouched when there is nothing to balance: no theme, no tagged bullets, or
    no neutral ones. Duplication only ever adds entries, so every bullet in the
    pool stays reachable.
    """
    if not theme:
        return options
    tagged = [x for x in options if theme in themes_of(flags_for(name, x))]
    neutral = [x for x in options if not themes_of(flags_for(name, x))]
    if not tagged or not neutral:
        return options

    # Want tagged*n / (tagged*n + neutral) >= share, so
    # n >= share*neutral / ((1 - share) * tagged).
    n = math.ceil(share * len(neutral) / ((1 - share) * len(tagged)))
    return tagged * max(1, n) + neutral


def apply_weapon_policy(options, category, mil, unarmed=False):
    """Bias or filter the Weapon roll to fit the NPC's Role.

    Three tiers, layered on top of filter_by_mil's civ/mil split:

      - A mil-flagged Role (a soldier, pilot or similar - see the note near
        the top of the tables file) is always armed, not just usually: the
        pool is restricted to bullets flagged 'sidearm' - a holstered or
        openly worn pistol, alone or paired with a slung primary weapon - so
        a holstered pistol is never optional. The compound pistol+rifle
        bullets outweigh the pistol-only ones, which is the "usually a rifle
        too" half of the brief. Never filtered to nothing: an untagged
        tables file falls back to the full pool rather than erroring.
      - WEAPON_POLICY['Officials'] ("restricted"): these almost never carry
        anything dangerous, and never anything but a pocketable weapon when
        they do. Bullets flagged 'weapon' are dropped unless also flagged
        'simple', then the unarmed bullets are duplicated heavily so an
        armed roll stays rare rather than impossible.
      - WEAPON_POLICY['Criminals'] ("armed_bias"): usually carrying something.
        'weapon'-flagged bullets are duplicated into the pool, the same
        trick this function used to reserve for a mil Role alone.
      - Every other non-mil category ("civilian", DEFAULT_WEAPON_POLICY):
        unarmed bullets are duplicated CIVILIAN_UNARMED_COPIES times so an
        ordinary Role - anything not named in WEAPON_POLICY, which is most
        of them - is unarmed more often than not rather than defaulting to
        the raw, mostly-armed pool.

    Untouched is no longer reachable through category at all; it now only
    happens for a tables file with no 'weapon'/'sidearm' flags to duplicate
    or filter on.
    """
    # --unarmed disarms who it can, not everyone. A mil Role's sidearm is a
    # setting guarantee and a Criminal's armament is most of what makes them
    # read as one; the flag exists to empty ordinary civilians' hands. Placed
    # first so the intent is visible before the tiers it overrides, though the
    # mil guard below would reach the same answer either way.
    if unarmed and not mil and category != "Criminals":
        disarmed = [x for x in options if "weapon" not in split_flags(x)[1]]
        return disarmed or options

    if mil:
        armed = [x for x in options if "sidearm" in split_flags(x)[1]]
        return armed or options

    policy = WEAPON_POLICY.get(category, DEFAULT_WEAPON_POLICY)
    if policy == "restricted":
        pocketable = [
            x for x in options
            if "weapon" not in split_flags(x)[1] or "simple" in split_flags(x)[1]
        ] or options
        unarmed_bullets = [x for x in pocketable if "weapon" not in split_flags(x)[1]]
        return pocketable + unarmed_bullets * 5 if unarmed_bullets else pocketable
    if policy == "armed_bias":
        tagged = [x for x in options if "weapon" in split_flags(x)[1]]
        return options + tagged * 4 if tagged else options
    if policy == "civilian":
        unarmed_bullets = [x for x in options if "weapon" not in split_flags(x)[1]]
        return options + unarmed_bullets * CIVILIAN_UNARMED_COPIES if unarmed_bullets else options
    return options


def resolve_pronouns(tables, subject):
    """'she' -> the full 'she/her/her/woman' bullet out of the Pronouns table.

    The table stays the source of truth: this matches on the subject field
    rather than knowing what pronoun sets exist, so adding a fourth bullet to
    the markdown makes it selectable here with no change to the script. Pinning
    the whole bullet rather than just the subject also keeps the fourth field -
    the noun the image prompt states outright - which is what actually stops the
    tokens coming back androgynous.
    """
    wanted = subject.strip().lower().split("/")[0]
    for bullet in tables["Pronouns"]:
        if bullet.split("/")[0].strip().lower() == wanted:
            return bullet
    raise SystemExit(
        "--pronouns %s: no such set in the Pronouns table. Available: %s"
        % (subject, ", ".join(sorted({b.split("/")[0] for b in tables["Pronouns"]})))
    )


def pronoun_fields(pronouns):
    """'she/her/her/woman' -> the subject/object/possessive fields prompts substitute.

    Split out of roll_npc so --regen-manifest can rebuild the same fields from
    a stored Pronouns trait without re-rolling anything.
    """
    bits = (pronouns.split("/") + ["", "", ""])[:4]
    subject, object_, possessive, gender = bits
    plural = subject == "they"
    gender = gender or {"she": "woman", "he": "man"}.get(subject, "person")
    return {
        "gender": gender,
        "subject": subject,
        "Subject": subject.capitalize(),
        "object": object_,
        "possessive": possessive,
        "Possessive": possessive.capitalize(),
        "is_are": "are" if plural else "is",
        "carry": "carry" if plural else "carries",
        "wear": "wear" if plural else "wears",
    }


def roll_npc(tables, rng, overrides=None, unarmed=False, probe=None):
    """One NPC as a flat dict of trait -> rolled text.

    `probe`, when a dict is passed, is filled with the fully-filtered pool
    this function computed for each table, keyed by table name. It is a
    read-out of work already being done rather than a second computation:
    every filter below narrows `options` and the draw comes off the end of
    it, so the list recorded here is by construction the set of bullets this
    table could have produced given the traits above it. That is the whole
    reason the query in trait_choices() can promise not to drift - there is
    nothing for it to drift from.

    Recording consumes no randomness and changes no value, so a probed roll
    and an unprobed roll at the same seed are the same NPC.
    test_set_trait_value.ProbeIsInert holds that, and every legality answer
    depends on it.

    Pronouns is the one table with no entry: it is drawn before the loop from
    an unfiltered list and is refused by both re-roll paths anyway, so there
    is no question to answer about it.
    """
    # Pronouns first: every other table may have a per-pronoun variant, so the
    # roll that selects between them has to happen before the rest.
    pronouns = (overrides or {}).get("Pronouns") or rng.choice(tables["Pronouns"])
    subject = pronouns.split("/")[0]

    # Age, Role, Outfit and Build are read up front, but for two different
    # reasons. Build's and Outfit's flags each gate a roll that happens
    # BEFORE their own table does - a forced Build narrows the Age pool, and
    # a forced Outfit narrows the Role pool - so those two have to be known
    # this early to narrow anything at all. Age and Role are read this early
    # too, but only so the loop below can tell "already forced" from "about
    # to be rolled" and skip narrowing a pool whose forced value would
    # discard the narrowing anyway; the actual both-forced contradiction is
    # caught later, once npc["Age"] and npc["Role"] are known either way.
    # Every forced value gating a *later* table is handled inside the loop,
    # where it replaces that table's draw. Pass the flag to keep it either
    # way, as in
    # --set-trait Age="in her late teens || young",
    # --set-trait Role="a Union marine soldier || mil", or
    # --set-trait Outfit="an elaborate floral kimono ... || civ notac".
    forced_age = (overrides or {}).get("Age")
    forced_role = (overrides or {}).get("Role")
    forced_outfit = (overrides or {}).get("Outfit")
    forced_build = (overrides or {}).get("Build")

    # Build gates a roll in the other direction to the three above: a forced
    # build flagged 'figure' describes an adult woman's, so it constrains the
    # *Age* roll rather than being constrained by it. Known before the loop for
    # the same reason - Age is rolled first.
    forced_figure = (
        forced_build is not None and "figure" in split_flags(forced_build)[1]
    )

    # Dress register runs the same way round as the Age/Build pairing. Role is
    # rolled before Outfit, so a rolled Role constrains the Outfit pool; but a
    # FORCED ceremonial Outfit has to constrain the Role roll instead, or an
    # explicit choice would collide with a randomly rolled dockworker and abort
    # the run. Both forced and contradictory is checked further down.
    forced_dressy = (
        forced_outfit is not None and "dressy" in split_flags(forced_outfit)[1]
    )

    # And the same shape a third time, for the helmet pairing. Headgear is
    # rolled before Gear, so a rolled helmet constrains the Gear pool; but a
    # PINNED carried helmet has to constrain the Headgear roll instead. This is
    # the path a --reroll-trait Headgear takes on an entry with raw bullets:
    # reroll_from_raw() pins every other trait as an override and frees the
    # target, so the Gear arrives here already fixed and the Headgear is the
    # only variable left to yield.
    #
    # Unlike the Age/Build and Role/Outfit pairings above, the both-forced case
    # is NOT an error further down. Those two raise because the prompt itself
    # would contradict - a teenager with an adult woman's build, a dockworker
    # in ceremonial dress. Two helmets contradict nothing; the clauses are both
    # true of the figure and only the render is ugly. Someone naming both with
    # --set-trait is overriding an aesthetic default on purpose, which is what
    # --set-trait is for, so it is honoured rather than refused.
    forced_gear = (overrides or {}).get("Gear")
    forced_headgear = (overrides or {}).get("Headgear")
    forced_carried_helmet = (
        forced_gear is not None and "helmet" in split_flags(forced_gear)[1]
    )

    # And a fourth time, for the hair pairing. Hair is rolled before Headgear,
    # so a rolled updo constrains the Headgear pool; but a PINNED helmet has to
    # constrain the Hair roll instead, and this is the path a
    # --reroll-trait Hair takes on an entry with raw bullets.
    #
    # The both-forced case is honoured rather than refused, the same way two
    # helmets are: a bun and a helmet are each true of the figure and only the
    # render is ugly, so naming both with --set-trait is an aesthetic override
    # made on purpose.
    forced_hair = (overrides or {}).get("Hair")
    forced_worn_helmet = (
        forced_headgear is not None
        and "helmet" in split_flags(forced_headgear)[1]
    )
    role_dress = DEFAULT_DRESS_POLICY

    # Theme is rolled before every appearance table it gates, for the same
    # reason Pronouns is: the roll that selects between pools has to happen
    # before those pools are drawn from. It is deliberately NOT gated on Role -
    # a pirate should be as likely to look neosamurai as cyberpunk - so nothing
    # here reads npc["Role"].
    theme = (overrides or {}).get("Theme") or rng.choice(tables["Theme"])
    # No filter runs on Theme - it is the thing the others are filtered by -
    # so its pool is the whole table. Recorded anyway, so a caller asking
    # "what could Theme be" gets a list rather than a KeyError, and so the
    # probe's coverage test can name every table uniformly.
    if probe is not None:
        probe["Theme"] = list(tables["Theme"])

    npc = {"Pronouns": pronouns, "Theme": theme}

    # The bullets exactly as the file spells them, flags and all, collected at
    # the moment each is drawn. npc[name] cannot serve: the strip block below
    # takes the flag segment off nine tables, so a rendered Weapon no longer
    # matches any line in the file, and two bullets differing only in flags
    # collapse into one.
    #
    # Two consumers want this. --trait-odds counts raw bullets, because a
    # count has to key on something the tables file actually contains. And
    # --reroll-trait wants to pin every trait but one back into a fresh roll,
    # which only works if the pinned values still carry the flags the filters
    # read - see the raw-bullets spec, which this implements the collection
    # half of.
    #
    # '_'-prefixed, so the manifest writer's `not k.startswith("_")` filter
    # keeps it out of stored entries until that spec's own half lands.
    raw = {"Pronouns": pronouns, "Theme": theme}

    young = False
    role_mil = False
    outfit_notac = False
    hair_updo = False
    headgear_helmet = False
    weapon_hands = False
    weapon_flags = ()
    for name in REQUIRED_TABLES:
        if name in ("Pronouns", "Theme", "Stance"):
            continue
        options = variant_table(tables, name, subject)

        # Theme gates every appearance table: its own tagged bullets plus the
        # neutral pool, with the tagged ones weighted up so the theme is
        # actually visible rather than merely available. Applied first, so the
        # civ/mil and policy filters below narrow within the theme rather than
        # across it - which is what lets a soldier be neosamurai in uniform.
        if name in THEMED_TABLES:
            options = filter_by_theme(options, theme, name)
            options = apply_theme_share(options, theme, name)

        # The Age/Build pairing runs both ways. When the Build was forced
        # to a bullet flagged 'figure' and the Age is being rolled, it is the
        # Age pool that yields: an explicit choice of build shouldn't collide
        # with a random teenager and abort the run. Forcing both at once still
        # raises further down, since two explicit choices that contradict each
        # other are a mistake worth reporting rather than silently resolving.
        if name == "Age" and forced_figure and forced_age is None:
            grown = [x for x in options if "young" not in split_flags(x)[1]]
            options = grown or options     # never filter the pool down to nothing

        # The inverse direction: a forced ceremonial Outfit drops the Role
        # categories that would contradict it, rather than the Role dropping
        # the Outfit. Mirrors 'figure'/'young' above exactly, including the
        # 'or options' guard - a Role table of nothing but Laborers should
        # still roll rather than abort.
        if name == "Role" and forced_dressy and forced_role is None:
            entitled = [x for x in options
                        if dress_policy_for(
                            ROLE_CATEGORIES.get(split_flags(x)[0])) != "plain"]
            options = entitled or options

        # The third pairing, running the same way round as the two above: a
        # pinned carried helmet drops the worn ones from the Headgear pool,
        # rather than the Headgear dropping the Gear. See forced_carried_helmet
        # for why this direction has to exist at all.
        if (name == "Headgear" and forced_carried_helmet
                and forced_headgear is None):
            bare = [x for x in options if "helmet" not in split_flags(x)[1]]
            options = bare or options      # never filter the pool down to nothing

        # The fourth, same shape again: a pinned worn helmet drops the cuts
        # gathered on top of the skull from the Hair pool, rather than the Hair
        # dropping the Headgear. See forced_worn_helmet.
        if name == "Hair" and forced_worn_helmet and forced_hair is None:
            flat = [x for x in options if "updo" not in split_flags(x)[1]]
            options = flat or options      # never filter the pool down to nothing

        # Build is filtered against the Age roll, the same way Stance is
        # filtered against Weapon and Gear below. An Age bullet flagged
        # 'young' is a teenager; the Build bullets flagged 'figure' describe
        # an adult woman's - bust, hips, waist - and the two must never be
        # combined.
        # Age precedes Build in REQUIRED_TABLES, so the flag is known by the
        # time this runs; keep it that way if the list is ever reordered.
        if name == "Build" and young:
            plain = [x for x in options if "figure" not in split_flags(x)[1]]
            options = plain or options     # never filter the pool down to nothing

        # An 'older' colour - greying, salt-and-pepper - asserts an age, so it
        # must not land on a teenager: the Age clause earlier in the same
        # prompt would contradict it. Age precedes Hair colour in
        # REQUIRED_TABLES, so the flag is already known. Same shape as the
        # Build/'figure' pairing above.
        if name == "Hair colour" and young:
            plain = [x for x in options if "older" not in flags_for(name, x)]
            options = plain or options     # never filter the pool down to nothing

        # Faction and Outfit are filtered against the Role roll the same way:
        # a Role flagged 'mil' excludes bullets flagged 'civ' and vice versa,
        # so a soldier doesn't turn up in a cropped tank top and a dockworker
        # doesn't turn up in a dress uniform. Weapon and Gear sit outside this
        # civ/mil split entirely - a civilian may carry a military-issue
        # weapon or piece of gear same as anyone. Weapon gets its own
        # Role-driven bias instead, from apply_weapon_policy() below; Gear is
        # filtered elsewhere in this same loop, just not by Role - by the
        # Weapon roll's 'hands' flag, by 'notac', and by a 'nogear' Backdrop.
        # Role precedes all three in REQUIRED_TABLES, so role_mil is already
        # known.
        if name in ("Faction", "Outfit"):
            options = filter_by_mil(options, role_mil, name)

        # Dress register, layered on top of civ/mil. Outfit only: a 'dressy'
        # Faction keeps its place in the pool and loses only its visual
        # segment, in build_prompts(). Role precedes Outfit in REQUIRED_TABLES,
        # so role_dress is already known.
        if name == "Outfit":
            options = filter_by_dress(options, role_dress)

        # An item that belongs to one occupation, kept off everyone else. This
        # runs first among the Gear filters, and before the hands and helmet
        # ones below, because it is the only one of the three that is a rule
        # rather than a preference - the others hand the pool back untouched
        # when they would empty it, and running them first could only mean a
        # locked bullet survived that fallback. Role precedes Gear in
        # REQUIRED_TABLES, so npc["Role"] is already the value this NPC keeps.
        if name == "Gear":
            options = filter_by_role_lock(options, npc["Role"])

        # A weapon that occupies the hands rules out equipment that also needs
        # one. Weapon precedes Gear in REQUIRED_TABLES so this flag is already
        # known, the same way Role precedes Faction and Outfit. Gear is what
        # yields: the weapon is the more theme-defining object, and dropping a
        # thermos costs nothing.
        if name == "Gear" and weapon_hands:
            free = [x for x in options if "hands" not in split_flags(x)[1]]
            options = free or options      # never filter the pool down to nothing

        # One head, one helmet. A Headgear bullet flagged 'helmet' is a helmet
        # actually worn, so the Gear bullet that carries one under an arm reads
        # as a spare rather than a pilot between sorties. Headgear precedes
        # Gear in REQUIRED_TABLES so this flag is already known, the same way
        # Weapon's 'hands' is above, and Gear yields for the same reason: the
        # thing on the head is the more defining object, and the table has
        # thirty other bullets to fall back on.
        #
        # Keyed on 'helmet' rather than the 'hardtech' register Headgear
        # already carries, because hard tech is the whole modern head register
        # - headsets, brow visors, ear implants - and none of those fight a
        # helmet held under an arm. Widening it would cost that pairing for
        # sixteen bullets to fix a clash that only three of them have.
        if name == "Gear" and headgear_helmet:
            bare = [x for x in options if "helmet" not in split_flags(x)[1]]
            options = bare or options      # never filter the pool down to nothing

        # One head, one volume. A Hair bullet flagged 'updo' gathers the hair
        # on top of the skull - a topknot, a high ponytail, a crowned bun - and
        # a helmet has nowhere to go over it: the render puts the bun through
        # the helmet, every seed, because the two clauses describe two objects
        # in the same place. Hair precedes Headgear in REQUIRED_TABLES so this
        # flag is already known, the same way Weapon's 'hands' is above, and
        # Headgear yields because the hair is drawn first and the table has
        # sixty other bullets to fall back on.
        #
        # Keyed on 'helmet' rather than 'hardtech' for the reason the Gear
        # filter below gives: a headset, a brow visor or an ear implant leaves
        # the crown free, and a topknot above one reads fine.
        if name == "Headgear" and hair_updo:
            bare = [x for x in options if "helmet" not in split_flags(x)[1]]
            options = bare or options      # never filter the pool down to nothing

        # A placement flagged 'scene' puts the light out in the environment -
        # on a wall, in the air, across the ground - so it only makes sense
        # when the BACKDROP is what casts it. The alternative source is
        # something the NPC wears or carries, and a lit visor does not light
        # the wall behind them. Glow placement follows Backdrop in
        # REQUIRED_TABLES precisely so the rolled scene is readable here, the
        # same way Role precedes Faction and Outfit.
        if name == "Glow placement" and not has_light_source(
                split_backdrop(npc["Backdrop"])[1]):
            on_figure = [x for x in options if "scene" not in split_flags(x)[1]]
            options = on_figure or options   # never filter the pool down to nothing

        # The Weapon policy runs BEFORE 'notac' below, and the order is
        # load-bearing: being armed is a guarantee, 'notac' is only a
        # preference, so the guarantee gets to pick the pool first. Run the
        # other way round the 'notac' strip empties the pool of every bullet
        # the mil-Role guarantee would have kept - every 'sidearm' bullet is
        # also flagged 'mil' - and apply_weapon_policy's own 'or options'
        # fallback then hands back the whole table, weighted empty entry
        # included, so a mil Role in a notac outfit rolled unarmed on 7 rolls
        # in 10. This way the policy narrows to the sidearms and 'notac's own
        # fallback re-admits them rather than the reverse.
        if name == "Weapon":
            options = apply_weapon_policy(
                options, ROLE_CATEGORIES.get(npc["Role"]), role_mil, unarmed)

        # 'notac' applies to both halves of the old Gear table: an elaborate or
        # traditional outfit should pair with neither a military-issue rifle
        # nor a military-issue radio. Restricting only the Weapon would leave a
        # kimono carrying a tactical assault pack.
        if name in ("Weapon", "Gear") and outfit_notac:
            no_mil = [x for x in options if "mil" not in split_flags(x)[1]]
            options = no_mil or options

        # And the third thing an NPC wears. Outfit precedes Headgear in
        # REQUIRED_TABLES, so outfit_notac is already known here, the same way
        # role_mil is known by the time Faction and Outfit roll. Keyed on its
        # own 'hardtech' flag rather than on 'mil' - see filter_by_hardtech().
        if name == "Headgear" and outfit_notac:
            options = filter_by_hardtech(options, outfit_notac)

        # Rolled either way, so that forcing a trait does not shift the rest
        # of the run's random stream and change every NPC after it. The
        # exception is a forced trait that *filters* a later pool - the
        # Age/Build pairing above, and the Gear and Stance filters below -
        # since a shorter pool draws differently. Those already behaved this
        # way for a rolled trait; forcing one just makes it reachable sooner.
        #
        # After the last filter and before the draw: this is the only line in
        # the function where `options` is exactly what the roller is about to
        # choose from, which is what makes it the honest answer to "what could
        # this table have produced for this NPC".
        if probe is not None:
            probe[name] = list(options)
        value = rng.choice(options)

        # A forced value replaces the draw here, at the moment its own table is
        # rolled, rather than at the npc.update(overrides) much further down -
        # so every filter that reads an earlier trait reads the bullet this NPC
        # actually keeps rather than the one the roll discarded.
        #
        # This named Age, Role and Outfit one at a time until reroll_from_raw()
        # arrived, because those three were the only forced traits anything
        # downstream read. A re-roll from stored raw bullets pins every trait
        # but one, so the rest are read too, and leaving them to the late
        # update produced exactly the contradictions the flags exist to
        # prevent: a pinned Weapon was invisible to the Gear and Stance
        # filters, which posed a figure with their hands in their pockets
        # around the rifle they are holding, and a pinned Backdrop was
        # invisible to the Glow placement filter, which washed light across a
        # scene that casts none. The three names above are kept where they
        # are, because those uses run the pairing the other way round - a
        # forced trait narrowing an *earlier* table's pool, which cannot be
        # decided from inside that table's own iteration.
        forced = (overrides or {}).get(name)
        if forced is not None:
            value = forced

        # Recorded here: after a forced value has replaced the draw, so _raw
        # describes the NPC rather than the bullet it discarded, and before
        # the strip block below, which is the last moment the flags exist.
        raw[name] = value
        # Whatever is left of a bullet is rendered straight into a prompt and
        # a dossier, so its flag segment comes off here. Hair, Feature and
        # Headgear are in this list because Theme tags them: the moment a
        # bullet reads 'a long braid || @neosamurai', the tag would otherwise
        # be shipped to the image model as part of the hairstyle. Weapon is
        # here for the same theme-tag reason, and also so weapon_hands is
        # known in time to filter Gear below - Weapon precedes Gear in
        # REQUIRED_TABLES. weapon_flags is kept around too (not just the
        # 'hands' bit) because the Stance filter further down needs the
        # 'gun' flag as well, and by the time that runs npc["Weapon"] has
        # already had its flags stripped right here - re-splitting it there
        # would just split plain text and get nothing back.
        #
        # Three tables are deliberately absent, for one shared reason:
        # Backdrop, Hair colour and Faction each separate three fields with
        # '||' rather than two, so split_flags() would take the third table's
        # prose - a Backdrop's scene, a Hair colour's tail, a Faction's
        # visual signature (the second segment, the description that reaches
        # the image prompt in place of the name) - for flags and throw it
        # away. Each is unpacked by its own splitter instead, Backdrop by
        # split_backdrop() downstream in build_prompts() and write_dossier(),
        # Hair colour by split_hair_colour() further down this function,
        # Faction by split_faction() in build_prompts() and write_dossier().
        # A newly themed table belongs in the list below only if its bullets
        # are the ordinary two-segment shape. Gear is absent for an unrelated
        # reason - its own flags gate the Stance roll further down, so it is
        # split there instead.
        if name in ("Age", "Build", "Role", "Outfit",
                    "Hair", "Feature", "Headgear", "Weapon", "Glow placement"):
            value, flags = split_flags(value)
            if name == "Age":
                young = "young" in flags
            if name == "Role":
                role_mil = "mil" in flags
                # Read off the stripped value, which is what ROLE_CATEGORIES
                # is keyed on.
                role_dress = dress_policy_for(ROLE_CATEGORIES.get(value))
            if name == "Outfit":
                outfit_notac = "notac" in flags
            if name == "Hair":
                hair_updo = "updo" in flags
            if name == "Headgear":
                headgear_helmet = "helmet" in flags
            if name == "Weapon":
                weapon_hands = "hands" in flags
                weapon_flags = flags
        npc[name] = value

    npc["_young"] = young
    # The Outfit's register, published for the same reason '_young' is: the
    # manifest stores Outfit with its flags stripped, so without this a
    # Headgear re-roll could not tell whether it was gated, and Headgear would
    # have to leave REROLLABLE_TRAITS - taking its button in the import GUI
    # with it. See the raw-bullets spec, which generalises this and subsumes
    # both keys.
    npc["_outfit_notac"] = outfit_notac

    # Stance is rolled last, and filtered against the Weapon and Gear rolls.
    # The tables are otherwise independent, which produced NPCs standing with
    # their hands pushed into their pockets while holding a rifle in both
    # hands. A carried item that occupies a hand rules out the stances that
    # need both of them free, and a Stance that describes aiming or firing a
    # weapon needs the roll to have actually come up a firearm, or the pose
    # has nothing in hand to back it up.
    #
    # npc["Weapon"] was already split above, in the loop - Weapon precedes
    # Gear in REQUIRED_TABLES, so its flags had to come off before Gear's
    # 'hands' filter could run. Gear is split here instead, same as before.
    npc["Gear"], gear_flags = split_flags(npc["Gear"])

    # Stance is filtered against the combined flags of both carried tables.
    # Splitting Weapon out of Gear moved every 'gun' bullet with it, so reading
    # gear_flags alone would make gun poses permanently unreachable - and a
    # figure holding a rifle in both hands could still be posed with both hands
    # in their pockets, which is the pairing this filter exists to stop.
    carried_flags = weapon_flags + gear_flags
    # Paired raw-bullet/flags rather than split text/flags, so the raw line is
    # still in hand when one is picked. The filters below read [1] either way,
    # and the strip block further down takes the flags off npc["Stance"] - it
    # already had to, for a --set-trait override that arrives with them on.
    stances = [(x, split_flags(x)[1])
               for x in variant_table(tables, "Stance", subject)]
    # Two flags, one hierarchy. 'armed' marks a pose that references a weapon
    # of any kind - a blade held, a hilt gripped, a weapon raised overhead;
    # 'gun' marks the narrower case of a firearm being handled. An NPC whose
    # Weapon roll came up empty can wear neither, or the prompt poses them
    # brandishing something no earlier sentence names. Before 'armed' existed
    # only 'gun' was gated, so seven melee poses could land on an unarmed
    # figure - rare on a plain roll, routine under --unarmed.
    #
    # The unarmed bullet is identified by its 'none' flag, which used to be an
    # inert marker and is now load-bearing; the Weapon table's comment says so.
    if "none" in weapon_flags:
        disarmed = [x for x in stances
                    if "armed" not in x[1] and "gun" not in x[1]]
        stances = disarmed or stances      # never filter the pool down to nothing
    elif "gun" not in carried_flags:
        unarmed = [x for x in stances if "gun" not in x[1]]
        stances = unarmed or stances       # never filter the pool down to nothing
    if "hands" in carried_flags:
        free = [x for x in stances if "hands" not in x[1]]
        stances = free or stances          # never filter the pool down to nothing
    # `stances` is (bullet, flags) pairs so the raw line survives the filters;
    # the probe wants the bullets alone, to match every other entry.
    if probe is not None:
        probe["Stance"] = [x[0] for x in stances]
    raw["Stance"] = npc["Stance"] = rng.choice(stances)[0]

    # A 'nogear' backdrop has the subject's hands full of whatever the scene
    # handed them, so a thermos held in one of them contradicts the picture.
    # Backdrop is rolled after Gear, so this re-rolls rather than filtering a
    # pool - the one place in this function that does, and only because the
    # dependency runs backwards.
    #
    # Stance above was already chosen from carried_flags computed before this
    # re-roll runs, so a nogear scene is judged against the pre-re-roll Gear.
    # That is only conservative today - the re-roll only narrows to non-hands
    # bullets, and none of this fixture or the live table's non-hands Gear
    # carries 'gun', so the "gun needs a gun-describing pose" pairing can't be
    # broken by it. It would stop being safe if a non-hands 'gun' Gear bullet
    # were ever added, since Stance would then be picked without knowing about
    # it. Not restructured to fix this, since nothing reachable today needs it.
    #
    # npc["Backdrop"] is already the effective one: the loop pastes a forced
    # value over its draw at the point that table is rolled, so a --set-trait
    # backdrop, or one pinned by reroll_from_raw(), is in hand here without
    # this line reading the override dict for itself. It used to do exactly
    # that, back when the paste covered only Age, Role and Outfit and
    # npc.update(overrides) - which runs below this - was the first place a
    # forced Backdrop appeared.
    if "nogear" in split_backdrop(npc["Backdrop"])[2] and "hands" in gear_flags:
        free = [x for x in filter_by_role_lock(
                    variant_table(tables, "Gear", subject), npc["Role"])
                if "hands" not in split_flags(x)[1]]
        # This re-draws from the raw table rather than from the pool the loop
        # narrowed, so every Gear filter has to be restated here or it is
        # simply undone. filter_by_role_lock() is applied inline above for
        # that reason, and 'notac' just below, same as it does in the loop's
        # own Gear roll (see the comment there) - otherwise a kimono flagged
        # 'notac' paired with a nogear scene could still re-roll onto a
        # military-issue Gear bullet the loop would have screened out. The
        # 'hands' and 'helmet' filters are not restated because this re-roll
        # narrows to non-hands bullets itself, and a carried helmet is one.
        if outfit_notac:
            civ = [x for x in free if "mil" not in split_flags(x)[1]]
            free = civ or free      # never filter the pool down to nothing
        if free:
            # The re-roll overwrites raw["Gear"] on purpose: this is the bullet
            # the NPC keeps, and both consumers want the keeper rather than the
            # draw it replaced.
            #
            # The probe entry is overwritten for the same reason. A 'nogear'
            # backdrop has already filled the subject's hands, so THIS is the
            # pool the NPC's Gear actually comes from, and the loop's wider one
            # is a list the roller has just finished overruling. Recording the
            # wider one would tell a caller that a 'hands' Gear is fine under a
            # scene that is about to take it away - which is the clash a pinned
            # Gear survives today (23 in 400, per the Backdrop -> Gear note in
            # TRAIT_DEPENDENTS), reported as if it were not there.
            if probe is not None:
                probe["Gear"] = list(free)
            raw["Gear"] = rng.choice(free)
            npc["Gear"], gear_flags = split_flags(raw["Gear"])

    npc.update(overrides or {})

    # The loop pastes a forced Age, Role and Outfit over their draws itself,
    # because those three gate later rolls and had to be known early. Every
    # other forced trait arrives only here, so _raw picks it up here to match -
    # a --set-trait bullet is given verbatim with its flags, which is exactly
    # the shape _raw stores. 'name' is filtered out: it is an override but not
    # a table, and REQUIRED_TABLES is the authority on which is which.
    raw.update({k: v for k, v in (overrides or {}).items() if k in REQUIRED_TABLES})
    npc["_raw"] = raw

    # Whether the Gear the NPC KEEPS is a carried helmet, published for the
    # same reason '_outfit_notac' is: the manifest stores Gear with its flags
    # stripped, so without this a legacy Headgear re-roll could not tell
    # whether the figure is already holding one, and Headgear would have to
    # leave REROLLABLE_TRAITS - taking its button in the import GUI with it.
    #
    # Read off raw["Gear"] rather than the gear_flags computed further up,
    # because both the 'nogear' correction above and a --set-trait override
    # can replace the drawn bullet, and raw["Gear"] is the one place that has
    # already accounted for both. Taken after npc.update(overrides) for that
    # reason, and before the strip block below, which is the last moment the
    # flags exist.
    npc["_gear_helmet"] = "helmet" in split_flags(raw["Gear"])[1]

    # The two halves of the hair/helmet pairing, published for the same reason
    # and read off raw for the same reason: the manifest stores both traits
    # with their flags stripped, so without these a legacy re-roll of either
    # one could not tell what the other is, and both would have to leave
    # REROLLABLE_TRAITS - taking their buttons in the import GUI with them.
    #
    # BOTH directions need a key here, unlike the carried-helmet pairing, which
    # needs only one: Gear is in UNREROLLABLE_REASONS on that path, so the
    # clash is reachable from the Headgear side alone. Hair and Headgear are
    # both re-rollable, so either can be the trait that moves into the clash.
    npc["_hair_updo"] = "updo" in split_flags(raw["Hair"])[1]
    npc["_headgear_helmet"] = "helmet" in split_flags(raw["Headgear"])[1]

    npc["Age"] = split_flags(npc["Age"])[0]   # the override still carries its flag
    # Same reason as Age: a --set-trait override for any of these pastes the
    # raw bullet text back over the split-out value above, flag and all.
    npc["Role"] = split_flags(npc["Role"])[0]
    npc["Outfit"] = split_flags(npc["Outfit"])[0]
    # The themed tables need it too, and Gear along with them: its split above
    # happens before this update, so --set-trait Gear='a rifle || hands gun'
    # would otherwise reach the prompt with its flags still attached.
    npc["Hair"] = split_flags(npc["Hair"])[0]
    npc["Feature"] = split_flags(npc["Feature"])[0]
    npc["Headgear"] = split_flags(npc["Headgear"])[0]
    npc["Weapon"] = split_flags(npc["Weapon"])[0]
    npc["Gear"] = split_flags(npc["Gear"])[0]
    # Stance for the same reason as Gear, and not because Stance is themed -
    # it isn't. Its rolled value was split above (rng.choice(stances)[0]), so
    # only a --set-trait Stance='... || hands' override still carries flags,
    # and without this they would reach the token prompt.
    npc["Stance"] = split_flags(npc["Stance"])[0]
    # Glow placement was added to the loop's own strip block above (it isn't
    # themed - it's there for the same reason Age is, not because THEMED_TABLES
    # says so) but was missed from this one, so a --set-trait override, or now
    # a rawTraits round-trip that feeds the rolled bullet straight back in,
    # still carried its 'scene' flag through to the prompt and the dossier.
    # Same fix, same place, same reason as every line above.
    npc["Glow placement"] = split_flags(npc["Glow placement"])[0]

    # Hair carries a '{colour}' slot rather than the template joining the two,
    # because the colour's position differs per bullet - "close-cropped
    # {colour} hair" against "a sleek {colour} bob cut level with the jaw" -
    # and no single join rule serves both. The tail goes after the whole cut
    # phrase, which is the only position a gradient reads correctly in.
    #
    # Hair colour is absent from the re-strip block above because split_flags()
    # is the wrong splitter for it: it would take the tail for flags and throw
    # the tail away. Its own three-segment split runs here instead, which
    # strips a forced bullet's flags for the same reason that block exists.
    # After npc.update(overrides), so a forced Hair colour is honoured, and
    # before the placeholder loop below, so that loop never meets an
    # unresolved '{colour}' and reports it as a bad pronoun.
    base, tail, _ = split_hair_colour(npc["Hair colour"])
    npc["Hair colour"] = base
    npc["Hair"] = npc["Hair"].replace("{colour}", base)
    if tail:
        npc["Hair"] = "%s, %s" % (npc["Hair"], tail)

    # Build needs the same unpacking, and for a second reason beyond tidiness:
    # the pool filters above only screen a *rolled* pool, so a pair of forced
    # traits walks straight past both of them. Re-check the pairing here, where
    # each flag is known whether it was rolled or forced. Only the both-forced
    # case can still reach this: a forced Build narrows the Age roll and a
    # forced Age narrows the Build roll, so either one alone resolves quietly.
    # The same both-forced case the Age/Build check below covers, one axis
    # over. Only this case can reach here: a forced Outfit narrows the Role
    # roll and a forced Role narrows the Outfit roll, so either alone resolves
    # quietly. Checked after the loop, where both values are known whether
    # they were rolled or forced.
    if (forced_dressy and forced_role is not None
            and dress_policy_for(ROLE_CATEGORIES.get(split_flags(forced_role)[0])) == "plain"):
        raise SystemExit(
            "Role and Outfit disagree: a bullet flagged 'dressy' is "
            "ceremonial or finely made and must not be combined with a "
            "Role whose work is manual. One of the two has to change, or "
            "the 'dressy' flag has to go."
        )

    build, build_flags = split_flags(npc["Build"])
    if young and "figure" in build_flags:
        raise SystemExit(
            "Age and Build disagree: a bullet flagged 'figure' describes "
            "an adult woman's build and must not be combined with an Age "
            "flagged 'young'. One of the two has to change, or the "
            "'figure' flag has to go."
        )
    npc["Build"] = build

    if "name" not in npc:
        npc["name"] = "%s %s" % (npc["Given names"], npc["Family names"])

    # subject/object/possessive, plus an optional fourth field: the noun the
    # image prompt uses for the subject. Pronouns alone left the model guessing
    # - tokens came back androgynous - so the prompt now says "adult woman" or
    # "adult man" outright. A three-field bullet still works and infers it.
    npc["_pronouns"] = pronoun_fields(npc["Pronouns"])

    # A bullet may carry pronoun placeholders of its own - "in {possessive}
    # forties" - so that a rolled trait agrees with the rolled pronouns rather
    # than hardcoding one set.
    for key, value in npc.items():
        if isinstance(value, str) and "{" in value:
            try:
                npc[key] = value.format(**npc["_pronouns"])
            except (KeyError, IndexError, ValueError) as exc:
                raise SystemExit(
                    "table %r, option %r: %s is not a pronoun placeholder. "
                    "Available: %s" % (key, value, exc, ", ".join(npc["_pronouns"]))
                )
    return npc


#: Memoisation for the bullet splitters below.
#
# Every filter pass in roll_npc() walks its pool asking each bullet for its
# flags, so one roll splits the same few hundred strings a couple of thousand
# times. That is invisible against a ComfyUI render, but --trait-odds rolls
# tens of thousands of NPCs and nothing else: profiled there, 82% of the time
# went on re-splitting strings already split. Caching them takes 20,000 rolls
# from 33s to 5.9s.
#
# Safe only because every splitter here is a pure function of hashable
# arguments returning str, tuple and frozenset - all immutable, so no caller
# can reach into a cached value and corrupt it for the next one. A splitter
# added later that returns a list or a dict MUST NOT be decorated with this;
# make it return a tuple or leave it uncached. test_trait_odds.py holds that
# line.
#
# Unbounded is right: the key space is the bullets of one tables file, and the
# generator is a short-lived CLI with nothing to leak into.
_bullet_cache = functools.lru_cache(maxsize=None)


@_bullet_cache
def split_flags(bullet):
    """'a rifle held in her hands || hands' -> the text, and its flags.

    Same '||' convention Backdrop uses, for tables whose bullets are a single
    phrase. On Gear/Weapon/Stance the flags are 'hands', meaning the entry
    occupies at least one hand or arm (on Gear or Weapon) or needs both of
    them free (on Stance), and 'gun', meaning the entry is an actual firearm
    held in hand (on Weapon) or a pose that describes aiming, firing or
    otherwise handling one (on Stance) - a bullet can carry both at once,
    '|| hands gun'. Gear and Weapon both may also carry 'mil', marking an
    actual weapon or piece of military-issue equipment (equipment on a Gear
    entry, an actual issued weapon on a Weapon entry). Weapon alone also
    carries 'weapon', 'simple' or 'sidearm', read by apply_weapon_policy()
    rather than filter_by_mil() - see the tables file for what each one
    means. Gear alone may also carry a lock flag named in ROLE_LOCKS
    ('admin'), which is read by filter_by_role_lock() and confines the bullet
    to one occupation. Age and Build reuse the same split for their own unrelated flags,
    'young' and 'figure', and so do Role ('mil', an active-duty military or
    paramilitary occupation), Faction/Outfit ('civ' or 'mil', filtered
    against the Role flag - see filter_by_mil()) and Outfit's own 'notac'
    (read in roll_npc() to keep tactical Weapon and Gear off a handful of
    outfits).
    """
    text, _, rest = bullet.partition("||")
    return text.strip(), tuple(f for f in rest.split() if f)


@_bullet_cache
def split_backdrop(bullet):
    """A Backdrop bullet carries the shot, the scene, and optional flags.

    Split on '||': the opening phrase ("A half-body character portrait"), then
    the scene sentence, then any flags. Shot and scene travel together because
    they have to agree - a dive toward the camera in dramatic foreshortening
    cannot be staged inside a half-body portrait, and a zero-gravity pose over a
    rain-streaked street would be nonsense either way.

    The one flag is 'nogear': an action scene that already put something in the
    subject's hands suppresses the merged carry sentence on the portrait (see
    carry_sentence() and build_prompts()), which otherwise arms them a second
    time from the Weapon/Gear rolls - a rolled rifle on top of the two blades
    the rooftop scene hands out. It also restricts Gear, at roll time in
    roll_npc(), to bullets that leave the hands free.
    """
    parts = [p.strip() for p in bullet.split("||")]
    if len(parts) == 1:
        return "A half-body character portrait", parts[0], ()
    shot, scene = parts[0], parts[1]
    flags = tuple(f for f in parts[2].split() if f) if len(parts) > 2 else ()
    return shot, scene, flags


@_bullet_cache
def split_hair_colour(bullet):
    """A Hair colour bullet carries the base, an optional tail, and flags.

    Three segments, the same shape split_backdrop() uses, and for the same
    reason: two of them are prose that reaches the prompt and the third is
    flags. The base fills the '{colour}' slot inside the rolled Hair bullet;
    the tail is appended after the whole cut phrase.

    That split exists because a gradient reads wrongly in adjective position -
    "a sleek silver-white fading to green at the tips bob" - and correctly as a
    trailing clause. A flat colour leaves the tail empty and reads inline.
    """
    parts = [p.strip() for p in bullet.split("||")]
    base = parts[0]
    tail = parts[1] if len(parts) > 1 else ""
    flags = tuple(f for f in parts[2].split() if f) if len(parts) > 2 else ()
    return base, tail, flags


@_bullet_cache
def split_faction(bullet):
    """A Faction bullet carries the name, an optional visual, and flags.

    Three segments, the same shape split_backdrop() and split_hair_colour()
    use, and for the same reason: two of them are prose that goes to different
    places and only the third is flags.

    The name is what the dossier and the GUI print - "Smith-Shimano Corpro".
    The visual is what reaches the image prompt, and it is deliberately allowed
    to be empty: two entries here are non-affiliations with nothing to show.

    The split exists because the single-segment form put a garment CATEGORY
    ("corporate wear", "service dress") in the prompt immediately after
    Outfit's specific garment description, competing with it for the same slot
    and losing every time - deleting the whole Faction clause from a prompt
    changed the render not at all. The visual segment is written to describe
    what Outfit does not: fabric, tailoring, insignia, patina.
    """
    parts = [p.strip() for p in bullet.split("||")]
    name = parts[0]
    visual = parts[1] if len(parts) > 1 else ""
    flags = tuple(f for f in parts[2].split() if f) if len(parts) > 2 else ()
    return name, visual, flags


@_bullet_cache
def themes_of(flags):
    """The '@theme' tags among a bullet's flags, with the '@' stripped.

    Theme tags share the '||' flag segment with the behavioural flags rather
    than getting a field of their own, because every consumer of this file -
    split_flags(), the npc-trait-import skill, the Import GUI's bullet editor -
    already parses that segment. The '@' prefix is what tells the two apart.

    An '@' token is invisible to the behavioural flag checks elsewhere in this
    module, which all test for a specific literal ('hands', 'civ', 'figure'),
    so split_flags() needs no change to coexist with these.
    """
    return frozenset(f[1:] for f in flags if f.startswith("@") and len(f) > 1)


@_bullet_cache
def flags_for(name, bullet):
    """A bullet's flag tuple, whichever '||' shape its table uses.

    Backdrop, Hair colour and Faction all carry three segments and keep their
    flags in the third, so a two-segment bullet of any of them has no flags at
    all - its second segment is prose. Every other table keeps flags in the
    second segment. Reading the last segment blindly would mistake a
    Backdrop's scene, a Hair colour's tail or a Faction's visual for flags.
    """
    if name == "Backdrop":
        return split_backdrop(bullet)[2]
    if name == "Hair colour":
        return split_hair_colour(bullet)[2]
    if name == "Faction":
        return split_faction(bullet)[2]
    return split_flags(bullet)[1]


def weather_sentence(npc):
    """The weather sentence this NPC's portrait gets, or '' for none.

    Weather is portrait-only: the token renders on flat white so it can be cut
    out, and falling snow would only give RMBG more to cut. It also reaches
    only the Backdrop entries flagged 'weather', since rain inside a cockpit or
    in hard vacuum is nonsense, and a Weather bullet flagged 'clear' opts out
    of it in turn - that flag is the dial for how often an outdoor scene comes
    up with nothing drifting in it.
    """
    if "weather" not in split_backdrop(npc["Backdrop"])[2]:
        return ""
    text, flags = split_flags(npc["Weather"])
    return "" if "clear" in flags else text


def carry_sentence(fields, weapon, gear):
    """The single sentence naming whatever the NPC is holding.

    One sentence rather than two, because two would repeat "{Subject} {carry}"
    on every armed NPC for no added clarity - and the token prompt has no
    tokens to spare for it. Returns "" when there is nothing to say, so the
    template's slot collapses cleanly rather than leaving an orphaned period
    or a doubled space.

    Both slots are genuinely optional: the Weapon table's weighted empty entry
    is what produces an unarmed NPC here. A 'nogear' Backdrop does not - it
    never reaches this function with an empty weapon; it skips the call
    entirely and blanks the portrait's whole sentence at the render site (see
    build_prompts()) instead.
    """
    carried = [x for x in (weapon, gear) if x]
    if not carried:
        return ""
    # A comma, not another "and", when either half is already compound: 25 of
    # the 56 live armament bullets read "a sidearm holstered at the hip and a
    # service rifle slung across her chest", and joining that to the Gear with
    # " and " again gives an unpunctuated "A and B and C" run-on on a majority
    # of rolls. The comma makes the sentence the list it actually is - and a
    # list is how the rest of both prompts already reads - while costing three
    # characters less than " and " rather than more, which the token prompt's
    # one-token margin cares about.
    join = ", " if any(" and " in x for x in carried) else " and "
    return "{Subject} {carry} %s. ".format(**fields) % join.join(carried)


def build_prompts(npc):
    """The portrait and token prompt text for one rolled NPC."""
    shot, scene, flags = split_backdrop(npc["Backdrop"])
    # .get, not npc["Weapon"]: --regen-manifest rebuilds npc from a stored
    # traits dict, and every entry written before this phase has no Weapon
    # key at all. Unlike the Height backfill above in regen_from_manifest,
    # this needs no warning - a pre-Weapon manifest entry describes an NPC
    # that genuinely had no weapon, so '' reproduces it exactly rather than
    # papering over a loss.
    weapon = npc.get("Weapon", "")
    fields = dict(npc["_pronouns"])
    fields.update({
        "role": npc["Role"],
        "age": npc["Age"],
        "maturity": MATURITY[npc["_young"]],
        "face": FACE[npc["_young"]],
        # Asserted for every NPC of that gender rather than rolled for, and
        # unlike the 'figure' builds not withheld from a young one.
        "traits": GENDER_TRAITS.get(npc["_pronouns"]["gender"], ""),
        "height": npc["Height"],
        "build": npc["Build"],
        "skin": npc["Skin"],
        "hair": npc["Hair"],
        "eyes": npc["Eyes"],
        "feature": npc["Feature"],
        "outfit": npc["Outfit"],
        "headgear": npc["Headgear"],
        "demeanor": npc["Demeanor"],
        "weapon": weapon,
        "gear": npc["Gear"],
        "glow": npc["Glow colour"],
        "placement": npc.get("Glow placement", LEGACY_GLOW_PLACEMENT),
        "shot": shot,
        "backdrop": scene,
        "stance": npc["Stance"],
    })
    weather = weather_sentence(npc)
    fields["weather_line"] = weather + " " if weather else ""

    # Built from the same fields and inserted already-substituted, since
    # str.format does a single pass and would leave any nested placeholder raw.
    carrying = carry_sentence(fields, weapon, npc["Gear"])

    # Pre-formatted rather than a bare slot, because a Faction with no visual
    # signature - the two non-affiliations - would otherwise leave a doubled
    # comma in the middle of the clothing sentence. Same reason gear_line is
    # assembled here rather than substituted raw.
    _, faction_visual, faction_flags = split_faction(npc["Faction"])

    # A 'dressy' Faction keeps its NAME - the dossier and byline still print
    # the affiliation - and loses only the visual that would reach the clothing
    # sentence, when the Role's work is manual. A dockworker employed by the
    # Karrakin Trade Baronies is good flavour; a dockworker in baronial
    # brocade and an heraldic crest is what this exists to stop. Barring the
    # faction outright would throw away the first to fix the second.
    #
    # Emptying the visual is the whole mechanism: the line below already drops
    # the clause rather than leaving a doubled comma, which is the path the two
    # non-affiliations - carrying no visual at all - have always taken.
    if ("dressy" in faction_flags
            and dress_policy_for(role_category(npc)) == "plain"):
        faction_visual = ""

    fields["faction_line"] = "%s, " % faction_visual if faction_visual else ""

    # A Faction flagged 'palette' asserts pigment of its own - dye in cloth,
    # not light - so the closing line's claim that the glow is the ONLY
    # saturated colour has to soften to "the only other saturated color", and
    # the no-glow case has to drop its "no stray saturated color" claim
    # entirely rather than contradict the uniform it just described.
    pigment = "palette" in faction_flags
    fields["other"] = "other " if pigment else ""
    none_line = GLOW_NONE_PIGMENT if pigment else GLOW_NONE

    # The glow colour only belongs in the prompt when something rolled for
    # this NPC would actually cast it. Equipped sources (something worn or
    # carried) apply to both shots; the backdrop's own light - a neon sign, an
    # instrument panel, a muzzle flash - only reaches the portrait, since the
    # token has no backdrop at all, just flat white.
    equipped_glow = has_light_source(
        weapon, npc["Gear"], npc["Outfit"], npc["Headgear"],
        npc["Feature"], npc["Eyes"])
    portrait_glow = equipped_glow or has_light_source(scene)

    # 'nogear' means the backdrop scene already put something in the subject's
    # hands, so the merged carry sentence is dropped from the PORTRAIT
    # entirely - not just the weapon half of it, since the scene contradicts
    # equipment held in one hand exactly as much as it contradicts a weapon.
    # The token keeps it: it has no backdrop at all, just flat white and a
    # rolled Stance, so nothing there contradicts what the NPC carries.
    portrait_fields = dict(
        fields, gear_line="" if "nogear" in flags else carrying,
        glow_line=(GLOW_PORTRAIT if portrait_glow else none_line).format(**fields))
    token_fields = dict(
        fields, gear_line=carrying,
        glow_line=(GLOW_TOKEN if equipped_glow else none_line).format(**fields))

    prompts = (PORTRAIT_TEMPLATE.format(**portrait_fields),
               TOKEN_TEMPLATE.format(**token_fields))

    for label, text in zip(("portrait", "token"), prompts):
        n = estimate_tokens(text)
        if n > TOKEN_LIMIT:
            print("! %s prompt is about %d tokens, over Krea 2's %d-token limit - the "
                  "tail will be truncated. Shorten the longest bullet it rolled."
                  % (label, n, TOKEN_LIMIT), file=sys.stderr)

    return prompts


# --------------------------------------------------------------------------
# Output paths and the dossier
# --------------------------------------------------------------------------


def _safe(name):
    """A filename Windows and Foundry are both happy with."""
    return re.sub(r"\s+", " ", re.sub(r'[<>:"/\\|?*]', "", name)).strip(" .")


def role_category(npc):
    """The folder this NPC's Role sorts into, warning once for an unmapped one."""
    category = ROLE_CATEGORIES.get(npc["Role"])
    if category is None:
        print("! Role %r has no entry in ROLE_CATEGORIES - filing under %r"
              % (npc["Role"], UNCATEGORIZED_ROLE), file=sys.stderr)
        category = UNCATEGORIZED_ROLE
    return category


def npc_folder(root, name, category, overwrite):
    """<root>/<category>/<Name>/, suffixed if that name has already been rolled."""
    base = _safe(name)
    folder = root / _safe(category) / base
    if overwrite or not folder.exists():
        return folder
    for n in range(2, 100):
        candidate = folder.parent / ("%s (%d)" % (base, n))
        if not candidate.exists():
            return candidate
    raise RuntimeError("too many NPCs already named %s" % base)


def write_dossier(path, npc, seed, prompts, images):
    portrait_prompt, token_prompt = prompts
    traits = [
        ("Callsign", npc["Callsigns"]),
        ("Pronouns", npc["Pronouns"]),
        ("Reads as", npc["_pronouns"]["gender"]),
        # .get rather than [...], so regenerating an NPC from a manifest entry
        # written before Theme existed still writes a dossier rather than raising.
        ("Theme", npc.get("Theme", "-")),
        ("Role", npc["Role"]),
        ("Affiliation", split_faction(npc["Faction"])[0]),
        ("Age", npc["Age"]),
        ("Height", npc["Height"]),
        ("Build", npc["Build"]),
        ("Skin", npc["Skin"]),
        ("Hair", npc["Hair"]),
        ("Eyes", npc["Eyes"]),
        ("Distinguishing", npc["Feature"]),
        ("Demeanor", npc["Demeanor"]),
        ("Wearing", npc["Outfit"]),
        ("Carrying", npc["Gear"]),
        ("Armed with", npc.get("Weapon", "-") or "unarmed"),
        ("Glow colour", npc["Glow colour"]),
        ("Portrait shot", split_backdrop(npc["Backdrop"])[0]),
        ("Portrait scene", split_backdrop(npc["Backdrop"])[1]),
        ("Portrait weather", weather_sentence(npc) or (
            "clear" if "weather" in split_backdrop(npc["Backdrop"])[2]
            else "none - the rolled scene is indoors or in vacuum")),
        ("Token stance", npc["Stance"]),
    ]

    lines = [
        "# %s" % npc["name"],
        "",
        '"%s" - %s, %s.' % (npc["Callsigns"], npc["Role"], split_faction(npc["Faction"])[0]),
        "",
        "Rolled by `generate-npc.py` on %s with `--seed %d`. Re-rolling with that"
        % (time.strftime("%Y-%m-%d"), seed),
        "seed and the same tables file reproduces this NPC exactly.",
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


# --------------------------------------------------------------------------
# ComfyUI
# --------------------------------------------------------------------------


class Knobs:
    """The slice of generate-art.py's argparse namespace its builders read.

    build_job() takes sampler and size overrides off an args object; rather
    than fake a full parser namespace, hand it just those fields with the size
    varying per image.
    """

    def __init__(self, args, size, output_prefix):
        self.steps = args.steps
        self.cfg = args.cfg
        self.sampler = args.sampler
        self.scheduler = args.scheduler
        self.width, self.height = size
        self.set = args.set
        self.output_prefix = output_prefix


def entry_for(category, slug, stage, prompt):
    """A generate-art.py Entry, so its job builder can be reused unchanged."""
    return art.Entry(name=slug, label=stage, path=[category, slug], prompt=prompt, line=0)


def fetch(comfy, image, target):
    """Download one rendered image straight to `target`.

    Comfy.download() mirrors the server's subfolder tree under the destination;
    here the destination filename is the whole point, so go to /view directly.
    """
    query = urllib.parse.urlencode({
        "filename": image["filename"],
        "subfolder": image.get("subfolder", ""),
        "type": image.get("type", "output"),
    })
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(comfy._get_bytes("/view?" + query))
    return target


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def default_root():
    return DEFAULT_OUTPUT_ROOT


def next_run_folder(root):
    """root/runN, the first N whose folder doesn't already exist.

    Always run1 on a fresh root - the increment only kicks in once a previous
    run has actually created that folder, so a bare, never-used root doesn't
    jump straight to some higher number.
    """
    n = 1
    while (root / ("run%d" % n)).exists():
        n += 1
    return root / ("run%d" % n)


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description=__doc__.split("\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Tables: %s" % DEFAULT_TABLES,
    )

    roll = p.add_argument_group("the roll")
    roll.add_argument("--count", type=int, default=1, help="how many NPCs to roll (default 1)")
    roll.add_argument("--seed", type=int,
                      help="base seed; NPC N uses seed+N, so a run is reproducible")
    roll.add_argument("--tables", type=Path, default=DEFAULT_TABLES,
                      help="roll-tables markdown (default: %(default)s)")
    roll.add_argument("--name", help="force the NPC's name instead of rolling one")
    roll.add_argument("--pronouns", metavar="SUBJECT",
                      help="roll only NPCs with this subject pronoun, e.g. --pronouns she; "
                           "matched against the first field of the Pronouns table, so it "
                           "gates every gendered variant table along with it")
    roll.add_argument("--set-trait", action="append", default=[], metavar="Table=value",
                      help="force one rolled trait, e.g. --set-trait Role='a field medic' "
                           "or --set-trait Theme=neosamurai to pin a whole group to one look "
                           "(repeatable; table names are the markdown headings)")
    roll.add_argument("--unarmed", action="store_true",
                      help="roll every NPC unarmed, except military Roles and "
                           "Criminals - a soldier's sidearm and a pirate's "
                           "armament are what make them read as one")

    gen = p.add_argument_group("generation")
    gen.add_argument("--workflow", type=Path, default=art.DEFAULT_WORKFLOW,
                     help="API-format generation workflow (default: %(default)s)")
    gen.add_argument("--workflow-woman", type=Path, metavar="PATH",
                     default=GENDER_WORKFLOWS["woman"],
                     help="generation workflow for NPCs who read as women "
                          "(default: %(default)s); pass the same path as --workflow "
                          "to put every NPC through one workflow")
    gen.add_argument("--rmbg", type=Path, default=art.POST_ALIASES["rmbg"],
                     help="background-removal workflow for the token")
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

    out = p.add_argument_group("output")
    out.add_argument("--out", type=Path, default=None,
                     help="root to write NPC folders into (default: a fresh runN folder "
                          "under %s, so a batch can be reviewed before any of it is moved "
                          "into Foundry by hand; passed explicitly, the path is used as-is "
                          "with no runN folder inserted)" % DEFAULT_OUTPUT_ROOT)
    out.add_argument("--overwrite", action="store_true",
                     help="reuse an existing folder of the same name instead of suffixing it")
    out.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST,
                     help="run log of every NPC rolled (default: %(default)s)")

    regen = p.add_argument_group("regenerate one NPC from a manifest entry")
    regen.add_argument("--regen-manifest", type=Path, metavar="PATH",
                       help="skip rolling entirely and reload one NPC's traits from this "
                            "manifest instead (requires --regen-id); the entry's own folder is "
                            "reused and overwritten in place, and the manifest is updated with "
                            "the new seed/files when it's done")
    regen.add_argument("--regen-id", metavar="ID",
                       help="the manifest entry's \"id\" to regenerate (requires --regen-manifest)")
    regen.add_argument("--new-seed", type=int, metavar="N",
                       help="seed for the re-render (default: the entry's original seed, which "
                            "reproduces the image exactly); every rolled trait comes from the "
                            "entry either way, so a different seed renders the same character "
                            "with new noise instead of a new roll")

    regen.add_argument("--reroll-trait", metavar="TABLE",
                       help="re-roll ONE trait of the regenerated NPC - and everything that "
                            "trait invalidates - instead of reproducing it. --reroll-trait Hair "
                            "gives an existing character a new haircut and nothing else; "
                            "--reroll-trait Theme redraws its whole visual world, twelve traits "
                            "of it. A trait that gates others takes them with it rather than "
                            "leaving them contradicting it, and every trait that goes with "
                            "it is named on the way past. Everything else comes from the entry "
                            "as usual, and the result overwrites the same folder and manifest "
                            "id. Re-rollable: "
                            + ", ".join(RAW_REROLLABLE_TRAITS)
                            + ". An NPC generated before its raw bullets were recorded is a "
                              "lossy record of its own roll - a stored Role has lost the 'mil' "
                              "flag its Faction, Outfit and Weapon are filtered on - so those "
                              "re-roll only: " + ", ".join(REROLLABLE_TRAITS))
    regen.add_argument("--trait-choices", metavar="TABLE",
                       help="print, as JSON on stdout, which values TABLE could take on "
                            "this NPC given its other traits - each with whether the roller "
                            "would have offered it ('allowed') and which kept traits it "
                            "would leave contradicting it ('conflicts'). Renders nothing and "
                            "contacts no server. Requires --regen-id, and needs the entry's "
                            "raw bullets.")
    regen.add_argument("--release", metavar="A,B",
                       help="with --set-trait, traits to re-roll instead of keeping - meant "
                            "for the ones --trait-choices reports as conflicting. Each name "
                            "expands to its whole cascade, so releasing Outfit also re-rolls "
                            "the Headgear, Weapon and Gear it gates.")

    run = p.add_argument_group("run mode")
    run.add_argument("--trait-odds", type=int, nargs="?", const=DEFAULT_ODDS_SAMPLES,
                     metavar="N",
                     help="roll N NPCs (default %d) and print each bullet's chance of "
                          "being rolled as JSON, then exit - no images, no manifest, "
                          "nothing written. Sampled through the real roller, so every "
                          "filter is accounted for: a Stance flagged '|| gun' reads "
                          "lower than its weight share because it needs a firearm to "
                          "be reachable at all. Read by the Import GUI's Tables page"
                          % DEFAULT_ODDS_SAMPLES)
    run.add_argument("--server", help="ComfyUI address, e.g. 127.0.0.1:8000")
    run.add_argument("--dry-run", action="store_true",
                     help="roll and print the NPCs and their prompts, queue nothing")
    run.add_argument("--timeout", type=float, default=1800, help="per-job timeout in seconds")
    run.add_argument("--pause", type=float, default=2.0,
                     help="seconds to sleep after each ComfyUI job (portrait, token, "
                          "background removal), so a batch doesn't queue jobs back-to-back "
                          "faster than the server can keep up (default: %(default)s)")

    args = p.parse_args(argv)

    if args.no_portrait and args.no_token:
        p.error("--no-portrait and --no-token together leave nothing to generate")

    if bool(args.regen_manifest) != bool(args.regen_id):
        p.error("--regen-manifest and --regen-id must be given together")
    if args.regen_manifest:
        # --set-trait is deliberately NOT in this list any more. "Replaces the
        # roll entirely" is still true of every flag that is: each of them
        # would be asking for a different NPC. Naming one trait's value while
        # reproducing the rest is the opposite request, and reroll_from_raw()
        # has had a `pinned` parameter for it since Theme's cascade needed one.
        conflicting = [
            flag for flag, given in (
                ("--count", args.count != 1), ("--seed", args.seed is not None),
                ("--name", bool(args.name)), ("--pronouns", bool(args.pronouns)),
                ("--unarmed", args.unarmed),
            ) if given
        ]
        if conflicting:
            p.error("--regen-manifest replaces the roll entirely; drop %s" % ", ".join(conflicting))
    elif args.new_seed is not None:
        p.error("--new-seed only makes sense with --regen-manifest")

    if args.count < 1:
        p.error("--count must be at least 1")
    if args.name and args.count > 1:
        p.error("--name only makes sense with a single NPC")

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
    if args.pronouns and "Pronouns" in overrides:
        p.error("--pronouns and --set-trait Pronouns= set the same thing; use one")
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

    args.release = [n.strip() for n in (args.release or "").split(",") if n.strip()]
    if args.release:
        if not args.overrides:
            p.error("--release only makes sense with --set-trait")
        # Only what the set trait actually gates. Releasing anything else is a
        # re-roll wearing a disguise, and --reroll-trait is the flag for that.
        releasable = set()
        for table in args.overrides:
            releasable |= set(TRAIT_DEPENDENTS.get(table, ()))
        stray = [n for n in args.release if n not in releasable]
        if stray:
            p.error(
                "--release %s: not gated by %s. Releasable here: %s"
                % (", ".join(stray), ", ".join(sorted(args.overrides)),
                   ", ".join(sorted(releasable)) or "nothing"))

    args.gender_workflows = dict(GENDER_WORKFLOWS, woman=args.workflow_woman)

    # --trait-odds joins --regen-manifest in not needing one: it renders
    # nothing. Picking a run folder here is harmless in itself (the path is
    # only computed, not created), but it would make the odds query depend on
    # the output root existing and be readable, which it has no business
    # caring about.
    if args.out is None and not args.regen_manifest and not args.trait_odds:
        args.out = next_run_folder(default_root())

    return args


def workflow_for(args, npc):
    """The generation workflow this NPC's gender selects, else --workflow."""
    return args.gender_workflows.get(npc["_pronouns"]["gender"], args.workflow)


def resolve_recorded_workflow(entry, npc, args):
    """The workflow a stored manifest entry was rendered through, still on disk.

    The manifest records an absolute path, so every entry written before this
    repository was split out of the campaign hub names a location that no
    longer exists. Rather than fail the regen, fall back to the copy this
    repository packages under the same filename - the graphs moved with the
    split, so the basename still identifies the right one. The substitution is
    reported rather than swallowed: regenerating through a *different* workflow
    than the original would quietly stop reproducing the original art.
    """
    recorded = entry.get("workflow")
    if not recorded:
        # No entry this script has ever written is missing the field, but a
        # hand-edited manifest could be - pick what a fresh roll of this NPC
        # would use rather than dying on a KeyError traceback.
        fallback = workflow_for(args, npc)
        print("! entry records no workflow - falling back to %s" % fallback,
              file=sys.stderr)
        return fallback

    path = Path(recorded)
    if path.exists():
        return path

    packaged = art.WORKFLOW_DIR / path.name
    if packaged.exists():
        print("! recorded workflow path is stale (%s)\n"
              "  resolved by name to %s" % (path, packaged), file=sys.stderr)
        return packaged

    raise SystemExit(
        "Workflow not found: %s\n"
        "  and no workflow of that name is packaged here either: %s"
        % (path, packaged)
    )


def load_workflows(args, rolled):
    """Load and validate one template per workflow the roll actually needs.

    Every NPC is rolled before anything is queued, so the exact set of genders
    is known here. Checking just those fails fast on a missing or malformed
    workflow without demanding a women's workflow exist for an all-men run.
    """
    loaded = {}
    for _, npc, _ in rolled:
        path = workflow_for(args, npc)
        if path in loaded:
            continue
        if not path.exists():
            raise SystemExit("Workflow not found: %s" % path)
        template = art.load_api_workflow(path)
        try:
            slots = art.locate_slots(template)
        except art.WorkflowError as exc:
            raise SystemExit("%s: %s" % (path.name, exc))
        if not slots.latent:
            print("! %s has no EmptyLatentImage - portrait and token will share the "
                  "workflow's own size instead of 1024x1024 / 1024x1280"
                  % path.name, file=sys.stderr)
        loaded[path] = (template, slots)
    return loaded


# Which traits --reroll-trait can re-roll from an entry that recorded no raw
# bullets - every entry written before rawTraits existed.
#
# A reroll re-rolls ONE trait and keeps every other, so it has to apply the
# same filters the original roll applied - and roll_npc() strips a bullet's
# flags before storing it, so such an entry is a lossy record of the roll. A
# trait is rerollable only when every filter gating it can be rebuilt from what
# the entry DOES carry: the rolled Theme, the recorded 'young' flag, the stored
# Backdrop scene, the stored Pronouns.
#
# The repo already met this problem once and solved it one flag at a time:
# 'young' is a manifest key of its own precisely because the Age bullet's flag
# was gone by the time it was stored. Storing the raw bullets generalises that,
# and has since landed - so this tuple, and the hand-rebuilt filters in
# reroll_trait() that go with it, are now the fallback for old entries rather
# than the only path. An entry that carries its raw bullets uses
# RAW_REROLLABLE_TRAITS below instead, and none of this applies to it.
REROLLABLE_TRAITS = (
    "Callsigns", "Build", "Height", "Skin", "Hair", "Eyes", "Feature",
    "Demeanor", "Headgear", "Glow colour", "Glow placement",
)

# Why each of the others is refused, printed verbatim so the answer to "why
# not hair colour" is in the error rather than in this file.
#
# Both paths read this dict, and every entry has to be true on the path that
# prints it. Only three are reachable from an entry that recorded its raw
# bullets - the two halves of the name and Pronouns, refused for reasons the
# bullets do not touch. Every other entry here is now a legacy-path message
# and nothing else: cascading re-rolls made the rest re-rollable, so the only
# reader who can ever see them is the owner of an entry written before
# rawTraits existed.
#
# Which is why they say "this entry" rather than "the manifest". The earlier
# wording - "the manifest stores Role with its flags already stripped" - was
# a claim about the format, and the format no longer does that. Printed today
# it would tell the owner of a modern NPC something false about a file that
# has the flag right there in it, and send them looking for a limitation that
# has been fixed instead of at the one-line cure, which is to re-roll the NPC
# so its bullets get recorded.
UNREROLLABLE_REASONS = {
    "Given names": "the NPC's folder and manifest id are derived from its name, "
                   "so re-rolling one would not be a change in place",
    "Family names": "the NPC's folder and manifest id are derived from its name, "
                    "so re-rolling one would not be a change in place",
    "Pronouns": "every per-pronoun variant table is selected by it, so the whole "
                "NPC would have to re-roll with it",
    # The design doc's §4.2, which is the one refusal here written out in the
    # spec rather than in this file. It names Role, Outfit and Weapon because
    # those are the cascade's own worst case: a themed re-roll of the last two
    # is filtered on the first one's 'mil' flag, and this entry no longer has
    # it.
    "Theme": "this NPC was generated before raw bullets were recorded, so its "
             "Role's 'mil' flag is gone and a themed re-roll of its Outfit "
             "and Weapon could contradict it",
    "Role": "it gates Faction, Outfit and Weapon, which would all have to "
            "re-roll with it, and this entry stored every one of them with "
            "its flags already stripped",
    "Age": "its pairing with Build needs that bullet's 'figure' flag, and this "
           "entry stored Build with its flags already stripped",
    "Hair colour": "the rolled cut has the colour substituted into it and its "
                   "'{colour}' slot is gone, so there is nowhere to put a new one - "
                   "re-roll Hair instead, which picks a new cut in the same colour",
    "Faction": "its civ/mil filter needs the Role bullet's 'mil' flag, and this "
               "entry stored Role with its flags already stripped",
    "Outfit": "its civ/mil filter needs the Role bullet's 'mil' flag, and this "
              "entry stored Role with its flags already stripped",
    "Weapon": "its policy needs the Role bullet's 'mil' flag and the Outfit's "
              "'notac', and this entry stored both with their flags stripped",
    "Gear": "its filter needs the Weapon bullet's 'hands' flag, the Outfit's "
            "'notac' and the Headgear's 'helmet', and this entry stored all "
            "three with their flags stripped",
    "Stance": "its filter needs the Weapon and Gear 'hands'/'gun' flags, and this "
              "entry stored both with their flags stripped",
    "Backdrop": "Glow placement and Gear are filtered against it and Weather is "
                "gated by it, so re-rolling it would leave all three describing "
                "a scene that is gone, and this entry kept no bullets to re-roll "
                "them from",
    "Weather": "it is gated by the Backdrop bullet's 'weather' flag, and this "
               "entry stored Backdrop without its flag segment",
}

# Which traits --reroll-trait can re-roll from an entry that DID record its raw
# bullets - which is all but three of them, because nearly every refusal above
# is a complaint about the lossy manifest and nothing else. A pinned raw bullet
# arrives carrying the flags its dependents filter on, so reroll_from_raw()
# rebuilds no filter at all; it re-runs the roller's own.
#
# Theme is here now, and it is the reason this list grew by one. It was held
# back because it is not a one-free-variable re-roll - it gates seven
# appearance tables - and reroll_trait() had only one free variable to offer.
# It now frees a whole cascade, so the objection is answered rather than
# waived: the seven and their four dependents re-roll with it, under the
# roller's own filters, which is precisely what "would all have to re-roll
# with it" was asking for.
#
# Derived from REQUIRED_TABLES by exclusion rather than written out, so a table
# added there next month is re-rollable the day it is added rather than the day
# somebody remembers this line. The three it excludes are refused for reasons
# raw bullets and cascades both leave untouched: the NPC's folder and manifest
# id are derived from its name, so re-rolling either half of the name is not a
# change in place, and Pronouns selects every per-pronoun variant table and
# takes the name with it.
RAW_REROLLABLE_TRAITS = tuple(
    name for name in REQUIRED_TABLES
    if name not in ("Given names", "Family names", "Pronouns"))


def hair_colour_tail(tables, subject, base):
    """The trailing clause belonging to a stored Hair colour base, or ''.

    roll_npc() splits a Hair colour into base and tail, stores only the base
    under 'Hair colour', and appends the tail to the rendered Hair phrase - so
    a stored NPC's tail exists only inside a cut that is about to be replaced.
    Recovering it by base is exact rather than approximate: the bases are
    distinct shades, so at most one bullet matches.
    """
    for bullet in variant_table(tables, "Hair colour", subject):
        candidate, tail, _ = split_hair_colour(bullet)
        if candidate == base:
            return tail
    return ""


def draw_different_theme(tables, current, rng):
    """A theme from the table that is not `current`.

    A Theme re-roll that draws the theme it already had spends twelve traits
    and a render to produce a differently-dressed version of the same idea,
    which is not what the button says it does. So the new theme has to differ.

    The design doc words that as "repeat until it differs", and a reader who
    has read it will look for the retry loop here and not find one. There is
    none because there need not be: excluding the current theme from the pool
    and drawing once conditions the same weighted distribution on the same
    event that rejection sampling would, so the two are distribution-equivalent
    - and unlike a retry loop this cannot spin forever on a tables file that
    offers a single theme. The weighting survives the exclusion because
    parse_tables() expands an 'x2 alpha' bullet into two copies in a flat list,
    so dropping one theme's copies leaves every other theme in its original
    proportion to the rest.

    Drawn from tables["Theme"] directly rather than through variant_table(),
    matching roll_npc()'s own Theme draw: theme bullets are bare names with no
    per-pronoun variants and no flag segment, so there is nothing for
    variant_table() or split_flags() to unpack here.

    A file offering only one theme has no different theme to give. Re-rolling
    within it is still a real change - the seven themed tables redraw inside
    that theme, and so do the four traits that depend on them - so this
    proceeds with the theme it has rather than refusing, and says so on stderr
    so the result is not mistaken for a theme that failed to change.
    """
    others = [theme for theme in tables["Theme"] if theme != current]
    if not others:
        print("! the tables file offers only one theme (%r), so the re-roll "
              "keeps it - the themed tables will draw again within it rather "
              "than under a new one" % current, file=sys.stderr)
        return current
    return rng.choice(others)


def reroll_from_raw(tables, npc, free, rng, pinned=None):
    """Re-draw the traits in `free`, with every other raw bullet pinned.

    A re-roll is a fresh roll with one free variable, and a Theme cascade is
    the same operation with twelve - so this takes the free set as an argument
    and neither end knows about the other. `free` is any container of trait
    names; everything else npc["_raw"] recorded is pinned as an override.

    `pinned` is for the one trait in a cascade whose new value is chosen rather
    than drawn: it is merged over the overrides after the free set has been
    subtracted, so a trait can be freed - releasing everything downstream of it
    - and still arrive at a value this function's caller picked. Theme is the
    only user today. It has to be in `free`, or the eleven traits it gates
    would stay pinned to bullets tagged for the theme being replaced; and its
    own draw has to be conditional, or a re-roll would keep landing back on the
    theme the user asked to leave. Those two are not in conflict, they just
    cannot both be expressed by the free set alone.

    Pinning raw bullets is the designed use of the override path, not a trick:
    it is the one --set-trait already documents, a bullet handed over verbatim
    with its flags ('an elaborate floral kimono ... || civ notac'). So every
    pinned trait arrives carrying the flags its dependents filter on, every
    freed trait is drawn by the ordinary roller under the ordinary filters,
    and there is no second copy of the filter chain here to drift away from
    the one in roll_npc(). 'name' needs no pinning of its own: it is rebuilt
    from the pinned Given names and Family names by roll_npc() itself. A name
    hand-edited in the manifest is therefore not preserved - the rebuild comes
    from the bullets, so it wins. That is unreachable for a machine-written
    entry, whose stored name IS that rebuild, and pinning the stored one
    instead would let an edited name outlive the bullets it claims to be made
    of.

    The result replaces `npc` wholesale rather than being copied trait by
    trait, npc["_raw"] included, because the fresh roll's _raw holds the
    bullets this NPC now actually has. Keeping the old one would leave the
    regen writer persisting rawTraits that describe bullets the NPC no longer
    carries - traits and rawTraits silently disagreeing, which is the one risk
    both specs single out. The recomputed _young and _outfit_notac ride along
    for the same reason. Cleared and updated rather than rebound, because
    reroll_trait()'s contract is to mutate in place and regenerate_one() holds
    the reference.
    """
    # A table this entry has no bullet for cannot be pinned, so it rolls free
    # and the trait changes without having been asked for - the same silent
    # drift the two lists guard against everywhere else, arriving through the
    # gap between them: RAW_REROLLABLE_TRAITS is derived from REQUIRED_TABLES
    # and so admits a newly added table the day it is added, while a rawTraits
    # written before that day carries no bullet for it.
    #
    # Warn and proceed, which is this file's settled answer to a stored entry
    # that predates a table: migrate_traits() says so for a missing Headgear,
    # regenerate_one() for a missing Height and for an unrecorded 'young'.
    # Refusing instead would break the promise that a stored NPC keeps
    # regenerating, and pinning a fabricated value would be worse than either.
    # Anything in `free` is excluded: it was asked for, so it re-rolling is
    # the request rather than a surprise.
    unrecorded = [trait for trait in REQUIRED_TABLES
                  if trait not in npc["_raw"] and trait not in free]
    if unrecorded:
        print("! this entry recorded no raw bullet for: %s (written before "
              "that table existed) - a trait with nothing to pin re-rolls "
              "along with the one you named instead of being kept. Re-roll "
              "the NPC to record it." % ", ".join(unrecorded), file=sys.stderr)

    overrides = {trait: bullet for trait, bullet in npc["_raw"].items()
                 if trait not in free}
    overrides.update(pinned or {})
    fresh = roll_npc(tables, rng, overrides)
    npc.clear()
    npc.update(fresh)


def reroll_trait(tables, npc, name, rng):
    """Re-roll one trait of an already-rolled NPC in place, and return it.

    Two paths, chosen by whether the entry recorded its raw bullets. With them,
    the whole thing is one pinned re-roll through reroll_from_raw() and every
    trait but the name and Pronouns is re-rollable. Without them - an entry
    written before rawTraits existed - it falls back to rebuilding by hand the
    few filters a lossy entry still supports, which is the code below and the
    reason REROLLABLE_TRAITS is a much shorter list. Mutates `npc` either way.

    On the raw path the free set is the target's CASCADE rather than the target
    alone, and that is the whole of this function's half of the cascade design.
    Pinning filters in one direction only: the freed trait is drawn against
    everything pinned, but a pinned trait is never drawn, so nothing re-checks
    it against the value that just changed. Freeing Role alone left the kept
    Faction on the wrong side of the civ/mil line 138 times in 400 on the live
    tables. Freeing the cascade instead redraws every trait a filter would have
    had to reject, so the contradiction has nowhere left to appear. A trait
    nothing depends on closes to itself, so the eleven that already re-rolled
    cleanly take the identical path and still move nothing but themselves.
    """
    # Absent means the entry predates rawTraits, and the hand-written path is
    # exactly the fallback written for that. A recorded-but-empty dict takes
    # the same path deliberately rather than being read as "raw bullets, all
    # of them nothing": pinning nothing would re-roll the entire NPC under the
    # name of one trait, which is the opposite of what this function promises,
    # and there would be nothing in it to pin anyway.
    raw = npc.get("_raw")
    rerollable = RAW_REROLLABLE_TRAITS if raw else REROLLABLE_TRAITS
    if name not in rerollable:
        reason = UNREROLLABLE_REASONS.get(
            name, "it is not a trait this script rolls")
        # The set that applies, not the shorter one: an entry with raw bullets
        # can re-roll eleven traits the fallback refuses, and printing the
        # fallback's list to its owner would be a lie about their own NPC.
        #
        # And when raw bullets are the only thing standing in the way, the cure
        # goes in the message. Every reason above is a legacy-path reason now,
        # so a reader of one is being told about a limitation of their entry
        # rather than of this script, and the difference is only useful if the
        # fix is named. Derived from the two sets rather than written into each
        # reason, so it appears exactly when it is true - Pronouns and the two
        # halves of the name are refused whatever the entry recorded, and
        # telling their owner to re-roll the NPC would send them off to record
        # bullets that change nothing.
        #
        # The opening clause moves with it. "on its own" is the right words for
        # a trait this script will not re-roll for anybody - Pronouns takes the
        # whole NPC with it however the entry was written. It is the wrong
        # words for Theme on the lossy path, which is not refused on its own at
        # all: it cascades perfectly well from an entry that kept its bullets,
        # and is refused here because this particular entry did not.
        if raw or name not in RAW_REROLLABLE_TRAITS:
            refusal = "cannot re-roll that one on its own"
            offer = "Re-rollable: %s" % ", ".join(rerollable)
        else:
            refusal = "cannot re-roll that one from this entry"
            offer = ("Re-roll the NPC to record them, or re-roll a single "
                     "trait from: %s" % ", ".join(rerollable))
        raise SystemExit(
            "--reroll-trait %s: %s, because %s.\n%s"
            % (name, refusal, reason, offer))

    if raw:
        # Theme's new value is chosen rather than drawn, and it is the only
        # one: a cascade that landed back on the theme it started from would
        # spend twelve traits and a render producing a differently-dressed
        # version of the same idea, which is not what the user asked for. It
        # still travels in the free set, so the seven themed tables and their
        # four dependents draw again under the new theme instead of staying
        # pinned to bullets tagged for the old one.
        pinned = None
        if name == "Theme":
            pinned = {"Theme": draw_different_theme(tables, npc["Theme"], rng)}
        reroll_from_raw(tables, npc, trait_cascade(name), rng, pinned)
        return npc[name]

    subject = npc["Pronouns"].split("/")[0].strip().lower()
    options = variant_table(tables, name, subject)

    # Theme is stored as a trait, so its filter rebuilds exactly.
    if name in THEMED_TABLES:
        theme = npc.get("Theme", "-")
        options = filter_by_theme(options, theme, name)
        options = apply_theme_share(options, theme, name)

    # 'figure' against the recorded 'young' flag - the one flag the manifest
    # already stores separately, for this same reason.
    if name == "Build" and npc.get("_young"):
        grown = [x for x in options if "figure" not in split_flags(x)[1]]
        options = grown or options

    # 'scene' against the stored Backdrop, which keeps its scene segment.
    if name == "Glow placement" and not has_light_source(
            split_backdrop(npc["Backdrop"])[1]):
        on_figure = [x for x in options if "scene" not in split_flags(x)[1]]
        options = on_figure or options

    # 'hardtech' against the recorded outfit register - the second flag the
    # manifest stores separately, for the same reason 'young' is the first.
    # None means the entry predates the key, which is not the same as False:
    # it is "nobody knows", and the honest answer to that is today's
    # unrestricted behaviour plus a warning, not a fabricated 'plain'.
    if name == "Headgear":
        register = npc.get("_outfit_notac")
        if register is None:
            print("! this entry has no recorded outfit register (written before "
                  "the Headgear register existed) - re-rolling headgear "
                  "unrestricted, so it may come back with hard tech over a "
                  "traditional outfit. Re-roll the NPC to record it.",
                  file=sys.stderr)
        options = filter_by_hardtech(options, bool(register))

    # 'helmet' against the recorded Gear register - the third key the manifest
    # stores separately, for the same reason 'young' is the first. This runs
    # in the opposite direction to the roller's own filter, and it has to:
    # roll_npc() drops the carried helmet under a worn one because Headgear is
    # rolled first, but here the Gear is already fixed and the Headgear is the
    # free variable, so the worn helmets are what give way. Gear is in
    # UNREROLLABLE_REASONS on this path, so this is the only way back into the
    # clash that a legacy entry has.
    #
    # None means the entry predates the key, which is not the same as False:
    # it is "nobody knows", and the honest answer to that is today's
    # unrestricted behaviour plus a warning, not a fabricated 'no helmet'.
    if name == "Headgear":
        carried = npc.get("_gear_helmet")
        if carried is None:
            print("! this entry has no recorded gear register (written before "
                  "the helmet flag existed) - re-rolling headgear "
                  "unrestricted, so it may come back wearing a helmet while "
                  "carrying one. Re-roll the NPC to record it.",
                  file=sys.stderr)
        if carried:
            bare = [x for x in options if "helmet" not in split_flags(x)[1]]
            options = bare or options  # never filter the pool down to nothing

    # 'updo' against the recorded Hair register - the fourth key the manifest
    # stores separately. Same direction as the roller's own filter, since Hair
    # is drawn first there too: the hair is fixed and the Headgear is the free
    # variable, so the helmets are what give way.
    #
    # None means the entry predates the key, which is not the same as False,
    # and the honest answer is today's unrestricted behaviour plus a warning
    # rather than a fabricated 'lies flat'.
    if name == "Headgear":
        gathered = npc.get("_hair_updo")
        if gathered is None:
            print("! this entry has no recorded hair register (written before "
                  "the updo flag existed) - re-rolling headgear "
                  "unrestricted, so it may come back wearing a helmet over "
                  "hair gathered on the crown. Re-roll the NPC to record it.",
                  file=sys.stderr)
        if gathered:
            bare = [x for x in options if "helmet" not in split_flags(x)[1]]
            options = bare or options  # never filter the pool down to nothing

    # And the same pairing from the other side, which the carried-helmet one
    # has no equivalent of: Gear cannot be re-rolled on this path, but Hair
    # can, so a stored helmet has to gate the Hair pool too or the clash walks
    # straight back in through a one-click Hair re-roll.
    if name == "Hair":
        helmeted = npc.get("_headgear_helmet")
        if helmeted is None:
            print("! this entry has no recorded headgear register (written "
                  "before the updo flag existed) - re-rolling hair "
                  "unrestricted, so it may come back gathered on the crown "
                  "under a helmet. Re-roll the NPC to record it.",
                  file=sys.stderr)
        if helmeted:
            flat = [x for x in options if "updo" not in split_flags(x)[1]]
            options = flat or options  # never filter the pool down to nothing

    value = split_flags(rng.choice(options))[0]

    # A new cut takes the NPC's existing colour, and the tail that colour
    # carries - otherwise re-rolling the hair would quietly drop a gradient.
    if name == "Hair":
        base = npc["Hair colour"]
        value = value.replace("{colour}", base)
        tail = hair_colour_tail(tables, subject, base)
        if tail:
            value = "%s, %s" % (value, tail)

    if "{" in value:
        try:
            value = value.format(**npc["_pronouns"])
        except (KeyError, IndexError, ValueError) as exc:
            raise SystemExit(
                "table %r, option %r: %s is not a pronoun placeholder."
                % (name, value, exc))
    npc[name] = value
    return value


def trait_choices(tables, npc, name):
    """Which bullets `name` could take on this NPC, and what each would cost.

    Two questions per bullet, and they run in opposite directions.

    Upstream: could the roller have produced this bullet for this table, given
    the traits above it? That is `probe[name]` from a roll with the whole NPC
    pinned - the pool roll_npc() filtered, read back rather than recomputed.
    One roll answers it for the entire table at once, because a table's pool
    is built from the traits ABOVE it and those are pinned to this NPC's own
    bullets regardless of which candidate is being asked about.

    Downstream: if this bullet replaced the current one, would any trait BELOW
    it be left holding a value the roller would no longer offer? Pinning
    filters one way only - a pinned trait is never re-drawn, so nothing
    re-checks it against a gate that has just changed - which is exactly the
    contradiction class reroll_from_raw()'s cascade exists to prevent. Here
    the cascade is deliberately not run, because keeping the dependents is the
    point, so the contradiction is reported instead of avoided.

    The downstream pass runs over every edge in TRAIT_DEPENDENTS bar Weather,
    including the pairs roll_npc() already filters both ways (Headgear/Gear,
    Age/Build). For those it is redundant and simply agrees with the upstream
    pool. Redundant beats an exception list that has to be re-derived every
    time an edge is added: a stale exception reports a conflict that is not
    real, but a missed edge hides one that is.

    Weather is exempt because its edge is not a filter. Nothing narrows the
    Weather pool - the Backdrop's 'weather' flag is read at prompt-build time
    by weather_sentence() and decides only whether the rolled Weather is
    RENDERED. A kept Weather is therefore never illegal, only newly hidden or
    newly shown, and checking it would report every Backdrop in the table as
    conflicting.

    Nothing is dropped. Both answers ride on the entry and the caller decides:
    the picker this feeds greys ruled-out values and still lets them be
    chosen, which mirrors --set-trait's own long-standing behaviour of
    bypassing the roll pool. This function describes the pool; it does not
    enforce it.

    The rng is fixed rather than passed in. Every roll here is fully pinned,
    so nothing is actually drawn and the seed cannot reach the result - but a
    caller handing in a live rng would have its stream silently consumed by a
    query, a bug that would only ever surface as an unrelated NPC changing.
    """
    subject = npc["Pronouns"].split("/")[0].strip().lower()
    raw = dict(npc["_raw"])

    baseline = {}
    roll_npc(tables, random.Random(0), raw, probe=baseline)
    pool = set(baseline.get(name, ()))

    dependents = [d for d in TRAIT_DEPENDENTS.get(name, ()) if d != "Weather"]

    # Deduplicated, order preserved. variant_table() repeats a bullet once per
    # point of weight, because that is how the roller makes a heavier bullet
    # more likely - fine for rng.choice(), wrong for a list somebody reads: a
    # weight-30 bullet would appear thirty times in the picker, and "the value
    # this NPC is wearing" would match all thirty of them.
    #
    # Weight is not lost, it is just not this function's subject. What a
    # bullet's odds are is what --trait-odds answers.
    candidates = list(dict.fromkeys(variant_table(tables, name, subject)))

    out = []
    for bullet in candidates:
        current = bullet == raw.get(name)
        # The value it already has cannot contradict what it is already
        # wearing, and skipping it here is not an optimisation - running the
        # check would compare the NPC against itself and could only ever
        # report a conflict that predates this feature.
        if dependents and not current:
            forced = dict(raw, **{name: bullet})
            after = {}
            try:
                roll_npc(tables, random.Random(0), forced, probe=after)
            except SystemExit:
                # Two pairings are refused outright rather than filtered: a
                # 'young' Age with a 'figure' Build, and a 'plain' Role with a
                # 'dressy' Outfit. roll_npc() checks those after the loop,
                # where both values are known whether they were rolled or
                # forced, because a pool filter cannot catch a pair that was
                # BOTH forced - which is every pair in here.
                #
                # That refusal is a conflict of the hardest kind, so it is
                # reported as one. Which dependent caused it is asked of the
                # roller rather than parsed out of its message: free one at a
                # time and see which one makes the refusal go away. Costs at
                # most len(dependents) extra rolls, and only for a candidate
                # that raised at all.
                conflicts = []
                for d in dependents:
                    if d not in raw:
                        continue
                    trial = dict(forced)
                    del trial[d]
                    try:
                        roll_npc(tables, random.Random(0), trial, probe={})
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
            "heading": heading_for(tables, name, subject, bullet),
            "allowed": bullet in pool,
            "current": current,
            "conflicts": conflicts,
            "releases": sorted(releases),
        })
    return out


def print_trait_choices(args):
    """--trait-choices: which values one trait could take, as JSON.

    Prints to stdout and nothing else, because the caller parses stdout whole
    - the same contract --trait-odds already keeps, and the reason
    npc_from_entry() is asked not to warn here. Anything diagnostic goes to
    stderr.
    """
    manifest = art.load_manifest(args.regen_manifest)
    _, entry = find_regen_entry(manifest, args.regen_id, args.regen_manifest)
    npc = npc_from_entry(entry, args.regen_id, warn=False)

    # Pinning is what makes a chosen value mean anything, and a legacy entry
    # has nothing to pin: its stored bullets lost their flags on the way in, so
    # the filters this query reports on cannot run against them. Refused with
    # the cure named, the way reroll_trait() names it.
    raw = npc.get("_raw")
    if not raw:
        raise SystemExit(
            "--trait-choices %s: this entry recorded no raw bullets, so there "
            "is nothing to pin the rest of the NPC to. Re-roll the NPC to "
            "record them." % args.trait_choices)

    # The same list reroll_trait() would use for this entry, so a trait the
    # GUI is told it cannot choose is a trait it is also told it cannot
    # re-roll. Offering one without the other would be worse than neither.
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
        "choices": trait_choices(tables, npc, args.trait_choices),
    }, sys.stdout)
    return 0


def find_regen_entry(manifest, regen_id, manifest_path):
    """The (folder path, entry) pair for one id, or a refusal naming it."""
    folder_path, entry = next(
        ((k, v) for k, v in manifest.items() if isinstance(v, dict) and v.get("id") == regen_id),
        (None, None),
    )
    if entry is None:
        raise SystemExit("--regen-id %r: no such entry in %s" % (regen_id, manifest_path))
    return folder_path, entry


def npc_from_entry(entry, regen_id, warn=True):
    """A manifest entry rebuilt into the dict roll_npc() would have produced.

    Lifted out of regenerate_one() so that --trait-choices reads an entry the
    same way a regen does. Two reconstructions would drift, and the direction
    they would drift in is the worst one available: a query answering about a
    slightly different NPC than the one the regen is about to render.

    `warn` is off for the query, which is a read-only question a GUI may ask
    many times over. The migration notices belong on the run that actually
    writes something - and the query prints JSON to stdout, so a stray line
    would corrupt it besides.
    """
    npc = migrate_traits(entry["traits"])
    npc["_pronouns"] = pronoun_fields(npc["Pronouns"])
    if warn and "young" not in entry:
        print("! %s has no recorded 'young' flag (written by an older version of this script) - "
              "assuming not young; the maturity/face wording may drift slightly from the "
              "original render." % regen_id, file=sys.stderr)
    npc["_young"] = entry.get("young", False)
    # No default: absent is 'not recorded', which reroll_trait() distinguishes
    # from a recorded False. Unlike 'young' this is not consumed by
    # build_prompts(), so a plain regen neither needs it nor warns about it -
    # the warning belongs where the value is actually used.
    npc["_outfit_notac"] = entry.get("outfit_notac")
    # And the same again for the Gear's helmet register, absent for the same
    # reason and distinguished from a recorded False the same way.
    npc["_gear_helmet"] = entry.get("gear_helmet")
    # And the two halves of the hair/helmet pairing, absent for the same
    # reason and distinguished from a recorded False the same way. Both are
    # needed because both traits are re-rollable from an entry - see the pair
    # of keys roll_npc() publishes.
    npc["_hair_updo"] = entry.get("hair_updo")
    npc["_headgear_helmet"] = entry.get("headgear_helmet")
    # No default here either, for the same reason: absent means "not
    # recorded" (an entry written before rawTraits existed), and that has to
    # stay distinguishable from a recorded-but-empty dict. A plain regen never
    # looks at _raw, so it neither needs this nor is degraded by its absence -
    # the warning belongs where a consumer actually needs the raw bullets and
    # doesn't have them.
    if "rawTraits" in entry:
        # Renamed the same way entry["traits"] was above, two lines up - a
        # raw bullet stored under a name LEGACY_TRAIT_NAMES has since renamed
        # (Accent -> Glow colour) would otherwise sit under a key nothing
        # reads any more, silently rolling that trait free on every re-roll
        # from here on rather than pinning it, with only the "recorded no raw
        # bullet for" warning to notice. Only the rename: entry["rawTraits"]
        # holds raw bullets, not rendered text, so neither the Faction
        # repair nor the Headgear backfill applies to it - see
        # rename_legacy_traits().
        npc["_raw"] = rename_legacy_traits(entry["rawTraits"])
    if "Height" not in npc:
        if warn:
            print("! %s has no recorded Height trait (written before the Height table existed) - "
                  "regenerating without one; re-roll instead of regenerating to pick one up."
                  % regen_id, file=sys.stderr)
        npc["Height"] = "of average height"
    return npc


def regenerate_one(args):
    """Re-render one NPC's portrait and/or token from a stored manifest entry.

    Skips roll_npc and the tables file entirely - every trait comes from the
    entry exactly as it was originally rolled, so the prompt reproduces
    identically regardless of --new-seed. The entry's own folder is reused and
    overwritten in place (same filenames), unlike a fresh roll's npc_folder(),
    which suffixes rather than collides.
    """
    manifest = art.load_manifest(args.regen_manifest)
    folder_path, entry = find_regen_entry(manifest, args.regen_id, args.regen_manifest)
    npc = npc_from_entry(entry, args.regen_id)

    # One trait re-rolled - and, on the raw path, everything a filter would
    # have had to reject alongside it. Everything else reproduced. Seeded from
    # the entry's own seed so the same reroll of the same NPC is repeatable,
    # unless --new-seed asks for a different draw.
    rerolled = None
    if args.reroll_trait:
        if not args.tables.exists():
            raise SystemExit("--reroll-trait needs the tables file: %s" % args.tables)
        tables = parse_tables(args.tables)
        check_tables(tables, args.tables, getattr(parse_tables, "repeated", ()))
        # Snapshot before the re-roll replaces the dict wholesale, and every
        # trait rather than the named one: on the raw path a dozen of them can
        # move and the old values are gone once roll_npc() has run.
        #
        # Whether they will is read here too, for the same reason. A cascade is
        # what the raw path does and the lossy fallback re-rolls the one trait
        # it was asked for, so which report to print is decided by which path
        # is about to run - and reroll_from_raw() leaves no trace of _raw
        # having been there.
        before = {k: v for k, v in npc.items() if not k.startswith("_")}
        cascading = bool(npc.get("_raw"))
        rerolled = reroll_trait(
            tables, npc, args.reroll_trait,
            random.Random(args.new_seed if args.new_seed is not None else entry["seed"]))
        print("re-rolled %s: %r -> %r"
              % (args.reroll_trait, before.get(args.reroll_trait), rerolled))
        # Enumerated rather than summarised, which is the CLI's half of the
        # design doc's §6: somebody who re-rolls Theme expecting a new palette
        # gets a new outfit, weapon, hair and scene, and "and 11 others" would
        # let them find that out from the render. Every trait that travelled is
        # named even where it came back unchanged - a cascade re-draws it
        # either way, and printing only the movers would make an unlucky run
        # look like a smaller change than it was.
        for trait in (trait_cascade(args.reroll_trait) if cascading else ()):
            if trait != args.reroll_trait:
                print("  with %s: %r -> %r"
                      % (trait, before.get(trait), npc.get(trait)))

    # One trait pinned to a chosen value, everything else reproduced - the
    # mirror of the block above, which draws a value instead of taking one.
    if args.overrides:
        if not args.tables.exists():
            raise SystemExit("--set-trait needs the tables file: %s" % args.tables)
        tables = parse_tables(args.tables)
        check_tables(tables, args.tables, getattr(parse_tables, "repeated", ()))
        if not npc.get("_raw"):
            raise SystemExit(
                "--set-trait on a regen needs the entry's raw bullets, so the "
                "rest of the NPC has something to be pinned to. Re-roll the "
                "NPC to record them.")

        # The same list --reroll-trait accepts, and refused for the same
        # reasons - naming a value rather than drawing one does not make
        # Pronouns any safer to change under an NPC whose every appearance
        # bullet was drawn for the old subject, and the two halves of the name
        # decide the folder and the manifest id. A table that is not rolled at
        # all is refused here too, rather than passed to roll_npc() where an
        # override for a table it has never heard of is silently dropped: a
        # typo would otherwise regenerate the NPC unchanged and report success.
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
        # Re-running roll_npc() rather than assigning npc[table] directly is
        # the point: _young, _outfit_notac, _gear_helmet, the '{colour}' fill
        # and the flag stripping all recompute, and _raw ends up describing the
        # NPC about to be rendered rather than the one it replaced.
        #
        # A released trait travels as its whole cascade. Freeing the bare name
        # would redraw it and leave everything it gates pinned to bullets
        # chosen for the value that just went - the same contradiction one
        # level down, which is what trait_cascade() exists to close.
        free = set()
        for name in args.release:
            free |= set(trait_cascade(name))
        before = {k: v for k, v in npc.items() if not k.startswith("_")}
        reroll_from_raw(
            tables, npc, free,
            random.Random(args.new_seed if args.new_seed is not None else entry["seed"]),
            dict(args.overrides))
        for table in args.overrides:
            print("set %s: %r -> %r" % (table, before.get(table), npc.get(table)))
        # Named rather than counted, for the same reason the re-roll cascade
        # above names its own: a release reaches further than the trait the
        # user typed, and finding that out from the render is the failure this
        # report exists to prevent.
        for trait in sorted(free):
            if trait not in args.overrides:
                print("  with %s: %r -> %r"
                      % (trait, before.get(trait), npc.get(trait)))

    seed = args.new_seed if args.new_seed is not None else entry["seed"]
    prompts = build_prompts(npc)
    portrait_prompt, token_prompt = prompts
    category = role_category(npc)
    folder = Path(folder_path)
    stem = _safe(npc["name"])
    slug = art._slug(npc["name"])

    print("regenerating %s  \"%s\"  seed=%d -> %s" % (npc["name"], npc["Callsigns"], seed, folder))

    workflow_path = resolve_recorded_workflow(entry, npc, args)
    template = art.load_api_workflow(workflow_path)
    try:
        slots = art.locate_slots(template)
    except art.WorkflowError as exc:
        raise SystemExit("%s: %s" % (workflow_path.name, exc))

    post_template = post_slots = None
    if not args.no_token:
        if not args.rmbg.exists():
            raise SystemExit("Background-removal workflow not found: %s" % args.rmbg)
        post_template = art.load_api_workflow(args.rmbg)
        try:
            post_slots = art.locate_post_slots(post_template)
        except art.WorkflowError as exc:
            raise SystemExit("%s: %s" % (args.rmbg.name, exc))

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
        knobs = Knobs(args, TOKEN_SIZE, COMFY_PREFIX)
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
            print("    token ...", flush=True)
            raw = render(token_prompt, "token", TOKEN_SIZE)[0]
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
    write_dossier(dossier, npc, seed, prompts, written)
    if dossier.name not in written:
        written.append(dossier.name)

    entry["seed"] = seed
    entry["files"] = written
    entry["portrait"] = portrait_file
    entry["portraitPrompt"] = portrait_prompt
    entry["token"] = token_file
    entry["tokenPrompt"] = token_prompt
    entry["young"] = npc["_young"]
    # Only when it is known. Rewriting an entry that predates the key with a
    # fabricated False would claim the outfit is not 'notac' when nothing here
    # knows either way, and a later re-roll would then trust the fabrication.
    if npc.get("_outfit_notac") is not None:
        entry["outfit_notac"] = npc["_outfit_notac"]
    if npc.get("_gear_helmet") is not None:
        entry["gear_helmet"] = npc["_gear_helmet"]
    if npc.get("_hair_updo") is not None:
        entry["hair_updo"] = npc["_hair_updo"]
    if npc.get("_headgear_helmet") is not None:
        entry["headgear_helmet"] = npc["_headgear_helmet"]
    # Only when a trait actually changed: a plain regen reproduces the entry
    # and rewriting traits it did not touch would just churn the manifest.
    if rerolled is not None:
        entry["traits"] = {k: v for k, v in npc.items() if not k.startswith("_")}
        # Only when _raw is actually known. A legacy entry loaded above with
        # no rawTraits leaves npc["_raw"] unset, and this regen never had raw
        # bullets to begin with - writing some in now would invent a
        # provenance the entry never actually had.
        if npc.get("_raw") is not None:
            entry["rawTraits"] = dict(npc["_raw"])
    entry["when"] = time.strftime("%Y-%m-%d %H:%M:%S")
    manifest[folder_path] = entry
    art.save_manifest(args.regen_manifest, manifest)

    print("done: %s" % folder)
    return 0


def main(argv=None):
    args = parse_args(argv)

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
                   "tables": trait_odds(tables, args.trait_odds, rng)},
                  sys.stdout)
        return 0

    unknown = [t for t in args.overrides if t not in REQUIRED_TABLES and t != "name"]
    if unknown:
        raise SystemExit(
            "--set-trait: unknown table(s) %s. Known: %s"
            % (", ".join(unknown), ", ".join(REQUIRED_TABLES))
        )

    # --pronouns already validates against the Pronouns table via
    # resolve_pronouns(); --set-trait Pronouns= bypasses that path entirely,
    # which is how a subject the table no longer offers (they/them, removed
    # for reading back androgynous - see the Pronouns table's own comment)
    # could still be forced back in. Same check, same error shape, so both
    # paths agree on what's actually selectable.
    if "Pronouns" in args.overrides:
        subject = args.overrides["Pronouns"].split("/")[0].strip().lower()
        known = {b.split("/")[0].strip().lower() for b in tables["Pronouns"]}
        if subject not in known:
            raise SystemExit(
                "--set-trait Pronouns=%r: no such subject in the Pronouns table. "
                "Available: %s" % (args.overrides["Pronouns"], ", ".join(sorted(known)))
            )

    # Same check, same shape, for the same class of mistake: a forced Theme the
    # table doesn't offer used to resolve in silence to an all-neutral roll.
    # The empty string is the sharper case - it is falsy, so roll_npc() rolls a
    # real theme and filters every themed pool with it, and then
    # npc.update(overrides) pastes the empty value back over the record. The
    # dossier would report no theme for an NPC that was themed, contradicting
    # the line it prints promising that this seed reproduces this NPC exactly.
    if "Theme" in args.overrides:
        known = sorted(set(tables["Theme"]))
        if args.overrides["Theme"] not in known:
            raise SystemExit(
                "--set-trait Theme=%r: no such theme in the Theme table. "
                "Available: %s" % (args.overrides["Theme"], ", ".join(known))
            )

    base_seed = args.seed if args.seed is not None else random.randint(0, 2 ** 32 - 1)
    overrides = dict(args.overrides)
    if args.name:
        overrides["name"] = args.name
    if args.pronouns:
        overrides["Pronouns"] = resolve_pronouns(tables, args.pronouns)

    rolled = []
    for n in range(args.count):
        seed = base_seed + n
        npc = roll_npc(tables, random.Random(seed), overrides, args.unarmed)
        rolled.append((seed, npc, build_prompts(npc)))

    print("%s: %d tables, %d NPC(s) rolled from base seed %d" % (
        args.tables.name, len(tables), args.count, base_seed))
    print("output root: %s" % args.out)

    if args.dry_run:
        for seed, npc, (portrait_prompt, token_prompt) in rolled:
            print("\n  %s  \"%s\"  (seed %d)" % (npc["name"], npc["Callsigns"], seed))
            print("    %s, %s" % (npc["Role"], split_faction(npc["Faction"])[0]))
            print("    -> %s" % (npc_folder(args.out, npc["name"], role_category(npc), args.overwrite)))
            print("    workflow %s" % workflow_for(args, npc).name)
            if not args.no_portrait:
                print("    portrait %dx%d ~%d tok:" % (
                    PORTRAIT_SIZE + (estimate_tokens(portrait_prompt),)))
                print("        %s" % portrait_prompt)
            if not args.no_token:
                print("    token    %dx%d ~%d tok:" % (
                    TOKEN_SIZE + (estimate_tokens(token_prompt),)))
                print("        %s" % token_prompt)
        stages = (0 if args.no_portrait else 1) + (0 if args.no_token else 2)
        print("\ndry run OK - %d job(s) would be queued" % (len(rolled) * stages))
        return 0

    workflows = load_workflows(args, rolled)

    post_template = post_slots = None
    if not args.no_token:
        if not args.rmbg.exists():
            raise SystemExit("Background-removal workflow not found: %s" % args.rmbg)
        post_template = art.load_api_workflow(args.rmbg)
        try:
            post_slots = art.locate_post_slots(post_template)
        except art.WorkflowError as exc:
            raise SystemExit("%s: %s" % (args.rmbg.name, exc))

    comfy = art.find_server(args.server)
    print("ComfyUI: %s" % comfy.base)
    manifest = art.load_manifest(args.manifest)

    def render(npc, prompt, category, slug, stage, size, seed):
        """Queue one text -> image job and return the images it produced."""
        template, slots = workflows[workflow_for(args, npc)]
        knobs = Knobs(args, size, COMFY_PREFIX)
        job = art.build_job(template, slots, entry_for(category, slug, stage, prompt), seed, knobs)
        record = comfy.wait(comfy.queue(job), timeout=args.timeout)
        images = comfy.images(record)
        if not images:
            raise RuntimeError("the %s job produced no image" % stage)
        return images

    def remove_background(image, category, slug, seed):
        knobs = Knobs(args, TOKEN_SIZE, COMFY_PREFIX)
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

    for index, (seed, npc, prompts) in enumerate(rolled, 1):
        portrait_prompt, token_prompt = prompts
        category = role_category(npc)
        folder = npc_folder(args.out, npc["name"], category, args.overwrite)
        slug = art._slug(npc["name"])
        stem = _safe(npc["name"])
        tag = "[%d/%d]" % (index, len(rolled))

        print("\n%s %s  \"%s\"  seed=%d" % (tag, npc["name"], npc["Callsigns"], seed))
        print("    %s, %s" % (npc["Role"], split_faction(npc["Faction"])[0]))

        written = []
        portrait_file = token_file = None
        try:
            folder.mkdir(parents=True, exist_ok=True)

            if not args.no_portrait:
                print("    portrait ...", flush=True)
                image = render(npc, portrait_prompt, category, slug, "portrait", PORTRAIT_SIZE, seed)[0]
                portrait_file = fetch(comfy, image, folder / ("%s Portrait.png" % stem)).name
                written.append(portrait_file)
                print("      -> %s" % written[-1])
                time.sleep(args.pause)

            if not args.no_token:
                print("    token ...", flush=True)
                raw = render(npc, token_prompt, category, slug, "token", TOKEN_SIZE, seed)[0]
                if args.keep_raw_token:
                    written.append(
                        fetch(comfy, raw, folder / ("%s Token (raw).png" % stem)).name)
                time.sleep(args.pause)
                print("      + background removal", flush=True)
                cut = remove_background(raw, category, slug, seed)
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
        write_dossier(dossier, npc, seed, prompts, written)
        written.append(dossier.name)
        print("    -> %s" % folder)

        done += 1
        manifest[str(folder)] = {
            # Deterministic from name+seed so a --overwrite rerun of the same
            # NPC reuses it rather than minting a new one - this is what the
            # Foundry importer keys its "already imported" tracking on.
            "id": "npc-%s-%d" % (slug, seed),
            "kind": "npc",
            "name": npc["name"],
            "callsign": npc["Callsigns"],
            "seed": seed,
            "tables": str(args.tables),
            "workflow": str(workflow_for(args, npc)),
            "traits": {k: v for k, v in npc.items() if not k.startswith("_")},
            # _raw is dropped by the dict comprehension above along with every
            # other '_'-prefixed key, so it has to be written out explicitly
            # here to survive at all. It is the bullets traits was built from,
            # flags and all - traits alone has already lost the 'mil' off a
            # Role or the 'notac' off an Outfit, which Faction, Weapon and
            # Headgear filter on, so a --reroll-trait against a stored NPC
            # needs this to see what its sibling traits actually require.
            "rawTraits": dict(npc["_raw"]),
            # Not itself a table roll, so it lives beside traits rather than in
            # it - --regen-manifest reads it back to pick the right MATURITY/
            # FACE clause without re-deriving it from the (already flag-
            # stripped) Age text.
            "young": npc["_young"],
            # Not a table roll either, and stored for the same reason: a
            # Headgear re-roll needs the Outfit bullet's 'notac' flag, and
            # traits are saved with their flags already stripped.
            "outfit_notac": npc["_outfit_notac"],
            # And the third, for the same reason again: that same Headgear
            # re-roll needs the Gear bullet's 'helmet' flag, to know whether
            # the figure is already holding one.
            "gear_helmet": npc["_gear_helmet"],
            # The fourth and fifth, for the hair/helmet pairing. A Headgear
            # re-roll needs the Hair bullet's 'updo' flag and a Hair re-roll
            # needs the Headgear bullet's 'helmet' one - both traits are
            # re-rollable, so the clash is reachable from either side.
            "hair_updo": npc["_hair_updo"],
            "headgear_helmet": npc["_headgear_helmet"],
            "files": written,
            "portrait": portrait_file,
            "portraitPrompt": portrait_prompt,
            "token": token_file,
            "tokenPrompt": token_prompt,
            "dossier": dossier.name,
            "when": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        art.save_manifest(args.manifest, manifest)

    print("\ndone: %d/%d generated, %d failed, %.1f min\nmanifest: %s" % (
        done, len(rolled), failed, (time.time() - started) / 60, args.manifest))
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
