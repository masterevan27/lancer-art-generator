#!/usr/bin/env python3
"""Turn one image into a looping animated .webp through Wan 2.2 I2V.

Point it at a portrait, get back a short animation of that same face - a
blink, a faint smile, a few degrees of head tilt - that loops back to the
source frame without a visible cut.

Point it at a scene with --background and the same machinery animates a
landscape instead: drifting smoke, flickering neon, cloud crossing a sky,
sized and quantised for a SillyTavern chat background.

A standalone entry point rather than a flag on generate-npc.py: this takes any
image on disk, not a rolled NPC, and it has no use for the tables, the
manifest or the output tree. It borrows only the ComfyUI plumbing.

    python animate-portrait.py portrait.png
    python animate-portrait.py portrait.png -d "she tilts her head and smiles"
    python animate-portrait.py portrait.png --out G:\\art\\jules.webp --seed 7
    python animate-portrait.py portrait.png --frames 49 --size 512
    python animate-portrait.py portrait.png --roll --seed 7
    python animate-portrait.py portrait.png --dry-run

    python animate-portrait.py canyon.png --background
    python animate-portrait.py canyon.png --background --roll --seed 7
    python animate-portrait.py canyon.png --background --no-pingpong

Full documentation: docs/animate-portrait.md
"""
import argparse
import collections
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
WORKFLOWS = SCRIPT_DIR / "workflows" / "api"
WORKFLOW = WORKFLOWS / "Util_Portrait_to_AnimatedWEBP_Wan22_v1.json"

# The same graph with the ping-pong tail cut off: the decode feeds the save
# node directly. A second checked-in file rather than three deletions from
# the first, because those three nodes are the graph's only custom-node
# dependency (KJNodes) - as a file of its own it is a workflow that opens
# and runs on stock ComfyUI, and it is covered by the same shape tests the
# looping one is rather than only by a patching test.
WORKFLOW_FORWARD = WORKFLOWS / "Util_Portrait_to_AnimatedWEBP_Wan22_Forward_v1.json"

# The one table in the NPC generator's file that the NPC generator never
# rolls: a pool of positive prompts for this script. It lives beside the NPC
# tables rather than in a file of its own so the import GUI's Tables tab
# edits it with the same editor, and so a portrait and its animation are
# authored from one place.
DEFAULT_TABLES = SCRIPT_DIR / "prompts" / "npc-generator-tables.md"
ANIMATION_TABLE = "Animation"

# The same arrangement one file over, for --background. Scene motion is not
# an NPC trait, so its pool lives with the other subject-free scene tables
# rather than in the NPC file, and the Tables tab edits it the same way.
BACKGROUND_TABLES = SCRIPT_DIR / "prompts" / "scene-and-spaceship-tables.md"
BACKGROUND_TABLE = "Background Animation"


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

# The same job for a landscape. Every clause moves weather, light, machinery
# or sky rather than a subject, because a background has no subject to move -
# and because a clause about a person is an invitation for Wan to draw one
# into an empty frame. The last clause pins the camera for the same reason it
# does above.
BACKGROUND_DESCRIPTION = (
    "Smoke, dust and thin haze drift slowly across the scene. Cloud slides "
    "gently across the sky, and distant lights flicker and pulse. Loose "
    "cables, banners and stray debris stir in a light wind. The buildings, "
    "terrain and machinery stay exactly where they are, and the camera is "
    "locked off and does not move."
)

# The portrait guard's middle clause is about a face keeping its identity,
# which a canyon does not have. What breaks a background instead is its
# geometry crawling - walls leaning, a horizon sliding - so the guard is
# rewritten around that and around the camera staying put.
BACKGROUND_NEGATIVE = (
    "static, frozen, still image, no motion, camera pan, camera zoom, camera "
    "shake, dolly, parallax, warping geometry, melting buildings, shifting "
    "horizon, crawling terrain, morphing, cut, jump cut, text, watermark, "
    "blurry, low quality, worst quality"
)

# What --background actually is: one bundle of defaults, swapped as a set.
# Everything downstream of parse_args - the upload, the graph, the loop, the
# download - is the same job either way, which is why this is a flag on this
# script rather than a second script beside it.
Preset = collections.namedtuple(
    "Preset", "describe negative tables table width height prefix quality")

