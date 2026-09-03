# Theme Mechanism (Phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Roll one Theme per NPC and gate every appearance table through it, so an NPC's look comes from one visual world instead of several.

**Architecture:** A `## Theme` table is rolled once, immediately after Pronouns and before every table it gates. Appearance bullets carry `@theme` tags inside the existing `||` flag segment. A rolled theme opens its own tagged bullets plus every untagged one, excludes other themes', then duplicates the tagged ones until they hold ~60% of the pool so the theme is actually visible. This phase ships the mechanism with **no bullets tagged**, so output is unchanged and can be verified against current behaviour.

**Tech Stack:** Python 3, standard library only — no `pip`, no dependencies. Tests use `unittest`.

**Spec:** `docs/superpowers/specs/2026-09-03-themed-npc-generation-design.md` (§3, §6, §10)

## Global Constraints

- **Standard library only.** No `pip install`, no `requirements.txt`. This applies to tests as well.
- **Never filter a pool to nothing.** Every filter in `roll_npc()` ends `return filtered or options`. New filters must too.
- **Flags are matched literally**; an unrecognised flag is ignored rather than reported.
- **`THEME_SHARE = 0.6`** — the target share of a themed roll held by that theme's own bullets.
- **Phase 1 tags no bullets.** Adding `@theme` tags to `npc-generator-tables.md` is Phase 4. Task 7 depends on nothing being tagged yet.
- **Do not reorder `REQUIRED_TABLES`** beyond inserting `"Theme"` where this plan says. The Backdrop move is Phase 3.
- Existing behaviour that must not change: `split_flags()` keeps returning a 2-tuple, and every existing caller of it keeps working untouched.

---

### Task 1: Test harness

Stand up `unittest` and a loader for `generate-npc.py`, whose hyphen makes it non-importable by name. Nothing else in the plan can be tested until this exists.

**Files:**
- Create: `test/__init__.py` (empty)
- Create: `test/helpers.py`
- Create: `test/fixtures/tables-minimal.md`
- Create: `test/test_harness.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `test.helpers.load_generator() -> module`, `test.helpers.FIXTURE_TABLES -> pathlib.Path`.

- [ ] **Step 1: Create the package marker and fixture directory**

Portable across PowerShell and bash — this repo is developed on Windows, so
avoid `touch` and `mkdir -p`:

```bash
python -c "import pathlib; pathlib.Path('test/fixtures').mkdir(parents=True, exist_ok=True); pathlib.Path('test/__init__.py').touch()"
```

- [ ] **Step 2: Write the loader helper**

Create `test/helpers.py`:

```python
"""Shared test helpers.

generate-npc.py has a hyphen in its name, so `import generate-npc` is a syntax
error. Load it by path instead - the same trick the module's own docstring
describes for generate-art.py.
"""
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURE_TABLES = Path(__file__).resolve().parent / "fixtures" / "tables-minimal.md"

_cached = None


def load_generator():
    """The generate-npc.py module object, loaded once per process."""
    global _cached
    if _cached is None:
        spec = importlib.util.spec_from_file_location(
            "gennpc", REPO / "generate-npc.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["gennpc"] = module
        spec.loader.exec_module(module)
        _cached = module
    return _cached
```

- [ ] **Step 3: Write the fixture tables file**

Create `test/fixtures/tables-minimal.md`. This is deliberately tiny and
independent of the real content, so authoring a bullet never breaks a test.
It must contain every table in `REQUIRED_TABLES`.

```markdown
# Minimal fixture tables

Used by the test suite. Not used by the generator at runtime.

## Theme
- x2 alpha
- beta

## Given names
- Test

## Family names
- Subject

## Callsigns
- Fixture

## Pronouns
- she/her/her/woman
- they/them/their/person

## Age
- in {possessive} thirties
- in {possessive} late teens || young

## Build
- lean and wiry
- full-figured through the hips || figure

## Height
- of average height

## Skin
- pale skin

## Hair
- a short crop
- a long braid || @alpha
- a shaved head || @beta

## Eyes
- grey eyes

## Feature
- a scar across one cheek

## Demeanor
- a flat stare

## Role
- a dockworker
- a Union marine soldier || mil

## Faction
- unaligned and freelance
- in dress uniform || mil

## Outfit
- grey coveralls
- lacquered plate || @alpha
- a neon techwear jacket || @beta

## Headgear
- {Subject} {is_are} bare-headed.
- {Subject} {wear} a wide woven hat. || @alpha

## Gear
- a battered data-slate || hands
- a service pistol worn openly at the thigh || mil weapon simple sidearm

## Accent
- teal-green

## Backdrop
- A half-body character portrait || Behind {object} is a plain wall.
- A character portrait || {Subject} {is_are} in a temple courtyard. || weather @alpha

## Weather
- in steady rain
- || clear

## Stance
- standing squarely
- {possessive} hands in {possessive} pockets || hands
```

- [ ] **Step 4: Write the failing test**

Create `test/test_harness.py`:

```python
import unittest

from test.helpers import FIXTURE_TABLES, load_generator


class TestHarness(unittest.TestCase):
    def test_generator_loads(self):
        gen = load_generator()
        self.assertTrue(hasattr(gen, "roll_npc"))

    def test_fixture_has_every_required_table(self):
        gen = load_generator()
        tables = gen.parse_tables(FIXTURE_TABLES)
        missing = [t for t in gen.REQUIRED_TABLES if t not in tables]
        self.assertEqual(missing, [], "fixture is missing required tables")

    def test_fixture_rolls_an_npc(self):
        import random
        gen = load_generator()
        tables = gen.parse_tables(FIXTURE_TABLES)
        npc = gen.roll_npc(tables, random.Random(0))
        self.assertEqual(npc["name"], "Test Subject")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m unittest discover test -v`

Expected: **PASS, 3 tests.** This task is the only one in the plan that does not
start red — its deliverable is a working harness, and a harness that cannot
load the generator or roll from the fixture is simply broken. The fixture is a
superset of today's `REQUIRED_TABLES` (it already carries `## Theme`, which
nothing reads yet), so all three pass.

