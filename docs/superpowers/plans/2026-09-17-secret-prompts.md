# Secret Prompts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a Secret-mode NPC be prompted from a user-written fill-in-the-blank template (`prompts/secret-prompts/*.md`) whose blanks are filled from the NPC's own rolled traits and from private tables, selectable by name or at random from the Secret Create NPC page, saved on the record and in presets, and regenerable.

**Architecture:** A new `secret_prompts.py` module beside `art_styles.py` owns the template file format (parse, validate, choose, fill, tidy, preview parts, listing JSON); `generate-npc.py` only wires it into flags, the roll loop, `build_prompts`, the manifest record and regeneration. The import GUI lists templates by running the generator's own `--list-secret-prompts` (one parser), adds a "Secret prompt" select to the Secret Create NPC page, passes `--secret-prompts PATH --secret-prompt NAME` on create, and shows the template on gallery cards. Content ships as two gitignored files written into the main checkout.

**Tech Stack:** Python 3 (`unittest`, `argparse`, `re`, `random`), Node 20+ (`node --test`, `node:vm`), vanilla browser JS, markdown table files.

**Spec:** `docs/superpowers/specs/2026-09-17-secret-prompts-design.md` (read it first; every task cites the section it implements).

## Global Constraints

- Template files live in `prompts/secret-prompts/*.md`, gitignored exactly like `prompts/secret-tables` (spec 2.1). Both folders are gitignored, so the content tasks write into the MAIN checkout `G:\GIT-REPOS\lancer-art-generator\prompts\...`, never into the worktree, and are never committed.
- Allowed `{npc:...}` fields, verbatim (spec 2.3): `Subject`, `subject`, `object`, `possessive`, `Possessive`, `is_are`, `wear`, `carry`, `identity`, `role`, `age`, `height`, `build`, `skin`, `hair`, `eyes`, `feature`, `outfit`, `headgear`, `demeanor`, `stance`, `backdrop`, `shot`, `name`.
- Every load error names the file, the template (when there is one) and the line: `"<file>, '<template>', line <n>: <problem>"` or `"<file>, line <n>: <problem>"`. A file with any error loads nothing (spec 2.5).
- `random` draws from `random.Random("<seed>:secret-prompt")` so the base NPC a seed rolls never moves (spec 3.3).
- While a secret prompt is active, no `Age` bullet flagged `young` can be rolled, pinned or forced; this is enforced in `roll_npc`, not in templates (spec 3.3 step 3).
- New generator flags: `--secret-prompts PATH` (repeatable), `--secret-prompt NAME`, `--secret-tables-dir DIR`, `--list-secret-prompts`. The first two require `--secret` and each other; the listing flag requires `--secret-prompts`. Refused beside `--secret-prompt`: `--prompt-layout`, `--disable-table`, `--extra-tables`, `--extra-table`, `--extra-target`. `--extra-value` stays allowed (spec 3.2).
- Manifest key `secretPrompt` = `{"file", "name", "portrait", "token"}` plus `"tables"` (absolute paths of the `tables:` files, added so a slot re-roll on regeneration needs no new arguments - spec 3.5 with 4.3). `extra_record()` writes it; `npc_from_entry()` reads it into `npc["_secret_prompt"]` (spec 3.4).
- GUI: config key `secretPromptsDir`, default the `secret-prompts` sibling of the secret tables folder; route `GET /api/secret/prompts`, Secret mode only; create body field `secretPrompt: {file, name}` with `name` possibly `"random"`; `lib/version.js` bumped from `1.1.2` to `1.2.0` (a large change per `AGENTS.md`); every new server test file gets its own fixed port - this plan uses **5433** (spec 4).
- Neither repo is pushed. Each repo's work ends fast-forward merged into local `main` with the worktree removed and the branch deleted (memory rule "merge-to-local-main-and-clean-up-worktree").
- Commit messages follow each repo's house style: one lowercase imperative sentence, no prefix, ending with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- The GUI's `--release-trait` / `--release` mismatch in `lib/secretGallery.js:169` is out of scope; do not touch it (spec 6).

---

## Repositories and worktrees

Generator work happens in the existing worktree `G:\GIT-REPOS\lancer-art-generator\.claude\worktrees\secret-prompts` on branch `secret-prompts` (already checked out; the spec is committed there as `35a9421`).

GUI work needs its own worktree. `G:\GIT-REPOS` is not a repository, so (memory rule "worktrees-in-multi-repo-workspace"):

```powershell
git -C G:\GIT-REPOS\lancer-npc-import-gui worktree add .claude\worktrees\secret-prompts -b secret-prompts
```

then `EnterWorktree` with `path: G:\GIT-REPOS\lancer-npc-import-gui\.claude\worktrees\secret-prompts` before the first GUI edit (Task 14). Run GUI tests from that worktree with `node --test test/<file>.test.js` per file (memory rule "gui-test-suite-port-flakes": create-presets/set-flag/table-bullets failures under the whole-suite run are pre-existing port collisions; run files alone).

Generator tests run from the generator worktree root: `python -m unittest test.test_secret_prompts -v`. Seven pre-existing failures in `test_scientists`, role-lock, import-flag and prompt-budget tests predate this work (memory rule "art-generator-preexisting-npc-test-failures"); confirm against `main` before blaming a task.

## File structure

**lancer-art-generator**

- Create `secret_prompts.py` - the whole template format: `tokens()`, `slots()`, `parse_file()`, `load()`, `listing()`, `choose()`, `merge_pins()`, `snapshot()`, `snapshot_secret_slots()`, `fill()`, `tidy()`, `parts()`. No import of `generate-npc.py`; the two things it needs from there (the extra-tables reader, the default tables dict) are passed in.
- Modify `prompt_composer.py` - extract the span-remapping loop of `_restyle()` into a public `reflow(parts, text)` so `secret_prompts.parts()` can map the tidied prompt back onto slot parts.
- Modify `generate-npc.py` - `parse_args` flags and refusals; `roll_npc(..., adults_only=False)`; `reroll_from_raw` passes it and keeps `_secret_prompt`; `build_prompts` template branch via new `_secret_prompt_build()`; `warn_token_limit()` extracted; `main()` loads templates, lists, chooses, pins, rolls slot tables, records; `regenerate_one()` slot re-roll; `extra_record`/`npc_from_entry`; `write_dossier` row; dry-run line.
- Modify `.gitignore` - add `prompts/secret-prompts`.
- Modify `README.md` - document the flags and the file format.
- Create `test/test_secret_prompts.py`.
- Content (main checkout, not committed): `prompts/secret-tables/explicit-table-3.md`, `prompts/secret-prompts/explicit-v1.md`.

**lancer-npc-import-gui**

- Modify `lib/paths.js` - `secretPromptsDir`.
- Create `lib/secretPrompts.js` - file-name check, generator-backed listing, selection validation, preset normalisation, `secretSlots()`.
- Modify `lib/kinds.js` - `createArgs` emits `--secret-prompts/--secret-prompt`, omits the refused flags.
- Modify `lib/secretPresets.js` - save/restore `secretPrompt`.
- Modify `lib/secretGallery.js` - `itemView` carries `secretPrompt` and slot tables in `rerollable`.
- Modify `server.js` - `GET /api/secret/prompts`; `handleCreateRequest(kind, body, runner, extras)`; secret `/create` and `/prompt-preview` resolve the selection; `/reroll-trait` accepts slot tables.
- Modify `public/prompt-composer.js` - `locked` option (read-only preview).
- Modify `public/app.js` - `override.locked` rows; locked rows excluded from the request body and preset settings.
- Modify `public/secret-mode.js`, `public/index.html`, `public/style.css` - the Secret prompt select, summary, pin locking, presets, gallery label, detail re-roll buttons for slots.
- Modify `lib/version.js` - `1.2.0`.
- Create `test/helpers/secretPromptsStub.js`, `test/secretPrompts.test.js`, `test/api.secretPrompts.test.js`, `test/ui.secretPrompts.test.js`; add cases to `test/kinds.test.js`, `test/paths.test.js`, `test/api.createArgs.test.js`.

---

## Part A - generator (`lancer-art-generator`, worktree `secret-prompts`)

### Task 1: `prompt_composer.reflow()` - span remapping as a public helper

**Files:**
- Modify: `prompt_composer.py:70-112`
- Test: `test/test_prompt_composer.py` (append one test)

**Interfaces:**
- Produces: `prompt_composer.reflow(parts, text) -> list[part]` - the same parts with their `prefix`/`value`/`suffix`/`text` rewritten so that `''.join(p['text'] for p in result) == text`, empty parts dropped, a part whose value vanished getting `sources=[]`. `_restyle()` keeps its behaviour and signature.

- [ ] **Step 1: Write the failing test**

Append to `test/test_prompt_composer.py`, inside the existing test class (it has `gen = load_generator()` at module level; add `import prompt_composer` at the top of the file if it is not imported already):

```python
    def test_reflow_maps_an_edited_string_back_onto_its_parts(self):
        import prompt_composer
        parts = [prompt_composer._part('text:0', 'a  portrait of '),
                 prompt_composer._part('npc:hair', 'red  hair', ['Hair']),
                 prompt_composer._part('text:2', ' , here')]
        moved = prompt_composer.reflow(parts, 'a portrait of red hair, here.')
        self.assertEqual(''.join(p['text'] for p in moved), 'a portrait of red hair, here.')
        self.assertEqual([p['id'] for p in moved], ['text:0', 'npc:hair', 'text:2'])
        self.assertEqual(moved[1]['value'], 'red hair')
        self.assertEqual(moved[1]['sources'], ['Hair'])
        self.assertIs(prompt_composer.reflow(parts, ''.join(p['text'] for p in parts)), parts)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m unittest test.test_prompt_composer -v -k reflow`
Expected: FAIL with `AttributeError: module 'prompt_composer' has no attribute 'reflow'`.

- [ ] **Step 3: Extract `reflow` from `_restyle`**

Replace the body of `_restyle` in `prompt_composer.py` from `owners = []` down to `return result` with a call, and add `reflow` above it:

```python
def reflow(parts, text):
    """The same parts, re-spanned so their texts join to exactly `text`.

    Character-level diff between the parts' current join and `text`; equal
    runs stay with the part that owned them, replaced or inserted runs go to
    the part owning the character they replace. Used by _restyle() for an
    art style's whole-prompt edits and by secret_prompts.parts() for the
    tidy-up a filled template gets, so a preview's fragments always join to
    the prompt the generator will render.
    """
    original = ''.join(part['text'] for part in parts)
    if text == original:
        return parts
    owners = []
    buffers = [{key: [] for key in ('prefix', 'value', 'suffix')} for _ in parts]
    for index, part in enumerate(parts):
        for key in ('prefix', 'value', 'suffix'):
            owners.extend([(index, key)] * len(part[key]))
    for operation, left, right, start, end in SequenceMatcher(None, original, text, autojunk=False).get_opcodes():
        if operation == 'equal':
            for offset, char in enumerate(text[start:end]):
                index, key = owners[left + offset]
                buffers[index][key].append(char)
        elif operation in ('replace', 'insert') and owners:
            index, key = owners[min(left, len(owners) - 1)]
            buffers[index][key].append(text[start:end])
    result = []
    for part, buffer in zip(parts, buffers):
        value = {key: ''.join(chars) for key, chars in buffer.items()}
        updated = dict(part, **value)
        updated['text'] = value['prefix'] + value['value'] + value['suffix']
        if updated['text']:
            if not updated['value']:
                updated['sources'] = []
            result.append(updated)
    return result


def _restyle(parts, style):
    """Apply the existing whole-prompt style rules, preserving span ownership."""
    original = ''.join(part['text'] for part in parts)
    styled = art_styles.apply_style(original, style)
    if styled == original:
        return parts
    tail = ''
    if style and style.get('id') != 'default' and style.get('prompt', '').strip():
        tail = '\nArt style: ' + style['prompt'].strip()
        if styled.endswith(tail):
            styled = styled[:-len(tail)]
        else:
            tail = ''
    result = reflow(parts, styled)
    if tail:
        result.append(_part('style:suffix', tail))
    return result
```

- [ ] **Step 4: Run the composer tests**

Run: `python -m unittest test.test_prompt_composer -v`
Expected: every test passes, including the new one (the old `_restyle` behaviour is byte-identical - `test_fragments_match_styles_and_disabled_tables` pins it).

- [ ] **Step 5: Commit**

```bash
git add prompt_composer.py test/test_prompt_composer.py
git commit -m "expose the composer's span remapping as reflow" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: `secret_prompts.py` - tokens, slots and file parsing

**Files:**
- Create: `secret_prompts.py`
- Create: `test/test_secret_prompts.py`

**Interfaces:**
- Produces:
  - `secret_prompts.NPC_FIELDS: tuple[str]` (the spec 2.3 list), `secret_prompts.NPC_SOURCES: dict[field -> tuple[table names]]`.
  - `tokens(text) -> list[(kind, value)]` with `kind in ('text', 'npc', 'secret')`; raises `ValueError` on a stray or unknown brace.
  - `slots(text) -> (npc_slots: list[str], secret_slots: list[str])`, ordered, deduplicated.
  - `parse_file(path) -> (tables: list[str], tables_line: int, templates: list[dict])`. Each template dict: `name`, `file` (basename), `line` (its `##` line), `weight` (float, default 1.0), `pin_text` (`{table: value-as-written}`), `portrait`, `token` (joined text), `npc_slots`, `secret_slots`, `slot_lines` (`{slot name: line}` for error messages). Purely syntactic checks; raises `ValueError` with the file/template/line message.
  - `_error(path, template, line, message) -> ValueError`.

- [ ] **Step 1: Write the failing tests**

Create `test/test_secret_prompts.py`:

```python
"""Secret prompts: fill-in-the-blank templates for Secret-mode NPCs.

The file format (spec 2), the generator wiring (spec 3) and the content
rules are tested here; the module under test is secret_prompts.py, loaded
as an ordinary import, and generate-npc.py through test.helpers.
"""
import contextlib
import io
import json
import random
import tempfile
import unittest
from pathlib import Path

import secret_prompts as sp
from test.helpers import FIXTURE_TABLES, load_generator, manifest_entry

gen = load_generator()
TABLES = gen.parse_tables(FIXTURE_TABLES)

TABLES_MD = """## Poses

- x2 kneeling upright with knees spread
- lying on her back with legs raised

## Clothing

- completely nude

## Lighting

- soft candlelight
"""

PROMPTS_MD = """# Test prompts
tables: tables.md

## Kneeling
weight: 3
pin: Pronouns = she/her

### portrait
A portrait of {npc:identity}, with {npc:hair}.
{npc:Subject} {npc:is_are} {secret:Poses}, {secret:Clothing}.
{secret:Lighting}.

### token
A full-body figure of {npc:identity}, {secret:Poses}, {secret:Clothing},
against an empty plain white background.

## Plain

### portrait
{{Literal}} braces and {npc:name}

### token
Token of {npc:name}.
"""


class Workspace:
    """A temp folder shaped like prompts/: secret-tables/ beside secret-prompts/."""

    def __init__(self, case, prompts=PROMPTS_MD, tables=TABLES_MD):
        self.tmp = tempfile.TemporaryDirectory()
        case.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.tables_dir = self.root / "secret-tables"
        self.prompts_dir = self.root / "secret-prompts"
        self.tables_dir.mkdir()
        self.prompts_dir.mkdir()
        self.tables = self.write_tables("tables.md", tables)
        self.prompts = self.write_prompts("x.md", prompts)
        self.config = self.root / "config.json"
        self.config.write_text(json.dumps({"secretImagesDir": str(self.root / "private")}), encoding="utf-8")

    def write_tables(self, name, text):
        path = self.tables_dir / name
        path.write_text(text, encoding="utf-8")
        return path

    def write_prompts(self, name, text):
        path = self.prompts_dir / name
        path.write_text(text, encoding="utf-8")
        return path

    def load(self, *paths):
        return sp.load(list(paths) or [self.prompts], None, TABLES, gen.REQUIRED_TABLES, gen.load_extra_tables)


class TestTokens(unittest.TestCase):
    def test_literal_text_and_both_slot_kinds(self):
        self.assertEqual(sp.tokens("A {npc:hair} and {secret:Poses}!"),
                         [("text", "A "), ("npc", "hair"), ("text", " and "), ("secret", "Poses"), ("text", "!")])

    def test_doubled_braces_are_literal(self):
        self.assertEqual(sp.tokens("{{x}} {npc:name}"), [("text", "{x} "), ("npc", "name")])

    def test_names_are_stripped(self):
        self.assertEqual(sp.tokens("{secret: Kneeling Poses }"), [("secret", "Kneeling Poses")])

    def test_stray_and_unknown_braces_are_errors(self):
        for bad in ("a { b", "a } b", "{foo}", "{npc:}", "{secret:x", "{npc:{secret:y}}"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                sp.tokens(bad)

    def test_slots_are_ordered_and_unique(self):
        self.assertEqual(sp.slots("{secret:B} {npc:hair} {secret:A} {secret:B} {npc:hair}"),
                         (["hair"], ["B", "A"]))


class TestParseFile(unittest.TestCase):
    def test_happy_path(self):
        ws = Workspace(self)
        tables, line, templates = sp.parse_file(ws.prompts)
        self.assertEqual(tables, ["tables.md"])
        self.assertEqual(line, 2)
        self.assertEqual([t["name"] for t in templates], ["Kneeling", "Plain"])
        kneeling, plain = templates
        self.assertEqual(kneeling["weight"], 3.0)
        self.assertEqual(kneeling["pin_text"], {"Pronouns": "she/her"})
        self.assertEqual(kneeling["line"], 4)
        self.assertEqual(kneeling["file"], "x.md")
        self.assertEqual(kneeling["secret_slots"], ["Poses", "Clothing", "Lighting"])
        self.assertEqual(kneeling["npc_slots"], ["identity", "hair", "Subject", "is_are"])
        self.assertEqual(plain["weight"], 1.0)
        self.assertEqual(plain["pin_text"], {})
        self.assertEqual(plain["portrait"], "{{Literal}} braces and {npc:name}")

    def test_lines_join_with_single_spaces(self):
        ws = Workspace(self)
        kneeling = sp.parse_file(ws.prompts)[2][0]
        self.assertEqual(kneeling["portrait"],
                         "A portrait of {npc:identity}, with {npc:hair}. "
                         "{npc:Subject} {npc:is_are} {secret:Poses}, {secret:Clothing}. {secret:Lighting}.")
        self.assertEqual(kneeling["token"],
                         "A full-body figure of {npc:identity}, {secret:Poses}, {secret:Clothing}, "
                         "against an empty plain white background.")

    def test_slot_lines_are_recorded_for_error_messages(self):
        ws = Workspace(self)
        kneeling = sp.parse_file(ws.prompts)[2][0]
        self.assertEqual(kneeling["slot_lines"]["Lighting"], 11)
        self.assertEqual(kneeling["slot_lines"]["hair"], 9)

    def assertError(self, text, pattern, name="bad.md"):
        ws = Workspace(self)
        path = ws.write_prompts(name, text)
        with self.assertRaisesRegex(ValueError, pattern):
            sp.parse_file(path)

    def test_every_syntax_error_names_file_template_and_line(self):
        cases = [
            ("stray line\n## A\n### portrait\nx\n### token\ny\n", r"^bad\.md, line 1: "),
            ("## A\nnonsense\n### portrait\nx\n### token\ny\n", r"^bad\.md, 'A', line 2: "),
            ("## A\nweight: nope\n### portrait\nx\n### token\ny\n", r"^bad\.md, 'A', line 2: .*weight"),
            ("## A\nweight: 0\n### portrait\nx\n### token\ny\n", r"^bad\.md, 'A', line 2: .*weight"),
            ("## A\nweight: 1\nweight: 2\n### portrait\nx\n### token\ny\n", r"^bad\.md, 'A', line 3: .*weight"),
            ("## A\npin: nonsense\n### portrait\nx\n### token\ny\n", r"^bad\.md, 'A', line 2: .*pin"),
            ("## A\npin: Age = a\npin: Age = b\n### portrait\nx\n### token\ny\n", r"^bad\.md, 'A', line 3: .*Age"),
            ("## A\n### portrait\nx\n", r"^bad\.md, 'A', line 1: .*token"),
            ("## A\n### token\nx\n", r"^bad\.md, 'A', line 1: .*portrait"),
            ("## A\n### portrait\nx\n### portrait\ny\n### token\nz\n", r"^bad\.md, 'A', line 4: .*portrait"),
            ("## A\n### portrait\nx\n### token\ny\n### other\nz\n", r"^bad\.md, 'A', line 6: .*other"),
            ("## A\n### portrait\na { b\n### token\ny\n", r"^bad\.md, 'A', line 3: .*brace"),
            ("## A\n### portrait\n{foo}\n### token\ny\n", r"^bad\.md, 'A', line 3: .*\{foo\}"),
            ("## A\n### portrait\n{npc:nope}\n### token\ny\n", r"^bad\.md, 'A', line 3: .*npc:nope"),
            ("## A\n### portrait\nx\n### token\ny\n## A\n### portrait\nx\n### token\ny\n", r"^bad\.md, 'A', line 6: .*already"),
            ("##   \n### portrait\nx\n### token\ny\n", r"^bad\.md, line 1: .*name"),
            ("tables: a.md\ntables: b.md\n## A\n### portrait\nx\n### token\ny\n", r"^bad\.md, line 2: .*tables"),
            ("## A\ntables: a.md\n### portrait\nx\n### token\ny\n", r"^bad\.md, 'A', line 2: "),
            ("## A\n### portrait\n\n### token\ny\n", r"^bad\.md, 'A', line 2: .*empty"),
        ]
        for text, pattern in cases:
            with self.subTest(text=text):
                self.assertError(text, pattern)

    def test_a_title_line_is_ignored_anywhere(self):
        ws = Workspace(self)
        path = ws.write_prompts("t.md", "# Title\n## A\n# another title\n### portrait\nx\n### token\ny\n")
        self.assertEqual(sp.parse_file(path)[2][0]["portrait"], "x")

    def test_a_file_with_no_templates_is_an_error(self):
        self.assertError("# Just a title\n", r"^bad\.md, line 1: .*no templates")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m unittest test.test_secret_prompts -v`
Expected: `ModuleNotFoundError: No module named 'secret_prompts'`.

- [ ] **Step 3: Create `secret_prompts.py` with the parser**

