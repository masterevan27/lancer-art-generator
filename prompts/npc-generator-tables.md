# Random NPC Generator Tables

Roll tables for `generate-npc.py`, which rolls one human NPC from these
lists and generates a matched pair of images in the campaign's house style: a
half-body **portrait** for the Foundry actor sheet, and a full-body **token** on
flat white that gets run through RMBG into a transparent PNG.

These are _people_ — pilots, contacts, dockhands, corpo liaisons — not mechs.
Mech art lives in `mech-catalogue-art-prompts.md` and is authored per chassis
rather than rolled. Every NPC these tables roll is an adult; the prompt templates
anchor adult height, proportion and facial structure explicitly, because the
campaign's painterly illustration style otherwise drifts toward short, soft-faced,
large-headed figures that read as teenagers. Keep new bullets consistent with
that — a bullet describing someone as short, small, slight or baby-faced fights
the templates and will bring the drift back.

## How the script reads this file

Every `## Heading` starts a table; every `-` bullet under it is one option. The
script looks tables up by their heading, so **renaming a heading breaks the
prompt template** — add and remove bullets freely, but leave the headings alone.

Weights are optional: a bullet may start with `xN ` to count as N entries, so
`- x4 nondescript grey work coveralls` shows up four times as often as a plain
bullet. Anything after the weight is used verbatim in the prompt, so write
bullets as sentence fragments that read correctly when dropped into the
templates at the bottom of this file.

`||` splits a bullet into segments. Eleven tables use it:

- **Age** and **Build** bullets carry a paired flag. `|| young` on an Age entry
  is an NPC under twenty: it swaps the prompt's "a fully grown adult" opening
  and its adult face clause for the young forms. `|| figure` on a Build entry
  marks a build written in terms of an adult woman's figure — bust, hips, waist
  — and those bullets are dropped from the pool whenever the Age roll came up
  `young`, so the unflagged builds are what a late-teen NPC rolls from. Keep
  enough of them to stay varied. The filter runs both ways: forcing a `figure`
  Build with `--set-trait` drops the `young` bullets from the Age pool instead,
  so an explicit build never collides with a randomly rolled teenager. Forcing
  *both* into a contradiction is an error rather than a silent pairing.
- **Gear**, **Weapon** and **Stance** bullets may end `|| hands`. On a Gear or
  Weapon entry that means the item occupies at least one hand or arm; on a
  Stance entry it means the pose needs both hands free. Stance is rolled
  after Gear and filtered against it, so an NPC never ends up holding
  something in both hands while standing with those hands in their pockets.
  Tag any new bullet the same way — an untagged one is treated as hands-free.
- **Weapon** and **Stance** bullets may also carry `|| gun`. On a Weapon
  entry that marks the item as an actual firearm held in hand; on a Stance
  entry it marks a pose that describes aiming, firing or otherwise handling
  a weapon — one the Weapon roll has to supply, so a gun pose is never
  rolled for an NPC whose Weapon roll came up empty or something pocketable.
  A bullet can carry both flags at once, `|| hands gun`. Stance poses that
  reference a weapon do so generically — "raising it", "sighting down it" —
  since the Weapon line earlier in the prompt has already named the specific
  weapon; naming it twice would just contradict itself if the two ever
  disagreed.
- **Backdrop** bullets carry three segments: the shot's opening phrase, the
  scene sentence, then optional flags. There are two: `nogear` and `weather`,
  and a bullet may carry both — `|| nogear weather`. `weather` marks a scene
  as outdoors, so a Weather roll can be dropped into it. `nogear` marks a
  scene that already puts something in the subject's hands, and has two
  effects: it drops the whole merged Weapon+Gear "carries ..." sentence from
  the portrait (the token keeps it, since the token has no scene to
  contradict), and it also keeps the Gear roll itself off any bullet flagged
  `|| hands` — so a `hands`-flagged Gear bullet you add will never turn up
  paired with a `nogear` scene. The comment above that table has the rest.
- **Hair colour** bullets carry three segments as well — the colour itself,
  then an optional trailing clause, then optional flags. The first fills the
  `{colour}` slot that every `## Hair` bullet carries, which is why colour and
  cut are separate rolls: a new shade is one bullet here rather than a rewrite
  of every cut. The second is for gradients, which read wrongly in adjective
  position and correctly as a clause hung off the end of the whole cut phrase
  — flat colours leave it empty. The only flag is `older`, which drops that
  colour when the Age roll came up `young`, the same pairing `figure` has:
  greying hair asserts an age the Age clause in the same prompt would
  contradict. A colour with a flag but no trailing clause writes the middle
  segment empty, `greying || || older`.
- **Weather** bullets may end `|| clear`, meaning the bullet contributes nothing
  to the prompt. Weather only reaches a portrait whose Backdrop is flagged
  `weather`, and never reaches the token at all.
- **Role** bullets may end `|| mil`, marking that occupation as active-duty
  military or paramilitary — a soldier, pilot, medic, comms operator or the
  like. It gates the Faction, Outfit and Gear rolls that follow it, because a
  civilian may carry any gear or weapon they like, including military-issue
  ones, but shouldn't turn up in a duty uniform, while a military NPC should
  almost always be in one and armed. **Faction** and **Outfit** bullets may
  in turn carry `|| civ` or `|| mil`: `civ` reads as plainly civilian dress
  and is dropped from the pool for a `mil` Role, `mil` reads as an actual
  issued uniform and is dropped for a civilian (unflagged) Role instead. A
  bullet with neither flag is neutral and reachable either way — most Outfit
  entries stay this way, the same as a build or gear item with no flag at
  all. **Gear** and **Weapon** bullets may also carry `|| mil`, marking the
  item as military-issue — equipment on a Gear entry, an actual issued
  weapon on a Weapon entry, since every bullet in that table already reads
  as one.

  Three more flags, plus one on Outfit, are read by `apply_weapon_policy()`
  rather than by the civ/mil split above — see the comments on the Weapon
  and Outfit tables themselves for the full detail: `weapon` (an actual
  weapon, as opposed to equipment that's merely `mil`), `simple` (a `weapon`
  small and pocketable enough for a role that should rarely be armed), and
  `sidearm` (a bullet that explicitly includes a holstered or worn pistol).
  All three now live on `## Weapon`, not `## Gear`. A `mil` Role's Weapon
  roll is restricted to `sidearm`-flagged bullets — always armed with at
  least a holstered pistol, not just usually — with the pistol+rifle
  compound bullets weighted heavier so a rifle on top of it is the common
  case rather than the rare one. Outfit's `notac` keeps a handful of
  elaborate or traditional outfits (a kimono, shrine robes) from ever
  pairing with `mil`-flagged Gear.

A flag beginning `@` is a **theme tag** rather than a behavioural flag —
`|| civ @neosamurai` reads as "civilian dress, belonging to the neosamurai
look". The `Theme` table is rolled once per NPC before any appearance table,
and a rolled theme opens its own tagged bullets plus every **untagged** one,
excluding bullets tagged with a different theme. A bullet may carry more than
one tag and is then reachable from either. An untagged bullet is neutral and
reachable from every theme — most bullets in this file are, and should stay
that way; tag only what is strongly of one look.

A theme tag is read on **seven tables and seven only**: `Hair`, `Hair
colour`, `Feature`, `Outfit`, `Headgear`, `Weapon` and `Backdrop`. `Gear` is
deliberately not one of them - it split away from `Weapon` because it isn't
theme-defining. Anywhere else it does nothing — the theme filter never looks
at that table — and on the tables whose bullets carry no `||` segment at all,
it is worse than nothing: `Skin`, `Eyes`, `Demeanor`, `Accent`, `Height` and
the name tables are never split, so their text is dropped into the prompt
exactly as written. A bullet reading `- chrome-inlaid irises || @cyberpunk`
under `## Eyes` would ship the literal text `|| @cyberpunk` to the image model
and print it in the dossier. Tag one of the seven, or leave the bullet
neutral; `test/test_theme_tag_placement.py` fails the moment a tag lands
anywhere else.

Flags are matched literally and an unrecognized one is ignored rather than
reported, so `|| Figure` or `|| hand` reads as no flag at all — which fails
quietly in the render rather than loudly at the console. Copy the spelling from
a neighboring bullet.

A bullet may also contain a pronoun placeholder, filled from the same roll.
That is how the Age table reads "in her forties" or "in their forties" without a
separate table per pronoun set. The full set is:

| Placeholder                               | Fills with                                                  |
| ----------------------------------------- | ----------------------------------------------------------- |
| `{subject}` / `{object}` / `{possessive}` | she / her / her                                             |
| `{Subject}` / `{Possessive}`              | Sentence-initial forms. There is no `{Object}`.             |
| `{is_are}` / `{carry}` / `{wear}`         | Verb agreement, so they/them bullets read correctly.        |
| `{gender}`                                | The noun the prompt calls the subject — woman, man, person. |

A placeholder that isn't on this list raises an error naming the bullet, so a
typo fails loudly rather than reaching a prompt.

Where a placeholder isn't enough, a table can have a **per-pronoun variant**,
in one of two forms:

- `<Table> (she)` is used **instead of** `<Table>` when she/her is rolled.
  `Build (she)` works this way, because the masculine builds should not apply
  at all.
- `<Table> (she) +` is **added to** `<Table>`, so a woman can roll any of the
  neutral options as well as the feminine ones — a woman in grey coveralls
  stays entirely possible. Most variants are this form.

`(he)` and `(they)` variants work identically. Rather than listing which tables
currently have one, look at the `##` headings below: every variant that exists
is a heading of its own, so scanning the table of contents of this file is the
list, and it cannot go stale.

Whatever stays in a base table is meant to be genuinely neutral, so when a
bullet only makes sense on one gender, move it into that gender's variant rather
than leaving it in the shared pool. The script has no idea which traits are
gendered, so adding a new variant needs no code change — drop the heading in
and it is picked up. The one exception is `GENDER_TRAITS` in
the script, a short clause asserted for every woman rather than rolled for —
see the Prompt templates section below. Weights apply inside variant tables too, which is the dial
for how often a gendered option comes up.

HTML comments, blank lines, and any prose paragraph that isn't a bullet are
ignored — so notes like this one are safe to leave inline.

---

## Given names

- Adaeze
- Anselm
- Arden
- Ari
- Ariane
- Aster
- Aven
- Ayodele
- Beatriz
- Cael
- Cai
- Camille
- Ciel
- Cyr
- Dalen
- Dmitri
- Eleni
- Eren
- Esperanza
- Fen
- Gabriel
- Hana
- Idris
- Ingrid
- Isabela
- Jae-won
- Jules
- Junia
- Kasimir
- Kest
- Kestrel
- Kiran
- Kwame
- Lior
- Lucia
- Mahmoud
- Maren
- Marisol
- Nadia
- Niko
- Nkechi
- Oksana
- Osric
- Priya
- Quintus
- Rashida
- Ren
- Rian
- Riven
- Rosalind
- Sable
- Sanjay
- Selin
- Sipho
- Soren
- Tamsin
- Tarin
- Thandiwe
- Tobias
- Ulla
- Valentina
- Varen
- Vesper
- Vey
- Wen
- Xiulan
- Yusuf
- Zaid
- Zora

## Given names (she) +

<!--
  '+' means these are added to the Given names table rather than replacing it,
  so a woman can still roll any of the neutral names above.
-->

- Alina
- Amara
- Astra
- Calia
- Cyra
- Elara
- Eris
- Ilyra
- Ivara
- Kaia
- Lena
- Liora
- Maelin
- Mara
- Naya
- Neris
- Nyra
- Rhea
- Selene
- Sera
- Seren
- Talia
- Thessa
- Vera
- Veya

## Given names (he) +

- Adrian
- Aren
- Cassian
- Corvin
- Darian
- Dax
- Elias
- Evren
- Jonas
- Joren
- Kael
- Kellan
- Luc
- Lucan
- Marek
- Milo
- Silas
- Tavian
- Theron
- Viktor

## Family names

- Abara
- Achterberg
- Adeyemi
- Aras
- Baptiste
- Beaumont
- Cade
- Calder
- Castellan
- Chaudhry
- Dalisay
- Delacroix
- Egwuatu
- Farkas
- Fontaine
- Gao
- Hale
- Halvorsen
- Ibarra
- Ikeda
- Jarrah
- Kade
- Kalu
- Karras
- Kess
- Kreel
- Lindqvist
- Machado
- Marchetti
- Mbeki
- Nakamura
- Okonkwo
- Orin
- Ors
- Oyelaran
- Petrov
- Quintero
- Rahimi
- Rane
- Renn
- Reyes
- Rook
- Sandoval
- Sarkisian
- Sokolova
- Sol
- Solvek
- Sorn
- Tanaka
- Thorne
- Ubeda
- Vale
- Varr
- Vasquez
- Venn
- Vey
- Veyran
- Veyre
- Volkov
- Vos
- Voss
- Whitlock
- Xu
- Yildirim
- Zabala

## Callsigns

<!--
  Used in the dossier, not in the art prompts.

  The '###' group headings below are for human eyes only - the parser reads a
  table from '##' to the next '##', so every bullet here is one flat pool and
  the groups do not affect the roll. They are here so a whole tone can be
  weighted or cut in one pass. Deleting the Comedic block, for instance, drops
  Steve and Wi-Fi without touching anything else.
-->

### Nautical / old-trade

- Ash
- Bellwether
- Bramble
- Cinder
- Cormorant
- Dogwatch
- Driftwood
- Eightball
- Ferryman
- Fixture
- Gallows
- Halfmast
- Hollow
- Ironmonger
- Kestrel
- Lantern
- Lodestar
- Magpie
- Nightjar
- Offcut
- Pallbearer
- Quarry
- Ratchet
- Redline
- Saltwater
- Shrike
- Sixpence
- Slipstream
- Tinder
- Undertow
- Verdigris
- Waypoint
- Whetstone
- Yardarm

### Military / professional

- Aegis
- Anvil
- Atlas
- Bastion
- Bishop
- Bulwark
- Coyote
- Fox
- Ghost
- Glaive
- Hammer
- Havoc
- Hound
- Jackal
- Knight
- Lance
- Lancer
- Mace
- Maverick
- Overwatch
- Palisade
- Phantom
- Rampart
- Raptor
- Reaper
- Rook
- Sentinel
- Spear
- Specter
- Striker
- Talon
- Vanguard
- Viper
- Vulture
- Warden
- Wolf
- Wraith

### Aggressive

- Aftershock
- Blackout
- Bloodhound
- Breach
- Breakneck
- Buckshot
- Burnout
- Cataclysm
- Crash
- Crusher
- Deadlock
- Detonator
- Extinction
- Graves
- Grim
- Grinder
- Killswitch
- Malice
- Mauler
- Overkill
- Razor
- Reckoning
- Rend
- Ripper
- Ruin
- Scorch
- Shatter
- Siege
- Slag
- Sunder
- Trigger
- Warpath
- Wrath
- Wreck

### Stealth / recon

- Afterimage
- Blackglass
- Blindspot
- Crow
- Darkstar
- Dead Air
- Drifter
- Echo
- Flicker
- Hush
- Lynx
- Mirage
- Moth
- Nightfall
- Null
- Owl
- Prowler
- Raven
- Shade
- Shadow
- Silence
- Stalker
- Static
- Veil
- Whisper
- Wisp
- Zero

### Hacker / tech

- 404
- AFK
- Backdoor
- Backtrace
- Bitrot
- Blue Screen
- Botnet
- Checksum
- Cipher
- Ciphertext
- Daemon
- Exploit
- Failsafe
- Fork
- Glitch
- Hash
- Heap
- Kernel
- Kernel Panic
- Killbit
- Loop
- Override
- Packet
- Paradox
- Payload
- Ping
- Process
- Proxy
- Race Condition
- Recursive
- Root
- Rootkit
- Sandbox
- Segfault
- Stack
- Thread
- Zero-Day

### HORUS-adjacent

- Angel
- Answer
- Anyone
- Bad Idea
- Black
- Bone
- Devil
- Do Not Open
- Doll
- Error
- Event Horizon
- Everyone
- Flesh
- God
- God.exe
- Knife
- Marionette
- Meat
- Mirror
- Mothman
- Mouth
- No One
- Nobody
- Oracle
- Problem
- Prophet
- Puppet
- Question
- Rabbit
- Red
- Saint
- Seraph
- Sinner
- Skin
- Solution
- Somebody
- Teeth
- The Algorithm
- The Other
- The Passenger
- The Thing
- The Voice
- Undefined
- Unknown
- Unperson
- White
- Witness
- Works On My Machine
- Worm

### Cosmic

