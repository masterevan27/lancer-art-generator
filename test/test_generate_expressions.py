import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from test.helpers import load_expressions
from test.workflow_schema import expected_inputs, object_info, server_is_up


REPO = Path(__file__).resolve().parent.parent
WORKFLOW = REPO / "workflows" / "api" / "Util_Expression_QwenEdit_RMBG_v1.json"
TABLE_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "expression-tables.md"
GROUP_TABLE_FIXTURE = (Path(__file__).resolve().parent / "fixtures" /
                       "expression-groups.md")
LIVE_TABLES = REPO / "prompts" / "expression-tables.md"
expressions = load_expressions()


def only(graph, class_type):
    found = [(node_id, node) for node_id, node in graph.items()
             if node["class_type"] == class_type]
    assert len(found) == 1, "%s appears %d times" % (class_type, len(found))
    return found[0]


class TestLabels(unittest.TestCase):
    def test_custom_labels_are_safe_for_flat_sprite_filenames(self):
        self.assertEqual(expressions.sanitize_label("  Happy / Now!  "),
                         "happy_now")
        with self.assertRaisesRegex(ValueError, "empty"):
            expressions.sanitize_label(" / ! ")

    def test_custom_prompt_text_is_optional(self):
        self.assertEqual(
            expressions.parse_custom_specs(["Battle Focus=grim resolve",
                                            "quiet awe"]),
            {"battle_focus": "grim resolve", "quiet_awe": None})

    def test_all_and_comma_selections_keep_the_declared_order(self):
        tables = {"joy": ["joyful"], "my_custom": ["custom"]}
        labels, full = expressions.select_labels(
            "all", True, {"my_custom": None}, tables)
        self.assertEqual(labels, expressions.DEFAULT_LABELS + ("my_custom",))
        self.assertTrue(full)

        labels, full = expressions.select_labels(
            "joy,anger", True, {}, tables)
        self.assertEqual(labels, ("joy", "anger"))
        self.assertFalse(full)

    def test_custom_only_run_does_not_implicitly_generate_all_defaults(self):
        labels, full = expressions.select_labels(
            "all", False, {"battle_focus": "cold concentration"}, {})
        self.assertEqual(labels, ("battle_focus",))
        self.assertFalse(full)

    def test_unknown_label_needs_a_custom_definition_or_table(self):
        with self.assertRaisesRegex(ValueError, "unknown expression"):
            expressions.select_labels("joy,not_real", True, {}, {})
        labels, _ = expressions.select_labels(
            "table_only", True, {}, {"table_only": ["focused"]})
        self.assertEqual(labels, ("table_only",))

    def test_file_names_are_classified_without_accepting_paths(self):
        self.assertEqual(expressions.classify_sprite_name("joy.webp"), "joy")
        self.assertEqual(expressions.classify_sprite_name("joy-12.webp"), "joy")
        self.assertEqual(expressions.classify_sprite_name("joy.expressive.webp"),
                         "joy")
        for name in ("../joy.webp", "Joy.webp", "joy.png", "joy-.webp"):
            with self.subTest(name=name):
                self.assertIsNone(expressions.classify_sprite_name(name))


