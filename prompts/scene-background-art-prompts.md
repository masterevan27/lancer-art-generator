# Scene & Background Art Prompts (Krea 2 Turbo, ComfyUI)

Wide establishing/mood shots — desktop backgrounds, loading screens, dramatic moment illustrations — as opposed to top-down tactical battlemaps (`gm/battlemap-art-prompts.md`) or individual character/equipment art. All in the same house style as the NPC portraits: a detailed painterly illustration with fine grain texture, clean linework and halftone dot shading in the shadows, moody cinematic lighting, and the restrained grey/olive/rust palette with a teal-green atmospheric accent.

The two style sentences in every prompt — the "Rendered in a detailed painterly illustration style…" opener and the "painterly brushwork with heavy grain and dense halftone screentone…" closer — are lifted word for word from `PORTRAIT_TEMPLATE` in `generate-npc.py`, so a background renders in the same family as the portrait that will sit in front of it. Earlier drafts asked for "bold black linework" and "high contrast" instead, the wording the equipment and battlemap files use, and came back inkier and flatter than the portraits. If the portrait template's style wording changes, change it here too.

## Mech Squad Battle — Canyon Skirmish

Recreates a wide mech-squad battle composition (two large mechs framed close in the foreground, a heavier gunner mech and additional squad silhouettes in the midground, fighter craft streaking overhead, a ringed planet on the horizon, a fire-scarred canyon) pulled back into the campaign's restrained palette instead of the brighter, more saturated coloring of the original reference — same composition, cooler and more grounded color treatment.

> A wide, cinematic establishing shot of a mech squad standing in a scorched rocky canyon at night, two large humanoid mechs framed close in the foreground on the left and right sides of the frame, shot from a low angle so they loom over the scene — the left one with an angular insectoid head and a single narrow teal-green optic slit, articulated shoulder plating; the right one with a boxier head and a single glowing amber-orange optic lens. Between them in the midground stands a heavier support mech with twin long-barreled cannons raised skyward, and a scattering of several more mechs silhouetted further back near the base of the canyon walls, reading as a full squad rather than a lone pair. High overhead, two fighter craft streak across the sky trailing bright engine flame, small against the vastness of the scene. A massive ringed planet dominates the horizon, its pale curve lit from one side, set against a deep night sky scattered with stars that fades to a restrained teal-green atmospheric haze near the horizon line. Steep rocky canyon walls frame both edges of the frame, and the canyon floor is scarred with fire and glowing fracture lines, thick smoke rising from a few scattered explosions and burning debris. Rendered in a detailed painterly illustration style with fine grain texture, clean linework and halftone dot shading worked into every shadow — the undersides of the mechs, the canyon walls, the smoke — moody cinematic lighting throughout. Keep the palette restrained: greys, olive drab, and rust on the mech plating and canyon rock, with the teal-green atmospheric accent as the dominant cool tone and warm orange fire/embers as the only saturated warm color in the frame, rather than a broad rainbow of bright hues. Cinematic side lighting rakes across the mechs' armor, casting hard-edged shadows and picking out plating seams and battle damage. Wide landscape composition, epic scale, dramatic and grounded rather than glossy, painterly brushwork with heavy grain and dense halftone screentone worked into every shadow.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate wide — 1920×1080 or similar landscape ratio — since this is a scene/background piece rather than a portrait or token.

### Note on the reference

The source image leans much more saturated (bright green sky, vivid orange fire, glowing blue/orange optics all at similar intensity) than the campaign's house style calls for. The prompt above keeps the composition — foreground mech pair, midground gunner, background squad, jets, ringed planet, canyon, fire — but reins the palette back to the restrained grey/olive/rust-plus-teal-accent scheme so it reads as part of the same visual family as the portraits, tokens, and battlemaps rather than a standalone glossy piece.

## Pilot's Quarters — Planetrise Through the Porthole

A quiet off-duty interior: a pilot reclining alone in a cramped orbital berth, watching the sun break over the planet below through a large circular porthole. Recreates the composition of a softer, more saturated reference piece in the campaign's house style — same cozy-cabin-in-a-warship framing, but pulled back to the restrained grey/olive/rust palette with the teal-green accent doing the atmospheric work instead of an all-over blue wash.

> A wide interior illustration of a cramped shipboard crew berth at night, viewed straight on from across the room, dominated by a large circular porthole set into the far bulkhead. Through the porthole hangs the curve of a planet below, its cloud banks catching the first hard white starburst of sunrise breaking over the limb, the rest of the view falling away into deep black speckled with stars. Trailing ivy and creeper vines have been trained around the porthole's heavy riveted frame and spill down both bulkheads, softening the hard military geometry. A pilot in a dark fitted flight suit with olive and dull-amber piping reclines on a low bunk on the right side of the frame, seen in profile, knees drawn up, boots planted on the mattress, head turned away from the viewer toward the window — small against the scale of the room, relaxed and off-duty. The left wall is packed with utilitarian shelving: worn books stacked flat and upright, a couple of potted plants, a battered enamel mug still steaming beside a keyboard, and an angled console monitor whose backlit screen reads a plain time-and-date readout in blocky type. More potted succulents and cacti sit on a high shelf on the right. A single narrow recessed light panel in the ceiling glows dull red, the only warm light in the room, while the cold light off the planet does the rest of the work. A worn patterned rug lies on the deck plating between the bunk and the shelves. Rendered in a detailed painterly illustration style with fine grain texture, clean linework and halftone dot shading worked into every shadow — under the shelves, along the bulkhead panel seams, in the folds of the bedding — moody cinematic lighting throughout. Keep the palette restrained: greys, olive drab, and rust on the bulkheads, deck plating and fixtures, with the teal-green of the vines and the pale cold planetlight as the dominant cool accent and the small red ceiling panel as the only saturated warm note, rather than an overall blue wash. Cinematic backlighting from the porthole rims every surface it touches and throws long hard-edged shadows back into the room. Wide landscape composition, quiet and intimate, grounded rather than glossy, painterly brushwork with heavy grain and dense halftone screentone worked into every shadow.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate wide — 1920×1080 or similar landscape ratio. Bump to CFG ~2.0–2.5 and 10–12 steps if the layout drifts (porthole off-center, figure losing the bunk) — there's a lot of specific furniture placement in this one, and turbo's low step count trades instruction-following for speed. Don't expect the monitor text to render cleanly at turbo settings; it's there to read as a screen, not to be legible.