- Aphelion
- Blueshift
- Burn
- Comet
- Corona
- Deepfield
- Drift
- Eclipse
- Escape Velocity
- Eventide
- Farpoint
- Gravity
- Horizon
- Lightcone
- Luna
- Meteor
- Nova
- Orbit
- Perihelion
- Pulsar
- Quasar
- Redshift
- Singularity
- Sol
- Solstice
- Starfall
- Starlight
- Terminus
- Umbra
- Vacuum
- Vector
- Void
- Wayfarer
- Zenith

### Pilot reputation

- Again
- Bad Luck
- Black Cat
- Close Call
- Dead Reckoning
- Deadeye
- Ghost Story
- Hard Reset
- Hardcase
- Kid
- Last Chance
- Last One
- Longshot
- Loose Cannon
- Lucky
- Lucky Seven
- Missed Me
- Near Miss
- Nevermind
- Nine Lives
- No Refunds
- Old Man
- One Shot
- Out of Ammo
- Problem Child
- Rabbit's Foot
- Respawn
- Second Wind
- Seven
- Still Here
- The Survivor
- Third Time
- Thirteen
- Two-Times
- Unkillable
- Unlucky
- Walking Away
- Wrong Way

### Comedic

- Accountant
- Audit
- Batteries
- Big Gun
- Blue on Blue
- Bluetooth
- Child Support
- Collateral
- Compliance
- Critical Error
- Customer Service
- Dad
- Dave
- Divorce
- Don't Worry
- Freebird
- Friendly Fire
- HR
- Intern
- It's Fine
- Kevin
- Legal
- Lunchbox
- Management
- Medium Gun
- Microwave
- Mom
- Mortgage
- My Bad
- Not Me
- Oops
- OSHA
- Printer
- Probably Fine
- Procurement
- Rent
- Skill Check
- Skill Issue
- Small Gun
- Steve
- Taxman
- Tech Support
- The Intern
- Toaster
- Trust Me
- Tuesday
- Warranty
- Wasn't Me
- Whoops
- Wi-Fi
- Witness Protection

### Futuristic

- Anathema
- Apostle
- Axiom
- Causality
- Coldstar
- Continuum
- Convergence
- Deadlight
- Divergence
- Eidolon
- Entropy
- Faraday
- Ghostline
- Halcyon
- Hardlight
- Heretic
- Iconoclast
- Invariant
- Lucid
- Memento
- Meridian
- Mnemonic
- Nightwire
- Oblivion
- Palimpsest
- Parallax
- Pariah
- Revenant
- Silverline
- Starling
- Threshold
- Vestige
- Wayline

## Pronouns

<!--
  Subject/object/possessive/noun; the script splits on the slashes.

  The fourth field is the noun the image prompt uses for the subject - "a fully
  grown adult woman in her forties". Pronouns alone were not a strong enough
  signal and tokens came back androgynous, so the prompt now states it outright.

  Drop the fourth field and it is inferred from the subject pronoun (she ->
  woman, he -> man, anything else -> person), so old three-field bullets and
  '--set-trait Pronouns=she/her/her' still work.

  A they/them/their/person set used to live here. It's gone - the fourth-field
  noun "person" wasn't a strong enough signal on its own, and the renders came
  back visibly androgynous/inconsistent rather than reading as a coherent look.
-->

- she/her/her/woman
- he/him/his/man

## Theme

<!--
  The visual world this NPC comes from, rolled once and honoured by every
  appearance table. This is what makes a rolled NPC read as one coherent
  character rather than a bag of independently-rolled traits.

  A bullet here is a bare name; appearance bullets refer to it with an '@'
  prefix in their flag segment - '|| civ @neosamurai'. A rolled theme opens
  its own tagged bullets plus every untagged one, and excludes the rest.

  Theme is deliberately independent of Role: a pirate is as likely to look
  neosamurai as cyberpunk. Do not gate one on the other.

  Weights start proportional to how much content each theme has, so a thin
  theme is rare rather than repetitive. Raise a weight as you author more -
  it needs no code change. The intended end state is roughly equal weights.

  There is deliberately no 'grounded' entry: the untagged bullets throughout
  this file already are the worn-industrial Lancer look, and they serve as the
  neutral floor every theme draws from rather than competing as a ninth theme.
-->

- x6 gundam
- x6 tactical
- x6 neosamurai
- x4 cyberpunk
- x2 neogothic
- grimdark
- corporate
- scav

## Age

<!--
  A bullet flagged 'young' is an NPC under twenty. The flag does two things in
  the script, because an age alone was not enough to move the render:

    1. It swaps the prompt's opening "a fully grown adult" for "a young", and
       the portrait's "mature adult facial structure" clause for a young one.
       Both templates otherwise assert an adult outright, in the highest-signal
       position in the prompt, and the model believed the assertion over the
       age - "a fully grown adult woman in her late teens" rendered as a woman
       in her thirties every time.

    2. It rules out the Build bullets flagged 'figure'. Those describe an adult
       one - bust, hips, curves - and must never be hung on a teenager. See the
       note on Build (she).

  Weights keep the roster mostly adult: these are soldiers, technicians and
  officers, so a late-teen NPC should read as the youngest person in the room
  rather than the median.
-->

- in {possessive} late teens, sixteen or seventeen, face still soft and unlined || young
- x2 just nineteen, newly in uniform and still growing into it || young
- x2 in {possessive} early twenties, jaw and cheekbones fully adult
- x2 twenty-one or twenty-two, fully grown for a couple of years now, the face still unlined and unweathered
- x3 in {possessive} mid-twenties, fully grown but not yet weathered
- x2 in {possessive} late twenties, jaw and cheekbones fully adult
- x3 in {possessive} early thirties, the first lines already setting around the eyes
- x2 in {possessive} mid-thirties, face lean and weathered
- in {possessive} forties, grey coming in at the temples
- in {possessive} fifties, weathered but unslowed, deeply lined
- in {possessive} sixties, face deeply creased, old enough that the war stories are first-hand

## Build

- x2 lean and wiry, all long limbs
- x2 solidly built through the chest and shoulders
- broad-shouldered and heavyset, a full head taller than most
- tall and rangy, stooping out of habit through low hatchways
- thickset and heavy-boned, built like someone who moves cargo
- rawboned and gaunt to the point of looking underfed
- heavy through the middle and soft-handed, plainly not a field operator

## Build (she)

<!--
  A per-pronoun variant table: because this heading is "Build (she)", it is used
  instead of "Build" whenever the rolled pronoun set is she/her. The range from
  overtly feminine to lean and androgynous lives inside the table, so how often
  a woman reads strongly feminine is tuned by editing weights here rather than
  in the script.

  The weights lean hard toward lean, fit and athletic frames. The heavier
  entries are left in at weight 1 apiece so the roster is not uniform, but they
  come up rarely - a heavy build also tends to disagree with the portrait, which
  is framed too close to show the body and so always reads slim.

  The 'figure' flag marks a bullet that describes an adult woman's figure -
  bust, hips, waist, curves. Those are dropped from the pool whenever the Age
  roll came up flagged 'young', so a teenage NPC is never described in those
  terms. Flag any new bullet that names one of those, and leave it off the ones
  that describe frame and conditioning alone; the unflagged entries are what a
  late-teen NPC rolls from, so keep enough of them to stay varied.
-->

- x3 lean and athletic, narrow-hipped and small-busted || figure
- x3 slim and fine-boned, light through the shoulders and hips || figure
- x2 athletic and fit, narrow waist and extremely large breasts || figure
- x2 lithe and slender, with fine shoulders and a long neck
- x2 trim and toned, flat through the midsection with defined shoulders
- x2 tall and rangy, long-limbed and narrow through the waist
- x2 compact and athletic, short and densely muscled
- x2 wiry and hard-trained, visibly strong without being bulky
- broad-shouldered and muscular, carrying obvious strength
- tall and statuesque, long-legged and narrow-waisted || figure
- slender but full-busted, with a clearly defined waist || figure
- sturdy and thickset through the shoulders and hips || figure

## Height

<!--
  A full replacement table for she/her the same way Build (she) is - see
  Height (she) below - so the two distributions can be tuned independently
  rather than fighting over one shared pool. The brief: women read fairly
  tall, only slightly shorter than men on average, and this table (like
  Build) skews the whole roster taller than a real-world average on purpose -
  it's a painterly action-adventure cast, not a demographic sample.
-->

- x3 tall, standing several inches over six feet
- x4 a solid six feet even
- x3 just under six feet, average height for the line of work
- x2 five foot ten or so, on the shorter side but still solid
- broad and towering, close to six and a half feet
- compact, a shade under five foot nine, built to fit tight spaces

## Height (she)

- x2 tall, standing just a few inches under six feet
- x4 a solid five foot nine or so
- x3 five foot seven, average height and unremarkable
- x2 five foot five, on the shorter side but not short
- statuesque, brushing six feet even
- compact and small, a shade over five feet

## Skin

- deep brown skin
- warm brown skin
- olive-toned skin
- light brown skin
- pale skin
- sun-darkened, weather-roughened skin
- sallow skin with the grey cast of too long under artificial light

## Hair

- close-cropped {colour} hair
- a shaved head with {colour} stubble and old surgical scarring at the temple
- long {colour} hair pulled back in a practical braid
- an untidy mop of {colour} curls
- {colour} hair cut short and severe
- shoulder-length {colour} hair, half of it dyed a faded synthetic color
- a tight coil of {colour} locs gathered at the nape
- a slicked-back {colour} corporate cut, not one strand out of place
- {colour} hair hacked off short and uneven, clearly self-cut
- long {colour} hair worn loose and unkempt, shoved back out of the face
- a high, tight {colour} topknot
- {colour} hair tied back in a short tail
- a wrapped headscarf with a few {colour} strands escaping at the temple
- a choppy shoulder-length {colour} cut
- {colour} wavy hair caught mid-motion in the wind
- a short choppy {colour} cut, spiky and layered at the crown, long bangs falling loose across the brow
- a wild untamed mane of {colour} hair, layered in heavy flicks that sweep back and outward, long strands falling either side of the face
- long {colour} hair worn loose past the shoulders, a heavy fringe hanging over one eye and a single stray strand standing up at the crown
- shoulder-length {colour} hair with a loose wave through it, swept back off the face and tucked behind one ear
- loose {colour} hair falling past the shoulders and caught by the wind, a small metal clip holding one side back
- long {colour} hair falling past the shoulders, cut with sharp jagged bangs across the brow

## Hair (she) +

<!--
  '+' means these are added to the Hair table rather than replacing it, so a
  woman can still roll any of the neutral cuts above.
-->

- long {colour} hair spilling loose over the shoulders in soft waves
- an elaborate crown of {colour} braids pinned close to the head
- a sleek {colour} bob cut level with the jaw
- a long {colour} ponytail pulled through the back of a worn cap
- {colour} hair swept up in a loose bun already falling apart
- twin {colour} braids tied off with frayed cord
- a short {colour} bob with long bangs swept across one eye
- long {colour} hair worn loose, a few strands falling across the face
- long {colour} hair spilling well past the shoulders, pushed back off the brow
- {colour} hair
- a chin-length {colour} cut with sharply angled bangs
- long {colour} hair loose on one side and cropped short above the other ear
- a heavy {colour} braid falling past the shoulder
- fine {colour} hair cut level with the jaw
- thick {colour} hair pinned up off the collar
- a short {colour} bob with a single bright-streaked forelock
- long {colour} hair
- long {colour} hair, cut with blunt bangs
- a short {colour} bob with a loose curling cowlick
- a short {colour} bob left deliberately choppy, the ends spiked and uneven, long bangs swept across one eye
- a high {colour} ponytail tied off loose and messy, long strands left free either side of the face
- {colour} hair worn poker-straight and very long, falling well past the waist, a long fringe swept down one side of the face
- a chin-length {colour} bob with a straight-cut fringe
- a {colour} bob swept low across one eye
- a long {colour} double braid falling past the waist
- {colour} hair cut in a blunt chin-length bob with heavy straight bangs
- a long {colour} twin-tail, loose strands pulled forward across one shoulder
- a messy {colour} topknot, one side shaved close beneath it
- a long single {colour} braid, loose strands escaping at the crown
- {colour} hair gathered into twin space buns, loose strands falling free at the temples
- a high {colour} ponytail, choppy bangs falling across one eye
- a {colour} bob with a sharp side-swept fringe and a single streaked strand
- a {colour} bob with a pair of small horn-shaped ornamental clips swept back at the temples
- a {colour} bob with a blunt fringe
- twin high {colour} ponytails held back by the band of a chunky headset, a long fringe swept across one brow
- twin high {colour} ponytails clipped at the base by a segmented mechanical binder, sweeping loose past the shoulders
- shoulder-length {colour} hair, center-parted with a long face-framing fringe
- {colour} hair swept back into a neat low bun, held with a single ornamental pin
- {colour} hair swept up in a bun crowned with a floral hairpin ornament, loose strands and bangs falling forward across the brow
- {colour} hair swept up into a high bun, secured with ornamental pins and a trailing ribbon
- {colour} hair swept up, an ornamental flower and dangling metal pins gathered at the crown

## Hair (he) +

<!--
  The masculine counterpart, additive the same way — a man can still roll any
  of the neutral cuts above.
-->

- {colour} hair
- a close {colour} fade with a longer sweep left on top
- {colour} hair cropped close
- a high-and-tight {colour} regulation cut, sidewalls shaved to the skin
- a hairline well back at the temples, what is left of the {colour} hair kept clipped short
- thick {colour} hair swept back off the brow, a shade too long for regulation

## Hair colour

