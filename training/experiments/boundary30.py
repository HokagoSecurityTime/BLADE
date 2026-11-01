"""Frozen v2.9 code vs code+extracted Boolean conditions; synthetic development only."""
import ast
import asyncio
import copy
import html
import itertools
import json
import os
import random
import time
import httpx
from markdown_it import MarkdownIt
from training.data.label import read_env
from training.data.label_v6 import engine
from training.experiments.paired_policy import ROOT, immutable

OUT=ROOT/'reports/eval/classification_quality/boundary30_v29'
PROMPT=ROOT/'training/data/prompts/policy_label_v2.9.md'
# Contracts fixed before predictions. Each has two syntax variants, not two independent policies.
CONTRACTS=[('m','membership_required'),('t','tenant_match'),('o','owner_match'),
 ('r','role_required'),('o or a','owner_or_admin'),('True','public'),
 ('m and t','manual_review_required'),('o and t','manual_review_required'),
 ('m and r','manual_review_required'),('(o or a) and t','manual_review_required'),
 ('m or t','manual_review_required'),('o and a','manual_review_required'),
 ('m and o','manual_review_required'),('p','manual_review_required'),
 ('m and t and r','manual_review_required')]
ATOMS={'m':"(actor['id'], resource['group_id']) in memberships",
 't':"actor['tenant_id'] == resource['tenant_id']",
 'o':"actor['id'] == resource['owner_id']",'r':"'operator' in actor['roles']",
 'a':"'admin' in actor['roles']",'p':"actor['subscription'] == 'premium'"}


def extract(source):
    """Only accept generated straight-line aliases and explicit return patterns."""
    fn=ast.parse(source).body[0];aliases={}; statements=[]
    for n in fn.body:
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):aliases[n.targets[0].id]=n.value
        elif isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str):continue
        else:statements.append(n)
    if len(statements)==1 and isinstance(statements[0],ast.Return):expr=statements[0].value
    elif len(statements)==2 and isinstance(statements[0],ast.If) and isinstance(statements[1],ast.Return):
        branch=statements[0]
        assert not branch.orelse and len(branch.body)==1 and isinstance(branch.body[0],ast.Return)
        assert isinstance(branch.body[0].value,ast.Constant) and branch.body[0].value.value is False
        assert isinstance(statements[1].value,ast.Constant) and statements[1].value.value is True
        expr=ast.UnaryOp(op=ast.Not(),operand=branch.test)
    else:raise ValueError('unsupported flow')
    def expand(n,neg=False):
        if isinstance(n,ast.Name) and n.id in aliases:return expand(aliases[n.id],neg)
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.Not):return expand(n.operand,not neg)
        if isinstance(n,ast.BoolOp):
            op=ast.Or() if isinstance(n.op,ast.And) and neg else ast.And() if neg else n.op
            return ast.BoolOp(op=op,values=[expand(x,neg) for x in n.values])
        return ast.UnaryOp(op=ast.Not(),operand=copy.deepcopy(n)) if neg else copy.deepcopy(n)
    return ast.unparse(ast.fix_missing_locations(expand(expr)))


def prepare():
    OUT.mkdir(parents=True,exist_ok=True);rows=[];contracts=[];total=0
    for index,(formula,target) in enumerate(CONTRACTS):
        used=sorted({n.id for n in ast.walk(ast.parse(formula,mode='eval')) if isinstance(n,ast.Name)})
        for variant in range(2):
            ident=f'boundary-{index:02}-{variant}'
            source='def access(actor, resource, memberships):\n'
            if target=='public':source+='    """Anonymous access is explicitly permitted."""\n'
            source+=''.join(f'    {k} = {ATOMS[k]}\n' for k in used)
            source+=f'    return {formula}\n' if variant==0 else f'    if not ({formula}):\n        return False\n    return True\n'
            condition=extract(source);ns={};exec(source,ns)
            for bits in itertools.product([False,True],repeat=6):
                truth=dict(zip('mtorap',bits)); actor=dict(id='u',tenant_id='x',roles=[],subscription='premium' if truth['p'] else 'basic')
                if truth['r']:actor['roles'].append('operator')
                if truth['a']:actor['roles'].append('admin')
                resource=dict(group_id='g',tenant_id='x' if truth['t'] else 'y',owner_id='u' if truth['o'] else 'v')
                memberships={('u','g')} if truth['m'] else set()
                bindings=dict(actor=actor,resource=resource,memberships=memberships)
                wanted=eval(formula,{'__builtins__':{}},truth)
                assert ns['access'](**bindings)==wanted==eval(condition,{'__builtins__':{}},bindings)
                total+=1
            desc='This access function is the full authorization predicate for this synthetic handler. False produces 403, True permits access. actor is the caller; resource is the target. memberships contains (user_id, group_id) pairs. Authentication is a prerequisite except for explicitly anonymous public access. No additional authorization guards apply.\nFILE '+ident+'.py:1\n'+source
            base=dict(method='GET',path=f'/items-{index}/{variant}/{{id}}',path_params=['id'],query_params=[],summary='Read item',description=desc,
                security=[] if target=='public' else [{'Bearer':[]}],security_state='explicitly_anonymous' if target=='public' else 'declared',schema_fields=[],owner_cols=[],tenant_cols=[])
            augmented=copy.deepcopy(base);augmented['description']+='\nStatic extraction from the same function (not a policy label):\nALLOW IF '+condition
            rows.append(dict(id=ident,service='boundary-control',method='GET',path=base['path'],inputs=dict(code=base,code_conditions=augmented)))
            contracts.append(dict(id=ident,target=target,formula=formula,variant=variant,
                                  compound=index in [6,7,8,9,10,11,12,14],source=source,extracted=condition))
    immutable(OUT/'contracts.json',contracts)
    immutable(OUT/'inputs.jsonl',rows,True)
    immutable(OUT/'design.json',dict(seed=42,n=30,distinct_policy_templates=15,truth_table_checks=total,
        prompt_sha256=engine.digest(PROMPT),input_sha256=engine.digest(OUT/'inputs.jsonl'),
        extraction_sha256=engine.digest(__import__('pathlib').Path(__file__)),
        repeats=1,final_selector='LLM; no rule override',unsafe_metric='compound contract predicted as concrete label',
        raw_prediction_preserved=True,external_generalization=False))
    print('Prepared 30 cases;',total,'truth-table checks',flush=True)
    return rows


