"""Stable, source-labeled fragments shared by preview and image generation."""
import re
import json
from difflib import SequenceMatcher
from string import Formatter

import art_styles

TARGETS = ('portrait', 'token')
MAX_PARTS = 256


def validate_layout(value):
    if value is None:
        return {}
    if not isinstance(value, dict) or any(k not in TARGETS for k in value):
        raise ValueError('promptLayout must contain only portrait and token lists')
    result = {}
    for target, entries in value.items():
        if not isinstance(entries, list) or len(entries) > MAX_PARTS:
            raise ValueError('promptLayout lists must have at most 256 snippets')
        seen = set()
        result[target] = []
        for entry in entries:
            key = entry if isinstance(entry, str) else entry.get('id') if isinstance(entry, dict) else None
            if not isinstance(key, str) or not key or len(key) > 240 or key in seen:
                raise ValueError('promptLayout snippet IDs must be unique, non-empty strings of at most 240 characters')
            seen.add(key)
            if isinstance(entry, dict):
                if set(entry) != {'id', 'text'} or not key.startswith('custom:') or not isinstance(entry['text'], str) or len(entry['text']) > 4000:
                    raise ValueError('custom snippets need a custom: ID and text of at most 4000 characters')
                result[target].append(dict(entry))
            else:
                result[target].append(entry)
    if len(json.dumps(result, ensure_ascii=False, separators=(',', ':')).encode('utf-16-le')) // 2 > 24000:
        raise ValueError('promptLayout is too large (24,000 characters maximum)')
    return result


def order_parts(parts, layout):
    """Keep inactive IDs in the saved layout; newly active parts are appended."""
    available = {part['id']: part for part in parts}
    ordered = []
    for entry in layout or []:
        if isinstance(entry, dict):
            ordered.append({'id': entry['id'], 'text': entry['text'], 'value': entry['text'],
                            'prefix': '', 'suffix': '', 'sources': [], 'custom': True})
        elif entry in available:
            ordered.append(available.pop(entry))
    ordered.extend(available.values())
    return ordered


def render(parts, customized=False):
    if not customized:
        return ''.join(part['text'] for part in parts)
    # Every moved snippet remains separated, even when it originally ended
    # immediately before punctuation. Custom text is literal, never formatted.
    text = ''
    for part in parts:
        value = part['text']
        if not value:
            continue
        if text and not text[-1].isspace() and not value[0].isspace() and value[0] not in ',.;:!?':
            text += ' '
        text += value
    return text.strip()


def _restyle(parts, style):
    """Apply the existing whole-prompt style rules, preserving span ownership.

    A style can change words inside a table value as well as template prose.
    Map those edits back to the fragments instead of shielding values behind
    placeholders, which would make preview and generation disagree.
    """
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
    owners = []
    buffers = [{key: [] for key in ('prefix', 'value', 'suffix')} for _ in parts]
    for index, part in enumerate(parts):
        for key in ('prefix', 'value', 'suffix'):
            owners.extend([(index, key)] * len(part[key]))
    for operation, left, right, start, end in SequenceMatcher(None, original, styled, autojunk=False).get_opcodes():
        if operation == 'equal':
            for offset, char in enumerate(styled[start:end]):
                index, key = owners[left + offset]
                buffers[index][key].append(char)
        elif operation in ('replace', 'insert') and owners:
            index, key = owners[min(left, len(owners) - 1)]
            buffers[index][key].append(styled[start:end])
    result = []
    for part, buffer in zip(parts, buffers):
        value = {key: ''.join(chars) for key, chars in buffer.items()}
        updated = dict(part, **value)
        updated['text'] = value['prefix'] + value['value'] + value['suffix']
        if updated['text']:
            if not updated['value']:
                updated['sources'] = []
            result.append(updated)
    if tail:
        result.append(_part('style:suffix', tail))
    return result


def _part(key, value, sources=(), prefix='', suffix=''):
    return {'id': key, 'text': prefix + value + suffix, 'value': value,
            'prefix': prefix, 'suffix': suffix, 'sources': list(sources)}


def split_field(key, text, candidates, sources=()):
    """Attach connecting prose to values within a single template field.

    Matching is scoped to that field, so a trait cannot label unrelated prose
    elsewhere in the prompt. Longest values win where phrases overlap.
    """
    candidates = [c for c in candidates if c[1]]
    if not candidates:
        return [_part(key, text, sources)] if text else []
    pattern = re.compile('|'.join(re.escape(c[1]) for c in sorted(candidates, key=lambda c: -len(c[1]))))
    parts, counts, offset = [], {}, 0
    for match in pattern.finditer(text):
        name, value, tables = next(c for c in candidates if c[1] == match.group())
        counts[name] = counts.get(name, 0) + 1
        ident = f'{key}:{name}' + (f':{counts[name]}' if counts[name] > 1 else '')
        parts.append(_part(ident, value, tables, text[offset:match.start()]))
        offset = match.end()
    if not parts:
        return [_part(key, text, sources)] if text else []
    parts[-1]['suffix'] = text[offset:]
    parts[-1]['text'] += text[offset:]
    return parts


def assemble(template, fields, npc, target, style):
    disabled = set(npc.get('_disabled') or ())
    def candidate(field, *sources):
        active = [s for s in sources if s not in disabled]
        return (field, fields.get(field, '') if active else '', active)
    details = {
        'identity': [candidate('role', 'Role'), candidate('maturity', 'Age'),
                     candidate('gender', 'Pronouns'), candidate('age', 'Age')],
        'figure_line': [candidate('height', 'Height'), candidate('build', 'Build'),
                        candidate('face', 'Age'), candidate('traits', 'Pronouns'),
                        candidate('skin', 'Skin'), candidate('hair', 'Hair', 'Hair colour'),
                        candidate('eyes', 'Eyes'), candidate('feature', 'Feature'),
                        candidate('outfit', 'Outfit'), candidate('faction_line', 'Faction')],
        'gear_line': [candidate('weapon', 'Weapon'), candidate('gear', 'Gear')],
        'glow_line': [candidate('glow', 'Glow colour'), candidate('placement', 'Glow placement')],
    }
    sources = {'shot': ['Backdrop'], 'backdrop_line': ['Backdrop'], 'weather_line': ['Weather'],
               'stance_line': ['Stance'], 'headgear_line': ['Headgear'], 'demeanor_line': ['Demeanor']}
    fragments, pending = [], ''
    for literal, field, _, _ in Formatter().parse(template):
        pending += literal
        if not field:
            continue
        if field in details or field in sources or field == 'extra_line':
            if pending:
                # Template boundaries do not change when nested traits vanish.
                fragments.append(_part('text:before:' + field, pending))
                pending = ''
        if field == 'extra_line':
            values = [(name, value.strip().rstrip('.').strip()) for name, value in (npc.get('_extra') or {}).items()
                      if (npc.get('_extra_targets') or {}).get(name, 'both') in ('both', target)]
            values = [(name, value) for name, value in values if value]
            for index, (name, value) in enumerate(values):
                if index == 0:
                    value = value[0].upper() + value[1:]
                fragments.append(_part('extra:' + name, value, [name], ', ' if index else '',
                                       '. ' if index == len(values) - 1 else ''))
        elif field in details or field in sources:
            for part in split_field(field, str(fields[field]), details.get(field, []),
                                    [source for source in sources.get(field, []) if source not in disabled]):
                fragments.append(part)
        else:
            # Pronouns in fixed framing prose are wording, not separate pills.
            pending += str(fields[field])
    if pending:
        fragments.append(_part('text:tail', pending))
    return _restyle(fragments, style)
