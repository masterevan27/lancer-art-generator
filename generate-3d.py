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
import os
import re
import sys
import time
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
    """
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

    raise SystemExit("stages are not wired up yet - see Task 4")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
