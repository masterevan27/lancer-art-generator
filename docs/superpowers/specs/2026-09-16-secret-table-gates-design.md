# Secret table gates: tables that only roll when an earlier pick opens them

**Date:** 2026-09-16
**Status:** approved (spec reviewed 2026-09-16; roll order panel added)
**Repositories:** `lancer-art-generator` (the format and the roll),
`lancer-npc-import-gui` (the Secret tables section of Create NPC and the
server-side check of a selection)

## 1. The problem

Secret mode's private tables (`--extra-tables`, the gitignored
`prompts/secret-tables/` folder) are flat: every enabled table rolls once and
its value is appended to the prompt. A collection that holds a list of men's
styles, a list of women's styles, and attribute tables for each has no way to
say "roll the men's attributes only when a man's style was picked". Today the
user either rolls both attribute tables and gets a contradictory prompt, or
unticks one by hand for every NPC.

The ask is a gate: a table that is used only when a value picked earlier opens
it, whether that value was fixed in the form or rolled.

## 2. What exists today

- `generate-npc.py` `load_extra_tables()` reads `.md` (through
  `parse_tables()` and `_markdown_extra_rows()`) and `.json` files into an
  ordered `{name: [(value, weight)]}`. `only` narrows it to the ticked tables,
  `values` narrows a table to the rows equal to a fixed value.
  `roll_extra()` then makes one `rng.choices` draw per table, after
  `roll_npc()`, so the base NPC for a seed never moves.
- A markdown bullet is taken whole: `||` flags and `=> Name` are literal text
  in a private file. The only structure is `###`, which the generator ignores
  and the GUI shows as `<optgroup>` categories.
- `lancer-npc-import-gui/lib/secretTables.js` mirrors that parse
  (`markdownTables`, `jsonTables`), lists the folder, and
  `validateSelection()` checks a Create request before `lib/kinds.js` turns it
  into `--extra-tables/--extra-table/--extra-value/--extra-target/--disable-table`.
- `public/secret-mode.js` `loadSecretTables()` draws one row per table:
  enable checkbox, value dropdown ("Random (weighted)" or a fixed value),
  Portrait/Token targets. Secret presets store those selections by table name
  and value text.
- No existing private file ends a bullet in `#word` or a heading in `(when:`,
  so the new syntax changes nothing for current files.

## 3. The format

### 3.1 Markdown

```markdown
## Styles
- x2 Rugged dockworker #man
- x1 Sharp-suited broker #man
- x2 Elegant courtesan #woman #noble

## Men's Attributes (when: man)
- x1 heavy stubble #scarred
- x1 broad shoulders

## Scars (when: scarred)
- x1 a burn scar across one cheek

## Jewellery (when: woman, noble)
- x1 a thin gold circlet
```

- **Tags.** One or more `#tag` tokens at the very end of a bullet, each
  preceded by whitespace, are that row's tags. A tag is
  `[A-Za-z0-9_-]+` and is compared case-insensitively (stored lower-case).
  Tags are stripped from the value: the prompt, the dropdown, `--extra-value`,
  presets and `extraTraits` all see `Rugged dockworker`. A `#` anywhere else
  (`a #3 jersey worn loose`) is text. The `xN` weight still comes first.
- **Gates.** A `##` heading ending in `(when: tag, tag)` is a gated table. The
  table's name is the heading with that suffix removed and trimmed
  (`Men's Attributes`); that name is what `--extra-table`, `--extra-value`,
  presets and the manifest use. The list is comma-separated and means *any*:
  the table opens when at least one picked value carries at least one listed
  tag. An empty list is an error.
- **Rows.** Two bullets with the same text and different tags are one row
  whose tags are the union, with their weights summed, so the "first
  appearance keeps its place" fold of `_markdown_extra_rows()` still holds.
- **Repeated headings.** A heading repeated with a different `(when:)` is an
  error; repeated with the same one (or none both times) merges as today.
- **Chains.** A gated table's rows may carry tags that open further tables.
- **Scope.** Tags are global across every loaded private file, so a styles
  file can open tables in an attributes file.
- `###` categories and `x0` rows behave as today.

### 3.2 JSON

For parity a JSON row may carry `"tags": ["man"]`, and a table may be written
as an object instead of a bare list:

```json
{
  "Styles": [{"value": "Rugged dockworker", "weight": 2, "tags": ["man"]}],
  "Men's Attributes": {"when": ["man"], "rows": [{"value": "heavy stubble"}]}
}
```

The bare-list form stays valid and means an ungated table. Tags and `when`
entries follow the same character rule as markdown.

### 3.3 Load-time validation (both parsers, same wording)

Load order is files in argument order, then tables in file order. The GUI
always sends files in its listing order (alphabetical).

