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

    def test_a_replacement_group_variant_replaces_the_group_the_way_a_table_does(self):
        """variant_table()'s two forms, mirrored: 'Name (she)' stands in for
        the group, 'Name (she) +' is added to it. A group is a table like any
        other and the preamble says so; returning both would give it the one
        shape no rolled table has."""
        tables = {"Plates": ["a"], "Plates (she)": ["b"], "Plates (she) +": ["c"],
                  "Plates (he) +": ["d"]}
        self.assertEqual(gen.group_headings(tables, "Plates", "she"), ["Plates (she)"])
        self.assertEqual(gen.group_headings(tables, "Plates", "he"),
                         ["Plates", "Plates (he) +"])
        self.assertEqual(gen.group_headings(tables, "Plates", "they"), ["Plates"])
        # The same answer variant_table() gives for a rolled table of the same
        # shape, which is the whole point of mirroring it.
        self.assertEqual(gen.variant_table(tables, "Plates", "she"), ["b"])

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

    def test_one_reference_per_group_per_family(self):
        """A target referenced once from the base table and again from its
        '(she) +' variant is not two references in two tables - it is the
        same group claimed twice by one family, which references_in()'s
        first-occurrence-wins would resolve silently and trait_odds() would
        then credit to the wrong bullet."""
        tables = fixture_tables()
        tables["Plates"] = ["a plate"]
        tables["Outfit"].append("=> Plates")
        tables["Outfit (she) +"] = ["=> Plates"]
        self.assertTrue(any("family" in p for p in self.check(tables)))

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

    def test_gear_is_refused_because_the_nogear_re_draw_does_not_resolve(self):
        """A Backdrop flagged 'nogear' re-draws Gear after the main loop, from
        a pool it narrowed by hand. That path knows nothing about groups, so a
        grouped Gear would resolve on most rolls and paste '=> Name' into the
        prompt on the rest."""
        tables = fixture_tables()
        tables["Plates"] = ["a plate"]
        tables["Gear"].append("=> Plates")
        [problem] = self.check(tables)
        self.assertIn("nogear", problem)
        self.assertIn("Gear", problem)

    def test_a_rerollable_trait_is_refused_because_the_legacy_re_roll_does_not_resolve(self):
        """reroll_trait() rebuilds the draw by hand for an entry written before
        _raw existed, for any of REROLLABLE_TRAITS. Same shape of bug, same
        refusal - and the message names that path rather than the nogear one,
        because they are fixed in different places."""
        for name in gen.REROLLABLE_TRAITS:
            if name not in gen.REQUIRED_TABLES:
                continue
            tables = fixture_tables()
            tables["Plates"] = ["a plate"]
            tables[name].append("=> Plates")
            with self.subTest(table=name):
                [problem] = self.check(tables)
                self.assertIn("legacy re-roll", problem)
                self.assertIn(name, problem)

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
    for key in ["Plates", "Plates (she) +", "Neon (beta)", "Civvies",
                "Civvies (he)", "Crop tops"]:
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

    def test_a_replacement_group_variant_stands_in_for_the_base_members(self):
        """'## Civvies (he)' replaces '## Civvies' for a man, the way
        'Build (she)' replaces 'Build'. The base members are not merely
        outweighed for him - they are not in his pool at all."""
        he = next(b for b in GROUPS["Pronouns"] if b.startswith("he"))
        she = next(b for b in GROUPS["Pronouns"] if b.startswith("she"))
        base = {"a cardigan || civ", "a sundress || civ"}
        probe = {}
        gen.roll_npc(GROUPS, random.Random(0), {"Pronouns": he}, probe=probe)
        self.assertEqual(set(probe["Civvies"]), {"a knit jumper || civ"})
        raws_he = {roll(s, Pronouns=he)["_raw"]["Outfit"] for s in range(600)}
        raws_she = {roll(s, Pronouns=she)["_raw"]["Outfit"] for s in range(600)}
        self.assertIn("a knit jumper || civ", raws_he)
        self.assertFalse(base & raws_he, raws_he & base)
        # And she still draws the base members, since she has no variant of it.
        self.assertTrue(base <= raws_she, base - raws_she)
        self.assertNotIn("a knit jumper || civ", raws_she)

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

    def test_a_group_cannot_re_admit_itself_through_a_fallback_the_parent_never_took(self):
        """A themed reference the theme gate drops, next to a civ bullet the
        mil gate drops. The union stays alive through the reference's own
        (untagged) members - but the parent pool is narrowed on its own, so it
        meets filter_by_mil's "never empty the pool" guard and comes back as
        the jacket alone, exactly as this two-bullet table would with a plain
        bullet in the reference's place. The members surviving in the union
        beside it cannot carry the reference back into a parent pool the theme
        gate has already dropped it from.

        This is the shape that made the third fallback level (`or options`, the
        raw un-narrowed pool) reachable while `parent` was carved out of the
        union's survivors; narrowing the parent alone retires it."""
        tables = {**GROUPS, "Outfit": ["=> Neon (beta) || @beta", "a jacket || civ"]}
        del tables["Outfit (she) +"]
        alpha = next(b for b in GROUPS["Theme"] if gen.split_flags(b)[0] == "alpha")
        mil = next(b for b in GROUPS["Role"] if "mil" in gen.split_flags(b)[1])
        for seed in range(50):
            probe = {}
            npc = gen.roll_npc(tables, random.Random(seed),
                               {"Theme": alpha, "Role": mil}, probe=probe)
            self.assertEqual(probe["Outfit"], ["a jacket || civ"], seed)
            self.assertEqual(npc["_raw"]["Outfit"], "a jacket || civ", seed)

    def test_an_emptied_reference_falls_back_to_the_narrowed_parent_not_the_raw_pool(self):
        """A reference bullet that itself carries no flags survives the mil
        gate even though both of its members do not, so the narrowed parent
        pool - not the raw one - holds just that reference; a sibling bullet
        the SAME gate actually dropped from the union (the civ jacket) must
        not be re-admitted by a fallback that reached further than it should."""
        tables = {**GROUPS, "Outfit": ["=> Civvies", "a jacket || civ"]}
        del tables["Outfit (she) +"]
        mil = next(b for b in GROUPS["Role"] if "mil" in gen.split_flags(b)[1])
        legal = {"a cardigan || civ", "a sundress || civ", "a knit jumper || civ"}
        for seed in range(50):
            npc = gen.roll_npc(tables, random.Random(seed), {"Role": mil})
            raw = npc["_raw"]["Outfit"]
            self.assertIsNone(gen.reference_target(raw), seed)
            self.assertNotEqual(raw, "a jacket || civ", seed)
            self.assertIn(raw, legal, seed)


