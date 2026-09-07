"""What each kind of ship may roll, and how big it has to be to roll it.

The brief this file exists to enforce, in the user's words: "non-combat ships
like cargo ships, should have minimal shielding and weapons (if any) and no
launch catapults. combat ships depending on their type and size may have some
or many of the previously described features."

Two axes, and keeping them apart is the whole design:

  TYPE decides what a hull is ALLOWED - a cargo hauler has no catapult at any
  size, because a catapult is for flinging mechs and a hauler flings pallets.
  SIZE decides what a hull can CARRY - a spinal lance the length of a city
  block does not fit on a one-hex patrol boat whatever its type is allowed.

Size is not a licence. A five-hex bulk freighter is the largest thing in the
tables and still rolls 'minimal' weapons, because the type gate ran first;
that pairing is the one this file is most often read to check, so it has a
test of its own.

The vocabulary is deliberately generate-npc.py's, so the two generators speak
the same language and a reader of one can read the other:

  EQUIPMENT_POLICY   is WEAPON_POLICY/DRESS_POLICY - a policy per bucket,
                     read by one filter, with a default for anything unlisted.
  'none' policy      is ROLE_LOCKS - the one shape in that file that does NOT
                     hand the pool back when it narrows, because falling back
                     would hand over exactly the thing the lock kept away.
  'civ'/'mil'        are filter_by_mil()'s flags, reused unchanged: civilian-
                     grade hardware and military-issue hardware. Both are live
                     here - see _prefer_military() and the 'minimal' tier.
  EQUIPMENT_GATES    is PLACEMENT_REQUIRES - a prop gate, except that the prop
                     is a piece of this ship's own equipment rather than
                     something in the scene. It is what stops '## Glow
                     placement' lighting a flight deck on a grain freighter.
  '@theme' tags      are the NPC Theme tags, and this file never reads them.
                     Theme decides what a gun LOOKS like; this decides whether
                     the ship has one. Keep those two apart.

Written as a module of its own rather than as another block in a ship
generator, because the matrix below is the deliverable a future author will
argue with, and it should be readable without scrolling past a render loop.
`split_flags` is duplicated from generate-npc.py rather than imported: that
file's name has a hyphen in it and cannot be imported normally (see
test/helpers.py), and this is nine lines.
"""
import sys


# ---------------------------------------------------------------------------
# Flags and bullets
# ---------------------------------------------------------------------------

def split_flags(bullet):
    """'a spinal lance || mil min-huge' -> the text, and its flags.

    Verbatim from generate-npc.py, for the reason in the module docstring.
    Every table this file reads keeps its flags in the SECOND segment; if a
    ship table ever grows a three-segment bullet the way Backdrop did, add a
    flags_for() seam here rather than teaching this function about it.

    A bullet must sit on ONE physical line in the tables file, flags included.
    parse_tables() matches bullets with `^-\\s+(.*?)\\s*$` and matches a
    wrapped continuation line against nothing at all, so a bullet broken
    across two lines arrives here truncated at the first, with its whole flag
    segment gone - and a min-huge spinal driver that has quietly lost its
    floor is neutral, which is how a one-hex patrol boat ends up carrying one.
    """
    text, _, rest = bullet.partition("||")
    return text.strip(), tuple(f for f in rest.split() if f)


# The prose a ship with no hardware of some kind contributes to its prompt:
# nothing at all. Held as a named constant because two places depend on it
# being the empty string - the sentence builders below drop an empty clause
# rather than printing "Its armament is ." - and because it is the value
# filter_by_ship_policy() falls back to when a table has no 'none' bullet to
# find. The Weapon table's weighted empty entry in generate-npc.py is the same
# idea; this one is named because three tables share it.
NO_EQUIPMENT = ""

# The four tables this matrix governs, in the order a prompt reads them out.
# A table added here needs a column in EQUIPMENT_POLICY and a row in
# DEFAULT_EQUIPMENT_POLICY; test_ship_policy.py fails until it has both.
EQUIPMENT_TABLES = (
    "Weapon",
    "Shield generator",
    "Launch catapult",
    "Command bridge",
)

# Tables where "nothing at all" is not a legal answer, and which therefore
# carry no 'none' bullet.
#
# A bridge is not fitted equipment, it is SILHOUETTE: every hull has somewhere
# to be flown from, even where that is one armoured slot in the prow, and a
# ship with no bridge of any kind is not a stealthier ship, it is an
# unfinished drawing. So '## Command bridge' is exempt from the 'none'-bullet
# invariant the other three tables are held to, and no cell may be given the
# 'none' policy for it - policy_for() says so out loud and a test asserts it.
#
# The cost of the exemption is that the two hard locks below lose their floor
# for this table, so both of them fall back to the unfiltered table here
# rather than to a synthesised blank. That is the right trade for exactly one
# table and would be the wrong one for the other three: an unarmed ship is
# always renderable, a bridgeless one is not.
ALWAYS_FITTED_TABLES = ("Command bridge",)

