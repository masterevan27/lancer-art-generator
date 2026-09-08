#!/usr/bin/env python3
"""Turn one portrait into a looping animated .webp through Wan 2.2 I2V.

Point it at an image, get back a short animation of that same face - a blink,
a faint smile, a few degrees of head tilt - that loops back to the source
frame without a visible cut.

A standalone entry point rather than a flag on generate-npc.py: this takes any
image on disk, not a rolled NPC, and it has no use for the tables, the
manifest or the output tree. It borrows only the ComfyUI plumbing.

    python animate-portrait.py portrait.png
    python animate-portrait.py portrait.png -d "she tilts her head and smiles"
    python animate-portrait.py portrait.png --out G:\\art\\jules.webp --seed 7
    python animate-portrait.py portrait.png --frames 49 --size 512
    python animate-portrait.py portrait.png --roll --seed 7
    python animate-portrait.py portrait.png --dry-run

Full documentation: docs/animate-portrait.md
"""
import argparse
import copy
import importlib.util
import json
import random
import re
import sys
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
WORKFLOW = SCRIPT_DIR / "workflows" / "api" / "Util_Portrait_to_AnimatedWEBP_Wan22_v1.json"

# The one table in the NPC generator's file that the NPC generator never
# rolls: a pool of positive prompts for this script. It lives beside the NPC
# tables rather than in a file of its own so the import GUI's Tables tab
# edits it with the same editor, and so a portrait and its animation are
# authored from one place.
DEFAULT_TABLES = SCRIPT_DIR / "prompts" / "npc-generator-tables.md"
ANIMATION_TABLE = "Animation"


