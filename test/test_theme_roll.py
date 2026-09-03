"""The theme roll itself: every NPC gets one, and it gates what they wear.

The cohesion test below is the reason the whole feature exists, so it is worth
saying how it is written. The obvious spelling - read the rolled value's own
flags back with flags_for() and check the tag - is vacuous for Outfit and Gear,
because roll_npc() strips the '||' segment off those two before returning
(npc["Gear"], gear_flags = split_flags(...)), leaving no tag to read. Those are
the two most theme-relevant tables in the feature, so instead we precompute,
per table and per theme, the set of bullets belonging to *some other* theme and
assert the rolled value is never one of them. That works whether or not
roll_npc() kept the flags.
"""
import pathlib
import random
import tempfile
import unittest

from test.helpers import FIXTURE_TABLES, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)

# Every pronoun set the fixture can roll, so a bullet's placeholders can be
# filled the same way roll_npc() fills them - see core_of() below.
PRONOUN_SETS = [gen.pronoun_fields(p) for p in TABLES["Pronouns"]]


def roll(seed, **overrides):
    return gen.roll_npc(TABLES, random.Random(seed), overrides or None)


def core_of(name, bullet):
    """A bullet reduced to the part that survives into the rolled NPC.

    Flags come off - Backdrop keeps them in a third segment, every other table
    in a second - so a rolled value and the fixture bullet it came from compare
    equal even for the tables roll_npc() strips flags from. Backdrop keeps both
    its shot and its scene, since two scenes can share a shot phrase.
    """
    if name == "Backdrop":
        shot, scene, _ = gen.split_backdrop(bullet)
        return "%s || %s" % (shot, scene)
    return gen.split_flags(bullet)[0]


def rendered(name, bullet):
    """Every string one fixture bullet can appear as once an NPC is rolled.

    roll_npc() substitutes pronoun placeholders into every value it returns, so
    "{Subject} {wear} a wide woven hat." comes back as "She wears a wide woven
    hat." Expanding the fixture side against all pronoun sets is what lets the
    comparison be a plain set membership test.
    """
    core = core_of(name, bullet)
    if "{" not in core:
        return {core}
    return {core.format(**fields) for fields in PRONOUN_SETS}


def bullets_for(name):
    """A table's bullets, including its per-pronoun variant tables."""
    return [
        bullet
        for key, options in TABLES.items()
        if key == name or key.startswith("%s (" % name)
        for bullet in options
    ]


def rendered_parts(name, value):
    """The parts of a rolled value that reach a prompt or a dossier.

    Everything but Backdrop is rendered whole, so the whole value has to be
    flag-free. Backdrop is the exception by design: it keeps all three of its
    segments, and split_backdrop() unpacks the two that get rendered from the
    flags that do not.
    """
    if name == "Backdrop":
        shot, scene, _ = gen.split_backdrop(value)
        return [shot, scene]
    return [value]


def foreign_bullets(name, theme):
    """Rendered bullets of `name` that belong to a theme other than `theme`.

    A bullet reachable under this theme as well - untagged, or tagged with this
    theme too - is subtracted back out, so a table that happens to repeat the
    same text under two themes cannot produce a false failure.
    """
    foreign, allowed = set(), set()
    for bullet in bullets_for(name):
        tags = gen.themes_of(gen.flags_for(name, bullet))
        (foreign if tags and theme not in tags else allowed).update(
            rendered(name, bullet))
    return foreign - allowed


