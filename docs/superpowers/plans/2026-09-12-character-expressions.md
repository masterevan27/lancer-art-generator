# Character Expressions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate expression sprites from portraits, manage them on NPC sheets, and explicitly import them into SillyTavern.

**Architecture:** The generator owns prompt rolling, image rendering and atomic sprite metadata. The GUI invokes that CLI through a pure argument builder and owns job lifecycle, file access, imports and the panel. Expressions are a tables-only kind, never a generated item kind.

**Tech Stack:** Python standard library and ComfyUI; Node standard library server and vanilla browser JavaScript.

**Spec:** `../specs/2026-09-12-character-expressions-design.md` (binding; both repositories are in scope).

## Global Constraints

- One Qwen edit job per sprite, always from the original portrait.
- Transparent by default (RMBG in the graph), `--keep-background` to opt out.
- Nodes are found by class type or link-following, never by hard-coded node id.
- Reuse `generate-npc.py`'s `parse_tables`: `xN` weights, disabled bullets skipped, table groups honoured.
- Appearance anchors: `Hair`, `Hair colour`, `Feature`, `Outfit`, `Headgear`; omit Demeanor, weapons, gear, backdrop and stance.
- Default labels in order: admiration, amusement, anger, annoyance, approval, caring, confusion, curiosity, desire, disappointment, disapproval, disgust, embarrassment, excitement, fear, gratitude, grief, joy, love, nervousness, neutral, optimism, pride, realization, relief, remorse, sadness, surprise.
- First file `<label>.webp`, then lowest unused `<label>-N.webp`; recognize `<label>.<anything>.webp` too. Labels contain only lowercase `[a-z0-9_]`.
- Replace never deletes existing sprites until the first successful render for that label. Sidecar writes use temp file + rename.
- GUI delete confirmation is inline, never browser `confirm()`. `--describe` remains CLI only.
- SillyTavern copies happen only after an explicit Import action. Do not modify production config or render libraries during tests.
- New server test files use their own unused port. Tests use temporary data, not real NPCs.

## Execution decisions and file boundaries

Generator worktree: `G:/GIT-REPOS/lancer-art-generator/.claude/worktrees/character-expressions`.
GUI worktree: `G:/GIT-REPOS/lancer-npc-import-gui/.claude/worktrees/character-expressions-gui`.
Generator baseline `08c1f67`; GUI baseline `6cb586e`. Existing table-groups worktrees are unrelated and remain untouched.

Use the spec as the full behavioral reference, with these clarifications: explicit NPC selectors (`--id`, `--manifest`, `--filter`, `--exclude`, `--limit`) establish NPC mode; no selector and no image is exit 2. Custom-only runs select only their custom labels unless `-e` was explicitly supplied. Explicit `all` includes all defaults plus supplied custom labels and applies the documented default skip policy when not replacing. Sidecar `source` is `{path, mtime}` with mtime in Unix milliseconds so it compares directly with Node `stat.mtimeMs` (allow sub-millisecond precision tolerance). GUI argv passes configured manifest and expression tables explicitly to honor relocated config.

### Task 1: Generator CLI, graph, prompt tables and documentation

**Files:** Create `generate-expressions.py`, `workflows/api/Util_Expression_QwenEdit_RMBG_v1.json`, `prompts/expression-tables.md`, `test/test_generate_expressions.py`, optional small fixture `test/fixtures/expression-tables.md`, `docs/generate-expressions.md`; modify `test/helpers.py`, `README.md`, `docs/animate-portrait.md`.

**Interfaces:** The complete CLI is spec §4. Add `--tables PATH` to honor GUI `expressionTablesPath`. Export testable parsing, planning, graph and persistence helpers from the script; add `load_expressions()` in test/helpers.py. Output sidecar uses `{filename: {label,prompt,seed,keepBackground,source:{path,mtime},when}}`.

- [ ] Read spec §4 and the transparency probe report supplied by the controller. Reuse client/discovery/upload patterns from animate-portrait.py and NPC selection/portrait resolution from generate-3d.py, without importing unrelated expensive runtime dependencies.
- [ ] Add meaningful failing tests for source and label selection, custom-only runs, sanitization, weighted/group/disabled table semantics, anchored prompts, skip/all, lowest free variant, dot variants, replace failing before success, single-file redo, sequential seeds, graph links and bypass, dry-run queue isolation, partial failure exit status and atomic sidecar preservation.

```python
# Concrete persistence acceptance scenario (adapt helper names to the module):
# Existing joy.webp, joy-1.webp, joy.expressive.webp and anger.webp.
# Failed first joy render under --replace leaves all four bytes and metadata unchanged.
# Successful --replace -e joy --count 2 leaves joy.webp, joy-1.webp and anger.webp.
# --file joy-1.webp changes only joy-1.webp and its metadata.
# -e joy in add mode fills any gap before allocating a higher suffix.
```