If `test_generator_loads` fails, the path in `helpers.py` is wrong. If
`test_fixture_rolls_an_npc` fails, the fixture is missing a table or a
pronoun placeholder — the error names which.

- [ ] **Step 6: Commit**

```bash
git add test/__init__.py test/helpers.py test/fixtures/tables-minimal.md test/test_harness.py
git commit -m "test: stand up a stdlib unittest harness for the NPC generator"
```

---

### Task 2: Read `@theme` tags off a bullet

**Files:**
- Modify: `generate-npc.py` (add two helpers next to `split_flags`)
- Create: `test/test_theme_tags.py`

**Interfaces:**
- Consumes: `split_flags(bullet) -> (text, flags)`, `split_backdrop(bullet) -> (shot, scene, flags)` — both existing, both unchanged.
- Produces:
  - `themes_of(flags: tuple) -> frozenset[str]`
  - `flags_for(table_name: str, bullet: str) -> tuple[str, ...]`

**Design note for the implementer:** `split_flags()` is deliberately **not**
changed. An `@alpha` token sitting in its returned tuple is invisible to every
existing check, because those all ask `"hands" in flags` or similar and
`"@alpha"` matches none of them. Adding a separate reader is therefore lower
risk than changing the shared splitter.

- [ ] **Step 1: Write the failing test**

Create `test/test_theme_tags.py`:

```python
import unittest

from test.helpers import load_generator

gen = load_generator()


class TestThemesOf(unittest.TestCase):
    def test_no_flags_means_no_themes(self):
        self.assertEqual(gen.themes_of(()), frozenset())

    def test_behavioural_flags_are_not_themes(self):
        self.assertEqual(gen.themes_of(("hands", "gun", "mil")), frozenset())

    def test_strips_the_at_prefix(self):
        self.assertEqual(gen.themes_of(("@alpha",)), frozenset({"alpha"}))

    def test_reads_several_and_ignores_behavioural_flags(self):
        self.assertEqual(
            gen.themes_of(("civ", "@alpha", "notac", "@beta")),
            frozenset({"alpha", "beta"}),
        )

    def test_a_bare_at_is_not_a_theme(self):
        self.assertEqual(gen.themes_of(("@",)), frozenset())


class TestFlagsFor(unittest.TestCase):
    def test_two_segment_table(self):
        self.assertEqual(
            gen.flags_for("Outfit", "lacquered plate || civ @alpha"),
            ("civ", "@alpha"),
        )

    def test_backdrop_reads_its_third_segment(self):
        self.assertEqual(
            gen.flags_for("Backdrop", "A shot || A scene. || weather @alpha"),
            ("weather", "@alpha"),
        )

    def test_backdrop_without_flags_has_none(self):
        # Two segments only: the scene must never be mistaken for flags.
        self.assertEqual(
            gen.flags_for("Backdrop", "A shot || A scene with an @ in it."),
            (),
        )

    def test_unflagged_bullet_of_any_table(self):
        self.assertEqual(gen.flags_for("Outfit", "grey coveralls"), ())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest test.test_theme_tags -v`

