# Dynamic Background Generator Tables

Each `##` heading is an independently editable pool. Every shipped pool has at
least 20 distinct substantive choices. Comment out a bullet to disable it; prefix
it with `xN` for a positive integer weight. Context flags are `[outdoor]`,
`[indoor]`, `[space]`, or a comma-separated combination. Unflagged entries work
in every context. `[weather=rain]` and similar flags link Weather and Motion.
Flags and weights remain in saved traits but are removed from image prompts.
Empty selected traits omit that feature. No groups or implicit duplicate entries.
Space means a vacuum exterior; sealed station rooms belong to indoor.
Vegetation, Interior life and the people pools are controlled by the scene-life settings.
They remain available to lock and reroll even when omitted from the prompt.
Population, Clothing and equipment, and Activity may use `[population=civilian]`,
`[population=military]`, `[population=mixed]`, or comma-separated combinations.
Tagged choices must share a population category; untagged choices suit any group.
Locks on clothing or activity also constrain the population roll. Adult age mix
and Appearance variety describe a group, with individual differences inside it.

The expanded settings draw on the Backdrop scenes and groups, Weather, and Glow
tables in `npc-generator-tables.md`, plus the subject-free Backdrop scenes in
`scene-and-spaceship-tables.md`. They extract places, light, routes and props into
independent choices, without portrait framing, character placeholders or NPC flags.

## Outdoor location
- [outdoor] a forward operating base of hardened shelters linked by duckboard paths and earth-filled blast walls
- [outdoor] a mech proving ground with reinforced observation bunkers and scarred target berms
- [outdoor] a carrier landing apron cut into a mountainside, with recessed fueling points and blast deflectors
- [outdoor] an evacuated city intersection converted into a fortified logistics checkpoint
- [outdoor] a field hospital compound of pressure tents around a sheltered casualty transfer lane
- [outdoor] a siege-battered transit station with an improvised defensive perimeter around the surviving platforms
- [outdoor] a jungle listening post with raised equipment huts and a narrow reinforced landing pad
- [outdoor] a coastal artillery redoubt with armored observation slits and salt-stained access ramps
- [outdoor] a dusty frontier trading town with domed ochre buildings and overhead utility cables
- [outdoor] a scrapyard of stacked transport hulls divided by floodlit salvage lanes
- [outdoor] a flooded wreck recovery site with a half-submerged dropship and a stable shore staging area
- [outdoor] a canyon settlement beneath transit bridges and tightly packed service balconies
- [outdoor] a frontier dropship landing yard with blast berms and recessed service pits
- [outdoor] a terraced mountain relay station above a deep communications gorge
- [outdoor] a flooded industrial district where loading bridges connect warehouse roofs
- [outdoor] a colonial market street beneath elevated freight tracks
- [outdoor] a canyon checkpoint with a narrow bridge and switchback approaches
- [outdoor] a coastal launch complex with seawalls and reinforced launch pads
- [outdoor] an abandoned agricultural arcology surrounded by irrigation channels
- [outdoor] a geothermal drilling camp across mineral-stained rock shelves
- [outdoor] a ruined transit interchange with collapsed flyovers and intact access ramps
- [outdoor] a solar collection field arranged around a maintenance control tower
- [outdoor] a fortified perimeter yard with offset gates and ammunition bunkers
- [outdoor] a highland reservoir dam with spillways and turbine access roads
- [outdoor] an excavation site exposing a buried precolonial machine complex
- [outdoor] a container port with crane rails and multiple freight aisles
- [outdoor] a forest research outpost connected by raised boardwalks
- [outdoor] a quarry settlement built into stepped stone benches
- [outdoor] a decommissioned reactor compound with shielded cooling trenches
- [outdoor] a dense residential courtyard between modular habitation towers
- [outdoor] an alien basalt basin crossed by mineral-processing pipelines
- [outdoor] a border rail depot with parallel sidings and armored signal huts

## Indoor location
- [indoor] a buried command bunker with recessed tactical displays and thick segmented blast doors
- [indoor] a mech maintenance hangar with gantries, chain hoists and separated repair cradles
- [indoor] a carrier ready room with flight gear lockers and compact briefing stations
- [indoor] an armored troop transport hold with folded restraint seats and secured equipment racks
- [indoor] a garrison mess hall with long practical tables and a closed serving counter
- [indoor] a field surgical module with screened treatment bays and sealed supply cabinets
- [indoor] a military communications room with shielded consoles and redundant cable trunks
- [indoor] a fortified armory with closed weapons cages and an inspection counter
- [indoor] a dropship cockpit with recessed instrument readouts and reinforced forward glazing
- [indoor] a cramped repair shop with parts racks reaching the ceiling and a clear central workbench
- [indoor] a station transit corridor lined with exposed conduit and worn hazard stripes
- [indoor] a dim salvage hangar containing immobilized derelict hulls beneath heavy support trusses
- [indoor] a dropship maintenance hangar with gantry access and recessed repair bays
- [indoor] a station command room with tiered consoles and a central projection well
- [indoor] a colonial clinic with partitioned treatment rooms and sterile supply alcoves
- [indoor] a reactor service hall with shielded conduits and inspection galleries
- [indoor] a freight sorting warehouse with conveyors and marked loading zones
- [indoor] a public transit concourse with ticket gates and branching platforms
- [indoor] a hydroponics laboratory with parallel cultivation racks and irrigation tanks
- [indoor] a military briefing room with a tactical display and stepped seating
- [indoor] a residential common kitchen adjoining a narrow communal dining area
- [indoor] a shipboard engine control compartment around a suspended drive housing
- [indoor] an abandoned data vault with cold storage cabinets and security vestibules
- [indoor] a merchant workshop with tool benches and unfinished machine assemblies
- [indoor] a customs inspection chamber with cargo scanners and enclosed search bays
- [indoor] an orbital hotel lobby with a reception island and recessed lounges
- [indoor] a water recycling plant with filter banks and grated maintenance routes
- [indoor] a bunker ammunition magazine divided by heavy blast partitions
- [indoor] a university fabrication studio with printers and material preparation tables
- [indoor] a salvage auction hall with display plinths and a sealed delivery gate
- [indoor] a station chapel with acoustic panels and an abstract memorial wall
- [indoor] an emergency shelter with modular sleeping berths and supply lockers

