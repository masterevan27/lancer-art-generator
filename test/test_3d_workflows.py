"""The two 3D workflows are checked in, so they can rot silently.

Half of this runs anywhere: the graph is internally consistent, and the node
set is the one the design chose. The other half needs a live ComfyUI and is
where the real value is - it re-derives the required input set from
/object_info and fails when a model is renamed, a combo option disappears, or
a dynamic combo grows a child. Skipped, not failed, when no server answers.
"""
import json
import unittest

from test.helpers import REPO
from test.workflow_schema import (
    dynamic_combo_choices, expected_inputs, object_info, server_is_up)

MESH = REPO / "workflows" / "api" / "Util_Image_to_Mesh_Hunyuan3D_v1.json"
RIG = REPO / "workflows" / "api" / "Util_Image_to_RiggedBody_SAM3D_v1.json"
GRAPHS = {"mesh": json.loads(MESH.read_text(encoding="utf-8")),
          "rig": json.loads(RIG.read_text(encoding="utf-8"))}


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
        for label, graph in GRAPHS.items():
            loads = [n for n, d in graph.items() if d["class_type"] == "LoadImage"]
            with self.subTest(graph=label):
                self.assertEqual(len(loads), 1)

    def test_each_graph_has_exactly_one_save_glb(self):
        for label, graph in GRAPHS.items():
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

    def test_the_specks_are_dropped_in_graph(self):
        """Spec §2.3 measured 10,878 sub-20-face components on one token."""
        remesh = node_named(GRAPHS["mesh"], "RemeshMesh")["inputs"]
        self.assertGreater(remesh["drop_small_components"], 0)

    def test_no_custom_node_pack_is_required(self):
        """Spec §2.1. Every class_type here ships with ComfyUI."""
        native = {
            "LoadImage", "SaveGLB", "KSampler", "ImageOnlyCheckpointLoader",
            "CLIPVisionEncode", "Hunyuan3Dv2Conditioning", "EmptyLatentHunyuan3Dv2",
            "VAEDecodeHunyuan3D", "VoxelToMesh", "RemeshMesh", "DecimateMesh",
            "SAM3DBody_Loader", "SAM3DBody_Predict", "BuildPoseFile",
        }
        for label, graph in GRAPHS.items():
            for nid, node in graph.items():
                with self.subTest(graph=label, node=nid):
                    self.assertIn(node["class_type"], native)


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
