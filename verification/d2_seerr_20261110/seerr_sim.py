"""Real-service runtime check of BLADE in front of Seerr v3.5.1 (D2, 2026-11-10). Adapted from verification/mealie_runtime/real_service_sim.py.

Ground truth (should_block) is the case design below: "attack" = a user acting on another user's object (or anonymous /
non-admin on admin-only data), "normal" = owner / admin / permitted access. It is fixed before BLADE runs and never read from
HTTP responses. Seerr's own status is recorded as an independent oracle (attack -> non-2xx, normal -> 2xx). No intended policy
label is written here: the policy labels are whatever LoRA v7 generated (reported alongside).

BLADE's verdict comes from the admin API detection log keyed by X-Blade-Request-Id (BLOCK = blocked, PASS/OBSERVE = passed).
Three chains with the same case matrix: proxy (client -> BLADE 127.0.0.3:8080 -> shim 5056 -> Seerr), shim (client -> shim ->
Seerr) and direct (client -> Seerr with X-API-Key + X-API-User). DELETE cases consume per-request targets from data/targets.json
(alice's own pending requests / single-comment issues), 20 per chain.
"""
import argparse
import json
import math
import os
import pathlib
import time
from dataclasses import dataclass
from typing import Any

import httpx
import jwt

ROOT = pathlib.Path(__file__).parent
TARGETS = json.loads((ROOT / 'data' / 'targets.json').read_text(encoding='utf-8'))
USERS = {'admin': 1, 'demo': 2, 'alice': 3, 'bob': 4}
ROLES = {'admin': ['admin'], 'demo': ['user'], 'alice': ['user'], 'bob': ['user']}
API_KEY = os.getenv('SEERR_API_KEY', 'testkey')


@dataclass(frozen=True)
class Case:
    endpoint: str      # "METHOD /api/v1/..." as in the policy
    kind: str          # normal | attack
    actor: str         # admin | alice | bob | anonymous
    note: str
    should_block: bool
    path_fn: Any       # (run_index, i) -> concrete path
    body: Any = None


