# generate-npc.py — random NPCs, portrait + token

A companion script, not a mode of [`generate-art.py`](README.md). That script
renders an *authored* corpus: every prompt it runs was written by hand into a
markdown file, and its whole selection model — `--filter`, `--resume`, the
manifest, the output tree — is keyed to that file's headings. A random NPC has
no authored entry to key against, needs two prompts with different sizes and
different post-processing, and wants a different folder layout at the end.
Those are the reasons it's a separate entry point rather than a flag.

What it *does* share is all the ComfyUI plumbing. `generate-npc.py` imports
`generate-art.py` and reuses its server discovery, workflow slot detection, job
builders, RMBG post pass and manifest helpers unchanged, so there is one
implementation of each. (The hyphen in the filename keeps it off the normal
import path, so it's loaded by file location — renaming it would invalidate every
doc and shell history that names it.)

## What one run produces

```
python generate-npc.py
```

Rolls one human NPC — pilots, mechanics, dock hands, corpo liaisons — out of
`prompts/npc-generator-tables.md`, composes a matched portrait and token
prompt in the campaign's house style, and writes a self-contained folder under
the Foundry Lancer token root:

```
<root>/NPCs/Nadia Okonkwo/Nadia Okonkwo Portrait.png   1024×1024, opaque
<root>/NPCs/Nadia Okonkwo/Nadia Okonkwo Token.png      1024×1280, transparent
<root>/NPCs/Nadia Okonkwo/Nadia Okonkwo.md             the rolled dossier
```

Both images come from the same roll, so they depict the same person. The portrait
keeps its blurred backdrop and skips background removal; only the token goes
through RMBG. That is why the two can't share a single `--post` chain.

`<root>` defaults to the live Foundry data tree —
`…\FoundryVTT-Node-13.351\data\Data\Images\LancerFoundryTokens` — which is the
doubled `data\Data` path Foundry actually reads at runtime, not the AppData copy.
If that path doesn't exist the script falls back to the hub's own
`Assets/LancerFoundryTokens/`. `--out` overrides both.

The dossier records the callsign, every rolled trait, the seed, and both prompts
verbatim, so an NPC you like can be re-rolled or hand-edited later.

## The roll tables

`prompts/npc-generator-tables.md` holds the tables — names, callsigns,
pronouns, theme, age, build, skin, hair, hair colour, eyes, distinguishing
feature, demeanor, role, faction, outfit, headgear, weapon, gear, glow
colour, portrait backdrop, portrait weather, token stance.
Every `##` heading is a table and every `-` bullet under it is one option, so
adding options needs no code change.

**That file's own header documents the format** — `xN` weights, the `||` flag
convention, the pronoun placeholders and the per-pronoun variant tables. It is
the reference to read before editing bullets, and it lives in the file being
edited rather than here. What follows is only what the script does with what it
reads.

`Pronouns` bullets are `subject/object/possessive/noun`. The fourth field is the
noun the image prompt uses for the subject — "a fully grown adult **woman** in
her forties" — and it appears in the opening phrase of both prompts, the
highest-signal position. Pronouns alone were not enough: tokens came back
androgynous, since nothing in the prompt named the subject outright. Drop the
fourth field and it is inferred (she → woman, he → man, anything else →
person), so three-field bullets and `--set-trait Pronouns=she/her/her` still
work. Edit it to taste — "androgynous person" pushes the look further than the
neutral "person".

The pronoun roll happens before every other table, because it decides which
per-pronoun variants the rest of the roll draws from. That is why
`--set-trait Pronouns=...` steers build, hair, outfit and stance as well as the
grammar.

`--pronouns she` is the shorthand for exactly that: it looks the subject up in
the `Pronouns` table and pins the whole bullet, fourth field included, so a run
comes back all women — drawing their builds, hair and outfits from the `(she)`
variant tables throughout. `--pronouns he` and `--pronouns they` do the same for
the other two, and a fourth bullet added to the markdown becomes selectable with
no change to the script. It and `--set-trait Pronouns=` set the same thing, so
passing both is an error rather than a silent precedence rule.

`Backdrop` bullets carry the portrait's opening phrase as well as its scene,
because the two have to agree — a dive at the camera cannot be staged inside "a
half-body character portrait". Roughly a third of the bullets are plain
`A half-body character portrait` background-only shots, most carrying `x3` so
they take about half the weighted pool; the rest are scene-specific — a cluster
of zero-gravity interiors and exterior EVA shots, mech-companion and hangar
scenes, rooftops, ruined streets, cockpits, hacker dens and frontier vistas.
Reweight the plain entries to shift the mix.

These proportions drift every time bullets are imported, and the exact counts
that used to sit in this paragraph were stale by more than half before anyone
checked. Count the table rather than trusting a number written about it.

The EVA entries add a slim harness over whatever `Outfit` was rolled, so a
corporate blouse in hard vacuum stays coherent.

`Weather` puts rain, snow, volcanic ash, embers, dust or fog into a portrait —
one short sentence dropped in behind the backdrop. It is gated twice, because
weather is only ever right in some of these shots. A Backdrop bullet has to
carry the `weather` flag to take any at all, which the outdoor and
semi-outdoor entries do — a little over half the weighted pool — and the
hangars, cockpits, corridors and vacuum scenes do not; and the `Weather`
table's own `clear` entries opt back out, weighted so about a quarter of
outdoor portraits come up with nothing drifting in them. Net effect: roughly
two portraits in five have weather in them.

The token never does. It renders on flat white so RMBG can cut it out, and
falling snow would just be more to cut.

There is no `--weather` flag; `Weather` is an ordinary table, so `--set-trait`
reaches it. Both gates still apply to a forced value, which means pinning the
`Backdrop` as well — a forced `Weather` on an unflagged backdrop is dropped
just as silently as a rolled one. Paste a whole bullet from each table:

```bash
python generate-npc.py --pronouns she --set-trait Weather="Driving snow cuts across the frame at an angle, washing the background pale behind it." --set-trait Backdrop="A half-body character portrait || Behind {object}, softly blurred well out of focus, is a colonial street at night, the signage smeared across wet pavement. || weather"
```

Keep the trailing `|| weather` on the pasted Backdrop bullet. That flag is the
thing being tested, and dropping it is exactly the case that produces no weather
without saying so. The `{object}` / `{possessive}` placeholders are filled
against the NPC's pronouns afterwards, so leave them as they are.

`--dry-run` prints the assembled prompt, and the dossier carries a
`Portrait weather` line either way — reading `clear` when the backdrop was
eligible and the weather opted out, and `none - the rolled scene is indoors or
in vacuum` when the backdrop was never eligible. That second line is how you
spot a forced `Weather` that was gated out rather than one that simply came up
clear.

## Theme

Every NPC rolls one **Theme** — the visual world they come from — before any
appearance table, and that theme gates Hair, Hair colour, Feature, Outfit,
Headgear, Weapon and Backdrop. It is what makes a rolled NPC read as one
coherent character instead of a bag of independently-rolled traits.

A rolled theme opens its own `@`-tagged bullets **plus every untagged one**,
and excludes bullets tagged with a different theme. Once bullets are tagged,
the intended mix is roughly 45% of the appearance bullets in the tables file
carrying no tag at all; that neutral pool is the campaign's plain
worn-industrial look and is reachable from every theme, so a neosamurai NPC in
grey coveralls stays entirely possible.

**As shipped, no bullet carries an `@` tag yet.** `filter_by_theme` and
`apply_theme_share` both fall back to the full, untouched pool whenever there
is nothing tagged to filter or balance against, so today Theme rolls and is
recorded on the dossier but does not yet change which Hair, Hair colour,
Feature, Outfit, Headgear, Weapon or Backdrop bullets get drawn — that starts
once a tagging pass adds `@theme` flags to bullets in
`prompts/npc-generator-tables.md`.

Because a thin theme would otherwise drown in that neutral pool once tagging
lands, its own bullets are duplicated until they hold `THEME_SHARE` (0.6) of
the pool. The multiplier is computed per table from the real pool sizes, so it
self-corrects as content is authored.

`THEME_SHARE` is a **target share of the pool as it stands before the civ/mil
and gear-policy filters narrow it** — not a guarantee about the value actually
drawn. `apply_theme_share` runs first and those filters run after it, dropping
tagged and neutral bullets at different rates, so the realized share drifts
from the nominal one by however much a theme's tags correlate with what those
filters keep. **It drifts in both directions**, and downward is the direction
that matters:

```
python -m test.theme_visibility --tables test/fixtures/tables-themed.md
```

On that fixture, against a nominal 0.6, `gundam` — the military-leaning theme
— has its `Weapon` realize 0.710, while `scav`'s `Outfit` realizes **0.328**:
its single tagged Outfit bullet is `civ`, so `filter_by_mil` drops it outright
for a military Role and the theme vanishes for half that theme's NPCs. A theme
authored entirely in one of `civ`/`mil` is therefore invisible to roles on the
other side, no matter what `THEME_SHARE` says. Give a theme bullets on both
sides of that split, or accept that it only reads on half the roster. These
numbers move as the fixture or the fixed-seed sample count changes — rerun the
command above for the current figures rather than trusting these.

The ordering is left as it is on purpose. Running `apply_theme_share` last
instead would let a theme's tagged Weapon bullets re-inflate past the
`unarmed * 5` bias in `WEAPON_POLICY["Officials"]` and arm officials roughly
60% of the time, so it is a real trade rather than an oversight — one for
Phase 2 to settle, now that the measurement exists to settle it with.

**Theme is independent of Role.** A pirate is as likely to look neosamurai as
cyberpunk — that independence is a requirement, not an oversight. Role still
governs whether they are uniformed and what they carry; the two compose, so a
soldier rolled neosamurai gets that theme's *uniformed* bullets.

Pin a whole group to one look with `--set-trait Theme=neosamurai`. The value is
checked against the `Theme` table and an unknown one is an error listing what is
available, the same as `--set-trait Pronouns=`: a typo used to roll all-neutral
in silence, and an empty value was worse still — a theme was rolled and used to
filter every pool, then overwritten with nothing on the dossier.

## Weapon and Gear

An NPC rolls **both**, so a mechanic can carry a tool bag *and* a holstered
sidearm — one combined roll could only ever yield one of the two.

`Weapon` is theme-gated and `Gear` is not. A weapon is the most theme-defining
object a figure carries, and one undifferentiated pool is why every theme's
armament used to land on everyone. What is left of `Gear` after the split is
data-slates, tool bags and thermoses, which no theme owns.

`Weapon` is rolled **first**, and `Gear` yields to it: a weapon that occupies
the hands drops the equipment that also needs one. Roughly a fifth of NPCs
would otherwise hold an impossibility — a parasol in one hand and a katana
raised in both.

The `Weapon` table's heavily weighted empty entry keeps an unarmed NPC the
common case. A `mil` Role never reaches it: `apply_weapon_policy` restricts
that pool to `sidearm`-flagged bullets, so the "always armed" guarantee is
stronger after the split than before it.

`apply_weapon_policy` also tiers the pool by Role, not just by mil/civ. The
`Officials` category almost never carries anything dangerous, and never
anything but a pocketable weapon when it does; `Criminals` usually carry
something. Every other Role — most of them — falls to `civilian`, the
default tier for any Role neither of those two named categories claims: it
stacks extra copies of the unarmed bullets into the pool so an ordinary Role
comes out unarmed more often than not. That default used to be no policy at
all, which is why seven civilian Roles — dockworker, chief mechanic,
freelance salvager and the like — came out armed 65% of the time; `civilian`
brings that down to roughly a third.

