"""The two 3D workflows are checked in, so they can rot silently.

Half of this runs anywhere: the graph is internally consistent, and the node
set is the one the design chose. The other half needs a live ComfyUI and is
where the real value is - it re-derives the required input set from
/object_info and fails when a model is renamed, a combo option disappears, or
a dynamic combo grows a child. Skipped, not failed, when no server answers.
"""
import json
import unittest

from test.helpers import REPO, load_3d
from test.workflow_schema import (
    dynamic_combo_choices, expected_inputs, object_info, server_is_up)

d3 = load_3d()

MESH = REPO / "workflows" / "api" / "Util_Image_to_Mesh_Hunyuan3D_v1.json"
RIG = REPO / "workflows" / "api" / "Util_Image_to_RiggedBody_SAM3D_v1.json"
BACKVIEW = REPO / "workflows" / "api" / "Util_BackView_QwenEdit_v1.json"
GRAPHS = {"mesh": json.loads(MESH.read_text(encoding="utf-8")),
          "rig": json.loads(RIG.read_text(encoding="utf-8")),
          "backview": json.loads(BACKVIEW.read_text(encoding="utf-8"))}

# The two reconstruction graphs. Three of TestGraphShape's checks are about
# image-to-mesh specifically - one LoadImage, one SaveGLB, a native node set
# that does not include the Qwen stack - and the back view answers to none of
# them. It gets TestBackViewGraph instead.
MESH_GRAPHS = {k: v for k, v in GRAPHS.items() if k in ("mesh", "rig")}


def links(node):
    """The ["node_id", slot] references in one node's inputs."""
    return [v for v in node["inputs"].values()
            if isinstance(v, list) and len(v) == 2 and isinstance(v[0], str)]


def node_named(graph, class_type):
    return next(d for d in graph.values() if d["class_type"] == class_type)


class TestGraphShape(unittest.TestCase):
    def test_every_link_points_at_a_real_node(self):
        for label, graph in GRAPHS.items():
            for nid, node in graph.items():
                for ref in links(node):
                    with self.subTest(graph=label, node=nid, ref=ref):
                        self.assertIn(ref[0], graph)

    def test_each_graph_has_exactly_one_load_image(self):
        """generate-3d.py finds it by class_type to patch the source in."""
        for label, graph in MESH_GRAPHS.items():
            loads = [n for n, d in graph.items() if d["class_type"] == "LoadImage"]
            with self.subTest(graph=label):
                self.assertEqual(len(loads), 1)

    def test_each_graph_has_exactly_one_save_glb(self):
        for label, graph in MESH_GRAPHS.items():
            saves = [n for n, d in graph.items() if d["class_type"] == "SaveGLB"]
            with self.subTest(graph=label):
                self.assertEqual(len(saves), 1)

    def test_no_input_is_a_nested_object(self):
        """The §2.6 trap: a dict here validates and then fails at execution."""
        for label, graph in GRAPHS.items():
            for nid, node in graph.items():
                for key, value in node["inputs"].items():
                    with self.subTest(graph=label, node=nid, key=key):
                        self.assertNotIsInstance(value, dict)

    def test_the_dotted_pose_keys_are_present(self):
        pose = node_named(GRAPHS["rig"], "BuildPoseFile")["inputs"]
        for key, value in (("format", "glb"),
                           ("format.mesh_style", "body_mesh"),
                           ("format.mesh_style.bone_vis", "off"),
                           ("format.mesh_style.shader", "default")):
            with self.subTest(key=key):
                self.assertEqual(pose[key], value)

    def test_the_pose_is_exported_at_the_bind_position(self):
        """'absolute' would bake the estimator's camera depth into the root."""
        self.assertEqual(
            node_named(GRAPHS["rig"], "BuildPoseFile")["inputs"]["camera_translation"],
            "off")

    def test_one_figure_only(self):
        """A second detected person would export a second armature."""
        self.assertEqual(
            node_named(GRAPHS["rig"], "BuildPoseFile")["inputs"]["track_index"], 0)

    def test_nothing_remeshes_between_the_voxels_and_the_save(self):
        """RemeshMesh clipped every reconstruction to a half-unit box.

        Measured on a real catalogue shell: straight off VoxelToMesh the
        figure spanned y -0.978..0.986 - head, hands and feet all present -
        and after RemeshMesh it spanned exactly y -0.503..0.504, flat-cut at
        both ends. Every downstream symptom this project chased for two
        phases (the torn "two half-figures", the missing head, the blank
        turnarounds) was that clip. Spec §2.3's speck dropping, which is what
        RemeshMesh was here for, now happens in npc_mesh.drop_small_components
        by surface area - 895 specks off one shell, one component left.

        The node stays out. If it ever comes back, it must be shown not to
        clip: assert the saved GLB spans more than a unit box first.
        """
        classes = {d["class_type"] for d in GRAPHS["mesh"].values()}
        self.assertNotIn("RemeshMesh", classes)
        self.assertIn("VoxelToMesh", classes)

    def test_no_custom_node_pack_is_required(self):
        """Spec §2.1. Every class_type here ships with ComfyUI."""
        native = {
            "LoadImage", "SaveGLB", "KSampler", "ImageOnlyCheckpointLoader",
            "CLIPVisionEncode", "Hunyuan3Dv2ConditioningMultiView",
            "EmptyLatentHunyuan3Dv2",
            "VAEDecodeHunyuan3D", "VoxelToMesh", "DecimateMesh",
            "SAM3DBody_Loader", "SAM3DBody_Predict", "BuildPoseFile",
        }
        for label, graph in MESH_GRAPHS.items():
            for nid, node in graph.items():
                with self.subTest(graph=label, node=nid):
                    self.assertIn(node["class_type"], native)


