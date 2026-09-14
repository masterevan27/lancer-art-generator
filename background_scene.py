"""Background tables, deterministic plans and ComfyUI graph construction.

This module deliberately has no ComfyUI or third-party import side effects.
"""
import importlib.util
import json
import os
from pathlib import Path
import random
import re
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parent
DEFAULT_TABLES = ROOT / "prompts/background-generator-tables.md"
ENVIRONMENTS = ["outdoor", "indoor", "space"]
MAX_SEED = 2**32 - 1
REQUEST_KEYS = {"environment", "seed", "count", "traits", "locked", "reroll", "view", "notes", "width", "height"}
PLAN_KEYS = {"version", "environment", "seed", "traits", "prompt", "motionPrompt", "view", "notes", "width", "height"}
TOPDOWN = (
    "Draw a true orthographic top-down gridless battlemap. The camera is directly "
    "above the ceiling looking straight down, exactly perpendicular to the floor. "
    "All floors are parallel to the image plane. Remove roofs and ceilings. "
    "Show walls only as low wall cross-sections; no visible vertical wall faces "
    "or furniture fronts. Show the tops of furniture and equipment. Redraw the "
    "layout from above rather than preserving any source framing. No horizon, "
    "sky, vanishing point, isometric tilt, oblique perspective, grid, hexes, "
    "labels, text, tokens or characters. Keep connected routes, door openings "
    "and cover clearly readable at a consistent tactical scale."
)


def _object(value, allowed, label):
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    unknown = set(value) - allowed
    if unknown:
        raise ValueError(f"Unknown {label} fields: {', '.join(sorted(unknown))}")


def integer(value, label, low, high, multiple=1):
    if type(value) is not int or not low <= value <= high or value % multiple:
        raise ValueError(f"{label} must be an integer from {low} to {high}, divisible by {multiple}")
    return value


def _text(value, label, maximum=16000):
    if not isinstance(value, str) or len(value) > maximum or "\x00" in value:
        raise ValueError(f"{label} must be text of at most {maximum} characters without NUL")
    return value


def _entry(raw):
    text = raw
    weight = 1
    match = re.match(r"x(\d+)\s+", text)
    if match:
        weight = int(match[1])
        text = text[match.end():]
    if not 1 <= weight <= 10000:
        raise ValueError("Table weights must be integers from 1 to 10000")
    envs = list(ENVIRONMENTS)
    weather = None
    seen_context = False
    while text.startswith("["):
        match = re.match(r"\[([^]]+)\]\s*", text)
        if not match:
            raise ValueError(f"Invalid table flag: {raw}")
        flag = match[1]
        if flag.startswith("weather="):
            weather = flag[len("weather="):]
            if not re.fullmatch(r"[a-z][a-z0-9_-]*", weather):
                raise ValueError(f"Invalid weather flag: {raw}")
        elif flag.startswith("time="):
            if flag[5:] not in ("day", "night", "twilight"):
                raise ValueError(f"Invalid time flag: {raw}")
        elif set(flag.split(",")) <= set(ENVIRONMENTS):
            if seen_context:
                raise ValueError(f"Use one comma-separated context flag: {raw}")
            envs = [e for e in ENVIRONMENTS if e in flag.split(",")]
            seen_context = True
        else:
            raise ValueError(f"Unknown table flag [{flag}]")
        text = text[match.end():]
    if not text.strip():
        raise ValueError("Table entries must contain a substantive description")
    return envs, weight, weather, text.strip()


def load_catalogue(path=DEFAULT_TABLES):
    content = re.sub(r"<!--.*?-->", "", Path(path).read_text(encoding="utf-8-sig"), flags=re.S)
    tables = []
    table = None
    for line in content.splitlines():
        if line.startswith("## "):
            name = line[3:].strip()
            if not name or any(t["name"] == name for t in tables):
                raise ValueError(f"Missing or duplicate table heading: {name}")
            table = {"name": name, "values": []}
            tables.append(table)
        elif line.startswith("- ") and table is not None:
            raw = line[2:].strip()
            envs, weight, _, _ = _entry(raw)
            if any(v["text"] == raw for v in table["values"]):
                raise ValueError(f"Duplicate entry in {table['name']}: {raw}")
            table["values"].append({"text": raw, "environments": envs, "weight": weight})
    if not tables:
        raise ValueError("Background tables contain no ## pools")
    for table in tables:
        if not table["values"]:
            raise ValueError(f"Background table {table['name']} has no enabled entries")
        table["environments"] = [e for e in ENVIRONMENTS if any(e in v["environments"] for v in table["values"])]
    return {"environments": list(ENVIRONMENTS), "tables": tables}


