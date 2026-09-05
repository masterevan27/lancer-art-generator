"""Regenerate the two fixture GLBs the Blender stage is tested against.

Not run by the test suite - the outputs are committed. Run it by hand when
the assembly's expectations change:

    "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" \\
        --background --factory-startup --python test/fixtures/3d/make_fixtures.py

base.glb  stands in for the SAM3DBody export: a rigged figure at real-world
          scale in metres, with an animation track to be discarded. Three
          bones, not 127 - the assembly does not care how many there are, only
          that they exist and carry weights.
shell.glb stands in for the Hunyuan3D export: unit-scaled, unrigged, wider
          than the body it wraps (a jacket), and carrying one detached speck,
          which is the thing spec §2.3 measured 10,878 of.
rigged.glb stands in for the Rigged.glb `assemble --rig` writes: shell.glb's
          own mesh, bound to a small armature - the relationship the texture
          stage's loop-for-loop atlas transfer depends on.
"""
import math
import sys
from pathlib import Path

import bpy

OUT = Path(__file__).resolve().parent
BODY_HEIGHT_M = 1.73


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def cylinder(name, radius, depth, location=(0, 0, 0), vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.active_object
    obj.name = name
    # Smooth-shaded, so a glTF round trip gives one normal per vertex
    # position instead of splitting every flat-shaded face corner into its
    # own vertex - the raw reconstructions this stands in for are smooth
    # meshes with no hard edges, and keep_largest_component()'s connectivity
    # walk needs shared vertices to see the cylinder as one piece.
    bpy.ops.object.shade_smooth()
    return obj


def make_base():
    reset()
    body = cylinder("body", 0.15, BODY_HEIGHT_M, (0, 0, BODY_HEIGHT_M / 2))

    bpy.ops.object.armature_add(location=(0, 0, 0))
    armature = bpy.context.active_object
    armature.name = "rig"
    bpy.ops.object.mode_set(mode='EDIT')
    bones = armature.data.edit_bones
    root = bones[0]
    root.name = "hips"
    root.head, root.tail = (0, 0, 0), (0, 0, BODY_HEIGHT_M / 3)
    spine = bones.new("spine")
    spine.head, spine.tail = root.tail, (0, 0, 2 * BODY_HEIGHT_M / 3)
    spine.parent = root
    head = bones.new("head")
    head.head, head.tail = spine.tail, (0, 0, BODY_HEIGHT_M)
    head.parent = spine
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')

    # An animation track, so 'discard the predicted pose' has something to
    # discard - the real base always carries one (spec §2.4).
    bpy.ops.object.mode_set(mode='POSE')
    bone = armature.pose.bones["spine"]
    bone.rotation_mode = 'XYZ'
    bone.rotation_euler = (math.radians(55), 0, 0)
    bone.keyframe_insert("rotation_euler", frame=1)
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='SELECT')
    # No UVs to export - a texture coordinate seam is another way a glTF
    # round trip splits a vertex that should stay single, for the same
    # reason smooth shading matters above.
    bpy.ops.export_scene.gltf(filepath=str(OUT / "base.glb"),
                              export_format='GLB', use_selection=True,
                              export_texcoords=False)


def make_shell():
    reset()
    # Unit-scaled, as Hunyuan3D's output is: a whole metre shorter than the
    # base, so the assembly's scale normalisation is genuinely exercised.
    jacket = cylinder("jacket", 0.20, 1.0, (0, 0, 0.5))
    speck = cylinder("speck", 0.01, 0.02, (0.6, 0, 0.5), vertices=6)

    bpy.ops.object.select_all(action='DESELECT')
    jacket.select_set(True)
    speck.select_set(True)
    bpy.context.view_layer.objects.active = jacket
    bpy.ops.object.join()          # one object, two loose parts

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(OUT / "shell.glb"),
                              export_format='GLB', use_selection=True,
                              export_texcoords=False)


def make_rigged():
    """Stands in for the Rigged.glb `assemble --rig` writes.

    The SAME mesh as shell.glb - same cylinders, same order - bound to a
    small armature. That sameness is the point: assemble exports Shell.glb
    and Rigged.glb from one object, so the texture stage transfers the atlas
    UVs loop for loop, and a fixture that merely resembled the shell would
    test the mismatch guard instead of the transfer.
    """
    reset()
    jacket = cylinder("jacket", 0.20, 1.0, (0, 0, 0.5))
    speck = cylinder("speck", 0.01, 0.02, (0.6, 0, 0.5), vertices=6)

    bpy.ops.object.select_all(action='DESELECT')
    jacket.select_set(True)
    speck.select_set(True)
    bpy.context.view_layer.objects.active = jacket
    bpy.ops.object.join()

    bpy.ops.object.armature_add(location=(0, 0, 0))
    armature = bpy.context.active_object
    armature.name = "rig"
    bpy.ops.object.mode_set(mode='EDIT')
    root = armature.data.edit_bones[0]
    root.name = "hips"
    root.head, root.tail = (0, 0, 0), (0, 0, 1.0)
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')
    jacket.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    # ARMATURE_NAME, not ARMATURE_AUTO. Automatic weights run a heat solver
    # that cannot find a solution when the mesh has a disconnected component -
    # and the speck is exactly that. It fails SILENTLY: parent_set returns
    # cleanly having weighted nothing, the glTF export then writes no skins
    # array, and the re-imported "armature" comes back as an EMPTY. Measured:
    # 0 of 44 vertices weighted. Weighting by hand is what this fixture needs
    # anyway - the quality of the bind is irrelevant here, only that there IS
    # one, so the export carries a skin and the mesh stays shell.glb's mesh.
    bpy.ops.object.parent_set(type='ARMATURE_NAME')
    group = (jacket.vertex_groups.get("hips")
             or jacket.vertex_groups.new(name="hips"))
    group.add(range(len(jacket.data.vertices)), 1.0, 'REPLACE')

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(OUT / "rigged.glb"),
                              export_format='GLB', use_selection=True,
                              export_texcoords=False)


if __name__ == "__main__":
    make_base()
    make_shell()
    make_rigged()
    for name in ("base.glb", "shell.glb", "rigged.glb"):
        print("wrote %s (%d bytes)" % (name, (OUT / name).stat().st_size),
              file=sys.stderr)
