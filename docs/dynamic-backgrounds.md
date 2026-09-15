# Dynamic backgrounds and battlemaps

`generate-background.py` generates editable scene plans without contacting
ComfyUI, renders those exact plans, and creates separate reference-based
battlemaps. It uses Python's standard library and the existing Krea scene and
Qwen image-edit workflows. It does not modify the source image or NPC tables.

## Preview and render

In PowerShell:

```powershell
python generate-background.py --catalogue
'{"environment":"outdoor","seed":42,"count":3,"view":"perspective"}' | python generate-background.py --preview --request-stdin > scenes.json
Get-Content scenes.json -Raw | python generate-background.py --render --request-stdin --output-dir output/backgrounds
```

Use `--tables PATH` with catalogue, preview and render to select an edited
catalogue. `--server host:port` selects ComfyUI; otherwise the existing client
probes localhost ports 8000–8015. `--timeout` defaults to 1800 seconds per image.
The still graph uses `workflows/api/Lancer_Scene_Workflow_v1.json` and its current
model, LoRA and sampling settings, with the requested prompt, seed and canvas.

Preview stdin is a JSON object with these optional fields:

| Field | Meaning |
| --- | --- |
| `environment` | `outdoor` (default), `indoor`, or `space`; space is exposed vacuum |
| `seed` | Integer 0–4294967295; omitted or null chooses a random seed and saves it |
| `count` | 1–8; default 1 |
| `traits` | Table-name to exact raw bullet text mapping |
| `locked` | Array of supplied trait names to preserve through rerolls and batches |
| `reroll` | Boolean; default false |
| `view` | `perspective` (default) or `topdown` |
| `populatePeople` | Boolean, default true; adds distinct people with customizable roles, clothing and activities in perspective scenes |
| `populationDensity` | `sparse`, `natural` (default), or `lively`; scales the number of people to the location |
| `vegetation` | `none`, `balanced` (default), or `lush`; applies outdoors and indoors |
| `interiorLife` | Boolean, default true; adds an indoor pet or aquarium vignette in perspective scenes |
| `notes` | Additional scene/layout direction, at most 4000 characters |
| `width`, `height` | Multiples of 8 from 64–8192; defaults 1920×1080 |

The first plan preserves every supplied trait unless `reroll` is true. Later
plans retain only locked traits. Set an optional trait to `""` to explicitly
omit it; lock that blank to omit it across a batch. The applicable location
cannot be blank. Unknown fields, unknown/disabled trait text, inapplicable
traits, missing lock values, and incompatible pinned combinations are rejected.
Omit inapplicable pools entirely when switching environments.

Weather constrains Motion, and Time constrains Lighting. Pinning a dependent
choice also constrains its parent roll. Blank parent traits allow only choices
without that dependency. The still prompt includes the elements needed for its
motion prompt. Indoor and vacuum scenes exclude outdoor weather. Direct top-down
prompts omit Sky, Distant features and Motion descriptions, adapt Layout into
floor-plan directions, and specify a gridless orthographic camera.
Every scene fills the frame; no area is reserved for a chat overlay.

Scene life adds outdoor trees, wild plants, shrubs, flowers and cultivated bonsai,
or indoor potted plants, orchids and small bonsai. The **Vegetation** pool chooses
the planting; the amount setting controls its abundance. **Interior life** picks
one small pet (cat, dog or fox) or fish tank. The people pools select population,
clothing, adult age mix, appearance variety and activities. These pools support the same pickers, omissions, locks and
rerolls as other traits. Disabling a feature suppresses its prompt instructions
while retaining its chosen trait for later reuse. Space excludes planting and
interior life; its people wear sealed pressure suits. Top-down views omit people,
all people traits and Interior life, retain planting as terrain, and have no motion prompt.
Location, condition, atmosphere and time take priority over life suggestions:
abandoned scenes use sparse visitors, and pets/aquariums are omitted where no
safe maintained habitat fits. These are prompt directions, interpreted by the
image model, so incompatible custom choices may still need adjustment.

People stay secondary to the setting. **Population** selects civilians, military
personnel or mixed groups; **Clothing and equipment** sets their dress and carried
kit; **Adult age mix** ranges from young adult groups to older or intergenerational
groups; **Appearance variety** guides individual faces, hair, skin tones, builds,
presentation and personal details. **Activity** includes work, downtime, patrols,
briefings and inspections. Population, clothing and activity choices must share
a category when tagged. Pinning any of these constrains the other rolls; conflicting
pins are rejected. Untagged activities adapt to the selected people and setting.
Uniforms can match while their wearers differ. Density and age distribution are image-model
directions, not exact counts or guarantees. Animation directions preserve the cast
with small gestures and keep any existing animals in place.

Backgrounds use the NPC illustration prompts' painterly brushwork, fine grain,
clean linework and dense halftone shadows, with wide environmental composition.

Preview returns `{"plans":[...]}`. Each plan has exactly `version:1`,
`environment`, `seed`, `traits`, `prompt`, `motionPrompt`, `view`, `notes`, `width`
and `height`, plus `populatePeople`, `populationDensity`, `vegetation` and
`interiorLife`. The four scene-life fields are optional when rendering older
version 1 plans, so existing saved prompts remain renderable unchanged.
The render command consumes this object, validates it, and renders
the exact `prompt` supplied. The user may edit the prompt before rendering;
render does not silently rebuild it from traits. Explicit prompt edits can
override the generated composition, so review them before rendering.

