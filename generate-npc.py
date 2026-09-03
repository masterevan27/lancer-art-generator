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
"""

from __future__ import annotations

import argparse
import importlib.util
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
REQUIRED_TABLES = [
    "Given names", "Family names", "Callsigns", "Pronouns", "Theme", "Age",
    "Build", "Height", "Skin", "Hair", "Eyes", "Feature", "Demeanor", "Role",
    "Faction", "Outfit", "Headgear", "Weapon", "Gear", "Accent", "Backdrop",
    "Weather", "Stance",
]

# The tables a rolled Theme gates. Everything else - names, age, build, height,
# skin, eyes, accent, weather, stance - describes the person or the moment
# rather than the visual world they come from, and stays untouched by theme.
# Gear is deliberately absent: what is left of it after the Weapon split is
# data-slates, tool bags and thermoses, which no theme owns. Weapon is here
# because armament is the most theme-defining object a figure carries.
# Phase 2 adds "Hair colour" when that table exists.
THEMED_TABLES = ("Hair", "Feature", "Outfit", "Headgear", "Weapon", "Backdrop")

# Krea 2 conditions on at most 512 tokens and silently truncates the rest, so a
# prompt that runs long loses its tail - which is where the palette, the flat
# white background and the closing style tags live. Measured against ComfyUI's
# own Qwen2 tokenizer over 9000 generated prompts, this file averages 4.8
# characters per token; the estimate is deliberately pessimistic at 4.5 so the
# warning fires before the server actually truncates.
TOKEN_LIMIT = 512
CHARS_PER_TOKEN = 4.5


def estimate_tokens(text):
    return int(len(text) / CHARS_PER_TOKEN)


# Words a rolled Gear, Outfit, Headgear, Feature, Eyes or Backdrop-scene bullet
# already uses when it describes something that would actually cast colored
# light - a lit instrument panel, a glowing seam, a neon sign, a muzzle flash.
# The accent-glow sentences below only fire when at least one rolled bullet
# matches, so the "faint {accent} glow" they describe always has something in
# frame to have cast it, rather than landing on a scene with no light source
# at all (a mech hangar in shadow, a dropship bay door against a plain sky).
# Deliberately excludes plain daylight/dusk words like "sun" or "sunlit" -
# natural light doesn't motivate an arbitrary saturated accent color either.
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
# the mil/civ split - see apply_weapon_policy(). A category with no entry
# here rolls Weapon exactly as it always has: no filter, no bias.
WEAPON_POLICY = {
    "Officials": "restricted",
    "Criminals": "armed_bias",
}

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
    "{skin}, {hair}, {eyes}, and {feature}, wearing {outfit}, {faction}, the clothing "
    "following the shape of that frame. {headgear} {Possessive} face carries {demeanor}. "
    "{gear_line}{backdrop} {weather_line}{accent_line} "
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
TOKEN_TEMPLATE = (
    "A full-body character illustration of {role}, {maturity} {gender} {age}, "
    "rendered in a detailed painterly illustration style with fine grain texture, clean "
    "linework and halftone dot shading worked into the shadows, moody cinematic lighting "
    "on the figure. {Subject} {is_are} "
    "standing at full height facing the viewer, entire body visible from the top of "
    "{possessive} head to the soles of {possessive} plain modern boots, no leg wraps or "
    "puttees, with clear empty space above and below, in realistic adult proportions "
    "roughly seven to eight heads tall. "
    "{Subject} {is_are} {height}, {build}, with {traits}{skin}, {hair}, {eyes}, and {feature}, wearing "
    "{outfit}, {faction}, the clothing following the shape of that frame. {headgear} "
    "{Possessive} face carries {demeanor}. {gear_line}{Subject} {is_are} {stance}, both "
    "boots planted and fully visible, the pose relaxed and natural with the arms free. "
    "{accent_line} The background alone is a solid flat plain white, no "
    "texture, no gradient, no shadow, no environment. Centered composition, dramatic "
    "lighting, isolated character illustration, clean silhouette, painterly brushwork "
    "with heavy grain and dense halftone screentone worked into every shadow."
)

# The two forms {accent_line} takes, gated on has_light_source() - see there
# for why. The "with" case keeps the original wording verbatim; the "without"
# case drops the accent color entirely rather than inventing a source for it.
ACCENT_PORTRAIT = (
    "A faint {accent} glow falls across one side of {possessive} face against "
    "warm dim ambient light on the other. Keep the palette restrained - greys, "
    "olive drab and rust - with {accent} the only saturated color in the frame."
)
ACCENT_PORTRAIT_NONE = (
    "Keep the palette restrained - greys, olive drab and rust, with no stray "
    "saturated color."
)
ACCENT_TOKEN = (
    "Keep the palette restrained - greys, olive drab and rust - with a single "
    "{accent} glow the only saturated color."
)
ACCENT_TOKEN_NONE = (
    "Keep the palette restrained - greys, olive drab and rust, with no stray "
    "saturated color."
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


def filter_by_mil(options, mil):
    """Faction/Outfit bullets flagged 'civ' or 'mil', filtered by a military Role.

    A bullet flagged 'civ' reads as plainly civilian dress and is dropped when
    the NPC's Role came up flagged 'mil' - a soldier should not turn up in a
    cropped tank top and cut-offs. One flagged 'mil' reads as an actual issued
    uniform and is dropped for a civilian Role instead, per the brief:
    civilians may carry any gear they like, including military-issue weapons,
    but shouldn't appear in uniform unless they used to serve. An unflagged
    bullet is neutral and reachable either way, the same as an untagged
    Gear/Stance entry - never filtered down to nothing.
    """
    exclude = "civ" if mil else "mil"
    plain = [x for x in options if exclude not in split_flags(x)[1]]
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
    direction that bites: measured against THEME_SHARE at 0.6, a
    military-leaning theme's Gear realized 0.76, while a theme whose only
    tagged Outfit is 'civ' realized 0.36 on that table, because filter_by_mil
    drops that bullet outright for a military Role. A theme authored entirely
    on one side of the civ/mil split is invisible to roles on the other side
    whatever `share` says - see `python -m test.theme_visibility`.

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


def apply_weapon_policy(options, category, mil):
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

    Any other category - or a tables file with no 'weapon'/'sidearm' flags at
    all - rolls Weapon exactly as before: untouched.
    """
    if mil:
        armed = [x for x in options if "sidearm" in split_flags(x)[1]]
        return armed or options

    policy = WEAPON_POLICY.get(category)
    if policy == "restricted":
        pocketable = [
            x for x in options
            if "weapon" not in split_flags(x)[1] or "simple" in split_flags(x)[1]
        ] or options
        unarmed = [x for x in pocketable if "weapon" not in split_flags(x)[1]]
        return pocketable + unarmed * 5 if unarmed else pocketable
    if policy == "armed_bias":
        tagged = [x for x in options if "weapon" in split_flags(x)[1]]
        return options + tagged * 4 if tagged else options
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


