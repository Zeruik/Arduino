"""Host source-logic tests only; no Windows GUI and no device flashing."""
import sys,json,hashlib,tempfile,copy,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'desktop'))
from package_checks import validate_package,LAYOUTS
from wizard import Wizard
class Checks(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name)
  self.m={'profile':'N16R8','files':[]}
  for name,(offset,limit) in LAYOUTS['N16R8'].items():
   b=b'unit test payload:'+name.encode();(self.base/name).write_bytes(b)
   self.m['files'].append({'name':name,'offset':offset,'size':len(b),'sha256':hashlib.sha256(b).hexdigest()})
 def tearDown(self):self.tmp.cleanup()
 def test_valid(self):self.assertEqual(validate_package(self.base,self.m),'N16R8')
 def test_corruption(self):
  (self.base/'model.bin').write_bytes(b'x'*self.m['files'][3]['size'])
  with self.assertRaisesRegex(ValueError,'校验失败'):validate_package(self.base,self.m)
 def test_profile_mismatch(self):
  with self.assertRaisesRegex(ValueError,'不一致'):validate_package(self.base,self.m,'N32R16')
 def test_profile_path(self):
  self.m['profile']='../../outside'
  with self.assertRaisesRegex(ValueError,'未知'):validate_package(self.base,self.m)
 def test_missing(self):
  self.m['files'].pop()
  with self.assertRaisesRegex(ValueError,'缺少'):validate_package(self.base,self.m)
 def test_duplicate(self):
  self.m['files'].append(copy.deepcopy(self.m['files'][0]))
  with self.assertRaisesRegex(ValueError,'重复'):validate_package(self.base,self.m)
 def test_offset(self):
  self.m['files'][3]['offset']=0
  with self.assertRaisesRegex(ValueError,'偏移'):validate_package(self.base,self.m)
 def test_path(self):
  self.m['files'][0]['name']='../outside'
  with self.assertRaisesRegex(ValueError,'文件名'):validate_package(self.base,self.m)
 def test_changed_after_import_never_launches_flasher(self):
  validate_package(self.base,self.m)
  (self.base/'model.bin').write_bytes(b'changed after import')
  events=[]
  fake=SimpleNamespace(installed=self.base,manifest=self.m,flash_profile='N16R8',flash_port='COM_TEST',root=SimpleNamespace(after=lambda *x:events.append(x)),working=True,next=None)
  with patch('wizard.subprocess.Popen') as launch:Wizard.flash(fake);launch.assert_not_called()
  self.assertFalse(fake.working);self.assertTrue(any('未完成' in x for x in events))
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
(root/'eval/round3-package-checks.json').write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'pass':result.wasSuccessful(),'scope':'Python source logic on '+sys.platform+'; no Windows installation UI or serial/device test'},indent=2))
if not result.wasSuccessful():raise SystemExit(1)
