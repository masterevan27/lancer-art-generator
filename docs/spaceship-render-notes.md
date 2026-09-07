# Spaceship render notes — first real renders against ComfyUI

Everything before this document was `--dry-run`. This is the record of the
first two real renders (ComfyUI 0.34.5, `http://127.0.0.1:8000`,
`Lancer_Scene_Workflow_v1.json` + `Util_RemoveBackground_makeTransparent.json`,
default `--rmbg-res 1536`), one at the smallest hull size (1x1 hex) and one at
the largest (5x3 hex) — the case the multi-hex token-framing language exists
for. The 5-hex case failed its framing acceptance check on the first attempt;
`PLAN_FRAMING` and the opening sentence of `TOKEN_TEMPLATE` were tuned once in
response, and the 5-hex case was re-rendered at the same seed. It still did
not achieve a true top-down orthographic view, though the tuning was not
without effect. Both the small-hull and huge-hull cases were re-rendered under
the tuned template so that the small hull's evidence is not stale.

**UPDATE, review round 1 (ruling R10): the tuning below was reverted.** It
narrowed the 5-hex crop and symmetrized the margins, but it did not achieve
its actual purpose — an orthographic top-down view with no crop — and it cost
real prompt-token budget while failing to buy the thing it was spent on. Over
an 800-ship sample, the tuned template pushed the token prompt's p99 to
500/512 and its MAX to 513/512, with 2 of 800 ships' token prompts actually
**exceeding** the 512-token limit (truncated). Truncation cuts the tail of
the prompt, which is exactly where the framing/closing-tag-block language
lives — for the ships most at risk of bad framing, the tuning was actively
working against itself. `PLAN_FRAMING["huge"]` and `TOKEN_TEMPLATE`'s opening
sentence have been restored verbatim to their pre-tuning text (commit
`97914cb`); `generate-spaceship.py` is otherwise identical to that commit.
Both attempts' prompts and both descriptions of what the model actually
returned are kept below unedited, because that comparison — what was tried,
what it cost, and what it did and didn't fix — is the most useful thing this
document can hand to whoever picks the framing problem up next. See
"Review round 1: the tuning was reverted" at the end of this document for the
full accounting, the recovered budget numbers, and what is recommended next.

## Seeds

- **Seed 4242** — `--ship-type patrol --size small` → "Adamant", callsign
  VYY-6349, Patrol boat, Karrakin Trade Baronies. Small hull, 1x1 hexes.
- **Seed 9001** — `--ship-type carrier --size huge` → "Mourner's Due",
  callsign SYO-1707, Carrier, House Clawthorne. Huge hull, 5x3 hexes.

Commands run:
```
python generate-spaceship.py --count 1 --seed 4242 --ship-type patrol --size small --out-root ./render-check
python generate-spaceship.py --count 1 --seed 9001 --ship-type carrier --size huge --out-root ./render-check
```

## 1-hex case (seed 4242, "Adamant") — BEFORE tuning

Rendered under the original `TOKEN_TEMPLATE`. Portrait `(1216, 832)` mode
`RGB`; token `(1024, 1024)` mode `RGBA` (alpha present — RMBG ran).

**Portrait prompt:**
```
A cluttered low angle of a patrol boat, a short-endurance picket, all engine and hull codes, its stores racks stripped back to the frames, fifty-five metres long, two crew hatches and a boarding step let into the flank, rendered in a detailed painterly illustration style with fine grain texture, clean linework and halftone dot shading worked into the shadows, moody cinematic lighting. The hull is a stubby olive-drab hull, a flat wedge body with a low armoured well sunk into the bow and bare mounting plates under the nose, attitude thruster quads clustered at the shoulders and at the tail root. The hull carries a mining laser rerigged as armament, its emitter head clamped in a swivel cradle on a stub crane boom and the coolant lines taped along the jib, and a squat civilian shield housing clamped to the dorsal plating, its single emitter lens hooded and a maker's plate bolted beside it. A hand-patched pilothouse welded onto the spine out of mismatched plating, a name painted by hand along its flank. Heraldic quartering in deep crimson and gold across the flank, a house banner at the prow, recovery and jacking-point stencils marked at each frame station, a working finish, paint dulled chalky on the sunward side. A shipbreaker's yard strung between two captured rocks, cut hull sections stacked in ragged piles, cable runs and worklight strings looped across the gap and a haze of torch smoke drifting through all of it. A dense dust curtain drags through the shot, reducing the far background to a flat pale wash. Keep the rest of the palette restrained - greys, olive drab and rust. Shallow depth of field, high detail, atmospheric sci-fi vessel illustration, painterly brushwork with heavy grain and dense halftone screentone worked into every shadow.
```

