# Headgear/Outfit Register Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop the generator pairing an elaborate or traditional Outfit with sealed, powered or instrumented Headgear, without losing the Headgear re-roll button.

**Architecture:** One new flag, `hardtech`, on 39 of the 64 base Headgear bullets, and one filter that drops those bullets when the rolled Outfit carries the existing `notac` flag. `Headgear` already follows `Outfit` in `REQUIRED_TABLES`, so no reorder is needed and no Outfit bullet changes. Because gating a trait on another trait's flag is what makes a trait un-re-rollable, the Outfit's register is recorded in the manifest as `outfit_notac`, following the `young` precedent, and `reroll_trait()` reads it back.

**Tech Stack:** Python 3 standard library only; `unittest` run as `python -m unittest discover -s test -t .`. No dependencies are added.

**Spec:** [`docs/superpowers/specs/2026-09-04-headgear-outfit-register-design.md`](../specs/2026-09-04-headgear-outfit-register-design.md)

## Global Constraints

- **Never filter a pool to nothing.** Every filter in `roll_npc()` ends `return narrowed or options`. The new one does too.
- **Flags are stripped before a value reaches a prompt or a dossier.** `Headgear` is already in the strip list at `generate-npc.py:994`; do not remove it.
- **`notac` is not `dressy`.** The gate keys on `notac`. Do not merge, rename or retire either flag.
- **Do not add `mil` or `civ` to Headgear bullets.** `Headgear` is not in `filter_by_mil()` and must not be added to it in this change.
- **`Headgear` must stay in `REROLLABLE_TRAITS`.** The import GUI derives its Re-roll buttons from that tuple.
- **Prompt length must not grow.** `test/prompt_budget.py` p99 is 485 for the portrait; this change swaps clauses and adds none.
- **House commit style:** `feat:` / `docs:` / `fix:` subject, then prose paragraphs explaining the reasoning — no bullet lists. Every commit message ends with the two trailer lines used elsewhere in this branch.

---

## File Structure

| File | Responsibility in this change |
|---|---|
| `prompts/npc-generator-tables.md` | Carries the 39 `\|\| hardtech` flags, and the preamble sentence that documents the flag. The change *is* this file, mostly. |
| `generate-npc.py` | `filter_by_hardtech()`, its two call sites (`roll_npc()`, `reroll_trait()`), and the `outfit_notac` manifest key at three sites. |
| `test/fixtures/tables-minimal.md` | Gains one `hardtech` Headgear bullet so the gate is reachable from a fixture roll. |
| `test/test_headgear_register.py` | New. Every behavioural claim in spec §8. |
| `docs/generate-npc.md` | The prose reference: a `hardtech` subsection beside the `dressy` one, and the flag summary. |
| `.claude/skills/npc-trait-import/SKILL.md` | So newly staged Headgear entries get classified rather than landing unflagged. |

---

### Task 1: Flag the table and gate the roll

**Files:**
- Modify: `prompts/npc-generator-tables.md` (Headgear table at `:1296`; `||` preamble at `:30`)
- Modify: `generate-npc.py` (new function after `filter_by_dress()` at `:588`; call site after the Weapon/Gear `notac` block at `:949`)
- Modify: `test/fixtures/tables-minimal.md` (Headgear table at `:73`)
- Test: `test/test_headgear_register.py` (create)

**Interfaces:**
- Consumes: `split_flags(bullet) -> (value, flags_list)`, `bullets_for(tables, name)` from `test.helpers`, the existing `outfit_notac` local in `roll_npc()`.
- Produces: `filter_by_hardtech(options, outfit_notac) -> list`, used again by Task 2.

- [ ] **Step 1: Add the fixture bullet the tests need**

The fixture Headgear table has two bullets and no flagged one, so a fixture roll can never exercise the gate. Add a third. Keep it short — the fixture feeds prompt-shape tests.

In `test/fixtures/tables-minimal.md`, the `## Headgear` block becomes:

```markdown
## Headgear
- {Subject} {is_are} bare-headed.
- {Subject} {wear} a wide woven hat. || @alpha
- {Subject} {wear} a sealed flight helmet. || hardtech
```

The fixture already carries `- an elaborate floral kimono || civ notac dressy` in its `## Outfit`, so no Outfit edit is needed here either.

