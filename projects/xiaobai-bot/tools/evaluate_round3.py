"""Run after training completes. Select checkpoint only with the wording validation set."""
import subprocess,sys,os,argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--profile',choices=['n16','n32'],required=True);p.add_argument('--stage',choices=['fixed','semantic'],required=True);a=p.parse_args()
name=f'{a.profile}-{a.stage}-round3';hf=f'models/{name}/final';q4=f'models/{a.profile}-{a.stage}-q4-round3';ctx='512' if a.profile=='n16' else '1024'
assert Path(hf+'/model.safetensors').exists(),'training has not finished'
def run(*s):subprocess.run([sys.executable,*s],check=True,env=dict(os.environ,OMP_NUM_THREADS='2'))
run('tools/export_model.py','--model',hf,'--out',q4,'--ctx',ctx,'--max-model-bytes',str(0xd80000 if a.profile=='n16' else 0xef0000),'--max-tokenizer-bytes','524288')
run('tools/verify_numerics.py','--model',q4,'--hf',hf,'--out',f'eval/round3-{name}-numerics.json')
run('tools/check_layout.py','--model',q4,'--profile',a.profile,'--out',f'eval/round3-{name}-layout.json')
run('tools/evaluate_hf_suite.py','--model',hf,'--suite','data/val-semantic-round3.jsonl','--out',f'eval/round3-{name}-val-fp32.json')
for fp32kv in [False,True]:
 run('tools/evaluate_frozen.py','--model',q4,'--ctx',ctx,'--suite','data/val-semantic-round3.jsonl','--out',f'eval/round3-{name}-val-'+('fp32kv' if fp32kv else 'int8kv')+'.json',*(['--fp32-kv'] if fp32kv else []))
# Independent suite is evaluated after final exists; outputs never enter training.
if a.stage=='semantic':
 run('tools/evaluate_frozen.py','--model',q4,'--ctx',ctx,'--suite','eval/independent-round3-frozen.jsonl','--out',f'eval/round3-{name}-independent-int8kv.json')
