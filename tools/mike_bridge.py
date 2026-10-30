#!/usr/bin/python3
"""JSON transport adapter for IDE → local Mike service. No agent/tool executor.

Input/reply/events are private IDE run files. stdout only wakes the IDE's
existing asynchronous pty reader; business data is structured JSON events.

`--login` is IDE account sign-in: the existing codelovesme browser handoff
(/desktop/connect, one-use state, token in a loopback POST body) and the
token handed straight to the shared service's attach. The IDE keeps only the
account name (`--account-file`, 0600); the token lives in this process only.

`--hear` is voice input: a WAV recording to the service's /v1/chat/hear (Mike's
Hear), the words written to `--result` (0600). Nothing is asked of Mike.
"""
import argparse
import base64
from http.server import BaseHTTPRequestHandler, HTTPServer
import importlib.util
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import sys
import threading
import time
from urllib.parse import parse_qs, urlencode, urlsplit
import webbrowser

PUBLIC_ORIGIN = 'https://apps.codeloves.me'
SIGN_IN = 'Settings → Account: Sign In'


def sdk():
    root = Path(__file__).resolve().parent
    candidates = [root / '.cdlvsm-deps/mike-service/client', root.parent / '.cdlvsm-deps/mike-service/client',
                  root.parent.parent / 'mike-desktop/client']
    if os.environ.get('MIKE_SERVICE_CLIENT_DIR'):
        candidates.insert(0, Path(os.environ['MIKE_SERVICE_CLIENT_DIR']))
    for directory in candidates:
        path = directory / 'mike_service.py'
        if path.is_file():
            spec = importlib.util.spec_from_file_location('mike_service', path)
            module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
            return module
    raise RuntimeError('Mike service client is absent; install the optional mike-service dependency')


def ide_account(path):
    """The account the IDE signed in as; '' when signed out of the IDE."""
    if not path: return ''
    try:
        fd = os.open(path, os.O_RDONLY|os.O_NOFOLLOW)
        with os.fdopen(fd) as opened: value = json.load(opened).get('account')
    except (OSError, ValueError, AttributeError): return ''
    return value if isinstance(value, str) else ''


def remember_account(path, account):
    temporary = path + '.new'
    try: os.unlink(temporary)
    except FileNotFoundError: pass
    fd = os.open(temporary, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as opened: json.dump({'account': account}, opened)
    os.replace(temporary, path)


def service_launcher():
    """The documented client search: named, CDLVSM-resolved, checkout, PATH."""
    root = Path(__file__).resolve().parent
    named = os.environ.get('MIKE_SERVICE_LAUNCHER')
    candidates = [Path(named)] if named else [root / '.cdlvsm-deps/mike-service/mike-service',
        root.parent / '.cdlvsm-deps/mike-service/mike-service', root.parent.parent / 'mike-desktop/bin/mike-service']
    found = shutil.which('mike-service')
    if not named and found: candidates.append(Path(found))
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK): return candidate
    return None


def start_service(module):
    """Start the intended installed service (user unit, else its launcher);
    never another executor. Truthful error when it is not installed."""
    if module.reachable(): return
    launcher = service_launcher()
    if launcher is None and not module.unit_installed():
        raise RuntimeError('Mike service is not installed; install it with: cdlvsm install ide --with mike')
    if not module.ensure_running(launcher or Path('mike-service')):
        raise RuntimeError('Mike service did not start; see ~/.local/state/mike-service/service.log')


def blocked(state, account):
    """Why this IDE account may not use the service now; '' when it may."""
    connection = state.get('connection')
    if not account: return 'Signed out of IDE; ' + SIGN_IN + ' with your codelovesme account'
    if connection == 'session_expired': return 'Your codelovesme session expired; ' + SIGN_IN + ' to refresh it'
    if connection in ('offline', 'gateway_unavailable'): return 'Mike is offline (gateway unreachable); try again when connected'
    if connection == 'revoked': return "This computer's Mike access was revoked; " + SIGN_IN + ' to connect it again'
    if connection != 'connected' or not state.get('account'): return 'The shared Mike service is signed out; ' + SIGN_IN
    if state['account'] != account:
        return ('The shared Mike service is signed in as ' + state['account'] + ', not your IDE account ' + account +
                '; sign in again, or use Account: Switch Shared Mike Service to move it explicitly')
    return ''


def attach(module, account_file=None):
    service = module.MikeService('ide', approvals=True)
    state = service.attach(None, connect='none')
    problem = blocked(state, ide_account(account_file))
    if problem:
        service.detach()
        raise RuntimeError(problem)
    if state.get('editor_version') != 1:
        service.detach()
        raise RuntimeError('Mike service lacks editor protocol 1; upgrade the shared service')
    return service, state