<!--
  Rolled separately from the cut, so colour varies independently and a new
  shade is one bullet here rather than a rewrite of every cut.

  THREE segments, not two: 'base || tail || flags', the same shape ## Backdrop
  uses. The base fills the '{colour}' slot inside the rolled Hair bullet; the
  optional tail is appended after the whole cut phrase, separated by a comma.
  That is what makes gradients work - they read wrongly in adjective position
  ("a sleek silver-white fading to green at the tips bob") and correctly as a
  trailing clause ("a sleek silver-white bob cut level with the jaw, fading to
  green at the tips"). Flat colours leave the tail empty.

  A colour with flags but no tail writes its middle segment empty:
  'greying || || older'. Slightly awkward, and the price of one table.

  The 'older' flag drops that colour when the Age roll came up 'young',
  mirroring the 'figure'/'young' pairing exactly. Greying hair asserts an age,
  and rolling it onto a teenager contradicts the Age clause in the same prompt.

  Write a base that reads correctly in adjective position, because that is
  where most cuts put it - "close-cropped {colour} hair", "a sleek {colour}
  bob". Anything that only works as a trailing clause belongs in the tail.

  Start a base with a CONSONANT. Four Hair bullets put the slot straight after
  an article - "a {colour} bob with a blunt fringe" - and nothing in the script
  fixes 'a' to 'an', so a vowel-initial base renders "a auburn bob" into the
  Krea prompt and the dossier. That is why the two shades here that would begin
  with one are written "dark auburn" and "pale ash-blonde" rather than bare.
  Qualify a new one the same way, or the failure is silent.

  Weights keep the roster mostly naturalistic: this is a setting of soldiers
  and technicians, so dyed and gradient shades should read as the striking one
  in the room rather than the median. The plain browns, blacks and blondes
  carry the heavy weights; the synthetic shades and the handful of entries
  with a tail are single-weight and come up rarely.

  A tail describes the ends or the underlayer of the hair, so it can strain
  against a cut that has neither - a shaved head does not have tips to fade
  at. Keeping the tails to five single-weight entries is what holds that
  pairing down to about one NPC in a hundred; adding more, or weighting them
  up, makes it common enough to need a flag rather than a weight.
-->

- x6 black
- x4 jet black
- x3 near-black
- x6 dark brown
- x4 dark
- x4 brown
- x3 light brown
- x3 chestnut
- x3 mousy brown
- x2 warm reddish-brown
- x3 pale ash-blonde
- x3 sandy blonde
- x2 honey-blonde
- x2 dark blonde
- x2 dirty-blonde
- x3 dark auburn
- x2 copper-red
- dark red
- x2 silver-grey
- x2 white
- platinum
- silver-white
- x2 greying || || older
- x2 salt-and-pepper || || older
- sandy || going prematurely white at the temples || older
- teal
- pale lavender
- pale mint-green
- pale seafoam-green
- dusty pink
- magenta-tinted black
- two-tone || dark over a bleached pale underlayer
- pale silver-white || fading to green at the tips
- fiery orange-red || fading to dark roots
- dirty-blonde || fading pale at the tips

## Eyes

- dark, steady eyes
- pale grey eyes that give nothing away
- one eye replaced by a matte optical implant with a faint glowing aperture
- deep-set eyes ringed with fatigue
- bright hazel eyes, quick and reading everything
- narrow eyes half-lidded in permanent skepticism
- eyes clouded by an old flash-burn, scarred at the lids
- warm brown eyes, quick to crease at the corners
- pale green eyes, cold and evaluating
- heavy-lidded eyes that make everything look like an imposition
- amber-brown eyes catching the light
- mismatched eyes, one brown and one pale blue
- eyes hidden behind scratched tinted lenses
- glowing red cybernetic eyes
- sharp gold eyes
- mismatched eyes, one pale blue-grey and the other a deep wine red
- one eye a natural brown, the other a lens-bright replacement in a mismatched color
- striking violet eyes, unusually pale
- ice-blue eyes, almost colorless at the rim
- sharp red eyes
- deep blue eyes, dark as ink toward the rim
- copper-orange eyes with a warm metallic sheen
- storm-grey eyes shading to blue at the edge
- eyes of a flat synthetic green, plainly not the originals

## Eyes (she) +

- dark eyes with long lashes, steady and level
- expressive eyes ringed in smudged black liner
- bright eyes beneath sharply arched brows
- large dark eyes with a faint violet cast to them
- keen eyes of a clear emerald green

## Feature

- a spray of old burn scarring up one side of the jaw
- a faded unit tattoo on the side of the neck
- a printed prosthetic forearm, its casing scuffed back to bare polymer
- a broken nose set badly and never corrected
- subdermal port housings tracked along the temple and collarbone
- a jagged shrapnel scar crossing one eyebrow
- knuckles thickened by years of manual work
- no distinguishing marks at all, which is itself a little strange
- a heavy scar seaming one forearm from wrist to elbow
- a chipped front tooth
- a permanent squint worn in by years of glare
- deep laugh lines bracketing the mouth
- a stark white streak through the hair from an old head wound
- ink-stained fingertips that never quite wash clean
- a compact armored gauntlet on one forearm with a small glowing sensor ring
- both arms mechanical cybernetic prosthetics, tan and cream, heavily articulated with visible joints, wiring and battle-damage scuffing
- both legs sleek mechanical prosthetics with exposed joints and a small lit panel at the thigh
- one sleek segmented prosthetic arm, a single small glow breaking through at the joint
- visible mechanical seams and joint lines across the shoulders, marking {object} as a cyborg
- thin tear-like markings traced beneath both eyes
- a small barcode stamped at the collarbone
- a diagonal scar cutting clean across one eye
- a gauze patch taped over one eye, the rest of the face unmarked
- a cybernetic optic implant wired into one side of the face, fine conduit lines tracing down past the jaw to the collar
- a synthetic shoulder casing peeled back at a seam, exposing internal wiring and structural framework beneath

## Feature (she) +

- a fine gold chain at the throat, the only thing on {object} not issued
- small hoop earrings worn thin and dented
- chipped dark polish on bitten nails
- a delicate line of old piercings climbing one ear
- a faded floral tattoo curling over one shoulder
- a wedding band worn on a cord rather than a finger
- a faint scatter of freckles across the bridge of the nose
- visible mechanical rib plating and joint segments across the bare midriff, marking {object} as heavily augmented
- faint surgical scarring tracing from temple to cheekbone, the mark of old cyberware work

## Feature (he) +

<!--
  '+' means these are added to the Feature table rather than replacing it, so a
  man can still roll any of the neutral marks above.
-->

- x2 permanently a few days past a decent shave
- a close-trimmed beard going grey at the chin
- a heavy moustache, grey at the edges

## Headgear

<!--
  Complete sentences, like Backdrop - a fragment would not sit cleanly between
  the outfit clause and the expression. Roughly a third of rolls come up
  bare-headed; reweight that first bullet to change how often headgear shows.
-->

- x6 {Subject} {is_are} bare-headed.
- x2 {Subject} {wear} a padded flight headset, earcups clamped over the ears and a boom mic swung down to the corner of {possessive} mouth, a coiled cable trailing from one side.
- {Subject} {wear} a lightweight comms earpiece with a slender mic arm tracking along the jaw.
- {Subject} {wear} scratched flight goggles pushed up onto {possessive} forehead.
- {Subject} {wear} a soft crew cap pushed back on {possessive} head.
- {Subject} {wear} a padded pilot skullcap with the visor unclipped and folded back.
- {Subject} {wear} a rolled bandana tied across {possessive} brow.
- {Subject} {wear} a knitted watch cap pulled down to the eyebrows.
- {Subject} {wear} a composite ballistic helmet with its rail-mounted visor hinged up.
- {Subject} {wear} a full flight helmet in scuffed pale grey-white, a tinted visor panel down over the eyes and a small lit accent lens at the temple, a thin tether cable trailing from the back.
- {Subject} {wear} a monocular sensor rig strapped over one eye, its lens faintly lit.
- {Subject} {wear} heavy ear defenders slung around {possessive} neck rather than on {possessive} head.
- {Subject} {wear} a welding visor tipped back on top of {possessive} head.
- {Subject} {wear} a worn ushanka-style fur hat with the flaps down, a faded unit star pinned to the front.
- {Subject} {wear} a tactical cap with a small circular unit emblem, dark sunglasses beneath it.
- {Subject} {wear} a night-vision helmet with the quad tubes flipped up clear of {possessive} eyes.
- {Subject} {wear} a sleek black mechanical headset piece mounted flush against one ear.
- {Subject} {wear} a stiff peaked officer's cap, the brim polished and a small insignia set at the crown.
- {Subject} {wear} a hooded shroud drawn up over a full-face helmet, its visor tinted dark and a breather mask sealed across the lower face.
- {Subject} {wear} a deep hood drawn up, a pair of goggles clipped across the brow of it.
- {Subject} {wear} a flat-brimmed ball cap with a small stitched patch at the front.
- {Subject} {wear} an open-face crash helmet with the visor swung up clear of {possessive} eyes.
- {Subject} {wear} a ballistic helmet with its visor tipped up and a black breather mask sealed over the lower face.
- {Subject} {wear} a russet leather flight cap with ear flaps and a monocular scanner lens fixed down over one eye.
- {Subject} {wear} a wide woven sedge hat, its brim throwing {possessive} face into shadow.
- {Subject} {wear} a pale cloth wrapped loosely over the lower face beneath a wide straw hat.
- {Subject} {wear} a sleek integrated visor plate curving back over one ear, thin cable jacks seated at the jaw and temple, a faint accent light glowing along its edge.
- {Subject} {wear} a bulky visored rig clamped down over the eyes, a stub antenna and a cluster of cable jacks rising from the crown, a single indicator light glowing beneath the visor's edge.
- {Subject} {wear} a gold-trimmed headset clamped over one ear, a coiled cable trailing from it down past {possessive} collar.
- {Subject} {wear} a sleek pilot's helmet with a curved visor, faint HUD readouts scrolling across the inside of the glass and a stencilled call-sign plate set at the jaw.
- {Subject} {wear} round wire-rimmed glasses, their lenses lit faintly at the edges with a soft glow.
- {Subject} {wear} a scuffed recon helmet with a stubby antenna and an integrated comm mic curling to the jaw, cable jacks trailing from the crown to a collar rig.
- {Subject} {wear} a bulky illuminated visor rig clamped low over the eyes, graffitied casing and a stub antenna rising from one side.
- {Subject} {wear} a curved white plate clipped snug over one ear, a short antenna-like horn rising from its crown and a thin cable trailing to the collar.
- {Subject} {wear} a sleek red-tinted visor strapped low across the eyes, built into a close-fitted skullcap with a jack seated at one temple.
- {Subject} {wear} a compact over-ear headset with red accent panels, a short boom mic curling toward the jaw.
- {Subject} {wear} a pair of boxy retro-industrial headphones, worn olive-grey earcups ringed in exposed rivets and a scuffed control dial on one side.
- {Subject} {wear} tinted wraparound sunglasses pushed rakishly up into {possessive} hair.
- {Subject} {wear} a segmented cybernetic implant sheathing one ear and running down the jaw, faint lit seams tracing its joints.
- {Subject} {wear} a domed flight helmet in weathered burnt-orange with a full mirrored visor down, a coiled comms cable trailing from one side.
- {Subject} {wear} a compact visor rig pushed up above the brow, articulated plating framing one side of the face and a thin mic boom curving down past the cheek.
- {Subject} {wear} a compact sensor rig clipped into {possessive} hair at the crown, trailing thin cables and a torn strip of fabric like a streamer.
- {Subject} {wear} a slim translucent visor band across the brow, a cluster of cabling running from a port at {possessive} temple back into the rig behind {object}.
- {Subject} {wear} a chunky over-ear headset with a lit accent ring at each cup, the band nested into {possessive} hair.
- {Subject} {wear} a red-plated visor rig clamped down over the eyes, twin lens apertures lit faintly, a cluster of thin cables trailing back into {possessive} hair.
- {Subject} {wear} a sleek visored headset clamped over the eyes, a hinged jaw guard sealed below it and a cluster of thin cables trailing back into {possessive} hair.
- {Subject} {wear} a segmented white cybernetic headpiece clamped over the crown and one temple, faint cable jacks seated at the jaw.
- {Subject} {wear} a sealed tactical helmet with a smoked visor and an integrated breather mask, a coiled comms cable trailing from the jaw.
- {Subject} {wear} a smooth blue-visored full-face helmet with a hood drawn up over it, a scarf wound loose at the throat.
- {Subject} {wear} a flat wide-brimmed lacquered hat crowned with a bird skull and trailing feathers, the brim throwing {possessive} face into shadow.
- {Subject} {wear} a bulky mechanical diagnostic rig clamped over the crown of {possessive} head, thick cabling trailing down to jacks at the collar, a status light lit at the side.
- {Subject} {wear} a sleek angular powered helmet with raised sensor fins and a full dark visor down, a single braid of hair falling free beneath it.
- {Subject} {wear} thin rectangular glasses framing sharp eyes.
- {Subject} {wear} a sleek mechanical half-mask sealed over the nose and mouth, a small lens node mounted at the temple.
- {Subject} {wear} a close-fitted respirator mask across the lower face beneath narrow tactical eyewear.
- {Subject} {wear} a horned kabuto-style helmet with a trailing neck guard, its crest catching the last light.
- {Subject} {wear} a wide flat lacquered hat rimmed in gold, a single red tassel hanging from the brim.
- {Subject} {wear} a horned kabuto helmet with a scowling mempo faceplate, eyes lit with a faint red glow.
- {Subject} {wear} a wide woven hat trimmed with small curved horns and hanging tassels, a segmented mechanical mask sealed over the nose and mouth beneath it, a faint accent light glowing at the seam.
- {Subject} {wear} a wide straw hat trimmed with small hanging bells and a tattered red ribbon at the crown, rain streaming off the brim.
- {Subject} {wear} a broad ceremonial hat strung with hanging tasseled bells, an antler-like crest rising from the crown.
- {Subject} {wear} a broad woven hat bristling with jagged spikes at the crown, its brim battered and weathered.
- {Subject} {wear} a broad dark hat trimmed with hanging chain ornaments and a feather crest, the brim shadowing {possessive} eyes.
- {Subject} {wear} a wide straw hat over a patterned cloth headband tied at the brow.

## Headgear (she) +

- x2 {Subject} {wear} a slim hairband holding the hair back off {possessive} face.
- {Subject} {wear} a wide fabric band knotted at the back of {possessive} head, hair gathered behind it.
- {Subject} {wear} a slim glowing accent band swept back through {possessive} hair like a hairband.
- {Subject} {wear} a wide woven hat, thin red-framed glasses catching the light and a long-stemmed pipe held between {possessive} lips.

## Demeanor

- a flat, unimpressed expression
- a guarded half-smile that never reaches the eyes
- a tired, patient look, as if waiting out a long shift
- an open, disarmingly friendly expression
- a set jaw, plainly spoiling for an argument
- a distracted look, attention half on something out of frame
- a calm, unreadable expression giving nothing away
- a wry, crooked grin
- a thin, humorless smile
- a level stare that simply waits you out
- the easy confidence of someone used to being obeyed
- a weary, faintly amused resignation
- a flicker of impatience barely held in check
- an appraising look, frankly sizing you up
- a hushed, grief-stricken stillness, eyes closed
- a hard, narrow-eyed glare, fixed and unblinking
- a face streaked with tears, jaw held tight against it

## Demeanor (she) +

- a warm, open smile that reaches the eyes
- a knowing look, one eyebrow fractionally raised
- a soft, unhurried expression that gives nothing away
- a bright, quick grin
- a cool, composed poise that does not invite argument
- a narrow-eyed, studious focus, lips slightly parted mid-read
- a lazy, half-lidded stare around a lit cigarette, faintly unimpressed
- a startled, wide-eyed alertness, lips parted as if caught mid-thought
- a level, appraising stare held around a cigarette clenched between the teeth

## Role

<!--
  '|| mil' marks an occupation as active-duty military or paramilitary - see
  the note on it near the top of this file. It lines up with ROLE_CATEGORIES
  in the script: everything the script files under "Pilots", "Soldiers" or
  "Support" is flagged here, everything else is left civilian.
-->

- a mech pilot || mil
- a starship pilot || mil
- a chief mechanic
- a dockworker
- a freelance salvager
- a corporate liaison officer
- a field medic || mil
- a Union inspector
- a smuggler
- a pirate
- a Union marine soldier || mil
- a comms and sensors operator || mil
- a mercenary squad lead || mil
- a colonial administrator
- a bar owner and information broker
- a maintenance technician
- a security officer || mil
- a data courier
- a scavenger-priest of a local machine cult
- a mercenary sniper || mil
- an elite mercenary pilot || mil
- a close-quarters blade specialist || mil

## Faction

- x2 unaligned and freelance || civ
- x2 in worn Union Administrative Department kit || mil
- in Harrison Armory service dress, imperial and immaculate || mil
- in Smith-Shimano Corpro corporate wear, sleek and expensive || civ
- in IPS-Northstar workwear, riveted and salt-stained || civ
- in Karrakin baronial livery, formal and slightly archaic
- in the mismatched kit of a colonial militia || mil
- in the deliberately anonymous gear of someone who does not answer questions

## Outfit

<!--
  '|| civ' and '|| mil' work the same way here as on Faction - see the note
  near the top of the file. 'civ' is plainly civilian dress, dropped from the
  pool for a Role flagged 'mil'; 'mil' is an actual issued uniform (rank
  markings, unit numbers, a named dress/service/combat uniform), dropped for
  a civilian Role instead. Body armor and tactical gear with no insignia on
  it - a plate carrier, a chest rig, an unmarked hardsuit - reads as
  equipment rather than a uniform and is deliberately left unflagged, so it
  stays reachable either way: a civilian with military-grade gear is exactly
  what the flag split is meant to allow.

  A third flag, 'notac', marks an elaborate or traditional outfit - a kimono,
  shrine robes - that shouldn't turn up paired with tactical gear no matter
  how the Gear roll would otherwise land. It drops every 'mil'-flagged Gear
  bullet from the pool for that NPC. See the note on the Gear table below.
-->

- a heavy work jacket over a stained undersuit, sleeves shoved to the elbow || civ
- a fitted flight suit with the top half unzipped and knotted at the waist
- layered grey work coveralls patched at both knees || civ
- a long weatherproof coat over practical fatigues
- a tailored jacket cut close, with a high collar || civ
- an armored vest worn over civilian clothes, its plates visibly mismatched || civ
- a sleeveless thermal top, arms bare, forearms wrapped in worn tape || civ
- a hooded utility poncho over a pressure-suit liner
- a quilted thermal jacket over layered underlayers || civ
- a canvas work apron over rolled shirtsleeves || civ
- a pressure-suit undersuit with the armor plates stripped off
- a battered leather jacket gone soft with years of wear || civ
- a modern combat uniform in faded broken-pattern camouflage, padded combat shirt with the sleeves pushed to the elbow, knee-padded trousers || mil
- a modular plate carrier loaded with magazine pouches over a padded combat shirt, MOLLE straps cinched flat || mil
- a composite plate harness over a dark undersuit, magazine pouches racked across the front and a small status indicator lit at the collar || mil
- scuffed hardshell carapace armor over a sealed undersuit, repainted in patches, helmet clipped at the belt || mil
- a formal service uniform, sharp high collar and rank tabs, a slim data-tab clipped at the breast || mil
- an armored softshell greatcoat over slim uniform trousers and composite-soled boots || mil
- a dust-caked arid-pattern combat uniform under a slim chest rig, a shemagh loose at the neck || mil
- a low-profile plate carrier over a sweat-stained combat shirt, tags visible at the collar || mil
- an EVA-rated hardsuit with the helmet seals open and the gauntlets stowed
- a hooded recon softshell in broken-pattern camouflage, hood down, face paint half worn off || mil
- a multicam combat uniform under a modular plate carrier, magazine pouches ranked across the chest, knee-padded trousers and fingerless tactical gloves || mil
- a powered load-bearing exo-frame strapped over a combat uniform, actuators tracking the limbs and a status strip lit at the hip || mil
- a sealed hardshell combat suit with segmented plating at the shoulders, chest and shins over a close dark bodyglove || mil
- weathered olive-green camouflage tactical gear, a plate carrier vest worn over a long-sleeve field jacket, camo trousers, fingerless tactical gloves and scuffed combat boots || mil
- a fitted black techwear jacket, sleeves lined with small data ports, over a form-fitting undersuit || civ
- a black tactical jacket, unzipped and open, its interior lining faintly glowing, over a fitted dark bodysuit with light plating at the shoulders, forearms and shins
- a worn olive field jacket with the collar up over a ribbed dark turtleneck and a slim chest rig, fingerless tactical gloves || mil
- a high-collared black tactical pilot jacket with glowing cable tubing threading down the front || mil
- a long dark coat lined with thin glowing cabling, a spiked collar choker at the throat || civ
- a weathered black field jacket stencilled with a unit number and a small hazard patch, worn over a coarse knit jumper || mil
- a black military utility jacket stencilled with a unit number and a hazard triangle patch, hanging open over a plain olive tank top || mil
- a form-fitting armored bodysuit of segmented black plating, neural-interface cabling running from a plug at the collar
- a heavy hooded weatherproof cloak, the hood pulled low and the face half lost in its shadow || civ
- a tan and beige flight suit with rust-red accents, padded shoulder and knee armor and utility straps at the thighs || mil
- a fitted maroon-red flight suit with a cream chest yoke and shoulder rank patches, a rolled tan poncho-cloak bundled loosely at the waist, a bandolier of pouches slung crosswise over the chest, white gloves, and knee-high brown boots wrapped in pale canvas leggings || mil
- a dark olive-grey tactical coat over practical field gear, collar up and sleeves pushed back, no insignia or unit markings anywhere on the kit
- a fitted tactical flight suit with a high collar, buckled straps, small unit patches and an armband || mil
- a black tactical bodysuit with sharp angular trim and a high collar piece lit with small accent glows, a barcode marking inked at the collarbone
- a black formal dress uniform with a high standing collar and small rank pips, a double row of buttons, dull red piping at the shoulder boards, a ribbon rack at the breast and white dress gloves || mil
- a sealed grey tactical suit with layered armor pads at the shoulders and knees, a chest rig of ranked pouches and a long split-tailed shroud coat hanging to the ankles
- a faded rescue-crew jumpsuit, its high-visibility panels dulled to grime, a cropped hooded jacket over it and armored greaves strapped over the shins || civ
- an oversized grey hooded jacket with the sleeves hanging long over a high black collar wrap, harness straps crossing the chest, cargo trousers with armored knee panels
- a dark armored combat suit under a loaded chest rig, a long asymmetric white half-cape hanging from one shoulder to the ankle
- a black hooded field jacket webbed with pull-tabs and cinch straps, a pale shoulder shroud thrown over one side, a chest rig above cargo trousers with padded thighs
- a sealed white-and-grey field suit with an armored gorget at the throat, a plate carrier and a compact pack strapped over it, padded knees and heavy boots || mil
- an olive bomber jacket over a black bodysuit and plate carrier, grey cargo trousers and a drop-leg holster rig strapped down one thigh
- an olive field jacket with the sleeves pushed back over a close black bodysuit, a chest rig of magazine pouches, armored knee and shin guards above heavy trainers
- a sealed rescue hardsuit of segmented panels with armored boots and a hard equipment pack riding high on the shoulders || civ
- a segmented armored bodysuit under an open hooded jacket, a long scarf wound at the throat and trailing loose behind
- a heavy insulated flight jacket over a hooded pullover, cargo trousers and strapped knee pads
- a plate carrier over a dark bodysuit with a powered leg exo-frame braced from hip to boot
- an oversized rollneck sweater with the sleeves pushed back, harness straps over both shoulders and enormously baggy cargo trousers gathered at the ankle || civ
- a dark travel-worn robe with a crimson underlayer at the collar and sleeves, belted over wide hakama-style trousers || civ notac
- layered white pilgrim's robes gone travel-stained at the hem, a coarse rope belt cinched at the waist || civ notac
- a weathered haori-style jacket over a high-collared undershirt, sleeves bound back with cord || civ notac
- segmented lacquered armor plates over a dark underrobe, a torn banner cord trailing from one shoulder
- a heavy hooded work jacket with a reflective hazard stripe down one sleeve and patched insignia at the shoulder || civ
- an oversized weatherproof jacket bristling with pouches and straps, worn over a slung backpack with its harness crossing {possessive} chest || civ
- a battered set of heavy segmented plate armor, scorched and scarred at the shoulders and forearms, in dull combat red || mil
- a segmented white technical armor shell with dark reinforced wrapping at the thighs, scorched and battle-worn || mil
- a weathered mustard-yellow flight suit with a shoulder star patch and a small unit patch at the chest, a pale scarf knotted loose at the throat || mil
- an olive tactical jumpsuit under a cropped chest harness loaded with hip pouches, fingerless gloves and low tactical boots || mil
- a weathered leather jacket with a segmented armor plate at one shoulder, worn open over a dark top || civ
- a padded jacket with riveted metal pauldrons at both shoulders, a scarf wound loose at the throat || civ
- a fitted black tactical bodysuit with buckled strap detailing at the shoulder and ribbed panel seams || civ
- a navy flight jumpsuit under a cropped tactical vest loaded with chest pouches, a sidearm holstered at the hip || mil
- a segmented composite tactical armor suit with actuated knee joints and a compact backpack module, worn over an olive combat shirt || mil
- a sleek black powered tactical exo-suit with segmented plating at the knees and shoulders, a long dark half-cape trailing from one shoulder || mil
- segmented dark armor pauldrons over a hooded travel robe, striped forearm wraps and small ornamental tassels at the shoulder
- a sleek angular powered armor suit with an oversized intake-vented backpack module, warning stencils and exposed cabling trailing from the shoulder || mil
- heavy segmented composite armor with a large stencilled unit number across the shoulder plate, status lights lit along the collar || mil
- a white flight jacket with a stencilled red-and-black shoulder patch marking a service unit || mil
- a mottled camouflage jacket worn open over a plain dark tee stencilled with a bold unit number, cargo trousers and fingerless tactical gloves || mil
- a sealed high-collared armored bodysuit with heavy pauldron-style shoulder plating and integrated sensor housings at each shoulder
- a fitted dark tactical bodysuit segmented with rust-orange trim plating at the joints and collar, a long weathered rust-colored cape trailing from one shoulder
- segmented crimson-lacquered armor plates over a floral-patterned quilted robe, tasseled cords trailing from one shoulder and a wrapped bundle slung across the back || civ notac
- full lacquered samurai armor in dark green and black with segmented shoulder pauldrons over a trailing hakama-style skirt, ornamental tassels at the waist || civ notac
- dark samurai robes with a long crimson cloak trailing from the shoulders, one leg bared and banded with tattooed markings || civ notac
- a tattered dark robe hanging open at the chest, its hems torn and trailing loose || civ notac
- a dark robe with a pale patterned collar, red fingerless gloves laced to the wrist || civ notac
- a dark patterned robe with a bright orange underlining, a string of prayer beads wound at one wrist || civ notac
- ragged wrapped cloth bindings over bare limbs, one wrist bound in worn bandaging, feet bare in simple woven sandals || civ notac
- a dark robe traced with gold embroidered trim, a purple sash knotted at the waist and small tassels hanging loose || civ notac
- a dark kimono cinched with a wide white sash tied in a full bow at the back || civ notac
- a fringed pleated mantle draped over the shoulders and swagged with hanging chain loops, worn over a dark strapped underlayer || civ notac

## Outfit (she) +

<!--
  Feminine cuts, added to the neutral options above rather than replacing them -
  a woman in grey coveralls is entirely normal and should stay possible.

  The armored-bodyglove entries deliberately name no glow color: the palette
  sentence in the template already makes the rolled Accent the only saturated
  color, so "glowing seam lines" picks it up instead of fighting it.
-->

- x2 a flight suit tailored close through the bust, waist and hips, the front zip run down past the sternum
- a cinched belted jumpsuit unzipped well below the collarbone, the belt hauled tight at the waist || civ
- a cropped utility jacket over a short high-waisted work skirt and sheer dark tights, a band of bare midriff between them || civ
- a deep wrap-front tunic belted at the waist over close-cut trousers, the crossed neckline cut low || civ
- a sleeveless coverall unzipped to the navel and knotted off at the waist over a cropped tank, arms and midriff bare || civ
- a long knitted cardigan over practical fatigues, sleeves pushed up || civ
- a tailored corporate blouse open two buttons at the throat over a narrow skirt slit high at the thigh, immaculate against the grime || civ
- a close-fitting pilot undersuit worn without its outer shell, unzipped to the sternum and clinging to every line of the figure
- a dress uniform tailored close to the figure, fitted jacket over a short straight skirt, bare legs above polished knee boots || mil
- a combat uniform taken in through the waist, sleeves pushed up, a plate carrier cinched tight over it || mil
- a fitted armored bodyglove under a partial plate harness, the plates leaving the midriff and one shoulder bare
- x2 a white-and-grey armored hardsuit of scuffed fitted plates over a black bodyglove, glowing seam lines tracing the limbs
- a black tactical jacket with piped trim over a close grey bodyglove and armored thigh-high boots, a hand's width of bare thigh above them
- a black military jacket with dull gold trim, worn open over a low-cut dark bodysuit and chipped white armor plates || mil
- a white field jacket thrown open over a black bodyglove cut deep at the chest and traced with faint glowing conduit lines
- a sleeveless flight harness of buckled straps over a black bodysuit unzipped low between them, a single lit indicator strip down the chest, arms and shoulders bare
- a close-cut pilot bodyglove in white and grey, lit seams tracing the waist and hips, partial shoulder plating and nothing over the bare midriff
- a sleek fitted flight suit, dark through the torso with silver-white segmented plating at the hips and thighs, thin glowing circuit piping tracing the shoulders and the chest seam, the front zip run down low
- a short light civilian dress patterned with small dark polka dots, thin straps at the shoulders, over dark thigh-high stockings, incongruous against the grime || civ
- a weathered field jacket stencilled with a unit number and a small hazard warning patch, hanging open over a cropped top and bare midriff || mil
- a tan tactical vest hanging open over a torn cropped tank, one arm wrapped in bandaging, worn cargo trousers slung low at the hips || civ
- an oversized open shirt sliding off one shoulder, draped loosely over a dark cropped tank || civ
- a sleeveless black tactical bodysuit with an exposed back framed by a cybernetic support harness, thin glowing circuit lines running along the spine and shoulder blades
- a black cropped tank top with a barcode tattoo and a stencilled unit number on the bare upper arm, a dark red jacket hanging off both shoulders and marked with a small hazard triangle patch
- a fitted crop top with tactical harness straps crossing the bare back, over close-cut white tactical trousers with accent straps and a pistol holstered at the thigh || civ
- a graffiti-tagged cropped t-shirt and cut-off shorts, midriff and legs bare || civ
- an asymmetric black coat-dress with a high collar, wire and cable detail threading down the front, ribbon straps and a beaded choker at the throat || civ
- a black hooded jacket trimmed in dull gold and draped loosely off both shoulders, over segmented pale grey-white plating at the hips and thighs and fitted leggings traced with a thin glowing line down the shin
- an open black jacket with a stiff collar over a fitted grey-white bodysuit, thin glowing stripes running down the sleeves and legs and tracing the seam at {possessive} bare midriff, segmented gloves and thigh-high boots
- an open white jacket over a fitted dark bodysuit marked with a small angular chevron at the chest, thigh-high leggings traced with glowing curved stripes, gloves and boots trimmed in dull orange
- a black sleeveless harness top with rust-red trim piping and buckled shoulder straps, a lit strip running down the center of the chest, long weathered grey-white bracers past the elbow with their plating cracked at the shoulder seams
- a high-collared tactical pilot suit with padded shoulder and knee armor, glowing cable detail running the length of one sleeve || mil
- a fitted grey-white bodysuit traced with a thin glowing circuit line, one oversized pauldron stencilled with a small insignia, segmented armor plating down the legs || mil
- a black strapless bodice leaving the shoulders and arms bare, a draped pale scarf-cowl wound loose at the throat and wide gold cuffs clasped on both forearms || civ
- a black formal dress uniform, high standing collar and rank pips above a ribbon rack at the breast, white dress gloves, a long dark pleated skirt gathered under a wide sash at the waist || mil
- a white double-breasted officer's tunic with a high open collar and armored shoulder boards, belted at the waist over a short flared skirt, a long dark cape hanging from the shoulders, garter straps at the thigh above white boots || mil
- a cropped olive bomber jacket over a slim chest rig and a fitted tee, a band of bare midriff above olive cargo trousers slung with pouches || civ
- a dark work shirt with the sleeves rolled to the elbow under a strapped harness rig, a radio pouch at the chest, baggy olive cargo trousers, tactical gloves and armored shin guards over heavy boots || civ
- an elaborate floral kimono layered over a plain white underrobe, sleeves trailing long past the fingertips || civ notac
- white shrine robes with a red hakama skirt, a cord-tied over-sash crossing the chest || civ notac
- a black jacket studded with spikes at the collar and shoulders, a small enamel pin at the breast, over a cropped top and a low-slung belt hung with metal loops || civ
- a worn hooded jacket patched with faded characters at the sleeve, torn and taped at the seams || civ
- an olive tank top over cargo trousers, a pair of fingerless gloves and worn lace-up boots || civ
- an oversized cropped black jacket with dull gold trim, worn open over a graphic crop top and a low-slung utility belt || civ
- a cropped black graphic hoodie with a small patch at the sleeve, over dark track trousers striped down the leg || civ
- a black leather corset-coat with a high spiked collar, a short pleated underskirt and thigh-high tactical boots || civ
- an oversized black tactical jacket, unzipped over a cropped top baring the midriff, small mismatched patches on one sleeve and a segmented armored panel at one shoulder
- a sleek black-and-white armored bodysuit with an oversized geometric pauldron on one shoulder, a lit status display set into the chest plate and thin glowing seams tracing the joints, a bare midriff panel at the waist
- a fitted black leather bodysuit with a high popped collar, rain-slicked and traced with faint glowing seam lines at the wrists
- a mustard-yellow flight suit with padded shoulder patches and a wide belted utility harness, sleeves rolled to reveal a lighter underlayer, a weathered grey scarf knotted loosely at the throat
- a glossy black bodysuit with a short pleated skirt panel at the hip, one arm sheathed in an articulated mechanical gauntlet running to the shoulder, over knee-high boots
- a cropped olive tank top with a patch pocket at the chest, twin red armbands worn above the elbow
- a lacquered single pauldron over a fitted dark robe with an embroidered high collar, tasseled cords hanging from the shoulder, a wide sash cinched at the waist || civ notac
- a fitted halter-neck tank top with a high choker collar, one bare shoulder crossed by a thin strap || civ
- a cropped bomber-style jacket zipped only at the chest over a fitted sports top and briefs, midriff and legs bare, wrists wrapped in tape || civ
- a fitted red-and-white segmented plate armor suit cut low across the chest, articulated joints at the shoulders and knees
- a sleek black tactical bodysuit with segmented dark red armor plating across one shoulder and arm, fingerless gloves and knee-high boots || civ
- a tattered black cloak like torn wings draped from the shoulders over a wrapped cropped top, buckled utility straps cinched at the waist and one armored bracer laced to the forearm || civ
- a fitted dark leather bodice cut low at the chest over a long dark wrap skirt, faint red markings tracing down one bared arm || civ
- a partial lacquered pauldron and vambrace worn over a cropped underlayer baring the midriff, small red tassels trailing from the shoulder plate || civ notac
- a white-and-black lacquered armor harness baring the midriff, fitted white trousers tucked into patterned boots || civ notac
- a sleeveless dark lamellar armor bodice with a red cord sash, plate segments hanging low over dark leggings, {possessive} shoulders left bare || civ notac
- a dark kimono patterned with pale plum blossoms, a crimson underlayer glimpsed at the collar and wide sleeves || civ notac

## Weapon

<!--
  What the NPC is armed with, rolled separately from Gear so a mechanic can
  carry a tool bag AND a holstered sidearm - one combined roll could only ever
  yield one of the two.

  A weapon is the most theme-defining object a figure carries, which is why
  this table is theme-gated and Gear is not: one undifferentiated pool is why
  every theme's armament used to land on everyone.

  The 'x30 || none' entry is an empty bullet: split_flags() parses it to text
  '' with flags ('none',), so it contributes nothing to the prompt - 'none' is
  a literal marker flag that nothing reads. It keeps an unarmed NPC the common
  case, and it keeps the average prompt short, since most NPCs then render no
  weapon phrase at all. Its weight is the dial for how armed the setting feels
  - raise it for a quieter one. A 'mil' Role never reaches it:
  apply_weapon_policy() restricts that pool to 'sidearm'-flagged bullets,
  which this is not.

  Flags here: 'weapon' (an actual weapon), 'simple' (small and pocketable),
  'sidearm' (includes a holstered or openly worn pistol - the guaranteed-armed
  baseline for a mil Role), 'gun' (an actual firearm held in hand), 'hands'
  (occupies at least one hand), 'mil' (military-issue).
-->

- x30 || none
- a sidearm holstered high on a chest rig || mil weapon simple sidearm
- a bullpup service carbine slung muzzle-down across {possessive} chest on its sling || mil weapon
- a bullpup service carbine held at a low ready in both hands, rail-mounted optic on top || hands gun mil weapon
- a katana with a colored glowing accent along its edge slung over {possessive} shoulder || mil weapon
- a katana with a colored glowing accent along its edge held in {possessive} hands || hands mil weapon
- a service pistol worn openly at the thigh || mil weapon simple sidearm
- a compact sidearm holstered at the hip and a utility belt of pouches at the waist || mil weapon simple sidearm
- a sheathed katana crossed against {possessive} back alongside a second, shorter blade || mil weapon
- a suppressed precision rifle with a rail-mounted optic, slung muzzle-up over one shoulder, one hand resting on the sling at {possessive} chest || hands gun mil weapon
- an AK-pattern assault rifle with a distinctive curved magazine held across {possessive} body || hands gun mil weapon
- a suppressed short-barrelled carbine carried muzzle-down in one hand || hands gun mil weapon
- a drop-leg holster rig and magazine pouches strapped down one thigh || mil weapon simple sidearm
- a sidearm gripped and raised in both hands, sighted dead level at the viewer || hands gun mil weapon simple
- an oversized rail cannon gripped and leveled at the viewer with both hands, a thick barrel shroud and boxy under-slung magazine || hands gun mil weapon
- twin sidearms held akimbo, one arm thrust forward and the other braced out to the side || hands gun mil weapon
- a service rifle held loosely in both hands at an easy, unhurried low ready || hands gun mil weapon
- twin sidearms held low and loose in both hands, muzzles angled down at {possessive} sides || hands gun mil weapon
- a long polearm banded in trailing red cord, planted butt-down and held upright in one hand || hands mil weapon
- a long suppressed sniper rifle with a scope, its stock stencilled with a small painted tally number, slung across {possessive} back || mil weapon
- a pair of oversized clawed gauntlets, a single sensor node glowing in each palm || hands mil weapon
- x4 a sidearm holstered at the hip and a service rifle slung muzzle-down across {possessive} chest || mil weapon sidearm
- x3 a service pistol worn openly at the thigh and a bullpup carbine slung across {possessive} back || mil weapon sidearm
- x3 a holstered sidearm and a suppressed carbine slung muzzle-down over one shoulder || mil weapon sidearm
- a plain combat knife sheathed at the hip || weapon simple
- a folding push-dagger tucked into a boot sheath || weapon simple
- a compact hold-out pistol tucked into a shoulder rig, mostly hidden under a jacket || weapon simple
- a slim single-edged blade held low and reversed at {possessive} side || hands mil weapon
- a massive twin-barreled support cannon carried braced against {possessive} hip || hands gun mil weapon
- a heavy shoulder-mounted weapon pod worn like a backpack, twin barrels rising above {possessive} head, a sidearm holstered at {possessive} hip || mil weapon sidearm
- a compact sidearm gripped low and loose in one hand || hands gun mil weapon simple
- a bullpup service rifle with an under-barrel attachment held at a low ready in both hands || hands gun mil weapon
- a suppressed marksman rifle with an extended barrel held low in one hand || hands gun mil weapon
- a katana half-drawn from its sheath at the hip, {possessive} free hand steadying the scabbard || hands mil weapon
- twin sheathed swords worn crosswise at the hip, tasseled cords hanging from the hilts || mil weapon
- a sheathed katana carried loose in one hand, hanging point-down at {possessive} side || hands mil weapon
- a sheathed katana worn at the hip, {possessive} hand resting loose on the hilt || weapon
- a katana gripped and raised overhead in both hands mid-swing || hands weapon
- a katana held drawn low in one hand, its point trailing near the ground || hands weapon
- a katana held drawn across the body, a bundle of additional sheathed blades and a small demonic mask hanging at {possessive} hip || hands weapon
- a bundle of sheathed blades bound together with cord at {possessive} hip || weapon
- twin katanas, one gripped loose in each hand and lowered at {possessive} sides || hands weapon
- a sheathed katana at {possessive} hip, one hand gripping the hilt, poised to draw || hands weapon
- a pair of blades hovering motionless in the air to either side, faint markings etched along them || weapon
- an oversized two-handed blade held low in one hand, its point trailing near the ground, a second shorter sword sheathed at {possessive} hip || hands weapon
- a sheathed katana crossed against {possessive} back alongside a second blade drawn and gripped in {possessive} hand, its edge glowing faintly || hands mil weapon
- a katana held upright close to {possessive} shoulder, its blade bared and ready || hands mil weapon
- a sheathed katana rested up over one shoulder, gripped loosely by the scabbard in one hand || hands mil weapon
- twin sheathed swords worn crossed at {possessive} hip, hilts angled outward || mil weapon
- a katana held up close to {possessive} face, its blade angled back and ready in one hand || hands mil weapon

## Gear

<!--
  '|| mil' marks a piece of military-issue equipment - see the note on it
  near the top of this file.

  Gear is equipment only now: tools, cases, packs, the odds and ends a figure
  has in hand or slung over a shoulder. Armament - anything that reads as a
  weapon - lives in '## Weapon', rolled separately; see that table's comment
  for its flags.
-->

- a battered data-slate tucked under one arm || hands
- a heavy multitool holstered at the hip
- a coil of cabling and diagnostic leads slung across the body
- a scarred pilot helmet carried in the crook of one elbow || hands
- a compact rebreather clipped at the collar
- a shoulder-slung tool bag, its strap worn through and re-stitched
- a slim wrist-mounted holographic interface projecting faint readouts
- a cigarette burned nearly to the filter, held forgotten || hands
- nothing at all, hands loose and empty
- a bundle of rolled schematics under one arm || hands
- a heavy pry bar hooked through a belt loop
- a caged inspection lamp trailing a length of cable || hands
- a bandolier of tool bits worn across the chest
- a sealed sample case cuffed to one wrist
- a folded jacket slung over one forearm || hands
- a sheaf of stamped requisition forms || hands
- a dented thermos of something long gone cold || hands
- a folded maintenance drone perched dormant on one shoulder
- a battered leather-bound ledger tucked in a breast pocket, worn soft from handling
- a loaded tactical backpack slung from one shoulder || mil
- a hard-shelled assault pack worn high on the back, its straps cinched across the chest || mil
- a compact field radio in a chest pouch, its stub antenna angled up past {possessive} shoulder || mil
- a slab-sided equipment case clipped to the harness at {possessive} hip
- a compact twin-thruster pack strapped across {possessive} back, its vents lit with a colored glow
- a folded oilpaper parasol held in one hand, its tip braced against the ground || hands
- a small pale fox cradled against the chest in both arms || hands
- a lacquered walking stick gripped in one hand, weight braced into it || hands
- a fist-sized holographic sphere hovering just above one open palm, its surface a shifting lattice of glowing fracture-lines and readouts
- a translucent holographic data-sheet held up in both hands, dense scrolling text glowing across its surface || hands
- a cracked-open slate bristling with jack cables and cracking tools, plainly meant for breaking into things it shouldn't || hands
- a pair of articulated mechanical wing extensions mounted at the shoulders, each feather-like segment tipped with a small lit sensor lens
- a small pendant amulet glowing softly at the throat
- an old-fashioned lantern glowing warm, carried by its handle in one hand || hands

## Accent

<!-- The single saturated glow color in an otherwise restrained frame. -->

- teal-green
- x2 amber
- dull copper-orange
- cold blue-white
- sickly yellow-green
- deep violet
- brass-gold
- crimson-red
- electric blue
- magenta-pink
- neon cyan

## Backdrop

<!--
  Portrait only - the token is always flat white for background removal.

  Each bullet carries BOTH halves of the shot, split on '||': the opening phrase
  on the left, the scene sentence on the right. They have to agree, so they are
  rolled together. A dive toward the camera cannot be staged inside "a half-body
  character portrait", and a zero-gravity pose over a rain-streaked street would
  be nonsense whichever opening it got.

  A third '||' segment carries flags. The only one is 'nogear', for scenes
  that already put something in the subject's hands - without it the
  gunfight and blade-draw scenes stacked a rolled rifle on top of the weapons
  they hand out, and the NPC came out carrying three. It drops the whole
  merged Weapon+Gear "carries ..." sentence from the portrait only (the token
  keeps it - it has no scene to contradict), and separately keeps the Gear
  roll itself off any '|| hands' bullet, so a scene never ends up paired with
  a Gear item it would visibly be fighting over the subject's hands.

  Writing zero-gravity entries: describe the BODY first - foreshortening, the
  arched back, the reaching arm, the trailing legs - and the room second.
  Entries that led with the environment rendered the subject standing on a deck
  no matter how many "weightless" qualifiers were bolted on.

  The standing entries are weighted x3 against eight zero-gravity ones, so about
  a quarter of portraits come up weightless. Change that weight to shift the mix.

  The exterior/vacuum entries dress the subject in a sealed EVA pressure suit
  and helmet over whatever Outfit was rolled, so a corporate blouse in hard
  vacuum stays coherent - a harness or open faceplate isn't enough on its own
  out there, so those entries commit to the full suit rather than implying
  one.
-->

- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is the dim interior of a mech hangar, gantries and chain hoists receding into shadow.
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cramped cockpit lit only by instrument readouts.
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a colonial street at night, the signage smeared across wet pavement. || weather
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is the cluttered back room of a repair shop, parts racked floor to ceiling.
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a station corridor lined with conduit and hazard striping.
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is an operations room wall of tactical displays.
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is the open bay door of a dropship, a pale sky beyond. || weather
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a bar interior, out-of-focus figures at the tables behind.
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} diving directly toward the viewer through a dim ship corridor in freefall, {possessive} body stretched into dramatic foreshortening, one arm reaching forward toward the viewer with open fingers and the other bent up near {possessive} head gripping an unseen handhold above the frame, legs trailing behind {object} in motion, faint streaks of motion blur emphasising {possessive} speed, the corridor's lit panels and hazard striping rushing past. Dramatic foreshortened composition.
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} weightless in freefall, {possessive} body tilted no more than about 30 to 40 degrees off vertical and stretched toward the viewer in strong foreshortening, one gloved hand thrust out at the camera and {possessive} legs trailing loose behind {object}, hair and tether lines floating free, having just pushed off a bulkhead out of frame - behind {object} a darkened docking bay, its running lights streaking past. Dramatic foreshortened composition.
- A close, low-angle character portrait || {Subject} {is_are} floating weightless in a narrow access tube, one arm braced against the wall above {possessive} head and knees drawn up, {possessive} body turned a mild 20 to 30 degrees off vertical with nothing underfoot, small debris and loose tools hanging motionless in the air alongside {object}, dim panel lighting receding down the tube behind.
- A dynamic, gently canted-angle character portrait || {Subject} {is_are} weightless in freefall, body tilted no more than about 30 to 40 degrees off vertical across the frame with one hand reaching out and {possessive} legs drifting loose behind {object}, hair lifted free - around {object} the netted crates of an unlit cargo hold hang untethered in the air, a single work lamp raking across {object} from one side.
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} gliding along the exterior hull of a ship in a low zero-gravity recline, {possessive} back arched and body tilted no more than about 30 to 40 degrees off vertical across the frame, one gloved hand reaching up and back to grip an angular strut above {possessive} head while the other extends down to brace against a rail beneath {object}, legs drawn up and bent, head tilted back inside a sealed EVA helmet, visor down, gazing up and to the side, a full pressure suit worn close over {possessive} kit - behind {object} the dark hull curves away into the void, faint teal atmospheric light bleeding in from one side and streaks of motion-blurred light trailing past in the starfield. Dramatic rim lighting along {possessive} silhouette.
- A dynamic, gently canted-angle character portrait || {Subject} {is_are} drifting weightless just outside an open airlock in a sealed EVA pressure suit and helmet, visor down, worn over {possessive} kit, body turned in a shallow roll no more than about 30 to 40 degrees off vertical with one gloved hand still on the hatch coaming and {possessive} legs floating free, tether line coiling loose behind {object} - beyond {object} the ship's plating falls away into the void and the lit limb of a planet curves across the background. Dramatic rim lighting along {possessive} silhouette.
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} braced weightless between two struts of an orbital gantry, {possessive} body tilted no more than about 30 to 40 degrees off vertical and slowly rotating, one gloved hand overhead on a spar and one boot hooked under a rail, a sealed EVA pressure suit and helmet, visor down, worn over {possessive} kit - behind {object} the scaffold recedes into the dark and the starfield streaks past in faint motion-blurred lines. Dramatic rim lighting along {possessive} silhouette.
- A close, low-angle character portrait || {Subject} {is_are} floating weightless inside a pressurised observation blister, one palm flat against the curved glass above {possessive} head and {possessive} body turned a mild 20 to 30 degrees off vertical, legs drawn up and bent, hair lifted free - beyond the glass the ship's hull curves away and the starfield turns slowly past. Rim lighting along {possessive} silhouette.
- A dynamic character portrait || {Subject} {is_are} caught in a three-quarter turn, raising a compact sidearm and firing directly toward the viewer, muzzle flash bursting from the barrel and a spent shell casing ejecting mid-air - behind {object} a dim industrial interior of dark metal panelling, faintly lit and kept soft and out of focus so {subject} {is_are} clearly the subject. Even key lighting on {possessive} face and weapon, with a dramatic but restrained rim light thrown by the muzzle flash. || nogear
- A dynamic, three-quarter rear-view character portrait || {Subject} {is_are} seen from behind on a rooftop ledge, glancing back over one shoulder and drawing a single-edged blade that glows faintly along its cutting edge, a second blade sheathed crosswise against {possessive} back - behind {object} a dim industrial cityscape stretches away, muted grey-olive towers dotted with sparse lit windows beneath a hazy dusk sky, and the hulking silhouette of something vast and serpentine looms low on the horizon as a dark rust-toned shape. Twin warning beacons glow dull amber at the edges of the frame. || nogear weather
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} weightless in freefall down a dim ship corridor, {possessive} body angled hard toward the viewer in strong foreshortening, one arm extended down and out gripping a raised sidearm with the muzzle tracking past the frame, the other hand bent back near {possessive} own head bracing against an unseen handhold, legs trailing loose behind {object}, faint motion blur streaking the corridor's lit panels and hazard striping as they rush past. Dramatic foreshortened composition. || nogear
- A character portrait || {Subject} {is_are} glancing back over one shoulder with a faint, private smile, one hand raised near {possessive} own face in a loose two-fingered gesture, hair drifting weightless with the motion - behind {object}, softly out of focus, a starfield and the curved limb of a planet glow low against the dark.
- A dynamic, close character portrait || {Subject} {is_are} standing square to the viewer with {possessive} arm fully extended, a pistol gripped level and aimed straight at the camera, {possessive} off hand braced beneath for support, {possessive} expression flat and controlled - behind {object}, blurred well out of focus, a plain dim interior with hard directional light. Dramatic side lighting rakes across {possessive} face and the weapon. || nogear
- A dynamic, low-angle character portrait || {Subject} {is_are} standing beside a parked matte-black superbike, both hands locked around an oversized cannon raised and leveled dead at the viewer, a sheathed blade slung crosswise across {possessive} back - behind {object} a rain-slick night street glows faintly blue through fogged storefront glass, the bike's windscreen starred with a bullet crack close beside {object}. || nogear weather
- A dynamic character portrait || {Subject} {is_are} braced with a double-barreled shotgun raised and shouldered, sighting hard toward the viewer, hair whipped loose by the wind - behind {object}, out of focus, an open sunlit horizon under a pale hazy sky. Hard directional light rakes across {possessive} face and the weapon. || nogear weather
- A dynamic, low-angle character portrait || {Subject} {is_are} braced low on one knee, a long suppressed sniper rifle shouldered and firing toward the viewer, a spent casing arcing free from the action and {possessive} hair caught mid-motion by the recoil - behind {object}, out of focus, a dusty open flatland fading into haze. Dramatic side lighting rakes across {possessive} face and the weapon. || nogear weather
- A dynamic, low-angle character portrait || {Subject} {is_are} braced low on one knee behind a belt-fed light machine gun, sighting down it toward the viewer with the ammo belt trailing to a drum magazine, gear-laden webbing crossing {possessive} chest - beside {object}, out of focus, the watchful shape of a large working dog crouches low in the frame, and behind them both a pale washed-out sky stretches away. || nogear weather
- A dynamic, low-angle character portrait || {Subject} {is_are} advancing down a cramped service corridor, a rifle raised and sighted toward the viewer, red emergency strip-lighting striping the walls and ceiling around {object} and dark stains marking the deck underfoot - ahead down the passage, two more silhouetted figures stand caught in a bright wash of light and drifting haze. Hard red-tinted side lighting rakes across {possessive} face and the weapon. || nogear
- x3 A half-body character portrait || Behind {object}, out of focus, is a muted frontier backdrop of dusty rockcrete structures and faint industrial haze, a dim atmospheric glow low on the horizon. Dramatic side lighting casts hard shadow across half {possessive} face. || weather
- A three-quarter character portrait || {Subject} {is_are} leaning intently over a cluttered workbench, hunched forward and studying something closely, both hands down on a mechanical keyboard - to one side a large monitor glows with dense terminal code, casting light across {possessive} face, and behind {object} a cluttered workshop of stacked machinery, tangled cabling and scattered papers recedes into soft focus under dim overhead light. Warm light on {possessive} face against the cooler background. || nogear
- A character portrait || {Subject} {is_are} leaning back against the flank of a long, low speeder bike parked at a fuel stop, ankles crossed and weight settled easy against the fuselage, a cigarette held forgotten near {possessive} mouth, gazing out at the fading light - behind {object} a hazy golden dusk skyline of distant spires rises beyond a scatter of old fuel pumps and hand-lettered signage crowding the foreground out of focus. || nogear weather
- A character portrait || {Subject} {is_are} sitting in profile, leaning back against the bent knee of a massive crouched military mech - the machine is boxy and heavily industrial, thick armored plating stencilled with unit markings, a single lit optic sensor and antenna protrusions rising from its head, its bulk looming just behind {possessive} shoulder. Behind them a rundown industrial refinery at dusk: tangled scaffolding, pipes and a tall numbered tower silhouetted against a low sun. Warm light rakes across {possessive} face and the mech's armor. || weather
- A dramatic low-angle character portrait || {Subject} {is_are} leaning back against the massive bent knee of a towering mech, looking down at the viewer, the shot angled steeply upward to emphasise the scale of both - the mech's leg fills the foreground in fine panel-line and rivet detail, a weapon barrel running off the top of the frame, a crescent moon faint through cloud above and a distant skyline low on the horizon. || weather
- A character portrait || {Subject} {is_are} sitting in the round hatch of an open viewport, one leg drawn up and hooked over the rim and the other hanging free outside it, {possessive} weight braced back against the frame in unhurried repose, gazing out past the opening. Tucked into the corner of frame below {object}, the domed head and lit photoreceptor of a small utility droid peeks into view. Beyond the hatch a pair of pale suns hang low over a sun-bleached horizon. || weather
- A character portrait seen from behind || {Subject} {is_are} leaning on a rooftop balcony railing high above a dense city street, glancing back over one shoulder at the viewer - below {object} the street is packed with stacked signage glowing through humid haze, the crowds and wet pavement dissolving into loose, almost impressionistic brushwork. A rooftop awning and railing frame the high vantage point. || weather
- A character portrait || {Subject} {is_are} standing in a bombed-out doorway between two weathered concrete walls, framed by scattered bullet holes, faded warning signs and pinned notices - behind {object} a ruined cityscape stretches away into smoke and dust, a massive mech silhouette looming among the broken buildings and a huge low sun bathing the scene. In the foreground the blurred silhouettes of two seated figures frame the bottom corners, well out of focus. || weather
- A close-up character portrait || {Subject} {is_are} framed tight against a dense city street at night, tangled overhead wires crossing a hazy sky behind {object} and stacked signage glowing softly out of focus, the light grading cool across {possessive} face. || weather
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a frontier rail platform in ochre haze, an incoming transit's headlamps glaring through the dust and tangled overhead wire. || weather
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cramped fire-escape landing tangled with cabling and pipework, neon shop signage bleeding pink and green through the grating and mist. || weather
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a crowded transit terminal beneath tangled cable runs, neon signage in unfamiliar characters glowing above loitering figures and drifting smoke.
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a snowbound crash site, a downed transport burning against a wall of white peaks. || weather
- x3 A half-body character portrait || Behind {object}, out of focus, an immense flying superstructure eclipses the low sun over a sprawl of sun-baked rooftops, its long shadow stretching through the haze. || weather
- A character portrait || {Subject} {is_are} standing on a windswept ridge, a weapon lowered and faintly smoking at {possessive} side, looking out over a mist-filled valley - behind {object} a vast ring of wreckage hangs frozen in the air above a plunging waterfall, a pair of transports drifting past far below. || nogear weather
- A character portrait || {Subject} {is_are} sitting cross-legged on a rooftop ledge, eyes closed in quiet stillness, a sheathed blade laid flat across {possessive} lap - behind {object} a dense night skyline glows through drifting haze, thin trails of aircraft light threading between the towers. || nogear weather
- A dynamic character portrait || {Subject} {is_are} walking straight toward the viewer down a rain-slicked neon-lit street at night, flanked on either side by a pair of hulking bipedal war-mechs looming half into frame, their optics burning dull red in the murk, signage bleeding into smeared reflections on the wet pavement behind them all. || weather
- A dynamic, low-angle character portrait || {Subject} {is_are} crouched low in a wide balanced stance atop a hovering skateboard ridden like a surfboard, knees bent and weight low, one arm flung out wide for balance and the other pointing off past the frame, a twin-thruster pack strapped across {possessive} back glowing faintly at the vents, hair and jacket sleeves whipped back by the wind - behind {object} a dense neon-lit cyberpunk skyline rises through drifting haze, towering signage in tangled scripts and corporate logos glowing through the mist, other riders on hoverbikes cutting past in the middle distance. || nogear weather
- A dramatic low-angle character portrait || {Subject} {is_are} crouched low behind an abandoned vehicle on a rain-slicked city street at night, weapon raised and sighting up at a colossal insectoid war-machine that fills the skyline ahead, its hull studded with glowing sensor clusters and thin segmented limbs trailing into the smoke-hazed street below, twin beams lancing down from its underside through the drifting mist - behind {object} a burning wreck casts long orange light across the wet pavement. || nogear weather
- A character portrait || {Subject} {is_are} standing just inside the shattered nave of a ruined cathedral, dust hanging thick in broad shafts of light falling through the broken vaulting overhead, gazing up at an ancient gold-plated war-machine crouched motionless among the rubble ahead - a pair of cloaked, hooded companions stand just ahead of {object}, silhouetted small against its bulk. || weather
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} caught mid-kick in heavy powered armor, driving a braced boot into the armored hull of a massive segmented war-machine at close quarters, {possessive} sidearm still gripped and firing point-blank in the other hand, sparks and debris bursting from the impact - behind {object} a shattered cityscape unfurls in smoke and falling rubble, distant explosions blooming against a pale hazy sky. || nogear weather
- A character portrait || {Subject} {is_are} standing amid drifting embers and rubble, watching a hulking quadrupedal war-mech stride past close behind {object}, an oversized cannon swinging loose from one of its forelimbs, a small armed flyer banking low overhead - beyond them a bombed-out industrial skyline fades into a bruised violet dusk, fire guttering low among the wreckage. || weather
- x2 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a windswept plain of tall pale grass, a small stilted wayside shrine strung with paper streamers and a spear driven upright nearby trailing a strip of red cloth, a faint rainbow arcing through the haze beyond. || weather
- x2 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-slick shrine courtyard at dusk, stone steps climbing to wooden eaves hung with a glowing paper lantern, pale fox-shaped shapes moving low through the mist. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is the fog-wrapped wreck of a fallen war-mech looming over a rain-soaked shrine courtyard, its broken frame threaded with strung paper talismans. || weather
- x2 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a sunlit ruin of towering stone archways and a broken aqueduct climbing a green mountainside, ivy and wind-bent trees reclaiming the old stonework. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a colossal robotic figure half-risen from a canal, only its ornate head, shoulders and clawed hands breaking the water, gold filigree tracing its dark plating; beyond it domed shrines and slender gold-latticed spires ring a plaza where two hooded robed figures pause at the water's edge beneath a hazy dusk sky, a dull red sun hanging low beside a darker second disc. || weather
- A three-quarter rear-view character portrait || {Subject} {is_are} standing in a mech's calibration bay, gazing up at a towering white-armored war-machine looming just ahead, one hand raised holding a slim holographic data-slate glowing with dense diagnostic readouts, {possessive} other hand braced at {possessive} hip - thick power cabling and chain hoists hang down around the mech's bulk, a wall-mounted display beside {object} scrolling systems-check telemetry, cool blue interior lighting washing the bay. || nogear
- A character portrait || {Subject} {is_are} standing atop the hull of a companion vessel in high orbit, sealed inside an EVA pressure suit and helmet, a cropped mission patch at the shoulder catching the thin light through the visor, looking back over one shoulder - beyond {object} a planet's night side curves away below, its cities burning in scattered threads of light against the dark.
- A dramatic low-angle character portrait || {Subject} {is_are} standing amid drifting embers on a scorched battlefield in heavy rain, {possessive} back to the viewer, a long rifle gripped and lowered at {possessive} side - ahead of {object} churned mud and shattered rock fade into grey mist streaked with falling ash. || nogear weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a floor-to-ceiling window wall overlooking a dense neon high-rise skyline at night, faint status readouts glowing at the edge of the frame.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a graffiti-tagged alley lit by tube neon signage bleeding red and teal through drifting mist.
- A character portrait || {Subject} {is_are} standing beside a parked muscle car on a dark cyberpunk street at night, one hand braced on the doorframe, glancing up at the looming high-rises ahead - behind {object} the car's tail-lights glow red against the wet pavement. || weather
- A character portrait || {Subject} {is_are} standing at a rooftop railing in the rain, glancing back over one shoulder, a pair of aircraft streaking low across the skyline behind {object} - below {object} a dense neon high-rise district stretches away into the haze. || weather
- A close character portrait || {Subject} {is_are} seated inside a parked vehicle's cockpit in heavy rain, one hand braced on the wheel, neon shopfronts smearing color across the fogged, rain-streaked windshield ahead. || weather
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} weightless in freefall, twisting hard to slip between a crossing lattice of taut laser tripwires, {possessive} body bent and one arm flung wide for balance while the other reaches ahead, loose debris and shattered fragments drifting alongside {object} - the beams cut bright green lines through the dark around {object}, faint structural wreckage receding into the black beyond.
- A character portrait || {Subject} {is_are} standing before the hull of a beached derelict starship, reaching up to touch a faint glowing panel set into its plating - behind {object} the ship's saucer-like silhouette looms against a field of stars.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a wall of humming, dust-caked monitors and tangled cable runs, their pale glow the only light in the room.
- A dynamic character portrait || {Subject} {is_are} crouched low and reaching forward through the wreckage of a gutted server room, heavy clawed gauntlets braced against a fallen strut - behind {object} shattered windows let pale light leak through drifting dust and hanging cable. || nogear
- A character portrait || {Subject} {is_are} perched on the raised knee-joint of a crouched companion mech in heavy night rain, one hand braced against its plating - behind {object} a neon-lit high-rise district fades into the downpour. || weather
- A character portrait || {Subject} {is_are} standing beside a parked muscle car on a pastel-lit street at dusk, one hand resting on the open door - behind {object} a tangle of towering cyberpunk architecture rises hazy into the fading light. || weather
- A character portrait || {Subject} {is_are} sitting cross-legged on a rooftop ledge at night, hands braced behind {object} - beyond {object} a massive ringed planet hangs low over a grid-lit synthwave skyline lined with palm trees.
- A character portrait || {Subject} {is_are} sitting on the hood of a parked muscle car beneath an enormous full moon, hands braced back against the metal - small dark shapes wheel through the night air above the rain-slick street around {object}. || weather
- A character portrait || {Subject} {is_are} seated low in a rain-slicked alley, jacket half-shrugged off one shoulder and cable straps trailing loose across {possessive} lap, gazing up past the camera - behind {object} neon signage in unfamiliar characters glows through the mist, a server rack blinking against the wall. || weather
- A character portrait || {Subject} {is_are} seated in a crowded night transit car, one hand raised holding a drink, oversized headphones clamped over {possessive} ears - behind {object} out-of-focus passengers sway with the motion and neon signage glows through the window beyond.
- A close character portrait || {Subject} {is_are} standing motionless before the lowered head of a colossal war-machine, its single optic burning close overhead, sparks showering down as welding light flares behind {possessive} shoulder - a steel catwalk and dim industrial scaffolding recede into the haze around {object}.
- A close character portrait || {Subject} {is_are} reclined still in a diagnostic rig, head tipped back and eyes closed, a crown of cabling radiating out from {possessive} temples to banks of softly blinking readouts on either side of {object}.
- A dramatic low-angle character portrait || {Subject} {is_are} braced against the wind with one hand raised to shield {possessive} face, tribal markings streaking {possessive} cheek - beyond {object} a huge moon hangs low over a besieged orbital structure, beam weapons lancing down through drifting smoke. || weather
- A character portrait || {Subject} {is_are} sitting cross-legged atop the hull of a parked armored vehicle, segmented mechanical prosthetic arms resting in {possessive} lap - behind {object} a dense neon-lit night skyline glows above a heavy cannon barrel angled into frame.
- A character portrait seen from behind || {Subject} {is_are} standing in silhouette against a huge glowing sun rising behind a ring of ruined structural arches, hair and coat trailing in the wind - a shattered cityscape stretches out to either side of {object} beneath the glow. || weather
- A dynamic character portrait || {Subject} {is_are} drifting limp and weightless above the planet's curve, arms trailing loose and a line of cabling reeling out behind {object}, shattered debris and a distant damaged vessel tumbling nearby, {possessive} suit scorched and torn across the chest.
- A character portrait || {Subject} {is_are} standing before the looming bulk of a black companion war-machine, its twin shoulder cannons rising to either side and its optics burning faint red overhead - behind {object} a hazy night skyline glows low against the dark.
- A close character portrait || {Subject} {is_are} framed tight in a cracked flight helmet, a thin readout glowing at the brow, half {possessive} face lit by a bright detonation tearing through a field of tumbling rock and debris just beyond {possessive} shoulder.
- A close character portrait || {Subject} {is_are} reclined loose in a vehicle's seat, one arm slung back over the headrest and a knee drawn up, glancing out through a rain-streaked window - neon signage smears past in the dark beyond {object}. || weather
- A dynamic character portrait || {Subject} {is_are} walking straight toward the viewer down a narrow overgrown alley, a heavy pack slung on {possessive} back - ivy and reclaimed neon signage crowd the walls to either side of {object}, an old arcade cabinet half-buried in creepers behind.
- A close character portrait || {Subject} {is_are} crouched low in a wrecked, fire-lit room, banks of dead monitors stacked behind {object} and a fire smoldering in the wreckage beyond.
- A close character portrait || {Subject} {is_are} tipped back in a mech cockpit seat, {possessive} gaze lifted past the camera - dense banks of glowing readouts and a night skyline crowd the canopy around {object}.
- A character portrait || {Subject} {is_are} reclined deep in a low chair, legs crossed and stretched long, a hand of cards held loosely - mechanical prosthetic arm plating catches the light, and a heavy weapon rests propped against the chair beside {object}, screens of dense readouts glowing at {possessive} back.
- A dramatic character portrait seen from behind || {Subject} {is_are} standing still in the rain, gazing up at a towering battle-scarred war-machine looming just ahead, its single core glowing steady in its chest - a dense city skyline rises hazy through the downpour behind {object}. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cramped hacker's den lit green by a wall of humming CRT monitors, rain streaking a window at the far end. || weather
- A character portrait seen from behind || {Subject} {is_are} sitting on a rooftop bar's counter ledge, glancing back over one shoulder - a dense rain-soaked high-rise district glows through the downpour beyond {object}, potted plants crowding the rail. || weather
- A close character portrait || {Subject} {is_are} leaning back into a mech cockpit seat, rain-damp hair swept across {possessive} face, one gloved hand braced on the console - beyond the canopy a night skyline glows through the rain. || weather
- A character portrait || {Subject} {is_are} sitting perched on a heap of mangled wreckage, one hand raised to {possessive} collar - a sun-bleached desert stretches out behind {object}, distant explosions blooming pale against the sky. || weather
- A character portrait || {Subject} {is_are} gripping an overhead handhold inside a moving vehicle, one arm raised and braced, glancing up and to the side - a night skyline streaks past the window behind {object}.
- A dramatic low-angle character portrait || {Subject} {is_are} crouched on a narrow icy ledge high above the city, a pistol held ready in one hand, glancing back over {possessive} shoulder - a dense high-rise skyline drops away into the night far below {object}. || nogear weather
- A character portrait || {Subject} {is_are} seated in a shuttle's passenger cabin, poring over a thick bound technical manual balanced on one knee, a travel bag propped against the seat, a richly robed diplomatic passenger seated close beside {object} - beyond the windows a scatter of escort ships hangs against the stars.
- A close, low-angle character portrait || {Subject} {is_are} reclined deep in a mech cockpit's padded seat, sealed head to toe in scuffed dark pressure armor, one gloved hand fallen slack across {possessive} lap, a dense asteroid field drifting past the canopy overhead - beside {object} a second pilot leans in close, watching the field pass.
- A three-quarter character portrait || {Subject} {is_are} seated at a terminal, working a hovering holographic display with one hand, a hulking rust-streaked companion mech looming close behind {possessive} shoulder, its optics glowing faintly in the low light - around {object} banks of server racks glow in the dark. || nogear
- A dynamic character portrait || {Subject} {is_are} leaning low over the handlebars of a weathered vintage motorcycle, cutting fast across a sunbaked salt flat, {possessive} scarf and hair streaming back in the wind - behind {object} a chain of distant mesas breaks the horizon under a darkening sky. || weather
- A character portrait || {Subject} {is_are} half-turned against open space, a tattered scarf-cloak streaming out weightless behind {object}, hair drifting loose in the void - beyond {object} a churning red nebula glows low around a dark dwarf star.
- A dramatic low-angle character portrait || {Subject} {is_are} crouched low on a rain-slick rooftop ledge, bracing a long rifle sighted down into the streets below, weight settled low over one knee - beneath {object} a dense neon-lit cityscape glows through the downpour. || nogear weather
- A character portrait || {Subject} {is_are} standing braced with both hands flat on a lit control console, framed against a floor-to-ceiling viewport of a rain-swept neon high-rise skyline beyond. || nogear weather
- A dramatic low-angle character portrait || {Subject} {is_are} standing framed close against the camera, hair and jacket lifted by displaced air, glancing back over {possessive} shoulder as a colossal armored war-machine looms directly overhead - the shot angled steeply upward to emphasise its scale against the neon high-rise skyline beyond. || weather
- A dynamic, close character portrait || {Subject} {is_are} raising a compact pistol close to the camera, fine circuitry glowing faintly along {possessive} fingertips and knuckles - behind {object} a pair of masked companions stand watch at a railing overlooking a dense rain-slicked neon cityscape. || nogear weather
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} tumbling backward through open air in cracked powered armor, twin beams of light searing across {possessive} torso and shattering plating away in jagged fragments, hair whipped wild by the fall - far below {object} a dark cityscape glows red beneath the drifting debris. || weather
- A character portrait || {Subject} {is_are} reclined loose in a cockpit's crash seat, one hand reaching lazily out into the glow, banks of console screens and readouts ringing {object} on every side.
- A character portrait || {Subject} {is_are} standing at a rooftop ledge, a data-slate held loose in one hand and a sidearm holstered at {possessive} hip, a dark fabric wrap pulled up over the lower face - beyond {object} a dense neon-lit skyline glows red through the night haze. || weather
- A dynamic character portrait || {Subject} {is_are} walking straight toward the viewer down a dim industrial hangar bay, a flight helmet carried loose under one arm, a hulking quadrupedal war-machine striding through drifting steam close behind {object}, overhead lights raking down through the haze. || nogear
- A character portrait || {Subject} {is_are} standing squared to the viewer, a long white coat draped over {possessive} shoulders, an immense capital ship descending directly behind {object}, its hull lit sharply against a burning red city glow far below, drifting haze softening the skyline. || weather
- A close character portrait || {Subject} {is_are} standing perfectly still as an oversized mechanical hand reaches into frame to project a thin beam of light directly into {possessive} eye, a small stamped code marked at {possessive} cheekbone, the moment held in tense stillness.
- A character portrait seen from behind || {Subject} {is_are} standing atop a rooftop ledge high above a sprawling neon-red cityscape at night, a sidearm held loose and low in one hand, gazing down at the grid of light far below. || nogear weather
- A character portrait || {Subject} {is_are} standing beside a towering crimson war-machine, its cockpit visor glowing pale blue in the dark, {possessive} fitted suit catching the light - around them the dim outline of a nighttime hangar recedes into shadow.
- A character portrait seen from behind || {Subject} {is_are} standing at a viewport beside a hulking white powered-armor companion, one hand raised flat against the glass, a stencilled unit number marking {possessive} shoulder - beyond the glass a sunlit planet curves away below, city lights scattered across its night side.
- A character portrait || {Subject} {is_are} standing in three-quarter profile, a towering red-and-white war-machine looming just behind {possessive} shoulder, its single optic lit - down the street behind {object} red paper lanterns and shopfront signage glow through the night haze. || weather
- A character portrait || {Subject} {is_are} standing with both cybernetic prosthetic hands raised and pressed together in prayer, forearms segmented and scarred with use, a ring of glowing script arcing overhead like a halo - behind {object} a congregation of hooded, bowed worshippers recedes into a dim golden haze, their faces indistinct.
- A character portrait || {Subject} {is_are} seated in the open cockpit of a parked attack craft on a rocky ridge at night, flight helmet secured and visor down, a stitched unit patch at the shoulder of {possessive} flight jacket, gazing off past the frame - behind {object} a huge banded planet glows low over the ridge, faint stars scattered through the dark. || weather
- A character portrait || {Subject} {is_are} standing with a spent cigarette held loosely at the corner of {possessive} mouth, a pair of heavy mechanical support struts trailing cabling rising to either side of {possessive} head - behind {object}, out of focus, a dense hazy cityscape glows faintly through drifting mist.
- A half-body character portrait || Behind {object}, out of focus, is a towering sci-fi skyline beneath a colossal glowing ring-shaped structure hanging in the night sky, freighters and cruisers drifting past its light, the streets below slick with rain and threaded with cool running-lights. || weather
- A character portrait || {Subject} {is_are} seated astride a parked matte-black superbike on a railed overlook, one boot braced against the ground, glancing back over {possessive} shoulder - behind {object} a tiered river city of lantern-lit pagodas and waterfalls spreads below towering spired structures at dusk. || weather
- A character portrait seen from behind || {Subject} {is_are} standing at the foot of a towering dormant war-machine in a cluttered maintenance bay, a ladder propped against its leg and a flight helmet held loose in one hand at {possessive} side, dim standby lighting glowing from vents across its hull - a weathered poster and status monitors line the walls to either side, steam venting low across the floor. || nogear
- A character portrait seen from behind || {Subject} {is_are} standing at a rocky overlook, a long tattered cloak snapping loose in the wind behind {object}, gazing out over a hazy desert city ringed by tall spires - overhead a massive banded planet with a debris ring dominates the sky, smaller moons scattered around it, the whole scene washed in the deep orange of a dying sun. || weather
- A dynamic character portrait || {Subject} {is_are} standing on the broken rocky surface of an airless moon, a pistol gripped and lowered at {possessive} side, glancing back over one shoulder - behind {object} a searing beam of weapons fire lances low across the horizon, kicking up a spray of debris where it grazes the ground. || nogear
- A character portrait || {Subject} {is_are} reclined loosely in a cockpit seat, one leg - a segmented cybernetic prosthetic - propped up against the console, {possessive} head tipped back and gaze drifting past the canopy - beyond {object} a dense starfield stretches away into the dark, banks of status readouts glowing at the edges of the frame.
- A dynamic character portrait || {Subject} {is_are} standing amid drifting debris and fire on a cratered surface, glancing sharply toward the viewer, one heavy geometric shoulder plate catching the light - behind {object} explosions bloom low across the ground and a bright streak burns across the black sky above.
- A character portrait seen from behind || {Subject} {is_are} standing at the edge of a high rooftop with both arms flung wide, an oversized jacket printed with bold graphic linework across the back - below and behind {object} a dense neon high-rise skyline stretches away into the haze, a single towering spire glowing at the center of the frame. || weather
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} punching forward through the air in heavy powered armor plating, {possessive} lead arm driven out toward the viewer in a braced clawed gauntlet and the trailing arm cocked back, {possessive} legs trailing behind in motion, hair whipped back - behind {object} bright beams of weapons fire streak past low across a debris-strewn battlefield. || weather
- A character portrait || {Subject} {is_are} reclined deep in a battered gaming chair, arms crossed and half-lidded, a translucent visor band glowing faintly across {possessive} brow and cabling trailing from a jack at {possessive} temple - around {object} a bank of terminal displays glows with dense scrolling data, a burned-down cigarette smoldering in a nearby ashtray. || nogear
- A character portrait || {Subject} {is_are} standing with {possessive} bare mechanical hands folded low in front, fully articulated at every joint - behind {object} a hulking twin-turreted combat vehicle looms close, its optics glowing steady in the dark, a pair of moons rising in the night sky beyond. || weather
- A character portrait || {Subject} {is_are} reclined in the driver's seat of a battered open-top vehicle, both hands laced behind {possessive} head, elbows out, gazing off past the frame - behind {object} a ruined cityscape rises in ivy-choked towers under a hazy morning sun, birds scattering across the empty street ahead. || weather
- A character portrait seen from behind || {Subject} {is_are} walking away down a narrow alley, one arm a fully articulated mechanical prosthetic at {possessive} side - behind {object} a rain-slicked passage recedes into drifting fog, hazy signage bleeding color low across the wet stone. || weather
- A character portrait || {Subject} {is_are} sitting cross-legged atop the hull of a parked aircraft at night, {possessive} fully articulated prosthetic hands resting loose on {possessive} knees, gazing up past the frame - behind {object} banks of cloud drift past a star-scattered sky, the aircraft's markings faintly lit along its flank. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-slicked stairway alley lined with paper lanterns and a tiny bar counter, a hazy city skyline glimpsed below through the wet stone steps. || weather
- A character portrait || {Subject} {is_are} sitting slouched against a graffiti-tagged wall in a rain-slicked neon alley, one boot planted and the other leg drawn up, {possessive} head tipped back and eyes half-lidded, loose change and a dropped data-chit scattered on the wet pavement beside {object} - behind {object} tangled cable runs and stacked neon signage in unfamiliar characters glow through the drifting mist. || weather
- A close-up character portrait || {Subject} {is_are} framed tight in profile, raising a segmented mechanical hand close to {possessive} own face, fingers half-curled - behind {object}, out of focus, a dense cyberpunk high-rise district glows through drifting haze.
- A character portrait || {Subject} {is_are} standing in profile beside the towering head of a war-machine looming just behind {possessive} shoulder, gazing out across a hazy industrial skyline as a beam weapon fires from a distant flying craft overhead, faded unit markings stencilled across the machine's scarred plating. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-slicked elevated transit line threading between towering neon-lit high-rises, billboards glowing in unfamiliar characters. || weather
- A character portrait || {Subject} {is_are} seated inside a transit car at night, gazing out through the window at a dense neon high-rise skyline sliding past, faint circuitry tracing along {possessive} jaw and throat - the glass behind {object} streaks with drifting rain and passing light. || weather
- A character portrait || {Subject} {is_are} seated at a bank of monitors glowing violet and cyan, both hands on the keyboard and dense telemetry scrolling across the screens ahead, thick cable runs hanging tangled from the ceiling around {object}. || nogear
- A character portrait || {Subject} {is_are} standing on a raised gantry platform beside the crouched bulk of a towering war-machine filling a dim maintenance bay, its single optic sensor lit and a heavy cannon barrel angled down past {object}, faded unit markings stencilled across its scarred armor plating, stacked crates and hazard placards cluttering the shadowed bay floor below.
- A character portrait || {Subject} {is_are} sitting atop the broad missile-pod shoulder of an idle war-machine, a cigarette smoking forgotten in one hand, looking out over a muddy grey wasteland toward a distant radio mast, the machine's hull marked with a faded heraldic shield insignia and streaked with rain. || nogear weather
- A character portrait || {Subject} {is_are} walking down a wide ceremonial ramp through falling snow, a combat helmet held loosely in one hand at {possessive} side, faction banners snapping either side and hooded onlookers lining the way, the hulking silhouette of a towering war-machine looming backlit behind {object} in the drifting snow and haze. || weather
- A character portrait || {Subject} {is_are} standing in profile, a colossal crow-like beast looming close behind {possessive} shoulder, its single eye burning with a saturated glow in the gloom - beyond {object} a ruined stone courtyard fades into rubble and haze. || weather
- A close character portrait || {Subject} {is_are} seen in profile close beside the angular head of {possessive} companion mech, its optics burning twin points in the dark, a stencilled shoulder patch marking {possessive} flight jacket - beyond them a hazy blue-lit hangar recedes into the dark.
- A dynamic character portrait || {Subject} {is_are} walking straight toward the viewer down a dim shipboard corridor, a pistol held low and loose in one hand, a second armed companion keeping pace just behind {possessive} shoulder - pipework and hazard striping line the walls to either side, receding into a hazy blue light. || nogear
- A character portrait seen from behind || {Subject} {is_are} standing atop a snow-dusted rooftop unit, hair streaming in the wind, a sheathed blade held loose at {possessive} side, a small cat perched watchful nearby - below {object} a dense neon-lit high-rise cityscape glows through drifting snow. || nogear weather
- A dramatic low-angle character portrait || {Subject} {is_are} standing at street level as a canyon of soaring high-rises rises sheer on every side, towering signage in unfamiliar characters glowing through drifting rain overhead. || weather
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} weightless in freefall, both arms flung wide overhead and twin long braids drifting loose in the air, {possessive} body arched back in strong foreshortening - beyond {object} the dark hull of a starship interior glints with scattered debris and drifting light.
- A dynamic, low-angle character portrait || {Subject} {is_are} leaning far out over the drop, one hand locked around a strut and {possessive} body braced forward, gazing straight down through a vast light-streaked shaft at a glittering neon cityscape far below.
- A character portrait || {Subject} {is_are} sitting perched on the folded knee of a crouched companion mech, one hand resting easy against its armored plating as its head looms close alongside {object}, twin optics glowing steady - beyond {object} a dense city skyline spreads out below in the fading dusk light. || weather
- A dynamic character portrait seen from behind || {Subject} {is_are} balanced on the tip of a rooftop antenna mast high above the city, one leg braced and bent, a long coat billowing wide in the wind - far below {object} a dense high-rise skyline glitters with countless warning lights through the downpour. || weather
- A character portrait || {Subject} {is_are} sitting perched on a rooftop ledge, one leg drawn up and a lit cigarette held near {possessive} mouth, gazing out over a vast river-split cityscape glowing under a deep orange sunset. || nogear weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a plant-filled loft apartment with a domed window overlooking a rain-streaked neon high-rise skyline, candlelight and string lights glowing warm across cluttered bookshelves. || weather
- A half-body character portrait || Behind {object}, out of focus, is a fog-bound harbor skyline of towering high-rises, an elevated highway curving low over dark water and a blocky industrial platform lit from beneath. || weather
- A dynamic, low-angle character portrait || {Subject} {is_are} crouched low on a rain-slicked rooftop platform, one hand gripping a glowing energy blade planted point-down and weight braced forward, ready to spring - behind {object} a dense neon-lit cyberpunk skyline rises through drifting haze, a colossal holographic face glowing between the towers and small hovercraft drifting past in the middle distance. || nogear weather
- A character portrait || {Subject} {is_are} gazing up through a viewport in quiet wonder, tubing and cabling trailing from {possessive} suit collar to a bulky comms headset clamped over the ears - beyond the glass a planet's cloud-swirled surface curves away below and a scatter of distant moons hangs in the black.
- A character portrait || {Subject} {is_are} reclined against the fairing of a parked speeder bike, one arm draped along the windscreen and chin propped in {possessive} hand - behind {object} a neon-lit street glows in smeared bursts of color through the haze. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-slicked old-town street lined with lantern-lit shopfronts and parked bicycles, a cherry blossom tree overhanging the road and a distant illuminated tower glowing hazy through the mist. || weather
- A character portrait || {Subject} {is_are} standing in heavy rain at the center of a narrow street, flanked on both sides by towering high-rises plastered with glowing neon signage in unfamiliar characters. || weather
- A character portrait || {Subject} {is_are} standing in profile amid a cherry blossom grove at dusk, petals drifting thick through the air around {object} - the trees glow warm pink and gold in the fading light. || weather
- A character portrait || {Subject} {is_are} standing in heavy rain, glancing back over one shoulder from beneath a wide straw hat, a lit lantern raised in one hand - behind {object} a rain-streaked cityscape of weathered high-rises and faded signage fades into the downpour. || nogear weather
- A dynamic, silhouetted character portrait || {Subject} {is_are} caught mid-swing on a rocky bluff, driving a blade down in a decisive two-handed arc as sparks scatter from the strike, {possessive} cloak and sash ribbons whipped by the motion - behind {object} a massive sun burns low behind hazy mountains and a still lake below. || nogear weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a towering domed tower rising against a hazy dusk sky, two silhouetted figures paused in a lit doorway below. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a paper-screened room with the sliding doors thrown open onto a night sky thick with stars and a drifting nebula.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a windswept plain of pale grass, a second blade planted upright in the ground nearby, its hilt trailing dark streamers. || weather
- A dynamic character portrait || {Subject} {is_are} walking straight toward the viewer through the burning gate of a hillside shrine, flames engulfing the structure and lantern posts to either side, embers drifting across the smouldering ground underfoot. || nogear weather
- A character portrait || {Subject} {is_are} standing wide-legged with twin blades held loose at {possessive} sides - behind {object} a massive torii gate frames a huge glowing moon low on the horizon, rocky windswept terrain falling away into mist, hung paper talismans stirring to either side. || nogear weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a fog-wrapped hillside town of wooden gatehouses and lit braziers, a sprawling tiered castle rising misty on the ridge above. || weather
- A character portrait || {Subject} {is_are} sitting on a wet rocky shoreline in heavy rain, one elbow propped on a knee - behind {object} a flat grey expanse of water fades into mist. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a mist-shrouded ruin lit by a single stone lantern, a pale spectral face hovering faint in the gloom. || weather
- A dynamic character portrait || {Subject} {is_are} gripping a drawn blade low in both hands, {possessive} robe torn open at the chest and trailing loose in the wind, thick mist coiling around {possessive} legs - behind {object} a total eclipse burns a thin ring of light around a blacked-out sun, its glow diffusing through the haze. || nogear weather
- A character portrait || {Subject} {is_are} sitting cross-legged beneath a towering maple in full red autumn leaf, fallen petals scattering across the ground around {object} - beyond {object} a weathered shrine's timber eaves rise beside the tree and pale mountains fade into a clear sky. || weather
- A character portrait || {Subject} {is_are} standing in profile with a cigarette held loosely between {possessive} lips, gripping two sheathed blades low at {possessive} hip - behind {object} the fogged silhouette of a ruined industrial structure looms half-lost in the mist. || nogear weather
- A character portrait || {Subject} {is_are} standing with arms crossed against the wind, hair lifted loose and small birds startled into flight around {object} - behind {object} a golden field of tall grass sways beneath a hazy sky. || weather
- A character portrait seen from behind || {Subject} {is_are} standing at the edge of flooded paddy fields at dusk, a sheathed sword resting at {possessive} hip, gazing out over the water - power lines and utility poles cut across the hazy sky beyond {object}. || nogear weather
- A character portrait seen from behind || {Subject} {is_are} walking away through drifting fog and bamboo toward a distant pagoda silhouette, a sheathed blade at {possessive} hip - the temple's tiered roofline fades into the mist ahead. || nogear weather
- A dramatic low-angle character portrait || {Subject} {is_are} standing atop a rocky summit in full armor, a sheathed blade held point-down at {possessive} side, drifting red leaves swirling past - behind {object} an enormous full moon fills the sky through a wreath of storm cloud. || nogear weather
- A character portrait || {Subject} {is_are} standing before a weathered torii gate at night, armor catching the pale light, a scatter of vivid red flowers spread across the ground around {object} - mist pools low between bare trees and a hooded figure waits distant among aged grave markers behind {object}. || weather
- A close character portrait || {Subject} {is_are} sitting with head bowed, a sheathed sword held loose across {possessive} lap, petals drifting thick through the air around {object} - beside {object} a second blade stands planted upright, a small paper talisman glowing faintly at its hilt. || nogear weather

