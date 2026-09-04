"""Assemble one NPC's two reconstructions into the deliverables.

Invoked headless by generate-3d.py:

    blender --background --factory-startup --python blender/assemble_npc.py -- \\
        <base.glb> <shell.glb> <outdir> --stem "<Name>"

Reports on stdout as a single machine-readable line:

    LANCER3D {"files": [...], "non_manifold": 0, ...}

A line rather than prose, because two callers read it - generate-3d.py, which
turns it into a dossier section, and the test suite, which asserts on it - and
neither should be parsing English. Blender writes a great deal else to stdout;
the prefix is what makes the report findable in it.
"""
import argparse
import json
import os
import sys
import traceback
from pathlib import Path

# Blender does not put a --python script's own directory on sys.path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import npc_mesh  # noqa: E402  (must follow the sys.path line)
import npc_render  # noqa: E402


def parse_argv(argv):
    p = argparse.ArgumentParser(prog="assemble_npc.py")
    p.add_argument("base", type=Path, help="the SAM3DBody rigged body GLB")
    p.add_argument("shell", type=Path, help="the Hunyuan3D clothed shell GLB")
    p.add_argument("outdir", type=Path, help="where the deliverables are written")
    p.add_argument("--stem", required=True, help="the NPC's filename stem")
    p.add_argument("--print-height-mm", type=float, default=32.0,
                   help="mini height in millimetres (default: %(default)s)")
    p.add_argument("--weld", type=float, default=0.0005,
                   help="weld distance in metres (default: %(default)s)")
    p.add_argument("--voxel", type=float, default=0.0,
                   help="voxel remesh size in metres; 0 disables (default: %(default)s)")
    p.add_argument("--no-render", action="store_true",
                   help="skip the turnarounds, for iterating on the mesh work")
    p.add_argument("--turnaround-size", type=int, default=768,
                   help="turnaround render size in pixels (default: %(default)s)")
    p.add_argument("--engine", default="BLENDER_EEVEE", choices=npc_render.ENGINES,
                   help="render engine (default: %(default)s); CYCLES needs no "
                        "GL context and is what the tests use")
    p.add_argument("--samples", type=int, default=16,
                   help="render samples (default: %(default)s)")
    return p.parse_args(argv)


def script_argv():
    """Everything after Blender's own '--' separator."""
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def main():
    args = parse_argv(script_argv())
    for path in (args.base, args.shell):
        if not path.exists():
            raise SystemExit("not found: %s" % path)
    args.outdir.mkdir(parents=True, exist_ok=True)

    npc_mesh.clear_scene()

    # The base first: it is the only thing that knows what real-world scale is.
    base_objects = npc_mesh.import_glb(args.base, guess_bind_pose=False)
    armature = npc_mesh.armature_of(base_objects)
    if armature is None:
        raise SystemExit("%s has no armature - not a SAM3DBody body_mesh export"
                         % args.base.name)
    npc_mesh.rest_pose(armature)
    body = npc_mesh.join(base_objects, "base_body")
    body_height = npc_mesh.height_of(body)
    if body_height <= 0:
        raise SystemExit("the base has no height")

    # The base is never transformed - it defines the frame, and moving its mesh
    # out from under its armature is the one way to break a rig invisibly. The
    # shell is what gets scaled and moved.
    shell_objects = npc_mesh.import_glb(args.shell)
    shell = npc_mesh.join(shell_objects, "shell")
    dropped = npc_mesh.clean_shell(shell, args.weld, args.voxel)
    npc_mesh.fit_to_height(shell, body_height)
    npc_mesh.align_to(shell, body)

    non_manifold = npc_mesh.non_manifold_edges(shell)
    if non_manifold:
        # Spec §6 step 7. A slicer given a leaking mesh produces a mini with
        # holes in it, hours later, with no warning - so this fails here.
        raise SystemExit(
            "the cleaned shell has %d non-manifold edges; it would not print. "
            "Raise --voxel to force a closed remesh." % non_manifold)

    files = []
    shell_glb = args.outdir / ("%s Shell.glb" % args.stem)
    npc_mesh.export_glb([shell], shell_glb)
    files.append(shell_glb.name)

    print_stl = args.outdir / ("%s Print.stl" % args.stem)
    npc_mesh.export_stl(shell, print_stl, args.print_height_mm)
    files.append(print_stl.name)

    if not args.no_render:
        files += npc_render.turnaround(
            shell, args.outdir, args.stem, size=args.turnaround_size,
            engine=args.engine, samples=args.samples)

    print("LANCER3D " + json.dumps({
        "files": files,
        "shell_height_m": round(npc_mesh.height_of(shell), 4),
        "components_dropped": dropped,
        "non_manifold": non_manifold,
        "rigged": False,
    }))


if __name__ == "__main__":
    # A --python script's own uncaught exception does not make this Blender
    # build exit non-zero - only SystemExit does. The explicit SystemExit
    # checks above (missing input, missing armature, non-manifold shell)
    # already propagate correctly and are left alone; this is the backstop
    # for whatever main() didn't anticipate - an npc_mesh RuntimeError, a
    # malformed input GLB the importer itself rejects, anything - so that a
    # failure this script never saw coming still exits non-zero instead of
    # looking exactly like success to a caller checking the return code
    # (spec §6 step 7).
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        sys.exit(1)
