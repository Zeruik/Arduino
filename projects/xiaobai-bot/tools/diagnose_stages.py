"""Stage ablation on existing DEVELOPMENT questions; never trains from test answers."""
import json, hashlib, time, argparse
from pathlib import Path
import torch
from transformers import AutoTokenizer, Qwen3ForCausalLM

root = Path(__file__).resolve().parents[1]
torch.set_num_threads(2)
stages = ['upstream-model', 'models/n16-base', 'models/n32-base',
          'models/n16-qat-v3/final', 'models/n32-qat-v3/final',
          'models/n16-v4-round1-step11428', 'models/n32-v4-round1-step11882']
ap=argparse.ArgumentParser();ap.add_argument('--stages',nargs='+');args=ap.parse_args()
if args.stages:stages=args.stages
questions = [json.loads(s)['question'] for s in (root/'data/test.jsonl').read_text().splitlines()]
for stage in stages:
    src = root/stage
    tok = AutoTokenizer.from_pretrained(src)
    m = Qwen3ForCausalLM.from_pretrained(src, dtype=torch.float32).eval()
    rows = []
    for q in questions:
        prompt = f'<|im_start|>user\n{q}<|im_end|>\n<|im_start|>assistant\n'
        ids = tok.encode(prompt, add_special_tokens=False, return_tensors='pt')
        with torch.no_grad():
            out = m.generate(ids, max_new_tokens=96, do_sample=False, eos_token_id=2, pad_token_id=3)
        rows.append({'question':q, 'prompt_tokens':ids.shape[1],
                     'answer':tok.decode(out[0,ids.shape[1]:],skip_special_tokens=True)})
    path = root/'eval'/('round2-'+stage.replace('/','-')+'.json')
    path.write_text(json.dumps({'stage':stage,'weights':'FP32','kv':'FP32',
        'model_sha256':hashlib.sha256((src/'model.safetensors').read_bytes()).hexdigest(),
        'question_sha256':hashlib.sha256((root/'data/test.jsonl').read_bytes()).hexdigest(),
        'suite_role':'development, already used in earlier iterations; not independent accuracy',
        'rows':rows,'physical_board_test':False},ensure_ascii=False,indent=2))
    print(stage, 'complete', flush=True)
    del m
