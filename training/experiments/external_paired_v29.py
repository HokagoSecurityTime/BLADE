"""Frozen external paired evaluation. No changes to runtime or frozen test."""
from __future__ import annotations

import ast
import asyncio
import copy
import hashlib
import json
import os
from pathlib import Path
import random
import re
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'reports/eval/classification_quality/external_paired_v29'
RAW = ROOT / 'datasets/blade/raw/external_paired_v29'
PROMPT = ROOT / 'training/data/prompts/policy_label_v2.9.md'
GUARD = ROOT / 'training/experiments/application_guard.py'
REPO = 'fastapi/full-stack-fastapi-template'
COMMIT = 'b1125d8839482cb7bbae603ddc6d0081bf87532e'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value: object, *, frozen: bool = False) -> None:
    data = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    if frozen and path.exists():
        assert path.read_text(encoding='utf8') == data, str(path)
    else:
        path.write_text(data, encoding='utf8')


def freeze() -> None:
    save(OUT / 'protocol.json', dict(
        version='external-paired-v29-1', prompt_sha256=digest(PROMPT),
        guard_sha256=digest(GUARD), repository=REPO, commit=COMMIT,
        model='gpt-4o-mini', temperature=0, seed=42, repeats=1,
        conditions=['oas', 'oas_code'], selection='All operations in the pinned backend API routes; no outcome-based removal.',
        reference='Agent source review before model predictions; intended policy and implemented checks separate. Not human ground truth.',
        guard='Use frozen verifier on original source only. Unsupported external grammar stays unassessable; no fixture rewrite.',
        oas='Prefer repository OAS; otherwise generate a static operation projection from route declarations, docstrings and schema (not authorization implementation). Disclose provenance.',
        metrics=['reference agreement', 'macro-F1 over supported labels and all 7 labels', 'manual rate', 'latency', 'unsafe detection with evaluable denominator', 'correct proposal false-block rate', 'unassessable rate'],
        deployment=False, runtime_changes=False, training=False,
    ), frozen=True)


def collect() -> None:
    freeze()
    tree = json.load(urllib.request.urlopen(f'https://api.github.com/repos/{REPO}/git/trees/{COMMIT}?recursive=1'))
    selected = [r['path'] for r in tree['tree'] if r['type'] == 'blob' and
                ((r['path'].startswith('backend/') and r['path'].endswith(('.py', '.md', '.toml')))
                 or 'openapi' in r['path'].lower() and r['path'].endswith(('.json', '.yaml', '.yml'))
                 or r['path'] in ['README.md', 'LICENSE'])]
    files = []
    for name in selected:
        path = RAW / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            data = urllib.request.urlopen(f'https://raw.githubusercontent.com/{REPO}/{COMMIT}/{name}').read()
            path.write_bytes(data)
        files.append(dict(path=name, sha256=digest(path)))
    save(OUT/'sources.json', dict(repository=REPO, commit=COMMIT, files=files), frozen=True)
    print('Collected', len(files), 'files', flush=True)


def span(path: Path, start: int, end: int) -> dict:
    lines = path.read_text(encoding='utf8').splitlines()
    return dict(file=path.relative_to(RAW).as_posix(), start=start, end=end,
                code='\n'.join(lines[start-1:end]), sha256=digest(path))


def function_span(path: Path, name: str) -> dict:
    # Text boundaries preserve newer Python syntax without rewriting upstream files.
    lines = path.read_text(encoding='utf8').splitlines()
    start = next(i for i, line in enumerate(lines) if re.match(rf'(async )?def {name}\(', line))
    end = start + 1
    while end < len(lines):
        if re.match(r'^(?:async def |def |class |@|[A-Za-z_]\w*\s*(?:=|:))', lines[end]):
            break
        end += 1
    return span(path, start+1, end)


def functions(path: Path) -> dict:
    return {m.group(1): function_span(path, m.group(1)) for m in
            re.finditer(r'^(?:async )?def (\w+)\(', path.read_text(encoding='utf8'), re.M)}


