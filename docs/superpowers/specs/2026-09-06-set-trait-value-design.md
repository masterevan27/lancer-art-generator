# Setting a trait to a chosen value on an already-rolled NPC

Date: 2026-09-06
Status: approved; implemented 2026-09-06 (`80e3d83`, merged in `235b3a2`) —
read this as the design record, not a work order
Companion spec: `lancer-npc-import-gui` →
`docs/superpowers/specs/2026-09-06-set-trait-value-picker-design.md`

## The gap

`--reroll-trait Hair` re-rolls one trait of a stored NPC and re-renders it.
There is no way to say *which* haircut. The user re-rolls until the dice agree
with them, which on a 27-bullet table with theme weighting is a lot of renders
for one decision.

`--set-trait Table=value` says exactly that, but only at roll time: an NPC that
already exists cannot be handed one. `parse_args()` refuses the combination
outright (`--regen-manifest replaces the roll entirely; drop --set-trait`).

So this spec adds two things:

1. **A pinned regen.** `--regen-manifest`/`--regen-id` with `--set-trait`, which
   keeps every other trait exactly as stored and changes the one named.
2. **A query mode.** `--trait-choices`, which answers *which values could this
   trait take on this NPC* — the question a picker has to ask before it can
   offer a list.

## Why the filtering cannot live in the GUI

The import GUI is where the picker will be, and it is JavaScript. Working the
legal values out there would mean a second copy of `roll_npc()`'s filter chain,
which would drift from this one silently — nothing would break, the list would
simply stop being true. `lib/traitOdds.js` already made that argument for the
odds display and settled it the same way: *where the generator already knows
something, ask it.* `--trait-odds` is the precedent for the shape — render
nothing, print JSON, let the GUI cache it.

## The primitive

Both directions of "is this legal" reduce to one operation: **run `roll_npc()`
with the whole NPC pinned and record the gated pool it computes for each
table.**

`roll_npc()` already computes a fully-filtered `options` list per table and only
*then* lets a forced value replace the draw. The forcing happens after the pool
is built, so the pool is the honest answer to "what could this table have
produced, given what the rest of this NPC is" — and it is built by the one
filter chain rather than a copy of it.

### The probe

`roll_npc(tables, rng, overrides=None, unarmed=False, probe=None)` gains an
optional dict. When given, the roller writes the pool it just finished
filtering into `probe[name]` at four points:

| Point | Table(s) | Note |
|---|---|---|
| The `for name in REQUIRED_TABLES` loop, after the last filter and before `rng.choice` | 22 tables | the ordinary case |
| The Theme draw near the top | `Theme` | no filter runs; the pool is the whole table |
| The `stances` block | `Stance` | pool is `(bullet, flags)` pairs; record the bullets |
| The `nogear` Gear correction | `Gear` | overwrites the loop's entry on purpose — see below |

Recording is side-effect free and consumes no randomness, so a probed roll and
an unprobed one with the same seed produce the same NPC. That is worth a test
of its own.

The Gear correction is the reason the probe records a *replacement* rather than
appending. A `nogear` Backdrop has already filled the subject's hands, so the
roller redraws Gear from the bullets that leave them free. That correction runs
*before* `npc.update(overrides)`, which is why a pinned Gear survives a scene
that forbids it — 23 times in 400 with Backdrop freed alone, per the
`Backdrop → Gear` note in `TRAIT_DEPENDENTS`. Recording the corrected pool means
the query sees the clash the roller silently loses, and reports it, instead of
inheriting the bug.

## Legality

For a candidate bullet `V` of trait `T` on NPC `N`, with `P` the probe from one
fully-pinned roll:

- **Upstream** — `V` is allowed iff `V ∈ P[T]`. One roll answers this for the
  whole table at once, because `T`'s own pool is built from the traits *above*
  it, all of which are pinned to `N`'s stored bullets regardless of `V`.