### Note on the reference

The source image is a soft, heavily saturated all-blue night scene with bright green foliage and glossy anime-style rendering. The prompt above keeps everything load-bearing about it — the circular porthole with planetrise, the ivy framing it, the shelf clutter and plants, the reclining pilot on the bunk, the red ceiling panel, the rug — but swaps the rendering for the campaign's painterly linework and halftone screentone, and reins the palette back to grey/olive/rust plus the teal-green accent so it sits in the same visual family as the canyon skirmish piece rather than reading as standalone fan art.

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
> unit codes and hazard chevrons, running lights glowing along their spines.
> Between them the apron opens out empty toward the horizon, marked with faded
> guidance lines and scattered cargo pallets, crates and coiled cable pushed to
> the sides. A row of corrugated prefab hangars and fuel drums lines the middle
> distance on the left, with tall floodlight masts rising above them, their beams
> cutting hard cones through the dust. On the right a communications mast and a
> cluster of antennas stand against the sky. Thin columns of smoke rise from a
> burn barrel and from something venting beyond the hangars, drifting sideways in
> a low wind, and loose dust hangs in the air at knee height across the whole
> apron. The horizon is a low broken ridgeline under a deep dusk sky, banded cloud
> stretched across it and catching the last light, a large pale moon low above the
> ridge and the first stars showing higher up. Rendered in a detailed painterly
> illustration style with fine grain texture, clean linework and halftone dot
> shading worked into every shadow — under the dropship hulls, along the hangar
> corrugations, in the dust and smoke — moody cinematic lighting throughout. Keep
> the palette restrained: greys, olive drab and rust on the hulls, hangars and
> concrete, with a teal-green atmospheric haze as the dominant cool tone and the
> warm amber of the floodlights and running lights as the only saturated warm
> note, rather than a broad rainbow of bright hues. Cinematic low sidelight rakes
> across the apron and throws long hard-edged shadows toward the viewer. Wide
> landscape composition, deep perspective, no people or figures anywhere in the
> frame, quiet and waiting rather than mid-battle, grounded rather than glossy,
> painterly brushwork with heavy grain and dense halftone screentone worked into
> every shadow.

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

The sections below are more of the same job — alternates for the same slot,
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
> centre of the view opens out onto nothing but void and the vast curve of a
> planet below, its cloud banks catching hard light along one limb, the terminator
> falling away into a dark hemisphere flecked with the faint amber of settlements.
> Higher up the black is scattered with stars, and a small distant vessel crosses
> the void near the horizon line trailing a pale engine glow. A thin drift of
> vented gas curls slowly from a coupling on the near berthing arm. Rendered in a
> detailed painterly illustration style with fine grain texture, clean linework
> and halftone dot shading worked into every shadow — under the structural ribs,
> along the gantry trusses, in the planet's dark hemisphere — moody cinematic
> lighting throughout. Keep the palette restrained: greys, olive drab and rust on
> the gallery structure, gantries and hull plating, with a teal-green atmospheric
> haze and the cold pale planetlight as the dominant cool tones and the warm amber
> of the berth running lights as the only saturated warm note, rather than a broad
> rainbow of bright hues. Cinematic backlighting from the planet rims every
> surface inside the gallery and throws long hard-edged shadows back across the
> deck toward the viewer. Wide landscape composition, deep perspective, enormous
> sense of scale, no people or figures anywhere in the frame, quiet and waiting
> rather than mid-battle, grounded rather than glossy, painterly brushwork with
> heavy grain and dense halftone screentone worked into every shadow.

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
> straight down the street into deep perspective. Sheer tenement and utility
> facades rise out of frame on both sides, packed with fire escapes, ducting,
> hanging cable bundles and stacked balconies, closing the frame in to left and
> right. Vertical signage boards and hanging light strips project from the walls
> at every level, glowing through the rain, and a heavy pedestrian bridge crosses
> overhead in the middle distance. The street surface is cracked wet asphalt
> running with standing water, its puddles holding broken reflections of the
> signage above, faded lane markings and a manhole venting a slow column of steam
> to one side. Shuttered storefronts, stacked crates, a dead vending kiosk and a
> row of bollards line the edges of the pavement, pushed to the sides. Rain falls
> hard and straight, sheeting off every ledge, awning and cable in the frame, and
> the air is thick with haze so the far end of the street dissolves into glow. Far
> above, a sliver of sky between the towers shows low cloud lit from beneath by
> the city. Rendered in a detailed painterly illustration style with fine grain
> texture, clean linework and halftone dot shading worked into every shadow —
> under the balconies and bridge, along the ducting, in the haze at street level —
> moody cinematic lighting throughout. Keep the palette restrained: greys, olive
> drab and rust on the facades, ducting and asphalt, with a teal-green atmospheric
> haze as the dominant cool tone and the warm amber and dull red of the signage as
> the only saturated warm notes, rather than a broad rainbow of bright hues.
> Cinematic lighting comes almost entirely from the signage and the wet ground
> bouncing it back, throwing hard-edged shadows up the walls. Wide landscape
> composition, deep perspective, no people or figures anywhere in the frame, no
> vehicles, quiet and waiting rather than mid-battle, grounded rather than glossy,
> painterly brushwork with heavy grain and dense halftone screentone worked into
> every shadow.

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
> mech stands held upright in a heavy service cradle set to the right of the
> frame, seen from below at a low angle, armour panels removed along one flank to
> expose ribbed actuator bundles and structural frame, umbilical hoses and power
> cabling running from its open access ports down to deck couplings. Articulated
> gantry arms and a catwalk wrap around it, hung with tool racks, chain hoists and
> coiled line. To the left the bay opens out into deep perspective down a row of
> empty cradles, each one marked with a stencilled bay number and lined with small
> status lights, the far end of the row fading into haze. The near left wall
> carries a bank of angled console screens and diagnostic panels glowing with
> blocky readouts, waveform traces and rows of indicator lamps, with a rolling
> equipment cart and stacked ammunition crates below them. Overhead, caged work
> lamps hang from an exposed ceiling truss and throw hard cones of light down onto
> the deck plating, and floor grates vent slow columns of steam that catch in the
> beams. Painted safety lines, chevrons and drainage channels mark the deck.
> Rendered in a detailed painterly illustration style with fine grain texture,
> clean linework and halftone dot shading worked into every shadow — inside the
> cradle structure, under the catwalk, in the steam — moody cinematic lighting
> throughout. Keep the palette restrained: greys, olive drab and rust on the mech
> plating, cradles, deck and bulkheads, with a teal-green glow off the console
> screens as the dominant cool tone and the warm amber of the work lamps and
> status lamps as the only saturated warm note, rather than a broad rainbow of
> bright hues. Cinematic overhead lighting rakes down across the mech's armour and
> throws long hard-edged shadows across the deck toward the viewer. Wide landscape
> composition, deep perspective, industrial and lived-in, no people or figures
> anywhere in the frame, quiet and off-shift rather than mid-repair, grounded
> rather than glossy, painterly brushwork with heavy grain and dense halftone
> screentone worked into every shadow.

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

