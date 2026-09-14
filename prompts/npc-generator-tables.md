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

A bullet of the form `- => Name` is a **group reference**: one slot of this
table whose value is drawn second, from the `## Name` table. Ten near-identical
black dresses in a `## Black dresses` table then weigh what one distinct jacket
weighs, and the specific dress is chosen inside the group. A reference takes an
`xN ` weight like any bullet and may carry `@theme` tags (`- => Black dresses
(gundam) || @gundam`), which make the whole group a themed one - except in
`## Backdrop`, whose note explains why a tag there is not read; it carries no
other flags, since `civ`, `mil`, `notac` and `dressy` belong on the members. A
group may have `(she)` and `(she) +` variants like any table, and a reference
placed in `## Outfit (she) +` makes the group women-only. One level only: a
group table holds no references. The script refuses a reference that names a
missing table or a rolled table, one that claims a group a second time for the
same family (a table and its variants count as one), and one written in a table
the script also draws somewhere that cannot resolve it - Gear, which a `nogear`
backdrop re-draws, and the traits an old entry re-rolls by hand. The `###`
sub-headings under Callsigns are the other kind of grouping, cosmetic only.

**Adding a new group** takes three steps, and the order of the blocks matters,
because a table runs from its heading to the next `##` heading:

1. Add one reference bullet, `- => Formal wear`, at the end of `## Outfit`. That
   single bullet covers the group's `(she)` variants too. Don't also add
   `- => Formal wear (she) +` to `## Outfit (she) +`. It isn't refused, but it
   gives she/her NPCs a second Formal wear slot that draws only from the
   `(she) +` bullets, doubling the group's weight for them. Put the reference in
   `## Outfit (she) +` *instead* only when the whole group should be women-only.
2. Add the `## Formal wear` table, and its `## Formal wear (she) +` if it has one,
   **after the last bullet of `## Outfit (she) +`**, beside the other group
   tables (`## Flight suits` onwards, before `## Weapon`). Never put a heading
   directly under `## Outfit (she) +` or between any table's bullets: every
   bullet below the new heading moves into the group. Outfit's own `=> ...`
   references are among them, and they then fail the one-level rule.
3. Write the members as plain bullets carrying their own flags. Once the heading
   exists, the importer and the Tables tab can add bullets to it, but neither
   ever creates a heading or a `=>` reference.

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
  exclusion, like the `admin` and `outlaw` role locks and unlike every preference filter
  in the file: it never falls back to the whole pool, because falling back
  would hand the scene to the Role it was kept from. An unflagged bullet is
  neutral and reachable by everyone, which is what some 157 of these are —
  keep it that way unless the scene puts the subject _doing_ the job rather
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
  item above. **Headgear** bullets may carry `|| mil` in the same sense, for the
  few that are part of an issued uniform — a peaked officer's cap — and the
  split drops them for a civilian Role the same way. **Gear** and **Weapon**
  bullets may also carry `|| mil`, marking
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
  all deliberately unflagged **for `hardtech`**: those are what a kimono
  _should_ reach, and a kabuto above one is the point rather than an
  oversight. Many of them do carry `crown`, which is a different question
  entirely — see that flag below. Two boundaries
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
- **Headgear** bullets may also carry `|| crown`, marking something that sits
  ON TOP of the skull without enclosing it — a wide brim, a tall or ceremonial
  hat, a cap of any kind, a rig clamped over the crown. It is the softer half
  of a pair with `helmet`, and the two divide the head into three registers:

  | Flag     | What it says                | What it drops                             |
  | -------- | --------------------------- | ----------------------------------------- |
  | `helmet` | the head is inside it       | `updo` Hair **and** carried `helmet` Gear |
  | `crown`  | it rests on top of the head | `updo` Hair only                          |
  | neither  | it leaves the crown free    | nothing                                   |

  That middle row is the whole reason this is a separate flag rather than
  `helmet` on the hats. A sedge hat has no quarrel with a flight helmet
  carried under one arm, and reusing `helmet` would have confiscated it.

  `crown` is a claim about **volume**, `hardtech` one about **register**, and
  they are orthogonal: a cybernetic headpiece clamped over the crown is
  honestly both, and carries both. What must never happen is a woven,
  lacquered or straw hat picking up `hardtech` — `notac` drops that register,
  and those hats are precisely what a kimono should reach.

  Flag what a topknot cannot fit under. A brow visor, a headset, an earpiece,
  an ear implant and goggles pushed up onto the forehead all leave the top of
  the head free and stay unflagged; so does a hood, which has slack enough to
  go over gathered hair.

- **Hair** bullets may carry `|| updo`, marking a cut whose mass sits on top
  of the skull — a topknot, a high ponytail, twin space buns, a bun crowned
  with a pin or a flower. Those are dropped whenever the Headgear roll came up
  `helmet` or `crown`, so nothing renders a bun growing through a flight
  helmet or a straw brim. Headgear
  is what yields on a fresh roll, since Hair is drawn first; the filter runs
  both ways, so a pinned or `--set-trait` hat or helmet drops the `updo` cuts
  from the Hair pool instead. Forcing both by hand is honoured rather than
  refused, the same way two helmets are.
  It is gated on `helmet` and `crown` rather than on `hardtech` for the reason
  the flag above gives: a headset, a brow visor or an ear implant leaves the
  crown free, and a topknot above one is fine. Flag only what stands proud of
  the skull — hair
  merely _pinned up off the collar_, a braid crown pinned close to the head, a
  low bun, a bob or anything cropped all lie flat, and those are exactly the
  cuts a helmet goes on over.
- **Hair** bullets may also carry `|| covered`, marking a cut that names
  something _worn_ as part of the phrase — a wrapped headscarf, a ponytail
  pulled through the back of a cap, ponytails held by a headset band. The
  bullet has already put an object on the head, so the Headgear pool is cut to
  the one bullet flagged `bare` and the NPC comes out bare-headed; anything
  else would describe two coverings in the same place.
  The headgear _clause_ then drops out of the prompt entirely, rather than
  printing the bare bullet's own sentence. "A wrapped headscarf ..." and "She
  is bare-headed." in one prompt contradict each other as flatly as the hat
  did, and a render told both does not get to pick the sensible one. The hair
  phrase is the headgear for these bullets, so the clause is what gives way —
  in the portrait, the token and the 3D back view alike.
  This is a strictly harder filter than `updo`, and gated wider on purpose.
  `updo` drops only `helmet` and hands back sixty other bullets, because a
  bun and a brow visor coexist; `covered` has nothing to hand back, because a
  headscarf leaves no room for a hairband either. It is still not a _lock_ —
  a file with no `bare` bullet gets the whole pool rather than an empty roll.
  Like `updo` the filter runs both ways: a pinned or `--set-trait` Headgear
  that is not `bare` drops the `covered` cuts from the Hair pool instead, and
  forcing both by hand is honoured rather than refused.
  Flag only a thing genuinely _worn_. Hair ornaments are not: a clip, a
  ribbon, an ornamental pin, a flower or a mechanical binder is part of the
  hairstyle and leaves the head free for a hat.
- The single **Headgear** bullet that leaves the head bare carries `|| bare`,
  which is what `covered` filters down to. It is a marker rather than a
  preference — nothing is dropped _for_ it — and it exists for the same
  reason `none` does on Weapon: a filter needs to be able to name the empty
  bullet without matching on its prose. Exactly one bullet should carry it.
- A **Gear** or **Headgear** bullet may carry a **role lock**: `admin` on
  Gear, `outlaw` on Headgear. It confines that bullet to the occupations named
  against the flag in `ROLE_LOCKS` in `generate-npc.py` — `admin` is a colonial
  administrator's and no one else's, `outlaw` belongs to the pirates, smugglers
  and other criminal Roles — and it is the one hard filter in this file. Every other
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

One table below is never rolled by `generate-npc.py` at all: `## Animation`,
just above the Prompt templates. Its bullets are whole positive prompts for
`animate-portrait.py`, which turns a finished portrait into a looping
animation, and they reach that script two ways — `animate-portrait.py --roll`
draws one at random, and the import GUI's NPC page offers the list on its
Animated portrait panel. Nothing in the two image prompts reads it, so a
bullet there changes no portrait or token.

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
- Allegra
- Anwen
- Briony
- Celeste
- Dahlia
- Elora
- Elodie
- Felicity
- Giselle
- Hannelore
- Inara
- Kamila
- Leona
- Mirabelle
- Niamh
- Odessa
- Ophelia
- Raina
- Solene
- Wren
- Zaria
- Azura
- Bellatrix
- Brielle
- Celesse
- Danika
- Edda
- Elysia
- Faelara
- Fenn
- Gaelle
- Halona
- Ilyssa
- Isolde
- Jora
- Kairi
- Kira
- Lysandra
- Lysia
- Maris
- Mirelle
- Naava
- Nyela
- Nyx
- Orelia
- Peri
- Qadira
- Quessa
- Rivenna
- Sage
- Salome
- Seraphine
- Sora
- Tindra
- Trissa
- Ursala
- Valina
- Xyla
- Yelena
- Zuri

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
- Alaric
- Ambrose
- Bastian
- Cassiel
- Cedric
- Dorian
- Elian
- Finlay
- Gideon
- Halden
- Jalen
- Konrad
- Leif
- Magnus
- Nabil
- Oren
- Paxton
- Rowan
- Silvan
- Zev
- Zane
- Ashen
- Bastion
- Beren
- Brann
- Caius
- Creed
- Daxen
- Draven
- Eamon
- Fane
- Galen
- Halik
- Ivo
- Jethro
- Jovian
- Kairo
- Lioran
- Nestor
- Nash
- Nyron
- Orion
- Pax
- Quade
- Rafe
- Ronan
- Sagan
- Thane
- Talon
- Torin
- Tiber
- Ulric
- Vance
- Varek
- Wolfe
- Xander
- Yorik
- Zephyr
- Zorren

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
- Abernathy
- Bellamy
- Carrow
- Donnelly
- Eberhardt
- Fenwick
- Garrick
- Hawthorne
- Ingram
- Kingsley
- Lennox
- Marlowe
- North
- Pemberton
- Quinlan
- Sheffield
- Sutherland
- Thatcher
- Ullman
- Whitaker
- Yorick
- Ashcroft
- Blackthorne
- Blackwell
- Braxton
- Caradoc
- Coldridge
- Crowley
- Darkmoor
- Eldridge
- Everly
- Faraday
- Galloway
- Halford
- Harken
- Hightower
- Ironwall
- Langford
- Larkspur
- Ledger
- Marrow
- Nightshade
- Northcliff
- Oakhurst
- Peregrine
- Quell
- Ravenshaw
- Rookwood
- Saltzman
- Stryker
- Stormvale
- Thornfield
- Thornley
- Valente
- Warden
- Wycliffe
- Yarrow
- Zeller
- Kurogane

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
- long-armed and rawboned, heavy through the hands and sloping shoulders like a street brawler
- massively built and heavily muscled, thick through the neck, shoulders and arms like a heavyweight fighter
- barrel-chested and thick through the neck and forearms, gone a little soft at the middle
- square-shouldered and densely muscled through the back, with a swimmer's long taper
- massively built, broad as a doorway across the shoulders and slabbed with heavy muscle

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
- voluptuous and long-limbed, full through the bust and hips above a sharply cinched waist || figure
- athletic and powerfully built through the thighs and hips, full-busted and hard-muscled || figure
- long-legged and lean-waisted, powerful through the thighs and hips || figure
- hourglass-shaped and strong-legged, full through the bust and hips with a sharply narrow waist || figure
- powerfully muscled and deep-chested, with thick corded forearms and a heavy neck
- massively built and heavily muscled, thick through the neck, shoulders and arms like a heavyweight fighter
- tall and willowy, long in the back and legs with softly full hips || figure
- leggy and full-hipped, long strong thighs beneath a narrow waist || figure
- a full-busted, narrow-waisted frame with broad, powerful shoulders || figure
- a lean, athletic build with a flat stomach and toned, defined limbs
- a curvaceous frame with a narrow waist and full, rounded hips || figure
- a lean, athletic frame with a nipped waist and softly curved hips || figure
- a lean, wide-hipped figure with strong, squared shoulders || figure
- statuesque, squared shoulders over a narrow waist || figure

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
- a wild, uncombed shock of {colour} hair standing up in stiff tufts
- shoulder-length {colour} hair
- a slicked-back {colour} high bun with loose front strands framing the face || updo
- a voluminous, loosely curled {colour} mane with soft bangs framing the face || 
- a sleek side-parted {colour} updo with a shaved undercut line above one ear || updo
- a short, tousled bob of {colour} hair falling loose around the jaw
- a {colour} shoulder-length wavy bob with long side-swept bangs
- shoulder-length {colour} hair swept back from a center part, one side tucked behind a small plug earring
- a sleek {colour} bob with blunt-cut bangs skimming the brow
- cascading {colour} micro braids gathered loosely over one shoulder
- a sleek high {colour} ponytail, a slim clip pinned above one temple || updo
- shaggy {colour} hair falling in heavy spikes across the brow, the back left ragged at the collar
- long ragged {colour} bangs hanging in sharp points between the eyes, the rest falling loose past the collar
- shaggy {colour} hair falling in heavy layered bangs over the brow and the tops of the ears
- thick spiky {colour} hair standing up in stiff points, a few heavy strands dropping across the brow
- untamed {colour} hair swept straight back from a high forehead, springing loose and wild at the sides
- long {colour} hair swept close back from the forehead into a thick braid falling over one shoulder
- long {colour} hair swept in a loose side part, several thin braids threaded among the flowing waves
- long {colour} hair gathered into two high ponytails that fan outward in loose strands || updo
- tousled {colour} hair falling in uneven chin-length locks, parted loosely with narrow strands across the brow

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
- twin high {colour} pigtails swept up into voluminous coils at the crown || updo
- {colour} hair gathered into twin high buns, loose strands drifting weightless around the face || updo
- {colour} hair gathered into twin high buns, loose strands falling around the face || updo
- twin thin braids drawn back from the temples into loose {colour} waves
- {colour} hair swept high into a knotted bun, a few loose strands framing the face || updo
- a high {colour} ponytail whipped into wild wind-streaked strands, a heavy fringe across the brow || updo
- long {colour} hair in a low loose side braid, blunt bangs and fine strands framing the cheeks
- twin high {colour} pigtails bound with a pair of glowing hair ties, wind-blown loose across the shoulders || updo
- long, straight {colour} hair falling past the waist
- long, loosely waved {colour} hair swept over one shoulder

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
- a messy {colour} topknot with spiked bangs falling loose, a feather charm bound into the tie || updo

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
- pale icy blue
- black || fading to red at the tips
- dark brown || fading to sun-bleached orange at the tips
- obsidian black || fading to cobalt blue at the roots
- deep umber || fading to olive-green at the tips
- gunmetal silver || fading to violet at the tips
- dark mahogany || melting to steel blue at the roots
- burnt sienna || fading to matte copper at the ends
- slate indigo || shading to pale chartreuse at the hairline
- charcoal olive || fading to icy violet at the ends
- black ink || fading to emerald green in the lowlight strands
- dusty lilac-black || with electric violet at the crown
- muted amethyst || fading to dark cyan at the temples

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
- a small red glyph decal stamped high on one cheekbone
- both hands replaced by articulated gold-plated mechanical prosthetics
- intricate tattoos tracing {possessive} shoulders and arms that seem to glow faintly beneath the skin || @cyberpunk
- a jagged scar crossing {possessive} cheek and eye that seems to glow faintly along its edges || @grimdark
- one arm replaced by a segmented mechanical prosthetic, ringed joint bands visible from the wrist to the shoulder || @cyberpunk
- a cluster of cybernetic jack ports lining the side of the neck, thin cables trailing from a glowing circular interface node at the temple || @cyberpunk
- fine mechanical seams tracing along the jaw and cheek, marking {object} as heavily cybernetic || @cyberpunk
- one entire arm and shoulder replaced by a gleaming articulated cybernetic frame, matte white plating exposed at the joints || @cyberpunk
- a segmented mechanical collar studded with cable jacks and status lights climbing to the jaw || @cyberpunk
- a segmented data-jack port set into the back of {possessive} neck
- a fully mechanical forearm and hand, a thin glowing seam running along the wrist || @cyberpunk
- fine glowing circuitry lines tracing across half of {possessive} face || @cyberpunk
- a circular audio implant set flush at {possessive} temple
- a glowing data-port set into the side of {possessive} neck || @cyberpunk
- a glowing collar-like implant encircling {possessive} throat || @cyberpunk
- a thin glowing ring-shaped band encircling {possessive} wrist, worn where a bracelet would sit || @cyberpunk
- twin camera-lens optical implants set where {possessive} eyes should be, each aperture glowing faintly || @cyberpunk
- a mechanical shoulder joint exposed at the back, plating peeled back to show the housing beneath
- chrome prosthetic legs from the knee down, articulated joints visible at the ankle and knee || @cyberpunk
- a fully articulated prosthetic arm from the shoulder down, its plating visible where the sleeve rides up
- a partially mechanical jaw and cheek plate
- a pair of digitigrade cybernetic legs replacing both from the knee down, jointed like a machine's || @cyberpunk
- an entirely synthetic exoskeletal body, every joint and panel line visible where clothing gaps open || @cyberpunk
- a thin glowing tear-line traced beneath one eye, like a permanent readout mark
- a thin glowing circuit-line implant tracing from the shoulder down the upper arm
- a fully robotic head unit with a glowing optic band across the eyes || @cyberpunk
- a circular optical sensor patch worn over one eye like a mechanical eyepatch
- fine circuit-line tracery running across one whole side of the face and down the neck
- an armored torso plate exposed where a shirt has torn away at the ribs
- an exposed mechanical spine with cabling and joint housings running the length of the lower back || @cyberpunk
- twin recessed power-core lights set into the chest, glowing faintly
- a raised cybernetic ridge implant running from the crown of the head down the back of the neck, jointed like a spine || @cyberpunk
- a row of small metal sutures closing a fresh laceration across one cheek, faint dried blood at the jaw
- a fine glowing sigil etched at the brow || @cyberpunk
- a spread of glowing tribal-patterned markings tracing one side of the face and down the neck || @cyberpunk
- a branching network of glowing markings tracing up the bare back and throat, faint beneath the skin || @cyberpunk
- a fully articulated cybernetic hand and forearm plated in glossy black, a circuit-like pattern etched along every joint || @cyberpunk
- a mechanical prosthetic forearm and hand, articulated steel plating replacing one arm from the elbow down
- glowing tribal markings tracing both arms and down the chest, faintly pulsing beneath the skin || @grimdark
- glowing rune-like markings tracing the spine and both arms || @neogothic
- a cybernetic jaw and throat brace of jointed gold plating fused seamlessly into the skin at the neck || @cyberpunk
- all four limbs replaced with oversized plated cybernetic prosthetics, heavy segmented armor casings with brass caps at every joint, far bulkier than the body they are fitted to
- an exposed mechanical neck of segmented vertebrae and fine cabling running from the jaw down to the collarbone
- a cybernetic optic socketed into the brow above one eye, its concentric lens ringed by exposed gears and plating
- a skeletal mechanical hand of bare jointed metal fingers, left without any casing over the frame
- an adhesive bandage stuck crooked across the bridge of the nose
- a small pale inverted-triangle marking beneath one eye
- dense luminous floral filigree tattooed across both shoulders and down the arms || @cyberpunk
- a mechanical hand with exposed finger hinges, narrow cable tendons and round fasteners across the palm
- one prosthetic arm stripped to a narrow exposed metal framework, articulated finger links and open gaps between the upper-arm struts
- fine geometric panel seams framing both cheeks and continuing into an articulated synthetic neck || @cyberpunk
- an exposed mechanical neck with paired piston-like tendons and a circular connector seated below each ear
- several small metallic studs tracing the exposed rim of one ear
- a rectangular barcode tattoo high on one upper arm with several short parallel lines beneath it
- a circular connector seated behind one ear with several exposed cable strands descending along the side of the neck
- pale synthetic neck plates separated by narrow dark channels, tiny fasteners and layered tendons visible beneath the ear
- a stitched scar crossing the cheek beneath one eye, with short vertical marks along its length
- dense curling luminous tattoos covering the exposed neck and cheek || @cyberpunk
- branching luminous circuit tattoos spreading across the bare upper back and neck || @cyberpunk
- symmetrical luminous scrollwork tattoos running from the collarbones across the shoulders and down both arms
- an exposed mechanical cheek panel with tiny illuminated circuits, slender neck pistons and flowers tucked among the cables || @cyberpunk
- fine branching ornamental tattoos crossing one cheek and continuing down the side of the neck
- dense luminous angular glyph tattoos covering the upper back, neck and both arms
- a scuffed leather eyepatch strapped over one eye

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
- one arm a heavy tan-plated cybernetic prosthetic with exposed pistons and a shoulder harness bracing it in place || @cyberpunk
- old bruising along both forearms, half-hidden under grubby tape
- a thin trail of dried blood tracked from beneath one eye down the cheek
- a sleeve of dark floral and skull tattoo work down one forearm, small charm-style ink dotting the other hand's knuckles
- a half-mechanical face and shoulder where flesh gives way to exposed servos and plating
- a cybernetic implant fused along the jaw and ear, seams of metal showing beneath the skin
- a barcode tattoo inked across {possessive} bare shoulder
- a pair of articulated mechanical wings grafted to {possessive} back, servos exposed at the joints
- a segmented cybernetic hand ending in sharp, claw-like fingertips
- visible mechanical seams at the jaw and neck where synthetic plating meets skin
- a cybernetic faceplate sheathing one side of the face, circuitry glowing faintly beneath the cheek, thin cabling threading back to the ear || @cyberpunk
- a slender triangular pendant earring catching light at one ear
- long gold drop earrings worn with a matching cuffed choker at the throat

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
- {Subject} {wear} a soft crew cap pushed back on {possessive} head. || crown
- {Subject} {wear} a padded pilot skullcap with the visor unclipped and folded back. || hardtech crown
- {Subject} {wear} a rolled bandana tied across {possessive} brow.
- {Subject} {wear} a knitted watch cap pulled down to the eyebrows. || crown
- {Subject} {wear} a composite ballistic helmet with its rail-mounted visor hinged up. || hardtech helmet
- {Subject} {wear} a full flight helmet in scuffed pale grey-white, a tinted visor panel down over the eyes and a small lit accent lens at the temple, a thin tether cable trailing from the back. || hardtech helmet
- {Subject} {wear} a monocular sensor rig strapped over one eye, its lens faintly lit. || hardtech
- {Subject} {wear} heavy ear defenders slung around {possessive} neck rather than on {possessive} head. || hardtech
- {Subject} {wear} a welding visor tipped back on top of {possessive} head. || hardtech crown
- {Subject} {wear} a worn ushanka-style fur hat with the flaps down, a faded unit star pinned to the front. || crown
- {Subject} {wear} a tactical cap with a small circular unit emblem, dark sunglasses beneath it. || hardtech crown
- {Subject} {wear} a night-vision helmet with the quad tubes flipped up clear of {possessive} eyes. || hardtech helmet
- {Subject} {wear} a sleek black mechanical headset piece mounted flush against one ear. || hardtech
- {Subject} {wear} a stiff peaked officer's cap, the brim polished and a small insignia set at the crown. || crown mil
- {Subject} {wear} a hooded shroud drawn up over a full-face helmet, its visor tinted dark and a breather mask sealed across the lower face. || hardtech helmet
- {Subject} {wear} a deep hood drawn up, a pair of goggles clipped across the brow of it.
- {Subject} {wear} a flat-brimmed ball cap with a small stitched patch at the front. || crown
- {Subject} {wear} an open-face crash helmet with the visor swung up clear of {possessive} eyes. || hardtech helmet
- {Subject} {wear} a ballistic helmet with its visor tipped up and a black breather mask sealed over the lower face. || hardtech helmet
- {Subject} {wear} a russet leather flight cap with ear flaps and a monocular scanner lens fixed down over one eye. || hardtech crown
- {Subject} {wear} a wide woven sedge hat, its brim throwing {possessive} face into shadow. || crown
- {Subject} {wear} a pale cloth wrapped loosely over the lower face beneath a wide straw hat. || crown
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
- {Subject} {wear} a segmented white cybernetic headpiece clamped over the crown and one temple, faint cable jacks seated at the jaw. || hardtech crown
- {Subject} {wear} a sealed tactical helmet with a smoked visor and an integrated breather mask, a coiled comms cable trailing from the jaw. || hardtech helmet
- {Subject} {wear} a smooth blue-visored full-face helmet with a hood drawn up over it, a scarf wound loose at the throat. || hardtech helmet
- {Subject} {wear} a flat wide-brimmed lacquered hat crowned with a bird skull and trailing feathers, the brim throwing {possessive} face into shadow. || crown
- {Subject} {wear} a bulky mechanical diagnostic rig clamped over the crown of {possessive} head, thick cabling trailing down to jacks at the collar, a status light lit at the side. || hardtech crown
- {Subject} {wear} a sleek angular powered helmet with raised sensor fins and a full dark visor down, a single braid of hair falling free beneath it. || hardtech helmet
- {Subject} {wear} thin rectangular glasses framing sharp eyes.
- {Subject} {wear} a sleek mechanical half-mask sealed over the nose and mouth, a small lens node mounted at the temple. || hardtech
- {Subject} {wear} a close-fitted respirator mask across the lower face beneath narrow tactical eyewear. || hardtech
- {Subject} {wear} a horned kabuto-style helmet with a trailing neck guard, its crest catching the last light. || helmet
- {Subject} {wear} a wide flat lacquered hat rimmed in gold, a single red tassel hanging from the brim. || crown
- {Subject} {wear} a horned kabuto helmet with a scowling mempo faceplate, eyes lit with a faint red glow. || helmet
- {Subject} {wear} a wide woven hat trimmed with small curved horns and hanging tassels, a segmented mechanical mask sealed over the nose and mouth beneath it, a faint accent light glowing at the seam. || crown
- {Subject} {wear} a wide straw hat trimmed with small hanging bells and a tattered red ribbon at the crown, rain streaming off the brim. || crown
- {Subject} {wear} a broad ceremonial hat strung with hanging tasseled bells, an antler-like crest rising from the crown. || crown
<!-- - {Subject} {wear} a broad woven hat bristling with jagged spikes at the crown, its brim battered and weathered. || crown -->
- {Subject} {wear} a broad dark hat trimmed with hanging chain ornaments and a feather crest, the brim shadowing {possessive} eyes. || crown
- {Subject} {wear} a wide straw hat over a patterned cloth headband tied at the brow. || crown
- {Subject} {wear} a horned kabuto-style helmet with a riveted neck guard and cheek plates framing {possessive} face. || helmet
- {Subject} {wear} a gilt-trimmed tricorn hat pinned with a skull-and-crossbones badge and a curling plume. || crown
- {Subject} {wear} a black tricorn hat trimmed in lace, a small skull-and-crossbones pinned above a red ribbon bow. || crown outlaw
- {Subject} {wear} a red bandana knotted at the brow, ends trailing into windblown hair.
- {Subject} {wear} a pair of oversized over-ear headphones with a boom mic curling toward {possessive} cheek. || hardtech
- {Subject} {wear} a matte combat helmet cinched down over a full rebreather mask, hoses looping to a chest-mounted filter. || hardtech helmet
- {Subject} {wear} a deep hood drawn low over {possessive} brow, shadowing {possessive} face down to the nose.
- {Subject} {wear} heavy over-ear headphones with a glowing status ring on each cup. || hardtech
- {Subject} {wear} a fin-eared tactical helmet with a mirrored visor. || hardtech helmet @cyberpunk
- {Subject} {wear} a streamlined flight helmet with cable ports ringing the crown, the visor cracked open to show eyes lit faintly beneath. || hardtech helmet @gundam
- {Subject} {wear} brass-rimmed welding goggles pushed low over a heavy over-ear headset, a cable trailing to a shoulder pack. || hardtech
- {Subject} {wear} a chrome respirator mask fitted along {possessive} jaw, a single lens glowing over one eye. || hardtech @cyberpunk
- {Subject} {wear} a pair of scuffed brass-and-leather over-ear headphones with an exposed pivot joint. || hardtech
- {Subject} {wear} a smooth black full-face combat helmet, a single narrow visor slit burning across the eyes. || hardtech helmet
- {Subject} {wear} a black balaclava printed with a pale grinning skull across the face.
- {Subject} {wear} clear wraparound safety glasses. || hardtech
- {Subject} {wear} a sleek sealed helmet with a glowing visor band and armored jaw vents, twin comms nodes at the temple. || hardtech helmet @gundam
- {Subject} {wear} a clear bubble-domed pressure helmet with a padded collar ring. || hardtech helmet
- {Subject} {wear} tinted rectangular glasses fused to a slim over-ear headset with a boom mic curling to the jaw. || hardtech
- {Subject} {wear} rounded welding goggles pushed up onto {possessive} forehead, a padded headband tracking back through {possessive} hair.
- {Subject} {wear} a small horn-shaped antenna clip fixed above one ear, a thin cable trailing into {possessive} hair. || hardtech
- {Subject} {wear} an open half-helmet with an armored jaw and cheek plates, thick cabling trailing from the crown down to {possessive} collar. || hardtech helmet @gundam
- {Subject} {wear} a heavy over-ear cybernetic headset with a glowing digital readout on the cup, thin cables threading down into {possessive} collar. || hardtech @cyberpunk
- {Subject} {wear} a bulky over-ear headset with twin raised antenna prongs and a glowing digital readout on the cup. || hardtech
- {Subject} {wear} an oversized angular helmet tipped back off {possessive} face, a single optic lens glowing beside the visor and a stencilled numeral across the crown. || hardtech helmet @cyberpunk
- {Subject} {wear} a sleek over-ear headset with a lit ring on each cup, its band merging into cabling that disappears down the back of {possessive} neck. || hardtech
- {Subject} {wear} a heavy head-harness clamped down over the crown, vents and cabling ringing the band. || hardtech crown
- {Subject} {wear} a full-face sensor visor that conceals the features entirely, a cross-shaped optic band glowing across the eyes. || hardtech helmet
- {Subject} {wear} a ragged black hood shadowing a bone-white skull mask crowned with branching antlers, twin points of light burning in the eye sockets. || @grimdark
- {Subject} {wear} a sealed helmet with curved cat-like ear flares and a rounded transparent visor. || hardtech helmet
- {Subject} {wear} a tall spiked black crown catching the last light. || crown @grimdark
- {Subject} {wear} a gilded segmented helmet with an ornate brow guard, swirling filigree engraved along the crown. || helmet @neogothic
- {Subject} {wear} an angular powered combat helmet with twin lensed optics glowing beneath the brow and a stub antenna trailing from the crown. || hardtech helmet
- {Subject} {wear} a woven headband holding {possessive} hair back from the brow.
- {Subject} {wear} a pair of tinted flight goggles pushed up onto {possessive} forehead, paired with a compact headset over one ear. || hardtech
- {Subject} {wear} a sealed tactical helmet with a slit visor and integrated comms. || hardtech helmet
- {Subject} {wear} an armored cybernetic plate capping the skull and wrapping down over one eye, a single round optic lit in its socket. || hardtech crown
- {Subject} {wear} a fitted leather flight cap with tinted goggles pushed up onto {possessive} forehead, gem-studded straps buckled at the temple. || crown
- {Subject} {wear} a scuffed yellow hard hat with a headlamp clipped to the brim, a half-face respirator strapped beneath it. || hardtech helmet
- {Subject} {wear} a wide metal-plated visor band that conceals both eyes, fused to jacks at the temple. || hardtech @cyberpunk
- {Subject} {wear} a compact angular earpiece hooked behind one ear, a small lit panel set into its casing. || hardtech
- {Subject} {wear} a sleek angular helmet with a reinforced jaw vent and a glowing sensor strip across the brow. || hardtech helmet
- {Subject} {wear} an angular full-face helmet with narrow glowing visor slits and raised sensor fins. || hardtech helmet
- {Subject} {wear} a sealed dark full-face helmet fused with a respirator mask, faint light glowing through narrow visor slits. || hardtech helmet
- {Subject} {wear} a sleek angular tactical helmet with a lit HUD visor and a short comms stalk curving to the jaw. || hardtech helmet
- {Subject} {wear} a sealed, faceless combat helmet, a single thin visor slit glowing across the brow above a ribbed respirator grille. || hardtech helmet
- {Subject} {wear} a smooth crested combat helmet sealed fully over the face, a thin lit visor strip glowing across the front. || hardtech helmet
- {Subject} {wear} a sleek angular full-face helmet with a raked crest and a single glowing lens node at the temple, twin vents flaring at the jaw. || hardtech helmet
- {Subject} {wear} a sharp angular full-face helmet with a peaked crest and a dark tinted visor, twin cable ports at the jaw. || hardtech helmet
- {Subject} {wear} a full sealed helmet with a smooth featureless visor and glowing seam lines along the jaw, a raised armored collar sealing it to the suit. || hardtech helmet @cyberpunk
- {Subject} {wear} a sleek featureless powered helmet with a single glowing optic and an integrated collar piece. || hardtech helmet
- {Subject} {wear} a smooth-shelled helmet with a narrow glowing visor slit and integrated jaw comms. || hardtech helmet
- {Subject} {wear} a compact targeting visor clipped over one eye, its lens glowing faintly. || hardtech
- {Subject} {wear} a pale monastic hood drawn close around {possessive} face, its hem scorched black at the edges.
- {Subject} {wear} a pair of over-ear headphones wired directly into a data port at {possessive} jaw. || hardtech @cyberpunk
- {Subject} {wear} an ornate winged helm with feathered wing shapes rising from the temples, a slim decorative faceguard framing the eyes. || helmet
- {Subject} {wear} a segmented tactical rebreather mask wired into a paired over-ear headset, a coiled cable trailing from one side. || hardtech
- {Subject} {wear} an ornate segmented respirator mask fused with a paired headset, faint lit studs tracing its plates. || hardtech
- {Subject} {wear} a bulbous glass-domed pressure helmet, cable ports and toggle switches studding the suit's collar rig below the seal. || hardtech helmet
- {Subject} {wear} a full black AR visor with a glowing circuit-pattern across the lenses, twin curling horn-like antenna prongs rising from the band. || hardtech @cyberpunk
- {Subject} {wear} a scavenged full-face respirator with round goggle lenses and a scuffed brass filter canister at the jaw. || hardtech @scav
- {Subject} {wear} a scarred horned helm, twin curling horns sweeping back above a narrow slit visor. || helmet @grimdark
- {Subject} {wear} a scarred half-helmet fused to a sealed respirator mask, a bulky comms module clamped over one ear with a lens glowing faintly at its center, a thin antenna trailing up from the crown. || hardtech helmet
- {Subject} {wear} a wide woven sedge hat over a masked face lit with two glowing eye-lenses. || crown @neosamurai
- {Subject} {wear} a stiff peaked officer's cap crested with a winged skull badge, a tasseled band circling the brim. || crown mil
- {Subject} {wear} a tall gilded ceremonial helmet with a spiked finial and dangling ear guards, its crest catching the light. || helmet
- {Subject} {wear} a crystalline crown of interlocking translucent spires. || crown @neogothic
- {Subject} {wear} a sleek segmented flight helmet, its visor lit from within by scrolling telemetry and a slim horizontal display strip across the brow. || hardtech helmet @gundam
- {Subject} {wear} a segmented white plated helmet closed tight over the face, narrow eye slits lit faintly and a stencilled unit designation across the brow. || hardtech helmet @gundam
- {Subject} {wear} a sealed angular helmet with a stepped brow plate and a narrow illuminated grille across the lower face. || hardtech helmet
- {Subject} {wear} a smooth enclosed helmet with an elongated central faceplate and recessed side vents. || hardtech helmet
- {Subject} {wear} a faceted full-face pressure helmet with a broad tinted visor, ribbed jaw hoses and a heavy padded neck seal. || hardtech helmet
- {Subject} {wear} large circular headphones with exposed radial supports and a coiled cable running down beside the collar. || hardtech
- {Subject} {wear} an open-face pale composite helmet with pointed sensor fins, exposed mechanisms at the ear and a lit circular side lens. || hardtech helmet @cyberpunk
- {Subject} {wear} a soft flat-topped crew cap with short folded sides and a narrow contrasting band. || crown
- {Subject} {wear} a broad padded over-ear flight headset with a thick upper band and a short hanging cable. || hardtech
- {Subject} {wear} a broad rectangular visor over the eyes with a circular temple module and a thin support strap around the head. || hardtech
- {Subject} {wear} a narrow wraparound visor beneath a swept-back crest of sharp mechanical fins. || hardtech crown @cyberpunk
- {Subject} {wear} a heavy rectangular binocular visor protruding from a battered helmet, long cables hanging from its side housings to the collar. || hardtech helmet
- {Subject} {wear} an open-faced angular helmet with an extended brow ridge, a luminous strip along the visor edge and exposed jaw-side fittings. || hardtech helmet
- {Subject} {wear} a ragged hood over an antlered mask with tiny glowing eye apertures. || @grimdark
- {Subject} {wear} a dark ceremonial helmet with tall swept-back hornlike wings framing the face. || helmet @neogothic
- {Subject} {wear} an open-faced pressure helmet with two triangular ear-like fins and oversized circular ear housings. || hardtech helmet
- {Subject} {wear} a compact ribbed respirator covering the nose and mouth, strapped into circular ear fittings. || hardtech
- {Subject} {wear} an ornate dark face veil hung with fine chains beneath a thin illuminated halo frame. || crown @neogothic
- {Subject} {wear} a sharply ridged composite helmet with a narrow dark faceplate and split armored jaw guards. || hardtech helmet
- {Subject} {wear} a pale open-faced exploration helmet with round ear housings and a thick ribbed pressure collar. || hardtech helmet
- {Subject} {wear} a horned composite helmet with a broad luminous visor and a patterned scarf wrapped below the jaw. || hardtech helmet @cyberpunk @neosamurai
- {Subject} {wear} a swept-back angular helmet with a deep black V-shaped visor and layered jaw plates. || hardtech helmet
- {Subject} {wear} a broad rectangular gold visor across the eyes, small fasteners and a rigid temple mount visible at its edges. || hardtech
- {Subject} {wear} a battered full-face respirator with round glass eyepieces and mismatched filter canisters. || hardtech
- {Subject} {wear} a sealed angular tactical helmet with paired circular illuminated lenses and a short side antenna. || hardtech helmet
- {Subject} {wear} a scarred helmet with a clear face shield, a large circular ear module and a paired-filter breathing mask. || hardtech helmet
- {Subject} {wear} a lacquered kabuto helmet with curved crescent horns at the brow and a hinged face guard framing {possessive} cheeks.
- {Subject} {wear} a horned kabuto helmet with twin sweeping crescent horns rising from the brow.

