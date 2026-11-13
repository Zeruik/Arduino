"""Final sealed evaluation only. Never trains, exports, or selects checkpoints."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--profile', choices=['n16', 'n32'], required=True)
a = p.parse_args()
os.chdir(ROOT)
suite = ROOT / 'eval/final-round6-frozen.jsonl'
manifest = json.loads((ROOT / 'eval/final-round6-manifest.json').read_text())
assert hashlib.sha256(suite.read_bytes()).hexdigest() == manifest['sha256']
assert len(suite.read_text().splitlines()) == 100
ctx = '512' if a.profile == 'n16' else '1024'
for stage, suffix in [('round3', 'semantic-q4-round3'), ('round5', 'orthogonal-q4-round5')]:
    model = f'models/{a.profile}-{suffix}'
    for kv in ['int8', 'fp32kv']:
        out = f'eval/round6-{a.profile}-{stage}-{kv}.json'
        print('START', model, kv, flush=True)
        command = [sys.executable, 'tools/evaluate_frozen.py', '--model', model,
                   '--ctx', ctx, '--suite', str(suite), '--out', out]
        if kv == 'fp32kv':
            command.append('--fp32-kv')
        subprocess.run(command, check=True, env=dict(os.environ, OMP_NUM_THREADS='2'))
        result = json.loads((ROOT / out).read_text())
        assert result['suite_sha256'] == manifest['sha256'] and len(result['rows']) == 100
        print('DONE', out, 'utf8_errors', sum(not r['utf8_valid'] for r in result['rows']), flush=True)
print('FINISHED', a.profile, 'NO TRAINING OR TEST-CONDITIONED UPDATES', flush=True)