**Generator** — the loaded set is refused, naming the file and table, when:

1. a `when:` tag is carried by rows of tables loaded *after* the gated table
   but by none loaded before it (a gate placed above its opener);
2. a tag or `when` entry breaks the character rule, or `when:` is empty;
3. a repeated heading disagrees about its `(when:)`.

A `when:` tag carried by no loaded table at all is **not** an error in the
generator: the file holding its opener may simply not be passed this run, and
that gated table just stays shut (a fixed value in it is refused by §4).

**GUI listing** — applies rules 1–3 across the whole folder in listing order,
and additionally refuses a `when:` tag that no table in the folder carries (a
misspelling); each tag in a multi-tag `(when:)` is checked individually, so a
gate opened by one correct tag is still refused over a misspelt sibling tag.
The error is attached to the file holding the gated table. This per-tag check
(and the whole-gate one it extends) is skipped while any file in the folder
has an error, since the tag it is missing might be inside that unreadable
file; the "comes before its opener" rule still runs regardless.

Loops cannot occur, because openers must come earlier in the order. A tag
that opens nothing is allowed (it may be for a future table). These checks run
before `only` narrows the set, so validity does not depend on which tables are
ticked.

## 4. Rolling (generator)

`load_extra_tables()` returns, per table, its rows as
`(value, weight, tags)` and its `when` set, still in load order.
`roll_extra()` walks that order keeping the set of *open tags*:

- An ungated table always rolls.
- A gated table rolls only when `when ∩ open_tags` is non-empty; otherwise it
  is skipped — no draw, no prompt text, no `extraTraits` entry.
- After a table rolls, the drawn row's tags join `open_tags`.

`only` (unticked tables) and `--disable-table` behave as before: an unticked
private table neither rolls nor opens anything. (`--disable-table` names
default tables only and is unaffected.)

**Fixed values in gated tables.** When the user fixes a value in a gated table
the gate must end up open, so before rolling, `load_extra_tables()` resolves
each such table's *requirement*:

1. If an earlier selected table is already narrowed (fixed) to rows that
   carry one of the `when` tags, the requirement is met.
2. Otherwise collect the *openers*: earlier selected, unfixed tables with at
   least one row carrying a `when` tag.
   - Exactly one opener: narrow it to its rows carrying a `when` tag. If that
     opener is itself gated, its own requirement is resolved the same way
     (recursively, earliest first).
   - None: refuse — `extra table 'Men's Attributes' has a fixed value but
     nothing selected can open it (when: man)`.
   - More than one: refuse — name them and ask for one to be fixed or
     unticked.
3. An earlier table fixed to a value without any `when` tag is not an opener.
   When it is the only table that could have opened the gate, the refusal
   in rule 2 names it: `extra table 'Men's Attributes' has a fixed value but
   'Styles' is fixed to 'Elegant courtesan', which is not #man`. When the
   opener was narrowed by another fixed gated table instead, the text is
   `... but 'Styles' is already limited to #woman by 'Women's Attributes'`.

Narrowing reuses the existing "fixed value narrows the row list" path, so
every selected table still makes exactly one draw when it rolls.

**Seeds.** Private tables still roll after `roll_npc()`, so the base NPC for a
seed is unchanged. A file that uses gates rolls its own tables differently
from today, because a skipped table makes no draw. Files without gates roll
exactly as today (pinned by a test).

**Regenerate** reuses `extraTraits` as today; a stored trait whose table is
now gated shut is simply reused (the stored picks are the record).

**Prompt preview.** The relabelling to `... if opened` is a GUI concern
(`secret-mode.js`, applied to the preview response, §5.2), not the
generator's `--prompt-preview` output itself. It applies only to a gated
table that rolls open on the preview's own sample seed; a table that stays
shut on that seed makes no draw and is simply absent from the sample rather
than appearing with a placeholder.

## 5. GUI

### 5.1 Parsing and listing (`lib/secretTables.js`)

`markdownTables` / `jsonTables` apply §3 exactly (same regexes, same
validation messages). A gated table in the list response gains
`when: string[]`, and a table with tagged rows gains `tags: {value: string[]}`;
`values` and `groups` stay plain strings, so dropdowns, presets and
`validateSelection`'s value check are unchanged. A file failing §3.3 is
listed with its error, as an unreadable file is today, and cannot be ticked.

The gate logic (tag/heading splitting, roll order, resolution and status
text) lives in one pure module, `public/secret-gates.js`, loaded by the page
and `require`d by `lib/secretTables.js`, so the form, the panel and the
server give the same answer.

### 5.2 Create NPC (`public/secret-mode.js`)

