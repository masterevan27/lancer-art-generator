# Random NPC Generator Tables

Roll tables for `Scripts/generate-npc.py`, which rolls one human NPC from these
lists and generates a matched pair of images in the campaign's house style: a
half-body **portrait** for the Foundry actor sheet, and a full-body **token** on
flat white that gets run through RMBG into a transparent PNG.

These are *people* — pilots, contacts, dockhands, corpo liaisons — not mechs.
Mech art lives in `mech-catalogue-art-prompts.md` and is authored per chassis
rather than rolled.

## How the script reads this file

Every `## Heading` starts a table; every `-` bullet under it is one option. The
script looks tables up by their heading, so **renaming a heading breaks the
prompt template** — add and remove bullets freely, but leave the headings alone.

Weights are optional: a bullet may start with `xN ` to count as N entries, so
`- x4 nondescript grey work coveralls` shows up four times as often as a plain
bullet. Anything after the weight is used verbatim in the prompt, so write
bullets as sentence fragments that read correctly when dropped into the
templates at the bottom of this file.

A bullet may also contain a pronoun placeholder — `{subject}`, `{object}`,
`{possessive}` and their capitalised forms, plus `{is_are}` and `{carry}` for
verb agreement — which is filled from the same roll. That is how the Age table
reads "in her forties" or "in their forties" without a separate table per
pronoun set.

HTML comments, blank lines, and any prose paragraph that isn't a bullet are
ignored — so notes like this one are safe to leave inline.

---

## Given names

- Adaeze
- Anselm
- Ayodele
- Beatriz
- Cai
- Camille
- Dmitri
- Eleni
- Esperanza
- Fen
- Gabriel
- Hana
- Idris
- Ingrid
- Isabela
- Jae-won
- Junia
- Kasimir
- Kwame
- Lior
- Lucia
- Mahmoud
- Marisol
- Nadia
- Nkechi
- Oksana
- Osric
- Priya
- Quintus
- Rashida
- Rosalind
- Sanjay
- Selin
- Sipho
- Tamsin
- Thandiwe
- Tobias
- Ulla
- Valentina
- Wen
- Xiulan
- Yusuf
- Zaid
- Zora

## Family names

- Abara
- Achterberg
- Adeyemi
- Baptiste
- Beaumont
- Castellan
- Chaudhry
- Dalisay
- Delacroix
- Egwuatu
- Farkas
- Fontaine
- Gao
- Halvorsen
- Ibarra
- Ikeda
- Jarrah
- Kalu
- Karras
- Lindqvist
- Machado
- Marchetti
- Mbeki
- Nakamura
- Okonkwo
- Oyelaran
- Petrov
- Quintero
- Rahimi
- Reyes
- Sandoval
- Sarkisian
- Sokolova
- Tanaka
- Thorne
- Ubeda
- Vasquez
- Volkov
- Whitlock
- Xu
- Yildirim
- Zabala

## Callsigns

<!-- Used in the dossier, not in the art prompts. -->

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

## Pronouns

<!-- Subject/object/possessive; the script splits on the slashes. -->

- she/her/her
- he/him/his
- they/them/their

## Age

- x2 in {possessive} early twenties
- x3 in {possessive} late twenties
- x3 in {possessive} mid-thirties
- x2 in {possessive} forties
- in {possessive} fifties, weathered but unslowed
- old enough that the war stories are first-hand

## Build

- x2 lean and wiry
- x2 compact and solidly built
- broad-shouldered and heavyset
- tall and rangy
- short and densely muscled
- thin to the point of looking underfed
- soft-bodied, plainly not a field operator

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
- sandy hair going prematurely white at the temples
- a slicked-back corporate cut, not one strand out of place
- hair hacked off short and uneven, clearly self-cut

## Eyes

- dark, steady eyes
- pale grey eyes that give nothing away
- one eye replaced by a matte optical implant with a faint glowing aperture
- deep-set eyes ringed with fatigue
- bright hazel eyes, quick and reading everything
- narrow eyes half-lidded in permanent skepticism
- eyes clouded by an old flash-burn, scarred at the lids

## Feature

- a spray of old burn scarring up one side of the jaw
- a faded unit tattoo on the side of the neck
- a printed prosthetic forearm, its casing scuffed back to bare polymer
- a broken nose set badly and never corrected
- subdermal port housings tracked along the temple and collarbone
- a jagged shrapnel scar crossing one eyebrow
- knuckles thickened by years of manual work
- no distinguishing marks at all, which is itself a little strange

## Demeanor

- a flat, unimpressed expression
- a guarded half-smile that never reaches the eyes
- a tired, patient look, as if waiting out a long shift
- an open, disarmingly friendly expression
- a set jaw, plainly spoiling for an argument
- a distracted look, attention half on something out of frame
- a calm, unreadable expression giving nothing away
- a wry, crooked grin

## Role

- a mech pilot
- a chief mechanic
- a dockworker
- a freelance salvager
- a corporate liaison officer
- a field medic
- a Union inspector
- a smuggler
- a comms and sensors operator
- a mercenary squad lead
- a colonial administrator
- a bar owner and information broker
- a maintenance technician
- a security officer
- a data courier
- a scavenger-priest of a local machine cult

