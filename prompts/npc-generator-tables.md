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

A bullet may also contain a pronoun placeholder — `{subject}`, `{object}`,
`{possessive}` and their capitalised forms, plus `{is_are}` and `{carry}` for
verb agreement — which is filled from the same roll. That is how the Age table
reads "in her forties" or "in their forties" without a separate table per
pronoun set.

Where a placeholder isn't enough, a table can have a **per-pronoun variant**,
in one of two forms:

- `<Table> (she)` is used **instead of** `<Table>` when she/her is rolled.
  `Build (she)` works this way, because the masculine builds should not apply
  at all.
- `<Table> (she) +` is **added to** `<Table>`. `Hair (she) +`, `Eyes (she) +`,
  `Feature (she) +`, `Outfit (she) +`, `Demeanor (she) +` and `Stance (she) +`
  all work this way, so a woman can roll any of the neutral options as well as
  the feminine ones — a woman in grey coveralls stays entirely possible.

`(he)` and `(they)` variants work identically; neither has one yet. The script
has no idea which traits are gendered, so adding `Hair (they) +` or
`Outfit (he)` needs no code change — drop the heading in and it is picked up.
Weights apply inside variant tables too, which is the dial for how often a
feminine option comes up.

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

- x2 in {possessive} late twenties, jaw and cheekbones fully adult
- x3 in {possessive} early thirties, the first lines already setting around the eyes
- x3 in {possessive} mid-thirties, face lean and weathered
- x2 in {possessive} forties, grey coming in at the temples
- in {possessive} fifties, weathered but unslowed, deeply lined
- old enough that the war stories are first-hand, face heavily creased
- weathered well past what {possessive} years alone would explain, deep lines across the face from too long out in bad weather

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
-->

- x2 full-busted and curvy, with a clearly defined waist and wide hips
- x2 soft and full-figured, broad at the bust and hips
- tall and statuesque, hourglass-figured with long legs and a narrow waist
- lean and athletic, narrow-hipped and small-busted
- wide-hipped and sturdy through the thighs, heavy-boned
- ample and heavy-set, thick through the arms and midsection
- lithe and slender, with fine shoulders and a long neck
- broad-shouldered and muscular, carrying obvious strength

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
- a heavy dark braid falling past the shoulder
- long hair worn loose and unkempt, shoved back out of the face
- a high, tight topknot
- fine ash-blonde hair cut level with the jaw
- thick auburn hair pinned up off the collar
- a close fade with a longer sweep left on top
- greying hair tied back in a short tail
- a wrapped headscarf with a few strands escaping at the temple
- a choppy shoulder-length cut, dark with subtle magenta undertones
- a short black bob with a single bright-streaked forelock
- long pale silver-white hair fading to green at the tips
- long dirty-blonde hair fading pale at the tips, cut with blunt bangs
- a short blonde bob with a loose curling cowlick
- dark wavy hair caught mid-motion in the wind
- salt-and-pepper hair cropped close

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

## Eyes (she) +

- dark eyes with long lashes, steady and level
- expressive eyes ringed in smudged black liner
- bright eyes beneath sharply arched brows

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
- permanently a few days past a decent shave
- a compact armored gauntlet on one forearm with a small glowing sensor ring
- both arms mechanical cybernetic prosthetics, tan and cream, heavily articulated with visible joints, wiring and battle-damage scuffing
- both legs sleek mechanical prosthetics with exposed joints and a small lit panel at the thigh
- one sleek segmented prosthetic arm, a single small glow breaking through at the joint
- visible mechanical seams and joint lines across the shoulders, marking {object} as a cyborg
- thin tear-like markings traced beneath both eyes
- a small barcode stamped at the collarbone
- a diagonal scar cutting clean across one eye

## Feature (she) +

- a fine gold chain at the throat, the only thing on {object} not issued
- small hoop earrings worn thin and dented
- chipped dark polish on bitten nails
- a delicate line of old piercings climbing one ear
- a faded floral tattoo curling over one shoulder
- a wedding band worn on a cord rather than a finger

## Headgear

<!--
  Complete sentences, like Backdrop - a fragment would not sit cleanly between
  the outfit clause and the expression. Roughly a third of rolls come up
  bare-headed; reweight that first bullet to change how often headgear shows.
-->

