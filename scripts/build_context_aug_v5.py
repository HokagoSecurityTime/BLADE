"""[S4] Permission-context augmentation for oas_code inputs (no training, no inference here, test_v6 never read). Revision 2 (stop 1 feedback).
Static analyzer. Entry = the record's handler (meta.source_locations[0] + controller_text only; other source_locations, the frozen label and
the draft/evidence/review columns are never read). Permission-related callees (auth|permission|access|role|member|owner|admin|can*|has*|
is*|check*|ensure*|require*|permissible) are resolved by FOLLOWING THE HANDLER FILE'S import/require statements (relative paths, project
aliases, re-exports, Ghost getter/property requires); a name that cannot be resolved through imports is NOT added (counted as unresolved).
Depth <= 2 (helper bodies are resolved through their own file's imports). Authentication-only helpers (api key / token / session / hash /
password ...) are dropped unless their body contains an authorization check; one-line type signatures and .d.ts are dropped; the same
definition (overlapping range) is never added twice; Rocket.Chat omnichannel/livechat files are allowed only for livechat routes.
Permission definition files: Ghost rolePermissions rows for the objects the handler checks (docName or canThis(...).action.object) +
model permissible + canThis core; Rocket.Chat permission->roles rows ONLY for permission names that literally occur in the handler or in a
kept helper, roomAccessValidators + validator bodies, permissionsRequired handling; Umami can* definitions + ROLES/PERMISSIONS/ROLE_PERMISSIONS.
Input = existing v3.0.1 oas_code_user + "\n\n[관련 권한 코드]\n" + blocks. Two budgets: ctx4096 and ctx6144 (chat prompt tokens incl. the
system prompt). Helper blocks are dropped from the tail in call order (count recorded; the last kept block may be cut by lines).
Stages: build --set test_v5|test_v30 ; stop12 (30-record precision sheet + 10-record samples)."""
from __future__ import annotations
import argparse, hashlib, json, os, random, re, statistics as st
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / 'reports/eval/context_aug_v5'; OSS = ROOT / 'datasets/blade/raw/opensource'; VULN = ROOT / 'datasets/blade/raw/vuln_apis'
PROMPT = ROOT / 'training/data/prompts/policy_label_v3.0.1.md'; PROMPT_SHA = 'd0913c27b5de185e7dd5734c111cb731f45e28ebca81fed787ff3914d02833ef'
SETS = {'test_v5': dict(test=ROOT / 'datasets/blade/processed/test_v5.jsonl', inputs=ROOT / 'training/lora/data_v5/test_v5_inputs.jsonl', manifest=ROOT / 'datasets/blade/processed/data_v5/test_v5_manifest.json', key='datasets/blade/processed/test_v5.jsonl'),
        'test_v30': dict(test=ROOT / 'datasets/blade/processed/test_v30.jsonl', inputs=ROOT / 'training/lora/data_v5/test_v30_inputs.jsonl', sha='9bd47216575afc602b03afa20e617308dd9a97476c94e67a117eb17009afd5e2')}
BUDGETS = {'ctx4096': 4096, 'ctx6144': 6144}
MAX_BLOCK_LINES, MAX_DEPTH, MAX_HELPERS, MAX_REEXPORT = 40, 2, 15, 4
EXT = {'.js': 'js', '.ts': 'js', '.mjs': 'js', '.cjs': 'js', '.py': 'py', '.go': 'go', '.java': 'java'}
PROJECTS = {
    'ghost': dict(root=OSS / 'TryGhost_Ghost', dirs=['ghost/core/server'], special='ghost', alias={}),
    'rocketchat': dict(root=OSS / 'RocketChat_Rocket.Chat', dirs=['apps/meteor/app', 'apps/meteor/server', 'apps/meteor/lib', 'packages/authorization/src', 'packages/models/src'], special='rocketchat',
                       alias={'@rocket.chat/authorization': 'packages/authorization/src/index.ts', '@rocket.chat/models': 'packages/models/src/index.ts'}),
    'umami': dict(root=OSS / 'umami-software_umami', dirs=['src'], special='umami', alias={'@/': 'src/'}),
    'juice-shop': dict(root=VULN / 'juice-shop', dirs=['routes', 'lib', 'models', 'server.ts'], alias={}),
    'Pixi': dict(root=VULN / 'Pixi', dirs=['api', 'app'], alias={}),
    'DVWS-node': dict(root=VULN / 'DVWS-node', dirs=['src'], alias={}),
    'VAmPI': dict(root=VULN / 'VAmPI', dirs=['api_views', 'models', 'app.py', 'config.py'], alias={}),
    'crAPI': dict(root=VULN / 'crAPI', dirs=['services/identity/src/main', 'services/community', 'services/workshop', 'services/gateway-service'], alias={}),
}
NAME_PAT = re.compile(r'(auth|permission|access|role|member|owner|admin|permissible|^can[A-Z_]|^has[A-Z_]|^is[A-Z_]|^check|^ensure|^require)', re.I)
STRONG_AUTHZ_NAME = re.compile(r'(permission|role|member|owner|admin|access|^can[A-Z_]|permissible|authoriz)', re.I)
AUTH_NAME = re.compile(r'(authenticat|apikey|api_key|token|session|hash|crypto|password|bearer|jwt|cookie|login|logout|credential|secret|sign[-_]?in|otp|2fa|totp|csrf|^checkAuth$|^authoriz\w*Api$)', re.I)
# an authorization *condition* in a body: role/permission/owner/member checks or a 403-style denial; plain "authorized/unauthorized" wording is not enough
AUTHZ_BODY = re.compile(r'(hasPermission|hasRole|hasAtLeastOne|hasAll|permission|\broles?\b|isOwner|\bowner|member|canAccess|canThis|permissible|isAdmin|\badmin\b|403|Forbidden)', re.I)
STRONG_AUTHZ_BODY = re.compile(r'(hasPermission|hasRole|hasAtLeastOne|hasAll|canAccess|canThis|permissible|403|Forbidden|\.role\b|roles\.|isOwner|owner_id|ownerId|member)', re.I)
NOISE = {'isArray', 'isEmpty', 'isString', 'isNull', 'isNil', 'isFunction', 'isObject', 'isUndefined', 'isNumber', 'isBoolean', 'isDate', 'isPlainObject', 'isEqual', 'isInteger', 'isFinite', 'hasOwnProperty', 'isNaN',
         'isNotEmpty', 'isDefined', 'isValid', 'isinstance', 'issubclass', 'isdigit', 'isalpha', 'hasattr', 'isNullOrUndefined', 'isPresent', 'isBlank', 'isTruthy', 'isFalsy', 'require', 'isRequired', 'isMatch', 'isBefore', 'isAfter',
         'isNode', 'isBuffer', 'isNative', 'isArrayLike', 'isSymbol', 'isMap', 'isSet', 'isRegExp', 'isError', 'isElement', 'isLength', 'isObjectLike', 'isSafeInteger', 'isTypedArray', 'isArguments', 'isDeepEqual', 'isOk', 'isVisible',
         'isNew', 'isModified', 'auth', 'required', 'roles', 'Authorization', 'authorized', 'unauthorized', 'skipAuth', 'authToken', 'authRequired', 'role', 'member', 'owner', 'admin', 'access', 'permission', 'permissions',
         'membership', 'ownerId', 'userId', 'adminId', 'isTruthy', 'isMeteorError', 'check', 'Match', 'isObjectId', 'isValidObjectId'}
