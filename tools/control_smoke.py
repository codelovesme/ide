"""Exercise the real IDE event loop, terminal environment and MCP transport.

python3 tools/control_smoke.py <bundle>/ide
Without an argument, use the release-pinned Code interpreter on main.code.
"""
import concurrent.futures
import json
import io
import time
from unittest.mock import patch
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

from drive import Session
from ide_control import descriptor, request as direct_request

APP = Path(__file__).resolve().parents[1]
HELPER = APP / 'tools/ide_control.py'
CODE = Path.home() / '.local/share/cdlvsm/packages/code/v2.14.5/code'


def run():
    with tempfile.TemporaryDirectory(prefix='ide-control-smoke-') as temp:
        root = Path(temp)
        sessions = []
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        def serviced(function, *args, **kwargs):
            future = executor.submit(function, *args, **kwargs)
            while not future.done():
                for session in sessions:
                    if session.exit is None:
                        session.pump(.03)
            return future.result()
        def request(*args, **kwargs):
            return serviced(direct_request, *args, **kwargs)
        try:
            def start(name):
                folder = root / name
                folder.mkdir()
                (folder / 'notes.md').write_text('keep this file\n')
                config = root / (name + '-config')
                config.mkdir()
                argv = [str(Path(sys.argv[1]).resolve()), str(folder)] if len(sys.argv) > 1 else [str(CODE), 'run', 'main.code']
                s = Session(argv, str(APP), {'IDE_FOLDER': str(folder), 'XDG_CONFIG_HOME': str(config)})
                sessions.append(s)
                assert s.wait_for('Explorer', 30), s.screen.text()
                assert 'control unavailable' not in s.screen.text(), s.screen.text()
                s.keys(b'\r', .4)  # keep an editor in the center
                s.keys(b'\x00', 1)
                out = folder / 'session-path'
                s.keys(('printf "%s" "$CODELOVESME_IDE_SESSION_FILE" > ' + str(out) + '\r').encode(), .7)
                assert out.exists() and out.read_text(), s.screen.text()
                data = descriptor(out.read_text())
                launcher = folder / 'launcher-path'
                s.keys(('command -v claude > ' + str(launcher) + '\r').encode(), .4)
                assert launcher.read_text().strip() == str(Path(data['bin']) / 'claude')
                return s, data, folder

            one, data, folder = start('one')
            two, other, _ = start('two')
            assert data['session'] != other['session']
            state = request(data)
            assert state['project'] == str(folder)
            assert state['terminals'][0]['terminal'] == 'terminal-1'
            assert state['terminals'][0]['slot'] == 'r'
            print('ok   distinct IDE identities and terminal environment')
            # Same backend port, valid credential, wrong identity must still fail.
            try:
                request(dict(data, session=other['session']))
                raise AssertionError('another session accepted')
            except ValueError as exc:
                assert 'session' in str(exc)
            req = urllib.request.Request(f'http://127.0.0.1:{data["port"]}/v1/control', data=b'{}')
            try:
                urllib.request.urlopen(req, timeout=5)
                raise AssertionError('unauthenticated request accepted')
            except urllib.error.HTTPError as exc:
                assert exc.code == 401
            print('ok   authentication and session mismatch rejection')
            for slot in ('l', 'b', 'r'):
                moved = request(data, 'move', 'terminal-1', slot=slot)
                assert moved['terminals'][0]['slot'] == slot
                one.pump(.4)
                assert 'Terminal 1' in one.screen.text()
            initial = request(data)['terminals'][0]['bounds']['width']
            grown = request(data, 'resize', 'terminal-1', delta=4)
            assert grown['terminals'][0]['bounds']['width'] == initial + 4
            smaller = request(data, 'resize', 'terminal-1', delta=-4)
            assert smaller['terminals'][0]['bounds']['width'] == initial
            assert request(other)['terminals'][0]['slot'] == 'r'
            print('ok   move left/bottom/right and resize target only; rendered terminal survives')
            for arguments in (dict(action='move', terminal='missing', slot='l'),
                              dict(action='resize', terminal='terminal-1', delta=1.5),
                              dict(action='resize', terminal='terminal-1', delta=True),
                              dict(action='move', terminal='terminal-1', slot='nowhere')):
                try:
                    request(data, **arguments)
                    raise AssertionError('invalid arguments accepted')
                except ValueError:
                    pass
            assert request(data)['terminals'][0]['slot'] == 'r'
            print('ok   invalid or closed targets cannot mutate layout')
            # The shell process receives real dimensions, not just new metadata.
            one.pump(.5)
            dimensions = folder / 'dimensions'
            one.keys(('stty size > ' + str(dimensions) + '\r').encode(), .7)
            expected = request(data)['terminals'][0]['bounds']
            assert dimensions.read_text().strip() == f'{expected["height"] - 1} {expected["width"] - 1}'
            print('ok   live PTY dimensions match the resized pane')
            env = dict(os.environ, CODELOVESME_IDE_SESSION_FILE=data['descriptor'], CODELOVESME_IDE_TERMINAL='terminal-1')
            messages = [
                {'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05'}},
                {'jsonrpc':'2.0','method':'notifications/initialized'},
                {'jsonrpc':'2.0','id':2,'method':'tools/list'},
                {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'ide_move_terminal','arguments':{'slot':'bottom'}}},
                {'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'ide_resize_terminal','arguments':{'delta':2}}},
            ]
            result = serviced(subprocess.run, ['python3', str(HELPER), 'mcp'], input=''.join(json.dumps(x)+'\n' for x in messages), text=True, capture_output=True, env=env, timeout=20)
            assert result.returncode == 0, result.stderr
            replies = [json.loads(line) for line in result.stdout.splitlines()]
            assert len(replies) == 4, replies
            assert data['session'] in replies[0]['result']['instructions']
            assert len(replies[1]['result']['tools']) == 3
            assert json.loads(replies[2]['result']['content'][0]['text'])['terminals'][0]['slot'] == 'b'
            assert not replies[3]['result'].get('isError'), replies[3]
            assert data['token'] not in result.stdout
            print('ok   MCP initializes with context and tools move/resize the real IDE')
            # Exercise actual launch adapters with fake CLI executables; their
            # output contains argv only, never credentials or model requests.
            fake = root / 'fake'
            fake.mkdir()
            for name in ('claude','codex'):
                executable = fake / name
                executable.write_text('#!/usr/bin/python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n')
                executable.chmod(0o700)
                launch_env = dict(env, PATH=data['bin']+':'+str(fake)+':'+os.environ['PATH'])
                result = serviced(subprocess.run, [str(Path(data['bin']) / name), 'hello'], env=launch_env, capture_output=True, text=True, timeout=10)
                assert result.returncode == 0, result.stderr
                assert 'codelovesme_ide' in result.stdout and 'hello' in result.stdout
                assert data['token'] not in result.stdout
            print('ok   ordinary claude/codex commands receive per-session MCP configuration')
            if os.environ.get('IDE_TEST_AGENTS') == '1':
                agent_env = dict(env, PATH=data['bin']+':'+os.environ['PATH'])
                prompt = ('Use only the codelovesme_ide MCP tools. Read the IDE state, '
                          'move terminal-1 to the left, grow it by 4, shrink it by 2, '
                          'then move it to the bottom, grow it by 2 and shrink it by 2. '
                          'Finally move it to the right. '
                          'Read the state again and reply with the IDE session id and terminal slot. '
                          'Do not run shell commands, inspect files, or modify source code.')
                for name, flags in [('codex', ['exec', '--skip-git-repo-check', prompt]),
                                    ('claude', ['-p', '--tools', '', '--permission-mode', 'dontAsk',
                                                '--allowedTools', 'mcp__codelovesme_ide__ide_state,mcp__codelovesme_ide__ide_move_terminal,mcp__codelovesme_ide__ide_resize_terminal',
                                                '--', prompt])]:
                    before_left = request(data)['sizes']['left']
                    completed = serviced(subprocess.run, [str(Path(data['bin']) / name), *flags],
                                          env=agent_env, cwd=str(folder), text=True,
                                          capture_output=True, timeout=240)
                    # Only the final summary is logged, never the descriptor.
                    assert completed.returncode == 0, name + ': ' + completed.stderr[-2000:]
                    assert data['session'] in completed.stdout, name + ': ' + completed.stdout[-2000:]
                    assert request(data)['terminals'][0]['slot'] == 'r'
                    assert request(data)['sizes']['left'] == before_left + 2
                    assert data['token'] not in completed.stdout + completed.stderr
                    print('ok   real ' + name + ' knows its IDE session and calls layout tools')
            if os.environ.get('IDE_TEST_MIKE') == '1':
                sys.path.insert(0, os.environ.get('IDE_MIKE_CLIENT_DIR', str(APP.parent / 'mike-desktop-cli/client')))
                from cli import Terminal
                from mike_service import MikeService
                client = MikeService('ide-control-smoke', approvals=True)
                output = io.StringIO()
                terminal = Terminal(client, str(folder), True, output)
                previous = request(data)['sizes']['left']
                prefix = ['python3', data['helper'], '--session-file', data['descriptor'], '--terminal', 'terminal-1']
                commands = [prefix+['state'], prefix+['move','--slot','left'], prefix+['resize','--delta','4'], prefix+['resize','--delta','-2'], prefix+['move','--slot','bottom'], prefix+['resize','--delta','2'], prefix+['resize','--delta','-2'], prefix+['move','--slot','right']]
                try:
                    with patch.dict(os.environ, dict(env, CODELOVESME_IDE_HELPER=data['helper'])):
                        serviced(terminal.attach)
                        serviced(terminal.ask, 'Test my enclosing IDE control. Use your local terminal tool to run these exact argument arrays in order, on this computer, in the supplied project directory: '
                                 +json.dumps(commands)+'. Do not run other commands or edit files. Finish by reporting the IDE session id. I authorize these reversible panel movements and resizing.')
                        deadline = time.monotonic()+300
                        while not terminal.finished and time.monotonic()<deadline:
                            serviced(terminal.poll)
                            if terminal.view.get('stage') == 'confirm':
                                serviced(terminal.command, '/yes '+terminal.view['confirmation_id'])
                            if terminal.local:
                                work = terminal.local
                                argv = work.get('argv', [])
                                normalized = ['python3', *argv[1:]] if argv and argv[0] == '/usr/bin/python3' else argv
                                if normalized not in commands or work.get('kind') != 'terminal':
                                    serviced(terminal.command, '/decline '+work['approval_id'])
                                    raise AssertionError('Mike requested a command outside the IDE smoke test')
                                serviced(terminal.command, '/approve '+work['approval_id'])
                            time.sleep(.2)
                        assert terminal.finished, 'Mike IDE turn timed out'
                        assert terminal.view.get('stage') == 'done', output.getvalue()[-1500:]
                        assert request(data)['terminals'][0]['slot'] == 'r'
                        assert request(data)['sizes']['left'] == previous+2, output.getvalue()[-1500:]
                        assert data['token'] not in output.getvalue()
                        print('ok   real Mike CLI/model/service controls its IDE using approved local commands')
                finally:
                    client.detach()
            request(data, 'move', 'terminal-1', slot='r')
            one.keys(b'\x14', .8)  # Ctrl+T: a second terminal takes focus
            panes = request(data)['terminals']
            assert {p['terminal'] for p in panes} == {'terminal-1', 'terminal-2'}
            changed = request(data, 'move', 'terminal-1', slot='l')
            assert next(p for p in changed['terminals'] if p['terminal'] == 'terminal-1')['slot'] == 'l'
            assert next(p for p in changed['terminals'] if p['terminal'] == 'terminal-2')['slot'] == 'r'
            print('ok   originating terminal is targeted even while a different terminal has focus')
            one.keys(b'\x11', .8)
            if one.exit is None: one.pump(3)
            assert one.exit == 0, f'exit={one.exit}\n' + one.screen.text()
            assert not Path(data['descriptor']).exists()
            try:
                request(data)
                raise AssertionError('closed IDE still answering')
            except (OSError, ValueError):
                pass
            assert request(other)['session'] == other['session']
            print('ok   closing an IDE removes its credentials and leaves other instances working')
        finally:
            for s in sessions:
                if s.exit is None:
                    s.keys(b'\x11', .5)
                os.close(s.fd)
            executor.shutdown()


if __name__ == '__main__':
    run()
