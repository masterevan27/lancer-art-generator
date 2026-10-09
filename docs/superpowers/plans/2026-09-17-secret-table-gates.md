---
type: "Plan"
title: "Secret Table Gates Implementation Plan"
description: "Implementation steps and constraints for Secret Table Gates."
---
# Secret Table Gates Implementation Plan

> **Status, 2026-09-17: implemented and tested.** The generator and GUI work
> landed on `main`; this checklist is retained as an implementation record.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let private (Secret mode) tables carry `#tag`s on bullets and `(when: tag)` gates on headings, so a gated table rolls or is offered only when an earlier pick opens it, with a collapsible roll-order panel in Create NPC.

**Architecture:** The generator (`lancer-art-generator/generate-npc.py`) owns the roll: `load_extra_tables()` returns an `ExtraTables` dict subclass carrying `when` and `tags` beside the unchanged `{name: [(value, weight)]}` rows, resolves fixed gated values by narrowing a single Random opener, and `roll_extra()` skips shut gates. The GUI (`lancer-npc-import-gui`) mirrors the same rules in one pure UMD module, `public/secret-gates.js`, used by `lib/secretTables.js` (listing + server validation) and by `public/secret-mode.js` (greying, notes, roll-order panel). Refusal texts are identical in both.

**Tech Stack:** Python 3 stdlib (`unittest`), Node.js stdlib (`node:test`), vanilla browser JS, plain CSS.

**Spec:** `lancer-art-generator/docs/superpowers/specs/2026-09-16-secret-table-gates-design.md`

## Global Constraints

- Worktrees (both on branch `secret-table-gates`):
  - generator: `G:\GIT-REPOS\lancer-art-generator\.claude\worktrees\secret-table-gates`
  - GUI: `G:\GIT-REPOS\lancer-npc-import-gui\.claude\worktrees\secret-table-gates`
  Run every command from the worktree of the repo being changed; use plain `git -C <worktree> ...` commands, never the main checkouts. Never push.
- Generator tests: `python -m unittest discover test` (single file: `python -m unittest test.test_extra_table_gates -v`). The pre-existing failures listed in memory (7 scientists/role-lock/import-flag/prompt-budget) are not ours; compare against `main` if they appear.
- GUI tests: `node --test --test-concurrency=4 --test-timeout=120000 "test/*.test.js"`. `api.createPresets`, `api.setFlag`, `api.tableBullets*` can flake on port collisions under the full run; re-run those files alone before treating a failure as real.
- Tag character rule: `[A-Za-z0-9_-]+`, compared lower-case. Tags are the trailing `(\s+#tag)+` run of a bullet only.
- Load order: files in argument order, then tables in file order. The GUI sends files in listing (alphabetical) order.
- Existing files and `test/test_extra_tables.py`, `test/secretTables.test.js`, `test/api.secretTables.test.js` must keep passing unchanged. A private set with no gates must roll byte-for-byte as before.
- Exact message texts (both languages, character for character):
  - `table '<name>' has an empty (when:)`
  - `table '<name>' has an empty entry in (when:)`
  - `table '<name>': '<tag>' is not a tag (letters, digits, - and _)`
  - `table '<name>' is repeated with a different (when:)`
  - `gated table '<name>' comes before '<opener>', the table that opens it (when: <a, b>)`
  - GUI only: `gated table '<name>' has no table in the folder carrying its tags (when: <a, b>)`
  - `extra table '<name>' has a fixed value but <reason>` where reason is one of:
    - `'<A>' and '<B>' could each open it (when: <a, b>); fix or untick all but one`
    - `'<opener>' is already limited to #x or #y by '<gated table>'`
    - `'<opener>' is fixed to '<value>', which is not #a or #b`
    - `nothing selected can open it (when: <a, b>)`
- Commit messages: lower-case imperative summary like the repos' logs (`let private extra tables pin exact NPC trait values`), ending with
  `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

---

## File map

**lancer-art-generator**
- Modify `generate-npc.py` (roll tables section, ~L1455-1605): tag/heading helpers, `ExtraTables`, `load_extra_tables`, `_markdown_extra_rows`, `_open_fixed_gates`, `roll_extra`.
- Create `test/test_extra_table_gates.py`.
- Modify `README.md` (`--extra-tables` section, ~L55-113).

**lancer-npc-import-gui**
- Create `public/secret-gates.js` — pure gate logic (UMD: `window.SecretGates` / `module.exports`).
- Create `test/secretGates.test.js`.
- Modify `lib/secretTables.js` — parse tags/gates, folder-level order errors, strict resolution in `validateSelection`.
- Modify `test/secretTables.test.js`, `test/api.secretTables.test.js`.
- Modify `public/index.html` — script tag, roll-order `<details>`, gate error line.
- Modify `public/secret-mode.js` — gate metadata per row, `refreshGates()`, skip closed tables, preview relabel, panel render + open state.
- Modify `public/style.css` — indentation, closed state, panel.
- Modify `test/ui.secretTables.test.js`.
- Modify `docs/secret-mode.md`, `README.md`.

---

### Task 1: Generator — parse tags and gates, keep the row shape

**Files:**
- Modify: `generate-npc.py` (`load_extra_tables` L1490-1577, `_markdown_extra_rows` L1580-1593)
- Test: `test/test_extra_table_gates.py` (create)

**Interfaces:**
- Produces:
  - `split_extra_tags(text) -> (str, tuple[str, ...])`
  - `extra_when(name, tags: list) -> tuple[str, ...]` (raises `ValueError`)
  - `split_extra_heading(heading) -> (str, tuple | None)`
  - `class ExtraTables(dict)` with `.when: {name: tuple}` and `.tags: {name: {value: tuple}}` (only tables/values that have any)
  - `load_extra_tables(paths, only=None, values=None) -> ExtraTables` (same rows as before)

- [ ] **Step 1: Write the failing tests**

Create `test/test_extra_table_gates.py`:

```python
"""Tag gates on private extra tables.

A bullet's trailing '#tag's say which gated tables its value opens; a
'## Name (when: tag, tag)' heading makes a table that rolls only when a value
rolled or fixed earlier carries one of those tags. See
docs/superpowers/specs/2026-09-16-secret-table-gates-design.md.
"""
import contextlib
import io
import json
import random
import tempfile
import unittest
from pathlib import Path

from test.helpers import FIXTURE_TABLES, load_generator

gen = load_generator()

STYLES_MD = """## Styles
- x2 Rugged dockworker #man
- x1 Sharp-suited broker #Man
- x2 Elegant courtesan #woman #noble

## Men's Attributes (when: man)
- heavy stubble #scarred
- broad shoulders

## Scars (when: scarred)
- a burn scar across one cheek

## Jewellery (when: woman, noble)
- a thin gold circlet
"""


class GateCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, name, content):
        path = Path(self.tmp.name) / name
        text = content if isinstance(content, str) else json.dumps(content)
        path.write_text(text, encoding="utf-8")
        return path

    def load(self, text=STYLES_MD, **kwargs):
        return gen.load_extra_tables([self.write("styles.md", text)], **kwargs)

    def refused(self, message, *args, **kwargs):
        with self.assertRaises(ValueError) as ctx:
            gen.load_extra_tables(*args, **kwargs)
        self.assertEqual(str(ctx.exception), message)


class TestParsing(GateCase):
    def test_trailing_tags_are_split_off_and_lower_cased(self):
        self.assertEqual(gen.split_extra_tags("Rugged dockworker #man #Noble"),
                         ("Rugged dockworker", ("man", "noble")))
        self.assertEqual(gen.split_extra_tags("a #3 jersey worn loose"), ("a #3 jersey worn loose", ()))
        self.assertEqual(gen.split_extra_tags("#man"), ("#man", ()))
        self.assertEqual(gen.split_extra_tags("a value#man"), ("a value#man", ()))
        self.assertEqual(gen.split_extra_tags("a #x #x"), ("a", ("x",)))

    def test_a_when_suffix_is_split_off_the_heading(self):
        self.assertEqual(gen.split_extra_heading("Men's Attributes (when: man, Noble)"),
                         ("Men's Attributes", ("man", "noble")))
        self.assertEqual(gen.split_extra_heading("Styles"), ("Styles", None))
        for heading, message in [
            ("T (when: )", "table 'T' has an empty (when:)"),
            ("T (when: a, )", "table 'T' has an empty entry in (when:)"),
            ("T (when: a b)", "table 'T': 'a b' is not a tag (letters, digits, - and _)"),
        ]:
            with self.subTest(heading=heading), self.assertRaises(ValueError) as ctx:
                gen.split_extra_heading(heading)
            self.assertEqual(str(ctx.exception), message)

    def test_markdown_values_names_gates_and_tags(self):
        extra = self.load()
        self.assertIsInstance(extra, dict)
        self.assertEqual(list(extra), ["Styles", "Men's Attributes", "Scars", "Jewellery"])
        self.assertEqual(extra["Styles"], [("Rugged dockworker", 2), ("Sharp-suited broker", 1),
                                           ("Elegant courtesan", 2)])
        self.assertEqual(extra.when, {"Men's Attributes": ("man",), "Scars": ("scarred",),
                                      "Jewellery": ("woman", "noble")})
        self.assertEqual(extra.tags["Styles"]["Elegant courtesan"], ("woman", "noble"))
        self.assertEqual(extra.tags["Men's Attributes"], {"heavy stubble": ("scarred",)})
        self.assertNotIn("Scars", extra.tags)

    def test_the_same_bullet_with_different_tags_is_one_row(self):
        extra = self.load("## T\n- a #x\n- x2 a #y\n")
        self.assertEqual(extra["T"], [("a", 3)])
        self.assertEqual(extra.tags["T"]["a"], ("x", "y"))

    def test_a_repeated_heading_must_agree_about_its_gate(self):
        self.refused("styles.md: table 'G' is repeated with a different (when:)",
                     [self.write("styles.md", "## T\n- a #x\n\n## G (when: x)\n- b\n\n## G\n- c\n")])
        extra = self.load("## T\n- a #x\n\n## G (when: x)\n- b\n\n## G (when: x)\n- c\n")
        self.assertEqual(extra["G"], [("b", 1), ("c", 1)])

    def test_a_bad_heading_names_the_file(self):
        self.refused("styles.md: table 'T' has an empty (when:)",
                     [self.write("styles.md", "## T (when:)\n- a\n")])

    def test_json_rows_carry_tags_and_tables_carry_gates(self):
        path = self.write("set.json", {
            "Styles": [{"value": "Rugged dockworker", "weight": 2, "tags": ["Man"]}],
            "Men's Attributes": {"when": ["man"], "rows": [{"value": "heavy stubble"}]},
        })
        extra = gen.load_extra_tables([path])
        self.assertEqual(extra["Men's Attributes"], [("heavy stubble", 1)])
        self.assertEqual(extra.when, {"Men's Attributes": ("man",)})
        self.assertEqual(extra.tags, {"Styles": {"Rugged dockworker": ("man",)}})

    def test_json_gate_and_tag_errors_name_the_file(self):
        for data in [
            {"T": {"when": [], "rows": [{"value": "a"}]}},
            {"T": {"when": ["a b"], "rows": [{"value": "a"}]}},
            {"T": {"when": ["a"], "rows": []}},
            {"T": [{"value": "a", "tags": "man"}]},
            {"T": [{"value": "a", "tags": ["no spaces"]}]},
        ]:
            with self.subTest(data=data), self.assertRaisesRegex(ValueError, "^bad.json: "):
                gen.load_extra_tables([self.write("bad.json", data)])

    def test_the_markdown_file_matches_its_json_twin(self):
        md = self.load("## S\n- x2 a #m\n\n## G (when: m)\n- b\n")
        js = gen.load_extra_tables([self.write("twin.json", {
            "S": [{"value": "a", "weight": 2, "tags": ["m"]}],
            "G": {"when": ["m"], "rows": [{"value": "b"}]},
        })])
        self.assertEqual((md, md.when, md.tags), (js, js.when, js.tags))


