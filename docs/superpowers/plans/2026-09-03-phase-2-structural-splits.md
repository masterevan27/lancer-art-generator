# Phase 2: Structural Splits Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split `Gear` into equipment + armament and `Hair` into cut + colour, so an NPC can carry both a tool and a weapon, the theme gates the weapon, and hair colour varies independently of cut — without pushing more prompts past Krea's 512-token ceiling.

**Architecture:** Two table splits, each landing content-first then code. `Weapon` is carved out of `Gear` mechanically by the existing `weapon` flag and rolls *before* Gear so Gear yields the hands. `Hair colour` is a three-segment table whose base fills a `{colour}` slot inside each cut bullet and whose optional tail is appended after it. Both splits are gated behind a prompt-budget fix, because the token prompt already truncates on 5.4% of rolls before this phase adds anything.

**Tech Stack:** Python 3, standard library only — no `pip`, no dependencies. Tests use `unittest`.

**Spec:** `docs/superpowers/specs/2026-09-03-phase-2-structural-splits-design.md`
(Parent: `docs/superpowers/specs/2026-09-03-themed-npc-generation-design.md`, three of whose statements the Phase 2 spec supersedes — see its §0.)

## Global Constraints

- **Standard library only.** No `pip install`, no `requirements.txt`. Applies to tests too.
- **Never filter a pool to nothing.** Every filter in `roll_npc()` ends `return filtered or options`. New filters must too.
- **Flags are matched literally**; an unrecognised flag is ignored rather than reported.
- **`THEME_SHARE = 0.6`** and `TOKEN_LIMIT = 512` are unchanged by this phase.
- **`split_flags()` keeps returning a 2-tuple**; every existing caller keeps working untouched.
- **Do not reorder `REQUIRED_TABLES`** beyond the two insertions this plan specifies.
- **`Weapon` is themed; `Gear` is not.** After Task 4, `THEMED_TABLES` contains `Weapon` and does not contain `Gear`.
- **Windows/Git Bash, Python 3.13.** Run `python`, never `python3`.
- The suite stands at **51 passing tests** before Task 1. It must never go red at a task boundary except where a task explicitly says so (Task 1 ships a deliberately failing test that Task 2 fixes).
- House style: `%`-formatting rather than f-strings; comments and docstrings explain *why*; `—` em-dashes in prose.

---

### Task 1: Prompt-budget instrument and its regression test

The token prompt already truncates on ~5.4% of rolls. This task measures that, and ships the test that Task 2 has to make pass. **This is the one task in the plan that ends with a failing test on purpose.**

**Files:**
- Create: `test/prompt_budget.py`
- Create: `test/test_prompt_budget.py`

**Interfaces:**
- Consumes: `test.helpers.load_generator`, `test.helpers.REPO`.
- Produces: `test.prompt_budget.measure(tables, count=1500, seed=0) -> {"portrait": [int], "token": [int]}`, `test.prompt_budget.percentile(values, q) -> int`.

- [ ] **Step 1: Write the instrument**

Create `test/prompt_budget.py`:

```python
"""Measure generated prompt length against Krea 2's token ceiling.

Not a test, and deliberately not named test_*: the number it reports is a
property of the content, and the content changes every time a bullet is
authored. It is the instrument the budget test reads, and a report you can run
by hand when a long bullet lands.

    python -m test.prompt_budget
    python -m test.prompt_budget --count 5000
"""
import argparse
import contextlib
import io
import random
import sys
from pathlib import Path

from test.helpers import REPO, load_generator

LIVE_TABLES = REPO / "prompts" / "npc-generator-tables.md"


def measure(tables, count=1500, seed=0):
    """Estimated token counts for both prompts over `count` rolled NPCs.

    build_prompts() writes an over-limit warning to stderr per prompt, which
    would bury a test run in noise, so it is swallowed here - the counts this
    returns are what callers judge, not the warnings.
    """
    gen = load_generator()
    out = {"portrait": [], "token": []}
    with contextlib.redirect_stderr(io.StringIO()):
        for n in range(count):
            npc = gen.roll_npc(tables, random.Random(seed + n))
            portrait, token = gen.build_prompts(npc)
            out["portrait"].append(gen.estimate_tokens(portrait))
            out["token"].append(gen.estimate_tokens(token))
    return out


def percentile(values, q):
    """The q-th percentile (0-100) by nearest rank, on a copy."""
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(len(ordered) * q / 100.0))
    return ordered[idx]


def main(argv=None):
    p = argparse.ArgumentParser(description="Measure prompt length vs TOKEN_LIMIT.")
    p.add_argument("--tables", type=Path, default=LIVE_TABLES)
    p.add_argument("--count", type=int, default=1500)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args(argv)

    gen = load_generator()
    tables = gen.parse_tables(args.tables)
    results = measure(tables, count=args.count, seed=args.seed)
    print("%s   %d rolls   limit %d\n" % (args.tables, args.count, gen.TOKEN_LIMIT))
    for name, values in results.items():
        over = sum(1 for v in values if v > gen.TOKEN_LIMIT)
        print("%-9s mean %4d  p50 %4d  p90 %4d  p99 %4d  max %4d   over: %5.1f%%" % (
            name, sum(values) // len(values), percentile(values, 50),
            percentile(values, 90), percentile(values, 99), max(values),
            100.0 * over / len(values)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run the instrument to see the baseline**

Run: `python -m test.prompt_budget --count 1500`

Expected: the `token` row shows roughly `p99 530  max 536  over: 5.4%`, and the
`portrait` row roughly `p99 497  over: 0.7%`. The exact figures shift as content
is authored; what matters is that `token` is over the limit and `portrait` is
close to clean.

**Record the numbers you actually get in your report** — Task 2 is judged
against them.

- [ ] **Step 3: Write the regression test**

Create `test/test_prompt_budget.py`:

```python
"""No rolled NPC may lose its prompt tail to Krea 2's token ceiling.

A truncated prompt loses whatever comes last, which in both templates is the
palette instruction, the flat-white background rule and the closing style tags
- the parts that make a token cut out cleanly. That makes over-limit prompts a
silent quality bug rather than a loud failure, which is why it gets a test.

The p99 rather than the max: one pathological bullet combination should be
fixed by shortening that bullet, not by holding the whole suite red. The max is
reported in the failure message so it is visible either way.
"""
import unittest

from test.helpers import REPO, load_generator
from test.prompt_budget import measure, percentile

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")
RESULTS = measure(LIVE, count=1500, seed=0)


class TestPromptBudget(unittest.TestCase):
    def test_p99_is_under_the_token_limit(self):
        for name, values in RESULTS.items():
            with self.subTest(prompt=name):
                p99 = percentile(values, 99)
                self.assertLess(
                    p99, gen.TOKEN_LIMIT,
                    "%s prompt p99 is %d against a limit of %d (max %d, %.1f%% "
                    "of rolls over) - the tail is being truncated"
                    % (name, p99, gen.TOKEN_LIMIT, max(values),
                       100.0 * sum(1 for v in values if v > gen.TOKEN_LIMIT)
                       / len(values)))

    def test_the_measurement_is_not_vacuous(self):
        """A silently empty sample would make the check above pass on nothing."""
        self.assertEqual(len(RESULTS["token"]), 1500)
        self.assertGreater(min(RESULTS["token"]), 200)
