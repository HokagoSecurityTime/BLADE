"""[S1] test_v5 label ceiling: inter-annotator agreement (no training, no inference).
  sample  test_v5 283 -> 60 stratified by label support (labels with support < 10 get at least 5), seed 42
          -> reports/eval/human_agreement_v5/sample_60.json (ids + frozen label; internal, not shown to reviewers)
  sheets  review/human_agreement_v5_A.xlsx, review/human_agreement_v5_B.xlsx: identical content/order, label-blind
          included: endpoint (project/service/method/path), OAS snippet, handler code (controller_text), source permalink,
                    label definitions (prompt v3.0.1 '## 고정 라벨' + '## 보류가 필수인 경우' excerpt)
          excluded: frozen label, AI draft label/confidence/reason/auth_summary/evidence, every model prediction
          input columns: label (dropdown, 7), 확신도 (상/중/하), 근거 메모
  score   (step 3, run only when instructed after both sheets are returned)
test_v5.jsonl is hash-asserted against data_v5/test_v5_manifest.json and read only."""
from __future__ import annotations
import argparse, hashlib, json, random, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'scripts'))
from build_data_v4 import LABELS, permalink
TEST = ROOT / 'datasets/blade/processed/test_v5.jsonl'; MANIFEST = ROOT / 'datasets/blade/processed/data_v5/test_v5_manifest.json'
OUT = ROOT / 'reports/eval/human_agreement_v5'; REVIEW = ROOT / 'review'; PROMPT = ROOT / 'training/data/prompts/policy_label_v3.0.1.md'
SEED, N, MIN_SMALL, SMALL = 42, 60, 5, 10; CONF = ['상', '중', '하']; REVIEWERS = ['A', 'B']
PROMPT_SHA = 'd0913c27b5de185e7dd5734c111cb731f45e28ebca81fed787ff3914d02833ef'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_test():
    man = json.loads(MANIFEST.read_text(encoding='utf-8')); want = man['sha256']['datasets/blade/processed/test_v5.jsonl']
    assert sha(TEST) == want, 'test_v5.jsonl differs from the frozen manifest hash'
    assert sha(PROMPT) == PROMPT_SHA, 'prompt v3.0.1 changed'
    return [json.loads(l) for l in TEST.read_text(encoding='utf-8').splitlines() if l.strip()], want


def allocate(support: Counter, n: int) -> dict:
    """Proportional allocation (largest remainder), then lift labels with support < SMALL to min(MIN_SMALL, support),
    taking the difference from the largest allocations."""
    labels = sorted(support); total = sum(support.values())
    raw = {l: support[l] * n / total for l in labels}; alloc = {l: int(raw[l]) for l in labels}
    for l in sorted(labels, key=lambda l: (-(raw[l] - alloc[l]), l))[: n - sum(alloc.values())]: alloc[l] += 1
    for l in labels:
        if support[l] < SMALL and alloc[l] < min(MIN_SMALL, support[l]): alloc[l] = min(MIN_SMALL, support[l])
    while sum(alloc.values()) > n:
        big = max(labels, key=lambda l: (alloc[l], l)); alloc[big] -= 1
    assert sum(alloc.values()) == n and all(alloc[l] <= support[l] for l in labels), alloc
    return alloc


