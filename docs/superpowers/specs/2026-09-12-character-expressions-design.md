# Character expressions: SillyTavern expression sprites from one portrait

**Date:** 2026-09-12
**Status:** approved in discussion, awaiting review of this document
**Repositories:** `lancer-art-generator` (the script, the workflow, the tables
file), `lancer-npc-import-gui` (the NPC-page panel, the SillyTavern import, the
Expressions kind on the Tables tab)

## 1. The goal

SillyTavern's Character Expressions extension swaps a character's sprite to
match the emotion of each reply. It looks for images in
`data/<user>/characters/<Character Name>/`, named `<label>.<format>`. Several
files for one label are allowed with a dash or dot suffix (`joy-1.webp`,
`joy.expressive.webp`), and SillyTavern picks among them at random. Names must
be lowercase, the folder flat, and PNG, WEBP and GIF keep transparency.

The 28 default labels (the GoEmotions set) are:

admiration, amusement, anger, annoyance, approval, caring, confusion,
curiosity, desire, disappointment, disapproval, disgust, embarrassment,
excitement, fear, gratitude, grief, joy, love, nervousness, neutral, optimism,
pride, realization, relief, remorse, sadness, surprise.

We want what tavernsprite.com does, locally: take an NPC's portrait (or any
character image), and produce transparent `.webp` sprites for all 28 labels, a
chosen subset, a single label, or a user-supplied custom label. That should work
from the CLI and from the import GUI.

## 2. What exists today

- `workflows/api/Util_BackView_QwenEdit_v1.json` is a Qwen-Image-Edit-2509
  (fp8, Lightning 4-step LoRA) graph that edits a reference image while keeping
  identity. `generate-3d.py` `build_backview_job` / `generate_back_view`
  (953-1051, 1386-1440) is a complete upload → patch → queue → fetch example.
- `workflows/api/Util_RemoveBackground_makeTransparent.json` is LoadImage →
  RMBG → SaveImage.
- `animate-portrait.py` shows the standalone-image script shape: it reuses
  `generate-art.py`'s `Comfy` client and `find_server`, uploads via multipart
  POST, finds nodes by class type, prints plain progress lines, and exits
  non-zero on failure. It gets its WebP from ComfyUI (`SaveAnimatedWEBP`), not
  Python. Pillow is not installed and every script is standard library only.
- NPC data lives in `.generated-npcs.json` (keys `callsign, files, name, seed,
  tables, traits, when`), and each NPC has a folder
  `runN/<Role category>/<Name>/` holding `<Name> Portrait.png`.
- The GUI's Animated Portrait and 3D panels share one pattern: a pure
  `lib/*.js` argv builder, an in-memory job map keyed by item id, the last
  stdout line as the stage, 2-second polling, and a `supports.*` capability
  flag per kind in `lib/kinds.js`.
- The Tables tab edits a markdown tables file per kind (`kind.tables`) through
  `/api/table-bullets?kind=`. The GUI has one SillyTavern setting,
  `sillyTavernBackgroundsDir`, and one SillyTavern write,
  `importBackgroundToSillyTavern`. Nothing writes into `characters/`.

## 3. Decisions made in discussion

| Question | Decision |
|---|---|
| Generation approach | One Qwen edit job per sprite, always from the original portrait. Not a neutral-base chain (one bad base spoils all 28) and not a sliced grid (≈256 px, identity drift). |
| What the Tables-tab "expressions list" is | Rollable prompt tables: `prompts/expression-tables.md`, one `## <label>` table per label with weighted bullets, so variants of one label actually differ. |
| Where sprites go | The NPC folder's `expressions/` (or `--out` for a supplied image). The GUI imports into SillyTavern with a button, and never writes there automatically. |
| Background | Transparent by default (RMBG in the graph), `--keep-background` to opt out. |
| Re-running a label that already has a sprite | Chosen per run: add a variant (default) or replace. A full default run skips labels that already have a sprite. Per-sprite Redo and Delete in the GUI. |

## 4. `generate-expressions.py` (lancer-art-generator)

### 4.1 Input: exactly one source

- **NPC mode:** `--id <id>` (and the `--manifest` / `--filter` / `--exclude` /
  `--limit` selection flags `generate-3d.py` has). It reads the portrait and
  traits from the manifest and writes to `<NPC folder>/expressions/`.
