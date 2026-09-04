"""Stage 0 renders the token again in a forced A-pose.

Skin-weight transfer is proximity-based, so the Hunyuan3D shell and the
SAM3DBody base have to be in the same pose or the shoulders smear. The base
is always A-pose; this is what puts the shell there too, by re-rendering the
source image rather than correcting for the mismatch afterwards.

Nothing here goes near --regen-manifest. Stage 0 is a different tool
rendering a different image, and both of that path's guards - the --set-trait
refusal and Stance's absence from REROLLABLE_TRAITS - stay exactly as they are.
"""
import unittest

from test.helpers import load_3d, load_generator, manifest_entry

gen = load_generator()
d3 = load_3d()

# A stance nothing else would produce, so "the forced stance replaced it" and
# "the roll happened to agree" cannot be confused.
CROUCH = "crouched low and coiled, weight braced forward on one arm"
ARMED = {"Weapon": "a heavy service rifle held in both hands",
         "Gear": "a bulky tool case"}


class TestAposeStance(unittest.TestCase):
    def test_the_stance_reaches_the_token_prompt(self):
        self.assertIn(d3.APOSE_STANCE, d3.apose_prompt(manifest_entry(1)))

    def test_the_rolled_stance_does_not(self):
        entry = manifest_entry(1, {"Stance": CROUCH})
        self.assertNotIn("crouched low", d3.apose_prompt(entry))

    def test_the_stance_describes_a_neutral_standing_pose(self):
        for phrase in ("standing straight", "arms held slightly away",
                       "palms forward", "feet shoulder-width apart"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, d3.APOSE_STANCE)

    def test_the_stance_reads_as_a_stance_bullet(self):
        """It substitutes into '{Subject} {is_are} {stance}, both feet...'.

        A leading capital or a trailing period would produce 'She is Standing.
        , both feet in frame', so both are banned - exactly as they are for
        every bullet in the live Stance table.
        """
        self.assertFalse(d3.APOSE_STANCE.endswith("."))
        self.assertTrue(d3.APOSE_STANCE[0].islower())

    def test_both_hands_are_emptied(self):
        """An NPC holding a carbine in both hands cannot hold an A-pose."""
        npc = d3.apose_npc(manifest_entry(2, ARMED))
        self.assertEqual(npc["Weapon"], "")
        self.assertEqual(npc["Gear"], "")

    def test_no_carry_sentence_survives_into_the_prompt(self):
        prompt = d3.apose_prompt(manifest_entry(2, ARMED))
        self.assertNotIn("service rifle", prompt)
        self.assertNotIn("tool case", prompt)

    def test_the_manifest_entry_is_not_mutated(self):
        """The caller still needs it for the dossier and the log line."""
        entry = manifest_entry(3, {"Stance": CROUCH})
        d3.apose_npc(entry)
        self.assertEqual(entry["traits"]["Stance"], CROUCH)

    def test_a_pre_weapon_entry_round_trips(self):
        """Entries written before '## Weapon' existed carry no Weapon key.

        build_prompts() has a .get shim for exactly this; the rebuild must not
        defeat it with a KeyError of its own.
        """
        entry = manifest_entry(4)
        del entry["traits"]["Weapon"]
        self.assertIn(d3.APOSE_STANCE, d3.apose_prompt(entry))

    def test_an_entry_with_no_height_round_trips(self):
        """Same, for entries written before '## Height' existed."""
        entry = manifest_entry(5)
        del entry["traits"]["Height"]
        self.assertIn(d3.APOSE_STANCE, d3.apose_prompt(entry))

    def test_an_entry_with_no_young_flag_round_trips(self):
        entry = manifest_entry(6)
        del entry["young"]
        self.assertIn(d3.APOSE_STANCE, d3.apose_prompt(entry))


if __name__ == "__main__":
    unittest.main()