class TestBackViewGraph(unittest.TestCase):
    """§4.4. Three LoadImage nodes and two encoders, so node_of() cannot
    address them - which is why generate-3d.py follows links from KSampler."""

    graph = GRAPHS["backview"]

    def test_exactly_one_ksampler(self):
        """The anchor everything else is reached from."""
        samplers = [n for n, d in self.graph.items()
                    if d["class_type"] == "KSampler"]
        self.assertEqual(len(samplers), 1)

    def test_exactly_one_save_image(self):
        saves = [n for n, d in self.graph.items()
                 if d["class_type"] == "SaveImage"]
        self.assertEqual(len(saves), 1)

    def test_three_load_image_nodes(self):
        loads = [n for n, d in self.graph.items()
                 if d["class_type"] == "LoadImage"]
        self.assertEqual(len(loads), 3)

    def test_the_slots_resolve(self):
        slots = d3.backview_slots(self.graph)
        for key in ("encode", "image1", "image2", "image3", "save"):
            with self.subTest(key=key):
                self.assertIn(slots[key], self.graph)

    def test_every_image_slot_is_a_distinct_load_image(self):
        slots = d3.backview_slots(self.graph)
        ids = [slots["image1"], slots["image2"], slots["image3"]]
        self.assertEqual(len(set(ids)), 3)
        for node_id in ids:
            with self.subTest(node=node_id):
                self.assertEqual(self.graph[node_id]["class_type"], "LoadImage")

    def test_the_encoder_is_the_positive_conditioning(self):
        slots = d3.backview_slots(self.graph)
        sampler = next(d for d in self.graph.values()
                       if d["class_type"] == "KSampler")
        self.assertEqual(sampler["inputs"]["positive"][0], slots["encode"])

    def test_the_negative_is_a_different_node(self):
        """Two TextEncodeQwenImageEditPlus nodes is the whole reason node_of()
        cannot be used here. If that ever stops being true, the simpler helper
        should come back."""
        sampler = next(d for d in self.graph.values()
                       if d["class_type"] == "KSampler")
        self.assertNotEqual(sampler["inputs"]["positive"][0],
                            sampler["inputs"]["negative"][0])

    def test_no_custom_node_pack_is_required(self):
        """Spec §2.1 and §2.2: everything here ships with ComfyUI."""
        for nid, node in self.graph.items():
            with self.subTest(node=nid):
                self.assertNotIn(".", node["class_type"])

    def test_the_cfg_is_pinned_to_one(self):
        """The negative encoder carries no vae and no images. That is valid
        only at cfg 1.0, where the negative branch cancels - see node 13's
        _meta. Raising cfg without rewiring node 12 silently degrades the
        conditioning, and nothing else would catch it."""
        sampler = next(d for d in self.graph.values()
                       if d["class_type"] == "KSampler")
        self.assertEqual(sampler["inputs"]["cfg"], 1.0)

    def test_the_negative_encoder_carries_no_images_or_vae(self):
        """The other half of the cfg==1.0 invariant: build_backview_job's
        docstring and node 13's _meta both depend on the negative encoder
        being a no-op. If someone wires it up with real images and a vae
        without also lowering cfg off 1.0, that has to fail somewhere - this
        is that somewhere. Found by following the sampler's 'negative' link,
        not by node id, since a re-export renumbers everything."""
        sampler = next(d for d in self.graph.values()
                       if d["class_type"] == "KSampler")
        negative = self.graph[sampler["inputs"]["negative"][0]]
        self.assertNotIn("vae", negative["inputs"])
        for key in ("image1", "image2", "image3"):
            self.assertNotIn(key, negative["inputs"])


