"""Texture one assembled NPC's shell from its own reference image.

Invoked headless by generate-3d.py, twice per NPC:

    blender --background --factory-startup --python blender/texture_npc.py -- \\
        <Shell.glb> <outdir> --stem "<Name>" --step back

    blender --background --factory-startup --python blender/texture_npc.py -- \\
        <Shell.glb> <outdir> --stem "<Name>" --step bake \\
        --front <apose_square.png> --front-margin 1.06 [--back <back.png>]

Two launches because a ComfyUI round trip sits between them (spec §4.1), and
`assemble` is deliberately one offline run with no network.

Reports on stdout as a single machine-readable line, the same contract
assemble_npc.py has and for the same two readers:

    LANCER3D {"step": "bake", "files": [...], ...}

Everything it writes is underscore-prefixed. This stage REWRITES an existing
deliverable, unlike rigging, so the caller moves the temporaries into place
only once the whole stage has succeeded - a crash mid-bake must not leave a
corrupt Shell.glb where a good one was (spec §5.3).
"""
import argparse
import json
import os
import sys
import traceback
from pathlib import Path

# Blender does not put a --python script's own directory on sys.path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import npc_mesh  # noqa: E402  (must follow the sys.path line)
import npc_render  # noqa: E402
import npc_texture  # noqa: E402


def parse_argv(argv):
    p = argparse.ArgumentParser(prog="texture_npc.py")
    p.add_argument("shell", type=Path, help="the assembled Shell.glb")
    p.add_argument("outdir", type=Path, help="where the results are written")
    p.add_argument("--stem", required=True, help="the NPC's filename stem")
    p.add_argument("--step", required=True, choices=("back", "bake"),
                   help="'back' renders the shell's 180-degree view for "
                        "ComfyUI to edit; 'bake' projects and bakes")
    p.add_argument("--front", type=Path, default=None,
                   help="the reference image - apose_square.png (step bake)")
    p.add_argument("--front-margin", type=float, default=None,
                   help="the front camera's ortho margin. Passed in rather "
                        "than restated here: it must equal square_apose()'s "
                        "own 1 + APOSE_MARGIN, and one definition of that "
                        "number is the only way it stays true")
    p.add_argument("--back", type=Path, default=None,
                   help="the painted back view (step bake). Without it the "
                        "front is projected alone - spec §3.2's fallback")
    p.add_argument("--rigged", type=Path, default=None,
                   help="also re-export this rigged GLB with the baked "
                        "texture (step bake). It is assembled BEFORE this "
                        "stage runs, so without this it would ship grey")
    p.add_argument("--size", type=int, default=2048,
                   help="atlas size in pixels (default: %(default)s)")
    p.add_argument("--samples", type=int, default=1,
                   help="Cycles samples for the bake (default: %(default)s); "
                        "an EMIT bake has no light transport, so 1 is exact")
    p.add_argument("--render-engine", default="BLENDER_EEVEE",
                   choices=npc_render.ENGINES,
                   help="engine for the back render (default: %(default)s); "
                        "CYCLES needs no GL context and is what tests use")
    p.add_argument("--render-samples", type=int, default=16,
                   help="samples for the back render (default: %(default)s)")
    return p.parse_args(argv)


def script_argv():
    """Everything after Blender's own '--' separator."""
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def load_shell(path):
    npc_mesh.clear_scene()
    shell = npc_mesh.join(npc_mesh.import_glb(path), "shell")
    # Re-weld what the GLB round trip split. assemble's clean_shell() welds at
    # this same distance, but glTF stores attributes per face CORNER, so
    # exporting and re-importing gives every triangle its own three vertices -
    # measured on a real shell, 501,763 verts for 170,613 faces against 85,515
    # distinct positions. Smart UV Project cannot build islands from a mesh
    # with no shared vertices: it produced 167,154 islands (one per triangle)
    # and an atlas that was almost entirely island margin. Welding first takes
    # it to 4,713.
    npc_mesh.weld(shell, distance=0.0005)
    return shell


def step_back(args):
    shell = load_shell(args.shell)
    name = "_back_render.png"
    npc_texture.render_back(shell, args.outdir / name,
                            engine=args.render_engine,
                            samples=args.render_samples)
    return {"files": [name], "render": name,
            "size": npc_texture.BACK_RENDER_PX}


