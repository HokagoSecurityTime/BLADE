"""BLADE LoRA v7 on RunPod (task data-v7): LoRA v5 recipe, training data = data-v7 (AGENTS.md "작업 data-v7").
  base unsloth/Qwen2.5-7B-Instruct-bnb-4bit, prompt v3.0.1, assistant JSON order label-first, max_seq_len 4096, max_new_tokens 256, LoRA r16/alpha16/dropout 0, 3 epochs,
  lr 2e-4, cosine, warmup 10, adamw_8bit, batch 2 x grad_acc 4, completion-only loss (train_on_responses_only), greedy, eval_batch 8 — identical to run_train.py (v5).
EVALUATION SCOPE (pre-registered): test_v30 only (oas, oas_code). test_v31_supp and test_v5 are TRAINING data in data-v7 and are never evaluated here (no SUPP/TESTV5 jobs).
test_v6 (hold-out for S9) is evaluated only after its freeze, through the TESTV6 manifest gate below (sha None = skipped), with --jobs v6test.
Usage:
    python run_train_v7.py --data v7 --seed 42 [--base /workspace/blade_lora_v3]   # train (resumes from the last checkpoint) + test_v30 predictions
    python run_train_v7.py --data v7 --seed 42 --eval-only                         # existing final adapter: missing/unfinished test_v30 prediction files only
    python run_train_v7.py --data v7 --seed 42 --preflight                         # base load + short generate + memory, no training
    python run_train_v7.py --data v7 --seed 42 --eval-only --jobs v6test           # S9 only: test_v6 predictions (requires the frozen manifest hash in TESTV6)
Outputs: <base>/runs/lora_v7_s<seed>/{config.json, env.json, logs/, adapter/, checkpoints/, eval/predictions_<cond>_lora_v7_s<seed>_final.jsonl (+ .timing.json)}.
No API keys or tokens."""
import argparse, glob, hashlib, json, logging, os, re, sys, time

HP = dict(base_model='unsloth/Qwen2.5-7B-Instruct-bnb-4bit', max_seq_len=4096, lora_r=16, lora_alpha=16, lora_dropout=0.0,
          target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj'], epochs=3, lr=2e-4, batch=2, grad_acc=4,
          warmup_steps=10, weight_decay=0.01, lr_scheduler='cosine', save_steps=30, eval_steps=30, eval_max_new_tokens=256, eval_batch=8,
          prompt_version='policy-label-v3.0.1', prompt_file='policy_label_v3.0.1.md', changed_vs_v5=dict(data='data-v5 -> data-v7 (training labels/rows only; see data_v7_hashes.json)'))
DATASETS = {
    'v7': dict(dir='data_v7', train='train_sft_v7.jsonl', val='val_sft_v7.jsonl', hashes='data_v7_hashes.json', sha='bd33f1bcf0f68ab5fe5b96195c0da3cf6affbb3486fb85bef542b3f77e88ba73', run='lora_v7_s{seed}', tag='lora_v7_s{seed}_final'),
    # S9 only (eval-only, --jobs v6test): the existing LoRA v5 final adapters restored to runs/lora_v5_s<seed>/adapter (blade_v5_adapters.tar.gz db6abe46…), inferred on test_v6 in the same pod/libraries as v7
    'v5': dict(dir='data_v7', train=None, val=None, hashes='data_v7_hashes.json', sha='bd33f1bcf0f68ab5fe5b96195c0da3cf6affbb3486fb85bef542b3f77e88ba73', run='lora_v5_s{seed}', tag='lora_v5_s{seed}_final'),
    # S9-base (reference only, after the S9 verdict; no adapter): base unsloth/Qwen2.5-7B-Instruct-bnb-4bit zero-shot on test_v6, prompt v3.0.1, greedy — single run (--seed 0)
    'base': dict(dir='data_v7', train=None, val=None, hashes='data_v7_hashes.json', sha='bd33f1bcf0f68ab5fe5b96195c0da3cf6affbb3486fb85bef542b3f77e88ba73', run='base_qwen7b_s9', tag='base_qwen7b_s9', no_adapter=True),
}
# test_v6 gate (S9): set sha to the SHA-256 of data_v7/test_v6_manifest.json written at the test_v6 freeze. While None, or manifest/inputs absent or different, NO test_v6 job runs.
# Frozen 2026-11-08 (A안, AGENTS.md "test_v6 동결"): manifest datasets/blade/processed/data_v6/test_v6_manifest.json SHA-256 a9ca4fca…, inputs 289 rows SHA-256 33d1aecd….
TESTV6 = dict(file='test_v6_inputs.jsonl', manifest='test_v6_manifest.json', sha='a9ca4fca05ee3e59226411c08c9f102440d5f36b2d4b45dc870bd74e346f3edc', key='training/lora/data_v6/test_v6_inputs.jsonl')
FORBIDDEN_EVAL = ('test_v31_supp_inputs.jsonl', 'test_v5_inputs.jsonl')   # training data in data-v7
LABELS = ['public', 'role_required', 'membership_required', 'tenant_match', 'owner_match', 'owner_or_admin', 'manual_review_required']


