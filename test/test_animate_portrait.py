"""The portrait animation workflow and the script that patches it.

Same split as test_3d_workflows.py: most of this runs anywhere and checks the
checked-in graph is internally consistent and wired the way the design chose,
while the live half re-derives the required input set from /object_info so a
renamed model or a moved input fails here rather than three minutes into a
render. Skipped, not failed, when no server answers.
"""
import contextlib
import io
import json
import unittest
from pathlib import Path

from test.helpers import load_animate
from test.workflow_schema import (
    dynamic_combo_choices, expected_inputs, object_info, server_is_up)

REPO = Path(__file__).resolve().parent.parent
WORKFLOW = REPO / "workflows" / "api" / "Util_Portrait_to_AnimatedWEBP_Wan22_v1.json"

ap = load_animate()


def graph():
    return json.loads(WORKFLOW.read_text(encoding="utf-8"))


def links(node):
    """The ["node_id", slot] references in one node's inputs."""
    return [v for v in node["inputs"].values()
            if isinstance(v, list) and len(v) == 2 and isinstance(v[0], str)]


def nodes_of(g, class_type):
    return {n: d for n, d in g.items() if d["class_type"] == class_type}


def only(g, class_type):
    """The single node of this class, by id."""
    found = nodes_of(g, class_type)
    assert len(found) == 1, "%s appears %d times" % (class_type, len(found))
    return next(iter(found.items()))


class TestWorkflowShape(unittest.TestCase):
    def test_the_workflow_file_is_checked_in(self):
        self.assertTrue(WORKFLOW.exists(), "%s is missing" % WORKFLOW)

    def test_every_link_points_at_a_real_node(self):
        g = graph()
        for nid, node in g.items():
            for ref in links(node):
                with self.subTest(node=nid, ref=ref):
                    self.assertIn(ref[0], g)

    def test_one_load_image_the_script_patches_the_portrait_into(self):
        self.assertEqual(len(nodes_of(graph(), "LoadImage")), 1)

    def test_one_save_animated_webp_that_produces_the_output(self):
        self.assertEqual(len(nodes_of(graph(), "SaveAnimatedWEBP")), 1)

    def test_decodes_with_the_wan_21_vae_not_the_22_vae(self):
        """The A14B high/low-noise I2V pair is a 2.1-VAE model.

        wan2.2_vae belongs to the 5B TI2V checkpoint. Pairing it with these
        UNets decodes to noise, and nothing upstream complains.
        """
        _, vae = only(graph(), "VAELoader")
        self.assertEqual(vae["inputs"]["vae_name"], "wan_2.1_vae.safetensors")

    def test_loads_both_the_high_and_low_noise_unets(self):
        loaded = {d["inputs"]["unet_name"]
                  for d in nodes_of(graph(), "UNETLoader").values()}
        self.assertEqual(loaded, {
            "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
            "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"})

    def test_text_is_encoded_for_wan(self):
        _, clip = only(graph(), "CLIPLoader")
        self.assertEqual(clip["inputs"]["type"], "wan")
        self.assertEqual(clip["inputs"]["clip_name"],
                         "umt5_xxl_fp8_e4m3fn_scaled.safetensors")

    def test_the_portrait_is_the_start_image_of_the_video_latent(self):
        g = graph()
        load_id, _ = only(g, "LoadImage")
        _, i2v = only(g, "WanImageToVideo")
        self.assertEqual(i2v["inputs"]["start_image"], [load_id, 0])

    def test_the_high_noise_pass_hands_leftover_noise_to_the_low_noise_pass(self):
        """Two-stage WAN 2.2: the second sampler continues the first's latent.

        If the high-noise pass returned a finished latent, or the low-noise
        pass added fresh noise, the two stages stop being one denoise.
        """
        g = graph()
        samplers = nodes_of(g, "KSamplerAdvanced")
        self.assertEqual(len(samplers), 2)
        high = [n for n, d in samplers.items()
                if d["inputs"]["add_noise"] == "enable"]
        low = [n for n, d in samplers.items()
               if d["inputs"]["add_noise"] == "disable"]
        self.assertEqual(len(high), 1)
        self.assertEqual(len(low), 1)
        self.assertEqual(
            g[high[0]]["inputs"]["return_with_leftover_noise"], "enable")
        self.assertEqual(
            g[low[0]]["inputs"]["return_with_leftover_noise"], "disable")
        self.assertEqual(g[low[0]]["inputs"]["latent_image"], [high[0], 0])

    def test_the_two_passes_hand_over_at_the_same_step(self):
        g = graph()
        samplers = nodes_of(g, "KSamplerAdvanced")
        high = next(d for d in samplers.values()
                    if d["inputs"]["add_noise"] == "enable")["inputs"]
        low = next(d for d in samplers.values()
                   if d["inputs"]["add_noise"] == "disable")["inputs"]
        self.assertEqual(high["end_at_step"], low["start_at_step"])
        self.assertEqual(high["steps"], low["steps"])
        self.assertEqual(high["start_at_step"], 0)

    def test_the_loop_is_the_forward_frames_followed_by_the_reversed_ones(self):
        """Ping-pong: decode -> reverse -> trim -> rejoin -> save."""
        g = graph()
        decode_id, _ = only(g, "VAEDecode")
        reverse_id, reverse = only(g, "ReverseImageBatch")
        trim_id, trim = only(g, "GetImageRangeFromBatch")
        join_id, join = only(g, "ImageBatch")
        _, save = only(g, "SaveAnimatedWEBP")

        self.assertEqual(reverse["inputs"]["images"], [decode_id, 0])
        self.assertEqual(trim["inputs"]["images"], [reverse_id, 0])
        self.assertEqual(join["inputs"]["image1"], [decode_id, 0])
        self.assertEqual(join["inputs"]["image2"], [trim_id, 0])
        self.assertEqual(save["inputs"]["images"], [join_id, 0])

    def test_the_reversed_half_starts_past_the_frame_it_would_duplicate(self):
        """Frame 0 of the reversed batch IS the last forward frame."""
        _, trim = only(graph(), "GetImageRangeFromBatch")
        self.assertEqual(trim["inputs"]["start_index"], 1)


