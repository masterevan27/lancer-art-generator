# Scene & Background Art Prompts (Krea 2 Turbo, ComfyUI)

Wide establishing/mood shots — desktop backgrounds, loading screens, dramatic moment illustrations — as opposed to top-down tactical battlemaps (`gm/battlemap-art-prompts.md`) or individual character/equipment art. All in the campaign's house style: bold black linework, halftone screentone shading in the shadows, restrained grey/olive/rust palette with a teal-green atmospheric accent, cinematic lighting, high contrast.

## Mech Squad Battle — Canyon Skirmish

Recreates a wide mech-squad battle composition (two large mechs framed close in the foreground, a heavier gunner mech and additional squad silhouettes in the midground, fighter craft streaking overhead, a ringed planet on the horizon, a fire-scarred canyon) pulled back into the campaign's restrained palette instead of the brighter, more saturated coloring of the original reference — same composition, cooler and more grounded color treatment.

> A wide, cinematic establishing shot of a mech squad standing in a scorched rocky canyon at night, two large humanoid mechs framed close in the foreground on the left and right sides of the frame, shot from a low angle so they loom over the scene — the left one with an angular insectoid head and a single narrow teal-green optic slit, articulated shoulder plating; the right one with a boxier head and a single glowing amber-orange optic lens. Between them in the midground stands a heavier support mech with twin long-barreled cannons raised skyward, and a scattering of several more mechs silhouetted further back near the base of the canyon walls, reading as a full squad rather than a lone pair. High overhead, two fighter craft streak across the sky trailing bright engine flame, small against the vastness of the scene. A massive ringed planet dominates the horizon, its pale curve lit from one side, set against a deep night sky scattered with stars that fades to a restrained teal-green atmospheric haze near the horizon line. Steep rocky canyon walls frame both edges of the frame, and the canyon floor is scarred with fire and glowing fracture lines, thick smoke rising from a few scattered explosions and burning debris. Rendered in bold black linework with halftone screentone dot shading worked into every shadow — the undersides of the mechs, the canyon walls, the smoke — high contrast throughout. Keep the palette restrained: greys, olive drab, and rust on the mech plating and canyon rock, with the teal-green atmospheric accent as the dominant cool tone and warm orange fire/embers as the only saturated warm color in the frame, rather than a broad rainbow of bright hues. Cinematic side lighting rakes across the mechs' armor, casting hard-edged shadows and picking out plating seams and battle damage. Wide landscape composition, epic scale, high contrast, dramatic and grounded rather than glossy.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate wide — 1920×1080 or similar landscape ratio — since this is a scene/background piece rather than a portrait or token.

### Note on the reference

The source image leans much more saturated (bright green sky, vivid orange fire, glowing blue/orange optics all at similar intensity) than the campaign's house style calls for. The prompt above keeps the composition — foreground mech pair, midground gunner, background squad, jets, ringed planet, canyon, fire — but reins the palette back to the restrained grey/olive/rust-plus-teal-accent scheme so it reads as part of the same visual family as the portraits, tokens, and battlemaps rather than a standalone glossy piece.

## Pilot's Quarters — Planetrise Through the Porthole

A quiet off-duty interior: a pilot reclining alone in a cramped orbital berth, watching the sun break over the planet below through a large circular porthole. Recreates the composition of a softer, more saturated reference piece in the campaign's house style — same cozy-cabin-in-a-warship framing, but pulled back to the restrained grey/olive/rust palette with the teal-green accent doing the atmospheric work instead of an all-over blue wash.

> A wide interior illustration of a cramped shipboard crew berth at night, viewed straight on from across the room, dominated by a large circular porthole set into the far bulkhead. Through the porthole hangs the curve of a planet below, its cloud banks catching the first hard white starburst of sunrise breaking over the limb, the rest of the view falling away into deep black speckled with stars. Trailing ivy and creeper vines have been trained around the porthole's heavy riveted frame and spill down both bulkheads, softening the hard military geometry. A pilot in a dark fitted flight suit with olive and dull-amber piping reclines on a low bunk on the right side of the frame, seen in profile, knees drawn up, boots planted on the mattress, head turned away from the viewer toward the window — small against the scale of the room, relaxed and off-duty. The left wall is packed with utilitarian shelving: worn books stacked flat and upright, a couple of potted plants, a battered enamel mug still steaming beside a keyboard, and an angled console monitor whose backlit screen reads a plain time-and-date readout in blocky type. More potted succulents and cacti sit on a high shelf on the right. A single narrow recessed light panel in the ceiling glows dull red, the only warm light in the room, while the cold light off the planet does the rest of the work. A worn patterned rug lies on the deck plating between the bunk and the shelves. Rendered in bold black linework with halftone screentone dot shading worked into every shadow — under the shelves, along the bulkhead panel seams, in the folds of the bedding — high contrast throughout. Keep the palette restrained: greys, olive drab, and rust on the bulkheads, deck plating and fixtures, with the teal-green of the vines and the pale cold planetlight as the dominant cool accent and the small red ceiling panel as the only saturated warm note, rather than an overall blue wash. Cinematic backlighting from the porthole rims every surface it touches and throws long hard-edged shadows back into the room. Wide landscape composition, quiet and intimate, grounded rather than glossy.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate wide — 1920×1080 or similar landscape ratio. Bump to CFG ~2.0–2.5 and 10–12 steps if the layout drifts (porthole off-center, figure losing the bunk) — there's a lot of specific furniture placement in this one, and turbo's low step count trades instruction-following for speed. Don't expect the monitor text to render cleanly at turbo settings; it's there to read as a screen, not to be legible.

