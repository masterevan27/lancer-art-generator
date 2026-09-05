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


def _activate(obj):
    """Make `obj` the one selected, active object. Mirrors npc_mesh._activate."""
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def atlas_uvs(obj, name="atlas"):
    """Smart UV Project into a layer of its own. Returns the island count.

    This layer is the DELIVERABLE's UV layer - the one the baked atlas is
    addressed by, and the only one that survives finish_material(). The
    projection layers are working data.

    Made the active layer, because bpy.ops.object.bake writes through
    whichever layer is active, not through whichever the material's image node
    happens to prefer.
    """
    mesh = obj.data
    existing = mesh.uv_layers.get(name)
    if existing:
        mesh.uv_layers.remove(existing)
    layer = mesh.uv_layers.new(name=name)
    mesh.uv_layers.active = layer

    _activate(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.002)
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')

    # Reported rather than asserted on: spec §7.3 records that whether this
    # packs well on a 162k-face open shell is unquantified, and a number in
    # every run's report is how it stops being unquantified.
    #
    # `name`, not `layer.name`: the mode_set(EDIT) / mode_set(OBJECT) round
    # trip above reallocates the mesh's CustomData layer array, and the
    # Python `layer` object still wraps the old array slot. Measured on this
    # Blender: after the round trip, `layer.name` came back as
    # 'custom_normal' - a different layer entirely - and every island lookup
    # silently failed. `name` is the plain string this function was called
    # with; it cannot go stale.
    return _uv_islands(obj, name)


def _uv_islands(obj, layer_name):
    """How many connected pieces `layer_name` cuts the mesh into."""
    import bmesh
    mesh = bmesh.new()
    mesh.from_mesh(obj.data)
    mesh.faces.ensure_lookup_table()
    layer = mesh.loops.layers.uv.get(layer_name)
    if layer is None:
        mesh.free()
        return 0
    seen, islands = set(), 0
    for face in mesh.faces:
        if face.index in seen:
            continue
        islands += 1
        seen.add(face.index)
        stack = [face]
        while stack:
            current = stack.pop()
            for loop in current.loops:
                uv = loop[layer].uv
                for other in loop.edge.link_faces:
                    if other.index in seen:
                        continue
                    # Same island only when the shared edge is not a UV seam:
                    # some loop of `other` sits on this loop's UV corner.
                    if any((l[layer].uv - uv).length < 1e-6
                           for l in other.loops):
                        seen.add(other.index)
                        stack.append(other)
    mesh.free()
    return islands


def load_view(path):
    """One view's image, tagged sRGB - it is colour, not data."""
    image = bpy.data.images.load(str(path))
    image.colorspace_settings.name = 'sRGB'
    return image


def projection_material(obj, front, back=None):
    """A material whose emission is the views, blended by facing angle.

    Emission rather than a Principled BSDF: the bake must return the source
    pixels, not the source pixels lit by something. An EMIT bake has no light
    transport at all, which makes the result independent of the world, the
    lamps and the sample count.

    The blend is spec §4.3 step 3. With the front camera at -Y looking +Y, a
    surface's facing is its world normal's Y component alone: a dead-front
    surface has Ny = -1 and a dead-back surface Ny = +1, so

        t = 0.5 + 0.5 * Ny

    runs 0 at dead-front to 1 at dead-back. Smoothstepped, that is the mix.
    Deliberately not max(0, +-Ny), whose weights BOTH reach zero at the
    silhouette - which is exactly where a naive blend tears.

    Each side's weight is then multiplied by its own sampled alpha (§4.3 step
    4), so where the mesh's silhouette overshoots the image's, the texel falls
    to the other view instead of sampling backdrop. The alpha term is remapped
    to 0.001..1.0 rather than 0..1, so a texel outside BOTH images still
    resolves to its geometric mix instead of dividing by zero and going black.

    With no back view, t is unused and the front is emitted directly: spec
    §3.2's fallback is this function with one view, not a second code path.
    """
    material = bpy.data.materials.new("projection")
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    output = tree.nodes.new("ShaderNodeOutputMaterial")
    emission = tree.nodes.new("ShaderNodeEmission")
    tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])

    def view(image, uv_layer):
        uv = tree.nodes.new("ShaderNodeUVMap")
        uv.uv_map = uv_layer
        texture = tree.nodes.new("ShaderNodeTexImage")
        texture.image = image
        texture.extension = 'EXTEND'
        texture.interpolation = 'Linear'
        tree.links.new(uv.outputs["UV"], texture.inputs["Vector"])
        return texture

    front_texture = view(front, "proj_front")
    obj.data.materials.clear()
    obj.data.materials.append(material)
    if back is None:
        tree.links.new(front_texture.outputs["Color"], emission.inputs["Color"])
        return material

    back_texture = view(back, "proj_back")

    def maths(operation, a=None, b=None, value_a=None, value_b=None,
              value_c=None):
        node = tree.nodes.new("ShaderNodeMath")
        node.operation = operation
        for index, value in ((0, value_a), (1, value_b), (2, value_c)):
            if value is not None:
                node.inputs[index].default_value = value
        for index, socket in ((0, a), (1, b)):
            if socket is not None:
                tree.links.new(socket, node.inputs[index])
        return node

    geometry = tree.nodes.new("ShaderNodeNewGeometry")
    split = tree.nodes.new("ShaderNodeSeparateXYZ")
    tree.links.new(geometry.outputs["Normal"], split.inputs["Vector"])

    # t = smoothstep(0, 1, 0.5 + 0.5 * Ny)
    half = maths('MULTIPLY_ADD', a=split.outputs["Y"],
                 value_b=0.5, value_c=0.5)
    # ShaderNodeMath has no SMOOTHSTEP operation - verified against this
    # Blender (5.2.1 LTS, the same binary the suite launches): its operation
    # enum has SMOOTH_MIN/SMOOTH_MAX but no true smoothstep, and assigning
    # 'SMOOTHSTEP' raises TypeError. ShaderNodeMapRange's interpolation_type
    # carries it instead. Its inputs are read by index, not by name (a Map
    # Range node carries both float and vector sockets under the same
    # display names, so inputs["From Min"] is ambiguous), and its output
    # socket is "Result", not "Value" - every downstream read of `t` follows
    # that. Do not "simplify" this back to a Math node.
    t = tree.nodes.new("ShaderNodeMapRange")
    t.interpolation_type = 'SMOOTHSTEP'
    t.inputs[1].default_value = 0.0  # From Min
    t.inputs[2].default_value = 1.0  # From Max
    t.inputs[3].default_value = 0.0  # To Min
    t.inputs[4].default_value = 1.0  # To Max
    tree.links.new(half.outputs["Value"], t.inputs[0])  # Value
    one_minus_t = maths('SUBTRACT', value_a=1.0, b=t.outputs["Result"])

    def weight(geometric, alpha):
        floored = maths('MULTIPLY_ADD', a=alpha, value_b=0.999, value_c=0.001)
        return maths('MULTIPLY', a=geometric, b=floored.outputs["Value"])

    front_weight = weight(one_minus_t.outputs["Value"],
                          front_texture.outputs["Alpha"])
    back_weight = weight(t.outputs["Result"], back_texture.outputs["Alpha"])
    total = maths('ADD', a=front_weight.outputs["Value"],
                  b=back_weight.outputs["Value"])

    def scaled(texture, weight_node):
        share = maths('DIVIDE', a=weight_node.outputs["Value"],
                      b=total.outputs["Value"])
        node = tree.nodes.new("ShaderNodeVectorMath")
        node.operation = 'SCALE'
        tree.links.new(texture.outputs["Color"], node.inputs[0])
        tree.links.new(share.outputs["Value"], node.inputs["Scale"])
        return node

    added = tree.nodes.new("ShaderNodeVectorMath")
    added.operation = 'ADD'
    tree.links.new(scaled(front_texture, front_weight).outputs["Vector"],
                   added.inputs[0])
    tree.links.new(scaled(back_texture, back_weight).outputs["Vector"],
                   added.inputs[1])
    tree.links.new(added.outputs["Vector"], emission.inputs["Color"])
    return material


