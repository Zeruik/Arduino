import subprocess,os,sys,argparse
from pathlib import Path
root=Path(__file__).resolve().parents[1];src=root/'firmware/XiaobaiBot/src';out=root/'build';out.mkdir(exist_ok=True)
names=['feng_model','feng_llm','feng_quant','feng_smp','feng_tokenizer','feng_sample','xb_runtime']
ap=argparse.ArgumentParser();ap.add_argument('--fp32-kv',action='store_true');a=ap.parse_args()
target=out/(('xiaobai-f32.dll' if os.name=='nt' else 'libxiaobai-f32.so') if a.fp32_kv else ('xiaobai.dll' if os.name=='nt' else 'libxiaobai.so'))
cmd=['gcc','-std=c23','-O2','-shared','-DFENG_KV_Q2=0','-DFENG_KV_INT8='+('0' if a.fp32_kv else '1'),'-DFENG_MAX_SCORES=2048']
if os.name!='nt':cmd+=['-fPIC']
cmd += ['-I'+str(src),*[str(src/(n+'.c')) for n in names],'-lm','-o',str(target)]
subprocess.run(cmd,check=True);print(target)
