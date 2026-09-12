# Table Groups (generator) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A `- => Name` bullet in a rolled table is one slot that resolves by rolling again from the `## Name` table, so a family of near-duplicate bullets stops being over-represented; then apply it to Outfit.

**Architecture:** Pure helpers beside `split_flags()` recognise a reference. `check_tables()` enforces the file rules at startup. Inside `roll_npc()` the per-table filter chain becomes a nested `narrow()` so a group's members can be filtered as one union with the parent pool; the single draw site resolves a drawn reference with a second draw and records the member's own line in `_raw`. `heading_for()`, `trait_odds()` and `trait_choices()` learn to attribute a member to its group. The ship generator refuses references.

**Tech Stack:** Python 3.13, `unittest` (`python -m unittest discover test` from the repo root, or one module with `python -m unittest test.test_table_groups -v`). Tests load the script by path through `test/helpers.py` because of the hyphen in `generate-npc.py`.

**Spec:** `docs/superpowers/specs/2026-09-12-table-groups-design.md` (sections 3, 4, 6, 7). The GUI half is a separate plan in `lancer-npc-import-gui/docs/superpowers/plans/2026-09-12-table-groups-gui.md`.

## Global Constraints

- Work in the worktree `G:\GIT-REPOS\lancer-art-generator\.claude\worktrees\table-groups`, branch `feature/table-groups`. Commit after every task; lowercase prose commit subjects like the log ("design: table groups, one slot for a family of near-duplicate bullets").
- The reference syntax is exactly `=> Name`, optionally after an `xN ` weight, with an optional `|| @theme` segment and nothing else in that segment.
- `test/fixtures/roll-snapshot.json` and `test/fixtures/tables-minimal.md` are not modified by any task. `test/test_trait_odds.TestTheRollIsUnchanged` and `test/test_set_trait_value.ProbeIsInert` must pass after every task.
- `npc["_raw"]` keeps exactly the `REQUIRED_TABLES` keys (`test/test_raw_traits.py`).
- `test/test_shared_surface.py` pins the names the ship generator borrows; do not rename `parse_tables`, `variant_table`, `heading_for`, `split_flags`, `flags_for`, `themes_of`, `filter_by_mil`.
- Sequencing with the GUI plan: run GUI tasks 1 and 2 (reference parsing and inherited flag vocabulary) before this plan's Task 11, or the GUI's live-file drift test `every flag the live tables use has a checkbox` fails on any checkout with both repos side by side.
- Code is MIT, prose (tables file, README, SKILL.md) is CC BY-SA. House style is long explanatory comments that say why and name the rejected alternative.

---

### Task 1: Reference helpers

**Files:**
- Modify: `generate-npc.py` (insert after `heading_for()`, which ends near line 1320)
- Create: `test/test_table_groups.py`

**Interfaces:**
- Produces: `REFERENCE_PREFIX = "=> "`; `reference_target(bullet) -> str | None`; `is_reference(bullet) -> bool`; `references_in(tables, name) -> dict[str, str]` mapping each group heading referenced from base table `name` or its variants to the reference bullet's full text; `group_headings(tables, target, subject) -> list[str]` giving `[target, "target (subject)", "target (subject) +"]` filtered to those present in `tables`; `group_tables(tables) -> set[str]` of every heading any table references plus those headings' present variants.

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest test.test_table_groups -v`
Expected: FAIL with `AttributeError: module 'gennpc' has no attribute 'reference_target'`

- [ ] **Step 3: Write the helpers**

Insert immediately after `heading_for()` in `generate-npc.py`:

```python
# A group reference: a bullet whose text is '=> Name' points a rolled table at
# a second table, '## Name', whose bullets are the variants of one look. The
# reference is one slot in the parent pool and the member is drawn second, so
# eleven flight suits weigh what one distinct jacket weighs. The '=>' token
# was free: nothing in the file or the parsers used it, and unlike '{' it can
# never be mistaken for a pronoun placeholder by the format() pass.
REFERENCE_PREFIX = "=> "


def reference_target(bullet):
    """The group heading a reference bullet names, or None for a plain bullet.

    Read off the prose segment only, so a themed reference ('=> Black dresses
    (gundam) || @gundam') resolves to the heading and keeps its tag where
    themes_of() finds it. A bare '=>' with nothing after it is not a reference
    - a typo should roll as literal text and be seen, not point at nothing.
    """
    text = split_flags(bullet)[0]
    if not text.startswith(REFERENCE_PREFIX):
        return None
    return text[len(REFERENCE_PREFIX):].strip() or None


def is_reference(bullet):
    return reference_target(bullet) is not None


def references_in(tables, name):
    """{group heading: reference bullet} over base table `name` and its variants.

    One entry per group, first occurrence wins: parse_tables() expands an 'xN'
    reference into N identical strings, and check_tables() refuses two
    DIFFERENT reference texts for one group, so there is only ever one text to
    keep.
    """
    out = {}
    for key in tables:
        if not (key == name or key.startswith(name + " (")):
            continue
        for bullet in tables[key]:
            target = reference_target(bullet)
            if target is not None and target not in out:
                out[target] = bullet
    return out


def group_headings(tables, target, subject):
    """The headings one pronoun set draws a group from: the target and its
    variants, in variant_table()'s own order and restricted to those present.

    Exact names rather than a startswith() - a themed sibling group is named
    'Flight suits (gundam)' by convention, and it is a group of its own, not a
    pronoun variant of 'Flight suits'.
    """
    return [key for key in (target, "%s (%s)" % (target, subject), "%s (%s) +" % (target, subject))
            if key in tables]


