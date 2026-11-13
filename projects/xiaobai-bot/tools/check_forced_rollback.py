"""Linux test-only sampler interposition to force an incomplete byte token.
No test hook is compiled into the shipped runtime/firmware.
"""
import ctypes as C,json,sys,subprocess
from pathlib import Path
from native import Native,ROOT
so=ROOT/'build/forced_sampler.so'
subprocess.run(['gcc','-std=c23','-O2','-shared','-fPIC',str(ROOT/'tests/forced_sampler.c'),'-o',str(so)],check=True)
stub=C.CDLL(str(so),mode=C.RTLD_GLOBAL);stub.force_token.argtypes=[C.c_int]
vocab=json.loads((ROOT/'models/n16-semantic-round3/final/tokenizer.json').read_text())['model']['vocab'];stub.force_token(vocab['ä'])
n=Native(ROOT/'models/n16-semantic-q4-round3',512);q='你好';np=len(n.tokens(f'<|im_start|>user\n{q}<|im_end|>\n<|im_start|>assistant\n')[0]);answer=n.answer(q,1)
assert answer=='' and n.lib.xb_utf8_rollbacks()==1 and n.lib.xb_context_tokens()==np+2
result={'pass':True,'test_only_forced_utf8_lead_token':True,'model_forward_real':True,'semantic_quality_test':False,'rollback_events':n.lib.xb_utf8_rollbacks(),'answer_empty':not answer,'context_matches_rolled_back_history':True,'test_hook_in_shipped_runtime':False}
(ROOT/'eval/round4-forced-rollback.json').write_text(json.dumps(result,indent=2));print(result)