- x6 {Subject} {is_are} bare-headed.
- x2 {Subject} {wear} a padded flight headset, earcups clamped over the ears and a boom mic swung down to the corner of {possessive} mouth, a coiled cable trailing from one side.
- x2 {Subject} {wear} a slim hairband holding the hair back off {possessive} face.
- {Subject} {wear} a lightweight comms earpiece with a slender mic arm tracking along the jaw.
- {Subject} {wear} scratched flight goggles pushed up onto {possessive} forehead.
- {Subject} {wear} a soft crew cap pushed back on {possessive} head.
- {Subject} {wear} a padded pilot skullcap with the visor unclipped and folded back.
- {Subject} {wear} a rolled bandana tied across {possessive} brow.
- {Subject} {wear} a knitted watch cap pulled down to the eyebrows.
- {Subject} {wear} an armored half-helm with the faceplate hinged open.
- {Subject} {wear} a full flight helmet in scuffed pale grey-white, a tinted visor panel down over the eyes and a small lit accent lens at the temple, a thin tether cable trailing from the back.
- {Subject} {wear} a monocular sensor rig strapped over one eye, its lens faintly lit.
- {Subject} {wear} heavy ear defenders slung around {possessive} neck rather than on {possessive} head.
- {Subject} {wear} a welding visor tipped back on top of {possessive} head.
- {Subject} {wear} a worn ushanka-style fur hat with the flaps down, a faded unit star pinned to the front.
- {Subject} {wear} a tactical cap with a small circular unit emblem, dark sunglasses beneath it.
- {Subject} {wear} a night-vision helmet with the quad tubes flipped up clear of {possessive} eyes.
- {Subject} {wear} a sleek black mechanical headset piece mounted flush against one ear.

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

## Role

- a mech pilot
- a starship pilot
- a chief mechanic
- a dockworker
- a freelance salvager
- a corporate liaison officer
- a field medic
- a Union inspector
- a smuggler
- a pirate
- a Union marine soldier
- a comms and sensors operator
- a mercenary squad lead
- a colonial administrator
- a bar owner and information broker
- a maintenance technician
- a security officer
- a data courier
- a scavenger-priest of a local machine cult
- a mercenary sniper
- an elite mercenary pilot
- a close-quarters blade specialist

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
- a quilted thermal jacket over layered underlayers
- a canvas work apron over rolled shirtsleeves
- a pressure-suit undersuit with the armor plates stripped off
- a battered leather jacket gone soft with years of wear
- full combat fatigues in faded digital camouflage, sleeves rolled to the elbow
- a military field jacket over webbing and a loaded chest rig
- a plated combat harness over a dark undersuit, magazine pouches across the front
- scuffed marine carapace armor, repainted in patches, helmet clipped at the belt
- a formal dress uniform, high collar and rank tabs, cuffs pressed sharp
- an armored greatcoat over uniform trousers bloused into boots
- a dust-caked desert-pattern field uniform, a shemagh loose at the neck
- a flak vest over a sweat-stained uniform shirt, tags visible at the collar
- an EVA-rated hardsuit with the helmet seals open and the gauntlets stowed
- a recon smock in broken-pattern camouflage, hood down, face paint half worn off
- a black tactical jacket, unzipped and open, its interior lining faintly glowing, over a fitted dark bodysuit with light plating at the shoulders, forearms and shins
- a sleeveless black tactical bodysuit with an exposed back framed by a cybernetic support harness, thin glowing circuit lines running along the spine and shoulder blades
- a worn olive field jacket with the collar up over a dark turtleneck and tactical webbing, fingerless gloves
- a weathered field jacket stencilled with a unit number and a small hazard warning patch, hanging open over a cropped top
- a tan tactical vest hanging open over a torn cropped tank, one arm wrapped in bandaging, worn cargo trousers
- an oversized open shirt draped loosely over a dark cropped tank
- a high-collared black tactical pilot jacket with glowing cable tubing threading down the front

## Outfit (she) +

<!--
  Feminine cuts, added to the neutral options above rather than replacing them -
  a woman in grey coveralls is entirely normal and should stay possible.

  The armored-bodyglove entries deliberately name no glow color: the palette
  sentence in the template already makes the rolled Accent the only saturated
  color, so "glowing seam lines" picks it up instead of fighting it.
-->

