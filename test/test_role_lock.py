"""A Gear bullet locked to an occupation reaches that occupation and no other.

ROLE_LOCKS is the only hard filter in the tables. Every other one - 'notac',
'dressy', 'hardtech', the civ/mil split, the 'hands' and 'helmet' yields -
hands the whole pool back rather than roll nothing, because each is answering
"does this pairing read badly" and a slightly odd pairing beats a crash. A lock
answers something else: the lacquered cane is a colonial administrator's badge
of office, and on a dockworker it is not a badge of anything. Falling back
would hand it to precisely the Role it was kept from, so filter_by_role_lock()
alone does not fall back - which makes the guard that its pool cannot empty
this file's job rather than the function's.

Rolls against a fixture of its own rather than tables-minimal.md. Adding a
bullet to the shared fixture would shift the random stream every other test
file draws from, and the locked bullet has to be *reachable* here for these
assertions to mean anything - a fixture whose Gear table cannot produce it
would pass every test below on nothing at all.

The last class reads the live tables, for the two ways a lock goes stale
silently: a flag in the file that ROLE_LOCKS never defines (an unrecognized
flag is ignored rather than reported, so the bullet would simply be unlocked),
and a Role name in ROLE_LOCKS that the Role table has since reworded (the
match is on exact text, so the lock would exclude everyone).
"""
import random
import unittest

from test.helpers import FIXTURE_TABLES, REPO, bullets_for, load_generator

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")

ADMIN = "a colonial administrator"
CANE = "a lacquered cane of office held in one hand"
SEAL = "a heavy brass seal of office carried on a cord at the neck"
SLATE = "a battered data-slate"

# The minimal fixture with two locked Gear bullets added - one that occupies a
# hand and one that does not. Both are needed: the loop's Gear roll and the
# 'nogear' backdrop re-roll are separate code paths, and the re-roll narrows to
# non-hands bullets, so a fixture carrying only the hands one would leave that
# path untested. The Backdrop table gains a 'nogear' scene for the same reason.
EXTRA_GEAR = [
    "- %s || hands admin" % CANE,
    "- %s || admin" % SEAL,
]
NOGEAR_BACKDROP = (
    "- A dynamic character portrait || {Subject} {is_are} firing a sidearm "
    "toward the viewer. || nogear")


def fixture_with_locks(tmpdir):
    """tables-minimal.md plus the locked bullets, written under `tmpdir`."""
    text = FIXTURE_TABLES.read_text(encoding="utf-8")
    lines = text.splitlines()
    out = []
    for line in lines:
        out.append(line)
        if line.strip() == "## Gear":
            out.extend(EXTRA_GEAR)
        if line.strip() == "## Backdrop":
            out.append(NOGEAR_BACKDROP)
    path = tmpdir / "tables-locked.md"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return gen.parse_tables(path)


class TestTheFilter(unittest.TestCase):
    """filter_by_role_lock() on its own, before any rolling."""

    def test_an_unflagged_bullet_reaches_everyone(self):
        pool = ["%s || hands" % SLATE, "a canvas tool roll at the hip"]
        for role in (ADMIN, "a dockworker", "a Union marine soldier"):
            self.assertEqual(gen.filter_by_role_lock(pool, role), pool)

    def test_a_locked_bullet_reaches_the_role_it_names(self):
        pool = ["%s || hands admin" % CANE]
        self.assertEqual(gen.filter_by_role_lock(pool, ADMIN), pool)

    def test_a_locked_bullet_reaches_nobody_else(self):
        pool = ["%s || hands admin" % CANE]
        for role in ("a dockworker", "a Union inspector", "a mech pilot"):
            self.assertEqual(gen.filter_by_role_lock(pool, role), [])

    def test_a_lock_survives_alongside_a_behavioural_flag(self):
        """'|| hands admin' is two flags, and only one of them is a lock. A
        filter that read the flag segment as a single token would drop the
        bullet for the administrator too."""
        pool = ["%s || hands admin" % CANE]
        self.assertEqual(gen.filter_by_role_lock(pool, ADMIN), pool)

    def test_an_unknown_flag_is_not_a_lock(self):
        """Flags are matched literally and an unrecognized one is ignored
        everywhere else in this file; a filter that treated any unknown flag as
        a lock would silently empty pools on a typo."""
        pool = ["%s || hands notaflag" % SLATE]
        self.assertEqual(gen.filter_by_role_lock(pool, "a dockworker"), pool)

    def test_it_does_not_fall_back_to_the_whole_pool(self):
        """The one filter in the generator that is allowed to return nothing.
        If this ever grows an 'or options' fallback, the lock stops meaning
        anything the moment it is the only bullet left."""
        pool = ["%s || admin" % SEAL]
        self.assertEqual(gen.filter_by_role_lock(pool, "a dockworker"), [])


