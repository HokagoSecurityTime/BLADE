"""v2 ORM bridge for the pinned audited project; explicit statement contracts."""
from __future__ import annotations
import ast
import copy
import json
from collections import Counter
from pathlib import Path
from training.experiments import external_binding_adapter as base
from training.experiments.external_binding_adapter_v2 import symbolic


def normalize(source: str) -> tuple[str,dict,list]:
    fn=ast.parse(source).body[0]
    bindings={};events=[];target=None;body=[]
    def event(node: ast.AST,kind: str) -> None:
        events.append(dict(kind=kind,line=node.lineno,code=ast.unparse(node)))
    for n in fn.body:
        s=ast.unparse(n)
        if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='session.get':
            if target or len(n.targets)!=1 or not isinstance(n.targets[0],ast.Name) or len(n.value.args)!=2 or n.value.keywords:raise ValueError('ambiguous lookup')
            model,param=map(ast.unparse,n.value.args)
            if model not in ['Item','User'] or param not in [a.arg for a in fn.args.args+fn.args.kwonlyargs]:raise ValueError('unbound lookup')
            target=n.targets[0].id;bindings=dict(model=model,parameter=param,target=target);event(n,'object_lookup');continue
        if isinstance(n,ast.If) and target and ast.unparse(n.test) in ['not '+target,target+' is None']:
            if len(n.body)!=1 or not isinstance(n.body[0],ast.Raise) or n.orelse:raise ValueError('unknown missing-object branch')
            call=n.body[0].exc
            if not isinstance(call,ast.Call) or ast.unparse(call.func)!='HTTPException' or not any(k.arg=='status_code' and isinstance(k.value,ast.Constant) and k.value.value==404 for k in call.keywords):raise ValueError('unknown missing-object denial')
            event(n,'existing_object_precondition');continue
        allowed={
            'update_dict = item_in.model_dump(exclude_unset=True)': 'validated_ItemUpdate_fields',
            'item.sqlmodel_update(update_dict)':'update_bound_object',
            'session.add(item)':'persist_bound_object','session.delete(item)':'delete_bound_object',
            'session.refresh(item)':'refresh_bound_object','session.delete(current_user)':'delete_authenticated_self',
            'session.delete(user)':'delete_bound_user','session.commit()':'transaction_commit',
            'statement = delete(Item).where(col(Item.owner_id) == user_id)':'cascade_bound_user_items',
            'session.exec(statement)':'execute_bound_cascade',
        }
        if s in allowed:
            event(n,allowed[s]);continue
        if isinstance(n,ast.Return) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='Message' and all(isinstance(k.value,ast.Constant) for k in n.value.keywords) and not n.value.args:
            event(n,'constant_success_response');body.append(ast.Return(value=ast.Name(id=target or 'current_user',ctx=ast.Load())));continue
        body.append(copy.deepcopy(n))
    if target is None:
        if not any(isinstance(n,ast.Return) and ast.unparse(n.value)=='current_user' for n in body):raise ValueError('self target missing')
        bindings=dict(model='User',target='current_user',parameter='JWT.sub',self_bound=True)
    fn.body=body;fn.decorator_list=[];fn.returns=None
    fn.args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='current_user'),ast.arg(arg=target or 'item')],kwonlyargs=[],kw_defaults=[],defaults=[])
    return ast.unparse(ast.fix_missing_locations(fn)),bindings,events


def extract(ident: str) -> dict:
    base.check_snapshot()
    if ident not in base.SUPPORTED:return dict(status='unresolved',reason='unaudited_handler')
    module,name=ident.split('.')
    path=base.RAW/f'backend/app/api/routes/{module}.py'
    ref=base.function_span(path,name)
    try:
        normalized,binding,events=normalize(ref['code'])
        allow=symbolic(normalized,binding['target'] if not binding.get('self_bound') else 'item')
        tree=ast.parse(path.read_text(encoding='utf8'))
        original=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        dep=any('get_current_active_superuser' in ast.unparse(d) for d in original.decorator_list)
        refs=[ref,base.function_span(base.RAW/'backend/app/api/deps.py','get_current_user')]
        if dep:
            d=base.function_span(base.RAW/'backend/app/api/deps.py','get_current_active_superuser')
            allow='('+symbolic(d['code'])+' and '+allow+')';refs.append(d)
        if binding.get('self_bound'):allow='(owner and '+allow+')'
        return dict(status='extracted',allow=allow,binding=binding,events=events,source_refs=refs,
                    caller_chain='CurrentUser -> get_current_user -> JWT sub -> session.get(User, sub)',
                    preconditions=['existing target','authenticated active caller'],
                    assumptions=['hash-pinned imports/models/router configuration audited','SQLModel operations use declared library semantics, not independently executed database'],normalized=normalized)
    except (ValueError,SyntaxError) as exc:return dict(status='unresolved',reason=str(exc))


def run() -> None:
    from markdown_it import MarkdownIt
    out=base.ROOT/'reports/eval/classification_quality/external_orm_adapter_v2'
    out.mkdir(exist_ok=True)
    rows=json.loads((base.INPUT/'inputs.json').read_text(encoding='utf8'))
    preds=[json.loads(s) for s in (base.INPUT/'predictions.jsonl').read_text(encoding='utf8').splitlines()]
    evidence={r['id']:extract(r['id']) for r in rows}
    decisions=[dict(id=p['id'],original_prediction=p,guard=base.verify(p,evidence[p['case_id']])) for p in preds]
    metrics={c:dict(Counter(d['guard']['reason'] for d in decisions if d['original_prediction']['condition']==c)) for c in ['oas','oas_code']}
    for name,value in [('evidence',evidence),('decisions',decisions),('metrics',metrics),('manifest',dict(api_calls=0,adapter_sha256=base.digest(Path(__file__)),prediction_sha256=base.digest(base.INPUT/'predictions.jsonl'),scope='development regression; not independent evaluation'))]:
        (out/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
    text='# 프롬프트 v2.9 / ORM 어댑터 v2 개발 검증\n\n검토한 고정 소스의 ORM 조회·인가 의존성·객체 변경 호출을 연결했다. v1과 기존 결과는 보존했다.\n\n'
    text+=f'지원 {sum(e["status"]=="extracted" for e in evidence.values())}/23건. 나머지는 보류한다. API 호출 0회.\n\n| 입력 | 결과 | 건수 |\n|---|---|---:|\n'
    for c,counts in metrics.items():
        for reason,n in counts.items():text+=f'| {c} | {reason} | {n} |\n'
    text+='\n## 범위\n\n호출과 변수 연결은 evidence.json에 원본 위치·정규화 내역으로 기록했다. 객체 부재 검사만 404 전제 처리하며 소유권 404는 조건으로 남긴다. 허용 목록 밖 호출·대입은 보류한다. 입력 소스 전체 해시를 매번 확인하므로 허용 목록을 임의의 외부 코드에 적용하지 않는다.\n\nSQLModel 라이브러리 의미와 검토한 모델을 전제로 한다. 실제 DB·JWT 통합 검증이나 일반적인 import/call graph 분석을 완료한 것은 아니다. 기존 프로젝트를 개발셋으로 재사용했으므로 독립 성능 수치가 아니다. 의미 통과도 자동 적용 승인이 아니며 auto_apply_allowed는 false다.\n'
    (out/'report.md').write_text(text,encoding='utf8')
    (out/'report.htm').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>ORM 어댑터 v2</title>'+MarkdownIt().enable('table').render(text)+'</html>',encoding='utf8')
    print(metrics)


if __name__=='__main__':run()