Expected: FAIL with `AttributeError: module 'gennpc' has no attribute 'themes_of'`

- [ ] **Step 3: Write the implementation**

In `generate-npc.py`, immediately after `split_backdrop()`, add:

```python
def themes_of(flags):
    """The '@theme' tags among a bullet's flags, with the '@' stripped.

    Theme tags share the '||' flag segment with the behavioural flags rather
    than getting a field of their own, because every consumer of this file -
    split_flags(), the npc-trait-import skill, the Import GUI's bullet editor -
    already parses that segment. The '@' prefix is what tells the two apart.

    An '@' token is invisible to the behavioural flag checks elsewhere in this
    module, which all test for a specific literal ('hands', 'civ', 'figure'),
    so split_flags() needs no change to coexist with these.
    """
    return frozenset(f[1:] for f in flags if f.startswith("@") and len(f) > 1)


def flags_for(name, bullet):
    """A bullet's flag tuple, whichever '||' shape its table uses.

    Backdrop bullets carry three segments and keep their flags in the third,
    so a two-segment Backdrop has no flags at all - its second segment is the
    scene. Every other table keeps flags in the second segment. Reading the
    last segment blindly would mistake a Backdrop's scene text for flags.
    """
    if name == "Backdrop":
        return split_backdrop(bullet)[2]
    return split_flags(bullet)[1]
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m unittest test.test_theme_tags -v`

Expected: PASS, 9 tests.

- [ ] **Step 5: Commit**

```bash
git add generate-npc.py test/test_theme_tags.py
git commit -m "feat: read '@theme' tags out of a bullet's flag segment"
```

---

### Task 3: Filter a pool by theme

**Files:**
- Modify: `generate-npc.py` (add `filter_by_theme()` next to `filter_by_mil()`)
- Create: `test/test_theme_filter.py`

**Interfaces:**
- Consumes: `themes_of()`, `flags_for()` from Task 2.
- Produces: `filter_by_theme(options: list[str], theme: str | None, name: str) -> list[str]`

- [ ] **Step 1: Write the failing test**

Create `test/test_theme_filter.py`:

```python
import unittest

from test.helpers import load_generator

gen = load_generator()

POOL = [
    "grey coveralls",                      # neutral
    "a work apron",                        # neutral
    "lacquered plate || civ @alpha",       # alpha
    "a neon jacket || civ @beta",          # beta
    "a hybrid rig || @alpha @beta",        # both
]


class TestFilterByTheme(unittest.TestCase):
    def test_opens_own_tagged_bullets_and_all_neutral_ones(self):
        got = gen.filter_by_theme(POOL, "alpha", "Outfit")
        self.assertIn("grey coveralls", got)
        self.assertIn("a work apron", got)
        self.assertIn("lacquered plate || civ @alpha", got)

    def test_excludes_other_themes(self):
        got = gen.filter_by_theme(POOL, "alpha", "Outfit")
        self.assertNotIn("a neon jacket || civ @beta", got)

    def test_multi_tagged_bullets_are_reachable_from_either_theme(self):
        both = "a hybrid rig || @alpha @beta"
        self.assertIn(both, gen.filter_by_theme(POOL, "alpha", "Outfit"))
        self.assertIn(both, gen.filter_by_theme(POOL, "beta", "Outfit"))

    def test_no_theme_leaves_the_pool_untouched(self):
        self.assertEqual(gen.filter_by_theme(POOL, None, "Outfit"), POOL)

    def test_never_filters_the_pool_to_nothing(self):
        only_foreign = ["a neon jacket || @beta", "a chrome visor || @beta"]
        self.assertEqual(
            gen.filter_by_theme(only_foreign, "alpha", "Outfit"), only_foreign)

    def test_works_on_backdrop_three_segment_bullets(self):
        pool = [
            "A shot || A plain scene.",
            "A shot || A temple courtyard. || weather @alpha",
            "A shot || A neon street. || weather @beta",
        ]
        got = gen.filter_by_theme(pool, "alpha", "Backdrop")
        self.assertEqual(len(got), 2)
        self.assertNotIn("A shot || A neon street. || weather @beta", got)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest test.test_theme_filter -v`

Expected: FAIL with `AttributeError: module 'gennpc' has no attribute 'filter_by_theme'`

- [ ] **Step 3: Write the implementation**

In `generate-npc.py`, immediately after `filter_by_mil()`, add:

