#!/usr/bin/env python3
"""Turn a generated NPC into a rigged GLB, a printable STL and turnarounds.

Reads .generated-npcs.json, so the whole existing back catalogue is eligible.
Four stages per NPC: re-render the token in a forced A-pose, reconstruct a
clothed shell and a rigged body from that one image, assemble them in headless
Blender, and write the results into the NPC's own folder.

A separate command rather than a flag on generate-npc.py: reconstruction is
slow and failure-prone, and it must never be able to break art generation.

    python generate-3d.py --filter Sokolova
    python generate-3d.py --id npc-jules-sokolova-40213 --stage apose
    python generate-3d.py --id npc-jules-sokolova-40213 --image apose.png
    python generate-3d.py --image figure.png --out G:\\3d\\jules
"""
import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import uuid
import zlib
from collections import namedtuple
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _load_npc_generator():
    """Import generate-npc.py, and through it generate-art.py.

    The same by-path load generate-npc.py uses on generate-art.py, for the
    same reason: the hyphen keeps it off the normal import path, and renaming
    it would invalidate every README, docstring and shell history that names
    it. Importing it is safe - its main() sits behind an
    `if __name__ == "__main__"` guard, so nothing runs on import.
    """
    path = SCRIPT_DIR / "generate-npc.py"
    if not path.exists():
        raise SystemExit("generate-npc.py not found next to this script (%s)" % SCRIPT_DIR)
    name = "lancer_generate_npc"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    # Registered before the body runs: generate-npc.py's own @dataclass use
    # resolves annotations through sys.modules[cls.__module__].
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


npc_gen = _load_npc_generator()
art = npc_gen.art

# The Stance every 3D source render is forced into.
#
# Written as an ordinary Stance bullet - lowercase, no trailing period - so it
# composes with the token template's "{Subject} {is_are} {stance}, both feet in
# frame" exactly as a rolled bullet does. A module constant here rather than a
# bullet in the tables file because no ROLLED NPC should ever get it: it is a
# reconstruction jig, not a pose anyone wants art of.
#
# A-pose is not a preference. The SAM3DBody base always comes out in A-pose
# (spec §2.4), the Hunyuan3D shell inherits the pose of its source image, and
# proximity-based weight transfer across a mismatch smears the shoulders. It
# also improves the reconstruction on its own, by separating the limbs from the
# torso so the arms do not fuse to the body.
APOSE_STANCE = (
    "standing straight and squarely facing the viewer, arms held slightly away "
    "from the sides with the palms forward, feet shoulder-width apart"
)


def apose_npc(entry):
    """The npc dict for one manifest entry, re-posed for reconstruction.

    Rebuilt the way regenerate_one() rebuilds it - migrate_traits(),
    pronoun_fields(), the recorded 'young' flag, the Height backfill - and then
    changed in exactly two ways: the Stance is replaced, and both hands are
    emptied.

    Emptying the hands is not optional. carry_sentence() puts the Weapon and
    the Gear in the subject's hands, and an NPC holding a carbine in both hands
    cannot hold an A-pose; the prompt would assert both at once and the model
    would resolve it by rendering neither. roll_npc() already filters Stance
    against occupied hands for the same reason - this is that rule reached from
    the other side, since here the stance is fixed and the equipment is what
    has to give.

    Gear goes with the Weapon rather than being kept: the Gear table is
    equipment held in a hand or slung over a shoulder, so it occupies a hand as
    readily as a weapon does.

    The entry is not mutated - the caller still needs it for the dossier and
    the log line.
    """
    npc = npc_gen.migrate_traits(entry["traits"])
    npc["_pronouns"] = npc_gen.pronoun_fields(npc["Pronouns"])
    npc["_young"] = entry.get("young", False)
    npc["_outfit_notac"] = entry.get("outfit_notac")
    if "Height" not in npc:
        # Written before '## Height' existed. build_prompts() has no shim for
        # this one, unlike Weapon, so supply what regenerate_one() supplies.
        npc["Height"] = "of average height"
    npc["Stance"] = APOSE_STANCE
    npc["Weapon"] = ""
    npc["Gear"] = ""
    return npc


# --------------------------------------------------------------------------
# The NPC's real height
# --------------------------------------------------------------------------

FEET = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
        "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}

# Checked against the text BEFORE the feet-and-inches phrase, longest first so
# that "just a few inches under six feet" reads as -3 and not as "just under".
NUDGES = (
    ("several inches over", 3), ("several inches under", -3),
    ("a few inches over", 3), ("a few inches under", -3),
    ("a little over", 1), ("a little under", -1),
    ("a shade over", 1), ("a shade under", -1),
    ("just over", 1), ("just under", -1),
    ("close to", -1), ("brushing", -1), ("nearly", -1),
)

NOMINAL_HEIGHT_M = 1.8288   # six feet, what --print-height-mm describes


def height_inches(bullet):
    """A '## Height' bullet's height in inches, or None if it names none.

    Parsed rather than looked up in a table of the twelve current bullets,
    because generate-3d.py's whole premise is that the back catalogue is
    eligible: a manifest entry stores the bullet text as it was when rolled,
    and a bullet since reworded would miss an exact-match table without
    anything noticing. Every bullet in both '## Height' tables says its height
    in words, so reading it is more robust than indexing it.

    None is not an error. 'of average height' is what regenerate_one() backfills
    for an entry written before '## Height' existed, and it names no number;
    the caller falls back to SAM3DBody's estimate rather than refusing to build
    the NPC over a refinement.
    """
    text = bullet.lower()
    match = re.search(r"\b(\w+)\s+and\s+a\s+half\s+feet\b", text)
    if match and match.group(1) in FEET:
        feet, extra = FEET[match.group(1)], 6
    else:
        match = re.search(r"\b(\w+)\s+(?:foot|feet)\b(?:\s+(\w+))?", text)
        if not match or match.group(1) not in FEET:
            return None
        feet, extra = FEET[match.group(1)], FEET.get(match.group(2) or "", 0)
    head = text[:match.start()].rstrip()
    for phrase, delta in NUDGES:
        if head.endswith(phrase):
            return feet * 12 + extra + delta
    return feet * 12 + extra


def height_metres(bullet):
    """Same, in metres, or None."""
    inches = height_inches(bullet)
    return None if inches is None else round(inches * 0.0254, 4)


def apose_prompt(entry):
    """The token prompt Stage 0 renders. The portrait half is discarded."""
    return npc_gen.build_prompts(apose_npc(entry))[1]


