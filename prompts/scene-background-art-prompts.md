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