class TestArgumentsAndSources(unittest.TestCase):
    def test_exactly_one_input_mode_is_required(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaisesRegex(SystemExit, "2"):
                expressions.parse_args([])
            with self.assertRaisesRegex(SystemExit, "2"):
                expressions.parse_args(["--image", "x.png", "--id", "npc-1"])

    def test_image_mode_default_output_is_beside_the_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "Hero.png"
            image.write_bytes(b"png")
            args = expressions.parse_args(["--image", str(image), "-e", "joy"])
            jobs = expressions.resolve_sources(args)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].name, "Hero")
        self.assertEqual(jobs[0].output_dir, image.parent / "Hero-expressions")
        self.assertEqual(jobs[0].source_kind, "image")

    def test_source_accepts_only_npc_token_or_portrait(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "Hero.png"
            image.write_bytes(b"png")
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaisesRegex(SystemExit, "2"):
                    expressions.parse_args([
                        "--image", str(image), "--source", "token"])
                with self.assertRaisesRegex(SystemExit, "2"):
                    expressions.parse_args([
                        "--manifest", str(Path(tmp) / "manifest.json"),
                        "--source", "bust"])

    def test_default_source_is_token_first_then_portrait(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "Pilot"
            folder.mkdir()
            token = folder / "custom-token.png"
            portrait = folder / "custom-portrait.png"
            token.write_bytes(b"token")
            portrait.write_bytes(b"portrait")
            manifest = root / "manifest.json"
            entry = {
                "id": "pilot-1", "name": "Pilot", "traits": {},
                "token": token.name, "portrait": portrait.name,
            }
            manifest.write_text(json.dumps({str(folder): entry}),
                                encoding="utf-8")

            default_args = expressions.parse_args([
                "--manifest", str(manifest), "--id", "pilot-1"])
            default_job = expressions.resolve_sources(default_args)[0]
            portrait_args = expressions.parse_args([
                "--manifest", str(manifest), "--id", "pilot-1",
                "--source", "portrait"])
            portrait_job = expressions.resolve_sources(portrait_args)[0]

            token.unlink()
            fallback_job = expressions.resolve_sources(default_args)[0]

        self.assertEqual((default_job.image, default_job.source_kind),
                         (token, "token"))
        self.assertEqual((portrait_job.image, portrait_job.source_kind),
                         (portrait, "portrait"))
        self.assertEqual((fallback_job.image, fallback_job.source_kind),
                         (portrait, "portrait"))

    def test_absent_manifest_filenames_use_canonical_compatibility_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "Pilot"
            folder.mkdir()
            canonical = folder / "Pilot Token.png"
            canonical.write_bytes(b"token")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({str(folder): {
                "id": "pilot-1", "name": "Pilot", "traits": {},
            }}), encoding="utf-8")
            args = expressions.parse_args([
                "--manifest", str(manifest), "--id", "pilot-1"])
            job = expressions.resolve_sources(args)[0]

        self.assertEqual(job.image, canonical)
        self.assertEqual(job.source_kind, "token")

    def test_explicit_unavailable_source_fails_without_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "Pilot"
            folder.mkdir()
            (folder / "Pilot Portrait.png").write_bytes(b"portrait")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({str(folder): {
                "id": "pilot-1", "name": "Pilot", "traits": {},
            }}), encoding="utf-8")
            args = expressions.parse_args([
                "--manifest", str(manifest), "--id", "pilot-1",
                "--source", "token"])
            with self.assertRaisesRegex(ValueError, "token.*not found"):
                expressions.resolve_sources(args)

            (folder / "Pilot Portrait.png").unlink()
            (folder / "Pilot Token.png").write_bytes(b"token")
            args = expressions.parse_args([
                "--manifest", str(manifest), "--id", "pilot-1",
                "--source", "portrait"])
            with self.assertRaisesRegex(ValueError, "portrait.*not found"):
                expressions.resolve_sources(args)

    def test_null_manifest_source_is_unavailable_not_an_unsafe_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "Pilot"
            folder.mkdir()
            portrait = folder / "custom-portrait.png"
            portrait.write_bytes(b"portrait")
            manifest = root / "manifest.json"
            entry = {
                "id": "pilot-1", "name": "Pilot", "traits": {},
                "token": None, "portrait": portrait.name,
            }
            manifest.write_text(json.dumps({str(folder): entry}),
                                encoding="utf-8")

            default_args = expressions.parse_args([
                "--manifest", str(manifest), "--id", "pilot-1"])
            fallback = expressions.resolve_sources(default_args)[0]
            token_args = expressions.parse_args([
                "--manifest", str(manifest), "--id", "pilot-1",
                "--source", "token"])
            with self.assertRaisesRegex(ValueError, "token.*not found"):
                expressions.resolve_sources(token_args)

            token = folder / "custom-token.png"
            token.write_bytes(b"token")
            entry.update({"token": token.name, "portrait": None})
            manifest.write_text(json.dumps({str(folder): entry}),
                                encoding="utf-8")
            token_only = expressions.resolve_sources(default_args)[0]
            portrait_args = expressions.parse_args([
                "--manifest", str(manifest), "--id", "pilot-1",
                "--source", "portrait"])
            with self.assertRaisesRegex(ValueError, "portrait.*not found"):
                expressions.resolve_sources(portrait_args)

        self.assertEqual((fallback.image, fallback.source_kind),
                         (portrait, "portrait"))
        self.assertEqual((token_only.image, token_only.source_kind),
                         (token, "token"))

    def test_manifest_source_paths_must_stay_inside_the_real_npc_folder(self):
        unsafe_values = ("../outside.png",)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "Pilot"
            folder.mkdir()
            outside = root / "outside.png"
            outside.write_bytes(b"outside")
            unsafe_values += (str(outside.resolve()),)
            link = folder / "linked.png"
            try:
                link.symlink_to(outside)
            except OSError:
                link = None
            manifest = root / "manifest.json"

            for value in unsafe_values + ((link.name,) if link else ()):
                with self.subTest(value=value):
                    manifest.write_text(json.dumps({str(folder): {
                        "id": "pilot-1", "name": "Pilot", "traits": {},
                        "token": value,
                        "portrait": "Pilot Portrait.png",
                    }}), encoding="utf-8")
                    (folder / "Pilot Portrait.png").write_bytes(b"portrait")
                    args = expressions.parse_args([
                        "--manifest", str(manifest), "--id", "pilot-1"])
                    with self.assertRaisesRegex(ValueError, "unsafe token"):
                        expressions.resolve_sources(args)

    def test_image_mode_input_is_not_constrained_to_an_npc_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "elsewhere" / "Hero.png"
            image.parent.mkdir()
            image.write_bytes(b"png")
            args = expressions.parse_args(["--image", str(image)])
            self.assertEqual(expressions.resolve_sources(args)[0].image,
                             image.resolve())

    def test_attached_short_expression_value_is_an_explicit_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "Hero.png"
            image.write_bytes(b"png")
            args = expressions.parse_args([
                "--image", str(image), "-ejoy", "--custom", "battle=x"])
        custom = expressions.parse_custom_specs(args.custom)
        labels, full = expressions.select_labels(
            args.expressions, args.expressions_explicit, custom, {})
        self.assertEqual(labels, ("joy", "battle"))
        self.assertFalse(full)

    def test_attached_short_expression_value_conflicts_with_file_redo(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "Hero.png"
            image.write_bytes(b"png")
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaisesRegex(SystemExit, "2"):
                    expressions.parse_args([
                        "--image", str(image), "--file", "joy.webp", "-ejoy"])

    def test_npc_selection_and_portrait_resolution_follow_the_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alpha = root / "Crew" / "Alpha"
            beta = root / "Pilots" / "Beta"
            alpha.mkdir(parents=True)
            beta.mkdir(parents=True)
            (alpha / "Alpha Portrait.png").write_bytes(b"a")
            (beta / "Beta Portrait.png").write_bytes(b"b")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                str(beta): {"id": "b", "name": "Beta", "callsign": "B",
                            "traits": {}},
                str(alpha): {"id": "a", "name": "Alpha", "callsign": "A",
                             "traits": {"Hair": "short"}},
            }), encoding="utf-8")
            args = expressions.parse_args([
                "--manifest", str(manifest), "--filter", "Crew", "--limit", "1"])
            jobs = expressions.resolve_sources(args)
        self.assertEqual([job.name for job in jobs], ["Alpha"])
        self.assertEqual(jobs[0].image, alpha / "Alpha Portrait.png")
        self.assertEqual(jobs[0].output_dir, alpha / "expressions")

    def test_npc_source_extracts_only_saved_portrait_style_clauses(self):
        original = (
            "A half-body character portrait of a pilot, rendered in a loose "
            "charcoal illustration style with rough crosshatching, soft side "
            "lighting. Her face carries a permanent scowl. She sits in a "
            "cockpit. Shallow depth of field, square framing, high detail, "
            "atmospheric sci-fi character portrait, painterly brushwork with "
            "violet grain in every shadow.")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "Pilot"
            folder.mkdir()
            (folder / "Pilot Portrait.png").write_bytes(b"portrait")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({str(folder): {
                "id": "pilot-1", "name": "Pilot", "traits": {
                    "Hair": "silver crop", "Demeanor": "permanent scowl",
                    "Stance": "arms crossed", "Backdrop": "cockpit",
                },
                "portraitPrompt": original,
                "tokenPrompt": "rendered in an unrelated glossy token style.",
            }}), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = expressions.main([
                    "--manifest", str(manifest), "--id", "pilot-1",
                    "--tables", str(TABLE_FIXTURE), "-e", "joy",
                    "--seed", "1", "--dry-run",
                ])

        rendered = output.getvalue()
        self.assertEqual(code, 0)
        self.assertIn(
            "rendered in a loose charcoal illustration style with rough "
            "crosshatching, soft side lighting.", rendered)
        self.assertIn(
            "painterly brushwork with violet grain in every shadow.", rendered)
        self.assertIn("silver crop", rendered)
        self.assertIn("Expression: joyful", rendered)
        for excluded in ("permanent scowl", "She sits in a cockpit",
                         "square framing", "Shallow depth of field",
                         "arms crossed", "unrelated glossy token style"):
            with self.subTest(excluded=excluded):
                self.assertNotIn(excluded, rendered)

    def test_missing_non_string_and_unrecognized_portrait_styles_fall_back(self):
        prompts = (
            None,
            ["not", "a", "string"],
            "A portrait whose backdrop mentions painterly brushwork in a mural.",
            "Rendered in anime style, but not from the generator template.",
        )
        for portrait_prompt in prompts:
            with self.subTest(portrait_prompt=portrait_prompt):
                self.assertEqual(
                    expressions.extract_portrait_style(portrait_prompt), "")

    def test_token_source_uses_only_the_saved_token_style_clauses(self):
        original = (
            "A full-body character illustration of a pilot, rendered in a "
            "bold ink illustration style with dry brush texture. They are "
            "facing the viewer with arms crossed. Behind them the background "
            "is white. Full-length wide shot, centered composition, dramatic "
            "lighting, high detail, isolated character illustration, clean "
            "silhouette, painterly brushwork with copper grain in every "
            "shadow.")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "Pilot"
            folder.mkdir()
            (folder / "Pilot Token.png").write_bytes(b"token")
            (folder / "Pilot Portrait.png").write_bytes(b"portrait")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({str(folder): {
                "id": "pilot-1", "name": "Pilot", "traits": {},
                "tokenPrompt": original,
                "portraitPrompt": "A half-body character portrait of a pilot, "
                                  "rendered in an unrelated oil style.",
            }}), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = expressions.main([
                    "--manifest", str(manifest), "--id", "pilot-1",
                    "--tables", str(TABLE_FIXTURE), "-e", "joy",
                    "--seed", "1", "--dry-run",
                ])

        rendered = output.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("bold ink illustration style with dry brush texture",
                      rendered)
        self.assertIn("painterly brushwork with copper grain", rendered)
        for excluded in ("arms crossed", "background is white",
                         "Full-length wide shot", "centered composition",
                         "unrelated oil style"):
            with self.subTest(excluded=excluded):
                self.assertNotIn(excluded, rendered)

    def test_main_records_the_actual_fallback_source_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "Pilot"
            folder.mkdir()
            (folder / "Pilot Portrait.png").write_bytes(b"portrait")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({str(folder): {
                "id": "pilot-1", "name": "Pilot", "traits": {},
            }}), encoding="utf-8")
            originals = (expressions.art.find_server,
                         expressions.upload_image,
                         expressions.render_sprite)
            expressions.art.find_server = lambda _server: object()
            expressions.upload_image = lambda _comfy, _path: "uploaded"
            expressions.render_sprite = (
                lambda _comfy, _ref, _args, _plan, _slug: b"webp")
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    code = expressions.main([
                        "--manifest", str(manifest), "--id", "pilot-1",
                        "--tables", str(TABLE_FIXTURE), "-e", "joy",
                    ])
            finally:
                (expressions.art.find_server,
                 expressions.upload_image,
                 expressions.render_sprite) = originals
            metadata = json.loads(
                (folder / "expressions" / "expressions.json").read_text(
                    encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(metadata["joy.webp"]["source"]["kind"], "portrait")

    def test_file_rejects_multi_sprite_options_and_missing_classified_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "p.png"
            image.write_bytes(b"p")
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaisesRegex(SystemExit, "2"):
                    expressions.parse_args([
                        "--image", str(image), "--file", "joy.webp",
                        "--count", "2"])
            args = expressions.parse_args([
                "--image", str(image), "--file", "joy.webp"])
            with self.assertRaisesRegex(ValueError, "existing"):
                expressions.make_plans(
                    Path(tmp) / "out", args, {}, {}, None)


class TestTablesAndPrompts(unittest.TestCase):
    def test_parser_reuses_weight_heading_and_disabled_bullet_semantics(self):
        tables = expressions.load_expression_tables(TABLE_FIXTURE)
        self.assertEqual(tables["joy"], [
            "joyful bright grin", "joyful bright grin",
            "joyful eyes crinkled with delight"])
        self.assertEqual(tables["anger"], ["angry clenched jaw"])
        self.assertNotIn("disabled", " ".join(tables["joy"]))

    def test_group_references_roll_weighted_members_without_raw_markers(self):
        tables = expressions.load_expression_tables(GROUP_TABLE_FIXTURE)
        self.assertEqual(tables["joyful_smiles"], [
            "joyful smile with raised cheeks",
            "joyful smile with raised cheeks",
            "joyful smile with raised cheeks",
            "joyful bright eyes",
        ])
        with tempfile.TemporaryDirectory() as tmp:
            args = SimpleNamespace(
                count=1, seed=0, replace=False, file=None,
                keep_background=False, describe=None)
            first, _ = expressions.make_plans(
                Path(tmp), args, tables, {}, (("joy",), False))
            args.seed = 1
            second, _ = expressions.make_plans(
                Path(tmp), args, tables, {}, (("joy",), False))
        self.assertIn("Expression: joyful bright eyes", first[0].prompt)
        self.assertIn(
            "Expression: joyful smile with raised cheeks", second[0].prompt)
        self.assertNotIn("=>", first[0].prompt + second[0].prompt)
        self.assertNotIn("disabled", " ".join(tables["joyful_smiles"]))

    def test_missing_group_target_is_rejected_while_loading_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.md"
            path.write_text("## joy\n\n- => Missing smiles\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Missing smiles"):
                expressions.load_expression_tables(path)

    def test_malformed_group_target_reports_file_and_reference_before_rendering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "Hero.png"
            image.write_bytes(b"not rendered")
            tables = root / "broken-expressions.md"
            tables.write_text("## joy\n\n- => !!!\n", encoding="utf-8")
            error = io.StringIO()
            with contextlib.redirect_stderr(error):
                code = expressions.main([
                    "--image", str(image), "--tables", str(tables),
                ])

            self.assertEqual(code, 2)
            self.assertIn(str(tables), error.getvalue())
            self.assertIn("=> !!!", error.getvalue())
            self.assertIn("group reference", error.getvalue())

    def test_prompt_is_anchored_to_appearance_but_not_demeanor_or_gear(self):
        prompt = expressions.assemble_prompt("joyful open smile", {
            "Hair": "cropped curls", "Hair colour": "silver",
            "Feature": "a cheek scar", "Outfit": "a red flight suit",
            "Headgear": "a black cap", "Demeanor": "permanent scowl",
            "Weapon": "rifle", "Gear": "scanner", "Backdrop": "hangar",
            "Stance": "arms crossed",
        })
        for text in ("cropped curls", "silver", "cheek scar",
                     "red flight suit", "black cap", "joyful open smile"):
            self.assertIn(text, prompt)
        for text in ("permanent scowl", "rifle", "scanner", "hangar",
                     "arms crossed"):
            self.assertNotIn(text, prompt)
        lowered = prompt.lower()
        for text in ("same character", "face", "hair", "outfit", "colours",
                     "accessories", "art style", "natural",
                     "full-body", "entire head", "hands", "both feet",
                     "margin", "no cropping or text", "unseen clothing",
                     "legs", "stance", "shoulders", "arms", "hand gestures"):
            with self.subTest(text=text):
                self.assertIn(text, lowered)
        self.assertNotIn("standing", lowered)
        self.assertNotIn("small body language", lowered)
        self.assertNotIn("camera framing and pose", lowered)
        self.assertNotIn("front-facing bust", lowered)

    def test_image_mode_prompt_has_no_trait_anchor_section(self):
        prompt = expressions.assemble_prompt("angry narrowed eyes")
        self.assertEqual(prompt.count("angry narrowed eyes"), 1)
        self.assertNotIn("Appearance anchors", prompt)
        for text in ("rendering medium", "linework", "brushwork",
                     "texture and grain", "shading", "colour palette",
                     "contrast", "detail level", "stylized proportions",
                     "newly invented full-body areas"):
            with self.subTest(text=text):
                self.assertIn(text, prompt)
        self.assertNotIn("painterly", prompt.lower())
        self.assertNotIn("halftone", prompt.lower())

    def test_default_expressions_supply_distinct_emotion_specific_body_language(self):
        tables = expressions.load_expression_tables(LIVE_TABLES)
        for label in expressions.DEFAULT_LABELS:
            with self.subTest(label=label, requirement="pose cue"):
                self.assertTrue(all("; " in bullet for bullet in tables[label]))
        expected = {
            "joy": "open welcoming arms",
            "pride": "lifted chin and confident posture",
            "sadness": "lowered shoulders and loosely clasped hands",
            "fear": "guarded hands and a recoiling weight shift",
        }
        for label, pose in expected.items():
            with self.subTest(label=label):
                self.assertTrue(all(pose in bullet for bullet in tables[label]))

    def test_describe_keeps_explicit_custom_pose_instructions(self):
        prompt = expressions.assemble_prompt(
            "quiet wonder while kneeling, left hand reaching toward the light")
        self.assertIn("while kneeling", prompt)
        self.assertIn("left hand reaching toward the light", prompt)

    def test_live_tables_cover_every_default_with_distinct_weighted_options(self):
        tables = expressions.load_expression_tables(LIVE_TABLES)
        self.assertEqual(tuple(tables), expressions.DEFAULT_LABELS)
        for label in expressions.DEFAULT_LABELS:
            distinct = set(tables[label])
            with self.subTest(label=label):
                self.assertGreaterEqual(len(distinct), 4)
                self.assertLessEqual(len(distinct), 6)
                self.assertTrue(all(label in bullet.lower() for bullet in distinct))


class TestPlanning(unittest.TestCase):
    def args(self, **overrides):
        values = dict(count=1, seed=10, replace=False, file=None,
                      keep_background=False, describe=None)
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_add_mode_takes_the_lowest_free_variant_including_gaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            for name in ("joy.webp", "joy-2.webp", "joy.expressive.webp"):
                (out / name).write_bytes(name.encode())
            plans, skipped = expressions.make_plans(
                out, self.args(count=2), {"joy": ["joyful"]}, {},
                (("joy",), False))
        self.assertEqual([p.destination.name for p in plans],
                         ["joy-1.webp", "joy-3.webp"])
        self.assertEqual(skipped, [])
        self.assertEqual([p.seed for p in plans], [10, 11])

    def test_full_all_run_skips_a_label_with_any_variant(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "joy.expressive.webp").write_bytes(b"old")
            plans, skipped = expressions.make_plans(
                out, self.args(), {"joy": ["joyful"], "anger": ["angry"]},
                {}, (("joy", "anger"), True))
        self.assertEqual([p.label for p in plans], ["anger"])
        self.assertEqual(skipped, [("joy", 1)])

    def test_replace_plans_start_from_the_base_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            plans, _ = expressions.make_plans(
                Path(tmp), self.args(count=2, replace=True),
                {"joy": ["joyful"]}, {}, (("joy",), False))
        self.assertEqual([p.destination.name for p in plans],
                         ["joy.webp", "joy-1.webp"])
        self.assertTrue(plans[0].replace_label)
        self.assertFalse(plans[1].replace_label)

    def test_file_redo_uses_saved_full_prompt_for_tableless_custom_sprite(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "battle_focus.webp").write_bytes(b"old")
            sidecar = {"battle_focus.webp": {
                "label": "battle_focus", "prompt": "saved full custom prompt",
                "seed": 1}}
            plans, _ = expressions.make_plans(
                out, self.args(file="battle_focus.webp"), {}, {}, None, sidecar)
        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0].destination.name, "battle_focus.webp")
        self.assertEqual(plans[0].prompt, "saved full custom prompt")

    def test_file_redo_prefers_saved_authored_prompt_over_builtin_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "joy.webp").write_bytes(b"old")
            saved = "authored joy prompt with a one-handed celebratory pose"
            sidecar = {"joy.webp": {"label": "joy", "prompt": saved,
                                      "seed": 1}}
            plans, _ = expressions.make_plans(
                out, self.args(file="joy.webp"),
                {"joy": ["stock joyful smile with both arms lowered"]}, {},
                None, sidecar)

        self.assertEqual(plans[0].prompt, saved)
        self.assertNotIn("stock joyful smile", plans[0].prompt)

    def test_file_redo_describe_overrides_saved_builtin_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "joy.webp").write_bytes(b"old")
            sidecar = {"joy.webp": {
                "label": "joy", "prompt": "saved authored joy prompt",
                "seed": 1}}
            plans, _ = expressions.make_plans(
                out, self.args(file="joy.webp", describe=(
                    "quiet joy while kneeling with one hand raised")),
                {"joy": ["stock joyful smile"]}, {}, None, sidecar)

        self.assertIn("quiet joy while kneeling with one hand raised",
                      plans[0].prompt)
        self.assertNotIn("saved authored joy prompt", plans[0].prompt)
        self.assertNotIn("stock joyful smile", plans[0].prompt)

    def test_file_redo_adapts_recognized_prompts_and_replaces_source_style(self):
        legacy = (
            "Keep the same character, face, hairstyle, outfit, colours, art "
            "style, camera framing and pose. Change only the facial expression "
            "and small body language. Front-facing bust, no text.")
        suffix = (
            " Appearance anchors: Hair: cropped curls; Outfit: red flight "
            "suit. Expression: cold focused determination")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            for name in ("legacy.webp", "current.webp", "authored.webp"):
                (out / name).write_bytes(b"old")
            sidecar = {
                "legacy.webp": {"prompt": legacy + suffix},
                "current.webp": {
                    "prompt": expressions.PRIOR_FULL_BODY_IDENTITY_PREAMBLE +
                              " " + expressions.STYLE_MATCH_INSTRUCTION +
                              " Original portrait style: rendered in old oil."
                              + suffix},
                "authored.webp": {
                    "prompt": "Keep this custom camera framing exactly."},
            }
            prompts = {}
            for name in sidecar:
                plans, _ = expressions.make_plans(
                    out, self.args(file=name), {}, {}, None, sidecar,
                    style_prompt="rendered in new ink.")
                prompts[name] = plans[0].prompt

        upgraded = (expressions.IDENTITY_PREAMBLE + suffix + " " +
                    expressions.STYLE_MATCH_INSTRUCTION + " " +
                    "Original source style: rendered in new ink.")
        self.assertEqual(prompts["legacy.webp"], upgraded)
        self.assertNotIn("camera framing and pose", prompts["legacy.webp"])
        self.assertNotIn("Front-facing bust", prompts["legacy.webp"])
        self.assertIn("Hair: cropped curls", prompts["legacy.webp"])
        self.assertIn("cold focused determination", prompts["legacy.webp"])
        self.assertEqual(prompts["current.webp"], upgraded)
        self.assertNotIn("old oil", prompts["current.webp"])
        self.assertEqual(prompts["current.webp"].count(
            expressions.IDENTITY_PREAMBLE), 1)
        self.assertEqual(prompts["authored.webp"],
                         "Keep this custom camera framing exactly.")

    def test_style_context_reaches_custom_describe_and_generated_file_redo(self):
        style = "rendered in ink with rough hatching. painterly brushwork."
        traits = {"Hair": "silver crop"}
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            custom, _ = expressions.make_plans(
                out, self.args(), {}, traits, (("battle",), False),
                custom={"battle": "cold determination"}, style_prompt=style)
            described, _ = expressions.make_plans(
                out, self.args(describe="quiet wonder"), {}, traits,
                (("joy",), False), style_prompt=style)
            (out / "battle.webp").write_bytes(b"old")
            saved_prompt = (
                expressions.IDENTITY_PREAMBLE +
                " Appearance anchors: Hair: silver crop. "
                "Expression: cold determination")
            redone, _ = expressions.make_plans(
                out, self.args(file="battle.webp"), {}, traits, None,
                {"battle.webp": {"prompt": saved_prompt}},
                style_prompt=style)

        for prompt, expression in (
                (custom[0].prompt, "cold determination"),
                (described[0].prompt, "quiet wonder"),
                (redone[0].prompt, "cold determination")):
            with self.subTest(expression=expression):
                self.assertIn("Original source style: " + style, prompt)
                self.assertIn("silver crop", prompt)
                self.assertIn(expression, prompt)
        self.assertEqual(redone[0].prompt.count("Original source style:"), 1)

        already_styled = redone[0].prompt
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "battle.webp").write_bytes(b"old")
            plans, _ = expressions.make_plans(
                out, self.args(file="battle.webp"), {}, traits, None,
                {"battle.webp": {"prompt": already_styled}},
                style_prompt=style)
        self.assertEqual(plans[0].prompt.count("Original source style:"), 1)

    def test_selected_pool_is_validated_before_any_plan_is_returned(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "no prompt"):
                expressions.make_plans(
                    Path(tmp), self.args(), {}, {}, (("joy",), False))


