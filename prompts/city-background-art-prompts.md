# City Background Art Prompts (Krea 2 Turbo, ComfyUI)

Animated chat backgrounds of modern and near-future cities at night, for
SillyTavern. **These are deliberately outside the campaign's house style.**
Every other prompt file here asks for the campaign's linework, halftone screentone
and the restrained grey/olive/rust palette; these ask for photographic realism
instead, and each prompt says so explicitly at the end so the render cannot
drift back toward illustration. Nothing about them is Lancer, and they are not
meant to sit in the same visual family as the mechs, tokens or battlemaps.

Nothing in the render pipeline enforces the house look — there is no style LoRA
in `Lancer_Scene_Workflow_v1.json`, only a detail slider — so the same workflow
renders these correctly with no flag changes. The style lives entirely in the
prompt text.

They follow the same three composition rules the animated Lancer backgrounds
do, because those are about the job rather than the style: nobody in the frame,
the middle of the composition left quiet for a chat panel to sit over, and the
moving elements chosen up front so the Wan pass has something to move that the
picture already contains.

## Render and animate

Two commands, the same pair as the Lancer scene backgrounds — the still is a
Krea 2 job, the animation is a Wan job:

    python generate-art.py --prompts prompts/city-background-art-prompts.md --filter <slug> --width 1920 --height 1080 --output-prefix CityBackgrounds --download-to <folder>

    python animate-portrait.py "<folder>\<the rendered png>" --background --no-pingpong -d "<the motion line under the prompt>"

`--roll` is not used here. Its `## Background Animation` table is written for
Lancer scenes — smoke, embers, dropships — so each section below carries its own
motion line instead, naming only what that particular frame contains. Pass it
with `-d`.

`--no-pingpong` plays the loop forward once rather than forward and back. It
costs roughly twice the render for the same playing length, and it is the right
choice for every scene here: rain falls, cloud drifts and traffic runs in one
direction, and a reversed second half gives all three away.

## Riverside Skyline — Across the Water

The classic wide skyline shot, seen low across a river from the opposite bank.
The towers stack up on the right and the far bank runs off to the left, leaving
the middle of the frame as open water and sky. Motion comes from the water, the
cloud and the aircraft warning beacons.

> A wide, cinematic photograph of a modern city skyline at night seen from the
> far bank of a broad river, camera at water level looking across. A dense cluster
> of glass and steel skyscrapers fills the right two thirds of the frame, rising at
> staggered heights, thousands of individual office windows lit in warm white and
> pale gold behind the glass, some floors dark, the curtain walls reflecting the
> lights of their neighbours. Slender red aircraft warning beacons sit at the top
> of the three tallest towers. Toward the left the skyline steps down into lower
> mid-rise blocks, a lit suspension bridge crossing out of frame, and beyond it the
> shoreline falls away into distant haze. The near bank is a low concrete
> embankment running across the bottom of the frame, wet, with mooring bollards and
> a handrail. The river itself takes up the whole middle of the composition, black
> and faintly rippled, carrying long soft vertical reflections of the entire
> skyline stretched down toward the camera. Above the towers the sky is deep
> blue-black with a band of low cloud lit orange from beneath by the city's own
> light pollution. Photorealistic, shot on a full-frame camera with a wide lens,
> long exposure, high dynamic range, deep depth of field, crisp architectural
> detail, natural colour, subtle lens bloom around the brightest lights. No people,
> no boats and no figures anywhere in the frame. Not an illustration, no linework,
> no halftone, no cel shading, no painterly brushwork.

**Motion:** `the water ripples slowly and the skyline reflections shiver and stretch in it. low cloud drifts across the sky above the towers. the red aircraft beacons blink slowly and scattered office windows flicker. the buildings and the embankment hold still. the camera is locked off and does not move.`

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio.

## Downtown From Above — Near-Future Grid

A high vantage looking down and across a dense downtown core, close enough to
read the streets as canyons of light. Slightly ahead of the present: a few
tapering supertalls, some illuminated facade banding, aerial traffic lanes
marked by running lights. The street grid runs through the middle of the frame
and stays dark, so the panel has somewhere to sit.

> A wide, cinematic photograph of a near-future downtown core at night, taken from
> high on a neighbouring tower looking down and out across the city. Dense
> skyscrapers crowd both sides of the frame in deep perspective, a mix of
> present-day glass curtain-wall towers and a few taller tapering supertalls with
> illuminated horizontal banding running up their edges and soft light spilling
> from their setbacks. Between them the street grid cuts through the middle of the
> composition as narrow dark canyons, threaded with the continuous white and red
> streaks of traffic and the small cool pools of streetlights, receding toward a
> hazy vanishing point. Rooftops in the foreground carry mechanical plant, vents,
> water tanks, satellite dishes and helipad markings, wet from earlier rain. Thin
> strings of small navigation lights mark elevated aerial corridors running between
> the towers at two different heights. Beyond the core the city flattens into an
> endless low carpet of orange sodium light stretching to the horizon, and above it
> the sky is heavy overcast, the cloud base underlit a dull amber by the whole city
> at once. Photorealistic, shot on a full-frame camera, long exposure so the
> traffic reads as light trails, high dynamic range, crisp architectural detail,
> natural colour, faint atmospheric haze with distance. No people and no figures
> anywhere in the frame. Not an illustration, no linework, no halftone, no cel
> shading, no painterly brushwork.