def schema_fields(name: str, classes: dict, seen: set | None = None) -> list[str]:
    seen = set() if seen is None else set(seen)
    if name in seen or name not in classes:
        return []
    seen.add(name)
    node = classes[name]
    result = [n.target.id for n in node.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)]
    for base in node.bases:
        if isinstance(base, ast.Name): result += schema_fields(base.id, classes, seen)
    for n in node.body:
        if isinstance(n, ast.AnnAssign):
            for a in ast.walk(n.annotation):
                if isinstance(a, ast.Name) and a.id in classes:
                    result += schema_fields(a.id, classes, seen)
    return sorted(set(result))


# Source/test review fixed before model execution. Null means unresolved, not manual.
REFERENCES = {
    'items.read_items': (None, 'collection row filtering by owner OR superuser; endpoint-wide scalar policy unresolved'),
    'items.read_item': ('owner_or_admin', '403 unless superuser OR Item.owner_id equals current_user.id'),
    'items.create_item': (None, 'creator binding; no existing object access check'),
    'items.update_item': ('owner_or_admin', '403 unless superuser OR Item.owner_id equals current_user.id'),
    'items.delete_item': ('owner_or_admin', '403 unless superuser OR Item.owner_id equals current_user.id'),
    'users.read_users': ('role_required', 'route dependency get_current_active_superuser'),
    'users.create_user': ('role_required', 'route dependency get_current_active_superuser'),
    'users.update_user_me': ('owner_match', 'mutates authenticated current_user; own user docstring'),
    'users.update_password_me': ('owner_match', 'own password; old password verification is reauthentication'),
    'users.read_user_me': ('owner_match', 'returns authenticated current_user'),
    'users.delete_user_me': ('manual_review_required', 'self binding AND NOT superuser; independent negative-role restriction'),
    'users.register_user': ('public', 'explicit docstring without login; registration is authentication entry'),
    'users.read_user_by_id': ('owner_or_admin', 'same user early return, otherwise superuser required'),
    'users.update_user': ('role_required', 'route dependency get_current_active_superuser'),
    'users.delete_user': ('manual_review_required', 'superuser AND target user differs from caller'),
    'login.login_access_token': ('public', 'authentication entry, credential validation is not preexisting session authorization'),
    'login.test_token': ('owner_match', 'returns current authenticated user only'),
    'login.recover_password': ('public', 'unauthenticated recovery initiation; same generic response'),
    'login.reset_password': (None, 'reset token capability bound to email; mapping into six policies unresolved'),
    'login.recover_password_html_content': ('role_required', 'route dependency get_current_active_superuser'),
    'utils.test_email': ('role_required', 'route dependency get_current_active_superuser'),
    'utils.health_check': ('public', 'unconditional True; no route auth dependency'),
    'private.create_user': (None, 'development-only registration; intended deployment policy not established'),
}


