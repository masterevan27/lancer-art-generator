# Scene & Spaceship Generator Tables

Roll tables for generators that don't exist yet — a mech generator and a
spaceship generator — plus any future use of environment shots behind an NPC.
Only **Background Animation** is read today, by
`animate-portrait.py --background --roll`; the rest is staged ahead of those
scripts the way `mech-catalogue-art-prompts.md` is staged ahead of authored
mech art.

Same convention as `npc-generator-tables.md`: every `## Heading` is a table,
every `-` bullet is one option, and a bullet may start `xN ` to weight it N
entries deep. See that file's own header for the full format (weights, `||`
flags, placeholders) if a future script here needs any of it — nothing below
uses it yet, because these tables have no subject to key placeholders off of.

**Backdrop** entries are deliberately subject-free — no `{object}` or
`{possessive}`, no "behind {object}" framing — so the same bullet can sit
behind a character portrait, a mech, or a ship without rewriting it. A
generator that needs the NPC table's tighter portrait-composition contract
(opening phrase paired with scene, weather gating, zero-g staging) should keep
using `Backdrop` in `npc-generator-tables.md` instead; this table is the
looser, general-purpose one.

**Background Animation** entries are Wan 2.2 motion prompts rather than
scene descriptions — what moves in a finished background still, not what is
in it. See that table's own comment for the rules an added bullet has to
keep, and `docs/animate-portrait.md` for the script that rolls them.

**Spaceships** entries describe one vessel each — hull shape, markings,
lighting — the way `Outfit` or `Gear` describe one item, so a future generator
can roll one and drop it into its own prompt template.

---

## Backdrop

- A dusty frontier trading town at street level — domed sandstone and ochre
  buildings crowd both sides of a wide sand-packed street, thick bundles of
  cable strung pole to pole overhead, a hooded figure and a small hovering
  delivery droid further down the street, heat-hazed light and drifting dust.
- An elevated view over the same kind of frontier settlement — a wide central
  plaza ringed by domed roofs and a broad wood-slatted awning structure,
  antennas and cable runs crossing between buildings, the town's skyline
  receding into pale haze at the edges.
- A ruined megacity street — hollowed-out skyscrapers torn open above street
  level, thick haze hanging between them, a heap of rubble and twisted rebar
  in the foreground with the shattered head of some huge machine half-buried
  in it, a flat hazy sun low between the towers.
- A rain-slicked city street at night — a dense crowd under umbrellas, masked
  faces lit by wet neon signage, a vast industrial structure venting smoke
  and steam looming over the street from above, small transports drifting
  past overhead.
- A vehicle scrapyard under a hazy alien sky — stacked wrecked hovercars and
  hulls several deep on both sides of a narrow cleared path, spindly
  floodlit gantries rising among them, a lone suited figure walking the path
  alone, a huge planet or moon hanging low over a distant city skyline.
- A night skyline with a fogbank rolling in — a dense wall of cloud sweeping
  low over blocky towers and lit structures, a handful of small craft
  crossing beneath it, scattered warm lights glowing faintly through the
  haze at ground level.
- A vast dark hangar or storage bay, its scale lost in shadow — several huge
  derelict ship hulls half-buried and thickly overgrown with moss, hard
  shafts of light beaming down from openings far overhead, a few small
  figures rappelling down a hull or picking through the wreckage below with
  handheld lamps.
- A night settlement wedged in a narrow canyon — sheer rock walls rising on
  both sides, small craft threading low between them on repulsor glow, cool
  blue floodlights and a scatter of lit windows picking out structures built
  into the canyon base.
- An elevated monorail or transit bridge on massive stilted supports,
  vanishing into thick fog with only its running lights visible past a
  certain distance, a few small figures on foot approaching along the open
  ground beneath it.
- A flooded wreck site at dusk — a downed starfighter lies half-submerged in
  murky standing water, a gun turret from the same wreck breaking the
  surface nearby, a small domed astromech droid standing motionless at the
  waterline, flat overcast light with no shadow.
- A bright interior hangar bay, a gunship raised on service jacks with its
  rear engine nacelle pulled and sparking work underway beneath an overhead
  gantry crane, yellow-suited ground crew working around it and a
  stencilled bay number on the wall.