**Token prompt (BEFORE tuning):**
```
A top-down orthographic illustration of a patrol boat, a short-endurance picket, all engine and hull codes, its stores racks stripped back to the frames, fifty-five metres long, two crew hatches and a boarding step let into the flank, seen from directly above with the bow toward the top of the frame, the whole hull in frame from bow to stern and wingtip to wingtip with clear empty space on all four sides, rendered in a detailed painterly illustration style with fine grain texture, clean linework and halftone dot shading worked into the shadows, moody cinematic lighting on the hull. The hull is a stubby olive-drab hull, a flat wedge body with a low armoured well sunk into the bow and bare mounting plates under the nose, attitude thruster quads clustered at the shoulders and at the tail root. The hull carries a mining laser rerigged as armament, its emitter head clamped in a swivel cradle on a stub crane boom and the coolant lines taped along the jib, and a squat civilian shield housing clamped to the dorsal plating, its single emitter lens hooded and a maker's plate bolted beside it. A hand-patched pilothouse welded onto the spine out of mismatched plating, a name painted by hand along its flank. Heraldic quartering in deep crimson and gold across the flank, a house banner at the prow, recovery and jacking-point stencils marked at each frame station, a working finish, paint dulled chalky on the sunward side. Keep the rest of the palette restrained - greys, olive drab and rust. Around the hull the background is an empty plain white void. The whole hull roughly as long as it is wide across the wings, a single vessel centered in frame and clear of the frame edge, dramatic lighting, high detail, isolated vehicle illustration, clean silhouette, painterly brushwork with heavy grain and dense halftone screentone worked into every shadow.
```

**Portrait — what it actually looks like:** a low-angle painterly illustration
of a small, heavily weathered grey/olive patrol boat with rust streaking down
the hull. A red-and-gold heraldic quartered shield (lion motif) is painted on
the bow flank. A boxy pilothouse with an antenna mast sits amidships; a
turreted weapon mount (the "mining laser rerigged as armament") sits just aft
of it with a crane boom beside it. The background is a foggy shipbreaker's
yard: stacked rusted hull sections, cable runs, strung worklight bulbs, rock
formations. Fine grain and halftone shading are visible in the shadows. This
reads as the intended painterly house style.

**Token — what it actually looks like:** a single top-down hull on an
off-white/transparent ground, bow at the top of the frame, stern at the
bottom. Long, narrow boat silhouette: pointed bow, tapering rounded stern.
A pilothouse and antenna mast sit amidships-forward; a turret with a barrel
and a round hatch/opening sit aft of it; small deck fittings run down to the
stern. Measured with the alpha channel: content occupies x=[374,650],
y=[20,1005] of the 1024x1024 canvas — margins of 374px left / 376px right
(36.5%) and 20px top / 19px bottom (1.9%). Nothing is clipped at any edge,
but the margin is markedly asymmetric — generous side-to-side, very tight
fore-and-aft. This foreshadowed the 5-hex failure: the model wants to draw a
long boat regardless of the canvas's actual proportions, so on a canvas taller
than the hull needs it fills top-to-bottom; the concern for a canvas *wider*
than the hull needs (the huge/5x3 case) is the reverse — under-filling the
width with the hull left small in the middle.

## 5-hex case (seed 9001, "Mourner's Due") — BEFORE tuning — FAILED

Rendered under the original `TOKEN_TEMPLATE` and `PLAN_FRAMING["huge"]`.
Portrait `(1216, 832)` mode `RGB`; token `(1920, 1152)` mode `RGBA`.

