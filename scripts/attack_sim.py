"""Repeat a labelled demo matrix; ground truth comes from cases, never HTTP responses."""
import argparse
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import time
from typing import Any

import httpx
import jwt


@dataclass(frozen=True)
class Case:
    label: str
    kind: str
    path: str
    user: str
    should_block: bool


def cases() -> list[Case]:
    pairs = [
        ('public', '/public/health', 'user_77', 'user_99'),
        ('role_required', '/admin/reports', 'admin_1', 'user_99'),
        ('membership_required', '/premium/content', 'admin_1', 'user_99'),
        ('tenant_match', '/orgs/org_1/docs', 'user_77', 'user_99'),
        ('owner_match', '/orders/1042', 'user_77', 'user_99'),
        ('owner_or_admin', '/users/user_77', 'admin_1', 'user_99'),
        ('manual_review_required', '/users/user_77', 'user_77', 'user_99'),
    ]
    return [Case(label, kind, path, user, kind == 'attack' and label != 'public')
            for label, path, normal, attack in pairs for kind, user in [('normal', normal), ('attack', attack)]]


def percentile(values: list[float], fraction: float) -> float | None:
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)] if values else None


def metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [r for r in rows if r['status'] in (200, 403)]
    tp = sum(r['should_block'] and r['status'] == 403 for r in valid)
    fn = sum(r['should_block'] and r['status'] == 200 for r in valid)
    fp = sum(not r['should_block'] and r['status'] == 403 for r in valid)
    tn = sum(not r['should_block'] and r['status'] == 200 for r in valid)
    latencies = [r['latency_ms'] for r in rows if r['latency_ms'] is not None]
    return dict(TP=tp, FN=fn, FP=fp, TN=tn, errors=len(rows)-len(valid),
                detection_rate=tp/(tp+fn) if tp+fn else None,
                false_positive_rate=fp/(fp+tn) if fp+tn else None,
                p50_ms=percentile(latencies,.5), p95_ms=percentile(latencies,.95))