def prepare() -> None:
    freeze()
    sources = json.loads((OUT/'sources.json').read_text(encoding='utf8'))
    assert all(digest(RAW/f['path']) == f['sha256'] for f in sources['files'])
    classes = {n.name: n for n in ast.parse((RAW/'backend/app/models.py').read_text(encoding='utf8')).body if isinstance(n, ast.ClassDef)}
    modules = {name: functions(RAW/f'backend/app/{name}.py') for name in ['crud', 'utils']}
    modules['security'] = functions(RAW/'backend/app/core/security.py')
    deps = RAW/'backend/app/api/deps.py'
    rows, references = [], []
    oas = dict(openapi='3.1.0', info=dict(title=REPO+' static projection', version=COMMIT), paths={},
               components=dict(securitySchemes=dict(OAuth2PasswordBearer=dict(type='oauth2', flows=dict(password=dict(tokenUrl='/api/v1/login/access-token', scopes={}))))),
               **{'x-provenance': 'Static route/schema projection; not a running application export; request/response schemas are field-name projections.'})
    for path in sorted((RAW/'backend/app/api/routes').glob('*.py')):
        tree = ast.parse(path.read_text(encoding='utf8'))
        prefix = ''
        for n in tree.body:
            if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call) and ast.unparse(n.value.func) == 'APIRouter':
                prefix = next((ast.literal_eval(k.value) for k in n.value.keywords if k.arg == 'prefix'), '')
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)): continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute) or dec.func.attr not in ['get','post','put','patch','delete']: continue
                ident = path.stem+'.'+node.name
                assert ident in REFERENCES
                url = '/api/v1'+prefix+ast.literal_eval(dec.args[0])
                method = dec.func.attr.upper()
                raw = function_span(path, node.name)
                decorator = ast.unparse(dec)
                has_super = 'get_current_active_superuser' in decorator
                requires_auth = has_super or any(a.annotation is not None and 'CurrentUser' in ast.unparse(a.annotation) for a in node.args.args+node.args.kwonlyargs)
                response = next((ast.unparse(k.value) for k in dec.keywords if k.arg == 'response_model'), ast.unparse(node.returns) if node.returns else '')
                fields = schema_fields(response, classes)[:40]
                path_params = re.findall(r'\{(\w+)\}', url)
                args = node.args.args+node.args.kwonlyargs
                query = [a.arg for a in args if a.arg not in path_params and a.annotation and ast.unparse(a.annotation) in ['int','str','EmailStr','bool']]
                operation = dict(operationId=ident, summary=node.name.replace('_',' ').title(), description=ast.get_docstring(node) or '',
                                 parameters=[dict(name=p, **{'in': 'path' if p in path_params else 'query'}, required=p in path_params, schema=dict(type='string')) for p in path_params+query],
                                 responses={'200':dict(description='Successful response',content={'application/json':dict(schema=dict(type='object',properties={f:{} for f in fields}))})})
                if requires_auth: operation['security']=[{'OAuth2PasswordBearer':[]}]
                # No invented explicit [] for endpoints whose generated spec omits security.
                payload = dict(method=method, path=url, path_params=path_params, query_params=query,
                               summary=operation['summary'], description=operation['description'],
                               security=operation.get('security'), security_state='declared' if requires_auth else 'unknown',
                               schema_fields=fields, owner_cols=[f for f in fields if f=='owner_id'], tenant_cols=[])
                oas['paths'].setdefault(url,{})[method.lower()] = operation
                refs = [span(path, min(d.lineno for d in node.decorator_list), node.end_lineno)]
                for context in ['backend/app/api/main.py','backend/app/main.py']:
                    context_path=RAW/context
                    refs.append(span(context_path,1,len(context_path.read_text(encoding='utf8').splitlines())))
                if requires_auth:
                    refs.append(function_span(deps,'get_current_user'))
                    # Alias and OAuth configuration, not unrelated handlers.
                    lines = deps.read_text(encoding='utf8').splitlines()
                    refs += [span(deps, i+1, i+1) for i,l in enumerate(lines) if l.startswith(('CurrentUser =','TokenDep ='))]
                    if has_super: refs.append(function_span(deps,'get_current_active_superuser'))
                if 'SessionDep' in raw['code']:
                    refs.append(function_span(deps,'get_db'))
                pending = [raw['code']]
                visited = set()
                while pending:
                    chunk = pending.pop()
                    for module, fns in modules.items():
                        for name, ref in fns.items():
                            pattern = rf'\b{module}\.{name}\(' if module != 'utils' else rf'(?<![\w.]){name}\('
                            if re.search(pattern,chunk) and (module,name) not in visited:
                                visited.add((module,name));refs.append(ref);pending.append(ref['code'])
                    # Calls between crud helpers and security utilities.
                    for module in ['crud','security']:
                        for name, ref in modules[module].items():
                            if re.search(rf'(?<![\w.]){name}\(',chunk) and (module,name) not in visited and not chunk.startswith('def '+name+'('):
                                visited.add((module,name));refs.append(ref);pending.append(ref['code'])
                relevant_classes = set()
                joined = '\n'.join(r['code'] for r in refs)
                for name in classes:
                    if re.search(rf'\b{name}\b',joined): relevant_classes.add(name)
                pending_classes = list(relevant_classes)
                while pending_classes:
                    n = classes[pending_classes.pop()]
                    for b in n.bases:
                        if isinstance(b,ast.Name) and b.id in classes and b.id not in relevant_classes:
                            relevant_classes.add(b.id);pending_classes.append(b.id)
                for name in sorted(relevant_classes):
                    n = classes[name]; refs.append(span(RAW/'backend/app/models.py',n.lineno,n.end_lineno))
                augmented = copy.deepcopy(payload)
                augmented['description'] += '\n\nSource evidence (original code, not policy annotations):\n'+'\n\n'.join(f"FILE {r['file']}:{r['start']}-{r['end']}\n{r['code']}" for r in refs)
                test_path = RAW/f'backend/tests/api/routes/test_{path.stem}.py'
                test_refs = []
                if test_path.exists():
                    # Store whole test-file provenance, never include tests in model inputs.
                    test_refs = [dict(file=test_path.relative_to(RAW).as_posix(),sha256=digest(test_path),execution='not run; static source evidence')]
                target, reason = REFERENCES[ident]
                references.append(dict(id=ident,reference_label=target,reference_status='agent_source_review' if target else 'unresolved',
                                       intended_policy=dict(explicit_text=operation['description'],label=None,status='docstring_only_not_independent_policy_spec'),
                                       implemented_check=reason,code_refs=refs,test_refs=test_refs,
                                       evidence_gaps=['No deployed end-to-end DB/JWT test','No independently human-confirmed intended policy'],
                                       development_only=path.stem=='private'))
                rows.append(dict(id=ident,service=REPO,method=method,path=url,inputs=dict(oas=payload,oas_code=augmented),
                                 raw_handler_source=raw['code'],requires_auth=requires_auth,has_super_dependency=has_super))
    assert set(r['id'] for r in rows) == set(REFERENCES)
    save(OUT/'openapi_projection.json',oas,frozen=True)
    save(OUT/'inputs.json',rows,frozen=True)
    save(OUT/'references.json',references,frozen=True)
    save(OUT/'prepared_manifest.json',dict(input_sha256=digest(OUT/'inputs.json'), reference_sha256=digest(OUT/'references.json'),
                                         oas_sha256=digest(OUT/'openapi_projection.json'),records=len(rows),frozen_before_model_execution=True),frozen=True)
    print('Prepared',len(rows),'operations',flush=True)


