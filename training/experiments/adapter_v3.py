"""Static necessary-condition evidence; unknown remainder never means approval."""
from __future__ import annotations
import ast
import hashlib
import re
from pathlib import Path

class IntegrityError(RuntimeError):
    pass

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_verified(path: Path, expected: dict[str,str], root: Path) -> str:
    key=path.relative_to(root).as_posix()
    if key not in expected or sha(path)!=expected[key]:raise IntegrityError('unverified source: '+key)
    return path.read_text(encoding='utf8')


def definition(text: str, name: str) -> tuple[str,int]:
    lines=text.splitlines()
    found=[i for i,l in enumerate(lines) if re.match(rf'^(?:async )?def {re.escape(name)}\(',l)]
    if len(found)!=1:raise ValueError('unresolved definition')
    start=found[0];end=start+1
    while end<len(lines) and not re.match(r'^(?:def |async def |class |@|[A-Za-z_]\w*\s*(?:=|:))',lines[end]):end+=1
    return '\n'.join(lines[start:end]),start+1


def analyze(root: Path, file: str, handler: str, hashes: dict[str,str]) -> dict:
    path=root/file;text=read_verified(path,hashes,root)
    tree=ast.parse(text)
    functions=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==handler]
    if len(functions)!=1:raise ValueError('ambiguous handler')
    fn=functions[0];evidence=[];necessary=[]
    imports={}
    for n in tree.body:
        if isinstance(n,ast.ImportFrom) and n.module and not n.level:
            for a in n.names:imports[a.asname or a.name]=(n.module,a.name)
    def resolve(name: str) -> tuple[str,dict]:
        if name in imports:
            module,original=imports[name]
            suffix=module.replace('.','/')+'.py'
            candidates=[k for k in hashes if k==suffix or k.endswith('/'+suffix)]
            if len(candidates)!=1:raise ValueError('module not unique')
            target=root/candidates[0];value=read_verified(target,hashes,root)
            source,line=definition(value,original)
            return source,dict(file=candidates[0],line=line,sha256=hashes[candidates[0]])
        source,line=definition(text,name)
        return source,dict(file=file,line=line,sha256=hashes[file])
    dependencies=[]
    for d in fn.decorator_list:
        for n in ast.walk(d):
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Depends' and n.args and isinstance(n.args[0],ast.Name):dependencies.append(n.args[0].id)
    for a in fn.args.defaults+fn.args.kw_defaults:
        if isinstance(a,ast.Call) and isinstance(a.func,ast.Name) and a.func.id=='Depends' and a.args and isinstance(a.args[0],ast.Name):dependencies.append(a.args[0].id)
    unresolved=[]
    for name in sorted(set(dependencies)):
        try:
            source,ref=resolve(name);dep=ast.parse(source).body[0]
            body=[n for n in dep.body if not isinstance(n,ast.Expr)]
            # A complete pure guard dependency: if not user.is_superuser: raise 403; return user.
            if len(body)!=2 or not isinstance(body[0],ast.If) or not isinstance(body[1],ast.Return):raise ValueError('not a pure guard')
            branch=body[0]
            if branch.orelse or len(branch.body)!=1 or not isinstance(branch.body[0],ast.Raise):raise ValueError('complex guard')
            test=branch.test
            if not isinstance(test,ast.UnaryOp) or not isinstance(test.op,ast.Not) or not isinstance(test.operand,ast.Attribute) or test.operand.attr!='is_superuser':raise ValueError('unknown role predicate')
            receiver=ast.unparse(test.operand.value)
            if receiver not in [a.arg for a in dep.args.args] or ast.unparse(body[1].value)!=receiver:raise ValueError('unbound principal')
            call=branch.body[0].exc
            if not isinstance(call,ast.Call) or ast.unparse(call.func)!='HTTPException' or not any(k.arg=='status_code' and isinstance(k.value,ast.Constant) and k.value.value in [403,404] for k in call.keywords):raise ValueError('unknown denial')
            necessary.append('admin');evidence.append(dict(kind='required_role',dependency=name,condition=receiver+'.is_superuser',**ref))
        except (ValueError,SyntaxError) as exc:unresolved.append(dict(dependency=name,reason=str(exc)))
    for n in ast.walk(fn):
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='where':
            evidence.append(dict(kind='orm_filter_candidate',expression=ast.unparse(n),file=file,line=n.lineno,verified_semantics=False))
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='get' and len(n.args)==2:
            evidence.append(dict(kind='lookup_candidate',expression=ast.unparse(n),file=file,line=n.lineno,verified_semantics=False))
        if isinstance(n,ast.Return) and isinstance(n.value,ast.Name):
            args=fn.args.args+fn.args.kwonlyargs
            a=next((a for a in args if a.arg==n.value.id),None)
            if a is not None:evidence.append(dict(kind='returned_parameter_binding',parameter=a.arg,annotation=ast.unparse(a.annotation) if a.annotation else None,file=file,line=n.lineno,authenticated_identity_verified=False))
    return dict(status='necessary_condition_only' if necessary else 'unresolved',necessary_conditions=sorted(set(necessary)),evidence=evidence,
                unresolved_dependencies=unresolved,complete_context=False,auto_apply_allowed=False,
                limitation='Only proven necessary dependency guards; ORM filters and identity are candidate evidence, not complete policy.')


def verify(prediction: dict, extracted: dict) -> dict:
    label=prediction.get('label')
    result=dict(original_label=label,original_confidence=prediction.get('confidence'),auto_apply_allowed=False,semantic_candidate_pass=False)
    if 'admin' in extracted['necessary_conditions'] and label in ['public','owner_match','owner_or_admin','membership_required','tenant_match']:
        return dict(result,reason='violates_proven_necessary_condition',counterexample=dict(admin=False,owner=True,member=True,tenant=True))
    return dict(result,reason='incomplete_context_or_binding')
