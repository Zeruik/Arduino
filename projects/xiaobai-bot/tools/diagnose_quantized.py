"""Development prompt ablation for Q4 weights with INT8 and FP32 KV (host only)."""
import argparse,json,hashlib,subprocess,sys
from pathlib import Path
from native import Native,ROOT
p=argparse.ArgumentParser();p.add_argument('--models',nargs='+',required=True);a=p.parse_args()
# The C runtime intentionally permits one model initialization per library/process.
if len(a.models)>1:
    for path in a.models:
        subprocess.run([sys.executable,__file__,'--models',path],check=True)
    raise SystemExit(0)
questions=[json.loads(s)['question'] for s in (ROOT/'data/test.jsonl').read_text().splitlines()]
for path in a.models:
    for fp32 in [False,True]:
        n=Native(path,512,fp32_kv=fp32)
        rows=[{'question':q,'answer':n.answer(q,96)} for q in questions]
        result={'weights':'Q4','kv':'FP32' if fp32 else 'INT8','ctx':512,
            'kv_bytes':n.lib.xb_kv_bytes(),'physical_board_test':False,
            'suite_role':'development regression, not independent accuracy',
            'model_sha256':hashlib.sha256((Path(path)/'model.bin').read_bytes()).hexdigest(),'rows':rows}
        out=ROOT/'eval'/('round2-'+Path(path).name+'-'+result['kv'].lower()+'.json')
        out.write_text(json.dumps(result,ensure_ascii=False,indent=2))
        print(str(out),flush=True)
