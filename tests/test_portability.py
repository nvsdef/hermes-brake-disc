"""Portability and MCP-consistency checks (H1.2 packaging, 2026-11-02).

Standard library only, so it runs in the SolidPilot venv on Windows and in CI.
"""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {'.md', '.json', '.yaml', '.yml', '.ps1', '.py', '.txt'}
PLACEHOLDERS = {'{{PACKAGE_ROOT}}', '{{ANSYS_AGENT_ROOT}}', '{{ANSYS_AGENT_PYTHON}}', '{{AWP_ROOT261}}'}

# SolidPilot tools OUTSIDE the include filter that the docs are allowed to name.
# Each one was reviewed on 2026-11-02 and is mentioned only as "do not call"
# (a measured trap). A new name here needs the same review.
REVIEWED_EXCLUDED_MENTIONS = {
    'submit_feature_graph', 'rebuild_from_ir', 'auto_dimension_drawing',
    'create_pattern', 'modify_dimension', 'add_mate', 'set_part_material',
    'save_body_as_part', 'compare_parts',
}
# Files that exist to list the full tool catalogue or its traps.
CATALOGUE_FILES = {'tools-used.md', 'tool-traps.md'}


def tracked_text_files():
    """Every text file that ships, except git internals, machine output and the
    original CTS (docs/source is historical evidence, kept verbatim)."""
    for p in ROOT.rglob('*'):
        rel = p.relative_to(ROOT)
        if not p.is_file() or p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if rel.parts[0] in {'.git', '.local'} or '__pycache__' in rel.parts or rel.parts[:2] == ('docs', 'source'):
            continue
        yield p


def inventory(name):
    data = json.loads((ROOT / 'mcp' / f'{name}-tools.json').read_text(encoding='utf-8'))
    return {t['name']: t for t in data['tools']}, data


def include_list():
    text = (ROOT / 'profile' / 'config.template.yaml').read_text(encoding='utf-8')
    block = re.search(r'include:[^\n]*\n((?:\s+- [a-z_]+[^\n]*\n)+)', text).group(1)
    return re.findall(r'- ([a-z_]+)', block)


