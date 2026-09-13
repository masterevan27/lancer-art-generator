# Selectable Expression Sources and Poses Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Offer token/portrait source selection with a token-first default, and generate expression-appropriate full-body poses.

**Architecture:** The Python generator resolves the chosen original NPC image and its stored style prompt. The GUI exposes that choice and tracks each sprite against its actual source, including after Foundry relocation. Pose cues live with expression prompts; no new model or rendering workflow is needed.

**Tech Stack:** Python standard library/unittest; Node built-ins and browser JS/HTML/node:test; ComfyUI Qwen edit, RMBG, WebP.

**Spec:** Approved in chat: a selectable Full-body token / Portrait option in the Expressions panel and CLI; user explicitly chose token-first with portrait fallback and expressive poses. Source guides identity/outfit/style, not a fixed pose. Generate and Redo use the selected source. Existing sprites remain untouched until explicitly regenerated. Original portrait-only and fixed-standing language is superseded.

## Global Constraints

- Token-first is the default. When no source is explicitly selected, use an existing safe token, otherwise portrait. Explicit token or portrait selection must not silently fall back.
- Source choices are `token` and `portrait`. CLI `--source` is NPC-only; arbitrary `--image` continues to use exactly the supplied image.
- Every sprite edits the selected original image independently, never another sprite. Keep 768x1344 output and transparent default.
- Reuse only the chosen image's saved style wording (`tokenPrompt` or `portraitPrompt`); exclude old demeanor, pose, framing and backdrop. Unknown/missing prompt uses reference-only style guidance.
- Both sources produce full-body, emotion-appropriate poses. Preserve identity, outfit, accessories and source style. Do not lock the source pose or force standing for every expression.
- Preserve safe add/replace/exact-file redo, unknown authored saved prompts, custom labels, configured manifests/tables, and path containment. No automatic image/metadata migration.
- Preserve the GUI's recently added collapsed sprite section. No unrelated refactoring or dependencies. Update documentation and verify tests before local merges/cleanup; no push.

### Task 1: Generator source selection, source metadata and expressive prompts

**Worktree:** `G:/GIT-REPOS/lancer-art-generator/.claude/worktrees/expression-source-poses` (base `b9a768c`).

**Files:** Modify `generate-expressions.py`, `test/test_generate_expressions.py`, `prompts/expression-tables.md`, `docs/generate-expressions.md`, `README.md`. Include this plan in the task commit.

**Interfaces for GUI Task 2:**

```text
generate-expressions.py --id ID [--source token|portrait] ...
POST /api/expressions body gains optional source: "token" | "portrait"
sidecar sprite.source gains kind: "token" | "portrait" | "image"
existing source.path and source.mtime remain actual source absolute path and Unix milliseconds
```

- [ ] RED: exercise real temporary manifests and source images through parse_args/resolve_sources/main dry-run. Verify omitted source picks token when both exist, portrait when token is absent, explicit portrait wins, explicit missing token/portrait fails before render, invalid source and --image plus --source fail. Manifest filenames must be respected (`token`/`portrait`), with canonical `<safe name> Token.png`/`Portrait.png` compatibility when a field is absent. Reject path traversal, absolute manifest filenames outside the NPC folder, and outward symlinks/junctions. Image-mode explicit input remains unconstrained by NPC folders.
- [ ] RED: verify token prompt style selection versus portrait prompt, no pose/demeanor/framing leakage, actual sidecar source kind/path/mtime through execute_plans with real files, and compatibility with legacy source records. Update test expectations only where approved behavior changes; retain unknown-prompt fallback tests.
- [ ] RED: test prompt output removes fixed-standing/small-body-only restriction and requests emotion-specific full-body gestures/stance with head/hands/feet within margins. Test known legacy bust and prior full-body saved custom Redo updates framing/pose and selected-source style without dropping custom emotion/appearance anchors or duplicating guidance. Unknown authored saved prompts stay verbatim. Explicit --describe/custom pose instructions must remain intact.
- [ ] Run `python -m unittest discover -s test -p test_generate_expressions.py -q`; record expected behavior failures before implementation.
- [ ] Implement `--source` using argparse choices with omitted value distinguishable from explicit selection. Source dataclass gets a trailing defaulted `source_kind`; thread it to main's execute_plans so saved metadata records actual kind, not requested fallback mode. Keep existing helper callers compatible with optional parameters.

```python
source.add_argument("--source", choices=("token", "portrait"), default=None)
# Selection order:
kinds = (args.source,) if args.source else ("token", "portrait")
```

  Resolve existing filenames safely inside the real NPC folder; use manifest explicit filename when supplied rather than guessing a different file. A missing preferred token permits default fallback; an explicitly selected unavailable source raises an actionable error. Do not mask malformed/unsafe manifest paths as valid alternatives.