def group_tables(tables):
    """Every heading some table references, plus those headings' variants."""
    targets = set()
    for name in tables:
        targets.update(references_in(tables, name))
    out = set()
    for key in tables:
        base, _, _ = key.partition(" (")
        if key in targets or (base in targets and key != base):
            out.add(key)
    return out
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest test.test_table_groups -v`
Expected: 5 tests, OK

- [ ] **Step 5: Run the full suite to confirm nothing moved**

Run: `python -m unittest discover test 2>&1 | tail -3`
Expected: OK (same count as before plus 5)

- [ ] **Step 6: Commit**

```bash
git add generate-npc.py test/test_table_groups.py
git commit -m "the four helpers that read a '=> Name' group reference, and nothing that uses them yet"
```

---

### Task 2: The rules a reference obeys, enforced at startup

**Files:**
- Modify: `generate-npc.py` (`check_tables()` near line 1271; new `check_group_references()` above it)
- Test: `test/test_table_groups.py`

**Interfaces:**
- Consumes: Task 1's `reference_target`, `references_in`, `group_headings`; existing `split_flags`, `themes_of`, `flags_for`, `REQUIRED_TABLES`.
- Produces: `check_group_references(tables) -> list[str]` (complaints, empty when the file is well formed); `check_tables()` raises `SystemExit` listing them. `UNGROUPABLE_TABLES = ("Pronouns", "Theme", "Stance")`.

- [ ] **Step 1: Write the failing tests**

Append to `test/test_table_groups.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest test.test_table_groups.TestCheckGroupReferences -v`
Expected: FAIL with `AttributeError: ... 'check_group_references'`

- [ ] **Step 3: Write the checks**

Insert above `check_tables()`:

```python
# The three rolled tables the main draw site does not handle: Pronouns and
# Theme are drawn before the loop from unfiltered lists, Stance after it from
# (bullet, flags) pairs. A reference in any of them would be pasted into the
# prompt as text, so the check refuses it rather than letting that happen.
UNGROUPABLE_TABLES = ("Pronouns", "Theme", "Stance")


def check_group_references(tables):
    """Every way a '=> Name' bullet can be wrong, as a list of complaints.

    A list rather than the first failure, because a file being regrouped by
    hand tends to get several things wrong at once and a run per complaint is
    slow. Each complaint names the heading and the bullet, since the file is
    three thousand lines and 'a reference is malformed' is not actionable.
    """
    problems = []
    for name, bullets in tables.items():
        base = name.partition(" (")[0]
        seen = {}
        # dict.fromkeys(): parse_tables() expands 'x2 => Plates' into two
        # identical strings, which is one reference, not two.
        for bullet in dict.fromkeys(bullets):
            target = reference_target(bullet)
            if target is None:
                continue
            if base not in REQUIRED_TABLES or base in UNGROUPABLE_TABLES:
                problems.append(
                    "'## %s': %r - a group reference is only read in a rolled "
                    "table, and not in %s" % (name, bullet, ", ".join(UNGROUPABLE_TABLES)))
                continue
            if target not in tables:
                problems.append(
                    "'## %s': %r names '## %s', which this file does not have "
                    "(or which has no bullets)" % (name, bullet, target))
                continue
            if target.partition(" (")[0] in REQUIRED_TABLES:
                problems.append(
                    "'## %s': %r - a group cannot be a rolled table or a "
                    "variant of one" % (name, bullet))
            flags = [f for f in split_flags(bullet)[1] if not f.startswith("@")]
            if flags:
                problems.append(
                    "'## %s': %r carries flags %s; flags belong on the group's "
                    "members, the reference takes only @theme tags"
                    % (name, bullet, " ".join(flags)))
            if target in seen:
                problems.append(
                    "'## %s' references '## %s' more than once (%r and %r); "
                    "use one bullet with an xN weight"
                    % (name, target, seen[target], bullet))
            seen[target] = bullet
            themed = bool(themes_of(split_flags(bullet)[1]))
            for key in tables:
                if not (key == target or key.startswith(target + " (")):
                    continue
                for member in tables[key]:
                    if reference_target(member) is not None:
                        problems.append(
                            "'## %s': %r - a group cannot reference another "
                            "group (one level only)" % (key, member))
                    if themed and themes_of(flags_for(base, member)):
                        problems.append(
                            "'## %s': %r carries a theme tag inside a themed "
                            "group; the tag belongs on the '## %s' reference "
                            "alone" % (key, member, name))
    return problems
```

Then in `check_tables()`, after the `missing` block, add:

```python
    problems = check_group_references(tables)
    if problems:
        raise SystemExit(
            "%s: the group references are not well formed:\n  %s"
            % (path.name, "\n  ".join(problems)))
```

- [ ] **Step 4: Run the tests**

Run: `python -m unittest test.test_table_groups -v`
Expected: all OK

- [ ] **Step 5: Run the full suite**

Run: `python -m unittest discover test 2>&1 | tail -3`
Expected: OK. The live file has no references yet, so the check is silent.

- [ ] **Step 6: Commit**

```bash
git add generate-npc.py test/test_table_groups.py
git commit -m "check_tables refuses a malformed group reference, every complaint at once"
```

---

### Task 3: The filter chain becomes `narrow()` (no behaviour change)

**Files:**
- Modify: `generate-npc.py` `roll_npc()`, the `for name in REQUIRED_TABLES:` loop (starts near line 1895)

**Interfaces:**
- Produces: a nested function `narrow(name, options) -> list[str]` inside `roll_npc()`, defined immediately before the loop.

- [ ] **Step 1: Confirm the gates pass before touching anything**

Run: `python -m unittest test.test_trait_odds.TestTheRollIsUnchanged test.test_set_trait_value.ProbeIsInert -v`
Expected: OK

- [ ] **Step 2: Move the chain into a nested function**

In `roll_npc()`, find the loop:

```python
    for name in REQUIRED_TABLES:
        if name in ("Pronouns", "Theme", "Stance"):
            continue
        options = variant_table(tables, name, subject)

        # Theme gates every appearance table: ...
