"""Small FP32-master autoregressive context probe using C-equivalent sampling/UTF8.
Eight stratified cases from an already observed suite; not a new blind benchmark.
"""
import argparse,json,ctypes as C,hashlib
from pathlib import Path
import torch
from transformers import AutoTokenizer,Qwen3ForCausalLM
from native import ROOT
p=argparse.ArgumentParser();p.add_argument('--profile',choices=['n16','n32'],required=True);a=p.parse_args();torch.set_num_threads(2)
src=ROOT/f'models/{a.profile}-orthogonal-round5/final';tok=AutoTokenizer.from_pretrained(src);m=Qwen3ForCausalLM.from_pretrained(src,dtype=torch.float32).eval()
# Same byte-level vocabulary mapping as tokenizer C decoder.
bs=list(range(33,127))+list(range(161,173))+list(range(174,256));cs=bs[:];n=0
for b in range(256):
 if b not in bs:bs.append(b);cs.append(256+n);n+=1
inverse={chr(c):b for b,c in zip(bs,cs)}
raw=[]
for i in range(len(tok)):
 piece=tok.convert_ids_to_tokens(i);raw.append(b'' if i in (0,1,2) else bytes(inverse[c] for c in piece))
class State(C.Structure):_fields_=[('left',C.c_ubyte),('lo',C.c_ubyte),('hi',C.c_ubyte)]
feed=C.CDLL(str(ROOT/'build/utf8_probe.so')).probe;feed.argtypes=[C.POINTER(State),C.c_char_p,C.c_size_t]
cases=[];counts={}
for line in (ROOT/'eval/context-round5-frozen.jsonl').read_text().splitlines():
 r=json.loads(line);k=r['kind']
 if counts.get(k,0)>=2:continue
 counts[k]=counts.get(k,0)+1;cases.append(r)
rows=[]
for case in cases:
 context=[];turns=[]
 for user in [x['content'] for x in case['messages'] if x['role']=='user']:
  prefix=tok.encode(f'<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n',add_special_tokens=False);context+=prefix
  hist=[];chunks=[];utf8=State();complete=0
  with torch.no_grad():
   state=m(torch.tensor([context]),use_cache=True)
   for step in range(32):
    logits=state.logits[0,-1].clone()
    for t in hist:logits[t]=logits[t]/1.25 if logits[t]>0 else logits[t]*1.25
    if len(hist)>=5:
     for h in range(len(hist)-5):
      if hist[h:h+5]==hist[-5:]:logits[hist[h+5]]=-1e30
    for _ in range(len(raw)):
     t=int(logits.argmax());stop=t in (0,2);candidate=State.from_buffer_copy(bytes(utf8));b=raw[t]
     if (stop and not utf8.left) or (not stop and b and feed(C.byref(candidate),b,len(b))):break
     logits[t]=-torch.inf
    else:raise RuntimeError('no valid candidate')
    if stop:break
    utf8=candidate;hist.append(t);chunks.append(b)
    state=m(torch.tensor([[t]]),past_key_values=state.past_key_values,use_cache=True)
    if not utf8.left:complete=len(hist)
  if utf8.left:hist=hist[:complete];chunks=chunks[:complete]
  answer=b''.join(chunks).decode('utf8');context+=hist+[2]+tok.encode('\n',add_special_tokens=False);turns.append({'question':user,'answer':answer})
 expected=case['messages'][-1]['content'];rows.append({'kind':case['kind'],'code':case['context_code'],'color':case['context_color'],'turns':turns,'expected_final':expected,'exact_whole_answer_match':turns[-1]['answer']==expected})
out={'weights':'FP32 master','kv':'FP32','sampler':'generated-only per-occurrence 1.25 penalty, no-repeat6, same C UTF8 prefix guard; max32','selection':'first two cases per kind from observed 96; diagnostic only','model_sha256':hashlib.sha256((src/'model.safetensors').read_bytes()).hexdigest(),'rows':rows,'physical_board_test':False}
(ROOT/f'eval/round5-{a.profile}-fp32-master-context-probe.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(a.profile,len(rows),sum(x['exact_whole_answer_match'] for x in rows))
