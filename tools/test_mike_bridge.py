"""Transport failures are structured and never install/start another service."""
import json
import os
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class BridgeTest(unittest.TestCase):
    def check_bridge(self, directory):
        env=dict(os.environ,MIKE_SERVICE_RUNTIME_DIR=str(directory))
        env.pop('MIKE_IDE_TOKEN',None)
        return subprocess.run(['/usr/bin/python3','-I',str(ROOT/'tools/mike_bridge.py'),'--check'],env=env,capture_output=True,text=True,timeout=5)
    def test_missing_service_is_reported_without_creating_it(self):
        with tempfile.TemporaryDirectory() as area:
            result=self.check_bridge(Path(area))
            self.assertEqual(result.returncode,1)
            reply=json.loads(result.stdout)
            self.assertFalse(reply['ready'])
            self.assertIn('not running',reply['note'])
            self.assertEqual(list(Path(area).iterdir()),[])
    def test_protocol_mismatch_is_not_downgraded(self):
        with tempfile.TemporaryDirectory() as area:
            directory=Path(area)
            for name,value in [('endpoint',json.dumps({'protocol':99,'port':1})),('client.key','x'*64)]:
                path=directory/name;path.write_text(value);path.chmod(0o600)
            result=self.check_bridge(directory)
            self.assertEqual(result.returncode,1)
            self.assertIn('protocol_mismatch',json.loads(result.stdout)['note'])
            self.assertNotIn('x'*64,result.stdout+result.stderr)

    def test_packaged_native_json_cannot_shadow_python_stdlib(self):
        with tempfile.TemporaryDirectory() as area:
            directory=Path(area)
            bridge=directory/'mike_bridge.py'
            shutil.copy2(ROOT/'tools/mike_bridge.py',bridge)
            (directory/'json.so').write_bytes(b'not a Python extension')
            env=dict(os.environ,MIKE_SERVICE_CLIENT_DIR=str(ROOT.parent/'mike-desktop/client'),MIKE_SERVICE_RUNTIME_DIR=str(directory/'absent'))
            env.pop('MIKE_IDE_TOKEN',None)
            result=subprocess.run(['/usr/bin/python3','-I',str(bridge),'--check'],cwd=directory,env=env,capture_output=True,text=True,timeout=5)
            self.assertEqual(result.returncode,1)
            self.assertIn('not running',json.loads(result.stdout)['note'])
            self.assertNotIn('ImportError',result.stderr)


