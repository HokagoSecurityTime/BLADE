"""Capture full HTTP exchanges for the requested presentation verification."""
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import time

import httpx
import jwt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'verification'
checks=[]
issues=[]
client=httpx.Client(timeout=15,trust_env=False)
for line in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines():
    if line.startswith(('BLADE_JWT_SECRET=','BLADE_POLICY_POLL_SEC=')):
        key,value=line.split('=',1);os.environ[key]=value.strip().strip('"').strip("'")


def check(name: str, expected: str, actual: str, passed: bool, cause: str = '') -> None:
    checks.append(dict(item=name,expected=expected,actual=actual,status='PASS' if passed else 'FAIL'))
    if not passed: issues.append(f'- {name}: {cause or actual}')
    (OUT/'presentation-progress.json').write_text(json.dumps(checks,indent=2,ensure_ascii=False),encoding='utf-8')
    print(f'{name}: {"PASS" if passed else "FAIL"} {actual}',flush=True)


def exchange(file: str, method: str, url: str, **kwargs: object) -> httpx.Response:
    request=client.build_request(method,url,**kwargs)
    body=request.read()
    prefix=f'\n===== {datetime.now(timezone.utc).isoformat()} REQUEST =====\n{method} {request.url.raw_path.decode()} HTTP/1.1\n'
    prefix+='\n'.join(k.decode()+': '+v.decode() for k,v in request.headers.raw)+'\n\n'
    with (OUT/file).open('ab') as stream:
        stream.write(prefix.encode()+body+b'\n')
        try: response=client.send(request)
        except httpx.HTTPError as exc:
            stream.write(f'\nNO HTTP RESPONSE: {type(exc).__name__}\n'.encode())
            raise
        suffix=f'\n===== RESPONSE =====\n{response.http_version} {response.status_code} {response.reason_phrase}\n'
        suffix+='\n'.join(k.decode()+': '+v.decode() for k,v in response.headers.raw)+'\n\n'
        stream.write(suffix.encode()+response.content+b'\n')
    return response


def capture_logs(file: str, ids: set[str], verdict: str) -> tuple[httpx.Response,bool]:
    deadline=time.monotonic()+10
    while True:
        response=exchange(file,'GET','http://127.0.0.1:8100/detections?limit=100')
        data=response.json() if response.status_code==200 else []
        found={r['request_id'] for r in data if r['verdict']==verdict}
        if ids<=found:return response,True
        if time.monotonic()>=deadline:return response,False
        time.sleep(.25)


