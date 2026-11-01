"""Writes training/lora/lora_v2_abstain_calib.ipynb (rev 2): label-conditional log-probability scoring (no generation for the scores, no training)
of the three LoRA v2 final adapters on val_v2 (oas / oas_code) and test_v30 (oas / oas_code). Output: per-label score jsonl under runs/lora_v2_seed<N>/calib/.
Rev 2 changes (after the first run produced invalid scores: top-label log-prob ~ -20 nat, 55-62% agreement with greedy generation in oas_code):
  - FastLanguageModel.for_inference() before scoring; cache mode primary, full mode uses RIGHT padding and absolute position indexing (no left padding);
  - mandatory self-check cell: on 5 val inputs the greedy-generated label must equal the scoring argmax and the top log-prob must be > -3 nat, else abort;
  - output file names and records carry the adapter tag; the summary cell prints tag per folder.
The manual penalty b is chosen later, locally and on val_v2 only, by scripts/calib_abstain.py.
Usage: python build_notebook_calib.py [runpod]  - 'runpod' writes lora_v2_abstain_calib_runpod.ipynb (no Drive mount, BASE=/workspace/blade_lora_v2, pip unsloth); cells 4-8 are identical."""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
H = json.loads((HERE / 'data_v2/data_v2_hashes.json').read_text(encoding='utf-8'))
RUNPOD = len(sys.argv) > 1 and sys.argv[1] == 'runpod'
BASE_PATH = '/workspace/blade_lora_v2' if RUNPOD else '/content/drive/MyDrive/blade_lora_v2'
UNSLOTH_PIP = 'unsloth' if RUNPOD else '"unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"\n%pip -q install --no-deps trl peft accelerate bitsandbytes xformers'   # RunPod: unsloth가 torch에 맞는 의존성을 함께 설치
NB_NAME = 'lora_v2_abstain_calib_runpod.ipynb' if RUNPOD else 'lora_v2_abstain_calib.ipynb'
cells = []
def md(s): cells.append({'cell_type': 'markdown', 'metadata': {}, 'source': s})
def code(s): cells.append({'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [], 'source': s})

md('''# BLADE LoRA v2 — 보류 문턱 조정용 label 조건부 로그확률 스코어링 (rev 2; 학습 없음)

seed 42·43·44 **final 어댑터**에 대해 val_v2(oas 52 / oas_code 46)와 test_v30(oas 269 / oas_code 265) 입력마다 7개 label 각각의 조건부 로그확률을 계산한다.
방법: 프롬프트(v3.0.1 system + user) 뒤에 assistant 응답 접두 `{"label": "`를 붙이고, 각 label 문자열 + `"`의 토큰 로그확률 합을 teacher forcing으로 구한다.
결과: `runs/lora_v2_seed<N>/calib/scores_{val|test}_{oas|oas_code}_lora_v2_s<N>_final.jsonl` (**파일 이름과 레코드의 tag가 어댑터 seed를 나타낸다. 폴더 이름이 아니라 tag를 믿는다**).

**rev 2**: 1차 실행 점수가 비정상(최고 label 로그확률 ≈ −20 nat, oas_code에서 생성 예측과 55~62% 일치)이어서 (1) `for_inference()` 적용, (2) full 모드를 왼쪽 패딩 → **오른쪽 패딩 + 절대 위치 인덱싱**으로 변경, (3) **자가 검증 셀(6)**: val 5건에서 greedy 생성 label == 스코어 argmax 이고 최고 로그확률 > −3 nat 이어야 진행, 아니면 중단. 감점 b 선택은 이 노트북에서 하지 않는다(로컬 `scripts/calib_abstain.py`, val_v2만 사용).

API 키·토큰 불필요. 예상 시간(A100): 어댑터당 약 20~40분 → 3 seed 1~2시간.''')

if RUNPOD:
    code('''# 1. RunPod: 볼륨 경로·HF 캐시 확인(Drive 마운트 없음). data_v2/ 5개 파일과 runs/lora_v2_seed<N>/adapter/ 를 미리 /workspace/blade_lora_v2 에 올려 둔다
import os
os.environ.setdefault('HF_HOME', '/workspace/hf')   # 베이스 모델 다운로드를 볼륨에 캐시(unsloth import 전에 설정)
BASE = '/workspace/blade_lora_v2'
need = [f'{BASE}/data_v2/{n}' for n in ('train_sft.jsonl', 'val_sft.jsonl', 'test_v30_inputs.jsonl', 'policy_label_v3.0.1.md', 'data_v2_hashes.json')]
need += [f'{BASE}/runs/lora_v2_seed{s}/adapter/{n}' for s in (42, 43, 44) for n in ('adapter_config.json', 'adapter_model.safetensors')]
missing = [p for p in need if not os.path.exists(p)]
assert not missing, f'필요 파일 없음, 중단: {missing}'
print('HF_HOME', os.environ['HF_HOME'], '| files OK')''')
else:
    code('''# 1. Google Drive 마운트
from google.colab import drive
drive.mount('/content/drive')''')

code(f'''# 2. 설정 (v2 학습 노트북과 같은 BASE/DATA_DIR; 어댑터는 runs/lora_v2_seed<N>/adapter)
import os, json, time, glob
BASE = '{BASE_PATH}'
DATA_DIR = f'{{BASE}}/data_v2'
SEEDS = [42, 43, 44]
ADAPTER = lambda seed: f'{{BASE}}/runs/lora_v2_seed{{seed}}/adapter'
OUT = lambda seed: f'{{BASE}}/runs/lora_v2_seed{{seed}}/calib'
HP = dict(base_model='unsloth/Qwen2.5-7B-Instruct-bnb-4bit', max_seq_len=4096, prompt_version='policy-label-v3.0.1', data_version='data-v2', rev=2)
LABELS = ['public','role_required','membership_required','tenant_match','owner_match','owner_or_admin','manual_review_required']
PREFIX_JSON = '{{"label": "'      # assistant 응답 접두(학습 target 형식과 동일: {{"label": "<label>", "confidence": ...}})
SCORE_MODE = 'cache'             # 'cache'(prefix 1회 + label별 continuation) / 'full'(오른쪽 패딩 배치). 셀 6 자가 검증을 통과한 모드만 사용
RESCORE = True                   # True면 rev 1(mode='full', rev 없음)으로 만들어진 기존 점수 파일을 .rev1.bak 으로 옮기고 다시 계산
INCLUDE_BASE = False             # True면 seed 42 폴더에 베이스 모델(어댑터 없음) 점수도 저장
print(HP, SEEDS)''')

code(f'''# 3. 패키지 설치
%pip -q install {UNSLOTH_PIP}
import torch; print(torch.cuda.get_device_name(0), torch.cuda.get_device_properties(0).total_memory // 2**30, 'GB')''')

code(f'''# 4. 데이터 로드 + data-v2 입력 해시 검증 (불일치면 중단)
import hashlib, json
EXPECTED = {json.dumps(H['generated'], indent=4)}
EXPECTED_SOURCES = {json.dumps(H['data_v2_sources'], indent=4)}   # AGENTS.md data-v2 절 기록값
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
mismatch = {{n: (sha(f'{{DATA_DIR}}/{{n}}'), h) for n, h in EXPECTED.items() if sha(f'{{DATA_DIR}}/{{n}}') != h}}
assert not mismatch, f'data-v2 입력 해시 불일치, 중단: {{mismatch}}'
rec = json.load(open(f'{{DATA_DIR}}/data_v2_hashes.json')); assert rec['data_v2_sources'] == EXPECTED_SOURCES, 'data_v2_hashes.json 원본 해시 불일치, 중단'
def read(p): return [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
SYSTEM = open(f'{{DATA_DIR}}/policy_label_v3.0.1.md', encoding='utf-8').read()
val_rows, test_rows = read(f'{{DATA_DIR}}/val_sft.jsonl'), read(f'{{DATA_DIR}}/test_v30_inputs.jsonl')
TARGETS = [('val', 'oas', [r for r in val_rows if r['condition'] == 'oas'], 'user'), ('val', 'oas_code', [r for r in val_rows if r['condition'] == 'oas_code'], 'user'),
           ('test', 'oas', test_rows, 'oas_user'), ('test', 'oas_code', [r for r in test_rows if 'oas_code_user' in r], 'oas_code_user')]
print([(s, c, len(rows)) for s, c, rows, _ in TARGETS], 'hash OK')
for s, c, rows, key in TARGETS: assert all(key in r for r in rows), (s, c, key)''')

code('''# 5. 스코어링 함수
from unsloth import FastLanguageModel
from peft import PeftModel
import torch, copy, time, re, torch.nn.functional as F
def messages(user): return [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': user}]
def load(seed_or_none):
    base, tok = FastLanguageModel.from_pretrained(model_name=HP['base_model'], max_seq_length=HP['max_seq_len'], dtype=None, load_in_4bit=True)
    model = PeftModel.from_pretrained(base, ADAPTER(seed_or_none)) if seed_or_none is not None else base
    FastLanguageModel.for_inference(model); model.eval(); return model, tok
def cont_ids(tok):
    # label 토큰열은 접두와 따로 토크나이즈해 이어붙인다(로컬 확인: Qwen2.5 토크나이저에서 접두+label+" 의 연결 토큰화와 전체 토큰화가 7개 label 모두 일치)
    return {lab: tok(lab + '"', add_special_tokens=False).input_ids for lab in LABELS}
def prompt_text(user): return tok.apply_chat_template(messages(user), tokenize=False, add_generation_prompt=True) + PREFIX_JSON
def prompt_ids(tok, user):
    ids = tok(prompt_text(user), add_special_tokens=False).input_ids; trunc = False
    if len(ids) > HP['max_seq_len'] - 8: ids = ids[:HP['max_seq_len'] - 8]; trunc = True
    return ids, trunc
@torch.no_grad()
def score_cache(model, ids, CONT):
    x = torch.tensor([ids], device='cuda'); out = model(input_ids=x, use_cache=True); past = out.past_key_values
    assert past is not None, 'no past_key_values returned'
    last = F.log_softmax(out.logits[0, -1].float(), -1); res = {}
    for lab, cont in CONT.items():
        lp = last[cont[0]].item()
        if len(cont) > 1:
            o2 = model(input_ids=torch.tensor([cont[:-1]], device='cuda'), past_key_values=copy.deepcopy(past), use_cache=True)
            lps = F.log_softmax(o2.logits[0].float(), -1); lp += sum(lps[i, cont[i + 1]].item() for i in range(len(cont) - 1))
        res[lab] = lp
    return res, int(last.argmax())
@torch.no_grad()
def score_full(model, ids, CONT, chunk=4):
    # 오른쪽 패딩: 모든 행이 같은 prefix로 시작하므로 위치 P-1..P+k-2 를 절대 인덱스로 읽는다(패딩은 뒤에만 있어 causal attention에 영향 없음)
    P = len(ids); labs = list(CONT); seqs = [ids + CONT[l][:-1] for l in labs]; T = max(len(s) for s in seqs)
    pad = tok.pad_token_id if tok.pad_token_id is not None else 0; res = {}; first = None
    for s0 in range(0, len(seqs), chunk):
        part = seqs[s0:s0 + chunk]; inp = torch.full((len(part), T), pad, dtype=torch.long); att = torch.zeros((len(part), T), dtype=torch.long)
        for i, s in enumerate(part): inp[i, :len(s)] = torch.tensor(s); att[i, :len(s)] = 1
        out = model(input_ids=inp.cuda(), attention_mask=att.cuda()); logits = out.logits.float()
        for i, lab in enumerate(labs[s0:s0 + chunk]):
            cont = CONT[lab]; k = len(cont); lps = F.log_softmax(logits[i, P - 1:P - 1 + k, :], -1); res[lab] = sum(lps[j, cont[j]].item() for j in range(k))
            if first is None: first = int(logits[i, P - 1, :].argmax())
        del out, logits
    return res, first
def score_one(model, tok, user, CONT, mode):
    ids, trunc = prompt_ids(tok, user); t0 = time.perf_counter()
    res, top = (score_cache if mode == 'cache' else score_full)(model, ids, CONT)
    return dict(scores={k: round(v, 4) for k, v in res.items()}, first_token_argmax=tok.decode([top]) if top is not None and top >= 0 else None, prompt_tokens=len(ids), truncated=trunc, ms=round((time.perf_counter() - t0) * 1000, 1), mode=mode, rev=HP['rev'])
@torch.no_grad()
def greedy_label(model, tok, user, max_new_tokens=12):
    enc = tok(prompt_text(user), return_tensors='pt', add_special_tokens=False).to('cuda')
    gen = model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False, temperature=None, top_p=None, pad_token_id=tok.pad_token_id)
    text = tok.decode(gen[0][enc.input_ids.shape[1]:], skip_special_tokens=True); m = re.match(r'\\s*([a-z_]+)', text)
    return (m.group(1) if m else None), text''')

code('''# 6. 자가 검증 (필수): val oas_code 5건 — greedy 생성 label == 스코어 argmax, 최고 로그확률 > −3 nat. 실패 시 중단
model, tok = load(SEEDS[0]); CONT = cont_ids(tok); print({k: len(v) for k, v in CONT.items()})
def check(mode, rows):
    ok = 0; rep = []
    for r in rows:
        try: o = score_one(model, tok, r['user'], CONT, mode)
        except Exception as e: return 0, [f'{mode} 실패: {e!r}']
        g, text = greedy_label(model, tok, r['user']); top = max(o['scores'], key=o['scores'].get)
        good = (g == top) and (o['scores'][top] > -3.0); ok += good
        rep.append(dict(id=r['id'], greedy=g, argmax=top, top_logp=round(o['scores'][top], 3), ms=o['ms'], ok=good))
    return ok, rep
rows5 = TARGETS[1][2][:5]; mode = None
for m in ([SCORE_MODE] + [x for x in ('cache', 'full') if x != SCORE_MODE]):
    ok, rep = check(m, rows5); print(m, ok, '/ 5'); [print('  ', x) for x in rep]
    if ok >= 4: mode = m; break
assert mode is not None, '자가 검증 실패: 두 모드 모두 greedy 생성과 불일치하거나 로그확률이 비정상. 점수 파일을 만들지 않고 중단.'
a = score_one(model, tok, rows5[0]['user'], CONT, 'cache') if mode == 'full' else None
print('SCORE_MODE =', mode)''')

code('''# 7. 실행: seed별 final 어댑터 × (val oas, val oas_code, test oas, test oas_code). 재개 가능(기존 rev2 파일의 id는 건너뜀; rev1 파일은 RESCORE=True면 .rev1.bak으로 이동)
def run_adapter(model, tok, tag, out_dir):
    os.makedirs(out_dir, exist_ok=True); CONT = cont_ids(tok)
    for split, cond, rows, key in TARGETS:
        path = f'{out_dir}/scores_{split}_{cond}_{tag}.jsonl'
        if os.path.exists(path):
            old = read(path)
            if old and old[0].get('rev') != HP['rev'] and RESCORE: os.replace(path, path + '.rev1.bak'); print('moved rev1 file ->', path + '.rev1.bak'); old = []
            done = {r['id'] for r in old if r.get('rev') == HP['rev']}
        else: done = set()
        todo = [r for r in rows if r['id'] not in done]; print(tag, split, cond, 'todo', len(todo), 'done', len(done)); t0 = time.time()
        with open(path, 'a', encoding='utf-8') as f:
            for i, r in enumerate(todo):
                o = score_one(model, tok, r[key], CONT, mode)
                rec = dict(id=r['id'], label=r['label'], source=r['source'], security_state=r['security_state'], split=split, condition=cond, tag=tag, prompt_version=HP['prompt_version'], **o)
                f.write(json.dumps(rec, ensure_ascii=False) + '\\n')
                if (i + 1) % 25 == 0: f.flush(); print(f'  {i + 1}/{len(todo)} {time.time() - t0:.0f}s')
        print(tag, split, cond, 'done', f'{time.time() - t0:.0f}s')
for SEED in SEEDS:
    if SEED != SEEDS[0] or model is None:
        del model; torch.cuda.empty_cache(); model, tok = load(SEED)
    # 어댑터별 재검증 1건 (greedy == argmax)
    g, _ = greedy_label(model, tok, TARGETS[1][2][0]['user']); o = score_one(model, tok, TARGETS[1][2][0]['user'], cont_ids(tok), mode); top = max(o['scores'], key=o['scores'].get)
    print('seed', SEED, 'check greedy', g, 'argmax', top, 'top_logp', o['scores'][top]); assert g == top and o['scores'][top] > -3.0, f'seed {SEED} 자가 검증 실패, 중단'
    run_adapter(model, tok, f'lora_v2_s{SEED}_final', OUT(SEED))
    model = None
if INCLUDE_BASE:
    model, tok = load(None); run_adapter(model, tok, 'base_v301', OUT(42)); del model; torch.cuda.empty_cache()
print('done. 산출물:', sorted(glob.glob(f'{BASE}/runs/lora_v2_seed*/calib/*.jsonl')))''')

code('''# 8. 요약·회수 안내 (폴더 ≠ tag 불일치 검사 포함)
import collections
for p in sorted(glob.glob(f'{BASE}/runs/lora_v2_seed*/calib/scores_*.jsonl')):
    rows = read(p); am = collections.Counter(max(r['scores'], key=r['scores'].get) for r in rows); tags = collections.Counter(r.get('tag') for r in rows)
    folder_seed = re.search(r'lora_v2_seed(\\d+)', p).group(1); tag_seed = re.search(r'_s(\\d+)_', os.path.basename(p)).group(1)
    tops = sorted(max(r['scores'].values()) for r in rows)
    print(os.path.relpath(p, BASE), len(rows), 'tag', dict(tags), 'folder==tag', folder_seed == tag_seed, 'rev', collections.Counter(r.get('rev') for r in rows), 'argmax manual', am['manual_review_required'], 'top_logp median', round(tops[len(tops) // 2], 2))
print('회수: runs/lora_v2_seed<N>/calib/ 폴더를 통째로 로컬 reports/eval/lora_v2/calib/lora_v2_seed<N>/ 로 복사(폴더 이름은 tag와 일치해야 함) →  python scripts/calib_abstain.py  (README_colab_calib.md)')''')

meta = {'kernelspec': {'display_name': 'Python 3', 'name': 'python3'}, 'language_info': {'name': 'python'}}
if not RUNPOD: meta = {'accelerator': 'GPU', 'colab': {'provenance': []}, **meta}
nb = {'cells': cells, 'metadata': meta, 'nbformat': 4, 'nbformat_minor': 5}
with open(HERE / NB_NAME, 'w', encoding='utf-8', newline='\n') as f: json.dump(nb, f, ensure_ascii=False, indent=1)
print('written', HERE / NB_NAME, len(cells), 'cells')