## Faction

- x2 unaligned and freelance
- x2 in worn Union Administrative Department kit
- in Harrison Armory service dress, imperial and immaculate
- in Smith-Shimano Corpro corporate wear, sleek and expensive
- in IPS-Northstar workwear, riveted and salt-stained
- in Karrakin baronial livery, formal and slightly archaic
- in the mismatched kit of a colonial militia
- in the deliberately anonymous gear of someone who does not answer questions

## Outfit

- a heavy work jacket over a stained undersuit, sleeves shoved to the elbow
- a fitted flight suit with the top half unzipped and knotted at the waist
- layered grey work coveralls patched at both knees
- a long weatherproof coat over practical fatigues
- a tailored jacket cut close, with a high collar
- an armored vest worn over civilian clothes, its plates visibly mismatched
- a sleeveless thermal top, arms bare, forearms wrapped in worn tape
- a hooded utility poncho over a pressure-suit liner

## Gear

- a battered data-slate tucked under one arm
- a heavy multitool holstered at the hip
- a sidearm holstered high on a chest rig
- a coil of cabling and diagnostic leads slung across the body
- a scarred pilot's helmet carried in the crook of one elbow
- a compact rebreather clipped at the collar
- a shoulder-slung tool bag, its strap worn through and re-stitched
- a slim wrist-mounted holographic interface projecting faint readouts
- a cigarette burned nearly to the filter, held forgotten
- nothing at all, hands loose and empty

## Accent

<!-- The single saturated glow color in an otherwise restrained frame. -->

- x3 teal-green
- x2 amber
- dull copper-orange
- cold blue-white
- sickly yellow-green
- deep violet
- brass-gold

## Backdrop

<!-- Portrait only; the token is always flat white for background removal. -->

- the dim interior of a mech hangar, gantries and chain hoists receding into shadow
- a cramped cockpit lit only by instrument readouts
- a rain-streaked colonial street at night
- the cluttered back room of a repair shop, parts racked floor to ceiling
- a station corridor lined with conduit and hazard striping
- an operations room wall of tactical displays
- the open bay door of a dropship, a pale sky beyond
- a bar interior, out-of-focus figures at the tables behind

## Stance

<!-- Token only. -->

- standing in a relaxed, watchful stance, weight settled evenly on both feet
- standing squared and formal, hands clasped behind the back
- standing with arms folded, weight shifted onto one hip
- standing loose and off-balance, one thumb hooked in a belt loop
- standing braced and alert, hands ready at the sides
- standing with hands pushed into jacket pockets, shoulders raised

---

## Prompt templates

These are the sentences the script assembles the rolled traits into. They are
reproduced here so the style is visible in one place alongside the tables, but
they live in `generate-npc.py` — editing them here changes nothing.

### Portrait (1024x1024, straight to the Foundry actor sheet, no background removal)

> A half-body character portrait of **{ROLE}**, **{AGE}**, rendered in a detailed
> painterly illustration style with fine grain texture and clean linework, halftone
> dot shading worked into the shadows, moody cinematic lighting. {SUBJECT} is
> **{BUILD}**, with **{SKIN}**, **{HAIR}**, and **{EYES}**, and **{FEATURE}**,
> wearing **{OUTFIT}**, **{FACTION}**. {POSSESSIVE} face carries **{DEMEANOR}**.
> {SUBJECT} carries **{GEAR}**. Behind {OBJECT}, softly blurred well out of focus,
> is **{BACKDROP}**, its lights casting a faint **{ACCENT}** glow across one side
> of {POSSESSIVE} face, contrasted against warm dim ambient light on the other.
> Keep the palette restrained — greys, olive drab and rust — with **{ACCENT}** as
> the only saturated color in the frame. Shallow depth of field, centered
> composition, square framing, high detail, atmospheric sci-fi character portrait.

### Token (1024x1280, then RMBG to a transparent PNG)

> A full-body character illustration of **{ROLE}**, **{AGE}**, standing and facing
> directly forward, entire body visible from the top of {POSSESSIVE} head to the
> soles of {POSSESSIVE} boots with clear empty space above and below, rendered in a
> detailed painterly illustration style with fine grain texture and clean linework,
> halftone dot shading worked into the shadows. {SUBJECT} is **{BUILD}**, with
> **{SKIN}**, **{HAIR}**, and **{EYES}**, and **{FEATURE}**, wearing **{OUTFIT}**,
> **{FACTION}**. {POSSESSIVE} face carries **{DEMEANOR}**. {SUBJECT} carries
> **{GEAR}**, picked out with a single **{ACCENT}** glow accent. {SUBJECT} is
> **{STANCE}**, boots fully planted and visible, looking straight ahead. Keep the
> palette restrained — greys, olive drab and rust — with **{ACCENT}** as the only
> saturated color. The background is a solid flat plain white, no texture, no
> gradient, no shadow, no environment. Centered composition, even lighting,
> isolated character illustration, clean silhouette.

### Settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt — the same
generation settings as every other prompt file in this folder.