def cases() -> list[Case]:
    const = lambda p: (lambda run, i: p)  # noqa: E731
    req = TARGETS['alice_requests']; iss = TARGETS['alice_issues']
    return [
        # request 1 = alice's movie request (TMDB 550); media 1
        Case('GET /api/v1/request/{requestId}', 'normal', 'alice', '본인 요청 조회', False, const('/api/v1/request/1')),
        Case('GET /api/v1/request/{requestId}', 'normal', 'admin', '관리자가 타인 요청 조회(MANAGE_REQUESTS)', False, const('/api/v1/request/1')),
        Case('GET /api/v1/request/{requestId}', 'attack', 'bob', '타인(alice) 요청 조회', True, const('/api/v1/request/1')),
        Case('GET /api/v1/request/{requestId}', 'attack', 'anonymous', '토큰 없음', True, const('/api/v1/request/1')),
        Case('PUT /api/v1/request/{requestId}', 'normal', 'admin', '관리자가 요청 수정(MANAGE_REQUESTS)', False, const('/api/v1/request/1'), {'mediaType': 'movie'}),
        Case('PUT /api/v1/request/{requestId}', 'attack', 'bob', '타인(alice) 요청 수정', True, const('/api/v1/request/1'), {'mediaType': 'movie'}),
        Case('DELETE /api/v1/request/{requestId}', 'normal', 'alice', '본인 PENDING 요청 삭제(요청마다 다른 대상)', False, lambda run, i: f"/api/v1/request/{req[run * 20 + i]['request_id']}"),
        Case('DELETE /api/v1/request/{requestId}', 'attack', 'bob', '타인(alice) 요청 삭제', True, const('/api/v1/request/1')),
        # issue 1 = alice's issue on media 1; comment 1 = alice's auto comment
        Case('GET /api/v1/issue/{issueId}', 'normal', 'alice', '본인 이슈 조회', False, const('/api/v1/issue/1')),
        Case('GET /api/v1/issue/{issueId}', 'normal', 'admin', '관리자가 타인 이슈 조회(MANAGE_ISSUES)', False, const('/api/v1/issue/1')),
        Case('GET /api/v1/issue/{issueId}', 'attack', 'bob', '타인(alice) 이슈 조회', True, const('/api/v1/issue/1')),
        Case('POST /api/v1/issue/{issueId}/comment', 'normal', 'alice', '본인 이슈에 댓글', False, const('/api/v1/issue/1/comment'), {'message': 'owner comment'}),
        Case('POST /api/v1/issue/{issueId}/comment', 'attack', 'bob', '타인(alice) 이슈에 댓글', True, const('/api/v1/issue/1/comment'), {'message': 'intruder comment'}),
        Case('DELETE /api/v1/issue/{issueId}', 'normal', 'alice', '본인 이슈 삭제(댓글 1개, 요청마다 다른 대상)', False, lambda run, i: f"/api/v1/issue/{iss[run * 20 + i]['issue_id']}"),
        Case('DELETE /api/v1/issue/{issueId}', 'attack', 'bob', '타인(alice) 이슈 삭제', True, const('/api/v1/issue/1')),
        Case('PUT /api/v1/issueComment/{commentId}', 'normal', 'alice', '본인 댓글 수정', False, const('/api/v1/issueComment/1'), {'message': 'edited by owner'}),
        Case('PUT /api/v1/issueComment/{commentId}', 'attack', 'bob', '타인(alice) 댓글 수정', True, const('/api/v1/issueComment/1'), {'message': 'edited by bob'}),
        Case('PUT /api/v1/issueComment/{commentId}', 'attack', 'admin', '관리자가 타인 댓글 수정(Seerr는 작성자만 허용)', True, const('/api/v1/issueComment/1'), {'message': 'edited by admin'}),
        # user 3 = alice
        Case('GET /api/v1/user/{userId}', 'normal', 'alice', '본인 프로필', False, const('/api/v1/user/3')),
        Case('GET /api/v1/user/{userId}', 'normal', 'admin', '관리자가 타인 프로필(MANAGE_USERS)', False, const('/api/v1/user/3')),
        Case('GET /api/v1/user/{userId}', 'normal', 'bob', '타인 프로필(Seerr는 로그인 사용자에게 필터된 공개 필드 허용)', False, const('/api/v1/user/3')),
        Case('GET /api/v1/user/{userId}', 'attack', 'anonymous', '토큰 없음', True, const('/api/v1/user/3')),
        Case('GET /api/v1/user/{userId}/quota', 'normal', 'alice', '본인 쿼터', False, const('/api/v1/user/3/quota')),
        Case('GET /api/v1/user/{userId}/quota', 'normal', 'admin', '관리자가 타인 쿼터(MANAGE_USERS∧MANAGE_REQUESTS)', False, const('/api/v1/user/3/quota')),
        Case('GET /api/v1/user/{userId}/quota', 'attack', 'bob', '타인(alice) 쿼터', True, const('/api/v1/user/3/quota')),
        Case('GET /api/v1/settings/main', 'normal', 'admin', '관리자 설정 조회', False, const('/api/v1/settings/main')),
        Case('GET /api/v1/settings/main', 'attack', 'alice', '일반 사용자가 설정 조회', True, const('/api/v1/settings/main')),
        Case('GET /api/v1/settings/main', 'attack', 'anonymous', '토큰 없음', True, const('/api/v1/settings/main')),
    ]


def blade_headers(actor: str, secret: str) -> dict[str, str]:
    if actor == 'anonymous':
        return {}
    tok = jwt.encode({'sub': str(USERS[actor]), 'roles': ROLES[actor], 'tenant_id': 'seerr', 'membership': 'basic',
                      'exp': int(time.time()) + 7200}, secret, algorithm='HS256')
    return {'Authorization': 'Bearer ' + tok}


def seerr_headers(actor: str, _secret: str) -> dict[str, str]:
    return {} if actor == 'anonymous' else {'X-API-Key': API_KEY, 'X-API-User': str(USERS[actor])}


def percentile(values: list[float], fraction: float) -> float | None:
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)] if values else None