- A dim landing-bay corridor lined with idle mining haulage drones and
  stacked cargo crates, hazard striping underfoot and signage pointing
  toward the bay beyond, a couple of armed figures crossing in the middle
  distance.
- The hold of a bulk freighter, rows of huge cylindrical cargo tanks racked
  to either side and stencilled with a hauling company's markings, a single
  figure walking small beneath them through shafts of light falling from
  overhead vents.
- The open flight deck of an orbital carrier at night, rows of fighters
  parked under floodlight and more coming in to land, ground crew moving
  between them and a scatter of escort ships crossing the dark beyond the
  deck edge.
- A dim hangar at night, a long shuttle resting with its ramp down and
  cables trailing from its nose, a caped, helmeted figure standing watch as
  ground crew work nearby.
- A snowbound industrial dockyard at night, floodlights picking out cable
  runs and gantries, a gunship settling in on glowing belly thrusters as
  armed figures take up position on the catwalks above.
- The gutted dome of a ruined library, shelving torn open and sunlight
  spilling through a collapsed section of roof, the heavy shape of a
  scavenged walker mech picking through the wreckage as robed figures move
  among the stacks below.
- A misty old-growth forest, a massive armored beast fitted with a heavy
  mechanical harness led on foot by a small armed party, moss-hung branches
  closing overhead.
- A colossal cargo hauler grounded in open desert beneath a huge ringed
  planet, intake nacelles towering over a scatter of ground equipment, a
  lone armed figure keeping watch as a fighter streaks past low overhead.
- A mountaintop landing platform strung with cable lifts, a hulking
  transport resting with its prow over the edge, snow-capped peaks falling
  away below and a second craft crossing the sky beyond.

## Spaceships

- A sleek matte-black and silver twin-boom gunship, forward-swept wings and a
  cluster of docking pylons framing the cockpit nose, glowing blue thrusters
  throwing hard rim light along the hull, small amber running lights along
  the wing edges.
- A dark angular interceptor landing on twin repulsor thrusters over a wet
  platform between towers, long swept wingtip stabilizers trailing back past
  the fuselage, a scatter of small position lights along the underside.
- A boxy white-and-orange autonomous cargo hauler in corporate delivery
  livery, a blunt rounded nose and a row of articulated docking or grapple
  arms slung beneath it, flanked by smaller courier drones in matching
  livery at a loading dock.
- A compact red-and-white liveried racer or shuttle, twin underslung engine
  pods, a glassed-in gold-tinted cockpit canopy, bold roundel markings
  across the flank.
- A sleek dark ship banking low and hard between towering city skyscrapers
  at dusk, a glowing blue engine cluster throwing light back across the
  building faces as it turns.
- A boxy, heavily weathered heavy-lift dropship in olive-and-white cargo
  livery, twin ramps lowered to the ground, landed in open scrubland with a
  small hazmat-suited ground crew working at the base of the ramp.
- A weathered teal-and-yellow twin-boom light gunship inverted mid-bank
  over a city skyline, twin underslung gun pods and a chin-mounted cannon,
  black hazard stencilling and a large sponsor logo along the tail booms.
- A scarred grey twin-nacelle VTOL, two bulbous glazed cockpit pods slung
  beneath swept-back wings and a pair of chin-mounted cannons, a
  red-and-white hazard chevron and a stencilled hull number low on the
  fuselage.
- A sleek deep-blue-and-white VIP shuttle with long swept delta wings and a
  low central spine canopy, a stylised crest on the wing root and a
  stencilled serial along the wingtip, parked gleaming on an open pad.
- A vast grey orbital freighter, three flattened disc-shaped pods mounted
  in a row along its spine, docking arms and solar-panel wings splayed from
  the hull, running lights picking it out against the planet's curve below.
- A dark diamond-hulled gunship settling into a floodlit dock at night,
  twin belly thrusters glowing amber beneath it, antennae bristling from
  the upper hull and its running lights flashing slowly against falling snow.
- A hulking grey angular transport perched on a mountaintop landing
  platform, its blunt prow overhanging the edge, cable-strung support
  towers rising alongside and a second ship crossing the sky beyond.