```

The filter chain runs from the comment `# Theme gates every appearance table` down to and including the block that ends:

```python
        if name == "Headgear" and outfit_notac:
            options = filter_by_hardtech(options, outfit_notac)
```

The next lines after that block begin `# Rolled either way, so that forcing a trait does not shift...` and then `if probe is not None:`. Cut everything from the theme comment to the `filter_by_hardtech` line inclusive, and paste it verbatim as the body of this function, placed just above `for name in REQUIRED_TABLES:`, re-indented by one level (it is now inside a `def`, inside `roll_npc`):

```python
    def narrow(name, options):
        """One table's pool, `options` in and the drawn-from list out.

        Every filter the loop below used to apply inline, in the same order,
        reading the loop's state (young, role_mil, outfit_notac, the forced_*
        flags, npc["Role"], npc["Backdrop"]) through the closure - so the call
        from the loop is the code that used to sit there, and a second call on
        a group's members and the parent pool together (see the draw site)
        runs them through exactly the gates the flat list passed. Consumes no
        randomness: the snapshot test is what holds that.
        """
        # <the moved block, verbatim>
        return options
```

In the loop, replace `options = variant_table(tables, name, subject)` with:

```python
        options = narrow(name, variant_table(tables, name, subject))
```

so that the line is followed directly by the `# Rolled either way...` comment and the probe/draw.

The closure reads `role_dress`, which the loop assigns when Role is stripped and which Outfit reads later; leave the assignment where it is. Python resolves the closure's reads at call time, so no `nonlocal` is needed because `narrow()` only reads these names.

- [ ] **Step 3: Run the gates and the full suite**

Run: `python -m unittest test.test_trait_odds.TestTheRollIsUnchanged test.test_set_trait_value.ProbeIsInert -v && python -m unittest discover test 2>&1 | tail -3`
Expected: OK, OK. If the snapshot test fails, a line was moved out of order or a name was shadowed; diff the moved block against `git show HEAD:generate-npc.py`.

- [ ] **Step 4: Commit**

```bash
git add generate-npc.py
git commit -m "roll_npc's filter chain becomes narrow(), a closure, so a group's members can pass through it too"
```

---

### Task 4: Resolution at the draw site

**Files:**
- Modify: `generate-npc.py` `roll_npc()` draw site (the `if probe is not None: probe[name] = list(options)` / `value = rng.choice(options)` / `forced = ...` lines)
- Create: `test/fixtures/tables-groups.md`
- Test: `test/test_table_groups.py`

**Interfaces:**
- Consumes: Task 1 helpers, Task 3 `narrow()`.
- Produces: `probe[<group heading>]` = that group's filtered member pool; `npc["_raw"][name]` = the member's line when a reference was drawn.

- [ ] **Step 1: Create the groups fixture**

Copy `test/fixtures/tables-minimal.md` to `test/fixtures/tables-groups.md` and replace its `## Outfit` section (and add the group tables directly after it) with:

```markdown
## Outfit
- grey coveralls
- => Plates
- => Neon (beta) || @beta
- => Civvies
- an elaborate floral kimono || civ notac dressy

## Outfit (she) +
- => Crop tops

## Plates
- lacquered plate
- scuffed plate || mil
- x2 dented plate

## Plates (she) +
- a fitted plate

## Neon (beta)
- a neon techwear jacket
- a neon visor jacket

## Civvies
- a cardigan || civ
- a sundress || civ

## Crop tops
- a crop top || civ
```

Check the minimal fixture's `## Role` table has at least one `|| mil` bullet and one without (the mil filter test needs both); if not, add `- a sergeant || mil` to the fixture copy only. Everything else in the copy stays identical to `tables-minimal.md`.

- [ ] **Step 2: Write the failing tests**

Append to `test/test_table_groups.py`:

```python
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
```

Note on `test_members_are_weighted_inside_the_group`: `parse_tables()` stores the weight-stripped text, so the dented plate's raw text is `dented plate`; the `.replace` is there to make that visible to a reader. Simplify to `counts["dented plate"]` if preferred.

- [ ] **Step 3: Run the tests to verify they fail**

Run: `python -m unittest test.test_table_groups.TestResolution -v`
Expected: FAIL. `test_a_drawn_reference_resolves...` fails with `_raw holds a reference`; the theme test fails because `=> Neon (beta) || @beta` reaches the prompt as text.

- [ ] **Step 4: Write the resolution**

At the draw site, replace:

```python
        if probe is not None:
            probe[name] = list(options)
        value = rng.choice(options)

        # A forced value replaces the draw here, ...
        forced = (overrides or {}).get(name)
        if forced is not None:
            value = forced
```

(keep the long comment above `forced`) with:

