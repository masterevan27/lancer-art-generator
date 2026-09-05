---
name: npc-trait-import
description: Extract Backdrop scenes, Stance poses, Weapon and Gear items, Outfit, Headgear, Hair, Hair colour, Feature, Demeanor (facial expression), Faction, Glow colour and Glow placement entries from reference images and stage them as importable candidate entries in a timestamped JSON file, for later selective review/import into npc-generator-tables.md (by the import webpage or by hand) rather than editing that file directly. Reads the live Theme table so every '@theme' tag it writes names a real theme, and where one run's images evidence a coherent visual world none of the live themes covers, stages a new named Theme entry alongside them. Use whenever the user shares one or more reference images (pasted inline or given as file paths) from this Lancer campaign's ComfyUI/Krea pipeline and asks to add, extract, stage, or import backdrops, scenes, poses, weapons, gear, outfits, headgear, hairstyles, hair colours, scars or prosthetics, expressions, themes or a new visual style, or where a glow or rim light falls "from these" or "in our house style" into the NPC generator.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent
argument-hint: [image paths or a directory, or omit to use images already shown in the conversation]
model: sonnet
---

# Import reference images into the NPC generator tables (staged)

This turns concept-art / screenshot reference images into **candidate** roll-
table bullets for
`prompts/npc-generator-tables.md`, written to a timestamped
JSON file under `prompts/staged-imports/` instead of being
edited into the table file directly. A separate review step (a webpage built
for this purpose) reads that file and lets the user selectively import
individual entries. **This skill never edits `npc-generator-tables.md`
itself** — it only produces reviewable candidates for that later step.

It does **not** invent prose from scratch — it reads what's actually in each
image and translates it into the table file's exact grammar and flag
conventions, exactly as if it were about to insert the bullet directly. The
only thing that changed from a direct-edit workflow is the last step: instead
of inserting the finished bullet, it's recorded as a candidate with enough
context for someone else (or a later pass) to insert it correctly.

## 0. Read the rules fresh, every time

Before writing anything, read `## How the script reads this file` at the top
of `npc-generator-tables.md` in full, **and the HTML comment above whichever
tables you're writing into** — the Weapon, Gear, Outfit, Faction and Hair
colour comments carry flag rules that the top-of-file section only
summarizes, and the `## Theme` comment carries the weighting policy and the
reason there is deliberately no ninth "grounded" theme, which §4.8 needs.

That file is the authoritative spec for `xN` weights, the `||` flag
conventions, and the pronoun placeholders. As of this writing the flags are:

| Flag | Tables | Meaning |
| --- | --- | --- |
| `hands` | Gear, Weapon, Stance | Gear/Weapon: occupies at least one hand/arm. Stance: pose needs both hands free. |
| `gun` | Weapon, Stance | Weapon: an actual firearm *held in hand*. Stance: the narrower case of a firearm being aimed, fired or otherwise handled. |
| `armed` | Stance | A pose that references a weapon of *any* kind — a blade held, a hilt gripped, something raised overhead. Dropped when the Weapon roll came up empty; a non-firearm weapon keeps `armed` reachable and drops only `gun`. A pose may carry both (`\|\| hands gun`). Poses reference the weapon generically ("raising it", "sighting down it") — the Weapon line has already named it. |
| `none` | Weapon | The single empty bullet, which is how an NPC rolls unarmed; it is also read directly by the Stance filter. Listed for completeness — never author one from a reference image. |
| `mil` | Role, Faction, Outfit, Weapon, Gear | An issued uniform or military-issue equipment. **What it does differs by table, and assuming otherwise is the trap.** On Faction and Outfit it is dropped for a civilian Role (and `civ` is dropped for a `mil` one) — that is `filter_by_mil()`, and Weapon and Gear are not in it. A civilian may carry military-issue kit; on those two tables `mil` is instead what a `notac` Outfit drops. |
| `civ` | Faction, Outfit | Plainly civilian dress. Dropped for a `mil` Role. |
| `palette` | Faction | The faction asserts colours of its own (dye in cloth, not light) — softens the closing glow-colour line from "the only saturated color" to "the only *other* saturated color" so pigment and glow can coexist. A faction with no colour scheme of its own must not carry it. |
| `weapon` | Weapon | An actual weapon, as opposed to equipment that merely *is* `mil` (a radio, a pack). |
| `simple` | Weapon | A `weapon` small and pocketable — a knife, one holstered pistol. |
| `sidearm` | Weapon | A bullet that explicitly includes a **holstered or openly worn** pistol. |
| `notac` | Outfit | Elaborate/traditional dress that must never pair with `mil`-flagged Weapon or Gear, nor with `hardtech` Headgear. |
| `hardtech` | Headgear | Modern technology worn on the head — helmets sealed or open, visor and lens rigs, sensor/night-vision hardware, breather masks, comms headsets, anything cabled or jacked, powered or cybernetic pieces, plus industrial eye and ear protection. Dropped when the Outfit roll came up `notac`. **Not** soft goods (cloth, straw, woven, leather, fur — hats, caps, hoods, bandanas, headbands), **not** plain eyewear, and **not** the traditional or ceremonial register: those are what an elaborate outfit *should* reach, and a kabuto over a kimono is the point. Goggles are eyewear, not hardware. A traditional hat with a mask beneath it is the hat. |
| `dressy` | Outfit, Faction | Ceremonial, formal or finely made — gold thread, lacquer, brocade, ornament. The two tables consume it differently: a `dressy` Outfit is dropped for a Role whose work is manual or dirty, while a `dressy` Faction keeps its place and loses only its *visual* segment, so the dossier still prints the affiliation. **Not** the same as `notac`, and merging them is the main way to get this wrong: `notac` covers rags as readily as finery, and the pilgrim's robes, the ragged bindings and the travel-worn robe are all `notac` and none are fine. Flag finery, not tradition. |
| `nogear` | Backdrop | The scene already puts something in the subject's hands. |
| `weather` | Backdrop | Outdoors, so a Weather roll can land in it. |
| `scene` | Glow placement | The light falls out in the *environment* — on a wall, in the air, across the ground. Only reachable when the Backdrop is what casts it, since the alternative source is something the NPC wears or carries and a lit visor cannot light the wall behind them. An unflagged placement keeps the light on or immediately around the figure and is reachable either way; most should stay unflagged, because the equipped case is the common one. |
| `clear` | Weather | Contributes nothing to the prompt. |
| `young` | Age | NPC under twenty; swaps the adult clauses. |
| `figure` | Build | Written in terms of an adult woman's figure; dropped when Age rolled `young`. |
| `older` | Hair colour | An age-linked colour (greying, salt-and-pepper); dropped when the Age roll came up `young`, the same pairing `figure` has with Build. |
| `@<theme>` | Hair, Hair colour, Feature, Outfit, Headgear, Weapon, Backdrop — **and nowhere else** | A *theme tag*, not a behavioural flag: the bullet belongs to that visual world. Untagged is neutral and reachable from every theme. `Gear` is deliberately not on this list — it split away from `Weapon` precisely because it isn't theme-defining. See the trap below before using one. |

