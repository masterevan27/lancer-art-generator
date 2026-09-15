"""People choices must stay coherent through rerolls, locks and saved plans."""
import unittest

from test.test_background_scene import scene


class BackgroundPeopleTests(unittest.TestCase):
    def setUp(self):
        self.catalogue = scene.load_catalogue()

    def test_population_constraints_work_in_both_directions_and_batches(self):
        # A miniature real catalogue makes conflicting civilian/military choices explicit.
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tables.md"
            path.write_text("## Outdoor location\n- [outdoor] a yard\n"
                            "## Activity\n- [population=civilian] browsing stalls\n"
                            "- [population=military] standing guard\n"
                            "## Clothing and equipment\n- [population=civilian,mixed] casual clothing\n"
                            "- [population=military,mixed] field uniforms\n"
                            "## Population\n- [population=civilian] civilian visitors\n"
                            "- [population=military] military personnel\n", encoding="utf-8")
            catalogue = scene.load_catalogue(path)
        military = "[population=military] military personnel"
        uniforms = "[population=military,mixed] field uniforms"
        for traits in ({"Population": military}, {"Activity": "[population=military] standing guard"}):
            plans = scene.preview({"seed": 42, "count": 5, "traits": traits, "locked": list(traits)}, catalogue)["plans"]
            for plan in plans:
                self.assertEqual(plan["traits"]["Population"], military)
                self.assertEqual(plan["traits"]["Clothing and equipment"], uniforms)
                self.assertNotIn("[population=", plan["prompt"])
        with self.assertRaisesRegex(ValueError, "[Pp]opulation"):
            scene.preview({"traits": {"Population": military, "Activity": "[population=civilian] browsing stalls"}}, catalogue)

    def test_people_traits_roll_save_and_disappear_from_unpopulated_prompts(self):
        names = {"Population", "Clothing and equipment", "Adult age mix", "Appearance variety", "Activity"}
        for env in ("outdoor", "indoor", "space"):
            plans = scene.preview({"environment": env, "seed": 81, "count": 5}, self.catalogue)["plans"]
            self.assertTrue(names <= set(plans[0]["traits"]))
            self.assertGreater(len({tuple(p["traits"][n] for n in sorted(names)) for p in plans}), 1)
            self.assertEqual(scene.validate_plans({"plans": plans}, self.catalogue), plans)
            locked = scene.preview({"environment": env, "seed": 1, "count": 5,
                                    "traits": plans[0]["traits"], "locked": list(names)}, self.catalogue)["plans"]
            for plan in locked:
                self.assertEqual({n: plan["traits"][n] for n in names}, {n: plans[0]["traits"][n] for n in names})
            for extra in ({"populatePeople": False}, {"view": "topdown"}):
                empty = scene.preview({"environment": env, "traits": plans[0]["traits"], **extra}, self.catalogue)["plans"][0]
                for name in names:
                    self.assertNotIn(name + ":", empty["prompt"])
                self.assertEqual(empty["traits"], plans[0]["traits"])

    def test_disabled_clothing_choices_constrain_the_random_population(self):
        clothing = next(t for t in self.catalogue["tables"] if t["name"] == "Clothing and equipment")
        clothing["values"] = [v for v in clothing["values"] if "[population=military]" in v["text"]]
        for extra in ({}, {"populatePeople": False}, {"view": "topdown"}):
            plans = scene.preview({"seed": 1, "count": 8, **extra}, self.catalogue)["plans"]
            self.assertTrue(all("[population=military]" in p["traits"]["Population"] for p in plans))
        # Explicit omission needs no garment and must not constrain the population.
        civilian = next(v["text"] for t in self.catalogue["tables"] if t["name"] == "Population"
                        for v in t["values"] if "[population=civilian]" in v["text"])
        plan = scene.preview({"traits": {"Population": civilian, "Clothing and equipment": ""}}, self.catalogue)["plans"][0]
        self.assertEqual(plan["traits"]["Clothing and equipment"], "")

    def test_vacuum_rejects_unsealed_ground_clothing(self):
        clothing = next(t for t in self.catalogue["tables"] if t["name"] == "Clothing and equipment")
        sleeves = next(v["text"] for v in clothing["values"] if "rolled sleeves" in v["text"])
        with self.assertRaisesRegex(ValueError, "incompatible trait"):
            scene.preview({"environment": "space", "traits": {"Clothing and equipment": sleeves}}, self.catalogue)

    def test_background_uses_npc_painterly_style_without_portrait_framing(self):
        plan = scene.preview({"seed": 7}, self.catalogue)["plans"][0]
        for phrase in ("painterly illustration", "fine grain texture", "clean linework", "halftone", "painterly brushwork"):
            self.assertIn(phrase, plan["prompt"])
        self.assertIn("full-frame", plan["prompt"])
        self.assertNotIn("Shallow depth of field", plan["prompt"])
        self.assertNotIn("median age around 20-25", plan["prompt"])


if __name__ == "__main__":
    unittest.main()
