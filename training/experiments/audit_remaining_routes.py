"""Authentication dependency traversal plus explicitly curated semantic triage.

Triage is a source review, not a general automatic seven-label classifier.
"""
import ast
from collections import Counter
import hashlib
import html
import json
from markdown_it import MarkdownIt
from training.experiments.fastapi_condition_adapter import Adapter, Unsupported
from training.experiments.external_condition_probe import ROOT, RAW

OUT=ROOT/'reports/eval/classification_quality/remaining_routes_v1'
AUTH='app.api.dependencies.authentication'
GROUPS={
    'public_read_candidate':['list_articles','retrieve_article_by_slug','list_comments_for_article','retrieve_profile_by_username','get_all_tags'],
    'authentication_entry':['login','register'],
    'creator_binding':['create_new_article','create_comment_for_article'],
    'self_account':['retrieve_current_user','update_current_user'],
    'caller_relation':['get_articles_for_user_feed','mark_article_as_favorite','remove_article_from_favorites','follow_for_user','unsubscribe_from_user'],
}
NOTES={
    'public_read_candidate':'공개 조회 후보. optional 인증 또는 인증 의존성 없음과 핸들러를 대조했다. 실제 배포 공개 접근은 미확정.',
    'authentication_entry':'기존 토큰 없이 로그인 자격 증명 검증 또는 가입을 수행한다. 인증 전 진입과 무조건 요청 성공은 다르다.',
    'creator_binding':'인증된 요청자를 새 레코드 작성자로 기록한다. 기존 객체 소유자 일치 검사와 구분한다.',
    'self_account':'인증된 사용자 객체를 응답·수정 대상으로 사용한다. 임의 대상 ID 비교와 다른 요청자 고정 방식이다.',
    'caller_relation':'요청자의 즐겨찾기·팔로우 관계 또는 피드를 조작한다. 대상 글이나 다른 프로필의 소유자여야 한다는 뜻이 아니다.',
}


def auth_dependencies(adapter,path,fn,seen=None):
    seen=set() if seen is None else seen
    key=(str(path),fn.name)
    if key in seen:return []
    seen.add(key);out=[]
    imports=adapter.module(path)[2]
    for dep in adapter.dependency_nodes(fn):
        if not dep.args:continue
        arg=dep.args[0]
        if isinstance(arg,ast.Call) and isinstance(arg.func,ast.Name) and imports.get(arg.func.id)==(AUTH,'get_current_user_authorizer'):
            required=next((k.value for k in arg.keywords if k.arg=='required'),ast.Constant(True))
            if arg.args or any(k.arg!='required' for k in arg.keywords) or not isinstance(required,ast.Constant) or type(required.value)!=bool:
                out.append(dict(state='unknown_factory_argument',path=str(path),via=fn.name));continue
            factory_path=RAW/'app/api/dependencies/authentication.py'
            factory=adapter.module(factory_path)[1]['get_current_user_authorizer']
            # Validate the pinned factory instead of interpreting its name alone.
            assert len(factory.body)==1 and isinstance(factory.body[0],ast.Return)
            value=factory.body[0].value
            assert ast.unparse(value)=='_get_current_user if required else _get_current_user_optional'
            out.append(dict(state='required' if required.value else 'optional',via=fn.name,
                factory_ref=adapter.ref(factory_path,factory),dependency_expression=ast.unparse(dep)))
        elif isinstance(arg,ast.Name):
            try:
                p,n=adapter.resolve(path,arg.id)
                out.extend(auth_dependencies(adapter,p,n,seen))
            except (Unsupported,OSError):pass
    return out


