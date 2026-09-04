# Glow Source Zones Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop the portrait asserting that a coloured light falls somewhere no rolled light source could have cast it, which makes the model paint the glow onto the figure as a hard-edged decal.

**Architecture:** Four new flags — `lit-face`, `lit-hands`, `lit-torso`, `lit-behind` — on the 35 bullets that genuinely emit light, and the same four on each `Glow placement` bullet naming the zones it will accept. At roll time the union of the rolled sources' zones is intersected with each placement's, at the filter site `roll_npc()` already runs for `scene`. `REQUIRED_TABLES` already orders all six source tables before `Glow placement`, so no reorder is needed. Costs zero prompt tokens: it changes which bullet is chosen, not what the sentence says.

**Tech Stack:** Python 3 standard library only; `unittest` run as `python -m unittest discover -s test -t .`. No dependencies are added.

**Spec:** [`docs/superpowers/specs/2026-09-04-glow-source-zones-design.md`](../specs/2026-09-04-glow-source-zones-design.md)

## Global Constraints

- **The zone flags are `lit-`-prefixed. This is not cosmetic.** The spec's §2 proposes a bare `hands`, which is **wrong and must not be implemented**: `hands` is already a flag meaning *this item occupies the hands*, read at `generate-npc.py:945`, `:1042`, `:1092`, `:1118` to gate the `Stance` roll. A bare `hands` on the wrist-interface Gear bullet would tell `Stance` both hands were full. Task 1 amends the spec. Use `lit-face`, `lit-hands`, `lit-torso`, `lit-behind` everywhere.
- **Never filter a pool to nothing.** Every filter in `roll_npc()` ends `narrowed or options`. The new one does too.
- **Flags are stripped before a value reaches a prompt or a dossier.** The strip list is at `generate-npc.py:1030`. `Eyes` is **not** in it today and gets no `split_flags()` call anywhere — Task 3 adds it, or `|| lit-face` ships verbatim into the image prompt.
- **`scene` is not `lit-behind`.** `scene` means the light is out in the environment and needs the *backdrop* to be the emitter. `lit-behind` means the light comes from behind the figure; a thruster pack qualifies and cannot stripe a wall. Do not merge, rename or retire either.
- **`Glow placement` must stay in `REROLLABLE_TRAITS`.** The import GUI derives its Re-roll buttons from that tuple.
- **Prompt length must not grow.** `test/prompt_budget.py` p99 is 485 portrait / 497 token against a 512 ceiling. This change adds no words to either template.
- **House commit style:** `feat:` / `docs:` / `fix:` subject where one fits, then prose paragraphs explaining the reasoning — no bullet lists. Every commit message ends with the two trailer lines used elsewhere in this branch.

---

## File Structure

| File | Responsibility in this change |
|---|---|
| `prompts/npc-generator-tables.md` | The 35 `lit-*` source flags, the zone flags on the placement table, three new placements, the `rakes across` reword, and the preamble comments documenting all of it. The change *is* mostly this file. |
| `generate-npc.py` | `REFLECTED_LIGHT`, `light_zones_for()`, the intersection at the two filter sites, `Eyes` added to the strip list, and the `light_zones` manifest key at three sites. |
| `test/test_glow_placement.py` | Extended: zone coverage, the intersection, the non-emitters. |
| `test/fixtures/tables-minimal.md`, `tables-themed.md` | Fixture sources and placements need zone flags or the filter is untested. |
| `docs/generate-npc.md` | The `## Glow placement` section documents the zone axis beside `scene`. |
| `.claude/skills/npc-trait-import/SKILL.md` | Emits `lit-*` for new source bullets; `test_import_skill_flags.py` fails otherwise. |
| `docs/superpowers/specs/2026-09-04-raw-bullets-in-the-manifest-design.md` | Its subsumed-keys list gains `light_zones`. |

---

### Task 1: Correct the spec's flag names before anything is built on them

**Files:**
- Modify: `docs/superpowers/specs/2026-09-04-glow-source-zones-design.md`

**Interfaces:**
- Consumes: nothing.
- Produces: the flag vocabulary every later task uses — `lit-face`, `lit-hands`, `lit-torso`, `lit-behind`.

- [ ] **Step 1: Confirm the collision is real**

Run: `grep -n '"hands"' generate-npc.py`

Expected: four hits at lines 945, 1042, 1092 and 1118, all testing a Weapon/Gear flag that gates `Stance`. This is what a bare `hands` zone flag would collide with.

- [ ] **Step 2: Amend §2 of the spec**

In `## 2. The zone vocabulary`, replace the zone-name column values `face`/`hands`/`torso`/`behind` with `lit-face`/`lit-hands`/`lit-torso`/`lit-behind`, and replace the sentence:

```
Flags are space-separated, exactly like the existing `|| hands mil weapon`.
```

with:

```
Flags are space-separated, like the existing `|| hands mil weapon`. They are
`lit-`-prefixed because `hands` is already taken: it means *this item occupies
the hands* and gates the `Stance` roll, so a bare `hands` zone on the
wrist-interface Gear bullet would claim both hands were full. The prefix also
makes the whole vocabulary greppable as one family.
```

