# Random NPC Generator Tables

Roll tables for `Scripts/generate-npc.py`, which rolls one human NPC from these
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

`||` splits a bullet into segments. Nine tables use it:

- **Age** and **Build** bullets carry a paired flag. `|| young` on an Age entry
  is an NPC under twenty: it swaps the prompt's "a fully grown adult" opening
  and its adult face clause for the young forms. `|| figure` on a Build entry
  marks a build written in terms of an adult woman's figure — bust, hips, waist
  — and those bullets are dropped from the pool whenever the Age roll came up
  `young`, so the unflagged builds are what a late-teen NPC rolls from. Keep
  enough of them to stay varied. Forcing both at once with `--set-trait` is an
  error rather than a silent pairing.
- **Gear** and **Stance** bullets may end `|| hands`. On a Gear entry that means
  the item occupies at least one hand or arm; on a Stance entry it means the
  pose needs both hands free. Stance is rolled after Gear and filtered against
  it, so an NPC never ends up holding a rifle in both hands while standing with
  those hands in their pockets. Tag any new bullet the same way — an untagged
  one is treated as hands-free.
- The same two tables may also carry `|| gun`. On a Gear entry that marks the
  item as an actual firearm held in hand; on a Stance entry it marks a pose
  that describes aiming, firing or otherwise handling a weapon — one the Gear
  roll has to supply, so a gun pose is never rolled for an NPC whose Gear came
  up a data-slate or a multitool. A bullet can carry both flags at once,
  `|| hands gun`. Stance poses that reference a weapon do so generically —
  "raising it", "sighting down it" — since the Gear line earlier in the prompt
  has already named the specific weapon; naming it twice would just contradict
  itself if the two ever disagreed.
- **Backdrop** bullets carry three segments: the shot's opening phrase, the
  scene sentence, then optional flags. There are two: `nogear` drops the
  "carries <Gear>" sentence for a scene that already puts something in the
  subject's hands, and `weather` marks a scene as outdoors, so a Weather roll
  can be dropped into it. A bullet may carry both — `|| nogear weather`. The
  comment above that table has the rest.
- **Weather** bullets may end `|| clear`, meaning the bullet contributes nothing
  to the prompt. Weather only reaches a portrait whose Backdrop is flagged
  `weather`, and never reaches the token at all.
- **Role** bullets may end `|| mil`, marking that occupation as active-duty
  military or paramilitary — a soldier, pilot, medic, comms operator or the
  like. It gates the Faction, Outfit and Gear rolls that follow it, because a
  civilian may carry any gear they like, including military-issue weapons, but
  shouldn't turn up in a duty uniform, while a military NPC should almost
  always be in one and armed. **Faction** and **Outfit** bullets may in turn
  carry `|| civ` or `|| mil`: `civ` reads as plainly civilian dress and is
  dropped from the pool for a `mil` Role, `mil` reads as an actual issued
  uniform and is dropped for a civilian (unflagged) Role instead. A bullet with
  neither flag is neutral and reachable either way — most Outfit entries stay
  this way, the same as a build or gear item with no flag at all. **Gear**
  bullets may also carry `|| mil`, marking an actual weapon or piece of
  military-issue equipment.

  Three more flags on Gear, plus one on Outfit, are read by
  `apply_gear_policy()` rather than by the civ/mil split above — see the
  comments on the Gear and Outfit tables themselves for the full detail:
  `weapon` (an actual weapon, as opposed to equipment that's merely `mil`),
  `simple` (a `weapon` small and pocketable enough for a role that should
  rarely be armed), and `sidearm` (a bullet that explicitly includes a
  holstered or worn pistol). A `mil` Role's Gear roll is now restricted to
  `sidearm`-flagged bullets — always armed with at least a holstered pistol,
  not just usually — with the pistol+rifle compound bullets weighted heavier
  so a rifle on top of it is the common case rather than the rare one.
  Outfit's `notac` keeps a handful of elaborate or traditional outfits (a
  kimono, shrine robes) from ever pairing with `mil`-flagged Gear.

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

- close-cropped black hair
- a shaved head with old surgical scarring at the temple
- long dark hair pulled back in a practical braid
- an untidy mop of curls
- silver-grey hair cut short and severe
- shoulder-length hair, half of it dyed a faded synthetic color
- a tight coil of locs gathered at the nape
- a slicked-back corporate cut, not one strand out of place
- hair hacked off short and uneven, clearly self-cut
- long hair worn loose and unkempt, shoved back out of the face
- a high, tight topknot
- greying hair tied back in a short tail
- a wrapped headscarf with a few strands escaping at the temple
- a choppy shoulder-length cut, dark with subtle magenta undertones
- dark wavy hair caught mid-motion in the wind
- a short choppy black cut, spiky and layered at the crown, long bangs falling loose across the brow
- a wild untamed mane of hair, layered in heavy flicks that sweep back and outward, long strands falling either side of the face
- long dark hair worn loose past the shoulders, a heavy fringe hanging over one eye and a single stray strand standing up at the crown
- shoulder-length hair with a loose wave through it, swept back off the face and tucked behind one ear
- loose hair falling past the shoulders and caught by the wind, a small metal clip holding one side back