Run `python -c "import importlib.util,sys,pathlib;s=importlib.util.spec_from_file_location('g','generate-npc.py');m=importlib.util.module_from_spec(s);sys.modules['g']=m;s.loader.exec_module(m);print(sorted(set(m.parse_tables(pathlib.Path('prompts/npc-generator-tables.md'))['Theme'])))"`
at the **start** of every run, to get the live list of theme names. That list
is what every `@` tag you write is checked against.

Never invent one *in a tag*. A misspelled theme is matched literally, belongs
to no theme, and quietly excludes the bullet from every roll but its own typo.
A visual world the live list genuinely does not cover is a different thing
from a typo, and it has a route: **§4.8**, which stages the theme itself as
its own candidate. That section is the only way a name absent from the live
list may appear anywhere in a staged file, and it has a gate in front of it.

**Treat that table as a mirror that has already gone stale once, not as the
spec.** It previously omitted `weapon`, `simple`, `sidearm` and `notac`
entirely, and a run trusting it emitted wrong flags. Diff it against the file
every run and fix this skill if they disagree.

**Flags the design specifies that do NOT exist yet — do not emit these.**
`docs/superpowers/specs/2026-09-03-themed-npc-generation-design.md` §7 lists
`bulk`, `enclosed`, `sealed`, `vacuum` and `mechown`/`mechwork`/`mechnear`.
**None of that has landed.** Those tables/flags don't exist and no filter
reads them, so emitting one now produces a bullet that is silently ignored —
or, on a table that is never split, one that renders the flag as literal
prompt text. Add them to this skill in the same change that adds them to the
generator, not before. `older`, and the `Gear`→`Gear`+`Weapon` and
`Hair`→`Hair`+`Hair colour` splits §4 of that design called for, have already
landed — they're documented in the flag table above and in §0/§4 below, not
on this not-yet-landed list.

Three flag traps worth stating outright, because each has been gotten wrong:

- **`sidearm` means holstered or worn, never gripped.** The Weapon comment is
  explicit that it only covers a "holstered or openly worn" pistol — a
  bullet gripped or raised in the hands doesn't count, even if it's a single
  pistol. It's the guaranteed-armed baseline for `mil` Roles (`Weapon`'s pool
  is restricted to `sidearm`-flagged bullets for a `mil` Role), so
  mis-tagging it puts an unarmed-looking bullet in that pool.
- **`hands`/`gun` describe the hands, not the hardware.** A shoulder-mounted
  pod or a slung rifle is `mil weapon` with no `hands`/`gun` — those two are
  for what the subject is actually holding.
- **A theme tag is the one flag where over-tagging is the failure mode.**
  Every other flag here is safer applied than omitted. Theme tags invert
  that. The design rests on roughly **45% of appearance bullets staying
  untagged**: that neutral pool is the campaign's plain worn-industrial look
  and is what every theme draws from, so a `@neosamurai` NPC can still turn
  up in grey coveralls. Tag a bullet only when it would look *wrong* in
  another theme's NPC — lacquered plate, a horned kabuto, glowing data
  ports. A tag on a plain jacket doesn't enrich a theme, it shrinks the
  neutral floor for all eight. **When in doubt, leave it neutral**; a
  reviewer can add a tag in one keystroke and will never notice a missing
  one.

  Two further rules, both silent when broken:

  - **The tag is read on seven tables only** — `Hair`, `Hair colour`,
    `Feature`, `Outfit`, `Headgear`, `Weapon`, `Backdrop`. `Weapon` **is**
    themed; `Gear` **is not** — it split away from `Weapon` specifically
    because equipment (data-slates, tool bags, thermoses) isn't what makes a
    figure read as one visual world, armament is. A `@theme` tag on a `Gear`
    bullet doesn't crash anything (`Gear` bullets are split on `||`, so it
    lands in the flag segment) — it's just silently ignored as an
    unrecognized flag, the same as any other typo'd flag, and the bullet
    stays reachable from every theme regardless of the tag. `Glow placement`
    behaves the same way: split on `||`, but not themed, so a tag there is
    swallowed rather than rendered. On `Skin`,
    `Eyes`, `Demeanor`, `Glow colour`, `Height` and the name tables a tag is
    *worse* than silently ignored: those are never split on `||` at all, so
    a bullet reading `- chrome-inlaid irises || @cyberpunk` ships the literal
    text `|| @cyberpunk` to the image model and prints it in the dossier.
  - **A bullet may carry more than one tag** (`|| civ @cyberpunk @gundam`)
    and is then reachable from either — the right move for genuinely
    cross-over hardware, and better than picking one arbitrarily.

The pronoun placeholders are
`{Subject}`/`{subject}`/`{object}`/`{possessive}`/`{Possessive}`/`{is_are}`/
`{carry}`/`{wear}`/`{gender}`. There is no `{Object}`, and no possessive
built on `{object}` — write `{possessive} shoulder`, never `{object}'s
shoulder`.

`Hair colour` has its own placeholder-like slot and its own three-segment
shape: `base || tail || flags` — the same `base || scene || flags` shape
`Backdrop` uses, not the two-segment `text || flags` most other tables use.
The `base` fills a `{colour}` token that every `## Hair` bullet carries
exactly once (`"a sleek {colour} bob cut level with the jaw"`); the optional
`tail` is appended as a trailing clause after the whole rolled cut, which is
what lets a gradient read correctly (`"fading to green at the tips"` reads
wrongly stuffed in front of the noun, correctly hung off the end). A colour
with flags but no tail still writes the middle segment, empty: `greying || ||
older`. Two things to get right if you ever author a `Hair colour` base
through this skill, both silent failures in the render if missed:

- **Start the base with a consonant.** Four `## Hair` bullets place
  `{colour}` immediately after the article "a" — `"a {colour} bob with a
  blunt fringe"` and three siblings. Nothing in the script fixes "a" to
  "an", so a vowel-initial base like `auburn` or `ash-blonde` renders as
  "**a** auburn bob" in both the image prompt and the dossier. The existing
  table dodges this by qualifying the base itself — `dark auburn`, `pale
  ash-blonde` — rather than leaving it bare. Do the same for any new
  vowel-initial shade; this is the one warning about it that lives outside
  the tables file's own `## Hair colour` comment, and the import path is
  exactly how a new colour is likely to arrive.
