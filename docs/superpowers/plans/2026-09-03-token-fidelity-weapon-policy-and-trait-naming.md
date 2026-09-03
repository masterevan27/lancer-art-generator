# Token Fidelity, Weapon Policy and Trait Naming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop the token prompt asserting things that are not true of the NPC it describes — a standing pose over a crouching one, a ledge under a figure destined for a transparent PNG, a weapon nobody carries — and rename two traits whose names now mislead.

**Architecture:** All changes land in `generate-npc.py` and `prompts/npc-generator-tables.md`. Three kinds of change: prompt-template edits that remove contradictory assertions, roll-table edits that remove content the token cannot show, and two trait renames (`Accent` → `Glow colour`, and `Faction` gaining a three-segment shape) that follow conventions the file already uses for `Backdrop` and `Hair colour`.

**Tech Stack:** Python 3 standard library only. `unittest` for tests, run via `python -m unittest discover -s test -t .` from the repo root. No third-party dependencies.

**Spec:** `docs/superpowers/specs/2026-09-03-token-fidelity-weapon-policy-and-trait-naming-design.md`

## Global Constraints

- **Token ceiling is 512.** `TOKEN_LIMIT = 512` in `generate-npc.py:140` is Krea 2's hard limit, not a preference. Never raise it and never relax `test/test_prompt_budget.py`. If a change pushes p99 over, shorten the content.
- **Measured baseline, before any change:** portrait p99 495 / max 540; token p99 **510** / max 537. Reproduce with `python -m test.prompt_budget`. The token prompt has two tokens of p99 headroom.
- **Test baseline:** 90 tests, all passing.
- **British spelling for new table headings**, matching the existing `Hair colour`. The trait is `Glow colour`, not `Glow color`.
- **Never filter a roll pool down to nothing.** Every filter in `roll_npc` and `apply_weapon_policy` ends `return filtered or options`. New filters follow that rule.
- **Weights are expanded at parse time.** `parse_tables` turns `x30 foo` into thirty copies in a flat list, so `options` is already weighted and `list * n` is the idiom for biasing.
- **Comments carry the reasoning.** This codebase documents *why* at each use site. Every change below specifies the comment to write; those comments are part of the deliverable, not optional decoration.
- Run the full suite (`python -m unittest discover -s test -t .`) before every commit, not just the new test.

---

### Task 1: Rename `Accent` to `Glow colour`

Mechanical, touches the most files, and blocks the companion GUI plan. Doing it first means every later task writes the new name once rather than renaming its own work.

**Files:**
- Modify: `generate-npc.py` — `REQUIRED_TABLES:118`, theme comment `:122`, the four `ACCENT_*` constants `:301-320`, `build_prompts`, `write_dossier`, `regenerate_one`
- Modify: `prompts/npc-generator-tables.md` — the `## Accent` heading and its comment
- Modify: `test/fixtures/tables-minimal.md` — the `## Accent` heading
- Modify: `test/test_theme_tag_placement.py`
- Create: `test/test_glow_rename.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `LEGACY_TRAIT_NAMES: dict[str, str]` and `migrate_traits(traits: dict) -> dict` at module level in `generate-npc.py`. The table key is `"Glow colour"`; the template slot is `{glow}`. Later tasks use `{glow}` and never `{accent}`.

- [ ] **Step 1: Write the failing test for the manifest compatibility shim**

Create `test/test_glow_rename.py`:

```python
"""The Accent -> Glow colour rename must not break stored manifest entries.

All 135 entries in .generated-npcs.json store the trait under 'Accent', and
--regen-manifest rebuilds an NPC from that stored dict rather than re-rolling.
A bare rename would raise KeyError in build_prompts() for every one of them.
"""
import unittest

from test.helpers import load_generator

gen = load_generator()


class TestLegacyTraitNames(unittest.TestCase):
    def test_a_stored_accent_becomes_a_glow_colour(self):
        migrated = gen.migrate_traits({"Accent": "amber", "Role": "a dockworker"})
        self.assertEqual(migrated["Glow colour"], "amber")
        self.assertNotIn("Accent", migrated)

    def test_an_entry_already_using_the_new_name_is_untouched(self):
        migrated = gen.migrate_traits({"Glow colour": "teal-green"})
        self.assertEqual(migrated["Glow colour"], "teal-green")

    def test_a_new_name_present_alongside_the_old_one_wins(self):
        """Belt and braces: never clobber a current value with a stale one."""
        migrated = gen.migrate_traits({"Accent": "amber", "Glow colour": "teal-green"})
        self.assertEqual(migrated["Glow colour"], "teal-green")

    def test_the_input_dict_is_not_mutated(self):
        original = {"Accent": "amber"}
        gen.migrate_traits(original)
        self.assertEqual(original, {"Accent": "amber"})

    def test_the_table_is_named_glow_colour_in_required_tables(self):
        self.assertIn("Glow colour", gen.REQUIRED_TABLES)
        self.assertNotIn("Accent", gen.REQUIRED_TABLES)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python -m unittest test.test_glow_rename -v`
Expected: FAIL — `AttributeError: module 'gennpc' has no attribute 'migrate_traits'`

- [ ] **Step 3: Add the migration function**

In `generate-npc.py`, immediately after the `WEAPON_POLICY` block (around line 239):

```python
# Trait names that have changed, old -> new. --regen-manifest rebuilds an NPC
# from a stored traits dict rather than re-rolling, so an entry written before
# a rename still carries the old key and would otherwise KeyError in
# build_prompts(). Same situation the npc.get("Weapon", "") and
# npc.get("Theme", "-") reads elsewhere in this file handle inline; factored
# out here because a rename is mechanical and a table of names is easier to
# extend than another scattered .get.
LEGACY_TRAIT_NAMES = {
    "Accent": "Glow colour",
}


def migrate_traits(traits):
    """A stored manifest trait dict brought forward to current table names."""
    out = dict(traits)
    for old, new in LEGACY_TRAIT_NAMES.items():
        if old in out:
            value = out.pop(old)
            out.setdefault(new, value)
    return out
```

- [ ] **Step 4: Run the test — the first four pass, the fifth still fails**

Run: `python -m unittest test.test_glow_rename -v`
Expected: four PASS, `test_the_table_is_named_glow_colour_in_required_tables` FAILs.

- [ ] **Step 5: Rename the table everywhere in the generator**

In `generate-npc.py`:

- `REQUIRED_TABLES` (line 118): `"Gear", "Accent", "Backdrop",` → `"Gear", "Glow colour", "Backdrop",`
- The theme comment at line 122-124 lists `accent` in its prose — change that word to `glow colour`.
- Rename the four constants and their slot. `ACCENT_PORTRAIT` → `GLOW_PORTRAIT`, `ACCENT_PORTRAIT_NONE` → `GLOW_NONE`, `ACCENT_TOKEN` → `GLOW_TOKEN`, `ACCENT_TOKEN_NONE` → delete (it is byte-identical to `ACCENT_PORTRAIT_NONE`; collapsing the duplicate is part of this rename). Inside them, `{accent}` → `{glow}`.
- In `build_prompts`: `"accent": npc["Accent"],` → `"glow": npc["Glow colour"],`, and the two `accent_line=` expressions use the renamed constants.
- The local `equipped_glow` / `portrait_glow` variables keep their names — they already read correctly.
- In `write_dossier`: `("Accent color", npc["Accent"])` → `("Glow colour", npc["Glow colour"])`.

Leave `has_light_source` untouched; its name is already right.

- [ ] **Step 6: Rename the heading in both tables files**

In `prompts/npc-generator-tables.md`, change `## Accent` to `## Glow colour` and update its comment to:

```
<!--
  The single saturated colour of the one light source in an otherwise
  restrained frame - not a design accent, which is what the old name implied.
  Only reached when something rolled for this NPC could actually cast it; see
  has_light_source() in generate-npc.py.
-->
```

In `test/fixtures/tables-minimal.md`, change `## Accent` to `## Glow colour`.

