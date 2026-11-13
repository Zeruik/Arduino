"""Selected checkpoint evaluation; no test-conditioned updates."""
import argparse,subprocess,sys,os
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--profile',choices=['n16','n32'],required=True);a=p.parse_args();profile=a.profile
hf=f'models/{profile}-orthogonal-round5/final';q4=f'models/{profile}-orthogonal-q4-round5';ctx='512' if profile=='n16' else '1024'
assert Path(hf+'/model.safetensors').exists()
def run(*s):subprocess.run([sys.executable,*s],check=True,env=dict(os.environ,OMP_NUM_THREADS='2'))
run('tools/export_model.py','--model',hf,'--out',q4,'--ctx',ctx,'--max-model-bytes',str(0xd80000 if profile=='n16' else 0xef0000),'--max-tokenizer-bytes','524288')
run('tools/verify_numerics.py','--model',q4,'--hf',hf,'--out',f'eval/round5-{profile}-numerics.json')
fw=f'firmware/.pio/build/{"n16r8" if profile=="n16" else "n32r16"}/firmware.bin'
run('tools/check_layout.py','--model',q4,'--profile',profile,'--firmware',fw,'--out',f'eval/round5-{profile}-layout.json')
for fp32 in [False,True]:
 run('tools/evaluate_context.py','--model',q4,'--ctx',ctx,'--suite','eval/context-round5-frozen.jsonl','--max-new','32','--out',f'eval/round5-{profile}-context-'+('fp32kv' if fp32 else 'int8')+'.json',*(['--fp32-kv'] if fp32 else []))
run('tools/evaluate_context.py','--model',q4,'--ctx',ctx,'--suite','eval/context-round5-counterfactual.jsonl','--max-new','32','--out',f'eval/round5-{profile}-counterfactual-int8.json')
run('tools/evaluate_frozen.py','--model',q4,'--ctx',ctx,'--suite','eval/independent-round3-frozen.jsonl','--out',f'eval/round5-{profile}-knowledge-regression.json')
run('tools/evaluate.py','--model',q4,'--hf',hf,'--ctx',ctx,'--out',f'eval/round5-{profile}-tokenizer-development.json')
run('tools/package.py','--profile','N16R8' if profile=='n16' else 'N32R16','--hf',hf,'--q4',q4,'--tag','v0.2-dev-round5')
