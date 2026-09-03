# Token fidelity, weapon policy and trait naming

Six changes to `generate-npc.py` and `prompts/npc-generator-tables.md`, covering
seven of the reported items and grouped because they share one theme: the prompt
asserts things that are not true of the NPC it describes, and the renders show it.

Companion spec: `lancer-npc-import-gui`'s
`docs/superpowers/specs/2026-09-03-tables-page-and-create-form-design.md`, which
covers the GUI half. **This spec ships first** — the GUI's unarmed checkbox and
its trait-override list both depend on changes made here.

## Measured baseline

Recorded before any change, so a regression is visible:

| | mean | p50 | p90 | p99 | max | over 512 |
|---|---|---|---|---|---|---|
| portrait | 418 | 418 | 463 | 495 | 540 | 0.2% |
| token | 451 | 451 | 484 | **510** | 537 | 0.7% |

`python -m test.prompt_budget`, 1500 rolls, seed 0. The token prompt has **two
tokens of p99 headroom** against Krea 2's 512 ceiling. Every change below is
costed against that number, and `test_prompt_budget.py` is the gate.

Test suite baseline: 90 tests, all passing.

---

## 1. The token template asserts standing and crouching at once

*Items 7, 8 and 11 of the request. One root cause.*

### The problem

`TOKEN_TEMPLATE` (`generate-npc.py:281`) opens with

> `{Subject} {is_are} standing at full height facing the viewer, entire body
> visible from the top of {possessive} head to the soles of {possessive} plain
> modern boots ... roughly seven to eight heads tall.`

and three sentences later injects the rolled pose:

> `{Subject} {is_are} {stance}, both boots planted and fully visible, the pose
> relaxed and natural with the arms free.`

When `{stance}` rolls *"crouched low and coiled on a raised ledge, weight braced
forward on one arm"*, the prompt asserts standing and crouching simultaneously,
and asserts that both boots are planted while one arm carries the weight. The
model resolves the contradiction the way diffusion models do: it renders both
readings. That is the reported "two people and a platform".

The ledge is the second half of the same failure. `Stance` is **token-only** —
the portrait takes its pose from `Backdrop` instead — and the token is rendered
on flat white for RMBG to cut to a transparent PNG. Any environment noun in a
`Stance` bullet is therefore a bug by construction.

### Why negatives cannot fix this

Generation runs at **CFG 1.0 with no negative prompt** (see the Settings section
of the tables file). The token template already says *"no texture, no gradient,
no shadow, no environment"* and the ledge appeared regardless. A positive noun
in the pose sentence outweighs a trailing negative. The fix must remove the
word, not counter it.

### Template change

`"standing at full height"` is doing two unrelated jobs: asserting the framing
(whole body in shot, correct proportions) and asserting a pose. Only the first
is wanted. Split them:

```
{Subject} {is_are} facing the viewer, the whole figure in frame from the top of
{possessive} head to the soles of {possessive} plain modern boots, no leg wraps
or puttees, with clear empty space above and below, in realistic adult
proportions roughly seven to eight heads tall.
...
{Possessive} face carries {demeanor}. {gear_line}{Subject} {is_are} {stance},
both feet in frame, the pose natural and unforced.
```

Three things happen:

- `"standing at full height"` goes. The framing survives intact in `"the whole
  figure in frame"`; only the pose claim is dropped.
- `"both boots planted and fully visible"` becomes `"both feet in frame"`. The
  old phrasing is false for every kneeling, sitting and crouching bullet in the
  table; the new one is a framing statement that holds for all of them.
- `"the pose relaxed and natural with the arms free"` becomes `"the pose natural
  and unforced"`. The `"arms free"` claim contradicts any pose braced on an arm.

Net effect: roughly **15 tokens shorter**, which moves the token p99 away from
the ceiling rather than toward it.

**Risk, stated plainly.** The dropped `"relaxed and natural with the arms free"`
clause was originally a counterweight to a rigid-attention drift that
`"standing at full height"` was itself causing. Removing the cause should make
the full counterweight unnecessary, and a shorter version is retained — but that
is only confirmable in renders, not tests. It is a two-line revert if the drift
returns.

### Table change

`## Stance` gets audited for anything that is not the body. Current offenders:

| Bullet | Problem |
|---|---|
| `crouched low and coiled on a raised ledge, ...` | scenery — the reported ledge |
| `leaning down into open machinery from above, ...` | scenery |
| `crouched low on one knee, gripping a blade planted point-down ...` | implies a ground plane; also names a weapon (see §3) |
| `sitting back with both hands laced behind {possessive} head, elbows out ...` | implies a chair |
| `raising {possessive} weapon high overhead ..., hair whipped wild by the wind and snow` | weather |
| `walking straight toward the viewer with {possessive} weapon raised over one shoulder, cloak snapping back in the rising heat` | weather |

Each is rewritten to be self-supporting. **The poses themselves stay** — crouching
tokens are wanted, they simply must not stand on anything. Kneeling and
cross-legged sitting stay too, now that the template no longer claims the boots
are planted.

A comment goes at the head of the table recording that `Stance` is token-only,
that the token is cut to a transparent PNG, and that bullets may therefore
describe only the body — no ground, furniture, props that are not held, weather
or environment. This is the drift that produced the bug; the comment is what
stops it recurring.

---

## 2. Civilians are armed two times in three

*Item 9, first half.*

`Weapon` deliberately sits outside the civ/mil filter (`generate-npc.py:646`):
a civilian may carry a military-issue weapon. But `WEAPON_POLICY` only has
entries for `Officials` (restricted) and `Criminals` (armed_bias), so seven
roles — chief mechanic, maintenance technician, dockworker, freelance salvager,
bar owner and information broker, data courier, scavenger-priest — hit
`apply_weapon_policy` with no policy at all and roll the raw pool.

Measured: the `Weapon` table is 50 bullets, weighted total 86, of which the
`x30 || none` entry is 30. **An ordinary civilian is armed 65% of the time.**

### Change

Add a `"civilian"` tier to `apply_weapon_policy` that duplicates the unarmed
bullets so unarmed becomes roughly two-thirds of a civilian roll — inverting
today's ratio. `unarmed * 3` gives 120 of 176, or 68%; the multiplier is a
single number and is the dial.

Make `"civilian"` the **default for any non-`mil` role** rather than another
hardcoded `ROLE_CATEGORIES` bucket. `Officials` and `Criminals` keep their
existing overrides; `mil` roles are unaffected because the `mil` branch returns
before policy is consulted. The benefit of defaulting rather than enumerating:
a civilian role added to the `Role` table later gets sane behaviour without also
needing a `ROLE_CATEGORIES` entry, which is exactly the omission that caused
this.

---

## 3. `--unarmed`, and the poses that name a weapon nobody has

*Item 9, second half. Item 5 in the GUI spec is the front end for this.*

### The flag

`--unarmed` forces the Weapon roll empty, **except** for:

- `mil` roles — soldiers, pilots, combat roles stay armed;
- `Criminals` — pirates and smugglers stay armed.

Implemented as a tier inside `apply_weapon_policy` that runs before the others,
so the existing ordering comment at `generate-npc.py:665` (policy before
`notac`, because a guarantee outranks a preference) continues to hold.

### The latent bug it exposes

Seven `Stance` bullets reference a weapon but are flagged `|| hands`, not
`|| gun`:

- `crouched low on one knee, gripping a blade planted point-down ...`
- `caught in a dynamic overhead swing, both hands driving a blade down ...`
- `kneeling formally with both hands folded around an upright hilt ...`
- `standing in profile with head bowed slightly, one hand resting on a sheathed blade at the hip`
- `walking straight toward the viewer with {possessive} weapon raised over one shoulder ...`
- `raising {possessive} weapon high overhead in both hands, mid-swing ...`
- `standing tense with both hands crossed at the hip, one gripping the hilt of {possessive} sheathed weapon ...`

Only `gun` is gated on the Weapon roll (`generate-npc.py:760`). So an unarmed
NPC can already be posed brandishing a weapon that no earlier sentence names —
rare today, routine under `--unarmed`.

### Change

Add an `armed` flag meaning *this pose references a weapon of any kind*, and
tag those seven bullets with it. `gun` keeps its narrower meaning — an actual
firearm being handled — and the two form a hierarchy:

- Weapon roll empty → drop stances flagged `armed` **or** `gun`.
- Weapon rolled but not a firearm → drop stances flagged `gun` only.
- Weapon rolled and a firearm → no stance filtering.

The existing filter at `generate-npc.py:760` generalises to this; the
`|| hands` flag is unrelated and unchanged.

---

## 4. `electric blue` renders actual electricity

