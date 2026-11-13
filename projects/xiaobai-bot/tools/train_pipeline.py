"""CI/本地均可复现的单型号流水线；最终包始终标注候选。"""
import argparse,subprocess,sys,shutil
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--profile',choices=['n16','n32'],required=True);ap.add_argument('--steps',type=int,default=6000);a=ap.parse_args()
def run(*s):subprocess.run([sys.executable,*s],check=True)
base=f'models/{a.profile}-base';out=f'models/{a.profile}-sft-ci';qat=f'models/{a.profile}-qat-ci';q4=f'models/{a.profile}-q4-ci';ctx='512' if a.profile=='n16' else '2048'
run('tools/prepare_data.py')
if not Path(base).exists():run('tools/prepare_model.py','--vocab','8192' if a.profile=='n16' else '16384','--out',base)
if not Path(out+'/final').exists():run('tools/train.py','--model',base,'--out',out,'--data','data/train-v2.jsonl','--val','data/val-v2.jsonl','--layers','4','--steps',str(a.steps),'--minutes','90','--threads','2','--lr','0.00002','--save-every','200','--resume')
if not Path(out+'/final').exists():raise SystemExit('本段训练达到时间上限；检查点保留，尚未完成计划步数。')
if not Path(qat+'/final').exists():run('tools/train.py','--model',out+'/final','--out',qat,'--data','data/train-v2.jsonl','--val','data/val-v2.jsonl','--layers','4','--steps','2000','--minutes','40','--threads','2','--lr','0.000005','--save-every','200','--resume','--qat')
if not Path(qat+'/final').exists():raise SystemExit('量化感知阶段尚未完成，保存检查点后退出。')
run('tools/export_model.py','--model',qat+'/final','--out',q4,'--ctx',ctx,'--max-model-bytes',str(0xd80000 if a.profile=='n16' else 0xef0000),'--max-tokenizer-bytes','524288')
run('tools/build_host.py');run('tools/build_host.py','--fp32-kv')
run('tools/verify_numerics.py','--model',q4,'--hf',qat+'/final','--out',f'eval/{a.profile}-numerics-ci.json')
run('tools/evaluate.py','--model',q4,'--hf',qat+'/final','--ctx',ctx,'--out',f'eval/{a.profile}-language-ci.json')
subprocess.run([sys.executable,'-m','platformio','run','-d','firmware','-e','n16r8' if a.profile=='n16' else 'n32r16'],check=True)
fw=f'firmware/.pio/build/{"n16r8" if a.profile=="n16" else "n32r16"}/firmware.bin'
run('tools/check_layout.py','--model',q4,'--profile',a.profile,'--firmware',fw,'--out',f'eval/{a.profile}-layout-ci.json')
run('tools/package.py','--profile','N16R8' if a.profile=='n16' else 'N32R16','--hf',qat+'/final','--q4',q4,'--tag','ci-candidate')
