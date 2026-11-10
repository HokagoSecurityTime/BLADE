"""Build BLADE /generate inputs for the Seerr v3.5.1 (564bfb08) D2 run: OpenAPI subset (10 operations) + flattened handlers.

Transformations, nothing else (same kind as the Mealie precedent verification/mealie_runtime/inputs/controller_mealie_flat.py):
  * OpenAPI: the server prefix `/api/v1` (servers[0].url = "{server}/api/v1") is expanded into each path so the path the
    proxy sees matches the policy endpoint; global `security` and components.securitySchemes are kept.
  * Handlers: each selected `router.<method>(` call is copied verbatim from upstream/routes/*.ts, except that
    (a) the Express route string is replaced by the full OpenAPI path (prefix expanded, `:param` -> OpenAPI param name),
        because BLADE matches code to an endpoint by `METHOD /path`, and
    (b) TypeScript generic arguments on the call (`router.get<{...}>(` -> `router.get(`) are removed, because the
        route regex in pipeline/parsers/controller.py expects `router.get(` directly. Handler bodies are untouched.
  Middleware helpers (isAuthenticated, isOwnProfileOrAdmin) are appended verbatim for the reader; BLADE only sends the
  matched handler snippet to the model.
Writes inputs/openapi_seerr_subset.json, inputs/controller_seerr_flat.ts, inputs/selection.json and prints SHA-256s.
"""
import hashlib
import json
import pathlib
import re

import yaml

ROOT = pathlib.Path(__file__).parent
UP = ROOT / 'upstream'
OUT = ROOT / 'inputs'
OUT.mkdir(exist_ok=True)
PREFIX = '/api/v1'

# (method, OpenAPI path, route file, Express route string as written in the file)
SELECTION = [
    ('GET', '/request/{requestId}', 'routes_request.ts', '/:requestId'),
    ('PUT', '/request/{requestId}', 'routes_request.ts', '/:requestId'),
    ('DELETE', '/request/{requestId}', 'routes_request.ts', '/:requestId'),
    ('GET', '/issue/{issueId}', 'routes_issue.ts', '/:issueId'),
    ('POST', '/issue/{issueId}/comment', 'routes_issue.ts', '/:issueId/comment'),
    ('DELETE', '/issue/{issueId}', 'routes_issue.ts', '/:issueId'),
    ('PUT', '/issueComment/{commentId}', 'routes_issueComment.ts', '/:commentId'),
    ('GET', '/user/{userId}', 'routes_user_index.ts', '/:id'),
    ('GET', '/user/{userId}/quota', 'routes_user_index.ts', '/:id/quota'),
    ('GET', '/settings/main', 'routes_settings_index.ts', '/main'),
]


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build_oas() -> None:
    doc = yaml.safe_load((UP / 'seerr-api.yml').read_text(encoding='utf-8'))
    paths = {}
    for method, path, _, _ in SELECTION:
        op = doc['paths'][path][method.lower()]
        paths.setdefault(PREFIX + path, {})[method.lower()] = op
        # path-level parameters, if any, travel with the path
        if 'parameters' in doc['paths'][path]:
            paths[PREFIX + path]['parameters'] = doc['paths'][path]['parameters']
    subset = {'openapi': doc['openapi'], 'info': doc['info'], 'security': doc['security'], 'paths': paths,
              'components': {'securitySchemes': doc['components']['securitySchemes']}}
    (OUT / 'openapi_seerr_subset.json').write_text(json.dumps(subset, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def extract_handler(src: str, method: str, express_path: str) -> str:
    # locate `router.<method>` whose first string literal argument equals express_path
    pat = re.compile(r'(\w+)\.' + method.lower() + r'(<[^(]*?>)?\(\s*([\'"])' + re.escape(express_path) + r'\3\s*,', re.S)
    m = pat.search(src)
    if not m:
        raise SystemExit(f'route not found: {method} {express_path}')
    ends = [i for i in (src.find('\n);\n', m.start()), src.find('\n});\n', m.start())) if i != -1]
    end = min(ends)
    end += len('\n);\n') if src.startswith('\n);\n', end) else len('\n});\n')
    return src[m.start():end]


def build_controller() -> dict:
    parts = ['// Seerr v3.5.1 (564bfb08) handlers flattened for BLADE (see build_inputs.py header for the two transformations).',
             '// Sources: server/routes/{request,issue,issueComment}.ts, server/routes/user/index.ts, server/routes/settings/index.ts',
             '']
    record = []
    for method, path, fname, express_path in SELECTION:
        src = (UP / 'routes' / fname).read_text(encoding='utf-8')
        snippet = extract_handler(src, method, express_path)
        head_re = re.compile(r'(\w+)\.' + method.lower() + r'(<[^(]*?>)?\(\s*([\'"])' + re.escape(express_path) + r'\3\s*,', re.S)
        hm = head_re.match(snippet)
        original_head = hm.group(0)
        new_head = f"{hm.group(1)}.{method.lower()}('{PREFIX + path}',"
        flat = new_head + snippet[hm.end():]
        parts.append(f'// --- {method} {PREFIX + path}  (from server/{fname.replace("_", "/", 1).replace("routes/", "routes/")} route {express_path!r})')
        parts.append(flat.rstrip() + '\n')
        record.append({'method': method, 'path': PREFIX + path, 'file': fname, 'express_route': express_path,
                       'call_head_original': original_head.strip(), 'call_head_flat': new_head.strip(),
                       'body_sha256': hashlib.sha256(snippet[hm.end():].encode()).hexdigest()})
    parts.append('// --- helpers referenced above, verbatim ---')
    parts.append('// server/utils/profileMiddleware.ts')
    parts.append((UP / 'profileMiddleware.ts').read_text(encoding='utf-8'))
    parts.append('// server/middleware/auth.ts')
    parts.append((UP / 'auth.ts').read_text(encoding='utf-8'))
    (OUT / 'controller_seerr_flat.ts').write_text('\n'.join(parts), encoding='utf-8')
    return {'selection': record}


if __name__ == '__main__':
    build_oas()
    rec = build_controller()
    rec['upstream_sha256'] = {p.name: sha(p) for p in sorted(UP.glob('*')) if p.is_file()} | {f'routes/{p.name}': sha(p) for p in sorted((UP / 'routes').glob('*.ts'))}
    rec['outputs_sha256'] = {p.name: sha(p) for p in sorted(OUT.glob('*')) if p.name != 'selection.json'}
    (OUT / 'selection.json').write_text(json.dumps(rec, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    for k, v in rec['outputs_sha256'].items():
        print(v, k)
    for r in rec['selection']:
        print(r['method'], r['path'], '<-', r['call_head_original'][:70].replace('\n', ' '))
