"""Generic MCP client. No product operations, implicit retries or global config writes."""
import argparse
import asyncio
from datetime import timedelta
import json
import os
from pathlib import Path
import sys


def load_server(path, name):
    data = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    servers = data.get('servers', {})
    if name not in servers:
        raise ValueError(f'Unknown server: {name}')
    cfg = servers[name]
    if not isinstance(cfg.get('command'), str) or not isinstance(cfg.get('args', []), list):
        raise ValueError('Server needs a command string and args list')
    return cfg


def sdk_timeout(seconds, version):
    """MCP 2 uses float seconds; MCP 1 used datetime.timedelta."""
    return float(seconds) if int(version.split('.')[0]) >= 2 else timedelta(seconds=seconds)


async def request(cfg, action, tool=None, arguments=None):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    # Explicit allowlist: do not forward model-provider credentials to application servers.
    safe = {'PATH', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'USERPROFILE', 'LOCALAPPDATA',
            'APPDATA', 'TEMP', 'TMP', 'TMPDIR', 'PROGRAMFILES', 'PROGRAMFILES(X86)',
            'PROGRAMDATA', 'HOMEDRIVE', 'HOMEPATH', 'PYTHONIOENCODING'}
    env = {k: v for k, v in os.environ.items() if k.upper() in safe}
    env.update(cfg.get('env', {}))
    params = StdioServerParameters(command=cfg['command'], args=cfg.get('args', []),
                                   env=env, cwd=cfg.get('cwd'))
    from importlib.metadata import version
    timeout = sdk_timeout(cfg.get('timeout', 180), version('mcp'))
    async with stdio_client(params) as streams:
        async with ClientSession(*streams, read_timeout_seconds=timeout) as session:
            await session.initialize()
            available = await session.list_tools()
            if action == 'list':
                return available.model_dump(mode='json', exclude_none=True)
            names = {t.name for t in available.tools}
            if tool not in names:
                raise ValueError(f'Tool not discovered: {tool}')
            result = await session.call_tool(tool, arguments or {})
            return result.model_dump(mode='json', exclude_none=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path(__file__).resolve().parents[1] / '.local' / 'servers.json')
    parser.add_argument('--server', required=True)
    parser.add_argument('action', choices=['list', 'call'])
    parser.add_argument('--tool')
    parser.add_argument('--arguments', type=Path, help='JSON argument object, not Python source')
    parser.add_argument('--output', type=Path, help='Optional NEW evidence file; never overwrites')
    args = parser.parse_args()
    cfg = load_server(args.config, args.server)
    payload = json.loads(args.arguments.read_text(encoding='utf-8-sig')) if args.arguments else {}
    if not isinstance(payload, dict):
        parser.error('Arguments must be an object')
    if args.action == 'call' and not args.tool:
        parser.error('call requires --tool')
    if args.output and args.output.exists():
        parser.error('Evidence output already exists; choose a new path before calling')
    result = asyncio.run(request(cfg, args.action, args.tool, payload))
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as f:
            f.write(text)
    print(text)
    return 1 if result.get('isError') else 0


if __name__ == '__main__':
    sys.exit(main())
