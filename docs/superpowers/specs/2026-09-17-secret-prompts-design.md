---
type: "Design"
title: "Secret prompts: fill-in-the-blank NPC prompts for Secret mode"
description: "Design decisions and requirements for Secret prompts: fill-in-the-blank NPC prompts for Secret mode."
---
# Secret prompts: fill-in-the-blank NPC prompts for Secret mode

**Date:** 2026-09-17
**Status:** implemented and tested 2026-09-17; retained as design history. The
generator, GUI routes, Secret Create NPC controls, preview, presets, and
regeneration path are present on `main`. The unchecked implementation plan
below is historical; use the current code and tests as the source of truth.
**Repositories:** `lancer-art-generator` (file format, generator, content),
`lancer-npc-import-gui` (Secret Create NPC page, presets, gallery)

## 1. The problem

Secret mode can already roll private tables (`--extra-tables`), but every
rolled value is appended to the NPC's house prompt as one extra sentence after
the gear line. The house prompt describes a Lancer NPC in a fixed order, so a
private table about poses or framing lands at the end, reads as an
afterthought, and fights the sentences before it.

A *secret prompt* is a user-written template - a mad lib - whose blanks are
filled from the NPC's own rolled traits and from private tables, in whatever
order the author chose. It replaces the house portrait and token templates for
that NPC, and is only reachable in Secret mode.

Decisions taken during design:

- It runs through the existing Create NPC flow and keeps the NPC record,
  manifest entry, dossier and regeneration. Templates may use normal NPC
  trait values alongside private table values.
- Each template defines both images: a portrait template and a token
  template. The token template is the author's, including its white
  background wording.
- In the GUI a template is picked by name, or "Random from <file>" rolls one
  per NPC by weight. The choice is saved in presets and on the record.
- File format: a separate markdown file of templates (option A of three; JSON
  and templates-inside-table-files were rejected as harder to author and as
  mixing two formats).

## 2. File format

### 2.1 Location

Template files live in `prompts/secret-prompts/*.md`, gitignored exactly like
`prompts/secret-tables`. The GUI finds the folder through a
`secretPromptsDir` config key, defaulting to a `secret-prompts` sibling of the
secret tables folder.

### 2.2 Shape

```markdown
# Explicit prompts - v1
tables: explicit-table-3.md, lighting-atmosphere-1.md

## Kneeling solo portrait
weight: 2
pin: Pronouns = she/her

### portrait
A portrait of {npc:identity}, {secret:Subject Archetypes (Female)},
with {npc:hair} and {npc:eyes}. {npc:Subject} {npc:is_are}
{secret:Kneeling Poses}, {secret:Clothing States}.
{secret:Solo Framing}, {secret:Lighting Atmosphere}.

### token
A full-body figure of {npc:identity}, whole body in frame from head to
feet, {secret:Standing/Squatting Poses}, {secret:Clothing States}, against an
empty plain white background.
```

