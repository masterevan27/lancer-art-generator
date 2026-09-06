"""What a bullet's real chance of being rolled is, and how it is measured.

A weight compares a bullet to its neighbour. It does not say how often the
bullet turns up, and dividing by the table total does not either: disabled
bullets are not in the pool at all, and most tables are filtered before they
are drawn from. `--trait-odds` answers the actual question by rolling the real
roller a great many times and counting what comes out.

The tests that matter most here are the ones that would fail if the odds were
secretly naive weight shares - test_a_gun_stance_is_rarer_than_its_weight and
test_a_themed_bullet_beats_its_weight - and the one that would fail if any of
this had changed a single draw, test_the_roll_is_unchanged.

See docs/superpowers/specs/2026-09-04-trait-roll-odds-design.md.
"""
import json
import os
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test.helpers import FIXTURE_TABLES, REPO, core_of, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")

SNAPSHOT = json.loads(
    (Path(__file__).resolve().parent / "fixtures" / "roll-snapshot.json")
    .read_text(encoding="utf-8"))

# Enough rolls that a share is stable to a percentage point or so, few enough
# that the whole module still runs in seconds. The shipped default is far
# larger; nothing here asserts to a precision that needs it.
SAMPLES = 4000


def roll(seed, tables=None, **overrides):
    return gen.roll_npc(tables or TABLES, random.Random(seed), overrides or None)


class TestTheRollIsUnchanged(unittest.TestCase):
    """The whole feature is only acceptable if it changed no draw at all.

    fixtures/roll-snapshot.json was captured from the roller before any of
    this landed. Every trait of every seed in it must still come out
    identical - memoising the splitters must be invisible, and collecting
    raw bullets must not consume a single extra number from the stream.

    The snapshot is not frozen forever, though, and it is worth being clear
    about when it may move, because "regenerate the fixture" is also how you
    would silently paper over a real regression. It may be recaptured only for
    a change that is MEANT to change the draw - a table added to or reordered
    within REQUIRED_TABLES, a new filter in the roll loop - and the recapture
    belongs in that same commit, so the diff shows the intended change and its
    effect together. It has moved once: when Glow colour was reordered to
    follow Backdrop and gated on the scene's own hue (filter_by_hue), which
    shifts every draw after it in the stream by construction. Anything that
    claims to be invisible to the roller - a refactor, a memoisation, a new
    piece of bookkeeping - must still leave this file untouched.
    """

    def test_the_roll_is_unchanged(self):
        for seed, expected in sorted(SNAPSHOT.items()):
            npc = roll(int(seed))
            got = {k: v for k, v in npc.items() if not k.startswith("_")}
            self.assertEqual(expected, got, "seed %s rolls differently now" % seed)


class TestMemoisedSplitters(unittest.TestCase):
    """The cache is only safe because every splitter returns immutable values.

    A splitter that returned a list would hand every caller the same list, and
    one caller mutating it would corrupt the answer for all the rest. Nothing
    does today; this is the test that notices if a future one does.
    """

    SPLITTERS = ("split_flags", "split_backdrop", "split_hair_colour",
                 "split_faction", "themes_of", "flags_for")

    def test_every_splitter_is_cached(self):
        for name in self.SPLITTERS:
            self.assertTrue(hasattr(getattr(gen, name), "cache_info"),
                            "%s is not memoised - see the spec's 3.2" % name)

    def test_every_splitter_returns_immutable_values(self):
        bullets = [b for key in LIVE for b in LIVE[key]]
        for bullet in bullets:
            for value in (gen.split_flags(bullet), gen.split_backdrop(bullet),
                          gen.split_hair_colour(bullet), gen.split_faction(bullet)):
                self.assertIsInstance(value, tuple)
                for part in value:
                    self.assertIsInstance(part, (str, tuple))
            self.assertIsInstance(gen.themes_of(gen.split_flags(bullet)[1]), frozenset)

    def test_the_cache_returns_equal_values(self):
        """Called twice, a splitter agrees with itself - and with a fresh split."""
        for bullet in [b for key in LIVE for b in LIVE[key]][:200]:
            text, _, rest = bullet.partition("||")
            self.assertEqual(
                (text.strip(), tuple(f for f in rest.split() if f)),
                gen.split_flags(bullet))


