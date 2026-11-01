"""BLADE LoRA v3/v4 on RunPod: one (data version, seed) run = train -> save final adapter -> test_v30 predictions (oas, oas_code)
-> test_v31_supp predictions (oas, oas_code) when <base>/data_v4 is present.

Usage (inside tmux, see run_all.sh / README_runpod_v4.md):
    python run_train.py --data v4 --seed 42 [--base /workspace/blade_lora_v3]
    python run_train.py --data v2 --seed 43      # RunPod baseline: data-v2 (s42 already exists)
    python run_train.py --data v3b --seed 42 --eval-only   # existing adapter: add the test_v31_supp predictions only
    python run_train.py --data base --seed 0     # base model without adapter (evaluation only)
    python run_train.py --data v4 --seed 42 --eval-only --decoding stable            # task B: re-evaluate with the stabilised decoding (DECODING), no training
    python run_train.py --data base --seed 0 --eval-only --decoding stable --limit 8  # smoke test: 8 rows per job into eval_stable_smoke/, not scored
    python run_train.py --data v5 --seed 42                     # task C-4: LoRA v5 (data-v5) train + test_v30 / test_v31_supp (+ test_v5 once frozen, see TESTV5)
    python run_train.py --data v4 --seed 42 --eval-only --jobs v5test   # existing v4 adapter: add the test_v5 predictions only (test_v30/supp predictions already exported)
Inputs: <base>/data_v3/ (train_sft_v3a.jsonl, train_sft_v3b.jsonl, val_sft_v3.jsonl, test_v30_inputs.jsonl, policy_label_v3.0.1.md, data_v3_hashes.json)
        and, for --data v2, <base>/data_v2/ (train_sft.jsonl, val_sft.jsonl, test_v30_inputs.jsonl, policy_label_v3.0.1.md, data_v2_hashes.json).
Outputs: <base>/runs/<run>/{config.json, env.json, logs/run.log, logs/train_log.jsonl, logs/train_result.json, adapter/, checkpoints/, eval/predictions_<cond>_<tag>.jsonl}
         with run/tag = lora_v3a_s<seed> / lora_v3a_s<seed>_final, lora_v3b_..., lora_v2_s<seed>_runpod / lora_v2_s<seed>_runpod_final.
Experiment rules (AGENTS.md 'data-v3 실험 규칙'): final adapter only (no checkpoint selection), no abstention-threshold tuning, hyperparameters = LoRA v2,
val is a training sanity check only. Resumable: an existing final adapter skips training, existing prediction files skip evaluation. No API keys or tokens."""
import argparse, glob, hashlib, json, logging, os, re, sys, time

HP = dict(base_model='unsloth/Qwen2.5-7B-Instruct-bnb-4bit', max_seq_len=4096, lora_r=16, lora_alpha=16, lora_dropout=0.0,
          target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj'], epochs=3, lr=2e-4, batch=2, grad_acc=4,
          warmup_steps=10, weight_decay=0.01, lr_scheduler='cosine', save_steps=30, eval_steps=30, eval_max_new_tokens=256, eval_batch=8,
          prompt_version='policy-label-v3.0.1')   # identical to LoRA v2 (training/lora/build_notebook_v2.py)