Also update the `Prompt templates` section further down the tables file. Every `{ACCENT_LINE}` / `{ACCENT}` in the reproduced templates becomes `{GLOW_LINE}` / `{GLOW}`. The prose beneath them names three constants by name — `ACCENT_PORTRAIT` → `GLOW_PORTRAIT`, `ACCENT_PORTRAIT_NONE` → `GLOW_NONE`, `ACCENT_TOKEN` → `GLOW_TOKEN` — and says `ACCENT_TOKEN_NONE` falls back to the same string as the portrait's; since that duplicate is being deleted, rewrite that sentence to say both no-glow cases share `GLOW_NONE`.

- [ ] **Step 7: Wire the shim into the regen path**

In `regenerate_one` (`generate-npc.py:1495`), change:

```python
    npc = dict(entry["traits"])
```

to:

```python
    npc = migrate_traits(entry["traits"])
```

- [ ] **Step 8: Update the theme placement test**

In `test/test_theme_tag_placement.py`, replace every `"Accent"` with `"Glow colour"`.

- [ ] **Step 9: Run the full suite**

Run: `python -m unittest discover -s test -t . 2>&1 | tail -5`
Expected: `OK`, 95 tests (90 baseline + 5 new).

- [ ] **Step 10: Confirm the budget is unchanged**

Run: `python -m test.prompt_budget`
Expected: token p99 still 510, portrait p99 still 495. A rename changes no lengths; a difference here means something else was edited by accident.

- [ ] **Step 11: Commit**

```bash
git add generate-npc.py prompts/npc-generator-tables.md test/fixtures/tables-minimal.md test/test_theme_tag_placement.py test/test_glow_rename.py
git commit -m "refactor: rename Accent to Glow colour, with a manifest shim

The table holds the colour of the one light source in the frame, gated on
has_light_source(); 'Accent' read as a design accent and will read worse
once Faction starts asserting pigment. All 135 stored manifest entries use
the old key and --regen-manifest rebuilds from them, so migrate_traits()
maps the old name forward rather than breaking regeneration."
```

---

### Task 2: Split framing from pose in the token template

**Files:**
- Modify: `generate-npc.py` — `TOKEN_TEMPLATE:281`
- Modify: `prompts/npc-generator-tables.md` — the reproduced Token template and its explanatory prose
- Create: `test/test_token_pose.py`

**Interfaces:**
- Consumes: `{glow}` slot naming from Task 1.
- Produces: `TOKEN_TEMPLATE` no longer contains the strings `"standing at full height"` or `"both boots planted"`, and does contain `"the whole figure in frame"`. Task 3's guard test asserts the same.

- [ ] **Step 1: Write the failing test**

Create `test/test_token_pose.py`:

```python
"""The token template must not assert a pose - {stance} does that.

'standing at full height' was doing two jobs: asserting the framing (whole
body in shot, right proportions) and asserting a pose. Only the framing was
wanted. With a crouching Stance rolled the prompt claimed both standing and
crouching at once, and the model resolved that by rendering two figures - one
standing, one crouched on the platform the pose's 'raised ledge' implied.
"""
import random
import unittest

from test.helpers import FIXTURE_TABLES, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)


class TestTokenTemplatePose(unittest.TestCase):
    def test_the_template_makes_no_standing_claim(self):
        self.assertNotIn("standing at full height", gen.TOKEN_TEMPLATE)

    def test_the_template_does_not_claim_the_boots_are_planted(self):
        """False for every kneeling, sitting and crouching bullet in Stance."""
        self.assertNotIn("both boots planted", gen.TOKEN_TEMPLATE)

    def test_the_template_does_not_claim_the_arms_are_free(self):
        """Contradicts any pose braced on an arm."""
        self.assertNotIn("arms free", gen.TOKEN_TEMPLATE)

    def test_the_framing_assertion_survives(self):
        """Dropping the pose claim must not drop the full-body framing with it."""
        for phrase in ("the whole figure in frame",
                       "clear empty space above and below",
                       "seven to eight heads tall",
                       "no leg wraps or puttees"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, gen.TOKEN_TEMPLATE)

    def test_a_crouching_stance_produces_no_contradiction(self):
        npc = gen.roll_npc(TABLES, random.Random(0),
                           {"Stance": "crouched low and coiled, "
                                      "weight braced forward on one arm"})
        _, token = gen.build_prompts(npc)
        self.assertIn("crouched low and coiled", token)
        self.assertNotIn("standing at full height", token)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python -m unittest test.test_token_pose -v`
Expected: FAIL on four of the five — `'standing at full height' unexpectedly found`, `'both boots planted' unexpectedly found`, `'arms free' unexpectedly found`, `'the whole figure in frame' not found`.

- [ ] **Step 3: Edit the template**

In `generate-npc.py`, `TOKEN_TEMPLATE`. Replace:

```python
    "on the figure. {Subject} {is_are} "
    "standing at full height facing the viewer, entire body visible from the top of "
    "{possessive} head to the soles of {possessive} plain modern boots, no leg wraps or "
    "puttees, with clear empty space above and below, in realistic adult proportions "
    "roughly seven to eight heads tall. "
```

with:

```python
    "on the figure. {Subject} {is_are} "
    "facing the viewer, the whole figure in frame from the top of "
    "{possessive} head to the soles of {possessive} plain modern boots, no leg wraps or "
    "puttees, with clear empty space above and below, in realistic adult proportions "
    "roughly seven to eight heads tall. "
```

And replace:

```python
    "{Possessive} face carries {demeanor}. {gear_line}{Subject} {is_are} {stance}, both "
    "boots planted and fully visible, the pose relaxed and natural with the arms free. "
```

with:

```python
    "{Possessive} face carries {demeanor}. {gear_line}{Subject} {is_are} {stance}, both "
    "feet in frame, the pose natural and unforced. "
```

Add this comment immediately above `TOKEN_TEMPLATE`, after the existing one:

```python
# The opening sentence asserts FRAMING only - the whole body in shot, at
# realistic proportions. It used to open "standing at full height", which also
# asserted a pose, and that fought {stance} on every crouching, kneeling or
# sitting bullet: the prompt claimed both at once and the model answered by
# rendering both, one standing figure and one crouched. The pose is {stance}'s
# job alone. "both boots planted and fully visible" went the same way - it is
# false for every non-standing bullet - and "the arms free" contradicted any
# pose braced on an arm. What replaces them says only what is true of every
# pose in the table: the feet are in frame and the pose is not rigid.
```

- [ ] **Step 4: Run the test**

Run: `python -m unittest test.test_token_pose -v`
Expected: PASS, 5 tests.

- [ ] **Step 5: Update the tables file's reproduced template**

In `prompts/npc-generator-tables.md`, under `### Token (1024x1280, then RMBG to a transparent PNG)`, update the quoted template to match the new wording exactly, and replace the paragraph beginning *"The token template names the footwear outright"* — keep that paragraph, it is still true — but add a new one after it:

```
The opening sentence asserts framing, not pose. It used to read "standing at
full height", which fought the rolled Stance on every crouching, kneeling or
sitting bullet - the prompt asserted standing and crouching at once and the
render came back with two figures. Stance owns the pose; this sentence owns
the framing, and the two no longer overlap.
```

- [ ] **Step 6: Confirm the budget improved**

Run: `python -m test.prompt_budget`
Expected: token p99 drops from 510 to roughly 495. Portrait unchanged at 495.

- [ ] **Step 7: Run the full suite**

Run: `python -m unittest discover -s test -t . 2>&1 | tail -5`
Expected: `OK`, 100 tests.

- [ ] **Step 8: Commit**

```bash
git add generate-npc.py prompts/npc-generator-tables.md test/test_token_pose.py
git commit -m "fix: stop the token template asserting a pose over the rolled Stance

'standing at full height' asserted framing and a pose at once. Against a
crouching Stance the prompt claimed both, and the model rendered both - the
reported two figures. Framing and pose are now separate sentences, and the
'boots planted'/'arms free' tail goes with it: both were false for every
kneeling, sitting and crouching bullet in the table. Buys ~15 tokens back
against the 512 ceiling."
```

---

### Task 3: Scrub scenery, furniture and weather from `Stance`

