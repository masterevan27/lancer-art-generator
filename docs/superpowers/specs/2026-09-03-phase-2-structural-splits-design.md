# Phase 2: structural splits (Gear/Weapon, Hair/Hair colour)

> **Status:** design, approved 2026-09-03. Implements Phase 2 of
> [`2026-09-03-themed-npc-generation-design.md`](2026-09-03-themed-npc-generation-design.md)
> (hereafter "the parent spec"), and **supersedes** parts of it — see §0.

## 0. What this supersedes in the parent spec

The parent spec was written before Phase 1 landed and before the visibility
measurement existed. Three of its statements are wrong or incomplete, and this
document overrides them. Where this file and the parent disagree, this file
wins for Phase 2.

| Parent | Superseded by |
|---|---|
| §6 roll order lists `Gear, Weapon` | **`Weapon, Gear`** — §3 below. Gear must yield the hands, not the weapon. |
| §4.2 says only that `Hair colour` is a new table | It is a **three-segment** table, `base \|\| tail \|\| flags`, and `Hair` bullets carry a `{colour}` slot — §2.2. |
| §4.1 addresses the `hands` collision only for Stance | Gear and Weapon can collide with **each other** — §3.1. Unaddressed, roughly 1 NPC in 5 is physically impossible. |

The parent spec's §10 also asks that prompt length be measured "before and
after". It has been, and the answer changes the shape of this phase: see §4.

## 1. Problem

Two tables each fuse two independent axes, and both fusions are visible in the
output.

**`## Gear` fuses equipment with armament.** 89 weighted bullets (82 unique):
56 carry the `weapon` flag, 33 do not. One roll yields one object, so an NPC is
either armed *or* carrying a tool, never both — and a katana is reachable by a
corporate liaison at the same odds as a data-slate. This is the single biggest
obstacle to themes reading: a weapon is the most theme-defining object a figure
carries, and one undifferentiated pool is why every theme's armament lands on
everyone.

**`## Hair` fuses cut with colour.** 68 bullets across the base table and its
two per-pronoun variants (21 + 41 `(she) +` + 6 `(he) +`). Colour cannot vary
independently of cut, so the palette skews toward whatever colours happened to
get written, and adding a new colour means writing it onto every cut.

### Goals

- An NPC can carry equipment *and* armament, independently rolled.
- Theme gates the armament, which is where it reads hardest.
- Hair colour varies independently of cut, gradients included.
- No NPC is physically impossible.
- **No increase in prompt truncation.** See §4 — this is a hard constraint,
  not a nice-to-have, and it is currently violated.

### Non-goals

- Phase 3's plausibility gates (`bulk`/`enclosed`, `sealed`/`vacuum`, Backdrop
  role gating, `MECH_ACCESS`).
- Settling the `apply_theme_share` filter-ordering question. Phase 2 gives that
  question its measurement; it does not answer it.
- Retiring `notac`.

## 2. The two splits

### 2.1 Gear → Gear + Weapon

**The split is mechanical.** Every bullet carrying the `weapon` flag moves to
`## Weapon`; every bullet without it stays in `## Gear`. The existing flag
already encodes the distinction exactly, so no bullet needs hand-classifying
and no judgement call can be got wrong.

```
## Weapon
- x30 || none
- a katana held drawn low in one hand, its point trailing near the ground || hands gun mil weapon sidearm
- a service pistol worn openly at the thigh || mil weapon simple sidearm

## Gear
- a dented thermos of something long gone cold || hands
- a canvas tool roll at the hip
```

**The empty entry.** `## Weapon` carries a heavily weighted bullet with no
text, written `|| none` in the style `## Weather` already uses for its `clear`
entry. It does two jobs: it keeps an unarmed NPC the common case for most
roles, and it keeps the mean prompt short, because most NPCs render no weapon
phrase at all (§4).

Its weight is the dial for how armed the setting feels. `x30` against ~56
armament bullets is the starting point — roughly a third of unrestricted rolls
unarmed — and it is a one-character edit, needing no code change.

Flag migration, unchanged from the parent spec §4.1:

| Flag | Goes to |
|---|---|
| `weapon`, `simple`, `sidearm`, `gun` | `Weapon` |
| `hands` | **both** — a data-slate occupies a hand too |
| `mil` | **both** — equipment can be military-issue |

### 2.2 Hair → Hair + Hair colour

