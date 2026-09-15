"""Selectable colour guidance for NPC prompts.

The house palette line - "Keep the palette restrained - greys, olive drab and
rust ..." - used to be baked into every portrait and token prompt. A colour
guidance catalog (color-guidance.json, same shape as art-styles.json) lets a
run swap that sentence for another while the rolled glow, which is light
rather than pigment, keeps its own sentence.
"""
import argparse
import importlib
import io
import json
import random
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest import mock

from test.helpers import FIXTURE_TABLES, load_generator

HOUSE = "Keep the palette restrained"
HOUSE_PIGMENT = "Keep the rest of the palette restrained"
CUSTOM = "Keep the palette to sun-bleached ochre, teal and bone white."
NONE_NAME = "None (no colour guidance)"


class ColorGuidanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('color_guidance'), 'colour guidance catalog module is missing')
        return importlib.import_module('color_guidance')

    def catalog(self, content):
        path = self.root / 'guidance.json'
        path.write_text(content, encoding='utf-8')
        return path

    def custom(self):
        return dict(id='ochre', name='Ochre', prompt=CUSTOM, hidden=False)

    def test_builtins_survive_missing_catalog_and_reserved_ids_are_refused(self):
        guidance = self.module()
        builtins = [dict(guidance.DEFAULT_GUIDANCE), dict(id='none', name=NONE_NAME, prompt='', hidden=False)]
        self.assertEqual(guidance.load_catalog(self.root / 'missing'), builtins)
        for content in ('', '{"guidance":[]}'):
            self.assertEqual(guidance.load_catalog(self.catalog(content)), builtins)
        for content in ('[]', '{"guidance":[{"id":"default","name":"X","prompt":"x"}]}',
                        '{"guidance":[{"id":"none","name":"X","prompt":"x"}]}',
                        '{"guidance":[{"id":"ochre","name":"Ochre","prompt":""}]}',
                        '{"guidance":[{"id":"../x","name":"X","prompt":"x"}]}'):
            with self.assertRaises(ValueError):
                guidance.load_catalog(self.catalog(content))
        self.assertEqual(guidance.select_guidance(self.root / 'missing', 'none')['prompt'], '')

    def test_none_guidance_drops_the_palette_sentence_and_keeps_glow(self):
        gen = load_generator()
        tables = gen.parse_tables(FIXTURE_TABLES)
        none = gen.color_guidance.select_guidance(self.root / 'missing', 'none')
        saw_glow = saw_dark = False
        for seed in range(40):
            npc = gen.roll_npc(tables, random.Random(seed))
            default_prompts = gen.build_prompts(npc)
            none_prompts = gen.build_prompts(npc, None, none)
            for before, after in zip(default_prompts, none_prompts):
                self.assertNotIn('palette', after.lower())
                self.assertNotIn('  ', after)
                self.assertTrue(before.startswith(after.split(' A faint ')[0][:40]))
                # The house line without a glow is one of two no-glow forms;
                # anything else means the default prompt described a glow.
                if 'no stray saturated color' in before or HOUSE_PIGMENT in before:
                    saw_dark = True
                    self.assertNotIn('A faint ', after)
                else:
                    saw_glow = True
                    self.assertIn('A faint ', after)
                    self.assertIn(' glow', after)
            portrait, token = none_prompts
            # The fixture's Weather bullet is a bare fragment, so only the
            # token's seam can be checked for a clean sentence boundary.
            self.assertIn(' Shallow depth of field', portrait)
            self.assertIn('. Behind ', token)
        self.assertTrue(saw_glow and saw_dark, 'fixture never rolled both a glow and no glow')
        for prompt in gen.build_prompts(npc, dict(id='ink', name='Ink', prompt='Monochrome ink wash.', hidden=False), none):
            self.assertNotIn('palette', prompt.lower())
            self.assertIn('Monochrome ink wash.', prompt)

    def test_select_honours_hidden_and_unknown_ids(self):
        guidance = self.module()
        path = self.catalog(json.dumps({'guidance': [dict(self.custom(), hidden=True)]}))
        with self.assertRaises(ValueError):
            guidance.select_guidance(path, 'ochre', False)
        self.assertEqual(guidance.select_guidance(path, 'ochre', True)['prompt'], CUSTOM)
        self.assertEqual(guidance.select_guidance(path, None)['id'], 'default')
        with self.assertRaises(ValueError):
            guidance.select_guidance(path, 'nope')

    def test_custom_guidance_replaces_house_palette_and_keeps_glow(self):
        gen = load_generator()
        tables = gen.parse_tables(FIXTURE_TABLES)
        saw_glow = False
        for seed in range(40):
            npc = gen.roll_npc(tables, random.Random(seed))
            default_prompts = gen.build_prompts(npc)
            self.assertEqual(gen.build_prompts(npc, None, dict(gen.color_guidance.DEFAULT_GUIDANCE)), default_prompts)
            custom_prompts = gen.build_prompts(npc, None, self.custom())
            for before, after in zip(default_prompts, custom_prompts):
                self.assertIn(CUSTOM, after)
                self.assertNotIn(HOUSE, after)
                self.assertNotIn(HOUSE_PIGMENT, after)
                self.assertTrue(before.startswith(after.split(' A faint ')[0][:40]))
                if 'A faint ' in before:
                    saw_glow = True
                    self.assertIn('A faint ', after)
                    self.assertIn(' glow', after)
                    self.assertLess(after.index('A faint '), after.index(CUSTOM))
        self.assertTrue(saw_glow, 'fixture never rolled a glow, so the glow path went untested')

    def test_custom_guidance_survives_art_style_application(self):
        gen = load_generator()
        npc = gen.roll_npc(gen.parse_tables(FIXTURE_TABLES), random.Random(3))
        style = dict(id='ink', name='Ink', prompt='Monochrome ink wash.', hidden=False)
        for prompt in gen.build_prompts(npc, style, self.custom()):
            self.assertIn(CUSTOM, prompt)
            self.assertIn('Monochrome ink wash.', prompt)
            self.assertNotIn(HOUSE, prompt)

    def test_cli_records_guidance_and_regen_preserves_it(self):
        gen = load_generator()
        catalog = self.catalog(json.dumps({'guidance': [self.custom()]}))
        manifest_path = self.root / 'manifest.json'
        graphs = []

        class Comfy:
            base = 'fixture'
            def queue(self, graph):
                graphs.append(graph)
                return 'test'
            def wait(self, *args, **kwargs):
                return {}
            def images(self, record):
                return [{'filename': 'test.png', 'subfolder': 'test', 'type': 'output'}]

        logs = io.StringIO()
        flags = ['--tables', str(FIXTURE_TABLES), '--out', str(self.root / 'out'), '--manifest', str(manifest_path),
                 '--color-guidance-catalog', str(catalog), '--pause', '0']
        with mock.patch.object(gen.art, 'find_server', return_value=Comfy()), \
                mock.patch.object(gen, 'fetch', side_effect=lambda comfy, image, target: (target.write_bytes(b'png'), target)[1]), \
                redirect_stdout(logs), redirect_stderr(logs):
            self.assertEqual(gen.main(flags + ['--color-guidance', 'ochre', '--seed', '5']), 0, logs.getvalue())
            manifest = json.loads(manifest_path.read_text())
            folder, entry = next(iter(manifest.items()))
            self.assertEqual(entry['color_guidance'], {'id': 'ochre', 'name': 'Ochre'})
            self.assertIn(CUSTOM, entry['portraitPrompt'])
            self.assertIn(CUSTOM, entry['tokenPrompt'])
            self.assertNotIn(HOUSE, entry['tokenPrompt'])

            self.assertEqual(gen.main(flags + ['--regen-manifest', str(manifest_path), '--regen-id', entry['id']]), 0, logs.getvalue())
            regenerated = json.loads(manifest_path.read_text())[folder]
            self.assertEqual(regenerated['color_guidance'], entry['color_guidance'])
            self.assertIn(CUSTOM, regenerated['portraitPrompt'])

            self.assertEqual(gen.main(flags + ['--regen-manifest', str(manifest_path), '--regen-id', entry['id'],
                                              '--color-guidance', 'default']), 0, logs.getvalue())
            reverted = json.loads(manifest_path.read_text())[folder]
            self.assertEqual(reverted['color_guidance'], {'id': 'default', 'name': 'Default'})
            self.assertIn(HOUSE, reverted['portraitPrompt'] + reverted['tokenPrompt'])

            self.assertEqual(gen.main(flags + ['--regen-manifest', str(manifest_path), '--regen-id', entry['id'],
                                              '--color-guidance', 'none']), 0, logs.getvalue())
            bare = json.loads(manifest_path.read_text())[folder]
            self.assertEqual(bare['color_guidance'], {'id': 'none', 'name': NONE_NAME})
            self.assertNotIn('palette', (bare['portraitPrompt'] + bare['tokenPrompt']).lower())

            self.assertEqual(gen.main(flags + ['--regen-manifest', str(manifest_path), '--regen-id', entry['id']]), 0, logs.getvalue())
            kept = json.loads(manifest_path.read_text())[folder]
            self.assertEqual(kept['color_guidance'], {'id': 'none', 'name': NONE_NAME})
            self.assertNotIn('palette', (kept['portraitPrompt'] + kept['tokenPrompt']).lower())
        self.assertGreaterEqual(len(graphs), 5)

    def test_legacy_entry_without_guidance_regenerates_with_default(self):
        guidance = self.module()
        args = argparse.Namespace(color_guidance=None, color_guidance_catalog=self.root / 'missing')
        guidance.restore_record(args, {'seed': 1})
        self.assertEqual(args.selected_guidance['id'], 'default')
        self.assertEqual(guidance.metadata(args), {'color_guidance': {'id': 'default', 'name': 'Default'}})

    def test_unknown_guidance_is_a_usage_error(self):
        gen = load_generator()
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            gen.parse_args(['--color-guidance', 'nope', '--color-guidance-catalog', str(self.root / 'missing'), '--dry-run'])


if __name__ == '__main__':
    unittest.main()