- [ ] **Step 2: Write the failing tests**

Create `test/test_headgear_register.py`:

```python
"""An Outfit flagged 'notac' does not pair with 'hardtech' Headgear.

A rolled corporate liaison came out in an elaborate floral kimono with a
sealed flight helmet over it - dressed for a reception from the neck down and
for a cockpit from the neck up. 'notac' already means "do not pair this with
tactical gear" and already gates Weapon and Gear; it had simply never reached
the third thing an NPC wears.

'hardtech' is deliberately not 'mil'. Half the clash is technical rather than
military - a cybernetic ear implant and a mechanical diagnostic rig fight a
kimono and neither is army kit - and Headgear is not in filter_by_mil().

See docs/superpowers/specs/2026-09-04-headgear-outfit-register-design.md.
"""
import random
import unittest

from test.helpers import FIXTURE_TABLES, REPO, bullets_for, load_generator

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")

KIMONO = "an elaborate floral kimono || civ notac dressy"


def roll(seed, **overrides):
    return gen.roll_npc(TABLES, random.Random(seed), overrides or None)


def hardtech_headgear(tables):
    """The rendered values of every 'hardtech' bullet, variants included."""
    return {gen.split_flags(b)[0] for b in bullets_for(tables, "Headgear")
            if "hardtech" in gen.split_flags(b)[1]}


def notac_outfits(tables):
    return {gen.split_flags(b)[0] for b in bullets_for(tables, "Outfit")
            if "notac" in gen.split_flags(b)[1]}


class TestTheFilter(unittest.TestCase):
    def test_it_drops_only_the_hardtech_ones(self):
        options = ["bare-headed.", "a helmet. || hardtech", "a straw hat. || @alpha"]
        self.assertEqual(
            gen.filter_by_hardtech(options, True),
            ["bare-headed.", "a straw hat. || @alpha"])

    def test_an_untac_outfit_filters_nothing(self):
        options = ["bare-headed.", "a helmet. || hardtech"]
        self.assertEqual(gen.filter_by_hardtech(options, False), options)

    def test_the_pool_is_never_filtered_to_nothing(self):
        """The starvation guard. It cannot fire on today's content - no
        Headgear bullet carries a theme tag, so filter_by_theme() never
        narrows this pool first - but Phase 4 will change that."""
        options = ["a helmet. || hardtech", "a visor rig. || hardtech"]
        self.assertEqual(gen.filter_by_hardtech(options, True), options)


class TestTheRollIsGated(unittest.TestCase):
    def test_a_notac_outfit_never_rolls_hardtech_headgear(self):
        hardtech = hardtech_headgear(TABLES)
        self.assertTrue(hardtech, "fixture needs a hardtech bullet to avoid")
        for seed in range(400):
            npc = roll(seed, Outfit=KIMONO)
            self.assertNotIn(
                npc["Headgear"], hardtech,
                "seed %d: a kimono rolled hard tech on its head" % seed)

    def test_an_ordinary_outfit_still_reaches_hardtech_headgear(self):
        """The other half of the gate. Filtering it for everyone would pass
        the test above while making 39 live bullets dead content."""
        hardtech = hardtech_headgear(TABLES)
        reached = 0
        for seed in range(400):
            npc = roll(seed, Outfit="grey coveralls")
            if npc["Headgear"] in hardtech:
                reached += 1
        self.assertTrue(reached, "no ordinary outfit ever reached hard tech")

    def test_a_gated_roll_still_has_somewhere_to_go(self):
        """Variety, not just legality: a kimono must reach more than one
        headgear, or the gate has replaced a clash with a uniform."""
        seen = {roll(seed, Outfit=KIMONO)["Headgear"] for seed in range(400)}
        self.assertGreater(len(seen), 1)

    def test_the_flag_never_reaches_a_prompt(self):
        for seed in range(200):
            npc = roll(seed)
            self.assertNotIn("hardtech", npc["Headgear"])
            for prompt in gen.build_prompts(npc):
                self.assertNotIn("hardtech", prompt)


class TestTheLiveTable(unittest.TestCase):
    def test_a_notac_outfit_keeps_a_varied_live_pool(self):
        """The live numbers the spec commits to, asserted as floors rather
        than equalities so adding a bullet does not fail the suite."""
        pool = [b for b in bullets_for(LIVE, "Headgear")
                if "hardtech" not in gen.split_flags(b)[1]]
        self.assertGreaterEqual(len(pool), 25)

    def test_the_traditional_register_survives_the_gate(self):
        """The point of gating on 'notac' rather than banning headgear: a
        kimono should still reach a kabuto."""
        pool = " ".join(b for b in bullets_for(LIVE, "Headgear")
                        if "hardtech" not in gen.split_flags(b)[1])
        for wanted in ("kabuto", "lacquered", "straw hat"):
            self.assertIn(wanted, pool)

    def test_every_sealed_helmet_is_flagged(self):
        """A spot-check on the classification itself. These four are the
        least arguable members of the set; if one is unflagged, the table
        edit was incomplete."""
        hardtech = " ".join(b for b in bullets_for(LIVE, "Headgear")
                            if "hardtech" in gen.split_flags(b)[1])
        for wanted in ("full flight helmet", "night-vision helmet",
                       "sealed tactical helmet", "respirator mask"):
            self.assertIn(wanted, hardtech)

    def test_no_headgear_bullet_carries_civ_or_mil(self):
        """Headgear is not in filter_by_mil(), so those flags would be inert
        and misleading. The spec rejects them by name."""
        for bullet in bullets_for(LIVE, "Headgear"):
            flags = gen.split_flags(bullet)[1]
            self.assertNotIn("civ", flags)
            self.assertNotIn("mil", flags)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests and watch them fail**

Run: `python -m unittest test.test_headgear_register -v`

Expected: errors, `AttributeError: module 'gennpc' has no attribute 'filter_by_hardtech'`, plus failures in `TestTheLiveTable` because no live bullet carries the flag yet.

- [ ] **Step 4: Add the filter**

In `generate-npc.py`, immediately after `filter_by_dress()` (which ends `return plain or options` at `:588`) and before `filter_by_mil()`:

```python
def filter_by_hardtech(options, outfit_notac):
    """Headgear flagged 'hardtech', dropped under an Outfit flagged 'notac'.

    'hardtech' is modern technology worn on the head: helmets sealed or open,
    visor and lens rigs, sensor and night-vision hardware, breather masks,
    comms headsets, anything strung with cabling or seated on jacks, and
    powered or cybernetic pieces. Not soft goods, not plain eyewear, and not
    the traditional register - a kimono wants a kabuto above it, and gets one.

    This is the third and last place 'notac' reaches. It already drops 'mil'
    bullets from Weapon and Gear so an elaborate outfit carries neither a
    military rifle nor a tactical pack; it had never reached what the NPC
    wears on their head, which is how a corporate liaison ended up in a floral
    kimono under a sealed flight helmet.

    Deliberately NOT keyed on 'mil'. That flag means "an actual issued
    uniform" on the two tables that carry it, Headgear is not in
    filter_by_mil(), and putting 'mil' on headgear bullets would invite
    someone to wire it in and quietly change what a civilian may wear. It is
    also the wrong word for a third of the set: a cybernetic ear implant, a
    mechanical diagnostic rig and a pair of retro-industrial headphones are
    none of them military and all three fight a kimono.
    """
    if not outfit_notac:
        return options
    soft = [x for x in options if "hardtech" not in split_flags(x)[1]]
    return soft or options        # never filter the pool down to nothing
