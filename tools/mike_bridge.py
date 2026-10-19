#!/usr/bin/python3
"""JSON transport adapter for IDE → local Mike service. No agent/tool executor.

Input/reply/events are private IDE run files. stdout only wakes the IDE's
existing asynchronous pty reader; business data is structured JSON events.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time


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


def attach(module):
    service = module.MikeService('ide', approvals=True)
    token = os.environ.get('MIKE_IDE_TOKEN')
    state = service.attach(token, connect='auto' if token else 'none')
    if state.get('connection') != 'connected':
        service.detach()
        raise RuntimeError('Mike is not signed in/online; connect the shared service or provide MIKE_IDE_TOKEN in a protected environment')
    if state.get('editor_version') != 1:
        service.detach()
        raise RuntimeError('Mike service lacks editor protocol 1; upgrade the shared service')
    return service, state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--request'); parser.add_argument('--events'); parser.add_argument('--reply')
    args = parser.parse_args()
    service = None; turn = ''; events = None
    try:
        module = sdk()
        service, initial = attach(module)
        if args.check:
            print(json.dumps({'ready':True,'note':'ready · '+initial['account']})); return 0
        if not args.request or not args.events or not args.reply: parser.error('request/events/reply required')
        request = json.loads(Path(args.request).read_text())
        fd = os.open(args.events, os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW, 0o600)
        events = os.fdopen(fd,'w')
        def emit(kind, **data):
            events.write(json.dumps({'kind':kind,**data})+'\n');events.flush()
            print('event',flush=True)
        turn = service.call('/v1/chat/ask',request)['turn_id']
        emit('started',turn_id=turn,account=initial['account'])
        seen = None; reply_seen = ''; deadline = time.monotonic()+3600
        while time.monotonic()<deadline:
            state = service.state()
            if state['account'] != initial['account']: raise RuntimeError('Mike account changed; old editor connection ended')
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
