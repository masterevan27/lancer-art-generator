"""Selection, skipping and the dossier section - everything before ComfyUI.

Nothing here queues a job. These are the parts of generate-3d.py that decide
WHICH NPCs get built and WHAT gets recorded afterwards, and they are the parts
a --dry-run has to get right for the run that follows to be worth starting.
"""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from test.helpers import load_3d, manifest_entry

d3 = load_3d()


def manifest_of(*entries):
    """A .generated-npcs.json-shaped dict, keyed by folder path as the real one is."""
    return {"/npcs/%s" % e["name"]: e for e in entries}


class TestSelection(unittest.TestCase):
    def setUp(self):
        self.a = manifest_entry(11)
        self.b = manifest_entry(12)
        self.manifest = manifest_of(self.a, self.b)

    def args(self, argv):
        return d3.parse_args(argv)

    def test_everything_by_default(self):
        picked = d3.select_entries(self.manifest, self.args([]))
        self.assertEqual(len(picked), 2)

    def test_id_picks_exactly_one(self):
        picked = d3.select_entries(self.manifest, self.args(["--id", self.a["id"]]))
        self.assertEqual([e["id"] for _, e in picked], [self.a["id"]])

    def test_an_unknown_id_is_an_error_not_an_empty_run(self):
        """Silently building nothing is the worst answer to a typo'd id."""
        with self.assertRaises(SystemExit):
            d3.select_entries(self.manifest, self.args(["--id", "npc-nobody-0"]))

    def test_filter_matches_the_name(self):
        picked = d3.select_entries(self.manifest, self.args(["--filter", self.a["name"]]))
        self.assertEqual([e["id"] for _, e in picked], [self.a["id"]])

    def test_exclude_removes_it_again(self):
        picked = d3.select_entries(
            self.manifest, self.args(["--exclude", self.a["name"]]))
        self.assertNotIn(self.a["id"], [e["id"] for _, e in picked])

    def test_filter_matches_the_folder_path(self):
        """Spec §8 asks for --filter by category, and the path carries it."""
        manifest = {"/npcs/Crew/one": self.a, "/npcs/Officers/two": self.b}
        picked = d3.select_entries(manifest, self.args(["--filter", "Officers"]))
        self.assertEqual([e["id"] for _, e in picked], [self.b["id"]])

    def test_limit_caps_the_batch(self):
        picked = d3.select_entries(self.manifest, self.args(["--limit", "1"]))
        self.assertEqual(len(picked), 1)

    def test_selection_is_ordered(self):
        """Two runs of the same --limit must pick the same NPCs."""
        first = d3.select_entries(self.manifest, self.args(["--limit", "1"]))
        second = d3.select_entries(self.manifest, self.args(["--limit", "1"]))
        self.assertEqual([k for k, _ in first], [k for k, _ in second])

    def test_non_npc_manifest_rows_are_ignored(self):
        """The manifest is a plain dict; a hand-added row need not be an NPC."""
        manifest = dict(self.manifest, note="a stray string", other={"kind": "mech"})
        picked = d3.select_entries(manifest, self.args([]))
        self.assertEqual(len(picked), 2)


class TestStageFlag(unittest.TestCase):
    def test_all_stages_by_default(self):
        self.assertEqual(list(d3.parse_args([]).stage), list(d3.STAGES))

    def test_one_stage_in_isolation(self):
        self.assertEqual(d3.parse_args(["--stage", "apose"]).stage, ["apose"])

    def test_stages_accumulate(self):
        args = d3.parse_args(["--stage", "apose", "--stage", "mesh"])
        self.assertEqual(args.stage, ["apose", "mesh"])

    def test_an_unknown_stage_is_refused(self):
        with self.assertRaises(SystemExit):
            d3.parse_args(["--stage", "texture"])


class TestSkipping(unittest.TestCase):
    def test_a_fresh_npc_is_not_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(d3.should_skip(Path(tmp) / "3d", d3.parse_args([])))

    def test_an_existing_3d_folder_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "3d"
            folder.mkdir()
            (folder / "apose.png").write_bytes(b"")
            self.assertTrue(d3.should_skip(folder, d3.parse_args([])))

    def test_overwrite_builds_it_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "3d"
            folder.mkdir()
            (folder / "apose.png").write_bytes(b"")
            self.assertFalse(d3.should_skip(folder, d3.parse_args(["--overwrite"])))

    def test_an_empty_3d_folder_is_not_skipped(self):
        """A folder left behind by a crashed run holds nothing worth keeping."""
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "3d"
            folder.mkdir()
            self.assertFalse(d3.should_skip(folder, d3.parse_args([])))


