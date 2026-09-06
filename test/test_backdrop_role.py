"""A Backdrop scene that asserts an occupation reaches that job and no other.

BACKDROP_ROLES is the second hard filter in the tables, after ROLE_LOCKS, and
it is here for the same reason: most of the Backdrop table is places, and a
place fits anyone, but a scene that puts the subject mid-action is a claim
about the person. A bar owner and information broker annotating a clipboard on
a maintenance gantry is not an odd pairing but a wrong one, so
filter_by_backdrop_role() alone does not fall back to the whole pool - which
makes the guard that its pool cannot empty this file's job rather than the
function's.

The margin here is much wider than the Gear lock's: some 180 of the table's
269 bullets carry no occupation flag at all and stay reachable by everyone.
TestTheLiveTables holds that margin against both filters that narrow this
table, since the theme roll runs first and the role filter must survive
whatever it leaves - the one combination that could actually empty a pool.

Rolls against a fixture of its own rather than tables-minimal.md, for the two
reasons test_role_lock.py gives: adding to the shared fixture would shift the
random stream every other test file draws from, and the flagged bullet has to
be reachable here or every assertion below passes on nothing at all.
"""
import random
import unittest

from test.helpers import FIXTURE_TABLES, REPO, bullets_for, load_generator

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")

DOCKER = "a dockworker"                  # Laborers
ADMIN = "a colonial administrator"       # Officials
SOLDIER = "a Union marine soldier"       # Soldiers

PLAIN = "A half-body character portrait || Behind {object} is a plain wall."
GANTRY = ("A character portrait || {Subject} {is_are} on a gantry with a "
          "wrench. || mechwork")
AUDIT = ("A character portrait || {Subject} {is_are} at a bare interview "
         "table. || inspection")

# 'mechwork' is a bucket entry and reaches the fixture's dockworker through
# Laborers; 'inspection' is a bucket entry reaching only the administrator.
# Both are needed: one proves a flag admits the right bucket, the other proves
# the same flag list excludes it, and a fixture carrying one alone could not
# tell a working filter from one that dropped everything.
EXTRA_BACKDROPS = ["- " + GANTRY, "- " + AUDIT]


def fixture_with_gates(tmpdir):
    """tables-minimal.md plus the flagged backdrops, written under `tmpdir`."""
    lines = FIXTURE_TABLES.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines:
        out.append(line)
        if line.strip() == "## Backdrop":
            out.extend(EXTRA_BACKDROPS)
    path = tmpdir / "tables-gated.md"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return gen.parse_tables(path)