# Tables exempt from the neutral-bullet invariant test_ship_policy.py holds
# against the live file.
#
# Every other equipment table has to carry bullets with NO size flag at all,
# because that neutral pool is what keeps the hard size filter from starving a
# small hull. A catapult table cannot: a catapult is a deck, not a fitting,
# and the smallest honest one still needs a three-hex hull, so demanding three
# size-neutral catapult bullets would demand three catapults that fit on a
# courier. What keeps THIS pool from emptying is its 'none' bullet, which is
# neutral by definition - which is also why this exemption may never be
# extended to a table in ALWAYS_FITTED_TABLES, since those have no 'none'
# bullet to fall back on.
NEUTRAL_POOL_EXEMPT = ("Launch catapult",)


# ---------------------------------------------------------------------------
# Size
# ---------------------------------------------------------------------------

# The four hull bands, their width in Foundry grid hexes, and the flag
# vocabulary an equipment bullet uses to say which hulls it belongs on.
#
# Hex width is not linear - 1, 2, 3, 5 - because the top band is not "one
# bigger than large", it is the cathedral-scale hull and the fleet carrier,
# and a token that reads as merely a bit bigger than a cruiser sells it short
# on the map. The gap is the point.
#
# Two flags per band, and they answer different questions:
#
#   'min-large'  this hardware NEEDS a hull at least this big. A launch
#                catapult is a deck, not a fitting; it has nowhere to go on a
#                one-hex boat. This is the floor, and it is a hard filter.
#   'max-medium' this hardware STOPS looking right above this hull. A single
#                pintle-mounted autocannon on a five-kilometre prow reads as a
#                typo rather than as armament. This is the bullet's own
#                ceiling, and it is why the filter is symmetric.
#
# A bullet carrying NEITHER is neutral and reachable by every hull, and most
# bullets should stay that way - the same discipline the theme tags ask for.
# That neutral pool is what makes the size filter safe to run hard: it cannot
# empty, so it never has to fall back and re-admit hardware that does not fit.
#
# The same two flags are the right vocabulary for a SCENE that cannot hold a
# capital hull - an enclosed commercial berth, an atmospheric descent - and
# filter_by_size() is written against bullets rather than against equipment,
# so '## Backdrop' can carry 'max-medium' and be filtered by this same code
# with nothing new written.
#
# The 'hex' entry is the width itself, spelled as the flag a '## Size' bullet
# carries so the VTT sizing and this module cannot drift apart silently:
# nothing here reads a hex flag to make a decision, but a live test asserts
# that a Size bullet saying 'hex3' is the same bullet saying 'large'.
SIZE_BANDS = {
    "small": {
        "hexes": 1,
        "min": "min-small",
        "max": "max-small",
        "hex": "hex1",
        # What the Size table's own bullets are describing, kept here so a
        # reader of the matrix knows what a band means without opening the
        # tables file. Not prose that reaches a prompt.
        "gloss": "one hex - a patrol boat, a courier, a single-crew hull",
    },
    "medium": {
        "hexes": 2,
        "min": "min-medium",
        "max": "max-medium",
        "hex": "hex2",
        "gloss": "two hexes - a destroyer, a working freighter, a corvette",
    },
    "large": {
        "hexes": 3,
        "min": "min-large",
        "max": "max-large",
        "hex": "hex3",
        "gloss": "three hexes - a cruiser, a light carrier, a bulk hauler",
    },
    "huge": {
        "hexes": 5,
        "min": "min-huge",
        "max": "max-huge",
        "hex": "hex5",
        "gloss": "five hexes - a fleet carrier, a battleship, a cathedral "
                 "hull",
    },
}

# The ordering a size floor needs. Derived from nothing - it IS the ordering -
# and every comparison in this file goes through size_rank() rather than
# comparing band names, so a fifth band inserted in the middle is one edit.
SIZE_ORDER = ("small", "medium", "large", "huge")


def size_rank(band):
    """Where a band sits in SIZE_ORDER; 0 for a band this file has never heard of.

    Unknown bands resolve DOWNWARD on purpose. Every filter here is a ceiling
    of some kind, so the smallest band is the least permissive answer, and a
    Size bullet mis-flagged in the tables file should cost a ship its spinal
    lance rather than hand a courier one. It says so on stderr either way: a
    silent 0 is how a whole band's hardware goes quietly unrollable.
    """
    if band in SIZE_ORDER:
        return SIZE_ORDER.index(band)
    print("! unknown ship size %r - treating it as %r, so this hull will roll "
          "the smallest hardware in every table. A '## Size' bullet is "
          "missing its band flag, or SIZE_BANDS has been renamed out from "
          "under it." % (band, SIZE_ORDER[0]), file=sys.stderr)
    return 0


def hexes_for(band):
    """The width in Foundry grid hexes of a size band; 1 for an unknown one."""
    return SIZE_BANDS.get(band, SIZE_BANDS[SIZE_ORDER[0]])["hexes"]


