#!/usr/bin/env python3
"""Generate transparent SillyTavern expression sprites from one portrait.

The source can be an NPC recorded in .generated-npcs.json or any image on
disk. Each sprite is an independent Qwen image edit of that original source;
no generated expression is ever used as the next expression's input.
"""
import argparse
import importlib.util
import json
import os
import random
import re
import sys
import time
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TABLES = SCRIPT_DIR / "prompts" / "expression-tables.md"
WORKFLOW = (SCRIPT_DIR / "workflows" / "api" /
            "Util_Expression_QwenEdit_RMBG_v1.json")
DEFAULT_LABELS = (
    "admiration", "amusement", "anger", "annoyance", "approval", "caring",
    "confusion", "curiosity", "desire", "disappointment", "disapproval",
    "disgust", "embarrassment", "excitement", "fear", "gratitude", "grief",
    "joy", "love", "nervousness", "neutral", "optimism", "pride",
    "realization", "relief", "remorse", "sadness", "surprise",
)
ANCHOR_TRAITS = ("Hair", "Hair colour", "Feature", "Outfit", "Headgear")
IDENTITY_PREAMBLE = (
    "Keep the same character, face, hairstyle, outfit, colours, art style, "
    "camera framing and pose. Change only the facial expression and small body "
    "language. Front-facing bust, no text."
)
SPRITE_RE = re.compile(
    r"^([a-z0-9_]+)(?:-(\d+)|\.([A-Za-z0-9_.-]+))?\.webp$")


def _load_npc_generator():
    """Load the existing table parser and ComfyUI client without generate-3d."""
    path = SCRIPT_DIR / "generate-npc.py"
    if not path.exists():
        raise SystemExit("generate-npc.py not found next to this script")
    name = "lancer_expression_npc"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


npc_gen = _load_npc_generator()
art = npc_gen.art


@dataclass(frozen=True)
class Source:
    image: Path
    output_dir: Path
    name: str
    traits: dict
    mode: str


@dataclass(frozen=True)
class SpritePlan:
    destination: Path
    label: str
    prompt: str
    seed: int
    keep_background: bool
    replace_label: bool = False
    replace_mode: bool = False


@dataclass(frozen=True)
class RunResult:
    written: int
    failed: int

    @property
    def exit_code(self):
        return 1 if self.failed else 0


def sanitize_label(label):
    """Return the flat, lowercase SillyTavern filename label for ``label``."""
    clean = re.sub(r"[^a-z0-9_]+", "_", str(label).strip().lower()).strip("_")
    if not clean:
        raise ValueError("custom label is empty after sanitizing")
    return clean


def parse_custom_specs(specs):
    """Parse repeatable ``label[=prompt]`` values, sanitizing their labels."""
    custom = {}
    for spec in specs or ():
        raw_label, separator, text = str(spec).partition("=")
        label = sanitize_label(raw_label)
        custom[label] = (text.strip() or None) if separator else None
    return custom


def load_expression_tables(path):
    """Load rollable expression pools through generate-npc.py's parser."""
    path = Path(path)
    if not path.exists():
        raise ValueError("no such expressions tables file: %s" % path)
    raw = npc_gen.parse_tables(path)
    tables = {}
    for heading, bullets in raw.items():
        try:
            label = sanitize_label(heading)
        except ValueError:
            continue
        tables.setdefault(label, []).extend(bullets)
    for heading, bullets in tables.items():
        for bullet in dict.fromkeys(bullets):
            target = npc_gen.reference_target(bullet)
            if target is None:
                continue
            target_label = sanitize_label(target)
            members = tables.get(target_label)
            if not members:
                raise ValueError(
                    "%s: group reference %r names missing or empty '## %s'"
                    % (path, bullet, target))
            nested = next((member for member in members
                           if npc_gen.reference_target(member) is not None), None)
            if nested is not None:
                raise ValueError(
                    "%s: group '## %s' contains group reference %r; groups "
                    "are one level only" % (path, target, nested))
    return tables


