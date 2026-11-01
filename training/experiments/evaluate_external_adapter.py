"""Route scan and isolated HTTP guard replay; no upstream application startup."""
import ast
import copy
import hashlib
import html
import json
from types import SimpleNamespace
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from starlette import status
from markdown_it import MarkdownIt
from training.experiments.external_condition_probe import ROOT, RAW, pure_predicate
from training.experiments.fastapi_condition_adapter import Adapter, evaluate

OUT=ROOT/'reports/eval/classification_quality/external_adapter_v1'


def replay_function(adapter,guard):
    path=RAW/guard['guard_ref']['path']; fn=adapter.module(path)[1][guard['chain'][0]]
    pp=RAW/guard['predicate_ref']['path']; pred=adapter.module(pp)[1][guard['chain'][1]]
    pure,_=pure_predicate(pred)
    # Only the already validated if-not-predicate / raise HTTPException shape.
    # Details in this pinned source use string constants. Reject other kwargs.
    call=fn.body[0].body[0].exc
    assert all(k.arg in ('status_code','detail') for k in call.keywords)
    detail=next((k.value for k in call.keywords if k.arg=='detail'),None)
    if detail is not None:
        assert isinstance(detail,ast.Attribute) and isinstance(detail.value,ast.Name) and detail.value.id=='strings'
    clean=copy.deepcopy(fn); clean.decorator_list=[];clean.returns=None;clean.args.defaults=[]
    for arg in clean.args.args:arg.annotation=None
    globals_={'__builtins__':{},'HTTPException':HTTPException,'status':status,
              'strings':SimpleNamespace(USER_IS_NOT_AUTHOR_OF_ARTICLE='not author'),pred.name:pure}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[clean],type_ignores=[])),'<original-guard-body>','exec'),globals_)
    return globals_[fn.name],[a.arg for a in fn.args.args]


