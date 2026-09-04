"""Binding the clothed shell to the base's armature.

This is spec §7.1 - the one part of the design the feasibility probe did not
settle. A-pose alignment removes the reason to expect failure, but nothing has
proven the transfer works on a bulky jacket whose silhouette departs from the
body underneath.

Two ways to bind, because that risk is real:

'transfer' is the design's choice - copy the base's own 127 vertex groups onto
the shell by proximity. It inherits SAM3DBody's actual skinning, which was
built for a human body and is better than anything derived from scratch.

'auto' is Blender's bone-heat weighting straight from the armature, ignoring
the base mesh's weights entirely. It cannot smear in the way transfer can,
because it never has to decide which base vertex a sleeve corresponds to - it
solves for the bones directly. Worse skinning where transfer works; a real
answer where transfer does not.

Note this is NOT the Surface Deform fallback the spec names. Surface Deform
has no glTF equivalent, so a shell bound that way cannot be exported as a
rigged GLB at all - only baked per frame, which is a different deliverable.
Automatic weights produce a genuinely rigged, exportable file, which is what
the goal actually asks for.
"""
import bpy

BINDS = ("transfer", "auto")


def deform_bones(armature):
    """The names of the bones that can actually deform a mesh."""
    return [bone.name for bone in armature.data.bones if bone.use_deform]


def _activate(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def transfer_weights(source, target):
    """Copy `source`'s vertex groups onto `target` by proximity.

    POLYINTERP_NEAREST - the nearest face, interpolated across it - rather
    than NEAREST vertex. The base is about 18k verts and the shell up to 200k,
    so a vertex-to-vertex mapping would quantise the shell's weights onto
    whichever body vertex happened to be closest and band the result at every
    joint. Interpolating across the nearest face is what lets a sleeve pick up
    a blend of the upper arm's weights rather than exactly one of them.

    datalayout_transfer() runs first and is not optional: the modifier writes
    into vertex groups that must already exist on the destination, and creates
    none of them itself. Without it the modifier applies cleanly and transfers
    nothing, which is the quiet failure this whole stage is built to avoid.
    """
    modifier = target.modifiers.new("weights", 'DATA_TRANSFER')
    modifier.object = source
    modifier.use_object_transform = True
    modifier.use_vert_data = True
    modifier.data_types_verts = {'VGROUP_WEIGHTS'}
    modifier.vert_mapping = 'POLYINTERP_NEAREST'
    modifier.layers_vgroup_select_src = 'ALL'
    modifier.layers_vgroup_select_dst = 'NAME'
    _activate(target)
    bpy.ops.object.datalayout_transfer(modifier=modifier.name)
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def bind(target, armature):
    """Parent `target` to `armature`, deforming through its vertex groups."""
    target.parent = armature
    target.matrix_parent_inverse = armature.matrix_world.inverted()
    modifier = target.modifiers.new("armature", 'ARMATURE')
    modifier.object = armature
    modifier.use_vertex_groups = True


def auto_weights(target, armature):
    """Bone-heat weighting straight from the armature, and parent in one step.

    parent_set does both the weighting and the Armature modifier, so this does
    not call bind() afterwards.
    """
    bpy.ops.object.select_all(action='DESELECT')
    target.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')


def unweighted_vertices(obj, bone_names):
    """Vertices carrying no non-zero weight in any deform group.

    Group membership with a zero weight is not weighting - a vertex like that
    still does not move with the skeleton - so the weight is checked, not just
    the membership.
    """
    wanted = {i for i, group in enumerate(obj.vertex_groups)
              if group.name in bone_names}
    if not wanted:
        return len(obj.data.vertices)
    return sum(
        1 for vert in obj.data.vertices
        if not any(g.group in wanted and g.weight > 0 for g in vert.groups))