import importlib.util, threading, urllib.request, urllib.parse, urllib.error, contextlib, io
def load_bridge():
    spec=importlib.util.spec_from_file_location('mike_bridge_under_test',ROOT/'tools/mike_bridge.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

TOKEN='account-session-token-must-not-leak'
class FakeServiceError(Exception):
    def __init__(self,error):super().__init__(error);self.error=error
class FakeSdk:
    """The service's attach contract (docs/local-service-protocol.md)."""
    ServiceError=FakeServiceError
    def __init__(self,account='',host='http://127.0.0.1:8962'):
        self.account=account;self.host=host;self.attaches=[]
        sdk=self
        class Service:
            def __init__(self,client,approvals=True):self.client=client;self.approvals=approvals
            def attach(self,token=None,connect='none'):
                sdk.attaches.append((self.client,self.approvals,connect,token))
                if connect!='none':
                    if token!=TOKEN:raise FakeServiceError('account_refused')
                    if sdk.account and sdk.account!='me@example.invalid' and connect!='switch':raise FakeServiceError('account_mismatch')
                    sdk.account='me@example.invalid'
                return {'host':sdk.host,'account':sdk.account,'connection':'connected' if sdk.account else 'signed_out','editor_version':1}
            def detach(self):pass
        self.MikeService=Service
    def reachable(self):return True

class LoginTest(unittest.TestCase):
    def run_login(self,sdk,browse,switch=False,timeout=5):
        bridge=load_bridge();opened=[];threads=[]
        def fake_open(url):
            opened.append(url);threads.append(threading.Thread(target=browse,args=(url,),daemon=True));threads[-1].start();return True
        bridge.webbrowser.open=fake_open
        with tempfile.TemporaryDirectory() as area:
            account=str(Path(area)/'account.json');out=io.StringIO()
            with contextlib.redirect_stdout(out):outcome=bridge.login(sdk,account,switch,timeout)
            for thread in threads:thread.join(5)
            stored=Path(account).read_text() if Path(account).exists() else ''
            mode=oct(Path(account).stat().st_mode&0o777) if stored else ''
        return outcome,stored,mode,opened,out.getvalue()
    @staticmethod
    def post(url,token=TOKEN,origin=None,state=None):
        query=urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        body=urllib.parse.urlencode({'state':state or query['state'][0],'token':token}).encode()
        request=urllib.request.Request('http://127.0.0.1:%s/callback'%query['port'][0],data=body,headers={'Origin':origin or 'http://127.0.0.1:8962'})
        try:return urllib.request.urlopen(request,timeout=5).status
        except urllib.error.HTTPError as error:return error.code
        except urllib.error.URLError:return 'closed'
    def test_browser_login_signs_in_a_signed_out_service(self):
        outcome,stored,mode,opened,printed=self.run_login(FakeSdk(),lambda url:self.post(url))
        self.assertTrue(outcome['signed_in']);self.assertEqual(json.loads(stored),{'account':'me@example.invalid'});self.assertEqual(mode,'0o600')
        parts=urllib.parse.urlsplit(opened[0]);query=urllib.parse.parse_qs(parts.query)
        self.assertEqual((parts.scheme,parts.netloc,parts.path),('http','127.0.0.1:8962','/desktop/connect'))
        self.assertEqual(query['app'],['IDE']);self.assertGreaterEqual(len(query['state'][0]),32)
        for shown in (json.dumps(outcome),stored,opened[0],printed):self.assertNotIn(TOKEN,shown)
    def test_wrong_state_or_origin_is_refused_and_one_use(self):
        codes=[]
        def browse(url):
            codes.append(self.post(url,state='x'*43));codes.append(self.post(url,origin='https://evil.example'))
            codes.append(self.post(url));codes.append(self.post(url))
        outcome,_,_,_,_=self.run_login(FakeSdk(),browse)
        self.assertTrue(outcome['signed_in']);self.assertEqual(codes[:3],[403,403,200])
        self.assertIn(codes[3],(403,'closed'))
    def test_cancelled_login_changes_nothing(self):
        sdk=FakeSdk(account='me@example.invalid')
        outcome,stored,_,_,_=self.run_login(sdk,lambda url:None,timeout=0.5)
        self.assertEqual(outcome['error'],'cancelled');self.assertEqual(stored,'')
        self.assertEqual([a[2] for a in sdk.attaches],['none'])
    def test_other_service_account_is_never_switched_silently(self):
        sdk=FakeSdk(account='other@example.invalid')
        outcome,stored,_,_,_=self.run_login(sdk,lambda url:self.post(url))
        self.assertEqual(outcome['error'],'account_mismatch');self.assertIn('other@example.invalid',outcome['note']);self.assertEqual(stored,'')
        self.assertEqual(sdk.account,'other@example.invalid')
        outcome,stored,_,_,_=self.run_login(sdk,lambda url:self.post(url),switch=True)
        self.assertTrue(outcome['signed_in']);self.assertEqual(sdk.account,'me@example.invalid')
        self.assertEqual(sdk.attaches[-1][2],'switch')
    def test_refused_session_and_untrusted_host(self):
        outcome,stored,_,_,_=self.run_login(FakeSdk(),lambda url:self.post(url,token='expired'))
        self.assertEqual(outcome['error'],'refused');self.assertEqual(stored,'')
        with self.assertRaises(RuntimeError):self.run_login(FakeSdk(host='https://evil.example'),lambda url:None)
    def test_sign_in_grants_no_approvals(self):
        sdk=FakeSdk();self.run_login(sdk,lambda url:self.post(url))
        self.assertTrue(all(approvals is False for _,approvals,_,_ in sdk.attaches))

class AccessTest(unittest.TestCase):
    def test_service_use_needs_the_same_ide_account(self):
        bridge=load_bridge();ok={'connection':'connected','account':'me@example.invalid'}
        self.assertEqual(bridge.blocked(ok,'me@example.invalid'),'')
        self.assertIn('Signed out of IDE',bridge.blocked(ok,''))
        self.assertIn('other@example.invalid',bridge.blocked(dict(ok,account='other@example.invalid'),'me@example.invalid'))
        self.assertIn('expired',bridge.blocked(dict(ok,connection='session_expired'),'me@example.invalid'))
        self.assertIn('offline',bridge.blocked(dict(ok,connection='offline'),'me@example.invalid'))
        self.assertIn('revoked',bridge.blocked(dict(ok,connection='revoked'),'me@example.invalid'))
        self.assertIn('signed out',bridge.blocked({'connection':'signed_out','account':''},'me@example.invalid'))
    def test_missing_installation_is_reported_not_replaced(self):
        bridge=load_bridge()
        class Absent:
            def reachable(self):return False
            def unit_installed(self):return False
            def ensure_running(self,*_):raise AssertionError('must not start anything')
        os.environ['MIKE_SERVICE_LAUNCHER']='/nonexistent/mike-service'
        try:
            with self.assertRaisesRegex(RuntimeError,'not installed'):bridge.start_service(Absent())
        finally:os.environ.pop('MIKE_SERVICE_LAUNCHER')

class HearSdk(FakeSdk):
    """FakeSdk whose session also answers /v1/chat/hear."""
    def __init__(self,account='me@example.invalid',answer=None,error=None):
        super().__init__(account=account);self.calls=[];sdk=self;base=self.MikeService
        class Service(base):
            def call(self,path,payload=None,timeout=20):
                sdk.calls.append((path,payload));
                if error:raise FakeServiceError(error)
                return answer
        self.MikeService=Service

class HearTest(unittest.TestCase):
    def run_hear(self,sdk,audio=b'RIFF'+b'\0'*4000,ide_account='me@example.invalid'):
        bridge=load_bridge()
        with tempfile.TemporaryDirectory() as area:
            wav=Path(area)/'voice.wav';wav.write_bytes(audio)
            account=Path(area)/'account.json'
            if ide_account:account.write_text(json.dumps({'account':ide_account}))
            return bridge.hear(sdk,str(wav),str(account))
    def test_recording_goes_to_hear_as_base64_wav(self):
        sdk=HearSdk(answer={'text':'open the readme'})
        self.assertEqual(self.run_hear(sdk),{'text':'open the readme'})
        path,payload=sdk.calls[0]
        self.assertEqual(path,'/v1/chat/hear');self.assertEqual(payload['format'],'wav')
        import base64;self.assertEqual(base64.b64decode(payload['audio_base64'])[:4],b'RIFF')
    def test_another_account_or_signed_out_ide_is_refused(self):
        with self.assertRaisesRegex(RuntimeError,'other@example.invalid'):self.run_hear(HearSdk(account='other@example.invalid'))
        with self.assertRaisesRegex(RuntimeError,'Signed out of IDE'):self.run_hear(HearSdk(),ide_account='')
    def test_old_service_and_long_recordings_say_why(self):
        self.assertIn('too old',self.run_hear(HearSdk(error='unknown_route'))['note'])
        sdk=HearSdk(answer={'text':'x'})
        self.assertEqual(self.run_hear(sdk,audio=b'\0'*3_000_001)['error'],'too_large');self.assertEqual(sdk.calls,[])

if __name__=='__main__':unittest.main()
