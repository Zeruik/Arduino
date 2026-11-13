"""记录原始模型回复；关键词只作提示，不把关键词命中冒充知识正确率。"""
import argparse,json,time,sys,ctypes as C,hashlib
from pathlib import Path
from native import Native, ROOT
ap=argparse.ArgumentParser();ap.add_argument('--model',required=True);ap.add_argument('--hf');ap.add_argument('--out',required=True);ap.add_argument('--ctx',type=int,default=512)
a=ap.parse_args();n=Native(a.model,a.ctx)
from transformers import AutoTokenizer
tok=AutoTokenizer.from_pretrained(a.hf) if a.hf else None
# GB2312 一级汉字 3755 + 二级区前 245，共 4000 个不同汉字；验证可编码，不代表认识这些字。
chars=[]
for zone in list(range(0xb0,0xd8))+list(range(0xd8,0xf8)):
    for cell in range(0xa1,0xff):
        try:s=bytes([zone,cell]).decode('gb2312')
        except UnicodeDecodeError:continue
        if '\u4e00'<=s<='\u9fff':chars.append(s)
chars=chars[:4000];assert len(set(chars))==4000
roundtrip=0;parity=0
for c in chars:
    ids,decoded=n.tokens(c);roundtrip+=decoded==c
    if tok:parity+=ids==tok.encode(c,add_special_tokens=False)
rows=[]
for r in [json.loads(x) for x in (ROOT/'data/test.jsonl').read_text().splitlines()]:
    t=time.monotonic();ans=n.answer(r['question']);rows.append(dict(r,answer=ans,seconds=round(time.monotonic()-t,3),keyword_hint=any(k in ans for k in r['keywords'])))
    print(r['question'],ans,flush=True)
result={'model':a.model,'model_sha256':hashlib.sha256((Path(a.model)/'model.bin').read_bytes()).hexdigest(),'ctx':a.ctx,'kv_bytes':n.lib.xb_kv_bytes(),'hanzi_roundtrip':roundtrip,'hanzi_count':4000,'tokenizer_hf_parity':parity if tok else 'not run','rows':rows,'status':'candidate; human knowledge review and physical board tests required','keyword_hint_is_accuracy':False}
Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('4000 汉字 roundtrip:',roundtrip)