class TestWorkflowAgainstLiveServer(unittest.TestCase):
    """Re-derive what the server demands, so a ComfyUI update fails here."""

    @classmethod
    def setUpClass(cls):
        if not server_is_up():
            raise unittest.SkipTest("no ComfyUI on 127.0.0.1:8000")

    def test_every_node_class_exists_on_the_server(self):
        for nid, node in graph().items():
            with self.subTest(node=nid, cls=node["class_type"]):
                self.assertIsNotNone(object_info(node["class_type"]))

    def test_every_required_input_is_present(self):
        for nid, node in graph().items():
            schema = object_info(node["class_type"])
            if schema is None:
                continue
            required = schema["input"].get("required", {})
            for key in expected_inputs(required, node["inputs"]):
                with self.subTest(node=nid, cls=node["class_type"], input=key):
                    self.assertIn(key, node["inputs"])

    def test_every_named_model_and_option_is_one_the_server_offers(self):
        for nid, node in graph().items():
            schema = object_info(node["class_type"])
            if schema is None:
                continue
            required = schema["input"].get("required", {})
            for name, definition in required.items():
                choices = definition[0]
                meta = definition[1] if len(definition) > 1 else {}
                value = node["inputs"].get(name)
                if not isinstance(choices, list) or isinstance(value, list):
                    continue
                if value is None:
                    continue
                if meta.get("image_upload"):
                    # LoadImage.image: the enumerated list is only what is
                    # sitting in the input folder right now. The checked-in
                    # placeholder is never a member - animate-portrait.py
                    # uploads the real portrait and patches the reference in
                    # before queueing. Same exemption test_3d_workflows.py
                    # makes, for the same reason.
                    continue
                with self.subTest(node=nid, cls=node["class_type"], input=name):
                    self.assertIn(value, choices)


