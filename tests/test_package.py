import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
ROLES = ['lead', 'solidworks-engineer', 'spaceclaim-engineer', 'fluent-engineer']
EXPECTED_SKILLS = {
    'lead': ['brake-lead-run', 'brake-duty-cycle'],
    'solidworks-engineer': ['sw-solidpilot', 'sw-rotor-build', 'sw-pads-calliper'],
    'spaceclaim-engineer': ['sc-fast-prep'],
    'fluent-engineer': ['fl-fast-run'],
    '_shared': ['brake-handoff'],
}
STAGE_SCRIPTS = ['fluent_fast.py', 'spaceclaim_prep.py']


def skill_files():
    return sorted((ROOT / 'agents').glob('*/skills/*/SKILL.md'))


class PackageTests(unittest.TestCase):
    def test_roles_and_souls(self):
        self.assertEqual(sorted(p.name for p in (ROOT / 'agents').iterdir() if p.is_dir()),
                         sorted(ROLES + ['_shared']))
        for role in ROLES:
            self.assertGreater(len((ROOT / 'agents' / role / 'SOUL.md').read_text(encoding='utf-8').split()), 450)

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
            self.assertGreater(len(text.split()), 650, path)
            for relative in set(re.findall(r'references/[A-Za-z0-9_-]+\.md', text)):
                self.assertTrue((path.parent / relative).is_file(), f'{path}: {relative}')

    def test_no_glued_numbers_in_skills(self):
        bad = re.compile(r'\b(?:within|all|record|count|initialize|target|below|Expected)\d')
        for path in (ROOT / 'agents').rglob('*.md'):
            self.assertIsNone(bad.search(path.read_text(encoding='utf-8')), path)

    def test_only_vetted_stage_scripts_and_clean_checkpoint(self):
        self.assertEqual([p.name for p in (ROOT / 'scripts').glob('*.py')], ['mcp_client.py'])
        self.assertEqual(sorted(p.name for p in (ROOT / 'scripts' / 'stages').glob('*.py')), STAGE_SCRIPTS)
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

    def test_no_drawing_image_or_report_stage_or_stale_revision(self):
        banned = re.compile(r'cad_iso|section_9deg\.png|named_selections\.png|report\.pdf|50_report|save_picture|'
                            r'brake-report|brake-design-review|sc-geometry-tagging|fl-meshing|fl-thermal-solve|fl-postprocess')
        files = list((ROOT / 'agents').rglob('*.md')) + [ROOT / 'AGENTS.md', ROOT / 'specs/handoffs.md',
                                                         ROOT / 'profile/SOUL.md', ROOT / 'examples/prompt.md']
        for path in files:
            text = path.read_text(encoding='utf-8')
            self.assertNotIn('H1.1', text, path)
            self.assertIsNone(banned.search(text), f'{path}: {banned.search(text)}')
        for gone in ('solidworks-engineer/skills/sw-drawing-visuals', 'lead/skills/brake-report',
                     'lead/skills/brake-design-review', 'spaceclaim-engineer/skills/sc-geometry-tagging'):
            self.assertFalse((ROOT / 'agents' / gone).exists(), gone)

    def test_no_step_reimport_in_cad_procedure(self):
        text = (ROOT / 'agents/solidworks-engineer/skills/sw-pads-calliper/SKILL.md').read_text(encoding='utf-8')
        self.assertNotIn('open_document(file_path=...brake.step)', text)
        self.assertIn('No STEP re-import', (ROOT / 'agents/solidworks-engineer/SOUL.md').read_text(encoding='utf-8'))

    def test_prompt_is_short_and_points_at_prd(self):
        prompt = (ROOT / 'examples/prompt.md').read_text(encoding='utf-8').strip().splitlines()
        self.assertLessEqual(len(prompt), 3)
        self.assertIn('specs/PRD.md', ' '.join(prompt))


if __name__ == '__main__':
    unittest.main()