class TestOrder(GateCase):
    def test_a_gate_above_its_opener_is_refused(self):
        self.refused("styles.md: gated table 'G' comes before 'S', the table that opens it (when: m)",
                     [self.write("styles.md", "## G (when: m)\n- b\n\n## S\n- a #m\n")])

    def test_order_runs_across_files_in_argument_order(self):
        gated = self.write("a.md", "## G (when: m)\n- b\n")
        opener = self.write("b.md", "## S\n- a #m\n")
        self.assertEqual(list(gen.load_extra_tables([opener, gated])), ["S", "G"])
        self.refused("a.md: gated table 'G' comes before 'S', the table that opens it (when: m)",
                     [gated, opener])

    def test_order_is_checked_before_only_narrows(self):
        with self.assertRaisesRegex(ValueError, "comes before"):
            self.load("## G (when: m)\n- b\n\n## S\n- a #m\n", only=["S"])

    def test_only_keeps_the_gates_of_the_tables_it_keeps(self):
        extra = self.load(only=["Styles", "Scars"])
        self.assertEqual(extra.when, {"Scars": ("scarred",)})
        self.assertEqual(list(extra.tags), ["Styles"])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest test.test_extra_table_gates -v`
Expected: errors such as `AttributeError: module 'gennpc' has no attribute 'split_extra_tags'`.

- [ ] **Step 3: Implement the helpers and loader**

In `generate-npc.py`, directly above `def load_extra_tables`, add:

```python
# Tag gates on private tables (docs/superpowers/specs/
# 2026-09-16-secret-table-gates-design.md). The trailing '#tag' run of a
# bullet says which gated tables its value opens; '(when: a, b)' at the end
# of a heading makes a table roll only once an earlier value carries a or b.
# lancer-npc-import-gui/public/secret-gates.js mirrors these rules and texts.
EXTRA_TAG = re.compile(r"[A-Za-z0-9_-]+")
_EXTRA_TRAILING_TAGS = re.compile(r"((?:\s+#[A-Za-z0-9_-]+)+)\s*$")
_EXTRA_WHEN = re.compile(r"^(.*?)\s*\(when:([^)]*)\)\s*$", re.IGNORECASE)


class ExtraTables(dict):
    """load_extra_tables()'s result: {name: [(value, weight)]}, plus the gates.

    `when` maps a gated table to the tuple of tags that open it; `tags` maps a
    table to {value: tuple of tags} for the values that carry any. A plain
    dict still rolls, ungated, so callers that build one by hand keep working.
    """

    def __init__(self, rows=(), when=None, tags=None):
        super().__init__(rows)
        self.when = dict(when or {})
        self.tags = dict(tags or {})


def split_extra_tags(text):
    """'Rugged dockworker #man #Noble' -> ('Rugged dockworker', ('man', 'noble')).

    Only the trailing run counts, and only when text is left in front of it,
    so 'a #3 jersey' and a bare '#man' are values, not tags.
    """
    match = _EXTRA_TRAILING_TAGS.search(text)
    if not match or not text[:match.start()].strip():
        return text, ()
    tags = re.findall(r"#([A-Za-z0-9_-]+)", match.group(1))
    return text[:match.start()].rstrip(), tuple(dict.fromkeys(tag.lower() for tag in tags))


def extra_when(name, tags):
    """A gate's tag list, checked and lower-cased, in first-seen order."""
    if not isinstance(tags, list) or not tags or all(
            isinstance(tag, str) and not tag.strip() for tag in tags):
        raise ValueError("table '%s' has an empty (when:)" % name)
    cleaned = []
    for tag in tags:
        if not isinstance(tag, str) or not tag.strip():
            raise ValueError("table '%s' has an empty entry in (when:)" % name)
        tag = tag.strip()
        if not EXTRA_TAG.fullmatch(tag):
            raise ValueError("table '%s': '%s' is not a tag (letters, digits, - and _)" % (name, tag))
        cleaned.append(tag.lower())
    return tuple(dict.fromkeys(cleaned))


def split_extra_heading(heading):
    """"Men's Attributes (when: man)" -> ("Men's Attributes", ("man",)); no suffix -> (heading, None)."""
    match = _EXTRA_WHEN.match(heading)
    if not match:
        return heading, None
    name = match.group(1).strip()
    return name, extra_when(name, match.group(2).split(","))
```

Replace the body of `load_extra_tables` (keep its docstring, but replace the sentence starting "A markdown bullet is taken whole" through "filtered." with: "A markdown bullet is taken whole apart from its trailing '#tag's: the '||' flags and '=> Name' references the default tables carry mean nothing here. Tags and '(when:)' gates are described above ExtraTables."), from `extra = {}` to `return extra`, with:

```python
    extra = ExtraTables()
    origin = {}
    for path in paths:
        path = Path(path)
        kind = path.suffix.lower()
        if kind not in (".json", ".md"):
            raise ValueError("%s: an extra tables file is .json or .md" % path.name)
        try:
            if kind == ".md":
                data = _markdown_extra_rows(path)
            else:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
        except OSError as exc:
            raise ValueError("%s: cannot read the extra tables file: %s" % (path.name, exc))
        except json.JSONDecodeError as exc:
            raise ValueError("%s: not valid JSON: %s" % (path.name, exc))
        except ValueError as exc:
            raise ValueError("%s: %s" % (path.name, exc))
        if not isinstance(data, dict):
            raise ValueError("%s: an extra tables file is one JSON object of "
                             "table name -> list of rows" % path.name)
        if not data:
            raise ValueError("%s: holds no tables" % path.name)
        for name, spec in data.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("%s: a table name must be non-blank text" % path.name)
            if name in REQUIRED_TABLES:
                raise ValueError(
                    "%s: '%s' is a default table; pass --disable-table %s and give "
                    "the private table another name" % (path.name, name, name))
            if name in extra:
                raise ValueError("%s: table '%s' is already loaded from another file"
                                 % (path.name, name))
            gate, rows = None, spec
            if isinstance(spec, dict):
                try:
                    gate = extra_when(name, spec.get("when"))
                except ValueError as exc:
                    raise ValueError("%s: %s" % (path.name, exc))
                rows = spec.get("rows")
            if not isinstance(rows, list) or not rows:
                raise ValueError("%s: table '%s' must be a non-empty list of rows"
                                 % (path.name, name))
            options, row_tags = [], {}
            for row in rows:
                if not isinstance(row, dict) or not isinstance(row.get("value"), str) \
                        or not row["value"].strip():
                    raise ValueError(
                        "%s: every row of '%s' is {\"value\": text, \"weight\": number}"
                        % (path.name, name))
                weight = row.get("weight", 1)
                if isinstance(weight, bool) or not isinstance(weight, (int, float)) \
                        or weight <= 0:
                    raise ValueError("%s: '%s' row %r has a weight that is not a "
                                     "positive number" % (path.name, name, row["value"]))
                tags = row.get("tags", [])
                if not isinstance(tags, list) or any(
                        not isinstance(tag, str) or not EXTRA_TAG.fullmatch(tag) for tag in tags):
                    raise ValueError("%s: '%s' row %r has tags that are not a list of "
                                     "letters, digits, - and _" % (path.name, name, row["value"]))
                value = row["value"].strip()
                options.append((value, weight))
                known = row_tags.get(value, ())
                row_tags[value] = tuple(dict.fromkeys(known + tuple(tag.lower() for tag in tags)))
            extra[name] = options
            origin[name] = path.name
            if gate:
                extra.when[name] = gate
            if any(row_tags.values()):
                extra.tags[name] = {value: tags for value, tags in row_tags.items() if tags}
    _check_gate_order(extra, origin)
    if only:
        missing = [name for name in only if name not in extra]
        if missing:
            raise ValueError("no loaded extra tables file holds: %s (loaded: %s)"
                             % (", ".join(missing), ", ".join(extra) or "none"))
        wanted = set(only)
        extra = ExtraTables(
            ((name, rows) for name, rows in extra.items() if name in wanted),
            when={name: gate for name, gate in extra.when.items() if name in wanted},
            tags={name: tags for name, tags in extra.tags.items() if name in wanted})
    for name, value in (values or {}).items():
        if name not in extra:
            raise ValueError("fixed value names an unselected extra table: %s" % name)
        matches = [(v, w) for v, w in extra[name] if v == value]
        if not matches:
            raise ValueError("value is not offered by extra table '%s': %s" % (name, value))
        extra[name] = matches
    return extra


def _check_gate_order(extra, origin):
    """Refuse a gated table loaded above every table that could open it.

    A tag no loaded table carries is not an error: the file holding the
    opener may simply not be part of this run, and the gate stays shut.
    """
    names = list(extra)
    carried = {name: {tag for tags in extra.tags.get(name, {}).values() for tag in tags}
               for name in names}
    for index, name in enumerate(names):
        need = extra.when.get(name)
        if not need or any(carried[other] & set(need) for other in names[:index]):
            continue
        later = [other for other in names[index + 1:] if carried[other] & set(need)]
        if later:
            raise ValueError("%s: gated table '%s' comes before '%s', the table that opens it "
                             "(when: %s)" % (origin[name], name, later[0], ", ".join(need)))
```

Replace `_markdown_extra_rows` with:

```python
def _markdown_extra_rows(path):
    """A markdown tables file as the row objects a JSON one would hold.

    parse_tables() expands 'x3 bullet' into three identical strings; this
    counts them back down, first appearance keeping the row's place, so a
    markdown table and the JSON table it is equivalent to load the same.
    Trailing '#tag's are split off each value (the same text with different
    tags is one row holding all of them) and a '(when:)' heading suffix
    becomes the object form {"when": [...], "rows": [...]}.
    """
    data, gates = {}, {}
    for heading, options in parse_tables(path).items():
        name, gate = split_extra_heading(heading)
        if name in gates and gates[name] != gate:
            raise ValueError("table '%s' is repeated with a different (when:)" % name)
        gates[name] = gate
        rows = data.setdefault(name, {})
        for option in options:
            value, tags = split_extra_tags(option)
            row = rows.setdefault(value, {"value": value, "weight": 0, "tags": ()})
            row["weight"] += 1
            row["tags"] = tuple(dict.fromkeys(row["tags"] + tags))
    result = {}
    for name, rows in data.items():
        listed = [{"value": row["value"], "weight": row["weight"], "tags": list(row["tags"])}
                  if row["tags"] else {"value": row["value"], "weight": row["weight"]}
                  for row in rows.values()]
        result[name] = {"when": list(gates[name]), "rows": listed} if gates[name] else listed
    return result