## Space location
- [space] the exterior flight deck of an orbital carrier with docking clamps and armored service recesses
- [space] a military repair dock surrounding the damaged flank of a moored capital ship
- [space] a fortified customs platform with external inspection cradles and redundant sensor masts
- [space] a naval listening array built from widely separated shielded receiver booms
- [space] a fleet ammunition transfer station with isolated armored storage pods
- [space] a damaged orbital defense ring with sealed bulkhead ends and tethered repair frames
- [space] the exterior hull of a troop carrier beside recessed boarding locks and equipment rails
- [space] a remote picket station with armored observation housings and folded docking arms
- [space] an orbital drydock surrounding an incomplete capital ship hull
- [space] a fractured asteroid refinery linked by exposed ore transfer spines
- [space] a communications satellite cluster arranged around a central relay bus
- [space] a derelict colony transport with ruptured cargo sections and detached modules
- [space] an outer station maintenance deck with docking clamps and service trusses
- [space] a fuel depot of spherical tanks protected by segmented debris shields
- [space] an evacuated lunar landing apron with pressure shelters and rover tracks
- [space] a navigation beacon mounted on an irregular captured asteroid
- [space] a solar power satellite with articulated panel wings and converter towers
- [space] an orbital elevator counterweight with cable anchors and docking collars
- [space] a ring habitat exterior with radiators and radial access spokes
- [space] a remote telescope array on disconnected instrument platforms
- [space] an ice mining station anchored inside a comet fissure
- [space] a shipbreaking platform with cut hull plates secured to storage racks
- [space] a defensive orbital bastion with recessed launch cells and armored lobes
- [space] a deep space cargo exchange built around a rotating transfer carousel
- [space] a vacuum foundry whose crucible housings sit on skeletal support frames
- [space] a crater observatory with sunken antenna dishes and buried conduits
- [space] a wreckage recovery site with tethered fragments and a salvage cradle
- [space] a jump navigation installation with nested field coils and anchor pylons

## Architecture
- [outdoor,indoor] layered bunker concrete with recessed armored shutters and sacrificial outer panels
- modular military shelter sections joined by standardized sealed couplings and protected service channels
- thick naval bulkheads with dogged access doors and rounded pressure-bearing corners
- [outdoor,indoor] prefabricated revetment walls braced by gabions and inset maintenance niches
- ribbed carrier-deck construction with flush latching panels and heavily reinforced load points
- [outdoor,indoor] domed frontier masonry joined to salvaged steel lintels and bundled cable conduits
- massive cast-concrete structural ribs with inset metal access panels
- modular ceramic cladding held in exposed precision-machined frames
- utilitarian corrugated steel surfaces patched with riveted repair plates
- smooth white composite shells interrupted by dark maintenance seams
- layered armored bulkheads with beveled corners and recessed fasteners
- weathered bronze alloy housings with green oxidation in sheltered joints
- carbon-black lattice supports around pale load-bearing panels
- translucent reinforced polymer partitions backed by visible structural struts
- angular industrial forms with broad diagonal braces and bolted junctions
- rounded pressure-rated modules joined by accordion expansion collars
- brushed titanium surfaces with ceramic thermal protection strips
- salvaged mismatched hull plates welded onto an older structural skeleton
- pale stone-composite blocks interleaved with narrow metallic expansion joints
- dark basalt aggregate panels reinforced by orange-painted steel beams
- repeating hexagonal structural cells with deep recessed connection points
- smooth streamlined housings contrasted with exposed ribbed utility runs
- thick prefabricated slabs supported by slender triangulated braces
- oxidized iron surfaces polished bright around frequently serviced fittings
- layered sacrificial shielding with offset plates and visible stand-off mounts
- charcoal synthetic timber cladding over a practical aluminum frame

## Palette
- warm ivory and faded olive with restrained rust-orange accents
- slate blue and pale concrete gray with amber warning markings
- charcoal and muted crimson with small bone-white identification panels
- desaturated teal and brushed silver with dark navy recesses
- sand beige and dark umber with worn turquoise trim
- cool lavender gray and gunmetal with pale yellow utility markings
- chalk white and soot black with a few signal-red structural details
- moss green and clay brown with dull brass fittings
- faded burgundy and warm gray with cream-colored panel edges
- deep indigo and dusty peach with muted copper joints
- neutral concrete gray with subdued cobalt blue service panels
- pale celadon and graphite with restrained maroon highlights
- ochre and dark steel with thin oxidized green seams
- dusty rose and warm ivory with tarnished silver supports
- petroleum blue and blackened bronze with subdued orange fixtures
- cool mint and slate with narrow white alignment markings
- smoke gray and faded plum with small ochre maintenance details
- pale limestone and deep forest green with dull nickel hardware
- muted terracotta and charcoal with cream-colored structural bands
- washed denim blue and dark brown with soft gray ceramic surfaces

## Lighting
- [outdoor] [time=night] narrow shielded perimeter floodlights leaving the distant approaches dark
- [outdoor] [time=twilight] pale dusk over the structures with red readiness lamps at access points
- [outdoor] [time=day] hard midday light broken into bands by overhead gantries and blast screens
- [outdoor] [time=night] cool blue gantry lamps and warm loading lights reflecting off metal fittings
- [indoor] red low-level readiness lighting beneath dim neutral ceiling strips
- [indoor] pale tactical display glow edged by warm console task lamps
- [indoor] bright surgical task lighting confined to work surfaces, with softer surrounding illumination
- [indoor] heavy overhead trusses casting broad shadow bands between white maintenance lamps
- [indoor] cool instrument readouts reflected in worn cockpit glazing and dark control housings
- [space] hard rim sunlight on armored edges with tiny recessed docking lights in deep shadow
- [outdoor] [time=day] low angled sunlight casting long parallel shadows through the structures
- [outdoor] [time=day] pale diffuse daylight that keeps surface textures evenly readable
- [outdoor] [time=day] amber sunlight grazing upper edges and leaving cool recesses
- [outdoor] [time=twilight] blue twilight with warm practical lamps defining entrances
- [outdoor] [time=night] moonlit darkness interrupted by shielded amber perimeter lamps
- [outdoor] [time=day] diffuse daylight illuminating broad exposed working surfaces
- [outdoor] [time=day] reflected sunlight creating soft secondary shadow directions
- [outdoor] shielded service lamps emphasizing the entrances and equipment bays
- [outdoor] rows of practical amber fixtures tracing the important circulation routes
- [indoor] recessed ceiling strips alternating with pools of warm task lighting
- [indoor] broad frosted ceiling panels providing shadow-softened white illumination
- [indoor] low amber emergency lamps tracing doors and floor-level routes
- [indoor] cool equipment indicators reflecting from dark structural surfaces
- [indoor] angled inspection lamps highlighting machinery and maintenance clearances
- [indoor] warm pendant fixtures creating distinct islands of illumination
- [indoor] dim violet instrument light balanced by neutral overhead service lamps
- [space] hard white sunlight producing crisp shadows on exposed hardware
- [space] reflected planetary blue light filling the shadowed sides of structures
- [space] warm sunlight catching hull edges against a deep black vacuum
- [space] red dwarf illumination bathing exposed surfaces in muted copper light
- [space] cold navigation lamps outlining otherwise unlit structural edges
- [space] bright maintenance floodlights revealing tool scars and panel joints
- [space] a narrow solar rim illuminating raised structures above dark recesses

