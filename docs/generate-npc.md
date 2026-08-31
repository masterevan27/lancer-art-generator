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
`../Art Prompts/npc-generator-tables.md`, composes a matched portrait and token
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

`../Art Prompts/npc-generator-tables.md` holds the tables — names, callsigns,
pronouns, age, build, skin, hair, eyes, distinguishing feature, demeanor, role,
faction, outfit, headgear, gear, accent color, portrait backdrop, portrait
weather, token stance.
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

`Backdrop` bullets carry the portrait's opening phrase as well as its scene,
because the two have to agree — a dive at the camera cannot be staged inside "a
half-body character portrait". Nine plain `A half-body character portrait`
entries carry `x3`, which is 27 of the 43 weighted entries, and sixteen are
scene-specific: eight zero-gravity (interior freefall — corridor dive, docking
bay, access tube, cargo hold; exterior EVA — hull recline, airlock drift,
orbital gantry, observation blister), a gunfight, a rooftop blade draw, a hacker
den, two mech-companion shots, a neon rooftop balcony, a bombed-out doorway, and
a frontier vista. Reweight the plain entries to shift the mix.

The EVA entries add a slim harness over whatever `Outfit` was rolled, so a
corporate blouse in hard vacuum stays coherent.

`Weather` puts rain, snow, volcanic ash, embers, dust or fog into a portrait —
one short sentence dropped in behind the backdrop. It is gated twice, because
weather is only ever right in some of these shots. A Backdrop bullet has to
carry the `weather` flag to take any at all, which the nine outdoor entries do
and the hangars, cockpits, corridors and vacuum scenes do not; and the `Weather`
table's own `clear` entries opt back out, weighted so about a third of outdoor
portraits come up with nothing drifting in them. Net effect: roughly a quarter
of portraits have weather in them.

The token never does. It renders on flat white so RMBG can cut it out, and
falling snow would just be more to cut.

## Where the entries came from

Many were reverse-engineered from authored prompts already on this machine, read
back out of the PNGs' embedded ComfyUI metadata rather than guessed from the
images: `<comfy>/output/LancerTTRPG_Images/` (the mercenary pilot, blade
specialist and frontier sniper) and `Assets/Unsorted Inspiration/` (the
prosthetics, hacker den, mech-companion staging and ruined-city scenes).

Two edits are applied to everything lifted that way:

- **Glow and neon colors are stripped.** The palette sentence already makes the
  rolled `Accent` the only saturated color, so "glowing cable tubing" picks it
  up instead of fighting it with a hardcoded red.
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

## Name the number

Every `Age` bullet names a decade. Two once described only a *look* — "old
enough that the war stories are first-hand, face heavily creased" — and the
model, given nothing numeric to hold, ignored them: that bullet rendered a
smooth-faced twenty-something whenever the `Hair` roll suggested one. Both now
say a decade ("in her sixties", "in her forties but weathered well past it") and
land. Keep new bullets numeric.

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
proportion and mature facial structure explicitly, and the Age and Build tables
avoid youth and small-stature wording. If you add bullets, keep them consistent:
anything describing an NPC as short, small, slight or baby-faced fights the
templates and brings the drift back.

The templates also state that clothing follows the figure rather than flattening
it, since heavy outerwear otherwise erases a rolled build entirely. A full-length
coat or heavy armor will still mute a silhouette — that's the garment, not the
prompt. Reweight the `Outfit` table if you want that to happen less often.

The prompt templates themselves live in the script, and are reproduced at the
bottom of the tables file so the house style is visible in one place.

## Options