class TestTheFilter(unittest.TestCase):
    """filter_by_backdrop_role() on its own, before any rolling."""

    def test_an_unflagged_scene_reaches_everyone(self):
        pool = [PLAIN, "A character portrait || {Subject} {is_are} in a bar."]
        for role in (DOCKER, ADMIN, SOLDIER, "a mech pilot"):
            self.assertEqual(gen.filter_by_backdrop_role(pool, role), pool)

    def test_a_bucket_flag_reaches_every_role_in_that_bucket(self):
        pool = [GANTRY]
        for role in ("a chief mechanic", "a maintenance technician",
                     DOCKER, "a freelance salvager", "a mech pilot"):
            self.assertEqual(gen.filter_by_backdrop_role(pool, role), pool)

    def test_a_bucket_flag_reaches_nobody_outside_it(self):
        pool = [GANTRY]
        for role in (ADMIN, SOLDIER, "a bar owner and information broker",
                     "a field medic", "a pirate"):
            self.assertEqual(gen.filter_by_backdrop_role(pool, role), [])

    def test_the_case_this_filter_was_written_for(self):
        """The clipboard-on-an-inspection-gantry scene, off the bar owner.

        Stated as its own case because it is the report this feature came from
        and the one a later reader will want to find: the live bullet, the live
        Role, and the exact pairing that used to roll.
        """
        live = [b for b in bullets_for(LIVE, "Backdrop")
                if "annotating a clipboard" in b]
        self.assertEqual(len(live), 1,
                         "expected exactly one clipboard gantry scene, got %d "
                         "- this test names a bullet that has moved" % len(live))
        self.assertEqual(
            gen.filter_by_backdrop_role(live,
                                        "a bar owner and information broker"),
            [])
        self.assertEqual(gen.filter_by_backdrop_role(live, "a chief mechanic"),
                         live)

    def test_a_role_flag_reaches_the_one_role_it_names(self):
        """Four entries name an exact Role bullet rather than a bucket, because
        the bucket is too coarse: 'Civilians' holds the bar owner, the data
        courier and the scavenger-priest alike."""
        pool = ["A character portrait || {Subject} {is_are} behind the bar. "
                "|| barkeep"]
        owner = "a bar owner and information broker"
        self.assertEqual(gen.filter_by_backdrop_role(pool, owner), pool)
        for role in ("a data courier",
                     "a scavenger-priest of a local machine cult", DOCKER):
            self.assertEqual(gen.filter_by_backdrop_role(pool, role), [],
                             "%r shares a bucket with %r but not the job"
                             % (role, owner))

    def test_a_gate_survives_alongside_a_behavioural_flag(self):
        """'|| nogear weather medic' is three flags and only one is a gate. A
        filter reading the segment as a single token would drop the bullet for
        the medic too."""
        pool = ["A character portrait || {Subject} {is_are} in a triage tent. "
                "|| nogear weather medic"]
        self.assertEqual(gen.filter_by_backdrop_role(pool, "a field medic"),
                         pool)

    def test_a_gate_survives_alongside_a_theme_tag(self):
        pool = ["A character portrait || {Subject} {is_are} on a gantry. "
                "|| nogear mechwork @gundam"]
        self.assertEqual(gen.filter_by_backdrop_role(pool, "a chief mechanic"),
                         pool)
        self.assertEqual(gen.filter_by_backdrop_role(pool, ADMIN), [])

    def test_an_unknown_flag_is_not_a_gate(self):
        """Flags are matched literally and an unrecognized one is ignored
        everywhere else in this file; a filter treating any unknown flag as a
        gate would silently empty pools on a typo."""
        pool = [PLAIN + " || notaflag"]
        self.assertEqual(gen.filter_by_backdrop_role(pool, DOCKER), pool)

    def test_flags_are_read_from_the_third_segment(self):
        """A Backdrop keeps its flags in the THIRD segment. A filter reading
        them with split_flags(), which takes the second, would read the scene
        sentence as a flag list - the trap flags_for() exists to cover."""
        scene = ("A character portrait || {Subject} {is_are} a mechwork "
                 "barkeep in a cockpit.")
        self.assertEqual(gen.filter_by_backdrop_role([scene], ADMIN), [scene])

    def test_it_does_not_fall_back_to_the_whole_pool(self):
        """The second filter in the generator allowed to return nothing. If
        this ever grows an 'or options' fallback, the gate stops meaning
        anything the moment it is the only bullet left."""
        self.assertEqual(gen.filter_by_backdrop_role([GANTRY], ADMIN), [])


class TestRolledNPCs(unittest.TestCase):
    """The filter as roll_npc() actually applies it."""

    @classmethod
    def setUpClass(cls):
        import tempfile
        from pathlib import Path
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tables = fixture_with_gates(Path(cls._tmp.name))
        cls.rolls = [gen.roll_npc(cls.tables, random.Random(seed))
                     for seed in range(600)]

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    # Matched on a distinctive phrase rather than on the whole scene, because
    # roll_npc() has already filled the '{Subject} {is_are}' slots by the time
    # the bullet reaches npc["Backdrop"] - the stored text is "She is on a
    # gantry...", never the template it came from.
    GANTRY_PHRASE = "on a gantry with a wrench"
    AUDIT_PHRASE = "at a bare interview table"

    def _scene(self, npc):
        return gen.split_backdrop(npc["Backdrop"])[1]

    def test_the_gated_scenes_are_reachable(self):
        """Without this every assertion below passes on an empty set."""
        scenes = [self._scene(n) for n in self.rolls]
        for phrase in (self.GANTRY_PHRASE, self.AUDIT_PHRASE):
            self.assertTrue(
                any(phrase in s for s in scenes),
                "no roll in %d produced %r - the fixture cannot reach it, so "
                "this file tests nothing" % (len(self.rolls), phrase))

    def test_only_the_admitted_bucket_rolls_the_gantry(self):
        for npc in self.rolls:
            if self.GANTRY_PHRASE in self._scene(npc):
                self.assertEqual(
                    npc["Role"], DOCKER,
                    "%r rolled a scene gated to Laborers" % npc["Role"])

    def test_only_the_admitted_bucket_rolls_the_audit(self):
        for npc in self.rolls:
            if self.AUDIT_PHRASE in self._scene(npc):
                self.assertEqual(
                    npc["Role"], ADMIN,
                    "%r rolled a scene gated to Officials" % npc["Role"])

    def test_the_pool_never_empties(self):
        """A Role that could reach no Backdrop at all would raise out of
        rng.choice(). Every NPC above rolled one, which is the assertion -
        stated explicitly so the reason this file cares is on the record."""
        self.assertTrue(all(npc["Backdrop"] for npc in self.rolls))