```python
"""Secret prompts: fill-in-the-blank NPC prompt templates for Secret mode.

A template file is markdown: '## Name' opens a template, optional 'weight:'
and 'pin:' lines follow, then '### portrait' and '### token' each hold the
text of one image prompt with '{npc:field}' and '{secret:Table}' slots. See
docs/superpowers/specs/2026-09-17-secret-prompts-design.md section 2.

This module owns the format end to end - parsing, validation, selection,
filling, tidy-up, the preview fragments and the listing JSON the import GUI
reads - and knows nothing of generate-npc.py: the two things it needs from
there (the extra-tables reader and the parsed default tables) are handed in.
"""
import random
import re
from pathlib import Path

# The fields a template may read off the rolled NPC, and which default
# tables each one comes from (for the preview's '[Random value from ...]').
PRONOUN_FIELDS = ("Subject", "subject", "object", "possessive", "Possessive",
                  "is_are", "wear", "carry")
NPC_SOURCES = {
    "identity": ("Role", "Age", "Pronouns"),
    "role": ("Role",), "age": ("Age",), "height": ("Height",), "build": ("Build",),
    "skin": ("Skin",), "hair": ("Hair", "Hair colour"), "eyes": ("Eyes",),
    "feature": ("Feature",), "outfit": ("Outfit",), "headgear": ("Headgear",),
    "demeanor": ("Demeanor",), "stance": ("Stance",), "backdrop": ("Backdrop",),
    "shot": ("Backdrop",), "name": ("Given names", "Family names"),
}
NPC_SOURCES.update({field: ("Pronouns",) for field in PRONOUN_FIELDS})
NPC_FIELDS = PRONOUN_FIELDS + tuple(f for f in NPC_SOURCES if f not in PRONOUN_FIELDS)

_SLOT = re.compile(r"\{\{|\}\}|\{(npc|secret):([^{}]*)\}|\{[^{}]*\}|[{}]")


def _error(path, template, line, message):
    where = "%s, '%s', line %d" % (Path(path).name, template, line) if template \
        else "%s, line %d" % (Path(path).name, line)
    return ValueError("%s: %s" % (where, message))


def tokens(text):
    """[(kind, value)]: 'text' runs, 'npc' fields and 'secret' table names.

    '{{' and '}}' are literal braces; any other brace is an error, so a typo
    like '{npc hair}' is reported rather than shipped to the image model.
    """
    out, pos = [], 0

    def emit(kind, value):
        if kind == "text" and out and out[-1][0] == "text":
            out[-1] = ("text", out[-1][1] + value)
        elif value or kind != "text":
            out.append((kind, value))

    for match in _SLOT.finditer(text):
        emit("text", text[pos:match.start()])
        token = match.group()
        if token == "{{":
            emit("text", "{")
        elif token == "}}":
            emit("text", "}")
        elif match.group(1):
            name = match.group(2).strip()
            if not name:
                raise ValueError("empty %s slot" % match.group(1))
            emit(match.group(1), name)
        elif token in "{}":
            raise ValueError("unbalanced brace near %r" % text[max(0, match.start() - 12):match.end() + 12])
        else:
            raise ValueError("unknown slot %s (use {npc:field}, {secret:Table} or {{ for a brace)" % token)
        pos = match.end()
    emit("text", text[pos:])
    return out


def slots(text):
    """The ordered, deduplicated (npc fields, secret tables) a text reads."""
    npc, secret = [], []
    for kind, value in tokens(text):
        target = npc if kind == "npc" else secret if kind == "secret" else None
        if target is not None and value not in target:
            target.append(value)
    return npc, secret


_HEADING = re.compile(r"^(#{1,3})\s+(.*?)\s*$")


def parse_file(path):
    """(tables list, tables line, templates) from one file, checking syntax only.

    Everything a file can get wrong on its own is reported here with the
    file, the template and the line; what needs the tables or the default
    tables (a secret slot naming no table, a pin the table does not offer)
    is checked by load().
    """
    path = Path(path)
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        raise ValueError("%s: cannot read the secret prompts file: %s" % (path.name, exc))
    tables, tables_line = None, 0
    templates, current, section = [], None, None

    def finish(template):
        if template is None:
            return
        for target in ("portrait", "token"):
            if template[target] is None:
                raise _error(path, template["name"], template["line"], "missing a '### %s' section" % target)
        for target in ("portrait", "token"):
            template[target] = " ".join(text for _, text in template[target])
        npc_slots, secret_slots, slot_lines = [], [], {}
        for target in ("portrait", "token"):
            for line_no, text in template["_lines"][target]:
                try:
                    line_npc, line_secret = slots(text)
                except ValueError as exc:
                    raise _error(path, template["name"], line_no, str(exc))
                for field in line_npc:
                    if field not in NPC_FIELDS:
                        raise _error(path, template["name"], line_no,
                                     "unknown field {npc:%s}; fields: %s" % (field, ", ".join(NPC_FIELDS)))
                    if field not in npc_slots:
                        npc_slots.append(field)
                    slot_lines.setdefault(field, line_no)
                for table in line_secret:
                    if table not in secret_slots:
                        secret_slots.append(table)
                    slot_lines.setdefault(table, line_no)
        template["npc_slots"], template["secret_slots"], template["slot_lines"] = npc_slots, secret_slots, slot_lines
        del template["_lines"]
        templates.append(template)

    for number, raw in enumerate(lines, 1):
        line = raw.rstrip()
        if not line.strip():
            continue
        heading = _HEADING.match(line)
        if heading and heading.group(1) == "#":
            continue
        if heading and heading.group(1) == "##":
            finish(current)
            name = heading.group(2)
            if not name:
                raise _error(path, None, number, "a template needs a name after '## '")
            if any(t["name"] == name for t in templates):
                raise _error(path, name, number, "template name already used in this file")
            current = {"name": name, "file": path.name, "line": number, "weight": 1.0, "pin_text": {},
                       "portrait": None, "token": None, "_lines": {"portrait": [], "token": []},
                       "_weight_line": None}
            section = None
            continue
        if heading and heading.group(1) == "###":
            if current is None:
                raise _error(path, None, number, "'### %s' before any '## Name'" % heading.group(2))
            target = heading.group(2).strip().lower()
            if target not in ("portrait", "token"):
                raise _error(path, current["name"], number,
                             "unknown section '### %s'; only portrait and token" % heading.group(2))
            if current[target] is not None:
                raise _error(path, current["name"], number, "a second '### %s' section" % target)
            current[target] = current["_lines"][target]
            section = target
            continue
        if current is None:
            key, _, value = line.partition(":")
            if key.strip() == "tables" and _:
                if tables is not None:
                    raise _error(path, None, number, "a second 'tables:' line")
                tables = [name.strip() for name in value.split(",") if name.strip()]
                tables_line = number
                continue
            raise _error(path, None, number, "stray line before the first '## Name': %r" % line.strip())
        if section is None:
            key, sep, value = line.partition(":")
            key, value = key.strip(), value.strip()
            if sep and key == "weight":
                if current["_weight_line"] is not None:
                    raise _error(path, current["name"], number, "a second 'weight:' line")
                try:
                    weight = float(value)
                except ValueError:
                    weight = 0.0
                if not weight > 0:
                    raise _error(path, current["name"], number, "weight must be a positive number, not %r" % value)
                current["weight"], current["_weight_line"] = weight, number
                continue
            if sep and key == "pin":
                table, eq, pinned = value.partition("=")
                table, pinned = table.strip(), pinned.strip()
                if not eq or not table or not pinned:
                    raise _error(path, current["name"], number, "pin must read 'pin: Table = value', not %r" % value)
                if table in current["pin_text"]:
                    raise _error(path, current["name"], number, "%s is pinned twice" % table)
                current["pin_text"][table] = pinned
                continue
            raise _error(path, current["name"], number,
                         "unexpected line between '## %s' and its first '###': %r" % (current["name"], line.strip()))
        current["_lines"][section].append((number, line.strip()))

    finish(current)
    for template in templates:
        for target in ("portrait", "token"):
            if not template[target].strip():
                raise _error(path, template["name"], template["line"] + 1, "the %s section is empty" % target)
        del template["_weight_line"]
    if not templates:
        raise _error(path, None, max(1, len(lines)), "no templates ('## Name') in this file")
    return tables or [], tables_line, templates
```

Note the empty-section check uses `template["line"] + 1` only as a fallback; to satisfy the test's `line 2` expectation for `"## A\n### portrait\n\n### token\ny\n"`, record the `###` heading line instead: store `current["_section_lines"] = {}` when a template opens, set `current["_section_lines"][target] = number` when a `###` is seen, and use `template["_section_lines"][target]` in the empty check (then delete the key alongside `_weight_line`).

- [ ] **Step 4: Run the tests**

Run: `python -m unittest test.test_secret_prompts -v`
Expected: all `TestTokens` and `TestParseFile` cases pass. If a `subTest` in `test_every_syntax_error_names_file_template_and_line` fails on its line number, fix the number the parser reports - the test encodes the spec's "names the line" promise, not the other way round.

- [ ] **Step 5: Commit**

```bash
git add secret_prompts.py test/test_secret_prompts.py
git commit -m "parse secret prompt template files" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: `secret_prompts.load()` and `listing()` - context checks

**Files:**
- Modify: `secret_prompts.py`
- Test: `test/test_secret_prompts.py`

**Interfaces:**
- Consumes: `parse_file()` (Task 2); the generator's `load_extra_tables(paths, only=None, values=None)` and `parse_tables()` output passed in by the caller.
- Produces:
  - `load(paths, tables_dir, npc_tables, required, read_tables) -> dict[name -> template]` in file order. Adds to each template: `path` (resolved `Path` of the prompts file), `tables` (list of resolved absolute path strings of the `tables:` files), `pins` (`{table: raw bullet with flags}`, the value handed to `roll_npc` overrides). `tables_dir=None` means `<prompts file's folder>/../secret-tables`. Raises `ValueError` with the file/template/line message on any of spec 2.5's errors.
  - `listing(paths, tables_dir, npc_tables, required, read_tables) -> dict` in the spec 4.1 JSON shape (`pins` there is `pin_text`).
  - `_core(bullet) -> str` (text before `||`, stripped).

- [ ] **Step 1: Write the failing tests**

Append to `test/test_secret_prompts.py` before `if __name__`:

```python
class TestLoad(unittest.TestCase):
    def test_happy_path_resolves_tables_and_pins(self):
        ws = Workspace(self)
        templates = ws.load()
        self.assertEqual(list(templates), ["Kneeling", "Plain"])
        kneeling = templates["Kneeling"]
        self.assertEqual(kneeling["tables"], [str(ws.tables.resolve())])
        self.assertEqual(kneeling["pins"], {"Pronouns": "she/her/her/woman"})
        self.assertEqual(kneeling["path"], ws.prompts.resolve())

    def test_tables_dir_override_and_default(self):
        ws = Workspace(self)
        elsewhere = ws.root / "elsewhere"
        elsewhere.mkdir()
        (elsewhere / "tables.md").write_text(TABLES_MD, encoding="utf-8")
        templates = sp.load([ws.prompts], elsewhere, TABLES, gen.REQUIRED_TABLES, gen.load_extra_tables)
        self.assertEqual(templates["Kneeling"]["tables"], [str((elsewhere / "tables.md").resolve())])

    def test_a_pin_resolves_to_the_raw_bullet_with_its_flags(self):
        ws = Workspace(self)
        path = ws.write_prompts("p.md", "## A\npin: Build = full-figured through the hips\n"
                                        "### portrait\nx\n### token\ny\n")
        self.assertEqual(sp.load([path], None, TABLES, gen.REQUIRED_TABLES, gen.load_extra_tables)["A"]["pins"],
                         {"Build": "full-figured through the hips || figure"})

    def assertLoadError(self, ws, text, pattern, name="bad.md", tables_dir=None):
        path = ws.write_prompts(name, text)
        with self.assertRaisesRegex(ValueError, pattern):
            sp.load([path], tables_dir, TABLES, gen.REQUIRED_TABLES, gen.load_extra_tables)

    def test_context_errors_name_file_template_and_line(self):
        ws = Workspace(self)
        ok = "### portrait\nx\n### token\ny\n"
        cases = [
            ("tables: tables.md\n## A\n### portrait\n{secret:Nope}\n### token\ny\n", r"^bad\.md, 'A', line 4: .*Nope"),
            ("## A\n### portrait\n{secret:Poses}\n### token\ny\n", r"^bad\.md, 'A', line 3: .*tables:"),
            ("tables: missing.md\n## A\n" + ok, r"^bad\.md, line 1: .*missing\.md"),
            ("tables: ../x.md\n## A\n" + ok, r"^bad\.md, line 1: .*escapes"),
            ("## A\npin: Nope = x\n" + ok, r"^bad\.md, 'A', line 2: .*Nope"),
            ("## A\npin: Build = not offered\n" + ok, r"^bad\.md, 'A', line 2: .*not offered"),
            ("## A\npin: Pronouns = he/him\n" + ok, r"^bad\.md, 'A', line 2: .*he/him"),
            ("## A\npin: Age = in {possessive} late teens\n" + ok, r"^bad\.md, 'A', line 2: .*adults only"),
        ]
        for text, pattern in cases:
            with self.subTest(text=text):
                self.assertLoadError(ws, text, pattern)

    def test_a_duplicate_name_across_files_is_an_error_and_nothing_loads(self):
        ws = Workspace(self)
        other = ws.write_prompts("y.md", "## Plain\n### portrait\nx\n### token\ny\n")
        with self.assertRaisesRegex(ValueError, r"^y\.md, 'Plain', line 1: .*x\.md"):
            ws.load(ws.prompts, other)

    def test_a_missing_or_unreadable_tables_file_names_the_prompts_file(self):
        ws = Workspace(self)
        ws.write_tables("broken.json", "{")
        self.assertLoadError(ws, "tables: broken.json\n## A\n### portrait\nx\n### token\ny\n",
                             r"^bad\.md, line 1: .*broken\.json")


class TestListing(unittest.TestCase):
    def test_listing_reports_each_file_and_marks_broken_ones(self):
        ws = Workspace(self)
        broken = ws.write_prompts("broken.md", "## A\n### portrait\n{npc:nope}\n### token\ny\n")
        data = sp.listing([ws.prompts, broken], None, TABLES, gen.REQUIRED_TABLES, gen.load_extra_tables)
        self.assertEqual(data["dir"], str(ws.prompts_dir.resolve()))
        self.assertEqual([f["file"] for f in data["files"]], ["x.md", "broken.md"])
        self.assertEqual(data["files"][0]["templates"][0], {
            "name": "Kneeling", "weight": 3.0, "pins": {"Pronouns": "she/her"},
            "npcSlots": ["identity", "hair", "Subject", "is_are"],
            "secretSlots": ["Poses", "Clothing", "Lighting"]})
        self.assertNotIn("templates", data["files"][1])
        self.assertRegex(data["files"][1]["error"], r"^broken\.md, 'A', line 3: ")
        json.dumps(data)

    def test_a_cross_file_duplicate_marks_the_later_file(self):
        ws = Workspace(self)
        other = ws.write_prompts("y.md", "## Plain\n### portrait\nx\n### token\ny\n")
        data = sp.listing([ws.prompts, other], None, TABLES, gen.REQUIRED_TABLES, gen.load_extra_tables)
        self.assertIn("templates", data["files"][0])
        self.assertRegex(data["files"][1]["error"], r"^y\.md, 'Plain', line 1: .*x\.md")
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m unittest test.test_secret_prompts -v -k Load -k Listing`
Expected: `AttributeError: module 'secret_prompts' has no attribute 'load'`.

- [ ] **Step 3: Implement `load` and `listing`**

Append to `secret_prompts.py`:

```python
def _core(bullet):
    return bullet.partition("||")[0].strip()


def _resolve_pin(table, value, npc_tables, required):
    """The raw bullet a 'pin: Table = value' names, flags and all, or a reason.

    Matched on the flag-stripped text across the base table and its
    per-pronoun variants ('Hair (she)'), and for Pronouns on the subject
    alone, the way --pronouns matches. The raw bullet is what roll_npc's
    overrides expect: 'in her late teens || young' carries the flag the
    adults-only rule reads.
    """
    if table not in required:
        raise ValueError("pin names no default table: %s (one of %s)" % (table, ", ".join(required)))
    keys = [k for k in npc_tables if k == table or k.startswith(table + " (")]
    bullets = [b for k in keys for b in npc_tables[k]]
    if table == "Pronouns":
        wanted = value.split("/")[0].strip().lower()
        matches = [b for b in bullets if b.split("/")[0].strip().lower() == wanted]
    else:
        matches = [b for b in bullets if _core(b) == value]
    if not matches:
        raise ValueError("pin: %s = %s: the %s table offers no such bullet" % (table, value, table))
    bullet = matches[0]
    if table == "Age" and "young" in bullet.partition("||")[2].split():
        raise ValueError("pin: Age = %s is flagged 'young'; secret prompts describe adults only" % value)
    return bullet


def load(paths, tables_dir, npc_tables, required, read_tables):
    """Every template in `paths`, keyed by name, fully validated - or a ValueError.

    `tables_dir` is where a file's 'tables:' names resolve; None means the
    'secret-tables' sibling of the prompts file's own folder. `npc_tables`
    is the parsed default tables file and `required` the REQUIRED_TABLES
    list, for pins. `read_tables(paths, only=None, values=None)` is
    generate-npc.py's load_extra_tables, so a tables file that would be
    refused at roll time is refused here with the same reason.
    """
    templates = {}
    for path in paths:
        path = Path(path).resolve()
        tables, tables_line, parsed = parse_file(path)
        root = (Path(tables_dir) if tables_dir else path.parent.parent / "secret-tables").resolve()
        resolved = []
        for name in tables:
            target = (root / name).resolve()
            if not target.is_relative_to(root):
                raise _error(path, None, tables_line, "tables: %s escapes %s" % (name, root))
            resolved.append(target)
        loaded = {}
        if resolved:
            try:
                loaded = read_tables(resolved)
            except ValueError as exc:
                raise _error(path, None, tables_line, "tables: %s" % exc)
        for template in parsed:
            for table in template["secret_slots"]:
                line = template["slot_lines"][table]
                if not tables:
                    raise _error(path, template["name"], line,
                                 "{secret:%s} needs a 'tables:' line before the first '##'" % table)
                if table not in loaded:
                    raise _error(path, template["name"], line,
                                 "{secret:%s}: no such table in %s (tables: %s)"
                                 % (table, ", ".join(tables), ", ".join(loaded) or "none"))
            pins = {}
            for table, value in template["pin_text"].items():
                try:
                    pins[table] = _resolve_pin(table, value, npc_tables, required)
                except ValueError as exc:
                    raise _error(path, template["name"], _pin_line(path, template, table), str(exc))
            if template["name"] in templates:
                raise _error(path, template["name"], template["line"],
                             "template name already used in %s" % templates[template["name"]]["file"])
            template.update(path=path, tables=[str(t) for t in resolved], pins=pins)
            templates[template["name"]] = template
    return templates


def _pin_line(path, template, table):
    """The line a template's 'pin: <table>' sits on, re-read for the message."""
    lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    for number in range(template["line"], len(lines) + 1):
        line = lines[number - 1].strip()
        if number > template["line"] and line.startswith("#"):
            break
        key, sep, value = line.partition(":")
        if sep and key.strip() == "pin" and value.partition("=")[0].strip() == table:
            return number
    return template["line"]


def listing(paths, tables_dir, npc_tables, required, read_tables):
    """The JSON the import GUI lists templates from: one entry per file.

    Each file is loaded on its own so one broken file cannot hide the rest;
    a template name shared across files marks the later file, since the
    first to claim the name is the one a preset could already refer to.
    """
    files, owners = [], {}
    for path in paths:
        path = Path(path).resolve()
        try:
            templates = load([path], tables_dir, npc_tables, required, read_tables)
        except ValueError as exc:
            files.append({"file": path.name, "error": str(exc)})
            continue
        taken = [t for t in templates.values() if t["name"] in owners]
        if taken:
            first = taken[0]
            files.append({"file": path.name, "error": str(_error(
                path, first["name"], first["line"], "template name already used in %s" % owners[first["name"]]))})
            continue
        for name in templates:
            owners[name] = path.name
        files.append({"file": path.name, "templates": [
            {"name": t["name"], "weight": t["weight"], "pins": dict(t["pin_text"]),
             "npcSlots": list(t["npc_slots"]), "secretSlots": list(t["secret_slots"])}
            for t in templates.values()]})
    return {"dir": str(Path(paths[0]).resolve().parent) if paths else "", "files": files}
```

- [ ] **Step 4: Run the tests**

Run: `python -m unittest test.test_secret_prompts -v`
Expected: all pass. (`Path.is_relative_to` needs Python 3.9+, which `art_styles.contained` already relies on.)

- [ ] **Step 5: Commit**

```bash
git add secret_prompts.py test/test_secret_prompts.py
git commit -m "validate secret prompt tables, slots and pins on load" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: `fill()`, `tidy()` and `parts()`

**Files:**
- Modify: `secret_prompts.py`
- Test: `test/test_secret_prompts.py`

**Interfaces:**
- Consumes: `tokens()` (Task 2), `prompt_composer._part()` and `prompt_composer.reflow()` (Task 1).
- Produces:
  - `fill(text, fields, extra) -> str` - the template text with `{npc:f}` from `fields[f]` and `{secret:T}` from `extra[T]`, sentence-start capitalisation of inserted values, then `tidy()`. Missing keys raise `ValueError` naming the slot.
  - `tidy(text) -> str` - spec 2.4 rules 2-4.
  - `parts(text, fields, extra) -> list[part]` - composer parts (`text:<n>` literals, `npc:<field>` / `secret:<table>` slots with `sources`), whose texts join to exactly `fill(text, fields, extra)`. Repeated slots get `:2`, `:3` suffixes on their ids.

- [ ] **Step 1: Write the failing tests**

Append to `test/test_secret_prompts.py`:

```python
FIELDS = dict(gen.pronoun_fields("she/her/her/woman"), identity="a dockworker, a mature adult woman in her thirties",
              hair="a long silver braid", name="Test Subject")
EXTRA = {"Poses": "kneeling upright with knees spread", "Clothing": "completely nude", "Lighting": "soft candlelight"}


class TestFill(unittest.TestCase):
    def test_fills_both_slot_kinds_and_tidies(self):
        text = ("A portrait of {npc:identity}, with {npc:hair}. {npc:Subject} {npc:is_are} {secret:Poses}, "
                "{secret:Clothing}. {secret:Lighting}.")
        self.assertEqual(sp.fill(text, FIELDS, EXTRA),
                         "A portrait of a dockworker, a mature adult woman in her thirties, with a long silver braid. "
                         "She is kneeling upright with knees spread, completely nude. Soft candlelight.")

    def test_a_value_starting_a_sentence_is_capitalised(self):
        self.assertEqual(sp.fill("{secret:Lighting}. {secret:Clothing}! {secret:Poses}? {npc:hair}", FIELDS, EXTRA),
                         "Soft candlelight. Completely nude! Kneeling upright with knees spread? A long silver braid.")
        self.assertEqual(sp.fill("with {npc:hair}", FIELDS, EXTRA), "with a long silver braid.")

    def test_whitespace_collapses(self):
        self.assertEqual(sp.fill("A  portrait\tof   {npc:hair} ,  here .", FIELDS, EXTRA),
                         "A portrait of a long silver braid, here.")

    def test_punctuation_repairs(self):
        self.assertEqual(sp.tidy("one ,. two .. three,. four"), "one. two. three. four.")
        self.assertEqual(sp.tidy("ends with a digit 7"), "ends with a digit 7")
        self.assertEqual(sp.tidy("  padded  "), "padded.")
        self.assertEqual(sp.tidy(""), "")

    def test_values_are_otherwise_verbatim(self):
        self.assertEqual(sp.fill("{secret:Poses}", FIELDS, {"Poses": "Kneeling, ALL caps kept"}),
                         "Kneeling, ALL caps kept.")

    def test_literal_braces_survive(self):
        self.assertEqual(sp.fill("{{Literal}} braces and {npc:name}", FIELDS, EXTRA), "{Literal} braces and Test Subject.")

    def test_a_missing_value_names_the_slot(self):
        with self.assertRaisesRegex(ValueError, "secret:Nope"):
            sp.fill("{secret:Nope}", FIELDS, EXTRA)
        with self.assertRaisesRegex(ValueError, "npc:nope"):
            sp.fill("{npc:nope}", FIELDS, EXTRA)


class TestParts(unittest.TestCase):
    TEXT = "A portrait of {npc:identity}, with {npc:hair}. {secret:Poses}, {secret:Clothing}. {secret:Poses}."

    def test_parts_join_to_the_filled_prompt(self):
        parts = sp.parts(self.TEXT, FIELDS, EXTRA)
        self.assertEqual("".join(p["text"] for p in parts), sp.fill(self.TEXT, FIELDS, EXTRA))

    def test_slot_parts_carry_ids_sources_and_values(self):
        parts = sp.parts(self.TEXT, FIELDS, EXTRA)
        ids = [p["id"] for p in parts]
        self.assertEqual([i for i in ids if not i.startswith("text:")],
                         ["npc:identity", "npc:hair", "secret:Poses", "secret:Clothing", "secret:Poses:2"])
        by_id = {p["id"]: p for p in parts}
        self.assertEqual(by_id["npc:identity"]["sources"], ["Role", "Age", "Pronouns"])
        self.assertEqual(by_id["npc:hair"]["sources"], ["Hair", "Hair colour"])
        self.assertEqual(by_id["secret:Poses"]["sources"], ["Poses"])
        self.assertEqual(by_id["secret:Poses"]["value"], "Kneeling upright with knees spread")
        self.assertEqual(by_id["secret:Poses:2"]["value"], "Kneeling upright with knees spread")
        for part in parts:
            if part["id"].startswith("text:"):
                self.assertEqual(part["sources"], [])
        self.assertEqual(len(set(ids)), len(ids))

    def test_tidy_edits_land_on_the_parts_not_between_them(self):
        parts = sp.parts("{secret:Poses} ,  {npc:hair}", FIELDS, EXTRA)
        self.assertEqual("".join(p["text"] for p in parts), "Kneeling upright with knees spread, a long silver braid.")
        self.assertEqual(parts[-1]["sources"], ["Hair", "Hair colour"])
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m unittest test.test_secret_prompts -v -k Fill -k Parts`
Expected: `AttributeError` on `sp.fill`.

- [ ] **Step 3: Implement**

Append to `secret_prompts.py`:

```python
def tidy(text):
    """Spec 2.4 rules 2-4: one space, no space before , or ., ',.' and '..'
    collapse to '.', stripped, and closed with a full stop after a letter."""
    text = re.sub(r"\s+", " ", text)
    text = text.replace(" ,", ",").replace(" .", ".")
    text = re.sub(r",\s*\.", ".", text)
    text = re.sub(r"\.{2,}", ".", text)
    text = text.strip()
    if text and text[-1].isalpha():
        text += "."
    return text