def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def read(p): return [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
def gib(b): return round(b / 2**30, 2)


def verify(data_dir, ds, log):
    hj = f"{data_dir}/{ds['hashes']}"
    assert sha(hj) == ds['sha'], f"{ds['hashes']} differs from the frozen one: {sha(hj)}"
    gen = json.load(open(hj, encoding='utf-8'))['generated']
    bad = {n: sha(f'{data_dir}/{n}') for n, h in gen.items() if sha(f'{data_dir}/{n}') != h}
    assert not bad, f'input hash mismatch, stop: {bad}'
    for n in FORBIDDEN_EVAL: assert not os.path.exists(f'{data_dir}/{n}'), f'{n} must not be in data_v7 (it is training data; never evaluated)'
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


def mem(log, what):
    import torch
    peak, res = torch.cuda.max_memory_allocated(), torch.cuda.max_memory_reserved()
    log.info('gpu memory %s: peak allocated %.2f GiB, peak reserved %.2f GiB', what, gib(peak), gib(res)); return dict(peak_allocated_gib=gib(peak), peak_reserved_gib=gib(res))


def load_base(log):
    import torch
    from unsloth import FastLanguageModel
    torch.cuda.reset_peak_memory_stats(); t0 = time.time()
    model, tok = FastLanguageModel.from_pretrained(model_name=HP['base_model'], max_seq_length=HP['max_seq_len'], dtype=None, load_in_4bit=True)
    cfg = model.config; log.info('base %s loaded in %.0fs: %d layers, hidden %d, allocated %.2f GiB', HP['base_model'], time.time() - t0, cfg.num_hidden_layers, cfg.hidden_size, gib(torch.cuda.memory_allocated()))
    return model, tok


def train(args, run, system, log):
    import torch
    from unsloth import FastLanguageModel
    from unsloth.chat_templates import train_on_responses_only
    from trl import SFTTrainer, SFTConfig
    from datasets import Dataset
    train_rows, val_rows = read(f"{args.data_dir}/{args.ds['train']}"), read(f"{args.data_dir}/{args.ds['val']}")
    model, tok = load_base(log)
    model = FastLanguageModel.get_peft_model(model, r=HP['lora_r'], lora_alpha=HP['lora_alpha'], lora_dropout=HP['lora_dropout'], target_modules=HP['target_modules'], bias='none', use_gradient_checkpointing='unsloth', random_state=args.seed)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad); log.info('LoRA trainable parameters: %d', trainable)
    to_ds = lambda rows: Dataset.from_list([{'text': tok.apply_chat_template(messages(system, r['user'], r['assistant']), tokenize=False)} for r in rows])
    train_ds = to_ds(train_rows); val_oas = to_ds([r for r in val_rows if r['condition'] == 'oas']); val_code = to_ds([r for r in val_rows if r['condition'] == 'oas_code'])
    lens = [len(tok(x['text']).input_ids) for x in train_ds]
    log.info('train %d, val oas %d / oas_code %d; train tokens max %d, > %d: %d', len(train_ds), len(val_oas), len(val_code), max(lens), HP['max_seq_len'], sum(l > HP['max_seq_len'] for l in lens))
    assert max(lens) <= HP['max_seq_len'], 'a training row exceeds max_seq_len (would be truncated): stop'
    cfg = SFTConfig(output_dir=f'{run}/checkpoints', per_device_train_batch_size=HP['batch'], gradient_accumulation_steps=HP['grad_acc'], num_train_epochs=HP['epochs'], learning_rate=HP['lr'],
                    warmup_steps=HP['warmup_steps'], weight_decay=HP['weight_decay'], lr_scheduler_type=HP['lr_scheduler'], seed=args.seed, logging_steps=5, save_steps=HP['save_steps'], save_total_limit=2,
                    eval_strategy='steps', eval_steps=HP['eval_steps'], per_device_eval_batch_size=1, bf16=torch.cuda.is_bf16_supported(), fp16=not torch.cuda.is_bf16_supported(),
                    optim='adamw_8bit', report_to='none', max_seq_length=HP['max_seq_len'], dataset_text_field='text', packing=False)
    trainer = SFTTrainer(model=model, tokenizer=tok, train_dataset=train_ds, eval_dataset={'oas': val_oas, 'oas_code': val_code}, args=cfg)
    trainer = train_on_responses_only(trainer, instruction_part='<|im_start|>user\n', response_part='<|im_start|>assistant\n')   # completion-only loss, as LoRA v5 (run_train.py:119)
    ex = trainer.train_dataset[0]; lab = ex.get('labels')
    if lab is not None: log.info('loss mask check (row 0): %d/%d tokens masked (-100), %d assistant tokens in loss', sum(x == -100 for x in lab), len(lab), sum(x != -100 for x in lab))
    pf = getattr(trainer.args, 'padding_free', None); log.info('SFTConfig padding_free=%s', pf)
    ckpts = sorted(glob.glob(f'{run}/checkpoints/checkpoint-*'), key=lambda p: int(p.rsplit('-', 1)[1])); resume = ckpts[-1] if ckpts else None
    log.info('training (resume from %s)', resume); torch.cuda.reset_peak_memory_stats(); t0 = time.time()
    res = trainer.train(resume_from_checkpoint=resume)
    model.save_pretrained(f'{run}/adapter'); tok.save_pretrained(f'{run}/adapter')
    with open(f'{run}/logs/train_log.jsonl', 'w') as f:
        for e in trainer.state.log_history: f.write(json.dumps(e) + '\n')
    ev = {c: [(e['step'], e[f'eval_{c}_loss']) for e in trainer.state.log_history if f'eval_{c}_loss' in e] for c in ('oas', 'oas_code')}
    out = dict(res.metrics, resumed_from=resume, steps=trainer.state.global_step, minutes=round((time.time() - t0) / 60, 1), eval_loss_by_condition=ev, gpu_memory=mem(log, 'training'), trainable_params=trainable, padding_free=pf,
               effective_batch=HP['batch'] * HP['grad_acc'], note='val is a sanity check only; the final adapter is evaluated regardless of val loss')
    json.dump(out, open(f'{run}/logs/train_result.json', 'w'), indent=2)
    losses = [e['loss'] for e in trainer.state.log_history if 'loss' in e]
    assert losses and all(l == l and l < 50 for l in losses), f'training loss abnormal (nan/divergent): {losses[-5:]}'
    log.info('train done: %s', {k: v for k, v in out.items() if k != 'eval_loss_by_condition'})
    del model, trainer; torch.cuda.empty_cache()