**Files:**
- Modify: `prompts/npc-generator-tables.md` — `## Stance` and `## Stance (she) +`
- Create: `test/test_stance_content.py`

**Interfaces:**
- Consumes: Task 2's template edit (the rewritten bullets assume the template no longer claims the boots are planted).
- Produces: a `Stance` table containing no environment nouns. Task 5 adds the `armed` flag to seven of these same bullets; this task does **not** add flags, only rewrites prose.

- [ ] **Step 1: Write the failing guard test**

Create `test/test_stance_content.py`:

```python
"""Stance is token-only, and the token is cut to a transparent PNG.

The portrait takes its pose from Backdrop; Stance reaches only the token,
which renders on flat white so ComfyUI's RMBG pass can cut it out. A bullet
naming a ledge, a wall, machinery or the weather therefore describes something
that must not be in the image at all - and cannot be argued away by the
template's trailing "no environment", because generation runs at CFG 1.0 with
no negative prompt. A positive noun beats a trailing negative. The only fix is
not to say the word, and this test is what keeps it unsaid.
"""
import re
import unittest

from test.helpers import REPO, load_generator, bullets_for

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")

# Word -> why it cannot appear. Matched on word boundaries, so "background"
# does not trip "ground" and "wound" does not trip "wind".
BANNED = {
    "ledge": "scenery the token cannot show",
    "machinery": "scenery the token cannot show",
    "wall": "scenery the token cannot show",
    "ground": "scenery the token cannot show",
    "floor": "scenery the token cannot show",
    "chair": "furniture the token cannot show",
    "bench": "furniture the token cannot show",
    "seat": "furniture the token cannot show",
    "rain": "weather the token cannot show",
    "snow": "weather the token cannot show",
    "wind": "weather the token cannot show",
    "heat": "weather the token cannot show",
}


class TestStanceContent(unittest.TestCase):
    def test_no_stance_bullet_names_anything_but_the_body(self):
        for bullet in bullets_for(LIVE, "Stance"):
            text = gen.split_flags(bullet)[0].lower()
            for word, why in BANNED.items():
                with self.subTest(bullet=bullet, word=word):
                    self.assertIsNone(
                        re.search(r"\b%s\b" % word, text),
                        "Stance bullet names %r - %s: %s" % (word, why, bullet))

    def test_the_stance_pool_is_not_empty(self):
        """A vacuous pass if the table were ever renamed out from under this."""
        self.assertGreater(len(bullets_for(LIVE, "Stance")), 30)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python -m unittest test.test_stance_content -v`
Expected: FAIL, exactly five subtests — `ledge` (1 bullet), `machinery` (1 bullet), and `wind`/`snow`/`heat` (2 bullets between them). Measured against the live table before writing this plan.

`ground`, `chair`, `bench`, `seat`, `floor`, `wall` and `rain` match nothing today. They are in the banned list to keep the door shut, not because anything currently trips them.

- [ ] **Step 3: Rewrite the offending bullets**

In `prompts/npc-generator-tables.md`, `## Stance`, apply exactly these six replacements.

**Four are driven by the test.** Two are judgement calls the test does not catch and would not catch — a blade planted point-down implies a ground plane and sitting back implies a chair, without either naming one. They are corrected here because Task 2 removed the template's "both boots planted" claim and these two are the bullets that most needed it:

```
- crouched low and coiled on a raised ledge, weight braced forward on one arm, ready to spring || hands
→
- crouched low and coiled, weight braced forward on one arm, ready to spring || hands
```

```
- leaning down into open machinery from above, braced on one forearm and reaching in with the other hand || hands
→
- leaning forward and down, braced on one forearm, the other hand reaching toward something out of frame || hands
```

```
- crouched low on one knee, gripping a blade planted point-down and ready to spring || hands
→
- crouched low on one knee, both hands wrapped around an upright blade, ready to spring || hands
```

*(judgement call — "planted point-down" names no banned word but plants the blade in a floor the token does not have)*

```
- raising {possessive} weapon high overhead in both hands, mid-swing, hair whipped wild by the wind and snow || hands
→
- raising {possessive} weapon high overhead in both hands, mid-swing, hair whipped wild by the motion || hands
```

```
- walking straight toward the viewer with {possessive} weapon raised over one shoulder, cloak snapping back in the rising heat || hands
→
- walking straight toward the viewer with {possessive} weapon raised over one shoulder, cloak snapping back behind {object} || hands
```

In `## Stance (she) +`:

```
- sitting back with both hands laced behind {possessive} head, elbows out, utterly at ease || hands
→
- standing with both hands laced behind {possessive} head, elbows out, utterly at ease || hands
```

*(judgement call — "sitting back" names no banned word but puts the figure in a chair the token cannot show)*

Leave the cross-legged and kneeling bullets alone. They name no furniture, and Task 2's template no longer claims their boots are planted.

- [ ] **Step 4: Add the table comment**

At the head of `## Stance`, before the first bullet:

```
<!--
  TOKEN ONLY. The portrait takes its pose from Backdrop; this table reaches
  only the token, which renders on flat white so the RMBG pass can cut it to a
  transparent PNG for dropping onto a battlemap.

  So a bullet here may describe the BODY and nothing else. No ground, no
  ledge, no wall, no furniture, no weather, no props that are not held in a
  hand. A pose may crouch, kneel or sit - it simply must not sit on anything.

  This is not a style preference. Generation runs at CFG 1.0 with no negative
  prompt, so the template's trailing "no environment" cannot argue a noun back
  out of the image: a rolled "raised ledge" put a visible platform under the
  figure and a second person on it. test_stance_content.py enforces the rule.
-->
```

- [ ] **Step 5: Run the test**

Run: `python -m unittest test.test_stance_content -v`
Expected: PASS.

- [ ] **Step 6: Run the full suite and the budget**

Run: `python -m unittest discover -s test -t . 2>&1 | tail -5`
Expected: `OK`, 102 tests.

Run: `python -m test.prompt_budget`
Expected: token p99 at or below the Task 2 figure.

- [ ] **Step 7: Commit**

```bash
git add prompts/npc-generator-tables.md test/test_stance_content.py
git commit -m "fix: scrub scenery, furniture and weather from the Stance table

Stance is token-only and the token is cut to a transparent PNG, so a bullet
naming a ledge, open machinery or driving snow describes something that must
not be in the frame at all. Six bullets rewritten to describe only the body;
the poses themselves are unchanged. A guard test now enforces it, since CFG
1.0 with no negative prompt means the template's 'no environment' cannot
argue the noun back out."
```

---

### Task 4: Give civilians a weapon policy