With a fixed seed, supplied traits, and unchanged tables, rolls are reproducible.
Batch seeds increment, wrapping at 2³². Duplicate trait combinations are
resampled up to 64 times; fully locked or exhausted pools can necessarily repeat.
Model/GPU execution itself is subject to the normal ComfyUI reproducibility limits.

## Tables

`prompts/background-generator-tables.md` contains 25 pools with at least 20
distinct substantive entries each: three context-specific location pools,
Architecture, Palette, Lighting, Layout, Weather, Details, Motion, Foreground,
Distant features, Terrain or floor, Sky, Time, Faction presence, Condition and
Atmosphere, Vegetation, Interior life, Activity, Population, Clothing and equipment,
Adult age mix and Appearance variety. Context subsets of a shared
pool may contain fewer than 20 entries.

Expanded locations, layouts, weather, lighting and details draw on NPC Backdrop
scenes and the general scene tables. Military choices include command bunkers,
mech service bays, carrier decks, field hospitals, checkpoints and defensive sites.

Each `## Heading` starts a pool. `- ` bullets are enabled entries; HTML comments
disable entries. Prefix a bullet with `xN` for an integer weight from 1–10000.
Flags precede prose: `[outdoor]`, `[indoor]`, `[space]`, or a comma-separated
combination. Unflagged entries apply to every environment. Weather and Motion
use matching `[weather=rain]`, `[weather=snow]`, etc. Time and Lighting use
`[time=day]`, `[time=twilight]`, or `[time=night]`. Population, Clothing and equipment,
and Activity accept `[population=civilian]`, `[population=military]`,
`[population=mixed]` or a comma-separated combination. These flag dependencies belong
to those named pools; custom headings are otherwise ordinary independent pools.
No groups or duplicated weight-expanded entries are used.

Catalogue output is `{"environments":["outdoor","indoor","space"],"tables":[...]}`.
Each table has `name`, `environments`, and `values`. Every value has `text`
(the entire raw bullet, including weight and flags), `environments` (an array),
and numeric `weight`. Prompts strip flags and weights; metadata preserves them.
Changing a selected bullet, its flags or its weight requires reselecting that
trait before another render. Previously saved images and sidecars remain intact.

## Separate battlemaps

```powershell
python generate-background.py --battlemap "output/backgrounds/scene.png" --width 1536 --height 1024 --seed 42 --notes "Keep both loading entrances accessible."
```

The source is uploaded once to ComfyUI and passed to `TextEncodeQwenImageEditPlus`
as an image reference. The workflow reuses the Qwen Edit 2509 model, Lightning
LoRA, CLIP and VAE settings from the existing expression-edit workflow; it
removes RMBG and writes an opaque PNG. A separate output canvas sets dimensions.
The prompt asks for a flat 2D overhead tabletop RPG map, with the camera exactly
90 degrees to the floor, connected rooms or terrain areas, and clear walkable
routes. It shows floor surfaces, furniture tops and walls as solid dark
cross-section outlines, removes roofs and ceilings, and excludes perspective,
isometric views, grids and text. People, pets, creatures and their shadows are
removed; planting is viewed from above with readable routes. The image reference supplies the scene's
colors, materials and illustration style.

A source sidecar supplies provenance when available: the original traits and
environment remain in the map metadata. Neither the original prompt nor a trait
dump is appended to the map instruction; the image reference carries identity.
This concise wording avoids the competing camera and composition directions
that preserved an angled view during initial live validation. Only the user's
map notes are appended. A bespoke source without metadata is interpreted directly from the
image and gets `environment:null` in the map metadata, rather than inventing a
context. Hidden geometry must be inferred by the image model. Visual fidelity,
orthographic compliance and tactical navigability require visual review of the
generated output; graph tests cannot establish those qualities.

Outputs default beside the source as `<source stem> Battlemap-<unique>.png`;
`--output-dir` overrides the directory. This command never overwrites the source.
Direct top-down generation instead uses a fresh scene plan and the Krea still
workflow, without a reference image.

## Saved files and integration

Each completed output has a neighbouring `<image stem>.background.json` written
atomically. Normal metadata contains the plan fields plus `kind:"background"`.
Map metadata contains the same fields with `kind:"battlemap"`, `view:"topdown"`,
an empty `motionPrompt`, and `source:{"path":"absolute source path","mtime":...}`.
`mtime` is the source image modification timestamp in milliseconds, matching
JavaScript's `mtimeMs`. Source identity traits are retained unchanged.

Image names use unique suffixes and exclusive creation. The CLI emits exactly
one stdout line per completed image:

```text
BACKGROUND_RESULT {"path":"absolute image path"}
```

Logs and actionable errors go to stderr. A later batch failure does not remove
earlier completed images or their result events. Download responses must have a
PNG signature before being saved. No outputs are automatically imported,
published or animated.

## Tests

```powershell
python -m unittest test.test_background_scene -v
python -m unittest discover -s test -q
```

Focused tests cover pools, flags, weights, deterministic rolls, context and
dependent compatibility, locks, blank omissions, batch diversity, strict plan
validation, prompts, workflow wiring, unique images, sidecars and source identity.
The CLI integration test uses a local HTTP fixture at the ComfyUI boundary to
exercise upload, graph submission, history polling, download and result events.
It does not run a GPU render or validate generated visual quality.

The existing full Python suite currently has seven independently reproduced
failures in NPC flag documentation, role locks, scientist trait distributions
and token prompt budgets. These checks are outside the background feature;
the user's existing NPC table edits have been preserved.