def size_of(bullet):
    """The band a rolled '## Size' bullet names, from its flag segment.

    The Size table's prose is what reaches the prompt ("a capital hull several
    kilometres long, ...") and the band is a flag on it, the same way a Role
    bullet carries 'mil'. Keying the matrix on the band rather than on the
    bullet text is the one place this file deliberately does NOT copy
    ROLE_CATEGORIES' exact-text keying: there will be a dozen ways to write
    "big", and they all mean the same four numbers.
    """
    for flag in split_flags(bullet)[1]:
        if flag in SIZE_BANDS:
            return flag
    return SIZE_ORDER[0]


def size_bounds(bullet):
    """(floor, ceiling) as SIZE_ORDER ranks for one equipment bullet's flags.

    An unflagged bullet is (0, 3) - the whole range - which is what makes it
    neutral. Multiple flags intersect rather than conflict: 'min-medium
    max-large' is a piece of hardware for the two middle bands, which is a
    thing an author will want to say and costs nothing to support.
    """
    flags = split_flags(bullet)[1]
    floor, ceiling = 0, len(SIZE_ORDER) - 1
    for rank, band in enumerate(SIZE_ORDER):
        if SIZE_BANDS[band]["min"] in flags:
            floor = max(floor, rank)
        if SIZE_BANDS[band]["max"] in flags:
            ceiling = min(ceiling, rank)
    return floor, ceiling


# ---------------------------------------------------------------------------
# Ship types
# ---------------------------------------------------------------------------

# The ten hull types, their display name, and the size bands each may roll.
#
# Keyed on a slug rather than on the '## Ship type' bullet's exact text - the
# other half of the argument size_of() makes above. ROLE_CATEGORIES keys on
# bullet text because a Role IS its sentence and there are twenty-two of them;
# a ship type is a category with several possible sentences ("a blunt-nosed
# bulk hauler", "an automated container barge") that must all land on the same
# policy row, so the slug is a flag on the bullet and this is keyed on the
# flag. test_ship_policy.py holds that every slug is carried by a live bullet,
# that every live bullet carries exactly one, and that the BANDS a live bullet
# lists are these bands exactly - the tables file and this dict are two
# statements of the same whitelist and there is no way to tell which one the
# generator obeyed by reading a render.
#
# 'sizes' is what the SIZE roll is drawn from once the type is known, so the
# type gates the size and not the other way round. Two bands each for most
# types, because one band makes a type's every render the same scale and four
# makes the type mean nothing. The bands overlap between neighbours on purpose
# - a large destroyer and a small cruiser are the same size and different
# ships, which is what the equipment matrix is for.
#
# Cruiser is the one type with three combat bands, and cargo the one non-
# combat type with three. Cruiser reaches 'huge' because the cathedral hull -
# kilometres of buttressed prow and gilt statuary - is a CRUISER at that
# scale and not a battleship, which SIZE_BANDS' own huge gloss already says;
# without the band the tables' best capital hull is unrollable. Cargo reaches
# it because a bulk hauler is genuinely the largest thing in the setting, and
# holding it there while its weapons stay 'minimal' is the clearest statement
# this file makes that size is not a licence.
SHIP_TYPES = {
    "carrier": {
        "name": "Carrier",
        "sizes": ("large", "huge"),
    },
    "battleship": {
        "name": "Battleship",
        "sizes": ("large", "huge"),
    },
    "cruiser": {
        "name": "Cruiser",
        "sizes": ("medium", "large", "huge"),
    },
    "destroyer": {
        "name": "Destroyer",
        "sizes": ("small", "medium"),
    },
    "patrol": {
        "name": "Patrol boat",
        "sizes": ("small",),
    },
    "stealth": {
        "name": "Stealth ship",
        "sizes": ("small", "medium"),
    },
    "recon": {
        "name": "Reconnaissance ship",
        "sizes": ("small", "medium"),
    },
    "smuggler": {
        "name": "Smuggler ship",
        "sizes": ("small", "medium"),
    },
    "cargo": {
        "name": "Cargo ship",
        "sizes": ("medium", "large", "huge"),
    },
    "support": {
        "name": "Support ship",
        "sizes": ("medium", "large"),
    },
}

# The order a listing prints them in - roughly line-of-battle first, then the
# small combatants, then the ships that are not warships at all. dict order
# already gives this; the constant exists so a caller does not have to know
# that, and so a reordering of the dict for readability cannot silently
# reorder a UI.
SHIP_TYPE_ORDER = tuple(SHIP_TYPES)


def sizes_for(ship_type):
    """The size bands `ship_type` may roll, smallest first."""
    return SHIP_TYPES[ship_type]["sizes"]


def ship_type_of(bullet):
    """The type slug a rolled '## Ship type' bullet carries, or None.

    None rather than a guess: an unslugged bullet is an authoring error, and
    policy_for() below is where it gets reported, once, with the table name
    that made it matter.
    """
    for flag in split_flags(bullet)[1]:
        if flag in SHIP_TYPES:
            return flag
    return None


def bands_of(bullet):
    """The size bands a '## Ship type' bullet lists, in SIZE_ORDER order.

    The tables file states the whitelist a second time, in flags, so that a
    reader of the bullet can see what it may roll. Two statements of one fact
    drift; this is what the live test compares against sizes_for().
    """
    flags = split_flags(bullet)[1]
    return tuple(band for band in SIZE_ORDER if band in flags)