## Headgear (she) +

- x2 {Subject} {wear} a slim hairband holding the hair back off {possessive} face.
- {Subject} {wear} a wide fabric band knotted at the back of {possessive} head, hair gathered behind it.
- {Subject} {wear} a slim glowing accent band swept back through {possessive} hair like a hairband.
- {Subject} {wear} a wide woven hat, thin red-framed glasses catching the light and a long-stemmed pipe held between {possessive} lips. || crown
- {Subject} {wear} a wide-brimmed felt hat canted low over one eye, a long feather trailing from the band.
- {Subject} {wear} a boxy black over-ear headset, foam pads pressed into loose waves of hair. || hardtech
- {Subject} {wear} a heavy augmented-reality visor rig bolted over one eye, circuitry glowing along its housing. || hardtech @cyberpunk
- {Subject} {wear} a heavy over-ear industrial headset wired down to a banded choker collar. || hardtech
- {Subject} {wear} a fused sensor-and-camera housing in place of a face, cabling snaking down into {possessive} collar. || hardtech helmet @cyberpunk
- {Subject} {wear} a compact audio rig mounted flush behind one ear, a thin cable trailing to {possessive} collar. || hardtech
- {Subject} {wear} an angular visor rig flipped up on its hinge, inner display still glowing faintly. || hardtech
- {Subject} {wear} a tactical visor pushed up onto the forehead. || hardtech @tactical
- {Subject} {wear} a bubble-domed EVA helmet with its tinted sun-visor flipped up, sensor pads and comms studding the collar ring. || hardtech helmet

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
- a teeth-bared snarl of pure fury, eyes wide and fixed
- a wide-eyed, open-mouthed look of raw panic
- a wide-eyed, slack-jawed look of dawning horror
- a serene, half-lidded expression with parted lips
- a sharp, wary glance thrown back over one shoulder
- a sly, half-lidded smirk
- a broad, warm smile that reaches the eyes
- a hollow, exhausted stare, eyes fixed on middle distance
- a wide-eyed, open-mouthed alarm, jaw dropped mid-shout
- a hard, weary stare, exhaustion pulling at half-lidded eyes
- a wide-eyed, open-mouthed alarm, brows drawn tight in disbelief
- a fierce, teeth-gritted scowl, brows drawn down hard
- a wild, open-mouthed shout, eyes wide and fixed on the viewer
- a cocky, scrappy grin under lowered brows, plainly enjoying the trouble
- a bared-teeth snarl, eyes narrowed to slits beneath the fringe
- a gritted-teeth grimace, eyes cut hard to one side
- a sagging, heavy-lidded fatigue, the mouth pulled down mid-word as if breaking bad news
- a rain-soaked upward stare, brow knotted and jaw slack at something terrible overhead
- a wide-eyed, open-mouthed wail of terror, tears running freely
- a pained grimace through gritted teeth, sweat beading at the brow
- a restful expression with closed eyes and the chin tipped gently upward
- a tight, hostile smile beneath lowered brows

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
- a cold, focused stare, jaw set and ready for a fight
- an intense, storm-lit glare, lips parted around a held breath
- an intense, otherworldly stare, chin lifted in solemn resolve
- a cold, knowing smirk, eyes glinting with quiet menace
- a wide-eyed, inquisitive half-smile, head tilted as if caught mid-thought
- a cool, clinical stare from under a lowered brow, lips pressed flat

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
- a municipal recycler foreman
- a mercenary sniper || mil
- an elite mercenary pilot || mil
- a close-quarters blade specialist || mil
- a deep-core scout pilot || mil
- an orbital interceptor pilot || mil
- a stealth dropship pilot || mil
- a grav-lift fighter pilot || mil
- a courier-liaison pilot || mil
- a jump-troop sergeant || mil
- a voidguard rifleman || mil
- a heavy-armor assault specialist || mil
- a covert strike specialist || mil
- a rapid-response marine || mil
- a reinforced infantryman || mil
- an urban recon scout || mil
- a tactical planning officer || mil
- a civilian trauma counselor
- a public broadcast coordinator
- an orbital traffic coordinator
- a starship systems technician
- a gravitic drive mechanic
- a servo-augmented armorer
- a cybernetic field engineer
- a mech-frame maintenance technician
- a prototype reactor engineer
- a systems biologist
- a lab-bench plasma physicist
- a xenobiology researcher
- a computational materials chemist
- a weapons effects analyst
- a forensic bioinformatics analyst
- a quantum mechanics adjunct
- an exobiology field scientist
- a neurointerface cognitive engineer
- a null-space theoretician
- a gravitic diagnostics physicist
- a frontier magistrate
- a corporate compliance auditor
- a station syndicate clerk
- a neon-market cartographer
- a dockside black-market broker
- a data-rat courier
- a data pirate
- an undercity fixer

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

  '|| unaffiliated' marks the two entries that are NOT an affiliation - the
  ones whose visual is empty because there is nothing to show. It is a marker
  rather than a preference, the same shape 'none' has on Weapon and 'bare' on
  Headgear: nothing is dropped FOR it, and it exists so a filter can name the
  non-affiliations without matching on their prose. Exactly two bullets carry
  it.

  What reads it is UNAFFILIATED_ROLES in generate-npc.py, which names the Role
  bullets whose own words say they work for nobody - "a freelance salvager" is
  the only one so far. Such a Role's Faction pool is cut to these two and
  nothing else, because "a freelance salvager, Affiliation: House Clawthorne"
  is a dossier disagreeing with itself rather than an interesting combination.
  The civ/mil split cannot catch that on its own: it drops House Clawthorne
  from a civilian's pool for being 'mil', and then hands them Smith-Shimano
  Corpro instead. A hard filter like the Gear lock and the Backdrop gates, for
  the same reason - handing the pool back would give the freelancer the
  employer this exists to keep off them.

  The mercenary Roles are deliberately NOT in that set. A mercenary company is
  an affiliation, with a name, a banner and a payroll, so "a mercenary squad
  lead, Ashfall Vanguard" is who pays them rather than a contradiction.

  Keep visuals to about a dozen words. Both prompts run close to Krea 2's
  512-token ceiling - see test/test_prompt_budget.py.
-->

- x2 Unaligned || || civ unaffiliated
- x2 Union Administrative Department || issued and worn thin, in faded institutional blue-grey || mil palette
- Harrison Armory || sharply pressed, high collar and polished fittings, in imperial green and gold || mil palette
- Smith-Shimano Corpro || precisely tailored with fine seam piping, in white and pale pastels || civ palette dressy
- IPS-Northstar || riveted and salt-stained heavy canvas, in rust orange || civ palette
- Karrakin Trade Baronies || heavy brocade and gold braid, an heraldic crest at the shoulder, in deep crimson || palette dressy
- Colonial militia || mismatched surplus, webbing straps and taped-over insignia || mil
- Unregistered || || unaffiliated
- House Clawthorne || a purple rabbit-skull crest banner, tarnished gold trim and dangling bone charms || mil palette
- Forge Household || a quartered crimson-and-black heraldic shield stitched over the breast, tarnished brass fastenings || mil palette
- Redstar Salvage || a red five-point star roundel stitched above the chest zipper, edges frayed and sun-faded || civ palette
- Ashfall Vanguard || a red skull-and-shield roundel stitched high on one shoulder, canvas gone soft with wear || mil palette
- Diamond Line Couriers || a faded orange diamond patch stitched high on one sleeve, canvas worn thin with age || civ palette
- Crimson Meridian Cartel || matte-black suits with violet seams and translucent chest tags || civ palette
- Neon Lotus Network || reflective cyan rainwear over charcoal layers and chrome trim || civ palette
- Kestrel City Couriers || narrow charcoal jackets, orange route stripes, and clipped satchel rigs || civ
- Redline Habitat Union || magenta overalls with olive-grey rope-burned shoulders || civ palette
- Ghostline Ascetics || silver-gray veils and black robes stitched with red prayer threads || civ dressy
- Iron Bastion Legion || tan-black plate coats, red armbands, and rank chevrons || mil palette
- Null-Sector Rangers || black body armor with green visor slits and matte field seams || mil palette
- Void Seraph Guard || white-black ceremonial harnesses over tactical layers, blue polished insignia || mil palette dressy
- Inquisitorial Host || midnight-blue capes, brass shoulder seals, and rigid gauntlet clasps || mil palette dressy
- Ashen Forge Mandate || soot-black work jackets and brown canvas tool belts over simple overalls || civ
- Redstar Covenant || crimson work coats over ivory underlayers and brass shoulder loops || civ palette
- Cinder Gate Customs || burnt-orange docking coats with bronze buckles and permit loops || mil
- Asterion Ascendance || iridescent green coats with gold thread and bead braids || civ palette
- Black Market Choir || cracked leather coats, violet embroidery, and coin-and-gear chains || civ dressy
- Gloom Market Merchants || dark indigo wraps over patched brown waistcoats and rope belts || civ
- Titanfall Veterans Brotherhood || forest-green field greaves, black pauldron wraps, weathered runes || mil palette
- Sable Mechanicus Choir || slate-gray robes, copper tool plates, and data loops || civ
- Dawnglass Priory || pale-blue clerical coats with silver trim and thin black gloves || mil palette dressy
- Kinetica Salvage Trust || heavy blue-grey vests with chain mesh and warning tape || civ
- Orbital Mercy Chapter || white and gold medical tabards over black stress-sleeves || mil palette
- Cerulean Wing Cartel || a pale butterfly roundel stencilled on sun-bleached rust-orange cloth, patched seams and chipped dye || palette
- Driftline Watch || a tan stitched sigil patch high on the sleeve, surplus fabric faded soft with wear || mil

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
- => Flight suits
- => Work coveralls
- => Long coats over fatigues
- a tailored jacket cut close, with a high collar || civ
- an armored vest worn over civilian clothes, its plates visibly mismatched || civ
- => Tank tops
- a hooded utility poncho over a pressure-suit liner
- a quilted thermal jacket over layered underlayers || civ
- a canvas work apron over rolled shirtsleeves || civ
- a pressure-suit undersuit with the armor plates stripped off
- => Leather jackets
- => Combat uniforms and plate carriers
- => Hardsuits and segmented armor
- => Dress uniforms
- a powered load-bearing exo-frame strapped over a combat uniform, actuators tracking the limbs and a status strip lit at the hip || mil
- a fitted black techwear jacket, sleeves lined with small data ports, over a form-fitting undersuit || civ
- => Open jackets over plated or glowing bodysuits
- => Field jackets
- a high-collared black tactical pilot jacket with glowing cable tubing threading down the front || mil
- a long dark coat lined with thin glowing cabling, a spiked collar choker at the throat || civ
- => Unlit tactical bodysuits
- a heavy hooded weatherproof cloak, the hood pulled low and the face half lost in its shadow || civ
- => Glowing-seam bodysuits
- => Caped armor suits
- a faded rescue-crew jumpsuit, its high-visibility panels dulled to grime, a cropped hooded jacket over it and armored greaves strapped over the shins || civ
- an oversized grey hooded jacket with the sleeves hanging long over a high black collar wrap, harness straps crossing the chest, cargo trousers with armored knee panels
- a black hooded field jacket webbed with pull-tabs and cinch straps, a pale shoulder shroud thrown over one side, a chest rig above cargo trousers with padded thighs
- a sealed white-and-grey field suit with an armored gorget at the throat, a plate carrier and a compact pack strapped over it, padded knees and heavy boots || mil
- => Bomber and flight jackets
- a plate carrier over a dark bodysuit with a powered leg exo-frame braced from hip to boot
- an oversized rollneck sweater with the sleeves pushed back, harness straps over both shoulders and enormously baggy cargo trousers gathered at the ankle || civ
- => Plain traditional robes
- => Lacquered samurai armor
- a heavy hooded work jacket with a reflective hazard stripe down one sleeve and patched insignia at the shoulder || civ
- an oversized weatherproof jacket bristling with pouches and straps, worn over a slung backpack with its harness crossing {possessive} chest || civ
- a padded jacket with riveted metal pauldrons at both shoulders, a scarf wound loose at the throat || civ
- => Kimonos and fine robes
- ragged wrapped cloth bindings over bare limbs, one wrist bound in worn bandaging, feet bare in simple woven sandals || civ notac
- a fringed pleated mantle draped over the shoulders and swagged with hanging chain loops, worn over a dark strapped underlayer || civ notac dressy
- a sleeveless tank top with bandage-wrapped forearms, worn over cargo trousers slung with mismatched belt pouches and holster straps || @scav
- a fitted maroon combat tunic with layered pauldron guards over each shoulder, cinched at the waist by a wide dark sash over cropped trousers || @neosamurai
- a quilted grey duty jumpsuit with articulated knee braces, an olive sash slung across one shoulder and a leather pauldron buckled over it || @neogothic
- a short-sleeved orange-and-white uniform shirt worn under a dark tactical vest, a unit patch stitched to the shoulder || mil
- a fitted flight suit with crimson piping and a raised segmented shoulder guard, high collar sealed to the throat || @gundam
- a soaked black assault suit cinched under a slim chest harness, fabric clinging dark and heavy || mil
- a cropped red flight jacket, sleeves shoved up over a stripped-down underlayer, patched insignia worn soft with scavenged wear || @scav
- plated crimson body armor with a glowing chest core and an articulated ridged spine || @gundam
- a segmented mechanical wing unit fanned wide from one shoulder, primaries tipped in bone-white feathers
- a cropped sleeveless hoodie worn over a bare midriff, a low-slung utility belt studded with cybernetic modules, and thigh-high leg wraps || @cyberpunk
- a matte grey optical-camouflage suit, the light bending across it in faint rippling distortion wherever it catches an edge
- => Cheap suits
- a sealed matte-black diving suit with its hood pushed back and the weight belt still buckled at the waist
- a boxy pale-blue police duty uniform with a black waist rig and a division patch at the shoulder, sleeves rolled to the elbow || mil
- a high-visibility site vest over a plaid work shirt and heavy canvas trousers, a loose chinstrap swinging at the throat || civ
- a torn sleeveless vest over a blood-spattered off-white tee, a chain looping from the belt to the pocket of ripped black trousers || civ
- a baggy rust-red padded jacket with the hood bunched thick around the neck and a strap running down the back || civ
- a long hooded rain slicker hanging below the knee over heavy rubber boots || civ
- a navy work shirt with the sleeves rolled, a climbing harness buckled over grey cargo trousers and strapped knee pads || civ
- a rumpled white lab coat hanging open over a charcoal shirt and dark tie, a photo ID badge clipped at the breast pocket || civ
- => Formal wear
- a fitted black bodysuit with gold filigree trim, a spiked shoulder guard, and a tattered floor-length cape || notac dressy
- a loose white blouse-dress cinched at the waist by a laced leather corset harness, sleeves rolled to the elbow || notac dressy
- A long fitted coat-dress with a popped collar, worn over sheer stockings and low heels. || civ dressy
- A cropped moto jacket worn open over a metallic slip dress, paired with thigh-high boots. || civ dressy
- A fitted button-front uniform dress with a stand collar and rolled sleeves, worn cinched at the waist. || civ dressy
- A cropped jacket layered beneath an open long coat, paired with sheer stockings and ankle boots. || civ
- A long belted trenchcoat worn over a fitted bodysuit dress and thigh-high boots, collar turned up against the chill. || civ
- a ragged black cloak in tattered strips over strapped harness gear, small trophy skulls and pouches hanging from a heavy belt || civ notac @grimdark
- a fitted dark tunic with gold filigree trim at the shoulders and cuffs, worn over close-fitted trousers || civ dressy
- a long tattered black cloak with a ragged trailing hem, worn over dark segmented armor || civ notac @grimdark
- a hooded traveling cloak over a plain draped robe, cinched with a dark sash at the waist and worn boots beneath || civ notac
- a long dark travel cloak with a stitched shoulder patch worn over layered robes, a wide belt slung with pouches and a satchel at the hip || civ
- a scuffed grey tactical jacket sewn with mismatched unit patches and stencilled lettering, cuffs rolled to the wrist || civ
- a long dark coat with ornate gold pauldrons and a wide belt, pale gauntlets and greaves trimmed in gold || civ dressy
- a quilted blue jacket seamed with a glowing accent, a cylindrical pack strapped high on the back and gloved hands trimmed in worn leather || civ @cyberpunk
- a dark navy duty shirt with epaulettes, a ribbon bar and unit patches at both shoulders, a utility belt hung with pouches at the waist || mil
- a weathered red hooded cloak over a loose tunic, cinched with a wide sash and worn over patched trousers || civ notac @neosamurai
- a backless black gown laced up the spine with dark ribbon, sleeves gathered by a wrapped armband || notac dressy @neogothic
- a heavy EVA suit collar ring hanging open at the throat, thick gloved fingers braced near the jaw
- a dark, off-shoulder gown with a plunging metal-trimmed bodice and butterfly clasps at the sleeves || notac dressy @neogothic
- a high-collared black jacket with a single crimson insignia patch at the throat || @cyberpunk
- an oversized pale hoodie with long drawstrings, the sleeves hanging down past the wrists || civ
- an oversized quilted black jacket zipped to the chin, its shoulders padded out enormous, over baggy olive cargo trousers || civ
- a close-fitting graphite armor shell with overlapping rib plates, rounded shoulder caps and a small luminous chevron at the sternum
- a pale pressure suit with a dark abdominal panel, broad circular collar coupling and reinforced joint sections
- a mustard track jacket with parallel stripes down the sleeves under a thick pale fleece collar, worn with practical cargo trousers || civ
- a fitted dark leather jacket with ribbed shoulder panels and an exposed central zip, belted over close-cut trousers || civ
- a cropped dark utility jacket over a close-fitting top, a short straight skirt over opaque leggings and heavy ankle boots || civ
- a pale hooded armored jacket with a dark fitted torso panel, segmented shoulder plates and a small luminous cross on one sleeve
- a fitted dark flight undersuit crossed by pale segmented harness plates at the chest and thighs, forearms left bare
- a glossy pale bomber jacket with a ribbed collar and cuffs over a dark shirt and straight utility trousers || civ
- a pale broad-shouldered cropped coat with oversized pointed lapels over a dark fitted underlayer || civ
- a loose dark pullover with its hood resting around the neck, long sleeves and a soft gathered waist over plain trousers || civ
- a long split-tailed coat with a thick feathered shoulder collar over close-fitting armor
- a padded exploration pressure suit with a rectangular chest control box, reinforced gloves and looping life-support hoses
- a hooded articulated suit of dark armor with a luminous geometric chest inset and overlapping thigh plates
- a smooth enclosed hardsuit with an elongated swept-back helmet profile, inset shoulder plates and luminous seams
- a close-fitting dark flight suit with reinforced shoulder panels, a central front zip and a compact waist belt
- a heavy fur-trimmed field coat over dark layered clothing, reinforced trousers and insulated boots
- a loose collared shirt with sleeves rolled above the elbows, high-waisted belted trousers and tall worn boots || civ
- a dark combat shirt beneath overlapping segmented shoulder plates and a loaded chest rig, padded cargo trousers and reinforced knee guards
- a ragged shoulder cape over a wrapped dark tunic, loose trousers and segmented forearm guards || notac @neosamurai
- a dark fitted pressure suit with ribbed side panels, raised shoulder guards and a triangular illuminated chest insert
- a pale pressure suit with dark side panels, broad harness straps and tall polished boots
- a graphite armored bodysuit with raised blade-like shoulder panels, inset chest plating and thin luminous seams
- a long black leather coat over a fitted high-neck shirt, slim reinforced trousers and buckled boots || civ
- a dark short-sleeved service shirt with a name strip, ribbon bars and shoulder insignia, tucked into matching duty trousers || mil
- a battered improvised chest plate on a leather harness, one spiked shoulder guard and patched reinforced cargo trousers || @scav
- a ragged short hooded cape over a loose wrap shirt and wide trousers, a cloth waist sash and pieced metal shin guards || notac
- a weathered sleeveless wrap tunic with a narrow waist sash, loose tapered trousers and worn boots || civ
- a camouflage combat shirt with a rectangular chest patch and shoulder insignia, reinforced trousers and a compact chest rig || mil
- a pale fitted flight suit with dark flexible side panels, wrist seals and rectangular mission patches || mil

## Outfit (she) +

<!--
  Feminine cuts, added to the neutral options above rather than replacing them -
  a woman in grey coveralls is entirely normal and should stay possible.

  The armored-bodyglove entries deliberately name no glow color: the palette
  sentence in the template already makes the rolled Glow colour the only
  saturated color, so "glowing seam lines" picks it up instead of fighting it.
-->

- a cinched belted jumpsuit unzipped well below the collarbone, the belt hauled tight at the waist || civ
- a cropped utility jacket over a short high-waisted work skirt and sheer dark tights, a band of bare midriff between them || civ
- a deep wrap-front tunic belted at the waist over close-cut trousers, the crossed neckline cut low || civ
- a long knitted cardigan over practical fatigues, sleeves pushed up || civ
- => Corporate skirt suits
- a short light civilian dress patterned with small dark polka dots, thin straps at the shoulders, over dark thigh-high stockings, incongruous against the grime || civ
- => Open jackets over crop tops
- a graffiti-tagged cropped t-shirt and cut-off shorts, midriff and legs bare || civ
- an asymmetric black coat-dress with a high collar, wire and cable detail threading down the front, ribbon straps and a beaded choker at the throat || civ
- a black sleeveless harness top with rust-red trim piping and buckled shoulder straps, a lit strip running down the center of the chest, long weathered grey-white bracers past the elbow with their plating cracked at the shoulder seams
- a black strapless bodice leaving the shoulders and arms bare, a draped pale scarf-cowl wound loose at the throat and wide gold cuffs clasped on both forearms || civ
- a dark work shirt with the sleeves rolled to the elbow under a strapped harness rig, a radio pouch at the chest, baggy olive cargo trousers, tactical gloves and armored shin guards over heavy boots || civ
- a worn hooded jacket patched with faded characters at the sleeve, torn and taped at the seams || civ
- a cropped black graphic hoodie with a small patch at the sleeve, over dark track trousers striped down the leg || civ
- a black leather corset-coat with a high spiked collar, a short pleated underskirt and thigh-high tactical boots || civ
- a glossy black bodysuit with a short pleated skirt panel at the hip, one arm sheathed in an articulated mechanical gauntlet running to the shoulder, over knee-high boots
- a tattered black cloak like torn wings draped from the shoulders over a wrapped cropped top, buckled utility straps cinched at the waist and one armored bracer laced to the forearm || civ
- a fitted dark leather bodice cut low at the chest over a long dark wrap skirt, faint red markings tracing down one bared arm || civ
- an ornate white and blue segmented armor jacket laced tight over a corseted front, finished with gauntlet-cuffed gloves || dressy
- a gold-braided long coat worn open over a laced corset top, cinched with a wide buckled sash and paired with striped thigh-high stockings || dressy
- a fitted leather corset baring the midriff under a long gold-buttoned coat trailing to the knee || civ dressy
- an off-shoulder pale gown with a black strap harness crossing the bodice || dressy
- a form-fitting flight suit plated at the collar and bust, seams sealed against a mounted harness || @gundam
- a backless halter gown with straps crisscrossed bare down the spine to the waist || dressy
- => Glowing-seam bodysuits (cyberpunk) || @cyberpunk
- a pale-blue police uniform blouse with the sleeves rolled, tucked into a straight duty skirt above a black belt rig || mil
- a cropped black jacket over a low-cut corseted bodice, a long black skirt slit high to the thigh and draped with fine gold chainwork || civ dressy
- a floor-length black column dress with sharp padded shoulders and long fitted sleeves, slit up the back of one leg || civ dressy
- a long white high-collared lab coat cut with dark side panels, slit high up one leg over dark leggings, an ID badge clipped at the hip || civ
- a cropped olive armored vest bulked out with padded pouch plates over a black crop top, pouched bands strapped round both upper arms and fingerless armored gloves
- a cropped military-style jacket with a segmented armored vambrace banded down one forearm and a unit patch at the shoulder, worn open over a white blouse and a black pleated skirt cinched by a wide belt || @neosamurai
- a white pressure suit with silver ring joints at the elbows and knees, a small flag patch at the chest and a compact oxygen pack strapped to the back
- a black zip-front jacket unzipped low over the chest, fastened by a chain-linked zipper pull || civ @cyberpunk
- a skin-tight sealed orange pressure suit with plated seams at the collar and shoulder, faint stencilled unit markings across the chest
- a fitted red halter top paired with an olive tactical thigh harness strapped over bare hips || mil
- a long open trench coat worn over a fitted slip dress and sheer stockings || civ
- a cropped athletic top with a jacket tied around the waist, worn over high-waisted shorts and thigh-high socks || civ
- a torn jacket worn open over a midriff-baring top and tactical cargo trousers, a strap cinched over one thigh || mil
- a fitted red bodycon dress paired with a cropped jacket with glowing seam piping, worn with sheer thigh-high stockings || dressy
- a single articulated black shoulder plate worn over an otherwise bare back, its ridged surface rain-slicked || mil
- a fitted red tactical bodysuit with a segmented grey harness strapped over the hips and thighs || mil
- a black backless halter gown with a plunging cutout panel, paired with long opera gloves || dressy
- an unbuttoned cropped jacket worn over a bare midriff, thigh straps crossing bare skin beneath it || mil
- a fitted black tactical jacket banded in red at the cuffs, a red insignia stitched at one shoulder and a wide red sash wound at the hip, mechanical pouches slung from a belt beneath it || @grimdark
- a white off-shoulder lace-trimmed blouse laced tight over a black high-waisted corset brief, thigh-high boots || civ
- a heavy black-and-red fur-trimmed coat with a metal pauldron buckled at one shoulder, worn open over a grey turtleneck and olive cargo trousers tucked into fur-cuffed boots || civ
- a loosely buttoned slate-blue blouse tucked into high-waisted brown trousers cinched with a wide belt, layered gold pendant necklaces at the throat || civ
- a high-collared dark coat trimmed in gold, cinched with a wide belt over a long skirt || civ dressy
- a flowing blue robe trimmed in gold brocade, cinched with a wide belt over a pale underlayer || civ notac dressy
- an open trench coat over a low-cut black top and dark trousers, a slouched bag at the hip || civ
- a sleeveless white ceremonial gown embroidered with dark cross motifs, a flowing red cape fastened high at the throat and a jeweled pendant hanging to the waist || notac dressy
- A bulky white pressure suit with a chest-mounted life-support console, cinched red webbing straps, and a national flag patch on the shoulder. || civ
- A long asymmetric dark coat-dress with an armored pauldron plate and trailing utility straps, worn over pale underlayer sleeves. || civ dressy
- a loose red bomber jacket worn over a dark cropped top and a short fitted skirt, with opaque thigh-high stockings and ankle boots || civ
- a loose cream sweater with sleeves pushed back, tucked into a short dark skirt over sheer tights || civ
- an oversized dark jacket slipping low from the shoulders over a fitted cropped top and high-cut shorts, with tall stockings || civ
- a dark cropped tank and short utility skirt with hanging buckle straps, sheer thigh-high stockings and heavy knee boots || civ
- a short fitted dress under an open cropped leather jacket, a narrow belt at the waist above dark stockings || civ
- an open cropped red jacket over a pale scoop-neck tank, a narrow black choker at the throat and dark trousers || civ
- an open long coat over a dark cropped tank and high-waisted utility trousers, the coat lining hanging in broad loose panels || civ
- a sleeveless dark tank with a high neckline, several stacked metal necklaces and a thick studded wrist cuff || civ
- a loose dark jacket with small sleeve patches over a high-cut pale bodysuit with a dark central torso panel
- a cropped work jacket over a scoop-neck top and fitted shorts, with a wide utility belt and worn knee boots || civ
- a long dark coat with a broad folded collar over a belted short tunic, opaque stockings and knee-high boots || civ
- a fitted metallic shift dress beneath an open red bomber jacket, the short straight hem above sheer dark stockings || civ
- an oversized pale pastel jacket over a short soft dress and light thigh-high socks || civ
- an olive utility parka worn open over a plain dark top and short fitted skirt, with tall socks and sturdy ankle boots || civ
- an oversized dark jacket over a fitted satin camisole and shorts, with dark thigh-high stockings || civ
- a high-neck sleeveless bodysuit beneath an open leather coat, thigh-high stockings leaving the upper thighs bare || civ
- a loose satin wrap robe belted low at the waist, broad sleeves and a long skirt falling open at one knee || civ notac dressy
- a close-fitted black composite hardsuit with overlapping hip plates and raised segmented shoulder shells
- a long-sleeved cropped top over a short pleated skirt, a wide belt and heavy ankle boots || civ
- a dark kimono with wide sleeves, a broad contrasting obi and a skirt slit up one thigh || civ notac dressy @neosamurai
- a polished dark bodysuit under sculpted gold chest and shoulder armor, narrow metallic bands tracing the hips || dressy
- a loose off-shoulder blouse tied at the waist over high-cut shorts and thigh-high boots || civ
- a fitted light exploration suit with rolled sleeves, a broad leather utility belt, side pouches and knee-high boots || civ
- an armored officer jacket with gold-fringed epaulettes, a segmented breastplate and a layered pleated skirt above armored boots || mil dressy
- a glossy fitted armored suit with rounded shoulder shells, dark flexible joints and curved hip plates
- a dark backless evening gown gathered into a twisted knot at the lower back || civ dressy notac
- a sleeveless printed tank top tucked into faded denim shorts, with scuffed lace-up ankle boots || civ
- a fitted dark corseted ensemble beneath a pale open robe with full sleeves, embroidered edging and jeweled fastenings || civ dressy notac
- a pale floral day dress with puffed sleeves, a fitted waist and a softly gathered calf-length skirt || civ
- a cream blouse with loose rolled sleeves tied at the waist above light high-waisted shorts || civ
- a tailored light coat draped over the shoulders above a dark V-neck dress || civ dressy
- an embroidered pale ceremonial dress with a long split skirt and an ornate red cape edged in gold || civ dressy notac
- a sleeveless floral sundress with a short gathered skirt and dark lace-up ankle boots || civ

## Formal wear

- a tailored charcoal formal coat with satin lapels, a narrow waistcoat and polished brass buttons over a pressed white shirt || civ dressy
- a floor-length black formal coat with a high collar and slim-cut pleats, worn over a pale undershirt and muted cuffs || civ dressy
- a dark olive dinner jacket with matte gold piping, a silk sash at the waist and pointed lapels folded at the throat || civ dressy
- a cream silk evening coat with a narrow high neckline, structured shoulders and a short side slit at the hem || civ dressy
- a white-collar ceremonial coat with subtle embroidery along the seams, a narrow cummerbund and restrained cuff bracelets || civ dressy
- a black velvet blazer with a soft lapel and narrow waist tie, cuffed sleeves finished with thin chrome thread || civ dressy
- a pale gray tailored frock coat with sculpted shoulders, a silk panel at the back and polished silver watch chain across the chest || civ dressy
- a midnight-blue civic coat with a narrow front drape, high-buttoned front and understated gold trim at cuffs || civ dressy
- a burgundy formal waistcoat worn over a clean shirt, short pleated skirt-tail and discreet chain loops at the beltline || civ dressy
- a silver-threaded ceremonial jacket with broad shoulders, a stiff collar and buttoned side panels over narrow dark slacks || civ dressy

## Formal wear (she) +

- a pleated ivory evening coat with a narrow waist seam, structured shoulders, and a narrow silk sash at the side || civ dressy
- a charcoal silk wrap dress with a high collar and hidden button stand, cut close through a tailored waist with slim cuffs || civ dressy
- a deep-burgundy formal jacket with sculpted lapels, narrow side slits, and a matte-gold waist sash || civ dressy
- a floor-length cobalt silk dress with a subtle bustle at the hips and restrained sleeve piping || civ dressy
- a black and ivory formal two-piece with a short-tail skirt and broad shoulder seams, pinned at the lapel with a tiny enamel badge || civ dressy
- a glossy white ceremonial coat over a fitted dark dress, with a narrow ribbon collar and a thin chain-belt at the back || civ dressy
- a pale gray tailored office dress with a structured bodice, narrow skirt panels and narrow-hemmed cuffs folded to the elbow || civ dressy
- a silver-threaded court coat with a high stand collar, short pleated panel at the waist and elegant wrist cuffs || civ dressy
- a dark jade evening jacket with matte-gold cuffs, sculpted front drape, and an ankle-length dark skirt panel over tailored slacks || civ dressy
- a cream formal bolero coat over a crisp white blouse and narrow-trouser jumpset, cut with a single side split || civ dressy

## Flight suits

- a fitted flight suit with the top half unzipped and knotted at the waist
- a tan and beige flight suit with rust-red accents, padded shoulder and knee armor and utility straps at the thighs || mil
- a fitted maroon-red flight suit with a cream chest yoke and shoulder rank patches, a rolled tan poncho-cloak bundled loosely at the waist, a bandolier of pouches slung crosswise over the chest, white gloves, and knee-high brown boots wrapped in pale canvas leggings || mil
- a fitted tactical flight suit with a high collar, buckled straps, small unit patches and an armband || mil
- a weathered mustard-yellow flight suit with a shoulder star patch and a small unit patch at the chest, a pale scarf knotted loose at the throat || mil
- an olive tactical jumpsuit under a cropped chest harness loaded with hip pouches, fingerless gloves and low tactical boots || mil
- a navy flight jumpsuit under a cropped tactical vest loaded with chest pouches, a sidearm holstered at the hip || mil
- a weathered orange flight jumpsuit with patched cargo sleeves, worn under a trailing grey scarf || civ
- a scuffed flight suit unzipped low at the collar, a crash harness cinched tight across the chest || mil
- a white-and-olive labor pilot's suit with a padded collar, buckled chest harness and a stencilled unit number at the thigh || mil
- a white-and-navy flight suit with padded shoulder patches and a chest-mounted rank tab, sleeves marked with a stenciled unit triangle || mil
- a fitted flight bodysuit worn under a tactical vest with segmented pauldron guards and a pouched belt rig || mil
- a fitted white flight suit with padded knees, chest rank patches and a crossed utility harness at the hips || mil
- A weathered orange flight coverall cinched with a chest harness and a boxy survival backpack, sleeves rolled to the elbow. || mil @scav

## Flight suits (she) +

- x2 a flight suit tailored close through the bust, waist and hips, the front zip run down past the sternum
- a close-fitting pilot undersuit worn without its outer shell, unzipped to the sternum and clinging to every line of the figure
- a sleek fitted flight suit, dark through the torso with silver-white segmented plating at the hips and thighs, thin glowing circuit piping tracing the shoulders and the chest seam, the front zip run down low
- a high-collared tactical pilot suit with padded shoulder and knee armor, glowing cable detail running the length of one sleeve || mil
- a mustard-yellow flight suit with padded shoulder patches and a wide belted utility harness, sleeves rolled to reveal a lighter underlayer, a weathered grey scarf knotted loosely at the throat
- a silver pressure suit with red accent piping, chest patches, and a bulky life-support pack riding high on the shoulders || mil
- a fitted orange pressure suit with a crossed chest harness and a holstered scanner pouch at the sternum, a wide belt and heavy tactical gloves
- a white-and-grey flight suit with orange piping, a padded chest harness and buckled utility straps at the thigh || mil @gundam
- a fitted olive flight suit with padded shoulder yokes, sealed tight to the collar || mil
- a fitted dark flight suit worked with gold filigree, a structured pauldron over one shoulder and a wide jeweled belt cinched at the waist || dressy
- a cream flight suit cinched with wide leather belts studded with turquoise gems, matching gauntlets and knee guards over tall buckled boots
- a fitted white-and-blue flight suit trimmed in brown leather straps, a wide buckled belt cinched at the waist and a chest patch at the collar

## Combat uniforms and plate carriers

- a modern combat uniform in faded broken-pattern camouflage, padded combat shirt with the sleeves pushed to the elbow, knee-padded trousers || mil
- a modular plate carrier loaded with magazine pouches over a padded combat shirt, MOLLE straps cinched flat || mil
- a composite plate harness over a dark undersuit, magazine pouches racked across the front and a small status indicator lit at the collar || mil
- a dust-caked arid-pattern combat uniform under a slim chest rig, a shemagh loose at the neck || mil
- a low-profile plate carrier over a sweat-stained combat shirt, tags visible at the collar || mil
- a hooded recon softshell in broken-pattern camouflage, hood down, face paint half worn off || mil
- a multicam combat uniform under a modular plate carrier, magazine pouches ranked across the chest, knee-padded trousers and fingerless tactical gloves || mil
- weathered olive-green camouflage tactical gear, a plate carrier vest worn over a long-sleeve field jacket, camo trousers, fingerless tactical gloves and scuffed combat boots || mil
- a battered plate carrier strapped over a sleeveless combat shirt, arms bare, fingerless armored gloves and loose knee-padded cargo trousers
- bright orange coveralls belted under a tan tactical vest studded with pouches || mil

