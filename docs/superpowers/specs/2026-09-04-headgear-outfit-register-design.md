# Headgear and outfit register: keeping hard tech off a kimono

> **Status:** design, 2026-09-04, for branch `headgear-outfit-register`,
> since merged to `main` (`a5b0b67`).
> A direct follow-on to the [role/dress-register
> spec](2026-09-04-role-dress-register-design.md), which added a register axis
> to Outfit and Faction. This adds the missing half: the axis never reached
> Headgear, so an outfit that survives every dress filter can still be crowned
> with a sealed flight helmet. Interacts with the [raw-bullets
> spec](2026-09-04-raw-bullets-in-the-manifest-design.md) — see §6.

## 1. Problem

A rolled corporate liaison officer came out wearing *"an elaborate floral
kimono layered over a plain white underrobe, sleeves trailing long past the
fingertips"* — and, one clause later, *"a full flight helmet in scuffed pale
grey-white, a tinted visor panel down over the eyes and a small lit accent lens
at the temple, a thin tether cable trailing from the back."*

Neither clause is wrong on its own. The Role is `Officials`, whose
`DRESS_POLICY` is `any` precisely so a liaison can be finely dressed; the
kimono is `|| civ notac dressy` and reached the pool legitimately. The helmet
is an ordinary Headgear bullet. The pairing is the bug: the figure is dressed
for a reception from the neck down and for a cockpit from the neck up, and the
image model resolves that by rendering neither convincingly.

**Headgear has no flags at all.** All 64 base bullets and all 4 in
`Headgear (she) +` are bare prose. Nothing gates them: not `civ`/`mil`, not
`dressy`, not `notac`, not Theme — `Headgear` is listed in `THEMED_TABLES` but
no headgear bullet carries an `@` tag, so `filter_by_theme()` is a no-op over
it. Every one of the 68 is reachable from every NPC the generator can roll.

**The flag that should have caught it already exists and already means this.**
`notac` is documented as *"do not pair this with tactical gear"*. It gates
`Weapon` and `Gear` at `generate-npc.py:949`, which drops `mil` bullets from
both so a kimono carries neither a military rifle nor a tactical assault pack.
It has simply never been extended to the third thing an NPC wears. This is a
gap in an existing design, not a new axis, and the reported prompt is what the
gap looks like.

### Goals

- An Outfit flagged `notac` never pairs with headgear that reads as sealed,
  powered or instrumented modern hardware.
- Every such outfit keeps a varied, idiomatically *right* headgear pool —
  including the traditional and ceremonial register, which is the point.
- `Headgear` stays in `REROLLABLE_TRAITS`. The re-roll button for it must
  survive.
- No pool is ever filtered to empty.

### Non-goals

- **The reverse gate.** A `mil` Outfit can still roll a horned kabuto. That is
  a real and symmetrical clash, and it is deliberately out of scope: it needs a
  second flag value on the same bullets and a policy to consume it, and the
  reported bug does not require it. §7 records what it would take.
- **Theme tags on Headgear.** The table has none, and adding them is the parent
  themed-NPC spec's Phase 4, not this. §7 notes why it would not have fixed
  this bug anyway.
- **Retiring `dressy` or `notac`.** Both stay, unchanged, and §3.1 explains why
  `notac` rather than `dressy` is the gate.
- **The raw-bullets manifest change.** §6 uses the one-flag-at-a-time pattern
  that spec generalises, and says how the two meet.

## 2. Approach

One new flag on the Headgear table, `hardtech`, and one filter that drops those
bullets when the rolled Outfit is `notac`.

```
- {Subject} {wear} a full flight helmet in scuffed pale grey-white, … || hardtech
```

`Headgear` follows `Outfit` in `REQUIRED_TABLES`, so `outfit_notac` is already
set by the time the Headgear pool is assembled — the same ordering guarantee
`Faction` and `Outfit` rely on for `role_mil`, and `Gear` relies on for
`weapon_hands`. No reorder is needed and none is made.

No Outfit bullet changes. The kimono is already `|| civ notac dressy`, and so
are the other twelve `notac` entries in the base table and the seven in
`Outfit (she) +`.

### 2.1 What `hardtech` means

**Modern technology worn on the head.** Concretely: helmets of any kind, sealed
or open; visors and lens rigs worn over the eyes; sensor, night-vision and
scanner hardware; breather and respirator masks; comms headsets and earpieces;
anything strung with cabling or seated on jacks; powered, illuminated or
cybernetic headpieces; and industrial eye and ear protection.