def _load_art():
    """Import generate-art.py, for the Comfy client and the server probe.

    The by-path load its own docstring describes - the hyphen keeps it off the
    normal import path. generate-art.py, not generate-npc.py: the NPC module
    would drag 4,600 lines of roll tables in behind it, and animating a
    portrait needs none of them.
    """
    path = SCRIPT_DIR / "generate-art.py"
    if not path.exists():
        raise SystemExit(
            "generate-art.py not found next to this script (%s)" % SCRIPT_DIR)
    spec = importlib.util.spec_from_file_location("lancer_generate_art", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["lancer_generate_art"] = module
    spec.loader.exec_module(module)
    return module


art = _load_art()


# The shipped motion. Written as prose because Wan reads prose, and kept to
# things a portrait can do without leaving the frame: the face is the subject,
# so every clause moves the face and the last one nails the camera down. Wan
# will invent a dolly-in given the chance, and a portrait that drifts is no
# longer a portrait of the thing it started as.
DEFAULT_DESCRIPTION = (
    "The character breathes gently and holds the viewer's gaze. They blink "
    "slowly, their head tilts a few degrees, and the corner of their mouth "
    "lifts into a faint, subtle smile. Hair and clothing shift very "
    "slightly. The camera is locked off and does not move."
)

# The two ways this particular job fails: nothing moves at all, or the face
# stops being the face in the source image.
DEFAULT_NEGATIVE = (
    "static, frozen, still image, no motion, distorted face, deformed "
    "features, morphing, identity change, different person, extra limbs, "
    "camera pan, camera zoom, cut, jump cut, text, watermark, blurry, "
    "low quality, worst quality"
)


def load_descriptions(tables_path):
    """The `## Animation` bullets of a tables file, weights expanded.

    A five-line reading of generate-npc.py's parse_tables() rather than an
    import of it - that module is 4,600 lines of roll tables, and this needs
    one heading. The conventions it honours are the two that file documents:
    `## Heading` opens a table, `- text` is a bullet, and a leading `xN `
    repeats the bullet N times. Anything else - prose, HTML comments, a
    bullet the GUI has disabled by wrapping it in a comment - is not a bullet
    and is skipped.
    """
    tables_path = Path(tables_path)
    if not tables_path.exists():
        raise SystemExit("no such tables file: %s" % tables_path)
    found = []
    inside = False
    for line in tables_path.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^##\s+(?!#)\s*(.*?)\s*$", line)
        if heading:
            inside = heading.group(1) == ANIMATION_TABLE
            continue
        bullet = re.match(r"^-\s+(.*?)\s*$", line)
        if inside and bullet:
            text = bullet.group(1)
            weight = re.match(r"^x(\d+)\s+(.*)$", text)
            count, text = (int(weight.group(1)), weight.group(2)) if weight else (1, text)
            found.extend([text] * count)
    if not found:
        raise SystemExit(
            "%s has no '## %s' table to roll a description from"
            % (tables_path.name, ANIMATION_TABLE))
    return found


def roll_description(descriptions, seed):
    """One entry, chosen by `seed` so a --roll is as repeatable as the render."""
    if not descriptions:
        raise SystemExit("no animation descriptions to roll from")
    return random.Random(int(seed)).choice(descriptions)


def snap_frames(frames):
    """The nearest frame count Wan will accept, at or below `frames`.

    WanImageToVideo.length steps by 4 from 1 - a latent is 4 frames per step
    plus the leading one. An illegal length is rejected at queue time with a
    validation error that names a number rather than a fix, so round here.
    """
    return max(1, ((int(frames) - 1) // 4) * 4 + 1)


def snap_size(pixels):
    """The nearest multiple of 16 at or below `pixels` (the latent grid)."""
    return max(16, (int(pixels) // 16) * 16)


def resolve_seed(seed):
    """-1 means roll one, so repeated runs are not one render repeated."""
    return random.randrange(0, 2**32 - 1) if int(seed) < 0 else int(seed)


def output_path(image, out):
    """Where the .webp lands: beside the portrait unless told otherwise."""
    if out:
        return Path(out)
    return image.parent / (image.stem + "-animated.webp")


def _node(graph, class_type):
    """The id of the single node of this class."""
    found = [n for n, d in graph.items() if d["class_type"] == class_type]
    if len(found) != 1:
        raise RuntimeError(
            "%s appears %d times in %s" % (class_type, len(found), WORKFLOW.name))
    return found[0]


def build_graph(image_ref, description, negative, width, height, frames, fps,
                steps, cfg, seed, prefix, pingpong=True):
    """The checked-in workflow, patched into one job. -> a new graph dict.

    Deep-copied from a fresh read every call: the graph is mutated in place
    here, and a shared dict would carry one run's settings into the next.
    """
    graph = copy.deepcopy(json.loads(WORKFLOW.read_text(encoding="utf-8")))

    graph[_node(graph, "LoadImage")]["inputs"]["image"] = image_ref

    i2v = graph[_node(graph, "WanImageToVideo")]["inputs"]
    i2v.update(width=width, height=height, length=frames)
    graph[i2v["positive"][0]]["inputs"]["text"] = description
    graph[i2v["negative"][0]]["inputs"]["text"] = negative

    # One denoise split across two models: same seed, same step count, and the
    # handover at the midpoint. High noise builds the motion, low noise
    # resolves the detail.
    half = max(1, steps // 2)
    for nid, node in graph.items():
        if node["class_type"] != "KSamplerAdvanced":
            continue
        first = node["inputs"]["add_noise"] == "enable"
        node["inputs"].update(
            noise_seed=seed, steps=steps, cfg=cfg,
            start_at_step=0 if first else half,
            end_at_step=half if first else 10000)

    save = graph[_node(graph, "SaveAnimatedWEBP")]["inputs"]
    save.update(fps=float(fps), filename_prefix=prefix)

    if pingpong:
        # The reversed half skips the frame at each end, both of which the
        # forward half already shows: without the trim the loop stutters on a
        # doubled frame at the turnaround and again at the seam.
        graph[_node(graph, "GetImageRangeFromBatch")]["inputs"].update(
            start_index=1, num_frames=max(1, frames - 2))
    else:
        # Dropped, not just bypassed - a dangling node still executes, and
        # these three are the graph's only custom-node dependency (KJNodes).
        decode = _node(graph, "VAEDecode")
        save["images"] = [decode, 0]
        for cls in ("ReverseImageBatch", "GetImageRangeFromBatch", "ImageBatch"):
            del graph[_node(graph, cls)]

    return graph


def _multipart(fields, field_name, filename, blob, content_type):
    """A multipart/form-data (content_type, body) for one file plus fields.

    The standard library has no builder for this and ComfyUI's /upload/image
    wants nothing else.
    """
    boundary = "----lancerportrait%s" % uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        parts.append(
            ('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n'
             % (boundary, name, value)).encode("utf-8"))
    parts.append(
        ('--%s\r\nContent-Disposition: form-data; name="%s"; filename="%s"\r\n'
         'Content-Type: %s\r\n\r\n'
         % (boundary, field_name, filename, content_type)).encode("utf-8"))
    parts.append(blob)
    parts.append(("\r\n--%s--\r\n" % boundary).encode("utf-8"))
    return "multipart/form-data; boundary=%s" % boundary, b"".join(parts)


CONTENT_TYPES = {".png": "image/png", ".jpg": "image/jpeg",
                 ".jpeg": "image/jpeg", ".webp": "image/webp"}


def upload_image(comfy, path, subfolder="lancer-portraits"):
    """Put the portrait in ComfyUI's input folder; return its LoadImage ref.

    Uploading rather than referencing a path: the server may not share a
    filesystem with this script, and an arbitrary source image is not already
    somewhere ComfyUI can see.
    """
    content_type, body = _multipart(
        {"type": "input", "subfolder": subfolder, "overwrite": "true"},
        "image", path.name, path.read_bytes(),
        CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream"))
    request = urllib.request.Request(
        comfy.base + "/upload/image", data=body,
        headers={"Content-Type": content_type})
    with urllib.request.urlopen(request, timeout=120) as resp:
        info = json.loads(resp.read().decode("utf-8"))
    sub = info.get("subfolder", "")
    name = "%s/%s" % (sub, info["name"]) if sub else info["name"]
    return "%s [input]" % name.replace("\\", "/")


def save_result(comfy, record, destination):
    """Download the finished animation and write it to `destination`.

    SaveAnimatedWEBP reports its output under the same "images" key a still
    render uses, so the .webp is picked by suffix rather than by position - a
    setup that also emits a poster frame would otherwise save the poster.
    """
    outputs = [i for node in record.get("outputs", {}).values()
               for i in node.get("images", [])]
    animations = [i for i in outputs
                  if i["filename"].lower().endswith(".webp")]
    if not animations:
        raise SystemExit(
            "the job finished but produced no .webp (outputs: %s)"
            % json.dumps(outputs)[:400])

    image = animations[0]
    query = urllib.parse.urlencode({
        "filename": image["filename"],
        "subfolder": image.get("subfolder", ""),
        "type": image.get("type", "output")})
    data = comfy._get_bytes("/view?" + query)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return data


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Animate a portrait into a looping .webp via Wan 2.2 I2V.")
    parser.add_argument("image", help="the portrait to animate")
    motion = parser.add_mutually_exclusive_group()
    motion.add_argument(
        "-d", "--describe", default=DEFAULT_DESCRIPTION,
        help="what the character does; defaults to a subtle idle motion")
    motion.add_argument(
        "--roll", action="store_true",
        help="draw the description from the tables file's '## %s' table "
             "instead; --seed pins the draw" % ANIMATION_TABLE)
    parser.add_argument(
        "--tables", type=Path, default=DEFAULT_TABLES,
        help="the tables file --roll reads (default: %s)" % DEFAULT_TABLES.name)
    parser.add_argument("--negative", default=DEFAULT_NEGATIVE)
    parser.add_argument("--out", help="output .webp (default: <image>-animated.webp)")
    parser.add_argument("--size", type=int, default=480,
                        help="square render size, snapped to 16 (default: 480)")
    parser.add_argument("--width", type=int, help="override --size")
    parser.add_argument("--height", type=int, help="override --size")
    parser.add_argument("--frames", type=int, default=33,
                        help="frames generated, snapped to 4n+1 (default: 33)")
    parser.add_argument("--fps", type=float, default=16.0)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--cfg", type=float, default=3.5)
    parser.add_argument("--seed", type=int, default=-1, help="-1 rolls one")
    parser.add_argument("--quality", type=int, default=90,
                        help="webp quality 0-100 (default: 90)")
    parser.add_argument("--no-pingpong", dest="pingpong", action="store_false",
                        help="play forward only; the loop point will show")
    parser.add_argument("--dry-run", action="store_true",
                        help="build the job and print it; queue nothing")
    parser.add_argument("--server", help="ComfyUI address (default: probe 8000-8015)")
    parser.add_argument("--timeout", type=float, default=3600.0,
                        help="seconds to wait for the render (default: 3600)")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    image = Path(args.image).expanduser()
    if not args.dry_run and not image.exists():
        raise SystemExit("no such image: %s" % image)

    width = snap_size(args.width or args.size)
    height = snap_size(args.height or args.size)
    frames = snap_frames(args.frames)
    seed = resolve_seed(args.seed)
    destination = output_path(image, args.out)

    # After the seed is settled, so one --seed reproduces both the draw and
    # the render it went into.
    if args.roll:
        args.describe = roll_description(load_descriptions(args.tables), seed)

    if frames != args.frames:
        print("  frames %d -> %d (Wan takes 4n+1)" % (args.frames, frames))

    total = frames + max(1, frames - 2) if args.pingpong else frames
    print("%s -> %s" % (image.name, destination))
    print("  %dx%d, %d frames -> %d played at %.3g fps (%.1fs), seed %d"
          % (width, height, frames, total, args.fps, total / args.fps, seed))
    print("  %s%s" % ("(rolled) " if args.roll else "", args.describe))

    if args.dry_run:
        graph = build_graph(
            image_ref="<uploaded at run time>", description=args.describe,
            negative=args.negative, width=width, height=height, frames=frames,
            fps=args.fps, steps=args.steps, cfg=args.cfg, seed=seed,
            prefix="AnimatedPortraits/" + image.stem, pingpong=args.pingpong)
        print(json.dumps(graph, indent=2))
        return 0

    comfy = art.find_server(args.server)
    print("  uploading...")
    ref = upload_image(comfy, image)

    graph = build_graph(
        image_ref=ref, description=args.describe, negative=args.negative,
        width=width, height=height, frames=frames, fps=args.fps,
        steps=args.steps, cfg=args.cfg, seed=seed,
        prefix="AnimatedPortraits/" + image.stem, pingpong=args.pingpong)
    graph[_node(graph, "SaveAnimatedWEBP")]["inputs"]["quality"] = args.quality

    started = time.time()
    prompt_id = comfy.queue(graph)
    print("  queued %s - a 14B two-stage pass is minutes, not seconds" % prompt_id)
    record = comfy.wait(prompt_id, timeout=args.timeout)

    data = save_result(comfy, record, destination)

    print("  %s (%.1f KB) in %.0fs"
          % (destination, len(data) / 1024.0, time.time() - started))
    return 0


if __name__ == "__main__":
    sys.exit(main())
