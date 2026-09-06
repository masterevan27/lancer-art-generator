"""The clothing clause belongs to the NPC, not to nobody in particular.

Both prompt templates used to read "wearing {outfit}, the clothing following
the shape of that frame" - impersonal determiners sitting between two
sentences that name the subject perfectly happily ("{Subject} {is_are}
{height}" before it, "{Possessive} face carries {demeanor}" after it). The
pronoun machinery was already there and already used on either side, so the
clause now takes {possessive} too: "her clothing following the shape of her
frame".

{possessive} is field 3 of the four-field Pronouns bullet - the possessive
DETERMINER, her/his/their - not {object} (her/him/them) and not the
sentence-initial {Possessive}, which would capitalise mid-sentence.
"""
import random
import unittest

from test.helpers import FIXTURE_TABLES, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)


class TestClothingPossessive(unittest.TestCase):
    def _prompts(self, pronouns):
        """Both prompts for an NPC pinned to one Pronouns value.

        roll_npc() honours a trait override, so a he/him/his/man NPC is
        reachable even though the minimal fixture only lists she and they.
        """
        npc = gen.roll_npc(TABLES, random.Random(0), {"Pronouns": pronouns})
        return gen.build_prompts(npc)

    def test_both_templates_use_the_possessive(self):
        for template in (gen.PORTRAIT_TEMPLATE, gen.TOKEN_TEMPLATE):
            with self.subTest(template=template[:40]):
                self.assertIn(
                    "{possessive} clothing following the shape of {possessive} frame",
                    template)
                self.assertNotIn("shape of that frame", template)

    def test_a_she_npc_renders_her(self):
        for prompt in self._prompts("she/her/her/woman"):
            self.assertIn("her clothing following the shape of her frame.", prompt)

    def test_a_he_npc_renders_his(self):
        for prompt in self._prompts("he/him/his/man"):
            self.assertIn("his clothing following the shape of his frame.", prompt)

    def test_a_they_npc_renders_their(self):
        for prompt in self._prompts("they/them/their/person"):
            self.assertIn("their clothing following the shape of their frame.", prompt)

    def test_the_possessive_stays_lowercase_mid_sentence(self):
        """The guard against reaching for {Possessive}, the capitalised form
        the following sentence uses. The clause is always preceded mid-sentence
        by "wearing {outfit}, {faction_line}", so a capital there would render
        "wearing a flight suit, in Karrakin livery, Her clothing ...".
        """
        for pronouns in ("she/her/her/woman", "he/him/his/man",
                         "they/them/their/person"):
            for prompt in self._prompts(pronouns):
                for wrong in ("Her clothing following", "His clothing following",
                              "Their clothing following"):
                    with self.subTest(pronouns=pronouns, wrong=wrong):
                        self.assertNotIn(wrong, prompt)


if __name__ == "__main__":
    unittest.main()
