"""Writes training/lora/lora_v1_colab.ipynb (Unsloth QLoRA, Qwen2.5-7B-Instruct, data-v1, prompt v3.0.1). Run: python training/lora/build_notebook.py"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
HASHES = json.loads((HERE / 'data_v1/data_v1_hashes.json').read_text(encoding='utf-8'))

cells = []
def md(s): cells.append({'cell_type': 'markdown', 'metadata': {}, 'source': s})
def code(s): cells.append({'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [], 'source': s})

md('''# BLADE LoRA v1 — data-v1, 프롬프트 v3.0.1 (Unsloth QLoRA, Qwen2.5-7B-Instruct)

이 노트북은 Colab에서 실행한다. API 키·토큰은 어디에도 쓰지 않는다(공개 모델만 사용).
입력은 Drive `MyDrive/blade_lora_v1/data_v1/`의 5개 파일(README 참조). 모든 산출물은 Drive `runs/<RUN_NAME>/`에 저장한다.

**GPU·예상 시간** (471건 × 3 epoch, max_seq_len 4096, 4bit QLoRA r=16)
- L4 24GB: 학습 약 40~60분, 평가(269건 × oas/oas_code × 베이스/LoRA ≈ 1,068 생성) 약 60분.
- T4 16GB: 학습 약 2시간, 평가 약 2.5시간. 메모리 부족 시 셀 2 주석대로 `BATCH=1, GRAD_ACC=8, MAX_SEQ_LEN=3584, EVAL_BATCH=2` 로 조정.

실행 순서: 셀 1 → 2 → 3 → 4(해시 검증, 불일치 시 중단) → 5 → 6(학습, 재개 가능) → 7 → 8(평가) → 9(보고서 저장).''')

code('''# 1. Google Drive 마운트
from google.colab import drive
drive.mount('/content/drive')''')

code('''# 2. 하이퍼파라미터·경로 (한 곳에서만 수정)
import os, json, time
RUN_NAME = 'lora_v1_run1'          # 세션이 끊기면 같은 이름으로 다시 실행 → 마지막 체크포인트에서 재개
BASE = '/content/drive/MyDrive/blade_lora_v1'
DATA_DIR = f'{BASE}/data_v1'
RUN_DIR = f'{BASE}/runs/{RUN_NAME}'
for d in ('checkpoints', 'adapter', 'logs', 'eval'): os.makedirs(f'{RUN_DIR}/{d}', exist_ok=True)

HP = dict(
    base_model='unsloth/Qwen2.5-7B-Instruct-bnb-4bit',  # Qwen2.5-7B-Instruct, 4bit
    max_seq_len=4096,      # train 최대 약 3.8k 토큰(o200k 기준). T4 부족 시 3584
    lora_r=16, lora_alpha=16, lora_dropout=0.0,
    target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'],
    epochs=3, lr=2e-4, batch=2, grad_acc=4,   # 유효 배치 8. T4: batch=1, grad_acc=8
    warmup_steps=10, weight_decay=0.01, lr_scheduler='cosine', seed=42,
    save_steps=30,         # 체크포인트 간격(step). Drive에 저장
    eval_max_new_tokens=256, eval_batch=8,     # T4: eval_batch=2
    prompt_version='policy-label-v3.0.1', data_version='data-v1',
)
json.dump(HP, open(f'{RUN_DIR}/config.json', 'w'), indent=2)
print(RUN_DIR); print(HP)''')

code('''# 3. 패키지 설치 (Colab)
%pip -q install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
%pip -q install --no-deps trl peft accelerate bitsandbytes xformers
import torch; print(torch.cuda.get_device_name(0), torch.cuda.get_device_properties(0).total_memory // 2**30, 'GB')''')

code(f'''# 4. 데이터 로드 + data-v1 해시 검증 (불일치면 중단)
import hashlib, json
EXPECTED = {json.dumps(HASHES['generated'], indent=4)}
EXPECTED_SOURCES = {json.dumps(HASHES['data_v1_sources'], indent=4)}   # AGENTS.md data-v1 기록값 (train_v30/val_v30/test_v30/프롬프트)
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
mismatch = {{n: (sha(f'{{DATA_DIR}}/{{n}}'), h) for n, h in EXPECTED.items() if sha(f'{{DATA_DIR}}/{{n}}') != h}}
assert not mismatch, f'data-v1 입력 해시 불일치, 중단: {{mismatch}}'
recorded = json.load(open(f'{{DATA_DIR}}/data_v1_hashes.json'))
assert recorded['data_v1_sources'] == EXPECTED_SOURCES, 'data_v1_hashes.json의 원본 해시가 data-v1 기록과 다름, 중단'
json.dump(dict(expected=EXPECTED, sources=EXPECTED_SOURCES, verified_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())), open(f'{{RUN_DIR}}/hashes.json', 'w'), indent=2)
def read(p): return [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
SYSTEM = open(f'{{DATA_DIR}}/policy_label_v3.0.1.md', encoding='utf-8').read()
train_rows, val_rows, test_rows = read(f'{{DATA_DIR}}/train_sft.jsonl'), read(f'{{DATA_DIR}}/val_sft.jsonl'), read(f'{{DATA_DIR}}/test_v30_inputs.jsonl')
print(len(train_rows), len(val_rows), len(test_rows), 'hash OK')''')

code('''# 5. 모델 로드 (4bit) + LoRA
from unsloth import FastLanguageModel
model, tokenizer = FastLanguageModel.from_pretrained(model_name=HP['base_model'], max_seq_length=HP['max_seq_len'], dtype=None, load_in_4bit=True)
model = FastLanguageModel.get_peft_model(model, r=HP['lora_r'], lora_alpha=HP['lora_alpha'], lora_dropout=HP['lora_dropout'], target_modules=HP['target_modules'],
                                         bias='none', use_gradient_checkpointing='unsloth', random_state=HP['seed'])
def messages(user, assistant=None):
    msgs = [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': user}]
    if assistant is not None: msgs.append({'role': 'assistant', 'content': assistant})
    return msgs
from datasets import Dataset
def to_text(rows): return Dataset.from_list([{'text': tokenizer.apply_chat_template(messages(r['user'], r['assistant']), tokenize=False)} for r in rows])
train_ds, val_ds = to_text(train_rows), to_text(val_rows)
lens = [len(tokenizer(t['text']).input_ids) for t in train_ds]
print('train tokens max/mean', max(lens), sum(lens)//len(lens), '| truncated:', sum(l > HP['max_seq_len'] for l in lens))''')

code('''# 6. 학습 (응답 부분만 손실 계산, Drive 체크포인트, 재개 가능)
from trl import SFTTrainer, SFTConfig
from unsloth.chat_templates import train_on_responses_only
import glob
cfg = SFTConfig(output_dir=f'{RUN_DIR}/checkpoints', per_device_train_batch_size=HP['batch'], gradient_accumulation_steps=HP['grad_acc'], num_train_epochs=HP['epochs'],
                learning_rate=HP['lr'], warmup_steps=HP['warmup_steps'], weight_decay=HP['weight_decay'], lr_scheduler_type=HP['lr_scheduler'], seed=HP['seed'],
                logging_steps=5, save_steps=HP['save_steps'], save_total_limit=3, eval_strategy='steps', eval_steps=HP['save_steps'], per_device_eval_batch_size=1,
                bf16=torch.cuda.is_bf16_supported(), fp16=not torch.cuda.is_bf16_supported(), optim='adamw_8bit', report_to='none', max_seq_length=HP['max_seq_len'], dataset_text_field='text', packing=False)
trainer = SFTTrainer(model=model, tokenizer=tokenizer, train_dataset=train_ds, eval_dataset=val_ds, args=cfg)
trainer = train_on_responses_only(trainer, instruction_part='<|im_start|>user\\n', response_part='<|im_start|>assistant\\n')
ckpts = sorted(glob.glob(f'{RUN_DIR}/checkpoints/checkpoint-*'), key=lambda p: int(p.rsplit('-', 1)[1]))
resume = ckpts[-1] if ckpts else None
print('resume from', resume)
result = trainer.train(resume_from_checkpoint=resume)
model.save_pretrained(f'{RUN_DIR}/adapter'); tokenizer.save_pretrained(f'{RUN_DIR}/adapter')
with open(f'{RUN_DIR}/logs/train_log.jsonl', 'w') as f:
    for e in trainer.state.log_history: f.write(json.dumps(e) + '\\n')
json.dump(dict(result.metrics, resumed_from=resume, steps=trainer.state.global_step), open(f'{RUN_DIR}/logs/train_result.json', 'w'), indent=2)
print(result.metrics)''')

code('''# 7. 평가 유틸 (JSON 파싱, 지표, public 오판 집계)
import re, time, json
LABELS = ['public','role_required','membership_required','tenant_match','owner_match','owner_or_admin','manual_review_required']
def parse(text):
    m = re.search(r'\\{.*\\}', text, re.S)
    try:
        o = json.loads(m.group(0)) if m else None
        return o if isinstance(o, dict) and o.get('label') in LABELS else None
    except Exception: return None
def generate(users, use_adapter):
    FastLanguageModel.for_inference(model); outs = []
    ctx = model.disable_adapter() if not use_adapter else __import__('contextlib').nullcontext()
    with ctx:
        for i in range(0, len(users), HP['eval_batch']):
            batch = users[i:i+HP['eval_batch']]
            prompts = [tokenizer.apply_chat_template(messages(u), tokenize=False, add_generation_prompt=True) for u in batch]
            tokenizer.padding_side = 'left'
            enc = tokenizer(prompts, return_tensors='pt', padding=True, truncation=True, max_length=HP['max_seq_len']).to('cuda')
            t0 = time.perf_counter()
            with torch.no_grad(): gen = model.generate(**enc, max_new_tokens=HP['eval_max_new_tokens'], do_sample=False, temperature=None, top_p=None, pad_token_id=tokenizer.pad_token_id)
            ms = (time.perf_counter() - t0) * 1000 / len(batch)
            for j in range(len(batch)):
                text = tokenizer.decode(gen[j][enc.input_ids.shape[1]:], skip_special_tokens=True)
                outs.append(dict(raw=text, parsed=parse(text), inference_ms=round(ms, 1)))
    return outs
def metrics(rows, outs):
    pred = [o['parsed']['label'] if o['parsed'] else 'output_error' for o in outs]; truth = [r['label'] for r in rows]
    per = {}
    for l in LABELS:
        tp = sum(t == l and p == l for t, p in zip(truth, pred)); fp = sum(t != l and p == l for t, p in zip(truth, pred)); fn = sum(t == l and p != l for t, p in zip(truth, pred))
        P = tp/(tp+fp) if tp+fp else 0.0; R = tp/(tp+fn) if tp+fn else 0.0; F = 2*P*R/(P+R) if P+R else 0.0
        per[l] = dict(support=sum(t == l for t in truth), precision=round(P,4), recall=round(R,4), f1=round(F,4))
    sup = [l for l in LABELS if per[l]['support']]
    conf = {a: {b: sum(t == a and p == b for t, p in zip(truth, pred)) for b in LABELS + ['output_error']} for a in LABELS}
    pub_bad = [r['id'] for r, p in zip(rows, pred) if p == 'public' and r['security_state'] == 'declared']
    return dict(records=len(rows), per_label=per, macro_f1_supported=round(sum(per[l]['f1'] for l in sup)/len(sup), 4), supported_labels=sup, confusion=conf,
                manual_ratio=round(pred.count('manual_review_required')/len(rows), 4), output_errors=pred.count('output_error'),
                public_misjudged_security_declared=len(pub_bad), public_misjudged_ids=pub_bad, declared_records=sum(r['security_state']=='declared' for r in rows),
                mean_inference_ms=round(sum(o['inference_ms'] for o in outs)/len(outs), 1),
                by_source={s: dict(records=sum(r['source']==s for r in rows), accuracy=round(sum(r['source']==s and t==p for r,t,p in zip(rows,truth,pred))/max(1,sum(r['source']==s for r in rows)),4)) for s in sorted({r['source'] for r in rows})})''')

code('''# 8. test_v30 평가: (a) 베이스 + v3.0.1, (b) LoRA v1 — 조건 oas / oas_code
results = {}
conditions = {'oas': test_rows, 'oas_code': [r for r in test_rows if 'oas_code_user' in r]}
for cond, rows in conditions.items():
    key = 'oas_user' if cond == 'oas' else 'oas_code_user'
    for name, use_adapter in (('base_v301', False), ('lora_v1', True)):
        outs = generate([r[key] for r in rows], use_adapter)
        with open(f'{RUN_DIR}/eval/predictions_{cond}_{name}.jsonl', 'w', encoding='utf-8') as f:
            for r, o in zip(rows, outs): f.write(json.dumps(dict(id=r['id'], label=r['label'], source=r['source'], security_state=r['security_state'], prediction=o['parsed'], raw=o['raw'], inference_ms=o['inference_ms']), ensure_ascii=False) + '\\n')
        results[f'{cond}/{name}'] = metrics(rows, outs)
        print(cond, name, 'macroF1', results[f'{cond}/{name}']['macro_f1_supported'], 'manual', results[f'{cond}/{name}']['manual_ratio'], 'public_misjudged', results[f'{cond}/{name}']['public_misjudged_security_declared'])
json.dump(dict(run=RUN_NAME, hp=HP, gpu=torch.cuda.get_device_name(0), results=results), open(f'{RUN_DIR}/eval/metrics.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)''')

code('''# 9. report.md 저장 (Drive)
def table(rows, header): return '| ' + ' | '.join(header) + ' |\\n|' + '|'.join('---' for _ in header) + '|\\n' + ''.join('| ' + ' | '.join(str(c) for c in r) + ' |\\n' for r in rows)
t = f"# LoRA v1 (data-v1) — test_v30 평가, run {RUN_NAME}, GPU {torch.cuda.get_device_name(0)}\\n\\n프롬프트 v3.0.1, 베이스 {HP['base_model']}, 해시 검증 통과(hashes.json). 하이퍼파라미터 config.json.\\n\\n## 요약\\n\\n"
t += table([[k, v['macro_f1_supported'], len(v['supported_labels']), f"{v['manual_ratio']:.1%}", f"{v['public_misjudged_security_declared']}/{v['declared_records']}", v['output_errors'], v['mean_inference_ms']] for k, v in results.items()],
           ['조건/모델', 'macro-F1', 'support 있는 label 수', 'manual 비율', 'public 오판(declared 중)', '출력 오류', '평균 ms'])
for k, v in results.items():
    t += f"\\n## {k}: label별 P/R/F1\\n\\n" + table([[l, d['support'], d['precision'], d['recall'], d['f1']] for l, d in v['per_label'].items()], ['label','support','P','R','F1'])
    cols = LABELS + ['output_error']
    t += '\\n혼동행렬(행=정답, 열=예측):\\n\\n| 정답\\\\예측 | ' + ' | '.join(cols) + ' |\\n|---|' + '---|'*len(cols) + '\\n' + ''.join('| ' + a + ' | ' + ' | '.join(str(v['confusion'][a][b]) for b in cols) + ' |\\n' for a in LABELS)
    t += '\\n출처별 정확도: ' + json.dumps(v['by_source']) + '\\n'
    if v['public_misjudged_ids']: t += '\\npublic 오판 id: ' + ', '.join(v['public_misjudged_ids']) + '\\n'
open(f'{RUN_DIR}/eval/report.md', 'w', encoding='utf-8').write(t); print(t[:3000])''')

nb = {'cells': cells, 'metadata': {'accelerator': 'GPU', 'colab': {'provenance': []}, 'kernelspec': {'display_name': 'Python 3', 'name': 'python3'}, 'language_info': {'name': 'python'}}, 'nbformat': 4, 'nbformat_minor': 5}
with open(HERE / 'lora_v1_colab.ipynb', 'w', encoding='utf-8', newline='\n') as f: json.dump(nb, f, ensure_ascii=False, indent=1)
print('written', HERE / 'lora_v1_colab.ipynb', len(cells), 'cells')