Update the two `catches {possessive} jaw and one shoulder from below` examples in §2 and §5 to read `lit-face lit-hands`.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-09-04-glow-source-zones-design.md
git commit -m "docs: prefix the glow zone flags so they stop colliding with 'hands'"
```

---

### Task 2: Stop two reflective bullets licensing a glow

**Files:**
- Modify: `generate-npc.py:161-171` (`LIGHT_SOURCE_WORDS`, `has_light_source`)
- Test: `test/test_glow_placement.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `has_light_source(*texts) -> bool`, unchanged signature, now returning `False` for a bullet whose only match is a reflective "catching the light".

- [ ] **Step 1: Write the failing test**

Append to `test/test_glow_placement.py`:

```python
class TestReflectedLightIsNotASource(unittest.TestCase):
    """A surface catching light someone else cast is not an emitter.

    LIGHT_SOURCE_WORDS matches the bare word 'light', so these two bullets
    each switched the whole glow sentence on with nothing in frame to have
    cast it - the same failure this table exists to prevent, one layer down.
    The regex comment already excludes daylight for exactly this reason.
    """

    NON_EMITTING = (
        "amber-brown eyes catching the light",
        "{Subject} {wear} a horned kabuto-style helmet with a trailing neck "
        "guard, its crest catching the last light.",
    )

    def test_a_reflective_bullet_is_not_a_light_source(self):
        for bullet in self.NON_EMITTING:
            with self.subTest(bullet=bullet):
                self.assertFalse(gen.has_light_source(bullet))

    def test_a_real_emitter_still_counts_beside_a_reflection(self):
        """Stripping the reflective phrase must not deafen the rest of the bullet."""
        self.assertTrue(gen.has_light_source(
            "eyes catching the light above a collar lit with a status indicator"))

    def test_the_ordinary_emitters_still_count(self):
        for bullet in ("glowing red cybernetic eyes",
                       "a small pendant amulet glowing softly at the throat",
                       "the streets below threaded with cool running-lights"):
            with self.subTest(bullet=bullet):
                self.assertTrue(gen.has_light_source(bullet))
```

- [ ] **Step 2: Run it and watch it fail**

Run: `python -m unittest test.test_glow_placement -v`

Expected: `test_a_reflective_bullet_is_not_a_light_source` FAILS with `False is not true` — twice, once per subTest. The other two pass already; that is fine, they are regression guards for step 3.

- [ ] **Step 3: Implement**

In `generate-npc.py`, immediately after the `LIGHT_SOURCE_WORDS` definition, add:

```python
# Reflective, not emitting: a surface catching light something else cast.
# LIGHT_SOURCE_WORDS has to match the bare word 'light' so that "running-lights"
# and "status lights" count, and that let "eyes catching the light" and a kabuto
# crest "catching the last light" each license a glow with no emitter in frame.
# Stripped before the emitter test rather than excluded from it, so a bullet
# carrying both a reflection and a real light still counts as a source.
REFLECTED_LIGHT = re.compile(
    r"\bcatch\w*\s+(?:the\s+)?(?:last\s+)?light\b", re.IGNORECASE)
```

and change `has_light_source` to:

```python
def has_light_source(*texts):
    return any(LIGHT_SOURCE_WORDS.search(REFLECTED_LIGHT.sub(" ", text))
               for text in texts)
```

- [ ] **Step 4: Run the tests and watch them pass**

Run: `python -m unittest discover -s test -t .`

Expected: `OK`. If `test_glow_colours.py` or `test_prompt_budget.py` moved, that is a real signal — two bullets no longer trigger a glow line, so a handful of rolled NPCs now take `GLOW_NONE`. Re-baseline the budget numbers in step 5's commit message rather than reverting.

- [ ] **Step 5: Commit**

```bash
git add generate-npc.py test/test_glow_placement.py
git commit -m "fix: stop a reflection licensing a glow that has no emitter"
```

---

### Task 3: Zone-flag the source bullets

**Files:**
- Modify: `prompts/npc-generator-tables.md` (35 bullets across `Eyes`, `Feature`, `Headgear`, `Outfit`, `Weapon`, `Gear`, plus preamble)
- Modify: `generate-npc.py:1030` (strip list gains `Eyes`)
- Test: `test/test_glow_placement.py`

**Interfaces:**
- Consumes: `has_light_source()` from Task 2.
- Produces: every emitting bullet carries at least one of `lit-face`, `lit-hands`, `lit-torso`, `lit-behind` in its flag segment.

- [ ] **Step 1: Write the failing test**

Append to `test/test_glow_placement.py`:

First add the vocabulary to `generate-npc.py`, immediately after
`has_light_source`, so the tests read one source of truth rather than
re-declaring the names:

```python
# Where a source's light can land. 'lit-'-prefixed because a bare 'hands'
# already means "this item occupies the hands" and gates the Stance roll -
# see the Weapon policy and the Stance filter. Glow placement is filtered
# against the union of the zones a roll produced.
LIGHT_ZONES = ("lit-face", "lit-hands", "lit-torso", "lit-behind")
```