def run_chain(name: str, base: str, run_index: int, n: int, header_fn, secret: str, admin: str | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with httpx.Client(timeout=60) as client:
        for case in cases():
            headers = header_fn(case.actor, secret)
            method = case.endpoint.split()[0]
            for i in range(n):
                path = case.path_fn(run_index, i)
                start = time.perf_counter()
                try:
                    r = client.request(method, base + path, headers=headers, json=case.body)
                    status, rid, pol = r.status_code, r.headers.get('X-Blade-Request-Id'), r.headers.get('X-Blade-Policy')
                    blade_403 = status == 403 and rid is not None and 'policy_id' in r.text
                except httpx.HTTPError:
                    status, rid, pol, blade_403 = 0, None, None, False
                rows.append(dict(chain=name, endpoint=case.endpoint, kind=case.kind, actor=case.actor, note=case.note,
                                 should_block=case.should_block, method=method, path=path, status=status, request_id=rid,
                                 policy_id=pol, blade_403=blade_403, latency_ms=(time.perf_counter() - start) * 1000))
    if admin:
        with httpx.Client(timeout=30) as client:
            deadline = time.monotonic() + 30
            while True:
                logs = {d['request_id']: d for d in client.get(admin + '/detections?limit=10000').json()}
                if all(r['request_id'] in logs for r in rows if r['request_id']):
                    break
                if time.monotonic() > deadline:
                    raise RuntimeError('detections incomplete')
                time.sleep(0.2)
        for r in rows:
            d = logs.get(r['request_id'])
            r['verdict'] = d['verdict'] if d else None
            r['reason'] = d['reason'] if d else None
            r['applied_label'] = d['label'] if d else None
    return rows


def confusion(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [r for r in rows if r.get('verdict') is not None]
    blocked = lambda r: r['verdict'] == 'BLOCK'  # noqa: E731
    tp = sum(r['should_block'] and blocked(r) for r in valid)
    fn = sum(r['should_block'] and not blocked(r) for r in valid)
    fp = sum((not r['should_block']) and blocked(r) for r in valid)
    tn = sum((not r['should_block']) and not blocked(r) for r in valid)
    lat = [r['latency_ms'] for r in rows]
    return dict(n=len(rows), TP=tp, FN=fn, FP=fp, TN=tn, errors=len(rows) - len(valid),
                detection_rate=tp / (tp + fn) if tp + fn else None,
                false_positive_rate=fp / (fp + tn) if fp + tn else None,
                p50_ms=percentile(lat, .5), p95_ms=percentile(lat, .95))


def oracle(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ok = sum((r['status'] >= 400) == r['should_block'] for r in rows if r['status'])
    return dict(n=len(rows), agree=ok, rate=ok / len(rows) if rows else None)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('-n', type=int, default=20)
    ap.add_argument('--proxy', default='http://127.0.0.3:8080')
    ap.add_argument('--shim', default='http://127.0.0.1:5056')
    ap.add_argument('--seerr', default=os.getenv('SEERR_URL', 'http://127.0.0.1:5055'))
    ap.add_argument('--admin', default=os.getenv('BLADE_ADMIN_URL', 'http://127.0.0.1:8102'))
    ap.add_argument('--out', type=pathlib.Path, default=ROOT / 'results')
    args = ap.parse_args()
    if not 1 <= args.n <= 20:
        ap.error('n must be 1..20 (seeded delete targets: 20 per chain)')
    secret = os.environ['BLADE_JWT_SECRET']
    args.out.mkdir(parents=True, exist_ok=True)

    with httpx.Client(timeout=30) as c:
        policies = c.get(args.admin + '/policies').json()
    (args.out / 'policies_at_run.json').write_text(json.dumps(policies, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    active = {p['endpoint']['method'] + ' ' + p['endpoint']['path'] for p in policies if p['status'] == 'ACTIVE'}
    endpoints = sorted({c.endpoint for c in cases()})
    missing = set(endpoints) - active
    if missing:
        raise SystemExit(f'not ACTIVE: {sorted(missing)}')

    started = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    proxy_rows = run_chain('proxy', args.proxy, 0, args.n, blade_headers, secret, args.admin)
    shim_rows = run_chain('shim', args.shim, 1, args.n, blade_headers, secret, None)
    direct_rows = run_chain('direct', args.seerr, 2, args.n, seerr_headers, secret, None)

    pol_of = {p['endpoint']['method'] + ' ' + p['endpoint']['path']: p for p in policies if p['status'] == 'ACTIVE'}
    by_label, by_endpoint, by_case = {}, {}, []
    for label in sorted({pol_of[r['endpoint']]['label'] for r in proxy_rows}):
        sub = [r for r in proxy_rows if pol_of[r['endpoint']]['label'] == label]
        by_label[label] = dict(**confusion(sub), normal=sum(r['kind'] == 'normal' for r in sub), attack=sum(r['kind'] == 'attack' for r in sub))
    for cs in cases():
        sub = [r for r in proxy_rows if r['endpoint'] == cs.endpoint and r['kind'] == cs.kind and r['actor'] == cs.actor]
        by_case.append(dict(endpoint=cs.endpoint, predicted=pol_of[cs.endpoint]['label'], kind=cs.kind, actor=cs.actor, note=cs.note,
                            should_block=cs.should_block, **confusion(sub),
                            verdicts=sorted({(r['verdict'], r['reason']) for r in sub}),
                            statuses=sorted({r['status'] for r in sub}),
                            seerr_direct_statuses=sorted({r['status'] for r in direct_rows if r['endpoint'] == cs.endpoint and r['kind'] == cs.kind and r['actor'] == cs.actor}),
                            shim_statuses=sorted({r['status'] for r in shim_rows if r['endpoint'] == cs.endpoint and r['kind'] == cs.kind and r['actor'] == cs.actor})))
    for ep in endpoints:
        by_endpoint[ep] = dict(predicted=pol_of[ep]['label'], **confusion([r for r in proxy_rows if r['endpoint'] == ep]))
    lat = {name: dict(p50_ms=percentile([r['latency_ms'] for r in rows], .5), p95_ms=percentile([r['latency_ms'] for r in rows], .95),
                      n=len(rows), errors=sum(r['status'] == 0 for r in rows),
                      non2xx_normal=sum(r['kind'] == 'normal' and not 200 <= r['status'] < 300 for r in rows))
           for name, rows in (('proxy', proxy_rows), ('shim', shim_rows), ('direct', direct_rows))}
    summary = dict(started_utc=started, n=args.n, seerr='v3.5.1 (ghcr.io/seerr-team/seerr:v3.5.1, 564bfb08)',
                   model=os.getenv('BLADE_LORA_MODEL'), min_confidence=os.getenv('BLADE_LORA_MIN_CONFIDENCE'),
                   total=confusion(proxy_rows), by_label=by_label, by_endpoint=by_endpoint, by_case=by_case, latency=lat,
                   oracle=dict(direct=oracle(direct_rows), shim=oracle(shim_rows)),
                   notes=['should_block is the case design (attack = other user\'s object / anonymous / non-admin on admin data), fixed before BLADE ran; never from responses.',
                          'Policy labels are LoRA v7 output; no human-decided label is used anywhere in this harness.',
                          'BLADE verdict = detection log verdict; BLOCK = blocked, PASS/OBSERVE = passed (OBSERVE on an attack = FN).',
                          'GET /user/{userId} by another logged-in user is normal: Seerr returns a filtered public profile by design.',
                          'Chains: proxy = client->BLADE->shim->Seerr, shim = client->shim->Seerr (BLADE JWT), direct = client->Seerr (X-API-Key + X-API-User).'])
    (args.out / 'metrics-proxy.json').write_text(json.dumps(proxy_rows, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    (args.out / 'metrics-shim.json').write_text(json.dumps(shim_rows, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    (args.out / 'metrics-direct.json').write_text(json.dumps(direct_rows, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    fmt = lambda v: 'N/A' if v is None else f'{v * 100:.1f}%'  # noqa: E731
    print('| generated label | 요청 | TP | FN | FP | TN | 탐지율 | 오탐율 |')
    print('|---|---:|---:|---:|---:|---:|---:|---:|')
    for label, m in by_label.items():
        print(f"| {label} | {m['n']} | {m['TP']} | {m['FN']} | {m['FP']} | {m['TN']} | {fmt(m['detection_rate'])} | {fmt(m['false_positive_rate'])} |")
    t = summary['total']
    print(f"| **전체** | {t['n']} | {t['TP']} | {t['FN']} | {t['FP']} | {t['TN']} | {fmt(t['detection_rate'])} | {fmt(t['false_positive_rate'])} |")
    print()
    for c in by_case:
        print(f"{c['endpoint']:44s} {c['kind']:6s} {c['actor']:9s} predicted={c['predicted']:22s} TP{c['TP']} FN{c['FN']} FP{c['FP']} TN{c['TN']} "
              f"verdicts={c['verdicts']} http={c['statuses']} shim={c['shim_statuses']} direct={c['seerr_direct_statuses']}")
    print()
    print('latency', json.dumps(lat))
    print('oracle', json.dumps(summary['oracle']))


if __name__ == '__main__':
    main()
