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

`||` splits a bullet into segments. Thirteen tables use it:

- **Age** and **Build** bullets carry a paired flag. `|| young` on an Age entry
  is an NPC under twenty: it swaps the prompt's "a fully grown adult" opening
  and its adult face clause for the young forms. `|| figure` on a Build entry
  marks a build written in terms of an adult woman's figure — bust, hips, waist
  — and those bullets are dropped from the pool whenever the Age roll came up
  `young`, so the unflagged builds are what a late-teen NPC rolls from. Keep
  enough of them to stay varied. The filter runs both ways: forcing a `figure`
  Build with `--set-trait` drops the `young` bullets from the Age pool instead,
  so an explicit build never collides with a randomly rolled teenager. Forcing
  _both_ into a contradiction is an error rather than a silent pairing.
- **Gear**, **Weapon** and **Stance** bullets may end `|| hands`. On a Gear or
  Weapon entry that means the item occupies at least one hand or arm; on a
  Stance entry it means the pose needs both hands free. Stance is rolled
  last, after Weapon and Gear alike, and filtered against the two of them
  together, so an NPC never ends up holding something in both hands while
  standing with those hands in their pockets.
  Tag any new bullet the same way — an untagged one is treated as hands-free.
- **Weapon** and **Stance** bullets may also carry `|| gun`, and a **Stance**
  bullet may separately carry `|| armed`. On a Weapon entry `gun` marks the
  item as an actual firearm held in hand. On a Stance entry the two form a
  hierarchy: `armed` marks a pose that references a weapon of any kind — a
  blade held, a hilt gripped, a weapon raised overhead — while `gun` marks
  the narrower case of a firearm specifically being aimed, fired or otherwise
  handled. Both read off the Weapon roll: an NPC whose Weapon came up empty
  drops both `armed` and `gun` poses, one whose Weapon is a non-firearm
  weapon drops only `gun` and keeps `armed` reachable, and one whose Weapon
  is a firearm reaches both. A bullet can carry both flags at once,
  `|| hands gun`. Stance poses that reference a weapon do so generically —
  "raising it", "sighting down it" — since the Weapon line earlier in the
  prompt has already named the specific weapon; naming it twice would just
  contradict itself if the two ever disagreed.
- **Backdrop** bullets carry three segments: the shot's opening phrase, the
  scene sentence, then optional flags. Two are behavioural — `nogear` and
  `weather`, and a bullet may carry both, `|| nogear weather`. `weather` marks a scene
  as outdoors, so a Weather roll can be dropped into it. `nogear` marks a
  scene that already puts something in the subject's hands, and has two
  effects: it drops the whole merged Weapon+Gear "carries ..." sentence from
  the portrait (the token keeps it, since the token has no scene to
  contradict), and it also keeps the Gear roll itself off any bullet flagged
  `|| hands` — so a `hands`-flagged Gear bullet you add will never turn up
  paired with a `nogear` scene. The rest are **occupation flags** — `cockpit`,
  `mechwork`, `frontline`, `barkeep` and the like — which keep a scene that
  asserts a job off the Roles that do not hold it: only a pilot rolls a
  cockpit, only the bar owner rolls the scene behind their own counter. Each
  one is defined in `BACKDROP_ROLES` in `generate-npc.py`, against either the
  Role categories that may roll it or an exact Role bullet. This is a hard
  exclusion, like `## Gear`'s `admin` lock and unlike every preference filter
  in the file: it never falls back to the whole pool, because falling back
  would hand the scene to the Role it was kept from. An unflagged bullet is
  neutral and reachable by everyone, which is what roughly 180 of these are —
  keep it that way unless the scene puts the subject *doing* the job rather
  than merely standing somewhere. The comment above that table has the rest.
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
- **Faction** bullets carry three segments too — the affiliation's name, then
  an optional visual signature, then flags. The name is what the dossier
  prints under "Affiliation" and what the byline names; the visual is what
  reaches the clothing sentence in the image prompt, in place of the name,
  and is deliberately left empty for the two non-affiliations. It is written
  to describe what Outfit's own bullet does not — fabric, tailoring,
  insignia, patina — since the two used to compete for the same slot and the
  more specific Outfit clause always won; a visual segment left empty writes
  the middle segment blank, the same idiom Hair colour uses above.
- **Glow placement** bullets may end `|| scene`, marking a placement that
  puts the light out in the environment - on a wall, in the air, across the
  ground. The glow has two possible sources: something the NPC wears or
  carries, or the Backdrop itself. Only the second can light a wall behind
  them, so a `scene` placement is dropped unless the rolled Backdrop is what
  casts the light (`has_light_source()` again, the same test that decides
  whether there is a glow sentence at all). An unflagged bullet keeps the
  light on or immediately around the figure and is reachable either way -
  most should stay that way, since the equipped source is the common one.
  The table is rolled _after_ Backdrop for exactly this reason.
- **Weather** bullets may end `|| clear`, meaning the bullet contributes nothing
  to the prompt. Weather only reaches a portrait whose Backdrop is flagged
  `weather`, and never reaches the token at all.
- **Role** bullets may end `|| mil`, marking that occupation as active-duty
  military or paramilitary — a soldier, pilot, medic, comms operator or the
  like. It gates the Faction, Outfit and Weapon rolls that follow it —
  Faction and Outfit through the `civ`/`mil` split described next, Weapon
  through `apply_weapon_policy()`. Gear is not Role-gated at all, because a
  civilian may carry any gear or weapon they like, including military-issue
  ones, but shouldn't turn up in a duty uniform, while a military NPC should
  almost always be in one and armed. **Faction** and **Outfit** bullets may
  in turn carry `|| civ` or `|| mil`: `civ` reads as plainly civilian dress
  and is dropped from the pool for a `mil` Role, `mil` reads as an actual
  issued uniform and is dropped for a civilian (unflagged) Role instead. A
  bullet with neither flag is neutral and reachable either way — most Outfit
  entries stay this way, the same as a build or gear item with no flag at
  all. The flag lives in Faction's third segment and Outfit's second, since
  the two tables carry different numbers of prose segments — see the Faction
  item above. **Gear** and **Weapon** bullets may also carry `|| mil`, marking
  the item as military-issue — equipment on a Gear entry, an actual issued
  weapon on a Weapon entry, since every bullet in that table already reads
  as one.

  **Outfit** and **Faction** bullets may also carry `|| dressy`, a third axis
  orthogonal to both `civ`/`mil` and to theme. It marks dress that is
  ceremonial, formal or finely made — gold thread, lacquer, brocade,
  ornament — and it is gated on the _kind of work_ the Role is, through
  `DRESS_POLICY` in the script rather than through a flag on the Role bullet:
  `ROLE_CATEGORIES` already knows which job an occupation is, and restating
  that here would only let the two drift. Roles filed under `Laborers` or
  `Technicians` are `plain` and everything else is unconstrained.

  The two tables consume the flag differently on purpose. A `dressy` **Outfit**
  is dropped from a `plain` Role's pool. A `dressy` **Faction** is not: it
  keeps its place, and only its visual segment is suppressed, so the dossier
  still prints the affiliation while the image prompt loses the brocade. A
  dockworker employed by the Karrakin Trade Baronies is good flavour; a
  dockworker dressed as a baron is what this exists to stop.

  `dressy` is **not** `notac`, however much the two overlap. `notac` means
  "do not pair with tactical gear" and covers rags as readily as finery — a
  dockworker in ragged cloth bindings, a travel-worn robe or a weathered
  haori is entirely plausible, and several of those read as _poorer_ than the
  default coveralls. The two disagree on seven of the thirteen `notac`
  bullets in the base table. Flag finery, not tradition.

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
  elaborate or traditional outfits (a kimono, shrine robes) from pairing with
  `mil`-flagged Weapon and Gear alike. On the Weapon side it is a preference
  rather than a rule: the `sidearm` restriction above is applied first and
  outranks it, so an elaborately dressed `mil` Role is still armed.

- **Headgear** bullets may carry `|| hardtech`, marking modern technology worn
  on the head — helmets sealed or open, visor and lens rigs, sensor and
  night-vision hardware, breather masks, comms headsets, anything strung with
  cabling or seated on jacks, and powered or cybernetic pieces. Those bullets
  are dropped whenever the Outfit roll came up `notac`, so an elaborate or
  traditional outfit is not crowned with a sealed flight helmet. It is the
  third and last table `notac` reaches, after Weapon and Gear. Soft goods —
  cloth, straw, woven, leather and fur hats, caps, hoods, bandanas and
  headbands — plain eyewear, and the traditional and ceremonial register are
  all deliberately unflagged: those are what a kimono _should_ reach, and a
  kabuto above one is the point rather than an oversight. Two boundaries
  worth knowing before you flag a new bullet: goggles count as eyewear, not
  hardware, and a traditional hat with a mask beneath it is the hat.
- **Headgear** and **Gear** bullets may also carry `|| helmet`. On a Headgear
  entry it means a helmet actually worn on the head; on a Gear entry it means
  a helmet carried rather than worn. A helmet on the head drops the carried
  ones from the Gear pool, so nobody turns up wearing a sealed tactical helmet
  with a second helmet tucked under one arm. Gear yields, the same way it
  yields to a `hands` Weapon.
  This is much narrower than `hardtech`, and deliberately so: a headset, a
  brow visor or an ear implant leaves the crown free, and a helmet held under
  the arm beside one of those reads well — a pilot between sorties, which is
  what the Gear bullet is for. Flag only the bullets where the head is
  actually inside a helmet. A kabuto counts and carries `helmet` without
  `hardtech`, since the clash is one of silhouette rather than register.
- **Hair** bullets may carry `|| updo`, marking a cut whose mass sits on top
  of the skull — a topknot, a high ponytail, twin space buns, a bun crowned
  with a pin or a flower. Those are dropped whenever the Headgear roll came up
  `helmet`, so nothing renders a bun growing through a flight helmet. Headgear
  is what yields on a fresh roll, since Hair is drawn first; the filter runs
  both ways, so a pinned or `--set-trait` helmet drops the `updo` cuts from the
  Hair pool instead. Forcing both by hand is honoured rather than refused, the
  same way two helmets are.
  It is gated on `helmet` rather than `hardtech` for the reason the flag above
  gives: a headset, a brow visor or an ear implant leaves the crown free, and a
  topknot above one is fine. Flag only what stands proud of the skull — hair
  merely *pinned up off the collar*, a braid crown pinned close to the head, a
  low bun, a bob or anything cropped all lie flat, and those are exactly the
  cuts a helmet goes on over.
- **Hair** bullets may also carry `|| covered`, marking a cut that names
  something *worn* as part of the phrase — a wrapped headscarf, a ponytail
  pulled through the back of a cap, ponytails held by a headset band. The
  bullet has already put an object on the head, so the Headgear pool is cut to
  the one bullet flagged `bare` and the NPC comes out bare-headed; anything
  else would describe two coverings in the same place.
  The headgear *clause* then drops out of the prompt entirely, rather than
  printing the bare bullet's own sentence. "A wrapped headscarf ..." and "She
  is bare-headed." in one prompt contradict each other as flatly as the hat
  did, and a render told both does not get to pick the sensible one. The hair
  phrase is the headgear for these bullets, so the clause is what gives way —
  in the portrait, the token and the 3D back view alike.
  This is a strictly harder filter than `updo`, and gated wider on purpose.
  `updo` drops only `helmet` and hands back sixty other bullets, because a
  bun and a brow visor coexist; `covered` has nothing to hand back, because a
  headscarf leaves no room for a hairband either. It is still not a *lock* —
  a file with no `bare` bullet gets the whole pool rather than an empty roll.
  Like `updo` the filter runs both ways: a pinned or `--set-trait` Headgear
  that is not `bare` drops the `covered` cuts from the Hair pool instead, and
  forcing both by hand is honoured rather than refused.
  Flag only a thing genuinely *worn*. Hair ornaments are not: a clip, a
  ribbon, an ornamental pin, a flower or a mechanical binder is part of the
  hairstyle and leaves the head free for a hat.
- The single **Headgear** bullet that leaves the head bare carries `|| bare`,
  which is what `covered` filters down to. It is a marker rather than a
  preference — nothing is dropped *for* it — and it exists for the same
  reason `none` does on Weapon: a filter needs to be able to name the empty
  bullet without matching on its prose. Exactly one bullet should carry it.
- A **Gear** bullet may carry a **role lock**, of which `admin` is so far the
  only one. It confines that bullet to the occupations named against the flag
  in `ROLE_LOCKS` in `generate-npc.py` — `admin` is a colonial administrator's
  and no one else's — and it is the one hard filter in this file. Every other
  flag here is a preference that hands the whole pool back rather than leave
  the roll with nothing; a lock never yields, since yielding would hand the
  item to the very Role it was kept from. Use it only where the object is an
  emblem of the job rather than a tool of it, and see the comment on the Gear
  table for what that distinction is doing. A lock flag not defined in
  `ROLE_LOCKS`, or one naming a Role the Role table has since reworded, fails
  `test/test_role_lock.py`.

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
it is worse than nothing: `Skin`, `Eyes`, `Demeanor`, `Glow colour`, `Height` and
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

  A bullet names a decade and nothing else. The trailing look-clauses these
  used to carry - "the first lines already setting around the eyes", "face
  lean and weathered" - are the part the model was already shown to ignore
  when a bullet gave it nothing numeric to hold, so they bought no render and
  spent tokens against Krea 2's 512 ceiling. The two under-twenty bullets are
  the exception and keep their explicit number, because the templates assert
  "a fully grown adult" in the highest-signal position and the model believes
  that over a bare "late teens". See "Name the number" in docs/generate-npc.md.
-->

- in {possessive} late teens, sixteen or seventeen || young
- x2 just nineteen || young
- x4 twenty-one or twenty-two
- x3 in {possessive} mid-twenties
- x2 in {possessive} late twenties
- x3 in {possessive} early thirties
- x2 in {possessive} mid-thirties
- in {possessive} forties
- in {possessive} fifties
- in {possessive} sixties

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
- x2 athletic and fit, narrow-waisted and very full-busted || figure
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

<!--
  Placing the '{colour}' slot straight after an article - "a {colour} bob" -
  makes the bullet depend on every ## Hair colour base starting with a
  consonant, since nothing in the script turns that 'a' into 'an'; four
  bullets in ## Hair (she) + already do, and the rule they rest on is
  documented on the colour table below.
-->

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
- a high, tight {colour} topknot || updo
- {colour} hair tied back in a short tail
- a wrapped headscarf with a few {colour} strands escaping at the temple || covered
- a choppy shoulder-length {colour} cut
- {colour} wavy hair caught mid-motion in the wind
- a short choppy {colour} cut, spiky and layered at the crown, long bangs falling loose across the brow
- a wild untamed mane of {colour} hair, layered in heavy flicks that sweep back and outward, long strands falling either side of the face
- long {colour} hair worn loose past the shoulders, a heavy fringe hanging over one eye and a single stray strand standing up at the crown
- shoulder-length {colour} hair with a loose wave through it, swept back off the face and tucked behind one ear
- loose {colour} hair falling past the shoulders and caught by the wind, a small metal clip holding one side back
- long {colour} hair falling past the shoulders, cut with sharp jagged bangs across the brow
- long wavy {colour} hair falling loose past the shoulders, framing the face
- short wavy {colour} hair falling to the jaw, one side swept over an eye
- {colour} hair swept into a high ponytail bound near the crown, loose strands framing the face || updo
- a sharp chin-length {colour} bob, its long fringe swept over one eye
- a tousled chin-length {colour} bob with choppy side-swept bangs
- long tousled {colour} waves spilling loosely over one shoulder

## Hair (she) +

<!--
  '+' means these are added to the Hair table rather than replacing it, so a
  woman can still roll any of the neutral cuts above.
-->

- long {colour} hair spilling loose over the shoulders in soft waves
- an elaborate crown of {colour} braids pinned close to the head
- a sleek {colour} bob cut level with the jaw
- a long {colour} ponytail pulled through the back of a worn cap || covered
- {colour} hair swept up in a loose bun already falling apart || updo
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
- a high {colour} ponytail tied off loose and messy, long strands left free either side of the face || updo
- {colour} hair worn poker-straight and very long, falling well past the waist, a long fringe swept down one side of the face
- a chin-length {colour} bob with a straight-cut fringe
- a {colour} bob swept low across one eye
- a long {colour} double braid falling past the waist
- {colour} hair cut in a blunt chin-length bob with heavy straight bangs
- a long {colour} twin-tail, loose strands pulled forward across one shoulder
- a messy {colour} topknot, one side shaved close beneath it || updo
- a long single {colour} braid, loose strands escaping at the crown
- {colour} hair gathered into twin space buns, loose strands falling free at the temples || updo
- a high {colour} ponytail, choppy bangs falling across one eye || updo
- a {colour} bob with a sharp side-swept fringe and a single streaked strand
- a {colour} bob with a pair of small horn-shaped ornamental clips swept back at the temples
- a {colour} bob with a blunt fringe
- twin high {colour} ponytails held back by the band of a chunky headset, a long fringe swept across one brow || updo covered
- twin high {colour} ponytails clipped at the base by a segmented mechanical binder, sweeping loose past the shoulders || updo
- shoulder-length {colour} hair, center-parted with a long face-framing fringe
- {colour} hair swept back into a neat low bun, held with a single ornamental pin
- {colour} hair swept up in a bun crowned with a floral hairpin ornament, loose strands and bangs falling forward across the brow || updo
- {colour} hair swept up into a high bun, secured with ornamental pins and a trailing ribbon || updo
- {colour} hair swept up, an ornamental flower and dangling metal pins gathered at the crown || updo

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
- magenta-tinted black
- two-tone || dark over a bleached pale underlayer
- pale silver-white || fading to green at the tips
- fiery orange-red || fading to dark roots
- dirty-blonde || fading pale at the tips
- vivid crimson red
- black || with the fringe dipped a pale contrasting shade
- dark cobalt blue
- jade green
- silver-white
- raven black
- deep crimson
- bubblegum pink
- vivid magenta-red
- dusty coral-pink
- dark garnet red