```python
def filter_by_theme(options, theme, name):
    """A theme's own bullets plus the neutral pool; other themes' are dropped.

    The neutral pool - every bullet carrying no '@' tag at all - is deliberately
    reachable from every theme. Roughly 45% of this file's appearance bullets
    are the campaign's plain worn-industrial look, and they belong in a
    neosamurai NPC's wardrobe as much as anyone's: a woman in a kimono and a
    woman in grey coveralls are both this setting.

    Never filtered down to nothing, the same as every other filter here: a
    tables file with no tags yet - which is exactly what this ships as - falls
    back to the full pool rather than erroring.
    """
    if not theme:
        return options
    keep = [
        x for x in options
        if not themes_of(flags_for(name, x)) or theme in themes_of(flags_for(name, x))
    ]
    return keep or options
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m unittest test.test_theme_filter -v`

Expected: PASS, 6 tests.

- [ ] **Step 5: Commit**

```bash
git add generate-npc.py test/test_theme_filter.py
git commit -m "feat: open a theme's bullets plus the neutral pool, excluding other themes"
```

---

### Task 4: Weight the theme so it is visible

Opening a theme's bullets is not enough. With 11 tagged bullets against a
185-bullet neutral floor, a themed NPC rolls neutral almost every time and the
theme is never seen. This duplicates the tagged bullets until they hold a
target share of the pool.

**Files:**
- Modify: `generate-npc.py` (add `THEME_SHARE` constant and `apply_theme_share()`)
- Create: `test/test_theme_share.py`

**Interfaces:**
- Consumes: `themes_of()`, `flags_for()` from Task 2.
- Produces: `THEME_SHARE: float`, `apply_theme_share(options: list[str], theme: str | None, name: str, share: float = THEME_SHARE) -> list[str]`

- [ ] **Step 1: Write the failing test**

Create `test/test_theme_share.py`:

```python
import unittest

from test.helpers import load_generator

gen = load_generator()


def build(tagged, neutral):
    return (["t%d || @alpha" % i for i in range(tagged)]
            + ["n%d" % i for i in range(neutral)])


def share_of(pool, theme="alpha", name="Outfit"):
    hits = sum(1 for x in pool if theme in gen.themes_of(gen.flags_for(name, x)))
    return hits / len(pool)


class TestApplyThemeShare(unittest.TestCase):
    def test_thin_theme_still_reaches_the_target_share(self):
        # 11 tagged against 60 neutral - the @grimdark case.
        out = gen.apply_theme_share(build(11, 60), "alpha", "Outfit")
        self.assertGreaterEqual(share_of(out), gen.THEME_SHARE)

    def test_fat_theme_also_reaches_it(self):
        # 56 tagged against 60 neutral - the @gundam case.
        out = gen.apply_theme_share(build(56, 60), "alpha", "Outfit")
        self.assertGreaterEqual(share_of(out), gen.THEME_SHARE)

    def test_every_neutral_bullet_stays_reachable(self):
        out = gen.apply_theme_share(build(3, 20), "alpha", "Outfit")
        for i in range(20):
            self.assertIn("n%d" % i, out)

    def test_every_tagged_bullet_stays_reachable(self):
        out = gen.apply_theme_share(build(3, 20), "alpha", "Outfit")
        for i in range(3):
            self.assertIn("t%d || @alpha" % i, out)

    def test_no_theme_leaves_the_pool_untouched(self):
        pool = build(3, 20)
        self.assertEqual(gen.apply_theme_share(pool, None, "Outfit"), pool)

    def test_no_tagged_bullets_leaves_the_pool_untouched(self):
        pool = ["n0", "n1", "n2"]
        self.assertEqual(gen.apply_theme_share(pool, "alpha", "Outfit"), pool)

    def test_no_neutral_bullets_leaves_the_pool_untouched(self):
        pool = ["t0 || @alpha", "t1 || @alpha"]
        self.assertEqual(gen.apply_theme_share(pool, "alpha", "Outfit"), pool)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest test.test_theme_share -v`

Expected: FAIL with `AttributeError: module 'gennpc' has no attribute 'apply_theme_share'`

- [ ] **Step 3: Write the implementation**

Add `import math` to the imports at the top of `generate-npc.py` if it is not
already there. Then, next to the other policy constants near `GEAR_POLICY`, add:

```python
# How much of a themed roll should come from that theme's own bullets rather
# than from the neutral pool. A theme that is merely *opened* is not *visible*:
# with a dozen tagged bullets against a neutral floor of nearly two hundred, a
# themed NPC would roll neutral almost every time and the theme would never be
# seen. Raise it for a stronger house style, lower it for more variety.
THEME_SHARE = 0.6
```