- x2 a fitted flight suit tailored close through the waist and hips
- a cinched belted jumpsuit, collar open at the throat
- a cropped utility jacket over a high-waisted work skirt and heavy tights
- a wrap-front tunic belted at the waist over close-cut trousers
- a sleeveless coverall unzipped to the waist over a fitted tank, arms bare
- a long knitted cardigan over practical fatigues, sleeves pushed up
- a tailored corporate blouse and narrow skirt, immaculate against the grime
- a close-fitting pilot undersuit worn without its outer shell
- a dress uniform tailored to the figure, fitted jacket over a straight skirt and polished boots
- combat fatigues taken in through the waist, sleeves rolled, webbing cinched tight
- a fitted armored bodyglove under a partial plate harness
- x2 a white-and-grey armored hardsuit of scuffed fitted plates over a black bodyglove, glowing seam lines tracing the limbs
- a black tactical jacket with piped trim over a close grey bodyglove and armored thigh-high boots
- a black military jacket with dull gold trim, worn open over a dark bodysuit and chipped white armor plates
- a white field jacket thrown open over a black bodyglove traced with faint glowing conduit lines
- a sleeveless flight harness of buckled straps over a black bodysuit, a single lit indicator strip down the chest, arms bare
- a close-cut pilot bodyglove in white and grey with lit seams and partial shoulder plating
- a sleek fitted flight suit, dark through the torso with silver-white segmented plating at the hips and thighs, thin glowing circuit piping tracing the shoulders, chest seam and zippered front

## Outfit (she) +

<!--
  Feminine cuts, added to the neutral options above rather than replacing them -
  a woman in grey coveralls is entirely normal and should stay possible.
-->

- x2 a fitted flight suit tailored close through the waist and hips
- a cinched belted jumpsuit, collar open at the throat
- a cropped utility jacket over a high-waisted work skirt and heavy tights
- a wrap-front tunic belted at the waist over close-cut trousers
- a sleeveless coverall unzipped to the waist over a fitted tank, arms bare
- a long knitted cardigan over practical fatigues, sleeves pushed up
- a tailored corporate blouse and narrow skirt, immaculate against the grime
- a close-fitting pilot undersuit worn without its outer shell

## Gear

- a battered data-slate tucked under one arm
- a heavy multitool holstered at the hip
- a sidearm holstered high on a chest rig
- a rifle slung over {possessive} shoulder
- a rifle held in {possessive} hands
- a katana with a colored glowing accent along its edge slung over {possessive} shoulder
- a katana with a colored glowing accent along its edge held in {possessive} hands
- a coil of cabling and diagnostic leads slung across the body
- a scarred pilot helmet carried in the crook of one elbow
- a compact rebreather clipped at the collar
- a shoulder-slung tool bag, its strap worn through and re-stitched
- a slim wrist-mounted holographic interface projecting faint readouts
- a cigarette burned nearly to the filter, held forgotten
- nothing at all, hands loose and empty
- a bundle of rolled schematics under one arm
- a heavy pry bar hooked through a belt loop
- a caged inspection lamp trailing a length of cable
- a bandolier of tool bits worn across the chest
- a sealed sample case cuffed to one wrist
- a folded jacket slung over one forearm
- a sheaf of stamped requisition forms
- a dented thermos of something long gone cold
- a service pistol worn openly at the thigh
- a folded maintenance drone perched dormant on one shoulder
- a compact sidearm holstered at the hip and a utility belt of pouches at the waist
- a sheathed katana crossed against {possessive} back alongside a second, shorter blade
- a long-barrelled scoped rifle held upright at {possessive} side, stock resting near one boot
- a battered leather-bound ledger tucked in a breast pocket, worn soft from handling
- an AK-pattern assault rifle with a distinctive curved magazine held across {possessive} body

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

  The exterior/vacuum entries add a slim EVA harness over whatever Outfit was
  rolled, so a corporate blouse in hard vacuum stays coherent.
-->

- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is the dim interior of a mech hangar, gantries and chain hoists receding into shadow.
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a cramped cockpit lit only by instrument readouts.
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a rain-streaked colonial street at night.
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is the cluttered back room of a repair shop, parts racked floor to ceiling.
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a station corridor lined with conduit and hazard striping.
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is an operations room wall of tactical displays.
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is the open bay door of a dropship, a pale sky beyond.
- x3 A half-body character portrait || Behind {object}, softly blurred well out of focus, is a bar interior, out-of-focus figures at the tables behind.
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} diving directly toward the viewer through a dim ship corridor in freefall, {possessive} body stretched into dramatic foreshortening, one arm reaching forward toward the viewer with open fingers and the other bent up near {possessive} head gripping an unseen handhold above the frame, legs trailing behind {object} in motion, faint streaks of motion blur emphasising {possessive} speed, the corridor's lit panels and hazard striping rushing past. Dramatic foreshortened composition.
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} weightless in freefall, {possessive} body rolled off vertical and stretched toward the viewer in strong foreshortening, one gloved hand thrust out at the camera and {possessive} legs trailing loose behind {object}, hair and tether lines floating free, having just pushed off a bulkhead out of frame - behind {object} a darkened docking bay, its running lights streaking past. Dramatic foreshortened composition.
- A close, low-angle character portrait || {Subject} {is_are} floating weightless in a narrow access tube, one arm braced against the wall above {possessive} head and knees drawn up, {possessive} body turned off vertical with nothing underfoot, small debris and loose tools hanging motionless in the air alongside {object}, dim panel lighting receding down the tube behind.
- A dynamic, canted-angle character portrait || {Subject} {is_are} weightless in freefall, body angled diagonally across the frame with one hand reaching out and {possessive} legs drifting loose behind {object}, hair lifted free - around {object} the netted crates of an unlit cargo hold hang untethered in the air, a single work lamp raking across {object} from one side.
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} gliding along the exterior hull of a ship in a low zero-gravity recline, {possessive} back arched and body stretched in a long diagonal across the frame, one arm reaching up and back to grip an angular strut above {possessive} head while the other extends down to brace against a rail beneath {object}, legs drawn up and bent, head tilted back gazing up and to the side, hair swept by the motion, a slim EVA harness pulled on over {possessive} kit - behind {object} the dark hull curves away into the void, faint teal atmospheric light bleeding in from one side and streaks of motion-blurred light trailing past in the starfield. Dramatic rim lighting along {possessive} silhouette.
- A dynamic, canted-angle character portrait || {Subject} {is_are} drifting weightless just outside an open airlock in a slim EVA harness pulled on over {possessive} kit, body turned in a slow diagonal roll with one hand still on the hatch coaming and {possessive} legs floating free, tether line coiling loose behind {object} - beyond {object} the ship's plating falls away into the void and the lit limb of a planet curves across the background. Dramatic rim lighting along {possessive} silhouette.
- A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} braced weightless between two struts of an orbital gantry, {possessive} body stretched at a long diagonal and slowly rotating, one gloved hand overhead on a spar and one boot hooked under a rail, a slim EVA harness pulled on over {possessive} kit - behind {object} the scaffold recedes into the dark and the starfield streaks past in faint motion-blurred lines. Dramatic rim lighting along {possessive} silhouette.
- A close, low-angle character portrait || {Subject} {is_are} floating weightless inside a pressurised observation blister, one palm flat against the curved glass above {possessive} head and {possessive} body turned lazily off vertical, legs drawn up and bent, hair lifted free - beyond the glass the ship's hull curves away and the starfield turns slowly past. Rim lighting along {possessive} silhouette.
- A dynamic character portrait || {Subject} {is_are} caught in a three-quarter turn, raising a compact sidearm and firing directly toward the viewer, muzzle flash bursting from the barrel and a spent shell casing ejecting mid-air - behind {object} a dim industrial interior of dark metal panelling, faintly lit and kept soft and out of focus so {subject} {is_are} clearly the subject. Even key lighting on {possessive} face and weapon, with a dramatic but restrained rim light thrown by the muzzle flash. || nogear
- A dynamic, three-quarter rear-view character portrait || {Subject} {is_are} seen from behind on a rooftop ledge, glancing back over one shoulder and drawing a single-edged blade that glows faintly along its cutting edge, a second blade sheathed crosswise against {possessive} back - behind {object} a dim industrial cityscape stretches away, muted grey-olive towers dotted with sparse lit windows beneath a hazy dusk sky, and the hulking silhouette of something vast and serpentine looms low on the horizon as a dark rust-toned shape. Twin warning beacons glow dull amber at the edges of the frame. || nogear
- x3 A half-body character portrait || Behind {object}, out of focus, is a muted frontier backdrop of dusty rockcrete structures and faint industrial haze, a dim atmospheric glow low on the horizon. Dramatic side lighting casts hard shadow across half {possessive} face.
- A three-quarter character portrait || {Subject} {is_are} leaning intently over a cluttered workbench, hunched forward and studying something closely, both hands down on a mechanical keyboard - to one side a large monitor glows with dense terminal code, casting light across {possessive} face, and behind {object} a cluttered workshop of stacked machinery, tangled cabling and scattered papers recedes into soft focus under dim overhead light. Warm light on {possessive} face against the cooler background. || nogear
- A character portrait || {Subject} {is_are} sitting in profile, leaning back against the bent knee of a massive crouched military mech - the machine is boxy and heavily industrial, thick armored plating stencilled with unit markings, a single lit optic sensor and antenna protrusions rising from its head, its bulk looming just behind {possessive} shoulder. Behind them a rundown industrial refinery at dusk: tangled scaffolding, pipes and a tall numbered tower silhouetted against a low sun. Warm light rakes across {possessive} face and the mech's armor.
- A dramatic low-angle character portrait || {Subject} {is_are} leaning back against the massive bent knee of a towering mech, looking down at the viewer, the shot angled steeply upward to emphasise the scale of both - the mech's leg fills the foreground in fine panel-line and rivet detail, a weapon barrel running off the top of the frame, a crescent moon faint through cloud above and a distant skyline low on the horizon.
- A character portrait seen from behind || {Subject} {is_are} leaning on a rooftop balcony railing high above a dense city street, glancing back over one shoulder at the viewer - below {object} the street is packed with stacked signage glowing through humid haze and light rain, the crowds and wet pavement dissolving into loose, almost impressionistic brushwork. A rooftop awning and railing frame the high vantage point.
- A character portrait || {Subject} {is_are} standing in a bombed-out doorway between two weathered concrete walls, framed by scattered bullet holes, faded warning signs and pinned notices - behind {object} a ruined cityscape stretches away into smoke and dust, a massive mech silhouette looming among the broken buildings and a huge low sun bathing the scene. In the foreground the blurred silhouettes of two seated figures frame the bottom corners, well out of focus.
- A close-up character portrait || {Subject} {is_are} framed tight against a dense city street at night, tangled overhead wires crossing a hazy sky behind {object} and stacked signage glowing softly out of focus, the light grading cool across {possessive} face.