```

- [ ] **Step 4: Run it and confirm it fails on the token prompt**

Run: `python -m unittest test.test_prompt_budget -v`

Expected: `test_p99_is_under_the_token_limit` **FAILS** on the `token` subtest
with a message naming a p99 around 530. The `portrait` subtest passes, and
`test_the_measurement_is_not_vacuous` passes.

**This failure is the point of the task.** It is the RED phase for Task 2. Do
not weaken the assertion, raise `TOKEN_LIMIT`, or skip the test to get a green
run.

- [ ] **Step 5: Commit**

```bash
git add test/prompt_budget.py test/test_prompt_budget.py
git commit -m "test: measure prompt length, and fail on the token prompt's overrun"
```

---

### Task 2: Trim the token template's repeated style language

Make Task 1's test pass. `TOKEN_TEMPLATE` is 262 tokens of fixed boilerplate against ~215 of rolled content, and it restates the painterly/grain/halftone style four separate times for ~75 tokens.

**This task has a human approval gate.** The restatements may be load-bearing — diffusion models often need a style repeated to hold it across a full-body figure, and these read like hard-won fixes rather than accidents. Token count is not the only criterion.

**Files:**
- Modify: `generate-npc.py` — `TOKEN_TEMPLATE` (around line 265)

**Interfaces:**
- Consumes: Task 1's `test/test_prompt_budget.py`.
- Produces: nothing new. `TOKEN_TEMPLATE` keeps every `{placeholder}` it has today — only literal prose changes.

- [ ] **Step 1: Locate the four restatements**

Run: `python -c "import importlib.util,sys;s=importlib.util.spec_from_file_location('g','generate-npc.py');m=importlib.util.module_from_spec(s);sys.modules['g']=m;s.loader.exec_module(m);print(m.TOKEN_TEMPLATE)"`

The four are:

1. `rendered in a detailed painterly illustration style with fine grain texture, clean linework and halftone dot shading worked into the shadows, moody cinematic lighting on the figure.`
2. `{Possessive} face carries the same fine grain and visible brushwork as a close-up portrait, not simplified or cel-shaded.`
3. `painterly brushwork with heavy grain and dense halftone screentone worked into every shadow`
4. `matching the same painterly rendering as the portrait shot.`

- [ ] **Step 2: Make the cut**

Keep **1** (the opening style assertion, which sets the render) and **3** (the
closing tag block, which is standard for this kind of prompt). Drop **2** and
**4**.

Rationale to preserve in a comment: 2 and 4 both exist to stop the token
drifting from the portrait's rendering, and 3 already says the same thing in
the position that matters. 1 and 3 bracket the prompt, which is where a
diffusion model weights style most heavily.

Replace `{Possessive} face carries the same fine grain and visible brushwork as a close-up portrait, not simplified or cel-shaded. ` with nothing, and `, matching the same painterly rendering as the portrait shot` with nothing.

Add above `TOKEN_TEMPLATE`:

```python
# The painterly style is asserted twice - once opening, once closing - and not
# four times. Two further restatements used to sit in the middle ("the same
# fine grain and visible brushwork as a close-up portrait", "matching the same
# painterly rendering as the portrait shot"); both existed to stop the token
# drifting from the portrait's look, and the closing tag block already says
# that in the position a diffusion model weights hardest. Removing them bought
# back the headroom the Weapon slot needed - see
# docs/superpowers/specs/2026-09-03-phase-2-structural-splits-design.md §4.
```

- [ ] **Step 3: Measure the recovery**

Run: `python -m test.prompt_budget --count 1500`

Expected: the `token` row's `over:` figure drops to **0.0%** or close to it, and
its p99 lands comfortably under 512. Compare against the numbers you recorded
in Task 1 and state the delta in your report.

If the trim recovers less than ~25 tokens, say so and stop — the plan's later
tasks assume this headroom exists, and a short recovery is a finding for the
controller, not something to paper over by cutting more prose on your own
judgement.

- [ ] **Step 4: Run the budget test**

Run: `python -m unittest test.test_prompt_budget -v`

Expected: **PASS**, both subtests.

- [ ] **Step 5: Run the whole suite**

Run: `python -m unittest discover test`

Expected: PASS, 53 tests (51 existing + 2 from Task 1).

- [ ] **Step 6: Generate a render comparison for the human gate**

Run:

```bash
python generate-npc.py --dry-run --count 3 --seed 1234
```

Put the three token prompts in your report **in full**. The controller needs
them to judge whether the trimmed prompt still reads as the same style before
this is rendered for real.

**Report `DONE_WITH_CONCERNS`** and say explicitly that the trim is a rendering
change awaiting an A/B on real renders. Do not describe it as verified — the
tests prove the token count, not the image.

- [ ] **Step 7: Commit**

```bash
git add generate-npc.py
git commit -m "perf: assert the painterly style twice, not four times"
```

---

### Task 3: Carve the Weapon table out of Gear

Content only — no code. The split is driven entirely by the existing `weapon` flag, so no bullet needs classifying by hand.

**Files:**
- Modify: `prompts/npc-generator-tables.md`

**Interfaces:**
- Consumes: nothing.
- Produces: a `## Weapon` table `parse_tables()` will pick up. Nothing reads it until Task 4.

- [ ] **Step 1: Confirm the split boundary before moving anything**

Run:

```bash
python -c "
import importlib.util,sys,pathlib
s=importlib.util.spec_from_file_location('g','generate-npc.py');m=importlib.util.module_from_spec(s);sys.modules['g']=m;s.loader.exec_module(m)
t=m.parse_tables(pathlib.Path('prompts/npc-generator-tables.md'))
g=t['Gear']; w=[b for b in g if 'weapon' in m.split_flags(b)[1]]
print('weighted %d  weapon %d  equipment %d' % (len(g), len(w), len(g)-len(w)))
"
```

Expected: `weighted 89  weapon 56  equipment 33`. If those numbers differ,
content has been authored since this plan was written — proceed anyway, but
report the actual figures.

- [ ] **Step 2: Move every `weapon`-flagged bullet into a new `## Weapon` section**

Insert `## Weapon` immediately **before** `## Gear` in the file, so the file's
order mirrors the roll order Task 4 establishes. Move each bullet carrying the
`weapon` flag out of `## Gear` and into it, text and flags unchanged.

Do not reword any bullet. Do not drop the `mil`, `hands`, `gun`, `simple` or
`sidearm` flags — they travel with the bullet.

- [ ] **Step 3: Add the weighted empty entry**

As the first bullet of `## Weapon`:

```markdown
- x30 || none
```

- [ ] **Step 4: Write the section comment**

Above the bullets in `## Weapon`:

```markdown
<!--
  What the NPC is armed with, rolled separately from Gear so a mechanic can
  carry a tool bag AND a holstered sidearm - one combined roll could only ever
  yield one of the two.

  A weapon is the most theme-defining object a figure carries, which is why
  this table is theme-gated and Gear is not: one undifferentiated pool is why
  every theme's armament used to land on everyone.

  The 'x30 || none' entry is an empty bullet, the same trick '## Weather' uses
  for its 'clear' entry. It keeps an unarmed NPC the common case, and it keeps
  the average prompt short, since most NPCs then render no weapon phrase at
  all. Its weight is the dial for how armed the setting feels - raise it for a
  quieter one. A 'mil' Role never reaches it: apply_weapon_policy() restricts
  that pool to 'sidearm'-flagged bullets, which this is not.

  Flags here: 'weapon' (an actual weapon), 'simple' (small and pocketable),
  'sidearm' (includes a holstered or openly worn pistol - the guaranteed-armed
  baseline for a mil Role), 'gun' (an actual firearm held in hand), 'hands'
  (occupies at least one hand), 'mil' (military-issue).
-->
```

- [ ] **Step 5: Update the `## Gear` comment**

`## Gear` is now equipment only. Amend its existing comment to say so, and to
point at `## Weapon` for armament. Remove any sentence claiming Gear holds
weapons.

- [ ] **Step 6: Verify both tables parse**

Run:

```bash
python -c "
import importlib.util,sys,pathlib
s=importlib.util.spec_from_file_location('g','generate-npc.py');m=importlib.util.module_from_spec(s);sys.modules['g']=m;s.loader.exec_module(m)
t=m.parse_tables(pathlib.Path('prompts/npc-generator-tables.md'))
print('Gear', len(t['Gear']), 'Weapon', len(t['Weapon']))
print('weapon-flagged left in Gear:', [b for b in t['Gear'] if 'weapon' in m.split_flags(b)[1]])
print('empty Weapon entries:', sum(1 for b in t['Weapon'] if not m.split_flags(b)[0]))
"
```

Expected: `Gear 33  Weapon 86` (56 armament + 30 weighted empties), an **empty
list** of weapon-flagged leftovers, and `30` empty entries.

- [ ] **Step 7: Confirm the generator still runs unchanged**

Run: `python -m unittest discover test` and `python generate-npc.py --dry-run --count 2`

Expected: 53 tests pass and the dry run works. `Weapon` is not in
`REQUIRED_TABLES` yet, so it is inert new content — `## Gear` shrinking to
equipment is the only behaviour change, and it means no NPC rolls a weapon
until Task 4. That is expected and temporary.

- [ ] **Step 8: Commit**

```bash
git add prompts/npc-generator-tables.md
git commit -m "content: split armament out of Gear into its own Weapon table"
```

---

### Task 4: Roll the Weapon

**Files:**
- Modify: `generate-npc.py` — `REQUIRED_TABLES` (~line 106), `THEMED_TABLES` (~line 123), `GEAR_POLICY` (~line 212), `apply_gear_policy()` (~line 455), `roll_npc()` (~line 516), `build_prompts()` (~line 835), `write_dossier()` (~line 894)
- Modify: `test/fixtures/tables-minimal.md`, `test/fixtures/tables-themed.md`
- Create: `test/test_weapon.py`

**Interfaces:**
- Consumes: the `## Weapon` table from Task 3.
- Produces: `WEAPON_POLICY: dict`, `apply_weapon_policy(options, category, mil) -> list[str]`; `roll_npc()` returns a dict with a `"Weapon"` key.

- [ ] **Step 1: Add `## Weapon` to both fixtures**

Both fixtures must carry every `REQUIRED_TABLES` entry or every existing test
breaks. Add to `test/fixtures/tables-minimal.md`:

```markdown
## Weapon
- x2 || none
- a service pistol worn openly at the thigh || mil weapon simple sidearm
- a long blade worn edge-up at the waist || mil weapon sidearm hands @alpha
```

Add to `test/fixtures/tables-themed.md`, keeping its proportioned shape:

```markdown
## Weapon
- x8 || none
- a service pistol worn openly at the thigh || mil weapon simple sidearm
- a holstered sidearm and a slung carbine || mil weapon sidearm
- a compact sidearm at the chest rig || mil weapon simple sidearm
- a marked ejection-seat sidearm holstered at the ribs || mil weapon simple sidearm @gundam
- a squadron-issue carbine held at a low ready in both hands || mil weapon sidearm hands gun @gundam
- a long single-edged blade worn edge-up at the waist || mil weapon sidearm @neosamurai
- a short companion blade at the small of the back || mil weapon simple sidearm @neosamurai
- a taped-together slug pistol shoved in the belt || mil weapon simple sidearm @scav
```

Then remove the `weapon`-flagged bullets from each fixture's `## Gear`, leaving
equipment only. In `tables-minimal.md` that means deleting the
`a service pistol worn openly at the thigh || mil weapon simple sidearm @alpha`
line; in `tables-themed.md` it means deleting the four `weapon`-flagged Gear
bullets.

- [ ] **Step 2: Write the failing test**

Create `test/test_weapon.py`:

```python
"""The Weapon roll: every NPC gets one, and a mil Role is never unarmed."""
import random
import unittest

from test.helpers import FIXTURE_TABLES, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)


def roll(seed, **overrides):
    return gen.roll_npc(TABLES, random.Random(seed), overrides or None)


class TestWeaponRoll(unittest.TestCase):
    def test_every_npc_has_a_weapon_key(self):
        for seed in range(50):
            self.assertIn("Weapon", roll(seed))

    def test_an_unarmed_npc_is_possible(self):
        """The weighted empty entry has to be reachable."""
        self.assertTrue(
            any(roll(s)["Weapon"] == "" for s in range(100)),
            "no roll in 100 came up unarmed - the empty entry is unreachable")

    def test_a_mil_role_is_never_unarmed(self):
        """apply_weapon_policy restricts a mil pool to 'sidearm' bullets.

        The empty entry is not one, so the guarantee gets stronger after the
        split rather than weaker - this pins that.
        """
        mil = "a Union marine soldier || mil"
        for seed in range(100):
            npc = roll(seed, Role=mil)
            self.assertNotEqual(
                npc["Weapon"], "",
                "seed %d: a mil Role rolled unarmed" % seed)

    def test_the_weapon_keeps_no_flag_segment(self):
        for seed in range(100):
            self.assertNotIn("||", roll(seed)["Weapon"])

    def test_weapon_is_themed_and_gear_is_not(self):
        self.assertIn("Weapon", gen.THEMED_TABLES)
        self.assertNotIn("Gear", gen.THEMED_TABLES)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run it to verify it fails**

Run: `python -m unittest test.test_weapon -v`

Expected: FAIL with `KeyError: 'Weapon'`.

- [ ] **Step 4: Add `Weapon` to `REQUIRED_TABLES` and `THEMED_TABLES`**

In `REQUIRED_TABLES`, insert `"Weapon"` immediately **before** `"Gear"`:

```python
REQUIRED_TABLES = [
    "Given names", "Family names", "Callsigns", "Pronouns", "Theme", "Age",
    "Build", "Height", "Skin", "Hair", "Eyes", "Feature", "Demeanor", "Role",
    "Faction", "Outfit", "Headgear", "Weapon", "Gear", "Accent", "Backdrop",
    "Weather", "Stance",
]
```

Change `THEMED_TABLES` to swap `Gear` for `Weapon`, and replace its trailing
Phase 2 note (which this task resolves) with the settled statement:

```python
# The tables a rolled Theme gates. Everything else - names, age, build, height,
# skin, eyes, accent, weather, stance - describes the person or the moment
# rather than the visual world they come from, and stays untouched by theme.
# Gear is deliberately absent: what is left of it after the Weapon split is
# data-slates, tool bags and thermoses, which no theme owns. Weapon is here
# because armament is the most theme-defining object a figure carries.
# Phase 2 adds "Hair colour" when that table exists.
THEMED_TABLES = ("Hair", "Feature", "Outfit", "Headgear", "Weapon", "Backdrop")
```

- [ ] **Step 5: Rename the gear policy to the weapon policy**

Rename `GEAR_POLICY` to `WEAPON_POLICY` and `apply_gear_policy()` to
`apply_weapon_policy()`. The bodies are unchanged — only the names, the
docstring's references to "Gear", and the call site move.

Update the docstring's opening line to read `Bias or filter the Weapon roll to
fit the NPC's Role.` and its closing paragraph to say `Any other category - or
a tables file with no 'weapon'/'sidearm' flags at all - rolls Weapon exactly as
before: untouched.`

- [ ] **Step 6: Wire the roll**

In `roll_npc()`, the block that currently reads:

```python
        if name == "Gear" and outfit_notac:
            no_mil = [x for x in options if "mil" not in split_flags(x)[1]]
            options = no_mil or options
        if name == "Gear":
            options = apply_gear_policy(options, ROLE_CATEGORIES.get(npc["Role"]), role_mil)