@unittest.skipUnless(server_is_up(), "no ComfyUI on 127.0.0.1:8000")
class TestAgainstLiveObjectInfo(unittest.TestCase):
    def test_every_node_class_is_registered(self):
        for label, graph in GRAPHS.items():
            for nid, node in graph.items():
                with self.subTest(graph=label, node=nid):
                    self.assertIsNotNone(object_info(node["class_type"]),
                                         "%s is not registered" % node["class_type"])

    def test_the_inputs_are_exactly_what_the_server_requires(self):
        """Missing keys fail at execution; stale ones mean a schema moved."""
        for label, graph in GRAPHS.items():
            for nid, node in graph.items():
                info = object_info(node["class_type"])
                if info is None:
                    continue
                wanted = expected_inputs(info["input"]["required"], node["inputs"])
                optional = list((info["input"].get("optional") or {}).keys())
                given = set(node["inputs"])
                with self.subTest(graph=label, node=nid, direction="missing"):
                    self.assertEqual(sorted(set(wanted) - given), [])
                with self.subTest(graph=label, node=nid, direction="unknown"):
                    self.assertEqual(sorted(given - set(wanted) - set(optional)), [])

    def test_every_combo_value_is_still_on_offer(self):
        """Catches a renamed checkpoint or a dropped sampler."""
        for label, graph in GRAPHS.items():
            for nid, node in graph.items():
                info = object_info(node["class_type"])
                if info is None:
                    continue
                for key, definition in info["input"]["required"].items():
                    kind = definition[0]
                    meta = definition[1] if len(definition) > 1 else {}
                    options = kind if isinstance(kind, list) else (
                        meta.get("options") if kind == "COMBO" else None)
                    value = node["inputs"].get(key)
                    if not options or isinstance(value, list) or value is None:
                        continue
                    if meta.get("image_upload"):
                        # LoadImage.image: the enumerated list is only what's
                        # currently sitting in the input folder. Both graphs'
                        # "apose.png [output]" is a placeholder generate-3d.py
                        # patches in before queueing (the "[output]" suffix
                        # points ComfyUI at the output folder instead), so it
                        # is never a member of this list - LoadImage validates
                        # it at execution time via a file-existence check, not
                        # combo membership. Checking it here would fail on any
                        # server that hasn't happened to render that exact
                        # filename already.
                        continue
                    with self.subTest(graph=label, node=nid, key=key):
                        self.assertIn(value, options)

    def test_every_dynamic_combo_choice_is_still_on_offer(self):
        """The plain-COMBO check above can't see COMFY_DYNAMICCOMBO_V3 keys.

        kind == "COMFY_DYNAMICCOMBO_V3" is a string, not a list and not the
        literal "COMBO", so it falls through both branches of the check above
        and is skipped there entirely - the chosen value of RemeshMesh's
        sign_mode, DecimateMesh's placement_mode and every level of
        BuildPoseFile's format is never verified against what the server
        offers. This walks the same dotted option tree
        test_the_inputs_are_exactly_what_the_server_requires uses to find
        required keys, but checks the value picked at each level instead.
        """
        for label, graph in GRAPHS.items():
            for nid, node in graph.items():
                info = object_info(node["class_type"])
                if info is None:
                    continue
                choices = dynamic_combo_choices(
                    info["input"]["required"], node["inputs"])
                for key, chosen, legal in choices:
                    with self.subTest(graph=label, node=nid, key=key):
                        self.assertIn(chosen, legal)

    def test_the_models_this_design_measured_are_installed(self):
        """Spec §2.3 and §2.4 name these exactly; nothing else was measured."""
        pairs = (("ImageOnlyCheckpointLoader", "ckpt_name",
                  "hunyuan3d-dit-v2-mv_fp16.safetensors"),
                 ("SAM3DBody_Loader", "model_file",
                  "sam_3d_body_dinov3_bf16.safetensors"))
        for class_type, key, name in pairs:
            definition = object_info(class_type)["input"]["required"][key]
            options = (definition[0] if isinstance(definition[0], list)
                       else definition[1]["options"])
            with self.subTest(model=name):
                self.assertIn(name, options)


if __name__ == "__main__":
    unittest.main()