## Layout
- [outdoor,indoor] a staggered checkpoint route with offset barriers and a broad inspection pocket
- a central service lane flanked by recessed equipment bays and protected side routes
- [outdoor,indoor] a layered defensive arrangement with successive thresholds and sheltered fallback passages
- [outdoor,indoor] a branching trench-like circulation plan linking recessed work areas and protected junctions
- paired observation positions overlooking a central approach, connected by a rear service route
- [outdoor,indoor] an open assembly area with supply storage on one side and clear evacuation routes on the other
- a narrow central spine opening into larger transverse staging bays
- [outdoor,indoor] parallel treatment or rest bays divided by partitions, with an uninterrupted supply aisle
- [outdoor,indoor] a compact courtyard surrounded by linked sheltered galleries and two offset entrances
- [space] several docking fingers extending from a reinforced central spine with separate maintenance rails
- a broad central route with narrower parallel service paths and staggered cover
- two connected zones separated by a substantial structural choke point
- a ring circulation route around a densely detailed central installation
- diagonal circulation crossing the frame between offset entrances
- three distinct terraces connected by broad ramps and maintenance stairs
- an asymmetric arrangement with a large assembly balanced by smaller utility structures
- a branching junction whose routes remain visually distinct and navigable
- parallel structural rows broken by occasional transverse access lanes
- a central working platform surrounded by recessed machinery and safe crossings
- staggered islands of equipment that form multiple connected circulation loops
- a narrow approach opening into a larger operational area with several exits
- a long axial route interrupted by offset baffles and side alcoves
- a perimeter service route around clustered central equipment
- two major masses linked by a bridge with alternative lower access
- an irregular layout shaped around a preexisting structural obstruction
- a sequence of interlocking rectangular zones with clear connecting thresholds
- a radial arrangement of service arms around a compact distribution hub
- broad open working surfaces punctuated by low cover and exposed conduits
- a stepped arrangement of equipment bays with a continuous access spine
- multiple small operating areas connected through a larger shared loading zone

## Weather
- [outdoor] [weather=rain] driving rain blowing diagonally across exposed approaches and pooling in wheel ruts
- [outdoor] [weather=rain] a passing storm leaving fresh runoff cascading from reinforced roof edges
- [outdoor] [weather=snow] wind-driven snow collecting against blast walls and half-burying unused tracks
- [outdoor] [weather=snow] wet sleet crusting railings and softening the outlines of distant gantries
- [outdoor] [weather=dust] an ochre dust front reducing distant structures to layered silhouettes
- [outdoor] [weather=dust] intermittent grit-laden gusts sweeping broad cleared landing surfaces
- [outdoor] [weather=fog] sea mist rolling over the approaches and diffusing distant practical lights
- [outdoor] [weather=fog] a cold fogbank hanging low between ruined building shells
- [outdoor] [weather=wind] strong crosswinds tugging at secured camouflage fabric and loose straps
- [outdoor] [weather=dry] oppressive dry heat producing a shallow shimmer over exposed hardstanding
- [outdoor] [weather=dry] dry still air with crisp distant visibility
- [outdoor] [weather=dry] dry cool air under scattered high cloud
- [outdoor] [weather=dry] warm dry air with a faint distant heat shimmer
- [outdoor] [weather=rain] steady fine rain darkening exposed surfaces
- [outdoor] [weather=rain] heavy rain feeding runoff channels and shallow puddles
- [outdoor] [weather=rain] intermittent showers leaving fresh beads on metalwork
- [outdoor] [weather=snow] slow snowfall accumulating on ledges and sheltered corners
- [outdoor] [weather=snow] dense falling snow softening distant silhouettes
- [outdoor] [weather=snow] fine crystalline flurries gathering along cold structural seams
- [outdoor] [weather=wind] a persistent crosswind pressing loose fittings and hanging fabric
- [outdoor] [weather=wind] strong irregular gusts passing through exposed structural gaps
- [outdoor] [weather=wind] a gentle breeze stirring hanging cables and small pennants
- [outdoor] [weather=fog] low ground fog collecting in recessed service routes
- [outdoor] [weather=fog] dense cool mist obscuring the most distant structures
- [outdoor] [weather=fog] thin ribbons of fog curling around large structural bases
- [outdoor] [weather=dust] fine windblown dust accumulating along downwind edges
- [outdoor] [weather=dust] a broad suspended dust haze reducing distant contrast
- [outdoor] [weather=dust] short gusts of grit sweeping exposed paved surfaces
- [outdoor] [weather=rain] cold drizzle gathering into rivulets beneath panel joints
- [outdoor] [weather=dry] dry overcast conditions with unusually sharp near-field detail