> A wide, cinematic establishing shot of a frozen battlefield at dawn under
> falling snow, viewed from ground level across an open snowfield. The broken hull
> of a large downed mech lies half-buried in a drift on the left of the frame,
> seen from behind and side-on, one arm thrown out and its torso split open, snow
> collected in every horizontal surface and hanging in a shelf along its shoulder
> plating. On the right, the burnt-out shell of an armoured transport sits canted
> in a shallow crater, tracks thrown, hatches open, scorch marks streaking back
> across the snow behind it. Between them the snowfield opens out unbroken toward
> the horizon, crossed only by wind-carved drift lines and a scatter of shell
> craters ringed with dark earth. Twisted structural debris, a bent antenna mast
> and a fallen signal pole with its cabling trailing across the snow stand in the
> middle distance. The horizon is a low ridgeline of dark rock under a heavy
> overcast sky, and along it several small fires still burn in the wreckage,
> guttering low, thin columns of black smoke rising from them and bending sideways
> in the wind. Snow falls steadily across the whole frame and loose powder lifts
> off the tops of the drifts. Rendered in a detailed painterly illustration style
> with fine grain texture, clean linework and halftone dot shading worked into
> every shadow — inside the split hull, under the transport, in the crater rims
> and the smoke — moody cinematic lighting throughout. Keep the palette
> restrained: greys, olive drab and rust on the wreckage and exposed earth, with a
> teal-green cast in the snow shadows and the overcast as the dominant cool tone
> and the warm orange of the distant fires as the only saturated warm note, rather
> than a broad rainbow of bright hues. Cinematic flat overcast light with a low
> hard rim of dawn along the ridge, shadows long and soft-edged across the snow.
> Wide landscape composition, deep perspective, desolate and still, no people or
> figures anywhere in the frame, the fighting long over rather than mid-battle,
> grounded rather than glossy, painterly brushwork with heavy grain and dense
> halftone screentone worked into every shadow.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio.

## Blink Gate Approach — Transit Lane Observation Deck

The view from a transit station parked a few hundred kilometres off a blink
gate, looking down the approach lane toward the ring. Written for the stars and
distant-vessel bullets in the animation table: the whole middle of the frame is
void, the gate sits high and small, and the ships in the lane are far enough off
to be running lights rather than hulls.

> A wide, cinematic establishing shot from inside an observation deck aboard a
> transit station in deep space, viewed straight out through a single enormous
> viewport that spans the frame, its heavy angled frame and riveted stanchions
> pushed to the left and right edges. Deck plating, a low guard rail and a run of
> conduit and stencilled markings occupy the bottom edge of the frame, and a
> bank of dim console panels glows along the lower left. Beyond the glass the
> approach lane stretches away into deep perspective, marked by a long double row
> of small navigation beacons blinking in sequence toward a blink gate hanging
> high and centre-right in the far distance, a vast dark ring with a faint
> teal-green shimmer across its interior. Several ships sit in the lane at
> intervals, small at this range, reading mainly as strings of running lights and
> pale engine glow, one heavy freighter drifting slowly toward the ring with its
> spine lights in a slow row. The black is scattered with hard stars, denser
> toward one side where a distant nebula lays a faint band of haze across the
> sky. The middle of the frame is empty void, the beacons and ships kept to the
> edges and the distance. Rendered in a detailed painterly illustration style
> with fine grain texture, clean linework and halftone dot shading worked into
> every shadow — under the viewport frame, along the deck plating, in the dark
> face of the gate ring — moody cinematic lighting throughout. Keep the palette
> restrained: greys, olive drab and rust on the deck structure and viewport frame,
> with the teal-green shimmer of the gate and the cold starlight as the dominant
> cool tones and the warm amber of the running lights and beacons as the only
> saturated warm note, rather than a broad rainbow of bright hues. Cinematic
> backlighting from the gate rims the viewport frame and throws long hard-edged
> shadows across the deck toward the viewer. Wide landscape composition, deep
> perspective, enormous sense of scale, no people or figures anywhere in the
> frame, quiet and waiting rather than mid-battle, grounded rather than glossy,
> painterly brushwork with heavy grain and dense halftone screentone worked into
> every shadow.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio.

## Karrakin Estate — Terrace Above the Valley

A baronial hilltop terrace in the Karrakin style, banners and cabling strung
between the pillars, looking out over cultivated valley floor toward a distant
walled city. Composed for the cloud-and-shadows bullet and the swaying-cables
bullet: the sky is big, the ground is open, and the terrace hardware that can
move is all at the frame edges.

