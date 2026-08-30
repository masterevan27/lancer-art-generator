#!/usr/bin/env python3
"""Roll random human NPCs and generate their Foundry portrait + token art.

Companion to generate-art.py. That script walks an authored art-prompt markdown
file and renders every prompt in it; this one has no authored corpus - it rolls
a person out of the tables in

    <comfy>/Art Prompts/npc-generator-tables.md

composes a matched pair of prompts in the campaign's house style, and renders
both through the same ComfyUI workflow generate-art.py uses. All the ComfyUI
plumbing - server discovery, workflow slot detection, job building, the RMBG
post pass - is imported from generate-art.py rather than reimplemented.

Each NPC lands in its own folder under the Foundry Lancer token root:

    <root>/Nadia Okonkwo/Nadia Okonkwo Portrait.png   1024x1024, opaque
    <root>/Nadia Okonkwo/Nadia Okonkwo Token.png      transparent, RMBG'd
    <root>/Nadia Okonkwo/Nadia Okonkwo.md             the rolled dossier

The portrait deliberately skips background removal - it wants its blurred
backdrop - so the two images take different paths through the same workflow
rather than sharing one --post chain.

Stdlib only, same as generate-art.py. Run with --dry-run first.

Examples:
  python generate-npc.py --dry-run
  python generate-npc.py                        # one NPC
  python generate-npc.py --count 5
  python generate-npc.py --seed 1234            # reproducible roll
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
    "Outfit", "Gear", "Accent", "Backdrop", "Stance",
]

PORTRAIT_SIZE = (1024, 1024)   # square, straight onto the Foundry actor sheet
TOKEN_SIZE = (1024, 1280)      # tall, so head and boots keep their margin

PORTRAIT_TEMPLATE = (
    "A half-body character portrait of {role}, {age}, rendered in a detailed painterly "
    "illustration style with fine grain texture and clean linework, halftone dot shading "
    "worked into the shadows, moody cinematic lighting. {Subject} {is_are} {build}, with "
    "{skin}, {hair}, {eyes}, and {feature}, wearing {outfit}, {faction}. {Possessive} "
    "face carries {demeanor}. {Subject} {carry} {gear}. Behind {object}, softly blurred "
    "well out of focus, is {backdrop}, its lights casting a faint {accent} glow across one "
    "side of {possessive} face, contrasted against warm dim ambient light on the other. "
    "Keep the palette restrained - greys, olive drab and rust - with {accent} as the only "
    "saturated color in the frame. Shallow depth of field, centered composition, square "
    "framing, high detail, atmospheric sci-fi character portrait."
)

TOKEN_TEMPLATE = (
    "A full-body character illustration of {role}, {age}, standing and facing directly "
    "forward, entire body visible from the top of {possessive} head to the soles of "
    "{possessive} boots with clear empty space above and below, rendered in a detailed "
    "painterly illustration style with fine grain texture and clean linework, halftone dot "
    "shading worked into the shadows. {Subject} {is_are} {build}, with {skin}, {hair}, "
    "{eyes}, and {feature}, wearing {outfit}, {faction}. {Possessive} face carries "
    "{demeanor}. {Subject} {carry} {gear}. A single {accent} glow - an indicator light, a lit "
    "seam, a display - is the only saturated color on {possessive} kit. "
    "{Subject} {is_are} {stance}, boots fully planted and visible, looking straight ahead. "
    "Keep the palette restrained - greys, olive drab and rust - with {accent} as the only "
    "saturated color. The background is a solid flat plain white, no texture, no gradient, "
    "no shadow, no environment. Centered composition, even lighting, isolated character "
    "illustration, clean silhouette."
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
    current = None

    for line in md_path.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^##\s+(?!#)\s*(.*?)\s*$", line)
        if heading:
            current = heading.group(1)
            tables.setdefault(current, [])
            continue

        bullet = re.match(r"^-\s+(.*?)\s*$", line)
        if bullet and current:
            text = bullet.group(1)
            weight = re.match(r"^x(\d+)\s+(.*)$", text)
            count, text = (int(weight.group(1)), weight.group(2)) if weight else (1, text)
            tables[current].extend([text] * count)

    return {name: options for name, options in tables.items() if options}


def check_tables(tables, path):
    missing = [name for name in REQUIRED_TABLES if name not in tables]
    if missing:
        raise SystemExit(
            "%s is missing the table(s) the prompt templates need: %s"
            % (path.name, ", ".join(missing))
        )


def roll_npc(tables, rng, overrides=None):
    """One NPC as a flat dict of trait -> rolled text."""
    npc = {name: rng.choice(tables[name]) for name in REQUIRED_TABLES}
    npc.update(overrides or {})

    if "name" not in npc:
        npc["name"] = "%s %s" % (npc["Given names"], npc["Family names"])

    subject, object_, possessive = (npc["Pronouns"].split("/") + ["", ""])[:3]
    plural = subject == "they"
    npc["_pronouns"] = {
        "subject": subject,
        "Subject": subject.capitalize(),
        "object": object_,
        "possessive": possessive,
        "Possessive": possessive.capitalize(),
        "is_are": "are" if plural else "is",
        "carry": "carry" if plural else "carries",
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


def build_prompts(npc):
    """The portrait and token prompt text for one rolled NPC."""
    fields = dict(npc["_pronouns"])
    fields.update({
        "role": npc["Role"],
        "age": npc["Age"],
        "build": npc["Build"],
        "skin": npc["Skin"],
        "hair": npc["Hair"],
        "eyes": npc["Eyes"],
        "feature": npc["Feature"],
        "outfit": npc["Outfit"],
        "faction": npc["Faction"],
        "demeanor": npc["Demeanor"],
        "gear": npc["Gear"],
        "accent": npc["Accent"],
        "backdrop": npc["Backdrop"],
        "stance": npc["Stance"],
    })
    return PORTRAIT_TEMPLATE.format(**fields), TOKEN_TEMPLATE.format(**fields)


# --------------------------------------------------------------------------
# Output paths and the dossier
# --------------------------------------------------------------------------


def _safe(name):
    """A filename Windows and Foundry are both happy with."""
    return re.sub(r"\s+", " ", re.sub(r'[<>:"/\\|?*]', "", name)).strip(" .")


def npc_folder(root, name, overwrite):
    """<root>/<Name>/, suffixed if that name has already been rolled."""
    base = _safe(name)
    folder = root / base
    if overwrite or not folder.exists():
        return folder
    for n in range(2, 100):
        candidate = root / ("%s (%d)" % (base, n))
        if not candidate.exists():
            return candidate
    raise RuntimeError("too many NPCs already named %s" % base)


def write_dossier(path, npc, seed, prompts, images):
    portrait_prompt, token_prompt = prompts
    traits = [
        ("Callsign", npc["Callsigns"]),
        ("Pronouns", npc["Pronouns"]),
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
        ("Portrait backdrop", npc["Backdrop"]),
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


def entry_for(slug, stage, prompt):
    """A generate-art.py Entry, so its job builder can be reused unchanged."""
    return art.Entry(name=slug, label=stage, path=[slug], prompt=prompt, line=0)


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
    roll.add_argument("--set-trait", action="append", default=[], metavar="Table=value",
                      help="force one rolled trait, e.g. --set-trait Role='a field medic' "
                           "(repeatable; table names are the markdown headings)")

    gen = p.add_argument_group("generation")
    gen.add_argument("--workflow", type=Path, default=art.DEFAULT_WORKFLOW,
                     help="API-format generation workflow (default: %(default)s)")
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
        overrides[table.strip()] = value.strip()
    args.overrides = overrides

    if args.out is None:
        args.out = default_root()

    return args


def main(argv=None):
    args = parse_args(argv)

    if not args.tables.exists():
        raise SystemExit("Tables file not found: %s" % args.tables)
    tables = parse_tables(args.tables)
    check_tables(tables, args.tables)

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
            print("    -> %s" % (npc_folder(args.out, npc["name"], args.overwrite)))
            if not args.no_portrait:
                print("    portrait %dx%d: %s..." % (PORTRAIT_SIZE + (portrait_prompt[:90],)))
            if not args.no_token:
                print("    token    %dx%d: %s..." % (TOKEN_SIZE + (token_prompt[:90],)))
        stages = (0 if args.no_portrait else 1) + (0 if args.no_token else 2)
        print("\ndry run OK - %d job(s) would be queued" % (len(rolled) * stages))
        return 0

    if not args.workflow.exists():
        raise SystemExit("Workflow not found: %s" % args.workflow)
    template = art.load_api_workflow(args.workflow)
    try:
        slots = art.locate_slots(template)
    except art.WorkflowError as exc:
        raise SystemExit("%s: %s" % (args.workflow.name, exc))
    if not slots.latent:
        print("! %s has no EmptyLatentImage - portrait and token will share the "
              "workflow's own size instead of 1024x1024 / 1024x1280"
              % args.workflow.name, file=sys.stderr)

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

    def render(prompt, slug, stage, size, seed):
        """Queue one text -> image job and return the images it produced."""
        knobs = Knobs(args, size, COMFY_PREFIX)
        job = art.build_job(template, slots, entry_for(slug, stage, prompt), seed, knobs)
        record = comfy.wait(comfy.queue(job), timeout=args.timeout)
        images = comfy.images(record)
        if not images:
            raise RuntimeError("the %s job produced no image" % stage)
        return images

    def remove_background(image, slug, seed):
        knobs = Knobs(args, TOKEN_SIZE, COMFY_PREFIX)
        prefix = "%s/%s/token_rmbg" % (COMFY_PREFIX, slug)
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
        folder = npc_folder(args.out, npc["name"], args.overwrite)
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
                image = render(portrait_prompt, slug, "portrait", PORTRAIT_SIZE, seed)[0]
                written.append(fetch(comfy, image, folder / ("%s Portrait.png" % stem)).name)
                print("      -> %s" % written[-1])

            if not args.no_token:
                print("    token ...", flush=True)
                raw = render(token_prompt, slug, "token", TOKEN_SIZE, seed)[0]
                if args.keep_raw_token:
                    written.append(
                        fetch(comfy, raw, folder / ("%s Token (raw).png" % stem)).name)
                print("      + background removal", flush=True)
                cut = remove_background(raw, slug, seed)
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
