import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ClientTests(unittest.TestCase):
    def test_load_rejects_unknown_server_and_preserves_config(self):
        path = ROOT / 'scripts' / 'mcp_client.py'
        self.assertTrue(path.exists(), 'generic MCP transport utility is missing')
        spec = importlib.util.spec_from_file_location('brake_mcp_client', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as d:
            config = Path(d) / 'servers.json'
            text = '{"servers":{"solidpilot":{"command":"python","args":["server.py"]}}}'
            config.write_text(text, encoding='utf-8')
            self.assertEqual(mod.load_server(config, 'solidpilot')['args'], ['server.py'])
            with self.assertRaises(ValueError):
                mod.load_server(config, 'unknown')
            self.assertEqual(config.read_text(encoding='utf-8'), text)


class TimeoutTests(unittest.TestCase):
    def test_mcp_two_uses_seconds_and_one_uses_timedelta(self):
        path = ROOT / 'scripts' / 'mcp_client.py'
        spec = importlib.util.spec_from_file_location('brake_mcp_timeout', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertTrue(hasattr(mod, 'sdk_timeout'), 'SDK timeout adapter is missing')
        from datetime import timedelta
        self.assertEqual(mod.sdk_timeout(180, '2.0.0a1'), 180.0)
        self.assertEqual(mod.sdk_timeout(180, '1.26.0'), timedelta(seconds=180))


if __name__ == '__main__':
    unittest.main()