## Hair colour (she) +

<!--
  Added to the shared colours above rather than replacing them - a woman rolls
  every neutral shade as well as these.

  Three segments, exactly as the base table: colour || trailing clause || flags.
  See the Hair colour item near the top of this file.
-->

- dusty pink

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
- a fitted eyepatch covering one eye
- a curling inked tattoo down one forearm
- a fitted leather eyepatch over one eye
- a compact comms module fused above one ear, a cable disappearing into {possessive} hairline || @cyberpunk
- a fully cybernetic arm plated in matte black, every joint lit along the seam || @cyberpunk
- a fused cybernetic faceplate sheathing half {possessive} skull, a single optic bar glowing level across the brow
- a geometric circuit-patterned tattoo banding one shoulder || @cyberpunk

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
- a climbing stack of small hoop and cuff piercings up one ear, a single dangling stud lit faintly || @cyberpunk

## Feature (he) +

<!--
  '+' means these are added to the Feature table rather than replacing it, so a
  man can still roll any of the neutral marks above.
-->

- x2 permanently a few days past a decent shave
- a close-trimmed beard going grey at the chin
- a heavy moustache, grey at the edges
- a scatter of freckles across the nose and cheeks

## Headgear

<!--
  Complete sentences, like Backdrop - a fragment would not sit cleanly between
  the outfit clause and the expression. Roughly a third of rolls come up
  bare-headed; reweight that first bullet to change how often headgear shows.
-->

- x6 {Subject} {is_are} bare-headed. || bare
- x2 {Subject} {wear} a padded flight headset, earcups clamped over the ears and a boom mic swung down to the corner of {possessive} mouth, a coiled cable trailing from one side. || hardtech
- {Subject} {wear} a lightweight comms earpiece with a slender mic arm tracking along the jaw. || hardtech
- {Subject} {wear} scratched flight goggles pushed up onto {possessive} forehead.
- {Subject} {wear} a soft crew cap pushed back on {possessive} head.
- {Subject} {wear} a padded pilot skullcap with the visor unclipped and folded back. || hardtech
- {Subject} {wear} a rolled bandana tied across {possessive} brow.
- {Subject} {wear} a knitted watch cap pulled down to the eyebrows.
- {Subject} {wear} a composite ballistic helmet with its rail-mounted visor hinged up. || hardtech helmet
- {Subject} {wear} a full flight helmet in scuffed pale grey-white, a tinted visor panel down over the eyes and a small lit accent lens at the temple, a thin tether cable trailing from the back. || hardtech helmet
- {Subject} {wear} a monocular sensor rig strapped over one eye, its lens faintly lit. || hardtech
- {Subject} {wear} heavy ear defenders slung around {possessive} neck rather than on {possessive} head. || hardtech
- {Subject} {wear} a welding visor tipped back on top of {possessive} head. || hardtech
- {Subject} {wear} a worn ushanka-style fur hat with the flaps down, a faded unit star pinned to the front.
- {Subject} {wear} a tactical cap with a small circular unit emblem, dark sunglasses beneath it. || hardtech
- {Subject} {wear} a night-vision helmet with the quad tubes flipped up clear of {possessive} eyes. || hardtech helmet
- {Subject} {wear} a sleek black mechanical headset piece mounted flush against one ear. || hardtech
- {Subject} {wear} a stiff peaked officer's cap, the brim polished and a small insignia set at the crown.
- {Subject} {wear} a hooded shroud drawn up over a full-face helmet, its visor tinted dark and a breather mask sealed across the lower face. || hardtech helmet
- {Subject} {wear} a deep hood drawn up, a pair of goggles clipped across the brow of it.
- {Subject} {wear} a flat-brimmed ball cap with a small stitched patch at the front.
- {Subject} {wear} an open-face crash helmet with the visor swung up clear of {possessive} eyes. || hardtech helmet
- {Subject} {wear} a ballistic helmet with its visor tipped up and a black breather mask sealed over the lower face. || hardtech helmet
- {Subject} {wear} a russet leather flight cap with ear flaps and a monocular scanner lens fixed down over one eye. || hardtech
- {Subject} {wear} a wide woven sedge hat, its brim throwing {possessive} face into shadow.
- {Subject} {wear} a pale cloth wrapped loosely over the lower face beneath a wide straw hat.
- {Subject} {wear} a sleek integrated visor plate curving back over one ear, thin cable jacks seated at the jaw and temple, a faint accent light glowing along its edge. || hardtech
- {Subject} {wear} a bulky visored rig clamped down over the eyes, a stub antenna and a cluster of cable jacks rising from the crown, a single indicator light glowing beneath the visor's edge. || hardtech
- {Subject} {wear} a gold-trimmed headset clamped over one ear, a coiled cable trailing from it down past {possessive} collar.
- {Subject} {wear} a sleek pilot's helmet with a curved visor, faint HUD readouts scrolling across the inside of the glass and a stencilled call-sign plate set at the jaw. || hardtech helmet
- {Subject} {wear} round wire-rimmed glasses, their lenses lit faintly at the edges with a soft glow.
- {Subject} {wear} a scuffed recon helmet with a stubby antenna and an integrated comm mic curling to the jaw, cable jacks trailing from the crown to a collar rig. || hardtech helmet
- {Subject} {wear} a bulky illuminated visor rig clamped low over the eyes, graffitied casing and a stub antenna rising from one side. || hardtech
- {Subject} {wear} a curved white plate clipped snug over one ear, a short antenna-like horn rising from its crown and a thin cable trailing to the collar. || hardtech
- {Subject} {wear} a sleek red-tinted visor strapped low across the eyes, built into a close-fitted skullcap with a jack seated at one temple. || hardtech
- {Subject} {wear} a compact over-ear headset with red accent panels, a short boom mic curling toward the jaw. || hardtech
- {Subject} {wear} a pair of boxy retro-industrial headphones, worn olive-grey earcups ringed in exposed rivets and a scuffed control dial on one side. || hardtech
- {Subject} {wear} tinted wraparound sunglasses pushed rakishly up into {possessive} hair.
- {Subject} {wear} a segmented cybernetic implant sheathing one ear and running down the jaw, faint lit seams tracing its joints. || hardtech
- {Subject} {wear} a domed flight helmet in weathered burnt-orange with a full mirrored visor down, a coiled comms cable trailing from one side. || hardtech helmet
- {Subject} {wear} a compact visor rig pushed up above the brow, articulated plating framing one side of the face and a thin mic boom curving down past the cheek. || hardtech
- {Subject} {wear} a compact sensor rig clipped into {possessive} hair at the crown, trailing thin cables and a torn strip of fabric like a streamer. || hardtech
- {Subject} {wear} a slim translucent visor band across the brow, a cluster of cabling running from a port at {possessive} temple back into the rig behind {object}. || hardtech
- {Subject} {wear} a chunky over-ear headset with a lit accent ring at each cup, the band nested into {possessive} hair. || hardtech
- {Subject} {wear} a red-plated visor rig clamped down over the eyes, twin lens apertures lit faintly, a cluster of thin cables trailing back into {possessive} hair. || hardtech
- {Subject} {wear} a sleek visored headset clamped over the eyes, a hinged jaw guard sealed below it and a cluster of thin cables trailing back into {possessive} hair. || hardtech
- {Subject} {wear} a segmented white cybernetic headpiece clamped over the crown and one temple, faint cable jacks seated at the jaw. || hardtech
- {Subject} {wear} a sealed tactical helmet with a smoked visor and an integrated breather mask, a coiled comms cable trailing from the jaw. || hardtech helmet
- {Subject} {wear} a smooth blue-visored full-face helmet with a hood drawn up over it, a scarf wound loose at the throat. || hardtech helmet
- {Subject} {wear} a flat wide-brimmed lacquered hat crowned with a bird skull and trailing feathers, the brim throwing {possessive} face into shadow.
- {Subject} {wear} a bulky mechanical diagnostic rig clamped over the crown of {possessive} head, thick cabling trailing down to jacks at the collar, a status light lit at the side. || hardtech
- {Subject} {wear} a sleek angular powered helmet with raised sensor fins and a full dark visor down, a single braid of hair falling free beneath it. || hardtech helmet
- {Subject} {wear} thin rectangular glasses framing sharp eyes.
- {Subject} {wear} a sleek mechanical half-mask sealed over the nose and mouth, a small lens node mounted at the temple. || hardtech
- {Subject} {wear} a close-fitted respirator mask across the lower face beneath narrow tactical eyewear. || hardtech
- {Subject} {wear} a horned kabuto-style helmet with a trailing neck guard, its crest catching the last light. || helmet
- {Subject} {wear} a wide flat lacquered hat rimmed in gold, a single red tassel hanging from the brim.
- {Subject} {wear} a horned kabuto helmet with a scowling mempo faceplate, eyes lit with a faint red glow. || helmet
- {Subject} {wear} a wide woven hat trimmed with small curved horns and hanging tassels, a segmented mechanical mask sealed over the nose and mouth beneath it, a faint accent light glowing at the seam.
- {Subject} {wear} a wide straw hat trimmed with small hanging bells and a tattered red ribbon at the crown, rain streaming off the brim.
- {Subject} {wear} a broad ceremonial hat strung with hanging tasseled bells, an antler-like crest rising from the crown.
- {Subject} {wear} a broad woven hat bristling with jagged spikes at the crown, its brim battered and weathered.
- {Subject} {wear} a broad dark hat trimmed with hanging chain ornaments and a feather crest, the brim shadowing {possessive} eyes.
- {Subject} {wear} a wide straw hat over a patterned cloth headband tied at the brow.
- {Subject} {wear} a horned kabuto-style helmet with a riveted neck guard and cheek plates framing {possessive} face. || helmet
- {Subject} {wear} a gilt-trimmed tricorn hat pinned with a skull-and-crossbones badge and a curling plume.
- {Subject} {wear} a black tricorn hat trimmed in lace, a small skull-and-crossbones pinned above a red ribbon bow.
- {Subject} {wear} a red bandana knotted at the brow, ends trailing into windblown hair.
- {Subject} {wear} a pair of oversized over-ear headphones with a boom mic curling toward {possessive} cheek. || hardtech
- {Subject} {wear} a matte combat helmet cinched down over a full rebreather mask, hoses looping to a chest-mounted filter. || hardtech
- {Subject} {wear} a deep hood drawn low over {possessive} brow, shadowing {possessive} face down to the nose.
- {Subject} {wear} heavy over-ear headphones with a glowing status ring on each cup. || hardtech
- {Subject} {wear} a fin-eared tactical helmet with a mirrored visor. || hardtech @cyberpunk
- {Subject} {wear} a streamlined flight helmet with cable ports ringing the crown, the visor cracked open to show eyes lit faintly beneath. || hardtech @gundam
- {Subject} {wear} brass-rimmed welding goggles pushed low over a heavy over-ear headset, a cable trailing to a shoulder pack. || hardtech
- {Subject} {wear} a chrome respirator mask fitted along {possessive} jaw, a single lens glowing over one eye. || hardtech @cyberpunk
- {Subject} {wear} a pair of scuffed brass-and-leather over-ear headphones with an exposed pivot joint. || hardtech

## Headgear (she) +

- x2 {Subject} {wear} a slim hairband holding the hair back off {possessive} face.
- {Subject} {wear} a wide fabric band knotted at the back of {possessive} head, hair gathered behind it.
- {Subject} {wear} a slim glowing accent band swept back through {possessive} hair like a hairband.
- {Subject} {wear} a wide woven hat, thin red-framed glasses catching the light and a long-stemmed pipe held between {possessive} lips.
- {Subject} {wear} a wide-brimmed felt hat canted low over one eye, a long feather trailing from the band.

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
- a sly one-eyed smirk, brow arched in challenge
- a half-lidded, unbothered stare, faintly amused
- a sly, dangerous smirk, one eyebrow lifted
- a half-lidded, pleased look caught mid-blown bubblegum bubble
- a level, unblinking stare with a faint challenging smirk
- a small, contented smile with the eyes closed
- a wide-eyed, breath-held stare cast back over one shoulder, jaw tight with tension
- a sly sidelong smirk, chin tucked and eyes cutting toward the viewer
- a lazy, self-satisfied smirk, one brow lifted
- a serene, closed-eyed smile
- a wary sidelong glance, one eye narrowed

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

<!--
  Three segments: the affiliation NAME, the visual signature, then flags.

  The name is what the dossier and the Import GUI print. The visual is the
  only part that reaches the image prompt, and it is what makes this table
  worth having at all: the old single-segment form put a garment CATEGORY
  ("corporate wear", "service dress") straight after Outfit's specific garment
  description, competing for the same slot and losing every time. Deleting the
  whole Faction clause from a prompt changed the render not at all.

  So a visual describes what Outfit does not - fabric, tailoring, insignia,
  patina, and where the faction has one, colour. Never a garment category.

  Two entries are non-affiliations with nothing to show and leave the visual
  empty; build_prompts() then drops the clause entirely rather than leaving a
  doubled comma.

  '|| dressy' marks a faction whose visual signature is finery - brocade and
  gold braid, precise tailoring in white and pastels. For a Role whose work is
  manual it suppresses the VISUAL ONLY: the affiliation still reaches the
  dossier and the byline, and only the clothing sentence loses the clause. A
  dockworker employed by the Karrakin Trade Baronies is good flavour; a
  dockworker in baronial heraldry is not, and barring the faction outright
  would throw the first away to fix the second. The suppression writes the
  middle segment empty, the same idiom the two non-affiliations already use.

  '|| palette' marks a faction that asserts colours of its own. Those are
  PIGMENT - dye in cloth - and they coexist with the Glow colour, which is
  LIGHT. The closing palette line softens from "the only saturated color" to
  "the only other saturated color" when one is rolled, so the prompt stops
  claiming something the uniform contradicts. A faction without a colour
  scheme should NOT carry the flag: Unaligned, Unregistered and the colonial
  militia deliberately leave the palette unconstrained.

  Keep visuals to about a dozen words. Both prompts run close to Krea 2's
  512-token ceiling - see test/test_prompt_budget.py.
-->

