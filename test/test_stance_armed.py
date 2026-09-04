"""An unarmed NPC must not be posed brandishing a weapon.

Seven Stance bullets reference a weapon - a blade held, a hilt gripped, a
weapon raised overhead - but carried only '|| hands'. Only 'gun' was gated on
the Weapon roll, so those seven could land on a figure whose Weapon came up
empty, and the prompt then posed them wielding something no earlier sentence
names. Rare on a plain roll; routine under --unarmed, which is what made it
worth a flag of its own.

'armed' is the wider flag - any weapon at all. 'gun' stays narrower: a firearm
being handled. A bullet may carry both.
"""
import random
import unittest

from test.helpers import FIXTURE_TABLES, REPO, load_generator, bullets_for

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")

WEAPON_WORDS = ("blade", "hilt", "weapon", "sidearm", "carbine", "rifle")


class TestArmedStanceFlag(unittest.TestCase):
    def test_every_weapon_naming_bullet_carries_a_weapon_flag(self):
        for bullet in bullets_for(LIVE, "Stance"):
            text, flags = gen.split_flags(bullet)
            if not any(w in text.lower() for w in WEAPON_WORDS):
                continue
            with self.subTest(bullet=bullet):
                self.assertTrue(
                    "armed" in flags or "gun" in flags,
                    "Stance bullet names a weapon but is gated on neither "
                    "'armed' nor 'gun': %s" % bullet)

    def test_an_unarmed_npc_never_gets_an_armed_pose(self):
        """Assert directly on the rolled text rather than reverse-mapping it.

        roll_npc() substitutes pronoun placeholders into the rolled Stance
        value, so a bullet containing '{possessive}' no longer string-equals
        the source bullet it came from by the time it lands in npc["Stance"].
        Reverse-mapping from the rolled text back to its source bullet, to
        then read that bullet's flags, is therefore unreliable for exactly
        the bullets this test most needs to catch. Checking the rolled text
        itself for the words a weapon-naming pose would use is what actually
        pins the guarantee: an unarmed figure is never posed wielding
        something.
        """
        for seed in range(100):
            npc = gen.roll_npc(TABLES, random.Random(seed),
                               {"Role": "a dockworker"}, unarmed=True)
            self.assertEqual(npc["Weapon"], "")
            stance = npc["Stance"].lower()
            for word in WEAPON_WORDS:
                self.assertNotIn(word, stance,
                                 "seed %d: %s" % (seed, npc["Stance"]))

    def test_an_armed_npc_can_still_reach_an_armed_pose(self):
        """The filter must not make those seven bullets permanently dead."""
        armed_bullets = [b for b in bullets_for(LIVE, "Stance")
                         if "armed" in gen.split_flags(b)[1]]
        self.assertGreaterEqual(
            len(armed_bullets), 7,
            "expected at least the seven weapon-naming bullets to be tagged")


if __name__ == "__main__":
    unittest.main()
