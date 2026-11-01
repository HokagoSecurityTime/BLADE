"""Pinned external-project transfer audit. No server/database execution."""
import ast
import copy
import hashlib
import html
import json
from pathlib import Path
from types import SimpleNamespace
from markdown_it import MarkdownIt
from training.experiments.policy_conditions import extract

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'datasets/blade/raw/external_conditions_v1'
OUT=ROOT/'reports/eval/classification_quality/external_conditions_v1'


def function(path,name):
    tree=ast.parse(path.read_text(encoding='utf8'))
    return next(n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)


def evidence(path,node):
    start=min([node.lineno]+[d.lineno for d in getattr(node,'decorator_list',[])])
    lines=path.read_text(encoding='utf8').splitlines()
    return dict(path=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        start=start,end=node.end_lineno,code='\n'.join(f'{i}: {lines[i-1]}' for i in range(start,node.end_lineno+1)))


def pure_predicate(node):
    # Execute only a verified single return of an attribute equality. No imports,
    # defaults, decorators, arbitrary calls, network or repository entrypoint.
    assert len(node.body)==1 and isinstance(node.body[0],ast.Return)
    expr=node.body[0].value
    assert isinstance(expr,ast.Compare) and len(expr.ops)==1 and isinstance(expr.ops[0],ast.Eq)
    for operand in [expr.left,*expr.comparators]:
        while isinstance(operand,ast.Attribute):operand=operand.value
        assert isinstance(operand,ast.Name)
    clean=copy.deepcopy(node);clean.decorator_list=[];clean.returns=None
    clean.args.defaults=[];clean.args.kw_defaults=[]
    for a in clean.args.args:a.annotation=None
    module=ast.fix_missing_locations(ast.Module(body=[clean],type_ignores=[]))
    namespace={'__builtins__':{}}
    exec(compile(module,'<verified-original-predicate>','exec'),namespace)
    return namespace[clean.name],ast.unparse(expr)


