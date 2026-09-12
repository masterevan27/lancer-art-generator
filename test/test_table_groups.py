"""Group references: '- => Name' in a rolled table is one slot that resolves
from '## Name'. See docs/superpowers/specs/2026-09-12-table-groups-design.md.
"""
import random
import unittest
from pathlib import Path

from test.helpers import FIXTURE_TABLES, REPO, load_generator

gen = load_generator()
GROUPS_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "tables-groups.md"


class TestReferenceHelpers(unittest.TestCase):
    def test_a_reference_names_its_target_with_flags_aside(self):
        self.assertEqual(gen.reference_target("=> Flight suits"), "Flight suits")
        self.assertEqual(gen.reference_target("=> Flight suits || @gundam"), "Flight suits")
        self.assertEqual(gen.reference_target("=>  Black dresses (gundam)  "), "Black dresses (gundam)")
        self.assertTrue(gen.is_reference("=> Flight suits"))

    def test_an_ordinary_bullet_is_not_a_reference(self):
        for bullet in ["a jacket", "a jacket || civ", "=>", "=> ", " => x", "a => b", "{Subject} {wear} a hat."]:
            with self.subTest(bullet=bullet):
                self.assertIsNone(gen.reference_target(bullet))
                self.assertFalse(gen.is_reference(bullet))

    def test_references_in_reads_the_base_table_and_its_variants_once_each(self):
        tables = {
            "Outfit": ["a jacket", "=> Flight suits", "=> Flight suits", "=> Robes || @neosamurai"],
            "Outfit (she) +": ["=> Crop tops"],
            "Outfit (he) +": ["a vest"],
            "Flight suits": ["a flight suit"], "Robes": ["a robe"], "Crop tops": ["a crop top"],
        }
        self.assertEqual(gen.references_in(tables, "Outfit"), {
            "Flight suits": "=> Flight suits",
            "Robes": "=> Robes || @neosamurai",
            "Crop tops": "=> Crop tops",
        })
        self.assertEqual(gen.references_in(tables, "Flight suits"), {})

    def test_group_headings_are_the_target_and_its_present_variants(self):
        tables = {"Flight suits": ["a"], "Flight suits (she) +": ["b"], "Flight suits (gundam)": ["c"]}
        self.assertEqual(gen.group_headings(tables, "Flight suits", "she"),
                         ["Flight suits", "Flight suits (she) +"])
        self.assertEqual(gen.group_headings(tables, "Flight suits", "he"), ["Flight suits"])
        self.assertEqual(gen.group_headings(tables, "Flight suits (gundam)", "she"),
                         ["Flight suits (gundam)"])

    def test_group_tables_is_every_referenced_heading_with_its_variants(self):
        tables = {
            "Outfit": ["=> Flight suits"], "Outfit (she) +": ["=> Crop tops"],
            "Flight suits": ["a"], "Flight suits (she) +": ["b"], "Flight suits (he)": ["c"],
            "Crop tops": ["d"], "Unreferenced": ["e"],
        }
        self.assertEqual(gen.group_tables(tables),
                         {"Flight suits", "Flight suits (she) +", "Flight suits (he)", "Crop tops"})


def fixture_tables():
    """A fresh copy of the minimal fixture, so a test can add groups to it."""
    return {k: list(v) for k, v in gen.parse_tables(FIXTURE_TABLES).items()}