> A wide, cinematic establishing shot from a stone terrace on a hilltop estate at
> late afternoon, viewed from the terrace looking out over a broad cultivated
> valley. Heavy carved stone pillars frame the left and right edges of the frame,
> hung with long heraldic banners in dull crimson and gold, and thick guy cables
> and hanging lanterns are strung between them, a stone balustrade running along
> the bottom of the frame. A pair of ornate but weathered defence turrets sit
> dormant on the terrace corners, their barrels lowered. Below the terrace the
> valley opens out in deep perspective, terraced fields and orchard rows stepping
> down toward a river, a raised rail line crossing on a viaduct in the middle
> distance, and a walled city with tall slender towers and a landing spire rising
> on the far side of the valley against low hills. Long shadows from the hilltop
> stretch across the fields. The sky is huge, three-quarters of the frame, with
> banks of low cloud sliding across it and a few tall cumulus catching the late
> light, a single pale moon showing high up. Dust hangs faintly above the fields
> where the light rakes through. Rendered in a detailed painterly illustration
> style with fine grain texture, clean linework and halftone dot shading worked
> into every shadow — inside the pillars' carving, under the balustrade, across
> the shadowed fields — moody cinematic lighting throughout. Keep the palette
> restrained: greys, olive drab and rust on the stone, fields and turrets, with a
> teal-green atmospheric haze across the far valley as the dominant cool tone and
> the warm amber of the lanterns and the crimson of the banners as the only
> saturated warm notes, rather than a broad rainbow of bright hues. Cinematic low
> sidelight rakes across the terrace and throws long hard-edged shadows from the
> pillars. Wide landscape composition, deep perspective, no people or figures
> anywhere in the frame, stately and quiet rather than mid-battle, grounded
> rather than glossy, painterly brushwork with heavy grain and dense halftone
> screentone worked into every shadow.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio.

## Jungle Relay — Overgrown Comms Station

A long-abandoned relay station being taken back by rainforest. The grass-and-
vines bullet is the whole reason for it: vines on every structure, tall grass
across the clearing, and shafts of light through the canopy that shift as cloud
passes. The dish and the hut are pushed to the sides and the clearing is left
open.

> A wide, cinematic establishing shot of an abandoned communications relay
> station in dense rainforest at midday, viewed from ground level across an
> overgrown clearing. A large rusted parabolic dish on a toppled mast lies angled
> against the trees on the left of the frame, thick vines and creepers hanging off
> its rim and its support struts, ferns growing from the pooled water in its
> bowl. On the right a squat prefab equipment hut sits with its door hanging open
> and its roof buckled, a dead solar array and an antenna cluster leaning off it,
> moss over every panel and vines pouring down its walls. Between them the
> clearing opens out in tall grass and low scrub to a wall of enormous buttress-
> rooted trees in the middle distance, their trunks disappearing up out of frame,
> hanging vines and aerial roots trailing down everywhere. Heavy shafts of
> sunlight break through gaps in the canopy and fall across the clearing in hard
> bright columns, mist and drifting pollen hanging in the beams, and the ground is
> dappled with moving light. A rusted cable spool, a fallen fence line and a
> half-buried supply crate lie in the grass at the edges. Rendered in a detailed
> painterly illustration style with fine grain texture, clean linework and
> halftone dot shading worked into every shadow — under the dish, inside the hut
> door, in the deep shade beneath the trees — moody cinematic lighting throughout.
> Keep the palette restrained: greys, olive drab and rust on the wreckage,
> equipment and tree trunks, with a teal-green cast in the foliage shadows and
> the mist as the dominant cool tone and the warm gold of the sunlight shafts as
> the only saturated warm note, rather than a broad rainbow of bright hues.
> Cinematic light comes almost entirely from the shafts through the canopy,
> throwing hard-edged shadows across the grass. Wide landscape composition, deep
> perspective, no people or figures anywhere in the frame, still and long
> abandoned rather than mid-battle, grounded rather than glossy, painterly
> brushwork with heavy grain and dense halftone screentone worked into every
> shadow.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio.

## Forward Base — Night Perimeter

A forward operating base seen from inside the wire after dark, searchlights
working the ground beyond the berm. Composed for the searchlights bullet:
several towers, several beams, low cloud for them to catch, dust in the air, and
the compound floor left open in the middle for the chat panel.

> A wide, cinematic establishing shot of a forward operating base at night,
> viewed from ground level inside the compound looking out toward the perimeter.
> Stacked earth-filled barrier walls topped with razor wire run across the middle
> distance, broken by a gated vehicle checkpoint dead centre, its drop arm down
> and its lamps dark. Two tall guard towers rise at the left and right of the
> frame, sandbagged platforms on steel legs, each with a large searchlight
> mounted on top throwing a hard beam out over the wire and up across the low
> cloud, dust and moths drifting through the light. Along the left a row of
> parked armoured vehicles sits under camouflage netting, and on the right a
> line of sandbagged tents and a fuel bladder stand beside a stack of supply
> crates and a generator trailer. The compound floor between them is bare packed
> earth and gravel marked with tyre ruts, a few floodlights on masts throwing pools
> of light, a burn barrel smoking near the wall. Beyond the wire a dark plain
> stretches to a low ridgeline under a heavy overcast that the searchlights paint
> from below, a faint glow on the far horizon from something burning a long way
> off. Rendered in a detailed painterly illustration style with fine grain
> texture, clean linework and halftone dot shading worked into every shadow —
> under the netting, along the barrier walls, in the dust beneath the beams —
> moody cinematic lighting throughout. Keep the palette restrained: greys, olive
> drab and rust on the vehicles, barriers and earth, with a teal-green cast in the
> overcast and the searchlight haze as the dominant cool tone and the warm amber of
> the floodlights and the distant fire as the only saturated warm notes, rather
> than a broad rainbow of bright hues. Cinematic lighting comes from the
> floodlights and the searchlight beams, throwing long hard-edged shadows across
> the compound. Wide landscape composition, deep perspective, no people or figures
> anywhere in the frame, watchful and quiet rather than mid-battle, grounded
> rather than glossy, painterly brushwork with heavy grain and dense halftone
> screentone worked into every shadow.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio.