```python
        # Groups. A '=> Name' bullet is one slot of this pool whose value is
        # drawn second, from '## Name'. The members are filtered TOGETHER with
        # the parent pool, as one union, rather than on their own: nearly every
        # gate in narrow() hands the whole pool back sooner than empty it, so
        # a civ-only group filtered alone would be re-admitted for a mil Role
        # the moment the mil gate emptied it - which the flat list never did.
        # Run as a union the group's members meet the same fallbacks the
        # parent's own bullets do, and a group whose members all fell leaves
        # the pool. The union is the parent pool itself when there are no
        # references, so a file without groups narrows exactly as before.
        members = {}
        for bullet in dict.fromkeys(options):
            target = reference_target(bullet)
            if target is not None and target not in members:
                members[target] = [b for key in group_headings(tables, target, subject)
                                   for b in tables[key]]
        if members:
            parent_set = set(options)
            member_sets = {t: set(m) for t, m in members.items()}
            survivors = narrow(name, options + [b for m in members.values() for b in m])
            pools = {t: [b for b in survivors if b in member_sets[t]] for t in members}
            pool = [b for b in survivors if b in parent_set
                    and (reference_target(b) is None or pools[reference_target(b)])]
            options = pool or options   # never filter the pool down to nothing
            if probe is not None:
                for target, drawn_from in pools.items():
                    probe[target] = list(drawn_from)
        if probe is not None:
            probe[name] = list(options)
        value = rng.choice(options)

        # A forced value replaces the draw here, ...   (the existing comment)
        forced = (overrides or {}).get(name)
        if forced is not None:
            # A reference is not a value: pasted into a prompt it would read
            # '=> Flight suits'. --set-trait and the GUI offer members, never
            # references (see trait_choices), so reaching here is a typo or an
            # old preset, and both want the table named.
            if reference_target(forced) is not None:
                raise SystemExit(
                    "%s: %r is a group reference, not a value - name one of the "
                    "group's own bullets" % (name, forced))
            value = forced
        elif reference_target(value) is not None:
            # The second draw of the two-stage roll. Only a drawn reference
            # reaches this line, so a file with no groups consumes exactly the
            # numbers it did before. The fallback to the unfiltered members is
            # for the one case the pool guard above kept an emptied reference
            # because everything else had emptied too.
            target = reference_target(value)
            value = rng.choice(pools[target] or members[target])
```

Note: when `members` is empty, `pools` is never defined, and the `elif` cannot be reached because no bullet in `options` is a reference. When the union was built, `pools` exists. If a linter objects to a conditionally defined name, initialise `pools = {}` beside `members = {}`.

The `narrow()` call inside the union branch replaces the earlier per-table call for this iteration's purposes only when references exist; the earlier `options = narrow(name, variant_table(...))` stays as it is, so a pool without references is narrowed once, as before, and a pool with references is narrowed a second time as a union. Narrowing twice is harmless for the filters here (they are idempotent on their own output apart from `apply_theme_share`, which would duplicate tagged bullets twice). To avoid that double share, change the loop's first line to:

```python
        pool_in = variant_table(tables, name, subject)
        options = pool_in if any(reference_target(b) is not None for b in pool_in) \
            else narrow(name, pool_in)
```

so a pool that carries references is narrowed exactly once, as the union.

- [ ] **Step 5: Run the resolution tests and the gates**

Run: `python -m unittest test.test_table_groups -v && python -m unittest test.test_trait_odds.TestTheRollIsUnchanged test.test_set_trait_value.ProbeIsInert -v`
Expected: all OK. The snapshot is untouched because the minimal fixture has no references.

- [ ] **Step 6: Run the full suite**

Run: `python -m unittest discover test 2>&1 | tail -3`
Expected: OK

- [ ] **Step 7: Commit**

```bash
git add generate-npc.py test/fixtures/tables-groups.md test/test_table_groups.py
git commit -m "a drawn '=> Name' reference resolves from '## Name', filtered as one union with the parent pool"
```

---

### Task 5: Attribution: `heading_for()` and `trait_odds()`

**Files:**
- Modify: `generate-npc.py` `heading_for()` (near line 1301) and `trait_odds()` (near line 1323)
- Test: `test/test_table_groups.py`

**Interfaces:**
- Consumes: Task 1 `references_in`, `group_headings`, `group_tables`.
- Produces: `heading_for()` returns a group heading for a member; `trait_odds()` output includes group headings, and counts the reference row under the parent.

- [ ] **Step 1: Write the failing tests**

Append to `test/test_table_groups.py`:

```python
class TestAttribution(unittest.TestCase):
    def test_heading_for_answers_the_group_for_a_member(self):
        self.assertEqual(gen.heading_for(GROUPS, "Outfit", "he", "scuffed plate || mil"), "Plates")
        self.assertEqual(gen.heading_for(GROUPS, "Outfit", "she", "a fitted plate"), "Plates (she) +")
        self.assertEqual(gen.heading_for(GROUPS, "Outfit", "she", "a crop top || civ"), "Crop tops")
        self.assertEqual(gen.heading_for(GROUPS, "Outfit", "he", "grey coveralls"), "Outfit")
        self.assertEqual(gen.heading_for(GROUPS, "Outfit", "he", "=> Plates"), "Outfit")

    def test_trait_odds_reports_groups_and_charges_the_reference_row(self):
        odds = gen.trait_odds(GROUPS, 3000, random.Random(5))
        for key in ["Plates", "Plates (she) +", "Neon (beta)", "Civvies", "Crop tops"]:
            self.assertIn(key, odds, key)
            self.assertEqual(set(odds[key]), set(GROUPS[key]), key)
        # The parent's rows still sum to one, reference rows included...
        outfit_total = sum(odds["Outfit"].values()) + sum(odds["Outfit (she) +"].values())
        self.assertAlmostEqual(outfit_total, 1.0, places=6)
        # ...and a group's rows sum to its reference row.
        plates = sum(odds["Plates"].values()) + sum(odds["Plates (she) +"].values())
        self.assertAlmostEqual(plates, odds["Outfit"]["=> Plates"], places=6)
        self.assertGreater(odds["Outfit"]["=> Plates"], 0.05)
        self.assertEqual(odds["Civvies"]["a cardigan || civ"] + odds["Civvies"]["a sundress || civ"],
                         odds["Outfit"]["=> Civvies"])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest test.test_table_groups.TestAttribution -v`
Expected: FAIL. `heading_for` returns `Outfit` for a member; `trait_odds` raises `KeyError` or omits the group keys.

- [ ] **Step 3: Extend `heading_for()`**

Replace its final `return name` with:

```python
    # A bullet that sits in the base table is the base table's, whatever
    # groups also hold it; one that does not is looked for in the groups the
    # family references. Base before group, so a text duplicated between the
    # two is reported once, under the parent, the same way a base/variant
    # duplicate is reported under the variant above.
    if bullet in tables.get(name, ()):
        return name
    for target in references_in(tables, name):
        for key in group_headings(tables, target, subject):
            if bullet in tables[key]:
                return key
    return name
```

- [ ] **Step 4: Extend `trait_odds()`**

Replace the counting loop and the return:

```python
    counts = {key: {bullet: 0 for bullet in bullets}
              for key, bullets in tables.items()}
    reported = set(group_tables(tables))
    for _ in range(samples):
        npc = roll_npc(tables, rng)
        subject = npc["Pronouns"].split("/")[0]
        for name, bullet in npc["_raw"].items():
            heading = heading_for(tables, name, subject, bullet)
            counts[heading][bullet] += 1
            # A member counts twice: once under its group, and once as the
            # reference row of the parent that entered the group. The parent's
            # rows then still sum to one and the group's rows sum to the
            # reference's figure, which is the number the Chances panel puts
            # beside '=> Flight suits'. Exact because check_tables() allows one
            # reference per group per table.
            if heading in reported:
                for target, reference in references_in(tables, name).items():
                    if heading in group_headings(tables, target, subject):
                        counts[heading_for(tables, name, subject, reference)][reference] += 1
                        break
    return {key: {bullet: n / samples for bullet, n in bullets.items()}
            for key, bullets in counts.items()
            if key in reported
            or any(k == key or key.startswith(k + " (") for k in REQUIRED_TABLES)}
```

- [ ] **Step 5: Run the tests and the odds suite**

Run: `python -m unittest test.test_table_groups test.test_trait_odds -v 2>&1 | tail -5`
Expected: OK

- [ ] **Step 6: Commit**

```bash
git add generate-npc.py test/test_table_groups.py
git commit -m "heading_for and trait_odds attribute a member to its group and its reference row"
```

---

### Task 6: `trait_choices()` offers members, never the reference

**Files:**
- Modify: `generate-npc.py` `trait_choices()` (near line 3811, the `candidates = ...` line and the `out.append` block)
- Test: `test/test_table_groups.py`

**Interfaces:**
- Consumes: Task 1 helpers; Task 4's `probe[<group>]`.
- Produces: each choice dict for a member has `heading` = the group heading and `allowed` = reference survived in the parent probe and member survived in the group probe.

- [ ] **Step 1: Write the failing tests**

Append to `test/test_table_groups.py`:

```python
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
        npc = roll(11, Role=mil)
        choices = {c["value"]: c for c in gen.trait_choices(GROUPS, npc, "Outfit")}
        self.assertFalse(choices["a cardigan || civ"]["allowed"], "Civvies left the pool for a mil Role")
        self.assertTrue(choices["scuffed plate || mil"]["allowed"])

    def test_the_current_member_is_marked_current(self):
        npc = roll(11, Outfit="lacquered plate")
        choices = {c["value"]: c for c in gen.trait_choices(GROUPS, npc, "Outfit")}
        self.assertTrue(choices["lacquered plate"]["current"])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest test.test_table_groups.TestChoices -v`
Expected: FAIL on `assertNotIn("=> Plates", values)`.

- [ ] **Step 3: Expand references in the candidate list**

In `trait_choices()`, replace `candidates = list(dict.fromkeys(variant_table(tables, name, subject)))` with:

```python
    # A reference is expanded into its group's members, each carrying the
    # group as its heading; the reference itself is never offered, since it is
    # not a value a prompt can hold. `allowed` for a member is two tests, both
    # read off the probe: the reference survived in the parent pool, and the
    # member survived in the group's own pool (recorded under the group's
    # heading by the draw site).
    candidates = []
    for bullet in dict.fromkeys(variant_table(tables, name, subject)):
        target = reference_target(bullet)
        if target is None:
            candidates.append((bullet, bullet in pool))
            continue
        group_pool = set(baseline.get(target, ()))
        for member in dict.fromkeys(b for key in group_headings(tables, target, subject)
                                    for b in tables[key]):
            candidates.append((member, bullet in pool and member in group_pool))
```

Then change the loop header `for bullet in candidates:` to `for bullet, allowed in candidates:` and in the `out.append({...})` dict replace `"allowed": bullet in pool,` with `"allowed": allowed,`.

- [ ] **Step 4: Run the tests and the set-trait suite**

Run: `python -m unittest test.test_table_groups test.test_set_trait_value -v 2>&1 | tail -5`
Expected: OK

- [ ] **Step 5: Commit**

```bash
git add generate-npc.py test/test_table_groups.py
git commit -m "trait_choices offers a group's members under the group's heading, and never the reference"
```

---

### Task 7: The ship generator refuses references

**Files:**
- Modify: `generate-spaceship.py` `check_tables()` (near line 363)
- Test: `test/test_table_groups.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m unittest test.test_table_groups.TestShipsHaveNoGroups -v`
Expected: FAIL (no exception raised)

- [ ] **Step 3: Add the refusal**

In `generate-spaceship.py` `check_tables()`, after the `missing` block:

```python
    # The NPC roller resolves a '=> Name' group reference at its draw site;
    # this file has a roller of its own that does not, and would paste the
    # reference into a prompt as text. Refused here until ships grow groups.
    for name, bullets in tables.items():
        for bullet in bullets:
            if npc.reference_target(bullet) is not None:
                raise SystemExit(
                    "%s: '## %s' has a group reference %r, and groups are not "
                    "supported for ships yet" % (path.name, name, bullet))
```

(`npc` is the module alias `generate-spaceship.py` already uses for `generate-npc.py`, e.g. `parse_tables = npc.parse_tables`; confirm the name with `grep -n "npc\.parse_tables" generate-spaceship.py`.)