## Details
- [outdoor,indoor] sealed ammunition transit cases strapped into a protected storage recess
- [outdoor,indoor] folded camouflage screens bundled beside portable sensor tripods
- [outdoor,indoor] wheeled casualty stretchers secured beside a closed medical supply cabinet
- [outdoor,indoor] portable armored partitions with visible impact wear around their lower edges
- [outdoor,indoor] ration containers and rolled bedding stowed in orderly recessed racks
- [outdoor,indoor] rugged field radios connected to neatly tied cable runs and backup battery cases
- [indoor] flight helmets in individual cubbies beside folded restraint harnesses
- [indoor] a tactical planning table with inset abstract illuminated shapes and no readable text
- [space] closed armored boarding hatches flanked by tether rails and recessed readiness lamps
- [space] external rescue pods held in mechanical release cradles along a protected hull recess
- [outdoor] low concrete vehicle barriers arranged around a maintenance access hatch
- [outdoor] empty cargo dollies parked beside sealed freight pallets
- [outdoor] worn direction markings and repaired seams in the paving
- [outdoor] armored drainage grates beside raised utility connection boxes
- [outdoor] stacked modular blast shields waiting beside a service entrance
- [outdoor] coiled industrial hoses and closed inspection covers near a loading bay
- [outdoor] recessed bollards protecting a cluster of power distribution cabinets
- [indoor] closed tool drawers and labeled storage bins beneath a work surface
- [indoor] overhead cable trays turning around structural columns
- [indoor] folded safety barriers stored beside an unobstructed doorway
- [indoor] sealed utility cabinets with inset analog pressure gauges
- [indoor] scuffed floor tiles repaired with mismatched replacement panels
- [indoor] a wheeled maintenance cart carrying neatly secured instrument cases
- [indoor] wall-mounted breathing equipment in sealed emergency lockers
- [space] tether attachment points and recessed handholds along exposed surfaces
- [space] folded manipulator arms secured beside a maintenance socket
- [space] micrometeorite scars and layered patch plates across older hull sections
- [space] insulated coolant pipes protected by segmented thermal covers
- [space] bolted-down cargo frames holding sealed transport containers
- [space] clusters of reaction-control nozzles around reinforced support junctions
- [space] stowed cable reels and latching tool mounts on an external service panel

## Motion
- [outdoor] [weather=rain] rain falls continuously and beads slide down the already wet metal surfaces
- [outdoor] [weather=rain] rainwater ripples in the puddles and trickles through the visible runoff channels
- [outdoor] [weather=snow] snowflakes drift slowly and settle along the existing snow-covered ledges
- [outdoor] [weather=snow] fine flurries pass across the frame while the accumulated snow remains still
- [outdoor] [weather=wind] the loose cable ends sway gently in the wind
- [outdoor] [weather=wind] the small hanging pennants flex with intermittent gusts
- [outdoor] [weather=fog] the low fog drifts slowly between structural bases
- [outdoor] [weather=fog] thin mist curls through the existing recessed service routes
- [outdoor] [weather=dust] fine dust drifts along the ground and around the downwind edges
- [outdoor] [weather=dust] faint curtains of suspended dust move across the distant structures
- [outdoor] a visible ventilation fan turns slowly inside its protective grille
- [outdoor] the amber perimeter warning lamps pulse at a slow regular interval
- [indoor] the equipment status lamps blink slowly in repeating patterns
- [indoor] a small ventilation rotor turns steadily behind its protective grille
- [indoor] the visible analog gauge needles make tiny controlled movements
- [indoor] the suspended insulated cable loops sway almost imperceptibly
- [indoor] a scanner light travels slowly across the visible inspection tray
- [indoor] faint display light cycles across the existing equipment monitors
- [indoor] a small circulation pump indicator rotates behind its transparent cover
- [space] the visible docking beacons flash in a slow repeating sequence
- [space] a hinged antenna dish makes a tiny deliberate tracking adjustment
- [space] the secured inspection arm rotates slowly at its exposed joint
- [space] faint sunlight shifts across a slowly turning external instrument gimbal
- [space] a small exposed radiator tracking mechanism pivots by a few degrees
- [space] the existing external maintenance lamps pulse gently without any atmospheric glow
- [space] a tethered sensor package makes a slow restrained rotation in the vacuum

## Foreground
- [outdoor] a chipped blast barrier with rain-dark seams and gravel gathered at its base
- [outdoor] a recessed trench entrance edged by sand-filled modular retaining blocks
- [outdoor,indoor] a secured stack of rugged field equipment cases beside a clear passing lane
- [indoor] a folded stretcher and sealed trauma kit resting within a marked storage bay
- [indoor] the edge of a reinforced briefing console with inset status lights
- [space] a closed armored service hatch surrounded by handholds and scuffed tether sockets
- [outdoor] a waist-high equipment enclosure with a hinged service lid
- [outdoor] a pair of staggered concrete traffic blocks beside the approach
- [outdoor] a recessed maintenance trench crossed by a removable steel plate
- [outdoor] an empty loading platform edged by battered impact rails
- [outdoor] a bank of ground-level electrical junction boxes
- [outdoor] an exposed pipeline bend protected by short barrier posts
- [outdoor] stacked sealed supply cases anchored to a freight skid
- [indoor] the corner of a bolted-down workbench with built-in storage
- [indoor] a freestanding instrument cabinet with a recessed control face
- [indoor] a low partition with inset utility sockets
- [indoor] a recessed floor access panel beside a structural pillar
- [indoor] a parked equipment trolley with locked wheel brakes
- [indoor] a modular seating block beside a clear circulation route
- [indoor] a heavy door frame with visible locking hardware
- [space] a raised docking guide rail with replaceable contact pads
- [space] a bolted instrument housing protected by a thermal shroud
- [space] a recessed tether anchor surrounded by scuffed hull plating
- [space] a folded external maintenance ladder beside a sealed hatch
- [space] a cluster of armored cable couplings on the nearest structural frame
- [space] a cargo restraint bracket with a coiled capture tether

