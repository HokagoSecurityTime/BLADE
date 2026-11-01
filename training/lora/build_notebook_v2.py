"""Writes training/lora/lora_v2.ipynb: Unsloth QLoRA on data-v2 (3 seeds), per-condition val loss every 30 steps, all checkpoints to Drive,
test_v30 evaluation of the final and best-per-condition checkpoints, predictions in the v1 format (scored later by scripts/eval_v30.py)."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
H = json.loads((HERE / 'data_v2/data_v2_hashes.json').read_text(encoding='utf-8'))
cells = []
def md(s): cells.append({'cell_type': 'markdown', 'metadata': {}, 'source': s})
def code(s): cells.append({'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [], 'source': s})

md('''# BLADE LoRA v2 — data-v2, 프롬프트 v3.0.1 (Unsloth QLoRA, Qwen2.5-7B-Instruct, seed 42·43·44)

Colab에서 실행한다. API 키·토큰 불필요. 입력은 Drive `MyDrive/blade_lora_v2/data_v2/`(README_colab_v2.md). 산출물은 `runs/lora_v2_seed<N>/`.
v1과의 차이: data-v2(train 799→4096 토큰 초과 제외, val 98), eval/save 30 step마다, val loss를 oas·oas_code 조건별로 기록, 체크포인트 전부 Drive 저장, seed 3회, 평가 대상 = 최종 + 조건별 val loss 최저 체크포인트. 평가 정의는 로컬 `scripts/eval_v30.py`(eval-def v2).

예상 시간(A100): 학습 seed당 약 25~35분 + 평가(체크포인트 최대 3개 × 4조합) 약 1~1.5시간. L4: 각각 약 2배.''')

code('''# 1. Google Drive 마운트
from google.colab import drive
drive.mount('/content/drive')''')

code('''# 2. 하이퍼파라미터·경로 (v1과 동일; seed만 셀 6에서 반복)
import os, json, time, glob
BASE = '/content/drive/MyDrive/blade_lora_v2'
DATA_DIR = f'{BASE}/data_v1' if False else f'{BASE}/data_v2'
SEEDS = [42, 43, 44]
HP = dict(base_model='unsloth/Qwen2.5-7B-Instruct-bnb-4bit', max_seq_len=4096, lora_r=16, lora_alpha=16, lora_dropout=0.0,
          target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'], epochs=3, lr=2e-4, batch=2, grad_acc=4,
          warmup_steps=10, weight_decay=0.01, lr_scheduler='cosine', save_steps=30, eval_steps=30, eval_max_new_tokens=256, eval_batch=8,
          prompt_version='policy-label-v3.0.1', data_version='data-v2')
os.makedirs(f'{BASE}/runs', exist_ok=True); print(HP)''')

code('''# 3. 패키지 설치
%pip -q install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
%pip -q install --no-deps trl peft accelerate bitsandbytes xformers
import torch; print(torch.cuda.get_device_name(0), torch.cuda.get_device_properties(0).total_memory // 2**30, 'GB')''')

code(f'''# 4. 데이터 로드 + data-v2 해시 검증 (불일치면 중단)
import hashlib, json
EXPECTED = {json.dumps(H['generated'], indent=4)}
EXPECTED_SOURCES = {json.dumps(H['data_v2_sources'], indent=4)}   # AGENTS.md data-v2 절 기록값
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
mismatch = {{n: (sha(f'{{DATA_DIR}}/{{n}}'), h) for n, h in EXPECTED.items() if sha(f'{{DATA_DIR}}/{{n}}') != h}}
assert not mismatch, f'data-v2 입력 해시 불일치, 중단: {{mismatch}}'
rec = json.load(open(f'{{DATA_DIR}}/data_v2_hashes.json')); assert rec['data_v2_sources'] == EXPECTED_SOURCES, 'data_v2_hashes.json 원본 해시 불일치, 중단'
def read(p): return [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
SYSTEM = open(f'{{DATA_DIR}}/policy_label_v3.0.1.md', encoding='utf-8').read()
train_rows, val_rows, test_rows = read(f'{{DATA_DIR}}/train_sft.jsonl'), read(f'{{DATA_DIR}}/val_sft.jsonl'), read(f'{{DATA_DIR}}/test_v30_inputs.jsonl')
print(len(train_rows), len(val_rows), len(test_rows), 'hash OK; 4096 초과 제외(로컬에서):', rec['counts']['train_excluded_over_4096'], rec.get('excluded_over_4096'))''')

code('''# 5. 공통 함수 (모델 로드, 데이터셋, 평가)
from unsloth import FastLanguageModel
from unsloth.chat_templates import train_on_responses_only
from trl import SFTTrainer, SFTConfig
from datasets import Dataset
import re, time
LABELS = ['public','role_required','membership_required','tenant_match','owner_match','owner_or_admin','manual_review_required']
def messages(user, assistant=None):
    m = [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': user}]
    if assistant is not None: m.append({'role': 'assistant', 'content': assistant})
    return m
def load_model(seed):
    model, tok = FastLanguageModel.from_pretrained(model_name=HP['base_model'], max_seq_length=HP['max_seq_len'], dtype=None, load_in_4bit=True)
    model = FastLanguageModel.get_peft_model(model, r=HP['lora_r'], lora_alpha=HP['lora_alpha'], lora_dropout=HP['lora_dropout'], target_modules=HP['target_modules'], bias='none', use_gradient_checkpointing='unsloth', random_state=seed)
    return model, tok
def to_ds(tok, rows): return Dataset.from_list([{'text': tok.apply_chat_template(messages(r['user'], r['assistant']), tokenize=False)} for r in rows])
def parse(text):
    m = re.search(r'\\{.*\\}', text, re.S)
    try:
        o = json.loads(m.group(0)) if m else None
        return o if isinstance(o, dict) and o.get('label') in LABELS else None
    except Exception: return None
def generate(model, tok, users):
    FastLanguageModel.for_inference(model); outs = []
    for i in range(0, len(users), HP['eval_batch']):
        batch = users[i:i+HP['eval_batch']]; prompts = [tok.apply_chat_template(messages(u), tokenize=False, add_generation_prompt=True) for u in batch]
        tok.padding_side = 'left'; enc = tok(prompts, return_tensors='pt', padding=True, truncation=True, max_length=HP['max_seq_len']).to('cuda'); t0 = time.perf_counter()
        with torch.no_grad(): gen = model.generate(**enc, max_new_tokens=HP['eval_max_new_tokens'], do_sample=False, temperature=None, top_p=None, pad_token_id=tok.pad_token_id)
        ms = (time.perf_counter() - t0) * 1000 / len(batch)
        for j in range(len(batch)):
            text = tok.decode(gen[j][enc.input_ids.shape[1]:], skip_special_tokens=True); outs.append(dict(raw=text, parsed=parse(text), inference_ms=round(ms, 1)))
    return outs
def write_predictions(path, rows, outs):
    with open(path, 'w', encoding='utf-8') as f:
        for r, o in zip(rows, outs): f.write(json.dumps(dict(id=r['id'], label=r['label'], source=r['source'], security_state=r['security_state'], prediction=o['parsed'], raw=o['raw'], inference_ms=o['inference_ms']), ensure_ascii=False) + '\\n')
def evaluate_checkpoint(model, tok, tag, run_dir):
    # predictions_{cond}_{tag}.jsonl in the v1 format -> scored locally with scripts/eval_v30.py
    FastLanguageModel.for_inference(model)
    for cond, key in (('oas', 'oas_user'), ('oas_code', 'oas_code_user')):
        rows = [r for r in test_rows if key in r]; outs = generate(model, tok, [r[key] for r in rows])
        write_predictions(f'{run_dir}/eval/predictions_{cond}_{tag}.jsonl', rows, outs)
        print(tag, cond, 'done', len(rows), 'manual', sum(o['parsed'] and o['parsed']['label'] == 'manual_review_required' for o in outs))''')

code('''# 6. 학습: seed 42·43·44 반복 (eval/save 30 step, 조건별 val loss, 체크포인트 전부 Drive 보존, 재개 가능)
from transformers import TrainerCallback
results = {}
for SEED in SEEDS:
    RUN = f'{BASE}/runs/lora_v2_seed{SEED}'; [os.makedirs(f'{RUN}/{d}', exist_ok=True) for d in ('checkpoints', 'adapter', 'logs', 'eval')]
    json.dump(dict(HP, seed=SEED), open(f'{RUN}/config.json', 'w'), indent=2); json.dump(dict(expected=EXPECTED, sources=EXPECTED_SOURCES), open(f'{RUN}/hashes.json', 'w'), indent=2)
    model, tok = load_model(SEED)
    train_ds = to_ds(tok, train_rows); val_oas = to_ds(tok, [r for r in val_rows if r['condition'] == 'oas']); val_code = to_ds(tok, [r for r in val_rows if r['condition'] == 'oas_code'])
    cfg = SFTConfig(output_dir=f'{RUN}/checkpoints', per_device_train_batch_size=HP['batch'], gradient_accumulation_steps=HP['grad_acc'], num_train_epochs=HP['epochs'], learning_rate=HP['lr'],
                    warmup_steps=HP['warmup_steps'], weight_decay=HP['weight_decay'], lr_scheduler_type=HP['lr_scheduler'], seed=SEED, logging_steps=5, save_steps=HP['save_steps'], save_total_limit=None,
                    eval_strategy='steps', eval_steps=HP['eval_steps'], per_device_eval_batch_size=1, bf16=torch.cuda.is_bf16_supported(), fp16=not torch.cuda.is_bf16_supported(), optim='adamw_8bit',
                    report_to='none', max_seq_length=HP['max_seq_len'], dataset_text_field='text', packing=False)
    trainer = SFTTrainer(model=model, tokenizer=tok, train_dataset=train_ds, eval_dataset={'oas': val_oas, 'oas_code': val_code}, args=cfg)
    trainer = train_on_responses_only(trainer, instruction_part='<|im_start|>user\\n', response_part='<|im_start|>assistant\\n')
    ckpts = sorted(glob.glob(f'{RUN}/checkpoints/checkpoint-*'), key=lambda p: int(p.rsplit('-', 1)[1])); resume = ckpts[-1] if ckpts else None
    print('seed', SEED, 'resume from', resume)
    res = trainer.train(resume_from_checkpoint=resume)
    model.save_pretrained(f'{RUN}/adapter'); tok.save_pretrained(f'{RUN}/adapter')
    with open(f'{RUN}/logs/train_log.jsonl', 'w') as f:
        for e in trainer.state.log_history: f.write(json.dumps(e) + '\\n')
    # best checkpoint per condition from eval logs
    best = {}
    for cond in ('oas', 'oas_code'):
        ev = [(e['step'], e[f'eval_{cond}_loss']) for e in trainer.state.log_history if f'eval_{cond}_loss' in e]
        if ev: best[cond] = min(ev, key=lambda x: x[1])
    json.dump(dict(res.metrics, resumed_from=resume, steps=trainer.state.global_step, best_by_condition=best), open(f'{RUN}/logs/train_result.json', 'w'), indent=2)
    results[SEED] = dict(final_step=trainer.state.global_step, best=best); print('seed', SEED, res.metrics, best)
    del model, trainer; torch.cuda.empty_cache()
json.dump(results, open(f'{BASE}/runs/summary_train.json', 'w'), indent=2); print(results)''')

code('''# 7. 평가: seed별 최종 어댑터 + 조건별 val loss 최저 체크포인트 (+ seed 42에서 베이스 모델 1회)
from peft import PeftModel
for SEED in SEEDS:
    RUN = f'{BASE}/runs/lora_v2_seed{SEED}'; res = json.load(open(f'{RUN}/logs/train_result.json')); best = res['best_by_condition']
    targets = {f'lora_v2_s{SEED}_final': f'{RUN}/adapter'}
    for cond, (step, loss) in best.items():
        ck = f'{RUN}/checkpoints/checkpoint-{step}'
        if os.path.isdir(ck): targets[f'lora_v2_s{SEED}_best_{cond}_step{step}'] = ck
    for tag, path in targets.items():
        if all(os.path.exists(f'{RUN}/eval/predictions_{c}_{tag}.jsonl') for c in ('oas', 'oas_code')): print('skip', tag); continue
        base, tok = FastLanguageModel.from_pretrained(model_name=HP['base_model'], max_seq_length=HP['max_seq_len'], dtype=None, load_in_4bit=True)
        model = PeftModel.from_pretrained(base, path); evaluate_checkpoint(model, tok, tag, RUN); del model, base; torch.cuda.empty_cache()
# base model once (same session) for the v2 comparison row
RUN0 = f'{BASE}/runs/lora_v2_seed42'
if not os.path.exists(f'{RUN0}/eval/predictions_oas_base_v301.jsonl'):
    base, tok = FastLanguageModel.from_pretrained(model_name=HP['base_model'], max_seq_length=HP['max_seq_len'], dtype=None, load_in_4bit=True)
    evaluate_checkpoint(base, tok, 'base_v301', RUN0); del base; torch.cuda.empty_cache()
print('done. 로컬에서: python scripts/eval_v30.py --pred <runs/*/eval/predictions_*.jsonl> --md reports/eval/lora_v2/eval_v30.md')''')

nb = {'cells': cells, 'metadata': {'accelerator': 'GPU', 'colab': {'provenance': []}, 'kernelspec': {'display_name': 'Python 3', 'name': 'python3'}, 'language_info': {'name': 'python'}}, 'nbformat': 4, 'nbformat_minor': 5}
with open(HERE / 'lora_v2.ipynb', 'w', encoding='utf-8', newline='\n') as f: json.dump(nb, f, ensure_ascii=False, indent=1)
print('written', HERE / 'lora_v2.ipynb', len(cells), 'cells')