KEYWORDS = {'if', 'for', 'while', 'switch', 'catch', 'function', 'return', 'await', 'async', 'else', 'new', 'typeof', 'throw', 'case', 'with', 'super', 'constructor', 'export', 'import', 'const', 'let', 'var', 'class', 'this', 'get', 'set'}
DEF_PATS = {
    'js': [re.compile(r'^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)\s*\('),
           re.compile(r'^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*(?::[^=]*)?=\s*'),
           re.compile(r'^\s*(?:(?:public|private|protected|static|async|readonly|override|get|set)\s+)*([A-Za-z_$][\w$]*)\s*(?:<[^>]*>)?\([^)]*\)\s*(?::\s*[^{;=]+)?\{\s*$'),
           re.compile(r'^\s*(?:async\s+)?([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{\s*$'),
           re.compile(r"^\s*'?([A-Za-z_$][\w$\-. ]*)'?\s*:\s*(?:async\s+)?(?:function\b|\([^)]*\)\s*(?::[^=]*)?=>|\{\s*$|\[\s*$|require\()"),
           re.compile(r'^\s*(?:export\s+)?class\s+([A-Za-z_$][\w$]*)\b'),
           re.compile(r'^\s*(?:module\.)?exports\.([A-Za-z_$][\w$]*)\s*=')],
    'py': [re.compile(r'^\s*(?:async\s+)?def\s+(\w+)\s*\('), re.compile(r'^\s*class\s+(\w+)\b'), re.compile(r'^(\w+)\s*=\s*')],
    'go': [re.compile(r'^func\s+(?:\([^)]*\)\s*)?(\w+)\s*\(')],
    'java': [re.compile(r'^\s*(?:(?:public|private|protected|static|final|synchronized|abstract|default)\s+)*[\w<>\[\],.? ]+\s+(\w+)\s*\([^)]*\)\s*(?:throws[\w, .]+)?\s*\{'), re.compile(r'^\s*@(\w+)')],
}
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Repo:
    def __init__(self, key):
        cfg = PROJECTS[key]; self.key = key; self.root = cfg['root']; self.special = cfg.get('special'); self.alias = cfg.get('alias', {}); self.files = {}; self.index = defaultdict(list); self._imp = {}
        assert self.root.exists(), self.root
        for d in cfg['dirs']:
            p = self.root / d
            if p.is_file(): self._add(p)
            elif p.is_dir():
                for dp, dns, fns in os.walk(p):
                    dns[:] = [x for x in dns if x not in ('node_modules', 'test', 'tests', '__tests__', 'dist', 'build', '.git', 'migrations', 'fixtures', 'public', 'client')]
                    for fn in fns:
                        if Path(fn).suffix in EXT and not re.search(r'\.(spec|test|stories|d|generated)\.[jt]s$|^contract\.', fn): self._add(Path(dp) / fn)
        for rel, lines in self.files.items():
            lang = EXT[Path(rel).suffix]
            for i, line in enumerate(lines):
                for pat in DEF_PATS[lang]:
                    m = pat.match(line)
                    if m and m.group(1) not in KEYWORDS: self.index[m.group(1).strip()].append((rel, i))

    def _add(self, p):
        try: self.files[p.relative_to(self.root).as_posix()] = p.read_text(encoding='utf-8', errors='replace').splitlines()
        except OSError: pass

    def lang(self, rel): return EXT[Path(rel).suffix]

    def defs_in(self, rel, name, lo=0, hi=None):
        return [i for r, i in self.index.get(name, []) if r == rel and i >= lo and (hi is None or i < hi)]

    # ---- module resolution
    def resolve_module(self, from_rel, spec):
        """Module specifier -> repo-relative file, or None (external package / not in the indexed tree)."""
        if spec in self.alias: return self.alias[spec] if self.alias[spec] in self.files else None
        for a, t in self.alias.items():
            if a.endswith('/') and spec.startswith(a): spec = t + spec[len(a):]; break
        else:
            if spec.startswith('.'): spec = (Path(from_rel).parent / spec).as_posix()
            elif not spec.startswith('src/') and not spec.startswith('packages/'): return None
        spec = os.path.normpath(spec).replace('\\', '/')
        for c in (spec, spec + '.ts', spec + '.js', spec + '.tsx', spec + '/index.ts', spec + '/index.js', spec + '.py'):
            if c in self.files: return c
        return None

    def imports(self, rel):
        """local name -> (module spec, exported name | '*' | 'default')."""
        if rel in self._imp: return self._imp[rel]
        text = '\n'.join(self.files[rel]); out = {}; lang = self.lang(rel)
        if lang == 'js':
            for m in re.finditer(r'^\s*import\s+(?:type\s+)?(.*?)\s+from\s+[\'"]([^\'"]+)[\'"]', text, re.M | re.S):
                clause, spec = m.group(1).strip(), m.group(2)
                if clause.startswith('type '): continue
                for part in re.split(r',(?![^{]*\})', clause):
                    part = part.strip()
                    if not part: continue
                    if part.startswith('{'):
                        for item in part.strip('{} \n').split(','):
                            item = item.strip()
                            if not item or item.startswith('type '): continue
                            mm = re.match(r'(\w+)(?:\s+as\s+(\w+))?', item)
                            if mm: out[mm.group(2) or mm.group(1)] = (spec, mm.group(1))
                    elif part.startswith('* as '): out[part[5:].strip()] = (spec, '*')
                    elif re.match(r'^\w+$', part): out[part] = (spec, 'default')
            for m in re.finditer(r'^\s*(?:const|let|var)\s+(\{[^}]*\}|\w+)\s*=\s*require\([\'"]([^\'"]+)[\'"]\)(?:\.(\w+))?', text, re.M):
                clause, spec, prop = m.group(1), m.group(2), m.group(3)
                if clause.startswith('{'):
                    for item in clause.strip('{} \n').split(','):
                        mm = re.match(r'\s*(\w+)(?:\s*:\s*(\w+))?', item)
                        if mm and mm.group(1): out[mm.group(2) or mm.group(1)] = (spec, mm.group(1))
                else: out[clause] = (spec, prop or '*')
        elif lang == 'py':
            for m in re.finditer(r'^\s*from\s+([\w.]+)\s+import\s+(.+)$', text, re.M):
                for item in m.group(2).strip('() ').split(','):
                    mm = re.match(r'\s*(\w+)(?:\s+as\s+(\w+))?', item)
                    if mm: out[mm.group(2) or mm.group(1)] = (m.group(1).replace('.', '/'), mm.group(1))
            for m in re.finditer(r'^\s*import\s+([\w.]+)(?:\s+as\s+(\w+))?', text, re.M): out[m.group(2) or m.group(1).split('.')[-1]] = (m.group(1).replace('.', '/'), '*')
        self._imp[rel] = out; return out

    def find_export(self, rel, name, depth=0):
        """('def', rel, line) | ('module', rel) | None — follows re-exports and getter/property requires."""
        if rel not in self.files or depth > MAX_REEXPORT: return None
        if name == 'default':
            for i, l in enumerate(self.files[rel]):
                m = re.match(r'^\s*export\s+default\s+(?:async\s+)?(?:function\s*\*?\s*(\w+)|class\s+(\w+)|(\w+)\s*;?\s*$)', l)
                if m:
                    n = m.group(1) or m.group(2) or m.group(3); d = self.defs_in(rel, n)
                    return ('def', rel, d[0]) if d else ('def', rel, i)
                if re.match(r'^\s*export\s+default\s+', l): return ('def', rel, i)
            mm = re.search(r'module\.exports\s*=\s*require\([\'"]([^\'"]+)[\'"]\)', '\n'.join(self.files[rel]))
            if mm:
                t = self.resolve_module(rel, mm.group(1)); return ('module', t) if t else None
            return ('module', rel)
        d = self.defs_in(rel, name)
        if d:
            i = d[0]; l = self.files[rel][i]
            m = re.match(r"^\s*'?" + re.escape(name) + r"'?\s*:\s*require\([\'\"]([^\'\"]+)[\'\"]\)", l)  # name: require('./x')
            if m:
                t = self.resolve_module(rel, m.group(1)); return ('module', t) if t else None
            if re.match(r'^\s*get\s+' + re.escape(name) + r'\s*\(', l):  # get name() { return ... require('./x') ... }
                a, b = self.block(rel, i); m2 = re.search(r'require\([\'"]([^\'"]+)[\'"]\)', '\n'.join(self.files[rel][a:b]))
                if m2:
                    t = self.resolve_module(rel, m2.group(1)); return ('module', t) if t else None
            m = re.match(r'^\s*(?:export\s+)?(?:const|let|var)\s+' + re.escape(name) + r'\s*(?::[^=]*)?=\s*(\w+)\s*;?\s*$', l)  # const a = b (alias)
            if m and m.group(1) != name:
                imp = self.imports(rel).get(m.group(1))
                if imp:
                    t = self.resolve_module(rel, imp[0]); return self.find_export(t, imp[1] if imp[1] != '*' else name, depth + 1) if t else None
            return ('def', rel, i)
        text = '\n'.join(self.files[rel])
        for m in re.finditer(r'^\s*export\s*\{([^}]*)\}\s*from\s*[\'"]([^\'"]+)[\'"]', text, re.M):
            for item in m.group(1).split(','):
                mm = re.match(r'\s*(\w+)(?:\s+as\s+(\w+))?', item)
                if mm and (mm.group(2) or mm.group(1)) == name:
                    t = self.resolve_module(rel, m.group(2)); return self.find_export(t, mm.group(1), depth + 1) if t else None
        for m in re.finditer(r'^\s*export\s+\*\s+from\s+[\'"]([^\'"]+)[\'"]', text, re.M):
            t = self.resolve_module(rel, m.group(1)); r = self.find_export(t, name, depth + 1) if t else None
            if r: return r
        m = re.search(r'module\.exports\s*=\s*require\([\'"]([^\'"]+)[\'"]\)', text)
        if m:
            t = self.resolve_module(rel, m.group(1)); return self.find_export(t, name, depth + 1) if t else None
        imp = self.imports(rel).get(name)  # imported and re-exported as `export { name }` or used as a value
        if imp and re.search(r'^\s*export\s*\{[^}]*\b' + re.escape(name) + r'\b', text, re.M):
            t = self.resolve_module(rel, imp[0]); return self.find_export(t, imp[1] if imp[1] != '*' else name, depth + 1) if t else None
        return None

    def resolve_chain(self, rel, parts):
        """Resolve a dotted chain (e.g. mw.authAdminApi, auth.authenticate.x, api.giftLinks.browse, hasPermissionAsync) from file rel.
        Returns ('def', rel, line) or (None, reason)."""
        first = parts[0]; imp = self.imports(rel).get(first); cur = None
        if imp:
            mod = self.resolve_module(rel, imp[0])
            if not mod: return (None, f'external:{imp[0]}')
            cur = ('module', mod) if imp[1] == '*' else self.find_export(mod, imp[1])
            if not cur: return (None, f'no export {imp[1]} in {mod}')
        elif self.defs_in(rel, first): cur = ('def', rel, self.defs_in(rel, first)[0])
        else: return (None, 'not imported / not defined in file')
        for p in parts[1:]:
            if cur[0] == 'module': cur = self.find_export(cur[1], p)
            elif cur[0] == 'def':
                r, i = cur[1], cur[2]; a, b = self.block(r, i); d = self.defs_in(r, p, a, b)
                if d:
                    l = self.files[r][d[0]]; m = re.match(r"^\s*'?" + re.escape(p) + r"'?\s*:\s*require\([\'\"]([^\'\"]+)[\'\"]\)", l)
                    if m:
                        t = self.resolve_module(r, m.group(1)); cur = ('module', t) if t else None
                    else: cur = ('def', r, d[0])
                else:
                    g = re.search(r'\bget\s+' + re.escape(p) + r'\s*\(', '\n'.join(self.files[r][a:b]))
                    cur = self.find_export(r, p) if g else None
            if not cur: return (None, f'member {p} not found')
        if cur[0] == 'module': return (None, 'resolves to a module, not a definition')
        return cur

    def block(self, rel, i):
        lines = self.files[rel]; lang = self.lang(rel)
        if lang == 'py':
            ind = len(lines[i]) - len(lines[i].lstrip()); j = i + 1
            while j < len(lines) and (not lines[j].strip() or len(lines[j]) - len(lines[j].lstrip()) > ind): j += 1
            while j > i + 1 and not lines[j - 1].strip(): j -= 1
            return i, j
        depth = 0; opened = False; j = i
        while j < len(lines) and j < i + 400:
            s = re.sub(r'//.*$|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`', '', lines[j])
            for ch in s:
                if ch in '{[(': depth += 1; opened = opened or ch in '{['
                elif ch in '}])': depth -= 1
            if opened and depth <= 0: return i, j + 1
            if not opened and (s.rstrip().endswith(';') or j > i + 8): return i, min(j + 1, len(lines))
            j += 1
        return i, min(j, len(lines))

    def enclosing(self, rel, line_no):
        cands = sorted(((i, name) for name, locs in self.index.items() for r, i in locs if r == rel and i <= line_no), reverse=True)
        for i, name in cands:
            a, b = self.block(rel, i)
            if b > line_no: return name, a, b
        return None


