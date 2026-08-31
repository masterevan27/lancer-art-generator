#!/usr/bin/env python3
"""Roll random human NPCs and generate their Foundry portrait + token art.

Companion to generate-art.py. That script walks an authored art-prompt markdown
file and renders every prompt in it; this one has no authored corpus - it rolls
a person out of the tables in

    <comfy>/Art Prompts/npc-generator-tables.md

composes a matched pair of prompts in the campaign's house style, and renders
both through a ComfyUI workflow - the one generate-art.py uses, unless the NPC's
gender selects its own (see GENDER_WORKFLOWS). All the ComfyUI plumbing - server
discovery, workflow slot detection, job building, the RMBG post pass - is
imported from generate-art.py rather than reimplemented.

Each NPC lands in its own folder, nested under a category folder for their
rolled Role (see ROLE_CATEGORIES), under the Foundry Lancer token root:

    <root>/Soldiers/Nadia Okonkwo/Nadia Okonkwo Portrait.png   1024x1024, opaque
    <root>/Soldiers/Nadia Okonkwo/Nadia Okonkwo Token.png      transparent, RMBG'd
    <root>/Soldiers/Nadia Okonkwo/Nadia Okonkwo.md             the rolled dossier

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
"""

from __future__ import annotations

import argparse
import importlib.util
import random
import re
import sys
import time
import urllib.parse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
COMFY_DIR = SCRIPT_DIR.parent
HUB_DIR = COMFY_DIR.parent.parent


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

DEFAULT_TABLES = COMFY_DIR / "Art Prompts" / "npc-generator-tables.md"
DEFAULT_MANIFEST = SCRIPT_DIR / ".generated-npcs.json"

# Foundry creates a 'Data' folder inside the --dataPath it is given, so the live
# tree is the doubled data\Data - the AppData copy is never read at runtime.
FOUNDRY_TOKEN_ROOT = Path(
    r"G:\Programs\FoundryVTT_v13\FoundryVTT-Node-13.351\data\Data\Images\LancerFoundryTokens"
)
FALLBACK_TOKEN_ROOT = HUB_DIR / "Assets" / "LancerFoundryTokens"
NPC_SUBFOLDER = "NPCs"

# Where ComfyUI's own output folder collects the raw renders, before they are
# fetched into the Foundry tree under their final names.
COMFY_PREFIX = "LancerNPCs"

# Tables the prompt templates below require. Anything else in the markdown file
# is ignored, so extra tables can be added for reference without breaking this.
REQUIRED_TABLES = [
    "Given names", "Family names", "Callsigns", "Pronouns", "Age", "Build",
    "Skin", "Hair", "Eyes", "Feature", "Demeanor", "Role", "Faction",
    "Outfit", "Headgear", "Gear", "Accent", "Backdrop", "Weather", "Stance",
]

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
    "{build}, {face}, and {traits}"
    "{skin}, {hair}, {eyes}, and {feature}, wearing {outfit}, {faction}, the clothing "
    "following the shape of that frame. {headgear} {Possessive} face carries {demeanor}. "
    "{gear_line}{backdrop} {weather_line}A faint {accent} glow falls across one side of {possessive} "
    "face against warm dim ambient light on the other. Keep the palette restrained - "
    "greys, olive drab and rust - with {accent} the only saturated color in the frame. "
    "Shallow depth of field, square framing, high detail, atmospheric sci-fi character "
    "portrait, painterly brushwork with heavy grain and dense halftone screentone worked "
    "into every shadow."
)

