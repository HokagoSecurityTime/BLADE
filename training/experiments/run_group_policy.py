"""LLM remains final semantic classifier; contract stays outside model inputs."""
import asyncio
import inspect
import json
import os
import html
from pathlib import Path
import httpx
from markdown_it import MarkdownIt
from training.data.label import read_env
from training.data.label_v6 import engine
from training.experiments import group_policy_fixture as fixture
from training.experiments.paired_policy import immutable, ROOT

OUT=ROOT/'reports/eval/classification_quality/group_policy_v29'
PROMPT=ROOT/'training/data/prompts/policy_label_v2.9.md'
CASES=[('group_access','/circles/{id}/files','membership_required',[1,0,1,0,0]),
 ('tenant_access','/archives/{id}','tenant_match',[1,1,0,0,0]),
 ('role_access','/dispatch/{id}','role_required',[0,0,0,1,0]),
 ('owner_access','/drafts/{id}','owner_match',[1,0,0,0,0]),
 ('owner_admin_access','/records/{id}','owner_or_admin',[1,0,0,0,1]),
 ('public_access','/catalog/{id}','public',[1,1,1,1,1]),
 ('group_tenant_access','/rooms/{id}/files','manual_review_required',[1,0,0,0,0]),
 ('subscription_access','/forecasts/{id}','manual_review_required',[0,1,0,0,0])]


def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    actors=[dict(id=n,tenant_id=t,role=r,subscription=s) for n,t,r,s in [
        ('alice','north','reader','basic'),('bob','north','reader','premium'),
        ('carol','south','reader','basic'),('dana','south','operator','basic'),('erin','south','admin','basic')]]
    resource=dict(group_id='circle-a',tenant_id='north',owner_id='alice')
    memberships={('alice','circle-a'),('carol','circle-a'),('bob','other-circle')}
    rows=[];checks=[]
    for name,path,label,expected in CASES:
        fn=getattr(fixture,name)
        for actor,wanted in zip(actors,expected):
            actual=fn(actor,resource,memberships)
            checks.append(dict(case=name,actor=actor['id'],expected=bool(wanted),actual=actual,passed=actual==bool(wanted)))
        source=inspect.getsource(fn);line=inspect.getsourcelines(fn)[1]
        # Omit actor fixtures, expected decisions, target labels and prediction history.
        value=dict(method='GET',path=path,path_params=['id'],query_params=[],summary='Retrieve resource',
            description='The handler calls the following access function and returns HTTP 403 when it returns False. Otherwise it returns the resource. actor is the authenticated caller, resource is the target object, memberships contains (user_id, group_id) relations. For public_access the actor may be anonymous.\n'
            +f'FILE training/experiments/group_policy_fixture.py:{line}\n'+source,
            security=None if name=='public_access' else [{'Bearer':[]}],
            security_state='unknown' if name=='public_access' else 'declared',schema_fields=[],owner_cols=[],tenant_cols=[])
        rows.append(dict(id=name,service='group-policy-control',method='GET',path=path,input=value,target=label))
    assert all(c['passed'] for c in checks)
    assert fixture.public_access(None,resource,memberships)
    immutable(OUT/'contract.json',dict(cases=[dict(id=r['id'],label=r['target']) for r in rows],checks=checks,
        anonymous_public_check=True,meaning='target-group membership, not subscription tier'))
    immutable(OUT/'inputs.jsonl',[dict(id=r['id'],input=r['input']) for r in rows],True)
    return rows


