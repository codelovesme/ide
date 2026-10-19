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

if __name__=='__main__':unittest.main()
