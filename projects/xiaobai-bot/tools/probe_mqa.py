"""Non-deployment MHA->MQA mean-pool probe. Evaluation uses validation, never frozen test."""
import json,torch,subprocess,sys
from pathlib import Path
from transformers import Qwen3ForCausalLM,AutoTokenizer
root=Path(__file__).resolve().parents[1];torch.set_num_threads(2)
src=root/'models/n16-v4-round1-step11428';dest=root/'models/n16-mqa-round1-init'
m=Qwen3ForCausalLM.from_pretrained(src,dtype=torch.float32);tok=AutoTokenizer.from_pretrained(src)
cfg=m.config;sd=m.state_dict();cfg.num_key_value_heads=1
for k in list(sd):
 if k.endswith(('self_attn.k_proj.weight','self_attn.v_proj.weight')):sd[k]=sd[k].reshape(7,64,448).mean(0)
mqa=Qwen3ForCausalLM(cfg);mqa.load_state_dict(sd);dest.mkdir(exist_ok=True);mqa.save_pretrained(dest);tok.save_pretrained(dest)
(root/'eval/mqa-round1-conversion.json').write_text(json.dumps({'source':str(src),'init':'mean of seven K/V heads, Q preserved','kv_heads':1,'c_export_supported':False,'deployment_replaced':False,'note':'Equal 200-step QAT budgets compared using val-v2; frozen independent suite not consumed.'},indent=2))
for name,model in [('mha',src),('mqa',dest)]:
 subprocess.run([sys.executable,'tools/train.py','--model',str(model),'--out',f'models/n16-{name}-probe-round1','--data','data/train-full-v4.jsonl','--val','data/val-v2.jsonl','--layers','11','--seq','384','--steps','200','--minutes','8','--threads','2','--lr','0.000003','--save-every','100','--qat'],cwd=root,check=True)