## Hair (she) +

<!--
  '+' means these are added to the Hair table rather than replacing it, so a
  woman can still roll any of the neutral cuts above.
-->

- long hair spilling loose over the shoulders in soft waves
- an elaborate crown of braids pinned close to the head
- a sleek dark bob cut level with the jaw
- a long ponytail pulled through the back of a worn cap
- hair swept up in a loose bun already falling apart
- twin braids tied off with frayed cord
- a short silver-white bob with long bangs swept across one eye
- long white hair worn loose, a few strands falling across the face
- long dark hair spilling well past the shoulders, pushed back off the brow
- two-tone hair, dark over a bleached pale underlayer
- a chin-length platinum cut with sharply angled bangs
- long hair loose on one side and cropped short above the other ear
- a heavy dark braid falling past the shoulder
- fine ash-blonde hair cut level with the jaw
- thick auburn hair pinned up off the collar
- a short black bob with a single bright-streaked forelock
- long pale silver-white hair fading to green at the tips
- long dirty-blonde hair fading pale at the tips, cut with blunt bangs
- a short blonde bob with a loose curling cowlick
- a short black bob left deliberately choppy, the ends spiked and uneven, long bangs swept across one eye
- a high ponytail tied off loose and messy, long strands left free either side of the face
- hair worn poker-straight and very long, falling well past the waist, a long fringe swept down one side of the face
- a pale chin-length bob with a straight-cut fringe
- a lavender-grey bob swept low across one eye
- a long teal double braid falling past the waist
- black hair cut in a blunt chin-length bob with heavy straight bangs
- a long twin-tail, loose strands pulled forward across one shoulder
- a messy silver-lavender topknot, one side shaved close beneath it
- a long single braid, loose strands escaping at the crown
- hair gathered into twin space buns, loose strands falling free at the temples
- a high ponytail in fiery orange-red fading to dark roots, choppy bangs falling across one eye
- a pale lavender bob with a sharp side-swept fringe and a single streaked strand
- a silver-white bob with a pair of small horn-shaped ornamental clips swept back at the temples

## Hair (he) +

<!--
  The masculine counterpart, additive the same way — a man can still roll any
  of the neutral cuts above.
-->

- sandy hair going prematurely white at the temples
- a close fade with a longer sweep left on top
- salt-and-pepper hair cropped close
- a high-and-tight regulation cut, sidewalls shaved to the skin
- a hairline well back at the temples, what is left kept clipped short
- thick dark hair swept back off the brow, a shade too long for regulation

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

## Headgear (she) +

- x2 {Subject} {wear} a slim hairband holding the hair back off {possessive} face.
- {Subject} {wear} a wide fabric band knotted at the back of {possessive} head, hair gathered behind it.

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

## Demeanor (she) +

- a warm, open smile that reaches the eyes
- a knowing look, one eyebrow fractionally raised
- a soft, unhurried expression that gives nothing away
- a bright, quick grin
- a cool, composed poise that does not invite argument
- a narrow-eyed, studious focus, lips slightly parted mid-read
- a lazy, half-lidded stare around a lit cigarette, faintly unimpressed

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

## Gear

<!--
  '|| mil' marks an actual weapon or piece of military-issue equipment - see
  the note on it near the top of this file.

  Three more flags layer on top of it, all read by apply_gear_policy() in the
  script rather than by filter_by_mil():

  - 'weapon' marks a bullet as an actual weapon - a firearm, a blade, a
    polearm - as opposed to equipment that just happens to be 'mil' (a radio,
    a backpack, magazine pouches with nothing on the hip to fill them). This
    is what GEAR_POLICY's Officials and Criminals tiers key off: Officials
    almost never roll a 'weapon' bullet at all, Criminals are biased toward
    rolling one.
  - 'simple' marks a 'weapon' bullet as small and pocketable - a knife, a
    single holstered or worn pistol - as opposed to something that reads as
    a real armament: a rifle, a katana drawn, twin pistols raised. This is
    the tier an armed Official is allowed to roll.
  - 'sidearm' marks a bullet that explicitly includes a holstered or openly
    worn pistol, alone or paired with a slung primary weapon (a rifle, a
    carbine). A mil-flagged Role's Gear roll is restricted to this set - see
    apply_gear_policy() - so "always at least a holstered pistol" is a
    guarantee about the bullet's text, not a weighting. A bullet gripped or
    raised in the hands doesn't count, even if it's a single pistol: that's
    reachable by everyone including a mil Role, just not part of the
    guaranteed baseline.

  A civilian (unflagged) Role rolls this table exactly as before - none of
  the three flags do anything without GEAR_POLICY or a mil Role in play.
