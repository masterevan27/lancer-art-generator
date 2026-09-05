"""Selection, skipping and the dossier section - everything before ComfyUI.

Nothing here queues a job. These are the parts of generate-3d.py that decide
WHICH NPCs get built and WHAT gets recorded afterwards, and they are the parts
a --dry-run has to get right for the run that follows to be worth starting.
"""
import io
import json
import re
import tempfile
import unittest
import zlib
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from test.helpers import REPO, load_3d, manifest_entry

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
            d3.parse_args(["--stage", "paint"])


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

    def test_a_narrowed_stage_is_never_skipped(self):
        """--stage apose, then --stage mesh, is the documented iteration flow.

        should_skip() must not defeat it: the second command sees apose.png
        already on disk from the first, and would skip the NPC outright if
        the skip applied to a narrowed --stage the same way it applies to a
        full default run.
        """
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "3d"
            folder.mkdir()
            (folder / "apose.png").write_bytes(b"")
            self.assertFalse(
                d3.should_skip(folder, d3.parse_args(["--stage", "mesh"])))

    def test_all_four_stages_explicitly_still_skip(self):
        """Naming all four stages by hand is the same as the default."""
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "3d"
            folder.mkdir()
            (folder / "apose.png").write_bytes(b"")
            args = d3.parse_args(
                ["--stage", "apose", "--stage", "mesh", "--stage", "assemble",
                 "--stage", "texture"])
            self.assertTrue(d3.should_skip(folder, args))


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
                 mock.patch.object(d3, "stage_apose", side_effect=fake_stage_apose), \
                 mock.patch.object(d3, "find_blender", return_value=Path("blender.exe")):
                # find_blender is mocked so this test's hermeticity does not
                # depend on Blender being installed on whatever machine runs
                # it - preflight() (generate-3d.py) checks it before the loop
                # starts, and this test is about per-NPC isolation of
                # stage_apose's own failure, not about preflight.
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


class TestPreflight(unittest.TestCase):
    """Regression test for a Final review finding: find_blender() and the
    workflow-file checks used to live only inside stage_assemble()/
    stage_mesh()/stage_apose(), which run inside main()'s per-NPC try/except
    - so a mistyped --blender failed once per NPC, each failure only
    surfacing after that NPC had already burned a full A-pose render and two
    3D reconstructions. preflight() must catch a missing precondition once,
    before any NPC is attempted at all.
    """

    def test_a_missing_precondition_fails_before_any_npc_is_attempted(self):
        a = manifest_entry(51)
        b = manifest_entry(52)
        attempted = []

        def fake_stage_apose(comfy, args, entry, folder):
            attempted.append(entry["name"])
            return Path(str(folder)) / "apose.png"

        fake_comfy = mock.Mock()
        fake_comfy.base = "http://fake"

        with tempfile.TemporaryDirectory() as tmp:
            manifest = {str(Path(tmp) / a["name"]): a, str(Path(tmp) / b["name"]): b}
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")

            with mock.patch.object(d3.art, "find_server", return_value=fake_comfy), \
                 mock.patch.object(d3, "stage_apose", side_effect=fake_stage_apose), \
                 mock.patch.object(d3, "find_blender",
                                   side_effect=SystemExit("Blender not found: nope.exe")):
                with self.assertRaises(SystemExit):
                    d3.main(["--manifest", str(path)])

        self.assertEqual(attempted, [],
                         "no NPC should be attempted once a global "
                         "precondition has already failed")

    def test_a_narrowed_apose_only_run_does_not_check_blender(self):
        """--stage apose does not reach assemble, so it must not require it."""
        with mock.patch.object(
                d3, "find_blender",
                side_effect=AssertionError(
                    "find_blender must not run for a --stage apose-only preflight")):
            d3.preflight(d3.parse_args(["--stage", "apose"]))

    def test_a_missing_rmbg_workflow_is_caught_for_the_apose_stage(self):
        args = d3.parse_args(["--stage", "apose", "--rmbg", "no/such/file.json"])
        with self.assertRaises(SystemExit):
            d3.preflight(args)

    def test_a_missing_mesh_workflow_is_caught_for_the_mesh_stage(self):
        args = d3.parse_args(["--stage", "mesh"])
        with mock.patch.object(d3, "MESH_WORKFLOW", Path("no/such/mesh.json")):
            with self.assertRaises(SystemExit):
                d3.preflight(args)