def _value(kind, name, fields, extra, so_far):
    """One slot's value, capitalised when it opens a sentence."""
    source = fields if kind == "npc" else extra
    if name not in source:
        raise ValueError("no value for {%s:%s}" % (kind, name))
    value = str(source[name])
    before = so_far.rstrip()
    if value and (not before or before[-1] in ".!?"):
        value = value[0].upper() + value[1:]
    return value


def fill(text, fields, extra):
    """The template text with every slot filled and the result tidied.

    Rule 1 of the tidy-up (a value that begins a sentence is capitalised)
    lives here rather than in tidy(), because only the filler knows which
    characters came from a value and which were the author's own.
    """
    out = []
    for kind, value in tokens(text):
        out.append(value if kind == "text" else _value(kind, value, fields, extra, "".join(out)))
    return tidy("".join(out))


def parts(text, fields, extra):
    """Composer fragments whose texts join to exactly fill(text, fields, extra).

    Literal runs are 'text:<n>' parts with no sources; each slot is one part
    whose id names it ('npc:hair', 'secret:Kneeling Poses', a second use of
    the same slot ':2') and whose sources are the tables it came from, so
    the GUI can show '[Random value from Kneeling Poses]' where nothing has
    fixed the draw. The tidy-up is then mapped back across the parts.
    """
    import prompt_composer
    pieces, counts, so_far = [], {}, ""
    for index, (kind, value) in enumerate(tokens(text)):
        if kind == "text":
            pieces.append(prompt_composer._part("text:%d" % index, value))
            so_far += value
            continue
        filled = _value(kind, value, fields, extra, so_far)
        counts[(kind, value)] = counts.get((kind, value), 0) + 1
        ident = "%s:%s" % (kind, value) + (":%d" % counts[(kind, value)] if counts[(kind, value)] > 1 else "")
        sources = list(NPC_SOURCES.get(value, ())) if kind == "npc" else [value]
        pieces.append(prompt_composer._part(ident, filled, sources))
        so_far += filled
    return prompt_composer.reflow(pieces, tidy(so_far))
```

- [ ] **Step 4: Run the tests**

Run: `python -m unittest test.test_secret_prompts -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add secret_prompts.py test/test_secret_prompts.py
git commit -m "fill secret prompt templates and map the tidy-up onto preview parts" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: `choose()`, `merge_pins()`, `snapshot()`

**Files:**
- Modify: `secret_prompts.py`
- Test: `test/test_secret_prompts.py`

**Interfaces:**
- Produces:
  - `choose(templates, name, seed) -> template` - `"random"` draws by `weight` from `random.Random("%s:secret-prompt" % seed)`; a name is looked up; unknown raises `ValueError` listing the names.
  - `merge_pins(template, overrides) -> dict` - a copy of `overrides` with the template's `pins` merged; a pin whose flag-stripped text (subject, for Pronouns) differs from an existing override raises `ValueError` naming both values.
  - `snapshot(template) -> dict` - `{"file", "name", "portrait", "token", "tables"}`.
  - `snapshot_secret_slots(snapshot) -> list[str]` - the union of the secret slots in its portrait and token texts.

- [ ] **Step 1: Write the failing tests**

Append to `test/test_secret_prompts.py`:

```python
class TestChoose(unittest.TestCase):
    def setUp(self):
        self.ws = Workspace(self)
        self.templates = self.ws.load()

    def test_a_name_is_looked_up(self):
        self.assertEqual(sp.choose(self.templates, "Plain", 1)["name"], "Plain")

    def test_an_unknown_name_lists_the_choices(self):
        with self.assertRaisesRegex(ValueError, "Kneeling, Plain"):
            sp.choose(self.templates, "Nope", 1)

    def test_random_is_weighted_and_reproducible_per_seed(self):
        picks = [sp.choose(self.templates, "random", seed)["name"] for seed in range(200)]
        self.assertEqual(picks, [sp.choose(self.templates, "random", seed)["name"] for seed in range(200)])
        self.assertGreater(picks.count("Kneeling"), 120)
        self.assertGreater(picks.count("Plain"), 15)

    def test_random_draws_from_its_own_stream(self):
        self.assertEqual(sp.choose(self.templates, "random", 7)["name"],
                         sp.choose(self.templates, "random", "7")["name"])
        expected = random.Random("7:secret-prompt").choices(["Kneeling", "Plain"], [3.0, 1.0])[0]
        self.assertEqual(sp.choose(self.templates, "random", 7)["name"], expected)


class TestPins(unittest.TestCase):
    def setUp(self):
        self.template = Workspace(self).load()["Kneeling"]

    def test_pins_merge_into_the_overrides(self):
        merged = sp.merge_pins(self.template, {"Role": "a dockworker"})
        self.assertEqual(merged, {"Role": "a dockworker", "Pronouns": "she/her/her/woman"})

    def test_an_agreeing_override_is_fine(self):
        merged = sp.merge_pins(self.template, {"Pronouns": "she/her/her/woman"})
        self.assertEqual(merged["Pronouns"], "she/her/her/woman")

    def test_a_disagreeing_override_names_both_values(self):
        with self.assertRaisesRegex(ValueError, r"she/her.*they/them/their/person|they/them/their/person.*she/her"):
            sp.merge_pins(self.template, {"Pronouns": "they/them/their/person"})

    def test_the_caller_dict_is_not_mutated(self):
        overrides = {}
        sp.merge_pins(self.template, overrides)
        self.assertEqual(overrides, {})


class TestSnapshot(unittest.TestCase):
    def test_snapshot_holds_the_text_and_the_tables(self):
        ws = Workspace(self)
        snap = sp.snapshot(ws.load()["Kneeling"])
        self.assertEqual(set(snap), {"file", "name", "portrait", "token", "tables"})
        self.assertEqual(snap["file"], "x.md")
        self.assertEqual(snap["name"], "Kneeling")
        self.assertIn("{secret:Poses}", snap["portrait"])
        self.assertEqual(snap["tables"], [str(ws.tables.resolve())])
        self.assertEqual(sp.snapshot_secret_slots(snap), ["Poses", "Clothing", "Lighting"])
        json.dumps(snap)
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m unittest test.test_secret_prompts -v -k Choose -k Pins -k Snapshot`
Expected: `AttributeError` on `sp.choose`.

- [ ] **Step 3: Implement**

Append to `secret_prompts.py`:

```python
def choose(templates, name, seed):
    """The template `name` asks for, or a weighted draw for 'random'.

    The draw seeds its own generator from the NPC's seed and a fixed tag,
    so it neither reads nor moves the stream roll_npc() consumes: the NPC a
    seed produces is the same with or without a template.
    """
    if name == "random":
        pool = list(templates.values())
        rng = random.Random("%s:secret-prompt" % seed)
        return rng.choices(pool, [t["weight"] for t in pool])[0]
    if name not in templates:
        raise ValueError("no secret prompt named %r; loaded: %s" % (name, ", ".join(templates) or "none"))
    return templates[name]


def merge_pins(template, overrides):
    """`overrides` plus the template's pins, refusing a pin that contradicts one."""
    merged = dict(overrides or {})
    for table, bullet in template["pins"].items():
        if table in merged:
            if table == "Pronouns":
                same = merged[table].split("/")[0].strip().lower() == bullet.split("/")[0].strip().lower()
            else:
                same = _core(merged[table]) == _core(bullet)
            if not same:
                raise ValueError("secret prompt '%s' pins %s = %s, but --set-trait asks for %s = %s"
                                 % (template["name"], table, template["pin_text"][table], table, merged[table]))
        merged[table] = bullet
    return merged


def snapshot(template):
    """What the manifest keeps: enough to refill the prompt with the file gone."""
    return {"file": template["file"], "name": template["name"],
            "portrait": template["portrait"], "token": template["token"],
            "tables": list(template["tables"])}


def snapshot_secret_slots(snap):
    """Every {secret:...} table the snapshot's two texts read, in order."""
    out = []
    for target in ("portrait", "token"):
        for table in slots(snap.get(target, ""))[1]:
            if table not in out:
                out.append(table)
    return out
```

- [ ] **Step 4: Run the tests**

Run: `python -m unittest test.test_secret_prompts -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add secret_prompts.py test/test_secret_prompts.py
git commit -m "choose, pin and snapshot secret prompt templates" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: generator flags and refusals

**Files:**
- Modify: `generate-npc.py:3987-3996` (flag definitions), `generate-npc.py:4101-4125` (validation after `art_styles.configure`)
- Test: `test/test_secret_prompts.py`

**Interfaces:**
- Produces: `args.secret_prompts: list[Path]`, `args.secret_prompt: str|None`, `args.secret_tables_dir: Path|None`, `args.list_secret_prompts: bool` on the parsed namespace, with the spec 3.2 refusals as `parser.error` calls (a `SystemExit` whose message names the offending flag).

- [ ] **Step 1: Write the failing tests**

Append to `test/test_secret_prompts.py`:

```python
class TestFlags(unittest.TestCase):
    def setUp(self):
        self.ws = Workspace(self)
        self.secret = ["--secret", "--secret-config", str(self.ws.config)]

    def parse(self, *argv):
        return gen.parse_args(["--tables", str(FIXTURE_TABLES), "--dry-run"] + list(argv))

    def assertRefused(self, pattern, *argv):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit):
            self.parse(*argv)
        self.assertRegex(err.getvalue(), pattern)

    def test_the_flags_parse(self):
        args = self.parse(*self.secret, "--secret-prompts", str(self.ws.prompts), "--secret-prompt", "random",
                          "--secret-tables-dir", str(self.ws.tables_dir))
        self.assertEqual(args.secret_prompts, [self.ws.prompts])
        self.assertEqual(args.secret_prompt, "random")
        self.assertEqual(args.secret_tables_dir, self.ws.tables_dir)
        self.assertFalse(args.list_secret_prompts)
        listing = self.parse(*self.secret, "--secret-prompts", str(self.ws.prompts), "--list-secret-prompts")
        self.assertTrue(listing.list_secret_prompts)

    def test_secret_is_required(self):
        self.assertRefused("--secret", "--secret-prompts", str(self.ws.prompts), "--secret-prompt", "random")
        self.assertRefused("--secret", "--secret-prompts", str(self.ws.prompts), "--list-secret-prompts")

    def test_the_pair_requires_each_other(self):
        self.assertRefused("--secret-prompt", *self.secret, "--secret-prompts", str(self.ws.prompts))
        self.assertRefused("--secret-prompts", *self.secret, "--secret-prompt", "random")

    def test_listing_requires_the_files(self):
        self.assertRefused("--secret-prompts", *self.secret, "--list-secret-prompts")

    def test_refused_combinations(self):
        base = self.secret + ["--secret-prompts", str(self.ws.prompts), "--secret-prompt", "Plain"]
        for flag in (["--prompt-layout", "{}"], ["--disable-table", "Stance"],
                     ["--extra-tables", str(self.ws.tables)], ["--extra-table", "Poses"],
                     ["--extra-target", "Poses=portrait"]):
            with self.subTest(flag=flag[0]):
                self.assertRefused(re.escape(flag[0]), *base, *flag)

    def test_extra_value_stays_allowed(self):
        args = self.parse(*self.secret, "--secret-prompts", str(self.ws.prompts), "--secret-prompt", "Plain",
                          "--extra-value", "Poses=completely nude")
        self.assertEqual(args.extra_value, ["Poses=completely nude"])

    def test_refused_on_regeneration(self):
        self.assertRefused("--secret-prompt", *self.secret, "--regen-manifest", str(self.ws.root / "private" / "manifest.json"),
                           "--regen-id", "x", "--secret-prompts", str(self.ws.prompts), "--secret-prompt", "Plain")
```

Add `import re` to the test file's imports.

- [ ] **Step 2: Run to verify they fail**

Run: `python -m unittest test.test_secret_prompts -v -k Flags`
Expected: `test_the_flags_parse` fails with `error: unrecognized arguments: --secret-prompts`.

- [ ] **Step 3: Add the flags and the checks**

In `parse_args`, after the `--disable-table` argument (line 3995):

```python
    roll.add_argument("--secret-prompts", action="append", default=[], type=Path, metavar="PATH",
                      help="a markdown file of secret prompt templates (repeatable; Secret mode only). "
                           "See README: '## Name' opens a template, '### portrait' and '### token' hold "
                           "its two prompts, {npc:field} and {secret:Table} are the blanks")
    roll.add_argument("--secret-prompt", metavar="NAME",
                      help="with --secret-prompts, the template to use, or 'random' for a weighted "
                           "draw per NPC; it replaces the house portrait and token templates")
    roll.add_argument("--secret-tables-dir", type=Path, metavar="DIR",
                      help="where a template file's 'tables:' names resolve (default: the "
                           "secret-tables folder beside the template file's own folder)")
```

In the `run` group, after `--trait-odds`:

```python
    run.add_argument("--list-secret-prompts", action="store_true",
                     help="with --secret-prompts, print every template as JSON (name, weight, pins, "
                          "slots, or the file's first error) and exit; read by the Import GUI")
```

After the `try: art_styles.configure(...)` block (line 4119) and before the `--no-portrait`/`--no-token` check:

```python
    if (args.secret_prompts or args.secret_prompt or args.list_secret_prompts) and not args.secret:
        p.error("--secret-prompts, --secret-prompt and --list-secret-prompts require --secret")
    if args.list_secret_prompts:
        if not args.secret_prompts:
            p.error("--list-secret-prompts needs at least one --secret-prompts file")
    elif bool(args.secret_prompts) != bool(args.secret_prompt):
        p.error("--secret-prompts and --secret-prompt go together: the files, and the template "
                "name (or 'random') to use from them")
    if args.secret_prompt:
        if args.regen_manifest:
            p.error("regeneration reuses the recorded secret prompt; --secret-prompt is for new NPCs")
        # The template decides what appears and in what order, so every flag
        # that edits the house prompt's composition is meaningless with one.
        for flag, given in (("--prompt-layout", bool(args.prompt_layout)),
                            ("--disable-table", bool(args.disable_table)),
                            ("--extra-tables", bool(args.extra_tables)),
                            ("--extra-table", bool(args.extra_table)),
                            ("--extra-target", bool(args.extra_target))):
            if given:
                p.error("%s cannot be combined with --secret-prompt: the template decides what "
                        "appears and in what order (--extra-value still pins a slot table's row)" % flag)
```

- [ ] **Step 4: Run the tests**

Run: `python -m unittest test.test_secret_prompts -v -k Flags`
Expected: all pass. Then `python -m unittest test.test_extra_tables test.test_art_styles -v` still passes (no existing flag changed).

- [ ] **Step 5: Commit**

```bash
git add generate-npc.py test/test_secret_prompts.py
git commit -m "add the secret prompt flags and their refusals" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: the adults-only rule in `roll_npc`

**Files:**
- Modify: `generate-npc.py:2341` (signature), `generate-npc.py:2531-2538` (the Age branch of `narrow`), `generate-npc.py:2975` (after `npc["_young"] = young`), `generate-npc.py:4527-4532` (`reroll_from_raw`)
- Test: `test/test_secret_prompts.py`

**Interfaces:**
- Produces: `roll_npc(tables, rng, overrides=None, unarmed=False, probe=None, adults_only=False)`. With `adults_only=True`, every `Age` bullet flagged `young` leaves the pool before the draw (an empty pool is a `SystemExit`), and a forced or pinned young Age is a `SystemExit` naming it. `reroll_from_raw` passes `adults_only=bool(npc.get("_secret_prompt"))` and keeps `_secret_prompt` across the wholesale replace.

- [ ] **Step 1: Write the failing tests**

Append to `test/test_secret_prompts.py`:

```python
class TestAdultsOnly(unittest.TestCase):
    YOUNG = "in {possessive} late teens || young"

    def test_a_plain_roll_can_be_young(self):
        self.assertTrue(any(gen.roll_npc(TABLES, random.Random(s), None)["_young"] for s in range(60)))

    def test_adults_only_never_rolls_young(self):
        for seed in range(60):
            self.assertFalse(gen.roll_npc(TABLES, random.Random(seed), None, adults_only=True)["_young"])

    def test_adults_only_does_not_move_other_tables(self):
        """With no young bullet to drop, the filtered pool is the pool: same seed, same NPC."""
        tables = dict(TABLES, Age=["in {possessive} thirties"])
        for seed in range(20):
            plain = gen.roll_npc(tables, random.Random(seed), None)
            adult = gen.roll_npc(tables, random.Random(seed), None, adults_only=True)
            self.assertEqual({k: v for k, v in plain.items() if not k.startswith("_")},
                             {k: v for k, v in adult.items() if not k.startswith("_")})

    def test_a_forced_young_age_is_refused(self):
        with self.assertRaisesRegex(SystemExit, "adults only"):
            gen.roll_npc(TABLES, random.Random(1), {"Age": self.YOUNG}, adults_only=True)

    def test_a_pool_of_only_young_ages_is_refused(self):
        tables = dict(TABLES, Age=[self.YOUNG])
        with self.assertRaisesRegex(SystemExit, "adults only"):
            gen.roll_npc(tables, random.Random(1), None, adults_only=True)

    def test_a_raw_reroll_keeps_the_snapshot_and_the_rule(self):
        npc = gen.roll_npc(TABLES, random.Random(3), None, adults_only=True)
        npc["_secret_prompt"] = {"file": "x.md", "name": "T", "portrait": "p", "token": "t", "tables": []}
        for seed in range(30):
            gen.reroll_from_raw(TABLES, npc, {"Age"}, random.Random(seed))
            self.assertFalse(npc["_young"])
            self.assertEqual(npc["_secret_prompt"]["name"], "T")
        with self.assertRaisesRegex(SystemExit, "adults only"):
            gen.reroll_from_raw(TABLES, npc, {"Age"}, random.Random(1), {"Age": self.YOUNG})
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m unittest test.test_secret_prompts -v -k AdultsOnly`
Expected: `TypeError: roll_npc() got an unexpected keyword argument 'adults_only'`.

- [ ] **Step 3: Implement**

Change the signature at line 2341:

```python
def roll_npc(tables, rng, overrides=None, unarmed=False, probe=None, adults_only=False):
```

and add to its docstring one paragraph:

```
    `adults_only` is the secret-prompt rule: an Age bullet flagged 'young'
    is dropped from the pool before the draw and refused if forced or
    pinned. It lives here rather than in the template loader so that no
    template, override or re-roll path can reach a young Age while a secret
    prompt is active.
```

In `narrow()`, immediately BEFORE the existing `if name == "Age" and forced_figure and forced_age is None:` block:

```python
        # Secret prompts describe adults only. Applied before the figure
        # pairing so that pairing's "never filter the pool down to nothing"
        # guard cannot put a young bullet back.
        if name == "Age" and adults_only:
            grown = [x for x in options if "young" not in split_flags(x)[1]]
            if not grown:
                raise SystemExit(
                    "every Age bullet the roll could reach is flagged 'young'; a secret "
                    "prompt describes adults only, so the Age table needs an adult bullet")
            options = grown
```

After `npc["_young"] = young` (line 2975):

```python
    if adults_only and young:
        raise SystemExit(
            "Age %r is flagged 'young'; a secret prompt describes adults only. Force or "
            "pin an adult Age instead." % npc["Age"])
```

In `reroll_from_raw`, replace the `fresh = roll_npc(tables, rng, overrides)` line and the `kept` line:

```python
    fresh = roll_npc(tables, rng, overrides, adults_only=bool(npc.get("_secret_prompt")))
    # Neither is a table roll, so the fresh roll knows nothing of them: the
    # private values, the disabled list, the layout and the secret prompt
    # snapshot travel with the entry.
    kept = {k: npc[k] for k in ("_extra", "_extra_targets", "_disabled", "_prompt_layout", "_secret_prompt")
            if k in npc}
```

- [ ] **Step 4: Run the tests**

Run: `python -m unittest test.test_secret_prompts test.test_reroll_trait test.test_set_trait_value -v`
Expected: the new cases pass and the two existing re-roll modules are unchanged (compare any failure against `main` per the memory note before treating it as a regression).

- [ ] **Step 5: Commit**

```bash
git add generate-npc.py test/test_secret_prompts.py
git commit -m "keep every secret prompt roll to adult ages" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: wire templates into the roll, the prompts and the record

**Files:**
- Modify: `generate-npc.py` - imports (top of file, beside `import art_styles`), `build_prompts` (insert after line 3644 `fields["identity"] = ...`), new `_secret_prompt_build()` and `warn_token_limit()` beside `extra_sentence()`, `extra_record()` (line 5104), `npc_from_entry()` (line 5055), `write_dossier()` (line 3838), `main()` (lines 5443-5566)
- Test: `test/test_secret_prompts.py`

**Interfaces:**
- Consumes: everything in `secret_prompts` (Tasks 2-5), `roll_npc(..., adults_only=True)` (Task 7).
- Produces:
  - `build_prompts(npc, style, guidance)` returns the filled template prompts when `npc["_secret_prompt"]` is set; `build_prompt_parts` returns template parts.
  - `warn_token_limit(prompts)` - the existing over-512-token warning, shared.
  - `extra_record(npc)` writes `"secretPrompt"`; `npc_from_entry` restores `_secret_prompt`.
  - `main()`: `--list-secret-prompts` prints the listing JSON and exits 0; a template run chooses, pins, rolls adults-only, rolls only the referenced tables, records the snapshot, prints `    secret prompt: <name> (<file>)` in `--dry-run`.

- [ ] **Step 1: Write the failing tests**

Append to `test/test_secret_prompts.py`:

```python
def rolled_with_template(ws, name="Kneeling", seed=3):
    templates = ws.load()
    template = sp.choose(templates, name, seed)
    rng = random.Random(seed)
    npc = gen.roll_npc(TABLES, rng, sp.merge_pins(template, {}), adults_only=True)
    npc["_extra"] = gen.roll_extra(gen.load_extra_tables(template["tables"], template["secret_slots"]), rng)
    npc["_extra_targets"] = {}
    npc["_secret_prompt"] = sp.snapshot(template)
    return npc


class TestBuildPrompts(unittest.TestCase):
    def test_the_template_replaces_both_house_prompts(self):
        ws = Workspace(self)
        npc = rolled_with_template(ws)
        portrait, token = gen.build_prompts(npc)
        # identity is "<Role>, <maturity> <gender> <age>", so only its head is pinned here.
        self.assertTrue(portrait.startswith("A portrait of %s, " % npc["Role"]), portrait)
        self.assertIn(", with %s. She is %s, completely nude. Soft candlelight." % (npc["Hair"], npc["_extra"]["Poses"]), portrait)
        self.assertTrue(token.startswith("A full-body figure of %s, " % npc["Role"]), token)
        self.assertIn("%s, completely nude, against an empty plain white background." % npc["_extra"]["Poses"], token)
        for prompt in (portrait, token):
            self.assertNotIn("painterly", prompt)
            self.assertNotIn("Keep the palette", prompt)
            self.assertNotIn("both feet in frame", prompt)

    def test_style_and_colour_guidance_apply(self):
        ws = Workspace(self)
        npc = rolled_with_template(ws)
        style = {"id": "ink", "name": "Ink", "prompt": "Monochrome ink wash.", "hidden": False}
        guidance = {"id": "warm", "name": "Warm", "prompt": "Warm amber palette throughout.", "hidden": False}
        portrait, token = gen.build_prompts(npc, style, guidance)
        for prompt in (portrait, token):
            self.assertTrue(prompt.endswith("\nArt style: Monochrome ink wash."), prompt)
            self.assertIn("Soft candlelight. Warm amber palette throughout.", portrait)
        plain = gen.build_prompts(npc)[0]
        self.assertNotIn("Warm amber", plain)

    def test_parts_join_to_the_prompts(self):
        ws = Workspace(self)
        npc = rolled_with_template(ws)
        parts = gen.build_prompt_parts(npc)
        prompts = gen.build_prompts(npc)
        for target, prompt in zip(("portrait", "token"), prompts):
            self.assertEqual("".join(p["text"] for p in parts[target]), prompt)
        ids = [p["id"] for p in parts["portrait"]]
        self.assertIn("secret:Poses", ids)
        self.assertIn("npc:identity", ids)
        self.assertEqual(next(p for p in parts["portrait"] if p["id"] == "secret:Poses")["sources"], ["Poses"])