## Rear Echelon — The Ridge From the Supply Dump

A battle happening to someone else: the view from an empty supply dump toward a
ridgeline where the fighting is, tracer and flares flickering along it. Written
for the tracer-fire bullet. The ridge sits along the top third, the dump is
pushed to the edges, and the open ground between stays quiet.

> A wide, cinematic establishing shot of a rear-area supply dump on open ground
> at night, viewed from ground level looking toward a distant ridgeline where a
> battle is under way. Stacks of ammunition crates, fuel drums and pallets under
> tarpaulins fill the left edge of the frame, and a parked cargo hauler with its
> ramp down and a shot-up communications trailer bristling with antennas stand on
> the right, a few camp lanterns hanging dim among them. The ground between opens
> out empty and churned with tyre tracks toward a shallow rise, faded marker
> flags on stakes leaning in the wind. Along the horizon a long dark ridgeline
> runs the full width of the frame, and across it silent threads of tracer arc
> back and forth in thin bright lines, muzzle flashes flicker along its length,
> and two slow illumination flares hang in the sky above it under small
> parachutes, throwing a hard pale light down onto the smoke. Tall columns of
> black smoke rise from several points along the ridge and lean slowly sideways
> in the wind, and a low glow of fires shows behind the crest. The sky above is
> deep night with a band of high broken cloud lit from beneath. Rendered in a
> detailed painterly illustration style with fine grain texture, clean linework
> and halftone dot shading worked into every shadow — under the tarpaulins,
> inside the hauler's hold, in the smoke along the ridge — moody cinematic lighting
> throughout. Keep the palette restrained: greys, olive drab and rust on the
> crates, vehicles and earth, with a teal-green atmospheric haze across the middle
> ground as the dominant cool tone and the warm orange of the tracer, flares and
> fires as the only saturated warm notes, rather than a broad rainbow of bright
> hues. Cinematic light comes from the flares and the distant fires, catching the
> edges of the crates and throwing long hard-edged shadows back toward the viewer.
> Wide landscape composition, deep perspective, no people or figures anywhere in
> the frame, the fighting distant and watched rather than close, grounded rather
> than glossy, painterly brushwork with heavy grain and dense halftone screentone
> worked into every shadow.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio.

## Salt Flat — Burning Crawler on the Convoy Road

A hardpan convoy road on a dry world at the hottest part of the day, a derelict
crawler burning beside it. Composed for the embers-and-heat-shimmer bullet:
one fire, a lot of air to distort above it, dust on the wind, and the road
running away down the empty middle.

> A wide, cinematic establishing shot of a convoy road crossing a vast white
> salt flat under a hard midday sun, viewed from ground level looking straight
> down the road into deep perspective. The road is a raised strip of compacted
> grey hardpan marked with faded lane paint and deep tyre ruts, running dead
> straight to a vanishing point on a horizon of distant flat-topped mesas that
> waver in the heat. On the left a huge wheeled cargo crawler lies derelict and
> canted off the road, its hull burnt out and its cab gone, thick black smoke
> pouring from its rear bay and a low fire still burning inside, embers lifting
> off it into the wind and the air above it rippling with heat shimmer. On the
> right a line of leaning route markers, a toppled water tower on a steel frame
> and a scatter of dropped cargo containers stand along the roadside. The salt
> flat stretches away pure and empty on both sides, cracked into polygons, with
> loose dust and salt blowing low across it in thin sheets and a distant dust
> devil rising on the right horizon. The sky is enormous, pale and bleached, a
> few thin streaks of high cloud and a second small sun low near the horizon.
> Rendered in a detailed painterly illustration style with fine grain texture,
> clean linework and halftone dot shading worked into every shadow — inside the
> crawler's hull, under the containers, in the smoke — moody cinematic lighting
> throughout. Keep the palette restrained: greys, olive drab and rust on the
> crawler, containers and road, with a teal-green cast in the shadows and the far
> haze as the dominant cool tone and the warm orange of the fire and embers as the
> only saturated warm note, rather than a broad rainbow of bright hues. Cinematic
> hard overhead sunlight bleaches the salt and throws short hard-edged shadows
> under everything that stands. Wide landscape composition, deep perspective, no
> people or figures anywhere in the frame, silent and scorched rather than
> mid-battle, grounded rather than glossy, painterly brushwork with heavy grain
> and dense halftone screentone worked into every shadow.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio. Bump to CFG ~2.0–2.5 and 10–12 steps
if the road loses its vanishing point.

## Omninet Relay — Server Cathedral

A planetary omninet relay: a cavernous hall of server stacks and cooling
towers, every surface carrying a readout. Built for the holographic-readouts
bullet — screens to scroll, indicator lamps to pulse, coolant steam to drift —
with the nave of the hall left open down the middle.

> A wide, cinematic establishing shot of the interior of a vast omninet relay
> hall at night, viewed from floor level looking straight down its central
> aisle into deep perspective. Towering server stacks rise on both sides like
> cathedral columns, each one a dark ribbed monolith faced with rows of small
> indicator lamps and narrow status screens, thick cable trunks bundled up their
> sides and disappearing into a vaulted ceiling of ducting and cooling pipes high
> above. Between the columns, tall translucent holographic panels hang in the air
> at intervals, dense blocks of scrolling text, waveform traces and slowly
> turning schematic diagrams glowing pale teal-green, their light falling on the
> polished deck. The central aisle is wide and empty, a raised walkway of dark
> grating with recessed guide lights running to a far bulkhead where a single huge
> circular core housing glows dimly through a wall of glass. Coolant vents along
> the base of the stacks breathe slow columns of white vapour that pool along the
> floor and drift across the aisle, and thin frost rimes the pipework nearest
> them. A few maintenance carts, a rolling ladder and a bank of angled control
> consoles with more readouts sit at the near left and right edges. Rendered in
> a detailed painterly illustration style with fine grain texture, clean linework
> and halftone dot shading worked into every shadow — between the stacks, up in
> the vaulted ceiling, in the vapour — moody cinematic lighting throughout. Keep
> the palette restrained: greys, olive drab and rust on the stacks, grating and
> pipework, with the teal-green glow of the holographic panels and screens as the
> dominant cool tone and the small warm amber indicator lamps as the only
> saturated warm note, rather than a broad rainbow of bright hues. Cinematic
> lighting comes almost entirely from the screens and the floor guide lights,
> throwing long hard-edged shadows up the columns. Wide landscape composition,
> deep perspective, cavernous, no people or figures anywhere in the frame, humming
> and unattended rather than mid-battle, grounded rather than glossy, painterly
> brushwork with heavy grain and dense halftone screentone worked into every
> shadow.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio. Don't expect the holographic text to
render legibly at turbo settings; it is there to read as data, not to be read.