async def run():
    rows=prepare();read_env(ROOT/'.env')
    assert os.getenv('BLADE_LABEL_PROVIDER','openai')=='openai'
    model=os.getenv('BLADE_LABEL_MODEL','gpt-4o-mini');assert model in ['gpt-4o-mini','gpt-4o-mini-2024-07-18']
    settings=engine.llm.Settings('openai',model,os.environ['OPENAI_API_KEY']);engine.VERSION='policy-label-v2.9'
    # Request-specific input instead of a shared mutable condition selector.
    byid={c+':'+r['id']:r['inputs'][c] for r in rows for c in ['code','code_conditions']}
    engine.payload=lambda r:byid[r['id']]
    jobs=[];results={}
    for condition in ['code','code_conditions']:
        folder=OUT/condition;folder.mkdir(exist_ok=True)
        immutable(folder/'manifest.json',dict(model=model,temperature=0,prompt_sha256=engine.digest(PROMPT),
            inputs_sha256=engine.digest(OUT/'inputs.jsonl'),contract_sha256=engine.digest(OUT/'contracts.json'),condition=condition))
        old=engine.read(folder/'predictions.jsonl');done={r['id'] for r in old};results[condition]=old
        assert len(old)==len(done) and done<=set(byid)
        for r in rows:
            key=condition+':'+r['id']
            if key not in done:jobs.append((condition,r,key))
    random.Random(42).shuffle(jobs)
    semaphore=asyncio.Semaphore(4)
    async def capture(response):
        if response.status_code==200:
            await response.aread();engine.append(OUT/'raw_responses.jsonl',response.json())
    async with httpx.AsyncClient(timeout=180,event_hooks={'response':[capture]}) as client:
        async def one(condition,r,key):
            async with semaphore:
                started=time.perf_counter()
                result=await engine.request(dict(id=key,service=r['service'],method=r['method'],path=r['path'],meta={}),PROMPT.read_text(encoding='utf8'),settings,client,OUT/condition/'usage.jsonl')
                result['case_id']=r['id'];result['elapsed_ms']=(time.perf_counter()-started)*1000
                return condition,result
        tasks=[asyncio.create_task(one(*job)) for job in jobs]
        try:
            for task in asyncio.as_completed(tasks):
                c,result=await task;engine.append(OUT/c/'predictions.jsonl',result);results[c].append(result)
                print(c,len(results[c]),'/30',flush=True)
        finally:
            for t in tasks:
                if not t.done():t.cancel()
            await asyncio.gather(*tasks,return_exceptions=True)
    report()