## Combat uniforms and plate carriers (she) +

- a combat uniform taken in through the waist, sleeves pushed up, a plate carrier cinched tight over it || mil
- a fitted black leather-and-plate corset jacket cinched with a heavy harness and thigh holsters || mil
- an olive segmented plate harness worn over a cropped tactical top, straps crossing a bare midriff || mil

## Field jackets

- a worn olive field jacket with the collar up over a ribbed dark turtleneck and a slim chest rig, fingerless tactical gloves || mil
- a weathered black field jacket stencilled with a unit number and a small hazard patch, worn over a coarse knit jumper || mil
- a black military utility jacket stencilled with a unit number and a hazard triangle patch, hanging open over a plain olive tank top || mil
- an olive field jacket with the sleeves pushed back over a close black bodysuit, a chest rig of magazine pouches, armored knee and shin guards above heavy trainers
- a mottled camouflage jacket worn open over a plain dark tee stencilled with a bold unit number, cargo trousers and fingerless tactical gloves || mil
- a weathered dark-green field jacket, collar turned up, patched high on one shoulder || mil
- a bulky fleece-collared field jacket gathered high at the throat, cuffs frayed at the wrist || civ
- a charcoal field jacket with reinforced elbow cuffs, zipped-open chest panels and a short harness loop over one shoulder
- a dark utility jacket with matte shoulder guards, a folded toolkit loop on the strap and an exposed diagnostic cable across the side
- a black field jacket with an open front, integrated wrist console strap and cable ties along the lower hem
- an olive drab jacket with patchwork seam tape, broad shoulder seams and a compact satchel hanging from a rear strap
- a weatherproof blue-green work jacket with rolled cuffs, steel-capped sleeves and a cross-body tool sling under the chest
- a short-collared field jacket with reinforced chest plate and stacked chain loops for quick sensor packs
- a lightweight utility jacket with twin forearm pockets, clipped gauge clips and a narrow utility cord tied at the waist
- a graphite field jacket with a partial quilted lining, open seams for heat vents and a clipped hardhat strap at the hip
- a broad-shouldered weather jacket with dark piping, a harness slot at the back and spare couplings on the belt
- a rugged tan field jacket open over an armored undershirt, with thumb loops for power clamps and knee braces
- a soot-streaked service jacket with hidden mesh vents, two pocketed patch flaps and a folded comm card at the collar
- a weathered orange hooded field jacket with oversized patch pockets, worn open over a dark base layer || civ
- an oversized olive field jacket hanging open over a fitted grey compression shirt, a canvas sling belt slung loose across the hips and fingerless gloves taped at the cuffs

## Field jackets (she) +

- a weathered field jacket stencilled with a unit number and a small hazard warning patch, hanging open over a cropped top and bare midriff || mil
- A drab field jacket worn open over a fitted bodysuit and knee-high boots, collar turned up against the rain. || mil
- a fur-hooded parka belted over tactical chest pouches and a slung radio pack || mil

## Open jackets over plated or glowing bodysuits

- a black tactical jacket, unzipped and open, its interior lining faintly glowing, over a fitted dark bodysuit with light plating at the shoulders, forearms and shins
- a segmented armored bodysuit under an open hooded jacket, a long scarf wound at the throat and trailing loose behind

## Open jackets over plated or glowing bodysuits (she) +

- a black tactical jacket with piped trim over a close grey bodyglove and armored thigh-high boots, a hand's width of bare thigh above them
- a black military jacket with dull gold trim, worn open over a low-cut dark bodysuit and chipped white armor plates || mil
- a white field jacket thrown open over a black bodyglove cut deep at the chest and traced with faint glowing conduit lines
- a black hooded jacket trimmed in dull gold and draped loosely off both shoulders, over segmented pale grey-white plating at the hips and thighs and fitted leggings traced with a thin glowing line down the shin
- an open black jacket with a stiff collar over a fitted grey-white bodysuit, thin glowing stripes running down the sleeves and legs and tracing the seam at {possessive} bare midriff, segmented gloves and thigh-high boots
- an open white jacket over a fitted dark bodysuit marked with a small angular chevron at the chest, thigh-high leggings traced with glowing curved stripes, gloves and boots trimmed in dull orange
- an open tactical jacket with a unit patch worn over a plated bodysuit that bares the midriff || mil @cyberpunk
- A long open coat worn over a form-fitted plated bodysuit and thigh-high stockings, the coat's hem trailing loose past the hips. || civ
- An open jacket worn over a fitted bodysuit with glowing seams down the sides, left loose over bare thighs and stockinged feet. || civ

## Glowing-seam bodysuits

- a black tactical bodysuit with sharp angular trim and a high collar piece lit with small accent glows, a barcode marking inked at the collarbone

## Glowing-seam bodysuits (she) +

- a sleeveless flight harness of buckled straps over a black bodysuit unzipped low between them, a single lit indicator strip down the chest, arms and shoulders bare
- a close-cut pilot bodyglove in white and grey, lit seams tracing the waist and hips, partial shoulder plating and nothing over the bare midriff
- a sleeveless black tactical bodysuit with an exposed back framed by a cybernetic support harness, thin glowing circuit lines running along the spine and shoulder blades
- a fitted grey-white bodysuit traced with a thin glowing circuit line, one oversized pauldron stencilled with a small insignia, segmented armor plating down the legs || mil
- a sleek black-and-white armored bodysuit with an oversized geometric pauldron on one shoulder, a lit status display set into the chest plate and thin glowing seams tracing the joints, a bare midriff panel at the waist
- a fitted black leather bodysuit with a high popped collar, rain-slicked and traced with faint glowing seam lines at the wrists
- a segmented tactical armor plate carrier with glowing seam lines down each forearm and shoulder, a call-sign patch stitched at the chest || mil @cyberpunk
- a fitted black segmented bodysuit with glowing joint rings at the elbow and knee, form-fitted through the torso and shoulders || @cyberpunk
- a segmented dark bodysuit with glowing seams down the torso and thighs, a stencilled unit code at the hip where cabling trails from a socket there
- a sealed pale armored bodysuit with glowing seam lines at the joints, a circular stencilled unit glyph on one shoulder plate || @cyberpunk
- a fitted crimson plated bodysuit with segmented armor panels and glowing seams tracing down the torso
- a fitted black segmented bodysuit plated at the chest and shoulders, thin glowing seams tracing the panel lines down each arm
- a glossy fitted bodysuit traced with fine glowing joint lines, articulated panel seams at the shoulders and hips || @gundam

## Glowing-seam bodysuits (cyberpunk)

- a skintight tactical bodysuit plated at one shoulder, every panel line glowing hairline-thin
- a skintight bio-mechanical bodysuit fused with plating at the shoulders and spine, seams glowing hairline-thin

## Unlit tactical bodysuits

- a form-fitting armored bodysuit of segmented black plating, neural-interface cabling running from a plug at the collar
- a fitted black tactical bodysuit with buckled strap detailing at the shoulder and ribbed panel seams || civ
- a sealed high-collared armored bodysuit with heavy pauldron-style shoulder plating and integrated sensor housings at each shoulder

## Unlit tactical bodysuits (she) +

- a fitted armored bodyglove under a partial plate harness, the plates leaving the midriff and one shoulder bare
- a sleek black tactical bodysuit with segmented dark red armor plating across one shoulder and arm, fingerless gloves and knee-high boots || civ
- a skin-tight charcoal bodysuit with a cropped halter back and thigh-high boots, wrist straps cinched over fingerless gloves
- a sleek black high-collared combat bodysuit cut away at the hips and lower back, thin straps crossing the bare skin, long gloves and thigh-high boots
- a high-collared black tactical bodysuit with a keyhole cutout below the throat, padded shoulders and a holster strap cinched round one upper arm
- a high-collared black bodysuit cut open in a keyhole at the chest and in long slashes over both hips, gloves running past the elbow
- a fitted matte-black tactical bodysuit with segmented chest and shoulder plating, faction patches stitched at the collar and thigh, a faint glowing accent along the seams || mil
- a fitted charcoal-black tactical pressure suit crossed by strap-harness rigging at the chest, unit tabs and a mission patch stitched at both shoulders || mil
- a black ribbed tactical catsuit zipped high to the throat, criss-crossed strap harness over the chest and a wide utility belt hung with pouches and holsters || civ
- a form-fitting matte-black tactical bodysuit with a segmented armored shoulder guard and a zippered high collar

## Hardsuits and segmented armor

- scuffed hardshell carapace armor over a sealed undersuit, repainted in patches, helmet clipped at the belt || mil
- an EVA-rated hardsuit with the helmet seals open and the gauntlets stowed
- a sealed hardshell combat suit with segmented plating at the shoulders, chest and shins over a close dark bodyglove || mil
- a sealed rescue hardsuit of segmented panels with armored boots and a hard equipment pack riding high on the shoulders || civ
- a battered set of heavy segmented plate armor, scorched and scarred at the shoulders and forearms, in dull combat red || mil
- a segmented white technical armor shell with dark reinforced wrapping at the thighs, scorched and battle-worn || mil
- a segmented composite tactical armor suit with actuated knee joints and a compact backpack module, worn over an olive combat shirt || mil
- a sleek angular powered armor suit with an oversized intake-vented backpack module, warning stencils and exposed cabling trailing from the shoulder || mil
- heavy segmented composite armor with a large stencilled unit number across the shoulder plate, status lights lit along the collar || mil
- a bulky riot-control suit of segmented off-white armor over a dark uniform, a numbered plate across the chest || mil
- matte black segmented assault armor with heavy rounded pauldrons, a belt of hard-cased pouches slung at the waist
- heavy faceless dark-grey armor of thick rounded plates, ammunition pouches racked at the belt and a bulky holster strapped to one thigh
- a segmented dark hardsuit with bronze-gold pauldron armor banded in yellow piping, a high knitted cowl collar wrapped at the throat || @gundam
- a segmented white-and-grey plate hardsuit with reinforced pauldrons and shin guards || mil
- a heavy shell of segmented black armor plating with a glowing detail tracing the seams at the joints and shoulders || mil
- segmented grey-and-black plate armor with raised pauldrons and a glowing seam accent, a utility belt slung at the hip
- a sealed segmented plate suit with an angular breastplate and shoulder pauldrons over a worn olive field jacket, a small metal cross fixed at the chest || mil
- a segmented dark tactical plate suit with an angular breastplate and articulated pauldrons || mil
- a fitted grey hardsuit with segmented black joint plating, a sealed chest emblem and cinched harness straps across the torso || mil @gundam
- hulking matte-black powered armor built up in faceted overlapping slabs, oversized pauldrons swallowing the shoulders

## Hardsuits and segmented armor (she) +

- x2 a white-and-grey armored hardsuit of scuffed fitted plates over a black bodyglove, glowing seam lines tracing the limbs
- a fitted red-and-white segmented plate armor suit cut low across the chest, articulated joints at the shoulders and knees
- a skin-tight segmented plate suit etched with glowing sigils, its long articulated tail-fins trailing to the floor || notac
- a sleek matte-black powered armor sculpted tight to the body, thin amber seams tracing every joint and plate
- a matte black segmented hardsuit with sharp plated shoulders and a curved lower-back panel, a glowing accent tracing the spine and hip seams
- a silver-grey segmented hardsuit with sharp angular chest and shoulder plating, a glowing accent lighting the seams
- a sleek matte-black segmented hardsuit plated at the chest, hips and shoulders, glowing seam lines tracing every joint || @cyberpunk
- an ornate gold-trimmed black hardsuit baring deep cleavage at a glowing chest core, gilded pauldrons and dangling ornamental chains at the hips || dressy
- a fitted charcoal hardsuit bodice with a sculpted high collar and glowing seam lines tracing the chest plating
- a full segmented powered armor suit in matte gunmetal, thin glowing accent lines tracing the joints and oversized pauldron guards at both shoulders
- sculpted gunmetal armor plating cut close to the body, glowing seams tracing down the torso over an exposed braided cable spine

## Caped armor suits

- a sealed grey tactical suit with layered armor pads at the shoulders and knees, a chest rig of ranked pouches and a long split-tailed shroud coat hanging to the ankles
- a dark armored combat suit under a loaded chest rig, a long asymmetric white half-cape hanging from one shoulder to the ankle
- a sleek black powered tactical exo-suit with segmented plating at the knees and shoulders, a long dark half-cape trailing from one shoulder || mil
- a fitted dark tactical bodysuit segmented with rust-orange trim plating at the joints and collar, a long weathered rust-colored cape trailing from one shoulder
- a cracked white plate breastplate with a glowing cross emblem at the shoulder, a hood drawn up and a trailing white cloak fastened at the back || dressy @neogothic
- a hooded suit of dark segmented plate armor with an ornate glowing emblem set at the chest, a short cloak trailing from the shoulders and a belt of pouches cinched at the waist || @neogothic

## Plain traditional robes

- a dark travel-worn robe with a crimson underlayer at the collar and sleeves, belted over wide hakama-style trousers || civ notac
- layered white pilgrim's robes gone travel-stained at the hem, a coarse rope belt cinched at the waist || civ notac
- a weathered haori-style jacket over a high-collared undershirt, sleeves bound back with cord || civ notac
- a tattered dark robe hanging open at the chest, its hems torn and trailing loose || civ notac
- a dark robe with a pale patterned collar, red fingerless gloves laced to the wrist || civ notac
- a dark patterned robe with a bright orange underlining, a string of prayer beads wound at one wrist || civ notac
- a plain hooded robe in weathered ochre wool, cinched with a rope belt and worn over heavy work boots || notac
- a hooded orange robe falling to the ankles, hands folded loose inside the sleeves || civ notac
- heavy hooded traveling cloaks worn over simple robes, the hems snapping in the wind || civ notac
- a heavy dark monastic robe with wide sleeves and subtly patterned hems || notac @neogothic

## Kimonos and fine robes

- dark samurai robes with a long crimson cloak trailing from the shoulders, one leg bared and banded with tattooed markings || civ notac dressy
- a dark robe traced with gold embroidered trim, a purple sash knotted at the waist and small tassels hanging loose || civ notac dressy
- a dark kimono cinched with a wide white sash tied in a full bow at the back || civ notac dressy
- a red-patterned haori jacket with a stiff swept collar worn open over a dark kimono, cinched by a wide sash, paired with pleated grey hakama trousers || notac @neosamurai
- a mustard-yellow haori stencilled with kanji and circular emblems, worn open over segmented black armor plating || notac @neosamurai

## Kimonos and fine robes (she) +

- an elaborate floral kimono layered over a plain white underrobe, sleeves trailing long past the fingertips || civ notac dressy
- white shrine robes with a red hakama skirt, a cord-tied over-sash crossing the chest || civ notac dressy
- a dark kimono patterned with pale plum blossoms, a crimson underlayer glimpsed at the collar and wide sleeves || civ notac dressy
- a flowing, wide-sleeved robe cinched with a soft obi-style sash, fabric billowing loose in the water || notac
- a loose floral silk robe worn open over bare shoulders, cinched loosely at the waist || civ dressy
- a black kimono with a glossy wide red obi cinched at the waist, lace panels showing through the slit hem, worn loose off one shoulder || dressy
- a dark indigo kimono-robe patterned with pale swirling clouds, bared at the nape and cinched with a wide obi bow at the back || notac @cyberpunk

## Lacquered samurai armor

- segmented lacquered armor plates over a dark underrobe, a torn banner cord trailing from one shoulder
- segmented dark armor pauldrons over a hooded travel robe, striped forearm wraps and small ornamental tassels at the shoulder
- segmented crimson-lacquered armor plates over a floral-patterned quilted robe, tasseled cords trailing from one shoulder and a wrapped bundle slung across the back || civ notac dressy
- full lacquered samurai armor in dark green and black with segmented shoulder pauldrons over a trailing hakama-style skirt, ornamental tassels at the waist || civ notac dressy
- a tattered straw mantle draped over segmented lacquered armor, one forearm sheathed in a scarred prosthetic gauntlet || civ notac
- segmented black-and-gold lacquered armor with ornate floral filigree plating over a dark underrobe || civ notac dressy

## Lacquered samurai armor (she) +

- a lacquered single pauldron over a fitted dark robe with an embroidered high collar, tasseled cords hanging from the shoulder, a wide sash cinched at the waist || civ notac dressy
- a partial lacquered pauldron and vambrace worn over a cropped underlayer baring the midriff, small red tassels trailing from the shoulder plate || civ notac dressy
- a white-and-black lacquered armor harness baring the midriff, fitted white trousers tucked into patterned boots || civ notac dressy
- a sleeveless dark lamellar armor bodice with a red cord sash, plate segments hanging low over dark leggings, {possessive} shoulders left bare || civ notac dressy

## Work coveralls

- layered grey work coveralls patched at both knees || civ
- a white mechanic's coverall with red trim at the cuffs and collar, sleeves rolled past the elbow under a matching soft cap
- a threadbare mustard-yellow work coverall patched at both knees, a canvas tool satchel cinched to one hip || civ
- a sun-faded orange work jumpsuit worn under a heavy grey scarf, cuffed sleeves over grease-stained gloves, a multi-pouch tool belt cinched at the waist || civ
- grease-blackened overalls stripped to the waist and knotted there over a sweat-damp undershirt, a heavy tool belt slung at the hips || civ
- olive expedition coveralls zipped open at the collar over a pale shirt and dark tie, heavy work gloves tucked into a laden belt || civ
- a faded charcoal work coverall with reinforced knee panels, patched elbows and a clipped radio pouch on the chest || civ
- a cobalt maintenance coverall with cable-port seams, tool loops at the thighs and a folded cloth patch for quick repairs
- a dust-caked orange-blue work overall split at the shoulder seams, thick seam tape down the calves and a belt harness for tool tubes || civ
- a deep slate coverall with riveted thigh pockets and an old respirator strap hanging loose across the chest
- a black field coverall over a short undershirt, sleeves tied high and a magnetic wrist rig fastened at the left forearm
- an olive utility jumpsuit with reinforced elbows, weathered knee guards and a short zipped utility panel at the waist
- a sun-bleached maintenance suit with scuffed cargo seams, a canvas chart roll folded at the belt and a taped forearm tab
- a greased brown mechanic coverall with folded knee pads, double-stitched shoulder seams and a broad cloth pouch at the rear
- an acid-washed industrial coverall with bright hazard tape at the cuffs, split thigh pockets and a clipped tablet case on the hip || civ
- a rust-red dock worker coverall with short sleeves, reinforced arm wraps and a looped tool satchel across the back
- a heavy insulated arctic coverall with a fur-trimmed hood and quilted panels, work gloves and goggles pushed up on the brow || civ

## Work coveralls (she) +

- a sleeveless coverall unzipped to the navel and knotted off at the waist over a cropped tank, arms and midriff bare || civ
- a scorched tan work jacket unzipped low over a dark tank top, crossed harness straps studded with tool pouches || civ
- a set of orange work coveralls cinched with a tool harness and belt pouches, straps crossing the back || civ

## Dress uniforms

- a formal service uniform, sharp high collar and rank tabs, a slim data-tab clipped at the breast || mil
- a black formal dress uniform with a high standing collar and small rank pips, a double row of buttons, dull red piping at the shoulder boards, a ribbon rack at the breast and white dress gloves || mil
- a tailored white dress uniform trimmed in gold braid, a stiff high collar and shoulder boards marking rank || mil dressy
- a fitted cream double-breasted service jacket with rust-toned collar tabs, matching trousers and a wide belt || mil dressy

## Dress uniforms (she) +

- a dress uniform tailored close to the figure, fitted jacket over a short straight skirt, bare legs above polished knee boots || mil
- a black formal dress uniform, high standing collar and rank pips above a ribbon rack at the breast, white dress gloves, a long dark pleated skirt gathered under a wide sash at the waist || mil
- a white double-breasted officer's tunic with a high open collar and armored shoulder boards, belted at the waist over a short flared skirt, a long dark cape hanging from the shoulders, garter straps at the thigh above white boots || mil
- a fitted black tactical officer's jacket trimmed in gold epaulette fringe, high stiff collar, worn over a pleated red skirt with garter straps and thigh-high stockings || mil dressy
- a fitted dark military tunic with a high white collar and gold shoulder cording, a small emblem pinned at the chest || mil
- a tailored white officer's coat with a high black collar and gold shoulder boards, dress gloves and a low-slung belt hung with sealed pouches over slim trousers || mil @corporate

## Long coats over fatigues

- a long weatherproof coat over practical fatigues
- an armored softshell greatcoat over slim uniform trousers and composite-soled boots || mil
- a dark olive-grey tactical coat over practical field gear, collar up and sleeves pushed back, no insignia or unit markings anywhere on the kit
- a long olive field coat over a black rollneck, a shoulder holster rig showing at the open front || civ
- a heavy olive winter greatcoat over a service uniform, the fur collar turned up and gloves stuffed in one pocket || mil

## Leather jackets

- a battered leather jacket gone soft with years of wear || civ
- a weathered leather jacket with a segmented armor plate at one shoulder, worn open over a dark top || civ
- a weathered tan leather jacket rolled to the elbow, layered over a thick wrapped scarf || civ
- a hip-length tan leather jacket worn open over a high-collared dark bodyglove, a drop-leg holster rig strapped down one thigh || civ

## Leather jackets (she) +

- a hip-length tan leather jacket over a high-cut dark combat leotard and thigh-high stockings, a drop-leg holster strapped down one bare thigh || civ
- a long black leather jacket worn open over a fitted top and shorts, paired with thigh-high boots || civ
- A cropped leather jacket worn open over a chrome underbust top and a high-waisted mini skirt, finished with fingerless driving gloves. || civ
- a black leather jacket over a fitted black mini skirt and sheer black tights, tall platform boots laced to the knee || civ
- a floor-length black coat with a crimson lining that flares open over fitted tactical layers, cinched by a wide belt || @cyberpunk

## Tank tops

- a sleeveless thermal top, arms bare, forearms wrapped in worn tape || civ

## Tank tops (she) +

- a tan tactical vest hanging open over a torn cropped tank, one arm wrapped in bandaging, worn cargo trousers slung low at the hips || civ
- a fitted crop top with tactical harness straps crossing the bare back, over close-cut white tactical trousers with accent straps and a pistol holstered at the thigh || civ
- an olive tank top over cargo trousers, a pair of fingerless gloves and worn lace-up boots || civ
- a cropped olive tank top with a patch pocket at the chest, twin red armbands worn above the elbow
- a fitted halter-neck tank top with a high choker collar, one bare shoulder crossed by a thin strap || civ
- a black tank top under crossed harness straps bracing a cybernetic arm, paired with pale cargo trousers and a fingerless glove || @cyberpunk
- a sweat-damp white tank top, one strap slipping loose at the shoulder || civ
- a cropped white tank top under an open black sleeveless vest, dark fitted trousers slung with a wide belt || civ

## Bomber and flight jackets

- an olive bomber jacket over a black bodysuit and plate carrier, grey cargo trousers and a drop-leg holster rig strapped down one thigh || mil
- a heavy insulated flight jacket over a hooded pullover, cargo trousers and strapped knee pads
- a white flight jacket with a stencilled red-and-black shoulder patch marking a service unit || mil

## Bomber and flight jackets (she) +

- a cropped olive bomber jacket over a slim chest rig and a fitted tee, a band of bare midriff above olive cargo trousers slung with pouches || civ
- a cropped bomber-style jacket zipped only at the chest over a fitted sports top and briefs, midriff and legs bare, wrists wrapped in tape || civ
- a white-and-navy zip jacket layered with a yellow tactical harness, chest pouches, and unit patches at the shoulder || mil
- a navy flight jacket with a stiff high collar and a shoulder patch, chest straps buckled over a white flight suit and a wide belt cinched at the waist || mil
- a satin souvenir jacket embroidered with a pair of birds, worn open over a blouse and a short skirt || civ
- a cropped purple jacket with glowing seam piping down the sleeves, worn open over a fitted top and a mini skirt
- a russet flight jacket worn open over a strapped white tank, unit patches on both shoulders || mil
- a black cropped bomber jacket worn open over a fitted purple crop top, with over-ear headphones slung loose around the neck || civ
- An olive flight jacket with a shoulder patch worn open over a slip dress, sleeves pushed to the elbow. || mil
- a black bomber jacket worn open over a fitted white slip dress, dark thigh-high stockings beneath || civ
- an oversized olive bomber jacket worn over a fitted camo-print slip dress || civ

## Open jackets over crop tops

- an oversized open shirt sliding off one shoulder, draped loosely over a dark cropped tank || civ
- a black cropped tank top with a barcode tattoo and a stencilled unit number on the bare upper arm, a dark red jacket hanging off both shoulders and marked with a small hazard triangle patch
- a black jacket studded with spikes at the collar and shoulders, a small enamel pin at the breast, over a cropped top and a low-slung belt hung with metal loops || civ
- an oversized cropped black jacket with dull gold trim, worn open over a graphic crop top and a low-slung utility belt || civ
- an oversized black tactical jacket, unzipped over a cropped top baring the midriff, small mismatched patches on one sleeve and a segmented armored panel at one shoulder
- a black jacket with a high flared collar worn open over a fitted white top and short pleated skirt || @gundam
- a dark cropped halter top left bare at the back, a loose jacket sliding off both shoulders || civ
- an open puffer jacket worn over a bralette top and high-waisted shorts, its zipper trim glowing faintly || civ
- A cropped zip-up jacket worn open over a sports bra and biker shorts, paired with over-the-knee socks and training sneakers. || civ
- an open scavenged field jacket over a cropped bra top, low-slung cargo trousers slung with mismatched belt pouches and holster straps || @scav

## Cheap suits

- a cheap dark suit with the tie pulled loose, a thin wire running from one ear down inside the collar || civ
- a rumpled brown suit under an open plastic raincoat, both hems dripping || civ
- a narrow-shoulder charcoal suit with loosened cuffs and a pale office shirt, desk dust on the collar
- a faded ash-gray blazer over a light shirt, tie draped at the neck and a penciled note card in a coat pocket
- a low-cost navy pinstriped jacket with rolled cuffs, a short ledger pencil clipped to the lapel
- a drab gray suit jacket with a synthetic vest, narrow slacks and a chain of process stamps tucked at the side
- a practical beige business coat with a soft undershirt, collar turned up and a clipped office pass at the throat
- an old office suit with a white shirt, sleeves pushed above the wrist and a folded stack of forms at the breast
- a cheap black jacket with a rain-softened lapel, untucked short-sleeve blouse and a utility folder hanging from the cuff
- a slate and ivory two-piece suit, tie loosened and pockets swollen from printed permits and station maps
- a plain beige office jacket over a narrow tie and practical trousers, cuffs rolled from long hours at a terminal
- a narrow charcoal blazer worn open at the front, with a chipped badge tab at the cuff and a hand-drawn chart in the pocket
- a plainly tailored dark blazer and trousers, cut without ornament || civ

## Corporate skirt suits

- a tailored corporate blouse open two buttons at the throat over a narrow skirt slit high at the thigh, immaculate against the grime || civ
- a tailored pinstripe blazer cinched over a short pencil skirt, collar snapped high at the throat || civ @corporate
- a white jacket piped in orange over a high-collared undershirt, a wide belt cinched above a short pleated skirt || civ

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
  (occupies at least one hand), 'mil' (military-issue), 'blade' (an edged
  weapon - see below), 'none' (the empty bullet below - load-bearing, not
  inert: the Stance filter in roll_npc() reads it directly to keep an unarmed
  NPC off an armed pose).

  'blade' is the one flag here read through WEAPON_ROLES in generate-npc.py,
  which names the flag a Role's armament MUST carry. It reads the opposite way
  round from ROLE_LOCKS on Gear:

    ROLE_LOCKS    this bullet is ONLY for these Roles   (keeps others out)
    WEAPON_ROLES  these Roles get ONLY this bullet      (keeps them in)

  A lock protects an emblem from the wrong job; this protects a job from the
  wrong emblem. It does NOT reserve the blades - everyone else still rolls
  them freely, and a pirate with a cutlass is still a pirate with a cutlass.

  It exists because "a close-quarters blade specialist" kept coming back
  holding a service pistol and no blade. The Role is 'mil', the 'mil' tier
  restricts the pool to 'sidearm' bullets, and no blade is a 'sidearm' - the
  two filters intersected to nothing and fell back to the whole table. So the
  WEAPON_ROLES restriction OUTRANKS the 'sidearm' one rather than composing
  with it. Adding a Role here means checking that some bullet actually carries
  its flag; test_weapon_role.py fails on a dangling name in either direction.
-->

- x30 || none
- a sidearm holstered high on a chest rig || mil weapon simple sidearm
- a bullpup service carbine slung muzzle-down across {possessive} chest on its sling || mil weapon
- a bullpup service carbine held at a low ready in both hands, rail-mounted optic on top || hands gun mil weapon
- a katana with a colored glowing accent along its edge slung over {possessive} shoulder || mil weapon blade
- a katana with a colored glowing accent along its edge held in {possessive} hands || hands mil weapon blade
- a service pistol worn openly at the thigh || mil weapon simple sidearm
- a compact sidearm holstered at the hip and a utility belt of pouches at the waist || mil weapon simple sidearm
- a sheathed katana crossed against {possessive} back alongside a second, shorter blade || mil weapon blade
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
- a plain combat knife sheathed at the hip || weapon simple blade
- a folding push-dagger tucked into a boot sheath || weapon simple blade
- a compact hold-out pistol tucked into a shoulder rig, mostly hidden under a jacket || weapon simple
- a slim single-edged blade held low and reversed at {possessive} side || hands mil weapon blade
- a massive twin-barreled support cannon carried braced against {possessive} hip || hands gun mil weapon
- a heavy shoulder-mounted weapon pod worn like a backpack, twin barrels rising above {possessive} head, a sidearm holstered at {possessive} hip || mil weapon sidearm
- a compact sidearm gripped low and loose in one hand || hands gun mil weapon simple
- a bullpup service rifle with an under-barrel attachment held at a low ready in both hands || hands gun mil weapon
- a suppressed marksman rifle with an extended barrel held low in one hand || hands gun mil weapon
- a katana half-drawn from its sheath at the hip, {possessive} free hand steadying the scabbard || hands mil weapon blade
- twin sheathed swords worn crosswise at the hip, tasseled cords hanging from the hilts || mil weapon blade
- a sheathed katana carried loose in one hand, hanging point-down at {possessive} side || hands mil weapon blade
- a sheathed katana worn at the hip, {possessive} hand resting loose on the hilt || weapon blade
- a katana gripped and raised overhead in both hands mid-swing || hands weapon blade
- a katana held drawn low in one hand, its point trailing near the ground || hands weapon blade
- a katana held drawn across the body, a bundle of additional sheathed blades and a small demonic mask hanging at {possessive} hip || hands weapon blade
- a bundle of sheathed blades bound together with cord at {possessive} hip || weapon blade
- twin katanas, one gripped loose in each hand and lowered at {possessive} sides || hands weapon blade
- a sheathed katana at {possessive} hip, one hand gripping the hilt, poised to draw || hands weapon blade
- a pair of blades hovering motionless in the air to either side, faint markings etched along them || weapon blade
- an oversized two-handed blade held low in one hand, its point trailing near the ground, a second shorter sword sheathed at {possessive} hip || hands weapon blade
- a sheathed katana crossed against {possessive} back alongside a second blade drawn and gripped in {possessive} hand, its edge glowing faintly || hands mil weapon blade
- a katana held upright close to {possessive} shoulder, its blade bared and ready || hands mil weapon blade
- a sheathed katana rested up over one shoulder, gripped loosely by the scabbard in one hand || hands mil weapon blade
- twin sheathed swords worn crossed at {possessive} hip, hilts angled outward || mil weapon blade
- a katana held up close to {possessive} face, its blade angled back and ready in one hand || hands mil weapon blade
- a silver revolver raised and cocked, hammer drawn back || hands gun weapon simple
- a slender rapier raised en garde, tip angled skyward || hands weapon
- a long slim blade held loose at {possessive} side, its sheathed twin crossed low across {possessive} hip || hands weapon blade @neosamurai
- a slender rapier drawn point-first, its grip wrapped in worn leather || hands weapon
- an antique-pattern pistol raised and cocked in one hand || hands gun weapon simple
- an ornate curved saber, jeweled pommel bright against a worn leather scabbard at the hip || weapon
- a curved blade raised overhead, wreathed in a faint inner glow || hands weapon blade @grimdark
- a suppressed carbine gripped low and ready in both hands, a weapon light and optic mounted along the top rail || hands gun mil weapon
- a holstered pistol strapped high on {possessive} thigh || weapon simple sidearm
- a bulky futuristic bullpup rifle gripped two-handed, vents glowing along the stock || hands gun mil weapon @cyberpunk
- a long-barreled sniper rifle steadied on a mounted scope, {possessive} finger resting along the guard || hands gun mil weapon
- a massive single-barreled railgun leveled one-handed, vents glowing along its length || hands gun weapon @cyberpunk
- a second pistol worn holstered at the small of {possessive} back, grip peeking above the belt line || weapon sidearm
- a compact pistol held loose at {possessive} side, muzzle dipped toward the floor || hands gun weapon simple
- a heavy angular rifle, its rear coil glowing, gripped low at {possessive} hip with the muzzle dipped toward the deck || hands gun weapon @cyberpunk
- a slim, wire-wrapped katana with a faint glowing edge along the blade || hands weapon blade @cyberpunk
- a boxy bullpup carbine with a top-feeding curved magazine, held level in both hands || hands gun mil weapon
<!-- - a long-barrelled heavy revolver holstered under one arm in a worn leather rig || weapon simple sidearm -->
- a compact machine pistol with its wire stock folded, clipped to a chest sling || mil weapon simple sidearm
- a slim vented pistol held low in a gloved hand, its muzzle angled at the ground || hands gun weapon simple
- a service revolver holstered at the belt beneath an open jacket || weapon simple sidearm
- a long riot baton gripped in one hand and a scuffed transparent shield braced on the other arm || hands weapon
- an anti-materiel rifle with its bipod folded, slung muzzle-up across {possessive} back || mil weapon
- a stubby grenade launcher slung across the chest above a bandolier of fat cased rounds || mil weapon
- a flare pistol tucked into a chest pouch, its casing scuffed orange || weapon simple
- a pump-action shotgun raised muzzle-up beside {possessive} head in one gloved hand || hands gun weapon
- a lance-cannon battle rifle with folding foregrips and ceramic cooling fins, held in both hands with a slight upward muzzle tilt || hands gun mil weapon @lancer
- a gravitic marksman rifle wrapped in matte armor plates and a mirrored top optic, two-handed on a stabilized rest || hands gun weapon @lancer
- a triangulated dual-feed long rifle with snake-cased cartridges clipped to a compact chest rig || hands gun weapon @lancer
- an anti-armor coil rifle with violet induction glow and a thumb-wheel fire selector, carried at low ready || hands gun weapon @lancer
- a compact rail-lance carbine with a detachable monopod and blue-lit aiming ghost across the barrel || hands gun mil weapon @lancer
- a collapsible plasma-assisted hunting rifle with a telescoping stock and dust-streaked matte barrel || hands gun weapon @lancer
- a chrome smartcarbine with retractable holographic stock and a noise-canceling muzzle shroud || hands gun mil weapon @cyberpunk
- a modular pulse rifle built around a vertical foregrip and modular cybernetic fire-module || hands gun mil weapon @cyberpunk
- a mag-ramp repeater with stacked tungsten magazines and vented barrel rings, shoulders settled into two-handed stance || hands gun weapon @cyberpunk
- a ghost-scope sniper rifle with adaptive thermal lens and neural recoil dampener || hands gun weapon @cyberpunk
- a twin-stack rail sniper platform with shoulder brace and AR tether cable hanging from the optic || hands gun weapon @cyberpunk
- a microburst scattergun with ceramic barrel sleeve and integrated flash-dampening grid, held muzzle-forward || hands gun weapon @cyberpunk
- a data-tethered coil rifle wrapped in white-gold insulation, one hand braced to its power coupler || hands gun mil weapon @ghostinshell
- a ghost-network acoustic rifle with a ghostly sensor sphere hovering over the muzzle || hands gun weapon @ghostinshell
- a vibro-rifle folded like a fan, its emitter teeth unfolding as it locks into a two-handed ready || hands gun weapon @ghostinshell
- an electro-net launcher with side cartridges and flickering green targeting lens at the muzzle || hands gun weapon @ghostinshell
- a covert electromagnetic carbine with gyrostabilized frame and matte black heat shield || hands gun weapon @ghostinshell
- a kinetic smart-rifle that tags targets with floating HUD readouts on its translucent frame || hands gun weapon @ghostinshell
- a weathered spacefaring hunting rifle with curved chrome receiver and worn recoil absorber pad || hands gun weapon @cowboybebop
- a twin-barreled trench rifle with interchangeable choke vents and scarred wood grips, slung across {possessive} chest || hands gun weapon @cowboybebop
- a solar-hardened blaster carbine with folding tubular stock and sun-etched engraving along the fore-end || hands gun weapon @cowboybebop
- a long-range bounty rifle with taped drum magazine and thumb-operable gas-recovery valve || hands gun weapon @cowboybebop
- a heavy rail repeater with side ammo drum, chrome barrel, and a targeting microdrone dangling from its shroud || hands gun mil weapon @cowboybebop
- a shotgun-carbine hybrid with a ribbed drum mag, curved top rail, and weathered red trim || hands gun weapon @cowboybebop
- a magnetic harpoon rifle with a coiled cable reel and reinforced bipod, held at a hunting-ready two-handed grip || hands gun weapon
- a compact photon shotgun disguised as a press camera rig, barrel ports blooming as it charges || hands gun weapon
- a wicked curved scythe with a chained counterweight || hands weapon blade
- a broad rune-etched greatsword with a glowing detail along its edge || hands weapon blade
- a wood-stocked bolt-action rifle resting across {possessive} lap || mil weapon
- a compact semi-auto pistol gripped and held low at {possessive} side || hands gun mil weapon simple
- a long katana with a chained hilt strap, its blade angled against the ground || hands weapon blade
- a katana wreathed in glowing energy along its blade, gripped and thrust forward at full arm's extension, a second sheathed blade worn crosswise at the hip || hands weapon blade @neosamurai
- a massive ornate broadsword with a jagged glowing blade, gripped upright in one hand || hands weapon blade @neogothic
- a compact service pistol gripped and aimed level in both hands || hands gun mil weapon simple
- a bulky, boxy pulse pistol held loosely at {possessive} side || hands gun mil weapon
- a rune-etched blade glowing along its edge, held drawn and ready in one hand || hands weapon blade @grimdark
- a long blade crackling with lightning down its length, held raised and angled across the body || hands weapon blade @grimdark
- a long straight blade with a glowing edge, gripped upright in both hands || hands weapon blade @neogothic
- a slender energy blade blazing with a stark glow, gripped low and ready in one hand || hands weapon blade @grimdark
- an ornately engraved pistol raised beside {possessive} face, scrollwork tracing the slide || hands gun weapon simple @cyberpunk
- a slim red-bladed katana gripped by the hilt and laid flat across {possessive} back || hands weapon blade
- a modern battle rifle with an underslung optic and foregrip, gripped and braced across the body in both hands || hands gun mil weapon
- a large double-edged fighting knife gripped point-down in one hand || hands weapon blade
- a pistol gripped and raised in one hand, sighted dead level || hands gun weapon simple
- a long spear planted butt-down and held upright in one hand || hands weapon @grimdark
- a long slender blade held loose at {possessive} side, a quiver of arrows slung across {possessive} back || hands weapon blade @neosamurai
- a massive cross-hilted greatsword wreathed in flame, gripped overhead in one hand || hands weapon blade
- twin katana gripped low, one in each hand, held loose at {possessive} sides || hands weapon blade @neosamurai
- twin pink-finished pistols gripped low at the hips, one in each hand || hands gun weapon simple
- a scoped bullpup assault rifle cradled tight across {possessive} chest, spare magazines taped to the stock || hands gun mil weapon
- twin sheathed katana slung low across {possessive} back, one hilt bound in frayed red cord || weapon blade
- a slender double-edged blade crackling with an energy discharge along its length, held low at {possessive} side || hands weapon blade
- a compact pistol gripped and raised in both hands, sighted level at the viewer || hands gun weapon simple
- a two-handed ornamental sword with a glowing rune-etched blade, gripped point-down before {object} || hands weapon blade @neogothic
- a compact carbine held ready in both hands, muzzle low || hands gun mil weapon
- a compact sidearm gripped in both hands, muzzle tracking level || hands gun mil weapon simple
- a two-handed broadsword point-down, its blade lit with a steady inner glow, gripped in both weathered hands || hands weapon blade @neogothic
- a bare katana rested back across one shoulder, gripped at the hilt in one hand, a small star-shaped charm swinging from the pommel || hands weapon blade
- an oversized glowing-edged cleaver blade carried on an articulated mechanical arm rising past one shoulder || mil weapon blade
- a long straight blade held at {possessive} side, its broad edge lit from within and the guard sharply angular || hands weapon blade
- a compact slab-sided pistol held forward in one hand, a squared barrel shroud extending beyond the trigger housing || hands gun weapon simple
- a short straight sword with a translucent luminous blade and a compact dark guard, held in one hand || hands weapon blade
- a straight luminous sword with a plain crossguard held diagonally across {possessive} body || hands weapon blade
- a broad straight sword held upright in one hand, a cross-shaped luminous channel running through its blade || hands weapon blade
- a notched double-edged broadsword gripped point-down in one hand at {possessive} side || hands weapon blade @grimdark

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

  '|| admin' is a ROLE LOCK, and the only one on this table ('outlaw' is its
  Headgear counterpart). A locked bullet is
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
- a padded daypack clipped into a climbing harness, a row of small status diodes lit along its base
- a translucent handheld navigation slate showing a glowing wireframe schematic || hands
- {possessive} survival pack of coiled hoses and an antenna slung across both shoulders, an open-face flight helmet held loose in one hand || hands helmet mil
- an ornate goggled flight helmet with glowing dial readouts cradled against one hip || hands helmet
- a heavy banded wooden shield gripped by the forearm straps, faint sigils traced across its face || hands
- a boxy grey instrument pack strapped high on the back, a scuffed readout window set into its lid
- a compact back-mounted mechanical wing rig with layered pale vanes and circular illuminated hinges
- a single luminous artificial flower held delicately by its stem || hands
- a teardrop pendant and matching dangling earrings joined by a fine chain necklace
- a compact padded backpack with a stitched rear pocket and thick shoulder straps
- a compact life-support backpack with a looped breathing hose and cylindrical side canister
- a compact wrist computer with an illuminated rectangular screen set into a thick cuff

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

  The other five flags are PROP GATES, and they are what stops a placement
  describing scenery the rolled scene does not have - 'washes the towering
  display wall stacked behind her' against a snowbound crash site, 'pools on
  the ground around him' against a man floating weightless in an observation
  blister. Each is matched against the Backdrop's scene sentence by
  PLACEMENT_REQUIRES (or, for 'air', PLACEMENT_FORBIDS) in generate-npc.py:

    'ground'  - the light pools on the floor, so the subject has to have their
                weight on one. Matched on the VERB the scene gives them -
                standing, walking, crouched - which is also why it drops the
                weightless scenes (they say floating and drifting) and every
                half-body one (those describe only the background, so they
                carry no verb for the subject at all, and a half-body shot
                crops above the ground anyway).
    'wall'    - an interior surface behind the subject: a corridor, a bay, an
                alley, a room.
    'screens' - a stacked display wall: monitors, readouts, consoles, a board.
    'signage' - a lit skyline: signage, neon, billboards.
    'air'     - the inverse of the four above. The glow hangs as a haze, and
                hard vacuum has no atmosphere to scatter it, so this one names
                what the scene must NOT be. Weightlessness is not the test:
                most of the zero-gravity scenes are shirt-sleeve interiors, and
                a pressurised compartment holds a haze as well as a street
                does. It is the vacuum ones this drops.

  A gate reads the scene and nothing else. Reading the Outfit or the Gear too
  would make this table a dependent of theirs in TRAIT_DEPENDENTS; the two
  bullets that used to assert worn props - a suit's seams, a shoulder harness -
  were reworded to '{possessive} clothing' and 'the near shoulder' instead,
  which are true of every roll.

  The COLOUR is gated too, though not from here: filter_by_hue() narrows the
  '## Glow colour' pool to shades agreeing with a coloured light the scene
  already named, so a wall of schematics lit crimson no longer gets a
  teal-green glow in front of it. That needs no flag - it reads the shade's own
  words - which is why '## Glow colour' bullets stay single-segment.