## Distant features
- [outdoor] the silhouettes of parked mechs beneath far-off maintenance gantries
- [outdoor] a line of fortified watch positions following the ridge beyond the site
- [outdoor] a ruined transit viaduct fading between hollowed-out towers
- [outdoor] distant carrier superstructures rising above layered docks and cranes
- [space] a formation of distant patrol ships reduced to small hull silhouettes against the starfield
- [space] the segmented arc of an orbital defense ring beyond the nearest structures
- [outdoor] low industrial towers forming a broken skyline beyond the site
- [outdoor] an elevated rail viaduct crossing the far edge of the district
- [outdoor] a stepped ridge carrying a line of communications masts
- [outdoor] a cluster of cylindrical storage silos beyond the perimeter
- [outdoor] an unfinished habitation tower surrounded by skeletal crane booms
- [outdoor] a long retaining wall marking the boundary of a higher district
- [outdoor] the arched supports of a distant freight terminal
- [indoor] a far doorway revealing a second enclosed service chamber
- [indoor] an upper gallery with an enclosed observation booth
- [indoor] a receding sequence of structural bays with utility cabinets
- [indoor] a far wall of sealed equipment racks behind a safety partition
- [indoor] a wide pressure door beneath an overhead gantry
- [indoor] a windowed control booth overlooking the far working area
- [indoor] a raised mechanical platform reached by two access stairs
- [space] a detached docking module connected by a narrow structural spine
- [space] an extended radiator array beyond the main operating surface
- [space] a cluster of fuel spheres at the far end of a service truss
- [space] the armored silhouette of an adjacent uncrewed station module
- [space] an array of long antenna booms beyond the perimeter rail
- [space] a distant tether anchor built into a separate rock outcrop

## Terrain or floor
- [outdoor] deeply rutted hardstanding reinforced with interlocking expeditionary ground panels
- [outdoor] packed earth crossed by shallow drainage cuts and battered duckboards
- [outdoor] broken concrete with embedded rebar ends covered by safe temporary bridging plates
- [indoor] scuffed carrier deck plating with recessed tie-down sockets and broad non-slip strips
- [indoor] easy-clean sealed floor panels with narrow drainage channels around work bays
- [space] ribbed hull walkway plates with magnetic foothold strips and captive fasteners
- [outdoor] cracked reinforced paving with broad expansion joints
- [outdoor] compacted gravel divided by embedded service conduits
- [outdoor] stepped basalt shelves joined by prefabricated access ramps
- [outdoor] pale packed regolith stabilized beneath modular ground mats
- [outdoor] heavy interlocking concrete tiles with repaired subsidence
- [outdoor] rust-stained bedrock interrupted by inset industrial platforms
- [outdoor] hard clay ground crossed by raised metal walkways
- [indoor] dark non-slip composite tiles with inset utility channels
- [indoor] grated steel flooring above an enclosed cable void
- [indoor] polished terrazzo broken by practical metal access covers
- [indoor] worn poured resin flooring with visible repair patches
- [indoor] modular raised floor panels edged with anti-slip strips
- [indoor] heavy rubberized flooring around exposed machinery bases
- [indoor] pale ceramic tiles divided by broad structural expansion seams
- [space] ribbed hull plating with recessed attachment sockets
- [space] cratered bare rock reinforced by anchored metal access mats
- [space] interlocking armored deck plates with thermal expansion gaps
- [space] sintered regolith slabs forming a level vacuum work surface
- [space] open lattice platforms with bolted solid operating pads
- [space] segmented ceramic shields inset between reinforced hull ribs

## Sky
- [outdoor] a broad pale sky above the structural silhouette
- [outdoor] a narrow band of sky between high industrial structures
- [outdoor] a large ringed moon faintly visible above the horizon
- [outdoor] a distant orbital elevator cable rising beyond the view
- [outdoor] a pale companion planet suspended far above the site
- [outdoor] a high arc of faint orbital debris far beyond the atmosphere
- [outdoor] a broad atmospheric gradient above a distant ridge
- [outdoor] thin high cloud streaks near the upper edge of the sky
- [outdoor] a distant broken moon with a subtle dust ring
- [outdoor] a faint chain of artificial orbital lights high overhead
- [space] a broad star field beyond the exposed installation
- [space] the curved limb of a blue terrestrial planet beyond the structure
- [space] the banded surface of a gas giant filling part of the distant void
- [space] a thin planetary ring crossing the distant black background
- [space] a cratered airless moon beyond the external platforms
- [space] a sparse star field interrupted by a distant red sun
- [space] a pale ice giant with narrow rings in the far background
- [space] the small bright disc of a remote companion star
- [space] a dense distant galactic star band beyond the local vacuum
- [space] the shadowed hemisphere of a nearby rocky planet

## Time
- [outdoor] [time=day] early morning as the daily work cycle begins
- [outdoor] [time=day] midmorning during a quiet interval between scheduled deliveries
- [outdoor] [time=day] local midday after the main cargo transfer window
- [outdoor] [time=day] early afternoon during a routine maintenance pause
- [outdoor] [time=day] late afternoon before the perimeter systems change shifts
- [outdoor] [time=twilight] predawn twilight before the first scheduled operations
- [outdoor] [time=twilight] evening twilight just after the work cycle ends
- [outdoor] [time=night] early night during the automatic security cycle
- [outdoor] [time=night] local midnight between service inspections
- [outdoor] [time=night] the final dark hour before morning operations
- [indoor] the start of the station's scheduled day cycle
- [indoor] a midday break between normal operating shifts
- [indoor] the evening turnover after equipment shutdown
- [indoor] the station's quiet overnight maintenance interval
- [indoor] the first operational hour after a planned systems restart
- [indoor] a scheduled inspection window with all work surfaces cleared
- [space] the beginning of a scheduled autonomous servicing cycle
- [space] a pause between orbital cargo transfer windows
- [space] the final calibration phase before the next docking operation
- [space] an extended unattended interval between maintenance visits

## Faction presence
- Union civil infrastructure with standardized public-service equipment
- Harrison Armory logistical presence expressed through robust armored fittings
- Smith-Shimano Corpro engineering expressed through elegant integrated instrument housings
- IPS-Northstar freight operations expressed through rugged cargo-handling machinery
- HORUS-adjacent technical occupation expressed through irregular experimental equipment assemblies
- a local planetary militia using repurposed civilian equipment and improvised protection
- an independent salvage cooperative with neatly sorted recovered components
- a colonial municipal works department with practical public maintenance fixtures
- a university research expedition with modular instrument cases and temporary labs
- a private security contractor with portable scanners and removable barriers
- a frontier medical relief organization with sealed aid supply containers
- a mining workers' collective with shared heavy tools and repaired utility machinery
- a shipping guild using standardized freight restraints and transfer equipment
- a local agricultural consortium with irrigation and crop-monitoring hardware
- a Union survey team with geodetic instruments and standardized field modules
- a mercenary maintenance detachment with portable repair rigs and armored supply boxes
- a civilian evacuation authority with organized emergency storage and access equipment
- a station residents' association maintaining patched communal infrastructure
- a remote observatory consortium with delicate instrument enclosures and calibration rigs
- a recently abandoned corporate concession with obsolete branded shapes but no readable logos

