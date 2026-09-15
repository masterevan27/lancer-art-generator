import unittest
from pathlib import Path
from test.helpers import load_generator, load_ship_generator
from tempfile import TemporaryDirectory


class WorkflowSelectionTests(unittest.TestCase):
    def test_explicit_workflow_overrides_gender_and_recorded_workflow(self):
        gen = load_generator()
        args = gen.parse_args(['--workflow', 'chosen.json', '--dry-run'])
        npc = {'_pronouns': {'gender': 'woman'}}
        self.assertEqual(gen.workflow_for(args, npc), Path('chosen.json'))
        self.assertEqual(gen.resolve_recorded_workflow({'workflow': 'old.json'}, npc, args), Path('chosen.json'))

    def test_default_retains_gender_selection(self):
        gen = load_generator()
        args = gen.parse_args(['--dry-run'])
        self.assertEqual(gen.workflow_for(args, {'_pronouns': {'gender': 'woman'}}), args.workflow_woman)

    def test_ship_regeneration_retains_recorded_workflow_unless_overridden(self):
        gen = load_ship_generator()
        with TemporaryDirectory() as folder:
            recorded = Path(folder) / 'original.json'
            recorded.write_text('{}')
            self.assertEqual(gen.resolve_recorded_workflow({'workflow': str(recorded)}, gen.parse_args([])), recorded)
            args = gen.parse_args(['--workflow', 'chosen.json'])
            self.assertEqual(gen.resolve_recorded_workflow({'workflow': str(recorded)}, args), Path('chosen.json'))
