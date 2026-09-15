"""Armament is a people pool: civilians stay unarmed unless a civilian entry says otherwise."""
import unittest

from test.test_background_scene import scene


def _table(catalogue, name):
    return next(t for t in catalogue["tables"] if t["name"] == name)


class BackgroundArmamentTests(unittest.TestCase):
    def setUp(self):
        self.catalogue = scene.load_catalogue()
        self.armament = _table(self.catalogue, "Armament")

    def test_armament_is_a_population_constrained_people_pool(self):
        self.assertIn("Armament", scene.POPULATION_TRAITS)
        self.assertIn("Armament", scene.PEOPLE_TRAITS)
        texts = [v["text"] for v in self.armament["values"]]
        self.assertGreaterEqual(len(set(texts)), 20)
        self.assertTrue(any("[population=military" in t for t in texts))
        self.assertTrue(any("[population=civilian" in t for t in texts))
        self.assertTrue(any("[population=" not in t for t in texts), "an untagged unarmed choice suits every group")
        for word in ("rifle", "pistol", "sword", "sidearm"):
            self.assertTrue(any(word in t for t in texts), word)

    def test_civilians_never_carry_military_armament(self):
        civilian = next(v["text"] for v in _table(self.catalogue, "Population")["values"] if "[population=civilian]" in v["text"])
        for env in ("outdoor", "indoor", "space"):
            plans = scene.preview({"environment": env, "seed": 3, "count": 8, "traits": {"Population": civilian},
                                   "locked": ["Population"]}, self.catalogue)["plans"]
            for plan in plans:
                kinds = scene._population_kinds({"Armament": plan["traits"]["Armament"]})
                self.assertIn("civilian", kinds, plan["traits"]["Armament"])
        military_only = next(v["text"] for v in self.armament["values"] if "[population=military]" in v["text"])
        with self.assertRaisesRegex(ValueError, "[Pp]opulation"):
            scene.preview({"traits": {"Population": civilian, "Armament": military_only}}, self.catalogue)

    def test_military_armament_is_varied_and_mostly_armed(self):
        military = next(v["text"] for v in _table(self.catalogue, "Population")["values"] if "[population=military]" in v["text"])
        chosen = []
        for seed in range(0, 400, 8):
            plans = scene.preview({"seed": seed, "count": 8, "traits": {"Population": military},
                                   "locked": ["Population"]}, self.catalogue)["plans"]
            chosen.extend(p["traits"]["Armament"] for p in plans)
        armed = [t for t in chosen if "[population=military" in t]
        self.assertGreater(len(armed) / len(chosen), 0.55, "armed military groups should be the common case")
        self.assertLess(len(armed) / len(chosen), 0.9, "some military groups stay unarmed or stowed")
        self.assertGreaterEqual(len(set(armed)), 12, "a good spread of weapon choices")
        for word in ("rifle", "pistol", "sword"):
            self.assertTrue(any(word in t for t in armed), word)

    def test_armament_reaches_prompts_only_with_people(self):
        plan = scene.preview({"seed": 11}, self.catalogue)["plans"][0]
        self.assertIn("Armament:", plan["prompt"])
        self.assertIn("never aimed", plan["prompt"])
        self.assertNotIn("[population=", plan["prompt"])
        for extra in ({"populatePeople": False}, {"view": "topdown"}):
            quiet = scene.preview({"seed": 11, "traits": plan["traits"], **extra}, self.catalogue)["plans"][0]
            self.assertNotIn("Armament:", quiet["prompt"])
            self.assertNotIn("never aimed", quiet["prompt"])
            self.assertEqual(quiet["traits"]["Armament"], plan["traits"]["Armament"])
        omitted = scene.preview({"seed": 11, "traits": {"Armament": ""}}, self.catalogue)["plans"][0]
        self.assertEqual(omitted["traits"]["Armament"], "")
        self.assertNotIn("Armament:", omitted["prompt"])

    def test_armed_scenes_keep_weapons_still_in_motion_prompts(self):
        armed = next(v["text"] for v in self.armament["values"] if "[population=military,mixed]" in v["text"])
        plan = scene.preview({"seed": 5, "traits": {"Armament": armed}}, self.catalogue)["plans"][0]
        self.assertIn("[population=", plan["traits"]["Population"])
        self.assertNotIn("[population=civilian]", plan["traits"]["Population"])
        self.assertIn("slung or holstered", plan["motionPrompt"])
        unarmed = scene.preview({"seed": 5, "traits": {"Armament": ""}}, self.catalogue)["plans"][0]
        self.assertNotIn("slung or holstered", unarmed["motionPrompt"])


if __name__ == "__main__":
    unittest.main()