## Weather

<!--
  Portrait only, and outdoors only. The token renders on flat white for
  background removal, so falling snow there would just be more for RMBG to cut
  out; and weather is only added to Backdrop entries carrying the 'weather'
  flag, because rain inside a cockpit or in hard vacuum is nonsense. Most of
  the outdoor and semi-outdoor scenes carry it - streets, rooftops, ruins,
  ridges and vistas, the mech-companion shots - while the hangars, cockpits,
  corridors, interiors and vacuum scenes do not.

  Don't trust a count written here: this used to claim twenty-three flagged
  bullets and had drifted to thirty-nine before anyone noticed. Count them
  when the number matters.

  The 'clear' flag means the bullet contributes nothing to the prompt; its text
  exists only so the dossier has something to print. That is the dial for how
  often a flagged scene actually gets weather in it - as weighted here, about a
  quarter of outdoor portraits come up clear.

  Keep these to one short sentence. Both prompts already run close to Krea 2's
  512-token ceiling, and this sentence lands ahead of the palette and framing
  tail that gets truncated first.
-->

- x6 clear air, nothing drifting in the frame || clear
- x2 Fine rain drifts across the frame, beading on {possessive} shoulders and in {possessive} hair.
- Heavy rain hammers down through the frame, water running off {possessive} shoulders and streaking every surface behind {object}.
- A thin drizzle hangs in the air, softening the lights behind {object} into halos.
- Snow falls in slow scattered flakes, settling on {possessive} shoulders.
- Driving snow cuts across the frame at an angle, washing the background pale behind it.
- Sleet blows through in sharp bright streaks, the ground behind {object} slick with it.
- x2 Fine grey volcanic ash sifts down through the frame, dusting {possessive} shoulders and hair.
- Embers and burning ash drift up through the frame from a fire somewhere out of shot, glowing faintly as they rise.
- Smoke rolls low across the scene from something burning behind {object}, the far background lost in it.
- Wind-driven dust and grit stream across the frame, hazing everything behind {object}.
- A dust-laden wind lifts {possessive} hair and drags a thick haze across the background.
- A low industrial fog rolls through, swallowing the background a few paces behind {object}.
- Heat shimmer distorts the air behind {object}, the background rippling with it.
- A pale ground mist clings low across open grass, blurring everything a few paces behind {object}.

