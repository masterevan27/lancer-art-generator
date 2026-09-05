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

    # A key and a dimmer fill, both returned so turnaround() can swing them
    # with the camera. Left fixed in world space - which is what they used to
    # be - they light angle 000 and leave 180 and 270 as black silhouettes on
    # transparent, because the world is near-black by design and a SUN lights
    # one side of a figure only. A turnaround whose back half is unreadable is
    # half a turnaround.
    lights = []
    for name, energy, offset in (("key", 4.0, 35.0), ("fill", 1.2, -110.0)):
        data = bpy.data.lights.new(name, type='SUN')
        data.energy = energy
        light = bpy.data.objects.new(name, data)
        light["offset"] = offset
        bpy.context.collection.objects.link(light)
        lights.append(light)
    aim_lights(lights, 0)
    return scene, lights


def aim_lights(lights, angle_deg):
    """Point every light at the subject from `angle_deg`'s point of view."""
    for light in lights:
        light.rotation_euler = (
            math.radians(55), 0, math.radians(angle_deg + light["offset"]))


def frame_camera(obj, angle_deg, margin=1.25):
    """An orthographic camera looking level at `obj` from `angle_deg` around Z.

    Orthographic rather than perspective: four views meant to be compared
    should not each apply their own foreshortening, and a token-scale render
    gains nothing from a lens.
    """
    bpy.context.view_layer.update()
    size = max(obj.dimensions)
    # The BOUNDING BOX centre, not the object origin. An imported reconstruction
    # carries whatever origin its exporter chose, and it is generally nowhere
    # near the mesh: measured on a real Hunyuan3D shell, the origin sat at
    # (0, 0, 0) while the mesh occupied y -0.500..-0.288, z -0.496..0.496, so
    # `origin + dimensions.z / 2` aimed the camera at the top of the head and
    # 0.39 units off to one side, and the figure rendered cropped and shoved
    # against the edge of the frame. align_to() happens to hide most of this in
    # the full pipeline by recentring the shell on the base; nothing guarantees
    # that, and turnaround() is called on whatever object it is handed.
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    centre = Vector((
        (min(c.x for c in corners) + max(c.x for c in corners)) / 2,
        (min(c.y for c in corners) + max(c.y for c in corners)) / 2,
        (min(c.z for c in corners) + max(c.z for c in corners)) / 2))

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
    _, lights = setup(engine, size, samples)
    written = []
    for angle in angles:
        camera = frame_camera(obj, angle)
        aim_lights(lights, angle)
        name = "%s Turnaround_%03d.png" % (stem, angle)
        bpy.context.scene.render.filepath = str(outdir / name)
        bpy.ops.render.render(write_still=True)
        written.append(name)
        bpy.data.objects.remove(camera, do_unlink=True)
    return written
