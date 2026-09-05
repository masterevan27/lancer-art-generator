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


def apose_prompt(entry):
    """The token prompt Stage 0 renders. The portrait half is discarded."""
    return npc_gen.build_prompts(apose_npc(entry))[1]


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


def stage_apose(comfy, args, entry, folder):
    """Render this NPC's token again in the A-pose, cut out. -> <folder>/apose.png

    Renders through the entry's OWN recorded workflow and its own seed, so the
    figure is the same person the token shows - only the pose and the empty
    hands differ. The portrait half of build_prompts() is discarded; nothing
    downstream has a use for a backdrop.
    """
    npc = apose_npc(entry)
    prompt = npc_gen.build_prompts(npc)[1]
    category = npc_gen.role_category(npc)
    slug = art._slug(npc["name"])
    seed = entry["seed"]
    knobs = npc_gen.Knobs(args, npc_gen.TOKEN_SIZE, npc_gen.COMFY_PREFIX)

    workflow_path = npc_gen.resolve_recorded_workflow(entry, npc, args)
    template = art.load_api_workflow(workflow_path)
    try:
        slots = art.locate_slots(template)
    except art.WorkflowError as exc:
        raise SystemExit("%s: %s" % (workflow_path.name, exc))

    job = art.build_job(template, slots,
                        npc_gen.entry_for(category, slug, "apose", prompt), seed, knobs)
    images = art.Comfy.images(comfy.wait(comfy.queue(job), timeout=args.timeout))
    if not images:
        raise RuntimeError("the A-pose render produced no image")
    time.sleep(args.pause)

    if not args.rmbg.exists():
        raise SystemExit("Background-removal workflow not found: %s" % args.rmbg)
    post = art.load_api_workflow(args.rmbg)
    try:
        post_slots = art.locate_post_slots(post)
    except art.WorkflowError as exc:
        raise SystemExit("%s: %s" % (args.rmbg.name, exc))

    prefix = "%s/%s/%s/apose_rmbg" % (npc_gen.COMFY_PREFIX, category, slug)
    cut_job = art.build_post_job(
        post, post_slots, art.image_ref(images[0]), prefix, seed, knobs)
    cut = art.Comfy.images(comfy.wait(comfy.queue(cut_job), timeout=args.timeout))
    if not cut:
        raise RuntimeError("background removal produced no image")
    time.sleep(args.pause)

    return npc_gen.fetch(comfy, cut[0], folder / "apose.png")


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


def stage_mesh(comfy, args, entry, folder, apose_png):
    """Reconstruct a clothed shell and a rigged body from one A-pose image.

    Two jobs from one source, deliberately: the Hunyuan3D shell has the
    clothing and the silhouette but a fragmented head and no rig (spec §2.3),
    and the SAM3DBody base has a clean 127-bone rig and a real face but no
    clothes (spec §2.4). Neither is the deliverable; Stage 2 is where they
    become one.

    Both files are underscore-prefixed because they are intermediates - the
    named deliverables of §6.1 land beside them.
    """
    npc = apose_npc(entry)
    category = npc_gen.role_category(npc)
    slug = art._slug(npc["name"])
    ref = upload_image(comfy, apose_png)

    written = []
    for workflow, label, target in (
            (MESH_WORKFLOW, "shell", folder / "_shell.glb"),
            (RIG_WORKFLOW, "base", folder / "_base.glb")):
        if not workflow.exists():
            raise SystemExit("Workflow not found: %s" % workflow)
        print("    %s ..." % label, flush=True)
        template = art.load_api_workflow(workflow)
        prefix = "%s/%s/%s/%s" % (npc_gen.COMFY_PREFIX, category, slug, label)
        job = build_mesh_job(template, ref, prefix, entry["seed"])
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


def assemble_command(blender, args, folder, stem, base, shell):
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
    if args.rig:
        command += ["--rig", "--bind", args.bind]
    return command