**Motion:** `traffic light trails run steadily along the streets far below and the aerial corridor lights drift slowly between the towers. low cloud slides across the sky and the underlit cloud base shifts. scattered office windows flicker and rooftop beacons blink. the buildings and rooftops hold still. the camera is locked off and does not move.`

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio.

**Do not raise CFG on these.** The other prompt files suggest bumping to ~2.5
when a layout drifts; on a photorealistic night city it does not drift, it
disintegrates — CFG 2.5 at 12 steps returned a frame of coloured noise with the
composition still faintly visible underneath, and CFG 1.0 at the default steps
returned a clean image from the same prompt. The `detail_slider` LoRA in
`Lancer_Scene_Workflow_v1.json` runs at strength 2, which is already a lot of
push for a turbo model. Fix a bad frame by rewording the prompt or re-rolling
the seed, not by turning up guidance.

## Observation Deck — Glass and City

An interior looking out: an empty observation floor near the top of a tower,
floor-to-ceiling glass, the city spread out below and beyond it. The deck
structure frames the edges and the glass fills the middle, so the composition
is quiet exactly where it needs to be, and the reflections in the glass give the
animation a second layer to work with.

> A wide, cinematic photograph of an empty observation deck near the top of a
> skyscraper at night, viewed from inside looking out through a continuous wall of
> floor-to-ceiling glass. Slim dark mullions divide the glazing at regular
> intervals and heavier structural columns frame the left and right edges of the
> frame. The polished stone floor runs out toward the glass, catching soft
> reflections, with a low brushed-metal handrail set back from it, a couple of
> empty benches and a dark unlit information plinth pushed to the sides. A recessed
> cove in the ceiling throws a dim warm wash back across the soffit, the only light
> source inside the room. Beyond the glass the whole city lies spread out far
> below: a dense field of lit towers immediately in front, their tops at or below
> eye level, the grid of streets between them glowing, and past those an endless
> carpet of city light reaching to a hazy horizon under a deep blue-black sky. The
> dim interior is faintly mirrored in the glass, ceiling cove and floor sheen laid
> over the view. Photorealistic, shot on a full-frame camera with a wide lens, long
> exposure, high dynamic range, crisp detail in both the interior and the view,
> natural colour, subtle bloom around the brightest city lights. No people and no
> figures anywhere in the frame, and no reflection of a person in the glass. Not an
> illustration, no linework, no halftone, no cel shading, no painterly brushwork.

**Motion:** `the city lights far below twinkle and scattered windows flicker in the towers. thin cloud drifts slowly past beyond the glass and distant aircraft lights cross the sky. the faint interior reflections in the glass shift very slightly. the deck, the glass and the buildings hold still. the camera is locked off and does not move.`

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio. If the interior collapses and the
frame becomes a plain skyline, re-roll the seed rather than raising CFG — see
the warning under **Downtown From Above**. The deck furniture and the
reflections in the glass are the first things turbo drops.

## Rain on the Avenue — Street Level

Ground level on a wide downtown avenue in heavy rain, glass towers going up out
of frame on both sides. The wet road running away down the centre is the quiet
middle, and it is also where most of the motion lives: rain, running water and
shivering reflections.

> A wide, cinematic photograph of a wide downtown avenue late at night in heavy
> rain, long after dark, camera at street level in the middle of the road looking
> straight down it into deep perspective. The sky is black night sky, no daylight
> anywhere in the frame. Modern glass and steel towers rise out of frame on both
> sides, mostly dark with scattered lit office floors, ground-level retail
> frontages glowing behind wet plate glass, illuminated signage and awnings
> projecting over the pavement. Traffic signals, streetlights on tall slim poles,
> and a row of parked cars line both kerbs, all beaded with water. The avenue
> itself runs empty away from the camera, black asphalt sheeted with standing
> water, lane markings and a crosswalk in the foreground, the whole surface holding
> long broken reflections of the signage and the towers above. Rain falls hard and
> straight through every light, sheeting off awnings, ledges and signal housings,
> and a manhole in the near middle distance vents a slow column of steam. Far down
> the avenue the buildings dissolve into rain haze and glow, and above them a narrow
> strip of black overcast night sky is underlit a dull orange by the city's own
> light. Everything in the frame is lit only by artificial light — streetlights,
> signage, shopfronts and traffic signals — against deep darkness. Photorealistic,
> shot on a full-frame camera with a wide lens, long exposure, high dynamic range,
> crisp detail, natural colour, visible rain streaks and strong specular highlights
> on every wet surface. Deep night, nighttime, dark. No people and no figures
> anywhere in the frame, and no moving vehicles. Not an illustration, no linework,
> no halftone, no cel shading, no painterly brushwork. Not daytime, not dawn, not
> dusk, not an overcast grey daylight scene.

**Motion:** `rain falls steadily and sheets off every awning, ledge and sign in the frame. standing water on the road ripples and the reflected lights shiver and break in it. steam drifts slowly up from the manhole and the signage flickers. the buildings, the parked cars and the street hold still. the camera is locked off and does not move.`

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate at
1920×1080 or another 16:9 landscape ratio.