def testv6_rows(args, log):
    d = args.data_dir; p = f"{d}/{TESTV6['file']}"; mj = f"{d}/{TESTV6['manifest']}"
    if not TESTV6['sha']: log.info('test_v6 not frozen (TESTV6 sha unset): test_v6 evaluation skipped'); return None
    if not (os.path.exists(p) and os.path.exists(mj)): log.info('test_v6 inputs or manifest not present: skipped'); return None
    assert sha(mj) == TESTV6['sha'], f"{TESTV6['manifest']} differs from the frozen one: {sha(mj)}"
    assert sha(p) == json.load(open(mj, encoding='utf-8'))['sha256'][TESTV6['key']], 'test_v6 inputs hash mismatch, stop'
    log.info('test_v6 inputs verified against %s (%s)', TESTV6['manifest'], TESTV6['sha'][:12]); return read(p)


def load_eval_model(args, run, log):
    from unsloth import FastLanguageModel
    from peft import PeftModel
    base, tok = load_base(log)
    model = PeftModel.from_pretrained(base, f'{run}/adapter') if run else base; FastLanguageModel.for_inference(model)
    if tok.pad_token_id is None: tok.pad_token = tok.eos_token
    return model, tok


def generate(model, tok, system, users):
    import torch
    prompts = [tok.apply_chat_template(messages(system, u), tokenize=False, add_generation_prompt=True) for u in users]
    tok.padding_side = 'left'; lens = [len(tok(p).input_ids) for p in prompts]
    enc = tok(prompts, return_tensors='pt', padding=True, truncation=True, max_length=HP['max_seq_len']).to('cuda')
    with torch.no_grad(): gen = model.generate(**enc, max_new_tokens=HP['eval_max_new_tokens'], do_sample=False, temperature=None, top_p=None, pad_token_id=tok.pad_token_id)
    stop = {tok.eos_token_id, tok.pad_token_id} | {i for i in (tok.convert_tokens_to_ids('<|im_end|>'),) if i is not None}
    L0 = enc.input_ids.shape[1]; res = []
    for j in range(len(users)):
        ids = gen[j][L0:].tolist(); n = next((k for k, i in enumerate(ids) if i in stop), len(ids))
        res.append((tok.decode(ids, skip_special_tokens=True), lens[j], n, lens[j] > HP['max_seq_len']))
    return res