`## Hair` becomes pure cut, with a `{colour}` placeholder marking where its
colour belongs. The position differs per bullet, which is why it is a
placeholder rather than a template-level join: `close-cropped {colour} hair`
and `a sleek {colour} bob cut level with the jaw` need the colour in different
places, and no single join rule serves both.

`## Hair colour` is a **three-segment** table — `base || tail || flags` —
mirroring `## Backdrop`, the shape `flags_for()` already special-cases:

```
## Hair colour
- black
- ash-blonde
- greying || || older
- silver-white || fading to green at the tips
- two-tone || dark over a bleached pale underlayer
- faded synthetic lavender || || @cyberpunk
```

The **base** fills the `{colour}` slot. The optional **tail** is appended after
the whole cut phrase, separated by a comma. This is what makes gradients work:
they read wrongly in adjective position and correctly as a trailing clause,
while flat colours read correctly inline.

```
"a sleek {colour} bob cut level with the jaw"  +  "silver-white || fading to green at the tips"
    -> "a sleek silver-white bob cut level with the jaw, fading to green at the tips"

"close-cropped {colour} hair"  +  "black"
    -> "close-cropped black hair"
```

A colour with flags but no tail writes its middle segment empty:
`greying || || older`. Slightly awkward to author, and the price of one table
instead of two.

**`Hair colour` adds no slot to either prompt template.** The base is
substituted into the rolled `Hair` value and the tail appended to it, so what
the template sees at `{hair}` is one finished phrase, exactly as today. This
matters for §4: the colour costs a couple of tokens, not a new clause. It does
mean `roll_npc()`'s placeholder substitution — which today formats only pronoun
fields and raises on anything else — has to learn `{colour}`, and has to run
*after* Hair colour is rolled.

**The `older` flag** drops that colour when the Age roll came up `young`,
mirroring the existing `figure`/`young` pairing exactly. Required rather than
cosmetic: greying and salt-and-pepper assert an age, and rolling either onto a
teenager contradicts the Age clause earlier in the same prompt.

Colour entries may carry theme tags. `Hair colour` joins `THEMED_TABLES`.

## 3. Roll order and filters

`REQUIRED_TABLES` becomes, with changes marked:

```
Given names, Family names, Callsigns, Pronouns, Theme,
Age, Build, Height, Skin,
Hair, Hair colour,          <- NEW, gated on Age via 'older'
Eyes, Feature, Demeanor, Role, Faction, Outfit, Headgear,
Weapon,                     <- NEW, carries WEAPON_POLICY
Gear,                       <- now equipment only, and yields to Weapon
Accent, Backdrop, Weather, Stance
```

`THEMED_TABLES` becomes `("Hair", "Hair colour", "Feature", "Outfit",
"Headgear", "Weapon", "Backdrop")` — `Weapon` in, `Gear` out, per the parent
spec §2's axis table. What is left of Gear is data-slates, tool bags and
thermoses, which are not theme-defining.

### 3.1 The hands collision — Weapon before Gear

Gear and Weapon roll independently, and **both can occupy hands**: 29 of the 56
armament bullets and 14 of the 33 equipment bullets carry `hands`. Rolled
without a filter that is roughly **one NPC in five** holding an impossibility —
a parasol in one hand and a katana raised in both, or a data-sheet held up in
both hands alongside twin sidearms.

**`Weapon` is rolled before `Gear`, and Gear's pool is filtered against the
Weapon's `hands` flag** — exactly how Stance is filtered against Gear today,
and ending `return filtered or options` like every other filter here.

