"""Record raw FP32 responses to an explicit suite; never calculate keyword accuracy."""
import argparse,json,hashlib
from pathlib import Path
import torch
from transformers import AutoTokenizer,Qwen3ForCausalLM
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--suite',required=True);p.add_argument('--out',required=True);p.add_argument('--limit',type=int);p.add_argument('--sampler',choices=['greedy','native'],default='native');a=p.parse_args()
torch.set_num_threads(2)
src=Path(a.model);suite=Path(a.suite)
tok=AutoTokenizer.from_pretrained(src);m=Qwen3ForCausalLM.from_pretrained(src,dtype=torch.float32).eval()
rows=[]
for line in suite.read_text().splitlines()[:a.limit]:
 r=json.loads(line);q=r['question'];ids=tok.encode(f'<|im_start|>user\n{q}<|im_end|>\n<|im_start|>assistant\n',add_special_tokens=False,return_tensors='pt')
 with torch.no_grad():
  if a.sampler=='greedy':out=m.generate(ids,max_new_tokens=96,do_sample=False,eos_token_id=2,pad_token_id=3)
  else:
   # Mirror feng_sample_greedy: generated history only, penalty per occurrence,
   # then no-repeat 6-gram. HF's built-in repetition_penalty has other semantics.
   hist=[];state=m(ids,use_cache=True)
   for _ in range(96):
    logits=state.logits[0,-1].clone()
    for token in hist:
     logits[token]=logits[token]/1.25 if logits[token]>0 else logits[token]*1.25
    if len(hist)>=5:
     for h in range(len(hist)-5):
      if hist[h:h+5]==hist[-5:]:logits[hist[h+5]]=-1e30
    token=int(logits.argmax())
    if token in (0,2):break
    hist.append(token);state=m(torch.tensor([[token]]),past_key_values=state.past_key_values,use_cache=True)
   out=torch.cat([ids,torch.tensor([hist],dtype=torch.long)],dim=1)
 rows.append({'question':q,'answer':tok.decode(out[0,ids.shape[1]:],skip_special_tokens=True),'generated_token_ids':out[0,ids.shape[1]:].tolist()})
Path(a.out).write_text(json.dumps({'model':a.model,'suite':a.suite,'suite_sha256':hashlib.sha256(suite.read_bytes()).hexdigest(),'model_sha256':hashlib.sha256((src/'model.safetensors').read_bytes()).hexdigest(),'weights':'FP32','kv':'FP32','sampler':a.sampler,'rows':rows,'scoring':'raw outputs; manual full-answer review required','physical_board_test':False},ensure_ascii=False,indent=2))