def clip(lines):
    lines = [l for l in lines if l.strip() and not re.match(r'^\s*(//|#|/\*|\*|\*/)', l)]
    if len(lines) <= MAX_BLOCK_LINES: return lines, False
    return lines[:MAX_BLOCK_LINES - 8] + ['      ...'] + lines[-6:], True


def chains_in(text):
    """Dotted call/reference chains whose segments include a permission-related name, in first-appearance order."""
    seen, out = set(), []
    for m in re.finditer(r'@?\b([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\b', text):
        chain = m.group(1); parts = chain.split('.')
        if parts[0] in ('this', 'req', 'res', 'frame', 'request', 'response', 'console', 'Promise', 'Object', 'Array', 'JSON', 'Math', 'String', 'Number', '_', 'self', 'cls', 'options', 'params', 'body', 'query'): continue
        parts = [p for p in parts if p not in KEYWORDS]
        if not parts: continue
        hit = [p for p in parts if NAME_PAT.search(p) and p not in NOISE and len(p) >= 4 and not re.search(r'(Props|Params|Schema|Response|Request|Error|Type|Types|Interface|Model|Dto|DTO|Enum)$', p)]
        if not hit: continue
        key = '.'.join(parts)
        if key in seen: continue
        seen.add(key); out.append(parts)
    return out


