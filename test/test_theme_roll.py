"""The theme roll itself: every NPC gets one, and it gates what they wear.

The cohesion test below is the reason the whole feature exists, so it is worth
saying how it is written. The obvious spelling - read the rolled value's own
flags back with flags_for() and check the tag - is vacuous for every themed
table, because roll_npc() strips the '||' segment off each one before
returning: Hair, Feature, Outfit, Headgear and Weapon via split_flags() in its
main loop, Backdrop and Hair colour via their own three-segment splitters -
leaving no tag on npc[name] to read. So instead we precompute, per table and
per theme, the set of bullets belonging to *some other* theme and assert the
rolled value is never one of them. That works whether or not roll_npc() kept
the flags.
"""
import contextlib
import io
import pathlib
import random
import tempfile
import unittest

from test.helpers import (
    FIXTURE_TABLES, bullets_for, core_of, foreign_texts, load_generator)

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)


def roll(seed, **overrides):
    return gen.roll_npc(TABLES, random.Random(seed), overrides or None)


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

    Thin wrapper binding the shared helper to this module's fixture, so the
    tests below read the way they did before the helper moved into
    test/helpers.py to be shared with the visibility measurement.
    """
    return foreign_texts(TABLES, name, theme)


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

        It only bites on a table the fixture really does tag for some theme
        other than the one being rolled; a fixture edit that dropped those tags
        would leave a green test that checks nothing at all. Asserted per
        table rather than over all of them at once, because `any()` across
        THEMED_TABLES stays green while six of the seven go vacuous - one
        untagged Outfit would be invisible.

        Per table but not per theme: a table the fixture tags for one theme
        only - Weapon is '@alpha', Feature is '@beta' - has no foreign bullet
        under that same theme, and demanding both would force every fixture
        table to carry a bullet of every theme for no extra coverage.
        """
        for name in gen.THEMED_TABLES:
            self.assertTrue(
                any(foreign_bullets(name, theme) for theme in ("alpha", "beta")),
                "fixture tags no %s bullet for any theme, so the cohesion "
                "check above asserts nothing about that table" % name)

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
        image model. Fails if any of the seven loses its stripping.
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

        roll_npc() re-splits after that paste, and every themed table has to
        be in that second pass as well as the first, since npc.update(overrides)
        only runs after the whole roll loop has already completed its own
        split. Stance is checked alongside the seven: it is not themed, but
        its rolled value is split in that same block and its override was
        leaking flags for the same reason.
        """
        for name in gen.THEMED_TABLES + ("Stance",):
            flagged = [b for b in bullets_for(TABLES, name) if gen.flags_for(name, b)]
            # Every table here must have material to force, or this test has
            # quietly stopped covering it.
            self.assertTrue(
                flagged, "fixture has no flagged %s bullet to force" % name)
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

    def test_every_themed_table_still_yields_a_value(self):
        """A themed roll must never come back empty, whatever the theme.

        A crash guard rather than a pool guard - it asserts only that a value
        exists, not that the pool it came from stayed a reasonable size. The
        actual no-starvation guarantee is
        test_theme_inert.test_every_theme_still_rolls_a_full_pool, which
        compares pool lengths.

        Weapon is exempt from the truthiness check, not from the key lookup:
        its weighted empty entry ('|| none') rolling to '' is the unarmed
        case, a real value rather than a crash. test_weapon.py owns that
        guarantee in both directions - test_an_unarmed_npc_is_possible pins
        that '' is reachable, test_an_armed_npc_is_possible pins that a real
        weapon is too - so this test only needs to keep checking that the key
        exists at all, the same as every other themed table.
        """
        for theme in ("alpha", "beta"):
            for seed in range(100):
                npc = roll(seed, Theme=theme)
                for name in gen.THEMED_TABLES:
                    value = npc[name]
                    if name != "Weapon":
                        self.assertTrue(value, "%s empty for %s" % (name, theme))


class TestForcedThemeIsValidated(unittest.TestCase):
    """`--set-trait Theme=` is checked against the Theme table, as Pronouns is.

    An unknown theme used to resolve in silence to an all-neutral roll. The
    empty string was worse: it is falsy, so roll_npc() rolled a real theme and
    filtered every themed pool with it, and npc.update(overrides) then pasted
    the empty string back over the record - a dossier claiming no theme for an
    NPC that was themed, contradicting the dossier's own printed promise that
    the seed reproduces the NPC exactly.
    """

    def force(self, value):
        """main() with one forced Theme, its dry-run chatter swallowed."""
        with contextlib.redirect_stdout(io.StringIO()):
            return gen.main(["--dry-run", "--tables", str(FIXTURE_TABLES),
                             "--set-trait", "Theme=%s" % value])

    def test_an_unknown_theme_is_rejected(self):
        with self.assertRaises(SystemExit) as caught:
            self.force("typo")
        message = str(caught.exception)
        self.assertIn("no such theme", message)
        # The available values are listed, the same as the Pronouns check does.
        self.assertIn("alpha", message)
        self.assertIn("beta", message)

    def test_an_empty_theme_is_rejected(self):
        with self.assertRaises(SystemExit) as caught:
            self.force("")
        self.assertIn("no such theme", str(caught.exception))

    def test_a_theme_the_table_offers_is_accepted(self):
        self.assertEqual(self.force("beta"), 0)


if __name__ == "__main__":
    unittest.main()
