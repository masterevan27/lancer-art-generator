---
name: spaceship-trait-import
description: Use when extracting or importing spaceship traits from reference images into this Lancer campaign's spaceship generator. Stages reviewable hull, equipment, markings, condition, backdrop and lighting candidates; use npc-trait-import for people.
---

# Stage spaceship traits from reference images

Work from the `lancer-art-generator` repository root. Read the supplied images
and translate visible features into candidates for
`prompts/spaceship-generator-tables.md`. Leave the live tables unchanged.
The older `scene-and-spaceship-tables.md` is not the target.

## Read the live contract

Read the table file's introductory rules through `## Placeholders`, then the
comments and existing bullets for every destination table. Read
`generate-spaceship.py`'s `REQUIRED_TABLES`, `THEMED_TABLES`, `ship_fields`,
placement filters and prompt templates; consult `ship_policy.py` for
`SHIP_TYPES`, `sizes_for`, equipment policy and size limits. Some table comments
predate the generator and claim readers have not landed: check executable code
before treating a flag as inert. Do not invent flags or type slugs.

Read the live `Theme` entries, rather than copying the NPC theme list. Theme
tags are read only on Hull, Detail, Weapon, Command bridge and Backdrop. Leave
ordinary industrial features neutral. Flag strongly distinctive styles only
with existing themes; report a possible new theme separately instead of
silently creating a vocabulary shared with NPCs. Check the live zero-or-at-least-
two tagged bullets per theme/table rule, including the effect of selective
imports. Do not manufacture a second observation just to satisfy that rule.

## Inspect and separate the traits

List every input image with its exact filename. Inspect pixels, including files
whose names mention File Explorer; names do not establish their content.
Contact sheets can organize large batches; open ambiguous details at larger
resolution. Account for every image with candidates or a specific skip reason.
For large batches, delegate disjoint filename lists with unique ID prefixes
and the exact JSON contract below; read and validate the returned files.

| Visible content | Destination and grammar |
| --- | --- |
| Form, proportions, plating and paint | `Hull`: lowercase noun phrase without terminal punctuation `|| type-slug size-band [palette] [@theme]` |
| Antennas, radiators, cargo fittings and other secondary structure | `Detail`: lowercase fragment `|| [civ/mil] [@theme]` |
| Guns, emitters, launch machinery, command structure | Separate `Weapon`, `Shield generator`, `Launch catapult`, `Command bridge`: lowercase fragment `|| [min-band] [max-band] [civ/mil] [@theme where supported]` |
| Registry stencils and surface symbols | `Markings`: lowercase fragment `|| [civ/mil]` |
| Surface wear or damage | `Condition`: lowercase fragment, no flags |
| A recognizable campaign affiliation's markings | `Faction`: `name || visual || flags`; do not infer identity from an unknown emblem |
| Space, dock or atmospheric surroundings | `Backdrop`: `shot phrase || scene sentence || scene flags [max-band] [@theme]` |
| Environmental weather | `Weather`: match its live sentence shape and flags; do not transfer an atmosphere into vacuum |
| Accent hue | `Glow colour`: hue alone, no flags or light-emitting object |
| Where light falls | `Glow placement`: lowercase verb predicate of `A {glow} glow ___. || applicable gates` |

Square brackets above indicate optional flags, not literal text. Read each
table comment for its current vocabulary. Only ship placeholders are legal:
`{ship}`, `{Ship}`, `{name}`, `{size}`, `{is_are}`. NPC pronouns are invalid.
Names, new ship types and size bands cannot be established from appearance
alone; report those ideas separately rather than expanding policy tables.

Keep equipment out of Hull, Detail, Markings, Condition and scene descriptions
of the subject ship. Hull owns the silhouette, not a second bridge, gun or
catapult. Engine bells, radiator fins and cargo clamps are structural; a bare
mounting pad can describe where independently rolled hardware goes.

Type decides what equipment is allowed; size decides what fits. A huge cargo
hull still follows cargo policy. Stage an observed turret as Weapon with honest
size/register flags; it need not remain paired with the source hull. Do not
relax policy or hide restricted hardware in another trait to recreate a source.
Hull requires exactly one legal type/size pair from `sizes_for(slug)`.
Do not guess scale from an unreferenced close-up: extract a scale-neutral detail
or explain the ambiguity. Never author new `none` entries from visual absence;
Command bridge is always fitted and has no empty option.

Use positive spacecraft descriptions: unbroken plating, docking recesses,
registry stripes. Avoid negations and water-specific fittings. Translate
published designs into generic visible forms without names or identifying
feature combinations. Extract content, not the reference's rendering style.
Hull owns paint; Faction adds insignia rather than repainting the hull. Glow
colour owns emitted hue. Follow the live character budgets and keep every
bullet on one physical line.

Glow placement names equipment only with `armed`, `shielded` or `deck` as
appropriate. Scene gates must match the current placement reader; `under-way`
is a forbid against docked scenes, not a requirement that Backdrop carries the
same word. Ship gates are different from NPC gates: do not copy `scene`,
`ground`, `hands`, `gun`, `notac` or human occupation flags into ship entries.

## Write the review file and references

Write one timestamped JSON directly under
`prompts/staged-imports-spaceship/<YYYY-MM-DD-HHMMSS>.json`.
This is a **sibling** of `staged-imports/`, never a child: the GUI selects the
destination generator by staging directory, and both generators have tables
called Hull/Weapon/Backdrop or other overlapping names. A top-level `kind`
field cannot repair a file saved in the NPC directory.

```json
{
  "generated_at": "2026-09-08T19:00:00-04:00",
  "source_images": ["freighter.png"],
  "entries": [
    {
      "id": "e1",
      "table": "Hull",
      "bullet": "a charcoal slab hull with staggered container cradles along its flanks || cargo huge",
      "source_image": "freighter.png",
      "placement_hint": "beside the neutral huge cargo hulls",
      "bookkeeping_note": null,
      "notes": "Hull structure only; independently rolled equipment remains governed by cargo policy."
    }
  ],
  "skipped": []
}
```

This is a format example, not an observation to add to a real run. Each skipped
record is `{"source_image":"exact filename","reason":"specific reason"}`.
Copy every distinct image referenced by entries, retaining exact filenames, to
`prompts/staged-imports-spaceship/refs/<JSON-stem>/<source_image>`.
Copy rather than move or link. Report failed copies; other candidates can still
be reviewed. For basename collisions across source folders, assign unique
preview names and preserve an explicit original-path mapping in the JSON.

## Validate and report

Parse the JSON; verify unique IDs, real destination headings, allowed segment
counts, placeholders, flags and themes. Confirm all inputs are accounted for
and every preview exists and has nonzero size. Compare against live bullets
and across workers; identify exact and near overlaps in notes so the reviewer
can avoid double weighting. Do not silently lose a source during deduplication.

Check Hull pairs with `sizes_for`, equipment floors/ceilings with
`filter_by_size` and `filter_by_ship_policy`, and light gates against equipped
and empty equipment cases. Check candidates' prose in the live templates and
their slot budgets. Perform these checks with in-memory or temporary tables;
do not apply candidates to live tables or queue renders as validation.
Read the resulting prose for equipment smuggled into structural descriptions;
flag validation alone cannot catch that.

Report the staged path, candidates by table, covered/skipped image counts and
skip categories, tagged/untagged ratio for the five themed tables, overlaps,
policy ambiguities, and reference-copy count/size/failures. Tell the user to
select **Spaceships** in the GUI's **Trait Imports** view to review the run.
