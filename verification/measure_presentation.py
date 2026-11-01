"""Verification-only runner: existing attack_sim CLI plus matched direct requests."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import httpx
import jwt
from scripts.attack_sim import cases, metrics, percentile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'verification'
env=os.environ.copy()
for line in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines():
    if line.startswith(('BLADE_JWT_SECRET=','BLADE_POLICY_POLL_SEC=')):
        k,v=line.split('=',1);env[k]=v.strip().strip('"').strip("'")
before_hash=hashlib.sha256((ROOT/'scripts/attack_sim.py').read_bytes()).hexdigest()
with httpx.Client(timeout=15) as client:
    r=client.get('http://127.0.0.1:8100/policies');r.raise_for_status();before=r.json()
(OUT/'metrics-policies-before.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
command=[str(ROOT/'.python/python.exe'),str(ROOT/'scripts/attack_sim.py'),'-n','20','--prepare-demo',
         '--proxy','http://127.0.0.1:8080','--admin','http://127.0.0.1:8100',
         '--output',str(OUT/'metrics-proxy.json')]
env['PYTHONPATH']=str(ROOT)
with (OUT/'metrics-attack-sim.log').open('wb') as log:
    result=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
print('attack_sim exit:',result.returncode,flush=True)
if result.returncode:
    raise RuntimeError('attack_sim failed; review log before selecting manual fallback')
proxy=json.loads((OUT/'metrics-proxy.json').read_text())
direct=[]
with httpx.Client(timeout=15) as client:
    for case in cases():
        admin=case.user=='admin_1'
        token=jwt.encode(dict(sub=case.user,roles=['admin'] if admin else ['user'],
            tenant_id='org_2' if case.user=='user_99' else 'org_1',membership='premium' if admin else 'basic',
            exp=int(time.time())+3600),env['BLADE_JWT_SECRET'],algorithm='HS256')
        for _ in range(20):
            start=time.perf_counter()
            try:
                response=client.get('http://127.0.0.1:9000'+case.path,headers={'Authorization':'Bearer '+token})
                code=response.status_code
            except httpx.HTTPError:
                code=0
            direct.append(dict(label=case.label,kind=case.kind,path=case.path,status=code,
                               latency_ms=(time.perf_counter()-start)*1000))
    r=client.get('http://127.0.0.1:8100/policies');r.raise_for_status();after=r.json()
restored=sorted(before,key=lambda p:p['id'])==sorted(after,key=lambda p:p['id'])
direct_times=[r['latency_ms'] for r in direct]
d50,d95=percentile(direct_times,.5),percentile(direct_times,.95)
summary=proxy['summary']
delta=summary['p95_ms']-d95
labels={}
for line in (OUT/'step1_policies.md').read_text(encoding='utf-8').splitlines():
    parts=[s.strip() for s in line.split('|')]
    if len(parts)>3 and parts[1].startswith('pol_'):labels[parts[1]]=parts[2]
intended={}
for node in ast.walk(ast.parse((ROOT/'demo_backend/main.py').read_text(encoding='utf-8'))):
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr in ('get','delete'):
        desc=next((kw.value.value for kw in node.keywords if kw.arg=='description' and isinstance(kw.value,ast.Constant)),None)
        if desc and desc.startswith('Intended policy:'):
            intended[(node.func.attr.upper(),node.args[0].value)]=desc.split(':',1)[1].split(';')[0].strip()
classification=[]
for p in before:
    key=(p['endpoint']['method'],p['endpoint']['path'])
    classification.append(dict(id=p['id'],method=key[0],path=key[1],predicted=labels[p['id']],expected=intended[key],correct=labels[p['id']]==intended[key]))
correct=sum(r['correct'] for r in classification)
unchanged=before_hash==hashlib.sha256((ROOT/'scripts/attack_sim.py').read_bytes()).hexdigest()
metadata=dict(run_utc=datetime.now(timezone.utc).isoformat(),command=command,exit_code=result.returncode,
              attack_sim_sha256=before_hash,attack_sim_unchanged=unchanged,policies_restored=restored,
              direct_count=len(direct),direct_non_200=sum(r['status']!=200 for r in direct),
              direct_p50_ms=d50,direct_p95_ms=d95,p95_difference_ms=delta,classification=classification)
(OUT/'metrics-direct.json').write_text(json.dumps(direct,indent=2),encoding='utf-8')
(OUT/'metrics-details.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
def pct(value):return '해당 없음' if value is None else f'{value*100:.2f}%'
lines=['# 발표용 측정 결과',
       '', '**실행 방식:** 기존 `scripts/attack_sim.py`를 수정 없이 정상/공격 각각 20회 실행했다. 종료 코드 0이며 수동 curl 대체는 사용하지 않았다.',
       '', '## 표1. Label별 탐지 결과', '',
       '| Label | 요청 수 | TP | FP | TN | FN | 탐지율 | 오탐율 |',
       '|---|---:|---:|---:|---:|---:|---:|---:|']
for label in dict.fromkeys(c.label for c in cases()):
    rows=[r for r in proxy['requests'] if r['label']==label];m=metrics(rows)
    lines.append(f'| {label} | {len(rows)} | {m["TP"]} | {m["FP"]} | {m["TN"]} | {m["FN"]} | {pct(m["detection_rate"])} | {pct(m["false_positive_rate"])} |')
lines.extend([f'| **전체** | **{len(proxy["requests"])}** | **{summary["TP"]}** | **{summary["FP"]}** | **{summary["TN"]}** | **{summary["FN"]}** | **{pct(summary["detection_rate"])}** | **{pct(summary["false_positive_rate"])}** |',
    '', '각 label은 정상 20회 + 공격 형태 요청 20회다. public은 인가 제한이 없어 공격 형태 요청도 TN으로 집계한다. manual_review_required의 타인 조회는 공격 정답이지만 OBSERVE로 통과하므로 FN이다. 분모가 0인 탐지율은 0%가 아닌 해당 없음으로 표기했다.',
    '', '## 표2. 전체 지표와 지연 비교', '', '| 지표 | 측정값 |', '|---|---:|',
    f'| 전체 탐지율 TP/(TP+FN) | {pct(summary["detection_rate"])} |',
    f'| 전체 오탐율 FP/(FP+TN) | {pct(summary["false_positive_rate"])} |',
    f'| 프록시 요청 수 | {len(proxy["requests"])} |', f'| 프록시 HTTP/연결 오류 | {summary["errors"]} |',
    f'| 프록시 p50 | {summary["p50_ms"]:.3f} ms |', f'| 프록시 p95 | {summary["p95_ms"]:.3f} ms |',
    f'| 백엔드 직접 요청 수 | {len(direct)} |', f'| 백엔드 직접 비-200/연결 오류 | {metadata["direct_non_200"]} |',
    f'| 백엔드 직접 p50 | {d50:.3f} ms |', f'| 백엔드 직접 p95 | {d95:.3f} ms |',
    '', f'**프록시 추가 지연 p95 {delta:+.3f} ms**',
    '', '같은 PC의 현재 로컬 서비스에서 순차 GET 요청으로 측정했다. 프록시 280회 후 동일한 label/정상·공격/경로/호출자/횟수 구성으로 백엔드에 280회를 직접 보냈다. 각 실험은 별도 HTTP 클라이언트의 연결을 재사용했고, 별도 워밍업은 하지 않았다. p50/p95는 nearest-rank 방식이다. 토큰 생성·정책 갱신 대기·탐지 로그 확인 시간은 요청 지연에서 제외했다.',
    '', '**해석 제한:** 위 추가 지연은 두 표본의 p95 차이다. 프록시는 공격을 403으로 단축 처리하지만 직접 호출은 백엔드까지 실행되므로, 같은 업무를 모두 수행한 요청에 대한 순수 프록시 처리 비용이나 동시 부하 성능을 뜻하지 않는다.',
    '', '## 표3. LLM 분류 정답률', '',
    '| Method | 경로 | 실제 생성 label (step1) | 데모 의도 label | 정답 |', '|---|---|---|---|---|'])
for row in classification:
    lines.append(f'| {row["method"]} | {row["path"]} | {row["predicted"]} | {row["expected"]} | {"O" if row["correct"] else "X"} |')
lines.extend(['',f'**LLM 분류 정답률 {correct}/7 ({correct/7*100:.2f}%)**',
    '', '분류 비교는 `step1_policies.md`의 실제 생성 라벨과 `demo_backend/main.py`에 명시된 Intended policy를 사용했다. 수동 검토 탈출은 정답으로 계산하지 않았다.',
    '', '**분류 정확도와 런타임 평가를 구분:** 7종 label 평가를 위해 기존 시뮬레이터의 `--prepare-demo`가 사용자 조회 정책을 owner_or_admin / manual_review_required로 일시 변경한다. 이는 생성된 정책을 그대로 사용한 종단 간 탐지율이 아니라 7종 평가 동작 시험이다. 종료 후 원본 정책을 복원했으며 분류 정확도 표에는 변경 전 step1의 결과만 사용했다.',
    '', '## 재현과 증거', '', '```bash',
    'python scripts/attack_sim.py --prepare-demo -n 20 --proxy http://127.0.0.1:8080 --admin http://127.0.0.1:8100 --output verification/metrics-proxy.json',
    '```', '', '환경변수 BLADE_JWT_SECRET, BLADE_POLICY_POLL_SEC는 실행 중 서비스와 동일하게 설정해야 한다.',
    '', f'- 측정 시각(UTC): {metadata["run_utc"]}',f'- 기존 스크립트 해시 동일: {unchanged}; 원본 정책 복원 확인: {restored}',
    '- [시뮬레이터 출력](metrics-attack-sim.log) · [프록시 요청별 결과](metrics-proxy.json) · [백엔드 직접 요청별 결과](metrics-direct.json)',
    '- [실행 정보·분류 비교 근거](metrics-details.json) · [측정 전 정책](metrics-policies-before.json)',
    '- 기존 JWT 시크릿 길이 경고는 발생했으며 수정하지 않았다.'])
(OUT/'METRICS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'proxy':summary,'direct_p50':d50,'direct_p95':d95,'delta':delta,'accuracy':f'{correct}/7','restored':restored},indent=2),flush=True)