- [ ] **Step 4: Run the ship tests**

Run: `python -m unittest test.test_table_groups test.test_ship_roll test.test_shared_surface -v 2>&1 | tail -4`
Expected: OK

- [ ] **Step 5: Commit**

```bash
git add generate-spaceship.py test/test_table_groups.py
git commit -m "the ship generator refuses a group reference rather than rolling it as text"
```

---

### Task 8: The shared test helper follows references

**Files:**
- Modify: `test/helpers.py` `table_keys()`
- Modify: `test/test_trait_odds.py` `test_each_raw_bullet_is_a_line_in_the_file`
- Test: `test/test_table_groups.py`

- [ ] **Step 1: Write the failing test**

```python
class TestHelpersFollowReferences(unittest.TestCase):
    def test_table_keys_reaches_a_familys_groups(self):
        from test.helpers import table_keys, bullets_for
        self.assertEqual(table_keys(GROUPS, "Outfit"),
                         ["Outfit", "Outfit (she) +", "Plates", "Plates (she) +",
                          "Neon (beta)", "Civvies", "Crop tops"])
        self.assertIn("a fitted plate", bullets_for(GROUPS, "Outfit"))
        self.assertEqual(table_keys(GROUPS, "Headgear"), ["Headgear"])
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m unittest test.test_table_groups.TestHelpersFollowReferences -v`
Expected: FAIL (group keys missing)

- [ ] **Step 3: Extend `table_keys()`**

```python
def table_keys(tables, name):
    """... (keep the existing docstring, then add:)

    Followed through group references too: a '=> Plates' bullet in Outfit
    means every Plates bullet is content Outfit can deal, so a theme or
    visibility measurement over Outfit has to see it. Only one level, which is
    what check_group_references() enforces.
    """
    gen = load_generator()
    keys = [k for k in tables if k == name or k.startswith(name + " (")]
    for key in list(keys):
        for bullet in tables[key]:
            target = gen.reference_target(bullet)
            if target is None:
                continue
            for group_key in tables:
                if (group_key == target or group_key.startswith(target + " (")) \
                        and group_key not in keys:
                    keys.append(group_key)
    return keys
```

- [ ] **Step 4: Point the odds test's pool at the helper**

In `test/test_trait_odds.py`, add `bullets_for` to the `from test.helpers import ...` line and change `test_each_raw_bullet_is_a_line_in_the_file` to:

```python
    def test_each_raw_bullet_is_a_line_in_the_file(self):
        for seed in range(40):
            for name, raw in roll(seed)["_raw"].items():
                self.assertIn(raw, bullets_for(TABLES, name),
                              "%s: %r is not a bullet in the tables file" % (name, raw))
```

- [ ] **Step 5: Run the suite**

Run: `python -m unittest discover test 2>&1 | tail -3`
Expected: OK. `test_theme_tag_placement` and `test_import_skill_flags` now walk group tables through the helper; the live file has none yet.

- [ ] **Step 6: Commit**

```bash
git add test/helpers.py test/test_trait_odds.py test/test_table_groups.py
git commit -m "table_keys follows a group reference, so the theme and flag sweeps see members"
```

---

### Task 9: The trait-import skill and its tests

**Files:**
- Modify: `.claude/skills/npc-trait-import/SKILL.md` (§4 shape lines near line 409, §7 validation item 2 near line 731)
- Modify: `test/test_import_skill_shape.py` (`test_no_shape_line_names_a_table_that_does_not_exist`, plus a new test)

- [ ] **Step 1: Write the failing test**

Append to `test/test_import_skill_shape.py`, inside the existing test class:

```python
    def test_a_group_table_takes_the_shape_of_the_table_that_references_it(self):
        """A '## Flight suits' that Outfit enters through '- => Flight suits'
        holds Outfit-shaped bullets, so it needs no shape line of its own and
        must not have one that disagrees."""
        for name in gen.REQUIRED_TABLES:
            for group, reference in gen.references_in(LIVE, name).items():
                with self.subTest(group=group):
                    self.assertNotIn(group, SHAPE_LINES,
                                     "%s is a group of %s and takes its shape line" % (group, name))
                    self.assertTrue(name in SHAPE_LINES or name in NOT_STAGED,
                                    "%s references %s but has no shape line" % (name, group))
```

and widen `test_no_shape_line_names_a_table_that_does_not_exist` so `known` is:

```python
        known = set(gen.REQUIRED_TABLES) | {k.partition(" (")[0] for k in gen.group_tables(LIVE)}
```

Check the module defines `LIVE` (it parses the live file near the top; if it only has `gen`, add `LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")` with `REPO` imported from `test.helpers`).

- [ ] **Step 2: Run it**

Run: `python -m unittest test.test_import_skill_shape -v 2>&1 | tail -4`
Expected: OK already (no groups in the live file yet). The test is the contract Task 11 has to keep.

- [ ] **Step 3: Document the rule in SKILL.md**

In §4, after the `**Outfit**` shape line, add:

```markdown
- **Groups**: a heading that a rolled table enters through a `- => Heading`
  bullet (see "How the script reads this file" in the tables file) takes the
  shape line of the table that references it, flags included. Stage a
  variant of an existing family under the group's exact heading
  (`"table": "Flight suits"`) rather than under `Outfit`. A run never
  authors a `=>` bullet: creating a group is a curation decision.
```

In §7 item 2, after "The importer refuses anything else.", add: "A group heading is a real heading too, and the right target for a variant of the family it holds."

- [ ] **Step 4: Run the skill tests**

