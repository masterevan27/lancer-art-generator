"""DISPOSABLE. Spec §8.1: does bounds-matching actually register?

Samples apose_square.png per VERTEX through the projection camera and writes
it to a colour attribute, then renders a turnaround of the result. No unwrap,
no bake, no ComfyUI - the only question is whether the reference's pixels land
on the right parts of the mesh.

    "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" \\
        --background --factory-startup --python blender/probe_projection.py -- \\
        "<3d/Jules Sokolova Shell.glb>" "<3d/apose_square.png>" "<outdir>"

Delete this file once §4.3 replaces it. It is committed only so the answer is
reproducible by whoever doubts it later.
"""
import os
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import npc_mesh   # noqa: E402
import npc_render  # noqa: E402

# 1 + generate-3d.py's APOSE_MARGIN (0.06). Hardcoded here because this file is
# disposable and takes no argument it does not need; the shipping code derives
# it instead (Task 4).
FRONT_MARGIN = 1.06


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    shell_path, image_path, outdir = Path(argv[0]), Path(argv[1]), Path(argv[2])
    outdir.mkdir(parents=True, exist_ok=True)

    npc_mesh.clear_scene()
    shell = npc_mesh.join(npc_mesh.import_glb(shell_path), "shell")

    # The camera's frame is square only if the render is: view_frame(), which
    # world_to_camera_view calls, reads the scene's aspect. This must come
    # first or every UV is stretched along one axis.
    scene = bpy.context.scene
    scene.render.resolution_x = scene.render.resolution_y = 1024

    image = bpy.data.images.load(str(image_path))
    width, height = image.size
    pixels = list(image.pixels)   # RGBA floats, bottom row first

    camera = npc_render.frame_camera(shell, 0, FRONT_MARGIN)
    # frame_camera sets the camera's rotation and location, but Blender does
    # not re-evaluate matrix_world until the depsgraph updates - and
    # world_to_camera_view reads matrix_world. Without this the projection
    # runs through an identity camera matrix and samples the reference by the
    # mesh's width and DEPTH instead of its height.
    bpy.context.view_layer.update()
    mesh = shell.data
    colours = mesh.color_attributes.new("probe", 'FLOAT_COLOR', 'POINT')
    for i, vertex in enumerate(mesh.vertices):
        uv = world_to_camera_view(scene, camera, shell.matrix_world @ vertex.co)
        x = min(max(int(uv.x * width), 0), width - 1)
        y = min(max(int(uv.y * height), 0), height - 1)
        base = (y * width + x) * 4
        colours.data[i].color = pixels[base:base + 4]
    bpy.data.objects.remove(camera, do_unlink=True)

    material = bpy.data.materials.new("probe")
    material.use_nodes = True
    tree = material.node_tree
    attribute = tree.nodes.new("ShaderNodeVertexColor")
    attribute.layer_name = "probe"
    emission = tree.nodes.new("ShaderNodeEmission")
    tree.links.new(attribute.outputs["Color"], emission.inputs["Color"])
    output = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL')
    tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    shell.data.materials.clear()
    shell.data.materials.append(material)

    npc_render.turnaround(shell, outdir, "Probe", angles=(0, 180),
                          size=1024, engine='CYCLES', samples=1)
    print("LANCER3D probe wrote %s" % outdir)


if __name__ == "__main__":
    main()