## Stance

- standing in a relaxed, watchful stance, weight settled evenly on both feet
- standing squared and formal, hands clasped behind the back || hands
- standing with arms folded, weight shifted onto one hip || hands
- standing loose and off-balance, one thumb hooked in a belt loop
- standing braced and alert, hands ready at the sides
- standing with hands pushed into jacket pockets, shoulders raised || hands
- standing at parade rest, spine straight
- standing square with both hands on the hips || hands
- standing slightly turned, shoulders angled a few degrees away
- caught mid-stride walking straight toward the viewer, the weight rolling onto the front foot
- standing side-on to the viewer, the body turned in profile and the head come back around to the camera
- standing squared with the feet set wide apart, head tilted a fraction
- standing turned away, glancing back at the viewer over one shoulder
- standing with one hand hooked over the strap at {possessive} chest, the other hanging loose || hands
- standing relaxed with {possessive} weapon held loosely in both hands, shoulders easy and unhurried || gun
- standing squared to the viewer with {possessive} weapon raised and shouldered, sighting down it || gun
- standing at a low ready, weapon angled down and across the body, alert and scanning the middle distance || gun
- standing in a sharp half-turn with a sidearm gripped in each hand, one arm extended straight out toward the viewer and the other braced out to the side || gun
- caught mid-stride walking straight toward the viewer, twin sidearms held low and loose at {possessive} sides || gun
- standing with head bowed and shoulders drawn in against the weather
- standing in a slow half-bow, one hand pressed flat against the chest
- standing with both arms raised overhead, a long board gripped in both hands and braced across the back of the shoulders like a yoke || hands
- sitting cross-legged in a formal meditative pose, palms pressed together at the chest, segmented mechanical arms folded still || hands
- leaning down into open machinery from above, braced on one forearm and reaching in with the other hand || hands
- crouched low and coiled on a raised ledge, weight braced forward on one arm, ready to spring || hands
- leaning low into a forward sprint, {possessive} braid whipped back and one arm driving down
- crouched low on one knee, gripping a blade planted point-down and ready to spring || hands
- standing in profile with head bowed slightly, one hand resting on a sheathed blade at the hip || hands
- caught in a dynamic overhead swing, both hands driving a blade down in a decisive arc, cloak and sash ribbons whipped by the motion || hands
- kneeling formally with both hands folded around an upright hilt held back against one shoulder || hands
- kneeling in profile with head bowed low, hands stilled in {possessive} lap
- walking straight toward the viewer with {possessive} weapon raised over one shoulder, cloak snapping back in the rising heat || hands
- raising {possessive} weapon high overhead in both hands, mid-swing, hair whipped wild by the wind and snow || hands
- sitting cross-legged with one elbow propped on a knee, chin resting in that hand, gazing out in quiet thought
- standing tense with both hands crossed at the hip, one gripping the hilt of {possessive} sheathed weapon, poised to draw || hands
- crouched low on the balls of the feet, one fist raised in a guarded ready stance, weight coiled forward || hands

