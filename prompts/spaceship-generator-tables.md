# Spaceship Generator Tables

Roll tables for `generate-spaceship.py`, which rolls one vessel from these
lists and generates a matched pair of images in the campaign's house style: a
landscape **portrait** of the hull in a scene, for the Foundry actor sheet, and
a top-down orthographic **token** on flat white that gets run through RMBG into
a transparent PNG sized to the ship's grid footprint.

These are _ships_ — carriers, cruisers, patrol boats, bulk haulers, smugglers'
runners — not people and not mechs. Human NPCs live in
`npc-generator-tables.md` and are rolled by `generate-npc.py`; mech art lives in
`mech-catalogue-art-prompts.md` and is authored per chassis rather than rolled.
`scene-and-spaceship-tables.md` is an older general-purpose file whose
`## Spaceships` table was mined into this one; nothing reads it any more.

Two modules read this file and neither of them can be argued with from here.
`generate-npc.py` supplies the parser and the theme, hue and light machinery,
loaded by path because its name has a hyphen in it. `ship_policy.py` supplies
the type/size matrix — `SHIP_TYPES`, `SIZE_BANDS`, `EQUIPMENT_POLICY`,
`LIGHT_CAP` — and is covered by tests that pass today. Every flag spelling
below is that module's, and a flag it does not recognise is **ignored rather
than reported**, so an invented gate ships silently inert. Add a flag to the
code that reads it before adding it to a bullet.

## How the script reads this file

Every `## Heading` starts a table; every `-` bullet under it is one option. The
script looks tables up by their heading, so **renaming a heading breaks the
prompt template** — add and remove bullets freely, but leave the headings
alone. The eighteen the generator requires, in the order it rolls them, are:

`Name prefixes`, `Ship names`, `Theme`, `Ship type`, `Size`, `Faction`, `Hull`,
`Detail`, `Weapon`, `Shield generator`, `Launch catapult`, `Command bridge`,
`Markings`, `Condition`, `Backdrop`, `Weather`, `Glow colour`, `Glow placement`.

**ONE PHYSICAL LINE PER BULLET, flags included, however long the line runs.**
This is the rule that breaks the file most quietly, so it is first. `parse_tables()`
matches a bullet with `^-\s+(.*?)\s*$` and matches a wrapped continuation line
against nothing at all, so a bullet broken across two lines is **silently
truncated at its first line and loses its whole flag segment** — a `min-huge`
spinal driver that has quietly lost its floor is neutral, which is how a
one-hex patrol boat ends up carrying one. The `<!-- -->` comment blocks wrap
freely at about 72 columns; a bullet never does. The longest bullet in the
sibling NPC file is 825 characters on one line, so length is not a reason.

Weights are optional: a bullet may start with `xN ` to count as N entries, so
`- x4 a cruiser, ...` shows up four times as often as a plain bullet. Anything
after the weight is used verbatim, so write bullets as fragments that read
correctly dropped into the templates.

**A weighted bullet cannot have an empty payload.** `x8 ` with nothing after it
does not parse as a weight — the bullet regex's trailing `\s*$` eats the space
the weight regex needs after the digits, so the entry ships as one option whose
literal text is `x8`, and a ship that rolled it would be named "x8 Vespertine".
Write the empty entry as `x60 || none` instead, the idiom `## Weapon` in
`npc-generator-tables.md` already uses; `split_flags()` parses it to empty text
carrying the flag `none`. `## Name prefixes` is the one single-segment table in
this file that must be run through `split_flags()` for that reason.

## Segments and flags

`||` splits a bullet into segments. Most tables use two — prose, then a bare
flag segment. Two use three. (The list below is indented two spaces so that
`parse_tables()` does not read it as a nineteenth table — its bullet regex is
anchored at column zero. `npc-generator-tables.md` does not bother, and carries
two inert extra tables in every parse as a result.)

  - **Ship type** carries exactly one `SHIP_TYPES` slug — `carrier` `battleship`
    `cruiser` `destroyer` `patrol` `stealth` `recon` `smuggler` `cargo`
    `support` — plus the size bands that slug may roll, plus `civ`/`mil`. The
    slug keys `EQUIPMENT_POLICY`, so it is what decides whether a hull may carry
    a gun at all. The band list **must equal `sizes_for(slug)` exactly**; a live
    test compares the two and the drift it catches is a whole (type, size) slot
    going unrollable.
  - **Size** carries exactly one band — `small` `medium` `large` `huge` — and the
    matching hex width, `hex1` `hex2` `hex3` `hex5`. The band is read by
    `size_of()`; nothing reads the hex flag, which is exactly why a test compares
    it against the band on the same bullet. A wrong hex width fails only in the
    VTT.
  - **Faction** carries three segments: `NAME || VISUAL || flags`, the same shape
    `split_faction()` already parses. Flags are `civ` `mil` `palette`
    `unaffiliated` `dressy`.
  - **Backdrop** carries three segments: `SHOT || SCENE || flags`, the same shape
    `split_backdrop()` already parses. Its flags are `weather` — the one flag
    on that table with a live reader today — plus the prop gates `vacuum`
    `dock` `atmosphere` `planetlight` `hull` `debris` `combat` `interior`, an
    optional `max-` cap and an optional `@theme`. Every bullet carries at
    least one flag, so all three segments are always present.
  - **The four equipment tables** — `Weapon`, `Shield generator`,
    `Launch catapult`, `Command bridge` — share one flag vocabulary, documented
    in full above `## Weapon`: a size floor `min-small` … `min-huge`, an optional
    ceiling `max-small` … `max-large`, `civ`/`mil` for the register, `none` on
    the empty bullet, and an optional theme tag on the two themed ones.
  - **Hull** carries exactly one `SHIP_TYPES` slug and exactly one size band —
    the pair the generator must filter on before rolling it — plus an optional
    `palette` where the coat is already a saturated colour, plus an optional
    `@theme`. It carries no `civ`/`mil`, because `## Ship type` already has
    the register in hand at roll time.
  - **Detail**, **Markings** and **Weather** carry `civ`/`mil`, `@theme` where
    the table is themed, and `clear` on a Weather bullet that contributes
    nothing.
  - **Glow placement** carries scene gates (`debris` `hull` `planetlight`
    `combat` as requires, `under-way` as the one forbid) — every one of them a
    word `## Backdrop` actually carries in its own flag segment — and the
    three equipment gates `armed`, `shielded`, `deck` from `EQUIPMENT_GATES`
    in `ship_policy.py`.
  - **Name prefixes**, **Ship names**, **Theme**, **Condition** and
    **Glow colour** are single-segment tables and carry no flags at all — except
    the one weighted empty bullet in `## Name prefixes`, which needs `|| none` to
    parse.

## The size flag vocabulary

`SIZE_BANDS` in `ship_policy.py`, four bands, two flags each, answering
different questions:

| band | hexes | floor flag | ceiling flag | what it is |
|---|---|---|---|---|
| `small` | 1 | `min-small` | `max-small` | a patrol boat, a courier, a single-crew hull |
| `medium` | 2 | `min-medium` | `max-medium` | a destroyer, a working freighter, a corvette |
| `large` | 3 | `min-large` | `max-large` | a cruiser, a light carrier, a bulk hauler |
| `huge` | 5 | `min-huge` | `max-huge` | a fleet carrier, a battleship, a cathedral hull |

`min-` says the hardware needs a hull at least this big; `max-` says it stops
looking right above this one. Multiple flags **intersect** — `min-medium
max-large` is hardware for the two middle bands. **A bullet carrying neither is
neutral and reachable by every hull, and most bullets must stay that way.**
That neutral pool is what makes `filter_by_size()` safe to run as a hard filter
with no fallback: it cannot empty, so it never has to re-admit hardware that
does not fit. `## Launch catapult` is the one exemption — a catapult is a deck
and has nowhere to sit on a one-hex hull — and what keeps that pool from
emptying is its `none` bullet instead.

## The `none` bullet

`## Weapon`, `## Shield generator` and `## Launch catapult` each carry exactly
one bullet whose prose is empty and whose flags contain `none`. It is the floor
every hard filter in `ship_policy.py` lands on when it narrows, and its prose
is empty rather than the words "no weapons" because `armament_sentence()` drops
an empty clause and CFG 1.0 would draw a named absence. It carries the marker
flag rather than the word in its text so a filter can name it without matching
on prose, and it carries a nominal `min-small` floor so the size filter never
has to special-case it.

`## Command bridge` is in `ALWAYS_FITTED_TABLES` and **must not** grow one. A
bridge is silhouette, not fitted equipment: every hull has somewhere to be
flown from, and a hull with no bridge of any kind is an unfinished drawing
rather than a stealthier ship. A hull that should read as blind gets the
faired-over sensor blister, which is a shape rather than an absence.

## Themes

```
THEMED_TABLES = ("Hull", "Detail", "Weapon", "Command bridge", "Backdrop")
```

**Five tables and five only.** `filter_by_theme()` never looks at a table
outside that list, so an `@tag` elsewhere either does nothing at all — failing
quietly, which is worse than failing loudly — or, on a single-segment table
like `## Ship names`, `## Condition` or `## Glow colour`, ships the literal
text `|| @cyberpunk` into the image prompt and the dossier both. The eight tags
are the NPC file's eight, unchanged, so a rolled ship and a rolled crew can be
asked for the same look: `@gundam` `@tactical` `@neosamurai` `@cyberpunk`
`@neogothic` `@grimdark` `@corporate` `@scav`.

A tagged bullet is **unreachable from seven themes out of eight**. So every
slot needs an untagged bullet before it gets a tagged one: every legal
(type, size) pair needs two neutral `## Hull` bullets, every size band of every
equipment table needs neutral hardware, and most bullets everywhere stay
untagged. Write the neutral ones first and the tagged one second, always in
that order.

**Zero tagged bullets for a theme in a themed table, or at least two — never
exactly one.** `apply_theme_share()` duplicates a theme's tagged bullets until
they hold `THEME_SHARE = 0.6` of the pool, computing
`n = ceil(share * neutral / ((1 - share) * tagged))` copies. With **one** tagged
bullet that arithmetic makes that single bullet **sixty per cent of every roll**
under that theme; with two it is thirty; with **none** the function returns the
pool untouched and the theme simply renders from the neutral pool, which is
what most of `npc-generator-tables.md` does in every one of its themed tables.
One is the only bad number, and an earlier draft of this file hit it in
sixteen (theme × table) cells — including all eight of `## Detail`, so that
sixty per cent of every Detail roll came back the same bullet no matter what
was rolled. Today: Hull, Detail, Weapon and Command bridge carry two per theme;
Backdrop carries two for five themes and none for the other three. Count them
before adding one, and if a theme cannot honestly earn a second bullet in a
table, take its first one out rather than leave it alone.

## Never write a negation

Generation runs at CFG 1.0 with **no negative prompt** — the lesson the
`## Stance` note in `npc-generator-tables.md` records, where a rolled "raised
ledge" put a visible platform under the figure and a second person on it. A
noun named in order to forbid it gets drawn anyway, so "no turrets" is how a
grain freighter grows turrets and "no livery at all" is how a shipbreaker's
hull ends up liveried. Say it positively and describe the empty surface rather
than the absent fitting: "bare mounting plates under the nose", "plating
unbroken between the stencils", "cutting scars and chalk survey marks", "the
paint still even everywhere". The absence is enforced by `EQUIPMENT_POLICY`,
which already knows a hauler carries nothing; prose cannot help it and can only
contradict it.

## Evoke, never cite

The reference register is Gundam, Armored Core, Cowboy Bebop, Space Battleship
Yamato and Warhammer 40k, and none of them may be named. No vessel, faction or
property from a published setting reaches a prompt, and no coined term from one
either — describe the prow, the buttress, the welded patch, and let the shape
do the work. Watch the combinations as well as the words: a handful of
individually public-domain naval features can still add up to one famous hull,
and when they do, drop the most identifying of them.

## Word budgets

Both prompts run at `TOKEN_LIMIT = 512` with `CHARS_PER_TOKEN = 4.5`, a ceiling
of about 2,300 characters, and the portrait spends nine rolled segments against
it. What overruns is the closing palette and style tail, which falls off the
end without a warning. Per-slot budgets, enforced at p99 by
`test/test_prompt_budget.py`:

These are the file's own budgets and every one of them is **the measured
maximum of the table as it stands, rounded up** — not an aspiration. Where a
number below differs from the one in design §5, it is because the design's
figure was set before the content existed and the content is what actually has
to fit; the totals at the bottom are what decides, and they fit.

| slot | budget | longest bullet today |
|---|---|---|
| `{size}` | ≤ 90 chars | 85 |
| `{hull}` | ≤ 160 (≈24 words) | 160 |
| `{detail}` | ≤ 90 (≈12 words) | 84 |
| each of the three equipment bullets | ≤ 160 | 155 |
| the three equipment bullets and their join | ≤ 470 sum-of-maxima | 457 |
| `{bridge_line}` | ≤ 135 | 131 |
| `{faction_line}` visual | ≤ 100 (about a dozen words) | 98 |
| `{markings}` + `{condition}` together | ≤ 160 | 157 |
| the Backdrop scene | ≤ 260 (about forty words) | 257 |
| a `## Weather` sentence | ≤ 105 | 100 |

**Measure both prompts, not just the portrait.** The token prompt drops
`{shot}` and the Backdrop scene and adds `{plan}` and a longer framing
preamble, and design §4 predicted it would land comfortably lower. It does not:
it drops about 300 characters and adds about 230, and `{weather_line}` — the
other thing §4 counted on the portrait spending — is empty on half of all rolls
anyway. Over 3,000 policy-legal rolls through this file, composing the design's
own two templates:

```
portrait  min 317  median 408  p90 436  p99 462  max 489   over 512: 0
token     min 331  median 416  p90 433  p99 465  max 484   over 512: 0
```

The token is the longer of the two at the median and at p99. An earlier draft
of this file ran portrait p99 480 / max 494 and token p99 491 / max 505 — over
the ceiling at the tail on the prompt nobody had scored — and `## Hull` at 309
characters against a 130-character budget was most of it. When headroom is
needed, `{hull}` is where to spend the trim, because it is charged in both
images.

## Flags that still need a reader

This file's own rule is *add a flag to the code that reads it before adding it
to a bullet*, and this section is where the file admits how much of itself is
still ahead of that rule. **`ship_policy.py` is written and tested and reads
exactly two things: the four equipment tables' `min-*`/`max-*`/`civ`/`none`
flags, via `filter_by_ship_policy()`, and `## Glow placement`'s `armed` /
`shielded` / `deck`, via `filter_by_gates()`.** `generate-npc.py` reads
`@theme` tags on the five themed tables, `weather` on `## Backdrop`, and the
`clear` flag on `## Weather`. **Everything else in the list below is inert
until `generate-spaceship.py` reads it**, and a flag that ships inert fails
quietly, which is worse than failing loudly. Each row is an obligation on that
script, not a suggestion, and each is a couple of lines:

| table | flag | what `generate-spaceship.py` must do |
|---|---|---|
| `Name prefixes` | `none` | Run `npc.split_flags()` over this table and use segment 0, so the weighted empty bullet renders as no prefix rather than the literal text `none`. |
| `Hull` | the type slug + the size band | Narrow `## Hull` to bullets carrying **both** the rolled `## Ship type` slug and the rolled `## Size` band, **before** the theme filter. Nothing filters this table today; run as-is, a one-hex patrol boat can roll a colossal fleet carrier. |
| `Hull` | `palette` | OR it into the same test that reads `palette` on the rolled `## Faction`, the one that softens the closing line to *"the only **other** saturated color"*. Eleven hull bullets assert a saturated coat and contradict the unsoftened sentence without it. |
| `Ship type`, `Faction`, `Detail`, `Markings` | `civ` / `mil` | Run `npc.filter_by_mil()` over `## Faction`, `## Detail` and `## Markings`, keyed on the register flag of the rolled `## Ship type` bullet. `npc.filter_by_mil` is **not** on design §1's borrowed-surface list and must be added to it. Without this a battleship rolls a courier line's diamonds and a passenger boarding sleeve. |
| `Backdrop` | `dock` `vacuum` `atmosphere` `planetlight` `hull` `debris` `combat` | Supply `PLACEMENT_REQUIRES` / `PLACEMENT_FORBIDS` for the ship copy of `filter_by_placement_prop()` (design §1 lists it as duplicate-and-adapt). The ship version matches **flag against flag** against `split_backdrop(...)[2]`, not the NPC version's regex over scene prose. |
| `Glow placement` | `debris` `hull` `planetlight` `combat` `under-way` | The gate side of the same pair: the first four are requires, `under-way` is forbidden by `dock`. |
| `Backdrop` | `max-small` / `max-medium` | Run `sp.filter_by_size()` over `## Backdrop` against the rolled band, so a five-hex hull does not roll the enclosed commercial berth. The reader exists in `ship_policy.py`; nothing calls it on this table. |
| `Size` | `hex1` `hex2` `hex3` `hex5` | Nothing should read it. The grid width comes from `sp.SIZE_BANDS[band]["hexes"]`, never from this flag; the flag exists so a test can compare the two and catch a typo that would otherwise fail only in the VTT. |

**The check nobody ran, and the one to write first.** Two of the bugs this
section exists to prevent are not "a flag with no reader" but its mirror — **a
reader with no supplier**. `weather_sentence()` gates the whole of `##
Weather` on a `weather` flag that `## Backdrop` carried on zero of its twenty
bullets, so nineteen authored lines and twenty-nine weighted options were dead
content that no roll could reach, and every dossier printed *clear*. Nothing in
`test_ship_policy.py` and nothing in the assembler's own validator looked
across tables. So: **for every flag any table gates on, assert that at least
one bullet of the table that supplies it actually carries it.** That is one
loop over `parse_tables()` and it would have caught this on the first run.

## Placeholders

There are **no pronouns** in this file. `ship_fields()` supplies `{ship}`,
`{Ship}`, `{name}`, `{size}` and `{is_are}`, and nothing else. The `{...}`
substitution pass raises `SystemExit` naming the offending table and option on
any other key, so a stray `{object}` copied over from the NPC file is a hard
failure at render time rather than a stray brace in a prompt.
## Name prefixes

