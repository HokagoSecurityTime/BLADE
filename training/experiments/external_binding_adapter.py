"""Pinned, source-audited external adapter; experimental, not deployment approval."""
from __future__ import annotations
import ast
import itertools
import json
from collections import Counter
from pathlib import Path
from training.experiments.external_paired_v29 import RAW, OUT as INPUT, ROOT, digest, function_span

OUT = ROOT/'reports/eval/classification_quality/external_binding_adapter_v1'
SUPPORTED = {'items.read_item', 'items.update_item', 'items.delete_item',
             'users.read_user_by_id', 'users.read_user_me', 'users.delete_user_me',
             'users.delete_user', 'login.test_token'}


def check_snapshot() -> None:
    manifest=json.loads((INPUT/'sources.json').read_text(encoding='utf8'))
    for row in manifest['files']:
        if digest(RAW/row['path'])!=row['sha256']:
            raise ValueError('Source snapshot changed: '+row['path'])


def symbolic(source: str, target: str | None) -> str:
    """Extract return reachability, preserving early return, NOT and AND/OR.

    Called only for reviewed hash-pinned handlers. Existing object and authenticated
    active user are preconditions; 404 is not an authorization predicate.
    """
    fn=ast.parse(source).body[0]
    def expression(n: ast.AST) -> str:
        value=ast.unparse(n)
        if value=='current_user.is_superuser':return 'admin'
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.Not):return '(not '+expression(n.operand)+')'
        if isinstance(n,ast.BoolOp):
            return '('+(' and ' if isinstance(n.op,ast.And) else ' or ').join(expression(v) for v in n.values)+')'
        if isinstance(n,ast.Compare) and len(n.ops)==1:
            left,right=ast.unparse(n.left),ast.unparse(n.comparators[0])
            if (left,right) in [(f'{target}.owner_id','current_user.id'),(target,'current_user')]:
                if isinstance(n.ops[0],ast.Eq):return 'owner'
                if isinstance(n.ops[0],ast.NotEq):return '(not owner)'
        raise ValueError('Unsupported authorization expression: '+value)
    def walk(nodes: list, active: str) -> list[str]:
        returns=[]
        for node in nodes:
            if isinstance(node,ast.Return):return returns+[active]
            if isinstance(node,ast.If):
                raises=[n for n in ast.walk(node) if isinstance(n,ast.Raise)]
                codes=[k.value.value for n in raises if isinstance(n.exc,ast.Call) for k in n.exc.keywords if k.arg=='status_code' and isinstance(k.value,ast.Constant)]
                if codes==[404]:continue
                test=expression(node.test)
                if codes==[403] and len(node.body)==1 and isinstance(node.body[0],ast.Raise) and not node.orelse:
                    active=f'({active} and not ({test}))'
                elif len(node.body)==1 and isinstance(node.body[0],ast.Return) and not node.orelse:
                    returns.append(f'({active} and {test})');active=f'({active} and not ({test}))'
                else:raise ValueError('Unsupported branch')
            elif isinstance(node,(ast.For,ast.While,ast.Try,ast.With,ast.Raise)):
                raise ValueError('Unsupported flow')
        return returns
    values=walk(fn.body,'True')
    if not values:raise ValueError('No successful return')
    return '('+' or '.join(values)+')'


def extract(ident: str) -> dict:
    if ident not in SUPPORTED:return dict(status='unresolved',reason='handler_not_audited')
    module,name=ident.split('.')
    path=RAW/f'backend/app/api/routes/{module}.py'
    ref=function_span(path,name)
    fn=ast.parse(ref['code']).body[0]
    lookup=None;target=None
    for node in fn.body:
        if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call) and ast.unparse(node.value.func)=='session.get':
            target=ast.unparse(node.targets[0])
            lookup=dict(model=ast.unparse(node.value.args[0]),parameter=ast.unparse(node.value.args[1]),variable=target,
                        file=ref['file'],line=ref['start']+node.lineno-1)
    self_bound=target is None and any(isinstance(n,ast.Return) and ast.unparse(n.value)=='current_user' or
                                     isinstance(n,ast.Call) and ast.unparse(n.func)=='session.delete' and n.args and ast.unparse(n.args[0])=='current_user' for n in ast.walk(fn))
    if not lookup and not self_bound:return dict(status='unresolved',reason='object_binding_missing')
    tree=ast.parse(path.read_text(encoding='utf8'))
    decorated=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    dep_required=any('get_current_active_superuser' in ast.unparse(d) for d in decorated.decorator_list)
    refs=[ref,function_span(RAW/'backend/app/api/deps.py','get_current_user')]
    allow=symbolic(ref['code'],target)
    if dep_required:
        dep=function_span(RAW/'backend/app/api/deps.py','get_current_active_superuser')
        allow=f'({symbolic(dep["code"],None)} and {allow})';refs.append(dep)
    if self_bound:allow=f'(owner and {allow})'
    return dict(status='extracted',allow=allow,lookup=lookup,self_bound=self_bound,
                caller_binding='CurrentUser -> get_current_user -> JWT sub -> session.get(User, token_data.sub)',
                admin_binding='current_user.is_superuser',owner_binding='target user equals caller' if self_bound or lookup['model']=='User' else 'Item.owner_id == current_user.id',
                source_refs=refs,preconditions=['authenticated active user','target exists'],
                limitations=['Pinned reviewed handlers only','DB/JWT and global deployment not verified','implemented policy, not proof of intended policy'])