- A gated table keeps its place in its file (its openers always come
  earlier) and is indented by chain depth, with a small `when: #man` label.
- **Opener fixed:** gated tables whose `when` meets the fixed value's tags
  are active; the rest are greyed out (dropdown and targets disabled, the
  checkbox still usable, the selection kept but not sent) with a note, e.g.
  `closed — 'Styles' is fixed to 'Sharp-suited broker', which is not #woman`.
- **Opener Random:** gated tables keep their controls, with the note
  `rolls only if Styles rolls #man`. (Exact status texts are pinned by
  `test/secretGates.test.js`.)
- **Gated value fixed while its opener is Random:** the note becomes
  `Styles will be limited to #man values`. If §4's rules would refuse, the
  section shows that refusal, and Create reports the same refusal from the
  server (§5.3).
- A greyed-out (closed) gated table is closed only because nothing selected
  can open it — its openers are unticked, or the user fixed them to values
  without its tags. Such a table is left out of the request instead of being
  refused. A conflict created by narrowing (two fixed gated tables that need
  different values of the same opener) is always a refusal.
- The prompt preview relabels a gated table's random source as
  `Men's Attributes if opened` (in `secret-mode.js`, on the preview response).
- The dropdown for a table lists values without their tags; `###`
  categories are unchanged.

### 5.3 Server (`validateSelection`)

Runs the same resolution as §4 on the posted selection and refuses the same
cases with the same messages, so an impossible selection fails before the
generator starts. Gated tables that are greyed out are not sent.

### 5.4 Roll order panel

A collapsible `<details class="secret-roll-order">` titled **Roll order and
gates**, placed at the top of `#secret-tables-content` and closed by default.
It lists every table of every listed, readable file as one numbered list in
the order the generator will walk them (files in the order the GUI sends them
as `--extra-tables`, which must be the listed order; tables in file order).
Each entry shows:

- the table name and its file;
- its gate: `always`, or `when: man, noble — opened by Styles (#man),
  Nobility (#noble)` naming each earlier table with a row carrying one of
  the tags (and which tag);
- the tags its own rows can open, e.g. `can open: #man → Men's Attributes`;
- a live status from the current form, recomputed on every checkbox and
  dropdown change with the same resolution as §5.2:
  `not selected`, `rolls`, `rolls only if Styles rolls #man`,
  `closed — <reason>`, `rolls, limited to #man by 'Men's Attributes'`,
  `rolls; limits 'Styles' to #man`. An impossible selection is shown once,
  in the section's error line.

Gated entries are indented by chain depth so a chain reads as a tree inside
the ordered list. Whether the panel is open is remembered per viewer in
`localStorage` (read and written in `try/catch`; closed when unavailable).
The summary line carries a count, e.g. `Roll order and gates (7 tables,
3 gated)`, so it is useful while closed. A file with an error is listed as
one entry carrying the error.

### 5.5 Presets

No format change: presets store table names and value text, which do not
include tags or the `(when:)` suffix. A preset whose fixed values are now
contradictory is loaded, and the note from §5.2 explains the block.

## 6. Out of scope

- "All of" gates (`when: man + noble`).
- Opening gates from the default NPC tables (e.g. the rolled pronouns opening
  `(when: she)`). A natural follow-up.
- Gates or tags on the default tables file.

## 7. Testing

**Generator** (new `test/test_extra_table_gates.py`; the existing
`test/test_extra_tables.py` must pass unchanged):

- tags stripped from values; `#` mid-text kept; case folding;
- `(when:)` stripped from the name; `--extra-value` uses the bare name;
- open vs closed gated tables; any-of `when`; chains; cross-file gates;
- duplicate bullets with different tags merge;
- JSON `tags` and object-form tables;
- validation: gate above its opener, empty `when`, bad characters,
  conflicting repeated heading; a tag no loaded table carries leaves the
  gated table shut without an error;
- fixed gated value narrows a single Random opener (and recursively);
  refusals for no opener and several openers; opener fixed to the wrong tag;
- a file without gates rolls exactly as before for a pinned seed.

**GUI:**

- `test/secretTables.test.js`: the same parse and validation cases, and
  `validateSelection` resolution and refusals;
- `test/api.secretTables.test.js`: list response carries `when` and `tags`;
  create refuses an impossible selection;
- `test/ui.secretTables.test.js`: nesting, greyed-out gated tables, the
  Random/limited notes, and the roll order panel (order, gate text, live
  status, closed by default).

## 8. Docs

- `lancer-npc-import-gui/docs/secret-mode.md`, section "Secret tables and
  disabled default tables": tags, gates, the rules in §4, an example.
- `lancer-art-generator/README.md`, `--extra-tables` section: the same, briefly.