def _settings(request):
    environment = request.get("environment", "outdoor")
    if environment not in ENVIRONMENTS:
        raise ValueError("environment must be outdoor, indoor or space")
    view = request.get("view", "perspective")
    if view not in ("perspective", "topdown"):
        raise ValueError("view must be perspective or topdown")
    return {
        "environment": environment,
        "seed": integer(request.get("seed", 0), "seed", 0, MAX_SEED),
        "view": view,
        "notes": _text(request.get("notes", ""), "notes", 4000),
        "width": integer(request.get("width", 1920), "width", 64, 8192, 8),
        "height": integer(request.get("height", 1080), "height", 64, 8192, 8),
    }


def _validate_traits(traits, environment, catalogue):
    tables = {t["name"]: t for t in catalogue["tables"]}
    _object(traits, set(tables), "traits")
    for name, raw in traits.items():
        _text(raw, name)
        applicable = [v for v in tables[name]["values"] if environment in v["environments"]]
        if not applicable:
            raise ValueError(f"{name} is inapplicable to {environment}; omit it")
        if name.endswith(" location") and not raw:
            raise ValueError(f"{name} is required and cannot be blank")
        if raw and not any(v["text"] == raw for v in applicable):
            raise ValueError(f"Unknown or incompatible trait in {name}: {raw}")
    if traits.get("Motion"):
        required = _entry(traits["Motion"])[2]
        if required and "Weather" in traits:
            actual = _entry(traits["Weather"])[2] if traits["Weather"] else None
            if actual != required:
                raise ValueError("Motion is incompatible with the selected Weather")
    if traits.get("Lighting") and "Time" in traits:
        required = _time_tag(traits["Lighting"])
        if required and required != _time_tag(traits["Time"]):
            raise ValueError("Lighting is incompatible with the selected Time")


def _time_tag(raw):
    match = re.search(r"\[time=(day|night|twilight)\]", raw)
    return match[1] if match else None


def _roll(rng, environment, pins, catalogue):
    pools = {t["name"]: [v for v in t["values"] if environment in v["environments"]]
             for t in catalogue["tables"]}
    pools = {name: values for name, values in pools.items() if values}
    traits = dict(pins)
    # Weather goes first even when the user reorders headings in the table editor.
    order = sorted(pools, key=lambda n: 0 if n in ("Weather", "Time") else 2 if n in ("Motion", "Lighting") else 1)
    for name in order:
        if name in traits:
            continue
        options = pools[name]
        if name == "Weather" and pins.get("Motion"):
            weather = _entry(pins["Motion"])[2]
            if weather:
                options = [v for v in options if _entry(v["text"])[2] == weather]
        if name == "Motion":
            weather = _entry(traits["Weather"])[2] if traits.get("Weather") else None
            options = [v for v in options if _entry(v["text"])[2] in (None, weather)]
        if name == "Time" and pins.get("Lighting"):
            required = _time_tag(pins["Lighting"])
            if required:
                options = [v for v in options if _time_tag(v["text"]) == required]
        if name == "Lighting":
            actual = _time_tag(traits.get("Time", ""))
            options = [v for v in options if _time_tag(v["text"]) in (None, actual)]
        if not options:
            raise ValueError(f"No compatible enabled entries in {name}; adjust the pinned traits or tables")
        traits[name] = rng.choices(options, weights=[v["weight"] for v in options], k=1)[0]["text"]
    _validate_traits(traits, environment, catalogue)
    return {name: traits[name] for name in pools}


