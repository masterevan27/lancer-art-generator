# Minimal ship fixture tables

Used by the test suite. Not used by the generator at runtime. The NPC-side
equivalent is `tables-minimal.md`; read that one first if this is your first
time here.

Every REQUIRED_TABLES heading is present. The four equipment tables each
carry a `none` marker (except `## Command bridge`, see below), a neutral pool,
and at least one bullet at each size band they are allowed to reach. Every one
of the five THEMED_TABLES carries exactly one `@salvage` bullet, and `## Theme`
carries `salvage` itself alongside a second theme so filter_by_theme() has
something to discriminate. Every table but `## Theme` carries one bullet using
a `{is_are}` placeholder, to prove the substitution pass reaches tables the
live file has never exercised it on - `{is_are}` rather than `{ship}` or
`{size}` on purpose, since those two are resolved from '## Ship type' and
'## Size' themselves and a bullet in either of those tables naming the other
would race the single-pass substitution loop in roll_ship().

Two deliberate departures from the "every equipment table alike" reading:

  `## Command bridge` carries no `none` bullet. ship_policy.py's own
  ALWAYS_FITTED_TABLES says a bridge is silhouette, not fitted equipment, and
  every hull has one - adding an empty bullet "to satisfy the four-table rule"
  is the live table's own note (:1763) for exactly what not to do here.

  `## Launch catapult` carries no neutral (unflagged) bullets, and its two
  fitted bullets sit at `min-large`/`min-huge` rather than one per band.
  ship_policy.py's NEUTRAL_POOL_EXEMPT and the live table's own comment
  (:1633-1650) say a catapult is a deck with nowhere to sit below a large
  hull; a `min-small` catapult bullet here would make a large battleship's
  LIGHT_CAP reachable-nothing test (see test_ship_policy.py) unreproducible
  and would contradict the very design this fixture is meant to exercise.

Every bullet is one physical line, flags included - see task-3-brief.md's
warning about `parse_tables()`'s bullet regex and continuation lines.

## Name prefixes

- x3 || none
- ISV
- Free Trader
- a provisional line that {is_are} rarely stencilled twice

## Ship names

- Windward Star
- Cold Coffee
- Not My Problem
- a name that {is_are} older than the hull

## Theme

- salvage
- corporate

## Ship type

- a fleet carrier, built around a full-length flight deck || carrier large huge mil
- a battleship, a line-of-battle hull built to trade fire || battleship large huge mil
- a cruiser, the fleet's general-purpose heavy hull, a class that {is_are} rarely retired || cruiser medium large huge mil
- a destroyer, a fast escort hull || destroyer small medium mil
- a patrol boat, a short-endurance picket || patrol small mil
- a stealth ship, a signature-suppressed hull || stealth small medium mil
- a reconnaissance ship, sensors over armament || recon small medium mil
- a smuggler's ship, an honest hull with concealed holds || smuggler small medium civ
- a cargo ship, a bulk hauler || cargo medium large huge civ
- a support ship, a tender for larger hulls || support medium large civ

## Size

- about forty metres bow to stern, a two-crew hull || small hex1
- a hundred and sixty metres bow to stern, four crew hatches along the flank || medium hex2
- four hundred metres bow to stern, lifeboat pods ranked in twos, a scale that {is_are} rare outside a fleet action || large hex3
- two and a half kilometres bow to stern, lifeboat pods ranked in dozens || huge hex5

## Faction

- Unaligned || || civ unaffiliated
- Free Traders' Guild || a hand-lettered registry number down the flank || civ
- Union Fleet || a formation stripe that {is_are} standard across the line || mil

## Hull

- a compact working hull with modest fittings || destroyer patrol stealth recon smuggler small
- a mid-sized hull with a broad service deck, plating that {is_are} scuffed at every seam || destroyer cruiser stealth recon smuggler cargo support medium
- a large hull with a broad silhouette and a stepped spine || carrier battleship cruiser cargo support large
- a colossal hull dwarfing everything nearby || carrier battleship cruiser cargo huge
- a corroded scavenger-hulk hull patched from stolen plate || cargo huge @salvage

