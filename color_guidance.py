"""Selectable colour guidance for NPC prompts.

The house palette sentence - "Keep the palette restrained - greys, olive drab
and rust ..." - is what every NPC portrait and token used to close on. A
colour guidance catalog (color-guidance.json beside the scripts, same shape as
art-styles.json but under a "guidance" key) offers alternatives: each entry's
prompt is a complete palette sentence that replaces the house one. The rolled
glow is light rather than pigment, so it keeps its own sentence either way -
see build_prompts() in generate-npc.py.

The built-in 'default' entry means "the house line, exactly as before", and
the built-in 'none' entry means "no palette sentence at all" - the prompt says
nothing about colour beyond the glow's own line. Both survive a missing, blank
or empty catalog the way the default and none art styles do.
Deliberately its own loader rather than a call into art_styles.load_catalog:
the two catalogs share a shape today, but the art style one carries the
private-output contract and is free to grow reserved entries of its own.
"""
import json
import re
from pathlib import Path
from types import MappingProxyType

DEFAULT_CATALOG = Path(__file__).resolve().parent / 'color-guidance.json'
DEFAULT_GUIDANCE = MappingProxyType({'id': 'default', 'name': 'Default', 'prompt': '', 'hidden': False})
EMPTY_GUIDANCE = MappingProxyType({'id': 'none', 'name': 'None (no colour guidance)', 'prompt': '', 'hidden': False})


def load_catalog(path=DEFAULT_CATALOG):
    path = Path(path)
    text = path.read_text(encoding='utf-8-sig') if path.exists() else ''
    data = json.loads(text) if text.strip() else {'guidance': []}
    if not isinstance(data, dict) or not isinstance(data.get('guidance'), list):
        raise ValueError('Colour guidance catalog must contain a guidance array')
    result = [dict(DEFAULT_GUIDANCE), dict(EMPTY_GUIDANCE)]
    seen = {'default', 'none'}
    for item in data['guidance']:
        if not isinstance(item, dict):
            raise ValueError('Each colour guidance entry must be an object')
        gid = item.get('id')
        if not isinstance(gid, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*', gid):
            raise ValueError('Colour guidance id must contain only letters, digits, underscores and hyphens')
        if gid in seen:
            raise ValueError('Duplicate or reserved colour guidance id: ' + gid)
        for field in ('name', 'prompt'):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError('Colour guidance %s requires a nonblank %s' % (gid, field))
        for field in ('hidden', 'secret'):
            if field in item and not isinstance(item[field], bool):
                raise ValueError('Colour guidance %s %s must be boolean' % (gid, field))
        result.append(dict(id=gid, name=item['name'].strip(), prompt=item['prompt'].strip(),
                           hidden=item.get('hidden', False) or item.get('secret', False)))
        seen.add(gid)
    return result


def select_guidance(path=DEFAULT_CATALOG, guidance_id=None, secret=False):
    for guidance in load_catalog(path):
        if guidance['id'] == (guidance_id or 'default'):
            if guidance['hidden'] and not secret:
                raise ValueError('Hidden colour guidance requires --secret')
            return guidance
    raise ValueError('Unknown colour guidance: %s' % guidance_id)


def add_arguments(parser):
    parser.add_argument('--color-guidance', metavar='ID',
                        help='palette sentence for the prompts (default: the house palette; none: no palette sentence)')
    parser.add_argument('--color-guidance-catalog', type=Path, default=DEFAULT_CATALOG, metavar='PATH')


def configure(args):
    args.selected_guidance = select_guidance(args.color_guidance_catalog, args.color_guidance,
                                             getattr(args, 'secret', False))
    return args


def metadata(args):
    guidance = getattr(args, 'selected_guidance', DEFAULT_GUIDANCE)
    return {'color_guidance': {key: guidance[key] for key in ('id', 'name')}}


def restore_record(args, entry):
    """Regeneration keeps the stored guidance unless the flag names another."""
    if not getattr(args, 'color_guidance', None):
        guidance_id = entry.get('color_guidance', {}).get('id', 'default')
        args.selected_guidance = select_guidance(getattr(args, 'color_guidance_catalog', DEFAULT_CATALOG),
                                                 guidance_id, getattr(args, 'secret', False))


def is_custom(guidance):
    """True when the guidance replaces the house palette line - a catalog
    entry's own sentence, or 'none', whose empty prompt drops the line."""
    return bool(guidance) and guidance['id'] != 'default'