<!--
  The registry mark painted ahead of the proper name - "ISV Vespertine",
  "Free Trader Long Odds", "Baronic Hammerfall". It is a single bare segment,
  and the generator joins it to the '## Ship names' roll as
  ("%s %s" % (prefix, name)).strip(), so an empty roll yields the bare name
  and nothing else.

  MOST HULLS HAVE NO PREFIX, and the weighted empty bullet at the top of the
  list is what makes that true. The sixteen named prefixes carry 28 entries
  between them, so 'x60 || none' leaves an unprefixed hull at 60 of 88 rolls,
  a little over two in three. That weight is the only dial for how registered
  the setting feels: raise it for a frontier, drop it for a Union core world.
  Adding a named prefix moves the ratio, so re-read the arithmetic here when
  you add one.

  THE EMPTY BULLET MUST CARRY '|| none', AND THE GENERATOR MUST RUN
  split_flags() OVER THIS TABLE. That is not decoration, and it is not the
  spelling the design document proposed ('- x8 ' with nothing after the
  weight). That spelling does not work, and it fails in the worst direction:
  parse_tables() matches a bullet with '^-\s+(.*?)\s*$', whose trailing
  '\s*$' eats the space after the weight, so the bullet text arrives as 'x8';
  the weight regex is '^x(\d+)\s+(.*)$' and needs whitespace after the
  digits, so it does not match, and the entry ships as ONE option whose
  literal text is "x8". Every ship that rolled it would be named "x8
  Vespertine". A weighted bullet with an empty payload cannot be written in
  one segment at all - the payload has to contain a non-whitespace character
  for the weight to parse, and the parser strips the whitespace that would
  separate them. '|| none' is this file's own answer, live today as
  'x30 || none' at npc-generator-tables.md:1987, and split_flags() parses it
  to text '' with flags ('none',). The alternative - sixty bare '- ' lines -
  parses correctly too, but any editor or hook that strips trailing
  whitespace deletes all sixty at once and silently gives every ship a
  prefix. This way fails loudly instead.

  Prefixes are drawn from the factions this campaign already has, in
  npc-generator-tables.md's '## Faction' and in '## Faction' here, so a
  rolled prefix and a rolled affiliation agree rather than inventing a second
  registry authority. Union hulls take ISV and UAD; the corpro lines take SSC
  and IPS-N; Harrison Armory takes the word rather than the initials, because
  "HA Hammerfall" reads as a laugh; the Karrakin Trade Baronies take
  "Baronic"; the Sector Defence Flotilla and the colonial militia take SDF
  and Militia; the Meridian Shipping Combine takes "Combine"; Redstar Salvage
  and Coldwater Shipbreakers both take "Salvor". MV, Free Trader, Chartered,
  Privateer and Prize are registrations rather than employers, belong to
  nobody, and carry the commercial weight for exactly that reason - a working
  hull is far likelier to be marked by its trade than by its owner.

  Nothing here may carry a theme tag. This table is single-segment and the
  only '||' in it is the empty bullet's, so a '@grimdark' would reach the
  dossier and the prow as literal text. "Consecrated" is the gothic
  registers' prefix and it will sometimes land on "Cold Coffee"; that is the
  cost of an untagged prefix table, and a spacer setting can carry the joke.
  If it stops being funny, the fix is to add this table to THEMED_TABLES and
  give every bullet a '||' segment, not to slip a bare tag in.

  Never a hull category. "Freighter Vespertine" or "Carrier Indomitable"
  names a type that '## Ship type' has already rolled and will contradict it
  most of the time. A prefix says who registered the hull, not what it is.
-->

- x60 || none
- x4 MV
- x3 Free Trader
- x3 ISV
- x2 UAD
- x2 SDF
- x2 IPS-N
- x2 SSC
- x2 Chartered
- Baronic
- Armory
- Combine
- Militia
- Salvor
- Privateer
- Consecrated
- Prize
## Ship names

<!--
  The name painted on the prow and printed in the dossier. Five registers
  mixed on purpose, because a system's traffic is not all of one kind:

    martial abstractions - Indomitable, Hammerfall, Redoubtable. The default
      warship register, readable under any theme, and the largest block here.
      A handful are old ordnance nouns - Falchion, Culverin, Basilisk - which
      read as a hull's name and never as its armament, since no bullet in
      this table reaches an image prompt.
    saints and virtues - Vigil Everlasting, Reliquary, Absolution Withheld.
      The gothic registers, where a hull is consecrated rather than
      commissioned.
    working-ship plainness - Cold Coffee, Wet Paint, Dead Reckoning. What a
      crew that lives aboard actually paints on it: jokes, grudges, debts,
      weather, and the old sea words a spacer trade inherited whole.
    corporate serials - Asset 12-Calder, Depreciation, Article 8802. A name
      that is really an asset number, or a virtue borrowed from a quarterly
      report.
    ironic spacer humour - Not My Problem, Insurance Claim, My Other Ship.
      The register a hull earns somewhere around its third owner.

  ONE SEGMENT, NO FLAGS, NO THEME TAGS. An earlier draft carried
  '|| @grimdark' and the like on 23 bullets. The tags are gone; every name
  they were on is kept. Only five tables in this file are themed - Hull,
  Detail, Weapon, Command bridge, Backdrop - and a '@tag' on a
  single-segment table ships the literal string "|| @grimdark" into the
  dossier and onto the prow, because nothing splits it off. Restoring them
  means adding this table to THEMED_TABLES and to test_ship_theme.py's
  pinned list FIRST, and accepting that a tagged name is unreachable from
  seven themes in eight - which on a 132-entry table is a large pool to
  shrink for a string nobody renders.

  Do not reuse a word this FILE already spends elsewhere. "Meridian Star"
  beside the "Meridian Shipping Combine" in '## Faction' reads as a mistake
  in the dossier rather than as a coincidence; it is "Windward Star" now,
  and the corporate serial is "Asset 12-Calder". The same check killed a
  "Registry 8802" against the Union Administrative Department's stencilled
  registry number, and it is "Article 8802" instead.

  Do not reuse a root word this TABLE already spends either. THE INVARIANT
  IS: strip the articles and prepositions - of, the, a, an, and, in, on, to,
  at, my, for - lowercase what is left, and no remaining word appears in two
  names. It holds across all 132 entries as they stand, and it does not hold
  by good intentions: an earlier draft asserted it in this paragraph while
  carrying "Long Odds" beside "Long Haul", "Cold Front" beside "Cold Coffee",
  "Morning Star" beside "Windward Star", "Iron Verdict" beside "Snow on
  Iron", "Hand of the Penitent" beside "Hand-Me-Down", "Line Ship Aurelia"
  beside "Line Item Nineteen", "Paid in Full" beside "Full Bunkers" and
  "Dead Reckoning" beside "Deadweight". A false invariant in a comment is
  worse than no invariant, because the next author trusts it instead of
  checking. So CHECK IT rather than believe this paragraph - the four-line
  script is a word split, a Counter and a filter on count > 1 - and if a
  duplicate is ever the right call, delete this paragraph rather than leave
  it lying.

  Keep the registers apart as well as the words. The debt joke is the one
  that spreads: it is native to working-ship plainness and to the corporate
  serials, and it had colonised the gothic block too - "Blessed Remittance",
  "Requiem in Arrears" and "Immaculate Ledger" were an accounting punchline
  wearing a censer, and they are "Blessed Silence", "Requiem Unsung" and
  "Immaculate Hour" now. Ten names in the pool still turn on money, which is
  about right for a spacer trade and well short of a theme.

  Never quote a vessel from the reference media. Evoke the register, not the
  ship - a hull named after a battleship somebody already filmed is a
  citation rather than a name. Every entry here is a common-noun
  construction for that reason, and this is the one table whose value is
  reproduced as literal text rather than paraphrased by a renderer, so it is
  the table to be strictest in.
-->

- Indomitable
- Unyielding
- Implacable
- Resolute
- Vigilant
- Steadfast
- Relentless
- Adamant
- Intrepid
- Tenacity
- Forthright
- Sentinel
- Warden
- Perseverance
- Undaunted
- Formidable
- Redoubtable
- Stalwart
- Obstinate
- Inflexible
- Fortitude
- Constancy
- Audacity
- Gallant
- Unrepentant
- Vespertine
- Hammerfall
- Onslaught
- Broadside
- Thunderhead
- Iron Verdict
- Falchion
- Halberd
- Culverin
- Basilisk
- Fair Warning
- Long Odds
- Northwind
- Cold Front
- Lodestone
- Pale Horizon
- Last Light
- Argus
- Bell and Anchor
- Morning Star
- Dawnbreaker
- Windward Reach
- Solar Wind
- Grey Watch
- Saint Alenna's Mercy
- Vigil Everlasting
- Procession of Candles
- Blessed Silence
- Litany of Ash
- Hand of the Penitent
- Weight of Contrition
- Ninety Martyrs
- Sanctified in Fire
- Ascendant Grace
- Candle Unquenched
- Reliquary
- Solemn Oath
- Threefold Benediction
- Ossuary
- Mourner's Due
- Censer
- Absolution Withheld
- Chalice Unbroken
- Anointed
- Sepulchre
- Faithful Servant
- Requiem Unsung
- Immaculate Hour
- White Lance
- Picket Four
- Hull 118
- Second Wife
- Nine Cats
- Previously Owned
- Dry Haul
- Bad Weather
- Burnt Coffee
- Silent Partner
- Paid Up
- Still Afloat
- Good Enough
- Two Weeks Late
- Nobody's Fault
- Half a Loaf
- Wet Paint
- Rough Passage
- Third Shift
- Overdue
- Off the Books
- Spare Parts
- Bilge Rat
- Mothballs
- Ballast
- Duty Roster
- Following Sea
- Slack Water
- Dead Reckoning
- Hard Aground
- Full Bunkers
- Quarterly Figures
- Consignment Eleven
- Asset 12-Calder
- Aurelia Consolidated
- Nightside Freight
- Serial K-1180
- Item Nineteen
- Depreciation
- Ready Deck
- Article 8802
- Grease Pencil
- Contract Vessel D-9
- Manifest Sixteen
- Bonded Cargo
- Lot 44-Brant
- Crane at Dusk
- First Snow
- Optimism
- In Theory
- Within Tolerance
- Reasonable Doubt
- My Other Ship
- Terms and Conditions
- Return to Sender
- Not My Problem
- Insurance Claim
- Somebody Else's Money
- Total Loss
## Theme

<!--
  The visual world the ship comes from, rolled once and honoured by every
  table that carries '@' tags. Same contract as the NPC file's own Theme
  table: a bullet here is a bare name, a tagged bullet elsewhere reads
  '|| mil @gundam', and a rolled theme opens its own tagged bullets plus every
  untagged one while excluding bullets tagged otherwise. ship_policy.py never
  reads a theme tag and says so in its own docstring: theme decides what a gun
  LOOKS like, the matrix decides whether the ship has one.

  The eight names are deliberately the NPC file's eight, unchanged, so a
  rolled ship and a rolled crew can be asked for the same look and mean the
  same thing by it.

  The discipline the tags need, stated once here because every tagged table in
  this file depends on it: a tagged bullet is UNREACHABLE from seven themes
  out of eight. So a pool whose only entry for some slot is tagged is an empty
  pool seven times in eight, and every (type, size) pair, every size band of
  every equipment table, needs an untagged bullet before it gets a tagged one.
  Tag only what is strongly of one look; most bullets stay neutral.

  The weights are NOT the NPC file's, and the difference is the point. Weight
  by how much SHIP art a look genuinely supports, which is a different
  question from how much clothing it supports - and check the tables actually
  carry that content before raising one:

    grimdark, neogothic - the most ship content of any theme here. Cathedral
      prows, flying buttresses, gilt statuary the height of a deck, votive
      banners kilometres long, soot and candle-smoke. Nearly every trait table
      in this file has something these two can take.
    gundam - named flagships, bridge towers, catapult decks, hard panel lining
      in white and primary colours. Deep on capital hulls, thinner on freight.
    tactical - grey, stencilled, utilitarian, no ornament. Supports any type
      at all, which is worth as much as depth.
    scav - welded patches, mismatched plate, hand-painted names, conduit run
      outside the hull. Excellent on small and working hulls, unconvincing on
      a battleship.
    corporate - liveried hulls, logo roundels, showroom finish. Strong on
      cargo and courier work, weak on anything that has been shot at.
    cyberpunk - cold industrial slabs and holographic markings. Real, but it
      overlaps corporate heavily and duplicating a look is not content.
    neosamurai - carried by two ship names and nothing else. It is a look
      built out of cloth, lacquer and blades, and a ship is none of those, so
      a rolled neosamurai ship renders as a neutral one with a name on it.
      Weight 1, and raise it only once there is hull, bridge or ornament
      content behind it - a lacquered bridge house is the cheapest place to
      start. Do not describe content this file does not contain.

  Raise a weight as you author into a theme; it needs no code change.
-->

- x6 grimdark
- x6 neogothic
- x6 gundam
- x5 tactical
- x5 scav
- x4 corporate
- x3 cyberpunk
- neosamurai
## Ship type