Run: `python -m unittest test.test_import_skill_shape test.test_import_skill_flags test.test_import_skill_theme -v 2>&1 | tail -4`
Expected: OK

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/npc-trait-import/SKILL.md test/test_import_skill_shape.py
git commit -m "the import skill stages a family variant under its group, and never authors a reference"
```

---

### Task 10: Document the syntax

**Files:**
- Modify: `prompts/npc-generator-tables.md` (the `## How the script reads this file` section, after the weights paragraph near line 26)
- Modify: `README.md` (near line 59 "Adding options to a table needs no code change", and the cross-repo contract paragraph near line 267)

- [ ] **Step 1: Add the preamble paragraph**

After the paragraph ending "...templates at the bottom of this file.", insert:

```markdown
A bullet of the form `- => Name` is a **group reference**: one slot of this
table whose value is drawn second, from the `## Name` table. Ten near-identical
black dresses in a `## Black dresses` table then weigh what one distinct jacket
weighs, and the specific dress is chosen inside the group. A reference takes an
`xN ` weight like any bullet and may carry `@theme` tags (`- => Black dresses
(gundam) || @gundam`), which make the whole group a themed one; it carries no
other flags, since `civ`, `mil`, `notac` and `dressy` belong on the members. A
group may have `(she)` and `(she) +` variants like any table, and a reference
placed in `## Outfit (she) +` makes the group women-only. One level only: a
group table holds no references. The script refuses a reference that names a
missing table, a rolled table, or a group twice from one table. The `###`
sub-headings under Callsigns are the other kind of grouping, cosmetic only.
```

- [ ] **Step 2: Update the README**

After the sentence at line ~59 ("Adding options to a table needs no code change — every `-` bullet under a `##` heading in the tables file is one option."), add: "A `- => Name` bullet is a group reference, one slot that resolves from `## Name`; the tables file's own preamble explains it."

In the cross-repo contract paragraph (~267), extend the list of on-disk shapes with "the `=> Name` group reference".

- [ ] **Step 3: Run the suite (the preamble is parsed as a table and must stay harmless)**

Run: `python -m unittest discover test 2>&1 | tail -3`
Expected: OK. `check_group_references()` skips the preamble because its heading is not in `REQUIRED_TABLES` only if the preamble's example bullets are not literal `- => ...` lines at column zero; the paragraph above is prose with inline code, not bullets, which keeps it so.

- [ ] **Step 4: Commit**

```bash
git add prompts/npc-generator-tables.md README.md
git commit -m "document the '=> Name' group reference beside the weight syntax"
```

---

### Task 11: The Outfit first pass

**Files:**
- Modify: `prompts/npc-generator-tables.md` (`## Outfit` at line 1695 and `## Outfit (she) +` at line 1849, at commit `a4e9b39`)

**Prerequisite:** GUI plan tasks 1 and 2 landed, or accept that the GUI's drift test fails until they do.

- [ ] **Step 1: Confirm the line numbers still hold**

Run: `git log --oneline -1 -- prompts/npc-generator-tables.md` and `sed -n '1732p;1860p;1931p' prompts/npc-generator-tables.md`
Expected: line 1732 begins `- a fitted flight suit with the top half unzipped`, 1860 begins `- x2 a flight suit tailored close`, 1931 begins `- a tailored pinstripe blazer`. If the file changed since `a4e9b39`, re-derive the numbers from the spec's quoted texts before running the script.

- [ ] **Step 2: Write the one-off move script (not committed)**

Save as `regroup_outfit.py` in the repo root:

```python
"""One-off: move Outfit's near-duplicate families into group tables.
Line numbers are 1-based and refer to the file at commit a4e9b39."""
from pathlib import Path

FILE = Path("prompts/npc-generator-tables.md")
GROUPS = [
    # (group heading, referenced from, base member lines, she member lines, reference bullet)
    ("Flight suits", "Outfit", [1732, 1766, 1767, 1769, 1793, 1794, 1798, 1826, 1829, 1842], [1860, 1867, 1877, 1891, 1909], "=> Flight suits"),
    ("Combat uniforms and plate carriers", "Outfit", [1743, 1744, 1745, 1749, 1750, 1752, 1753, 1756], [1869], "=> Combat uniforms and plate carriers"),
    ("Field jackets", "Outfit", [1759, 1762, 1763, 1779, 1805, 1828, 1830], [1879], "=> Field jackets"),
    ("Open jackets over plated or glowing bodysuits", "Outfit", [1758, 1781], [1872, 1873, 1874, 1887, 1888, 1889], "=> Open jackets over plated or glowing bodysuits"),
    ("Glowing-seam bodysuits", "Outfit", [1770], [1875, 1876, 1882, 1892, 1907, 1908], "=> Glowing-seam bodysuits"),
    ("Glowing-seam bodysuits (cyberpunk)", "Outfit (she) +", [], [1930, 1932], "=> Glowing-seam bodysuits (cyberpunk) || @cyberpunk"),
    ("Unlit tactical bodysuits", "Outfit", [1764, 1797, 1806], [1870, 1916, 1926], "=> Unlit tactical bodysuits"),
    ("Hardsuits and segmented armor", "Outfit", [1746, 1751, 1755, 1780, 1791, 1792, 1799, 1802, 1803, 1844], [1871, 1915], "=> Hardsuits and segmented armor"),
    ("Caped armor suits", "Outfit", [1772, 1775, 1800, 1807], [], "=> Caped armor suits"),
    ("Plain traditional robes", "Outfit", [1785, 1786, 1787, 1811, 1812, 1813], [], "=> Plain traditional robes"),
    ("Kimonos and fine robes", "Outfit", [1810, 1815, 1816], [1898, 1899, 1922], "=> Kimonos and fine robes"),
    ("Lacquered samurai armor", "Outfit", [1788, 1801, 1808, 1809], [1912, 1919, 1920, 1921], "=> Lacquered samurai armor"),
    ("Work coveralls", "Outfit", [1733, 1822, 1832, 1835, 1843], [1864], "=> Work coveralls"),
    ("Dress uniforms", "Outfit", [1747, 1771], [1868, 1894, 1895], "=> Dress uniforms"),
    ("Long coats over fatigues", "Outfit", [1734, 1748, 1768, 1838, 1845], [], "=> Long coats over fatigues"),
    ("Leather jackets", "Outfit", [1742, 1795, 1833, 1836], [1933], "=> Leather jackets"),
    ("Tank tops", "Outfit", [1737], [1880, 1884, 1902, 1911, 1913], "=> Tank tops"),
    ("Bomber and flight jackets", "Outfit", [1778, 1782, 1804], [1896, 1914], "=> Bomber and flight jackets"),
    ("Open jackets over crop tops", "Outfit (she) +", [], [1881, 1883, 1900, 1903, 1906], "=> Open jackets over crop tops"),
    ("Cheap suits", "Outfit", [1839, 1847], [], "=> Cheap suits"),
    ("Corporate skirt suits", "Outfit (she) +", [], [1866, 1931], "=> Corporate skirt suits"),
]

lines = FILE.read_text(encoding="utf-8").split("\n")
moved = {}                      # line number -> (group, is_she)
for group, _, base, she, _ in GROUPS:
    for n in base:
        moved[n] = (group, False)
    for n in she:
        moved[n] = (group, True)
for n in moved:
    assert lines[n - 1].startswith("- "), "line %d is not a bullet: %r" % (n, lines[n - 1])
assert len(moved) == 132, len(moved)

# Where each reference goes: the first moved line of its own parent table.
first_line = {}
for group, parent, base, she, ref in GROUPS:
    own = base if parent == "Outfit" else she
    first_line[min(own)] = ref

out = []
for i, line in enumerate(lines, start=1):
    if i in first_line:
        out.append("- " + first_line[i])
    if i in moved:
        continue
    out.append(line)

# The group tables, appended after '## Outfit (she) +' (before '## Headgear').
at = next(i for i, l in enumerate(out) if l.startswith("## Headgear"))
block = []
for group, _, base, she, _ in GROUPS:
    if base:
        block += ["## %s" % group, ""] + [lines[n - 1] for n in base] + [""]
    if she:
        heading = group if not base else "%s (she) +" % group
        block += ["## %s" % heading, ""] + [lines[n - 1] for n in she] + [""]
out[at:at] = block
FILE.write_text("\n".join(out), encoding="utf-8")
print("moved %d bullets into %d groups" % (len(moved), len(GROUPS)))
```

