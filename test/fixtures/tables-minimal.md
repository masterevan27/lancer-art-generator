# Minimal fixture tables

Used by the test suite. Not used by the generator at runtime.

## Theme
- x2 alpha
- beta

## Given names
- Test

## Family names
- Subject

## Callsigns
- Fixture

## Pronouns
- she/her/her/woman
- they/them/their/person

## Age
- in {possessive} thirties
- in {possessive} late teens || young

## Build
- lean and wiry
- full-figured through the hips || figure

## Height
- of average height

## Skin
- pale skin

## Hair
- a short {colour} crop
- a long {colour} braid || @alpha
- a shaved head, {colour} at the stubble || @beta

## Hair colour
- black
- greying || || older
- silver-white || fading to green at the tips || @alpha

## Eyes
- grey eyes

## Feature
- a scar across one cheek
- a line of chrome ports along one temple || @beta

## Demeanor
- a flat stare

## Role
- a dockworker
- a Union marine soldier || mil

## Faction
- unaligned and freelance
- in dress uniform || mil

## Outfit
- grey coveralls
- lacquered plate || @alpha
- a neon techwear jacket || @beta
- an elaborate floral kimono || civ notac

## Headgear
- {Subject} {is_are} bare-headed.
- {Subject} {wear} a wide woven hat. || @alpha

## Weapon

One armament bullet here is deliberately compound - it contains " and " of
its own, the way 25 of the 56 live ones do - so that `carry_sentence()`'s
comma join is reachable from a plain roll. Without it every rolled carry
sentence has exactly two halves, and the "A and B and C" run-on that join
exists to prevent cannot be produced at all.

- x2 || none
- a service pistol worn openly at the thigh || mil weapon simple sidearm
- a holstered sidearm and a slung carbine || mil weapon sidearm
- a long blade worn edge-up at the waist || mil weapon sidearm hands gun @alpha

## Gear
- a battered data-slate || hands
- a canvas tool roll at the hip
- a hard-shelled tactical backpack || mil

## Glow colour
- teal-green

## Backdrop
- A half-body character portrait || Behind {object} is a plain wall.
- A character portrait || {Subject} {is_are} in a temple courtyard. || weather @alpha
- A character portrait || {Subject} {is_are} firing a sidearm down a corridor. || nogear

## Weather
- in steady rain
- || clear

## Stance
- standing squarely
- {possessive} hands in {possessive} pockets || hands
- {possessive} weapon raised and sighted down the barrel || gun