# hashes: SHA-256 of the frozen hash manifest (data_v3_hashes.json: git tags data-v3a / data-v3b; data_v2_hashes.json: tag data-v2). The run stops if it differs.
DATASETS = {
    'v3a': dict(dir='data_v3', train='train_sft_v3a.jsonl', val='val_sft_v3.jsonl', hashes='data_v3_hashes.json', sha='100b8c732c5a60e4704a6ed54de8f18634f373d42abeb4854f6237ec026c1bf7', run='lora_v3a_s{seed}', tag='lora_v3a_s{seed}_final'),
    'v3b': dict(dir='data_v3', train='train_sft_v3b.jsonl', val='val_sft_v3.jsonl', hashes='data_v3_hashes.json', sha='100b8c732c5a60e4704a6ed54de8f18634f373d42abeb4854f6237ec026c1bf7', run='lora_v3b_s{seed}', tag='lora_v3b_s{seed}_final'),
    'v2': dict(dir='data_v2', train='train_sft.jsonl', val='val_sft.jsonl', hashes='data_v2_hashes.json', sha='ba10df85e40ef254752d5bb2e6fff7cebdd6d41073fa61d07eec6a7ed0328715',
               run='lora_v2_s{seed}_runpod', tag='lora_v2_s{seed}_runpod_final'),
    'v4': dict(dir='data_v4', train='train_sft_v4.jsonl', val='val_sft_v4.jsonl', hashes='data_v4_hashes.json', sha='df24db709d1922fadf2a7e7f6f5931ff75ff4310208804cfa8fb70a117ad0867', run='lora_v4_s{seed}', tag='lora_v4_s{seed}_final'),
    # data-v5 (AGENTS.md 'data-v5 동결' 2026-10-31): data-v4 SFT rows byte-identical + 296 train / 32 val code-rule additions (Dendrite, NodeBB, Taiga). HP, prompt unchanged.
    'v5': dict(dir='data_v5', train='train_sft_v5.jsonl', val='val_sft_v5.jsonl', hashes='data_v5_hashes.json', sha='39c302c5fb33d1b1506487678cd15f40cc83ffd59435449522786388554753ac', run='lora_v5_s{seed}', tag='lora_v5_s{seed}_final'),
    # evaluation only: the base model without an adapter (same RunPod environment as the LoRA runs)
    'base': dict(dir='data_v4', train=None, val=None, hashes='data_v4_hashes.json', sha='df24db709d1922fadf2a7e7f6f5931ff75ff4310208804cfa8fb70a117ad0867', run='base_qwen_runpod', tag='base_qwen_runpod'),
}
# test_v31_supp (separate evaluation condition, AGENTS.md 'test_v31_supp 검수 규약'): every run also predicts it when <base>/data_v4 is present.
SUPP = dict(dir='data_v4', file='test_v31_supp_inputs.jsonl', hashes='data_v4_hashes.json', sha='df24db709d1922fadf2a7e7f6f5931ff75ff4310208804cfa8fb70a117ad0867')
# test_v5 (hold-out, AGENTS.md 작업 C). Gate required by the order change (user decision 2026-10-31: data-v5 was frozen before test_v5, with no test_v5 label read):
# TESTV5['sha'] must be the SHA-256 of data_v5/test_v5_manifest.json written by scripts/build_test_v5.py freeze. While it is None, or the manifest/inputs are absent
# or differ, NO test_v5 prediction job is created (test_v30 / test_v31_supp jobs run as usual). test_v5_inputs.jsonl is deliberately not in data_v5_hashes.json.
TESTV5 = dict(dir='data_v5', file='test_v5_inputs.jsonl', manifest='test_v5_manifest.json', sha='57fd384f46e89e905209e627a7ff7fb9f312e22a7bed222639e91a80bd05fccd', key='training/lora/data_v5/test_v5_inputs.jsonl')
LABELS = ['public', 'role_required', 'membership_required', 'tenant_match', 'owner_match', 'owner_or_admin', 'manual_review_required']
# Decoding settings (task B, reports/eval/stable_decoding). Fixed before any result was seen. 'default' = the LoRA v2/v3/v4 evaluation setting (greedy, no penalty,
# no constraint). 'stable' changes exactly two things: repetition_penalty 1.1 and JSON-schema constrained decoding (label = 7-value enum) via lm-format-enforcer.
# Everything else (greedy, max_new_tokens 256, eval_batch 8, left padding, adapters, prompt, inputs) is identical. Stable outputs go to <run>/eval_stable/ with the
# tag suffix _stable, so the default files are never touched and resume logic keeps working. A truncated (256-token) rationale still counts as an output error.
DECODING = {'default': dict(repetition_penalty=None, schema=False, enforcer=None),
            'stable': dict(repetition_penalty=1.1, schema=True, enforcer='lm-format-enforcer')}
SCHEMA = {'type': 'object', 'properties': {'label': {'enum': LABELS}, 'confidence': {'type': 'number'}, 'rationale': {'type': 'string'},
                                           'evidence_fields': {'type': 'array', 'items': {'type': 'string'}}}, 'required': ['label']}


def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def read(p): return [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]