- [ ] Implement one-source input selection, all flags/defaults in spec, prompt assembly and planning; errors in usage are exit 2, rendering failures exit 1, success exit 0. `--file` must be a safe basename matching an existing classified file; reject incompatible multi-sprite options. Validate source image existence and selected table pools before queueing.
- [ ] Derive the graph from the checked-in Qwen backview workflow, preserve required model/LoRA settings, patch image/prompt/seed/steps/save quality by class or link. Route RMBG alpha into one-frame SaveAnimatedWEBP if probe confirms it; otherwise use documented lazy Pillow fallback. Upload to `lancer-expressions` and fetch the correct output node result.
- [ ] Render in planned order with flushed progress. Hold first replacement image in memory before destructive cleanup; write images and sidecar atomically. A failed sprite does not abort remaining work. Dry-run prints destination, label and full prompt and makes no server calls or output changes.
- [ ] Write 4-6 weighted, distinct bust-expression bullets per default label, explicitly naming the emotion. Document CLI recipes, defaults, selection, custom labels in SillyTavern settings, variants, safety, quality, dependencies and transparent output evidence; link from README and animation sprite note.
- [ ] Run `python -m unittest test.test_generate_expressions -v`, then the repository suite once; report actual baseline exceptions and live checks separately. Commit only task files using repository commit style.

### Task 2: GUI tables-only kind and pure expression contract

**Files:** Modify GUI `lib/paths.js`, `lib/kinds.js`, `server.js`, `public/app.js`, `public/index.html`, tests `test/paths.test.js`, `test/kinds.test.js`, `test/api.tablesByKind.test.js` and capability-focused tests as needed; create `lib/expressions.js`, `test/expressions.test.js`.

**Interfaces:** `DEFAULT_EXPRESSION_LABELS` ordered array; `sanitizeExpressionLabel(value)`; `classifyExpressionFiles(names)` returns an object mapping labels to naturally ordered filename arrays; `expressionArgs(opts)` accepts `{script,id,manifest,tables,labels,custom,count,mode,file,keepBackground,server}` and returns CLI argv. `derivePaths` adds `generateExpressionsScript`, `expressionTablesPath`, `expressionPresetsDir`; expression presets default below existing presetsDir.

- [ ] Use controller's kinds audit to enumerate capability consumers, then add failing tests proving an installed expression tables file offers a Tables option even without a generator script, but is never an Import category or Create option. Unsupported odds, staging, candidates, create/regen and Foundry actions must reject safely rather than dereference missing paths or methods.
- [ ] Add expressions capability true only for NPCs. Add registry `expression` with only `tables:true` and no script/createArgs/regenArgs. Distinguish table availability from item availability at actual consumers, preserving missing-script behavior for NPCs/spaceships.
- [ ] Add configured path derivation and table presets. Existing table/preset/group operations must work with `kind=expression`; do not merge unrelated table-groups branches.
- [ ] Implement and test the pure expression module, sharing default labels with the frontend through API payload (no duplicate frontend constant). Match Python sanitization and classification including all suffix forms; reject path separators, invalid filenames and invalid count/mode/custom inputs.

```js
// Contract fixtures:
// classifyExpressionFiles(['joy.webp','joy-2.webp','joy-1.webp','joy.soft.webp',
//                         'expressions.json','joy.png','../joy.webp'])
// => {joy:['joy.webp','joy-1.webp','joy-2.webp','joy.soft.webp']}
// expressionArgs({script:'g.py',id:'n',labels:['joy'],count:2,mode:'replace'})
// => ['g.py','--id','n','-e','joy','--count','2','--replace']
```

- [ ] Run focused path/kind/expression/table tests, then the GUI suite once under the controller's verified baseline invocation. Commit and report interfaces and audit outcomes for Tasks 3-4.

### Task 3: GUI expression jobs, safe routes and SillyTavern import

**Files:** Modify GUI `server.js`, `config.example.json`; create `test/api.expressions.test.js`, `test/api.expressionsImport.test.js`. A focused filesystem helper `lib/expression-files.js` is permitted if needed to keep route/file safety logic independently testable; pure argument/classification logic stays in lib/expressions.js.

**Interfaces:** Use Task 2 exports. `GET /api/expressions?id=` returns `{groups:[{label,files:[{file,...sidecarEntry,stale}]}],labels:DEFAULT_EXPRESSION_LABELS,sidecar,job,importTarget:{directory,folderName,path,error}}`; default groups include empty labels, custom groups follow. `job` carries jobId/status/stage/log/error. `POST /api/expressions` accepts spec body plus id and returns job. Other routes and behavior are spec §5.1/5.3.