```

becomes:

```python
        # 'notac' applies to both halves of the old Gear table: an elaborate or
        # traditional outfit should pair with neither a military-issue rifle
        # nor a military-issue radio. Restricting only the Weapon would leave a
        # kimono carrying a tactical assault pack.
        if name in ("Weapon", "Gear") and outfit_notac:
            no_mil = [x for x in options if "mil" not in split_flags(x)[1]]
            options = no_mil or options
        if name == "Weapon":
            options = apply_weapon_policy(
                options, ROLE_CATEGORIES.get(npc["Role"]), role_mil)
```

- [ ] **Step 7: Strip the Weapon's flags and expose it downstream**

`npc["Gear"], gear_flags = split_flags(npc["Gear"])` sits just above the Stance
block. Add the Weapon beside it, keeping its flags for Task 5:

```python
    npc["Weapon"], weapon_flags = split_flags(npc["Weapon"])
    npc["Gear"], gear_flags = split_flags(npc["Gear"])
```

Add `"Weapon"` to the post-override re-strip list alongside the others, so a
forced `--set-trait Weapon=` cannot smuggle its flags back in:

```python
    npc["Weapon"] = split_flags(npc["Weapon"])[0]
```

- [ ] **Step 8: Teach `has_light_source` about the Weapon**

In `build_prompts()`, change:

```python
    equipped_glow = has_light_source(
        npc["Gear"], npc["Outfit"], npc["Headgear"], npc["Feature"], npc["Eyes"])
```

to include the Weapon — a glowing energy blade is exactly the source this
function exists to catch:

```python
    equipped_glow = has_light_source(
        npc["Weapon"], npc["Gear"], npc["Outfit"], npc["Headgear"],
        npc["Feature"], npc["Eyes"])
```

Also add `"weapon": npc["Weapon"],` to the `fields` dict beside `"gear"`.

- [ ] **Step 9: Add the dossier row**

In `write_dossier()`, immediately after the `("Carrying", npc["Gear"])` entry:

```python
        ("Armed with", npc.get("Weapon", "-") or "unarmed"),
```

`.get` for the same reason the Theme row uses it — a manifest entry written
before this change still writes a dossier. `or "unarmed"` because the empty
entry would otherwise render a blank table cell.

- [ ] **Step 10: Run the test**

Run: `python -m unittest test.test_weapon -v`

Expected: PASS, 5 tests.

- [ ] **Step 11: Run the whole suite**

Run: `python -m unittest discover test`

Expected: PASS, 58 tests.

**If `test_prompt_budget` fails here,** the Weapon slot has eaten Task 2's
headroom. Report it — do not adjust the budget test.

- [ ] **Step 12: Commit**

```bash
git add generate-npc.py test/test_weapon.py test/fixtures/tables-minimal.md test/fixtures/tables-themed.md
git commit -m "feat: roll a Weapon separately from Gear, and theme-gate it"
```

---

### Task 5: Gear yields the hands to the Weapon

Both tables can occupy hands — 29 of 56 armament bullets and 14 of 33 equipment bullets carry `hands`. Rolled independently that is roughly one NPC in five holding an impossibility.

**Files:**
- Modify: `generate-npc.py` — `roll_npc()`
- Create: `test/test_hands.py`

**Interfaces:**
- Consumes: `Weapon` from Task 4.
- Produces: nothing new. `Weapon` precedes `Gear` in `REQUIRED_TABLES`, so `weapon_hands` is known when Gear is rolled.

- [ ] **Step 1: Write the failing test**

Create `test/test_hands.py`:

```python
"""No NPC holds more things than they have hands.

Weapon and Gear roll independently and both can carry the 'hands' flag, so
without a filter an NPC can end up with a parasol in one hand and a katana
raised in both. Weapon is rolled first and Gear yields, because the weapon is
the more theme-defining object.
"""
import random
import unittest

from test.helpers import FIXTURE_TABLES, bullets_for, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)


def roll(seed, **overrides):
    return gen.roll_npc(TABLES, random.Random(seed), overrides or None)


def texts_with_hands(name):
    """Flag-stripped texts of `name`'s bullets that occupy a hand."""
    return {gen.split_flags(b)[0] for b in bullets_for(TABLES, name)
            if "hands" in gen.split_flags(b)[1]}


class TestHands(unittest.TestCase):
    def test_weapon_and_gear_never_both_occupy_hands(self):
        armed = texts_with_hands("Weapon")
        held = texts_with_hands("Gear")
        for seed in range(300):
            npc = roll(seed)
            self.assertFalse(
                npc["Weapon"] in armed and npc["Gear"] in held,
                "seed %d: %r and %r both need hands"
                % (seed, npc["Weapon"], npc["Gear"]))

    def test_the_check_can_actually_fail(self):
        """Both pools must really carry hands bullets, or the test is vacuous."""
        self.assertTrue(texts_with_hands("Weapon"), "fixture Weapon has no hands bullet")
        self.assertTrue(texts_with_hands("Gear"), "fixture Gear has no hands bullet")

    def test_gear_is_what_yields(self):
        """Forcing a two-handed weapon must not empty the Gear pool."""
        two_handed = next(
            b for b in bullets_for(TABLES, "Weapon")
            if "hands" in gen.split_flags(b)[1])
        for seed in range(50):
            npc = roll(seed, Weapon=two_handed)
            self.assertEqual(npc["Weapon"], gen.split_flags(two_handed)[0])
            self.assertTrue(npc["Gear"], "Gear pool starved by a forced weapon")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m unittest test.test_hands -v`

Expected: `test_weapon_and_gear_never_both_occupy_hands` **FAILS**, naming a
seed and the two colliding items. The other two pass.

- [ ] **Step 3: Track the Weapon's hands flag before the loop**

In `roll_npc()`, beside the other pre-loop state (`young`, `role_mil`,
`outfit_notac`), add:

```python
    weapon_hands = False
```

- [ ] **Step 4: Record it when the Weapon is rolled**

The block that unpacks flags by table name currently reads
`if name in ("Age", "Build", "Role", "Faction", "Outfit", "Hair", "Feature", "Headgear"):`.
Add `"Weapon"` to that tuple, and inside it record the flag:

```python
            if name == "Weapon":
                weapon_hands = "hands" in flags
```

- [ ] **Step 5: Filter the Gear pool**

Immediately before the `notac` block added in Task 4:

```python
        # A weapon that occupies the hands rules out equipment that also needs
        # one. Weapon precedes Gear in REQUIRED_TABLES so this flag is already
        # known, the same way Role precedes Faction and Outfit. Gear is what
        # yields: the weapon is the more theme-defining object, and dropping a
        # thermos costs nothing.
        if name == "Gear" and weapon_hands:
            free = [x for x in options if "hands" not in split_flags(x)[1]]
            options = free or options      # never filter the pool down to nothing
```

- [ ] **Step 6: Fix the Stance filter, which is now reading the wrong table**

**This is a regression Task 3 introduced and nothing has caught yet.** The
Stance filter reads `gear_flags` alone:

```python
    npc["Gear"], gear_flags = split_flags(npc["Gear"])
    stances = [split_flags(x) for x in variant_table(tables, "Stance", subject)]
    if "gun" not in gear_flags:
        ...
