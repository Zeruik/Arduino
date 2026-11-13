"""Autoregressive real C conversation, and the same final query after reset.
Exact whole-string equality is a copy-task diagnostic, not factual accuracy.
"""
import argparse,json,hashlib
from pathlib import Path
from native import Native,ROOT
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--ctx',required=True,type=int);p.add_argument('--out',required=True);p.add_argument('--fp32-kv',action='store_true');p.add_argument('--suite',default='eval/context-round4-frozen.jsonl');a=p.parse_args()
suite=ROOT/a.suite;n=Native(a.model,a.ctx,fp32_kv=a.fp32_kv);rows=[]
for line in suite.read_text().splitlines():
 case=json.loads(line);turns=[]
 for message in case['messages']:
  if message['role']!='user':continue
  response=n.answer(message['content'],64,reset=not turns)
  turns.append({'question':message['content'],'answer':response})
 reset_answer=n.answer(turns[-1]['question'],64,reset=True)
 expected=case['messages'][-1]['content']
 rows.append({'code':case['context_code'],'color':case['context_color'],'turns':turns,'expected_final':expected,'reset_final':reset_answer,'exact_whole_answer_match':turns[-1]['answer']==expected,'reset_exact_whole_answer_match':reset_answer==expected})
result={'model':a.model,'model_sha256':hashlib.sha256((Path(a.model)/'model.bin').read_bytes()).hexdigest(),'ctx':a.ctx,'weights':'Q4','kv':'FP32' if a.fp32_kv else 'INT8','suite_sha256':hashlib.sha256(suite.read_bytes()).hexdigest(),'rows':rows,'exact_whole_answer_matches':sum(r['exact_whole_answer_match'] for r in rows),'reset_exact_matches':sum(r['reset_exact_whole_answer_match'] for r in rows),'metric':'strict entire string equality on temporary user-provided fields; not semantic or knowledge accuracy','physical_board_test':False}
Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2));print(a.out,result['exact_whole_answer_matches'])