**Not** soft goods — cloth, straw, woven, leather and fur hats, caps, hoods,
bandanas and headbands; not plain eyewear, including lightly-lit eyewear; and
not the traditional or ceremonial register, which is exactly what a kimono
wants above it.

Two boundary cases are settled explicitly because they will otherwise be
relitigated every time someone adds a bullet:

- **Goggles are not `hardtech`.** Both goggle bullets ride pushed up on the
  forehead or clipped to a hood rather than over the eyes, they carry no
  cabling, and goggles over robes is a wasteland-traveller staple rather than a
  clash. Keeping them unflagged also keeps the two hood bullets consistent with
  each other.
- **A traditional hat with technology under it is not `hardtech`.** *"a wide
  woven hat trimmed with small curved horns and hanging tassels, a segmented
  mechanical mask sealed over the nose and mouth beneath it"* is a hybrid that
  was clearly authored for this register. The hat dominates the silhouette and
  the mask sits beneath it; it pairs with a kimono better than most of the
  unflagged bullets do.

### 2.2 Why a new flag rather than `mil`

Reusing `mil` would make the filter a one-line edit to the existing `notac`
branch, since that branch already drops `mil` bullets from `Weapon` and `Gear`.
It is rejected for two reasons.

`mil` means something else on the two tables that carry it. On `Faction` and
`Outfit` it means *an actual issued uniform*, and `filter_by_mil()` uses it to
keep civilians out of dress uniforms and soldiers out of cut-offs. `Headgear`
is not in that filter and is not being added to it. A `mil` flag on headgear
bullets would sit there inviting exactly the drift this file's comments keep
warning about — someone reasonably wiring `Headgear` into `filter_by_mil()` and
silently changing what a civilian can wear.

And it is the wrong word. A segmented cybernetic ear implant, a bulky mechanical
diagnostic rig and a pair of boxy retro-industrial headphones are none of them
military, and all three fight a kimono. Roughly a third of the bullets this
change flags have no military reading at all.

`hardtech` rather than `tac` because `tac` and `notac` differ by two characters
and would appear within a few lines of each other in the same file.

## 3. The gate

In `roll_npc()`, immediately after the existing `notac` branch for `Weapon` and
`Gear`:

```python
# 'notac' reaches the third thing an NPC wears. A traditional or ceremonial
# outfit should no more be crowned with a sealed flight helmet than it should
# carry a military rifle - and unlike Weapon and Gear, Headgear has no 'mil'
# flag to key on, because half the clash is technical rather than military.
if name == "Headgear" and outfit_notac:
    soft = [x for x in options if "hardtech" not in split_flags(x)[1]]
    options = soft or options
```

The `or options` fallback is the same guarantee every filter in that loop
carries: a pool is never narrowed to nothing. It cannot fire today — with no
theme tags on Headgear, the unflagged pool is always the full 25 base bullets —
but it must be there for the moment Phase 4 tags the table.

Headgear is already in the loop's flag-strip list at `generate-npc.py:994`, so
`|| hardtech` comes off the value before it reaches a prompt or a dossier. No
change is needed there, and the existing reason for its presence in that list
(Theme would otherwise ship `|| @tag` to the image model) now has a second one.

### 3.1 Why `notac` and not `dressy`

`dressy` is the narrower flag and the reported outfit carries both, so it would
also fix the reported case. It is the wrong gate.

`dressy` means *ceremonial, formal or finely made* and exists to answer a
question about the **Role**: may this person's job be seen in finery? It gates
6 base and 7 feminine Outfit bullets. `notac` means *do not pair with tactical
gear* and answers a question about the **garment**: does this thing sit
alongside hard kit? It covers 13 base bullets, and the seven where the two
disagree — the pilgrim's robes, the travel-worn robe, the tattered robe, the
ragged cloth bindings, the weathered haori and the two plainer dark robes — are
precisely the ones this change must also cover. A pilgrim in layered
travel-stained robes under a night-vision helmet is the same bug as the liaison
in the kimono; none of those bullets is finery, several read as poorer than the
default coveralls, and `dressy` would leave every one of them wearing sealed
hardware.

Gating on `notac` also means Faction is not involved, and needs no equivalent
of the visual-stripping the dress spec gave it. Headgear takes no input from
Faction.

## 4. The table

39 of the 64 base bullets take `|| hardtech`. All 4 in `Headgear (she) +` stay
unflagged — they are hairbands, a fabric band, a glowing accent band and a
woven hat.

### 4.1 Flagged `hardtech` (39)

