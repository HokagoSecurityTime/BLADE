"""Create the per-request DELETE targets for the Seerr run, through Seerr's HTTP API only (acting as alice via X-API-Key + X-API-User).

- alice movie requests: N_REQ distinct TMDB movies taken from Seerr's own discover endpoint (a request for an already-requested
  movie is rejected as duplicate), all PENDING -> DELETE /request/{id} normal targets (20 per chain x 3 chains + spare).
- alice issues on media 1 (TMDB 550), one auto comment each -> DELETE /issue/{id} normal targets (owner may delete only while
  the issue has <= 1 comment).
Writes data/targets.json. Nothing is written to the DB directly.
"""
import json
import os
import pathlib

import httpx

BASE = os.getenv('SEERR_URL', 'http://127.0.0.1:5055').rstrip('/') + '/api/v1'
KEY = os.getenv('SEERR_API_KEY', 'testkey')
ALICE = 3
N_REQ, N_ISSUE = 70, 80
OUT = pathlib.Path(__file__).with_name('data') / 'targets.json'


def client(user_id: int) -> httpx.Client:
    return httpx.Client(base_url=BASE, timeout=60, headers={'X-API-Key': KEY, 'X-API-User': str(user_id)})


def main() -> None:
    with client(ALICE) as c:
        existing = {m['tmdbId'] for m in c.get('/media', params={'take': 200}).json()['results']}
        ids: list[int] = []
        page = 1
        while len(ids) < N_REQ and page <= 10:
            for m in c.get('/discover/movies', params={'page': page}).json()['results']:
                if m['id'] not in existing and m['id'] not in ids:
                    ids.append(m['id'])
            page += 1
        requests, failed = [], []
        for tmdb in ids[:N_REQ]:
            r = c.post('/request', json={'mediaType': 'movie', 'mediaId': tmdb})
            if r.status_code == 201:
                d = r.json(); requests.append({'request_id': d['id'], 'media_id': d['media']['id'], 'tmdb': tmdb, 'status': d['status']})
            else:
                failed.append({'tmdb': tmdb, 'status': r.status_code, 'body': r.text[:200]})
        issues = []
        for i in range(N_ISSUE):
            r = c.post('/issue', json={'issueType': 4, 'message': f'alice delete-target issue {i}', 'mediaId': 1})
            r.raise_for_status(); d = r.json()
            issues.append({'issue_id': d['id'], 'comment_ids': [cm['id'] for cm in d.get('comments', [])]})
    OUT.write_text(json.dumps({'alice_requests': requests, 'alice_issues': issues, 'failed_requests': failed}, indent=1) + '\n', encoding='utf-8')
    print('requests', len(requests), 'failed', len(failed), 'issues', len(issues))


if __name__ == '__main__':
    main()