class TestRunSummary(unittest.TestCase):
    """Regression test for a Final review finding: warned counts contained
    failures - a rig that did not bind, or (since the texture stage) a
    texture that did not bake - and printing the parenthetical unconditionally
    would read as "every NPC got a warning" when in fact none did. It must
    appear only when a warning was actually recorded.

    --no-texture is passed throughout: this class is about the rig-note
    mechanism, and the texture stage - on by default - would otherwise add
    its own contained failure (there is no real Shell.glb on disk here) and
    confound the count these tests are checking.
    """

    def run_main(self, extra_args, report):
        a = manifest_entry(61)
        fake_comfy = mock.Mock()
        fake_comfy.base = "http://fake"

        with tempfile.TemporaryDirectory() as tmp:
            manifest = {str(Path(tmp) / a["name"]): a}
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")

            with mock.patch.object(d3.art, "find_server", return_value=fake_comfy), \
                 mock.patch.object(d3, "find_blender", return_value=Path("blender.exe")), \
                 mock.patch.object(d3, "stage_apose",
                                   return_value=Path(tmp) / "apose.png"), \
                 mock.patch.object(d3, "stage_mesh",
                                   return_value=(Path(tmp) / "_shell.glb",
                                                 Path(tmp) / "_base.glb")), \
                 mock.patch.object(d3, "stage_assemble", return_value=report):
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    d3.main(["--manifest", str(path), "--no-texture"] + extra_args)
        return buffer.getvalue()

    def test_the_rig_note_is_omitted_without_a_warning(self):
        output = self.run_main([], {"files": ["Shell.glb"]})
        self.assertNotIn("with a warning", output)
        self.assertIn("done: 1 built,", output)

    def test_the_rig_note_appears_with_a_warning(self):
        output = self.run_main(
            ["--rig"], {"files": ["Shell.glb"], "rig_error": "boom"})
        self.assertIn("(1 with a warning)", output)


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

    def test_voxel_defaults_to_0_013(self):
        """0.0, assemble_npc.py's own default, refuses to write an STL at all -
        a real reconstruction is never closed on arrival.

        A finer voxel has a thinner narrow band and leaks where a coarser one
        does not, so this sits clear of the cliff rather than on the finest
        value that happened to work once. Measured as the fraction of surface
        area surviving the remesh, on the square-framed shell the pipeline now
        produces: 0.004 kept 32%, 0.008 kept 39%, 0.013 kept ~67%. The earlier
        0.010 was tuned against the pre-squaring shell, which was denser and
        less open, and does not survive on this one."""
        self.assertEqual(d3.parse_args([]).voxel, 0.013)

    def test_the_command_passes_voxel_through(self):
        command = self._command_for(["--voxel", "0.02"])
        self.assertIn("--voxel", command)
        self.assertEqual(command[command.index("--voxel") + 1], "0.02")

    def test_the_default_voxel_reaches_the_command_untouched(self):
        command = self._command_for([])
        self.assertEqual(command[command.index("--voxel") + 1], "0.013")


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


class TestRealHeight(unittest.TestCase):
    """The NPC's rolled '## Height' beats SAM3DBody's estimate of it.

    SAM3DBody infers metric scale from a single image with no reference in it
    and guesses low - 1.5065 m for an NPC whose Height bullet says "a solid
    five foot nine or so", which is 1.753 m. The estimate is self-consistent,
    so nothing downstream ever caught it; it is simply the wrong person.
    """

    def test_every_height_bullet_in_the_tables_parses(self):
        """The guard that matters. A reworded bullet must not silently stop
        resolving and drop that NPC back onto the estimate."""
        text = (REPO / "prompts" / "npc-generator-tables.md").read_text(encoding="utf-8")
        bullets = []
        for heading in ("## Height\n", "## Height (she)\n"):
            start = text.index(heading)
            end = text.index("\n## ", start + len(heading))
            bullets += [re.sub(r"^- (?:x\d+ )?", "", line)
                        for line in text[start:end].splitlines()
                        if line.startswith("- ")]
        self.assertGreaterEqual(len(bullets), 12, "both Height tables should be found")
        for bullet in bullets:
            with self.subTest(bullet=bullet):
                inches = d3.height_inches(bullet)
                self.assertIsNotNone(inches, "names no parseable height")
                # 4'0" to 7'0" - wide enough for any bullet anyone would write,
                # narrow enough to catch a parse that grabbed the wrong number.
                self.assertGreaterEqual(inches, 48)
                self.assertLessEqual(inches, 84)

    def test_the_nudge_words_move_the_number(self):
        self.assertEqual(d3.height_inches("a solid six feet even"), 72)
        self.assertEqual(d3.height_inches("just under six feet"), 71)
        self.assertEqual(d3.height_inches("standing several inches over six feet"), 75)
        self.assertEqual(d3.height_inches("standing just a few inches under six feet"), 69)
        self.assertEqual(d3.height_inches("close to six and a half feet"), 77)
        self.assertEqual(d3.height_inches("a shade over five feet"), 61)

    def test_a_bullet_with_no_number_is_none_not_an_error(self):
        """'of average height' is regenerate_one()'s backfill for an entry
        written before '## Height' existed. It must fall back, not fail."""
        self.assertIsNone(d3.height_inches("of average height"))
        self.assertIsNone(d3.height_metres("of average height"))

    def test_five_foot_nine_is_one_point_seven_five_metres(self):
        self.assertAlmostEqual(d3.height_metres("a solid five foot nine or so"),
                               1.7526, places=3)


class TestRealHeightReachesBlender(unittest.TestCase):
    def _command(self, height):
        args = d3.parse_args([])
        fake = mock.Mock(returncode=0, stdout='LANCER3D {"files": []}\n', stderr="")
        with mock.patch.object(d3, "find_blender", return_value=Path("blender.exe")), \
             mock.patch.object(d3.subprocess, "run", return_value=fake) as run:
            d3.stage_assemble(args, Path("/npcs/x/3d"), "X",
                              Path("base.glb"), Path("shell.glb"), height)
        return run.call_args[0][0]

    def test_a_known_height_is_passed_through(self):
        command = self._command(1.7526)
        self.assertEqual(command[command.index("--real-height-m") + 1], "1.7526")
        self.assertEqual(command[command.index("--nominal-height-m") + 1],
                         str(d3.NOMINAL_HEIGHT_M))

    def test_an_unknown_height_passes_no_flag_at_all(self):
        """Absent, not zero: assemble_npc.py falls back to the estimate on
        None, and --real-height-m 0 would scale the figure out of existence."""
        self.assertNotIn("--real-height-m", self._command(None))

    def test_the_nominal_height_is_six_feet(self):
        self.assertAlmostEqual(d3.NOMINAL_HEIGHT_M, 1.8288, places=4)