def tagged_share(pool, theme, name="Outfit"):
    """What fraction of a drawn-from pool carries `theme`'s own tag."""
    hits = sum(1 for b in pool if theme in gen.themes_of(gen.flags_for(name, b)))
    return hits / len(pool)


class TestTheThemeShareIsSizedAgainstTheParent(unittest.TestCase):
    """apply_theme_share duplicates a tagged bullet until it holds THEME_SHARE
    of the pool it is handed. A group's members are narrowed together with the
    parent as one union, so if the share ran on that union the multiplier would
    be computed against the members too and then every copy would be left
    behind in the parent pool when the members are split back out - a parent
    that reads 0.60 tagged without groups reading 0.80+ with them, for no
    reason an author of the tables file could see.
    """

    def parent_only(self, bullets, theme):
        """The pre-feature theme chain over the parent list alone."""
        return gen.apply_theme_share(
            gen.filter_by_theme(bullets, theme, "Outfit"), theme, "Outfit")

    def test_a_groups_size_never_inflates_the_parents_theme_share(self):
        """The ceiling. One tagged reference and two neutral parent slots, with
        four members hanging off the two references: the recorded parent pool
        has to carry exactly the share the same three bullets carry on their
        own, whatever the groups behind them weigh."""
        they = next(b for b in GROUPS["Pronouns"] if b.startswith("they"))
        beta = next(b for b in GROUPS["Theme"] if gen.split_flags(b)[0] == "beta")
        plain = next(b for b in GROUPS["Role"] if "mil" not in gen.split_flags(b)[1])
        parent = ["grey coveralls", "=> Neon (beta) || @beta", "=> Civvies"]
        tables = {**GROUPS, "Outfit": parent}
        probe = {}
        gen.roll_npc(tables, random.Random(0),
                     {"Pronouns": they, "Theme": beta, "Role": plain}, probe=probe)
        self.assertAlmostEqual(tagged_share(probe["Outfit"], beta),
                               tagged_share(self.parent_only(parent, beta), beta),
                               places=9, msg=probe["Outfit"])
        # And the pre-feature number itself, spelled out, so a regression that
        # moved both sides together would still be caught: one tagged slot
        # against two neutral ones needs three copies to clear 0.60.
        self.assertAlmostEqual(tagged_share(probe["Outfit"], beta), 0.6, places=9)

    def test_a_tagged_member_of_a_neutral_group_is_weighted_inside_the_group(self):
        """A neutral reference whose members carry tags: spec section 3 says the
        tag is 'filtered and weighted inside the group only', so the member's
        share is sized against its own group and does not move when the parent
        or a sibling group grows."""
        they = next(b for b in GROUPS["Pronouns"] if b.startswith("they"))
        beta = next(b for b in GROUPS["Theme"] if gen.split_flags(b)[0] == "beta")
        plain = next(b for b in GROUPS["Role"] if "mil" not in gen.split_flags(b)[1])
        civvies = ["a cardigan || civ", "a sundress || civ",
                   "a neon cardigan || civ @beta"]

        def group_pool(parent):
            tables = {**GROUPS, "Outfit": parent, "Civvies": civvies}
            probe = {}
            gen.roll_npc(tables, random.Random(0),
                         {"Pronouns": they, "Theme": beta, "Role": plain}, probe=probe)
            return probe["Civvies"]

        small = group_pool(["grey coveralls", "=> Civvies"])
        self.assertGreaterEqual(tagged_share(small, beta), gen.THEME_SHARE)
        self.assertAlmostEqual(
            tagged_share(small, beta),
            tagged_share(self.parent_only(civvies, beta), beta), places=9)
        # The same group beside a fatter parent and a second group: its own
        # pool is unchanged, because nothing outside it was ever counted.
        big = group_pool(["grey coveralls", "a jacket", "a parka", "a poncho",
                          "=> Civvies", "=> Plates"])
        self.assertEqual(small, big)