And after `filter_by_theme()`, add:

```python
def apply_theme_share(options, theme, name, share=THEME_SHARE):
    """Duplicate the theme's own bullets until they hold `share` of the pool.

    The multiplier is computed from the actual pool sizes rather than fixed, so
    it self-corrects as content is authored: a theme with 56 outfits barely
    needs duplicating, one with 11 needs a lot. A thin theme therefore still
    reads as itself - at the cost of repeating within a run, which its low
    weight in the Theme table already makes uncommon.

    Untouched when there is nothing to balance: no theme, no tagged bullets, or
    no neutral ones. Duplication only ever adds entries, so every bullet in the
    pool stays reachable.
    """
    if not theme:
        return options
    tagged = [x for x in options if theme in themes_of(flags_for(name, x))]
    neutral = [x for x in options if not themes_of(flags_for(name, x))]
    if not tagged or not neutral:
        return options

    # Want tagged*n / (tagged*n + neutral) >= share, so
    # n >= share*neutral / ((1 - share) * tagged).
    n = math.ceil(share * len(neutral) / ((1 - share) * len(tagged)))
    return tagged * max(1, n) + neutral
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m unittest test.test_theme_share -v`

Expected: PASS, 7 tests.

- [ ] **Step 5: Commit**

```bash
git add generate-npc.py test/test_theme_share.py
git commit -m "feat: weight a rolled theme so it outweighs the neutral pool"
```

---

### Task 5: Add the `## Theme` table to the tables file

Content and documentation only — no code. The eight themes and their starting
weights come from clustering the existing bullets; see spec §3.1.

**Files:**
- Modify: `prompts/npc-generator-tables.md` (new `## Theme` section, and the header note)

**Interfaces:**
- Consumes: nothing.
- Produces: a `## Theme` table that `parse_tables()` will pick up, whose bullets are bare theme names matching the `@` tags used later.

- [ ] **Step 1: Add the table**

Insert a new section into `prompts/npc-generator-tables.md`, immediately after
the `## Pronouns` table and before `## Age`, so the file's order mirrors the
roll order:

```markdown
## Theme

<!--
  The visual world this NPC comes from, rolled once and honoured by every
  appearance table. This is what makes a rolled NPC read as one coherent
  character rather than a bag of independently-rolled traits.

  A bullet here is a bare name; appearance bullets refer to it with an '@'
  prefix in their flag segment - '|| civ @neosamurai'. A rolled theme opens
  its own tagged bullets plus every untagged one, and excludes the rest.

  Theme is deliberately independent of Role: a pirate is as likely to look
  neosamurai as cyberpunk. Do not gate one on the other.

  Weights start proportional to how much content each theme has, so a thin
  theme is rare rather than repetitive. Raise a weight as you author more -
  it needs no code change. The intended end state is roughly equal weights.

  There is deliberately no 'grounded' entry: the untagged bullets throughout
  this file already are the worn-industrial Lancer look, and they serve as the
  neutral floor every theme draws from rather than competing as a ninth theme.
-->

- x6 gundam
- x6 tactical
- x6 neosamurai
- x4 cyberpunk
- x2 neogothic
- grimdark
- corporate
- scav
```

- [ ] **Step 2: Document the tag syntax in the file header**

In the `## How the script reads this file` section, immediately after the
paragraph beginning "`||` splits a bullet into segments.", add:

```markdown
A flag beginning `@` is a **theme tag** rather than a behavioural flag — 
`|| civ @neosamurai` reads as "civilian dress, belonging to the neosamurai
look". The `Theme` table is rolled once per NPC before any appearance table,
and a rolled theme opens its own tagged bullets plus every **untagged** one,
excluding bullets tagged with a different theme. A bullet may carry more than
one tag and is then reachable from either. An untagged bullet is neutral and
reachable from every theme — most bullets in this file are, and should stay
that way; tag only what is strongly of one look.
```

- [ ] **Step 3: Verify the table parses**

Run:

```bash
python -c "
import importlib.util, sys, pathlib
spec = importlib.util.spec_from_file_location('g', 'generate-npc.py')
m = importlib.util.module_from_spec(spec); sys.modules['g']=m; spec.loader.exec_module(m)
t = m.parse_tables(pathlib.Path('prompts/npc-generator-tables.md'))
print('Theme entries (weighted):', len(t['Theme']))
import collections; print(collections.Counter(t['Theme']))
"
```

Expected: `Theme entries (weighted): 27`, with `gundam`, `tactical` and
`neosamurai` at 6 each, `cyberpunk` at 4, `neogothic` at 2, and `grimdark`,
`corporate`, `scav` at 1.

