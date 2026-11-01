"""Frozen independent-project test; no adapter modifications during evaluation."""
from __future__ import annotations
import ast
import asyncio
import copy
import json
import os
import random
import time
from pathlib import Path
from training.experiments import adapter_v3
from training.experiments.external_paired_v29 import ROOT, save, digest

OUT=ROOT/'reports/eval/classification_quality/adapter_v3_holdout'
RAW=ROOT/'datasets/blade/raw/adapter_v3_holdout'
FROZEN=ROOT/'reports/eval/classification_quality/adapter_v3_development/frozen.json'
PROMPT=ROOT/'training/data/prompts/policy_label_v2.9.md'


def frozen() -> None:
    d=json.loads(FROZEN.read_text(encoding='utf8'))
    for f,h in d['files'].items():assert digest(ROOT/f)==h,f


def source(file: str,node: ast.AST) -> dict:
    lines=(RAW/file).read_text(encoding='utf8').splitlines()
    start=min([node.lineno]+[d.lineno for d in getattr(node,'decorator_list',[])])
    return dict(file=file,start=start,end=node.end_lineno,code='\n'.join(lines[start-1:node.end_lineno]),sha256=digest(RAW/file))


def prepare() -> None:
    frozen()
    hashes={p.relative_to(RAW).as_posix():digest(p) for p in RAW.rglob('*') if p.is_file()}
    save(OUT/'sources.json',dict(**json.loads((RAW/'commit.json').read_text()),hashes=hashes),frozen=True)
    route_file='fastapi_users/router/users.py'
    tree=ast.parse((RAW/route_file).read_text(encoding='utf8'))
    factory=next(n for n in tree.body if isinstance(n,ast.FunctionDef))
    authfile='fastapi_users/authentication/authenticator.py'
    authclass=next(n for n in ast.parse((RAW/authfile).read_text(encoding='utf8')).body if isinstance(n,ast.ClassDef) and n.name=='Authenticator')
    authrefs=[source(authfile,n) for n in authclass.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in ['current_user','_authenticate','_get_dependency_signature']]
    mgrfile='fastapi_users/manager.py'
    mgrclass=next(n for n in ast.parse((RAW/mgrfile).read_text(encoding='utf8')).body if isinstance(n,ast.ClassDef) and n.name=='BaseUserManager')
    methods={n.name:n for n in mgrclass.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    helpers={n.name:n for n in factory.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and not n.decorator_list}
    rows=[];refs=[];operations={}
    for fn in factory.body:
        if not isinstance(fn,ast.AsyncFunctionDef) or not fn.decorator_list:continue
        dec=fn.decorator_list[0]
        method=dec.func.attr.upper();path=ast.literal_eval(dec.args[0])
        response_desc=[n.value for k in dec.keywords if k.arg=='responses' for n in ast.walk(k.value) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
        operation=dict(operationId=fn.name,summary=fn.name.replace('_',' ').title(),description=ast.get_docstring(fn) or '',response_text=response_desc,
                       security=[{'configured_authentication_backend':[]}])
        # Router-relative OAS projection: mounting prefix and backend scheme are configurable.
        payload=dict(method=method,path=path,path_params=['id'] if '{id}' in path else [],query_params=[],summary=operation['summary'],
                     description=operation['description']+'\nDeclared response descriptions: '+json.dumps(response_desc),security=operation['security'],security_state='declared',schema_fields=['id','email','is_active','is_superuser','is_verified'],owner_cols=[],tenant_cols=[])
        evidence=[source(route_file,fn)]+authrefs
        assignments=[n for n in factory.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['get_current_active_user','get_current_superuser'] for t in n.targets)]
        evidence += [source(route_file,n) for n in assignments]
        names=set()
        if fn.name in ['get_user','update_user','delete_user']:
            evidence.append(source(route_file,helpers['get_user_or_404']));names.update(['get','parse_id'])
        if fn.name in ['update_me','update_user']:names.add('update')
        if fn.name=='delete_user':names.add('delete')
        pending=list(names);visited=set()
        while pending:
            name=pending.pop()
            if name in visited or name not in methods:continue
            visited.add(name);node=methods[name];evidence.append(source(mgrfile,node))
            for call in ast.walk(node):
                if isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute) and isinstance(call.func.value,ast.Name) and call.func.value.id=='self':pending.append(call.func.attr)
        # Base database protocol only, actual deployment adapter remains unknown.
        dbfile='fastapi_users/db/base.py'
        dbtree=ast.parse((RAW/dbfile).read_text(encoding='utf8'))
        for n in ast.walk(dbtree):
            if isinstance(n,ast.AsyncFunctionDef) and n.name in ['get','update','delete'] and n.name in visited:evidence.append(source(dbfile,n))
        enhanced=copy.deepcopy(payload)
        enhanced['description']+='\nSource scope: default router with requires_verification=False; base manager methods, no custom callback overrides. Backend and database implementation are deployment-specific and not included.\n'
        enhanced['description']+='\n'.join(f"FILE {e['file']}:{e['start']}-{e['end']}\n{e['code']}" for e in evidence)
        label='owner_match' if fn.name in ['me','update_me'] else 'role_required'
        refs.append(dict(id=fn.name,reference_label=label,source_refs=evidence,intended_policy='default users router documentation and declared dependency factory',
                         implemented='authenticated self target' if label=='owner_match' else 'superuser=True prerequisite; arbitrary target via manager.get',
                         reference_status='agent source review, not human gold',gaps=['configured DB/backend missing','custom manager callbacks may change policy','default requires_verification=False only']))
        rows.append(dict(id=fn.name,service='fastapi-users/fastapi-users',method=method,path=path,inputs=dict(oas=payload,oas_code=enhanced)))
        operations.setdefault(path,{})[method.lower()]=operation
    assert len(rows)==5
    save(OUT/'inputs.json',rows,frozen=True);save(OUT/'references.json',refs,frozen=True)
    save(OUT/'oas_projection.json',dict(paths=operations,provenance='static router-relative projection, configurable backend scheme placeholder; not live OAS export'),frozen=True)
    extracted={r['id']:adapter_v3.analyze(RAW,route_file,r['id'],hashes) for r in rows}
    save(OUT/'extracted.json',extracted,frozen=True)
    save(OUT/'prepared.json',dict(input_sha256=digest(OUT/'inputs.json'),references_sha256=digest(OUT/'references.json'),frozen_sha256=digest(FROZEN)),frozen=True)
    print('Prepared 5 paired cases, adapter frozen',flush=True)


