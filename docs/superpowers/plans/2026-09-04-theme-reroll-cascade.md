# Theme re-roll cascade — implementation plan

Spec: [2026-09-04-theme-reroll-cascade-design.md](../specs/2026-09-04-theme-reroll-cascade-design.md)
Prerequisite spec: [2026-09-04-raw-bullets-in-the-manifest-design.md](../specs/2026-09-04-raw-bullets-in-the-manifest-design.md)

## Context

`--reroll-trait Theme` is refused today because Theme gates seven appearance
tables. The spec makes it re-rollable by re-rolling the twelve traits whose
correctness depends on it, keeping the other thirteen, so the NPC stays the
same person.

The cascade cannot be built on today's manifest: `roll_npc()` strips a bullet's
flag segment before storing it, so a stored `Role` has lost the `|| mil` that
`Faction`, `Outfit` and `Weapon` filter on. The prerequisite spec fixes this by
storing raw bullets beside the rendered ones. Its collection half already
shipped (`npc["_raw"]`, added for `--trait-odds`); its persistence and
consumption halves are Tasks 1–2 here.

**The unifying insight both specs share.** Raw-bullets §2.1 and cascade §4
describe *the same operation*: re-roll the NPC with every trait except a free
set pinned as overrides.

```python
overrides = {name: raw for name, raw in entry["rawTraits"].items()
             if name not in free}
npc = roll_npc(tables, rng, overrides)
```

A single-trait re-roll is `free = (name,)`. A Theme cascade is
`free = THEME_CASCADE`. Build one function, parameterised by the free set —
not two. Every filter then runs exactly as it does for a fresh roll, because it
*is* a fresh roll, which is what deletes the eleven hand-written filter
rebuilds in `reroll_trait()` rather than extending them.