def main():
    manifest=json.loads((RAW/'manifest.json').read_text(encoding='utf8'))
    for f in manifest['files']:assert hashlib.sha256((RAW/f['path']).read_bytes()).hexdigest()==f['sha256']
    adapter=Adapter(RAW)
    existing=json.loads((ROOT/'reports/eval/classification_quality/external_adapter_v1/results.json').read_text(encoding='utf8'))
    groups={h:g for g,handlers in GROUPS.items() for h in handlers};results=[]
    for r in existing['routes']:
        if r['guards']:continue
        name=r['handler'];group=groups[name]
        p=RAW/r['route_ref']['path'];fn=adapter.module(p)[1][name]
        auth=auth_dependencies(adapter,p,fn)
        states={x['state'] for x in auth}
        state='required' if 'required' in states else 'optional' if 'optional' in states else 'none_found'
        repo_refs=[]
        # Relevant repository method excerpts: resolve repository class imports and
        # only retain method names actually called in this handler.
        calls={n.func.attr for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
        for _,(module,symbol) in adapter.module(p)[2].items():
            if not module.startswith('app.db.repositories.'):continue
            repo=RAW.joinpath(*module.split('.')).with_suffix('.py')
            if not repo.exists():continue
            tree=ast.parse(repo.read_text(encoding='utf8'))
            for cls in tree.body:
                if isinstance(cls,ast.ClassDef) and cls.name==symbol:
                    repo_refs.extend(adapter.ref(repo,n) for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in calls)
        results.append(dict(handler=name,method=r['method'],relative_route=r['relative_route'],triage_group=group,
            triage_origin='Codex static source review; not LLM API or universal rule',reason=NOTES[group],
            authentication_state=state,authentication_evidence=auth,handler_ref=r['route_ref'],repository_refs=repo_refs,
            unresolved=['SQL execution and constraints','deployed middleware/configuration','end-to-end HTTP with real authentication'],
            final_label=None,training_eligible=False))
    assert len(results)==16
    counts=dict(Counter(r['triage_group'] for r in results))
    OUT.mkdir(parents=True,exist_ok=True)
    data=dict(repository=manifest['repository'],commit=manifest['commit'],counts=counts,routes=results,
        api_calls=0,final_labels_confirmed=0,full_application_executed=False)
    (OUT/'results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    text='# 남은 16개 라우트의 코드 기반 분류\n\n분석 미지원 16건을 모두 같은 문제로 다루지 않고 요청 의미와 인증 의존성을 분리했다. 이것은 최종 7종 라벨 확정이 아니라 후속 추출 범위 결정이다.\n\n'
    text+='| 유형 | 건수 | 해석 |\n|---|---:|---|\n'
    for group,n in counts.items():text+=f'| {group} | {n} | {NOTES[group]} |\n'
    text+='\n## 라우트별 상태\n\n| 메서드 | 상대 경로 | 핸들러 | 인증 | 유형 |\n|---|---|---|---|---|\n'
    for r in results:text+=f'| {r["method"]} | {r["relative_route"]} | {r["handler"]} | {r["authentication_state"]} | {r["triage_group"]} |\n'
    text+='\n## 핵심 발견\n\n- 인증만으로 역할 요구를 만들지 않는다. 생성자 기록은 기존 객체 소유권 검사와 다르다.\n- 본인 계정은 대상 객체를 인증 사용자로 고정하는 방식이다. 직접 비교문만 찾는 기존 추출기는 이를 놓친다.\n- 즐겨찾기·팔로우는 요청자의 관계 레코드가 보호 대상이다. 글·프로필 소유권으로 치환하면 의미가 바뀐다.\n- 공개 후보 5건 중 4건은 직접·간접 optional 인증 경로가 있고, tags는 인증 의존성이 발견되지 않았다. tags를 공개라고 확정하는 근거는 아직 부족하다.\n- login/register에는 기존 토큰 요구가 없지만 login은 비밀번호를 검사한다. public이 모든 입력을 성공시킨다는 뜻은 아니다.\n\n'
    text+='## 다음 구현 우선순위\n\n1. self_account 2건의 요청자→수정 대상 바인딩을 추출하고 타인 ID 주입 차단을 격리 테스트한다.\n2. creator_binding 2건의 작성자 강제 귀속을 확인한다. 기존 객체 조건과 별도 저장한다.\n3. caller_relation 5건은 repository→SQL에서 요청자 키가 WHERE/INSERT에 어떻게 쓰이는지 추적한다. 대상 객체 소유권으로 자동 매핑하지 않는다.\n4. 공개 후보는 실제 익명 요청과 유효·무효 토큰을 구분해 통합 검증한다.\n\n'
    text+='현재 단계에서 전체 서버·JWT·DB를 실행하지 않았다. 위 요청 의미 분류는 소스 검토이며, 지원되지 않는 모든 호출이 해소됐다는 뜻이 아니다. 라벨·데이터셋·런타임은 변경하지 않았다.\n'
    text+=f'\n출처: https://github.com/{manifest["repository"]}/tree/{manifest["commit"]}\n'
    (OUT/'report.md').write_text(text,encoding='utf8')
    content=MarkdownIt('commonmark').enable('table').render(text)
    for r in results:content+='<details><summary>'+html.escape(r['handler'])+'</summary><pre>'+html.escape(json.dumps(r,ensure_ascii=False,indent=2))+'</pre></details>'
    (OUT/'report.htm').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>남은 라우트 분석</title><style>body{max-width:1200px;margin:40px auto;padding:20px;font:16px/1.7 system-ui}td,th{border:1px solid #ccd;padding:10px}table{border-collapse:collapse}pre{white-space:pre-wrap;overflow-wrap:anywhere}details{margin:12px 0}</style>'+content+'</html>',encoding='utf8')
    print(json.dumps(counts));print(Counter(r['authentication_state'] for r in results))


if __name__=='__main__':main()