def verify(data_dir, ds, log):
    hj = f"{data_dir}/{ds['hashes']}"
    assert sha(hj) == ds['sha'], f"{ds['hashes']} differs from the frozen one: {sha(hj)}"
    gen = json.load(open(hj, encoding='utf-8'))['generated']
    bad = {n: sha(f'{data_dir}/{n}') for n, h in gen.items() if sha(f'{data_dir}/{n}') != h}
    assert not bad, f'input hash mismatch, stop: {bad}'
    log.info('inputs verified against %s (%d files)', ds['hashes'], len(gen))


def messages(system, user, assistant=None):
    m = [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}]
    if assistant is not None: m.append({'role': 'assistant', 'content': assistant})
    return m


def parse(text):
    m = re.search(r'\{.*\}', text, re.S)
    try:
        o = json.loads(m.group(0)) if m else None
        return o if isinstance(o, dict) and o.get('label') in LABELS else None
    except Exception: return None


def schema_prefix_fn(tok, log):
    """prefix_allowed_tokens_fn for model.generate() that restricts output to SCHEMA (lm-format-enforcer TokenEnforcer).
    The library's transformers integration imports modules that moved in transformers 5.x; if that import fails the same tokenizer data is built here."""
    from lmformatenforcer import JsonSchemaParser, TokenEnforcer
    from lmformatenforcer.tokenenforcer import TokenEnforcerTokenizerData
    try:
        from lmformatenforcer.integrations.transformers import build_token_enforcer_tokenizer_data
        td = build_token_enforcer_tokenizer_data(tok); how = 'lmformatenforcer.integrations.transformers'
    except ImportError as e:
        log.warning('lm-format-enforcer transformers integration unavailable (%s): building the tokenizer data directly (same construction)', e)
        vocab = len(tok); t0 = tok.encode('0')[-1]; special = set(tok.all_special_ids); reg = []
        for i in range(vocab):
            if i in special: continue
            after0 = tok.decode([t0, i])[1:]; plain = tok.decode([i]); reg.append((i, after0, len(after0) > len(plain)))
        td = TokenEnforcerTokenizerData(reg, lambda ids: tok.decode(ids).rstrip('�'), tok.eos_token_id, False, vocab); how = 'direct'
    enf = TokenEnforcer(td, JsonSchemaParser(SCHEMA))
    return (lambda batch_id, sent: enf.get_allowed_tokens(sent.tolist()).allowed_tokens), how, len(td.tokenizer_alphabet)


def train(args, run, system, log):
    import torch
    from unsloth import FastLanguageModel
    from unsloth.chat_templates import train_on_responses_only
    from trl import SFTTrainer, SFTConfig
    from datasets import Dataset
    train_rows, val_rows = read(f"{args.data_dir}/{args.ds['train']}"), read(f"{args.data_dir}/{args.ds['val']}")
    model, tok = FastLanguageModel.from_pretrained(model_name=HP['base_model'], max_seq_length=HP['max_seq_len'], dtype=None, load_in_4bit=True)
    model = FastLanguageModel.get_peft_model(model, r=HP['lora_r'], lora_alpha=HP['lora_alpha'], lora_dropout=HP['lora_dropout'], target_modules=HP['target_modules'],
                                             bias='none', use_gradient_checkpointing='unsloth', random_state=args.seed)
    to_ds = lambda rows: Dataset.from_list([{'text': tok.apply_chat_template(messages(system, r['user'], r['assistant']), tokenize=False)} for r in rows])
    train_ds = to_ds(train_rows); val_oas = to_ds([r for r in val_rows if r['condition'] == 'oas']); val_code = to_ds([r for r in val_rows if r['condition'] == 'oas_code'])
    log.info('train %d, val oas %d / oas_code %d', len(train_ds), len(val_oas), len(val_code))
    cfg = SFTConfig(output_dir=f'{run}/checkpoints', per_device_train_batch_size=HP['batch'], gradient_accumulation_steps=HP['grad_acc'], num_train_epochs=HP['epochs'], learning_rate=HP['lr'],
                    warmup_steps=HP['warmup_steps'], weight_decay=HP['weight_decay'], lr_scheduler_type=HP['lr_scheduler'], seed=args.seed, logging_steps=5,
                    save_steps=HP['save_steps'], save_total_limit=2,   # checkpoints only for resuming after a disconnect; the experiment uses the final adapter
                    eval_strategy='steps', eval_steps=HP['eval_steps'], per_device_eval_batch_size=1, bf16=torch.cuda.is_bf16_supported(), fp16=not torch.cuda.is_bf16_supported(),
                    optim='adamw_8bit', report_to='none', max_seq_length=HP['max_seq_len'], dataset_text_field='text', packing=False)
    trainer = SFTTrainer(model=model, tokenizer=tok, train_dataset=train_ds, eval_dataset={'oas': val_oas, 'oas_code': val_code}, args=cfg)
    trainer = train_on_responses_only(trainer, instruction_part='<|im_start|>user\n', response_part='<|im_start|>assistant\n')
    ckpts = sorted(glob.glob(f'{run}/checkpoints/checkpoint-*'), key=lambda p: int(p.rsplit('-', 1)[1])); resume = ckpts[-1] if ckpts else None
    log.info('training (resume from %s)', resume); t0 = time.time()
    res = trainer.train(resume_from_checkpoint=resume)
    model.save_pretrained(f'{run}/adapter'); tok.save_pretrained(f'{run}/adapter')
    with open(f'{run}/logs/train_log.jsonl', 'w') as f:
        for e in trainer.state.log_history: f.write(json.dumps(e) + '\n')
    ev = {c: [(e['step'], e[f'eval_{c}_loss']) for e in trainer.state.log_history if f'eval_{c}_loss' in e] for c in ('oas', 'oas_code')}
    out = dict(res.metrics, resumed_from=resume, steps=trainer.state.global_step, minutes=round((time.time() - t0) / 60, 1), eval_loss_by_condition=ev,
               note='val is a sanity check only; the final adapter is evaluated regardless of val loss')
    json.dump(out, open(f'{run}/logs/train_result.json', 'w'), indent=2)
    losses = [e['loss'] for e in trainer.state.log_history if 'loss' in e]
    assert losses and all(l == l and l < 50 for l in losses), f'training loss abnormal (nan/divergent): {losses[-5:]}'
    log.info('train done: %s', {k: v for k, v in out.items() if k != 'eval_loss_by_condition'})
    del model, trainer; torch.cuda.empty_cache()


