"""Static cross-module FastAPI guard adapter, isolated from the runtime.

Extracts supported dependency conditions, never claims whole-route completeness.
No upstream modules are imported or executed by this extractor.
"""
from __future__ import annotations
import ast
import hashlib
from pathlib import Path


class Unsupported(ValueError):
    pass


class Adapter:
    def __init__(self, root: Path):
        self.root=root.resolve()
        self.modules={}

    def module(self, path):
        path=Path(path).resolve()
        if not path.is_relative_to(self.root):raise Unsupported('path_outside_source_root')
        if path not in self.modules:
            tree=ast.parse(path.read_text(encoding='utf8'))
            funcs={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
            imports={}
            for n in tree.body:
                if isinstance(n,ast.ImportFrom) and n.level==0 and n.module:
                    for a in n.names:imports[a.asname or a.name]=(n.module,a.name)
            self.modules[path]=(tree,funcs,imports)
        return self.modules[path]

    def resolve(self,path,name):
        _,funcs,imports=self.module(path)
        if name in funcs:return Path(path),funcs[name]
        if name not in imports:raise Unsupported('symbol_unresolved:'+name)
        module,symbol=imports[name]
        target=self.root.joinpath(*module.split('.')).with_suffix('.py')
        if not target.is_file():raise Unsupported('import_module_unresolved:'+module)
        _,funcs,_=self.module(target)
        if symbol not in funcs:raise Unsupported('import_function_unresolved:'+symbol)
        return target,funcs[symbol]

    def ref(self,path,node):
        path=Path(path);lines=path.read_text(encoding='utf8').splitlines()
        start=min([node.lineno]+[d.lineno for d in getattr(node,'decorator_list',[])])
        return dict(path=path.relative_to(self.root).as_posix(),start=start,end=node.end_lineno,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            code='\n'.join(f'{i}: {lines[i-1]}' for i in range(start,node.end_lineno+1)))

    @staticmethod
    def dependency_nodes(fn):
        defaults=[*fn.args.defaults,*[x for x in fn.args.kw_defaults if x is not None]]
        for d in fn.decorator_list:
            if isinstance(d,ast.Call):
                for k in d.keywords:
                    if k.arg=='dependencies' and isinstance(k.value,(ast.List,ast.Tuple)):defaults.extend(k.value.elts)
        return [n for n in defaults if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Depends']

    @staticmethod
    def attr(node):
        parts=[]
        while isinstance(node,ast.Attribute):parts.insert(0,node.attr);node=node.value
        if not isinstance(node,ast.Name):raise Unsupported('not_static_attribute_path')
        return [node.id,*parts]

    def predicate(self,path,fn,call):
        if fn.decorator_list or len(fn.body)!=1 or not isinstance(fn.body[0],ast.Return):raise Unsupported('predicate_not_pure_return')
        params=[a.arg for a in fn.args.args]
        if call.keywords or len(params)!=len(call.args):raise Unsupported('predicate_argument_binding')
        binding={p:self.attr(a) for p,a in zip(params,call.args)}
        def operand(n):
            fields=self.attr(n)
            if fields[0] not in binding:raise Unsupported('unbound_predicate_parameter')
            return binding[fields[0]]+fields[1:]
        def expr(n):
            if isinstance(n,ast.BoolOp):return dict(op='and' if isinstance(n.op,ast.And) else 'or',args=[expr(x) for x in n.values])
            if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.Not):return dict(op='not',arg=expr(n.operand))
            if isinstance(n,ast.Compare) and len(n.ops)==1 and isinstance(n.ops[0],(ast.Eq,ast.NotEq)):
                return dict(op='eq' if isinstance(n.ops[0],ast.Eq) else 'ne',left=operand(n.left),right=operand(n.comparators[0]))
            raise Unsupported('unsupported_predicate_expression')
        return expr(fn.body[0].value)

    def guard(self,path,fn):
        if fn.decorator_list or len(fn.body)!=1 or not isinstance(fn.body[0],ast.If):raise Unsupported('not_single_rejection_guard')
        branch=fn.body[0]
        if branch.orelse or len(branch.body)!=1 or not isinstance(branch.body[0],ast.Raise):raise Unsupported('unsupported_guard_branch')
        rejection=branch.body[0].exc
        if not isinstance(rejection,ast.Call) or not isinstance(rejection.func,ast.Name) or rejection.func.id!='HTTPException':raise Unsupported('not_HTTPException')
        imports=self.module(path)[2]
        if imports.get('HTTPException')!=('fastapi','HTTPException'):raise Unsupported('HTTPException_origin_unverified')
        status=next((k.value for k in rejection.keywords if k.arg=='status_code'),rejection.args[0] if rejection.args else None)
        literal=isinstance(status,ast.Constant) and status.value==403
        symbolic=isinstance(status,ast.Attribute) and isinstance(status.value,ast.Name) and status.value.id=='status' and status.attr=='HTTP_403_FORBIDDEN' and imports.get('status')==('starlette','status')
        if not (literal or symbolic):raise Unsupported('not_verified_403')
        test=branch.test
        if not isinstance(test,ast.UnaryOp) or not isinstance(test.op,ast.Not) or not isinstance(test.operand,ast.Call) or not isinstance(test.operand.func,ast.Name):raise Unsupported('guard_not_negated_predicate')
        call=test.operand; pp,pf=self.resolve(path,call.func.id)
        condition=self.predicate(pp,pf,call)
        # Follow parameter provenance: User comes from current-user dependency.
        # The external factory is NOT resolved for whole-route completeness.
        parameters=[*fn.args.posonlyargs,*fn.args.args]
        defaults=[None]*(len(parameters)-len(fn.args.defaults))+list(fn.args.defaults)
        callers=[]
        for arg,default in zip(parameters,defaults):
            if not isinstance(default,ast.Call) or not isinstance(default.func,ast.Name) or default.func.id!='Depends' or not default.args:continue
            factory=default.args[0]
            if isinstance(factory,ast.Call):
                name=ast.unparse(factory.func)
                if name in ('get_current_user_authorizer','authentication.get_current_user_authorizer'):
                    if name=='get_current_user_authorizer' and imports.get(name)!=('app.api.dependencies.authentication',name):continue
                    if name.startswith('authentication.') and imports.get('authentication')!=('app.api.dependencies','authentication'):continue
                    callers.append(arg.arg)
        label=None
        if condition['op']=='eq':
            a,b=condition['left'],condition['right']
            for actor,resource in [(a,b),(b,a)]:
                if len(actor)==2 and actor[0] in callers and actor[1]=='username' and len(resource)==3 and resource[1:]==['author','username'] and resource[0]!=actor[0]:label='owner_match'
        return dict(condition=condition,condition_label_proposal=label,
            mapping_basis='requester username equals resource author username; same-source tests must corroborate semantics',
            chain=[fn.name,pf.name],guard_ref=self.ref(path,fn),predicate_ref=self.ref(pp,pf),
            unresolved=['authentication factory behavior','object lookup provenance beyond dependency declaration'])

    def route(self,path,fn):
        guards=[];unresolved=[]
        for dep in self.dependency_nodes(fn):
            if len(dep.args)!=1 or not isinstance(dep.args[0],ast.Name):
                unresolved.append('dynamic_dependency:'+ast.unparse(dep));continue
            try:
                p,f=self.resolve(path,dep.args[0].id)
                guards.append(self.guard(p,f))
            except (Unsupported,OSError) as exc:unresolved.append(str(exc))
        return dict(handler=fn.name,route_ref=self.ref(path,fn),guards=guards,
            combined_condition=dict(op='and',args=[g['condition'] for g in guards]) if guards else None,
            endpoint_final_label=None,unresolved=unresolved+['full handler effects and deployment middleware not analyzed'])


def evaluate(expr,bindings):
    def read(path):
        obj=bindings[path[0]]
        for part in path[1:]:obj=getattr(obj,part)
        return obj
    if expr['op']=='and':return all(evaluate(x,bindings) for x in expr['args'])
    if expr['op']=='or':return any(evaluate(x,bindings) for x in expr['args'])
    if expr['op']=='not':return not evaluate(expr['arg'],bindings)
    same=read(expr['left'])==read(expr['right'])
    return same if expr['op']=='eq' else not same
