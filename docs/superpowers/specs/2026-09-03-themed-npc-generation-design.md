# Themed NPC generation

Design for making `generate-npc.py` roll NPCs that read as one coherent
character rather than as a bag of independently-rolled traits.

Covers nine requested changes, referred to throughout by their original
numbers: **1** (laborers unarmed), **3** (weapons table), **6** (headgear vs
outfit), **7** (kimono pairing), **8** (vacuum backdrop), **10** (hair colour
table), **11** (hair vs helmet), **12** (even distribution), **13** (mech
proximity).

Two further items from the same batch — the stale regenerate path and the
forced-`Build` error — were bounded fixes, already implemented and verified
separately. They are out of scope here.

---

## 1. Problem

Every appearance table rolls independently. That is what produces a dockworker
in a lacquered samurai pauldron holding a katana, and it is why the campaign's
several visual idioms — clean panelled mecha-military, worn industrial,
neon techwear, lacquered eastern-traditional, gothic militarist — arrive
shuffled together on one figure instead of one at a time.

The tables have been fighting this by hand. There are already seven pairwise
filters in `roll_npc()` (`young`/`figure`, `civ`/`mil`, `hands`/`gun`, `notac`,
`nogear`, `weather`, `sidearm`/`weapon`/`simple`), and the requested changes
would add five more. Each is a bespoke rule in code. The count only goes up.

### Goals

- An NPC's outfit, headgear, hair, weapon and backdrop read as belonging to
  one visual world.
- Which world is **independent of the NPC's job**: a pirate is as likely to
  look neosamurai as cyberpunk.
- Roll distribution is set deliberately, not as an accident of how many
  bullets happen to have been authored in each style.
- Physical impossibilities (breathing vacuum, a ponytail through a sealed
  helmet) never render, in any style.

### Non-goals

- Changing the prompt templates' house style or wording, beyond the new slots
  §4 requires.
- Reworking the pronoun-variant system, the manifest, or the ComfyUI plumbing.
- Cross-theme deliberate mixing. A rolled theme is exclusive; see §3.3.

---

## 2. Three axes

The requested changes are not one problem. They are three, and conflating them
is what has been driving the filter count up.

| Axis | Question | Governs | Items |
|---|---|---|---|
| **Theme** (new) | What visual world is this person from? | Outfit, Headgear, Hair, Hair colour, Weapon, Backdrop, Feature | 6, 7, 12 |
| **Role** (exists) | What is their job? | uniformed or not, armed or not, what they carry, where they can be | 1, 8, 13 |
| **Plausibility** (new) | Could this be one photograph? | hard constraints that hold in every theme | 8, 11 |

Theme and Role are deliberately independent — that independence is the
requirement, not an accident. Plausibility overrides both.

---

## 3. Theme

### 3.1 The table

A new `## Theme` table, rolled once per NPC. Eight entries, derived from
clustering the 405 unique appearance bullets already in the file:

| Theme | Existing bullets | Weight |
|---|---|---|
| `@gundam` — clean panelled mecha-military, flight suits, pilot bodygloves | 56 | x6 |
| `@tactical` — modern military realism: plate carriers, multicam, chest rigs | 55 | x6 |
| `@neosamurai` — lacquered plate, hakama, wide woven hats, blades | 52 | x6 |
| `@cyberpunk` — techwear, glowing seams, data ports, barcodes, chrome | 33 | x4 |
| `@neogothic` — torn-wing cloaks, bird skulls, demonic masks, amulets | 16 | x2 |
| `@grimdark` — greatcoats, ushankas, stencilled unit numbers, scorched plate | 11 | x1 |
| `@corporate` — tailored blouses, dress uniforms, ribbon racks | 10 | x1 |
| `@scav` — ragged, taped, self-cut, graffitied, salvaged | 8 | x1 |

Weights start proportional to available content, so a thin theme is rare
rather than repetitive. **Raising a weight as content lands is a one-character
edit to this table and needs no code change** — the same as any other bullet.
The intended end state is roughly equal weights once each theme has ~30+
bullets.

There is deliberately **no `@grounded` theme.** The 185 untagged bullets — 45%
of the appearance corpus — already *are* the worn-industrial Lancer look. They
serve as the neutral floor every theme draws from (§3.3) rather than competing
as a ninth entry.

### 3.2 Tag syntax

Theme tags ride in the **existing `||` flag segment**, prefixed `@`:

```
- full lacquered samurai armor in dark green and black … || civ notac @neosamurai
- a fitted black techwear jacket, sleeves lined with data ports … || civ @cyberpunk
- layered grey work coveralls patched at both knees || civ
```

