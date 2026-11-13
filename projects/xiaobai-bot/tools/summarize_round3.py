"""Collect measured round3 status, without keyword-based factual accuracy."""
import json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def read(p):return json.loads((root/p).read_text())
s={'round':3,'total_rounds':6,'next_round':4,'date':'2026-11-13','baseline_steps':{'n16':11428,'n32':11882},'baseline_training_process_alive_on_entry':False,'finish_v4_log_bytes':(root/'logs/finish-v4.log').stat().st_size,'knowledge_accepted':False,'physical_board_accepted':False,'windows_interaction_tested':False,'windows_new_source_built':False,'default_candidate_replaced':False,'probes':{},'independent':{}}
for name in ['n16-fixed','n16-semantic','n32-semantic']:
 d=root/f'models/{name}-round3';s['probes'][name]={'summary':read(str(d.relative_to(root)/'summary.json')),'selected_extra_step':read(str(d.relative_to(root)/'final/checkpoint_meta.json'))['step'],'fp32_sha256':hashlib.sha256((d/'final/model.safetensors').read_bytes()).hexdigest()}
 if name.endswith('semantic'):
  a=read(f'eval/round3-{name}-round3-val-int8kv.json');b=read(f'eval/round3-{name}-round3-val-fp32kv.json');s['probes'][name].update({'kv_bytes':a['kv_bytes'],'kv_identical_out_of_24':sum(x['answer']==y['answer'] for x,y in zip(a['rows'],b['rows'])),'q4_layout':read(f'eval/round3-{name}-round3-layout.json'),'numerics':read(f'eval/round3-{name}-round3-numerics.json')['pass']})
for name in ['n16-baseline','n32-baseline','n16-semantic-round3','n32-semantic-round3']:
 d=read(f'eval/round3-{name}-independent-int8kv.json');s['independent'][name]={'rows':len(d['rows']),'invalid_utf8':sum(not x.get('utf8_valid',True) for x in d['rows']),'comprehensive_knowledge_accepted':False,'multi_turn_accepted':False}
s['new_package_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'dist').glob('*v0.2-dev-round3*.zip'))}
a=read('eval/round3-n16-dequant-sampler-probe.json');b=read('eval/round3-n16-semantic-round3-val-fp32kv.json');s['sampler_probe']={'matched_answers':sum(x['answer']==y['answer'] for x,y in zip(a['rows'],b['rows'])),'total':4,'comparison':'HF actual dequantized Q4 with native sampler vs C Q4 FP32-KV; does not prove all prompts'}
(root/'eval/round3-status.json').write_text(json.dumps(s,ensure_ascii=False,indent=2))
print({k:v for k,v in s.items() if k in ['round','independent','sampler_probe']})
