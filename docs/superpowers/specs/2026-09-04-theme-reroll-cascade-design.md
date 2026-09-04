# Re-rolling Theme, and the twelve traits that go with it

> **Status:** design, not started 2026-09-04. Depends on
> [raw bullets in the manifest](2026-09-04-raw-bullets-in-the-manifest-design.md),
> whose collection half already shipped with `--trait-odds`.

## 1. Problem

`--reroll-trait` refuses `Theme`, and says why:

```
"Theme": "it gates seven appearance tables, which would all have to re-roll with it",
```

That is a true statement about the cost, not an argument against paying it.
Theme is the trait a GM most wants to change — it is the whole visual world
the NPC comes from — and "re-roll the entire NPC" is not a substitute, because
it throws away the name, the role and the face that made the character worth
keeping.

So: make `Theme` re-rollable, re-roll everything it gates, and tell the user
what that means **before** they spend a render on it.

The raw-bullets spec currently lists this as a non-goal ("Those are a 're-roll
the NPC' feature, not a per-trait one"). §7 below retires that line. The
reasoning there was about `reroll_trait()`'s one-free-variable shape, which
this does not fit; it was not a judgment that the feature is unwanted.

### Goals

- `--reroll-trait Theme` re-rolls the theme and every trait whose correctness
  depends on it, under the same filters a fresh roll applies.
- The NPC stays the same person: name, callsign, pronouns, age, build, height,
  skin, eyes, demeanor, role and faction survive.
- The import GUI names every affected trait before anything runs.

### Non-goals

- Re-rolling `Pronouns`. Every per-pronoun variant table is selected by it, so
  it takes the whole NPC with it, including the name. That genuinely is a
  "roll a new NPC" feature.
- Changing what a plain `--regen-manifest` reproduces.
- A partial cascade. "Keep the backdrop, change the look" was considered and
  rejected in design: `Backdrop` is one of the seven tables `Theme` gates, so
  keeping it leaves the NPC standing in a scene tagged to the theme they no
  longer have — the exact contradiction the tags exist to prevent.

## 2. Prerequisite: raw bullets in the manifest

This cannot be built on today's manifest. `roll_npc()` strips a bullet's flag
segment before storing it, so a stored `Role` has lost the `|| mil` that
`Faction`, `Outfit` and `Weapon` are filtered on. A cascade that re-rolls
`Outfit` from a stripped `Role` would offer a service uniform to a colonial
administrator — a contradiction dressed as a feature.

The raw-bullets spec fixes this generally, and is **half done already**:
`npc["_raw"]` is collected during the roll (it shipped as part of
`--trait-odds`, which needs the unstripped bullets to count them). What
remains is persistence and consumption:

1. Write `_raw` to the manifest as `rawTraits`, beside `traits`, in both entry
   writers (`generate-npc.py:2548` for a fresh roll, `:2341` for a regen that
   re-rolled something).
2. Have `reroll_trait()` prefer `rawTraits` when present, which deletes the
   hand-written filter rebuilds and lets the other refused traits in.

**The Foundry importer contract does not block this.** The raw-bullets spec
flagged `docs/foundry-importer-contract.md` as "the one item that could change
the shape of the design", to be read before landing. It has now been read. The
contract governs the three `/importer/*` routes, whose job payload carries
`itemId`, `kind`, `name`, `callsign`, `role`, `faction`, `portraitPath` and
`tokenPath` — it never exposes `traits`, so it cannot be disturbed by a key
added beside them. No contract change, no module bump.

## 3. What re-rolls

Twelve of twenty-five. Not a taste judgment — each one is forced by a filter
that reads a flag from a trait above it:

| Re-rolled | Why |
|---|---|
| `Theme` | the target |
| `Hair`, `Hair colour`, `Feature`, `Outfit`, `Headgear`, `Weapon`, `Backdrop` | `THEMED_TABLES` — `filter_by_theme()` and `apply_theme_share()` select their bullets by the rolled theme, so a new theme makes the old bullets ones the roll could not have produced |
| `Gear` | filtered on the `Weapon` bullet's `hands` flag and the `Outfit`'s `notac`; both just changed, and a kept Gear could put a second object in a hand the new weapon already occupies |
| `Stance` | filtered on the combined `Weapon` + `Gear` flags — this is the filter that exists to stop hands-in-pockets poses around a rifle |
| `Glow placement` | filtered against the `Backdrop`'s light source via `has_light_source(split_backdrop(...))`; a kept placement would assert a scene that is gone |
| `Weather` | gated by the `Backdrop` bullet's `weather` flag, same reason |

Kept — thirteen: `Given names`, `Family names`, `Callsigns`, `Pronouns`, `Age`,
`Build`, `Height`, `Skin`, `Eyes`, `Demeanor`, `Role`, `Faction`,
`Glow colour`. None is themed, and none is filtered by anything being
re-rolled. `Faction`'s civ/mil filter reads `Role`'s `mil` flag, but `Faction`
is not being drawn, so no filter runs.

## 4. Approach

A Theme cascade is a fresh roll with thirteen variables pinned:

```python
overrides = {name: raw for name, raw in entry["rawTraits"].items()
             if name not in THEME_CASCADE}
npc = roll_npc(tables, rng, overrides)
```

This is the designed use of the override path, the same one §2.1 of the
raw-bullets spec relies on: `--set-trait` takes a bullet verbatim *with* its
flags, so every pinned trait arrives carrying the flags its dependents filter
on, and every re-rolled trait is drawn by the ordinary roller under the
ordinary filters. There is no second copy of the filter chain to drift.

Deriving the keep-set rather than listing it twice: the twelve above are
`("Theme",) + THEMED_TABLES` plus the four dependents, so the module defines

```python
# Traits a Theme re-roll must draw again, and why - see the design doc.
# Order follows REQUIRED_TABLES so this cannot disagree with the roller.
THEME_CASCADE = ("Theme",) + THEMED_TABLES + ("Gear", "Stance",
                                              "Glow placement", "Weather")
```

and the keep-set is `REQUIRED_TABLES` minus that. A table added to
`THEMED_TABLES` next month is then covered with no edit here — the same
property `REQUIRED_TABLES` already buys elsewhere in this file.

### 4.1 The new theme must be a different theme

A re-roll that draws the theme it already had spends twelve traits and a
render to produce a differently-dressed version of the same idea, which is not
what the button says it does. So the Theme draw repeats until it differs from
the stored one, unless the table offers only one theme, in which case it
proceeds and says so.

This makes the Theme draw conditional rather than weighted, which is a real
distribution change and is the point: the user asked for a different theme.
`--trait-odds` is unaffected — it samples fresh rolls, not re-rolls.

### 4.2 Entries written before `rawTraits`

Refused, with the reason, in the same shape every other refusal here takes:

```
--reroll-trait Theme: this NPC was generated before raw bullets were recorded,
so its Role's 'mil' flag is gone and a themed re-roll of its Outfit and Weapon
could contradict it. Re-roll the NPC to record them, or re-roll a single trait
from: <REROLLABLE_TRAITS>
```

Not a silent fallback to a partial cascade: a partial cascade is precisely the
set of contradictions this whole design exists to avoid.

## 5. The import GUI

`REROLLABLE_TRAITS` is read out of `generate-npc.py` by
`overrideTables.rerollableTraitsFrom()`, so `Theme` appears as a button the
moment it joins that tuple — no GUI change is needed to *offer* it. The change
is that it must not fire silently.

- **Server.** `/api/npc-tables` gains `cascades`, derived from the generator's
  own `THEME_CASCADE` by the same read-the-source route as `rerollable`.
  Derived, not restated: a hard-coded list in `app.js` is a second source of
  truth that goes stale the first time `THEMED_TABLES` changes. If it cannot
  be read, the Theme button is not offered — the same safe-way-to-be-wrong the
  existing `REROLLABLE_TRAITS` read already takes.
- **Dialog.** Clicking Re-roll on a trait that has a cascade opens a
  confirmation before anything is queued, reusing the existing
  `.confirm-dialog` pattern from delete. It names the trait being re-rolled,
  lists the twelve that go with it and the thirteen that are kept, says the
  NPC keeps its folder and manifest id, and warns that the render takes
  minutes. Cancel is the default action; the confirm button carries the
  count ("Re-roll Theme and 11 other traits").
- **Non-cascading traits are untouched.** The other eleven buttons keep firing
  on one click. A confirmation on every re-roll would train the user to click
  through the one that matters.

## 6. Risks

**The user expected a smaller change.** Twelve traits is most of an NPC's
appearance, and someone who clicks Re-roll on Theme expecting a new palette
gets a new outfit, weapon, hair and scene. This is why the dialog enumerates
rather than summarises, and why it is a dialog rather than a tooltip.

**`traits` and `rawTraits` disagreeing.** Inherited from the raw-bullets spec,
and this feature adds a second writer of both. The test that every `rawTraits`
value strips to its `traits` value covers it, and must run over a re-rolled
entry, not only a freshly rolled one.

**Manifest churn.** A cascade rewrites twelve trait values plus both prompts.
That is the feature working, but it means a re-roll is not reversible from the
manifest — the old bullets are gone once written. Out of scope here; worth
noting before somebody asks for undo.

## 7. Amendment to the raw-bullets spec

Its non-goal list currently reads:

> - Re-rolling `Pronouns` or `Theme`, which gate whole groups of tables and
>   would require re-rolling those too. Those are a "re-roll the NPC" feature,
>   not a per-trait one.

`Theme` comes out of that line, leaving `Pronouns`, with a pointer here. The
sentence stays true of `Pronouns`, which takes the name with it.

## 8. Verification

1. A fresh roll writes `rawTraits` for every trait in `traits`, and each raw
   value strips to exactly its rendered counterpart — after a cascade too, not
   only after a fresh roll.
2. A Theme cascade leaves all thirteen kept traits byte-identical, over a few
   thousand entries.
3. A Theme cascade never produces the theme it started from, given a table
   with more than one theme.
4. Every re-rolled trait is legal under the new theme: no bullet tagged for
   another theme survives, checked through `filter_by_theme()` rather than by
   re-reading the file.
5. No contradiction across the cascade: `Stance` never comes back
   hands-free on an NPC whose new `Weapon` or `Gear` occupies a hand, and
   `Glow placement` never asserts a light source the new `Backdrop` lacks.
6. An entry with no `rawTraits` refuses the Theme re-roll and still offers the
   traits it can.
7. The GUI's cascade list matches `THEME_CASCADE` read from the generator, and
   the Theme button disappears when the generator cannot be read.
8. `importerContract.test.js` passes unchanged, and a manifest carrying
   `rawTraits` still drives an import end to end.
