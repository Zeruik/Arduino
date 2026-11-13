"""FP32 master diagnostic on one frozen prompt per category (not a full FP32 suite)."""
import json,torch,hashlib
from pathlib import Path
from transformers import AutoTokenizer,Qwen3ForCausalLM
root=Path(__file__).resolve().parents[1];torch.set_num_threads(2)
for p,step in [('n16',11428),('n32',11882)]:
 src=root/f'models/{p}-v4-round1-step{step}';tok=AutoTokenizer.from_pretrained(src);m=Qwen3ForCausalLM.from_pretrained(src,dtype=torch.float32);m.eval();rows=[]
 for l in (root/'eval/independent-round1-frozen.jsonl').read_text().splitlines():
  r=json.loads(l)
  if not r['id'].endswith('-01'):continue
  ids=tok.encode(f'<|im_start|>user\n{r["question"]}<|im_end|>\n<|im_start|>assistant\n',add_special_tokens=False,return_tensors='pt')
  with torch.no_grad():out=m.generate(ids,max_new_tokens=96,do_sample=False,eos_token_id=2,pad_token_id=3)
  r['answer']=tok.decode(out[0,ids.shape[1]:],skip_special_tokens=True);rows.append(r)
 (root/f'eval/{p}-round1-fp32-master-probe.json').write_text(json.dumps({'weights':'FP32','kv':'FP32','model_sha256':hashlib.sha256((src/'model.safetensors').read_bytes()).hexdigest(),'rows':rows,'physical_board_test':False},ensure_ascii=False,indent=2))
 print(p,'FP32 probe complete',flush=True)
