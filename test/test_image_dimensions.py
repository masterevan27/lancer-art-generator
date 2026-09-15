import argparse
import importlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from test.helpers import load_generator, load_ship_generator


class ImageDimensionsTests(unittest.TestCase):
    def test_creation_and_regeneration_keep_custom_canvas_for_both_generators(self):
        for generator in (load_generator(), load_ship_generator()):
            with self.subTest(generator=generator.__name__), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                config = root / 'config.json'
                config.write_text(json.dumps({'secretImagesDir': str(root / 'private')}))
                graphs = []

                class Comfy:
                    base = 'fixture'
                    def queue(self, graph):
                        graphs.append(graph)
                        return 'test'
                    def wait(self, *args, **kwargs):
                        return {}
                    def images(self, record):
                        return [{'filename': 'test.png', 'subfolder': 'secret/test', 'type': 'output'}]

                flags = ['--secret', '--secret-config', str(config), '--pause', '0']
                with mock.patch.object(generator.art, 'find_server', return_value=Comfy()), \
                        mock.patch.object(generator, 'fetch', side_effect=lambda comfy, image, target: (target.write_bytes(b'png'), target)[1]), \
                        redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    self.assertEqual(generator.main(flags + ['--width', '1920', '--height', '1080', '--seed', '5']), 0)
                    manifest_path = root / 'private' / 'manifest.json'
                    entry = next(iter(json.loads(manifest_path.read_text()).values()))
                    self.assertEqual(entry['imageDimensions'], {'width': 1920, 'height': 1080})
                    if entry['kind'] == 'spaceship':
                        self.assertEqual((entry['tokenWidth'], entry['tokenHeight']), (1920, 1080))
                    self.assertEqual(generator.main(flags + ['--regen-manifest', str(manifest_path), '--regen-id', entry['id']]), 0)
                    regenerated = next(iter(json.loads(manifest_path.read_text()).values()))
                    if regenerated['kind'] == 'spaceship':
                        self.assertEqual((regenerated['tokenWidth'], regenerated['tokenHeight']), (1920, 1080))
                renders = [graph for graph in graphs if any(node['class_type'].startswith('EmptyLatent') for node in graph.values())]
                self.assertEqual(len(renders), 4, 'creation and regeneration each render a portrait and token')
                for graph in renders:
                    latent = graph[generator.art.locate_slots(graph).latent]['inputs']
                    self.assertEqual((latent['width'], latent['height']), (1920, 1080))

    def test_both_generators_accept_dimensions_and_pass_them_to_workflow(self):
        for generator in (load_generator(), load_ship_generator()):
            with self.subTest(generator=generator.__name__):
                args = generator.parse_args(['--width', '1920', '--height', '1080', '--dry-run'])
                knobs = generator.Knobs(args, (1024, 1024), 'test')
                template = {
                    '1': {'class_type': 'CLIPTextEncode', 'inputs': {'text': ''}},
                    '2': {'class_type': 'EmptyLatentImage', 'inputs': {'width': 1024, 'height': 1024, 'batch_size': 1}},
                    '3': {'class_type': 'KSampler', 'inputs': {'seed': 1, 'positive': ['1', 0], 'latent_image': ['2', 0]}},
                    '4': {'class_type': 'SaveImage', 'inputs': {'filename_prefix': 'test', 'images': ['5', 0]}},
                    '5': {'class_type': 'VAEDecode', 'inputs': {'samples': ['3', 0]}},
                }
                slots = generator.art.locate_slots(template)
                job = generator.art.build_job(template, slots, generator.art.Entry(name='test', label='test', path=[], prompt='test', line=0), 1, knobs)
                self.assertEqual(job['2']['inputs']['width'], 1920)
                self.assertEqual(job['2']['inputs']['height'], 1080)

    def test_invalid_and_incomplete_dimensions_are_rejected(self):
        for generator in (load_generator(), load_ship_generator()):
            for flags in (['--width', '1920'], ['--height', '1080'], ['--width', '0', '--height', '1080'],
                          ['--width', '9000', '--height', '1080'], ['--width', '1919', '--height', '1080']):
                with self.subTest(flags=flags), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    generator.parse_args(flags)

    def test_defaults_and_saved_dimensions(self):
        dimensions = importlib.import_module('image_dimensions')
        args = argparse.Namespace(width=None, height=None)
        self.assertEqual(dimensions.size(args, (1024, 1280)), (1024, 1280))
        self.assertEqual(dimensions.metadata(args), {})
        dimensions.restore(args, {'imageDimensions': {'width': 1920, 'height': 1080}})
        self.assertEqual(dimensions.size(args, (1024, 1280)), (1920, 1080))
        self.assertEqual(dimensions.metadata(args), {'imageDimensions': {'width': 1920, 'height': 1080}})
        args.width, args.height = 1080, 1920
        dimensions.restore(args, {'imageDimensions': {'width': 1920, 'height': 1080}})
        self.assertEqual(dimensions.size(args, (1024, 1280)), (1080, 1920))

    def test_custom_dimensions_require_an_editable_workflow_canvas(self):
        dimensions = importlib.import_module('image_dimensions')
        with self.assertRaisesRegex(ValueError, 'no editable latent image size'):
            dimensions.require_slots(argparse.Namespace(width=1920), argparse.Namespace(latent=None))
        dimensions.require_slots(argparse.Namespace(width=None), argparse.Namespace(latent=None))

    def test_legacy_ship_pixel_metadata_updates_without_a_raw_size_trait(self):
        entry = {'imageDimensions': {'width': 1920, 'height': 1080}, 'gridWidth': 3, 'gridHeight': 2}
        load_ship_generator().persist_size(entry, {})
        self.assertEqual((entry['tokenWidth'], entry['tokenHeight']), (1920, 1080))
        self.assertEqual((entry['gridWidth'], entry['gridHeight']), (3, 2))