class TestCheckGroupReferences(unittest.TestCase):
    def check(self, tables):
        return gen.check_group_references(tables)

    def test_a_well_formed_file_has_no_complaints(self):
        tables = fixture_tables()
        tables["Outfit"] += ["=> Plates", "=> Neon (beta) || @beta"]
        tables["Outfit (she) +"] = ["=> Crop tops"]
        tables["Plates"] = ["lacquered plate", "scuffed plate || mil"]
        tables["Plates (she) +"] = ["a fitted plate"]
        tables["Neon (beta)"] = ["a neon jacket", "a neon visor jacket"]
        tables["Crop tops"] = ["a crop top || civ"]
        self.assertEqual(self.check(tables), [])

    def test_a_missing_target_is_named(self):
        tables = fixture_tables()
        tables["Outfit"].append("=> Nowhere")
        [problem] = self.check(tables)
        self.assertIn("Nowhere", problem)
        self.assertIn("Outfit", problem)

    def test_a_rolled_table_or_its_variant_cannot_be_a_group(self):
        for target in ["Headgear", "Build (she)", "Outfit (she) +"]:
            tables = fixture_tables()
            tables.setdefault(target, ["x"])
            tables["Outfit"].append("=> " + target)
            with self.subTest(target=target):
                self.assertTrue(any("rolled table" in p for p in self.check(tables)), self.check(tables))

    def test_a_reference_carries_no_behavioural_flags(self):
        tables = fixture_tables()
        tables["Plates"] = ["a plate"]
        tables["Outfit"].append("=> Plates || civ @alpha")
        [problem] = self.check(tables)
        self.assertIn("civ", problem)
        self.assertNotIn("@alpha", problem.split("carries flags")[1].split(";")[0])

    def test_one_reference_per_group_per_table(self):
        tables = fixture_tables()
        tables["Plates"] = ["a plate"]
        tables["Outfit"] += ["=> Plates", "=> Plates || @alpha"]
        self.assertTrue(any("more than once" in p for p in self.check(tables)))
        # An xN weight is N copies of ONE text, which is fine.
        tables["Outfit"] = [b for b in tables["Outfit"] if b != "=> Plates || @alpha"] + ["=> Plates"]
        self.assertEqual(self.check(tables), [])

    def test_a_group_cannot_reference_a_group(self):
        tables = fixture_tables()
        tables["Outfit"].append("=> Plates")
        tables["Plates"] = ["a plate", "=> Heavy plates"]
        tables["Heavy plates"] = ["a heavy plate"]
        self.assertTrue(any("one level" in p for p in self.check(tables)))

    def test_a_themed_groups_members_carry_no_tags(self):
        tables = fixture_tables()
        tables["Outfit"].append("=> Neon (beta) || @beta")
        tables["Neon (beta)"] = ["a neon jacket", "a neon visor || @beta"]
        [problem] = self.check(tables)
        self.assertIn("a neon visor", problem)
        # A neutral group's members may be tagged; the tag then filters inside the group.
        tables["Outfit"][-1] = "=> Neon (beta)"
        self.assertEqual(self.check(tables), [])

    def test_a_reference_lives_only_in_a_rolled_table_the_main_draw_handles(self):
        for name in ["Pronouns", "Theme", "Stance", "Animation"]:
            tables = fixture_tables()
            tables["Plates"] = ["a plate"]
            tables.setdefault(name, []).append("=> Plates")
            with self.subTest(name=name):
                self.assertTrue(any("only read in" in p for p in self.check(tables)))

    def test_check_tables_refuses_a_malformed_file_with_every_problem_listed(self):
        tables = fixture_tables()
        tables["Outfit"] += ["=> Nowhere", "=> Headgear"]
        with self.assertRaises(SystemExit) as cm:
            gen.check_tables(tables, Path("tables.md"))
        self.assertIn("Nowhere", str(cm.exception))
        self.assertIn("Headgear", str(cm.exception))


GROUPS = gen.parse_tables(GROUPS_FIXTURE)


def roll(seed, **overrides):
    return gen.roll_npc(GROUPS, random.Random(seed), overrides or None)


def outfit_family(npc):
    """Which fixture family the rolled Outfit came from."""
    raw = npc["_raw"]["Outfit"]
    for key in ["Plates", "Plates (she) +", "Neon (beta)", "Civvies", "Crop tops"]:
        if raw in GROUPS[key]:
            return key.partition(" (")[0]
    return raw