async def harness() -> None:
    from types import SimpleNamespace as NS
    from fastapi import HTTPException, status
    file='fastapi_users/authentication/authenticator.py'
    tree=ast.parse((RAW/file).read_text(encoding='utf8'))
    fn=copy.deepcopy(next(n for n in ast.walk(tree) if isinstance(n,ast.AsyncFunctionDef) and n.name=='_authenticate'))
    for a in fn.args.args+fn.args.kwonlyargs: a.annotation=None
    if fn.args.vararg:fn.args.vararg.annotation=None
    if fn.args.kwarg:fn.args.kwarg.annotation=None
    fn.returns=None
    # Future annotations prevents evaluation of local type declarations; original body unchanged.
    ns=dict(HTTPException=HTTPException,status=status,name_to_variable_name=lambda n:n,name_to_strategy_variable_name=lambda n:'strategy_'+n)
    code=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),fn],type_ignores=[])
    exec(compile(ast.fix_missing_locations(code),file,'exec'),ns)
    tests=[]
    for required in [False,True]:
        for admin in [False,True]:
            for active in [False,True]:
                actor=NS(is_active=active,is_superuser=admin,is_verified=False)
                class Strategy:
                    async def read_token(self,token,user_manager):return actor
                backend=NS(name='stub');self=NS(backends=[backend])
                try:
                    result=await ns['_authenticate'](self,user_manager=object(),active=True,verified=False,superuser=required,stub='token',strategy_stub=Strategy())
                    actual=200;assert result[0] is actor
                except HTTPException as exc:actual=exc.status_code
                expected=401 if not active else 403 if required and not admin else 200
                assert actual==expected
                tests.append(dict(require_superuser=required,actor_superuser=admin,active=active,status=actual))
    save(OUT/'handler_checks.json',dict(checks=tests,passed=len(tests),scope='original _authenticate body, strategy/identity doubles; no deployed integration'),frozen=True)