def bake_atlas(obj, size, path, samples=1, margin_px=8):
    """Bake the projection material's emission to a PNG. Returns the image.

    CYCLES because bpy.ops.object.bake does not exist for EEVEE, and CPU
    because a headless run cannot assume a GL context - the same trade
    npc_render's engine parameter documents.

    view_transform 'Standard' is load-bearing. Blender's default is a tone
    map, and save_render() applies it: without this, a bake of a flat #DC1E1E
    comes back visibly washed out and nothing in the pipeline would say why.
    """
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.render.bake.margin = margin_px
    scene.render.bake.use_clear = True
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '8'

    image = bpy.data.images.new("atlas", size, size, alpha=True)
    tree = obj.data.materials[0].node_tree
    target = tree.nodes.new("ShaderNodeTexImage")
    target.image = image
    # The bake writes into whichever image node is ACTIVE and reads through
    # whichever UV layer is active. Both are set explicitly; neither defaults
    # to what this needs.
    for node in tree.nodes:
        node.select = False
    target.select = True
    tree.nodes.active = target

    _activate(obj)
    bpy.ops.object.bake(type='EMIT', use_clear=True, margin=margin_px)

    image.save_render(filepath=str(path), scene=scene)
    return image


def finish_material(obj, image, keep="atlas"):
    """Replace the projection rig with a plain textured Principled.

    The deliverable must not carry the rig: three UV layers and a node graph
    referencing two source PNGs that live in the NPC's 3d/ folder would export
    as a GLB with dangling image references and ambiguous texture coordinates.
    What ships is one UV layer, one material, one image.
    """
    mesh = obj.data
    for layer in [l for l in mesh.uv_layers if l.name != keep]:
        mesh.uv_layers.remove(layer)
    mesh.uv_layers.active = mesh.uv_layers[keep]

    material = bpy.data.materials.new("textured")
    material.use_nodes = True
    tree = material.node_tree
    principled = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    texture = tree.nodes.new("ShaderNodeTexImage")
    texture.image = image
    tree.links.new(texture.outputs["Color"], principled.inputs["Base Color"])
    mesh.materials.clear()
    mesh.materials.append(material)


def render_back(obj, path, size=BACK_RENDER_PX, engine='BLENDER_EEVEE',
                samples=16):
    """Render `obj`'s 180-degree view - the image ComfyUI edits into a back.

    Rendered at BACK_MARGIN, which the bake step also samples at, so the
    generated back view is registered to the mesh by construction (spec §2.2)
    and the projection that reads it back needs no calibration.

    Lit through npc_render's own key and fill rather than flat: the edit model
    is given the shell's form to paint onto, and a silhouette carries none.
    """
    _, lights = npc_render.setup(engine, size, samples)
    npc_render.aim_lights(lights, 180)
    camera = projection_camera(obj, 180, BACK_MARGIN)
    try:
        bpy.context.scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
    finally:
        bpy.data.objects.remove(camera, do_unlink=True)
