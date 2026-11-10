"""BLADE LoRA v6a on RunPod (task S5): one (data v6a, seed) run = train -> final adapter -> test_v30 predictions (oas, oas_code) -> test_v5 predictions (oas, oas_code).
Derived from run_train.py (LoRA v5). Differences, all pre-registered in AGENTS.md "작업 S5":
  - system prompt policy_label_v3.1.md (data_v6a/), assistant JSON order {evidence_fields, rationale, label, confidence}
  - HP: max_seq_len 4096 -> 6144 (the only hyperparameter change; the v3.1 system prompt is +1,099 tokens), eval max_new_tokens 256 -> 512
  - label-token probability (label_prob) recorded per prediction from generate(output_scores=True): p_first, p_prefix, p_norm (used for thresholds), p_seq, candidates
  - evaluation appends one row per record and resumes by id (--resume is the default), so a pod restart loses nothing
  - test_v31_supp is not evaluated (judgement set = test_v5 dev + regression test_v30)
Loss masking: unsloth train_on_responses_only (assistant tokens only) exactly as run_train.py line 119.
Usage:
    python run_train_v6.py --data v6a --seed 42 [--base /workspace/blade_lora_v3]     # train (resumes from the last checkpoint) + evaluate
    python run_train_v6.py --data v6a --seed 42 --eval-only                           # existing final adapter: missing/unfinished prediction files only
    python run_train_v6.py --data v6a --seed 42 --preflight                           # load base + 4-token generate with output_scores, no training
    python run_train_v6.py --data v6a --seed 42 --eval-only --limit 8                 # smoke: 8 rows per job into eval_smoke/ (not scored)
Outputs: <base>/runs/lora_v6a_s<seed>/{config.json, env.json, logs/, adapter/, checkpoints/, eval/predictions_<cond>_lora_v6a_s<seed>_final.jsonl,
         eval/v5test_predictions_<cond>_lora_v6a_s<seed>_final.jsonl, eval/*.timing.json}. File names follow run_train.py so scripts/eval_v30.py and eval_test_v5.py read them unchanged.
No API keys or tokens. test_v6 is never read."""
import argparse, glob, hashlib, json, logging, os, re, sys, time

HP = dict(base_model='unsloth/Qwen2.5-7B-Instruct-bnb-4bit', max_seq_len=6144, lora_r=16, lora_alpha=16, lora_dropout=0.0,
          target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj'], epochs=3, lr=2e-4, batch=2, grad_acc=4,
          warmup_steps=10, weight_decay=0.01, lr_scheduler='cosine', save_steps=30, eval_steps=30, eval_max_new_tokens=512, eval_batch=8,
          prompt_version='policy-label-v3.1', prompt_file='policy_label_v3.1.md', output_order=['evidence_fields', 'rationale', 'label', 'confidence'],
          changed_vs_v5=dict(max_seq_len='4096 -> 6144 (v3.1 system prompt +1,099 tokens)', eval_max_new_tokens='256 -> 512 (rationale precedes label)'))
DATASETS = {
    'v6a': dict(dir='data_v6a', train='train_sft_v6a.jsonl', val='val_sft_v6a.jsonl', hashes='data_v6a_hashes.json', sha='c079b9f5735242b4bf2a340dce530236e6d5a2da806dad7c0b7e0d42ebaae288',
                run='lora_v6a_s{seed}', tag='lora_v6a_s{seed}_final'),
}
# test_v5 gate (same as run_train.py TESTV5): the manifest hash is frozen; test_v5_inputs.jsonl is verified against the manifest, not the data bundle hashes.
TESTV5 = dict(file='test_v5_inputs.jsonl', manifest='test_v5_manifest.json', sha='57fd384f46e89e905209e627a7ff7fb9f312e22a7bed222639e91a80bd05fccd', key='training/lora/data_v5/test_v5_inputs.jsonl')
LABELS = ['public', 'role_required', 'membership_required', 'tenant_match', 'owner_match', 'owner_or_admin', 'manual_review_required']


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


