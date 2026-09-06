"""A blade specialist is always carrying a blade.

"a close-quarters blade specialist" came back holding a service pistol and
nothing else, over and over, and the reason was structural rather than
unlucky. The Role is flagged 'mil', and apply_weapon_policy() restricts every
'mil' Role's pool to bullets flagged 'sidearm' - a holstered or openly worn
pistol - so that a soldier is always armed rather than usually. Not one of the
twenty-six blade bullets in the Weapon table carries 'sidearm', because none
of them is a pistol. The intersection was empty, and the specialist could not
reach a sword through the very filter that guaranteed them a gun.

So the fix is not another weight or another preference. WEAPON_ROLES names the
flag a Role's armament MUST carry, and it outranks the 'sidearm' restriction
rather than composing with it - composing is what produced the empty set.

The shape is deliberately ROLE_LOCKS'/BACKDROP_ROLES': a mapping from a flag
to the Roles it belongs to. It reads the opposite way round from ROLE_LOCKS,
though, and the difference is worth keeping straight:

  ROLE_LOCKS    this bullet is ONLY for these Roles   (keeps others out)
  WEAPON_ROLES  these Roles get ONLY this bullet      (keeps them in)

A lock protects an emblem from the wrong job. This protects a job from the
wrong emblem.
"""
import random
import unittest

from test.helpers import (
    FIXTURE_TABLES, REPO, bullets_for, load_generator, rendered)

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")

SPECIALIST = "a close-quarters blade specialist || mil"
SOLDIER = "a Union marine soldier || mil"
DOCKWORKER = "a dockworker"

KATANA = "a sheathed katana worn at the hip || hands mil weapon blade"
SWORD = "twin sheathed swords worn crosswise at the hip || mil weapon blade"
PISTOL = "a service pistol worn openly at the thigh || mil weapon simple sidearm"


def _blade_tables():
    """The shared fixture plus a blade specialist and two blades to give them.

    Built in memory rather than written into fixtures/tables-minimal.md for
    the reason the other conflict suites give: that file is the baseline for
    fixtures/roll-snapshot.json, and adding a bullet to a table moves every
    seed's draw from it.

    Two blades rather than one, so "always a blade" is measurably different
    from "always the same blade".
    """
    tables = gen.parse_tables(FIXTURE_TABLES)
    tables["Role"] = tables["Role"] + [SPECIALIST]
    tables["Weapon"] = tables["Weapon"] + [KATANA, SWORD]
    return tables


TABLES = _blade_tables()


def roll(seed, **overrides):
    return gen.roll_npc(TABLES, random.Random(seed), overrides or None)


def blades(tables):
    out = set()
    for bullet in bullets_for(tables, "Weapon"):
        if "blade" in gen.flags_for("Weapon", bullet):
            out |= rendered(tables, "Weapon", bullet)
    return out


class TestTheSpecialistIsAlwaysArmedWithABlade(unittest.TestCase):
    def test_every_seed_lands_on_a_blade(self):
        armed = blades(TABLES)
        self.assertTrue(armed, "fixture needs a blade to reach")
        for seed in range(400):
            npc = roll(seed, Role=SPECIALIST)
            self.assertIn(
                npc["Weapon"], armed,
                "seed %d: the blade specialist came back without a blade (%r)"
                % (seed, npc["Weapon"]))

    def test_the_specialist_never_lands_on_the_empty_bullet(self):
        """'none' is the unarmed bullet. A specialist in close-quarters blades
        is not sometimes unarmed."""
        for seed in range(400):
            npc = roll(seed, Role=SPECIALIST)
            self.assertTrue(npc["Weapon"].strip(), "seed %d: unarmed" % seed)

    def test_the_restriction_outranks_the_sidearm_one(self):
        """The actual bug. The Role is 'mil', so the sidearm restriction runs
        for it, and no blade bullet is a 'sidearm' - composing the two filters
        yields the empty set and falls back to the whole pool, which is how a
        blade specialist ended up holding a pistol."""
        pistols = rendered(TABLES, "Weapon", PISTOL)
        landed = sum(
            roll(seed, Role=SPECIALIST)["Weapon"] in pistols
            for seed in range(400))
        self.assertEqual(
            landed, 0,
            "the sidearm restriction is still winning over the blade one")

    def test_the_specialist_still_reaches_more_than_one_blade(self):
        """Variety, not just legality. A restriction that pins the roll to a
        single bullet has replaced a bug with a uniform."""
        seen = {roll(seed, Role=SPECIALIST)["Weapon"] for seed in range(400)}
        self.assertGreater(len(seen), 1)

    def test_the_flag_never_reaches_a_prompt(self):
        for seed in range(200):
            npc = roll(seed, Role=SPECIALIST)
            self.assertNotIn("blade ", npc["Weapon"].split("||")[0][-8:])
            self.assertNotIn("||", npc["Weapon"])
            for prompt in gen.build_prompts(npc):
                self.assertNotIn("|| blade", prompt)