def rc_perm_names(text):
    out = []
    for m in re.finditer(r'(?:hasPermissionAsync|hasAtLeastOnePermissionAsync|hasAllPermissionAsync|hasPermission|permissionsRequired|hasAtLeastOnePermission|hasAllPermission|hasPermissionAsync)\s*[:(]([^;]{0,400})', text):
        out += [q for q in re.findall(r"'([a-z][a-z0-9\-]+)'", m.group(1)) if '-' in q and not q.startswith('error-')]
    return list(dict.fromkeys(out))


class Analyzer:
    def __init__(self, repo: Repo): self.repo = repo

    def run(self, handler_loc, controller_text, route_path=''):
        repo = self.repo; blocks = []; have = []; order = 0; self.in_input = set(); self.unresolved = []; self.excluded = Counter(); self.excluded_locs = {}; self.controller_text = controller_text
        livechat = bool(re.search(r'livechat|omnichannel', route_path, re.I))
        def add(rel, a, b, name, depth, kind, via=''):
            nonlocal order
            if rel not in repo.files: return None
            def ex(reason): self.excluded[reason] += 1; self.excluded_locs[(rel, a + 1)] = reason; return None
            if re.search(r'(^|/)(omnichannel|livechat)/', rel) and not livechat: return ex('omnichannel')
            for blk in blocks:  # same / overlapping definition already present
                if blk['file'] == rel and not (b <= blk['start'] - 1 or a >= blk['end']):
                    if kind != 'helper' and blk['kind'] == 'helper': blk['kind'] = kind; blk['name'] = name
                    return ex('duplicate')
            lines = repo.files[rel][a:b]; code = [l for l in lines if l.strip() and not re.match(r'^\s*(//|#|/\*|\*)', l)]
            if kind == 'helper':
                if len(code) <= 1 and '{' not in ''.join(code) and '=>' not in ''.join(code): return ex('type_signature')
                body = '\n'.join(code); last = name.split('.')[-1]
                if AUTH_NAME.search(last) and not STRONG_AUTHZ_BODY.search(body): return ex('authentication')
                if not AUTHZ_BODY.search(body) and not STRONG_AUTHZ_NAME.search(last): return ex('no_authz_signal')
            if len(code) >= 2 and code[0].strip() in controller_text and code[1].strip() in controller_text: self.in_input.add(kind); self.excluded_locs[(rel, a + 1)] = 'in_input'; return None
            shown, cut = clip(lines); order += 1
            blk = dict(file=rel, start=a + 1, end=b, name=name, depth=depth, kind=kind, order=order, lines=len(lines), clipped=cut, via=via, text='\n'.join(shown)); blocks.append(blk); return blk
        # seed: handler definition (bounded) + the existing excerpt; files whose text the excerpt may come from
        seed = controller_text; hrel = None; ctx_files = []
        if handler_loc and handler_loc['file'] in repo.files:
            hrel = handler_loc['file']; a = handler_loc['start_line'] - 1; b = handler_loc.get('end_line', handler_loc['start_line'])
            enc = repo.enclosing(hrel, a)
            if enc and enc[2] - enc[1] > 150: enc = None
            seed += '\n' + '\n'.join(repo.files[hrel][(enc[1] if enc else a):(max(enc[2], b) if enc else b)]); ctx_files = [hrel]
        self.hrel = hrel; self.seed = seed
        # depth-1: resolve chains of the seed through the handler file's imports (and through files the chain text literally comes from)
        def resolve_from(files, parts):
            for f in files:
                r = repo.resolve_chain(f, parts)
                if r[0] == 'def': return r, f
            return (None, 'unresolved'), None
        frontier = []
        for parts in chains_in(seed):
            r, f = resolve_from(ctx_files, parts)
            if r[0] != 'def':  # the excerpt may be from another file (Ghost endpoint file): try files reachable from the handler whose text contains the chain
                for f2 in list(self.reachable(hrel))[:30]:
                    if '.'.join(parts) in '\n'.join(repo.files[f2]):
                        r2 = repo.resolve_chain(f2, parts)
                        if r2[0] == 'def': r, f = r2, f2; break
            if r[0] != 'def': self.unresolved.append('.'.join(parts) + f' [{r[1]}]'); continue
            frontier.append((r[1], r[2], '.'.join(parts), 1))
        self.resolved_names = set(); done = set()
        while frontier:
            rel, i, name, depth = frontier.pop(0)
            if (rel, i) in done: continue
            done.add((rel, i)); a, b = repo.block(rel, i); blk = add(rel, a, b, name, depth, 'helper'); self.resolved_names.add(name)
            if blk and depth < MAX_DEPTH:
                for parts in chains_in(blk['text']):
                    if '.'.join(parts) == name: continue
                    r = repo.resolve_chain(rel, parts)
                    if r[0] == 'def': frontier.append((r[1], r[2], '.'.join(parts), depth + 1))
                    else: self.unresolved.append('.'.join(parts) + f' (depth2 in {rel.split("/")[-1]}) [{r[1]}]')
        getattr(self, 'special_' + repo.special, lambda *a: None)(seed, blocks, add) if repo.special else None
        rank = {'perm_table': 0, 'permissible': 1, 'perm_flow': 2, 'helper': 3}
        blocks.sort(key=lambda b: (rank.get(b['kind'], 9), b['order']))
        helpers = [b for b in blocks if b['kind'] == 'helper']
        self.excluded['helper_cap'] += max(0, len(helpers) - MAX_HELPERS)
        self.seed = seed
        return [b for b in blocks if b['kind'] != 'helper'] + helpers[:MAX_HELPERS]

    def reachable(self, hrel):
        """Files imported by the handler file (one hop)."""
        if not hrel: return []
        out = []
        for spec, _ in set(self.repo.imports(hrel).values()):
            t = self.repo.resolve_module(hrel, spec)
            if t and t not in out: out.append(t)
        if self.repo.special == 'ghost':  # route -> api.<name>.<method> -> endpoints/<file>
            for m in re.finditer(r'api\.(\w+)\.\w+', self.controller_text):
                r = self.repo.resolve_chain(hrel, ['api', m.group(1)])
                if r[0] is None:
                    idx = 'ghost/core/server/api/endpoints/index.js'; fe = self.repo.find_export(idx, m.group(1))
                    if fe and fe[0] == 'module' and fe[1] not in out: out.append(fe[1])
        return out

    # ---- project permission definition files
    def ghost_objects(self):
        """Permission object types the handler checks: docName (excerpt or endpoint file) and canThis(ctx).action.object chains."""
        ct = self.controller_text; objs = []
        m = re.search(r"permissions:\s*\{[^}]*docName:\s*'(\w+)'", ct) or re.search(r"docName:\s*'(\w+)'", ct); doc = m.group(1) if m else None
        if not doc:
            for f in self.reachable(self.hrel):
                if f.startswith('ghost/core/server/api/endpoints/'):
                    mm = re.search(r"docName:\s*'(\w+)'", '\n'.join(self.repo.files[f]))
                    if mm: doc = mm.group(1); break
        sing = lambda d: {'pages': 'post', 'posts': 'post'}.get(d, d[:-3] + 'y' if d.endswith('ies') else d[:-1] if d.endswith('s') else d)
        if doc and re.search(r'permissions\s*:', ct): objs.append(sing(doc))
        objs += [o for _, o in re.findall(r'canThis\([^)]*\)\.(\w+)\.(\w+)\(', ct)]
        return list(dict.fromkeys(objs)), doc

    def special_ghost(self, seed, blocks, add):
        repo = self.repo; pd = 'ghost/core/server/services/permissions/permissions-data.ts'
        objs, doc = self.ghost_objects(); self.ghost_doc = doc
        if re.search(r'permissions:\s*false', self.controller_text) and 'canThis(' not in self.controller_text: self.excluded['ghost_permissions_false'] += 1; return  # endpoint declares no permission check
        if not objs or pd not in repo.files: return
        lines = repo.files[pd]; out = []; role = None; start = next((i for i, l in enumerate(lines) if l.startswith('export const permissions = {')), None)
        for obj in objs:
            for i, l in enumerate(lines):
                mo = re.match(rf'^  {obj}: (.*)$', l)
                if mo and start is not None and i < start + 60: out.append(f'permissions.{obj}: {mo.group(1)}')
                mr = re.match(r"^  '?([\w \-]+)'?: \{\s*$", l)
                if mr: role = mr.group(1)
                mo = re.match(rf'^    {obj}: (.*)$', l)
                if mo and role:
                    v = mo.group(1)
                    if v.endswith('['):
                        j = i + 1
                        while j < len(lines) and ']' not in lines[j]: v += ' ' + lines[j].strip(); j += 1
                        v += ' ' + lines[j].strip()
                    out.append(f'rolePermissions.{role}.{obj}: {v}')
        if out: blocks.append(dict(file=pd, start=1, end=len(lines), name='rolePermissions[' + ','.join(objs) + ']', depth=1, kind='perm_table', order=0, lines=len(out), clipped=False, via='docName/canThis', text='\n'.join(out)))
        for obj in objs:
            for rel in [f'ghost/core/server/models/{obj}.js'] + (['ghost/core/server/models/relations/authors.js'] if obj == 'post' else []):
                if rel in repo.files:
                    for i, l in enumerate(repo.files[rel]):
                        if re.match(r'^\s*(?:async\s+)?permissible\s*[:(]|^\s*permissible:\s*(?:async\s+)?function', l): a, b = repo.block(rel, i); add(rel, a, b, f'{obj}.permissible', 1, 'permissible', 'model'); break
        ct = 'ghost/core/server/services/permissions/can-this.js'
        if ct in repo.files:
            ls = repo.files[ct]; a = next((i for i, l in enumerate(ls) if 'const { isOwner }' in l), None); b = next((i for i, l in enumerate(ls) if 'TargetModel.permissible(' in l), None)
            if a is not None and b is not None: add(ct, a, b + 10, 'canThis(core)', 1, 'perm_flow', 'permissions service')

    def rc_table(self, kept_helpers):
        """Rocket.Chat permission -> roles rows for permission names that literally occur in the handler or a kept helper."""
        perms = 'apps/meteor/server/lib/authorization/constant/permissions.ts'
        names = rc_perm_names(self.seed) + [n for b in kept_helpers for n in rc_perm_names(b['text'])]
        if not names or perms not in self.repo.files: return None
        out = []; src = {n: 'handler' for n in rc_perm_names(self.seed)}
        for n in dict.fromkeys(names):
            for l in self.repo.files[perms]:
                if f"_id: '{n}'" in l: out.append(l.strip()); break
            else: out.append(f"// '{n}': not found in permissions.ts")
        return dict(file=perms, start=1, end=len(self.repo.files[perms]), name='permission→roles', depth=1, kind='perm_table', order=0, lines=len(out), clipped=False, via=','.join(f'{n}:{src.get(n, "helper")}' for n in dict.fromkeys(names)), text='\n'.join(out))

    def special_rocketchat(self, seed, blocks, add):
        repo = self.repo; pt = 'packages/authorization/src/canAccessRoom.ts'
        t = self.rc_table([b for b in blocks if b['kind'] == 'helper'])
        if t: blocks.append(t)
        if re.search(r'canAccessRoom', seed) and pt in repo.files:
            ls = repo.files[pt]; i = next((k for k, l in enumerate(ls) if 'roomAccessValidators' in l and '=' in l), None)
            if i is not None:
                a, b = repo.block(pt, i); add(pt, a, b, 'roomAccessValidators', 1, 'perm_flow', 'canAccessRoom')
                for n in dict.fromkeys(re.findall(r'\b(can\w+|is\w+|has\w+|validate\w*)\b', '\n'.join(ls[a:b]))):
                    r = repo.resolve_chain(pt, [n])
                    if r[0] == 'def': aa, bb = repo.block(r[1], r[2]); add(r[1], aa, bb, n, 2, 'perm_flow', 'roomAccessValidators')
        if 'permissionsRequired' in seed:
            rel = 'apps/meteor/server/api/api.helpers.ts'
            if rel in repo.files:
                ls = repo.files[rel]; k = next((k for k, l in enumerate(ls) if 'permissionsRequired' in l and ('hasAllPermission' in l or 'hasAtLeastOne' in l or 'if (' in l)), None); enc = repo.enclosing(rel, k) if k is not None else None
                if enc: add(rel, enc[1], enc[2], enc[0] + '(permissionsRequired)', 1, 'perm_flow', 'API.addRoute')

    def special_umami(self, seed, blocks, add):
        repo = self.repo; cs = 'src/lib/constants.ts'
        for b in blocks:
            if b['kind'] == 'helper' and b['file'].startswith('src/permissions/'): b['kind'] = 'perm_flow'
        text = seed + '\n'.join(b['text'] for b in blocks)
        if ('hasPermission' in text or re.search(r'\bcan[A-Z]\w+\(', text)) and cs in repo.files:
            for n in ('ROLES', 'PERMISSIONS', 'ROLE_PERMISSIONS'):
                for rel, k in repo.index.get(n, []):
                    if rel == cs: a, b = repo.block(rel, k); add(rel, a, b, n, 2, 'perm_table', 'hasPermission')