class TestSquareApose(unittest.TestCase):
    """The A-pose is squared before it reaches CLIPVisionEncode.

    crop="center" scales the short side to the vision tower's resolution and
    centre-crops the long one, so a 4:5 A-pose loses 9% off each end of the
    subject - the helmet crown and the whole boot. Every reconstruction came
    back with a flat-sliced head and legs ending in stumps until this landed.
    """

    def _tall_subject(self, path, width=100, height=200,
                      box=(30, 10, 69, 189), backdrop=(236, 230, 232)):
        """A PNG with an opaque red rectangle on a transparent backdrop."""
        x0, y0, x1, y1 = box
        rows = []
        for y in range(height):
            row = bytearray(bytes(backdrop + (0,)) * width)
            if y0 <= y <= y1:
                for x in range(x0, x1 + 1):
                    row[x * 4:x * 4 + 4] = bytes((255, 0, 0, 255))
            rows.append(row)
        d3._png_write(path, width, height, rows)
        return box

    def test_the_png_helpers_round_trip(self):
        """Written by hand, so the writer and the reader have to agree."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.png"
            self._tall_subject(path)
            width, height, rows = d3._png_read(path)
            self.assertEqual((width, height), (100, 200))
            self.assertEqual(tuple(rows[100][30 * 4:30 * 4 + 4]), (255, 0, 0, 255))
            self.assertEqual(rows[0][3], 0)

    def test_it_finds_the_subject(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.png"
            box = self._tall_subject(path)
            width, height, rows = d3._png_read(path)
            self.assertEqual(d3.subject_bounds(rows, width, height), box)

    def test_the_result_is_square_and_holds_the_whole_subject(self):
        """The point of the exercise: nothing of the figure may be cut."""
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / "a.png", Path(tmp) / "b.png"
            self._tall_subject(src)                      # subject is 40 x 180
            side = d3.square_apose(src, dst, margin=0.06)
            width, height, rows = d3._png_read(dst)
            self.assertEqual(width, height, "not square")
            self.assertEqual(width, side)
            x0, y0, x1, y1 = d3.subject_bounds(rows, width, height)
            self.assertEqual((x1 - x0 + 1, y1 - y0 + 1), (40, 180),
                             "the subject changed size")
            self.assertGreaterEqual(y0, 1, "subject touches the top edge")
            self.assertLessEqual(y1, height - 2, "subject touches the bottom edge")

    def test_the_subject_is_centred(self):
        """Off-centre in, centred out - the centre crop is only a no-op if the
        subject actually sits in the middle of the square."""
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / "a.png", Path(tmp) / "b.png"
            self._tall_subject(src, box=(0, 10, 39, 189))     # hard against the left
            side = d3.square_apose(src, dst)
            width, height, rows = d3._png_read(dst)
            x0, y0, x1, y1 = d3.subject_bounds(rows, width, height)
            self.assertLessEqual(abs((x0 + x1) / 2 - (side - 1) / 2), 1.0)
            self.assertLessEqual(abs((y0 + y1) / 2 - (side - 1) / 2), 1.0)

    def test_the_backdrop_is_uniform_everywhere(self):
        """Not just in the padding. A seam between the added fill and the
        source's own faintly textured backdrop is a rectangle, and Hunyuan3D
        reconstructed one as a slab standing behind the figure."""
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / "a.png", Path(tmp) / "b.png"
            self._tall_subject(src)
            d3.square_apose(src, dst)
            width, height, rows = d3._png_read(dst)
            backdrop = set()
            for row in rows:
                for x in range(width):
                    if row[x * 4 + 3] == 0:
                        backdrop.add(tuple(row[x * 4:x * 4 + 3]))
            self.assertEqual(backdrop, {(236, 230, 232)},
                             "more than one backdrop colour: %s" % backdrop)

    def test_a_soft_alpha_edge_is_blended_not_thresholded(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / "a.png", Path(tmp) / "b.png"
            rows = []
            for y in range(20):
                row = bytearray(bytes((200, 200, 200, 0)) * 20)
                if 5 <= y <= 14:
                    for x in range(5, 15):
                        row[x * 4:x * 4 + 4] = bytes((0, 0, 0, 128))
                rows.append(row)
            d3._png_write(src, 20, 20, rows)
            d3.square_apose(src, dst, threshold=16)
            _, _, out = d3._png_read(dst)
            blended = [tuple(r[x * 4:x * 4 + 4]) for r in out for x in range(len(r) // 4)
                       if r[x * 4 + 3] == 128]
            self.assertTrue(blended, "the soft pixels vanished")
            # 0 over 200 at alpha 128, integer-blended: 200*127//255 = 99.
            # The point is that it is neither pure black nor the flat backdrop.
            self.assertEqual(blended[0][:3], (99, 99, 99))

    def test_an_empty_cutout_is_a_loud_failure(self):
        """Background removal eating the figure must not reach ComfyUI as a
        blank square that reconstructs into nothing."""
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / "a.png", Path(tmp) / "b.png"
            d3._png_write(src, 8, 8, [bytearray(bytes((0, 0, 0, 0)) * 8) for _ in range(8)])
            with self.assertRaises(RuntimeError):
                d3.square_apose(src, dst)


def write_png(path, width=8, height=8, alpha=255, blob=None):
    """An 8-bit RGBA PNG. `alpha` fills the canvas; `blob` is an opaque box.

    Two shapes matter to --image: a fully opaque image - one that still has a
    background - and a real cutout, a figure standing on transparency. Both
    come from the same primitive so a test names which one it means.
    """
    rows = []
    for y in range(height):
        row = bytearray()
        for x in range(width):
            a = alpha
            if blob and blob[0] <= x <= blob[2] and blob[1] <= y <= blob[3]:
                a = 255
            row += bytes((200, 200, 200, a))
        rows.append(row)
    d3._png_write(path, width, height, rows)
    return path


class TestImageFlag(unittest.TestCase):
    """--image: reconstruct from an A-pose the caller supplies.

    The whole point of stage apose is to produce one cut-out A-pose PNG. When
    the caller already has that image, every check here exists to make the
    ways it can be the WRONG image fail before a reconstruction is queued -
    each of them costs minutes on the GPU and produces a plausible-looking
    wrong answer rather than an error.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cutout = write_png(self.root / "cutout.png", alpha=0, blob=(2, 2, 5, 5))
        self.opaque = write_png(self.root / "opaque.png", alpha=255)
        self.entry = manifest_entry(11)
        self.folder_path = self.root / "npc"
        self.folders = [d3.npc_3d_folder(self.folder_path)]

    def args(self, argv):
        return d3.parse_args(argv)

    # -- the flag itself ---------------------------------------------------

    def test_the_path_is_read_onto_the_args(self):
        args = self.args(["--image", str(self.cutout)])
        self.assertEqual(Path(args.image), self.cutout)

    def test_no_image_by_default(self):
        self.assertIsNone(self.args([]).image)

    def test_an_image_skips_the_apose_stage_by_default(self):
        """The supplied image IS the A-pose; rendering one would discard it."""
        args = self.args(["--image", str(self.cutout)])
        self.assertEqual(list(args.stage), ["mesh", "assemble", "texture"])

    def test_an_explicit_stage_still_wins(self):
        args = self.args(["--image", str(self.cutout), "--stage", "mesh"])
        self.assertEqual(args.stage, ["mesh"])

    def test_an_image_with_stage_apose_is_refused(self):
        """One supplies the A-pose, the other generates it. Naming both is a typo."""
        with self.assertRaises(SystemExit):
            self.args(["--image", str(self.cutout), "--stage", "apose"])

    def test_a_missing_image_fails_at_parse_time(self):
        with self.assertRaises(SystemExit):
            self.args(["--image", str(self.root / "nope.png")])

    def test_remove_bg_without_an_image_is_refused(self):
        """There is nothing for it to cut out - stage apose already cuts its own."""
        with self.assertRaises(SystemExit):
            self.args(["--remove-bg"])

    # -- what the image has to be ------------------------------------------

    def test_a_cutout_passes_the_check(self):
        d3.check_image(self.args(["--image", str(self.cutout)]), self.folders)

    def test_an_opaque_image_names_remove_bg(self):
        """docs/generate-3d.md: a leftover backdrop reconstructs as a slab
        standing behind the figure. It looks like a successful run."""
        args = self.args(["--image", str(self.opaque)])
        with self.assertRaises(SystemExit) as caught:
            d3.check_image(args, self.folders)
        self.assertIn("--remove-bg", str(caught.exception))

    def test_an_opaque_image_is_fine_with_remove_bg(self):
        d3.check_image(
            self.args(["--image", str(self.opaque), "--remove-bg"]), self.folders)

    def test_a_cutout_with_remove_bg_is_allowed(self):
        """Cutting an already-cut image is wasteful, not wrong - rmbg is
        idempotent on transparency, and refusing it would block the caller
        who knows their alpha is unreliable."""
        d3.check_image(
            self.args(["--image", str(self.cutout), "--remove-bg"]), self.folders)

    def test_an_unreadable_png_is_refused(self):
        """square_apose() reads PNG by hand and understands one shape only."""
        bad = self.root / "bad.png"
        bad.write_bytes(b"not a png at all")
        with self.assertRaises(SystemExit):
            d3.check_image(self.args(["--image", str(bad)]), self.folders)

    def test_a_non_rgba_png_is_refused_before_the_gpu_sees_it(self):
        """8-bit greyscale: a real PNG that _png_read cannot decode."""
        grey = self.root / "grey.png"
        payload = zlib.compress(b"".join(bytes([0]) + bytes(8) for _ in range(8)), 6)

        def chunk(kind, body):
            return (len(body).to_bytes(4, "big") + kind + body
                    + (zlib.crc32(kind + body) & 0xffffffff).to_bytes(4, "big"))

        grey.write_bytes(
            bytes([137, 80, 78, 71, 13, 10, 26, 10])
            + chunk(b"IHDR", (8).to_bytes(4, "big") + (8).to_bytes(4, "big")
                    + bytes((8, 0, 0, 0, 0)))
            + chunk(b"IDAT", payload) + chunk(b"IEND", b""))
        with self.assertRaises(SystemExit):
            d3.check_image(self.args(["--image", str(grey)]), self.folders)

    # -- how many NPCs it can mean -----------------------------------------

    def test_two_npcs_and_one_image_is_refused(self):
        """One image cannot be the A-pose of two different people, and a batch
        that quietly gave all of them the same body would look like it worked."""
        args = self.args(["--image", str(self.cutout)])
        folders = self.folders + [d3.npc_3d_folder(self.root / "other")]
        with self.assertRaises(SystemExit) as caught:
            d3.check_image(args, folders)
        self.assertIn("2", str(caught.exception))

    # -- not clobbering a render already on disk ---------------------------

    def test_an_existing_apose_is_not_clobbered(self):
        folder = d3.npc_3d_folder(self.folder_path)
        folder.mkdir(parents=True)
        write_png(folder / "apose.png", alpha=0, blob=(1, 1, 3, 3))
        with self.assertRaises(SystemExit) as caught:
            d3.check_image(self.args(["--image", str(self.cutout)]), self.folders)
        self.assertIn("--overwrite", str(caught.exception))

    def test_overwrite_replaces_it(self):
        folder = d3.npc_3d_folder(self.folder_path)
        folder.mkdir(parents=True)
        write_png(folder / "apose.png", alpha=0, blob=(1, 1, 3, 3))
        d3.check_image(
            self.args(["--image", str(self.cutout), "--overwrite"]), self.folders)

    # -- installing it ------------------------------------------------------

    def test_a_cutout_is_copied_into_the_npc_folder(self):
        """Copied, not read in place: everything downstream - apose_square.png,
        the skip check, the dossier - assumes the 3d/ folder holds the record
        of what the reconstruction was built from."""
        folder = d3.npc_3d_folder(self.folder_path)
        folder.mkdir(parents=True)
        args = self.args(["--image", str(self.cutout)])
        apose = d3.install_image(None, args, d3.subject_of(self.entry, args), folder)
        self.assertEqual(apose, folder / "apose.png")
        self.assertEqual(apose.read_bytes(), self.cutout.read_bytes())

    def test_the_source_image_is_left_alone(self):
        folder = d3.npc_3d_folder(self.folder_path)
        folder.mkdir(parents=True)
        before = self.cutout.read_bytes()
        args = self.args(["--image", str(self.cutout)])
        d3.install_image(None, args, d3.subject_of(self.entry, args), folder)
        self.assertEqual(self.cutout.read_bytes(), before)

    def test_remove_bg_routes_the_image_through_the_cut(self):
        """--remove-bg must not copy the raw image; it must upload it, run the
        rmbg workflow and land THAT result as apose.png."""
        folder = d3.npc_3d_folder(self.folder_path)
        folder.mkdir(parents=True)
        args = self.args(["--image", str(self.opaque), "--remove-bg"])
        cut = write_png(self.root / "cut-result.png", alpha=0, blob=(1, 1, 4, 4))

        def fake_cut(comfy, args_, entry, source, folder_):
            (folder_ / "apose.png").write_bytes(cut.read_bytes())
            return folder_ / "apose.png"

        with mock.patch.object(d3, "cut_out", side_effect=fake_cut) as cut_out:
            apose = d3.install_image(mock.Mock(), args,
                                     d3.subject_of(self.entry, args), folder)
        self.assertTrue(cut_out.called, "--remove-bg did not run the cut")
        self.assertEqual(apose.read_bytes(), cut.read_bytes())
        self.assertNotEqual(apose.read_bytes(), self.opaque.read_bytes())

    def test_without_remove_bg_no_server_is_touched(self):
        """A cut-out image needs no ComfyUI job at all before the mesh stage."""
        folder = d3.npc_3d_folder(self.folder_path)
        folder.mkdir(parents=True)
        with mock.patch.object(d3, "cut_out",
                               side_effect=AssertionError("cut_out must not run")):
            args = self.args(["--image", str(self.cutout)])
            d3.install_image(None, args, d3.subject_of(self.entry, args), folder)

    # -- end to end through main() -----------------------------------------

    def test_dry_run_names_the_image_instead_of_a_prompt(self):
        """--image means no prompt is ever built, so printing one would be
        describing a render that is not going to happen."""
        entry = manifest_entry(72)
        manifest_path = self.root / "dry.json"
        manifest_path.write_text(
            json.dumps({str(self.root / "run" / entry["name"]): entry}),
            encoding="utf-8")
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = d3.main(["--manifest", str(manifest_path), "--dry-run",
                            "--image", str(self.cutout)])
        self.assertEqual(code, 0)
        self.assertIn(str(self.cutout), buffer.getvalue())
        self.assertNotIn("A-pose token prompt", buffer.getvalue())

    def test_main_reconstructs_from_the_supplied_image(self):
        """No A-pose render is queued, and stage_mesh sees the copied file."""
        entry = manifest_entry(71)
        manifest_path = self.root / "manifest.json"
        folder_path = self.root / "run" / entry["name"]
        manifest_path.write_text(
            json.dumps({str(folder_path): entry}), encoding="utf-8")
        seen = {}

        def fake_mesh(comfy, args, entry_, folder, apose_png):
            seen["apose"] = Path(apose_png)
            return folder / "_shell.glb", folder / "_base.glb"

        fake_comfy = mock.Mock()
        fake_comfy.base = "http://fake"
        with mock.patch.object(d3.art, "find_server", return_value=fake_comfy), \
             mock.patch.object(d3, "find_blender", return_value=Path("blender.exe")), \
             mock.patch.object(d3, "stage_apose",
                               side_effect=AssertionError(
                                   "--image must not render an A-pose")), \
             mock.patch.object(d3, "stage_mesh", side_effect=fake_mesh), \
             mock.patch.object(d3, "stage_assemble",
                               return_value={"files": ["X.glb"]}):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = d3.main(["--manifest", str(manifest_path),
                                "--image", str(self.cutout)])

        self.assertEqual(code, 0, buffer.getvalue())
        self.assertEqual(seen["apose"].read_bytes(), self.cutout.read_bytes())
        self.assertEqual(seen["apose"].name, "apose.png")