```

- [ ] **Step 4: Run the new and existing tests**

Run: `python -m unittest test.test_extra_table_gates test.test_extra_tables -v`
Expected: `TestParsing` and `TestOrder` pass; every `test_extra_tables` test passes unchanged.

- [ ] **Step 5: Commit**

```bash
git -C "G:/GIT-REPOS/lancer-art-generator/.claude/worktrees/secret-table-gates" add generate-npc.py test/test_extra_table_gates.py
git -C "G:/GIT-REPOS/lancer-art-generator/.claude/worktrees/secret-table-gates" commit -m "read tags and when gates from private extra tables" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Generator — roll through gates and resolve fixed gated values

**Files:**
- Modify: `generate-npc.py` (`load_extra_tables` tail, new `_open_fixed_gates`, `roll_extra` L1596-1604)
- Test: `test/test_extra_table_gates.py`

**Interfaces:**
- Consumes: `ExtraTables`, `load_extra_tables` from Task 1.
- Produces: `roll_extra(extra, rng) -> {name: value}` (omits shut gated tables); `_open_fixed_gates(extra, fixed_names)` mutating `extra`.

- [ ] **Step 1: Write the failing tests**

Append to `test/test_extra_table_gates.py`:

```python
class TestRolling(GateCase):
    def test_a_gated_table_rolls_only_when_an_earlier_value_opens_it(self):
        extra = self.load()
        seen = set()
        for seed in range(200):
            rolled = gen.roll_extra(extra, random.Random(seed))
            man = rolled["Styles"] in ("Rugged dockworker", "Sharp-suited broker")
            self.assertEqual("Men's Attributes" in rolled, man)
            self.assertEqual("Jewellery" in rolled, not man)
            self.assertEqual("Scars" in rolled, rolled.get("Men's Attributes") == "heavy stubble")
            seen.add(tuple(rolled))
        self.assertIn(("Styles", "Men's Attributes", "Scars"), seen)
        self.assertIn(("Styles", "Men's Attributes"), seen)
        self.assertIn(("Styles", "Jewellery"), seen)

    def test_tags_open_tables_in_another_file(self):
        opener = self.write("a.md", "## S\n- a #m\n")
        gated = self.write("b.json", {"G": {"when": ["m"], "rows": [{"value": "b"}]}})
        self.assertEqual(gen.roll_extra(gen.load_extra_tables([opener, gated]), random.Random(0)),
                         {"S": "a", "G": "b"})

    def test_a_tag_no_loaded_table_carries_leaves_the_gate_shut(self):
        extra = gen.load_extra_tables([self.write("a.md", "## G (when: m)\n- b\n")])
        self.assertEqual(gen.roll_extra(extra, random.Random(1)), {})

    def test_an_unticked_opener_opens_nothing(self):
        self.assertEqual(gen.roll_extra(self.load(only=["Men's Attributes"]), random.Random(0)), {})

    def test_values_never_carry_their_tags(self):
        for seed in range(20):
            rolled = gen.roll_extra(self.load(), random.Random(seed))
            self.assertFalse(any("#" in value for value in rolled.values()), rolled)

    def test_a_set_without_gates_rolls_exactly_as_before(self):
        plain = {"a": [("x", 1), ("y", 2)], "b": [("z", 1), ("w", 1)]}
        path = self.write("plain.json", {name: [{"value": v, "weight": w} for v, w in rows]
                                         for name, rows in plain.items()})
        extra = gen.load_extra_tables([path])
        for seed in range(20):
            rng = random.Random(seed)
            expected = {name: rng.choices([v for v, _ in rows], [w for _, w in rows])[0]
                        for name, rows in plain.items()}
            self.assertEqual(gen.roll_extra(extra, random.Random(seed)), expected)
            self.assertEqual(gen.roll_extra(dict(plain), random.Random(seed)), expected)


class TestFixedGatedValues(GateCase):
    def test_a_fixed_gated_value_narrows_its_single_random_opener(self):
        extra = self.load(values={"Men's Attributes": "broad shoulders"})
        self.assertEqual(extra["Styles"], [("Rugged dockworker", 2), ("Sharp-suited broker", 1)])
        for seed in range(30):
            self.assertEqual(gen.roll_extra(extra, random.Random(seed))["Men's Attributes"],
                             "broad shoulders")

    def test_narrowing_follows_a_chain(self):
        extra = self.load(values={"Scars": "a burn scar across one cheek"})
        self.assertEqual(extra["Men's Attributes"], [("heavy stubble", 1)])
        self.assertEqual([v for v, _ in extra["Styles"]], ["Rugged dockworker", "Sharp-suited broker"])
        for seed in range(10):
            self.assertIn("Scars", gen.roll_extra(extra, random.Random(seed)))

    def test_a_fixed_opener_that_opens_the_gate_is_enough(self):
        extra = self.load(values={"Styles": "Sharp-suited broker", "Men's Attributes": "broad shoulders"})
        self.assertEqual(gen.roll_extra(extra, random.Random(0))["Men's Attributes"], "broad shoulders")

    def test_impossible_selections_are_refused(self):
        styles = self.write("styles.md", STYLES_MD)
        two = self.write("two.md", "## A\n- a #m\n\n## B\n- b #m\n\n## G (when: m)\n- g\n")
        cases = [
            (dict(values={"Styles": "Elegant courtesan", "Men's Attributes": "broad shoulders"}),
             [styles],
             "extra table 'Men's Attributes' has a fixed value but 'Styles' is fixed to "
             "'Elegant courtesan', which is not #man"),
            (dict(only=["Men's Attributes"], values={"Men's Attributes": "broad shoulders"}),
             [styles],
             "extra table 'Men's Attributes' has a fixed value but nothing selected can open it "
             "(when: man)"),
            (dict(values={"Men's Attributes": "broad shoulders", "Jewellery": "a thin gold circlet"}),
             [styles],
             "extra table 'Jewellery' has a fixed value but 'Styles' is already limited to #man "
             "by 'Men's Attributes'"),
            (dict(values={"G": "g"}), [two],
             "extra table 'G' has a fixed value but 'A' and 'B' could each open it (when: m); "
             "fix or untick all but one"),
        ]
        for kwargs, paths, message in cases:
            with self.subTest(message=message):
                self.refused(message, paths, **kwargs)

    def test_fixing_one_of_several_openers_is_enough(self):
        two = self.write("two.md", "## A\n- a #m\n- c\n\n## B\n- b #m\n\n## G (when: m)\n- g\n")
        extra = gen.load_extra_tables([two], values={"A": "a", "G": "g"})
        self.assertEqual(extra["B"], [("b", 1)])
        self.assertEqual(gen.roll_extra(extra, random.Random(0))["G"], "g")


class TestCli(GateCase):
    def run_main(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = gen.main(["--tables", str(FIXTURE_TABLES), "--dry-run", "--seed", "5",
                             "--out", self.tmp.name] + list(argv))
        return code, out.getvalue()

    def test_a_fixed_gated_value_reaches_the_prompt_and_its_shut_sibling_does_not(self):
        styles = str(self.write("styles.md", STYLES_MD))
        code, out = self.run_main("--extra-tables", styles, "--count", "3",
                                  "--extra-value", "Men's Attributes=broad shoulders")
        self.assertEqual(code, 0)
        self.assertEqual(out.lower().count("broad shoulders"), 6)
        self.assertNotIn("gold circlet", out.lower())
        self.assertNotIn("#man", out.lower())

    def test_an_impossible_selection_is_a_clean_exit(self):
        styles = str(self.write("styles.md", STYLES_MD))
        with self.assertRaises(SystemExit) as ctx:
            self.run_main("--extra-tables", styles, "--extra-table", "Men's Attributes",
                          "--extra-value", "Men's Attributes=broad shoulders")
        self.assertIn("nothing selected can open it", str(ctx.exception))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest test.test_extra_table_gates -v`
Expected: `TestRolling` fails (gated tables always roll), `TestFixedGatedValues` fails (no narrowing, no refusals).

- [ ] **Step 3: Implement**

In `load_extra_tables`, replace the final `return extra` with:

```python
    _open_fixed_gates(extra, [name for name in extra if name in (values or {})])
    return extra
```

Add below `_check_gate_order`:

```python
def _open_fixed_gates(extra, fixed_names):
    """Make sure every gated table given a fixed value will be open.

    An earlier fixed table whose every row opens the gate is enough.
    Otherwise the one Random table that could open it is narrowed to its
    opening rows (and, if that table is gated too, the same is done for it).
    Anything else is a selection that cannot happen, refused with the text
    public/secret-gates.js shows in the form.
    """
    names = list(extra)
    fixed = set(fixed_names)
    narrowed_by = {}
    done = set()

    def opens(table, value, need):
        return any(tag in need for tag in extra.tags.get(table, {}).get(value, ()))

    def tag_list(tags):
        return " or ".join("#" + tag for tag in tags)

    def require(name):
        if name in done:
            return
        done.add(name)
        need = extra.when.get(name)
        if not need:
            return
        earlier = names[:names.index(name)]
        for other in earlier:
            if other in fixed and all(opens(other, v, need) for v, _ in extra[other]):
                return require(other)
        openers = [other for other in earlier if other not in fixed
                   and any(opens(other, v, need) for v, _ in extra[other])]
        head = "extra table '%s' has a fixed value but " % name
        if len(openers) == 1:
            opener = openers[0]
            extra[opener] = [(v, w) for v, w in extra[opener] if opens(opener, v, need)]
            fixed.add(opener)
            narrowed_by[opener] = (name, need)
            return require(opener)
        if openers:
            raise ValueError(head + "%s could each open it (when: %s); fix or untick all but one"
                             % (" and ".join("'%s'" % o for o in openers), ", ".join(need)))
        carriers = [other for other in earlier if other in fixed and any(
            tag in need for tags in extra.tags.get(other, {}).values() for tag in tags)]
        for other in carriers:
            if other in narrowed_by:
                by, limit = narrowed_by[other]
                raise ValueError(head + "'%s' is already limited to %s by '%s'"
                                 % (other, tag_list(limit), by))
        if carriers:
            raise ValueError(head + "'%s' is fixed to '%s', which is not %s"
                             % (carriers[0], extra[carriers[0]][0][0], tag_list(need)))
        raise ValueError(head + "nothing selected can open it (when: %s)" % ", ".join(need))

    for name in names:
        if name in fixed_names:
            require(name)
```

Replace `roll_extra` with:

```python
def roll_extra(extra, rng):
    """One weighted draw per open extra table, keyed by table name in table order.

    Drawn AFTER roll_npc() from the same generator, so loading a private set
    never moves the base NPC a seed rolls - the default tables consume the
    stream first and these read what is left. A gated table (see
    ExtraTables) is skipped, with no draw, unless a value drawn before it
    carries one of its tags; a set with no gates draws exactly as it always
    has.
    """
    when = getattr(extra, "when", {})
    tags = getattr(extra, "tags", {})
    opened, rolled = set(), {}
    for name, rows in extra.items():
        need = when.get(name)
        if need and not opened.intersection(need):
            continue
        value = rng.choices([v for v, _ in rows], [w for _, w in rows])[0]
        rolled[name] = value
        opened.update(tags.get(name, {}).get(value, ()))
    return rolled
```