def sample(args):
    rows, test_sha = load_test(); support = Counter(r['label'] for r in rows); alloc = allocate(support, N)
    rng = random.Random(SEED); picked = []
    for l in sorted(alloc):
        pool = sorted([r for r in rows if r['label'] == l], key=lambda r: r['id']); picked += rng.sample(pool, alloc[l])
    picked.sort(key=lambda r: (r['meta']['project'], r['id']))  # neutral presentation order, identical in both sheets
    rep = dict(test_v5_sha256=test_sha, n_test=len(rows), n_sample=len(picked), seed=SEED, rule='label support proportional (largest remainder); support < 10 -> min 5',
               support=dict(support), allocation=alloc, by_project=dict(Counter(r['meta']['project'] for r in picked)),
               ids=[dict(id=r['id'], project=r['meta']['project'], method=r['method'], path=r['path'], label=r['label']) for r in picked])
    OUT.mkdir(parents=True, exist_ok=True); (OUT / 'sample_60.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({k: rep[k] for k in ('n_sample', 'support', 'allocation', 'by_project')}, ensure_ascii=False))


def defs_text():
    system = PROMPT.read_text(encoding='utf-8')
    body = system.split('## 고정 라벨')[1].split('## 판단 절차')[0]
    return ('프롬프트 v3.0.1 라벨 정의(발췌: "## 고정 라벨", "## 보류가 필수인 경우")\n\n## 고정 라벨' + body.rstrip()
            + '\n\n작성 방법: 각 행의 엔드포인트(method·path), OAS, 핸들러 코드(controller_text), source permalink만 보고 label 열(드롭다운 7종)을 고른다. '
              '확신도는 상/중/하, 근거 메모에는 판단 근거(코드 줄·명세 문구)를 적는다. 다른 검수자와 상의하지 않는다. 모든 행을 채운다(빈 칸은 미응답으로 집계).')


def sheets(args):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    rows, _ = load_test(); by_id = {r['id']: r for r in rows}; samp = json.loads((OUT / 'sample_60.json').read_text(encoding='utf-8'))
    picked = [by_id[x['id']] for x in samp['ids']]; assert len(picked) == N
    header = ['id', '검수자', 'project', 'service', 'method', 'path', 'OAS(oas_snippet)', 'controller_text(핸들러 코드)', 'source permalink', 'label', '확신도(상/중/하)', '근거 메모']
    widths = [26, 8, 11, 12, 8, 40, 60, 80, 40, 24, 12, 50]
    for rv in REVIEWERS:
        wb = Workbook(); ws = wb.active; ws.title = 'human_agreement_v5'; ws.append(header)
        for c in ws[1]: c.font = Font(bold=True); c.fill = PatternFill('solid', fgColor='DDEBF7'); c.alignment = Alignment(wrap_text=True, vertical='top')
        for r in picked: ws.append([r['id'], rv, r['meta']['project'], r['service'], r['method'], r['path'], r['oas_snippet'], r['controller_text'], permalink(r['meta']), '', '', ''])
        for i, w in enumerate(widths, 1): ws.column_dimensions[ws.cell(1, i).column_letter].width = w
        for row in ws.iter_rows(min_row=2):
            for c in row: c.alignment = Alignment(wrap_text=True, vertical='top')
        fill = PatternFill('solid', fgColor='FFF2CC')
        for col in ('J', 'K', 'L'):
            for i in range(2, N + 2): ws[f'{col}{i}'].fill = fill
        dv = DataValidation(type='list', formula1='"' + ','.join(LABELS) + '"', allow_blank=True, showErrorMessage=True); ws.add_data_validation(dv); dv.add(f'J2:J{N + 1}')
        dc = DataValidation(type='list', formula1='"' + ','.join(CONF) + '"', allow_blank=True, showErrorMessage=True); ws.add_data_validation(dc); dc.add(f'K2:K{N + 1}')
        ws.freeze_panes = 'C2'; ws.auto_filter.ref = ws.dimensions
        d = wb.create_sheet('라벨 정의'); d.column_dimensions['A'].width = 150
        for line in defs_text().splitlines(): d.append([line])
        for row in d.iter_rows():
            for c in row: c.alignment = Alignment(wrap_text=True, vertical='top')
        d.append([]); d.append(['입력 열: label(J, 드롭다운 7종) · 확신도(K, 상/중/하) · 근거 메모(L). 노란 칸만 채운다. 나머지 열은 수정하지 않는다.'])
        path = REVIEW / f'human_agreement_v5_{rv}.xlsx'; wb.save(path)
    # blind check: no frozen label / draft / prediction field leaked into either workbook
    from openpyxl import load_workbook
    banned = ['label', 'draft', 'confidence', 'reason', 'auth_summary', 'evidence', 'pred']
    for rv in REVIEWERS:
        wb = load_workbook(REVIEW / f'human_agreement_v5_{rv}.xlsx'); ws = wb['human_agreement_v5']
        hdr = [c.value for c in ws[1]]; assert hdr == header and ws.max_row == N + 1
        for b in banned: assert not any(b in str(h) for h in hdr if h not in ('label',)), (rv, b)
        for row in ws.iter_rows(min_row=2, values_only=True): assert row[9] in (None, '') and row[10] in (None, '') and row[11] in (None, '')
    a = [tuple(r) for r in load_workbook(REVIEW / 'human_agreement_v5_A.xlsx')['human_agreement_v5'].iter_rows(values_only=True)]
    b = [tuple(r) for r in load_workbook(REVIEW / 'human_agreement_v5_B.xlsx')['human_agreement_v5'].iter_rows(values_only=True)]
    assert [r[:1] + r[2:] for r in a] == [r[:1] + r[2:] for r in b], 'A/B content differs'
    rep = dict(rows=N, files={rv: (REVIEW / f'human_agreement_v5_{rv}.xlsx').relative_to(ROOT).as_posix() for rv in REVIEWERS},
               sha256={rv: sha(REVIEW / f'human_agreement_v5_{rv}.xlsx') for rv in REVIEWERS}, columns=header, excluded_fields=['label', 'meta.draft_*', 'meta.auth_summary', 'meta.evidence', 'meta.final_reason', 'meta.review_note', 'model predictions'])
    (OUT / 'sheets_report.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8'); print(json.dumps(rep, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('stage', choices=['sample', 'sheets']); a = ap.parse_args()
    {'sample': sample, 'sheets': sheets}[a.stage](a)


if __name__ == '__main__': main()