The weapon keeps its hands because it is the more theme-defining object;
dropping the thermos costs nothing. This is why the parent spec's `Gear,
Weapon` ordering is superseded: under that order the weapon is what yields.

This filter costs nothing the split was for. The parent spec's motivating
example — a mechanic carrying a tool bag *and* a holstered sidearm — involves
no `hands` item on either side, and is unaffected.

### 3.2 The rest of the filter chain

| Filter | Rule |
|---|---|
| **`nogear` Backdrop** | Two separate effects, and they are not symmetric — see below. 45 of 205 Backdrop bullets carry it. |
| **Stance** | Filtered against the **combined** `hands`/`gun` flags of Weapon and Gear. |
| **`notac` Outfit** | Applies to **both** tables. Applying it only to Weapon would leave a kimono carrying a tactical assault pack. |
| **`older` Hair colour** | Dropped when Age is `young`. |
| **Theme** | Gates `Weapon`, not `Gear`. |

**`nogear` in detail.** Today the flag suppresses the carry sentence on the
**portrait only** — `build_prompts()` passes `gear_line=""` to the portrait
when it is set, and passes `carrying` to the token unconditionally. That
asymmetry is correct and is kept: the flag exists because the *backdrop scene*
already puts something in the subject's hands, and the token has no backdrop
at all, just flat white and a rolled Stance. Post-split it keeps behaving that
way — the portrait omits the whole merged carry sentence, the token still
renders it.

Its second effect is new and applies at roll time, so it reaches both prompts:
**`Gear` is restricted to non-`hands` bullets when the Backdrop is `nogear`**,
because a scene that occupies the subject's hands contradicts a thermos held in
one of them. This reuses §3.1's machinery with the scene standing in for a
`hands` weapon. It is a roll-time filter rather than a render-time suppression
because the NPC carries one set of objects, and both prompts must agree about
what those objects are.

`has_light_source()` must also learn `npc["Weapon"]`. It currently reads Gear,
Outfit, Headgear, Feature and Eyes to decide whether an accent glow belongs in
the prompt, and a glowing energy blade is exactly the kind of source it exists
to catch — leaving Weapon out would silently drop the accent line for the most
likely lit object an NPC carries.

`GEAR_POLICY` is renamed `WEAPON_POLICY` and reads `Weapon`;
`apply_gear_policy()` becomes `apply_weapon_policy()`. The Officials and
Criminals tiers move unchanged. The `mil`-Role sidearm guarantee gets
*stronger* rather than weaker: it restricts the pool to `sidearm`-flagged
bullets, which the empty entry is not, so a mil Role can no longer roll
unarmed at all.

## 4. The prompt budget — the binding constraint

**Measured over 1500 rolls against Krea 2's 512-token ceiling, before any
Phase 2 change:**

| | over 512 | p90 | p99 |
|---|---|---|---|
| portrait | 0.7% | 449 | 497 |
| **token** | **5.4%** | **504** | **530** |

The token prompt already truncates on roughly one roll in eighteen, losing the
tail — where the flat-white background instruction and the closing style tags
live, which is exactly what `TOKEN_LIMIT`'s own comment warns about. **This is
a live defect, not a Phase 2 risk.**

Projected, if the split adds a flat N tokens to every prompt:

| | +8 | +15 | +25 |
|---|---|---|---|
| portrait | 0.7% | 1.0% | 1.6% |
| token | 10.1% | 17.0% | **31.8%** |

**The two additions are not equal, and neither is flat.** `Hair colour` adds no
template slot at all — the colour is substituted *into* the existing `{hair}`
value, so it costs one adjective (~2 tokens) plus an optional tail on the ~5
gradient entries (~6). `Weapon` is the expensive one, and it is bimodal: zero
when the empty entry rolls, ~16-26 when it does not. So the realistic
distribution is most prompts near +2 and a large minority near +20 — which
means the *tail* is what breaches, and the tail is what already breaches
today.

The cause is the template, not the content: `TOKEN_TEMPLATE` is **262 tokens of
fixed boilerplate** against ~215 of rolled content, where `PORTRAIT_TEMPLATE` is
only 108. Within that boilerplate the painterly/grain/halftone style is
restated **four separate times**, totalling ~75 tokens.

### 4.1 Required work

1. **Consolidate the style restatements.** The trim must recover **≥25 tokens
   to break even** on the new slots, and **~50 to also clear the existing
   5.4%**. Both are within the ~75 available.
2. **A/B the trim on real renders before it lands.** This is prompt
   engineering, not dead code: diffusion models often need a style restated to
   hold it across a full-body figure, and these restatements read like
   hard-won fixes. Cutting them is a rendering-quality change and must be
   judged on output, by a human, not on token count.
3. **Ship a prompt-length regression test** pinning the token prompt's p99
   under 512. It fails against today's content, so it lands together with the
   trim rather than before it.

### 4.2 What softens this

The heavily weighted empty `Weapon` entry means most NPCs render **no weapon
phrase at all**, so the *mean* prompt grows far less than the worst case. The
+25 column is the tail, not the middle. Weight the empty entry up and the
budget problem shrinks with it — which makes that weight a second dial on
prompt length, worth remembering if the trim comes up short.

### 4.3 The carry sentence

`{gear_line}` — today `{Subject} {carry} {gear}. ` — becomes a single merged
sentence built from whichever of Weapon and Gear is non-empty:

| Weapon | Gear | Renders |
|---|---|---|
| yes | yes | `She carries a katana held drawn low in one hand and a battered data-slate.` |
| yes | no | `She carries a katana held drawn low in one hand.` |
| no | yes | `She carries a battered data-slate.` |
| no | no | *(omitted entirely)* |

One sentence rather than two, because two would cost a second `{Subject}
{carry}` on every armed NPC for no added clarity. All four combinations are
reachable — the empty Weapon entry and the `nogear` Backdrop both produce the
no-weapon rows — so all four are tested.

## 5. Content work

| Table | Count | Work |
|---|---|---|
| `Gear` → `Weapon` | 56 weighted | Mechanical, driven by the `weapon` flag. No judgement. |
| `Hair`: insert `{colour}` | ~59 of 68 | Hand-edit: strip the fused colour, mark its position. 9 are already colour-free. |
| `Hair colour`: new | ~35 | Authored, including ~5 gradients (tail form) and ~3 `older`. |
| `Backdrop` `nogear` | 45 | **No edit.** The flag's meaning changes; its placement does not. |

The `Hair` edit is the only one carrying real risk, because it is per-bullet
judgement across 59 bullets in three tables (`Hair`, `Hair (she) +`,
`Hair (he) +`). A bullet whose `{colour}` slot is misplaced reads wrongly but
does not fail, so §6's slot test matters more than usual.

## 6. Verification

Beyond the existing 51 tests, all of which must still pass:

- **No NPC holds two `hands` items.** Over a large sample, and per Role, since
  `WEAPON_POLICY` narrows the Weapon pool differently per role.
- **`older` never lands on a `young` Age.** Mirrors the existing `figure`
  pairing test.
- **Every `{colour}` slot resolves.** No rolled Hair value may contain a
  literal `{` after substitution, across every cut × colour pair — this is the
  guard on the 59-bullet hand-edit.
- **The carry sentence degrades correctly** at all four Weapon/Gear
  combinations, including the doubled-space and trailing-comma cases that an
  omitted slot invites.
- **`nogear` suppresses the Weapon** and leaves no `hands` Gear.
- **A `mil` Role is never unarmed**, now that the empty entry exists to be
  wrongly reachable.
- **Prompt length:** token p99 < 512 over ≥1500 rolls. Fails today; lands with
  the trim.
- **Theme visibility** (`python -m test.theme_visibility`) picks up `Weapon`
  and `Hair colour` automatically, since it reads `THEMED_TABLES`. The
  `Weapon` column is the one to watch — it is where themes should read hardest.

## 7. Consumers

| Consumer | Change |
|---|---|
| `generate-npc.py` | Both splits, `WEAPON_POLICY`, the roll reorder, the hands filter, the merged carry sentence, the template trim |
| `prompts/npc-generator-tables.md` | Two new tables, the `{colour}` edit, updated header documentation for the three-segment `Hair colour` shape |
| `.claude/skills/npc-trait-import/SKILL.md` | Must learn `Weapon` and `Hair colour`, the `older` flag, the three-segment colour shape, and that `Gear` is no longer themed while `Weapon` is. Its §0 already carries a "flags that do not exist yet" block listing exactly these — that block is deleted as they land. |
| `docs/generate-npc.md` | The reorder, the two new axes, the new flags, the carry sentence |
| `test/fixtures/tables-minimal.md`, `tables-themed.md` | Both need the two new tables to keep rolling |
| `lancer-npc-import-gui` | Reads headings generically, so expected to need no change. **Still to be verified** — carried over from the parent spec §9, and now more pressing: a three-segment `Hair colour` is a genuinely new bullet shape, where Phase 1 only added a heading. |

## 8. Open dials

One-line changes, deliberately not settled here:

- The empty `Weapon` entry's weight — how armed the setting feels, and a
  second lever on prompt length (§4.2).
- Whether the style trim keeps two restatements or one (§4.1) — decided on
  renders, not here.
- `apply_theme_share`'s position in the filter chain. Phase 2 supplies the
  measurement; the decision stays open.