class TestPersistence(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.out = Path(self.temp.name)
        self.source = self.out / "portrait.png"
        self.source.write_bytes(b"portrait")
        self.sidecar_path = self.out / "expressions.json"
        self.old_meta = {}
        for name in ("joy.webp", "joy-1.webp", "joy.expressive.webp",
                     "anger.webp"):
            (self.out / name).write_bytes(("old-" + name).encode())
            self.old_meta[name] = {"label": name.split(".")[0].split("-")[0],
                                   "prompt": "old", "seed": 1}
        self.sidecar_path.write_text(json.dumps(self.old_meta, sort_keys=True),
                                     encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def plans(self, replace=True):
        args = SimpleNamespace(count=2, seed=20, replace=replace, file=None,
                               keep_background=False, describe=None)
        return expressions.make_plans(
            self.out, args, {"joy": ["joyful"]}, {},
            (("joy",), False), self.old_meta)[0]

    def test_failed_first_replace_preserves_all_files_and_sidecar_bytes(self):
        before_files = {p.name: p.read_bytes() for p in self.out.glob("*.webp")}
        before_sidecar = self.sidecar_path.read_bytes()

        def fail(_plan):
            raise RuntimeError("render failed")

        result = expressions.execute_plans(
            self.plans(), fail, self.sidecar_path, self.source)
        self.assertEqual(result.failed, 2)
        self.assertEqual({p.name: p.read_bytes() for p in self.out.glob("*.webp")},
                         before_files)
        self.assertEqual(self.sidecar_path.read_bytes(), before_sidecar)

    def test_successful_replace_removes_all_suffix_forms_after_first_render(self):
        plans = self.plans()
        result = expressions.execute_plans(
            plans, lambda plan: ("new-" + plan.destination.name).encode(),
            self.sidecar_path, self.source)
        self.assertEqual((self.out / "joy.webp").read_bytes(), b"new-joy.webp")
        self.assertEqual((self.out / "joy-1.webp").read_bytes(), b"new-joy-1.webp")
        self.assertFalse((self.out / "joy.expressive.webp").exists())
        self.assertEqual((self.out / "anger.webp").read_bytes(), b"old-anger.webp")
        metadata = json.loads(self.sidecar_path.read_text(encoding="utf-8"))
        self.assertEqual(set(metadata), {"joy.webp", "joy-1.webp", "anger.webp"})
        self.assertEqual(set(metadata["joy.webp"]), {
            "label", "prompt", "seed", "keepBackground", "source", "when"})
        self.assertEqual(set(metadata["joy.webp"]["source"]),
                         {"kind", "path", "mtime"})
        self.assertEqual(metadata["joy.webp"]["source"]["kind"], "image")
        self.assertEqual(metadata["joy.webp"]["source"]["path"],
                         str(self.source.resolve()))
        self.assertEqual(metadata["joy.webp"]["source"]["mtime"],
                         self.source.stat().st_mtime_ns / 1_000_000)
        self.assertEqual(result.written, 2)

    def test_explicit_actual_source_kind_is_saved_and_legacy_records_survive(self):
        legacy_source = {"path": "C:/legacy/portrait.png", "mtime": 10}
        self.old_meta["anger.webp"]["source"] = legacy_source
        self.sidecar_path.write_text(json.dumps(self.old_meta, sort_keys=True),
                                     encoding="utf-8")
        plans = self.plans(replace=False)
        result = expressions.execute_plans(
            plans, lambda _plan: b"new", self.sidecar_path, self.source,
            source_kind="token")
        metadata = json.loads(self.sidecar_path.read_text(encoding="utf-8"))

        self.assertEqual(result.written, 2)
        self.assertEqual(metadata["joy-2.webp"]["source"]["kind"], "token")
        self.assertEqual(metadata["anger.webp"]["source"], legacy_source)

    def test_later_success_is_the_first_destructive_point_after_a_failure(self):
        attempts = 0

        def fail_then_succeed(_plan):
            nonlocal attempts
            attempts += 1
            # Rendering happens before cleanup: both attempts can still see
            # every old variant, including the attempt that will succeed.
            self.assertTrue((self.out / "joy.expressive.webp").exists())
            if attempts == 1:
                raise RuntimeError("first render failed")
            return b"first-success"

        result = expressions.execute_plans(
            self.plans(), fail_then_succeed, self.sidecar_path, self.source)
        self.assertEqual((result.written, result.failed), (1, 1))
        self.assertEqual((self.out / "joy.webp").read_bytes(), b"first-success")
        self.assertFalse((self.out / "joy-1.webp").exists())
        self.assertFalse((self.out / "joy.expressive.webp").exists())

    def test_single_file_redo_changes_only_that_file_and_metadata(self):
        args = SimpleNamespace(count=1, seed=44, replace=False,
                               file="joy-1.webp", keep_background=False,
                               describe="joyful new grin")
        plans, _ = expressions.make_plans(
            self.out, args, {}, {}, None, self.old_meta)
        expressions.execute_plans(
            plans, lambda _plan: b"redone", self.sidecar_path, self.source)
        self.assertEqual((self.out / "joy-1.webp").read_bytes(), b"redone")
        self.assertEqual((self.out / "joy.webp").read_bytes(), b"old-joy.webp")
        self.assertTrue((self.out / "joy.expressive.webp").exists())
        metadata = json.loads(self.sidecar_path.read_text(encoding="utf-8"))
        self.assertEqual(metadata["joy.webp"], self.old_meta["joy.webp"])
        self.assertEqual(metadata["joy-1.webp"]["seed"], 44)

    def test_partial_failure_continues_and_returns_failure_status(self):
        args = SimpleNamespace(count=1, seed=1, replace=False, file=None,
                               keep_background=False, describe=None)
        plans, _ = expressions.make_plans(
            self.out, args, {"anger": ["angry"], "sadness": ["sad"]}, {},
            (("anger", "sadness"), False), self.old_meta)

        def render(plan):
            if plan.label == "anger":
                raise RuntimeError("bad anger")
            return b"sad-image"

        result = expressions.execute_plans(
            plans, render, self.sidecar_path, self.source)
        self.assertEqual(result.exit_code, 1)
        self.assertEqual((result.written, result.failed), (1, 1))
        self.assertTrue((self.out / "sadness.webp").exists())

    def test_dry_run_prints_full_plan_without_calling_renderer_or_writing(self):
        args = SimpleNamespace(count=1, seed=8, replace=False, file=None,
                               keep_background=False, describe=None)
        empty = self.out / "dry"
        plans, _ = expressions.make_plans(
            empty, args, {"joy": ["joyful wide grin"]}, {},
            (("joy",), False))
        output = io.StringIO()

        def forbidden(_plan):
            self.fail("dry-run called the renderer")

        result = expressions.execute_plans(
            plans, forbidden, empty / "expressions.json", self.source,
            dry_run=True, output=output)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("joy.webp", output.getvalue())
        self.assertIn("joyful wide grin", output.getvalue())
        self.assertFalse(empty.exists())


class TestGraph(unittest.TestCase):
    def build(self, **overrides):
        values = dict(image_ref="lancer-expressions/portrait.png [input]",
                      prompt="joyful grin", seed=123, steps=4, quality=90,
                      keep_background=False, prefix="Expressions/joy")
        values.update(overrides)
        return expressions.build_graph(**values)

    def test_graph_patches_image_prompt_seed_steps_and_quality(self):
        graph = self.build(seed=9, steps=7, quality=81)
        load_id, load = only(graph, "LoadImage")
        _, sampler = only(graph, "KSampler")
        encode = graph[sampler["inputs"]["positive"][0]]
        _, save = only(graph, "SaveAnimatedWEBP")
        self.assertEqual(load["inputs"]["image"],
                         "lancer-expressions/portrait.png [input]")
        self.assertEqual(encode["inputs"]["image1"], [load_id, 0])
        self.assertEqual(encode["inputs"]["prompt"], "joyful grin")
        self.assertEqual((sampler["inputs"]["seed"], sampler["inputs"]["steps"]),
                         (9, 7))
        self.assertEqual(save["inputs"]["quality"], 81)

    def test_graph_samples_a_tall_full_body_canvas_from_original_conditioning(self):
        graph = self.build()
        load_id, _ = only(graph, "LoadImage")
        _, sampler = only(graph, "KSampler")
        latent = graph[sampler["inputs"]["latent_image"][0]]
        positive = graph[sampler["inputs"]["positive"][0]]
        self.assertEqual(latent["class_type"], "EmptySD3LatentImage")
        self.assertEqual(latent["inputs"], {
            "width": 768, "height": 1344, "batch_size": 1})
        self.assertEqual(positive["inputs"]["image1"], [load_id, 0])

    def test_background_removal_is_default_and_can_be_bypassed(self):
        transparent = self.build()
        rmbg_id, _ = only(transparent, "RMBG")
        _, save = only(transparent, "SaveAnimatedWEBP")
        self.assertEqual(save["inputs"]["images"], [rmbg_id, 0])

        kept = self.build(keep_background=True)
        decode_id, _ = only(kept, "VAEDecode")
        _, save = only(kept, "SaveAnimatedWEBP")
        self.assertEqual(save["inputs"]["images"], [decode_id, 0])

    def test_workflow_preserves_qwen_edit_model_and_lightning_lora(self):
        graph = self.build()
        _, unet = only(graph, "UNETLoader")
        _, lora = only(graph, "LoraLoaderModelOnly")
        self.assertEqual(unet["inputs"]["unet_name"],
                         "qwen_image_edit_2509_fp8_e4m3fn.safetensors")
        self.assertEqual(lora["inputs"]["lora_name"],
                         "Qwen\\Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors")


class TestWorkflowAgainstLiveServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not server_is_up():
            raise unittest.SkipTest("no ComfyUI on 127.0.0.1:8000")

    def test_classes_and_required_inputs_exist(self):
        graph = json.loads(WORKFLOW.read_text(encoding="utf-8"))
        for node_id, node in graph.items():
            schema = object_info(node["class_type"])
            with self.subTest(node=node_id, class_type=node["class_type"]):
                self.assertIsNotNone(schema)
            if schema is None:
                continue
            required = schema["input"].get("required", {})
            for key in expected_inputs(required, node["inputs"]):
                with self.subTest(node=node_id, input=key):
                    self.assertIn(key, node["inputs"])


if __name__ == "__main__":
    unittest.main()