class TestSubject(unittest.TestCase):
    """The five things a reconstruction needs to know about who it is of.

    Name, ComfyUI output category, slug, seed and real height - and nothing
    else. Naming them explicitly is what lets a standalone image reach the
    same stages a manifest entry does, instead of a second code path beside
    them.
    """

    def test_an_entry_carries_its_rolled_height(self):
        """Regression on the refactor: the NPC's own Height, not an estimate."""
        entry = manifest_entry(81, {"Height": "a solid five foot nine or so"})
        subject = d3.subject_of(entry, d3.parse_args([]))
        self.assertAlmostEqual(subject.height, 1.7526, places=3)

    def test_an_entry_with_no_parseable_height_gets_none(self):
        entry = manifest_entry(82, {"Height": "of average height"})
        self.assertIsNone(d3.subject_of(entry, d3.parse_args([])).height)

    def test_an_entry_keeps_its_name_and_seed(self):
        entry = manifest_entry(83)
        subject = d3.subject_of(entry, d3.parse_args([]))
        self.assertEqual(subject.name, entry["name"])
        self.assertEqual(subject.seed, entry["seed"])

    def test_height_m_overrides_a_rolled_height(self):
        """An override that silently did nothing in NPC mode would be a trap."""
        entry = manifest_entry(84, {"Height": "a solid five foot nine or so"})
        subject = d3.subject_of(entry, d3.parse_args(["--height-m", "2.1"]))
        self.assertEqual(subject.height, 2.1)