- [ ] Extend conservative style extraction for the known token template: opening `A full-body character illustration of ..., rendered in ... .`, closing style after `isolated character illustration, clean silhouette, painterly brushwork ... .`. Preserve those actual style words, excluding intervening stance/background and framing tag words. Keep existing portrait extraction behavior. Current generator templates can be inspected to establish delimiters but must not supply style text for an old NPC.
- [ ] Replace fixed standing/small-body-only prompt wording with natural expression-appropriate stance, shoulders, arms and hand gestures while keeping the face readable and entire body within frame. Extend every default expression-table bullet with a concise matching pose cue; preserve headings, weights, number of options, and label words. Examples: joy -> open welcoming arms; pride -> lifted chin and confident posture; sadness -> lowered shoulders and loosely clasped hands; fear -> guarded hands and recoiling weight shift. Custom expressions get general emotion-to-body-language guidance without an imposed default-label pose.
- [ ] Adapt recognized generated saved prompts during explicit Redo only: preserve the custom expression and appearance information, update obsolete framing/pose instructions and replace old source-style guidance with the newly selected source's style. Do not accumulate contradictory style blocks on repeated Redo. Unknown authored full prompts remain verbatim, documented as such.
- [ ] Update current docs/README with token-first fallback, explicit CLI choices, matching source style, full-body poses, metadata kind, and opt-in regeneration. Run focused tests and full suite once (`python -m unittest discover -s test -q`), diff check, self-review and commit. Report RED/GREEN commands/output, interfaces and concerns. Root owns live GPU renders; do not render yourself.

### Task 2: GUI selector, validation, stale checks and relocation

**Worktree:** `G:/GIT-REPOS/lancer-npc-import-gui/.claude/worktrees/expression-source-poses` (base `c21965d`).

**Files:** Modify `public/index.html`, `public/app.js`, `lib/expressions.js`, `lib/expression-files.js`, `server.js`, `README.md`; extend `test/expressions.test.js`, `test/api.expressions.test.js`, `test/api.expressionsFoundryImport.test.js`, `test/ui.expressionsPanel.test.js`. Add focused test utility/fixture code only as required by existing patterns.

**Consumes Task 1:** CLI `--source token|portrait`; missing source means token-first then portrait; explicit unavailable selection fails. New sidecar source.kind identifies actual `token`, `portrait`, or `image`; old absent kind means legacy portrait.

**Produces API additions:**

```json
{"sources":{"token":{"available":true},"portrait":{"available":true}},"defaultSource":"token"}
```

  These are additive fields on GET /api/expressions. Availability uses only safe, existing files inside the NPC folder. `defaultSource` is token when available, otherwise portrait; when neither exists both choices are disabled and generation reports no usable source. POST accepts optional `source` validated against exactly token/portrait; absent source follows CLI default.

- [ ] RED: pure argv/payload tests demonstrate selected source passes to CLI and invalid source is rejected. API tests using stub generator assert explicit token/portrait argv, omitted token-first fallback, token-only NPC can generate, missing/unsafe selected sources fail before spawn, and existing output-directory/symlink protections remain intact.
- [ ] RED: exercise UI selector through real renderer/handlers in existing VM harness. Initial source comes from available token-first default; missing options disabled; polling preserves unsent selection; switching NPC resets to its own default; running/starting jobs disable the select; Generate and Redo both send the current source. Keep collapsed sprite section and current form choices/error ownership behavior.
- [ ] RED: mixed-source sprite listing: token sprites compare against token mtime, portrait sprites against portrait mtime; changing the unselected source does not mark stale; deleting a known source marks its sprites stale; legacy records lacking kind remain portrait-based. Never read arbitrary source.path from sidecars. Cover missing/malformed metadata leniently without crashes.
- [ ] RED: Foundry relocation copies both source assets and expression sprites safely, updates source.path for each supported kind, keeps fresh sprites fresh and already-stale sprites stale, and supports legacy portrait records. Avoid treating token timestamps as portrait timestamps. Preserve existing running-job and junction guards.
- [ ] Run `node --test --test-concurrency=1 test/expressions.test.js test/api.expressions.test.js test/api.expressionsFoundryImport.test.js test/ui.expressionsPanel.test.js` and record RED before implementation.
- [ ] Add a source select in existing expression options row:

```html
<label>Source image
  <select id="expressions-source">
    <option value="token">Full-body token</option>
    <option value="portrait">Portrait</option>
  </select>
</label>
```

  Initialize availability/default only on a new NPC form, preserve selection on poll, and include `select` in running-state disabling. If selected asset disappears, disable rendering until a valid source is chosen; do not silently override an intentional choice on poll.
- [ ] Extend expressionJobPayload and expressionArgs to validate/forward source; include it in both Generate and Redo requests. Server resolves/validates the requested/default source before spawn, using consistent manifest filename behavior with CLI (canonical compatibility only for absent fields). Factor one focused helper if needed to avoid separate availability/preflight resolution rules drifting. No unsafe sidecar path reads.
- [ ] Resolve stale comparison via supported source.kind, falling back to portrait only for legacy absent kind. Invalid/image kinds must not induce filesystem reads from arbitrary paths. Change stale badge wording from `old portrait` to `old source image` and document the source selector.
- [ ] Generalize source timestamp rebasing on Foundry copy by kind. For finite original and copied timestamps, preserve each sprite's recorded timestamp delta so fresh and stale states survive copying; update the appropriate safe destination path while retaining kind and other metadata. Keep legacy behavior for missing/unknown metadata without corrupting entries.
- [ ] Update README with defaults, explicit selections/Redo, source-aware stale status and relocation. Run focused tests, full GUI suite once (`node --test --test-concurrency=1 --test-reporter=tap`), syntax/diff checks, self-review and commit. Root owns final cross-repo and browser verification; no subagents.