- **Image mode:** `--image <path> [--out <dir>] [--name <Name>]`. Traits are not
  available, so prompts use only the identity preamble and the rolled bullet.
  `--out` defaults to `<image stem>-expressions/` next to the image.

Passing both, or neither, is a usage error (exit 2).

### 4.2 Which expressions

- `--expressions all` is the default, meaning the 28 labels in the order above.
- `--expressions joy,anger` or `-e joy` selects a subset or a single label.
  Unknown names are an error unless they are also given as `--custom` or have
  a table in the tables file.
- `--custom "<label>=<prompt text>"` can be repeated. The label is sanitised:
  lowercased, whitespace and anything other than `[a-z0-9_]` turned into `_`,
  and leading/trailing `_` stripped. An empty result is an error. The
  `=<text>` part is optional when `prompts/expression-tables.md` already has a
  `## <label>` table. SillyTavern only uses a custom label once that label is
  added in its Expressions settings, and the README says so.
- `--count N` (default 1) makes N files per label in this run.
- `--file <name.webp>` redoes exactly one existing file. Its label is parsed
  from the name and it implies `--replace` for that one file only (§4.5). This
  is what the GUI's Redo button calls.

### 4.3 Prompt assembly

Each sprite's edit instruction is built from three parts:

1. **Identity preamble (fixed):** keep the same character, face, hairstyle,
   outfit, colours, art style, camera framing and pose. Change only the facial
   expression and small body language. Front-facing bust, no text.
2. **Identity anchors (NPC mode only):** the manifest traits that describe
   appearance: `Hair`, `Hair colour`, `Feature`, `Outfit`, `Headgear`, each
   included when present. `Demeanor` is deliberately left out: it is a rolled
   fixed facial expression and would fight the target one. Weapons, gear,
   backdrop and stance are also left out.
3. **Expression:** a bullet rolled from `## <label>` in
   `prompts/expression-tables.md`, using the same parser semantics as the NPC
   tables (`xN` weights, disabled `<!-- - -->` bullets skipped, table groups
   honoured, all by reusing `generate-npc.py`'s `parse_tables` rather than a
   fifth parser). With `--custom label=text`, the text replaces the roll.
   `--describe <text>` replaces the roll for every selected label (for
   free-text overrides from the CLI).

Each label's table must say the label's emotion in words, not only in facial
mechanics (for example "joyful, wide grin, eyes crinkled"), so the model and a
reader agree on what is meant.

### 4.4 Rendering

- New workflow `workflows/api/Util_Expression_QwenEdit_RMBG_v1.json`, derived
  from the back-view graph with one reference image, then RMBG, then save.
  `--keep-background` routes the decoded image straight to the save node.
- Nodes are found by class type or link-following, as in `animate-portrait.py`
  and `build_backview_job`, never by hard-coded node id.
- **WebP output:** the save node is ComfyUI's `SaveAnimatedWEBP` with one frame,
  which keeps the script standard library only. The first implementation task
  checks that a one-frame save keeps alpha. **If it does not**, the fallback is
  a `SaveImage` PNG plus conversion with Pillow, and Pillow becomes a documented
  requirement of this script only (imported inside the function, with a clear
  error if it is missing). `--quality` (default 90) is passed through.
- The seed is random per sprite unless `--seed S` is given, in which case sprite
  k of the run uses `S + k`. `--steps`, `--server`, `--timeout` and `--dry-run`
  behave as in the other scripts. `--dry-run` prints each planned file, its
  label and its full prompt, and queues nothing.
- Uploads go to input subfolder `lancer-expressions`.

### 4.5 Files, variants and re-runs

The first file for a label is `<label>.webp`, then `<label>-1.webp`,
`<label>-2.webp`, …, always taking the lowest free index.

| Mode | Behaviour |
|---|---|
| default (`add`) with explicit `-e`/`--custom` | Adds `--count` new files per label next to whatever exists. |
| default with `--expressions all` (explicit or implied) | Skips labels that already have any file, and says so in the output. |
| `--replace` | For each selected label, first deletes `<label>.webp`, `<label>-N.webp` and `<label>.<anything>.webp`, and removes their sidecar entries, then writes `--count` fresh files starting at `<label>.webp`. Deletion happens only after that label's first render succeeds (the render is held in memory), so a failed replace does not leave the label empty. |
| `--file joy-1.webp` | Renders one new sprite for `joy` and writes it over exactly `joy-1.webp`. Other files are untouched. |