then append to `test/test_glow_placement.py`:

```python
ZONES = gen.LIGHT_ZONES
SOURCE_TABLES = ("Eyes", "Feature", "Headgear", "Outfit", "Weapon", "Gear")


class TestSourceZones(unittest.TestCase):
    """Every emitter says where its light can land; nothing else does.

    A source with no zone would be invisible to the filter and could license
    any placement at all, which is the bug this whole change exists to fix.
    """

    def _emitters(self):
        for name in SOURCE_TABLES:
            for bullet in bullets_for(LIVE, name):
                text, flags = gen.split_flags(bullet)
                if gen.has_light_source(text):
                    yield name, bullet, flags

    def test_the_scan_is_not_vacuous(self):
        self.assertGreater(len(list(self._emitters())), 25)

    def test_every_emitter_carries_a_zone(self):
        for name, bullet, flags in self._emitters():
            with self.subTest(table=name, bullet=bullet):
                self.assertTrue(
                    [f for f in flags if f in ZONES],
                    "this bullet emits light but never says where it lands, so "
                    "it would license every placement: %r" % bullet)

    def test_no_non_emitter_carries_a_zone(self):
        """A zone on a bullet that emits nothing is a copy-paste, not a source."""
        for name in SOURCE_TABLES:
            for bullet in bullets_for(LIVE, name):
                text, flags = gen.split_flags(bullet)
                if gen.has_light_source(text):
                    continue
                with self.subTest(table=name, bullet=bullet):
                    self.assertFalse([f for f in flags if f in ZONES], bullet)

    def test_no_zone_flag_shadows_the_hands_flag(self):
        """'hands' gates the Stance roll. The zone vocabulary must not reuse it."""
        self.assertNotIn("hands", ZONES)
```

- [ ] **Step 2: Run it and watch it fail**

Run: `python -m unittest test.test_glow_placement -v`

Expected: `test_every_emitter_carries_a_zone` FAILS once per emitting bullet (about 35 subTests), each naming the bullet.

- [ ] **Step 3: Add `Eyes` to the strip list**

`Eyes` has never carried a flag, so it is absent from the strip list and from every other `split_flags()` call site. Without this, `|| lit-face` ships verbatim into the image prompt.

In `generate-npc.py`, change:

```python
        if name in ("Age", "Build", "Role", "Outfit",
                    "Hair", "Feature", "Headgear", "Weapon", "Glow placement"):
```

to:

```python
        # 'Eyes' joined this list when the glow zones landed: it had never
        # carried a flag before, so an unstripped '|| lit-face' would have gone
        # straight into the prompt.
        if name in ("Age", "Build", "Role", "Outfit", "Eyes",
                    "Hair", "Feature", "Headgear", "Weapon", "Glow placement"):
```

- [ ] **Step 4: Flag the bullets**

Append the zone to each emitting bullet's existing flag segment, adding a `||` segment where there is none. The assignment, verbatim:

`lit-face` — every `Headgear` emitter (all 12 after Task 2 removes the kabuto-crest reflection); the two emitting `Eyes` (`one eye replaced by a matte optical implant with a faint glowing aperture`, `glowing red cybernetic eyes`); the three `Outfit` collar entries (`…a small status indicator lit at the collar`, `…a high collar piece lit with small accent glows`, `…status lights lit along the collar`); the `Gear` bullet `a small pendant amulet glowing softly at the throat`.

`lit-hands` — all four `Weapon` emitters; the `Gear` bullets `a slim wrist-mounted holographic interface projecting faint readouts`, `a fist-sized holographic sphere hovering just above one open palm…`, `a translucent holographic data-sheet held up in both hands…`, `an old-fashioned lantern glowing warm…`; the `Feature` bullets `a compact armored gauntlet on one forearm with a small glowing sensor ring` and `one sleek segmented prosthetic arm, a single small glow breaking through at the joint`.

`lit-torso` — the `Outfit` bullets `a powered load-bearing exo-frame…a status strip lit at the hip`, `a black tactical jacket…its interior lining faintly glowing…`, `a high-collared black tactical pilot jacket with glowing cable tubing threading down the front`, `a long dark coat lined with thin glowing cabling…`; the `Feature` bullet `both legs sleek mechanical prosthetics with exposed joints and a small lit panel at the thigh`.

`lit-behind` — the `Gear` bullets `a compact twin-thruster pack strapped across {possessive} back, its vents lit with a colored glow` and `a pair of articulated mechanical wing extensions mounted at the shoulders, each feather-like segment tipped with a small lit sensor lens`.

Two worked examples, showing both the append-to-existing and the add-a-segment shapes:

```
- a compact armored gauntlet on one forearm with a small glowing sensor ring || lit-hands
- a katana with a colored glowing accent along its edge held in {possessive} hands || hands mil weapon lit-hands
```

The second keeps its existing `hands` — that flag means the katana occupies the hands and still does. `lit-hands` is the separate claim that its glow lands there.

- [ ] **Step 5: Document the vocabulary in the tables file**