- A `# ` line is a title and is ignored.
- `tables:` (file level, before the first `##`, required if any template uses
  a `secret:` slot) is a comma-separated list of secret-tables files. Names
  resolve against the secret tables folder (`--secret-tables-dir`, default the
  `secret-tables` sibling of the prompts file's folder). A path that escapes
  that folder is refused.
- `## Name` opens a template. Names are nonblank and unique across every
  loaded file.
- Between `## Name` and its first `###`, optional metadata lines:
  - `weight: N` - positive number, default 1, used only by `random`.
  - `pin: Table = value` - repeatable. `Table` is any `REQUIRED_TABLES` name;
    `value` must be a bullet that table offers (flags stripped). Pins act as
    forced traits (section 3.3).
- `### portrait` and `### token` are both required, once each. Their text is
  every following nonblank line up to the next heading, joined with single
  spaces. Other `###` headings are an error.
- Anything else before the first `##` or in the metadata block is an error, so
  a typo is reported rather than silently ignored.

### 2.3 Slots

- `{npc:field}` - a value the generator computes for its own templates.
  Allowed fields: `Subject`, `subject`, `object`, `possessive`, `Possessive`,
  `is_are`, `wear`, `carry`, `identity`, `role`, `age`, `height`, `build`,
  `skin`, `hair`, `eyes`, `feature`, `outfit`, `headgear`, `demeanor`,
  `stance`, `backdrop`, `shot`, `name`.
- `{secret:Table Name}` - a row from a table in the file's `tables:` files.
  Each table referenced anywhere in a template rolls once per NPC, so the same
  table in portrait and token gives the same value. Tables a template does not
  reference are not rolled.
- `{{` and `}}` are literal braces. Any other `{...}` is an error.

### 2.4 Tidy-up after filling

Applied to each filled prompt, in order:

1. A value that begins a sentence (start of text, or after `. `, `! `, `? `)
   gets its first letter capitalised.
2. Runs of whitespace collapse to one space.
3. ` ,` and ` .` lose the space; `,.` becomes `.`; `..` becomes `.`.
4. The result is stripped and ends with a full stop if it ends in a letter.

Values are otherwise inserted verbatim.

### 2.5 Load errors

Every error names the file, the template (when there is one) and the line:
unknown `npc:` field, `secret:` table absent from the `tables:` files, missing
or repeated `### portrait` / `### token`, unknown `###`, unknown or unoffered
`pin:`, bad `weight`, duplicate template name across files, unreadable or
escaping `tables:` path, unbalanced braces, stray lines. A file with any error
loads nothing.

## 3. Generator (`lancer-art-generator`)

### 3.1 New module `secret_prompts.py`

Beside `art_styles.py` and `prompt_composer.py`. It owns parsing and
validation (`load(paths, tables_dir, npc_tables)`), selection
(`choose(templates, name, seed)`), filling (`fill(template, fields, extra)`),
tidy-up, and the listing JSON (`listing(...)`). `generate-npc.py` only wires it
in.

### 3.2 Flags

- `--secret-prompts PATH` (repeatable) - template files.
- `--secret-prompt NAME` - a template name, or `random`.
- `--secret-tables-dir DIR` - overrides where `tables:` resolves.
- `--list-secret-prompts` - prints the listing JSON (section 4.1) and exits.

`--secret-prompt` and `--secret-prompts` require `--secret` (refused like a
hidden art style otherwise) and each requires the other.
`--list-secret-prompts` requires `--secret-prompts`.

Refused alongside `--secret-prompt`, because the template decides what appears
and in what order: `--prompt-layout`, `--disable-table`, `--extra-tables`,
`--extra-table`, `--extra-target`. `--extra-value TABLE=VALUE` stays allowed
and pins a slot table's row.

### 3.3 Roll order

1. **Choose.** `random` draws from `random.Random("<seed>:secret-prompt")`,
   so templates never move the base NPC a seed rolls. A named template is
   looked up directly.
2. **Pin.** The template's pins merge into the roll overrides. A pin that
   disagrees with an explicit override (`--set-trait`, which GUI trait pickers and presets also
   use) is an error
   naming both values.
3. **Adults only.** While a secret prompt is active, `roll_npc` never picks an
   `Age` bullet flagged `young`, and a pin or override that asks for one is
   refused. This lives in code so no template can bypass it.
4. **Roll the NPC** as today.
5. **Roll slot tables.** `load_extra_tables` over the `tables:` files with
   `only` = the template's referenced tables, then `roll_extra`. Values go to
   `npc["_extra"]` and are saved as `extraTraits` as today;
   `npc["_extra_targets"]` stays empty.
6. **Build.** `build_prompts` fills the template's portrait and token text
   with the same field dict it builds for the house templates, instead of
   `PORTRAIT_TEMPLATE` / `TOKEN_TEMPLATE`. The art style is then applied as
   today (`apply_style`, adding `Art style: ...`); a selected non-house colour
   guidance sentence is appended; the house glow sentences are omitted.

### 3.4 Record

The manifest entry gains:

```json
"secretPrompt": {"file": "explicit-v1.md", "name": "Kneeling solo portrait",
                 "portrait": "<template text>", "token": "<template text>"}
```

The template text is a snapshot, so a regeneration reproduces the prompt even
if the file is edited or deleted; `file` and `name` are for display and
presets. `extra_record()` writes it; `npc_from_entry()` reads it back into
`npc["_secret_prompt"]`.

### 3.5 Regeneration and rerolls

`regenerate_one`, `--reroll-trait`, `--set-trait` and `--release` refill the
snapshot with the updated values. `--reroll-trait` additionally accepts the
name of a table the snapshot references, re-rolling just that slot and
persisting it to `extraTraits`; any other extra table name is refused. The
adults-only rule applies on these paths too. `--prompt-layout` stays refused
on regeneration.

### 3.6 Preview and dry run

`--prompt-preview` prints the usual `{"portrait": [...], "token": [...]}`.
With a template, each literal run is a `text:` part and each slot a part with
id `npc:<field>` or `secret:<table>`, carrying `sources` and `randomSources`
as today so the GUI can show `[Random value from Kneeling Poses]`. Parts from
a template are not reorderable (the GUI shows them read-only). `--dry-run`
prints the final prompts as today.

### 3.7 Tests

`test/test_secret_prompts.py`, loading the generator through
`test/helpers.py`:

- parsing: happy path, metadata, joined lines, literal braces;
- every load error in 2.5, each asserting the file/template/line message;
- filling and each tidy-up rule;
- pins, and the pin-versus-override conflict;
- the adults-only rule (roll, pin, override, reroll);
- `random` is weighted and reproducible per seed, and leaves the base NPC
  unchanged;
- only referenced tables roll;
- the record snapshot, and regeneration after the source file changes;
- slot reroll accepted for referenced tables, refused otherwise;
- refused flag combinations and the `--secret` requirement;
- `--list-secret-prompts` JSON, including a file with an error;
- `--prompt-preview` parts.

## 4. Import GUI (`lancer-npc-import-gui`)

### 4.1 Listing

`lib/paths.js` resolves `secretPromptsDir`. `lib/secretPrompts.js` runs
`generate-npc.py --secret --secret-config ... --list-secret-prompts
--secret-prompts <each file>` so there is one parser. The JSON:

```json
{"dir": "...", "files": [
  {"file": "explicit-v1.md",
   "templates": [{"name": "...", "weight": 2,
                  "pins": {"Pronouns": "she/her"},
                  "npcSlots": ["identity", "hair"],
                  "secretSlots": ["Kneeling Poses"]}]},
  {"file": "broken.md", "error": "broken.md, 'X', line 4: ..."}]}
```

`GET /api/secret/prompts` serves it, Secret mode only, like
`/api/secret/tables`. A file with an error is listed with its message and
cannot be selected.

### 4.2 Secret Create NPC page

- A "Secret prompt" select: **None** (default, today's behaviour), one
  **Random from <file>** per valid file, then each template grouped by file.
- With a template selected: the secret tables picker, the disable-table
  controls and the drag composer are hidden; a summary lists the pins and the
  slot tables; **Preview prompt** still works and shows the filled template
  read-only; trait pickers covered by a pin are locked to the pinned value.
- Back to None restores all of it unchanged.

### 4.3 Create, presets, gallery

- The create request carries `secretPrompt: {file, name}` (`name` may be
  `"random"`). The server checks that the file resolves inside
  `secretPromptsDir` and that the name exists (or the file is valid, for
  random), then `lib/kinds.js` adds `--secret-prompts <path> --secret-prompt
  <name>` and omits the refused flags.
- Secret presets save and restore `secretPrompt`.
- The gallery shows "Secret prompt: <name>" for records with `secretPrompt`,
  and the reroll trait list includes that template's slot tables.
  Regeneration needs no new arguments.
- `lib/version.js` is bumped per `AGENTS.md`.

### 4.4 Tests

- `test/secretPrompts.test.js` - listing, path containment, selection
  validation.
- `test/api.secretPrompts.test.js` - route, refused outside Secret mode.
- additions to `test/api.createArgs.test.js` and the secret preset tests -
  argument building, refused-flag omission, preset round trip.
- `test/ui.secretPrompts.test.js` - select hides/restores tables and
  composer, pins lock pickers, gallery label.
- the fake generator in `test/helpers` learns `--list-secret-prompts`.
- each new test file gets its own fixed port.

## 5. Content

### 5.1 `prompts/secret-tables/explicit-table-3.md`

A rewrite of `explict-table-2.md`, which is left untouched so existing
records and presets keep working.

- Every row is a lowercase fragment with no leading "She"/"Her" and no
  trailing full stop, so it reads mid-sentence.
- The nine pose groups become their own `##` tables (`Kneeling Poses`,
  `Lying Down Poses`, `Sitting/Reclining Poses`, `Cream/Dripping Poses`,
  `Ahegao Expression Poses`, `Anal Presentation Poses`, `Oral/BJ Ready Poses`,
  `Masturbation/Insertion Poses`, `Standing/Squatting Poses`).
- `Camera Angles & Framing` splits into `Solo Framing` and
  `Partnered Framing`.
- `Participant Configuration` is dropped; the template decides who is present.
- `Primary Sex Acts` and `Sex Positions` merge, deduplicated, into
  `Partnered Positions`.
- `Visibility Tags (Body Type)` becomes `Body Details`; the penis tags join
  the futanari tables; the feet/boots tags become `Foot Details`.
- `Bespoke Entire Scenes` stays as whole-scene rows.
- Every archetype row describes an adult ("early-twenties adult ...",
  "adult woman with a fresh girl-next-door look", "short, petite adult
  frame").

### 5.2 Prompt order

Every starter template follows: framing and subject (`{npc:identity}`) ->
body archetype and NPC looks (hair, eyes, skin) -> pose or action -> clothing
state -> partner, if any -> body details and fluids -> camera -> setting ->
lighting. Templates do not name a medium; the selected art style does.

### 5.3 `prompts/secret-prompts/explicit-v1.md`

`tables: explicit-table-3.md, lighting-atmosphere-1.md, setting-location-1.md`

Seven templates, each pinning `Pronouns = she/her`: Solo kneeling, Solo lying
down, Solo reclining, Solo self-pleasure, Couple scene (adds
`Male Partner Archetypes`, `Partnered Positions`, `Partnered Framing`),
Futanari solo, Bespoke scene.

Every token template is one figure, whole body from head to feet, on an empty
plain white background, using `Standing/Squatting Poses` and the clothing
state; no partner and no penetration, so it still cuts out as a map token.

### 5.4 Quality check

After implementation, dry-run each template across several seeds and read
the filled prompts for grammar and flow; the user then renders a sample in
ComfyUI and wording is tuned from the results.

## 6. Out of scope

- Reordering template fragments in the composer.
- Mixing ordinary appended extra tables with a template.
- Secret prompts for spaceships, backgrounds or expressions.
- The GUI's `--release-trait` / `--release` mismatch
  (`lib/secretGallery.js:169`), noticed during research; fixed separately.
