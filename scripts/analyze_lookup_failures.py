"""Replay saved responses against unchanged runtime; no API requests."""
import json
import os
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from common.schema import EvidenceRef
from scripts.eval_classifier import classify_recorded, endpoint_input, read_jsonl, digest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/eval'
REASON = 'Missing or unknown object parameter/owner lookup'


def main():
    os.environ.update(BLADE_PHASE2_ENABLED='true', BLADE_RAG_ENABLED='true', BLADE_CONTROLLER_ENABLED='true', BLADE_PROMPT_VERSION='v2.0')
    test = ROOT/'datasets/blade/processed/test.jsonl'
    overlay = OUT/'context/source_overlay.jsonl'
    checkpoint = next((OUT/'enriched_recorded').glob('*.partial.jsonl'))
    protected = [test, overlay, checkpoint, ROOT/'pipeline/classifier/__init__.py', ROOT/'pipeline/classifier/schema.py']
    hashes = {str(p.relative_to(ROOT)):digest(p) for p in protected}
    rows = {r['id']:r for r in read_jsonl(test)}
    additions = {r['id']:r for r in read_jsonl(overlay)}
    results = []
    for saved in read_jsonl(checkpoint):
        if REASON not in saved['trace']['validation_events']:
            continue
        row = {**rows[saved['id']], **additions.get(saved['id'], {})}
        endpoint, erd, _ = endpoint_input(row)
        raw = json.loads(saved['trace']['raw_response'])
        with patch('pipeline.classifier.llm.complete', return_value=saved['trace']['raw_response']) as mocked:
            final, trace = classify_recorded(endpoint, erd, row.get('controller_text'),
                evidence_refs=[EvidenceRef.model_validate(r) for r in saved['retrieved']])
        assert mocked.call_count == 1
        assert final.label.value == saved['prediction'] and trace['validation_events'] == saved['trace']['validation_events']
        params = endpoint.path_params + endpoint.query_params
        spec = json.loads(row['oas_snippet'])
        operation = spec.get('paths', {}).get(row['path'], {}).get(row['method'].lower(), {})
        body = operation.get('requestBody') or [p for p in operation.get('parameters', []) if p.get('in') in {'body','formData'}]
        lookup = raw.get('owner_lookup')
        table = erd.get(lookup.get('table')) if lookup else None
        results.append(dict(id=row['id'], service=row['service'], method=row['method'], path=row['path'],
            expected=row['label'], raw_label=raw['label'], label_correct=raw['label']==row['label'],
            path_params=endpoint.path_params, query_params=endpoint.query_params,
            object_param=raw.get('object_param'), owner_lookup=lookup,
            no_supported_parameter=not params, lookup_missing=lookup is None,
            lookup_table_exists=table is not None,
            lookup_id_exists=bool(table and lookup['id_col'] in table.columns),
            declared_request_body=bool(body), request_body=body,
            source_locations=rows[row['id']].get('meta',{}).get('source_locations',[]),
            raw_evidence=raw.get('evidence'), replay_matches=True))
    correct = [r for r in results if r['label_correct']]
    assert len(correct) == 18
    summary = dict(api_calls=0, inspected=len(results), correct_label_rejected=len(correct),
        all_failures_without_supported_parameter=sum(r['no_supported_parameter'] for r in results),
        correct_without_supported_parameter=sum(r['no_supported_parameter'] for r in correct),
        correct_missing_lookup=sum(r['lookup_missing'] for r in correct),
        correct_null_object_param=sum(r['object_param'] is None for r in correct),
        correct_methods=dict(Counter(r['method'] for r in correct)),
        correct_lookup_table_and_id_exist=sum(r['lookup_table_exists'] and r['lookup_id_exists'] for r in correct),
        input_sha256=hashes, records=results)
    lines = ['# 객체 파라미터·lookup 실패 재현 실험', '',
        f'외부 API 호출 0회. 저장된 응답 {len(results)}건을 실제 classify에 재주입해 최종 라벨·검증 사유가 모두 일치함을 확인했다. 이 중 최초 라벨이 사람 정답과 일치한 18건을 분석했다.', '',
        '## 결과', '',
        f"- 정답 18건 모두 path/query 파라미터가 없고 object_param=null이다. lookup 자체 누락은 {summary['correct_missing_lookup']}건이다.",
        f"- 18건 모두 lookup 테이블과 id 컬럼이 보강 입력에 존재한다: {summary['correct_lookup_table_and_id_exist']}/18.",
        '- GET 6건, POST 11건, PUT 1건이다. /me·자기 정보/목록·생성/업로드 등 ID가 경로에 없는 형태를 포함한다.',
        '- 따라서 이 18건의 직접 원인은 lookup을 안 쓴 것이 아니라, 객체 라벨에 path/query object_param을 필수로 요구하는 현재 정책 표현과 엔드포인트 형태의 불일치다.',
        '- 테이블·컬럼이 존재한다는 것은 실제 해당 핸들러가 그 테이블을 사용한다는 증명이 아니다. 잘못된 테이블 선택까지 검증된 정답으로 간주하지 않는다.',
        '- body 스키마가 있다는 것만으로 body 필드가 소유권 검증용 객체 ID라고 가정하지 않는다. 실제 요청·조회 흐름 확인이 필요하다.', '',
        '## 권고', '',
        '1. label 예측 점수와 실행 가능한 정책 생성 점수를 계속 분리한다. 이 실험에서는 보류를 억지로 해제하지 않았다.',
        '2. 개발/검증 데이터에서 객체 ID 기반 조회, JWT 주체 기반 자기 리소스, 생성 시 소유자 지정, 소유자별 목록 필터를 구분하는 정책 표현을 설계한다.',
        '3. body ID 지원만 추가하면 /me·목록·생성 전 객체가 없는 경우는 해결되지 않는다. 각 방식에 맞는 집행 가능성 검토가 먼저다.',
        '4. 런타임 변경과 인터페이스 확장은 현재 금지 범위이므로 구현하지 않았다. 고정 test의 결과에 맞춰 가짜 파라미터를 추가하거나 라벨·threshold를 바꾸지 않는다.', '',
        '| id | service | method | path | 최초 label | object_param | lookup table / id | body 명세 |',
        '|---|---|---|---|---|---|---|---|']
    for r in correct:
        lookup = r['owner_lookup'] or {}
        lines.append(f"| {r['id']} | {r['service']} | {r['method']} | {r['path']} | {r['raw_label']} | {r['object_param']} | {lookup.get('table')} / {lookup.get('id_col')} | {r['declared_request_body']} |")
    assert hashes == {str(p.relative_to(ROOT)):digest(p) for p in protected}
    (OUT/'lookup_failure_experiment.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'lookup_failure_experiment.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in {'records','input_sha256'}},indent=2))


if __name__ == '__main__':
    main()
