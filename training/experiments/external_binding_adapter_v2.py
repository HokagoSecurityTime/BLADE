"""Conservative guard-function analyzer. Unknown calls never silently pass."""
from __future__ import annotations
import ast
import json
from pathlib import Path
from training.experiments import external_binding_adapter as v1


def symbolic(source: str, target: str = 'item', helpers: dict[str,str] | None = None,
             *, assertions_enabled: bool = False, stack: tuple = ()) -> str:
    module=ast.parse(source)
    if len(module.body)!=1 or not isinstance(module.body[0],ast.FunctionDef):raise ValueError('unsupported function')
    fn=module.body[0]
    if fn.decorator_list or fn.args.defaults or fn.args.kwonlyargs or fn.args.vararg or fn.args.kwarg:
        raise ValueError('unsupported signature')
    helpers=helpers or {}
    def expr(n: ast.AST) -> str:
        text=ast.unparse(n)
        if text=='current_user.is_superuser':return 'admin'
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.Not):return '(not '+expr(n.operand)+')'
        if isinstance(n,ast.BoolOp):return '('+(' and ' if isinstance(n.op,ast.And) else ' or ').join(expr(x) for x in n.values)+')'
        if isinstance(n,ast.Compare) and len(n.ops)==1 and (ast.unparse(n.left),ast.unparse(n.comparators[0])) in [(target+'.owner_id','current_user.id'),(target,'current_user')]:
            if isinstance(n.ops[0],ast.Eq):return 'owner'
            if isinstance(n.ops[0],ast.NotEq):return '(not owner)'
        raise ValueError('unknown condition: '+text)
    def walk(nodes: list, active: str) -> tuple[list[str],str]:
        returns=[]
        for node in nodes:
            if isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):continue
            if isinstance(node,ast.Return):
                if node.value is not None and (not isinstance(node.value,ast.Name) or node.value.id not in [target,'current_user']):raise ValueError('unsupported return')
                return returns+[active],'False'
            if isinstance(node,ast.Raise):
                call=node.exc
                if not isinstance(call,ast.Call) or not isinstance(call.func,ast.Name) or call.func.id not in ['Denied','HTTPException'] or call.args:raise ValueError('unknown exception')
                codes=[k.value.value for k in call.keywords if k.arg=='status_code' and isinstance(k.value,ast.Constant)]
                if codes not in [[403],[404]] or any(not isinstance(k.value,ast.Constant) for k in call.keywords):raise ValueError('unknown denial')
                return returns,'False'
            if isinstance(node,ast.If):
                test=expr(node.test)
                yes,y=walk(node.body,f'({active} and {test})')
                no,n=walk(node.orelse,f'({active} and not ({test}))')
                returns+=yes+no;active=f'({y} or {n})'
            elif isinstance(node,ast.Assert):
                if not assertions_enabled:raise ValueError('assert execution mode unverified')
                active=f'({active} and {expr(node.test)})'
            elif isinstance(node,ast.Expr) and isinstance(node.value,ast.Call):
                call=node.value
                if not isinstance(call.func,ast.Name) or call.func.id not in helpers or call.keywords:raise ValueError('unresolved call')
                name=call.func.id
                if name in stack:raise ValueError('recursive helper')
                helper=ast.parse(helpers[name]).body[0]
                params=[a.arg for a in helper.args.args]
                if len(params)!=len(call.args) or any(not isinstance(a,ast.Name) or a.id not in ['current_user',target] for a in call.args):raise ValueError('unknown argument binding')
                mapping=dict(zip(params,call.args))
                class Bind(ast.NodeTransformer):
                    def visit_Name(self,n: ast.Name) -> ast.AST:
                        return ast.copy_location(ast.Name(id=mapping[n.id].id,ctx=n.ctx),n) if n.id in mapping else n
                bound=Bind().visit(helper)
                constraint=symbolic(ast.unparse(bound),target,helpers,assertions_enabled=assertions_enabled,stack=stack+(name,))
                active=f'({active} and {constraint})'
            else:raise ValueError('unsupported statement: '+type(node).__name__)
        return returns,active
    returns,fallthrough=walk(fn.body,'True')
    return '('+' or '.join(returns+[fallthrough])+')'


def extract(ident: str) -> dict:
    # Each entry validates the audited snapshot; no unchecked standalone extraction.
    v1.check_snapshot()
    if ident not in v1.SUPPORTED:return dict(status='unresolved',reason='handler_not_audited')
    # Full handlers contain ORM calls. Do not reuse v1's silent statement skipping.
    return dict(status='unresolved',reason='full_handler_orm_and_call_closure_not_supported',id=ident)


def run() -> None:
    from markdown_it import MarkdownIt
    origin=v1.ROOT/'reports/eval/classification_quality/adapter_stress_v1'
    protocol=json.loads((origin/'protocol.json').read_text(encoding='utf8'))
    actual={r['id']:r['states'] for r in json.loads((origin/'results.json').read_text(encoding='utf8'))['results']}
    helper='def require_owner(user, obj):\n    if obj.owner_id != user.id:\n        raise Denied(status_code=403)\n'
    results=[]
    for ident,source in protocol['cases'].items():
        try:
            formula=symbolic(source,helpers={'require_owner':helper})
            errors=[s for s in actual[ident] if v1.boolean(formula,s)!=s['actual']]
            result=dict(id=ident,status='incorrect' if errors else 'equivalent',formula=formula,counterexamples=errors)
        except ValueError as exc:result=dict(id=ident,status='held',reason=str(exc))
        results.append(result)
    counts={k:sum(r['status']==k for r in results) for k in ['equivalent','incorrect','held']}
    out=v1.ROOT/'reports/eval/classification_quality/adapter_v2_regression'
    out.mkdir(exist_ok=True)
    (out/'results.json').write_text(json.dumps(dict(counts=counts,results=results,api_calls=0,adapter_sha256=v1.digest(Path(__file__))),indent=2),encoding='utf8')
    text='# 어댑터 v2 회귀 검증\n\n프롬프트는 v2.9 그대로다. v1의 기존 변형 10건을 재사용한 개발 검증이며 독립 평가가 아니다.\n\n'
    text+=f'정확한 추출 {counts["equivalent"]}건 / 잘못된 추출 {counts["incorrect"]}건 / 보류 {counts["held"]}건. API 호출 0회.\n\n'
    text+='| 사례 | 결과 | 보류 사유 |\n|---|---|---|\n'
    for r in results:text+=f'| {r["id"]} | {r["status"]} | {r.get("reason", "")} |\n'
    text+='\n404 인가 거부와 전달된 helper의 인자 연결을 보존한다. 미해결 호출·대입은 보류한다. assert는 Python 최적화 실행에서 사라질 수 있어 기본적으로 보류하며, 활성화가 확인된 테스트에서만 해석한다.\n\n**제약:** 실제 ORM 핸들러 전체 호출 연결은 아직 미지원이다. v2는 이를 보류하며 v1의 8건 지원을 유지했다고 주장하지 않는다. 단독 extract 호출도 원본 해시를 확인한다. helper 소스는 명시적으로 전달해야 하며 자동 import 해석은 미구현이다. 외부 독립 실험 전에 ORM/호출 그래프 지원을 별도로 추가해야 한다. 자동 적용은 하지 않는다.\n'
    (out/'report.md').write_text(text,encoding='utf8')
    (out/'report.htm').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>어댑터 v2</title>'+MarkdownIt().enable('table').render(text)+'</html>',encoding='utf8')
    print(counts)


if __name__=='__main__':run()
