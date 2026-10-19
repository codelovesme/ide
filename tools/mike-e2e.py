#!/usr/bin/python3
"""Real IDE pty → shared service → central Mike → buffer/diff integration.

Uses the isolated scratch stack from my-euglena-apps/tools/mike-scratch-stack.py.
No live deployment, installed-package changes or real user project edits.
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

ROOT=Path(__file__).resolve().parents[1]
MIKE=ROOT.parent/'mike-desktop'
STACK=Path(os.environ.get('STACK_DIR','/var/tmp/m162/stack'))
stack=json.loads((STACK/'stack.json').read_text())
os.environ['STACK_DIR']=str(STACK)
os.environ['EUGLENA_HOST_URL']=stack['web']
os.environ['CODE_BIN']=str(Path.home()/'.local/share/cdlvsm/packages/code/v2.14.5/code')
headless=runpy.run_path(str(MIKE/'tools/headless-e2e.py'))
helpers=runpy.run_path(str(MIKE/'tools/service-e2e.py'))
sys.path.insert(0,str(ROOT/'tools'))
from drive import Session
checks=0

def check(value,label):
    global checks
    if not value and globals().get('screen'):
        print(screen.screen.text()[-5000:],flush=True)
    assert value,label
    checks+=1;print('PASS '+label,flush=True)

with tempfile.TemporaryDirectory(prefix='ide-mike-e2e-') as temporary:
    area=Path(temporary);project=area/'project';project.mkdir()
    target=project/'a.code';target.write_text('disk-value\n')
    config=area/'config/codelovesme-ide';config.mkdir(parents=True)
    (config/'settings.json').write_text(json.dumps({'ai.provider':'mike','ai.agent.mode':'edit','ai.providers':{'mike':{'type':'mike'}}}))
    service_area=area/'service';service_area.mkdir()
    service=helpers['Service'](service_area)
    client=None;screen=None
    try:
        email,token=headless['account']('ide162')
        service.start();client=service.client('ide-e2e-control');state=client.attach(token,connect='auto')
        check(state.get('editor_version')==1,'shared service advertises IDE protocol')
        env=dict(service.env,IDE_FOLDER=str(project),XDG_CONFIG_HOME=str(area/'config'),TERM='xterm-256color',MIKE_SERVICE_CLIENT_DIR=str(MIKE/'client'))
        binary=os.environ.get('IDE_TEST_BIN','/var/tmp/m162/ide-bin')
        screen=Session([binary],str(ROOT),env)
        check(screen.wait_for('Explorer',30),'real IDE starts on scratch project')
        screen.keys(b'\r',1)
        check(screen.wait_for('a.code',10),'file opens in IDE')
        screen.keys(b'UNSAVED-',1)
        check('UNSAVED-disk-value' in screen.screen.text(),'unsaved content differs from disk')
        screen.keys(b'\x0c',1) # Ctrl+L: existing AI chat
        question='In the active a.code use ReadBuffer and EditBuffer to replace disk-value with done, preserving the UNSAVED- prefix. Use save=false (buffer only). Do not use terminal commands. Finish with IDE162DONE.'
        screen.keys(question.encode()+b'\r',1)
        check(screen.wait_for('Mike proposes a change',180),'Mike uses live editor tools and opens the existing diff UI')
        check(target.read_text()=='disk-value\n','proposal has not changed disk')
        screen.keys(b'a',1)
        check(screen.wait_for('IDE162DONE',120),'normal diff acceptance returns structured result to central Mike')
        check('UNSAVED-done' in screen.screen.text(),'actual IDE buffer contains the requested change')
        check(target.read_text()=='disk-value\n','buffer-only result is not falsely saved')
        # A second client remains usable; IDE never ran Mike CLI or another service.
        check(service.process.poll() is None and client.state()['account']==email,'same shared service and other client stay connected')
        screen.keys(b'\x11',0.3) # Ctrl+Q; unsaved prompt is refused below
        screen.keys(b'n',0.3)
    finally:
        if screen:
            try: os.kill(screen.pid,signal.SIGTERM)
            except ProcessLookupError: pass
            screen.pump(0.3)
            os.close(screen.fd)
        if client:
            try: client.revoke()
            finally: client.detach()
        service.stop();service.log.close()
print(f'{checks}/10 real IDE integration checks passed')