async def main():
    rows=prepare();read_env(ROOT/'.env')
    assert os.getenv('BLADE_LABEL_PROVIDER','openai')=='openai'
    model=os.getenv('BLADE_LABEL_MODEL','gpt-4o-mini')
    assert model in ['gpt-4o-mini','gpt-4o-mini-2024-07-18']
    settings=engine.llm.Settings('openai',model,os.environ['OPENAI_API_KEY'])
    byid={r['id']:r['input'] for r in rows};engine.payload=lambda r:byid[r['id']]
    all_results={}
    for version in ['2.8','2.9']:
        folder=OUT/('v'+version.replace('.',''));folder.mkdir(exist_ok=True)
        prompt=ROOT/f'training/data/prompts/policy_label_v{version}.md'
        immutable(folder/'manifest.json',dict(model=model,temperature=0,input_sha256=engine.digest(OUT/'inputs.jsonl'),
            prompt_sha256=engine.digest(prompt),contract_sha256=engine.digest(OUT/'contract.json'),version=version))
        engine.VERSION='policy-label-v'+version
        results=engine.read(folder/'predictions.jsonl');done={r['id'] for r in results}
        assert len(done)==len(results) and done<=set(byid)
        async def capture(response):
            if response.status_code==200:
                await response.aread();engine.append(folder/'raw_responses.jsonl',response.json())
        async with httpx.AsyncClient(timeout=120,event_hooks={'response':[capture]}) as client:
            for r in rows:
                if r['id'] in done:continue
                result=await engine.request({k:r[k] for k in ['id','service','method','path']}|{'meta':{}},prompt.read_text(encoding='utf8'),settings,client,folder/'usage.jsonl')
                engine.append(folder/'predictions.jsonl',result);results.append(result)
                print(version,len(results),'/8',flush=True)
        all_results[version]={r['id']:r for r in results}
    text='# 제출 설계 정렬: 그룹 구성원 라벨 실험\n\n최종 라벨은 OpenAI gpt-4o-mini가 선택했다. 조건 코드는 입력 근거이며 정답·검사 결과는 모델에 제공하지 않았다. 모델 출력을 규칙으로 덮어쓰지 않았다.\n\n'
    text+='| 사례 | 새 기준 계약 | v2.8 | v2.9 |\n|---|---|---|---|\n'
    for r in rows:text+=f"| {r['id']} | {r['target']} | {all_results['2.8'][r['id']].get('label')} | {all_results['2.9'][r['id']].get('label')} |\n"
    metrics={v:dict(agreement=sum(p[r['id']].get('label')==r['target'] for r in rows),n=len(rows),
        errors=sum(bool(x['meta'].get('label_error')) for x in p.values()),
        evidence_invalid=sum(bool(x['meta'].get('evidence_invalid')) for x in p.values())) for v,p in all_results.items()}
    text+='\n'+json.dumps(metrics,ensure_ascii=False)+'\n\n'
    text+='## 의미와 한계\n\nv2.9의 membership_required는 특정 요청 대상 그룹에 요청자가 속하는 관계다. 같은 tenant, 구독 등급, 객체 소유와 별개다. 구독만 요구하는 사례는 새 6종 중 표현할 라벨이 없어 보류한다. 그룹과 tenant가 동시에 필수인 경우도 단일 라벨로 조건을 버리지 않고 보류한다. v2.8은 다른 정의를 사용하므로 새 기준 일치도이며 기존 기준 정확도 하락을 뜻하지 않는다.\n\n합성 경계 사례 8건, 접근 함수 40건 및 익명 public 1건 검증이다. 함수 단위 검사이며 실제 서버 인증·DB 통합 검증이 아니다. 각 라벨의 표본이 매우 작고 같은 제작자가 계약과 코드를 만들었으므로 일반 성능을 주장하지 않는다.\n\n'
    text+='## 런타임 호환성: 자동 적용 금지\n\n현재 proxy/evaluator.py는 claims.membership이 policy.params.allowed_membership 목록에 있는지 비교한다. 이는 요청 대상 group_id와 요청자 사이의 구성원 관계 조회가 아니다. 새 의미의 membership 예측을 현재 런타임 정책으로 자동 배포하면 안 된다. 이번 변경은 실험 프롬프트와 보고서에 한정되며 runtime·정책 스키마·고정 test·기존 학습 라벨은 보존한다. runtime 변경에는 별도 설계가 필요하다.\n'
    immutable(OUT/'metrics.json',metrics)
    (OUT/'report.md').write_text(text,encoding='utf8')
    body=MarkdownIt('commonmark').enable('table').render(text)
    for v,p in all_results.items():body+='<details><summary>v'+v+' 원시 예측</summary><pre>'+html.escape(json.dumps(p,ensure_ascii=False,indent=2))+'</pre></details>'
    (OUT/'report.htm').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>그룹 라벨 정렬</title><style>body{max-width:1200px;margin:40px auto;font:16px/1.7 system-ui}td,th{padding:10px;border:1px solid #ccc}pre{white-space:pre-wrap}</style>'+body+'</html>',encoding='utf8')
    assert engine.digest(ROOT/'datasets/blade/processed/test.jsonl')=='bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa'
    print(metrics)


if __name__=='__main__':asyncio.run(main())