*Item 10.*

Both templates wrap the rolled value as a glow — *"A faint `{glow}` glow falls
across one side of `{possessive}` face"*, *"a single `{glow}` glow the only
saturated color"*. So `electric blue` becomes "electric blue glow" and the model
renders arcs. `neon cyan` has the same defect.

Rename to hue-only wording:

- `electric blue` → `vivid cobalt blue`
- `neon cyan` → `bright cyan`

The other nine entries (amber, brass-gold, sickly yellow-green, deep violet,
teal-green, crimson-red, magenta-pink, cold blue-white, dull copper-orange) are
already hue-only and do not change.

A table comment records the rule: **entries name a hue, never a light-emitting
phenomenon**, because of how the template frames them. Without the comment the
next author adds "neon pink" and the bug returns.

---

## 5. Faction contributes nothing to the image

*Item 12.*

### Diagnosis

Both templates read:

```
wearing {outfit}, {faction}, the clothing following the shape of that frame.
```

`{outfit}` rolls something concrete — *"an oversized open shirt sliding off one
shoulder, draped loosely over a dark cropped tank"*. `{faction}` then adds a
second, vaguer clause **about the same garment** — *"in Smith-Shimano Corpro
corporate wear, sleek and expensive"*. Two descriptions compete for one slot and
the specific one wins outright.

This is not primarily an unknown-proper-noun problem, though the proper nouns
are also unknown to the model. It is structural: seven of the eight bullets name
a garment *category* (service dress, corporate wear, livery, kit, gear), which
is precisely what `Outfit` already specifies. The one with a chance of landing
is `IPS-Northstar workwear, **riveted and salt-stained**` — surface and wear
state, a different axis from garment shape. Two bullets (`unaligned and
freelance`, `the deliberately anonymous gear of someone who does not answer
questions`) carry no visual content at all.

### Structure

`Faction` becomes three segments — `name || visual || flags` — the shape
`Backdrop` and `Hair colour` already use. This requires:

1. A `split_faction()` alongside `split_backdrop()` / `split_hair_colour()`.
2. An entry in `flags_for()` (`generate-npc.py:965`), whose whole purpose is
   dispatching flag-parsing by table shape.
3. Removing `"Faction"` from the two-segment list at `generate-npc.py:724`.
4. Routing `filter_by_mil()`'s flag read through `flags_for` rather than
   `split_flags`. **Without this the `civ`/`mil` filter starts scanning the
   visual prose for the words "civ" and "mil"** — `split_flags` uses
   `partition("||")` and would return every word after the first separator as a
   flag.
5. Extending the comment at `generate-npc.py:713` to name Faction as the third
   three-segment table. That comment already states the rule; it just needs to
   stay accurate.

`npc["Faction"]` keeps the raw bullet, matching how `Backdrop` is stored.
`write_dossier` renders segment 1; `build_prompts` renders segment 2. An empty
segment 2 contributes nothing to the prompt, the way `Weather`'s `clear` flag
already works.

### Content

Segment 1 becomes the display name, which also fixes the dossier byline — from
*"Callsign" — a corporate liaison officer, in Smith-Shimano Corpro corporate
wear, sleek and expensive.* to *"Callsign" — a corporate liaison officer,
Smith-Shimano Corpro.* The two no-affiliation entries are renamed so they stop
reading as duplicates.

Segment 2 works on axes `Outfit` leaves free — fabric, tailoring, insignia,
patina — never garment category.

| Name | Visual signature | Asserts pigment |
|---|---|---|
| Unaligned | *(empty)* | no |
| Unregistered | *(empty)* | no |
| Union Administrative Department | issued and worn thin, stitched shoulder patch | yes — institutional blue-grey |
| Harrison Armory | sharply pressed, high stiff collar, polished fittings | yes — imperial green and gold |
| Smith-Shimano Corpro | precisely tailored, fine seam piping, soft organic curves | yes — white and pale pastels |
| IPS-Northstar | heavy canvas and riveted leather, salt-bleached and patched | yes — rust orange, hazard striping |
| Karrakin Trade Baronies | heraldic livery, stiff standing collar, archaic formality | yes — deep crimson and gold |
| Colonial militia | mismatched surplus, webbing straps, taped-over insignia | no |

Exact wording is written to a length budget — see Budget below.

### Pigment versus light

Faction colour is **pigment**; the glow colour is **light**. They coexist: a
green-and-gold Harrison uniform lit by a red instrument glow is coherent.