class PortabilityTests(unittest.TestCase):
    def test_no_author_machine_paths_in_portable_files(self):
        bad = re.compile(r'C:[\\/]+Users[\\/]|OneDrive - NVIDIA|AppData[\\/]Local[\\/]hermes[\\/]profiles')
        for p in tracked_text_files():
            if p.resolve() == Path(__file__).resolve():
                continue  # this file holds the pattern itself
            for i, line in enumerate(p.read_text(encoding='utf-8').splitlines(), 1):
                self.assertIsNone(bad.search(line), f'{p.relative_to(ROOT)}:{i}: {line.strip()[:120]}')

    def test_profile_template_placeholders_and_structure(self):
        text = (ROOT / 'profile' / 'config.template.yaml').read_text(encoding='utf-8')
        self.assertEqual(set(re.findall(r'\{\{[A-Z0-9_]+\}\}', text)), PLACEHOLDERS)
        dirs = re.findall(r'^\s+- "(\{\{PACKAGE_ROOT\}\}/agents/[^"]+)"', text, re.M)
        self.assertEqual(sorted(d.split('/agents/')[1] for d in dirs),
                         sorted(['lead/skills', 'solidworks-engineer/skills', 'spaceclaim-engineer/skills',
                                 'fluent-engineer/skills', '_shared/skills']))
        for d in dirs:
            self.assertTrue((ROOT / d.replace('{{PACKAGE_ROOT}}/', '')).is_dir(), d)
        for key in ('oneshot_max_children: 0', 'max_concurrent_children: 1', '- code_execution', '- delegation'):
            self.assertIn(key, text)
        self.assertNotIn('exclude:', text, 'H1.2 uses tools.include, not tools.exclude')
        self.assertTrue((ROOT / 'profile' / 'SOUL.md').is_file())
        servers = (ROOT / 'profile' / 'servers.template.json').read_text(encoding='utf-8')
        json.loads(servers)
        self.assertLessEqual(set(re.findall(r'\{\{[A-Z0-9_]+\}\}', servers)), PLACEHOLDERS)

    def test_rendered_template_parses_when_yaml_available(self):
        try:
            import yaml
        except ImportError:
            self.skipTest('PyYAML not installed in this interpreter')
        text = (ROOT / 'profile' / 'config.template.yaml').read_text(encoding='utf-8')
        for ph in PLACEHOLDERS:
            text = text.replace(ph, 'D:/x y/' + ph.strip('{}').lower())
        cfg = yaml.safe_load(text)
        self.assertEqual(len(cfg['mcp_servers']['solidpilot']['tools']['include']), 17)
        self.assertEqual(set(cfg['mcp_servers']), {'solidpilot', 'ansys'})
        self.assertEqual(len(cfg['skills']['external_dirs']), 5)

    def test_include_list_matches_inventory_skill_and_environment(self):
        inc = include_list()
        sp, sp_doc = inventory('solidpilot')
        an, an_doc = inventory('ansys')
        env = json.loads((ROOT / 'profile' / 'environment.json').read_text(encoding='utf-8'))
        self.assertEqual(len(inc), len(set(inc)))
        self.assertLessEqual(set(inc), set(sp))
        self.assertEqual(len(inc), env['solidpilot']['include_count'])
        self.assertEqual(len(sp), env['solidpilot']['tool_count'])
        self.assertEqual(len(an), env['ansys_agent']['tool_count'])
        self.assertEqual(sp_doc['tool_count'], len(sp))
        self.assertEqual(an_doc['tool_count'], len(an))
        used = (ROOT / 'agents/solidworks-engineer/skills/sw-solidpilot/references/tools-used.md').read_text(encoding='utf-8')
        include_section = used.split('## Include')[1].split('## Must stay excluded')[0]
        table_tools = re.findall(r'^\| `([a-z_]+)` \|', include_section, re.M)
        self.assertEqual(sorted(table_tools), sorted(inc))
        for broken in ('submit_feature_graph', 'rebuild_from_ir', 'auto_dimension_drawing'):
            self.assertNotIn(broken, inc)

    def test_out_of_filter_tools_only_reviewed_mentions(self):
        sp, _ = inventory('solidpilot')
        excluded = set(sp) - set(include_list())
        found = {}
        for p in list((ROOT / 'agents').rglob('*.md')) + [ROOT / 'AGENTS.md', ROOT / 'profile' / 'SOUL.md']:
            if p.name in CATALOGUE_FILES:
                continue
            text = p.read_text(encoding='utf-8')
            for name in excluded:
                if re.search(r'(?<![A-Za-z_])' + name + r'(?![A-Za-z_])', text):
                    found.setdefault(name, []).append(str(p.relative_to(ROOT)))
        unreviewed = {k: v for k, v in found.items() if k not in REVIEWED_EXCLUDED_MENTIONS}
        self.assertEqual(unreviewed, {}, 'a skill names a SolidPilot tool that the profile filters out')
        never = (ROOT / 'agents/solidworks-engineer/skills/sw-solidpilot/SKILL.md').read_text(encoding='utf-8')
        for name in ('submit_feature_graph', 'rebuild_from_ir', 'create_pattern', 'modify_dimension'):
            self.assertIn(name, never)

    def test_preflight_tool_suffixes_exist(self):
        text = (ROOT / 'agents/lead/skills/brake-lead-run/references/preflight.md').read_text(encoding='utf-8')
        inc = set(include_list())
        an, _ = inventory('ansys')
        sp_row = re.search(r'^\| solidpilot \| (.+) \|$', text, re.M).group(1)
        an_row = re.search(r'^\| ansys \| (.+) \|$', text, re.M).group(1)
        self.assertLessEqual(set(re.findall(r'`([a-z_]+)`', sp_row)), inc)
        self.assertLessEqual(set(re.findall(r'`([a-z_]+)`', an_row)), set(an))

    def test_environment_pins_are_exact_versions(self):
        env = json.loads((ROOT / 'profile' / 'environment.json').read_text(encoding='utf-8'))
        for name, ver in env['ansys_agent']['required_packages'].items():
            self.assertRegex(ver, r'^\d+\.\d+\.\d+$', name)
        self.assertEqual(env['prd_revision'], 'H1.2')
        self.assertEqual(env['conventions']['runs_root'], 'C:/brake-runs')
        self.assertEqual(env['conventions']['solidpilot_root'], 'C:/solidpilot')

    def test_powershell_scripts_are_ps51_safe(self):
        for p in sorted((ROOT / 'scripts').glob('*.ps1')):
            raw = p.read_bytes()
            self.assertTrue(all(b < 128 for b in raw), f'{p.name}: non-ASCII byte (PS 5.1 reads BOM-less files as ANSI)')
            text = raw.decode('ascii')
            self.assertIn("$ErrorActionPreference = 'Stop'", text, p.name)
            # Native commands must go through Invoke-Native, or their stderr aborts PS 5.1.
            for i, line in enumerate(text.splitlines(), 1):
                stripped = line.strip()
                if re.match(r'^(?:\$\w+\s*=\s*)?\(?& (git|gh|hermes|\$py|\$spPy|\$aaPy)\b', stripped):
                    self.fail(f'{p.name}:{i}: native call outside Invoke-Native: {stripped}')
            for token in ('??', '?.', '&&', '||'):
                self.assertNotIn(token, re.sub(r"'[^']*'|\"[^\"]*\"|#.*", '', text), f'{p.name}: PS7-only {token}')

    def test_no_credentials_in_repo(self):
        secret = re.compile(r'nvapi-[A-Za-z0-9_-]{10,}|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|'
                            r'(?i:api[_-]?key)\s*[:=]\s*["\']?[A-Za-z0-9_-]{16,}')
        for p in ROOT.rglob('*'):
            rel = p.relative_to(ROOT)
            if p.is_file() and rel.parts[0] not in {'.git', '.local'} and p.suffix.lower() in TEXT_SUFFIXES:
                self.assertIsNone(secret.search(p.read_text(encoding='utf-8', errors='ignore')), str(rel))

    def test_gitignore_keeps_machine_files_out(self):
        ignore = (ROOT / '.gitignore').read_text(encoding='utf-8').split()
        for entry in ('.local/', 'BUILD_STATE.json', 'runs/', '__pycache__/'):
            self.assertIn(entry, ignore)