class TestAttribution(unittest.TestCase):
    def test_heading_for_answers_the_group_for_a_member(self):
        self.assertEqual(gen.heading_for(GROUPS, "Outfit", "he", "scuffed plate || mil"), "Plates")
        self.assertEqual(gen.heading_for(GROUPS, "Outfit", "she", "a fitted plate"), "Plates (she) +")
        self.assertEqual(gen.heading_for(GROUPS, "Outfit", "she", "a crop top || civ"), "Crop tops")
        self.assertEqual(gen.heading_for(GROUPS, "Outfit", "he", "grey coveralls"), "Outfit")
        self.assertEqual(gen.heading_for(GROUPS, "Outfit", "he", "=> Plates"), "Outfit")
        # A replacement group variant, attributed the way variant_table()
        # would roll it: his jumper is 'Civvies (he)', and the base members
        # are not his to be attributed at all.
        self.assertEqual(gen.heading_for(GROUPS, "Outfit", "he", "a knit jumper || civ"),
                         "Civvies (he)")
        self.assertEqual(gen.heading_for(GROUPS, "Outfit", "she", "a cardigan || civ"),
                         "Civvies")

    def test_trait_odds_reports_groups_and_charges_the_reference_row(self):
        odds = gen.trait_odds(GROUPS, 3000, random.Random(5))
        for key in ["Plates", "Plates (she) +", "Neon (beta)", "Civvies",
                "Civvies (he)", "Crop tops"]:
            self.assertIn(key, odds, key)
            self.assertEqual(set(odds[key]), set(GROUPS[key]), key)
        # The parent's rows still sum to one, reference rows included...
        outfit_total = sum(odds["Outfit"].values()) + sum(odds["Outfit (she) +"].values())
        self.assertAlmostEqual(outfit_total, 1.0, places=6)
        # ...and a group's rows sum to its reference row.
        plates = sum(odds["Plates"].values()) + sum(odds["Plates (she) +"].values())
        self.assertAlmostEqual(plates, odds["Outfit"]["=> Plates"], places=6)
        self.assertGreater(odds["Outfit"]["=> Plates"], 0.05)
        # Civvies is the replacement-variant case: a man's rows live under
        # 'Civvies (he)' INSTEAD of the base two, so the reference row is the
        # sum across both headings and neither alone.
        self.assertAlmostEqual(odds["Civvies"]["a cardigan || civ"]
                               + odds["Civvies"]["a sundress || civ"]
                               + odds["Civvies (he)"]["a knit jumper || civ"],
                               odds["Outfit"]["=> Civvies"], places=6)
        self.assertGreater(odds["Civvies (he)"]["a knit jumper || civ"], 0)
        # ...even when the reference itself lives in a '+' variant rather
        # than the base table.
        self.assertGreater(odds["Outfit (she) +"]["=> Crop tops"], 0)
        self.assertAlmostEqual(sum(odds["Crop tops"].values()),
                                odds["Outfit (she) +"]["=> Crop tops"], places=6)