class TestGraphPatching(unittest.TestCase):
    """What the script hands ComfyUI, given the arguments it was called with."""

    def build(self, **kw):
        args = dict(image_ref="uploaded.png", description="she smiles",
                    negative="static", width=480, height=480, frames=33,
                    fps=16.0, steps=20, cfg=3.5, seed=7,
                    prefix="AnimatedPortraits/x", pingpong=True)
        args.update(kw)
        return ap.build_graph(**args)

    def test_the_uploaded_portrait_is_what_gets_loaded(self):
        _, load = only(self.build(), "LoadImage")
        self.assertEqual(load["inputs"]["image"], "uploaded.png")

    def test_size_and_frame_count_reach_the_video_latent(self):
        _, i2v = only(self.build(width=512, height=640, frames=49),
                      "WanImageToVideo")
        self.assertEqual(i2v["inputs"]["width"], 512)
        self.assertEqual(i2v["inputs"]["height"], 640)
        self.assertEqual(i2v["inputs"]["length"], 49)

    def test_the_description_becomes_the_positive_prompt(self):
        g = self.build(description="he tilts his head", negative="frozen")
        _, i2v = only(g, "WanImageToVideo")
        positive = g[i2v["inputs"]["positive"][0]]
        negative = g[i2v["inputs"]["negative"][0]]
        self.assertEqual(positive["inputs"]["text"], "he tilts his head")
        self.assertEqual(negative["inputs"]["text"], "frozen")

    def test_both_passes_share_one_seed(self):
        """Two samplers denoising one latent; a split seed is two renders."""
        g = self.build(seed=1234)
        seeds = {d["inputs"]["noise_seed"]
                 for d in nodes_of(g, "KSamplerAdvanced").values()}
        self.assertEqual(seeds, {1234})

    def test_the_passes_hand_over_at_half_the_step_count(self):
        g = self.build(steps=30)
        samplers = nodes_of(g, "KSamplerAdvanced")
        for d in samplers.values():
            self.assertEqual(d["inputs"]["steps"], 30)
        high = next(d for d in samplers.values()
                    if d["inputs"]["add_noise"] == "enable")["inputs"]
        low = next(d for d in samplers.values()
                   if d["inputs"]["add_noise"] == "disable")["inputs"]
        self.assertEqual(high["end_at_step"], 15)
        self.assertEqual(low["start_at_step"], 15)

    def test_the_reversed_half_is_two_frames_shorter_than_the_forward_half(self):
        """One frame each end, or the loop stutters on a duplicate."""
        _, trim = only(self.build(frames=49), "GetImageRangeFromBatch")
        self.assertEqual(trim["inputs"]["num_frames"], 47)

    def test_fps_and_prefix_reach_the_save_node(self):
        _, save = only(self.build(fps=24.0, prefix="Foo/bar"),
                       "SaveAnimatedWEBP")
        self.assertEqual(save["inputs"]["fps"], 24.0)
        self.assertEqual(save["inputs"]["filename_prefix"], "Foo/bar")

    def test_without_pingpong_the_decode_feeds_the_save_directly(self):
        g = self.build(pingpong=False)
        decode_id, _ = only(g, "VAEDecode")
        _, save = only(g, "SaveAnimatedWEBP")
        self.assertEqual(save["inputs"]["images"], [decode_id, 0])

    def test_without_pingpong_the_loop_nodes_are_gone(self):
        """Left dangling they would still execute - and they are KJNodes,
        the one custom dependency this graph has."""
        g = self.build(pingpong=False)
        for cls in ("ReverseImageBatch", "GetImageRangeFromBatch", "ImageBatch"):
            with self.subTest(cls=cls):
                self.assertEqual(nodes_of(g, cls), {})

    def test_patching_leaves_the_checked_in_workflow_alone(self):
        """build_graph is called once per run; a shared dict would leak."""
        before = json.loads(WORKFLOW.read_text(encoding="utf-8"))
        self.build(width=768, description="mutated")
        self.assertEqual(json.loads(WORKFLOW.read_text(encoding="utf-8")), before)
        _, i2v = only(self.build(), "WanImageToVideo")
        self.assertEqual(i2v["inputs"]["width"], 480)


class TestArgumentHandling(unittest.TestCase):
    def test_frames_snap_to_a_length_wan_accepts(self):
        """WanImageToVideo.length steps by 4 from 1; 30 is not a legal latent."""
        self.assertEqual(ap.snap_frames(30), 29)
        self.assertEqual(ap.snap_frames(33), 33)
        self.assertEqual(ap.snap_frames(50), 49)

    def test_frames_never_snap_below_a_single_frame(self):
        self.assertEqual(ap.snap_frames(1), 1)
        self.assertEqual(ap.snap_frames(2), 1)

    def test_size_snaps_to_the_sixteen_pixel_grid(self):
        self.assertEqual(ap.snap_size(500), 496)
        self.assertEqual(ap.snap_size(480), 480)

    def test_the_output_sits_next_to_the_portrait_by_default(self):
        out = ap.output_path(Path("G:/art/jules.png"), None)
        self.assertEqual(out, Path("G:/art/jules-animated.webp"))

    def test_an_explicit_out_wins(self):
        out = ap.output_path(Path("G:/art/jules.png"), "D:/x/loop.webp")
        self.assertEqual(out, Path("D:/x/loop.webp"))

    def test_the_default_description_is_a_subtle_idle_motion(self):
        """Shipped default: it has to move the face without moving the camera."""
        text = ap.DEFAULT_DESCRIPTION.lower()
        self.assertIn("blink", text)
        self.assertIn("smile", text)
        self.assertIn("camera", text)

    def test_the_default_negative_guards_a_frozen_frame(self):
        self.assertIn("static", ap.DEFAULT_NEGATIVE.lower())

    def test_describing_the_motion_is_optional(self):
        opts = ap.parse_args(["portrait.png"])
        self.assertEqual(opts.describe, ap.DEFAULT_DESCRIPTION)
        self.assertEqual(opts.image, "portrait.png")
        self.assertTrue(opts.pingpong)

    def test_no_pingpong_turns_the_loop_off(self):
        self.assertFalse(ap.parse_args(["p.png", "--no-pingpong"]).pingpong)

    def test_a_seed_of_minus_one_is_replaced_by_a_random_one(self):
        """Two runs with the default seed must not be the same render."""
        self.assertNotEqual(ap.resolve_seed(-1), ap.resolve_seed(-1))
        self.assertEqual(ap.resolve_seed(42), 42)


