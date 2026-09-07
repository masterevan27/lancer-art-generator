"""save_manifest() never leaves a half-written manifest behind.

The manifest is not a private file. The Import GUI re-reads it every two
seconds while a job runs, and answers an unparseable one with an empty list -
which reads to the browser as "the library is empty" and stops its poller
mid-job. A truncate-and-write puts that window at the very end of a regen,
milliseconds before the child exits, so the one poll most likely to land in it
is the one watching for the transition the poller exists to see.

Writing a sibling temp file and renaming closes the window: os.replace is
atomic on both POSIX and Windows when source and destination share a
directory, so a reader sees either the whole old file or the whole new one.
The sibling part is load-bearing rather than tidy - a temp file on another
filesystem makes the rename a copy, and the atomicity goes with it.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test.helpers import load_generator

art = load_generator().art

BEFORE = {"npcs/one": {"id": "npc-1", "seed": 1}}
AFTER = {"npcs/one": {"id": "npc-1", "seed": 2}}


class SaveManifestIsAtomic(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.path = Path(self.dir.name) / ".generated-npcs.json"
        self.path.write_text(json.dumps(BEFORE), encoding="utf-8")

    def test_the_new_manifest_is_what_ends_up_on_disk(self):
        art.save_manifest(self.path, AFTER)
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), AFTER)

    def test_a_successful_write_leaves_no_temp_file_behind(self):
        art.save_manifest(self.path, AFTER)
        self.assertEqual(
            sorted(p.name for p in Path(self.dir.name).iterdir()),
            [self.path.name],
            "the temp file should have been renamed onto the manifest, not "
            "left beside it")

    def test_the_temp_file_is_a_sibling_of_the_manifest(self):
        # Not decoration: os.replace is only atomic within one filesystem, so
        # a temp file written to /tmp - or anywhere but the manifest's own
        # directory - degrades the rename to a copy and reopens the window
        # this whole function exists to close.
        seen = []
        real = os.replace
        with mock.patch.object(os, "replace",
                               lambda src, dst: (seen.append(src), real(src, dst))[1]):
            art.save_manifest(self.path, AFTER)
        self.assertEqual(len(seen), 1)
        self.assertEqual(Path(seen[0]).parent, self.path.parent)

    def test_a_write_that_fails_leaves_the_old_manifest_intact(self):
        """The failure the GUI actually sees is a reader arriving mid-write
        rather than the writer crashing, but the two are the same defect: a
        destination that is only ever replaced whole cannot be read - or left -
        in a state that was never a manifest."""
        with mock.patch.object(os, "replace", side_effect=OSError("no rename")):
            with self.assertRaises(OSError):
                art.save_manifest(self.path, AFTER)
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), BEFORE)


if __name__ == "__main__":
    unittest.main()