class TestRecord(unittest.TestCase):
    def test_snapshot_round_trips_and_survives_the_file_going(self):
        ws = Workspace(self)
        npc = rolled_with_template(ws)
        prompts = gen.build_prompts(npc)
        entry = manifest_entry(seed=3)
        gen.persist_traits(entry, npc)
        gen.persist_flags(entry, npc)   # the 'young' flag the maturity wording reads
        self.assertEqual(entry["secretPrompt"]["name"], "Kneeling")
        self.assertEqual(entry["secretPrompt"]["file"], "x.md")
        self.assertEqual(entry["extraTraits"], npc["_extra"])
        self.assertNotIn("extraTraitTargets", entry)
        ws.prompts.unlink()
        ws.write_tables("tables.md", "## Poses\n- something else entirely\n")
        restored = gen.npc_from_entry(json.loads(json.dumps(entry)), entry["id"], warn=False)
        self.assertEqual(restored["_secret_prompt"], npc["_secret_prompt"])
        self.assertEqual(gen.build_prompts(restored), prompts)

    def test_a_record_without_a_template_has_no_key(self):
        npc = gen.roll_npc(TABLES, random.Random(1), None)
        self.assertNotIn("secretPrompt", gen.extra_record(npc))
        self.assertNotIn("_secret_prompt", gen.npc_from_entry(manifest_entry(seed=1), "x", warn=False))

    def test_the_dossier_names_the_template(self):
        ws = Workspace(self)
        npc = rolled_with_template(ws)
        path = ws.root / "d.md"
        gen.write_dossier(path, npc, 3, gen.build_prompts(npc), [])
        self.assertIn("| Secret prompt | Kneeling (x.md) |", path.read_text(encoding="utf-8"))


class TestCli(unittest.TestCase):
    def setUp(self):
        self.ws = Workspace(self)

    def run_main(self, *argv, secret=True):
        out = io.StringIO()
        base = ["--tables", str(FIXTURE_TABLES), "--dry-run", "--seed", "5"]
        if secret:
            base += ["--secret", "--secret-config", str(self.ws.config)]
        with contextlib.redirect_stdout(out):
            code = gen.main(base + list(argv))
        return code, out.getvalue()

    def templated(self, name, *argv):
        return self.run_main("--secret-prompts", str(self.ws.prompts), "--secret-prompt", name, *argv)

    def test_dry_run_prints_the_filled_template_and_names_it(self):
        code, out = self.templated("Kneeling")
        self.assertEqual(code, 0)
        self.assertIn("secret prompt: Kneeling (x.md)", out)
        self.assertIn("She is ", out)
        self.assertIn("completely nude", out)
        self.assertNotIn("painterly", out)

    def test_a_template_leaves_the_base_npc_unchanged(self):
        _, plain = self.run_main()
        _, templated = self.templated("Plain")
        self.assertEqual(plain.splitlines()[3], templated.splitlines()[3])

    def test_random_picks_by_weight_and_is_reproducible(self):
        names = []
        for seed in range(40):
            _, out = self.run_main("--secret-prompts", str(self.ws.prompts), "--secret-prompt", "random",
                                   "--seed", str(seed))
            names.append("Kneeling" if "secret prompt: Kneeling" in out else "Plain")
        self.assertGreater(names.count("Kneeling"), 20)
        self.assertIn("Plain", names)
        again = [self.run_main("--secret-prompts", str(self.ws.prompts), "--secret-prompt", "random",
                               "--seed", str(seed))[1] for seed in range(40)]
        self.assertEqual(names, ["Kneeling" if "secret prompt: Kneeling" in out else "Plain" for out in again])

    def test_only_referenced_tables_roll(self):
        self.ws.write_prompts("x.md", PROMPTS_MD.replace("{secret:Lighting}.", ""))
        _, out = self.templated("Kneeling")
        self.assertNotIn("candlelight", out)

    def test_extra_value_pins_a_slot(self):
        _, out = self.templated("Kneeling", "--extra-value", "Poses=lying on her back with legs raised", "--count", "3")
        self.assertEqual(out.count("lying on her back with legs raised"), 6)
        with self.assertRaises(SystemExit):
            self.templated("Kneeling", "--extra-value", "Nope=x")

    def test_a_pin_versus_override_conflict_is_a_clean_exit(self):
        with self.assertRaises(SystemExit) as caught:
            self.templated("Kneeling", "--pronouns", "they")
        self.assertIn("Pronouns", str(caught.exception))

    def test_a_young_override_is_refused(self):
        with self.assertRaisesRegex(SystemExit, "adults only"):
            self.templated("Kneeling", "--set-trait", "Age=in {possessive} late teens || young")

    def test_a_broken_file_is_a_clean_exit_naming_the_line(self):
        self.ws.write_prompts("x.md", "## A\n### portrait\n{npc:nope}\n### token\ny\n")
        with self.assertRaises(SystemExit) as caught:
            self.templated("A")
        self.assertIn("x.md, 'A', line 3", str(caught.exception))

    def test_list_secret_prompts_prints_json_and_nothing_else(self):
        broken = self.ws.write_prompts("broken.md", "## A\n### portrait\n{npc:nope}\n### token\ny\n")
        code, out = self.run_main("--secret-prompts", str(self.ws.prompts), "--secret-prompts", str(broken),
                                  "--list-secret-prompts")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual([f["file"] for f in data["files"]], ["x.md", "broken.md"])
        self.assertEqual(data["files"][0]["templates"][0]["name"], "Kneeling")
        self.assertRegex(data["files"][1]["error"], r"^broken\.md, 'A', line 3: ")

    def test_prompt_preview_parts(self):
        code, out = self.templated("Kneeling", "--prompt-preview", "--extra-value", "Clothing=completely nude")
        self.assertEqual(code, 0)
        data = json.loads(out)
        ids = {p["id"]: p for p in data["portrait"]}
        self.assertEqual(ids["secret:Poses"]["randomSources"], ["Poses"])
        self.assertEqual(ids["secret:Clothing"]["randomSources"], [])
        self.assertEqual(ids["npc:identity"]["randomSources"], ["Role", "Age"])
        self.assertEqual(ids["npc:Subject"]["randomSources"], [])
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m unittest test.test_secret_prompts -v -k BuildPrompts -k Record -k Cli`
Expected: `TestBuildPrompts` fails because the house template is rendered; `TestCli` fails with `SystemExit` or missing output.

- [ ] **Step 3: Imports and `build_prompts`**

At the top of `generate-npc.py`, beside `import art_styles`:

```python
import secret_prompts
```

Beside `extra_sentence()` add:

```python
def warn_token_limit(prompts):
    """The over-limit warning both prompt builders print, on stderr."""
    for label, text in zip(("portrait", "token"), prompts):
        n = estimate_tokens(text)
        if n > TOKEN_LIMIT:
            print("! %s prompt is about %d tokens, over Krea 2's %d-token limit - the "
                  "tail will be truncated. Shorten the longest bullet it rolled."
                  % (label, n, TOKEN_LIMIT), file=sys.stderr)


def _secret_prompt_build(npc, template, fields, style, guidance, parts_only):
    """Both prompts from the NPC's secret prompt snapshot, not the house templates.

    The template's two texts are filled from the same field dict the house
    templates get plus the NPC's name, then the selected art style is applied
    exactly as for a house prompt. A selected colour guidance sentence is
    appended before the style line; the house glow and palette sentences are
    never added - the template author decides what the prompt says.
    """
    import prompt_composer
    fields = dict(fields, name=npc["name"])
    extra = npc.get("_extra") or {}
    palette = guidance["prompt"].strip() if color_guidance.is_custom(guidance) else ""
    prompts, parts = [], {}
    for target in ("portrait", "token"):
        text = secret_prompts.fill(template[target], fields, extra)
        if palette:
            text = "%s %s" % (text, palette)
        prompts.append(art_styles.apply_style(text, style))
        if parts_only:
            pieces = secret_prompts.parts(template[target], fields, extra)
            if palette:
                pieces.append(prompt_composer._part("text:guidance", " " + palette))
            parts[target] = prompt_composer._restyle(pieces, style)
    if parts_only:
        return parts
    warn_token_limit(prompts)
    return tuple(prompts)
```

In `build_prompts`, right after `fields["identity"] = ", ".join(identity) or "a person"` (line 3644):

```python
    # A secret prompt replaces both house templates from here on. Everything
    # above computed the fields a template may read; everything below is the
    # house prompt's own composition.
    template = npc.get("_secret_prompt")
    if template:
        return _secret_prompt_build(npc, template, fields, style, guidance, _parts)
```

Replace the token-limit loop at the end of `build_prompts` (lines 3755-3760) with `warn_token_limit(prompts)`.

- [ ] **Step 4: Record and dossier**

In `extra_record()`, after the `promptLayout` line:

```python
    if npc.get("_secret_prompt"):
        record["secretPrompt"] = dict(npc["_secret_prompt"])
```

In `npc_from_entry()`, after the `promptLayout` restore:

```python
    if entry.get("secretPrompt"):
        npc["_secret_prompt"] = dict(entry["secretPrompt"])
```

In `write_dossier()`, after `traits += list((npc.get("_extra") or {}).items())`:

```python
    if npc.get("_secret_prompt"):
        traits.append(("Secret prompt", "%s (%s)" % (npc["_secret_prompt"]["name"], npc["_secret_prompt"]["file"])))
```

- [ ] **Step 5: `main()`**

After the `--trait-odds` block (which returns at line 5448) and before the `unknown = [...]` override check, insert:

```python
    # Templates load before anything rolls: a broken file is a clean exit,
    # and the listing prints JSON alone on stdout, like --trait-odds.
    templates = None
    if args.secret_prompts:
        if args.list_secret_prompts:
            json.dump(secret_prompts.listing(args.secret_prompts, args.secret_tables_dir, tables,
                                             REQUIRED_TABLES, load_extra_tables), sys.stdout)
            return 0
        try:
            templates = secret_prompts.load(args.secret_prompts, args.secret_tables_dir, tables,
                                            REQUIRED_TABLES, load_extra_tables)
        except ValueError as exc:
            raise SystemExit("--secret-prompts: %s" % exc)
```

In the `--extra-value` parsing `try:` block, after `values[name] = value` loop and before `extra = load_extra_tables(...)`, keep the existing code but guard the extra load so a template run does not load `args.extra_tables` (which is empty anyway) and refuses a value naming no slot:

```python
        if templates:
            known = {t for tpl in templates.values() for t in tpl["secret_slots"]}
            stray = [name for name in values if name not in known]
            if stray:
                raise ValueError("--extra-value %s: no loaded secret prompt has that slot table (slots: %s)"
                                 % (", ".join(stray), ", ".join(sorted(known)) or "none"))
```

Replace the per-NPC roll (the three lines `npc = roll_npc(...)`, `npc["_extra"] = roll_extra(extra, rng)`, `npc["_extra_targets"] = dict(targets)`) with:

```python
        template = None
        if templates:
            template = secret_prompts.choose(templates, args.secret_prompt, seed)
            try:
                pinned = secret_prompts.merge_pins(template, overrides)
            except ValueError as exc:
                raise SystemExit(str(exc))
            npc = roll_npc(tables, rng, pinned, args.unarmed, adults_only=True)
            # Only the tables the template reads roll, from the same generator
            # after the base roll - see roll_extra().
            try:
                slot_tables = load_extra_tables(
                    template["tables"], template["secret_slots"],
                    {name: value for name, value in values.items() if name in template["secret_slots"]})
            except ValueError as exc:
                raise SystemExit("--secret-prompts: %s" % exc)
            npc["_extra"] = roll_extra(slot_tables, rng)
            npc["_extra_targets"] = {}
            npc["_secret_prompt"] = secret_prompts.snapshot(template)
        else:
            npc = roll_npc(tables, rng, overrides, args.unarmed)
            # From the same generator, after the base roll, so the default tables
            # see the stream they always have - see roll_extra().
            npc["_extra"] = roll_extra(extra, rng)
            npc["_extra_targets"] = dict(targets)
```

Note `load_extra_tables(..., only=...)` with an empty `only` list loads every table in the files - a template with no secret slots must roll nothing, so pass `template["secret_slots"] or None` and, when it is empty, skip the load entirely: `slot_tables = load_extra_tables(...) if template["secret_slots"] else {}`.

In the `--prompt-preview` branch, after `fixed.update(values)`:

```python
            if template:
                fixed.update(template["pins"])
```

In the dry-run loop, after the `print("    %s, %s" % (npc["Role"], ...))` line:

```python
            if npc.get("_secret_prompt"):
                print("    secret prompt: %s (%s)" % (npc["_secret_prompt"]["name"], npc["_secret_prompt"]["file"]))
```

- [ ] **Step 6: Run the tests**

Run: `python -m unittest test.test_secret_prompts -v`
Expected: all pass. Then `python -m unittest test.test_extra_tables test.test_prompt_composer test.test_art_styles -v` still passes.

- [ ] **Step 7: Commit**

```bash
git add generate-npc.py test/test_secret_prompts.py
git commit -m "roll and record secret prompt templates" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 9: regeneration - slot re-roll and the adults-only rule on regen

**Files:**
- Modify: `generate-npc.py:5179-5213` (`regenerate_one`, the `--reroll-trait` block)
- Test: `test/test_secret_prompts.py`

**Interfaces:**
- Consumes: `secret_prompts.snapshot_secret_slots()`, `load_extra_tables`, `roll_extra`.
- Produces: `--reroll-trait <slot table>` on an entry with `secretPrompt` re-rolls just that slot from the snapshot's `tables` files and persists it; any other extra-table name falls through to `reroll_trait()`'s existing refusal.

- [ ] **Step 1: Write the failing tests**

Append to `test/test_secret_prompts.py`:

```python
class TestRegeneration(unittest.TestCase):
    def setUp(self):
        self.ws = Workspace(self)
        self.private = self.ws.root / "private"
        self.private.mkdir()
        npc = rolled_with_template(self.ws)
        self.entry = manifest_entry(seed=3)
        self.entry.update({"secret": True, "seed": 3, "files": [], "portrait": None, "token": None})
        gen.persist_traits(self.entry, npc)
        gen.persist_flags(self.entry, npc)
        self.manifest = self.private / "manifest.json"
        self.manifest.write_text(json.dumps({str(self.private / "npcs" / "Test"): self.entry}), encoding="utf-8")

    def run_regen(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = gen.main(["--tables", str(FIXTURE_TABLES), "--secret", "--secret-config", str(self.ws.config),
                             "--regen-manifest", str(self.manifest), "--regen-id", self.entry["id"],
                             "--apply-only"] + list(argv))
        return code, out.getvalue(), err.getvalue()

    def saved(self):
        return next(iter(json.loads(self.manifest.read_text(encoding="utf-8")).values()))

    def test_a_slot_table_rerolls_and_persists(self):
        self.ws.write_tables("tables.md", TABLES_MD.replace("- x2 kneeling upright with knees spread\n", ""))
        code, out, err = self.run_regen("--reroll-trait", "Poses", "--new-seed", "9")
        self.assertEqual(code, 0, err)
        self.assertIn("re-rolled Poses", err)
        saved = self.saved()
        self.assertEqual(saved["extraTraits"]["Poses"], "lying on her back with legs raised")
        self.assertEqual(saved["secretPrompt"]["name"], "Kneeling")
        self.assertTrue(saved["artStale"])

    def test_an_unknown_extra_name_is_still_refused(self):
        with self.assertRaises(SystemExit) as caught:
            self.run_regen("--reroll-trait", "Nope", "--new-seed", "9")
        self.assertIn("Nope", str(caught.exception))

    def test_set_trait_refuses_a_young_age_on_a_templated_entry(self):
        with self.assertRaisesRegex(SystemExit, "adults only"):
            self.run_regen("--set-trait", "Age=in {possessive} late teens || young", "--new-seed", "9")

    def test_a_trait_reroll_keeps_the_snapshot(self):
        code, _, err = self.run_regen("--reroll-trait", "Hair", "--new-seed", "9")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.saved()["secretPrompt"], self.entry["secretPrompt"])
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m unittest test.test_secret_prompts -v -k Regeneration`
Expected: `test_a_slot_table_rerolls_and_persists` raises `SystemExit` from `reroll_trait` ("cannot re-roll that one").

- [ ] **Step 3: Implement**

In `regenerate_one`, replace `rerolled = None` and the line `if args.reroll_trait:` with:

```python
    rerolled = None
    snapshot = npc.get("_secret_prompt")
    slot_tables = secret_prompts.snapshot_secret_slots(snapshot) if snapshot else []
    if args.reroll_trait and args.reroll_trait in slot_tables:
        # A secret prompt slot: drawn again from the tables file the snapshot
        # recorded, everything else reproduced. No cascade - a private table
        # gates nothing.
        try:
            rows = load_extra_tables(snapshot["tables"], [args.reroll_trait])
        except ValueError as exc:
            raise SystemExit("--reroll-trait %s: %s" % (args.reroll_trait, exc))
        before = dict(npc.get("_extra") or {})
        rerolled = roll_extra(rows, random.Random(
            args.new_seed if args.new_seed is not None else entry["seed"]))[args.reroll_trait]
        npc.setdefault("_extra", {})[args.reroll_trait] = rerolled
        say("re-rolled %s: %r -> %r" % (args.reroll_trait, before.get(args.reroll_trait), rerolled))
    elif args.reroll_trait:
```

(the rest of the original block stays as the body of that `elif`, re-indented by nothing - it was already inside the `if`).

- [ ] **Step 4: Run the tests**

Run: `python -m unittest test.test_secret_prompts -v`
Expected: all pass. `test_a_trait_reroll_keeps_the_snapshot` relies on Task 7's `kept` change.

- [ ] **Step 5: Commit**

```bash
git add generate-npc.py test/test_secret_prompts.py
git commit -m "re-roll a single secret prompt slot on regeneration" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 10: README, gitignore, and the generator's full test run

**Files:**
- Modify: `README.md` (after the `--disable-table` paragraph and the powershell example, before "`prompts/secret-tables/` is gitignored")
- Modify: `.gitignore` (after `prompts/secret-tables`)

- [ ] **Step 1: Document the flags and the format**

Insert into `README.md` before the line beginning "`prompts/secret-tables/` is gitignored":

````markdown
A *secret prompt* replaces both house templates with one of your own, in
Secret mode only. `--secret-prompts PATH` (repeatable) loads a markdown file of
templates and `--secret-prompt NAME` picks one by name, or `random` for a
weighted draw per NPC that never moves the base NPC a seed rolls:

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

### token
A full-body figure of {npc:identity}, {secret:Standing/Squatting Poses},
{secret:Clothing States}, against an empty plain white background.
```