> **Amended after Task 2 (see the ledger's plan-defect ruling).** The claim
> above — raw-bullets §2.1's "it *is* a fresh roll with one free variable" — is
> true downstream and **false upstream**. A pinned trait is never drawn, so the
> filter that would have constrained it never runs: re-roll `Role` and the kept
> `Faction` sits on the wrong side of civ/mil 138 times in 400 on the live
> tables, measured by the implementer and re-verified at the controller. Since
> those traits are *refused* today, widening them without cascades trades a
> refusal for a contradiction.
>
> So `free` is never a single trait. It is the target's **cascade** — the
> target plus the transitive closure of everything whose filters read a flag
> from it, which is exactly the rule cascade §3 states for Theme. Tasks 3–4 are
> rewritten to build that map and derive every cascade from it. `THEME_CASCADE`
> becomes the closure of `Theme`, which is verified to be exactly the twelve
> traits spec §3 names — so the map *derives* the spec's tuple instead of
> restating it, which is the property spec §4 asked for. For a trait with no
> dependents the cascade is just itself, so the eleven traits that re-roll
> cleanly today are unaffected.

### Scope: this repository only

The spec spans two repositories. §5 ("The import GUI") describes
`/api/npc-tables`, `lib/overrideTables.js`, `app.js` and `.confirm-dialog` —
all of which live in the **separate** `lancer-npc-import-gui` repository. This
repo contains no JavaScript or HTML on any branch.

**In scope:** §2, §3, §4 (incl. 4.1, 4.2), §7, and verification items 1–6.
**Out of scope:** §5 and verification items 7–8 (GUI repo).

This ordering is forced anyway: §5 says the GUI derives `cascades` from the
generator's own `THEME_CASCADE`, so the GUI work cannot start until Task 3
lands that constant.

## Global Constraints

- **Python 3, standard library only.** No new dependencies.
- **`python -m unittest discover test` must stay green.** Baseline at branch
  point: 243 tests, OK. Every task ends with the full suite green.
- Tests load the generator with `test.helpers.load_generator()` (the file's
  hyphen makes it non-importable) and roll against
  `test/fixtures/tables-minimal.md`, not the live tables, so authoring a bullet
  never breaks a test. Follow that convention.
- **A plain `--regen-manifest` must keep reproducing byte-identical prompts.**
  This is an explicit non-goal of both specs. Nothing in this plan may change
  what a regen without `--reroll-trait` produces.
- **Entries written before `rawTraits` keep today's behaviour exactly**, at
  today's reduced coverage. The new path is additive; the old path is kept
  rather than replaced.
- **Never fabricate an unknown value into the manifest.** The file already
  makes this distinction twice, deliberately: `outfit_notac` is written only
  when known, because `None` means "nobody recorded it" and is not the same as
  a recorded `False`. Absent `rawTraits` means "not recorded" — do not write
  `{}`, and do not fall back to a partial cascade.
- **Match the house comment style.** `generate-npc.py` explains *why* at each
  site, in full prose paragraphs, often citing the specific contradiction the
  code prevents. Terse comments are a style regression here. Read the
  surrounding twenty lines before writing a comment.
- Do not restate a list the module can derive. `THEME_CASCADE` is built from
  `THEMED_TABLES`, and the keep-set from `REQUIRED_TABLES` minus the cascade,
  precisely so a table added to `THEMED_TABLES` next month needs no edit here.

### The render rule (Task 1 and every test that touches raw vs rendered)

`rawTraits[k]` does **not** simply strip to `traits[k]`. The roller's render
rule varies per table, and any test that hand-codes the variation becomes a
second copy of the roller:

- `Age, Build, Role, Outfit, Hair, Feature, Headgear, Weapon, Glow placement,
  Gear, Stance` — `split_flags(raw)[0]`.
- `Backdrop, Faction` — identity; both carry three `||` segments that are kept
  whole in `traits` (their own splitters run downstream in `build_prompts()`).
- `Hair colour` — `split_hair_colour(raw)[0]`, the base only.
- `Hair` — split, then `{colour}` replaced by the Hair colour base, then the
  colour's tail appended if it has one.
- everything else — identity.

**So do not write `split_flags(raw)[0] == traits[k]`.** It is false for four
tables, and special-casing them duplicates `roll_npc()`'s render rules. Assert
the round-trip property instead (Task 1).

## Task 1 — Persist and reload `rawTraits`

**Files:** `generate-npc.py`, `test/test_raw_traits.py` (new)

Spec: cascade §2 step 1; raw-bullets §2, §4.1.

1. **Fresh-roll writer** (`generate-npc.py:2548`, the `manifest[str(folder)] =
   {...}` literal). Add `"rawTraits": dict(npc["_raw"]),` immediately after
   `"traits"`. Comment it the way `young` and `outfit_notac` are commented
   just below: the writer excludes `_`-prefixed keys by construction, so this
   is written explicitly.
2. **`regenerate_one()`** (around `generate-npc.py:2203`, after
   `npc = migrate_traits(entry["traits"])`). When the entry has `rawTraits`,
   set `npc["_raw"] = dict(entry["rawTraits"])`. When it does not, leave
   `_raw` **unset** — absent means "not recorded", which later code must be
   able to tell from an empty dict. Do not warn here: a plain regen neither
   needs `_raw` nor is degraded by its absence, so the warning belongs where
   the value is actually consumed (the same reasoning the existing
   `_outfit_notac` comment gives).
3. **Regen writer** (`generate-npc.py:2341`, inside the existing
   `if rerolled is not None:` block). Alongside `entry["traits"]`, write
   `entry["rawTraits"] = dict(npc["_raw"])` — but only when `npc.get("_raw")`
   is present. A legacy entry re-rolled through the old path has no raw
   bullets to record, and inventing them would claim knowledge nothing has.
   Keep the existing "only when a trait actually changed" guard: a plain regen
   must not churn the manifest.

**Tests** (`test/test_raw_traits.py`):

- **Round-trip (the primary test).** Roll an NPC. Feed `npc["_raw"]` back as
  the *complete* override set to a second `roll_npc()` with a different seed.
  Assert every key in `REQUIRED_TABLES`, plus `name`, is byte-identical to the
  first roll's. This is the invariant every later task depends on — that a raw
  bullet pinned as an override renders back to exactly the trait it came from —
  and it tests it without duplicating the render rule above.
- **Coverage.** `set(npc["_raw"]) == set(REQUIRED_TABLES)`, and `"name"` is
  absent from `_raw` (it is an override but not a table).
- **What the writer stores.** Build the two dicts with the same expressions the
  writer uses — `{k: v for k, v in npc.items() if not k.startswith("_")}` and
  `dict(npc["_raw"])` — and assert every key of the first except `name` is a
  key of the second. Say plainly in the test docstring that the writer's own
  two lines are covered end to end only; do not extract a helper from the
  manifest literal just to make it unit-testable (YAGNI — the literal has one
  caller).

Run several seeds. Do not assert on a specific rolled bullet's text.

## Task 2 — Re-roll from raw bullets, on the pinned-override path

**Files:** `generate-npc.py`, `test/test_reroll_trait.py`

Spec: cascade §2 step 2; raw-bullets §2.1, §2.2, §4.2–§4.5.

1. **Add `reroll_from_raw(tables, npc, free, rng)`.** It pins every recorded
   raw trait *not* in `free` as an override, calls `roll_npc()`, and copies the
   result back over `npc` in place (`reroll_trait()`'s existing contract is to
   mutate `npc`, and `regenerate_one()` holds the reference). Docstring: this
   is the designed use of the override path, the same one `--set-trait` uses —
   a bullet verbatim with its flags — so every pinned trait arrives carrying
   the flags its dependents filter on, and there is no second copy of the
   filter chain to drift. `name` needs no special handling: it reconstructs
   from the pinned `Given names` and `Family names` at
   `generate-npc.py:1313`.

   **The copy-back must replace `npc` wholesale, `_raw` included**
   (`npc.clear()` then `npc.update(fresh)`, so the caller's reference stays
   valid). `roll_npc()` builds a fresh `npc["_raw"]` holding the bullets it
   actually drew; copying only the rendered traits back would leave the old
   `_raw` in place, and Task 1's regen writer would then persist `rawTraits`
   describing bullets this NPC no longer has — `traits` and `rawTraits`
   silently disagreeing, which is the risk both specs single out. The
   recomputed `_young` and `_outfit_notac` ride along for the same reason.
2. **`reroll_trait()` prefers raw when present.** At the top, when
   `npc.get("_raw")` is recorded, delegate to
   `reroll_from_raw(tables, npc, (name,), rng)` and return the new value. When
   it is not, fall through to today's hand-written path **entirely unchanged** —
   that path is kept, not replaced.
3. **Widen what is re-rollable, only on the raw path.** Add a raw-aware
   counterpart to `REROLLABLE_TRAITS`, derived rather than restated: every
   entry of `REQUIRED_TABLES` except `Given names`, `Family names` and
   `Pronouns` (refused for the reasons both specs' non-goals give — the folder
   and manifest id derive from the name; Pronouns selects every per-pronoun
   variant table and takes the name with it).

   **`Theme` is excluded here and stays refused in this task.** It is not a
   one-free-variable re-roll; Task 4 adds it through the cascade. This is the
   deliberate seam between the two tasks — it keeps each independently green.
4. **The refusal message must say which set applies.** An entry with raw
   bullets and an entry without offer different sets, and printing the legacy
   tuple to a user whose entry has raw bullets would be a lie.

**Tests** (extend `test/test_reroll_trait.py`; keep its existing cases green —
they cover the legacy path, which must not change):

- Re-rolling `Outfit` on a `mil` Role never yields a `civ` bullet, and vice
  versa, over a few thousand rolls (raw-bullets §4.2).
- Re-rolling `Stance` never yields a two-hands-free pose when the Weapon or
  Gear occupies a hand (§4.3). Reuse whatever `test_stance_armed.py` /
  `test_hands.py` already use to decide "occupies a hand" rather than inventing
  a second definition.
- Re-rolling any single trait leaves every other trait byte-identical (§4.4).
- An entry with no `_raw` still re-rolls exactly the eleven it can and refuses
  the rest with today's message (§4.5) — assert the legacy path is untouched.
- `Theme` is still refused in this task, on both paths.

## Task 3 — The trait dependency map, and cascades derived from it

**Files:** `generate-npc.py`, `test/test_trait_cascades.py` (new)

Spec: cascade §3, §4, §4.1 — generalised, per the ledger's plan-defect ruling.

**Why this task changed shape.** Task 2 shipped the raw-bullets re-roll and
measured a contradiction the specs did not anticipate: a one-free-variable
re-roll filters the *freed* trait against everything pinned, but never
re-filters a *pinned* trait against the new one. Re-rolling `Role` strands the
kept `Faction` on the wrong side of civ/mil 138 times in 400 on the live
tables (verified twice — implementer and controller). Raw bullets cannot fix
this; it is the reverse direction. Cascade §3 already states the cure — re-roll
the target plus everything whose filters read a flag from it — and Theme is one
instance of it rather than a special case. So build the general thing.

1. **Define the dependency map**, as data, beside `THEMED_TABLES`. Each entry is
   "re-rolling this trait invalidates these", with the *reason* named in a
   comment the way this file names every other reason:

   - `Theme` → the seven `THEMED_TABLES` (selected by theme, not by a flag).
     Derive this entry from `THEMED_TABLES`; do not type the seven out.
   - `Role` → `Faction`, `Outfit`, `Weapon` (all read Role's `mil`; Outfit also
     reads its dress policy via `ROLE_CATEGORIES`).
   - `Outfit` → `Headgear`, `Gear`, `Weapon` (all read Outfit's `notac`).
   - `Weapon` → `Gear`, `Stance` (read its `hands` and `gun`).
   - `Gear` → `Stance` (the combined hands filter).
   - `Backdrop` → `Weather` (its `weather` flag), `Glow placement`
     (`has_light_source(split_backdrop(...))`).
   - `Hair colour` → `Hair` (the cut carries a `{colour}` slot filled from it).
   - `Age` → `Build` and `Build` → `Age` (the `young`/`figure` pairing runs both
     ways — the map is deliberately not acyclic, so the closure below must
     tolerate a cycle rather than assume a DAG).
   - `Age` → `Hair colour` — **added during Task 3**, from an audit of
     `roll_npc()`'s filter chain rather than from the spec. `:1135` drops
     `older` colours on a `young` Age, so an `older` colour asserts an age the
     Age clause contradicts. Measured live at 3/400 before the edge existed.
   - `Backdrop` → `Gear` — **added during Task 3**, same audit. The `nogear`
     correction re-rolls a `hands` Gear to a free-handed one, but it runs
     *before* `npc.update(overrides)`, so a pinned Gear pastes straight back
     over the correction and survives a scene that forbids it. Measured live
     at 23/400. This is an ordering bug the map closes rather than a filter
     read, which is why it is worth its own sentence in the code.

   The spec's §3 table was written to justify Theme's cascade, not as a
   complete dependency graph, so treat it as a starting point and audit
   `roll_npc()`'s filter chain against it. Both additions above were verified
   at the controller to leave the closure of `Theme` at exactly the spec's
   twelve; they widen only `Age`, `Build` and `Backdrop`.

2. **Derive each trait's cascade as the transitive closure** of its dependents,
   including itself. One small function; it must terminate on the Age/Build
   cycle. Return the result ordered by `REQUIRED_TABLES` so it can never
   disagree with the roller's own order — the property spec §4 asks for.

3. **`THEME_CASCADE` is the closure of `Theme`, not a hand-written tuple.**
   Verified at the controller: that closure is *exactly* the twelve traits
   spec §3 names — `Theme`, the seven themed tables, plus `Gear`, `Stance`,
   `Glow placement` and `Weather`, which arrive transitively through `Outfit`,
   `Weapon` and `Backdrop`. Keep the name `THEME_CASCADE` (spec §4 and the GUI
   handoff both refer to it) but bind it to the derived value. This is what
   spec §4 wanted: a table added to `THEMED_TABLES` next month is covered with
   no edit here.

4. **The different-theme draw** (§4.1). Theme is drawn at `generate-npc.py:926`
   with a bare `rng.choice(tables["Theme"])` — bare-name bullets, no
   `variant_table()`, no flags. So "repeat until it differs" is implemented as
   drawing from the pool with the current theme excluded, which is
   distribution-equivalent to rejection sampling and cannot loop forever. Say
   that in the comment: a reader who has read §4.1 will expect a retry loop and
   deserves to know why there isn't one. When excluding the old theme empties
   the pool — a table offering only one theme — proceed with the theme it has
   and say so on stderr, per §4.1.

**Tests** (`test/test_trait_cascades.py`):

- The closure of `Theme` is exactly the twelve traits spec §3 names. **Write
  the twelve out literally in the test** — this is where the spec's claim gets
  pinned, and deriving both sides from the same expression would assert
  nothing.
- The keep-set (`REQUIRED_TABLES` minus the Theme cascade) is exactly the
  thirteen §3 names, written out literally for the same reason.
- Every member of `THEMED_TABLES` is in the Theme cascade — the property that
  makes a future themed table covered without an edit.
- Every cascade is a subset of `REQUIRED_TABLES`, contains its own trait, and
  has no duplicates.
- The closure terminates on the `Age`/`Build` cycle and yields
  `{Age, Build, Hair colour, Hair}` from either end — still a cycle test (the
  point is that mutual edges terminate), just with more members once `Age` →
  `Hair colour` is in the map.
- Every cascade is ordered consistently with `REQUIRED_TABLES`.
- The theme draw never returns the old theme over many seeds on a multi-theme
  table, and returns the only theme with a notice on a single-theme one. Build
  a one-theme table in the test; do not edit the shared fixture.

## Task 4 — Wire every cascade through `--reroll-trait`

**Files:** `generate-npc.py`, `test/test_trait_cascades.py`,
`test/test_reroll_trait.py`

Spec: cascade §4, §4.2, §8.2–§8.6, plus the ledger's plan-defect ruling.

1. **Route every re-roll through its cascade.** `reroll_trait()` already
   prefers the raw path when `_raw` is recorded (Task 2); it now calls
   `reroll_from_raw()` with the target's **cascade** as the free set rather
   than the single trait. For a dependency-free trait the cascade is just
   itself, so the eleven traits that re-roll cleanly today are unchanged —
   confirm that rather than assume it.
2. **Theme.** Its cascade is the twelve. Draw the new theme with Task 3's
   helper and pin it as an override so Theme takes the drawn value rather than
   a fresh uniform draw; the other eleven are free.
3. **§4.2 refusal, verbatim.** An entry without `rawTraits` asked to re-roll
   `Theme` gets the spec's message — the reason, and the traits it can still
   re-roll. Not a silent fallback to a partial cascade. Update
   `UNREROLLABLE_REASONS`: the `Theme` entry, and every other entry whose
   reason was "the manifest stores X with its flags stripped", is now
   describing a solved problem. Those traits are re-rollable on the raw path;
   their reasons only apply to the legacy path, and the message must not claim
   otherwise.
4. **Reporting.** The existing single-trait line (`re-rolled %s: %r -> %r`)
   cannot describe twelve. Print the target's change, then the traits that went
   with it. This is the CLI's half of §6's "enumerate rather than summarise",
   and it now applies to every cascading trait, not only Theme.
5. **Manifest.** A cascade must set `rerolled` truthy so the existing
   `if rerolled is not None:` block rewrites `traits`, and Task 1's addition
   rewrites `rawTraits` with it. Confirm `young` and `outfit_notac` carry the
   recomputed values rather than assuming.

**Tests** — spec §8 items 2–6, generalised:

- **§8.2** All thirteen kept traits, and `name`, byte-identical after a Theme
  cascade, over a few thousand entries.
- **§8.3** A cascade never produces the theme it started from, on a multi-theme
  table.
- **§8.4** Every re-rolled trait is legal under the new theme, checked by
  putting the new bullets back through `filter_by_theme()` — not by re-reading
  the tables file.
- **§8.5** No contradiction across the cascade: `Stance` never comes back
  hands-free when the new `Weapon` or `Gear` occupies a hand, and
  `Glow placement` never asserts a light source the new `Backdrop` lacks.
- **The general contradiction test — this is the one that closes the defect.**
  For *every* trait on the raw-rerollable path, re-rolling it must leave no
  kept trait contradicting the new value. Assert at minimum the pairs the
  implementer measured: `Role`→`Faction` civ/mil (was 138/400), `Role`→`Outfit`
  (110/400), `Gear`→`Stance` (32), `Backdrop`→`Glow placement` (30),
  `Outfit`→`Headgear` (16). All must be 0. Reuse the existing definitions of
  "occupies a hand" and civ/mil from `test_hands.py`, `test_stance_armed.py`
  and `test_faction.py`; do not invent second ones.
- **§8.6** An entry with no `rawTraits` refuses the Theme re-roll with the §4.2
  message and still offers the traits it can.
- **§8.1 after a cascade.** The raw/rendered round-trip holds after a cascade,
  not only after a fresh roll — spec §6 names this explicitly.
- The eleven legacy-path traits still re-roll identically on an entry with no
  `rawTraits`. `test_reroll_trait.py`'s existing cases must stay green.


## Task 5 — Documentation

**Files:** `docs/superpowers/specs/2026-09-04-raw-bullets-in-the-manifest-design.md`,
`docs/superpowers/specs/2026-09-04-theme-reroll-cascade-design.md`,
`docs/generate-npc.md`

Spec: cascade §7.

1. **§7 amendment.** The raw-bullets spec's non-goal list already carries the
   amended wording (`Theme` taken off the line, pointer to the cascade spec) —
   it was updated when the cascade spec landed. **Verify this and change
   nothing if it already reads correctly.** Do not re-amend an amended line.
2. **`docs/generate-npc.md`.** Document the `rawTraits` manifest key, the
   widened `--reroll-trait` coverage on entries that have it, the Theme
   cascade and what it re-rolls, and the refusal for entries that predate the
   key. Match the file's existing register.
3. **Spec status lines.** Both specs' `> **Status:**` headers say design /
   not started. Update to reflect what landed, and note in the cascade spec
   that §5 remains outstanding in `lancer-npc-import-gui`.

No code, no tests. Verify the suite is still green.

## Out of scope — handoff to `lancer-npc-import-gui`

Cascade §5 and verification 7–8 need the other repository:

- `/api/npc-tables` gains `cascades`, derived from the generator's
  `THEME_CASCADE` by the same read-the-source route
  `lib/overrideTables.js` already uses for `REROLLABLE_TRAITS`. Derived, not
  restated. If it cannot be read, the Theme button is not offered.
- A `.confirm-dialog` before a cascading re-roll, naming the trait, listing the
  twelve re-rolled and thirteen kept, saying the folder and manifest id
  survive, warning that the render takes minutes. Cancel is the default; the
  confirm button carries the count.
- Non-cascading traits keep firing on one click.
- `importerContract.test.js` passes unchanged (both specs already establish
  the payload never exposes `traits`, so no contract change and no module
  bump).