| Flag | Effect |
| --- | --- |
| `--count N` | Roll N NPCs in one run. Default 1. |
| `--seed N` | Base seed. NPC *i* uses `seed+i`, so a whole run is reproducible. Random if omitted. |
| `--name "Ivo Karras"` | Use this name instead of rolling one. Single NPC only. |
| `--set-trait Table=value` | Force one rolled trait, e.g. `--set-trait Role="a field medic"`. Repeatable. |
| `--tables PATH` | A different tables file. |
| `--no-portrait` / `--no-token` | Generate only one of the two. |
| `--keep-raw-token` | Also save the token's opaque pre-RMBG render. |
| `--out PATH` | Token root to write NPC folders into. |
| `--overwrite` | Reuse an existing folder of that name instead of suffixing it `(2)`. |
| `--workflow` / `--rmbg` | Swap either workflow. Same defaults as [`generate-art.py`](README.md#options). |
| `--steps` / `--cfg` / `--sampler` / `--scheduler` / `--set` | Same generation overrides as [`generate-art.py`](README.md#options). |
| `--server` / `--timeout` | Same as [`generate-art.py`](README.md#options). |
| `--dry-run` | Roll, print the NPCs and their prompts, queue nothing. |

Sizes are fixed per image — 1024×1024 for the portrait, 1024×1280 for the token —
since the token needs headroom and footroom for a clean background-removal crop
and the portrait wants to drop straight onto a square actor sheet.

Run log: `.generated-npcs.json`, holding every roll's traits and seed. It's local
state, gitignored alongside `generate-art.py`'s manifest.

```
python generate-npc.py --dry-run --count 5
python generate-npc.py --count 3
python generate-npc.py --seed 4242            # re-roll a specific NPC
python generate-npc.py --set-trait Faction="in Harrison Armory service dress, imperial and immaculate"
```

## Rolling a group

`--count` plus a few pinned traits is how you get a *set* of NPCs that belong
together rather than five unrelated strangers. Two rules shape every example
below:

- **A pinned trait is pinned for the whole run.** `--set-trait` takes one value,
  not a subset, so `--count 5 --set-trait Role="a field medic"` gives five field
  medics. A group that should vary along an axis needs one run per value EM the
  runs are independent and each NPC gets its own folder, so they compose freely.
- **`--set-trait` values are not checked against the table.** Anything you pass
  goes into the prompt verbatim, which is how you get a role or faction the
  tables never listed. The cost is that a typo fails silently rather than
  erroring, so `--dry-run` first.

Always `--dry-run` a group before committing to it. Each NPC is three ComfyUI
jobs — portrait, token, RMBG pass — so a five-NPC group is fifteen.

**A Union marine fireteam EM five women, same unit.** `Pronouns` must carry all
four fields (`subject/object/possessive/noun`); `she/her` alone leaves
`{possessive}` empty and the prompt reads "in  mid-thirties".

```
python generate-npc.py --count 5 --seed 1000   --set-trait Pronouns="she/her/her/woman"   --set-trait Role="a Union marine soldier"   --set-trait Faction="in worn Union Administrative Department kit"
```

**A mercenary crew EM one outfit, mixed people, varied jobs.** Roles differ, so
this is three runs sharing a faction. Pronouns are left to roll.

```
python generate-npc.py --count 2 --seed 1100 --set-trait Faction="unaligned and freelance" --set-trait Role="a mercenary squad lead"
python generate-npc.py --count 2 --seed 1200 --set-trait Faction="unaligned and freelance" --set-trait Role="a mercenary sniper"
python generate-npc.py --count 2 --seed 1300 --set-trait Faction="unaligned and freelance" --set-trait Role="an elite mercenary pilot"
```

**A corpo delegation EM SSC, immaculate, all in the same room.** Pinning
`Backdrop` puts the whole group in one location, which is what makes them read as
a delegation rather than six portraits. Backdrop bullets carry both halves of the
shot split on `||`, so paste a whole bullet:

```
python generate-npc.py --count 4 --seed 1400   --set-trait Role="a corporate liaison officer"   --set-trait Faction="in Smith-Shimano Corpro corporate wear, sleek and expensive"   --set-trait Backdrop="A half-body character portrait || Behind {object}, softly blurred well out of focus, is a station corridor lined with conduit and hazard striping."
```

**An EVA salvage crew EM everyone weightless.** Same trick, pointed at one of the
zero-gravity bullets. Copy the one you want out of the tables file; the EVA
entries add a slim harness over whatever `Outfit` rolls, so the kit stays
coherent in vacuum.

```
python generate-npc.py --count 3 --seed 1500   --set-trait Role="a freelance salvager"   --set-trait Backdrop="A close, low-angle character portrait || {Subject} {is_are} floating weightless in a narrow access tube, one arm braced against the wall above {possessive} head and knees drawn up, {possessive} body turned off vertical with nothing underfoot, small debris and loose tools hanging motionless in the air alongside {object}, dim panel lighting receding down the tube behind."
```

**A station's worth of background faces.** No pins at all EM just volume, for
when you want a folder to draw from rather than a specific crew.

```
python generate-npc.py --count 10 --seed 2000
```

**Tokens only, for actors that already have portrait art.**

```
python generate-npc.py --count 6 --seed 2100 --no-portrait
```

**Re-rolling one member of a group.** NPC *i* of a run uses `seed+i`, counting
from zero, so the third NPC of the fireteam above is seed 1002. Re-run it alone
with the same pins and you get that exact person back:

```
python generate-npc.py --count 1 --seed 1002   --set-trait Pronouns="she/her/her/woman"   --set-trait Role="a Union marine soldier"   --set-trait Faction="in worn Union Administrative Department kit"
```

Give each group a base seed far enough apart that their blocks don't overlap EM
1000, 1100, 1200 EM and any group can be reproduced or extended later. The seed
is also recorded per NPC in the dossier and in `.generated-npcs.json`.

**One caveat on forced pronouns.** `Given names` is a single mixed pool with no
per-pronoun variant, so a run pinned to `she/her/her/woman` still draws names
like Quintus or Anselm. Everything else EM build, hair, outfit, stance EM does
follow the pinned pronouns, since the pronoun roll happens before the variant
tables are chosen. Use `--name` for a single NPC you care about, or split
`Given names` into `(she) +` / `(he) +` variants the way `Hair` is split.