This is chosen over a new syntax because every consumer already parses that
segment: `split_flags()`, the `npc-trait-import` skill, and the GUI's bullet
editor. The `@` prefix distinguishes a theme tag from a behavioural flag
without a second field.

A bullet may carry more than one tag — 43 currently would (most commonly
`@cyberpunk @gundam`). Multi-tagged bullets are reachable from either theme.

An untagged bullet is neutral and reachable from **all** themes.

### 3.3 The gate: exclusive plus neutral

A rolled theme opens:

- every bullet tagged with that theme, **plus**
- every untagged bullet,

and excludes every bullet tagged with a *different* theme.

```
Theme = @neosamurai
Outfit pool = @neosamurai bullets (11)  +  untagged bullets (~60)
              EXCLUDES @cyberpunk, @gundam, @grimdark, …
```

As with every existing filter in `roll_npc()`, the pool is **never filtered
down to nothing** — a table with no tagged and no untagged bullets falls back
to the full pool rather than raising.

### 3.4 Visibility weighting

A theme that is merely *opened* is not *visible*. With `@grimdark`'s 11 bullets
against a 185-bullet neutral floor, a grimdark NPC would roll neutral coveralls
almost every time — the theme would be rolled and then never seen.

So within the opened pool, tagged bullets are duplicated until they hold a
target share:

```python
THEME_SHARE = 0.6   # tagged bullets should win ~60% of themed rolls
```

The multiplier is computed per table from the actual pool sizes rather than
fixed, so it self-corrects as content is authored: `@gundam`'s 56 Outfit
bullets barely need duplication, `@grimdark`'s few need a lot. A thin theme
therefore still *reads* as itself, at the cost of repeating within a run —
which its low Theme weight already makes uncommon.

`THEME_SHARE` is a single module constant, deliberately tunable in one place.

### 3.5 What Theme replaces

**Item 12 (even distribution) is solved by construction.** Distribution stops
depending on bullet count. Today 13 of 87 Outfit bullets are traditional dress,
so 14% of civilian NPCs arrive in it purely because that many got written.
After this change that share is one weight in the Theme table. New samurai
outfits add *variety* without adding *frequency* — which was the stated goal.

**Item 6 needs no mechanism of its own.** The sedge hat, the wide straw hats,
the kimono and the shrine robes are all `@neosamurai`; tagging them is the
whole fix. A `@neosamurai` outfit can no longer meet a `@cyberpunk` visor.

**Item 7 is covered, but by two mechanisms rather than one, and it is worth
being precise about which does what.** The kimono's *headgear* pairing is
Theme, as above. Its *backdrop* pairing is *not*: a warzone is not an
aesthetic, so military-setting backdrops are not theme-tagged. They are gated
by Role instead (§5.3) — and since every `notac` outfit is also flagged `civ`,
only a civilian Role can roll one, and a civilian Role is already barred from
`mil` backdrops. The kimono therefore never reaches a military setting, via the
Role gate rather than the Theme gate.

The existing `notac` flag overlaps `@neosamurai` but is **kept**, because it
does something Theme does not: it bars *military-styled gear* specifically,
which matters for the civilian roles rolling within `@neosamurai`.

---

## 4. Structural splits

### 4.1 Weapon (item 3)

`## Gear` currently holds 82 unique bullets: 22 blades/polearms, 23 firearms,
37 pieces of equipment. A katana is reachable by a corporate liaison or a
dockworker at 26% odds.

Split into two tables with two prompt slots:

- **`## Gear`** — equipment only (~37 bullets): data-slates, tool bags, pry
  bars, thermoses, rebreathers, cabling.
- **`## Weapon`** — armament only (~45 bullets), plus a heavily-weighted
  "no weapon" entry so an unarmed NPC stays the common case for most roles.

An NPC rolls **both**, so a mechanic can carry a tool bag *and* a holstered
sidearm — currently impossible, since one Gear roll yields one thing.

This is what makes themes read hardest. A weapon is the single most
theme-defining object a figure carries, and one undifferentiated pool is why
`@neosamurai`'s katanas currently land on everyone.

Migration of existing flags:

| Flag | Moves to | Notes |
|---|---|---|
| `weapon`, `simple`, `sidearm` | `Weapon` | these only ever described armament |
| `gun` | `Weapon` | |
| `hands` | **both** | a data-slate occupies a hand too |
| `mil` | both | equipment can be military-issue |