```

- [ ] **Step 5: Call it from the roll**

In `roll_npc()`, directly after the existing block:

```python
        if name in ("Weapon", "Gear") and outfit_notac:
            no_mil = [x for x in options if "mil" not in split_flags(x)[1]]
            options = no_mil or options
```

add:

```python
        # The third thing an NPC wears. Outfit precedes Headgear in
        # REQUIRED_TABLES, so outfit_notac is already known here, the same way
        # role_mil is known by the time Faction and Outfit roll.
        if name == "Headgear" and outfit_notac:
            options = filter_by_hardtech(options, outfit_notac)
```

- [ ] **Step 6: Run the filter and roll tests**

Run: `python -m unittest test.test_headgear_register.TestTheFilter test.test_headgear_register.TestTheRollIsGated -v`

Expected: PASS. `TestTheLiveTable` still fails — the live table is untouched so far.

- [ ] **Step 7: Flag the live table**

In `prompts/npc-generator-tables.md`, append ` || hardtech` to these 39 bullets under `## Headgear`. All four bullets under `## Headgear (she) +` stay unflagged.

Flag — helmets and full enclosures: the padded pilot skullcap with the folded visor; the composite ballistic helmet; the full flight helmet in scuffed pale grey-white; the night-vision helmet; the hooded shroud over a full-face helmet; the open-face crash helmet; the ballistic helmet with the black breather mask; the sleek pilot's helmet with HUD readouts; the scuffed recon helmet; the domed burnt-orange flight helmet; the sealed tactical helmet; the smooth blue-visored full-face helmet under a hood; the sleek angular powered helmet.