class TestChoices(unittest.TestCase):
    def test_members_are_offered_under_their_group_and_the_reference_is_not(self):
        npc = roll(11)
        choices = gen.trait_choices(GROUPS, npc, "Outfit")
        values = [c["value"] for c in choices]
        self.assertNotIn("=> Plates", values)
        self.assertIn("scuffed plate || mil", values)
        plate = next(c for c in choices if c["value"] == "scuffed plate || mil")
        self.assertEqual(plate["heading"], "Plates")
        coveralls = next(c for c in choices if c["value"] == "grey coveralls")
        self.assertEqual(coveralls["heading"], "Outfit")

    def test_allowed_follows_both_the_reference_and_the_member(self):
        mil = next(b for b in GROUPS["Role"] if "mil" in gen.split_flags(b)[1])
        # Pronouns pinned: Civvies has a '(he)' replacement variant, so a man
        # is not offered the two base bullets this asserts on at all.
        they = next(b for b in GROUPS["Pronouns"] if b.startswith("they"))
        npc = roll(11, Role=mil, Pronouns=they)
        choices = {c["value"]: c for c in gen.trait_choices(GROUPS, npc, "Outfit")}
        self.assertFalse(choices["a cardigan || civ"]["allowed"], "Civvies left the pool for a mil Role")
        self.assertTrue(choices["scuffed plate || mil"]["allowed"])

    def test_a_replacement_group_variant_is_the_only_one_offered(self):
        """The picker offers what the roller could produce, so a man is offered
        his own Civvies and not the two the variant replaced."""
        he = next(b for b in GROUPS["Pronouns"] if b.startswith("he"))
        npc = roll(11, Pronouns=he)
        choices = {c["value"]: c for c in gen.trait_choices(GROUPS, npc, "Outfit")}
        self.assertIn("a knit jumper || civ", choices)
        self.assertEqual(choices["a knit jumper || civ"]["heading"], "Civvies (he)")
        self.assertNotIn("a cardigan || civ", choices)
        self.assertNotIn("a sundress || civ", choices)

    def test_the_current_member_is_marked_current(self):
        npc = roll(11, Outfit="lacquered plate")
        choices = {c["value"]: c for c in gen.trait_choices(GROUPS, npc, "Outfit")}
        self.assertTrue(choices["lacquered plate"]["current"])


class TestShipsHaveNoGroups(unittest.TestCase):
    def test_the_ship_check_refuses_a_reference(self):
        from test.helpers import load_ship_generator
        ship = load_ship_generator()
        tables = ship.parse_tables(REPO / "test" / "fixtures" / "ship-tables-minimal.md")
        tables["Hull"] = list(tables["Hull"]) + ["=> Hulls"]
        tables["Hulls"] = ["a hull"]
        with self.assertRaises(SystemExit) as cm:
            ship.check_tables(tables, Path("ship.md"))
        self.assertIn("not supported for ships", str(cm.exception))


class TestHelpersFollowReferences(unittest.TestCase):
    def test_table_keys_reaches_a_familys_groups(self):
        from test.helpers import table_keys, bullets_for
        self.assertEqual(table_keys(GROUPS, "Outfit"),
                         ["Outfit", "Outfit (she) +", "Plates", "Plates (she) +",
                          "Neon (beta)", "Civvies", "Civvies (he)", "Crop tops"])
        self.assertIn("a fitted plate", bullets_for(GROUPS, "Outfit"))
        self.assertEqual(table_keys(GROUPS, "Headgear"), ["Headgear"])
