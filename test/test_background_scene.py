"""Contract tests for reproducible scene plans and reference-based battlemaps."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:
    import background_scene as scene
except ImportError:
    scene = None


class BackgroundSceneTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(scene, "background_scene implementation is missing")
        self.catalogue = scene.load_catalogue(ROOT / "prompts/background-generator-tables.md")

    def test_every_pool_has_twenty_distinct_enabled_entries(self):
        self.assertEqual(self.catalogue["environments"], ["outdoor", "indoor", "space"])
        for table in self.catalogue["tables"]:
            values = table["values"]
            self.assertGreaterEqual(len({v["text"] for v in values}), 20, table["name"])
            self.assertTrue(all(v["weight"] > 0 for v in values))
            self.assertTrue(all(set(v["environments"]) <= {"outdoor", "indoor", "space"} for v in values))

    def test_comments_weights_and_raw_bullets(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tables.md"
            path.write_text("## Weather\n- x3 [outdoor] [weather=rain] steady rain\n<!--\n- [outdoor] disabled\n-->\n", encoding="utf-8")
            result = scene.load_catalogue(path)["tables"][0]["values"]
            self.assertEqual(result, [{"text": "x3 [outdoor] [weather=rain] steady rain", "environments": ["outdoor"], "weight": 3}])

    def test_determinism_context_and_batch_diversity(self):
        for env in self.catalogue["environments"]:
            request = {"environment": env, "seed": 42, "count": 8}
            plans = scene.preview(request, self.catalogue)["plans"]
            self.assertEqual(plans, scene.preview(request, self.catalogue)["plans"])
            self.assertEqual(len({p["prompt"] for p in plans}), 8)
            for plan in plans:
                for name, raw in plan["traits"].items():
                    table = next(t for t in self.catalogue["tables"] if t["name"] == name)
                    value = next(v for v in table["values"] if v["text"] == raw)
                    self.assertIn(env, value["environments"])
                if env != "outdoor":
                    self.assertNotIn("Weather", plan["traits"])
                self.assertIn("camera is locked", plan["motionPrompt"])

    def test_pins_locks_and_blank_omissions(self):
        initial = scene.preview({"seed": 4}, self.catalogue)["plans"][0]
        request = {"seed": 20, "count": 3, "traits": initial["traits"], "locked": ["Palette"]}
        plans = scene.preview(request, self.catalogue)["plans"]
        self.assertEqual(plans[0]["traits"], initial["traits"])
        self.assertTrue(all(p["traits"]["Palette"] == initial["traits"]["Palette"] for p in plans))
        rerolled = scene.preview(dict(request, reroll=True), self.catalogue)["plans"][0]
        self.assertNotEqual(rerolled["traits"], initial["traits"])
        omitted = scene.preview({"traits": {"Weather": "", "Motion": ""}}, self.catalogue)["plans"][0]
        self.assertEqual(omitted["traits"]["Weather"], "")
        self.assertNotIn("Weather:", omitted["prompt"])

    def test_validation_and_incompatible_pins(self):
        for bad in ({"nonsense": 1}, {"count": 0}, {"seed": True}, {"width": 7},
                    {"traits": {"Palette": "invented"}}, {"locked": ["Palette"]},
                    {"environment": "underwater"}, {"reroll": "yes"}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                scene.preview(bad, self.catalogue)
        weather = next(v["text"] for t in self.catalogue["tables"] if t["name"] == "Weather" for v in t["values"])
        with self.assertRaises(ValueError):
            scene.preview({"environment": "space", "traits": {"Weather": weather}}, self.catalogue)

    def test_weather_and_motion_are_compatible_including_pinned_motion(self):
        rain_motion = next(v["text"] for t in self.catalogue["tables"] if t["name"] == "Motion" for v in t["values"] if "[weather=rain]" in v["text"])
        dry_weather = next(v["text"] for t in self.catalogue["tables"] if t["name"] == "Weather" for v in t["values"] if "[weather=dry]" in v["text"])
        with self.assertRaises(ValueError):
            scene.preview({"traits": {"Motion": rain_motion, "Weather": dry_weather}}, self.catalogue)
        for seed in range(30):
            p = scene.preview({"seed": seed, "traits": {"Motion": rain_motion}}, self.catalogue)["plans"][0]
            self.assertIn("[weather=rain]", p["traits"]["Weather"])
        with self.assertRaises(ValueError):
            scene.preview({"traits": {"Motion": rain_motion, "Weather": ""}}, self.catalogue)
        repaired = scene.preview({"traits": {"Motion": rain_motion, "Weather": dry_weather}, "reroll": True, "locked": []}, self.catalogue)
        self.assertEqual(len(repaired["plans"]), 1)
        with self.assertRaises(ValueError):
            scene.preview({"traits": {"Motion": rain_motion, "Weather": dry_weather}, "reroll": True, "locked": ["Motion", "Weather"]}, self.catalogue)

    def test_full_frame_and_topdown_prompts_and_exact_render_validation(self):
        p = scene.preview({"view": "topdown", "notes": "Two connected courtyards."}, self.catalogue)["plans"][0]
        self.assertIn("orthographic", p["prompt"])
        self.assertIn("gridless", p["prompt"].lower())
        self.assertIn("Two connected courtyards.", p["prompt"])
        self.assertNotIn("chat panel", p["prompt"])
        p["prompt"] = "An explicitly edited scene prompt."
        self.assertEqual(scene.validate_plans({"plans": [p]}, self.catalogue)[0]["prompt"], p["prompt"])
        with self.assertRaises(ValueError):
            scene.validate_plans({"plans": [dict(p, seed=-1)]}, self.catalogue)

    def test_graphs_connect_correct_models_dimensions_and_reference(self):
        p = scene.preview({"width": 1280, "height": 768, "seed": 123}, self.catalogue)["plans"][0]
        graph = scene.build_scene_graph(p, "test")
        sampler = next(n for n in graph.values() if n["class_type"] == "KSampler")
        self.assertEqual(sampler["inputs"]["seed"], 123)
        latent = graph[sampler["inputs"]["latent_image"][0]]["inputs"]
        self.assertEqual((latent["width"], latent["height"]), (1280, 768))
        self.assertEqual(graph[sampler["inputs"]["positive"][0]]["inputs"]["text"], p["prompt"])
        edit = scene.build_battlemap_graph("reference.png [input]", "edit scene", 99, 1024, 768, "map")
        encode = next(n for n in edit.values() if n["class_type"] == "TextEncodeQwenImageEditPlus" and n["inputs"].get("image1"))
        self.assertEqual(edit[encode["inputs"]["image1"][0]]["inputs"]["image"], "reference.png [input]")
        self.assertFalse(any(n["class_type"] in {"RMBG", "SaveAnimatedWEBP"} for n in edit.values()))
        self.assertTrue(any(n["class_type"] == "SaveImage" for n in edit.values()))

    def test_sidecars_preserve_identity_source_and_never_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "Original.png"
            source.write_bytes(b"original")
            p = scene.preview({"environment": "indoor", "seed": 5}, self.catalogue)["plans"][0]
            scene.write_sidecar(source, dict(p, kind="background"))
            meta = scene.battlemap_metadata(source, 1024, 768, 15, "Preserve both doorways.")
            self.assertEqual(meta["traits"], p["traits"])
            self.assertEqual(meta["environment"], "indoor")
            self.assertEqual(meta["source"]["path"], str(source.resolve()))
            self.assertAlmostEqual(meta["source"]["mtime"], source.stat().st_mtime_ns / 1000000)
            self.assertIn("Preserve both doorways.", meta["prompt"])
            a = scene.save_result(folder, "Original Battlemap", b"image-a", meta)
            b = scene.save_result(folder, "Original Battlemap", b"image-b", meta)
            self.assertNotEqual(a, b)
            self.assertEqual(source.read_bytes(), b"original")
            self.assertEqual(json.loads(a.with_suffix(".background.json").read_text())["kind"], "battlemap")

    def test_cli_preview_and_errors_are_machine_readable(self):
        cmd = [sys.executable, str(ROOT / "generate-background.py"), "--preview", "--request-stdin"]
        result = subprocess.run(cmd, input='{"seed":77,"environment":"space"}', text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["plans"][0]["seed"], 77)
        bad = subprocess.run(cmd, input='{"count":0}', text=True, capture_output=True)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("count", bad.stderr)

    def test_requested_layers_and_bounds_and_required_location(self):
        names = {t["name"] for t in self.catalogue["tables"]}
        self.assertTrue({"Foreground", "Distant features", "Terrain or floor", "Sky", "Time", "Faction presence", "Condition", "Atmosphere"} <= names)
        for bad in ({"count": 9}, {"seed": 2**32}, {"traits": {"Outdoor location": ""}}):
            with self.assertRaises(ValueError):
                scene.preview(bad, self.catalogue)
        p = scene.preview({"width": 64, "height": 8192, "seed": 2**32 - 1}, self.catalogue)["plans"][0]
        self.assertEqual((p["width"], p["height"]), (64, 8192))

    def test_temporal_lighting_constraints_and_sky_exclusion_on_maps(self):
        daytime = next(v["text"] for t in self.catalogue["tables"] if t["name"] == "Time" for v in t["values"] if "[outdoor]" in v["text"] and "[time=day]" in v["text"])
        nightlight = next(v["text"] for t in self.catalogue["tables"] if t["name"] == "Lighting" for v in t["values"] if "[outdoor]" in v["text"] and "[time=night]" in v["text"])
        with self.assertRaises(ValueError):
            scene.preview({"traits": {"Time": daytime, "Lighting": nightlight}}, self.catalogue)
        p = scene.preview({"traits": {"Lighting": nightlight}, "view": "topdown"}, self.catalogue)["plans"][0]
        self.assertIn("[time=night]", p["traits"]["Time"])
        self.assertNotIn("Sky:", p["prompt"])
        self.assertNotIn("Distant features:", p["prompt"])
        self.assertNotIn("Visible scene elements for later animation:", p["prompt"])

    def test_render_rejects_missing_location_and_incomplete_json(self):
        p = scene.preview({}, self.catalogue)["plans"][0]
        del p["traits"]["Outdoor location"]
        with self.assertRaises(ValueError):
            scene.validate_plans({"plans": [p]}, self.catalogue)

    def test_blank_seed_randomizes_preview_but_render_requires_concrete_seed(self):
        p = scene.preview({"seed": None}, self.catalogue)["plans"][0]
        self.assertIs(type(p["seed"]), int)
        self.assertTrue(0 <= p["seed"] <= 2**32 - 1)
        p["seed"] = None
        with self.assertRaises(ValueError):
            scene.validate_plans({"plans": [p]}, self.catalogue)

    def test_real_cli_render_and_battlemap_protocol_against_comfy_boundary(self):
        state = {"graphs": [], "uploads": 0, "bad_image": False}
        png = b"\x89PNG\r\n\x1a\n" + b"fake pixels for boundary test"

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def reply(self, body, content_type="application/json"):
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.end_headers()
                self.wfile.write(body if isinstance(body, bytes) else json.dumps(body).encode())

            def do_GET(self):
                if self.path == "/system_stats":
                    self.reply({})
                elif self.path.startswith("/history/"):
                    graph = state["graphs"][-1]
                    save = next(k for k, n in graph.items() if n["class_type"] == "SaveImage")
                    self.reply({"test-job": {"status": {"completed": True}, "outputs": {save: {"images": [{"filename": "render.png", "subfolder": "test", "type": "output"}]}}}})
                elif self.path.startswith("/view?"):
                    self.reply(b"not a png" if state["bad_image"] else png, "image/png")

            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"]))
                if self.path == "/prompt":
                    state["graphs"].append(json.loads(body)["prompt"])
                    self.reply({"prompt_id": "test-job"})
                elif self.path == "/upload/image":
                    state["uploads"] += 1
                    self.reply({"name": "source.png", "subfolder": "boundary", "type": "input"})

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            with tempfile.TemporaryDirectory() as folder:
                common = [sys.executable, str(ROOT / "generate-background.py"), "--server", f"127.0.0.1:{server.server_port}", "--output-dir", folder]
                plan = scene.preview({"environment": "indoor", "seed": 71}, self.catalogue)["plans"][0]
                plan["prompt"] = "A precise user-edited reference scene."
                rendered = subprocess.run(common + ["--render", "--request-stdin"], input=json.dumps({"plans": [plan]}), text=True, capture_output=True)
                self.assertEqual(rendered.returncode, 0, rendered.stderr)
                source = Path(json.loads(rendered.stdout.removeprefix("BACKGROUND_RESULT "))["path"])
                self.assertEqual(source.read_bytes(), png)
                metadata = json.loads(source.with_suffix(".background.json").read_text())
                self.assertEqual(metadata["prompt"], "A precise user-edited reference scene.")
                mapped = subprocess.run(common + ["--battlemap", str(source), "--width", "1024", "--height", "768"], text=True, capture_output=True)
                self.assertEqual(mapped.returncode, 0, mapped.stderr)
                destination = Path(json.loads(mapped.stdout.removeprefix("BACKGROUND_RESULT "))["path"])
                self.assertIn(" Battlemap-", destination.name)
                self.assertEqual(state["uploads"], 1)
                self.assertEqual(json.loads(destination.with_suffix(".background.json").read_text())["traits"], plan["traits"])
                self.assertEqual(source.read_bytes(), png)
                state["bad_image"] = True
                failed = subprocess.run(common + ["--render", "--request-stdin"], input=json.dumps({"plans": [plan]}), text=True, capture_output=True)
                self.assertNotEqual(failed.returncode, 0)
                self.assertNotIn("BACKGROUND_RESULT", failed.stdout)
                self.assertEqual(len(list(Path(folder).glob("*.png"))), 2)
        finally:
            server.shutdown()
            server.server_close()
            worker.join()

    def test_battlemap_uses_compact_identity_without_source_camera_or_sky(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.png"
            source.write_bytes(b"reference")
            plan = scene.preview({"seed": 1}, self.catalogue)["plans"][0]
            plan["prompt"] = "Wide cinematic view, camera near ground level looking toward a distant skyline."
            scene.write_sidecar(source, dict(plan, kind="background"))
            result = scene.battlemap_metadata(source, 768, 768, 4, "Two connected rooms.")
            for text in ("Wide cinematic", "near ground level", "distant skyline", "Sky:", "Distant features:", "Layout:", "Motion:", "Scene identity:", "Architecture:"):
                self.assertNotIn(text, result["prompt"])
            self.assertIn("walls as solid dark cross-section outlines", result["prompt"])
            self.assertIn("floor", result["prompt"])
            self.assertEqual(result["traits"], plan["traits"])


if __name__ == "__main__":
    unittest.main()