-->

- x2 falls across one side of {possessive} face against warm dim ambient light on the other
- rakes across {possessive} chest and shoulder, the face left in warmer shadow
- catches {possessive} jaw and one shoulder from below
- rims {possessive} shoulders and hair from behind, the face lit only by what spills around it
- falls across {possessive} back and one shoulder, the front of the figure in warm shadow
  <!-- - catches {possessive} profile and one hand at a sharp angle, the rest of the figure left in shadow -->
  <!-- - washes across the scene behind {object}, throwing {possessive} outline into near-silhouette || scene -->
- pools on the ground around {object} and throws colour up onto {possessive} hands || scene ground
- stripes the wall behind {object} and catches one side of {possessive} face || scene wall
- hangs in the air as a haze across the whole depth of the shot || scene air
- washes across {possessive} cheek and the near shoulder at a low angle
- washes the towering display wall stacked behind {object} || scene screens
- picks out the seams and edges of {possessive} clothing in a hairline of light
- spills across the skyline in overlapping signage behind {object} || scene signage
- edges {possessive} profile in a thin line and leaves the rest of the figure in shadow
- lies along {possessive} shoulder and the side of {possessive} neck, the face turned out of it
- catches the underside of {possessive} chin and the line of {possessive} jaw from low down
- bleeds up the surface behind {object} in a soft bloom, {possessive} outline read almost as a silhouette || scene wall
- spills sideways across {possessive} face and near shoulder from a display wall just beside {object}, the far side of the face left in shadow || scene screens
- pools in broken reflections across the rain-slick ground at {possessive} feet || scene ground
- catches in {possessive} eyes, throwing hard-edged shadow across the brow

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
  a triage tent. Some 157 of these bullets are ungated and should stay that
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

  Most of the zero-gravity scenes now live in two groups, `## Freefall dives
  toward the viewer` and `## Floating weightless aboard ship`, one slot each;
  the sealed-EVA vacuum ones stay here because they carry a gate (see below).
  Put an `xN` on either reference, not on the members, if weightless portraits
  should come up more often.

  GROUPS. Families of near-duplicate scenes - rooftop ledges over a night city,
  shuttles on a landing apron, rings in the sky - are moved into group tables
  after the last bullet here (from `## Freefall dives toward the viewer` to
  just before `## Weather`), each entered by one `- => Name` reference, so a
  family of seven rolls as often as one distinct scene. Members keep the full
  `shot || scene || flags` shape. Three kinds of bullet stay ungrouped here:
  - Occupation-gated scenes (`medic`, `deskwork`, `cockpit` and the rest). The
    gate already keeps them to their Roles, and grouping them would cut a
    medic's chance of a medic scene to one slot.
  - Theme-tagged scenes. A reference's `@theme` tag is not read in this
    table: Backdrop's flags live in the third segment and `=> Name || @theme`
    has only two, so a themed Backdrop group would roll for every theme. Keep
    tagged scenes as plain bullets, or tag the members of a neutral group.
  - The x3 half-body staples at the top, which are weighted to be common.

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
- => Freefall dives toward the viewer
- => Floating weightless aboard ship
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} gliding along the exterior hull of a ship in a low zero-gravity recline, {possessive} back arched and body tilted no more than about 30 to 40 degrees off vertical across the frame, one gloved hand reaching up and back to grip an angular strut above {possessive} head while the other extends down to brace against a rail beneath {object}, legs drawn up and bent, head tilted back inside a sealed EVA helmet, visor down, gazing up and to the side, a full pressure suit worn close over {possessive} kit - behind {object} the dark hull curves away into the void, faint teal atmospheric light bleeding in from one side and streaks of motion-blurred light trailing past in the starfield. Dramatic rim lighting along {possessive} silhouette. || vacuum
- A dynamic, gently canted-angle character portrait || {Subject} {is_are} drifting weightless just outside an open airlock in a sealed EVA pressure suit and helmet, visor down, worn over {possessive} kit, body turned in a shallow roll no more than about 30 to 40 degrees off vertical with one gloved hand still on the hatch coaming and {possessive} legs floating free, tether line coiling loose behind {object} - beyond {object} the ship's plating falls away into the void and the lit limb of a planet curves across the background. Dramatic rim lighting along {possessive} silhouette. || vacuum
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} braced weightless between two struts of an orbital gantry, {possessive} body tilted no more than about 30 to 40 degrees off vertical and slowly rotating, one gloved hand overhead on a spar and one boot hooked under a rail, a sealed EVA pressure suit and helmet, visor down, worn over {possessive} kit - behind {object} the scaffold recedes into the dark and the starfield streaks past in faint motion-blurred lines. Dramatic rim lighting along {possessive} silhouette. || vacuum
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
- => Hunched at terminals
- => Posing with parked bikes
- A character portrait || {Subject} {is_are} sitting in profile, leaning back against the bent knee of a massive crouched military mech - the machine is boxy and heavily industrial, thick armored plating stencilled with unit markings, a single lit optic sensor and antenna protrusions rising from its head, its bulk looming just behind {possessive} shoulder. Behind them a rundown industrial refinery at dusk: tangled scaffolding, pipes and a tall numbered tower silhouetted against a low sun. Warm light rakes across {possessive} face and the mech's armor. || weather mechyard
- A dramatic low-angle character portrait || {Subject} {is_are} leaning back against the massive bent knee of a towering mech, looking down at the viewer, the shot angled steeply upward to emphasise the scale of both - the mech's leg fills the foreground in fine panel-line and rivet detail, a weapon barrel running off the top of the frame, a crescent moon faint through cloud above and a distant skyline low on the horizon. || weather mechyard
- A character portrait || {Subject} {is_are} sitting in the round hatch of an open viewport, one leg drawn up and hooked over the rim and the other hanging free outside it, {possessive} weight braced back against the frame in unhurried repose, gazing out past the opening. Tucked into the corner of frame below {object}, the domed head and lit photoreceptor of a small utility droid peeks into view. Beyond the hatch a pair of pale suns hang low over a sun-bleached horizon. || weather
- => Glancing back from a rooftop railing
- A character portrait || {Subject} {is_are} standing in a bombed-out doorway between two weathered concrete walls, framed by scattered bullet holes, faded warning signs and pinned notices - behind {object} a ruined cityscape stretches away into smoke and dust, a massive mech silhouette looming among the broken buildings and a huge low sun bathing the scene. In the foreground the blurred silhouettes of two seated figures frame the bottom corners, well out of focus. || weather
- A close-up character portrait || {Subject} {is_are} framed tight against a dense city street at night, tangled overhead wires crossing a hazy sky behind {object} and stacked signage glowing softly out of focus, the light grading cool across {possessive} face. || weather
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a frontier rail platform in ochre haze, an incoming transit's headlamps glaring through the dust and tangled overhead wire. || weather
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cramped fire-escape landing tangled with cabling and pipework, neon shop signage bleeding pink and green through the grating and mist. || weather
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a crowded transit terminal beneath tangled cable runs, neon signage in unfamiliar characters glowing above loitering figures and drifting smoke.
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a snowbound crash site, a downed transport burning against a wall of white peaks. || weather
- x3 A half-body character portrait || Behind {object}, out of focus, an immense flying superstructure eclipses the low sun over a sprawl of sun-baked rooftops, its long shadow stretching through the haze. || weather
- A character portrait || {Subject} {is_are} standing on a windswept ridge, a weapon lowered and faintly smoking at {possessive} side, looking out over a mist-filled valley - behind {object} a vast ring of wreckage hangs frozen in the air above a plunging waterfall, a pair of transports drifting past far below. || nogear weather frontline
- => Sitting on a rooftop ledge above the city
- => Beneath towering war machines
- A dynamic, low-angle character portrait || {Subject} {is_are} crouched low in a wide balanced stance atop a hovering skateboard ridden like a surfboard, knees bent and weight low, one arm flung out wide for balance and the other pointing off past the frame, a twin-thruster pack strapped across {possessive} back glowing faintly at the vents, hair and jacket sleeves whipped back by the wind - behind {object} a dense neon-lit cyberpunk skyline rises through drifting haze, towering signage in tangled scripts and corporate logos glowing through the mist, other riders on hoverbikes cutting past in the middle distance. || nogear weather
- A dramatic low-angle character portrait || {Subject} {is_are} crouched low behind an abandoned vehicle on a rain-slicked city street at night, weapon raised and sighting up at a colossal insectoid war-machine that fills the skyline ahead, its hull studded with glowing sensor clusters and thin segmented limbs trailing into the smoke-hazed street below, twin beams lancing down from its underside through the drifting mist - behind {object} a burning wreck casts long orange light across the wet pavement. || nogear weather frontline
- A character portrait || {Subject} {is_are} standing just inside the shattered nave of a ruined cathedral, dust hanging thick in broad shafts of light falling through the broken vaulting overhead, gazing up at an ancient gold-plated war-machine crouched motionless among the rubble ahead - a pair of cloaked, hooded companions stand just ahead of {object}, silhouetted small against its bulk. || weather
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} caught mid-kick in heavy powered armor, driving a braced boot into the armored hull of a massive segmented war-machine at close quarters, {possessive} sidearm still gripped and firing point-blank in the other hand, sparks and debris bursting from the impact - behind {object} a shattered cityscape unfurls in smoke and falling rubble, distant explosions blooming against a pale hazy sky. || nogear weather frontline
- x2 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a windswept plain of tall pale grass, a small stilted wayside shrine strung with paper streamers and a spear driven upright nearby trailing a strip of red cloth, a faint rainbow arcing through the haze beyond. || weather
- => Misty shrine ruins
- x2 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a sunlit ruin of towering stone archways and a broken aqueduct climbing a green mountainside, ivy and wind-bent trees reclaiming the old stonework. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a colossal robotic figure half-risen from a canal, only its ornate head, shoulders and clawed hands breaking the water, gold filigree tracing its dark plating; beyond it domed shrines and slender gold-latticed spires ring a plaza where two hooded robed figures pause at the water's edge beneath a hazy dusk sky, a dull red sun hanging low beside a darker second disc. || weather
- A three-quarter rear-view character portrait || {Subject} {is_are} standing in a mech's calibration bay, gazing up at a towering white-armored war-machine looming just ahead, one hand raised holding a slim holographic data-slate glowing with dense diagnostic readouts, {possessive} other hand braced at {possessive} hip - thick power cabling and chain hoists hang down around the mech's bulk, a wall-mounted display beside {object} scrolling systems-check telemetry, cool blue interior lighting washing the bay. || nogear mechwork
- A character portrait || {Subject} {is_are} standing atop the hull of a companion vessel in high orbit, sealed inside an EVA pressure suit and helmet, a cropped mission patch at the shoulder catching the thin light through the visor, looking back over one shoulder - beyond {object} a planet's night side curves away below, its cities burning in scattered threads of light against the dark. || vacuum
- A dramatic low-angle character portrait || {Subject} {is_are} standing amid drifting embers on a scorched battlefield in heavy rain, {possessive} back to the viewer, a long rifle gripped and lowered at {possessive} side - ahead of {object} churned mud and shattered rock fade into grey mist streaked with falling ash. || nogear weather frontline
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a floor-to-ceiling window wall overlooking a dense neon high-rise skyline at night, faint status readouts glowing at the edge of the frame.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a graffiti-tagged alley lit by tube neon signage bleeding red and teal through drifting mist.
- => Posing with parked cars
- => Vehicle seats at night
- => Walking toward colossal wrecks
- => Walls of monitors
- A dynamic character portrait || {Subject} {is_are} crouched low and reaching forward through the wreckage of a gutted server room, heavy clawed gauntlets braced against a fallen strut - behind {object} shattered windows let pale light leak through drifting dust and hanging cable. || nogear frontline
- A character portrait || {Subject} {is_are} perched on the raised knee-joint of a crouched companion mech in heavy night rain, one hand braced against its plating - behind {object} a neon-lit high-rise district fades into the downpour. || weather ownmech
- => Slumped in rain-slick alleys
- => Riding night transit
- A close character portrait || {Subject} {is_are} standing motionless before the lowered head of a colossal war-machine, its single optic burning close overhead, sparks showering down as welding light flares behind {possessive} shoulder - a steel catwalk and dim industrial scaffolding recede into the haze around {object}. || mechwork
- => Diagnostic chairs and rigs
- A dramatic low-angle character portrait || {Subject} {is_are} braced against the wind with one hand raised to shield {possessive} face, tribal markings streaking {possessive} cheek - beyond {object} a huge moon hangs low over a besieged orbital structure, beam weapons lancing down through drifting smoke. || weather
- => Sitting on idle machines
- A character portrait seen from behind || {Subject} {is_are} standing in silhouette against a huge glowing sun rising behind a ring of ruined structural arches, hair and coat trailing in the wind - a shattered cityscape stretches out to either side of {object} beneath the glow. || weather
- A dynamic character portrait || {Subject} {is_are} drifting limp and weightless above the planet's curve, arms trailing loose and a line of cabling reeling out behind {object}, shattered debris and a distant damaged vessel tumbling nearby, {possessive} suit scorched and torn across the chest. || vacuum
- A character portrait || {Subject} {is_are} standing before the looming bulk of a black companion war-machine, its twin shoulder cannons rising to either side and its optics burning faint red overhead - behind {object} a hazy night skyline glows low against the dark. || ownmech
- A close character portrait || {Subject} {is_are} framed tight in a cracked flight helmet, a thin readout glowing at the brow, half {possessive} face lit by a bright detonation tearing through a field of tumbling rock and debris just beyond {possessive} shoulder. || cockpit
- A dynamic character portrait || {Subject} {is_are} walking straight toward the viewer down a narrow overgrown alley, a heavy pack slung on {possessive} back - ivy and reclaimed neon signage crowd the walls to either side of {object}, an old arcade cabinet half-buried in creepers behind.
- A close character portrait || {Subject} {is_are} crouched low in a wrecked, fire-lit room, banks of dead monitors stacked behind {object} and a fire smoldering in the wreckage beyond.
- A close character portrait || {Subject} {is_are} tipped back in a mech cockpit seat, {possessive} gaze lifted past the camera - dense banks of glowing readouts and a night skyline crowd the canopy around {object}. || cockpit
- A character portrait || {Subject} {is_are} reclined deep in a low chair, legs crossed and stretched long, a hand of cards held loosely - mechanical prosthetic arm plating catches the light, and a heavy weapon rests propped against the chair beside {object}, screens of dense readouts glowing at {possessive} back.
- A close character portrait || {Subject} {is_are} leaning back into a mech cockpit seat, rain-damp hair swept across {possessive} face, one gloved hand braced on the console - beyond the canopy a night skyline glows through the rain. || weather cockpit
- A character portrait || {Subject} {is_are} sitting perched on a heap of mangled wreckage, one hand raised to {possessive} collar - a sun-bleached desert stretches out behind {object}, distant explosions blooming pale against the sky. || weather
- A dramatic low-angle character portrait || {Subject} {is_are} crouched on a narrow icy ledge high above the city, a pistol held ready in one hand, glancing back over {possessive} shoulder - a dense high-rise skyline drops away into the night far below {object}. || nogear weather frontline
- A character portrait || {Subject} {is_are} seated in a shuttle's passenger cabin, poring over a thick bound technical manual balanced on one knee, a travel bag propped against the seat, a richly robed diplomatic passenger seated close beside {object} - beyond the windows a scatter of escort ships hangs against the stars.
- A close, low-angle character portrait || {Subject} {is_are} reclined deep in a mech cockpit's padded seat, sealed head to toe in scuffed dark pressure armor, one gloved hand fallen slack across {possessive} lap, a dense asteroid field drifting past the canopy overhead - beside {object} a second pilot leans in close, watching the field pass. || cockpit
- A three-quarter character portrait || {Subject} {is_are} seated at a terminal, working a hovering holographic display with one hand, a hulking rust-streaked companion mech looming close behind {possessive} shoulder, its optics glowing faintly in the low light - around {object} banks of server racks glow in the dark. || nogear ownmech
- => Riding bikes at speed
- A character portrait || {Subject} {is_are} half-turned against open space, a tattered scarf-cloak streaming out weightless behind {object}, hair drifting loose in the void - beyond {object} a churning red nebula glows low around a dark dwarf star.
- A dramatic low-angle character portrait || {Subject} {is_are} crouched low on a rain-slick rooftop ledge, bracing a long rifle sighted down into the streets below, weight settled low over one knee - beneath {object} a dense neon-lit cityscape glows through the downpour. || nogear weather frontline
- A character portrait || {Subject} {is_are} standing braced with both hands flat on a lit control console, framed against a floor-to-ceiling viewport of a rain-swept neon high-rise skyline beyond. || nogear weather
- A dynamic, close character portrait || {Subject} {is_are} raising a compact pistol close to the camera, fine circuitry glowing faintly along {possessive} fingertips and knuckles - behind {object} a pair of masked companions stand watch at a railing overlooking a dense rain-slicked neon cityscape. || nogear weather frontline
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} tumbling backward through open air in cracked powered armor, twin beams of light searing across {possessive} torso and shattering plating away in jagged fragments, hair whipped wild by the fall - far below {object} a dark cityscape glows red beneath the drifting debris. || weather frontline
- A character portrait || {Subject} {is_are} reclined loose in a cockpit's crash seat, one hand reaching lazily out into the glow, banks of console screens and readouts ringing {object} on every side. || cockpit
- A character portrait || {Subject} {is_are} standing at a rooftop ledge, a data-slate held loose in one hand and a sidearm holstered at {possessive} hip, a dark fabric wrap pulled up over the lower face - beyond {object} a dense neon-lit skyline glows red through the night haze. || weather frontline
- A dynamic character portrait || {Subject} {is_are} walking straight toward the viewer down a dim industrial hangar bay, a flight helmet carried loose under one arm, a hulking quadrupedal war-machine striding through drifting steam close behind {object}, overhead lights raking down through the haze. || nogear cockpit
- => Beneath ships hovering overhead
- A close character portrait || {Subject} {is_are} standing perfectly still as an oversized mechanical hand reaches into frame to project a thin beam of light directly into {possessive} eye, a small stamped code marked at {possessive} cheekbone, the moment held in tense stillness.
- A character portrait seen from behind || {Subject} {is_are} standing atop a rooftop ledge high above a sprawling neon-red cityscape at night, a sidearm held loose and low in one hand, gazing down at the grid of light far below. || nogear weather frontline
- A character portrait || {Subject} {is_are} standing beside a towering crimson war-machine, its cockpit visor glowing pale blue in the dark, {possessive} fitted suit catching the light - around them the dim outline of a nighttime hangar recedes into shadow. || ownmech
- A character portrait seen from behind || {Subject} {is_are} standing at a viewport beside a hulking white powered-armor companion, one hand raised flat against the glass, a stencilled unit number marking {possessive} shoulder - beyond the glass a sunlit planet curves away below, city lights scattered across its night side. || ownmech
- A character portrait || {Subject} {is_are} standing with both cybernetic prosthetic hands raised and pressed together in prayer, forearms segmented and scarred with use, a ring of glowing script arcing overhead like a halo - behind {object} a congregation of hooded, bowed worshippers recedes into a dim golden haze, their faces indistinct. || clergy
- A character portrait || {Subject} {is_are} seated in the open cockpit of a parked attack craft on a rocky ridge at night, flight helmet secured and visor down, a stitched unit patch at the shoulder of {possessive} flight jacket, gazing off past the frame - behind {object} a huge banded planet glows low over the ridge, faint stars scattered through the dark. || weather cockpit
- A character portrait || {Subject} {is_are} standing with a spent cigarette held loosely at the corner of {possessive} mouth, a pair of heavy mechanical support struts trailing cabling rising to either side of {possessive} head - behind {object}, out of focus, a dense hazy cityscape glows faintly through drifting mist.
- => Rings in the sky
- A character portrait seen from behind || {Subject} {is_are} standing at the foot of a towering dormant war-machine in a cluttered maintenance bay, a ladder propped against its leg and a flight helmet held loose in one hand at {possessive} side, dim standby lighting glowing from vents across its hull - a weathered poster and status monitors line the walls to either side, steam venting low across the floor. || nogear cockpit
- A character portrait seen from behind || {Subject} {is_are} standing at a rocky overlook, a long tattered cloak snapping loose in the wind behind {object}, gazing out over a hazy desert city ringed by tall spires - overhead a massive banded planet with a debris ring dominates the sky, smaller moons scattered around it, the whole scene washed in the deep orange of a dying sun. || weather
- A dynamic character portrait || {Subject} {is_are} standing on the broken rocky surface of an airless moon, a pistol gripped and lowered at {possessive} side, glancing back over one shoulder - behind {object} a searing beam of weapons fire lances low across the horizon, kicking up a spray of debris where it grazes the ground. || nogear frontline
- A character portrait || {Subject} {is_are} reclined loosely in a cockpit seat, one leg - a segmented cybernetic prosthetic - propped up against the console, {possessive} head tipped back and gaze drifting past the canopy - beyond {object} a dense starfield stretches away into the dark, banks of status readouts glowing at the edges of the frame. || cockpit
- A dynamic character portrait || {Subject} {is_are} standing amid drifting debris and fire on a cratered surface, glancing sharply toward the viewer, one heavy geometric shoulder plate catching the light - behind {object} explosions bloom low across the ground and a bright streak burns across the black sky above. || frontline
- => Standing at a rooftop edge
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} punching forward through the air in heavy powered armor plating, {possessive} lead arm driven out toward the viewer in a braced clawed gauntlet and the trailing arm cocked back, {possessive} legs trailing behind in motion, hair whipped back - behind {object} bright beams of weapons fire streak past low across a debris-strewn battlefield. || weather frontline
- A character portrait || {Subject} {is_are} reclined deep in a battered gaming chair, arms crossed and half-lidded, a translucent visor band glowing faintly across {possessive} brow and cabling trailing from a jack at {possessive} temple - around {object} a bank of terminal displays glows with dense scrolling data, a burned-down cigarette smoldering in a nearby ashtray. || nogear
- A character portrait || {Subject} {is_are} standing with {possessive} bare mechanical hands folded low in front, fully articulated at every joint - behind {object} a hulking twin-turreted combat vehicle looms close, its optics glowing steady in the dark, a pair of moons rising in the night sky beyond. || weather
- A character portrait || {Subject} {is_are} reclined in the driver's seat of a battered open-top vehicle, both hands laced behind {possessive} head, elbows out, gazing off past the frame - behind {object} a ruined cityscape rises in ivy-choked towers under a hazy morning sun, birds scattering across the empty street ahead. || weather
- => Walking wet streets at night
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-slicked stairway alley lined with paper lanterns and a tiny bar counter, a hazy city skyline glimpsed below through the wet stone steps. || weather
- A close-up character portrait || {Subject} {is_are} framed tight in profile, raising a segmented mechanical hand close to {possessive} own face, fingers half-curled - behind {object}, out of focus, a dense cyberpunk high-rise district glows through drifting haze.
- => Elevated trains between towers
- A character portrait || {Subject} {is_are} standing on a raised gantry platform beside the crouched bulk of a towering war-machine filling a dim maintenance bay, its single optic sensor lit and a heavy cannon barrel angled down past {object}, faded unit markings stencilled across its scarred armor plating, stacked crates and hazard placards cluttering the shadowed bay floor below. || mechwork
- A character portrait || {Subject} {is_are} walking down a wide ceremonial ramp through falling snow, a combat helmet held loosely in one hand at {possessive} side, faction banners snapping either side and hooded onlookers lining the way, the hulking silhouette of a towering war-machine looming backlit behind {object} in the drifting snow and haze. || weather ceremony
- A character portrait || {Subject} {is_are} standing in profile, a colossal crow-like beast looming close behind {possessive} shoulder, its single eye burning with a saturated glow in the gloom - beyond {object} a ruined stone courtyard fades into rubble and haze. || weather
- A close character portrait || {Subject} {is_are} seen in profile close beside the angular head of {possessive} companion mech, its optics burning twin points in the dark, a stencilled shoulder patch marking {possessive} flight jacket - beyond them a hazy blue-lit hangar recedes into the dark. || cockpit
- A dynamic character portrait || {Subject} {is_are} walking straight toward the viewer down a dim shipboard corridor, a pistol held low and loose in one hand, a second armed companion keeping pace just behind {possessive} shoulder - pipework and hazard striping line the walls to either side, receding into a hazy blue light. || nogear frontline
- A character portrait seen from behind || {Subject} {is_are} standing atop a snow-dusted rooftop unit, hair streaming in the wind, a sheathed blade held loose at {possessive} side, a small cat perched watchful nearby - below {object} a dense neon-lit high-rise cityscape glows through drifting snow. || nogear weather swordwork
- => Standing in neon street canyons
- A dynamic, low-angle character portrait || {Subject} {is_are} leaning far out over the drop, one hand locked around a strut and {possessive} body braced forward, gazing straight down through a vast light-streaked shaft at a glittering neon cityscape far below.
- A character portrait || {Subject} {is_are} sitting perched on the folded knee of a crouched companion mech, one hand resting easy against its armored plating as its head looms close alongside {object}, twin optics glowing steady - beyond {object} a dense city skyline spreads out below in the fading dusk light. || weather ownmech
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a plant-filled loft apartment with a domed window overlooking a rain-streaked neon high-rise skyline, candlelight and string lights glowing warm across cluttered bookshelves. || weather
- A half-body character portrait || Behind {object}, out of focus, is a fog-bound harbor skyline of towering high-rises, an elevated highway curving low over dark water and a blocky industrial platform lit from beneath. || weather
- A dynamic, low-angle character portrait || {Subject} {is_are} crouched low on a rain-slicked rooftop platform, one hand gripping a glowing energy blade planted point-down and weight braced forward, ready to spring - behind {object} a dense neon-lit cyberpunk skyline rises through drifting haze, a colossal holographic face glowing between the towers and small hovercraft drifting past in the middle distance. || nogear weather frontline
- => Gazing out of viewports
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-slicked old-town street lined with lantern-lit shopfronts and parked bicycles, a cherry blossom tree overhanging the road and a distant illuminated tower glowing hazy through the mist. || weather
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
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a dim institutional corridor, flickering fluorescent tubes above a scuffed door and a lone waste bin.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a weathered stilt-built river town, houseboats moored along a plank dock beneath sagging corrugated roofs. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a stone arch bridge spanning a slow river, glass towers rising beyond a green, overgrown embankment. || weather
- A wide character portrait || Behind {object}, softly blurred well out of focus, is a towering white combat walker suspended in a service gantry, ground crew in coveralls swarming its limbs across a hazard-striped deck. || mechyard
- A wide character portrait || Behind {object}, softly blurred well out of focus, is a pair of heavy gunships banking hard through a bank of storm cloud, cannon pods and missile racks bristling from their articulated weapon arms. || weather
- A wide character portrait || {Subject} {is_are} wading ashore from a beached inflatable boat, rifle held low and ready, boots crunching over dockside rubble - gantry cranes and floodlights glowing through rain and fog behind {object}. || nogear weather frontline
- A close character portrait || {Subject} {is_are} sitting atop a mound of stripped combat-frame wreckage, boots planted on a skeletal actuator arm, scavenged machine parts sprawling into darkness under a pair of close, cratered moons. || weather salvage @scav
- A wide character portrait || {Subject} {is_are} standing at a rain-slicked overlook rail with a great cat settled at heel, watching a glowing ring-gate span a sea of cloud toward a floating district of lantern-lit pagoda towers. || weather @neosamurai
- A wide character portrait || {Subject} {is_are} striding forward with one hand looped through a great cat's harness at {possessive} side, cloak snapping back-lit by a churning vortex of light framed between two rune-carved standing stones - across a windswept, fog-slicked stone concourse. || weather
- => Cratered moons under the stars
- A wide character portrait || {Subject} {is_are} standing motionless in the rain beneath a vast hovering vessel, its underside ringed in light, a dense skyline glowing behind {object}. || weather @gundam
- A wide character portrait || {Subject} {is_are} sitting cross-legged on a sunlit wooden engawa with a sketchbook and iced tea set at {possessive} side, a mossy stream and stone-set waterfall running just beyond the rail.
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
- A character portrait || {Subject} {is_are} standing ankle-deep in the flooded arcade of an abandoned shopping street, still water mirroring the dead signage overhead, a shaft of grey daylight falling through a collapsed section of roof far ahead. || weather
- A close character portrait || {Subject} {is_are} seated in the dark of a parked surveillance van, a bank of monitors washing {possessive} face in pale grey light, cable looms underfoot and cold cups crowding the console. || deskwork
- A half-body character portrait || Behind {object}, out of focus, is the wrecked hall of a natural history museum, a shattered tree-of-life mural across the far wall and the slumped bulk of a disabled multi-legged combat walker among the fallen masonry. || warzone
- x2 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a maintenance hangar, a boxy industrial work-mech kneeling in its cradle with gantry crews along its arms and arc-welding flare stuttering off the walls. || mechyard
- A character portrait || {Subject} {is_are} standing on a seawall above a vast reclaimed-land project, dredgers and gantry cranes ranked across flat grey water behind {object} and a typhoon sky stacking up dark on the horizon. || weather
- => Street food counters
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
- A character portrait || {Subject} {is_are} kneeling in the red-lit cabin of a casualty flight with one knee braced against a stretcher rail, squeezing a bag valve two-handed over a strapped-down casualty as the airframe shudders around {object} - crew silhouettes and a swinging drip line crowd the bay behind {object}. || nogear medic
- A character portrait || {Subject} {is_are} standing over a reclined cyberbrain rig with {possessive} arms folded, watching a patient's neural map turn slowly in the air at head height, the skull cradle's fine manipulator arms folded back and waiting - the theatre's tiled walls recede cold and green behind {object}. || medic
- A character portrait || {Subject} {is_are} crouched at a colony shelter's triage line knotting a sorting tag onto a seated evacuee's wrist, a marker clamped between {possessive} teeth - rows of blanketed figures and stacked bedding recede behind {object} beneath a taped-up casualty board. || nogear medic
- A character portrait || {Subject} {is_are} washing to the elbow at a bay sink with {possessive} sleeves shoved back and {possessive} head down, a splashed apron still tied on - an instrument tray and a heap of soiled gowns crowd the counter beside {object}, the theatre doors swinging shut behind. || nogear medic
- A character portrait || {Subject} {is_are} sitting on an upturned crate outside a construction site's first-aid post splinting the forearm of a labourer seated opposite, a torn hi-vis jacket bundled at their feet - beyond them a toppled work-frame lies half across the road under floodlights and drifting dust. || nogear weather medic
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a back-alley implant clinic's shopfront, a reclining chair visible through smeared glass beneath a ring of surgical lamps and shelves of boxed limbs. || medic
- A character portrait || {Subject} {is_are} sitting back against a corridor bulkhead with {possessive} legs stretched out and {possessive} gloves still on, head tipped back and eyes shut - down the passage behind {object} a lit theatre door stands propped open and a mop bucket waits against the wall. || medic
- A dramatic low-angle character portrait || {Subject} {is_are} braced in the open side door of a hovering ambulance craft, one hand on the frame and a jump line clipped at {possessive} harness, looking down past the skids - far below {object} a wet street glows with the strobing lights of a cordon. || nogear weather medic
- A character portrait || {Subject} {is_are} standing waist-deep among stacked frame torsos in a breaker's yard, a cutting torch idle in one gloved hand and a hauling strap slung across {possessive} chest - behind {object} a gantry crane swings a severed limb section slowly against a flat white sky. || nogear weather salvage
- A character portrait || {Subject} {is_are} crouched inside the opened chest cavity of a downed war-machine, {possessive} headlamp throwing a hard cone across severed cable looms as {subject} works a connector free - the machine's ribbed interior recedes into the dark around {object}. || nogear salvage
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a tidal scrapyard at low water, half-sunk hulls and stripped actuator limbs bedded in grey mud beneath a wide colourless sky. || weather salvage
- A character portrait || {Subject} {is_are} sitting on an upturned crate beside a weighing scale heaped with salvaged servo parts, arguing a price with a dealer whose back fills the foreground out of focus - behind {object} a tarpaulin stall of sorted scrap glows amber under strung work lights. || salvage
- A character portrait || {Subject} {is_are} walking a narrow catwalk between towering stacks of crushed vehicle bodies, a coil of recovered cable looped over one shoulder and a sorting hook swinging in {possessive} free hand - rust-red canyon walls of compacted metal rise to either side of {object} into a hazy sky. || nogear weather salvage
- A character portrait || {Subject} {is_are} standing on the sun-blasted upper hull of a beached colony section prying at a seam with a long bar, {possessive} shadow thrown long across the plating - behind {object} the structure's torn ring curves away into a heat-shimmering desert. || nogear weather salvage
- A character portrait || {Subject} {is_are} crouched in the sand-drifted cockpit of a half-buried war-machine brushing grit off a seized control yoke with the back of one glove - the frame's exposed ribs break the dune line behind {object} and a hot white sky flattens the horizon. || nogear weather salvage
- A character portrait || {Subject} {is_are} walking a stripped synthetic chassis upright on a hand truck through a chop shop's roller door, its faceplate gone and its cabling bundled at the neck - racks of mismatched limbs and torsos line the walls behind {object} under bare fluorescent tubes. || nogear salvage
- A character portrait || {Subject} {is_are} standing at the rail of a scrap barge beneath a bay bridge with a cargo hook laid across {possessive} shoulder, watching a crane swing a crushed cab aboard - the far shore's gantries and stacked containers fade into brown smog behind {object}. || nogear weather salvage
- A character portrait || {Subject} {is_are} kneeling on wet plating in a flooded service culvert hauling a severed cable loom hand over hand out of the silt, {possessive} headlamp throwing a hard cone down the tunnel - water runs steadily past {possessive} knees into the dark. || nogear salvage
- A character portrait || {Subject} {is_are} sitting in the open jaw of a parked grapple crane with {possessive} boots dangling over the drop and a tin of food balanced on one knee, looking out across the yard - ranked rows of stripped hulls stretch away below {object} into a rust-coloured evening. || nogear weather salvage
- A close character portrait || {Subject} {is_are} holding a pulled optic module up to a strung work light, turning it to read the maker's stamp etched around its housing - behind {object} a night market stall of sorted chrome glitters on a folding table, buyers browsing out of focus. || nogear salvage
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a bonded salvage lot at first light, numbered wrecks ranked in rows under frost and a chain-link fence running away into the mist. || weather salvage
- A character portrait || {Subject} {is_are} standing in a hangar doorway with a sealed document wallet tucked under one arm, taking in the bay ahead without stepping into it, {possessive} lanyard badge turned face-out at {possessive} chest - work crews and a shrouded war-machine stand paused in the light behind {object}. || nogear inspection
- A character portrait || {Subject} {is_are} seated across a bare interview table from an empty chair, a recorder set squarely between them and {possessive} hands folded on a closed folio - the room's acoustic panelling and one high window recede flat and grey behind {object}. || inspection
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a records vault of racked archive boxes and rolling ladder rails, a single strip light burning away down a long aisle. || inspection
- A character portrait || {Subject} {is_are} holding a stamped compliance placard up against a machine housing on a factory floor, comparing it to the serial plate at eye level - conveyor lines and a shift-change crowd blur away behind {object} under flat sodium light. || nogear inspection
- A character portrait || {Subject} {is_are} standing at a rain-lashed dockside barrier with a tablet held low and shielded under one arm, watching a container crane work - floodlights burn cones through the downpour behind {object} and a queue of idling haulers stretches back to the gate. || nogear weather inspection
- A character portrait || {Subject} {is_are} descending a spiral stair into a colony's lower service level, one hand on the rail and a survey lamp raised in the other, condensation beading the pipe runs that crowd the shaft around {object}. || nogear inspection
- A character portrait || {Subject} {is_are} standing at an observation gallery rail above an assembly floor, a stylus paused over a checklist and {possessive} attention down on the line below - ranked frame chassis crawl past on the belt beneath {object} under flat white light. || nogear inspection
- A character portrait || {Subject} {is_are} crouched at an opened bonded container with the broken seal still hanging from its latch, sweeping a scanner wand across the crates stacked inside - the warehouse aisles recede behind {object} under caged lamps, a forklift idling out of focus. || nogear inspection
- A character portrait || {Subject} {is_are} holding a tape measure taut across a cracked weld on a pressure bulkhead and photographing it one-handed, the flash catching the seam - pipe runs and painted frame numbers crowd close behind {object}. || nogear inspection
- A character portrait || {Subject} {is_are} seated at a hearing-room table with a stack of tabbed folders squared at {possessive} elbow and one hand raised mid-question, a gooseneck microphone bent toward {object} - tiered empty benches and a hung institutional seal recede behind {object}. || inspection
- A character portrait || {Subject} {is_are} standing in a colony's reactor annex reading a dosimeter held up at arm's length, {possessive} badge clipped face-out at {possessive} collar - shielded conduit and painted hazard chevrons climb the wall behind {object} under a steady amber lamp. || nogear inspection
- A character portrait || {Subject} {is_are} stepping down from an idling inspection car at a road checkpoint with a stamped manifest held flat against the door, rain beading across the folder's cover - a queue of covered haulers stretches back past {object} into the downpour. || nogear weather inspection
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a permit office papered floor to ceiling with pinned notices and expired certificates, a numbered ticket display glowing above a shuttered counter. || inspection
- A character portrait || {Subject} {is_are} standing behind a narrow bar counter polishing a glass with both elbows loose, the back-bar shelves stacked with mismatched bottles under a strip of warm tube light - a patron's shoulder blurs across the foreground and rain streaks the window beyond {object}. || nogear weather barkeep
- A character portrait || {Subject} {is_are} leaning across a booth table with both palms flat on the laminate, saying something low to a figure seated out of focus opposite - behind {object} the bar's back room glows in stacked neon and a beaded curtain hangs half-parted. || barkeep
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a shuttered bar at closing, chairs upended on the tables and a lone pendant lamp burning over a wiped-down counter. || barkeep
- A character portrait || {Subject} {is_are} sitting at the end of {possessive} own counter with a ledger open and a cash tin beside it, glancing up at the door - behind {object} a wall of pinned business cards, chits and faded photographs climbs to the ceiling beside a dead payphone. || nogear barkeep
- A character portrait || {Subject} {is_are} drawing a cellar hatch shut behind {object} with a crate of bottles balanced on one hip, the stairwell's bare bulb still swinging - overhead the bar's floorboards leak music and the moving shapes of feet. || nogear barkeep
- A character portrait || {Subject} {is_are} standing under a taped-over security monitor at the end of the bar with {possessive} arms folded, watching four grainy feeds of the alley and the door while the room's warm noise blurs past {possessive} shoulder. || barkeep
- A character portrait || {Subject} {is_are} drawing a beer at a wall of taps with {possessive} eyes not on the glass but on a booth across the room, foam climbing the rim - the back-bar mirror behind {object} carries the blurred reflection of two figures leaning close together. || nogear barkeep
- A character portrait || {Subject} {is_are} setting two glasses down on a corner table and sliding a thin data chit beneath one of them with two fingers, {possessive} expression giving nothing away - cracked vinyl and a low pendant lamp frame the booth, the room's noise blurred beyond. || nogear barkeep
- A character portrait || {Subject} {is_are} standing at the head of the bar's basement stair beneath a dead neon sign, arms folded and one shoulder against the doorframe, watching the wet street - rain runs off the awning past {object} and headlights slide by out of focus. || weather barkeep
- A character portrait || {Subject} {is_are} working the pass of {possessive} own noodle counter beneath an expressway, ladling broth one-handed with steam rolling up past {possessive} face - a row of empty stools and a hand-lettered price board recede behind {object}, traffic rumbling overhead. || nogear weather barkeep
- A character portrait || {Subject} {is_are} leaning back against the back-bar shelves with a handset trapped between {possessive} shoulder and ear, writing a name on the inside of {possessive} own wrist - stacked bottles and a strip of warm tube light glow behind {object}, the room dark beyond. || nogear barkeep
- A character portrait || {Subject} {is_are} sitting on a stool at the closed end of the counter under a half-drawn shutter, thumbing a stack of chits and marking one - the room stands dark behind {object} but for a single lamp and the shutter's slatted light laid across the floor. || nogear barkeep
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is the bar's back office, a wall of unlabelled keys on hooks beside a battered safe and a rack of pigeonholes stuffed with folded notes. || barkeep
- A character portrait || {Subject} {is_are} clamped by one boot to the spine of a drydocked warship in a sealed EVA pressure suit and helmet, visor down, a torque tool floating tethered at {possessive} hip, looking back along the hull - beyond {object} the ship's bare ribs recede into the scaffold and a work light glares white off the plating. Dramatic rim lighting along {possessive} silhouette. || vacuum
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} pushing off toward the viewer through a debris field in a sealed EVA pressure suit and helmet, visor down, one gauntlet thrust out at the camera and {possessive} tether whipping loose behind {object}, {possessive} body tilted no more than about 30 to 40 degrees off vertical - shattered panel fragments turn slowly past {object} against the starfield. || vacuum
- A character portrait || {Subject} {is_are} standing magnet-soled on the outer hull of a colony cylinder in a sealed EVA pressure suit and helmet, visor down, one gauntlet raised against the glare and a survey slate clipped at {possessive} thigh - the cylinder's vast painted flank curves away behind {object} toward a distant mirror panel burning white. || vacuum
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} riding a manoeuvring pack away from the camera and looking back over one shoulder in a sealed EVA pressure suit and helmet, visor down, {possessive} body tilted no more than about 30 to 40 degrees off vertical with thruster plumes feathering white at {possessive} hips - behind {object} a half-built station truss recedes into the dark. Dramatic rim lighting along {possessive} silhouette. || vacuum
- A character portrait || {Subject} {is_are} floating tethered beside a shattered solar array in a sealed EVA pressure suit and helmet, visor down, one gauntlet steadying a torn frame member and {possessive} legs drifting loose - behind {object} the array's broken wing trails away in glittering fragments and a planet's terminator cuts a bright line across the dark. Dramatic rim lighting along {possessive} silhouette. || vacuum
- A character portrait || {Subject} {is_are} leaning in over a shoulder-height plot table with both fists planted either side of a lit tactical overlay, calling something off past the frame - ranked operator stations glow blue behind {object} in the dim of a flag bridge. || nogear deskwork
- A character portrait || {Subject} {is_are} seated at a combat information console in a headset, one hand cupped over the earpiece and the other steady on a trackball, a wall of plot repeaters washing {possessive} face green in the dark. || nogear deskwork
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a night watch room, three unmanned consoles glowing beneath a wall clock and a rack of dead handsets. || deskwork
- A character portrait || {Subject} {is_are} standing at a division office whiteboard with a marker capped in one hand, a duty roster and a pinned street map crowding the wall beside {object} - behind {possessive} shoulder mismatched desks stand heaped with folders under a slowly turning fan. || nogear deskwork
- A character portrait || {Subject} {is_are} reclined at a listening station with {possessive} headphones pushed off one ear and {possessive} boots crossed on the desk edge, spectrogram traces crawling across three stacked displays - the booth's soundproofing recedes into shadow behind {object}. || deskwork
- A character portrait || {Subject} {is_are} seated in an editing suite with a segmented playback rig lowered over {possessive} temples, both hands paused above a scrub wheel, layered recording windows hanging in the air around {possessive} head and throwing shifting colour across {possessive} face. || nogear deskwork
- A character portrait || {Subject} {is_are} standing behind a seated operator's chair on a dim watch floor, one hand on the seat back and {possessive} attention up on the big board, a mug of tea going cold on the console below - rows of glowing stations stretch away behind {object} into the dark. || nogear deskwork
- A character portrait || {Subject} {is_are} bent close over a paper plotting chart under a hooded lamp, drawing a bearing line with a parallel rule and a handset trapped between {possessive} shoulder and ear - the rest of the plot room falls away into red-lit gloom behind {object}. || nogear deskwork
- A character portrait || {Subject} {is_are} wedged behind a desk buried under stacked paper with a handset trapped at {possessive} ear, stamping a form without looking down at it - mismatched desks, a dying pot plant and a wall of pinned duty notices crowd the office behind {object}. || nogear deskwork
- A character portrait || {Subject} {is_are} standing at a wall-sized district map with a pin held between finger and thumb, threads already strung taut between a dozen markers across it - the ops room falls away behind {object}, one lamp burning over a table of spread photographs. || nogear deskwork
- A character portrait || {Subject} {is_are} seated at a dispatch console with one hand flat on a transmit key and {possessive} eyes up on the status board, unit markers glowing in ranks above {object} - another operator's back blurs across the foreground and the room's handsets hang dead on their hooks. || nogear deskwork
- A character portrait || {Subject} {is_are} leaning in over a seated radio operator's shoulder with one hand braced on the equipment rack, a headset held to one ear and the other ear open to the room - banks of receivers glow green down the bulkhead behind them. || nogear deskwork
- A character portrait || {Subject} {is_are} sitting on the corner of a desk in a dark office reading down a long printout roll that spills from {possessive} hands to the floor, the only light a swan-neck lamp - rows of unmanned desks and dead monitors recede behind {object}. || nogear deskwork
- A character portrait || {Subject} {is_are} writing on the far side of a glass status wall with a marker, the lettering running backwards toward the viewer and {possessive} face lit through it - beyond the glass a watch floor of glowing stations stretches away into the dark. || nogear deskwork
- A character portrait || {Subject} {is_are} standing at the head of a briefing table pointing up into a projected overlay hanging above it, seated silhouettes ranked down both sides of the room - the projector's beam cuts through drifting smoke above {possessive} shoulder. || nogear deskwork
- A character portrait || {Subject} {is_are} slumped back at a desk at the dead hour with {possessive} boots crossed on an open drawer and a cold cup balanced on {possessive} chest, staring at a screen of unread traffic - the office behind {object} is dark but for three other terminals left running. || nogear deskwork
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a records basement of racked case files, a single terminal glowing at the end of a long aisle with its cursor blinking on an open query. || deskwork
- A character portrait seen from behind || {Subject} {is_are} standing at the edge of a bridge viewport, looking out at a vast slab-sided capital ship gliding past above a sea of cloud, its engine bank blazing and a screen of escort fighters streaking alongside - a pale moon hangs in the black above the curve of the planet beyond {object}.
- A character portrait || {Subject} {is_are} reclined across a battered red sofa set out in the rain, legs stretched long and one hand propping a clear umbrella over {possessive} shoulder - behind {object} a rain-streaked alley of glowing shop signage and ribbed tower pipework dissolves into haze, steam venting from a rooftop stack. || nogear weather
- A half-body character portrait || Behind {object}, out of focus, the bright curve of a planet falls away beneath a dense starfield, a small ringed world hanging luminous in the dark.
- => Night rooftops of masts and tanks
- => Neon tower canyons
- A dramatic low-angle character portrait || {Subject} {is_are} reaching up to lay one hand flat against the vast armored fingers of a companion war-machine lowering its hand toward {object}, embers drifting through the dark around them both. || nogear ownmech
- => Street riots and panics
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} lunging forward into a thrown haymaker, one armored fist driven straight at the viewer and the other arm flung back wide, weight dropped deep over the front knee - behind {object} an armored transport's headlights blaze through the rain of a neon-lit alley, a soldier with a raised rifle half-lost in the glare. || weather frontline
- A dynamic character portrait || {Subject} {is_are} sprinting straight toward the viewer down a crowded market street, arms pumping and mouth open mid-shout, a panicked crowd running at {possessive} back - behind {object} a fireball blooms out of a tower block, sagging power lines and lit shop signage framing the street. || weather
- A dramatic low-angle character portrait || {Subject} {is_are} dropping to the street on a fast-rope, one gloved fist locked around the line and boots swinging down, the open hold of a hovering dropship looming overhead - neon signage glows through the fog across the facades behind {object}. || nogear weather frontline
- A dramatic low-angle character portrait || {Subject} {is_are} standing braced and firing a rifle one-handed up at the underbelly of a gunship hovering low overhead, muzzle flash flaring - a ragged street crew fires alongside {object}, cable-strung towers crowding the night sky behind. || nogear weather frontline
- => Watching the city burn
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a dark marble-walled penthouse office, a lit backbar of bottles glowing against the stone and a rain-streaked night skyline through the glass beyond.
- A dynamic character portrait || {Subject} {is_are} charging low toward the viewer down a neon-lit back street, fists clenched and teeth bared, masked gunmen opening fire from the doorways behind {object}. || weather frontline
- A character portrait seen from behind || {Subject} {is_are} standing in a trash-strewn neon alley with one arm locked straight out, a pistol sighted on a line of masked gunmen advancing out of the smoke ahead, a small fire burning in the gutter. || nogear weather frontline
- A dynamic, low-angle character portrait || {Subject} {is_are} caught mid high-kick in a rain-slick back alley at night, one leg driven straight up into a charging attacker's chest and a pistol held out in the other hand - behind {object} more armed thugs advance past a burning wreck, lit shop signage stacked up both walls of the narrow street. || nogear weather frontline
- A character portrait seen from behind || {Subject} {is_are} hunched over an improvised surveillance station on a steel desk in a derelict warehouse, stacked monitors tracking a city map marked with spreading red zones, a radio set and a swan-neck lamp at {possessive} elbow and cabling spilling off the desk edge - rusted drums and a lone brazier glow in the dark beyond {object}. || nogear deskwork
- => Ruined corridors and halls
- A low-angle character portrait || {Subject} {is_are} stepping out between a pair of heavy riveted steel doors swung open onto a grimy service corridor, a cold strip light burning in the passage behind {object} and rust-streaked pipes climbing the concrete walls to either side.
- A half-body character portrait || {Subject} {is_are} standing at the foot of a gaunt white-plated humanoid frame locked upright in its service cradle, a large stencilled unit number across its shoulder plating and bundled cabling hanging from the gantry around it - the dim hangar recedes into dark steel behind {object}. || mechyard
- => Dig sites and survey camps
- A character portrait || {Subject} {is_are} seated behind a broad holographic workstation, translucent display panes glowing up across {possessive} hands, articulated robotic arms folded at either side - dark server racks blink in rows behind {object}. || deskwork
- => Rooftop dropship pads
- => Escorted by faceless troopers
- => Machines in service cradles
- => Shipboard corridors
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a translucent holographic display hanging in a dim lab, a flayed anatomical figure and ranks of glowing data nodes mapped across its surface.
- A character portrait || {Subject} {is_are} sitting back in a heavy padded restraint chair bolted to the deck of a steel holding room, both forearms laid flat along its armrests - a figure stands watching from the open doorway behind {object}, half lost in shadow.
- A close character portrait || {Subject} {is_are} slouched sideways in a cramped cockpit seat, one leg hooked up over the console and an arm slung across the knee, a sullen look turned on the viewer - scuffed instrument panels and dim readouts crowd the canopy frame around {object}. || cockpit
- A character portrait || {Subject} {is_are} sitting with knees drawn up on a grassy rise, beyond {object} a winding path leads toward slender colony towers and a distant smoking mountain. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a barren ridged planetary landscape beneath a huge turbulent sun low above the horizon. || weather
- => Industrial tower canyons
- => Warships over cities
- => Finned slab towers
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a battered twin-pod shuttle banking through a shadowed industrial ravine, its scraped panels catching the light. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a compact crew cabin with an unmade bunk, inset windows, storage lockers and exposed ceiling conduits. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a tall covered industrial alley framed by heavy cross-bracing and dim lamps, scattered refuse along the lower walls. ||
- A character portrait || {Subject} {is_are} standing alongside an armored utility rover while another crew member sits on its upper hull, a dusty mountain plain stretching behind them. || weather
- => Flying traffic boulevards
- => Standing by landed shuttles
- => Shipboard briefing rooms
- => Walking out to waiting craft
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a glossy high-ceilinged transit passage leading toward a brilliant circular portal, light reflecting along the floor. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a pale sprawling city seen from a rocky overlook beneath a crescent moon and low bands of cloud. || weather
- => Spaceport aprons
- A character portrait || {Subject} {is_are} standing inside a curved observation gallery among several other onlookers, a planet and distant streaks of spacecraft fire filling the panoramic window. ||
- => Monumental ring gateways
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a tiered glass-fronted residence extending over dark coastal water, warm interior lights showing through the stacked terraces. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a broad fortified city beneath a star-filled sky and drifting bands of auroral light. || weather
- => Storm-lashed coasts
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a pale angular coastal facility built into a wooded cliff, broad terraces projecting over breaking surf. || weather
- => Repairing electronics
- A character portrait || {Subject} {is_are} leaning toward the viewer with one hand reaching across a bank of illuminated controls, dense cockpit equipment surrounding {object}. || cockpit
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cavernous server hall with repeated illuminated rack columns, suspended cables and shallow reflections on the floor. ||
- A character portrait || {Subject} {is_are} leaning sideways across a low seat in a dim industrial room, tall gridded windows casting broken light through the haze. ||
- A character portrait || {Subject} {is_are} standing side-on at a wide electronic console, one hand extended over its controls and layered city lights visible through the window. || deskwork
- => Beside utility robots
- A character portrait || {Subject} {is_are} sitting in a cramped flight chair and looking down at the controls, a broad curved forward viewport opening onto stars. || cockpit
- => Sitting on a bunk
- => Apartment windows over the night city
- => Vending machines and street terminals
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a compact listening room lined with large speaker cabinets, framed panels and narrow overhead light strips. ||
- A character portrait || {Subject} {is_are} standing between tall banks of electronic equipment in a cramped room, an open window showing signs across the street. ||
- => Diner and bar counters
- => Waiting at stations and shelters
- => Abandoned transit stations
- A character portrait || {Subject} {is_are} sitting bent forward in a glass-walled maintenance chamber, loops of cable descending around {object}. ||
- A character portrait || {Subject} {is_are} standing outside a brightly lit shop window filled with closely spaced display shelves, deep city shadows beside the doorway. || weather
- A character portrait || {Subject} {is_are} standing face-to-face with a tall pale armored mech in its maintenance bay, lit support structures enclosing the machine. || mechyard
- A character portrait || {Subject} {is_are} standing beneath the spread shoulder assemblies of a looming dark mech in a cool-lit hangar. || mechyard
- A character portrait || {Subject} {is_are} standing at an angled shipboard control desk and turning toward a broad forward window, luminous clouds and stars visible outside. || deskwork
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a dense city of evenly spaced illuminated avenues viewed from above, a huge low sun at the skyline. || weather
- A character portrait || {Subject} {is_are} sitting cross-legged on the polished floor of a vast open-sided hall, a carved dragon mural across one wall and distant industrial towers beyond the balcony. ||
- A character portrait || {Subject} {is_are} sitting with one knee raised beneath a star-filled sky, a brilliant cloud-covered planetary horizon beyond {object}. ||
- A character portrait || {Subject} {is_are} standing close to a pale humanoid mech with one palm resting on its broad chest plate, the surrounding hangar struts receding into shadow. || ownmech
- A character portrait || {Subject} {is_are} leaning forward over a narrow illuminated keyboard in a dim equipment room, dense hanging cables close around the workstation. || deskwork
- => Lone war machines on open ground
- A character portrait || {Subject} {is_are} sitting on the sloped plating of a large armored machine with legs hanging loose, a windswept plain beyond it. || ownmech weather
- A character portrait || {Subject} {is_are} leaning over a sloping equipment console with one mechanical hand extended toward the viewer, dense overhead cable looms filling the room. || deskwork
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a wide hovering transport beyond a rain-streaked window, its engine lights diffused by pale cloud. ||
- => Starship lounges
- A character portrait || {Subject} {is_are} sitting on a low barrier at a covered roadside fuel station, a broad lit canopy and shuttered service bays behind {object}. ||
- A character portrait || {Subject} {is_are} sitting on an upper-level balcony railing with one leg folded inward, an open atrium of shops and layered walkways below. ||
- A character portrait || {Subject} {is_are} standing beside a stairway between densely stacked city storefronts, large glowing sign panels jutting above the landing. || weather
- A character portrait || {Subject} {is_are} standing beside a dark urban canal, illuminated bridges and densely packed windows reflecting in the water. || weather
- A character portrait || {Subject} {is_are} sitting at a cramped desk between tall bookcases, an open book in {possessive} hands and a small monitor glowing nearby. || nogear
- A character portrait || {Subject} {is_are} sitting with one knee raised on a locker-room bench, an elbow resting on the knee, metal locker doors lining the narrow room. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a flower-shop window crowded with luminous blossoms, the city dropping away beyond the glass. ||
- A character portrait || {Subject} {is_are} leaning against a kitchenette counter beside an open refrigerator, its interior light spilling over {possessive} legs. ||
- => Empty cockpits and flight decks
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a dense low settlement enclosed by colossal dark pylons beneath a heavy storm front. || weather
- A character portrait || {Subject} {is_are} walking toward the viewer along a crowded high-rise street, a low vehicle passing behind {object} beneath an orange dusk sky. || weather
- => Empty starship bridges
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a tapered launch tower perched above a river gorge, lit vertical panels between projecting landing platforms. || weather
- => Alien vistas under giant planets
- A character portrait || {Subject} {is_are} sitting at a compact computer desk before a wall-height window, a dark shoreline and luminous dusk horizon beyond the glass. ||
- A character portrait || {Subject} {is_are} walking along a wet exposed causeway toward a curved spaceport tower, moored vessels hanging above storm-driven water. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a domed colony hub surrounded by circular landing pads and dense machinery against a dark planetary horizon. ||
- => Shuttles landed in the wild
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a vertical shipyard where long vessels hang between illuminated towers at different heights. ||
- A character portrait || {Subject} {is_are} walking in a sealed EVA pressure suit and closed helmet across a dark landing field, a handheld lamp illuminating the dust before {object} beneath two moons. || nogear vacuum
- => Overgrown abandoned interiors
- => Shuttle hangars
- => Habitat atriums
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a crowded club with illuminated rectangular frames suspended over a reflective dance floor. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a narrow neighborhood electronics shop, boxed components and display screens crowding the windows beneath exposed wall piping. || weather
- => Night markets
- => Industrial harbors and refineries
- A character portrait || {Subject} {is_are} sitting in a raised central command chair, crew stations flanking {object} and a broad planetary window filling the bridge behind. || deskwork
- => Observation windows onto space
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a monumental tower with a glowing arched opening above clouds, narrow platforms projecting from its sides. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a neglected coastal settlement threaded with grass and scrap, a low vessel crossing above the sea at dusk. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a hovering ring-shaped craft casting a vertical beam between tall city pylons. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rocky cavern opening filled by a curling luminous vortex. ||
- A character portrait || {Subject} {is_are} standing at a narrow balcony rail overlooking a dense canyon of stacked wooden-fronted shops and distant metal towers. || weather
- => Dwarfed by colossal structures
- A character portrait || {Subject} {is_are} walking in a sealed EVA pressure suit and closed helmet between frost-coated habitat walls, a low bridge spanning the route beneath a huge planetary crescent. || vacuum
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a compact container cafe with a service hatch, potted plants and a palm tree beside its awning. || weather
- => Shattered worlds on fire
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a tall machinery bay with cylindrical modules suspended from cranes above striped service lanes. ||
- => Floating cities
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a vast cavern of industrial shrines dominated by a colossal skull-shaped structure with glowing eye sockets. || @grimdark
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a needle-like tower rising from a dark blue frozen plain beneath a low planet. || weather
- A character portrait || {Subject} {is_are} walking through a gold-trimmed observation salon, other passengers gathered before a great oval window framing orbital rings. ||
- A character portrait || {Subject} {is_are} sitting at a flight station with one hand on the controls and the other near a transparent display, the canopy fractured into bright splinters behind {object}. || cockpit
- => Distant war machines in battle
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a tiered tiled-roof palace beside an arched bridge, flowering trees and lantern reflections crowding the still canal. || weather @neosamurai
- => Alien gardens
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a spotless white spacecraft laboratory with paired workbenches, glossy dark flooring and a curved skylight opening onto stars. ||
- A character portrait || {Subject} {is_are} sitting beside a companion at a tiny outdoor table, both turned toward an enormous mushroom cloud rising over the distant plain. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a circular landing dais surrounded by broken stone, a narrow beacon rising toward a hovering ship beneath an immense planetary limb. || weather
- A character portrait || {Subject} {is_are} walking along a narrow railed landing gantry with a round flight helmet tucked beneath one arm, terraces and distant spacecraft opening behind {object}. || nogear weather
- A character portrait || {Subject} {is_are} standing beside a companion beneath a colossal rectangular stone arch, a sheer drop and a sea of cloud stretching beyond the ruined threshold. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a lantern-lit canal winding between tiered palace roofs and flowering trees, a turbulent sky reflected in the water. || weather @neosamurai
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a columned sanctuary inset deep inside the mouth of a sheer cliff, a dark conifer forest climbing the slopes below. || weather
- A character portrait || {Subject} {is_are} climbing a broad stone stair toward a spherical habitat with round illuminated windows, suited companions ahead amid barren ridges. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a towering patchwork war machine parked amid ruined apartment blocks, groups of people gathering beneath its massive legs. || weather
- A character portrait || {Subject} {is_are} sitting at a curved flight console beside a second crew member, hands resting on the controls beneath an arched window filled by an alien moon. || cockpit
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rocky observation site crowded with monitors, an enormous whale-like organism drifting through the star-filled sky above. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a monumental circular canopy carried by a row of impossibly tall columns above a winding road through rocky hills. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a narrow riveted observation corridor with a counter beneath tall windows, a cat perched beside equipment overlooking a neon city. ||
- A character portrait || {Subject} {is_are} bracing at a damaged flight station as sparks shower from overhead panels, other crew ducking around the central command chair. || cockpit
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a deep industrial launch shaft with layered gantries, a spacecraft suspended beside a tall curtain of light. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a city of slender white towers and looping elevated roads beneath a huge ringed planet at sunset. || weather
- A character portrait || {Subject} {is_are} leaning forward over a wall of analog flight controls, one hand adjusting a switch beneath a wide window framing the planet below. || cockpit
- A character portrait || {Subject} {is_are} standing in a vast open observation arch between heavy consoles, a ringed planet filling the sky beyond the pale landscape. ||
- A character portrait || {Subject} {is_are} leaning both hands on the edge of a luminous navigation table, crew gathered around the chart beneath a broad planetary observation window. || deskwork
- => Cliffside cities with waterfalls
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cavernous derelict shipyard crossed by skeletal beams, battered spacecraft lying beneath broken skylights. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a moonlit mountain valley with jagged snowy peaks and a bright winding river beneath dense stars. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a misty jungle stream bordered by mossy ruins, several armored figures and a tall companion machine crossing a fallen trunk. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a dark hovering sphere surrounded by concentric incandescent rings above a circular landing basin in barren terrain. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a domed pavilion with a glowing arched entrance reflected in a thawing pool, snowfields beneath a ringed planet. || weather
- A character portrait || {Subject} {is_are} standing on a narrow bridge through a dark conifer gorge, a spherical hovering probe with clustered sensor lights looming above. || weather
- A character portrait || {Subject} {is_are} standing beside a pack animal inside a deep rocky cavern, a shaft of sunlight falling through an opening far overhead. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a tall cylindrical landing tower bearing illuminated vertical lettering, ground lights and small vehicles glowing through night fog. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a low circular landing building reflected in still water, tall glass towers rising behind it beneath broken clouds. || weather
- A wide character portrait || {Subject} {is_are} sitting back on a grassy hillside in a sealed EVA pressure suit, bubble helmet catching the sunset light, wildflowers around {object} - beyond {object} a spired, domed city glows across the valley below. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a churning red giant star swallowing the sky above a scorched, rocky wasteland. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a canyon of pipe-wrapped industrial towers rising into a hazy, cloud-streaked sky. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cramped conduit corridor lined with old monitors and tangled cabling, lit by flickering overhead strips. || @cyberpunk
- A wide character portrait || {Subject} {is_are} climbing a long stone stairway toward a colossal, twisting ancient tree that dominates the night sky - its canopy pale and heavy with age. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a jagged black warship thundering low over a neon-lit megacity, twin engines flaring hard. || weather @cyberpunk
- A dynamic character portrait || {Subject} {is_are} sitting cross-legged at the roof's edge, empty cans and spent injectors scattered around {object} - beyond {object} a sprawling neon-lit metropolis and drifting gunships glow through the smog below. || weather @cyberpunk
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cluster of angular black skyscrapers wreathed in fog and rain, signage glimmering through the mist. || weather @cyberpunk
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is the gutted wreck of a gunship canted against rust-streaked ruins, backlit by a hazy, smoke-choked sun. || weather warzone
- A wide character portrait || {Subject}, a battle-worn synthetic sentinel, {is_are} standing watch over a fog-choked ruin - a battered cargo hauler roars low overhead, twin engines blazing. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cluttered shipboard berth, an unmade bunk and cable-strewn floor beneath a round viewport looking out on a distant spired skyline.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-slicked industrial alley choked with crossed girders, hanging cable, and a lone lit doorway. || weather
- A wide character portrait || {Subject} {is_are} sitting atop an armored patrol vehicle's hull, boots dangling - beside {object} a crewmate stands watch and more vehicles roll through the hills behind them. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a hovering saucer-shaped craft looming low over a grimy, traffic-choked city street beneath heavy clouds. || weather
- A wide character portrait || {Subject} {is_are} trading words with a fellow pilot beneath the nose of a parked starfighter - more craft and a pack animal shelter deeper in the ice-walled hangar cave behind them. || mechyard
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a sunlit command chamber ringed by a raised oval console, its viewport framing distant mountains beneath a starry false ceiling.
- A wide character portrait || {Subject} {is_are} standing in a line of packed-out troops - all watching a heavy dropship settle onto the dusty tarmac ahead of stacked cargo containers. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a vaulted dim-lit corridor of stacked machinery and support struts opening onto a hazy hangar beyond.
- A dynamic character portrait || {Subject} {is_are} drifting underwater in flowing robes, cupping a glowing jellyfish in both hands - more drift past in the dark water around {object}. || nogear
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a soaring lit hangar arch, a ship easing past far below and guide-lights striping the deck.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a hulking, organic-armored gunship bristling with running lights, hovering low over a rain-slick neon street. || weather @cyberpunk
- A dynamic character portrait || {Subject} {is_are} standing at the command station of a bridge crew, arm raised to issue orders - a space battle rages beyond the viewport behind {object}. || deskwork
- A wide character portrait || {Subject} {is_are} standing amid a vast robed congregation filling a carved stone amphitheater - all facing a colossal golden ringed artifact suspended in the archway ahead. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-slicked spaceport landing field crowded with white-and-orange dropships, distant figures moving between them under a smoke-hazed sky. || weather
- A character portrait || {Subject} {is_are} standing in a sun-baked desert canyon, a hovering orange-and-white shuttle idling behind {object} in a haze of kicked-up dust, sheer red-rock cliffs rising beyond. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a corporate executive's cliffside villa glowing above a dark sea, glass balconies stacked in tiers of white light. || weather @corporate
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a hazy desert mountain range under a pale sky. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a long circular ship corridor lined with humming consoles and tangled conduit, a bright hatch glowing at the far end.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a sprawling fog-wrapped city under an aurora-streaked night sky, its central spire lit against distant orbital wreckage. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a lone comms tower rising beside a winding river, a vivid magenta sun sinking behind jagged mountain peaks. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a neon-lit coastal skyline battered by towering storm waves beneath a lightning-veined cyclone. || weather @cyberpunk
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a derelict station gantry framing a fractured lava-veined planet, its molten cracks bleeding orange light across the wreckage.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a beached derelict superstructure jutting from coastal cliffs, surf breaking against its hull beneath a pastel dawn sky. || weather
- A character portrait || {Subject} {is_are} standing in a windswept maple grove, gazing off to one side as red and gold leaves swirl past - behind {object} an enormous pale sun rises huge through drifting haze. || weather @neosamurai
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a retro-futurist city skyline crowded with slender spires, a monorail gliding past beneath a huge setting sun and streaking aircraft. || weather
- A character portrait || {Subject} {is_are} sitting on a grassy hillside in a full sealed pressure suit and bubble helmet, an oxygen pack braced against {possessive} back, gazing out over a wildflower-strewn slope - behind {object} a gleaming spired city glows under a burnt-orange sunset sky. || weather
- A close character portrait || {Subject} {is_are} seated at a cluttered signal-analysis console, reaching a hand out toward the viewer, banks of radar and comms screens glowing behind {object} in the dark. || deskwork
- A character portrait || {Subject} {is_are} reclining loose-limbed in a cockpit chair, one arm draped over the armrest and reaching out toward the viewer - banks of radar and system-status screens glow all around {object} in the dark. || cockpit
- A dynamic, close character portrait || {Subject} {is_are} leaning in close, a welding torch sparking bright against machinery just out of frame, one gloved hand braced against a conduit pipe - behind {object} a cramped mechanical bay glows with banks of blue status lighting. || nogear mechwork
- A character portrait || {Subject} {is_are} sitting perched atop the wing of a colossal downed war-machine, one leg bent and the other dangling free, hair streaming in the wind - behind {object} a huge pale moon hangs low through drifting clouds. || weather warzone
- A dynamic, low-angle character portrait || {Subject} {is_are} crouched on a rain-slick rooftop ledge, both hands locked around a pistol raised and sighted toward the viewer - behind {object} a dense neon-lit skyline glows through the downpour, animated signage flickering between towers. || nogear weather frontline
- A character portrait || {Subject} {is_are} reclining against a rack of ship machinery, gazing out through an open bay at a green-ringed planet curving past below, status placards and stencilled numerals crowding the paneling around {object}.
- A dynamic character portrait || {Subject} {is_are} leaning hard into a cramped cockpit, reaching one hand down for the controls, a targeting display glowing through the canopy ahead. || cockpit
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a neon-drenched server garden, light bleeding through hanging cable bundles.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a flooded server hall lined with towering data columns, tangled cabling dripping from the ceiling.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a neon tower-lined night skyline glowing through drifting haze.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a dense wall of glitching status displays and system readouts, flickering light. || @cyberpunk
- A character portrait || {Subject} {is_are} seated on a parked matte-black motorcycle in the rain, glancing back over one shoulder - behind {object} a tangle of overhead wires crosses a rain-streaked alley beneath hazy tower lights. || weather
- A character portrait || {Subject} {is_are} leaning back with arms folded against the sleek hull of a parked jet fighter, a unit patch stitched to one sleeve - behind {object} a rain-slicked airfield stretches away under sodium lights, distant tow tractors and hangar gantries fading into the night haze. || weather
- A character portrait || {Subject} {is_are} leaning over a lit mixing console, one cybernetic hand adjusting the controls as a holographic waveform display glows above it - behind {object} a floor-to-ceiling window frames a dense green neon skyline at night.
- A character portrait || {Subject} {is_are} standing at a rooftop railing, glancing back over one shoulder, a jacket slipping loose off {possessive} shoulders - behind {object} a dense neon-lit skyline glows beneath an enormous full moon, a small craft streaking past overhead. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a maze of glowing conduit pipes threading through a dim mechanical bay.
- A character portrait || {Subject} {is_are} riding low in an open mechanical rig, reaching one hand forward to the controls - behind {object} a hazy industrial harbor glows under a smoke-streaked night sky, a tall lattice crane tower rising at the waterline. || weather
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} drifting weightless on {possessive} back, body arched and limbs trailing loose, thick cabling snaking from a socket at {possessive} hip - around {object} shattered debris and wreckage hang motionless in the dark, a green-banded planet curving below.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-soaked alley strung with neon signage in unfamiliar characters, steam rising off nearby piping. || weather
- A close, low-angle character portrait || {Subject} {is_are} leaning over a lit mixing console in a server room, cable bundles snaking underfoot and rack lights glowing through the haze behind {object}.
- A half-body character portrait || {Subject} {is_are} standing beside a hulking rust-scarred war machine, its sensor cluster glowing above {object} as hazy towers rise behind them.
- A close cockpit character portrait || {Subject} {is_are} piloting through a star-lit night sky, one hand steady on the control column as distant skyline lights streak past the canopy. || cockpit
- A wide character portrait || {Subject} {is_are} standing in a rain-soaked neon alley beside a hulking quadrupedal combat drone, its single sensor-eye glowing above the wet pavement. || weather
- A close cockpit character portrait || {Subject} {is_are} reclining in a mech's pilot seat, restraint straps loose across {possessive} shoulders as the console blinks beside {object}. || cockpit
- A wide character portrait || {Subject} {is_are} climbing a gantry ladder beside a hulking industrial mech in a sunlit machine bay, girders and catwalks framing the scene. || mechyard weather
- A wide, low-angle character portrait || {Subject} {is_are} standing atop {possessive} own mech's shoulder, arms spread wide as neon towers plunge away on either side of a rain-lit canyon street below. || ownmech weather
- A half-body character portrait || {Subject} {is_are} perched on a lobby console beside floor-to-ceiling windows overlooking a rain-streaked marina at night.
- A half-body character portrait || {Subject} {is_are} sitting cross-legged on a windowsill surrounded by a boombox and scattered cassette tapes, neon signs bleeding through rain-streaked glass beside {object}.
- A wide character portrait || {Subject} {is_are} walking straight toward the viewer down a narrow neon-lit alley, shuttered storefronts and glowing signage lining the wet pavement on either side. || weather
- A half-body character portrait || {Subject} {is_are} sprawled across a bus seat, one arm hooked over the rail behind {object} as rain streaks the window beside {possessive} head.
- A wide character portrait || {Subject} {is_are} leaning in to inspect a lit vending machine at the mouth of a quiet alley, steam curling from a nearby drain.
- A half-body character portrait || {Subject} {is_are} sitting at an outdoor food stall counter nursing a drink, rain dripping steadily from the awning overhead. || weather
- A wide character portrait || {Subject} {is_are} relaxing on a couch scrolling a tablet, surrounded by stacked CRT monitors and a record player, a lit city skyline framed in the window behind {object}.
- A half-body character portrait || {Subject} {is_are} reclining against a stack of speaker cabinets in a cassette-lined room, cables strung between neon tube lights overhead.
- A wide character portrait || {Subject} {is_are} standing at a neon-lit payphone in the rain, one mechanical hand resting on the receiver as signage glows overhead. || weather
- A half-body character portrait || {Subject} {is_are} sitting at a diner counter beside a rain-streaked window, a vintage radio humming next to {possessive} hand as neon signs blur across the street outside.
- A wide character portrait || {Subject} {is_are} standing on an observatory rooftop terrace, one hand pressed to a headphone as a neon skyline glitters far below.
- A half-body character portrait || {Subject} {is_are} reclining along a train bench seat, headphones trailing a cord to {possessive} collar as rain streaks the round windows beside {object}.
- A half-body character portrait || {Subject} {is_are} sitting in a near-empty train car, one leg crossed over the other and a mechanical hand resting on {possessive} knee, neon signage smeared across the rain-streaked window behind {object}.
- A dynamic, low-angle character portrait || {Subject} {is_are} crouched low mid-stride through a collapsed shopping mall atrium, broken skylights spilling light over vines and dead escalators. || weather
- A wide character portrait || {Subject} {is_are} standing squarely in a circuit-etched doorway overlooking a lit skyline, twin banks of windows framing the city on either side.
- A wide character portrait || {Subject} {is_are} curled low inside a sunken observation chamber, coral and kelp drifting past the glass as a drowned skyline glows beyond.
- A wide character portrait || {Subject} {is_are} walking past a lit record shop window stacked with vinyl and tape decks, wet pavement reflecting the glow behind {object}. || weather
- A close, over-the-shoulder character portrait || {Subject} {is_are} glancing back through the rain, a jumbotron overhead replaying {possessive} own dripping face against a dense neon skyline. || weather
- A wide character portrait || {Subject} {is_are} standing before a towering white-and-blue mobile suit, its cockpit hatch lit and cabling trailing loose across the plaza between them. || @gundam
- A wide character portrait || {Subject} {is_are} standing before a hulking black war machine, its optics glowing as a hazy city skyline rises behind them both.
- A wide character portrait || {Subject} {is_are} glancing back over one shoulder on a rooftop ledge, retro neon signage for a hotel and a playhouse glowing across the skyline behind {object}. || weather
- A close cockpit character portrait || {Subject} {is_are} lying prone inside a sealed flight pod, cheek pressed to the padding as instrument light glows through the canopy overhead. || cockpit
- A wide character portrait || {Subject} {is_are} standing at a rain-lit bus shelter at night, smoke curling from {possessive} lips as neon signage glows across the wet street beyond. || weather
- A close character portrait || {Subject} {is_are} standing in heavy rain with the hulking silhouettes of two mechs looming behind {object}, their sensor-eyes glowing dull in the downpour. || weather
- A half-body character portrait || {Subject} {is_are} manning a console on a starship's crowded bridge, headset in place, as a colossal space station drifts past the viewport behind {possessive} crewmates. || deskwork
- A half-body character portrait || {Subject} {is_are} standing with {possessive} back to camera at a rooftop railing, a huge blood-red moon rising over a sprawling neon skyline below. || weather
- A wide character portrait || {Subject} {is_are} kneeling alone on a temple's polished wooden floor, a sheathed blade resting at {possessive} side, before a towering ink mural of a coiled dragon and an open veranda looking out over a misty lake. || weather
- A half-body character portrait || {Subject} {is_are} sitting on a rooftop ledge, back to a rain-slicked megacity glittering with corporate signage. || weather @cyberpunk
- A close character portrait || {Subject} {is_are} glancing back over {possessive} shoulder from the cockpit seat of a crimson mecha, the cabin lit by instrument glow. || cockpit
- A wide character portrait || {Subject} {is_are} standing atop a tower with arms flung wide, a glowing blade gripped in each hand, lightning splitting a storm-wracked sky behind a huge full moon. || weather nogear @neogothic
- A half-body character portrait || {Subject} {is_are} raising one hand beneath a glowing ring of projected script above a rain-soaked rooftop, a neon-lit city sprawling below. || weather
- A wide character portrait || {Subject} {is_are} dropping into a low fighting crouch in a rain-slick alley, a glowing dagger gripped and thrust low to one side. || weather nogear @neogothic
- A wide character portrait || {Subject} {is_are} striding away from camera through crumbling ruins beneath an underpass, a glowing blade held low in one hand, faint sigils drifting in the misty air. || weather nogear
- A wide character portrait || {Subject} {is_are} advancing warily down a cobweb-strewn ship corridor, flashlight raised in one hand. || nogear
- A half-body character portrait || {Subject} {is_are} leaning back in a padded flight seat, full-face visor tipped skyward, as a cratered planet fills the capsule window at {possessive} side. || cockpit
- A half-body character portrait || {Subject} {is_are} reaching up to rest a palm against the armored chest of a towering white mech cradled in its hangar bay. || mechyard
- A wide character portrait || {Subject} {is_are} clinging low across the shoulder of a hulking clawed war machine as it looms through a shattered, overgrown building. || weather warzone
- A wide character portrait || {Subject} {is_are} leaning over a glowing tactical map table with clasped hands, flanked by fellow officers amid banks of humming server racks. || deskwork
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a massive quadrupedal war-walker cresting a farmhouse roof, its gatling arm leveled out over rolling fields. || weather
- A half-body character portrait || {Subject} {is_are} sitting atop a rusted train car beneath a star-strewn sky, boots dangling over the edge as refinery towers smoke in the distance. || weather
- A wide character portrait || {Subject} {is_are} perched on the knee of a resting war-mech, boots braced on its armor plating, a ruined coastal refinery sprawling beyond. || weather mechyard
- A half-body character portrait || {Subject} {is_are} watching from a high balcony as a mile-long dreadnought drifts low over a spired gothic skyline through falling snow. || weather
- A wide character portrait || {Subject} {is_are} diving forward low over a rain-slicked rooftop, fingertips brushing the surface, a glittering high-rise skyline stretching out below. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a black-and-gold cyberpunk den with a glowing staircase, banks of monitors, and a rain-lit skyline through a curved window. || 
- A dynamic character portrait || {Subject} {is_are} perched on a concrete barrier outside an abandoned gas station, patrol drones hovering nearby while rain slicks the pumps and a glowing skyline rises behind {object}. || weather
- A dynamic character portrait || {Subject} {is_are} lounging on a glass-walled elevator bench, one arm braced against the seat, a light-trail highway and dense night skyline stretching beyond the window.
- A dynamic character portrait || {Subject} {is_are} sitting on a weight bench catching {possessive} breath, dumbbell racks and a floor-to-ceiling window looking out over the neon skyline behind {object}.
- A half-body character portrait || {Subject} {is_are} sitting alone at a café table beside a vintage radio, neon signage glowing through the rain-streaked window behind {object}.
- A dynamic character portrait || {Subject} {is_are} sitting behind the wheel of a rally coupe, one gloved hand on the shifter, a cassette deck and neon storefronts sliding past outside the window.
- A half-body character portrait || {Subject} {is_are} curled on a worn couch, a phone resting beside {object}, rain streaking a wall of windows over a dense rain-lit city.
- A dynamic character portrait || {Subject} {is_are} leaning back against a bridge railing over a canal, a stone bridge and lantern-lit shopfronts glowing across the water behind {object}. || weather
- A dynamic character portrait || {Subject} {is_are} standing on a rooftop ledge beside a blank glowing billboard, an elevated highway and glowing storefronts curving away below. || weather
- A dynamic character portrait || {Subject} {is_are} perched on a stool at a rain-slicked street food stall, cup in hand, awning lights and passing taxis glowing behind {object}. || weather nogear
- A dynamic character portrait || {Subject} {is_are} crouched low on a bus seat gripping the overhead rail, cybernetic legs braced beneath {object} - rain streaks the lit windows of a near-empty late-night bus.
- A dynamic character portrait || {Subject} {is_are} sitting at a chrome diner counter cradling a mug, neon ramen signage glowing through the rain-streaked window behind {object}. || nogear
- A dynamic character portrait || {Subject} {is_are} sitting on a transit bench, drones and flying traffic threading between towers beyond the platform glass. || weather
- A dynamic character portrait || {Subject} {is_are} standing beside a glowing phone booth on a wet side street, an elevated rail line and shopfront signs stacked in the rain behind {object}. || weather
- A dynamic character portrait || {Subject} {is_are} kneeling at a cluttered workbench of vintage radio gear, lit by the glow of the dials, neon shopfronts blurring through the rain-streaked window behind {object}.
- A dynamic character portrait || {Subject} {is_are} leaning against a rooftop railing beside a mounted telescope, a glittering night skyline spread out beyond {object}. || weather
- A dynamic character portrait || {Subject} {is_are} wiping down a chrome tabletop in a retro diner, neon ramen and café signs glowing through the window behind the booths. || barkeep
- A half-body character portrait || {Subject} {is_are} sprawled across a train berth seat, neon streaks blurring past the window as the train speeds through the night.
- A dynamic character portrait || {Subject} {is_are} sitting on a bench in an abandoned, overgrown shopping mall, dead escalators and shattered skylights framing {object}.
- A dynamic character portrait || {Subject} {is_are} descending a row of stadium bleacher stairs, floodlights and an empty pitch glowing below in the night. || weather
- A dynamic character portrait || {Subject} {is_are} sitting astride a customized motorcycle in a cluttered garage workshop, tool racks and a glowing motors sign filling the space behind {object}.
- A half-body character portrait || {Subject} {is_are} perched at the edge of a bed, a television hissing static beside stacks of tapes and records.
- A half-body character portrait || {Subject} {is_are} sitting back against a low dresser, an old television hissing static and a record spinning on the turntable beside {object}.
- A half-body character portrait || {Subject} {is_are} sitting alone on a subway car bench, hands folded, rain-streaked neon light blurring past the windows.
- A dynamic character portrait || {Subject} {is_are} descending a station stairway toward the platform, a monorail pulling in past glowing ad panels overhead. || weather
- A half-body character portrait || {Subject} {is_are} resting a hand on a riverside railing, an arched stone bridge and warmly lit shopfronts reflected in the canal behind {object}. || weather
- A dynamic character portrait || {Subject} {is_are} leaning across a subway bench toward the window, dawn light bleeding through the rain-streaked glass.
- A half-body character portrait || {Subject} {is_are} kneeling at a record player adjusting the needle, city lights glowing through the window behind {object}.
- A dynamic character portrait || {Subject} {is_are} sitting atop a library desk reading a book, banks of glowing retro terminals lining the shelves around {object}. || nogear
- A dynamic character portrait || {Subject} {is_are} standing squarely on a rooftop running track, a rail line and city towers glowing behind {object}. || weather
- A half-body character portrait || {Subject} {is_are} sitting on a rain-soaked bench beside a glowing vending machine, neon shop signs blurring in the wet street behind {object}. || weather
- A dynamic character portrait || {Subject} {is_are} kneeling between rows of lockers, a gym bag at {possessive} feet, fluorescent strip lights humming down a narrow row of steel doors.
- A dynamic character portrait || {Subject} {is_are} leaning forward over a bar counter lined with bottles, back to the camera, rain streaking the window that looks out on the glowing street beyond.
- A dynamic character portrait || {Subject} {is_are} standing on an elevated train platform, a monorail gliding in past a skyline studded with holographic ads. || weather
- A half-body character portrait || {Subject} {is_are} examining a glowing orchid inside a cramped flower shop, potted blooms and holographic signage crowding the glass storefront behind {object}. || nogear
- A character portrait || {Subject} {is_are} sitting cross-legged on the floor working a set of tube-radio dials, rain streaking the tall window and neon signs behind {object}. || nogear
- A dynamic character portrait || {Subject} {is_are} leaning heavily against a rooftop railing, flying traffic and towering signage crowding the skyline beyond {object}. || weather
- A half-body character portrait || {Subject} {is_are} sitting on a low stool beside a rooftop water tower, laundry lines strung overhead, an elevated train gliding past the skyline behind {object}. || weather
- A character portrait || {Subject} {is_are} eating noodles at a counter, chopsticks held in a mechanical prosthetic hand as steam curls from the bowl - behind {object} a rain-streaked ramen shop window glows with hanging paper lanterns and pink neon signage. || nogear weather
- A character portrait || {Subject} {is_are} holding up a glowing flower to look at it, headphones settled over both ears - behind {object} a rain-streaked flower shop window looks out on a neon-lit street. || nogear weather
- A character portrait || {Subject} {is_are} leaning back against a station pillar, arms loose at {possessive} sides - beyond {object} an elevated monorail platform stretches away beneath a neon-lit night skyline.
- A character portrait || {Subject} {is_are} leaning against a kitchen counter with one leg crossed over the other, a refrigerator standing open nearby - behind {object} a night skyline glows with neon signage through the window.
- A character portrait seen from behind || {Subject} {is_are} sitting cross-legged on a couch in a cluttered apartment, gazing out at the skyline - beyond {object} colossal airships drift past a dense futuristic cityscape lit gold by the setting sun. || weather
- A character portrait || {Subject} {is_are} braced amid drifting wreckage in a sealed EVA pressure suit and helmet, one gloved hand steadying a companion nearby - the debris field glints under harsh sunlight against the black of space. || vacuum
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a smoke-hazed industrial spaceport at dawn, a squat orange transport idling amid milling ground crews and heavy freight haulers.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a colossal angular warship in low orbit, its hull studded with lit viewports against the curve of the planet below.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is an empty starship command bridge lit in dueling neon, twin control chairs facing a bank of readouts.
- A character portrait seen from behind || {Subject} {is_are} walking away down a wrecked elevated roadway toward a distant glow, neon signage bleeding down twin rows of ruined towers to either side - the sky above hangs heavy with storm cloud. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a fog-choked moonlit forest littered with bleached skulls underfoot. || weather @grimdark
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a vast alien hive-colony sprawling beneath towering root-like structures, smoke rising from distant fires across the plain.
- A character portrait || {Subject} {is_are} walking straight toward the viewer down a rain-slicked cyberpunk street at dusk, a hazy orange sun sinking between the high-rises - behind {object} traffic idles amid glowing storefront signage and drifting pedestrians. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a crowded command bridge overlooking Earth, a formation of escort ships holding steady formation against the stars beyond the viewport.
- A half-body character portrait || Behind {object}, out of focus, is a needle-thin high-rise fortress studded with neon signage, perched above a waterfall-fed canyon as aircraft streak past under a low sun. || weather
- A character portrait || {Subject} {is_are} sitting amid a field of drifting wreckage inside a torn-open module, one gloved hand reaching toward a console, sealed inside a pressure suit and helmet - beyond {object} jagged debris drifts weightless in the dark. || vacuum
- A character portrait || {Subject} {is_are} lounging back on a couch with one leg crossed over the other, a pistol held raised near {possessive} shoulder, two drinks resting on the table nearby - behind {object} tropical leaves crowd a sunlit doorway. || nogear
- A character portrait || {Subject} {is_are} sitting in a window alcove, offering a piece of fruit to a small tri-clawed alien creature perched beside {object} - beyond the glass a crescent space station arcs against a nebula-streaked sky. || nogear
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a sleek transport streaking past a vast ringed gas giant, twin engine trails burning blue against the banded clouds.
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} weightless amid a drifting debris field in a sealed EVA suit, one arm reaching forward and the other trailing back, twin thruster housings glowing at {possessive} shoulders - beyond {object} the wreck of a colony structure tumbles slowly in the light of a distant sun. || vacuum
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a vast ringed orbital station wheeling slowly against a field of stars, small transports threading between its rings.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a massive dark planet crowned in a thin halo of light, rising low over a frozen icefield stretching to the horizon.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a quiet fishing harbor at sunset, rust-streaked cranes looming over weathered boats moored at the pier. || weather
- A character portrait seen from behind || {Subject} {is_are} walking alone across wind-carved dunes toward the wreckage of a colossal crashed superstructure, a tattered black cloak dragging long across the sand - overhead a churning sky burns dull orange-red through drifting haze. || weather @grimdark
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a still tidal river winding through low hills beneath an enormous ringed planet rising huge on the horizon.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a black cathedral-spired dreadnought hanging low over the planet's curve, a small escort gunship peeling away nearby and a lone amber moon rising past its towers. || @neogothic
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a sleek cross-winged white fighter craft banking above the planet's cloud tops, twin engines burning blue.
- A character portrait seen from behind || {Subject} {is_are} seated at a bank of monitors dense with scrolling code, the glow lighting {possessive} face from below - beyond the window a neon-lit high-rise skyline burns orange into violet at dusk. || nogear
- A dynamic character portrait || {Subject} {is_are} sprinting across a rain-lashed gantry alongside {possessive} squad toward a docked warship, lightning cracking through the clouds overhead - beyond {object} massive loading cranes rise over a storm-tossed sea and inbound gunships streak past through the rain. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a misty pine forest with a waterfall tumbling over moss-covered boulders into a shallow stream. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a shattered ship corridor breached open to a churning crimson nebula, severed cabling and debris drifting in the wreckage.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a vast domed orbital station bristling with docking spires, hanging low over a nightbound planet.
- A character portrait seen from behind || {Subject} {is_are} standing at the edge of a snowbound peak, watching an ornate gilded airship glide low over an endless sea of clouds, {possessive} cloak snapping in the wind. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a sleek dropship grounded on a drifting ice floe, open arctic water stretching to the horizon. || weather
- A half-body character portrait || Behind {object}, out of focus, is a towering gilded ceremonial archway on a mountain terrace, robed acolytes assembled in ranks before it. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a convoy of armored escort ships flanking a marked prison hauler low over a cratered planet, thin engine trails cutting through the dark.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a fleet of angular warships hanging low over a dense neon-lit cityscape at night. || weather
- A half-body character portrait || Behind {object}, out of focus, is a fireball erupting over a sun-baked desert airfield, a pair of strike aircraft peeling away through the smoke. || weather warzone
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a vast ringed orbital station studded with domes, hanging over a cloud-wrapped planet.
- A half-body character portrait || Behind {object}, out of focus, is a cratered airless moonscape under a sky streaked with burning asteroid fragments and a distant flare of light.
- A character portrait || {Subject} {is_are} standing before a wooden lattice wall strung with glowing paper lanterns, a black folding fan raised beside {possessive} face - a narrow lantern-lit alley recedes into misty light behind {object}. || weather nogear @neosamurai
- A character portrait seen from behind || {Subject} {is_are} standing on a rain-slicked rooftop, a loaded pack crossing both shoulders, looking out at a huge amber moon breaking through smoke-dark clouds beside a skeletal transmission tower and a neon-lit skyline below. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a vast marble palace of domed towers and gilded statues perched over a waterfall gorge, a grand arched bridge spanning the falls. || weather @neogothic
- A character portrait seen from behind || {Subject} {is_are} walking a stone causeway through a misty alien jungle toward a pair of colossal glowing ring structures wreathed in waterfalls, two companions ahead on the path and a small parked shuttle off to one side. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a grounded heavy freighter squatting on an ice field beneath a hazy binary sky, a line of parka-clad workers hauling crates toward it. || weather
- A half-body character portrait || Behind {object}, out of focus, is a sleek grounded transport ship resting in a windswept golden plain, a scatter of grazing bison nearby. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a fleet of parked dropships in an overgrown city courtyard, towering trees rising between the hulls and hazy smoke drifting beyond. || weather
- A character portrait seen from behind || {Subject} {is_are} standing at the base of a vast marble stairway, cloaked pilgrims climbing in their hundreds toward a domed temple at the summit, a grey-bearded elder pausing nearby to look back. || weather
- A dynamic character portrait || {Subject} {is_are} braced against a solar panel truss in a sealed EVA pressure suit and helmet, welding a torn strut as sparks scatter into the void - beyond {object} the banded clouds of a gas giant fill the horizon, support craft holding station in the distance. || nogear vacuum
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a wrecked ship corridor strung with torn cabling, arcs of stray electricity crackling between exposed conduits.
- A half-body character portrait || Behind {object}, out of focus, is a hulking dark battlecruiser holding station near a swirling accretion disk, a scatter of escort fighters cutting past its hull.
- A character portrait seen from behind || {Subject} {is_are} standing alone on an ornate inlaid marble floor at the foot of twin curling staircases, dwarfed beneath towering fluted columns and carved winged figures, a dark archway yawning ahead.
- A half-body character portrait || Behind {object}, out of focus, is a colossal triangular warship descending over a hazy neon-lit megacity, smaller escort craft scattered through the smog. || weather
- A half-body character portrait || Behind {object}, out of focus, is a crowd kneeling in ranks before a colossal gilded shield set into a marble temple wall, an ancient tree towering over the terrace beyond. || weather
- A half-body character portrait || Behind {object}, out of focus, is a colossal wave curling over a neon-spired coastal city, a small ship threading beneath its crest as a pale moon hangs low. || weather
- A character portrait seen from behind || {Subject} {is_are} seated at the head of a gleaming command bridge, officers in dress uniforms at consoles to either side, a fleet of escort ships holding formation beyond the viewport as a fractured moon glows below. || deskwork
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a colossal megacity of stacked lit towers linked by sweeping elevated bridges, hazy spires fading into the smog beyond. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-slick spaceport tarmac crowded with parked dropships and idling ground vehicles, a distant skyline smudged by rising smoke. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-slicked cyberpunk street beneath a pipe-wrapped tenement block, neon signage bleeding pink and cyan across the wet pavement. || weather @cyberpunk
- A character portrait || {Subject} {is_are} walking away across a moonlit alien wasteland in a sealed EVA pressure suit and helmet, a handheld light sweeping the ground ahead - behind {object} an antenna-studded lander rests on a ridge beneath a cluster of close moons as a battered gunship banks low overhead trailing sparks. || nogear vacuum
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a churning green sea breaking white against black coastal rocks beneath a smoke-orange sunset, jagged dark peaks rising through low cloud beyond. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a stark alien snowfield where a tailfin-finned dropship rests on skeletal legs before the ice-crusted ruin of a colossal white tower. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a moss-drowned factory atrium reclaimed by a canal and a single wide-canopied tree, catwalks lost beneath hanging vines overhead.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cavernous hangar bay where ground crews and cargo loaders swarm a newly landed dropship, a lit night skyline visible through the open bay doors beyond.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a mist-filled ravine where a glowing waterfall spills past ancient wind-bent trees, jagged mountain spires breaking the clouded sky beyond. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a marble palace balcony shaded by a wide parasol, a colossal gold-plated pyramid tower looming over a sun-baked hillside city of palms and red-tiled roofs beyond. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a sleek ship's lounge of low couches facing a vast viewport, a swirling accretion disc collapsing into a black hole framed beyond the glass.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a sunlit ship's common room of low couches and potted greenery, a mountain waterfall framed through the wraparound viewport beyond.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a glass-partitioned nightclub bar lit in bleeding neon, patrons and drifting vapor crowding the counters beyond. || @cyberpunk
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cluttered street-level electronics shopfront crowded with screens and potted plants, a hazy tower-lined avenue receding behind it. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cramped maintenance corridor strung with ducting and flickering monitor banks, figures receding down the wet grated deck beyond.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a fog-choked cyberpunk avenue lined with towering signage, traffic crawling past beneath the drifting haze. || weather @cyberpunk
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a colossal gilded ring of cathedral spires and tracery opening onto a starfield, pale towers rising from the mist below. || @neogothic
- A character portrait || {Subject} {is_are} seated in a raised command chair on a ship's bridge, crew stationed at consoles to either side - beyond the viewport a fleet of escort ships holds formation above a blue planet's curve. || deskwork
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-slicked dockyard of parked dropships beneath smoke-belching towers, ground crews moving between them in the fading dusk light. || weather
- A dynamic, low-angle character portrait || {Subject} {is_are} crossing a long exposed gantry bridge slung between two colossal megastructure towers, a dropship drifting past far below - haze and drifting cloud fill the deep chasm to either side. || weather
- A close character portrait || {Subject} {is_are} pressed to a scratched viewport, watching a besieged capital ship trade fire with a swarm of escorts through drifting flak - the battle rages low over the churning cloud tops of a planet far below. || warzone
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a colossal arched spire rising through cloud, a cluster of white-suited figures gathered on a platform within its glowing ring as transports thread past the tower's flank. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a scavenged coastal shantytown at sunset, salvaged junk piled between leaning towers as a battered flying hulk descends through the rain. || weather @scav
- A close character portrait || {Subject} {is_are} pausing in profile inside a sealed pressure-suit helmet, gazing out across a mineral flat toward jagged spires - behind {object} a bulbous transport ship hangs low against a hazy dusk sky. || weather vacuum
- A half-body character portrait || Behind {object}, out of focus, is a megacity canyon split by twin spires, a vast ringed station hovering overhead and venting a bright beam down between them. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a swirling green-and-violet spiral nebula rising over a close asteroid horizon.
- A character portrait seen from behind || {Subject} {is_are} standing at the head of a rooftop stairwell, backpack slung over one shoulder, looking down over a tiered market street strung with cable and red lanterns toward twin megatowers beyond. || weather
- A half-body character portrait || Behind {object}, out of focus, is a narrow gap between towering vertical spires, two colossal spheres suspended in the storm-lit sky beyond, lightning arcing between them over a hazy cityscape far below. || weather
- A half-body character portrait || Behind {object}, out of focus, is a frozen alien valley between two colossal fanged vessel-hulks locked into the ice, a slung bridge between them beneath a huge banded planet and crescent moon, distant figures and landers scattered on the ice. || @grimdark
- A half-body character portrait || Behind {object}, out of focus, is a massive terraced fortress rising from a stone breakwater, cranes and antenna clusters bristling from its towers as dockworkers and cargo dot the pier below. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a weathered beachside kiosk bar strung with lanterns beneath swaying palms, the tide rolling in past loitering figures. || weather
- A half-body character portrait || Behind {object}, out of focus, is a faceted crystalline structure breaking up through cratered grey regolith, a small moon and hazy nebula glow in the black sky above.
- A half-body character portrait || Behind {object}, softly blurred, is a dim command bridge, an ornate raised pilot's chair before a wall of switch panels and glowing gauges, silhouetted crew at the boards on either side, the galaxy's core blazing through the viewport beyond. || deskwork
- A half-body character portrait || Behind {object}, out of focus, is a vast overgrown atrium of rusted gantries and cracked skylights, moss and flowering vines swallowing broken machinery around a still reflecting pool. || @scav
- A half-body character portrait || Behind {object}, out of focus, is a pristine white hangar bay opening onto vacuum, a sleek fighter craft parked at the threshold with Earth's blue curve filling the gap beyond. || @corporate
- A half-body character portrait || Behind {object}, out of focus, is a battered scavenged transport hovering low over jagged wasteland ruins, a comet's tail bleeding red light across the night sky above. || weather @scav
- A half-body character portrait || Behind {object}, out of focus, is a neon-lit cyberpunk canyon of stacked highways and signage, flying transports threading between towers bathed in a hazy glow. || weather @cyberpunk
- A half-body character portrait || Behind {object}, softly blurred, is the crumpled hull of a derelict transport half-buried in grey regolith, a luminous spiral galaxy rising above the close horizon.
- A half-body character portrait || Behind {object}, softly blurred, is a sleek starship lounge of curved red-and-white couches under soft blue skylights, a dim viewscreen glowing at the far end. || @corporate
- A half-body character portrait || Behind {object}, out of focus, is a smoke-hazed industrial hangar bay, a boxy dropship settled on its landing struts as ground crews and haul trucks work around it, a starlit gantry framework visible through the open bay door beyond.
- A half-body character portrait || Behind {object}, out of focus, is a colossal black spired warship, twin raked prongs sweeping wide, hovering low over a dense grey apartment-block skyline at dusk as a lit beam lances down at its center. || weather @grimdark
- A half-body character portrait || Behind {object}, out of focus, is a churning white-capped tideline against black volcanic sand, a shattered orange moon crumbling into flame overhead and a ringed sun burning through drifting ash. || weather @grimdark
- A half-body character portrait || Behind {object}, out of focus, is a blocky black-and-white city-ship marked with bold red hull numbers, banking above a dense cloud layer at sunset as small craft peel away around it, a lit spired nightscape glimpsed far below. || weather
- A half-body character portrait || Behind {object}, out of focus, is a cavernous shipyard bay, segmented hull pods suspended from an overhead crane as work crews in high-visibility gear move between rail-mounted haulers below.
- A half-body character portrait || Behind {object}, out of focus, is a battered red rocket-shuttle grounded on cracked ice among towering luminous crystal spires, a pale moon rising through a dusk-orange sky. || weather
- A character portrait || {Subject} {is_are} leaning back against a rusted rooftop railing, one arm hooked over the rail, gazing out over sun-bleached ruined tower blocks - an abandoned office chair sits nearby on the cracked terrace. || weather
- A half-body character portrait || Behind {object}, out of focus, is a towering cybernetic reactor spire ringed with glowing signage panels, thin catwalks radiating from its base against a hazy neon skyline. || weather @cyberpunk
- A half-body character portrait || Behind {object}, softly blurred, is a derelict ship corridor with peeling arched plating and scattered debris, dim amber emergency lights flickering at the edges of the dark. || @grimdark
- A half-body character portrait || Behind {object}, out of focus, is a crowded neon-lit night market corridor, throngs of figures moving past glowing signage in unfamiliar characters. || @cyberpunk
- A half-body character portrait || Behind {object}, out of focus, is a hulking white capital ship marked with bold red hull numbers, cruising above an endless sea of clouds lit gold by a low sun, smaller escort craft trailing below. || weather
- A dramatic, low-angle character portrait || {Subject} {is_are} standing at the edge of a weathered stone terrace, gazing out at a chain of vast floating rock spires crowned with overgrown ruins - beyond {object} the tiered islands hang suspended above a rolling sea of cloud, their undersides trailing dark stone tendrils into the mist below. || weather
- A dramatic, wide character portrait || {Subject} {is_are} standing at a cliff's edge with hair whipped by the wind, watching small craft glide past a colossal ringed city hanging in the sunset sky - below {object} a canyon city of terraced towers and waterfalls stretches to the horizon. || weather
- A three-quarter character portrait || {Subject} {is_are} crouched over an open circuit panel, sparks scattering as {possessive} tool bites into the bared wiring while a crewmate's hand steadies the housing beside {object} - around {object} the cluttered engine bay of a starship recedes into shadow, drifting smoke and glowing status screens crowding the walls. || nogear mechwork
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a smoky dockside cantina strung with neon signage, patrons hunched over drinks and a gunship framed in the viewport beyond.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a hazy cyberpunk skyline of angular black towers strung with vertical neon signage and jutting screen panels.
- A wide, low-angle character portrait || {Subject} {is_are} standing at the mouth of a misty valley, gazing up at a colossal glowing ring embedded in the hillside - around {object} terraced greenery and drifting fog fall away into the haze below. || weather
- A dynamic character portrait || {Subject} {is_are} standing atop a girdered rooftop, watching small craft weave beneath a crowded sky of planets and moons - behind {object} a fantastical spired city recedes into drifting cloud and lantern-lit haze. || weather
- A half-body character portrait || Behind {object}, out of focus, is an alien river canyon under a hazy binary-lit sky, a ringed planet hanging low near the horizon. || weather
- A dramatic, low-angle character portrait || {Subject} {is_are} standing on a lantern-lit bridge, dwarfed beneath the colossal glowing skull that looms over the ruined skyline - behind {object} jagged spires and drifting embers recede into the dark. || weather @grimdark
- A half-body character portrait || Behind {object}, out of focus, is a moonlit alien desert bristling with distant black megastructure spires, a shooting star streaking past a banded planet low in the sky. || weather
- A wide character portrait || {Subject} {is_are} walking toward a knot of waiting dignitaries across a gilded observation deck, an alien envoy among them - beyond the great curved window a crescent starport hangs before a banded planet.
- A dynamic character portrait || {Subject} {is_are} seated in the cockpit with one hand on the throttle, gazing out at a wrecked orbital station drifting past a cratered moon. || cockpit
- A half-body character portrait || Behind {object}, out of focus, is a smoke-choked battlefield where towering war machines exchange laser fire under a bruised sky. || warzone
- A half-body character portrait || Behind {object}, out of focus, is the towering silhouette of a war machine striding toward a distant embattled skyline, smoke rising against the fading light. || weather warzone
- A dynamic character portrait || {Subject} {is_are} gathered with the rest of the crew around a lit tactical display table, studying a scrolling star chart - around {object} the cramped operations deck of a starship recedes into shadow. || deskwork
- A half-body character portrait || Behind {object}, out of focus, is a banded gas giant looming over a cratered moon, a distant outpost glinting near its terminator.
- A half-body character portrait || Behind {object}, out of focus, is a cratered lunar horizon lit by a departing dropship's engine flare, a crescent world rising beyond.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a maintenance bay dominated by a hulking war machine, status lights blinking along its plating and a technician's silhouette dwarfed at its feet. || mechyard
- A dynamic, wide character portrait || {Subject} {is_are} perched on the shoulder of {possessive} own war machine as it strides across a muddy wasteland, a cigarette smoldering forgotten between {possessive} fingers - behind {object} a radio mast leans against the storm-dark horizon. || weather ownmech
- A half-body character portrait || Behind {object}, out of focus, is a rain-soaked battlefield where towering war machines and armored columns advance beneath twin hazy suns, banners snapping in the wind. || weather warzone
- A half-body character portrait || Behind {object}, out of focus, is a dust-choked warzone where armored war machines exchange laser fire and tracer fire under a burnt orange sky. || warzone
- A half-body character portrait || Behind {object}, out of focus, is a colossal ringed space station, its glass biodomes holding entire forests and skylines within, silhouetted against a distant nebula.
- A half-body character portrait || Behind {object}, out of focus, is a colossal dark world encircled by blazing orange rings of light, its glow spilling across jagged alien peaks and small ships threading past.
- A character portrait || {Subject} {is_are} standing at a viewport aboard a ship's corridor, gazing out at a distant spiral nebula, the paneled walls glowing with soft accent lighting to either side.
- A half-body character portrait || Behind {object}, out of focus, is a scattered highland farming village of stone-and-tin cottages terraced into the hillside, a lone figure trudging the dirt path below. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cobbled corner street at dusk, warm shopfront lantern-light spilling from an old stone building's arched doorway beneath a lit signboard. || weather
- A character portrait || {Subject} {is_are} sitting on a snow-dusted bench at night, boots stretched out and shoulders hunched against the cold, breath fogging in the streetlamp glow - behind {object} snow falls past glowing shopfront signage and empty café chairs stacked at the curb. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a fog-shrouded canyon settlement of steam-vented ironwork towers and lantern-lit terraces, small figures gathered at an open-air café below. || weather
- A dynamic character portrait || {Subject} {is_are} advancing through a dead moonlit grass field in bulky segmented armor, gripping an assault rifle at a low ready, twin lensed optics glowing beneath {possessive} helmet - behind {object} bare skeletal trees stand black against a huge pale moon breaking through drifting haze. || nogear weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a windswept ice shore where a domed stone shrine glows warm behind twin lantern-lit archways, seabirds wheeling against the dusk. || weather
- A dynamic, low-angle character portrait || {Subject} {is_are} standing at the edge of a rain-slicked rooftop, one hand resting on a tall staff planted before {object}, watching a massive drop-ship descend trailing shuttle pods through the storm-dark clouds above a burning cityscape below - {possessive} silhouette dark against the vessel's running lights. || nogear weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a fogbound forest bridge beneath a massive spherical airship, its twin round viewports glowing in the mist. || weather
- A dynamic character portrait || {Subject} {is_are} walking away from the viewer beneath the looming legs of a towering mech walker, a rifle held down at {possessive} side and a loaded pack riding high on {possessive} back - ahead of {object} a ruined industrial refinery burns against a molten sunset. || nogear weather mechyard
- A character portrait seen from behind || {Subject} {is_are} standing on a rocky outcrop in a full pressure suit, watching a hooded rider on horseback beside {object}, a saucer-shaped transport hovering low over the storm-lit desert ahead. || weather
- A dynamic, low-angle character portrait || {Subject} {is_are} walking toward a hulking armored transport at night, snow blowing past its headlamps beneath a huge rising moon, a rifle slung across {possessive} back and a loaded pack riding high between {possessive} shoulders. || nogear weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a burning warship listing low over a harbor city, its hull venting fire and debris raining into the water below. || weather warzone
- A character portrait || {Subject} {is_are} standing on rocky desert ground, gazing up at a massive saucer-shaped vessel hovering low overhead, a handful of armed figures fanned out to one side beneath distant mountains. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a moss-grown cave interior, shafts of pale light breaking through a jagged opening in the rock above. || weather
- A character portrait || {Subject} {is_are} walking alongside a massive scorched engine module borne on a heavy tracked transporter, its hull towering overhead against a darkening sky strewn with distant moons and stars. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-lashed industrial tower lit with tall neon signage, an armored patrol vehicle idling nearby with a gunner perched atop it. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a gleaming glass-and-steel corporate skyline at dusk, its towers mirrored in the still water of a harbor basin. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a gunship descending on burning thrusters toward a grounded transport with its loading ramp lowered, a light vehicle waiting on the tarmac. || weather
- A character portrait seen from behind || {Subject} {is_are} walking away down a rain-slicked alley between weathered concrete blocks, a dense city skyline glowing gold at dusk in the distance ahead. || nogear weather
- A character portrait seen from behind || {Subject} {is_are} walking through a torchlit archway at the base of a towering stone monument, flanked by mounted knight statues rearing on plinths, lightning forking across the storm-wracked sky above. || weather @neogothic
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is the spiked hull of a capital ship gliding above a curving planetary limb, a violet ion trail lancing from a smaller escort craft nearby.
- A character portrait || {Subject} {is_are} walking through drifting fog in a full sealed pressure suit and helmet, approaching the wreck of a grounded transport at the foot of a towering waterfall, three pale suns glowing faint through the clouds above. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a pilot's canopy view over a cloud-wrapped planet, a distant comet streaking past a drifting satellite station. || cockpit
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a pair of sleek exploratory craft cruising low over a violet crystalline planetscape.
- A three-quarter character portrait || {Subject} {is_are} seated in the cockpit of a weathered scout craft, one hand raised to a floating holographic display and the other resting on the control stick, an alien valley of jagged spires and luminous flora spreading beyond the canopy in the early light. || nogear cockpit
- A dynamic, close character portrait || {Subject} {is_are} crouched low in dense forest fern, gripping a compact carbine and sighting it level at the viewer, twin braids falling forward over {possessive} tactical vest - behind {object}, out of focus, sunlit woodland fades into soft green haze. || nogear weather frontline
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a battered gunship descending over a neon-lit rooftop landing pad, armed figures moving between parked vehicles under drifting smoke. || weather @cyberpunk
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a storm-lit neon skyline above crashing surf, lightning forking against a molten dusk sky. || weather @cyberpunk
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a vehicle's dashboard readouts, framing a distant spired ice citadel beyond a shattered frozen plain. || cockpit
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a fleet of angular warships descending through a blood-red sunset toward a spired city, a pale crescent moon hanging above the smoke-dark clouds. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a fleet of black battlecruisers descending through cloud banks over a dense neon-lit metropolis at night. || weather @cyberpunk
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a row of hulking industrial refinery towers rising out of mist above a churning waterfall, a lone worker silhouetted on a platform far below. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a lantern-lit temple perched on a jagged mountain crag, cherry blossoms and a lacquered bridge crossing the pool below. || weather @neosamurai
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a sleek white medical bay lined with reclined beds, a domed skylight open to a field of stars overhead.
- A half-body character portrait || Behind {object}, out of focus, an immense flying superstructure marked with bold hull lettering eclipses the sun over a dense neon-orange sprawl, airships drifting past below. || weather
- A character portrait || {Subject} {is_are} standing beneath a grand stone archway, cradling a flight helmet against one hip - beyond {object} a canyon city strung with waterfalls glows under a crescent-ringed skyline. || nogear weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is an ornate white warship hanging over a barren icy moon, a beam of light lancing down to a distant landing platform.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cluster of slender spired towers and glass-domed habitats floating above a sea of clouds, winged flyers weaving between them. || weather
- A half-body character portrait || Behind {object}, out of focus, is a colossal stone archway framing a sea of clouds, two robed travelers picked out small against the light. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a lantern-lit palace complex of tiered pagodas beside canals and arched bridges, cherry blossoms crowding the banks under a bruised crimson sky. || weather @neosamurai
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a twin-rotor VTOL gunship squatting on broad mechanical legs atop a snowbound stone platform, its canopy dusted with falling snow. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a worn command chair facing a wide viewport onto a blue world, banked control panels to either side and escort ships drifting beyond the glass.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a battered dropship suspended on a hydraulic lift inside a cavernous repair dock, ground crew working small beneath its hull.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a colonnaded marble temple glowing warm at the mouth of a vast stone cavern, tiny figures climbing its lit steps between dark pine slopes. || weather
- A dynamic, low-angle character portrait || {Subject} {is_are} climbing a lit stairway in a sealed EVA pressure suit and helmet toward a spherical station airlock, a second suited figure following a few steps behind - overhead, twin transports drift past a moon's cratered dark and a pale rising world. || vacuum
- A half-body character portrait || Behind {object}, out of focus, a colossal scrap-built mech looms over a ruined industrial yard, small onlookers dwarfed at its feet. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a row of white-and-orange dropships parked wingtip to wingtip on a smoke-hazed industrial airfield, ground crews moving between them. || weather
- A character portrait || {Subject} {is_are} seated at an ornate flight console, one hand steady on the controls while a second crewmember beside {object} works a glowing holographic globe display - beyond the canopy a lightning-lit storm frames a vast crescent-shaped city adrift in the clouds. || cockpit
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a vast ringed station wheeling slowly in orbit, docking spurs and habitation rings glinting beside a cratered moon.
- A half-body character portrait || Behind {object}, out of focus, an immense saucer-shaped mothership hangs low over a sprawling colony settlement, a beam of light lancing down through smoke and scaffolding to a circular platform below. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a fractured asteroid canyon opening onto a molten dying world, a lone attack craft banking past drifting embers and smoke plumes.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a scarred capital ship descending low over a dense colony skyline, a swarm of escort fighters peeling away above the docking spires.
- A dramatic low-angle character portrait || {Subject} {is_are} standing on a storm-lit ridge, gripping a blade that crackles with a colored energy discharge, a jagged bolt of lightning forking down through drifting cloud behind {object} and a bruised violet moon rising over broken stone spires in the distance. || weather swordwork
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is an empty command console ringed with readouts, the light washing teal on one side and deep crimson on the other.
- A character portrait || {Subject} {is_are} kneeling at the edge of a lit pool, reaching to touch a small glowing bloom growing from the water - behind {object} a pair of ring-topped stone archways rise misty from the rock beneath a banded planet. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is the reflective interior of a colossal ship hangar, angular hull plating stacked in tiers as a small craft climbs toward a shaft of light at the open bay doors. || mechyard
- A character portrait || {Subject} {is_are} kneeling among a cluster of luminous alien eggs half-buried in rubble, sealed head to toe in an EVA suit, a colossal bone-white leviathan drifting through a nebula haze in the sky overhead. || vacuum
- A character portrait seen from behind || {Subject} {is_are} walking toward a fog-wrapped megacity, a full-length hooded cloak trailing behind {object}, its towers laced with neon conduit lines climbing ahead beneath a rising moon. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a ruined transit atrium reclaimed by hanging vines and flowering growth, rusted gantries spiraling up toward a distant skyline. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a waterside refinery of towering stacks venting black smoke into a bruised dusk sky. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a sleek twin-hulled naval strike craft cutting hard across open water beneath scattered cumulus cloud. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a scarred long-haul freighter descending low over wind-carved desert spires beneath a rising moon. || weather
- A half-body character portrait || Behind {object}, out of focus, is the golden underside of a colossal ring-shaped structure hovering low over a winding river valley, rows of ancient stone columns descending to the water. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a fog-wrapped ironclad airship bristling with funnel stacks drifting low over a gothic spired skyline, a second hull trailing distant behind it. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a mist-filled canyon strung with floating moss-crowned islets beneath a close ringed planet at dawn. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is the grimy cabin of a rail car, cables and vents crowding the low ceiling and a stray white cat perched on the console before neon high-rises glowing beyond the window. || @cyberpunk
- A dynamic character portrait || {Subject} {is_are} seated commanding a bridge crew through a raging void battle, {possessive} hands braced on the armrests as tracer fire and debris streak past the viewport, officers bent low over consoles to either side - beyond the canopy a besieged fleet burns against the curve of a blue world. || deskwork
- A character portrait || {Subject} {is_are} standing dwarfed beside a towering industrial walker, its thruster housings glowing in the mist, a pale moon rising over the wet tarmac behind {object}. || weather
- A half-body character portrait || Behind {object}, out of focus, is a spindly six-legged artillery walker striding across sun-scorched dunes, its long cannon barrel casting a hard shadow across the sand. || weather
- A character portrait || {Subject} {is_are} standing dwarfed among towering bioluminescent growths trailing long tendrils into a green aurora-lit sky, a banded moon rising beyond the dark canyon walls around {object}. || weather
- A half-body character portrait || Behind {object}, out of focus, is a jagged moonscape horizon beneath a blazing red galactic core smeared low across the night sky.
- A character portrait seen from behind || {Subject} {is_are} standing with two others in near-silhouette, watching a boxy cargo shuttle idle on the tarmac ahead, banks of overhead work lights hazing the fog-thick air of the hangar around them.
- A half-body character portrait || Behind {object}, out of focus, is a fortified floating city bristling with spires, cables trailing down into a sea of cloud beneath a rising sun and a close ringed planet. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is the vast interior dock of a starship yard, a rough-hewn vessel drifting through hanging shafts of blue work light. || mechyard
- A half-body character portrait || Behind {object}, out of focus, is a dreadnought and its escorts lancing crimson beam-fire across the curve of a blue world. || warzone
- A character portrait || {Subject} {is_are} standing on a raised platform, gazing up at a matte white gunship settling through drifting exhaust haze, red-lettered megablock towers looming close behind {object}. || weather
- A half-body character portrait || Behind {object}, out of focus, is a skyline of soaring white spire towers under a close ringed planet at sunrise, transports threading between them. || weather
- A character portrait || {Subject} {is_are} seated at a chart table working an old dial console, a steaming mug and an open logbook at {possessive} elbow - beyond the viewport a formation of escort cruisers drifts against the curve of a blue world. || deskwork
- A half-body character portrait || Behind {object}, out of focus, is an angular strike-wing fighter screaming past camera, twin flare-lit engine trails burning across the open starfield.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a green-clad megacity under twin moons, a needle-nosed cruiser banking low between the towers. || weather
- A half-body character portrait || {Subject} {is_are} standing with both hands braced on a glowing tactical starmap table, briefing gathered officers - a bridge deck overlooking the planet below. || deskwork
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a colossal ring of interlocking clockwork gears turning above a sprawling city, a red twin-engine fighter cutting across its face. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a low-flying gunship streaking between neon-lit towers, motion-blurred against the haze of a smog-choked skyline. || weather @cyberpunk
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a ring-shaped cathedral spire complex hanging in the clouds above green farmland, its overgrown ramparts studded with lit windows. || weather @neogothic
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-slicked market street glowing under foreign-script neon signage, a crowd drifting past a corner bar's stools. || weather @cyberpunk
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a gutted freighter's cargo deck stretching away in tangled girders and dead conduit, grey light leaking through a shattered hull overhead. || @scav
- A full-body character portrait || {Subject} {is_are} standing at a cliff's edge in silhouette, gazing up at a vast lit hull crawling with running lights - sunset breaking beneath a sea of clouds as it passes low overhead. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is an empty shoreline facing a coastal city as a shattered planet burns apart in the sky above the waves. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a matte-black interceptor cutting low across a jagged, snow-capped mountain range, belly lights flickering blue-white. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a retro-styled monorail gliding beneath saucer-topped towers and needle spires, two aircraft streaking past a swollen sunset. || weather
- A half-body character portrait || {Subject} {is_are} glancing back over one shoulder from a cockpit seat, one hand braced on the canopy frame - holographic displays glowing around the controls as a ship streaks past outside. || cockpit
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-slicked avenue glazed green from towering signage, saucer-shaped hovercars gliding low between pedestrians. || weather @cyberpunk
- A full-body character portrait || {Subject} {is_are} riding away from camera down a cracked desert highway - dust trailing behind toward the wreck of a colossal fallen warship jutting from the earth. || weather warzone
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a moonlit river winding through a jagged mountain valley, its peaks pale under a rising moon and a trail of stars. || weather
- A full-body character portrait || {Subject} {is_are} leading two other troopers along a mossy riverbank between sheer jungle cliffs, rifle held ready - birds scattering overhead as they advance. || weather
- A full-body character portrait || {Subject} {is_are} standing atop scattered aircraft wreckage, weight shifted onto one hip - a fighter roaring past low over the sea beyond. || weather
- A full-body character portrait || {Subject} {is_are} crouching on a rain-slicked rooftop ledge, coat snapping in the wind - a city skyline glowing beyond the storm. || weather @cyberpunk
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a sleek transport idling on a sunlit landing pad inside a garden-ringed hangar, distant figures crossing the tarmac as light streams through overhead vents.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a smoke-trailing patchwork freighter descending over a sprawling scrap-metal settlement, its rust-streaked hull catching the last of a desert sunset. || weather @scav
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is an alien valley of feather-leafed rust-orange trees and glowing turquoise blossoms lining a shallow stream, sunlight flaring through drifting motes. || weather
- A full-body character portrait || {Subject} {is_are} threading through a lantern-lit night bazaar of hooded traders and simmering food-stalls, a ringed gas giant glowing beyond the archway ahead. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a stacked concrete megastructure with twin waterfalls crashing between neon-lined catwalks and a vine-choked pedestrian bridge. || weather @cyberpunk
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cliffside temple-city of green-domed rotundas, colonnaded terraces, and towering bronze statues linked by a soaring stone bridge over a waterfall gorge. || weather
- A distant character portrait || {Subject} {is_are} walking away down a fog-shrouded, rain-slicked alley lined with dripping neon signage in a foreign script, puddles smearing the glow underfoot. || weather @cyberpunk
- A full-body character portrait || {Subject} {is_are} leaning on a stone balustrade beside a companion, watching a scarred orange airship drift past a cliffside coastal town. || weather @scav
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a darkened command bridge of glowing multicolor console banks facing a wraparound window over a mountainous coastline. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a line of hooded pilgrims filing along a moonlit mountain path toward a colossal glowing gold ring-gate split into the cliffside. || weather
- A character portrait || {Subject} {is_are} walking through a canvas-tented refugee camp, hooded figures huddled near cookfires as a bombed-out city skyline rises smoke-hazed beyond the tent line. || weather
- A close character portrait || {Subject} {is_are} bent over a soldering iron at a cluttered workbench, a stripped radio chassis and spooled wire crowding the light of a single desk lamp.
- A wide character portrait || {Subject} {is_are} leaning over a cluttered workbench inside a tent-workshop, trading quiet words with a younger companion across a dented kettle and stripped circuit boards - a hazy waterfront skyline visible past the canvas flaps. || weather
- A character portrait || {Subject} {is_are} seated at a cluttered workbench nursing a steaming mug, salvaged radios and instrument racks stacked close behind, a scavenger camp glimpsed through a gap in the tent wall beyond. || nogear
- A wide character portrait || {Subject} {is_are} standing over the central plot table of a sweeping command center, banks of analysts monitoring holo-displays around a wall of windows overlooking a smoke-hazed horizon. || deskwork
- A wide character portrait || {Subject} {is_are} standing dwarfed at the foot of a towering combat mech in its hangar cradle, its optics glowing steady overhead and rows of gantries stretching into the dark bay behind. || mechyard
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a colossal fortress complex, armored transports rolling past ranked troops beneath concrete ramparts rising into an overcast sky. || weather
- A wide character portrait || {Subject} {is_are} striding through a vast mech assembly hangar, gantries and idle loader arms rising to either side, red hazard lights blinking in the gloom farther back.
- A character portrait seen from behind || {Subject} {is_are} standing with back to camera at the foot of a towering combat mech powering up in its gantry cradle, red sensor lights flaring along its chassis. || mechyard
- A wide character portrait || {Subject} {is_are} pointing toward a mech suspended in service gantries, tablet in hand, technicians working cranes and welding rigs around the towering chassis. || nogear
- A wide character portrait || {Subject} {is_are} briefing two companions on an open hangar deck, insignia-marked crates and skeletal gantries rising behind.
- A wide character portrait || {Subject} {is_are} harnessed into a mech cockpit chair, giving a double thumbs-up beneath crimson alert lighting as banks of telemetry screens flank the seat. || cockpit
- A character portrait || {Subject} {is_are} reclined in a battered lounge chair reading a dog-eared book, headphones looped around {possessive} neck and a steel mug cooling on the crate beside them, a faction emblem painted large on the wall behind. || nogear

