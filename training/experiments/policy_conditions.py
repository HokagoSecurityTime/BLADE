"""Conservative Python guard extractor for the paired development experiment.

Not a general control-flow verifier. Only straight-line local calls and explicit
HTTPException rejection guards are supported; unknown control flow abstains.
"""
import ast
import re


def invert(expr):
    if expr['op'] in ('and', 'or'):
        return {'op': 'or' if expr['op']=='and' else 'and', 'args':[invert(x) for x in expr['args']]}
    return {**expr, 'comparison': 'eq' if expr['comparison']=='ne' else 'ne'}


def field(node):
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and isinstance(node.slice, ast.Constant):
        return (node.value.id, node.slice.value)
    return None


def expression(node):
    if isinstance(node, ast.BoolOp):
        return {'op':'and' if isinstance(node.op, ast.And) else 'or', 'args':[expression(v) for v in node.values]}
    if not isinstance(node, ast.Compare) or len(node.ops)!=1 or not isinstance(node.ops[0], (ast.Eq,ast.NotEq)):
        raise ValueError('unsupported comparison')
    left,right=field(node.left),field(node.comparators[0])
    comparison='eq' if isinstance(node.ops[0],ast.Eq) else 'ne'
    if left and right and left[0]!=right[0] and {left[1],right[1]}=={'sub','owner'}:
        kind='owner_equal';value=None
    elif left and right and left[0]!=right[0] and left[1]==right[1]=='tenant':
        kind='tenant_equal';value=None
    elif left and left[1] in ('role','plan') and isinstance(node.comparators[0],ast.Constant):
        kind='role' if left[1]=='role' else 'subscription';value=node.comparators[0].value
    else:
        raise ValueError('unknown subject/resource relationship')
    return dict(op='atom',kind=kind,value=value,comparison=comparison,source_expression=ast.unparse(node))


def status_code(statement):
    if isinstance(statement,ast.Raise) and isinstance(statement.exc,ast.Call):
        call=statement.exc
        if isinstance(call.func,ast.Name) and call.func.id=='HTTPException':
            value=call.args[0] if call.args else next((k.value for k in call.keywords if k.arg=='status_code'),None)
            if isinstance(value,ast.Constant):return value.value
    return None


def extract(excerpts, method, path):
    functions={}; locations={}; issues=[]; root=None; credential_sources=set()
    for e in excerpts:
        code='\n'.join(re.sub(r'^\d+: ', '', line) for line in e['code'].splitlines())
        try: tree=ast.parse(code)
        except SyntaxError:
            issues.append('non_top_level_or_incomplete_excerpt');continue
        for n in tree.body:
            if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='HTTPBearer':
                credential_sources.update(t.id for t in n.targets if isinstance(t,ast.Name))
            if isinstance(n,ast.FunctionDef):
                functions[n.name]=n;locations[n.name]=e
                for d in n.decorator_list:
                    if isinstance(d,ast.Call) and isinstance(d.func,ast.Attribute) and d.func.attr==method.lower() and d.args and isinstance(d.args[0],ast.Constant) and d.args[0].value==path:
                        root=n.name
    if root is None:return dict(conditions=None,authentication=False,evidence=[],issues=issues+['handler_unresolved'])
    conditions=[];evidence=[];seen=set();auth=False
    def visit(name):
        nonlocal auth
        if name in seen:return
        seen.add(name);fn=functions[name];e=locations[name]
        for default in fn.args.defaults:
            if isinstance(default,ast.Call) and isinstance(default.func,ast.Name) and default.func.id=='Depends':
                if default.args and isinstance(default.args[0],ast.Name) and default.args[0].id in functions:
                    visit(default.args[0].id)
                elif not (default.args and isinstance(default.args[0],ast.Name) and default.args[0].id in credential_sources):
                    issues.append('unresolved_dependency')
        for st in fn.body:
            if isinstance(st,ast.If):
                if len(st.body)!=1 or st.orelse:
                    issues.append('unsupported_guard_control_flow');continue
                code=status_code(st.body[0])
                if code==403:
                    try:
                        allow=invert(expression(st.test));conditions.append(allow)
                        evidence.append(dict(path=e['path'],sha256=e['sha256'],
                            line=e['start']+st.lineno-1, rejection=ast.unparse(st.test),allow=allow))
                    except ValueError as exc:issues.append(str(exc))
                elif code==401:
                    auth=True
                elif code!=404:issues.append('unknown_guard_effect')
            elif isinstance(st,(ast.For,ast.While,ast.Try,ast.With,ast.Match)):
                issues.append('unsupported_control_flow')
            elif isinstance(st,ast.Return):
                # A return before the last statement invalidates straight-line dominance.
                if st is not fn.body[-1]:issues.append('early_return')
            elif isinstance(st,ast.Raise):issues.append('unconditional_raise')
            for call in ast.walk(st):
                if isinstance(call,ast.Call) and not isinstance(call.func,ast.Name):
                    issues.append('unresolved_method_or_dynamic_call')
                if isinstance(call,ast.Call) and isinstance(call.func,ast.Name):
                    target=call.func.id
                    if target in functions:
                        params=[a.arg for a in functions[target].args.args]
                        if call.keywords or len(call.args)!=len(params) or any(not isinstance(a,ast.Name) or a.id!=p for a,p in zip(call.args,params)):
                            issues.append('unsupported_argument_binding')
                        if not isinstance(st,(ast.Expr,ast.Assign,ast.Return)):
                            issues.append('conditional_local_call')
                        else:visit(target)
                    elif target not in ('HTTPException',):issues.append('unresolved_call:'+target)
    visit(root)
    expr=conditions[0] if len(conditions)==1 else dict(op='and',args=conditions) if conditions else None
    return dict(conditions=expr,authentication=auth,evidence=evidence,issues=sorted(set(issues)),functions=sorted(seen))


def map_label(result, positive_public=False):
    if result['issues']:return 'manual_review_required','unsupported_or_incomplete_code'
    expr=result['conditions']
    if expr is None:
        if positive_public and not result['authentication']:return 'public','explicit_anonymous_evidence'
        return 'manual_review_required','no_supported_authorization_condition'
    if expr['op']=='atom' and expr['comparison']=='eq':
        return {'owner_equal':'owner_match','tenant_equal':'tenant_match','role':'role_required','subscription':'membership_required'}[expr['kind']], 'single_condition'
    if expr['op']=='or' and len(expr['args'])==2:
        atoms=expr['args']
        if all(a['op']=='atom' and a['comparison']=='eq' for a in atoms):
            if any(a['kind']=='owner_equal' for a in atoms) and any(a['kind']=='role' and a['value']=='admin' for a in atoms):
                return 'owner_or_admin','explicit_owner_or_admin'
    return 'manual_review_required','compound_or_unrepresentable_condition'