Helmets and full head enclosures: the padded pilot skullcap with its folded
visor; the composite ballistic helmet; the full flight helmet (the reported
one); the night-vision helmet; the hooded shroud over a full-face helmet; the
open-face crash helmet; the ballistic helmet with the breather mask; the sleek
pilot's helmet with HUD readouts; the scuffed recon helmet; the domed
burnt-orange flight helmet; the sealed tactical helmet; the blue-visored
full-face helmet under a hood; the sleek angular powered helmet.

Visor and lens rigs: the monocular sensor rig; the sleek integrated visor
plate; the bulky visored rig with the stub antenna; the bulky illuminated
graffitied visor rig; the curved white ear plate with the antenna horn; the
sleek red-tinted visor skullcap; the compact visor rig pushed above the brow;
the compact sensor rig clipped into the hair; the slim translucent visor band;
the red-plated visor rig; the sleek visored headset with the jaw guard; the
russet leather flight cap with the monocular scanner lens.

Comms and audio hardware: the padded flight headset with the boom mic; the
lightweight comms earpiece; the sleek black mechanical ear headset; the compact
red-panelled over-ear headset; the boxy retro-industrial headphones; the chunky
over-ear headset with the lit accent rings.

Masks and cybernetics: the sleek mechanical half-mask; the close-fitted
respirator under tactical eyewear; the segmented cybernetic ear-and-jaw
implant; the segmented white cybernetic headpiece; the bulky mechanical
diagnostic rig.

Tactical and industrial: the tactical cap with dark sunglasses; the heavy ear
defenders; the welding visor.

### 4.2 Left unflagged (25 base, 4 feminine)

`bare-headed` (weighted `x6`); the scratched flight goggles pushed up; the soft
crew cap; the rolled bandana; the knitted watch cap; the ushanka with the unit
star; the stiff peaked officer's cap; the deep hood with goggles clipped to
it; the flat-brimmed ball cap; the wide woven sedge hat; the pale cloth under a
straw hat; the gold-trimmed ear headset; the round wire-rimmed glasses; the
tinted wraparound sunglasses; the lacquered bird-skull hat; the thin
rectangular glasses; both horned kabuto helmets; the gold-rimmed lacquered hat
with the red tassel; the woven hat with horns, tassels and a mask beneath; the
straw hat with hanging bells; the broad ceremonial hat with tasseled bells; the
spiked woven hat; the dark hat with chain ornaments and a feather crest; the
straw hat over a cloth headband.

Three of those are judgement calls worth naming, since the argument for
flagging each is real:

- **The lightweight comms earpiece** and **the sleek black mechanical ear
  headset** are flagged, while **the gold-trimmed ear headset** is not. All
  three are ear-mounted comms hardware; the third was written with gilding on
  it, which is a deliberate signal that it belongs with fine dress.
- **The stiff peaked officer's cap** stays unflagged. It is military, but it is
  cloth and formal, and it belongs to the same dress-uniform register as the
  outfits this filter protects.
- **Both kabuto helmets are helmets and stay unflagged**, because `hardtech`
  is about modern technology, not about head coverage. The mempo-faceplate
  kabuto with red-lit eyes is the single most on-register piece of headgear in
  the table for a `notac` outfit.

### 4.3 The resulting pool

A `notac` outfit rolls from 25 base bullets, 30 by weight — 29 and 35 for a
woman, whose four extra bullets include a `x2` hairband. It contains the whole traditional register (two kabuto, two lacquered
hats, the bird-skull hat, four straw and woven hats, the ceremonial tasseled
hat), the soft caps and hoods, all three eyewear bullets, and a heavily
weighted bare-headed. That is not a fallback pool; it is a better-matched one
than the full table.

## 5. Keeping Headgear re-rollable

`Headgear` is one of the 11 entries in `REROLLABLE_TRAITS`, and gating it on
another trait's flag is exactly what puts a trait into `UNREROLLABLE_REASONS`:
the manifest stores Outfit with its flags stripped, so a re-roll cannot tell
whether the outfit was `notac`. Doing nothing would delete the Headgear re-roll
button from the import GUI, which derives its button list from this tuple.

The register is therefore recorded, following the precedent the file already
names — `young` is a manifest key of its own for exactly this reason.

- `roll_npc()` sets `npc["_outfit_notac"]` beside the `npc["_young"]` it
  already sets, in the same `if name == "Outfit"` branch that reads the flag.
