"""Evaluate a restricted static implementation, not a new LLM model."""
import json
import html
import re
from pathlib import Path
from markdown_it import MarkdownIt
from training.experiments.paired_policy import OUT as PREVIOUS, ROOT, score, engine, FROZEN
from training.experiments.policy_conditions import extract, map_label

OUT=PREVIOUS.parent/'condition_extraction_v1'


def main():
    rows=engine.read(PREVIOUS/'evidence.jsonl');results=[]
    # Prediction path only uses the exact previous input excerpts/OAS description.
    for row in rows:
        source=row['implemented_checks']['excerpts']
        extraction=extract(source,row['method'],row['path'])
        description=row['inputs']['oas_only']['description'].lower()
        positive=any(s in description for s in ['no authentication is required','auth not required'])
        label,reason=map_label(extraction,positive)
        results.append(dict(id=row['id'],label=label,reason=reason,extraction=extraction,elapsed_ms=0))
    OUT.mkdir(parents=True,exist_ok=True)
    engine.dump(OUT/'predictions.json',results)
    predictions={r['id']:r for r in results}
    metrics=score(rows,predictions)
    old=json.loads((PREVIOUS/'metrics.json').read_text(encoding='utf8'))['metrics']['oas_code']
    # Independent contract's expected decision sets, checked over all fixture actors.
    from training.experiments import paired_policy_fixture as fixture
    contract=json.loads((ROOT/'training/experiments/paired_policy_contract.json').read_text(encoding='utf8'))
    policies={h:p for p in contract['policies'] for h in p['handlers']}
    def evaluate(expr,actor):
        if expr is None:return True
        if expr['op']=='and':return all(evaluate(x,actor) for x in expr['args'])
        if expr['op']=='or':return any(evaluate(x,actor) for x in expr['args'])
        expected={'owner_equal':actor['sub']=='alice','tenant_equal':actor['tenant']=='north',
                  'role':actor['role']==expr['value'],'subscription':actor['plan']==expr['value']}[expr['kind']]
        return expected if expr['comparison']=='eq' else not expected
    checks=[]
    for r in results:
        if not r['id'].startswith('controlled-observatory:'):continue
        policy=policies[r['id'].split(':')[1]];ext=r['extraction']
        for name,actor in fixture.ACTORS.items():
            actual=None if ext['issues'] else evaluate(ext['conditions'],actor)
            checks.append(dict(id=r['id'],actor=name,expected=name in policy['allow'],actual=actual,passed=actual==(name in policy['allow'])))
    engine.dump(OUT/'condition_checks.json',checks)
    engine.dump(OUT/'metrics.json',dict(mapping=metrics,condition_checks=len(checks),
        condition_checks_passed=sum(c['passed'] for c in checks),api_calls=0,
        input_sha256=engine.digest(PREVIOUS/'evidence.jsonl'),extractor_sha256=engine.digest(Path(__file__).with_name('policy_conditions.py'))))
    text='# 검사 조건 추출·라벨 매핑 실험\n\n기존 v2.8 프롬프트와 런타임을 바꾸지 않은 제한적 Python 정적 분석 실험이다. 추가 API 호출은 0회다.\n\n'
    text+='| 방법 | 합성 계약 일치 / 14 | macro-F1 |\n|---|---:|---:|\n'
    text+=f"| 기존 v2.8 LLM + 코드 | {old['correct']} | {old['macro_f1']:.4f} |\n| 조건 추출 + 규칙 매핑 | {metrics['correct']} | {metrics['macro_f1']:.4f} |\n"
    text+=f"\n추출한 조건식의 허용/거부 결과: {sum(c['passed'] for c in checks)}/{len(checks)} 계약 검사 일치. 기존 HTTP 98개 검사는 별도 기록에 보존했다. 조건식 검사와 라벨 매핑 점수를 구분한다.\n"
    text+='\n## 처리 방식\n\n- HTTPException(403) 거부 조건을 논리적으로 반전하여 허용식을 만든다. `not owner AND not admin`은 `owner OR admin`이다.\n- 순서대로 호출한 두 검사 함수는 AND로 결합한다. owner와 tenant, tenant와 subscription 조건을 하나로 버리지 않는다.\n- 반환 객체의 owner 필드만으로는 조건을 만들지 않는다. 인증(401)과 객체 부재(404)는 인가 조건과 분리한다.\n- 근거 경로·해시·줄번호·원래 거부식과 허용식을 predictions.json에 기록한다.\n- 지원하지 않는 제어 흐름·함수 호출·외부 프레임워크는 보류한다. 불확실한 의도를 구현에서 만들어내지 않는다.\n'
    text+='\n## 적용 범위와 한계\n\n이 추출기는 현재 개발 합성 코드의 Python/HTTPException 및 sub·owner·tenant·role·plan 필드 관례에 맞춘 제한적 구현이다. 일반 변수 별칭, 메서드 호출, DB query 필터, 동적 dispatch, 전역 middleware를 검증하는 범용 분석기가 아니다. 외부 Django 4건은 지원 범위 밖이며 미확정 상태를 유지한다. 기존 14건을 보고 개발했으므로 독립 정확도나 새 모델 성능으로 보고하지 않는다. OAS-only는 명시적 공개 근거 외에 구체 조건을 추측하지 않는 것이 원칙이다. 새 외부 프로젝트와 독립 표본의 검증이 여전히 필요하다.\n'
    text+='\n## 개별 결과\n\n| ID | 라벨 | 사유 | 추출 상태 |\n|---|---|---|---|\n'
    for r in results:text+=f"| {r['id']} | {r['label']} | {r['reason']} | {', '.join(r['extraction']['issues']) or '지원 범위 내'} |\n"
    (OUT/'report.md').write_text(text,encoding='utf8')
    content=MarkdownIt('commonmark',{'html':False}).enable('table').render(text)
    for r in results:content+='<details><summary>'+html.escape(r['id'])+'</summary><pre>'+html.escape(json.dumps(r,ensure_ascii=False,indent=2))+'</pre></details>'
    (OUT/'report.htm').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>조건 추출 실험</title><style>body{max-width:1200px;margin:40px auto;font:16px/1.7 system-ui;padding:20px}table{border-collapse:collapse;display:block;overflow:auto}td,th{border:1px solid #ccc;padding:10px}pre{white-space:pre-wrap}details{margin:12px 0}</style>'+content+'</html>',encoding='utf8')
    assert engine.digest(ROOT/'datasets/blade/processed/test.jsonl')==FROZEN
    print('mapping',metrics['correct'],'/14; conditions',sum(c['passed'] for c in checks),'/',len(checks))


if __name__=='__main__':main()