async def run() -> None:
    import httpx
    from contextvars import ContextVar
    from training.data.label import read_env
    from training.data.label_v6 import engine
    frozen();await harness()
    prep=json.loads((OUT/'prepared.json').read_text())
    assert prep['input_sha256']==digest(OUT/'inputs.json')
    assert prep['references_sha256']==digest(OUT/'references.json')
    read_env(ROOT/'.env');model=os.getenv('BLADE_LABEL_MODEL','gpt-4o-mini')
    assert model=='gpt-4o-mini' and os.getenv('BLADE_LABEL_PROVIDER','openai')=='openai'
    settings=engine.llm.Settings('openai',model,os.environ['OPENAI_API_KEY'])
    engine.VERSION='policy-label-v2.9'
    rows=json.loads((OUT/'inputs.json').read_text(encoding='utf8'))
    payloads={c+':'+r['id']:r['inputs'][c] for r in rows for c in ['oas','oas_code']}
    engine.payload=lambda r:payloads[r['id']]
    save(OUT/'execution.json',dict(**prep,model=model,temperature=0,experiment_sha256=digest(Path(__file__))),frozen=True)
    done={r['id'] for r in engine.read(OUT/'predictions.jsonl')};keyvar=ContextVar('request_case',default=None)
    async def capture(response):
        await response.aread()
        if response.status_code==200:engine.append(OUT/'raw_responses.jsonl',dict(id=keyvar.get(),response=response.json()))
    jobs=[(c,r) for r in rows for c in ['oas','oas_code'] if c+':'+r['id'] not in done];random.Random(42).shuffle(jobs)
    async with httpx.AsyncClient(timeout=180,event_hooks={'response':[capture]}) as client:
        for c,r in jobs:
            key=c+':'+r['id'];keyvar.set(key);start=time.perf_counter()
            result=await engine.request(dict(id=key,service=r['service'],method=r['method'],path=r['path'],meta={}),PROMPT.read_text(encoding='utf8'),settings,client,OUT/'usage.jsonl')
            result.update(condition=c,case_id=r['id'],elapsed_ms=(time.perf_counter()-start)*1000)
            engine.append(OUT/'predictions.jsonl',result);print(key,flush=True)
    frozen()