<!--
  What the vessel IS and what it is FOR, in that order, because the dossier
  prints this line under "Class" and the image prompt uses the same words. A
  bullet is a prose fragment, not a label: "a destroyer" alone tells a
  renderer nothing about what the hull should look like it does. Keep it to
  function and form. No backstory - "a battle it does not close with itself",
  "is not seen doing it" and "more engine than its papers admit" were all
  narrative a renderer cannot draw, and they have been rewritten.

  This bullet fills {ship} in both templates, mid-sentence, immediately after
  "A three-quarter view of" or "A top-down orthographic illustration of". So
  it must open with an article and a noun and read on from there without a
  full stop: "a fleet carrier, its hull built around ..." works, "Fleet
  carrier. Built around ..." does not.

  One physical line per bullet, flags included. parse_tables() in
  generate-npc.py matches a bullet with '^-\s+(.*?)\s*$' and matches
  continuation lines against nothing, so a wrapped bullet is truncated at its
  first line and loses its whole flag segment silently. Every bullet in every
  table in this file is therefore one line, however long; the '<!-- -->'
  blocks are the only thing here that wraps.

  Three flag groups, all read by the generator rather than by the prompt.

  The first is the TYPE flag - 'carrier', 'battleship', 'cruiser',
  'destroyer', 'patrol', 'stealth', 'recon', 'smuggler', 'cargo', 'support'.
  It is read by ship_type_of() in ship_policy.py and keys both SHIP_TYPES and
  EQUIPMENT_POLICY, so it is what gates equipment, and it is the whole reason
  this table carries flags at all: launch catapults exist to throw mechs off a
  deck and belong to 'carrier' first and to the largest 'battleship' hulls at
  a stretch. Nothing else has one - DEFAULT_EQUIPMENT_POLICY gives an unlisted
  type 'none' there, so a new type fails safe. A cargo hauler and a patrol
  boat carry minimal shielding, few weapons or none, and no catapult whatever
  their size rolls. Combat types earn armament in proportion to type and size
  together. test_ship_policy.py holds that every slug in SHIP_TYPES is carried
  by a live bullet here and that every bullet carries exactly one.

  The second is the SIZE BAND set - one or more of 'small medium large huge',
  naming which '## Size' bullets this type may roll. It is a whitelist, not a
  preference: a patrol boat is a patrol boat because it is small, and handing
  the pool back would produce a five-hex picket boat. Give a new type the
  narrowest honest set. Two bands is usually right; four means the type is
  doing too much and probably wants splitting.

  The band set here MUST equal SHIP_TYPES[slug]["sizes"] in ship_policy.py,
  exactly and in the same bands, and
  test_every_ship_type_bullets_bands_match_the_matrix() now holds it. It has
  already caught one drift: every cruiser bullet said 'medium large' while
  SHIP_TYPES has said 'medium large huge' since the cathedral hull was argued
  into the matrix, which quietly made the file's best capital-scale cruiser
  content unrollable. Change the module and these lines in the same commit.

  The third is the REGISTER flag, 'civ' or 'mil'. ship_policy.py does not read
  it on this table - _prefer_military() reads 'civ' on equipment bullets only
  - so it costs nothing here and is carried for the dossier, for the GUI's
  filtering, and so that a later filter has an honest axis to read. It is the
  same flag filter_by_mil() uses in generate-npc.py, unchanged in meaning:
  commissioned hardware against everything else. Two slugs are honestly both,
  and carry one bullet each way - a naval scout and a chartered survey hull
  are the same 'recon' row and look nothing alike, and so are a fleet tender
  and a yard tender.

  TWO BULLETS PER SLUG, minimum, and that is the point of the second ten. A
  type with one phrasing renders the identical opening clause every time it
  comes up, and 'cruiser' comes up more than any other row, so the repetition
  is loudest exactly where it is most visible. The pair must differ in more
  than a synonym: one leads on role, the other on the shape the role forces.

  AND THE PAIR MUST OPEN ON DIFFERENT CLASS NOUNS. {ship} splices immediately
  after "A three-quarter view of" or "A top-down orthographic illustration
  of", so the first three words of the bullet are the most visible words in
  the whole prompt, and a pair that opens "a battleship" twice has bought
  nothing for the slot the second bullet exists to vary. Eight of the ten
  slugs differentiated (fleet carrier / mech carrier, cruiser / heavy
  cruiser, patrol boat / patrol cutter, cargo ship / container hauler,
  support ship / yard tender, reconnaissance ship / survey ship, stealth ship
  / low-observable hull, smuggler's ship / runner); battleship and destroyer
  did not, and destroyer carries the joint-heaviest weight in the table, so
  the repetition landed on the most-rolled row. They are "a battleship" / "a
  dreadnought" and "a destroyer" / "a torpedo destroyer" now. Check the
  opening clause, not the flag, when a pair goes in.

  Weights aim at the fleet an actual campaign meets. Cruisers and destroyers
  are the working hulls and come up most; patrol boats, cargo and support
  ships are common because they are what a system is full of; battleships and
  carriers are rare on purpose, so rolling one still means something. Each new
  bullet carries the same xN as the bullet it partners, so adding the second
  ten doubled the pool without moving a single type's odds.
-->

- a fleet carrier, its hull built around a full-length flight deck with the mech wings ranked below it || carrier large huge mil
- a mech carrier, a blunt slab of a hull given over almost entirely to hangar volume, with a clear deck run down its dorsal spine || carrier large huge mil
- a battleship, a line-of-battle hull built to stand in the open and trade main-gun fire with its own kind || battleship large huge mil
- a dreadnought, gun houses stepped along a deeply belted hull with the whole forward third given over to the main battery || battleship large huge mil
- x4 a cruiser, the fleet's general-purpose heavy hull, sent out alone to hold a system for months at a time || cruiser medium large huge mil
- x4 a heavy cruiser, a self-sufficient warship hull with broadside batteries stepped the length of a long armoured flank || cruiser medium large huge mil
- x4 a destroyer, a fast escort built to screen larger hulls and run down anything smaller than itself || destroyer small medium mil
- x4 a torpedo destroyer, a narrow hull that is mostly engine room and tube room, built to hold station at the edge of a screen || destroyer small medium mil
- x3 a patrol boat, a short-endurance picket, all engine and hull codes, its stores racks stripped back to the frames || patrol small mil
- x3 a patrol cutter, a single-deck hull with a stencilled registry down the flank, a boarding ramp and endurance measured in days || patrol small mil
- x3 a cargo ship, a bulk hauler whose whole reason for existing is the tonnage racked along its spine || cargo medium large huge civ
- x3 a container hauler, a long open spine of stacked freight boxes with the crew and the drives bunched at either end || cargo medium large huge civ
- x2 a support ship, a tender rigged for repair, refuelling and resupply of hulls larger than itself || support medium large mil
- x2 a yard tender, a squat working hull hung with handling arms, hose reels and spare plate racked along the flank || support medium large civ
- x2 a reconnaissance ship, sensor masts and long-baseline optics carried on a hull built to run rather than fight || recon small medium mil
- x2 a survey ship, a light hull carrying more antenna than armour, optics blistered in a row along its dorsal line || recon small medium civ
- x2 a stealth ship, a signature-suppressed hull, flat-faceted and dark, built to be looked at and missed || stealth small medium mil
- x2 a low-observable hull, faceted flat across every surface with every fitting recessed flush into the plating || stealth small medium mil
- x2 a smuggler's ship, an honest freighter hull with concealed holds and far more engine than a hull that size should need || smuggler small medium civ
- x2 a runner, a plain freighter hull with oversized drive bells and a run of flank panels that do not match the plating around them || smuggler small medium civ
## Size

<!--
  How big the thing is, in terms a renderer can act on. Scale is the hardest
  thing to get out of an image model - a hull with no reference beside it
  renders the same size at every band - so every bullet NAMES A NUMBER, and
  then, at most, one comparison. "Vast" buys nothing.

  Naming the number is the '## Age' finding from docs/generate-npc.md,
  applied one table over: a bullet that describes a look instead of stating a
  figure is the part the model was measured ignoring, so it costs tokens and
  buys nothing. {size} has a 90-character budget in the prompt and every
  bullet here is inside it. The previous four bullets each ran to about a
  hundred and twenty characters because the number was followed by two
  clauses of surface description; the number and one reference is the whole
  bullet now.

  The reference, where there is one, must be to something OUTSIDE the frame's
  control - a house, a city block - or to something on the hull's own
  surface: a crew hatch, a ladder, a viewport row, an armour plate, a lifeboat
  pod. Three registers, and each band carries at least one of each, so a
  rolled band is not one sentence:

    LENGTH   - the plain figure, bow to stern.
    COMPLEMENT - how many people it is built around, EXPRESSED AS SOMETHING
      ON THE OUTSIDE OF THE HULL. A two-crew hull has one canopy and one
      hatch; a four-hundred-metre hull has lifeboat pods in ranks. A count of
      people is not drawable from any exterior shot, so it is the hatches,
      canopies, viewport rows and pod cradles that go in the bullet and never
      the number of berths behind them. An earlier draft had "several hundred
      aboard" and "about thirty berths aboard", which is the same failure as
      "thousands aboard" with a smaller number in it.
    COMPARISON - the figure restated against something outside the frame's
      control. ONE UNIT PER COMPARISON WORD, at one value: a city block is a
      hundred and thirty metres here and appears once, on the bullet that IS
      a hundred and thirty metres, because three bullets using the block at
      three different values (130 m, 90 m, 125 m) teaches a renderer nothing
      about scale except that the unit is meaningless. A house appears twice,
      both times at house scale.

  Two things this table must not do, both learned from the previous draft.

  It must not name what is around the ship. "Sat small against the station it
  is docked to" moors the hull, and '## Backdrop' owns the setting - most of
  that table is under way, in deep space, or in atmosphere, and every one of
  those rolls contradicted it outright.

  It must not name an interior. "A moving city with weather of its own in the
  upper galleries" is invisible from any exterior shot and put clouds and a
  gallery into a prompt whose subject is a hull.

  Two flags, and both matter downstream.

  The BAND flag - 'small', 'medium', 'large', 'huge' - is read by size_of() in
  ship_policy.py. It is what '## Ship type' whitelists against and what
  filter_by_size() gates equipment on: catapults, main-gun batteries and
  hangar decks need a hull to sit in. Exactly one per bullet; size_of() reads
  the first and ignores the rest.

  The HEX flag is the Foundry grid width of the finished token: 'hex1',
  'hex2', 'hex3', 'hex5'. NOTHING in ship_policy.py reads it - the widths live
  in SIZE_BANDS[band]["hexes"], which is 1, 2, 3, 5 - so a wrong value here
  fails silently in the VTT and nowhere else, which is why a test compares it
  against the band on the same bullet.

  On the ladder itself, because it is the first thing a reader will argue
  with: the hex widths are 1, 2, 3 and 5, and the metres below are not in that
  ratio. They cannot be. A battlemap footprint is an abstraction that has to
  stay playable at the top end, and SIZE_BANDS says so out loud - the jump
  from three hexes to five is deliberately not linear because the top band is
  the fleet carrier and the cathedral hull rather than "one bigger than
  large". What the prose owes the footprint is the ORDER and the SEPARATION:
  every band is clearly longer than the one below, no two bands overlap in
  metres, and the largest gap in the prose sits where the largest gap in the
  hexes sits. The ladder is small 30-60 m, medium 130-200 m, large
  360-500 m, huge 2-4 km, and the large-to-huge jump is the big one on
  purpose.

  IT ALSO OWES THE REST OF THE FILE AGREEMENT, and this is the harder half.
  {size} and {hull} land two clauses apart in the same prompt, so a number
  here is read against every length word anywhere else in the file. An
  earlier draft set huge at 1,000-1,500 m while '## Hull' still said
  "kilometres of soot-blackened flank", '## Launch catapult' said "a launch
  bay opened in the flank of a kilometres-long hull", and ship_policy.py's
  own SIZE_BANDS note reached for "a five-kilometre prow" and "kilometres of
  buttressed prow" to describe this band. Twelve hundred metres is not
  kilometres of anything, and the contradiction sat inside one sentence pair
  on every huge roll. The huge band is 2-4 km here for that reason: it is the
  smallest ladder on which every other length word in this file, and in the
  module, is literally true. Before moving a figure here, grep the file for
  "kilometre" and "metre" and move those with it.

  Four bullets per band, and the band is chosen before this table is rolled:
  '## Ship type' whitelists the bands and the generator narrows this pool to
  the one it picked, so a weight here would only pick between phrasings of the
  same number. There are none.
-->

- about forty metres bow to stern, a two-crew hull || small hex1
- sixty metres of hull, a single airlock and one crew hatch along the whole flank || small hex1
- under thirty metres, one welded ladder reaching from the landing foot to the spine || small hex1
- fifty-five metres long, two crew hatches and a boarding step let into the flank || small hex1
- a hundred and sixty metres bow to stern, four crew hatches spaced along the flank || medium hex2
- two hundred metres of hull, one viewport row reading as pinpricks along the flank || medium hex2
- a hundred and thirty metres, roughly the length of a city block || medium hex2
- a hundred and eighty metres prow to thruster bells, panel plates a few metres square || medium hex2
- four hundred metres bow to stern, lifeboat pods ranked in twos along both flanks || large hex3
- half a kilometre of hull, deck levels legible as banded window rows up the flank || large hex3
- three hundred and sixty metres, its bow hatch alone the size of a house || large hex3
- a four-hundred-and-fifty-metre hull, single armour plates the size of a house || large hex3
- two and a half kilometres bow to stern, lifeboat pods ranked in dozens || huge hex5
- three kilometres of hull, the flank a wall of stacked window rows and gantries || huge hex5
- four kilometres end to end, crew hatches too small along the flank to pick out singly || huge hex5
- two kilometres of hull, single armour plates as broad as a terrace of houses || huge hex5
## Faction

<!--
  Three segments: the affiliation NAME, its visual signature, then flags. The
  same shape the NPC file's Faction table uses, and deliberately the same
  NAMES wherever a faction plausibly owns hulls, so a rolled ship and a rolled
  crew can be given one affiliation and agree about what it looks like.

  The name is what the dossier prints. The visual is the only part that
  reaches the image prompt, and it must describe MARKINGS - insignia,
  stencilling, numerals, banners, pinstriping, patina, and the colour OF
  THOSE. It may not recoat the hull. '## Hull' has already painted
  the ship, and "imperial green with gold lining every panel edge" laid over
  "a gleaming white-and-blue container ship" is two coats of paint in one
  prompt; "gold lining picked out along every panel edge" composes with
  either. Never a hull shape either: that table owns the silhouette and will
  win the slot outright, exactly the way Outfit beat the old single-segment
  Faction bullets in the NPC file. If a visual you are writing would still
  make sense on a shuttle and on a battleship both, and would still make sense
  over any hull colour the other table can roll, it is at the right altitude.

  Keep a visual to NINETY CHARACTERS, about a dozen words, and measure it
  rather than eyeball it. The ship prompt rolls nine segments against the NPC
  prompt's slots and runs at the same 512-token ceiling, and this clause is
  one of the easiest to trim. The number is not invented: the sibling
  '## Faction' in npc-generator-tables.md runs a median of 80 characters and
  a maximum of 98 across its eleven visuals, so 90 is what the house style
  actually holds. An earlier draft of this table ran to 129 with eleven of
  its thirteen visuals over budget, every one of them by carrying a third
  clause about patina that '## Condition' rolls anyway. Two clauses about
  markings, stop; the wear is another table's.

  Say what IS on the plating, never what is missing. Generation runs at CFG
  1.0 with no negative prompt, so a noun named in order to forbid it gets
  drawn anyway - the lesson the NPC file's '## Stance' note records. "No
  livery at all" is how a shipbreaker's hull ends up liveried; "cutting scars
  and chalk survey marks" is the same fact, drawable.

  '|| palette' marks a faction asserting colours of its own. Those are PAINT,
  and they coexist with the Glow colour, which is LIGHT - the closing palette
  line softens from "the only saturated colour" to "the only other saturated
  colour" when one is rolled. A faction with no scheme should NOT carry it:
  the militia, the shipbreakers and the two non-affiliations leave the hull
  unconstrained on purpose.

  '|| civ' and '|| mil' are filter_by_mil()'s flags in generate-npc.py, reused
  unchanged in meaning - 'mil' is a commissioned warship's markings, 'civ' a
  working or commercial hull. Be warned that NOTHING READS THEM HERE YET:
  ship_policy.py reads 'civ' only inside the 'minimal' branch of
  filter_by_ship_policy(), and no hull-side filter exists, so today a
  battleship can roll a courier line's diamonds. That is row four of
  "Flags that still need a reader" in the file header, where it sits with
  '## Detail' and '## Markings' as one obligation on
  generate-spaceship.py rather than three separate intentions. The split is carried so the
  exclusion can be made explicit rather than incidental; a generator wiring it
  in should key on the rolled '## Ship type' slug - the four non-combat types
  (cargo, support, recon, smuggler) plus 'patrol' at a stretch drop 'mil', and
  the combat types drop 'civ'. Until that lands, this note describes an
  intention rather than a behaviour, and says so on purpose.

  '|| unaffiliated' marks the two entries that are NOT an affiliation. Their
  visual segment is empty because there is nothing to show, and the generator
  drops the clause rather than leaving a doubled comma - the same idiom the
  NPC file uses, and the same shape 'none' has in the equipment tables. It is
  a marker, so a filter can name the non-affiliations without matching on
  their prose; UNAFFILIATED_ROLES is what reads the NPC file's copy, and
  nothing reads this one yet. Exactly two bullets carry it, and a smuggler or
  a scav hull should reach them often.
-->

- x2 Unaligned || || civ unaffiliated
- Unregistered || || unaffiliated
- Union Administrative Department || a plain white departmental seal amidships and a long registry number stencilled down the flank || mil palette
- Harrison Armory || gold lining picked out along every panel edge and a gilt crest at the prow || mil palette
- Smith-Shimano Corpro || pale pastel accent bands over a polished finish, a small logo roundel set high on the prow || civ palette
- IPS-Northstar || cargo placards and a stencilled star roundel repeated down the flank, rust worn back at every edge || civ palette
- Karrakin Trade Baronies || heraldic quartering in deep crimson and gold across the flank, a house banner at the prow || mil palette
- House Clawthorne || a purple rabbit-skull crest painted huge amidships, votive charms wired along the hull rails || mil palette
- Sector Defence Flotilla || a broad orange identification band ringing the hull and black patrol numerals a deck high || mil palette
- Colonial militia || taped-over prior insignia showing through fresh grey patches, a hull number lettered on by hand || mil
- Meridian Shipping Combine || a broad blue cargo stripe down the flank, tonnage placards stencilled beside every hatch || civ palette
- Redstar Salvage || a red five-point star painted across the flank, its edges sun-bleached to pink || civ palette
- Diamond Line Couriers || faded yellow diamond markings at prow and stern, thin black pinstriping scoured to primer || civ palette
- Coldwater Shipbreakers || cutting scars, chalk survey marks and lot numbers scrawled across mismatched replacement plate || civ
## Hull

<!--
  One hull per bullet, rolled into a ship prompt the way `Outfit` rolls
  one garment.

  A LOWERCASE NOUN PHRASE WITH NO FULL STOP, and this is the first rule
  because an earlier draft of this table broke it on all thirty-five of
  its bullets. The slot is `The spacecraft's hull is {hull}, {detail}.`
  in both templates, so the value lands MID-SENTENCE and is used
  verbatim - a bullet written as a standalone sentence renders as "The
  spacecraft's hull is A colossal dark-blue fleet carrier, ... across
  the stern., a three-tier lattice mast ...", with a capital letter
  inside a clause and a doubled `., ` where the period met the comma, on
  one hundred per cent of rolls and in both images. Every other prose table in this file - Detail,
  Markings, Condition, Weapon, Shield generator, Launch catapult, Command
  bridge - is already written as a lowercase unterminated fragment for
  the same reason, and Hull was the only one that was not. Start with
  "a"/"an", end with the last word of the clause, and read it back inside
  the template before you commit it.

  DO NOT NAME THE CLASS. `{ship}` is rolled from '## Ship type' and lands
  eight words earlier in the same sentence - "A three-quarter view of a
  fleet carrier, ... The hull is a colossal dark-blue fleet carrier" says
  the type twice, and both prompts did that on every bullet in the
  earlier draft. This table owns COLOUR, PROPORTION AND FORM: "a colossal
  dark-blue slab hull broadening to a squared bow block". The class word
  is the other table's and the silhouette is this one's.

  NO DETAIL THAT ONLY MAKES SENSE ON WATER. This is the table that broke
  the renders: two bullets here asked for a surface warship outright -
  "a steel-grey hull on a wet-navy silhouette, a flared clipper bow above
  a recessed anchor housing" and "a painted waterline stripe running its
  whole length" - and krea2TurboInt8 gave back what they asked for, a
  present-day battleship floating in the sea. Both are rewritten
  ("dreadnought silhouette", "flared armoured bow above a recessed
  docking cradle", "a painted registry stripe"), and
  test/test_ship_spacecraft_register.py holds the rewrite over the live
  table so the next one cannot come back in silence.

  The line is narrow and it is about WATER, not about the naval register
  as a whole. The setting names its ships after wet-navy ones on purpose
  and this table leans on that: `prow`, `keel`, `stern`, `mast`, `flank`,
  `belted`, `barbette`, `casemate` and `ram bow` are all carried by live
  bullets and all read correctly on a starship, because science fiction
  has used them since it had ships at all. What is barred is the handful
  of details that describe a hull's relationship to a waterline and
  nothing else - a waterline stripe, an anchor or hawse pipe, a clipper
  bow, a gunwale, a bilge, draught marks, a bow wave. Those have no
  spacecraft reading to fall back on, and the templates cannot out-argue
  them: the sampler runs at CFG 1.0 with the negative conditioning zeroed
  out (see the "Never write a negation" section), so a prompt that names
  a waterline has named one.

  ONE PHYSICAL LINE PER BULLET, flags included, however long the line
  runs. parse_tables() in generate-npc.py matches a bullet with
  `^-\s+(.*?)\s*$` and matches continuation lines against nothing at all,
  so a wrapped bullet is silently truncated at its first line and loses
  its whole flag segment - a hull with no type and no size band, which
  every filter downstream then treats as neutral. The wrapping in
  `scene-and-spaceship-tables.md` gets away with it only because nothing
  parses that file. Wrap the comment block, never a bullet.

  SUBJECT ONLY. A bullet here describes the hull and nothing else -
  shape, proportion, plating, paint, surface wear, silhouette. No
  setting, no hangar, no planet, no other craft in frame, no weather, no
  time of day, and no lighting that belongs to a place. A separate
  Backdrop table supplies the scene and a separate Glow table supplies
  the accent light; a bullet carrying its own scene fights both of them
  and the render gets to pick which one it obeys. For the same reason,
  name engine hardware - nozzles, bells, exhaust slots, radiator fins -
  rather than the colour of anything glowing: the Glow roll owns that.

  The same division covers EQUIPMENT, and it is the rule this table gets
  wrong most easily. Weapon, Shield generator, Launch catapult and
  Command bridge each roll their own hardware under EQUIPMENT_POLICY in
  ship_policy.py, and several types are policy-bound to roll one - a
  carrier's bridge and catapult cells are both 'heavy', so a hull bullet
  naming a command tower and a catapult deck does not add them, it
  guarantees a second of each. Name where hardware GOES and let the
  equipment roll fill it: a bare barbette ring, a hardpoint pad, a
  recessed launch trench, an open deck recess, a casemate recess, a
  pintle ring. Engine hardware, radiator fins, cargo clamps, sensor booms
  and antenna masts are the hull's, because no table rolls those. The one
  standing exception is structure that IS the type's silhouette - a
  carrier's flat dorsal deck - and even then name the DECK and not the
  launch gear on it.

  THE BRIDGE IS THE HARDEST HALF OF THAT RULE, because a command tower
  looks like silhouette. It is not: '## Command bridge' is in
  ALWAYS_FITTED_TABLES, so every hull rolls one and there is no 'none'
  bullet to lose - a hull bullet naming a tower, a pilothouse, a
  blockhouse, a conning tower, a raised deck block or a cab puts TWO
  command structures on one ship, every time, with no roll that can take
  the second away. Five bullets in the earlier draft did it. Name the
  BASE and let the other table build on it: "a low pedestal block offset
  to one side of a flat dorsal run" is right, "a tiered command pedestal
  rising off the dorsal spine" is the bridge's job wearing the hull's
  clothes.

  Paint is the hull's; insignia is not. This bullet owns the coat -
  colour, panel blocking, lining, stripes, chalking, weathering, patches
  of resprayed primer. The Faction roll owns livery laid ON that coat:
  crests, roundels, registry numerals, unit codes, tonnage placards. Two
  tables both painting the whole hull is how a prompt ends up with two
  coats of paint arguing, so leave the numerals and the seal to the
  faction and spend the words on surface instead.

  NEVER WRITE A NEGATION. Generation runs at CFG 1.0 with no negative
  prompt - see the `## Stance` note in npc-generator-tables.md, where a
  rolled "raised ledge" put a visible platform under the figure and a
  second person on it. A noun named in order to forbid it gets drawn
  anyway, so "no turrets" is how a grain freighter ends up with turrets.
  Say it POSITIVELY instead: "bare mounting plates under the nose",
  "instrument bays where a warship carries gun decks", "cargo clamps at
  every hull station", "plating unbroken between the stencils". Describe
  the empty surface, not the absent gun. The absence is enforced by
  EQUIPMENT_POLICY, which already knows a hauler carries nothing; prose
  cannot help it and can only contradict it.

  `||` splits the bullet into prose and a final flag segment. Every
  bullet carries two required flags, may carry `palette`, and may carry a
  theme tag:

    - a TYPE, one of carrier battleship destroyer cruiser patrol stealth
      recon smuggler cargo support. These are the slugs of SHIP_TYPES in
      ship_policy.py; test_ship_policy.py fails on one the module does
      not define.
    - a SIZE BAND - small (one grid hex, a patrol boat or courier),
      medium (two), large (three), huge (five, a fleet carrier, a
      battleship or a cathedral hull). The bands a type may actually roll are
      sizes_for(slug) in ship_policy.py, and a (type, size) pair outside
      that list is a bullet no roll will ever reach. Check it before
      writing one: `carrier medium` and `patrol large` look plausible and
      are both dead.
    - optionally `palette`, meaning THIS COAT IS ALREADY A SATURATED
      COLOUR. The closing line of both prompts reads "with {glow} the only
      {other}saturated color in the frame", and {other} softens it to
      "only other" when the rolled '## Faction' carries `palette`. A hull
      painted orange-and-white, red-and-blue or mustard-yellow makes the
      unsoftened sentence a flat contradiction with a clause two sentences
      above it, so the eleven bullets below that assert a saturated coat
      carry the flag too. See "Flags that still need a reader" in the file
      header: generate-spaceship.py must OR this flag into the same test it
      runs on the Faction bullet. A grey, slate, olive, pewter, sand,
      charcoal, oxide-red or bronze-green hull is inside the restrained
      register the palette line names and does NOT carry it.
    - optionally one `@theme` tag, sharing the NPC generator's
      vocabulary: @gundam @tactical @neosamurai @cyberpunk @neogothic
      @grimdark @corporate @scav. ship_policy.py never reads these; theme
      decides what a hull LOOKS like, the matrix decides what it carries.

  EVERY LEGAL (type, size) PAIR NEEDS AT LEAST TWO UNTAGGED BULLETS, and
  the second one is not a nicety. A rolled theme opens its own tagged
  bullets plus every untagged one, so a slot whose only hull is tagged
  comes up empty under the other seven themes and a slot with no hull at
  all comes up empty under all eight - but a slot with exactly ONE hull is
  barely better, because {hull} is the longest rolled slot in either
  prompt and that whole type-and-size then renders the identical hull
  sentence forever. An earlier draft had nine of the twenty-one pairs
  pinned to exactly one bullet - carrier large, battleship large,
  destroyer small, stealth small, recon small, smuggler medium, cargo
  medium, cargo huge, support large - and twenty of twenty-one pinned to
  exactly one UNTAGGED bullet. Rolled end to end against '## Ship type's
  own weights, one hull sentence was 8.4% of every ship the generator
  would ever make. It is the same doctrine test_ship_policy.py applies to
  hardware in test_no_live_cell_is_pinned_to_one_piece_of_hardware - zero
  real answers or two, never exactly one - and a hull deserves it more
  than a turret does, not less. Twenty-one pairs are legal and all
  twenty-one carry two neutral hulls below. Write the two neutral ones
  first and a tagged one after, always in that order.

  Cruiser reaches `huge` - SHIP_TYPES says so, because the cathedral-scale
  hull is a cruiser at that size and not a battleship - so `cruiser huge`
  is a real cell and needs its two like every other.

  ON THEME TAGS: a theme has ZERO tagged hulls here or at least TWO, never
  exactly one. apply_theme_share() in generate-npc.py duplicates the
  tagged pool until it holds THEME_SHARE = 0.6 of the whole, so ONE tagged
  bullet becomes sixty per cent of every roll under that theme, while zero
  tagged bullets leaves the pool untouched and the theme simply renders
  neutral - which is what most of the sibling NPC file does, and it is
  fine. One is the only bad number. Eight themes, two hulls each, sixteen
  tagged bullets below. Tag only a hull strongly of one register.

  THE TYPE AND BAND FLAGS ARE A CONTRACT NOTHING ENFORCES YET, and that
  has to be said here because it is not visible from the file. '## Hull'
  is not one of ship_policy.EQUIPMENT_TABLES, so filter_by_ship_policy()
  does not apply to it; filter_by_size() reads only min-*/max-*, of which
  no bullet here carries any; and there is no filter_hull() in the module.
  Run today, filter_by_ship_policy(hull_options, 'patrol', 'small',
  'Hull') hands back all fifty-eight bullets and a one-hex patrol boat can
  roll a colossal fleet carrier. THE OBLIGATION IS THE GENERATOR'S:
  generate-spaceship.py MUST narrow '## Hull' to bullets whose flags
  contain both the rolled type slug and the rolled size band before it
  rolls this table, and must do that BEFORE the theme filter, for the
  reason design section 3 gives about policy running before theme. That is
  three lines, and it is the only reader these flags have or will have
  unless someone adds one to ship_policy.py, which this work may not edit.
  It is also a deviation from design section 2 row 7, which lists Hull's
  flags as civ/mil plus form flags plus @theme and names neither the type
  nor the band: the design's own section 3 makes the type-and-size pairing
  mandatory, these flags are how the pairing is expressed, and the parent
  should ratify the vocabulary rather than let it stand undeclared. There
  is no civ/mil flag on this table for the same reason there are no form
  flags - nothing reads it, and '## Ship type' already carries the
  register on a bullet the generator has in hand.

  BUDGET: 160 CHARACTERS OF PROSE, and measure it rather than eyeball it.
  {hull} appears in both prompts, and the token prompt is the longer of
  the two on real rolls, so a long hull bullet is charged twice. An
  earlier draft ran to 309 characters against a stated budget of 130 and
  was the single biggest reason the token prompt sat within a dozen tokens
  of the 512-token ceiling at p99. Colour, form, two or three structural
  clauses, stop.

  Evoke, never cite. No named vessel, faction or property from any
  published setting reaches a prompt, and no coined term from one either
  - describe the prow, the buttress, the welded patch, and let the shape
  do the work. Watch the combinations as well as the words: a handful of
  individually public-domain naval features can still add up to one
  famous hull, and when they do, drop the most identifying of them.
-->

- a long white-and-slate flat-decked hull, an unbroken dorsal deck laid the length of a slab body, hangar door recesses folded open along both flanks || carrier large
- a grey-green hull broad across the beam, a low pedestal block offset to one side of a flat dorsal run and four boxed engine housings ranked across the stern || carrier large
- a colossal dark-blue slab hull broadening to a squared bow block, a deep open deck recess cut the full length of each flank, ribbed radiator fins down the spine || carrier huge palette
- an immense pale grey hull built as one flat-topped wedge, deep launch trenches recessed into both flanks and six boxed engine housings across the stern || carrier huge
- a colossal white hull in red and blue panel blocking broken by hard black lining, a squared bow block, a low pedestal base and deep flank trenches || carrier huge @gundam palette
- a steel-grey hull on a dreadnought silhouette, a flared armoured bow above a recessed docking cradle and three stepped barbette rings on a raised centreline deck || battleship large
- a dark grey armoured hull with a long belted flank, riveted courses laid in overlapping bands and a painted registry stripe running its whole length || battleship large
- a grey slab-sided citadel hull, a broad flat foredeck stepping up amidships, belt armour banded its whole length and six engine bells across the stern || battleship huge
- a blue-black armoured hull built massively square, bare barbette rings ranked fore and aft on a raised deck and a stepped ram bow faced in angled plate || battleship huge
- a dark iron hull like a cathedral laid on its side, a ram prow crowned with gilt statuary, kilometres of soot-blackened flank pierced by casemate recesses || battleship huge @grimdark palette
- a dark bronze-green stepped wedge hull, prow armour laid in overlapping angled slabs to a blunt tip and a recessed spine trench running aft || cruiser medium
- a pewter-grey hull long and lean through the waist, armour plate stepping down both flanks and a broad radiator array fanned open across the stern || cruiser medium
- a hull lacquered black over hard-edged plate, its prow swept up like a raised blade, a broad enamelled band inlaid amidships and slatted vanes at the stern || cruiser medium @neosamurai
- a grey hull built long and narrow on a triple-keel frame, three parallel tubes braced by ring frames with open bays standing between them || cruiser large
- a slate hull with a squared prow block and a long raised shoulder deck, bare hardpoint pads spaced the length of each flank and clustered exhaust nozzles aft || cruiser large
- a vast bronze-and-bone hull, a cathedral prow of arched windows and carved figures, buttresses climbing a long spine and gilt filigree over blackened plating || cruiser large @neogothic palette
- a soot-blackened iron hull with a blunt riveted ram prow, a low spine of arched galleries stepping aft and iron-grated exhaust throats ranked across the stern || cruiser large @grimdark
- a vast pewter-grey armoured wedge hull with a stepped spinal ridge, bare barbette rings on a raised centreline deck and deep casemate recesses down both flanks || cruiser huge
- a colossal oxide-red hull built as one armoured slab, its prow faced in overlapping angled courses and ribbed radiator strakes stepping down the spine || cruiser huge
- a compact slate-blue hull, a single tapered fuselage with a fat engine block filling the aft third and short strake fins standing off the flanks || destroyer small
- a dull olive hull, a narrow tube with a shallow armoured ridge down the spine, a blunt capped nose and weathering streaked back from every panel joint || destroyer small
- a graphite hull with lacquered scarlet panels let into the shoulders, a raked prow edge and a fan of slatted vanes standing at the stern || destroyer small @neosamurai palette
- a lean dark-grey hull, a narrow knife of a body with a raked bow, a low spine ridge running back to four clustered engine bells || destroyer medium
- a chalky grey-brown hull with a long slab flank, bare hardpoint pads set flush into the shoulders and a wide-mouthed exhaust cluster aft || destroyer medium
- a white hull with hard-edged panel lining and blue and red blocking across the shoulders, bare turret rings set on the dorsal line || destroyer medium @gundam palette
- a narrow black hull with a bladed ram prow, cliff-like buttressed flanks stepping up to a spired stern tier and small arched recesses lining the sides || destroyer medium @neogothic
- a compact orange-and-white hull, a rounded fuselage tapering to a blunt sensor nose and a bare pintle ring seated in the dorsal plating || patrol small palette
- a stubby olive-drab hull, a flat wedge body with a low armoured well sunk into the bow and bare mounting plates under the nose || patrol small
- a stubby grey hull, a flat wedge body with hazard striping ringing the airlock hatch and plain plating unbroken between the stencils || patrol small @tactical
- a faceted matte-black hull, every surface angled flat to break its silhouette, a blank nose and lamp housings faired flush into the skin || stealth small
- a charcoal hull raked to a single angle across every panel, shrouded exhaust slots sunk along the tail, the finish a dead flat matte that swallows light || stealth small
- a dark grey-green slab-sided hull with knife-edged chines, flush-skinned bay covers laid along the belly and exhaust slots let into the tail root || stealth medium
- a graphite hull built of flat facets with every seam raked to one angle, a folded sensor blade tucked into a spine channel and every fitting recessed || stealth medium
- a charcoal slab-sided hull with knife-edged chines, holographic markings drifting faintly across otherwise unbroken plating and bay covers retracted flush || stealth medium @cyberpunk
- a slender white hull, a needle nose carrying a cluster of forward probe booms, a small observation blister under the belly and instrument pods along the flanks || recon small
- a pale sand hull, a long thin body with two antenna booms outrigged from its sides and a flat instrument deck let into the spine || recon small
- a pale grey flattened hull crowded with phased-array panels and mast-mounted domes, cable runs and instrument bays taking up both flanks || recon medium
- a chalky white hull with a shallow slab body, optics blisters ranked along the dorsal line and a slim engine section faired into the tail || recon medium
- a drab olive flattened hull, low-visibility paint gone chalky across the flanks and bare hardpoint rails running the length of the spine || recon medium @tactical
- a dull brown-and-cream hull, a stubby fuselage with an oversized engine block faired in behind the cabin and a smooth belly pod slung under the keel || smuggler small
- a grey hull sanded back and resprayed in mismatched patches, a short deep body with a flush hatch seam cut into the underside || smuggler small
- a battered rust-and-teal hull, mismatched plates welded on in patches over a stubby cargo pod belly and exposed conduit strapped along the spine || smuggler small @scav palette
- a nondescript brown hull with a broad flat belly and two stubby engine pods on outrigger pylons, a wide bow ramp and a cabin blister offset to one side || smuggler medium
- a dust-grey hull with oversized drive bells, plating patchy where old paint was sanded back and a run of flank panels that do not match || smuggler medium
- a black hull under a wet gloss finish, thin lit data strips let into the panel seams and a long flush access run down the spine || smuggler medium @cyberpunk
- a sand-and-olive hull built as an open equipment frame, cargo modules bolted into the bays between its ribs and hydraulic rams left exposed along the spine || cargo medium
- a rust-brown hull, a short blunt body with a squared cargo section amidships, thin unarmoured plating over the crew block and cargo clamps at every station || cargo medium
- a pale blue-grey hull, a smooth bow fairing capping a long ribbed cargo spine with container stacks locked in matched rows along it || cargo large
- a weathered grey hull, a bare girder spine strung with cylindrical tanks and a squat engine block faired into the stern || cargo large
- a gleaming white-and-blue hull, a smooth bow fairing capping a long ribbed cargo spine, the plating polished to a showroom finish || cargo large @corporate palette
- a colossal ochre-and-black hull, a bare girder spine strung with dozens of tanks and stacked container racks and an enormous engine block at the stern || cargo huge palette
- an immense slate-grey hull, kilometres of open rack frame with a small pressurised crew module perched forward and cargo clamps at every hull station || cargo huge
- a pale grey barrel hull ringed with machinery bays and access hatches, articulated grapple arms folded flat against its flanks and scorched paint aft || support medium
- a dull green hull, a short deep body hung with hose reels and spare plate racked along the flank and bare stanchion sockets ranked along the rail || support medium
- a squat mustard-yellow hull bristling with work gear, four articulated grapple arms folded against a barrel body and welding rigs lashed to external racks || support medium @scav palette
- a clean white hull banded with grey machinery bays and hard black panel lining, replenishment booms folded along both flanks || support large
- a pale olive service hull, a long slab body with smooth plating running unbroken between ranked service bays and a squared exhaust block at the stern || support large
- a pearl-grey hull with pale accent banding along the shoulder line, every seam faired flat and service bay covers seated flush into the plating || support large @corporate
## Detail

<!--
  One piece of hardware standing off the hull, rolled after '## Hull'
  and dropped into the same sentence: "The hull is {hull}, {detail}." So a
  bullet is a LOWERCASE NOUN PHRASE that reads as one more item in the
  comma list the hull bullet already is - "a folded boarding arm stowed
  flat along the flank" - and never an independent clause, never a verb
  the ship is doing, never a sentence of its own. This is the '## Feature'
  analogue in the NPC file: one distinguishing mark, not a second hull.

  ONE PHYSICAL LINE PER BULLET, flags included, however long the line
  runs. parse_tables() in generate-npc.py matches a bullet with
  `^-\s+(.*?)\s*$` and matches continuation lines against nothing at all,
  so a wrapped bullet is silently truncated at its first line and loses
  its whole flag segment. Wrap this comment block freely; never a bullet.

  ADD SOMETHING THE HULL DID NOT, and re-read '## Hull' AT BULLET LEVEL
  before adding one - not the summary in this paragraph, which is how the
  collisions got in last time. As that table stands it names: fixed
  radiator fins, strakes and arrays, probe booms, antenna booms,
  phased-array panels, mast-mounted domes, optics blisters, instrument
  pods and decks, a folded sensor blade, cargo clamps, container racks and
  stacks, exposed conduit, hydraulic rams, engine bells, nozzles, housings
  and exhaust throats, grapple arms, replenishment booms, hose reels,
  spare plate, bare stanchion sockets and a workshop bay. Restating one of
  those does not add a detail, it doubles a noun the renderer has already
  placed. An earlier pair of drafts collided on four - a folding dish
  against a gimballed dish, a bow docking collar against a docking arm,
  roll-bar handrails against grab handles, engine nozzles against vernier
  housings - because this table was written against a summary of that one.

  What is left over is this table's, and it is a lot: masts that
  telescope, dishes on gimbals, umbilical and refuelling ports, tow eyes
  and mooring gear, drop tanks, attitude thrusters, solar wings, escape
  pod cradles, EVA rails and grab handles, crawlway rails and the machine
  that rides them, boarding arms and ramps, louvre banks, derricks,
  winches, signal lamps, screens and boss plates. Where a noun is
  unavoidably near a hull noun, make the difference the point: the hull's
  radiator fins are fixed to the plating, so a radiator here STANDS OFF it
  on stalks or folds. And check this table against ITSELF as well - a
  crawlway rail with a trolley on it and crawler rails on stanchions were
  one fitting written twice, and the second is an engine-section
  inspection hatch now.

  NEVER NAME A WEAPON, A SHIELD, A CATAPULT OR A BRIDGE. Those are four
  separate tables, each rolled under EQUIPMENT_POLICY in ship_policy.py,
  and several types are policy-bound to roll one while others are locked
  out of it entirely. A gun named here does not arm a freighter the matrix
  has disarmed on purpose - it gives the render a gun the matrix cannot
  see and cannot take away; a bridge named here gives a hull two of them.
  So no turret, mount, barbette, missile cell, torpedo tube, launch rail,
  flight deck, blast trench, emitter, projector node, field shimmer,
  ablative course, canopy, pilothouse, conning tower or command block.
  Sensor masts, comms dishes, radiators, docking and tow gear, tankage and
  crew fittings are safe because no other table rolls them.

  SUBJECT ONLY, and no state. No hangar, no planet, no other craft, no
  weather, no time of day, and nothing the ship is in the middle of doing.
  '## Backdrop' owns the setting and '## Glow placement' owns the
  accent light. "a docking arm reaching for the collar" moors the hull;
  "a folded docking arm stowed flat along the flank" reads under way, in
  dock and on a plain white token alike, which is what this table needs.

  NEVER WRITE A NEGATION. Generation runs at CFG 1.0 with no negative
  prompt - the '## Stance' note in npc-generator-tables.md records what
  that costs - so a noun named in order to forbid it gets drawn anyway.
  Describe the empty surface, never the absent fitting: "bare stanchion
  sockets along the rail", not "no mast fitted".

  Two flags, both optional, plus a theme tag.

    civ / mil are filter_by_mil()'s flags in generate-npc.py, unchanged in
    meaning: 'mil' is warship fitting-out, 'civ' a working or commercial
    hull's. NOTHING CALLS THAT FILTER ON THIS TABLE YET - see "Flags that
    still need a reader" in the file header, which lists it as an
    obligation on generate-spaceship.py along with '## Faction' and
    '## Markings'. Until it lands, a battleship can roll the passenger
    boarding sleeve and the solar wings; sixteen of the forty-eight bullets
    below are flagged and they are inert. An UNFLAGGED bullet is neutral
    and reachable either way, and most bullets here are and must stay that
    way - the filter ends `plain or options` and hands the pool back rather
    than roll nothing, but a table flagged all the way down would swing the
    whole look of a ship on one bit. Flag only what would read as an error
    on the other kind of hull: a rappel-line boarding ramp, a passenger
    boarding sleeve.

    One optional @theme tag, from the eight the '## Theme' table rolls.
    Detail is one of the FIVE themed tables - Hull, Detail, Weapon,
    Command bridge, Backdrop - and the only place in this table a tag may
    appear is the flag segment after '||', where split_flags() strips it.
    A tagged bullet is unreachable from seven themes out of eight, so tag
    only what is strongly of one look and let the neutral pool carry the
    table. Thirty-two of the forty-eight here are neutral.

    ZERO TAGGED BULLETS PER THEME OR AT LEAST TWO, NEVER EXACTLY ONE.
    apply_theme_share() in generate-npc.py duplicates the tagged pool
    until it holds THEME_SHARE = 0.6 of the whole, computed as n =
    ceil(share * neutral / ((1 - share) * tagged)) copies. With one tagged
    bullet that arithmetic makes THAT ONE BULLET sixty per cent of every
    roll under that theme; with two it is thirty; with none the function
    returns the pool untouched and the theme renders neutral, which is
    what most of the sibling NPC file does and is perfectly fine. An
    earlier draft carried exactly one tag for every one of the eight
    themes - the worst possible arrangement, and the only table in the
    file to hit it on all eight - so sixty per cent of all Detail rolls
    came back the same bullet no matter which theme was rolled. Two each
    now, sixteen tagged. When a theme cannot honestly earn a second one,
    take its first one off rather than leave it alone.

  NO FORM FLAGS, deliberately, and this is a decision rather than an
  omission. The design lists a form vocabulary (twinboom, discspine,
  slabside, deltawing, obelisk, flatdeck) for Hull and Detail both, and
  '## Hull' as authored carries none of them. A form flag here that
  no hull can satisfy is inert under a preference filter and fatal under a
  hard one - the bullet is simply unreachable - so every bullet in this
  table is written to compose with any silhouette instead, which is the
  right altitude for a twelve-word clause anyway. If form flags are wanted
  later, they go onto both tables in one pass, hull first.

  LIGHT IS A SIDE EFFECT HERE AND A DELIBERATE ONE. has_light_source() in
  generate-npc.py scans this table's text along with the hull and the
  equipment, and 'beacons', 'strobes', 'readouts', 'flares' and 'glow*'
  are in EMITTER_WORDS - so a lit detail is what turns the glow sentence
  on for a hull whose equipment rolled dark. Two bullets do that on
  purpose. NEVER NAME A HUE NEXT TO ONE: light_hues() binds a colour word
  within twenty-four characters of a light word and constrains the whole
  '## Glow colour' roll to that family. "beacon strobes on short posts" is
  right; "amber beacon strobes" quietly decides the ship's only saturated
  colour for it.

  ABOUT TWELVE WORDS, ninety characters of prose at the outside. The
  '{detail}' slot is budgeted at 90 chars in the prompt design and it sits
  in a prompt already carrying a hull, an armament sentence, a bridge, a
  faction visual, markings, a condition, a backdrop and a glow line
  against a 512-token ceiling. One fitting, one clause about it, stop.

  Evoke, never cite. No named vessel, faction or property reaches a
  prompt, and no coined term from one either. Watch the combinations as
  well as the words - a few individually ordinary fittings can still add
  up to one famous hull, and when they do, drop the most identifying.
-->

- a retractable sensor mast telescoped up off the spine in a braced collar
- a mesh comms dish on a two-axis gimbal, its face angled off the beam
- a pair of star-tracker heads on short stalks either side of the nose
- whip antennae raked back in a row along the dorsal line, thin as wire
- an umbilical port let into the flank, its cover swung back on a hinge || civ
- tow eyes forged into the bow frame, the paint scrubbed off them to bare metal
- a crawlway rail tracking the length of the hull, a hand trolley parked on it
- a maintenance walker folded onto its rail bracket amidships
- drop tanks slung on stub pylons under each shoulder, fill caps chained shut
- attitude thruster quads clustered at the shoulders and at the tail root
- deployed radiator panels standing off the spine on stalks, turned edge-on
- a mooring bollard and capstan set into the deck behind the bow lip || civ
- inspection lamps on gooseneck arms bent over every access panel
- beacon strobes on short posts at the extremities, blinking out of step
- an EVA tether rail running from the airlock ring back along the spine
- grab handles and toe rails stitched across the plating around every hatch
- a docking arm folded flat along the flank, its collar capped
- escape pod cradles ranked along the flank, their hatch rings standing proud
- a magnetometer boom outrigged far off the hull on an open lattice spar
- a heat-exchanger louvre bank let into the flank, its vanes stepped open
- a refuelling drogue reel faired into the belly behind a hinged door || mil
- a cargo derrick folded down along the spine, its hook stowed in a cradle || civ
- a hinged inspection hatch standing open on the engine section, its stay rod propped
- a solar wing folded in accordion pleats against the flank, hinged at the root
- solar wings outspread on a rotating boom, their cells crazed by dust strikes || civ
- a passenger boarding sleeve stowed in a flush recess, its bellows folded flat || civ
- cargo webbing lashed down over the dorsal racks and cinched at every rib || civ
- a push pad faced in scarred buffer plate across the stern quarter || civ
- spare atmosphere bottles racked in a caged frame beside the airlock || civ
- a signal lamp housing on a short yard, its shutter blades stacked open || mil
- a three-tier lattice mast carrying dipole rings at every level || mil
- a boarding ramp folded against the flank, rappel lines coiled at its head || mil
- a folded manipulator arm racked flat against the flank, its joints hard-lined || @gundam
- a squared sensor block seated on the spine, its faces divided by hard panel lines || @gundam
- a stabilised camera head on a short mast, its lens hood squared off || mil @tactical
- a hand-crank cable winch bolted to the deck lip, its drum wound with steel line || mil @tactical
- relay boxes clipped up a data mast in stacks, cable bundles strapped between them || @cyberpunk
- a flat panel screen bolted to the flank, its face scrolling and dim || @cyberpunk
- a brass orrery armature turning slowly on a pylon set into the spine || @neogothic
- a bell yoke mounted on the spine, its bell hung in a wrought iron cradle || @neogothic
- an incinerator stack standing off the spine on braced legs, its throat crusted black || @grimdark
- a riveted iron mask boss bolted over the forward frame, streaked with soot || @grimdark
- salvaged tanks strapped into a cradle of rebar welded on beside the hatch || civ @scav
- a mismatched aerial wired to a length of pipe clamped upright at the stern rail || civ @scav
- a courtesy handrail run in polished trim from the airlock forward to the nose || civ @corporate
- a flush service panel set with a small maker's plate, the seam faired invisible || civ @corporate
- a fan-shaped radiator vane lacquered on its outer face, folded flat at the spine || @neosamurai
- a paper-thin banner blade standing off the spine on a single lacquered staff || @neosamurai
## Weapon

<!--
  What is visibly bolted to the hull. The Weapon, Shield generator and
  Launch catapult rolls are joined into ONE sentence by
  armament_sentence() in ship_policy.py - "The hull carries {weapon},
  {shield} and {catapult}." - so every bullet has to read correctly as
  something a hull CARRIES, and it is a noun phrase naming hardware a
  renderer can draw: barrels, cell hatches, turret drums, muzzle
  apertures, blast staining. Never a capability and never a rating.
  "Heavy anti-ship firepower" draws nothing; "four long barrels in a
  slab-armoured box" draws a turret. "Civilian rated", "otherwise
  unarmed" and "plainly an afterthought" draw nothing either - they are
  judgements about the SHIP, and the ship's posture is the type's
  business, not the mount's.

  Wear is fine. Blast staining, scorched cell lips, blistered paint are
  surface texture and read on any hull, docked or under way. STATE is
  not: "hatches blown open", "as it charges", "answering the fire" put
  the ship mid-engagement, and the Backdrop roll is what decides
  whether it is in one.

  Name the hardware, never the colour of the light it makes and never
  the colour of the hull it sits on. "{glow} glow" is a separate roll
  and the palette line calls it the only saturated colour in the frame;
  the hull's paint belongs to '## Hull' and its markings to
  '## Faction', and a white turret named here fights both.

  Flags, and this is the vocabulary all four equipment tables share:

    min-small / min-medium / min-large / min-huge
      the size floor - the smallest hull this hardware plausibly fits
      on. A chin turret is min-small, a spinal lance is min-huge. Read
      by filter_by_size() in ship_policy.py, which is a HARD filter and
      does not hand the pool back when it narrows, so a floor set one
      band too high quietly empties a slot.

    max-small / max-medium / max-large
      the scale cap, for hardware that reads as too slight for a bigger
      hull. One light autocannon on a five-hex battleship looks like an
      error rather than an armament. Most bullets need no cap, and a
      bullet with a min-small floor and no cap at all is NEUTRAL:
      size_bounds() returns (0,3) and every hull reaches it. That
      neutral pool is what makes the size filter safe to run hard,
      because it cannot empty, and
      test_every_equipment_table_carries_neutral_bullets asks this
      table for at least three. Do not cap a small mount that would
      read fine on a capital hull as a secondary battery - that is what
      thinned the pool to one in the first draft.

    mil
      warship-issue hardware. This flag was called 'combat' in the
      first draft, which collided with the scene gate of the same name
      in '## Backdrop' and '## Glow placement'. Nothing filters on
      'mil' today: a non-combat hull is kept off it by the 'minimal'
      policy in EQUIPMENT_POLICY, which admits only 'civ' and the empty
      bullet. It is carried so that exclusion is explicit rather than
      incidental, and it is what test_ship_policy.py asserts never
      reaches a minimal hull.

    civ
      hardware that reads mercantile - a merchantman's token turret, a
      debris-burning defence laser, a cannon lashed to a hauler's spine
      by her own crew. This is the entire pool a 'minimal' hull has, so
      it has to hold real answers at EVERY band: three of these carry
      no max cap for exactly that reason. Cap them all at max-medium
      and every armed freighter in the fleet ends up with the same
      docking laser.

    none
      the empty bullet. It parses to no text and contributes no weapon
      phrase at all, and it carries the marker flag rather than the
      word "none" in its prose, so a filter can name the empty bullet
      without matching on text - the same idiom the NPC Weapon table
      uses. It carries a nominal min-small floor so the size filter
      never has to special-case it, and it carries NO WEIGHT:
      MINIMAL_NONE_COPIES already stacks it for the hulls that should
      usually be unarmed, and weighting it here would also thin out the
      patrol boats and the stealth hulls, which are warships.

  A new bullet must set its floor honestly: ask what the smallest hull
  could physically carry the thing, and flag that, not the hull you had
  in mind while writing it. Do not assume a hull SHAPE either - wings,
  a fuselage, a cockpit, cargo clamps - because '## Hull' rolls
  slabs, spines and girder frames as often as anything with a nose.
  Theme tags are for armament strongly of one look - engraved brass
  cowls, hard-lined panelled housings - and most bullets stay untagged
  so every theme can reach them. TWO PER THEME OR NONE, NEVER ONE:
  apply_theme_share() duplicates a theme's tagged bullets to sixty per
  cent of the pool, so a single tagged weapon is the same gun on three
  rolls in five under that theme, while zero tagged weapons leaves the
  pool alone and the theme arms from the neutral twenty-three. An earlier
  draft ran corporate and neosamurai at zero and cyberpunk at one; the
  pairs below are a compliance module and a faired defence pod for
  corporate, a lacquered cannon and scaled launch cells for neosamurai,
  and a clamped rail mount beside the holographic-status turret blocks for
  cyberpunk. Sixteen tagged of forty.
-->

- || none min-small
- a pair of stub torpedo tubes let into the belly either side of the keel, their muzzle caps hinged back and the plating scoured bare around each opening || min-small max-medium mil
- a lone glazed ball turret set behind the bridge, swivelled off to one side with its barrels depressed || min-small max-medium mil
- two stub pylons braced against the hull shoulders and hung with slim missile pods, their nose caps painted in warning stripes || min-small max-medium mil
- two fixed forward guns set into the leading edges of the hull, blast staining smeared back across the plating from the muzzles || min-small mil
- a rotary cannon slung under the nose on a powered chin mount, its ammunition feed running back into the hull in an armoured conduit || min-small mil
- a slim rail mount clamped along the dorsal line, its power trunking taped in a bundled run and tagged at every joint || min-small mil @cyberpunk
- a retractable turret ring flush with the upper hull, barrels folded down into their well and the cover plates seated almost seamlessly || min-small mil
- paired launch cells faced in overlapping lacquered scales, their hatch lips edged in worked metal and a crest set between them || min-small max-medium mil @neosamurai
- a pair of small gun blisters set into the hull shoulders, each a low armoured dome with a single stubby barrel standing out of it || min-small mil
- a small turret bolted to the spine well aft on a welded pedestal, its cabling run outside the hull to a junction box beside the mount || min-small max-medium civ
- a compliance turret module seated flush in the upper hull, its housing panelled to match the plating and a small maker's plate bolted beside it || min-small max-medium civ @corporate
- an elderly deck gun on a hand-cranked mount bolted to the dorsal plating, its barrel wrapped against vacuum in taped sheeting || min-small max-medium civ @scav
- a mining laser rerigged as armament, its emitter head clamped in a swivel cradle on a stub crane boom and the coolant lines taped along the jib || min-small max-medium civ @scav
- a pair of squat point-defence drums mounted fore and aft on the dorsal line, short barrels and open ammunition lockers bolted beside each mount || min-small civ
- a defence pod on a neat retracting pylon, its casing faired to the hull line and every fastener capped flush || min-small civ @corporate
- a gimballed defence laser array ringing the forward hull, small lens heads on stubby posts angled out and up || min-medium civ
- a lone heavy autocannon on a pintle mount above the main hatch, its ammunition boxes stacked and strapped down around the mount ring || min-medium civ
- an escort mount left bolted to the dorsal deck, its cradle empty and its cabling capped off at a junction box beside it || min-large civ
- a row of point-defence turrets spaced along the dorsal spine, each a small armoured drum with paired stub barrels || min-medium mil
- flush vertical launch cells set in blocks into the upper hull, hatch covers stencilled with cell numbers and scorched at the lips || min-medium mil @tactical
- two heavy beam projectors in sponsons either side of the hull, cooling fins ribbing their housings and frost feathering the intakes || min-medium mil
- a twin-barrel main turret amidships, the barrels long enough to overhang the hull edge fore and aft || min-medium mil
- a long-barrelled cannon in a lacquered housing, an enamelled crest set on its cheek plate and its cradle wrapped in braided cord || min-medium mil @neosamurai
- torpedo apertures ranked low in the prow, heavy armoured shutters closed across them and the paint blistered around each opening || min-medium mil
- a hexagonal cluster of missile cells amidships, hatch covers seated flush and stencilled with cell numbers || min-medium mil
- hard-lined turret housings ranked along the hull shoulders in the hull's own trim, sharp panel lines dividing them from the plating || min-medium mil @gundam
- a swivel-mounted particle cannon on a raised dorsal barbette, thick power trunking running back from it along the spine || min-medium mil
- stencilled gun tubs stepped in tiers along the flank, each ringed by a low splinter shield with its number painted on the shield face || min-medium mil @tactical
- slab-sided turret blocks along the dorsal line, holographic status markings hanging in the air beside each mount || min-medium mil @cyberpunk
- a rank of reliquary turrets along the spine, each barrel sleeved in engraved brass and shrouded by a hinged iron cowl worked into a praying figure || min-medium mil @neogothic
- broadside gun decks running most of the hull length, three tiers of casemate ports standing open along the flank || min-large mil
- quadruple turret barbettes ranked along the centreline, each a slab-armoured box with its long barrels laid out level || min-large mil
- a heavy dorsal battery of paired guns in stepped turrets, superfiring one above the other toward the prow || min-large mil @tactical
- a rotating drum battery amidships, four short-barrelled mortars ranked around its face and an armoured hoist trunk feeding it from the deck below || min-large mil
- a spinal cannon muzzle set into the prow on the centreline, its aperture ringed by hard-edged blast collars and a band of trim striping || min-large mil @gundam
- a broadside of long beam lances seated in individual armoured sleeves, their emitter heads glowing dull along the flank || min-large mil @grimdark
- a spinal mass driver running the ship's entire length, its muzzle a single vast aperture set into the prow between blast shutters || min-huge mil
- a prow-mounted particle lance cradled in a lattice of exposed conductor rings, heavy bus bars strapped between them and ceramic standoffs at every joint || min-huge mil @grimdark
- gun batteries stacked a dozen casemate tiers high, muzzles jutting between flying buttresses and soot-black statuary || min-huge mil @neogothic
## Shield generator

<!--
  The visible shielding hardware and what it does to the light around
  the hull. It lands in the same sentence as the Weapon and Launch
  catapult rolls - "The hull carries {weapon}, {shield} and
  {catapult}." - so a bullet has to read as something the hull CARRIES:
  an emitter ring, a belt of blisters, scales of ablative plate. Not a
  protection rating. A renderer can draw an emitter ring, a shimmer, a
  crawling arc; it cannot draw "resilient".

  Half these bullets are dark, dormant or bare plating on purpose,
  because a hull with no field showing is the common case and a visible
  envelope on every ship would flatten the whole table.

  Name the hardware and the effect, never the hue. A blue skin of light
  clinging to the plating is a second saturated colour arguing with the
  "{glow} glow" roll, and the palette line claims that roll is the only
  one in the frame.

  Flags are the shared set the '## Weapon' comment documents in full: a
  size floor on every bullet, read by filter_by_size(); an optional max
  cap; 'mil' for hardware only a warship carries; 'civ' for hardware a
  merchantman carries; and the 'none' marker on the empty bullet.

  THIS TABLE IS NOT THEMED, and an earlier draft carried seven '@' tags
  here that did nothing at all. THEMED_TABLES is Hull, Detail, Weapon,
  Command bridge and Backdrop - five and only five - and
  filter_by_theme() never looks at a table outside that list, so a tag
  here is stripped into the flag segment and silently ignored. That is
  the '## Gear' argument from npc-generator-tables.md: an emitter ring is
  not theme-defining, and a tag that fails quietly is worse than one that
  fails loudly. All seven bullets are still here; only the tags are gone,
  and losing them WIDENED the pool, because a tagged bullet is
  unreachable from seven themes out of eight. Adding this table to
  THEMED_TABLES means editing test_ship_theme.py's pinned list first.

  STRIPPING A TAG IS HALF THE JOB; THE PROSE HAS TO COME WITH IT. A bullet
  written to be gated is written to be seen by one theme, and taking the
  gate off without touching the words makes it reachable from all eight -
  which is how a corporate showroom container ship came to be able to roll
  a censer-hung array breathing along the gothic ribs of the hull. Three
  bullets here were rewritten to neutral for that reason: the censer array
  is a heavy array hung with counterweights between the prow fittings, the
  corporate-liveried housings are neatly faired housings, and the iron
  reliquary emitters are heavy iron emitters. A fourth was asserting hull
  shape it had no right to - "along the hull's ribs and towers beneath it",
  when the ribs belong to two hull bullets in fifty-eight and the tower is
  '## Command bridge's roll - and reads "across the plating beneath it"
  now. Neutral prose is the price of a wide pool; if a bullet cannot pay
  it, it wants a tag and a themed table, not a strip.

  The 'civ' flags here are load-bearing rather than decorative. Cargo
  and smuggler hulls run 'minimal' on this column in EQUIPMENT_POLICY,
  which keeps only 'civ' and the empty bullet, so anything NOT flagged
  'civ' is unreachable by them - and in the first draft that meant a
  freighter's only answer was the empty bullet in seven themes out of
  eight. "Minimal shielding" turning into "never shielded" is not what
  the campaign rule asked for. The bare plating, the dormant ring, the
  projector nodes and the clamped housing are flagged 'civ' and left
  uncapped for exactly that reason: they are what a merchantman
  carries, at every band.

  A new bullet must respect the floor: a full envelope needs a hull
  large enough to justify the generators, while a courier gets nodes
  and plating. Keep the effect anchored to a surface - standing off the
  plating by a few metres, crawling along a hull seam, brightening at
  the prow - so the image has somewhere to put the light.
-->

- || none min-small
- overlapping scales of bare ablative plating, scorched and pitted where they have already taken hits || min-small civ
- a dormant emitter ring around the hull's waist, dark and unpowered, its segments beaded with frost || min-small civ
- a scatter of small projector nodes along the hull edges, each a stubby post with a lens head and a spill of cabling at its base || min-small civ
- a squat civilian shield housing clamped to the dorsal plating, its single emitter lens hooded and a maker's plate bolted beside it || min-small civ
- a faint hexagonal shimmer standing a few metres off the plating, its cells brightening one by one where dust grazes them || min-small
- mismatched salvaged shield nodes clamped to the hull wherever they would fit, half of them dead and one arcing softly to its neighbour || min-small max-medium civ
- a debris-deflection array ringed around the hull's midsection, stubby emitter posts spaced along the rails with cable looms sagging between them || min-medium civ
- a belt of armoured emitter blisters down each flank, throwing a thin skin of light that clings tight to the hull || min-medium
- ablative plating layered over the prow in stepped courses, the outer sheets blackened and curling away at their edges || min-medium
- projector pylons standing proud of the hull at the shoulders, a taut bubble of pale light drawn between their tips || min-medium mil
- a hard-edged shield collar ringing the command structure, its panels hard-lined and stepped with sharp shadow cut between them || min-medium
- a stencilled emitter rail running the hull line, the field visible only as a heat-shimmer distortion against the stars || min-medium
- neatly faired emitter housings flush with the plating, the field reading as a clean sheen rippling flat across the hull || min-medium max-large civ
- a row of heavy iron emitters bolted along the hull rails, deposit crusted down their housings and the field standing off the plating in a low unsteady skin || min-medium
- a heavy shield envelope crackling at the hull line, whole panels of it flaring hard where debris burns through || min-large mil
- banks of shield generators bulging from the dorsal spine like boiler drums, thick conduit trunking running forward from each || min-large
- a full energy-shield envelope shrouding the hull in slow-rolling light, discharge arcs walking across the plating beneath it || min-huge mil
- a heavy shield array hung with counterweights between the prow fittings, its field breathing slowly in and out along the plating || min-huge
## Launch catapult

<!--
  Mech launch hardware, and only that. These rails and tubes exist to
  fling a mech into space, which is why this table is reached by
  carriers first and by the largest battleships second, and by nothing
  else at all - a cargo hauler, a patrol boat or a smuggler has no
  catapult, and the campaign rule says so outright. EQUIPMENT_POLICY
  gives those types the 'none' policy on this column and
  DEFAULT_EQUIPMENT_POLICY makes a new type fail safe the same way, so
  if a generator ever reaches this table from another hull, that is a
  bug in the caller and not a missing bullet here.

  The bullet lands in the shared armament sentence - "The hull carries
  {weapon}, {shield} and {catapult}." - so it is a noun phrase about
  visible structure: rail, deck, tube mouth, blast door, the mech
  itself sitting on the shuttle waiting to go. Putting a mech on the
  rail in a few of these is deliberate - it sets the scale of
  everything else on the hull better than any measurement in the prompt
  would.

  Floors matter more here than anywhere else in the file, and there are
  two tiers:

    min-large is the RAIL tier - one rail, a pair of rails, a row of
    tube mouths, chutes cut into the belly. Modest hardware a big
    warship can carry without becoming a carrier.

    min-huge is the DECK tier - full-length flight decks, ranked mechs
    under floodlight, banks of drop tubes. A carrier's alone.

  Between them sit three deck-scale bullets floored min-large and
  CAPPED max-large, and that cap is doing real work. LIGHT_CAP in
  ship_policy.py lowers a huge battleship's ceiling to 'large', so
  every UNCAPPED min-large bullet is reachable by it and the first
  draft handed a battleship an open launch deck cut clean through the
  hull. The cap needs a top band of at least the hull's own, so
  max-large excludes every huge hull: a LARGE carrier still reaches all
  three, a huge battleship is left the rail tier the matrix promises,
  and a huge carrier loses nothing because the deck tier above was
  written for it.

  This table has NO neutral bullets, on purpose. Every fitted bullet is
  min-large or above, because a catapult is a deck and has nowhere to
  sit on a one-hex hull; demanding a size-neutral catapult would put a
  flight deck on a courier, which is the exact thing the filter exists
  to prevent. ship_policy.py carries the table in NEUTRAL_POOL_EXEMPT
  for that reason. The 'none' bullet is what keeps this pool from
  emptying, not a neutral tier.

  Flags are otherwise the shared set the '## Weapon' comment documents,
  and 'mil' is on all of the fitted hardware. There are no theme tags:
  this table is not in THEMED_TABLES either - Hull, Detail, Weapon,
  Command bridge and Backdrop, five and only five - so filter_by_theme()
  never reads it, and the four tags an earlier draft carried were split
  into the flag segment and ignored. Those four bullets are all still
  here, reachable from every theme now instead of from one - and their
  PROSE was neutralised in the same pass, because a stripped tag on
  unchanged words just makes one theme's content everybody's: the gothic
  arches and votive banners framing a launch aperture are a heavy arched
  frame and blast staining now, and the hard black panel lining and trim
  striping down two deck edges are raised seams and scorch fans.

  NOTHING STANDS ON THE DECK. This is a token-prompt rule and it is
  absolute. TOKEN_TEMPLATE asks for "a single vessel centered in frame and
  clear of the frame edge ... isolated vehicle illustration, clean
  silhouette" on "an empty plain white void", and then feeds the result to
  RMBG for background removal - so a mech standing ready in the throat of a
  bay, deck crew and tow tractors alongside a rail, or ranks of mechs under
  floodlight are extra figures the mask has to cut around, in the one image
  where there must be exactly one object. Five bullets here did that, and
  EQUIPMENT_POLICY['carrier']['Launch catapult'] is 'heavy', so a carrier
  can never roll the empty bullet and roughly two carrier tokens in five
  would have carried them. Describe the DECK and not what is standing on
  it: blast deflectors raised behind each rail, holdback gear ranked down
  the rail, scorch fans spreading back down the deck, deck lighting laid in
  lines. The mechs and the deck crew belong in '## Backdrop', which is
  portrait-only.

  MOST SHIPS NEVER SEE THIS TABLE, and the numbers are worth writing down
  rather than rediscovering. Eighteen of the twenty-one legal (type, size)
  cells reach exactly ONE option here - the empty bullet - because
  EQUIPMENT_POLICY gives eight of the ten types the 'none' policy outright,
  and 'battleship large' reaches ZERO real catapults because LIGHT_CAP maps
  'large' to a 'medium' ceiling and the smallest catapult below carries a
  'min-large' floor. Both are correct and both are pinned by
  test_ship_policy.py. Rolled end to end, about 6% of ships reach any of
  the thirteen real bullets below. That is the brief working, not a gap:
  "no cell is pinned to exactly one piece of hardware" is a claim about
  cells that reach real hardware at all, and eighteen cells here reach none
  on purpose. Name the structure, never
  the colour of the light coming off it - "{glow} glow" owns the hue -
  and keep the hardware out of mid-launch narrative: scorch fans and
  worn deck paint read on a moored ship, a rail firing does not.
-->

- || none min-small
- a single linear catapult rail set into the dorsal deck, its blast trench running the length of the hull to an open muzzle at the bow || min-large mil
- twin catapult rails flanking the spine, blast deflectors folded down between them and the shuttle cradles standing empty || min-large mil
- catapult tubes ranked in a row along one flank, each mouth a square armoured aperture with its number stencilled above it || min-large mil
- angled launch chutes cut into the underside of the hull, exhaust staining fanned back from every mouth || min-large mil
- an open launch deck cut clean through the hull, lit strip by strip along its floor and its throat framed in heavy blast collars || min-large max-large mil
- an armoured launch bay with its blast doors folded open, the rail inside running back into the hull and hard light spilling out past its lip || min-large max-large mil
- a catapult deck extending from the hull shoulder in a stepped box structure, its outer edge banded and scorch fans spreading back across it || min-large max-large mil
- a pair of catapult decks slung under the forward hull like jaws, deck lighting running along their inner faces and holdback gear ranked down each rail || min-huge mil
- four catapult rails ranked across the bow, blast deflectors raised behind each and scorch fans spreading back down the deck from every rail || min-huge mil
- a launch bay opened in the flank of a kilometres-long hull, a heavy arched frame around the aperture and blast staining fanned back from the rail || min-huge mil
- a full-width flight deck running the ship's length, deck lighting laid in lines down it and blast deflectors raised behind every rail || min-huge mil
- twin full-length catapult decks running the flanks, every plate divided by raised seams and scorch fans spreading back down both deck edges || min-huge mil
- a bank of vertical drop tubes through the belly armour, their doors standing open one after another down the line || min-huge mil
## Command bridge

<!--
  The visible command superstructure - where the ship's crew sits and
  what that looks like from outside. This is the silhouette element
  that most decides what a hull reads as, so the table runs the full
  span from a blister barely there to a spire that dominates the ship,
  and the size floor is what keeps a bridge castle off a courier and a
  single canopy off a five-hex battleship.

  There is no empty bullet here, and that is deliberate rather than an
  oversight. A bridge is silhouette, not fitted equipment: every hull
  has somewhere to be flown from, even if that is one armoured slot in
  the prow. The policies on this column include 'any' and 'light', both
  of which admit the empty bullet, so adding one would leave freighters
  and stealth hulls with no command structure drawn at all - the table
  would be answering "what is the bridge" with silence on the two hull
  types whose bridge IS the silhouette. ship_policy.py carries this
  table in ALWAYS_FITTED for that reason and the 'none'-bullet
  invariant skips it there; do not add an empty bullet to satisfy the
  four-table rule. A hull that should read as blind gets the
  faired-over sensor blister, which is a shape rather than an absence.

  Never name a weapon in a bridge bullet. Cargo and support hulls reach
  this table under an 'any' policy while their Weapon column is
  'minimal', so a gun cupola described here walks armament straight
  past the gate that exists to keep it off them. Armour is fine.
  Armament is not.

  Bridge windows are worth naming - a lit bridge is often the only warm
  light on a hull and it tells the renderer where the front is - but
  name the windows, not the colour of what burns in them. "{glow} glow"
  is a separate roll and the palette line calls it the only saturated
  colour in the frame. Keep the hull's own paint out too: '## Hull'
  has already coloured the ship and '## Faction' owns its markings.

  Flags are the shared set the '## Weapon' comment documents: a size
  floor on every bullet, read by filter_by_size(); an optional max cap;
  'mil' where the structure is armoured for a warship's purpose; 'civ'
  where it reads mercantile or corporate; and an optional theme tag.
  Three untagged bullets sit at min-small with no cap so the neutral
  pool this table has to keep is never empty, and the two 'civ' modules
  carry max-large so a showroom bridge cannot land on a fleet carrier.
-->

- a flush armoured blister barely raised above the plating, a single dark vision slit cut across its face || min-small max-medium
- a squared bridge block set low in the spine, a wide banded viewport across its front and hard lining down every edge || min-small max-medium @gundam
- a low canopy set into the hull's back, its glass tinted gold and its frame faired smooth into the surrounding plates || min-small max-medium
- a smoked bridge canopy set flush in the plating, thin lit data strips running the length of its frame || min-small max-medium @cyberpunk
- a squat armoured cockpit block at the prow, thick blast shutters hinged open either side of the forward glass || min-small
- an armoured bridge slot let into the prow face, a narrow band of thick glass set deep behind a hooded brow of plate || min-small
- a narrow stone-faced bridge turret with lancet windows and a carved tympanum above the forward glass || min-small max-medium @neogothic
- a stepped conning tower rising in two blunt tiers behind the prow, antenna masts and a spinning radar dish crowning it || min-small
- a faired-over sensor blister of solid armour plate, a narrow band of lens apertures cut across its face where a canopy would sit || min-small @tactical
- a hand-patched pilothouse welded onto the spine out of mismatched plating, a name painted by hand along its flank || min-small max-medium civ @scav
- a bridge cab lifted whole off some other hull and bolted down on a welded frame, its seams caulked and painted over || min-small max-large civ @scav
- a wraparound bridge gallery ringing the forward hull, a continuous band of windows running right around it || min-medium civ
- a raised bridge pavilion with a slatted screen wall along its gallery, its posts and rails lacquered dark || min-medium @neosamurai
- a glass-fronted bridge module seated flush in the upper hull, polished panelling around it and every seam faired flat || min-medium max-large civ @corporate
- a bridge module glazed corner to corner in one curved pane, its mullions polished and its frame faired flat || min-medium max-large civ @corporate
- an armoured bridge tower set well back on the spine, splinter shielding around its base and a lattice mast rising behind it || min-medium mil @tactical
- a slab-sided command block with holographic markings drifting across its face, broken only by a single lit data band || min-medium @cyberpunk
- a low bridge house roofed in overlapping lacquered plates that sweep up at the corners, an enamelled crest above the forward glass || min-medium @neosamurai
- a tall bridge tower standing proud of the hull, hard panel lines cut across every face and a broad viewport banded across its front || min-medium mil @gundam
- a multi-deck bridge castle stacked amidships, tier on tier of lit windows and a forest of masts and dishes rising from its roof || min-large
- an armoured citadel bridge sunk into the hull's shoulders, only its upper deck and its vision band standing clear of the plating || min-large mil
- a towering bridge castle at the stern, flanked by twin funnel-like exhaust stacks and hung with signal lights down its length || min-large
- a squat crenellated tower of blackened iron set aft, arrow-slit windows burning narrow down its face, a votive banner above it || min-large mil @grimdark
- a cathedral spire crowning the ship's back, buttressed and gilded, stone statuary standing in ranks along its flying arches || min-huge @neogothic
- a fortress bridge like a cliff face across the hull, buttressed shoulders stepping back in tiers and light in a thousand windows || min-huge mil @grimdark
## Markings

<!--
  The paint that says nothing about who owns the ship. Rolled into the
  same sentence as the Faction visual and the Condition -
  "{faction_line}{markings}, {condition}." - so a bullet is a LOWERCASE
  NOUN PHRASE that comma-joins cleanly on both sides, the same shape the
  Faction visual segment has. Never a clause, never a verb the ship is
  doing.

  ONE PHYSICAL LINE PER BULLET, flags included. parse_tables() matches
  `^-\s+(.*?)\s*$` and drops continuation lines silently, taking the flag
  segment with them.

  THE FACTION BOUNDARY, which is the whole reason this table is separate.
  '## Faction' owns the AFFILIATION'S livery: its crest, its roundel, its
  house colours, its unit numerals, its company stripe - anything a
  stranger could read the owner off. This table owns the IMPERSONAL paint
  the same hull would carry under any flag: hazard striping around things
  that move, service stencils, panel and muster lettering, tallies, chalk,
  crew scrawl, a seal taped over a hatch. The test is ownership, and the
  tell is scale. Faction paints at identity scale - a crest amidships, a
  number a deck high, visible from the next ship over. Markings paints at
  arm's length - lettering sized for the person standing next to it,
  repeated wherever the job needs it. Both tables land in one sentence, so
  two coats of paint arguing is the failure mode, and the way to lose that
  argument is to write a big identifying mark here.

  ONE IDENTITY NUMBER PER SHIP, AND IT IS USUALLY THE FACTION'S. This
  table paints at arm's length from the affiliation, but the prompt puts
  the two clauses side by side - "{faction_line}{markings}, {condition}." -
  and an earlier draft answered a faction visual reading "a hull number
  stencilled on by hand" with a pennant number at the bow AND a registry
  code at bow and stern quarter AND a repeated hull code beside every
  airlock, which is four identity numbers in one sentence. Two overpaint
  bullets sat beside the militia's taped-over insignia in the same way.
  What survives is the neutral repeated hull code, which is a stencil
  rather than a name, and one overpaint; the pennant number is
  recovery-and-jacking-point stencils now, the registry code is a chalked
  bay assignment, and the censored rectangle is an ordnance handling lane.
  Before adding a marking, read the fifteen '## Faction' visuals and ask
  whether the new one would be the second of anything.

  NEVER NAME A SATURATED COLOUR. The prompt's closing palette line claims
  the rolled glow is "the only saturated color in the frame", and it
  softens to "the only OTHER saturated color" for exactly one reason: a
  Faction flagged '|| palette' asserting pigment of its own. This table
  carries no such flag and nothing softens for it, so "chevrons in
  yellow-and-black" contradicts the same prompt two sentences later.
  Greys, black, white, rust, chalk and bare metal are free - they are what
  the palette line already permits - and the chevrons read as chevrons
  without being told what colour they are.

  NOT A THEMED TABLE. The five themed tables are Hull, Detail, Weapon,
  Command bridge and Backdrop, and this is the '## Gear' argument from
  npc-generator-tables.md: a stencilled tonnage figure is not
  theme-defining, and filter_by_theme() never looks at a table outside
  that list, so an '@' tag here would be stripped into the flags segment
  and do nothing at all - failing quietly rather than loudly, which is
  worse. Theme reaches a ship through its silhouette and its hardware;
  the service stencils look the same in every one of the eight.

  NEVER WRITE A NEGATION. CFG 1.0, no negative prompt, so a noun named to
  forbid it gets drawn - "no unit insignia" is how a shipbreaker's hull
  ends up wearing one. "flat grey overpaint over older lettering, the
  shapes still showing through" is the same fact and is drawable.

  Say what IS on the plating, and keep it to paint. Physical fittings -
  boards, placards on brackets, anything that stands off the skin - are
  '## Detail'. A stencil, a decal, a chalk mark and a strip of tape are
  this table's; a bolted-on frame is not.

  '|| civ' and '|| mil' are filter_by_mil()'s flags, unchanged in meaning.
  An unflagged bullet is neutral and reachable by both, and twelve of the
  twenty-nine here are, which is what keeps the filter safe to run: it
  ends `plain or options` and never rolls nothing. Flag a bullet only
  where it would read as an error on the other kind of hull - kill
  tallies and muster letters are a warship's, a load line and a sponsor
  decal are not.

  ABOUT TEN WORDS, eighty characters of prose at the outside. '{markings}'
  shares a 130-character budget with '{condition}' in the same sentence.

  Evoke, never cite. No real navy's pennant system, no real carrier's
  registry, no real company's decal. Describe the stencil and let it be
  anyone's.
-->

- x2 hazard chevrons striped around every hatch lip and moving joint
- x2 a stencilled hull code repeated small beside each airlock and access panel
- walkway edges picked out in white striping down the length of the spine
- tow-point arrows stencilled onto the plating at every lifting eye
- warning triangles stencilled around the thruster mouths, soot-fringed
- panel numbers stencilled small at the corner of every access plate
- chalked inspection dates scrawled beside the seams, half of them scrubbed out
- a quarantine seal taped across one hatch, its corners lifting away
- crew nicknames hand-lettered small beside the crew hatch in uneven capitals
- flat grey overpaint over older lettering, the shapes still showing through
- a boarding warning stencilled in block capitals beside the main hatch
- stencil fonts mismatched where lettering has been replaced piecemeal
- kill tallies stencilled in rows of small hull silhouettes below the prow || mil
- recovery and jacking-point stencils marked at each frame station || mil
- muster station letters stencilled at intervals along the flank || mil
- damage-control diagrams stencilled beside every armoured hatch || mil
- a formation stripe painted down the dorsal plating for station-keeping || mil
- small stencilled arrows marking each joint in the armour belt || mil
- rescue markings at the crew module, a cut-here arrow stencilled beside them || mil
- warning stencilling ringed around every deck aperture, its edges chipped back || mil
- a marked ordnance handling lane painted across the deck plating in broken bars || mil
- a load-line mark and draught figures painted at the bow || civ
- sponsor decals ranked along the flank in mismatched sizes, several part-scraped || civ
- nose art hand-painted below the forward hatch, its lacquer cracked all over || civ
- a fuel-type placard and grounding marks stencilled by the umbilical port || civ
- dockyard chalk and a stencilled inspection stamp over the repaired plate || civ
- safety instructions stencilled in three alphabets beside the airlock || civ
- a bay assignment number chalked large beside the loading hatch || civ
- weight figures stencilled onto each container lock along the rack || civ
## Condition

<!--
  How hard the hull has been used, rolled on its own so the bullets in
  '## Hull' do not each have to end in "and weathered". Hull owns the
  silhouette and the coat of paint; this table owns what has happened to that
  coat since. Keep a bullet to about eight words - it shares a sentence with
  '## Markings' and the portrait prompt already carries nine rolled segments
  against a 512-token ceiling. See test/test_prompt_budget.py.

  It has to COMPOSE, which is the whole reason it is a separate roll. A hull
  bullet has already said "a pale blue-grey container ship" or "a faceted
  matte-black stealth craft"; a condition bullet says what state that finish
  is in, at an altitude that is true of any of them. So: no hull colour, no
  hull shape, no hull furniture. "Rust blooms creeping out of every seam"
  works on all of them. "Rusted orange plating" repaints two and fights
  the rest.

  It also has to compose with the wear the hull bullets DO carry, which is
  why several obvious bullets are deliberately absent. Three hull bullets
  already fan soot or scorch back from a vent or a thruster housing; two
  already sand paint back and respray it in mismatched patches; one already
  welds mismatched plate on in patches; the IPS-Northstar livery in
  '## Faction' already wears rust orange back to bare metal at every edge.
  Writing those again here does not stack, it says the same thing twice in
  one sentence and spends the budget doing it. These bullets reach for
  pitting, rime, bleaching, salt crust, primer, patch plate and battle damage
  instead, none of which any hull or faction bullet claims.

  Say what IS there. Generation runs at CFG 1.0 with no negative prompt, so a
  noun named in order to forbid it gets drawn anyway - the lesson the NPC
  file's '## Stance' note records. "Undamaged" and "no rust anywhere" are how
  a hull ends up dented and rusty; "the paint still even everywhere" is the
  same fact, drawable.

  Single segment, no flags, no theme tags, no gates - so it needs no reader
  beyond the roll loop and the '{condition}' slot. The range runs yard-fresh
  to barely spaceworthy and the weights sit in the middle of it, because a
  working hull is the common case: a fleet is mostly ships that have been
  somewhere. Both ends stay reachable from every roll, which does mean a
  corporate showroom hull can roll patch plate and tension cable. That
  cross-product is left open on purpose - the alternative is a civ/mil or
  theme gate on a table the design specifies as flagless, and a showroom
  freighter that has visibly had a bad decade is a better picture than a
  fourth filter.
-->

- straight out of the yard, the paint still even everywhere
- worked up and clean, seams touched up, edges sharp
- x2 lightly used, faint scuffing around the hatches and handholds
- x3 a working finish, paint dulled chalky on the sunward side
- x3 weathered evenly, micrometeorite pitting freckled across every leading surface
- x2 long in service, rust blooms creeping out of every seam
- x2 the topcoat scoured back to primer in wide swathes
- x2 ice rimed thick in the shadowed recesses and vent throats
- radiation bleaching washed pale across one whole flank
- salt-white residue crusted along every seam from atmospheric work
- field repairs riveted down over older field repairs
- scarred deep along one flank where something got through
- gouges raked across the belly plating, their edges bright
- held together by patch plate and tension cable
## Backdrop

<!--
  Ship portraits only. This is NOT the general-purpose `## Backdrop` in
  npc-generator-tables.md that sits behind a character or a mech - a bullet
  from that one put behind a ship sets the shot in a street. The two carry
  the same heading and must stay in separate files for that reason:
  parse_tables() in generate-npc.py does tables.setdefault(name, []) and
  extends, so two blocks called `## Backdrop` inside one file merge into a
  single pool and a freighter rolls a rain-slicked alley three times in four.
  This is the ship generator's copy, in prompts/spaceship-generator-tables.md,
  which is what LIVE_TABLES in test/test_ship_policy.py already points at.
  Never paste an NPC backdrop in here, and never paste one of these there.

  Every bullet is ONE PHYSICAL LINE, flags included, however long it runs.
  parse_tables() matches a bullet with ^-\s+(.*?)\s*$ and matches
  continuation lines against nothing at all, so a wrapped bullet is
  truncated at its first line and its whole flag segment is dropped in
  silence - a capped scene becomes uncapped, a 'combat' scene becomes
  neutral. Only this comment block wraps.

  Each bullet carries BOTH halves of the shot, split on '||': the framing
  phrase on the left, the scene sentence on the right. They are rolled
  together because they have to agree - a low angle from below cannot be
  staged inside a nebula's inner curtain, and a cathedral drydock's interior
  is not something you get a distant profile shot of.

  The framing half is a BARE SHOT DESCRIPTOR and carries no preposition of
  its own. The template supplies the join, the way `**{SHOT}** of **{ROLE}**`
  does in npc-generator-tables.md, and the scene half then lands as its own
  standalone sentence after it. A framing half ending in "of" or "through"
  gets that preposition twice, or gets a capitalised sentence welded to it
  mid-clause; neither reads. Write the framing so a noun phrase can follow it
  and write the scene so it stands alone.

  READ THE FRAMING BACK AS "{shot} of {ship}" BEFORE COMMITTING IT. Three
  earlier ones failed that read and each failed differently. "A low dramatic
  angle from below" composed as "A low dramatic angle from below of a patrol
  cutter" - the trailing adverbial takes the preposition slot the template
  needs, and it is "A low dramatic angle" now. "A cathedral-scale interior
  shot" composed as "A cathedral-scale interior shot of a battleship", which
  reads as a view of the inside of the battleship when the interior in
  question is the drydock the ship is sitting in; it is "A cathedral-scale
  wide shot" now. And "A tiny distant silhouette" promised an unresolvable
  subject in a prompt that goes on to ask for stencilled block figures and
  scuffing round the handholds - the far register is already covered by "A
  distant profile shot" and "A long telephoto view", so it is "A far-off
  three-quarter view" now.

  The absolute rule is COMPOSABILITY: a backdrop describes THE SETTING ONLY.
  Not one word about the subject's hull, colour, class, markings, weapons or
  size - the hull roll already spent a paragraph on those, and every
  adjective a backdrop spends on the subject fights it. A "battle-scarred"
  scene that renders a pristine liveried courier is the whole failure mode.
  Write the scene AROUND an unnamed vessel: other ships, stations, planets,
  debris, crew and light sources are all yours, and the subject is not. Do
  not reach for it even as "it" or "the ship" - there is no placeholder in
  this table. That includes a drive plume, a reentry sheath and a fuel-scoop
  wake, all of which are the subject's own hardware wearing a scene's
  clothes; put them on a background hull instead, where they cost nothing.

  No pronoun that could REBIND, either. The subject is inserted between the
  two halves at render time, so "its flank" eight words after "a crippled
  hull" reads as the subject's flank by the time an image model sees it.
  Name the thing again - "the wreck's flank", "the deck edge".

  The same rule covers equipment. Background hulls may carry launch decks,
  gun batteries and armour belts because they are other ships, but nothing
  in a scene may imply the SUBJECT has any of it - no "fighters launching
  from its deck", no "its guns answering the fire". A cargo hauler and a
  fleet carrier both have to be able to roll almost every bullet here, and
  the two exceptions are declared with a size cap rather than left to luck.

  Keep a scene sentence under about forty words and to at most three things
  happening. A ship prompt rolls nine segments against the NPC prompt's
  slots and runs at the same TOKEN_LIMIT = 512 ceiling (see
  test/test_prompt_budget.py); the backdrop is the longest of the nine, and
  what overruns costs the palette line and the closing style tags, which
  fall off the end without a warning.

  A scene that names a saturated HUE constrains the Glow roll, because the
  palette line claims the glow is the only saturated colour in the frame.
  Background objects may carry a colour - dirty orange flak, sodium
  worklights, a dull red cooling wreck - but keep it to one or two per
  scene and never let it wash over the subject. That is why the nebula names
  structure and depth and lets the glow tint it: "curtains of magenta and
  teal gas" plus a rolled copper-orange glow is three palettes arguing. If
  more hues are ever added here, filter_by_hue() in generate-npc.py has to
  run against this table too, narrowing '## Glow colour' to shades that
  agree with what the scene already committed to.

  The flags:

  Note that 'combat' stays 'combat' HERE while the four equipment tables
  rename theirs to 'mil': this one is a scene gate the policy matrix never
  reads, and the equipment one keys against EQUIPMENT_POLICY. The full list
  is below, and it is enumerated in one place on purpose - an earlier
  version of it listed four flags, omitted 'weather' entirely, and
  documented a 'max-small' bullet that did not exist.

  'weather' - THE ONLY FLAG ON THIS TABLE THAT HAS A LIVE READER TODAY, and
  the one an earlier draft forgot. weather_sentence() in generate-npc.py,
  which design section 5 names as the source of {weather_line} and copies
  verbatim, opens `if "weather" not in split_backdrop(npc["Backdrop"])[2]:
  return ""`. So '## Weather' renders ONLY against a bullet here carrying
  this flag, and the earlier draft carried it on zero of twenty bullets -
  nineteen authored Weather lines, twenty-nine weighted options and a
  forty-seven-line comment block that could never reach a prompt, with
  "clear" stamped into every dossier. The sibling NPC file runs 171 of 353
  backdrops flagged, about 48%; thirteen of the twenty-six here is 50%, and
  the ONE-IN-THREE-STAYS-CLEAR dial lives in '## Weather's own weights, not
  in how many scenes are flagged. A scene gets the flag when it has a medium
  something can drift through or hang in - atmosphere, a nebula, dust, loose
  debris, an enclosed bay's still air, a working dock's exhaust haze - and
  goes without when it is open hard vacuum with nothing in it. IF YOU ADD A
  SCENE, DECIDE THIS FLAG DELIBERATELY; it is the difference between a table
  that renders and one that does not.

  'dock' - stationary, moored, or under service. No motion blur, no drive
  plume, nothing streaking past. Eight bullets carry it. '## Glow placement'
  reads it twice over: it is the FORBID for the 'under-way' engine glow,
  which cannot be lit at a berth, and half the gate for the placement that
  washes light onto a neighbouring hull. Spelled 'dock' and not 'docked' so
  it matches design section 2 row 15 and the gate word on the placement
  table; nothing reads it yet, so the rename cost nothing and the drift
  would have.

  'vacuum' - hard vacuum, no atmosphere or haze to scatter a glow: drive
  light, weapons fire and floodlights all cut off hard at the hull instead
  of blooming. Most of this table is airless.

  'atmosphere' - the opposite: air around the hull, so light blooms and a
  distance haze is legal. Three bullets - the descent, the gas-giant skim
  and the planetside hardstand - and it never appears beside 'vacuum'.

  'planetlight' - a planet, moon or cloud deck fills part of the frame and
  throws reflected light up onto the hull. Six bullets.

  'hull' - another vessel is close enough aboard to be a surface: a tender,
  a wreck, a moored neighbour, a queued hauler. Nineteen bullets, and it is
  the gate for the placement that washes colour onto a second hull.

  'debris' - loose matter close aboard, big enough to catch light: an
  asteroid field, a post-battle debris field, a breaker's yard, a wreck
  graveyard. Five bullets, and it is the gate for the placement that throws
  colour across the tumbling pieces.

  'combat' - the scene is an active engagement. Four of the twenty-six,
  because a portrait table that comes up fighting one time in three stops
  reading as a portrait table.

  'interior' - an enclosed bay or dock, surfaces close enough on every side
  to catch cast light and throw it back. All four interior bullets are also
  'dock'; they need not be, but a ship under way inside a sealed bay is a
  strange thing to ask a renderer for.

  'max-small' / 'max-medium' - the scene physically cannot hold a hull
  bigger than this. Two bullets, both 'max-medium': the enclosed commercial
  berth and the atmospheric descent, neither of which takes a five-hex
  cathedral cruiser. NO BULLET CARRIES 'max-small' and an earlier version of
  this paragraph documented one that did not exist, which is the same class
  of error as an unread flag with the sign reversed - a reader trusting the
  note would look for a cap that is not there. Everything else scales,
  because open space and a kilometres-long drydock hold anything. This is
  the same flag vocabulary the equipment tables use and the same reader
  parses it - size_bounds() and filter_by_size() in ship_policy.py - so a
  cap here needs no new code, though nothing calls that reader on THIS table
  yet either; see "Flags that still need a reader" in the file header.
  There is no 'min-' bullet here and there should not be: a small hull looks
  fine anywhere.

  An unrecognised flag is IGNORED rather than reported, exactly as
  BACKDROP_ROLES warns in npc-generator-tables.md, so a gate invented here
  and not added to its reader ships silently inert. Before adding a flag,
  add it to the code that reads it - and then check the other direction as
  well, which is the check nobody ran: EVERY FLAG SOME OTHER TABLE GATES ON
  MUST BE SUPPLIED BY A BULLET HERE. 'weather' is the cautionary tale.

  '## Glow placement' gates five of its bullets against this table, and the
  ship-side contract is FLAG AGAINST FLAG, not the NPC file's regex over the
  scene prose. generate-spaceship.py's PLACEMENT_REQUIRES maps a placement's
  gate word onto a flag that must appear in split_backdrop(...)[2], and
  PLACEMENT_FORBIDS onto one that must not; 'debris', 'hull', 'planetlight'
  and 'combat' are requires, 'dock' is the forbid behind 'under-way'. Flags
  rather than prose because the ship copy is being written fresh and a
  keyword list over twenty-six scene sentences is a maintenance liability
  the flag segment already solves. What this table owes in return is SUPPLY:
  five debris scenes, nineteen with a second hull, six with a planet, four
  in combat and eight at dock. Deleting the last bullet in any of those
  groups empties a gate one table over, and nothing will say so.

  Theme tags are the NPC generator's vocabulary, so the two generators speak
  the same language. Ten of the twenty-six carry one, in FIVE PAIRS: a
  tagged bullet is unreachable from every other theme, so tag only a scene
  strongly and unmistakably of one look - the votive banners, the colony
  cylinder's primary-coloured traffic, the grease-streaked hab-ring berth. A
  patrol lane, a debris field and an asteroid belt look the same in every
  campaign and stay neutral.

  PAIRS, and never a single. apply_theme_share() duplicates the tagged pool
  to THEME_SHARE = 0.6 of the whole, so one tagged backdrop under a theme is
  sixty per cent of that theme's rolls - the same scene three times in five
  - while ZERO tagged backdrops leaves the pool alone and the theme renders
  from the neutral sixteen, which is what corporate, neosamurai and tactical
  do here and what most of the sibling NPC file does in every table. Two or
  none. If a sixth theme earns a scene, it earns two.

  Never name a property, faction or vessel, and never a coined term from
  one - "shrine world" draws nothing an unmarked planet does not. These go
  to an image model, which cannot draw a citation: describe the form and let
  the reference show through.
-->

- A wide three-quarter view || A fleet line action spread across kilometres of dark, two ranks of capital hulls trading beam fire, flak blooming dirty orange between the lines and one far hull venting a burning plume from a torn flank. || combat vacuum hull
- A distant profile shot || Low orbit over a planet's terminator, the daylit crescent burning hard white along one edge, the nightside below threaded with city grids and silent storm flashes, a cylindrical habitat turning slowly further out. || vacuum planetlight
- A low dramatic angle || A descent through a planet's upper atmosphere, pale ionisation trails hanging where other craft have come through ahead, a torn cloud deck rushing past below, a landing corridor picked out by strobing marker beacons stepping down toward a distant spaceport. || weather atmosphere planetlight max-medium
- A close side-on view || A replenishment run in high orbit, a blunt fleet tender holding station a hundred metres off with a rigid transfer boom extended across the gap, pallet cradles riding the boom on a powered track under flat hard floodlight. || dock vacuum hull
- A high three-quarter view || A berth inside a hab ring's commercial dock, the enclosed bay walls crowded with clamps, fuel gantries and hand-lettered berth numbers, cargo drones stacking crates on the grease-streaked deck below, sodium worklights catching a drifting haze of exhaust. || weather dock interior hull max-medium @scav
- A tight raking view || A dense asteroid field in low sunlight, house-sized rocks tumbling slowly through the foreground, a broken kilometre-long fragment turning end over end beyond them, hard black shadows and pale grey dust across every face. || weather vacuum debris
- A far-off three-quarter view || Empty deep space at cruising speed, a hard unblinking starfield edge to edge and the cold far smear of a galactic arm laid across one corner, the dark between them unbroken. || vacuum
- A wide elevated view || An orbital shipyard cradle, open scaffolding ribs and gantry arms folded around the berth, work lamps clustered along them in a dozen bright knots, welding arcs throwing drifting sparks as suited crews cross between the spars. || weather dock vacuum hull
- A slow drifting view || A debris field hours after a battle, torn hull plating and frozen propellant crystals turning end over end, a cooling wreck still glowing dull red deep inside a broken frame, lifepod strobes blinking in the dark further out. || weather vacuum debris hull
- A backlit wide view || A nebula's inner edge, curtains of gas layered kilometres deep and lit from within by a cluster of young stars, dust pillars silhouetted against the glow, the haze scattering every light in the scene into a soft bloom. || weather
- A head-on view || A jump point, a vast ring gate hanging against the stars with traffic queued along the approach lane in a strung line of running lights, the aperture warping the starfield into a slow spiral. || vacuum hull
- A tight low angle || A boarding action under way against a crippled hull nearby, grapple lines and a rigid umbilical strung from an assault craft to the wreck's buckled flank, armoured figures crossing the lines while point-defence fire stitches the dark beyond. || combat vacuum hull
- A wide slow pan || A derelict graveyard, dead hulls moored in ragged rows and stripped back to bare frames, cutting torches winking along their spines where breaker crews work, salvage barges creeping between them with nets strung full of plating. || weather vacuum debris hull
- A long telephoto view || A convoy strung out along a shipping lane, a dozen bulk haulers running nose to tail in a lit line, escorts spaced wide on the flanks, formation lights blinking in slow sequence toward a far pale sun. || vacuum hull
- A low three-quarter view || A planetside hardstand outside a spaceport, blast-scarred concrete running away flat under a pale sky, fuel bowsers and service trucks parked in a line along the apron edge and a row of landing lights stepping out toward the far pads. || weather atmosphere planetlight
- A hard-lit low pass || A colony cylinder's open end cap, interior terraces stepping away in daylight behind a kilometres-wide aperture, white and primary-coloured tenders queued along the rim under lane markings painted a deck high, a mirror array turning slowly beyond. || vacuum hull @gundam
- A slow rising angle || A colony ring under construction, bare frame sections held in place by tugs against a hard starfield, guide markings painted a deck high along every spar and a swarm of small work pods crossing between them in ordered lanes. || vacuum dock hull @gundam
- A low sweeping angle || A gas giant's cloud tops, banded ochre and cream storm belts scrolling past close below, a tanker hull further along the belt trailing a long scoop wake through the haze, lightning flickering deep inside the bands. || weather atmosphere planetlight
- A cathedral-scale wide shot || An enclosed orbital drydock, ribbed gantry vaults arching overhead like a nave, votive banners hanging kilometres long between the spars, censer smoke and welding sparks drifting through shafts of lamplight above robed work-gangs on the deck plates. || weather dock interior hull @neogothic
- A tall narrow view || A processional approach lane to a shrine station, columned buttresses rising either side of it, hanging censers turning slowly on their chains between them and lamplight falling in shafts through the drifting smoke. || weather dock interior hull @neogothic
- A vast low-angle wide shot || A warfleet at anchor above a world crusted with cathedral cities, kilometres-long hulls holding station in slow procession, gilt statuary and buttressed prows catching the sun beneath them, tender craft swarming around them like sparks. || vacuum planetlight hull @grimdark
- A grim low angle || A siege line above a burning moon, ranked capital hulls holding station in slow procession, gun smoke and vented atmosphere trailing away from the broken wrecks between them, ash drifting through the lower orbit. || combat vacuum debris hull @grimdark
- A high downward angle || An orbital bombardment in progress, lances of fire falling in ordered ranks through the cloud layer onto a continent already burning, smoke fronts spreading hundreds of kilometres wide, a screen of warships holding a hard line high above. || combat vacuum planetlight hull
- A cold flat side view || The underside of an industrial orbital plate, a slab-sided kilometre of unpainted structure, cargo throats and heat radiators hanging from the deck edge, stacked hull codes and holographic traffic markers glowing across the lanes below. || vacuum hull @cyberpunk
- A rain-streaked wide view || A lower-level docking gallery on an orbital plate, holographic lane markers stacked in tiers above the berths, cargo lifts running up the wall behind them and spill from a hundred small lit frontages washing across the deck. || weather dock interior hull @cyberpunk
- A cluttered low angle || A shipbreaker's yard strung between two captured rocks, cut hull sections stacked in ragged piles, cable runs and worklight strings looped across the gap and a haze of torch smoke drifting through all of it. || weather debris dock hull @scav
## Weather

<!--
  Ported from '## Weather' in npc-generator-tables.md, which is where the
  shape, the flag and the weighting argument all come from. Read that table's
  note first; this one only records what changed.

  PORTRAIT ONLY, and only against a '## Backdrop' bullet carrying the
  'weather' flag. The token renders on flat white for background removal, so
  anything drifting through it would just be more for RMBG to cut out - and
  the ship generator has a harder version of the NPC file's "rain inside a
  cockpit" problem, because most of its backdrops are hard vacuum.

  THIS TABLE IS ONLY AS ALIVE AS THAT FLAG. weather_sentence() opens `if
  "weather" not in split_backdrop(npc["Backdrop"])[2]: return ""`, and an
  earlier draft of '## Backdrop' carried the flag on none of its twenty
  bullets - so every line below, and this whole comment, was unreachable
  content that no roll could ever print, while the dossier stamped "clear"
  on every ship. Thirteen of the twenty-six backdrops carry it now: the
  atmospheric descent, the gas-giant skim, the nebula's inner edge, the
  planetside hardstand, the asteroid field, the post-battle debris field,
  the derelict graveyard, the shipyard cradle, the hab-ring berth, the
  enclosed drydock, the shrine approach, the breaker's yard and the docking
  gallery. Open hard vacuum with nothing in it does not - deep space at
  cruising speed, the jump point, the convoy lane, the fleet action.
  ENCLOSED BAYS AND DOCKS DO carry it, which reverses what an earlier
  version of this paragraph claimed: a bay has still air and an exhaust
  haze, and the third 'clear' bullet below exists to name exactly that.

  Some of these need GROUND, and the ground is one specific backdrop. The
  rain, the ground fog and the snow all describe a hull sitting on a pad
  with its landing feet under it, and the only scene in the file that
  supplies one is the planetside hardstand outside a spaceport. It was added
  for them. If that bullet is ever deleted, delete these three with it or
  rewrite them onto the descent, which is the other atmospheric scene.

  For a hull, "weather" is THE MEDIUM THE SHIP SITS IN, which is a wider
  category than rain. Nebula haze, ionisation off the leading edges, dust,
  entry plasma, venting propellant and drifting debris all belong here, and
  all of them do the same job the NPC file's rain does: they put something
  between the camera and the far end of the subject, which is most of how a
  painterly frame gets depth.

  The 'clear' flag means the bullet contributes nothing to the prompt at all;
  its text exists only so the dossier has something to print. That is the dial
  for how often a flagged scene actually gets weather in it, and it is set
  much heavier here than in the NPC file on purpose: a quarter of outdoor
  portraits coming up clear is right for a street, and a majority coming up
  clear is right for a ship, because empty space is the default medium and a
  hull with something drifting past it every single time reads as a weather
  generator rather than a fleet. As weighted below, eleven of twenty-nine
  entries are clear.

  Three clear bullets rather than one, because they are not the same clear:
  vacuum, still atmosphere and the dead air of an enclosed bay print
  differently in a dossier even though all three print nothing in a prompt.

  No pronoun placeholders. The NPC bullets carry {possessive} and {object};
  ship_fields() supplies {ship}, {Ship}, {name}, {size} and {is_are} and
  nothing else, so a stray {object} here is a SystemExit at substitution time.
  Say "the hull", "the plating", "the frame".

  Nothing here is themed and nothing here carries a size flag. A tag on this
  table would ship the literal '|| @cyberpunk' to the image model, and a nebula
  does not care how many hexes the ship is.

  Keep these to one short sentence. Both prompts already run close to Krea 2's
  512-token ceiling, and this sentence lands ahead of the palette and framing
  tail that gets truncated first.

  NEVER NAME A SATURATED HUE HERE. The closing palette line claims the rolled
  '## Glow colour' is the only saturated colour in the frame, and this
  sentence sits four clauses ahead of it: "a shell of orange" reentry plasma
  was a second saturated colour arguing with the first, and it is "a shell of
  fire" now. Say the phenomenon and let the light table own the shade.

  And check the list against itself. "Fine dust streams across the frame in
  long grains" and a wind-driven grit doing the same thing in the same words
  were one entry written twice; the second is blown sand piling in the
  leeward seams now, which is a different picture rather than a synonym.

  Don't trust a count written here - the NPC table's own note claimed
  twenty-three and had drifted to thirty-nine. Count them when it matters.
-->

- x6 hard vacuum, nothing at all between the hull and the stars || clear
- x3 clear air, nothing drifting in the frame || clear
- x2 still air in the bay, the hull sitting in it unmoved || clear
- x2 Thin nebula haze drifts across the frame, softening the far end of the hull into the background.
- Dense nebula gas rolls through the shot, the stern lost in it and the bow lit hard against it.
- Ionisation crawls in pale sheets across the leading edges, flaring brightest along the bow.
- A charged particle wash streams past in fine bright lines, breaking over the plating.
- x2 Fine dust streams across the frame in long grains, hazing everything beyond the hull.
- A dense dust curtain drags through the shot, reducing the far background to a flat pale wash.
- Entry plasma burns a shell of fire back along the belly, the air behind it rippling.
- Heat shimmer rolls off the plating in waves, the background rippling behind it.
- Heavy rain sheets down over the grounded hull, water running off the plating and streaking the deck.
- Fine rain beads across the upper surfaces and stands in every panel seam.
- A low ground fog rolls across the pad, swallowing the landing feet and the far background with them.
- Snow settles in a thin even layer along the dorsal plating and drifts up against the landing feet.
- Blown sand rattles across the plating and piles up in every leeward seam.
- Venting propellant fogs out along the flank and hangs in the frame as a slow white plume.
- Smoke rolls low across the scene from something burning out of shot, the far background lost in it.
- Micro-debris drifts through the frame in slow glinting specks, turning as it catches the light.
## Glow colour

<!--
  The one saturated colour ON THE SUBJECT in an otherwise restrained frame:
  drive plume, running lights, shield shimmer, a lit row of viewports. The
  colour and its placement are separate rolls, the same split Hair colour and
  Hair use in the NPC file - a new shade is one bullet here rather than a
  rewrite of every placement.

  "On the subject" is the honest form of the claim. A backdrop may carry lit
  objects of its own - a beacon, a welding arc, a nebula, tracer fire - and
  the closing palette line has to mean the hull, not the whole frame. What
  nothing outside this roll may do is name a hue that falls on or against the
  HULL: an equipment bullet calling its shield skin blue gives a magenta-pink
  roll a second glow to disagree with. The equipment tables carry that rule in
  their own notes.

  Where the backdrop does name a saturated hue, the fix is the NPC file's:
  filter_by_hue() in generate-npc.py narrows this pool to shades that agree
  with a coloured light the scene already committed to. It reads the shade's
  own words and needs no flag, which is the other reason these bullets stay
  single-segment. Unlike the NPC file's roll, this one is not gated by
  has_light_source() - a ship in vacuum is lit by its own hull - so it is
  rolled every time.

  Entries name a HUE and nothing else. The template wraps the value as
  "{glow} glow", so a bullet naming a light-emitting THING renders the thing:
  "plasma blue" pulled arcing plasma into frame, "neon cyan" pulled tubing.
  Say the shade and let the template supply the light.

  Weights favour the shades that read as a working drive - the cold blues and
  whites, amber, cobalt - since the engines are lit on most rolls and the
  exotic hues are for shield wash, alarm lighting and hangar floods. A frame
  whose main drive burns magenta should be uncommon enough to be a choice.

  Keep the shades far enough apart to be worth separate entries. "Pale
  ice-white" was deleted because it is what "cold blue-white" already renders
  as, against three weighted copies of it, and "teal-green" moved to "deep
  jade-green" to clear "bright cyan". Never put a theme tag here: with no
  '||' in the bullet the tag would ship as literal text into the prompt and
  the dossier both.
-->

- x4 cold blue-white
- x3 amber
- x2 vivid cobalt blue
- x2 dull copper-orange
- deep jade-green
- crimson-red
- brass-gold
- deep violet
- sickly yellow-green
- bright cyan
- magenta-pink
## Glow placement

<!--
  WHERE the rolled colour falls on or around the hull. Each bullet is the
  PREDICATE of "A {glow} glow ___." - it starts with a verb and carries its
  own contrast clause where it wants one.

  Do not name the colour. The template has already said it, and saying it
  twice is how a frame ends up with two glows disagreeing about the shade.

  Do not name a hull SHAPE. '## Hull' owns the silhouette; this
  table only says which part of it is lit. "Along the flank", "at the stern",
  "down the spine" are true of every hull that table can roll, and that is the
  level to write at.

  Do not name EQUIPMENT either, unless you gate it. Four other tables decide
  what this hull carries and half of them can come back with NO_EQUIPMENT, so
  a charging muzzle on a freighter with no guns, or a lit envelope on a hull
  whose shield roll was the empty bullet, is this table routing around the
  matrix that ship_policy.py exists to enforce. The gate flags below are how a
  bullet gets to name hardware anyway.

  The flags, in three groups:

    SCENE GATES, matched against the rolled backdrop's FLAG SEGMENT. Every
    word below is a flag '## Backdrop' actually carries, and that is not a
    coincidence - it is the contract. The four in the first group are
    PLACEMENT_REQUIRES entries; 'under-way' is the one PLACEMENT_FORBIDS
    entry. Three of the design's five prop words - 'dock', 'planetlight',
    'hull' - are in use here; 'vacuum' and 'atmosphere' are supplied by the
    backdrop table and reserved for a placement that needs them; 'debris',
    'combat' and 'under-way' are three additions on top of the design's five
    and are declared here so a reader is not left inferring them.
      'debris'    - the scene has loose matter close aboard: a debris field,
                    an asteroid belt, a wreck graveyard, a breaker's yard.
                    Five backdrops supply it.
      'hull'      - the scene has a second vessel close enough aboard to be a
                    surface. Nineteen backdrops supply it, and this gate is
                    always carried with 'dock', because the light has to
                    reach it.
      'planetlight'- the scene has a planet, a moon or a cloud deck in frame.
                    Six backdrops supply it.
      'combat'    - only makes sense mid-battle: a charging muzzle, a shield
                    under load, a hull torn open. Four backdrops supply it.
      'under-way' - the main drive is lit, so the ship is moving. THIS ONE IS
                    A FORBID, not a require: it is dropped against a 'dock'
                    backdrop, which has already moored the ship. A moored
                    freighter with its engines burning is exactly what the
                    flag exists to prevent. The manoeuvring-thruster bullet
                    stays unflagged on purpose - station-keeping thrusters
                    fire at a berth.
    An earlier draft spelled these 'docked', 'planet' and 'scene'. 'scene'
    was a fifth gate meaning "the light lands out in the environment", and it
    was dropped rather than renamed: every bullet that carried it also
    carried a specific prop gate, so it narrowed nothing that was not already
    narrowed, and a flag that never changes an outcome is a flag that will be
    trusted to do something one day.

    EQUIPMENT GATES, matched against what the equipment rolls came back with.
      'armed'    - reachable only when the '## Weapon' roll was not
                   NO_EQUIPMENT.
      'shielded' - reachable only when '## Shield generator' was not. A
                   dormant emitter ring and a lit envelope are not the same
                   ship.
      'deck'     - reachable only when '## Launch catapult' was not, which
                   under EQUIPMENT_POLICY means a carrier, or a huge
                   battleship at the rail tier. Nine types in ten have no
                   flight deck to light, and without this gate the glow puts a
                   lit launch deck on a grain freighter - the one thing the
                   whole matrix is built to prevent.

    An unflagged bullet is neutral and reachable from any roll, which is what
    most of these are.

  THE THREE EQUIPMENT GATES ALREADY HAVE THEIR READER, and it is
  ship_policy.filter_by_gates() at ship_policy.py:839. Its docstring names
  this table by heading, it reads exactly 'armed', 'shielded' and 'deck' out
  of EQUIPMENT_GATE_FLAGS (ship_policy.py:606), it keeps every bullet
  carrying no gate flag, and test_no_live_glow_placement_is_left_without_a_
  pool runs it against this very table over forty seeds for every legal
  (type, size) pair. An earlier version of this paragraph said in capitals
  that NONE of these gates had a reader, which would have sent the next
  author off to hand-write a duplicate of a tested function.

  THE FIVE SCENE GATES DO NOT HAVE ONE. filter_by_placement_prop() is on
  design section 1's duplicate-and-adapt list, not its borrow list, because
  the NPC original closes over PLACEMENT_REQUIRES and PLACEMENT_FORBIDS -
  human-scale props, ground and wall and signage. generate-spaceship.py owns
  the ship copy and the two dicts above it, and until it lands, the five
  scene gates are inert and every bullet here is reachable from every
  backdrop. Write them as flag lookups against split_backdrop(...)[2], as the
  group above specifies, and do it before the generator ships. An
  unrecognised flag is ignored rather than reported, which is how a gate
  ships silently inert.

  A gate reads the backdrop's flags or the equipment roll and nothing else;
  reading the hull bullet too would make this table a dependent of that one.
-->

- x2 burns deep in the engine housings at the stern and throws hard light forward along the hull flanks || under-way
- runs the full length of the running-light strips, picking the hull's edges out of the dark
- lights a long row of viewport windows down the flank, each one a small hard point in a wall of dark plating
- picks out the command structure's window band and the masts standing above it
- seeps from the hull seams and panel gaps where the plating does not quite meet
- traces the radiator fins and vent louvres running the length of the spine
- underlights the ventral plating from the manoeuvring thrusters set along the belly
- pools inside the recessed hatches and service wells set along the flank
- floods an open bay mouth low in the hull and spills past its lip into the dark || deck
- lines the approach markings painted down the middle of the flight deck || deck
- stands off the plating as a thin skin of light across the whole shield envelope || combat shielded
- gathers at the muzzles of the ship's guns as they charge || combat armed
- flares out of a torn-open section amidships and flickers along the buckled plating around it || combat
- throws colour across the tumbling debris drifting close alongside the hull || debris
- washes onto the flank of a second hull moored alongside, close enough to read its markings || dock hull
- lays a long streak of colour across the cloud deck of the planet turning below || planetlight
