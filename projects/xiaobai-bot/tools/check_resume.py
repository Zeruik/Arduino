"""Exercise bounded resume best preservation and config rejection on disposable copies."""
import hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(prefix='resume-round2-',dir=root/'models') as t:
    out=Path(t)
    source=root/'models/n16-mha-probe-round1'
    for name in ['rolling','best']:shutil.copytree(source/name,out/name)
    summary=json.loads((source/'summary.json').read_text())
    # A strictly lower recorded loss forces the preservation branch.
    summary['best_val_loss']=-1.0
    (out/'summary.json').write_text(json.dumps(summary))
    before=sha(out/'best/model.safetensors')
    cmd=[sys.executable,'tools/train.py','--model','models/n16-v4-round1-step11428',
         '--out',str(out),'--data','data/train-full-v4.jsonl','--val','data/val-v2.jsonl',
         '--layers','11','--seq','384','--steps','200','--minutes','1','--threads','2',
         '--lr','0.000003','--save-every','100','--qat','--resume']
    run=subprocess.run(cmd,cwd=root,capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    preserved=before==sha(out/'best/model.safetensors')
    assert preserved
    # final guard is unrelated to configuration check; remove disposable final.
    shutil.rmtree(out/'final')
    cmd[cmd.index('--seq')+1]='192'
    bad=subprocess.run(cmd,cwd=root,capture_output=True,text=True)
    assert bad.returncode!=0 and 'configuration/data changed' in bad.stderr
    result={'best_weights_preserved':preserved,'configuration_mismatch_rejected':True,
            'training_steps_added':0,'scope':'CPU QAT checkpoint load, no-op resume; not board testing'}
    (root/'eval/round2-resume-check.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))