- **Downstream** — for each `D` in `TRAIT_DEPENDENTS[T]`, re-run pinned with
  `T = V` and check that `N`'s **current** bullet for `D` is still in `P'[D]`.
  Each `D` that falls out is a named conflict.

The downstream pass runs over **every** edge in `TRAIT_DEPENDENTS` bar the
Weather one, including the pairs `roll_npc()` already filters in both directions
— `Headgear`↔`Gear`, and `Age`↔`Build`, whose edge is in the map for the
one-click-re-roll promise rather than because the filter is one-way. For those
the pass is redundant: the upstream pool already accounted for the kept value,
so the check simply agrees. Redundant is the right trade against an exception
list that has to be re-derived every time an edge is added — a missed exception
would report a conflict that is not one, but a missed *edge* would hide one that
is.

Eight traits have dependents: `Theme`, `Role`, `Outfit`, `Weapon`, `Gear`,
`Backdrop`, `Hair colour`, `Age`. The other seventeen — `Faction`, `Headgear`,
`Build`, `Glow placement`, `Stance`, `Weather` and the rest of the appearance
tables — cost one roll for the whole table. A trait with dependents costs one
roll per candidate. `roll_npc()` measures at **0.33ms** on the live tables, so
the worst table in the file — Backdrop, 213 bullets — is about 70ms. No cache,
no sampling, no cleverness required.

### What a conflict is named after

The trait, not the filter. `"conflicts": ["Headgear"]` is something a picker can
render as *"would conflict with Headgear: a hard-tech visor"*. Naming
`filter_by_hardtech` instead would be naming an implementation detail at a user.

### Weather is not a contradiction

`Backdrop → Weather` is in `TRAIT_DEPENDENTS` as a *freshness* edge, not a
filter one — nothing narrows the Weather pool; the Backdrop's `weather` flag
only decides at prompt-build time whether the rolled Weather is rendered. So a
kept Weather is never illegal, only newly hidden or newly shown. The downstream
pass must skip it, or every Backdrop in the table reports a conflict that is
not one.

## `--trait-choices`

```
generate-npc.py --regen-manifest .generated-npcs.json --regen-id <ID> \
                --trait-choices Outfit
