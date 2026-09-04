"""Mesh work for the NPC assembly: import, align, clean, export.

Runs inside Blender's own Python. bpy and bmesh are available; nothing else
is, and nothing else may be - spec §2.2 rules out any dependency that needs a
compiler, and Blender's interpreter has no site-packages of ours anyway.

Every operator name here is the Blender 5.2 spelling. Two are easy to get
wrong from memory: the STL exporter is `wm.stl_export` (the 4.2+ operator,
not `export_mesh.stl`), and the render engine enum is `BLENDER_EEVEE`, not
`BLENDER_EEVEE_NEXT`.
"""
import bmesh
import bpy
from mathutils import Vector


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_glb(path, guess_bind_pose=True):
    """Import one GLB and return only the objects it added.

    guess_bind_pose=False for the SAM3DBody base. The importer's default is to
    reconstruct a bind pose from the animation's first frame, and that frame is
    exactly the crouched, spike-fingered prediction spec §2.4 measured - so
    guessing from it would bake the bad pose into the rest position, where
    pose_position='REST' could no longer discard it.
    """
    before = set(bpy.data.objects)
    # disable_bone_shape=True is LOAD-BEARING, not defensive hygiene - an
    # earlier note claiming this was byte-identical to remove was tested only
    # against a fixture with no custom bone shapes and does not hold on real
    # input. Without it, the importer's hidden per-armature bone-shape
    # Icosphere gets swept into base_body by join() and height_of() measures
    # ITS 2.0 m instead of the real body's 1.571 m, mis-scaling the shell -
    # measured on a real reconstruction, this took shell_height_m from 1.571
    # to 2.0 and made weight transfer fail totally (292,296 of 292,296 shell
    # vertices unweighted). Do not remove this flag.
    bpy.ops.import_scene.gltf(filepath=str(path), guess_original_bind_pose=guess_bind_pose,
                              disable_bone_shape=True)
    added = [o for o in bpy.data.objects if o not in before]
    if not added:
        raise RuntimeError("%s imported nothing" % path)
    return added


def armature_of(objects):
    return next((o for o in objects if o.type == 'ARMATURE'), None)


def meshes_of(objects):
    return [o for o in objects if o.type == 'MESH']


def rest_pose(armature):
    """Discard the predicted pose, leaving the A-pose bind position.

    Spec §2.4: the prediction fails on this house style and was never the
    valuable part - a rigged character wants a neutral bind pose, which is
    what the rest position already is.
    """
    armature.data.pose_position = 'REST'
    for obj in [armature] + list(armature.children):
        if obj.animation_data:
            obj.animation_data_clear()
    bpy.context.view_layer.update()