`expressions/expressions.json` is a sidecar mapping each filename to
`{label, prompt, seed, keepBackground, source, when}`. `source` is the portrait's
path and mtime, so the GUI can flag sprites made from an older portrait. Writes
are atomic (temp file + rename).

### 4.6 Progress and exit codes

Plain, flushed stdout lines, which the GUI shows as the last line:

```
source: .../Vex Portrait.png (npc Vex)
skip: joy (already has 2 files)
[3/28] anger: rendering (seed 12345)
wrote expressions/anger.webp (41 KB, 6.2 s)
failed: grief: <reason>
done: 27 written, 1 skipped, 1 failed
```

One failed label does not stop the run. The exit code is 0 only if nothing
failed, 1 if any sprite failed, and 2 for usage errors. Warnings go to stderr.

### 4.7 Tables file

`prompts/expression-tables.md` gets a short header explaining its purpose, then
one table per default label in the order above, each with 4-6 weighted bullets
written for a bust sprite. It lives next to the NPC tables, and the GUI resolves
it as `expressionTablesPath` (§5.4).

### 4.8 Tests (`unittest`, `test/test_generate_expressions.py`)

- Label parsing: `all`, comma lists, unknown label errors, `--custom`
  sanitising and the optional `=text`.
- Variant naming (lowest free index) and replace cleanup across all three
  suffix forms, including the "no delete before the first success" rule.
- The skip rule for a full default run.
- Prompt assembly with and without traits, and that Demeanor is excluded.
- Rolling from a fixture tables file through `parse_tables`.
- Graph patching of the new workflow (image, prompt, seed, keep-background
  bypass, quality).
- A live `/object_info` check, skipped without a server, as in
  `test_animate_portrait.py`.
- A `test/helpers.py` loader for the hyphenated script.

Docs: `docs/generate-expressions.md` plus a README section, and the existing
`docs/animate-portrait.md` sprite note links to it.

## 5. GUI (lancer-npc-import-gui)

### 5.1 Server

- `lib/paths.js`: `generateExpressionsScript` (defaulting next to
  `generateNpcScript`) and `expressionTablesPath` (next to the NPC tables).
- `lib/expressions.js` is a pure module:
  - `expressionArgs(opts)` builds the argv:
    `script --id <id> [-e a,b] [--custom l=t]… [--count N] [--replace]
    [--file f] [--keep-background] [--server s]`.
  - `classifyExpressionFiles(names)` groups files by label (all three suffix
    forms), sorts variants, and ignores non-webp files and the sidecar.
  - The list of 28 default labels, shared with the front end.
- `server.js`: `startExpressionJob` spawns `config.pythonExecutable` with cwd
  set to the script folder, tracked in `expressionJobsByItemId`. The stage is
  the last stdout line and the log keeps the last 8000 characters.
  - It refuses to start while a regenerate or animate job for that NPC is
    running, or while an expression job is already running for it.
  - A stale completion is told apart by `jobId`, as the animate fix did.
- `itemView` gains `hasExpressions`, `expressionCount` and `expressionStatus`.
- Routes:
  - `GET /api/expressions?id=`: files grouped by label, sidecar data, job
    status, and the default SillyTavern import target.
  - `POST /api/expressions`: start a job. The body carries `labels[]`,
    `custom[{label,text}]`, `count`, `mode` (`add`|`replace`),
    `keepBackground` and an optional `file`. It is validated with the same
    sanitising as the script.
  - `POST /api/expressions/cancel`.
  - `GET /api/expression-image?id=&file=`: the file name must match a
    classified sprite, and no path separators are allowed.
  - `DELETE /api/expressions/file?id=&file=`: removes the file and its sidecar
    entry.
  - `POST /api/expressions/import` with `{id, folderName}` (§5.3).
- `lib/kinds.js`: `supports.expressions` is `true` for NPCs and `false` for
  spaceships.

### 5.2 Expressions panel (NPC detail page)

It sits next to Animated Portrait and 3D in `public/index.html`, rendered by
`renderExpressionsPanel` / `refreshExpressions` in `public/app.js`, and
refreshed by the existing `startPolling` while a job runs.

