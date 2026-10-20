#!/usr/bin/python3
"""Ticket 168: fresh installed-style IDE + shared service, normal browser sign-in → Mike.

A CDLVSM-shaped install (`IDE_PACKAGES`: packages/ide/<v> with
.cdlvsm-deps/mike-service → packages/mike-service/<v>, packages/code/current)
runs under a scratch HOME with no systemd user bus, no Desktop, no CLI and no
token in the environment. The person's browser steps run in a real Chromium
(tools/browser-login.mjs) on the scratch stack's own /desktop/connect page.
Uses my-euglena-apps/tools/mike-scratch-stack.py; changes nothing installed.
"""
import json
import os
from pathlib import Path
import runpy
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
MIKE = ROOT.parent / 'mike-desktop'
APPS = ROOT.parent / 'my-euglena-apps'
STACK = Path(os.environ.get('STACK_DIR', '/var/tmp/m168/stack'))
PACKAGES = Path(os.environ['IDE_PACKAGES'])
BUNDLE = PACKAGES / 'ide' / os.environ.get('IDE_VERSION', 'dev')
stack = json.loads((STACK / 'stack.json').read_text())
PHASE = os.environ.get('E2E_PHASE', 'main')  # main | expiry (needs a stack up with --token-seconds)
os.environ['STACK_DIR'] = str(STACK)
headless = runpy.run_path(str(MIKE / 'tools/headless-e2e.py'))
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(BUNDLE / '.cdlvsm-deps/mike-service/client'))
from drive import Session  # noqa: E402
import mike_service  # noqa: E402

checks = 0
screen = None
PLAYWRIGHT = str(APPS / 'tools/browser/node_modules/playwright/index.mjs')
ALT_S = b'\x1bs'
DOWN = b'\x1b[B'


def check(value, label):
    global checks
    if not value and screen:
        print(screen.screen.text()[-4000:], flush=True)
    assert value, label
    checks += 1
    print('PASS ' + label, flush=True)


def menu(index):
    """Settings menu item: 7 Sign In, 8 Sign Out, 9 Switch Shared Mike Service."""
    screen.keys(ALT_S, 0.5)
    for _ in range(index):
        screen.keys(DOWN, 0.1)
    screen.keys(b'\r', 0.8)


def chat():
    """Ctrl+L opens and focuses the AI Chat, or closes it when focused."""
    screen.keys(b'\x0c', 0.8)
    if 'shared local service' not in screen.screen.text():
        screen.keys(b'\x0c', 0.8)


def until(probe, seconds, every=1.0):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            if probe():
                return True
        except Exception:
            pass
        screen.pump(every)
    return False


def opened_url(area, previous=''):
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        screen.pump(0.3)
        record = area / 'opened.txt'
        if record.exists():
            url = record.read_text().strip().splitlines()[-1]
            if url != previous:
                return url
    raise AssertionError('IDE did not open the browser')