TOKEN_TEMPLATE = (
    "A full-body character illustration of {role}, {maturity} {gender} {age}, "
    "rendered in a detailed painterly illustration style with fine grain texture, clean "
    "linework and halftone dot shading worked into the shadows, moody cinematic lighting "
    "on the figure. {Possessive} face carries the same fine grain and visible brushwork "
    "as a close-up portrait, not simplified or cel-shaded. {Subject} {is_are} "
    "standing at full height facing the viewer, entire body visible from the top of "
    "{possessive} head to the soles of {possessive} plain modern boots, no leg wraps or "
    "puttees, with clear empty space above and below, in realistic adult proportions "
    "roughly seven to eight heads tall. "
    "{Subject} {is_are} {build}, with {traits}{skin}, {hair}, {eyes}, and {feature}, wearing "
    "{outfit}, {faction}, the clothing following the shape of that frame. {headgear} "
    "{Possessive} face carries {demeanor}. {gear_line}{Subject} {is_are} {stance}, both "
    "boots planted and fully visible, the pose relaxed and natural with the arms free. "
    "Keep the palette restrained - greys, olive drab and rust - with a single {accent} "
    "glow the only saturated color. The background alone is a solid flat plain white, no "
    "texture, no gradient, no shadow, no environment. Centered composition, dramatic "
    "lighting, isolated character illustration, clean silhouette, painterly brushwork "
    "with heavy grain and dense halftone screentone worked into every shadow, matching "
    "the same painterly rendering as the portrait shot."
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


def roll_npc(tables, rng, overrides=None):
    """One NPC as a flat dict of trait -> rolled text."""
    # Pronouns first: every other table may have a per-pronoun variant, so the
    # roll that selects between them has to happen before the rest.
    pronouns = (overrides or {}).get("Pronouns") or rng.choice(tables["Pronouns"])
    subject = pronouns.split("/")[0]

    # Age is resolved up front for the same reason Pronouns is: its flag gates
    # the Build roll, so an override has to be in hand before Build is rolled
    # rather than pasted over the result afterwards. Pass the flag to keep it,
    # as in --set-trait Age="in her late teens || young".
    forced_age = (overrides or {}).get("Age")

    npc = {"Pronouns": pronouns}
    young = False
    for name in REQUIRED_TABLES:
        if name in ("Pronouns", "Stance"):
            continue
        options = variant_table(tables, name, subject)

        # Build is filtered against the Age roll, the same way Stance is
        # filtered against Gear below. An Age bullet flagged 'young' is a
        # teenager; the Build bullets flagged 'figure' describe an adult
        # woman's - bust, hips, waist - and the two must never be combined.
        # Age precedes Build in REQUIRED_TABLES, so the flag is known by the
        # time this runs; keep it that way if the list is ever reordered.
        if name == "Build" and young:
            plain = [x for x in options if "figure" not in split_flags(x)[1]]
            options = plain or options     # never filter the pool down to nothing

        # Rolled either way, so that forcing a trait does not shift the rest of
        # the run's random stream and change every NPC after it.
        value = rng.choice(options)
        if name == "Age" and forced_age is not None:
            value = forced_age
        # Only these two are unpacked here. Backdrop's '||' separates three
        # fields rather than two and is parsed by split_backdrop, and Gear's
        # flags are read further down, so neither can be split in passing.
        if name in ("Age", "Build"):
            value, flags = split_flags(value)
            if name == "Age":
                young = "young" in flags
        npc[name] = value

    npc["_young"] = young

    # Stance is rolled last, and filtered against the Gear roll. The two tables
    # are otherwise independent, which produced NPCs standing with their hands
    # pushed into their pockets while holding a rifle in both hands. Gear that
    # occupies a hand rules out the stances that need both of them free, and a
    # Stance that describes aiming or firing a weapon needs the Gear roll to
    # have actually come up a firearm, or the pose has nothing in hand to back
    # it up.
    npc["Gear"], gear_flags = split_flags(npc["Gear"])
    stances = [split_flags(x) for x in variant_table(tables, "Stance", subject)]
    if "gun" not in gear_flags:
        unarmed = [x for x in stances if "gun" not in x[1]]
        stances = unarmed or stances       # never filter the pool down to nothing
    if "hands" in gear_flags:
        free = [x for x in stances if "hands" not in x[1]]
        stances = free or stances          # never filter the pool down to nothing
    npc["Stance"] = rng.choice(stances)[0]

    npc.update(overrides or {})
    npc["Age"] = split_flags(npc["Age"])[0]   # the override still carries its flag

    # Build needs the same unpacking, and for a second reason beyond tidiness:
    # the young/figure filter above only screens the *rolled* pool, so a forced
    # Build walks straight past it. Re-check the pairing here, where the Age
    # flag is known whether it was rolled or forced.
    build, build_flags = split_flags(npc["Build"])
    if young and "figure" in build_flags:
        raise SystemExit(
            "--set-trait Build: a bullet flagged 'figure' describes an adult "
            "woman's build and must not be combined with an Age flagged "
            "'young'. Drop one of the two flags."
        )
    npc["Build"] = build

    if "name" not in npc:
        npc["name"] = "%s %s" % (npc["Given names"], npc["Family names"])

    # subject/object/possessive, plus an optional fourth field: the noun the
    # image prompt uses for the subject. Pronouns alone left the model guessing
    # - tokens came back androgynous - so the prompt now says "adult woman" or
    # "adult man" outright. A three-field bullet still works and infers it.
    bits = (npc["Pronouns"].split("/") + ["", "", ""])[:4]
    subject, object_, possessive, gender = bits
    plural = subject == "they"
    gender = gender or {"she": "woman", "he": "man"}.get(subject, "person")
    npc["_pronouns"] = {
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
    phrase. On Gear/Stance the flags are 'hands', meaning the entry occupies at
    least one hand (on Gear) or needs both of them free (on Stance), and 'gun',
    meaning the entry is an actual firearm held in hand (on Gear) or a pose that
    describes aiming, firing or otherwise handling one (on Stance) - a bullet
    can carry both at once, '|| hands gun'. Age and Build reuse the same split
    for their own unrelated flags, 'young' and 'figure'.
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

    The one flag is 'nogear': an action scene that already puts a weapon in the
    subject's hands suppresses the "{Subject} {carry} {gear}" sentence, which
    otherwise arms them a second time from the Gear roll - a rolled rifle on top
    of the two blades the rooftop scene hands out.
    """
    parts = [p.strip() for p in bullet.split("||")]
    if len(parts) == 1:
        return "A half-body character portrait", parts[0], ()
    shot, scene = parts[0], parts[1]
    flags = tuple(f for f in parts[2].split() if f) if len(parts) > 2 else ()
    return shot, scene, flags


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


def build_prompts(npc):
    """The portrait and token prompt text for one rolled NPC."""
    shot, scene, flags = split_backdrop(npc["Backdrop"])
    fields = dict(npc["_pronouns"])
    fields.update({
        "role": npc["Role"],
        "age": npc["Age"],
        "maturity": MATURITY[npc["_young"]],
        "face": FACE[npc["_young"]],
        # Asserted for every NPC of that gender rather than rolled for, and
        # unlike the 'figure' builds not withheld from a young one.
        "traits": GENDER_TRAITS.get(npc["_pronouns"]["gender"], ""),
        "build": npc["Build"],
        "skin": npc["Skin"],
        "hair": npc["Hair"],
        "eyes": npc["Eyes"],
        "feature": npc["Feature"],
        "outfit": npc["Outfit"],
        "headgear": npc["Headgear"],
        "faction": npc["Faction"],
        "demeanor": npc["Demeanor"],
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
    carrying = "{Subject} {carry} {gear}. ".format(**fields)
    portrait_fields = dict(fields, gear_line="" if "nogear" in flags else carrying)

    prompts = (PORTRAIT_TEMPLATE.format(**portrait_fields),
               TOKEN_TEMPLATE.format(**dict(fields, gear_line=carrying)))

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
        ("Role", npc["Role"]),
        ("Affiliation", npc["Faction"]),
        ("Age", npc["Age"]),
        ("Build", npc["Build"]),
        ("Skin", npc["Skin"]),
        ("Hair", npc["Hair"]),
        ("Eyes", npc["Eyes"]),
        ("Distinguishing", npc["Feature"]),
        ("Demeanor", npc["Demeanor"]),
        ("Wearing", npc["Outfit"]),
        ("Carrying", npc["Gear"]),
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
    if FOUNDRY_TOKEN_ROOT.exists():
        return FOUNDRY_TOKEN_ROOT / NPC_SUBFOLDER
    return FALLBACK_TOKEN_ROOT / NPC_SUBFOLDER


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
                     help="token root to write NPC folders into (default: the live "
                          "Foundry Images/LancerFoundryTokens/NPCs, else the hub's Assets copy)")
    out.add_argument("--overwrite", action="store_true",
                     help="reuse an existing folder of the same name instead of suffixing it")
    out.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST,
                     help="run log of every NPC rolled (default: %(default)s)")

    run = p.add_argument_group("run mode")
    run.add_argument("--server", help="ComfyUI address, e.g. 127.0.0.1:8000")
    run.add_argument("--dry-run", action="store_true",
                     help="roll and print the NPCs and their prompts, queue nothing")
    run.add_argument("--timeout", type=float, default=1800, help="per-job timeout in seconds")

    args = p.parse_args(argv)

    if args.no_portrait and args.no_token:
        p.error("--no-portrait and --no-token together leave nothing to generate")
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

    if args.out is None:
        args.out = default_root()

    return args


def workflow_for(args, npc):
    """The generation workflow this NPC's gender selects, else --workflow."""
    return args.gender_workflows.get(npc["_pronouns"]["gender"], args.workflow)


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


def main(argv=None):
    args = parse_args(argv)

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
                print("    portrait %dx%d ~%d tok: %s..." % (
                    PORTRAIT_SIZE + (estimate_tokens(portrait_prompt), portrait_prompt[:70])))
            if not args.no_token:
                print("    token    %dx%d ~%d tok: %s..." % (
                    TOKEN_SIZE + (estimate_tokens(token_prompt), token_prompt[:70])))
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
        try:
            folder.mkdir(parents=True, exist_ok=True)

            if not args.no_portrait:
                print("    portrait ...", flush=True)
                image = render(npc, portrait_prompt, category, slug, "portrait", PORTRAIT_SIZE, seed)[0]
                written.append(fetch(comfy, image, folder / ("%s Portrait.png" % stem)).name)
                print("      -> %s" % written[-1])

            if not args.no_token:
                print("    token ...", flush=True)
                raw = render(npc, token_prompt, category, slug, "token", TOKEN_SIZE, seed)[0]
                if args.keep_raw_token:
                    written.append(
                        fetch(comfy, raw, folder / ("%s Token (raw).png" % stem)).name)
                print("      + background removal", flush=True)
                cut = remove_background(raw, category, slug, seed)
                written.append(fetch(comfy, cut, folder / ("%s Token.png" % stem)).name)
                print("      -> %s" % written[-1])

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
            "name": npc["name"],
            "callsign": npc["Callsigns"],
            "seed": seed,
            "tables": str(args.tables),
            "workflow": str(workflow_for(args, npc)),
            "traits": {k: v for k, v in npc.items() if not k.startswith("_")},
            "files": written,
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