def roll_npc(tables, rng, overrides=None):
    """One NPC as a flat dict of trait -> rolled text."""
    # Pronouns first: every other table may have a per-pronoun variant, so the
    # roll that selects between them has to happen before the rest.
    pronouns = (overrides or {}).get("Pronouns") or rng.choice(tables["Pronouns"])
    subject = pronouns.split("/")[0]

    # Age, Role and Outfit are all resolved up front, for the same reason
    # Pronouns is: each one's flag gates a later roll, so an override has to
    # be in hand before that later table is rolled rather than pasted over
    # the result afterwards. Pass the flag to keep it, as in
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

    # Theme is rolled before every appearance table it gates, for the same
    # reason Pronouns is: the roll that selects between pools has to happen
    # before those pools are drawn from. It is deliberately NOT gated on Role -
    # a pirate should be as likely to look neosamurai as cyberpunk - so nothing
    # here reads npc["Role"].
    theme = (overrides or {}).get("Theme") or rng.choice(tables["Theme"])

    npc = {"Pronouns": pronouns, "Theme": theme}
    young = False
    role_mil = False
    outfit_notac = False
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

        # Build is filtered against the Age roll, the same way Stance is
        # filtered against Gear below. An Age bullet flagged 'young' is a
        # teenager; the Build bullets flagged 'figure' describe an adult
        # woman's - bust, hips, waist - and the two must never be combined.
        # Age precedes Build in REQUIRED_TABLES, so the flag is known by the
        # time this runs; keep it that way if the list is ever reordered.
        if name == "Build" and young:
            plain = [x for x in options if "figure" not in split_flags(x)[1]]
            options = plain or options     # never filter the pool down to nothing

        # Faction and Outfit are filtered against the Role roll the same way:
        # a Role flagged 'mil' excludes bullets flagged 'civ' and vice versa,
        # so a soldier doesn't turn up in a cropped tank top and a dockworker
        # doesn't turn up in a dress uniform. Gear isn't filtered at all - a
        # civilian may carry military gear same as anyone - just biased
        # toward its 'mil'-flagged bullets when the Role calls for it. Role
        # precedes all three in REQUIRED_TABLES, so role_mil is already known.
        if name in ("Faction", "Outfit"):
            options = filter_by_mil(options, role_mil)

        # A weapon that occupies the hands rules out equipment that also needs
        # one. Weapon precedes Gear in REQUIRED_TABLES so this flag is already
        # known, the same way Role precedes Faction and Outfit. Gear is what
        # yields: the weapon is the more theme-defining object, and dropping a
        # thermos costs nothing.
        if name == "Gear" and weapon_hands:
            free = [x for x in options if "hands" not in split_flags(x)[1]]
            options = free or options      # never filter the pool down to nothing

        # 'notac' applies to both halves of the old Gear table: an elaborate or
        # traditional outfit should pair with neither a military-issue rifle
        # nor a military-issue radio. Restricting only the Weapon would leave a
        # kimono carrying a tactical assault pack.
        if name in ("Weapon", "Gear") and outfit_notac:
            no_mil = [x for x in options if "mil" not in split_flags(x)[1]]
            options = no_mil or options
        if name == "Weapon":
            options = apply_weapon_policy(
                options, ROLE_CATEGORIES.get(npc["Role"]), role_mil)

        # Rolled either way, so that forcing a trait does not shift the rest
        # of the run's random stream and change every NPC after it. The
        # exception is a forced trait that *filters* a later pool - the
        # Age/Build pairing above, and the Gear and Stance filters below -
        # since a shorter pool draws differently. Those already behaved this
        # way for a rolled trait; forcing one just makes it reachable sooner.
        value = rng.choice(options)
        if name == "Age" and forced_age is not None:
            value = forced_age
        if name == "Role" and forced_role is not None:
            value = forced_role
        if name == "Outfit" and forced_outfit is not None:
            value = forced_outfit
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
        # Backdrop is the one themed table still absent: its '||' separates
        # three fields rather than two and is parsed by split_backdrop
        # downstream, which is where its flags are read. Gear is absent for
        # an unrelated reason - its own flags gate the Stance roll further
        # down, so it is split there instead.
        if name in ("Age", "Build", "Role", "Faction", "Outfit",
                    "Hair", "Feature", "Headgear", "Weapon"):
            value, flags = split_flags(value)
            if name == "Age":
                young = "young" in flags
            if name == "Role":
                role_mil = "mil" in flags
            if name == "Outfit":
                outfit_notac = "notac" in flags
            if name == "Weapon":
                weapon_hands = "hands" in flags
                weapon_flags = flags
        npc[name] = value

    npc["_young"] = young

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
    stances = [split_flags(x) for x in variant_table(tables, "Stance", subject)]
    if "gun" not in carried_flags:
        unarmed = [x for x in stances if "gun" not in x[1]]
        stances = unarmed or stances       # never filter the pool down to nothing
    if "hands" in carried_flags:
        free = [x for x in stances if "hands" not in x[1]]
        stances = free or stances          # never filter the pool down to nothing
    npc["Stance"] = rng.choice(stances)[0]

    # A 'nogear' backdrop has the subject's hands full of whatever the scene
    # handed them, so a thermos held in one of them contradicts the picture.
    # Backdrop is rolled after Gear, so this re-rolls rather than filtering a
    # pool - the one place in this function that does, and only because the
    # dependency runs backwards.
    #
    # Read from overrides first, falling back to the rolled value - the same
    # pattern Pronouns and Theme use above. npc.update(overrides) hasn't run
    # yet at this point in the function, so a forced Backdrop (--set-trait, or
    # a test's override dict) would otherwise be invisible here and this
    # filter would key off the random roll it was meant to replace.
    effective_backdrop = (overrides or {}).get("Backdrop", npc["Backdrop"])
    if "nogear" in split_backdrop(effective_backdrop)[2] and "hands" in gear_flags:
        free = [x for x in variant_table(tables, "Gear", subject)
                if "hands" not in split_flags(x)[1]]
        if free:
            npc["Gear"], gear_flags = split_flags(rng.choice(free))

    npc.update(overrides or {})
    npc["Age"] = split_flags(npc["Age"])[0]   # the override still carries its flag
    # Same reason as Age: a --set-trait override for any of these pastes the
    # raw bullet text back over the split-out value above, flag and all.
    npc["Role"] = split_flags(npc["Role"])[0]
    npc["Faction"] = split_flags(npc["Faction"])[0]
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

    # Build needs the same unpacking, and for a second reason beyond tidiness:
    # the pool filters above only screen a *rolled* pool, so a pair of forced
    # traits walks straight past both of them. Re-check the pairing here, where
    # each flag is known whether it was rolled or forced. Only the both-forced
    # case can still reach this: a forced Build narrows the Age roll and a
    # forced Age narrows the Build roll, so either one alone resolves quietly.
    build, build_flags = split_flags(npc["Build"])
    if young and "figure" in build_flags:
        raise SystemExit(
            "--set-trait Age and --set-trait Build disagree: a bullet flagged "
            "'figure' describes an adult woman's build and must not be "
            "combined with an Age flagged 'young'. Force only one of the two "
            "and the other will roll to match, or drop a flag."
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
    means. Age and Build reuse the same split for their own unrelated flags,
    'young' and 'figure', and so do Role ('mil', an active-duty military or
    paramilitary occupation), Faction/Outfit ('civ' or 'mil', filtered
    against the Role flag - see filter_by_mil()) and Outfit's own 'notac'
    (read in roll_npc() to keep tactical Weapon and Gear off a handful of
    outfits).
    """
    text, _, rest = bullet.partition("||")
    return text.strip(), tuple(f for f in rest.split() if f)


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


def flags_for(name, bullet):
    """A bullet's flag tuple, whichever '||' shape its table uses.

    Backdrop bullets carry three segments and keep their flags in the third,
    so a two-segment Backdrop has no flags at all - its second segment is the
    scene. Every other table keeps flags in the second segment. Reading the
    last segment blindly would mistake a Backdrop's scene text for flags.
    """
    if name == "Backdrop":
        return split_backdrop(bullet)[2]
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
    produces an unarmed NPC, and a 'nogear' Backdrop suppresses the whole
    sentence on the portrait - see build_prompts() - because the scene already
    put one in their hands.
    """
    carried = [x for x in (weapon, gear) if x]
    if not carried:
        return ""
    return "{Subject} {carry} %s. ".format(**fields) % " and ".join(carried)


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
        "faction": npc["Faction"],
        "demeanor": npc["Demeanor"],
        "weapon": weapon,
        "gear": npc["Gear"],
        "accent": npc["Accent"],
        "shot": shot,
        "backdrop": scene,
        "stance": npc["Stance"],
    })
    weather = weather_sentence(npc)
    fields["weather_line"] = weather + " " if weather else ""

    # Built from the same fields and inserted already-substituted, since
    # str.format does a single pass and would leave any nested placeholder raw.
    carrying = carry_sentence(fields, weapon, npc["Gear"])

    # The accent glow only belongs in the prompt when something rolled for
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
        accent_line=(ACCENT_PORTRAIT if portrait_glow else ACCENT_PORTRAIT_NONE).format(**fields))
    token_fields = dict(
        fields, gear_line=carrying,
        accent_line=(ACCENT_TOKEN if equipped_glow else ACCENT_TOKEN_NONE).format(**fields))

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
        ("Affiliation", npc["Faction"]),
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
        ("Accent color", npc["Accent"]),
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
        '"%s" - %s, %s.' % (npc["Callsigns"], npc["Role"], npc["Faction"]),
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

    run = p.add_argument_group("run mode")
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
        conflicting = [
            flag for flag, given in (
                ("--count", args.count != 1), ("--seed", args.seed is not None),
                ("--name", bool(args.name)), ("--pronouns", bool(args.pronouns)),
                ("--set-trait", bool(args.set_trait)),
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

    args.gender_workflows = dict(GENDER_WORKFLOWS, woman=args.workflow_woman)

    if args.out is None and not args.regen_manifest:
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


def regenerate_one(args):
    """Re-render one NPC's portrait and/or token from a stored manifest entry.

    Skips roll_npc and the tables file entirely - every trait comes from the
    entry exactly as it was originally rolled, so the prompt reproduces
    identically regardless of --new-seed. The entry's own folder is reused and
    overwritten in place (same filenames), unlike a fresh roll's npc_folder(),
    which suffixes rather than collides.
    """
    manifest = art.load_manifest(args.regen_manifest)
    folder_path, entry = next(
        ((k, v) for k, v in manifest.items() if isinstance(v, dict) and v.get("id") == args.regen_id),
        (None, None),
    )
    if entry is None:
        raise SystemExit("--regen-id %r: no such entry in %s" % (args.regen_id, args.regen_manifest))

    npc = dict(entry["traits"])
    npc["_pronouns"] = pronoun_fields(npc["Pronouns"])
    if "young" not in entry:
        print("! %s has no recorded 'young' flag (written by an older version of this script) - "
              "assuming not young; the maturity/face wording may drift slightly from the "
              "original render." % args.regen_id, file=sys.stderr)
    npc["_young"] = entry.get("young", False)
    if "Height" not in npc:
        print("! %s has no recorded Height trait (written before the Height table existed) - "
              "regenerating without one; re-roll instead of regenerating to pick one up."
              % args.regen_id, file=sys.stderr)
        npc["Height"] = "of average height"

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
    entry["when"] = time.strftime("%Y-%m-%d %H:%M:%S")
    manifest[folder_path] = entry
    art.save_manifest(args.regen_manifest, manifest)

    print("done: %s" % folder)
    return 0


def main(argv=None):
    args = parse_args(argv)

    if args.regen_manifest:
        return regenerate_one(args)

    if not args.tables.exists():
        raise SystemExit("Tables file not found: %s" % args.tables)
    tables = parse_tables(args.tables)
    check_tables(tables, args.tables, getattr(parse_tables, "repeated", ()))

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
        npc = roll_npc(tables, random.Random(seed), overrides)
        rolled.append((seed, npc, build_prompts(npc)))

    print("%s: %d tables, %d NPC(s) rolled from base seed %d" % (
        args.tables.name, len(tables), args.count, base_seed))
    print("output root: %s" % args.out)

    if args.dry_run:
        for seed, npc, (portrait_prompt, token_prompt) in rolled:
            print("\n  %s  \"%s\"  (seed %d)" % (npc["name"], npc["Callsigns"], seed))
            print("    %s, %s" % (npc["Role"], npc["Faction"]))
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
        print("    %s, %s" % (npc["Role"], npc["Faction"]))

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
            # Not itself a table roll, so it lives beside traits rather than in
            # it - --regen-manifest reads it back to pick the right MATURITY/
            # FACE clause without re-deriving it from the (already flag-
            # stripped) Age text.
            "young": npc["_young"],
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