## Armory Foundry — Casting Floor

A Harrison Armory chassis foundry mid-pour, seen from the gantry level. The
embers bullet again, this time indoors: sparks off the crucible, heat shimmer
above the moulds, smoke in the roof trusses. The crucible and the mould line
are pushed to the edges and the floor between them is left clear.

> A wide, cinematic establishing shot of the interior of a vast military
> foundry hall at night, viewed from an elevated gantry looking down the length
> of the casting floor. On the left a huge tilted crucible hangs from an
> overhead crane, pouring a stream of molten metal into a mould below in a
> brilliant fall of sparks and white glare, embers spraying out across the floor
> and rising into the roof. On the right a long line of open mould pits glows
> dull orange from their cooling contents, heat shimmer rippling the air above
> them, and beyond them a row of half-assembled mech torsos hang in armature
> frames along the wall, their plating stencilled with foundry codes. The floor
> between runs open and deep toward a far wall of enormous blast furnaces, their
> tap doors glowing, smoke and steam gathering in the roof trusses and hanging
> under the skylights. Gantry cranes, chain hoists, ladle carts and stacked
> ingots line the edges, and painted safety chevrons and drainage channels mark
> the floor. Caged work lamps hang from the trusses. Rendered in a detailed
> painterly illustration style with fine grain texture, clean linework and
> halftone dot shading worked into every shadow — under the gantries, inside the
> armature frames, in the smoke overhead — moody cinematic lighting throughout.
> Keep the palette restrained: greys, olive drab and rust on the machinery,
> floor and mech plating, with a teal-green cast in the smoke and the high
> shadows as the dominant cool tone and the warm orange-white of the molten metal
> and embers as the only saturated warm note, rather than a broad rainbow of
> bright hues. Cinematic lighting comes from the pour and the mould pits, throwing
> huge hard-edged shadows up the walls and across the trusses. Wide landscape
> composition, deep perspective, industrial and immense, no people or figures
> anywhere in the frame, the machinery working unattended rather than mid-battle,
> grounded rather than glossy, painterly brushwork with heavy grain and dense
> halftone screentone worked into every shadow.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio.

## Ocean Platform — Storm Front

An offshore drilling and refuelling platform on a water world with a storm
rolling in. Written for the rain bullet: the deck is wet steel, rain runs off
every rail and pipe, and the puddles hold the platform's lights. The
helideck sits open in the middle of the frame.

> A wide, cinematic establishing shot of the upper deck of an offshore
> industrial platform on an ocean world at dusk, viewed from deck level looking
> out across an open helideck toward the sea. The helideck is a wide circle of
> wet steel plating painted with a faded landing ring and perimeter lights,
> standing water sheeting across it and holding broken reflections of the lights
> around it. A tall derrick tower rises out of frame on the left, hung with pipe
> runs, ladders and a flare stack burning a low ragged flame at its tip, and on
> the right a stack of crew modules, a crane and a cluster of radar and antenna
> masts stand against the sky, warning lights blinking on the mast tops. Rain
> falls hard and slanting across the whole frame, streaming off every rail,
> ledge and pipe, and spray lifts over the deck edge where the sea heaves
> below. Beyond the helideck the ocean stretches to the horizon, heavy grey swell
> under a towering wall of storm cloud that fills the sky, lit from within by a
> flicker of lightning, a last band of dusk light showing under its leading
> edge. A second distant platform is a small cluster of lights on the horizon.
> Rendered in a detailed painterly illustration style with fine grain texture,
> clean linework and halftone dot shading worked into every shadow — under the
> derrick, along the module walls, in the belly of the storm cloud — moody
> cinematic lighting throughout. Keep the palette restrained: greys, olive drab
> and rust on the platform steel and the sea, with a teal-green cast in the storm
> cloud and the rain haze as the dominant cool tone and the warm amber of the deck
> lights and the flare stack as the only saturated warm notes, rather than a broad
> rainbow of bright hues. Cinematic light comes from the deck lights bouncing off
> the wet steel and the lightning behind the cloud. Wide landscape composition,
> deep perspective, no people or figures anywhere in the frame, braced for weather
> rather than mid-battle, grounded rather than glossy, painterly brushwork with
> heavy grain and dense halftone screentone worked into every shadow.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio.

## Frontier Main Street — Dust Storm Coming

The single street of a Diasporan frontier town with a dust front rolling in
from the end of it. The cloud-and-cables bullet: power lines and hanging signs
to sway, shutters to rattle, a wall of dust to drift. The street runs away down
the middle and stays empty.