But the closing line's exclusivity claim stops being true when a pigment faction
is rolled, so it softens — *"with `{glow}` the only saturated color in the
frame"* becomes *"...the only **other** saturated color."*, and the no-glow
variant drops its *"no stray saturated color"* claim.

Rather than doubling the four `GLOW_*` constants to eight, the closing line is
assembled from parts so the pigment-aware variant is one branch. Factions
asserting pigment carry a `palette` flag; the branch reads that flag.

---

## 6. `Accent` is a misnomer, and §5 makes it worse

*Item 13.*

The table holds hues (`amber`, `teal-green`) describing the single coloured
light source, gated by `has_light_source()`. It is not a design accent, and once
Faction owns pigment the name actively misleads.

Rename `Accent` → **`Glow colour`**: "glow" is the word both templates already
use and matches the gate exactly, while `colour` matches the sibling
`Hair colour` heading. `ACCENT_*` constants become `GLOW_*`, the `{accent}` slot
becomes `{glow}`, and the dossier label goes from `Accent color` to
`Glow colour`.

Touched: the heading in the tables file, `REQUIRED_TABLES`
(`generate-npc.py:118`), the theme comment at `generate-npc.py:122` whose prose
lists "accent", the four template constants, `write_dossier`, and
`test_theme_tag_placement.py`.

### Manifest compatibility

All **135** entries in `.generated-npcs.json` store the trait under `"Accent"`,
and `--regen-manifest` rebuilds an NPC from that stored dict. A bare rename
breaks regeneration for every existing NPC.

The read falls back to the old key, following the precedent already in the file
(`npc.get("Weapon", "")`, `npc.get("Theme", "-")`, both with comments explaining
the same situation). A test pins it.

---

## Budget

Changes and their cost against the token prompt's 2-token p99 headroom:

| Change | Direction |
|---|---|
| §1 template split | **−~15 tokens** |
| §4 hue renames | ~0 |
| §5 Faction: proper noun dropped, visual signature added | net depends on wording |
| §5 pigment-aware closing line | +~2 tokens, only on pigment factions |
| §6 rename | ~0 |

§1 pays for the rest. `test_prompt_budget.py` is the gate: if p99 regresses, the
faction signatures get shorter. The test is not relaxed and the ceiling is not
raised — 512 is Krea 2's limit, not a preference.

## Tests

Extending the existing suite (90 passing):

- **`test_weapon.py`** — civilian tier produces ~2/3 unarmed; `--unarmed` leaves
  `mil` and `Criminals` armed and disarms everyone else; `civilian` is the
  default for an uncategorised non-mil role.
- **`test_stance_filter.py`** (new or folded into the weapon tests) — an empty
  Weapon roll drops both `armed` and `gun` stances; a non-firearm weapon drops
  only `gun`.
- **`test_token_scenery.py`** (new) — a guard test: no `Stance` bullet contains
  scenery, furniture or weather nouns, and `TOKEN_TEMPLATE` does not contain
  `"standing at full height"`. This is what keeps §1 from drifting back.
- **`test_faction.py`** (new) — `split_faction` round-trips all three segments;
  `filter_by_mil` still filters correctly on three-segment bullets; an empty
  visual half contributes nothing to either prompt; the dossier shows the name
  and the prompt shows the visual.
- **`test_glow_rename.py`** (new) — a manifest entry storing `"Accent"`
  regenerates identically to one storing `"Glow colour"`.
- **`test_prompt_budget.py`** — unchanged, must stay green, expected to improve.
- **`test_theme_tag_placement.py`** — updated for the rename.

## Sequencing

1. §6 rename (mechanical, touches the most files, blocks the GUI spec).
2. §1 token template and `Stance` scrub (buys the token budget everything else spends).
3. §2 civilian policy, then §3 `--unarmed` and the `armed` flag.
4. §4 hue renames.
5. §5 Faction restructure, then content, then the pigment-aware closing line.
6. README and `docs/generate-npc.md` updates.

## Out of scope

- Theme-gating the new Faction visual signatures. `Faction` is not currently
  theme-gated and making it so is a separate question.
- The `x30 || none` weight itself. §2 changes the policy layer, not the table's
  own dial.
- Re-rendering the 135 existing NPCs. Nothing here invalidates them; the
  compatibility work in §6 exists so they keep regenerating on demand.