```

Every `gun`-flagged bullet moved to `Weapon` in Task 3, so `gear_flags` can
never contain `gun` again — which means the `unarmed` branch always fires and
**no NPC can ever roll a gun stance.** Silent and total.

Replace that block with one reading both tables:

```python
    # Stance is filtered against the combined flags of both carried tables.
    # Splitting Weapon out of Gear moved every 'gun' bullet with it, so reading
    # gear_flags alone would make gun poses permanently unreachable - and a
    # figure holding a rifle in both hands could still be posed with both hands
    # in their pockets, which is the pairing this filter exists to stop.
    carried_flags = weapon_flags + gear_flags
    stances = [split_flags(x) for x in variant_table(tables, "Stance", subject)]
    if "gun" not in carried_flags:
        unarmed = [x for x in stances if "gun" not in x[1]]
        stances = unarmed or stances       # never filter the pool down to nothing
    if "hands" in carried_flags:
        free = [x for x in stances if "hands" not in x[1]]
        stances = free or stances          # never filter the pool down to nothing
    npc["Stance"] = rng.choice(stances)[0]
```

`weapon_flags` is already in scope from Task 4's Step 7, which unpacks it
beside `gear_flags`.

- [ ] **Step 7: Add the Stance coverage to the test**

Append to `test/test_hands.py`:

```python
class TestStanceReadsBothTables(unittest.TestCase):
    """Stance is filtered against Weapon and Gear together, not Gear alone.

    Every 'gun' bullet lives in Weapon after the split, so a filter reading
    only gear_flags would make gun stances unreachable rather than merely
    mis-filtered - a silent, total loss.
    """

    def _stance_texts(self, flag):
        return {gen.split_flags(b)[0]
                for b in bullets_for(TABLES, "Stance")
                if flag in gen.split_flags(b)[1]}

    def test_a_gun_stance_is_still_reachable(self):
        gun_stances = self._stance_texts("gun")
        self.assertTrue(gun_stances, "fixture Stance has no 'gun' pose to reach")
        self.assertTrue(
            any(roll(s)["Stance"] in gun_stances for s in range(300)),
            "no roll in 300 reached a gun stance - the Stance filter is "
            "probably still reading gear_flags alone, and every 'gun' bullet "
            "now lives in Weapon")

    def test_a_gun_stance_needs_a_gun(self):
        gun_stances = self._stance_texts("gun")
        for seed in range(300):
            npc = roll(seed)
            if npc["Stance"] in gun_stances:
                self.assertTrue(
                    npc["Weapon"],
                    "seed %d: a gun pose with no weapon" % seed)

    def test_a_hands_free_stance_is_not_paired_with_full_hands(self):
        free_stances = {gen.split_flags(b)[0]
                        for b in bullets_for(TABLES, "Stance")
                        if "hands" in gen.split_flags(b)[1]}
        armed = texts_with_hands("Weapon")
        held = texts_with_hands("Gear")
        for seed in range(300):
            npc = roll(seed)
            if npc["Stance"] in free_stances:
                self.assertNotIn(npc["Weapon"], armed, "seed %d" % seed)
                self.assertNotIn(npc["Gear"], held, "seed %d" % seed)
```

The fixture needs a `gun`-flagged Stance bullet and a `gun`-flagged Weapon for
these to bite. `test/fixtures/tables-minimal.md` has neither today — add to its
`## Stance`:

```markdown
- {possessive} weapon raised and sighted down the barrel || hands gun
```

and confirm the `## Weapon` bullet added in Task 4 Step 1 carries `gun`; if it
does not, add `gun` to the `a long blade worn edge-up at the waist` line's
flags — a drawn blade counts as a handled weapon for this pairing.

- [ ] **Step 8: Run the test**

Run: `python -m unittest test.test_hands -v`

Expected: PASS, 6 tests. **Verify `test_a_gun_stance_is_still_reachable`
actually fails before Step 6's fix** — stash the fix, run it, confirm red,
restore. Report that check; without it the regression could be re-introduced
silently.

- [ ] **Step 9: Run the whole suite**

Run: `python -m unittest discover test`

Expected: PASS, 64 tests.

- [ ] **Step 10: Commit**

```bash
git add generate-npc.py test/test_hands.py test/fixtures/tables-minimal.md
git commit -m "fix: filter Stance against Weapon and Gear together"
```

---

### Task 6: Merge the carry sentence, and redefine `nogear`

One sentence covering both slots rather than two, because two would cost a second `{Subject} {carry}` on every armed NPC for no added clarity.

**Files:**
- Modify: `generate-npc.py` — `build_prompts()`, `roll_npc()`
- Create: `test/test_carry_sentence.py`

**Interfaces:**
- Consumes: `Weapon` (Task 4), `weapon_hands` (Task 5).
- Produces: `carry_sentence(fields, weapon, gear) -> str`.

- [ ] **Step 1: Write the failing test**

Create `test/test_carry_sentence.py`:

```python
"""The one sentence that renders both the Weapon and the Gear.

All four combinations are reachable in real rolls - the weighted empty Weapon
entry and the 'nogear' Backdrop both produce the no-weapon rows - so all four
are pinned here, including the spacing and punctuation an omitted slot invites.
"""
import unittest

from test.helpers import load_generator

gen = load_generator()

FIELDS = {"Subject": "She", "carry": "carries"}


class TestCarrySentence(unittest.TestCase):
    def test_both(self):
        self.assertEqual(
            gen.carry_sentence(FIELDS, "a katana", "a data-slate"),
            "She carries a katana and a data-slate. ")

    def test_weapon_only(self):
        self.assertEqual(
            gen.carry_sentence(FIELDS, "a katana", ""),
            "She carries a katana. ")

    def test_gear_only(self):
        self.assertEqual(
            gen.carry_sentence(FIELDS, "", "a data-slate"),
            "She carries a data-slate. ")

    def test_neither_renders_nothing(self):
        self.assertEqual(gen.carry_sentence(FIELDS, "", ""), "")

    def test_no_prompt_ever_shows_a_doubled_space_or_stray_and(self):
        import random
        from test.helpers import FIXTURE_TABLES
        tables = gen.parse_tables(FIXTURE_TABLES)
        for seed in range(200):
            npc = gen.roll_npc(tables, random.Random(seed))
            for text in gen.build_prompts(npc):
                self.assertNotIn("  ", text, "seed %d: doubled space" % seed)
                self.assertNotIn("carries  ", text)
                self.assertNotIn("carries and", text)
                self.assertNotIn(" . ", text, "seed %d: orphaned period" % seed)


class TestNogear(unittest.TestCase):
    """A 'nogear' backdrop already put a weapon in the subject's hands.

    Its two effects are deliberately asymmetric, so both are pinned: the
    portrait drops the weapon because the scene contradicts it, the token keeps
    it because the token has no scene at all - just flat white and a Stance.
    """

    def setUp(self):
        import random
        from test.helpers import FIXTURE_TABLES
        self.random = random
        self.tables = gen.parse_tables(FIXTURE_TABLES)
        self.nogear = next(
            b for b in self.tables["Backdrop"]
            if "nogear" in gen.split_backdrop(b)[2])

    def _roll(self, seed):
        return gen.roll_npc(self.tables, self.random.Random(seed),
                            {"Backdrop": self.nogear})

    def test_the_portrait_omits_an_armed_npcs_weapon(self):
        for seed in range(100):
            npc = self._roll(seed)
            if not npc["Weapon"]:
                continue
            portrait, _ = gen.build_prompts(npc)
            self.assertNotIn(
                npc["Weapon"], portrait,
                "seed %d: a nogear scene still named the weapon" % seed)

    def test_the_token_still_names_it(self):
        for seed in range(100):
            npc = self._roll(seed)
            if not npc["Weapon"]:
                continue
            _, token = gen.build_prompts(npc)
            self.assertIn(
                npc["Weapon"], token,
                "seed %d: the token dropped the weapon, but it has no scene "
                "to contradict it" % seed)
            return
        self.fail("no armed NPC in 100 rolls - the check asserted nothing")

    def test_no_hands_gear_survives_a_nogear_scene(self):
        held = {gen.split_flags(b)[0]
                for b in gen.variant_table(self.tables, "Gear", "she")
                if "hands" in gen.split_flags(b)[1]}
        self.assertTrue(held, "fixture Gear has no hands bullet")
        for seed in range(100):
            self.assertNotIn(
                self._roll(seed)["Gear"], held,
                "seed %d: a nogear scene left hands-occupying gear" % seed)


if __name__ == "__main__":
    unittest.main()
```