def select_labels(expression_spec, expression_explicit, custom, tables):
    """Return ``(ordered labels, is_full_all_run)`` for CLI selection."""
    if not expression_explicit and custom:
        return tuple(custom), False
    if expression_spec.strip().lower() == "all":
        labels = list(DEFAULT_LABELS)
        for label in custom:
            if label not in labels:
                labels.append(label)
        return tuple(labels), True

    labels = []
    for raw in expression_spec.split(","):
        label = sanitize_label(raw)
        if label not in labels:
            labels.append(label)
    if not labels:
        raise ValueError("no expressions selected")
    known = set(DEFAULT_LABELS) | set(custom) | set(tables)
    unknown = [label for label in labels if label not in known]
    if unknown:
        raise ValueError("unknown expression label(s): %s" % ", ".join(unknown))
    for label in custom:
        if label not in labels:
            labels.append(label)
    return tuple(labels), False


def classify_sprite_name(name):
    """Return a safe sprite's label, or None for non-sprites and paths."""
    name = str(name)
    if "/" in name or "\\" in name or Path(name).name != name:
        return None
    match = SPRITE_RE.fullmatch(name)
    return match.group(1) if match else None


def classified_sprites(output_dir):
    """Existing .webp sprites grouped by label, in stable name order."""
    output_dir = Path(output_dir)
    groups = {}
    if not output_dir.exists():
        return groups
    for path in sorted(output_dir.iterdir(), key=lambda item: item.name):
        label = classify_sprite_name(path.name) if path.is_file() else None
        if label:
            groups.setdefault(label, []).append(path)
    return groups


def assemble_prompt(expression, traits=None):
    """Build one edit instruction, using only identity-safe appearance traits."""
    parts = [IDENTITY_PREAMBLE]
    anchors = ["%s: %s" % (name, traits[name]) for name in ANCHOR_TRAITS
               if traits and traits.get(name)]
    if anchors:
        parts.append("Appearance anchors: " + "; ".join(anchors) + ".")
    parts.append("Expression: %s" % expression.strip())
    return " ".join(parts)


def _seed_at(base_seed, index):
    if base_seed is None:
        return random.SystemRandom().randrange(0, 2**32)
    return int(base_seed) + index


def _expression_prompt(label, seed, tables, custom, describe, traits,
                       saved=None):
    if describe:
        return assemble_prompt(describe, traits)
    if custom.get(label):
        return assemble_prompt(custom[label], traits)
    pool = tables.get(label) or []
    if pool:
        rng = random.Random(seed)
        expression = rng.choice(pool)
        target = npc_gen.reference_target(expression)
        if target is not None:
            members = tables.get(sanitize_label(target)) or []
            if not members:
                raise ValueError(
                    "expression '%s' references missing group '%s'"
                    % (label, target))
            expression = rng.choice(members)
        return assemble_prompt(expression, traits)
    if saved and saved.get("prompt"):
        return saved["prompt"]
    raise ValueError(
        "no prompt for expression '%s' (add its table, --custom text, or "
        "--describe text)" % label)


def _variant_name(label, index):
    return "%s.webp" % label if index == 0 else "%s-%d.webp" % (label, index)


def _numeric_variants(label, paths):
    used = set()
    for path in paths:
        if path.name == "%s.webp" % label:
            used.add(0)
            continue
        match = re.fullmatch(re.escape(label) + r"-(\d+)\.webp", path.name)
        if match:
            used.add(int(match.group(1)))
    return used