## Condition
- recently mobilized readiness with freshly secured stores and equipment prepared for deployment
- veteran military upkeep with worn finishes, carefully repaired fittings and orderly service access
- [outdoor,indoor] a recently evacuated position with neatly closed equipment cases and empty workstations
- [outdoor,indoor] a reclaimed defensive site with cleared routes through older impact damage
- post-mission recovery with temporary repair braces and protected inspection points
- newly commissioned infrastructure with clean seals, unused sockets and pristine replacement panels
- recently commissioned surfaces with clean joints and only light tool marks
- well-maintained older infrastructure with polished wear around frequent access points
- heavy daily use visible in scratched paint and neatly repaired fittings
- temporary shutdown with protective covers secured over sensitive equipment
- long-term abandonment with dull finishes and detached nonessential panels
- recent mechanical damage isolated behind portable safety barriers
- extensive field repairs using mismatched plates and exposed reinforcing brackets
- incomplete construction with secured unfinished junctions and staged materials
- meticulous restoration preserving older structural forms beneath new protective coatings
- partial decommissioning with empty mounting points and sealed disconnected conduits
- resource-constrained maintenance with repeated patches and carefully reused fasteners
- a recent inspection with removable access covers neatly set beside their openings
- superficial blast scoring across durable surfaces without destroying the main layout
- uneven aging where newer modules meet much older load-bearing structures
- protective wrapping still attached to a few recently installed replacement components
- routine cleaning in progress with tools stowed and surfaces partly polished
- structural reinforcement added around overloaded junctions and support points
- an emergency repair state with portable braces stabilizing a damaged assembly
- redundant systems removed, leaving clearly sealed mounting sockets and service ports
- ceremonial refurbishment with repainted panels over otherwise practical working infrastructure

## Atmosphere
- restrained military readiness conveyed by orderly stores and protected lines of movement
- the disciplined quiet of a watch change, with practical light concentrated at duty stations
- tense anticipation suggested by closed protective shutters and prepared staging areas
- exhausted post-deployment calm with workspaces reset for maintenance and rest
- a temporary expeditionary foothold, practical and well organized despite limited infrastructure
- the solemn stillness of an evacuated outpost with its essential systems left running
- quiet operational readiness conveyed by orderly equipment and clear access routes
- tense isolation conveyed by sealed thresholds and uncompromising structural forms
- patient abandonment conveyed by idle machinery and interrupted maintenance work
- cautious optimism conveyed by new repairs and carefully organized shared resources
- institutional precision conveyed by repeated modules and disciplined spatial organization
- improvised resilience conveyed by practical adaptations and carefully reused materials
- monumental scale conveyed by massive supports dwarfing ordinary utility fittings
- intimate practicality conveyed by closely arranged work areas and accessible controls
- restrained unease conveyed by closed access points and asymmetrical sight lines
- calm technical focus conveyed by delicate instruments inside protective housings
- austere military discipline conveyed by robust barriers and ordered equipment bays
- civic generosity conveyed by wide accessible routes and durable public fixtures
- industrial fatigue conveyed by layered repairs and heavily worn working surfaces
- exploratory anticipation conveyed by unfamiliar instruments and temporary installation frames
- solemn remembrance conveyed by maintained empty spaces and abstract memorial forms
- methodical recovery conveyed by sorted salvage and stabilized damaged structures
- economic decline conveyed by unused capacity and partially dismantled equipment
- frontier self-sufficiency conveyed by multipurpose installations and visible repair capability
- remote scientific detachment conveyed by specialized apparatus and minimal comforts
- durable everyday normality conveyed by modest service equipment and unremarkable practical repairs

## Vegetation
- [outdoor] wild grasses and fern patches beneath large native trees, with medium and small shrubs along the edges
- [outdoor] broad-canopied old trees shading layered flowering shrubs and low groundcover beside the paths
- [outdoor] hardy wild plants between paving joints and small shrubs sheltered behind retaining walls
- [outdoor] tall slender trees with fine foliage above medium bushes and drifts of colorful wildflowers
- [outdoor] an irrigated pocket garden with large shade trees, dwarf shrubs and bright orchids beneath a canopy
- [outdoor] rain-dark tree trunks surrounded by ferns, moss and delicate flowering vines in sheltered corners
- [outdoor] sculpted large and medium bonsai trees in broad stone containers beside a cultivated courtyard
- [outdoor] flowering fruit trees and medium shrubs edged with small daisies and meadow flowers
- [outdoor] drought-tolerant trees in watered beds with compact shrubs, succulents and small vivid desert flowers
- [outdoor] weathered native trees with layered understory shrubs and seasonal flowers bordering a clear walkway
- [outdoor] climbing greenery on trellises, large trees beyond, and pockets of orchids in protected planters
- [outdoor] a community garden of tall shade trees, medium bonsai, fragrant shrubs and mixed flowering beds
- [indoor] large leafy plants in floor-standing ceramic pots and medium ferns in smaller planters near the light
- [indoor] a flowering orchid in a glazed pot beside a small carefully pruned bonsai on a side table
- [indoor] medium broad-leaf plants in clustered planters beneath a large potted indoor tree
- [indoor] a small bonsai in a shallow tray, miniature flowering plants and a tall palm in a floor planter
- [indoor] orchids of different colors on recessed shelves and medium plants in textured earthenware pots
- [indoor] a large potted ficus beside a bench with smaller fern pots and a few bright flowering plants
- [indoor] cascading plants on wall shelves above medium rubber plants and one small flowering bonsai
- [indoor] large and medium foliage plants in built-in planters around seating, with orchids as small accents
- [indoor] a miniature bonsai collection beside a window, each tree a different shape, with a large leafy floor plant
- [indoor] a sheltered atrium planting bed with a large indoor tree, medium shrubs and small flowering orchids