class TestStandalone(unittest.TestCase):
    """--out: reconstruct an image that is nobody's token.

    A custom PNG has no manifest entry, so there is no seed to reuse, no role
    category, no rolled height and no dossier to append to. --out supplies the
    one thing such a run cannot infer - where the results go - and switches
    off everything that reads the manifest.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cutout = write_png(self.root / "apose_rmbg_00011_.png",
                                alpha=0, blob=(2, 2, 5, 5))
        self.out = self.root / "jules"

    def args(self, argv):
        return d3.parse_args(argv)

    def standalone(self, *extra):
        return self.args(["--image", str(self.cutout), "--out", str(self.out)]
                         + list(extra))

    # -- the flag pair ------------------------------------------------------

    def test_out_without_an_image_is_refused(self):
        """There is no NPC to render, so there is nothing to reconstruct from."""
        with self.assertRaises(SystemExit):
            self.args(["--out", str(self.out)])

    def test_out_with_a_selection_flag_is_refused(self):
        """--out reads no manifest, so an NPC selection cannot mean anything."""
        for flag, value in (("--id", "npc-x-1"), ("--filter", "Crew"),
                            ("--exclude", "Pilots"), ("--limit", "3")):
            with self.subTest(flag=flag):
                with self.assertRaises(SystemExit):
                    self.standalone(flag, value)

    def test_no_out_by_default(self):
        self.assertIsNone(self.args([]).out)

    def test_name_without_out_is_refused(self):
        """An NPC's deliverables are named after the NPC, so --name would
        silently do nothing rather than renaming anything."""
        with self.assertRaises(SystemExit):
            self.args(["--name", "Jules"])

    # -- who the subject is -------------------------------------------------

    def test_the_name_defaults_to_the_output_folder(self):
        """Not the image stem: apose_rmbg_00011_ is ComfyUI's counter, and it
        would end up in the deliverable filenames."""
        self.assertEqual(d3.standalone_subject(self.standalone()).name, "jules")

    def test_name_overrides_the_folder(self):
        subject = d3.standalone_subject(self.standalone("--name", "Jules Sokolova"))
        self.assertEqual(subject.name, "Jules Sokolova")

    def test_height_m_reaches_the_subject(self):
        subject = d3.standalone_subject(self.standalone("--height-m", "1.75"))
        self.assertEqual(subject.height, 1.75)

    def test_no_height_is_none_not_zero(self):
        """assemble_npc.py falls back to the estimate on a missing flag, and
        --real-height-m 0 would scale the figure out of existence."""
        self.assertIsNone(d3.standalone_subject(self.standalone()).height)

    def test_the_slug_is_derived_from_the_name(self):
        """art._slug keeps the case, as the real ComfyUI tree shows:
        output/LancerNPCs/Pilots/Jules-Sokolova/."""
        subject = d3.standalone_subject(self.standalone("--name", "Jules Sokolova"))
        self.assertEqual(subject.slug, "Jules-Sokolova")

    # -- clobber protection still applies -----------------------------------

    def test_an_existing_apose_in_the_out_folder_is_not_clobbered(self):
        self.out.mkdir(parents=True)
        write_png(self.out / "apose.png", alpha=0, blob=(1, 1, 3, 3))
        with self.assertRaises(SystemExit) as caught:
            d3.check_image(self.standalone(), [self.out])
        self.assertIn("--overwrite", str(caught.exception))

    # -- end to end through main() ------------------------------------------

    def run_standalone(self, *extra):
        """main() with the two ComfyUI stages and Blender patched out."""
        seen = {}

        def fake_mesh(comfy, args, subject, folder, apose_png):
            seen["apose"] = Path(apose_png)
            seen["subject"] = subject
            return folder / "_shell.glb", folder / "_base.glb"

        def fake_assemble(args, folder, stem, base, shell, height=None):
            seen["stem"] = stem
            seen["height"] = height
            seen["folder"] = Path(folder)
            return {"files": ["%s Shell.glb" % stem]}

        fake_comfy = mock.Mock()
        fake_comfy.base = "http://fake"
        with mock.patch.object(d3.art, "find_server", return_value=fake_comfy), \
             mock.patch.object(d3, "find_blender", return_value=Path("blender.exe")), \
             mock.patch.object(d3, "stage_apose",
                               side_effect=AssertionError(
                                   "a standalone run must not render an A-pose")), \
             mock.patch.object(d3, "stage_mesh", side_effect=fake_mesh), \
             mock.patch.object(d3, "stage_assemble", side_effect=fake_assemble):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                seen["code"] = d3.main(
                    ["--image", str(self.cutout), "--out", str(self.out)]
                    + list(extra))
        seen["stdout"] = buffer.getvalue()
        return seen

    def test_it_runs_with_no_manifest_on_disk_at_all(self):
        """The manifest default points at a real path on the author's machine.
        A standalone run must not read it, or even require it to exist."""
        seen = self.run_standalone("--manifest", str(self.root / "absent.json"))
        self.assertEqual(seen["code"], 0, seen["stdout"])

    def test_the_image_lands_in_the_out_folder(self):
        seen = self.run_standalone()
        self.assertEqual(seen["apose"], self.out / "apose.png")
        self.assertEqual(seen["apose"].read_bytes(), self.cutout.read_bytes())

    def test_the_out_folder_is_created(self):
        self.assertFalse(self.out.exists())
        self.run_standalone()
        self.assertTrue(self.out.is_dir())

    def test_the_deliverables_are_named_after_the_folder(self):
        seen = self.run_standalone()
        self.assertEqual(seen["stem"], "jules")

    def test_name_reaches_the_deliverables(self):
        seen = self.run_standalone("--name", "Jules Sokolova")
        self.assertEqual(seen["stem"], "Jules Sokolova")

    def test_height_m_reaches_the_assembly(self):
        seen = self.run_standalone("--height-m", "1.75")
        self.assertEqual(seen["height"], 1.75)

    def test_nothing_is_tracked(self):
        """No dossier, no manifest write - a standalone run leaves only the
        files in --out."""
        seen = self.run_standalone()
        self.assertEqual(sorted(p.name for p in self.out.iterdir()), ["apose.png"])
        self.assertNotIn("dossier", seen["stdout"].lower())


class TestTextureFlags(unittest.TestCase):
    def test_texture_is_a_stage(self):
        self.assertEqual(d3.STAGES, ("apose", "mesh", "assemble", "texture"))

    def test_all_four_stages_by_default(self):
        self.assertEqual(d3.parse_args([]).stage, list(d3.STAGES))

    def test_texture_runs_in_isolation(self):
        self.assertEqual(d3.parse_args(["--stage", "texture"]).stage, ["texture"])

    def test_texturing_is_on_by_default(self):
        """Unlike --rig. This is the point of the exercise, not an experiment."""
        self.assertTrue(d3.parse_args([]).texture)

    def test_no_texture_turns_it_off(self):
        self.assertFalse(d3.parse_args(["--no-texture"]).texture)

    def test_no_texture_leaves_the_stage_list_alone(self):
        """should_skip() compares the stage set against STAGES. Dropping
        'texture' from it would quietly stop a --no-texture batch skipping
        NPCs that already have a 3d/ folder."""
        self.assertEqual(d3.parse_args(["--no-texture"]).stage, list(d3.STAGES))

    def test_no_texture_with_stage_texture_is_refused(self):
        with self.assertRaises(SystemExit):
            d3.parse_args(["--stage", "texture", "--no-texture"])

    def test_the_atlas_defaults_to_2048(self):
        self.assertEqual(d3.parse_args([]).texture_size, 2048)

    def test_the_atlas_size_is_settable(self):
        self.assertEqual(d3.parse_args(["--texture-size", "4096"]).texture_size,
                         4096)

    def test_the_back_view_is_on_by_default(self):
        self.assertTrue(d3.parse_args([]).back_view)

    def test_no_back_view_turns_it_off(self):
        self.assertFalse(d3.parse_args(["--no-back-view"]).back_view)


class TestFrontMargin(unittest.TestCase):
    def test_it_is_squared_aposes_own_margin(self):
        """Spec §4.2 says 1.12; square_apose() has always used 1.06. The two
        framings are the same rule, so the camera takes the constant the image
        was actually built with - derived, never restated."""
        self.assertAlmostEqual(d3.FRONT_MARGIN, 1 + d3.APOSE_MARGIN)

    def test_it_reaches_the_blender_command(self):
        command = d3.texture_command(
            Path("blender.exe"), d3.parse_args([]), Path("/3d"), "Name",
            Path("/3d/Name Shell.glb"), "bake", front=Path("/3d/sq.png"))
        self.assertEqual(command[command.index("--front-margin") + 1],
                         str(d3.FRONT_MARGIN))


class TestTextureCommand(unittest.TestCase):
    def setUp(self):
        self.args = d3.parse_args([])
        self.shell = Path("/3d/Name Shell.glb")

    def build(self, step, **kwargs):
        return d3.texture_command(Path("blender.exe"), self.args, Path("/3d"),
                                  "Name", self.shell, step, **kwargs)

    def test_the_back_step_names_the_script_and_the_step(self):
        command = self.build("back")
        self.assertIn(str(d3.TEXTURE_SCRIPT), command)
        self.assertEqual(command[command.index("--step") + 1], "back")

    def test_the_back_step_passes_no_front(self):
        self.assertNotIn("--front", self.build("back"))

    def test_the_bake_step_passes_the_front_and_the_size(self):
        command = self.build("bake", front=Path("/3d/sq.png"))
        self.assertEqual(command[command.index("--front") + 1],
                         str(Path("/3d/sq.png")))
        self.assertEqual(command[command.index("--size") + 1], "2048")

    def test_the_bake_step_omits_back_when_there_is_none(self):
        self.assertNotIn("--back", self.build("bake", front=Path("/3d/sq.png")))

    def test_the_bake_step_passes_back_when_there_is_one(self):
        command = self.build("bake", front=Path("/3d/sq.png"),
                             back=Path("/3d/back.png"))
        self.assertEqual(command[command.index("--back") + 1],
                         str(Path("/3d/back.png")))

    def test_the_stem_reaches_the_command_unsplit(self):
        """A two-word name must arrive as one argv element, not two."""
        command = d3.texture_command(
            Path("blender.exe"), self.args, Path("/3d"), "Jules Sokolova",
            self.shell, "back")
        self.assertIn("Jules Sokolova", command)


class TestTextureDossier(unittest.TestCase):
    def test_the_texture_file_is_listed(self):
        body = d3.dossier_3d_section(
            ["Name Shell.glb", "Name Texture.png"], [Path("A.json")], "standing")
        self.assertIn("- `3d/Name Texture.png`", body)

    def test_a_back_stance_is_recorded_when_there_was_one(self):
        body = d3.dossier_3d_section(
            ["Name Shell.glb"], [Path("A.json")], "standing",
            back_stance="back to the viewer")
        self.assertIn("back to the viewer", body)

    def test_no_back_row_without_a_back_view(self):
        body = d3.dossier_3d_section(
            ["Name Shell.glb"], [Path("A.json")], "standing")
        self.assertNotIn("Back-view stance", body)


class TestTextureContainment(unittest.TestCase):
    """Spec §5.3: a texture failure costs the texture and nothing else."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self._tmp.name)
        self.shell = self.folder / "Name Shell.glb"
        self.shell.write_bytes(b"the good shell")
        (self.folder / "apose_square.png").write_bytes(b"not really a png")
        self.args = d3.parse_args(["--no-back-view"])

    def tearDown(self):
        self._tmp.cleanup()

    def test_a_failed_bake_leaves_the_shell_untouched(self):
        with mock.patch.object(d3, "run_texture_step",
                               side_effect=RuntimeError("bake exploded")):
            with self.assertRaises(RuntimeError):
                d3.stage_texture(None, self.args, None, self.folder, "Name")
        self.assertEqual(self.shell.read_bytes(), b"the good shell")

    def test_a_crash_after_a_partial_write_leaves_the_shell_untouched(self):
        def half_done(*a, **k):
            (self.folder / "_Name Texture.png").write_bytes(b"partial")
            raise RuntimeError("died during export")

        with mock.patch.object(d3, "run_texture_step", side_effect=half_done):
            with self.assertRaises(RuntimeError):
                d3.stage_texture(None, self.args, None, self.folder, "Name")
        self.assertEqual(self.shell.read_bytes(), b"the good shell")
        self.assertFalse((self.folder / "Name Texture.png").exists())

    def test_a_successful_bake_moves_both_temporaries_into_place(self):
        def succeed(*a, **k):
            (self.folder / "_Name Texture.png").write_bytes(b"the atlas")
            (self.folder / "_Name Shell.glb").write_bytes(b"the textured shell")
            return {"step": "bake", "texture": "_Name Texture.png",
                    "shell": "_Name Shell.glb", "size": 2048, "islands": 12,
                    "views": ["front"], "rigged": None,
                    "files": ["_Name Texture.png", "_Name Shell.glb"]}

        with mock.patch.object(d3, "run_texture_step", side_effect=succeed):
            report = d3.stage_texture(None, self.args, None, self.folder, "Name")
        self.assertEqual(self.shell.read_bytes(), b"the textured shell")
        self.assertEqual((self.folder / "Name Texture.png").read_bytes(),
                         b"the atlas")
        self.assertEqual(report["files"], ["Name Texture.png"])
        self.assertFalse((self.folder / "_Name Shell.glb").exists())

    def test_no_back_view_queues_no_comfyui_job(self):
        """comfy is None here: touching it at all is an AttributeError."""
        def succeed(*a, **k):
            (self.folder / "_Name Texture.png").write_bytes(b"a")
            (self.folder / "_Name Shell.glb").write_bytes(b"b")
            return {"texture": "_Name Texture.png", "shell": "_Name Shell.glb",
                    "views": ["front"], "files": []}

        with mock.patch.object(d3, "run_texture_step", side_effect=succeed):
            d3.stage_texture(None, self.args, None, self.folder, "Name")

    def test_a_missing_shell_names_the_stage_to_run(self):
        self.shell.unlink()
        with self.assertRaises(RuntimeError) as caught:
            d3.stage_texture(None, self.args, None, self.folder, "Name")
        self.assertIn("assemble", str(caught.exception))


