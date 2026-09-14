"""The gate sidecar: a JSON file beside the tables that redefines who a gate
flag admits, so the Import GUI can edit ROLE_LOCKS, BACKDROP_ROLES,
WEAPON_ROLES, UNAFFILIATED_ROLES and ROLE_CATEGORIES without rewriting this
script.

The Python literals stay the defaults. A sidecar that names a map replaces
that map whole; one it leaves out is untouched, so a file written by an older
GUI keeps working after a new map is added here.
"""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from test.helpers import load_generator

gen = load_generator()

GATE_GLOBALS = ("ROLE_CATEGORIES", "ROLE_LOCKS", "BACKDROP_ROLES",
                "WEAPON_ROLES", "UNAFFILIATED_ROLES")


class GateCase(unittest.TestCase):
    """Every test mutates module globals through load_gates(), and the module
    is loaded once per process, so each one puts the defaults back."""

    def setUp(self):
        self._saved = {name: getattr(gen, name) for name in GATE_GLOBALS}
        self._tmp = tempfile.TemporaryDirectory()
        self.tables = Path(self._tmp.name) / "npc-generator-tables.md"
        self.tables.write_text(
            "## Role\n- a mech pilot || mil\n- a Union inspector\n- a field medic || mil\n"
            "- a pirate\n- a smuggler\n- a colonial administrator\n",
            encoding="utf-8")

    def tearDown(self):
        for name, value in self._saved.items():
            setattr(gen, name, value)
        self._tmp.cleanup()

    def write_sidecar(self, data):
        path = gen.gates_path(self.tables)
        path.write_text(json.dumps(data), encoding="utf-8")
        return path


class TestThePath(unittest.TestCase):
    def test_the_sidecar_sits_beside_the_tables_file(self):
        tables = Path("/somewhere/prompts/npc-generator-tables.md")
        self.assertEqual(gen.gates_path(tables),
                         Path("/somewhere/prompts/npc-generator-tables.gates.json"))


class TestLoading(GateCase):
    def test_no_sidecar_leaves_every_default_alone(self):
        before = {name: getattr(gen, name) for name in GATE_GLOBALS}
        self.assertIsNone(gen.load_gates(self.tables))
        for name in GATE_GLOBALS:
            self.assertIs(getattr(gen, name), before[name], name)

    def test_a_sidecar_replaces_the_maps_it_names(self):
        self.write_sidecar({
            "roleLocks": {"badge": ["a Union inspector"]},
            "backdropRoles": {"cockpit": ["Pilots", "a field medic"]},
            "weaponRoles": {"blade": ["a pirate"]},
            "unaffiliatedRoles": ["a smuggler"],
            "roleCategories": {"a smuggler": "Officials"},
        })
        gen.load_gates(self.tables)
        self.assertEqual(gen.ROLE_LOCKS, {"badge": ("a Union inspector",)})
        self.assertEqual(gen.BACKDROP_ROLES,
                         {"cockpit": ("Pilots", "a field medic")})
        self.assertEqual(gen.WEAPON_ROLES, {"blade": ("a pirate",)})
        self.assertEqual(gen.UNAFFILIATED_ROLES, frozenset({"a smuggler"}))
        self.assertEqual(gen.ROLE_CATEGORIES, {"a smuggler": "Officials"})

    def test_a_map_the_sidecar_leaves_out_is_untouched(self):
        self.write_sidecar({"roleLocks": {"badge": ["a Union inspector"]}})
        gen.load_gates(self.tables)
        self.assertEqual(gen.ROLE_LOCKS, {"badge": ("a Union inspector",)})
        self.assertIs(gen.BACKDROP_ROLES, self._saved["BACKDROP_ROLES"])
        self.assertIs(gen.ROLE_CATEGORIES, self._saved["ROLE_CATEGORIES"])
        self.assertIs(gen.UNAFFILIATED_ROLES, self._saved["UNAFFILIATED_ROLES"])

    def test_the_filters_read_the_loaded_maps(self):
        """The maps are rebound rather than copied, so a filter that read a
        stale module-level reference would silently keep the defaults."""
        self.write_sidecar({"roleLocks": {"badge": ["a Union inspector"]}})
        gen.load_gates(self.tables)
        pool = ["a brass badge || badge", "a data-slate"]
        self.assertEqual(gen.filter_by_role_lock(pool, "a Union inspector"), pool)
        self.assertEqual(gen.filter_by_role_lock(pool, "a colonial administrator"),
                         ["a data-slate"])
        # 'admin' is no longer a lock at all once the sidecar replaced the map.
        self.assertEqual(gen.filter_by_role_lock(["a cane || admin"], "a dockworker"),
                         ["a cane || admin"])

    def test_malformed_json_names_the_file(self):
        path = gen.gates_path(self.tables)
        path.write_text("{not json", encoding="utf-8")
        with self.assertRaises(SystemExit) as caught:
            gen.load_gates(self.tables)
        self.assertIn(path.name, str(caught.exception))

    def test_a_wrongly_shaped_map_is_refused(self):
        for bad in (
            {"roleLocks": ["admin"]},
            {"roleLocks": {"admin": "a colonial administrator"}},
            {"roleCategories": {"a mech pilot": ["Pilots"]}},
            {"unaffiliatedRoles": "a freelance salvager"},
        ):
            self.write_sidecar(bad)
            with self.assertRaises(SystemExit, msg=json.dumps(bad)) as caught:
                gen.load_gates(self.tables)
            self.assertIn("gates.json", str(caught.exception))
            for name in GATE_GLOBALS:
                self.assertIs(getattr(gen, name), self._saved[name],
                              "a refused sidecar must not half-apply")

    def test_an_unknown_key_is_ignored(self):
        """A newer GUI may write a map this script does not read yet."""
        self.write_sidecar({"futureGate": {"x": ["y"]},
                            "roleLocks": {"badge": ["a Union inspector"]}})
        gen.load_gates(self.tables)
        self.assertEqual(gen.ROLE_LOCKS, {"badge": ("a Union inspector",)})

    def test_a_role_the_table_lacks_warns_rather_than_fails(self):
        self.write_sidecar({"roleLocks": {"badge": ["a role nobody rolls"]}})
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            gen.load_gates(self.tables)
        self.assertIn("a role nobody rolls", err.getvalue())
        self.assertEqual(gen.ROLE_LOCKS, {"badge": ("a role nobody rolls",)})


class TestBucketLocks(unittest.TestCase):
    """A ROLE_LOCKS entry may name a ROLE_CATEGORIES bucket, the way a
    BACKDROP_ROLES entry already may - so the GUI offers one shape of gate
    editor for both, and 'outlaw' can be written as ('Criminals',)."""

    def setUp(self):
        self._locks = gen.ROLE_LOCKS
        gen.ROLE_LOCKS = {"outlaw": ("Criminals",), "admin": ("a colonial administrator",)}

    def tearDown(self):
        gen.ROLE_LOCKS = self._locks

    def test_a_bucket_admits_every_role_in_it(self):
        pool = ["a tricorn || outlaw"]
        for role, bucket in gen.ROLE_CATEGORIES.items():
            expected = pool if bucket == "Criminals" else []
            self.assertEqual(gen.filter_by_role_lock(pool, role), expected, role)

    def test_an_exact_role_still_works_beside_a_bucket(self):
        pool = ["a cane || admin"]
        self.assertEqual(gen.filter_by_role_lock(pool, "a colonial administrator"), pool)
        self.assertEqual(gen.filter_by_role_lock(pool, "a pirate"), [])


if __name__ == "__main__":
    unittest.main()
