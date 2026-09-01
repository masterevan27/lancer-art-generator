---
name: npc-trait-import
description: Extract Backdrop scenes, Stance poses, Gear/weapons, Outfit, Headgear, Hair, Demeanor (facial expression), Faction and Accent-color entries from reference images and stage them as importable candidate entries in a timestamped JSON file, for later selective review/import into npc-generator-tables.md (by the import webpage or by hand) rather than editing that file directly. Use whenever the user shares one or more reference images (pasted inline or given as file paths) from this Lancer campaign's ComfyUI/Krea pipeline and asks to add, extract, stage, or import backdrops, scenes, poses, gear, weapons, outfits, headgear, hairstyles, or expressions "from these" or "in our house style" into the NPC generator.
allowed-tools: Read, Write, Grep, Glob
argument-hint: [image paths, or omit to use images already shown in the conversation]
model: sonnet
---

# Import reference images into the NPC generator tables (staged)

This turns concept-art / screenshot reference images into **candidate** roll-
table bullets for
`AI GM/ComfyUI/Art Prompts/npc-generator-tables.md`, written to a timestamped
JSON file under `AI GM/ComfyUI/Art Prompts/staged-imports/` instead of being
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
of `npc-generator-tables.md` in full. It is the authoritative spec for `xN`
weights, the `||` flag conventions (`hands`, `gun`, `civ`, `mil`, `nogear`,
`weather`, `clear`, `young`, `figure`), and the pronoun placeholders
(`{Subject}`/`{subject}`/`{object}`/`{possessive}`/`{Possessive}`/`{is_are}`/
`{carry}`/`{wear}`/`{gender}`). It can change independently of this skill, so
don't rely on memory of it — read it live.

Also skim `Scripts/generate-npc.md`, specifically **"Where the entries came
from"**, **"Period vocabulary matters"**, and **"Keeping figures adult and
on-model"**. Those sections encode lessons learned the hard way about this
exact task (importing reference art into these tables) and are the source of
the translation rules below.

## 1. Gather the images

Images arrive one of two ways:

- **Pasted inline** in the conversation — look at what's already shown to you.
- **File paths** passed as arguments — `Read` each one.

Look at every image before writing anything. A batch of images can feed
several different tables (one is a backdrop, one is a weapon, one is a
garment) — don't assume they all belong to the same table.

## 2. Classify each image by what it actually adds