## Interior life
- [indoor] a planted freshwater fish tank in a lounge alcove, with tiny colorful fish among aquatic leaves
- [indoor] a wide aquarium integrated into a sheltered reception wall, with a few fish at different depths
- [indoor] a compact aquarium on a sturdy sideboard, with smooth stones and a small shoal of bright fish
- [indoor] a tall glass fish tank beside seating, with aquatic plants, soft lighting and slow-moving fish
- [indoor] a low aquarium in a protected common room niche, with driftwood and a few jewel-colored fish
- [indoor] a small tabby cat curled on a cushion in a quiet seating alcove
- [indoor] a black-and-white cat stretching beside its bed near a lounge window
- [indoor] a ginger cat watching the room from a low bench in a safe common area
- [indoor] a small gray cat resting on a padded shelf beside a water bowl
- [indoor] a calico cat peeking around a lounge chair with its tail relaxed
- [indoor] a cute small curly-coated dog dozing on a mat in a sheltered lounge
- [indoor] a small floppy-eared dog sitting beside a bench with a chew toy at its paws
- [indoor] a compact cream-colored dog resting in a basket beneath a side table
- [indoor] a friendly little mixed-breed dog stretching on a rug near a water bowl
- [indoor] a small short-legged dog watching from its bed beside communal seating
- [indoor] a calm small red fox curled in a padded pet nook in a residential common area
- [indoor] a small fennec fox with large ears resting on a cushion in a protected lounge
- [indoor] a silver fox companion reclining beside its water dish in a cozy habitation alcove
- [indoor] a small fox with a white-tipped tail sitting alert on a lounge rug
- [indoor] a sleepy fox companion tucked into a soft basket away from the working area

## Activity
- [outdoor,indoor] [population=military,mixed] uniformed personnel checking equipment before a watch change, each attending to a different small task
- [outdoor,indoor] [population=military,mixed] a small patrol moving along a clear route with relaxed spacing and equipment carried safely
- [outdoor,indoor] [population=military,mixed] service personnel consulting a portable map while a colleague observes the approaches
- [outdoor,indoor] [population=military,mixed] off-duty troops sharing a quiet meal beside their neatly stowed kit
- [outdoor,indoor] [population=military,mixed] a squad leader briefing a few attentive adults with varied listening postures
- [outdoor,indoor] [population=military,mixed] military technicians checking secured maintenance fittings while a supervisor records the inspection
- [outdoor,indoor] [population=military,mixed] uniformed logistics personnel comparing supply cases against a handheld manifest
- [outdoor,indoor] [population=military,mixed] a sentry exchanging a brief handover with an arriving colleague
- [outdoor,indoor] [population=civilian,mixed] civilian travelers checking their bags and quietly discussing their onward route
- [outdoor,indoor] [population=civilian,mixed] local workers taking a brief break and sharing a drink away from moving equipment
- [outdoor,indoor] [population=mixed] uniformed personnel giving directions to civilian visitors at a safe stopping point
- [outdoor,indoor] [population=mixed] civilian contractors and military technicians comparing notes over a small secured tool case
- [space] [population=military,mixed] tethered naval technicians inspecting closed boarding hatches with gloved hand signals
- [space] [population=military,mixed] a pressure-suited military repair team securing replacement panels from anchored work positions
- [space] [population=civilian,mixed] a tethered civilian salvage crew checking strapped-down components without releasing debris
- [space] [population=mixed] a suited naval inspector and civilian technician comparing an exterior service fitting from secure handholds
- [outdoor,indoor] individuals walking to their destinations, with one pair pausing for a quiet conversation
- [outdoor,indoor] residents relaxing on available seating while others pass naturally through the space
- [outdoor,indoor] maintenance workers checking a safe service point while a colleague consults a handheld tool
- [outdoor,indoor] a few visitors orienting themselves and exchanging a casual gesture
- [outdoor,indoor] workers carrying small supplies along a clear route, at different stages of their tasks
- [outdoor,indoor] off-duty adults chatting with relaxed postures and varied gazes
- [outdoor,indoor] one adult reading a handheld device while companions discuss their next destination
- [outdoor,indoor] site personnel making a routine inspection, with natural spacing and differing stances
- [outdoor,indoor] travelers resting with small bags near seating while other adults walk past
- [outdoor,indoor] adults sharing a brief greeting before continuing separate everyday tasks
- [outdoor,indoor] a local guide pointing out an architectural detail to a couple of interested adult visitors
- [outdoor,indoor] colleagues comparing notes at a safe stopping place off the main route
- [outdoor,indoor] a custodian attending to a small upkeep task while passersby give them space
- [outdoor,indoor] an adult adjusting a shoulder bag as companions wait nearby
- [outdoor,indoor] adults pausing to appreciate the surroundings while others continue on their way
- [space] tethered suited technicians inspecting exterior access fittings from secure handholds
- [space] a small pressure-suited work crew moving supplies between attached service platforms
- [space] tethered inspection workers exchanging hand signals beside a docking structure
- [space] pressure-suited specialists checking a secured instrument bay without drifting away
- [space] suited maintenance workers at separate anchored work positions along an exterior truss

## Population
- x3 [population=civilian] civilian residents and local workers going about their day
- x3 [population=civilian] civilian travelers with a few local guides and transport staff
- x3 [population=civilian] civilian engineers and maintenance specialists on a routine assignment
- x3 [population=civilian] civilian port workers and freight handlers between scheduled transfers
- x3 [population=civilian] civilian researchers and survey staff comparing observations
- x3 [population=civilian] civilian medical and support staff taking a break between duties
- x3 [population=civilian] civilian contractors and site managers checking ongoing work
- x3 [population=civilian] civilian salvage specialists and visiting inspectors examining the site
- [population=military] regular military personnel from one unit, with distinct individuals and varied duties
- [population=military] naval service personnel including deck crew, technicians and watch officers
- [population=military] mech pilots accompanied by military maintenance and support specialists
- [population=military] expeditionary infantry and their logistics support personnel
- [population=military] garrison troops and a small number of duty officers
- [population=military] military medical personnel and service support staff
- [population=military] reconnaissance personnel with a few communications specialists
- [population=military] off-duty military personnel relaxing between assignments
- x2 [population=mixed] mixed civilian workers and uniformed military personnel sharing the location
- x2 [population=mixed] civilian contractors working alongside military engineers
- x2 [population=mixed] civilian travelers passing through with uniformed service personnel nearby
- x2 [population=mixed] local civilian specialists coordinating with a visiting military delegation

