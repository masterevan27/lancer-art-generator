"""Orbit renders of one assembled NPC, for the Foundry VTT side of the goal.

Four views of the same person from four angles is what a token cannot give
you, and it is the cheapest useful thing to do with a mesh once it exists.

The engine is a parameter, not a constant. EEVEE is what a real run wants -
it is an order of magnitude faster and the GPU is there - but it needs a GL
context, which a test should not have to assume. Cycles on the CPU at one
sample always works headless, and for a 64-pixel smoke test that is the right
trade.

Blender 5.2's engine enum is BLENDER_EEVEE. It is NOT BLENDER_EEVEE_NEXT,
which is the 4.x spelling and will raise on assignment here.
"""
import math

import bpy
from mathutils import Vector

ENGINES = ("BLENDER_EEVEE", "CYCLES")


def setup(engine, size, samples):
    scene = bpy.context.scene
    if engine not in ENGINES:
        raise ValueError("unknown engine %r - expected one of %s" % (engine, ENGINES))
    scene.render.engine = engine
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = True
    if engine == 'CYCLES':
        scene.cycles.samples = samples
    else:
        scene.eevee.taa_render_samples = samples

    world = bpy.data.worlds.new("turnaround")
    world.use_nodes = False
    world.color = (0.05, 0.05, 0.06)
    scene.world = world

    light_data = bpy.data.lights.new("key", type='SUN')
    light_data.energy = 4.0
    light = bpy.data.objects.new("key", light_data)
    light.rotation_euler = (math.radians(55), 0, math.radians(35))
    bpy.context.collection.objects.link(light)
    return scene


def frame_camera(obj, angle_deg, margin=1.25):
    """An orthographic camera looking level at `obj` from `angle_deg` around Z.

    Orthographic rather than perspective: four views meant to be compared
    should not each apply their own foreshortening, and a token-scale render
    gains nothing from a lens.
    """
    bpy.context.view_layer.update()
    size = max(obj.dimensions)
    centre = obj.matrix_world.translation + Vector((0, 0, obj.dimensions.z / 2))

    data = bpy.data.cameras.new("turnaround")
    data.type = 'ORTHO'
    data.ortho_scale = size * margin
    camera = bpy.data.objects.new("turnaround", data)
    bpy.context.collection.objects.link(camera)

    radians = math.radians(angle_deg)
    distance = size * 3
    camera.location = centre + Vector(
        (math.sin(radians) * distance, -math.cos(radians) * distance, 0))
    # Level with the middle of the figure, turned to face it: X 90 degrees
    # stands the camera up out of its default top-down rest orientation, Z
    # swings it around the subject.
    camera.rotation_euler = (math.radians(90), 0, radians)
    bpy.context.scene.camera = camera
    return camera


def turnaround(obj, outdir, stem, angles=(0, 90, 180, 270), size=768,
               engine='BLENDER_EEVEE', samples=16):
    """Render `obj` from each angle. Returns the filenames written."""
    setup(engine, size, samples)
    written = []
    for angle in angles:
        camera = frame_camera(obj, angle)
        name = "%s Turnaround_%03d.png" % (stem, angle)
        bpy.context.scene.render.filepath = str(outdir / name)
        bpy.ops.render.render(write_still=True)
        written.append(name)
        bpy.data.objects.remove(camera, do_unlink=True)
    return written