Controls:
- A label checkbox grid of the 28 labels, with **All**, **None** and
  **Missing only** buttons. Ticking one label is the single-label case.
- **Custom expression:** a label field and a prompt field. The prompt may be
  empty when the Expressions tables already have that label. An **Add** button
  puts it into the run as a chip, and a run can carry several.
- **Variants per label:** a number, 1-8.
- **Mode:** Add variants / Replace (radio).
- **Keep background:** a checkbox, off by default.
- **Generate** and **Cancel** buttons, plus the stage line and a collapsible log.

Sprite grid:
- Labels in default order with custom labels after, one row per label with its
  thumbnails. A label with no files shows an empty slot.
- Hovering a sprite shows its prompt and seed. A sprite made from an older
  portrait (sidecar mtime ≠ current portrait) gets an "old portrait" badge.
- Per sprite: **Redo**, which starts a job with `file` set, and **Delete**. The
  delete confirmation is an in-page inline confirm, never a browser `confirm()`.

### 5.3 Import into SillyTavern

- A new config key `sillyTavernCharactersDir` in `config.example.json`, the
  `server.js` defaults and the README, validated like
  `sillyTavernBackgroundsDir` (unset → "set sillyTavernCharactersDir…", not a
  folder → an error naming the path).
- The panel shows the target `<dir>/<folderName>/`. `folderName` defaults to
  the NPC's name and can be edited, because it must match the SillyTavern
  character card's name exactly.
- The import rejects folder names with path separators or `..`, creates the
  folder if needed, and copies every classified `.webp` sprite. Same-name files
  are overwritten. Files already there that no longer exist here are left
  alone. It returns and shows `copied N, replaced M` and the path.

### 5.4 Expressions kind on the Tables tab

- `lib/kinds.js` gets a tables-only entry: `id: 'expression'`,
  `label: 'Expressions'`, `subject: 'expression'`,
  `tables: paths.expressionTablesPath`, its own `presetsDir`, and `supports`
  with only `tables: true` (every other flag false, and no
  script/createArgs/regenArgs).
- Every consumer that iterates kinds or reads `?kind=` has to respect the flags.
  The implementation plan starts with an audit of those sites (Import tab,
  Create tab, odds, trait staging and candidates, Foundry export, the
  `/api/items` kind list, `applyKindAvailability`) and fixes any that assume
  every kind has a script or manifest.
- Presets and table groups work unchanged through `?kind=expression`.

### 5.5 Tests (`node --test`, each new server test file on its own unused port)

- `expressions.test.js`: `expressionArgs` for all modes, and
  `classifyExpressionFiles` for all suffix forms and non-sprite files.
- `api.expressions.test.js`, with a Node stub script writing fake webps and
  printing progress:
  - job lifecycle and stage, refusal while another job runs, and the stale
    `jobId`
  - Redo argv and delete
  - image route path-traversal rejection
- `api.expressionsImport.test.js`: the unset, not-a-folder and bad folder-name
  errors, and a copy/replace count into a temp characters folder.
- `ui.expressionsPanel.test.js`: grid, custom chips, mode, and the Redo and
  Delete controls.
- `kinds.test.js` and `api.tablesByKind.test.js` extended: the expression kind
  serves tables and presets, and does not appear on the Import or Create tabs.

## 6. Order of work

1. **lancer-art-generator:**
   - Check that a one-frame `SaveAnimatedWEBP` keeps alpha, and pick the WebP
     path (§4.4).
   - Workflow, tables file, script, tests, docs.
   - Usable from the CLI when done.
2. **lancer-npc-import-gui:** the kinds audit, then the paths/kinds/lib module,
   routes, panel, import, the Tables kind, tests and docs.

Both repos have an unmerged `table-groups` worktree. This work branches from
`main` and does not depend on it, but it reuses `parse_tables`, so whichever
merges second rebases.

## 7. Out of scope

- Animated expression sprites. `animate-portrait.py` can already animate a
  finished sprite by hand.
- Sprites for spaceships.
- Uploading a ZIP to SillyTavern or editing SillyTavern's custom-label list.
- Image mode in the GUI (the CLI covers supplied images).
- Batch expressions across many NPCs in the GUI (the CLI's `--filter` covers
  it).