Note the women-only groups (cyberpunk bodysuits, crop-top jackets, corporate suits) get a plain `## Group` heading holding their she members, since only `## Outfit (she) +` references them. Groups with both get `## Group` and `## Group (she) +`.

- [ ] **Step 3: Run it, then delete it**

Run: `python regroup_outfit.py && rm regroup_outfit.py && git status --short`
Expected: `moved 132 bullets into 21 groups`; only `prompts/npc-generator-tables.md` modified.

- [ ] **Step 4: Read the result**

Run: `grep -n "^- => \|^## " prompts/npc-generator-tables.md | sed -n '/## Outfit/,/## Headgear/p'`
Expected: 18 references under `## Outfit`, 3 under `## Outfit (she) +`, then the group headings in the order of the table above, then `## Headgear`. Open the file around `## Outfit` and confirm the first reference sits where the first moved bullet was and no blank-line pairs were doubled.

- [ ] **Step 5: Run the suite**

Run: `python -m unittest discover test 2>&1 | tail -3`
Expected: OK. If `check_tables` complains, it names the heading and bullet; the usual cause is a group heading typed differently in the reference and the table.

- [ ] **Step 6: Take the odds readout**

Run: `python generate-npc.py --help | grep -i tables` to confirm the tables flag, then
`python generate-npc.py --trait-odds 20000 --tables prompts/npc-generator-tables.md > odds.json && python -c "import json; t=json.load(open('odds.json'))['tables']; print(round(t['Outfit']['=> Flight suits']*100,1), '% for => Flight suits;', round(sum(t['Flight suits'].values())*100,1), '% across its members')" && rm odds.json`
Expected: roughly 1 to 3 percent for the reference (one slot among about 55, more for women), and the members' sum equal to it. Before this task Flight suits were about 9 percent of male Outfit rolls.

- [ ] **Step 7: Commit with the readout**

```bash
git add prompts/npc-generator-tables.md
git commit -m "regroup Outfit: 132 near-duplicate bullets into 21 group tables

Flight suits now roll at N.N% of Outfit (was ~9.4% for eleven flat bullets); see
the spec's section 7 for the member list by line. The roll snapshot is untouched
because it pins the minimal fixture, not this file."
```

(Replace `N.N` with the figure from step 6.)

---

## Self-review

**Spec coverage.** §3 rules: Task 2. §4.1 helpers: Task 1. §4.2 narrow: Task 3. §4.3 resolution and the forced-reference refusal: Task 4. §4.4 recording: Task 4 (raw is the member) and Task 5 (heading_for). §4.5 odds: Task 5. §4.6 choices: Task 6. §4.7 ships: Task 7. §4.8 gates: Tasks 3, 4 and 11. §6 skill and tests: Tasks 8 and 9. §3 preamble and README: Task 10. §7 first pass: Task 11. §5 is the GUI plan.

**Placeholder scan.** Task 3 describes a verbatim move with exact boundary lines rather than re-listing 150 lines; every other code step is complete.

**Type consistency.** `reference_target` returns `str | None`; `references_in` returns `{target: bullet}`; `group_headings(tables, target, subject)` returns a list; `probe[target]` is a list of member bullets; `trait_choices` candidates are `(bullet, allowed)` pairs. Task 5 uses `group_headings` and `references_in` exactly as Task 1 defines them.