> A wide, cinematic establishing shot of the main street of a small frontier
> town on a dry world in late afternoon, viewed from ground level looking
> straight down the street into deep perspective. Low prefab and rammed-earth
> buildings with corrugated awnings line both sides, a general store, a machine
> shop with a hoist out front, a water seller's tanks, a cantina with a dead
> holo-sign, their windows shuttered and their doors closed. Power lines, guy
> wires and strings of unlit lanterns cross the street overhead at every
> building, all leaning the same way in the wind, loose sheeting flapping on a
> roof and a hanging shop sign swinging. Parked along the edges are a dusty
> ground truck, a covered mech-scale cargo trailer and a row of water drums. The
> street itself is packed dirt scored with wheel ruts and a single dry drainage
> channel, dust already blowing along it in low streamers. At the far end of the
> street, filling the whole horizon and rising high into the sky, a towering wall
> of dust rolls toward the town, its leading edge boiling and lit amber by the low
> sun behind it, the last buildings at the end of the street already dissolving
> into it. A wind turbine and a comms mast stand against it on the right.
> Rendered in a detailed painterly illustration style with fine grain texture,
> clean linework and halftone dot shading worked into every shadow — under the
> awnings, inside the shuttered doorways, in the body of the dust wall — moody
> cinematic lighting throughout. Keep the palette restrained: greys, olive drab
> and rust on the buildings, vehicles and street, with a teal-green cast in the
> shadows under the awnings as the dominant cool tone and the warm amber of the
> sunlit dust as the only saturated warm note, rather than a broad rainbow of
> bright hues. Cinematic low sidelight comes through the dust and throws long
> hard-edged shadows across the street. Wide landscape composition, deep
> perspective, no people or figures anywhere in the frame, shuttered and waiting
> rather than mid-battle, grounded rather than glossy, painterly brushwork with
> heavy grain and dense halftone screentone worked into every shadow.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio. Bump to CFG ~2.0–2.5 and 10–12 steps
if the street loses its vanishing point.

## Agrarian Belt — Grain Terminal at Harvest Night

A grain terminal on an agricultural world at the end of harvest: silos, a
loading rail spur and fields of tall grain running to the horizon. Composed for
the grass-and-shafts-of-light bullet and the cloud bullet together, the
silos pushed to one side and the fields left open under a big moonlit sky.

> A wide, cinematic establishing shot of a grain terminal on an agricultural
> world at night under a full moon, viewed from ground level at the edge of a
> harvested field looking out across standing grain toward the terminal. A row
> of tall cylindrical silos stands on the left of the frame, joined by conveyor
> gantries and topped with blinking warning lights, a loading tower and a rail
> spur with a line of hopper cars beside them, a few work lamps glowing along the
> loading dock. On the right a huge idle harvesting machine sits at the field
> edge with its header raised, dust still hanging around it, beside a stack of
> grain sacks under tarpaulin and a leaning fence line with cables strung along
> it. Between them the field of tall grain opens out to the horizon, bending in
> long waves in the wind, cut through by a dirt track running to a distant
> homestead whose windows glow small and warm. Low cloud moves across the moon
> and throws slow moving shadows over the fields, and moonlight breaks through in
> shafts that sweep the grain. Moths and chaff drift in the work lamps. The sky
> is deep and clear between the clouds, thick with stars and the faint band of
> the galaxy. Rendered in a detailed painterly illustration style with fine grain
> texture, clean linework and halftone dot shading worked into every shadow —
> under the gantries, inside the harvester's frame, in the shadowed troughs of
> the grain — moody cinematic lighting throughout. Keep the palette restrained:
> greys, olive drab and rust on the silos, machinery and fence, with a
> teal-green cast in the moonlit grain and the cloud shadows as the dominant cool
> tone and the warm amber of the work lamps and the homestead windows as the only
> saturated warm notes, rather than a broad rainbow of bright hues. Cinematic
> moonlight rakes across the field and throws long soft-edged shadows from the
> silos. Wide landscape composition, deep perspective, no people or figures
> anywhere in the frame, the harvest done and the night quiet rather than
> mid-battle, grounded rather than glossy, painterly brushwork with heavy grain
> and dense halftone screentone worked into every shadow.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio.

## Landing Zone — Dropship on Final Approach

A marked landing zone on rough ground with a dropship coming down through the
haze. This is the dropship bullet made literal: the ship is small and far,
still descending, and the strobes and dust on the ground below it are what
the Wan pass will move. The LZ itself sits open in the centre.

> A wide, cinematic establishing shot of a hastily marked landing zone on
> broken open ground at dusk, viewed from low behind a raised earth berm looking
> across the zone toward the sky. The near edge of the frame is the top of the
> berm, sandbags and a coil of wire along it, a stack of supply crates and a
> folded stretcher frame at the left corner and a tripod signal lamp with a
> tangle of cabling at the right. Beyond the berm the landing zone is a wide
> circle of flattened scrub ringed with landing strobes on stakes, blinking in
> sequence, a scorched patch at its centre from earlier landings and dust
> already lifting off it in slow spirals. In the middle distance a heavy
> dropship descends toward the zone through drifting haze, still high, its
> blocky hull dark against the sky, landing gear extending and running lights
> flashing slowly along its spine, its engines throwing a faint heat glow down
> into the dust. Behind it the ground rises to a line of low hills scattered with
> scrub and a few dead trees, and beyond those the sky is banded dusk, deep
> teal-green fading up into night with the first stars showing, thin smoke from
> something over the hills drifting across it. A parked light utility vehicle
> and a marker panel sit on the far side of the zone. Rendered in a detailed
> painterly illustration style with fine grain texture, clean linework and
> halftone dot shading worked into every shadow — under the dropship's hull,
> along the berm, in the dust across the zone — moody cinematic lighting
> throughout. Keep the palette restrained: greys, olive drab and rust on the
> berm, crates, vehicle and hull, with the teal-green dusk sky as the dominant
> cool tone and the warm amber of the landing strobes and engine glow as the only
> saturated warm notes, rather than a broad rainbow of bright hues. Cinematic low
> backlight from the dusk sky silhouettes the dropship and rims the berm. Wide
> landscape composition, deep perspective, no people or figures anywhere in the
> frame, expectant and quiet rather than mid-battle, grounded rather than glossy,
> painterly brushwork with heavy grain and dense halftone screentone worked into
> every shadow.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio.

## Union Plaza — Administrative District After Hours

A Union administrative district at night, all clean stone, glass and public
holo-boards, empty after the offices close. The neon-and-steam bullet in a
Union register: pale teal information panels flickering instead of neon,
steam from the utility grates. The plaza floor is left empty in the middle.