- [ ] Add stub-process API tests for lifecycle/progress/bounded log, malformed inputs, custom-only and configured argv, partial failure, cancellation followed by new job with stale old completion, mutual exclusion with animate and regeneration in both directions, itemView counts, exact-file redo, and safe delete with sidecar cleanup.
- [ ] Implement startExpressionJob and expressionJobsByItemId following animate pattern; guard child callbacks by jobId. Keep stdout stage and last 8000 log characters, retain partial output on error, integrate deleteItem cleanup and itemView `{hasExpressions,expressionCount,expressionStatus}`. Explicitly refuse sprite deletion while that NPC's expression job runs.
- [ ] Implement GET/list, POST/start, POST/cancel, GET/image, DELETE/file and POST/import. Image and delete accept only classified basenames without separators. Confirm resolved real files stay inside expressions directory, reject symlink escapes/directories, handle stream errors. Read sidecar leniently, write mutations atomically. Compare source mtime in milliseconds with current portrait for old-portrait status.
- [ ] Add `sillyTavernCharactersDir:''` defaults/example; empty setting and non-directory base return actionable errors. Reject empty names, separators and `..`; validate resolved destination containment including existing symlinks. Copy only classified files, count new and replaced separately, leave destination-only files untouched, return `{copied,replaced,path}`. Imports never run automatically.

```js
// Import fixture: source joy.webp and anger.webp; destination joy.webp and love.webp.
// POST {id,folderName:'Vex'} returns {copied:1,replaced:1,path:<base>/Vex}.
// love.webp survives. '../Vex', 'a/b', 'a\\b' and '..' all fail.
// GET image file='../joy.webp' never returns bytes from outside the sprite folder.
```

- [ ] Run focused API tests on distinct ports, then GUI suite once. Commit and record concrete endpoint response schema in report for Task 4.

### Task 4: NPC Expressions panel and integrated UI tests

**Files:** Modify GUI `public/index.html`, `public/app.js`, `public/style.css` (or actual existing stylesheet filename); create `test/ui.expressionsPanel.test.js` and extend polling tests where necessary.

**Interfaces:** Consume Task 3 API schema and itemView flags; implement `renderExpressionsPanel` and `refreshExpressions`. Receive default labels from server rather than defining a second list.

- [ ] Add tests matching existing UI harness for grid/order/empty slots, checkbox selection, All/None/Missing, multiple sanitized custom chips including table-only custom, count bounds, add/replace/background submission, Redo file payload, inline Delete confirmation, polling completion/stale responses and NPC-only capability visibility.
- [ ] Add panel next to Animated Portrait and 3D. Controls: 28 checkboxes; All/None/Missing only; custom label+prompt+Add+removable chips; variants 1-8; Add variants/Replace radios; Keep background off; Generate/Cancel; stage and collapsible log. Preserve unsent form choices across polling.
- [ ] Render ordered rows/thumbnails with empty slots and custom rows last; prompt+seed hover text, old-portrait badge, Redo and inline-confirm Delete. Escape user-controlled text and URLs. Button state tracks jobs and selection; stale async responses cannot replace another NPC's current panel.
- [ ] Integrate 2-second existing startPolling and refresh on completion/delete/redo. Track current item and jobId for late callbacks. Include expression jobs in running-job detection and do not discard selected custom text during refresh.
- [ ] Show editable SillyTavern folder defaulting to NPC name, target path/config error and explicit Import button; render copied/replaced counts and path. No CLI-only describe field.
- [ ] Run focused UI tests and relevant API smoke tests, then full suite once. Commit and report browser verification feasibility.

### Task 5: GUI documentation and cross-repository contract verification

**Files:** Modify GUI `README.md` and relevant existing usage docs if they describe capabilities/config; update generator docs only for concrete integration differences discovered.

- [ ] Document setup and path overrides, panel controls, custom label registration in SillyTavern, default transparency, rerun/replace/redo safety, old-portrait badge, tables-only Expressions editor and preset behavior, explicit copy counts/overwrite rules and required card-name folder match.
- [ ] Verify documented commands against actual CLI `--help`/dry-run and GUI config/path exports; ensure both sides agree on label order, filename rules, source mtime, configured manifest/tables and custom-only behavior. Add a focused regression only if this reveals a missing contract check.
- [ ] Run relevant documentation/static checks and report actual end-to-end limits (live GPU/model availability versus stub coverage). Commit docs using house style.

## Completion

Controller requests whole-branch Astra review across both repositories, routes any findings through one reviewed fix wave, runs final relevant verification, then merges each feature into its local main and verifies merged state. User has already authorized local merges and deletion of these feature worktrees/branches. Do not push main or delete unrelated worktrees. Preserve local config, output, and untracked user files.