- A massive boxy grey dropship looming low over a rooftop landing zone,
  engine nacelles glowing at its flanks and a smaller stub-winged gunship
  escort hovering just beneath it.
- A dark angular VTOL banking hard above cloud cover, swept wings and a
  slab-sided fuselage, a distant ring-shaped station and a second vessel
  visible far beyond it in high orbit.
- A white twin-boom aerospace fighter skimming low over jungle wetlands,
  underslung engine pods trailing thin exhaust and wingtip stencilling
  naming its serial, startled birds scattering in its wake.
- A colossal dark obelisk-shaped dropship descending into a rocky valley
  at night, its blunt hull lit only by a cold blue glow from the underside
  thrusters, faint running lights tracing lines up the fuselage.
- A colossal grey-and-rust cargo hauler resting in open desert, a cluster
  of huge intake nacelles at its stern and layered armor plating along its
  flanks, a small escort fighter streaking past low overhead.
- A heavily armored grey capital ship exchanging beam fire with a
  scattered enemy formation in orbit, its hull bristling with turrets and
  sensor masts, fighters weaving through the crossfire around it.
- A long flat-decked carrier holding formation in orbit, rows of parked
  fighters lining an open flight deck and more peeling off to land as
  smaller support ships pass close overhead.
- A weathered grey carrier-frigate marked with a stencilled tentacled
  emblem and hull code, its flight deck lit for night operations as
  fighters queue to land and larger haulers cruise past in the distance.
- A sleek matte-black gunship raised on service jacks in a bright interior
  hangar, its rear engine nacelle pulled and sparking beneath an overhead
  gantry crane, yellow-suited ground crew working around it.

## Background Animation

<!-- Positive prompts for `animate-portrait.py --background` (Wan 2.2
     image-to-video), one per bullet. The scene-side twin of the `##
     Animation` table in npc-generator-tables.md, and it lives here rather
     than there because scene motion is not an NPC trait.

     Written to animate a landscape without changing what the landscape is.
     Wan moves what the prompt names, so every bullet spends its motion on
     weather, light, machinery and sky - smoke, cloud, rain, snow, embers,
     neon, holographic readouts, searchlights, a ship crossing the distance -
     and none of them names a subject. That last part is load-bearing: a
     background has nobody in it, and a clause about a character is an
     invitation for Wan to draw one into an empty frame. Buildings, terrain
     and hardware are named only to say they hold still, because the failure
     mode of an animated establishing shot is geometry that crawls.

     The closing clause pins the camera, for the reason the `## Animation`
     table gives. Keep it on anything you add, and keep each bullet to one
     line - the parser reads the first line of a bullet and nothing else. -->

- smoke drifts slowly across the scene and thin dust hangs in the air. distant fires flicker along the horizon. the buildings and terrain hold still. the camera is locked off and does not move.
- low cloud slides across the sky and long shadows creep slowly over the ground. loose cables and hanging wires sway in the wind. the camera is locked off and does not move.
- rain falls steadily and runs off every hard edge in the frame. puddles ripple and the reflected lights shiver in them. the camera is locked off and does not move.
- neon signage flickers and pulses through heavy haze. steam vents from grates and drifts slowly upward. the camera is locked off and does not move.
- snow falls gently and settles over the wreckage. wind lifts loose powder off the ground in slow curls. the camera is locked off and does not move.
- embers rise from burning debris and drift out of frame. heat shimmer distorts the air above the fires. the camera is locked off and does not move.
- a dropship descends slowly through the haze in the far distance, its running lights flashing slowly. dust stirs on the ground far below it. the camera is locked off and does not move.
- stars drift almost imperceptibly beyond the viewport. a distant vessel crosses the void, engine glow pulsing steadily. the camera is locked off and does not move.
- holographic readouts scroll and flicker across the console screens. indicator lights pulse in sequence along the bulkhead. the camera is locked off and does not move.
- searchlights sweep slowly across the compound and across the low cloud above it. dust drifts through the beams. the camera is locked off and does not move.
- silent tracer fire and muzzle flashes flicker along a distant ridgeline. columns of smoke lean slowly in the wind. the camera is locked off and does not move.
- tall grass and hanging vines stir in a slow breeze. shafts of light shift as cloud passes overhead. the camera is locked off and does not move.