`--unarmed` forces the `Weapon` roll empty outright, but not for everyone: a
`mil` Role keeps its guaranteed sidearm and `Criminals` keep whatever
`armed_bias` gave them, since a soldier's sidearm and a pirate's armament are
what make the two read as one rather than an accessory that just didn't
roll. Every other Role, `Officials` included, comes up with nothing in hand.
`Stance`'s `armed` flag — the wider sibling of `gun`, marking a pose that
references a weapon of any kind rather than a firearm specifically — reads
off the same roll, so an NPC `--unarmed` disarms is never posed brandishing
something nothing in the prompt names.

## Faction

`Faction` is a **three-segment** table too — `name || visual || flags` —
the same shape `Backdrop` and `Hair colour` use. The name is what the
dossier prints under "Affiliation" and what the byline names; the visual is
the only part that reaches the image prompt, dropped into the clothing
sentence in place of the name.

The split exists because the single-segment form put a garment *category* —
"corporate wear", "service dress" — right after `Outfit`'s specific garment
description, competing for the same slot and losing every time; deleting the
whole `Faction` clause from a prompt used to change the render not at all.
A visual is written to describe what `Outfit` doesn't: fabric, tailoring,
insignia, patina, and where the faction has one, colour — never a garment
category.

Two entries, the non-affiliations `Unaligned` and `Unregistered`, have
nothing to show and leave the visual empty on purpose; `build_prompts` drops
the clause entirely rather than leave a doubled comma. `Faction` also carries
the `civ`/`mil` split `Outfit` does, filtered by Role the same way, and a
`palette` flag: five factions assert pigment of their own (dye in cloth,
distinct from `Glow colour`'s light), which softens the closing palette
line's claim from "the only saturated color" to "the only *other* saturated
color" so the prompt stops contradicting a uniform it just described.

**`--set-trait Faction=` needs that same shape.** A bare string — the form
every example below used before this table gained a visual segment — parses
as the name with an empty visual, so the faction clause silently disappears
from the prompt instead of erroring. Paste a whole bullet, or write your own
`name || visual` pair:

```bash
python generate-npc.py --set-trait Faction="Harrison Armory || sharply pressed, high collar and polished fittings, in imperial green and gold || mil palette"
```

## Hair colour

Cut and colour roll separately, so a new shade is one bullet rather than a
rewrite of every cut.

`Hair colour` is a **three-segment** table — `base || tail || flags` — like
`Backdrop`. The base fills a `{colour}` slot inside the rolled cut; the
optional tail is appended after the whole phrase. That is what lets gradients
work, since they read wrongly in adjective position and correctly as a
trailing clause:

    "a sleek {colour} bob cut level with the jaw"
      + "silver-white || fading to green at the tips"
      -> "a sleek silver-white bob cut level with the jaw, fading to green at the tips"

A colour flagged `older` — greying, salt-and-pepper — is dropped when the Age
roll came up `young`, mirroring the `figure`/`young` pairing exactly.

## Glow placement

Colour and placement roll separately, for the same reason cut and colour do:
a new placement is one bullet rather than a rewrite of every shade.

The portrait's glow sentence used to be a single fixed phrase baked into the
template — the light fell across one side of the subject's face in every render
the generator had ever produced. That phrasing is still in the table, as one
weighted bullet among ten.

A bullet is written as the **predicate** of `A faint {glow} glow ___.`, so it
begins with a verb and carries its own contrast clause where it wants one. It
must not name the colour: the template has already said it, and saying it twice
is how a frame ends up with two glows — the same failure the `Glow colour`
table's own comment records for naming a light-emitting phenomenon instead of a
hue.

A placement flagged `scene` puts the light out in the environment — on a wall,
in the air, across the ground. The glow has two possible sources, and only one
of them can do that:

| Source | Example | Can light a wall? |
| --- | --- | --- |
| Equipped — worn or carried | a lit visor, glowing cabling, an instrument panel | no |
| The Backdrop itself | a neon sign, a burning wreck, a lit corridor | yes |

So a `scene` placement is dropped unless the rolled Backdrop is what casts the
light. `Glow placement` is rolled immediately **after** `Backdrop` in
`REQUIRED_TABLES` precisely so that the scene is known in time to test it —
the same ordering dependency `Role` has on `Faction` and `Outfit`.

The token prompt gets no placement at all. It renders on flat white with no
scene to place anything against, so it keeps the unplaced wording it always
had.

## Where the entries came from

Many were reverse-engineered from authored prompts already on this machine, read
back out of the PNGs' embedded ComfyUI metadata rather than guessed from the
images: `<comfy>/output/LancerTTRPG_Images/` (the mercenary pilot, blade
specialist and frontier sniper) and `Assets/Unsorted Inspiration/` (the
prosthetics, hacker den, mech-companion staging and ruined-city scenes).

Two edits are applied to everything lifted that way:

- **Glow and neon colors are stripped.** The palette sentence already makes the
  rolled `Glow colour` the only saturated color, so "glowing cable tubing" picks
  it up instead of fighting it with a hardcoded red.
- **Only content is taken, never rendering style.** Those references are
  saturated cel/anime; the campaign is painterly with halftone and a restrained
  palette. Prosthetics, kit and staging carry over; the look does not.

Two things learned the hard way, worth keeping if you add more:

- Describe the **body first** — foreshortening, the reaching arm, the trailing
  legs — and the room second. Entries that led with the environment rendered the
  subject standing on a deck no matter how many "weightless" qualifiers were
  bolted on.
- The opening phrase does real work. While it was hardcoded to "A half-body
  character portrait", no amount of scene wording produced a proper dive.

Newer entries arrive through tooling rather than by hand, applying those same
two edits. The `/npc-trait-import` skill
(`.claude/skills/npc-trait-import/`) reads reference images and writes
*candidate* bullets to `prompts/staged-imports/<timestamp>.json` — it
never edits the tables file itself. The Import GUI (`import-gui-server`, part
of the NHP Uplink repo and started by `StackLauncher.ps1`) then shows those
candidates for review and appends the accepted ones, marking each `imported`
in the staged file so it can't be imported twice.

Two consequences worth knowing when you read a staged file: the importer
appends each bullet as the **last** bullet in its section, so the
`placement_hint` recorded alongside a candidate is advice for a human, not
something the tool acts on; and it refuses a `table` whose `## heading`
doesn't already exist rather than inventing one.

## Name the number

Every `Age` bullet names a decade, and *only* a decade. Two once described a
look instead — "old enough that the war stories are first-hand, face heavily
creased" — and the model, given nothing numeric to hold, ignored them: that
bullet rendered a smooth-faced twenty-something whenever the `Hair` roll
suggested one.

Naming the decade fixed those two, but the look-clauses stayed on every other
bullet as a trailing description — "the first lines already setting around the
eyes", "face lean and weathered", "grey coming in at the temples". They are
gone now, and the same finding is why: a clause describing skin, lines or
weathering is the part the model was already demonstrated to ignore, so it
bought nothing and spent tokens on a prompt that runs close to Krea 2's 512
ceiling. Trimming them dropped the portrait's over-budget share from 0.3% to
0.1% and its p99 from 496 to 487. A bullet is now the decade and nothing else:
"in her mid-twenties", "in her sixties".

The under-twenty bullets are the one exception, and keep their explicit number
— "sixteen or seventeen", "just nineteen" — rather than leaving "late teens"
to carry it alone. That is not decoration: the templates assert `a fully grown
adult` in the highest-signal position in the prompt, and without a number to
argue against it the model believes the assertion over the age. They also carry
the `young` flag; see
[Keeping figures adult and on-model](#keeping-figures-adult-and-on-model).

So: name the decade, name the number under twenty, and describe nothing else.

## Dress register

A rolled dockworker came out in *"a dark robe traced with gold embroidered
trim, a purple sash knotted at the waist and small tassels hanging loose"*,
with the Faction clause adding *"heavy brocade and gold braid, an heraldic
crest at the shoulder"* on top. The figure read as minor nobility; the Role
line two clauses earlier said dockworker.

The `civ`/`mil` split could never have caught that. It distinguishes *not a
uniform* from *a uniform*, and says nothing about whether a garment is workaday
or ceremonial. So `dressy` is a third axis, orthogonal to `civ`/`mil` and to
Theme alike, gated on the kind of work a Role is:

```python
DRESS_POLICY = {
    "Laborers":    "plain",   # dockworker, freelance salvager
    "Technicians": "plain",   # chief mechanic, maintenance technician
}
DEFAULT_DRESS_POLICY = "any"
```

Keyed on the `ROLE_CATEGORIES` bucket rather than on a flag on the Role bullet,
because that mapping already encodes which job an occupation is — the 22 Role
bullets need no edit. Only two categories are `plain`, and the rest are
deliberate: Pilots, Soldiers and Support are entirely `mil` Roles and
`filter_by_mil()` already drops every `civ` bullet from their pool, which is
every ceremonial outfit there is; Officials is the case the gate must *not*
break, since fine dress is right for a corporate liaison; Criminals keeps it
because a pirate in finery is a genre staple; and Civilians holds the
scavenger-priest, for whom robes are the point.

**The two tables consume the flag differently.** A `dressy` Outfit is dropped
from a `plain` Role's pool. A `dressy` Faction is not — it keeps its place and
loses only its *visual* segment, so the dossier still prints the affiliation
while the prompt loses the brocade. A dockworker employed by the Karrakin Trade
Baronies is good flavour; a dockworker dressed as a baron is the bug, and
barring the faction outright would throw the first away to fix the second.

`dressy` is **not** `notac`, and the temptation to merge them is the main way
to get this wrong. `notac` means "do not pair with tactical gear" and covers
rags as readily as finery. The two disagree on seven of the thirteen `notac`
bullets in the base Outfit table — the pilgrim's robes, the tattered robe, the
ragged cloth bindings, the travel-worn robe and the weathered haori are all
`notac` and none are finery; several read as *poorer* than the default
coveralls. Flag finery, not tradition.

Measured over 4000 rolls after the change: of 691 NPCs with a `plain` Role,
none wore a `dressy` outfit and none carried a `dressy` faction's visual, while
ceremonial dress still reached Officials, Criminals and Civilians — the gate
narrows the roles it targets and no others.

Forcing a contradiction follows the `young`/`figure` precedent exactly. A
forced `dressy` Outfit narrows the *Role* roll; a forced `plain` Role narrows
the Outfit roll; forcing both into a contradiction is an error naming the pair
rather than a silent pairing.

### Headgear register

`notac` reaches a third table. It already means "do not pair this with tactical
gear" and already drops `mil` bullets from Weapon and Gear; a `hardtech`
Headgear bullet is now dropped the same way, so an elaborate or traditional
outfit is not crowned with a sealed flight helmet. `Headgear` follows `Outfit`
in `REQUIRED_TABLES`, so the flag is in hand when the pool is assembled — the
same ordering guarantee `Faction` and `Outfit` rely on for `role_mil`.

`hardtech` is **not** `mil`, and the shortcut is tempting because the Weapon
and Gear filter already keys on `mil`. `mil` means "an actual issued uniform"
on `Faction` and `Outfit`, `Headgear` is not in `filter_by_mil()`, and a `mil`
flag sitting on headgear bullets would invite someone to wire it in and quietly
change what a civilian may wear. It is also the wrong word for roughly a third
of the set — a cybernetic ear implant, a mechanical diagnostic rig and a pair
of retro-industrial headphones are none of them military and all three fight a
kimono.

`hardtech` is **not** `dressy` either. `dressy` asks whether a Role may be seen
in finery; this asks whether a garment sits alongside hard kit. The seven
bullets the two disagree on — the pilgrim's robes, the ragged bindings, the
travel-worn robe — are exactly the ones this must also cover: a pilgrim under a
night-vision helmet is the same bug as a liaison in a kimono.

39 of the 64 base Headgear bullets carry it; all 4 in `Headgear (she) +` do
not. A `notac` outfit still draws from 25 bullets, 30 by weight, including the
whole traditional register — both kabuto, both lacquered hats, the bird-skull
hat, the straw and woven hats — which is the point rather than a consolation.
Two boundaries are settled so they are not relitigated per bullet: goggles are
eyewear rather than hardware, and a traditional hat with a mask beneath it is
the hat.

Measured over 4000 rolls after the change: of 355 NPCs with a `notac` Outfit,
none wore `hardtech` headgear, while hard tech still reached 1996 of the 4000
overall and those 355 drew 54 distinct headgear between them — the gate narrows
the outfits it targets and no others, without flattening what is left.

The reverse gate is deliberately absent: a combat uniform can still roll a
horned kabuto. Doing it properly needs a second value on the same axis and a
decision about which Outfits reject it, which is not simply `mil` — the black
formal dress uniform should keep a peaked cap and reject a bird-skull hat, and
both are unflagged today.

## Period vocabulary matters

The military entries originally used mid-20th-century words — *webbing*, *flak
vest*, *greatcoat*, *smock*, *fatigues*, *trousers bloused into boots* — and the
model rendered them faithfully: puttees, brass buckles, WW1-pattern helmets,
wooden-stocked bolt rifles. They now use current/near-future load-bearing
vocabulary instead (*plate carrier*, *MOLLE*, *combat shirt*, *knee-padded*,
*softshell*, *composite plate*, *exo-frame*), which is enough on its own to move
the whole silhouette forward a century. Nothing else in the prompt changed.

If a new entry comes out looking dated, check its nouns before adding qualifiers.

## Keeping figures adult and on-model

The painterly style drifts toward short, soft-faced, large-headed figures that
read as teenagers, so both templates anchor adult height, seven-to-eight-head
proportion and mature facial structure explicitly. That anchor is why an `Age`
bullet reading "in her late teens" used to render a woman in her thirties: the
opening phrase asserted `a fully grown adult` in the highest-signal position in
the prompt, and the model believed the assertion over the age.

Two of those three anchors are now conditional, keyed off a single flag:

| | default | `Age` bullet flagged `young` |
| --- | --- | --- |
| opening phrase | `a fully grown adult {gender}` | `a young {gender}` |
| face clause | `with mature adult facial structure - grown brow, cheekbones and jaw` | `with a young face, the brow and jaw not yet fully grown` |
| token proportions | seven-to-eight heads tall | *unchanged* |

Proportion stays anchored either way, because it is what stops the chibi drift
and a sixteen-year-old is within a head-height of adult anyway. Flag the bullet
and the other two follow; leave it off and nothing changes.

The `young` flag also gates the **Build** roll. Build bullets flagged `figure`
describe an adult woman's — bust, hips, waist, curves — and are dropped from the
pool entirely when the age came up `young`, the same way a `Weapon` or `Gear`
bullet flagged `hands` drops the `Stance` entries that need both hands free.
That filter is the reason
the flag exists on `Age` rather than the wording simply being baked into the
bullet: the two tables roll independently, so nothing else would stop an adult
figure descriptor landing on a teenager. Six unflagged builds remain for a young
NPC to roll from — keep it that way if you add more.

`Age` is resolved before `Build` in `REQUIRED_TABLES` so the flag is known in
time. Don't reorder that list. `--set-trait Age=` is likewise applied before the
Build roll rather than pasted over the result, and it takes the flag inline:

```bash
python generate-npc.py --set-trait Age="in her late teens, sixteen or seventeen || young"
```

Forcing `Build` runs the pairing in the other direction. A build flagged
`figure` describes an adult woman's, so when you force one and leave `Age` to
the roll, it is the **Age pool that yields**: the `young` bullets are dropped
before it is drawn, exactly as `figure` builds are dropped when the age came up
`young`. An explicit choice of build shouldn't abort the run because the dice
handed it a teenager.

```bash
python generate-npc.py --set-trait Build="slender but full-busted, with a clearly defined waist || figure"
```

That rolls an adult age every time, and queues normally.

Forcing *both* into a contradiction is still an error, because two explicit
choices that disagree are a mistake worth reporting rather than silently
resolving in favour of one of them. This combination stops before anything is
queued:

```bash
python generate-npc.py --set-trait Age="in her late teens, sixteen or seventeen || young" --set-trait Build="slender but full-busted, with a clearly defined waist || figure"
```

```
--set-trait Age and --set-trait Build disagree: a bullet flagged 'figure'
describes an adult woman's build and must not be combined with an Age flagged
'young'. Force only one of the two and the other will roll to match, or drop a
flag.
```

Drop whichever flag you didn't mean — a `figure` build with an unflagged adult
`Age` is fine, and so is a `young` age with any of the six unflagged builds.

Note that a pool filter shortens the list a draw is taken from, so a run that
forces `Build` will not reproduce an unforced run's *other* NPCs at the same
seed. That is true of every filter here — Age/Build, Weapon+Gear/Stance,
Role/Weapon — and forcing a trait only makes it reachable sooner.

A forced Build is also unpacked the same way a rolled one is, so a pasted bullet
keeps its `|| figure` suffix out of the image prompt. Before that, the flag went
into the prompt as literal text.

If you add bullets, keep the rest consistent: anything describing an NPC as
short, small, slight or baby-faced fights the templates and brings the drift
back on an NPC who is *not* flagged young.

The templates also state that clothing follows the figure rather than flattening
it, since heavy outerwear otherwise erases a rolled build entirely. A full-length
coat or heavy armor will still mute a silhouette — that's the garment, not the
prompt. Reweight the `Outfit` table if you want that to happen less often.

The prompt templates themselves live in the script, and are reproduced at the
bottom of the tables file so the house style is visible in one place.

## Traits every woman gets

A trait that should reach nearly every NPC of one gender cannot come out of a
table: one bullet in a pool of thirty lands about three percent of the time, and
weighting it high enough to dominate crowds out everything else in the pool.
`GENDER_TRAITS` in the script asserts those outright instead, the same way
`MATURITY` and `FACE` assert age:

```python
GENDER_TRAITS = {"woman": "full lips, feminine posture, "}
```

It is keyed on the fourth field of the `Pronouns` bullet — the noun the prompt
calls the subject — so `he` and `they` NPCs get nothing, and a new pronoun set
opts in by naming its gender as a key. The clause lands in the same slot in both
templates, immediately before the `Skin` roll:

> ...with mature adult facial structure - grown brow, cheekbones and jaw, and
> **full lips, feminine posture,** warm brown skin, greying hair tied back in a
> short tail...

Keep the trailing comma and space if you edit it; both templates read
`{traits}{skin}` with nothing between them.

Unlike the `figure` builds, this clause is not gated on the `Age` flag — it
describes a face and a bearing rather than an adult figure, so every woman the
tables roll gets it, teenagers included. Keep new additions to it on that side
of the line: anything naming bust, hips or waist belongs in a `figure` `Build`
bullet, which a `young` NPC cannot roll.

Everything here is spent from the same 512-token budget. This clause costs about
seven tokens, which moved the portraits that overflow it from two in six thousand
to four; keep any addition short, and re-check with a long `--count` dry run.

## Women render through their own workflow

Everything above is prompt text. This is the other half of the same idea, one
level down: women are rendered through a different ComfyUI workflow entirely, so
the checkpoint and LoRA stack can differ rather than only the words fed into it.

```python
GENDER_WORKFLOWS = {
    "woman": art.WORKFLOW_DIR / "Lancer_Scene_Workflow_for_girls_v1.json",
}
```

Keyed exactly like `GENDER_TRAITS` — on the fourth field of the `Pronouns`
bullet, the noun the prompt calls the subject, not on the subject pronoun — so
the two stay in step, a gender not named falls through to `--workflow`, and a new
pronoun set opts in by adding a key. Only the two text-to-image stages follow it:

| NPC reads as | portrait + token | background removal |
| --- | --- | --- |
| `woman` | `Lancer_Scene_Workflow_for_girls_v1.json` | `Util_RemoveBackground_makeTransparent.json` |
| `man`, `person`, anything else | `Lancer_Scene_Workflow_v1.json` | *same* |

Cutting a background out is the same operation whoever is standing in front of
it, so `--rmbg` stays a single workflow and there is no gendered equivalent of
it. An unpinned run switches per NPC, which means one `--count 10` can queue
against both files.

`--workflow-woman` overrides the default; `--workflow` is the fallback everyone
else uses. Point the two at the same file to collapse a run back onto one
workflow without editing the script:

```bash
python generate-npc.py --count 10 --workflow-woman "workflows/api/Lancer_Scene_Workflow_v1.json"
```

Both workflows are loaded and validated before the first job is queued, but only
the ones the run actually needs. The whole roll happens up front, so the script
knows which genders came up: an all-men run never opens the women's file, and a
missing or UI-format one fails immediately rather than eight NPCs into a batch.
Whichever workflow each NPC used is recorded alongside its seed in
`.generated-npcs.json`.

Swapping in a different file is the same contract `--workflow` has always had —
API format, and the script locates its own nodes by walking `SaveImage` →
`KSampler` → `CLIPTextEncode` / `EmptyLatentImage`, so a re-export with different
node ids still works. `--dry-run` names the workflow per NPC, which is how to
check the routing without queueing anything:

```bash
python generate-npc.py --dry-run --count 2 --seed 43
```

```
  Seren Ibarra  "Perihelion"  (seed 43)
    a mech pilot, Colonial militia
    -> ...\NPCs\Seren Ibarra
    workflow Lancer_Scene_Workflow_for_girls_v1.json
    portrait 1024x1024 ~422 tok: A three-quarter character portrait of a mech pilot, a fully grown...

  Adrian Fontaine  "Overkill"  (seed 44)
    a corporate liaison officer, Karrakin Trade Baronies
    -> ...\NPCs\Adrian Fontaine
    workflow Lancer_Scene_Workflow_v1.json
    portrait 1024x1024 ~452 tok: A character portrait seen from behind of a corporate liaison officer, a fully grown...
```

This output reflects the tables at time of writing. Names, roles, factions and
token counts drift every time a bullet is added or edited — the same drift the
`Backdrop` proportions above are subject to — so re-run the command rather than
trusting the sample printed here.

Sizes are unaffected: 1024×1024 and 1024×1280 are written into whichever
workflow renders them. A file with no `EmptyLatentImage` gives up that control
and prints a warning naming itself, so a two-workflow run says which of the two
is the problem.

## Re-rolling one trait

`--reroll-trait TABLE`, alongside `--regen-manifest`/`--regen-id`, re-rolls a
single trait of an already-generated NPC and reproduces every other one, then
re-renders into the same folder under the same manifest id:

```bash
python generate-npc.py --regen-manifest .generated-npcs.json     --regen-id npc-Nadia-Okonkwo-1234 --reroll-trait Hair
```

Only some traits can be re-rolled alone, and the reason is worth knowing
because it is not a matter of taste. **The manifest is a lossy record of a
roll**: `roll_npc()` strips a bullet's flags before storing it, so an entry
carries `a colonial administrator`, not `a colonial administrator || mil`. A
trait whose filters need another trait's flags therefore cannot be re-rolled
correctly from an entry — re-rolling `Outfit` without knowing whether the Role
was `mil` produces a civilian in a service uniform.

The script already met this once and solved it one flag at a time: `young` is a
manifest key of its own precisely because the Age bullet's flag was gone by the
time it was stored.

| | |
| --- | --- |
| **Re-rollable** | `Callsigns`, `Build`, `Height`, `Skin`, `Hair`, `Eyes`, `Feature`, `Demeanor`, `Headgear`, `Glow colour`, `Glow placement` |
| **Refused** | everything else, each with its own reason — see `UNREROLLABLE_REASONS` |

The filters that *do* rebuild are the ones whose inputs survive storage: the
rolled `Theme` is a stored trait, `young` and `outfit_notac` are stored keys,
and the stored `Backdrop` keeps its scene segment, which is what
`Glow placement`'s `scene` flag is tested against.

`Headgear` is on the re-rollable list *because* of that second key. It is gated
by the Outfit bullet's `notac` flag, and the manifest stores Outfit with its
flags already stripped — the exact condition that refuses `Weapon`, `Gear` and
`Stance`. `outfit_notac` is therefore written beside `young`, for the reason
`young` is written at all. An entry from before that key exists reads back as
`None` rather than `False`, which is not the same claim: it re-rolls headgear
unrestricted, exactly as it did before the register existed, and says so on
stderr; a regen of such an entry declines to write a fabricated `False` over
the gap.

`Hair` is the fiddly one and worth describing. `roll_npc()` substitutes the
colour into the cut and appends the colour's trailing clause to the whole
phrase, storing only the bare base under `Hair colour` — so a new cut is
re-filled from that base, and the tail is recovered from the table *by* that
base. Without the recovery step, re-rolling someone's haircut would silently
drop a gradient they had. `Hair colour` itself is refused for the mirror-image
reason: the stored cut has the colour already substituted in and its
`{colour}` slot is gone, so there is nowhere to put a new one. Re-roll `Hair`
instead, which picks a new cut in the same colour.

The re-roll draws from `--new-seed` (or the entry's seed), so the same re-roll
of the same NPC is repeatable.

## Options

| Flag | Effect |
| --- | --- |
| `--count N` | Roll N NPCs in one run. Default 1. |
| `--seed N` | Base seed. NPC *i* uses `seed+i`, so a whole run is reproducible. Random if omitted. |
| `--name "Ivo Karras"` | Use this name instead of rolling one. Single NPC only. |
| `--pronouns she` | Roll only NPCs with that subject pronoun — `she`, `he` or `they`. Matched against the first field of the `Pronouns` table, so it gates every gendered variant table too. |
| `--set-trait Table=value` | Force one rolled trait, e.g. `--set-trait Role="a field medic"`. Repeatable across tables, but naming the same table twice is an error rather than a silent last-wins. |
| `--unarmed` | Roll every NPC unarmed, except `mil` Roles and `Criminals` — a soldier's sidearm and a pirate's armament are what make the two read as one. See [Weapon and Gear](#weapon-and-gear). |
| `--tables PATH` | A different tables file. |
| `--no-portrait` / `--no-token` | Generate only one of the two. |
| `--keep-raw-token` | Also save the token's opaque pre-RMBG render. |
| `--out PATH` | Token root to write NPC folders into. |
| `--overwrite` | Reuse an existing folder of that name instead of suffixing it `(2)`. |
| `--workflow` / `--rmbg` | Swap the generation or background-removal workflow. Same defaults as [`generate-art.py`](README.md#options). `--workflow` covers every NPC a gender-specific workflow doesn't claim. |
| `--workflow-woman PATH` | Generation workflow for NPCs who read as women. Defaults to `Lancer_Scene_Workflow_for_girls_v1.json`; pass the same path as `--workflow` to put the whole run through one workflow. |
| `--steps` / `--cfg` / `--sampler` / `--scheduler` / `--set` | Same generation overrides as [`generate-art.py`](README.md#options). |
| `--server` / `--timeout` | Same as [`generate-art.py`](README.md#options). |
| `--dry-run` | Roll, print the NPCs and their prompts, queue nothing. |

Sizes are fixed per image — 1024×1024 for the portrait, 1024×1280 for the token —
since the token needs headroom and footroom for a clean background-removal crop
and the portrait wants to drop straight onto a square actor sheet.

Run log: `.generated-npcs.json`, holding every roll's traits, seed and the
workflow it rendered through. It's local state, gitignored alongside
`generate-art.py`'s manifest.

```
python generate-npc.py --dry-run --count 5
python generate-npc.py --count 3
python generate-npc.py --count 5 --pronouns she   # women only
python generate-npc.py --seed 4242            # re-roll a specific NPC
python generate-npc.py --set-trait Faction="IPS-Northstar || riveted and salt-stained heavy canvas, in rust orange || civ palette"

python generate-npc.py --dry-run --count 6 --seed 42   # which workflow each NPC gets
python generate-npc.py --count 4 --pronouns he         # never opens the women's workflow
python generate-npc.py --count 4 --workflow-woman "workflows/api/Lancer_Scene_Workflow_v1.json"
```

## Rolling a group

`--count` plus a few pinned traits is how you get a *set* of NPCs that belong
together rather than five unrelated strangers. Two rules shape every example
below:

- **A pinned trait is pinned for the whole run.** `--set-trait` takes one value,
  not a subset, so `--count 5 --set-trait Role="a field medic"` gives five field
  medics. A group that should vary along an axis needs one run per value — the
  runs are independent and each NPC gets its own folder, so they compose freely.
- **`--set-trait` values are not checked against the table.** Anything you pass
  goes into the prompt verbatim, which is how you get a role or faction the
  tables never listed. The cost is that a typo fails silently rather than
  erroring, so `--dry-run` first.

  Three things *are* checked, because each one used to fail quietly in a way
  that looked like it had worked: naming the same table twice (an error naming
  both values, rather than the last one silently winning), a `figure` Build
  forced onto a `young` Age *when both were forced* (force just one and the
  other's pool narrows to match), and — not an error, just a silent no-op worth
  knowing about — a forced `Weather` whose Backdrop lacks the `weather` flag.

Always `--dry-run` a group before committing to it. Each NPC is three ComfyUI
jobs — portrait, token, RMBG pass — so a five-NPC group is fifteen.

**A Union marine fireteam — five women, same unit.** `Pronouns` must carry all
four fields (`subject/object/possessive/noun`); `she/her` alone leaves
`{possessive}` empty and the prompt reads "in  mid-thirties".

```
python generate-npc.py --count 5 --seed 1000   --set-trait Pronouns="she/her/her/woman"   --set-trait Role="a Union marine soldier"   --set-trait Faction="Union Administrative Department || issued and worn thin, in faded institutional blue-grey || mil palette"
```

**A mercenary crew — one outfit, mixed people, varied jobs.** Roles differ, so
this is three runs sharing a faction. Pronouns are left to roll. `Unaligned`'s
visual segment is deliberately empty — see [Faction](#faction) — so this pins
the dossier's "Affiliation" line without adding a clothing sentence; `Outfit`
alone carries the look.

```
python generate-npc.py --count 2 --seed 1100 --set-trait Faction="Unaligned || || civ" --set-trait Role="a mercenary squad lead"
python generate-npc.py --count 2 --seed 1200 --set-trait Faction="Unaligned || || civ" --set-trait Role="a mercenary sniper"
python generate-npc.py --count 2 --seed 1300 --set-trait Faction="Unaligned || || civ" --set-trait Role="an elite mercenary pilot"
```

**A corpo delegation — SSC, immaculate, all in the same room.** Pinning
`Backdrop` puts the whole group in one location, which is what makes them read as
a delegation rather than six portraits. Backdrop bullets carry both halves of the
shot split on `||`, so paste a whole bullet:

```
python generate-npc.py --count 4 --seed 1400   --set-trait Role="a corporate liaison officer"   --set-trait Faction="Smith-Shimano Corpro || precisely tailored with fine seam piping, in white and pale pastels || civ palette"   --set-trait Backdrop="A half-body character portrait || Behind {object}, softly blurred well out of focus, is a station corridor lined with conduit and hazard striping."
```

**An EVA salvage crew — everyone weightless.** Same trick, pointed at one of the
zero-gravity bullets. Copy the one you want out of the tables file; the EVA
entries add a slim harness over whatever `Outfit` rolls, so the kit stays
coherent in vacuum.

```
python generate-npc.py --count 3 --seed 1500   --set-trait Role="a freelance salvager"   --set-trait Backdrop="A close, low-angle character portrait || {Subject} {is_are} floating weightless in a narrow access tube, one arm braced against the wall above {possessive} head and knees drawn up, {possessive} body turned off vertical with nothing underfoot, small debris and loose tools hanging motionless in the air alongside {object}, dim panel lighting receding down the tube behind."
```

**A station's worth of background faces.** No pins at all — just volume, for
when you want a folder to draw from rather than a specific crew.

```
python generate-npc.py --count 10 --seed 2000
```

**Tokens only, for actors that already have portrait art.**

```
python generate-npc.py --count 6 --seed 2100 --no-portrait
```

**A group that exercises both workflows.** Leaving `Pronouns` to roll is all
it takes — the run switches per NPC. Worth a `--dry-run` first, since the two
workflows need not be the same speed:

```
python generate-npc.py --dry-run --count 8 --seed 2300 --set-trait Faction="Union Administrative Department || issued and worn thin, in faded institutional blue-grey || mil palette"
```

**The same crew twice, to compare the two workflows.** A pinned seed and pinned
pronouns make the roll identical, so the only variable left is which workflow
rendered it. Point `--workflow-woman` at the men's file for the second run and
give it an `--out` of its own, or the second run suffixes every folder `(2)`:

```
python generate-npc.py --count 4 --seed 2200 --pronouns she
python generate-npc.py --count 4 --seed 2200 --pronouns she --out ./compare --workflow-woman "workflows/api/Lancer_Scene_Workflow_v1.json"
```

**Re-rolling one member of a group.** NPC *i* of a run uses `seed+i`, counting
from zero, so the third NPC of the fireteam above is seed 1002. Re-run it alone
with the same pins and you get that exact person back:

```
python generate-npc.py --count 1 --seed 1002   --set-trait Pronouns="she/her/her/woman"   --set-trait Role="a Union marine soldier"   --set-trait Faction="Union Administrative Department || issued and worn thin, in faded institutional blue-grey || mil palette"
```

Give each group a base seed far enough apart that their blocks don't overlap —
1000, 1100, 1200 — and any group can be reproduced or extended later. The seed
is also recorded per NPC in the dossier and in `.generated-npcs.json`.

**One caveat on forced pronouns.** `Given names` is a single mixed pool with no
per-pronoun variant, so a run pinned to `she/her/her/woman` still draws names
like Quintus or Anselm. Everything else — build, hair, outfit, stance — does
follow the pinned pronouns, since the pronoun roll happens before the variant
tables are chosen. Use `--name` for a single NPC you care about, or split
`Given names` into `(she) +` / `(he) +` variants the way `Hair` is split.