**Portrait prompt:**
```
A head-on view of a mech carrier, a blunt slab of a hull given over almost entirely to hangar volume, with a clear deck run down its dorsal spine, two and a half kilometres bow to stern, lifeboat pods ranked in dozens, rendered in a detailed painterly illustration style with fine grain texture, clean linework and halftone dot shading worked into the shadows, moody cinematic lighting. The hull is a colossal dark-blue slab hull broadening to a squared bow block, a deep open deck recess cut the full length of each flank, ribbed radiator fins down the spine, an incinerator stack standing off the spine on braced legs, its throat crusted black. The hull carries a row of point-defence turrets spaced along the dorsal spine, each a small armoured drum with paired stub barrels, a heavy shield array hung with counterweights between the prow fittings, its field breathing slowly in and out along the plating, and twin full-length catapult decks running the flanks, every plate divided by raised seams and scorch fans spreading back down both deck edges. An armoured bridge slot let into the prow face, a narrow band of thick glass set deep behind a hooded brow of plate. A purple rabbit-skull crest painted huge amidships, votive charms wired along the hull rails, a quarantine seal taped across one hatch, its corners lifting away, field repairs riveted down over older field repairs. A jump point, a vast ring gate hanging against the stars with traffic queued along the approach lane in a strung line of running lights, the aperture warping the starfield into a slow spiral. Keep the rest of the palette restrained - greys, olive drab and rust. Shallow depth of field, high detail, atmospheric sci-fi vessel illustration, painterly brushwork with heavy grain and dense halftone screentone worked into every shadow.
```

**Token prompt (BEFORE tuning):**
```
A top-down orthographic illustration of a mech carrier, a blunt slab of a hull given over almost entirely to hangar volume, with a clear deck run down its dorsal spine, two and a half kilometres bow to stern, lifeboat pods ranked in dozens, seen from directly above with the bow toward the top of the frame, the whole hull in frame from bow to stern and wingtip to wingtip with clear empty space on all four sides, rendered in a detailed painterly illustration style with fine grain texture, clean linework and halftone dot shading worked into the shadows, moody cinematic lighting on the hull. The hull is a colossal dark-blue slab hull broadening to a squared bow block, a deep open deck recess cut the full length of each flank, ribbed radiator fins down the spine, an incinerator stack standing off the spine on braced legs, its throat crusted black. The hull carries a row of point-defence turrets spaced along the dorsal spine, each a small armoured drum with paired stub barrels, a heavy shield array hung with counterweights between the prow fittings, its field breathing slowly in and out along the plating, and twin full-length catapult decks running the flanks, every plate divided by raised seams and scorch fans spreading back down both deck edges. An armoured bridge slot let into the prow face, a narrow band of thick glass set deep behind a hooded brow of plate. A purple rabbit-skull crest painted huge amidships, votive charms wired along the hull rails, a quarantine seal taped across one hatch, its corners lifting away, field repairs riveted down over older field repairs. Keep the rest of the palette restrained - greys, olive drab and rust. Around the hull the background is an empty plain white void. A vast hull filling the frame bow to stern, half again as long as it is broad, a single vessel centered in frame and clear of the frame edge, dramatic lighting, high detail, isolated vehicle illustration, clean silhouette, painterly brushwork with heavy grain and dense halftone screentone worked into every shadow.
```