## Freefall dives toward the viewer

- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} diving directly toward the viewer through a dim ship corridor in freefall, {possessive} body stretched into dramatic foreshortening, one arm reaching forward toward the viewer with open fingers and the other bent up near {possessive} head gripping an unseen handhold above the frame, legs trailing behind {object} in motion, faint streaks of motion blur emphasising {possessive} speed, the corridor's lit panels and hazard striping rushing past. Dramatic foreshortened composition.
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} weightless in freefall, {possessive} body tilted no more than about 30 to 40 degrees off vertical and stretched toward the viewer in strong foreshortening, one gloved hand thrust out at the camera and {possessive} legs trailing loose behind {object}, hair and tether lines floating free, having just pushed off a bulkhead out of frame - behind {object} a darkened docking bay, its running lights streaking past. Dramatic foreshortened composition.
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} weightless in freefall, twisting hard to slip between a crossing lattice of taut laser tripwires, {possessive} body bent and one arm flung wide for balance while the other reaches ahead, loose debris and shattered fragments drifting alongside {object} - the beams cut bright green lines through the dark around {object}, faint structural wreckage receding into the black beyond.
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} weightless in freefall, both arms flung wide overhead and twin long braids drifting loose in the air, {possessive} body arched back in strong foreshortening - beyond {object} the dark hull of a starship interior glints with scattered debris and drifting light.
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} coasting head-on toward the viewer down the central shaft of a colony spoke, arms tucked close and {possessive} body tilted no more than about 30 to 40 degrees off vertical, hair fanned loose around {possessive} face - the shaft's ladder rungs and stencilled level numbers streak away behind {object}. Dramatic foreshortened composition.
- A dynamic character portrait || {Subject} {is_are} turning weightless in the air of a zero-gravity gymnasium ring, one arm sweeping wide and the other tucked close, {possessive} body tilted no more than about 30 to 40 degrees off vertical - behind {object} the inner wall of a colony cylinder climbs away, its terraced farmland hanging overhead through the haze.
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} diving toward the viewer through the open ribs of a colony under construction in freefall, {possessive} body stretched into strong foreshortening with both arms swept back along {possessive} sides and {possessive} legs trailing, girders and taped bundles of cable streaking past to either side. Dramatic foreshortened composition.
- A dynamic, gently canted-angle character portrait || {Subject} {is_are} pushing off hard from a hatch coaming with both feet, {possessive} body already tilted no more than about 30 to 40 degrees off vertical and {possessive} arms folding tight to {possessive} chest, a document wallet tumbling free of {possessive} grip behind {object} - numbered lockers fall away past {possessive} shoulder.
- A dynamic character portrait || {Subject} {is_are} weightless and reaching overhead to catch a stanchion mid-tumble, {possessive} body arched and tilted no more than about 30 to 40 degrees off vertical with {possessive} free arm swept across {possessive} chest - warning strobes wash the corridor around {object} amber and a hatch stands cycling open behind.