# --------------------------------------------------------------------------
# Who a reconstruction is of
# --------------------------------------------------------------------------

# Everything the stages need to know about their subject, and nothing else:
# the display name the deliverables are called after, the two strings that
# address ComfyUI's output folder, the seed both reconstructions run at, and
# the real height the assembly scales to (None to let SAM3DBody estimate it).
#
# Named as a thing of its own because a manifest entry is not the only way to
# get one. A standalone image has no entry - no traits, no role category, no
# rolled height - and yet it has all five of these. Taking the five out of the
# stages is what lets one code path serve both, rather than a second set of
# stages beside the first that drifts out of step with it.
Subject = namedtuple("Subject", "name category slug seed height")

# The ComfyUI output folder for a run with no NPC behind it. Its own category
# rather than a shared one, so a standalone experiment cannot land in the tree
# a real NPC's renders live in.
STANDALONE_CATEGORY = "Standalone"


def subject_of(entry, args):
    """The Subject of one manifest entry."""
    npc = apose_npc(entry)
    return Subject(
        name=entry["name"],
        category=npc_gen.role_category(npc),
        slug=art._slug(entry["name"]),
        seed=entry["seed"],
        # The NPC's own rolled height, not SAM3DBody's guess at it - and
        # --height-m over both, for an entry whose Height is wrong. None for
        # an entry whose Height names no number (the legacy 'of average
        # height' backfill), and the estimate stands.
        height=args.height_m if args.height_m is not None
        else height_metres(npc["Height"]))


def standalone_subject(args):
    """The Subject of a --out run, which has no manifest entry behind it.

    The name comes from the output folder, not the image: a supplied image is
    typically ComfyUI's own output (apose_rmbg_00011_.png), and that counter
    would end up in every deliverable's filename. Seed 0 because there is no
    recorded seed to reuse and a fixed one at least makes the run repeatable.
    """
    name = args.name or args.out.name
    return Subject(name=name, category=STANDALONE_CATEGORY,
                   slug=art._slug(name), seed=0, height=args.height_m)


# --------------------------------------------------------------------------
# Paths and the stages
# --------------------------------------------------------------------------

MESH_WORKFLOW = art.WORKFLOW_DIR / "Util_Image_to_Mesh_Hunyuan3D_v1.json"
RIG_WORKFLOW = art.WORKFLOW_DIR / "Util_Image_to_RiggedBody_SAM3D_v1.json"
ASSEMBLE_SCRIPT = SCRIPT_DIR / "blender" / "assemble_npc.py"

# Named rather than numbered, so `--stage mesh` says what it does. The order
# is the dependency order: mesh needs apose's PNG, assemble needs mesh's GLBs.
STAGES = ("apose", "mesh", "assemble")