# ---------------------------------------------------------------------------
# The matrix
# ---------------------------------------------------------------------------

# What each type may roll from each of the four equipment tables.
#
# The five policies, weakest to strongest:
#
#   'none'     always the 'none' bullet; the real pool is never reached at
#              all. A HARD LOCK - it does not fall back, ever. See
#              filter_by_ship_policy() for why that is safe here in a way it
#              is not for the NPC file's Gear table.
#   'minimal'  bullets flagged 'civ', or the 'none' bullet, with the 'none'
#              bullet stacked MINIMAL_NONE_COPIES deep so "if any" reads as
#              "usually not". Civilian-grade hardware only: a hauler's point-
#              defence turret, not a naval gun.
#   'light'    the real pool, but capped to LIGHT_CAP[size] hardware - a small
#              hull's guns are small guns, and a large hull under this policy
#              still gets nothing above medium-class. This is the policy for a
#              ship that is armed but is not a warship of the line.
#   'any'      the real pool, floor and ceiling only. The 'none' bullet is
#              still reachable, so a ship under this policy is USUALLY fitted
#              and not ALWAYS.
#   'heavy'    the 'none' bullet is excluded; the ship always has one, and
#              civilian-grade hardware is dropped while military-grade
#              hardware remains. The other hard direction, and the one the
#              carriers' catapults need.
#
# Each row is justified against the brief on its own line. The justification
# is the point of the row: a later author changing a cell should be able to
# see, in one line, what argument they are overturning.
EQUIPMENT_POLICY = {
    # The flight deck IS the weapon, so its guns stay defensive ('any', not
    # 'heavy') while the catapults are the one thing it may never lack.
    "carrier": {
        "Weapon": "any",
        "Shield generator": "heavy",
        "Launch catapult": "heavy",
        "Command bridge": "heavy",
    },
    # The line-of-battle hull: always armed, always shielded, always a tower.
    # Catapults 'light' rather than 'none' or 'heavy' - the brief allows the
    # largest battleships one, and under LIGHT_CAP that resolves to exactly
    # that: a five-hex battleship may roll the rail-scale hardware, a three-
    # hex one rolls nothing, and the launch DECKS stay a carrier's, because
    # they carry a 'max-large' ceiling that a huge hull cannot reach.
    "battleship": {
        "Weapon": "heavy",
        "Shield generator": "heavy",
        "Launch catapult": "light",
        "Command bridge": "heavy",
    },
    # A warship, so armed and shielded without exception; no mech capacity,
    # which is where the brief draws the catapult line.
    "cruiser": {
        "Weapon": "heavy",
        "Shield generator": "heavy",
        "Launch catapult": "none",
        "Command bridge": "heavy",
    },
    # Armed without exception, but a screening hull: shields 'any' so a
    # stripped-down escort is reachable, and no deck to fly anything off.
    "destroyer": {
        "Weapon": "heavy",
        "Shield generator": "any",
        "Launch catapult": "none",
        "Command bridge": "any",
    },
    # Small hull, small guns - the user's own words. Everything is capped by
    # 'light' rather than forbidden: a patrol boat is a warship, just a tiny
    # one, and its bridge is a canopy rather than a tower.
    "patrol": {
        "Weapon": "light",
        "Shield generator": "light",
        "Launch catapult": "none",
        "Command bridge": "light",
    },
    # The user's spec exactly: shields 'any' (it survives by not being seen
    # and by soaking the shot that finds it anyway), weapons 'light' (a big
    # gun needs a big mounting and a big mounting breaks the silhouette),
    # bridge 'light' so it stays flush and low-profile rather than a tower.
    "stealth": {
        "Weapon": "light",
        "Shield generator": "any",
        "Launch catapult": "none",
        "Command bridge": "light",
    },
    # Sensors are the payload. Armed only enough to break contact, so
    # 'minimal' rather than 'light' - the difference between a ship that
    # fights its way out and one that runs.
    "recon": {
        "Weapon": "minimal",
        "Shield generator": "light",
        "Launch catapult": "none",
        "Command bridge": "light",
    },
    # Armed because the job is dangerous, quietly because the job is illegal:
    # 'light' weapons on a hull whose shielding is whatever could be bought
    # second-hand. Not a warship, so no catapult.
    "smuggler": {
        "Weapon": "light",
        "Shield generator": "minimal",
        "Launch catapult": "none",
        "Command bridge": "light",
    },
    # The brief's named case, and the reason this file exists: minimal
    # weapons, minimal shielding, no catapults - at every size, including the
    # five-hex bulk hulls, which are the largest ships in the tables. Bridge
    # stays 'any' because a hauler's crew tower is a real and often huge
    # structure; it is the one thing about a freighter that is not minimal.
    "cargo": {
        "Weapon": "minimal",
        "Shield generator": "minimal",
        "Launch catapult": "none",
        "Command bridge": "any",
    },
    # A fleet auxiliary - tender, tug, hospital, replenishment. Non-combat, so
    # 'minimal' weapons; but it keeps station with the battle line and gets
    # shot at there, which is the whole argument for 'light' shields rather
    # than 'minimal' ones. Handling gear is not a catapult and belongs in the
    # hull tables, not here.
    "support": {
        "Weapon": "minimal",
        "Shield generator": "light",
        "Launch catapult": "none",
        "Command bridge": "any",
    },
}

