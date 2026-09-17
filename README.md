# Lancer Art Generator

## Art styles and private generation

The generation CLIs accept `--art-style ID` and `--art-styles PATH`. The latter
defaults to `art-styles.json` beside the scripts. Its format is:

```json
{
  "styles": [
    {"id": "ink", "name": "Ink wash", "prompt": "Monochrome ink wash with soft paper texture.", "hidden": false}
  ]
}
```

The built-in `default` style always preserves the original subject-specific
prompts. The built-in `none` style (**None (no art style)**) removes the house
rendering clauses and adds no `Art style:` suffix. Both remain available when
the catalog is missing, blank, or empty; neither reserved ID can be redefined.
Custom styles replace the house rendering
clauses while retaining subject and framing instructions. IDs use letters,
digits, hyphens, and underscores; names must be nonblank. Prompts must be strings;
empty or whitespace-only prompts behave like `none`.
`secret: true` is accepted as an alias for `hidden: true`.

Hidden styles require `--secret`. Every `--secret` job, including one using the
default or a public style, also requires `--secret-config PATH`. That JSON file
must contain `secretImagesDir`; the GUI configuration file can be passed
directly. Relative storage paths resolve beside the configuration file.

```powershell
python generate-npc.py --art-style ink --dry-run
python generate-npc.py --art-style none --dry-run
python generate-npc.py --secret --secret-config C:/private/lancer-config.json --art-style ink
python generate-spaceship.py --secret --secret-config C:/private/lancer-config.json
```

### Private tables, and switching a default table off

The Import GUI's Secret Create NPC page includes a **Prompt composer**. It
previews the generator's prompt fragments, identifies their source tables,
and lets you reorder them and add literal custom text independently for the
portrait and token. Secret presets and generated records retain the layout;
regeneration and trait rerolls reuse it. Random sources appear as placeholders
in the GUI; conditional fragments can change when those traits roll.

`--prompt-preview` prints the fragments as JSON without rendering or writing
records. `--prompt-layout JSON` accepts an object with `portrait` and/or `token`
arrays of fragment IDs (from the preview), mixed with custom text objects such
as `{"id":"custom:opening","text":"Dramatic overhead lighting."}`. Custom
text is literal, including braces. Unspecified fragments remain included;
newly active fragments follow the saved sequence, while inactive IDs are kept
for later reactivation. Omitting the layout preserves the existing prompts.

`generate-npc.py` can roll tables of your own alongside the default ones.
`--extra-tables PATH` (repeatable) loads a file of them; every table in every
loaded file rolls one value per NPC, by weight, and the values are appended to
both prompts as one extra sentence, in table order, after the line naming what
the NPC carries. The rolled values are recorded on the manifest entry as
`extraTraits` and in the dossier, so a regeneration reproduces them. Two file
shapes are read, told apart by extension:

```json
{
  "camera_framing": [
    {"value": "low angle looking up", "weight": 3},
    {"value": "eye level medium shot"}
  ]
}
```

```markdown
## camera_framing

- x3 low angle looking up
- eye level medium shot
```

A missing JSON weight is 1; a markdown `xN ` prefix is the weight, exactly as
in `npc-generator-tables.md`, and a markdown bullet is taken whole - the
`|| flag` and `=> Name` conventions the default tables use mean nothing to a
private table, which is appended as text and never filtered. A table name that
matches a default table is refused, as is the same name in two files.
`--extra-table NAME` (repeatable) rolls only the named tables from the loaded
files.

#### Tags and gates

A private table can be *gated*: it rolls only when a value rolled (or fixed)
earlier carries one of its tags.

```markdown
## Styles
- x2 Rugged dockworker #man
- x2 Elegant courtesan #woman #noble

## Men's Attributes (when: man)
- heavy stubble #scarred
- broad shoulders

## Scars (when: scarred)
- a burn scar across one cheek

## Jewellery (when: woman, noble)
- a thin gold circlet
```