- x2 Unaligned || || civ
- x2 Union Administrative Department || issued and worn thin, in faded institutional blue-grey || mil palette
- Harrison Armory || sharply pressed, high collar and polished fittings, in imperial green and gold || mil palette
- Smith-Shimano Corpro || precisely tailored with fine seam piping, in white and pale pastels || civ palette dressy
- IPS-Northstar || riveted and salt-stained heavy canvas, in rust orange || civ palette
- Karrakin Trade Baronies || heavy brocade and gold braid, an heraldic crest at the shoulder, in deep crimson || palette dressy
- Colonial militia || mismatched surplus, webbing straps and taped-over insignia || mil
- Unregistered || ||
- House Clawthorne || a purple rabbit-skull crest banner, tarnished gold trim and dangling bone charms || mil palette
- Forge Household || a quartered crimson-and-black heraldic shield stitched over the breast, tarnished brass fastenings || mil palette
- Redstar Salvage || a red five-point star roundel stitched above the chest zipper, edges frayed and sun-faded || civ palette
- Ashfall Vanguard || a red skull-and-shield roundel stitched high on one shoulder, canvas gone soft with wear || mil palette
- Diamond Line Couriers || a faded orange diamond patch stitched high on one sleeve, canvas worn thin with age || civ palette

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

  A fourth flag, 'dressy', marks dress that is ceremonial, formal or finely
  made - gold thread, lacquer, brocade, ornament - and drops it from the pool
  for a Role whose work is manual (DRESS_POLICY files Laborers and Technicians
  as 'plain'). This is what stops a dockworker rolling a gold-embroidered robe
  with a purple sash, which the civ/mil split never could: 'civ' says "not a
  uniform", not "not ceremonial".

  Do NOT flag a bullet 'dressy' just because it is 'notac'. The two overlap on
  about half the bullets and disagree on the rest: the pilgrim's robes, the
  tattered robe, the ragged cloth bindings, the travel-worn robe and the
  weathered haori are all 'notac' and none of them are finery - several read
  as poorer than the default coveralls, and a dockworker in any of them is
  entirely plausible. Flag finery, not tradition.

  A third flag, 'notac', marks an elaborate or traditional outfit - a kimono,
  shrine robes - that shouldn't turn up paired with tactical gear no matter
  how the Weapon and Gear rolls would otherwise land. It drops every
  'mil'-flagged bullet from both of those pools for that NPC - on Weapon only
  where something is left afterwards, since a 'mil' Role's 'sidearm'
  restriction runs first and being armed outranks the preference. See the
  notes on the Weapon and Gear tables below.
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
- segmented crimson-lacquered armor plates over a floral-patterned quilted robe, tasseled cords trailing from one shoulder and a wrapped bundle slung across the back || civ notac dressy
- full lacquered samurai armor in dark green and black with segmented shoulder pauldrons over a trailing hakama-style skirt, ornamental tassels at the waist || civ notac dressy
- dark samurai robes with a long crimson cloak trailing from the shoulders, one leg bared and banded with tattooed markings || civ notac dressy
- a tattered dark robe hanging open at the chest, its hems torn and trailing loose || civ notac
- a dark robe with a pale patterned collar, red fingerless gloves laced to the wrist || civ notac
- a dark patterned robe with a bright orange underlining, a string of prayer beads wound at one wrist || civ notac
- ragged wrapped cloth bindings over bare limbs, one wrist bound in worn bandaging, feet bare in simple woven sandals || civ notac
- a dark robe traced with gold embroidered trim, a purple sash knotted at the waist and small tassels hanging loose || civ notac dressy
- a dark kimono cinched with a wide white sash tied in a full bow at the back || civ notac dressy
- a fringed pleated mantle draped over the shoulders and swagged with hanging chain loops, worn over a dark strapped underlayer || civ notac dressy
- a sleeveless tank top with bandage-wrapped forearms, worn over cargo trousers slung with mismatched belt pouches and holster straps || @scav
- a fitted maroon combat tunic with layered pauldron guards over each shoulder, cinched at the waist by a wide dark sash over cropped trousers || @neosamurai
- a quilted grey duty jumpsuit with articulated knee braces, an olive sash slung across one shoulder and a leather pauldron buckled over it || @neogothic
- a short-sleeved orange-and-white uniform shirt worn under a dark tactical vest, a unit patch stitched to the shoulder || mil
- a white mechanic's coverall with red trim at the cuffs and collar, sleeves rolled past the elbow under a matching soft cap
- a fitted flight suit with crimson piping and a raised segmented shoulder guard, high collar sealed to the throat || @gundam
- a soaked black assault suit cinched under a slim chest harness, fabric clinging dark and heavy || mil
- a cropped red flight jacket, sleeves shoved up over a stripped-down underlayer, patched insignia worn soft with scavenged wear || @scav
- a weathered orange flight jumpsuit with patched cargo sleeves, worn under a trailing grey scarf || civ
- plated crimson body armor with a glowing chest core and an articulated ridged spine || @gundam
- a weathered dark-green field jacket, collar turned up, patched high on one shoulder || mil
- a scuffed flight suit unzipped low at the collar, a crash harness cinched tight across the chest || mil
- a bulky fleece-collared field jacket gathered high at the throat, cuffs frayed at the wrist || civ
- a segmented mechanical wing unit fanned wide from one shoulder, primaries tipped in bone-white feathers
- a threadbare mustard-yellow work coverall patched at both knees, a canvas tool satchel cinched to one hip || civ
- a weathered tan leather jacket rolled to the elbow, layered over a thick wrapped scarf || civ
- a cropped sleeveless hoodie worn over a bare midriff, a low-slung utility belt studded with cybernetic modules, and thigh-high leg wraps || @cyberpunk
- a sun-faded orange work jumpsuit worn under a heavy grey scarf, cuffed sleeves over grease-stained gloves, a multi-pouch tool belt cinched at the waist || civ
- a hip-length tan leather jacket worn open over a high-collared dark bodyglove, a drop-leg holster rig strapped down one thigh || civ
- a matte grey optical-camouflage suit, the light bending across it in faint rippling distortion wherever it catches an edge
- a long olive field coat over a black rollneck, a shoulder holster rig showing at the open front || civ
- a cheap dark suit with the tie pulled loose, a thin wire running from one ear down inside the collar || civ
- a sealed matte-black diving suit with its hood pushed back and the weight belt still buckled at the waist
- a boxy pale-blue police duty uniform with a black waist rig and a division patch at the shoulder, sleeves rolled to the elbow || mil
- a white-and-olive labor pilot's suit with a padded collar, buckled chest harness and a stencilled unit number at the thigh || mil
- grease-blackened overalls stripped to the waist and knotted there over a sweat-damp undershirt, a heavy tool belt slung at the hips || civ
- a bulky riot-control suit of segmented off-white armor over a dark uniform, a numbered plate across the chest || mil
- a heavy olive winter greatcoat over a service uniform, the fur collar turned up and gloves stuffed in one pocket || mil
- a high-visibility site vest over a plaid work shirt and heavy canvas trousers, a loose chinstrap swinging at the throat || civ
- a rumpled brown suit under an open plastic raincoat, both hems dripping || civ

## Outfit (she) +

<!--
  Feminine cuts, added to the neutral options above rather than replacing them -
  a woman in grey coveralls is entirely normal and should stay possible.

  The armored-bodyglove entries deliberately name no glow color: the palette
  sentence in the template already makes the rolled Glow colour the only
  saturated color, so "glowing seam lines" picks it up instead of fighting it.
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
- an elaborate floral kimono layered over a plain white underrobe, sleeves trailing long past the fingertips || civ notac dressy
- white shrine robes with a red hakama skirt, a cord-tied over-sash crossing the chest || civ notac dressy
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
- a lacquered single pauldron over a fitted dark robe with an embroidered high collar, tasseled cords hanging from the shoulder, a wide sash cinched at the waist || civ notac dressy
- a fitted halter-neck tank top with a high choker collar, one bare shoulder crossed by a thin strap || civ
- a cropped bomber-style jacket zipped only at the chest over a fitted sports top and briefs, midriff and legs bare, wrists wrapped in tape || civ
- a fitted red-and-white segmented plate armor suit cut low across the chest, articulated joints at the shoulders and knees
- a sleek black tactical bodysuit with segmented dark red armor plating across one shoulder and arm, fingerless gloves and knee-high boots || civ
- a tattered black cloak like torn wings draped from the shoulders over a wrapped cropped top, buckled utility straps cinched at the waist and one armored bracer laced to the forearm || civ
- a fitted dark leather bodice cut low at the chest over a long dark wrap skirt, faint red markings tracing down one bared arm || civ
- a partial lacquered pauldron and vambrace worn over a cropped underlayer baring the midriff, small red tassels trailing from the shoulder plate || civ notac dressy
- a white-and-black lacquered armor harness baring the midriff, fitted white trousers tucked into patterned boots || civ notac dressy
- a sleeveless dark lamellar armor bodice with a red cord sash, plate segments hanging low over dark leggings, {possessive} shoulders left bare || civ notac dressy
- a dark kimono patterned with pale plum blossoms, a crimson underlayer glimpsed at the collar and wide sleeves || civ notac dressy
- an ornate white and blue segmented armor jacket laced tight over a corseted front, finished with gauntlet-cuffed gloves || dressy
- a gold-braided long coat worn open over a laced corset top, cinched with a wide buckled sash and paired with striped thigh-high stockings || dressy
- a fitted leather corset baring the midriff under a long gold-buttoned coat trailing to the knee || civ dressy
- a skin-tight charcoal bodysuit with a cropped halter back and thigh-high boots, wrist straps cinched over fingerless gloves
- an off-shoulder pale gown with a black strap harness crossing the bodice || dressy
- a form-fitting flight suit plated at the collar and bust, seams sealed against a mounted harness || @gundam
- a backless halter gown with straps crisscrossed bare down the spine to the waist || dressy
- a skintight tactical bodysuit plated at one shoulder, every panel line glowing hairline-thin || @cyberpunk
- a tailored pinstripe blazer cinched over a short pencil skirt, collar snapped high at the throat || civ @corporate
- a skintight bio-mechanical bodysuit fused with plating at the shoulders and spine, seams glowing hairline-thin || @cyberpunk
- a hip-length tan leather jacket over a high-cut dark combat leotard and thigh-high stockings, a drop-leg holster strapped down one bare thigh || civ
- a pale-blue police uniform blouse with the sleeves rolled, tucked into a straight duty skirt above a black belt rig || mil

## Weapon

<!--
  What the NPC is armed with, rolled separately from Gear so a mechanic can
  carry a tool bag AND a holstered sidearm - one combined roll could only ever
  yield one of the two.

  A weapon is the most theme-defining object a figure carries, which is why
  this table is theme-gated and Gear is not: one undifferentiated pool is why
  every theme's armament used to land on everyone.

  The 'x30 || none' entry is an empty bullet: split_flags() parses it to text
  '' with flags ('none',), so it contributes nothing to the prompt. It keeps
  an unarmed NPC the common case, and it keeps the average prompt short, since
  most NPCs then render no weapon phrase at all. Its weight is the dial for
  how armed the setting feels - raise it for a quieter one. A 'mil' Role never
  reaches it: apply_weapon_policy() restricts that pool to 'sidearm'-flagged
  bullets, which this is not.

  'none' is also read directly, by the Stance filter in roll_npc(): once the
  Weapon roll lands on this bullet, a pose that names a weapon - flagged
  'armed' or 'gun' - is no longer reachable, so an unarmed NPC is never posed
  brandishing something the prompt never named.

  That weight is the baseline. On top of it, apply_weapon_policy() gives every
  non-military Role a 'civilian' tier that stacks further copies of this entry
  into the pool - CIVILIAN_UNARMED_COPIES in generate-npc.py - because without
  it an ordinary dockworker came out armed two rolls in three. Weapon sits
  outside the civ/mil filter on purpose, so nothing else was holding a
  civilian back from the military bullets here.

  Flags here: 'weapon' (an actual weapon), 'simple' (small and pocketable),
  'sidearm' (includes a holstered or openly worn pistol - the guaranteed-armed
  baseline for a mil Role), 'gun' (an actual firearm held in hand), 'hands'
  (occupies at least one hand), 'mil' (military-issue), 'none' (the empty
  bullet below - load-bearing, not inert: the Stance filter in roll_npc()
  reads it directly to keep an unarmed NPC off an armed pose).
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
- a silver revolver raised and cocked, hammer drawn back || hands gun weapon simple
- a slender rapier raised en garde, tip angled skyward || hands weapon
- a long slim blade held loose at {possessive} side, its sheathed twin crossed low across {possessive} hip || hands weapon @neosamurai
- a slender rapier drawn point-first, its grip wrapped in worn leather || hands weapon
- an antique-pattern pistol raised and cocked in one hand || hands gun weapon simple
- an ornate curved saber, jeweled pommel bright against a worn leather scabbard at the hip || weapon
- a curved blade raised overhead, wreathed in a faint inner glow || hands weapon @grimdark
- a suppressed carbine gripped low and ready in both hands, a weapon light and optic mounted along the top rail || hands gun mil weapon
- a holstered pistol strapped high on {possessive} thigh || weapon simple sidearm
- a bulky futuristic bullpup rifle gripped two-handed, vents glowing along the stock || hands gun mil weapon @cyberpunk
- a long-barreled sniper rifle steadied on a mounted scope, {possessive} finger resting along the guard || hands gun mil weapon
- a massive single-barreled railgun leveled one-handed, vents glowing along its length || hands gun weapon @cyberpunk
- a second pistol worn holstered at the small of {possessive} back, grip peeking above the belt line || weapon sidearm
- a compact pistol held loose at {possessive} side, muzzle dipped toward the floor || hands gun weapon simple
- a heavy angular rifle, its rear coil glowing, gripped low at {possessive} hip with the muzzle dipped toward the deck || hands gun weapon @cyberpunk
- a slim, wire-wrapped katana with a faint glowing edge along the blade || hands weapon @cyberpunk
- a boxy bullpup carbine with a top-feeding curved magazine, held level in both hands || hands gun mil weapon
- a long-barrelled heavy revolver holstered under one arm in a worn leather rig || weapon simple sidearm
- a compact machine pistol with its wire stock folded, clipped to a chest sling || mil weapon simple sidearm
- a slim vented pistol held low in a gloved hand, its muzzle angled at the ground || hands gun weapon simple
- a service revolver holstered at the belt beneath an open jacket || weapon simple sidearm
- a long riot baton gripped in one hand and a scuffed transparent shield braced on the other arm || hands weapon
- an anti-materiel rifle with its bipod folded, slung muzzle-up across {possessive} back || mil weapon
- a stubby grenade launcher slung across the chest above a bandolier of fat cased rounds || mil weapon
- a flare pistol tucked into a chest pouch, its casing scuffed orange || weapon simple

## Gear

<!--
  '|| mil' marks a piece of military-issue equipment - see the note on it
  near the top of this file.

  Gear is equipment only now: tools, cases, packs, the odds and ends a figure
  has in hand or slung over a shoulder. Armament - anything that reads as a
  weapon - lives in '## Weapon', rolled separately; see that table's comment
  for its flags.

  It is also the everyday half of what a person carries, and deliberately so.
  Most NPCs this file rolls are not soldiers, and a setting whose civilians
  all carry diagnostic leads and tactical packs reads as a barracks rather
  than a colony. A thermos, a market basket, a folded umbrella, a paper
  parcel of something hot - those are what the great majority of people in
  any inhabited place have in their hands, and they cost nothing to render.
  Keep authoring them: the ratio of ordinary objects to issued equipment here
  is most of what makes a rolled crowd feel lived-in.

  '|| admin' is a ROLE LOCK, and the only one so far. A locked bullet is
  reachable by the occupations named against that flag in ROLE_LOCKS in
  generate-npc.py and by no others - 'admin' is a colonial administrator's
  and nobody else's. It is the one hard filter on this table: unlike 'notac',
  'hands' or 'helmet', which hand the whole pool back rather than roll
  nothing, a lock never yields, because yielding would give the item to
  precisely the Role it was locked away from.

  Use it sparingly and only where the object is an emblem of the job rather
  than a tool of it. A cane of office, a seal, a warrant - things that say
  something about the person holding them. A multitool says nothing: anyone
  may own one, and locking tools by trade would just make the table thinner
  without making it truer. Adding a lock means adding its flag to ROLE_LOCKS
  with the exact Role bullet text; test/test_role_lock.py fails on a flag
  that is missing there, and on a Role name there that the Role table has
  since reworded.
-->