## Floating weightless aboard ship

- A close, low-angle character portrait || {Subject} {is_are} floating weightless in a narrow access tube, one arm braced against the wall above {possessive} head and knees drawn up, {possessive} body turned a mild 20 to 30 degrees off vertical with nothing underfoot, small debris and loose tools hanging motionless in the air alongside {object}, dim panel lighting receding down the tube behind.
- A dynamic, gently canted-angle character portrait || {Subject} {is_are} weightless in freefall, body tilted no more than about 30 to 40 degrees off vertical across the frame with one hand reaching out and {possessive} legs drifting loose behind {object}, hair lifted free - around {object} the netted crates of an unlit cargo hold hang untethered in the air, a single work lamp raking across {object} from one side.
- A close, low-angle character portrait || {Subject} {is_are} floating weightless inside a pressurised observation blister, one palm flat against the curved glass above {possessive} head and {possessive} body turned a mild 20 to 30 degrees off vertical, legs drawn up and bent, hair lifted free - beyond the glass the ship's hull curves away and the starfield turns slowly past. Rim lighting along {possessive} silhouette.
- A character portrait || {Subject} {is_are} floating in a darkened observation blister with {possessive} legs drawn up and drifting, one hand steadying against a console rail, a scatter of pens and a loose clipboard hanging motionless in the air around {object} - the room's readouts glow dim across {possessive} face.
- A character portrait || {Subject} {is_are} hanging weightless in a station galley with one boot hooked under a table rail, a drink bulb held loose and {possessive} body turned a mild 20 to 30 degrees off vertical, crumbs and a spoon suspended nearby - stowage netting and taped-up duty notices line the bulkhead behind {object}.
- A character portrait || {Subject} {is_are} braced weightless in a launch tube with both hands on the guide rails, {possessive} body angled a mild 20 to 30 degrees off vertical and {possessive} hair lifted free, gazing away down the tube past the frame - ranked catapult lights recede behind {object} into the dark.
- A character portrait || {Subject} {is_are} drifting weightless down a corridor left dark by a power loss, one hand trailing along the wall rail and emergency chemlights glowing green at intervals past {object}, loose paperwork turning slowly in the air around {possessive} shoulders.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a zero-gravity cargo lock, netted pallets hanging untethered in the air beneath a rank of amber warning strobes.
- A character portrait || {Subject} {is_are} curled loose in a bunk niche's sleep sack with one arm floated free of the netting and {possessive} hair fanned around {possessive} face, {possessive} body turned a mild 20 to 30 degrees off vertical - stowed kit and a taped-up photograph line the niche wall behind {object}.
- A dynamic character portrait || {Subject} {is_are} twisting weightless to catch a thrown wrench, {possessive} body rotating a mild 20 to 30 degrees off vertical with one hand snapping shut on it and the other flung back as counterweight - a workshop's tool boards and a drift of loose swarf hang motionless behind {object}. || nogear
- A close, low-angle character portrait || {Subject} {is_are} hanging inverted with {possessive} boots hooked through an overhead rail and {possessive} head lowest in frame, both hands working at an opened panel above {possessive} face and {possessive} hair falling the wrong way - conduit runs recede past {object} in dim standby light.
- A character portrait || {Subject} {is_are} floating with {possessive} legs drawn up and {possessive} palms cupped around a wobbling sphere of water held in the air before {possessive} face, {possessive} body tilted no more than about 30 to 40 degrees off vertical - a survey bay's racked sample cases and a drifting pen hang behind {object}. || nogear
- A character portrait || {Subject} {is_are} turning slowly weightless inside the gutted interior of a derelict, {possessive} body tilted no more than about 30 to 40 degrees off vertical and one hand fending off a drifting sheet of torn panelling - frozen condensation glitters in the air around {object} wherever {possessive} lamp beam catches it.
- A close character portrait || {Subject} {is_are} floating close to the camera with {possessive} eyes shut and {possessive} hair spread wide around {possessive} head, one hand raised loose beside {possessive} face and {possessive} body turned a mild 20 to 30 degrees off vertical - behind {object} a dark compartment recedes with a single amber standby lamp burning.
- A character portrait || {Subject} {is_are} sitting weightless with {possessive} legs crossed and drifting slightly apart, hands resting loose in {possessive} lap and {possessive} body turned a mild 20 to 30 degrees off vertical, hair lifted free - behind {object} a long observation ring curves away, its windows full of slow-turning stars.
- A character portrait || {Subject} {is_are} reclining weightless within a compact spacecraft workstation, knees bent and one hand resting near a screen as loose hoses loop around {object}. ||