The fixture needs a `nogear` Backdrop bullet for this to bite.
`test/fixtures/tables-minimal.md` has none — add to its `## Backdrop`:

```markdown
- A character portrait || {Subject} {is_are} firing a sidearm down a corridor. || nogear
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m unittest test.test_carry_sentence -v`

Expected: FAIL with `AttributeError: module 'gennpc' has no attribute 'carry_sentence'`.

- [ ] **Step 3: Write the implementation**

In `generate-npc.py`, immediately above `build_prompts()`:

```python
def carry_sentence(fields, weapon, gear):
    """The single sentence naming whatever the NPC is holding.

    One sentence rather than two, because two would repeat "{Subject} {carry}"
    on every armed NPC for no added clarity - and the token prompt has no
    tokens to spare for it. Returns "" when there is nothing to say, so the
    template's slot collapses cleanly rather than leaving an orphaned period
    or a doubled space.

    Both slots are genuinely optional: the Weapon table's weighted empty entry
    produces an unarmed NPC, and a 'nogear' Backdrop suppresses the weapon on
    the portrait because the scene already put one in their hands.
    """
    carried = [x for x in (weapon, gear) if x]
    if not carried:
        return ""
    return "{Subject} {carry} %s. ".format(**fields) % " and ".join(carried)
```

- [ ] **Step 4: Use it in `build_prompts()`**

Replace:

```python
    carrying = "{Subject} {carry} {gear}. ".format(**fields)
```

with:

```python
    carrying = carry_sentence(fields, npc["Weapon"], npc["Gear"])
```

and replace the portrait's suppression so that `nogear` drops only the weapon,
keeping any equipment:

```python
    # 'nogear' means the backdrop scene already put a weapon in the subject's
    # hands, so naming another one would arm them twice. It suppresses the
    # weapon on the PORTRAIT only - the token has no backdrop at all, just flat
    # white and a rolled Stance, so nothing there contradicts the weapon. The
    # equipment survives either way; a slung tool bag does not fight the scene.
    portrait_carrying = (carry_sentence(fields, "", npc["Gear"])
                         if "nogear" in flags else carrying)

    portrait_fields = dict(
        fields, gear_line=portrait_carrying,
        accent_line=(ACCENT_PORTRAIT if portrait_glow else ACCENT_PORTRAIT_NONE).format(**fields))
    token_fields = dict(
        fields, gear_line=carrying,
        accent_line=(ACCENT_TOKEN if equipped_glow else ACCENT_TOKEN_NONE).format(**fields))
```

- [ ] **Step 5: Restrict Gear when the Backdrop is `nogear`**

A scene that occupies the subject's hands contradicts equipment held in one.
`Backdrop` is rolled *after* `Gear`, so this cannot be a pool filter in the
loop — instead, resolve it where Backdrop's flags are already known. In
`roll_npc()`, after the Stance block and before the `npc.update(overrides)`
line:

```python
    # A 'nogear' backdrop has the subject's hands full of whatever the scene
    # handed them, so a thermos held in one of them contradicts the picture.
    # Backdrop is rolled after Gear, so this re-rolls rather than filtering a
    # pool - the one place in this function that does, and only because the
    # dependency runs backwards.
    if "nogear" in split_backdrop(npc["Backdrop"])[2] and "hands" in gear_flags:
        free = [x for x in variant_table(tables, "Gear", subject)
                if "hands" not in split_flags(x)[1]]
        if free:
            npc["Gear"], gear_flags = split_flags(rng.choice(free))
```

- [ ] **Step 6: Run the test**

Run: `python -m unittest test.test_carry_sentence -v`

Expected: PASS, 8 tests.

- [ ] **Step 7: Run the whole suite and a dry run**

Run: `python -m unittest discover test` and `python generate-npc.py --dry-run --count 3`

Expected: 72 tests pass; the dry run shows a merged carry sentence.

- [ ] **Step 8: Commit**

```bash
git add generate-npc.py test/test_carry_sentence.py
git commit -m "feat: name the weapon and the gear in one sentence"
```

---

### Task 7: Split colour out of the Hair bullets

Content only — no code. This is the largest hand-edit in the plan: ~59 of 68 bullets across three tables.

**Files:**
- Modify: `prompts/npc-generator-tables.md`

**Interfaces:**
- Consumes: nothing.
- Produces: a `## Hair colour` table, and `## Hair` bullets carrying a `{colour}` slot. Nothing reads either until Task 8.

- [ ] **Step 1: Add the `## Hair colour` table**

Insert immediately after `## Hair`'s variant tables, before `## Eyes`:

```markdown
## Hair colour

<!--
  Rolled separately from the cut, so colour varies independently and a new
  shade is one bullet here rather than a rewrite of every cut.

  THREE segments, not two: 'base || tail || flags', the same shape ## Backdrop
  uses. The base fills the '{colour}' slot inside the rolled Hair bullet; the
  optional tail is appended after the whole cut phrase, separated by a comma.
  That is what makes gradients work - they read wrongly in adjective position
  ("a sleek silver-white fading to green at the tips bob") and correctly as a
  trailing clause ("a sleek silver-white bob cut level with the jaw, fading to
  green at the tips"). Flat colours leave the tail empty.

  A colour with flags but no tail writes its middle segment empty:
  'greying || || older'. Slightly awkward, and the price of one table.

  The 'older' flag drops that colour when the Age roll came up 'young',
  mirroring the 'figure'/'young' pairing exactly. Greying hair asserts an age,
  and rolling it onto a teenager contradicts the Age clause in the same prompt.
-->

- black
- dark brown
- ash-blonde
- auburn
- sandy blonde
- jet black
- chestnut
- mousy brown
- copper-red
- dark with a warm reddish cast
- greying || || older
- salt-and-pepper || || older
- sandy || going prematurely white at the temples || older
- two-tone || dark over a bleached pale underlayer
- silver-white || fading to green at the tips
```

Author roughly 35 entries in total, weighted so the plain naturalistic colours
dominate. Keep gradients to the handful that genuinely need a tail.

- [ ] **Step 2: Strip the colour out of each `## Hair` bullet and mark its slot**

Work through `## Hair`, `## Hair (she) +` and `## Hair (he) +` — 68 bullets.
For each one, remove the colour adjective and put `{colour}` where it stood:

```
- close-cropped black hair              ->  - close-cropped {colour} hair
- long dark hair pulled back in a       ->  - long {colour} hair pulled back in a
  practical braid                            practical braid
- silver-grey hair cut short and severe ->  - {colour} hair cut short and severe
- a sleek dark bob cut level with the   ->  - a sleek {colour} bob cut level with
  jaw                                        the jaw
- an untidy mop of curls                ->  - an untidy mop of {colour} curls
```

Rules:
- **Every** Hair bullet gets exactly one `{colour}`, including the ~9 that
  carry no colour today — otherwise those bullets would silently ignore the
  colour roll, which is the inconsistency the split exists to remove.
- Put the slot where it reads naturally for that bullet. Most take
  `{colour} hair` or `a {adjective} {colour} bob`.