class TestThemeRoll(unittest.TestCase):
    def test_every_npc_has_a_theme(self):
        for seed in range(50):
            self.assertIn(roll(seed)["Theme"], {"alpha", "beta"})

    def test_theme_can_be_forced(self):
        self.assertEqual(roll(0, Theme="beta")["Theme"], "beta")

    def test_no_npc_carries_a_foreign_theme(self):
        """The core cohesion guarantee, over every themed table."""
        banned = {
            theme: {name: foreign_bullets(name, theme) for name in gen.THEMED_TABLES}
            for theme in ("alpha", "beta")
        }
        for seed in range(300):
            npc = roll(seed)
            theme = npc["Theme"]
            for name in gen.THEMED_TABLES:
                self.assertNotIn(
                    core_of(name, npc[name]), banned[theme][name],
                    "seed %d: theme %r rolled a %s belonging to another theme"
                    % (seed, theme, name))

    def test_the_cohesion_check_can_actually_fail(self):
        """Guard against the test above quietly asserting nothing.

        It only bites if the fixture really does tag some bullets for a theme
        other than the one being rolled; a fixture edit that dropped those tags
        would leave a green test that checks nothing at all.
        """
        for theme in ("alpha", "beta"):
            self.assertTrue(
                any(foreign_bullets(name, theme) for name in gen.THEMED_TABLES),
                "fixture has no bullets foreign to theme %r" % theme)

    def test_theme_is_independent_of_role(self):
        """A pirate must be as likely to look alpha as any other role is."""
        rolled = [roll(s) for s in range(600)]
        pairs = [(n["Theme"], n["Role"]) for n in rolled]
        roles = {r for _, r in pairs}
        self.assertGreater(len(roles), 1, "fixture must roll more than one role")
        for role in roles:
            themes = [t for t, r in pairs if r == role]
            alpha = themes.count("alpha") / len(themes)
            # Fixture weights alpha 2:1, so expect ~0.67 regardless of role.
            self.assertGreater(alpha, 0.45, "role %r skews low on alpha" % role)
            self.assertLess(alpha, 0.85, "role %r skews high on alpha" % role)

    def test_no_themed_value_keeps_its_flag_segment(self):
        """A theme tag must never be rendered as part of the trait it tags.

        Every themed table's value goes straight into a Krea prompt and a
        dossier row, so 'a long braid || @neosamurai' would ship the tag to the
        image model. Fails if any of the six loses its stripping.
        """
        for seed in range(100):
            npc = roll(seed)
            for name in gen.THEMED_TABLES:
                for part in rendered_parts(name, npc[name]):
                    self.assertNotIn(
                        "||", part,
                        "seed %d: %s kept its flags: %r" % (seed, name, npc[name]))

    def test_a_forced_trait_does_not_smuggle_its_flags_back_in(self):
        """--set-trait pastes the raw bullet back over the split-out value.

        roll_npc() re-splits after that paste, and every themed table has to be
        in that second pass as well as the first - Gear especially, whose first
        split happens before the override is applied at all.
        """
        for name in gen.THEMED_TABLES:
            flagged = [b for b in bullets_for(name) if gen.flags_for(name, b)]
            # Feature is the one themed table the fixture leaves unflagged, so
            # it has nothing to force; every other table must have material
            # here, or this test has quietly stopped covering it.
            self.assertTrue(
                flagged or name == "Feature",
                "fixture has no flagged %s bullet to force" % name)
            for bullet in flagged:
                npc = roll(0, **{name: bullet})
                for part in rendered_parts(name, npc[name]):
                    self.assertNotIn(
                        "||", part,
                        "forced %s kept its flags: %r" % (name, npc[name]))

    def test_theme_reaches_the_dossier(self):
        """The rendered dossier carries a Theme row, and its '-' fallback.

        write_dossier() reads npc.get("Theme", "-") rather than npc["Theme"] so
        that regenerating an NPC from a manifest entry written before Theme
        existed still writes a dossier instead of raising. Both branches are
        pinned here; asserting only that roll_npc() returns the key would let
        that fallback regress unnoticed.
        """
        npc = roll(0)
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "dossier.md"

            gen.write_dossier(path, npc, 0, ("portrait", "token"), [])
            self.assertIn(
                "| Theme | %s |" % npc["Theme"], path.read_text(encoding="utf-8"))

            del npc["Theme"]        # a manifest entry written before Theme existed
            gen.write_dossier(path, npc, 0, ("portrait", "token"), [])
            self.assertIn("| Theme | - |", path.read_text(encoding="utf-8"))

    def test_no_pool_is_ever_starved(self):
        """Every themed table must still yield a value for every theme."""
        for theme in ("alpha", "beta"):
            for seed in range(100):
                npc = roll(seed, Theme=theme)
                for name in gen.THEMED_TABLES:
                    self.assertTrue(npc[name], "%s empty for %s" % (name, theme))


if __name__ == "__main__":
    unittest.main()