`GEAR_POLICY` is renamed `WEAPON_POLICY` and reads the `Weapon` table.
`apply_gear_policy()` becomes `apply_weapon_policy()`. The `mil`-Role sidearm
guarantee and the Officials/Criminals tiers move with it unchanged.

**`notac` after the split.** `notac` currently drops every `mil`-flagged bullet
from one combined pool. Post-split it applies to **both** tables: an elaborate
or traditional outfit should pair with neither a military-issue rifle nor a
military-issue radio. Applying it only to `Weapon` would leave a kimono
carrying a tactical assault pack.

Stance filtering (§6) now reads the `hands` flags of **both** tables combined,
so a figure holding a slate in one hand and a rifle in the other cannot also be
posed with both hands in their pockets.

### 4.2 Hair colour (item 10)

`## Hair` currently fuses cut and colour in 40 of its 68 bullets, which is why
colour cannot vary independently and why the table skews pale.

- **`## Hair`** becomes pure cut (~67 bullets).
- **`## Hair colour`** is new, and holds three kinds of entry:

| Kind | Example | Notes |
|---|---|---|
| Flat | `black`, `ash-blonde`, `auburn` | |
| Gradient | `two-tone, dark over a bleached pale underlayer`; `silver-white fading to green at the tips` | extensible — new gradients are added here, not to `Hair` |
| Age-linked | `greying`, `salt-and-pepper`, `sandy going prematurely white at the temples` | flagged `older` |

Colour entries may carry theme tags — a faded synthetic lavender is
`@cyberpunk`, an ash-blonde is neutral.

**The `older` flag** drops that colour from the pool when the `Age` roll came
up `young`, mirroring the existing `figure`/`young` pairing exactly. This is
required, not cosmetic: greying and salt-and-pepper assert an age, so rolling
either onto a teenager contradicts the Age line earlier in the same prompt.

Content work, measured against the current file:

| Group | Count | Action |
|---|---|---|
| Already colour-free | 28 | none |
| Colour is one swappable adjective | 31 | hand-edit to strip it |
| Gradient carrying a cut | 5 | split into a cut half and a colour entry |
| Pure colour, no cut | 1 | moves wholly into `Hair colour` |
| Age-linked | 3 | split; colour half flagged `older` |

(28 + 31 + 5 + 1 + 3 = 68, the current total.) One entry —
*"shoulder-length hair, half of it dyed a faded synthetic color"* — is counted
as separable because it names no specific hue: it already reads correctly with
any rolled colour dropped in.

---

## 5. Plausibility

Hard constraints that hold regardless of theme or role. Kept visibly separate
from Theme rather than folded into it, because a violated one produces a
broken image, not merely an incongruous one.

### 5.1 Hair versus helmet (item 11)

Two new flags:

- `enclosed` on Headgear — a helmet or hood that seals the head. **20 of 70**
  current bullets qualify.
- `bulk` on Hair — volume or length with nowhere to go under one. **~31 of 68**.

Hair is rolled before Headgear in `REQUIRED_TABLES`, so **Headgear yields**:
a `bulk` Hair roll drops the `enclosed` bullets from the Headgear pool. This is
the same direction as every existing filter — the later table narrows against
the earlier — and it preserves hair, which is more identity-defining than
headgear.

The collision is common enough to matter: roughly **one roll in seven** today.

The tables already solve this once by hand — *"a sleek angular powered helmet
with raised sensor fins and a full dark visor down, a single braid of hair
falling free beneath it"*. That bullet is the model for the exception: a
Headgear bullet that explicitly accommodates hair stays reachable by carrying
no `enclosed` flag.

### 5.2 Vacuum (item 8)

`vacuum` on Backdrop bullets marks a scene with no breathable atmosphere.
It requires **both** a `sealed` Outfit and a `sealed` Headgear — a conjunction
across two tables, which nothing in the current design does.

Resolved by **roll order**: Backdrop moves to immediately after Role (§6), so
the environment is known before the appearance tables are rolled and can gate
them. A `vacuum` Backdrop restricts Outfit to `sealed` bullets and Headgear to
`sealed` ones.

The alternative — filtering Backdrop against an already-rolled Outfit — was
rejected: only 4 Outfit bullets currently read as sealed, so vacuum backdrops
would become effectively unreachable.

### 5.3 Backdrop role gating (items 8 and 13)

Backdrop gains two independent role gates.

**`civ` / `mil`** (item 8), the same vocabulary Faction and Outfit already use.
The airless-moon combat backdrop is `mil`-only. Where a `nogear` scene already
names a weapon in the subject's hands, that satisfies a `mil` Role's armament
guarantee, so moving the Gear sentence out no longer silently disarms them.