### Note on the reference

The source image is a soft, heavily saturated all-blue night scene with bright green foliage and glossy anime-style rendering. The prompt above keeps everything load-bearing about it — the circular porthole with planetrise, the ivy framing it, the shelf clutter and plants, the reclining pilot on the bunk, the red ceiling panel, the rug — but swaps the rendering for the campaign's black linework and halftone screentone, and reins the palette back to grey/olive/rust plus the teal-green accent so it sits in the same visual family as the canyon skirmish piece rather than reading as standalone fan art.

## Default Animated Background — Dropship Yard at Dusk

The starting point for `animate-portrait.py --background` when you don't have a
background of your own yet. Composed for that job rather than as a standalone
piece: a wide, deep frontier landing yard with the interest pushed to the edges
and the horizon, a quiet middle where a chat panel will sit, and smoke, cloud,
dust and running lights scattered through it so the Wan pass has something to
move. Nobody is in the frame on purpose — a background this will sit behind
already has a portrait in front of it.

> A wide, cinematic establishing shot of a military dropship landing yard on a
> dusty frontier world at dusk, viewed from ground level across an open apron of
> cracked concrete. Two heavy dropships sit on landing struts toward the left and
> right edges of the frame, their rear ramps lowered, blocky hulls stencilled with
> unit codes and hazard chevrons, running lights glowing along their spines. Between
> them the apron opens out empty toward the horizon, marked with faded guidance lines
> and scattered cargo pallets, crates and coiled cable pushed to the sides. A row of
> corrugated prefab hangars and fuel drums lines the middle distance on the left,
> with tall floodlight masts rising above them, their beams cutting hard cones through
> the dust. On the right a communications mast and a cluster of antennas stand against
> the sky. Thin columns of smoke rise from a burn barrel and from something venting
> beyond the hangars, drifting sideways in a low wind, and loose dust hangs in the air
> at knee height across the whole apron. The horizon is a low broken ridgeline under a
> deep dusk sky, banded cloud stretched across it and catching the last light, a large
> pale moon low above the ridge and the first stars showing higher up. Rendered in bold
> black linework with halftone screentone dot shading worked into every shadow — under
> the dropship hulls, along the hangar corrugations, in the dust and smoke — high
> contrast throughout. Keep the palette restrained: greys, olive drab and rust on the
> hulls, hangars and concrete, with a teal-green atmospheric haze as the dominant cool
> tone and the warm amber of the floodlights and running lights as the only saturated
> warm note, rather than a broad rainbow of bright hues. Cinematic low sidelight rakes
> across the apron and throws long hard-edged shadows toward the viewer. Wide landscape
> composition, deep perspective, no people or figures anywhere in the frame, quiet and
> waiting rather than mid-battle, grounded rather than glossy.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio.

### Note on animating it

Render the still, then feed it to the animator. Two commands, because the still
is a Krea 2 job and the animation is a Wan job:

    python generate-art.py --prompts prompts/scene-background-art-prompts.md --filter Default-Animated-Background --width 1920 --height 1080 --output-prefix LancerBackgrounds

    python animate-portrait.py "<the rendered png>" --background --roll --seed 7

`--filter` is a regex over the section slug, so it also takes a partial name.
Add `--download-to <folder>` to the first command to get the still out of
ComfyUI's output tree and somewhere you can point the second one at.

The `--roll` draws from the `## Background Animation` table in
`prompts/scene-and-spaceship-tables.md`. Every element this prompt puts in the
frame, smoke and dust and cloud and floodlights and running lights, is
something a bullet in that table names, which is why they were put there. See
`docs/animate-portrait.md` for what the render costs and where the `.webp`
lands.