def assemble_prompt(settings, traits):
    intro = (TOPDOWN if settings["view"] == "topdown" else
             "Wide cinematic establishing view with coherent depth and detailed full-frame composition.")
    context = {
        "outdoor": "An outdoor planetary environment with an atmosphere.",
        "indoor": "An enclosed interior. No outdoor precipitation, windblown dust, or atmospheric weather inside.",
        "space": "An exposed vacuum environment. No atmospheric haze, rain, snow, wind, drifting smoke, or clouds among the structures.",
    }[settings["environment"]]
    parts = [intro, context,
             "Lancer science-fiction environment illustration, confident ink linework, restrained halftone texture, believable industrial construction. "
             "Distribute visual interest naturally across the entire image. No people, characters, text, logos or interface overlays."]
    for name, raw in traits.items():
        if settings["view"] == "topdown" and name in ("Sky", "Distant features", "Motion"):
            continue
        if raw:
            description = _entry(raw)[3]
            if name == "Motion":
                parts.append("Visible scene elements for later animation: " + description + ". Depict a single still moment.")
            elif name == "Layout" and settings["view"] == "topdown":
                parts.append("Floor-plan arrangement: " + description + ". Depict all routes and changes of level in plan projection, without perspective depth.")
            else:
                parts.append(f"{name}: {description}.")
    if settings["notes"].strip():
        parts.append("Additional scene and layout direction: " + settings["notes"].strip())
    return "\n".join(parts)


def preview(request, catalogue):
    _object(request, REQUEST_KEYS, "request")
    if request.get("seed") is None:
        request = dict(request, seed=random.SystemRandom().randrange(MAX_SEED + 1))
    settings = _settings(request)
    count = integer(request.get("count", 1), "count", 1, 8)
    traits = request.get("traits", {})
    _object(traits, {t["name"] for t in catalogue["tables"]}, "traits")
    for name, raw in traits.items():
        _text(raw, name)
    locked = request.get("locked", [])
    if not isinstance(locked, list) or not all(isinstance(n, str) for n in locked) or len(set(locked)) != len(locked):
        raise ValueError("locked must be an array of distinct table names")
    if any(n not in traits for n in locked):
        raise ValueError("Every locked table must have a supplied trait (blank is allowed)")
    reroll = request.get("reroll", False)
    if type(reroll) is not bool:
        raise ValueError("reroll must be boolean")
    plans = []
    signatures = set()
    for index in range(count):
        seed = (settings["seed"] + index) % (MAX_SEED + 1)
        pins = traits if index == 0 and not reroll else {n: traits[n] for n in locked}
        _validate_traits(pins, settings["environment"], catalogue)
        rng = random.Random(seed)
        # Resample repeated combinations within the batch when the pools permit it.
        for _ in range(64):
            chosen = _roll(rng, settings["environment"], pins, catalogue)
            signature = tuple(chosen.items())
            if signature not in signatures:
                break
        signatures.add(signature)
        plan = dict(version=1, **dict(settings, seed=seed), traits=chosen)
        plan["prompt"] = assemble_prompt(settings, chosen)
        motion = _entry(chosen["Motion"])[3] + ". " if chosen.get("Motion") else ""
        plan["motionPrompt"] = motion + "The camera is locked off and does not move. Preserve the scene geometry; no new objects or characters."
        plans.append(plan)
    return {"plans": plans}


def validate_plans(request, catalogue):
    _object(request, {"plans"}, "render request")
    plans = request.get("plans")
    if not isinstance(plans, list) or not 1 <= len(plans) <= 8:
        raise ValueError("plans must contain 1 to 8 scene plans")
    for plan in plans:
        _object(plan, PLAN_KEYS, "plan")
        if set(plan) != PLAN_KEYS or type(plan["version"]) is not int or plan["version"] != 1:
            raise ValueError("Every plan must have all version 1 plan fields")
        _settings(plan)
        _validate_traits(plan["traits"], plan["environment"], catalogue)
        required = plan["environment"].capitalize() + " location"
        if not plan["traits"].get(required):
            raise ValueError(f"Every rendered plan requires {required}")
        if not _text(plan["prompt"], "prompt").strip():
            raise ValueError("prompt cannot be blank")
        _text(plan["motionPrompt"], "motionPrompt")
    return plans


