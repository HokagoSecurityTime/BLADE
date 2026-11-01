"""Compare two complete, paired recorded evaluations without additional inference."""
import json
from collections import Counter
from pathlib import Path
from scripts.eval_classifier import diagnostic_metrics, read_jsonl, metrics, LABELS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/eval'


def main():
    def load(folder):
        paths = list((OUT/folder).glob('*_metrics.json'))
        assert len(paths) == 1
        report = json.loads(paths[0].read_text(encoding='utf-8'))
        assert report['state'] == 'complete' and report['metrics']['completed'] == 253
        checkpoint = paths[0].with_name(paths[0].name.replace('_metrics.json', '.partial.jsonl'))
        return report, read_jsonl(checkpoint)
    before, a = load('recorded')
    after, b = load('enriched_recorded')
    for key in ['test_sha256','provider','model','prompt_sha256','rag','controller','corpus_sha256','runner_sha256']:
        assert before[key] == after[key], key
    by_id = {r['id']:r for r in b}
    assert {r['id'] for r in a} == set(by_id)
    frozen = {r['id']:r for r in read_jsonl(ROOT/'datasets/blade/processed/test.jsonl')}
    paired = []
    for r in a:
        s = by_id[r['id']]
        assert r['expected'] == s['expected']
        paired.append(dict(id=r['id'], service=r['service'], expected=r['expected'],
            raw_before=r['trace']['raw_label'], raw_after=s['trace']['raw_label'],
            final_before=r['prediction'], final_after=s['prediction'],
            events_before=r['trace']['validation_events'], events_after=s['trace']['validation_events'],
            same_prompt=r['prompt_sha256'] == s['prompt_sha256']))
    summary = dict(before=diagnostic_metrics(a), after=diagnostic_metrics(b), rows=paired,
        same_prompt_count=sum(r['same_prompt'] for r in paired),
        same_prompt_final_changed=sum(r['same_prompt'] and r['final_before'] != r['final_after'] for r in paired),
        provenance=dict(before=before, after=after))
    for key, rows in [('before',a),('after',b)]:
        summary[key]['parsed'] = metrics([{**r, 'prediction':r['trace']['parsed_label'] if r['trace']['parsed_label'] in LABELS else '__invalid__'} for r in rows])
        summary[key]['lost_correct_reasons'] = dict(Counter('; '.join(r['trace']['validation_events']) for r in rows
            if r['trace']['raw_label'] == r['expected'] and r['prediction'] != r['expected']))
        summary[key]['manual_origins'] = dict(Counter('model_manual' if r['trace']['raw_label'] == 'manual_review_required' else 'converted'
            for r in rows if r['prediction'] == 'manual_review_required'))
    lines = ['# GPT-4o-mini 입력 보강 전후 평가', '',
        '고정 test 253건, v2.0, RAG on, controller on. 두 실행 모두 모델 원문을 저장했다.', '',
        '| 입력 | 최초 macro-F1 | 검증 후 macro-F1 | 최초 보류율 | 최종 보류율 | 검증으로 정답→오답 | 오답→정답 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for name,key in [('기존 입력','before'),('소스 보강 입력','after')]:
        d = summary[key]
        lines.append(f"| {name} | {d['raw']['macro_f1']:.4f} | {d['final']['macro_f1']:.4f} | {d['raw']['manual_ratio']:.2%} | {d['final']['manual_ratio']:.2%} | {d['correct_to_wrong']} | {d['wrong_to_correct']} |")
    lines += ['', '## 입력 전달 범위', '', '| 입력 | ERD | controller 상태 |', '|---|---|---|']
    for name, report in [('기존',before),('보강',after)]:
        lines.append('| '+name+' | '+json.dumps(report['metrics']['erd_context'])+' | '+json.dumps(report['metrics']['controller_status'])+' |')
    lines += ['', '## 검증 사유', '', '| 입력 | 사유별 건수 (한 레코드에 여러 사유 가능) |', '|---|---|']
    for key in ['before','after']:
        lines.append('| '+key+' | '+json.dumps(summary[key]['validation_events'])+' |')
    lines += ['', '## 실제 정답 손실 원인', '', '| 입력 | 원문→스키마 처리 후→정책 검증 후 macro-F1 | 정답→오답 사유별 건수 | 최종 보류의 출처 |', '|---|---|---|---|']
    for key in ['before','after']:
        d = summary[key]
        lines.append(f"| {key} | {d['raw']['macro_f1']:.4f} → {d['parsed']['macro_f1']:.4f} → {d['final']['macro_f1']:.4f} | {json.dumps(d['lost_correct_reasons'])} | {json.dumps(d['manual_origins'])} |")
    lines += ['', '## 해석 제한', '',
        '- 보강은 ERD와 소스 연결을 함께 바꿨다. ERD가 RAG 검색 질의에도 들어가므로 개선량을 ERD 단독 효과로 해석하지 않는다.',
        '- 각 조건 한 번의 호출이다. 모델의 출력 변동이 포함되며 통계적 유의성이나 일반화 성능을 보장하지 않는다.',
        f"- 동일 prompt 해시: {summary['same_prompt_count']}건. 이 중 최종 라벨 변경: {summary['same_prompt_final_changed']}건.",
        '- MongoDB 스키마는 논리적 필드 목록을 DDL 문법으로 전달했다. SQL 실행 가능성을 뜻하지 않는다.',
        '- 경로 파싱 성공은 핸들러 전체 및 호출된 서비스의 인가 검사를 이해했다는 뜻이 아니다. Java/Go/Flask 등 지원하지 않는 형태는 누락으로 유지했다.',
        '- 고정 test 및 런타임 코드는 수정하지 않았으며 학습이나 재라벨링을 수행하지 않았다.', '',
        '## 소스별 점수', '', '| 소스 | 입력 | 최초 macro-F1 | 최종 macro-F1 |', '|---|---|---:|---:|']
    for source in ['vuln','synthetic']:
        for name, rows in [('기존',a),('보강',b)]:
            d = diagnostic_metrics([r for r in rows if frozen[r['id']]['source'] == source])
            lines.append(f"| {source} | {name} | {d['raw']['macro_f1']:.4f} | {d['final']['macro_f1']:.4f} |")
    (OUT/'context_comparison.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'context_comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'.join(lines[:9]))


if __name__ == '__main__':
    main()
