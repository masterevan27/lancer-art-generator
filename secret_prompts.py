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