**Files:**
- Modify: `generate-npc.py` — `WEAPON_POLICY:236`, `apply_weapon_policy:472`
- Modify: `prompts/npc-generator-tables.md` — the `## Weapon` comment
- Modify: `test/test_weapon.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `DEFAULT_WEAPON_POLICY = "civilian"` and `CIVILIAN_UNARMED_COPIES = 3` at module level. `apply_weapon_policy(options, category, mil)` keeps its signature in this task; Task 5 adds a fourth parameter.

- [ ] **Step 1: Write the failing test**

Append to `test/test_weapon.py`, inside a new class:

```python
class TestCivilianWeaponPolicy(unittest.TestCase):
    """Seven Roles reached apply_weapon_policy with no policy at all.

    WEAPON_POLICY only named Officials and Criminals, so a dockworker, a
    maintenance technician or a data courier rolled the raw pool - measured at
    65% armed against the live tables, because Weapon deliberately sits
    outside the civ/mil filter and a civilian can reach every military bullet
    in it.
    """

    def unarmed_share(self, options):
        unarmed = [x for x in options if "weapon" not in gen.split_flags(x)[1]]
        return len(unarmed) / len(options)

    def test_an_uncategorised_civilian_role_gets_the_civilian_tier(self):
        """The default, not another hardcoded bucket - so a Role added to the
        table later is covered without also needing a ROLE_CATEGORIES entry."""
        biased = gen.apply_weapon_policy(TABLES["Weapon"], None, False)
        self.assertGreater(self.unarmed_share(biased), 0.6)

    def test_a_named_civilian_category_gets_it_too(self):
        biased = gen.apply_weapon_policy(TABLES["Weapon"], "Laborers", False)
        self.assertGreater(self.unarmed_share(biased), 0.6)

    def test_the_civilian_tier_leaves_armed_rolls_reachable(self):
        """Two-thirds unarmed, not always unarmed."""
        biased = gen.apply_weapon_policy(TABLES["Weapon"], "Laborers", False)
        self.assertLess(self.unarmed_share(biased), 0.95)

    def test_criminals_keep_their_armed_bias(self):
        biased = gen.apply_weapon_policy(TABLES["Weapon"], "Criminals", False)
        self.assertLess(self.unarmed_share(biased),
                        self.unarmed_share(TABLES["Weapon"]))

    def test_officials_keep_their_restriction(self):
        biased = gen.apply_weapon_policy(TABLES["Weapon"], "Officials", False)
        self.assertGreater(self.unarmed_share(biased), 0.6)

    def test_a_mil_role_is_unaffected_by_the_civilian_default(self):
        """The mil branch returns before policy is consulted."""
        armed = gen.apply_weapon_policy(TABLES["Weapon"], None, True)
        self.assertEqual(self.unarmed_share(armed), 0.0)
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python -m unittest test.test_weapon -v`
Expected: FAIL on `test_an_uncategorised_civilian_role_gets_the_civilian_tier` and `test_a_named_civilian_category_gets_it_too` — the unarmed share is 0.4 in the fixture, below 0.6.

- [ ] **Step 3: Add the civilian tier**

In `generate-npc.py`, extend the `WEAPON_POLICY` block:

```python
# The Weapon-roll policy each ROLE_CATEGORIES bucket gets, layered on top of
# the mil/civ split - see apply_weapon_policy().
WEAPON_POLICY = {
    "Officials": "restricted",
    "Criminals": "armed_bias",
}

# What a non-mil Role gets when WEAPON_POLICY names no policy for it. It used
# to be "none at all", which meant seven civilian Roles - dockworker, chief
# mechanic, maintenance technician, freelance salvager, bar owner, data
# courier, scavenger-priest - rolled the raw pool and came out armed 65% of
# the time. Weapon sits outside the civ/mil filter by design (a civilian may
# carry a military-issue weapon), so nothing else was holding them back.
# A default rather than seven more WEAPON_POLICY entries, so a civilian Role
# added to the Role table later is covered without a second edit here.
DEFAULT_WEAPON_POLICY = "civilian"

# How many extra copies of the unarmed bullets the civilian tier stacks into
# the pool. The live table is 86 weighted entries, 30 of them unarmed; three
# extra copies makes it 176 with 120 unarmed, or 68%. This is the dial for how
# armed ordinary civilians feel - raise it for a quieter setting.
CIVILIAN_UNARMED_COPIES = 3
```

In `apply_weapon_policy`, change:

```python
    policy = WEAPON_POLICY.get(category)
```

to:

```python
    policy = WEAPON_POLICY.get(category, DEFAULT_WEAPON_POLICY)
```

and add this branch after the `armed_bias` branch, before the final `return options`:

```python
    if policy == "civilian":
        unarmed = [x for x in options if "weapon" not in split_flags(x)[1]]
        return options + unarmed * CIVILIAN_UNARMED_COPIES if unarmed else options
    return options
```

Update the function's docstring: the "Any other category ... rolls Weapon exactly as before: untouched" paragraph is no longer true. Replace it with a fourth bullet describing the civilian tier and a note that the untouched case is now only reachable from a tables file with no `weapon` flags at all.

- [ ] **Step 4: Run the test**

Run: `python -m unittest test.test_weapon -v`
Expected: PASS, all tests in the file.

- [ ] **Step 5: Update the Weapon table comment**

In `prompts/npc-generator-tables.md`, in the `## Weapon` comment, the sentence *"Its weight is the dial for how armed the setting feels - raise it for a quieter one."* is now only half the story. Append:

```
  That weight is the baseline. On top of it, apply_weapon_policy() gives every
  non-military Role a 'civilian' tier that stacks further copies of this entry
  into the pool - CIVILIAN_UNARMED_COPIES in generate-npc.py - because without
  it an ordinary dockworker came out armed two rolls in three. Weapon sits
  outside the civ/mil filter on purpose, so nothing else was holding a
  civilian back from the military bullets here.
```

- [ ] **Step 6: Run the full suite**

Run: `python -m unittest discover -s test -t . 2>&1 | tail -5`
Expected: `OK`, 108 tests.

- [ ] **Step 7: Commit**

```bash
git add generate-npc.py prompts/npc-generator-tables.md test/test_weapon.py
git commit -m "fix: give civilian Roles a weapon policy instead of the raw pool

WEAPON_POLICY named only Officials and Criminals, so seven civilian Roles
fell through to no policy at all and rolled 65% armed - Weapon sits outside
the civ/mil filter by design, so nothing was holding them back. The civilian
tier is now the default for any non-mil Role rather than seven more entries,
so a Role added later is covered without a second edit."
```

---

### Task 5: `--unarmed`, and the `armed` stance flag

**Files:**
- Modify: `generate-npc.py` — `apply_weapon_policy:472`, `roll_npc:558`, the stance filter at `:759`, `parse_args:1275`, the `roll_npc` call at `:1671`
- Modify: `prompts/npc-generator-tables.md` — `## Stance` bullets and the `||` conventions section
- Modify: `test/test_weapon.py`
- Create: `test/test_stance_armed.py`

**Interfaces:**
- Consumes: `DEFAULT_WEAPON_POLICY` from Task 4; the rewritten Stance bullets from Task 3.
- Produces: `apply_weapon_policy(options, category, mil, unarmed=False)` and `roll_npc(tables, rng, overrides=None, unarmed=False)`. The GUI plan's unarmed checkbox shells out to `--unarmed` and depends on this task.

- [ ] **Step 1: Write the failing test for the flag**

Append to `test/test_weapon.py`:

```python
class TestUnarmedFlag(unittest.TestCase):
    """--unarmed disarms who it can, not everyone.

    Soldiers, pilots and other mil Roles keep their guaranteed sidearm, and so
    do Criminals - a pirate with empty hands is not what the flag is for. It
    disarms the civilians, who are the ones you actually want unarmed when you
    are populating a market or a dockside.
    """

    def test_a_civilian_is_disarmed(self):
        for seed in range(50):
            npc = gen.roll_npc(TABLES, random.Random(seed),
                               {"Role": "a dockworker"}, unarmed=True)
            self.assertEqual(npc["Weapon"], "",
                             "seed %d: a civilian rolled armed under --unarmed" % seed)

    def test_a_mil_role_stays_armed(self):
        for seed in range(50):
            npc = gen.roll_npc(TABLES, random.Random(seed),
                               {"Role": "a Union marine soldier || mil"}, unarmed=True)
            self.assertNotEqual(npc["Weapon"], "",
                                "seed %d: a mil Role was disarmed" % seed)

    def test_criminals_stay_armed_at_the_policy_level(self):
        biased = gen.apply_weapon_policy(TABLES["Weapon"], "Criminals", False, unarmed=True)
        armed = [x for x in biased if "weapon" in gen.split_flags(x)[1]]
        self.assertTrue(armed, "--unarmed emptied the Criminals pool")

    def test_the_default_is_unchanged(self):
        """Omitting the flag must not disarm anyone."""
        self.assertTrue(
            any(gen.roll_npc(TABLES, random.Random(s),
                             {"Role": "a dockworker"})["Weapon"] != ""
                for s in range(100)),
            "a civilian never rolled armed without --unarmed")
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python -m unittest test.test_weapon.TestUnarmedFlag -v`
Expected: FAIL — `TypeError: roll_npc() got an unexpected keyword argument 'unarmed'`

- [ ] **Step 3: Thread the flag through**

In `apply_weapon_policy`, change the signature to `def apply_weapon_policy(options, category, mil, unarmed=False):` and add this as the **first** branch in the body, before `if mil:`:

```python
    # --unarmed disarms who it can, not everyone. A mil Role's sidearm is a
    # setting guarantee and a Criminal's armament is most of what makes them
    # read as one; the flag exists to empty ordinary civilians' hands. Placed
    # first so the intent is visible before the tiers it overrides, though the
    # mil guard below would reach the same answer either way.
    if unarmed and not mil and category != "Criminals":
        disarmed = [x for x in options if "weapon" not in split_flags(x)[1]]
        return disarmed or options
```

In `roll_npc`, change the signature to `def roll_npc(tables, rng, overrides=None, unarmed=False):` and the policy call to:

```python
        if name == "Weapon":
            options = apply_weapon_policy(
                options, ROLE_CATEGORIES.get(npc["Role"]), role_mil, unarmed)
```

In `parse_args`, in the `roll` argument group after `--set-trait`:

```python
    roll.add_argument("--unarmed", action="store_true",
                      help="roll every NPC unarmed, except military Roles and "
                           "Criminals - a soldier's sidearm and a pirate's "
                           "armament are what make them read as one")
```

At the `roll_npc` call site (`generate-npc.py:1671`):

```python
        npc = roll_npc(tables, random.Random(seed), overrides, args.unarmed)
```

Add to the `--regen-manifest` conflict list in `parse_args`, alongside `--count` and the rest:

```python
                ("--unarmed", args.unarmed),
```

- [ ] **Step 4: Run the flag test**

Run: `python -m unittest test.test_weapon.TestUnarmedFlag -v`
Expected: PASS, 4 tests.

- [ ] **Step 5: Write the failing test for the `armed` stance flag**

Create `test/test_stance_armed.py`:

```python
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
        for seed in range(100):
            npc = gen.roll_npc(TABLES, random.Random(seed),
                               {"Role": "a dockworker"}, unarmed=True)
            self.assertEqual(npc["Weapon"], "")
            stance = npc["Stance"]
            source = next(b for b in bullets_for(TABLES, "Stance")
                          if gen.split_flags(b)[0] == stance
                          or "{" in b)  # pronoun slots are substituted by now
            flags = gen.split_flags(source)[1]
            self.assertNotIn("armed", flags, "seed %d: %s" % (seed, stance))
            self.assertNotIn("gun", flags, "seed %d: %s" % (seed, stance))

    def test_an_armed_npc_can_still_reach_an_armed_pose(self):
        """The filter must not make those seven bullets permanently dead."""
        armed_bullets = [b for b in bullets_for(LIVE, "Stance")
                         if "armed" in gen.split_flags(b)[1]]
        self.assertGreaterEqual(
            len(armed_bullets), 7,
            "expected at least the seven weapon-naming bullets to be tagged")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 6: Run it to confirm it fails**

Run: `python -m unittest test.test_stance_armed -v`
Expected: FAIL — bullets naming a weapon carry neither flag, and `armed_bullets` is empty.

- [ ] **Step 7: Tag the seven bullets and gate them**

In `prompts/npc-generator-tables.md`, `## Stance`, change `|| hands` to `|| hands armed` on exactly these seven (three of which Task 3 already rewrote — use the post-rewrite text):

1. `crouched low on one knee, both hands wrapped around an upright blade, ready to spring`
2. `caught in a dynamic overhead swing, both hands driving a blade down in a decisive arc, cloak and sash ribbons whipped by the motion`
3. `kneeling formally with both hands folded around an upright hilt held back against one shoulder`
4. `standing in profile with head bowed slightly, one hand resting on a sheathed blade at the hip`
5. `walking straight toward the viewer with {possessive} weapon raised over one shoulder, cloak snapping back behind {object}`
6. `raising {possessive} weapon high overhead in both hands, mid-swing, hair whipped wild by the motion`
7. `standing tense with both hands crossed at the hip, one gripping the hilt of {possessive} sheathed weapon, poised to draw`

In `generate-npc.py`, replace the stance gun filter at `:759-762`:

```python
    stances = [split_flags(x) for x in variant_table(tables, "Stance", subject)]
    if "gun" not in carried_flags:
        unarmed = [x for x in stances if "gun" not in x[1]]
        stances = unarmed or stances       # never filter the pool down to nothing
```

with:

```python
    stances = [split_flags(x) for x in variant_table(tables, "Stance", subject)]
    # Two flags, one hierarchy. 'armed' marks a pose that references a weapon
    # of any kind - a blade held, a hilt gripped, a weapon raised overhead;
    # 'gun' marks the narrower case of a firearm being handled. An NPC whose
    # Weapon roll came up empty can wear neither, or the prompt poses them
    # brandishing something no earlier sentence names. Before 'armed' existed
    # only 'gun' was gated, so seven melee poses could land on an unarmed
    # figure - rare on a plain roll, routine under --unarmed.
    #
    # The unarmed bullet is identified by its 'none' flag, which used to be an
    # inert marker and is now load-bearing; the Weapon table's comment says so.
    if "none" in weapon_flags:
        disarmed = [x for x in stances
                    if "armed" not in x[1] and "gun" not in x[1]]
        stances = disarmed or stances      # never filter the pool down to nothing
    elif "gun" not in carried_flags:
        unarmed = [x for x in stances if "gun" not in x[1]]
        stances = unarmed or stances       # never filter the pool down to nothing
```

- [ ] **Step 8: Run the stance test**

Run: `python -m unittest test.test_stance_armed -v`
Expected: PASS, 3 tests.

- [ ] **Step 9: Document both flags in the tables file**

In `## How the script reads this file`, the bullet describing `|| gun` currently says *"**Weapon** and **Stance** bullets may also carry `|| gun`"*. Extend that bullet to introduce `armed` as the wider flag, and state the hierarchy: an empty Weapon roll drops both, a non-firearm weapon drops only `gun`.

In the `## Weapon` comment, the sentence *"'none' is a literal marker flag that nothing reads"* is now false. Change it to say the Stance filter reads it to decide whether a weapon-naming pose is reachable.

- [ ] **Step 10: Run the full suite and the budget**

Run: `python -m unittest discover -s test -t . 2>&1 | tail -5`
Expected: `OK`, 115 tests.

Run: `python -m test.prompt_budget`
Expected: token p99 unchanged from Task 3.

- [ ] **Step 11: Commit**

```bash
git add generate-npc.py prompts/npc-generator-tables.md test/test_weapon.py test/test_stance_armed.py
git commit -m "feat: add --unarmed, and stop unarmed NPCs being posed with weapons

--unarmed empties civilian hands while leaving mil Roles and Criminals
armed. Adding it exposed a latent bug worth fixing on its own: seven Stance
bullets name a weapon but carried only '|| hands', and only 'gun' was gated
on the Weapon roll, so an unarmed figure could be posed raising a weapon no
earlier sentence names. 'armed' is the wider flag; 'gun' keeps its narrower
firearm meaning."
```

---

### Task 6: Hue-only glow colours

Small and self-contained. Kept separate from Task 1 because that task was a rename and this one is a content judgement.

**Files:**
- Modify: `prompts/npc-generator-tables.md` — `## Glow colour`
- Create: `test/test_glow_colours.py`

**Interfaces:**
- Consumes: the `Glow colour` heading from Task 1.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Write the failing test**

Create `test/test_glow_colours.py`:

```python
"""Glow colours name a hue, never a light-emitting phenomenon.

Both templates wrap the rolled value as a glow - "A faint {glow} glow falls
across one side of her face", "a single {glow} glow the only saturated color".
So 'electric blue' renders as "electric blue glow" and the model draws actual
arcing electricity; 'neon cyan' pulls neon tubing into frame the same way. The
intent was only ever to name a shade.
"""
import re
import unittest

from test.helpers import REPO, load_generator, bullets_for

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")

# Words that name a light SOURCE rather than a shade. Anything here will be
# read as an instruction to draw the thing, not to tint the light.
PHENOMENA = ("electric", "neon", "laser", "plasma", "fluorescent", "led",
             "strobe", "flame", "spark")


class TestGlowColours(unittest.TestCase):
    def test_no_glow_colour_names_a_light_source(self):
        for bullet in bullets_for(LIVE, "Glow colour"):
            text = gen.split_flags(bullet)[0].lower()
            for word in PHENOMENA:
                with self.subTest(bullet=bullet, word=word):
                    self.assertIsNone(
                        re.search(r"\b%s\b" % word, text),
                        "Glow colour %r names a light source, not a hue - it "
                        "will be rendered rather than used as a tint" % bullet)

    def test_the_pool_is_not_empty(self):
        self.assertGreaterEqual(len(bullets_for(LIVE, "Glow colour")), 10)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python -m unittest test.test_glow_colours -v`