## Detail

- a sensor mast standing off the spine
- an antenna cluster bolted to the hull shoulder || mil
- a cargo boom folded flat against the flank || civ
- a lacquered pennant mast, one that {is_are} rarely seen outside a fleet review || @salvage

## Weapon

- || none min-small
- a point-defence turret bolted flush to the plating
- a chin-mounted repeater with an exposed ammo feed
- a pintle-mounted autocannon on a simple cradle || civ
- a rack of stub torpedo tubes let into the hull, mounts that {is_are} standard issue || min-small mil
- a twin-barrel turret mounted amidships || min-medium mil
- a broadside gun deck with tiered casemate ports || min-large mil
- a spinal mass driver running the ship's length || min-huge mil
- a lacquered cannon on a lacquered mount, an enamelled crest cast into the cheek plate || min-medium mil @salvage

## Shield generator

- || none min-small
- overlapping scales of ablative plating, scorched and pitted
- a dormant emitter ring around the hull's waist
- a scatter of small projector nodes along the hull edges || civ
- a squat civilian shield housing clamped to the plating, one that {is_are} common on working hulls || min-small civ
- a belt of armoured emitter blisters down each flank || min-medium
- a heavy shield envelope crackling at the hull line || min-large mil
- a full energy-shield envelope shrouding the hull in slow light || min-huge mil

## Launch catapult

- || none min-small
- a single linear catapult rail set into the dorsal deck, a fitting that {is_are} rare outside a carrier || min-large mil
- a bank of vertical drop tubes through the belly armour || min-huge mil

## Command bridge

- a flush armoured blister barely raised above the plating, one that {is_are} common on working hulls || min-small
- a low canopy set into the hull's back || min-small
- a squat armoured cockpit block at the prow || min-small
- a wraparound bridge gallery ringing the forward hull || min-medium civ
- a multi-deck bridge castle stacked amidships || min-large
- a cathedral spire crowning the ship's back || min-huge
- a hand-patched pilothouse welded onto the spine, plating salvaged from elsewhere || min-small civ @salvage

## Markings

- faded stencil numbers along the flank
- hazard chevrons around the main hatch || mil
- a bay assignment number chalked beside the loading hatch || civ
- a registry code, lettering that {is_are} scoured half illegible

## Condition

- straight out of the yard, the paint still even
- a working finish, dulled and scuffed at the edges
- long in service, rust blooms creeping from every seam
- a hull that {is_are} held together by patch plate and tension cable

## Backdrop

- A wide three-quarter view || Empty deep space, a hard starfield beyond the hull. || vacuum
- A close side-on view || A replenishment run alongside a fleet tender, a boom locked across the gap. || dock vacuum hull
- A low dramatic angle || A descent through cloud, strobing beacons marking a path that {is_are} rarely flown at night. || weather atmosphere planetlight
- A backlit wide view || A nebula's inner edge, curtains of gas lit from within. || weather @salvage
- A tight raking view || A dense debris field, torn plating tumbling past in the foreground. || weather vacuum debris
- A tight low angle || An engagement under way, point-defence fire stitching the dark nearby. || combat vacuum hull

## Weather

- x2 hard vacuum, nothing between the hull and the stars || clear
- thin nebula haze drifting past the plating
- fine dust scouring the leading edges, grit that {is_are} hard to clean from the seams

## Glow colour

- cold blue-white
- amber
- a shade that {is_are} chosen to match the hull's own trim

## Glow placement

- runs along the flank picking out panel seams
- gathers at the muzzles of the guns as they charge || armed
- stands off the plating in a thin skin across the shield envelope || shielded
- lines the deck edges and floods the bay mouth || deck
- washes across a neighbouring hull nearby || hull
- picks out the command windows, a detail that {is_are} visible from far off
