"""No ship prompt starts a sentence in lower case.

The Detail, Command bridge, Markings and {plan} clauses are all bullets or
phrases written to sit mid-sentence, and the templates join several of them
with a full stop. Nothing capitalized them, so every prompt the model ever saw
carried about two lowercase sentence-starts - 40 across twenty ships, and half
of those were {plan} following the token template's white-void sentence.

The NPC script never has this problem because each of its clauses opens with a
{Subject} slot that pronoun_fields() capitalizes (generate-npc.py:1727). A hull
has no pronoun, so the ship script capitalizes at the join instead.

Asserted over the LIVE tables rather than a fixture: the defect is a property
of how the real bullets are punctuated, and a fixture would only prove that the
assertion runs.
"""
import random
import re
import unittest

from test.helpers import load_ship_generator

ship = load_ship_generator()
TABLES = ship.parse_tables(ship.DEFAULT_TABLES)

# A full stop, a space, then a lower-case letter. Safe against decimals -
# "1.5" has no space - and the tables carry no abbreviation in this shape.
LOWER_SENTENCE_START = re.compile(r'\. [a-z]')

# The mirror defect: a comma-joined MID-sentence continuation (Markings after
# a faction visual, e.g.) that got capitalized as if it were a new sentence.
# sentence_case() is only ever meant to run at a full-stop join; applying it
# (or leaving stray capitalization) at a comma join would print ", A crest
# painted..." mid-sentence. Nothing in LOWER_SENTENCE_START catches this - it
# is the opposite failure - so it needs its own pattern.
OVER_CAPITALIZED_COMMA_JOIN = re.compile(r', [A-Z]')


class TestNoLowercaseSentenceStarts(unittest.TestCase):
    def test_no_prompt_starts_a_sentence_in_lower_case(self):
        offenders = []
        for seed in range(60):
            rolled = ship.roll_ship(TABLES, random.Random(seed))
            for label, text in zip(("portrait", "token"),
                                   ship.build_ship_prompts(rolled)):
                for m in LOWER_SENTENCE_START.finditer(text):
                    offenders.append(
                        "seed %d %s: ...%s..."
                        % (seed, label, text[max(0, m.start() - 40):m.end() + 30]))
        self.assertEqual(
            offenders, [],
            "%d lowercase sentence-starts, first ten:\n%s"
            % (len(offenders), "\n".join(offenders[:10])))

    def test_no_comma_joined_clause_is_capitalized_as_if_a_new_sentence(self):
        offenders = []
        for seed in range(60):
            rolled = ship.roll_ship(TABLES, random.Random(seed))
            for label, text in zip(("portrait", "token"),
                                   ship.build_ship_prompts(rolled)):
                for m in OVER_CAPITALIZED_COMMA_JOIN.finditer(text):
                    offenders.append(
                        "seed %d %s: ...%s..."
                        % (seed, label, text[max(0, m.start() - 40):m.end() + 30]))
        self.assertEqual(
            offenders, [],
            "%d over-capitalized comma joins, first ten:\n%s"
            % (len(offenders), "\n".join(offenders[:10])))


class TestSentenceCase(unittest.TestCase):
    def test_capitalises_only_the_first_character(self):
        self.assertEqual(ship.sentence_case("a Karrakin hull"), "A Karrakin hull")

    def test_leaves_an_already_capital_alone(self):
        self.assertEqual(ship.sentence_case("A Karrakin hull"), "A Karrakin hull")

    def test_an_empty_string_is_safe(self):
        self.assertEqual(ship.sentence_case(""), "")