- **Reserve tails for cuts that suit them.** A tail like `fading to green at
  the tips` reads fine on long hair and oddly on a very short one —
  `"close-cropped {colour} hair, fading to green at the tips"` describes tips
  that a close crop doesn't have. `Hair colour` and `Hair` roll independently
  with no flag pairing them yet (that's Phase 3 work), so nothing stops a
  tail landing on a short cut. It's rare overall — about one roll in a
  hundred — but a male NPC is meaningfully more likely to hit it than a
  female one: the male `Hair` pool is both smaller and skews shorter. Keep
  new tails few, and prefer them for colours that read well on long hair.

**Unrecognized flags fail silently** (matched literally, ignored if unknown),
while an unlisted placeholder raises a hard error. So a typo'd flag reaches a
render and quietly does nothing — which is exactly why §7's validation pass
exists.

Also skim `docs/generate-npc.md`, specifically **"Where the entries came
from"**, **"Period vocabulary matters"**, and **"Keeping figures adult and
on-model"**. Those sections encode lessons learned the hard way about this
exact task (importing reference art into these tables) and are the source of
the translation rules below.

## 1. Gather the images

Images arrive one of two ways:

- **Pasted inline** in the conversation — look at what's already shown to you.
- **File paths** passed as arguments — `Read` each one.

- **A directory path** — list it first and treat *every* image file in it as
  an input. Don't infer content from filenames: screenshot names like
  `2026-09-01 13_42_31-... - File Explorer.png` are usually full-screen
  captures of the artwork itself, not pictures of a file manager.

Look at every image before writing anything. A batch of images can feed
several different tables (one is a backdrop, one is a weapon, one is a
garment) — don't assume they all belong to the same table.

### Large batches (roughly 20+ images)

A hundred-plus images won't fit in one context. Split them across parallel
subagents, but hold these lines, all of which have failed in practice:

- **Give each worker a verbatim output contract** — the exact JSON shape, an
  id prefix unique to its chunk (`c1-e1`, `c2-e1`, …) so ids can't collide,
  and an instruction to return *only* that JSON. Workers have returned a
  status sentence ("the forks are running, I'll merge shortly") instead of
  results, and a worker that echoes coordinator-speak has done no work.
  **Read what came back before merging it**; re-dispatch the ones that didn't
  comply rather than accepting the gap.
- **Require exact filenames.** Workers abbreviate long names to
  `2026-09-01 13_54_27-...batch2 - File Explo.png`, which resolves to
  nothing. Every `source_image` must be a real filename, verified against the
  directory listing in §7.
- **Trust the pixels, not the worker's label.** A worker mislabeled which
  screenshot a scene came from, and the error was only caught by opening both
  images. When a listing and a description disagree, open the image.
- **Each worker must account for every image it was given** — as an entry or
  as a `skipped` record. Silent drops are how an image disappears from a
  139-file run without anyone noticing.
- **Dedupe at merge time, not in the workers.** Workers can't see each
  other's output, so near-duplicates across chunks are yours to catch. Note
  the overlap in `notes` and let the reviewer choose; don't silently drop one.

## 2. Classify each image by what it actually adds

| What the image shows | Table | Notes |
| --- | --- | --- |
| A wide scene/environment, with or without the subject doing something in it | **Backdrop** | Portrait only. If the subject is actively posed against the scene (leaning, fighting, kneeling), stage the whole shot as one `{Subject} {is_are} ...` sentence rather than a blurred-background phrase. |
| A body pose with no particular environment, meant for the full-body token | **Stance** | Token only, and that means **the body and nothing else** — no ground, ledge, wall, furniture, weather or props that aren't in a hand. A pose may crouch, kneel or sit; it must not sit *on* anything. See the trap in §4. Tag `hands` if the pose needs both hands free, `armed` if it references a weapon at all, `gun` if it specifically aims or fires one. An untagged pose is treated as hands-free and weaponless, so a raised blade left untagged will turn up on an unarmed NPC. |
| A weapon — held, slung, holstered or worn | **Weapon** | Tag `hands`/`gun`/`mil`/`weapon`/`simple`/`sidearm` as applicable — see the flag traps in §0. |
| A tool, pack, or other carried item that isn't a weapon | **Gear** | Tag `hands`/`mil` only — `gun`/`weapon`/`simple`/`sidearm` moved to `Weapon` with the split and no longer apply here. |
| A garment, armor, or full kit | **Outfit** (or `Outfit (she) +` if the cut only reads on a woman's figure) | Tag `civ`/`mil`, plus `notac` if it is elaborate or traditional and `dressy` if it is finery. The two are not the same — see the flag table. |
| A helmet, hood, hat, or headset | **Headgear** (or `Headgear (she) +`) | Full sentence: `{Subject} {wear} ...`. Tag `hardtech` if it is a helmet, visor rig, sensor or comms hardware, a breather mask or a cybernetic piece; leave soft hats, hoods, plain eyewear and the traditional register unflagged. |
| A hairstyle/cut visible on its own (not tucked under headgear) | **Hair** (or `Hair (she) +` / `Hair (he) +` if the cut only reads on one gender) | Noun phrase with exactly one `{colour}` placeholder standing in for the shade — no literal color word, no flags. If headgear covers all but a fringe or a couple of strands, it's fine to note that (existing bullets do), but the cut itself is still what gets recorded. A distinctive *shade* seen in the image (not just the cut) is a separate `Hair colour` candidate — see the note on that table's shape in §0. |
| A distinctive facial expression / mood on the subject | **Demeanor** (or `Demeanor (she) +`) | Noun phrase describing the look, not the backstory behind it — "a wry, crooked grin," not "someone who's seen a lot." |
| A scar, tattoo, prosthetic, implant or other mark carried on the body | **Feature** (or `Feature (she) +` / `Feature (he) +`) | Noun phrase, no behavioural flags — but it *is* one of the seven themed tables, so a mark strongly of one look may carry a `@theme` tag. Distinct from `Demeanor`, which is the expression, and from `Headgear`, which is worn and removable: a cybernetic optic wired into the face is a Feature, a visor strapped over the eyes is Headgear. |
| An insignia, unit livery, or faction-defining look | **Faction** | `name || visual || flags` — the name is dossier-only; the visual is the only part that reaches the prompt, and it must describe fabric, tailoring, insignia or patina, **never a garment category** (that loses to `Outfit` every time). Tag `palette` if the faction asserts colours of its own, `dressy` if the livery is ceremonial. See §4 for the full shape. |
| A distinctive glow/neon color with nothing else new | **Glow colour** | Just the color name — see the palette-strip rule below before adding one. |
| A distinctive *placement* of the glow — rim light from behind, colour pooling on the ground, a haze hanging in the air | **Glow placement** | Portrait only. The predicate of "A faint {glow} glow ___", so it starts with a verb and never names the colour. Tag `scene` only if the light lands out in the environment rather than on the figure, and never let an unflagged one claim the whole shot — see §4. |
| A coherent *visual world* that none of the live themes covers, showing up across several images and several tables | **Theme** | The one table here you are normally forbidden to write to, and it is gated: read **§4.8** in full before staging one. A single striking image is never enough, and most apparent new worlds are an existing theme seen from an odd angle. |

Most reference images you'll be handed for this campaign are wide "hero
shot" environments (a mech towering over a street, a ruin, a battlefield) —
those are Backdrop entries nine times out of ten. Hair and Demeanor only come
up when a reference is a close-enough character/portrait shot to actually show
a cut or an expression clearly — don't force one out of a wide environment
shot where the face is small or averted.

## 3. Translate into house style, not just description

This is the part that actually requires judgment — a literal description of
the image will not fit this file. Apply all of these:

- **Strip literal glow/neon colors.** The Glow colour table supplies the *one*
  saturated color in the frame, and `has_light_source()` in `generate-npc.py`
  only lights the palette when something in the rolled text implies a light
  source at all. Write "a glowing detail" / "optics burning dull red" /
  "sensor clusters glowing" — implying light without hardcoding a color that
  would fight the rolled Glow colour. (One existing exception worth matching:
  named colors already baked into a few Backdrop bullets, like "dull
  rust-toned" for a kaiju silhouette or "dull amber" beacons — those read as
  scene color, not the glow, and are fine to keep if the reference image's
  color is scene-defining rather than a single light source.)
- **Take content and staging, never rendering style.** If the reference is
  cel-shaded, photographic, anime, or otherwise off-style, ignore that
  entirely — the shared prompt templates already assert this campaign's
  painterly/halftone/restrained-palette look. Only the *nouns* (what's in the
  scene, what someone is wearing, what they're holding, how they're posed)
  carry over.
- **Body first, environment second**, for any dynamic/action Backdrop or
  Stance — foreshortening, the reaching arm, the braced leg, the kick, *then*
  the room or skyline. Entries that lead with environment render the subject
  standing flat-footed no matter how much action language follows.
- **Near-future tactical vocabulary for military gear/outfits** — plate
  carrier, MOLLE, combat shirt, chest rig, knee-padded, composite plate,
  exo-frame — never mid-20th-century words (webbing, flak vest, greatcoat,
  puttees), which render as WWI-pattern kit even when everything else in the
  prompt is contemporary.
- **Keep it to one shot.** Both the portrait and token prompts run close to
  Krea 2's 512-token ceiling, and a Backdrop's scene sentence lands ahead of
  the palette/framing tail that gets truncated first if the prompt overflows.
  Match the length of neighboring bullets in the same table — don't write a
  paragraph where the existing entries are a sentence.
- **Numbers over vague qualifiers**, if age or scale ever comes up — this file
  learned that "old enough that the war stories are first-hand" gets ignored
  by the model while "in her sixties" lands. Not usually relevant to
  image-derived Backdrop/Gear/Outfit entries, but keep it in mind if an image
  suggests an Age bullet.
- **Nothing that reads short, small, slight, or baby-faced** on an unflagged
  (adult) entry — this file's whole painterly style already drifts young, and
  new bullets that fight the anchor bring that drift back.

## 4. Write the bullet in the exact grammar for its table

- **Backdrop**: `<opening shot phrase> || <scene sentence> || [nogear] [weather]` (may start with `xN `)
  Two shapes exist — pick based on the image:
  - Background-only: `A half-body character portrait || Behind {object}, softly blurred well out of focus, is ...`
  - Subject staged in the scene: `A <descriptor> character portrait || {Subject} {is_are} <doing something>, ... - <environment clause>.`
  Add `weather` if the scene is outdoors/semi-outdoors (a Weather roll can
  then land in it). Add `nogear` only if the sentence already puts a weapon
  in the subject's hands, so the template doesn't also hand them a rolled
  Gear item on top of it.
- **Stance**: `<participial phrase, third person> || [hands] [armed] [gun]`
  `armed` and `gun` are a hierarchy, not alternatives: `armed` is any weapon
  referenced at all, `gun` the narrower case of a firearm being aimed or
  fired, and a pose aiming a rifle two-handed is `hands armed gun`. Leaving a
  weapon-referencing pose untagged is silent — it stays reachable by an NPC
  who rolled no weapon, and the prompt then describes a blade nobody has.

  **The pose may name the body and nothing else.** This table reaches only
  the token, which renders on flat white so the background can be cut to a
  transparent PNG — so no ground, ledge, wall, furniture, machinery, weather
  or props that aren't held in a hand. Crouching, kneeling and sitting are
  all fine; sitting *on* something is not. This is not a style preference:
  generation runs at CFG 1.0 with no negative prompt, so the template's
  trailing "no environment" cannot argue a noun back out of the image, and a
  rolled "raised ledge" put a visible platform and a second person into the
  token. A reference image always has a floor and usually a room — describe
  what the body is doing and drop the rest. `test/test_stance_content.py`
  fails on a bullet that keeps it, but only once the entry is imported, which
  is too late; catch it here. Six bullets staged before this rule was written
  had to be reworded after import.
- **Weapon**: `<noun phrase, may use {possessive}> || [hands] [gun] [mil] [weapon] [simple] [sidearm]`
  A held weapon is `hands gun mil weapon` (+ `simple` if pocketable); a worn
  or slung one drops `hands gun`; only a holstered/worn pistol earns
  `sidearm`. Re-read the §0 traps before tagging.
- **Gear**: `<noun phrase, may use {possessive}> || [hands] [mil]`
  Equipment only — data-slates, tool bags, radios, packs, anything that
  doesn't read as a weapon. No `gun`/`weapon`/`simple`/`sidearm` here; those
  flags live on `Weapon` now.
- **Outfit**: `<noun phrase clause> || [civ] [mil] [notac] [dressy]`
- **Headgear**: `{Subject} {wear} <full sentence>. || [hardtech]`
  Flag it if the piece is a helmet, a visor or lens rig, sensor or
  night-vision hardware, a breather mask, a comms headset, anything cabled or
  jacked, a powered or cybernetic piece, or industrial eye/ear protection.
  Leave it unflagged if it is a soft hat, cap, hood, bandana or headband,
  plain eyewear, or anything in the traditional/ceremonial register.
- **Hair**: `<noun phrase, exactly one {colour}>` (no flags — dropped straight
  into `{hair}` alongside `{skin}` and `{eyes}` in the prompt template, with
  the rolled `Hair colour` filling the `{colour}` slot first; see the shape
  note in §0 before writing one of these)
- **Hair colour**: `<base, consonant-initial> || [tail] || [older]` — the
  `base` fills the cut's `{colour}` slot, the optional `tail` is a trailing
  clause for gradients, and `older` is the only flag. See the consonant and
  tail traps in §0 before adding a shade.
- **Demeanor**: `<noun phrase>` (no flags, no placeholders — dropped straight into "{POSSESSIVE} face carries **{DEMEANOR}**")
- **Feature**: `<noun phrase, may use {object}>` — a mark carried on the body:
  scarring, a tattoo, a prosthetic, an implant, worn-in lines. No behavioural
  flags, but it is one of the seven themed tables, so a `@theme` tag is legal
  here and belongs in a second segment (`<noun phrase> || @cyberpunk`) when
  the mark is strongly of one look. Most should stay neutral, per §0.
- **Faction**: `<name> || <visual, about a dozen words> || [civ] [mil] [palette] [dressy]`
  — the `name` is what the dossier and the Import GUI print ("Smith-Shimano
  Corpro"); the `visual` is the *only* part that reaches the image prompt, and
  must describe fabric, tailoring, insignia or patina — **never a garment
  category** ("corporate wear", "service dress"), which loses every time to
  Outfit's specific garment description sitting right next to it in the same
  sentence. Leave the visual segment empty (`name || || flags`) for a
  non-affiliation with nothing to show. Add `palette` only when the faction
  asserts colours of its own (dye in cloth, not light) — it softens the
  closing glow-colour line so pigment and glow can coexist; a faction with no
  colour scheme of its own must not carry it.
- **Glow colour**: `<hue only, never a light-emitting phenomenon>`, e.g.
  `dull rust-orange` or `vivid cobalt blue` — both templates wrap the value as
  "**{glow}** glow", so a phenomenon word reads wrong ("electric blue" comes
  out as arcing electricity, "neon cyan" pulls neon tubing into frame). Say
  the shade and let the template supply the glow.
- **Glow placement**: `<verb-initial predicate, may use {possessive}/{object}> || [scene]`
  Portrait only — the token renders on flat white and keeps its own unplaced
  wording. Each bullet is the predicate of "A faint {glow} glow ___.", so it
  begins with a verb and carries its own contrast clause where it wants one:
  `rims {possessive} shoulders and hair from behind, the face lit only by what
  spills around it`. **Never name the colour** — the template has already said
  it, and saying it twice is how the frame ends up with two glows. Add `scene`
  only when the light lands out in the environment (a wall, the air, the
  ground); a placement on or immediately around the figure stays unflagged and
  is reachable either way, which is what most should be.

  **An unflagged placement must not describe light at the scale of the whole
  shot.** It is reachable from an equipped source — a lit visor, glowing
  cabling, a thruster vent — and none of those can throw colour across a
  starfield. So an unflagged bullet never says "the frame", "the shot" or
  "the scene": `test_glow_placement.py` rejects those three literally, and the
  reason is what generalises past them, so don't rephrase around the list.
  One bullet read "cuts across the frame at an angle, catching {possessive}
  profile and one hand", fired off a pilot's glowing thruster pack, and the
  model drew exactly that — a hard cobalt stripe running corner to corner
  behind him. It was reworded, not flagged `scene`: a corner-to-corner beam is
  not a placement anyone wants even when a backdrop can motivate it. If a
  reference image shows light genuinely filling the environment, that is a
  `scene` placement; if it rakes across a figure, say what it touches.
- **Theme**: `<one lowercase word>` — a bare name, no segments, no flags, no
  `xN`. Gated: read §4.8 before writing one at all.

This is the exact text that will eventually follow `- ` in the table file —
write it as that final form, not a description of it. Only use a placeholder
from the table in §0 — an unlisted one raises a hard error at generation time
rather than failing quietly.

### 4.8 Proposing a new theme

A theme is the visual world an NPC comes from, rolled once and honoured by
every appearance table — it is what makes a rolled NPC read as one character
rather than a bag of independent traits. Which themes exist is whatever §0's
one-liner prints — read it, never recall it. Staging a new one is allowed, and
it is the one thing in this skill with a hard bar in front of it, because the cost of a wrong one is paid by every future roll: the
Theme roll is a fixed-size pie, and a theme that shouldn't exist takes its
slice from the ones that should.

**The gate.** Stage a `Theme` entry only when this run produces at least
**4 candidates across 2 of the seven themed tables** — `Hair`, `Hair colour`,
`Feature`, `Outfit`, `Headgear`, `Weapon`, `Backdrop` — that all read as one
visual world, and that world is not one of the live themes. Below that bar,
stage the candidates **untagged** and say so in §8: "these three read as a
coherent look with no home, worth watching." A theme is a container, and one
with nothing in it is worse than no theme at all — it dilutes the roll and
delivers an NPC indistinguishable from a neutral one.

**Three filters, in order. Most apparent new worlds do not survive them.**

1. **Is it a visual world, or something the file already models?** A theme is
   silhouette, materials and era-register. It is not a faction (that table
   exists, and carries livery and insignia), not an occupation (`Role`), not a
   colour (`Glow colour`), and not one striking object (that is a `Weapon`,
   `Headgear` or `Feature` bullet doing its job). "Everyone in these images
   wears the same unit patch" is a Faction. "Everything in these images is
   made of the same stuff, cut the same way" is a theme.
2. **Is it actually one of the live themes?** Check that list from §0 against
   the images before deciding it is absent, and be uncharitable to yourself
   here — a shrine-punk look is `neosamurai`, a rusted-salvage look is `scav`,
   a clean corporate-security look is `corporate` or `tactical`. Coining a
   synonym for a theme that already exists is the expected failure of this
   section, and it is worse than doing nothing: it splits one world's content
   across two names, and each half then loses to the neutral floor.
3. **Does it survive the neutral test?** Themes and the untagged floor are in
   tension — roughly 45% of appearance bullets stay untagged on purpose, and
   that pool is the campaign's plain worn-industrial look. If the candidates
   would look fine on an NPC of any theme, they are neutral bullets and there
   is no theme here. A theme's content must look *wrong* in another theme.

**Naming it.** One lowercase word, no spaces and no hyphens, matching the form
of the live entries (`gundam`, `tactical`, `neosamurai`, `cyberpunk`,
`neogothic`, `grimdark`, `corporate`, `scav`). This is not a style preference:
the name is the literal string after every `@`, flags are matched literally
and a space would split the flag segment outright. Prefer an existing genre
term a reader already knows over a coinage — the name has to mean the same
thing to whoever authors the next twenty bullets for it. Keep it short; it
gets typed on every tag.

**No weight.** Write the bullet as the bare name with no `xN`. That table's
comment sets weights proportional to how much content a theme has, and a brand
new theme has the least in the file — it starts rare and the user raises it as
they author. Its `bookkeeping_note` should point at that comment, since the
weights paragraph there is what a reviewer will want to revisit later.

**The dependency, and why it needs shouting about.** Take `kitbash` as the
worked example throughout — a name deliberately not in the live table, since
this is the one section about a theme that does not exist yet. A candidate
tagged `@kitbash` is only correct if the `Theme` entry is imported too. If a
reviewer takes the Outfit bullets and passes on the theme, those bullets carry
a tag matched against nothing: they belong to no theme, they are not untagged
either, and they are excluded from every roll from then on, silently. The
staged format has no way to express "import this one first" — the importer
reads entries independently — so the protocol is convention, and it has to be
loud:

- The `Theme` entry is **`entries[0]`**, with the id **`t1`**. Ids beginning
  `t` are reserved for theme entries and `e` for everything else, so the two
  never collide and a reviewer can find the theme without reading the file.
- Every candidate tagged with it opens its `notes` with this exact line,
  filled in and nothing else changed:

  `DEPENDS ON t1 (new theme @kitbash) — import t1 first, or drop this tag.`

- §8 leads with it, before the counts. A reviewer who reads only the chat
  summary must still learn that this run contains an ordering constraint.

Be honest about the limit when you report it: this is a note a person has to
read, not a check the importer runs. That is the argument for the gate rather
than a reason to relax it — a run that stages one well-evidenced theme is one
note to honour, and a run that stages three is a trap.

## 5. Record placement and bookkeeping context — don't discard it

Since this skill stages candidates rather than inserting them, capture what
whoever imports the entry later (a person, or a future pass) would otherwise
have had to work out fresh:

- **`placement_hint`** — which existing bullets in that table this one
  belongs next to (the mech-companion shots, the ruined-city shots, the
  gunfight poses, etc.), same judgment call as picking an insertion point
  during a direct edit, just written down instead of acted on.
- **`bookkeeping_note`** — if importing this entry would change one of the
  file's own flagged-entry counts (e.g. the `## Weather` section's "about
  twenty-three backdrop bullets are flagged [weather]" comment, or the
  enumeration in `docs/generate-npc.md`'s "The roll tables" section), name
  the comment and what the new count would be. Leave it `null` when nothing
  is affected — a stale count is worse than no count, and this note is what
  keeps the later import from introducing one.
- **`notes`** — anything else worth flagging to whoever reviews the
  candidate: an unusual translation call, an ambiguous source detail, why a
  color was stripped or kept, etc.

## 6. Write the staging file

Write one JSON file per skill run to
`prompts/staged-imports/<YYYY-MM-DD-HHMMSS>.json` (create the
`staged-imports/` directory if it doesn't exist yet), with this shape:

```json
{
  "generated_at": "2026-09-01T14:23:00-05:00",
  "source_images": [
    "colossal-insect-warmachine.png",
    "gold-mech-cathedral.png"
  ],
  "entries": [
    {
      "id": "e1",
      "table": "Backdrop",
      "bullet": "A dramatic low-angle character portrait || {Subject} {is_are} crouched low behind an abandoned vehicle on a rain-slicked city street at night, weapon raised and sighting up at a colossal insectoid war-machine that fills the skyline ahead, its hull studded with glowing sensor clusters and thin segmented limbs trailing into the smoke-hazed street below, twin beams lancing down from its underside through the drifting mist - behind {object} a burning wreck casts long orange light across the wet pavement. || nogear weather",
      "source_image": "colossal-insect-warmachine.png",
      "placement_hint": "next to the other mech-companion / cityscape Backdrop bullets",
      "bookkeeping_note": "adds one to the weather-flagged Backdrop count in the ## Weather section comment and in docs/generate-npc.md's roll-table enumeration",
      "notes": "nogear because the sentence already puts a weapon in the subject's hands; glow left uncolored so it doesn't fight the rolled Glow colour"
    }
  ],
  "skipped": [
    { "source_image": "lighthouse-cottage.png", "reason": "contemporary/mundane, no sci-fi content to translate" }
  ]
}
```

Field notes:

- `id` — short, unique within the file (`e1`, `e2`, ...); stable so a reviewer
  can refer to one entry unambiguously. A `Theme` entry staged under §4.8 is
  `t1` instead and sits first in `entries`, so the entry other entries depend
  on is findable without reading the file.
- `table` — the *exact* `##` heading this targets, including any variant
  suffix (`"Outfit (she) +"`, `"Hair"`, `"Demeanor (she) +"`) — this is what
  tells the later import step which table to insert into.
- `bullet` — the finished line from §4, exactly as it should appear after
  `- ` in the table file (including any `xN`, `||` segments, and flags).
- `source_image` — the **exact** filename this candidate came from, byte for
  byte as it appears on disk (or a short description if the image was pasted
  inline with no filename). Never abbreviate or elide part of a long name:
  the GUI shows this string and the reviewer uses it to find the image.
- `placement_hint` / `bookkeeping_note` / `notes` — from §5. Use `null` for
  `bookkeeping_note` when nothing is affected; the other two are always a
  string.
- `skipped` — every input image that produced no candidate, each with a
  `reason` (off-genre, near-duplicate of an existing bullet, unreadable
  file, nothing new to add). Together with `entries` this must account for
  every image in the run — that's what §7 checks.

Group every candidate from this run into one file's `entries` array, even
when they target different tables — the review step filters by table on its
own side.

**What the importer actually does with this file** (`import-gui-server`'s
`allTraitCandidates()` / `insertBulletIntoTables()`), which shapes what
matters here:

- It reads only `entries` and `generated_at`. Extra top-level keys like
  `source_images` and `skipped` are ignored, and survive the write-back it
  does when marking an entry `imported`.
- It **refuses a `table` whose `## heading` doesn't exist** rather than
  inventing one — so an invented or misspelled table name is a hard failure
  at import, not a silent one.
- It appends the bullet as the **last bullet in that section**, so
  `placement_hint` is advice for the human reviewer, not something the
  importer acts on. Write it for a person.

### 6.1 Copy each referenced image beside the run

`source_image` names the image a candidate came from; this puts the image
itself within reach, so the review page can *show* the reference instead of
only naming it. After writing the JSON, copy every image an `entries` record
names into:

```
prompts/staged-imports/refs/<the JSON's stem>/<source_image>
```

So `2026-09-02-221633.json` gets `refs/2026-09-02-221633/`, holding one file
per distinct `source_image`, each keeping its filename **byte for byte** —
that name is the only key the GUI has to match them up.

Four things this gets wrong if you improvise:

- **Copy, don't move, link, or shortcut.** The source directories are somebody's
  asset library and get reorganised, cleaned out and renamed; a copy is the
  whole reason the preview still works in six months.
- **Only images `entries` actually reference.** A `skipped` image has no
  candidate to preview, so copying it wastes tens of megabytes for nothing.
  A run that reads 81 images and stages 66 of them copies 66.
- **Per-run folders are what make bare filenames safe.** Generic names —
  `images (3).jpg`, `screenshot.png` — repeat across asset folders, and a
  flat shared directory would let one run's copy answer for another's. Two
  runs that read the same image keep a copy each; that is the intended trade.
- **A failed copy is not a failed run.** If an image is gone, locked, or
  unreadable, note it in §8 and carry on. The GUI treats a missing copy as
  "no preview available" and falls back to naming the file, which is exactly
  today's behaviour — so a candidate with no copy is still importable.

`refs/` is local working state and is gitignored, like the staged `*.json`
beside it. Expect real size: reference images run about a megabyte each, so a
large run leaves 50-100MB on disk. Say so in §8 rather than letting the user
discover it.

## 7. Validate the file before reporting it

Most of what can go wrong here fails *silently* — an unknown flag is ignored
at render time, a truncated filename resolves to nothing, a dropped image is
invisible. Don't hand over a staged file you haven't checked. Run these
against the file you just wrote and fix anything they surface:

1. **It parses.** Valid JSON, and `entries` is non-empty.
2. **Every `table` is a real `## heading`** in `npc-generator-tables.md`,
   matched exactly including any variant suffix. The importer refuses
   anything else.
3. **Every flag is in §0's table.** Unknown flags fail quietly forever.
4. **Every `@theme` tag resolves** — to a theme in the live `## Theme` table
   (get the list with the one-liner in §0) **or** to a `Theme` entry staged in
   this same file under §4.8. A tag matching neither is the silent-exclusion
   bug: the bullet belongs to no theme, is not untagged either, and never
   rolls again. And every tag **sits on one of the seven tables that read
   it** — `Hair`, `Hair colour`, `Feature`, `Outfit`, `Headgear`, `Weapon`,
   `Backdrop` (**not** `Gear`), counting variant suffixes (`Outfit (she) +`
   reads tags; `Eyes (she) +` does not). Both failures are silent at render
   time, and the second renders the tag as literal prompt text.
5. **The run did not over-tag.** Count the tagged candidates against the
   untagged ones for the seven themed tables. If most of this run's
   appearance candidates carry a tag, stop and re-read the over-tagging trap
   in §0 — that ratio is backwards, and the fix is to drop tags, not to
   justify them. Report the ratio in §8 either way.
6. **Every `{placeholder}` is in the allowed set**, with no `{Object}` and no
   `{object}'s`.
7. **Every `source_image` exists on disk**, compared against a real directory
   listing — this catches both truncation and invention.
8. **Every input image is accounted for** in `entries` or `skipped`, with no
   image referenced that isn't in the run.
9. **`id`s are unique.**
10. **Every `Hair` candidate's bullet contains exactly one `{colour}`.** Zero
    means the base cut can never take a rolled shade; more than one means the
    same shade gets substituted twice and the second copy is very likely
    wrong once the placeholder logic fills it in.
11. **Every `Hair colour` candidate's flags sit in the third segment**, not
    the second. `Hair colour` is `base || tail || flags` — the same shape as
    `Backdrop`, not the `text || flags` shape most other tables use — so a
    flag like `older` written as `base || older` lands in the *tail* and is
    read as gradient prose, not as a flag. A colour with a flag but no tail
    still needs the empty middle segment: `greying || || older`, never
    `greying || older`.
12. **Every `Faction` candidate's flags sit in the third segment** — the same
    trap one table over. `Faction` is `name || visual || flags`, so `civ`
    written as `name || civ` becomes the *visual signature* and reaches the
    image prompt as the literal word. A faction with flags but nothing to
    show still writes the empty middle segment: `unaligned and freelance || ||
    civ`.
13. **No `Stance` candidate names anything but the body.** Read each one for a
    noun that is scenery, furniture, machinery, ground, weather, or a prop not
    held in a hand — "on a raised ledge", "into open machinery", "in the
    rising heat", "wind and snow" all shipped before this check existed. The
    token has no environment to put them in, and CFG 1.0 with no negative
    prompt means the template cannot argue them back out.

14. **Any staged `Theme` entry clears §4.8's gate.** It carries at least
    4 candidates across 2 of the seven themed tables in this same file, its
    name is one lowercase word, it has no `xN`, its id is `t1`, and it is
    first in `entries`. A theme below the bar is not a smaller version of a
    good one — delete it and untag its candidates, which are then perfectly
    good neutral bullets.
15. **Every candidate tagged with a staged theme carries the `DEPENDS ON`
    line** as the opening of its `notes`, naming the right id and theme. This
    is the only thing standing between a partial import and a set of bullets
    excluded from every roll, and it is a string a person reads — check it
    literally, not approximately.
16. **No unflagged `Glow placement` candidate claims the whole shot.** None
    contains "the frame", "the shot" or "the scene" unless it carries `scene`;
    `test_glow_placement.py` rejects those three literally. Read for the rule
    rather than the three strings — "spans the whole image" passes the grep
    and fails the point. Every placement also starts lowercase, since each one
    is mid-sentence.
17. **Every referenced `source_image` has a copy under `refs/<stem>/`**, with
    a byte-identical name and a non-zero size — the §6.1 copy step, checked
    rather than assumed. Any that are missing go in the §8 report by name;
    they are a degraded preview, not a broken run, so don't fail on them.

A short script is the fast way to do most of these — 13, and the judgement
halves of 14 and 16, are a read rather than a regex; if the run was small
enough to eyeball, eyeball it. Report what you
checked, not just that you checked.

## 8. Tell the user what you staged

**If this run staged a `Theme` entry, say so first, before the counts.** Name
the theme, say what evidence cleared §4.8's gate (which candidates, which
tables), say which of the eight live themes you considered it against and why
it isn't one of them, and state the ordering constraint plainly: import `t1`
first, or reject the tagged candidates along with it, because a tag naming a
theme that isn't in the table excludes its bullet from every roll. That last
part is a convention the importer cannot enforce, so the user hearing it is
the enforcement. If the run found a coherent look that did *not* clear the
gate, say that too, in a sentence — it is the user's call whether to keep
watching for it, and they can only make it if each run reports the near-miss.

After writing the file, summarize in chat: how many candidates, which tables
they target, how many images were skipped and why (in categories, not one
line per image), **the theme-tag ratio from §7.5** (how many of this run's
six-table appearance candidates carry a tag, and which themes), and the file
path — so the user knows a review step is waiting without needing to open the
JSON to check.

State the tag ratio even when it is zero. A run that tagged nothing is a
perfectly good run — the neutral pool is load-bearing — but the user is the
one deciding when a theme has enough content to raise its weight, and they
can only do that if every run says what it contributed.

Say how many reference images you copied under `refs/<stem>/` and roughly
what they weigh, and name any that could not be copied — those candidates
will show a filename with no preview, and the user should hear it from the
report rather than from an empty detail sheet.

Surface anything the reviewer would otherwise discover the hard way:
candidates that overlap each other or an existing bullet, judgment calls you
made on their behalf, and any bookkeeping counts that will need recounting
after they choose what to import.

## 9. Confirm a candidate renders, if the user wants a check

`generate-npc.py --dry-run` prints the assembled prompt without queuing a
render, which is the fast way to sanity-check token budget and placeholder
substitution on a candidate bullet before it's ever imported:

```bash
python generate-npc.py --dry-run --count 1 --set-trait Backdrop="<paste the candidate's bullet field>"
```

`--set-trait` is repeatable, so a candidate can be checked against the rest of
the roll it has to sit beside — pinning `Theme`, `Role` or `Outfit` alongside
it is the way to see whether a flag actually gates the way you expect. Once an
entry *is* imported, `--reroll-trait <Table>` re-rolls that one trait on an
existing NPC, and anything whose filters read a flag from it — see
`docs/generate-npc.md`'s cascade section for what a given table pulls in —
which is how a new bullet gets seen on a character that already exists.

Only offer these — don't run one unprompted, since it's the user's call
whether they want a test roll right now.

## Worked example

Given three concept-art references — a colossal insectoid war-machine looming
over a rain-slicked city street at night with troops taking cover; an ancient
gold-plated mech crouched in a sunlit ruined cathedral with cloaked figures
looking up at it; a soldier in powered armor delivering a close-quarters kick
to a massive segmented war-machine amid a shattered, smoking cityscape — all
three read as staged Backdrop scenes (subject acting *in* the environment,
not just standing in front of it), so each became one `{Subject} {is_are}...`
Backdrop candidate with `weather` (all three are outdoors) and `nogear` on the
two where a weapon is already in the subject's hands. The run produces one
file, `prompts/staged-imports/2026-09-01-142300.json`:

```json
{
  "generated_at": "2026-09-01T14:23:00-05:00",
  "source_images": [
    "insect-warmachine-street.png",
    "gold-mech-cathedral.png",
    "powered-armor-kick.png"
  ],
  "entries": [
    {
      "id": "e1",
      "table": "Backdrop",
      "bullet": "A dramatic low-angle character portrait || {Subject} {is_are} crouched low behind an abandoned vehicle on a rain-slicked city street at night, weapon raised and sighting up at a colossal insectoid war-machine that fills the skyline ahead, its hull studded with glowing sensor clusters and thin segmented limbs trailing into the smoke-hazed street below, twin beams lancing down from its underside through the drifting mist - behind {object} a burning wreck casts long orange light across the wet pavement. || nogear weather",
      "source_image": "insect-warmachine-street.png",
      "placement_hint": "next to the other mech-companion / cityscape Backdrop bullets",
      "bookkeeping_note": "adds one to the weather-flagged Backdrop count",
      "notes": "nogear because a weapon is already in the subject's hands; no color name on the war-machine's glow so it doesn't fight the rolled Glow colour"
    },
    {
      "id": "e2",
      "table": "Backdrop",
      "bullet": "A character portrait || {Subject} {is_are} standing just inside the shattered nave of a ruined cathedral, dust hanging thick in broad shafts of light falling through the broken vaulting overhead, gazing up at an ancient gold-plated war-machine crouched motionless among the rubble ahead - a pair of cloaked, hooded companions stand just ahead of {object}, silhouetted small against its bulk. || weather",
      "source_image": "gold-mech-cathedral.png",
      "placement_hint": "next to the other ruin/cathedral-style Backdrop bullets",
      "bookkeeping_note": "adds one to the weather-flagged Backdrop count",
      "notes": null
    },
    {
      "id": "e3",
      "table": "Backdrop",
      "bullet": "A dynamic, dramatically foreshortened character portrait || {Subject} {is_are} caught mid-kick in heavy powered armor, driving a braced boot into the armored hull of a massive segmented war-machine at close quarters, {possessive} sidearm still gripped and firing point-blank in the other hand, sparks and debris bursting from the impact - behind {object} a shattered cityscape unfurls in smoke and falling rubble, distant explosions blooming against a pale hazy sky. || nogear weather",
      "source_image": "powered-armor-kick.png",
      "placement_hint": "next to the other close-quarters action Backdrop bullets",
      "bookkeeping_note": "adds one to the weather-flagged Backdrop count",
      "notes": "nogear because the sidearm is already in hand and firing"
    }
  ]
}
```

Note what didn't carry over from the source images: no color names for the
machines' lighting (left as "glowing"/lit), no mention of the reference art's
own rendering style, and no restatement of anything the shared templates
already assert (painterly style, halftone shading, restrained palette).

## Common mistakes

All of these have actually happened on a run of this skill.

| Mistake | Fix |
| --- | --- |
| Trusting this skill's flag list instead of the file's | Diff §0 against the file every run; it has drifted before. |
| `sidearm` on a pistol held in hand | `sidearm` is holstered/worn only — see §0. |
| `hands gun` on a slung or shoulder-mounted weapon | Those flags describe the hands, not the hardware. |
| `{object}'s shoulder` | Use `{possessive} shoulder`; there is no `{Object}`. |
| Abbreviating a long filename in `source_image` | Copy it byte for byte; verify it against a directory listing. |
| Assuming a `- File Explorer.png` name is a UI screenshot | Open it — they're usually full-screen captures of the art. |
| Accepting a subagent's status sentence as its results | Read the return; re-dispatch anything that didn't produce JSON. |
| Handing over the file without checking it | Run §7. Unknown flags and bad filenames fail silently. |
| Inventing a table heading that doesn't exist yet | The importer refuses it; use an existing `##` heading. |
| Staging armament as a `Gear` candidate | Anything that reads as a weapon is `Weapon` now — `Gear` is equipment only, and `weapon`/`gun`/`simple`/`sidearm` are silently ignored there. 25 staged entries had to be re-tabled after the split. |
| A `Stance` pose that names the ground, a wall, or the weather | The token has no environment. Describe the body and drop the rest — §4. |
| A `Faction` flag written in the second segment | That segment is the visual signature and reaches the prompt as literal text. `name \|\| \|\| civ`. |
