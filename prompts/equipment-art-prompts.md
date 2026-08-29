# Equipment Art Prompts (Krea 2 Turbo, ComfyUI)

Shared collection of prompts for gear/equipment art — items that can belong to more than
one pilot's loadout, kept separate from individual character dossiers. All in the
campaign's house style: flat cel-shaded, bold black linework, halftone screentone dot
shading, restrained grey/olive/rust palette with a teal-green atmospheric accent.

## Pattern-A Smoke Charges (smoke mine)

From Absolom "Ledger" Raithe's mech systems loadout — deployable as a grenade or mine,
3 uses.

### Item portrait (detail view, 1024×1024)

```
A close-up illustration of a compact deployable smoke charge device, rendered in flat
cel-shaded style with bold black linework and halftone screentone dot shading in the
shadows, high contrast. The device is a squat cylindrical canister, olive-grey military
hardware with scuffed paint, stenciled warning markings, and a small pressure-trigger
cap on top. Thin wisps of grey-white smoke curl faintly from vents along its side,
suggesting it has just been armed or triggered. It rests on a dusty rockcrete surface,
small chips of debris scattered nearby. Dramatic side lighting casts hard shadow across
half the canister, a faint teal-green atmospheric glow visible in the soft blurred
background haze. Restrained palette of greys, olive drab, and rust, with the teal-green
haze as the color accent. Cinematic close-up composition, halftone shading, high
contrast, tense and utilitarian mood.
```

### Item token/icon (isolated, for the Foundry item sheet)

```
A single compact deployable smoke charge device, viewed from a three-quarter angle,
rendered in flat cel-shaded style with bold black linework and halftone screentone dot
shading, high contrast. The device is a squat cylindrical canister, olive-grey military
hardware with scuffed paint and small stenciled warning markings, a pressure-trigger cap
on top, thin wisps of grey-white smoke curling faintly from its side vents. The
background is a solid flat plain white, no texture, no gradient, no shadow, no
environment. Centered composition, even lighting, isolated object illustration, clean
silhouette.
```

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Portrait at 1024×1024;
token can go smaller (512×512) since it's a simple isolated object. Background-removal
pass optional on the token — a flat white square works fine as a Foundry item icon
without needing true transparency, unlike character/mech tokens.

## Pattern-A Jericho Deployable Cover

From Absolom "Ledger" Raithe's mech systems loadout — unlike the smoke charges, this one
becomes an actual object on the battlefield once deployed, so it needs two different art
pieces: a stowed icon for the item sheet, and a deployed piece built for the map itself.
The deployed piece is top-down like the battlemaps, not front-facing like a character
token, since Foundry treats terrain objects as Tiles on the grid rather than Tokens — a
front-facing icon would look pasted-on next to top-down map art.

### Item icon — stowed/compact state (for the Foundry item sheet, 512–1024px)

```
A compact deployable cover unit in its stowed, folded configuration, viewed from a
three-quarter angle, rendered in flat cel-shaded style with bold black linework and
halftone screentone dot shading, high contrast. It's a squat, angular olive-grey
military hardware pack about the size of a rucksack, ribbed folding panels compressed
flat against its sides, a small stenciled "PATTERN-A · JERICHO" marking and hazard
striping near the release latch, scuffed paint and light rust streaking along the edges.
The background is a solid flat plain white, no texture, no gradient, no shadow, no
environment. Centered composition, even lighting, isolated object illustration, clean
silhouette.
```

### Deployed cover — battlefield tile (top-down, transparent background)

```
A top-down, orthographic view of a deployed segmented ballistic cover barrier, freshly
unfolded and standing upright on the ground: three or four hinged olive-grey armor
panels fanned out in a shallow arc, ribbed reinforcement ribs, stenciled "JERICHO"
markings and hazard striping visible on the panel faces, scuffed paint and rust streaks
consistent with worn military hardware. Shot from directly above so the panel tops,
their thickness, and the short shadow they cast on the ground beneath them are all
visible, exactly the way a piece of terrain would read on a tactical map. Rendered in a
detailed painterly illustration style with fine grain texture and halftone dot shading
in the shadow pockets between panels, bold clean linework on every edge so the barrier
reads clearly as solid cover at a glance. The background outside the object is fully
transparent — no ground, no environment, just the cover piece and its own cast shadow,
isolated and ready to be dropped onto a battlemap as a Foundry VTT tile.
```

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate the deployed
tile against a flat white background as usual, then run it through the ComfyUI-RMBG
background-removal pass (same as the pilot tokens) rather than skipping that step the
way the smoke charge icon does — this one needs true transparency since it sits directly
on top of map art, not on a sheet.

### Foundry note

Import the stowed icon as the system's item icon like any other piece of gear. Import
the deployed tile through the Tiles layer (not Tokens) when it's placed on the
battlemap, and size it to roughly a 2×1 grid footprint so it reads as a real chunk of
cover rather than a single-square prop.