class TestRolledNPCs(unittest.TestCase):
    """The filter as roll_npc() actually applies it."""

    @classmethod
    def setUpClass(cls):
        import tempfile
        from pathlib import Path
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tables = fixture_with_locks(Path(cls._tmp.name))
        cls.rolls = [gen.roll_npc(cls.tables, random.Random(seed))
                     for seed in range(600)]

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_the_locked_items_are_reachable(self):
        """Without this every assertion below passes on an empty set."""
        admins = [n for n in self.rolls if n["Role"] == ADMIN]
        self.assertGreater(len(admins), 20,
                           "the fixture barely rolls administrators, so the "
                           "reachability check below proves little")
        carried = {n["Gear"] for n in admins}
        self.assertTrue(
            carried & {CANE, SEAL},
            "no administrator in %d rolls carried either locked item - the "
            "fixture cannot produce them, so this file tests nothing"
            % len(self.rolls))

    def test_nobody_else_carries_a_locked_item(self):
        for npc in self.rolls:
            if npc["Gear"] in (CANE, SEAL):
                self.assertEqual(
                    npc["Role"], ADMIN,
                    "%r carries %r, which is locked to %r"
                    % (npc["Role"], npc["Gear"], ADMIN))

    def test_a_nogear_scene_does_not_re_roll_onto_a_locked_item(self):
        """The 'nogear' correction re-draws from the raw Gear table rather than
        from the pool the loop narrowed, so every Gear filter has to be
        restated there. It is the one path that can hand an NPC a bullet the
        loop already screened out."""
        nogear = [n for n in self.rolls
                  if "nogear" in gen.split_backdrop(n["Backdrop"])[2]]
        self.assertGreater(len(nogear), 20,
                           "too few nogear scenes rolled to test the re-roll")
        for npc in nogear:
            if npc["Gear"] in (CANE, SEAL):
                self.assertEqual(
                    npc["Role"], ADMIN,
                    "a nogear scene re-rolled %r onto %r, which is locked to "
                    "%r" % (npc["Gear"], npc["Role"], ADMIN))

    def test_the_pool_never_empties(self):
        """A Role that could reach no Gear bullet at all would raise out of
        rng.choice(). Every NPC above rolled one, which is the assertion - it
        is stated explicitly so the reason this file cares is on the record."""
        self.assertTrue(all(npc["Gear"] for npc in self.rolls))


class TestTheLiveTables(unittest.TestCase):
    """The two ways a lock goes stale without anything failing."""

    def test_every_lock_flag_in_the_file_is_defined(self):
        for bullet in bullets_for(LIVE, "Gear"):
            for flag in gen.split_flags(bullet)[1]:
                if flag in ("hands", "mil", "helmet") or flag.startswith("@"):
                    continue
                self.assertIn(
                    flag, gen.ROLE_LOCKS,
                    "%r on a Gear bullet is neither a known behavioural flag "
                    "nor a lock defined in ROLE_LOCKS. An unrecognized flag is "
                    "ignored rather than reported, so the bullet is simply "
                    "unlocked: %r" % (flag, bullet))

    def test_every_lock_names_a_role_that_still_exists(self):
        roles = {gen.split_flags(b)[0] for b in bullets_for(LIVE, "Role")}
        for flag, locked_to in sorted(gen.ROLE_LOCKS.items()):
            for role in locked_to:
                self.assertIn(
                    role, roles,
                    "ROLE_LOCKS[%r] names %r, which the Role table no longer "
                    "carries - the match is on exact bullet text, so the lock "
                    "now excludes everyone and its bullets are unrollable."
                    % (flag, role))

    def test_every_lock_is_still_in_use(self):
        """A lock nothing carries is a lock that will one day be attached to
        the wrong thing by someone who assumed it was already load-bearing."""
        used = set()
        for bullet in bullets_for(LIVE, "Gear"):
            used |= set(gen.split_flags(bullet)[1])
        for flag in sorted(gen.ROLE_LOCKS):
            self.assertIn(flag, used,
                          "ROLE_LOCKS defines %r but no Gear bullet carries "
                          "it - drop it, or flag the bullet it was for."
                          % flag)

    def test_the_live_gear_pool_survives_every_role(self):
        """The reason filter_by_role_lock() may return nothing is that it
        cannot: the live table is overwhelmingly unlocked. This holds that
        margin, and would fail long before a roll actually crashed."""
        pool = bullets_for(LIVE, "Gear")
        for bullet in bullets_for(LIVE, "Role"):
            role = gen.split_flags(bullet)[0]
            left = gen.filter_by_role_lock(pool, role)
            self.assertGreater(
                len(left), 10,
                "only %d Gear bullets are reachable by %r - locks have been "
                "applied far too widely" % (len(left), role))


if __name__ == "__main__":
    unittest.main()