Flag — visor and lens rigs: the monocular sensor rig over one eye; the sleek integrated visor plate; the bulky visored rig with the stub antenna; the bulky illuminated graffitied visor rig; the curved white ear plate with the antenna horn; the sleek red-tinted visor skullcap; the compact visor rig pushed above the brow; the compact sensor rig clipped into the hair; the slim translucent visor band; the red-plated visor rig; the sleek visored headset with the hinged jaw guard; the russet leather flight cap with the monocular scanner lens.

Flag — comms and audio hardware: the padded flight headset with the boom mic; the lightweight comms earpiece; the sleek black mechanical ear headset; the compact red-panelled over-ear headset; the boxy retro-industrial headphones; the chunky over-ear headset with the lit accent rings.

Flag — masks and cybernetics: the sleek mechanical half-mask; the close-fitted respirator under narrow tactical eyewear; the segmented cybernetic ear-and-jaw implant; the segmented white cybernetic headpiece; the bulky mechanical diagnostic rig.

Flag — tactical and industrial: the tactical cap with dark sunglasses; the heavy ear defenders; the welding visor.

Leave unflagged, all 25: bare-headed; the scratched flight goggles pushed up; the soft crew cap; the rolled bandana; the knitted watch cap; the ushanka with the unit star; the stiff peaked officer's cap; the deep hood with goggles clipped to it; the flat-brimmed ball cap; the wide woven sedge hat; the pale cloth under a straw hat; the gold-trimmed ear headset; the round wire-rimmed glasses; the tinted wraparound sunglasses; the lacquered bird-skull hat; the thin rectangular glasses; both horned kabuto helmets; the gold-rimmed lacquered hat with the red tassel; the woven hat with horns, tassels and a mask beneath; the straw hat with hanging bells; the broad ceremonial hat with tasseled bells; the spiked woven hat; the dark hat with chain ornaments and a feather crest; the straw hat over a cloth headband.

The three judgement calls, so they are not silently reversed later: the gold-trimmed ear headset stays unflagged although the other two ear headsets are flagged, because the gilding is a deliberate signal that it belongs with fine dress; the officer's cap stays unflagged because it is cloth and formal and belongs to the dress-uniform register; both kabuto stay unflagged because `hardtech` is about modern technology, not head coverage.

- [ ] **Step 8: Add the flag to the tables-file preamble**

`npc-generator-tables.md:30` opens a list introduced by "`||` splits a bullet into segments. Twelve tables use it:". Change "Twelve" to "Thirteen" and add a bullet after the Outfit/Faction one:

```markdown
- **Headgear** bullets may carry `|| hardtech`, marking modern technology worn
  on the head — helmets sealed or open, visor and lens rigs, sensor and
  night-vision hardware, breather masks, comms headsets, anything strung with
  cabling or seated on jacks, and powered or cybernetic pieces. Those bullets
  are dropped whenever the Outfit roll came up `notac`, so an elaborate or
  traditional outfit is not crowned with a sealed flight helmet. Soft goods —
  cloth, straw, woven, leather and fur hats, caps, hoods, bandanas and
  headbands — plain eyewear, and the traditional and ceremonial register are
  all deliberately unflagged: those are what a kimono *should* reach. Goggles
  count as eyewear, not hardware. A traditional hat with a mask beneath it is
  the hat, not the mask.
```

Verify the count first — `grep -c '^- \*\*' ` over that list — rather than trusting "Twelve".

- [ ] **Step 9: Run the whole suite**

Run: `python -m unittest discover -s test -t . -v`

