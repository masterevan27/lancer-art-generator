"""Every ship prompt says, in words, that the subject is a spacecraft.

The generator rolled hulls that krea2TurboInt8 rendered as present-day surface
warships sitting in water. It is not hard to see why once the assembled prompt
is read back: nothing in either template ever said "spacecraft". The subject
slot arrived as "a cruiser", "a destroyer", "a patrol boat", "a cargo ship";
the hull sentence said "The hull is..."; and the only science-fiction word in
the whole portrait prompt was "sci-fi" buried in the closing tag block, with
the token prompt's closing block saying nothing stronger than "vehicle". Every
class noun the '## Ship type' table draws on is a real-world naval one, because
that is the register the setting is written in - so absent a contradicting
assertion, a grey hull with a belted flank and a raised centreline deck is a
battleship on the sea, and the model was right to draw one.

The fix cannot be a negation. Lancer_Scene_Workflow_v1.json runs the sampler at
CFG 1.0 with ConditioningZeroOut on the negative input, so there is no negative
prompt to put "not a boat" into, and the tables file's "Never write a negation"
section says the same thing for the same reason. What is left is positive
assertion, repeated at the positions a diffusion model actually weights: the
opening subject slot, the middle of the prompt where the naval-flavoured hull
description lands, and the closing tag block.

Asserted over the LIVE tables, like test_ship_prompts.py, because the thing
being defended is a property of the real assembled prompt. A fixture would only
prove the assertion runs.

The table guard at the bottom is the other half. Two live '## Hull' bullets did
not merely fail to say "spacecraft" - they asked for water outright ("a
steel-grey hull on a wet-navy silhouette, a flared clipper bow above a recessed
anchor housing", "a painted waterline stripe running its whole length"), which
no amount of template language wins against. They are rewritten, and this holds
the rewrite: a future bullet reaching for the same real-world naval detail is
the exact defect coming back, and it would come back silently.
"""
import random
import re
import unittest

from test.helpers import load_ship_generator

ship = load_ship_generator()
TABLES = ship.parse_tables(ship.DEFAULT_TABLES)

# The words that assert the subject's medium. Checked case-insensitively as
# whole words, so "spacecraft's" in the hull sentence counts and "spaceport"
# in a '## Backdrop' scene does not - a spaceport on the horizon says nothing
# about what the subject in the foreground is.
CRAFT_WORD = re.compile(r'\b(spacecraft|spaceship|starship)\b', re.I)

# How far into the prompt the FIRST such word has to appear. Both templates
# open "{shot} of a spacecraft - {ship}", and the longest shot descriptor in
# '## Backdrop' is "A cathedral-scale wide shot" (27 chars); the token
# template's is the fixed "A top-down orthographic illustration" (35). 60
# chars leaves room for either and still fails if the assertion drifts back
# behind the twenty-odd words of a '## Ship type' bullet, which is the whole
# point of putting it in front of them.
OPENING_WINDOW = 60

# The closing tag block is the last sentence of each template. A diffusion
# text encoder weights the tail hard, and it is also the first thing lost to
# truncation - which is why test_ship_prompt_budget.py holds the max as well
# as the p99.
CLOSING_WINDOW = 160

# Real-world surface-navy detail that no spaceship bullet may carry. Each of
# these describes a hull's relationship to WATER and nothing else, so a bullet
# carrying one is asking the renderer for a boat however the template opens.
#
# 'anchor' carries a negative lookbehind for "at ". A hull with an anchor on
# it is a boat - "a recessed anchor housing" is half of the bullet that
# started this - but "at anchor" is a dead idiom for holding station, and a
# '## Backdrop' scene uses it correctly of a warfleet in orbit. SUBJECT_TRAITS
# already excludes Backdrop, so today the lookbehind changes nothing; it is
# here so the pattern stays honest if this guard is ever pointed at the scene
# table, which is the sort of reuse that would otherwise empty a live bullet.
WET_NAVY = re.compile(
    r'\b(waterline|wet[- ]navy|clipper bow|hawse|gunwale|bow wave|keelson|'
    r'bilge|draught marks|plimsoll)\b'
    r'|(?<!at )\banchors?\b', re.I)

# The traits whose bullets describe the subject's own hull and fittings. A
# '## Backdrop' scene is deliberately excluded: it describes the setting, and
# "a warfleet at anchor above a world" is a legitimate scene sentence.
SUBJECT_TRAITS = ("Ship type", "Hull", "Detail", "Weapon", "Shield generator",
                  "Launch catapult", "Command bridge", "Markings", "Condition")


def rolled_prompts(seeds=range(80)):
    """[(seed, label, prompt_text)] over the live tables."""
    out = []
    for seed in seeds:
        rolled = ship.roll_ship(TABLES, random.Random(seed))
        for label, text in zip(("portrait", "token"),
                               ship.build_ship_prompts(rolled)):
            out.append((seed, label, text))
    return out