- a battered data-slate tucked under one arm || hands
- a heavy multitool holstered at the hip
- a coil of cabling and diagnostic leads slung across the body
- a scarred pilot helmet carried in the crook of one elbow || hands helmet
- a compact rebreather clipped at the collar
- a shoulder-slung tool bag, its strap worn through and re-stitched
- a slim wrist-mounted holographic interface projecting faint readouts
- a cigarette burned nearly to the filter, held forgotten || hands
- nothing at all, hands loose and empty
- a bundle of rolled schematics under one arm || hands
<!-- - a heavy pry bar hooked through a belt loop -->
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
- a lacquered walking stick gripped in one hand, weight braced into it || hands admin
- a fist-sized holographic sphere hovering just above one open palm, its surface a shifting lattice of glowing fracture-lines and readouts
- a translucent holographic data-sheet held up in both hands, dense scrolling text glowing across its surface || hands
- a cracked-open slate bristling with jack cables and cracking tools, plainly meant for breaking into things it shouldn't || hands
- a pair of articulated mechanical wing extensions mounted at the shoulders, each feather-like segment tipped with a small lit sensor lens
- a small pendant amulet glowing softly at the throat
- an old-fashioned lantern glowing warm, carried by its handle in one hand || hands
- a boxy red trauma pack worn high on both shoulder straps, its star-of-life patch and reflective strip catching the light
- a slim, battered laptop balanced open on a fold-down tray || hands
- a mechanical multi-dial comm unit clipped to a shoulder harness strap || mil
- a crossed tactical harness worn bare over the shoulders, cables trailing down to the belt || mil
- a scuffed leather briefcase gripped by the handle, corners worn pale with use || hands
- a battered acoustic guitar cradled against {possessive} chest, {possessive} fretting hand pressed to the neck || hands
- a heavy iron wrench gripped in one grease-streaked glove || hands
- a string bag of groceries hanging from one hand, a loaf and a bundle of greens showing through the mesh || hands
- a chipped enamel mug cradled in both hands, steam curling off it || hands
- a paper-wrapped parcel of hot food held close against the chest || hands
- a cheap folding umbrella hooked over one forearm, still beaded with rain || hands
- a battered canvas satchel worn crossbody, its flap held down by one surviving buckle
- a woven market basket carried in the crook of one arm, a cloth laid over it against the dust || hands
- a bundle of laundry rolled under one arm, a wooden peg still clipped to a corner || hands
- a small toy mech held forgotten in one hand, its paint worn down to bare metal || hands
- a paperback gone soft at the spine, held open on one thumb || hands
- a ring of worn keys and stamped door-tags hooked through a belt loop
- a plastic crate of empty bottles balanced against one shoulder || hands
- a bundle of cut flowers wrapped in newsprint, carried head-down at one side || hands
- a scuffed instrument case slung from one shoulder, its clasps mismatched
- a folded broadsheet tucked under one arm, its edges gone damp || hands
- a transit pass on a frayed lanyard at the neck, the print worn off it
- a dented lunch tin knotted into a cloth wrap and carried by the knot || hands
- a stray cat riding one shoulder, tail hooked round the back of {possessive} neck for balance
- a hand-lettered price board carried face-down at one side || hands
- a long torque wrench rested across one shoulder, its handle wrapped in worn tape || hands
- a welding mask carried by its strap in one hand, the lens burned nearly opaque || hands
- a spool of solder and a cooling iron clipped at the breast pocket
- a set of calipers hooked in a breast pocket beside a row of markers
- a steel tape and a flat carpenter's pencil stuffed in a hip pocket
- a tin of grease and a fistful of oil-black rags gathered in one hand || hands
- a stiff-bristled deck broom held upright in one hand || hands
- a coil of nylon line and a pair of shackles hung at the belt
- a pressure gauge on a looped length of hose slung over one shoulder
- a cordless driver holstered at the thigh, a strip of bits taped along its body
- a clipboard of work orders held against one hip, the top sheet curling with damp || hands
- a length of neural interface cabling running from the nape of {possessive} neck to a jack held in one hand || hands
- a slim diagnostic wand on a ribbon cable, held up against the base of {possessive} own skull || hands
- an operator's control gauntlet worn to the elbow, thick cabling looping from the wrist back to a pack at the shoulder
- a scuffed white site helmet carried under one arm, a stencilled unit number across the crown || hands helmet
- a radio handset held up at the shoulder, its curled cord running down to a set at the belt || hands
- a foam-lined optics case carried level in both hands, its latches sprung open || hands
- a thick bound incident file wedged under one arm, tagged along the edge with coloured slips || hands
- a heat-warped hydraulic line coiled over one shoulder, still weeping fluid
- a marshalling paddle held down at each side, reflective tape banding both cuffs || hands
- a tagged evidence bag held up at eye level, something small and dark shifting inside it || hands
- a beaten aluminium riot helmet with a scratched face bar, carried in one hand || hands helmet
- a case file rolled into a tube and tapped absently against one leg || hands
- a bricklayer's trowel and a coiled line level hooked at the belt
- a test meter dangling from one hand by its probe leads || hands
- a length of threaded pipe balanced across one shoulder, a wrench hooked over the end || hands
- a paint roller on a long pole rested back over one shoulder, its sleeve stiff with dried colour || hands
- a sheet of glass held edge-on in gloved hands, tape crossed over it in a wide X || hands
- a pincushion strapped to one wrist and a tape measure hung round the neck
- a bolt of patterned cloth balanced on one shoulder and steadied with one hand || hands
- a tray of seedlings held level in both hands, the soil in them still dark with water || hands
- a soil probe and a folded moisture reader stuffed in a hip pocket
- a pair of long-handled pruning shears hooked over one shoulder || hands
- a wringer bucket swinging from one hand, grey water slopping over the lip || hands
- a battered inventory scanner holstered at the hip, its screen cracked across a corner
- a blunt cargo hook slung through the belt at the small of {possessive} back
- a spool of printer feedstock tucked under one arm, its seal broken and half unwound || hands
- a freshly printed part cradled in both hands, its support scaffolding not yet snapped off || hands
- a cook's knife roll of worn canvas under one arm, its ties hanging loose || hands
- a sack of flour hoisted onto one shoulder, a white handprint left below it || hands
- a foam cool-box slung from its shoulder strap, condensation beading the lid
- a hand balance and a pouch of brass weights hooked at the belt
- a tray of skewers slung from a neck strap, a folded fan in one hand for the coals || hands
- a small child riding on one hip, both arms wound round {possessive} neck || hands
- a scruffy dog leaning against one leg, its lead looped twice round {possessive} wrist || hands
- a hen tucked under one arm, entirely unbothered || hands
- a potted plant hugged against the chest in both arms, leaves brushing {possessive} chin || hands
- a strap-bound stack of schoolbooks wedged against one hip || hands
- a scuffed handheld comm held low at one side, its screen lit on a half-typed message || hands
- a foil ration brick half-unwrapped and eaten one-handed || hands
- a dented water can swinging from one hand, the ration stencil half scrubbed off it || hands
- an old film camera hanging at the chest on a worn neck strap
- a plain wooden cane hooked over one forearm, its tip worn to a bevel || hands
- a rigid courier box strapped high on the back, a delivery tag fluttering from its handle
- a bundle of incense sticks and a folded paper charm held in one hand || hands
- a paper cone of roasted nuts held in one hand, the top of it still steaming || hands
- a folded camp stool tucked under one arm by its crossed legs || hands

## Glow colour

<!--
  The single saturated colour of the one light source in an otherwise
  restrained frame - not a design accent, which is what the old name implied.
  Only reached when something rolled for this NPC could actually cast it; see
  has_light_source() in generate-npc.py.

  Entries name a HUE, never a light-emitting phenomenon. Both templates wrap
  the value as "{glow} glow", so "electric blue" came out as arcing
  electricity and "neon cyan" pulled neon tubing into frame. Say the shade -
  "vivid cobalt blue" - and let the template supply the glow.
-->

- teal-green
- x2 amber
- dull copper-orange
- cold blue-white
- sickly yellow-green
- deep violet
- brass-gold
- crimson-red
- vivid cobalt blue
- magenta-pink
- bright cyan

## Glow placement

<!--
  WHERE the rolled Glow colour falls in the portrait. The colour and its
  placement are separate rolls for the same reason Hair colour split away from
  Hair: a new placement is one bullet here rather than a rewrite of every
  shade.

  Portrait only. The token renders on flat white with no scene at all, so it
  keeps the single unplaced "a single {glow} glow" wording it always had.

  Each bullet is the PREDICATE of "A faint {glow} glow ___." - it starts with a
  verb and carries its own contrast clause where it wants one. Do not name the
  colour; the template has already said it, and saying it twice is how the
  frame ends up with two glows.

  '|| scene' marks a placement that puts the light out in the environment -
  on a wall, in the air, across the ground. Those are only reachable when the
  BACKDROP is what casts the light, since the alternative source is something
  the NPC wears or carries (a lit visor, glowing cabling, an instrument panel)
  and that cannot light a wall behind them. An unflagged bullet keeps the light
  on or immediately around the figure and is reachable either way - most
  should stay that way, since the equipped case is the common one. See
  has_light_source() in generate-npc.py.
-->

- x2 falls across one side of {possessive} face against warm dim ambient light on the other
- rakes across {possessive} chest and shoulder, the face left in warmer shadow
- catches {possessive} jaw and one shoulder from below
- rims {possessive} shoulders and hair from behind, the face lit only by what spills around it
- falls across {possessive} back and one shoulder, the front of the figure in warm shadow
  <!-- - catches {possessive} profile and one hand at a sharp angle, the rest of the figure left in shadow -->
  <!-- - washes across the scene behind {object}, throwing {possessive} outline into near-silhouette || scene -->
- pools on the ground around {object} and throws colour up onto {possessive} hands || scene
- stripes the wall behind {object} and catches one side of {possessive} face || scene
- hangs in the air as a haze across the whole depth of the shot || scene
- washes across {possessive} cheek and shoulder harness at a low angle
- washes the towering display wall stacked behind {object} || scene
- traces the seams of {possessive} suit in a hairline of light down each limb
- spills across the skyline in overlapping signage behind {object} || scene

## Backdrop

<!--
  Portrait only - the token is always flat white for background removal.

  Each bullet carries BOTH halves of the shot, split on '||': the opening phrase
  on the left, the scene sentence on the right. They have to agree, so they are
  rolled together. A dive toward the camera cannot be staged inside "a half-body
  character portrait", and a zero-gravity pose over a rain-streaked street would
  be nonsense whichever opening it got.

  A third '||' segment carries flags. The behavioural one is 'nogear', for
  scenes that already put something in the subject's hands - without it the
  gunfight and blade-draw scenes stacked a rolled rifle on top of the weapons
  they hand out, and the NPC came out carrying three. It drops the whole
  merged Weapon+Gear "carries ..." sentence from the portrait only (the token
  keeps it - it has no scene to contradict), and separately keeps the Gear
  roll itself off any '|| hands' bullet, so a scene never ends up paired with
  a Gear item it would visibly be fighting over the subject's hands.
  'weather' marks the scene outdoors, so a Weather roll can land in it.

  The rest of the flag vocabulary is OCCUPATION GATES - 'cockpit', 'ownmech',
  'mechwork', 'mechyard', 'warzone', 'frontline', 'vacuum', 'swordwork',
  'deskwork', 'ceremony', 'inspection', 'salvage', 'clergy', 'medic',
  'barkeep' - each defined in BACKDROP_ROLES in generate-npc.py against the
  Role categories (or the exact Role bullets) allowed to roll it. A flagged
  scene is unreachable from every other Role, with no fallback: this is a hard
  filter, the same shape as Gear's 'admin' lock and unlike every preference
  filter in this file, because handing the pool back would give the scene to
  precisely the Role it was kept from.

  The test for whether a scene needs one is LOCATION versus ACTIVITY. A
  blurred background is a place, and a place fits anyone - standing in front
  of a mech hangar is fine for a bar owner, and gets no flag. A scene that
  puts the subject mid-action is a claim about the person: flying the machine,
  welding its plating, annotating a clipboard on an inspection gantry, running
  a triage tent. Some 180 of these bullets are ungated and should stay that
  way. Reach for a gate only where the sentence would be FALSE about a wrong
  Role, not merely unusual - over-gating this table is how you end up with
  three occupations that can only ever roll six scenes between them.

  Adding a gate flag to a bullet without adding it to BACKDROP_ROLES does
  nothing at all: an unrecognized flag is ignored rather than reported, so the
  scene ships silently ungated. test_backdrop_role.py is what catches that.

  Writing zero-gravity entries: describe the BODY first - foreshortening, the
  arched back, the reaching arm, the trailing legs - and the room second.
  Entries that led with the environment rendered the subject standing on a deck
  no matter how many "weightless" qualifiers were bolted on.

  Nineteen of these are zero-gravity, against 303 weighted entries in all, so
  about one portrait in sixteen comes up weightless. That figure is far below
  the "about a quarter" this note used to claim: the count was written when the
  table was a fraction of its present size and the standing entries carried an
  x3 weight, and the table outgrew it rather than the weighting changing. Add a
  weight to the zero-gravity bullets, not to the standing ones, if you want the
  mix back - there are 250 of the latter now and re-weighting them all is a
  much larger edit than it was.

  The exterior/vacuum entries dress the subject in a sealed EVA pressure suit
  and helmet over whatever Outfit was rolled, so a corporate blouse in hard
  vacuum stays coherent - a harness or open faceplate isn't enough on its own
  out there, so those entries commit to the full suit rather than implying
  one.
-->

- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is the dim interior of a mech hangar, gantries and chain hoists receding into shadow. || mechyard
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
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} gliding along the exterior hull of a ship in a low zero-gravity recline, {possessive} back arched and body tilted no more than about 30 to 40 degrees off vertical across the frame, one gloved hand reaching up and back to grip an angular strut above {possessive} head while the other extends down to brace against a rail beneath {object}, legs drawn up and bent, head tilted back inside a sealed EVA helmet, visor down, gazing up and to the side, a full pressure suit worn close over {possessive} kit - behind {object} the dark hull curves away into the void, faint teal atmospheric light bleeding in from one side and streaks of motion-blurred light trailing past in the starfield. Dramatic rim lighting along {possessive} silhouette. || vacuum
- A dynamic, gently canted-angle character portrait || {Subject} {is_are} drifting weightless just outside an open airlock in a sealed EVA pressure suit and helmet, visor down, worn over {possessive} kit, body turned in a shallow roll no more than about 30 to 40 degrees off vertical with one gloved hand still on the hatch coaming and {possessive} legs floating free, tether line coiling loose behind {object} - beyond {object} the ship's plating falls away into the void and the lit limb of a planet curves across the background. Dramatic rim lighting along {possessive} silhouette. || vacuum
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} braced weightless between two struts of an orbital gantry, {possessive} body tilted no more than about 30 to 40 degrees off vertical and slowly rotating, one gloved hand overhead on a spar and one boot hooked under a rail, a sealed EVA pressure suit and helmet, visor down, worn over {possessive} kit - behind {object} the scaffold recedes into the dark and the starfield streaks past in faint motion-blurred lines. Dramatic rim lighting along {possessive} silhouette. || vacuum
- A close, low-angle character portrait || {Subject} {is_are} floating weightless inside a pressurised observation blister, one palm flat against the curved glass above {possessive} head and {possessive} body turned a mild 20 to 30 degrees off vertical, legs drawn up and bent, hair lifted free - beyond the glass the ship's hull curves away and the starfield turns slowly past. Rim lighting along {possessive} silhouette.
- A dynamic character portrait || {Subject} {is_are} caught in a three-quarter turn, raising a compact sidearm and firing directly toward the viewer, muzzle flash bursting from the barrel and a spent shell casing ejecting mid-air - behind {object} a dim industrial interior of dark metal panelling, faintly lit and kept soft and out of focus so {subject} {is_are} clearly the subject. Even key lighting on {possessive} face and weapon, with a dramatic but restrained rim light thrown by the muzzle flash. || nogear frontline
- A dynamic, three-quarter rear-view character portrait || {Subject} {is_are} seen from behind on a rooftop ledge, glancing back over one shoulder and drawing a single-edged blade that glows faintly along its cutting edge, a second blade sheathed crosswise against {possessive} back - behind {object} a dim industrial cityscape stretches away, muted grey-olive towers dotted with sparse lit windows beneath a hazy dusk sky, and the hulking silhouette of something vast and serpentine looms low on the horizon as a dark rust-toned shape. Twin warning beacons glow dull amber at the edges of the frame. || nogear weather frontline
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} weightless in freefall down a dim ship corridor, {possessive} body angled hard toward the viewer in strong foreshortening, one arm extended down and out gripping a raised sidearm with the muzzle tracking past the frame, the other hand bent back near {possessive} own head bracing against an unseen handhold, legs trailing loose behind {object}, faint motion blur streaking the corridor's lit panels and hazard striping as they rush past. Dramatic foreshortened composition. || nogear frontline
- A character portrait || {Subject} {is_are} glancing back over one shoulder with a faint, private smile, one hand raised near {possessive} own face in a loose two-fingered gesture, hair drifting weightless with the motion - behind {object}, softly out of focus, a starfield and the curved limb of a planet glow low against the dark.
- A dynamic, close character portrait || {Subject} {is_are} standing square to the viewer with {possessive} arm fully extended, a pistol gripped level and aimed straight at the camera, {possessive} off hand braced beneath for support, {possessive} expression flat and controlled - behind {object}, blurred well out of focus, a plain dim interior with hard directional light. Dramatic side lighting rakes across {possessive} face and the weapon. || nogear frontline
- A dynamic, low-angle character portrait || {Subject} {is_are} standing beside a parked matte-black superbike, both hands locked around an oversized cannon raised and leveled dead at the viewer, a sheathed blade slung crosswise across {possessive} back - behind {object} a rain-slick night street glows faintly blue through fogged storefront glass, the bike's windscreen starred with a bullet crack close beside {object}. || nogear weather frontline
- A dynamic character portrait || {Subject} {is_are} braced with a double-barreled shotgun raised and shouldered, sighting hard toward the viewer, hair whipped loose by the wind - behind {object}, out of focus, an open sunlit horizon under a pale hazy sky. Hard directional light rakes across {possessive} face and the weapon. || nogear weather frontline
- A dynamic, low-angle character portrait || {Subject} {is_are} braced low on one knee, a long suppressed sniper rifle shouldered and firing toward the viewer, a spent casing arcing free from the action and {possessive} hair caught mid-motion by the recoil - behind {object}, out of focus, a dusty open flatland fading into haze. Dramatic side lighting rakes across {possessive} face and the weapon. || nogear weather frontline
- A dynamic, low-angle character portrait || {Subject} {is_are} braced low on one knee behind a belt-fed light machine gun, sighting down it toward the viewer with the ammo belt trailing to a drum magazine, gear-laden webbing crossing {possessive} chest - beside {object}, out of focus, the watchful shape of a large working dog crouches low in the frame, and behind them both a pale washed-out sky stretches away. || nogear weather frontline
- A dynamic, low-angle character portrait || {Subject} {is_are} advancing down a cramped service corridor, a rifle raised and sighted toward the viewer, red emergency strip-lighting striping the walls and ceiling around {object} and dark stains marking the deck underfoot - ahead down the passage, two more silhouetted figures stand caught in a bright wash of light and drifting haze. Hard red-tinted side lighting rakes across {possessive} face and the weapon. || nogear frontline
- x3 A half-body character portrait || Behind {object}, out of focus, is a muted frontier backdrop of dusty rockcrete structures and faint industrial haze, a dim atmospheric glow low on the horizon. Dramatic side lighting casts hard shadow across half {possessive} face. || weather
- A three-quarter character portrait || {Subject} {is_are} leaning intently over a cluttered workbench, hunched forward and studying something closely, both hands down on a mechanical keyboard - to one side a large monitor glows with dense terminal code, casting light across {possessive} face, and behind {object} a cluttered workshop of stacked machinery, tangled cabling and scattered papers recedes into soft focus under dim overhead light. Warm light on {possessive} face against the cooler background. || nogear
- A character portrait || {Subject} {is_are} leaning back against the flank of a long, low speeder bike parked at a fuel stop, ankles crossed and weight settled easy against the fuselage, a cigarette held forgotten near {possessive} mouth, gazing out at the fading light - behind {object} a hazy golden dusk skyline of distant spires rises beyond a scatter of old fuel pumps and hand-lettered signage crowding the foreground out of focus. || nogear weather
- A character portrait || {Subject} {is_are} sitting in profile, leaning back against the bent knee of a massive crouched military mech - the machine is boxy and heavily industrial, thick armored plating stencilled with unit markings, a single lit optic sensor and antenna protrusions rising from its head, its bulk looming just behind {possessive} shoulder. Behind them a rundown industrial refinery at dusk: tangled scaffolding, pipes and a tall numbered tower silhouetted against a low sun. Warm light rakes across {possessive} face and the mech's armor. || weather mechyard
- A dramatic low-angle character portrait || {Subject} {is_are} leaning back against the massive bent knee of a towering mech, looking down at the viewer, the shot angled steeply upward to emphasise the scale of both - the mech's leg fills the foreground in fine panel-line and rivet detail, a weapon barrel running off the top of the frame, a crescent moon faint through cloud above and a distant skyline low on the horizon. || weather mechyard
- A character portrait || {Subject} {is_are} sitting in the round hatch of an open viewport, one leg drawn up and hooked over the rim and the other hanging free outside it, {possessive} weight braced back against the frame in unhurried repose, gazing out past the opening. Tucked into the corner of frame below {object}, the domed head and lit photoreceptor of a small utility droid peeks into view. Beyond the hatch a pair of pale suns hang low over a sun-bleached horizon. || weather
- A character portrait seen from behind || {Subject} {is_are} leaning on a rooftop balcony railing high above a dense city street, glancing back over one shoulder at the viewer - below {object} the street is packed with stacked signage glowing through humid haze, the crowds and wet pavement dissolving into loose, almost impressionistic brushwork. A rooftop awning and railing frame the high vantage point. || weather
- A character portrait || {Subject} {is_are} standing in a bombed-out doorway between two weathered concrete walls, framed by scattered bullet holes, faded warning signs and pinned notices - behind {object} a ruined cityscape stretches away into smoke and dust, a massive mech silhouette looming among the broken buildings and a huge low sun bathing the scene. In the foreground the blurred silhouettes of two seated figures frame the bottom corners, well out of focus. || weather
- A close-up character portrait || {Subject} {is_are} framed tight against a dense city street at night, tangled overhead wires crossing a hazy sky behind {object} and stacked signage glowing softly out of focus, the light grading cool across {possessive} face. || weather
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a frontier rail platform in ochre haze, an incoming transit's headlamps glaring through the dust and tangled overhead wire. || weather
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cramped fire-escape landing tangled with cabling and pipework, neon shop signage bleeding pink and green through the grating and mist. || weather
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a crowded transit terminal beneath tangled cable runs, neon signage in unfamiliar characters glowing above loitering figures and drifting smoke.
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a snowbound crash site, a downed transport burning against a wall of white peaks. || weather
- x3 A half-body character portrait || Behind {object}, out of focus, an immense flying superstructure eclipses the low sun over a sprawl of sun-baked rooftops, its long shadow stretching through the haze. || weather
- A character portrait || {Subject} {is_are} standing on a windswept ridge, a weapon lowered and faintly smoking at {possessive} side, looking out over a mist-filled valley - behind {object} a vast ring of wreckage hangs frozen in the air above a plunging waterfall, a pair of transports drifting past far below. || nogear weather frontline
- A character portrait || {Subject} {is_are} sitting cross-legged on a rooftop ledge, eyes closed in quiet stillness, a sheathed blade laid flat across {possessive} lap - behind {object} a dense night skyline glows through drifting haze, thin trails of aircraft light threading between the towers. || nogear weather
- A dynamic character portrait || {Subject} {is_are} walking straight toward the viewer down a rain-slicked neon-lit street at night, flanked on either side by a pair of hulking bipedal war-mechs looming half into frame, their optics burning dull red in the murk, signage bleeding into smeared reflections on the wet pavement behind them all. || weather
- A dynamic, low-angle character portrait || {Subject} {is_are} crouched low in a wide balanced stance atop a hovering skateboard ridden like a surfboard, knees bent and weight low, one arm flung out wide for balance and the other pointing off past the frame, a twin-thruster pack strapped across {possessive} back glowing faintly at the vents, hair and jacket sleeves whipped back by the wind - behind {object} a dense neon-lit cyberpunk skyline rises through drifting haze, towering signage in tangled scripts and corporate logos glowing through the mist, other riders on hoverbikes cutting past in the middle distance. || nogear weather
- A dramatic low-angle character portrait || {Subject} {is_are} crouched low behind an abandoned vehicle on a rain-slicked city street at night, weapon raised and sighting up at a colossal insectoid war-machine that fills the skyline ahead, its hull studded with glowing sensor clusters and thin segmented limbs trailing into the smoke-hazed street below, twin beams lancing down from its underside through the drifting mist - behind {object} a burning wreck casts long orange light across the wet pavement. || nogear weather frontline
- A character portrait || {Subject} {is_are} standing just inside the shattered nave of a ruined cathedral, dust hanging thick in broad shafts of light falling through the broken vaulting overhead, gazing up at an ancient gold-plated war-machine crouched motionless among the rubble ahead - a pair of cloaked, hooded companions stand just ahead of {object}, silhouetted small against its bulk. || weather
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} caught mid-kick in heavy powered armor, driving a braced boot into the armored hull of a massive segmented war-machine at close quarters, {possessive} sidearm still gripped and firing point-blank in the other hand, sparks and debris bursting from the impact - behind {object} a shattered cityscape unfurls in smoke and falling rubble, distant explosions blooming against a pale hazy sky. || nogear weather frontline
- A character portrait || {Subject} {is_are} standing amid drifting embers and rubble, watching a hulking quadrupedal war-mech stride past close behind {object}, an oversized cannon swinging loose from one of its forelimbs, a small armed flyer banking low overhead - beyond them a bombed-out industrial skyline fades into a bruised violet dusk, fire guttering low among the wreckage. || weather
- x2 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a windswept plain of tall pale grass, a small stilted wayside shrine strung with paper streamers and a spear driven upright nearby trailing a strip of red cloth, a faint rainbow arcing through the haze beyond. || weather
- x2 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-slick shrine courtyard at dusk, stone steps climbing to wooden eaves hung with a glowing paper lantern, pale fox-shaped shapes moving low through the mist. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is the fog-wrapped wreck of a fallen war-mech looming over a rain-soaked shrine courtyard, its broken frame threaded with strung paper talismans. || weather
- x2 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a sunlit ruin of towering stone archways and a broken aqueduct climbing a green mountainside, ivy and wind-bent trees reclaiming the old stonework. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a colossal robotic figure half-risen from a canal, only its ornate head, shoulders and clawed hands breaking the water, gold filigree tracing its dark plating; beyond it domed shrines and slender gold-latticed spires ring a plaza where two hooded robed figures pause at the water's edge beneath a hazy dusk sky, a dull red sun hanging low beside a darker second disc. || weather
- A three-quarter rear-view character portrait || {Subject} {is_are} standing in a mech's calibration bay, gazing up at a towering white-armored war-machine looming just ahead, one hand raised holding a slim holographic data-slate glowing with dense diagnostic readouts, {possessive} other hand braced at {possessive} hip - thick power cabling and chain hoists hang down around the mech's bulk, a wall-mounted display beside {object} scrolling systems-check telemetry, cool blue interior lighting washing the bay. || nogear mechwork
- A character portrait || {Subject} {is_are} standing atop the hull of a companion vessel in high orbit, sealed inside an EVA pressure suit and helmet, a cropped mission patch at the shoulder catching the thin light through the visor, looking back over one shoulder - beyond {object} a planet's night side curves away below, its cities burning in scattered threads of light against the dark. || vacuum
- A dramatic low-angle character portrait || {Subject} {is_are} standing amid drifting embers on a scorched battlefield in heavy rain, {possessive} back to the viewer, a long rifle gripped and lowered at {possessive} side - ahead of {object} churned mud and shattered rock fade into grey mist streaked with falling ash. || nogear weather frontline
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a floor-to-ceiling window wall overlooking a dense neon high-rise skyline at night, faint status readouts glowing at the edge of the frame.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a graffiti-tagged alley lit by tube neon signage bleeding red and teal through drifting mist.
- A character portrait || {Subject} {is_are} standing beside a parked muscle car on a dark cyberpunk street at night, one hand braced on the doorframe, glancing up at the looming high-rises ahead - behind {object} the car's tail-lights glow red against the wet pavement. || weather
- A character portrait || {Subject} {is_are} standing at a rooftop railing in the rain, glancing back over one shoulder, a pair of aircraft streaking low across the skyline behind {object} - below {object} a dense neon high-rise district stretches away into the haze. || weather
- A close character portrait || {Subject} {is_are} seated inside a parked vehicle's cockpit in heavy rain, one hand braced on the wheel, neon shopfronts smearing color across the fogged, rain-streaked windshield ahead. || weather
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} weightless in freefall, twisting hard to slip between a crossing lattice of taut laser tripwires, {possessive} body bent and one arm flung wide for balance while the other reaches ahead, loose debris and shattered fragments drifting alongside {object} - the beams cut bright green lines through the dark around {object}, faint structural wreckage receding into the black beyond.
- A character portrait || {Subject} {is_are} standing before the hull of a beached derelict starship, reaching up to touch a faint glowing panel set into its plating - behind {object} the ship's saucer-like silhouette looms against a field of stars.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a wall of humming, dust-caked monitors and tangled cable runs, their pale glow the only light in the room.
- A dynamic character portrait || {Subject} {is_are} crouched low and reaching forward through the wreckage of a gutted server room, heavy clawed gauntlets braced against a fallen strut - behind {object} shattered windows let pale light leak through drifting dust and hanging cable. || nogear frontline
- A character portrait || {Subject} {is_are} perched on the raised knee-joint of a crouched companion mech in heavy night rain, one hand braced against its plating - behind {object} a neon-lit high-rise district fades into the downpour. || weather ownmech
- A character portrait || {Subject} {is_are} standing beside a parked muscle car on a pastel-lit street at dusk, one hand resting on the open door - behind {object} a tangle of towering cyberpunk architecture rises hazy into the fading light. || weather
- A character portrait || {Subject} {is_are} sitting cross-legged on a rooftop ledge at night, hands braced behind {object} - beyond {object} a massive ringed planet hangs low over a grid-lit synthwave skyline lined with palm trees.
- A character portrait || {Subject} {is_are} sitting on the hood of a parked muscle car beneath an enormous full moon, hands braced back against the metal - small dark shapes wheel through the night air above the rain-slick street around {object}. || weather
- A character portrait || {Subject} {is_are} seated low in a rain-slicked alley, jacket half-shrugged off one shoulder and cable straps trailing loose across {possessive} lap, gazing up past the camera - behind {object} neon signage in unfamiliar characters glows through the mist, a server rack blinking against the wall. || weather
- A character portrait || {Subject} {is_are} seated in a crowded night transit car, one hand raised holding a drink, oversized headphones clamped over {possessive} ears - behind {object} out-of-focus passengers sway with the motion and neon signage glows through the window beyond.
- A close character portrait || {Subject} {is_are} standing motionless before the lowered head of a colossal war-machine, its single optic burning close overhead, sparks showering down as welding light flares behind {possessive} shoulder - a steel catwalk and dim industrial scaffolding recede into the haze around {object}. || mechwork
- A close character portrait || {Subject} {is_are} reclined still in a diagnostic rig, head tipped back and eyes closed, a crown of cabling radiating out from {possessive} temples to banks of softly blinking readouts on either side of {object}.
- A dramatic low-angle character portrait || {Subject} {is_are} braced against the wind with one hand raised to shield {possessive} face, tribal markings streaking {possessive} cheek - beyond {object} a huge moon hangs low over a besieged orbital structure, beam weapons lancing down through drifting smoke. || weather
- A character portrait || {Subject} {is_are} sitting cross-legged atop the hull of a parked armored vehicle, segmented mechanical prosthetic arms resting in {possessive} lap - behind {object} a dense neon-lit night skyline glows above a heavy cannon barrel angled into frame.
- A character portrait seen from behind || {Subject} {is_are} standing in silhouette against a huge glowing sun rising behind a ring of ruined structural arches, hair and coat trailing in the wind - a shattered cityscape stretches out to either side of {object} beneath the glow. || weather
- A dynamic character portrait || {Subject} {is_are} drifting limp and weightless above the planet's curve, arms trailing loose and a line of cabling reeling out behind {object}, shattered debris and a distant damaged vessel tumbling nearby, {possessive} suit scorched and torn across the chest. || vacuum
- A character portrait || {Subject} {is_are} standing before the looming bulk of a black companion war-machine, its twin shoulder cannons rising to either side and its optics burning faint red overhead - behind {object} a hazy night skyline glows low against the dark. || ownmech
- A close character portrait || {Subject} {is_are} framed tight in a cracked flight helmet, a thin readout glowing at the brow, half {possessive} face lit by a bright detonation tearing through a field of tumbling rock and debris just beyond {possessive} shoulder. || cockpit
- A close character portrait || {Subject} {is_are} reclined loose in a vehicle's seat, one arm slung back over the headrest and a knee drawn up, glancing out through a rain-streaked window - neon signage smears past in the dark beyond {object}. || weather
- A dynamic character portrait || {Subject} {is_are} walking straight toward the viewer down a narrow overgrown alley, a heavy pack slung on {possessive} back - ivy and reclaimed neon signage crowd the walls to either side of {object}, an old arcade cabinet half-buried in creepers behind.
- A close character portrait || {Subject} {is_are} crouched low in a wrecked, fire-lit room, banks of dead monitors stacked behind {object} and a fire smoldering in the wreckage beyond.
- A close character portrait || {Subject} {is_are} tipped back in a mech cockpit seat, {possessive} gaze lifted past the camera - dense banks of glowing readouts and a night skyline crowd the canopy around {object}. || cockpit
- A character portrait || {Subject} {is_are} reclined deep in a low chair, legs crossed and stretched long, a hand of cards held loosely - mechanical prosthetic arm plating catches the light, and a heavy weapon rests propped against the chair beside {object}, screens of dense readouts glowing at {possessive} back.
- A dramatic character portrait seen from behind || {Subject} {is_are} standing still in the rain, gazing up at a towering battle-scarred war-machine looming just ahead, its single core glowing steady in its chest - a dense city skyline rises hazy through the downpour behind {object}. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cramped hacker's den lit green by a wall of humming CRT monitors, rain streaking a window at the far end. || weather
- A character portrait seen from behind || {Subject} {is_are} sitting on a rooftop bar's counter ledge, glancing back over one shoulder - a dense rain-soaked high-rise district glows through the downpour beyond {object}, potted plants crowding the rail. || weather
- A close character portrait || {Subject} {is_are} leaning back into a mech cockpit seat, rain-damp hair swept across {possessive} face, one gloved hand braced on the console - beyond the canopy a night skyline glows through the rain. || weather cockpit
- A character portrait || {Subject} {is_are} sitting perched on a heap of mangled wreckage, one hand raised to {possessive} collar - a sun-bleached desert stretches out behind {object}, distant explosions blooming pale against the sky. || weather
- A character portrait || {Subject} {is_are} gripping an overhead handhold inside a moving vehicle, one arm raised and braced, glancing up and to the side - a night skyline streaks past the window behind {object}.
- A dramatic low-angle character portrait || {Subject} {is_are} crouched on a narrow icy ledge high above the city, a pistol held ready in one hand, glancing back over {possessive} shoulder - a dense high-rise skyline drops away into the night far below {object}. || nogear weather frontline
- A character portrait || {Subject} {is_are} seated in a shuttle's passenger cabin, poring over a thick bound technical manual balanced on one knee, a travel bag propped against the seat, a richly robed diplomatic passenger seated close beside {object} - beyond the windows a scatter of escort ships hangs against the stars.
- A close, low-angle character portrait || {Subject} {is_are} reclined deep in a mech cockpit's padded seat, sealed head to toe in scuffed dark pressure armor, one gloved hand fallen slack across {possessive} lap, a dense asteroid field drifting past the canopy overhead - beside {object} a second pilot leans in close, watching the field pass. || cockpit
- A three-quarter character portrait || {Subject} {is_are} seated at a terminal, working a hovering holographic display with one hand, a hulking rust-streaked companion mech looming close behind {possessive} shoulder, its optics glowing faintly in the low light - around {object} banks of server racks glow in the dark. || nogear ownmech
- A dynamic character portrait || {Subject} {is_are} leaning low over the handlebars of a weathered vintage motorcycle, cutting fast across a sunbaked salt flat, {possessive} scarf and hair streaming back in the wind - behind {object} a chain of distant mesas breaks the horizon under a darkening sky. || weather
- A character portrait || {Subject} {is_are} half-turned against open space, a tattered scarf-cloak streaming out weightless behind {object}, hair drifting loose in the void - beyond {object} a churning red nebula glows low around a dark dwarf star.
- A dramatic low-angle character portrait || {Subject} {is_are} crouched low on a rain-slick rooftop ledge, bracing a long rifle sighted down into the streets below, weight settled low over one knee - beneath {object} a dense neon-lit cityscape glows through the downpour. || nogear weather frontline
- A character portrait || {Subject} {is_are} standing braced with both hands flat on a lit control console, framed against a floor-to-ceiling viewport of a rain-swept neon high-rise skyline beyond. || nogear weather
- A dramatic low-angle character portrait || {Subject} {is_are} standing framed close against the camera, hair and jacket lifted by displaced air, glancing back over {possessive} shoulder as a colossal armored war-machine looms directly overhead - the shot angled steeply upward to emphasise its scale against the neon high-rise skyline beyond. || weather
- A dynamic, close character portrait || {Subject} {is_are} raising a compact pistol close to the camera, fine circuitry glowing faintly along {possessive} fingertips and knuckles - behind {object} a pair of masked companions stand watch at a railing overlooking a dense rain-slicked neon cityscape. || nogear weather frontline
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} tumbling backward through open air in cracked powered armor, twin beams of light searing across {possessive} torso and shattering plating away in jagged fragments, hair whipped wild by the fall - far below {object} a dark cityscape glows red beneath the drifting debris. || weather frontline
- A character portrait || {Subject} {is_are} reclined loose in a cockpit's crash seat, one hand reaching lazily out into the glow, banks of console screens and readouts ringing {object} on every side. || cockpit
- A character portrait || {Subject} {is_are} standing at a rooftop ledge, a data-slate held loose in one hand and a sidearm holstered at {possessive} hip, a dark fabric wrap pulled up over the lower face - beyond {object} a dense neon-lit skyline glows red through the night haze. || weather frontline
- A dynamic character portrait || {Subject} {is_are} walking straight toward the viewer down a dim industrial hangar bay, a flight helmet carried loose under one arm, a hulking quadrupedal war-machine striding through drifting steam close behind {object}, overhead lights raking down through the haze. || nogear cockpit
- A character portrait || {Subject} {is_are} standing squared to the viewer, a long white coat draped over {possessive} shoulders, an immense capital ship descending directly behind {object}, its hull lit sharply against a burning red city glow far below, drifting haze softening the skyline. || weather
- A close character portrait || {Subject} {is_are} standing perfectly still as an oversized mechanical hand reaches into frame to project a thin beam of light directly into {possessive} eye, a small stamped code marked at {possessive} cheekbone, the moment held in tense stillness.
- A character portrait seen from behind || {Subject} {is_are} standing atop a rooftop ledge high above a sprawling neon-red cityscape at night, a sidearm held loose and low in one hand, gazing down at the grid of light far below. || nogear weather frontline
- A character portrait || {Subject} {is_are} standing beside a towering crimson war-machine, its cockpit visor glowing pale blue in the dark, {possessive} fitted suit catching the light - around them the dim outline of a nighttime hangar recedes into shadow. || ownmech
- A character portrait seen from behind || {Subject} {is_are} standing at a viewport beside a hulking white powered-armor companion, one hand raised flat against the glass, a stencilled unit number marking {possessive} shoulder - beyond the glass a sunlit planet curves away below, city lights scattered across its night side. || ownmech
- A character portrait || {Subject} {is_are} standing in three-quarter profile, a towering red-and-white war-machine looming just behind {possessive} shoulder, its single optic lit - down the street behind {object} red paper lanterns and shopfront signage glow through the night haze. || weather
- A character portrait || {Subject} {is_are} standing with both cybernetic prosthetic hands raised and pressed together in prayer, forearms segmented and scarred with use, a ring of glowing script arcing overhead like a halo - behind {object} a congregation of hooded, bowed worshippers recedes into a dim golden haze, their faces indistinct. || clergy
- A character portrait || {Subject} {is_are} seated in the open cockpit of a parked attack craft on a rocky ridge at night, flight helmet secured and visor down, a stitched unit patch at the shoulder of {possessive} flight jacket, gazing off past the frame - behind {object} a huge banded planet glows low over the ridge, faint stars scattered through the dark. || weather cockpit
- A character portrait || {Subject} {is_are} standing with a spent cigarette held loosely at the corner of {possessive} mouth, a pair of heavy mechanical support struts trailing cabling rising to either side of {possessive} head - behind {object}, out of focus, a dense hazy cityscape glows faintly through drifting mist.
- A half-body character portrait || Behind {object}, out of focus, is a towering sci-fi skyline beneath a colossal glowing ring-shaped structure hanging in the night sky, freighters and cruisers drifting past its light, the streets below slick with rain and threaded with cool running-lights. || weather
- A character portrait || {Subject} {is_are} seated astride a parked matte-black superbike on a railed overlook, one boot braced against the ground, glancing back over {possessive} shoulder - behind {object} a tiered river city of lantern-lit pagodas and waterfalls spreads below towering spired structures at dusk. || weather
- A character portrait seen from behind || {Subject} {is_are} standing at the foot of a towering dormant war-machine in a cluttered maintenance bay, a ladder propped against its leg and a flight helmet held loose in one hand at {possessive} side, dim standby lighting glowing from vents across its hull - a weathered poster and status monitors line the walls to either side, steam venting low across the floor. || nogear cockpit
- A character portrait seen from behind || {Subject} {is_are} standing at a rocky overlook, a long tattered cloak snapping loose in the wind behind {object}, gazing out over a hazy desert city ringed by tall spires - overhead a massive banded planet with a debris ring dominates the sky, smaller moons scattered around it, the whole scene washed in the deep orange of a dying sun. || weather
- A dynamic character portrait || {Subject} {is_are} standing on the broken rocky surface of an airless moon, a pistol gripped and lowered at {possessive} side, glancing back over one shoulder - behind {object} a searing beam of weapons fire lances low across the horizon, kicking up a spray of debris where it grazes the ground. || nogear frontline
- A character portrait || {Subject} {is_are} reclined loosely in a cockpit seat, one leg - a segmented cybernetic prosthetic - propped up against the console, {possessive} head tipped back and gaze drifting past the canopy - beyond {object} a dense starfield stretches away into the dark, banks of status readouts glowing at the edges of the frame. || cockpit
- A dynamic character portrait || {Subject} {is_are} standing amid drifting debris and fire on a cratered surface, glancing sharply toward the viewer, one heavy geometric shoulder plate catching the light - behind {object} explosions bloom low across the ground and a bright streak burns across the black sky above. || frontline
- A character portrait seen from behind || {Subject} {is_are} standing at the edge of a high rooftop with both arms flung wide, an oversized jacket printed with bold graphic linework across the back - below and behind {object} a dense neon high-rise skyline stretches away into the haze, a single towering spire glowing at the center of the frame. || weather
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} punching forward through the air in heavy powered armor plating, {possessive} lead arm driven out toward the viewer in a braced clawed gauntlet and the trailing arm cocked back, {possessive} legs trailing behind in motion, hair whipped back - behind {object} bright beams of weapons fire streak past low across a debris-strewn battlefield. || weather frontline
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
- A character portrait || {Subject} {is_are} standing on a raised gantry platform beside the crouched bulk of a towering war-machine filling a dim maintenance bay, its single optic sensor lit and a heavy cannon barrel angled down past {object}, faded unit markings stencilled across its scarred armor plating, stacked crates and hazard placards cluttering the shadowed bay floor below. || mechwork
- A character portrait || {Subject} {is_are} sitting atop the broad missile-pod shoulder of an idle war-machine, a cigarette smoking forgotten in one hand, looking out over a muddy grey wasteland toward a distant radio mast, the machine's hull marked with a faded heraldic shield insignia and streaked with rain. || nogear weather
- A character portrait || {Subject} {is_are} walking down a wide ceremonial ramp through falling snow, a combat helmet held loosely in one hand at {possessive} side, faction banners snapping either side and hooded onlookers lining the way, the hulking silhouette of a towering war-machine looming backlit behind {object} in the drifting snow and haze. || weather ceremony
- A character portrait || {Subject} {is_are} standing in profile, a colossal crow-like beast looming close behind {possessive} shoulder, its single eye burning with a saturated glow in the gloom - beyond {object} a ruined stone courtyard fades into rubble and haze. || weather
- A close character portrait || {Subject} {is_are} seen in profile close beside the angular head of {possessive} companion mech, its optics burning twin points in the dark, a stencilled shoulder patch marking {possessive} flight jacket - beyond them a hazy blue-lit hangar recedes into the dark. || cockpit
- A dynamic character portrait || {Subject} {is_are} walking straight toward the viewer down a dim shipboard corridor, a pistol held low and loose in one hand, a second armed companion keeping pace just behind {possessive} shoulder - pipework and hazard striping line the walls to either side, receding into a hazy blue light. || nogear frontline
- A character portrait seen from behind || {Subject} {is_are} standing atop a snow-dusted rooftop unit, hair streaming in the wind, a sheathed blade held loose at {possessive} side, a small cat perched watchful nearby - below {object} a dense neon-lit high-rise cityscape glows through drifting snow. || nogear weather swordwork
- A dramatic low-angle character portrait || {Subject} {is_are} standing at street level as a canyon of soaring high-rises rises sheer on every side, towering signage in unfamiliar characters glowing through drifting rain overhead. || weather
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} weightless in freefall, both arms flung wide overhead and twin long braids drifting loose in the air, {possessive} body arched back in strong foreshortening - beyond {object} the dark hull of a starship interior glints with scattered debris and drifting light.
- A dynamic, low-angle character portrait || {Subject} {is_are} leaning far out over the drop, one hand locked around a strut and {possessive} body braced forward, gazing straight down through a vast light-streaked shaft at a glittering neon cityscape far below.
- A character portrait || {Subject} {is_are} sitting perched on the folded knee of a crouched companion mech, one hand resting easy against its armored plating as its head looms close alongside {object}, twin optics glowing steady - beyond {object} a dense city skyline spreads out below in the fading dusk light. || weather ownmech
- A dynamic character portrait seen from behind || {Subject} {is_are} balanced on the tip of a rooftop antenna mast high above the city, one leg braced and bent, a long coat billowing wide in the wind - far below {object} a dense high-rise skyline glitters with countless warning lights through the downpour. || weather
- A character portrait || {Subject} {is_are} sitting perched on a rooftop ledge, one leg drawn up and a lit cigarette held near {possessive} mouth, gazing out over a vast river-split cityscape glowing under a deep orange sunset. || nogear weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a plant-filled loft apartment with a domed window overlooking a rain-streaked neon high-rise skyline, candlelight and string lights glowing warm across cluttered bookshelves. || weather
- A half-body character portrait || Behind {object}, out of focus, is a fog-bound harbor skyline of towering high-rises, an elevated highway curving low over dark water and a blocky industrial platform lit from beneath. || weather
- A dynamic, low-angle character portrait || {Subject} {is_are} crouched low on a rain-slicked rooftop platform, one hand gripping a glowing energy blade planted point-down and weight braced forward, ready to spring - behind {object} a dense neon-lit cyberpunk skyline rises through drifting haze, a colossal holographic face glowing between the towers and small hovercraft drifting past in the middle distance. || nogear weather frontline
- A character portrait || {Subject} {is_are} gazing up through a viewport in quiet wonder, tubing and cabling trailing from {possessive} suit collar to a bulky comms headset clamped over the ears - beyond the glass a planet's cloud-swirled surface curves away below and a scatter of distant moons hangs in the black.
- A character portrait || {Subject} {is_are} reclined against the fairing of a parked speeder bike, one arm draped along the windscreen and chin propped in {possessive} hand - behind {object} a neon-lit street glows in smeared bursts of color through the haze. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-slicked old-town street lined with lantern-lit shopfronts and parked bicycles, a cherry blossom tree overhanging the road and a distant illuminated tower glowing hazy through the mist. || weather
- A character portrait || {Subject} {is_are} standing in heavy rain at the center of a narrow street, flanked on both sides by towering high-rises plastered with glowing neon signage in unfamiliar characters. || weather
- A character portrait || {Subject} {is_are} standing in profile amid a cherry blossom grove at dusk, petals drifting thick through the air around {object} - the trees glow warm pink and gold in the fading light. || weather
- A character portrait || {Subject} {is_are} standing in heavy rain, glancing back over one shoulder from beneath a wide straw hat, a lit lantern raised in one hand - behind {object} a rain-streaked cityscape of weathered high-rises and faded signage fades into the downpour. || nogear weather
- A dynamic, silhouetted character portrait || {Subject} {is_are} caught mid-swing on a rocky bluff, driving a blade down in a decisive two-handed arc as sparks scatter from the strike, {possessive} cloak and sash ribbons whipped by the motion - behind {object} a massive sun burns low behind hazy mountains and a still lake below. || nogear weather swordwork
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a towering domed tower rising against a hazy dusk sky, two silhouetted figures paused in a lit doorway below. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a paper-screened room with the sliding doors thrown open onto a night sky thick with stars and a drifting nebula.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a windswept plain of pale grass, a second blade planted upright in the ground nearby, its hilt trailing dark streamers. || weather swordwork
- A dynamic character portrait || {Subject} {is_are} walking straight toward the viewer through the burning gate of a hillside shrine, flames engulfing the structure and lantern posts to either side, embers drifting across the smouldering ground underfoot. || nogear weather
- A character portrait || {Subject} {is_are} standing wide-legged with twin blades held loose at {possessive} sides - behind {object} a massive torii gate frames a huge glowing moon low on the horizon, rocky windswept terrain falling away into mist, hung paper talismans stirring to either side. || nogear weather swordwork
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a fog-wrapped hillside town of wooden gatehouses and lit braziers, a sprawling tiered castle rising misty on the ridge above. || weather
- A character portrait || {Subject} {is_are} sitting on a wet rocky shoreline in heavy rain, one elbow propped on a knee - behind {object} a flat grey expanse of water fades into mist. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a mist-shrouded ruin lit by a single stone lantern, a pale spectral face hovering faint in the gloom. || weather
- A dynamic character portrait || {Subject} {is_are} gripping a drawn blade low in both hands, {possessive} robe torn open at the chest and trailing loose in the wind, thick mist coiling around {possessive} legs - behind {object} a total eclipse burns a thin ring of light around a blacked-out sun, its glow diffusing through the haze. || nogear weather swordwork
- A character portrait || {Subject} {is_are} sitting cross-legged beneath a towering maple in full red autumn leaf, fallen petals scattering across the ground around {object} - beyond {object} a weathered shrine's timber eaves rise beside the tree and pale mountains fade into a clear sky. || weather
- A character portrait || {Subject} {is_are} standing in profile with a cigarette held loosely between {possessive} lips, gripping two sheathed blades low at {possessive} hip - behind {object} the fogged silhouette of a ruined industrial structure looms half-lost in the mist. || nogear weather swordwork
- A character portrait || {Subject} {is_are} standing with arms crossed against the wind, hair lifted loose and small birds startled into flight around {object} - behind {object} a golden field of tall grass sways beneath a hazy sky. || weather
- A character portrait seen from behind || {Subject} {is_are} standing at the edge of flooded paddy fields at dusk, a sheathed sword resting at {possessive} hip, gazing out over the water - power lines and utility poles cut across the hazy sky beyond {object}. || nogear weather swordwork
- A character portrait seen from behind || {Subject} {is_are} walking away through drifting fog and bamboo toward a distant pagoda silhouette, a sheathed blade at {possessive} hip - the temple's tiered roofline fades into the mist ahead. || nogear weather swordwork
- A dramatic low-angle character portrait || {Subject} {is_are} standing atop a rocky summit in full armor, a sheathed blade held point-down at {possessive} side, drifting red leaves swirling past - behind {object} an enormous full moon fills the sky through a wreath of storm cloud. || nogear weather swordwork
- A character portrait || {Subject} {is_are} standing before a weathered torii gate at night, armor catching the pale light, a scatter of vivid red flowers spread across the ground around {object} - mist pools low between bare trees and a hooded figure waits distant among aged grave markers behind {object}. || weather swordwork
- A close character portrait || {Subject} {is_are} sitting with head bowed, a sheathed sword held loose across {possessive} lap, petals drifting thick through the air around {object} - beside {object} a second blade stands planted upright, a small paper talisman glowing faintly at its hilt. || nogear weather swordwork
- A wide character portrait || Behind {object}, softly blurred well out of focus, a corroded knight-engine wades through ankle-deep floodwater, a jagged chain-bladed arm raised and skull-toothed plating dripping with soot and embers. || weather warzone @grimdark
- A wide character portrait || {Subject} {is_are} lounging deep in a skull-carved throne, cloak pooled over the armrest and one boot draped past a grinning skull finial, hands resting easy on the bone-white arms - within a smoke-hazed hall of crumbling gothic stone lit cold, black feathers drifting past. || nogear ceremony @grimdark
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a towering war engine firing twin cannons through drifting smoke, its eagle-marked armor scarred and scorched. || weather warzone @neogothic
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a corrupted war engine looming out of the haze, horned and tusked, trailing chains and dangling trophies from a clawed fist. || warzone @grimdark
- A character portrait || {Subject} {is_are} standing on an iron gantry, pen in hand annotating a clipboard, one shoulder braced with a leather pauldron - behind {possessive} shoulder looms a towering war engine's gilded, skull-marked head, its sensor-eyes glowing steady in the gloom. || nogear mechwork @neogothic
- A character portrait || {Subject} {is_are} leaning over a scaffold rail with a wrench in hand, tightening bolts on a towering mobile suit's sensor head looming close behind {object}, cable conduits and gantry struts crowding the frame. || nogear mechwork @gundam
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a mobile-suit production gantry, war machines suspended in scaffolding beneath hazard-striped catwalks and a safety banner. || mechyard @gundam
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a sprawling tomato patch, heavy fruit-laden vines climbing staked rows under open sky. || weather
- A character portrait || {Subject} {is_are} hunched at a cluttered desk of humming terminal equipment and tangled cable runs, glancing up sharply at a shadow in the doorway - fluorescent light bars glinting off server racks and taped-up notices behind {object}.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a dim institutional corridor, flickering fluorescent tubes above a scuffed door and a lone waste bin.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a weathered stilt-built river town, houseboats moored along a plank dock beneath sagging corrugated roofs. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a stone arch bridge spanning a slow river, glass towers rising beyond a green, overgrown embankment. || weather
- A wide character portrait || Behind {object}, softly blurred well out of focus, is a towering white combat walker suspended in a service gantry, ground crew in coveralls swarming its limbs across a hazard-striped deck. || mechyard
- A wide character portrait || Behind {object}, softly blurred well out of focus, is a pair of heavy gunships banking hard through a bank of storm cloud, cannon pods and missile racks bristling from their articulated weapon arms. || weather
- A wide character portrait || {Subject} {is_are} wading ashore from a beached inflatable boat, rifle held low and ready, boots crunching over dockside rubble - gantry cranes and floodlights glowing through rain and fog behind {object}. || nogear weather frontline
- A wide character portrait || {Subject} {is_are} standing at the tail of a parked sports car atop a sunlit overlook, weight shifted onto one hip, a distant glass tower rising past scattered clouds. || weather
- A half-body character portrait || {Subject} {is_are} sitting hunched over a slim laptop at a train tray-table, hood drawn up against the compartment lights, rain streaking neon signage that smears past the window in long coloured lines.
- A close character portrait || {Subject} {is_are} sitting atop a mound of stripped combat-frame wreckage, boots planted on a skeletal actuator arm, scavenged machine parts sprawling into darkness under a pair of close, cratered moons. || weather salvage @scav
- A wide character portrait || {Subject} {is_are} standing at a rain-slicked overlook rail with a great cat settled at heel, watching a glowing ring-gate span a sea of cloud toward a floating district of lantern-lit pagoda towers. || weather @neosamurai
- A wide character portrait || {Subject} {is_are} striding forward with one hand looped through a great cat's harness at {possessive} side, cloak snapping back-lit by a churning vortex of light framed between two rune-carved standing stones - across a windswept, fog-slicked stone concourse. || weather
- A wide character portrait || {Subject} {is_are} standing motionless on a barren lunar plain, a blue Earth and a river of stars filling the black sky above the jagged horizon.
- A wide character portrait || {Subject} {is_are} standing motionless in the rain beneath a vast hovering vessel, its underside ringed in light, a dense skyline glowing behind {object}. || weather @gundam
- A wide character portrait || {Subject} {is_are} sitting cross-legged on a sunlit wooden engawa with a sketchbook and iced tea set at {possessive} side, a mossy stream and stone-set waterfall running just beyond the rail.
- A wide character portrait || {Subject} {is_are} standing at the ledge of a rain-slick rooftop, {possessive} weight braced on one heel as a neon-veined skyline spreads out far below. || weather
- A wide character portrait || {Subject} {is_are} walking a moss-swallowed street between crumbling towers, cabling and lit windows overhead, exhaust haze drifting between the ruined blocks. || weather @scav
- A close character portrait || {Subject} {is_are} reclined in a battered cockpit chair, boots up on the console, {possessive} scarf loose across one shoulder as star-flecked space and a lit console glow beyond the canopy. || cockpit
- A wide character portrait || {Subject} {is_are} kneeling in silence before a towering glowing gate, hands folded in {possessive} lap as stone lanterns burn on either side and embers drift up through the dark shrine hall. || @neosamurai
- A wide character portrait || {Subject} {is_are} trudging down a snowbound rail line, rifle slung across {possessive} back, boots crunching through drifted snow between gutted trolley cars and frost-blackened tenements lost in the storm. || weather frontline @scav
- A wide character portrait || {Subject} {is_are} perched astride a hulking mech's shoulder joint, one hand braced on a control lever jutting from the housing - a neon-washed skyline and a second machine's optics glow hazy behind. || weather ownmech @gundam
- A wide character portrait || {Subject} {is_are} reclined against the headrest with both arms raised behind {possessive} head, half-lit console displays lining the rails below - a banded gas giant curves past the canopy overhead. || cockpit
- A wide character portrait || Behind {object}, softly blurred well out of focus, is a towering wall of technical schematics lit crimson, ticker readouts scrolling across it. || @cyberpunk
- A wide character portrait || {Subject} {is_are} standing poised at the front of a torchlit crowd, masked figures packed shoulder to shoulder behind {object} - towering screens and drifting sparks light the smoke-hazed rally ground. || ceremony @cyberpunk
- A wide character portrait || Behind {object}, softly blurred well out of focus, is a rain-slick neon skyline threaded with cable between towers, a distant explosion flaring against the haze. || weather @cyberpunk
- A wide character portrait || {Subject} {is_are} crouched on a battered mech's shoulder, torch sparking bright as {subject} welds a seam in the plating - a sunset ridge of hills sprawls hazy behind the machine. || nogear weather mechwork @gundam
- A half-body character portrait || {Subject} {is_are} strumming a battered acoustic guitar, {possessive} head tilted toward the fretting hand - a candlelit room glows beyond, an old piano topped by a watching black cat and frost-laced windows in the dark. || nogear
- A half-body character portrait || {Subject} {is_are} pulling open a heavy plank door, sunbeams cutting across a cluttered workshop-bar lined with hanging lanterns, shelved bottles and tools. || nogear @scav
- A half-body character portrait || {Subject} {is_are} working a hand pump at an open-air bar counter tucked under a rusted porch, sun-bleached hills and a distant industrial skyline rolling beyond the pipework columns. || nogear weather @scav
- A wide character portrait || {Subject} {is_are} walking toward a rust-streaked scavenger trading post, a spotted hyena loping at {possessive} heel - pressure tanks and tangled pipework rise behind a hand-lettered sign under sun-bleached desert hills and a wide open sky. || weather @scav
- A wide character portrait || {Subject} {is_are} glancing back over {possessive} shoulder atop a rain-slicked rooftop, blade drawn at {possessive} side - a dense skyline of stacked signage and towers glowing beyond. || nogear weather frontline @cyberpunk
- x2 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a canal-side street in an old quarter, laundry strung between concrete tenements above brown water and stacked signage climbing the walls in unfamiliar scripts. || weather
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} falling backwards off the parapet of a tower block, arms spread wide and {possessive} coat snapping open, the grid of streets and rooftops laid out far below - {possessive} outline already shimmering and refracting as optical camouflage takes hold, bending the light behind {object}. Dramatic foreshortened composition. || nogear weather frontline
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a dim diagnostic bay, a reclined chair beneath a hooded scanner and thick cable looms dropping from the ceiling to a wall of dark racked hardware.
- A character portrait || {Subject} {is_are} standing ankle-deep in the flooded arcade of an abandoned shopping street, still water mirroring the dead signage overhead, a shaft of grey daylight falling through a collapsed section of roof far ahead. || weather
- A close character portrait || {Subject} {is_are} seated in the dark of a parked surveillance van, a bank of monitors washing {possessive} face in pale grey light, cable looms underfoot and cold cups crowding the console. || deskwork
- A half-body character portrait || Behind {object}, out of focus, is the wrecked hall of a natural history museum, a shattered tree-of-life mural across the far wall and the slumped bulk of a disabled multi-legged combat walker among the fallen masonry. || warzone
- x2 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a maintenance hangar, a boxy industrial work-mech kneeling in its cradle with gantry crews along its arms and arc-welding flare stuttering off the walls. || mechyard
- A character portrait || {Subject} {is_are} standing on a seawall above a vast reclaimed-land project, dredgers and gantry cranes ranked across flat grey water behind {object} and a typhoon sky stacking up dark on the horizon. || weather
- A character portrait || {Subject} {is_are} leaning at the counter of a late-night noodle stall beneath a highway overpass, steam rolling off the pass and rain sheeting off the awning's edge into the road behind {object}. || weather
- x2 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-lashed construction site at night, pile drivers and floodlit scaffolding rising around the shell of a half-built tower. || weather
- A character portrait || {Subject} {is_are} standing on an iced-over bridge deck in falling snow, an armored vehicle slewed across the roadway behind {object} and the grey shape of an airship hanging low over a silent skyline. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cramped divisional office of stacked case files and dead desk plants, a fan turning slowly above a wall of pinned notices.
- A close character portrait || {Subject} {is_are} sitting in the back of a parked command vehicle, folding console screens open around {object} and a wall of labelled switches lit dull amber at {possessive} shoulder. || deskwork
- A character portrait || {Subject} {is_are} standing in the flooded, listing hold of a derelict cargo ship, water washing across the canted deck around {possessive} boots and a shaft of daylight falling through torn hull plating far above.
- A character portrait || {Subject} {is_are} kneeling on a hangar deck beside a loaded stretcher, one hand steadying the casualty's shoulder and a pressure dressing held ready in the other, {possessive} opened kit spilling ampoules across the plating beside {object} - behind {object} the scuffed foot of a war-machine and a press of legs recede into the bay's hard overhead light. || nogear medic
- A character portrait || {Subject} {is_are} standing in a warship's sick bay reading a bulkhead vitals display with {possessive} arms folded, three empty berths racked in a row behind {object} and a stowed stretcher strapped flat to the wall, cold white light falling even across the compartment. || medic
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is the interior of a triage tent, saline bags hanging from a strut above a folding cot and a caged work lamp burning against the canvas. || medic
- A character portrait || {Subject} {is_are} peeling off a pair of tacky gloves at the mouth of a field surgery, {possessive} apron streaked and {possessive} sleeves shoved past the elbow, an unlit cigarette waiting at the corner of {possessive} mouth - behind {object} a tarpaulin awning sags under the rain and a generator throbs beside stacked supply crates. || nogear weather medic
- A character portrait || {Subject} {is_are} bent close over a clinic chair under a swing-arm lamp, working a fine driver into the opened forearm housing of a patient's prosthetic, tool trays and spooled cabling crowding the bench at {possessive} elbow - the room's tiled walls throw back a faint green cast from the lamp. || nogear medic
- A character portrait || {Subject} {is_are} sitting on the lowered tail ramp of a parked medical transport with a flask cradled in both hands and {possessive} kit bag slumped against {possessive} leg, watching a grey dawn come up over a churned airfield - a stencilled medical cross flakes at the ramp's edge beside {object}. || nogear weather medic
- A character portrait || {Subject} {is_are} standing waist-deep among stacked frame torsos in a breaker's yard, a cutting torch idle in one gloved hand and a hauling strap slung across {possessive} chest - behind {object} a gantry crane swings a severed limb section slowly against a flat white sky. || nogear weather salvage
- A character portrait || {Subject} {is_are} crouched inside the opened chest cavity of a downed war-machine, {possessive} headlamp throwing a hard cone across severed cable looms as {subject} works a connector free - the machine's ribbed interior recedes into the dark around {object}. || nogear salvage
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a tidal scrapyard at low water, half-sunk hulls and stripped actuator limbs bedded in grey mud beneath a wide colourless sky. || weather salvage
- A character portrait || {Subject} {is_are} sitting on an upturned crate beside a weighing scale heaped with salvaged servo parts, arguing a price with a dealer whose back fills the foreground out of focus - behind {object} a tarpaulin stall of sorted scrap glows amber under strung work lights. || salvage
- A character portrait || {Subject} {is_are} walking a narrow catwalk between towering stacks of crushed vehicle bodies, a coil of recovered cable looped over one shoulder and a sorting hook swinging in {possessive} free hand - rust-red canyon walls of compacted metal rise to either side of {object} into a hazy sky. || nogear weather salvage
- A character portrait || {Subject} {is_are} standing on the sun-blasted upper hull of a beached colony section prying at a seam with a long bar, {possessive} shadow thrown long across the plating - behind {object} the structure's torn ring curves away into a heat-shimmering desert. || nogear weather salvage
- A character portrait || {Subject} {is_are} standing in a hangar doorway with a sealed document wallet tucked under one arm, taking in the bay ahead without stepping into it, {possessive} lanyard badge turned face-out at {possessive} chest - work crews and a shrouded war-machine stand paused in the light behind {object}. || nogear inspection
- A character portrait || {Subject} {is_are} seated across a bare interview table from an empty chair, a recorder set squarely between them and {possessive} hands folded on a closed folio - the room's acoustic panelling and one high window recede flat and grey behind {object}. || inspection
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a records vault of racked archive boxes and rolling ladder rails, a single strip light burning away down a long aisle. || inspection
- A character portrait || {Subject} {is_are} holding a stamped compliance placard up against a machine housing on a factory floor, comparing it to the serial plate at eye level - conveyor lines and a shift-change crowd blur away behind {object} under flat sodium light. || nogear inspection
- A character portrait || {Subject} {is_are} standing at a rain-lashed dockside barrier with a tablet held low and shielded under one arm, watching a container crane work - floodlights burn cones through the downpour behind {object} and a queue of idling haulers stretches back to the gate. || nogear weather inspection
- A character portrait || {Subject} {is_are} descending a spiral stair into a colony's lower service level, one hand on the rail and a survey lamp raised in the other, condensation beading the pipe runs that crowd the shaft around {object}. || nogear inspection
- A character portrait || {Subject} {is_are} standing behind a narrow bar counter polishing a glass with both elbows loose, the back-bar shelves stacked with mismatched bottles under a strip of warm tube light - a patron's shoulder blurs across the foreground and rain streaks the window beyond {object}. || nogear weather barkeep
- A character portrait || {Subject} {is_are} leaning across a booth table with both palms flat on the laminate, saying something low to a figure seated out of focus opposite - behind {object} the bar's back room glows in stacked neon and a beaded curtain hangs half-parted. || barkeep
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a shuttered bar at closing, chairs upended on the tables and a lone pendant lamp burning over a wiped-down counter. || barkeep
- A character portrait || {Subject} {is_are} sitting at the end of {possessive} own counter with a ledger open and a cash tin beside it, glancing up at the door - behind {object} a wall of pinned business cards, chits and faded photographs climbs to the ceiling beside a dead payphone. || nogear barkeep
- A character portrait || {Subject} {is_are} drawing a cellar hatch shut behind {object} with a crate of bottles balanced on one hip, the stairwell's bare bulb still swinging - overhead the bar's floorboards leak music and the moving shapes of feet. || nogear barkeep
- A character portrait || {Subject} {is_are} standing under a taped-over security monitor at the end of the bar with {possessive} arms folded, watching four grainy feeds of the alley and the door while the room's warm noise blurs past {possessive} shoulder. || barkeep
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} coasting head-on toward the viewer down the central shaft of a colony spoke, arms tucked close and {possessive} body tilted no more than about 30 to 40 degrees off vertical, hair fanned loose around {possessive} face - the shaft's ladder rungs and stencilled level numbers streak away behind {object}. Dramatic foreshortened composition.
- A character portrait || {Subject} {is_are} floating in a darkened observation blister with {possessive} legs drawn up and drifting, one hand steadying against a console rail, a scatter of pens and a loose clipboard hanging motionless in the air around {object} - the room's readouts glow dim across {possessive} face.
- A character portrait || {Subject} {is_are} hanging weightless in a station galley with one boot hooked under a table rail, a drink bulb held loose and {possessive} body turned a mild 20 to 30 degrees off vertical, crumbs and a spoon suspended nearby - stowage netting and taped-up duty notices line the bulkhead behind {object}.
- A character portrait || {Subject} {is_are} braced weightless in a launch tube with both hands on the guide rails, {possessive} body angled a mild 20 to 30 degrees off vertical and {possessive} hair lifted free, gazing away down the tube past the frame - ranked catapult lights recede behind {object} into the dark.
- A dynamic character portrait || {Subject} {is_are} turning weightless in the air of a zero-gravity gymnasium ring, one arm sweeping wide and the other tucked close, {possessive} body tilted no more than about 30 to 40 degrees off vertical - behind {object} the inner wall of a colony cylinder climbs away, its terraced farmland hanging overhead through the haze.
- A character portrait || {Subject} {is_are} drifting weightless down a corridor left dark by a power loss, one hand trailing along the wall rail and emergency chemlights glowing green at intervals past {object}, loose paperwork turning slowly in the air around {possessive} shoulders.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a zero-gravity cargo lock, netted pallets hanging untethered in the air beneath a rank of amber warning strobes.
- A character portrait || {Subject} {is_are} clamped by one boot to the spine of a drydocked warship in a sealed EVA pressure suit and helmet, visor down, a torque tool floating tethered at {possessive} hip, looking back along the hull - beyond {object} the ship's bare ribs recede into the scaffold and a work light glares white off the plating. Dramatic rim lighting along {possessive} silhouette. || vacuum
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} pushing off toward the viewer through a debris field in a sealed EVA pressure suit and helmet, visor down, one gauntlet thrust out at the camera and {possessive} tether whipping loose behind {object}, {possessive} body tilted no more than about 30 to 40 degrees off vertical - shattered panel fragments turn slowly past {object} against the starfield. || vacuum
- A character portrait || {Subject} {is_are} standing magnet-soled on the outer hull of a colony cylinder in a sealed EVA pressure suit and helmet, visor down, one gauntlet raised against the glare and a survey slate clipped at {possessive} thigh - the cylinder's vast painted flank curves away behind {object} toward a distant mirror panel burning white. || vacuum
- A character portrait || {Subject} {is_are} leaning in over a shoulder-height plot table with both fists planted either side of a lit tactical overlay, calling something off past the frame - ranked operator stations glow blue behind {object} in the dim of a flag bridge. || nogear deskwork
- A character portrait || {Subject} {is_are} seated at a combat information console in a headset, one hand cupped over the earpiece and the other steady on a trackball, a wall of plot repeaters washing {possessive} face green in the dark. || nogear deskwork
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a night watch room, three unmanned consoles glowing beneath a wall clock and a rack of dead handsets. || deskwork
- A character portrait || {Subject} {is_are} standing at a division office whiteboard with a marker capped in one hand, a duty roster and a pinned street map crowding the wall beside {object} - behind {possessive} shoulder mismatched desks stand heaped with folders under a slowly turning fan. || nogear deskwork
- A character portrait || {Subject} {is_are} reclined at a listening station with {possessive} headphones pushed off one ear and {possessive} boots crossed on the desk edge, spectrogram traces crawling across three stacked displays - the booth's soundproofing recedes into shadow behind {object}. || deskwork
- A character portrait || {Subject} {is_are} seated in an editing suite with a segmented playback rig lowered over {possessive} temples, both hands paused above a scrub wheel, layered recording windows hanging in the air around {possessive} head and throwing shifting colour across {possessive} face. || nogear deskwork
- A character portrait || {Subject} {is_are} standing behind a seated operator's chair on a dim watch floor, one hand on the seat back and {possessive} attention up on the big board, a mug of tea going cold on the console below - rows of glowing stations stretch away behind {object} into the dark. || nogear deskwork
- A character portrait || {Subject} {is_are} bent close over a paper plotting chart under a hooded lamp, drawing a bearing line with a parallel rule and a handset trapped between {possessive} shoulder and ear - the rest of the plot room falls away into red-lit gloom behind {object}. || nogear deskwork

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

