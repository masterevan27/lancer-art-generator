"""The glow has to agree with the light the rest of the roll already described.

Three separate ways a portrait's glow sentence used to read as out of place,
and the three filters that answer them. They are one file because they are one
complaint: the glow is the single saturated colour in an otherwise restrained
frame, so anything about it that fights the scene is the most visible error
either prompt can make.

  1. THE GLOW FIRED ON A SCENE WITH NO COLOURED LIGHT IN IT. has_light_source()
     used to match the bare words 'lit', 'light', 'lights', 'lighting' and
     'glaring', which almost every Backdrop scene says somewhere and which are
     usually WHITE where they say it - floodlights over a dock, fluorescent
     tubes in an office, "hard directional light", a caged work lamp, grey
     daylight through a hole in a roof. The sentence fired on 88% of rolls.

  2. THE COLOUR CONTRADICTED A COLOUR THE SCENE HAD ALREADY NAMED. A wall of
     schematics "lit crimson" behind a subject lit by a faint teal-green glow
     asks the model for two incompatible light sources and it draws both.

  3. THE PLACEMENT NAMED A PROP THE SCENE DID NOT HAVE. "Washes the towering
     display wall stacked behind her" against a snowbound crash site; "pools on
     the ground around him" against a man floating weightless in an
     observation blister.

Rolls against the live tables where the assertion is about content and against
the fixture where it is about the roller, the same split test_glow_placement.py
uses.
"""
import random
import unittest

from test.helpers import (
    FIXTURE_TABLES, REPO, bullets_for, load_generator, rendered)

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")

LIVE_BACKDROPS = list(dict.fromkeys(LIVE["Backdrop"]))
LIVE_COLOURS = bullets_for(LIVE, "Glow colour")
LIVE_PLACEMENTS = bullets_for(LIVE, "Glow placement")


def scenes():
    return [gen.split_backdrop(b)[1] for b in LIVE_BACKDROPS]


class TestWhatCountsAsALightSource(unittest.TestCase):
    """White light is not a reason to paint the frame magenta."""

    NEUTRAL = (
        "Behind her is a rain-lashed construction site at night, pile drivers "
        "and floodlit scaffolding rising around the shell of a half-built tower.",
        "She is standing at a rain-lashed dockside barrier with a tablet held "
        "low, watching a container crane work - floodlights burn cones through "
        "the downpour behind her.",
        "Behind him is a dim institutional corridor, flickering fluorescent "
        "tubes above a scuffed door and a lone waste bin.",
        "He is standing ankle-deep in the flooded arcade of an abandoned "
        "shopping street, a shaft of grey daylight falling through a collapsed "
        "section of roof far ahead.",
        "Behind her is the interior of a triage tent, saline bags hanging from "
        "a strut above a folding cot and a caged work lamp burning against the "
        "canvas.",
        "Hard directional light rakes across her face and the weapon.",
    )

    COLOURED = (
        "Behind her is a graffiti-tagged alley lit by tube neon signage.",
        "Behind him is a wall of technical schematics lit crimson.",
        "He is advancing down a service corridor, red emergency strip-lighting "
        "striping the walls around him.",
        "She is seated at a bank of monitors glowing violet and cyan.",
        "He is standing in a mech's calibration bay, cool blue interior "
        "lighting washing the bay.",
        "She is firing directly toward the viewer, muzzle flash bursting from "
        "the barrel.",
    )

    def test_white_light_is_not_a_light_source(self):
        for text in self.NEUTRAL:
            with self.subTest(text=text[:60]):
                self.assertFalse(
                    gen.has_light_source(text),
                    "this scene's light is white or natural, so a saturated "
                    "glow has nothing in frame to have come from: %r" % text)

    def test_coloured_light_still_is_one(self):
        for text in self.COLOURED:
            with self.subTest(text=text[:60]):
                self.assertTrue(
                    gen.has_light_source(text),
                    "this scene names a coloured light and must still "
                    "motivate a glow: %r" % text)

    def test_the_live_table_is_split_rather_than_emptied(self):
        """Narrowing the match must not have turned the glow off entirely.

        A filter that never fires is as wrong as one that always does - the
        glow sentence is a feature, not a hazard - so this holds the live
        table's lit share inside a band rather than asserting a number.
        """
        lit = [s for s in scenes() if gen.has_light_source(s)]
        share = len(lit) / len(LIVE_BACKDROPS)
        self.assertGreater(share, 0.25, "almost no scene motivates a glow now")
        self.assertLess(share, 0.75, "the old always-on behaviour is back")