-->

- a battered data-slate tucked under one arm || hands
- a heavy multitool holstered at the hip
- a sidearm holstered high on a chest rig || mil weapon simple sidearm
- a bullpup service carbine slung muzzle-down across {possessive} chest on its sling || mil weapon
- a bullpup service carbine held at a low ready in both hands, rail-mounted optic on top || hands gun mil weapon
- a katana with a colored glowing accent along its edge slung over {possessive} shoulder || mil weapon
- a katana with a colored glowing accent along its edge held in {possessive} hands || hands mil weapon
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
- a service pistol worn openly at the thigh || mil weapon simple sidearm
- a folded maintenance drone perched dormant on one shoulder
- a compact sidearm holstered at the hip and a utility belt of pouches at the waist || mil weapon simple sidearm
- a sheathed katana crossed against {possessive} back alongside a second, shorter blade || mil weapon
- a suppressed precision rifle with a rail-mounted optic, slung muzzle-up over one shoulder, one hand resting on the sling at {possessive} chest || hands gun mil weapon
- a battered leather-bound ledger tucked in a breast pocket, worn soft from handling
- an AK-pattern assault rifle with a distinctive curved magazine held across {possessive} body || hands gun mil weapon
- a loaded tactical backpack slung from one shoulder || mil
- a suppressed short-barrelled carbine carried muzzle-down in one hand || hands gun mil weapon
- a hard-shelled assault pack worn high on the back, its straps cinched across the chest || mil
- a drop-leg holster rig and magazine pouches strapped down one thigh || mil weapon simple sidearm
- a compact field radio in a chest pouch, its stub antenna angled up past {possessive} shoulder || mil
- a slab-sided equipment case clipped to the harness at {possessive} hip
- a sidearm gripped and raised in both hands, sighted dead level at the viewer || hands gun mil weapon simple
- an oversized rail cannon gripped and leveled at the viewer with both hands, a thick barrel shroud and boxy under-slung magazine || hands gun mil weapon
- twin sidearms held akimbo, one arm thrust forward and the other braced out to the side || hands gun mil weapon
- a service rifle held loosely in both hands at an easy, unhurried low ready || hands gun mil weapon
- twin sidearms held low and loose in both hands, muzzles angled down at {possessive} sides || hands gun mil weapon
- a compact twin-thruster pack strapped across {possessive} back, its vents lit with a colored glow
- a folded oilpaper parasol held in one hand, its tip braced against the ground || hands
- a small pale fox cradled against the chest in both arms || hands
- a lacquered walking stick gripped in one hand, weight braced into it || hands
- a long polearm banded in trailing red cord, planted butt-down and held upright in one hand || hands mil weapon
- a long suppressed sniper rifle with a scope, its stock stencilled with a small painted tally number, slung across {possessive} back || mil weapon
- a fist-sized holographic sphere hovering just above one open palm, its surface a shifting lattice of glowing fracture-lines and readouts
- a translucent holographic data-sheet held up in both hands, dense scrolling text glowing across its surface || hands
- a pair of oversized clawed gauntlets, a single sensor node glowing in each palm || hands mil weapon
- x4 a sidearm holstered at the hip and a service rifle slung muzzle-down across {possessive} chest || mil weapon sidearm
- x3 a service pistol worn openly at the thigh and a bullpup carbine slung across {possessive} back || mil weapon sidearm
- x3 a holstered sidearm and a suppressed carbine slung muzzle-down over one shoulder || mil weapon sidearm
- a plain combat knife sheathed at the hip || weapon simple
- a folding push-dagger tucked into a boot sheath || weapon simple
- a compact hold-out pistol tucked into a shoulder rig, mostly hidden under a jacket || weapon simple
- a cracked-open slate bristling with jack cables and cracking tools, plainly meant for breaking into things it shouldn't || hands

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

  A third '||' segment carries flags. The only one is 'nogear', which drops
  the "carries <Gear>" sentence for scenes that already put a weapon in the
  subject's hands - without it the gunfight and blade-draw scenes stacked a
  rolled rifle on top of the weapons they hand out, and the NPC came out
  carrying three.

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