class TestEveryOtherRoleIsUnaffected(unittest.TestCase):
    def test_an_ordinary_soldier_still_gets_a_sidearm(self):
        """The restriction is one Role's. Widening it to every 'mil' Role
        would arm the whole army with swords."""
        pistols = rendered(TABLES, "Weapon", PISTOL)
        landed = sum(
            roll(seed, Role=SOLDIER)["Weapon"] in pistols
            for seed in range(400))
        self.assertTrue(landed, "a marine lost the service pistol")

    def test_an_ordinary_soldier_is_not_forced_onto_a_blade(self):
        armed = blades(TABLES)
        seen = {roll(seed, Role=SOLDIER)["Weapon"] for seed in range(400)}
        self.assertTrue(seen - armed, "a marine was forced onto a blade")

    def test_a_civilian_is_still_often_unarmed(self):
        """The civilian tier still runs. The role restriction is a filter for
        the Roles it names and a no-op for every other.

        The floor is well under half on purpose. This fixture's empty bullet
        is 'x2' where the live table's is 'x30', so the unarmed share here is
        much lower than a real roll's - what is being asserted is that
        CIVILIAN_UNARMED_COPIES is still stacking the empty bullet at all, not
        a rate anyone should read off this number.
        """
        unarmed = sum(
            not roll(seed, Role=DOCKWORKER)["Weapon"].strip()
            for seed in range(400))
        self.assertGreater(unarmed, 120, "the dockworker stopped being quiet")

    def test_a_civilian_can_still_reach_a_blade(self):
        """'blade' restricts the Roles named in WEAPON_ROLES to blades. It is
        not a lock, so it does not reserve the blades FOR them - a pirate with
        a cutlass is still a pirate with a cutlass."""
        armed = blades(TABLES)
        reached = sum(
            roll(seed, Role=DOCKWORKER)["Weapon"] in armed
            for seed in range(400))
        self.assertTrue(reached, "the blades became one Role's private stock")


class TestItDegradesRatherThanAborts(unittest.TestCase):
    def test_a_tables_file_with_no_blade_flags_still_rolls(self):
        """Every filter in this generator hands the whole pool back rather
        than roll nothing. An untagged tables file must behave as it did
        before this change instead of erroring."""
        tables = dict(TABLES)
        tables["Weapon"] = [
            b for b in bullets_for(TABLES, "Weapon")
            if "blade" not in gen.flags_for("Weapon", b)]
        for seed in range(100):
            npc = gen.roll_npc(
                tables, random.Random(seed), {"Role": SPECIALIST})
            self.assertTrue(npc["Weapon"] is not None)


class TestTheMappingIsWellFormed(unittest.TestCase):
    def test_every_named_role_is_a_live_role_bullet(self):
        """The same guard test_role_lock.py and test_backdrop_role.py keep: a
        Role reworded in the tables file must not leave a dangling name
        here, silently switching the restriction off."""
        live = {gen.split_flags(b)[0] for b in bullets_for(LIVE, "Role")}
        for flag, roles in gen.WEAPON_ROLES.items():
            for role in roles:
                with self.subTest(flag=flag, role=role):
                    self.assertIn(
                        role, live,
                        "WEAPON_ROLES names a Role the table no longer has")

    def test_every_named_flag_is_carried_by_a_live_weapon(self):
        """The other end of the same wire. A flag no bullet carries restricts
        its Role to an empty pool, which falls back to the whole table - the
        exact silent no-op this feature exists to remove."""
        for flag in gen.WEAPON_ROLES:
            carriers = [b for b in bullets_for(LIVE, "Weapon")
                        if flag in gen.flags_for("Weapon", b)]
            with self.subTest(flag=flag):
                self.assertTrue(
                    carriers, "no live Weapon bullet carries %r" % flag)


class TestTheLiveTable(unittest.TestCase):
    def _flagged(self):
        return [gen.split_flags(b)[0] for b in bullets_for(LIVE, "Weapon")
                if "blade" in gen.flags_for("Weapon", b)]

    def test_the_blades_are_flagged(self):
        flagged = " ".join(self._flagged())
        for wanted in ("katana", "twin sheathed swords", "combat knife",
                       "push-dagger", "single-edged blade",
                       "two-handed blade"):
            with self.subTest(phrase=wanted):
                self.assertIn(wanted, flagged,
                              "%r is not flagged 'blade'" % wanted)

    def test_no_firearm_is_flagged_a_blade(self):
        flagged = " ".join(self._flagged())
        for unwanted in ("pistol", "carbine", "rifle", "shotgun", "revolver",
                         "submachine"):
            with self.subTest(phrase=unwanted):
                self.assertNotIn(unwanted, flagged,
                                 "%r is a firearm, not a blade" % unwanted)

    def test_every_blade_is_also_a_weapon(self):
        """'weapon' is what the unarmed and Officials tiers read. A blade that
        forgot it would slip past both."""
        for bullet in bullets_for(LIVE, "Weapon"):
            flags = gen.flags_for("Weapon", bullet)
            if "blade" not in flags:
                continue
            with self.subTest(bullet=bullet):
                self.assertIn("weapon", flags)

    def test_the_specialist_keeps_a_varied_pool(self):
        """The starvation guard against live content rather than the fixture:
        the specialist's whole world is now the blade bullets, so there had
        better be a good number of them."""
        self.assertGreaterEqual(len(self._flagged()), 15)

    def test_no_other_table_carries_blade(self):
        for name in gen.REQUIRED_TABLES:
            if name == "Weapon":
                continue
            for bullet in bullets_for(LIVE, name):
                self.assertNotIn("blade", gen.flags_for(name, bullet),
                                 "%s carries an inert 'blade' flag" % name)


if __name__ == "__main__":
    unittest.main()
