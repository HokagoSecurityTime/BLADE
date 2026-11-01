"""Run the Ollama-served LoRA v5 model (blade-qwen-lora-v5, seed 42 final merged, GGUF Q4_K_M) on frozen inputs, in the run_train.py prediction format.
C-5 (AGENTS.md 작업 C), derived from eval_ollama_v4.py; the only changes are the data-v5 paths/hashes, the default model name and the --data-dir/--prompt overrides for RunPod.

--split test: test_v30 oas_code condition only (GGUF conversion equivalence check against the HF s42 final predictions; nothing is tuned on it).
--split val:  val_sft_v5 (oas + oas_code rows; used only to choose the pipeline confidence threshold, choose_threshold_v4.py --rule precision).
Same decoding as run_train.py evaluate(): system = prompt v3.0.1, greedy, max 256 new tokens, same parse().
Requests go through /api/chat, so the Modelfile TEMPLATE is what the pipeline will use. --check-template also renders the
HF chat template from the adapter tokenizer and sends it raw for the first N rows; prompt token counts must be identical.
Resumable: finished ids in <out>.partial are skipped.

Usage: python -X utf8 training/lora/eval_ollama_v5.py --split test --out reports/eval/lora_v5_gguf/predictions_oas_code_lora_v5_s42_gguf_q4km.jsonl
RunPod: python eval_ollama_v5.py --split test --data-dir data_v5 --prompt data_v5/policy_label_v3.0.1.md --check-template 3 --tokenizer runs/lora_v5_s42/adapter --out export/gguf_eval/...
"""
import argparse, hashlib, json, os, re, sys, time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
HASHES_SHA = '39c302c5fb33d1b1506487678cd15f40cc83ffd59435449522786388554753ac'   # data_v5_hashes.json (AGENTS.md data-v5)
PROMPT_SHA = 'd0913c27b5de185e7dd5734c111cb731f45e28ebca81fed787ff3914d02833ef'
LABELS = {'public', 'role_required', 'membership_required', 'tenant_match', 'owner_match', 'owner_or_admin', 'manual_review_required'}
OPTIONS = dict(temperature=0, num_predict=256)


def sha(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()


def parse(text: str):   # identical to run_train.py
    m = re.search(r'\{.*\}', text, re.S)
    try:
        o = json.loads(m.group(0)) if m else None
        return o if isinstance(o, dict) and o.get('label') in LABELS else None
    except Exception: return None


def rows(data: Path, split: str) -> list[dict]:
    hashes = data / 'data_v5_hashes.json'
    assert sha(hashes) == HASHES_SHA, 'data_v5_hashes.json hash mismatch, stop'
    gen = json.loads(hashes.read_text(encoding='utf-8'))['generated']
    name = 'test_v30_inputs.jsonl' if split == 'test' else 'val_sft_v5.jsonl'
    assert sha(data / name) == gen[name], f'{name} hash mismatch, stop'
    raw = [json.loads(l) for l in open(data / name, encoding='utf-8') if l.strip()]
    if split == 'test':
        return [dict(id=r['id'], label=r['label'], source=r['source'], security_state=r['security_state'], user=r['oas_code_user']) for r in raw if 'oas_code_user' in r]
    return [dict(id=r['id'], label=r['label'], source=r['source'], security_state=r['security_state'], condition=r['condition'], user=r['user']) for r in raw]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--split', choices=['test', 'val'], required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--model', default='blade-qwen-lora-v5')
    ap.add_argument('--url', default=os.getenv('BLADE_OLLAMA_URL', 'http://127.0.0.1:11434'))
    ap.add_argument('--data-dir', type=Path, default=ROOT / 'training/lora/data_v5', help='dir with data_v5_hashes.json, test_v30_inputs.jsonl, val_sft_v5.jsonl')
    ap.add_argument('--prompt', type=Path, default=None, help='policy_label_v3.0.1.md (default: <data-dir>/policy_label_v3.0.1.md); hash asserted')
    ap.add_argument('--check-template', type=int, default=0, metavar='N')
    ap.add_argument('--tokenizer', help='adapter dir (HF tokenizer + chat template) for --check-template')
    args = ap.parse_args()
    prompt = args.prompt or args.data_dir / 'policy_label_v3.0.1.md'
    assert sha(prompt) == PROMPT_SHA, 'prompt v3.0.1 hash mismatch, stop'
    system = prompt.read_text(encoding='utf-8')
    data = rows(args.data_dir, args.split)
    client = httpx.Client(timeout=1800)

    def chat(user: str) -> dict:
        r = client.post(f'{args.url}/api/chat', json=dict(model=args.model, stream=False, options=OPTIONS,
                        messages=[dict(role='system', content=system), dict(role='user', content=user)]))
        r.raise_for_status(); return r.json()

    if args.check_template:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(args.tokenizer)
        for r in data[:args.check_template]:
            text = tok.apply_chat_template([dict(role='system', content=system), dict(role='user', content=r['user'])], tokenize=False, add_generation_prompt=True)
            raw = client.post(f'{args.url}/api/generate', json=dict(model=args.model, prompt=text, raw=True, stream=False, options=OPTIONS)).json()
            via_chat = chat(r['user'])
            hf_tokens = len(tok(text).input_ids)
            # Token count proves the rendered prompt is identical. Output equality is only reported: greedy decoding
            # can differ by KV-cache state (which prefix was cached before), independent of the template.
            print(json.dumps(dict(id=r['id'], hf_prompt_tokens=hf_tokens, raw_prompt_tokens=raw['prompt_eval_count'],
                                  chat_prompt_tokens=via_chat['prompt_eval_count'],
                                  same_output=raw['response'] == via_chat['message']['content']), ensure_ascii=False), flush=True)
            assert hf_tokens == raw['prompt_eval_count'] == via_chat['prompt_eval_count'], 'Modelfile TEMPLATE renders a different prompt, stop'

    args.out.parent.mkdir(parents=True, exist_ok=True)
    partial = args.out.with_suffix(args.out.suffix + '.partial')
    done = {json.loads(l)['id']: json.loads(l) for l in open(partial, encoding='utf-8')} if partial.exists() else {}
    with open(partial, 'a', encoding='utf-8') as f:
        for i, r in enumerate(data):
            if r['id'] in done: continue
            t0 = time.perf_counter(); res = chat(r['user']); ms = (time.perf_counter() - t0) * 1000
            text = res['message']['content']
            rec = dict({k: v for k, v in r.items() if k != 'user'}, prediction=parse(text), raw=text, inference_ms=round(ms, 1),
                       done_reason=res.get('done_reason'), prompt_eval_count=res.get('prompt_eval_count'), eval_count=res.get('eval_count'))
            f.write(json.dumps(rec, ensure_ascii=False) + '\n'); f.flush(); done[r['id']] = rec
            print(f'{i + 1}/{len(data)} {r["id"]} {(rec["prediction"] or {}).get("label")} {ms / 1000:.1f}s', flush=True)
    with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
        for r in data: f.write(json.dumps(done[r['id']], ensure_ascii=False) + '\n')
    partial.unlink()
    errors = sum(done[r['id']]['prediction'] is None for r in data)
    print(f'done {len(data)} rows, parse errors {errors}, mean {sum(done[r["id"]]["inference_ms"] for r in data) / len(data) / 1000:.1f}s/row')


if __name__ == '__main__':
    sys.exit(main())
