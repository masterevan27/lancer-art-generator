"""Optional portrait/token canvas overrides shared by both generators."""


def add_arguments(parser):
    parser.add_argument('--width', type=int, help='image width in pixels; requires --height (64-8192, multiples of 8)')
    parser.add_argument('--height', type=int, help='image height in pixels; requires --width (64-8192, multiples of 8)')
    parser.add_argument('--token-width', type=int, help='override token width; requires --token-height (64-8192, multiples of 8)')
    parser.add_argument('--token-height', type=int, help='override token height; requires --token-width (64-8192, multiples of 8)')


def validate(args):
    for prefix in ('', 'token_'):
        values = tuple(getattr(args, prefix + key, None) for key in ('width', 'height'))
        if values == (None, None):
            continue
        if any(type(value) is not int or not 64 <= value <= 8192 or value % 8 for value in values):
            raise ValueError(('Token width' if prefix else 'Width') + ' and height must both be whole pixels from 64 to 8192, in multiples of 8.')


def size(args, default, token=False):
    validate(args)
    if token and getattr(args, 'token_width', None) is not None:
        return args.token_width, args.token_height
    return (args.width, args.height) if getattr(args, 'width', None) is not None else default


def metadata(args):
    dimensions = size(args, None)
    result = {'imageDimensions': dict(zip(('width', 'height'), dimensions))} if dimensions else {}
    if getattr(args, 'token_width', None) is not None:
        result['tokenImageDimensions'] = {'width': args.token_width, 'height': args.token_height}
    return result


def restore(args, entry):
    for prefix, key in (('', 'imageDimensions'), ('token_', 'tokenImageDimensions')):
        if all(getattr(args, prefix + axis, None) is None for axis in ('width', 'height')):
            saved = entry.get(key, {})
            for axis in ('width', 'height'):
                setattr(args, prefix + axis, saved.get(axis))
    validate(args)


def require_slots(args, slots):
    if any(getattr(args, key, None) is not None for key in ('width', 'token_width')) and not slots.latent:
        raise ValueError('This workflow has no editable latent image size; choose another workflow for custom dimensions.')