## Clothing and equipment
- [outdoor,indoor] [population=civilian] varied practical civilian jackets, trousers and comfortable footwear with individual colors and wear
- [outdoor,indoor] [population=civilian] civilian work coveralls with differently rolled sleeves and small personal tool pouches
- [outdoor,indoor] [population=civilian] layered civilian travel clothing with compact bags and light outerwear
- [outdoor,indoor] [population=civilian] civilian utility vests over mixed shirts and rugged work trousers
- [outdoor,indoor] [population=civilian] understated tailored civilian clothing with distinct cuts and restrained accessories
- [outdoor,indoor] [population=civilian] civilian technical workwear with safety harnesses or protective gear where the location requires it
- [outdoor,indoor] [population=civilian] worn civilian salvage clothing with patched pockets and securely carried compact tools
- [outdoor,indoor] [population=civilian] civilian medical workwear with practical closed shoes and small duty bags
- [outdoor,indoor] [population=military] coherent service uniforms with individual fit, sleeve choices and subtle wear
- [outdoor,indoor] [population=military] field fatigues with compact webbing and safely secured duty equipment
- [outdoor,indoor] [population=military] flight suits with individual harness adjustments and helmets stowed when the environment permits
- [outdoor,indoor] [population=military] naval duty coveralls with restrained rank distinctions and personal tool pouches
- [outdoor,indoor] [population=military] light protective service armor over fitted underlayers, with safely slung equipment
- [outdoor,indoor] [population=military] off-duty service shirts and trousers with jackets loosely worn or folded nearby
- [outdoor,indoor] [population=military] military engineering coveralls with reinforced knees and compact maintenance kits
- [outdoor,indoor] [population=military] medical service fatigues with small trauma pouches and practical protective gloves
- [outdoor,indoor] [population=mixed] clearly civilian jackets and workwear alongside a smaller group in coherent service uniforms
- [outdoor,indoor] [population=mixed] civilian contractor coveralls alongside military engineering fatigues, distinguished by cut and equipment
- [outdoor,indoor] [population=mixed] varied civilian travel layers alongside naval duty coveralls and compact service bags
- [outdoor,indoor] [population=mixed] civilian specialist workwear alongside military field uniforms, with distinct individual wear and accessories
- [outdoor,indoor] practical layered clothing suited to the selected roles, with a few restrained personal accessories
- [outdoor,indoor] environment-appropriate protective workwear, with differences in fit, wear and securely carried tools
- [space] [population=civilian] civilian industrial pressure suits with closed helmets, compact life-support packs and tethered tools
- [space] [population=civilian] patched civilian salvage pressure suits with sealed gloves, closed helmets and scuffed protective knee plates
- [space] [population=civilian] civilian survey pressure suits with closed helmets, secured instrument pouches and individual suit colors
- [space] [population=military] military EVA pressure suits with sealed helmets, armored outer panels and compact secured duty equipment
- [space] [population=military] naval maintenance pressure suits with closed helmets, protected joints and tethered service tools
- [space] [population=military] military rescue pressure suits with sealed helmets, compact medical packs and secure handhold attachments
- [space] [population=mixed] civilian work pressure suits alongside military EVA pressure suits, all with sealed helmets and visibly different equipment
- [space] [population=mixed] civilian survey pressure suits and naval inspection pressure suits, with closed helmets and distinct individual suit markings
- [space] role-appropriate sealed pressure suits with closed helmets, secured tools and restrained individual color accents

## Adult age mix
- x3 mostly young adults in their twenties, with a few experienced adults in their forties
- x3 young adults spanning their twenties and early thirties, with visibly different levels of maturity
- x3 mostly adults in their twenties and thirties, with one older colleague when group size permits
- x3 a young adult majority supported by a small number of middle-aged mentors
- adults distributed evenly from their twenties through their fifties
- a broad adult age range from early twenties to late sixties, avoiding a single dominant age
- mostly adults in their thirties and forties, with a few younger colleagues
- mostly middle-aged adults with varied signs of age and a few younger adults
- mostly adults in their forties and fifties, with a small number of older specialists
- older adults in their fifties and sixties with a few younger adult colleagues
- mostly older adults, with natural facial lines, varied posture and realistic mobility
- a few young adults working alongside a larger group of experienced middle-aged adults
- pairs or small groups that each include adults of different generations
- young adult newcomers alongside older adult mentors, with neither group dominating the scene
- a mix of early-career adults and late-career adults with fewer people of intermediate ages
- adults mostly in their thirties, with distinct faces rather than a uniform youthful appearance
- adults mostly in their forties, with varied hairlines, facial lines and body types
- adults mostly in their fifties, with believable differences in fitness and posture
- a small intergenerational adult group spanning several decades, scaled to the requested population density
- an unstructured adult age mix, with each small group showing a different balance of younger and older adults

## Appearance variety
- varied skin tones, face shapes, hair textures and builds, with restrained natural hair colors
- broad variation in height and body build, with each person's silhouette easy to distinguish
- a balanced mix of masculine, feminine and androgynous adult presentations, with individual styling
- varied natural hairstyles including short cuts, tied-back hair, curls and close-cropped hair
- a few selectively dyed hair accents among mostly natural hair colors, consistent with the selected roles
- varied adult faces with freckles, fine lines or small healed scars visible only at appropriate distances
- a few practical assistive devices or unobtrusive prosthetic limbs, with natural everyday posture
- subtle cybernetic details on a minority of adults, integrated into otherwise ordinary human appearances
- a wide mix of adult body types, including slender, broad, stocky and soft builds
- mostly practical short or tied-back hairstyles, with varied textures, hairlines and natural colors
- varied facial hair, clean-shaven faces and makeup choices appropriate to each adult's presentation
- a few distinctive eyeglass frames or practical eyewear, without repeating the same face or accessory
- diverse skin tones with individual freckles, facial structure and hair texture where visible
- mostly feminine-presenting adults with varied heights, builds and distinct individual faces
- mostly masculine-presenting adults with varied heights, builds and distinct individual faces
- many androgynous-presenting adults alongside other presentations, with varied faces and builds
- occasional visible tattoos or small personal jewelry, kept subtle and appropriate to clothing and duties
- visibly different postures and movement styles, with a few relaxed and a few more alert individuals
- varied natural hair colors including dark, brown, blond, red and gray, with realistic individual combinations
- restrained personal styling within the selected dress code, expressed through hair, grooming and minor accessories