# What a ship type gets from a table EQUIPMENT_POLICY does not name.
#
# Per-table rather than a single value, and that asymmetry is the whole point.
# generate-npc.py learned the hard way that one unlisted bucket falling
# through to the permissive default arms seven civilian Roles by accident
# (see DEFAULT_WEAPON_POLICY), so the default here has to be the safe answer
# for each column separately. Weapons and shields default to 'light' - a new
# type is probably some kind of combatant and 'light' is wrong in neither
# direction badly. Catapults default to 'none', because there is exactly one
# type in the file that always has them and nine that never do, and a new type
# guessed into a flight deck is precisely the brief's failure. Bridges default
# to 'any' because every ship has somewhere to stand.
DEFAULT_EQUIPMENT_POLICY = {
    "Weapon": "light",
    "Shield generator": "light",
    "Launch catapult": "none",
    "Command bridge": "any",
}

# Every policy filter_by_ship_policy() implements. A cell holding anything
# else is not an error anywhere in that function - it falls through to the
# 'any' tail and quietly unrestricts itself - so the tests read this constant
# rather than a list of their own.
POLICIES = ("none", "minimal", "light", "any", "heavy")

# The hardware ceiling 'light' imposes, per hull band: one band BELOW the
# hull, floored at 'small'.
#
# One below rather than the hull's own band, because a cap equal to the hull is
# what 'any' already means - a 'light' policy that resolved to the hull's own
# band would be a no-op, which is the quietest way for a policy row to stop
# doing anything. So a two-hex stealth hull rolls one-hex guns: a big gun needs
# a big mounting and a big mounting is what a stealth hull cannot have.
#
# Neutral bullets - the ones carrying no size flag at all, which is most of
# every table - have a floor of 'small' and stay reachable under every cap, so
# this narrows the pool without ever starving it.
#
# 'huge' capping at 'large' is the one entry that reaches above max-medium, and
# it exists for exactly one cell in the matrix: a five-hex battleship's launch
# catapult. A catapult is large-class hardware at the least, so any lower cap
# would forbid them outright and the brief allows the largest battleships one.
# The result is the intended reading of "plausibly the largest battleships" -
# a huge battleship may roll the rail tier, a large one rolls nothing at all.
# What keeps it off a full flight DECK is not this cap but the deck bullets'
# own 'max-large' ceiling: a cap says how big the hardware may be, a ceiling
# says how big the hull may be, and only the second can say "this belongs to
# carriers, who reach it at three hexes, and to nobody at five".
LIGHT_CAP = {
    "small": "small",
    "medium": "small",
    "large": "medium",
    "huge": "large",
}

# How many extra copies of the 'none' bullet the 'minimal' tier stacks into
# the pool - the dial for the brief's "(if any)". CIVILIAN_UNARMED_COPIES in
# generate-npc.py is the same knob for the same purpose and sits at 3; this is
# one higher because a freighter with no guns at all is more ordinary than a
# civilian with empty hands, and because the civ-grade pool it is stacked
# against is small.
MINIMAL_NONE_COPIES = 4

# How much military-grade hardware a 'heavy' cell must still have left before
# it drops the civilian-grade bullets from its pool.
#
# The 'mil'/'civ' split used to be decorative here: only the 'minimal' tier
# read 'civ', so nothing kept a commissioned destroyer off "a token defensive
# turret, plainly an afterthought" or a fleet carrier off corporate liveried
# emitter housings polished to showroom finish. 'heavy' means a warship of the
# line, and a warship of the line is issued its hardware.
#
# It is a PREFERENCE and not a lock, and this number is why: a table that has
# not yet grown two military bullets in some band would otherwise pin the cell
# to one piece of hardware, or empty it, and a slightly civilian gun is a far
# smaller failure than every ship of a type carrying the identical mount. Two,
# rather than one, because one real answer is a uniform rather than a roll.
MIL_PREFERENCE_FLOOR = 2

# Which equipment roll each gate flag needs to have come back fitted.
#
# PLACEMENT_REQUIRES in generate-npc.py gates a glow placement against a prop
# in the scene - 'ground', 'wall', 'signage'. The ship generator has the same
# problem one table over: '## Glow placement' can light a flight deck, a
# shield envelope or a charging gun muzzle, and whether the ship HAS one of
# those is four rolls that already happened. Without this gate the glow puts a
# lit launch deck on a grain freighter, which routes around the 'none' lock in
# the one direction the lock cannot see.
#
# Keyed the other way round from EQUIPMENT_POLICY on purpose: a table has one
# gate, a gate names one table, and a placement bullet spells the gate rather
# than the table so it reads as English - '|| combat armed', not
# '|| combat Weapon'.
#
# There is no gate for '## Command bridge' because there is no roll it can
# lose: it is in ALWAYS_FITTED_TABLES, so a placement may always speak of the
# bridge. It may not speak of a bridge TOWER - that is hull shape, and the
# placement table's own note is where that rule lives.
EQUIPMENT_GATES = {
    "Weapon": "armed",
    "Shield generator": "shielded",
    "Launch catapult": "deck",
}