def step_bake(args):
    if args.front is None or args.front_margin is None:
        raise SystemExit("--step bake needs --front and --front-margin")
    for path in (args.front, args.back):
        if path is not None and not path.exists():
            raise SystemExit("not found: %s" % path)

    shell = load_shell(args.shell)
    # Square first: the projection cameras' frames take their aspect from the
    # render resolution, and a non-square one stretches every UV.
    npc_texture.square_render(args.size)

    front = npc_texture.load_view(args.front)
    camera = npc_texture.projection_camera(shell, 0, args.front_margin)
    npc_texture.project_uvs(shell, camera, "proj_front")
    bpy.data.objects.remove(camera, do_unlink=True)

    back = None
    views = ["front"]
    if args.back is not None:
        back = npc_texture.load_view(args.back)
        camera = npc_texture.projection_camera(
            shell, 180, npc_texture.BACK_MARGIN)
        npc_texture.project_uvs(shell, camera, "proj_back")
        bpy.data.objects.remove(camera, do_unlink=True)
        views.append("back")

    islands = npc_texture.atlas_uvs(shell)
    npc_texture.projection_material(shell, front, back)

    texture_name = "_%s Texture.png" % args.stem
    image = npc_texture.bake_atlas(shell, args.size, args.outdir / texture_name,
                                   samples=args.samples)
    npc_texture.finish_material(shell, image)

    shell_name = "_%s Shell.glb" % args.stem
    npc_mesh.export_glb([shell], args.outdir / shell_name)

    rigged_name = None
    if args.rigged is not None and args.rigged.exists():
        # A second import into the same scene, not a re-use of `shell`: the
        # rigged export is a DIFFERENT object - it carries vertex groups and
        # an armature modifier the plain shell does not - and re-deriving it
        # from this one would mean redoing the bind that assemble already did.
        # Its UVs and its material are what change, and finish_material() is
        # exactly that change.
        objects = npc_mesh.import_glb(args.rigged)
        armature = npc_mesh.armature_of(objects)
        meshes = npc_mesh.meshes_of(objects)
        if armature is None or not meshes:
            raise SystemExit(
                "%s has no armature or no mesh - not a Rigged.glb"
                % args.rigged.name)
        rigged = npc_mesh.join(meshes, "rigged_shell")
        # Weld exactly as load_shell() welds the plain shell import, and for
        # the same reason: glTF stores attributes per face CORNER, so a round
        # trip through export/import splits every triangle into its own three
        # vertices. Without re-welding here, a real rigged export and its
        # matching shell come back with DIFFERENT loop counts even though they
        # started as the same mesh (measured on a real NPC: 511,839 loops
        # unwelded against the shell's 511,791 welded) - which would trip the
        # loop guard below on every real run, not just a genuine mismatch.
        npc_mesh.weld(rigged, distance=0.0005)
        # The bind is per vertex, and the rigged mesh is the same vertices in
        # the same order as the shell it was bound from, so the atlas UVs
        # transfer loop for loop. Asserted rather than assumed: a mismatch
        # would silently texture the figure with someone else's unwrap.
        if len(rigged.data.loops) != len(shell.data.loops):
            raise SystemExit(
                "%s has %d loops and the shell has %d - they are not the same "
                "mesh, so the atlas cannot be transferred"
                % (args.rigged.name, len(rigged.data.loops),
                   len(shell.data.loops)))
        atlas = (rigged.data.uv_layers.get("atlas")
                 or rigged.data.uv_layers.new(name="atlas"))
        source = shell.data.uv_layers["atlas"].data
        for index, loop in enumerate(atlas.data):
            loop.uv = source[index].uv
        npc_texture.finish_material(rigged, image)
        rigged_name = "_%s Rigged.glb" % args.stem
        npc_mesh.export_glb([armature, rigged], args.outdir / rigged_name)

    files = [texture_name, shell_name]
    if rigged_name:
        files.append(rigged_name)
    return {
        "files": files,
        "texture": texture_name,
        "shell": shell_name,
        "rigged": rigged_name,
        "size": args.size,
        "islands": islands,
        "views": views,
        "faces": len(shell.data.polygons),
    }


def main():
    args = parse_argv(script_argv())
    if not args.shell.exists():
        raise SystemExit("not found: %s" % args.shell)
    args.outdir.mkdir(parents=True, exist_ok=True)

    report = step_back(args) if args.step == "back" else step_bake(args)
    report["step"] = args.step
    print("LANCER3D " + json.dumps(report))


if __name__ == "__main__":
    # A --python script's own uncaught exception does not make Blender exit
    # non-zero - only SystemExit does. The same backstop assemble_npc.py has,
    # and it matters more here: the caller decides whether to overwrite a good
    # Shell.glb based on this process's return code.
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        sys.exit(1)