class FakeComfy:
    """Stands in for the HTTP client; records what it was asked to fetch."""

    def __init__(self, blobs):
        self.blobs = blobs
        self.asked = []

    def _get_bytes(self, path):
        self.asked.append(path)
        for name, blob in self.blobs.items():
            if name in path:
                return blob
        raise AssertionError("asked for something unexpected: %s" % path)


class TestSavingTheResult(unittest.TestCase):
    """SaveAnimatedWEBP reports under the same key as still images."""

    def record(self, filenames):
        return {"outputs": {"17": {"images": [
            {"filename": f, "subfolder": "AnimatedPortraits", "type": "output"}
            for f in filenames]}}}

    def test_the_webp_is_downloaded_and_written_where_asked(self):
        import tempfile
        comfy = FakeComfy({"loop.webp": b"RIFFfake-webp-bytes"})
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "nested" / "out.webp"
            ap.save_result(comfy, self.record(["loop.webp"]), dest)
            self.assertEqual(dest.read_bytes(), b"RIFFfake-webp-bytes")

    def test_a_still_preview_alongside_the_webp_is_not_the_one_saved(self):
        """Some setups emit a poster frame too; picking it would save a PNG."""
        import tempfile
        comfy = FakeComfy({"loop.webp": b"the-animation",
                           "preview.png": b"a-single-frame"})
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "out.webp"
            ap.save_result(comfy, self.record(["preview.png", "loop.webp"]), dest)
            self.assertEqual(dest.read_bytes(), b"the-animation")

    def test_a_job_that_produced_no_webp_is_an_error_not_an_empty_file(self):
        import tempfile
        comfy = FakeComfy({"preview.png": b"a-single-frame"})
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "out.webp"
            with self.assertRaises(SystemExit):
                ap.save_result(comfy, self.record(["preview.png"]), dest)
            self.assertFalse(dest.exists())

    def test_the_subfolder_and_type_are_carried_into_the_request(self):
        """/view needs all three or it 404s on anything in a subfolder."""
        import tempfile
        comfy = FakeComfy({"loop.webp": b"x"})
        with tempfile.TemporaryDirectory() as tmp:
            ap.save_result(comfy, self.record(["loop.webp"]), Path(tmp) / "o.webp")
        asked = comfy.asked[0]
        self.assertIn("filename=loop.webp", asked)
        self.assertIn("subfolder=AnimatedPortraits", asked)
        self.assertIn("type=output", asked)