class TestResolution(unittest.TestCase):
    def test_a_drawn_reference_resolves_to_a_member_and_raw_holds_the_member(self):
        seen = set()
        for seed in range(200):
            npc = roll(seed)
            raw = npc["_raw"]["Outfit"]
            self.assertIsNone(gen.reference_target(raw), "%d: _raw holds a reference" % seed)
            self.assertIsNone(gen.reference_target(npc["Outfit"]))
            seen.add(outfit_family(npc))
        self.assertIn("Plates", seen)
        self.assertIn("grey coveralls", seen)

    def test_a_group_is_one_slot(self):
        """Plates holds four weighted members and grey coveralls is one bullet;
        with the reference weighing one slot they come up about as often."""
        counts = {"Plates": 0, "grey coveralls": 0}
        n = 3000
        for seed in range(n):
            fam = outfit_family(roll(seed))
            if fam in counts:
                counts[fam] += 1
        ratio = counts["Plates"] / counts["grey coveralls"]
        self.assertGreater(ratio, 0.75, counts)
        self.assertLess(ratio, 1.33, counts)

    def test_members_are_weighted_inside_the_group(self):
        counts = {}
        for seed in range(3000):
            npc = roll(seed)
            if outfit_family(npc) == "Plates":
                counts[npc["_raw"]["Outfit"]] = counts.get(npc["_raw"]["Outfit"], 0) + 1
        self.assertGreater(counts["x2 dented plate".replace("x2 ", "")], counts["lacquered plate"] * 1.4, counts)

    def test_an_ineligible_group_leaves_the_pool(self):
        """Civvies holds only civ members. A mil Role drops them, and the
        reference goes with them rather than falling back to the members."""
        mil = next(b for b in GROUPS["Role"] if "mil" in gen.split_flags(b)[1])
        for seed in range(300):
            self.assertNotEqual(outfit_family(roll(seed, Role=mil)), "Civvies", seed)

    def test_a_themed_reference_obeys_the_theme_filter_and_share(self):
        alpha = next(b for b in GROUPS["Theme"] if gen.split_flags(b)[0] == "alpha")
        beta = next(b for b in GROUPS["Theme"] if gen.split_flags(b)[0] == "beta")
        for seed in range(300):
            self.assertNotEqual(outfit_family(roll(seed, Theme=alpha)), "Neon", seed)
        hits = sum(1 for seed in range(600) if outfit_family(roll(seed, Theme=beta)) == "Neon")
        self.assertGreater(hits / 600, 0.4, "a themed group should carry the theme share")

    def test_a_womens_variant_joins_the_group_and_a_womens_reference_is_hers_alone(self):
        she = next(b for b in GROUPS["Pronouns"] if b.startswith("she"))
        he = next(b for b in GROUPS["Pronouns"] if b.startswith("he"))
        raws_she = {roll(s, Pronouns=she)["_raw"]["Outfit"] for s in range(600)}
        raws_he = {roll(s, Pronouns=he)["_raw"]["Outfit"] for s in range(600)}
        self.assertIn("a fitted plate", raws_she)
        self.assertIn("a crop top || civ", raws_she)
        self.assertNotIn("a fitted plate", raws_he)
        self.assertNotIn("a crop top || civ", raws_he)

    def test_the_probe_records_each_groups_pool_and_stays_inert(self):
        probe = {}
        plain = roll(7)
        probed = gen.roll_npc(GROUPS, random.Random(7), None, probe=probe)
        self.assertEqual(plain, probed)
        self.assertIn("Plates", probe)
        self.assertTrue(set(probe["Plates"]) <= set(GROUPS["Plates"] + GROUPS["Plates (she) +"]))
        self.assertIn("=> Plates", probe["Outfit"])

    def test_same_seed_reproduces_the_member(self):
        for seed in range(50):
            self.assertEqual(roll(seed)["_raw"]["Outfit"], roll(seed)["_raw"]["Outfit"])

    def test_a_forced_member_is_kept_and_a_forced_reference_is_refused(self):
        npc = roll(3, Outfit="scuffed plate || mil")
        self.assertEqual(npc["_raw"]["Outfit"], "scuffed plate || mil")
        self.assertEqual(npc["Outfit"], "scuffed plate")
        with self.assertRaises(SystemExit) as cm:
            roll(3, Outfit="=> Plates")
        self.assertIn("Outfit", str(cm.exception))

    def test_a_file_without_references_rolls_as_before(self):
        """The minimal fixture and its snapshot are the gate; this is the same
        statement made against the groups fixture with its references removed."""
        stripped = {k: [b for b in v if gen.reference_target(b) is None] for k, v in GROUPS.items()}
        for seed in range(30):
            a = gen.roll_npc(stripped, random.Random(seed), None)
            b = gen.roll_npc(stripped, random.Random(seed), None)
            self.assertEqual(a, b)

    def test_the_raw_pool_is_the_last_resort_when_the_union_survives_but_every_parent_bullet_falls(self):
        """A themed reference the theme gate drops, next to a civ bullet the
        mil gate drops: the union stays alive through the reference's own
        (untagged) members, but the parent's own two bullets both empty out,
        so `parent` is empty too and the fallback has to reach the raw,
        un-narrowed pool. A reference drawn from there still resolves through
        its member pool exactly as a narrowed one would."""
        tables = {**GROUPS, "Outfit": ["=> Neon (beta) || @beta", "a jacket || civ"]}
        del tables["Outfit (she) +"]
        alpha = next(b for b in GROUPS["Theme"] if gen.split_flags(b)[0] == "alpha")
        mil = next(b for b in GROUPS["Role"] if "mil" in gen.split_flags(b)[1])
        legal = {"a jacket || civ", "a neon techwear jacket", "a neon visor jacket"}
        for seed in range(50):
            npc = gen.roll_npc(tables, random.Random(seed), {"Theme": alpha, "Role": mil})
            raw = npc["_raw"]["Outfit"]
            self.assertIsNone(gen.reference_target(raw), seed)
            self.assertIn(raw, legal, seed)

    def test_an_emptied_reference_falls_back_to_the_narrowed_parent_not_the_raw_pool(self):
        """A reference bullet that itself carries no flags survives the mil
        gate even though both of its members do not, so the narrowed parent
        pool - not the raw one - holds just that reference; a sibling bullet
        the SAME gate actually dropped from the union (the civ jacket) must
        not be re-admitted by a fallback that reached further than it should."""
        tables = {**GROUPS, "Outfit": ["=> Civvies", "a jacket || civ"]}
        del tables["Outfit (she) +"]
        mil = next(b for b in GROUPS["Role"] if "mil" in gen.split_flags(b)[1])
        legal = {"a cardigan || civ", "a sundress || civ"}
        for seed in range(50):
            npc = gen.roll_npc(tables, random.Random(seed), {"Role": mil})
            raw = npc["_raw"]["Outfit"]
            self.assertIsNone(gen.reference_target(raw), seed)
            self.assertNotEqual(raw, "a jacket || civ", seed)
            self.assertIn(raw, legal, seed)