## Stance

- standing in a relaxed, watchful stance, weight settled evenly on both feet
- standing squared and formal, hands clasped behind the back
- standing with arms folded, weight shifted onto one hip
- standing loose and off-balance, one thumb hooked in a belt loop
- standing braced and alert, hands ready at the sides
- standing with hands pushed into jacket pockets, shoulders raised
- standing at parade rest, spine straight
- standing square with both hands on the hips
- standing slightly turned, shoulders angled a few degrees away

## Stance (she) +

- standing with weight on one hip and the other leg relaxed, an easy contrapposto
- standing with one hand resting on the hip, chin slightly lifted
- standing tall with shoulders back and feet close together
- standing with arms loosely crossed, head tilted a fraction to one side

## Prompt templates

These are the sentences the script assembles the rolled traits into. They are
reproduced here so the style is visible in one place alongside the tables, but
they live in `generate-npc.py` — editing them here changes nothing.

### Portrait (1024x1024, straight to the Foundry actor sheet, no background removal)

> **{SHOT}** of **{ROLE}**, **{AGE}**, rendered in a detailed
> painterly illustration style with fine grain texture and clean linework, halftone
> dot shading worked into the shadows, moody cinematic lighting. {SUBJECT} is
> **{BUILD}**, with **{SKIN}**, **{HAIR}**, and **{EYES}**, and **{FEATURE}**,
> wearing **{OUTFIT}**, **{FACTION}**. {POSSESSIVE} face carries **{DEMEANOR}**.
> **{HEADGEAR}** {POSSESSIVE} face carries **{DEMEANOR}**. {SUBJECT} carries
> **{GEAR}**. **{BACKDROP}** A faint **{ACCENT}** glow falls across one side of
> {POSSESSIVE} face, contrasted against warm dim ambient light on the other. Keep
> the palette restrained — greys, olive drab and rust — with **{ACCENT}** as the
> only saturated color in the frame. Shallow depth of field, square framing, high
> detail, atmospheric sci-fi character portrait.

`{HEADGEAR}` is a whole sentence rather than a noun phrase. `{SHOT}` and
`{BACKDROP}` are the two halves of one Backdrop bullet, split on `||` — the
opening phrase and the scene. Rolling them together is what lets a zero-gravity
entry restage the whole shot, swapping "a half-body character portrait" for "a
dynamic, dramatically foreshortened character portrait" and putting the subject
in freefall, without a separate pose table to keep in sync.

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