**Portrait — what it actually looks like:** a head-on painterly shot, low
angle looking up the bow, of a massive dark slab-hulled carrier. A wide
flight/hangar deck runs across the top of frame with visible deck markings
(taxi/launch lines); twin bow-side sponsons each carry point-defence turret
clusters on raised platforms. The prow face below the deck is a huge armoured
wedge with hatches, rivets, a bridge slot. Dark starfield visible around the
superstructure. Rust-red hull striping low on the bow. This matches several
prompt elements directly ("a colossal dark-blue slab hull broadening to a
squared bow block," "a row of point-defence turrets spaced along the dorsal
spine," "an armoured bridge slot let into the prow face"). The purple
rabbit-skull crest and jump-point ring-gate backdrop are not visible in this
framing — plausible given the chosen camera angle, but not independently
confirmed.

**Token — what it actually looks like — THE FAILURE:** this is not a
top-down orthographic view. It is a dramatic, foreshortened, elevated-camera
shot looking down and forward along the flight deck from just above and
behind the bow — visually similar in style to a "carrier splash art" trope,
with the deck's parallel taxi lines converging toward a vanishing point near
a tower/incinerator-stack structure at the top of the frame, drop shadows
consistent with a raked, non-overhead light, and size gradients (turrets
nearer the bottom of frame read larger than the ones near the top). Measured
with the alpha channel: content bbox is x=[59,1871], y=[8,1152] of the
1920x1152 canvas. The bottom edge is **touched exactly** — `b == h == 1152`
— and 1750 of the 1920 pixels in the very bottom row are non-transparent
hull. That is a hard crop: turret housings and hull structure are cut off
flush at the bottom of the frame across nearly the full width of the canvas.
Top margin is 8px (0.7%) — also essentially touching. Left/right margins are
59px/49px (roughly 3%) — tight given the ship reads as "half again as long as
broad," not "vast," in the portion actually shown. This is exactly the
failure mode the brief was written to catch: the stern (or, in this
composition, the aft two-thirds-plus of "two and a half kilometres bow to
stern" hull, since the visible content is only the bow and the flight deck's
forward run) never entered the frame in the first place, and what little of
the ship IS at the frame's trailing edge is itself cropped.

## Step 7: tuning attempt

**Changed, and nothing else** (`generate-spaceship.py`):

`PLAN_FRAMING["huge"]`
- Before: `"a vast hull filling the frame bow to stern, half again as long as it is broad"`
- After: `"a vast hull, half again as long as it is broad, shrunk to fit entirely inside the frame with the bow, the stern and both wingtips all clear of the frame edge"`

`TOKEN_TEMPLATE`'s opening sentence (shared by all four size bands)
- Before: `"A top-down orthographic illustration of {ship}, {size}, seen from directly above with the bow toward the top of the frame, the whole hull in frame from bow to stern and wingtip to wingtip with clear empty space on all four sides, rendered in a detailed painterly illustration style with fine grain texture, clean linework and halftone dot shading worked into the shadows, moody cinematic lighting on the hull. "`
- After: `"A flat top-down orthographic illustration of {ship}, {size}, viewed straight down from directly overhead with no perspective and the bow toward the top of the frame, the entire hull shrunk to fit inside the frame from bow to stern and wingtip to wingtip with clear empty space on all four sides and nothing cropped at any edge, rendered in a detailed painterly illustration style with fine grain texture, clean linework and halftone dot shading worked into the shadows, moody cinematic lighting on the hull. "`

Rationale: the observed failure was not "square ship centred with dead space"
but a forced-perspective shot that crops the trailing edge. The edit adds an
explicit anti-perspective clause ("no perspective," "viewed straight down"),
strengthens the anti-crop language in both the opening sentence and
`PLAN_FRAMING["huge"]`, and switches "filling the frame" (which risks reading
as an instruction to zoom in tight, i.e. to crop) to "shrunk to fit... clear
of the frame edge."

The canvas aspect (1920x1152, still derived from the 5x3 grid footprint) was
**not** touched.

### Both re-rendered at the same seeds under the tuned template

```
python generate-spaceship.py --count 1 --seed 4242 --ship-type patrol --size small --out-root ./render-check
python generate-spaceship.py --count 1 --seed 9001 --ship-type carrier --size huge --out-root ./render-check
```

Both size bands were re-rendered, not just the huge one, because
`TOKEN_TEMPLATE`'s opening sentence is shared by all four bands — the small
hull's earlier (pre-tuning) evidence is not valid evidence for the template
that ships.

## 1-hex case (seed 4242, "Adamant") — AFTER tuning — no regression

Portrait `(1216, 832)` mode `RGB` (unchanged prompt, unchanged image
composition expected — `PORTRAIT_TEMPLATE` was not touched). Token
`(1024, 1024)` mode `RGBA`.

**Token prompt (AFTER tuning):**
```
A flat top-down orthographic illustration of a patrol boat, a short-endurance picket, all engine and hull codes, its stores racks stripped back to the frames, fifty-five metres long, two crew hatches and a boarding step let into the flank, viewed straight down from directly overhead with no perspective and the bow toward the top of the frame, the entire hull shrunk to fit inside the frame from bow to stern and wingtip to wingtip with clear empty space on all four sides and nothing cropped at any edge, rendered in a detailed painterly illustration style with fine grain texture, clean linework and halftone dot shading worked into the shadows, moody cinematic lighting on the hull. The hull is a stubby olive-drab hull, a flat wedge body with a low armoured well sunk into the bow and bare mounting plates under the nose, attitude thruster quads clustered at the shoulders and at the tail root. The hull carries a mining laser rerigged as armament, its emitter head clamped in a swivel cradle on a stub crane boom and the coolant lines taped along the jib, and a squat civilian shield housing clamped to the dorsal plating, its single emitter lens hooded and a maker's plate bolted beside it. A hand-patched pilothouse welded onto the spine out of mismatched plating, a name painted by hand along its flank. Heraldic quartering in deep crimson and gold across the flank, a house banner at the prow, recovery and jacking-point stencils marked at each frame station, a working finish, paint dulled chalky on the sunward side. Keep the rest of the palette restrained - greys, olive drab and rust. Around the hull the background is an empty plain white void. The whole hull roughly as long as it is wide across the wings, a single vessel centered in frame and clear of the frame edge, dramatic lighting, high detail, isolated vehicle illustration, clean silhouette, painterly brushwork with heavy grain and dense halftone screentone worked into every shadow.
```
(`PLAN_FRAMING["small"]` was not touched, so the closing sentence is
unchanged from the before-tuning version above.)

**Token — what it actually looks like:** visually near-identical to the
before-tuning render — same long boat silhouette, bow at top, stern at
bottom, same pilothouse/turret/deck fittings. Measured with the alpha
channel: content bbox x=[372,650], y=[19,1006] — margins 372px left / 374px
right (36.3%/36.5%), 19px top / 18px bottom (1.9%/1.8%) — within a few
pixels of the before-tuning measurement (374/376/20/19). **No regression**:
the stronger "shrunk to fit... nothing cropped at any edge" language did not
push the small hull into an over-margined, needlessly small rendering; the
1-hex composition is effectively unchanged.

## 5-hex case (seed 9001, "Mourner's Due") — AFTER tuning — STILL FAILS

Portrait `(1216, 832)` mode `RGB`. Token `(1920, 1152)` mode `RGBA`.

**Token prompt (AFTER tuning):**
```
A flat top-down orthographic illustration of a mech carrier, a blunt slab of a hull given over almost entirely to hangar volume, with a clear deck run down its dorsal spine, two and a half kilometres bow to stern, lifeboat pods ranked in dozens, viewed straight down from directly overhead with no perspective and the bow toward the top of the frame, the entire hull shrunk to fit inside the frame from bow to stern and wingtip to wingtip with clear empty space on all four sides and nothing cropped at any edge, rendered in a detailed painterly illustration style with fine grain texture, clean linework and halftone dot shading worked into the shadows, moody cinematic lighting on the hull. The hull is a colossal dark-blue slab hull broadening to a squared bow block, a deep open deck recess cut the full length of each flank, ribbed radiator fins down the spine, an incinerator stack standing off the spine on braced legs, its throat crusted black. The hull carries a row of point-defence turrets spaced along the dorsal spine, each a small armoured drum with paired stub barrels, a heavy shield array hung with counterweights between the prow fittings, its field breathing slowly in and out along the plating, and twin full-length catapult decks running the flanks, every plate divided by raised seams and scorch fans spreading back down both deck edges. An armoured bridge slot let into the prow face, a narrow band of thick glass set deep behind a hooded brow of plate. A purple rabbit-skull crest painted huge amidships, votive charms wired along the hull rails, a quarantine seal taped across one hatch, its corners lifting away, field repairs riveted down over older field repairs. Keep the rest of the palette restrained - greys, olive drab and rust. Around the hull the background is an empty plain white void. A vast hull, half again as long as it is broad, shrunk to fit entirely inside the frame with the bow, the stern and both wingtips all clear of the frame edge, a single vessel centered in frame and clear of the frame edge, dramatic lighting, high detail, isolated vehicle illustration, clean silhouette, painterly brushwork with heavy grain and dense halftone screentone worked into every shadow.
```

**Token — what it actually looks like:** the same forced-perspective
composition as the before-tuning render — a raised, foreshortened view
looking down the flight deck toward a tower/incinerator structure near the
top of frame, with converging deck lines, directional shadows and a
size gradient, not a flat orthographic top-down. Turret clusters and hull
structure are again cut off flush at the bottom edge. Measured with the
alpha channel: content bbox x=[236,1684], y=[9,1152]. The bottom edge is
again **touched exactly** (`b == h == 1152`), with 1352 of 1920 bottom-row
pixels non-transparent — still a hard crop, though narrower than before
(1352 vs 1750 px). Top margin 9px (0.8%, essentially unchanged from 8px).
Left/right margins widened from 59px/49px to 236px/236px (12.3% each) — the
tuning did measurably pull the hull narrower and more centered
left-to-right, and made the margins symmetric — but it did **not** fix the
two things that matter: the view is still not orthographic, and the trailing
edge of the ship is still cropped at the bottom of the frame.

## Step 5: the four acceptance checks, answered

Answered against the AFTER-tuning 5-hex render, since that is the version
that would ship.

1. **Aspect.** `1920/1152 = 1.6667`; `5/3 = 1.6667`. Exact match — **PASS**.
   No distortion when Foundry stretches the image into the token rectangle.
2. **Framing.** **FAIL.** The hull is not rendered as a long top-down
   silhouette filling the frame bow to stern. Instead the model renders a
   dramatic, foreshortened, elevated-angle view down the flight deck — the
   same failure mode in both the before- and after-tuning renders, just with
   narrower crop after tuning. This is not the "roughly square ship centred
   with dead space" failure mode the brief specifically named as the thing
   to watch for; it is arguably a related but distinct failure — the model
   is not respecting "orthographic" or "directly overhead" at all for this
   ship type/theme, regardless of how strongly that is asserted in text.
3. **Cropping.** **FAIL.** The trailing edge (bottom of frame, opposite the
   bow) is cut off flush against the canvas edge in both renders — 1750/1920
   px (before) and 1352/1920 px (after) of the bottom row are non-transparent
   hull. The near-touching top margin (8-9px) is not itself a crop but
   leaves almost no room for error.
4. **Alpha quality.** Where the RMBG mask DID have edges to work with (top,
   left, right), it held up well: thin structures — the antenna mast/wire
   rigging on the tower structure, the long thin gun barrels on every turret
   cluster, the raised deck-edge railings — are all visibly present and
   distinct against the transparent ground in both the before- and
   after-tuning tokens, at the default `--rmbg-res 1536`. No obvious
   thread-thin structure loss was observed. (The bottom-edge crop is a
   framing/composition problem upstream of RMBG, not a masking problem —
   there is no alpha to lose along an edge the generation itself cut off.)
   `--rmbg-res 1024` was not tried since the default resolution's alpha was
   not the limiting factor here.

**Verdict: the wide-token framing did not pass, before or after tuning.**
The tuning was not wasted — it narrowed the crop (1750→1352 px of the bottom
row) and widened/symmetrized the side margins (59/49px → 236/236px each) —
but it did not produce a true top-down orthographic view or eliminate the
crop. Within the scope this task permits (only `PLAN_FRAMING` and the token
template's framing sentence — not CFG, not the workflow, not a negative
prompt), a second, more aggressive tuning pass could be tried, but there is
a real possibility that this specific checkpoint/LoRA has a strong learned
prior for carrier-shaped hulls toward the "raised view down the flight deck"
composition (a common trope in this art style) that text framing alone,
at CFG 1.0, cannot fully override. That is a finding for whoever picks this
up next, not something this task resolved.

## Step 6: dossier and manifest verification (F1 confirmed by inspection)

Both dossiers (`Adamant.md`, `Mourner's Due.md`) were read in full and match
the prompts recorded above verbatim, plus the full rolled-trait table (hull,
detail, weapon, shield, catapult, bridge, markings, condition, glow, etc.).

Manifest (`.generated-npcs.json`) after both AFTER-tuning renders — two
`spaceship`-kind entries, one per seed:

```
id           'ship-adamant-4242'      str
kind         'spaceship'              str
sizeBand     'small'                  str
hexes        1                        int
gridWidth    1                        int
gridHeight   1                        int
tokenWidth   1024                     int
tokenHeight  1024                     int

id           'ship-mourners-due-9001' str
kind         'spaceship'              str
sizeBand     'huge'                   str
hexes        5                        int
gridWidth    5                        int
gridHeight   3                        int
tokenWidth   1920                     int
tokenHeight  1152                     int
```

**F1 confirmed by inspection**, on the case that matters (5x3, not 1x1):
`gridWidth`/`gridHeight` are `5`/`3` — **grid units**, matching the 5x3 hex
footprint — and `tokenWidth`/`tokenHeight` are `1920`/`1152` — **pixels** —
and all four are Python `int`, not `str` or `float`. The GUI's importer must
send `gridWidth`/`gridHeight` (not `tokenWidth`/`tokenHeight`) to Foundry's
grid-size field, or a 1920 would draw a 1x1 ship the width of a continent.

## Prompt token budget after tuning

The tuning materially lengthened `TOKEN_TEMPLATE`'s opening sentence for
every size band. `test/test_ship_prompt_budget.py` (p99 over a 1500-ship
sample, `TOKEN_LIMIT = 512`) still passes, but headroom is now thin:

- Portrait p99: 453 / 512 (unaffected — `PORTRAIT_TEMPLATE` was not
  touched).
- Token p99: **499 / 512** — 13 tokens of headroom, down from roughly 363
  before this change. *(Superseded — this "363" figure was a coordinator
  error: a single dry-run measurement compared against a p99, two different
  statistics. The authoritative pre-tuning figure, measured the same way as
  the number above, is p99 = 460, i.e. 52 tokens of headroom — see "Budget,
  before and after the revert" below.)* The single longest sampled token
  prompt in the run was 513 tokens, one over the limit (the p99 assertion
  tolerates this — see the test's own docstring on why p99 rather than max is
  asserted — but the margin for the *next* change to this template is now
  small).

This is a real constraint for whoever tunes `PLAN_FRAMING`/`TOKEN_TEMPLATE`
next: there is only about a dozen tokens of headroom left at p99 before a
further lengthening starts failing this test.

## Files changed

*(Superseded by the revert — see "Review round 1: the tuning was reverted"
below. At the time this section was written, mid-task, `generate-spaceship.py`
did carry the `PLAN_FRAMING["huge"]`/`TOKEN_TEMPLATE` edit described here. It
no longer does: the tuning was reverted verbatim, so this task's net effect on
`generate-spaceship.py` is **zero changed lines** — `git diff --stat 97914cb
HEAD -- generate-spaceship.py` is empty. The paragraph below is left as
written for the historical record of what the tuning attempt touched before
it was undone.)*

- `generate-spaceship.py` — `PLAN_FRAMING["huge"]` and `TOKEN_TEMPLATE`'s
  opening sentence, as diffed above. Nothing else in this file changed.
- `docs/spaceship-render-notes.md` — this file, new.
- `generate-npc.py`, `generate-art.py`, `generate-3d.py`, `ship_policy.py` —
  zero lines changed (`git diff --stat HEAD -- generate-npc.py
  generate-art.py generate-3d.py ship_policy.py` is empty).

## Test suite

`python -m unittest discover -s test -q` → **1069 passed, 0 failed, 0
skipped**, both before and after the `PLAN_FRAMING`/`TOKEN_TEMPLATE` edit.
`test/test_ship_prompt_budget.py` and `test/test_ship_prompts.py` specifically
re-run and pass (see above for the budget numbers).

## Open concern for the next person

The wide-token framing does not yet meet its acceptance bar. The stern (or,
for this particular hull, the aft majority of the ship) is cropped at the
canvas edge in both the untuned and the tuned render, and the view reads as a
dramatic elevated shot rather than a flat orthographic top-down, regardless
of how explicitly "orthographic," "no perspective," and "nothing cropped at
any edge" are asserted in the prompt. Options for whoever picks this up,
roughly in order of how much they cost:

1. A further, more aggressive prompt-only pass within the same scope this
   task used (there is ~13 tokens of budget headroom left at p99 — any
   further lengthening should look for words to cut, not just words to add).
2. Testing whether the failure is specific to the "carrier" ship-type/theme
   pairing rolled by seed 9001, by rendering a different huge-band ship type
   at the same grid footprint, to see whether the composition bias is
   type-specific or applies to every huge hull.
3. A workflow- or sampler-level change (CFG, negative prompt, etc.) — out of
   this task's permitted scope, but worth naming since prompt text alone did
   not resolve it after one real attempt.

**This section (and the ~13-token headroom figure in point 1 above) describes
the state as it stood immediately after the tuning attempt. It was
superseded the same review cycle — see the next section.**

## Review round 1: the tuning was reverted

The controller reviewed the tuning attempt above and measured its true
budget cost independently, over an 800-ship sample (this document's own
in-attempt measurement, taken over a 1500-ship sample with a stale p99-only
metric, undercounted the damage by not reporting MAX or the over-limit
count):

```
TUNED template, n=800:  token prompt p50=429  p99=500  MAX=513  limit=512
                         2 of 800 ships' token prompts EXCEED the limit
```

Two ships in every 800 were being truncated by ComfyUI/the encoder at 512
tokens. Truncation cuts the *tail* of the prompt — and the tail of
`TOKEN_TEMPLATE` is exactly where `{plan}` and the closing tag block
("...a single vessel centered in frame and clear of the frame edge...")
live, which is the framing language the tuning existed to strengthen. So for
precisely the ships most at risk of being cropped, the tuned prompt was
actively sabotaging itself: the longer opening sentence pushed the total
length past the point where the framing reinforcement at the tail would even
reach the model intact.

**Ruling (R10): a change that fails its stated purpose (fixing the framing)
while consuming real budget is strictly worse than no change.** The tuning
did narrow the crop (1750→1352 non-transparent bottom-row pixels) and
symmetrize the margins (59px/49px → 236px/236px) — that observation stands,
it is not being dismissed — but it did not produce an orthographic view or
eliminate the crop, which is what it was actually for. Spending budget on a
partial, cosmetic improvement while failing the goal is not a trade worth
keeping. The tuning can be reapplied deliberately later by whoever has
actually solved the framing problem and can show it is worth the tokens —
that is a decision for that attempt to make with a working fix in hand, not
something that should ride along as a side effect of a failed one.

### The revert

`PLAN_FRAMING["huge"]` and `TOKEN_TEMPLATE`'s opening sentence were restored
verbatim to the text at commit `97914cb` (`git show
97914cb:generate-spaceship.py` was the source of truth). `git diff 97914cb --
generate-spaceship.py` is empty — the file is byte-identical to that commit
again. Nothing else in the file was touched.

### Budget, before and after the revert (the numbers the next attempt needs)

Measured with `test/ship_prompt_budget.py`'s own `measure()` over an 800-ship
sample (`seed=0`, `ship.DEFAULT_TABLES`), matching the controller's
methodology, and cross-checked at 1500 ships:

```
TUNED (as committed in 1c0364c), n=800:
  token prompt   p50=429  p99=500  MAX=513  limit=512
  2 of 800 ships' token prompts EXCEED the limit (truncated)

REVERTED (current, == 97914cb), n=800:
  token prompt   p50=407  p99=460  MAX=474  limit=512
  0 of 800 ships' token prompts exceed the limit
  portrait       p50=391  p99=456  MAX=469

REVERTED (current, == 97914cb), n=1500 (cross-check):
  token prompt   p50=406  p99=460  MAX=474  limit=512
  0 of 1500 ships' token prompts exceed the limit
```

The revert recovers the budget: MAX is back to 474, well under 512, and the
over-limit count is back to 0 at both sample sizes.

**On the "~137 tokens of headroom" figure:** the review round asked this
document to record that the remaining headroom at p99 against the
pre-tuning baseline is roughly 137 tokens (i.e. p99 ≈ 375). My own
measurement, using the project's own `test/ship_prompt_budget.py:measure()`
and `test/test_ship_prompt_budget.py`'s own p99 definition
(`sorted(values)[int(len(values)*0.99)]`), against the exact
now-reverted-to-97914cb template, gives **p99 = 460, i.e. headroom of 52
tokens** at both n=800 and n=1500 — not 137. I could not reproduce a p99 of
375 against this template with this measurement method and am recording the
actual measured number rather than the estimate, per this task's standing
instruction to verify before asserting. Whoever spends this budget next
should treat **52 tokens of headroom at p99 against the reverted (pre-tuning)
baseline** as the working number, and re-measure with
`test/ship_prompt_budget.py` before relying on either figure.

### Covering test run after the revert

```
python -m unittest discover -s test -q
```
→ **1069 passed, 0 failed, 0 skipped.**

```
python -m unittest test.test_ship_prompt_budget -v
```
→ `test_portrait_p99_is_under_the_limit`, `test_the_sample_is_not_vacuous`,
`test_token_p99_is_under_the_limit` — all `ok`. (This test's own p99-only,
1500-ship-sample assertion would in fact have passed even under the *tuned*
template, at p99=499/512 — it does not sample MAX or the over-limit count,
which is why the controller's independent 800-ship measurement, which does,
was the one that caught the truncation. That gap in the existing test's
coverage is itself worth flagging for whoever next touches this file, though
fixing it is outside this task's scope.)

### What is recommended next, and what is not

The framing failure described above (Step 5: forced-perspective composition
on the huge/5-hex carrier, hard crop at the trailing edge, both before and
after the reverted tuning attempt) is unresolved. A prompt-level fix was
attempted here — twice, in effect, since both the original and tuned wording
were tried — and neither produced an orthographic top-down view for this
ship. Only the "carrier" ship type at the huge band (seed 9001) was tested;
whether this is a carrier-specific compositional bias (plausible — a raised
view down a flight deck is a very common trope for this ship type in similar
art styles) or a bias that would show up on any huge-band hull was not
tested and is unknown. The next attempt should probably look at the
workflow or CFG level — not at more prompt words — since the words that
were tried did not work and the remaining token budget (52 at p99) is not
large. No workflow or CFG change was attempted in this task; that is
explicitly out of this plan's scope, and is a decision for the user to make
deliberately, not something to be tried opportunistically here.