def make_plans(output_dir, args, tables, traits, selection, sidecar=None,
               custom=None):
    """Plan filenames, prompts and seeds without changing the filesystem."""
    output_dir = Path(output_dir)
    sidecar = sidecar or {}
    custom = custom or {}
    existing = classified_sprites(output_dir)

    if args.file:
        label = classify_sprite_name(args.file)
        destination = output_dir / args.file
        if label is None or not destination.is_file():
            raise ValueError("--file must name an existing classified .webp sprite")
        seed = _seed_at(args.seed, 0)
        prompt = _expression_prompt(
            label, seed, tables, custom, args.describe, traits,
            sidecar.get(args.file))
        return ([SpritePlan(destination, label, prompt, seed,
                            args.keep_background)], [])

    labels, full_run = selection
    skipped = []
    generating = []
    for label in labels:
        files = existing.get(label, [])
        if full_run and files and not args.replace:
            skipped.append((label, len(files)))
        else:
            generating.append(label)

    plans = []
    sequence = 0
    reserved = {label: _numeric_variants(label, paths)
                for label, paths in existing.items()}
    for label in generating:
        label_reserved = set() if args.replace else reserved.setdefault(label, set())
        for count_index in range(args.count):
            seed = _seed_at(args.seed, sequence)
            prompt = _expression_prompt(
                label, seed, tables, custom, args.describe, traits)
            if args.replace:
                variant = count_index
            else:
                variant = 0
                while variant in label_reserved:
                    variant += 1
                label_reserved.add(variant)
            plans.append(SpritePlan(
                output_dir / _variant_name(label, variant), label, prompt, seed,
                args.keep_background,
                replace_label=bool(args.replace and count_index == 0),
                replace_mode=bool(args.replace)))
            sequence += 1
    return plans, skipped


def load_sidecar(path):
    path = Path(path)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("invalid expressions sidecar %s: %s" % (path, exc))
    if not isinstance(data, dict):
        raise ValueError("expressions sidecar must contain an object: %s" % path)
    return data


def _atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp-%s" % uuid.uuid4().hex)
    try:
        temp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _stage_bytes(destination, data):
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_name(
        destination.name + ".tmp-%s" % uuid.uuid4().hex)
    temp.write_bytes(data)
    return temp