- [ ] **Step 4: Commit**

```bash
git add prompts/npc-generator-tables.md
git commit -m "content: add the Theme table and document the '@theme' tag syntax"
```

---

### Task 6: Roll the theme and wire the filters in

**Files:**
- Modify: `generate-npc.py` — `REQUIRED_TABLES` (~line 105), `roll_npc()` (~line 453), `write_dossier()` (~line 755), the `--set-trait` help text (~line 931)
- Create: `test/test_theme_roll.py`

**Interfaces:**
- Consumes: `filter_by_theme()` (Task 3), `apply_theme_share()` (Task 4), the `## Theme` table (Task 5).
- Produces: `THEMED_TABLES: tuple[str, ...]`; `roll_npc()` returns a dict with a `"Theme"` key.

- [ ] **Step 1: Write the failing test**

Create `test/test_theme_roll.py`:

```python
import random
import unittest

from test.helpers import FIXTURE_TABLES, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)


def roll(seed, **overrides):
    return gen.roll_npc(TABLES, random.Random(seed), overrides or None)


class TestThemeRoll(unittest.TestCase):
    def test_every_npc_has_a_theme(self):
        for seed in range(50):
            self.assertIn(roll(seed)["Theme"], {"alpha", "beta"})

    def test_theme_can_be_forced(self):
        self.assertEqual(roll(0, Theme="beta")["Theme"], "beta")

    def test_no_npc_carries_a_foreign_theme(self):
        """The core cohesion guarantee, over every themed table."""
        for seed in range(300):
            npc = roll(seed)
            theme = npc["Theme"]
            for name in gen.THEMED_TABLES:
                tags = gen.themes_of(gen.flags_for(name, npc[name]))
                if tags:
                    self.assertIn(
                        theme, tags,
                        "seed %d: theme %r got a %s tagged %s"
                        % (seed, theme, name, sorted(tags)))

    def test_theme_is_independent_of_role(self):
        """A pirate must be as likely to look alpha as any other role is."""
        rolled = [roll(s) for s in range(600)]
        pairs = [(n["Theme"], n["Role"]) for n in rolled]
        roles = {r for _, r in pairs}
        self.assertGreater(len(roles), 1, "fixture must roll more than one role")
        for role in roles:
            themes = [t for t, r in pairs if r == role]
            alpha = themes.count("alpha") / len(themes)
            # Fixture weights alpha 2:1, so expect ~0.67 regardless of role.
            self.assertGreater(alpha, 0.45, "role %r skews low on alpha" % role)
            self.assertLess(alpha, 0.85, "role %r skews high on alpha" % role)

    def test_theme_reaches_the_dossier(self):
        npc = roll(0)
        self.assertIn("Theme", npc)

    def test_no_pool_is_ever_starved(self):
        """Every themed table must still yield a value for every theme."""
        for theme in ("alpha", "beta"):
            for seed in range(100):
                npc = roll(seed, Theme=theme)
                for name in gen.THEMED_TABLES:
                    self.assertTrue(npc[name], "%s empty for %s" % (name, theme))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest test.test_theme_roll -v`

Expected: FAIL with `KeyError: 'Theme'` — `roll_npc()` does not roll one yet.

- [ ] **Step 3: Add `Theme` to `REQUIRED_TABLES` and declare the themed tables**

In `generate-npc.py`, change `REQUIRED_TABLES` to insert `"Theme"` directly
after `"Pronouns"`:

```python
REQUIRED_TABLES = [
    "Given names", "Family names", "Callsigns", "Pronouns", "Theme", "Age",
    "Build", "Height", "Skin", "Hair", "Eyes", "Feature", "Demeanor", "Role",
    "Faction", "Outfit", "Headgear", "Gear", "Accent", "Backdrop", "Weather",
    "Stance",
]

# The tables a rolled Theme gates. Everything else - names, age, build, height,
# skin, eyes, accent, weather, stance - describes the person or the moment
# rather than the visual world they come from, and stays untouched by theme.
# Phase 2 adds "Weapon" and "Hair colour" here when those tables exist.
THEMED_TABLES = ("Hair", "Feature", "Outfit", "Headgear", "Gear", "Backdrop")
```

- [ ] **Step 4: Roll the theme before the loop and filter inside it**

In `roll_npc()`, immediately after the `pronouns` / `subject` lines at the top,
add the theme roll:

```python
    # Theme is rolled before every appearance table it gates, for the same
    # reason Pronouns is: the roll that selects between pools has to happen
    # before those pools are drawn from. It is deliberately NOT gated on Role -
    # a pirate should be as likely to look neosamurai as cyberpunk - so nothing
    # here reads npc["Role"].
    theme = (overrides or {}).get("Theme") or rng.choice(tables["Theme"])
```

Change the dict initialiser on the next line from `npc = {"Pronouns": pronouns}`
to:

```python
    npc = {"Pronouns": pronouns, "Theme": theme}
```

Change the loop's skip line from `if name in ("Pronouns", "Stance"):` to:

```python
        if name in ("Pronouns", "Theme", "Stance"):
            continue
```

Then, inside the loop directly after `options = variant_table(tables, name, subject)`
and **before** the `Build`/`Age` filter block, add:

```python
        # Theme gates every appearance table: its own tagged bullets plus the
        # neutral pool, with the tagged ones weighted up so the theme is
        # actually visible rather than merely available. Applied first, so the
        # civ/mil and policy filters below narrow within the theme rather than
        # across it - which is what lets a soldier be neosamurai in uniform.
        if name in THEMED_TABLES:
            options = filter_by_theme(options, theme, name)
            options = apply_theme_share(options, theme, name)
```

- [ ] **Step 5: Show the theme in the dossier**

In `write_dossier()`, add a row to the `traits` list, immediately after the
`("Reads as", ...)` entry:

```python
        ("Theme", npc.get("Theme", "-")),
```

`.get` rather than `[...]`, so regenerating an NPC from a manifest entry
written before this change still writes a dossier instead of raising.

- [ ] **Step 6: Mention Theme in the `--set-trait` help**

In `parse_args()`, extend the `--set-trait` help string to name Theme as a
forceable trait:

```python
    roll.add_argument("--set-trait", action="append", default=[], metavar="Table=value",
                      help="force one rolled trait, e.g. --set-trait Role='a field medic' "
                           "or --set-trait Theme=neosamurai to pin a whole group to one look")
```

- [ ] **Step 7: Run the test to verify it passes**

Run: `python -m unittest test.test_theme_roll -v`

Expected: PASS, 6 tests.

- [ ] **Step 8: Run the whole suite**

Run: `python -m unittest discover test -v`

Expected: PASS, all tests from Tasks 1-6.

- [ ] **Step 9: Commit**

```bash
git add generate-npc.py test/test_theme_roll.py
git commit -m "feat: roll a Theme per NPC and gate the appearance tables through it"
```

---

### Task 7: Prove the mechanism is inert against the real tables

Phase 1 ships with **no bullets tagged**, so both new filters must be no-ops
against the live tables file. This is what makes the phase safe to land ahead
of the content work.

**What this task does NOT assert.** An earlier draft of this plan tried to pin
whole prompts byte-identical to before the change. That premise is wrong:
`rng.choice(tables["Theme"])` consumes one draw before every other roll, so
every downstream draw shifts and a given seed legitimately produces a different
NPC. That is true of *any* new table — `Height` did the same when it was added
— and the dossier's reproducibility promise is already scoped to "that seed
**and the same tables file**". Do not try to preserve the stream; assert the
filters are no-ops instead, which is both exact and what actually matters.

**Files:**
- Create: `test/test_theme_inert.py`

**Interfaces:**
- Consumes: `filter_by_theme()`, `apply_theme_share()`, `THEMED_TABLES`, `flags_for()`, `themes_of()`.
- Produces: nothing.

- [ ] **Step 1: Write the test**

Create `test/test_theme_inert.py`:

```python
import unittest

from test.helpers import REPO, load_generator

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")
THEMES = sorted(set(LIVE["Theme"]))


class TestUntaggedTablesAreUnaffected(unittest.TestCase):
    """Until Phase 4 tags content, both theme filters must be no-ops.

    Delete this file when Phase 4 begins - once bullets carry '@' tags these
    filters are *supposed* to narrow the pool, and this becomes a false alarm
    rather than a regression.
    """

    def test_the_live_tables_carry_no_theme_tags_yet(self):
        for name in gen.THEMED_TABLES:
            for bullet in LIVE[name]:
                self.assertEqual(
                    gen.themes_of(gen.flags_for(name, bullet)), frozenset(),
                    "%s is already tagged: %r - Phase 4 has started, delete "
                    "test/test_theme_inert.py" % (name, bullet[:60]))

    def test_filter_by_theme_is_a_no_op(self):
        for name in gen.THEMED_TABLES:
            for theme in THEMES:
                self.assertEqual(
                    gen.filter_by_theme(LIVE[name], theme, name), LIVE[name],
                    "%s changed under theme %r" % (name, theme))

    def test_apply_theme_share_is_a_no_op(self):
        for name in gen.THEMED_TABLES:
            for theme in THEMES:
                self.assertEqual(
                    gen.apply_theme_share(LIVE[name], theme, name), LIVE[name],
                    "%s changed under theme %r" % (name, theme))

    def test_every_theme_still_rolls_a_full_pool(self):
        """No theme may starve any table it gates."""
        for name in gen.THEMED_TABLES:
            for theme in THEMES:
                pool = gen.apply_theme_share(
                    gen.filter_by_theme(LIVE[name], theme, name), theme, name)
                self.assertEqual(len(pool), len(LIVE[name]))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it**

Run: `python -m unittest test.test_theme_inert -v`

Expected: PASS, 4 tests.

**If `test_the_live_tables_carry_no_theme_tags_yet` fails,** someone has begun
Phase 4's tagging early. Finish Phase 1 against a clean tables file first.

**If either no-op test fails,** a filter is mutating an untagged pool — most
likely `apply_theme_share()` failing to return early when `tagged` is empty.
Fix the filter, not the test.

- [ ] **Step 3: Run the whole suite**

Run: `python -m unittest discover test -v`

Expected: PASS, every test from Tasks 1-7.

- [ ] **Step 4: Commit**

```bash
git add test/test_theme_inert.py
git commit -m "test: pin that both theme filters are no-ops until content is tagged"
```

---

### Task 8: Documentation

**Files:**
- Modify: `docs/generate-npc.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: everything above.
- Produces: nothing.

- [ ] **Step 1: Document the Theme axis in the generator docs**

In `docs/generate-npc.md`, add a section after the roll-table enumeration:

```markdown
## Theme

Every NPC rolls one **Theme** — the visual world they come from — before any
appearance table, and that theme gates Hair, Feature, Outfit, Headgear, Gear
and Backdrop. It is what makes a rolled NPC read as one coherent character
instead of a bag of independently-rolled traits.

A rolled theme opens its own `@`-tagged bullets **plus every untagged one**,
and excludes bullets tagged with a different theme. Roughly 45% of the
appearance bullets in the tables file carry no tag at all; that neutral pool is
the campaign's plain worn-industrial look and is reachable from every theme, so
a neosamurai NPC in grey coveralls stays entirely possible.

Because a thin theme would otherwise drown in that neutral pool, its own
bullets are duplicated until they hold `THEME_SHARE` (0.6) of the pool. The
multiplier is computed per table from the real pool sizes, so it self-corrects
as content is authored.

**Theme is independent of Role.** A pirate is as likely to look neosamurai as
cyberpunk — that independence is a requirement, not an oversight. Role still
governs whether they are uniformed and what they carry; the two compose, so a
soldier rolled neosamurai gets that theme's *uniformed* bullets.

Pin a whole group to one look with `--set-trait Theme=neosamurai`.
```

- [ ] **Step 2: Note the test suite in the README**

In `README.md`, add after the `generate-npc.py` section:

```markdown
### Tests

Standard library `unittest`, no dependencies:

```
python -m unittest discover test
```

Tests load the generator by path (its hyphen makes it non-importable) and roll
against `test/fixtures/tables-minimal.md` rather than the live tables, so
authoring a bullet never breaks a test.
```

- [ ] **Step 3: Verify both commands in the docs actually run**

Run:

```bash
python -m unittest discover test
python generate-npc.py --dry-run --count 3 --set-trait Theme=neosamurai
```

Expected: tests pass; the dry run reports 9 jobs would be queued and does not
error on the forced theme.

- [ ] **Step 4: Commit**

```bash
git add docs/generate-npc.md README.md
git commit -m "docs: document the Theme axis and the new test suite"
```

---

## Phase 1 done when

- `python -m unittest discover test` passes.
- Both theme filters are proven no-ops against the live tables (Task 7), so the
  mechanism is inert until content is tagged.
- Every NPC rolls a Theme, no NPC can carry a foreign theme's bullet, and Theme
  is statistically independent of Role (Task 6).
- `--set-trait Theme=<name>` pins a group to one look.
- No bullet in `npc-generator-tables.md` carries an `@` tag yet — that is
  Phase 4, and `test/test_theme_inert.py` must be deleted when it starts.

**Expected behaviour change:** a given `--seed` now rolls a different NPC than
it did before this phase, because the Theme draw shifts the random stream. This
is normal for any added table and is not a regression — reproducibility is
scoped to a seed *plus an unchanged tables file*.