## Stance (she) +

<!--
  Weighted so a woman lands on one of these most of the time. The base Stance
  table is neutral-to-military - parade rest, braced and alert, hands at the
  sides - and because this table is additive rather than a replacement, without
  weights the neutral entries won nearly seven rolls in ten.

  Entries needing both hands carry '|| hands' like anywhere else, so they are
  skipped when the Gear roll already occupies them.
-->

- x2 standing with weight on one hip and the other leg relaxed, an easy contrapposto
- x2 standing with one hand resting on the hip, chin slightly lifted
- x2 standing with {possessive} weight swung onto one hip, one hand on the hip and the other hanging loose
- x2 standing with {possessive} hips angled to one side and one knee softly bent, shoulders squared to the viewer
- x2 standing tall with shoulders back and feet close together
- x2 standing with arms loosely crossed, head tilted a fraction to one side || hands
- standing with one hand raised to push a strand of hair back from {possessive} face
- standing with one foot crossed lightly over the other, hands clasped low in front || hands
- standing with one hand at {possessive} collar and the other resting on {possessive} belt
- standing with one thumb hooked in {possessive} belt and the opposite hip pushed out
- standing with one arm folded across {possessive} waist, the other hand raised near {possessive} shoulder || hands
- standing with {possessive} head tilted slightly, one hand trailing loose at {possessive} thigh
- standing with {possessive} back to the viewer and one hand set on the hip, looking back over {possessive} shoulder
- standing with one hip kicked out, one hand brushing a loose strand of hair back near {possessive} temple, the other resting low on {possessive} belt
- sitting back with both hands laced behind {possessive} head, elbows out, utterly at ease || hands