class TestTheLiveTables(unittest.TestCase):
    """The ways a gate goes stale without anything failing."""

    BEHAVIOURAL = ("nogear", "weather")

    def test_every_flag_in_the_file_is_defined(self):
        for bullet in bullets_for(LIVE, "Backdrop"):
            for flag in gen.split_backdrop(bullet)[2]:
                if flag in self.BEHAVIOURAL or flag.startswith("@"):
                    continue
                self.assertIn(
                    flag, gen.BACKDROP_ROLES,
                    "%r on a Backdrop bullet is neither a known behavioural "
                    "flag nor a gate defined in BACKDROP_ROLES. An "
                    "unrecognized flag is ignored rather than reported, so the "
                    "scene is simply ungated: %r" % (flag, bullet))

    def test_every_gate_names_something_that_still_exists(self):
        """An entry is either a ROLE_CATEGORIES bucket or an exact Role bullet.
        Both match on literal text, so a reworded Role or a renamed bucket
        leaves the gate excluding everyone and its scenes unrollable."""
        roles = {gen.split_flags(b)[0] for b in bullets_for(LIVE, "Role")}
        buckets = set(gen.ROLE_CATEGORIES.values())
        for flag, admitted in sorted(gen.BACKDROP_ROLES.items()):
            for name in admitted:
                self.assertTrue(
                    name in buckets or name in roles,
                    "BACKDROP_ROLES[%r] names %r, which is neither a "
                    "ROLE_CATEGORIES bucket nor a bullet the Role table still "
                    "carries" % (flag, name))

    def test_every_gate_admits_at_least_one_role(self):
        """A gate nobody can satisfy is a set of scenes that never render."""
        roles = [gen.split_flags(b)[0] for b in bullets_for(LIVE, "Role")]
        for flag in sorted(gen.BACKDROP_ROLES):
            pool = ["x || y || %s" % flag]
            reachable = [r for r in roles
                         if gen.filter_by_backdrop_role(pool, r)]
            self.assertTrue(
                reachable,
                "no live Role satisfies %r, so every scene carrying it is "
                "unrollable" % flag)

    def test_every_gate_is_still_in_use(self):
        """A gate nothing carries is one that will be attached to the wrong
        thing by someone who assumed it was already load-bearing."""
        used = set()
        for bullet in bullets_for(LIVE, "Backdrop"):
            used |= set(gen.split_backdrop(bullet)[2])
        for flag in sorted(gen.BACKDROP_ROLES):
            self.assertIn(flag, used,
                          "BACKDROP_ROLES defines %r but no Backdrop bullet "
                          "carries it - drop it, or flag the scene it was for."
                          % flag)

    def test_the_neutral_pool_stays_the_bulk_of_the_table(self):
        """The reason filter_by_backdrop_role() may return nothing is that it
        cannot. Gating is meant to be the exception; this fails long before a
        roll could actually crash."""
        pool = bullets_for(LIVE, "Backdrop")
        neutral = [b for b in pool
                   if not (set(gen.split_backdrop(b)[2]) & set(gen.BACKDROP_ROLES))]
        self.assertGreater(
            len(neutral), len(pool) // 2,
            "only %d of %d Backdrop bullets are ungated - gates have been "
            "applied far too widely" % (len(neutral), len(pool)))

    def test_the_live_pool_survives_every_role_under_every_theme(self):
        """The theme roll narrows this table before the role filter does, so
        the combination is what has to survive, not either filter alone. This
        is the assertion that would catch a theme whose whole tagged set was
        gated to one occupation."""
        pool = bullets_for(LIVE, "Backdrop")
        themes = [gen.split_flags(b)[0] for b in bullets_for(LIVE, "Theme")]
        roles = [gen.split_flags(b)[0] for b in bullets_for(LIVE, "Role")]
        for theme in themes:
            themed = gen.filter_by_theme(pool, theme, "Backdrop")
            for role in roles:
                left = gen.filter_by_backdrop_role(themed, role)
                self.assertGreater(
                    len(left), 20,
                    "only %d Backdrop bullets are reachable by %r under theme "
                    "%r" % (len(left), role, theme))


if __name__ == "__main__":
    unittest.main()