<!--
  TOKEN ONLY. The portrait takes its pose from Backdrop; this table reaches
  only the token, which renders on flat white so the RMBG pass can cut it to a
  transparent PNG for dropping onto a battlemap.

  So a bullet here may describe the BODY and nothing else. No ground, no
  ledge, no wall, no furniture, no weather, no props that are not held in a
  hand. A pose may crouch, kneel or sit - it simply must not sit on anything.

  This is not a style preference. Generation runs at CFG 1.0 with no negative
  prompt, so the template's trailing "no environment" cannot argue a noun back
  out of the image: a rolled "raised ledge" put a visible platform under the
  figure and a second person on it. test_stance_content.py enforces the rule.
-->

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
- standing with head bowed and shoulders drawn in tight
- standing in a slow half-bow, one hand pressed flat against the chest
<!-- - standing with both arms raised overhead, a long board gripped in both hands and braced across the back of the shoulders like a yoke || hands -->
- sitting cross-legged in a formal meditative pose, palms pressed together at the chest, segmented mechanical arms folded still || hands
- leaning forward and down, braced on one forearm, the other hand reaching toward something out of frame || hands
- crouched low and coiled, weight braced forward on one arm, ready to spring || hands
- leaning low into a forward sprint, {possessive} braid whipped back and one arm driving down
- crouched low on one knee, both hands wrapped around an upright blade, ready to spring || hands armed
- standing in profile with head bowed slightly, one hand resting on a sheathed blade at the hip || hands armed
- caught in a dynamic overhead swing, both hands driving a blade down in a decisive arc, cloak and sash ribbons whipped by the motion || hands armed
- kneeling formally with both hands folded around an upright hilt held back against one shoulder || hands armed
- kneeling in profile with head bowed low, hands stilled in {possessive} lap
- walking straight toward the viewer with {possessive} weapon raised over one shoulder, cloak snapping back behind {object} || hands armed
- raising {possessive} weapon high overhead in both hands, mid-swing, hair whipped wild by the motion || hands armed
- sitting cross-legged with one elbow propped on a knee, chin resting in that hand, gazing out in quiet thought
- standing tense with both hands crossed at the hip, one gripping the hilt of {possessive} sheathed weapon, poised to draw || hands armed
- crouched low on the balls of the feet, one fist raised in a guarded ready stance, weight coiled forward || hands
- standing with one hand raised to shade {possessive} eyes while scanning the middle distance

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
- standing with both hands laced behind {possessive} head, elbows out, utterly at ease || hands
- standing with both weapons drawn, one leg braced forward and the coat's tails caught mid-swirl || armed gun