def harness() -> None:
    """Execute only reviewed functions, with local object/session doubles; no server or DB."""
    from types import SimpleNamespace as NS
    from fastapi import HTTPException

    def load(file: str, name: str, extra: dict | None = None):
        raw = function_span(RAW/file,name)
        fn = ast.parse(raw['code']).body[0]
        fn.decorator_list=[];fn.returns=None
        for arg in fn.args.args+fn.args.kwonlyargs: arg.annotation=None
        namespace={'HTTPException':HTTPException,'Item':object(),'User':object(),'Message':lambda **kw:NS(**kw)}
        namespace.update(extra or {})
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),file,'exec'),namespace)
        return namespace[name]

    class Object:
        def __init__(self, **kw): self.__dict__.update(kw)
        def sqlmodel_update(self, values): self.__dict__.update(values)

    class Session:
        def __init__(self,obj): self.obj=obj;self.lookups=[];self.writes=[]
        def get(self,model,key): self.lookups.append(str(key));return self.obj
        def add(self,obj): self.writes.append(('add',obj))
        def delete(self,obj): self.writes.append(('delete',obj))
        def commit(self): pass
        def refresh(self,obj): pass

    checks=[]
    for name in ['read_item','update_item','delete_item']:
        fn=load('backend/app/api/routes/items.py',name)
        for own in [False,True]:
            for admin in [False,True]:
                actor=Object(id='caller',is_superuser=admin)
                obj=Object(id='target',owner_id='caller' if own else 'other')
                session=Session(obj)
                kwargs=dict(session=session,current_user=actor,id='target')
                if name=='update_item':kwargs['item_in']=NS(model_dump=lambda **kw:{'title':'changed'})
                try:fn(**kwargs);status=200
                except HTTPException as exc:status=exc.status_code
                assert status==(200 if own or admin else 403)
                assert session.lookups==['target']
                assert status!=403 or not session.writes
                checks.append(dict(id='items.'+name,own=own,admin=admin,status=status,lookup='target',denied_writes=bool(session.writes) if status==403 else None))
    fn=load('backend/app/api/routes/users.py','read_user_by_id')
    for own in [False,True]:
        for admin in [False,True]:
            actor=Object(id='caller',is_superuser=admin)
            obj=actor if own else Object(id='other',is_superuser=False)
            session=Session(obj)
            try:fn(user_id=obj.id,session=session,current_user=actor);status=200
            except HTTPException as exc:status=exc.status_code
            assert status==(200 if own or admin else 403)
            checks.append(dict(id='users.read_user_by_id',own=own,admin=admin,status=status,lookup=obj.id))
    fn=load('backend/app/api/deps.py','get_current_active_superuser')
    for admin in [False,True]:
        try:fn(NS(is_superuser=admin));status=200
        except HTTPException as exc:status=exc.status_code
        assert status==(200 if admin else 403)
        checks.append(dict(id='dependency.get_current_active_superuser',admin=admin,status=status))
    for name in ['read_user_me','delete_user_me']:
        fn=load('backend/app/api/routes/users.py',name)
        for admin in [False,True]:
            actor=Object(id='caller',is_superuser=admin);session=Session(actor)
            try:
                result=fn(current_user=actor,**({'session':session} if name=='delete_user_me' else {}));status=200
                if name=='read_user_me':assert result is actor
            except HTTPException as exc:status=exc.status_code
            assert status==(403 if name=='delete_user_me' and admin else 200)
            if status==403:assert not session.writes
            checks.append(dict(id='users.'+name,admin=admin,status=status))
    save(OUT/'handler_checks.json',dict(checks=checks,passed=len(checks),scope='original function bodies; mocked session/model, authenticated caller supplied; not full HTTP/JWT/SQL integration'),frozen=True)
    print('Original handler/dependency checks:',len(checks),'passed',flush=True)


