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


_HEADING = re.compile(r"^(#{1,3})(?:\s+(.*?))?\s*$")


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
            name = heading.group(2) or ""
            if not name:
                raise _error(path, None, number, "a template needs a name after '## '")
            if any(t["name"] == name for t in templates):
                raise _error(path, name, number, "template name already used in this file")
            current = {"name": name, "file": path.name, "line": number, "weight": 1.0, "pin_text": {},
                       "portrait": None, "token": None, "_lines": {"portrait": [], "token": []},
                       "_weight_line": None, "_section_lines": {}}
            section = None
            continue
        if heading and heading.group(1) == "###":
            if current is None:
                raise _error(path, None, number, "'### %s' before any '## Name'" % (heading.group(2) or ""))
            target = (heading.group(2) or "").strip().lower()
            if target not in ("portrait", "token"):
                raise _error(path, current["name"], number,
                             "unknown section '### %s'; only portrait and token" % (heading.group(2) or ""))
            if current[target] is not None:
                raise _error(path, current["name"], number, "a second '### %s' section" % target)
            current[target] = current["_lines"][target]
            current["_section_lines"][target] = number
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
                raise _error(path, template["name"], template["_section_lines"][target], "the %s section is empty" % target)
        del template["_weight_line"]
        del template["_section_lines"]
    if not templates:
        raise _error(path, None, max(1, len(lines)), "no templates ('## Name') in this file")
    return tables or [], tables_line, templates


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