def stage_assemble(args, folder, stem, base, shell):
    """Run headless Blender over the two GLBs. Returns the assembly's report.

    The whole report rather than just report["files"], because the caller has
    to be able to say more about a run than which files came out of it - and
    because Phase 3 adds keys to it.

    Blender's own stderr is only surfaced when it fails: a successful run
    prints several screens of startup noise that would bury a 160-NPC batch's
    actual progress.

    --voxel is passed through explicitly rather than left to
    assemble_npc.py's own default of 0.0. Run by hand against real Stage 0/1
    output for a catalogue NPC: at 0.0 the cleaned shell had 3 non-manifold
    edges and the stage correctly refused to write an unprintable STL; at
    0.004 it produced a manifold result with 0 components dropped in a few
    seconds. assemble_npc.py's own default is left alone deliberately - it is
    a general-purpose tool with its own reviewed tests - and generate-3d.py
    supplies the value that actually works for real reconstruction output.
    """
    blender = find_blender(args.blender)
    if not ASSEMBLE_SCRIPT.exists():
        raise SystemExit("assembly script not found: %s" % ASSEMBLE_SCRIPT)

    command = assemble_command(blender, args, folder, stem, base, shell)
    proc = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout)
    if proc.returncode != 0:
        raise RuntimeError("Blender assembly failed (%d):\n%s"
                           % (proc.returncode, proc.stderr[-2000:]))
    report = parse_report(proc.stdout)
    print("      %d component(s) dropped, %d non-manifold edge(s)"
          % (report.get("components_dropped", 0), report.get("non_manifold", 0)))
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
    stage.add_argument("--voxel", type=float, default=0.004,
                       help="voxel remesh size in metres, forcing a closed, "
                            "printable surface on the cleaned shell (default: "
                            "%(default)s - raise it further if a mesh still "
                            "reports non-manifold edges)")
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
        args.stage = list(STAGES)
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
    if "apose" in args.stage and not args.rmbg.exists():
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

    if not args.manifest.exists():
        raise SystemExit("Manifest not found: %s" % args.manifest)
    manifest = art.load_manifest(args.manifest)
    picked = select_entries(manifest, args)
    if not picked:
        print("nothing selected")
        return 0

    if args.dry_run:
        for folder_path, entry in picked:
            print("\n%s  \"%s\"  -> %s"
                  % (entry["name"], entry.get("callsign", ""),
                     npc_3d_folder(folder_path)))
            print("  stages: %s" % ", ".join(args.stage))
            print("  A-pose token prompt:\n%s" % apose_prompt(entry))
        return 0

    preflight(args)

    comfy = art.find_server(args.server)
    print("ComfyUI: %s" % comfy.base)

    done = failed = skipped = warned = 0
    started = time.time()
    queued_any = False
    for folder_path, entry in picked:
        folder = npc_3d_folder(folder_path)
        if should_skip(folder, args):
            print("skip %s (3d/ exists; --overwrite to rebuild)" % entry["name"])
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

        print("\n%s  \"%s\"  -> %s" % (entry["name"], entry.get("callsign", ""), folder))
        folder.mkdir(parents=True, exist_ok=True)
        try:
            apose = None
            if "apose" in args.stage:
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
                shell, base = stage_mesh(comfy, args, entry, folder, apose)
            elif "assemble" in args.stage and not (shell.exists() and base.exists()):
                raise RuntimeError(
                    "no _shell.glb / _base.glb in %s - run --stage mesh first" % folder)

            if "assemble" in args.stage:
                print("    assembling ...", flush=True)
                stem = npc_gen._safe(entry["name"])
                report = stage_assemble(args, folder, stem, base, shell)
                built = report["files"]
                for name in built:
                    print("      -> %s" % name)
                if report.get("rig_error"):
                    warned += 1

                dossier = Path(folder_path) / ("%s.md" % stem)
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