# ---------------------------------------------------------------- label-token probability (AGENTS.md S5, reports/eval/lora_v6a/data_prep.md section 4)
class LabelTokens:
    """Token ids of the 7 labels inside the JSON context '"label": "'. Distinguishing prefix: 1 token for 5 labels, 2 tokens for owner_match / owner_or_admin
    (shared first token 'owner'). Asserts prefix stability of the tokenizer for this context."""
    def __init__(self, tok):
        pre = '{"evidence_fields": ["description"], "rationale": "x", "label": "'; ids_pre = tok(pre).input_ids; self.ids = {}
        for l in LABELS:
            full = tok(pre + l + '", "confidence": 0.9}').input_ids; lab = tok(l, add_special_tokens=False).input_ids
            assert full[:len(ids_pre)] == ids_pre and full[len(ids_pre):len(ids_pre) + len(lab)] == lab, f'tokenizer prefix instability for {l}'
            self.ids[l] = lab
        self.first = {l: v[0] for l, v in self.ids.items()}; self.owner_id = self.first['owner_match']
        assert self.first['owner_or_admin'] == self.owner_id and len({self.first[l] for l in LABELS}) == 6, 'unexpected label tokenization (expected exactly the owner pair to share the first token)'
        self.singles = [l for l in LABELS if self.first[l] != self.owner_id]
        self.second = {l: self.ids[l][1] for l in ('owner_match', 'owner_or_admin')}

    def probs(self, tok, ids, logits_at):
        """ids: generated token ids (trimmed at eos). logits_at(t) -> 1-D logits tensor for generated position t. Returns the label_prob record or None."""
        import torch
        text = ''; pos = None
        for t, i in enumerate(ids):
            if re.search(r'"label":\s*"$', text): pos = t; break
            text += tok.decode([i])
        if pos is None: return None
        sm = lambda t: torch.softmax(logits_at(t).float(), -1)
        gen_lab = next((l for l, lid in self.ids.items() if ids[pos:pos + len(lid)] == lid), None)
        if gen_lab is None: return dict(label_token_pos=pos, tokenization_match=False)
        p0 = sm(pos); cand = {l: float(p0[self.first[l]]) for l in self.singles}
        if self.first[gen_lab] == self.owner_id:
            p1 = sm(pos + 1); po = float(p0[self.owner_id])
            cand['owner_match'] = po * float(p1[self.second['owner_match']]); cand['owner_or_admin'] = po * float(p1[self.second['owner_or_admin']])
            owner_mass = cand['owner_match'] + cand['owner_or_admin']; exact = True
        else:
            cand['owner_match'] = cand['owner_or_admin'] = None; owner_mass = float(p0[self.owner_id]); exact = False   # upper bound of the owner subtree
        denom = sum(cand[l] for l in self.singles) + owner_mass
        p_first = float(p0[self.first[gen_lab]]); p_prefix = cand[gen_lab]
        p_seq = 1.0
        for k, tid in enumerate(self.ids[gen_lab]): p_seq *= float(sm(pos + k)[tid])
        return dict(label_token_pos=pos, generated_label=gen_lab, tokenization_match=True, p_first=round(p_first, 6), p_prefix=round(p_prefix, 6), p_norm=round(p_prefix / denom, 6) if denom > 0 else None,
                    p_seq=round(p_seq, 6), candidates={l: (round(v, 6) if v is not None else None) for l, v in cand.items()}, owner_group_mass=round(owner_mass, 6), owner_split_exact=exact, candidate_mass=round(denom, 6))


def trim(ids, stop_ids):
    out = []
    for i in ids:
        if i in stop_ids: break
        out.append(i)
    return out


