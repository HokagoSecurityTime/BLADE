"""Blind development review selection, excluding recorded prior exposure."""
import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from training.data.label_v5 import payload

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/eval/classification_quality/fresh_review_v1'


def main():
    dataset=ROOT/'datasets/blade/processed/apisguru_enriched_v2.jsonl'
    rows=[json.loads(s) for s in dataset.read_text(encoding='utf8').splitlines()]
    ids={r['id'] for r in rows}
    excluded=set(); sources=[]
    # Known human review, pilot selections, diagnoses and prompts. Full model
    # labeling outputs alone are not human exposure and are deliberately omitted.
    paths=set((ROOT/'training/data').glob('review*.md'))
    paths.update((ROOT/'training/data').glob('pilot*.json'))
    paths.update((ROOT/'training/data').glob('human_corrections*'))
    paths.update((ROOT/'training/data/prompts').glob('*.md'))
    paths.update((ROOT/'training/data').glob('*error_analysis*'))
    paths.update((ROOT/'training/data/policy_pilot_decisions').glob('*'))
    paths.update((ROOT/'reports/eval/classification_quality').glob('*.json*'))
    paths.update((ROOT/'reports/eval/classification_quality').glob('*.md'))
    for p in sorted(paths):
        if not p.is_file():continue
        text=p.read_text(encoding='utf8')
        found={i for i in ids if i in text}
        excluded.update(found)
        sources.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),matched_ids=len(found)))
    eligible=[r for r in rows if r['id'] not in excluded]
    assert len(eligible)>=100
    rng=random.Random(42)
    # Signal-only stratification avoids exposing or depending on old model labels.
    groups={k:[] for k in ['owner','tenant','both','path_only','none']}
    for r in eligible:groups[r['meta']['signal_class']].append(r)
    for group in groups.values():rng.shuffle(group)
    selected=[];counts=Counter()
    # Round robin across signals, cap each service at three records.
    while len(selected)<100:
        progress=False
        for group in groups.values():
            while group and counts[group[-1]['service']]>=3:group.pop()
            if group and len(selected)<100:
                row=group.pop();selected.append(row);counts[row['service']]+=1;progress=True
        assert progress, 'Insufficient service-diverse sample'
    selected.sort(key=lambda r:(r['service'],r['method'],r['path']))
    assert not {r['id'] for r in selected}&excluded
    assert not OUT.exists(), 'Preserve existing review'
    OUT.mkdir(parents=True)
    packets=[]
    for row in selected:
        value=payload(row)
        # Supply fixed source evidence only; no original labels/rationales.
        value['security_details']=row['enrichment']['security']
        packets.append(dict(id=row['id'],service=row['service'],input=value))
    (OUT/'blind_inputs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in packets),encoding='utf8')
    lines=['# 새 개발 검수표 100건', '',
        '기준: training/data/LABEL_STANDARD_DEV_V1.md. 아래 입력 근거만 보고 확정 라벨과 사유를 작성한다. 정보가 부족하면 manual_review_required를 사용할 수 있다.', '',
        '기존 모델 라벨은 숨겼다. signal_class 균형·service 최대 3건·seed 42 표본이며 모집단 분포를 대표하는 무작위 표본은 아니다.', '',
        '미사용은 저장된 검수·pilot·분석·예시 파일의 ID와 겹치지 않음을 뜻한다. APIs.guru 전량이 이전 자동 라벨링을 거쳤으므로 모델 호출 이력이 없는 데이터라는 뜻은 아니다.', '',
        '| 번호 | id | service | method | path | 확정 label | 검수 사유 |', '|---:|---|---|---|---|---|---|']
    for n,r in enumerate(packets,1):
        v=r['input'];lines.append(f"| {n} | {r['id']} | {r['service']} | {v['method']} | {v['path']} | | |")
    for n,r in enumerate(packets,1):
        lines+=['',f"## {n}. {r['id']}",'','입력 근거 전문:','','```json',json.dumps(r['input'],ensure_ascii=False,indent=2),'```']
    (OUT/'review_100.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    manifest=dict(seed=42,total_input=len(rows),excluded=len(excluded),eligible=len(eligible),selected=100,
        services=len(counts),max_per_service=max(counts.values()),signal_distribution=dict(Counter(r['meta']['signal_class'] for r in selected)),
        method_distribution=dict(Counter(r['method'] for r in selected)),ids=[r['id'] for r in selected],
        dataset_sha256=hashlib.sha256(dataset.read_bytes()).hexdigest(),exclusion_sources=sources,
        overlap=0,label_stratification=False,prior_automatic_labeling=True)
    (OUT/'selection_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in manifest.items() if k not in {'ids','exclusion_sources'}},ensure_ascii=False))


if __name__=='__main__':main()