class TestReferenceImage(unittest.TestCase):
    """The back-catalogue case: --stage texture on a folder built last week."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_an_existing_square_is_used_as_is(self):
        square = self.folder / "apose_square.png"
        square.write_bytes(b"already squared")
        self.assertEqual(d3.reference_image(self.folder), square)

    def test_it_is_rebuilt_from_apose_when_absent(self):
        """A pure function of apose.png - requiring --stage mesh to have run
        in this working copy would defeat the whole back-catalogue case."""
        with mock.patch.object(d3, "square_apose", return_value=800) as squared:
            (self.folder / "apose.png").write_bytes(b"a cutout")
            result = d3.reference_image(self.folder)
        squared.assert_called_once()
        self.assertEqual(result, self.folder / "apose_square.png")

    def test_neither_is_a_clear_failure(self):
        with self.assertRaises(RuntimeError) as caught:
            d3.reference_image(self.folder)
        self.assertIn("apose", str(caught.exception))


class TestTexturePreflight(unittest.TestCase):
    def test_the_texture_stage_checks_blender(self):
        args = d3.parse_args(["--stage", "texture"])
        args.blender = Path("nowhere/blender.exe")
        with self.assertRaises(SystemExit):
            d3.preflight(args)

    def test_no_texture_checks_nothing_it_will_not_open(self):
        d3.preflight(d3.parse_args(["--no-texture", "--stage", "apose"]))