if __name__ == '__main__':
    unittest.main()


class StageScriptTests(unittest.TestCase):
    """The two vetted stage scripts (fast run profile, PRD section 6A)."""
    SCRIPTS = ['spaceclaim_prep.py', 'fluent_fast.py']

    def test_scripts_compile_and_take_the_run_folder_from_outside(self):
        import py_compile
        for n in self.SCRIPTS:
            p = ROOT / 'scripts' / 'stages' / n
            py_compile.compile(str(p), doraise=True)
            text = p.read_text(encoding='utf-8')
            self.assertIn('os.environ.get("BRAKE_RUN")', text, n)
            self.assertNotRegex(text, r'FR330V-\d{8}', f'{n}: hard-coded run id')
            self.assertIn('"BLOCKED"', text, f'{n}: must refuse to start beside another Ansys session')

    def test_gate_numbers_are_prd_numbers(self):
        prd = (ROOT / 'specs' / 'PRD.md').read_text(encoding='utf-8').replace(' ', '')
        sc = (ROOT / 'scripts' / 'stages' / 'spaceclaim_prep.py').read_text(encoding='utf-8')
        fl = (ROOT / 'scripts' / 'stages' / 'fluent_fast.py').read_text(encoding='utf-8')
        for v in ('2647566.01', '2030484.53', '167037.60', '240205.78', '42997.28', '330.0'):
            self.assertIn(v, sc)
        for v in ('167037.60', '240205.78', '42997.28', '5864.31', '142865.51'):
            self.assertIn(v, prd, v)
        for v in ('5864.31', '2030484.53'):
            self.assertIn(v, fl)
        # materials in the Fluent script equal PRD MAT-01..03
        for triple in ('(7200.0, 447.0, 52.0)', '(2500.0, 900.0, 1.2)', '(8030.0, 502.0, 16.3)'):
            self.assertIn(triple, fl)
        self.assertIn('"cheek_out", "cheek_in"', fl)   # only the two cheeks rotate

    def test_fast_profile_defaults_match_prd_6a(self):
        prd = (ROOT / 'specs' / 'PRD.md').read_text(encoding='utf-8')
        self.assertIn('## 6A. Fast run profile', prd)
        fl = (ROOT / 'scripts' / 'stages' / 'fluent_fast.py').read_text(encoding='utf-8')
        self.assertIn('END = float(END_ENV) if END_ENV else TS', fl)
        for frag in ('"FAST_DT_S", 0.05', '"FAST_ITERS", 3', '"FAST_WINDOW_STEPS", 4',
                     '"FAST_MESH_MIN_MM", 4.0', '"cheek": 8.0', '"vane": 8.0', '"hat": 12.0'):
            self.assertIn(frag, fl)
        for frag in ('0 to 3.540681 s, the full stop', '0.05 s, 3 iterations per step', 'cheeks 8, vanes 8, hat 12 mm'):
            self.assertIn(frag, prd)


