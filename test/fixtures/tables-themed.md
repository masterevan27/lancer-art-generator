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
`apply_gear_policy()` narrow a pool *after* the theme weighting is applied, so
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

## Accent

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

- unaligned and freelance
- in dress uniform || mil

## Hair

- a short crop
- a long loose braid
- hair shaved at one side
- a blunt fringe cut straight
- shoulder-length and unstyled
- a tight practical bun
- cropped close at the neck
- a side-parted sweep
- flat hair pushed back by a headset
- a low ponytail
- wind-tangled to one side
- a plain center part
- close-cropped with a faint scar line through it
- hair tucked behind both ears
- damp hair pushed off the forehead
- a pilot's flattened undercut, helmet-pressed at the crown || @gundam
- hair cropped to a sensor-jack line behind one ear || @gundam
- a short crop under a flight-cap ring || @gundam
- neat regulation-short hair, parted hard || @gundam
- a squadron buzz with a single dyed stripe || @gundam
- a high topknot bound in dark cord || @neosamurai
- long hair gathered into a lacquered clasp || @neosamurai
- a shaved crown with a single trailing tail || @neosamurai
- self-cut and uneven, hacked short with a blade || @scav

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

- x8 || none
- a service pistol worn openly at the thigh || mil weapon simple sidearm
- a holstered sidearm and a slung carbine || mil weapon sidearm
- a compact sidearm at the chest rig || mil weapon simple sidearm
- a marked ejection-seat sidearm holstered at the ribs || mil weapon simple sidearm @gundam
- a squadron-issue carbine held at a low ready in both hands || mil weapon sidearm hands gun @gundam
- a long single-edged blade worn edge-up at the waist || mil weapon sidearm @neosamurai
- a short companion blade at the small of the back || mil weapon simple sidearm @neosamurai
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