- [ ] **Step 4: Run the tests**

Run: `python -m unittest test.test_extra_table_gates test.test_extra_tables -v`
Expected: all pass.
Then run the whole suite: `python -m unittest discover test` — expected: no new failures versus `main` (see Global Constraints).

- [ ] **Step 5: Commit**

```bash
git -C "G:/GIT-REPOS/lancer-art-generator/.claude/worktrees/secret-table-gates" add generate-npc.py test/test_extra_table_gates.py
git -C "G:/GIT-REPOS/lancer-art-generator/.claude/worktrees/secret-table-gates" commit -m "roll private tables through their when gates" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Generator — document tags and gates

**Files:**
- Modify: `README.md` (the `--extra-tables` section, ~L55-113)

- [ ] **Step 1: Add a subsection after the markdown shape description**

Insert, after the paragraph that describes the markdown extra tables shape:

````markdown
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
  gates it opens (letters, digits, `-`, `_`; case-insensitive).
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
````

- [ ] **Step 2: Commit**

```bash
git -C "G:/GIT-REPOS/lancer-art-generator/.claude/worktrees/secret-table-gates" add README.md
git -C "G:/GIT-REPOS/lancer-art-generator/.claude/worktrees/secret-table-gates" commit -m "document tags and when gates for private tables" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: GUI — the pure gate module

**Files:**
- Create: `public/secret-gates.js`
- Test: `test/secretGates.test.js` (create)

**Interfaces:**
- Produces (as `window.SecretGates` and `module.exports`):
  - `splitTags(text) -> { value, tags: string[] }`
  - `checkWhen(name, list) -> string[]` (throws `Error`)
  - `splitWhen(heading) -> { name, when: string[] | null }`
  - `entryKey(file, name) -> string`
  - `rollOrder(files) -> Entry[]` where `files` is the listing's `[{ file, tables, error? }]` and
    `Entry = { key, file, name, when: string[]|null, rows: [{ value, tags }], depth, openers: [{ file, name, tags }], opens: [{ tag, tables: string[] }] }`
  - `orderErrors(files) -> Map<file, message>`
  - `resolveGates(order, picks: Map<key, fixedValue|''>, { dropClosed }) -> { error: string|null, status: Map<key, { state, text, limited }> }`
    with `state` one of `'unselected' | 'rolls' | 'maybe' | 'closed'`
  - `rollOrderView(order, result, fileErrors: [{ file, error }]) -> { summary, items: [{ depth, title, file, gate, opens, status }] }`
  - `markGatedSources(preview, gatedNames: string[]) -> preview copy`
- A listing table is `{ name, count, values: string[], when?: string[], tags?: { [value]: string[] }, groups? }` (Task 5 produces this shape).

- [ ] **Step 1: Write the failing tests**

Create `test/secretGates.test.js`:

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const gates = require('../public/secret-gates');

/*
 * The gate rules shared by the Create form, the roll order panel and the
 * server's validateSelection. They mirror generate-npc.py's
 * load_extra_tables()/roll_extra() and must produce the same refusal texts
 * (see test/test_extra_table_gates.py in lancer-art-generator).
 */

const STYLES = {
    file: 'styles.md',
    tables: [
        { name: 'Styles', count: 3, values: ['Rugged dockworker', 'Sharp-suited broker', 'Elegant courtesan'],
            tags: { 'Rugged dockworker': ['man'], 'Sharp-suited broker': ['man'], 'Elegant courtesan': ['woman', 'noble'] } },
        { name: "Men's Attributes", count: 2, values: ['heavy stubble', 'broad shoulders'], when: ['man'],
            tags: { 'heavy stubble': ['scarred'] } },
        { name: 'Scars', count: 1, values: ['a burn scar across one cheek'], when: ['scarred'] },
        { name: 'Jewellery', count: 1, values: ['a thin gold circlet'], when: ['woman', 'noble'] },
    ],
};
const TWO = { file: 'two.md', tables: [
    { name: 'A', count: 2, values: ['a', 'c'], tags: { a: ['m'] } },
    { name: 'B', count: 1, values: ['b'], tags: { b: ['m'] } },
    { name: 'G', count: 1, values: ['g'], when: ['m'] },
] };
const key = (name, file = 'styles.md') => gates.entryKey(file, name);
const picks = (entries, file = 'styles.md') => new Map(Object.entries(entries).map(([name, value]) => [key(name, file), value]));
const ALL = { Styles: '', "Men's Attributes": '', Scars: '', Jewellery: '' };

test('trailing tags are split off and lower-cased; other hashes are text', () => {
    assert.deepEqual(gates.splitTags('Rugged dockworker #man #Noble'), { value: 'Rugged dockworker', tags: ['man', 'noble'] });
    assert.deepEqual(gates.splitTags('a #3 jersey worn loose'), { value: 'a #3 jersey worn loose', tags: [] });
    assert.deepEqual(gates.splitTags('#man'), { value: '#man', tags: [] });
    assert.deepEqual(gates.splitTags('a value#man'), { value: 'a value#man', tags: [] });
    assert.deepEqual(gates.splitTags('a #x #x'), { value: 'a', tags: ['x'] });
});

test('a when suffix is split off a heading with the generator texts', () => {
    assert.deepEqual(gates.splitWhen("Men's Attributes (when: man, Noble)"), { name: "Men's Attributes", when: ['man', 'noble'] });
    assert.deepEqual(gates.splitWhen('Styles'), { name: 'Styles', when: null });
    assert.throws(() => gates.splitWhen('T (when: )'), { message: "table 'T' has an empty (when:)" });
    assert.throws(() => gates.splitWhen('T (when: a, )'), { message: "table 'T' has an empty entry in (when:)" });
    assert.throws(() => gates.splitWhen('T (when: a b)'), { message: "table 'T': 'a b' is not a tag (letters, digits, - and _)" });
    assert.throws(() => gates.checkWhen('T', []), { message: "table 'T' has an empty (when:)" });
});

test('roll order lists tables in file order with depth, openers and what each opens', () => {
    const order = gates.rollOrder([STYLES, { file: 'bad.md', tables: [], error: 'nope' }]);
    assert.deepEqual(order.map(e => [e.name, e.depth]), [['Styles', 0], ["Men's Attributes", 1], ['Scars', 2], ['Jewellery', 1]]);
    assert.deepEqual(order[3].openers, [{ file: 'styles.md', name: 'Styles', tags: ['woman', 'noble'] }]);
    assert.deepEqual(order[0].opens, [{ tag: 'man', tables: ["Men's Attributes"] }, { tag: 'woman', tables: ['Jewellery'] }, { tag: 'noble', tables: ['Jewellery'] }]);
    assert.deepEqual(order[1].rows, [{ value: 'heavy stubble', tags: ['scarred'] }, { value: 'broad shoulders', tags: [] }]);
});

test('a table value named like an Object property has no tags', () => {
    const order = gates.rollOrder([{ file: 'x.md', tables: [{ name: 'T', count: 1, values: ['constructor'] }] }]);
    assert.deepEqual(order[0].rows, [{ value: 'constructor', tags: [] }]);
});

test('order errors: a gate above its opener, and a tag nothing in the folder carries', () => {
    const errors = gates.orderErrors([
        { file: 'a.md', tables: [{ name: 'G', count: 1, values: ['b'], when: ['m'] }] },
        { file: 'b.md', tables: [{ name: 'S', count: 1, values: ['a'], tags: { a: ['m'] } }, { name: 'H', count: 1, values: ['h'], when: ['zzz'] }] },
    ]);
    assert.equal(errors.get('a.md'), "gated table 'G' comes before 'S', the table that opens it (when: m)");
    assert.equal(errors.get('b.md'), "gated table 'H' has no table in the folder carrying its tags (when: zzz)");
    assert.equal(gates.orderErrors([STYLES]).size, 0);
});

test('with everything Random, gated tables may roll and say what opens them', () => {
    const { error, status } = gates.resolveGates(gates.rollOrder([STYLES]), picks(ALL));
    assert.equal(error, null);
    assert.deepEqual(status.get(key('Styles')), { state: 'rolls', text: 'rolls', limited: false });
    assert.deepEqual(status.get(key("Men's Attributes")), { state: 'maybe', text: 'rolls only if Styles rolls #man', limited: false });
    assert.deepEqual(status.get(key('Scars')), { state: 'maybe', text: "rolls only if Men's Attributes rolls #scarred", limited: false });
    assert.deepEqual(status.get(key('Jewellery')), { state: 'maybe', text: 'rolls only if Styles rolls #woman or #noble', limited: false });
});

test('a fixed opener opens its gates and closes the others', () => {
    const { error, status } = gates.resolveGates(gates.rollOrder([STYLES]), picks({ ...ALL, Styles: 'Sharp-suited broker' }));
    assert.equal(error, null);
    assert.equal(status.get(key("Men's Attributes")).state, 'rolls');
    assert.deepEqual(status.get(key('Jewellery')), { state: 'closed', limited: false,
        text: "closed — 'Styles' is fixed to 'Sharp-suited broker', which is not #woman or #noble" });
});

test('unticked tables are not selected and open nothing', () => {
    const { status } = gates.resolveGates(gates.rollOrder([STYLES]), picks({ "Men's Attributes": '' }));
    assert.deepEqual(status.get(key('Styles')), { state: 'unselected', text: 'not selected', limited: false });
    assert.deepEqual(status.get(key("Men's Attributes")), { state: 'closed', limited: false,
        text: 'closed — nothing selected can open it (when: man)' });
});

test('a fixed gated value limits its single Random opener, through a chain', () => {
    const { error, status } = gates.resolveGates(gates.rollOrder([STYLES]), picks({ ...ALL, Scars: 'a burn scar across one cheek' }));
    assert.equal(error, null);
    assert.deepEqual(status.get(key('Styles')), { state: 'rolls', limited: true, text: "rolls, limited to #man by 'Men's Attributes'" });
    assert.deepEqual(status.get(key("Men's Attributes")), { state: 'rolls', limited: true,
        text: "rolls, limited to #scarred by 'Scars'; limits 'Styles' to #man" });
    assert.deepEqual(status.get(key('Scars')), { state: 'rolls', limited: false, text: "rolls; limits 'Men's Attributes' to #scarred" });
    assert.equal(status.get(key('Jewellery')).state, 'closed');
});

test('impossible selections carry the generator refusal texts', () => {
    const order = gates.rollOrder([STYLES]);
    const cases = [
        [{ Styles: 'Elegant courtesan', "Men's Attributes": 'broad shoulders' },
            "extra table 'Men's Attributes' has a fixed value but 'Styles' is fixed to 'Elegant courtesan', which is not #man"],
        [{ "Men's Attributes": 'broad shoulders' },
            "extra table 'Men's Attributes' has a fixed value but nothing selected can open it (when: man)"],
        [{ ...ALL, "Men's Attributes": 'broad shoulders', Jewellery: 'a thin gold circlet' },
            "extra table 'Jewellery' has a fixed value but 'Styles' is already limited to #man by 'Men's Attributes'"],
    ];
    for (const [selection, message] of cases) {
        assert.equal(gates.resolveGates(order, picks(selection)).error, message);
    }
    assert.equal(gates.resolveGates(gates.rollOrder([TWO]), picks({ A: '', B: '', G: 'g' }, 'two.md')).error,
        "extra table 'G' has a fixed value but 'A' and 'B' could each open it (when: m); fix or untick all but one");
    assert.equal(gates.resolveGates(gates.rollOrder([TWO]), picks({ A: 'a', B: '', G: 'g' }, 'two.md')).error, null);
});