In the `## Glow colour` preamble comment, after the existing paragraph, add:

```
  A bullet in Eyes, Feature, Headgear, Outfit, Weapon or Gear that emits light
  also carries a zone - 'lit-face', 'lit-hands', 'lit-torso' or 'lit-behind' -
  saying where that light can land. Glow placement is filtered against the
  union of the zones a roll produced, so a collar indicator cannot light a
  chest. They are 'lit-'-prefixed because bare 'hands' already means "this
  occupies the hands" and gates the Stance roll. A new emitting bullet needs
  one, and test_glow_placement.py fails without it.
```

- [ ] **Step 6: Run the tests and watch them pass**

Run: `python -m unittest discover -s test -t .`

Expected: `OK`. A failure naming a bullet in `test_no_non_emitter_carries_a_zone` means a zone was pasted onto something that does not emit; remove it rather than loosening the test.

- [ ] **Step 7: Check no flag leaked into a prompt**

Run: `python generate-npc.py --count 40 --dry-run --out /tmp/zonecheck 2>&1 | grep -c "lit-"`

Expected: `0`. Any hit means a table is missing from the strip list.

- [ ] **Step 8: Commit**

```bash
git add prompts/npc-generator-tables.md generate-npc.py test/test_glow_placement.py
git commit -m "feat: say where each light source's light can land"
```

---

### Task 4: Zone-flag the placements and give the thin zones somewhere to go

**Files:**
- Modify: `prompts/npc-generator-tables.md` (`## Glow placement`)
- Test: `test/test_glow_placement.py`

**Interfaces:**
- Consumes: the `ZONES` tuple from Task 3.
- Produces: every placement carries at least one zone; every zone has at least two placements.

- [ ] **Step 1: Write the failing test**

Append to `test/test_glow_placement.py`:

```python
class TestPlacementZones(unittest.TestCase):
    def test_every_placement_accepts_at_least_one_zone(self):
        for bullet in LIVE_PLACEMENTS:
            flags = gen.split_flags(bullet)[1]
            with self.subTest(bullet=bullet):
                self.assertTrue([f for f in flags if f in ZONES], bullet)

    def test_every_zone_has_somewhere_to_land(self):
        """With one placement a zone is deterministic - every lantern-carrying
        NPC would get the identical sentence. Two is the floor for variety."""
        for zone in ZONES:
            reachable = [b for b in LIVE_PLACEMENTS
                         if zone in gen.split_flags(b)[1]]
            with self.subTest(zone=zone):
                self.assertGreaterEqual(len(reachable), 2, zone)

    def test_a_scene_placement_is_always_reachable_from_behind(self):
        """Backdrop light is the only thing that can light a wall, and it
        arrives from behind - so no 'scene' bullet may exclude lit-behind."""
        for bullet in LIVE_PLACEMENTS:
            flags = gen.split_flags(bullet)[1]
            if "scene" in flags:
                with self.subTest(bullet=bullet):
                    self.assertIn("lit-behind", flags, bullet)
```

- [ ] **Step 2: Run it and watch it fail**

Run: `python -m unittest test.test_glow_placement -v`

Expected: `test_every_placement_accepts_at_least_one_zone` fails for all ten bullets; `test_every_zone_has_somewhere_to_land` fails for all four zones.

- [ ] **Step 3: Rewrite the placement table**

Replace the ten bullets under `## Glow placement` with these thirteen:

```
- x2 falls across one side of {possessive} face against warm dim ambient light on the other || lit-face
- grazes {possessive} near shoulder and upper arm from one side and falls away across the chest, the face left in warmer shadow || lit-torso
- picks out the plating across {possessive} chest and dies out before it reaches the shoulders || lit-torso
- catches {possessive} jaw and one shoulder from below || lit-face lit-hands
- pools in {possessive} hands and throws colour up under {possessive} chin, the rest of the figure in warm shadow || lit-hands
- picks out {possessive} fingers and the edge of one forearm, everything past the wrist in shadow || lit-hands
- rims {possessive} shoulders and hair from behind, the face lit only by what spills around it || lit-behind
- falls across {possessive} back and one shoulder, the front of the figure in warm shadow || lit-behind
- cuts across the frame at an angle, catching {possessive} profile and one hand || lit-behind lit-hands
- washes across the scene behind {object}, throwing {possessive} outline into near-silhouette || scene lit-behind
- pools on the ground around {object} and throws colour up onto {possessive} hands || scene lit-behind
- stripes the wall behind {object} and catches one side of {possessive} face || scene lit-behind
- hangs in the air as a haze across the whole depth of the shot || scene lit-behind
```

Three of these are new (`picks out the plating…`, `pools in {possessive} hands…`, `picks out {possessive} fingers…`), and `rakes across {possessive} chest and shoulder` is reworded into `grazes {possessive} near shoulder and upper arm…`.

- [ ] **Step 4: Record why `rakes` went**

In the `## Glow placement` preamble comment, after the paragraph beginning "Each bullet is the PREDICATE", add:

```
  Do not write "a glow rakes across <a flat surface>". Everywhere that verb
  works in this repo its subject is a light SOURCE - "Dramatic side lighting
  rakes across {possessive} face", "Hard directional light rakes across the
  mechs' armor". With a coloured *glow* as the subject and a chest plate as
  the object, the model drew the sentence instead of lighting it: a hard-edged
  emissive band across the armour, reading as a decal. Name an incoming
  direction and a falloff, not a path across a plane.

  Each bullet also carries the zones it will accept - 'lit-face', 'lit-hands',
  'lit-torso', 'lit-behind' - and is only reachable when a rolled source can
  light there. A 'scene' bullet always carries 'lit-behind' too: backdrop
  light is the only thing that can stripe a wall, and it comes from behind.
```

- [ ] **Step 5: Run the tests and watch them pass**

Run: `python -m unittest discover -s test -t .`

Expected: `OK`. `test_every_placement_reads_as_a_predicate` and `test_no_placement_names_a_colour` must still pass against the three new bullets — they start lowercase, contain no ` glow`, and name no colour.

- [ ] **Step 6: Commit**

```bash
git add prompts/npc-generator-tables.md test/test_glow_placement.py
git commit -m "feat: say which sources each glow placement will accept"
```

---

### Task 5: Intersect the two at roll time

**Files:**
- Modify: `generate-npc.py` (roll loop, and the `Glow placement` filter around line 955)
- Modify: `test/fixtures/tables-minimal.md`, `test/fixtures/tables-themed.md`
- Test: `test/test_glow_placement.py`

**Interfaces:**
- Consumes: source flags from Task 3, placement flags from Task 4.
- Produces: `light_zones_for(*bullets) -> set[str]`; `npc["_light_zones"]`, a `set` of zone strings, available to `build_prompts()` and Task 6.

- [ ] **Step 1: Give the fixtures something to filter**

Both fixture tables need a source carrying a zone and placements that disagree, or the filter is exercised by nothing. In `test/fixtures/tables-minimal.md`, under `## Glow placement`, replace the bullets with:

```
- falls across one side of {possessive} face against warm dim ambient light on the other || lit-face
- catches {possessive} jaw and one shoulder from below || lit-face lit-hands
- pools in {possessive} hands and throws colour up under {possessive} chin || lit-hands
- washes across the scene behind {object} || scene lit-behind
```

and ensure its `## Headgear` contains at least one `lit-face` emitter and its `## Gear` at least one `lit-hands` emitter. Apply the same shape to `tables-themed.md`, keeping whatever theme tags those files already carry.

- [ ] **Step 2: Write the failing test**

Append to `test/test_glow_placement.py`:

```python
class TestZoneIntersection(unittest.TestCase):
    def test_light_zones_reads_the_union_of_the_rolled_sources(self):
        zones = gen.light_zones_for(
            "a compact armored gauntlet on one forearm with a small glowing "
            "sensor ring || lit-hands",
            "a composite plate harness ... a small status indicator lit at the "
            "collar || mil lit-face",
            "grey coveralls")
        self.assertEqual(zones, {"lit-hands", "lit-face"})

    def test_a_non_emitting_bullet_contributes_no_zone(self):
        """A zone on a bullet that does not emit must not be believed."""
        self.assertEqual(gen.light_zones_for("plain grey coveralls || lit-torso"),
                         set())

    def test_a_torso_placement_is_unreachable_without_a_torso_source(self):
        """The reported bug: a forearm ring and a collar LED lit a whole chest."""
        for seed in range(60):
            npc = gen.roll_npc(TABLES, random.Random(seed))
            placement = npc.get("Glow placement")
            if not placement:
                continue
            zones = npc["_light_zones"]
            flags = {f for b in bullets_for(TABLES, "Glow placement")
                     for f in ([] if gen.split_flags(b)[0] != placement
                               else gen.split_flags(b)[1])}
            if not flags:
                continue
            with self.subTest(seed=seed):
                self.assertTrue(
                    zones & {f for f in flags if f in ZONES},
                    "rolled a placement no rolled source can cast: %r from %r"
                    % (placement, zones))
```

- [ ] **Step 3: Run it and watch it fail**

Run: `python -m unittest test.test_glow_placement -v`

Expected: the first two FAIL with `AttributeError: module has no attribute 'light_zones_for'`.

- [ ] **Step 4: Implement `light_zones_for`**

In `generate-npc.py`, after `has_light_source`, add:

`LIGHT_ZONES` already exists from Task 3. Add beside it:

```python
def light_zones_for(*bullets):
    """The union of the zones the emitting bullets among `bullets` can light.

    A zone is only believed on a bullet that actually emits: the flag says
    where this thing's light falls, so on a bullet with no light it says
    nothing. That keeps a stray copy-pasted flag from widening the pool.
    """
    zones = set()
    for bullet in bullets:
        text, flags = split_flags(bullet or "")
        if has_light_source(text):
            zones.update(f for f in flags if f in LIGHT_ZONES)
    return zones
```

- [ ] **Step 5: Collect the zones during the roll**