## Prompt templates

These are the sentences the script assembles the rolled traits into. They are
reproduced here so the style is visible in one place alongside the tables, but
they live in `generate-npc.py` — editing them here changes nothing.

### Portrait (1024x1024, straight to the Foundry actor sheet, no background removal)

> **{SHOT}** of **{ROLE}**, **{AGE}**, rendered in a detailed
> painterly illustration style with fine grain texture and clean linework, halftone
> dot shading worked into the shadows, moody cinematic lighting. {SUBJECT} is
> **{BUILD}**, with **{TRAITS}** **{SKIN}**, **{HAIR}**, and **{EYES}**, and **{FEATURE}**,
> wearing **{OUTFIT}**, **{FACTION}**. **{HEADGEAR}** {POSSESSIVE} face carries
> **{DEMEANOR}**. {SUBJECT} carries
> **{GEAR}**. **{BACKDROP}** **{WEATHER}** **{ACCENT_LINE}** Shallow depth of field, square
> framing, high detail, atmospheric sci-fi character portrait. Painterly illustration
> throughout with visible brushwork, heavy fine grain texture over every surface, and
> dense halftone dot screentone worked deep into the shadows.

`{TRAITS}` is not rolled from a table at all: it is a fixed clause the script
asserts for every woman — currently "full lips, feminine posture" — including
one whose `Age` came up `young`, since it describes a face and a bearing rather
than an adult figure. It lives in `GENDER_TRAITS` in
`generate-npc.py`, because a trait that should reach nearly every NPC of one
gender cannot come out of a pool of thirty bullets.