- Both manifest write sites write it: the fresh-roll entry at
  `generate-npc.py:2322` and the regen/re-roll rewrite at `:2115`, in both
  cases beside `"young"`.
- `regenerate_one()` reads it back as
  `npc["_outfit_notac"] = entry.get("outfit_notac", False)`.
- `reroll_trait()` gains a branch next to the `Build`/`young` one:

  ```python
  if name == "Headgear" and npc.get("_outfit_notac"):
      soft = [x for x in options if "hardtech" not in split_flags(x)[1]]
      options = soft or options
  ```

**Entries written before this change** have no `outfit_notac` key and default
to `False`, which is today's unrestricted behaviour — a re-roll of Headgear on
an old entry can still hand back a flight helmet, exactly as it does now. A
warning is printed when the key is missing *and* the trait being re-rolled is
`Headgear`, so the message appears where it means something rather than on
every regen. It mirrors the wording of the existing missing-`young` warning and
says what to do: re-roll the NPC to pick the register up.

Deriving the flag instead, by matching the stored Outfit prose back to the
Outfit table, is rejected. Outfit bullets contain `{possessive}` slots that are
substituted before storage, and an edited or deleted bullet stops matching — a
lookup that silently returns "not `notac`" on failure is worse than a recorded
value that is honestly absent.

## 6. Relationship to the raw-bullets spec

[Storing raw bullets in the
manifest](2026-09-04-raw-bullets-in-the-manifest-design.md) generalises this
exact problem and would make `outfit_notac` redundant: with `rawTraits` present,
a re-roll is a full `roll_npc()` with every other trait pinned, and the flag
comes off the raw Outfit bullet with no bespoke key. That spec is design-only
and not started, and this change does not wait for it.

`outfit_notac` therefore joins `young` as a key that spec subsumes, and that
spec's §2.1 — which deletes the hand-written filter rebuilds in
`reroll_trait()` — deletes the new branch in §5 along with the other eleven.
A note to that effect belongs in the raw-bullets spec so the two do not drift.

The manifest gains one additive boolean key. `docs/foundry-importer-contract.md`
in the import GUI governs the HTTP surface rather than the manifest schema, and
that repo does no schema validation and never reads `young`, so nothing there
breaks.

## 7. What this deliberately leaves

**The reverse gate.** Nothing stops a modern combat uniform rolling a horned
kabuto or a ceremonial tasseled hat. Doing it properly means a second value on
the same axis — a `formal` or `trad` flag on roughly a dozen Headgear bullets —
plus a decision about which Outfits reject it, which is not simply `mil`: the
black formal dress uniform should keep a peaked cap and reject a bird-skull
hat, and both are unflagged today. It is a coherent follow-up and a larger one.

**Theme tags on Headgear.** Worth having and would narrow this table usefully,
but it would not have fixed the reported bug and must not be mistaken for a fix
for it. The offending flight helmet carries no tag, and under Phase 4 the
untagged neutral pool stays reachable from every theme by design — a neutral
bullet is reachable from a neosamurai NPC precisely so the campaign's plain
worn-industrial look stays available. The helmet would still have been in the
pool. Register and theme are different axes and this change is about register.

## 8. Verification

1. Over several thousand rolls, no NPC with a `notac` Outfit wears a `hardtech`
   Headgear — and `hardtech` headgear still reaches the other outfits at
   roughly unchanged frequency, so the gate narrows what it targets and nothing
   else.
2. Forcing a `notac` Outfit with `--set-trait` produces the same guarantee.
3. The `or options` fallback returns the full pool when a filter would empty it,
   asserted against a fixture whose Headgear table is entirely `hardtech`.
4. A `notac` Outfit still reaches a varied pool — over a few thousand rolls it
   draws more than a handful of distinct headgear values, including at least
   one from the traditional register.
5. `Headgear` is still in `REROLLABLE_TRAITS`, and `--reroll-trait Headgear` on
   an entry recorded as `outfit_notac` never yields a `hardtech` bullet.
6. `--reroll-trait Headgear` on an entry with no `outfit_notac` key re-rolls
   unrestricted and prints the warning.
7. A fresh roll writes `outfit_notac` into the manifest entry; a re-roll rewrite
   preserves it.
8. A plain `--regen-manifest` regen of a pre-change entry produces a
   byte-identical prompt.
9. `test/prompt_budget.py` p99 is unchanged. This change swaps one clause for
   another and adds none.
10. Every `hardtech` flag is stripped before the value reaches a prompt or a
    dossier — no rolled NPC's Headgear text contains the substring `hardtech`.