def supp_rows(args, log):
    d = f"{args.base}/{SUPP['dir']}"; p = f"{d}/{SUPP['file']}"
    if not os.path.exists(p): log.info('test_v31_supp inputs not present: skipped'); return None
    hj = f"{d}/{SUPP['hashes']}"; assert sha(hj) == SUPP['sha'], f"{SUPP['hashes']} differs from the frozen one"
    assert sha(p) == json.load(open(hj, encoding='utf-8'))['generated'][SUPP['file']], 'test_v31_supp inputs hash mismatch, stop'
    return read(p)


def testv5_rows(args, log):
    d = f"{args.base}/{TESTV5['dir']}"; p = f"{d}/{TESTV5['file']}"; mj = f"{d}/{TESTV5['manifest']}"
    if not TESTV5['sha']: log.info('test_v5 not frozen (TESTV5 sha unset): test_v5 evaluation skipped'); return None
    if not (os.path.exists(p) and os.path.exists(mj)): log.info('test_v5 inputs or manifest not present: test_v5 evaluation skipped'); return None
    assert sha(mj) == TESTV5['sha'], f"{TESTV5['manifest']} differs from the frozen one: {sha(mj)}"
    assert sha(p) == json.load(open(mj, encoding='utf-8'))['sha256'][TESTV5['key']], 'test_v5 inputs hash mismatch, stop'
    log.info('test_v5 inputs verified against %s (%s)', TESTV5['manifest'], TESTV5['sha'][:12]); return read(p)