`{HEADGEAR}` is a whole sentence rather than a noun phrase, and so is
`{WEATHER}` — which is empty unless the rolled Backdrop is flagged `weather`.
`{SHOT}` and `{BACKDROP}` are the two halves of one Backdrop bullet, split on
`||` — the opening phrase and the scene. Rolling them together is what lets a zero-gravity
entry restage the whole shot, swapping "a half-body character portrait" for "a
dynamic, dramatically foreshortened character portrait" and putting the subject
in freefall, without a separate pose table to keep in sync.

`{ACCENT_LINE}` is "A faint **{ACCENT}** glow falls across one side of
{POSSESSIVE} face against warm dim ambient light on the other. Keep the palette
restrained — greys, olive drab and rust — with **{ACCENT}** as the only
saturated color in the frame." _only_ when something rolled for this NPC would
actually cast that glow — a lit instrument panel, neon signage, a muzzle flash
in the Backdrop scene, or a glowing/lit detail in Gear, Outfit, Headgear,
Feature or Eyes. `has_light_source()` in `generate-npc.py` checks the rolled
text of those fields against a short list of light-implying words (`glow`,
`lit`, `neon`, `lantern`, `beacon`, `readout`, `monitor`, `display`, `screen`,
`flame`, `ember`, `burning`, `instrument`, `holographic`, `headlamp`, `glaring`,
`muzzle flash`) — deliberately excluding plain daylight words like `sun`, since
natural light doesn't motivate an arbitrary saturated accent color either. When
nothing matches, `{ACCENT_LINE}` falls back to "Keep the palette restrained —
greys, olive drab and rust, with no stray saturated color." instead of
inventing a source for a color that has nothing to shine from — which used to
happen on plenty of rolls (a dim mech hangar, a dropship bay door against a
plain sky) and is why a stray green glow could land on a face with nothing
nearby to cast it.

### Token (1024x1280, then RMBG to a transparent PNG)

> A full-body character illustration of **{ROLE}**, **{AGE}**, standing at full
> adult height and facing the viewer, entire body visible from the top of {POSSESSIVE} head to the
> soles of {POSSESSIVE} plain modern boots, no leg wraps or puttees, with clear empty
> space above and below, rendered in a
> detailed painterly illustration style with fine grain texture and clean linework,
> halftone dot shading worked into the shadows, moody cinematic lighting on the
> figure. {SUBJECT} is **{BUILD}**, with
> **{TRAITS}** **{SKIN}**, **{HAIR}**, and **{EYES}**, and **{FEATURE}**, wearing **{OUTFIT}**,
> **{FACTION}**. {POSSESSIVE} face carries **{DEMEANOR}**. {SUBJECT} carries
> **{GEAR}**. {SUBJECT} is
> **{STANCE}**, both boots planted and fully visible, {POSSESSIVE} face toward the
> viewer — a relaxed, natural pose with the arms free, not a rigid attention
> stance with the hands pinned at the sides. **{ACCENT_LINE}** The background alone
> is a solid flat plain white, no texture, no
> gradient, no shadow, no environment. Centered composition, dramatic lighting,
> isolated character illustration, clean silhouette. Painterly illustration throughout with
> visible brushwork, heavy fine grain texture over every surface, and dense
> halftone dot screentone worked deep into the shadows, matching the same painterly
> rendering as the portrait shot.

`{ACCENT_LINE}` here is "Keep the palette restrained — greys, olive drab and
rust — with a single **{ACCENT}** glow the only saturated color.", gated the
same way as the portrait's — except the token has no backdrop at all (it's
flat white for RMBG), so only an equipped source counts: something glowing or
lit in the rolled Gear, Outfit, Headgear, Feature or Eyes. No match falls back
to "Keep the palette restrained — greys, olive drab and rust, with no stray
saturated color." See the portrait section above for the word list.

The token template names the footwear outright - "plain modern boots, no leg
wraps or puttees" - because with nothing said about them the campaign's
painterly style kept defaulting to wrapped WWI-style puttees rising from the
boot tops, the same kind of drift the Age table fights with an explicit "fully
grown adult". Outfit bullets that specify their own footwear (the knee boots,
thigh-high boots and so on in `Outfit (she) +`) still win, since they land
later in the prompt and are far more specific.

The `even lighting` / flat-background phrasing this used to carry was flattening
the whole render toward a clean cel-shaded look rather than just the background —
`{ACCENT}` aside, the token came out visibly less painterly than the portrait even
though both prompts asserted the same style words. Scoping "no texture, no
gradient" to "the background alone" and giving the figure its own "moody
cinematic lighting" / "dramatic lighting" cue keeps the flat cutout background
Comfy's RMBG pass needs, without pulling the figure's rendering along with it.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt — the same
generation settings as every other prompt file in this folder.
