"""Validated art styles and the shared private-output contract for every CLI."""
import json
import os
import re
import uuid
from pathlib import Path
from types import MappingProxyType

DEFAULT_CATALOG = Path(__file__).resolve().parent / 'art-styles.json'
DEFAULT_STYLE = MappingProxyType({'id': 'default', 'name': 'Default', 'prompt': '', 'hidden': False})
EMPTY_STYLE = MappingProxyType({'id': 'none', 'name': 'None (no art style)', 'prompt': '', 'hidden': False})


def load_catalog(path=DEFAULT_CATALOG):
    path = Path(path)
    text = path.read_text(encoding='utf-8-sig') if path.exists() else ''
    data = json.loads(text) if text.strip() else {'styles': []}
    if not isinstance(data, dict) or not isinstance(data.get('styles'), list):
        raise ValueError('Art style catalog must contain a styles array')
    result = [dict(DEFAULT_STYLE), dict(EMPTY_STYLE)]
    seen = {'default', 'none'}
    for item in data['styles']:
        if not isinstance(item, dict):
            raise ValueError('Each art style must be an object')
        sid = item.get('id')
        if not isinstance(sid, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*', sid):
            raise ValueError('Art style id must contain only letters, digits, underscores and hyphens')
        if sid in seen:
            raise ValueError('Duplicate or reserved art style id: ' + sid)
        if not isinstance(item.get('name'), str) or not item['name'].strip():
            raise ValueError('Art style %s requires a nonblank name' % sid)
        if not isinstance(item.get('prompt'), str):
            raise ValueError('Art style %s requires a string prompt (may be empty)' % sid)
        for field in ('hidden', 'secret'):
            if field in item and not isinstance(item[field], bool):
                raise ValueError('Art style %s %s must be boolean' % (sid, field))
        result.append(dict(id=sid, name=item['name'].strip(), prompt=item['prompt'].strip(),
                           hidden=item.get('hidden', False) or item.get('secret', False)))
        seen.add(sid)
    return result


def select_style(path=DEFAULT_CATALOG, style_id=None, secret=False):
    for style in load_catalog(path):
        if style['id'] == (style_id or 'default'):
            if style['hidden'] and not secret:
                raise ValueError('Hidden art styles require --secret')
            return style
    raise ValueError('Unknown art style: %s' % style_id)


def add_arguments(parser):
    parser.add_argument('--art-style', metavar='ID', help='rendering style (default: default; none: no art style)')
    parser.add_argument('--art-styles', type=Path, default=DEFAULT_CATALOG, metavar='PATH')
    parser.add_argument('--secret', action='store_true', help='keep every output in private storage')
    parser.add_argument('--secret-config', type=Path, metavar='PATH', help='JSON configuration containing secretImagesDir')


def contained(path, root):
    path, root = Path(path).expanduser().resolve(), Path(root).expanduser().resolve()
    if not path.is_relative_to(root):
        raise ValueError('Private output path must stay inside secretImagesDir: %s' % path)
    return path


def configure(args, category, output_attr='out'):
    args.selected_style = select_style(args.art_styles, args.art_style, args.secret)
    if not args.secret:
        return args
    if not args.secret_config:
        raise ValueError('--secret requires --secret-config with secretImagesDir')
    config_path = Path(args.secret_config).resolve()
    config = json.loads(config_path.read_text(encoding='utf-8-sig'))
    root = config.get('secretImagesDir')
    if not isinstance(root, str) or not root.strip():
        raise ValueError('Secret configuration requires secretImagesDir')
    root = Path(root).expanduser()
    args.secret_root = (root if root.is_absolute() else config_path.parent / root).resolve()
    args.private_prefix = 'secret/' + uuid.uuid4().hex
    output = getattr(args, output_attr, None)
    setattr(args, output_attr, contained(output or args.secret_root / category, args.secret_root))
    if hasattr(args, 'manifest'):
        args.manifest = contained(args.secret_root / 'manifest.json', args.secret_root)
    if getattr(args, 'regen_manifest', None):
        args.regen_manifest = contained(args.regen_manifest, args.secret_root)
    if getattr(args, 'dump_job', None):
        args.dump_job = contained(args.dump_job, args.secret_root)
    return args


def metadata(args):
    style = getattr(args, 'selected_style', DEFAULT_STYLE)
    return {'art_style': {key: style[key] for key in ('id', 'name')},
            'secret': bool(getattr(args, 'secret', False))}


def restore_record(args, entry, folder=None, manifest=None):
    """Fail closed before touching a stored private record or its files."""
    if entry.get('secret') and not getattr(args, 'secret', False):
        raise ValueError('Private records require --secret and --secret-config')
    if getattr(args, 'secret', False):
        for path in (folder, manifest):
            if path is not None:
                contained(path, args.secret_root)
        for filename in entry.get('files', []):
            if folder is not None:
                contained(Path(folder) / filename, args.secret_root)
        for field in ('portrait', 'token'):
            if folder is not None and entry.get(field):
                contained(Path(folder) / entry[field], args.secret_root)
    if not getattr(args, 'art_style', None):
        style_id = entry.get('art_style', {}).get('id', 'default')
        args.selected_style = select_style(getattr(args, 'art_styles', DEFAULT_CATALOG), style_id,
                                           getattr(args, 'secret', False))


def apply_style(prompt, style=None):
    """Replace the house rendering clauses, retaining subject and composition."""
    if not style or style['id'] == 'default':
        return prompt
    # A preview may already contain its selected style. Reapplying at render
    # time replaces that generated suffix instead of stacking style directives.
    prompt = prompt.split('\nArt style: ', 1)[0]
    prompt = re.sub(r'\s+', ' ', prompt)
    prompt = prompt.replace('Keep the reference colors, materials, planting areas and illustration style.',
                            'Keep the reference colors, materials and planting areas.')
    prompt = re.sub(r'rendered in a detailed painterly illustration style with fine grain texture, '
                    r'clean linework and halftone dot shading worked into the shadows, moody cinematic lighting'
                    r'(?: on the (?:figure|hull))?', 'rendered using the selected art style', prompt)
    prompt = re.sub(r',? painterly brushwork with heavy grain and dense halftone screentone worked into every shadow', '', prompt)
    prompt = re.sub(r'rendered in a detailed painterly illustration style matching worn military hardware:',
                    'with worn military hardware:', prompt, flags=re.I)
    prompt = re.sub(r', fine grain texture, halftone dot shading in the shadows', '', prompt)
    prompt = re.sub(r'rendered in flat\s+cel-shaded style with bold black linework and halftone screentone dot\s+'
                    r'shading(?: in the\s+shadows)?, high contrast', 'rendered using the selected art style', prompt, flags=re.I)
    prompt = re.sub(r', halftone shading, high\s+contrast', '', prompt)
    # Legacy scene and battlemap catalogues have their own complete style
    # sentence; their subject and camera instructions live outside it.
    prompt = re.sub(r'rendered in a detailed painterly illustration style[^.!?]*\.',
                    '', prompt, flags=re.I)
    prompt = re.sub(r'Not an illustration,\s*no linework,\s*no halftone,\s*'
                    r'no cel shading,\s*no painterly brushwork\.', '', prompt, flags=re.I)
    prompt = re.sub(r'Photorealistic,\s*', '', prompt, flags=re.I)
    prompt = re.sub(r'\bphotograph\b', 'image', prompt, flags=re.I)
    style_prompt = style['prompt'].strip()
    if not style_prompt:
        prompt = re.sub(r',?\s*rendered using the selected art style', '', prompt)
        return prompt.strip()
    return prompt + '\nArt style: ' + style_prompt


def private_prefix(args, prefix):
    if not getattr(args, 'secret', False):
        return prefix
    # Discard caller supplied path components so --set/prefix cannot escape.
    base = getattr(args, 'private_prefix', 'secret')
    return base + '/' + re.sub(r'[^a-zA-Z0-9_-]', '_', str(prefix))[-160:]


def protect_graph(graph, args):
    if getattr(args, 'secret', False):
        for node_id, node in graph.items():
            inputs = node.get('inputs', {})
            if 'filename_prefix' in inputs:
                inputs['filename_prefix'] = private_prefix(args, inputs['filename_prefix'])
            if node.get('class_type', '').startswith('Preview'):
                raise ValueError('Private workflows must not contain preview output nodes: ' + node_id)
    return graph


def check_source(args, image):
    """Recognize private generated sources before standalone derived jobs."""
    image = Path(image).resolve()
    records = []
    for sidecar in (image.with_suffix('.background.json'), image.with_suffix('.art.json')):
        if sidecar.exists():
            records.append(json.loads(sidecar.read_text(encoding='utf-8-sig')))
    for parent in image.parents:
        marker = parent / '.art.json'
        if marker.is_file():
            records.append(json.loads(marker.read_text(encoding='utf-8-sig')))
        manifest = parent / 'manifest.json'
        if manifest.is_file():
            data = json.loads(manifest.read_text(encoding='utf-8-sig'))
            if isinstance(data, dict):
                for folder, entry in data.items():
                    if isinstance(entry, dict) and image.is_relative_to(Path(folder).resolve()):
                        records.append(entry)
    for record in records:
        restore_record(args, record, image.parent if record.get('secret') else None)
    return records[-1] if records else {}


def write_metadata(path, args):
    path = Path(path)
    if getattr(args, 'secret', False):
        contained(path, args.secret_root)
    path.write_text(json.dumps(metadata(args), indent=2) + '\n', encoding='utf-8')


def safe_output_directory(args, directory):
    """Check existing targets before tools that choose their own filenames run."""
    directory = Path(directory)
    if getattr(args, 'secret', False):
        contained(directory, args.secret_root)
        for folder, directories, files in os.walk(directory, followlinks=False):
            for name in directories + files:
                contained(Path(folder) / name, args.secret_root)
    return directory
