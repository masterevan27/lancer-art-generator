# Themed fixture tables

Used by `test/test_theme_visibility.py` and `python -m test.theme_visibility`.
Not used by the generator at runtime.

`tables-minimal.md` is deliberately tiny - one or two bullets a table - which
makes it perfect for "does this roll at all" and useless for "how often does a
theme win", where every share collapses to 0 or 1. This file exists to be
*proportioned* instead: three themes of deliberately different weight against a
neutral floor, so a measured share is a real number.

The proportions mirror the live file's shape rather than its size. Per themed
table: roughly fifteen neutral bullets, five `@gundam`, three `@neosamurai`,
and a single `@scav` - the thin theme whose visibility is the whole reason
apply_theme_share() exists. A theme that reads as itself on one bullet is the
hard case; if the measurement can see that, it can see anything.

Both a `civ` and a `mil` Role are here on purpose. `filter_by_mil()` and
`apply_weapon_policy()` narrow a pool *after* the theme weighting is applied, so
the realized share diverges from THEME_SHARE by an amount that depends on how
tags correlate with the civ/mil split. A fixture with only civilians would hide
exactly the interaction worth measuring.

## Theme

- x3 gundam
- x2 neosamurai
- scav

## Given names

- Test

## Family names

- Subject

## Callsigns

- Fixture

## Pronouns

- she/her/her/woman
- he/him/his/man

## Age

- in {possessive} thirties

## Build

- lean and wiry

## Height

- of average height

## Skin

- pale skin

## Eyes

- grey eyes

## Demeanor

- a flat stare

## Glow colour

- teal-green

## Weather

- in steady rain
- || clear

## Stance

- standing squarely
- {possessive} hands in {possessive} pockets || hands

## Role

- a dockworker
- a Union marine soldier || mil

## Faction

- Unaligned || unaligned and freelance
- Dress uniform || in dress uniform || mil

## Hair

- a short {colour} crop
- a long loose {colour} braid
- {colour} hair shaved at one side
- a blunt {colour} fringe cut straight
- shoulder-length {colour} hair, unstyled
- a tight practical {colour} bun
- {colour} hair cropped close at the neck
- a side-parted {colour} sweep
- flat {colour} hair pushed back by a headset
- a low {colour} ponytail
- {colour} hair wind-tangled to one side
- a plain {colour} center part
- close-cropped {colour} hair with a faint scar line through it
- {colour} hair tucked behind both ears
- damp {colour} hair pushed off the forehead
- a pilot's flattened {colour} undercut, helmet-pressed at the crown || @gundam
- {colour} hair cropped to a sensor-jack line behind one ear || @gundam
- a short {colour} crop under a flight-cap ring || @gundam
- neat regulation-short {colour} hair, parted hard || @gundam
- a {colour} squadron buzz with a single dyed stripe || @gundam
- a high {colour} topknot bound in dark cord || @neosamurai
- long {colour} hair gathered into a lacquered clasp || @neosamurai
- a shaved crown with a single trailing {colour} tail || @neosamurai
- self-cut and uneven {colour} hair, hacked short with a blade || @scav

## Hair colour

Three segments, like `## Backdrop`: base, an optional tail appended after the
whole cut phrase, then flags. Tagged for all three themes because
`Hair colour` is in `THEMED_TABLES`, and every themed table here has to carry
content for each theme or the pool-share assertion has nothing to measure.

- black
- dark brown
- sandy blonde
- greying || || older
- salt-and-pepper || going white at the temples || older
- pale silver-white || fading to green at the tips || @gundam
- lacquer-black || shot through with a single red streak || @neosamurai
- bleached straw-blonde || dark at the roots || @scav

## Feature

- a scar across one cheek
- a chipped front tooth
- a faded burn along one forearm
- ink-stained fingertips
- a crooked, once-broken nose
- callused knuckles
- a pale scar through one eyebrow
- sun-cracked lips
- a birthmark below one eye
- deep-set squint lines
- a missing fingertip
- weather-reddened cheeks
- a thin scar under the jaw
- oil worked permanently into the cuticles
- a faint tremor in one hand
- a G-load flush still fading across the cheekbones || @gundam
- a neural port seated behind the ear, capped in white || @gundam
- calibration tattoos inked along one wrist || @gundam
- a duelling scar laid clean down one cheek || @neosamurai
- a clan mon burned small at the temple || @neosamurai
- teeth lacquered black at the edges || @neosamurai
- a crude self-stitched seam across the brow || @scav

## Outfit

- grey coveralls patched at both knees || civ
- a heavy canvas work jacket || civ
- a quilted vest over a thermal layer || civ
- oil-stained overalls tied at the waist || civ
- a plain shirt with the sleeves rolled || civ
- a hooded utility smock || civ
- layered work clothes, all of it worn thin || civ
- a fitted olive fatigue shirt || mil
- a plate carrier over drab fatigues || mil
- a stained field jacket, insignia stripped || mil
- webbing over a rolled-sleeve uniform || mil
- a service tunic buttoned to the throat || mil
- a padded liner suit worn alone || mil
- a duty jumpsuit, zipped low || mil
- a rain cape over working clothes || civ
- a white panelled pilot bodyglove, seams lit faint blue || @gundam mil
- a flight suit with squadron patches at the shoulder || @gundam mil
- a hardsuit chest rig over a mesh underlayer || @gundam mil
- a clean-panelled ground crew jacket || @gundam civ
- a pressure vest with rank tabs at the collar || @gundam mil
- a dark lacquered cuirass laced over a hakama || @neosamurai mil notac
- a layered indigo kimono, sleeves bound back for work || @neosamurai civ notac
- a haori worn open over segmented plate || @neosamurai mil notac
- mismatched scrap plate lashed on with cargo strap || @scav civ