def main() -> None:
    ready=True
    for port in (9000,8100,8080):
        deadline=time.monotonic()+30
        while True:
            try:
                with socket.create_connection(('127.0.0.1',port),timeout=1):break
            except OSError:
                if time.monotonic()>=deadline:ready=False;break
                time.sleep(.2)
    logs_exist=all((OUT/'logs'/f'{n}.log').exists() for n in ('demo_backend','admin_api','proxy'))
    check('services','9000/8100/8080 listening; stdout/stderr logs',f'ready={ready}, logs={logs_exist}',ready and logs_exist)
    expires=int(time.time())+172800
    def token(user: str) -> str:
        return jwt.encode(dict(sub=user,roles=['user'],tenant_id='org_2' if user=='user_99' else 'org_1',membership='basic',exp=expires),os.environ['BLADE_JWT_SECRET'],algorithm='HS256')
    t99,t77=token('user_99'),token('user_77')
    parts=t99.split('.')
    payload=json.loads(base64.urlsafe_b64decode(parts[1]+'='*(-len(parts[1])%4)))
    payload['sub']='user_77'
    encoded=base64.urlsafe_b64encode(json.dumps(payload,separators=(',',':')).encode()).decode().rstrip('=')
    forged=parts[0]+'.'+encoded+'.'+parts[2]
    commands=f'''# Presentation commands — Git Bash

Run from `C:/BLADE`. Services are already running on ports 9000/8100/8080.
Tokens expire at {datetime.fromtimestamp(expires,timezone.utc).isoformat()} (UTC).
These are local demo tokens, not API keys.

```bash
cd /c/BLADE
TOKEN99='{t99}'
TOKEN77='{t77}'
FORGED='{forged}'
```

## Step 1 (already executed)

The current store contains the generated policies. Repeating /generate will return 409;
this command records the original operation, not a reset command. Start at step 3 for recording.

```bash
curl -i -X POST http://localhost:8100/generate -F oas=@demo_backend/openapi.json -F erd=@demo_backend/schema.sql
```
'''
    (OUT/'COMMANDS.md').write_text(commands,encoding='utf-8')
    print('Starting actual LLM generation (sequential endpoints)...',flush=True)
    files={key:(filename,(ROOT/'demo_backend'/filename).read_bytes()) for key,filename in [('oas','openapi.json'),('erd','schema.sql')]}
    response=exchange('step1_generate.txt','POST','http://127.0.0.1:8100/generate',files=files,timeout=1500)
    policies=response.json() if response.status_code==200 and isinstance(response.json(),list) else []
    check('step1','7 PENDING policies',f'HTTP {response.status_code}; policies={len(policies)}',len(policies)==7 and all(p['status']=='PENDING' for p in policies),'Generation/provider failure or nonempty store; see step1 response.')
    table='| id | label |\n|---|---|\n'+'\n'.join(f'| {p["id"]} | {p["label"]} |' for p in policies)+'\n'
    (OUT/'step1_policies.md').write_text(table,encoding='utf-8')
    approve_codes=[]
    commands+='\n## Step 2 (already approved; repeated approval returns 409)\n\n```bash\n'
    for policy in policies:
        url='http://127.0.0.1:8100/policies/'+policy['id']+'/approve'
        approve_codes.append(exchange('step2_approve.txt','POST',url).status_code)
        commands+=f'curl -i -X POST http://localhost:8100/policies/{policy["id"]}/approve\n'
    response=exchange('step2_approve.txt','GET','http://127.0.0.1:8100/policies?status=ACTIVE')
    active=response.json() if response.status_code==200 else []
    check('step2','7 approvals HTTP 200; ACTIVE list has 7',f'approvals={approve_codes}; ACTIVE={len(active)}',len(active)==7 and len(approve_codes)==7 and all(c==200 for c in approve_codes),'Approval/state transition or generation failure.')
    commands+='curl -i "http://localhost:8100/policies?status=ACTIVE"\n```\n'
    time.sleep(float(os.getenv('BLADE_POLICY_POLL_SEC','5'))+1)
    base='http://127.0.0.1:8080'
    h99={'Authorization':'Bearer '+t99};h77={'Authorization':'Bearer '+t77}
    backend=OUT/'logs/demo_backend.log'
    before=backend.read_bytes().splitlines()
    response3=exchange('step3_other_owner.txt','GET',base+'/orders/1042',headers=h99)
    time.sleep(.4)
    after=backend.read_bytes().splitlines()
    extra=after[len(before):]
    (OUT/'step3_backend_untouched.txt').write_bytes(
        f'before_lines={len(before)}\nafter_lines={len(after)}\ndelta={len(after)-len(before)}\nstep3_status={response3.status_code}\n'
        .encode()+b'New lines (verbatim):\n'+b'\n'.join(extra)+b'\n')
    check('step3','user_99 GET -> 403',str(response3.status_code),response3.status_code==403,'Policy may not enforce owner_match or lookup failed open.')
    check('backend_untouched','step3 403; backend log line delta=0',f'HTTP {response3.status_code}; {len(before)} -> {len(after)} lines',response3.status_code==403 and len(before)==len(after),'Backend access log changed during blocked request; inspect appended lines.')
    response4=exchange('step4_owner.txt','GET',base+'/orders/1042',headers=h77)
    check('step4','user_77 GET -> 200',str(response4.status_code),response4.status_code==200,'Owner lookup, seed data, or generated policy mismatch.')
    response5=exchange('step5_delete.txt','DELETE',base+'/orders/1042',headers=h99)
    preserved=exchange('step5_delete.txt','GET',base+'/orders/1042',headers=h77)
    check('step5','DELETE 403; owner GET 200',f'{response5.status_code}; {preserved.status_code}',response5.status_code==403 and preserved.status_code==200,'DELETE policy enforcement or order preservation failure.')
    response6=exchange('step6_no_token.txt','GET',base+'/orders/1042')
    check('step6','no Authorization -> 403',str(response6.status_code),response6.status_code==403,'Missing-token policy enforcement failure.')
    ids={r.headers.get('X-Blade-Request-Id','missing') for r in (response3,response5,response6)}
    response7,matched=capture_logs('step7_detections.txt',ids,'BLOCK')
    count=sum(r['verdict']=='BLOCK' for r in response7.json()) if response7.status_code==200 else 0
    check('step7','BLOCK >=3; step3/5/6 request IDs match',f'BLOCK={count}; matched={matched}',count>=3 and matched,'Asynchronous log delivery or incorrect verdict.')
    broken=exchange('break1.txt','GET',base+'/orders/1042',headers={'Authorization':'Bearer '+forged})
    check('break1','tampered sub with original signature -> 403',str(broken.status_code),broken.status_code==403,'JWT verification or missing-token enforcement failure.')
    response=exchange('break2.txt','GET',base+'/nothing/here')
    _,observed=capture_logs('break2.txt',{response.headers.get('X-Blade-Request-Id','missing')},'OBSERVE')
    check('break2','non-5xx response; OBSERVE log',f'HTTP {response.status_code}; OBSERVE={observed}',response.status_code<500 and observed,'Unmatched-route forwarding or detection logging failure.')
    commands+='''
## Step 3 — expect 403
```bash
curl -i -H "Authorization: Bearer $TOKEN99" http://localhost:8080/orders/1042
```
## Step 4 — expect 200
```bash
curl -i -H "Authorization: Bearer $TOKEN77" http://localhost:8080/orders/1042
```
## Step 5 — expect 403 then 200
```bash
curl -i -X DELETE -H "Authorization: Bearer $TOKEN99" http://localhost:8080/orders/1042
curl -i -H "Authorization: Bearer $TOKEN77" http://localhost:8080/orders/1042
```
## Step 6 — expect 403
```bash
curl -i http://localhost:8080/orders/1042
```
## Step 7 — expect BLOCK >=3 (asynchronous delivery)
```bash
curl -i 'http://localhost:8100/detections?limit=100'
```
## Break 1 — expect 403
```bash
curl -i -H "Authorization: Bearer $FORGED" http://localhost:8080/orders/1042
```
## Break 2 — expect backend 404 and OBSERVE
```bash
curl -i http://localhost:8080/nothing/here
curl -i 'http://localhost:8100/detections?limit=100'
```
## Backend log lines for step 3
```bash
wc -l verification/logs/demo_backend.log
curl -i -H "Authorization: Bearer $TOKEN99" http://localhost:8080/orders/1042
wc -l verification/logs/demo_backend.log
```
'''
    (OUT/'COMMANDS.md').write_text(commands,encoding='utf-8')
    before_hashes=json.loads((OUT/'presentation-source-before.json').read_text())
    changed=[p for p,h in before_hashes.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    (OUT/'presentation-source-check.json').write_text(json.dumps({'changed':changed},indent=2))
    if changed:issues.append('- Source integrity: unexpected changed files: '+', '.join(changed))
    summary='# Presentation verification\n\nRun UTC: '+datetime.now(timezone.utc).isoformat()+'\n\n'
    summary+='The requested list has 10 checks; service startup/log capture is the 11th item.\n\n'
    summary+='| Item | Expected | Actual | Result |\n|---|---|---|---|\n'
    summary+='\n'.join(f'| {r["item"]} | {r["expected"]} | {r["actual"]} | {r["status"]} |' for r in checks)
    summary+='\n\nSource files changed: '+str(changed)+'\n\n'
    summary+='Services remain running. PIDs: presentation-processes.json. Logs: logs/*.log.\n'
    summary+='Runtime data: presentation-runtime/ (fresh SQLite and generated policies). Existing Docker volumes are unchanged; previous containers are stopped.\n'
    summary+='HTTP evidence contains complete request/response headers and bodies, including the requested demo Bearer tokens.\n'
    summary+='Backend non-arrival is supported by unchanged access-log lines; this is not a packet capture. No health requests run against the backend during step3.\n'
    (OUT/'SUMMARY.md').write_text(summary,encoding='utf-8')
    (OUT/'ISSUES.md').write_text('# Issues\n\n'+('\n'.join(issues) if issues else 'No FAIL items detected. No application code or configuration was modified.')+'\n',encoding='utf-8')
    print('COMPLETE: '+str(sum(r['status']=='PASS' for r in checks))+'/'+str(len(checks))+' PASS',flush=True)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        with (OUT/'ISSUES.md').open('a',encoding='utf-8') as f:f.write(f'\nVerification runner interrupted: {type(exc).__name__}: {exc}\n')
        raise
