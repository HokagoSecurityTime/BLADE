"""Human intervention on the 10 generated Seerr policies (D2) — labels stay the model's (LoRA v7); only the ERD binding of
owner_lookup is corrected where the pipeline failed or picked a column Seerr never fills. Every edit is recorded.

Edits (all via PUT /policies/{id}, then every policy is approved):
  E1 GET/DELETE /api/v1/request/{requestId}: model label owner_or_admin (confidence 0.9) was demoted to manual (confidence 0.0)
     by the parameter stage ("Unknown lookup table or id column": requestId not bound to an ERD table). Human: owner_lookup =
     media_request.id / owner_col requestedById (ERD: media_request.requestedById -> user.id); label restored to the model label.
  E2 PUT /api/v1/issueComment/{commentId}: model label owner_match demoted the same way. Human: owner_lookup = issue_comment.id /
     owner_col userId; label restored to owner_match.
  E3 GET/DELETE /api/v1/issue/{issueId}, POST /api/v1/issue/{issueId}/comment: pipeline bound owner_col = modifiedById, a column
     Seerr only fills on update (NULL on freshly created issues, so the real owner would be blocked). Human: owner_col -> createdById.
Not edited: PUT /request (role_required, roles ['admin','user'] as extracted), GET /user/{userId} (role_required ['admin']),
GET /user/{userId}/quota (owner_or_admin user.id/id), GET /settings/main (model owner_match had no object -> stays manual).
"""
import json
import os
import pathlib
import sys

import httpx

ADMIN = os.getenv('BLADE_ADMIN_URL', 'http://127.0.0.1:8102').rstrip('/')
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / 'human_edits.json'

EDITS = {
    ('GET', '/api/v1/request/{requestId}'): dict(edit='E1', label='owner_or_admin', confidence=0.9, object_param='requestId',
        owner_lookup={'table': 'media_request', 'id_col': 'id', 'owner_col': 'requestedById', 'tenant_col': None}, roles=['owner', 'admin']),
    ('DELETE', '/api/v1/request/{requestId}'): dict(edit='E1', label='owner_or_admin', confidence=0.9, object_param='requestId',
        owner_lookup={'table': 'media_request', 'id_col': 'id', 'owner_col': 'requestedById', 'tenant_col': None}, roles=['owner', 'admin']),
    ('PUT', '/api/v1/issueComment/{commentId}'): dict(edit='E2', label='owner_match', confidence=0.9, object_param='commentId',
        owner_lookup={'table': 'issue_comment', 'id_col': 'id', 'owner_col': 'userId', 'tenant_col': None}),
    ('GET', '/api/v1/issue/{issueId}'): dict(edit='E3', owner_lookup={'table': 'issue', 'id_col': 'id', 'owner_col': 'createdById', 'tenant_col': None}),
    ('DELETE', '/api/v1/issue/{issueId}'): dict(edit='E3', owner_lookup={'table': 'issue', 'id_col': 'id', 'owner_col': 'createdById', 'tenant_col': None}),
    ('POST', '/api/v1/issue/{issueId}/comment'): dict(edit='E3', owner_lookup={'table': 'issue', 'id_col': 'id', 'owner_col': 'createdById', 'tenant_col': None}),
}
KEYS = ('id', 'endpoint', 'label', 'params', 'confidence', 'evidence', 'created_at', 'mode', 'version', 'source')


def main() -> None:
    with httpx.Client(base_url=ADMIN, timeout=60) as c:
        policies = c.get('/policies').json()
        record = []
        for p in policies:
            key = (p['endpoint']['method'], p['endpoint']['path'])
            before = json.loads(json.dumps(p))
            e = EDITS.get(key)
            if e:
                body = {k: p[k] for k in KEYS}
                if 'label' in e:
                    body['label'] = e['label']; body['confidence'] = e['confidence']
                params = dict(body['params'])
                if 'object_param' in e:
                    params['object_param'] = e['object_param']
                params['owner_lookup'] = e['owner_lookup']
                if 'roles' in e:
                    params['roles'] = e['roles']
                body['params'] = params
                body['source'] = 'manual'
                body['evidence'] = p['evidence'] + f" | human edit {e['edit']} (D2 2026-11-10): " + (
                    f"label restored to model label {e['label']}; " if 'label' in e else '') + f"owner_lookup={json.dumps(e['owner_lookup'])}"
                r = c.put(f"/policies/{p['id']}", json=body)
                r.raise_for_status()
                after = r.json()
            else:
                after = p
            a = c.post(f"/policies/{p['id']}/approve"); a.raise_for_status()
            final = a.json()
            record.append({'id': p['id'], 'method': key[0], 'path': key[1], 'edit': e['edit'] if e else None,
                           'before': {'label': before['label'], 'confidence': before['confidence'], 'params': before['params']},
                           'after': {'label': final['label'], 'confidence': final['confidence'], 'params': final['params'], 'status': final['status'], 'source': final['source']}})
            print(key[0], key[1], before['label'], '->', final['label'], final['status'], 'edit', e['edit'] if e else '-',
                  'owner_lookup', final['params'].get('owner_lookup'), 'roles', final['params'].get('roles'))
    OUT.write_text(json.dumps(record, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print('wrote', OUT, len(record))


if __name__ == '__main__':
    sys.exit(main())