async def run() -> None:
    import httpx
    from contextvars import ContextVar
    from training.data.label import read_env
    from training.data.label_v6 import engine
    freeze()
    rows=json.loads((OUT/'inputs.json').read_text(encoding='utf8'))
    prepared=json.loads((OUT/'prepared_manifest.json').read_text(encoding='utf8'))
    assert prepared['input_sha256']==digest(OUT/'inputs.json')
    assert prepared['reference_sha256']==digest(OUT/'references.json')
    read_env(ROOT/'.env')
    assert os.getenv('BLADE_LABEL_PROVIDER','openai')=='openai'
    model=os.getenv('BLADE_LABEL_MODEL','gpt-4o-mini')
    assert model=='gpt-4o-mini'
    settings=engine.llm.Settings('openai',model,os.environ['OPENAI_API_KEY'])
    engine.VERSION='policy-label-v2.9'
    byid={c+':'+r['id']:r['inputs'][c] for r in rows for c in ['oas','oas_code']}
    engine.payload=lambda row:byid[row['id']]
    save(OUT/'execution_manifest.json',dict(**prepared,prompt_sha256=digest(PROMPT),guard_sha256=digest(GUARD),
         experiment_sha256=digest(Path(__file__)),model=model,temperature=0,seed=42,repeats=1),frozen=True)
    old=engine.read(OUT/'predictions.jsonl');done={r['id'] for r in old}
    assert len(done)==len(old) and done<=set(byid)
    jobs=[(c,r) for r in rows for c in ['oas','oas_code'] if c+':'+r['id'] not in done]
    random.Random(42).shuffle(jobs)
    keyvar=ContextVar('experiment_case',default=None)
    async def capture(response):
        await response.aread()
        if response.status_code==200:
            engine.append(OUT/'raw_responses.jsonl',dict(request_id=keyvar.get(),response=response.json()))
    semaphore=asyncio.Semaphore(4)
    async with httpx.AsyncClient(timeout=180,event_hooks={'response':[capture]}) as client:
        async def one(c,r):
            async with semaphore:
                key=c+':'+r['id'];keyvar.set(key);start=time.perf_counter()
                result=await engine.request(dict(id=key,service=r['service'],method=r['method'],path=r['path'],meta={}),PROMPT.read_text(encoding='utf8'),settings,client,OUT/'usage.jsonl')
                result.update(case_id=r['id'],condition=c,elapsed_ms=(time.perf_counter()-start)*1000)
                return result
        tasks=[asyncio.create_task(one(c,r)) for c,r in jobs]
        try:
            for task in asyncio.as_completed(tasks):
                result=await task
                engine.append(OUT/'predictions.jsonl',result);done.add(result['id'])
                print(len(done),'/',len(byid),result['id'],flush=True)
        finally:
            for task in tasks:
                if not task.done():task.cancel()
            await asyncio.gather(*tasks,return_exceptions=True)
    freeze()


def main(action: str) -> None:
    if action=='run':asyncio.run(run())
    else:{'collect':collect,'prepare':prepare,'harness':harness,'report':report}[action]()


