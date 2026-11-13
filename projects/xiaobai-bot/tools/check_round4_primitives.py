"""Differential UTF8-prefix checks and real-tokenizer assistant-mask checks."""
import ctypes as C,codecs,random,subprocess,json,sys
from pathlib import Path
from transformers import AutoTokenizer
from chat_data import encode_row
root=Path(__file__).resolve().parents[1]
p=root/'tests/utf8_probe.c';p.write_text('#include "xb_utf8.h"\nint probe(xb_utf8_state *s,const char*b,size_t n){return xb_utf8_feed(s,b,n);}\n')
so=root/'build/utf8_probe.so';subprocess.run(['gcc','-std=c23','-O2','-shared','-fPIC','-I'+str(root/'firmware/XiaobaiBot/src'),str(p),'-o',str(so)],check=True)
class State(C.Structure):_fields_=[('left',C.c_ubyte),('lo',C.c_ubyte),('hi',C.c_ubyte)]
f=C.CDLL(str(so)).probe;f.argtypes=[C.POINTER(State),C.c_char_p,C.c_size_t]
def ref(b):
 if b'\0' in b:return False
 try:
  decoder=codecs.getincrementaldecoder('utf8')();decoder.decode(b,final=False)
  pending=decoder.getstate()[0]
  # Python may defer rejection of impossible prefixes such as ED A0 until the
  # final byte. Require that a prefix can actually be completed to a scalar.
  if pending:
   lead=pending[0];need=2 if lead<0xe0 else 3 if lead<0xf0 else 4
   suffix=bytearray()
   if len(pending)==1:
    suffix.append(0xa0 if lead==0xe0 else 0x90 if lead==0xf0 else 0x80)
   suffix.extend(b'\x80'*(need-len(pending)-len(suffix)))
   (b+suffix).decode('utf8')
  return True
 except UnicodeDecodeError:return False
def check(b):
 s=State();got=bool(f(C.byref(s),b,len(b)));assert got==ref(b),b.hex()
for x in range(65536):check(x.to_bytes(2,'big'))
random.seed(444)
for _ in range(10000):check(random.randbytes(random.randrange(0,16)))
# Every non-NUL Unicode scalar, including astral code points.
b=''.join(chr(i) for i in range(1,0x110000) if not 0xd800<=i<=0xdfff).encode();s=State();assert f(C.byref(s),b,len(b)) and not s.left
for text in ['小白Bot','𠀀😀é','一二三','a\n你\t好']:
 b=text.encode()
 for cut in range(len(b)+1):
  s=State();assert f(C.byref(s),b[:cut],cut);assert f(C.byref(s),b[cut:],len(b)-cut) and not s.left
# Invalid extension must not mutate prefix state.
s=State();assert f(C.byref(s),b'\xe4',1);before=bytes(s);assert not f(C.byref(s),b'A',1);assert bytes(s)==before
T=AutoTokenizer.from_pretrained(root/'models/n16-semantic-round3/final')
legacy=0
for line in (root/'data/curated.jsonl').read_text().splitlines():
 r=json.loads(line);ids,labels=encode_row(T,r)
 pre=T.encode(f'<|im_start|>user\n{r["question"]}<|im_end|>\n<|im_start|>assistant\n',add_special_tokens=False);tail=T.encode(r['answer']+'<|im_end|>\n',add_special_tokens=False)
 assert ids==pre+tail and labels==[-100]*len(pre)+tail;legacy+=1
r=json.loads((root/'data/val-multiturn-round4.jsonl').read_text().splitlines()[0]);ids,labels=encode_row(T,r);tail=T.encode(r['messages'][-1]['content']+'<|im_end|>\n',add_special_tokens=False)
assert labels==[-100]*(len(ids)-len(tail))+tail
bad={'messages':[{'role':'assistant','content':'x'},{'role':'user','content':'y'}]}
try:encode_row(T,bad);raise AssertionError('bad roles accepted')
except ValueError:pass
report={'pass':True,'all_two_byte_strings':65536,'random_prefixes':10000,'unicode_scalars':0x110000-0x800-1,'legacy_rows_identical':legacy,'split_tokens_valid':True,'invalid_extension_atomic':True,'last_turn_mask_checked':True,'invalid_roles_rejected':True,'physical_board_test':False}
(root/'eval/round4-primitives.json').write_text(json.dumps(report,indent=2));print(report)