def simulate(proxy: str, admin: str, secret: str, n: int, prepare: bool, poll: float) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    with httpx.Client(timeout=15) as client:
        response = client.get(admin + '/policies'); response.raise_for_status()
        policies = response.json()
        user_policy = next((p for p in policies if p['endpoint'] == {'method':'GET','path':'/users/{userId}'}), None)
        original = json.loads(json.dumps(user_policy))
        if not prepare:
            raise ValueError('Demo shares /users/{userId} across two labels. Pass --prepare-demo to temporarily switch its policy and restore it.')
        if not user_policy or user_policy['status'] != 'ACTIVE':
            raise ValueError('Approve the users policy before running --prepare-demo')
        for path in ('/orders/{orderId}', '/admin/reports', '/orgs/{orgId}/docs', '/premium/content', '/public/health'):
            if not any(p['endpoint'] == {'method':'GET','path':path} and p['status']=='ACTIVE' for p in policies):
                raise ValueError(f'Approve the GET policy for {path} before running')
        current = None
        try:
            for case in cases():
                if case.label in {'owner_or_admin', 'manual_review_required'} and current != case.label:
                    changed = dict(original)
                    changed.pop('status')
                    changed['label'] = case.label
                    changed['params'] = (dict(object_param='userId', owner_lookup=dict(table='users', id_col='id', owner_col='id', tenant_col=None),
                                              roles=['admin'], allowed_membership=[])
                                         if case.label == 'owner_or_admin' else dict(object_param=None, owner_lookup=None, roles=[], allowed_membership=[]))
                    response = client.put(admin + '/policies/' + user_policy['id'], json=changed); response.raise_for_status()
                    time.sleep(poll + .2)
                    current = case.label
                is_admin = case.user == 'admin_1'
                token = jwt.encode(dict(sub=case.user, roles=['admin'] if is_admin else ['user'],
                                        tenant_id='org_2' if case.user=='user_99' else 'org_1',
                                        membership='premium' if is_admin else 'basic', exp=int(time.time())+3600), secret, algorithm='HS256')
                for _ in range(n):
                    start = time.perf_counter()
                    try:
                        result = client.get(proxy + case.path, headers={'Authorization':'Bearer '+token})
                        status, request_id = result.status_code, result.headers.get('X-Blade-Request-Id')
                    except httpx.HTTPError:
                        status, request_id = 0, None
                    rows.append(dict(label=case.label, kind=case.kind, should_block=case.should_block,
                                     status=status, request_id=request_id, latency_ms=(time.perf_counter()-start)*1000))
        finally:
            if current is not None:
                restore = dict(original); restore.pop('status')
                response = client.put(admin + '/policies/' + original['id'], json=restore); response.raise_for_status()
                time.sleep(poll + .2)
        # Confirm the actual applied labels through asynchronously persisted detections.
        deadline = time.monotonic() + 10
        while True:
            response = client.get(admin + '/detections?limit=10000'); response.raise_for_status()
            logs = {r['request_id']:r for r in response.json()}
            if all(r['request_id'] in logs for r in rows if r['request_id']):
                break
            if time.monotonic() > deadline:
                raise RuntimeError('Not all simulation detections arrived')
            time.sleep(.1)
        for row in rows:
            log = logs.get(row['request_id'])
            row['verdict'] = log['verdict'] if log else None
            row['applied_label'] = log['label'] if log else None
            if log and log['label'] != row['label']:
                raise RuntimeError(f'Applied label mismatch: {row["label"]} vs {log["label"]}')
    grouped = [dict(label=c.label, kind=c.kind, **metrics([r for r in rows if r['label']==c.label and r['kind']==c.kind])) for c in cases()]
    return dict(n=n, summary=metrics(rows), groups=grouped, requests=rows,
                notes=['Public attack probe is authorized (TN), because public has no authorization restriction.',
                       'Manual-review cross-owner probe is an attack; OBSERVE forwarding counts as FN.',
                       'HTTP 200/403 only enter the confusion matrix; other statuses and network failures are errors.',
                       'Sequential GET requests; setup and policy polling are excluded from request latency.'])


def table(result: dict[str, Any]) -> str:
    def fmt(value: float | None, percent: bool = False) -> str:
        return 'N/A' if value is None else f'{value*100:.1f}%' if percent else f'{value:.2f}'
    lines = ['| label | case | TP | FN | FP | TN | errors | detection | FPR | p50 ms | p95 ms |',
             '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for row in result['groups'] + [dict(label='TOTAL',kind='all',**result['summary'])]:
        lines.append('| ' + ' | '.join([row['label'],row['kind'],*[str(row[k]) for k in ('TP','FN','FP','TN','errors')],
                                       fmt(row['detection_rate'],True),fmt(row['false_positive_rate'],True),fmt(row['p50_ms']),fmt(row['p95_ms'])]) + ' |')
    return '\n'.join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-n',type=int,default=5)
    parser.add_argument('--proxy',default=os.getenv('BLADE_SIM_PROXY_URL','http://127.0.0.1:8080'))
    parser.add_argument('--admin',default=os.getenv('BLADE_ADMIN_URL','http://127.0.0.1:8100'))
    parser.add_argument('--prepare-demo',action='store_true',help='Temporarily edit the ACTIVE users policy for two label groups, then restore it')
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    if not 1 <= args.n <= 500: parser.error('n must be between 1 and 500 (detection lookup limit)')
    secret = os.getenv('BLADE_JWT_SECRET')
    if not secret: parser.error('Set BLADE_JWT_SECRET')
    result = simulate(args.proxy,args.admin,secret,args.n,args.prepare_demo,float(os.getenv('BLADE_POLICY_POLL_SEC','5')))
    print(table(result))
    for note in result['notes']: print(note)
    if args.output: args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()