def main():
    manifest=json.loads((RAW/'manifest.json').read_text(encoding='utf8'))
    for f in manifest['files']:assert hashlib.sha256((RAW/f['path']).read_bytes()).hexdigest()==f['sha256']
    adapter=Adapter(RAW);rows=[]
    for path in sorted((RAW/'app/api/routes').rglob('*.py')):
        for fn in adapter.module(path)[1].values():
            for decorator in fn.decorator_list:
                if isinstance(decorator,ast.Call) and isinstance(decorator.func,ast.Attribute) and decorator.func.attr in ('get','post','put','delete','patch'):
                    r=adapter.route(path,fn)
                    r.update(method=decorator.func.attr.upper(),relative_route=ast.literal_eval(decorator.args[0]) if decorator.args else '',
                             path_scope='relative router path; include_router prefixes not reconstructed')
                    rows.append(r)
    checks=[];http_checks=[]
    for r in rows:
        for guard in r['guards']:
            original,names=replay_function(adapter,guard)
            for owner,user in [('alice','alice'),('alice','bob'),('bob','alice'),('bob','bob')]:
                obj=SimpleNamespace(author=SimpleNamespace(username=owner));actor=SimpleNamespace(username=user)
                bindings={names[0]:obj,names[1]:actor}
                extracted=evaluate(guard['condition'],bindings)
                try:original(**bindings);actual=200
                except HTTPException as exc:actual=exc.status_code
                checks.append(dict(handler=r['handler'],owner=owner,user=user,extracted_allow=extracted,
                    original_guard_status=actual,passed=(actual==200)==extracted,semantic_expected=owner==user))
            # Execute original guard as a dependency in an isolated ASGI harness.
            # Upstream handler/DB/JWT are not executed or replaced in the repository.
            app=FastAPI()
            def dependency(x_actor:str=Header(...),x_author:str=Header(...)):
                return original(**{names[0]:SimpleNamespace(author=SimpleNamespace(username=x_author)),names[1]:SimpleNamespace(username=x_actor)})
            def handler():return {'ok':True}
            app.add_api_route('/probe',handler,methods=[r['method']],dependencies=[Depends(dependency)])
            with TestClient(app) as client:
                for author,user in [('alice','alice'),('alice','bob'),('bob','alice'),('bob','bob')]:
                    response=client.request(r['method'],'/probe',headers={'x-actor':user,'x-author':author})
                    expected=200 if author==user else 403
                    http_checks.append(dict(handler=r['handler'],author=author,user=user,expected=expected,actual=response.status_code,passed=response.status_code==expected))
    OUT.mkdir(parents=True,exist_ok=True)
    result=dict(repository=manifest['repository'],commit=manifest['commit'],route_count=len(rows),
        routes_with_supported_guard=sum(bool(r['guards']) for r in rows),routes=rows,
        condition_checks=checks,http_harness_checks=http_checks,api_calls=0,
        upstream_integration_tests_executed=False,endpoint_final_labels_confirmed=0,
        adapter_sha256=hashlib.sha256((ROOT/'training/experiments/fastapi_condition_adapter.py').read_bytes()).hexdigest())
    (OUT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    n=result['routes_with_supported_guard']
    text=f'# 외부 FastAPI 추출 어댑터와 다음 단계 검증\n\n전체 라우트 {len(rows)}건을 스캔해 {n}건에서 연결된 인가 조건을 자동 추출했다. 기존 수동 지정 3건만 검색한 것이 아니며, 나머지는 지원하지 못하거나 구체 조건이 미확보된 상태다.\n\n'
    text+='| 단계 | 결과 |\n|---|---|\n'
    text+=f'| 모듈 import → Depends → 비교 함수 자동 연결 | {n} 라우트 |\n| 연결된 조건의 라벨 제안 | owner_match {n}건 |\n| 추출식 vs 원본 거부 함수 | {sum(c["passed"] for c in checks)}/{len(checks)} |\n| 원본 거부 함수를 의존성으로 실행한 격리 HTTP 검사 | {sum(c["passed"] for c in http_checks)}/{len(http_checks)} |\n| 전체 엔드포인트 정답 확정 | 0건 |\n\n'
    text+='## 구현\n\n비동기 라우트, 데코레이터 dependencies 및 인자 Depends, 절대 import의 함수 연결, `if not predicate: raise HTTPException(403)`, 속성 동등 비교를 지원한다. 실제 인자 바인딩을 반영하고 AND/OR/NOT 구조를 보존한다. 요청자 의존성과 author.username 비교를 확인한 경우에만 owner 조건 후보를 만든다. 전체 요청의 나머지 검사가 해결되지 않았으므로 후보를 최종 라벨로 승격하지 않는다.\n\n'
    text+='## 검증 해석\n\n이전에는 순수 비교 함수만 실행했다. 이번에는 원본 거부 함수 본문도 실행하고 FastAPI의 Depends 경로로 HTTP 200/403을 확인했다. 단, 원본 JWT·DB·원본 비즈니스 핸들러를 실행한 통합 테스트가 아니다. 인자에는 대역 객체를 제공하고 인증 헤더는 테스트용이다. article 검사 두 라우트가 같은 함수를 공유하므로 12건이 독립 정책 12개인 것은 아니다.\n\n'
    text+='## 남은 제한\n\n인증 factory, DB 객체 조회, 전역 middleware, include_router prefix는 완전 분석하지 않는다. 이 소스를 보고 어댑터를 확장했으므로 독립 외부 정확도로 주장하지 않는다. 역할·tenant·구독 조건의 외부 검증은 여전히 별도 필요하다. 미지원 라우트를 public으로 바꾸지 않는다. 원본 소스·기존 보고서·런타임·고정 test를 유지한다.\n\n'
    text+='## 전체 라우트 상태\n\n| 메서드 | 상대 경로 | 핸들러 | 추출 조건 수 |\n|---|---|---|---:|\n'
    for r in rows:text+=f'| {r["method"]} | {r["relative_route"]} | {r["handler"]} | {len(r["guards"])} |\n'
    text+=f'\n출처: https://github.com/{manifest["repository"]}/tree/{manifest["commit"]}\n'
    (OUT/'report.md').write_text(text,encoding='utf8')
    body=MarkdownIt('commonmark').enable('table').render(text)
    for r in rows:body+='<details><summary>'+html.escape(r['handler'])+'</summary><pre>'+html.escape(json.dumps(r,ensure_ascii=False,indent=2))+'</pre></details>'
    (OUT/'report.htm').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>외부 추출 어댑터 검증</title><style>body{max-width:1200px;margin:40px auto;padding:20px;font:16px/1.7 system-ui}table{border-collapse:collapse}td,th{padding:8px;border:1px solid #ccd}pre{white-space:pre-wrap;overflow-wrap:anywhere}details{margin:12px 0}</style>'+body+'</html>',encoding='utf8')
    assert all(c['passed'] for c in checks+http_checks)
    assert hashlib.sha256((ROOT/'datasets/blade/processed/test.jsonl').read_bytes()).hexdigest()=='bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa'
    print('routes',len(rows),'supported guards',n,'condition checks',len(checks),'HTTP checks',len(http_checks))


if __name__=='__main__':main()