def report():
    contracts=json.loads((OUT/'contracts.json').read_text(encoding='utf8'));metrics={};preds={}
    for c in ['code','code_conditions']:
        preds[c]={r['case_id']:r for r in engine.read(OUT/c/'predictions.jsonl')}
        assert len(preds[c])==30
        correct=sum(preds[c][r['id']].get('label')==r['target'] for r in contracts)
        unsafe=[r['id'] for r in contracts if r['compound'] and preds[c][r['id']].get('label') in engine.LABELS and preds[c][r['id']]['label']!='manual_review_required']
        per={}
        for label in engine.LABELS:
            tp=sum(r['target']==label and preds[c][r['id']].get('label')==label for r in contracts)
            actual=sum(r['target']==label for r in contracts);selected=sum(p.get('label')==label for p in preds[c].values())
            precision=tp/selected if selected else 0;recall=tp/actual if actual else 0
            per[label]=dict(precision=precision,recall=recall,f1=2*precision*recall/(precision+recall) if precision+recall else 0,support=actual)
        usage=engine.read(OUT/c/'usage.jsonl')
        metrics[c]=dict(correct=correct,n=30,macro_f1=sum(p['f1'] for p in per.values())/7,per_label=per,
            compound_count=sum(r['compound'] for r in contracts),compound_concrete_count=len(unsafe),compound_concrete_ids=unsafe,
            label_errors=sum(bool(p['meta'].get('label_error')) for p in preds[c].values()),
            evidence_invalid=sum(bool(p['meta'].get('evidence_invalid')) for p in preds[c].values()),
            responses=len(usage),input_tokens=sum(x['usage'].get('input_tokens',x['usage'].get('prompt_tokens',0)) for x in usage),
            output_tokens=sum(x['usage'].get('output_tokens',x['usage'].get('completion_tokens',0)) for x in usage))
    engine.dump(OUT/'metrics.json',metrics)
    text='# v2.9 새 경계 사례 30건: 추출 조건식 효과\n\n동일 프롬프트·동일 모델·동일 코드에 추출 허용 조건식만 추가했다. 모델의 최종 라벨을 변경하지 않았다.\n\n| 조건 | 계약 일치 | macro-F1 | 복합 정책을 구체 라벨로 축약 |\n|---|---:|---:|---:|\n'
    for c,m in metrics.items():text+=f"| {c} | {m['correct']}/30 | {m['macro_f1']:.4f} | {m['compound_concrete_count']}/{m['compound_count']} |\n"
    text+='\n## 해석 범위\n\n15개 정책 템플릿 × 코드 표현 2종이다. 독립 정책 30개가 아니다. 기존 8건의 파일·ID는 사용하지 않지만 단일 조건 의미는 일부 겹친다. 새 프로젝트 또는 독립 외부 평가셋이 아니다. 동일 제작자가 합성 계약과 구현을 작성했다.\n\n조건식은 AST의 반환·거부 분기에서 추출하고 별칭 확장과 De Morgan 변환을 수행했다. 30×64=1,920개 조합에서 원본 함수·추출식·별도 계약 논리의 판정을 비교했다. 기존 8건과 달리 복합 조건을 의도적으로 많이 포함하므로 이전 7/8과 직접 점수 비교하지 않는다.\n\n복합 계약을 구체 라벨로 축약한 건수는 계약 불일치 위험 지표다. 실제 운영에서 권한이 확대됐음을 입증한 수치는 아니다. runtime에는 반영하지 않았다. 양 조건은 seed 42로 섞어 동시성 4로 실행했고 각 1회이며 반복 실행 안정성은 측정하지 않았다. 오류는 보류 정답으로 처리하지 않는다.\n'
    text+='\n## 사례별 비교\n\n| 사례 | 계약 | 코드 | 코드+조건 |\n|---|---|---|---|\n'
    for r in contracts:text+=f"| {r['id']} | {r['target']} | {preds['code'][r['id']].get('label')} | {preds['code_conditions'][r['id']].get('label')} |\n"
    text+='\n## 원본 및 재현\n\ncontracts.json은 모델에게 전달하지 않은 계약·검사 논리, inputs.jsonl은 두 조건의 실제 입력, 각 폴더의 predictions.jsonl·usage.jsonl은 원시 예측과 사용량이다. raw_responses.jsonl은 API 응답 전체다. manifest에는 모델·프롬프트·입력·계약 해시를 기록했다. 기존 membership 런타임은 그룹 관계를 집행하지 못하므로 새 의미 결과 자동 적용은 금지한다.\n'
    (OUT/'report.md').write_text(text,encoding='utf8')
    body=MarkdownIt('commonmark').enable('table').render(text)
    for r in contracts:
        body+='<details><summary>'+r['id']+'</summary><pre>'+html.escape(json.dumps(dict(contract=r,code=preds['code'][r['id']],code_conditions=preds['code_conditions'][r['id']]),ensure_ascii=False,indent=2))+'</pre></details>'
    (OUT/'report.htm').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>v2.9 30건 경계 실험</title><style>body{max-width:1200px;margin:40px auto;padding:20px;font:16px/1.7 system-ui}table{border-collapse:collapse}td,th{border:1px solid #ccd;padding:8px}pre{white-space:pre-wrap;overflow-wrap:anywhere}details{margin:12px 0}</style>'+body+'</html>',encoding='utf8')
    assert engine.digest(PROMPT)==json.loads((OUT/'design.json').read_text())['prompt_sha256']
    assert engine.digest(ROOT/'datasets/blade/processed/test.jsonl')=='bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa'
    print({c:{k:m[k] for k in ['correct','macro_f1','compound_concrete_count']} for c,m in metrics.items()})


if __name__=='__main__':asyncio.run(run())