def report() -> None:
    from markdown_it import MarkdownIt
    from collections import Counter
    frozen()
    refs={r['id']:r for r in json.loads((OUT/'references.json').read_text(encoding='utf8'))}
    preds=[json.loads(s) for s in (OUT/'predictions.jsonl').read_text(encoding='utf8').splitlines()]
    extraction=json.loads((OUT/'extracted.json').read_text(encoding='utf8'))
    decisions=[dict(id=p['id'],original_prediction=p,guard=adapter_v3.verify(p,extraction[p['case_id']])) for p in preds]
    labels=['public','role_required','membership_required','tenant_match','owner_match','owner_or_admin','manual_review_required']
    metrics={}
    for c in ['oas','oas_code']:
        selected=[p for p in preds if p['condition']==c];assert len(selected)==5
        matrix={l:{k:0 for k in labels+['output_error']} for l in labels}
        for p in selected:matrix[refs[p['case_id']]['reference_label']][p['label'] if p['label'] in labels else 'output_error']+=1
        per={}
        for label in labels:
            tp=matrix[label][label];support=sum(matrix[label].values());chosen=sum(matrix[l][label] for l in labels)
            precision=tp/chosen if chosen else 0;recall=tp/support if support else 0
            per[label]=dict(support=support,precision=precision,recall=recall,f1=2*precision*recall/(precision+recall) if precision+recall else 0)
        correct=sum(p['label']==refs[p['case_id']]['reference_label'] for p in selected)
        # In this router all scored cases require an active caller; public is a definite unsafe broadening.
        unsafe=sum(p['label']=='public' for p in selected)
        metrics[c]=dict(n=5,correct=correct,accuracy=correct/5,macro_f1_7=sum(v['f1'] for v in per.values())/7,
                        macro_f1_supported=sum(v['f1'] for v in per.values() if v['support'])/2,per_label=per,confusion_matrix=matrix,
                        manual_rate=sum(p['label']=='manual_review_required' for p in selected)/5,mean_ms=sum(p['elapsed_ms'] for p in selected)/5,
                        complete_guard_coverage=0,partial_guard_coverage=sum(bool(e['necessary_conditions']) for e in extraction.values())/5,
                        guard_unassessable_rate=1.0,supported_domain_false_block_rate=None,correct_proposal_held=correct,
                        operational_correct_hold_rate=1.0 if correct else None,confirmed_unsafe=unsafe,specific_unsafe_detection_rate=0 if unsafe else None,
                        reference_uncertainty='default library configuration only, no human gold; other deployed configurations unresolved')
    save(OUT/'metrics.json',metrics);save(OUT/'decisions.json',decisions)
    text='# 프롬프트 v2.9 / 어댑터 v3 — 독립 프로젝트 결과\n\n'
    text+='새 프로젝트 fastapi-users/fastapi-users의 users 라우터 전체 5건을 같은 ID로 비교했다. 어댑터는 소스를 보기 전에 고정했고 평가 중 수정하지 않았다. 이 프로젝트는 커스터마이즈 가능한 라이브러리이며 배포된 서비스가 아니다. 표본은 5건·2종이라 전체 6종 성능은 말할 수 없다.\n\n'
    commit=json.loads((RAW/'commit.json').read_text())['commit']
    text+=f'[원본 커밋](https://github.com/fastapi-users/fastapi-users/tree/{commit})\n\n'
    text+='## LLM 분류\n\n참조는 API 실행 전에 기록한 에이전트 소스 검토 결과다. 사람 정답 정확도가 아니다. 기본 requires_verification=False·기본 manager 동작을 범위로 한다. 실제 배포의 backend·DB·callback override는 미확보다. OAS는 라우터 상대 경로·응답 설명의 정적 투영본이며 라이브 export가 아니다.\n\n| 입력 | 참조 일치 | macro-F1(2종) | macro-F1(7종) | 보류율 | 평균 ms |\n|---|---:|---:|---:|---:|---:|\n'
    for c,m in metrics.items():text+=f"| {c} | {m['correct']}/5 | {m['macro_f1_supported']:.4f} | {m['macro_f1_7']:.4f} | {m['manual_rate']:.0%} | {m['mean_ms']:.0f} |\n"
    text+='\n## 어댑터\n\n완전 분석 0/5, 필수 조건 부분 분석 0/5. 평가 불가 100%다. 동적 factory가 생성한 의존성은 지원 문법 밖이므로 모두 보류했다. 올바른 제안도 전부 보류되는 운영 손실이 있다. 지원 영역의 오차단율은 분모 0으로 N/A다. public이 나온 사례만 확실한 인증 조건 누락으로 계산하며, 이를 특정 조건 누락으로 탐지한 건수는 0이다. 전부 보류를 탐지 성공으로 세지 않는다. 그 외 라벨의 위험 여부는 바인딩 미확보로 미확정이다.\n\n'
    for c,m in metrics.items():text+=f"- {c}: 올바른 제안 보류 {m['correct_proposal_held']}건, 확실한 public 허용 확대 {m['confirmed_unsafe']}건, 구체 탐지율 {m['specific_unsafe_detection_rate'] if m['specific_unsafe_detection_rate'] is not None else 'N/A'}.\n"
    text+='\n## 근거 및 검증\n\n원본 _authenticate 본문에 사용자·전략 대역을 넣은 허용/거부 8건 통과. 실제 JWT/DB/HTTP 통합 테스트가 아니다. 호출 코드 위치는 references.json에 보존했다. 라벨별 P/R/F1·혼동행렬은 metrics.json, 원래 라벨과 별도 검증 결과는 decisions.json에 있다.\n\n## 개발/독립 결과 분리\n\n개발 프로젝트는 완전 분석 8/23, 추가 필수 조건 5/23으로 확대했다. 독립 프로젝트에서는 동적 의존성 factory 때문에 0/5다. 개발 성과를 일반화할 수 없다. 다음 개발은 factory 인자→내부 인증 조건 전달 추적이며, 이번 holdout을 개발에 쓰면 다음 평가는 또 다른 프로젝트가 필요하다. 자동 적용·학습·기존 test 수정은 하지 않았다.\n'
    (OUT/'report.md').write_text(text,encoding='utf8')
    (OUT/'report.htm').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>독립 평가</title><style>body{max-width:1100px;margin:40px auto;font:16px/1.7 system-ui}td,th{padding:8px;border:1px solid #bbb}table{border-collapse:collapse}</style>'+MarkdownIt().enable('table').render(text)+'</html>',encoding='utf8')
    print({c:{k:m[k] for k in ['correct','macro_f1_supported','confirmed_unsafe']} for c,m in metrics.items()})


def main(action: str) -> None:
    if action=='prepare':prepare()
    elif action=='run':asyncio.run(run())
    elif action=='report':report()
    else:raise ValueError(action)

if __name__=='__main__':
    import sys
    main(sys.argv[1])