def evaluate(args, run, system, tag, log):
    import torch
    from unsloth import FastLanguageModel
    from peft import PeftModel
    # test_v30 files keep the predictions_<cond>_<tag> name (scripts/eval_v30.py); test_v31_supp files are supp_predictions_<cond>_<tag> (scripts/eval_v31_supp.py)
    # --decoding stable: same names under <run>/eval_stable/ with tag suffix _stable (scorers group seeds by the _s<seed> part, so the suffix is harmless).
    # --limit N (smoke test): first N rows of every job, written under <run>/<eval_dir>_smoke/, always overwritten, never scored or exported.
    dec = DECODING[args.decoding]; eval_dir = 'eval' if args.decoding == 'default' else f'eval_{args.decoding}'
    if args.limit: eval_dir += '_smoke'
    os.makedirs(f'{run}/{eval_dir}', exist_ok=True)
    jobs = []
    if args.jobs == 'all':   # --jobs v5test: only the test_v5 jobs (eval-only addition for the exported v4 / base runs; their test_v30 / supp predictions are not recomputed)
        jobs = [(f'{run}/{eval_dir}/predictions_{c}_{tag}.jsonl', k, read(f'{args.data_dir}/test_v30_inputs.jsonl')) for c, k in (('oas', 'oas_user'), ('oas_code', 'oas_code_user'))]
        supp = supp_rows(args, log)
        if supp is not None: jobs += [(f'{run}/{eval_dir}/supp_predictions_{c}_{tag}.jsonl', k, supp) for c, k in (('oas', 'oas_user'), ('oas_code', 'oas_code_user'))]
    t5 = testv5_rows(args, log)   # files: v5test_predictions_<cond>_<tag>.jsonl (scripts/eval_test_v5.py)
    if t5 is not None: jobs += [(f'{run}/{eval_dir}/v5test_predictions_{c}_{tag}.jsonl', k, t5) for c, k in (('oas', 'oas_user'), ('oas_code', 'oas_code_user'))]
    elif args.jobs == 'v5test': raise SystemExit('--jobs v5test but test_v5 is not frozen / not present (TESTV5)')
    if not args.limit:
        for j in jobs:
            if os.path.exists(j[0]): log.info('skip %s (exists)', j[0])
        jobs = [j for j in jobs if not os.path.exists(j[0])]
    if not jobs: return
    base, tok = FastLanguageModel.from_pretrained(model_name=HP['base_model'], max_seq_length=HP['max_seq_len'], dtype=None, load_in_4bit=True)
    model = PeftModel.from_pretrained(base, f'{run}/adapter') if args.data != 'base' else base; FastLanguageModel.for_inference(model)
    gen_kw = dict(max_new_tokens=HP['eval_max_new_tokens'], do_sample=False, temperature=None, top_p=None, pad_token_id=tok.pad_token_id)
    if dec['repetition_penalty']: gen_kw['repetition_penalty'] = dec['repetition_penalty']
    if dec['schema']:
        t0 = time.perf_counter(); gen_kw['prefix_allowed_tokens_fn'], how, alpha = schema_prefix_fn(tok, log)
        log.info('decoding=%s: %s, schema-constrained via lm-format-enforcer [%s] (tokenizer data built in %.1fs, alphabet %d chars)', args.decoding, {k: v for k, v in dec.items() if k != 'schema'}, how, time.perf_counter() - t0, alpha)
    else: log.info('decoding=%s: %s', args.decoding, dec)
    for path, key, test_rows in jobs:
        cond = 'oas_code' if key == 'oas_code_user' else 'oas'
        rows = [r for r in test_rows if key in r][:args.limit or None]; outs = []
        for i in range(0, len(rows), HP['eval_batch']):   # same batched greedy decoding as LoRA v2 (left padding for generation)
            batch = rows[i:i + HP['eval_batch']]; prompts = [tok.apply_chat_template(messages(system, r[key]), tokenize=False, add_generation_prompt=True) for r in batch]
            tok.padding_side = 'left'; enc = tok(prompts, return_tensors='pt', padding=True, truncation=True, max_length=HP['max_seq_len']).to('cuda'); t0 = time.perf_counter()
            with torch.no_grad(): gen = model.generate(**enc, **gen_kw)
            ms = (time.perf_counter() - t0) * 1000 / len(batch)
            for j in range(len(batch)):
                text = tok.decode(gen[j][enc.input_ids.shape[1]:], skip_special_tokens=True); outs.append(dict(raw=text, parsed=parse(text), inference_ms=round(ms, 1)))
        tmp = path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            for r, o in zip(rows, outs):
                f.write(json.dumps(dict(id=r['id'], label=r['label'], source=r['source'], security_state=r['security_state'], prediction=o['parsed'], raw=o['raw'], inference_ms=o['inference_ms']), ensure_ascii=False) + '\n')
        os.replace(tmp, path)
        log.info('%s %s%s: %d rows, parse errors %d, manual %d, mean %.0f ms/row%s', tag, 'supp ' if '/supp_' in path else 'v5test ' if '/v5test_' in path else '', cond, len(rows), sum(o['parsed'] is None for o in outs),
                 sum(bool(o['parsed']) and o['parsed']['label'] == 'manual_review_required' for o in outs), sum(o['inference_ms'] for o in outs) / max(1, len(outs)), ' [SMOKE]' if args.limit else '')
    del model, base; torch.cuda.empty_cache()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', choices=sorted(DATASETS), required=True); ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--base', default='/workspace/blade_lora_v3'); ap.add_argument('--skip-eval', action='store_true')
    ap.add_argument('--eval-only', action='store_true', help='never train: evaluate an existing final adapter (adds missing prediction files, e.g. test_v31_supp)')
    ap.add_argument('--decoding', choices=sorted(DECODING), default='default', help='evaluation decoding setting (see DECODING); stable = task B output stabilisation')
    ap.add_argument('--limit', type=int, default=0, help='smoke test: evaluate only the first N rows per job into <run>/<eval_dir>_smoke/ (not scored, not exported)')
    ap.add_argument('--jobs', choices=['all', 'v5test'], default='all', help='v5test = only the test_v5 prediction jobs (requires the frozen test_v5, see TESTV5)')
    args = ap.parse_args(); args.ds = ds = DATASETS[args.data]; args.data_dir = f"{args.base}/{ds['dir']}"
    if args.decoding != 'default': assert args.eval_only or args.data == 'base', '--decoding stable is an evaluation-only setting: use it with --eval-only (training is unchanged)'
    tag = ds['tag'].format(seed=args.seed) + ('' if args.decoding == 'default' else f'_{args.decoding}'); run = f"{args.base}/runs/{ds['run'].format(seed=args.seed)}"
    for d in ('checkpoints', 'adapter', 'logs', 'eval'): os.makedirs(f'{run}/{d}', exist_ok=True)
    logname = 'run.log' if args.decoding == 'default' else f'run_{args.decoding}.log'   # stable evaluations log separately so the original run.log stays as exported
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', handlers=[logging.FileHandler(f'{run}/logs/{logname}', encoding='utf-8'), logging.StreamHandler(sys.stdout)])
    log = logging.getLogger('blade'); log.info('run %s data=%s seed=%d base=%s decoding=%s limit=%d', tag, args.data, args.seed, args.base, args.decoding, args.limit)
    verify(args.data_dir, ds, log)
    import torch, transformers, trl, peft
    try: import unsloth; uv = unsloth.__version__
    except Exception as e: uv = repr(e)
    env = dict(gpu=torch.cuda.get_device_name(0), vram_gb=torch.cuda.get_device_properties(0).total_memory // 2**30, torch=torch.__version__, transformers=transformers.__version__,
               trl=trl.__version__, peft=peft.__version__, unsloth=uv, python=sys.version.split()[0])
    cfg = dict(HP, data=args.data, seed=args.seed, train_file=ds['train'], val_file=ds['val'], tag=tag, decoding=args.decoding, decoding_settings=DECODING[args.decoding], schema=SCHEMA if DECODING[args.decoding]['schema'] else None)
    if args.decoding == 'default': json.dump(env, open(f'{run}/env.json', 'w'), indent=2); json.dump(cfg, open(f'{run}/config.json', 'w'), indent=2)
    else: json.dump(env, open(f'{run}/env_{args.decoding}.json', 'w'), indent=2); json.dump(cfg, open(f'{run}/config_{args.decoding}.json', 'w'), indent=2)   # the exported originals are kept as they were
    log.info('env %s', env)
    system = open(f'{args.data_dir}/policy_label_v3.0.1.md', encoding='utf-8').read()
    if args.data == 'base': log.info('base model: no training')
    elif os.path.exists(f'{run}/adapter/adapter_model.safetensors') and (args.eval_only or os.path.exists(f'{run}/logs/train_result.json')): log.info('final adapter exists: skip training')   # eval-only pods (new_pod.sh) restore adapter/ only, without logs/train_result.json
    elif args.eval_only: raise SystemExit(f'--eval-only but no final adapter in {run}/adapter (restore it from blade_v4_adapters.tar.gz)')
    else: train(args, run, system, log)
    if not args.skip_eval: evaluate(args, run, system, tag, log)
    log.info('done %s', tag)


if __name__ == '__main__': main()
