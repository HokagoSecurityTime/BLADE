"""Offline attribution of saved baseline results; never reconstruct missing raw labels."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/eval'
MANUAL = 'manual_review_required'
REASONS = {
    'Missing or unknown object parameter/owner lookup': 'object_binding',
    'Unknown lookup table or id column': 'lookup_table_or_id',
    'Cannot identify ownership column in ERD': 'ownership_column',
    'Unknown ownership column in ERD': 'ownership_column',
    'owner_or_admin requires admin role': 'admin_role',
    'Caller-attribute/public policy conflicts with object lookup': 'unexpected_lookup',
    'Missing required roles': 'roles',
    'Missing allowed membership': 'membership',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    paths = sorted(OUT.glob('*.partial.jsonl'))
    protected = paths + list(OUT.glob('*_metrics.json')) + [
        ROOT / 'datasets/blade/processed/test.jsonl',
        ROOT / 'pipeline/classifier/__init__.py',
        ROOT / 'pipeline/classifier/schema.py', ROOT / 'scripts/eval_classifier.py']
    before = {str(p.relative_to(ROOT)): digest(p) for p in protected}
    report = {'input_sha256': before, 'api_calls': 0, 'raw_outputs_saved': False,
              'attribution': 'Runtime reason signatures interpreted against current source; original raw responses were not saved.',
              'runs': {}}
    lines = ['# 기존 베이스라인 검증 단계 감사', '',
        'API 호출 0회. 원시 응답은 저장되지 않았다. 아래는 최종 결과와 런타임 사유 문자열에 따른 분해이며, 원시 라벨의 F1 또는 검증 전후 점수 차이를 복원한 결과가 아니다.', '',
        '구체 라벨로 남은 결과는 런타임에서 label이 바뀌지 않은 결과다. 검증 실패 사유는 현재 코드의 반환 문자열과 대조했다. 원시 응답이 없으므로 모델이 동일 문자열을 직접 출력했을 가능성까지 배제하는 실행 추적 증거는 아니다.', '',
        '| 설정 | 최종 macro-F1 | 구체 라벨 정답 | 구체 라벨 오답 | 정책 검증→보류 | JSON/schema 실패 | 원인 구분 불가 보류 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    sections = []
    for path in paths:
        rows = [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()]
        assert len(rows) == 253 and len({r['id'] for r in rows}) == 253
        counts, details, reasons = Counter(), [], Counter()
        for row in rows:
            c = row['classification']
            assert c['label'] == row['prediction']
            reason = c['evidence']
            if row['prediction'] != MANUAL:
                stage = 'unchanged_correct' if row['prediction'] == row['expected'] else 'unchanged_wrong'
            elif reason in REASONS and c['confidence'] == 0:
                stage = 'policy_validation_fallback'
                reasons[reason] += 1
            elif reason == 'Invalid classification JSON or schema; manual review required':
                stage = 'schema_failure'
            else:
                stage = 'manual_origin_unknown'
            counts[stage] += 1
            details.append(dict(id=row['id'], service=row['service'], expected=row['expected'],
                final_label=row['prediction'], saved_confidence=c['confidence'], stage=stage,
                raw_label=row['prediction'] if row['prediction'] != MANUAL else None,
                erd_table_count=row.get('erd_table_count'), evidence=reason))
        metric = json.loads(path.with_name(path.name.replace('.partial.jsonl', '_metrics.json')).read_text(encoding='utf-8'))['metrics']
        fallback = [r for r in details if r['stage'] == 'policy_validation_fallback']
        name = path.name[0]
        report['runs'][name] = dict(counts=dict(counts), final_macro_f1=metric['macro_f1'],
            final_correct=sum(r['expected'] == r['prediction'] for r in rows),
            fallback_reasons=dict(reasons),
            fallback_expected_labels=dict(Counter(r['expected'] for r in fallback)),
            fallback_missing_erd=sum(r['erd_table_count'] == 0 for r in fallback), rows=details)
        lines.append(f"| {name} | {metric['macro_f1']:.4f} | {counts['unchanged_correct']} | {counts['unchanged_wrong']} | {counts['policy_validation_fallback']} | {counts['schema_failure']} | {counts['manual_origin_unknown']} |")
        sections += ['', f'## {name}: 검증 실패 분해', '', '| 사유 | 건수 |', '|---|---:|']
        sections += [f'| {k} | {v} |' for k, v in reasons.items()]
        sections += ['', '검증 보류의 사람 정답: `' + json.dumps(report['runs'][name]['fallback_expected_labels'], ensure_ascii=False) + '`.',
            f"검증 보류 중 ERD가 비어 있는 건수: {report['runs'][name]['fallback_missing_erd']}/{len(fallback)}.", '',
            '아래 목록은 검증에서 보류로 바뀐 것으로 식별된 사례다. 원래 세부 label을 알 수 없어 정답이 오답으로 바뀐 건수라고 해석하면 안 된다.', '',
            '| id | service | 사람 정답 | 검증 사유 |', '|---|---|---|---|']
        sections += [f"| {r['id']} | {r['service']} | {r['expected']} | {r['evidence']} |" for r in fallback]
    lines += ['', 'a = gpt-4o-mini, RAG/controller on; b = qwen2.5:7b, on; c = qwen2.5:7b, off.', '',
        '## 해석과 한계', '',
        '- 정책 검증은 구체 라벨을 manual로 바꾸지만, 해당 구체 라벨이 원래 정답이었는지는 기록되지 않았다. 위 건수를 점수 하락 건수로 계산하지 않는다.',
        '- 원인 구분 불가 보류에는 모델 자체 보류, confidence < 0.7에 의한 변환, 미등록 label 변환이 섞일 수 있다. 저장된 confidence가 낮다는 것만으로 변환 전 label을 알아낼 수 없다.',
        '- 구체 라벨 오답은 런타임 label 변환 탓이 아니다. 모델·프롬프트·입력 문맥을 포함한 검증 이전 단계의 오류이며 모델 자체 능력만의 오류로 단정하지 않는다.',
        '- b와 c는 RAG와 controller 두 설정이 동시에 다르므로 점수 차이를 RAG 단독 효과로 해석할 수 없다.',
        '- 정확한 전후 점수는 평가 스크립트에서 llm.complete 반환 원문을 파싱 전에 별도로 기록하는 재측정이 필요하다. 이 감사에서는 재호출하거나 런타임을 수정하지 않았다.',
        '- 근거 코드: scripts/eval_classifier.py의 record 저장, pipeline/classifier/schema.py의 unknown_label/low_confidence/parse_result, pipeline/classifier/__init__.py의 classify 검증 분기.',
        '- JSON 보고서에는 759건 전부의 단계 분류와 입력 파일 해시를 보존한다.'] + sections
    assert before == {str(p.relative_to(ROOT)): digest(p) for p in protected}
    (OUT / 'runtime_validation_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'runtime_validation_audit.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({k: {x: v for x, v in r.items() if x != 'rows'} for k, r in report['runs'].items()}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