def execute_plans(plans, render_one, sidecar_path, source, dry_run=False,
                  output=None, error=None):
    """Render all plans, containing failures and atomically installing output."""
    output = output or sys.stdout
    error = error or sys.stderr
    plans = list(plans)
    if dry_run:
        for plan in plans:
            print("dry-run: %s | label: %s | prompt: %s" %
                  (plan.destination, plan.label, plan.prompt),
                  file=output, flush=True)
        return RunResult(0, 0)

    sidecar_path = Path(sidecar_path)
    metadata = load_sidecar(sidecar_path)
    source = Path(source)
    source_info = {
        "path": str(source.resolve()),
        "mtime": source.stat().st_mtime_ns / 1_000_000,
    }
    written = failed = 0
    replaced = set()
    replacement_successes = {}
    total = len(plans)
    for index, plan in enumerate(plans, 1):
        print("[%d/%d] %s: rendering (seed %d)" %
              (index, total, plan.label, plan.seed), file=output, flush=True)
        started = time.time()
        try:
            data = render_one(plan)
            if not isinstance(data, (bytes, bytearray)):
                raise RuntimeError("renderer returned no WebP bytes")

            destination = plan.destination
            if plan.replace_mode:
                success_index = replacement_successes.get(plan.label, 0)
                destination = destination.parent / _variant_name(
                    plan.label, success_index)
            staged = _stage_bytes(destination, bytes(data))
            try:
                if plan.replace_mode and plan.label not in replaced:
                    for old in classified_sprites(destination.parent).get(
                            plan.label, []):
                        old.unlink()
                    metadata = {
                        name: record for name, record in metadata.items()
                        if classify_sprite_name(name) != plan.label
                    }
                    replaced.add(plan.label)
                os.replace(staged, destination)
            finally:
                if staged.exists():
                    staged.unlink()

            metadata[destination.name] = {
                "label": plan.label,
                "prompt": plan.prompt,
                "seed": plan.seed,
                "keepBackground": plan.keep_background,
                "source": source_info,
                "when": datetime.now(timezone.utc).isoformat(),
            }
            _atomic_json(sidecar_path, metadata)
            if plan.replace_mode:
                replacement_successes[plan.label] = (
                    replacement_successes.get(plan.label, 0) + 1)
            written += 1
            print("wrote %s (%d KB, %.1f s)" %
                  (destination, max(1, len(data) // 1024),
                   time.time() - started), file=output, flush=True)
        except (Exception, SystemExit) as exc:
            failed += 1
            print("failed: %s: %s" % (plan.label, exc),
                  file=error, flush=True)
    return RunResult(written, failed)


def _node(graph, class_type):
    found = [node_id for node_id, node in graph.items()
             if node.get("class_type") == class_type]
    if len(found) != 1:
        raise RuntimeError("%s appears %d times in the workflow" %
                           (class_type, len(found)))
    return found[0]


def _positive_encode(graph):
    sampler = _node(graph, "KSampler")
    link = graph[sampler]["inputs"].get("positive")
    if not isinstance(link, list) or link[0] not in graph:
        raise RuntimeError("KSampler.positive is not a workflow link")
    return link[0]


def build_graph(image_ref, prompt, seed, steps, quality, keep_background,
                prefix):
    """Return one independently patched Qwen edit -> optional RMBG -> WebP job."""
    graph = art.load_api_workflow(WORKFLOW)
    load = _node(graph, "LoadImage")
    encode = _positive_encode(graph)
    sampler = _node(graph, "KSampler")
    decode = _node(graph, "VAEDecode")
    save = _node(graph, "SaveAnimatedWEBP")
    graph[load]["inputs"]["image"] = image_ref
    graph[encode]["inputs"]["prompt"] = prompt
    graph[sampler]["inputs"].update(seed=int(seed), steps=int(steps))
    graph[save]["inputs"].update(
        filename_prefix=prefix, quality=int(quality), fps=1.0,
        lossless=False, method="default")
    if keep_background:
        graph[save]["inputs"]["images"] = [decode, 0]
        del graph[_node(graph, "RMBG")]
    else:
        rmbg = _node(graph, "RMBG")
        graph[save]["inputs"]["images"] = [rmbg, 0]
    return graph


def _multipart(fields, field_name, filename, blob, content_type):
    boundary = "----lancerexpression%s" % uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        parts.append((
            '--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n'
            % (boundary, name, value)).encode("utf-8"))
    parts.append((
        '--%s\r\nContent-Disposition: form-data; name="%s"; filename="%s"\r\n'
        'Content-Type: %s\r\n\r\n'
        % (boundary, field_name, filename, content_type)).encode("utf-8"))
    parts.extend((blob, ("\r\n--%s--\r\n" % boundary).encode("utf-8")))
    return "multipart/form-data; boundary=%s" % boundary, b"".join(parts)


CONTENT_TYPES = {".png": "image/png", ".jpg": "image/jpeg",
                 ".jpeg": "image/jpeg", ".webp": "image/webp"}


def upload_image(comfy, path, subfolder="lancer-expressions"):
    """Upload one original source and return its ComfyUI LoadImage reference."""
    path = Path(path)
    content_type, body = _multipart(
        {"type": "input", "subfolder": subfolder, "overwrite": "true"},
        "image", path.name, path.read_bytes(),
        CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream"))
    request = urllib.request.Request(
        comfy.base + "/upload/image", data=body,
        headers={"Content-Type": content_type})
    with urllib.request.urlopen(request, timeout=120) as response:
        info = json.loads(response.read().decode("utf-8"))
    name = "%s/%s" % (info.get("subfolder", ""), info["name"])
    return "%s [input]" % name.strip("/").replace("\\", "/")


def _webp_output(record, save_node):
    images = record.get("outputs", {}).get(str(save_node), {}).get("images", [])
    webps = [image for image in images
             if str(image.get("filename", "")).lower().endswith(".webp")]
    if not webps:
        raise RuntimeError("the expression job produced no WebP at its save node")
    return webps[0]


def render_sprite(comfy, image_ref, args, plan, source_slug):
    prefix = "LancerExpressions/%s/%s" % (
        source_slug, plan.destination.stem)
    graph = build_graph(image_ref, plan.prompt, plan.seed, args.steps,
                        args.quality, plan.keep_background, prefix)
    save_node = _node(graph, "SaveAnimatedWEBP")
    record = comfy.wait(comfy.queue(graph), timeout=args.timeout)
    image = _webp_output(record, save_node)
    query = urllib.parse.urlencode({
        "filename": image["filename"],
        "subfolder": image.get("subfolder", ""),
        "type": image.get("type", "output"),
    })
    return comfy._get_bytes("/view?" + query)


def _flag_present(argv, names):
    return any(arg in names or any(arg.startswith(name + "=") for name in names)
               for arg in argv)


def parse_args(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        description="Generate SillyTavern expression sprites from one portrait.")
    source = parser.add_argument_group("source (choose exactly one mode)")
    source.add_argument("--image", type=Path)
    source.add_argument("--out", type=Path)
    source.add_argument("--name")
    source.add_argument("--manifest", type=Path, default=npc_gen.DEFAULT_MANIFEST)
    source.add_argument("--id", action="append", default=[])
    source.add_argument("--filter", metavar="REGEX")
    source.add_argument("--exclude", metavar="REGEX")
    source.add_argument("--limit", type=int, metavar="N")

    select = parser.add_argument_group("expressions")
    select.add_argument("-e", "--expressions", default=None)
    select.add_argument("--custom", action="append", default=[],
                        metavar="LABEL[=PROMPT]")
    select.add_argument("--describe")
    select.add_argument("--count", type=int, default=1)
    select.add_argument("--replace", action="store_true")
    select.add_argument("--file", metavar="NAME.webp")
    select.add_argument("--tables", type=Path, default=DEFAULT_TABLES)

    render = parser.add_argument_group("rendering")
    render.add_argument("--keep-background", action="store_true")
    render.add_argument("--seed", type=int)
    render.add_argument("--steps", type=int, default=4)
    render.add_argument("--quality", type=int, default=90)
    render.add_argument("--server")
    render.add_argument("--timeout", type=float, default=1800)
    render.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    args.expressions_explicit = args.expressions is not None
    if args.expressions is None:
        args.expressions = "all"
    npc_flags = ("--manifest", "--id", "--filter", "--exclude", "--limit")
    args.npc_mode = _flag_present(argv, npc_flags)
    if bool(args.image) == bool(args.npc_mode):
        parser.error("choose exactly one source: --image, or an NPC selector "
                     "(--id/--manifest/--filter/--exclude/--limit)")
    if args.image and not args.image.is_file():
        parser.error("--image not found: %s" % args.image)
    if args.out and not args.image:
        parser.error("--out is only valid with --image")
    if args.name and not args.image:
        parser.error("--name is only valid with --image")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")
    if args.count < 1:
        parser.error("--count must be at least 1")
    if args.steps < 1:
        parser.error("--steps must be at least 1")
    if not 0 <= args.quality <= 100:
        parser.error("--quality must be between 0 and 100")
    if args.file:
        conflicts = []
        if args.expressions_explicit:
            conflicts.append("--expressions")
        if args.custom:
            conflicts.append("--custom")
        if args.count != 1:
            conflicts.append("--count")
        if args.replace:
            conflicts.append("--replace")
        if classify_sprite_name(args.file) is None:
            parser.error("--file must be a safe .webp basename")
        if conflicts:
            parser.error("--file redoes one sprite and is incompatible with %s"
                         % ", ".join(conflicts))
    return args


def _select_entries(manifest, args):
    pairs = sorted((Path(folder), entry) for folder, entry in manifest.items()
                   if isinstance(entry, dict)
                   and isinstance(entry.get("traits"), dict))
    if args.id:
        wanted = set(args.id)
        pairs = [(folder, entry) for folder, entry in pairs
                 if entry.get("id") in wanted]
        missing = sorted(wanted - {entry.get("id") for _, entry in pairs})
        if missing:
            raise ValueError("no manifest entry with id %s" % ", ".join(missing))

    def searchable(folder, entry):
        return "%s %s %s" % (folder, entry.get("name", ""),
                              entry.get("callsign", ""))

    try:
        if args.filter:
            pattern = re.compile(args.filter, re.I)
            pairs = [(folder, entry) for folder, entry in pairs
                     if pattern.search(searchable(folder, entry))]
        if args.exclude:
            pattern = re.compile(args.exclude, re.I)
            pairs = [(folder, entry) for folder, entry in pairs
                     if not pattern.search(searchable(folder, entry))]
    except re.error as exc:
        raise ValueError("invalid selection regex: %s" % exc)
    return pairs[:args.limit] if args.limit else pairs


def resolve_sources(args):
    """Resolve and validate all selected original portraits before queueing."""
    if args.image:
        image = args.image.resolve()
        output = (args.out.resolve() if args.out else
                  image.parent / (image.stem + "-expressions"))
        return [Source(image, output, args.name or image.stem, {}, "image")]

    if not args.manifest.is_file():
        raise ValueError("manifest not found: %s" % args.manifest)
    jobs = []
    for folder, entry in _select_entries(art.load_manifest(args.manifest), args):
        name = entry.get("name")
        if not name:
            raise ValueError("manifest entry at %s has no name" % folder)
        portrait = folder / ("%s Portrait.png" % npc_gen._safe(name))
        if not portrait.is_file():
            raise ValueError("portrait not found: %s" % portrait)
        jobs.append(Source(portrait, folder / "expressions", name,
                           entry["traits"], "npc"))
    return jobs


def main(argv=None):
    args = parse_args(argv)
    try:
        tables = load_expression_tables(args.tables)
        custom = parse_custom_specs(args.custom)
        selection = (None if args.file else select_labels(
            args.expressions, args.expressions_explicit, custom, tables))
        sources = resolve_sources(args)
        prepared = []
        for source in sources:
            sidecar_path = source.output_dir / "expressions.json"
            sidecar = load_sidecar(sidecar_path)
            plans, skipped = make_plans(
                source.output_dir, args, tables, source.traits, selection,
                sidecar, custom)
            prepared.append((source, sidecar_path, plans, skipped))
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2

    if not prepared:
        print("nothing selected", flush=True)
        return 0

    if args.dry_run:
        skipped_count = 0
        for source, sidecar_path, plans, skipped in prepared:
            print("source: %s (%s %s)" %
                  (source.image, source.mode, source.name), flush=True)
            for label, count in skipped:
                print("skip: %s (already has %d files)" % (label, count),
                      flush=True)
            skipped_count += len(skipped)
            execute_plans(plans, None, sidecar_path, source.image, dry_run=True)
        print("done: 0 written, %d skipped, 0 failed" % skipped_count, flush=True)
        return 0

    try:
        comfy = art.find_server(args.server)
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 1

    total_written = total_failed = total_skipped = 0
    for source, sidecar_path, plans, skipped in prepared:
        print("source: %s (%s %s)" %
              (source.image, source.mode, source.name), flush=True)
        for label, count in skipped:
            print("skip: %s (already has %d files)" % (label, count), flush=True)
        total_skipped += len(skipped)
        if not plans:
            continue
        try:
            image_ref = upload_image(comfy, source.image)
        except (Exception, SystemExit) as exc:
            for plan in plans:
                print("failed: %s: upload failed: %s" % (plan.label, exc),
                      file=sys.stderr, flush=True)
            total_failed += len(plans)
            continue
        slug = art._slug(source.name)
        result = execute_plans(
            plans,
            lambda plan, ref=image_ref, source_slug=slug: render_sprite(
                comfy, ref, args, plan, source_slug),
            sidecar_path, source.image)
        total_written += result.written
        total_failed += result.failed
    print("done: %d written, %d skipped, %d failed" %
          (total_written, total_skipped, total_failed), flush=True)
    return 1 if total_failed else 0


if __name__ == "__main__":
    sys.exit(main())
