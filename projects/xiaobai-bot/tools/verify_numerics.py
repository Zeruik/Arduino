"""将实际导出的 Q4 文件反量化到 HF，与共享 C 核心的 fp32 KV 路径对拍。"""
import argparse,ctypes as C,json,struct,os
from pathlib import Path
import numpy as np,torch
from transformers import Qwen3ForCausalLM,AutoTokenizer
from native import ROOT
torch.set_num_threads(4)
ap=argparse.ArgumentParser();ap.add_argument('--model',required=True);ap.add_argument('--hf',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
d=Path(a.model);b=(d/'model.bin').read_bytes();hdr=struct.unpack_from('<9I2f',b);nt=hdr[2];tensors={}
for i in range(nt):
    name,dt,*vals=struct.unpack_from('<32sIIIIIQQ',b,44+i*68);shape=[x for x in vals[:4] if x];off,size=vals[4:];name=name.rstrip(b'\0').decode();buf=b[off:off+size]
    if dt==0:arr=np.frombuffer(buf,dtype='<f2').astype('float32').reshape(shape)
    else:
        rows,cols=shape;blocks=cols//64;rb=blocks*34;raw=np.frombuffer(buf,dtype='uint8').reshape(rows,rb);s=raw[:,:blocks*2].copy().view('<f2').astype('float32').reshape(rows,blocks,1);p=raw[:,blocks*2:].reshape(rows,blocks,32);v=np.empty((rows,blocks,64),dtype='float32');v[:,:,::2]=(p&15).astype('float32')-8;v[:,:,1::2]=(p>>4).astype('float32')-8;arr=(v*s).reshape(shape)
    tensors[name]=torch.from_numpy(arr.copy())
m=Qwen3ForCausalLM.from_pretrained(a.hf,dtype=torch.float32).eval();sd=m.state_dict();sd['model.embed_tokens.weight']=tensors['tok_embd.weight'];sd['lm_head.weight']=tensors['tok_embd.weight'];sd['model.norm.weight']=tensors['output_norm.weight']
mapping={'attn_norm':'input_layernorm','ffn_norm':'post_attention_layernorm','attn_q':'self_attn.q_proj','attn_k':'self_attn.k_proj','attn_v':'self_attn.v_proj','attn_output':'self_attn.o_proj','attn_q_norm':'self_attn.q_norm','attn_k_norm':'self_attn.k_norm','ffn_gate':'mlp.gate_proj','ffn_up':'mlp.up_proj','ffn_down':'mlp.down_proj'}
for i in range(hdr[3]):
    for x,y in mapping.items():sd[f'model.layers.{i}.{y}.weight']=tensors[f'blk.{i}.{x}.weight']
m.load_state_dict(sd);tok=AutoTokenizer.from_pretrained(a.hf)
lib=C.CDLL(str(ROOT/'build'/('xiaobai-f32.dll' if os.name=='nt' else 'libxiaobai-f32.so')))
lib.xb_init.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_int];lib.xb_logits.argtypes=[C.c_int,C.c_int,C.c_void_p,C.c_int]
mb=C.create_string_buffer(b);tb=C.create_string_buffer((d/'tokenizer.bin').read_bytes());assert lib.xb_init(mb,len(b),tb,len(tb)-1,512)==0
rows=[]
for text in ['你好','欧姆定律是什么','你叫什么名字','中国的首都是哪里']:
    ids=tok.encode('<|im_start|>user\n'+text+'<|im_end|>\n<|im_start|>assistant\n',add_special_tokens=False)
    with torch.no_grad():ref=m(torch.tensor([ids])).logits[0,-1].numpy()
    lib.xb_reset();out=(C.c_float*len(ref))()
    for pos,id in enumerate(ids):assert lib.xb_logits(id,pos,out,len(ref))==len(ref)
    got=np.array(out);diff=np.abs(got-ref);r={'prompt':text,'max_abs_diff':float(diff.max()),'mean_abs_diff':float(diff.mean()),'top1_match':int(got.argmax())==int(ref.argmax())};rows.append(r);print(r)
passed=all(r['max_abs_diff']<0.01 and r['top1_match'] for r in rows)
report={'pass':passed,'comparison':'dequantized actual Q4 vs C; fp32 KV isolates weight/forward parity; deployment INT8 KV separately evaluated in language tests','rows':rows}
Path(a.out).write_text(json.dumps(report,ensure_ascii=False,indent=2))
if not passed:raise SystemExit(1)
