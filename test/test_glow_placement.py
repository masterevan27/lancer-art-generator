"""Where the rolled Glow colour falls, and what keeps a placement plausible.

The portrait's glow sentence used to be one fixed phrase - the light fell
across one side of the subject's face in every single render. Placement is now
its own roll, split from the colour for the reason Hair colour split from Hair:
a new placement is one bullet rather than a rewrite of every shade.

The interesting property is the 'scene' flag. The glow has two possible
sources - something the NPC wears or carries, or the backdrop itself - and only
the second can light a wall behind them. A placement that puts colour out in
the environment is therefore reachable only when the Backdrop is what casts it.
"""
import random
import unittest

from test.helpers import (
    FIXTURE_TABLES, REPO, bullets_for, load_generator, rendered)

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")

LIVE_PLACEMENTS = bullets_for(LIVE, "Glow placement")


def roll(seed, **overrides):
    return gen.roll_npc(TABLES, random.Random(seed), overrides or None)


class TestTheLiveTable(unittest.TestCase):
    def test_the_table_exists_and_is_rolled(self):
        self.assertIn("Glow placement", gen.REQUIRED_TABLES)
        self.assertTrue(LIVE_PLACEMENTS)

    def test_it_is_rolled_after_backdrop(self):
        """The 'scene' filter reads the rolled Backdrop, so order is load-bearing.

        Listed before Backdrop, npc["Backdrop"] would not exist yet and the
        filter would raise - loudly, but only on the roll that reached it.
        """
        order = gen.REQUIRED_TABLES
        self.assertLess(order.index("Backdrop"), order.index("Glow placement"))

    def test_no_placement_names_a_colour(self):
        """The template has already said the colour; saying it twice gives two glows.

        The same failure the Glow colour table's own comment records for
        light-emitting phenomena, one slot further along.
        """
        colours = {gen.split_flags(b)[0] for b in bullets_for(LIVE, "Glow colour")}
        for bullet in LIVE_PLACEMENTS:
            text = gen.split_flags(bullet)[0].lower()
            for colour in colours:
                self.assertNotIn(
                    colour.lower(), text,
                    "this placement names the colour the template already "
                    "supplied, so the prompt would assert it twice: %r" % bullet)

    def test_every_placement_reads_as_a_predicate(self):
        """Each bullet completes "A faint {glow} glow ___." so it must not
        restate the subject: a bullet beginning "the light falls" would render
        as "A faint amber glow the light falls."."""
        for bullet in LIVE_PLACEMENTS:
            text = gen.split_flags(bullet)[0]
            self.assertFalse(
                text[0].isupper(),
                "a placement is mid-sentence and should not be capitalised: %r" % bullet)
            self.assertNotIn(
                " glow", text,
                "a placement should not repeat the word the template supplies: %r" % bullet)


class TestSceneFlag(unittest.TestCase):
    def _scene_texts(self, tables):
        """Every string a 'scene'-flagged placement can appear as once rolled.

        Through rendered() rather than split_flags() alone: a rolled value has
        had its pronoun placeholders substituted, so comparing it against the
        raw bullet text matches nothing - and matching nothing is invisible
        here, since the assertion it feeds is assertNotIn. Both tests below
        would pass on zero comparisons. They count what they checked for the
        same reason.
        """
        return {text
                for b in bullets_for(tables, "Glow placement")
                if "scene" in gen.split_flags(b)[1]
                for text in rendered(tables, "Glow placement", b)}

    def test_the_fixture_carries_both_kinds(self):
        scene = self._scene_texts(TABLES)
        allx = {text
                for b in bullets_for(TABLES, "Glow placement")
                for text in rendered(TABLES, "Glow placement", b)}
        self.assertTrue(scene, "fixture needs a 'scene' placement to test against")
        self.assertTrue(allx - scene, "fixture needs an unflagged placement too")

    def test_a_scene_placement_never_lands_on_an_unlit_backdrop(self):
        scene = self._scene_texts(TABLES)
        checked = 0
        for seed in range(400):
            npc = roll(seed)
            backdrop_scene = gen.split_backdrop(npc["Backdrop"])[1]
            if gen.has_light_source(backdrop_scene):
                continue
            checked += 1
            self.assertNotIn(
                npc["Glow placement"], scene,
                "seed %d: a 'scene' placement landed on a backdrop that casts "
                "no light of its own - nothing in frame could light that wall"
                % seed)
        self.assertTrue(checked, "no unlit backdrop was rolled; the test checked nothing")

    def test_a_scene_placement_is_reachable_when_the_backdrop_lights_the_scene(self):
        """The filter must not be a blanket ban - that would pass the test
        above while making four live bullets dead content."""
        scene = self._scene_texts(TABLES)
        lit = 0
        reached = 0
        for seed in range(400):
            npc = roll(seed)
            if not gen.has_light_source(gen.split_backdrop(npc["Backdrop"])[1]):
                continue
            lit += 1
            if npc["Glow placement"] in scene:
                reached += 1
        self.assertTrue(lit, "no lit backdrop was rolled; the test checked nothing")
        self.assertTrue(reached, "no 'scene' placement was ever rolled")


class TestRenderedPrompt(unittest.TestCase):
    def test_the_placement_reaches_the_portrait(self):
        """Searched rather than skipped on a fixed seed.

        The glow sentence only fires when something rolled for the NPC could
        actually cast the light, so a hardcoded seed makes this test pass or
        skip depending on an unrelated roll. Finding a lit one asserts the
        thing every time.
        """
        checked = 0
        for seed in range(200):
            npc = roll(seed, **{"Glow placement": "rims {possessive} shoulders"})
            portrait, _ = gen.build_prompts(npc)
            if "glow" not in portrait:
                continue
            checked += 1
            self.assertIn("rims", portrait)
        self.assertTrue(checked, "no roll produced a glow sentence to check")

    def test_no_flag_segment_reaches_a_prompt(self):
        """A rolled placement is dropped into the prompt verbatim, so an
        unstripped '|| scene' would ship the literal words to the image model
        and print them in the dossier - the same failure the tables file warns
        about for theme tags on an unsplit table."""
        for seed in range(200):
            npc = roll(seed)
            self.assertNotIn("||", npc["Glow placement"])
            self.assertFalse(npc["Glow placement"].endswith("scene"))

    def test_the_token_prompt_carries_no_placement(self):
        """The token renders on flat white with no scene at all, so it keeps
        the unplaced wording it always had."""
        self.assertNotIn("{placement}", gen.GLOW_TOKEN)
        for seed in range(50):
            npc = roll(seed)
            _, token = gen.build_prompts(npc)
            self.assertNotIn(npc["Glow placement"], token)

    def test_a_stored_npc_with_no_placement_still_builds(self):
        """--regen-manifest rebuilds from stored traits, and an entry written
        before this table existed has no key for it. It must not KeyError, and
        the fallback must not leak an unsubstituted placeholder - a manifest's
        traits have already had their pronouns filled in, so nothing would
        re-run the substitution."""
        npc = roll(0)
        del npc["Glow placement"]
        portrait, token = gen.build_prompts(npc)
        self.assertNotIn("{", portrait)
        self.assertNotIn("{", token)
        self.assertNotIn("{", gen.LEGACY_GLOW_PLACEMENT)


if __name__ == "__main__":
    unittest.main()