def preflight(args, system, log):
    import torch
    model, tok = load_eval_model(args, None, log)
    r = generate(model, tok, system, ['Return JSON.\n{"method": "GET", "path": "/ping", "path_params": [], "query_params": [], "summary": "ping", "description": "", "security": [], "schema_fields": [], "security_state": "unknown"}'])
    text, ptoks, n, _ = r[0]; log.info('preflight ok: prompt %d tokens, %d generated tokens, parsed=%s, text=%s', ptoks, n, bool(parse(text)), text[:200].replace('\n', ' '))
    json.dump(dict(base_model=HP['base_model'], prompt_tokens=ptoks, output_tokens=n, parsed=parse(text), gpu_memory=mem(log, 'preflight')), open(f'{args.run}/logs/preflight.json', 'w'), indent=2)
    del model; torch.cuda.empty_cache()


def evaluate(args, run, system, tag, log):
    import torch
    eval_dir = 'eval_smoke' if args.limit else 'eval'; os.makedirs(f'{run}/{eval_dir}', exist_ok=True); jobs = []
    if args.jobs == 'all': jobs = [(f'{run}/{eval_dir}/predictions_{c}_{tag}.jsonl', k, read(f'{args.data_dir}/test_v30_inputs.jsonl')) for c, k in (('oas', 'oas_user'), ('oas_code', 'oas_code_user'))]
    t6 = testv6_rows(args, log) if args.jobs in ('v6test',) else None
    if t6 is not None: jobs += [(f'{run}/{eval_dir}/v6test_predictions_{c}_{tag}.jsonl', k, t6) for c, k in (('oas', 'oas_user'), ('oas_code', 'oas_code_user'))]
    elif args.jobs == 'v6test': raise SystemExit('--jobs v6test but test_v6 is not frozen / not present (TESTV6)')
    todo = []
    for path, key, rows in jobs:
        rows = [r for r in rows if key in r][:args.limit or None]; done = {}
        if os.path.exists(path) and not args.limit:
            for r in read(path): done[r['id']] = r
        rem = [r for r in rows if r['id'] not in done]
        if not rem: log.info('skip %s (complete: %d rows)', path, len(done)); continue
        todo.append((path, key, rows, rem, len(done)))
    if not todo: return
    model, tok = load_eval_model(args, None if args.ds.get('no_adapter') else run, log); torch.cuda.reset_peak_memory_stats()
    if args.ds.get('no_adapter'): log.info('no adapter: base model %s zero-shot (S9-base reference run)', HP['base_model'])
    for path, key, rows, rem, n_done in todo:
        cond = 'oas_code' if key == 'oas_code_user' else 'oas'; name = path.split('/')[-1]; log.info('%s %s: %d rows, %d already done, %d to run', tag, name, len(rows), n_done, len(rem))
        f = open(path, 'a' if (n_done and not args.limit) else 'w', encoding='utf-8'); t_all = time.perf_counter(); n_err = n_manual = trunc = 0; ms_sum = 0.; out_toks = []; tok_max = 0
        for i in range(0, len(rem), HP['eval_batch']):
            batch = rem[i:i + HP['eval_batch']]; t0 = time.perf_counter(); res = generate(model, tok, system, [r[key] for r in batch]); ms = (time.perf_counter() - t0) * 1000 / len(batch)
            for r, (text, ptoks, ntoks, tr) in zip(batch, res):
                p = parse(text); n_err += p is None; n_manual += bool(p) and p['label'] == 'manual_review_required'; trunc += tr; ms_sum += ms; out_toks.append(ntoks); tok_max = max(tok_max, ptoks)
                f.write(json.dumps(dict(id=r['id'], label=r['label'], source=r.get('source'), security_state=r.get('security_state'), prediction=p, raw=text, inference_ms=round(ms, 1), prompt_tokens=ptoks, output_tokens=ntoks), ensure_ascii=False) + '\n'); f.flush()
            if (i // HP['eval_batch']) % 10 == 0: log.info('%s: %d/%d rows, %.0f ms/row', name, n_done + i + len(batch), len(rows), ms)
        f.close(); wall = time.perf_counter() - t_all
        timing = dict(out=path, cond=cond, base_model=HP['base_model'], rows_total=len(rows), rows_run=len(rem), resumed=n_done, inference_wall_s=round(wall, 1), mean_ms_per_row=round(ms_sum / max(1, len(rem)), 1), parse_errors=n_err, manual=n_manual,
                      prompt_tokens_max=tok_max, truncated_prompts=trunc, output_tokens_mean=round(sum(out_toks) / max(1, len(out_toks)), 1), output_tokens_max=max(out_toks) if out_toks else 0, hit_max_new_tokens=sum(t >= HP['eval_max_new_tokens'] for t in out_toks),
                      gpu_memory=mem(log, f'eval {name}'), finished=time.strftime('%Y-%m-%dT%H:%M:%S'))
        prev = path + '.timing.json'
        if os.path.exists(prev) and n_done:
            try:
                old = json.load(open(prev, encoding='utf-8')); timing['inference_wall_s'] = round(old.get('inference_wall_s', 0) + wall, 1); timing['runs'] = old.get('runs', 1) + 1
                for k in ('parse_errors', 'manual', 'truncated_prompts', 'hit_max_new_tokens'): timing[k] += old.get(k, 0)
            except Exception: pass
        json.dump(timing, open(prev, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        log.info('%s %s%s: %d rows, parse errors %d, manual %d, mean %.0f ms/row, output tokens mean %.0f max %d%s', tag, 'v6test ' if '/v6test_' in path else '', cond, len(rem), n_err, n_manual, ms_sum / max(1, len(rem)), timing['output_tokens_mean'], timing['output_tokens_max'], ' [SMOKE]' if args.limit else '')
    del model; torch.cuda.empty_cache()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', choices=sorted(DATASETS), required=True); ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--base', default='/workspace/blade_lora_v3'); ap.add_argument('--skip-eval', action='store_true'); ap.add_argument('--eval-only', action='store_true')
    ap.add_argument('--preflight', action='store_true'); ap.add_argument('--limit', type=int, default=0); ap.add_argument('--jobs', choices=['all', 'v6test'], default='all', help='v6test = only the test_v6 jobs (S9, requires the frozen manifest)')
    args = ap.parse_args(); args.ds = ds = DATASETS[args.data]; args.data_dir = f"{args.base}/{ds['dir']}"
    if ds['train'] is None: assert args.eval_only and args.jobs == 'v6test', '--data v5/base is for the S9 test_v6 evaluation only (--eval-only --jobs v6test)'
    tag = ds['tag'].format(seed=args.seed); run = args.run = f"{args.base}/runs/{ds['run'].format(seed=args.seed)}"
    for d in ('checkpoints', 'adapter', 'logs', 'eval'): os.makedirs(f'{run}/{d}', exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', handlers=[logging.FileHandler(f'{run}/logs/run.log', encoding='utf-8'), logging.StreamHandler(sys.stdout)])
    log = logging.getLogger('blade'); log.info('run %s data=%s seed=%d base=%s preflight=%s eval_only=%s jobs=%s limit=%d', tag, args.data, args.seed, args.base, args.preflight, args.eval_only, args.jobs, args.limit)
    verify(args.data_dir, ds, log)
    import torch, transformers, trl, peft
    try: import unsloth; uv = unsloth.__version__
    except Exception as e: uv = repr(e)
    env = dict(gpu=torch.cuda.get_device_name(0), vram_gb=torch.cuda.get_device_properties(0).total_memory // 2**30, torch=torch.__version__, cuda=torch.version.cuda, transformers=transformers.__version__, trl=trl.__version__, peft=peft.__version__, unsloth=uv, python=sys.version.split()[0], base_model=HP['base_model'])
    json.dump(env, open(f'{run}/env.json', 'w'), indent=2); json.dump(dict(HP, data=args.data, seed=args.seed, train_file=ds['train'], val_file=ds['val'], tag=tag), open(f'{run}/config.json', 'w'), indent=2)
    log.info('env %s', env); log.info('HP %s', HP)
    system = open(f"{args.data_dir}/{HP['prompt_file']}", encoding='utf-8').read()
    if args.preflight: preflight(args, system, log); log.info('preflight done'); return
    if ds.get('no_adapter'): assert args.eval_only, 'base (no adapter) is eval-only'; log.info('base model without adapter: no training')
    elif os.path.exists(f'{run}/adapter/adapter_model.safetensors') and (args.eval_only or os.path.exists(f'{run}/logs/train_result.json')): log.info('final adapter exists: skip training')
    elif args.eval_only: raise SystemExit(f'--eval-only but no final adapter in {run}/adapter')
    else: train(args, run, system, log)
    if not args.skip_eval: evaluate(args, run, system, tag, log)
    log.info('done %s', tag)


if __name__ == '__main__': main()