## Glancing back from a rooftop railing

- A character portrait seen from behind || {Subject} {is_are} leaning on a rooftop balcony railing high above a dense city street, glancing back over one shoulder at the viewer - below {object} the street is packed with stacked signage glowing through humid haze, the crowds and wet pavement dissolving into loose, almost impressionistic brushwork. A rooftop awning and railing frame the high vantage point. || weather
- A character portrait || {Subject} {is_are} standing at a rooftop railing in the rain, glancing back over one shoulder, a pair of aircraft streaking low across the skyline behind {object} - below {object} a dense neon high-rise district stretches away into the haze. || weather
- A character portrait seen from behind || {Subject} {is_are} sitting on a rooftop bar's counter ledge, glancing back over one shoulder - a dense rain-soaked high-rise district glows through the downpour beyond {object}, potted plants crowding the rail. || weather
- A character portrait || {Subject} {is_are} turning to glance back over one bare shoulder beside a rooftop railing, a full moon above the bright city beyond. || weather
- A character portrait || {Subject} {is_are} turning to look back from a city rooftop, densely packed lit windows and signs spreading into the haze. || weather
- A character portrait || {Subject} {is_are} standing at a rooftop railing with one hand lifted near the jaw, a vast illuminated city and a bulky parked machine behind {object}. || weather
- A character portrait || {Subject} {is_are} resting one hip against a stair railing on a city rooftop, low banks of lights outlining the broad landing pad nearby. || weather

## Sitting on a rooftop ledge above the city

- A character portrait || {Subject} {is_are} sitting cross-legged on a rooftop ledge, eyes closed in quiet stillness, a sheathed blade laid flat across {possessive} lap - behind {object} a dense night skyline glows through drifting haze, thin trails of aircraft light threading between the towers. || nogear weather
- A character portrait || {Subject} {is_are} sitting cross-legged on a rooftop ledge at night, hands braced behind {object} - beyond {object} a massive ringed planet hangs low over a grid-lit synthwave skyline lined with palm trees.
- A character portrait || {Subject} {is_are} sitting perched on a rooftop ledge, one leg drawn up and a lit cigarette held near {possessive} mouth, gazing out over a vast river-split cityscape glowing under a deep orange sunset. || nogear weather
- A character portrait || {Subject} {is_are} sitting with {possessive} back turned slightly toward the viewer on a high city overlook, dense towers and scattered illuminated signs receding toward a hazy sunset. || weather
- A character portrait || {Subject} {is_are} sitting on a high rooftop edge with one knee raised and hair streaming to one side, the city falling away below. || weather
- A character portrait || {Subject} {is_are} sitting sideways on a high ledge with one knee tucked up, an open jacket hanging loose against a wall of bright city signage. || weather
- A character portrait || {Subject} {is_are} sitting sideways on a rooftop ledge with knees drawn up, laundry lines and a cylindrical water tank silhouetted against apartment towers. || weather

## Standing at a rooftop edge

- A character portrait seen from behind || {Subject} {is_are} standing at the edge of a high rooftop with both arms flung wide, an oversized jacket printed with bold graphic linework across the back - below and behind {object} a dense neon high-rise skyline stretches away into the haze, a single towering spire glowing at the center of the frame. || weather
- A dynamic character portrait seen from behind || {Subject} {is_are} balanced on the tip of a rooftop antenna mast high above the city, one leg braced and bent, a long coat billowing wide in the wind - far below {object} a dense high-rise skyline glitters with countless warning lights through the downpour. || weather
- A wide character portrait || {Subject} {is_are} standing at the ledge of a rain-slick rooftop, {possessive} weight braced on one heel as a neon-veined skyline spreads out far below. || weather
- A character portrait || {Subject} {is_are} standing on a wet rooftop facing a huge low sun, unfinished antenna towers and glowing signage scattered below. || weather

## Night rooftops of masts and tanks

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-dark rooftop overlooking a sprawling night city, tiers of elevated rail viaducts strung with dull red warning lamps threading between the towers and a lone aircraft hanging in the haze above. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a night-time rooftop of rusted water tanks and lattice radio masts, smokestacks trailing plumes across a lit tower-block skyline. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is an industrial rooftop of antenna masts and pipework at night, a fireball blooming over the distant tower blocks. || weather

## Posing with parked cars

- A character portrait || {Subject} {is_are} standing beside a parked muscle car on a dark cyberpunk street at night, one hand braced on the doorframe, glancing up at the looming high-rises ahead - behind {object} the car's tail-lights glow red against the wet pavement. || weather
- A character portrait || {Subject} {is_are} standing beside a parked muscle car on a pastel-lit street at dusk, one hand resting on the open door - behind {object} a tangle of towering cyberpunk architecture rises hazy into the fading light. || weather
- A character portrait || {Subject} {is_are} sitting on the hood of a parked muscle car beneath an enormous full moon, hands braced back against the metal - small dark shapes wheel through the night air above the rain-slick street around {object}. || weather
- A wide character portrait || {Subject} {is_are} standing at the tail of a parked sports car atop a sunlit overlook, weight shifted onto one hip, a distant glass tower rising past scattered clouds. || weather
- A character portrait || {Subject} {is_are} sitting on the broad nose of a parked vehicle beneath the night sky, illuminated towers beyond the landing area. || weather

## Posing with parked bikes

- A character portrait || {Subject} {is_are} leaning back against the flank of a long, low speeder bike parked at a fuel stop, ankles crossed and weight settled easy against the fuselage, a cigarette held forgotten near {possessive} mouth, gazing out at the fading light - behind {object} a hazy golden dusk skyline of distant spires rises beyond a scatter of old fuel pumps and hand-lettered signage crowding the foreground out of focus. || nogear weather
- A character portrait || {Subject} {is_are} seated astride a parked matte-black superbike on a railed overlook, one boot braced against the ground, glancing back over {possessive} shoulder - behind {object} a tiered river city of lantern-lit pagodas and waterfalls spreads below towering spired structures at dusk. || weather
- A character portrait || {Subject} {is_are} reclined against the fairing of a parked speeder bike, one arm draped along the windscreen and chin propped in {possessive} hand - behind {object} a neon-lit street glows in smeared bursts of color through the haze. || weather
- A character portrait || {Subject} {is_are} sitting astride a broad red motorcycle in a cluttered garage, instrument panels and parked cars behind {object}. ||

## Riding bikes at speed

- A dynamic character portrait || {Subject} {is_are} leaning low over the handlebars of a weathered vintage motorcycle, cutting fast across a sunbaked salt flat, {possessive} scarf and hair streaming back in the wind - behind {object} a chain of distant mesas breaks the horizon under a darkening sky. || weather
- A dynamic character portrait seen from behind || {Subject} {is_are} leaning a massive fat-wheeled superbike through traffic on a rain-flooded city highway at night, the rear wheel throwing a sheet of spray as it slips between tail-lit cars - glass towers and lit billboards line the road ahead into the drizzle. || nogear weather
- A dynamic, low-angle character portrait || {Subject} {is_are} hunched forward over the bars of a heavy fat-wheeled superbike tearing down a rain-slick elevated expressway at night, spray fanning off the tyres and the headlamp burning - behind {object} smoke-hazed towers and burning rooftops rise beyond the overpass, lit billboards smeared by speed. || nogear weather

## Vehicle seats at night

- A close character portrait || {Subject} {is_are} seated inside a parked vehicle's cockpit in heavy rain, one hand braced on the wheel, neon shopfronts smearing color across the fogged, rain-streaked windshield ahead. || weather
- A close character portrait || {Subject} {is_are} reclined loose in a vehicle's seat, one arm slung back over the headrest and a knee drawn up, glancing out through a rain-streaked window - neon signage smears past in the dark beyond {object}. || weather
- A character portrait || {Subject} {is_are} gripping an overhead handhold inside a moving vehicle, one arm raised and braced, glancing up and to the side - a night skyline streaks past the window behind {object}.
- A character portrait || {Subject} {is_are} sitting back in a vehicle seat with one arm extended toward the controls, a dense night skyline visible through the side window. ||
- A character portrait || {Subject} {is_are} sitting behind a vehicle steering wheel with one hand resting on its rim, illuminated buildings visible through the side window. ||

## Riding night transit

- A character portrait || {Subject} {is_are} seated in a crowded night transit car, one hand raised holding a drink, oversized headphones clamped over {possessive} ears - behind {object} out-of-focus passengers sway with the motion and neon signage glows through the window beyond.
- A character portrait || {Subject} {is_are} seated inside a transit car at night, gazing out through the window at a dense neon high-rise skyline sliding past, faint circuitry tracing along {possessive} jaw and throat - the glass behind {object} streaks with drifting rain and passing light. || weather
- A half-body character portrait || {Subject} {is_are} sitting hunched over a slim laptop at a train tray-table, hood drawn up against the compartment lights, rain streaking neon signage that smears past the window in long coloured lines.
- A character portrait || {Subject} {is_are} sitting curled into a transit seat with one forearm resting across a raised knee, tall city buildings passing beyond the window. ||
- A character portrait || {Subject} {is_are} sitting beside a wide train window with one forearm resting on the sill, city lights stretching outside. ||