```

Renders nothing, talks to no ComfyUI, prints one JSON object on stdout:

```json
{
  "trait": "Outfit",
  "current": "a padded synthweave work jacket || civ",
  "dependents": ["Headgear", "Weapon", "Gear"],
  "choices": [
    { "value": "a padded synthweave work jacket || civ",
      "heading": "Outfit", "allowed": true, "current": true,
      "conflicts": [], "releases": [] },
    { "value": "an elaborate floral kimono ... || civ notac",
      "heading": "Outfit", "allowed": true, "current": false,
      "conflicts": ["Headgear"], "releases": ["Gear", "Headgear", "Stance"] }
  ]
}
```

- `value` is the raw bullet, flags included and verbatim, because that is what
  `--set-trait` takes and what the downstream filters read. Prettying it is the
  GUI's job (`lib/traitOptions.js` already has `readableLabel`).
- `heading` is the table the bullet came from, so a variant table
  (`Outfit (she) +`) stays distinguishable from the base pool.
- `allowed` is the upstream answer; `conflicts` is the downstream one — the
  **direct** dependents whose kept bullet this value would invalidate.
  `releases` is what `--release <conflicts>` would actually free: the union of
  those traits' cascade closures, minus the trait being set. It is reported
  rather than left to the caller to derive, so the picker can name what moves
  without a copy of `trait_cascade()` in JavaScript. Empty whenever `conflicts`
  is.
- **Both are reported and neither is dropped** — the picker shows illegal values too,
  greyed and still selectable, and it cannot do that if this end filters them
  out. It also matches `--set-trait`'s own long-standing behaviour of bypassing
  the roll pool: this command describes the pool, it does not enforce it.
- Variant tables are folded into the base name, the same way
  `lib/traitOptions.js` folds them, because `--set-trait` takes base names only.

Refusals reuse `reroll_trait()`'s: a trait outside the list that applies to this
entry exits with the same message and the same offer of what *is* available.
`--trait-choices` on an entry with no `rawTraits` is refused for the whole
feature (below) rather than answered from the legacy path.

## `--set-trait` on a regen

`--set-trait` comes out of the `--regen-manifest` conflict list. When both are
given, `regenerate_one()` routes to:

```python
reroll_from_raw(tables, npc, free=set(), pinned=overrides, rng=rng)
```

`free=set()` pins every stored raw bullet; `pinned` swaps the one named. That is
"keep the dependents, change one thing" expressed in the function that already
exists for it — its `pinned` parameter is documented as *"for the one trait in a
cascade whose new value is chosen rather than drawn"*, and Theme has been its
only user. Re-running `roll_npc()` rather than poking `npc[T]` directly is the
point: `_young`, `_outfit_notac`, `_gear_helmet`, the `{colour}` fill, the flag
stripping and the prompts all recompute from the new bullet set, and `_raw` ends
up describing the NPC that is actually being rendered.

`--reroll-trait` and `--set-trait` together are refused. They are two answers to
the same question.

### Also re-rolling the conflicting traits

`--set-trait Theme=<x>` keeping all seven themed traits — twelve once their own
dependents are counted — gives an NPC labelled for one visual world and dressed
for another. So the pinned regen takes an optional companion:

```
--set-trait Theme="neosamurai || ..." --release Hair,Outfit,Headgear
```

`--release` names traits to leave out of the pin. It is refused unless
`--set-trait` is given, and each name must be a **direct** dependent of a set
trait — releasing something unrelated is a re-roll wearing a disguise, and
`--reroll-trait` is the flag for that.

**Each released name expands to its cascade closure**, and the union of those
closures is the `free` set. Releasing the bare name would recreate the exact
contradiction this feature is trying to avoid, one level down: free `Outfit`
alone and it redraws while `Headgear`, `Weapon` and `Gear` stay pinned to
bullets chosen for the outfit that is now gone. `trait_cascade()` already
computes the closure and `reroll_from_raw()` already takes it as `free`; this
is the case they were written for.

Every trait that moved is printed, the way the `--reroll-trait` cascade report
already prints its own, so a release that reaches further than the name
suggests says so rather than being discovered in the render.

The GUI drives this from the conflict list it already has: the picker offers
*"also re-roll Headgear"*, unchecked, and sends the conflicting names.
Nothing releases unless the user asks.

## Entries without raw bullets

The whole feature is offered only where `npc["_raw"]` is present and non-empty
— the same test `reroll_trait()` uses to choose between its two paths, and the
same one the GUI already uses to decide which re-roll buttons to draw.

Pinning is what makes a chosen value mean anything, and a legacy entry has
nothing to pin: its stored bullets have had their flags stripped, so the
filters the query reports on cannot run against them. `--trait-choices` and a
pinned `--set-trait` both refuse such an entry, with the message
`reroll_trait()` already writes for this case — *re-roll the NPC to record
them*.

## Testing

New tests in `test/test_set_trait_value.py`:

- A probed roll and an unprobed roll at the same seed produce an identical NPC.
- Every table in `REQUIRED_TABLES` that `--trait-choices` accepts gets a probe
  entry — a table added later must not silently return an empty pool.
- The NPC's own current bullet is `allowed` for every trait. This is the
  invariant that catches a broken pin: the value it is wearing was legal when
  it was rolled and nothing has changed.
- `Theme` reports every other theme as conflicting with the themed traits an
  NPC actually carries, and reports none for an NPC whose themed bullets are
  all neutral.
- `Backdrop` flagged `nogear` conflicts with a `hands` Gear — the correction the
  probe exists to expose.
- `Backdrop` never reports a `Weather` conflict.
- A pinned `--set-trait` regen changes the named trait and no other, and
  rewrites `rawTraits` consistently with `traits`.
- `--release Outfit` frees `Outfit`'s whole cascade, not just `Outfit` — the
  closure test, and the reason the flag exists in this shape.
- Releasing a non-dependent is refused; `--release` without `--set-trait` is
  refused.
- A candidate's `releases` equals the closure the matching `--release` run
  actually frees. The query and the command have to agree, or the picker
  promises one thing and the regen does another.
- `--set-trait` with `--reroll-trait` is refused.
- Both commands refuse an entry with empty `rawTraits`.

## Out of scope

- Re-rolling a trait to a *random* value: `--reroll-trait` already does it.
- Editing the tables file. The picker offers bullets that exist; adding one is
  the Tables tab's job.
- Legacy entries. See above.
