"""Actual Q4 inference under tiny output budgets/caps; checks bytes and KV rollback."""
import ctypes as C,json,argparse
from pathlib import Path
from native import Native,ROOT
p=argparse.ArgumentParser();p.add_argument('--profile',choices=['n16','n32'],required=True);a=p.parse_args()
n=Native(ROOT/f'models/{a.profile}-semantic-q4-round3',512 if a.profile=='n16' else 1024)
queries=['你好','月亮自己发光吗','请简要解释中文编码','电压是什么意思']
count=rollbacks=rejected=0
for q in queries:
 prefix=f'<|im_start|>user\n{q}<|im_end|>\n<|im_start|>assistant\n';np=len(n.tokens(prefix)[0])
 for budget in [1,2,3,4,7,8]:
  for cap in [2,3,5,9,17]:
   n.lib.xb_reset();buf=(C.c_ubyte*(cap+8))(*([0xa5]*(cap+8)));ptr=C.cast(C.byref(buf,4),C.c_void_p)
   rc=n.lib.xb_answer(q.encode(),ptr,cap,budget,None);assert rc>=0
   assert bytes(buf[:4])==b'\xa5'*4 and bytes(buf[-4:])==b'\xa5'*4
   raw=bytes(buf[4:4+cap]);assert b'\0' in raw;answer=raw.split(b'\0',1)[0];answer.decode('utf8')
   assert n.lib.xb_context_tokens()==np+rc+2,(q,budget,cap,n.lib.xb_context_tokens(),np,rc)
   rejected+=n.lib.xb_utf8_rejections();rollbacks+=n.lib.xb_utf8_rollbacks();count+=1
# A follow-up after a truncated first reply must also remain decodable.
n.answer('你好',1);n.answer('再说一句话',16,reset=False)
report={'pass':True,'actual_q4_cases':count,'boundary_canaries_intact':True,'all_outputs_strict_utf8':True,'context_length_matches_retained_tokens':True,'rollback_events':rollbacks,'rejected_candidates':rejected,'empty_boundary_outputs_allowed':True,'physical_board_test':False}
(ROOT/f'eval/round4-{a.profile}-utf8-boundaries.json').write_text(json.dumps(report,indent=2));print(report)
