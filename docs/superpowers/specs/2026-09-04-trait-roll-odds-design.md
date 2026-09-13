# Trait roll odds: what a bullet's real chance of being rolled is

> **Status:** design 2026-09-04; shipped as `--trait-odds` (`3e68698`).
> Companion spec: `lancer-npc-import-gui`'s
> `2026-09-04-trait-roll-odds-display-design.md` covers the GUI half.
> **This spec ships first** — the GUI's percentage cell reads the JSON this
> one defines, and has nothing to display until it exists.

## 1. Problem

The Import GUI's Tables page shows each bullet's weight. A weight answers
"how does this bullet compare to its neighbour" and nothing else. The question
someone editing the tables actually has is "how often will this turn up", and
the weight does not answer it — not even after dividing by the table's total.

Two things stand between a weight and a probability.

**Disabled bullets.** A bullet wrapped `<!-- - … -->` is skipped by
`parse_tables()`, so it contributes nothing. Anyone reading weights off the
page has to mentally exclude them before dividing.

**Filters.** Most tables are not rolled from whole. `roll_npc()` narrows the
pool before drawing, and the narrowing depends on rolls that already happened:

```
Theme        gates Hair, Hair colour, Feature, Outfit, Headgear, Weapon, Backdrop
Age          gates Build ('figure') and Hair colour ('older')
Role         gates Faction and Outfit ('civ'/'mil'), and Weapon (apply_weapon_policy)
Outfit       gates Weapon, Gear ('notac') and Headgear ('hardtech')
Weapon       gates Gear ('hands') and Stance ('armed', 'gun')
Backdrop     gates Glow placement ('scene') and re-rolls Gear ('nogear')
```

So a Stance bullet flagged `|| gun` is unreachable unless the Weapon roll came
up a firearm, and a Weapon bullet flagged `|| mil` is unreachable under a
`notac` outfit. Their share of the table's weight overstates them, sometimes by
a lot. A `@neosamurai` Hair bullet is in the opposite position: `filter_by_theme`
plus `apply_theme_share` make it *more* likely than its weight suggests
whenever its theme comes up, and unreachable otherwise.

The net effect is that the one number the tables file makes visible is the one
number that is not the answer, and the gap is largest exactly where someone is
most likely to be tuning — the flagged bullets, which are the ones with
interesting behaviour.

### Goals

- A per-bullet probability that is correct under every filter the roller
  applies, including ones added after this spec.
- Reported per heading as it appears in the tables file, variants included, so
  the GUI can key it straight onto the rows it already renders.
- Cheap enough to recompute while someone is editing weights.

### Non-goals

- Changing how anything rolls. This spec reports on the roller; it must not
  alter a single draw. Byte-identical prompts for a given seed, before and
  after.