class TestBackgroundPreset(unittest.TestCase):
    """--background swaps one bundle of defaults; everything else is shared.

    The flag exists because a background and a portrait differ only in their
    defaults - shape, motion, negative, which table --roll reads, where the
    render lands. The graph, the upload, the loop and the download are the
    same job, so they stay one script rather than two.
    """

    def test_the_flag_is_off_so_the_portrait_path_is_the_default(self):
        self.assertFalse(ap.parse_args(["p.png"]).background)

    def test_a_background_renders_widescreen_rather_than_square(self):
        """SillyTavern paints a background across the window, and Wan 2.2's
        native landscape bucket is 832x480."""
        opts = ap.parse_args(["bg.png", "--background"])
        self.assertEqual((opts.width, opts.height), (832, 480))

    def test_a_portrait_still_renders_square(self):
        opts = ap.parse_args(["p.png"])
        self.assertEqual((opts.width, opts.height), (480, 480))

    def test_size_still_overrides_both_sides(self):
        opts = ap.parse_args(["bg.png", "--background", "--size", "640"])
        self.assertEqual((opts.width, opts.height), (640, 640))

    def test_an_explicit_dimension_beats_the_preset(self):
        opts = ap.parse_args(["bg.png", "--background", "--width", "1280"])
        self.assertEqual((opts.width, opts.height), (1280, 480))

    def test_the_default_motion_moves_the_scene_not_a_face(self):
        text = ap.BACKGROUND_DESCRIPTION.lower()
        self.assertNotIn("blink", text)
        self.assertNotIn("smile", text)
        self.assertIn("camera", text)

    def test_a_background_gets_the_scene_description_by_default(self):
        opts = ap.parse_args(["bg.png", "--background"])
        self.assertEqual(opts.describe, ap.BACKGROUND_DESCRIPTION)

    def test_the_background_negative_drops_the_face_guards(self):
        """Nothing in a landscape has an identity to drift, and naming a
        face in the negative invites Wan to put one in the frame."""
        text = ap.BACKGROUND_NEGATIVE.lower()
        self.assertIn("static", text)
        self.assertNotIn("face", text)
        self.assertNotIn("limbs", text)

    def test_describing_the_motion_still_wins_over_the_preset(self):
        opts = ap.parse_args(["bg.png", "--background", "-d", "rain falls"])
        self.assertEqual(opts.describe, "rain falls")

    def test_roll_reads_the_background_table_from_the_scene_tables(self):
        opts = ap.parse_args(["bg.png", "--background", "--roll"])
        self.assertEqual(Path(opts.tables), ap.BACKGROUND_TABLES)
        self.assertEqual(opts.table, ap.BACKGROUND_TABLE)

    def test_roll_still_reads_the_npc_animation_table_for_a_portrait(self):
        opts = ap.parse_args(["p.png", "--roll"])
        self.assertEqual(Path(opts.tables), ap.DEFAULT_TABLES)
        self.assertEqual(opts.table, ap.ANIMATION_TABLE)

    def test_an_explicit_tables_file_beats_the_preset(self):
        opts = ap.parse_args(["bg.png", "--background", "--tables", "x.md"])
        self.assertEqual(Path(opts.tables), Path("x.md"))

    def test_the_webp_is_smaller_by_default_because_a_page_loads_it(self):
        self.assertEqual(ap.parse_args(["bg.png", "--background"]).quality, 80)
        self.assertEqual(ap.parse_args(["p.png"]).quality, 90)

    def test_the_two_kinds_land_in_separate_comfy_folders(self):
        self.assertEqual(ap.parse_args(["bg.png", "--background"]).prefix,
                         "AnimatedBackgrounds")
        self.assertEqual(ap.parse_args(["p.png"]).prefix, "AnimatedPortraits")


class TestBackgroundDryRun(unittest.TestCase):
    """The whole flag, end to end, without a server."""

    def graph_for(self, argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            ap.main(argv)
        printed = out.getvalue()
        return json.loads(printed[printed.index("{"):])

    def test_a_background_dry_run_carries_the_preset_into_the_graph(self):
        g = self.graph_for(["bg.png", "--background", "--dry-run", "--seed", "3"])
        _, i2v = only(g, "WanImageToVideo")
        self.assertEqual(i2v["inputs"]["width"], 832)
        self.assertEqual(i2v["inputs"]["height"], 480)
        positive = g[i2v["inputs"]["positive"][0]]["inputs"]["text"]
        self.assertEqual(positive, ap.BACKGROUND_DESCRIPTION)
        _, save = only(g, "SaveAnimatedWEBP")
        self.assertTrue(
            save["inputs"]["filename_prefix"].startswith("AnimatedBackgrounds/"),
            save["inputs"]["filename_prefix"])

    def test_the_portrait_dry_run_is_unchanged(self):
        g = self.graph_for(["p.png", "--dry-run", "--seed", "3"])
        _, i2v = only(g, "WanImageToVideo")
        self.assertEqual(i2v["inputs"]["width"], 480)
        self.assertEqual(i2v["inputs"]["height"], 480)
        positive = g[i2v["inputs"]["positive"][0]]["inputs"]["text"]
        self.assertEqual(positive, ap.DEFAULT_DESCRIPTION)
        _, save = only(g, "SaveAnimatedWEBP")
        self.assertTrue(
            save["inputs"]["filename_prefix"].startswith("AnimatedPortraits/"),
            save["inputs"]["filename_prefix"])


if __name__ == "__main__":
    unittest.main()