class TestRawBullets(unittest.TestCase):
    """npc['_raw'] - the collection half of the raw-bullets spec.

    Counting cannot read the rendered traits: roll_npc() strips flags off nine
    tables before storing them, so a rendered Weapon no longer matches any line
    in the file. The raw bullet is captured at the moment it is drawn instead.
    """

    def test_every_rolled_table_is_recorded(self):
        raw = roll(3)["_raw"]
        self.assertEqual(set(gen.REQUIRED_TABLES), set(raw))

    def test_each_raw_bullet_strips_to_its_rendered_trait(self):
        """Two records of one thing must agree - the raw-bullets spec's own risk.

        Rendered on the raw side as well as stripped: roll_npc() substitutes
        the pronoun placeholders a bullet carries ('in {possessive} late
        teens') into what it returns, and _raw deliberately keeps the bullet
        as the file spells it, placeholders included - that is what a re-roll
        has to hand back as an override.
        """
        for seed in range(40):
            npc = roll(seed)
            for name, raw in npc["_raw"].items():
                if name in ("Hair", "Hair colour"):
                    continue   # '{colour}' is substituted, so they never match literally
                self.assertEqual(core_of(name, raw).format(**npc["_pronouns"]),
                                 core_of(name, npc[name]),
                                 "%s: %r does not strip to %r" % (name, raw, npc[name]))

    def test_each_raw_bullet_is_a_line_in_the_file(self):
        for seed in range(40):
            for name, raw in roll(seed)["_raw"].items():
                pool = [b for key in LIVE if key == name or key.startswith(name + " (")
                        for b in TABLES.get(key, [])]
                self.assertIn(raw, pool or TABLES[name],
                              "%s: %r is not a bullet in the tables file" % (name, raw))

    def test_a_forced_trait_is_recorded_as_forced(self):
        """_raw follows the NPC, not the discarded draw.

        A re-roll pins every other trait from _raw, so a _raw that disagreed
        with the NPC would pin it to a bullet the NPC does not have.
        """
        forced = "a colonial administrator || mil"
        npc = roll(5, Role=forced)
        self.assertEqual(forced, npc["_raw"]["Role"])

    def test_the_nogear_re_roll_is_what_gets_recorded(self):
        """Gear is rolled twice on a nogear backdrop; _raw holds the keeper.

        Were _raw written before the re-roll it would sometimes carry a
        'hands' bullet - exactly the bullet the re-roll exists to replace.
        """
        seen = 0
        for seed in range(400):
            npc = roll(seed)
            if "nogear" not in gen.split_backdrop(npc["_raw"]["Backdrop"])[2]:
                continue
            seen += 1
            self.assertNotIn("hands", gen.split_flags(npc["_raw"]["Gear"])[1],
                             "seed %d kept a hands Gear under a nogear backdrop" % seed)
        self.assertTrue(seen, "no nogear backdrop rolled - the test proved nothing")


class TestHeadingAttribution(unittest.TestCase):
    """A raw bullet has to be reported under the heading it actually came from.

    variant_table() serves 'Build (she)' in place of 'Build', and 'Outfit'
    plus 'Outfit (she) +' as one pool. The rolled value alone does not say
    which, so the subject resolves it - in variant_table()'s own order, or the
    two would disagree the moment one of them changed.
    """

    def test_a_replacement_variant_wins(self):
        for bullet in LIVE["Build (she)"]:
            self.assertEqual("Build (she)",
                             gen.heading_for(LIVE, "Build", "she", bullet))

    def test_a_replacement_variant_is_not_reached_by_another_subject(self):
        self.assertEqual("Build", gen.heading_for(LIVE, "Build", "he", LIVE["Build"][0]))

    def test_an_additive_variant_wins_for_its_own_bullets(self):
        only_she = [b for b in LIVE["Hair (she) +"] if b not in LIVE["Hair"]]
        self.assertTrue(only_she, "fixture drift: 'Hair (she) +' shares every bullet")
        for bullet in only_she:
            self.assertEqual("Hair (she) +",
                             gen.heading_for(LIVE, "Hair", "she", bullet))

    def test_an_additive_variant_leaves_the_base_alone(self):
        base_only = [b for b in LIVE["Hair"] if b not in LIVE["Hair (she) +"]]
        for bullet in base_only:
            self.assertEqual("Hair", gen.heading_for(LIVE, "Hair", "she", bullet))

    def test_a_subject_with_no_variant_falls_back_to_the_base(self):
        self.assertEqual("Skin", gen.heading_for(LIVE, "Skin", "she", LIVE["Skin"][0]))