Expected: every test passes, including the pre-existing 191. If a theme or budget test moved, the fixture bullet in Step 1 is the suspect — it is neutral (no `@` tag) and so is reachable from every theme by design.

- [ ] **Step 10: Commit**

```bash
git add prompts/npc-generator-tables.md generate-npc.py test/fixtures/tables-minimal.md test/test_headgear_register.py
git commit -F <message file>
```

Subject: `feat: keep hard tech off an outfit that is already flagged 'notac'`. The body argues why `hardtech` rather than `mil` (see the docstring in Step 4), why `notac` rather than `dressy`, and names the three judgement calls from Step 7.

---

### Task 2: Keep Headgear re-rollable

**Files:**
- Modify: `generate-npc.py` (`roll_npc()` at `:1010`; `regenerate_one()` at `:1997` and `:2115`; the fresh-roll entry at `:2322`; `reroll_trait()` at `:1941`)
- Test: `test/test_headgear_register.py` (extend)

**Interfaces:**
- Consumes: `filter_by_hardtech(options, outfit_notac)` from Task 1.
- Produces: `npc["_outfit_notac"]` (bool from a live roll, `None` from an entry that predates the key) and the manifest key `outfit_notac`.

- [ ] **Step 1: Write the failing tests**

Append to `test/test_headgear_register.py`:

```python
class TestTheRegisterIsRecorded(unittest.TestCase):
    def test_a_roll_records_the_outfits_register(self):
        self.assertTrue(roll(0, Outfit=KIMONO)["_outfit_notac"])
        self.assertFalse(roll(0, Outfit="grey coveralls")["_outfit_notac"])

    def test_headgear_is_still_rerollable(self):
        """The whole reason the key exists. Gating Headgear on another
        trait's flag is exactly what puts a trait in UNREROLLABLE_REASONS,
        and the import GUI builds its Re-roll buttons from this tuple."""
        self.assertIn("Headgear", gen.REROLLABLE_TRAITS)
        self.assertNotIn("Headgear", gen.UNREROLLABLE_REASONS)


class TestTheRerollRespectsIt(unittest.TestCase):
    def _entry_npc(self, register):
        npc = roll(0, Outfit=KIMONO)
        npc["_outfit_notac"] = register
        return npc

    def test_a_recorded_notac_outfit_never_rerolls_into_hardtech(self):
        hardtech = hardtech_headgear(TABLES)
        npc = self._entry_npc(True)
        for seed in range(200):
            value = gen.reroll_trait(TABLES, npc, "Headgear", random.Random(seed))
            self.assertNotIn(value, hardtech, "seed %d" % seed)

    def test_a_recorded_plain_outfit_still_reaches_hardtech(self):
        hardtech = hardtech_headgear(TABLES)
        npc = self._entry_npc(False)
        reached = sum(
            gen.reroll_trait(TABLES, npc, "Headgear", random.Random(seed)) in hardtech
            for seed in range(200))
        self.assertTrue(reached)

    def test_an_entry_predating_the_key_rerolls_unrestricted(self):
        """None is 'not recorded', which is not the same as False. It must
        behave as it did before this change rather than silently claiming
        the outfit was plain."""
        hardtech = hardtech_headgear(TABLES)
        npc = self._entry_npc(None)
        reached = sum(
            gen.reroll_trait(TABLES, npc, "Headgear", random.Random(seed)) in hardtech
            for seed in range(200))
        self.assertTrue(reached)

    def test_rerolling_something_else_is_unaffected(self):
        npc = self._entry_npc(True)
        before = dict(npc)
        gen.reroll_trait(TABLES, npc, "Eyes", random.Random(0))
        self.assertEqual(npc["Headgear"], before["Headgear"])
```

- [ ] **Step 2: Run them and watch them fail**

Run: `python -m unittest test.test_headgear_register.TestTheRegisterIsRecorded test.test_headgear_register.TestTheRerollRespectsIt -v`

Expected: `KeyError: '_outfit_notac'` on the first, and the re-roll tests failing because `reroll_trait()` ignores the register.

- [ ] **Step 3: Record it on the rolled NPC**

In `roll_npc()`, beside the line that already publishes the other flag:

```python
    npc["_young"] = young
    # The Outfit's register, published for the same reason '_young' is: the
    # manifest stores Outfit with its flags stripped, so without this a
    # Headgear re-roll could not tell whether it was gated, and Headgear would
    # have to leave REROLLABLE_TRAITS - taking its button in the import GUI
    # with it. See the raw-bullets spec, which generalises this and subsumes
    # both keys.
    npc["_outfit_notac"] = outfit_notac
```

- [ ] **Step 4: Honour it in the re-roll**

In `reroll_trait()`, after the `Glow placement` / `scene` branch and before `value = split_flags(rng.choice(options))[0]`:

```python
    # 'hardtech' against the recorded outfit register. None means the entry
    # predates the key, which is not the same as False: it is "nobody knows",
    # and the honest answer is today's unrestricted behaviour plus a warning.
    if name == "Headgear":
        register = npc.get("_outfit_notac")
        if register is None:
            print("! this entry has no recorded outfit register (written before "
                  "the Headgear register existed) - re-rolling headgear "
                  "unrestricted, so it may come back with hard tech over a "
                  "traditional outfit. Re-roll the NPC to record it.",
                  file=sys.stderr)
        options = filter_by_hardtech(options, bool(register))
```

- [ ] **Step 5: Read it back and write it out**

In `regenerate_one()`, after `npc["_young"] = entry.get("young", False)`:

```python
    # No default: absent is 'not recorded', which reroll_trait() distinguishes
    # from a recorded False. Unlike 'young' this is not consumed by
    # build_prompts(), so a plain regen neither needs it nor warns about it.
    npc["_outfit_notac"] = entry.get("outfit_notac")
```

In the same function's manifest rewrite, after `entry["young"] = npc["_young"]`:

```python
    # Only when it is known. Rewriting a pre-key entry with a fabricated False
    # would claim the outfit is not 'notac' when nothing here knows either way.
    if npc.get("_outfit_notac") is not None:
        entry["outfit_notac"] = npc["_outfit_notac"]
```

In the fresh-roll entry literal, after `"young": npc["_young"],`:

```python
            # Not a table roll either, and stored for the same reason: a
            # Headgear re-roll needs the Outfit's 'notac' flag, and traits are
            # saved with their flags already stripped.
            "outfit_notac": npc["_outfit_notac"],
```

- [ ] **Step 6: Run the suite**

Run: `python -m unittest discover -s test -t . -v`

Expected: all pass. `test/test_reroll_trait.py` is the one to watch — it exercises `reroll_trait()` on NPCs built by `roll_npc()`, which now always carry a real bool, so the warning branch should not fire there.

- [ ] **Step 7: Verify the manifest round-trip by hand**

Run: `python generate-npc.py --count 1 --seed 7 --dry-run`

Expected: it rolls and prints without raising. Then confirm the key reaches a written entry by checking the writer, since `--dry-run` queues nothing:

Run: `python -c "import importlib.util,sys,pathlib;s=importlib.util.spec_from_file_location('g','generate-npc.py');m=importlib.util.module_from_spec(s);sys.modules['g']=m;s.loader.exec_module(m);import random;n=m.roll_npc(m.parse_tables(pathlib.Path('prompts/npc-generator-tables.md')),random.Random(7),None);print(n['_outfit_notac'])"`

Expected: `True` or `False`, not a traceback.

- [ ] **Step 8: Commit**

```bash
git add generate-npc.py test/test_headgear_register.py
git commit -F <message file>
```

Subject: `feat: record the outfit's register so Headgear stays re-rollable`. The body explains that gating a trait on another trait's flag is what fills `UNREROLLABLE_REASONS`, that `young` is the precedent the file names itself, and that `None` is deliberately distinct from `False`.

---

### Task 3: Documentation and the import skill

**Files:**
- Modify: `docs/generate-npc.md` (the dress-register prose ends at `:449`; the re-roll table at `:694`)
- Modify: `.claude/skills/npc-trait-import/SKILL.md` (flag table at `:48`; per-table shapes at `:297-298`)

**Interfaces:**
- Consumes: the flag name `hardtech` and the classification rule from Task 1. Nothing consumes this task.

- [ ] **Step 1: Add the reference prose**

In `docs/generate-npc.md`, after the dress-register section that ends with the measured-over-4000-rolls paragraph at `:449`, add:

```markdown
### Headgear register

`notac` reaches a third table. It already means "do not pair this with tactical
gear" and already drops `mil` bullets from Weapon and Gear; a `hardtech`
Headgear bullet is now dropped the same way, so an elaborate or traditional
outfit is not crowned with a sealed flight helmet. `Headgear` follows `Outfit`
in `REQUIRED_TABLES`, so the flag is in hand when the pool is assembled.

`hardtech` is **not** `mil`, and the shortcut is tempting because the Weapon
and Gear filter already keys on `mil`. `mil` means "an actual issued uniform"
on `Faction` and `Outfit`, `Headgear` is not in `filter_by_mil()`, and a `mil`
flag sitting on headgear bullets would invite someone to wire it in and quietly
change what a civilian may wear. It is also the wrong word for roughly a third
of the set — a cybernetic ear implant, a mechanical diagnostic rig and a pair of
retro-industrial headphones are none of them military and all three fight a
kimono.

`hardtech` is **not** `dressy` either. `dressy` asks whether a Role may be seen
in finery; this asks whether a garment sits alongside hard kit. The seven
bullets the two disagree on — the pilgrim's robes, the ragged bindings, the
travel-worn robe — are exactly the ones this must also cover: a pilgrim under a
night-vision helmet is the same bug as a liaison in a kimono.

39 of the 64 base Headgear bullets carry it; all 4 in `Headgear (she) +` do not.
A `notac` outfit still draws from 25 bullets, 30 by weight, including the whole
traditional register — both kabuto, both lacquered hats, the straw and woven
hats — which is the point rather than a consolation.

The reverse gate is deliberately absent: a combat uniform can still roll a
horned kabuto. Doing it properly needs a second value on the same axis and a
decision about which Outfits reject it, which is not simply `mil`.
```

- [ ] **Step 2: Note the manifest key beside the re-roll table**

Immediately after the `| **Refused** |` row at `:695`, add:

```markdown
`Headgear` is gated by the Outfit's `notac` flag and stays re-rollable only
because the entry records it: `outfit_notac` is a manifest key of its own,
beside `young`, for the same reason `young` is one. An entry written before
that key re-rolls headgear unrestricted and says so on stderr.
```

- [ ] **Step 3: Teach the import skill the flag**

In `.claude/skills/npc-trait-import/SKILL.md`, add a row to the flag table after the `notac` row at `:48`:

```markdown
| `hardtech` | Headgear | Modern technology worn on the head — helmets sealed or open, visor and lens rigs, sensor/night-vision hardware, breather masks, comms headsets, anything cabled or jacked, powered or cybernetic pieces, plus industrial eye and ear protection. Dropped when the Outfit roll came up `notac`. **Not** soft goods (cloth, straw, woven, leather, fur — hats, caps, hoods, bandanas, headbands), **not** plain eyewear, and **not** the traditional or ceremonial register: those are what an elaborate outfit *should* reach. Goggles are eyewear, not hardware. A traditional hat with a mask beneath it is the hat. |
```

Then correct the two per-table shape lines at `:297-298`:

```markdown
- **Outfit**: `<noun phrase clause> || [civ] [mil] [notac] [dressy]`
- **Headgear**: `{Subject} {wear} <full sentence>. || [hardtech]`
```

The `dressy` addition is a pre-existing omission — the dress-register change added the flag and never updated this line. Fixing it here keeps a staged import from landing an unflagged ceremonial outfit.

- [ ] **Step 4: Check the docs against the code**

Run: `grep -n "hardtech" docs/generate-npc.md prompts/npc-generator-tables.md generate-npc.py .claude/skills/npc-trait-import/SKILL.md | wc -l`

Expected: a non-zero count in all four files. Then re-read the new prose once against `filter_by_hardtech()`'s docstring — they must not disagree about what the flag means.

- [ ] **Step 5: Commit**

```bash
git add docs/generate-npc.md .claude/skills/npc-trait-import/SKILL.md
git commit -F <message file>
```

Subject: `docs: document the headgear register, and give the import skill the flag`.

---

### Task 4: Measured verification

**Files:**
- Modify: none. This task produces the numbers the Task 1 commit message claims and confirms nothing else moved.

**Interfaces:**
- Consumes: everything from Tasks 1-3.