The four sections below are more of the same job — alternates for the same slot,
each composed for `--background` rather than as standalone pieces. They follow
the same three rules the dropship yard does: nobody in the frame, the middle of
the composition left quiet for a chat panel, and every moving element chosen
from what a bullet in the `## Background Animation` table actually names, so
`--roll` has something to move that the picture already contains.

## Orbital Dock — Planetfall Gallery

An observation gallery running along the throat of a Union orbital dock, looking
out across the berths at the planet turning below. The structure is pushed to
the frame edges and the middle is open sky and planet, with the motion — drifting
stars, a vessel crossing the far distance, running lights along the berths —
scattered through the deep field rather than the foreground.

> A wide, cinematic establishing shot of an observation gallery inside a large
> orbital dock, viewed from inside the gallery looking out through a continuous
> wall of tall angular viewport panes that spans the whole frame. Heavy structural
> ribs and riveted stanchions divide the glazing at intervals and frame both edges
> of the frame, with cable runs, conduit and stencilled deck markings on the
> bulkhead and grating underfoot. Beyond the glass the dock's berthing arms reach
> away to the left and right in deep perspective, skeletal gantry structures
> studded with small running lights and numbered berth markers, a heavy freighter
> hull moored along the far arm with its spine lights glowing in a slow row. The
> centre of the view opens out onto nothing but void and the vast curve of a planet
> below, its cloud banks catching hard light along one limb, the terminator falling
> away into a dark hemisphere flecked with the faint amber of settlements. Higher
> up the black is scattered with stars, and a small distant vessel crosses the void
> near the horizon line trailing a pale engine glow. A thin drift of vented gas
> curls slowly from a coupling on the near berthing arm. Rendered in bold black
> linework with halftone screentone dot shading worked into every shadow — under the
> structural ribs, along the gantry trusses, in the planet's dark hemisphere — high
> contrast throughout. Keep the palette restrained: greys, olive drab and rust on
> the gallery structure, gantries and hull plating, with a teal-green atmospheric
> haze and the cold pale planetlight as the dominant cool tones and the warm amber
> of the berth running lights as the only saturated warm note, rather than a broad
> rainbow of bright hues. Cinematic backlighting from the planet rims every surface
> inside the gallery and throws long hard-edged shadows back across the deck toward
> the viewer. Wide landscape composition, deep perspective, enormous sense of scale,
> no people or figures anywhere in the frame, quiet and waiting rather than
> mid-battle, grounded rather than glossy.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio.

## Rain-Slick Arcology Street — Corpro Underlevel

A street at the bottom of a corpro-state arcology stack, hard rain coming down
past the signage. The wet ground and the neon are the point: they give the Wan
pass rippling puddles, water running off every hard edge and a flickering light
source, which is three bullets of the animation table at once. The street runs
away down the middle of the frame and stays quiet.

> A wide, cinematic establishing shot of a narrow street at the bottom of a
> towering arcology stack at night in heavy rain, viewed from ground level looking
> straight down the street into deep perspective. Sheer tenement and utility facades
> rise out of frame on both sides, packed with fire escapes, ducting, hanging cable
> bundles and stacked balconies, closing the frame in to left and right. Vertical
> signage boards and hanging light strips project from the walls at every level,
> glowing through the rain, and a heavy pedestrian bridge crosses overhead in the
> middle distance. The street surface is cracked wet asphalt running with standing
> water, its puddles holding broken reflections of the signage above, faded lane
> markings and a manhole venting a slow column of steam to one side. Shuttered
> storefronts, stacked crates, a dead vending kiosk and a row of bollards line the
> edges of the pavement, pushed to the sides. Rain falls hard and straight, sheeting
> off every ledge, awning and cable in the frame, and the air is thick with haze so
> the far end of the street dissolves into glow. Far above, a sliver of sky between
> the towers shows low cloud lit from beneath by the city. Rendered in bold black
> linework with halftone screentone dot shading worked into every shadow — under the
> balconies and bridge, along the ducting, in the haze at street level — high
> contrast throughout. Keep the palette restrained: greys, olive drab and rust on
> the facades, ducting and asphalt, with a teal-green atmospheric haze as the
> dominant cool tone and the warm amber and dull red of the signage as the only
> saturated warm notes, rather than a broad rainbow of bright hues. Cinematic
> lighting comes almost entirely from the signage and the wet ground bouncing it
> back, throwing hard-edged shadows up the walls. Wide landscape composition, deep
> perspective, no people or figures anywhere in the frame, no vehicles, quiet and
> waiting rather than mid-battle, grounded rather than glossy.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio. Bump to CFG ~2.0–2.5 and 10–12 steps
if the street loses its vanishing point — the deep one-point perspective is the
first thing turbo's low step count gives up.