# The gate vocabulary a '## Glow placement' bullet may carry, for the tables
# file's note to quote and for a test to check nothing else is being read.
EQUIPMENT_GATE_FLAGS = tuple(sorted(EQUIPMENT_GATES.values()))


def policy_for(ship_type, table_name):
    """The policy `ship_type` gets for `table_name`.

    An unknown type or an unlisted table falls to DEFAULT_EQUIPMENT_POLICY and
    says so once on stderr. Loud rather than silent for the reason size_rank()
    gives: a type slug reworded in the tables file otherwise turns the whole
    matrix off for that hull with nothing to show for it, and the direction it
    fails in - catapults - is the one the brief is about.
    """
    row = EQUIPMENT_POLICY.get(ship_type)
    if row is None:
        print("! no EQUIPMENT_POLICY row for ship type %r - falling back to "
              "the per-table defaults, which give it no launch catapult. Add "
              "a row, or check the '## Ship type' bullet's slug flag."
              % ship_type, file=sys.stderr)
        return DEFAULT_EQUIPMENT_POLICY.get(table_name, "light")
    return row.get(table_name, DEFAULT_EQUIPMENT_POLICY.get(table_name, "light"))


# ---------------------------------------------------------------------------
# The filters
# ---------------------------------------------------------------------------

def filter_by_size(options, size, cap=None):
    """Bullets whose size flags admit a hull of band `size`.

    Keeps a bullet when its floor is at or below the effective ceiling AND its
    own ceiling is at or above the hull - the two halves of the SIZE_BANDS
    note. `cap` lowers the ceiling below the hull's own band, which is how the
    'light' policy is expressed: the hull could carry more, the policy says it
    does not.

    Written against bullets rather than against equipment, so a scene table
    can use it unchanged: a '## Backdrop' bullet flagged 'max-medium' is an
    enclosed berth that a five-hex hull does not fit inside, which is the same
    sentence about a different kind of object.

    A HARD filter. It does not hand the pool back when it narrows, and that is
    a deliberate departure from filter_by_dress()/filter_by_mil()/
    filter_by_theme() in generate-npc.py, all of which end 'or options'. Those
    are answering "does this pairing read badly", where a slightly odd pairing
    beats a crash. This one is answering "does this object physically fit",
    where the fallback does not produce an odd ship, it produces a one-hex
    patrol boat carrying a kilometre-long spinal lance - the single most
    visible way this generator can be wrong.

    It is safe to run hard because it cannot empty a well-formed table: an
    unflagged bullet is neutral and passes for every band, and every equipment
    table is required to carry neutral bullets plus a 'none' bullet, which is
    itself neutral. test_ship_policy.py holds both invariants against the live
    file, the way test_role_lock.py holds the margin that keeps
    filter_by_role_lock() safe to return nothing from.
    """
    hull = size_rank(size)
    ceiling = hull if cap is None else min(hull, size_rank(cap))
    kept = []
    for bullet in options:
        floor, top = size_bounds(bullet)
        if floor <= ceiling and hull <= top:
            kept.append(bullet)
    return kept


def _prefer_military(pool):
    """Civilian-grade bullets dropped, while enough military ones remain.

    The 'heavy' tier only. A PREFERENCE, guarded by MIL_PREFERENCE_FLOOR: a
    band where the table has not yet grown two military bullets keeps its
    civilian ones rather than collapsing onto a single answer. See that
    constant for the argument.
    """
    military = [x for x in pool if "civ" not in split_flags(x)[1]]
    return military if len(military) >= MIL_PREFERENCE_FLOOR else pool


