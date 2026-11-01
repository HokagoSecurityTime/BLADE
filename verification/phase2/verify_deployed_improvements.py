"""Check the dedicated stack without printing webhook secrets or sending alerts."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import httpx

OUT = Path('verification/phase2')
ADMIN = 'http://127.0.0.1:18100'


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def main(stage: str) -> None:
    with httpx.Client(timeout=10) as client:
        settings_response = client.get(ADMIN + '/settings/alerts')
        settings_response.raise_for_status()
        settings = settings_response.json()
        policies_response = client.get(ADMIN + '/policies')
        policies_response.raise_for_status()
        policies = policies_response.json()
        snapshot = dict(settings_digest=digest(settings), policies_digest=digest(policies),
                        slack_configured=bool(settings.get('slack_webhook')), policy_count=len(policies))
        if stage == 'before':
            (OUT / 'deployment-before.json').write_text(json.dumps(snapshot, indent=2), encoding='utf-8')
            print(json.dumps(snapshot))
            return
        previous = json.loads((OUT / 'deployment-before.json').read_text(encoding='utf-8'))
        assert snapshot == previous, 'Stored policy/settings changed during deployment'
        health_policies = [p for p in policies if p['status'] == 'ACTIVE' and
                           p['endpoint']['path'] == '/public/health']
        assert not health_policies or all(p['label'] == 'public' for p in health_policies)
        expected_verdict = 'PASS' if health_policies else 'OBSERVE'
        response = client.get('http://127.0.0.1:18080/public/health')
        assert response.status_code == 200
        identifier = response.headers['X-Blade-Request-Id']
        row = None
        for _ in range(100):
            detections = client.get(ADMIN + '/detections?limit=100').json()
            row = next((item for item in detections if item['request_id'] == identifier), None)
            if row is not None:
                break
            time.sleep(.1)
        assert row is not None and row['verdict'] == expected_verdict and not row['would_block']
        assert client.get('http://127.0.0.1:13000').status_code == 200
        hashes = json.loads((OUT / 'phase1-test-hashes.json').read_text(encoding='utf-8'))
        assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected
                   for path, expected in hashes.items())
        result = dict(passed=True, settings_preserved=True, policies_preserved=True,
                      public_proxy_status=200, detection_stored=True, verdict=row['verdict'],
                      dashboard_status=200, original_tests_unchanged=len(hashes),
                      slack_configured=snapshot['slack_configured'])
        (OUT / 'deployment-improved-result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['before', 'after'])
    main(parser.parse_args().stage)