The roll loop strips flags before storing, so the zones must be read while the raw bullet is still in hand. Beside the existing `outfit_notac` / `weapon_hands` captures at `generate-npc.py:1036-1043`, accumulate:

```python
            if name in ("Eyes", "Feature", "Headgear", "Outfit", "Weapon"):
                light_zones |= light_zones_for(raw_value)
```

where `light_zones = set()` is initialised beside `weapon_flags = ()` before the loop and `raw_value` is the bullet as read, before `split_flags()`. `Gear` is split separately further down; add the same union beside that split. After the `Backdrop` roll, add:

```python
    # Backdrop light is behind the subject by definition - it is the only
    # source that can also stripe a wall, which is what 'scene' gates on.
    if has_light_source(split_backdrop(npc["Backdrop"])[1]):
        light_zones.add("lit-behind")

    npc["_light_zones"] = light_zones
```

- [ ] **Step 6: Intersect at the filter site**

Extend the existing filter at `generate-npc.py:955`:

```python
        if name == "Glow placement":
            if not has_light_source(split_backdrop(npc["Backdrop"])[1]):
                on_figure = [x for x in options if "scene" not in split_flags(x)[1]]
                options = on_figure or options
            # A placement is only reachable when something rolled for this NPC
            # could have cast light where it claims the light falls. Without
            # this a forearm sensor ring licensed a rake across a whole chest,
            # and the model drew the glow on as a band rather than lighting it.
            castable = [x for x in options
                        if light_zones & {f for f in split_flags(x)[1]
                                          if f in LIGHT_ZONES}]
            if castable:
                options = castable
            else:
                # Nothing rolled can cast light where any placement claims it
                # falls. Rather than assert a location no source could produce
                # - the whole bug - drop the placement and let build_prompts()
                # use the unplaced wording the token already has. Empty is
                # distinct from absent: absent means an entry written before
                # this table existed, which keeps LEGACY_GLOW_PLACEMENT.
                npc[name] = ""
                continue
```

The house rule is "never filter a pool to nothing", and this is the one place
it is deliberately not applied: an uncastable placement is worse than no
placement. Task 4 step 1's coverage test is what keeps this branch unreachable
from the live tables.

- [ ] **Step 7: Teach `build_prompts` the unplaced form**

`GLOW_TOKEN` is already the unplaced wording - it names the colour and
constrains the palette without asserting where the light falls. Reuse it for
the portrait when the placement came back empty. At `generate-npc.py:1487`:

```python
    # An empty placement means step 6 found nothing the rolled sources could
    # cast, so the portrait takes the token's unplaced wording rather than
    # claiming a location. A MISSING key is different - that is an entry from
    # before the table existed, and npc.get() above still gives it the legacy
    # phrase.
    placed = "Glow placement" not in npc or npc["Glow placement"]
    portrait_glow_line = (
        GLOW_PORTRAIT if portrait_glow and placed
        else GLOW_TOKEN if portrait_glow
        else none_line)
```

and pass `portrait_glow_line` where `GLOW_PORTRAIT if portrait_glow else none_line`
is passed today.

- [ ] **Step 8: Test the fallback directly**

Append to `test/test_glow_placement.py`:

```python
    def test_an_uncastable_roll_drops_the_placement_rather_than_faking_one(self):
        """Task 4's coverage test should make this unreachable from the live
        tables, so the state is forced here rather than waited for."""
        npc = gen.roll_npc(TABLES, random.Random(0))
        npc["Glow placement"] = ""
        npc["_light_zones"] = set()
        portrait, _ = gen.build_prompts(npc)
        self.assertNotIn("A faint", portrait)
        self.assertIn("the only", portrait)
```

Run: `python -m unittest test.test_glow_placement -v`
Expected: PASS after step 7; before it, FAIL with the portrait still asserting
`A faint ... glow .`.

- [ ] **Step 9: Run the tests and watch them pass**

Run: `python -m unittest discover -s test -t .`

Expected: `OK`.

- [ ] **Step 10: Commit**

```bash
git add generate-npc.py test/ prompts/
git commit -m "feat: only offer a placement some rolled source could cast"
```

---

### Task 6: Keep the placement re-rollable

**Files:**
- Modify: `generate-npc.py` (manifest write, manifest read, `reroll_trait()`)
- Test: `test/test_reroll_trait.py`

**Interfaces:**
- Consumes: `npc["_light_zones"]` from Task 5.
- Produces: manifest key `light_zones`, a JSON list; `npc["_light_zones"]` restored as a `set` on the regen path.

- [ ] **Step 1: Write the failing test**

There is **no** `manifest_entry()` / `load_manifest_entry()` pair - the write
is inline around `generate-npc.py:2172-2185` and the read is inline in the
regen path around `:2049-2060`. So test the observable behaviour of
`reroll_trait()` rather than helpers that do not exist.

Append to `test/test_reroll_trait.py`:

```python
class TestGlowPlacementReroll(unittest.TestCase):
    """The manifest stores traits with flags stripped, so a re-roll cannot see
    the zones. 'young' met this first and became a manifest key of its own;
    'light_zones' is the third of that kind, and the raw-bullets spec subsumes
    all three."""

    def _flags_of(self, placement):
        return next((gen.split_flags(b)[1]
                     for b in bullets_for(TABLES, "Glow placement")
                     if gen.split_flags(b)[0] == placement), ())

    def test_a_reroll_only_offers_placements_the_stored_sources_can_cast(self):
        npc = npc_for(3)
        npc["_light_zones"] = {"lit-face"}
        for n in range(20):
            gen.reroll_trait(TABLES, npc, "Glow placement", random.Random(n))
            placement = npc["Glow placement"]
            if not placement:
                continue
            with self.subTest(n=n):
                self.assertIn(
                    "lit-face", self._flags_of(placement),
                    "re-rolled a placement no stored source can cast: %r"
                    % placement)

    def test_an_entry_with_no_recorded_zones_keeps_its_full_range(self):
        """Absent means written before zones existed. Widen rather than narrow:
        an old entry then keeps the coverage it was rolled under instead of
        silently losing its glow sentence."""
        npc = npc_for(4)
        npc["_light_zones"] = set(gen.LIGHT_ZONES)
        gen.reroll_trait(TABLES, npc, "Glow placement", random.Random(2))
        self.assertTrue(npc["Glow placement"])
```

- [ ] **Step 2: Run it and watch it fail**

Run: `python -m unittest test.test_reroll_trait -v`

Expected: FAIL with `KeyError: '_light_zones'` on the restored entry.

- [ ] **Step 3: Write the key**

Beside the existing `entry["young"] = npc["_young"]` write (around `generate-npc.py:2178`) and the second site around `:2390`, add:

```python
        # The third hand-written key of its kind, after 'young' and
        # 'outfit_notac': the manifest stores the source traits with their
        # flags stripped, so a Glow placement re-roll could not otherwise tell
        # which zones the rolled sources light. Sorted for a stable diff.
        # 2026-09-04-raw-bullets-in-the-manifest-design.md subsumes all three.
        entry["light_zones"] = sorted(npc["_light_zones"])
```

- [ ] **Step 4: Read the key back**

Beside `npc["_young"] = entry.get("young", False)` (around `:2055`):

```python
    # Absent means an entry written before zones existed. Fall back to every
    # zone rather than none: an old entry then keeps the placement coverage it
    # was rolled under instead of silently losing its glow sentence.
    npc["_light_zones"] = set(entry.get("light_zones", LIGHT_ZONES))
```

- [ ] **Step 5: Mirror the filter in `reroll_trait()`**

At the second filter site (around `generate-npc.py:1990`), apply the same intersection as Task 5 step 6, reading `npc["_light_zones"]` instead of the loop-local `light_zones`.

- [ ] **Step 6: Re-roll an orphaning trait**

`Eyes`, `Feature` and `Headgear` are rerollable and all carry `lit-face`. Re-rolling one can delete the last `face` source under a face placement. In `reroll_trait()`, after a successful re-roll of any of those three, recompute the zone set from the stored traits and, if the stored `Glow placement` is now unreachable, re-roll it too:

```python
    if name in ("Eyes", "Feature", "Headgear", "Outfit", "Weapon", "Gear"):
        npc["_light_zones"] = light_zones_for(*(npc.get(t, "") for t in (
            "Eyes", "Feature", "Headgear", "Outfit", "Weapon", "Gear")))
        # Stored traits have their flags stripped, so this recovers only the
        # zones still recoverable; it is deliberately paired with the widening
        # fallback above rather than trusted as exact. Recompute rather than
        # refuse, because these are traits a user re-rolls often.
```

Note honestly in the commit message that this recomputation is lossy against stripped traits and that the raw-bullets spec is what makes it exact.

- [ ] **Step 7: Run the tests and watch them pass**

Run: `python -m unittest discover -s test -t .`

Expected: `OK`.

- [ ] **Step 8: Commit**

```bash
git add generate-npc.py test/test_reroll_trait.py
git commit -m "feat: keep Glow placement re-rollable once it depends on the sources"
```

---

### Task 7: Documentation, the import skill, and the handoff

**Files:**
- Modify: `docs/generate-npc.md` (`## Glow placement`)
- Modify: `.claude/skills/npc-trait-import/SKILL.md`
- Modify: `docs/superpowers/specs/2026-09-04-raw-bullets-in-the-manifest-design.md`

**Interfaces:**
- Consumes: the finished vocabulary.
- Produces: nothing code depends on.

- [ ] **Step 1: Run the skill-sync test first and read what it wants**

Run: `python -m unittest test.test_import_skill_flags -v`

Expected: FAIL, naming the `lit-*` flags as present in the tables but absent from the skill. Read the failure message before editing — it states the exact contract.

- [ ] **Step 2: Document the zone axis**

In `docs/generate-npc.md`, in the `## Glow placement` section after the `scene` source table, add:

```markdown
`scene` answers *can this light reach a wall*. A second axis answers *can it
reach this part of the figure*: each emitting bullet in `Eyes`, `Feature`,
`Headgear`, `Outfit`, `Weapon` or `Gear` carries a zone — `lit-face`,
`lit-hands`, `lit-torso` or `lit-behind` — and each placement carries the zones
it accepts. A placement is reachable when the two sets intersect.

The prefix is not decoration. A bare `hands` already means *this item occupies
the hands* and gates the `Stance` roll, so the zone vocabulary cannot reuse it.

This is what stops a collar indicator lighting a whole chest. `lit-torso` is
the rarest zone — five sources out of thirty-five — so broad chest lighting is
now uncommon because few things can produce it, rather than because a weight
says so.
```

- [ ] **Step 3: Teach the import skill to emit zones**

In `.claude/skills/npc-trait-import/SKILL.md`, add `lit-face` / `lit-hands` / `lit-torso` / `lit-behind` to the flag reference table with the row text:

```
| `lit-face`, `lit-hands`, `lit-torso`, `lit-behind` | Eyes, Feature, Headgear, Outfit, Weapon, Gear | Where this source's light lands. Required on any bullet that emits light; `Glow placement` is filtered against the union of them. `lit-`-prefixed because bare `hands` already means "occupies the hands". |
```

and, wherever the skill instructs on staging a candidate for those tables, add the instruction that a bullet describing anything lit, glowing or emitting must carry exactly the zone its emitter sits in.

- [ ] **Step 4: Hand `light_zones` to the raw-bullets spec**

In `docs/superpowers/specs/2026-09-04-raw-bullets-in-the-manifest-design.md`, in the paragraph that names `young` and `outfit_notac` as subsumed keys, add `light_zones` to the list, with a clause noting it is derivable from the raw source bullets once those are stored.

- [ ] **Step 5: Run the whole suite**

Run: `python -m unittest discover -s test -t .`

Expected: `OK`, including `test_import_skill_flags`.

- [ ] **Step 6: Commit**

```bash
git add docs/ .claude/skills/npc-trait-import/SKILL.md
git commit -m "docs: record the glow zone axis and hand light_zones to rawTraits"
```

---

### Task 8: Measured verification

**Files:**
- Test: none created; this task measures.

- [ ] **Step 1: Confirm the reported NPC is fixed**

Run: `python generate-npc.py --seed 2940687489 --dry-run --out /tmp/zonecheck`

That seed is a different NPC (Ayodele Venn, a `lit-behind`/`lit-face` roll). The one that produced the decal was a field medic with a forearm ring, a collar indicator and a ring-structure backdrop. Assert the general property instead, over a large sample:

```bash
python - <<'PY'
import random, contextlib, io
from test.helpers import REPO, load_generator
gen = load_generator()
T = gen.parse_tables(REPO/"prompts"/"npc-generator-tables.md")
bad = 0
with contextlib.redirect_stderr(io.StringIO()):
    for n in range(3000):
        npc = gen.roll_npc(T, random.Random(n))
        p = npc.get("Glow placement")
        if not p:
            continue
        flags = next((gen.split_flags(b)[1] for b in T["Glow placement"]
                      if gen.split_flags(b)[0] == p), ())
        zones = {f for f in flags if f in gen.LIGHT_ZONES}
        if zones and not (npc["_light_zones"] & zones):
            bad += 1
print("placements no rolled source could cast:", bad, "of 3000")
PY
```

Expected: `0 of 3000`.

- [ ] **Step 2: Confirm the budget did not move**

Run: `python -m test.prompt_budget`

Expected: portrait p99 485, token p99 497, both unchanged from before this plan — the change adds no words to either template. A move means a placement bullet grew; shorten it.

- [ ] **Step 3: Report the new placement distribution**

```bash
python - <<'PY'
import random, collections, contextlib, io
from test.helpers import REPO, load_generator
gen = load_generator()
T = gen.parse_tables(REPO/"prompts"/"npc-generator-tables.md")
c = collections.Counter()
with contextlib.redirect_stderr(io.StringIO()):
    for n in range(3000):
        npc = gen.roll_npc(T, random.Random(n))
        c[npc.get("Glow placement", "(none)")[:60]] += 1
for text, n in c.most_common():
    print("%5d  %s" % (n, text))
PY
```

Expected: every placement appears at least once, and the two `lit-torso` bullets are visibly rarer than the `lit-face` ones. A placement at zero means no source can reach it — fix the tables, not the test.

- [ ] **Step 4: Commit any table adjustment the measurements forced**

```bash
git add prompts/npc-generator-tables.md
git commit -m "fix: even out a glow zone the measured distribution left unreachable"
```

---

## Notes for the executor

- The spec's §2 zone names are **wrong** as written and Task 1 fixes them. If you are reading the spec directly, use `lit-`-prefixed names.
- The spec's §5 says the table grows "10 to ~13"; Task 4 pins it at exactly 13.
- The spec's §8 records `light_zones` as knowing debt. Do not try to solve it properly here — that is the raw-bullets spec's job, and Task 7 step 4 is the handoff.
- `test/prompt_budget.py` is not a test and is not named `test_*`. Run it by hand as `python -m test.prompt_budget`.