PROMPTS = rolled_prompts()


class TestTheSubjectIsNamedAsSpacecraft(unittest.TestCase):
    def test_the_sample_is_not_vacuous(self):
        self.assertEqual(len(PROMPTS), 160)

    def test_every_prompt_names_the_subject_as_a_spacecraft(self):
        offenders = ["seed %d %s" % (seed, label)
                     for seed, label, text in PROMPTS
                     if not CRAFT_WORD.search(text)]
        self.assertEqual(
            offenders, [],
            "%d prompts never say spacecraft/spaceship/starship: %s"
            % (len(offenders), ", ".join(offenders[:10])))

    def test_the_assertion_lands_in_the_opening_subject_slot(self):
        offenders = []
        for seed, label, text in PROMPTS:
            m = CRAFT_WORD.search(text)
            if m is None or m.start() >= OPENING_WINDOW:
                offenders.append("seed %d %s: %r" % (seed, label,
                                                     text[:OPENING_WINDOW]))
        self.assertEqual(
            offenders, [],
            "%d prompts do not assert the medium within the first %d chars, "
            "first five:\n%s"
            % (len(offenders), OPENING_WINDOW, "\n".join(offenders[:5])))

    def test_the_closing_tag_block_asserts_it_again(self):
        offenders = []
        for seed, label, text in PROMPTS:
            if not CRAFT_WORD.search(text[-CLOSING_WINDOW:]):
                offenders.append("seed %d %s: %r" % (seed, label,
                                                     text[-CLOSING_WINDOW:]))
        self.assertEqual(
            offenders, [],
            "%d prompts do not repeat the medium in the closing tag block, "
            "first five:\n%s" % (len(offenders), "\n".join(offenders[:5])))

    def test_the_hull_sentence_attributes_the_hull_to_the_craft(self):
        """The middle assertion, where the naval-flavoured hull text lands.

        Between the opening slot and the closing block sits the longest run of
        naval vocabulary in the prompt - belted flanks, barbette rings, a
        raised centreline deck. "The hull is" left that run unattributed for
        two hundred-odd tokens; "The spacecraft's hull is" does not.
        """
        offenders = ["seed %d %s" % (seed, label)
                     for seed, label, text in PROMPTS
                     if "The spacecraft's hull is" not in text]
        self.assertEqual(
            offenders, [],
            "%d prompts do not attribute the hull to the craft: %s"
            % (len(offenders), ", ".join(offenders[:10])))


class TestNoBulletAsksForAWaterHull(unittest.TestCase):
    def test_no_rolled_subject_bullet_carries_surface_navy_detail(self):
        offenders = []
        for seed in range(400):
            rolled = ship.roll_ship(TABLES, random.Random(seed))
            for trait in SUBJECT_TRAITS:
                m = WET_NAVY.search(rolled[trait])
                if m:
                    offenders.append("%s: %r (seed %d)"
                                     % (trait, rolled[trait], seed))
        self.assertEqual(
            sorted(set(offenders)), [],
            "%d subject bullets ask the renderer for a surface ship, "
            "first five:\n%s"
            % (len(set(offenders)), "\n".join(sorted(set(offenders))[:5])))

    def test_the_guard_would_catch_the_bullets_it_was_written_for(self):
        """The two live bullets this test was added because of.

        A guard that matches nothing proves nothing, and both of the strings
        below were in prompts/spaceship-generator-tables.md when this file was
        written. Kept verbatim so the pattern cannot be loosened into a no-op.
        """
        self.assertTrue(WET_NAVY.search(
            "a steel-grey hull on a wet-navy silhouette, a flared clipper bow "
            "above a recessed anchor housing"))
        self.assertTrue(WET_NAVY.search(
            "riveted courses laid in overlapping bands and a painted "
            "waterline stripe running its whole length"))

    def test_the_guard_leaves_legitimate_space_prose_alone(self):
        """Words that read as naval but are honest spacecraft vocabulary.

        'prow', 'keel', 'mast' and 'stern' are all carried by live bullets and
        all read correctly on a starship - science fiction has used them since
        it had ships at all. Only the water-specific detail is barred, and this
        pins the line so a later tightening of WET_NAVY cannot quietly empty
        the '## Hull' table.
        """
        for legitimate in (
                "a ram prow crowned with gilt statuary",
                "a grey hull built long and narrow on a triple-keel frame",
                "sensor masts and long-baseline optics",
                "a smooth belly pod slung under the keel",
                "a warfleet at anchor above a world crusted with cathedral cities",
        ):
            with self.subTest(legitimate):
                self.assertIsNone(WET_NAVY.search(legitimate))