**Mech proximity** (item 13), a three-tier flag. The existing `mil` flag is
the wrong axis for this and cannot be reused: `a chief mechanic` and
`a maintenance technician` are not `mil` but belong beside a mech, while
`a field medic` and `a comms and sensors operator` are `mil` but should not be
sitting on one. It keys on `ROLE_CATEGORIES` instead — where `WEAPON_POLICY`
already keys.

| Flag | Meaning | Current bullets |
|---|---|---|
| `mechown` | it is *their* machine — on its knee, in its cockpit, "companion mech" | 11 |
| `mechwork` | they service it — calibration bay, maintenance bay, gantry | 7 |
| `mechnear` | it merely shares the scene — a war-mech striding past | 18 |

```python
MECH_ACCESS = {           # ordered: own > work > near
    "Pilots":      "own",    # it is their machine
    "Technicians": "work",   # they maintain it
    "Soldiers":    "near",   # it shares their battlefield
    "Support":     "near",   # medics and comms operators are on that battlefield
}                            # every other category: no mech backdrops
```

A category's tier admits that tier and every tier below it. An untagged
Backdrop is reachable by everyone.

**Tagging caution:** 8 backdrops mention a *prosthetic* limb or a mechanical
hand rather than a mech. They take no mech flag. A naive keyword pass on
"mech" catches all 8 wrongly.

Cost to the pool: a civilian role drops from 174 backdrops to 138. No
starvation risk.

### 5.4 Laborers unarmed (item 1)

```python
WEAPON_POLICY["Laborers"] = "never_in_hand"
```

Drops `Weapon` bullets flagged both `weapon` and `hands`. A dockworker or
salvager may still wear a holstered sidearm — they simply never hold one.

This is a real gap, not an edge case: `Gear` receives no `civ`/`mil` filter at
all and `Laborers` has no policy entry, so a dockworker currently rolls a
weapon 63% of the time and a gun *in hand* 15% of the time.

---

## 6. Roll order

`REQUIRED_TABLES` becomes, with changes marked:

```
Given names, Family names, Callsigns, Pronouns,
Theme,                      <- NEW: gates every appearance table
Age, Build, Height, Skin,
Hair, Hair colour,          <- NEW table, gated on Age via 'older'
Eyes, Feature, Demeanor,
Role,
Backdrop,                   <- MOVED earlier: gates Outfit/Headgear on 'vacuum',
                               and is itself gated by Role for civ/mil and mech
Faction, Outfit, Headgear,  <- Headgear gated on Hair via bulk/enclosed
Gear, Weapon,               <- Gear SPLIT; Weapon carries the policy
Accent, Weather, Stance
```

Ordering rules this must preserve:

- Pronouns first — every table may have a per-pronoun variant.
- Theme before every appearance table it gates.
- Age before Build (`figure`) and before Hair colour (`older`).
- Role before Backdrop (`civ`/`mil`, mech tiers) and before Faction/Outfit/Weapon.
- Backdrop before Outfit and Headgear (`vacuum`).
- Hair before Headgear (`bulk`/`enclosed`).
- Stance last — filtered against the combined `hands` flags of Gear and Weapon.

The existing documentation says "Don't reorder that list." That warning is
kept, and this reorder is recorded here and in `docs/generate-npc.md` as the
deliberate exception, with the dependency list above as the reason.

---

## 7. Complete flag vocabulary

New flags introduced by this design, alongside the existing ones:

| Flag | Table | Meaning |
|---|---|---|
| `@<theme>` | any appearance table | belongs to that theme; untagged is neutral |
| `older` | Hair colour | an age-linked colour; dropped when Age is `young` |
| `bulk` | Hair | volume or length that cannot fit under a sealed helmet |
| `enclosed` | Headgear | seals the head; dropped when Hair is `bulk` |
| `sealed` | Outfit, Headgear | airtight; required by a `vacuum` Backdrop |
| `vacuum` | Backdrop | no breathable atmosphere |
| `civ` / `mil` | Backdrop | *(existing vocabulary, newly applied here)* |
| `mechown` / `mechwork` / `mechnear` | Backdrop | mech proximity tier |

Flags remain matched literally, and an unrecognised one is still ignored rather
than reported — so the existing warning about copying spelling from a
neighbouring bullet applies to all of these.

---

## 8. Content work