def boolean(formula: str, state: dict) -> bool:
    def visit(n: ast.AST) -> bool:
        if isinstance(n,ast.Constant) and type(n.value)==bool:return n.value
        if isinstance(n,ast.Name) and n.id in state:return state[n.id]
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.Not):return not visit(n.operand)
        if isinstance(n,ast.BoolOp) and isinstance(n.op,(ast.And,ast.Or)):
            return all(visit(v) for v in n.values) if isinstance(n.op,ast.And) else any(visit(v) for v in n.values)
        raise ValueError('Unsupported boolean formula')
    return visit(ast.parse(formula,mode='eval').body)


def verify(pred: dict, evidence: dict) -> dict:
    result=dict(original_label=pred.get('label'),original_confidence=pred.get('confidence'),auto_apply_allowed=False,semantic_candidate_pass=False)
    if evidence['status']!='extracted':return dict(result,reason='unresolved_source')
    patterns=dict(public='True',owner_match='owner',owner_or_admin='owner or admin',membership_required='member',tenant_match='tenant')
    label=pred.get('label')
    if label=='role_required':return dict(result,reason='role_parameter_unresolved')
    if label not in patterns:return dict(result,reason='manual_or_invalid_label')
    broader=[];stricter=[]
    for bits in itertools.product([False,True],repeat=4):
        state=dict(zip(['owner','admin','member','tenant'],bits))
        actual=boolean(evidence['allow'],state);proposed=boolean(patterns[label],state)
        if proposed and not actual:broader.append(state)
        if actual and not proposed:stricter.append(state)
    reason='missing_required_condition' if broader else 'overrestriction' if stricter else 'equivalent'
    if any(pred.get('meta',{}).get(k) for k in ['label_error','evidence_invalid','flag_review']):reason='prediction_validation_failed'
    return dict(result,reason=reason,semantic_candidate_pass=reason=='equivalent',counterexample=(broader or stricter or [None])[0],broadened_states=len(broader),overrestricted_states=len(stricter))


def run() -> None:
    from markdown_it import MarkdownIt
    check_snapshot()
    rows=json.loads((INPUT/'inputs.json').read_text(encoding='utf8'))
    preds=[json.loads(s) for s in (INPUT/'predictions.jsonl').read_text(encoding='utf8').splitlines()]
    hashes={str(p):digest(p) for p in [INPUT/'predictions.jsonl',ROOT/'datasets/blade/processed/test.jsonl',ROOT/'training/experiments/application_guard.py']}
    evidence={r['id']:extract(r['id']) for r in rows}
    decisions=[dict(id=p['id'],prediction=p,guard=verify(p,evidence[p['case_id']])) for p in preds]
    metrics={c:dict(Counter(d['guard']['reason'] for d in decisions if d['prediction']['condition']==c)) for c in ['oas','oas_code']}
    OUT.mkdir(exist_ok=True)
    for name,value in [('evidence',evidence),('decisions',decisions),('metrics',metrics),('manifest',dict(api_calls=0,input_hashes=hashes,adapter_sha256=digest(Path(__file__)),scope='development on previously evaluated project'))]:
        (OUT/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
    text='# 외부 코드 바인딩 어댑터 v1\n\n기존 실험을 개발셋으로 사용했다. 새 독립 성능 평가가 아니다. API 재호출 없이 원래 예측을 보존했다.\n\n'
    text+=f'23개 중 {sum(e["status"]=="extracted" for e in evidence.values())}개 핸들러의 객체 바인딩·허용 조건을 추출했다. 나머지는 미확정이다. 원본 해시가 달라지면 실행을 거부한다. 범용 Python 파서가 아니라 검토한 고정 소스용 어댑터다.\n\n'
    text+='| 조건 | 검증 결과 | 건수 |\n|---|---|---:|\n'
    for c,counts in metrics.items():
        for reason,count in counts.items():text+=f'| {c} | {reason} | {count} |\n'
    text+='\n## 추출한 조건\n\n| 핸들러 | 허용 조건 | 객체 조회 |\n|---|---|---|\n'
    for ident,e in evidence.items():
        if e['status']=='extracted':text+=f'| {ident} | `{e["allow"]}` | `{e["lookup"] or "authenticated self"}` |\n'
    text+='\nNOT superuser와 target != caller를 보존하며, 조기 반환은 OR 경로로 반영한다. 인증 사용자 반환을 그룹 membership으로 해석하지 않는다. role_required는 실제 역할 파라미터가 없어 미확정 처리한다.\n\n의미 통과와 실제 자동 적용은 다르다. 집행 설정·DB/JWT 통합 검증이 없어 auto_apply_allowed는 전부 false다. 코드의 현재 검사와 의도된 정책 일치를 입증하지 않는다. 기존 검증기·프롬프트·고정 test·런타임을 변경하지 않았다.\n'
    (OUT/'report.md').write_text(text,encoding='utf8')
    (OUT/'report.htm').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>외부 어댑터</title><style>body{max-width:1200px;margin:40px auto;font:16px/1.7 system-ui}table{border-collapse:collapse}td,th{border:1px solid #bbb;padding:8px}</style>'+MarkdownIt().enable('table').render(text)+'</html>',encoding='utf8')
    assert hashes=={p:digest(Path(p)) for p in hashes}
    print(json.dumps(metrics,indent=2))


if __name__=='__main__':run()