## Waiting at stations and shelters

- A character portrait || {Subject} {is_are} sitting with legs crossed on a slatted station bench, one arm extended along its back beneath circular wall windows. ||
- A character portrait || {Subject} {is_are} waiting beneath a glass-roofed roadside shelter, a backlit advertisement and wet illuminated pavement behind {object}. || weather
- A character portrait || {Subject} {is_are} sitting on a narrow transit bench inside a glass-sided shelter, glowing route panels framing the city behind {object}. ||
- A character portrait || {Subject} {is_are} sitting on a long upholstered transit bench beneath parallel light strips, other passengers distant along the corridor. ||
- A character portrait || {Subject} {is_are} leaning back against a broad station pillar, ankles loosely crossed, illuminated tracks and windows receding behind {object}. ||

## Abandoned transit stations

- A character portrait || {Subject} {is_are} crouching in the entrance hall of an abandoned transit station, ruined escalators climbing toward a broken glazed roof. ||
- A character portrait || {Subject} {is_are} sitting upright on a battered transit bench beneath a broken glazed roof, abandoned escalators rising behind {object}. ||

## Standing in neon street canyons

- A dramatic low-angle character portrait || {Subject} {is_are} standing at street level as a canyon of soaring high-rises rises sheer on every side, towering signage in unfamiliar characters glowing through drifting rain overhead. || weather
- A character portrait || {Subject} {is_are} standing in heavy rain at the center of a narrow street, flanked on both sides by towering high-rises plastered with glowing neon signage in unfamiliar characters. || weather
- A character portrait || {Subject} {is_are} standing with {possessive} back to the viewer in a towering city canyon, bright signs climbing both walls above {object}. || weather

## Walking wet streets at night

- A character portrait seen from behind || {Subject} {is_are} walking away down a narrow alley, one arm a fully articulated mechanical prosthetic at {possessive} side - behind {object} a rain-slicked passage recedes into drifting fog, hazy signage bleeding color low across the wet stone. || weather
- A character portrait || {Subject} {is_are} walking through driving rain across a wet city street at night, other cloaked pedestrians passing beneath the streetlamps - behind {object} an elevated highway curves between the towers and a column of smoke rises from a burning high-rise. || weather
- A character portrait || {Subject} {is_are} walking alone along a wet alley beneath hanging luminous signs, overhead cables disappearing into dense haze. || weather

## Neon tower canyons

- A half-body character portrait || Behind {object}, out of focus, a rain-drenched canyon of stacked towers strung with sagging cables recedes into blue haze, the crumbling wall at {possessive} shoulder overgrown with dripping vines. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a fog-choked canyon of neon-signed high-rises, a four-rotor surveillance drone hanging low in the air overhead with its twin optics burning in the gloom. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a deep avenue of battered tower blocks, vertical luminous signs and wet paving converging into haze. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a freestanding apartment block clad in exposed pipes, its stacked balcony windows glowing over a wet street. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a tower of stacked circular balconies wrapped in glowing cylindrical advertisement panels. || weather

## Industrial tower canyons

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a deep industrial street canyon crossed by pipes and narrow bridges between tiered tower walls. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a canyon between immense tiered industrial towers, bridges and transport lanes crossing at many heights. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a huge horizontal conduit crossing between weathered industrial towers over a haze-filled drop. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is an immense vertical industrial trench with glowing open bays and narrow bridges crossing between dark walls. ||

## Elevated trains between towers

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-slicked elevated transit line threading between towering neon-lit high-rises, billboards glowing in unfamiliar characters. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a city of slender curving towers and elevated transit tracks, a streamlined train passing beneath a low sun. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is an elevated transit platform with a sleek train approaching between illuminated tower blocks. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a streamlined elevated train curving between slender retrofuturistic towers, a broad sun low behind the skyline. || weather

## Flying traffic boulevards

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a vast tiered city traffic complex beneath a passing swept-wing aircraft, circular infrastructure rings rising among the buildings. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a dense city boulevard with parked cars and a broad oval shuttle passing between the upper floors. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is an elevated traffic lane running between enormous towers with glowing inset billboards. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a broad boulevard between rounded luminous towers, sleek hovering vehicles threading between the upper stories. || weather

## Vending machines and street terminals

- A character portrait || {Subject} {is_are} leaning forward with both hands resting above the knees toward a wall-mounted vending display in a narrow illuminated street. || weather
- A character portrait || {Subject} {is_are} standing side-on and reaching toward a wall-mounted public terminal in a narrow city alley. || weather
- A character portrait || {Subject} {is_are} sitting on a bench beside a tall illuminated vending machine in a narrow wet street, dark doorways receding into the distance. || weather

## Street food counters

- A character portrait || {Subject} {is_are} leaning at the counter of a late-night noodle stall beneath a highway overpass, steam rolling off the pass and rain sheeting off the awning's edge into the road behind {object}. || weather
- A character portrait || {Subject} {is_are} sitting on a stool outside a brightly lit food kiosk, one hand raised near {possessive} face and the counter window glowing behind {object}. || weather
- A character portrait || {Subject} {is_are} sitting sideways at a narrow noodle counter with chopsticks lifted over a steaming bowl, stacked dishes and hanging menu boards behind {object}. || nogear

## Diner and bar counters

- A character portrait || {Subject} {is_are} sitting at a wooden counter with legs crossed, warm pendant lamps above and city signs beyond the window. ||
- A character portrait || {Subject} {is_are} sitting on a high stool at a bright diner counter with legs crossed, broad windows and reflected sign light behind {object}. ||
- A character portrait || {Subject} {is_are} leaning forward across a round diner table with both palms resting on its edge, empty upholstered booths stretching behind {object}. ||
- A character portrait || {Subject} {is_are} leaning forward over a bar with both palms on the counter, shelves of bottles and a rain-streaked city window behind {object}. ||

## Night markets

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a crowded station market corridor with waist-high electronics stalls beneath a dense ceiling of pipes. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a crowded night market hall with luminous signs above its stalls and colored floor markings between pedestrians. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a crowded neon market street with overhead cables, layered signs and food counters reflected in wet paving. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a crowded covered night bazaar with hanging lanterns and tightly packed stalls, an enormous moon visible through the open roof. || weather

## Slumped in rain-slick alleys

- A character portrait || {Subject} {is_are} seated low in a rain-slicked alley, jacket half-shrugged off one shoulder and cable straps trailing loose across {possessive} lap, gazing up past the camera - behind {object} neon signage in unfamiliar characters glows through the mist, a server rack blinking against the wall. || weather
- A character portrait || {Subject} {is_are} sitting slouched against a graffiti-tagged wall in a rain-slicked neon alley, one boot planted and the other leg drawn up, {possessive} head tipped back and eyes half-lidded, loose change and a dropped data-chit scattered on the wet pavement beside {object} - behind {object} tangled cable runs and stacked neon signage in unfamiliar characters glow through the drifting mist. || weather

## Sitting on a bunk

- A character portrait || {Subject} {is_are} sitting sideways on an unmade bunk with one knee drawn up, a compact monitor and stacked wall equipment crowding the cabin. ||
- A character portrait || {Subject} {is_are} sitting on the edge of a bunk with one knee raised and an arm resting loosely across it, illuminated towers filling the nearby window. ||
- A character portrait || {Subject} {is_are} sitting on the edge of a low bunk with one elbow on a knee and a hand against the cheek, dim monitors and a shaded lamp lighting the room. ||

## Apartment windows over the night city

- A character portrait || {Subject} {is_are} reclining along a low couch with one arm thrown over its back, wide windows framing the crowded night city. ||
- A character portrait || {Subject} {is_are} sitting sideways on a deep window ledge with knees drawn up, a shaded bedside lamp beside {object} and illuminated towers beyond. ||
- A character portrait || {Subject} {is_are} sitting with legs spread on a worn apartment floor, a small game board between {possessive} knees and a wall of city windows behind. ||
- A character portrait || {Subject} {is_are} sitting at the edge of a sofa facing a panoramic apartment window, a low flying craft crossing above the distant skyline. ||

## Watching the city burn

- A character portrait seen from behind || {Subject} {is_are} seated in a leather lounge chair before a floor-to-ceiling window, looking down on a riot burning through the streets far below, police lights and a gunship's searchlight cutting through the smoke - a potted palm and a lit candle on a side table stand beside {object}.
- A character portrait seen from behind || {Subject} {is_are} standing at a floor-to-ceiling window, watching fires and black smoke roll through the city far below, a spired skyline lit beyond and rain streaking the glass.
- A character portrait || {Subject} {is_are} standing on an elevated industrial walkway overlooking a city consumed by distant fires, smoke rising around an illuminated communications spire. || weather

## Street riots and panics

- A half-body character portrait || Behind {object}, out of focus, a neon-lit city intersection has broken into a riot, cars burning in the road beneath columns of black smoke and crowds scattering across the crosswalks between muzzle flashes. || weather
- A half-body character portrait || Behind {object}, out of focus, a narrow tarp-roofed market alley has turned into a firefight, an armored personnel carrier grinding forward between the stalls with headlights blazing as soldiers trade fire from the balconies above. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-lashed night plaza packed with a frightened crowd, faces turned up toward something vast overhead. || weather

## Walls of monitors

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a wall of humming, dust-caked monitors and tangled cable runs, their pale glow the only light in the room.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cramped hacker's den lit green by a wall of humming CRT monitors, rain streaking a window at the far end. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a wall of stacked CRT monitors and rack decks, every screen showing the same burning streets and the largest cracked clean through.

## Hunched at terminals

- A three-quarter character portrait || {Subject} {is_are} leaning intently over a cluttered workbench, hunched forward and studying something closely, both hands down on a mechanical keyboard - to one side a large monitor glows with dense terminal code, casting light across {possessive} face, and behind {object} a cluttered workshop of stacked machinery, tangled cabling and scattered papers recedes into soft focus under dim overhead light. Warm light on {possessive} face against the cooler background. || nogear
- A character portrait || {Subject} {is_are} seated at a bank of monitors glowing violet and cyan, both hands on the keyboard and dense telemetry scrolling across the screens ahead, thick cable runs hanging tangled from the ceiling around {object}. || nogear
- A character portrait || {Subject} {is_are} hunched at a cluttered desk of humming terminal equipment and tangled cable runs, glancing up sharply at a shadow in the doorway - fluorescent light bars glinting off server racks and taped-up notices behind {object}.

## Repairing electronics

- A character portrait || {Subject} {is_are} leaning forward over an open equipment panel with one arm braced, sparks spilling from the machinery beneath {possessive} working hand. || nogear
- A character portrait || {Subject} {is_are} hunching over a cluttered repair bench, one hand extended among dismantled instruments and stacked test equipment. || nogear
- A character portrait || {Subject} {is_are} kneeling beside a stack of open electronic equipment cases on a cabin floor, one hand reaching toward a control panel. || nogear
- A character portrait || {Subject} {is_are} leaning over an open console with a compact repair tool in hand, exposed leads and sparks visible while a colleague braces the panel beside {object}. || nogear

## Diagnostic chairs and rigs

- A close character portrait || {Subject} {is_are} reclined still in a diagnostic rig, head tipped back and eyes closed, a crown of cabling radiating out from {possessive} temples to banks of softly blinking readouts on either side of {object}.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a dim diagnostic bay, a reclined chair beneath a hooded scanner and thick cable looms dropping from the ceiling to a wall of dark racked hardware.
- A character portrait || {Subject} {is_are} sitting on the edge of a padded exam table in a cramped clinic bay, forearms resting on {possessive} knees, a ceiling rig of folded robotic surgical arms hanging behind {object} and a glowing vitals readout floating at shoulder height beside the table.
- A character portrait || {Subject} {is_are} reclining with {possessive} head tipped back across a broad translucent lit platform, hanging cables and deep machinery shadows surrounding {object}. ||

## Beneath towering war machines

- A dynamic character portrait || {Subject} {is_are} walking straight toward the viewer down a rain-slicked neon-lit street at night, flanked on either side by a pair of hulking bipedal war-mechs looming half into frame, their optics burning dull red in the murk, signage bleeding into smeared reflections on the wet pavement behind them all. || weather
- A character portrait || {Subject} {is_are} standing amid drifting embers and rubble, watching a hulking quadrupedal war-mech stride past close behind {object}, an oversized cannon swinging loose from one of its forelimbs, a small armed flyer banking low overhead - beyond them a bombed-out industrial skyline fades into a bruised violet dusk, fire guttering low among the wreckage. || weather
- A dramatic character portrait seen from behind || {Subject} {is_are} standing still in the rain, gazing up at a towering battle-scarred war-machine looming just ahead, its single core glowing steady in its chest - a dense city skyline rises hazy through the downpour behind {object}. || weather
- A dramatic low-angle character portrait || {Subject} {is_are} standing framed close against the camera, hair and jacket lifted by displaced air, glancing back over {possessive} shoulder as a colossal armored war-machine looms directly overhead - the shot angled steeply upward to emphasise its scale against the neon high-rise skyline beyond. || weather
- A character portrait || {Subject} {is_are} standing in three-quarter profile, a towering red-and-white war-machine looming just behind {possessive} shoulder, its single optic lit - down the street behind {object} red paper lanterns and shopfront signage glow through the night haze. || weather
- A character portrait || {Subject} {is_are} standing in profile beside the towering head of a war-machine looming just behind {possessive} shoulder, gazing out across a hazy industrial skyline as a beam weapon fires from a distant flying craft overhead, faded unit markings stencilled across the machine's scarred plating. || weather

## Sitting on idle machines

- A character portrait || {Subject} {is_are} sitting cross-legged atop the hull of a parked armored vehicle, segmented mechanical prosthetic arms resting in {possessive} lap - behind {object} a dense neon-lit night skyline glows above a heavy cannon barrel angled into frame.
- A character portrait || {Subject} {is_are} sitting cross-legged atop the hull of a parked aircraft at night, {possessive} fully articulated prosthetic hands resting loose on {possessive} knees, gazing up past the frame - behind {object} banks of cloud drift past a star-scattered sky, the aircraft's markings faintly lit along its flank. || weather
- A character portrait || {Subject} {is_are} sitting atop the broad missile-pod shoulder of an idle war-machine, a cigarette smoking forgotten in one hand, looking out over a muddy grey wasteland toward a distant radio mast, the machine's hull marked with a faded heraldic shield insignia and streaked with rain. || nogear weather
- A character portrait || {Subject} {is_are} sitting atop a battered rounded machine hull among scattered snow patches, distant peaks beneath a full moon. || weather

## Beside utility robots

- A character portrait || {Subject} {is_are} standing close beside a bulky round-bodied robot in a narrow city passage, the machine extending one long jointed arm above {object}. ||
- A character portrait || {Subject} {is_are} standing beside a squat round-bodied robot in a crowded illuminated street, thick cables trailing beneath the machine. || weather
- A character portrait || {Subject} {is_are} looking upward from the foot of a metal service stair at a towering yellow utility robot leaning over the railing. ||

## Machines in service cradles

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is an empty suit of crimson humanoid powered armor hanging upright in a cable-strung launch gantry, steam venting from the clamps around it in a cavernous dark bay.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a white-armored war machine standing in a dark service cradle among gantries and hanging cables. ||

## Distant war machines in battle

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a muddy battlefield where two distant war machines exchange beams across churned earth. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a churned battlefield where two distant war machines exchange fire through low smoke and scattered burning wreckage. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a muddy vehicle track winding through blasted scrub, a distant tank and the silhouette of a war machine barely visible through dust. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a line of heavy war machines advancing across a smoke-filled ridge, streaks of weapons fire crossing the haze. || weather

## Lone war machines on open ground

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a squat heavily armored machine with a rotary cannon standing amid dry grass and scattered ruins. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a towering narrow machine with a glowing circular core rising through heavy smoke over a rocky plain. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a broad barren valley with the silhouette of a heavy war machine standing against the low sun. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a lone heavy war machine silhouetted against a pale sunset above a barren rolling plain. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a blocky missile-equipped war machine crossing a treeless ridge beneath a heavy grey sky. || weather

## Escorted by faceless troopers

- A character portrait || {Subject} {is_are} sitting slumped on the bench of a dim dropship troop bay, forearms resting on {possessive} knees, a pair of faceless armored troopers seated close on either side with bulky rifles across their laps - glowing strip-lights run along the bulkhead behind them.
- A dramatic low-angle character portrait || {Subject} {is_are} walking straight toward the viewer out of a long, brightly lit hangar passage, a pair of heavily armored faceless troopers keeping step at either shoulder, one carrying a bulky rifle across its chest - massive blast doors stand open around them, warning lights glowing low at their base.

## Rooftop dropship pads

- A wide character portrait || {Subject} {is_are} walking toward the open side hatch of a matte-black armored dropship parked on a rain-slicked rooftop landing pad, a boarding step set below the door and helmeted troopers seated in the dim bay beyond it - past the hull a burning city skyline smokes under a grey overcast. || weather
- A wide character portrait || {Subject} {is_are} standing at the rail of a rain-soaked rooftop landing pad, watching a heavy black dropship descend on four burning thrusters out of a storm-dark sky - beyond it the towers of a city burn, black smoke columns climbing from their crowns. || weather

## Misty shrine ruins

- x2 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-slick shrine courtyard at dusk, stone steps climbing to wooden eaves hung with a glowing paper lantern, pale fox-shaped shapes moving low through the mist. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is the fog-wrapped wreck of a fallen war-mech looming over a rain-soaked shrine courtyard, its broken frame threaded with strung paper talismans. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a mist-shrouded ruin lit by a single stone lantern, a pale spectral face hovering faint in the gloom. || weather

## Gazing out of viewports

- A character portrait || {Subject} {is_are} gazing up through a viewport in quiet wonder, tubing and cabling trailing from {possessive} suit collar to a bulky comms headset clamped over the ears - beyond the glass a planet's cloud-swirled surface curves away below and a scatter of distant moons hangs in the black.
- A character portrait || {Subject} {is_are} sitting sideways in the open threshold of a spacecraft compartment, a broad planet filling the view beyond the hull. ||
- A character portrait || {Subject} {is_are} sitting curled beside a circular observation window, one hand extended toward a perched pet while a curved orbital structure hangs beyond the glass. ||

## Observation windows onto space

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a thick circular observation port framing a damaged battleship venting fire over a planet. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is an immaculate white observation room with recessed side consoles and a sculpted doorway framing a planet. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is an angular spacecraft observation alcove with bright window borders, a nebula and distant planet visible beyond. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a circular spacecraft viewing window above banks of analog controls, planets and streaks of light filling the starfield beyond. ||

## Empty cockpits and flight decks

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a compact circular flight cabin with two empty seats, wraparound instrument panels and broad luminous windows. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a broad wraparound cockpit canopy with curved transparent readouts suspended above the instrument panel. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a curved spacecraft windscreen framing a distant spired citadel across an ice plain, dark instrument panels below the glass. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a panoramic flight deck with banks of dark consoles, broad windows showing calm blue water and low distant land. ||

## Empty starship bridges

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a warm-lit starship bridge with a raised central command chair and a broad window framing a planet. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a darkened bridge with an empty command chair, low instrument lights and a wide starfield window. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a tan-padded command chair flanked by boxy armrest consoles, a wide observation window opening onto a planet and nearby ships. ||

## Starship lounges

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a compact dark lounge with long padded benches, low tables and repeated triangular light emblems overhead. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a lavish circular starship salon with illuminated floor rings and a panoramic planetary window. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a compact spacecraft lounge with facing bench seats, overhead conduit and a circular dark hatch at the far end. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a bright passenger lounge with curved booths, round tables and luminous recessed ceiling panels. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a crowded shipboard lounge where low tables and glowing wall screens sit beneath heavy exposed ceiling pipes. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a compact spacecraft lounge with a central pedestal console, wraparound screens and recessed strip lights tracing the ceiling. ||

## Shipboard briefing rooms

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a clean shipboard conference room with a long recessed central table, angular chairs and an illuminated ceiling panel. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a dim shipboard briefing room with several crew gathered around a broad illuminated table. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a dim spacecraft briefing room with crew clustered around a central table, ribbed bulkheads and recessed workstations. ||

## Shipboard corridors

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a riveted steel bulkhead door stencilled with a deck number, a keypad lock lit beside it in a cold blue corridor.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cramped service passage lined with exposed overhead pipes, wall racks and small illuminated access panels. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a long angular ship corridor with slanted wall consoles and repeated luminous ceiling recesses. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cylindrical maintenance tunnel ribbed with repeated metal rings, conduits and small monitors lining its full length. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a long arched service tunnel of riveted panels, its ribbed vault lined with alternating small lamps. ||

## Ruined corridors and halls

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cavernous flooded service tunnel of stained concrete and tangled pipework, sparks raining from a broken ceiling fixture onto black standing water.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cavernous ruined machine hall beneath a circular vault, lightning illuminating broken walkways and piled wreckage. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a damaged industrial corridor open to firelit space through a torn overhead hull, reflections trembling along the deck. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a ruined machine corridor with hanging conduits and electrical arcs bridging the broken ceiling. ||

## Overgrown abandoned interiors

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is an abandoned multi-level interior garden, mossy walkways over dark water beneath ribbed metal balconies. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is an abandoned cylindrical station corridor, vines spilling from tiered walkways beneath a broken glazed roof. ||

## Habitat atriums

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a two-storey glazed habitat lounge with recessed seats, indoor trees and exposed ceiling beams. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cylindrical habitat atrium with planted terraces and narrow walkways stacked beneath a circular skylight. ||

## Spaceport aprons

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a compact cargo craft resting on a lit landing pad, exposed tubing and packed machinery covering its rounded hull. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a broad rain-dark spaceport apron crowded with low cargo ships, service equipment and scattered pedestrian traffic. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-dark spaceport apron with a squat transport beside service towers and scattered ground crews. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a broad industrial landing yard crowded with low shuttles, gantries and service roads. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is rows of broad armored shuttles parked nose-to-tail across a smoky industrial apron. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a battered shuttle lifting above a wet industrial apron, a fireball and dense smoke erupting behind its hull. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a heavy freighter hovering over a wheeled industrial loader, exhaust vapor falling around their blocky silhouettes at dusk. || weather

## Shuttles landed in the wild

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a pale shuttle resting on an isolated ice floe among dark open-water channels. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rounded metal shuttle settled in open grassland among grazing animals. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rounded shuttle parked on an icy apron, frost-covered towers beyond its lowered landing gear. || weather

## Shuttle hangars

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a transport hangar with a squat shuttle resting under service gantries, its lowered rear ramp lit from within. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a battered industrial spacecraft suspended in a cavernous repair hall, floodlights picking out gantries, service carts and drifting steam. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a long ribbed spacecraft hangar with a reflective deck and a compact shuttle suspended beneath rows of angular ceiling panels. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a landed shuttle on a polished hangar deck, sunlight falling through high open bays onto encroaching greenery. ||

## Standing by landed shuttles

- A character portrait || {Subject} {is_are} standing beneath the broad engine nacelle of a parked transport inside a cavernous hangar, compact service craft arrayed nearby. ||
- A character portrait || {Subject} {is_are} standing on a sandy landing field beside a low rounded shuttle, flat-topped desert cliffs beyond it. || weather
- A character portrait || {Subject} {is_are} leaning against the curved nose of a parked shuttle on a wet landing apron, distant floodlights and gantries reflected in puddles. || weather
- A character portrait || {Subject} {is_are} standing beneath the raised tail and circular engine of an angular shuttle, its landing struts planted before a pale tower. || weather
- A character portrait || {Subject} {is_are} standing with two companions at the edge of a floodlit hangar, the low faceted nose of a parked shuttle ahead. ||
- A character portrait || {Subject} {is_are} standing beneath a landed shuttle in a multilevel city dock, tall support struts framing stacked walkways and service signs. || weather
- A character portrait || {Subject} {is_are} standing at a rocky landing ledge beside a weathered round-nosed shuttle, a ladder and dock equipment framed by sea cliffs. || weather

## Walking out to waiting craft

- A character portrait || {Subject} {is_are} standing among a loose line of travelers beneath the low hull of a departing transport, another cargo craft looming over the open landing field. || weather
- A character portrait || {Subject} {is_are} walking with a scattered line of travelers toward a landed cylindrical transport on a snowfield beneath an eclipsed sun. || weather
- A character portrait || {Subject} {is_are} walking among travelers toward enormous spherical spacecraft crowded inside an ornate terminal. ||
- A character portrait || {Subject} {is_are} walking beneath a towering spherical lander raised on articulated legs, steam and floodlights spilling across its landing apron. || weather
- A character portrait || {Subject} {is_are} walking with a companion toward an immense wheeled rover, headlamps reflected in the wet landing ground beneath a pale moon. || weather
- A character portrait || {Subject} {is_are} walking with a group beside a huge cylindrical spacecraft mounted on a many-wheeled transporter, a crescent moon above the frozen road. || weather
- A character portrait || {Subject} {is_are} walking with three companions toward a dark landed shuttle in a mist-filled mountain basin, distant floodlights shining through the vapor. || weather

## Beneath ships hovering overhead

- A character portrait || {Subject} {is_are} standing squared to the viewer, a long white coat draped over {possessive} shoulders, an immense capital ship descending directly behind {object}, its hull lit sharply against a burning red city glow far below, drifting haze softening the skyline. || weather
- A character portrait || {Subject} {is_are} standing on a rocky ridge looking toward a broad transport hovering low overhead, a distant moon above the forested valley. || weather
- A character portrait || {Subject} {is_are} standing on a snowy precipice above the clouds, a smooth gold-trimmed vessel hovering level with {possessive} head. || weather
- A character portrait || {Subject} {is_are} standing on a rocky rise with distant companions below, a massive blunt-bowed spacecraft hovering low through fog. || weather
- A character portrait || {Subject} {is_are} standing at a cliff edge above a sea of cloud, the glowing engine bank of a vast dark ship looming overhead at sunset. || weather
- A character portrait || {Subject} {is_are} standing with two companions on a rocky plain beneath a weathered flying saucer, dust hanging beneath its broad circular hull. || weather
- A character portrait || {Subject} {is_are} walking with a companion beneath a bulbous hovering spacecraft, clustered hull lights shining through a rocky mountain pass at night. || weather

## Warships over cities

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a bulky freighter hovering above needle-like city towers, its bank of engine nozzles shining through the haze. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a spired city under a blazing sunset, broad wedge-shaped cruisers hanging above its silhouetted towers. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a dense city lost in cloud, the pointed armored bow of a vast cruiser passing over the towers. || weather

## Finned slab towers

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cluster of tall slab towers capped by sharply slanted pale roof fins above a mist-filled city. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a skyline of narrow dark towers with projecting pale rectangular fins near their tops. || weather

## Floating cities

- A character portrait || {Subject} {is_are} standing on a cliff-edge terrace facing immense floating circular gardens above the clouds. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a city of slender floating stone towers, garden terraces and glass domes suspended over a river. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a vast circular platform suspended over a dense city, a bright column connecting its underside to the urban grid below. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a garden city built across the top and underside of a hovering platform, waterfalls spilling from its hanging terraces into cloud. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a coastal city below tall levitating platforms, slender spires projecting both upward and down through the clouds. || weather

## Cliffside cities with waterfalls

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a surf-filled inlet between dark rock pinnacles, glowing waterfalls spilling from clustered cliffside towers under a low sun. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a moss-covered concrete city built across a river gorge, waterfalls dropping past bridges and stacked apartment walls. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a domed cliffside city connected by high arched bridges, waterfalls descending through the rock beneath its balconies. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cavern settlement with warm-lit rooms and narrow balconies suspended against immense rock walls, mist filling the passage below. || weather

## Storm-lashed coasts

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a flooded coastal city beneath an immense curling storm cloud, rough waves surging between the remaining towers. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is an enormous curling wave dwarfing coastal spires, a tiny craft skimming its face beneath a pale planet. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a black-rock shoreline lashed by surf, needlelike industrial towers rising through storm haze across the bay. || weather

## Industrial harbors and refineries

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is towering industrial pylons with blocky colored upper housings rising above a harbor. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a massive stacked waterside factory with offset platforms jutting above a working harbor. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a chain of blocky industrial platforms lifted above thick fog, bridges and crane arms connecting their illuminated decks. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is an angular refinery bristling with smokestacks, parallel pipelines crossing the foreground beneath dirty storm clouds. || weather

## Monumental ring gateways

- A character portrait || {Subject} {is_are} standing among a line of robed visitors before a colossal circular inset structure, its polished dark center framed by densely carved stone. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a monumental gilded oval gateway on a circular mountainside platform, a line of figures dwarfed beneath its rim. || weather
- A character portrait || {Subject} {is_are} walking along a mossy path toward a colossal crescent-shaped gateway rising from a forest sanctuary. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a vast illuminated circular portal mounted above a tiered platform, luminous particles suspended inside its rim. ||
- A character portrait || {Subject} {is_are} standing on a forested ridge facing a monumental circular gateway set into the mountainside, its inner edge glowing through the mist. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a colossal upright stone ring covered in forests and towers, its open center framing cloud and distant farmland. || weather
- A character portrait || {Subject} {is_are} walking with scattered companions toward an immense luminous ring set into a dark mountainside, worn steps cutting through the grassy slope. || weather

## Rings in the sky

- A half-body character portrait || Behind {object}, out of focus, is a towering sci-fi skyline beneath a colossal glowing ring-shaped structure hanging in the night sky, freighters and cruisers drifting past its light, the streets below slick with rain and threaded with cool running-lights. || weather
- A character portrait || {Subject} {is_are} standing on a rocky overlook above a desert city, a colossal paired-ring structure hovering in the sunset beyond. || weather
- A character portrait || {Subject} {is_are} walking beside a mounted companion across a rocky plain beneath a colossal ring spanning the sky. ||

## Alien vistas under giant planets

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a broad cloud sea with a dark planet looming low above the glowing horizon. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rocky alien shore beneath a vast ringed planet, shallow water reflecting the pale sky. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is an alien river valley dotted with strange plants and jagged mesas beneath enormous pale planets. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a broad wooded valley disappearing into golden mist, the rings of an enormous planet curving across the dawn sky. || weather

## Cratered moons under the stars

- A wide character portrait || {Subject} {is_are} standing motionless on a barren lunar plain, a blue Earth and a river of stars filling the black sky above the jagged horizon.
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a barren cratered plain beneath falling meteor fragments and a streaked starfield. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cylindrical spacecraft wreck half-buried in a cratered plain beneath a hard starfield. ||
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a bare cratered moon plain beneath a broad red-streaked nebula and dense stars. ||

## Shattered worlds on fire

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is an alien coastline under a fractured burning planet, molten channels running between dark coastal ruins. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is an immense fiery ring rising over a fractured city and molten chasms, a distant spacecraft silhouetted against its center. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a deserted shore with an empty deck chair, immense burning planetary debris hanging over a ruined coastal city. || weather

## Alien gardens

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a lush ravine of broad alien flowers and orange-leaved trees, narrow waterfalls dropping into a misty pool. || weather
- A character portrait || {Subject} {is_are} kneeling beside a shallow pool with one hand extended toward a glowing alien flower, crystalline growths and ruined arches beneath a vast moon. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rocky alien grove with towering jellyfish-like growths, translucent caps trailing luminous tendrils above tangled roots. || weather
- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a dense alien garden with oversized orange rosettes, branching ferns and tiny glowing flowers under a bright sky. || weather

## Walking toward colossal wrecks

- A character portrait || {Subject} {is_are} standing before the hull of a beached derelict starship, reaching up to touch a faint glowing panel set into its plating - behind {object} the ship's saucer-like silhouette looms against a field of stars.
- A character portrait || {Subject} {is_are} walking across rippled dunes toward the tilted wreck of a colossal spacecraft, its broken spine silhouetted against smoke and sunset. || weather
- A character portrait || {Subject} {is_are} walking along a cracked roadway through a barren salt plain toward a colossal broken fin-shaped structure leaning out of the haze. || weather

## Dwarfed by colossal structures

- A character portrait || {Subject} {is_are} standing in the shadow of a colossal suspended industrial structure, further hanging masses fading into mist beyond {object}. || weather
- A character portrait || {Subject} {is_are} standing alone before a colossal dark tower scored with illuminated vertical channels and circular ports, a pale moon rising above low fog. || weather
- A character portrait || {Subject} {is_are} walking toward a tall hovering tower above a ruined city square, scattered small craft circling through storm clouds. || weather
- A character portrait || {Subject} {is_are} walking through a deserted city passage beside an immense tilted architectural slab, the towers ahead reflected in rainwater. || weather
- A character portrait || {Subject} {is_are} standing at the foot of a tall narrow monument between two equestrian statues, lightning-bright clouds behind its pointed crown. || weather

## Dig sites and survey camps

- A half-body character portrait || Behind {object}, softly blurred well out of focus, is a mud-churned drilling camp under a rain-heavy sky, a lattice derrick and crawler crane rising over rows of low field tents in the drizzle. || weather
- A close character portrait || {Subject} {is_are} huddled with a handful of field technicians under a dim canvas tent, faces lit from below by the glowing slates in the others' hands, rain-dark tarpaulin sagging behind {object}.
- A low-angle character portrait || {Subject} {is_are} standing at the crumbling lip of a freshly dug excavation pit at night, floodlights glaring through drifting haze - behind {object} a drilling tower and sagging canvas field tents loom over a scattered line of survey crew. || weather
- A dramatic low-angle character portrait || {Subject} {is_are} climbing down a sagging rope ladder into a vertical rock shaft, one hand locked on a rung and a headlamp beam cutting through the dust - far overhead the shaft's jagged mouth opens onto pale daylight, a second climber silhouetted against it.
- A low-angle character portrait seen from behind || {Subject} {is_are} standing among a line of harnessed survey crew on the floor of a vast cavern, floodlights stabbing up into the dark toward the colossal buried silhouette of something ancient and machine-shaped overhead.

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
- hunched forward in a wide-legged brawler's crouch, shoulders rolled and both arms hanging loose and ready, weight pitched onto the balls of the feet || hands
- standing turned three-quarters away with one arm locked straight out, sighting down {possessive} weapon || armed gun
- caught mid high-kick, one leg driven straight up level with the shoulder, the weapon held out in the opposite hand for balance || armed
- kneeling low, braced on one forearm, the other hand gathering a long braid back over the shoulder || hands
- crouching low with the weapon raised in a two-handed grip, weight thrown hard to one side || hands armed gun
- braced in a deep forward lunge, both arms locked out and {possessive} weapon sighted level || hands armed gun
- standing with one knee drawn up high, {possessive} weapon raised in both hands and sighted past the viewer || hands armed gun
- holding one hand lightly across the mouth with the head bowed and the other arm relaxed
- pitching the torso forward with one arm reaching ahead and the other swept backward, knees bent beneath the body
- crouching with one knee lifted, the torso twisted and one elbow drawn back while the other forearm reaches forward
- leaping with both arms spread wide, both knees bent backward and the chest lifted || hands
- kneeling on one knee, both arms extended together to aim it directly ahead || hands armed gun
- crouching with one knee raised, torso turned sideways and one forearm resting across the raised knee
- raising one index finger beside {possessive} head, elbow bent and chin tipped toward the viewer

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
- standing side-on with one hip cocked, glancing down over {possessive} shoulder

## Animation

<!-- Positive prompts for animate-portrait.py (Wan 2.2 image-to-video), one
     per bullet. Not an NPC trait: generate-npc.py never rolls this table and
     neither image prompt reads it. Readers are `animate-portrait.py --roll`
     and the import GUI's Animated portrait panel.

     Written to animate a portrait without changing who is in it. Wan moves
     what the prompt names, so each bullet keeps the figure still - breathing,
     at most a blink or a glance - and spends its motion on what the figure
     wears (hair, scarves, coat tails, straps, a hat brim) and on the scene
     behind them (smoke, cloud, rain, snow, embers, neon, starfields, ships,
     distant gunfire). The closing clause pins the camera; Wan invents a
     dolly-in given the chance, and a portrait that drifts stops being the
     portrait it started as. Keep that clause on anything you add. Pronouns
     are neutral on purpose, since one bullet serves every NPC. -->

- the character stands still breathing gently. the wind gently moves their hair. the smoke in the background gently drifts by. the camera is locked off and does not move.
- the character holds still, breathing slowly. their scarf and loose clothing ripple in a light breeze. clouds drift slowly across the sky behind them. the camera is locked off and does not move.
- the character breathes gently and blinks once. strands of hair lift and settle in a soft wind. stars glitter faintly in the background and a single shooting star streaks past. the camera is locked off and does not move.
- the character stays still. the tails of their coat sway in the wind. far behind them a spaceship slowly crosses the sky, its engine lights pulsing. the camera is locked off and does not move.
- the character breathes steadily. dust and sparks drift through the air around them. distant muzzle flashes and tracer fire flicker silently in the background. the camera is locked off and does not move.
- the character stands calmly. rain falls steadily in the background and water drips from the brim of their hat. their eyes slowly shift to one side and back. the camera is locked off and does not move.
- the character holds still, breathing gently. neon signs in the background flicker and pulse. steam rises and drifts past behind them. the camera is locked off and does not move.
- the character breathes slowly. a strap hanging from their gear sways slightly. holographic readouts in the background scroll and flicker. the camera is locked off and does not move.
- the character stands still. snow falls gently and settles on their shoulders and hair. their breath fogs faintly in the cold air. the camera is locked off and does not move.
- the character stays still, breathing gently. the light of a flickering flame plays across their face and clothing. embers rise and drift away in the background. the camera is locked off and does not move.
- the character holds still. the fabric of their clothing stirs in a low breeze and loose hair drifts across their face. far behind them, dropships descend slowly through hazy clouds. the camera is locked off and does not move.

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