## Prompt templates

These are the sentences the script assembles the rolled traits into. They are
reproduced here so the style is visible in one place alongside the tables, but
they live in `generate-npc.py` — editing them here changes nothing.

### Portrait (1024x1024, straight to the Foundry actor sheet, no background removal)

> **{SHOT}** of **{ROLE}**, **{AGE}**, rendered in a detailed
> painterly illustration style with fine grain texture and clean linework, halftone
> dot shading worked into the shadows, moody cinematic lighting. {SUBJECT} is
> **{BUILD}**, with **{TRAITS}** **{SKIN}**, **{HAIR}**, and **{EYES}**, and **{FEATURE}**,
> wearing **{OUTFIT}**, **{FACTION_LINE}**{POSSESSIVE} clothing following the shape
> of {POSSESSIVE} frame. **{HEADGEAR}** {POSSESSIVE} face carries
> **{DEMEANOR}**. {SUBJECT} carries
> **{GEAR}**. **{BACKDROP}** **{WEATHER}** **{GLOW_LINE}** Shallow depth of field, square
> framing, high detail, atmospheric sci-fi character portrait. Painterly illustration
> throughout with visible brushwork, heavy fine grain texture over every surface, and
> dense halftone dot screentone worked deep into the shadows.

`{TRAITS}` is not rolled from a table at all: it is a fixed clause the script
asserts for every woman — currently "full lips, feminine posture" — including
one whose `Age` came up `young`, since it describes a face and a bearing rather
than an adult figure. It lives in `GENDER_TRAITS` in
`generate-npc.py`, because a trait that should reach nearly every NPC of one
gender cannot come out of a pool of thirty bullets.

