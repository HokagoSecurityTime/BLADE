"""Prepare source-grounded development inputs, without changing labels/prompts."""
import hashlib
import json
from collections import Counter
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'datasets/blade/raw/openapi-directory/APIs'
OUT = ROOT/'reports/eval/classification_quality'


def main():
    split = json.loads((ROOT/'training/data/human_corrections_v5_split.json').read_text(encoding='utf-8'))
    ids = set(split['fewshot_ids']) | set(split['validation_ids'])
    analysis = json.loads((ROOT/'training/data/v6_error_analysis.json').read_text(encoding='utf-8'))
    errors = {r['id']:r for r in analysis['records']}
    packets, audit = [], []
    for line in (ROOT/'datasets/blade/processed/apisguru_enriched_v2.jsonl').read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        if row['id'] not in ids:
            continue
        enrich = row['enrichment']
        path = (SOURCE/enrich['source_file']).resolve()
        assert path.is_relative_to(SOURCE.resolve())
        spec = yaml.safe_load(path.read_text(encoding='utf-8')) if path.exists() else {}
        sha = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        # Added source text is isolated from human answers and diagnosis.
        extra = dict(service_info={k:spec.get('info',{}).get(k) for k in ['title','description'] if spec.get('info',{}).get(k)},
            security_details=enrich['security'], operation_tags=enrich['operation'].get('tags',[]),
            parameter_definitions=enrich['operation'].get('parameters',[]),
            unresolved_references=enrich.get('unresolved_references',[]))
        packets.append(dict(id=row['id'], partition='fewshot_development' if row['id'] in split['fewshot_ids'] else 'previously_inspected_validation',
            supplemental_input=extra, source_file=enrich['source_file'], source_sha256=sha,
            matches_enrichment_source_hash=sha == enrich.get('source_sha256')))
        if row['id'] in errors:
            e = errors[row['id']]
            audit.append(dict(id=row['id'],category=e['category'],human_label=e['human_label'],model_label=e['model_label'],
                diagnosis=e['diagnosis'],action=e['recommended_action'],human_confirmation=''))
    assert {p['id'] for p in packets} == ids
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'development_evidence.jsonl').write_text(''.join(json.dumps(p,ensure_ascii=False)+'\n' for p in packets),encoding='utf-8')
    lines = ['# 분류 품질 개선: 개발 근거 복구', '',
        '외부 API 호출 0회. 학습·라벨 변경·프롬프트 변경 없음. 고정 test를 읽거나 개선 규칙 선정에 사용하지 않았다.', '',
        f'- 사람 교정 개발 30건 및 기존 검증 31건: 총 {len(packets)}건의 보충 입력 생성.',
        f"- 서비스 설명 복구: {sum(bool(p['supplemental_input']['service_info'].get('description')) for p in packets)}건.",
        f"- 상세 security schemes 존재: {sum(bool(p['supplemental_input']['security_details'].get('schemes')) for p in packets)}건.",
        f"- 원본 해시 일치: {sum(p['matches_enrichment_source_hash'] for p in packets)}/{len(packets)}.",
        '- API key/JWT/OAuth 존재는 역할 제한의 증거가 아니다. 서비스가 공개 OAS를 제공한다는 것 또한 endpoint가 public이라는 증거가 아니다.',
        '- 서비스 설명·보안 정의·파라미터 정의는 보충 입력 파일에만 기록하며 사람 정답·교정 사유는 포함하지 않는다.',
        '- 이 보충 입력을 실제 모델이 사용한 효과는 아직 측정하지 않았다. 파일 생성만으로 품질 향상을 주장하지 않는다.',
        '- 기존 검증 31건은 오류 분석에 이미 사용됐다. 이후 튜닝 결과를 독립 일반화 성능으로 보고하지 않는다. 별도 미사용 사람 검수 표본이 필요하다.', '',
        '## 기준 재검수 대상', '',
        '기존 28건 분석의 범주 분류는 가설이며 사람 확정이 아니다. 아래 사례의 라벨은 자동 변경하지 않았다.', '',
        '| id | 범주 | 사람 label | 모델 label | 진단 | 확인 |', '|---|---|---|---|---|---|']
    for r in audit:
        if r['category'] in {'규칙·라벨 기준 충돌','사람 라벨 재확인'}:
            lines.append('| '+' | '.join(str(r[k]).replace('|','\\|').replace('\n',' ') for k in ['id','category','human_label','model_label','diagnosis'])+' | |')
    (OUT/'development_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'diagnosis.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(records=len(packets), hash_matches=sum(p['matches_enrichment_source_hash'] for p in packets),
        description=sum(bool(p['supplemental_input']['service_info'].get('description')) for p in packets),
        categories=dict(Counter(r['category'] for r in audit))),ensure_ascii=False))


if __name__ == '__main__':
    main()