# Where Blender 5.2 LTS installs by default on this machine. LANCER_BLENDER
# overrides it, so a different install or a different version needs no edit.
DEFAULT_BLENDER = Path(
    os.environ.get("LANCER_BLENDER")
    or r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")


def find_blender(explicit=None):
    """The Blender executable, or a SystemExit naming what to set."""
    path = Path(explicit) if explicit else DEFAULT_BLENDER
    if not path.exists():
        raise SystemExit(
            "Blender not found: %s\n"
            "  pass --blender PATH, or set LANCER_BLENDER" % path)
    return path


def npc_3d_folder(folder_path):
    """The 3d/ subfolder inside one NPC's own folder.

    Beside the portrait and the token rather than in a tree of its own, so an
    NPC folder stays self-contained - and so the ignore rules that already
    cover output/ and ComfyUI's own output directory cover this too, with no
    new rule to write (spec §7.4).
    """
    return Path(folder_path) / "3d"


def should_skip(folder, args):
    """True when this NPC already has 3D output and --overwrite was not given.

    An EMPTY 3d/ folder does not count: it is what a crashed run leaves
    behind, and skipping on it would make every such NPC permanently
    unbuildable without --overwrite.

    Only applies when --stage is the full default set of all three stages.
    The docstring above and docs/generate-3d.md both advertise running
    `--stage apose`, inspecting the result, then `--stage mesh` as the normal
    way to iterate - and that sequence is exactly what this skip used to
    break: the second command would see apose.png already on disk and skip
    the NPC entirely. A narrowed --stage means the caller is deliberately
    iterating on one stage, and skipping on leftover output from a previous
    stage would defeat the reason they narrowed it in the first place.
    """
    if set(args.stage) != set(STAGES):
        return False
    return folder.exists() and any(folder.iterdir()) and not args.overwrite


def select_entries(manifest, args):
    """The (folder_path, entry) pairs this run will build, in a stable order.

    Rows without a 'traits' dict are skipped rather than rejected: the
    manifest is a plain JSON object and nothing stops a hand-added row, but
    the whole 3D rebuild starts from traits.
    """
    pairs = sorted((k, v) for k, v in manifest.items()
                   if isinstance(v, dict) and isinstance(v.get("traits"), dict))

    if args.id:
        wanted = set(args.id)
        pairs = [(k, v) for k, v in pairs if v.get("id") in wanted]
        found = {v.get("id") for _, v in pairs}
        # An unknown id is a typo, and a typo that silently builds nothing is
        # indistinguishable from a run that had nothing to do.
        missing = sorted(wanted - found)
        if missing:
            raise SystemExit("no manifest entry with id %s" % ", ".join(missing))

    def text(folder_path, entry):
        """What --filter and --exclude match against.

        Name, callsign AND the folder path - the path is what carries the role
        category (output/LancerNPCs/run3/Crew/jules-sokolova), so `--filter
        Crew` selects by category without the entry having to store one. Spec
        §8 asks for name or category; this gives both from what is already
        there.
        """
        return "%s %s %s" % (folder_path, entry.get("name", ""),
                             entry.get("callsign", ""))

    if args.filter:
        rx = re.compile(args.filter, re.I)
        pairs = [(k, v) for k, v in pairs if rx.search(text(k, v))]
    if args.exclude:
        rx = re.compile(args.exclude, re.I)
        pairs = [(k, v) for k, v in pairs if not rx.search(text(k, v))]
    if args.limit:
        pairs = pairs[:args.limit]
    return pairs


# --------------------------------------------------------------------------
# The dossier's 3D section
# --------------------------------------------------------------------------

DOSSIER_MARKER = "\n## 3D\n"


def dossier_3d_section(files, workflows, stance):
    """The '## 3D' block: what was built, and everything needed to rebuild it.

    The dossier's existing property is that it records enough to reproduce its
    own output - the seed, the tables, both prompts verbatim. The 3D output is
    reproduced from the two workflow graphs and the forced stance instead, so
    those are what this records.
    """
    lines = [
        "## 3D",
        "",
        "Built by `generate-3d.py` on %s." % time.strftime("%Y-%m-%d"),
        "",
    ]
    lines += ["- `3d/%s`" % name for name in files] or ["- _(none built)_"]
    lines += [
        "",
        "### Reproduced by",
        "",
        "| | |",
        "|---|---|",
    ]
    lines += ["| Workflow | `%s` |" % Path(w).name for w in workflows]
    lines += ["| A-pose stance | %s |" % stance, ""]
    return "\n".join(lines)


def append_dossier_3d(path, files, workflows, stance):
    """Add or REPLACE the dossier's '## 3D' section.

    Replace, because a --overwrite re-run would otherwise stack a second
    section under the first and the dossier would stop describing what is
    actually on disk - which is the only thing it is for.
    """
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    cut = text.find(DOSSIER_MARKER)
    if cut != -1:
        text = text[:cut]
    body = dossier_3d_section(files, workflows, stance)
    path.write_text("%s\n\n%s" % (text.rstrip("\n"), body), encoding="utf-8")


# --------------------------------------------------------------------------
# Stage 0: the A-pose source render
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# Squaring the A-pose for reconstruction
# --------------------------------------------------------------------------
#
# CLIPVisionEncode's crop="center" scales the short side to the vision tower's
# resolution and centre-crops the long one. apose.png is 1024x1280 with the
# figure filling y 13..1265, so the crop kept rows 128..1151 and discarded 115
# pixels off the top of the subject and 113 off the bottom - 9% at each end,
# about six inches of a five-foot-nine figure. Hunyuan3D reconstructed exactly
# what it was shown: a helmet sliced flat across the crown, and trouser legs
# ending in stumps with no boots at all.
#
# Squaring the image first makes the crop a no-op. Done here rather than in the
# graph because the crop has to be tight to the SUBJECT, and finding the
# subject needs the alpha channel rmbg already produced - the core ComfyUI
# nodes can pad to a fixed size but cannot measure a mask's bounds.
#
# PNG by hand because spec 2.2 rules out a dependency that needs a compiler and
# Pillow is not installed. rmbg's output is always 8-bit RGBA and never
# interlaced, so that one shape is all this has to understand.

APOSE_MARGIN = 0.06     # breathing room around the subject, as a fraction


def _png_read(path):
    """-> (width, height, [bytearray rows]) for an 8-bit RGBA non-interlaced PNG."""
    data = path.read_bytes()
    position, idat, header = 8, [], None
    while position < len(data):
        length = int.from_bytes(data[position:position + 4], "big")
        kind = data[position + 4:position + 8]
        if kind == b"IHDR":
            header = data[position + 8:position + 8 + length]
        elif kind == b"IDAT":
            idat.append(data[position + 8:position + 8 + length])
        position += 12 + length
    if header is None:
        raise ValueError("%s has no IHDR - not a PNG" % path)
    width = int.from_bytes(header[0:4], "big")
    height = int.from_bytes(header[4:8], "big")
    depth, colour, interlace = header[8], header[9], header[12]
    if (depth, colour, interlace) != (8, 6, 0):
        raise ValueError("%s is not 8-bit RGBA non-interlaced (depth=%d colour=%d "
                         "interlace=%d)" % (path, depth, colour, interlace))
    raw, stride = zlib.decompress(b"".join(idat)), width * 4

    def paeth(a, b, c):
        p = a + b - c
        pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
        return a if pa <= pb and pa <= pc else (b if pb <= pc else c)

    rows, previous, position = [], bytearray(stride), 0
    for _ in range(height):
        filter_type = raw[position]
        position += 1
        line = bytearray(raw[position:position + stride])
        position += stride
        if filter_type:
            for i in range(stride):
                a = line[i - 4] if i >= 4 else 0
                b = previous[i]
                c = previous[i - 4] if i >= 4 else 0
                if filter_type == 1:
                    line[i] = (line[i] + a) & 255
                elif filter_type == 2:
                    line[i] = (line[i] + b) & 255
                elif filter_type == 3:
                    line[i] = (line[i] + ((a + b) >> 1)) & 255
                elif filter_type == 4:
                    line[i] = (line[i] + paeth(a, b, c)) & 255
                else:
                    raise ValueError("%s uses PNG filter %d" % (path, filter_type))
        rows.append(line)
        previous = line
    return width, height, rows


def _png_write(path, width, height, rows):
    """Write 8-bit RGBA rows as a PNG. Filter 0 throughout - zlib does the work."""
    def chunk(kind, payload):
        return (len(payload).to_bytes(4, "big") + kind + payload
                + (zlib.crc32(kind + payload) & 0xffffffff).to_bytes(4, "big"))

    raw = b"".join(bytes([0]) + bytes(row) for row in rows)
    path.write_bytes(
        bytes([137, 80, 78, 71, 13, 10, 26, 10])
        + chunk(b"IHDR", width.to_bytes(4, "big") + height.to_bytes(4, "big")
                + bytes((8, 6, 0, 0, 0)))
        + chunk(b"IDAT", zlib.compress(raw, 6))
        + chunk(b"IEND", b""))


def subject_bounds(rows, width, height, threshold=16):
    """(x0, y0, x1, y1) of everything more opaque than `threshold`, or None."""
    x0, y0, x1, y1 = width, height, -1, -1
    for y, row in enumerate(rows):
        opaque = [x for x in range(width) if row[x * 4 + 3] > threshold]
        if not opaque:
            continue
        if y < y0:
            y0 = y
        y1 = y
        if opaque[0] < x0:
            x0 = opaque[0]
        if opaque[-1] > x1:
            x1 = opaque[-1]
    return None if x1 < 0 else (x0, y0, x1, y1)


def square_apose(src, dst, margin=APOSE_MARGIN, threshold=16):
    """Crop `src` to its subject and centre it on a square, uniform backdrop.

    The WHOLE canvas is rebuilt, not just the added margin. Padding alone
    leaves a seam where the flat fill meets the source's faintly textured
    backdrop, and that rectangle is not ignored: Hunyuan3D reconstructed it as
    a slab standing behind the figure. rmbg has already produced an exact alpha
    cutout, so the subject is composited over one flat colour everywhere and no
    edge is left to mistake for geometry. A soft alpha edge is blended rather
    than thresholded, so the silhouette stays antialiased.

    Returns the square's side in pixels.
    """
    width, height, rows = _png_read(src)
    bounds = subject_bounds(rows, width, height, threshold)
    if bounds is None:
        raise RuntimeError(
            "%s is entirely transparent - background removal ate the figure"
            % src.name)
    x0, y0, x1, y1 = bounds
    subject_w, subject_h = x1 - x0 + 1, y1 - y0 + 1
    side = int(max(subject_w, subject_h) * (1 + margin))

    backdrop = (rows[0][0], rows[0][1], rows[0][2])
    flat = bytes(backdrop + (0,))
    out = [bytearray(flat * side) for _ in range(side)]
    ox, oy = (side - subject_w) // 2, (side - subject_h) // 2
    for y in range(subject_h):
        source, target = rows[y0 + y], out[oy + y]
        for x in range(subject_w):
            si, di = (x0 + x) * 4, (ox + x) * 4
            alpha = source[si + 3]
            if not alpha:
                continue
            if alpha == 255:
                target[di:di + 4] = source[si:si + 4]
            else:
                for c in range(3):
                    target[di + c] = ((source[si + c] * alpha
                                       + backdrop[c] * (255 - alpha)) // 255)
                target[di + 3] = alpha
    _png_write(dst, side, side, out)
    return side


def _multipart(fields, field_name, filename, blob):
    """A multipart/form-data (content_type, body) for one file plus fields.

    The standard library has no builder for this and ComfyUI's /upload/image
    wants nothing else. Kept separate from the POST so it can be checked
    without a server.
    """
    boundary = "----lancer3d%s" % uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        parts.append(
            ('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n'
             % (boundary, name, value)).encode("utf-8"))
    parts.append(
        ('--%s\r\nContent-Disposition: form-data; name="%s"; filename="%s"\r\n'
         'Content-Type: image/png\r\n\r\n' % (boundary, field_name, filename)).encode("utf-8"))
    parts.append(blob)
    parts.append(("\r\n--%s--\r\n" % boundary).encode("utf-8"))
    return "multipart/form-data; boundary=%s" % boundary, b"".join(parts)


def upload_image(comfy, path, subfolder="lancer3d"):
    """Put one PNG in ComfyUI's input folder; return its LoadImage reference.

    Stage 1 could reference the Stage 0 output where it already sits on the
    server, with image_ref() - but only inside one run. `--stage mesh` on its
    own, which is the whole point of the flag, has nothing but the file on
    disk. Uploading is the one path that works both ways, so it is the only
    path taken.
    """
    content_type, body = _multipart(
        {"type": "input", "subfolder": subfolder, "overwrite": "true"},
        "image", path.name, path.read_bytes())
    request = urllib.request.Request(
        comfy.base + "/upload/image", data=body, headers={"Content-Type": content_type})
    with urllib.request.urlopen(request, timeout=120) as resp:
        info = json.loads(resp.read().decode("utf-8"))
    sub = info.get("subfolder", "")
    name = "%s/%s" % (sub, info["name"]) if sub else info["name"]
    return "%s [input]" % name.replace("\\", "/")


def render_apose(comfy, args, entry):
    """Render this NPC's token again in the A-pose. -> the raw ComfyUI image dict.

    Renders through the entry's OWN recorded workflow and its own seed, so the
    figure is the same person the token shows - only the pose and the empty
    hands differ. The portrait half of build_prompts() is discarded; nothing
    downstream has a use for a backdrop.

    Still has its background: cut_out() is the other half.
    """
    npc = apose_npc(entry)
    prompt = npc_gen.build_prompts(npc)[1]
    category = npc_gen.role_category(npc)
    slug = art._slug(npc["name"])
    knobs = npc_gen.Knobs(args, npc_gen.TOKEN_SIZE, npc_gen.COMFY_PREFIX)

    workflow_path = npc_gen.resolve_recorded_workflow(entry, npc, args)
    template = art.load_api_workflow(workflow_path)
    try:
        slots = art.locate_slots(template)
    except art.WorkflowError as exc:
        raise SystemExit("%s: %s" % (workflow_path.name, exc))

    job = art.build_job(template, slots,
                        npc_gen.entry_for(category, slug, "apose", prompt),
                        entry["seed"], knobs)
    images = art.Comfy.images(comfy.wait(comfy.queue(job), timeout=args.timeout))
    if not images:
        raise RuntimeError("the A-pose render produced no image")
    time.sleep(args.pause)
    return images[0]


def cut_out(comfy, args, subject, source, folder):
    """Run `source` through --rmbg. -> <folder>/apose.png

    `source` is either an image already sitting on the server - what
    render_apose() returns, referenced in place - or a Path on this machine,
    which is uploaded first. Both arrive at the same rmbg graph; the two
    callers differ only in where their image starts out, and making that the
    argument's business rather than each caller's is what lets --remove-bg
    reuse the half of stage apose that does the actual cutting.
    """
    knobs = npc_gen.Knobs(args, npc_gen.TOKEN_SIZE, npc_gen.COMFY_PREFIX)

    if not args.rmbg.exists():
        raise SystemExit("Background-removal workflow not found: %s" % args.rmbg)
    post = art.load_api_workflow(args.rmbg)
    try:
        post_slots = art.locate_post_slots(post)
    except art.WorkflowError as exc:
        raise SystemExit("%s: %s" % (args.rmbg.name, exc))

    ref = upload_image(comfy, source) if isinstance(source, Path) \
        else art.image_ref(source)
    prefix = "%s/%s/%s/apose_rmbg" % (npc_gen.COMFY_PREFIX,
                                      subject.category, subject.slug)
    cut_job = art.build_post_job(post, post_slots, ref, prefix, subject.seed, knobs)
    cut = art.Comfy.images(comfy.wait(comfy.queue(cut_job), timeout=args.timeout))
    if not cut:
        raise RuntimeError("background removal produced no image")
    time.sleep(args.pause)

    return npc_gen.fetch(comfy, cut[0], folder / "apose.png")


def stage_apose(comfy, args, entry, folder):
    """Render this NPC's token again in the A-pose, cut out. -> <folder>/apose.png

    Takes the entry, not a Subject: the render half needs the whole trait set
    to build a prompt from, which is exactly what a standalone run does not
    have - and is why --out requires --image.
    """
    return cut_out(comfy, args, subject_of(entry, args),
                   render_apose(comfy, args, entry), folder)


# --------------------------------------------------------------------------
# Stage 0, the other way in: an A-pose the caller already has
# --------------------------------------------------------------------------


def has_cutout(path, threshold=16):
    """True when `path` has real transparency - a figure standing on nothing.

    The one property that separates an A-pose ready to reconstruct from a
    render that still has its backdrop, and it cannot be inferred from the
    filename. An image with no transparent pixel anywhere has a background,
    and square_apose() will build its square around the whole canvas rather
    than around the subject - which is how a flat slab ends up standing
    behind the figure in the finished mesh.
    """
    width, _, rows = _png_read(path)
    return any(row[x * 4 + 3] <= threshold for row in rows for x in range(width))


def check_image(args, folders):
    """A SystemExit naming why --image cannot be used for this run.

    Every one of these is cheap to check and expensive to discover later: a
    reconstruction takes minutes on the GPU and answers a wrong input with a
    plausible-looking wrong mesh rather than an error. Checked once here,
    against the run's target folders, rather than inside the per-NPC loop that
    catches SystemExit and turns a global mistake into one failure per NPC.
    """
    if not args.image:
        return

    if len(folders) != 1:
        raise SystemExit(
            "--image is one person's A-pose, but %d NPCs are selected - "
            "narrow the run with --id, or reconstruct the image on its own "
            "with --out DIR" % len(folders))

    # Broad on purpose: _png_read() raises ValueError for a shape it refuses,
    # but a truncated or non-PNG file reaches it as a zlib error or an index
    # out of range instead, and all three mean the same thing to the caller.
    try:
        _png_read(args.image)
    except Exception as exc:
        raise SystemExit("--image cannot be read as an 8-bit RGBA non-interlaced "
                         "PNG: %s" % exc)

    if not args.remove_bg and not has_cutout(args.image):
        raise SystemExit(
            "--image has no transparent pixels, so it still has a background. "
            "A backdrop reconstructs as a flat slab behind the figure; pass "
            "--remove-bg to cut it out first, or supply a cut-out image.")

    apose = folders[0] / "apose.png"
    if apose.exists() and not args.overwrite:
        raise SystemExit("%s already exists - pass --overwrite to replace it "
                         "with --image" % apose)


def install_image(comfy, args, subject, folder):
    """Put --image at <folder>/apose.png, cutting it out first if asked.

    Copied into the NPC's own folder rather than read where it lies: every
    stage downstream - apose_square.png beside it, should_skip(), the dossier
    section - treats 3d/ as the record of what this reconstruction was built
    from, and a source path that only ever existed in one shell history is not
    that record.
    """
    target = folder / "apose.png"
    if args.remove_bg:
        print("    cutting out %s ..." % args.image.name, flush=True)
        return cut_out(comfy, args, subject, args.image, folder)
    target.write_bytes(args.image.read_bytes())
    return target


# --------------------------------------------------------------------------
# Stage 1: the two meshes
# --------------------------------------------------------------------------


def node_of(graph, class_type):
    """The one node of that class_type, or a WorkflowError naming the count.

    Both 3D graphs are checked in beside this script, so addressing their
    nodes by class rather than by id survives a re-export from the ComfyUI
    editor - which renumbers every node - while still failing loudly if
    someone adds a second LoadImage.
    """
    found = [n for n, d in graph.items() if d.get("class_type") == class_type]
    if len(found) != 1:
        raise art.WorkflowError(
            "expected exactly one %s node, found %d" % (class_type, len(found)))
    return found[0]


def build_mesh_job(template, ref, prefix, seed=None):
    """One queueable image -> mesh job. The template is left untouched."""
    graph = json.loads(json.dumps(template))
    graph[node_of(graph, "LoadImage")]["inputs"]["image"] = ref
    graph[node_of(graph, "SaveGLB")]["inputs"]["filename_prefix"] = prefix
    if seed is not None:
        for node in graph.values():
            if node.get("class_type") == "KSampler":
                node["inputs"]["seed"] = seed
    return graph


def mesh_outputs(record, suffix=".glb"):
    """Every saved file in a history record whose filename ends in `suffix`.

    Comfy.images() reads the "images" key, which is right for an image node
    and wrong for SaveGLB - a 3D save reports under a UI key of its own, and
    which key that is has changed between ComfyUI versions. Walking every list
    of file dicts in the record costs nothing and makes a rename upstream a
    non-event, where a hardcoded key would turn "the key moved" into "the job
    produced no .glb".
    """
    out = []
    for node_output in record.get("outputs", {}).values():
        for value in node_output.values():
            if not isinstance(value, list):
                continue
            for item in value:
                if (isinstance(item, dict)
                        and str(item.get("filename", "")).endswith(suffix)):
                    out.append(item)
    return out


def stage_mesh(comfy, args, subject, folder, apose_png):
    """Reconstruct a clothed shell and a rigged body from one A-pose image.

    Two jobs from one source, deliberately: the Hunyuan3D shell has the
    clothing and the silhouette but a fragmented head and no rig (spec §2.3),
    and the SAM3DBody base has a clean 127-bone rig and a real face but no
    clothes (spec §2.4). Neither is the deliverable; Stage 2 is where they
    become one.

    Both files are underscore-prefixed because they are intermediates - the
    named deliverables of §6.1 land beside them.
    """
    # Squared before upload, never the raw A-pose: CLIPVisionEncode centre-crops
    # a 4:5 image and takes the head and the boots with it. Kept on disk beside
    # apose.png rather than made in a temporary, because it is what the
    # reconstruction actually saw and the one thing worth looking at when a
    # shell comes out wrong.
    square_png = folder / "apose_square.png"
    side = square_apose(apose_png, square_png)
    print("    squared -> %s (%dx%d)" % (square_png.name, side, side), flush=True)
    ref = upload_image(comfy, square_png)

    written = []
    for workflow, label, target in (
            (MESH_WORKFLOW, "shell", folder / "_shell.glb"),
            (RIG_WORKFLOW, "base", folder / "_base.glb")):
        if not workflow.exists():
            raise SystemExit("Workflow not found: %s" % workflow)
        print("    %s ..." % label, flush=True)
        template = art.load_api_workflow(workflow)
        prefix = "%s/%s/%s/%s" % (npc_gen.COMFY_PREFIX,
                                  subject.category, subject.slug, label)
        job = build_mesh_job(template, ref, prefix, subject.seed)
        record = comfy.wait(comfy.queue(job), timeout=args.timeout)
        files = mesh_outputs(record)
        if not files:
            raise RuntimeError("the %s job produced no .glb" % label)
        written.append(npc_gen.fetch(comfy, files[0], target))
        print("      -> %s" % target.name)
        # --pause-3d, not --pause. These two jobs are an order of magnitude
        # heavier than a text-to-image render - Hunyuan3D holds a 3072-token
        # latent and a 256^3 octree decode, SAM3DBody a DINOv3 backbone at
        # batch 64 - and ComfyUI reports a job "done" when the last node
        # returns, not when the VRAM it held has actually been freed. Queueing
        # the next reconstruction into that window is what makes a long
        # unattended batch OOM on a machine that runs any single NPC fine.
        time.sleep(args.pause_3d)

    return tuple(written)


# --------------------------------------------------------------------------
# Stage 2: Blender assembly
# --------------------------------------------------------------------------

REPORT_PREFIX = "LANCER3D "


def parse_report(stdout):
    """The assembly's machine-readable line, out of everything Blender printed.

    An absent or unparseable report is an error rather than an empty dict: it
    means the script died somewhere after the argument check, and continuing
    would write a dossier claiming files that are not there.
    """
    lines = [l for l in stdout.splitlines() if l.startswith(REPORT_PREFIX)]
    if not lines:
        raise RuntimeError("the Blender assembly printed no report line")
    try:
        return json.loads(lines[-1][len(REPORT_PREFIX):])
    except ValueError as exc:
        raise RuntimeError("the Blender assembly's report was not JSON: %s" % exc)


def assemble_command(blender, args, folder, stem, base, shell, height=None):
    """The full argv for one headless assembly run.

    Split out from stage_assemble() because getting a flag to the far side of
    Blender's '--' separator is exactly the kind of thing that fails silently
    - an unrecognised flag after '--' is argparse's problem inside the
    script, 600 seconds later.

    --rig is opt-in, not opt-out. Both bind modes were measured against a
    real Lucia Vos reconstruction (see docs/generate-3d.md#rigging):
    `transfer` produced a complete rig with visible tearing at the shoulder
    under a 30-degree bone rotation, and `auto` left every vertex of the
    shell unweighted. Neither is a result a 160-NPC unattended batch should
    be defaulted into, so a rigged GLB is only written when someone asks for
    one with --rig.
    """
    command = [
        str(blender), "--background", "--factory-startup",
        "--python", str(ASSEMBLE_SCRIPT), "--",
        str(base), str(shell), str(folder), "--stem", stem,
        "--voxel", str(args.voxel),
    ]
    if height is not None:
        command += ["--real-height-m", str(height),
                    "--nominal-height-m", str(NOMINAL_HEIGHT_M)]
    if args.rig:
        command += ["--rig", "--bind", args.bind]
    return command


def stage_assemble(args, folder, stem, base, shell, height=None):
    """Run headless Blender over the two GLBs. Returns the assembly's report.

    The whole report rather than just report["files"], because the caller has
    to be able to say more about a run than which files came out of it - and
    because Phase 3 adds keys to it.

    Blender's own stderr is only surfaced when it fails: a successful run
    prints several screens of startup noise that would bury a 160-NPC batch's
    actual progress.

    --voxel is passed through explicitly rather than left to
    assemble_npc.py's own default of 0.0, which would refuse to write an STL
    at all: a real reconstruction is never closed on arrival. It applies to
    the PRINTABLE copy only - the GLB and the turnarounds keep the full
    ~162,000-face detail mesh - and it is in real metres, because
    clean_shell() fits the height before anything measures a distance.

    0.010 was measured against a real catalogue shell (Jules Sokolova), as the
    fraction of the detail mesh's surface area that survives the remesh:

        0.006 -> REFUSED (7%)    0.008 -> 96.1%, 63,624 faces
        0.010 -> 92.7%, 39,488   0.015 -> 85.5%, 16,418

    0.008 is the finest that works and 0.010 is what ships, because the cliff
    below 0.008 is sheer - see npc_mesh.printable_copy() for why a FINER voxel
    leaks where a coarser one does not - and 39,000 faces is already far more
    than a 32 mm mini can resolve. A shell that still fails wants --voxel
    RAISED, not lowered.
    """
    blender = find_blender(args.blender)
    if not ASSEMBLE_SCRIPT.exists():
        raise SystemExit("assembly script not found: %s" % ASSEMBLE_SCRIPT)

    command = assemble_command(blender, args, folder, stem, base, shell, height)
    proc = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout)
    if proc.returncode != 0:
        raise RuntimeError("Blender assembly failed (%d):\n%s"
                           % (proc.returncode, proc.stderr[-2000:]))
    report = parse_report(proc.stdout)
    print("      %d component(s) dropped, %d non-manifold edge(s)"
          % (report.get("components_dropped", 0), report.get("non_manifold", 0)))
    if report.get("shell_height_m"):
        print("      %.2f m tall (SAM3DBody estimated %.2f m), mini %.1f mm"
              % (report["shell_height_m"], report.get("estimated_height_m", 0),
                 report.get("print_height_mm", 0)))
    if report.get("rig_error"):
        print("    ! rigging failed: %s" % report["rig_error"], file=sys.stderr)
    elif report.get("rigged"):
        print("      rigged: %d bones, every vertex weighted" % report["bones"])
    return report


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description=__doc__.split("\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Manifest: %s" % npc_gen.DEFAULT_MANIFEST,
    )

    pick = p.add_argument_group("which NPCs")
    pick.add_argument("--manifest", type=Path, default=npc_gen.DEFAULT_MANIFEST,
                      help="the NPC run log to read (default: %(default)s)")
    pick.add_argument("--id", action="append", default=[], metavar="ID",
                      help="build one entry by its manifest \"id\" (repeatable)")
    pick.add_argument("--filter", metavar="REGEX",
                      help="build only NPCs whose name, callsign or folder path "
                           "matches - the path carries the role category")
    pick.add_argument("--exclude", metavar="REGEX",
                      help="skip NPCs matching the same three")
    pick.add_argument("--limit", type=int, metavar="N", help="stop after N NPCs")
    pick.add_argument("--overwrite", action="store_true",
                      help="rebuild an NPC that already has a 3d/ folder")

    stage = p.add_argument_group("which stages")
    stage.add_argument("--stage", action="append", choices=STAGES, default=None,
                       help="run one stage in isolation while iterating "
                            "(repeatable; default: all of %s)" % ", ".join(STAGES))
    stage.add_argument("--blender", type=Path, default=None,
                       help="the Blender executable (default: %s)" % DEFAULT_BLENDER)
    stage.add_argument("--voxel", type=float, default=0.013,
                       help="voxel remesh size in metres, forcing a closed, "
                            "printable surface on the STL's copy of the shell "
                            "(default: %(default)s). RAISE it if a mesh comes "
                            "back destroyed or non-manifold - lowering it "
                            "makes both worse")
    stage.add_argument("--rig", action="store_true",
                       help="also bind the shell to the base's armature and "
                            "export a rigged GLB; off by default because both "
                            "bind modes were measured against a real "
                            "reconstruction and neither is trustworthy "
                            "unattended - see docs/generate-3d.md#rigging")
    stage.add_argument("--bind", default="transfer", choices=("transfer", "auto"),
                       help="how to weight the shell, when --rig is given: "
                            "'transfer' copies the base's own vertex groups by "
                            "proximity, 'auto' solves for the bones directly "
                            "(default: %(default)s)")

    supplied = p.add_argument_group("an A-pose you supply instead")
    supplied.add_argument("--image", type=Path, default=None, metavar="PATH",
                          help="reconstruct from THIS image rather than rendering "
                               "an A-pose. It is copied to the NPC's 3d/apose.png "
                               "and must already be a cut-out - a figure on "
                               "transparency, 8-bit RGBA, non-interlaced. Implies "
                               "skipping stage apose, and only ever means one NPC")
    supplied.add_argument("--remove-bg", action="store_true",
                          help="the --image still has a background: cut it out "
                               "through --rmbg first, and use that result")
    supplied.add_argument("--out", type=Path, default=None, metavar="DIR",
                          help="reconstruct --image as a thing of its own, with "
                               "no NPC behind it, writing everything into DIR. "
                               "No manifest is read and nothing is tracked, so "
                               "the NPC selection flags cannot be used with it")
    supplied.add_argument("--name", metavar="TEXT",
                          help="what a --out run's deliverables are called "
                               "(default: the --out folder's own name)")
    supplied.add_argument("--height-m", type=float, default=None, metavar="METRES",
                          help="the figure's real height, which the assembly "
                               "scales to. Without it SAM3DBody estimates one, "
                               "and it estimates low - 1.51 m for a 1.75 m "
                               "figure. Overrides an NPC's rolled Height too")

    gen = p.add_argument_group("the A-pose render")
    gen.add_argument("--workflow", type=Path, default=art.DEFAULT_WORKFLOW,
                     help="fallback generation workflow, for an entry that records none")
    gen.add_argument("--workflow-woman", type=Path, metavar="PATH",
                     default=npc_gen.GENDER_WORKFLOWS["woman"],
                     help="same, for NPCs who read as women")
    gen.add_argument("--rmbg", type=Path, default=art.POST_ALIASES["rmbg"],
                     help="background-removal workflow (default: %(default)s)")
    gen.add_argument("--steps", type=int, help="override sampler steps")
    gen.add_argument("--cfg", type=float, help="override CFG")
    gen.add_argument("--sampler", help="override sampler_name")
    gen.add_argument("--scheduler", help="override scheduler")
    gen.add_argument("--set", action="append", default=[], metavar="NODE.input=value",
                     help="patch any workflow input, as in generate-art.py")

    run = p.add_argument_group("run mode")
    run.add_argument("--server", help="ComfyUI address, e.g. 127.0.0.1:8000")
    run.add_argument("--dry-run", action="store_true",
                     help="print the NPCs and their A-pose prompts, queue nothing")
    run.add_argument("--timeout", type=float, default=1800,
                     help="per-job timeout in seconds (default: %(default)s)")
    run.add_argument("--pause", type=float, default=2.0,
                     help="seconds to sleep after each ComfyUI job (default: %(default)s)")
    run.add_argument("--pause-3d", type=float, default=15.0, metavar="SECONDS",
                     help="seconds to sleep after each RECONSTRUCTION job, and "
                          "between NPCs - the 3D jobs are far heavier than a "
                          "render and the host needs time to give the VRAM back "
                          "(default: %(default)s)")

    args = p.parse_args(argv)

    if args.stage is None:
        # --image supplies what stage apose exists to produce, so the default
        # set drops it. Named stages are left exactly as given: `--image X
        # --stage mesh` is a caller deliberately stopping before assembly.
        args.stage = [s for s in STAGES if s != "apose"] if args.image else list(STAGES)
    elif args.image and "apose" in args.stage:
        p.error("--image supplies the A-pose and --stage apose renders one - "
                "pass only one of them")
    if args.image and not args.image.exists():
        p.error("--image not found: %s" % args.image)
    if args.remove_bg and not args.image:
        p.error("--remove-bg has nothing to cut out without --image "
                "(stage apose already cuts out its own render)")

    if args.out and not args.image:
        p.error("--out reconstructs a standalone --image; with no NPC behind "
                "it there are no traits to render an A-pose from")
    if args.out:
        # Refused rather than ignored: a --out run never opens the manifest,
        # so a selection flag here is a caller who thinks they are picking an
        # NPC, and the run they get would not be the one they asked for.
        named = [flag for flag, value in
                 (("--id", args.id), ("--filter", args.filter),
                  ("--exclude", args.exclude), ("--limit", args.limit)) if value]
        if named:
            p.error("--out reads no manifest, so %s cannot select anything"
                    % ", ".join(named))
    elif args.name:
        p.error("--name names a standalone --out run; an NPC's deliverables "
                "are named after the NPC")
    if args.limit is not None and args.limit < 1:
        p.error("--limit must be at least 1")

    try:
        args.set = [art.parse_set(spec) for spec in args.set]
    except ValueError as exc:
        p.error(str(exc))

    # resolve_recorded_workflow() and workflow_for() read this off the args
    # object, so the same shape generate-npc.py builds has to be here too.
    args.gender_workflows = dict(npc_gen.GENDER_WORKFLOWS, woman=args.workflow_woman)
    return args


def preflight(args):
    """A SystemExit naming what is missing, for whatever the selected stages need.

    find_blender(), ASSEMBLE_SCRIPT.exists() and the workflow-file checks
    already live inside stage_assemble()/stage_mesh()/stage_apose() and are
    left there as defence in depth - but those run inside main()'s per-NPC
    try/except, which per-NPC isolation (spec §8) requires to catch
    SystemExit. The result: a mistyped --blender or a missing workflow file
    does not fail once, it fails once PER NPC, each failure only surfacing
    after that NPC has already burned a full A-pose render and two 3D
    reconstructions. Checking here, before the loop even starts, turns that
    into one fast, clear failure instead of N slow, identical ones.
    """
    if ("apose" in args.stage or args.remove_bg) and not args.rmbg.exists():
        raise SystemExit("Background-removal workflow not found: %s" % args.rmbg)
    if "mesh" in args.stage:
        for workflow in (MESH_WORKFLOW, RIG_WORKFLOW):
            if not workflow.exists():
                raise SystemExit("Workflow not found: %s" % workflow)
    if "assemble" in args.stage:
        find_blender(args.blender)
        if not ASSEMBLE_SCRIPT.exists():
            raise SystemExit("assembly script not found: %s" % ASSEMBLE_SCRIPT)


def main(argv=None):
    args = parse_args(argv)

    # (folder, the NPC folder the dossier lives in, the manifest entry). The
    # last two are None for a standalone run, and that is the whole difference
    # between the two modes below this point: no dossier to append to, and no
    # entry to derive a Subject from.
    if args.out:
        jobs = [(args.out, None, None)]
    else:
        if not args.manifest.exists():
            raise SystemExit("Manifest not found: %s" % args.manifest)
        manifest = art.load_manifest(args.manifest)
        picked = select_entries(manifest, args)
        if not picked:
            print("nothing selected")
            return 0
        jobs = [(npc_3d_folder(p), Path(p), e) for p, e in picked]

    if args.dry_run:
        for folder, _, entry in jobs:
            if entry:
                print("\n%s  \"%s\"  -> %s"
                      % (entry["name"], entry.get("callsign", ""), folder))
            else:
                print("\n%s  -> %s" % (standalone_subject(args).name, folder))
            print("  stages: %s" % ", ".join(args.stage))
            if args.image:
                print("  A-pose supplied: %s%s"
                      % (args.image, " (cut out first)" if args.remove_bg else ""))
            else:
                print("  A-pose token prompt:\n%s" % apose_prompt(entry))
        return 0

    check_image(args, [folder for folder, _, _ in jobs])
    preflight(args)

    comfy = art.find_server(args.server)
    print("ComfyUI: %s" % comfy.base)

    done = failed = skipped = warned = 0
    started = time.time()
    queued_any = False
    for folder, folder_path, entry in jobs:
        subject = subject_of(entry, args) if entry else standalone_subject(args)
        if should_skip(folder, args):
            print("skip %s (3d/ exists; --overwrite to rebuild)" % subject.name)
            skipped += 1
            continue

        # Between NPCs, not just between jobs. The last thing the previous NPC
        # did was a headless Blender assembly, which competes with ComfyUI for
        # the same machine; going straight from that into the next A-pose
        # render is the batch's tightest moment. Gated on queued_any so a
        # single-NPC run - the way this is normally driven by hand - pays
        # nothing for it, and skipped NPCs (which touch neither) do not
        # either.
        if queued_any:
            time.sleep(args.pause_3d)
        queued_any = True

        if entry:
            print("\n%s  \"%s\"  -> %s"
                  % (entry["name"], entry.get("callsign", ""), folder))
        else:
            print("\n%s  -> %s" % (subject.name, folder))
        folder.mkdir(parents=True, exist_ok=True)
        try:
            apose = None
            if args.image:
                apose = install_image(comfy, args, subject, folder)
                print("      -> %s (from %s)" % (apose.name, args.image.name))
            elif "apose" in args.stage:
                print("    A-pose render ...", flush=True)
                apose = stage_apose(comfy, args, entry, folder)
                print("      -> %s" % apose.name)
            else:
                apose = folder / "apose.png"
                if not apose.exists():
                    raise RuntimeError(
                        "no apose.png in %s - run --stage apose first" % folder)

            shell = folder / "_shell.glb"
            base = folder / "_base.glb"
            if "mesh" in args.stage:
                shell, base = stage_mesh(comfy, args, subject, folder, apose)
            elif "assemble" in args.stage and not (shell.exists() and base.exists()):
                raise RuntimeError(
                    "no _shell.glb / _base.glb in %s - run --stage mesh first" % folder)

            if "assemble" in args.stage:
                print("    assembling ...", flush=True)
                stem = npc_gen._safe(subject.name)
                if subject.height is None:
                    print("    ! %s - using SAM3DBody's estimate"
                          % ("no --height-m given" if entry is None
                             else "%s names no height" % subject.name),
                          file=sys.stderr)
                report = stage_assemble(args, folder, stem, base, shell,
                                        subject.height)
                built = report["files"]
                for name in built:
                    print("      -> %s" % name)
                if report.get("rig_error"):
                    warned += 1

                # A standalone run tracks nothing by design: there is no NPC
                # whose dossier this belongs in, and inventing one would put a
                # record of an experiment into the campaign's own notes.
                if folder_path is not None:
                    dossier = folder_path / ("%s.md" % stem)
                    if dossier.exists():
                        append_dossier_3d(dossier, built,
                                          [MESH_WORKFLOW, RIG_WORKFLOW], APOSE_STANCE)
                    else:
                        # Not an error: an NPC folder moved by hand into Foundry
                        # keeps its art and loses nothing by having no dossier.
                        print("    ! no dossier at %s - skipping the 3D section"
                              % dossier.name, file=sys.stderr)
        except KeyboardInterrupt:
            print("\ninterrupted - cancelling the running job")
            comfy.cancel_all()
            return 130
        except (Exception, SystemExit) as exc:
            # Per-NPC isolation, spec §8: one bad reconstruction must not take
            # the rest of a 160-NPC batch with it. SystemExit is caught here
            # deliberately, not by oversight - it derives from BaseException,
            # not Exception, so a bare `except Exception` lets it sail past
            # this handler and abort the whole run. stage_apose() (and
            # stage_mesh(), later) raise SystemExit for a missing workflow
            # file or a malformed one; inside this loop that is exactly one
            # NPC's failure, not a reason to stop the batch. Do not narrow
            # this back to `except Exception` - a SystemExit escaping here
            # was proven, by hand, to silently drop every NPC after the
            # first.
            failed += 1
            print("    ! %s" % exc, file=sys.stderr)
            continue
        done += 1

    # The "(N without a rig)" parenthetical only means anything when rigging
    # was actually attempted. warned counts rig attempts that failed, and
    # --rig defaults off - so on a normal, unrigged run warned is always 0,
    # and "0 without a rig" reads as "all of them got rigged" when in fact
    # none did. Print it only when --rig was passed.
    rig_note = " (%d without a rig)" % warned if args.rig else ""
    print("\ndone: %d built%s, %d skipped, %d failed, %.1f min"
          % (done, rig_note, skipped, failed, (time.time() - started) / 60))
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