Expected: FAIL on two subtests — `electric blue` and `neon cyan`.

- [ ] **Step 3: Rename the two entries**

In `prompts/npc-generator-tables.md`, `## Glow colour`:

```
- electric blue   →   - vivid cobalt blue
- neon cyan       →   - bright cyan
```

- [ ] **Step 4: Extend the table comment**

Append to the `## Glow colour` comment written in Task 1:

```
  Entries name a HUE, never a light-emitting phenomenon. Both templates wrap
  the value as "{glow} glow", so "electric blue" came out as arcing
  electricity and "neon cyan" pulled neon tubing into frame. Say the shade -
  "vivid cobalt blue" - and let the template supply the glow.
```

- [ ] **Step 5: Run the test and the full suite**

Run: `python -m unittest test.test_glow_colours -v`
Expected: PASS.

Run: `python -m unittest discover -s test -t . 2>&1 | tail -5`
Expected: `OK`, 117 tests.

- [ ] **Step 6: Commit**

```bash
git add prompts/npc-generator-tables.md test/test_glow_colours.py
git commit -m "fix: name hues, not light sources, in the Glow colour table

Both templates wrap the value as '{glow} glow', so 'electric blue' rendered
arcing electricity rather than tinting the light. Renamed to 'vivid cobalt
blue' and 'bright cyan', with a test so the next author does not add
'neon pink'."
```

---

### Task 7: Give `Faction` a three-segment shape

Plumbing only — the table content stays as-is in this task, moved into the new shape. Task 8 rewrites it. Splitting the two keeps a parsing change reviewable separately from a content change.

**Files:**
- Modify: `generate-npc.py` — add `split_faction`, `flags_for:965`, `filter_by_mil:387`, `roll_npc:724` and `:807`, `build_prompts`, `write_dossier`, `PORTRAIT_TEMPLATE:260`, `TOKEN_TEMPLATE:281`, the comment at `:713`
- Modify: `prompts/npc-generator-tables.md` — `## Faction`, the `||` conventions section
- Modify: `test/fixtures/tables-minimal.md` — `## Faction`
- Create: `test/test_faction.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `split_faction(bullet) -> (name: str, visual: str, flags: tuple[str, ...])`. `build_prompts` gains a `faction_line` field replacing `faction`; both templates use `{faction_line}` and no longer use `{faction}`.

- [ ] **Step 1: Write the failing test**

Create `test/test_faction.py`:

```python
"""Faction carries a name for the dossier and a visual for the prompt.

The single-segment form put a garment CATEGORY - "corporate wear", "service
dress" - into the prompt directly after Outfit's specific garment description,
where the vaguer clause simply lost. Deleting the Faction line from a prompt
changed the render not at all. Splitting it lets the dossier keep the
affiliation name while the prompt gets a signature written to describe what
Outfit does not: fabric, tailoring, insignia, patina.

Three segments, the same shape Backdrop and Hair colour use - and for the same
reason: two of them are prose and only the third is flags.
"""
import random
import unittest

from test.helpers import FIXTURE_TABLES, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)


class TestSplitFaction(unittest.TestCase):
    def test_all_three_segments(self):
        name, visual, flags = gen.split_faction(
            "Harrison Armory || sharply pressed, high collar || mil palette")
        self.assertEqual(name, "Harrison Armory")
        self.assertEqual(visual, "sharply pressed, high collar")
        self.assertEqual(flags, ("mil", "palette"))

    def test_an_empty_visual_segment(self):
        name, visual, flags = gen.split_faction("Unaligned || || civ")
        self.assertEqual(name, "Unaligned")
        self.assertEqual(visual, "")
        self.assertEqual(flags, ("civ",))

    def test_a_bare_name_has_no_visual_and_no_flags(self):
        self.assertEqual(gen.split_faction("Unregistered"), ("Unregistered", "", ()))


class TestFactionFlags(unittest.TestCase):
    def test_flags_for_reads_the_third_segment(self):
        """Reading the second blindly would take the visual prose for flags."""
        flags = gen.flags_for("Faction", "Harrison Armory || sharply pressed || mil")
        self.assertEqual(flags, ("mil",))

    def test_the_civ_mil_filter_still_works_on_three_segments(self):
        options = [
            "Unaligned || || civ",
            "Harrison Armory || sharply pressed || mil",
        ]
        self.assertEqual(gen.filter_by_mil(options, True, "Faction"),
                         ["Harrison Armory || sharply pressed || mil"])
        self.assertEqual(gen.filter_by_mil(options, False, "Faction"),
                         ["Unaligned || || civ"])

    def test_visual_prose_containing_a_flag_word_is_not_read_as_a_flag(self):
        """The trap split_flags() would fall into: partition('||') returns
        every word after the first separator, so a visual mentioning 'civil'
        or 'military' would leak into the flag tuple."""
        flags = gen.flags_for(
            "Faction", "Colonial militia || mismatched military surplus || mil")
        self.assertEqual(flags, ("mil",))


class TestFactionInOutput(unittest.TestCase):
    def test_the_dossier_gets_the_name_and_the_prompt_gets_the_visual(self):
        npc = gen.roll_npc(TABLES, random.Random(0),
                           {"Faction": "Harrison Armory || sharply pressed || mil"})
        self.assertEqual(gen.split_faction(npc["Faction"])[0], "Harrison Armory")
        portrait, token = gen.build_prompts(npc)
        for prompt in (portrait, token):
            self.assertIn("sharply pressed", prompt)
            self.assertNotIn("Harrison Armory", prompt)

    def test_an_empty_visual_leaves_no_orphaned_comma(self):
        npc = gen.roll_npc(TABLES, random.Random(0),
                           {"Faction": "Unaligned || || civ"})
        portrait, token = gen.build_prompts(npc)
        for prompt in (portrait, token):
            self.assertNotIn(", ,", prompt)
            self.assertNotIn(",  ", prompt)
            self.assertIn("the clothing following the shape of that frame", prompt)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python -m unittest test.test_faction -v`
Expected: FAIL — `module 'gennpc' has no attribute 'split_faction'`, and `filter_by_mil()` takes 2 positional arguments.

- [ ] **Step 3: Add the splitter**

In `generate-npc.py`, immediately after `split_hair_colour`:

```python
def split_faction(bullet):
    """A Faction bullet carries the name, an optional visual, and flags.

    Three segments, the same shape split_backdrop() and split_hair_colour()
    use, and for the same reason: two of them are prose that goes to different
    places and only the third is flags.

    The name is what the dossier and the GUI print - "Smith-Shimano Corpro".
    The visual is what reaches the image prompt, and it is deliberately allowed
    to be empty: two entries here are non-affiliations with nothing to show.

    The split exists because the single-segment form put a garment CATEGORY
    ("corporate wear", "service dress") in the prompt immediately after
    Outfit's specific garment description, competing with it for the same slot
    and losing every time - deleting the whole Faction clause from a prompt
    changed the render not at all. The visual segment is written to describe
    what Outfit does not: fabric, tailoring, insignia, patina.
    """
    parts = [p.strip() for p in bullet.split("||")]
    name = parts[0]
    visual = parts[1] if len(parts) > 1 else ""
    flags = tuple(f for f in parts[2].split() if f) if len(parts) > 2 else ()
    return name, visual, flags
```

- [ ] **Step 4: Teach `flags_for` about it**

In `flags_for`, add before the final `return`:

```python
    if name == "Faction":
        return split_faction(bullet)[2]