| Task | Scale |
|---|---|
| Tag appearance bullets with themes | ~220 of 405 (45% stay untagged) |
| Split `Gear` into Gear + Weapon | 82 bullets sorted |
| Rewrite `Hair` for the colour split | 40 of 68 touched, 28 untouched |
| Author `## Hair colour` | new, ~25–30 entries |
| Flag Headgear `enclosed` | 20 of 70 |
| Flag Hair `bulk` | ~31 of 68 |
| Flag Outfit/Headgear `sealed` | ~4 + ~10 |
| Flag Backdrop `vacuum`, `civ`/`mil`, mech tiers | 36 of 174 mech + a handful vacuum |
| Fill out the four thin themes | ongoing, via `npc-trait-import` |

The thin themes (`@neogothic`, `@grimdark`, `@corporate`, `@scav`) are
deliberately shipped under-populated with low weights rather than held back;
their weights rise as the import skill fills them in.

---

## 9. Consumers

| Consumer | Change |
|---|---|
| `generate-npc.py` | Theme roll and filter, share-weighting, Weapon and Hair colour tables, three plausibility filters, `MECH_ACCESS`, `WEAPON_POLICY`, roll reorder, two new prompt slots |
| `prompts/npc-generator-tables.md` | Two new tables, the tagging and rewriting passes above, updated header documentation |
| **`.claude/skills/npc-trait-import/SKILL.md`** | Must learn `@theme` tags, the `Weapon` and `Hair colour` tables, and every flag in §7 — it is the tool the thin themes get authored with, so it is a blocker for §8, not a follow-up |
| `docs/generate-npc.md` | The reorder, the new axes, the new flags, worked examples |
| `lancer-npc-import-gui` | Reads headings generically, so it is expected to need no change. **To be verified, not assumed** — the Tables tab, presets, and the `--set-trait` form all touch this file's shape |

---

## 10. Verification

The generator has no test harness and this design does not add one; the checks
are run directly and their output reported.

- **Theme cohesion** — roll several hundred NPCs per theme and assert no NPC
  carries bullets tagged with a theme other than its own.
- **Theme visibility** — measure the actual share of tagged bullets per themed
  roll against `THEME_SHARE`, per table, including for the thin themes.
- **Distribution** — confirm theme frequency tracks the Theme table's weights
  and is independent of Role, by cross-tabulating rolled theme against rolled
  role over a large sample. This is the direct test of item 12 and of the
  pirate-as-samurai requirement.
- **Plausibility** — assert across a large sample that no NPC pairs `bulk` Hair
  with `enclosed` Headgear; that every `vacuum` Backdrop has a `sealed` Outfit
  and Headgear; that no Laborer holds a weapon; that no mech backdrop reaches a
  role outside its `MECH_ACCESS` tier.
- **No starvation** — assert no table's pool is ever filtered to the fallback
  for any combination of Theme, Role and Age.
- **Prompt length** — the two new slots lengthen every prompt against a 512
  token ceiling that already warns near the limit. Measure before and after;
  if the margin is gone, the templates need tightening as part of this work.

---

## 11. Phasing

Nine items is a lot for one plan. They are specified together because they
share one interface — the tables file's format — and splitting the spec would
mean designing that format three times. The *implementation* should still be
phased, and each phase below leaves the generator working:

**Phase 1 — mechanism, no content.** Theme roll, tag parsing, the
exclusive-plus-neutral gate, `THEME_SHARE`. With nothing tagged yet, every
theme opens the whole neutral pool and output is unchanged — which makes this
phase safe to verify against current behaviour.

**Phase 2 — structural splits.** `Gear` → Gear + Weapon, `Hair` → Hair + Hair
colour, the two new prompt slots, `WEAPON_POLICY`. This is the largest content
edit and the one that changes prompt shape, so it is worth landing alone.

**Phase 3 — plausibility and role gates.** The reorder, `bulk`/`enclosed`,
`sealed`/`vacuum`, Backdrop `civ`/`mil`, `MECH_ACCESS`, Laborers. These are
independent filters and could land individually if the phase is still too big.

**Phase 4 — theme tagging.** The ~220-bullet tagging pass, which is what
finally makes Phase 1 visible. Needs the `npc-trait-import` skill updated
first (§9).

**Phase 5 — fill the thin themes.** Ongoing content work, no code.

## 12. Open dials

Deliberately left as one-line changes rather than settled here:

- `THEME_SHARE = 0.6` — how strongly a theme asserts itself over the neutral pool.
- Theme weights — start proportional to content, intended to converge on equal.
- `MECH_ACCESS`: `Support` is granted `near`, and `Criminals` is excluded.
  A pirate beside a salvaged wreck is arguable and is one line to allow.
- Whether `notac` is eventually retired once `@neosamurai` is fully tagged.