def main():
    manifest=json.loads((RAW/'manifest.json').read_text(encoding='utf8'))
    for f in manifest['files']:
        assert hashlib.sha256((RAW/f['path']).read_bytes()).hexdigest()==f['sha256']
    definitions=[
        ('PUT','/{slug}','app/api/routes/articles/articles_resource.py','update_article_by_slug','articles','check_article_modification_permissions','check_user_can_modify_article'),
        ('DELETE','/{slug}','app/api/routes/articles/articles_resource.py','delete_article_by_slug','articles','check_article_modification_permissions','check_user_can_modify_article'),
        ('DELETE','/{comment_id}','app/api/routes/comments.py','delete_comment_from_article','comments','check_comment_modification_permissions','check_user_can_modify_comment')]
    rows=[];checks=[]
    for method,path,file,handler,domain,guard,predicate in definitions:
        routepath=RAW/file;guardpath=RAW/f'app/api/dependencies/{domain}.py';predpath=RAW/f'app/services/{domain}.py'
        route=function(routepath,handler);check=function(guardpath,guard);pred=function(predpath,predicate)
        assert any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Depends' and any(isinstance(a,ast.Name) and a.id==guard for a in n.args) for d in route.decorator_list for n in ast.walk(d))
        assert len(check.body)==1 and isinstance(check.body[0],ast.If)
        condition=check.body[0]
        assert isinstance(condition.test,ast.UnaryOp) and isinstance(condition.test.op,ast.Not)
        assert isinstance(condition.test.operand,ast.Call) and condition.test.operand.func.id==predicate
        assert len(condition.body)==1 and isinstance(condition.body[0],ast.Raise)
        call=condition.body[0].exc
        assert any(k.arg=='status_code' and isinstance(k.value,ast.Attribute) and k.value.attr=='HTTP_403_FORBIDDEN' for k in call.keywords)
        fn,expression=pure_predicate(pred)
        for author,user,expected in [('alice','alice',True),('alice','bob',False),('bob','bob',True),('bob','alice',False)]:
            actual=fn(SimpleNamespace(author=SimpleNamespace(username=author)),SimpleNamespace(username=user))
            checks.append(dict(handler=handler,author=author,user=user,expected=expected,actual=actual,passed=actual==expected))
        excerpts=[evidence(routepath,route),evidence(guardpath,check),evidence(predpath,pred)]
        baseline=extract(excerpts,method,path)
        testpath=RAW/f'tests/test_api/test_routes/test_{domain}.py'
        tests=ast.parse(testpath.read_text(encoding='utf8'))
        relevant=[evidence(testpath,n) for n in tests.body if isinstance(n,ast.AsyncFunctionDef) and
            ('not_authored' in n.name or 'can_delete_his' in n.name or 'can_delete_comment' in n.name)]
        rows.append(dict(handler=handler,method=method,relative_route=path,
            route_dependency_edge=[handler,guard,predicate],original_extractor=baseline,
            implemented_allow_expression=expression,proposed_condition_label='owner_match',
            condition_proposal_basis='exact original predicate + connected 403 dependency; not inferred from resource name',
            endpoint_final_label=None,unresolved=['authentication factory','repository retrieval','global middleware','full integration execution'],
            excerpts=excerpts,upstream_tests=relevant,upstream_tests_executed=False))
    OUT.mkdir(parents=True,exist_ok=True)
    result=dict(repository=manifest['repository'],commit=manifest['commit'],cases=rows,
        predicate_checks=checks,api_calls=0,full_application_executed=False,
        supported_by_original_extractor=sum(not r['original_extractor']['issues'] for r in rows),
        classification_accuracy=None)
    (OUT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    text='# 새 외부 프로젝트 조건 추출 검증\n\n'
    text+='기존 합성 14/14를 외부 성능으로 일반화할 수 없다는 점을 확인했다. 고정 추출기는 새 프로젝트 3개 라우트를 모두 지원하지 못했다.\n\n'
    text+=f"출처: https://github.com/{manifest['repository']}/tree/{manifest['commit']}\n\n"
    text+='| 항목 | 결과 |\n|---|---|\n| 기존 추출기 지원 | 0/3 라우트 |\n| 라우트→권한 의존성→서비스 비교 연결 | 3/3 확인 |\n| 실제 원본 비교 함수 단위 검사 | 12/12 통과 |\n| 서로 다른 비교 함수 | 2개 (article·comment) |\n| 전체 서버·DB·상위 테스트 실행 | 미실행 |\n| 최종 엔드포인트 정답 | 미확정 |\n\n'
    text+='## 확인한 근거\n\nPUT article·DELETE article·DELETE comment는 데코레이터 Depends에서 권한 검사로 연결된다. 검사는 작성자 username과 요청자 username의 동일성을 검사하는 원본 함수가 false이면 403을 발생시킨다. 같은 커밋의 상위 테스트에도 타인 수정·삭제 거부가 명시돼 있다.\n\n'
    text+='원본 파일은 수정하지 않았다. 단위 실행은 import·annotation·기본값 실행을 제외하고, 호출이 없는 단일 속성 비교 return 본문만 검증 후 실행했다. 객체는 SimpleNamespace 대역이다. 따라서 JWT·DB·HTTP 요청 전체를 검증한 결과가 아니다. 12개 검사는 3개 라우트×4개 입력이며 article 비교 함수는 두 라우트에서 공유하므로 독립 12개 정책 사례가 아니다.\n\n'
    text+='## 지원하지 못한 원인과 다음 구현 범위\n\n기존 추출기는 동기 함수, 함수 인자 Depends, sub/owner 딕셔너리 비교만 제한적으로 처리했다. 새 소스는 async 라우트, 데코레이터 dependencies, 별도 모듈 함수, author.username 속성 비교를 사용한다. 우선 이 연결을 별도 어댑터로 다뤄야 하며, 이름만 owner_match로 치환하면 안 된다. 이번 탐색의 조건 후보와 기존 추출기 예측은 분리했다. 아직 범용 추출기 지원 확장이나 LLM 정확도 개선을 입증한 것은 아니다.\n'
    text+='\n이 외부 사례는 owner 계열에 한정된다. tenant·membership 등 나머지 유형의 외부 검증은 남아 있다. 런타임·기존 프롬프트·고정 test는 변경하지 않았다.\n'
    (OUT/'report.md').write_text(text,encoding='utf8')
    body=MarkdownIt('commonmark').enable('table').render(text)
    for row in rows:body+='<details><summary>'+html.escape(row['handler'])+'</summary><pre>'+html.escape(json.dumps(row,ensure_ascii=False,indent=2))+'</pre></details>'
    (OUT/'report.htm').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>외부 조건 검증</title><style>body{max-width:1100px;margin:40px auto;font:16px/1.7 system-ui}td,th{padding:10px;border:1px solid #ccc}pre{white-space:pre-wrap}details{margin:15px 0}</style>'+body+'</html>',encoding='utf8')
    assert all(c['passed'] for c in checks)
    print('3 route chains; 12/12 original predicate checks; baseline supported 0/3; no endpoint accuracy claimed')


if __name__=='__main__':main()