- Bullets whose colour is inseparable from the cut ("a high ponytail in fiery
  orange-red fading to dark roots") get the colour moved wholly into
  `## Hair colour` as a gradient, and the cut keeps a plain `{colour}` slot.

- [ ] **Step 3: Verify every Hair bullet has exactly one slot**

Run:

```bash
python -c "
import importlib.util,sys,pathlib
s=importlib.util.spec_from_file_location('g','generate-npc.py');m=importlib.util.module_from_spec(s);sys.modules['g']=m;s.loader.exec_module(m)
t=m.parse_tables(pathlib.Path('prompts/npc-generator-tables.md'))
bad=[]
for k in [x for x in t if x=='Hair' or x.startswith('Hair (')]:
    for b in t[k]:
        if b.count('{colour}') != 1: bad.append((k,b))
print('bullets without exactly one {colour}:', len(bad))
for k,b in bad[:10]: print('  ', k, '|', b[:70])
print('Hair colour entries:', len(t['Hair colour']))
"
```

Expected: `bullets without exactly one {colour}: 0`, and a `Hair colour` count
around 35.

- [ ] **Step 4: Update the file header for the three-segment shape**

In `## How the script reads this file`, the paragraph listing which tables use
`||` says "Nine tables use it". Add `Hair colour` to that enumeration and note
that it, like `Backdrop`, uses **three** segments. Update the count.

- [ ] **Step 5: Confirm nothing breaks yet**

Run: `python -m unittest discover test` and `python generate-npc.py --dry-run --count 1`

Expected: **the dry run now FAILS**, with the placeholder error naming
`{colour}` — `roll_npc()` substitutes only pronoun fields and raises on
anything else. That is expected: Task 8 teaches it the new field. Record the
exact error in your report.

The test suite runs against the fixtures, which have no `{colour}` yet, so it
should still pass at 72.

- [ ] **Step 6: Commit**

```bash
git add prompts/npc-generator-tables.md
git commit -m "content: split colour out of the Hair bullets into its own table"
```

---

### Task 8: Roll the Hair colour

**Files:**
- Modify: `generate-npc.py` — `REQUIRED_TABLES`, `THEMED_TABLES`, `roll_npc()`, `write_dossier()`
- Modify: `test/fixtures/tables-minimal.md`, `test/fixtures/tables-themed.md`
- Create: `test/test_hair_colour.py`

**Interfaces:**
- Consumes: the `## Hair colour` table from Task 7.
- Produces: `split_hair_colour(bullet) -> (base, tail, flags)`; `roll_npc()` returns a dict with a `"Hair colour"` key, and its `"Hair"` value has the colour already substituted.

- [ ] **Step 1: Add `## Hair colour` to both fixtures and slots to their Hair bullets**

In `test/fixtures/tables-minimal.md`, change `## Hair` to:

```markdown
## Hair
- a short {colour} crop
- a long {colour} braid || @alpha
- a shaved head, {colour} at the stubble || @beta
```

and add:

```markdown
## Hair colour
- black
- greying || || older
- silver-white || fading to green at the tips || @alpha
```

Do the same for `test/fixtures/tables-themed.md`: insert `{colour}` into each
of its 24 Hair bullets and add a `## Hair colour` table of ~8 entries, at least
one with a tail and one flagged `older`.

- [ ] **Step 2: Write the failing test**

Create `test/test_hair_colour.py`:

```python
"""Hair colour rolls independently of cut and lands inside the cut phrase."""
import random
import unittest

from test.helpers import FIXTURE_TABLES, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)


def roll(seed, **overrides):
    return gen.roll_npc(TABLES, random.Random(seed), overrides or None)


class TestSplitHairColour(unittest.TestCase):
    def test_flat_colour_has_no_tail_and_no_flags(self):
        self.assertEqual(gen.split_hair_colour("black"), ("black", "", ()))

    def test_tail_is_the_second_segment(self):
        self.assertEqual(
            gen.split_hair_colour("silver-white || fading to green at the tips"),
            ("silver-white", "fading to green at the tips", ()))

    def test_flags_are_the_third_segment(self):
        self.assertEqual(
            gen.split_hair_colour("greying || || older"),
            ("greying", "", ("older",)))

    def test_tail_and_flags_together(self):
        self.assertEqual(
            gen.split_hair_colour("sandy || going white at the temples || older"),
            ("sandy", "going white at the temples", ("older",)))


class TestHairColourRoll(unittest.TestCase):
    def test_no_rolled_hair_keeps_an_unresolved_slot(self):
        """The guard on Task 7's 68-bullet hand-edit."""
        for seed in range(200):
            self.assertNotIn("{", roll(seed)["Hair"])

    def test_the_tail_is_appended_after_the_cut(self):
        npc = roll(0, **{"Hair": "a short {colour} crop",
                         "Hair colour": "silver-white || fading to green at the tips"})
        self.assertEqual(
            npc["Hair"], "a short silver-white crop, fading to green at the tips")

    def test_a_flat_colour_appends_nothing(self):
        npc = roll(0, **{"Hair": "a short {colour} crop", "Hair colour": "black"})
        self.assertEqual(npc["Hair"], "a short black crop")

    def test_older_never_lands_on_a_young_age(self):
        """Mirrors the figure/young pairing exactly."""
        older = {gen.split_hair_colour(b)[0] for b in TABLES["Hair colour"]
                 if "older" in gen.split_hair_colour(b)[2]}
        self.assertTrue(older, "fixture must carry an 'older' colour")
        for seed in range(300):
            npc = roll(seed)
            if npc["_young"]:
                self.assertNotIn(
                    npc["Hair colour"], older,
                    "seed %d: an 'older' colour landed on a young NPC" % seed)

    def test_hair_colour_is_themed(self):
        self.assertIn("Hair colour", gen.THEMED_TABLES)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run it to verify it fails**

Run: `python -m unittest test.test_hair_colour -v`

Expected: FAIL with `AttributeError: module 'gennpc' has no attribute 'split_hair_colour'`.

- [ ] **Step 4: Write the splitter**

In `generate-npc.py`, immediately after `split_backdrop()`:

```python
def split_hair_colour(bullet):
    """A Hair colour bullet carries the base, an optional tail, and flags.

    Three segments, the same shape split_backdrop() uses, and for the same
    reason: two of them are prose that reaches the prompt and the third is
    flags. The base fills the '{colour}' slot inside the rolled Hair bullet;
    the tail is appended after the whole cut phrase.

    That split exists because a gradient reads wrongly in adjective position -
    "a sleek silver-white fading to green at the tips bob" - and correctly as a
    trailing clause. A flat colour leaves the tail empty and reads inline.
    """
    parts = [p.strip() for p in bullet.split("||")]
    base = parts[0]
    tail = parts[1] if len(parts) > 1 else ""
    flags = tuple(f for f in parts[2].split() if f) if len(parts) > 2 else ()
    return base, tail, flags
```

- [ ] **Step 5: Teach `flags_for` the new shape**

`flags_for()` special-cases Backdrop. Add Hair colour beside it:

```python
def flags_for(name, bullet):
    """A bullet's flag tuple, whichever '||' shape its table uses.

    Backdrop and Hair colour both carry three segments and keep their flags in
    the third, so a two-segment bullet of either has no flags at all - its
    second segment is prose. Every other table keeps flags in the second
    segment. Reading the last segment blindly would mistake a Backdrop's scene
    or a Hair colour's tail for flags.
    """
    if name == "Backdrop":
        return split_backdrop(bullet)[2]
    if name == "Hair colour":
        return split_hair_colour(bullet)[2]
    return split_flags(bullet)[1]
```

- [ ] **Step 6: Add the table to the roll**

Insert `"Hair colour"` into `REQUIRED_TABLES` immediately after `"Hair"`, and
add it to `THEMED_TABLES`:

```python
THEMED_TABLES = ("Hair", "Hair colour", "Feature", "Outfit", "Headgear",
                 "Weapon", "Backdrop")
```

- [ ] **Step 7: Filter `older` against the Age roll**

In `roll_npc()`'s loop, beside the `Build`/`young` filter:

```python
        # An 'older' colour - greying, salt-and-pepper - asserts an age, so it
        # must not land on a teenager: the Age clause earlier in the same
        # prompt would contradict it. Age precedes Hair colour in
        # REQUIRED_TABLES, so the flag is already known. Same shape as the
        # Build/'figure' pairing above.
        if name == "Hair colour" and young:
            plain = [x for x in options if "older" not in flags_for(name, x)]
            options = plain or options     # never filter the pool down to nothing
```

- [ ] **Step 8: Substitute the colour into the Hair value**

After the loop, before the pronoun-placeholder pass, resolve the colour. Place
it immediately after the `npc["Weapon"] = split_flags(...)` re-strip block:

```python
    # Hair carries a '{colour}' slot rather than the template joining the two,
    # because the colour's position differs per bullet - "close-cropped
    # {colour} hair" against "a sleek {colour} bob cut level with the jaw" -
    # and no single join rule serves both. The tail goes after the whole cut
    # phrase, which is the only position a gradient reads correctly in.
    base, tail, _ = split_hair_colour(npc["Hair colour"])
    npc["Hair colour"] = base
    npc["Hair"] = npc["Hair"].replace("{colour}", base)
    if tail:
        npc["Hair"] = "%s, %s" % (npc["Hair"], tail)
```

This must run **before** the `for key, value in npc.items()` placeholder loop,
so that loop never sees an unresolved `{colour}` and raises on it.

- [ ] **Step 9: Add the dossier row**

In `write_dossier()`, the `("Hair", npc["Hair"])` row already carries the
resolved colour, so no new row is needed. Confirm this by reading the rendered
dossier in Step 11 rather than assuming it.

- [ ] **Step 10: Run the test**

Run: `python -m unittest test.test_hair_colour -v`

Expected: PASS, 9 tests.

- [ ] **Step 11: Run the whole suite and a real dry run**

Run: `python -m unittest discover test` and `python generate-npc.py --dry-run --count 3`

Expected: 81 tests pass. The dry run now works again — it failed at the end of
Task 7 — and every hair phrase reads naturally with its colour in place. Paste
three hair phrases into your report.

- [ ] **Step 12: Commit**

```bash
git add generate-npc.py test/test_hair_colour.py test/fixtures/tables-minimal.md test/fixtures/tables-themed.md
git commit -m "feat: roll hair colour independently of cut"
```

---

### Task 9: Documentation and the import skill

**Files:**
- Modify: `docs/generate-npc.md`
- Modify: `README.md`
- Modify: `.claude/skills/npc-trait-import/SKILL.md`

**Interfaces:**
- Consumes: everything above.
- Produces: nothing.

- [ ] **Step 1: Document both splits in the generator docs**

In `docs/generate-npc.md`, update the `## The roll tables` enumeration to name
`weapon` and `hair colour` in roll order, and add a section after `## Theme`:

```markdown
## Weapon and Gear

An NPC rolls **both**, so a mechanic can carry a tool bag *and* a holstered
sidearm — one combined roll could only ever yield one of the two.

`Weapon` is theme-gated and `Gear` is not. A weapon is the most theme-defining
object a figure carries, and one undifferentiated pool is why every theme's
armament used to land on everyone. What is left of `Gear` after the split is
data-slates, tool bags and thermoses, which no theme owns.

`Weapon` is rolled **first**, and `Gear` yields to it: a weapon that occupies
the hands drops the equipment that also needs one. Roughly a fifth of NPCs
would otherwise hold an impossibility — a parasol in one hand and a katana
raised in both.

The `Weapon` table's heavily weighted empty entry keeps an unarmed NPC the
common case. A `mil` Role never reaches it: `apply_weapon_policy` restricts
that pool to `sidearm`-flagged bullets, so the "always armed" guarantee is
stronger after the split than before it.
```

and a section on hair colour:

```markdown
## Hair colour

Cut and colour roll separately, so a new shade is one bullet rather than a
rewrite of every cut.

`Hair colour` is a **three-segment** table — `base || tail || flags` — like
`Backdrop`. The base fills a `{colour}` slot inside the rolled cut; the
optional tail is appended after the whole phrase. That is what lets gradients
work, since they read wrongly in adjective position and correctly as a
trailing clause:

    "a sleek {colour} bob cut level with the jaw"
      + "silver-white || fading to green at the tips"
      -> "a sleek silver-white bob cut level with the jaw, fading to green at the tips"

A colour flagged `older` — greying, salt-and-pepper — is dropped when the Age
roll came up `young`, mirroring the `figure`/`young` pairing exactly.
```

- [ ] **Step 2: Note the prompt budget in the README**

Add to the README's `### Tests` section, after the visibility paragraph:

```markdown
Prompt length is measured too, against Krea 2's 512-token ceiling — a prompt
that runs long silently loses its tail, which is where the palette and the
flat-white background instruction live:

```
python -m test.prompt_budget
```
```

- [ ] **Step 3: Update the import skill**

In `.claude/skills/npc-trait-import/SKILL.md`:

- Add `Weapon` and `Hair colour` to the flag table's tables column where
  relevant, and add an `older` row (`Hair colour` — an age-linked colour,
  dropped when Age is `young`).
- Update the `@<theme>` row's table list: `Weapon` is themed, `Gear` is **not**.
- Document the three-segment `Hair colour` shape and the `{colour}` slot,
  beside the existing pronoun-placeholder guidance.
- **Delete the "Flags the design specifies that do NOT exist yet" block's
  entries for `Weapon`, `Hair colour` and `older`** — they exist now. Leave the
  block itself, with `bulk`, `enclosed`, `sealed`, `vacuum` and the mech tiers,
  which are still Phase 3.
- Add to §7's validation list: every `Hair` bullet contains exactly one
  `{colour}`; every `Hair colour` bullet's flags are in the third segment.

- [ ] **Step 4: Verify every documented command runs**

Run:

```bash
python -m unittest discover test
python -m test.prompt_budget --count 500
python -m test.theme_visibility --count 200
python generate-npc.py --dry-run --count 3
```

Expected: 81 tests pass; both instruments print their grids; the dry run
reports 9 jobs. Paste all four outputs into your report.

- [ ] **Step 5: Commit**

```bash
git add docs/generate-npc.md README.md .claude/skills/npc-trait-import/SKILL.md
git commit -m "docs: document the Weapon and Hair colour splits"
```

---

## Phase 2 done when

- `python -m unittest discover test` passes at 81 tests.
- `python -m test.prompt_budget` reports **0.0% over** on both prompts — the
  token prompt's pre-existing 5.4% overrun is fixed, not merely held level.
- An NPC can roll equipment and armament together, and never holds two
  `hands` items.
- `Weapon` is in `THEMED_TABLES`; `Gear` is not.
- Hair colour rolls independently, gradients read correctly, and no `older`
  colour lands on a `young` Age.
- `python -m test.theme_visibility` shows a `Weapon` column — still at zero
  until Phase 4 tags content, which is correct.

**Expected behaviour change:** a given `--seed` rolls a different NPC than it
did before this phase, because two new draws shift the random stream. Normal
for any added table, and not a regression — reproducibility is scoped to a seed
*plus an unchanged tables file*.

**Carried into Phase 3, deliberately not fixed here:** the `apply_theme_share`
filter-ordering question (this phase supplies its measurement, not its answer),
and a theme authored with no `sidearm`-flagged Weapon silently degrading the
`mil`-Role armed guarantee — latent until content is tagged.