## Mech Bay — Cradle Deck, Third Watch

A maintenance deck with a chassis up in its service cradle, lit by work lamps and
console glow. Written for the console-and-indicator bullets in the animation
table: every screen, status panel and running light in here is something the Wan
pass can flicker, scroll or pulse without touching the geometry. The cradle sits
off to one side and the deck opens up behind it.

> A wide, cinematic establishing shot of the interior of a military mech
> maintenance bay at night, viewed from the deck floor. A single large humanoid
> mech stands held upright in a heavy service cradle set to the right of the frame,
> seen from below at a low angle, armour panels removed along one flank to expose
> ribbed actuator bundles and structural frame, umbilical hoses and power cabling
> running from its open access ports down to deck couplings. Articulated gantry arms
> and a catwalk wrap around it, hung with tool racks, chain hoists and coiled line.
> To the left the bay opens out into deep perspective down a row of empty cradles,
> each one marked with a stencilled bay number and lined with small status lights,
> the far end of the row fading into haze. The near left wall carries a bank of
> angled console screens and diagnostic panels glowing with blocky readouts,
> waveform traces and rows of indicator lamps, with a rolling equipment cart and
> stacked ammunition crates below them. Overhead, caged work lamps hang from an
> exposed ceiling truss and throw hard cones of light down onto the deck plating,
> and floor grates vent slow columns of steam that catch in the beams. Painted
> safety lines, chevrons and drainage channels mark the deck. Rendered in bold black
> linework with halftone screentone dot shading worked into every shadow — inside the
> cradle structure, under the catwalk, in the steam — high contrast throughout. Keep
> the palette restrained: greys, olive drab and rust on the mech plating, cradles,
> deck and bulkheads, with a teal-green glow off the console screens as the dominant
> cool tone and the warm amber of the work lamps and status lamps as the only
> saturated warm note, rather than a broad rainbow of bright hues. Cinematic overhead
> lighting rakes down across the mech's armour and throws long hard-edged shadows
> across the deck toward the viewer. Wide landscape composition, deep perspective,
> industrial and lived-in, no people or figures anywhere in the frame, quiet and
> off-shift rather than mid-repair, grounded rather than glossy.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio. Bump to CFG ~2.0–2.5 and 10–12 steps
if the cradle and the mech fuse into one mass — the exposed-frame flank is the
detail turbo drops first.

## Snowbound Wreck Field — The Morning After

A battlefield gone cold: hulls half-buried in snow, a few fires still guttering
along the ridge. Composed for the snow and ember bullets in the animation
table — falling snow, wind lifting powder off the drifts, distant fires flickering
on the horizon — with the wrecks arranged along the edges and a bare snowfield
across the middle.

> A wide, cinematic establishing shot of a frozen battlefield at dawn under falling
> snow, viewed from ground level across an open snowfield. The broken hull of a
> large downed mech lies half-buried in a drift on the left of the frame, seen from
> behind and side-on, one arm thrown out and its torso split open, snow collected in
> every horizontal surface and hanging in a shelf along its shoulder plating. On the
> right, the burnt-out shell of an armoured transport sits canted in a shallow
> crater, tracks thrown, hatches open, scorch marks streaking back across the snow
> behind it. Between them the snowfield opens out unbroken toward the horizon,
> crossed only by wind-carved drift lines and a scatter of shell craters ringed with
> dark earth. Twisted structural debris, a bent antenna mast and a fallen signal pole
> with its cabling trailing across the snow stand in the middle distance. The horizon
> is a low ridgeline of dark rock under a heavy overcast sky, and along it several
> small fires still burn in the wreckage, guttering low, thin columns of black smoke
> rising from them and bending sideways in the wind. Snow falls steadily across the
> whole frame and loose powder lifts off the tops of the drifts. Rendered in bold
> black linework with halftone screentone dot shading worked into every shadow —
> inside the split hull, under the transport, in the crater rims and the smoke — high
> contrast throughout. Keep the palette restrained: greys, olive drab and rust on the
> wreckage and exposed earth, with a teal-green cast in the snow shadows and the
> overcast as the dominant cool tone and the warm orange of the distant fires as the
> only saturated warm note, rather than a broad rainbow of bright hues. Cinematic
> flat overcast light with a low hard rim of dawn along the ridge, shadows long and
> soft-edged across the snow. Wide landscape composition, deep perspective, desolate
> and still, no people or figures anywhere in the frame, the fighting long over
> rather than mid-battle, grounded rather than glossy.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio.