- Analytic exactness. §2 explains why sampling is the answer and what it costs.
- Conditional odds ("given that the Weapon came up a rifle, how likely is this
  Stance"). The number here is unconditional: the fraction of generated NPCs
  that end up with this bullet.
- Any GUI change. That is the companion spec.

## 2. Why this is sampled and not computed

The obvious implementation is to compute the marginals directly: propagate a
distribution over the gate variables — subject, theme, `young`, role category
and its `mil`/dress flags, `notac`, the Weapon flag set, the Backdrop's
`nogear` and light-source bits, Gear's `hands` — and read each table's
probability off it. This is exact, instant, and noise-free.

It is also a **second implementation of the filter chain, living beside the
first**. Every filter in `roll_npc()` would need a matching term in the
propagator, and the two would have to agree not only today but after every
future change. The failure mode is the bad one: nothing crashes, no test
necessarily fails, the numbers are simply wrong and nobody knows. This repo has
been deliberate about the opposite — `lib/overrideTables.js` in the GUI parses
`REQUIRED_TABLES` out of this file's source rather than restating it, precisely
so the two cannot drift.

The propagator is also harder than it looks. Every filter here ends
`options = filtered or options` — "never filter the pool down to nothing" —
so each term needs its own fallback branch. `apply_weapon_policy()` reweights
rather than filters. `apply_theme_share()` reweights conditionally on the pool
it is handed. The `nogear` Gear re-roll runs *backwards* through the table
order. An exact propagator is perhaps 300 lines of subtle code whose only
purpose is to agree with 200 lines of code sitting above it.

Sampling has none of that. Roll N NPCs through the actual roller and count what
comes out. It is correct by construction, it stays correct through every future
filter with no maintenance at all, and it is *impossible* for it to disagree
with the generator, because it is the generator.

What it costs is precision and latency, and §3.2 buys back enough of both.

## 3. Approach

### 3.1 `npc["_raw"]`, the collection half of the raw-bullets spec

Counting cannot read the returned trait values. `roll_npc()` strips the flag
segment off nine tables before storing them, so `npc["Weapon"]` is
`'a compact sidearm'` where the bullet in the file reads
`'a compact sidearm || hands gun sidearm mil'`. Counting stripped values would
fail to match the file, and would merge any two bullets that differ only in
flags.

It also cannot tell which *heading* a value came from. `variant_table()` serves
`Build (she)` in place of `Build`, and `Outfit` + `Outfit (she) +` as one pool.
The rolled value alone does not say which.

Both are solved by the mechanism the [raw-bullets
spec](2026-09-04-raw-bullets-in-the-manifest-design.md) already designed for
`--reroll-trait`: collect each bullet raw, at the moment it is drawn, into
`npc["_raw"]`. That spec's §2 puts it exactly this way — "`roll_npc()` already
has each raw bullet in hand at the moment it strips it, so collecting them is a
dict assignment in the loop it already runs, exposed as `npc["_raw"]` next to
the `npc["_young"]` it already sets."

**This spec implements that collection, and only that.** Writing `rawTraits`
into the manifest, rebuilding `--reroll-trait` on top of it, and retiring the
hand-written filter rebuilds all stay with the raw-bullets spec, whose §3 risk
about the Foundry importer contract is entirely about the manifest half and is
untouched here. When that spec lands it finds `_raw` already built and tested.

Three points where this spec pins `_raw` down more tightly than the raw-bullets
spec needed to:

- **Every rolled table, not just the strip list.** `Pronouns`, `Theme` and
  `Stance` are drawn outside the main loop and are omitted from the strip list,
  but the GUI renders their headings like any other and wants their odds. So
  `_raw` covers all of `REQUIRED_TABLES`. This is strictly more than the
  raw-bullets spec needs and costs it nothing; its own non-goals already rule
  out re-rolling `Pronouns` and `Theme`, which is a statement about what may be
  re-rolled, not about what may be recorded.
- **The last draw wins.** A `nogear` Backdrop re-rolls Gear. `_raw["Gear"]`
  holds the re-rolled bullet, not the discarded one, because that is the bullet
  the NPC actually kept. Both consumers want it that way: the odds must count
  what was kept, and a re-roll must be pinned to what was kept.
- **Overrides are not draws.** `--set-trait Outfit=…` is not a roll and must
  not be counted as one. `_raw` records what `rng.choice()` returned; where a
  forced value replaces it, `_raw` takes the forced value too, so that a
  re-roll pinning the rest of the NPC sees the same bullets the NPC has. The
  odds mode never passes overrides, so the distinction cannot affect it — but
  it needs stating, because the two consumers would otherwise want opposite
  things from the same key.

No signature change. `_raw` is a key on the returned dict, like `_young` and
`_outfit_notac`, and the manifest writer's `not k.startswith("_")` filter
already excludes it.

### 3.2 Memoising the splitters

Sampling only works if a roll is cheap. Measured on the live tables file,
20,000 rolls took **33.1 s** (1.66 ms/roll), which is far too slow to sit
behind a UI. A profile says why:

```
  ncalls  tottime  cumtime  function
 4093087    0.916    7.097  flags_for          <- 2,047 calls per roll
 2806574    2.338    3.763  split_flags
 1234000    1.468    2.523  split_backdrop
 3812334    1.379    2.232  themes_of
```

82% of the time is spent re-splitting the same few hundred strings. Every
filter pass walks its pool calling `flags_for()` on bullets whose flags have
already been parsed thousands of times in the same process.

`functools.lru_cache(maxsize=None)` on `split_flags`, `split_backdrop`,
`split_hair_colour`, `split_faction`, `themes_of` and `flags_for` takes 20,000
rolls to **5.9 s** (0.29 ms/roll) — 5.6× — with no behavioural change.

This is safe by inspection, and the reason is worth recording so nobody
un-does it later or extends it unsafely. All six are pure functions of their
arguments, all six take only strings or tuples (hashable), and all six return
only `str`, `tuple` and `frozenset` (immutable). Nothing a caller can do to a
returned value can corrupt a cached one. **A splitter that returned a list or
dict could not be memoised this way**, and if one is ever added it must return
a tuple or stay uncached. §5 keeps a test on this.

The cache is unbounded, which is correct here: the key space is the set of
bullet strings in one tables file, a few hundred entries for the process's
lifetime. The generator is a short-lived CLI, so there is nothing to leak into.

This speed-up is not confined to the odds mode. Every ordinary generation run
gets it too; it just does not matter there, since those runs are dominated by
waiting on ComfyUI.

### 3.3 `--trait-odds`

A new mode, alongside `--regen-manifest`:

```
generate-npc.py --trait-odds [N]      # default N = 20000
```

It parses the tables file, rolls N NPCs, tallies `_raw`, prints JSON on stdout
and exits. It contacts no ComfyUI, reads no manifest, writes no file and
creates no directory — it is a read-only query, and must stay one, because the
GUI will call it every time someone nudges a weight.

Output:

```json
{
  "samples": 20000,
  "tables": {
    "Weapon": {
      "a compact sidearm || hands gun sidearm mil": 0.0413,
      "": 0.2216
    },
    "Outfit (she) +": { "a fitted flight suit … || civ": 0.0071 }
  }
}
```

Keys are raw bullet text exactly as it appears in the file after the weight
prefix is removed — which is precisely the `text` the GUI's own
`tableBullets.js` produces via `splitWeight()`, so the two agree without either
knowing about the other. The prefix is gone for free rather than by agreement:
`parse_tables()` expresses a weight by *repeating* the bullet `N` times in the
pool rather than carrying a weights column, so `xN ` never survives into a
rolled value in the first place. Values are fractions of `samples`, not
percentages; formatting is the GUI's business.

**A variant family splits its total; a heading does not carry one.** For a
table with no variants the heading's rows sum to 1.0. For one with variants
they do not, and should not: a `Build (she)` bullet is reachable only by a
woman, so that heading sums to the share of NPCs who are women (measured:
0.498 against `Build`'s 0.502). This is the honest unconditional answer and
the display wants it — a reader looking at `Build (she)` is being told how
often that bullet lands on an NPC, not how often it wins a roll it was
eligible for. What sums to 1.0 is the *family*: a base table plus every
`(subject)` and `(subject) +` heading derived from it.

A bullet that never came up is present with `0.0` rather than absent, so the
GUI can tell "genuinely unreachable" from "heading the generator does not
roll". A disabled bullet is not in the file's parsed tables at all, so it is
absent — again a real distinction, and the GUI renders it as `—`.

**Heading attribution.** `_raw` gives a table name and a raw bullet; the
heading may be a variant. Resolve it against the same subject the roll used
(`npc["Pronouns"].split("/")[0]`), in `variant_table()`'s own order:

1. if `<name> (<subject>)` exists, that is the whole pool — attribute there;
2. else if `<name> (<subject>) +` exists and contains the bullet, attribute
   there;
3. else attribute to `<name>`.

The one ambiguity is a bullet whose text appears in both a base table and its
`+` variant. Step 2 hands it to the variant. This is worth one sentence in the
mode's docstring rather than a mechanism: a duplicated bullet is a mistake in
the file, and the odds display quietly listing it under one of its two
headings is not the worst consequence of it.

### 3.4 What the number means

**The fraction of generated NPCs that end up with this bullet from this
heading.** Unconditional, and measured after the `nogear` Gear re-roll.

For all but one table this is the intuitive reading and needs no gloss. The
exception is `Weather`, which is always rolled but only reaches a prompt when
the Backdrop is flagged `weather` — `weather_sentence()` returns `""`
otherwise. So `Weather`'s odds sum to 1.0 while most NPCs show no weather at
all.

The number stays as-is; the note belongs in the GUI. Reporting the joint
probability instead would be worse, because a `Weather` bullet flagged `clear`
opts out of rendering by design, and would then read `0%` when what the reader
wants to know is how often "clear" wins the roll. The honest split is a correct
number plus a sentence about what it is a number *of*, and the sentence is a
display concern.

## 4. Changes

| File | Change |
|---|---|
| `generate-npc.py` | `lru_cache` on the six splitters (§3.2) |
| `generate-npc.py` | `_raw` collected at all five draw sites (§3.1) |
| `generate-npc.py` | `--trait-odds` mode, JSON to stdout (§3.3) |
| `generate-npc.py` | `--help` text for the new flag |
| `docs/generate-npc.md` | the mode, its output, and what the number means |
| `test/test_trait_odds.py` | new — §5 |

`REQUIRED_TABLES`, `THEMED_TABLES`, the filters and the prompt templates are
all untouched.

## 5. Verification

1. **No behavioural drift.** A fixed seed produces byte-identical prompts and
   dossiers before and after the whole change. This is the test that matters
   most: the entire spec is only acceptable if the roller is unchanged.
2. **Memoised equals unmemoised.** Each of the six splitters, called on every
   bullet in the live tables file, returns values equal to the uncached
   implementation — and returns only immutable types, so the cache cannot be
   corrupted through a returned value.
3. **`_raw` strips to `traits`.** For a rolled NPC, every `_raw` value passes
   through its table's splitter to exactly the rendered trait. This is the
   raw-bullets spec's own §3 concern ("two records of one thing") and is cheap
   to hold from the start.
4. **`_raw` covers every table.** Its key set is `REQUIRED_TABLES`, including
   `Pronouns`, `Theme` and `Stance`.
5. **The re-roll wins.** On an NPC whose Backdrop is `nogear` and whose first
   Gear draw was flagged `hands`, `_raw["Gear"]` is the re-rolled bullet.
6. **Variant attribution.** A bullet present only in `Hair (she) +` is reported
   under that heading and never under `Hair`; a `Build (she)` roll is never
   attributed to `Build`.
7. **Each variant family sums to ~1**, and a variant heading on its own sums
   to strictly less (§3.3). Checked per family, not per heading, which is the
   distinction a test written the obvious way gets wrong.
8. **Filters actually show up.** A Stance bullet flagged `|| gun` has a
   probability strictly below its share of the Stance pool, and a themed
   bullet has one strictly above its share. These are the assertions that
   would fail if `--trait-odds` were quietly reporting naive weight shares.
   The theme half must run against `test/fixtures/tables-themed.md`: the live
   file describes `@` tags in its documentation but carries none on any
   bullet, so the same assertion against the live tables would pass vacuously
   today and silently start meaning something later.
9. **A disabled bullet is absent** from the output entirely, not present at
   `0.0`.
10. **It writes nothing.** `--trait-odds` run in a temp cwd creates no files
    and no directories, and produces valid JSON on stdout with nothing else
    mixed in.