def report() -> None:
    from collections import Counter
    from markdown_it import MarkdownIt
    from training.experiments.application_guard import verify, condition
    freeze()
    rows={r['id']:r for r in json.loads((OUT/'inputs.json').read_text(encoding='utf8'))}
    refs={r['id']:r for r in json.loads((OUT/'references.json').read_text(encoding='utf8'))}
    predictions=[json.loads(s) for s in (OUT/'predictions.jsonl').read_text(encoding='utf8').splitlines()]
    labels=['public','role_required','membership_required','tenant_match','owner_match','owner_or_admin','manual_review_required']
    decisions=[];metrics={}
    for pred in predictions:
        row=rows[pred['case_id']]
        # The frozen synthetic-only gate cannot prove external context/bindings.
        gate=verify(pred,row['raw_handler_source'],complete_context=False,fixture_bindings=False)
        try:condition(row['raw_handler_source']);parse_status='supported'
        except (ValueError,SyntaxError,TypeError):parse_status='unsupported_external_grammar'
        risk=None
        if pred['case_id'] in ['items.read_item','items.update_item','items.delete_item','users.read_user_by_id']:
            if pred.get('label') in ['public','tenant_match','membership_required']:
                risk=dict(kind='source_confirmed_broadening',witness='non-owner, non-superuser; independent tenant/group may match',scope='four handler boundaries tested with local doubles')
            elif pred.get('label') in ['owner_match','owner_or_admin']:
                risk=dict(kind='no_broadening_for_bound_owner_semantics',overrestriction=pred['label']=='owner_match')
        decisions.append(dict(id=pred['id'],original_prediction=pred,guard=gate,parser_status=parse_status,independent_risk_audit=risk))
    save(OUT/'guard_decisions.json',decisions)
    for c in ['oas','oas_code']:
        selected=[p for p in predictions if p['condition']==c]
        assert len(selected)==len(rows)
        scored=[p for p in selected if refs[p['case_id']]['reference_label'] is not None]
        correct=sum(p.get('label')==refs[p['case_id']]['reference_label'] for p in scored)
        matrix={k:{j:0 for j in labels+['output_error']} for k in labels}
        for p in scored:
            matrix[refs[p['case_id']]['reference_label']][p.get('label') if p.get('label') in labels else 'output_error']+=1
        per={}
        for label in labels:
            tp=matrix[label][label];actual=sum(matrix[label].values());chosen=sum(matrix[k][label] for k in labels)
            precision=tp/chosen if chosen else 0;recall=tp/actual if actual else 0
            per[label]=dict(support=actual,precision=precision,recall=recall,f1=2*precision*recall/(precision+recall) if precision+recall else 0)
        supported=[v['f1'] for v in per.values() if v['support']]
        concrete_correct=[p for p in scored if p['label']==refs[p['case_id']]['reference_label'] and p['label']!='manual_review_required']
        ds=[d for d in decisions if d['original_prediction']['condition']==c]
        unsafe=[d for d in ds if (d['independent_risk_audit'] or {}).get('kind')=='source_confirmed_broadening']
        metrics[c]=dict(total=len(selected),reference_evaluable=len(scored),reference_unresolved=len(selected)-len(scored),
                        accuracy=correct/len(scored),correct=correct,macro_f1_7=sum(v['f1'] for v in per.values())/7,
                        macro_f1_supported=sum(supported)/len(supported),per_label=per,confusion_matrix=matrix,
                        label_counts=dict(Counter(p.get('label') for p in selected)),manual_rate=sum(p.get('label')=='manual_review_required' for p in selected)/len(selected),
                        output_errors=sum(p.get('label') not in labels for p in selected),mean_ms=sum(p['elapsed_ms'] for p in selected)/len(selected),
                        guard_evaluable=0,guard_unassessable=len(ds),guard_unassessable_rate=1.0,
                        supported_domain_false_block_rate=None,correct_concrete_held=len(concrete_correct),correct_concrete=len(concrete_correct),
                        operational_correct_proposal_hold_rate=1.0 if concrete_correct else None,
                        independently_confirmed_unsafe=len(unsafe),specific_unsafe_detection=0,
                        specific_unsafe_detection_rate=0.0 if unsafe else None,
                        unsafe_auto_apply_blocked=len(unsafe),auto_apply_allowed=0)
    save(OUT/'metrics.json',metrics)
    usage=[json.loads(s) for s in (OUT/'usage.jsonl').read_text(encoding='utf8').splitlines()]
    usage_summary=dict(responses=len(usage),input_tokens=sum(x['usage'].get('input_tokens',x['usage'].get('prompt_tokens',0)) for x in usage),output_tokens=sum(x['usage'].get('output_tokens',x['usage'].get('completion_tokens',0)) for x in usage))
    save(OUT/'usage_summary.json',usage_summary)
    text='# v2.9 고정 · 새 외부 프로젝트 OAS/코드 비교\n\n'
    text+='**새 프로젝트 1개, 엔드포인트 23개를 두 입력 조건으로 실행했다. 분류 결과와 적용 검증 결과를 분리했다. 고정 검증기는 외부 코드·바인딩을 지원하지 않아 23/23건 평가 불가이며, 모두 적용 보류다. 이는 위험 탐지 성공률 100%를 뜻하지 않는다.**\n\n'
    text+=f'출처: [{REPO}](https://github.com/{REPO}/tree/{COMMIT}). 이전 실험 수집 manifest/스크립트 검색에서 이 프로젝트 사용 기록이 없었다. 같은 프레임워크 일반화 검증이며, 다중 프로젝트·6종 전체 평가가 아니다.\n\n'
    text+='## 고정 조건\n\nv2.9 프롬프트·application_guard.py 해시는 수집 전에 protocol.json에 고정했다. 모델 gpt-4o-mini, temperature 0, seed 42, 조건별 1회, 동시 요청 4개다. 대상 ID·입력·에이전트 참조 라벨은 API 실행 전에 해시로 고정했다. 조건별 ID는 같다. 원시 응답과 원래 라벨을 보존했다.\n\n'
    text+='저장소에 OpenAPI 파일이 없어 라우트 선언·docstring·응답 필드로 만든 **정적 OAS 투영본**을 사용했다. 실제 서버 export와 동일하다고 주장하지 않는다. 타입/본문 스키마는 완전하지 않다. 익명 경로에 임의 security: []를 추가하지 않았으며, 인증 없는 경로의 security_state는 unknown이다. 코드 조건에는 실제 핸들러·참조 함수·모델·라우터 등록과 전역 middleware를 추가했다. 정답·검수 설명·테스트 코드는 모델 입력에 넣지 않았다. private 경로 1개는 개발 환경 전용임을 기록했다.\n\n'
    text+='## 분류 결과 — 사람 정답 정확도가 아닌 코드 검토 참조 일치율\n\n의도된 정책 원문, 구현 검사, 근거 확보 여부를 references.json에 분리했다. 독립 명시 정책이 부족하므로 의도 라벨은 확정하지 않았다. 평가 가능한 19건의 라벨은 에이전트의 소스·테스트 검토 참조이며, 미확정 4건을 manual 정답으로 채우지 않았다.\n\n| 입력 | 참조 일치 | macro-F1(지원 라벨) | macro-F1(7종) | 모델 보류 | 평균 ms |\n|---|---:|---:|---:|---:|---:|\n'
    for c,m in metrics.items():
        text+=f"| {c} | {m['correct']}/{m['reference_evaluable']} ({m['accuracy']:.1%}) | {m['macro_f1_supported']:.4f} | {m['macro_f1_7']:.4f} | {m['manual_rate']:.1%} | {m['mean_ms']:.0f} |\n"
    text+='\n분모에서 빠진 4건은 목록 행 필터링, 새 객체 생성, reset-token capability, 개발 전용 등록이다. tenant/membership 정답 사례가 없어 이 두 라벨의 성능은 측정할 수 없다. 지원 라벨 macro-F1은 참조 support가 있는 5종 평균이며, 7종 평균에서는 support 없는 라벨 F1을 0으로 둔다.\n\n'
    for c,m in metrics.items():
        text+=f'### {c}: 라벨별 지표\n\n| 라벨 | support | P | R | F1 |\n|---|---:|---:|---:|---:|\n'
        for label,v in m['per_label'].items():text+=f"| {label} | {v['support']} | {v['precision']:.3f} | {v['recall']:.3f} | {v['f1']:.3f} |\n"
        text+='\n혼동행렬(행=참조, 열=예측):\n\n| 참조 / 예측 | '+' | '.join(labels+['output_error'])+' |\n|---|'+'---:|'*8+'\n'
        for label,v in m['confusion_matrix'].items():text+='| '+label+' | '+' | '.join(str(v[k]) for k in labels+['output_error'])+' |\n'
    text+='\n## 검증기 결과\n\n| 입력 | 평가 불가 | 올바른 구체 제안도 보류 | 별도 소스 감사에서 허용 확대 | 검증기의 구체 누락 탐지 | 자동 적용 |\n|---|---:|---:|---:|---:|---:|\n'
    for c,m in metrics.items():
        text+=f"| {c} | {m['guard_unassessable']}/{m['total']} | {m['correct_concrete_held']}/{m['correct_concrete']} | {m['independently_confirmed_unsafe']} | 0/{m['independently_confirmed_unsafe']} | 0 |\n"
    text+='\n0/0은 N/A다. 지원 영역에서의 오차단율은 지원 표본 0건이므로 N/A다. 운영 관점에서는 올바른 구체 제안도 모두 보류되는 적용 손실이 있다. 허용 확대 보조 감사는 실제 핸들러 본문 검증을 수행한 item 조회·수정·삭제와 user-by-id 4개 경계에 한정한다. public/tenant/membership 제안이 비소유자·비관리자를 허용할 수 있는 반례를 확인한다. 특정 역할 바인딩 없는 role_required 등의 안전성을 추정하지 않는다. 나머지 경로의 위험 검출률로 일반화하지 않는다. 모든 요청 보류를 특정 필수 조건 누락 탐지로 세지 않았다.\n\n'
    checks=json.loads((OUT/'handler_checks.json').read_text(encoding='utf8'))
    text+=f"## 검증 범위\n\n원본 함수 본문을 사용한 로컬 handler/dependency 검사 {checks['passed']}건 통과. DB 세션·객체는 대역이며 로그인/JWT/PostgreSQL/전체 HTTP 통합 검증이 아니다. 원본 upstream 테스트는 수집·정적으로 확인했지만 실행하지 않았다. 런타임·기존 test·train은 수정하지 않았다.\n\n"
    text+='## 전체 결과\n\n| ID | 참조 | OAS | OAS+코드 | 근거 상태 |\n|---|---|---|---|---|\n'
    by={(p['condition'],p['case_id']):p for p in predictions}
    for ident,ref in refs.items():text+=f"| {ident} | {ref['reference_label'] or '미확정'} | {by['oas',ident].get('label')} | {by['oas_code',ident].get('label')} | {ref['reference_status']} |\n"
    text+=f"\nAPI 응답 {usage_summary['responses']}회, 입력 {usage_summary['input_tokens']:,}토큰, 출력 {usage_summary['output_tokens']:,}토큰. 실제 결제 금액은 이 보고서에서 추정하지 않았다.\n\n"
    text+='## 판단\n\n현재 고정 검증기는 외부 환경에 바로 적용할 수 없다. 안전하게 보류하지만 활용률이 0이다. 다음 개발 과제는 원래 코드→조건/객체 바인딩 어댑터이며, 이 데이터는 이후 어댑터 개발에 쓰면 개발셋으로 취급해야 한다. 프롬프트와 검증기를 결과에 맞춰 이번 실행 도중 고치지 않았다. 새 어댑터의 효과는 별도 버전과 다른 프로젝트로 측정해야 한다.\n\n원자료: inputs.json, references.json, handler_checks.json, raw_responses.jsonl, predictions.jsonl, guard_decisions.json, metrics.json, protocol.json, execution_manifest.json.\n'
    (OUT/'report.md').write_text(text,encoding='utf8')
    body=MarkdownIt().enable('table').render(text)
    (OUT/'report.htm').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>v2.9 외부 비교 실험</title><style>body{max-width:1400px;margin:32px auto;padding:20px;font:16px/1.7 system-ui}table{border-collapse:collapse;font-size:13px}th,td{border:1px solid #bbb;padding:7px}h1,h2{color:#16345a}</style>'+body+'</html>',encoding='utf8')
    assert digest(ROOT/'datasets/blade/processed/test.jsonl')=='bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa'
    print(json.dumps({c:{k:m[k] for k in ['correct','reference_evaluable','macro_f1_supported','guard_unassessable','independently_confirmed_unsafe']} for c,m in metrics.items()},indent=2))


if __name__ == '__main__':
    import sys
    main(sys.argv[1] if len(sys.argv)>1 else 'collect')