`tables:` names files in the secret tables folder (`--secret-tables-dir`,
default the `secret-tables` sibling of the template file's folder). `{npc:…}`
reads the rolled NPC - `identity`, `hair`, `eyes`, `skin`, `outfit`, `stance`,
`backdrop`, `shot`, `name`, the pronoun fields and the rest of the list
`generate-npc.py --help` prints on an error - and `{secret:Table}` rolls one
row of a table from the `tables:` files, once per NPC however often it is
used; `{{` and `}}` are literal braces. `weight:` steers `random`; `pin:`
forces a default table's bullet, the way `--set-trait` does. Every template
pins adults only: an Age flagged `young` cannot be rolled, pinned or forced
while a secret prompt is active. `--prompt-layout`, `--disable-table` and the
`--extra-*` flags except `--extra-value` are refused beside a template, since
the template decides what appears and in what order. The chosen template is
saved on the manifest entry as `secretPrompt` (text included, so regeneration
works after the file changes), the dossier names it, and `--reroll-trait`
accepts any table the template reads. `--list-secret-prompts` prints the
templates as JSON for the Import GUI; a file with an error is listed with the
file, template and line. Templates live in `prompts/secret-prompts/`, which
is gitignored beside the tables.
````

- [ ] **Step 2: Ignore the folder**

In `.gitignore`, after `prompts/secret-tables`:

```
# Ignore personal prompt templates:
prompts/secret-prompts
```

- [ ] **Step 3: Run the generator suite**

Run: `python -m unittest discover -s test -v 2>&1 | tail -30`
Expected: only the seven pre-existing failures (memory rule); every `test_secret_prompts` case passes. If anything else fails, run the same file on `main` (`git stash` is forbidden; use `git worktree list` to find the main checkout and run there) before treating it as new.

- [ ] **Step 4: Commit**

```bash
git add README.md .gitignore
git commit -m "document secret prompts and ignore their folder" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

## Part B - content (main checkout, gitignored, never committed)

Both files below go into `G:\GIT-REPOS\lancer-art-generator\prompts\` in the MAIN checkout, not the worktree: the folders are gitignored and the worktree does not have them. Nothing in Part B is committed.

### Task 11: `prompts/secret-tables/explicit-table-3.md`

**Files:**
- Create: `G:\GIT-REPOS\lancer-art-generator\prompts\secret-tables\explicit-table-3.md`
- Leave untouched: `explict-table-2.md` (existing records and presets keep working - spec 5.1)

**Interfaces:**
- Produces the table names Task 12's templates reference: `Bespoke Entire Scenes`, `Subject Archetypes (Female)`, `Subject Archetypes (Futanari)`, `Futanari Details`, `Male Partner Archetypes`, `Kneeling Poses`, `Lying Down Poses`, `Sitting/Reclining Poses`, `Cream/Dripping Poses`, `Ahegao Expression Poses`, `Anal Presentation Poses`, `Oral/BJ Ready Poses`, `Masturbation/Insertion Poses`, `Standing/Squatting Poses`, `Sexual Actions`, `Sexual Intensity States`, `Anal Specific Actions`, `Body Fluids & Extras`, `Clothing States`, `Cum Finish Locations`, `Fetish Elements`, `Partnered Positions`, `Solo Framing`, `Partnered Framing`, `Body Details`, `Foot Details`.

Rules applied (spec 5.1): every row is a lowercase fragment with no leading "She"/"Her" and no trailing full stop; the nine pose groups are their own `##` tables; `Camera Angles & Framing` is split; `Participant Configuration` is dropped; `Primary Sex Acts` and `Sex Positions` merge into `Partnered Positions`; `Visibility Tags (Body Type)` becomes `Body Details` with the penis tags moved to a new `Futanari Details` table (the plan's reading of "join the futanari tables") and the feet/boots tags to `Foot Details`; every archetype row describes an adult. Three age-coded rows of v2 are dropped rather than rewritten ("Younger college age" is rewritten as early-twenties adult; "School uniform disheveled", "Age play schoolgirl outfit" are dropped) and "Prostate milking, male subject" is dropped because every template's subject is the NPC.

- [ ] **Step 1: Write the file**

```markdown
# Explicit Table - v3

Every row is a lowercase mid-sentence fragment for a secret prompt slot.
No leading pronoun, no trailing full stop; the template supplies both.

## Bespoke Entire Scenes

- x1 an adult woman lying prone on soft blush-pink sheets, body stretched and relaxed, face turned toward camera with dreamy parted lips, wearing a sheer black lace bodysuit with delicate long sleeves, the fabric clinging to her arched back as her hips lift from the mattress, while an adult man kneels over her from behind, muscular body leaning forward, one arm braced beside her shoulder, low three-quarter side angle, soft natural lighting, cozy bedroom interior with decorative wall art and warm wooden furniture slightly out of focus
- x1 an adult woman lying face down on a plush beige couch, body prone and relaxed into the cushions, hips raised and back arched in a gentle curve, one knee tucked beneath her and the other leg extended back along the couch, head turned to the side with her cheek resting against the upholstery and dark hair tousled across her shoulders, while an adult man kneels behind her on the couch with one hand on the small of her back, leaning forward, low side angle showing her full profile, soft natural window light, a living space with hints of a staircase in shallow depth of field
- x1 a platinum blonde adult woman with braided pigtails kneeling on a soft carpeted floor, looking up at the camera with an eager expression, mouth slightly open with her tongue visible, wearing a white cropped cheerleader top with red trim and a matching red skirt, large breasts exposed and resting heavily against her chest, thick white cum covering her face and dripping down her chin onto her breasts, glistening under harsh direct flash lighting that throws dramatic shadows and sharp highlights, one hand planted behind her for support, body angled toward the camera, steep overhead angle capturing face and torso in intimate close-up, dark out-of-focus background emphasizing her illuminated form, high contrast and glossy skin textures with photorealistic detail on fluids and skin

## Subject Archetypes (Female)

- x1 an adult hourglass bombshell with voluptuous curves and a tiny waist
- x1 a slim, petite adult spinner with a delicate frame and perky assets
- x1 an athletic adult gym body with defined muscles and a tight physique
- x1 an adult woman with voluptuous thick thighs, wide hips and soft feminine padding
- x1 a mature MILF with experienced confidence and a fuller figure
- x1 an early-twenties adult with a firm natural body and playful energy
- x1 an alternative tattooed goth adult with pale skin and a dark aesthetic
- x1 a platinum blonde adult with a bimbo aesthetic and enhanced proportions
- x1 an adult woman with a fresh girl-next-door look, natural beauty and an approachable air
- x1 a fiery adult redhead with pale freckled skin and wild curls
- x1 an adult woman of mixed heritage with striking features and golden skin
- x1 a porcelain-pale gothic adult with raven hair and dramatic makeup
- x1 a tanned adult beach babe with sun-kissed skin and bleached hair
- x1 an adult fitness competitor with muscular definition and low body fat
- x1 a plus-size adult BBW with abundant soft curves and confidence
- x1 a small-chested athletic adult with a runner's physique
- x1 an adult woman with huge natural breasts against a slim waist
- x1 an adult woman with enhanced fake breasts in a high round profile
- x1 an adult woman with an innocent look and subtle freckles
- x1 a severe adult dominatrix aesthetic in leather and latex

## Subject Archetypes (Futanari)

- x1 an adult feminine beauty with a massive horse-cock disproportionate to her frame
- x1 a cute, petite adult frame with an impressively thick throbbing member
- x1 an adult woman with voluptuous curves and a heavy hanging uncut cock between her thighs
- x1 an athletic, toned adult body with a veiny erect penis jutting upward
- x1 a modestly endowed adult with a small feminine penis and large balls
- x1 an adult woman with a massive erect phallus reaching toward her navel, balls heavy and full
- x1 an adult with soft feminine features contrasted by a thick veiny shaft
- x1 an adult woman with a long slender cock and smooth feminine testicles beneath her curves
- x1 an adult woman fully engorged and throbbing, precum dripping from the tip
- x1 an adult woman semi-hard and growing, stiffening before the viewer's eyes

## Futanari Details

- x1 her penis clearly visible and prominent
- x1 an implied penis bulge visible through her clothing

## Male Partner Archetypes

- x1 a tall muscular adult bodybuilder with defined abs and vascular arms
- x1 an average-build adult everyman with an approachable dad bod
- x1 a slim athletic adult man with a runner's build and lean muscles
- x1 a chubby adult bear type with a hairy chest and soft belly
- x1 a mature silver fox with distinguished gray hair and experience
- x1 an early-twenties adult man with endless stamina and smooth skin
- x1 a tattooed adult punk with a mohawk and an alternative aesthetic
- x1 a clean-cut adult business type in a partially unbuttoned dress shirt
- x1 a bearded adult lumberjack with a masculine hairy chest and strong arms
- x1 a shaven-headed dominant adult alpha male with an intense gaze
- x1 a nerdy adult intellectual with glasses and surprising confidence
- x1 a tanned adult surfer with a beach body and sun-bleached hair
- x1 a pale gothic adult man with dark hair and a mysterious vibe
- x1 a heavily tattooed adult man with full sleeves and piercings
- x1 an adult uniformed authority figure in partial uniform
- x1 an adult man of foreign heritage with striking features
- x1 a slender feminine adult twink with a smooth hairless body
- x1 a hairy-chested adult dad bod with masculine confidence
- x1 a chiseled-jawed adult male model with perfect bone structure
- x1 a masked or hooded anonymous adult man for mystery

## Kneeling Poses

- x1 kneeling upright with knees spread wide, hands resting on her thighs, back straight with her chest pushed forward, looking up with an inviting expression
- x1 sitting back on her heels with hands bound together above her head suggesting restraint, back arched, head tilted to expose her neck
- x1 kneeling with one hand on the floor for support and the other touching her own lips, leaning forward as if crawling toward the viewer
- x1 kneeling with knees together but parting at the ankles, hands on her knees, leaning forward with hair cascading down to obscure her face seductively
- x1 kneeling with legs spread and one hand between her thighs touching herself through her clothing, head thrown back with her mouth open in pleasure
- x1 kneeling on a soft carpeted floor with her body angled to show her curves

## Lying Down Poses

- x1 lying on her back with legs spread and bent, feet flat, hands above her head gripping an invisible headboard, back arched off the floor
- x1 prone on her stomach with legs bent and kicked up behind her, crossed at the ankles, chin resting on her hands, looking directly at the camera
- x1 lying on her side in a stretched fetal position, one hand between her thighs, the other pinching her own nipple through the fabric
- x1 lying on her back with her head hanging off the edge upside down, hair cascading toward the floor, arms reaching back, throat exposed
- x1 lying on her side with the top leg raised and bent, one hand sliding from breast to hip to thigh in a continuous caress
- x1 prone on cushions with hips raised and back arched in a gentle curve, body relaxed and inviting

## Sitting/Reclining Poses

- x1 sitting with legs spread wide and bent at the knees, leaning back on one hand, the other pulling at her neckline to expose her cleavage
- x1 reclining on one hip, propped up on an elbow, one leg bent and raised, running a hand down her own side and hip
- x1 sitting cross-legged but leaning forward, hands reaching toward the camera as if beckoning, breasts pressed together by her arms
- x1 lounging on her side with one leg bent and raised to obscure her groin while exposing her thigh, a hand resting on her own stomach
- x1 sitting with knees drawn up to her chest, arms wrapped around her legs, peeking over her knees with a shy but seductive expression

## Cream/Dripping Poses

- x1 lying on her back with legs spread and raised, cum dripping out and running down to her ass, one finger collecting it
- x1 sitting with legs spread, cum visible on her inner thighs and dripping from her pussy, a hand touching the mess and pulling away strings
- x1 standing with one leg raised on an invisible surface, cum running down her leg from under her skirt, a hand catching the drip
- x1 on her back with legs pulled up to her chest, cum pooled on her stomach and dripping down her sides, a satisfied smile on her face
- x1 kneeling with thighs pressed together, cum dripping from between her legs onto the floor, looking down at it

## Ahegao Expression Poses

- x1 leaning back on her hands with legs spread wide, eyes rolled back showing only the whites, tongue out and drooling, lost in pleasure
- x1 lying on her back with her head tilted sharply to the side, mouth open with her tongue lolling out, eyes crossed slightly, a hand on her breast
- x1 sitting with legs folded to one side and leaning forward, face contorted in orgasm, spit on her chin, a hand between her legs shaking
- x1 standing against an invisible wall with legs spread, head thrown back with her mouth wide open in a scream of pleasure, hands clawing at the wall
- x1 on hands and knees with hair covering her face, tongue hanging out to touch the floor, ass wiggling in the air, a hand between her legs moving frantically

## Anal Presentation Poses

- x1 on hands and knees with her chest pressed to the floor, one hand reaching back to spread her ass cheeks wide open, face turned to the camera
- x1 lying on her stomach with legs spread in a V, hands reaching back to pull her cheeks apart, looking back over her shoulder
- x1 standing bent forward with hands on her knees and legs spread, back arched to present her rear, one hand reaching back to touch her hole
- x1 kneeling with her chest down and ass high in the air, face pressed sideways to the floor, hands reaching back to spread herself
- x1 lying on her side with the top leg raised and held by a hand behind the knee, fully exposed from behind, the other hand spreading a cheek

## Oral/BJ Ready Poses

- x1 kneeling with hands behind her back as if bound, mouth open wide with her tongue extended flat, looking up with watery eyes, drool on her chin
- x1 sitting back on her heels with her head tilted all the way back, throat exposed and mouth open in a perfect O, hands on her own breasts
- x1 lying on her back with her head hanging off the edge, mouth open and ready, hair inverted, arms spread wide submissively
- x1 kneeling upright with two fingers in her mouth sucking wetly, pulling them out with a string of saliva, the other hand between her legs
- x1 crawling forward on her elbows with her mouth open and tongue out touching her own chin, looking up with begging eyes, ass raised high

## Masturbation/Insertion Poses

- x1 sitting with knees bent and spread, two fingers buried deep inside herself, the other hand rubbing her clit, head thrown back in ecstasy
- x1 lying on her back with legs pulled up to her shoulders, both hands working a toy or her fingers inside, mouth open in a silent moan
- x1 on hands and knees with one hand reaching back to plunge her fingers inside, back arched sharply, looking back with desperate eyes
- x1 reclining on her side with the top leg raised high holding her ankle, three fingers knuckle-deep inside, stomach muscles visibly tense
- x1 standing with legs crossed and a hand slipped down the front of her panties, fingers clearly moving beneath the fabric, biting her lower lip

## Standing/Squatting Poses

- x1 squatting low with knees spread wide and heels flat on the ground, one hand spreading herself open while looking down with fascination
- x1 standing with one leg raised high and bent, foot pressed against an invisible wall, hands holding her ankle to display herself fully spread
- x1 in a deep squat with knees together but thighs parted, hands on her knees pushing them apart, looking up with an ahegao expression and her tongue out
- x1 standing bent completely forward at the waist, hands gripping her ankles, legs straight and spread, hair pooling on the floor between her feet
- x1 in a one-legged stand with the other leg raised high in a standing split, hands holding the raised ankle, completely exposed and balanced

## Sexual Actions

- x1 being fucked from behind in doggy style, back arched, hips slamming back to meet each thrust
- x1 taking a thick cock deep in her pussy while lying on her back, legs wrapped tight around her partner's waist
- x1 riding cowgirl style with her breasts bouncing on each thrust, hands braced on her partner's chest
- x1 getting pounded in missionary with her legs spread wide and held down, back arching off the bed
- x1 being taken in reverse cowgirl, her ass slapping against his hips with each downward thrust
- x1 getting fucked standing up against a wall with one leg wrapped around her partner's waist, pinned helplessly
- x1 being penetrated deep in a piledriver position, legs over his shoulders, taking every inch
- x1 taking it from behind while bent over furniture, her hair pulled back forcefully, face flushed
- x1 getting railed in a prone bone position, face pressed into the sheets, ass raised and vulnerable
- x1 being double penetrated with both holes filled at once, overwhelmed with sensation
- x1 getting face-fucked on her knees, makeup running down her face, throat bulging
- x1 being lifted and fucked in a standing missionary against her partner, supported by strong arms
- x1 taking a massive cock balls deep in her tight pussy, stomach bulging from the size
- x1 getting pounded in a mating press, legs locked behind her partner's back, unable to escape
- x1 being fucked in a spooning position from behind, her partner's hand over her mouth
- x1 riding reverse cowgirl while her partner grabs her hips and pulls her down hard
- x1 getting drilled in a butterfly position on the edge of the bed, legs trembling uncontrollably
- x1 being taken anally while rubbing her clit, mixing pain and pleasure
- x1 getting spit-roasted between two partners, both ends filled completely
- x1 being fucked in a wheelbarrow position with her hands on the floor, body suspended and helpless

## Sexual Intensity States

- x1 moaning loudly as she gets pounded relentlessly, her voice echoing in the room
- x1 eyes rolling back from intense pleasure, whites showing, completely lost
- x1 gripping the sheets tightly as she is rammed deep, knuckles white
- x1 screaming in ecstasy from the hard thrusting, mouth wide open
- x1 body trembling from a continuous orgasm, shaking uncontrollably
- x1 drooling and mind-broken from pleasure overload, babbling incoherently
- x1 sweating and flushed from vigorous fucking, skin glistening
- x1 begging for more while getting railed harder, desperate and needy
- x1 an ahegao face from being fucked senseless, tongue out and eyes crossed
- x1 a creampie dripping from her used pussy, running down her thighs
- x1 her cervix pounded by an oversized cock, the deep penetration visible
- x1 her womb bulging from deep penetration, her stomach showing the outline
- x1 stretched to her limits around a thick shaft, her pussy gripping tight
- x1 squirting while being pounded without mercy, fluids spraying
- x1 her clit throbbing visibly as she takes every inch, engorged and sensitive
- x1 nipples hard and sensitive while getting railed, erect and aching
- x1 body convulsing in continuous climax, multiple orgasms rolling through her
- x1 fucked until she is a trembling mess, completely spent and satisfied
- x1 being bred with a deep creampie, fertile and filled completely
- x1 gaping after intense rough sex, her pussy stretched and open

## Anal Specific Actions

- x1 anal gaping with her hole wide open, the pink interior visible and exposed
- x1 an anal creampie dripping out slowly, running down to her pussy
- x1 ass-to-mouth cleaning, tasting herself off the cock
- x1 a rimjob preparing her for anal, a tongue circling her tight hole
- x1 double anal with two cocks in her ass at once, stretched wide
- x1 anal beads being pulled out one by one, her hole gaping after each
- x1 a butt plug with its jewel visible, sparkling between her cheeks
- x1 rough anal pounding, balls-deep thrusts making her scream
- x1 a gentle slow anal entry, careful stretching and preparation
- x1 anal fingering and stretching, preparing for a larger insertion
- x1 extreme anal fisting, an arm buried deep inside her
- x1 a speculum holding her open with a view deep inside her ass
- x1 an enema clean-out, water filling and expelling
- x1 anal hook bondage, the metal hook inserted and tied to her hair
- x1 twerking on a cock anally, bouncing her ass up and down
- x1 reverse cowgirl anal, facing away while riding with her ass
- x1 deep piledriver anal, legs pushed back and her hole exposed
- x1 standing anal against a wall, pinned and taken from behind
- x1 anal missionary with her legs up, looking into her partner's eyes

## Body Fluids & Extras

- x1 excessive cum, buckets' worth covering her completely
- x1 female squirting ejaculation, spraying visibly
- x1 saliva dripping messily, wet and sloppy oral
- x1 an oiled-up shiny body, glistening and slick
- x1 sweat-glistening skin from exertion
- x1 tears from deepthroat, eyes watering and makeup running
- x1 runny mascara from crying, black streaks down her face
- x1 watersports, a golden shower on her face
- x1 watersports, a golden shower covering her body
- x1 pissing during penetration, losing control completely
- x1 light menstrual spotting, natural and unfiltered
- x1 spit-roasted between two partners, saliva connecting them
- x1 cum-swapping and snowballing between partners
- x1 cum play with her fingers, spreading and examining it
- x1 drool on her breasts, wet and messy cleavage
- x1 a wet-look oil everywhere, dripping and shiny
- x1 slimy tentacle alien fluids coating her
- x1 a lactation spray, breasts leaking and dripping milk
- x1 grool visible on her pussy, thick and white
- x1 precum dripping in a string, connecting the cock to her skin
- x1 thick white cum covering her face, dripping down her chin and onto her breasts

## Clothing States

- x1 completely nude, no clothing, bare skin exposed
- x1 lingerie pulled aside, crotchless and open
- x1 bra on but panties pulled down to her thighs
- x1 panties on but bra pulled down exposing her breasts
- x1 fully clothed but with her skirt lifted up around her waist
- x1 torn clothing ripped open, exposed through the tears
- x1 wet see-through clothing, the fabric clinging to her skin
- x1 stockings and heels only, otherwise completely naked
- x1 a corset cinched tight, nude below the waist
- x1 a business suit skirt hiked up, panties shifted to the side
- x1 yoga pants pulled down to her thighs, ass exposed
- x1 jeans unzipped and pulled down, trapped around her ankles
- x1 a dress hiked up around her waist, panties removed
- x1 a bikini pulled to the side for access, still technically on
- x1 a latex catsuit unzipped at the crotch, shiny and tight
- x1 a sports bra and shorts pulled aside for penetration
- x1 a wedding dress lifted up, defiled in her white gown
- x1 a maid outfit with no panties, easy access under the skirt
- x1 a leather harness with strategic holes, BDSM aesthetic

## Cum Finish Locations

- x1 a creampie, internal vaginal cum dripping out slowly
- x1 an anal creampie leaking out of her ass
- x1 a facial, thick ropes of cum across her features
- x1 cum in her mouth as she swallows, overflowing and dripping out
- x1 cum on her tits, pooling in her cleavage
- x1 cum on her stomach, splattered across her navel
- x1 cum on her ass cheeks, dripping down between them
- x1 cum on her back, splattered across her spine
- x1 cum on her feet, painted on her soles
- x1 cum in her hair, sticky and matting her locks
- x1 cum on her clothing while dressed, ruining her outfit
- x1 multiple facials from a group, completely covered
- x1 excessive cum covering her whole body, drenched completely
- x1 cum in her open palm, examining the load
- x1 cum on her glasses, obscuring her vision
- x1 cum on food that she then eats, perverted consumption
- x1 cum on a mirror that she licks off, tasting it from her reflection
- x1 a creampie dripping out in close-up, detailed view
- x1 cum on her pussy externally only, covering her lips
- x1 cum on her armpit, an unusual fetish placement

## Fetish Elements

- x1 bondage with her wrists tied above her head, restrained and helpless
- x1 bondage spread-eagle on the bed, completely immobilized
- x1 blindfolded sensory deprivation, unable to see what is coming
- x1 a collar and leash, submissive, led and controlled
- x1 handcuffed and restrained, the metal cuffs digging into her wrists
- x1 a shibari rope harness with intricate knots and patterns
- x1 a ball gag in her mouth, drooling around the restraint
- x1 nipple clamps attached with a chain connecting them
- x1 a butt plug inserted, its jewel or tail visible
- x1 a vibrator inserted or held on her clit, forced stimulation
- x1 whipping marks on her skin, red welts across her back or ass
- x1 choking breath play, a hand around her throat
- x1 spanking, red handprints, her ass glowing red
- x1 nurse and doctor medical play on an examination table
- x1 police officer arrest play, a power dynamic
- x1 a step-family roleplay scenario, a taboo dynamic
- x1 cuckold dirty talk, her husband watching
- x1 gloryhole anonymous sex, a disembodied cock
- x1 risky public sex, almost caught, the danger of exposure

## Partnered Positions

- x1 vaginal penetration only, traditional intercourse
- x1 anal penetration only, backdoor exclusively
- x1 an oral blowjob on her knees, servicing him
- x1 an oral blowjob lying down in a relaxed position
- x1 deepthroat face-fucking, throat penetration
- x1 receiving cunnilingus, her pussy licked
- x1 rimming, oral on her ass
- x1 tit-fucking between her breasts, paizuri
- x1 a handjob, manual stimulation with her hands
- x1 a footjob with skilled footwork
- x1 armpit fucking, an unusual fetish
- x1 thigh fucking between her closed legs
- x1 double penetration, vaginal and anal, filled completely
- x1 triple penetration with every hole filled, airtight
- x1 vaginal fisting, extreme stretching and insertion
- x1 anal fisting, extreme backdoor stretching
- x1 tribbing with another adult woman, grinding clit on clit
- x1 strap-on penetration by another adult woman
- x1 mutual oral in a 69, simultaneous pleasure
- x1 facesitting oral service with her on top
- x1 missionary with her legs wrapped around her partner
- x1 doggy style on hands and knees, the classic position
- x1 doggy style with her face pressed to the surface, submissive
- x1 cowgirl riding on top, in control
- x1 reverse cowgirl, facing away
- x1 spooning from behind, intimate and close
- x1 standing against a wall, pinned and taken
- x1 bent over furniture at a convenient height
- x1 missionary with her legs over his shoulders for deep penetration
- x1 a piledriver with her legs pushed back at an extreme angle
- x1 prone bone lying flat, a helpless position
- x1 seated on his lap facing him with intimate eye contact
- x1 seated on his lap facing away as he uses her
- x1 standing doggy from behind, supported while standing
- x1 side-by-side spooning penetration, lazy sex
- x1 a wheelbarrow position, suspended and helpless
- x1 a butterfly position on the edge of a surface, legs spread
- x1 a bridged position with her hips raised, arching her back
- x1 split-legged deep penetration, flexible and open
- x1 folded in half with her legs behind her head, maximum exposure

## Solo Framing

- x1 a close-up on her face capturing every expression
- x1 a close-up on her spread genitalia, an explicit anatomy focus
- x1 a wide environmental shot with the room and context visible
- x1 a low angle looking up, emphasizing dominance
- x1 a high angle looking down, a voyeuristic view
- x1 a mirror reflection angle, watching herself
- x1 a voyeur's view through a doorway
- x1 from underneath looking up, a worm's-eye view
- x1 an overhead bird's-eye view looking straight down
- x1 an extreme close-up on her wetness, macro detail
- x1 full body with her face visible, a complete composition
- x1 cinematic shallow depth of field with artistic blur
- x1 an elevated bird's-eye perspective looking down at a slight angle
- x1 floor level looking upward, a dramatic low-angle view
- x1 a close-up intimate angle with shallow depth of field
- x1 a foot-of-the-bed wide establishing shot, straight-on

## Partnered Framing

- x1 a close-up on the penetration, explicit joined genitals
- x1 a close-up on her face reacting, capturing every expression
- x1 a medium shot of both full bodies, showing their complete forms
- x1 a wide environmental shot with the room and context visible
- x1 a POV from the man looking down, a dominant perspective
- x1 a POV from her looking up, a submissive perspective
- x1 a side-view profile showing depth and their connection
- x1 a rear view from behind, a doggy perspective
- x1 an over-the-shoulder POV shot from behind her partner
- x1 a focus on the joined genitals, the connection point
- x1 a low side angle capturing her full profile and the depth of the scene
- x1 a low three-quarter side angle, an intimate profile of their connection
- x1 a three-quarter rear perspective, low near mattress level
- x1 a foot-of-the-bed wide establishing shot, straight-on
- x1 split-screen multiple angles showing everything
- x1 cinematic shallow depth of field with artistic blur

## Body Details

- x1 a pregnant, fertile adult belly, glowing and round
- x1 bikini tan lines visible on her skin
- x1 freckles scattered naturally across her body
- x1 tattoos visible on her skin, inked artwork
- x1 pierced nipples and genitals with jewelry
- x1 enhanced fake lips, plumped and full
- x1 muscular defined abs, a visible six-pack
- x1 a very tall amazon stature, a towering presence
- x1 a short, petite adult frame, tiny and delicate
- x1 large dark areolas, prominent and pronounced
- x1 inverted nipples, unique anatomy
- x1 an outie with prominent visible labia
- x1 an innie with tucked labia, neat and compact

## Foot Details

- x1 her boots visible in frame
- x1 her bare feet visible in frame
```

- [ ] **Step 2: Check it loads**

From the generator worktree:

```powershell
python -c "import sys; sys.argv=['x']; import importlib.util; s=importlib.util.spec_from_file_location('g','generate-npc.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); t=m.load_extra_tables([r'G:\GIT-REPOS\lancer-art-generator\prompts\secret-tables\explicit-table-3.md']); print(len(t), 'tables'); print(sorted(t))"
```

Expected: `26 tables` and the list of names above. Every row must be lowercase-first: `python -c "..."` again with `print([v for rows in t.values() for v, _ in rows if v[0].isupper() or v.endswith('.')])` expected `[]`.

No commit (gitignored).

---

### Task 12: `prompts/secret-prompts/explicit-v1.md` and the quality check

**Files:**
- Create: `G:\GIT-REPOS\lancer-art-generator\prompts\secret-prompts\explicit-v1.md`

**Interfaces:**
- Consumes: the tables of Task 11, `lighting-atmosphere-1.md` (`## Lighting Atmosphere`), `setting-location-1.md` (`## Setting Location`), and the generator of Part A.

Every template follows spec 5.2's order (framing and subject, body archetype and NPC looks, pose or action, clothing state, partner if any, body details and fluids, camera, setting, lighting), names no medium, pins `Pronouns = she/her`, and gives the token one figure, whole body head to feet, on an empty plain white background with a `Standing/Squatting Poses` row and the clothing state, no partner and no penetration (spec 5.3).

- [ ] **Step 1: Write the file**

```markdown
# Explicit prompts - v1
tables: explicit-table-3.md, lighting-atmosphere-1.md, setting-location-1.md

## Solo kneeling
weight: 2
pin: Pronouns = she/her

### portrait
A portrait of {npc:identity}, {secret:Subject Archetypes (Female)}, with {npc:hair},
{npc:eyes} and {npc:skin}. {npc:Subject} {npc:is_are} {secret:Kneeling Poses},
{secret:Clothing States}, {secret:Body Details}. {secret:Solo Framing}, in
{secret:Setting Location}, {secret:Lighting Atmosphere}.

### token
A full-body figure of {npc:identity}, {secret:Subject Archetypes (Female)}, with
{npc:hair} and {npc:eyes}, {npc:possessive} whole body in frame from head to feet,
{secret:Standing/Squatting Poses}, {secret:Clothing States}, against an empty
plain white background.

## Solo lying down
weight: 2
pin: Pronouns = she/her

### portrait
A portrait of {npc:identity}, {secret:Subject Archetypes (Female)}, with {npc:hair},
{npc:eyes} and {npc:skin}. {npc:Subject} {npc:is_are} {secret:Lying Down Poses},
{secret:Clothing States}, {secret:Body Details}, {secret:Foot Details}.
{secret:Solo Framing}, in {secret:Setting Location}, {secret:Lighting Atmosphere}.

### token
A full-body figure of {npc:identity}, {secret:Subject Archetypes (Female)}, with
{npc:hair} and {npc:eyes}, {npc:possessive} whole body in frame from head to feet,
{secret:Standing/Squatting Poses}, {secret:Clothing States}, against an empty
plain white background.

## Solo reclining
weight: 2
pin: Pronouns = she/her

### portrait
A portrait of {npc:identity}, {secret:Subject Archetypes (Female)}, with {npc:hair},
{npc:eyes} and {npc:skin}, {npc:possessive} face carrying {npc:demeanor}.
{npc:Subject} {npc:is_are} {secret:Sitting/Reclining Poses}, {secret:Clothing States},
{secret:Body Details}. {secret:Solo Framing}, in {secret:Setting Location},
{secret:Lighting Atmosphere}.

### token
A full-body figure of {npc:identity}, {secret:Subject Archetypes (Female)}, with
{npc:hair} and {npc:eyes}, {npc:possessive} whole body in frame from head to feet,
{secret:Standing/Squatting Poses}, {secret:Clothing States}, against an empty
plain white background.

## Solo self-pleasure
weight: 2
pin: Pronouns = she/her

### portrait
A portrait of {npc:identity}, {secret:Subject Archetypes (Female)}, with {npc:hair},
{npc:eyes} and {npc:skin}. {npc:Subject} {npc:is_are}
{secret:Masturbation/Insertion Poses}, {secret:Clothing States}, {secret:Body Details},
{secret:Body Fluids & Extras}. {secret:Solo Framing}, in {secret:Setting Location},
{secret:Lighting Atmosphere}.

### token
A full-body figure of {npc:identity}, {secret:Subject Archetypes (Female)}, with
{npc:hair} and {npc:eyes}, {npc:possessive} whole body in frame from head to feet,
{secret:Standing/Squatting Poses}, {secret:Clothing States}, against an empty
plain white background.

## Couple scene
weight: 3
pin: Pronouns = she/her

### portrait
A scene of {npc:identity}, {secret:Subject Archetypes (Female)}, with {npc:hair},
{npc:eyes} and {npc:skin}, {secret:Clothing States}, with {secret:Male Partner Archetypes}.
{npc:Subject} {npc:is_are} {secret:Sexual Actions}, {secret:Partnered Positions},
{secret:Sexual Intensity States}, {secret:Body Details}, {secret:Cum Finish Locations}.
{secret:Partnered Framing}, in {secret:Setting Location}, {secret:Lighting Atmosphere}.

### token
A full-body figure of {npc:identity}, {secret:Subject Archetypes (Female)}, with
{npc:hair} and {npc:eyes}, alone, {npc:possessive} whole body in frame from head
to feet, {secret:Standing/Squatting Poses}, {secret:Clothing States}, against an
empty plain white background.

## Futanari solo
weight: 1
pin: Pronouns = she/her

### portrait
A portrait of {npc:identity}, {secret:Subject Archetypes (Futanari)}, with {npc:hair},
{npc:eyes} and {npc:skin}, {secret:Futanari Details}. {npc:Subject} {npc:is_are}
{secret:Standing/Squatting Poses}, {secret:Clothing States}, {secret:Body Details}.
{secret:Solo Framing}, in {secret:Setting Location}, {secret:Lighting Atmosphere}.

### token
A full-body figure of {npc:identity}, {secret:Subject Archetypes (Futanari)}, with
{npc:hair} and {npc:eyes}, {secret:Futanari Details}, {npc:possessive} whole body
in frame from head to feet, {secret:Standing/Squatting Poses}, {secret:Clothing States},
against an empty plain white background.

## Bespoke scene
weight: 1
pin: Pronouns = she/her

### portrait
{secret:Bespoke Entire Scenes}. The woman is {npc:identity}, with {npc:hair},
{npc:eyes} and {npc:skin}. {secret:Lighting Atmosphere}.

### token
A full-body figure of {npc:identity}, {secret:Subject Archetypes (Female)}, with
{npc:hair} and {npc:eyes}, {npc:possessive} whole body in frame from head to feet,
{secret:Standing/Squatting Poses}, {secret:Clothing States}, against an empty
plain white background.
```

- [ ] **Step 2: List it through the generator**

From the generator worktree, with a throwaway secret config (`--secret` needs one; nothing is written on a listing or a dry run):

```powershell
Set-Content -Path "$env:CLAUDE_JOB_DIR\tmp\secret.json" -Value '{"secretImagesDir": "C:\\Users\\Evan\\.claude\\jobs\\7dfdf198\\tmp\\private"}'
python generate-npc.py --secret --secret-config "$env:CLAUDE_JOB_DIR\tmp\secret.json" --secret-prompts "G:\GIT-REPOS\lancer-art-generator\prompts\secret-prompts\explicit-v1.md" --secret-tables-dir "G:\GIT-REPOS\lancer-art-generator\prompts\secret-tables" --list-secret-prompts
```

Expected: JSON with one file, seven templates, no `error` key. A `secret:` slot naming a table Task 11 spelled differently shows up here as `explicit-v1.md, '<template>', line <n>: {secret:...}: no such table`; fix the spelling in whichever file is wrong.

- [ ] **Step 3: Quality check (spec 5.4)**

Dry-run every template across several seeds and read the filled prompts for grammar and flow:

```powershell
foreach ($name in 'Solo kneeling','Solo lying down','Solo reclining','Solo self-pleasure','Couple scene','Futanari solo','Bespoke scene') {
  python generate-npc.py --secret --secret-config "$env:CLAUDE_JOB_DIR\tmp\secret.json" --secret-prompts "G:\GIT-REPOS\lancer-art-generator\prompts\secret-prompts\explicit-v1.md" --secret-tables-dir "G:\GIT-REPOS\lancer-art-generator\prompts\secret-tables" --secret-prompt $name --count 4 --seed 100 --dry-run
}
```

Read each portrait and token line. Things to fix in the template or table wording, not in code: a doubled article ("a a slim"), a role that reads oddly before an archetype, a `{npc:skin}` value that does not read after "and", a token over the 512-token warning. Record the seeds and any wording you changed in the final report; the user then renders a sample in ComfyUI and tunes from the results.

No commit (gitignored).

---

## Part C - import GUI (`lancer-npc-import-gui`, new worktree `secret-prompts`)

Before Task 13: create and enter the GUI worktree (see "Repositories and worktrees"). Run each test file alone with `node --test test/<file>`.

### Task 13: `secretPromptsDir` in `lib/paths.js`

**Files:**
- Modify: `lib/paths.js:75-76` (after `secretTablesDir`) and the returned object
- Test: `test/paths.test.js` (append)

**Interfaces:**
- Produces: `derivePaths(config).secretPromptsDir` - `config.secretPromptsDir`, else `path.join(path.dirname(secretTablesDir), 'secret-prompts')`.

- [ ] **Step 1: Write the failing test**

Append to `test/paths.test.js` (it already requires `derivePaths` and `path`):

```js
test('secretPromptsDir is the secret-prompts sibling of the secret tables folder, unless configured', () => {
    const derived = derivePaths({ npcManifestPath: 'G:/gen/.generated-npcs.json' });
    assert.equal(derived.secretPromptsDir, path.join('G:/gen', 'prompts', 'secret-prompts'));
    const moved = derivePaths({ npcManifestPath: 'G:/gen/.generated-npcs.json', secretTablesDir: 'D:/mine/tables' });
    assert.equal(moved.secretPromptsDir, path.join('D:/mine', 'secret-prompts'));
    const explicit = derivePaths({ npcManifestPath: 'G:/gen/.generated-npcs.json', secretPromptsDir: 'E:/prompts' });
    assert.equal(explicit.secretPromptsDir, 'E:/prompts');
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `node --test test/paths.test.js`
Expected: the new test fails with `undefined !== 'G:\\gen\\prompts\\secret-prompts'`.

- [ ] **Step 3: Implement**

After the `secretTablesDir` block in `lib/paths.js`:

```js
    // The user's secret prompt templates, read by generate-npc.py's
    // --secret-prompts. A sibling of the secret tables folder rather than
    // of the tables file, so a GM who moved their tables folder finds the
    // templates beside it.
    const secretPromptsDir = config.secretPromptsDir
        || path.join(path.dirname(secretTablesDir), 'secret-prompts');
```

and add `secretPromptsDir` to the returned object after `secretTablesDir`.

- [ ] **Step 4: Run the tests**

Run: `node --test test/paths.test.js`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add lib/paths.js test/paths.test.js
git commit -m "derive the secret prompts folder" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 14: `lib/secretPrompts.js` and the stub generator

**Files:**
- Create: `lib/secretPrompts.js`
- Create: `test/helpers/secretPromptsStub.js`
- Create: `test/secretPrompts.test.js`

**Interfaces:**
- Produces:
  - `isSecretPromptsFileName(name) -> bool` (a bare `*.md` name, no separators).
  - `listSecretPrompts({ dir, script, tablesPath, tablesDir, configFile, artStylesPath, executable }) -> Promise<{dir, exists, files}>`; a missing folder resolves `{dir, exists: false, files: []}` without spawning; an empty one `{dir, exists: true, files: []}`; otherwise it runs the generator with `--list-secret-prompts` and passes its `files` through.
  - `validateSelection(raw, listing) -> null | {file: absolute path, name}`; throws on an unknown or broken file, a bad name.
  - `normaliseSelection(raw) -> null | {file, name}` for presets (shape only).
  - `secretSlots(snapshot) -> string[]`.
  - `test/helpers/secretPromptsStub.js` exports `STUB`, the Node source of a fake `generate-npc` that echoes its argv, answers `--prompt-preview` with fragments plus `argv`, answers `--list-secret-prompts` by reading each `--secret-prompts` file, and carries the `REROLLABLE_TRAITS`/`DISABLEABLE_TABLES` comment `lib/overrideTables.js` scrapes.

- [ ] **Step 1: Write the stub**

`test/helpers/secretPromptsStub.js`:

```js
/**
 * A Node script standing in for generate-npc.py in the secret prompt tests.
 * Echoes its argv (so a create's command line can be asserted on), answers
 * --prompt-preview with fragments, and answers --list-secret-prompts by
 * reading each --secret-prompts file: a '## Name' line is a template, and a
 * file whose first line is 'broken' is listed with an error. The comment
 * block carries the constants lib/overrideTables.js scrapes.
 */
const STUB = [
    '/*',
    'REQUIRED_TABLES = [',
    '    "Pronouns", "Age", "Gear",',
    ']',
    'REROLLABLE_TRAITS = ("Gear",)',
    'RAW_REROLLABLE_TRAITS = tuple(t for t in REQUIRED_TABLES if t not in ("Pronouns"))',
    'DISABLEABLE_TABLES = (',
    '    "Stance", "Gear",',
    ')',
    '*/',
    'const fs = require("fs"), path = require("path");',
    'const argv = process.argv.slice(2);',
    'if (argv.includes("--list-secret-prompts")) {',
    '  const files = argv.flatMap((a, i) => a === "--secret-prompts" ? [argv[i + 1]] : []);',
    '  console.log(JSON.stringify({ dir: path.dirname(files[0]), files: files.map(file => {',
    '    const text = fs.readFileSync(file, "utf8");',
    '    if (text.startsWith("broken")) return { file: path.basename(file), error: `${path.basename(file)}, line 1: broken on purpose` };',
    '    const templates = [...text.matchAll(/^## (.+)$/gm)].map(m => ({ name: m[1], weight: 1,',
    '      pins: { Pronouns: "she/her" }, npcSlots: ["identity"], secretSlots: ["Poses", "Clothing"] }));',
    '    return { file: path.basename(file), templates };',
    '  }) }));',
    '} else if (argv.includes("--prompt-preview")) {',
    '  console.log(JSON.stringify({ portrait: [{ id: "npc:identity", text: "a mechanic", sources: ["Role"], randomSources: ["Role"] },',
    '    { id: "secret:Poses", text: " kneeling", sources: ["Poses"], randomSources: ["Poses"] }], token: [], argv }));',
    '} else console.log(argv.join(" "));',
].join('\n');

module.exports = { STUB };
```

- [ ] **Step 2: Write the failing unit tests**

`test/secretPrompts.test.js`:

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { STUB } = require('./helpers/secretPromptsStub');
const { isSecretPromptsFileName, listSecretPrompts, validateSelection, normaliseSelection, secretSlots } = require('../lib/secretPrompts');

/*
 * The Secret prompt select of Create NPC is built from the generator's own
 * --list-secret-prompts, so the parser lives in one place. These tests run
 * the listing against a Node stub of the generator and check the pure
 * validation around it.
 */

function folder(t, files) {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'secret-prompts-'));
    t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
    for (const [name, text] of Object.entries(files)) fs.writeFileSync(path.join(dir, name), text);
    return dir;
}

function options(t, dir) {
    const script = path.join(folder(t, { 'generate-npc.js': STUB }), 'generate-npc.js');
    return { dir, script, tablesPath: 'tables.md', tablesDir: path.join(dir, '..', 'secret-tables'),
        configFile: 'config.json', artStylesPath: 'art-styles.json', executable: process.execPath };
}

test('file names are bare .md names', () => {
    for (const ok of ['a.md', 'Explicit v1.MD']) assert.ok(isSecretPromptsFileName(ok), ok);
    for (const bad of ['a.json', '../a.md', 'x/a.md', 'x\\a.md', '.md', '', null, 7]) assert.ok(!isSecretPromptsFileName(bad), String(bad));
});

test('a missing folder lists nothing without running the generator', async (t) => {
    const missing = path.join(folder(t, {}), 'nope');
    const listing = await listSecretPrompts({ ...options(t, missing), executable: 'no-such-binary' });
    assert.deepEqual(listing, { dir: missing, exists: false, files: [] });
});

test('an empty folder is empty, and a folder of files is listed through the generator', async (t) => {
    const empty = folder(t, { 'notes.txt': 'ignored' });
    assert.deepEqual(await listSecretPrompts(options(t, empty)), { dir: empty, exists: true, files: [] });
    const dir = folder(t, { 'b.md': '## Two\n', 'a.md': '## One\n## Uno\n', 'broken.md': 'broken\n', 'x.json': '{}' });
    const listing = await listSecretPrompts(options(t, dir));
    assert.equal(listing.exists, true);
    assert.deepEqual(listing.files.map(f => f.file), ['a.md', 'b.md', 'broken.md']);
    assert.deepEqual(listing.files[0].templates.map(t => t.name), ['One', 'Uno']);
    assert.match(listing.files[2].error, /broken\.md, line 1/);
});

test('the generator is run with the secret, tables and listing flags', async (t) => {
    const dir = folder(t, { 'a.md': '## One\n' });
    const seen = folder(t, {});
    const spy = path.join(seen, 'spy.js');
    fs.writeFileSync(spy, 'require("fs").writeFileSync(process.argv[2] + ".argv", JSON.stringify(process.argv.slice(2)));\n' + STUB);
    await listSecretPrompts({ ...options(t, dir), script: spy });
    const argv = JSON.parse(fs.readFileSync(spy + '.argv', 'utf8'));
    assert.equal(argv[0], spy);
    for (const flag of ['--secret', '--secret-config', '--art-styles', '--tables', '--secret-tables-dir', '--list-secret-prompts']) assert.ok(argv.includes(flag), flag);
    assert.ok(argv.includes(path.join(dir, 'a.md')));
});

test('a generator failure is a readable error', async (t) => {
    const dir = folder(t, { 'a.md': '## One\n' });
    const bad = path.join(folder(t, {}), 'bad.js');
    fs.writeFileSync(bad, 'console.error("boom"); process.exit(2);');
    await assert.rejects(listSecretPrompts({ ...options(t, dir), script: bad }), /boom/);
    const junk = path.join(folder(t, {}), 'junk.js');
    fs.writeFileSync(junk, 'console.log("not json");');
    await assert.rejects(listSecretPrompts({ ...options(t, dir), script: junk }), /did not return a secret prompt listing/);
});

test('a selection must name a listed, valid file and a template in it', () => {
    const listing = { dir: 'D:/p', files: [
        { file: 'a.md', templates: [{ name: 'One' }] },
        { file: 'broken.md', error: 'broken.md, line 1: broken' },
    ] };
    assert.equal(validateSelection(null, listing), null);
    assert.equal(validateSelection(undefined, listing), null);
    assert.deepEqual(validateSelection({ file: 'a.md', name: 'One' }, listing), { file: path.join('D:/p', 'a.md'), name: 'One' });
    assert.deepEqual(validateSelection({ file: 'a.md', name: 'random' }, listing), { file: path.join('D:/p', 'a.md'), name: 'random' });
    for (const [raw, pattern] of [
        [{ file: '../a.md', name: 'One' }, /unknown secret prompts file/],
        [{ file: 'missing.md', name: 'One' }, /unknown secret prompts file "missing.md"/],
        [{ file: 'broken.md', name: 'random' }, /broken\.md: broken\.md, line 1/],
        [{ file: 'a.md', name: 'Two' }, /a\.md has no secret prompt "Two"/],
        [{ file: 'a.md', name: '' }, /name/],
        [{ file: 'a.md' }, /name/],
        ['a.md', /secretPrompt must be/],
        [['a.md', 'One'], /secretPrompt must be/],
    ]) assert.throws(() => validateSelection(raw, listing), pattern, JSON.stringify(raw));
});

test('presets keep the selection by shape alone', () => {
    assert.equal(normaliseSelection(null), null);
    assert.deepEqual(normaliseSelection({ file: 'a.md', name: 'One', extra: 1 }), { file: 'a.md', name: 'One' });
    assert.throws(() => normaliseSelection({ file: '../a.md', name: 'One' }), /file/);
    assert.throws(() => normaliseSelection({ file: 'a.md', name: '  ' }), /name/);
});

test('secretSlots reads every {secret:...} slot of a stored snapshot once', () => {
    assert.deepEqual(secretSlots({ portrait: 'A {secret:Poses}, {secret:Clothing States}.', token: '{secret:Poses} {secret: Lighting }' }),
        ['Poses', 'Clothing States', 'Lighting']);
    assert.deepEqual(secretSlots(null), []);
    assert.deepEqual(secretSlots({ portrait: 'no slots {{here}}' }), []);
});
```

- [ ] **Step 3: Run to verify they fail**

Run: `node --test test/secretPrompts.test.js`
Expected: `Cannot find module '../lib/secretPrompts'`.

- [ ] **Step 4: Implement `lib/secretPrompts.js`**

```js
/**
 * Secret prompts: the user's fill-in-the-blank prompt templates for Secret
 * mode, read by generate-npc.py's --secret-prompts. The listing runs the
 * generator's own --list-secret-prompts so there is exactly one parser of
 * the file format; this module only lists the folder, validates a
 * selection against that listing, and reads the slot tables out of a
 * stored record's snapshot so the gallery can offer to re-roll them.
 */
const fs = require('node:fs');
const path = require('node:path');
const { execFile } = require('node:child_process');

const FILE_NAME_RE = /^[^\\/]+\.md$/i;

function isSecretPromptsFileName(name) {
    return typeof name === 'string' && FILE_NAME_RE.test(name) && name.toLowerCase() !== '.md';
}

function promptFiles(dir) {
    let entries;
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return null; }
    return entries.filter(entry => entry.isFile() && isSecretPromptsFileName(entry.name))
        .map(entry => entry.name).sort((a, b) => a.localeCompare(b));
}

/**
 * { dir, exists, files } where files is the generator's own listing: each
 * { file, templates: [{ name, weight, pins, npcSlots, secretSlots }] } or
 * { file, error }. A missing folder is exists: false with no files, like
 * listSecretTables; nothing is spawned for it or for an empty folder.
 */
function listSecretPrompts({ dir, script, tablesPath, tablesDir, configFile, artStylesPath, executable }) {
    const names = promptFiles(dir);
    if (names === null) return Promise.resolve({ dir, exists: false, files: [] });
    if (!names.length) return Promise.resolve({ dir, exists: true, files: [] });
    const args = [script, '--secret', '--secret-config', configFile, '--art-styles', artStylesPath,
        '--tables', tablesPath, '--secret-tables-dir', tablesDir, '--list-secret-prompts',
        ...names.flatMap(name => ['--secret-prompts', path.join(dir, name)])];
    return new Promise((resolve, reject) => {
        execFile(executable, args, { cwd: path.dirname(script), windowsHide: true, timeout: 15000, maxBuffer: 1024 * 1024,
            encoding: 'utf8', env: { ...process.env, PYTHONIOENCODING: 'utf-8' } }, (error, stdout, stderr) => {
            if (error) return reject(new Error(stderr.trim() || 'Could not list secret prompts. Check that the generator supports --list-secret-prompts.'));
            let data;
            try { data = JSON.parse(stdout); } catch { data = null; }
            if (!data || !Array.isArray(data.files)) {
                return reject(new Error('The generator did not return a secret prompt listing. Update lancer-art-generator.'));
            }
            resolve({ dir, exists: true, files: data.files });
        });
    });
}

/** The create request's secretPrompt, resolved to the file's path - or null for none. */
function validateSelection(raw, listing) {
    if (raw === null || raw === undefined) return null;
    if (typeof raw !== 'object' || Array.isArray(raw)) throw new Error('secretPrompt must be {file, name}');
    const { file, name } = raw;
    const known = isSecretPromptsFileName(file) && listing.files.find(entry => entry.file === file);
    if (!known) throw new Error(`unknown secret prompts file "${file}"`);
    if (known.error) throw new Error(`${file}: ${known.error}`);
    if (typeof name !== 'string' || !name.trim()) throw new Error('secret prompt name must be a non-empty string');
    if (name !== 'random' && !(known.templates || []).some(template => template.name === name)) {
        throw new Error(`${file} has no secret prompt "${name}"`);
    }
    return { file: path.join(listing.dir, file), name };
}

/** A preset's secretPrompt: the shape is checked here, existence when it is used. */
function normaliseSelection(raw) {
    if (raw === null || raw === undefined) return null;
    if (typeof raw !== 'object' || Array.isArray(raw)) throw new Error('secretPrompt must be {file, name}');
    if (!isSecretPromptsFileName(raw.file)) throw new Error('secretPrompt.file must be a bare .md file name');
    if (typeof raw.name !== 'string' || !raw.name.trim()) throw new Error('secretPrompt.name must be a non-empty string');
    return { file: raw.file, name: raw.name };
}

/** Every {secret:Table} a stored snapshot's two texts read, in order, once. */
function secretSlots(snapshot) {
    if (!snapshot || typeof snapshot !== 'object') return [];
    const out = [];
    for (const key of ['portrait', 'token']) {
        for (const match of String(snapshot[key] || '').matchAll(/\{secret:([^{}]+)\}/g)) {
            const name = match[1].trim();
            if (name && !out.includes(name)) out.push(name);
        }
    }
    return out;
}

module.exports = { isSecretPromptsFileName, listSecretPrompts, validateSelection, normaliseSelection, secretSlots };
```

- [ ] **Step 5: Run the tests**

Run: `node --test test/secretPrompts.test.js`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add lib/secretPrompts.js test/secretPrompts.test.js test/helpers/secretPromptsStub.js
git commit -m "list and validate secret prompt templates through the generator" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 15: `createArgs` emits the template flags and drops the refused ones

**Files:**
- Modify: `lib/kinds.js:85-90`
- Test: `test/kinds.test.js` (append)

**Interfaces:**
- Consumes: `opts.secretPrompt = { file: absolute path, name }` from the route (Task 16).
- Produces: `KINDS.npc.createArgs(opts)` with a `secretPrompt` appends `--secret-prompts <file> --secret-prompt <name>` and never emits `--extra-tables`, `--extra-table`, `--extra-target`, `--disable-table` or `--prompt-layout`; `--extra-value` still passes.

- [ ] **Step 1: Write the failing test**

Append to `test/kinds.test.js` (it already builds `KINDS` from a fixture config):

```js
test('a secret prompt adds its two flags and silences the composition flags', () => {
    const base = { count: 1, seed: null, overrides: [], extraTables: ['D:/t/a.md'], extraTableNames: ['one'],
        extraValues: [{ table: 'Poses', value: 'kneeling' }], extraTargets: [{ table: 'one', target: 'token' }],
        disabledTables: ['Stance'], promptLayout: { portrait: ['shot'] } };
    const plain = KINDS.npc.createArgs(base).join(' ');
    assert.match(plain, /--extra-tables D:\/t\/a\.md --extra-table one --extra-value Poses=kneeling --extra-target one=token --disable-table Stance --prompt-layout/);
    assert.doesNotMatch(plain, /--secret-prompt/);
    const templated = KINDS.npc.createArgs({ ...base, secretPrompt: { file: 'D:/p/explicit-v1.md', name: 'Solo kneeling' } });
    const joined = templated.join(' ');
    assert.ok(templated.includes('--secret-prompts') && templated[templated.indexOf('--secret-prompts') + 1] === 'D:/p/explicit-v1.md');
    assert.ok(templated[templated.indexOf('--secret-prompt') + 1] === 'Solo kneeling');
    assert.match(joined, /--extra-value Poses=kneeling/);
    for (const flag of ['--extra-tables', '--extra-table ', '--extra-target', '--disable-table', '--prompt-layout']) {
        assert.ok(!joined.includes(flag), flag);
    }
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `node --test test/kinds.test.js`
Expected: the new test fails on the `--secret-prompts` assertion.

- [ ] **Step 3: Implement**

Replace lines 85-90 of `lib/kinds.js` (the five `for` loops and the `promptLayout` line) with:

```js
            // A secret prompt template decides what appears and in what
            // order, so the composition flags are omitted beside one; the
            // generator refuses them outright. --extra-value still pins a
            // slot table's row.
            const templated = !!(opts.secretPrompt && opts.secretPrompt.file);
            if (!templated) {
                for (const file of opts.extraTables || []) args.push('--extra-tables', file);
                for (const name of opts.extraTableNames || []) args.push('--extra-table', name);
            }
            for (const { table, value } of opts.extraValues || []) args.push('--extra-value', `${table}=${value}`);
            if (!templated) {
                for (const { table, target } of opts.extraTargets || []) args.push('--extra-target', `${table}=${target}`);
                for (const name of opts.disabledTables || []) args.push('--disable-table', name);
                if (opts.promptLayout && Object.keys(opts.promptLayout).length) args.push('--prompt-layout', JSON.stringify(opts.promptLayout));
            } else {
                args.push('--secret-prompts', opts.secretPrompt.file, '--secret-prompt', opts.secretPrompt.name);
            }
```

- [ ] **Step 4: Run the tests**

Run: `node --test test/kinds.test.js test/api.createArgs.test.js`
Expected: pass (the untemplated argv order is unchanged).

- [ ] **Step 5: Commit**

```bash
git add lib/kinds.js test/kinds.test.js
git commit -m "pass a secret prompt template to the generator on create" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 16: server routes, presets and the gallery view

**Files:**
- Modify: `server.js` (require near line 2686; `handleCreateRequest` at 3039 and its `runner(...)` call at 3149; secret routes at 4033-4076; the reroll route at 4036-4046)
- Modify: `lib/secretPresets.js`
- Modify: `lib/secretGallery.js:45-58`
- Test: `test/api.secretPrompts.test.js` (port 5433), `test/api.createArgs.test.js` (append)

**Interfaces:**
- Produces:
  - `GET /api/secret/prompts` → `{dir, exists, files}` (Secret mode only; `{..., error}` with `files: []` when `secretImagesDir` is unset, since the generator's `--secret` needs it).
  - `handleCreateRequest(kindEntry, body, runner = startCreateJob, extras = {})` - `extras` is merged into the runner's opts; a body carrying `secretPrompt` on the public path is `400 "secret prompts are available in Secret mode only"`, on a non-NPC kind `400 "secret prompts are not a <subject> field"`.
  - Secret `/create` and `/prompt-preview` resolve `body.secretPrompt` through `validateSelection` against a fresh listing (400 on failure) and pass `{ secretPrompt }` as `extras`.
  - `/reroll-trait` accepts a trait in `rerollableFor(item)` OR in `secretSlots(item.secretPrompt)`.
  - `secretPresets.normaliseSettings` keeps `secretPrompt` (via `normaliseSelection`) when present.
  - `secretGallery.itemView` adds `secretPrompt: {file, name} | null` and extends `rerollable` with the snapshot's slot tables.

- [ ] **Step 1: Write the failing tests**

`test/api.secretPrompts.test.js`:

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const { startTestServer } = require('./helpers/testServer');
const { STUB } = require('./helpers/secretPromptsStub');

/*
 * Secret prompts end to end: the listing the select is built from, the
 * argv a selection becomes on the private create and preview, the
 * refusals (public path, unknown file, broken file, unknown name), the
 * preset round trip, and the gallery's view of a templated record with a
 * re-rollable slot table. Port 5433 is this file's own.
 */

const PORT = 5433;

async function setup(t) {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'secret-prompts-api-'));
    t.after(() => fs.rmSync(root, { recursive: true, force: true }));
    const privateDir = path.join(root, 'private'); fs.mkdirSync(privateDir);
    const tablesDir = path.join(root, 'secret-tables'); fs.mkdirSync(tablesDir);
    const promptsDir = path.join(root, 'secret-prompts'); fs.mkdirSync(promptsDir);
    fs.writeFileSync(path.join(tablesDir, 'b.md'), '## mood\n\n- x2 harsh light\n- soft light\n');
    fs.writeFileSync(path.join(promptsDir, 'explicit-v1.md'), '## Solo kneeling\n## Couple scene\n');
    fs.writeFileSync(path.join(promptsDir, 'broken.md'), 'broken\n');
    const salt = '0123456789abcdef0123456789abcdef';
    const passwordHash = `scrypt$${salt}$${crypto.scryptSync('test-password', salt, 64).toString('hex')}`;
    const server = await startTestServer({ tablesText: '## Pronouns\n- she/her/her/woman\n## Age\n- adult\n## Gear\n- a tool\n', port: PORT, generatorSource: STUB,
        extraConfig: { secretImagesDir: privateDir, secretTablesDir: tablesDir, secretPromptsDir: promptsDir, secretMode: { username: 'tester', passwordHash } } });
    t.after(() => server.stop());
    let cookie = '';
    const call = (route, body, authenticated = false) => fetch(server.baseUrl + route, {
        method: body === undefined ? 'GET' : 'POST',
        headers: { 'Content-Type': 'application/json', ...(authenticated ? { Cookie: cookie } : {}) },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
    const login = await call('/api/secret/login', { username: 'tester', password: 'test-password' });
    assert.equal(login.status, 200);
    cookie = login.headers.get('set-cookie').split(';')[0];
    async function jobLog(route, body) {
        const res = await call(route, body, true);
        const text = await res.text();
        assert.equal(res.status, 202, text);
        const { jobId } = JSON.parse(text);
        for (let i = 0; i < 50; i++) {
            const job = await (await call('/api/secret/create-status?jobId=' + jobId, undefined, true)).json();
            if (job.status !== 'running') return job.log;
            await new Promise((r) => setTimeout(r, 40));
        }
        throw new Error('job never finished');
    }
    const createLog = body => jobLog('/api/secret/create', { dryRun: true, count: 1, ...body });
    return { call, createLog, jobLog, promptsDir, privateDir, server };
}

test('the listing needs a session and reports templates and broken files', async (t) => {
    const { call, promptsDir } = await setup(t);
    assert.equal((await call('/api/secret/prompts')).status, 401);
    const res = await call('/api/secret/prompts', undefined, true);
    assert.equal(res.status, 200);
    assert.equal(res.headers.get('cache-control'), 'no-store');
    const data = await res.json();
    assert.equal(data.dir, promptsDir);
    assert.equal(data.exists, true);
    assert.deepEqual(data.files.map(f => f.file), ['broken.md', 'explicit-v1.md']);
    assert.match(data.files[0].error, /broken\.md, line 1/);
    assert.deepEqual(data.files[1].templates.map(t => t.name), ['Solo kneeling', 'Couple scene']);
    assert.deepEqual(data.files[1].templates[0].pins, { Pronouns: 'she/her' });
});

test('a selection becomes --secret-prompts and --secret-prompt, and the composition flags are dropped', async (t) => {
    const { createLog, promptsDir } = await setup(t);
    const log = await createLog({ secretPrompt: { file: 'explicit-v1.md', name: 'Solo kneeling' },
        extraTables: [{ file: 'b.md', tables: ['mood'], values: { mood: 'soft light' }, targets: { mood: 'token' } }],
        disabledTables: ['Stance'], promptLayout: { portrait: ['shot'] } });
    assert.ok(log.includes(`--secret-prompts ${path.join(promptsDir, 'explicit-v1.md')} --secret-prompt Solo kneeling`), log);
    assert.match(log, /--extra-value mood=soft light/);
    for (const flag of ['--extra-tables', '--extra-table ', '--extra-target', '--disable-table', '--prompt-layout']) assert.ok(!log.includes(flag), flag);
    assert.match(log, /--secret --secret-config/);
    const random = await createLog({ secretPrompt: { file: 'explicit-v1.md', name: 'random' } });
    assert.match(random, /--secret-prompt random/);
    const none = await createLog({ secretPrompt: null });
    assert.doesNotMatch(none, /--secret-prompt/);
});

test('the preview carries the selection too', async (t) => {
    const { call } = await setup(t);
    const res = await call('/api/secret/prompt-preview', { secretPrompt: { file: 'explicit-v1.md', name: 'Couple scene' } }, true);
    assert.equal(res.status, 200, await res.clone().text());
    const body = await res.json();
    assert.equal(body.portrait[1].id, 'secret:Poses');
    assert.ok(body.argv.includes('--secret-prompt') && body.argv.includes('Couple scene'));
    assert.ok(!body.argv.includes('--prompt-layout'));
    assert.equal((await call('/api/secret/prompt-preview', { secretPrompt: { file: 'explicit-v1.md', name: 'Nope' } }, true)).status, 400);
});

test('the public path, an unknown file, a broken file and an unknown name are refused', async (t) => {
    const { call } = await setup(t);
    const publicRes = await call('/api/create-npc', { dryRun: true, count: 1, secretPrompt: { file: 'explicit-v1.md', name: 'random' } });
    assert.equal(publicRes.status, 400);
    assert.match((await publicRes.json()).error, /Secret mode only/);
    for (const [selection, pattern] of [
        [{ file: '../explicit-v1.md', name: 'random' }, /unknown secret prompts file/],
        [{ file: 'missing.md', name: 'random' }, /unknown secret prompts file "missing.md"/],
        [{ file: 'broken.md', name: 'random' }, /broken\.md: broken\.md, line 1/],
        [{ file: 'explicit-v1.md', name: 'Nope' }, /has no secret prompt "Nope"/],
        ['explicit-v1.md', /secretPrompt must be/],
    ]) {
        const res = await call('/api/secret/create', { dryRun: true, count: 1, secretPrompt: selection }, true);
        assert.equal(res.status, 400, JSON.stringify(selection));
        assert.match((await res.json()).error, pattern, JSON.stringify(selection));
    }
    const ship = await call('/api/secret/create', { kind: 'spaceship', dryRun: true, count: 1, secretPrompt: { file: 'explicit-v1.md', name: 'random' } }, true);
    assert.equal(ship.status, 400);
    assert.match((await ship.json()).error, /not a spaceship field/);
});

test('secret presets keep the selection and refuse a malformed one', async (t) => {
    const { call } = await setup(t);
    const settings = { count: 1, artStyle: 'default', workflow: 'default', colorGuidance: 'default', secretPrompt: { file: 'explicit-v1.md', name: 'random' } };
    const saved = await call('/api/secret/presets', { name: 'Kneelers', settings }, true);
    assert.equal(saved.status, 200, await saved.clone().text());
    const { slug } = await saved.json();
    const full = await (await call('/api/secret/presets/export?slug=' + slug, undefined, true)).json();
    assert.deepEqual(full.settings.secretPrompt, { file: 'explicit-v1.md', name: 'random' });
    const without = await call('/api/secret/presets', { name: 'Plain', settings: { ...settings, secretPrompt: null } }, true);
    assert.equal(without.status, 200);
    const plain = await (await call('/api/secret/presets/export?slug=' + (await without.json()).slug, undefined, true)).json();
    assert.equal(plain.settings.secretPrompt, undefined);
    assert.equal((await call('/api/secret/presets', { name: 'Bad', settings: { ...settings, secretPrompt: { file: '../x.md', name: 'a' } } }, true)).status, 400);
});

test('a templated record shows its template and can re-roll a slot table', async (t) => {
    const { call, jobLog, privateDir } = await setup(t);
    const folder = path.join(privateDir, 'npcs', 'Private'); fs.mkdirSync(folder, { recursive: true });
    const entry = { id: 'private-id', name: 'Private', kind: 'npc', seed: 23, traits: { Gear: 'a tool' }, rawTraits: { Gear: 'a tool' }, secret: true,
        art_style: { id: 'default', name: 'Default' }, extraTraits: { Poses: 'kneeling' },
        secretPrompt: { file: 'explicit-v1.md', name: 'Solo kneeling', portrait: 'A {secret:Poses} of {npc:identity}.', token: '{secret:Clothing}.', tables: [] } };
    fs.writeFileSync(path.join(privateDir, 'manifest.json'), JSON.stringify({ [folder]: entry }));
    const { items } = await (await call('/api/secret/items', undefined, true)).json();
    assert.deepEqual(items[0].secretPrompt, { file: 'explicit-v1.md', name: 'Solo kneeling' });
    assert.ok(items[0].rerollable.includes('Poses') && items[0].rerollable.includes('Clothing'), JSON.stringify(items[0].rerollable));
    const log = await jobLog('/api/secret/reroll-trait', { id: 'private-id', trait: 'Poses' });
    assert.match(log, /--reroll-trait Poses --apply-only/);
    assert.doesNotMatch(log, /--secret-prompts/);
    assert.equal((await call('/api/secret/reroll-trait', { id: 'private-id', trait: 'Nope' }, true)).status, 400);
    const plainEntry = { ...entry, id: 'plain-id', secretPrompt: undefined };
    fs.writeFileSync(path.join(privateDir, 'manifest.json'), JSON.stringify({ [folder]: plainEntry }));
    const plain = (await (await call('/api/secret/items', undefined, true)).json()).items[0];
    assert.equal(plain.secretPrompt, null);
    assert.ok(!plain.rerollable.includes('Poses'));
});
```

Append to `test/api.createArgs.test.js` (it has `TABLES_FIXTURE`, `STUB`, `runCreate` and uses port 5193):

```js
test('a public create refuses a secret prompt rather than dropping it', async (t) => {
    const server = await startTestServer({ tablesText: TABLES_FIXTURE, port: 5193, generatorSource: STUB });
    t.after(() => server.stop());
    const res = await fetch(`${server.baseUrl}/api/create-npc`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count: 1, dryRun: true, secretPrompt: { file: 'a.md', name: 'random' } }) });
    assert.equal(res.status, 400);
    assert.match((await res.json()).error, /Secret mode only/);
});
```

- [ ] **Step 2: Run to verify they fail**

Run: `node --test test/api.secretPrompts.test.js`
Expected: the listing test fails with status 404 on `/api/secret/prompts`.

- [ ] **Step 3: `handleCreateRequest` and the public refusal**

In `server.js`, near `const secretTables = require('./lib/secretTables');` (line 2686) add:

```js
const secretPrompts = require('./lib/secretPrompts');
```

Change the signature at line 3039 to `function handleCreateRequest(kindEntry, body, runner = startCreateJob, extras = {}) {`, and right after the `promptLayout` block (before `let extraTables = [] ...`) add:

```js
    // A secret prompt template is Secret-mode, NPC-only. Refused rather
    // than dropped on the public path, for the reason the secret tables
    // are: a request that named one and got a house-prompt NPC back would
    // look like it worked.
    if (body.secretPrompt !== null && body.secretPrompt !== undefined) {
        if (runner === startCreateJob) {
            return { status: 400, body: { error: 'secret prompts are available in Secret mode only' } };
        }
        if (kindEntry.id !== DEFAULT_KIND) {
            return { status: 400, body: { error: `secret prompts are not a ${kindEntry.subject} field` } };
        }
    }
```

In the `runner(kindEntry, {...})` call, add `...extras,` as the last property before the closing brace.

- [ ] **Step 4: The listing helper and the secret routes**

Above `async function handleSecretApi` add:

```js
function listSecretPromptsNow() {
    return secretPrompts.listSecretPrompts({
        dir: DERIVED_PATHS.secretPromptsDir, script: KINDS.npc.script, tablesPath: KINDS.npc.tables,
        tablesDir: DERIVED_PATHS.secretTablesDir, configFile: CONFIG_FILE, artStylesPath: ART_STYLES_PATH,
        executable: config.pythonExecutable,
    });
}

/** body.secretPrompt validated against a fresh listing, or null; throws with a 400-worthy message. */
async function resolveSecretPrompt(body) {
    if (body.secretPrompt === null || body.secretPrompt === undefined) return null;
    if (!secretGallery.root) throw new Error('Set secretImagesDir before using secret prompts');
    return secretPrompts.validateSelection(body.secretPrompt, await listSecretPromptsNow());
}
```

Inside `handleSecretApi`'s `try`, next to the `/tables` route:

```js
        if (route === '/prompts' && req.method === 'GET') {
            if (!secretGallery.root) {
                return sendJson(res, 200, { dir: DERIVED_PATHS.secretPromptsDir, exists: false, files: [],
                    error: 'Set secretImagesDir before using secret prompts' });
            }
            return sendJson(res, 200, await listSecretPromptsNow());
        }
```

Change the `/prompt-preview` route body to:

```js
            const body = JSON.parse(await readBody(req, 256 * 1024));
            if (body.kind && body.kind !== 'npc') return sendJson(res, 400, { error: 'Prompt composer is available for Secret NPCs only' });
            let secretPrompt;
            try { secretPrompt = await resolveSecretPrompt(body); }
            catch (err) { return sendJson(res, 400, { error: err.message }); }
            let options;
            const result = handleCreateRequest(KINDS.npc, { ...body, count: 1, seed: body.seed ?? 0, dryRun: true }, (_kind, opts) => {
                options = opts;
                return { ok: true };
            }, { secretPrompt });
            if (!options) return sendJson(res, result.status, result.body);
            return sendJson(res, 200, await secretGallery.previewPrompts(KINDS.npc, options));
```

and the `/create` route body to:

```js
            const body = JSON.parse(await readBody(req, 256 * 1024));
            const kind = resolveKind(url, body);
            if (!kind) return sendJson(res, 400, { error: 'Unknown kind' });
            let secretPrompt = null;
            if (kind.id === DEFAULT_KIND) {
                try { secretPrompt = await resolveSecretPrompt(body); }
                catch (err) { return sendJson(res, 400, { error: err.message }); }
            }
            const result = handleCreateRequest(kind, body, secretGallery.startCreate, { secretPrompt });
            return sendJson(res, result.status, result.body);
```

In the `/regenerate` + `/reroll-trait` route, replace the `rerollableFor(...).includes(trait)` check with:

```js
            const allowed = [...rerollableFor({ ...item, kind: kind.id }), ...secretPrompts.secretSlots(item.secretPrompt)];
            if (route === '/reroll-trait' && !allowed.includes(trait)) return sendJson(res, 400, { error: 'Unknown or unavailable trait' });
```

- [ ] **Step 5: Presets and the gallery view**

`lib/secretPresets.js`: add `const secretPrompts = require('./secretPrompts');` and, before the `for (const key of ['artStyle', ...` loop:

```js
    const secretPrompt = secretPrompts.normaliseSelection(raw.secretPrompt);
    if (secretPrompt) settings.secretPrompt = secretPrompt;
```

`lib/secretGallery.js`: add `const secretPrompts = require('./secretPrompts');` beside the other requires, and in `itemView` change the `rerollable:` property and add `secretPrompt`:

```js
            rerollable: [...rerollableFor({ ...item, kind: item.kind || 'npc' }), ...secretPrompts.secretSlots(item.secretPrompt)],
            // The template a Secret-mode NPC was prompted from, for the card and the detail sheet.
            secretPrompt: item.secretPrompt && typeof item.secretPrompt === 'object' && typeof item.secretPrompt.name === 'string'
                ? { file: item.secretPrompt.file, name: item.secretPrompt.name } : null,
```

- [ ] **Step 6: Run the tests**

Run: `node --test test/api.secretPrompts.test.js` then `node --test test/api.secretTables.test.js`, `node --test test/api.createArgs.test.js`, `node --test test/api.secret.test.js`
Expected: all pass. (`api.secretTables` still passes because its stub echoes argv and never receives `secretPrompt`.)

- [ ] **Step 7: Commit**

```bash
git add server.js lib/secretPresets.js lib/secretGallery.js test/api.secretPrompts.test.js test/api.createArgs.test.js
git commit -m "serve, create with and re-roll secret prompt templates" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 17: the composer's read-only mode

**Files:**
- Modify: `public/prompt-composer.js:39-175`
- Test: `test/ui.secretPrompts.test.js` (create; the composer harness is copied from `test/ui.promptComposer.test.js`)

**Interfaces:**
- Produces: `PromptComposer.create({ element, getRequest, request, active, locked = () => false })`. While `locked()` is true: pills render with their caption and value only (no grip, no arrow buttons, no drag handlers), Add/Reset stay disabled, `getLayout()` returns `{}`, and the status line reads `Secret prompt selected: the template fixes the order. Random values resolve when you generate.`

- [ ] **Step 1: Write the failing test**

Create `test/ui.secretPrompts.test.js` with the harness and the first test (later tasks append to this file):

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

/*
 * The Secret prompt select of Create NPC: the request router carrying the
 * pick, the markup, the read-only composer while a template is chosen,
 * and the source-level pins of secret-mode.js and app.js the way
 * ui.secretTables does.
 */

const read = (file) => fs.readFileSync(path.join(__dirname, '..', 'public', file), 'utf8');
const ui = () => require('../public/secret-mode');

function composerPage(locked, request = async () => ({ portrait: [
    { id: 'npc:identity', text: 'A mechanic', sources: ['Role'], randomSources: ['Role'] },
    { id: 'secret:Poses', text: ' kneeling.', sources: ['Poses'], randomSources: ['Poses'] },
], token: [] })) {
    class Element {
        constructor(tag = 'div') { this.tag = tag; this.children = []; this.dataset = {}; this.listeners = {}; this.style = { setProperty() {} }; this.classList = { add() {}, remove() {} }; this.textContent = ''; this.value = ''; }
        append(...nodes) { for (const node of nodes) { node.parent = this; this.children.push(node); } }
        replaceChildren(...nodes) { this.children = []; this.append(...nodes); }
        addEventListener(type, action) { (this.listeners[type] ||= []).push(action); }
        dispatch(type, extra = {}) { for (const action of this.listeners[type] || []) action({ target: this, preventDefault() {}, stopPropagation() {}, ...extra }); }
        setAttribute(key, value) { this[key] = value; }
        focus() { this.focused = true; }
        closest() { return form; }
        contains(node) { return node === this || this.children.some(child => child.contains(node)); }
        querySelectorAll(selector) {
            const attribute = selector.match(/^\[data-(.*)\]$/)?.[1].replace(/-([a-z])/g, (_, c) => c.toUpperCase());
            return this.children.flatMap(child => [...((attribute ? Object.hasOwn(child.dataset, attribute) : child.tag === selector) ? [child] : []), ...child.querySelectorAll(selector)]);
        }
        querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
    }
    const form = new Element(), element = new Element(); form.append(element);
    for (const name of ['target', 'pills', 'status', 'prose', 'add', 'reset']) {
        const node = new Element(); node.dataset['composer' + name[0].toUpperCase() + name.slice(1)] = ''; element.append(node);
    }
    const timers = new Map(); let next = 0;
    const window = { crypto: { randomUUID: () => 'test-custom' } };
    const context = vm.createContext({ window, document: { createElement: tag => new Element(tag), getElementById: () => null },
        setTimeout: callback => { timers.set(++next, callback); return next; }, clearTimeout: id => timers.delete(id) });
    vm.runInContext(read('prompt-composer.js'), context);
    const controller = window.PromptComposer.create({ element, request, getRequest: () => ({}), active: () => true, locked });
    const node = name => element.querySelector(`[data-composer-${name}]`);
    const flush = async () => { const pending = [...timers.values()]; timers.clear(); await Promise.all(pending.map(callback => callback())); };
    return { controller, node, flush };
}

test('a locked composer previews the filled template read-only', async () => {
    let locked = true;
    const view = composerPage(() => locked); await view.flush();
    assert.match(view.node('prose').textContent, /Random value from Poses/);
    assert.equal(view.node('pills').querySelectorAll('[data-handle]').length, 0);
    assert.equal(view.node('add').disabled, true);
    assert.equal(view.node('reset').disabled, true);
    assert.match(view.node('status').textContent, /template fixes the order/);
    assert.deepEqual(view.controller.getLayout(), {});
    locked = false;
    // setLayout re-renders at once; refresh() alone would skip an unchanged request.
    view.controller.setLayout({}); await view.flush();
    assert.equal(view.node('pills').querySelectorAll('[data-handle]').length, 2);
    assert.equal(view.node('add').disabled, false);
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `node --test test/ui.secretPrompts.test.js`
Expected: fails on the handle count (`2 !== 0`).

- [ ] **Step 3: Implement**

In `public/prompt-composer.js`:

- `function create({ element, getRequest, request, active, locked = () => false }) {`
- In `render()`, compute `const fixed = locked();` at the top. Inside the `for` loop, build `header` as today but only append the grip and arrows when not fixed:

```js
                const header = document.createElement('div'); header.className = 'prompt-pill-header';
                const caption = document.createElement('span'); caption.textContent = source;
                if (fixed) {
                    header.append(caption);
                } else {
                    const handle = button('⠿', `Move ${source}; use left and right arrow keys`, () => {});
                    handle.dataset.handle = part.id; handle.draggable = true;
                    handle.addEventListener('dragstart', event => {
                        dragging = part.id; event.dataTransfer.effectAllowed = 'move';
                        event.dataTransfer.setData('text/plain', part.id); card.classList.add('dragging');
                    });
                    handle.addEventListener('dragend', () => { dragging = null; card.classList.remove('dragging'); });
                    handle.addEventListener('keydown', event => {
                        if (event.key === 'ArrowLeft' && index > 0) { event.preventDefault(); movePart(part.id, parts[index - 1].id); }
                        if (event.key === 'ArrowRight' && index < parts.length - 1) { event.preventDefault(); movePart(part.id, parts[index + 2]?.id); }
                    });
                    const previous = button('←', `Move ${source} earlier`, () => movePart(part.id, parts[index - 1]?.id));
                    const next = button('→', `Move ${source} later`, () => movePart(part.id, parts[index + 2]?.id));
                    previous.disabled = index === 0; next.disabled = index === parts.length - 1;
                    header.append(handle, caption, previous, next);
                }
                card.append(header);
```

  and register the `dragover`/`drop` listeners on the card only when `!fixed`. At the end of `render()`:

```js
            query('[data-composer-add]').disabled = !ready || fixed;
            query('[data-composer-reset]').disabled = !ready || fixed;
```

- In `refresh()`, after `render()` succeeds, set the status to the locked wording when `locked()`:

```js
                status.textContent = locked()
                    ? 'Secret prompt selected: the template fixes the order. Random values resolve when you generate.'
                    : 'Preview updated. Random values resolve when you generate; conditional snippets may change with the roll.';
```

- `getLayout: () => locked() ? {} : JSON.parse(JSON.stringify(layout)),`
- `updateProse()` joins with `join(parts, !!layout[target]?.length && !locked())`.

- [ ] **Step 4: Run both composer test files**

Run: `node --test test/ui.secretPrompts.test.js test/ui.promptComposer.test.js`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add public/prompt-composer.js test/ui.secretPrompts.test.js
git commit -m "let the prompt composer preview a fixed template read-only" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 18: the Secret prompt select, pin locking, presets and the gallery label

**Files:**
- Modify: `public/index.html:193-194` (insert before `id="secret-tables-section"`)
- Modify: `public/style.css` (append)
- Modify: `public/app.js:4462-4660` (`renderOverrideRows`), `4738-4755` (`createRequestBody`), `4908-4922` (`createFormSettings`)
- Modify: `public/secret-mode.js`
- Test: `test/ui.secretPrompts.test.js` (append)

**Interfaces:**
- Consumes: `GET /api/secret/prompts` (Task 16), `PromptComposer.create({ locked })` (Task 17).
- Produces:
  - `routeRequest(path, options, authenticated, selections)` adds `body.secretPrompt` from `selections.secretPrompt` on a logged-in NPC create and then deletes `extraTables`, `disabledTables` and `promptLayout` from the body.
  - `createState.overrides[i].locked === true` rows: rendered disabled with the note "Pinned by the selected secret prompt", excluded from `createRequestBody()` and `createFormSettings()`.
  - Markup ids: `secret-prompt-section` (hidden), `secret-prompt-select`, `secret-prompt-status`, `secret-prompt-summary`.
  - Gallery card line `Secret prompt: <name>`; detail sheet extra-trait rows get a Re-roll button when the trait is in `item.rerollable`.

- [ ] **Step 1: Write the failing tests**

Append to `test/ui.secretPrompts.test.js`:

```js
test('a logged-in NPC create carries the secret prompt and drops the composition fields', () => {
    const options = { method: 'POST', body: JSON.stringify({ count: 1 }) };
    const pick = { file: 'explicit-v1.md', name: 'random' };
    const picks = { extraTables: [{ file: 'a.json', tables: ['one'] }], disabledTables: ['Stance'] };
    const npc = ui().routeRequest('/api/create-npc', options, true, { npc: 'ink', secretTables: picks, promptLayout: { portrait: ['shot'] }, secretPrompt: pick });
    assert.equal(npc.path, '/api/secret/create');
    assert.deepEqual(JSON.parse(npc.options.body), { count: 1, kind: 'npc', artStyle: 'ink', secretPrompt: pick });
    const none = ui().routeRequest('/api/create-npc', options, true, { npc: 'ink', secretTables: picks, secretPrompt: null });
    assert.deepEqual(JSON.parse(none.options.body), { count: 1, kind: 'npc', artStyle: 'ink', ...picks });
    const ship = ui().routeRequest('/api/create', { method: 'POST', body: '{"kind":"spaceship"}' }, true, { secretPrompt: pick });
    assert.deepEqual(JSON.parse(ship.options.body), { kind: 'spaceship', artStyle: 'default' });
    const loggedOut = ui().routeRequest('/api/create-npc', options, false, { secretPrompt: pick });
    assert.deepEqual(JSON.parse(loggedOut.options.body), { count: 1, artStyle: 'default' });
});

test('the markup ships the select hidden, just before the secret tables section', () => {
    const html = read('index.html');
    const section = html.indexOf('id="secret-prompt-section"');
    assert.notEqual(section, -1);
    assert.match(html.slice(section, section + 60), /hidden/);
    assert.ok(section > html.indexOf('id="add-override"'));
    assert.ok(section < html.indexOf('id="secret-tables-section"'));
    for (const id of ['secret-prompt-select', 'secret-prompt-status', 'secret-prompt-summary']) assert.ok(html.includes(`id="${id}"`), id);
});

test('secret-mode.js fills the select from the listing, locks pins, labels the gallery and clears on logout', () => {
    const js = read('secret-mode.js');
    assert.match(js, /json\('\/api\/secret\/prompts'\)/);
    assert.match(js, /Random from \$\{/);
    assert.match(js, /locked: \(\) => !!promptPick/);
    assert.match(js, /Pinned by the selected secret prompt|locked: true/);
    assert.match(js, /Secret prompt: \$\{item\.secretPrompt\.name\}/);
    assert.match(js, /secretPrompt: secretPromptPick\(\)/);
    assert.match(js, /Reload Secret mode: secret prompt/);
    const clear = js.slice(js.indexOf('function clearPrivateView'), js.indexOf('function expire'));
    assert.match(clear, /promptPick = null/);
    assert.match(clear, /secret-prompt-section'\)\.hidden = true|secret-prompt-section'\)\) get\('secret-prompt-section'\)\.hidden = true/);
    // The detail sheet offers Re-roll on a slot table the record can re-roll.
    const detail = js.slice(js.indexOf('function openDetail'), js.indexOf('function stepDetail'));
    assert.match(detail, /item\.extraTraits[\s\S]*rerollable[\s\S]*includes\(key\)/);
});

test('app.js renders locked override rows and keeps them out of requests and presets', () => {
    const js = read('app.js');
    const rows = js.slice(js.indexOf('function renderOverrideRows'), js.indexOf('function createRequestBody'));
    assert.match(rows, /override\.locked/);
    assert.match(rows, /Pinned by the selected secret prompt/);
    const body = js.slice(js.indexOf('function createRequestBody'), js.indexOf('async function startCreateJob'));
    assert.match(body, /!o\.locked/);
    const settings = js.slice(js.indexOf('function createFormSettings'), js.indexOf('function applyCreateSettings'));
    assert.match(settings, /!o\.locked/);
});
```

- [ ] **Step 2: Run to verify they fail**

Run: `node --test test/ui.secretPrompts.test.js`
Expected: the four new tests fail (router body carries `extraTables`; markup id missing; source patterns missing).

- [ ] **Step 3: Markup and style**

In `public/index.html`, immediately before `<div class="secret-tables" id="secret-tables-section" hidden>`:

```html
    <div class="secret-prompt" id="secret-prompt-section" hidden>
      <label>Secret prompt
        <select id="secret-prompt-select" aria-describedby="secret-prompt-status"><option value="">None</option></select>
      </label>
      <p class="hint" id="secret-prompt-status"></p>
      <p class="hint" id="secret-prompt-summary" hidden></p>
    </div>
```

Append to `public/style.css`:

```css
.secret-prompt { margin-top: 1rem; }
.secret-prompt select { max-width: 100%; }
.filter-row-locked select, .filter-row-locked input { opacity: 0.7; }
```

- [ ] **Step 4: `app.js` - locked override rows**

In `renderOverrideRows()`, as the last statement of the `createState.overrides.forEach((override, index) => { ... })` callback (after every control has been appended to `row`):

```js
    // A row pinned by the selected secret prompt: shown, disabled, and kept
    // out of the request (the template pins it) - see createRequestBody.
    if (override.locked) {
      row.classList.add("filter-row-locked");
      tableSelect.disabled = true;
      search.hidden = true;
      valueSelect.disabled = true;
      valueInput.disabled = true;
      valueInput.hidden = false;
      for (const button of row.querySelectorAll("button")) button.disabled = true;
      note.textContent = "Pinned by the selected secret prompt.";
      note.hidden = false;
    }
```

In `createRequestBody()`: `overrides: createState.overrides.filter((o) => o.table && o.value.trim() && !o.locked),`.

In `createFormSettings()`: `.filter((o) => o.table && String(o.value).trim() && !o.locked)`.

- [ ] **Step 5: `secret-mode.js`**

Module-level state, beside `let galleryItems = [] ...`:

```js
  let promptListing = null, promptPick = null, savedPronouns = null;
  function secretPromptPick() { return promptPick ? { file: promptPick.file, name: promptPick.name } : null; }
```

`selections()` gains `secretPrompt: secretPromptPick()` after `promptLayout`. In `routeRequest`, after the `promptLayout` line:

```js
      if (create && authenticated && kind === 'npc' && selections.secretPrompt) {
        // The template decides what appears: the picker's tables, the
        // disabled list and the composer's order do not travel with it.
        body.secretPrompt = selections.secretPrompt;
        delete body.extraTables; delete body.disabledTables; delete body.promptLayout;
      }
```

Add the loader and the selection handler after `loadSecretTables`:

```js
  // The Secret prompt select: None, one "Random from <file>" per valid
  // file, then every template grouped by file. Broken files are named in
  // the status line and cannot be picked.
  async function loadSecretPrompts() {
    const section = get('secret-prompt-section');
    if (!section) return;
    if (!transport.authenticated) { section.hidden = true; return; }
    promptListing = await json('/api/secret/prompts');
    const select = get('secret-prompt-select');
    select.replaceChildren(new Option('None', ''));
    const valid = (promptListing.files || []).filter(file => !file.error);
    for (const file of valid) select.append(new Option(`Random from ${file.file}`, `random\n${file.file}`));
    for (const file of valid) {
      const group = document.createElement('optgroup'); group.label = file.file;
      group.append(...(file.templates || []).map(template => new Option(template.name, `${template.name}\n${file.file}`)));
      select.append(group);
    }
    const broken = (promptListing.files || []).filter(file => file.error).map(file => file.error);
    get('secret-prompt-status').textContent = promptListing.error ? promptListing.error
      : !promptListing.exists ? `Folder not found: ${promptListing.dir}. Create it, or point secretPromptsDir at yours in Settings.`
      : broken.length ? broken.join(' ') : valid.length ? `From ${promptListing.dir}.` : `No .md template files in ${promptListing.dir}.`;
    section.hidden = false;
    select.value = '';
    applySecretPrompt();
  }

  function applySecretPrompt() {
    const value = get('secret-prompt-select').value;
    const [name, file] = value ? value.split('\n') : [null, null];
    const entry = file && (promptListing?.files || []).find(candidate => candidate.file === file && !candidate.error);
    promptPick = entry ? { file, name } : null;
    const templates = !entry ? [] : name === 'random' ? entry.templates || [] : (entry.templates || []).filter(template => template.name === name);
    // With Random, only a pin every template of the file agrees on locks a picker.
    const pins = {};
    for (const [table, pinned] of Object.entries(templates[0]?.pins || {})) {
      if (templates.every(template => template.pins?.[table] === pinned)) pins[table] = pinned;
    }
    const slots = [...new Set(templates.flatMap(template => template.secretSlots || []))];
    const summary = get('secret-prompt-summary');
    summary.hidden = !promptPick;
    summary.textContent = !promptPick ? '' : `${name === 'random' ? `Rolled per NPC from ${templates.length} template${templates.length === 1 ? '' : 's'}. ` : ''}`
      + `Pins: ${Object.entries(pins).map(([table, pinned]) => `${table} = ${pinned}`).join(', ') || 'none'}. Slot tables: ${slots.join(', ') || 'none'}.`;
    const collapsed = get('secret-tables-toggle').getAttribute('aria-expanded') === 'false';
    get('secret-tables-content').hidden = !!promptPick || collapsed;
    get('secret-tables-toggle').disabled = !!promptPick;
    lockPins(pins);
    composer?.refresh();
  }

  // Trait pickers a pin covers are locked to the pinned value. Rows the user
  // made keep their own value under the lock and get it back on None; rows
  // added for a pin are removed again.
  function lockPins(pins) {
    for (const row of createState.overrides) {
      if (row.locked && row.pinned) { Object.assign(row, row.pinned); delete row.pinned; }
      delete row.locked;
    }
    createState.overrides = createState.overrides.filter(row => !row.added);
    for (const [table, pinned] of Object.entries(pins)) {
      if (table === 'Pronouns') continue;
      const row = createState.overrides.find(candidate => candidate.table === table);
      if (row) { row.pinned = { value: row.value, custom: row.custom }; Object.assign(row, { value: pinned, custom: true, locked: true }); }
      else createState.overrides.push({ table, value: pinned, custom: true, locked: true, added: true, search: '' });
    }
    const pronouns = elCreate.pronouns;
    if (Object.hasOwn(pins, 'Pronouns')) {
      if (!pronouns.disabled) savedPronouns = pronouns.value;
      pronouns.value = pins.Pronouns.split('/')[0].trim();
      pronouns.disabled = true;
    } else if (pronouns.disabled && savedPronouns !== null) {
      pronouns.value = savedPronouns; pronouns.disabled = false; savedPronouns = null;
    }
    renderOverrideRows();
  }
```

Wire it up:

- In `loadSecretTables()`, replace the final `await loadSecretPresets();` with `await loadSecretPrompts(); await loadSecretPresets();`. In the `DOMContentLoaded` `catch` around `loadSecretTables()`, also show `get('secret-prompt-section').hidden = false` so a listing failure still shows its status line (the status is set by the thrown message: `get('secret-prompt-status').textContent = \`Could not load secret prompts: ${err.message}\``).
- In `setSecretTablesCollapsed`, change `get('secret-tables-content').hidden = collapsed;` to `get('secret-tables-content').hidden = collapsed || !!promptPick;`.
- In `DOMContentLoaded`, after the `secret-tables-collapse` listener: `get('secret-prompt-select').addEventListener('change', applySecretPrompt);`.
- The composer creation gains `locked: () => !!promptPick,`.
- In `clearPrivateView()`, after the `secret-tables-section` line:

```js
    promptListing = null; promptPick = null; savedPronouns = null;
    get('secret-prompt-select')?.replaceChildren(new Option('None', ''));
    if (get('secret-prompt-summary')) get('secret-prompt-summary').hidden = true;
    if (get('secret-prompt-section')) get('secret-prompt-section').hidden = true;
```

- Preset save (`secret-preset-save` handler): add `secretPrompt: secretPromptPick()` to `settings`.
- `applySecretSettings(settings, presetName)`: with the other pre-checks (before `applyCreateSettings`), add

```js
    const select = get('secret-prompt-select');
    const wanted = settings.secretPrompt ? `${settings.secretPrompt.name}\n${settings.secretPrompt.file}` : '';
    if (wanted && ![...select.options].some(option => option.value === wanted)) {
      throw new Error(`Reload Secret mode: secret prompt ${settings.secretPrompt.name} in ${settings.secretPrompt.file} has changed.`);
    }
```

  and, as the LAST statements of the function (after `composer?.setLayout(...)`): `select.value = wanted; applySecretPrompt();`.

- `renderGallery()`: add `['sub secret-prompt-label', item.secretPrompt ? \`Secret prompt: ${item.secretPrompt.name}\` : '']` to the card lines after the preset label.
- `openDetail()`: `get('secret-detail-style').textContent = \`Art style: ${item.artStyle?.name || 'Default'}${item.secretPrompt ? \` · Secret prompt: ${item.secretPrompt.name}\` : ''}\`;` and in the `item.extraTraits` loop, replace the empty `control` cell with a Re-roll button when the record can re-roll it:

```js
    for (const [key, value] of Object.entries(item.extraTraits || {})) {
      const row = document.createElement('tr'), control = document.createElement('td'), name = document.createElement('td'), text = document.createElement('td');
      if ((item.rerollable || []).includes(key)) {
        const button = document.createElement('button'); button.type = 'button'; button.className = 'reroll-btn'; button.textContent = 'Re-roll';
        button.disabled = detailBusy || item.regenStatus === 'running';
        button.addEventListener('click', () => mutateDetail('/api/secret/reroll-trait', { id: item.id, trait: key }));
        control.append(button);
      }
      row.className = 'secret-extra-trait'; name.textContent = key; text.textContent = value;
      row.append(control, document.createElement('td'), name, text); traitRows.append(row);
    }
```

  and update the comment above it: slot tables of a secret prompt are re-rollable, other extra values are not.

- [ ] **Step 6: Run the UI tests**

Run: `node --test test/ui.secretPrompts.test.js test/ui.secretTables.test.js test/ui.promptComposer.test.js test/ui.secretMode.test.js`
Expected: pass.

- [ ] **Step 7: Smoke it in the browser**

Start the GUI from the worktree (`node server.js` with the real `config.json`), log into Secret mode, open Create NPC. Check: the select lists "Random from explicit-v1.md" and the seven templates; picking one hides the tables picker and shows the summary with `Pronouns = she/her`; the pronoun field locks to `she`; Preview prompt shows the filled template with no grips; Dry run succeeds; back to None restores the picker and the pronoun field; save and load a secret preset with the template; the gallery card of a generated NPC shows `Secret prompt: ...` and its detail sheet offers Re-roll on a slot table. Note anything that misbehaves in the final report.

- [ ] **Step 8: Commit**

```bash
git add public/index.html public/style.css public/app.js public/secret-mode.js test/ui.secretPrompts.test.js
git commit -m "pick a secret prompt template on the Secret Create NPC page" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 19: version bump and the GUI test sweep

**Files:**
- Modify: `lib/version.js`

- [ ] **Step 1: Bump**

`const APP_VERSION = '1.2.0';` (a large change: minor up, subversion reset, per `AGENTS.md`).

- [ ] **Step 2: Run the version test and the whole suite**

Run: `node --test test/version.test.js` then `node --test` (whole suite).
Expected: `version.test.js` passes. In the whole-suite run, only the known port-collision files may fail (`create-presets`, `set-flag`, `table-bullets` - memory rule); re-run each of those alone and confirm they pass. Every file touched in this plan passes alone.

- [ ] **Step 3: Commit**

```bash
git add lib/version.js
git commit -m "bump the version for secret prompt templates" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

## Part D - finish

### Task 20: merge both branches into local `main` and clean up

Per the memory rule "merge-to-local-main-and-clean-up-worktree": fast-forward only, no push.

- [ ] **Step 1: Generator**

From the generator worktree, confirm `git status` is clean and `git log --oneline main..secret-prompts` lists the spec commit plus Tasks 1-10. Then leave the worktree (`ExitWorktree`, keep) and from the main checkout:

```powershell
git -C G:\GIT-REPOS\lancer-art-generator merge --ff-only secret-prompts
git -C G:\GIT-REPOS\lancer-art-generator worktree remove .claude\worktrees\secret-prompts
git -C G:\GIT-REPOS\lancer-art-generator branch -d secret-prompts
```

If `--ff-only` refuses because `main` moved, rebase the branch onto `main` first (`git rebase main` inside the worktree), re-run `python -m unittest test.test_secret_prompts`, then merge.

- [ ] **Step 2: GUI**

Same three commands with `G:\GIT-REPOS\lancer-npc-import-gui`.

- [ ] **Step 3: Verify the content is in place**

`Test-Path G:\GIT-REPOS\lancer-art-generator\prompts\secret-tables\explicit-table-3.md` and `...\prompts\secret-prompts\explicit-v1.md` both `True`; `git -C G:\GIT-REPOS\lancer-art-generator status --short` shows neither (gitignored).

- [ ] **Step 4: Report**

State: the two merged commits ranges, the version now in `lib/version.js`, the dry-run seeds read in Task 12 and any wording changed, the browser smoke result from Task 18, and that the user's next step is rendering a sample in ComfyUI (spec 5.4).

---

## Self-review against the spec

- 2.1 location and gitignore: Tasks 10, 11, 12, 13. 2.2 shape: Task 2. 2.3 slots and the field list: Tasks 2, 4. 2.4 tidy-up: Task 4. 2.5 every load error: Tasks 2, 3.
- 3.1 module: Tasks 2-5. 3.2 flags and refusals: Task 6. 3.3 roll order (choose, pin, adults only, roll, slot tables, build): Tasks 5, 7, 8. 3.4 record: Task 8 (with the documented `tables` extension). 3.5 regeneration and slot re-roll: Tasks 7, 9. 3.6 preview and dry run: Task 8. 3.7 test list: Tasks 2-9 (`test/test_secret_prompts.py`).
- 4.1 listing and route: Tasks 3, 14, 16. 4.2 page behaviour: Tasks 17, 18. 4.3 create, presets, gallery, version: Tasks 15, 16, 18, 19. 4.4 tests: Tasks 14-18 (the spec's "fake generator in test/helpers" is `test/helpers/secretPromptsStub.js`; the spec's `api.createArgs` additions are the public-path refusal there plus `kinds.test.js` for argv building).
- 5.1-5.4 content and quality check: Tasks 11, 12.
- 6 out of scope: nothing here reorders template fragments, mixes appended extra tables with a template, or touches `secretGallery.js:169`.