def browser(url, email, action='connect'):
    done = subprocess.run(['node', str(ROOT / 'tools/browser-login.mjs'),
                           json.dumps({'url': url, 'email': email, 'password': headless['PASSWORD'], 'action': action})],
                          env=dict(os.environ, PLAYWRIGHT=PLAYWRIGHT), capture_output=True, text=True, timeout=180)
    try:
        return json.loads(done.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {'ok': False, 'error': (done.stdout + done.stderr)[-800:]}


def processes():
    names = []
    for entry in Path('/proc').iterdir():
        if entry.name.isdigit():
            try:
                names.append((entry / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace'))
            except OSError:
                pass
    return names


with tempfile.TemporaryDirectory(prefix='ide-login-e2e-') as temporary:
    area = Path(temporary)
    home = area / 'home'
    runtime = area / 'run'
    project = area / 'project'
    for directory in (home, runtime, project):
        directory.mkdir(mode=0o700)
    target = project / 'a.code'
    target.write_text('disk-value\n')
    config = home / '.config/codelovesme-ide'
    config.mkdir(parents=True)
    (config / 'settings.json').write_text(json.dumps({'ai.provider': 'mike', 'ai.agent.mode': 'edit'}))
    recorder = area / 'browser.sh'
    recorder.write_text('#!/bin/sh\nprintf "%s\\n" "$1" >> ' + str(area / 'opened.txt') + '\n')
    recorder.chmod(0o700)
    relay = headless['Relay'](int(stack['web'].rsplit(':', 1)[1]))  # the gateway, as the service reaches it
    keep = {k: v for k, v in os.environ.items() if k in ('LANG', 'LC_ALL', 'USER', 'LOGNAME')}
    env = dict(keep, HOME=str(home), XDG_CONFIG_HOME=str(home / '.config'), XDG_RUNTIME_DIR=str(runtime),
               PATH='/usr/bin:/bin', TERM='xterm-256color', BROWSER=str(recorder),
               MIKE_SERVICE_HOST_URL=f'http://127.0.0.1:{relay.port}')
    service_env = dict(env)  # what the IDE's own processes see; used for the observer below
    observer = None
    email, _ = headless['account']('ide168')    # account exists; its API token is not used
    other, _ = headless['account']('ide168b')
    try:
        check('MIKE_IDE_TOKEN' not in env and 'DBUS_SESSION_BUS_ADDRESS' not in env, 'no token or user bus in the IDE environment')
        screen = Session([str(BUNDLE / 'ide'), str(project)], str(project), env)
        check(screen.wait_for('Explorer', 30), 'installed-style IDE starts on a scratch project')
        screen.keys(b'\r', 1)
        check(screen.wait_for('a.code', 10), 'file opens')
        screen.keys(b'UNSAVED-', 0.6)
        check('UNSAVED-disk-value' in screen.screen.text(), 'unsaved edit in the buffer')

        chat()  # the native AI Chat
        screen.keys(b'hello\r', 1)
        check(screen.wait_for('Signed out of IDE', 60), 'before sign-in Mike says the IDE is signed out (installed service started on request)')
        os.environ['MIKE_SERVICE_RUNTIME_DIR'] = str(runtime / 'mike-service')
        check(mike_service.reachable(), 'the installed service is running in the scratch runtime directory')

        menu(7)
        first = opened_url(area)
        check('/desktop/connect?' in first and 'app=IDE' in first and 'token' not in first, 'IDE opens the existing /desktop/connect handoff')
        left = browser(first, email, 'leave')
        check(left.get('ok'), 'person signs in in the browser but does not connect: ' + str(left.get('error', '')))
        menu(7)
        check(screen.wait_for('Sign-in cancelled', 10), 'sign-in can be cancelled; nothing changed')
        check(not (config / 'account.json').exists(), 'no account recorded after cancellation')

        menu(7)
        second = opened_url(area, first)
        connected = browser(second, email)
        check(connected.get('ok') and connected.get('token_in_url') is False, 'normal browser login + Connect: ' + str(connected))
        check(screen.wait_for('Signed in as ' + email, 30), 'IDE shows the signed-in account')
        check(json.loads((config / 'account.json').read_text()) == {'account': email}, 'IDE keeps only the account name')
        check(oct((config / 'account.json').stat().st_mode & 0o777) == '0o600', 'account record is private')

        if PHASE == 'expiry':
            # Stack started with --token-seconds: the account session runs out.
            observer = mike_service.MikeService('ide168-observer', approvals=False)
            observer.attach(None, 'none')
            check(until(lambda: observer.state().get('connection') == 'session_expired', 300, 5), 'service reports the session expired')
            chat()
            screen.keys(b'after expiry\r', 1)
            check(screen.wait_for('session expired', 30), 'expiry is explicit in IDE')
            menu(7)
            again = opened_url(area, second)
            check(browser(again, email).get('ok'), 'browser login again after expiry')
            check(screen.wait_for('Signed in as ' + email, 30), 'same-account sign-in refreshes the expired session')
            check(until(lambda: observer.state().get('connection') == 'connected', 90), 'service connected with the fresh session')
        else:
            chat()
            question = ('In the active a.code use ReadBuffer and EditBuffer to replace disk-value with done, preserving the UNSAVED- prefix. '
                        'Use save=false (buffer only). Do not use terminal commands. Finish with IDE168DONE.')
            screen.keys(question.encode() + b'\r', 1)
            check(screen.wait_for('Mike proposes a change', 240), 'Mike answers through the shared service with live editor tools')
            check(target.read_text() == 'disk-value\n', 'proposal has not changed disk')
            screen.keys(b'a', 1)
            check(screen.wait_for('IDE168DONE', 180), 'diff acceptance returns to Mike, which finishes')
            check('UNSAVED-done' in screen.screen.text(), 'the IDE buffer holds the change; unsaved work kept')
            check(target.read_text() == 'disk-value\n', 'buffer-only change not saved to disk')

            # A different account is refused, never switched silently.
            menu(7)
            third = opened_url(area, second)
            check(browser(third, other).get('ok'), 'browser login as a second account')
            check(screen.wait_for('Not switched: shared Mike uses ' + email, 30), 'a different account is refused explicitly')
            observer = mike_service.MikeService('ide168-observer', approvals=False)
            check(observer.attach(None, 'none').get('account') == email, 'shared service stays on the first account')
            check(json.loads((config / 'account.json').read_text()) == {'account': email}, 'IDE account unchanged')

            # Signing in again as the same account refreshes the service's session.
            menu(7)
            fourth = opened_url(area, third)
            check(browser(fourth, email).get('ok'), 'browser login again as the same account')
            check(screen.wait_for('Signed in as ' + email, 30), 'same-account sign-in refreshes, no switch')
            check(observer.state().get('account') == email, 'other client kept across the refresh')

            # Gateway offline: the service says so, IDE keeps its account, nothing switches.
            relay.cut()
            check(until(lambda: observer.state().get('connection') == 'offline', 120), 'service sees the gateway offline')
            chat()
            screen.keys(b'while offline\r', 1)
            check(screen.wait_for('Mike is offline', 30), 'offline is an explicit state in IDE')
            relay.restore()
            check(until(lambda: observer.state().get('connection') == 'connected', 120), 'service reconnects by itself')
            check(json.loads((config / 'account.json').read_text()) == {'account': email}, 'IDE account kept while offline')

            # The explicit switch moves the shared service; old sessions end.
            menu(9)
            fifth = opened_url(area, fourth)
            check(browser(fifth, other).get('ok'), 'browser login as the second account for an explicit switch')
            check(screen.wait_for('Signed in as ' + other, 30), 'explicit switch signs IDE in as the second account')
            try:
                observer.state(); ended = ''
            except mike_service.ServiceError as error:
                ended = error.error + ' ' + str(error.body.get('reason', ''))
            check('account_changed' in ended or 'session_ended' in ended, 'old-account sessions end on the switch: ' + ended)
            observer = mike_service.MikeService('ide168-observer', approvals=False)
            check(observer.attach(None, 'none').get('account') == other, 'shared service now on the second account')

            # Revoked access: explicit state; plain sign-in refuses, the switch reconnects.
            observer.revoke()
            observer = mike_service.MikeService('ide168-observer', approvals=False)
            check(until(lambda: observer.attach(None, 'none').get('connection') in ('revoked', 'signed_out'), 30), 'device revoked')
            chat()
            screen.keys(b'after revoke\r', 1)
            check(screen.wait_for('revoked', 30) or screen.wait_for('service is signed out', 5), 'revoked access is explicit in IDE')
            menu(7)
            sixth = opened_url(area, fifth)
            check(browser(sixth, other).get('ok'), 'browser login after revocation')
            check(screen.wait_for('access was revoked; use Account: Switch', 30), 'plain sign-in does not re-pair silently')
            menu(9)
            seventh = opened_url(area, sixth)
            check(browser(seventh, other).get('ok'), 'browser login for the explicit reconnect')
            check(screen.wait_for('Signed in as ' + other, 30), 'explicit switch reconnects the computer')
            observer = mike_service.MikeService('ide168-observer', approvals=False)
            check(observer.attach(None, 'none').get('connection') == 'connected', 'service connected again')

            # IDE-local sign-out leaves the service and its other clients alone.
            menu(8)
            check(screen.wait_for('Signed out of IDE. The shared Mike service', 10), 'IDE-local sign-out')
            check(observer.state().get('account') == other, 'other client still attached and signed in')
            chat()
            screen.keys(b'after sign-out\r', 1)
            check(screen.wait_for('Signed out of IDE;', 30), 'after sign-out Mike is blocked in the IDE')

            tree = ''.join(p.read_text(errors='replace') for p in config.rglob('*') if p.is_file())
            check('eyJ' not in tree, 'no session token in IDE settings, account or run files')
            check(not any('eyJ' in line for line in processes()), 'no session token in any process argv')
            mine = [line for line in processes() if str(area) in line or str(PACKAGES) in line]
            check(not any('mike-desktop' in line or 'mike-cli' in line or 'desktop_webview' in line for line in mine),
                  'no Mike Desktop or CLI process')
            check(sum(1 for line in mine if 'service/main.code' in line or 'mike-service run' in line) <= 1, 'one shared service, no second executor')
        screen.keys(b'\x11', 0.3)  # Ctrl+Q; refuse the unsaved prompt
        screen.keys(b'n', 0.3)
    finally:
        if screen:
            try:
                os.kill(screen.pid, signal.SIGTERM)
                screen.pump(0.3)
            except (ProcessLookupError, ChildProcessError):
                pass
            os.close(screen.fd)
        if observer:
            try:
                print('scratch device revoked:', observer.revoke().get('revoked'))
            except Exception as error:  # cleanup only; the stack's databases are dropped anyway
                print('scratch device not revoked:', error)
            observer.detach()
        subprocess.run([str(BUNDLE / '.cdlvsm-deps/mike-service/mike-service'), 'stop'], env=service_env,
                       capture_output=True, timeout=60)
print(f'{checks} real IDE sign-in integration checks passed')