> A wide, cinematic establishing shot of a broad civic plaza in a Union
> administrative district at night, viewed from ground level at one end of the
> plaza looking down its length. Tall clean-lined government buildings of pale
> stone and dark glass rise on both sides, their facades stepped back in
> terraces, long horizontal light strips glowing along each level and huge
> translucent public information boards mounted on their faces, scrolling pale
> teal-green text, slowly cycling emblems and flickering transit schedules. The
> plaza floor is polished stone laid in a wide geometric pattern, wet from
> earlier rain and holding reflections of the boards above, a line of slim
> lamp standards down each side, planters with clipped trees, empty benches and
> a dry ornamental water channel running down the centre toward a far
> monumental gateway with a slender spire rising behind it. Steam vents from
> utility grates along the edges and drifts across the stone, and a light haze
> softens the far end of the plaza. Above the buildings a few tall towers show
> against a deep night sky, aircraft lights crossing slowly between them and low
> cloud reflecting the city glow. A parked maintenance drone cart and a stack of
> barriers sit at the near right edge. Rendered in a detailed painterly
> illustration style with fine grain texture, clean linework and halftone dot
> shading worked into every shadow — under the terraces, beneath the trees, in
> the haze at the far end — moody cinematic lighting throughout. Keep the palette
> restrained: greys, olive drab and rust on the stone, planters and barriers,
> with the teal-green glow of the information boards and their reflections as
> the dominant cool tone and the warm amber of the lamp standards as the only
> saturated warm note, rather than a broad rainbow of bright hues. Cinematic
> lighting comes from the boards and the lamps, throwing long hard-edged
> shadows across the wet stone. Wide landscape composition, deep perspective, no
> people or figures anywhere in the frame, orderly and empty after hours rather
> than mid-battle, grounded rather than glossy, painterly brushwork with heavy
> grain and dense halftone screentone worked into every shadow.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio. Don't expect the board text to render
legibly at turbo settings.

## Derelict Hulk — Hangar Open to the Void

The main hangar of a dead ship, its outer doors torn away, open to space. The
stars-and-vessel bullet from inside a wreck: the void fills the middle of the
frame, the hangar wreckage frames it, and a few emergency lamps still pulse on
backup power. Debris drifts, the hull holds still.

> A wide, cinematic establishing shot of the interior of a derelict starship's
> main hangar bay, viewed from deep inside the bay looking out through the
> ruined outer doors into open space. The huge hangar doors have been torn away
> and hang in twisted plates at the left and right edges of the frame, their
> edges scorched and peeled back, exposing frame ribs and severed conduit.
> Inside, the bay is dark and wrecked, a mech-scale gantry crane collapsed
> against the left wall, empty launch cradles and fuel couplings along the right,
> a scatter of tools, crates and loose plating drifting weightless in the air
> where the deck grating has buckled, frozen coolant crystals glittering on
> every surface. A few emergency lamps still glow dull red on backup power along
> the bulkheads, pulsing slowly, and a single console screen flickers on the
> right with a dead status readout. Beyond the doors the void fills the centre of
> the frame, dense with hard stars and the faint band of a nebula, a large gas
> giant showing as a banded crescent low on the right, and a small distant vessel
> crossing far out with a steady pale engine glow. Cold light from the planet
> spills in across the deck. Rendered in a detailed painterly illustration style
> with fine grain texture, clean linework and halftone dot shading worked into
> every shadow — inside the collapsed crane, behind the cradles, in the deep of
> the bay — moody cinematic lighting throughout. Keep the palette restrained:
> greys, olive drab and rust on the hull structure, cradles and debris, with the
> cold pale planetlight and a teal-green cast in the frost as the dominant cool
> tones and the dull red of the emergency lamps as the only saturated warm note,
> rather than a broad rainbow of bright hues. Cinematic backlighting from the
> void rims every torn edge of the doors and throws long hard-edged shadows back
> into the bay toward the viewer. Wide landscape composition, deep perspective,
> no people or figures anywhere in the frame, dead and silent rather than
> mid-battle, grounded rather than glossy, painterly brushwork with heavy grain
> and dense halftone screentone worked into every shadow.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio.

## Refinery Fire — Seen From the Pipeline Road

A fuel refinery burning at night, watched from the service road along its
pipeline a kilometre off. The smoke-and-fires bullet at scale: multiple fires,
tall smoke columns, embers on the wind, the pipeline running down the frame's
edge and the middle ground left open.

> A wide, cinematic establishing shot of a burning fuel refinery at night,
> viewed from ground level on a raised service road running alongside a pipeline
> toward it. A heavy pipeline of several parallel pipes on concrete saddles runs
> from the near right corner away toward the refinery in deep perspective, a
> valve station and a leaning chain-link fence beside it. On the left the road is
> lined with a row of dark storage tanks, a pump house and a tipped-over tanker
> truck with its cab dark. In the middle distance the refinery sprawls across
> the horizon, a tangle of fractionating columns, flare stacks, catwalks and
> spherical tanks, and several of its structures are burning hard, tall columns
> of black smoke rising from them and leaning sideways in the wind, sheets of
> flame lighting the undersides of the smoke, embers streaming downwind across
> the sky. A ruptured tank burns lowest and brightest, and heat shimmer wavers
> the air above the whole complex. The open ground between the road and the
> refinery is bare scrub and drainage ditches, lit orange by the fire, and low
> haze hangs across it. Above, the smoke spreads into a heavy overcast that the
> fire lights from below. Rendered in a detailed painterly illustration style
> with fine grain texture, clean linework and halftone dot shading worked into
> every shadow — under the pipeline, inside the pump house, in the body of the
> smoke — moody cinematic lighting throughout. Keep the palette restrained:
> greys, olive drab and rust on the pipes, tanks and road, with a teal-green
> cast in the unlit shadows and the far haze as the dominant cool tone and the
> warm orange of the fires and embers as the only saturated warm note, rather
> than a broad rainbow of bright hues. Cinematic light comes entirely from the
> fires, throwing long hard-edged shadows back along the road toward the viewer.
> Wide landscape composition, deep perspective, no people or figures anywhere in
> the frame, watched from a distance rather than mid-battle, grounded rather than
> glossy, painterly brushwork with heavy grain and dense halftone screentone
> worked into every shadow.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio.
