"""Optional portrait/token canvas overrides shared by both generators."""


def add_arguments(parser):
    parser.add_argument('--width', type=int, help='image width in pixels; requires --height (64-8192, multiples of 8)')
    parser.add_argument('--height', type=int, help='image height in pixels; requires --width (64-8192, multiples of 8)')


def validate(args):
    values = (getattr(args, 'width', None), getattr(args, 'height', None))
    if values == (None, None):
        return
    if any(type(value) is not int or not 64 <= value <= 8192 or value % 8 for value in values):
        raise ValueError('Width and height must both be whole pixels from 64 to 8192, in multiples of 8.')


def size(args, default):
    validate(args)
    return (args.width, args.height) if getattr(args, 'width', None) is not None else default


def metadata(args):
    dimensions = size(args, None)
    return {'imageDimensions': dict(zip(('width', 'height'), dimensions))} if dimensions else {}


def restore(args, entry):
    if getattr(args, 'width', None) is None and getattr(args, 'height', None) is None:
        saved = entry.get('imageDimensions', {})
        args.width, args.height = saved.get('width'), saved.get('height')
    validate(args)


def require_slots(args, slots):
    if getattr(args, 'width', None) is not None and not slots.latent:
        raise ValueError('This workflow has no editable latent image size; choose another workflow for custom dimensions.')
