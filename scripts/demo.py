"""Seven-step demo, executed inside admin-api by demo.sh (no host Python needed)."""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import time
from typing import Any

import httpx
import jwt
from common.features import enabled


def run(admin: str, proxy: str, db: Path, source: Path, poll: float) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    def report(step: int, detail: str, **data: Any) -> None:
        results.append(dict(step=step, detail=detail, **data))
        print(f'[{step}/7] PASS {detail}', flush=True)

    def token(user: str) -> str:
        return jwt.encode(dict(sub=user, roles=['user'], tenant_id='org_2' if user == 'user_99' else 'org_1',
                               membership='basic', exp=int(time.time()) + 3600),
                          os.environ['BLADE_JWT_SECRET'], algorithm='HS256')

    with httpx.Client(timeout=10) as client:
        deadline = time.monotonic() + 60
        while True:
            try:
                client.get(admin + '/policies').raise_for_status()
                client.get(proxy + '/public/health').raise_for_status()
                break
            except httpx.HTTPError:
                if time.monotonic() >= deadline:
                    raise RuntimeError('Services did not become ready within 60s') from None
                time.sleep(.2)
        if client.get(admin + '/policies').json():
            raise RuntimeError('Demo requires an empty policy store; use a fresh Compose project/volumes.')
        files = {name: (filename, (source / filename).read_bytes())
                 for name, filename in [('oas', 'openapi.json'), ('erd', 'schema.sql')]}
        response = client.post(admin + '/generate', files=files, timeout=1500)
        response.raise_for_status()
        policies = response.json()
        assert len(policies) == 7 and all(p['status'] == 'PENDING' for p in policies), 'Expected 7 PENDING policies'
        report(1, 'POST /generate: 7 PENDING policies')
        get_id = 'pol_orders_get_by_orderId'
        for identifier in (get_id, 'pol_orders_delete_by_orderId'):
            policy = next(p for p in policies if p['id'] == identifier)
            assert policy['label'] == 'owner_match', f'{identifier}: LLM returned {policy["label"]}; review generated policy'
        # Approve the GET policy last so its propagation time has a precise origin.
        policies.sort(key=lambda p: p['id'] == get_id)
        for policy in policies:
            response = client.post(admin + '/policies/' + policy['id'] + '/approve')
            response.raise_for_status()
            assert response.json()['status'] == 'ACTIVE'
            if enabled('BLADE_MODE_ENABLED'):
                response = client.post(admin + '/policies/' + policy['id'] + '/mode', json={'mode': 'enforce'})
                response.raise_for_status()
                assert response.json()['mode'] == 'enforce'
        approved = time.monotonic()
        report(2, 'All 7 policies approved')

        def request(method: str, user: str) -> httpx.Response:
            return client.request(method, proxy + '/orders/1042', headers={'Authorization': 'Bearer ' + token(user)})

        def changed(expected: int, start: float) -> tuple[httpx.Response, float]:
            while True:
                response = request('GET', 'user_99')
                elapsed = time.monotonic() - start
                if response.status_code == expected:
                    assert elapsed <= poll, f'Hot reload exceeded poll interval: {elapsed:.3f}s > {poll}s'
                    return response, elapsed
                assert elapsed < poll, f'Hot reload failed: expected {expected}, got {response.status_code}'
                time.sleep(min(.02, max(0, poll - elapsed)))

        blocked_get, approval_sec = changed(403, approved)
        report(3, f'user_99 GET: 403; approve hot reload {approval_sec:.3f}s <= {poll}s', elapsed_sec=approval_sec)
        owner = request('GET', 'user_77')
        assert owner.status_code == 200, f'Owner GET: {owner.status_code}'
        report(4, 'user_77 GET: 200')
        blocked_delete = request('DELETE', 'user_99')
        assert blocked_delete.status_code == 403, f'DELETE: {blocked_delete.status_code}'
        with sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True) as conn:
            assert conn.execute('SELECT user_id FROM orders WHERE id=?', (1042,)).fetchone() == ('user_77',)
        report(5, 'user_99 DELETE: 403; SQLite confirms order 1042 still belongs to user_77')

        def wait_logs(ids: set[str], verdict: str) -> list[dict[str, Any]]:
            deadline = time.monotonic() + 10
            while True:
                response = client.get(admin + '/detections', params={'limit': 10000})
                response.raise_for_status()
                found = [row for row in response.json() if row['request_id'] in ids]
                if len(found) == len(ids):
                    assert all(row['verdict'] == verdict for row in found), found
                    return found
                assert time.monotonic() < deadline, 'Detection delivery exceeded 10s'
                time.sleep(.05)

        ids = {r.headers['X-Blade-Request-Id'] for r in (blocked_get, blocked_delete)}
        wait_logs(ids, 'BLOCK')
        report(6, 'GET /detections: both demo requests have BLOCK records', block_count=2)
        response = client.post(admin + '/policies/' + get_id + '/rollback')
        response.raise_for_status()
        assert response.json()['status'] == 'PENDING'
        rolled_back = time.monotonic()
        observed, rollback_sec = changed(200, rolled_back)
        log = wait_logs({observed.headers['X-Blade-Request-Id']}, 'OBSERVE')[0]
        assert log['reason'] == 'no_policy'
        assert 'X-Blade-Policy' not in observed.headers
        report(7, f'Rollback: user_99 GET 200 + OBSERVE/no_policy; {rollback_sec:.3f}s <= {poll}s', elapsed_sec=rollback_sec)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--admin', default='http://localhost:8100')
    parser.add_argument('--proxy', default='http://proxy:8080')
    parser.add_argument('--db', type=Path, default=Path('/demo/demo.db'))
    parser.add_argument('--source', type=Path, default=Path('/app/demo_backend'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        results = run(args.admin, args.proxy, args.db, args.source, float(os.getenv('BLADE_POLICY_POLL_SEC', '5')))
    except (AssertionError, RuntimeError, httpx.HTTPError, sqlite3.Error, KeyError) as exc:
        parser.exit(1, f'DEMO FAILED: {exc}\n')
    if args.output:
        args.output.write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