- [ ] **Step 1: Count the flags against the spec**

Run: `grep -c 'hardtech' prompts/npc-generator-tables.md`

Expected: 40 — 39 bullets plus the one mention in the preamble added in Task 1 Step 8. If it is 39 or 41, one bullet was missed or double-flagged; reconcile against the lists in Task 1 Step 7 before continuing.

- [ ] **Step 2: Sweep several thousand rolls**

Run:

```bash
python - <<'PY'
import importlib.util, pathlib, random, sys
s = importlib.util.spec_from_file_location("g", "generate-npc.py")
m = importlib.util.module_from_spec(s); sys.modules["g"] = m; s.loader.exec_module(m)
T = m.parse_tables(pathlib.Path("prompts/npc-generator-tables.md"))
hard = {m.split_flags(b)[0] for k in T if k.startswith("Headgear")
        for b in T[k] if "hardtech" in m.split_flags(b)[1]}
notac_n = hard_on_notac = hard_total = 0
for seed in range(4000):
    npc = m.roll_npc(T, random.Random(seed), None)
    h = npc["Headgear"] in hard
    hard_total += h
    if npc["_outfit_notac"]:
        notac_n += 1
        hard_on_notac += h
print("notac NPCs: %d, of which hard tech: %d" % (notac_n, hard_on_notac))
print("hard tech overall: %d / 4000" % hard_total)
PY
```

Expected: `of which hard tech: 0`, and an overall count that is still a substantial fraction of 4000 — the gate must narrow the outfits it targets and nothing else. Record both numbers; they belong in the Task 1 commit message.

- [ ] **Step 3: Confirm the prompt budget did not move**

Run: `python -m unittest test.test_prompt_budget -v`

Expected: PASS, p99 unchanged at 485. This change swaps one clause for another and adds none, so a move here means something else was disturbed.

- [ ] **Step 4: Run the whole suite one last time**

Run: `python -m unittest discover -s test -t .`

Expected: all pass, with the count risen by the tests added in Tasks 1 and 2.

- [ ] **Step 5: Amend the Task 1 commit message with the measured numbers**

If Task 1 was committed with placeholder counts, `git commit --amend` on that commit is wrong once later commits sit on top of it. Instead put the numbers in the Task 4 verification note, or reword during the branch merge. Prefer writing Task 1's message *after* this task if the numbers are wanted in it.

---

## Self-Review

**Spec coverage.** §2 and §3 → Task 1 Steps 4-7. §2.1 and §2.2 (what `hardtech` means, why not `mil`) → Task 1 Step 4 docstring and Task 3 Step 1. §3.1 (why not `dressy`) → Task 3 Step 1. §4 (the classification) → Task 1 Step 7, with §4.2's three judgement calls named there. §5 (re-rollability) → Task 2 in full. §6 (raw-bullets relationship) → the comment in Task 2 Step 3; the raw-bullets spec itself already carries the reciprocal note. §7 (non-goals) → Task 3 Step 1's closing paragraph. §8 items 1-4 → Task 1 Steps 2 and 9 plus Task 4 Step 2; items 5-7 → Task 2 Step 1; item 8 → Task 2 Step 6 via the existing regen tests; item 9 → Task 4 Step 3; item 10 → Task 1 Step 2's `test_the_flag_never_reaches_a_prompt`.

One spec item has no task and is deliberate: §8 item 2 (forcing a `notac` Outfit with `--set-trait`) is covered by Task 1's roll tests, which force `Outfit=KIMONO` through the same override path `--set-trait` uses.

**Placeholder scan.** No TBDs. Every code step carries the code. Commit messages are described by subject and argument rather than written out, which is deliberate — the house style is prose that argues from what was found, and Task 4 supplies numbers two of them want.

**Type consistency.** `filter_by_hardtech(options, outfit_notac)` is defined in Task 1 Step 4 and called with that signature in Task 1 Step 5 and Task 2 Step 4. `npc["_outfit_notac"]` is a bool from `roll_npc()` (Task 2 Step 3) and `None`-or-bool from `regenerate_one()` (Task 2 Step 5); `reroll_trait()` handles both via `bool(register)` after checking `is None`, and the test at Task 2 Step 1 covers all three states. The manifest key is `outfit_notac` (no underscore prefix) at all three sites.