## Headgear

- {Subject} {is_are} bare-headed.
- {Subject} {wear} a knitted watch cap pulled low.
- {Subject} {wear} a pair of scuffed goggles pushed up onto the forehead.
- {Subject} {wear} a flat cap, brim worn soft.
- {Subject} {wear} ear defenders slung around the neck.
- {Subject} {wear} a bandana tied back over the hair.
- {Subject} {wear} a hard hat, its lamp dark.
- {Subject} {wear} a dust mask hanging loose at the chin.
- {Subject} {wear} a beanie with a torn seam.
- {Subject} {wear} safety glasses smeared with grease.
- {Subject} {wear} a hood drawn up against the rain.
- {Subject} {wear} a sweat-stained headband.
- {Subject} {wear} a comms headset with one cup pushed off the ear.
- {Subject} {wear} nothing on {possessive} head, hair wind-flattened.
- {Subject} {wear} a folded cloth cap.
- {Subject} {wear} a white flight helmet with a raised smoked visor. || @gundam
- {Subject} {wear} a padded flight cap with the cable still jacked in. || @gundam
- {Subject} {wear} a sleek sensor-finned helmet, visor down. || @gundam
- {Subject} {wear} a light headset ring seated over a bodyglove collar. || @gundam
- {Subject} {wear} a slotted grid-visor helmet in clean white. || @gundam
- {Subject} {wear} a horned kabuto with a trailing neck guard. || @neosamurai
- {Subject} {wear} a wide lacquered hat rimmed in dull gold. || @neosamurai
- {Subject} {wear} a scowling mempo faceplate under a low brim. || @neosamurai
- {Subject} {wear} a cracked visor held on with tape and wire. || @scav

## Weapon

The two `@neosamurai` blades are deliberately not flagged `mil`: a traditional
blade is not military-issue, and on a Weapon `mil` is read by nothing but the
`notac` filter. All three `@neosamurai` Outfits carry `notac`, so the flag
filtered that theme's own armament away whenever it wore its own clothes -
realized share 0.265, against test_theme_visibility's 0.25 collapse floor.
Running `apply_weapon_policy()` ahead of `notac` lifted that to 0.578 on its
own; dropping the untrue flag takes it to 0.825. The blades keep `sidearm`,
which is the flag the mil-Role armed guarantee reads.

- x8 || none
- a service pistol worn openly at the thigh || mil weapon simple sidearm
- a holstered sidearm and a slung carbine || mil weapon sidearm
- a compact sidearm at the chest rig || mil weapon simple sidearm
- a marked ejection-seat sidearm holstered at the ribs || mil weapon simple sidearm @gundam
- a squadron-issue carbine held at a low ready in both hands || mil weapon sidearm hands gun @gundam
- a long single-edged blade worn edge-up at the waist || weapon sidearm @neosamurai
- a short companion blade at the small of the back || weapon simple sidearm @neosamurai
- a taped-together slug pistol shoved in the belt || mil weapon simple sidearm @scav

## Gear

- a battered data-slate || hands
- a coil of cable slung over one shoulder
- a heavy wrench hanging from a belt loop || hands
- a clipboard tucked under one arm || hands
- a canvas tool roll at the hip
- a multitool clipped to the belt
- a thermos held in both hands || hands
- a dented lunch tin
- a torch pushed into a pocket
- a spool of tape around one wrist
- a hand scanner on a lanyard
- a rolled tarp under one arm || hands
- a flight checklist board strapped to one thigh || @gundam
- a helmet carried under one arm, cable trailing || hands @gundam
- a launch-crew signal wand held low || hands @gundam
- a sealed avionics case at the hip || @gundam
- a wrapped bundle carried across both arms || hands @neosamurai

## Backdrop

- A half-body character portrait || Behind {object} is a plain riveted wall.
- A character portrait || {Subject} {is_are} standing in a cluttered workshop. || weather
- A half-body character portrait || {Subject} {is_are} on a wet loading dock. || weather
- A character portrait || Behind {object} a cargo lift stands open.
- A half-body character portrait || {Subject} {is_are} in a narrow service corridor.
- A character portrait || {Subject} {is_are} beside a stack of shipping crates. || weather
- A half-body character portrait || Behind {object} a window shows grey sky. || weather
- A character portrait || {Subject} {is_are} in a dim mess hall.
- A half-body character portrait || {Subject} {is_are} under a flickering strip light.
- A character portrait || {Subject} {is_are} at a rain-streaked gantry rail. || weather
- A half-body character portrait || Behind {object} pipework crosses the ceiling.
- A character portrait || {Subject} {is_are} in a stripped equipment bay.
- A half-body character portrait || {Subject} {is_are} beside an idling ground vehicle. || weather
- A character portrait || Behind {object} a stairwell drops into shadow.
- A half-body character portrait || {Subject} {is_are} in a bare briefing room.
- A character portrait || {Subject} {is_are} on a launch deck beneath a white panelled machine, its shoulder lit by floodlights. || weather @gundam
- A half-body character portrait || Behind {object} a raised cockpit canopy looms. || @gundam
- A character portrait || {Subject} {is_are} in a hangar of gantries and cable runs. || @gundam
- A half-body character portrait || {Subject} {is_are} at a pre-flight console, screens lit. || @gundam
- A character portrait || {Subject} {is_are} in a stone temple courtyard, rain off the eaves. || weather @neosamurai
- A half-body character portrait || Behind {object} a paper screen filters lamplight. || @neosamurai
- A character portrait || {Subject} {is_are} on a boarded walkway above a dark garden. || weather @neosamurai
- A half-body character portrait || {Subject} {is_are} in a shack of salvaged panels. || @scav
