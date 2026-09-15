import argparse
import importlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest import mock

from test.helpers import load_generator, load_ship_generator


class ArtStylesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def styles(self):
        self.assertIsNotNone(importlib.util.find_spec('art_styles'), 'shared style catalog is missing')
        return importlib.import_module('art_styles')

    def catalog(self, content):
        path = self.root / 'styles.json'
        path.write_text(content, encoding='utf-8')
        return path

    def test_default_survives_missing_empty_and_reserved_override(self):
        styles = self.styles()
        self.assertEqual(styles.load_catalog(self.root / 'missing'), [dict(styles.DEFAULT_STYLE)])
        for content in ('', ' \n\t ', '{"styles":[]}'):
            self.assertEqual(styles.load_catalog(self.catalog(content)), [dict(styles.DEFAULT_STYLE)])
        with self.assertRaises(ValueError):
            styles.load_catalog(self.catalog('{"styles":[{"id":"default","name":"Secret","prompt":"x","hidden":true}]}'))

    def test_hidden_alias_and_strict_validation(self):
        styles = self.styles()
        path = self.catalog('{"styles":[{"id":"ink","name":"Ink","prompt":"ink wash","secret":true}]}')
        with self.assertRaises(ValueError):
            styles.select_style(path, 'ink', False)
        self.assertTrue(styles.select_style(path, 'ink', True)['hidden'])
        for content in ('[]', '{"styles":[{"id":"x","name":"X","prompt":"","hidden":false}]}',
                        '{"styles":[{"id":"../x","name":"X","prompt":"ink"}]}'):
            with self.assertRaises(ValueError):
                styles.load_catalog(self.catalog(content))

    def test_private_cli_routes_and_rejects_escape(self):
        self.styles()
        config = self.root / 'config.json'
        config.write_text(json.dumps({'secretImagesDir': str(self.root / 'private')}))
        for generator, category in ((load_generator(), 'npcs'), (load_ship_generator(), 'spaceships')):
            args = generator.parse_args(['--secret', '--secret-config', str(config), '--dry-run'])
            self.assertEqual(args.manifest, self.root / 'private' / 'manifest.json')
            self.assertTrue(args.out.is_relative_to(self.root / 'private' / category))
            with self.assertRaises(SystemExit):
                generator.parse_args(['--secret', '--secret-config', str(config), '--out', str(self.root / 'public')])

    def test_custom_templates_replace_house_style_keep_framing(self):
        styles = self.styles()
        custom = {'id': 'ink', 'name': 'Ink', 'prompt': 'Monochrome ink wash.', 'hidden': False}
        for module in (load_generator(), load_ship_generator()):
            for template in (module.PORTRAIT_TEMPLATE, module.TOKEN_TEMPLATE):
                self.assertEqual(styles.apply_style(template, styles.DEFAULT_STYLE), template)
                actual = styles.apply_style(template, custom)
                self.assertIn('Monochrome ink wash.', actual)
                self.assertNotIn('painterly', actual)
                self.assertNotIn('halftone', actual)
                if template == module.TOKEN_TEMPLATE:
                    self.assertIn('empty plain white void', actual)
                    self.assertIn('frame', actual)

    def test_regen_refuses_public_manifest_and_preserves_saved_style(self):
        styles = self.styles()
        config = self.root / 'config.json'
        config.write_text(json.dumps({'secretImagesDir': str(self.root / 'private')}))
        args = argparse.Namespace(secret=True, secret_config=config, art_styles=self.root / 'missing', art_style=None)
        styles.configure(args, 'npcs')
        with self.assertRaises(ValueError):
            styles.restore_record(args, {'secret': True}, self.root / 'public', self.root / 'public.json')
        with self.assertRaises(ValueError):
            styles.restore_record(argparse.Namespace(secret=False), {'secret': True}, self.root / 'private', None)

    def test_private_derived_source_requires_secret_and_private_destination(self):
        styles = self.styles()
        image = self.root / 'scene.png'
        image.write_bytes(b'fixture')
        image.with_suffix('.background.json').write_text(json.dumps({'secret': True}))
        with self.assertRaises(ValueError):
            styles.check_source(argparse.Namespace(secret=False), image)

    def test_existing_private_output_tree_rejects_resolved_file_escape(self):
        styles = self.styles()
        args = argparse.Namespace(secret=True, secret_root=self.root)
        folder = self.root / 'nested'
        folder.mkdir()
        target = folder / 'output.png'
        target.write_bytes(b'existing')
        original = Path.resolve
        def resolve(path, *a, **kw):
            return self.root.parent / 'public.png' if path == target else original(path, *a, **kw)
        with mock.patch.object(Path, 'resolve', resolve), self.assertRaises(ValueError):
            styles.safe_output_directory(args, folder)

    def test_graph_enforcement_overrides_traversal_and_preview_output(self):
        styles = self.styles()
        args = argparse.Namespace(secret=True, private_prefix='secret/job')
        graph = {'1': {'class_type': 'SaveImage', 'inputs': {'filename_prefix': '../../public'}}}
        styles.protect_graph(graph, args)
        prefix = graph['1']['inputs']['filename_prefix']
        self.assertTrue(prefix.startswith('secret/job/'))
        self.assertNotIn('..', prefix)
        with self.assertRaises(ValueError):
            styles.protect_graph({'2': {'class_type': 'PreviewImage', 'inputs': {}}}, args)

    def test_catalogue_style_replacement_retains_hardware_description(self):
        styles = self.styles()
        prompt = load_generator().art.parse_prompts(load_generator().art.DEFAULT_PROMPTS)[0].prompt
        custom = dict(id='ink', name='Ink', prompt='Ink {wash}.', hidden=False)
        actual = styles.apply_style(prompt, custom)
        self.assertNotIn('painterly', actual)
        self.assertNotIn('halftone', actual)
        self.assertIn('weathered olive-grey armor plating', actual)
        self.assertIn('clear empty space above and below', actual)
        self.assertIn('Ink {wash}.', actual)

    def test_private_npc_generation_and_regeneration_keep_metadata_and_prefixes(self):
        generator = load_generator()
        catalog = self.catalog('{"styles":[{"id":"ink","name":"Ink","prompt":"Ink {wash}.","hidden":true}]}')
        config = self.root / 'config.json'
        private = self.root / 'private'
        config.write_text(json.dumps({'secretImagesDir': str(private)}))
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

        logs = io.StringIO()
        flags = ['--secret', '--secret-config', str(config), '--art-styles', str(catalog), '--pause', '0']
        with mock.patch.object(generator.art, 'find_server', return_value=Comfy()), \
                mock.patch.object(generator, 'fetch', side_effect=lambda comfy, image, target: (target.write_bytes(b'png'), target)[1]), \
                redirect_stdout(logs), redirect_stderr(logs):
            self.assertEqual(generator.main(flags + ['--art-style', 'ink', '--seed', '5']), 0, logs.getvalue())
            manifest_path = private / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            folder, entry = next(iter(manifest.items()))
            self.assertTrue(Path(folder).is_relative_to(private / 'npcs'))
            self.assertEqual(entry['art_style'], {'id': 'ink', 'name': 'Ink'})
            self.assertTrue(entry['secret'])
            self.assertIn('Ink {wash}.', entry['portraitPrompt'])
            self.assertEqual(generator.main(flags + ['--regen-manifest', str(manifest_path), '--regen-id', entry['id']]), 0)
            regenerated = json.loads(manifest_path.read_text())[folder]
            self.assertEqual(regenerated['art_style'], entry['art_style'])
            self.assertTrue(regenerated['secret'])
        self.assertGreaterEqual(len(graphs), 6)
        for graph in graphs:
            for node in graph.values():
                prefix = node.get('inputs', {}).get('filename_prefix')
                if prefix:
                    self.assertTrue(prefix.startswith('secret/'), prefix)

    def test_catalogue_downloads_include_style_sidecars(self):
        art = load_generator().art
        class Comfy:
            base = 'fixture'
            download = art.Comfy.download
            def _get_bytes(self, path):
                return b'png'
            def queue(self, graph):
                return 'test'
            def wait(self, *args, **kwargs):
                return {}
            def images(self, record):
                return [{'filename': 'test.png', 'subfolder': 'rendered', 'type': 'output'}]
        output = self.root / 'output'
        with mock.patch.object(art, 'find_server', return_value=Comfy()), redirect_stdout(io.StringIO()):
            self.assertEqual(art.main(['--limit', '1', '--download-to', str(output), '--manifest', str(self.root / 'manifest.json')]), 0)
        sidecar = output / 'rendered' / 'test.background.json'
        self.assertTrue(sidecar.exists(), 'catalogue download must carry style metadata beside the image')
        data = json.loads(sidecar.read_text())
        self.assertEqual(data['art_style'], {'id': 'default', 'name': 'Default'})
        self.assertFalse(data['secret'])

    def test_legacy_background_catalogues_replace_rendering_instructions(self):
        styles = self.styles()
        art = load_generator().art
        for filename in ('scene-background-art-prompts.md', 'city-background-art-prompts.md', 'battlemap-art-prompts.md'):
            for entry in art.parse_prompts(art.SCRIPT_DIR / 'prompts' / filename):
                result = styles.apply_style(entry.prompt, dict(id='ink', prompt='Ink wash.'))
                for old_style in ('painterly', 'halftone', 'Photorealistic', 'Not an illustration'):
                    self.assertNotIn(old_style, result, entry.name)
                self.assertIn('Ink wash.', result)

    def test_battlemap_custom_style_reaches_graph_and_saved_metadata(self):
        import background_scene as scene
        cli = scene._load_module('generate-background.py', 'style_background_cli')
        expressions = scene._load_module('generate-expressions.py', 'lancer_background_expressions')
        catalog = self.catalog('{"styles":[{"id":"ink","name":"Ink","prompt":"Monochrome ink wash.","hidden":false}]}')
        source = self.root / 'reference.png'
        source.write_bytes(b'fixture')
        output = self.root / 'maps'
        graphs = []
        def render(comfy, graph, timeout):
            graphs.append(graph)
            return b'fixture rendered pixels'
        with mock.patch.object(scene.art_module(), 'find_server', return_value=object()), \
                mock.patch.object(expressions, 'upload_image', return_value='reference.png [input]'), \
                mock.patch.object(cli, '_render_graph', side_effect=render), redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['--battlemap', str(source), '--output-dir', str(output),
                                       '--art-styles', str(catalog), '--art-style', 'ink']), 0)
        self.assertEqual(len(graphs), 1)
        prompt = graphs[0]['9']['inputs']['prompt']
        self.assertIn('Monochrome ink wash.', prompt)
        self.assertIn('exactly 90 degrees to the floor', prompt)
        self.assertNotIn('and illustration style', prompt)
        metadata = json.loads(next(output.glob('*.background.json')).read_text())
        self.assertEqual(metadata['prompt'], prompt)
        self.assertEqual(metadata['art_style'], {'id': 'ink', 'name': 'Ink'})


if __name__ == '__main__':
    unittest.main()
