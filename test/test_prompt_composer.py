"""Composer fragments must reproduce and reorder the actual rendered prompts."""
import contextlib
import io
import random
import unittest

from test.helpers import FIXTURE_TABLES, load_generator, manifest_entry

gen = load_generator()


class PromptComposerTests(unittest.TestCase):
    def npc(self):
        return gen.roll_npc(gen.parse_tables(FIXTURE_TABLES), random.Random(17))

    def test_parts_reproduce_existing_prompts_and_identify_tables(self):
        npc = self.npc()
        original = gen.build_prompts(npc)
        self.assertTrue(callable(getattr(gen, 'build_prompt_parts', None)),
                        'generator must expose the fragments used by the composer')
        parts = gen.build_prompt_parts(npc)
        for target, prompt in zip(('portrait', 'token'), original):
            self.assertEqual(''.join(p['text'] for p in parts[target]), prompt)
            self.assertEqual(len({p['id'] for p in parts[target]}), len(parts[target]))
            self.assertTrue(any('Role' in p['sources'] for p in parts[target]))

    def test_reorder_changes_render_and_survives_manifest_reload(self):
        npc = self.npc()
        npc['_extra'] = {'camera': 'low angle looking up'}
        npc['_prompt_layout'] = {'portrait': ['extra:camera']}
        portrait, token = gen.build_prompts(npc)
        self.assertTrue(portrait.lower().startswith('low angle looking up'))
        self.assertFalse(token.lower().startswith('low angle looking up'))
        record = gen.extra_record(npc)
        self.assertEqual(record.get('promptLayout'), npc['_prompt_layout'])
        entry = manifest_entry(17)
        entry.update(record)
        restored = gen.npc_from_entry(entry, entry['id'], warn=False)
        self.assertEqual(restored['_prompt_layout'], npc['_prompt_layout'])
        gen.reroll_trait(gen.parse_tables(FIXTURE_TABLES), restored, 'Demeanor', random.Random(18))
        self.assertEqual(restored['_prompt_layout'], npc['_prompt_layout'])

    def test_preview_json_does_not_render(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            try:
                result = gen.main(['--tables', str(FIXTURE_TABLES), '--seed', '17', '--prompt-preview'])
            except SystemExit:
                self.fail('the generator must support a read-only JSON prompt preview')
        import json
        self.assertEqual(result, 0)
        self.assertIn('portrait', json.loads(out.getvalue()))

    def test_custom_text_targets_and_disabled_sources(self):
        npc = self.npc()
        npc['_extra'] = {'camera': 'a unique camera angle'}
        npc['_extra_targets'] = {'camera': 'portrait'}
        npc['_disabled'] = ['Backdrop', 'Hair colour', 'Role']
        parts = gen.build_prompt_parts(npc)
        self.assertTrue(any(p['id'] == 'extra:camera' for p in parts['portrait']))
        self.assertFalse(any(p['id'] == 'extra:camera' for p in parts['token']))
        for snippets in parts.values():
            self.assertFalse(any(set(p['sources']) & set(npc['_disabled']) for p in snippets))
        npc['_prompt_layout'] = {'token': [{'id': 'custom:test', 'text': 'Exact {literal} text.'}]}
        portrait, token = gen.build_prompts(npc)
        self.assertTrue(token.startswith('Exact {literal} text.'))
        self.assertNotIn('Exact {literal}', portrait)

    def test_fragments_match_styles_and_disabled_tables(self):
        for seed in range(8):
            npc = gen.roll_npc(gen.parse_tables(FIXTURE_TABLES), random.Random(seed))
            npc['_extra'] = {'one': 'my first trait', 'two': 'my second trait.'}
            npc['_disabled'] = ['Height', 'Role'] if seed % 2 else []
            for style in [None, {'id': 'none', 'prompt': ''}, {'id': 'ink', 'prompt': 'Ink wash.'}]:
                parts = gen.build_prompt_parts(npc, style)
                original = gen.build_prompts(npc, style)
                for target, prompt in zip(('portrait', 'token'), original):
                    self.assertEqual(''.join(p['text'] for p in parts[target]), prompt)

    def test_fixed_prose_keeps_its_position_when_a_table_is_disabled(self):
        npc = self.npc()
        parts = gen.build_prompt_parts(npc)
        npc['_prompt_layout'] = {'portrait': [part['id'] for part in parts['portrait']]}
        npc['_disabled'] = ['Height']
        composed = gen.build_prompts(npc)[0]
        npc.pop('_prompt_layout')
        original = gen.build_prompts(npc)[0]
        self.assertEqual(composed.split(), original.split())

    def test_style_transforms_table_text_in_preview_and_generation_equally(self):
        npc = self.npc()
        npc['_extra'] = {'camera': 'a photograph taken from above'}
        style = {'id': 'ink', 'prompt': 'Ink wash.'}
        parts = gen.build_prompt_parts(npc, style)
        original = gen.build_prompts(npc, style)[0]
        self.assertEqual(''.join(p['text'] for p in parts['portrait']), original)

    def test_preview_cannot_enter_regeneration(self):
        from unittest.mock import patch
        with patch.object(gen, 'regenerate_one') as regenerate:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                gen.main(['--prompt-preview', '--regen-manifest', 'does-not-exist.json', '--regen-id', 'npc-test'])
            regenerate.assert_not_called()
