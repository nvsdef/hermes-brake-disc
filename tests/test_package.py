import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
ROLES = ['lead', 'solidworks-engineer', 'spaceclaim-engineer', 'fluent-engineer']
EXPECTED_SKILLS = {
    'lead': ['brake-lead-run', 'brake-duty-cycle', 'brake-design-review', 'brake-report'],
    'solidworks-engineer': ['sw-solidpilot', 'sw-rotor-build', 'sw-pads-calliper'],
    'spaceclaim-engineer': ['sc-geometry-tagging'],
    'fluent-engineer': ['fl-meshing', 'fl-thermal-solve', 'fl-postprocess-energy'],
    '_shared': ['brake-handoff'],
}


def skill_files():
    return sorted((ROOT / 'agents').glob('*/skills/*/SKILL.md'))


class PackageTests(unittest.TestCase):
    def test_roles_and_souls(self):
        self.assertEqual(sorted(p.name for p in (ROOT / 'agents').iterdir() if p.is_dir()),
                         sorted(ROLES + ['_shared']))
        for role in ROLES:
            self.assertGreater(len((ROOT / 'agents' / role / 'SOUL.md').read_text(encoding='utf-8').split()), 800)

    def test_expected_skills_present_and_routed_in_agents_md(self):
        agents_md = (ROOT / 'AGENTS.md').read_text(encoding='utf-8')
        for role, names in EXPECTED_SKILLS.items():
            for name in names:
                self.assertTrue((ROOT / 'agents' / role / 'skills' / name / 'SKILL.md').is_file(), name)
                self.assertIn(name, agents_md, name)

    def test_skill_frontmatter_and_references(self):
        files = skill_files()
        self.assertEqual(len(files), sum(len(v) for v in EXPECTED_SKILLS.values()))
        for path in files:
            text = path.read_text(encoding='utf-8')
            self.assertTrue(text.startswith('---\n'), path)
            name = re.search(r'^name: "?([a-z0-9-]+)"?$', text, re.M).group(1)
            self.assertEqual(name, path.parent.name)
            desc = re.search(r'^description: "(.+)"$', text, re.M).group(1)
            self.assertLessEqual(len(desc), 60, path)
            self.assertIn('## Verification', text, path)
            self.assertGreater(len(text.split()), 700, path)
            for relative in set(re.findall(r'references/[A-Za-z0-9_-]+\.md', text)):
                self.assertTrue((path.parent / relative).is_file(), f'{path}: {relative}')

    def test_no_glued_numbers_in_skills(self):
        bad = re.compile(r'\b(?:within|all|record|count|initialize|target|below|Expected)\d')
        for path in (ROOT / 'agents').rglob('*.md'):
            self.assertIsNone(bad.search(path.read_text(encoding='utf-8')), path)

    def test_no_prebuilt_engineering_code_or_completed_checkpoint(self):
        self.assertEqual([p.name for p in (ROOT / 'scripts').glob('*.py')], ['mcp_client.py'])
        self.assertEqual(list((ROOT / 'agents').rglob('*.py')), [])
        state = json.loads((ROOT / 'examples/BUILD_STATE.template.json').read_text())
        self.assertEqual(state['status'], 'pending')
        self.assertEqual(state['completed_gates'], [])
        self.assertIsNone(state['run_id'])
        self.assertEqual(state['prd_revision'], 'H1.2')

    def test_all_cts_requirement_identifiers_in_prd(self):
        source = (ROOT / 'docs/source/CTS-BRK-0117-revC.md').read_text(encoding='utf-8')
        prd = (ROOT / 'specs/PRD.md').read_text(encoding='utf-8')
        ids = set(re.findall(r'\b(?:PKG|THM|MAS|GEO|PAD|MAT|DV)-\d{2}\b', source))
        for identifier in ids:
            self.assertIn(identifier, prd)

    def test_no_drawing_stage_or_stale_revision(self):
        for path in list((ROOT / 'agents').rglob('*.md')) + [ROOT / 'AGENTS.md', ROOT / 'specs/handoffs.md']:
            text = path.read_text(encoding='utf-8')
            self.assertNotIn('H1.1', text, path)
        self.assertFalse((ROOT / 'agents/solidworks-engineer/skills/sw-drawing-visuals').exists())

    def test_prompt_is_short_and_points_at_prd(self):
        prompt = (ROOT / 'examples/prompt.md').read_text(encoding='utf-8').strip().splitlines()
        self.assertLessEqual(len(prompt), 3)
        self.assertIn('specs/PRD.md', ' '.join(prompt))


if __name__ == '__main__':
    unittest.main()