class TestHueAgreement(unittest.TestCase):
    def test_a_scene_that_names_a_hue_binds_the_shade(self):
        cases = {
            "a wall of technical schematics lit crimson": "red",
            "red emergency strip-lighting striping the walls": "red",
            "a bank of monitors glowing violet and cyan": "violet",
            "a hacker's den lit green by a wall of humming CRT monitors": "green",
            "cool blue interior lighting washing the bay": "blue",
            "faint teal atmospheric light bleeding in from one side": "green",
        }
        for scene, family in cases.items():
            with self.subTest(scene=scene):
                self.assertIn(family, gen.light_hues(scene))

    def test_an_uncommitted_scene_binds_nothing(self):
        """The common case, and the one that keeps the table varied.

        A bank of readouts, an ember, an unqualified neon sign all cast light
        without saying what colour it is, and those must leave the shade free -
        a filter that bound every lit scene would collapse the table to
        whatever hue happened to be nearest.
        """
        for scene in ("a wall of humming, dust-caked monitors",
                      "drifting embers and rubble",
                      "stacked neon signage glowing through the drifting mist"):
            with self.subTest(scene=scene):
                self.assertEqual(gen.light_hues(scene), set())

    def test_pigment_is_not_light(self):
        """A red machine is not a red lamp.

        The proximity window is what makes this a risk: a hue word and a light
        word in the same sentence do not necessarily describe each other, and
        the window is deliberately short enough that a clause boundary
        separates them.
        """
        for scene in ("rust-red canyon walls of compacted metal rise to either "
                      "side of her into a hazy sky",
                      "a long white coat draped over his shoulders",
                      "a dull red sun hanging low beside a darker second disc"):
            with self.subTest(scene=scene):
                self.assertEqual(gen.light_hues(scene), set())

    def test_every_hue_family_a_scene_can_name_has_a_shade_to_offer(self):
        """Otherwise filter_by_hue() falls back and the binding does nothing.

        The fallback is deliberate - never roll an empty pool - but a family
        with no shade behind it means the filter silently stops applying, and a
        silent no-op is exactly what this file exists to notice.
        """
        offered = set()
        for bullet in LIVE_COLOURS:
            offered |= gen.glow_hue_families(gen.split_flags(bullet)[0])
        wanted = set()
        for scene in scenes():
            wanted |= gen.light_hues(scene)
        self.assertTrue(wanted, "no live scene names a hue; nothing was checked")
        self.assertFalse(
            wanted - offered,
            "the live Backdrop table names light in %s, and '## Glow colour' "
            "has no shade in %s" % (sorted(wanted), sorted(wanted - offered)))

    def test_the_rolled_shade_agrees_with_the_rolled_scene(self):
        checked = 0
        for seed in range(400):
            npc = gen.roll_npc(LIVE, random.Random(seed))
            hues = gen.light_hues(gen.split_backdrop(npc["Backdrop"])[1])
            if not hues:
                continue
            checked += 1
            self.assertTrue(
                gen.glow_hue_families(npc["Glow colour"]) & hues,
                "seed %d: the scene's light is %s but the glow is %r"
                % (seed, sorted(hues), npc["Glow colour"]))
        self.assertTrue(checked, "no scene naming a hue was rolled")


class TestPlacementProps(unittest.TestCase):
    def test_every_prop_flag_used_in_the_table_is_defined(self):
        """An undefined flag is ignored rather than reported, so it ships the
        placement silently ungated - the failure BACKDROP_ROLES has its own
        test for, one table along."""
        known = (set(gen.PLACEMENT_REQUIRES) | set(gen.PLACEMENT_FORBIDS)
                 | {"scene"})
        for bullet in LIVE_PLACEMENTS:
            for flag in gen.split_flags(bullet)[1]:
                self.assertIn(
                    flag, known,
                    "'%s' on %r is defined nowhere, so it gates nothing"
                    % (flag, bullet))

    def test_every_defined_flag_is_used_by_some_bullet(self):
        used = {f for b in LIVE_PLACEMENTS for f in gen.split_flags(b)[1]}
        for flag in set(gen.PLACEMENT_REQUIRES) | set(gen.PLACEMENT_FORBIDS):
            self.assertIn(flag, used,
                          "'%s' is defined but no placement carries it" % flag)

    def test_a_prop_flag_never_lands_on_a_scene_without_the_prop(self):
        gated = []
        for bullet in LIVE_PLACEMENTS:
            text, flags = gen.split_flags(bullet)
            props = [f for f in flags
                     if f in gen.PLACEMENT_REQUIRES or f in gen.PLACEMENT_FORBIDS]
            if props:
                gated.append((text, props, rendered(LIVE, "Glow placement", bullet)))
        self.assertTrue(gated, "no placement is prop-gated; nothing to check")

        checked = 0
        for seed in range(400):
            npc = gen.roll_npc(LIVE, random.Random(seed))
            scene = gen.split_backdrop(npc["Backdrop"])[1]
            for text, props, forms in gated:
                if npc["Glow placement"] not in forms:
                    continue
                checked += 1
                for flag in props:
                    want = gen.PLACEMENT_REQUIRES.get(flag)
                    if want is not None:
                        self.assertTrue(
                            want.search(scene),
                            "seed %d: placement %r needs a '%s' in the scene "
                            "and the scene is %r" % (seed, text, flag, scene))
                    deny = gen.PLACEMENT_FORBIDS.get(flag)
                    if deny is not None:
                        self.assertFalse(
                            deny.search(scene),
                            "seed %d: placement %r cannot be true of %r"
                            % (seed, text, scene))
        self.assertTrue(checked, "no prop-gated placement was ever rolled")

    def test_no_placement_asserts_something_worn(self):
        """A prop gate reads the scene alone, so a placement that names a
        garment has nothing that could check it.

        Two used to: "traces the seams of {possessive} suit" and "washes across
        {possessive} cheek and shoulder harness". Both fired on rolls wearing
        neither - a kimono has no seams to trace in a hairline and a bar owner
        has no harness - and both were reworded rather than gated, because
        gating them would have made this table a dependent of Outfit, Gear and
        Weapon in TRAIT_DEPENDENTS and widened three cascades to fix two
        bullets.
        """
        worn = ("suit", "harness", "webbing", "armor", "armour", "coverall",
                "uniform", "jacket", "helmet", "visor")
        for bullet in LIVE_PLACEMENTS:
            text = gen.split_flags(bullet)[0].lower()
            for word in worn:
                self.assertNotIn(
                    " %s" % word, text,
                    "a placement cannot name something worn - no filter reads "
                    "the Outfit, so this lands on rolls without one: %r" % bullet)


if __name__ == "__main__":
    unittest.main()