class FlippedTwinContractTests(unittest.TestCase):
    """Decision 46: the inboard twins are flipped instances, consistently everywhere."""
    FLIP = '[1,0,0,0,-1,0,0,0,-1,0,0,0,1]'

    def test_flip_transform_and_counts_are_consistent(self):
        files = {
            'PRD': ROOT / 'specs/PRD.md',
            'pads': ROOT / 'agents/solidworks-engineer/skills/sw-pads-calliper/SKILL.md',
            'B1': ROOT / 'agents/lead/skills/brake-lead-run/references/commission-templates.md',
            'gate': ROOT / 'agents/lead/skills/brake-lead-run/references/gate-checklists.md',
        }
        for k, p in files.items():
            t = p.read_text(encoding='utf-8')
            self.assertIn(self.FLIP, t, k)
            self.assertNotRegex(t, r'MANIFOLD_SOLID_BREP[^\n]{0,40}\b28\b', k)
        prd = files['PRD'].read_text(encoding='utf-8')
        self.assertIn('**25** `MANIFOLD_SOLID_BREP`', prd)
        self.assertIn('**9** `NEXT_ASSEMBLY_USAGE_OCCURRENCE`', prd)

    def test_inboard_parts_are_not_built(self):
        rotor = (ROOT / 'agents/solidworks-engineer/skills/sw-rotor-build/SKILL.md').read_text(encoding='utf-8')
        self.assertIn('## Part 2: `cheek_in` - 0 calls (not built)', rotor)
        pads = (ROOT / 'agents/solidworks-engineer/skills/sw-pads-calliper/SKILL.md').read_text(encoding='utf-8')
        self.assertNotIn("| `innerpad` | -0.022 |", pads)
        self.assertNotIn("| `bp_inner` | -0.031 |", pads)

    def test_spaceclaim_script_never_renames_bodies(self):
        sc = (ROOT / 'scripts/stages/spaceclaim_prep.py').read_text(encoding='utf-8')
        self.assertNotRegex(sc, r'^\s*b\.name\s*=', 'instances share a master body')


class BundledMcpTests(unittest.TestCase):
    """Everything a new workstation needs for the two MCP servers is in the repo."""

    def test_ansys_agent_is_vendored_with_lock(self):
        v = ROOT / 'mcp' / 'ansys-agent'
        for rel in ('ansys_mcp_server.py', 'ansys_agent/__init__.py', 'skills/spaceclaim-cad/SKILL.md',
                    'skills/ansys-fluent-cfd/SKILL.md', 'requirements.lock.txt', 'README.md'):
            self.assertTrue((v / rel).is_file(), rel)
        lock = (v / 'requirements.lock.txt').read_text(encoding='utf-8')
        for pin in ('ansys-geometry-core==0.15.5', 'ansys-fluent-core==0.41.0', 'mcp=='):
            self.assertIn(pin, lock)
        server = (v / 'ansys_mcp_server.py').read_text(encoding='utf-8')
        for tool in json.loads((ROOT / 'mcp' / 'ansys-tools.json').read_text(encoding='utf-8'))['tools']:
            self.assertIn('def ' + tool['name'] + '(', server, tool['name'])
        for junk in ('.venv', 'jobs', 'results', 'viewport', 'kit_ext'):
            self.assertFalse((v / junk).exists(), junk)

    def test_solidpilot_is_pinned_with_lock(self):
        s = ROOT / 'mcp' / 'solidpilot'
        src = (s / 'SOURCE.md').read_text(encoding='utf-8')
        env = json.loads((ROOT / 'profile' / 'environment.json').read_text(encoding='utf-8'))
        self.assertIn(env['solidpilot']['observed_source_head'], src)
        boot = (ROOT / 'scripts' / 'bootstrap_workstation.ps1').read_text(encoding='utf-8')
        self.assertIn(env['solidpilot']['observed_source_head'], boot)
        self.assertIn('mcp==2.0.0', (s / 'requirements.lock.txt').read_text(encoding='utf-8'))
        self.assertTrue((s / 'env.template').is_file())

    def test_claude_mcp_template_registers_both_servers(self):
        cfg = json.loads((ROOT / 'profile' / 'claude_mcp_servers.template.json').read_text(encoding='utf-8'))
        self.assertEqual(set(cfg['mcpServers']), {'solidpilot', 'ansys-agent'})
        self.assertEqual(cfg['mcpServers']['ansys-agent']['env']['ANSYS_RUNTIME_DIR'], 'C:/brake-runs/_ansys-runtime')