| What the image shows | Table | Notes |
| --- | --- | --- |
| A wide scene/environment, with or without the subject doing something in it | **Backdrop** | Portrait only. If the subject is actively posed against the scene (leaning, fighting, kneeling), stage the whole shot as one `{Subject} {is_are} ...` sentence rather than a blurred-background phrase. |
| A body pose with no particular environment, meant for the full-body token | **Stance** | Token only — no scene, no lighting, just the pose. |
| A weapon, tool, or carried item | **Gear** | Tag `hands`/`gun`/`mil` as applicable. |
| A garment, armor, or full kit | **Outfit** (or `Outfit (she) +` if the cut only reads on a woman's figure) | Tag `civ`/`mil`. |
| A helmet, hood, hat, or headset | **Headgear** (or `Headgear (she) +`) | Full sentence: `{Subject} {wear} ...`. |
| A hairstyle/cut visible on its own (not tucked under headgear) | **Hair** (or `Hair (she) +` / `Hair (he) +` if the cut only reads on one gender) | Noun phrase only — no flags, no sentence. If headgear covers all but a fringe or a couple of strands, it's fine to note that (existing bullets do), but the cut itself is still what gets recorded. |
| A distinctive facial expression / mood on the subject | **Demeanor** (or `Demeanor (she) +`) | Noun phrase describing the look, not the backstory behind it — "a wry, crooked grin," not "someone who's seen a lot." |
| An insignia, unit livery, or faction-defining look | **Faction** | Short phrase starting "in ..." or similar. |
| A distinctive glow/neon color with nothing else new | **Accent** | Just the color name — see the palette rule below before adding one. |

Most reference images you'll be handed for this campaign are wide "hero
shot" environments (a mech towering over a street, a ruin, a battlefield) —
those are Backdrop entries nine times out of ten. Hair and Demeanor only come
up when a reference is a close-enough character/portrait shot to actually show
a cut or an expression clearly — don't force one out of a wide environment
shot where the face is small or averted.

## 3. Translate into house style, not just description

This is the part that actually requires judgment — a literal description of
the image will not fit this file. Apply all of these:

- **Strip literal glow/neon colors.** The Accent table supplies the *one*
  saturated color in the frame, and `has_light_source()` in `generate-npc.py`
  only lights the palette when something in the rolled text implies a light
  source at all. Write "a glowing accent" / "optics burning dull red" /
  "sensor clusters glowing" — implying light without hardcoding a color that
  would fight the rolled Accent. (One existing exception worth matching: named
  colors already baked into a few Backdrop bullets, like "dull rust-toned" for
  a kaiju silhouette or "dull amber" beacons — those read as scene color, not
  the accent glow, and are fine to keep if the reference image's color is
  scene-defining rather than a single light source.)
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
- **Stance**: `<participial phrase, third person> || [hands] [gun]`
- **Gear**: `<noun phrase, may use {possessive}> || [hands] [gun] [mil]`
- **Outfit**: `<noun phrase clause> || [civ] [mil]`
- **Headgear**: `{Subject} {wear} <full sentence>.` (no flags)
- **Hair**: `<noun phrase>` (no flags, no placeholders — dropped straight into `{HAIR}` alongside Skin and Eyes)
- **Demeanor**: `<noun phrase>` (no flags, no placeholders — dropped straight into "{POSSESSIVE} face carries **{DEMEANOR}**")
- **Faction**: `<short phrase, usually starting "in ..."> || [civ] [mil]`
- **Accent**: `<color name only>`, e.g. `dull rust-orange`

This is the exact text that will eventually follow `- ` in the table file —
write it as that final form, not a description of it. Only use a placeholder
from the table in §0 — an unlisted one raises a hard error at generation time
rather than failing quietly.

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
  enumeration in `Scripts/generate-npc.md`'s "The roll tables" section), name
  the comment and what the new count would be. Leave it `null` when nothing
  is affected — a stale count is worse than no count, and this note is what
  keeps the later import from introducing one.
- **`notes`** — anything else worth flagging to whoever reviews the
  candidate: an unusual translation call, an ambiguous source detail, why a
  color was stripped or kept, etc.

## 6. Write the staging file

Write one JSON file per skill run to
`AI GM/ComfyUI/Art Prompts/staged-imports/<YYYY-MM-DD-HHMMSS>.json` (create the
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
      "bookkeeping_note": "adds one to the weather-flagged Backdrop count in the ## Weather section comment and in Scripts/generate-npc.md's roll-table enumeration",
      "notes": "nogear because the sentence already puts a weapon in the subject's hands; glow left uncolored so it doesn't fight the rolled Accent"
    }
  ]
}
```

Field notes:

- `id` — short, unique within the file (`e1`, `e2`, ...); stable so a reviewer
  can refer to one entry unambiguously.
- `table` — the *exact* `##` heading this targets, including any variant
  suffix (`"Outfit (she) +"`, `"Hair"`, `"Demeanor (she) +"`) — this is what
  tells the later import step which table to insert into.
- `bullet` — the finished line from §4, exactly as it should appear after
  `- ` in the table file (including any `xN`, `||` segments, and flags).
- `source_image` — which image (by filename, or a short description if the
  image was pasted inline with no filename) this candidate came from.
- `placement_hint` / `bookkeeping_note` / `notes` — from §5. Use `null` for
  `bookkeeping_note` when nothing is affected; the other two are always a
  string.

Group every candidate from this run into one file's `entries` array, even
when they target different tables — the review step filters by table on its
own side.

## 7. Tell the user what you staged

After writing the file, summarize in chat: how many candidates, which tables
they target, and the file path — so the user knows a review step is waiting
without needing to open the JSON to check.

## 8. Confirm a candidate renders, if the user wants a check

`generate-npc.py --dry-run` prints the assembled prompt without queuing a
render, which is the fast way to sanity-check token budget and placeholder
substitution on a candidate bullet before it's ever imported:

```bash
python generate-npc.py --dry-run --count 1 --set-trait Backdrop="<paste the candidate's bullet field>"
```

Only offer this — don't run it unprompted, since it's the user's call whether
they want a test roll right now.

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
file, `AI GM/ComfyUI/Art Prompts/staged-imports/2026-09-01-142300.json`:

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
      "notes": "nogear because a weapon is already in the subject's hands; no color name on the war-machine's glow so it doesn't fight the rolled Accent"
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