# ---------------------------------------------------------------- training (same as run_train.train, HP above)
def train(args, run, system, log):
    import torch
    from unsloth import FastLanguageModel
    from unsloth.chat_templates import train_on_responses_only
    from trl import SFTTrainer, SFTConfig
    from datasets import Dataset
    train_rows, val_rows = read(f"{args.data_dir}/{args.ds['train']}"), read(f"{args.data_dir}/{args.ds['val']}")
    assert all(list(json.loads(r['assistant'])) == HP['output_order'] for r in train_rows + val_rows), 'assistant key order differs from the pre-registered output order'
    model, tok = FastLanguageModel.from_pretrained(model_name=HP['base_model'], max_seq_length=HP['max_seq_len'], dtype=None, load_in_4bit=True)
    model = FastLanguageModel.get_peft_model(model, r=HP['lora_r'], lora_alpha=HP['lora_alpha'], lora_dropout=HP['lora_dropout'], target_modules=HP['target_modules'],
                                             bias='none', use_gradient_checkpointing='unsloth', random_state=args.seed)
    to_ds = lambda rows: Dataset.from_list([{'text': tok.apply_chat_template(messages(system, r['user'], r['assistant']), tokenize=False)} for r in rows])
    train_ds = to_ds(train_rows); val_oas = to_ds([r for r in val_rows if r['condition'] == 'oas']); val_code = to_ds([r for r in val_rows if r['condition'] == 'oas_code'])
    lens = [len(tok(x['text']).input_ids) for x in train_ds]; log.info('train %d, val oas %d / oas_code %d; train tokens max %d, > %d: %d', len(train_ds), len(val_oas), len(val_code), max(lens), HP['max_seq_len'], sum(l > HP['max_seq_len'] for l in lens))
    assert max(lens) <= HP['max_seq_len'], 'a training row exceeds max_seq_len (would be truncated): stop'
    cfg = SFTConfig(output_dir=f'{run}/checkpoints', per_device_train_batch_size=HP['batch'], gradient_accumulation_steps=HP['grad_acc'], num_train_epochs=HP['epochs'], learning_rate=HP['lr'],
                    warmup_steps=HP['warmup_steps'], weight_decay=HP['weight_decay'], lr_scheduler_type=HP['lr_scheduler'], seed=args.seed, logging_steps=5,
                    save_steps=HP['save_steps'], save_total_limit=2,
                    eval_strategy='steps', eval_steps=HP['eval_steps'], per_device_eval_batch_size=1, bf16=torch.cuda.is_bf16_supported(), fp16=not torch.cuda.is_bf16_supported(),
                    optim='adamw_8bit', report_to='none', max_seq_length=HP['max_seq_len'], dataset_text_field='text', packing=False)
    trainer = SFTTrainer(model=model, tokenizer=tok, train_dataset=train_ds, eval_dataset={'oas': val_oas, 'oas_code': val_code}, args=cfg)
    trainer = train_on_responses_only(trainer, instruction_part='<|im_start|>user\n', response_part='<|im_start|>assistant\n')   # completion-only loss, as LoRA v5 (run_train.py:119)
    # masking evidence for the report: fraction of label == -100 in the first training example (system+user masked, assistant kept)
    ex = trainer.train_dataset[0]; lab = ex.get('labels');
    if lab is not None: log.info('loss mask check (row 0): %d/%d tokens masked (-100), %d assistant tokens in loss', sum(x == -100 for x in lab), len(lab), sum(x != -100 for x in lab))
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


def testv5_rows(args, log):
    d = args.data_dir; p = f"{d}/{TESTV5['file']}"; mj = f"{d}/{TESTV5['manifest']}"
    if not (os.path.exists(p) and os.path.exists(mj)): log.info('test_v5 inputs or manifest not present: test_v5 evaluation skipped'); return None
    assert sha(mj) == TESTV5['sha'], f"{TESTV5['manifest']} differs from the frozen one: {sha(mj)}"
    assert sha(p) == json.load(open(mj, encoding='utf-8'))['sha256'][TESTV5['key']], 'test_v5 inputs hash mismatch, stop'
    log.info('test_v5 inputs verified against %s (%s)', TESTV5['manifest'], TESTV5['sha'][:12]); return read(p)


def load_eval_model(args, run):
    from unsloth import FastLanguageModel
    from peft import PeftModel
    base, tok = FastLanguageModel.from_pretrained(model_name=HP['base_model'], max_seq_length=HP['max_seq_len'], dtype=None, load_in_4bit=True)
    model = PeftModel.from_pretrained(base, f'{run}/adapter') if run else base; FastLanguageModel.for_inference(model)
    if tok.pad_token_id is None: tok.pad_token = tok.eos_token
    return model, tok


def generate(model, tok, system, users, key_len_out=None):
    """Batched greedy generation with scores. Returns per sample: (ids trimmed at eos, text, logits_at(t), prompt_tokens)."""
    import torch
    prompts = [tok.apply_chat_template(messages(system, u), tokenize=False, add_generation_prompt=True) for u in users]
    tok.padding_side = 'left'; lens = [len(tok(p).input_ids) for p in prompts]
    enc = tok(prompts, return_tensors='pt', padding=True, truncation=True, max_length=HP['max_seq_len']).to('cuda')
    with torch.no_grad():
        out = model.generate(**enc, max_new_tokens=HP['eval_max_new_tokens'], do_sample=False, temperature=None, top_p=None, pad_token_id=tok.pad_token_id, return_dict_in_generate=True, output_scores=True)
    assert getattr(out, 'scores', None) is not None and len(out.scores) > 0, 'generate() returned no scores: label_prob impossible'
    stop = {tok.eos_token_id, tok.pad_token_id} | {i for i in (tok.convert_tokens_to_ids('<|im_end|>'),) if i is not None}
    L0 = enc.input_ids.shape[1]; res = []
    for j in range(len(users)):
        raw_ids = out.sequences[j][L0:].tolist(); ids = trim(raw_ids, stop)
        res.append((ids, tok.decode(raw_ids, skip_special_tokens=True), (lambda t, j=j: out.scores[t][j]), lens[j], len(ids), lens[j] > HP['max_seq_len']))
    return res