def render(blocks):
    return '\n\n'.join(f"FILE {b['file']}:{b['start']}-{b['end']} [{b['kind']} {b['name']}]\n{b['text']}" for b in blocks)


def fit(tok, system, user, blocks, max_tokens, refresh=None):
    n_tok = lambda u: len(tok.apply_chat_template([{'role': 'system', 'content': system}, {'role': 'user', 'content': u}], tokenize=True, add_generation_prompt=True))
    base = n_tok(user); head = n_tok(user + '\n\n[관련 권한 코드]\n'); est = lambda ks: head + sum(len(tok(render([b])).input_ids) + 2 for b in ks)
    kept = list(blocks); dropped = 0; cut = False
    def shrink():
        nonlocal dropped, cut
        last = kept[-1]; ls = last['text'].split('\n')
        if len(ls) > 12: kept[-1] = dict(last, text='\n'.join(ls[:len(ls) // 2]) + '\n      ...', clipped=True); cut = True
        else: kept.pop(); dropped += 1
    while kept and est(kept) > max_tokens: shrink()
    if refresh: kept[:] = refresh(kept)
    u = user + ('\n\n[관련 권한 코드]\n' + render(kept) if kept else '\n\n[관련 권한 코드]\n(없음)'); total = n_tok(u)
    while total > max_tokens and kept:
        shrink(); u = user + ('\n\n[관련 권한 코드]\n' + render(kept) if kept else '\n\n[관련 권한 코드]\n(없음)'); total = n_tok(u)
    return u, base, total, kept, dropped, cut


def load(set_key):
    s = SETS[set_key]
    want = json.loads(s['manifest'].read_text(encoding='utf-8'))['sha256'][s['key']] if 'manifest' in s else s['sha']
    assert sha(s['test']) == want, f'{set_key} differs from the frozen hash'; assert sha(PROMPT) == PROMPT_SHA
    return {r['id']: r for r in rd(s['test'])}, rd(s['inputs'])


def project_of(r):
    return r['meta'].get('project') or {'juice-shop': 'juice-shop', 'crAPI': 'crAPI', 'Pixi': 'Pixi', 'DVWS-node': 'DVWS-node', 'VAmPI': 'VAmPI'}.get(r.get('service'))


def analyze(set_key, ids=None):
    """Run the analyzer only (no tokenizer): id -> (record, input row, analyzer, blocks)."""
    test, inputs = load(set_key); repos = {}; out = {}
    for inp in inputs:
        r = test[inp['id']]
        if ids and r['id'] not in ids: continue
        if not r.get('controller_text') or 'oas_code_user' not in inp: continue
        pj = project_of(r)
        if pj not in PROJECTS: out[r['id']] = (r, inp, None, []); continue
        repos.setdefault(pj, Repo(pj)); an = Analyzer(repos[pj]); locs = r['meta'].get('source_locations') or []
        out[r['id']] = (r, inp, an, an.run(locs[0] if locs else None, r['controller_text'], r['path']))
    return out


def build(set_key, ids=None, write=True):
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained('unsloth/Qwen2.5-7B-Instruct-bnb-4bit', local_files_only=True); system = PROMPT.read_text(encoding='utf-8')
    res = analyze(set_key, ids); rows = {k: [] for k in BUDGETS}; stats = {k: [] for k in BUDGETS}
    for rid, (r, inp, an, blocks) in res.items():
        pj = project_of(r)
        for bk, mt in BUDGETS.items():
            if an is None: rows[bk].append(inp); stats[bk].append(dict(id=rid, project=pj, skipped='no repo config')); continue
            refresh = None
            if an.repo.special == 'rocketchat':
                def refresh(kept, an=an):
                    t = an.rc_table([b for b in kept if b['kind'] == 'helper']); rest = [b for b in kept if b['kind'] != 'perm_table' or b['name'] != 'permission→roles']
                    return ([t] if t else []) + rest
            user, base, total, kept, dropped, cut = fit(tok, system, inp['oas_code_user'], blocks, mt, refresh)
            row = dict(inp); row['oas_code_user'] = user; row['ctx'] = dict(budget=mt, blocks=[{k: v for k, v in b.items() if k != 'text'} for b in kept], found=len(blocks), kept=len(kept), dropped=dropped, cut=cut, tokens_before=base, tokens_after=total)
            rows[bk].append(row)
            stats[bk].append(dict(id=rid, project=pj, method=r['method'], path=r['path'], found=len(blocks), kept=len(kept), dropped=dropped, cut=cut, tokens_before=base, tokens_after=total,
                                  kinds=dict(Counter(b['kind'] for b in kept)), kinds_found=dict(Counter(b['kind'] for b in blocks)), kinds_in_input=sorted(an.in_input), names=[b['name'] for b in kept],
                                  unresolved=an.unresolved, excluded=dict(an.excluded), ghost_doc=getattr(an, 'ghost_doc', None)))
    if write:
        (OUT / 'inputs').mkdir(parents=True, exist_ok=True)
        for bk in BUDGETS:
            with open(OUT / f'inputs/{set_key}_{bk}_inputs.jsonl', 'w', encoding='utf-8') as f:
                for row in rows[bk]: f.write(json.dumps(row, ensure_ascii=False) + '\n')
            (OUT / f'{set_key}_{bk}_stats.json').write_text(json.dumps(summarize(stats[bk], set_key, bk), ensure_ascii=False, indent=1), encoding='utf-8')
    return rows, stats


def summarize(stats, set_key, budget):
    s = [x for x in stats if 'skipped' not in x]; by = defaultdict(list)
    for x in s: by[x['project']].append(x)
    per = {}
    for pj, xs in by.items():
        ex = Counter()
        for x in xs: ex.update(x['excluded'])
        per[pj] = dict(n=len(xs), perm_table=sum('perm_table' in x['kinds'] for x in xs), perm_flow=sum('perm_flow' in x['kinds'] for x in xs), permissible=sum('permissible' in x['kinds'] for x in xs),
                       perm_table_in_input=sum('perm_table' in x['kinds_in_input'] for x in xs), perm_flow_in_input=sum('perm_flow' in x['kinds_in_input'] for x in xs), permissible_in_input=sum('permissible' in x['kinds_in_input'] for x in xs),
                       perm_any=sum(bool({'perm_table', 'perm_flow', 'permissible'} & (set(x['kinds']) | set(x['kinds_in_input']))) for x in xs),
                       helper=sum('helper' in x['kinds'] for x in xs), any_block=sum(x['kept'] > 0 for x in xs), perm_table_found_but_dropped=sum('perm_table' in x['kinds_found'] and 'perm_table' not in x['kinds'] for x in xs),
                       dropped_any=sum(x['dropped'] > 0 or x['cut'] for x in xs), blocks_found_mean=round(st.mean(x['found'] for x in xs), 2), blocks_kept_mean=round(st.mean(x['kept'] for x in xs), 2),
                       unresolved_records=sum(bool(x['unresolved']) for x in xs), unresolved_names=sum(len(x['unresolved']) for x in xs), excluded=dict(ex),
                       tokens_before_mean=round(st.mean(x['tokens_before'] for x in xs)), tokens_after_mean=round(st.mean(x['tokens_after'] for x in xs)), tokens_after_max=max(x['tokens_after'] for x in xs))
    return dict(set=set_key, budget=budget, n=len(s), skipped=len(stats) - len(s), per_project=per, records=stats)


# ---------------- stop 1-2: precision sheet (30 records) + 10 samples
def pick_ids(test, plan, seed=42):
    rng = random.Random(seed); pick = []
    for pj, k in plan:
        pool = sorted(i for i, r in test.items() if r['meta']['project'] == pj); pick += rng.sample(pool, k)
    return pick


ROOM_FAMILY = {'groups': 'private', 'channels': 'public', 'im': 'direct', 'dm': 'direct'}


def auto_class(b, record, new_reach=None, new_excluded=None, new_class=None):
    """direct / indirect / irrelevant / wrong_impl by rule (reviewed by hand afterwards; see stop12 report)."""
    path = record['path']; f = b['file']; key = (b['file'], b['start'])
    if re.search(r'(^|/)(omnichannel|livechat)/', f) and not re.search(r'livechat|omnichannel', path, re.I): return 'wrong_impl', 'omnichannel file for a non-livechat route'
    m = re.search(r'roomTypes/(\w+)\.ts', f)
    if m:
        fam = ROOM_FAMILY.get(path.split('/')[-1].split('.')[0])
        if fam and m.group(1) != fam: return 'wrong_impl', f'room type {m.group(1)} for a {fam} route'
    if new_reach is not None:  # old-analyzer block: judge by what the import-based resolver did with the same definition
        if key in new_reach and new_class and key in new_class: return new_class[key], 'same definition kept by the import-based analyzer'
        reason = (new_excluded or {}).get(key)
        if reason in ('authentication', 'no_authz_signal', 'type_signature'): return 'irrelevant', f'reached through imports but excluded: {reason}'
        if reason == 'duplicate': return 'indirect', 'overlapping copy of a kept definition'
        if reason == 'in_input': return 'direct', 'already in the handler excerpt'
        if key not in new_reach: return 'wrong_impl', 'not reachable through the handler file imports (global name match)'
    if b['name'] in ('canThis(core)', 'checkPermissions(permissionsRequired)', 'ROLES', 'PERMISSIONS'): return 'indirect', 'permission framework flow / constant, not the deciding condition'
    if b['kind'] in ('perm_table', 'permissible', 'perm_flow'): return 'direct', b['kind']
    if re.match(r'^(hasPermissionAsync|hasAllPermissionAsync|hasAtLeastOnePermissionAsync|hasRoleAsync|hasAnyRoleAsync|hasPermission)$', b['name'].split('.')[-1]): return 'indirect', 'thin wrapper around the authorization service'
    if b['name'].endswith('AdminApi') or b['name'] == 'tokenPermissionCheck': return 'indirect', 'route middleware chain / token scope guard'
    body = b.get('text', ''); authz = bool(AUTHZ_BODY.search(body))
    if authz and b['depth'] == 1: return 'direct', 'authorization check, called from the handler'
    if authz: return 'indirect', 'authorization check, depth 2'
    return 'irrelevant', 'no authorization condition in the body'


def stop12(args):
    import importlib.util, sys
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    test, _ = load('test_v5'); pick30 = pick_ids(test, (('ghost', 8), ('rocketchat', 14), ('umami', 8))); pick10 = pick_ids(test, (('ghost', 3), ('rocketchat', 4), ('umami', 3)))
    if args.reuse and all((OUT / f'inputs/test_v5_{bk}_inputs.jsonl').exists() and (OUT / f'test_v5_{bk}_stats.json').exists() for bk in BUDGETS):
        rows = {bk: rd(OUT / f'inputs/test_v5_{bk}_inputs.jsonl') for bk in BUDGETS}; summ = {bk: json.loads((OUT / f'test_v5_{bk}_stats.json').read_text(encoding='utf-8')) for bk in BUDGETS}; stats = {bk: summ[bk]['records'] for bk in BUDGETS}
    else:
        rows, stats = build('test_v5', write=True)  # full 283 for both budgets
        summ = {bk: summarize(stats[bk], 'test_v5', bk) for bk in BUDGETS}
    new = analyze('test_v5', ids=set(pick30))
    # old analyzer (pre-feedback snapshot) for the before/after comparison
    old_path = Path(args.old) if args.old else None; old_blocks = {}
    if old_path and old_path.exists():
        spec = importlib.util.spec_from_file_location('ctx_old', old_path); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        repos = {}
        for rid in pick30:
            r = test[rid]; pj = r['meta']['project']; repos.setdefault(pj, mod.Repo(pj)); an = mod.Analyzer(repos[pj]); locs = r['meta']['source_locations']
            old_blocks[rid] = an.run(locs[0], r['controller_text'])
    kept4096 = {x['id']: x for x in stats['ctx4096'] if 'skipped' not in x}; rows4096 = {x['id']: x for x in rows['ctx4096']}
    cls = dict(new={}, old={}); sheet = []
    for rid in pick30:
        r, inp, an, blocks = new[rid]; reach = {(b['file'], b['start']) for b in blocks} | set(an.excluded_locs); new_class = {}
        kept = [b for b in blocks if any(k['file'] == b['file'] and k['start'] == b['start'] for k in rows4096[rid]['ctx']['blocks'])]
        for b in kept:
            c, why = auto_class(b, r); new_class[(b['file'], b['start'])] = c; sheet.append(dict(ver='new', id=rid, project=r['meta']['project'], method=r['method'], path=r['path'], kind=b['kind'], name=b['name'], loc=f"{b['file']}:{b['start']}-{b['end']}", depth=b['depth'], auto=c, why=why))
        for b in blocks:  # found but dropped by the ctx4096 budget: classified too (they are kept under ctx6144 or not at all)
            if (b['file'], b['start']) not in new_class: new_class[(b['file'], b['start'])] = auto_class(b, r)[0]
        for b in old_blocks.get(rid, []):
            c, why = auto_class(b, r, new_reach=reach, new_excluded=an.excluded_locs, new_class=new_class); sheet.append(dict(ver='old', id=rid, project=r['meta']['project'], method=r['method'], path=r['path'], kind=b['kind'], name=b['name'], loc=f"{b['file']}:{b['start']}-{b['end']}", depth=b['depth'], auto=c, why=why))
    (OUT / 'stop12_precision.json').write_text(json.dumps(dict(sample30=pick30, sheet=sheet), ensure_ascii=False, indent=1), encoding='utf-8')
    render_precision(sheet, pick30, summ)
    # 10 samples re-print (ctx4096 and ctx6144 blocks)
    s = ['# S4 정지 지점 1-2: 10건 입력 샘플 재출력 (개선 후) — 2026-11-03', '', '같은 10건(seed 42: Ghost 3 · Rocket.Chat 4 · Umami 3). 각 건에 ctx4096 블록 원문과 ctx6144에서 추가로 유지된 블록 이름을 적었다.', '']
    r6 = {x['id']: x for x in rows['ctx6144']}
    for rid in pick10:
        r = test[rid]; row = rows4096[rid]; c = row['ctx']; c6 = r6[rid]['ctx']; blk = row['oas_code_user'].split('[관련 권한 코드]', 1)[1]
        extra = [b for b in c6['blocks'] if not any(k['file'] == b['file'] and k['start'] == b['start'] for k in c['blocks'])]
        s += [f"### {rid} — {r['meta']['project']} {r['method']} {r['path']}", '', f"ctx4096: 발견 {c['found']} / 유지 {c['kept']} / 탈락 {c['dropped']} / 절단 {c['cut']} · 토큰 {c['tokens_before']} → {c['tokens_after']} · 미해석 {len(kept4096[rid]['unresolved'])}: {', '.join(kept4096[rid]['unresolved'][:6])}",
              f"ctx6144: 유지 {c6['kept']} / 탈락 {c6['dropped']} · 토큰 → {c6['tokens_after']} · 추가 유지: " + (', '.join(f"{b['kind']}:{b['name']}" for b in extra) or '(없음)'), '', '```', '[관련 권한 코드]' + blk.rstrip(), '```', '']
    (OUT / 'stop12_samples10.md').write_text('\n'.join(s) + '\n', encoding='utf-8')
    print(json.dumps({bk: {pj: {k: p[k] for k in ('n', 'perm_any', 'helper', 'unresolved_records', 'excluded', 'tokens_after_mean')} for pj, p in summ[bk]['per_project'].items()} for bk in BUDGETS}, ensure_ascii=False))


def rerender(args):
    """Re-apply stop12_manual_overrides.json to the saved sheet and rewrite stop12_precision.md (no recomputation)."""
    d = json.loads((OUT / 'stop12_precision.json').read_text(encoding='utf-8')); summ = {bk: json.loads((OUT / f'test_v5_{bk}_stats.json').read_text(encoding='utf-8')) for bk in BUDGETS}
    render_precision(d['sheet'], d['sample30'], summ)


def render_precision(sheet, pick30, summ):
    ov_path = OUT / 'stop12_manual_overrides.json'; overrides = json.loads(ov_path.read_text(encoding='utf-8')) if ov_path.exists() else {}
    for row in sheet:
        k = f"{row['ver']}|{row['id']}|{row['loc'].rsplit('-', 1)[0]}"; row['final'] = overrides.get(k, {}).get('class', row['auto']); row['note'] = overrides.get(k, {}).get('note', '')
    stats = {bk: summ[bk]['records'] for bk in BUDGETS}
    def table(ver):
        t = [f'| project | 블록 수 | 직접 관련 | 간접 | 무관 | 잘못된 구현 | 직접+간접 비율 |', '|---|---:|---:|---:|---:|---:|---:|']
        for pj in ('ghost', 'rocketchat', 'umami', '전체'):
            xs = [x for x in sheet if x['ver'] == ver and (pj == '전체' or x['project'] == pj)]; c = Counter(x['final'] for x in xs); n = len(xs)
            t.append(f"| {pj} | {n} | {c['direct']} | {c['indirect']} | {c['irrelevant']} | {c['wrong_impl']} | {((c['direct'] + c['indirect']) / n if n else 0):.0%} |")
        return t
    t = ['# S4 정지 지점 1-2: 분석기 정밀도 점검 (test_v5 30건, 개선 전/후) — 2026-11-03', '',
         '분류는 유지 블록(ctx4096 기준, 개선 후) / 개선 전 분석기(전역 이름 검색, 스크래치 보존본)의 유지 블록에 대해 규칙으로 1차 분류한 뒤 Claude(AI)가 블록 본문을 읽고 수정했다(stop12_manual_overrides.json에 수정 내역·사유). 정답 열은 읽지 않았다. 사람 확인은 아직 없다.',
         '직접 = 해당 엔드포인트의 인가 판단 조건(권한표·permissible·canAccessRoom·역할/소유자 검사)을 담은 블록. 간접 = 인가 흐름의 일부지만 결정 조건이 아닌 블록(깊이 2 호출, 권한 프레임워크 공통 코드). 무관 = 인증·검증·유틸 등 인가 조건이 없는 블록. 잘못된 구현 = 동명 다른 함수·다른 방 종류·omnichannel 파일 등 이 핸들러가 실제로 호출하지 않는 정의.', '',
         f"표본 30건(seed 42): Ghost 8 · Rocket.Chat 14 · Umami 8 — {', '.join(pick30)}", '',
         '## 개선 후 (import 경로 해석, 인증 제외, 권한표 행 필터)', '', *table('new'), '', '## 개선 전 (전역 이름 매칭)', '', *table('old'), '',
         '## 프로젝트별 집계 (test_v5 283 전체, 개선 후)', '']
    for bk in BUDGETS:
        t += [f'### {bk}', '', '| project | n | 권한표 신규 / 기존 | 권한 흐름 신규 / 기존 | permissible 신규 / 기존 | 권한 정의 1종 이상 | 헬퍼 추가 | 블록 1개 이상 | 잘림 건수 | 블록 발견/유지 평균 | 미해석 이름(건수/이름 수) | 제외 사유 | 토큰 전/후 평균 | 후 최대 |', '|---|---:|---|---|---|---:|---:|---:|---:|---|---|---|---|---:|']
        for pj, p in summ[bk]['per_project'].items():
            t.append(f"| {pj} | {p['n']} | {p['perm_table']} / {p['perm_table_in_input']} | {p['perm_flow']} / {p['perm_flow_in_input']} | {p['permissible']} / {p['permissible_in_input']} | {p['perm_any']} | {p['helper']} | {p['any_block']} | {p['dropped_any']} | {p['blocks_found_mean']} / {p['blocks_kept_mean']} | {p['unresolved_records']} / {p['unresolved_names']} | {', '.join(f'{k} {v}' for k, v in sorted(p['excluded'].items()))} | {p['tokens_before_mean']} / {p['tokens_after_mean']} | {p['tokens_after_max']} |")
        t.append('')
    gd = [x for x in stats['ctx4096'] if x.get('project') == 'ghost' and 'skipped' not in x]
    t += ['## Ghost docName 탐지', '', f"docName 확인 {sum(1 for x in gd if x['ghost_doc'])}/{len(gd)} (발췌 또는 엔드포인트 파일). 권한표 미포함 Ghost 건: " + ', '.join(f"{x['id']}({x['method']} {x['path']})" for x in gd if 'perm_table' not in x['kinds'] and 'perm_table' not in x['kinds_in_input']) + '.',
          '원인: gift_links는 엔드포인트가 docName 없이 `permissions(frame)` 함수에서 canThis(context).manage.gift_link / edit.post를 직접 호출한다 → canThis 체인에서 객체(gift_link, post)를 읽어 권한표를 만들도록 변경. 나머지 미포함 건은 permissions 설정이 없는 엔드포인트(인증 전용 라우트·authentication 계열)다.', '',
          '## 30건 블록 목록 (개선 후, ctx4096 유지 블록)', '', '| id | method path | kind | name | 위치 | depth | 1차 | 최종 | 비고 |', '|---|---|---|---|---|---:|---|---|---|']
    for x in sheet:
        if x['ver'] == 'new': t.append(f"| {x['id']} | {x['method']} {x['path']} | {x['kind']} | {x['name']} | {x['loc']} | {x['depth']} | {x['auto']} | {x['final']} | {x['note']} |")
    t += ['', '## 30건 블록 목록 (개선 전)', '', '| id | method path | kind | name | 위치 | depth | 1차 | 최종 | 비고 |', '|---|---|---|---|---|---:|---|---|---|']
    for x in sheet:
        if x['ver'] == 'old': t.append(f"| {x['id']} | {x['method']} {x['path']} | {x['kind']} | {x['name']} | {x['loc']} | {x['depth']} | {x['auto']} | {x['final']} | {x['note']} |")
    (OUT / 'stop12_precision.md').write_text('\n'.join(t) + '\n', encoding='utf-8')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('stage', choices=['build', 'stop12', 'rerender']); ap.add_argument('--set', default='test_v5'); ap.add_argument('--old', default=None); ap.add_argument('--reuse', action='store_true'); a = ap.parse_args()
    if a.stage == 'stop12': stop12(a)
    elif a.stage == 'rerender': rerender(a)
    else: _, stats = build(a.set); print(json.dumps({bk: summarize(stats[bk], a.set, bk)['per_project'] for bk in BUDGETS}, ensure_ascii=False))


if __name__ == '__main__': main()