`{FACTION_LINE}` is the rolled Faction's visual signature alone, already
comma-suffixed and ready to sit in front of "{POSSESSIVE} clothing following
the shape of {POSSESSIVE} frame" — never the affiliation name.
`split_faction()` keeps the name ("Smith-Shimano Corpro") for the dossier's
"Affiliation" row only; the name never reaches either prompt. The two
non-affiliations (`Unaligned`, `Unregistered`) roll no visual at all, so
`{FACTION_LINE}` is empty for them and the sentence reads "wearing
**{OUTFIT}**, {POSSESSIVE} clothing following..." with no orphaned comma.

`{HEADGEAR}` is a whole sentence rather than a noun phrase, and so is
`{WEATHER}` — which is empty unless the rolled Backdrop is flagged `weather`.
`{SHOT}` and `{BACKDROP}` are the two halves of one Backdrop bullet, split on
`||` — the opening phrase and the scene. Rolling them together is what lets a zero-gravity
entry restage the whole shot, swapping "a half-body character portrait" for "a
dynamic, dramatically foreshortened character portrait" and putting the subject
in freefall, without a separate pose table to keep in sync.

`{GLOW_LINE}` takes one of four forms, crossing two independent questions:
whether anything rolled for this NPC would actually cast a glow
(`has_light_source()`), and whether the rolled Faction asserts pigment of its
own (flagged `palette`) — pigment (dye in cloth) and glow (light) are
different things and coexist happily, but the line's wording has to agree
with whichever pair is true this roll:

- **Glow, no pigment** — "A faint **{GLOW}** glow falls across one side of
  {POSSESSIVE} face against warm dim ambient light on the other. Keep the
  palette restrained — greys, olive drab and rust — with **{GLOW}** the only
  saturated color in the frame."
- **Glow, with pigment** — the same sentence, but "the only saturated color"
  softens to "the only **other** saturated color", since the Faction's own
  colours are already in frame and the line would otherwise contradict the
  uniform it just described.
- **No glow, no pigment** — "Keep the palette restrained — greys, olive drab
  and rust, with no stray saturated color."
- **No glow, with pigment** (`GLOW_NONE_PIGMENT`) — "Keep the rest of the
  palette restrained — greys, olive drab and rust." The "no stray saturated
  color" claim is dropped entirely rather than kept and contradicted, since
  the Faction's pigment is itself a saturated color already in the frame.

The glow half of that pairing fires only when something rolled for this NPC
would actually cast the glow — a lit instrument panel, neon signage, a muzzle
flash in the Backdrop scene, or a glowing/lit detail in Gear, Outfit,
Headgear, Feature or Eyes. `has_light_source()` in `generate-npc.py` checks
the rolled text of those fields against a short list of light-implying words
(`glow`, `lit`, `neon`, `lantern`, `beacon`, `readout`, `monitor`, `display`,
`screen`, `flame`, `ember`, `burning`, `instrument`, `holographic`,
`headlamp`, `glaring`, `muzzle flash`) — deliberately excluding plain daylight
words like `sun`, since natural light doesn't motivate an arbitrary saturated
glow color either. Absent that, `{GLOW_LINE}` falls back to one of the two
no-glow forms above instead of inventing a source for a color that has
nothing to shine from — which used to happen on plenty of rolls (a dim mech
hangar, a dropship bay door against a plain sky) and is why a stray green
glow could land on a face with nothing nearby to cast it.

### Token (1024x1280, then RMBG to a transparent PNG)

> A full-body character illustration of **{ROLE}**, **{MATURITY}** **{GENDER}**
> **{AGE}**, rendered in a detailed painterly illustration style with fine
> grain texture, clean linework and halftone dot shading worked into the
> shadows, moody cinematic lighting on the figure. {SUBJECT} is facing the
> viewer, {POSSESSIVE} whole figure in frame from the top of {POSSESSIVE} head to
> the soles of {POSSESSIVE} shoes, the head drawn small in frame with clear empty
> space above and below, in
> realistic adult proportions roughly seven to eight heads tall. {SUBJECT}
> is **{HEIGHT}**, **{BUILD}**, with **{TRAITS}**
> **{SKIN}**, **{HAIR}**, **{EYES}**, and **{FEATURE}**, wearing **{OUTFIT}**,
> **{FACTION_LINE}**{POSSESSIVE} clothing following the shape of {POSSESSIVE}
> frame. **{HEADGEAR}**
> {POSSESSIVE} face carries **{DEMEANOR}**. {SUBJECT} carries **{GEAR}**.
> {SUBJECT} is **{STANCE}**, both feet in frame, the pose natural and
> unforced. **{GLOW_LINE}** The background alone is a solid flat plain white,
> no texture, no gradient, no shadow, no environment. Full-length wide shot,
> the whole figure clear of the frame edge, centered composition,
> dramatic lighting, isolated character illustration, clean silhouette,
> painterly brushwork with heavy grain and dense halftone screentone worked
> into every shadow.

`{FACTION_LINE}` is the same pre-formatted, visual-only slot the portrait
uses — see the portrait section above; the affiliation name never reaches
either prompt, only the dossier.

`{GLOW_LINE}` here takes one of the same four forms as the portrait's, gated
the same way — except the token has no backdrop at all (it's flat white for
RMBG), so only an equipped source counts: something glowing or lit in the
rolled Gear, Outfit, Headgear, Feature or Eyes.

- **Glow, no pigment** — "Keep the palette restrained — greys, olive drab and
  rust — with a single **{GLOW}** glow the only saturated color."
- **Glow, with pigment** — the same sentence with "the only saturated color"
  softened to "the only **other** saturated color".
- **No glow, no pigment** and **no glow, with pigment** fall back to the same
  two strings as the portrait's no-glow cases above - both prompts share the
  one `GLOW_NONE` and one `GLOW_NONE_PIGMENT` constant in `generate-npc.py`
  rather than each keeping their own copy of an identical sentence.

See the portrait section above for the light-implying word list.

The framing sentence names no footwear. It used to - "plain modern boots, no
leg wraps or puttees" - back when the painterly style kept defaulting to
wrapped WWI-style puttees rising from the boot tops with nothing said about
them. The Faction and Outfit tables now describe each faction's dress
specifically enough that the drift no longer happens, and the old clause was
actively wrong for any character who isn't in boots at all. "the soles of
{POSSESSIVE} shoes" asserts the framing - the bottom of the figure is in shot -
and still leaves what is actually on the feet to Outfit, which names the
footwear for the factions that have any.

It says "shoes" rather than "feet" because a shoe is a worn object rather than
a body part, so the clause reads as an instruction about where the frame ends
rather than about anatomy. "Shoes" stays generic enough not to fight a rolled
boot, sandal or greave the way the old "plain modern boots" did.

The opening sentence asserts framing, not pose. It used to read "standing at
full height", which fought the rolled Stance on every crouching, kneeling or
sitting bullet - the prompt asserted standing and crouching at once and the
render came back with two figures. Stance owns the pose; this sentence owns
the framing, and the two no longer overlap.

Framing is asserted three times, and that is deliberate. "the whole figure in
frame ... to the soles of {POSSESSIVE} shoes" on its own was losing at CFG 1.0
to the detail the rest of the prompt asks for: the model anchored the head near
the top of the canvas, drew it at portrait scale, and ran out of room somewhere
around the shins, cropping off the feet the sentence had just promised. Two
clauses were added against that.

- **"the head drawn small in frame"** is the scale instruction that
  "seven to eight heads tall" was being asked to carry and cannot. A head-count
  is a _ratio_ between head and body, and a head too big for the canvas
  satisfies it just as well as one that fits - the proportions came back
  correct and the feet still came back missing. This says the absolute size.
- **"Full-length wide shot, the whole figure clear of the frame edge"** opens
  the closing tag block. That block is the position a diffusion model weights
  hardest, and it was naming the composition ("Centered composition") without
  ever naming the _distance_; shot-scale vocabulary is the term the training
  data actually indexes framing under.

A Stance that reaches upward - arms raised overhead, something held above the
shoulders - spends vertical canvas at the top and squeezes the feet hardest, so
those bullets are the ones to check first if cropping reappears.

The `even lighting` / flat-background phrasing this used to carry was flattening
the whole render toward a clean cel-shaded look rather than just the background —
`{GLOW}` aside, the token came out visibly less painterly than the portrait even
though both prompts asserted the same style words. Scoping "no texture, no
gradient" to "the background alone" and giving the figure its own "moody
cinematic lighting" / "dramatic lighting" cue keeps the flat cutout background
Comfy's RMBG pass needs, without pulling the figure's rendering along with it.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt — the same
generation settings as every other prompt file in this folder.