- `#tag`s at the very end of a bullet are removed from the value and name the
  gates it opens (letters, digits, `-`, `_`; case-insensitive). Any trailing
  `#word` is a tag, digits included - `Jersey number #7` rolls as `Jersey
  number`; put such text earlier in the line or drop the space before the `#`.
- `(when: a, b)` at the end of a heading gates the table; it opens on *any*
  listed tag. The table's name is the heading without the suffix, so
  `--extra-value "Men's Attributes=broad shoulders"`.
- Tables roll in order: files in `--extra-tables` order, then tables in file
  order. A gated table above every table that could open it is refused; a tag
  no loaded file carries simply keeps the gate shut.
- Fixing a value in a gated table narrows its single Random opener to the
  values that open it; if no table, or more than one, could open it the run
  stops with a message saying which.
- JSON: `{"value": "...", "tags": ["man"]}` on a row, and
  `"Men's Attributes": {"when": ["man"], "rows": [...]}` for a gated table.

`--extra-target TABLE=portrait`, `TABLE=token`, or `TABLE=both` (repeatable)
chooses which image prompts receive a selected table's value. Unspecified
tables apply to both images, sharing one roll. For example,
`--extra-target camera_framing=portrait` keeps that table out of the token
prompt. Targets are saved as `extraTraitTargets` in the manifest and retained
when regenerating or rerolling traits; older entries default to both.

`--disable-table TABLE` (repeatable) leaves a default table's clause out of
both prompts - `--disable-table Stance` when a private table describes the
pose. The trait is still rolled, so every filter that reads it runs as before
and the seed reproduces the same NPC; only the sentence goes, and the dossier
marks the row `(disabled)`. Every table in `REQUIRED_TABLES` can be selected
independently. Backdrop removes the rolled shot and scene in favor of neutral
portrait framing. Hair colour removes the base and appended colour tail while
retaining the cut; Glow placement keeps the colour with a generic glow
description. Age removes maturity and face-age wording, and Pronouns uses
neutral narration without the gender description. Names, callsigns and Theme
already contribute no direct image-prompt text: their switches record the
choice while keeping the metadata, folder names, IDs and roll dependencies.

```powershell
python generate-npc.py --dry-run --extra-tables prompts/secret-tables/mine.json --disable-table Stance
python generate-npc.py --dry-run --extra-tables mine.md --extra-tables more.json --extra-table camera_framing
```

`prompts/secret-tables/` is gitignored and is where the Import GUI looks for
these files in Secret mode. The flags themselves are not tied to `--secret`.

Private NPCs, ships, and backgrounds go under `secretImagesDir/npcs`,
`secretImagesDir/spaceships`, and `secretImagesDir/backgrounds`. The shared
private manifest is `secretImagesDir/manifest.json`. Output overrides and
regeneration paths must resolve inside that root. Records retain `art_style`
(`id`, `name`) and `secret` metadata; regeneration retains the saved style unless
explicitly changed. Missing saved style definitions cause a clear failure.

Background creation accepts the same flags for preview and render; pass the
same selection for both. Expressions, animation, and 3D commands also accept
the privacy flags and refuse recognized private sources without them. Private
ComfyUI uploads and output prefixes use a separate `secret/` namespace,
including intermediate background-removal and mesh passes. ComfyUI itself is
an operator-controlled backend; browser authentication is provided by the GUI
server, not by these trusted local CLIs. No credentials are shipped here.

### Custom NPC and spaceship image dimensions

Add `--token-width 1024 --token-height 1024` to override only the token canvas.
For example, `--width 1920 --height 1080 --token-width 1024 --token-height 1024`
renders a landscape portrait and square token. The token pair can also be used
alone, leaving the portrait at its default. Without a token override, the shared
`--width`/`--height` setting still applies to both images. Token overrides are
saved separately as `tokenImageDimensions` and restored during regeneration;
spaceship token pixel metadata also reflects the override.