class TestDossierSection(unittest.TestCase):
    FILES = ["Jules Sokolova Rigged.glb", "Jules Sokolova Print.stl"]
    WORKFLOWS = ["workflows/api/Util_Image_to_Mesh_Hunyuan3D_v1.json",
                 "workflows/api/Util_Image_to_RiggedBody_SAM3D_v1.json"]

    def section(self):
        return d3.dossier_3d_section(self.FILES, self.WORKFLOWS, d3.APOSE_STANCE)

    def test_it_lists_every_file(self):
        text = self.section()
        for name in self.FILES:
            with self.subTest(name=name):
                self.assertIn(name, text)

    def test_it_names_both_workflows(self):
        text = self.section()
        for path in self.WORKFLOWS:
            with self.subTest(path=path):
                self.assertIn(Path(path).name, text)

    def test_it_records_the_stance(self):
        """Spec §6.1: the dossier keeps recording everything needed to reproduce."""
        self.assertIn(d3.APOSE_STANCE, self.section())

    def test_appending_twice_leaves_one_section(self):
        """A re-run with --overwrite must replace the section, not stack one."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Jules Sokolova.md"
            path.write_text("# Jules Sokolova\n\n## Art\n\n- `x.png`\n", encoding="utf-8")
            for _ in range(2):
                d3.append_dossier_3d(path, self.FILES, self.WORKFLOWS, d3.APOSE_STANCE)
            self.assertEqual(path.read_text(encoding="utf-8").count("\n## 3D\n"), 1)

    def test_the_existing_dossier_survives(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Jules Sokolova.md"
            path.write_text("# Jules Sokolova\n\n## Art\n\n- `x.png`\n", encoding="utf-8")
            d3.append_dossier_3d(path, self.FILES, self.WORKFLOWS, d3.APOSE_STANCE)
            text = path.read_text(encoding="utf-8")
            self.assertIn("## Art", text)
            self.assertIn("- `x.png`", text)


class TestDryRun(unittest.TestCase):
    def test_it_prints_the_apose_prompt_and_queues_nothing(self):
        entry = manifest_entry(21)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(manifest_of(entry)), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = d3.main(["--manifest", str(path), "--dry-run"])
        self.assertEqual(code, 0)
        output = buffer.getvalue()
        self.assertIn(entry["name"], output)
        self.assertIn(d3.APOSE_STANCE, output)


class TestBatchIsolation(unittest.TestCase):
    """Regression test for a Critical review finding on Task 4.

    stage_apose() raises SystemExit for a missing/malformed workflow file.
    SystemExit derives from BaseException, not Exception, so a per-NPC
    handler written as `except Exception` lets it escape the batch loop
    entirely - the exact failure spec §8's "one bad reconstruction must not
    take the rest of a 160-NPC batch with it" forbids. This drives main()
    over a two-entry manifest with stage_apose() faked to always raise
    SystemExit, and checks the isolation property itself - that BOTH NPCs
    were attempted and BOTH are counted as failed - not merely that no
    exception happened to propagate, which a version that silently skipped
    the second NPC would also satisfy.
    """

    def test_a_systemexit_from_one_npc_does_not_abort_the_batch(self):
        a = manifest_entry(41)
        b = manifest_entry(42)
        attempted = []

        def fake_stage_apose(comfy, args, entry, folder):
            attempted.append(entry["name"])
            raise SystemExit("Background-removal workflow not found: nope.json")

        fake_comfy = mock.Mock()
        fake_comfy.base = "http://fake"

        with tempfile.TemporaryDirectory() as tmp:
            manifest = {str(Path(tmp) / a["name"]): a, str(Path(tmp) / b["name"]): b}
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")

            with mock.patch.object(d3.art, "find_server", return_value=fake_comfy), \
                 mock.patch.object(d3, "stage_apose", side_effect=fake_stage_apose):
                buffer = io.StringIO()
                try:
                    with redirect_stdout(buffer):
                        code = d3.main(["--manifest", str(path)])
                except SystemExit as exc:
                    self.fail("SystemExit from one NPC's stage escaped main() "
                              "and aborted the batch: %r" % (exc,))

        self.assertEqual(attempted, [a["name"], b["name"]],
                         "both NPCs must be attempted, not just the first")
        self.assertIn("2 failed", buffer.getvalue())
        self.assertEqual(code, 1)


class TestMultipart(unittest.TestCase):
    """The upload body is built by hand, so it is worth checking by hand.

    ComfyUI's /upload/image takes multipart/form-data and the standard library
    has no builder for it. Splitting the body construction out from the POST
    is what makes it checkable without a server.
    """

    def body(self):
        return d3._multipart({"type": "input", "subfolder": "lancer3d"},
                             "image", "apose.png", b"\x89PNG\r\n\x1a\n")

    def test_the_boundary_is_declared_and_used(self):
        content_type, body = self.body()
        self.assertTrue(content_type.startswith("multipart/form-data; boundary="))
        boundary = content_type.split("boundary=")[1]
        self.assertIn(boundary.encode(), body)

    def test_it_ends_with_the_closing_boundary(self):
        content_type, body = self.body()
        boundary = content_type.split("boundary=")[1]
        self.assertTrue(body.endswith(("--%s--\r\n" % boundary).encode()))

    def test_every_field_is_present(self):
        _, body = self.body()
        for token in (b'name="type"', b'input', b'name="subfolder"', b'lancer3d',
                      b'name="image"', b'filename="apose.png"'):
            with self.subTest(token=token):
                self.assertIn(token, body)

    def test_the_binary_payload_is_not_mangled(self):
        _, body = self.body()
        self.assertIn(b"\x89PNG\r\n\x1a\n", body)

    def test_the_boundary_does_not_occur_in_the_payload(self):
        """A collision would truncate the upload silently."""
        content_type, _ = self.body()
        boundary = content_type.split("boundary=")[1]
        self.assertNotIn(boundary.encode(), b"\x89PNG\r\n\x1a\n")


class TestMeshJob(unittest.TestCase):
    """Patching the two graphs, without a server."""

    def setUp(self):
        self.template = json.loads(
            (d3.MESH_WORKFLOW).read_text(encoding="utf-8"))

    def test_the_source_image_is_patched_in(self):
        job = d3.build_mesh_job(self.template, "lancer3d/apose.png [input]", "3d/x")
        load = job[d3.node_of(job, "LoadImage")]
        self.assertEqual(load["inputs"]["image"], "lancer3d/apose.png [input]")

    def test_the_output_prefix_is_patched_in(self):
        job = d3.build_mesh_job(self.template, "a.png [input]", "LancerNPCs/Crew/jules/shell")
        save = job[d3.node_of(job, "SaveGLB")]
        self.assertEqual(save["inputs"]["filename_prefix"], "LancerNPCs/Crew/jules/shell")

    def test_the_template_on_disk_is_not_mutated(self):
        """One template is patched once per NPC across a 160-NPC batch."""
        before = json.dumps(self.template, sort_keys=True)
        d3.build_mesh_job(self.template, "a.png [input]", "3d/x")
        self.assertEqual(json.dumps(self.template, sort_keys=True), before)

    def test_the_seed_reaches_every_sampler(self):
        job = d3.build_mesh_job(self.template, "a.png [input]", "3d/x", seed=4242)
        seeds = [n["inputs"]["seed"] for n in job.values()
                 if n["class_type"] == "KSampler"]
        self.assertEqual(seeds, [4242])

    def test_node_of_refuses_an_ambiguous_graph(self):
        graph = {"1": {"class_type": "LoadImage", "inputs": {}},
                 "2": {"class_type": "LoadImage", "inputs": {}}}
        with self.assertRaises(d3.art.WorkflowError):
            d3.node_of(graph, "LoadImage")

    def test_node_of_refuses_a_missing_node(self):
        with self.assertRaises(d3.art.WorkflowError):
            d3.node_of({}, "SaveGLB")


class TestMeshOutputs(unittest.TestCase):
    """SaveGLB does not report under "images", and its key has moved before.

    Reading every list of file dicts in the record, rather than one hardcoded
    UI key, is what stops a ComfyUI rename turning into "the job produced no
    .glb" on a job that produced one.
    """

    def test_it_finds_a_glb_under_any_key(self):
        for key in ("3d", "result", "images", "gltf"):
            record = {"outputs": {"5": {key: [
                {"filename": "base_00001_.glb", "subfolder": "3d", "type": "output"}]}}}
            with self.subTest(key=key):
                found = d3.mesh_outputs(record)
                self.assertEqual([f["filename"] for f in found], ["base_00001_.glb"])

    def test_it_ignores_a_png_beside_the_glb(self):
        record = {"outputs": {"5": {"images": [
            {"filename": "preview.png"}, {"filename": "base.glb"}]}}}
        self.assertEqual([f["filename"] for f in d3.mesh_outputs(record)], ["base.glb"])

    def test_it_survives_a_record_with_no_outputs(self):
        self.assertEqual(d3.mesh_outputs({}), [])

    def test_it_survives_scalar_output_values(self):
        record = {"outputs": {"5": {"text": "done", "count": 3}}}
        self.assertEqual(d3.mesh_outputs(record), [])


class TestReportParsing(unittest.TestCase):
    """Blender writes a lot to stdout; the report is one line inside it."""

    def test_it_finds_the_report_among_the_noise(self):
        stdout = ("Blender 5.2.1 LTS\n"
                  'LANCER3D {"files": ["a.glb"], "non_manifold": 0}\n'
                  "Blender quit\n")
        self.assertEqual(d3.parse_report(stdout)["files"], ["a.glb"])

    def test_the_last_report_wins(self):
        """Defensive: one run, one report - but never silently read a stale one."""
        stdout = ('LANCER3D {"files": ["old.glb"]}\n'
                  'LANCER3D {"files": ["new.glb"]}\n')
        self.assertEqual(d3.parse_report(stdout)["files"], ["new.glb"])

    def test_no_report_is_an_error(self):
        with self.assertRaises(RuntimeError):
            d3.parse_report("Blender quit\n")

    def test_a_malformed_report_is_an_error(self):
        with self.assertRaises(RuntimeError):
            d3.parse_report("LANCER3D not json\n")


class TestStageAssemble(unittest.TestCase):
    """The Blender command stage_assemble builds - subprocess.run mocked out,
    so this needs neither a real Blender nor the assembly script to run."""

    def _command_for(self, argv):
        """The command list stage_assemble hands to subprocess.run, for argv."""
        args = d3.parse_args(argv)
        fake_proc = mock.Mock(returncode=0, stdout='LANCER3D {"files": ["x.glb"]}\n', stderr="")
        with mock.patch.object(d3, "find_blender", return_value=Path("blender.exe")), \
             mock.patch.object(d3.subprocess, "run", return_value=fake_proc) as run:
            d3.stage_assemble(args, Path("/npcs/x/3d"), "X", Path("base.glb"), Path("shell.glb"))
        return run.call_args[0][0]

    def test_voxel_defaults_to_0_004(self):
        """0.0, assemble_npc.py's own default, left a real cleaned shell with 3
        non-manifold edges; 0.004 was the value that measurably fixed it."""
        self.assertEqual(d3.parse_args([]).voxel, 0.004)

    def test_the_command_passes_voxel_through(self):
        command = self._command_for(["--voxel", "0.01"])
        self.assertIn("--voxel", command)
        self.assertEqual(command[command.index("--voxel") + 1], "0.01")

    def test_the_default_voxel_reaches_the_command_untouched(self):
        command = self._command_for([])
        self.assertEqual(command[command.index("--voxel") + 1], "0.004")


class TestRigFlags(unittest.TestCase):
    """Rigging ships off. Both bind modes were measured against a real Lucia
    Vos reconstruction and neither is trustworthy unattended: `transfer`
    produced a complete rig with severe tearing at the shoulder, and `auto`
    left every one of 292,296 shell vertices unweighted. See
    docs/generate-3d.md#rigging for the numbers."""

    def test_rigging_is_off_by_default(self):
        self.assertFalse(d3.parse_args([]).rig)

    def test_rig_turns_it_on(self):
        self.assertTrue(d3.parse_args(["--rig"]).rig)

    def test_the_bind_mode_defaults_to_transfer(self):
        self.assertEqual(d3.parse_args([]).bind, "transfer")

    def test_an_unknown_bind_mode_is_refused(self):
        with self.assertRaises(SystemExit):
            d3.parse_args(["--bind", "magic"])

    def test_the_flags_reach_the_blender_command(self):
        args = d3.parse_args(["--rig", "--bind", "auto"])
        command = d3.assemble_command("/blender.exe", args, Path("/out"), "Jules",
                                      Path("/b.glb"), Path("/s.glb"))
        self.assertIn("--rig", command)
        self.assertIn("--bind", command)
        self.assertIn("auto", command)

    def test_without_rig_the_flag_is_omitted(self):
        args = d3.parse_args([])
        command = d3.assemble_command("/blender.exe", args, Path("/out"), "Jules",
                                      Path("/b.glb"), Path("/s.glb"))
        self.assertNotIn("--rig", command)

    def test_the_stem_reaches_the_command_unsplit(self):
        """A name with a space must arrive as one argv element, not two."""
        args = d3.parse_args([])
        command = d3.assemble_command("/blender.exe", args, Path("/out"),
                                      "Jules Sokolova", Path("/b.glb"), Path("/s.glb"))
        self.assertIn("Jules Sokolova", command)


if __name__ == "__main__":
    unittest.main()