def trusted_host(host):
    if host == PUBLIC_ORIGIN: return True
    try: parts = urlsplit(host)
    except ValueError: return False
    return parts.scheme == 'http' and parts.hostname in ('127.0.0.1', 'localhost') and parts.port is not None and parts.path in ('', '/')


def browser_handoff(origin, timeout):
    """The existing /desktop/connect handoff. Returns the token or None."""
    expected = secrets.token_urlsafe(32); got = {}; arrived = threading.Event()

    class Callback(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != '/callback' or self.headers.get('Origin') not in (origin, 'null') or arrived.is_set():
                self.send_error(403); return
            try: length = int(self.headers.get('Content-Length', '0'))
            except ValueError: length = 0
            if not 0 < length <= 4096: self.send_error(400); return
            try: fields = parse_qs(self.rfile.read(length).decode('utf-8'), strict_parsing=True)
            except (UnicodeDecodeError, ValueError): self.send_error(400); return
            state = fields.get('state', [''])[0]; token = fields.get('token', [''])[0]
            if not secrets.compare_digest(state, expected) or not token: self.send_error(403); return
            got['token'] = token; arrived.set()
            page = b'<!doctype html><title>IDE connected</title><p>You are signed in. You can return to the IDE.</p>'
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Security-Policy', "default-src 'none'")
            self.send_header('Content-Length', str(len(page))); self.end_headers(); self.wfile.write(page)

        def log_message(self, *_args): pass

    server = HTTPServer(('127.0.0.1', 0), Callback)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = origin + '/desktop/connect?' + urlencode({'port': server.server_port, 'state': expected, 'app': 'IDE'})
        print('Finish signing in to codelovesme in your browser', flush=True)
        if not webbrowser.open(url): raise RuntimeError('No browser could be opened for sign-in')
        arrived.wait(timeout)
        return got.get('token')
    finally:
        server.shutdown(); server.server_close()


LOGIN_ERRORS = {
    'account_refused': ('refused', 'codelovesme refused the sign-in (expired or invalid); ' + SIGN_IN + ' again'),
    'connect_required': ('revoked', "This computer's Mike access was revoked; use Account: Switch Shared Mike Service to connect it again"),
    'gateway_unavailable': ('offline', 'Mike gateway is unreachable; IDE stays signed out; try again when connected'),
}


def login(module, account_file, switch, timeout):
    """IDE account sign-in. `auto` signs a signed-out service in or refreshes
    the same account; a different account is refused unless `switch` (an
    explicit person's choice). No grants or approvals are given."""
    start_service(module)
    observer = module.MikeService('ide-sign-in', approvals=False)
    before = observer.attach(None, connect='none'); observer.detach()
    origin = str(before.get('host') or '').rstrip('/')
    if not trusted_host(origin): raise RuntimeError('Mike service host is not a codelovesme origin: ' + origin[:80])
    token = browser_handoff(origin, timeout)
    if not token:
        return {'signed_in': False, 'error': 'cancelled', 'note': 'Sign-in was cancelled or timed out; nothing changed'}
    connector = module.MikeService('ide-sign-in', approvals=False)
    try:
        state = connector.attach(token, connect='switch' if switch else 'auto')
    except module.ServiceError as error:
        token = None
        if error.error == 'account_mismatch':
            return {'signed_in': False, 'error': 'account_mismatch', 'note': 'Not switched: shared Mike uses ' +
                    str(before.get('account') or 'another account') + ' (Account: Switch Shared Mike Service moves it)'}
        kind, note = LOGIN_ERRORS.get(error.error, ('failed', 'Sign-in failed: ' + error.error))
        return {'signed_in': False, 'error': kind, 'note': note}
    finally:
        token = None; connector.detach()
    account = state.get('account') or ''
    if not account: return {'signed_in': False, 'error': 'failed', 'note': 'The service did not report an account'}
    remember_account(account_file, account)
    return {'signed_in': True, 'account': account, 'note': 'Signed in as ' + account}


# The service takes up to 4,000,000 base64 characters: about a minute of
# 16 kHz mono WAV.
HEAR_MOST_BYTES = 3_000_000

HEAR_ERRORS = {
    'unknown_route': 'The shared Mike service is too old to hear; upgrade it (cdlvsm upgrade mike-service)',
    'too_large': 'The recording is too long for Mike; keep it under a minute',
    'signed_out': 'The shared Mike service is signed out; ' + SIGN_IN,
    'mike_unavailable': 'Mike could not make out the recording',
}


def hear(module, wav, account_file):
    """A recording as words through the shared service, for this IDE account."""
    audio = Path(wav).read_bytes()
    if len(audio) > HEAR_MOST_BYTES:
        return {'error': 'too_large', 'note': HEAR_ERRORS['too_large']}
    start_service(module)
    service, _ = attach(module, account_file)
    try:
        answer = service.call('/v1/chat/hear', {'audio_base64': base64.b64encode(audio).decode('ascii'), 'format': 'wav'}, timeout=45)
    except module.ServiceError as error:
        return {'error': error.error, 'note': HEAR_ERRORS.get(error.error, 'Mike could not hear it: ' + error.error)}
    finally:
        service.detach()
    text = answer.get('text') if isinstance(answer, dict) else None
    if not isinstance(text, str): return {'error': 'failed', 'note': 'Mike answered without words'}
    return {'text': text}


def write_private(path, value):
    fd = os.open(path, os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as opened: json.dump(value, opened)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--request'); parser.add_argument('--events'); parser.add_argument('--reply')
    parser.add_argument('--account-file'); parser.add_argument('--login', action='store_true')
    parser.add_argument('--switch', action='store_true'); parser.add_argument('--result')
    parser.add_argument('--timeout', type=float, default=300)
    parser.add_argument('--hear')
    args = parser.parse_args()
    if args.hear:
        if not args.account_file or not args.result: parser.error('--hear needs --account-file and --result')
        try: outcome = hear(sdk(), args.hear, args.account_file)
        except Exception as error: outcome = {'error': 'unavailable', 'note': str(error)[:300]}
        write_private(args.result, outcome)
        print('done', flush=True)
        return 0 if 'text' in outcome else 1
    if args.login:
        if not args.account_file or not args.result: parser.error('--login needs --account-file and --result')
        try: outcome = login(sdk(), args.account_file, args.switch, args.timeout)
        except Exception as error: outcome = {'signed_in': False, 'error': 'unavailable', 'note': str(error)[:300]}
        fd = os.open(args.result, os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w') as opened: json.dump(outcome, opened)
        print('done', flush=True)
        return 0 if outcome['signed_in'] else 1
    service = None; turn = ''; events = None
    try:
        if not args.check:
            if not args.request or not args.events or not args.reply: parser.error('request/events/reply required')
            # Opened first, so sign-in/service problems reach the chat as events.
            fd = os.open(args.events, os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW, 0o600)
            events = os.fdopen(fd,'w')
        module = sdk()
        if not args.check: start_service(module)
        service, initial = attach(module, args.account_file)
        if args.check:
            print(json.dumps({'ready':True,'note':'ready · '+initial['account']})); return 0
        request = json.loads(Path(args.request).read_text())
        def emit(kind, **data):
            events.write(json.dumps({'kind':kind,**data})+'\n');events.flush()
            print('event',flush=True)
        turn = service.call('/v1/chat/ask',request)['turn_id']
        emit('started',turn_id=turn,account=initial['account'])
        seen = None; reply_seen = ''; deadline = time.monotonic()+3600
        while time.monotonic()<deadline:
            state = service.state()
            if state['account'] != initial['account'] or ide_account(args.account_file) != initial['account']:
                raise RuntimeError('Mike account changed; old editor connection ended')
            view = service.call('/v1/chat/progress',{'turn_id':turn})
            if view != seen: emit('progress',view=view);seen=view
            if view['stage'] in ('done','failed'): return 0 if view['stage']=='done' else 1
            try: reply = json.loads(Path(args.reply).read_text())
            except (OSError,ValueError): reply = None
            if isinstance(reply,dict) and reply.get('turn_id')==turn and reply.get('id') != reply_seen:
                # Consume before forwarding; never rerun an edit after a lost ACK.
                reply_seen = reply.get('id')
                if reply.get('kind')=='confirm':
                    service.call('/v1/chat/confirm',{'turn_id':turn,'confirmation_id':reply.get('id'),'yes':reply.get('yes') is True})
                elif reply.get('kind')=='editor':
                    service.call('/v1/editor/result',{'turn_id':turn,'id':reply['id'],'result':reply.get('result')})
            work=state.get('work')
            if work and work.get('id')==view.get('work_id') and work.get('approval_id'):
                emit('local',work=work)
                if isinstance(reply,dict) and reply.get('kind')=='local' and reply.get('id')==work['approval_id']:
                    service.claim(work['approval_id'])
                    service.answer(work['approval_id'],'approve' if reply.get('yes') is True else 'decline')
            time.sleep(0.5)
        raise RuntimeError('Editor connection timed out; no editor operation was replayed')
    except (Exception,KeyboardInterrupt) as error:
        message=str(error)[:500]
        if args.check: print(json.dumps({'ready':False,'note':message}));return 1
        if events:
            reset = getattr(error,'error','') in ('session_ended','account_changed','signed_out') or 'account changed' in message.lower()
            events.write(json.dumps({'kind':'error','text':message,'reset':reset})+'\n');events.flush();print('event',flush=True)
        else: print(message,file=sys.stderr)
        return 1
    finally:
        if service:
            service.detach()
        if events: events.close()


if __name__=='__main__':
    signal.signal(signal.SIGTERM,lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    sys.exit(main())
