"""Same old weight bytes, same failing prompt: previous vs guarded C libraries."""
import json,hashlib
from pathlib import Path
from native import Native,ROOT
q='负载电流超过器件额定值会有什么风险？';rows=[]
for name in ['libxiaobai-round3.so','libxiaobai.so']:
 lib=ROOT/'build'/name;n=Native(ROOT/'models/n32-q4-round1',1024,library_path=lib)
 try:answer=n.answer(q);r={'answer':answer,'utf8_valid':True}
 except UnicodeDecodeError as e:r={'answer':e.object.decode('utf8',errors='replace'),'raw_answer_hex':e.object.hex(),'utf8_valid':False}
 r.update(runtime=name,runtime_sha256=hashlib.sha256(lib.read_bytes()).hexdigest())
 if hasattr(n.lib,'xb_utf8_rejections'):r.update(rejected=n.lib.xb_utf8_rejections(),rollbacks=n.lib.xb_utf8_rollbacks())
 rows.append(r)
assert not rows[0]['utf8_valid'] and rows[1]['utf8_valid']
(ROOT/'eval/round4-utf8-reproduction.json').write_text(json.dumps({'question':q,'same_weights':True,'rows':rows,'physical_board_test':False},ensure_ascii=False,indent=2));print(rows)