def filter_by_ship_policy(options, ship_type, size, table_name):
    """The bullets a ship of this type and size may roll from this table.

    Same signature shape as the filter_by_* family in generate-npc.py - the
    pool first, the rolled traits that gate it next, the table name last for
    the filters that need to know which table's flags they are reading.

    WHICH PARTS ARE HARD, stated here because the NPC file draws this line
    per-filter and a reader coming from there will look for it:

      HARD LOCKS - never fall back, never re-admit what they removed:
        * policy 'none'. A cargo ship's launch catapult is not an odd pairing
          that a fallback could be forgiven for producing; it is the exact
          thing the brief forbids. Falling back would hand over precisely what
          the lock kept away, which is filter_by_role_lock()'s argument.
        * the size floor and ceiling, via filter_by_size() - see its docstring.
        * policy 'heavy' excluding the 'none' bullet. A carrier without a
          catapult is not a carrier.

      PREFERENCES - hand the pool back rather than roll nothing:
        * 'minimal' narrowing to 'civ' hardware. If a table has no civ-grade
          bullets yet, a freighter rolling a naval gun is a bad render; a
          crash is a bad program. This is filter_by_dress()'s trade exactly.
        * 'heavy' dropping 'civ' hardware, via _prefer_military().
        * the weighting steps. They only ever add copies, so every bullet the
          hard filters left reachable stays reachable.

    The hard locks are affordable here in a way they are not on the NPC file's
    Gear table, and the reason is worth having in writing: NOTHING is always a
    legal answer for a piece of ship equipment. filter_by_role_lock() can
    return [] only because the Gear pool is fifty bullets deep and a test holds
    that margin; this function can return the 'none' bullet, which three of
    these four tables carry, so it never has to choose between a wrong ship
    and an IndexError. Where even that is missing it synthesises NO_EQUIPMENT
    rather than yielding - an unfitted ship is always renderable.

    The exception is a table in ALWAYS_FITTED_TABLES, where an unfitted ship
    is NOT renderable: a hull with no bridge of any kind is an unfinished
    drawing rather than a stealthier ship. Those tables have no floor to land
    on, so both locks yield to the unfiltered table there and say so on
    stderr, which is the only place in this file a hard filter hands back what
    it removed.
    """
    policy = policy_for(ship_type, table_name)
    always_fitted = table_name in ALWAYS_FITTED_TABLES
    nothing = [x for x in options if "none" in split_flags(x)[1]]

    if policy == "none":
        if always_fitted:
            # Forbidden by construction - a test asserts no cell does this -
            # so this branch is for the edit that adds one anyway.
            print("! '## %s' is in ALWAYS_FITTED_TABLES and cannot be given "
                  "the 'none' policy; every hull has one of these. Treating "
                  "it as 'any'." % table_name, file=sys.stderr)
            policy = "any"
        else:
            # HARD LOCK. The real pool is not consulted at all - not filtered,
            # not weighted, not fallen back to. The synthesised NO_EQUIPMENT
            # is the floor under it: a tables file with no 'none' bullet in
            # this table still cannot give a cargo hauler a flight deck.
            return nothing or [NO_EQUIPMENT]

    # HARD. 'light' lowers the ceiling; every other policy takes the hull's own.
    cap = LIGHT_CAP.get(size) if policy == "light" else None
    pool = filter_by_size(options, size, cap)
    if not pool:
        # Only reachable on a tables file with no neutral bullets in this
        # table at all - an authoring failure the tests catch long before a
        # run does. Yield to 'nothing' rather than to `options`: handing back
        # the unfiltered pool would put min-huge hardware on a one-hex hull,
        # which is the one outcome the hard filter above exists to prevent.
        print("! '## %s' has no bullet a %s hull can carry - this ship will "
              "have none. Every equipment table needs bullets carrying no "
              "size flag at all." % (table_name, size), file=sys.stderr)
        if always_fitted:
            # Except here, where "none" is not an answer this table can give.
            # An oversized bridge is a bad render; a bridgeless hull is a
            # broken one.
            print("! ... except '## %s' has no empty bullet to fall back on, "
                  "so this hull keeps the whole table and may get a bridge "
                  "too big for it." % table_name, file=sys.stderr)
            return options
        return nothing or [NO_EQUIPMENT]

    if policy == "minimal":
        # PREFERENCE: civilian-grade hardware, or nothing, weighted toward
        # nothing. 'civ' is filter_by_mil()'s flag, unchanged in meaning.
        quiet = [x for x in pool
                 if "civ" in split_flags(x)[1] or "none" in split_flags(x)[1]]
        if not quiet:
            print("! '## %s' has no bullet flagged 'civ' and no 'none' bullet, "
                  "so a %s cannot be fitted minimally - falling back to the "
                  "whole table, and this ship may come out better armed than "
                  "its type should allow."
                  % (table_name, SHIP_TYPES.get(ship_type, {}).get("name",
                                                                   ship_type)),
                  file=sys.stderr)
            return pool
        empty = [x for x in quiet if "none" in split_flags(x)[1]]
        return quiet + empty * MINIMAL_NONE_COPIES if empty else quiet

    if policy == "heavy":
        # HARD: the 'none' bullet is out, and no branch below re-admits it.
        fitted = [x for x in pool if "none" not in split_flags(x)[1]]
        if fitted:
            # PREFERENCE: and a warship of the line is issued its hardware.
            return _prefer_military(fitted)
        # Every real bullet was filtered out by size, or the table holds
        # nothing but its 'none' bullet. Both are authoring failures; say so
        # rather than silently shipping an unarmed battleship.
        print("! '## %s' can offer a %s %s nothing but its 'none' bullet - a "
              "'heavy' policy means this ship should always have one."
              % (table_name, size,
                 SHIP_TYPES.get(ship_type, {}).get("name", ship_type)),
              file=sys.stderr)
        return pool

    # 'any' and 'light': the size-filtered pool, 'none' bullet included, so a
    # ship under these policies is usually fitted rather than always.
    return pool