# Generated frames, before the loop doubles them: 33 in, a 64-frame 4-second
# loop out at 16 fps. The forward-only default is derived from this one rather
# than written down beside it, so raising this raises both.
DEFAULT_FRAMES = 33

PORTRAIT_PRESET = Preset(
    describe=DEFAULT_DESCRIPTION, negative=DEFAULT_NEGATIVE,
    tables=DEFAULT_TABLES, table=ANIMATION_TABLE,
    width=480, height=480, prefix="AnimatedPortraits", quality=90)

# 832x480 is Wan 2.2's native landscape bucket, and SillyTavern scales a
# background to the window with CSS - so rendering it larger buys nothing but
# render time. Quality 80 rather than the portrait's 90 because this file is
# fetched on every page load of the chat UI, and a 64-frame webp at 90 is
# several megabytes of wallpaper.
BACKGROUND_PRESET = Preset(
    describe=BACKGROUND_DESCRIPTION, negative=BACKGROUND_NEGATIVE,
    tables=BACKGROUND_TABLES, table=BACKGROUND_TABLE,
    width=832, height=480, prefix="AnimatedBackgrounds", quality=80)


def load_descriptions(tables_path, heading=ANIMATION_TABLE):
    """The `## <heading>` bullets of a tables file, weights expanded.

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
        match = re.match(r"^##\s+(?!#)\s*(.*?)\s*$", line)
        if match:
            inside = match.group(1) == heading
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
            % (tables_path.name, heading))
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


def snap_frames_up(frames):
    """The nearest frame count Wan will accept, at or above `frames`.

    Rounding the other way, for the one caller that is matching a length
    rather than honouring a ceiling: a ping-pong total is always even and a
    Wan length is always odd, so an exact match is arithmetically impossible
    and the choice is one frame over or three frames under.
    """
    return max(1, -(-(int(frames) - 1) // 4) * 4 + 1)


def played_frames(frames, pingpong):
    """How many frames the finished .webp actually shows.

    Ping-pong plays the batch forward and then back minus the frame at each
    end, so it is very nearly double. Forward-only shows what was generated.
    """
    return frames + max(1, frames - 2) if pingpong else frames


def forward_frames(frames):
    """Frames to generate for a forward loop as long as `frames` ping-ponged.

    What makes --no-pingpong a usable default rather than a way to halve the
    output: without this, dropping the loop silently halves the animation.
    """
    return snap_frames_up(played_frames(frames, True))


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
            "%s appears %d times in the workflow" % (class_type, len(found)))
    return found[0]


def build_graph(image_ref, description, negative, width, height, frames, fps,
                steps, cfg, seed, prefix, pingpong=True):
    """The checked-in workflow, patched into one job. -> a new graph dict.

    Which of the two workflows is chosen by `pingpong`: they differ only in
    what sits between the decode and the save, and every patch below applies
    to both.

    Deep-copied from a fresh read every call: the graph is mutated in place
    here, and a shared dict would carry one run's settings into the next.
    """
    source = WORKFLOW if pingpong else WORKFLOW_FORWARD
    graph = copy.deepcopy(json.loads(source.read_text(encoding="utf-8")))

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


def resolve_preset(args):
    """Fill whatever the caller left unset from the chosen preset.

    Applied after parsing rather than as argparse defaults because which
    default is right is not known until --background has been seen. Every
    option keeps its "unset" value as None so an explicit flag is always
    distinguishable from a default, and so it always wins.
    """
    preset = BACKGROUND_PRESET if args.background else PORTRAIT_PRESET
    for name in ("describe", "negative", "tables", "quality"):
        if getattr(args, name) is None:
            setattr(args, name, getattr(preset, name))
    args.table = preset.table
    args.prefix = preset.prefix
    args.width = snap_size(args.width or args.size or preset.width)
    args.height = snap_size(args.height or args.size or preset.height)
    # Mode-dependent for the same reason the sizes are preset-dependent: what
    # the caller cares about is how long the animation runs, and the number of
    # frames that buys depends on whether the loop is going to double them.
    if args.frames is None:
        args.frames = (DEFAULT_FRAMES if args.pingpong
                       else forward_frames(DEFAULT_FRAMES))
    return args


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Animate an image into a looping .webp via Wan 2.2 I2V.")
    parser.add_argument("image", help="the portrait or scene to animate")
    parser.add_argument(
        "--background", action="store_true",
        help="animate a scene rather than a face: widescreen, scene motion, "
             "and --roll reads the '## %s' table" % BACKGROUND_TABLE)
    motion = parser.add_mutually_exclusive_group()
    motion.add_argument(
        "-d", "--describe",
        help="what moves; defaults to a subtle idle motion for the preset")
    motion.add_argument(
        "--roll", action="store_true",
        help="draw the description from the preset's table instead; "
             "--seed pins the draw")
    parser.add_argument(
        "--tables", type=Path,
        help="the tables file --roll reads (default: %s, or %s with "
             "--background)" % (DEFAULT_TABLES.name, BACKGROUND_TABLES.name))
    parser.add_argument("--negative")
    parser.add_argument("--out", help="output .webp (default: <image>-animated.webp)")
    parser.add_argument("--size", type=int,
                        help="square render size, snapped to 16 "
                             "(default: 480; 832x480 with --background)")
    parser.add_argument("--width", type=int, help="override --size")
    parser.add_argument("--height", type=int, help="override --size")
    parser.add_argument("--frames", type=int,
                        help="frames generated, snapped to 4n+1 (default: %d, "
                             "or %d with --no-pingpong, which are the same "
                             "length played)"
                             % (DEFAULT_FRAMES, forward_frames(DEFAULT_FRAMES)))
    parser.add_argument("--fps", type=float, default=16.0)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--cfg", type=float, default=3.5)
    parser.add_argument("--seed", type=int, default=-1, help="-1 rolls one")
    parser.add_argument("--quality", type=int,
                        help="webp quality 0-100 (default: 90; 80 with "
                             "--background)")
    parser.add_argument("--no-pingpong", dest="pingpong", action="store_false",
                        help="play forward only, at the same length: --frames "
                             "defaults to the whole loop rather than half of "
                             "it, so it costs roughly twice the render")
    parser.add_argument("--dry-run", action="store_true",
                        help="build the job and print it; queue nothing")
    parser.add_argument("--server", help="ComfyUI address (default: probe 8000-8015)")
    parser.add_argument("--timeout", type=float, default=3600.0,
                        help="seconds to wait for the render (default: 3600)")
    return resolve_preset(parser.parse_args(argv))


def main(argv=None):
    args = parse_args(argv)

    image = Path(args.image).expanduser()
    if not args.dry_run and not image.exists():
        raise SystemExit("no such image: %s" % image)

    width, height = args.width, args.height
    frames = snap_frames(args.frames)
    seed = resolve_seed(args.seed)
    destination = output_path(image, args.out)

    # After the seed is settled, so one --seed reproduces both the draw and
    # the render it went into.
    if args.roll:
        args.describe = roll_description(
            load_descriptions(args.tables, args.table), seed)

    if frames != args.frames:
        print("  frames %d -> %d (Wan takes 4n+1)" % (args.frames, frames))

    total = played_frames(frames, args.pingpong)
    print("%s -> %s" % (image.name, destination))
    print("  %dx%d, %d frames -> %d played %s at %.3g fps (%.1fs), seed %d"
          % (width, height, frames, total,
             "ping-ponged" if args.pingpong else "forward",
             args.fps, total / args.fps, seed))
    print("  %s%s" % ("(rolled) " if args.roll else "", args.describe))

    if args.dry_run:
        graph = build_graph(
            image_ref="<uploaded at run time>", description=args.describe,
            negative=args.negative, width=width, height=height, frames=frames,
            fps=args.fps, steps=args.steps, cfg=args.cfg, seed=seed,
            prefix=args.prefix + "/" + image.stem, pingpong=args.pingpong)
        print(json.dumps(graph, indent=2))
        return 0

    comfy = art.find_server(args.server)
    print("  uploading...")
    ref = upload_image(comfy, image)

    graph = build_graph(
        image_ref=ref, description=args.describe, negative=args.negative,
        width=width, height=height, frames=frames, fps=args.fps,
        steps=args.steps, cfg=args.cfg, seed=seed,
        prefix=args.prefix + "/" + image.stem, pingpong=args.pingpong)
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