`generate-npc.py` and `generate-spaceship.py` accept `--width` and `--height`
together, for example `--width 1920 --height 1080`. Each dimension must be a
multiple of 8 from 64 to 8192 pixels. Both portrait and token renders use the
requested canvas unless a token override is supplied; omitting all size flags
keeps their existing default sizes.
The manifest records `imageDimensions`, which regeneration reuses unless a new
pair is supplied. Workflows must expose an editable latent canvas. Additional
resizing nodes in a custom workflow still affect its final output.

The Import GUI exposes these options in Secret mode and saves them in Secret NPC
presets. Update both repositories together.

### Colour guidance

`generate-npc.py` also accepts `--color-guidance ID` and
`--color-guidance-catalog PATH` (default: `color-guidance.json` beside the
scripts, see `color-guidance.example.json`). The catalog has the same shape as
the art style one under a `guidance` key, and each entry's `prompt` is a
complete palette sentence:

```json
{
  "guidance": [
    {"id": "sun-bleached", "name": "Sun-bleached desert", "prompt": "Keep the palette to sun-bleached ochre, dusty teal and bone white."}
  ]
}
```

The built-in `default` keeps the house line ("Keep the palette restrained -
greys, olive drab and rust ..."). A custom entry replaces that sentence in both
the portrait and token prompts; the rolled glow, which is light rather than
pigment, keeps its own short sentence ahead of it. The built-in `none`
(**None (no colour guidance)**) drops the palette sentence entirely, so the
prompt says nothing about colour beyond the glow's own line. Manifest records carry
`color_guidance` (`id`, `name`) and regeneration reuses the saved guidance
unless `--color-guidance` names another. `hidden: true` entries require
`--secret`, as with art styles.

A ComfyUI-driven batch art pipeline for a *Lancer* TTRPG campaign, extracted
from the [Lancer-TTRPG-GM-Hub](https://github.com/masterevan27/Lancer-TTRPG-GM-Hub)
campaign repository into its own standalone tool. Three entry points —
`generate-art.py`, `generate-npc.py` and `generate-spaceship.py` — turn
prompt-table markdown into batches of ComfyUI renders in the campaign's house
style, and three more take those renders further: `generate-3d.py` into a
printable figure, `animate-portrait.py` into a looping animation, and
`generate-expressions.py` into SillyTavern expression sprites.

**This repository is a sibling clone of `Lancer-TTRPG-GM-Hub`, not a
submodule.** It has no dependency on the Hub at runtime or in its git history;
clone it anywhere. The sibling relationship only matters for humans keeping
both checked out side by side, and for the `npc-trait-import` skill note
below.

## Tooling

### `generate-art.py`

Batch-generates images from the art-prompt markdown files through ComfyUI's HTTP
API. It pulls every prompt block out of a prompts file, queues one job per prompt
against an API-format workflow, and writes results into ComfyUI's output folder
under a path mirroring the markdown headings. Standard library only — no pip
installs. Chain image-to-image passes with `--post` to take a mech from text to
image to transparent PNG in one run; those passes write to their own root
(`LancerFoundryTokens/` by default, same heading structure underneath), so the
finished transparent PNGs are a self-contained tree to import into Foundry.

```
python generate-art.py --list
python generate-art.py --dry-run
python generate-art.py --filter blackbeard --variants 3
```

Start with `--list` or `--dry-run`. Full documentation:
[`docs/generate-art.md`](docs/generate-art.md).

### `generate-npc.py`

Rolls random human NPCs — pilots, mechanics, dock hands, corpo liaisons — from
the tables in `prompts/npc-generator-tables.md` and generates each one a
matched pair of images in the campaign's house style: a 1024x1024 portrait
for the Foundry actor sheet, and a full-body token run through background
removal into a transparent PNG. Both come from the same roll, so they depict
the same person. Each NPC gets its own folder under the output root, holding
the two images and a markdown dossier recording the rolled traits, the seed,
and both prompts verbatim.

It's a separate entry point rather than a flag on `generate-art.py` because that
script's whole model — filtering, resuming, the manifest, the output tree — is
keyed to the headings of an authored prompt file, and a random NPC has no such
entry to key against. All the ComfyUI plumbing is imported from `generate-art.py`
rather than duplicated.

```
python generate-npc.py --dry-run --count 5
python generate-npc.py --count 3
```

Private table rolls can fix a value with `--extra-value "TABLE=VALUE"` alongside
`--extra-tables PATH` (repeat for multiple tables). The value must occur in a
selected extra table; other tables retain their weighted random rolls. The
Import GUI's Secret mode offers these choices and saves private Create NPC
recipes under `prompts/presets/secret-presets/`.

Adding options to a table needs no code change — every `-` bullet under a `##`
heading in the tables file is one option. A `- => Name` bullet is a group
reference, one slot that resolves from `## Name`; the tables file's own
preamble explains it. The exception is `GENDER_TRAITS` in the
script, a short clause the prompt asserts for every NPC of one gender rather than
rolling for it, since a single bullet in a pool of thirty rarely comes up. Full
documentation, including worked examples for rolling a whole group of related NPCs:
[`docs/generate-npc.md`](docs/generate-npc.md).

### `generate-spaceship.py`

Rolls random spaceships — patrol boats up to fleet carriers — from the tables in
`prompts/spaceship-generator-tables.md` and generates each one a matched portrait
and token, the same shape `generate-npc.py` produces for people. It shares that
script's markdown table parser, theme filters, glow subsystem and ComfyUI
plumbing by loading `generate-npc.py` by path rather than duplicating it — the
same technique `generate-3d.py` already uses for `DEFAULT_MANIFEST` — so it
changes zero lines of `generate-npc.py`, `generate-art.py` or `generate-3d.py`.
What a hull is allowed to carry (which sizes a Ship type can roll, which
equipment tables a given size may reach) lives in `ship_policy.py`.

Unlike an NPC, a ship's token is not one fixed size: Foundry draws it across
1 to 5 grid hexes depending on the rolled Size band, so the token's canvas, its
aspect and the framing language in its prompt all vary per ship, and the
manifest entry carries the grid width and height for the Foundry importer to
set `token.width`/`token.height` from.

```
python generate-spaceship.py --dry-run --count 20
python generate-spaceship.py --count 3
python generate-spaceship.py --ship-type carrier --size huge
python generate-spaceship.py --ship-catalogue
```

Start with `--dry-run`, same as the other two generators. See
[`docs/spaceship-render-notes.md`](docs/spaceship-render-notes.md) for notes
from the first real renders, including an open, unresolved framing issue on
the largest (multi-hex) hulls.

### `generate-3d.py`

Turns an NPC already in `.generated-npcs.json` into a printable 32 mm STL, a
cleaned 3D shell and four turnaround renders, by re-rendering its token in a
forced A-pose and reconstructing from that. Needs a running ComfyUI and
Blender 5.2. See [docs/generate-3d.md](docs/generate-3d.md).

```
python generate-3d.py --filter Sokolova
```

### `generate-expressions.py`

Makes transparent 768×1344 full-body WebP expression sprites from a generated
NPC's token or portrait, or any supplied character image. NPC mode uses an
existing token first and falls back to its portrait; `--source token` and
`--source portrait` make that choice strict. It supports all 28
SillyTavern default labels, weighted prompt tables, custom expressions, safe
add/replace variants and exact-file redo. Each edit asks Qwen to match style
from the chosen reference image; recognized stored NPC token or portrait
prompts contribute only that source's original style wording without carrying
over the old expression, pose, backdrop or framing. Default expressions add
matching full-body stance and gesture cues while keeping the head, hands and
feet within the canvas. Sidecar metadata records the actual source kind, path
and timestamp. Style matching is not guaranteed, and existing sprites are
never regenerated automatically: Redo or Replace opts them into current
framing, pose and source-style guidance.

```powershell
python generate-expressions.py --id npc-jules-sokolova-40213 --dry-run
python generate-expressions.py --id npc-jules-sokolova-40213 --source portrait -e joy
python generate-expressions.py --id npc-jules-sokolova-40213 -e joy,anger
python generate-expressions.py --image portrait.png --custom "battle focus=cold determination"
```

See [docs/generate-expressions.md](docs/generate-expressions.md) for setup,
selection rules, variant safety and SillyTavern custom-label configuration.

### `animate-portrait.py`

Turns any portrait image into a looping animated `.webp` — a slow blink, a
faint smile, a few degrees of head tilt — through Wan 2.2 image-to-video. It
takes an image rather than a rolled NPC, so it is not wired into the
generators; run it by hand on whatever portrait you like, or from the import
GUI's NPC page, whose Animated portrait panel runs it over a rolled NPC's
portrait. `--roll` draws the motion from the `## Animation` table in
`prompts/npc-generator-tables.md` — the one table there the NPC generator
never rolls, written to move hair, clothing and backdrop while the figure
holds still. Needs a running ComfyUI with the Wan 2.2 I2V models. See
[docs/animate-portrait.md](docs/animate-portrait.md).

For editable procedural scenes, full-frame backgrounds, and reference-based
gridless top-down maps, see [Dynamic backgrounds and battlemaps](docs/dynamic-backgrounds.md)
and `generate-background.py`. Its scene catalogue supports reproducible previews,
per-trait locks and batch rendering, with metadata saved beside each image.
Scenes now include distinct people by default, with population density, balanced
or lush vegetation, and optional indoor pets/aquariums. All choices are saved
with the scene; top-down maps omit people and pets.
People traits customize civilian, military or mixed groups, clothing and equipment,
adult ages, appearance and activities. Expanded scene pools include military settings
and NPC-inspired backdrops, rendered with the NPC prompts' painterly house style.

`--background` points the same machinery at a scene instead of a face:
widescreen, a motion prompt that moves smoke and cloud and lights rather
than a mouth, and `--roll` reading the `## Background Animation` table in
`prompts/scene-and-spaceship-tables.md`. The output is a looping `.webp`
sized and quantised to drop straight into SillyTavern's backgrounds folder.
If you have no background still to animate yet, render one first from
`prompts/scene-background-art-prompts.md`, which carries twenty-two scenes in
the same painterly house style as the NPC portraits. Twenty of them are composed
for this job rather than as standalone pieces — nobody in the frame, a quiet
middle where a chat panel will sit, and every moving element named by a bullet
in the animation table so `--roll` has something to move.

`prompts/city-background-art-prompts.md` does the same job outside the house
style: photorealistic modern and near-future cities at night, no linework, no
halftone, nothing Lancer. Nothing in the pipeline enforces either look —
`Lancer_Scene_Workflow_v1.json` carries a detail slider and no style LoRA — so
the same workflow renders both families and the style lives entirely in the
prompt text. That file carries a per-section motion line to pass with `-d`
instead of using `--roll`, whose table names smoke, embers and dropships.

By default the animation is played forward and back, so it lands on the frame
it started on. `--no-pingpong` plays it forward once instead, at the same
length and about twice the render — the right choice when the motion has a
direction, like drifting smoke or crossing cloud, that a reversed half would
give away.

```
python animate-portrait.py "Jules Sokolova Portrait.png"
python animate-portrait.py portrait.png -d "she laughs and looks away"
python animate-portrait.py portrait.png --roll --seed 7
python animate-portrait.py canyon.png --background --roll --seed 7
python animate-portrait.py canyon.png --background --no-pingpong
```

### Tests

Standard library `unittest`, no dependencies:

```
python -m unittest discover test
```

Tests load the generator by path (its hyphen makes it non-importable) and roll
against `test/fixtures/tables-minimal.md` rather than the live tables, so
authoring a bullet never breaks a test. The exceptions are the guards that have
nothing to say about a fixture, and so read the live tables file: where a
`@theme` tag may appear, the Headgear register's classification, and the check
that the `npc-trait-import` skill documents every flag the tables actually use.
That last one exists because the skill's own handoff checklist refuses a staged
bullet whose flag is undocumented, which had quietly drifted five flags behind.

**Changing the tables means re-checking that skill, and two test files enforce
it rather than leaving it to habit.** The skill is documentation the generator
silently depends on: a staging run copies its shape lines to write bullets, and
`generate-npc.py` ignores an unrecognized flag rather than reporting one, so a
skill that has fallen behind produces bullets that fail quietly in the render.

- `test/test_import_skill_flags.py` — every flag the tables use appears in all
  **three** places the skill names flags: its §0 flag table, its §4 per-table
  shape lines, and its §3 routing rows. Add a flag and all three must follow.
  A flag a run must never author (`Weapon/none`, `Headgear/bare` — an image
  cannot show an absence) is exempted by name in `NEVER_STAGED`, with a reason.
- `test/test_import_skill_shape.py` — the two gaps that one leaves. Every table
  the generator rolls either has a shape line or is named in `NOT_STAGED` with
  a reason, so a **new table** cannot be added without a decision about whether
  the skill stages it; and each shape line's `||` **segment count** matches
  what the generator actually reads, so a bullet staged from it cannot put its
  flags where `flags_for()` reads prose. It also pins the three-segment table
  list against `flags_for()` itself, so a fourth added there fails here.

Between them: add a flag, add a table, or change a table's shape, and the suite
tells you exactly which part of the skill to update.

Theme visibility is measured rather than asserted, because the number is a
property of the content and the content is authored over time:

```
python -m test.theme_visibility                  # the live tables
python -m test.theme_visibility --tables test/fixtures/tables-themed.md
```

That prints, per theme and per gated table, how much content the theme has and
how often a rolled NPC of that theme actually got one of its bullets rather
than a neutral one, and marks with `!` each table whose tagged bullets lose
more often than the `THEME_SHARE` target. Run it while tagging to watch a
theme come up; most themes carry only a handful of tagged bullets so far, so
the live tables still report a good many `(untagged)` cells and `!` marks.

Prompt length is measured too, against Krea 2's 512-token ceiling — a prompt
that runs long silently loses its tail, which is where the palette and the
flat-white background instruction live:

```
python -m test.prompt_budget
```

### Output location

Both scripts write renders under ComfyUI's own output folder. Set
`COMFYUI_OUTPUT_DIR` to point at a ComfyUI install elsewhere on your machine;
if it's unset, they fall back to an `output/` folder beside the scripts (i.e.
at the repository root), so a fresh clone runs without any configuration.

### Workflow formats

<details>
<summary><strong><code>workflows/</code> keeps the same graphs twice, because ComfyUI uses two incompatible JSON shapes</strong></summary>

- **`workflows/editable/`** — UI format, with node positions and links. Drag these
  onto the ComfyUI canvas to edit them by hand.
- **`workflows/api/`** — API format, a flat map of node ids. This is what
  the `/prompt` endpoint accepts and what `generate-art.py` consumes.

Edit the editable copy, then re-export via **Workflow → Export (API)** to
refresh its API-format twin.

</details>

## Staged imports, and table presets

Two folders under `prompts/` hold JSON written by tooling rather than by hand,
and they are tracked on opposite terms because they are opposite kinds of file.

`prompts/staged-imports/` is a working folder for candidate NPC-table entries
extracted from reference images (see the `npc-trait-import` skill below). Its
JSON files are gitignored so a run doesn't dirty the tree; `examples/` holds
three worked examples that stay tracked as a reference for the file shape.

`prompts/presets/` holds **table presets** — a snapshot of which bullet is
enabled in every table and at what roll weight, saved as one file. This is the
default location the Import GUI (below) writes them to; nothing in this
repository reads or writes them, and the generator itself is unaware of them,
since a preset is applied by editing `npc-generator-tables.md` in place rather
than by being passed to a run. They are **not** gitignored, unlike the staged
imports beside them: a preset is meant to be handed to another GM, so a named
one is content worth keeping in history. That does mean saving a preset leaves
the tree dirty until you commit it or throw it away.

## The Import GUI

The tool that edits the tables and turns a rolled NPC into a Foundry Actor
lives in a sibling clone at `G:\GIT-REPOS\lancer-npc-import-gui`. It reads
this repository directly — `.generated-npcs.json` for the run log,
`prompts/npc-generator-tables.md` for the tables, and the two folders above —
and shells out to `generate-npc.py` to roll new NPCs and re-roll single traits.

Nothing here depends on it: the generator runs standalone, and every table edit
it makes is an edit you could make in a text editor. It matters to this
repository only because it is a second writer of
`prompts/npc-generator-tables.md`, so a table's on-disk shape — the `- ` bullet
under a `##` heading, the `|| flag` suffixes, the `xN ` weight prefix, the
`=> Name` group reference — is a contract between the two, not just a
convention. See that repository's README.

## The `npc-trait-import` Claude Code skill

`.claude/skills/npc-trait-import/SKILL.md` extracts backdrops, poses, gear,
outfits, hair, expressions and similar traits out of reference images and
stages them as candidate entries for `prompts/npc-generator-tables.md`. It is
only picked up by Claude Code when Claude Code is run **from this
repository's root** — Claude Code discovers skills under the current
project's `.claude/skills/`, not from an arbitrary working directory. If you
want it available while working elsewhere (e.g. from the Hub), symlink it
into your user-level skills directory instead of copying it, so edits here
stay the single source of truth (adjust the source path if you cloned this
repository somewhere other than `/g/GIT-REPOS/lancer-art-generator`):

```
ln -s "/g/GIT-REPOS/lancer-art-generator/.claude/skills/npc-trait-import" ~/.claude/skills/npc-trait-import
```

## The `spaceship-trait-import` skill

`.agents/skills/spaceship-trait-import/SKILL.md` (Codex) and its matching
`.claude/skills/spaceship-trait-import/SKILL.md` extract spaceship traits from
reference images. Invoke `spaceship-trait-import` with images or a folder.
It stages candidates in `prompts/staged-imports-spaceship/` with reference
copies for the Import GUI's **Spaceships → Trait Imports** view. Hulls,
equipment, scenes and lighting follow the ship generator's type/size policies;
the skill leaves the live tables unchanged for selective review.

## License

Dual-licensed, because this repository holds both prose and code:

- **Written material** — the prompt tables under `prompts/`, and other
  documentation — under
  [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
  See [`LICENSE`](LICENSE). The prompt tables are the headline content here —
  the house style people actually want — so this is the license that governs
  most of what you'd copy out of this repository.
- **Code** — `generate-art.py`, `generate-npc.py`, and the JSON presets,
  configs, and workflows — under the MIT license. See
  [`LICENSE-CODE`](LICENSE-CODE).

*Lancer* is a trademark of Massif Press. This is an unofficial fan project, not
affiliated with or endorsed by Massif Press, and contains no rulebook text.
# Choosing a generation workflow

`generate-art.py`, `generate-npc.py`, `generate-spaceship.py`, and dynamic
scene rendering with `generate-background.py` accept `--workflow PATH` for a
ComfyUI API-format JSON graph. The graph must expose the prompt, sampler,
latent size, and image output slots supported by the generator.

For NPCs, an explicit `--workflow` applies to every gender and overrides the
recorded workflow during regeneration. `--workflow-woman` can still provide a
separate override for new women NPCs. Without `--workflow`, existing defaults
and recorded regeneration workflows continue to apply. Spaceship regeneration
also keeps its recorded workflow unless `--workflow` overrides it.

The import GUI discovers graphs in `workflows/api/`. Put private graphs in
`workflows/api/secret/` to make them selectable only in Secret mode. `UTIL_`
files are always excluded. Optional `workflows.json` beside the scripts uses
the format in `workflows.example.json` to give main-folder graphs friendly
names or mark them `hidden`/`secret`. This local catalog is ignored by Git.