def roll_equipment(tables, ship_type, size, rng):
    """{table name: rolled prose} for the four equipment tables.

    The seam between this matrix and the ship generator that will use it: the
    generator rolls type and size however it likes and hands them here, and
    gets back four strings ready for the prompt, flags already stripped the way
    roll_npc() strips them. Kept in this module so the matrix can be tested
    end-to-end - a policy is only true if a roll obeys it - without the tests
    depending on a generator that is not written yet.
    """
    rolled = {}
    for name in EQUIPMENT_TABLES:
        pool = filter_by_ship_policy(tables[name], ship_type, size, name)
        rolled[name] = split_flags(rng.choice(pool))[0]
    return rolled


# ---------------------------------------------------------------------------
# Equipment gates, for the tables that light this ship rather than fit it
# ---------------------------------------------------------------------------

def gates_for(ship):
    """The gate flags a rolled ship satisfies: 'armed', 'shielded', 'deck'.

    `ship` is a roll_equipment() result. A table is satisfied when its roll
    came back with prose - the 'none' bullet is NO_EQUIPMENT, so "has one" and
    "is truthy" are the same question, which is the whole reason that bullet's
    prose is empty rather than the words "no weapons".
    """
    return frozenset(gate for table, gate in EQUIPMENT_GATES.items()
                     if ship.get(table))


def filter_by_gates(options, ship):
    """Bullets whose gate flags this ship's equipment rolls satisfy.

    For '## Glow placement', and for anything else that describes the ship's
    hardware after the hardware has been rolled. PLACEMENT_REQUIRES in
    generate-npc.py, with the scene swapped for the four equipment tables.

    A bullet carrying NO gate flag is ungated and always kept - the same
    neutral-pool discipline the size flags rely on, and the reason this can be
    hard without starving: a placement that speaks only of the flank, the
    stern or the spine is true of every ship ever rolled. If a table is ever
    written so that every bullet is gated, this hands the pool back and says
    so, because a ship with no glow at all is a worse render than a slightly
    wrong one - the light is the frame's one saturated colour.
    """
    gates = gates_for(ship)
    kept = []
    for bullet in options:
        wanted = set(split_flags(bullet)[1]) & set(EQUIPMENT_GATE_FLAGS)
        if wanted <= gates:
            kept.append(bullet)
    if kept:
        return kept
    print("! every bullet offered to filter_by_gates() needs equipment this "
          "ship does not have - falling back to the whole pool. A placement "
          "table needs bullets carrying no gate flag at all.",
          file=sys.stderr)
    return options


# ---------------------------------------------------------------------------
# Prompt text
# ---------------------------------------------------------------------------

def join_clause(items):
    """'A', 'B', 'C' -> 'A, B and C'; with a compound item, 'A, B, and C'.

    carry_sentence()'s join in generate-npc.py, corrected for three items.
    That one switched the WHOLE separator on finding a compound bullet, which
    gave 'A and B and C' on a plain three-item warship roll and 'A, B, C' -
    a list with no conjunction at all - on a compound one. Ship bullets are
    frequently compound ("four turret batteries and a pair of torpedo tubes"),
    so the fix keeps the list commas and moves only the last connector: an
    Oxford comma appears exactly when an item already contains an 'and', which
    is the one case where it is doing work rather than decorating.
    """
    if len(items) == 1:
        return items[0]
    last = ", and " if any(" and " in x for x in items) else " and "
    return ", ".join(items[:-1]) + last + items[-1]


def armament_sentence(ship):
    """The one sentence naming a ship's guns, shielding and catapults, or ''.

    carry_sentence() in generate-npc.py, applied to a hull: one sentence rather
    than three, because three would open "The hull carries" three times on
    every warship, and returning "" when there is nothing to say so the
    template's slot collapses cleanly instead of leaving "The hull carries ."
    behind. That is the whole of how an unarmed cargo ship's prompt omits the
    armament sentence rather than printing an empty one - the 'none' bullet's
    prose is NO_EQUIPMENT, it falls out of the list here, and if all three fall
    out the sentence is never built.

    Every bullet in these three tables has to read as something a hull CARRIES,
    because this is the sentence they land in. That is a real constraint on the
    tables and it is stated in each of their notes: "overlapping scales of bare
    ablative plating" carries; "bare ablative plating along the hull" does not,
    and doubles the noun besides.
    """
    fitted = [ship.get(name, "") for name in
              ("Weapon", "Shield generator", "Launch catapult")]
    fitted = [x for x in fitted if x]
    if not fitted:
        return ""
    return "The hull carries %s. " % join_clause(fitted)


def bridge_sentence(ship):
    """The command bridge sentence, or '' for a hull with nothing to say.

    Separate from the armament sentence rather than a fourth item in it,
    because a bridge is not carried - it is part of the silhouette, and the
    renderer treats "a tiered bridge tower rising aft" as hull shape rather
    than as fitted equipment. The empty-string branch is kept even though
    '## Command bridge' is in ALWAYS_FITTED_TABLES and should never roll one:
    a caller assembling a ship dict by hand, or a tables file that grows an
    empty bridge bullet anyway, gets a clean omission rather than a stray full
    stop.
    """
    bridge = ship.get("Command bridge", "")
    return "%s. " % bridge if bridge else ""