test('in the form, a fixed gated table nothing can open is closed rather than refused', () => {
    const order = gates.rollOrder([STYLES]);
    const shut = gates.resolveGates(order, picks({ Styles: 'Elegant courtesan', "Men's Attributes": 'broad shoulders' }), { dropClosed: true });
    assert.equal(shut.error, null);
    assert.deepEqual(shut.status.get(key("Men's Attributes")), { state: 'closed', limited: false,
        text: "closed — 'Styles' is fixed to 'Elegant courtesan', which is not #man" });
    const chained = gates.resolveGates(order, picks({ Styles: 'Elegant courtesan', "Men's Attributes": '', Scars: 'a burn scar across one cheek' }), { dropClosed: true });
    assert.equal(chained.error, null);
    assert.equal(chained.status.get(key('Scars')).text, "closed — 'Men's Attributes' is closed");
    const conflict = gates.resolveGates(order, picks({ ...ALL, "Men's Attributes": 'broad shoulders', Jewellery: 'a thin gold circlet' }), { dropClosed: true });
    assert.match(conflict.error, /already limited to #man/);
});

test('the roll order view summarises and describes every entry', () => {
    const order = gates.rollOrder([STYLES]);
    const result = gates.resolveGates(order, picks({ Styles: '', "Men's Attributes": '' }), { dropClosed: true });
    const view = gates.rollOrderView(order, result, [{ file: 'bad.md', error: 'not valid JSON' }]);
    assert.equal(view.summary, 'Roll order and gates (4 tables, 3 gated)');
    assert.deepEqual(view.items[0], { depth: 0, title: 'Styles', file: 'styles.md', gate: 'always',
        opens: "can open: #man → Men's Attributes; #woman → Jewellery; #noble → Jewellery", status: 'rolls' });
    assert.deepEqual(view.items[1], { depth: 1, title: "Men's Attributes", file: 'styles.md',
        gate: 'when: #man — opened by Styles (#man)', opens: 'can open: #scarred → Scars', status: 'rolls only if Styles rolls #man' });
    assert.equal(view.items[2].status, 'not selected');
    assert.deepEqual(view.items[4], { depth: 0, title: 'bad.md', file: 'bad.md', gate: '', opens: '', status: 'not valid JSON' });
    assert.equal(gates.rollOrderView([], gates.resolveGates([], new Map()), []).summary, 'Roll order and gates (no tables)');
});

test('preview sources of gated tables are marked as conditional', () => {
    const preview = { portrait: [{ id: 'extra:G', randomSources: ['G'] }, { id: 'shot', randomSources: ['Backdrop'] }, { id: 'x' }], token: [] };
    const marked = gates.markGatedSources(preview, ['G']);
    assert.deepEqual(marked.portrait[0].randomSources, ['G if opened']);
    assert.deepEqual(marked.portrait[1].randomSources, ['Backdrop']);
    assert.deepEqual(marked.portrait[2], { id: 'x' });
    assert.deepEqual(preview.portrait[0].randomSources, ['G']);
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `node --test test/secretGates.test.js`
Expected: FAIL with `Cannot find module '../public/secret-gates'`.

- [ ] **Step 3: Implement `public/secret-gates.js`**

```js
/* Tag gates for Secret mode's private tables, shared by the Create form,
 * its roll order panel and the server (lib/secretTables.js). A bullet's
 * trailing '#tag's name the gated tables its value opens; '(when: a, b)' at
 * the end of a heading makes a table roll only once an earlier value carries
 * a or b. Mirrors generate-npc.py (split_extra_tags, extra_when,
 * _check_gate_order, _open_fixed_gates, roll_extra), texts included. */
(function (root) {
  'use strict';
  const TAG_RE = /^[A-Za-z0-9_-]+$/;
  const unique = list => [...new Set(list)];
  const tagList = tags => tags.map(tag => `#${tag}`).join(' or ');
  const hasTag = (row, need) => row.tags.some(tag => need.includes(tag));

  function splitTags(text) {
    const match = text.match(/((?:\s+#[A-Za-z0-9_-]+)+)\s*$/);
    if (!match || !text.slice(0, match.index).trim()) return { value: text, tags: [] };
    return { value: text.slice(0, match.index).trimEnd(),
      tags: unique(match[1].match(/#[A-Za-z0-9_-]+/g).map(tag => tag.slice(1).toLowerCase())) };
  }

  function checkWhen(name, list) {
    if (!Array.isArray(list) || !list.length || list.every(tag => typeof tag === 'string' && !tag.trim())) {
      throw new Error(`table '${name}' has an empty (when:)`);
    }
    return unique(list.map(tag => {
      if (typeof tag !== 'string' || !tag.trim()) throw new Error(`table '${name}' has an empty entry in (when:)`);
      const trimmed = tag.trim();
      if (!TAG_RE.test(trimmed)) throw new Error(`table '${name}': '${trimmed}' is not a tag (letters, digits, - and _)`);
      return trimmed.toLowerCase();
    }));
  }

  function splitWhen(heading) {
    const match = heading.match(/^(.*?)\s*\(when:([^)]*)\)\s*$/i);
    if (!match) return { name: heading, when: null };
    const name = match[1].trim();
    return { name, when: checkWhen(name, match[2].split(',')) };
  }

  const entryKey = (file, name) => `${file}\n${name}`;

  function rollOrder(files) {
    const order = [];
    for (const file of files) {
      if (file.error) continue;
      for (const table of file.tables || []) {
        const tags = table.tags || {};
        order.push({ key: entryKey(file.file, table.name), file: file.file, name: table.name, when: table.when || null,
          rows: table.values.map(value => ({ value, tags: Object.hasOwn(tags, value) ? tags[value] : [] })) });
      }
    }
    order.forEach((entry, index) => {
      const earlier = order.slice(0, index);
      entry.openers = !entry.when ? [] : earlier
        .filter(other => other.rows.some(row => hasTag(row, entry.when)))
        .map(other => ({ file: other.file, name: other.name,
          tags: entry.when.filter(tag => other.rows.some(row => row.tags.includes(tag))) }));
      entry.depth = !entry.when ? 0 : 1 + Math.max(0, ...entry.openers.map(opener =>
        earlier.find(other => other.file === opener.file && other.name === opener.name).depth));
    });
    for (const entry of order) {
      entry.opens = unique(entry.rows.flatMap(row => row.tags))
        .map(tag => ({ tag, tables: order.filter(other => other.when?.includes(tag)
          && other.openers.some(opener => opener.file === entry.file && opener.name === entry.name)).map(other => other.name) }))
        .filter(item => item.tables.length);
    }
    return order;
  }

  function orderErrors(files) {
    const order = rollOrder(files);
    const errors = new Map();
    order.forEach((entry, index) => {
      if (!entry.when || entry.openers.length || errors.has(entry.file)) return;
      const label = entry.when.join(', ');
      const later = order.slice(index + 1).find(other => other.rows.some(row => hasTag(row, entry.when)));
      errors.set(entry.file, later
        ? `gated table '${entry.name}' comes before '${later.name}', the table that opens it (when: ${label})`
        : `gated table '${entry.name}' has no table in the folder carrying its tags (when: ${label})`);
    });
    return errors;
  }

  function resolveGates(order, picks, { dropClosed = false } = {}) {
    const selected = order.filter(entry => picks.has(entry.key));
    const rows = new Map(selected.map(entry => [entry.key, entry.rows]));
    const fixed = new Map();
    for (const entry of selected) {
      const value = picks.get(entry.key);
      if (!value) continue;
      rows.set(entry.key, entry.rows.filter(row => row.value === value));
      fixed.set(entry.key, { by: null, need: null });
    }
    const dropped = new Map();
    const done = new Set();

    function follow(opener) {
      const inner = require(opener);
      if (inner?.drop) { dropped.set(opener.key, inner.drop); return { drop: `'${opener.name}' is closed` }; }
      return inner;
    }

    function require(entry) {
      if (done.has(entry.key)) return null;
      done.add(entry.key);
      if (!entry.when) return null;
      const need = entry.when;
      const live = selected.filter(other => !dropped.has(other.key));
      const earlier = live.slice(0, live.indexOf(entry));
      const sure = earlier.find(other => fixed.has(other.key) && rows.get(other.key).every(row => hasTag(row, need)));
      if (sure) return follow(sure);
      const openers = earlier.filter(other => !fixed.has(other.key) && rows.get(other.key).some(row => hasTag(row, need)));
      if (openers.length === 1) {
        const [opener] = openers;
        rows.set(opener.key, rows.get(opener.key).filter(row => hasTag(row, need)));
        fixed.set(opener.key, { by: entry.name, need });
        return follow(opener);
      }
      const head = `extra table '${entry.name}' has a fixed value but `;
      if (openers.length) {
        return { error: `${head}${openers.map(other => `'${other.name}'`).join(' and ')} could each open it (when: ${need.join(', ')}); fix or untick all but one` };
      }
      const carriers = earlier.filter(other => fixed.has(other.key) && other.rows.some(row => hasTag(row, need)));
      const narrowed = carriers.find(other => fixed.get(other.key).by);
      if (narrowed) {
        const { by, need: limit } = fixed.get(narrowed.key);
        return { error: `${head}'${narrowed.name}' is already limited to ${tagList(limit)} by '${by}'` };
      }
      const reason = carriers.length
        ? `'${carriers[0].name}' is fixed to '${rows.get(carriers[0].key)[0].value}', which is not ${tagList(need)}`
        : `nothing selected can open it (when: ${need.join(', ')})`;
      return dropClosed ? { drop: reason } : { error: head + reason };
    }

    let error = null;
    for (const entry of selected) {
      if (!picks.get(entry.key) || !entry.when) continue;
      const outcome = require(entry);
      if (outcome?.drop) dropped.set(entry.key, outcome.drop);
      if (outcome?.error) { error = outcome.error; break; }
    }

    const status = new Map();
    const state = new Map();
    for (const entry of order) {
      const limit = fixed.get(entry.key);
      const limited = Boolean(limit?.by);
      if (!picks.has(entry.key)) { status.set(entry.key, { state: 'unselected', text: 'not selected', limited: false }); continue; }
      let current;
      let text;
      if (dropped.has(entry.key)) {
        current = 'closed'; text = `closed — ${dropped.get(entry.key)}`;
      } else if (!entry.when) {
        current = 'rolls';
      } else {
        const earlier = selected.slice(0, selected.indexOf(entry)).filter(other => state.get(other.key) !== 'closed');
        const could = earlier.filter(other => rows.get(other.key).some(row => hasTag(row, entry.when)));
        if (!could.length) {
          const carrier = earlier.find(other => fixed.has(other.key) && !fixed.get(other.key).by && other.rows.some(row => hasTag(row, entry.when)));
          current = 'closed';
          text = `closed — ${carrier
            ? `'${carrier.name}' is fixed to '${rows.get(carrier.key)[0].value}', which is not ${tagList(entry.when)}`
            : `nothing selected can open it (when: ${entry.when.join(', ')})`}`;
        } else if (could.some(other => state.get(other.key) === 'rolls' && rows.get(other.key).every(row => hasTag(row, entry.when)))) {
          current = 'rolls';
        } else {
          current = 'maybe';
          text = `rolls only if ${could.map(other => other.name).join(' or ')} rolls ${tagList(entry.when)}`;
        }
      }
      if (current === 'rolls') {
        const limits = selected.filter(other => fixed.get(other.key)?.by === entry.name)
          .map(other => `limits '${other.name}' to ${tagList(fixed.get(other.key).need)}`);
        text = [limited ? `rolls, limited to ${tagList(limit.need)} by '${limit.by}'` : 'rolls', ...limits].join('; ');
      }
      state.set(entry.key, current);
      status.set(entry.key, { state: current, text, limited });
    }
    return { error, status };
  }

  function rollOrderView(order, result, fileErrors = []) {
    const gated = order.filter(entry => entry.when).length;
    const summary = order.length ? `Roll order and gates (${order.length} tables, ${gated} gated)` : 'Roll order and gates (no tables)';
    const items = order.map(entry => ({
      depth: entry.depth,
      title: entry.name,
      file: entry.file,
      gate: !entry.when ? 'always' : `when: ${entry.when.map(tag => `#${tag}`).join(', ')} — ${entry.openers.length
        ? `opened by ${entry.openers.map(opener => `${opener.name} (${opener.tags.map(tag => `#${tag}`).join(', ')})`).join(', ')}`
        : 'nothing listed opens it'}`,
      opens: entry.opens.length ? `can open: ${entry.opens.map(item => `#${item.tag} → ${item.tables.join(', ')}`).join('; ')}` : '',
      status: result.status.get(entry.key)?.text || 'not selected',
    }));
    for (const { file, error } of fileErrors) items.push({ depth: 0, title: file, file, gate: '', opens: '', status: error });
    return { summary, items };
  }

  function markGatedSources(preview, gatedNames) {
    const copy = {};
    for (const [target, parts] of Object.entries(preview || {})) {
      copy[target] = !Array.isArray(parts) ? parts : parts.map(part => !part?.randomSources ? part
        : { ...part, randomSources: part.randomSources.map(source => gatedNames.includes(source) ? `${source} if opened` : source) });
    }
    return copy;
  }

  const api = { splitTags, checkWhen, splitWhen, entryKey, rollOrder, orderErrors, resolveGates, rollOrderView, markGatedSources, TAG_RE };
  root.SecretGates = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window === 'undefined' ? globalThis : window);
```

- [ ] **Step 4: Run the tests**

Run: `node --test test/secretGates.test.js`
Expected: all pass. If an expected text differs, fix the module (the texts in the test are the contract shared with the generator), not the test.

- [ ] **Step 5: Commit**

```bash
git -C "G:/GIT-REPOS/lancer-npc-import-gui/.claude/worktrees/secret-table-gates" add public/secret-gates.js test/secretGates.test.js
git -C "G:/GIT-REPOS/lancer-npc-import-gui/.claude/worktrees/secret-table-gates" commit -m "add the shared tag gate rules for secret tables" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: GUI — listing and server validation

**Files:**
- Modify: `lib/secretTables.js` (`markdownTables` L28-58, `jsonTables` L60-81, `listSecretTables` L113-125, `validateSelection` L127-181)
- Test: `test/secretTables.test.js`, `test/api.secretTables.test.js`

**Interfaces:**
- Consumes: `require('../public/secret-gates')` from Task 4.
- Produces: listing tables `{ name, count, values, when?, tags?, groups? }`; `validateSelection` throws the Task 4 refusal texts.

- [ ] **Step 1: Write the failing tests**

Append to `test/secretTables.test.js` (and add `validateSelection` to the `require('../lib/secretTables')` destructuring at the top):

```js
const GATED_MD = [
    '## Styles', '- x2 Rugged dockworker #man', '- Sharp-suited broker #Man', '- x2 Elegant courtesan #woman #noble',
    '', "## Men's Attributes (when: man)", '- heavy stubble #scarred', '- broad shoulders',
    '', '## Jewellery (when: woman, noble)', '- a thin gold circlet',
].join('\n');

test('markdown tags and gates are parsed off values and headings', (t) => {
    const dir = folder(t, { 'styles.md': GATED_MD });
    assert.deepEqual(listSecretTables(dir).files[0].tables, [
        { name: 'Styles', count: 3, values: ['Rugged dockworker', 'Sharp-suited broker', 'Elegant courtesan'],
            tags: { 'Rugged dockworker': ['man'], 'Sharp-suited broker': ['man'], 'Elegant courtesan': ['woman', 'noble'] } },
        { name: "Men's Attributes", count: 2, values: ['heavy stubble', 'broad shoulders'], when: ['man'],
            tags: { 'heavy stubble': ['scarred'] } },
        { name: 'Jewellery', count: 1, values: ['a thin gold circlet'], when: ['woman', 'noble'] },
    ]);
});

test('json rows carry tags and object tables carry gates', (t) => {
    const dir = folder(t, { 'set.json': JSON.stringify({
        Styles: [{ value: 'Rugged dockworker', tags: ['Man'] }],
        "Men's Attributes": { when: ['man'], rows: [{ value: 'heavy stubble' }] },
    }) });
    assert.deepEqual(listSecretTables(dir).files[0].tables, [
        { name: 'Styles', count: 1, values: ['Rugged dockworker'], tags: { 'Rugged dockworker': ['man'] } },
        { name: "Men's Attributes", count: 1, values: ['heavy stubble'], when: ['man'] },
    ]);
});

test('gate errors are reported against the file that holds the gate', (t) => {
    const dir = folder(t, {
        'a.md': '## G (when: m)\n- b\n',
        'b.md': '## S\n- a #m\n',
        'c.md': '## T (when:)\n- a\n',
        'd.md': '## U\n- a #x\n\n## H (when: x)\n- b\n\n## H\n- c\n',
        'e.json': JSON.stringify({ T: [{ value: 'a', tags: ['no spaces'] }] }),
        'f.md': '## Lonely (when: nobody)\n- x\n',
    });
    const errors = Object.fromEntries(listSecretTables(dir).files.map(file => [file.file, file.error]));
    assert.equal(errors['a.md'], "gated table 'G' comes before 'S', the table that opens it (when: m)");
    assert.equal(errors['b.md'], undefined);
    assert.equal(errors['c.md'], "table 'T' has an empty (when:)");
    assert.equal(errors['d.md'], "table 'H' is repeated with a different (when:)");
    assert.match(errors['e.json'], /tags that are not a list of letters, digits, - and _/);
    assert.equal(errors['f.md'], "gated table 'Lonely' has no table in the folder carrying its tags (when: nobody)");
});

test('validateSelection refuses impossible gate selections with the generator texts', (t) => {
    const dir = folder(t, { 'styles.md': GATED_MD });
    const listing = listSecretTables(dir);
    const pick = (values, tables) => ({ extraTables: [{ file: 'styles.md', ...(tables ? { tables } : {}), values }] });
    assert.throws(() => validateSelection(pick({ Styles: 'Elegant courtesan', "Men's Attributes": 'broad shoulders' }), listing, []),
        { message: "extra table 'Men's Attributes' has a fixed value but 'Styles' is fixed to 'Elegant courtesan', which is not #man" });
    assert.throws(() => validateSelection(pick({ "Men's Attributes": 'broad shoulders' }, ["Men's Attributes"]), listing, []),
        { message: "extra table 'Men's Attributes' has a fixed value but nothing selected can open it (when: man)" });
    const ok = validateSelection(pick({ "Men's Attributes": 'broad shoulders' }), listing, []);
    assert.deepEqual(ok.extraValues, [{ table: "Men's Attributes", value: 'broad shoulders' }]);
});
```

In `test/api.secretTables.test.js`, add a gated file to `setup()` right after the `b.md` line:

```js
    fs.writeFileSync(path.join(tablesDir, 'c.md'), '## style\n\n- rugged #man\n- elegant #woman\n\n## beard (when: man)\n\n- stubble\n');
```

and append:

```js
test('the listing carries gates and tags, and an impossible gate selection is refused', async (t) => {
    const { call } = await setup(t);
    const listing = await (await call('/api/secret/tables', undefined, true)).json();
    const gated = listing.files.find(file => file.file === 'c.md');
    assert.deepEqual(gated.tables[1], { name: 'beard', count: 1, values: ['stubble'], when: ['man'] });
    assert.deepEqual(gated.tables[0].tags, { rugged: ['man'], elegant: ['woman'] });
    const refused = await call('/api/secret/create', { kind: 'npc', count: 1,
        extraTables: [{ file: 'c.md', values: { style: 'elegant', beard: 'stubble' } }] }, true);
    assert.equal(refused.status, 400);
    assert.match((await refused.json()).error, /'style' is fixed to 'elegant', which is not #man/);
});
```

Before writing this test, read `setup()`'s return value and an existing refusal test in `api.secretTables.test.js` (for example "the public path, an unknown file, a bad file and unknown tables are refused") and match its helper names, status code and error field exactly. The existing listing test asserts `data.files.map((f) => f.file)` equals `['a.json', 'b.md', 'bad.json']` (L165); change it to `['a.json', 'b.md', 'bad.json', 'c.md']`, and check that test for any other per-file assertions that the new file shifts.

- [ ] **Step 2: Run to verify they fail**

Run: `node --test test/secretTables.test.js test/api.secretTables.test.js`
Expected: the new tests fail (headings keep `(when: man)`, values keep `#man`, no refusals).

- [ ] **Step 3: Implement**

In `lib/secretTables.js`:

1. Under the existing `require`s add `const gates = require('../public/secret-gates');`, and extend the header comment's `.md` line with: `'#tag' at a bullet's end and '(when: tag)' at a heading's end gate tables (public/secret-gates.js)`.

2. Replace `markdownTables` with:

```js
/** '##' opens a table, '###' groups its choices, '- bullet' is a row; '#tag' and '(when:)' gate them. */
function markdownTables(text) {
    const tables = new Map();
    let current = null;
    let category = '';
    for (const line of text.split(/\r?\n/)) {
        const heading = line.match(/^##\s+(?!#)\s*(.*?)\s*$/);
        if (heading) {
            const { name, when } = gates.splitWhen(heading[1]);
            if (tables.has(name) && String(tables.get(name).when) !== String(when)) {
                throw new Error(`table '${name}' is repeated with a different (when:)`);
            }
            if (!tables.has(name)) tables.set(name, { when, count: 0, values: [], tags: new Map(), groups: new Map() });
            current = name;
            category = '';
            continue;
        }
        const subsection = line.match(/^###\s+(?!#)\s*(.*?)\s*$/);
        if (subsection) {
            category = subsection[1];
            continue;
        }
        if (current && /^-\s+\S/.test(line)) {
            if (/^-\s+x0+\s/.test(line)) continue;
            const { value, tags } = gates.splitTags(line.replace(/^-\s+/, '').replace(/^x\d+\s+/, '').trim());
            const table = tables.get(current);
            table.count += 1;
            if (!table.values.includes(value)) table.values.push(value);
            table.tags.set(value, [...new Set([...(table.tags.get(value) || []), ...tags])]);
            if (!table.groups.has(category)) table.groups.set(category, new Set());
            table.groups.get(category).add(value);
        }
    }
    return [...tables].filter(([, table]) => table.count > 0)
        .map(([name, { when, count, values, tags, groups }]) => ({ name, count, values,
            ...(when ? { when } : {}),
            ...tagsField(tags),
            ...([...groups.keys()].some(Boolean) ? {
                groups: [...groups].map(([name, values]) => ({ name, values: [...values] })),
            } : {}),
        }));
}

/** { tags: { value: [tag] } } for the values that carry any, or nothing. */
function tagsField(tags) {
    const tagged = [...tags].filter(([, list]) => list.length);
    return tagged.length ? { tags: Object.fromEntries(tagged) } : {};
}
```

(The `when` key sits between `values` and `groups` so the existing categories test, which has no gates, still deep-equals.)

3. Replace `jsonTables` with:

```js
function jsonTables(text) {
    const data = JSON.parse(text);
    if (!data || typeof data !== 'object' || Array.isArray(data)) {
        throw new Error('an extra tables file is one JSON object of table name -> list of rows');
    }
    return Object.entries(data).map(([name, spec]) => {
        if (!name.trim()) throw new Error('a table name must be non-blank text');
        const gated = spec && typeof spec === 'object' && !Array.isArray(spec);
        const when = gated ? gates.checkWhen(name, spec.when) : null;
        const rows = gated ? spec.rows : spec;
        if (!Array.isArray(rows) || !rows.length) {
            throw new Error(`table "${name}" must be a non-empty list of rows`);
        }
        const tags = new Map();
        for (const row of rows) {
            if (!row || typeof row !== 'object' || typeof row.value !== 'string' || !row.value.trim()) {
                throw new Error(`every row of "${name}" is {"value": text, "weight": number}`);
            }
            const weight = row.weight === undefined ? 1 : row.weight;
            if (typeof weight !== 'number' || !(weight > 0)) {
                throw new Error(`"${name}" row "${row.value}" has a weight that is not a positive number`);
            }
            const rowTags = row.tags === undefined ? [] : row.tags;
            if (!Array.isArray(rowTags) || rowTags.some(tag => typeof tag !== 'string' || !gates.TAG_RE.test(tag))) {
                throw new Error(`"${name}" row "${row.value}" has tags that are not a list of letters, digits, - and _`);
            }
            const value = row.value.trim();
            tags.set(value, [...new Set([...(tags.get(value) || []), ...rowTags.map(tag => tag.toLowerCase())])]);
        }
        return { name, count: rows.length, values: [...tags.keys()], ...(when ? { when } : {}), ...tagsField(tags) };
    });
}
```

4. In `listSecretTables`, replace the final `return` with:

```js
    const files = names.map((name) => readSecretTablesFile(path.join(dir, name), reserved));
    // Gate order and unknown tags are checked across the whole folder, in
    // listing order - the order the form sends files to the generator.
    const errors = gates.orderErrors(files);
    return { dir, exists: true, files: files.map((file) => errors.has(file.file)
        ? { file: file.file, tables: [], error: errors.get(file.file) } : file) };
```

5. In `validateSelection`, before `return {`, add:

```js
    // The same gate resolution the generator runs, so an impossible
    // selection is refused here with the generator's own words.
    const order = gates.rollOrder([...chosen.keys()].map(file => listing.files.find(entry => entry.file === file)));
    const gatePicks = new Map();
    for (const pick of selected) {
        for (const table of pick.tables) {
            gatePicks.set(gates.entryKey(pick.file, table), Object.hasOwn(pick.values, table) ? pick.values[table] : '');
        }
    }
    const { error: gateError } = gates.resolveGates(order, gatePicks);
    if (gateError) throw new Error(gateError);
```

- [ ] **Step 4: Run the tests**

Run: `node --test test/secretTables.test.js test/api.secretTables.test.js test/secretGates.test.js test/api.secret.test.js test/secretPresets.test.js`
(Skip any of those names that do not exist: `ls test | grep -i secret`.)
Expected: all pass, including the pre-existing ones.

- [ ] **Step 5: Commit**

```bash
git -C "G:/GIT-REPOS/lancer-npc-import-gui/.claude/worktrees/secret-table-gates" add lib/secretTables.js test/secretTables.test.js test/api.secretTables.test.js
git -C "G:/GIT-REPOS/lancer-npc-import-gui/.claude/worktrees/secret-table-gates" commit -m "list and validate secret table gates" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: GUI — gated rows in the Create NPC form

**Files:**
- Modify: `public/index.html` (script tags ~L1076; Secret tables section ~L194-205)
- Modify: `public/secret-mode.js` (`secretTablePicks` L89, `loadSecretTables` L200-290, `applySecretSettings`, `clearPrivateView`, composer `request` ~L673)
- Modify: `public/style.css` (after L450)
- Test: `test/ui.secretTables.test.js`

**Interfaces:**
- Consumes: `root.SecretGates` (Task 4); listing `when`/`tags` (Task 5).
- Produces: `refreshGates()` inside `secret-mode.js`, module-level `gateOrder` and `gateFileErrors`, per-input `gateKey`, `gateClosed`, `gateNote`, `gateRow`; a `renderRollOrder(result)` stub, which Task 7 fills in.

- [ ] **Step 1: Write the failing tests**

Append to `test/ui.secretTables.test.js`:

```js
test('the page loads the gate rules before secret-mode.js and has a gate error line', () => {
    const html = read('index.html');
    const gatesScript = html.indexOf('<script src="/secret-gates.js"></script>');
    assert.notEqual(gatesScript, -1);
    assert.ok(gatesScript < html.indexOf('<script src="/secret-mode.js"></script>'));
    const content = html.slice(html.indexOf('id="secret-tables-content"'), html.indexOf('id="secret-disable-tables"'));
    assert.match(content, /id="secret-tables-gate-error"[^>]*hidden/);
});

test('secret-mode.js greys closed gated tables and leaves them out of the request', () => {
    const js = read('secret-mode.js');
    const picks = js.slice(js.indexOf('function secretTablePicks'), js.indexOf('const transport'));
    assert.match(picks, /box\.gateClosed/);
    const refresh = js.slice(js.indexOf('function refreshGates'), js.indexOf('function renderRollOrder'));
    assert.match(refresh, /SecretGates\.resolveGates\(gateOrder, picks, \{ dropClosed: true \}\)/);
    assert.match(refresh, /secret-table-closed/);
    assert.match(refresh, /secret-tables-gate-error/);
    const load = js.slice(js.indexOf('async function loadSecretTables'), js.indexOf('async function loadSecretPresets'));
    assert.match(load, /SecretGates\.rollOrder\(/);
    assert.match(load, /secret-table-gated/);
    assert.match(load, /refreshGates\(\)/);
    assert.match(js, /SecretGates\.markGatedSources\(/);
});

test('style.css indents gated rows and dims closed ones', () => {
    const css = fs.readFileSync(path.join(__dirname, '..', 'public', 'style.css'), 'utf8');
    assert.match(css, /\.secret-table-gated\s*\{[^}]*--gate-depth/);
    assert.match(css, /\.secret-table-closed\s*\{[^}]*opacity/);
});
```

- [ ] **Step 2: Run to verify they fail**

Run: `node --test test/ui.secretTables.test.js`
Expected: the three new tests fail.

- [ ] **Step 3: Implement**

`public/index.html`:
- Insert `<script src="/secret-gates.js"></script>` on the line before `<script src="/secret-mode.js"></script>`.
- Replace `        <p class="hint" id="secret-tables-status"></p>` with:

```html
        <p class="hint" id="secret-tables-status"></p>
        <p class="settings-error" id="secret-tables-gate-error" role="alert" hidden></p>
```

`public/secret-mode.js`:

1. In `secretTablePicks`, change `if (!box.checked) continue;` to `if (!box.checked || box.gateClosed) continue;`.

2. Directly above `async function loadSecretTables()`, add:

```js
  // Gate state for the Secret tables section (public/secret-gates.js):
  // the roll order of every listed table, recomputed into greyed rows,
  // notes and the roll order panel whenever a box or dropdown changes.
  let gateOrder = [];
  let gateFileErrors = [];
  function refreshGates() {
    const inputs = [...document.querySelectorAll('[data-secret-table]')];
    const picks = new Map(inputs.filter(box => box.checked).map(box => [box.dataset.gateKey, box.valueSelect.value]));
    const result = root.SecretGates.resolveGates(gateOrder, picks, { dropClosed: true });
    for (const box of inputs) {
      const entry = gateOrder.find(item => item.key === box.dataset.gateKey);
      const status = result.status.get(box.dataset.gateKey);
      box.gateClosed = status?.state === 'closed';
      box.gateRow.classList.toggle('secret-table-closed', box.gateClosed);
      box.gateRow.style.setProperty('--gate-depth', String(entry?.depth || 0));
      const text = box.checked && status && (entry?.when || status.limited) ? status.text : '';
      box.gateNote.textContent = text;
      box.gateNote.hidden = !text;
      box.syncControls();
    }
    const error = get('secret-tables-gate-error');
    if (error) { error.textContent = result.error || ''; error.hidden = !result.error; }
    renderRollOrder(result);
  }

  function renderRollOrder() { /* Task 7 */ }
```

3. In `loadSecretTables`, right after `const data = await json('/api/secret/tables');`, add:

```js
    gateOrder = root.SecretGates.rollOrder(data.files || []);
    gateFileErrors = (data.files || []).filter(file => file.error).map(({ file, error }) => ({ file, error }));
```

4. Inside the per-table loop:
   - after `input.dataset.secretTable = table.name; input.dataset.secretFile = file.file;` add
     `input.dataset.gateKey = root.SecretGates.entryKey(file.file, table.name);`
   - replace `label.append(input, \` ${table.name} \`, count); header.append(label);` with:

```js
        label.append(input, ` ${table.name} `, count);
        if (table.when) {
          row.classList.add('secret-table-gated');
          const when = document.createElement('span'); when.className = 'hint secret-table-when';
          when.textContent = ` when: ${table.when.map(tag => `#${tag}`).join(', ')}`;
          label.append(when);
        }
        header.append(label);
        const gateNote = document.createElement('p'); gateNote.className = 'hint secret-table-gate-note'; gateNote.hidden = true;
        input.gateNote = gateNote; input.gateRow = row;
```

   - replace `row.append(header, valueField); box.append(row); inputs.push(input);` with
     `row.append(header, valueField, gateNote); box.append(row); inputs.push(input);`
   - in `input.syncControls`, change `select.disabled = !input.checked;` to
     `select.disabled = !input.checked || Boolean(input.gateClosed);` and change the two target lines to include the same `|| Boolean(input.gateClosed)` in each disabled expression.
   - change `select.addEventListener('change', () => input.syncControls());` to
     `select.addEventListener('change', () => { input.syncControls(); refreshGates(); });`
   - in the `input.addEventListener('change', ...)` body, add `refreshGates();` as the last statement.
   - in the `all.addEventListener('change', ...)` body, add `refreshGates();` as the last statement.

5. In `loadSecretTables`, add `refreshGates();` immediately before `section.hidden = false;`.

6. In `applySecretSettings`, after the loop that restores each input's `checked`/`valueSelect.value` (the `for (const input of inputs) { ... }` block), add `refreshGates();`.

7. In `clearPrivateView`, next to the statement that empties `secret-tables-files`, add
   `gateOrder = []; gateFileErrors = [];`.

8. In the composer setup, change `request: body => post('/api/secret/prompt-preview', body) });` to:

```js
        request: body => post('/api/secret/prompt-preview', body).then(preview =>
          root.SecretGates.markGatedSources(preview, gateOrder.filter(entry => entry.when).map(entry => entry.name))) });
```

`public/style.css` — after the `.secret-table-value select:disabled` rule add:

```css
.secret-tables-file .secret-tables-table.secret-table-gated { --gate-indent: calc(var(--gate-depth, 1) * 1.25rem); margin-left: var(--gate-indent); width: calc(100% - var(--gate-indent)); }
.secret-table-closed { opacity: 0.55; }
.secret-table-when { margin-left: 0.25rem; }
.secret-table-gate-note { margin: 0; }
```

- [ ] **Step 4: Run the tests and a browser check**

Run: `node --test test/ui.secretTables.test.js test/ui.secretMode.test.js test/secretMode.test.js test/secretGates.test.js`
Expected: all pass.

Then use the `run` skill, or start the GUI the way its README says, with a temporary copy of the spec's example saved as a `.md` file in the configured `secretTablesDir`. Log in to Secret mode and check, in a phone-width and a desktop window, that:
- gated rows are indented and show `when: #man`;
- fixing Styles to a #woman value greys Men's Attributes and shows the closed note;
- fixing Men's Attributes while Styles is Random shows `rolls, limited to #man by 'Men's Attributes'` under Styles;
- the prompt composer shows `[Random value from Men's Attributes if opened]`.
Remove the temporary file afterwards.

- [ ] **Step 5: Commit**

```bash
git -C "G:/GIT-REPOS/lancer-npc-import-gui/.claude/worktrees/secret-table-gates" add public/index.html public/secret-mode.js public/style.css test/ui.secretTables.test.js
git -C "G:/GIT-REPOS/lancer-npc-import-gui/.claude/worktrees/secret-table-gates" commit -m "grey out and annotate gated secret tables in Create NPC" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: GUI — the roll order and gates panel

**Files:**
- Modify: `public/index.html` (inside `#secret-tables-content`)
- Modify: `public/secret-mode.js` (`renderRollOrder`, panel open state, `clearPrivateView`)
- Modify: `public/style.css`
- Test: `test/ui.secretTables.test.js`

**Interfaces:**
- Consumes: `SecretGates.rollOrderView` (Task 4); `gateOrder`, `gateFileErrors`, `refreshGates` (Task 6).

- [ ] **Step 1: Write the failing tests**

Append to `test/ui.secretTables.test.js`:

```js
test('the roll order panel is a closed details block at the top of the section', () => {
    const html = read('index.html');
    const content = html.indexOf('id="secret-tables-content"');
    const panel = html.indexOf('id="secret-roll-order"');
    assert.ok(panel > content && panel < html.indexOf('id="secret-tables-files"'));
    const tag = html.slice(html.lastIndexOf('<details', panel), html.indexOf('>', panel) + 1);
    assert.match(tag, /class="secret-roll-order"/);
    assert.doesNotMatch(tag, /\sopen[\s>]/);
    assert.ok(html.includes('id="secret-roll-order-summary"'));
    assert.ok(html.includes('id="secret-roll-order-list"'));
});

test('secret-mode.js renders the panel from the shared view and remembers it per viewer', () => {
    const js = read('secret-mode.js');
    const render = js.slice(js.indexOf('function renderRollOrder'), js.indexOf('function initRollOrderPanel'));
    assert.match(render, /SecretGates\.rollOrderView\(gateOrder, result, gateFileErrors\)/);
    assert.match(render, /secret-roll-order-summary/);
    assert.match(render, /--gate-depth/);
    assert.doesNotMatch(render, /innerHTML/);
    const init = js.slice(js.indexOf('function initRollOrderPanel'), js.indexOf('async function loadSecretTables'));
    assert.match(init, /try \{[^}]*localStorage\.getItem/);
    assert.match(init, /try \{[^}]*localStorage\.setItem/);
    const clear = js.slice(js.indexOf('function clearPrivateView'), js.indexOf('function expire'));
    assert.match(clear, /secret-roll-order-list/);
});
```

- [ ] **Step 2: Run to verify they fail**

Run: `node --test test/ui.secretTables.test.js`
Expected: the two new tests fail.

- [ ] **Step 3: Implement**

`public/index.html` — immediately after `<div id="secret-tables-content">` add:

```html
        <details class="secret-roll-order" id="secret-roll-order">
          <summary id="secret-roll-order-summary">Roll order and gates</summary>
          <p class="hint">Tables roll top to bottom. A gated table rolls only when a value above it carries one of its tags.</p>
          <ol class="secret-roll-order-list" id="secret-roll-order-list"></ol>
        </details>
```

`public/secret-mode.js` — replace the Task 6 stub `function renderRollOrder() { /* Task 7 */ }` with:

```js
  function renderRollOrder(result) {
    const list = get('secret-roll-order-list');
    if (!list) return;
    const view = root.SecretGates.rollOrderView(gateOrder, result, gateFileErrors);
    get('secret-roll-order-summary').textContent = view.summary;
    list.replaceChildren(...view.items.map(item => {
      const li = document.createElement('li'); li.className = 'secret-roll-order-item';
      li.style.setProperty('--gate-depth', String(item.depth));
      const title = document.createElement('strong'); title.textContent = item.title;
      const file = document.createElement('span'); file.className = 'hint'; file.textContent = ` ${item.file}`;
      li.append(title, file);
      for (const [className, text] of [['secret-roll-order-gate', item.gate], ['secret-roll-order-opens', item.opens], ['secret-roll-order-status', item.status]]) {
        if (!text) continue;
        const line = document.createElement('div'); line.className = className; line.textContent = text;
        li.append(line);
      }
      return li;
    }));
  }

  // Whether the panel is open is a per-viewer convenience only.
  const ROLL_ORDER_OPEN_KEY = 'secretRollOrderOpen';
  function initRollOrderPanel() {
    const panel = get('secret-roll-order');
    if (!panel || panel.dataset.ready) return;
    panel.dataset.ready = '1';
    try { panel.open = root.localStorage.getItem(ROLL_ORDER_OPEN_KEY) === '1'; } catch { panel.open = false; }
    panel.addEventListener('toggle', () => {
      try { root.localStorage.setItem(ROLL_ORDER_OPEN_KEY, panel.open ? '1' : '0'); } catch { /* storage unavailable */ }
    });
  }
```

In `loadSecretTables`, call `initRollOrderPanel();` right after the `gateFileErrors = ...` line from Task 6.

In `clearPrivateView`, next to the Task 6 `gateOrder = [];` line, add:

```js
    get('secret-roll-order-list')?.replaceChildren();
    if (get('secret-roll-order-summary')) get('secret-roll-order-summary').textContent = 'Roll order and gates';
```

`public/style.css` — append after the Task 6 rules:

```css
.secret-roll-order { margin: 0.5rem 0; border: 1px solid var(--line); border-radius: var(--r-md); padding: 0.5rem 0.75rem; background: var(--surface); }
.secret-roll-order summary { cursor: pointer; font-weight: 600; }
.secret-roll-order-list { margin: 0.5rem 0 0; padding-left: 1.5rem; }
.secret-roll-order-item { margin: 0.35rem 0 0.35rem calc(var(--gate-depth, 0) * 1.25rem); overflow-wrap: anywhere; }
.secret-roll-order-item > div { color: var(--text-3); font-size: 0.85rem; }
.secret-roll-order-status { color: var(--text-2); }
```

- [ ] **Step 4: Run the tests and a browser check**

Run: `node --test test/ui.secretTables.test.js`
Expected: all pass.

Browser check, with the same temporary file as Task 6:
- the panel starts closed and its summary reads `Roll order and gates (4 tables, 3 gated)` or similar;
- opened, it lists tables in order, with Scars indented twice;
- its status lines change as boxes and dropdowns change;
- it stays open after a reload;
- nothing overflows at phone width.

- [ ] **Step 5: Commit**

```bash
git -C "G:/GIT-REPOS/lancer-npc-import-gui/.claude/worktrees/secret-table-gates" add public/index.html public/secret-mode.js public/style.css test/ui.secretTables.test.js
git -C "G:/GIT-REPOS/lancer-npc-import-gui/.claude/worktrees/secret-table-gates" commit -m "show the secret table roll order and gates in Create NPC" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: GUI — docs and full verification

**Files:**
- Modify: `docs/secret-mode.md` (section "Secret tables and disabled default tables", ~L97-151)
- Modify: `README.md` (Secret tables notes, ~L115-119 and ~L768)

- [ ] **Step 1: Document**

In `docs/secret-mode.md`, after the markdown/JSON shape description, add a `### Tags and gates` subsection containing the same example and bullets as the generator README (Task 3), followed by:

```markdown
In Create NPC:

- Gated tables are indented under the file's tables and labelled `when: #man`.
- A gated table nothing selected can open (its opener is unticked, or fixed to
  a value without its tags) is greyed out and left out of the run.
- With its opener on Random, a gated table notes `rolls only if Styles rolls #man`.
  Fixing a value in it limits that opener to matching values.
- Selections that cannot happen, such as two fixed gated tables that need
  different values of the same opener, are refused with the generator's own
  message.
- **Roll order and gates**, a closed panel at the top of the section, lists
  every table in roll order with its gate, what its tags open, and its live
  status.
- The folder is checked as a whole: a gated table above its opener, or a tag
  that no table in the folder carries, marks that file with the error.
```

In `README.md`, extend the Secret tables line(s) with one sentence: "Private tables can be gated with `#tag`s on bullets and `(when: tag)` on headings; see docs/secret-mode.md."

- [ ] **Step 2: Run the full GUI suite**

Run: `node --test --test-concurrency=4 --test-timeout=120000 "test/*.test.js"`
Expected: all pass. Re-run any port-collision flakes (see Global Constraints) alone and record the result.

- [ ] **Step 3: Run the full generator suite once more**

Run in the generator worktree: `python -m unittest discover test`
Expected: no failures beyond the known pre-existing ones; confirm any that appear also fail on `main`.

- [ ] **Step 4: Commit**

```bash
git -C "G:/GIT-REPOS/lancer-npc-import-gui/.claude/worktrees/secret-table-gates" add docs/secret-mode.md README.md
git -C "G:/GIT-REPOS/lancer-npc-import-gui/.claude/worktrees/secret-table-gates" commit -m "document secret table tags and gates" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

- [ ] **Step 5: Hand-off**

Per the user's standing preference, when both branches are green:
1. Exit the worktree with `keep`.
2. In each repo, fast-forward `main` to `secret-table-gates`, remove the worktree and delete the branch.
3. Do not push.
4. If a main checkout has overlapping uncommitted edits, follow the patch-check procedure in memory, or leave the branch in place and report the merge commands.