class TestTheOdds(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.odds = gen.trait_odds(LIVE, SAMPLES, random.Random(11))

    def test_every_rolled_heading_is_reported(self):
        for name in gen.REQUIRED_TABLES:
            for key in [k for k in LIVE if k == name or k.startswith(name + " (")]:
                self.assertIn(key, self.odds)

    def test_a_variant_family_sums_to_one(self):
        """Per FAMILY, not per heading.

        A 'Build (she)' bullet is only reachable by a woman, so that heading's
        own rows sum to the share of NPCs who are women - which is the honest
        unconditional answer, and the reason the sum is checked across the
        family rather than within a heading.
        """
        for name in gen.REQUIRED_TABLES:
            family = [k for k in LIVE if k == name or k.startswith(name + " (")]
            total = sum(p for key in family for p in self.odds[key].values())
            self.assertAlmostEqual(1.0, total, places=6,
                                   msg="%s sums to %r" % (name, total))

    def test_a_variant_heading_sums_to_less_than_one(self):
        she = sum(self.odds["Build (she)"].values())
        self.assertGreater(she, 0.0)
        self.assertLess(she, 1.0)

    def test_every_bullet_is_reported_even_at_zero(self):
        """Unreachable and absent are different answers and must look different."""
        for key, bullets in self.odds.items():
            self.assertEqual(set(LIVE[key]), set(bullets))

    def test_a_gun_stance_is_rarer_than_its_weight(self):
        """The assertion that fails if these are secretly naive weight shares.

        A '|| gun' pose needs the Weapon roll to have produced an actual
        firearm, so it must come in under its share of the Stance table.
        """
        stances = self.odds["Stance"]
        naive = self._weight_shares(LIVE["Stance"])
        gunny = [b for b in set(stances) if "gun" in gen.split_flags(b)[1]]
        self.assertTrue(gunny, "fixture drift: no '|| gun' Stance bullet")
        for bullet in gunny:
            self.assertLess(stances[bullet], naive[bullet],
                            "%r is not rarer than its weight share" % bullet)

    def test_weight_still_orders_an_unfiltered_table(self):
        """Where nothing filters, a heavier bullet is simply likelier."""
        odds = self.odds["Height"]
        by_weight = sorted(set(LIVE["Height"]), key=LIVE["Height"].count)
        self.assertLess(odds[by_weight[0]], odds[by_weight[-1]])

    @staticmethod
    def _weight_shares(bullets):
        """What each bullet's share would be if nothing filtered the pool.

        parse_tables() expands 'x4 …' into four identical list entries rather
        than carrying a weights column, so a bullet's weight is how many times
        it appears and the naive share is just its count over the length.
        """
        return {b: bullets.count(b) / len(bullets) for b in bullets}


class TestThemedOdds(unittest.TestCase):
    """Theme runs the filter the other way: a tagged bullet is weighted UP.

    Against the themed fixture rather than the live tables, which carry no '@'
    tags on any bullet yet - only in the documentation describing them. A test
    reading LIVE here would pass vacuously today and start meaning something
    on a day nobody was looking.
    """

    @classmethod
    def setUpClass(cls):
        cls.tables = gen.parse_tables(REPO / "test" / "fixtures" / "tables-themed.md")
        cls.odds = gen.trait_odds(cls.tables, SAMPLES, random.Random(4))

    def test_a_themed_bullet_beats_its_weight(self):
        hair = self.odds["Hair"]
        naive = TestTheOdds._weight_shares(self.tables["Hair"])
        tagged = [b for b in set(hair) if gen.themes_of(gen.split_flags(b)[1])]
        self.assertTrue(tagged, "fixture drift: no themed Hair bullet")
        self.assertTrue(any(hair[b] > naive[b] for b in tagged),
                        "no themed Hair bullet beats its weight share")


class TestDisabledBullets(unittest.TestCase):
    """A commented-out bullet is not in the pool, so it has no probability.

    Absent rather than 0.0, and the difference is the point: 0.0 means the
    generator can reach it and never did, absent means it was switched off.
    """

    def test_a_disabled_bullet_is_absent(self):
        cut = "a short {colour} crop"
        text = FIXTURE_TABLES.read_text(encoding="utf-8")
        self.assertIn("- %s\n" % cut, text, "fixture drift: that Hair bullet is gone")
        disabled = text.replace("- %s\n" % cut, "<!-- - %s -->\n" % cut, 1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tables.md"
            path.write_text(disabled, encoding="utf-8")
            odds = gen.trait_odds(gen.parse_tables(path), 200, random.Random(2))
        self.assertNotIn(cut, odds["Hair"])
        self.assertTrue(odds["Hair"], "disabling one bullet emptied the table")


class TestTheCommandLine(unittest.TestCase):

    def _run(self, *args, cwd):
        return subprocess.run(
            [sys.executable, str(REPO / "generate-npc.py"), "--trait-odds", *args,
             "--tables", str(FIXTURE_TABLES)],
            capture_output=True, text=True, cwd=cwd, timeout=300)

    def test_it_prints_json_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            before = set(os.listdir(tmp))
            done = self._run("300", cwd=tmp)
            self.assertEqual(0, done.returncode, done.stderr)
            self.assertEqual(before, set(os.listdir(tmp)),
                             "--trait-odds created something in the working directory")
        report = json.loads(done.stdout)
        self.assertEqual(300, report["samples"])
        self.assertIn("Skin", report["tables"])

    def test_stdout_is_json_and_nothing_else(self):
        """The GUI parses stdout whole; one stray print would break it."""
        with tempfile.TemporaryDirectory() as tmp:
            done = self._run("200", cwd=tmp)
        json.loads(done.stdout)          # raises if anything else was printed

    def test_the_sample_count_defaults(self):
        self.assertEqual(gen.DEFAULT_ODDS_SAMPLES,
                         gen.parse_args(["--trait-odds"]).trait_odds)

    def test_it_does_not_need_an_output_folder(self):
        self.assertIsNone(gen.parse_args(["--trait-odds"]).out)


if __name__ == "__main__":
    unittest.main()
