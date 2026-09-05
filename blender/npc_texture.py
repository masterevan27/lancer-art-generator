"""Projecting a reference image onto a reconstruction, and baking the result.

The shell sits in final world space at Hunyuan3D's own orientation - nothing
between reconstruction and export rotates it (spec §2.3) - so the camera that
looks at the front of the mesh is the same camera the reference image was
framed by, and the reference's pixels can be projected straight back on.

Per-view UVs are computed here in Python rather than with
bpy.ops.uv.project_from_view. That operator needs a VIEW_3D area and its poll
fails under --background, which is the only way this module is ever run.
world_to_camera_view() does the same arithmetic, handles orthographic cameras
explicitly, and works headless.
"""
import bpy
from bpy_extras.object_utils import world_to_camera_view

import npc_render

# The back view's framing. Free, unlike the front's - step 'back' renders the
# image at this camera and step 'bake' samples it at the same one, so any
# value works as long as the two agree. Both read this constant, so they
# cannot disagree; npc_render.frame_camera's own default is where the number
# came from.
BACK_MARGIN = 1.25

# The back render's size in pixels. Square, because a projection camera's
# frame is square only when the render is - see square_render().
BACK_RENDER_PX = 1024


def square_render(size):
    """Make the scene's render square at `size`. Returns the scene.

    Load-bearing, not tidiness. Camera.view_frame(), which world_to_camera_view
    calls, derives the frame's aspect from the scene's render resolution. A
    non-square render gives a non-square frame and stretches every projected UV
    along one axis - silently, and only visibly once the texture is on the
    model.
    """
    scene = bpy.context.scene
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    return scene


def projection_camera(obj, angle_deg, margin):
    """The camera a view is both rendered at and sampled through.

    npc_render.frame_camera unchanged - it already takes the margin as a
    parameter, and spec §4.2's whole point is that the projection camera is
    not new code. Wrapped only so callers name what they are doing.
    """
    return npc_render.frame_camera(obj, angle_deg, margin)


def project_uvs(obj, camera, name):
    """Write one UV layer holding `obj`'s screen position in `camera`.

    Per LOOP, because a UV layer is indexed by loop - but computed per vertex
    and shared, since the projection depends only on the vertex position and
    world_to_camera_view is the expensive part of this loop. A dense shell has
    roughly six loops per vertex.

    Returns the layer's name.
    """
    scene = bpy.context.scene
    bpy.context.view_layer.update()
    mesh = obj.data
    layer = mesh.uv_layers.get(name) or mesh.uv_layers.new(name=name)

    matrix = obj.matrix_world
    projected = [None] * len(mesh.vertices)
    for index, vertex in enumerate(mesh.vertices):
        position = world_to_camera_view(scene, camera, matrix @ vertex.co)
        projected[index] = (position.x, position.y)

    data = layer.data
    for loop in mesh.loops:
        data[loop.index].uv = projected[loop.vertex_index]
    return layer.name
