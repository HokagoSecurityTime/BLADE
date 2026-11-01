"""Authorized abstention-only prompt experiment on previously inspected 31 rows."""
import asyncio
import json
import os
from pathlib import Path
from collections import Counter
import httpx
from training.data.label import read_env
from training.data.label_v6 import engine

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'reports/eval/classification_quality'


def make_prompt():
    original = engine.PROMPT.read_text(encoding='utf8')
    lines = original.splitlines()
    for i,line in enumerate(lines):
        if line.startswith('결정 트리:'):
            lines[i] = line[:line.index('manual_review_required는')]+'manual_review_required는 신호가 모순되거나, 구체 인가 패턴을 구분할 근거가 부족한 경우 허용한다.'
        elif line.startswith('4. owner_match는'):
            lines[i] = line[:line.index('소유 단서 없는 콘텐츠는')]+'소유 단서 없는 콘텐츠는 명시적 공개 근거가 있으면 public, 그 외에는 근거 부족 시 manual_review_required로 보류한다.'
        elif line.startswith('6. confidence:'):
            lines[i] = line.replace('약한 추정→0.4(예: 사용자 단서 없는 콘텐츠 ID에서 가장 가능성 높은 패턴)', '근거가 약하지만 구체 패턴을 지지하는 경우→0.4; 콘텐츠 ID만 있어 패턴을 구분할 수 없으면 manual_review_required')
        elif line.startswith('1. confidence와 label을 분리한다.'):
            lines[i] = '1. confidence와 label을 분리한다. 낮은 confidence만으로 보류하지 않는다. 신호가 모순되거나 인가 패턴을 구분할 근거가 부족하면 manual_review_required를 사용한다. 객체 식별자·스코프·설명의 존재만으로 구체 라벨을 강제하지 않는다. 예시의 교정도 이 근거 충분성 규칙과 충돌하면 이 규칙을 따른다.'
        elif line.startswith('2. confidence 네 구간'):
            lines[i] = line.replace('약한 추정(콘텐츠 객체 ID만 있고 공개 여부 불명) → 가장 가능성 높은 label 0.4.', '약하지만 구체 패턴을 지지하는 근거 → 해당 label 0.4. 콘텐츠 ID만 있고 정책 구분 근거가 없으면 manual_review_required.')
    return '\n'.join(lines)+'\n'


async def main():
    read_env(ROOT/'.env')
    model = os.getenv('BLADE_LABEL_MODEL','gpt-4o-mini')
    assert os.getenv('BLADE_LABEL_PROVIDER','openai')=='openai' and model in {'gpt-4o-mini','gpt-4o-mini-2024-07-18'}
    settings = engine.llm.Settings('openai',model,os.environ['OPENAI_API_KEY'])
    system = make_prompt()
    prompt = ROOT/'training/data/prompts/policy_label_v2.6_abstention_dev.md'
    if prompt.exists():
        assert prompt.read_text(encoding='utf8')==system
    else:
        prompt.write_text(system,encoding='utf8')
    ids = json.loads((ROOT/'training/data/human_corrections_v5_split.json').read_text(encoding='utf8'))['validation_ids']
    baseline = {r['id']:r for r in engine.read(OUT/'paired_results.jsonl') if r['_condition']=='supplemented'}
    corrections = {r['id']:r for r in engine.read(ROOT/'training/data/human_corrections_v5.jsonl')}
    extras = {r['id']:r for r in engine.read(OUT/'development_evidence.jsonl')}
    inputs = {r['id']:r for r in engine.read(engine.INPUT)}
    original_payload = engine.payload
    def payload(row):
        value = original_payload(row)
        value['description'] += '\n\nSupplemental source OAS context (not operation description):\n'+json.dumps(extras[row['id']]['supplemental_input'],ensure_ascii=False)
        return value
    engine.payload = payload
    engine.VERSION = 'policy-label-v2.6-abstention-dev'
    manifest = dict(ids=ids,model=model,prompt_sha256=engine.digest(prompt),input_sha256=engine.digest(engine.INPUT),
        evidence_sha256=engine.digest(OUT/'development_evidence.jsonl'),baseline_sha256=engine.digest(OUT/'paired_results.jsonl'),
        implementation_sha256=engine.digest(Path(__file__)),temperature=0)
    stamp = OUT/'abstention.manifest.json'
    if stamp.exists():
        assert json.loads(stamp.read_text(encoding='utf8'))==manifest
    else:
        engine.dump(stamp,manifest)
    output = OUT/'abstention_results.jsonl'
    results = engine.read(output)
    done = {r['id'] for r in results}
    assert len(done)==len(results) and done<=set(ids)
    async with httpx.AsyncClient(timeout=180) as client:
        for ident in ids:
            if ident in done:
                continue
            r = await engine.request(inputs[ident],system,settings,client,OUT/'abstention_usage.jsonl')
            engine.append(output,r)
            results.append(r)
            print(f'{len(results)}/31',flush=True)
            if r['meta'].get('label_error'):
                raise RuntimeError('Label error: stop, checkpoint retained')
    def score(rows):
        concrete = [r for r in rows if r['label']!='manual_review_required']
        return dict(n=len(rows),correct=sum(r['label']==corrections[r['id']]['corrected_label'] for r in rows),
            concrete_n=len(concrete),concrete_correct=sum(r['label']==corrections[r['id']]['corrected_label'] for r in concrete),
            labels=dict(Counter(r['label'] for r in rows)),evidence_invalid=sum(bool(r['meta'].get('evidence_invalid')) for r in rows))
    summary = dict(before=score(list(baseline.values())),after=score(results),
        transitions=[dict(id=r['id'],human=corrections[r['id']]['corrected_label'],before=baseline[r['id']]['label'],after=r['label'],rationale=r['rationale']) for r in results])
    engine.dump(OUT/'abstention_summary.json',summary)
    lines = ['# 強制 선택 제거 실험', '', '동일 보충 입력·gpt-4o-mini·temperature 0, 기존 31건. before는 직전 supplemented 실행을 재사용했다.', '',
        '| 조건 | 일치 | 보류 | 구체 선택률 | 구체 선택 정확도 | evidence_invalid |','|---|---:|---:|---:|---:|---:|']
    for key in ['before','after']:
        s=summary[key];n=s['n'];c=s['concrete_n']
        accuracy=f"{s['concrete_correct']/c:.2%}" if c else 'N/A'
        lines.append(f"| {key} | {s['correct']}/{n} ({s['correct']/n:.2%}) | {n-c}/{n} | {c/n:.2%} | {accuracy} ({s['concrete_correct']}/{c}) | {s['evidence_invalid']} |")
    lines += ['', '이 표본은 v5 오류에서 선정됐고 분석에 사용됐다. 일반 성능 추정이나 독립 검증이 아니다. 보류 증가만으로 개선이라고 판단하지 않는다. 단일 실행 및 이전 대조군 재사용으로 출력 변동의 영향이 남는다.', '',
        '| id | 사람 label | before | after | rationale |','|---|---|---|---|---|']
    for r in summary['transitions']:
        lines.append('| '+' | '.join(str(r[k]).replace('|','\\|').replace('\n',' ') for k in ['id','human','before','after','rationale'])+' |')
    (OUT/'abstention_report.md').write_text('\n'.join(lines).replace('強制','강제')+'\n',encoding='utf8')
    print(json.dumps({k:summary[k] for k in ['before','after']}))


if __name__=='__main__':
    asyncio.run(main())