def _activate(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def join(objects, name):
    """Join every mesh in `objects` into one object called `name`."""
    meshes = meshes_of(objects)
    if not meshes:
        raise RuntimeError("nothing to join - no mesh among %d objects" % len(objects))
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active
    joined.name = name
    return joined


def apply_transforms(obj):
    _activate(obj)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def height_of(obj):
    """The object's Z extent. glTF is Y-up; the importer converts to Z-up."""
    bpy.context.view_layer.update()
    return obj.dimensions.z


def fit_to_height(obj, target_z):
    """Scale uniformly so the Z extent is `target_z`."""
    current = height_of(obj)
    if current <= 0:
        raise RuntimeError("%s has no height to scale" % obj.name)
    factor = target_z / current
    obj.scale = [component * factor for component in obj.scale]
    apply_transforms(obj)


def world_bounds(obj):
    """The (min, max) corners of the object's world-space bounding box."""
    bpy.context.view_layer.update()
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    low = Vector((min(c.x for c in corners), min(c.y for c in corners),
                  min(c.z for c in corners)))
    high = Vector((max(c.x for c in corners), max(c.y for c in corners),
                   max(c.z for c in corners)))
    return low, high


def align_to(obj, reference):
    """Move `obj` so its footprint centre and its floor match `reference`'s.

    ONLY `obj` moves, and that is the point. The base's mesh and its armature
    are already in correspondence; applying a transform to the mesh alone would
    break it, and the symptom - a rig that animates a figure standing somewhere
    else - looks nothing like its cause. So the base defines the coordinate
    frame and is never touched, and the shell is what comes to meet it.

    Two figures standing on the same floor, centred on the same axis, at the
    same height, are in correspondence closely enough for a proximity transfer.
    """
    low, high = world_bounds(obj)
    ref_low, ref_high = world_bounds(reference)
    obj.location.x += ((ref_low.x + ref_high.x) - (low.x + high.x)) / 2
    obj.location.y += ((ref_low.y + ref_high.y) - (low.y + high.y)) / 2
    obj.location.z += ref_low.z - low.z
    apply_transforms(obj)


def drop_to_floor(obj):
    """Centre X and Y on the world origin, and put the lowest point on Z=0.

    For the STL copy only. A print wants its model sitting on the build plate
    at the origin; nothing else here does, and nothing else may use this - see
    align_to() for why the base must not be moved.
    """
    low, high = world_bounds(obj)
    obj.location.x -= (low.x + high.x) / 2
    obj.location.y -= (low.y + high.y) / 2
    obj.location.z -= low.z
    apply_transforms(obj)


def _components(bm):
    """One set of vertex indices per connected component."""
    seen = set()
    groups = []
    for vert in bm.verts:
        if vert.index in seen:
            continue
        stack, group = [vert], set()
        while stack:
            current = stack.pop()
            if current.index in group:
                continue
            group.add(current.index)
            for edge in current.link_edges:
                other = edge.other_vert(current)
                if other.index not in group:
                    stack.append(other)
        seen |= group
        groups.append(group)
    return groups


def keep_largest_component(obj):
    """Delete every loose part but the biggest. Returns how many were dropped.

    Spec §2.3 measured 10,895 components on a raw reconstruction with 83.5% of
    the faces in one of them. RemeshMesh's drop_small_components removes most
    of that in-graph; this is the backstop for whatever survives, and it is why
    the STL can promise a single body.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    groups = _components(bm)
    if len(groups) > 1:
        biggest = max(groups, key=len)
        doomed = [v for v in bm.verts if v.index not in biggest]
        bmesh.ops.delete(bm, geom=doomed, context='VERTS')
        bm.to_mesh(obj.data)
        obj.data.update()
    bm.free()
    return max(len(groups) - 1, 0)


def weld(obj, distance=0.0005):
    """Merge vertices closer than `distance`, in metres."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=distance)
    bm.to_mesh(obj.data)
    obj.data.update()
    bm.free()


def fill_holes(obj):
    """Cap every boundary loop. sides=0 means no size limit."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=0)
    bm.to_mesh(obj.data)
    obj.data.update()
    bm.free()


def remesh(obj, voxel_size):
    """Voxel remesh: the last resort that guarantees a closed surface."""
    modifier = obj.modifiers.new("remesh", 'REMESH')
    modifier.mode = 'VOXEL'
    modifier.voxel_size = voxel_size
    _activate(obj)
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def non_manifold_edges(obj):
    """Edges bounded by anything other than exactly two faces."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    count = sum(1 for edge in bm.edges if len(edge.link_faces) != 2)
    bm.free()
    return count


def clean_shell(obj, weld_distance=0.0005, voxel_size=0.0):
    """Largest part only, welded, capped, optionally remeshed. Returns drops.

    In that order: dropping the specks first means the weld and the hole fill
    are not asked to reason about 10,000 stray triangles, and the remesh - when
    it is asked for at all - runs on a surface that is already nearly closed.
    """
    dropped = keep_largest_component(obj)
    weld(obj, weld_distance)
    fill_holes(obj)
    if voxel_size > 0:
        remesh(obj, voxel_size)
    return dropped


def export_glb(objects, path):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format='GLB', use_selection=True,
        export_animations=False)


def export_stl(obj, path, height_mm):
    """Export a copy of `obj` scaled so its height is `height_mm`.

    STL carries no units and every slicer reads it as millimetres, so scaling
    the copy to 32 Blender units and exporting at global_scale 1.0 is what
    makes it come off the printer 32 mm tall.

    A copy, because the same object is still wanted at real-world scale for the
    GLB and the turnarounds, and transform_apply is destructive.
    """
    copy = obj.copy()
    copy.data = obj.data.copy()
    bpy.context.collection.objects.link(copy)
    try:
        fit_to_height(copy, height_mm)
        drop_to_floor(copy)
        _activate(copy)
        bpy.ops.wm.stl_export(
            filepath=str(path), export_selected_objects=True,
            global_scale=1.0, apply_modifiers=True, ascii_format=False)
    finally:
        bpy.data.objects.remove(copy, do_unlink=True)
