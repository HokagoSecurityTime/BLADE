"""Paired 31-row development measurement; never starts full labeling."""
import asyncio
from collections import Counter
import json
import os
from pathlib import Path
import httpx
from training.data.label import read_env
from training.data.label_v6 import engine

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'reports/eval/classification_quality'


async def main():
    read_env(ROOT/'.env')
    model = os.getenv('BLADE_LABEL_MODEL','gpt-4o-mini')
    if os.getenv('BLADE_LABEL_PROVIDER','openai') != 'openai' or model not in {'gpt-4o-mini','gpt-4o-mini-2024-07-18'}:
        raise RuntimeError('Expected authorized OpenAI labeling model')
    settings = engine.llm.Settings('openai',model,os.environ['OPENAI_API_KEY'])
    split = json.loads((ROOT/'training/data/human_corrections_v5_split.json').read_text(encoding='utf8'))
    ids = split['validation_ids']
    inputs = {r['id']:r for r in engine.read(engine.INPUT)}
    extras = {r['id']:r for r in engine.read(OUT/'development_evidence.jsonl')}
    corrections = {r['id']:r for r in engine.read(ROOT/'training/data/human_corrections_v5.jsonl')}
    diagnoses = {r['id']:r['category'] for r in engine.read(OUT/'development_evidence.jsonl') if False}
    diagnoses = {r['id']:r['category'] for r in json.loads((OUT/'diagnosis.json').read_text(encoding='utf8'))}
    system = engine.PROMPT.read_text(encoding='utf8')
    baseline_payload = engine.payload
    # Preserve existing evidence-field vocabulary; source additions go in description
    # with explicit provenance rather than pretending to be operation description.
    def payload(row):
        value = baseline_payload(row)
        if row.get('_condition') == 'supplemented':
            value['description'] += '\n\nSupplemental source OAS context (not operation description):\n'+json.dumps(extras[row['id']]['supplemental_input'],ensure_ascii=False)
        return value
    engine.payload = payload
    manifest = dict(ids=ids, model=model,prompt_sha256=engine.digest(engine.PROMPT),
        input_sha256=engine.digest(engine.INPUT),evidence_sha256=engine.digest(OUT/'development_evidence.jsonl'),
        implementation_sha256=engine.digest(Path(__file__)),conditions=['original','supplemented'],temperature=0)
    stamp = OUT/'paired.manifest.json'
    if stamp.exists():
        assert json.loads(stamp.read_text(encoding='utf8')) == manifest
    else:
        engine.dump(stamp,manifest)
    path = OUT/'paired_results.jsonl'
    results = engine.read(path)
    done = {(r['id'],r['_condition']) for r in results}
    async with httpx.AsyncClient(timeout=180) as client:
        for ident in ids:
            for condition in manifest['conditions']:
                if (ident,condition) in done:
                    continue
                row = {**inputs[ident], '_condition':condition}
                result = await engine.request(row,system,settings,client,OUT/'paired_usage.jsonl')
                engine.append(path,result)
                results.append(result)
                print(f'{len(results)}/62',flush=True)
                if result['meta'].get('label_error'):
                    raise RuntimeError('Label error; checkpoint retained')
    summary = {}
    for condition in manifest['conditions']:
        group = [r for r in results if r['_condition']==condition]
        categories = {}
        for category in sorted({diagnoses.get(r['id'],'previously_correct') for r in group}):
            subset = [r for r in group if diagnoses.get(r['id'],'previously_correct')==category]
            categories[category] = dict(n=len(subset),correct=sum(r['label']==corrections[r['id']]['corrected_label'] for r in subset))
        summary[condition] = dict(n=len(group), correct=sum(r['label']==corrections[r['id']]['corrected_label'] for r in group),
            labels=dict(Counter(r['label'] for r in group)),categories=categories,
            evidence_invalid=sum(r['meta'].get('evidence_invalid',False) for r in group))
    engine.dump(OUT/'paired_summary.json',summary)
    lines = ['# 보충 입력 효과 측정', '',
        '기존 검증 31건을 동일 v2.6 프롬프트·gpt-4o-mini·temperature 0으로 조건별 재호출했다. 전체 재라벨링은 수행하지 않았다.', '',
        '| 입력 | 사람 라벨 일치 | 일치율 | evidence_invalid |','|---|---:|---:|---:|']
    for key,s in summary.items():
        lines.append(f"| {key} | {s['correct']}/{s['n']} | {s['correct']/s['n']:.2%} | {s['evidence_invalid']} |")
    lines += ['', '과거 v2.6은 3/31(9.68%). 이번 original 재호출과 supplemented를 비교해야 입력 효과와 시간에 따른 출력 변동을 일부 구분할 수 있다.', '',
        '| 진단 가설 | 건수 | original 정답 | supplemented 정답 |','|---|---:|---:|---:|']
    for category,s in summary['original']['categories'].items():
        lines.append(f"| {category} | {s['n']} | {s['correct']} | {summary['supplemented']['categories'][category]['correct']} |")
    lines += ['', '이 31건은 v5 오답에서 선정했고 이미 분석에 사용됐다. 일반 정확도나 독립 test 성능이 아니다. 범주는 기존 분석 가설이며 사람 확정 라벨을 수정하지 않았다.',
        '보충 입력은 기존 description 뒤에 별도 출처 문맥으로 명시했다. 프롬프트·근거 필드 규약은 유지했다. 각 조건 1회 측정으로 인과나 통계적 유의성을 보장하지 않는다.']
    (OUT/'paired_report.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps(summary,ensure_ascii=False))


if __name__ == '__main__':
    asyncio.run(main())