def _load_module(filename, name):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ROOT / filename)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def art_module():
    return _load_module("generate-art.py", "lancer_background_art")


def build_scene_graph(plan, prefix):
    art = art_module()
    graph = art.load_api_workflow(ROOT / "workflows/api/Lancer_Scene_Workflow_v1.json")
    slots = art.locate_slots(graph)
    graph[slots.positive]["inputs"]["text"] = plan["prompt"]
    graph[slots.sampler]["inputs"]["seed"] = plan["seed"]
    graph[slots.latent]["inputs"].update(width=plan["width"], height=plan["height"], batch_size=1)
    graph[slots.save]["inputs"]["filename_prefix"] = prefix
    art.prune_orphans(graph)
    return graph


def build_battlemap_graph(image_ref, prompt, seed, width, height, prefix):
    graph = json.loads((ROOT / "workflows/api/Util_Expression_QwenEdit_RMBG_v1.json").read_text(encoding="utf-8"))
    graph["1"]["inputs"]["image"] = image_ref
    graph["8"]["inputs"].update(width=width, height=height)
    graph["9"]["inputs"]["prompt"] = prompt
    graph["11"]["inputs"]["seed"] = seed
    del graph["13"]
    graph["14"] = {"class_type": "SaveImage", "inputs": {"images": ["12", 0], "filename_prefix": prefix}}
    return graph


def write_sidecar(image, metadata):
    destination = Path(image).with_suffix(".background.json")
    fd, temporary = tempfile.mkstemp(prefix=".background-", suffix=".tmp", dir=destination.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(metadata, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save_result(output_dir, stem, data, metadata):
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    # Exclusive creation ensures even concurrent jobs cannot overwrite a result.
    safe_stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", stem).strip(" .")[:140] or "Background"
    while True:
        image = output_dir / f"{safe_stem}-{uuid.uuid4().hex[:12]}.png"
        try:
            with image.open("xb") as stream:
                stream.write(data)
            break
        except FileExistsError:
            continue
    try:
        write_sidecar(image, metadata)
    except Exception:
        image.unlink(missing_ok=True)
        raise
    return image


def battlemap_metadata(source, width, height, seed, notes):
    source = Path(source).resolve(strict=True)
    if not source.is_file() or source.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
        raise ValueError("battlemap source must be an existing PNG, JPEG or WebP image")
    settings = _settings({"width": width, "height": height, "seed": seed, "notes": notes, "view": "topdown"})
    sidecar = source.with_suffix(".background.json")
    original = {}
    if sidecar.exists():
        original = json.loads(sidecar.read_text(encoding="utf-8-sig"))
        if not isinstance(original, dict):
            raise ValueError("Source background metadata must be an object")
    environment = original.get("environment")
    if environment not in ENVIRONMENTS:
        environment = None  # A bespoke source has no reliable context until the reference is interpreted.
    traits = original.get("traits", {})
    if not isinstance(traits, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in traits.items()):
        raise ValueError("Source background traits must be a text mapping")
    prompt = (
        "Redraw this location as a flat 2D overhead tabletop RPG battlemap. "
        "The camera looks vertically down from directly above, exactly 90 degrees to the floor. "
        "Show only floor surfaces, the top surfaces of furniture, and walls as solid dark cross-section outlines. "
        "Remove all ceilings and roofs. Do not show the sides of furniture or the vertical faces of walls. "
        "No perspective, no vanishing point, no isometric view. "
        "Arrange connected rooms or terrain areas and clear walkable routes. "
        "Keep the reference colors, materials and illustration style. Gridless, no text."
    )
    if notes.strip():
        prompt += "\nMap layout direction: " + notes.strip()
    return dict(settings, version=1, kind="battlemap", environment=environment, traits=traits,
                prompt=prompt, motionPrompt="", source={"path": str(source), "mtime": source.stat().st_mtime_ns / 1_000_000})
