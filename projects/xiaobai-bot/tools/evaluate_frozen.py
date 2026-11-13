"""Frozen evaluation: store full answers, no keyword scoring or training feedback."""
import argparse,json,hashlib,time
from pathlib import Path
from native import Native,ROOT
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--ctx',type=int,required=True);p.add_argument('--out',required=True);p.add_argument('--fp32-kv',action='store_true');p.add_argument('--suite',default='eval/independent-round1-frozen.jsonl');a=p.parse_args()
suite=ROOT/a.suite;n=Native(a.model,a.ctx,fp32_kv=a.fp32_kv)
rows=[]
def answer_record(q,reset=True):
 try:return {'answer':n.answer(q,96,reset=reset),'utf8_valid':True}
 except UnicodeDecodeError as e:
  # Retain exact bytes and flag the failure. Display replacement is not a pass.
  return {'answer':e.object.decode('utf-8',errors='replace'),'utf8_valid':False,
          'raw_answer_hex':e.object.hex(),'decode_error':str(e)}
for l in suite.read_text().splitlines():
 r=json.loads(l);start=time.monotonic();r.update(answer_record(r['question']));r['host_seconds']=time.monotonic()-start;rows.append(r)
turns=[]
for q in ['我正在学习机械。请记住我刚才说的学习方向。','我刚才说在学什么？','你的名字和作者是谁？']:
 turns.append(dict(question=q,**answer_record(q,reset=not turns)))
result={'model':a.model,'model_sha256':hashlib.sha256((Path(a.model)/'model.bin').read_bytes()).hexdigest(),'suite_sha256':hashlib.sha256(suite.read_bytes()).hexdigest(),'weights':'Q4','kv':'FP32' if a.fp32_kv else 'INT8','ctx':a.ctx,'kv_bytes':n.lib.xb_kv_bytes(),'rows':rows,'multi_turn':turns,'physical_board_test':False,'scoring':'unscored; manual factual review required; timings are host-only'}
Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2));print(a.out,len(rows),flush=True)