def preflight(args, system, log):
    """Load the base model as in evaluation and check that generate() yields scores and the label tokenizer assumptions hold (no training)."""
    import torch
    model, tok = load_eval_model(args, None); lt = LabelTokens(tok); log.info('label tokens: %s', {l: lt.ids[l] for l in LABELS})
    r = generate(model, tok, system, ['Return JSON.\n{"method": "GET", "path": "/ping", "path_params": [], "query_params": [], "summary": "ping", "description": "", "security": [], "schema_fields": [], "security_state": "unknown"}'])
    ids, text, logits_at, ptoks, n, _ = r[0]; lp = lt.probs(tok, ids, logits_at)
    log.info('preflight ok: %d generated tokens, scores available, label_prob=%s, text=%s', n, json.dumps(lp)[:200] if lp else None, text[:200].replace('\n', ' '))
    del model; torch.cuda.empty_cache()


def evaluate(args, run, system, tag, log):
    import torch
    eval_dir = 'eval_smoke' if args.limit else 'eval'; os.makedirs(f'{run}/{eval_dir}', exist_ok=True)
    jobs = [(f'{run}/{eval_dir}/predictions_{c}_{tag}.jsonl', k, read(f'{args.data_dir}/test_v30_inputs.jsonl')) for c, k in (('oas', 'oas_user'), ('oas_code', 'oas_code_user'))]
    t5 = testv5_rows(args, log)
    if t5 is not None: jobs += [(f'{run}/{eval_dir}/v5test_predictions_{c}_{tag}.jsonl', k, t5) for c, k in (('oas', 'oas_user'), ('oas_code', 'oas_code_user'))]
    todo = []
    for path, key, rows in jobs:
        rows = [r for r in rows if key in r][:args.limit or None]; done = {}
        if os.path.exists(path) and not args.limit:
            for r in read(path): done[r['id']] = r
        rem = [r for r in rows if r['id'] not in done]
        if not rem: log.info('skip %s (complete: %d rows)', path, len(done)); continue
        todo.append((path, key, rows, rem, len(done)))
    if not todo: return
    model, tok = load_eval_model(args, run); lt = LabelTokens(tok)
    for path, key, rows, rem, n_done in todo:
        cond = 'oas_code' if key == 'oas_code_user' else 'oas'; log.info('%s %s: %d rows, %d already done, %d to run', tag, path.split('/')[-1], len(rows), n_done, len(rem))
        f = open(path, 'a' if (n_done and not args.limit) else 'w', encoding='utf-8'); t_all = time.perf_counter(); n_err = n_manual = n_lp = trunc = 0; ms_sum = 0.; out_toks = []; tok_max = 0
        for i in range(0, len(rem), HP['eval_batch']):
            batch = rem[i:i + HP['eval_batch']]; t0 = time.perf_counter(); res = generate(model, tok, system, [r[key] for r in batch]); ms = (time.perf_counter() - t0) * 1000 / len(batch)
            for r, (ids, text, logits_at, ptoks, ntoks, tr) in zip(batch, res):
                p = parse(text); lp = lt.probs(tok, ids, logits_at) if p else None
                if lp and lp.get('generated_label') and lp['generated_label'] != p['label']: lp['parsed_label_mismatch'] = True
                n_err += p is None; n_manual += bool(p) and p['label'] == 'manual_review_required'; n_lp += bool(lp and lp.get('p_norm') is not None); trunc += tr; ms_sum += ms; out_toks.append(ntoks); tok_max = max(tok_max, ptoks)
                f.write(json.dumps(dict(id=r['id'], label=r['label'], source=r.get('source'), security_state=r.get('security_state'), prediction=p, raw=text, inference_ms=round(ms, 1), prompt_tokens=ptoks, output_tokens=ntoks, label_prob=lp), ensure_ascii=False) + '\n'); f.flush()
            del res; torch.cuda.empty_cache()
            if (i // HP['eval_batch']) % 5 == 0: log.info('%s: %d/%d rows, %.0f ms/row', path.split('/')[-1], n_done + i + len(batch), len(rows), ms)
        f.close(); wall = time.perf_counter() - t_all
        timing = dict(out=path, cond=cond, rows_total=len(rows), rows_run=len(rem), resumed=n_done, inference_wall_s=round(wall, 1), mean_ms_per_row=round(ms_sum / max(1, len(rem)), 1), parse_errors=n_err, manual=n_manual,
                      label_prob_available=n_lp, prompt_tokens_max=tok_max, truncated_prompts=trunc, output_tokens_mean=round(sum(out_toks) / max(1, len(out_toks)), 1), output_tokens_max=max(out_toks) if out_toks else 0,
                      hit_max_new_tokens=sum(t >= HP['eval_max_new_tokens'] for t in out_toks), finished=time.strftime('%Y-%m-%dT%H:%M:%S'))
        prev = path + '.timing.json'
        if os.path.exists(prev) and n_done:
            try:
                old = json.load(open(prev, encoding='utf-8')); timing['inference_wall_s'] = round(old.get('inference_wall_s', 0) + wall, 1); timing['runs'] = old.get('runs', 1) + 1
                for k in ('parse_errors', 'manual', 'label_prob_available', 'truncated_prompts', 'hit_max_new_tokens'): timing[k] += old.get(k, 0)
            except Exception: pass
        json.dump(timing, open(prev, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        log.info('%s %s: %d rows, parse errors %d, manual %d, label_prob %d, mean %.0f ms/row, output tokens mean %.0f max %d%s', tag, cond, len(rem), n_err, n_manual, n_lp, ms_sum / max(1, len(rem)), timing['output_tokens_mean'], timing['output_tokens_max'], ' [SMOKE]' if args.limit else '')
    del model; torch.cuda.empty_cache()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', choices=sorted(DATASETS), required=True); ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--base', default='/workspace/blade_lora_v3'); ap.add_argument('--skip-eval', action='store_true'); ap.add_argument('--eval-only', action='store_true')
    ap.add_argument('--preflight', action='store_true', help='base model load + generate(output_scores) check, then exit (no training)')
    ap.add_argument('--limit', type=int, default=0, help='smoke test: first N rows per job into <run>/eval_smoke/ (not scored)')
    args = ap.parse_args(); args.ds = ds = DATASETS[args.data]; args.data_dir = f"{args.base}/{ds['dir']}"
    tag = ds['tag'].format(seed=args.seed); run = f"{args.base}/runs/{ds['run'].format(seed=args.seed)}"
    for d in ('checkpoints', 'adapter', 'logs', 'eval'): os.makedirs(f'{run}/{d}', exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', handlers=[logging.FileHandler(f'{run}/logs/run.log', encoding='utf-8'), logging.StreamHandler(sys.stdout)])
    log = logging.getLogger('blade'); log.info('run %s data=%s seed=%d base=%s preflight=%s eval_only=%s limit=%d', tag, args.data, args.seed, args.base, args.preflight, args.eval_only, args.limit)
    verify(args.data_dir, ds, log)
    import torch, transformers, trl, peft
    try: import unsloth; uv = unsloth.__version__
    except Exception as e: uv = repr(e)
    env = dict(gpu=torch.cuda.get_device_name(0), vram_gb=torch.cuda.get_device_properties(0).total_memory // 2**30, torch=torch.__version__, cuda=torch.version.cuda, transformers=transformers.__version__,
               trl=trl.__version__, peft=peft.__version__, unsloth=uv, python=sys.version.split()[0])
    json.dump(env, open(f'{run}/env.json', 'w'), indent=2); json.dump(dict(HP, data=args.data, seed=args.seed, train_file=ds['train'], val_file=ds['val'], tag=tag), open(f'{run}/config.json', 'w'), indent=2)
    log.info('env %s', env); log.info('HP %s', HP)
    system = open(f"{args.data_dir}/{HP['prompt_file']}", encoding='utf-8').read()
    if args.preflight: preflight(args, system, log); log.info('preflight done'); return
    if os.path.exists(f'{run}/adapter/adapter_model.safetensors') and (args.eval_only or os.path.exists(f'{run}/logs/train_result.json')): log.info('final adapter exists: skip training')
    elif args.eval_only: raise SystemExit(f'--eval-only but no final adapter in {run}/adapter')
    else: train(args, run, system, log)
    if not args.skip_eval: evaluate(args, run, system, tag, log)
    log.info('done %s', tag)


if __name__ == '__main__': main()