```

and update that function's docstring, which currently says *"Backdrop and Hair colour both carry three segments"* — it is three tables now.

- [ ] **Step 5: Route `filter_by_mil` through `flags_for`**

Change the signature and body:

```python
def filter_by_mil(options, mil, name):
```

```python
    exclude = "civ" if mil else "mil"
    plain = [x for x in options if exclude not in flags_for(name, x)]
    return plain or options
```

Add to its docstring: *"Takes the table name because Faction keeps its flags in a third segment while Outfit keeps them in a second — `split_flags` on a three-segment bullet would return the visual prose as flags."*

Update the call site in `roll_npc`:

```python
        if name in ("Faction", "Outfit"):
            options = filter_by_mil(options, role_mil, name)
```

- [ ] **Step 6: Stop stripping Faction to one segment**

In `roll_npc`, remove `"Faction"` from the tuple at `:724`:

```python
        if name in ("Age", "Build", "Role", "Outfit",
                    "Hair", "Feature", "Headgear", "Weapon"):
```

Delete line `:807` entirely:

```python
    npc["Faction"] = split_flags(npc["Faction"])[0]
```

Extend the comment at `:713` — it names Backdrop and Hair colour as the two three-segment tables. Make it three, and say Faction's second segment is the visual signature the prompt uses.

- [ ] **Step 7: Give the templates a `faction_line`**

An empty visual would leave `wearing X, , the clothing...` — a doubled comma. Pre-format it the way `gear_line` already is.

In `build_prompts`, replace `"faction": npc["Faction"],` in the `fields` dict with nothing, and after `carrying` is built add:

```python
    # Pre-formatted rather than a bare slot, because a Faction with no visual
    # signature - the two non-affiliations - would otherwise leave a doubled
    # comma in the middle of the clothing sentence. Same reason gear_line is
    # assembled here rather than substituted raw.
    faction_name, faction_visual, faction_flags = split_faction(npc["Faction"])
    fields["faction_line"] = "%s, " % faction_visual if faction_visual else ""
```

In both templates, change `wearing {outfit}, {faction}, the clothing following` to `wearing {outfit}, {faction_line}the clothing following`.

In `write_dossier`, change `("Affiliation", npc["Faction"])` to `("Affiliation", split_faction(npc["Faction"])[0])`, and the byline `'"%s" - %s, %s.' % (npc["Callsigns"], npc["Role"], npc["Faction"])` to use `split_faction(npc["Faction"])[0]`.

- [ ] **Step 8: Move the existing table content into the new shape**

In `prompts/npc-generator-tables.md`, `## Faction` — keep today's wording, just reshaped, so this task changes no prose:

```
- x2 Unaligned || unaligned and freelance || civ
- x2 Union Administrative Department || in worn Union Administrative Department kit || mil
- Harrison Armory || in Harrison Armory service dress, imperial and immaculate || mil
- Smith-Shimano Corpro || in Smith-Shimano Corpro corporate wear, sleek and expensive || civ
- IPS-Northstar || in IPS-Northstar workwear, riveted and salt-stained || civ
- Karrakin Trade Baronies || in Karrakin baronial livery, formal and slightly archaic
- Colonial militia || in the mismatched kit of a colonial militia || mil
- Unregistered || in the deliberately anonymous gear of someone who does not answer questions
```

In `test/fixtures/tables-minimal.md`, `## Faction`:

```
- Unaligned || unaligned and freelance
- Dress uniform || in dress uniform || mil
```

- [ ] **Step 9: Run the test and the full suite**

Run: `python -m unittest test.test_faction -v`
Expected: PASS, 8 tests.

Run: `python -m unittest discover -s test -t . 2>&1 | tail -5`
Expected: `OK`, 125 tests.

- [ ] **Step 10: Confirm the prompts are byte-identical for a fixed seed**

This task is pure plumbing — the prompt text must not change yet.

Run: `python generate-npc.py --seed 1 --count 3 --dry-run 2>&1 | head -40`
Expected: the rendered clothing sentences read exactly as before, e.g. `wearing ..., in IPS-Northstar workwear, riveted and salt-stained, the clothing following the shape of that frame.`

Run: `python -m test.prompt_budget`
Expected: unchanged from Task 6.

- [ ] **Step 11: Commit**

```bash
git add generate-npc.py prompts/npc-generator-tables.md test/fixtures/tables-minimal.md test/test_faction.py
git commit -m "refactor: give Faction a name/visual/flags three-segment shape

Plumbing only - the prose is unchanged, just moved into the new shape, so
the rendered prompts are byte-identical for a fixed seed. filter_by_mil now
reads flags through flags_for(): split_flags() uses partition('||') and
would have returned the visual prose as flags, quietly breaking the civ/mil
split. The templates take a pre-formatted faction_line so an empty visual
leaves no doubled comma."
```

---

### Task 8: Faction content, and pigment alongside light

**Files:**
- Modify: `prompts/npc-generator-tables.md` — `## Faction` content and comment
- Modify: `generate-npc.py` — the `GLOW_*` constants, `build_prompts`
- Modify: `test/test_faction.py`

**Interfaces:**
- Consumes: `split_faction` and `faction_line` from Task 7; the `GLOW_*` constants from Task 1.
- Produces: a `palette` flag on pigment-asserting Faction bullets, and `GLOW_NONE_PIGMENT`. `fields["other"]` is `"other "` or `""`.

- [ ] **Step 1: Write the failing test**

Append to `test/test_faction.py`:

```python
class TestFactionPigment(unittest.TestCase):
    """Faction colour is pigment; the glow colour is light. They coexist.

    A green-and-gold Harrison uniform lit by a red instrument glow is
    coherent - but the closing line's claim that the glow is "the only
    saturated color in the frame" stops being true, so it softens to "the only
    other saturated color". Factions asserting pigment carry '|| palette'.
    """

    def test_a_pigment_faction_softens_the_exclusivity_claim(self):
        npc = gen.roll_npc(TABLES, random.Random(0), {
            "Faction": "Harrison Armory || in imperial green and gold || mil palette",
            "Glow colour": "amber",
            "Gear": "an old-fashioned lantern glowing warm, carried in one hand",
        })
        portrait, token = gen.build_prompts(npc)
        for prompt in (portrait, token):
            self.assertIn("only other saturated color", prompt)

    def test_a_plain_faction_keeps_the_exclusive_claim(self):
        npc = gen.roll_npc(TABLES, random.Random(0), {
            "Faction": "Unaligned || || civ",
            "Glow colour": "amber",
            "Gear": "an old-fashioned lantern glowing warm, carried in one hand",
        })
        portrait, token = gen.build_prompts(npc)
        for prompt in (portrait, token):
            self.assertIn("only saturated color", prompt)
            self.assertNotIn("only other saturated color", prompt)

    def test_a_pigment_faction_with_no_glow_drops_the_no_stray_colour_claim(self):
        """'no stray saturated color' contradicts a uniform that has one."""
        npc = gen.roll_npc(TABLES, random.Random(0), {
            "Faction": "Harrison Armory || in imperial green and gold || mil palette",
            "Gear": "a canvas tool roll at the hip",
        })
        portrait, token = gen.build_prompts(npc)
        for prompt in (portrait, token):
            self.assertNotIn("no stray saturated color", prompt)
            self.assertIn("Keep the rest of the palette restrained", prompt)

    def test_every_pigment_faction_actually_names_a_colour(self):
        """A 'palette' flag on a bullet with no colour in it would soften the
        closing line for nothing."""
        live = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")
        for bullet in live["Faction"]:
            _, visual, flags = gen.split_faction(bullet)
            if "palette" not in flags:
                continue
            with self.subTest(bullet=bullet):
                self.assertIn(" in ", visual,
                              "a palette faction must name its colours: %s" % bullet)
```

Add `REPO` to the imports at the top of the file:

```python
from test.helpers import FIXTURE_TABLES, REPO, load_generator
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python -m unittest test.test_faction.TestFactionPigment -v`
Expected: FAIL — `'only other saturated color' not found`.

- [ ] **Step 3: Parameterise the closing line**

In `generate-npc.py`, replace the glow constants with:

```python
# The forms the closing palette line takes. Two dimensions: whether anything
# rolled for this NPC could cast a glow (has_light_source), and whether the
# rolled Faction asserts pigment of its own ('|| palette').
#
# Pigment and light are different things and coexist happily - a green-and-gold
# Harrison uniform lit by a red instrument glow reads correctly - but the
# line's claim that the glow is the ONLY saturated colour stops being true when
# the uniform has one, so {other} softens it. Four constants and one slot
# rather than eight constants.
GLOW_PORTRAIT = (
    "A faint {glow} glow falls across one side of {possessive} face against "
    "warm dim ambient light on the other. Keep the palette restrained - greys, "
    "olive drab and rust - with {glow} the only {other}saturated color in the frame."
)
GLOW_TOKEN = (
    "Keep the palette restrained - greys, olive drab and rust - with a single "
    "{glow} glow the only {other}saturated color."
)
GLOW_NONE = (
    "Keep the palette restrained - greys, olive drab and rust, with no stray "
    "saturated color."
)
GLOW_NONE_PIGMENT = (
    "Keep the rest of the palette restrained - greys, olive drab and rust."
)
```

In `build_prompts`, after the `faction_line` block from Task 7:

```python
    pigment = "palette" in faction_flags
    fields["other"] = "other " if pigment else ""
    none_line = GLOW_NONE_PIGMENT if pigment else GLOW_NONE
```

and change the two `accent_line=` expressions to:

```python
    portrait_fields = dict(
        fields, gear_line="" if "nogear" in flags else carrying,
        accent_line=(GLOW_PORTRAIT if portrait_glow else none_line).format(**fields))
    token_fields = dict(
        fields, gear_line=carrying,
        accent_line=(GLOW_TOKEN if equipped_glow else none_line).format(**fields))
```

- [ ] **Step 4: Run the pigment test**

Run: `python -m unittest test.test_faction.TestFactionPigment -v`
Expected: three PASS, `test_every_pigment_faction_actually_names_a_colour` passes vacuously (no `palette` flags in the table yet).

- [ ] **Step 5: Write the Faction content**

Replace `## Faction`'s bullets. Keep each visual under about twelve words — the budget check in Step 7 is the gate.

```
- x2 Unaligned || || civ
- x2 Union Administrative Department || issued and worn thin, in faded institutional blue-grey || mil palette
- Harrison Armory || sharply pressed, high collar and polished fittings, in imperial green and gold || mil palette
- Smith-Shimano Corpro || precisely tailored with fine seam piping, in white and pale pastels || civ palette
- IPS-Northstar || riveted and salt-stained heavy canvas, in rust orange || civ palette
- Karrakin Trade Baronies || formal heraldic livery with a stiff standing collar, in deep crimson and gold || palette
- Colonial militia || mismatched surplus, webbing straps and taped-over insignia || mil
- Unregistered || || 
```

Replace the table's comment with:

```
<!--
  Three segments: the affiliation NAME, the visual signature, then flags.

  The name is what the dossier and the Import GUI print. The visual is the
  only part that reaches the image prompt, and it is what makes this table
  worth having at all: the old single-segment form put a garment CATEGORY
  ("corporate wear", "service dress") straight after Outfit's specific garment
  description, competing for the same slot and losing every time. Deleting the
  whole Faction clause from a prompt changed the render not at all.

  So a visual describes what Outfit does not - fabric, tailoring, insignia,
  patina, and where the faction has one, colour. Never a garment category.

  Two entries are non-affiliations with nothing to show and leave the visual
  empty; build_prompts() then drops the clause entirely rather than leaving a
  doubled comma.

  '|| palette' marks a faction that asserts colours of its own. Those are
  PIGMENT - dye in cloth - and they coexist with the Glow colour, which is
  LIGHT. The closing palette line softens from "the only saturated color" to
  "the only other saturated color" when one is rolled, so the prompt stops
  claiming something the uniform contradicts. A faction without a colour
  scheme should NOT carry the flag: Unaligned, Unregistered and the colonial
  militia deliberately leave the palette unconstrained.

  Keep visuals to about a dozen words. Both prompts run close to Krea 2's
  512-token ceiling - see test/test_prompt_budget.py.
-->
```

- [ ] **Step 6: Run the faction tests**

Run: `python -m unittest test.test_faction -v`
Expected: PASS, 12 tests.

- [ ] **Step 7: Check the budget — this is the gate**

Run: `python -m test.prompt_budget`
Expected: token p99 **below 512**, and ideally at or below the Task 3 figure.

If p99 has regressed above 512: shorten the Faction visuals, starting with the longest (Karrakin, then Harrison Armory). Do **not** relax the test or raise `TOKEN_LIMIT`. Re-run until green.

- [ ] **Step 8: Run the full suite**

Run: `python -m unittest discover -s test -t . 2>&1 | tail -5`
Expected: `OK`, 129 tests.

- [ ] **Step 9: Eyeball a real dry run**

Run: `python generate-npc.py --seed 1 --count 5 --dry-run 2>&1 | head -60`
Confirm by reading: the byline reads `"Callsign" - a role, Smith-Shimano Corpro.` rather than the old clothing clause; the clothing sentence carries the visual signature and not the proper noun; an `Unaligned` roll has no orphaned comma.

- [ ] **Step 10: Commit**

```bash
git add generate-npc.py prompts/npc-generator-tables.md test/test_faction.py
git commit -m "feat: give Faction a visual signature, and let pigment sit beside light

Each faction now carries a signature written on the axes Outfit leaves free -
fabric, tailoring, insignia, patina, and colour where the faction has a
scheme. Five assert pigment and carry '|| palette'; Unaligned, Unregistered
and the colonial militia leave the palette unconstrained on purpose. Pigment
and the Glow colour coexist, so the closing line softens to 'the only other
saturated color' rather than claiming an exclusivity the uniform contradicts."
```

---

### Task 9: Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/generate-npc.md`

**Interfaces:**
- Consumes: everything above.
- Produces: nothing.

- [ ] **Step 1: Find every stale reference**

Run:

```bash
grep -rn "Accent\|accent\|electric blue\|neon cyan\|standing at full height" README.md docs/*.md
```

Expected: a list of references to update. Every hit is either a rename (`Accent` → `Glow colour`), a renamed colour, or template prose changed in Task 2.

- [ ] **Step 2: Update `docs/generate-npc.md`**

- Rename `Accent` to `Glow colour` throughout, including any trait-table listing.
- Document `--unarmed` in the flags section, with the tiering stated: military Roles and Criminals stay armed.
- Update any reproduced Token template text to Task 2's wording.
- Add `Faction`'s three-segment shape to whatever section describes the `||` conventions, alongside `Backdrop` and `Hair colour`.

- [ ] **Step 3: Update `README.md`**

Same rename sweep. If the README lists CLI flags, add `--unarmed`.

- [ ] **Step 4: Confirm nothing stale remains**

Run:

```bash
grep -rn "Accent\|electric blue\|neon cyan\|standing at full height" README.md docs/ prompts/npc-generator-tables.md generate-npc.py test/ | grep -v "docs/superpowers/" | grep -v "LEGACY_TRAIT_NAMES" | grep -v "test_glow_rename"
```

Expected: no output. The exclusions are deliberate — the spec and plan record the old names as history, `LEGACY_TRAIT_NAMES` maps them forward, and `test_glow_rename.py` tests that mapping.

- [ ] **Step 5: Run the full suite one last time**

Run: `python -m unittest discover -s test -t . 2>&1 | tail -5`
Expected: `OK`, 129 tests.

Run: `python -m test.prompt_budget`
Expected: token p99 below 512 with headroom to spare.

- [ ] **Step 6: Commit**

```bash
git add README.md docs/generate-npc.md
git commit -m "docs: record --unarmed, the Glow colour rename and Faction's new shape"
```

---

## Handoff to the GUI plan

Once this plan is complete, `lancer-npc-import-gui`'s plan can start. It depends on:

- `--unarmed` existing on `generate-npc.py` (Task 5).
- `REQUIRED_TABLES` naming `Glow colour` rather than `Accent` (Task 1) — the GUI derives its trait-override list from it.

Nothing else crosses the boundary.
