"""Select with context validation only; record actual C multi-turn and regression."""
import argparse,subprocess,sys,os
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--profile',choices=['n16','n32'],required=True);a=p.parse_args();profile=a.profile
hf=f'models/{profile}-multiturn-round4/final';q4=f'models/{profile}-multiturn-q4-round4';ctx='512' if profile=='n16' else '1024'
assert Path(hf+'/model.safetensors').exists()
def run(*s):subprocess.run([sys.executable,*s],check=True,env=dict(os.environ,OMP_NUM_THREADS='2'))
run('tools/export_model.py','--model',hf,'--out',q4,'--ctx',ctx,'--max-model-bytes',str(0xd80000 if profile=='n16' else 0xef0000),'--max-tokenizer-bytes','524288')
run('tools/verify_numerics.py','--model',q4,'--hf',hf,'--out',f'eval/round4-{profile}-numerics.json')
fw=f'firmware/.pio/build/{"n16r8" if profile=="n16" else "n32r16"}/firmware.bin'
run('tools/check_layout.py','--model',q4,'--profile',profile,'--firmware',fw,'--out',f'eval/round4-{profile}-layout.json')
for fp32 in [False,True]:
 run('tools/evaluate_context.py','--model',q4,'--ctx',ctx,'--out',f'eval/round4-{profile}-context-'+('fp32kv' if fp32 else 'int8')+'.json',*(['--fp32-kv'] if fp32 else []))
run('tools/evaluate_frozen.py','--model',q4,'--ctx',ctx,'--suite','eval/independent-round3-frozen.jsonl','--out',f'eval/round4-{profile}-knowledge-regression.json')
run('tools/evaluate.py','--model',q4,'--hf',hf,'--ctx',ctx,'--out',f'eval/round4-{profile}-tokenizer-development.json')
run('tools/package.py','--profile','N16R8' if profile=='n16' else 'N32R16','--hf',hf,'--q4',q4,'--tag','v0.2-dev-round4')
