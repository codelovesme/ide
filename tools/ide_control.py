#!/usr/bin/env python3
"""Session-local IDE control client, CLI launch adapters and stdio MCP server.

No packages required. The private descriptor carries credentials; model-facing
context contains only identities and a command pointing to that descriptor.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import shlex
import shutil
import stat
import sys
import tempfile
import urllib.error
import urllib.request

PROTOCOL = 1
SLOTS = {'left': 'l', 'right': 'r', 'top': 't', 'bottom': 'b', 'center': 'c'}


def initialize():
    root = Path(tempfile.mkdtemp(prefix='codelovesme-ide-'))
    root.chmod(0o700)
    helper = str(Path(__file__).resolve())
    bindir = root / 'bin'
    bindir.mkdir(mode=0o700)
    (bindir / '.codelovesme-ide-agents').touch(mode=0o600)
    for name in ('claude', 'codex', 'ide-control'):
        command = ['python3', helper]
        if name != 'ide-control':
            command += ['agent', name]
        script = '#!/bin/sh\nexec ' + shlex.join(command) + ' "$@"\n'
        (bindir / name).write_text(script)
        (bindir / name).chmod(0o700)
    # Bash startup files commonly prepend ~/.local/bin. Source the user's
    # rc first, then put these per-session adapters first without editing it.
    bashrc = root / 'bashrc'
    bashrc.write_text('if [ -f "$HOME/.bashrc" ]; then . "$HOME/.bashrc"; fi\n'
                      + 'export PATH=' + shlex.quote(str(bindir)) + ':"$PATH"\n')
    bashrc.chmod(0o600)
    info = dict(version=PROTOCOL, session=secrets.token_hex(16),
                token=secrets.token_urlsafe(32), descriptor=str(root / 'session.json'),
                helper=helper, bin=str(bindir), bashrc=str(bashrc))
    write_private(root / 'session.json', info)
    return info


def write_private(path, data):
    temp = path.with_suffix('.tmp')
    with open(temp, 'w', opener=lambda p, flags: os.open(p, flags | os.O_NOFOLLOW, 0o600)) as stream:
        json.dump(data, stream)
    temp.replace(path)


def descriptor(path=None):
    path = Path(path or os.environ.get('CODELOVESME_IDE_SESSION_FILE', ''))
    mode = path.lstat()
    if not stat.S_ISREG(mode.st_mode) or mode.st_uid != os.getuid() or mode.st_mode & 0o077:
        raise ValueError('IDE session descriptor must be a private file owned by this user')
    data = json.loads(path.read_text())
    if data.get('version') != PROTOCOL:
        raise ValueError('unsupported IDE control protocol')
    return data


def request(data, action='state', terminal=None, **arguments):
    port = data['port']
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError('invalid IDE port')
    # Refuse stale endpoints now owned by another OS user before disclosing
    # the session key. A same-user process can already read the descriptor.
    wanted = f'0100007F:{port:04X}'
    owner = None
    for line in Path('/proc/net/tcp').read_text().splitlines()[1:]:
        fields = line.split()
        if len(fields) > 7 and fields[1] == wanted and fields[3] == '0A':
            owner = int(fields[7])
            break
    if owner != os.getuid():
        raise ValueError('IDE session has no local listener owned by this user')
    payload = dict(version=PROTOCOL, session=data['session'], action=action,
                   terminal=terminal or os.environ.get('CODELOVESME_IDE_TERMINAL', ''), **arguments)
    req = urllib.request.Request(
        f'http://127.0.0.1:{port}/v1/control', data=json.dumps(payload).encode(),
        headers={'Authorization': 'Bearer ' + data['token'], 'Content-Type': 'application/json'},
    )
    # A localhost control request must never be sent through HTTP_PROXY.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=5) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = json.loads(exc.read()).get('error', str(exc))
        raise ValueError(detail) from exc
    if result.get('session') != data['session']:
        raise ValueError('IDE returned another session')
    return result


def context(data, terminal=None):
    state = request(data, terminal=terminal)
    terminal = terminal or os.environ.get('CODELOVESME_IDE_TERMINAL', '')
    if not any(pane['terminal'] == terminal for pane in state['terminals']):
        raise ValueError('originating IDE terminal is closed or does not exist')
    command = shlex.join(['python3', data['helper'], '--session-file', data['descriptor'],
                          '--terminal', terminal])
    return (f'You are running in a terminal of CodeLovesMe IDE (Integrated Development Environment). '
            f'IDE session: {state["session"]}. Originating terminal: {terminal}. '
            f'The IDE currently has project {state["project"]!r} open. '
            'The shell working directory may differ from the IDE project. '
            'For current layout use ide_state; to move your terminal use ide_move_terminal; '
            'to grow/shrink it use ide_resize_terminal. These tools target this IDE session. '
            'Re-read state after resuming; a closed session must not be replaced with another. '
            f'If MCP tools are unavailable, use the local command {command} followed by '
            'state, move --slot left|right|top|bottom|center, or resize --delta 2 (negative shrinks). '
            'Use the existing local terminal tool for that command if available. '
            'The session identifier is not a credential. Do not read or transmit the private session file.')


TOOLS = [
    {'name': 'ide_state', 'description': 'Read this CodeLovesMe IDE session and its terminal panes, slots and actual dimensions.',
     'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False}},
    {'name': 'ide_move_terminal', 'description': 'Move the originating terminal tab in this IDE, keeping its process alive.',
     'inputSchema': {'type': 'object', 'properties': {'slot': {'type': 'string', 'enum': ['left', 'right', 'top', 'bottom', 'center', 'tl', 'tr', 'bl', 'br']}}, 'required': ['slot'], 'additionalProperties': False}},
    {'name': 'ide_resize_terminal', 'description': 'Grow (positive delta) or shrink (negative delta) the terminal side track in columns or rows. Center cannot resize independently. Returns actual dimensions; shared tracks affect other panes on that track.',
     'inputSchema': {'type': 'object', 'properties': {'delta': {'type': 'integer', 'minimum': -20, 'maximum': 20}}, 'required': ['delta'], 'additionalProperties': False}},
]


def tool_call(data, name, arguments):
    if not isinstance(arguments, dict):
        raise ValueError('tool arguments must be an object')
    if name == 'ide_state' and not arguments:
        return request(data)
    if name == 'ide_move_terminal' and set(arguments) == {'slot'}:
        return request(data, 'move', slot=SLOTS.get(arguments['slot'], arguments['slot']))
    if name == 'ide_resize_terminal' and set(arguments) == {'delta'}:
        return request(data, 'resize', delta=arguments['delta'])
    raise ValueError('unknown tool or arguments')


def mcp(data):
    for raw in sys.stdin:
        response = None
        message = None
        try:
            message = json.loads(raw)
            if not isinstance(message, dict):
                raise ValueError('expected a JSON-RPC object')
            if 'id' not in message:
                continue
            method = message.get('method')
            if method == 'initialize':
                result = dict(protocolVersion=message.get('params', {}).get('protocolVersion', '2024-11-05'),
                              capabilities={'tools': {}}, serverInfo={'name': 'codelovesme-ide', 'version': '1.0.0'},
                              instructions=context(data))
            elif method == 'ping':
                result = {}
            elif method == 'tools/list':
                result = {'tools': TOOLS}
            elif method == 'tools/call':
                params = message.get('params', {})
                try:
                    value = tool_call(data, params.get('name'), params.get('arguments', {}))
                    result = {'content': [{'type': 'text', 'text': json.dumps(value)}]}
                except (ValueError, OSError, KeyError, TypeError) as exc:
                    result = {'isError': True, 'content': [{'type': 'text', 'text': str(exc)}]}
            else:
                response = {'jsonrpc': '2.0', 'id': message['id'], 'error': {'code': -32601, 'message': 'method not found'}}
                result = None
            if response is None:
                response = {'jsonrpc': '2.0', 'id': message['id'], 'result': result}
        except (ValueError, OSError, KeyError, TypeError) as exc:
            response = {'jsonrpc': '2.0', 'id': message.get('id') if isinstance(locals().get('message'), dict) else None,
                        'error': {'code': -32603, 'message': str(exc)}}
        print(json.dumps(response), flush=True)


def launch(name, args, data):
    entries = [p for p in os.get_exec_path() if not (Path(p) / '.codelovesme-ide-agents').is_file()]
    executable = shutil.which(name, path=os.pathsep.join(entries))
    if not executable:
        raise ValueError(f'{name} is not installed on PATH')
    if any(flag in args for flag in ('--help', '-h', '--version', '-V')):
        os.execv(executable, [executable, *args])
    if name == 'claude':
        instructions = context(data)
        config = {'mcpServers': {'codelovesme_ide': {'command': 'python3', 'args': [data['helper'], 'mcp'],
                  'env': {'CODELOVESME_IDE_SESSION_FILE': data['descriptor'],
                          'CODELOVESME_IDE_TERMINAL': os.environ.get('CODELOVESME_IDE_TERMINAL', '')}}}}
        extra = ['--append-system-prompt', instructions, '--mcp-config', json.dumps(config)]
    else:
        # Per-invocation MCP configuration preserves the user's instructions
        # and other servers. Its initialize instructions supply IDE context.
        extra = ['-c', 'mcp_servers.codelovesme_ide.command="python3"',
                 '-c', 'mcp_servers.codelovesme_ide.args=' + json.dumps([data['helper'], 'mcp']),
                 '-c', 'mcp_servers.codelovesme_ide.env.CODELOVESME_IDE_SESSION_FILE=' + json.dumps(data['descriptor']),
                 '-c', 'mcp_servers.codelovesme_ide.env.CODELOVESME_IDE_TERMINAL=' + json.dumps(os.environ.get('CODELOVESME_IDE_TERMINAL', ''))]
    os.execv(executable, [executable, *extra, *args])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session-file')
    parser.add_argument('--terminal')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('init')
    sub.add_parser('publish')
    sub.add_parser('cleanup')
    sub.add_parser('state')
    sub.add_parser('context')
    sub.add_parser('mcp')
    move = sub.add_parser('move')
    move.add_argument('--slot', required=True)
    resize = sub.add_parser('resize')
    resize.add_argument('--delta', type=int, required=True)
    agent = sub.add_parser('agent')
    agent.add_argument('name', choices=['claude', 'codex'])
    agent.add_argument('args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command == 'init':
        result = initialize()
    elif args.command == 'publish':
        data = json.load(sys.stdin)
        previous = descriptor(data['descriptor'])
        if previous['session'] != data['session'] or previous['token'] != data['token']:
            raise ValueError('session changed during initialization')
        write_private(Path(data['descriptor']), data)
        result = {'ok': True}
    else:
        data = descriptor(args.session_file)
        if args.command == 'cleanup':
            # Only remove the descriptor we own; leave no live launch adapters.
            Path(data['descriptor']).unlink(missing_ok=True)
            shutil.rmtree(data['bin'])
            Path(data['bashrc']).unlink(missing_ok=True)
            Path(data['descriptor']).parent.rmdir()
            result = {'ok': True}
        elif args.command == 'mcp':
            mcp(data)
            return
        elif args.command == 'agent':
            launch(args.name, args.args, data)
            return
        elif args.command == 'context':
            result = {'context': context(data, args.terminal)}
        else:
            arguments = {}
            if args.command == 'move': arguments['slot'] = SLOTS.get(args.slot, args.slot)
            if args.command == 'resize': arguments['delta'] = args.delta
            result = request(data, args.command, args.terminal, **arguments)
    print(json.dumps(result))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        print(f'ide-control: {error}', file=sys.stderr)
        sys.exit(1)
