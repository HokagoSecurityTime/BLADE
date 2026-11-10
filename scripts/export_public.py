"""Export the two public repositories (project / dataset) from the internal BLADE checkout — copy, scan, git init.

Usage (PowerShell or Git Bash, from C:\\BLADE):
    python -X utf8 scripts/export_public.py --repo all --clean [--detect-secrets <path to detect-secrets exe>] [--redact-paths] [--commit-anyway]

What it does, per repository (export/project_manifest.txt -> C:\\BLADE_public\\blade-project,
export/dataset_manifest.txt -> C:\\BLADE_public\\bap7-dataset):
  1. Resolve the manifest against `git ls-files` (only tracked files are ever copied; .gitignore'd files cannot leak),
     always exclude the 32 originals listed in datasets/blade/processed/public/PUBLIC_EXCLUDE.txt, copy byte-for-byte.
  2. Leak checks on the copied tree:
       a. no file with the same basename or the same SHA-256 as a PUBLIC_EXCLUDE original;
       b. none of the 162 withheld code excerpts (withheld_manifest.json ids -> text read from the internal originals)
          appears in any file (raw, JSON-escaped, XML-escaped inside .xlsx);
       c. secrets / personal data: .env, *.db, JWT-like tokens, API-key patterns, Slack/Discord webhooks, JWT secret
          assignments, personal Windows paths (<USERPROFILE>), personal e-mail addresses (optionally detect-secrets);
       d. no file above 50 MB.
  3. `git init` (branch main) + first commit — only when every blocking check is clean, unless --commit-anyway.
  4. Report: <out>/export_report.json and <out>/export_report.md. Nothing is pushed.

The internal repository is read-only for this script. Redaction (--redact-paths) rewrites personal Windows paths in the
COPIES only and is off by default.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_EXCLUDE = ROOT / 'datasets/blade/processed/public/PUBLIC_EXCLUDE.txt'
WITHHELD_MANIFEST = ROOT / 'datasets/blade/processed/public/withheld_manifest.json'
DEFAULT_OUT = Path(r'C:\BLADE_public')
REPOS = {
    'project': dict(manifest='export/project_manifest.txt', dirname='BLADE'),
    'dataset': dict(manifest='export/dataset_manifest.txt', dirname='BLADE-dataset'),
}
SIZE_LIMIT = 50 * 1024 * 1024
BINARY_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.woff', '.woff2', '.ttf', '.mp4', '.pyc', '.zip', '.gz', '.tgz'}
PERSONAL_EMAIL_DOMAINS = {'gmail.com', 'naver.com', 'daum.net', 'hanmail.net', 'kakao.com', 'nate.com', 'outlook.com', 'hotmail.com',
                          'yahoo.com', 'icloud.com', 'protonmail.com', 'proton.me', 'me.com', 'live.com'}

# (category, regex, blocking) — content patterns for check (c)
SECRET_PATTERNS = [
    ('jwt_token', re.compile(r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'), True),
    ('openai_key', re.compile(r'\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}'), True),
    ('github_token', re.compile(r'\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{20,}'), True),
    ('aws_key', re.compile(r'\bAKIA[0-9A-Z]{16}\b'), True),
    ('slack_token', re.compile(r'\bxox[baprs]-[A-Za-z0-9-]{10,}'), True),
    ('google_key', re.compile(r'\bAIza[0-9A-Za-z_-]{35}\b'), True),
    ('huggingface_token', re.compile(r'\bhf_[A-Za-z0-9]{30,}\b'), True),
    ('private_key', re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY'), True),
    ('slack_webhook', re.compile(r'https?://hooks\.slack(?:-gov)?\.com/\S+'), True),
    ('slack_webhook_host_mention', re.compile(r'hooks\.slack\.com'), False),
    ('discord_webhook', re.compile(r'discord(?:app)?\.com/api/webhooks/\S+'), True),
    ('jwt_secret_assignment', re.compile(r'BLADE_JWT_SECRET\s*[=:]\s*["\']?([A-Za-z0-9_\-]{8,})'), True),
    # Windows user-profile paths only (C:\Users\<name>, C:/Users/<name>, /c/Users/<name>); API paths like "GET:/users/{id}" do not match.
    ('personal_path', re.compile(r'(?:(?<![A-Za-z0-9])[A-Za-z]:\\{1,2}Users\\{1,2}[^\\/\s"\'`)\]<>|]+|(?<![A-Za-z0-9/])[A-Za-z]:/Users/[^/\s"\'`)\]<>|]+|<USERPROFILE>/\s"\'`)\]<>|]+)'), True),
    ('bearer_token', re.compile(r'Bearer\s+[A-Za-z0-9\-_.=]{40,}'), False),
    ('generic_secret_literal', re.compile(r'(?i)\b(?:api[_-]?key|secret|token|passw(?:or)?d)\b["\']?\s*[:=]\s*["\'][^"\'\s]{12,}["\']'), False),
]
EMAIL_RE = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
PLACEHOLDER_SECRETS = {'demo-only-change-me', 'change-me', 'changeme', 'your-secret', 'secret', 'example'}
# Same strict shape as the personal_path check: a real drive-letter Windows user-profile path only. "GET:/users/{id}" never matches.
REDACT_PATTERNS = [
    (re.compile(r'(?<![A-Za-z0-9])[A-Za-z]:\\{1,2}Users\\{1,2}[^\\/\s"\'`)\]<>|]+'), r'<USERPROFILE>'),
    (re.compile(r'(?<![A-Za-z0-9/])[A-Za-z]:/Users/[^/\s"\'`)\]<>|]+'), r'<USERPROFILE>'),
    (re.compile(r'<USERPROFILE>/\s"\'`)\]<>|]+'), r'<USERPROFILE>'),
]
DETECT_SECRETS_TYPE_OF = {'jwt_token': 'JSON Web Token', 'private_key': 'Private Key', 'aws_key': 'AWS Access Key', 'github_token': 'GitHub Token',
                          'slack_token': 'Slack Token', 'openai_key': 'OpenAI Token', 'jwt_secret_assignment': 'Secret Keyword'}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.run(['git', *args], cwd=str(cwd), capture_output=True, text=True, encoding='utf-8', errors='replace', check=True).stdout


def tracked_files() -> list[str]:
    out = subprocess.run(['git', 'ls-files', '-z'], cwd=str(ROOT), capture_output=True, check=True).stdout
    return [p.decode('utf-8') for p in out.split(b'\0') if p]


def parse_manifest(path: Path) -> tuple[list[str], list[str], list[tuple[str, str]]]:
    inc, exc, ren = [], [], []
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if '#' in line:  # trailing comment
            line = line.split('#', 1)[0].rstrip()
        if line.startswith('- '):
            exc.append(line[2:].strip())
        elif line.startswith('= '):
            src, dst = [s.strip() for s in line[2:].split('->', 1)]
            ren.append((src, dst))
        else:
            inc.append(line)
    return inc, exc, ren


def load_public_exclude() -> list[str]:
    return [l.strip() for l in PUBLIC_EXCLUDE.read_text(encoding='utf-8').splitlines() if l.strip() and not l.startswith('#')]


def matches_any(path: str, patterns: list[str]) -> str | None:
    for pat in patterns:
        if fnmatch.fnmatchcase(path, pat) or path == pat or (pat.endswith('/') and path.startswith(pat)):
            return pat
    return None


def select_files(manifest: Path, tracked: list[str], always_exclude: list[str]) -> tuple[list[tuple[str, str]], dict]:
    """Return [(source_rel, dest_rel)] and a selection summary."""
    inc, exc, ren = parse_manifest(manifest)
    tracked_set = set(tracked)
    chosen: dict[str, str] = {}
    excluded_by_manifest: dict[str, str] = {}
    excluded_by_public: list[str] = []
    for p in tracked:
        if not any(p == i or (i.endswith('/') and p.startswith(i)) for i in inc):
            continue
        if p in always_exclude:
            excluded_by_public.append(p)
            continue
        hit = matches_any(p, exc)
        if hit:
            excluded_by_manifest[p] = hit
            continue
        chosen[p] = p
    missing_inc = [i for i in inc if not i.endswith('/') and i not in tracked_set]
    for src, dst in ren:
        if src in always_exclude:
            raise SystemExit(f'manifest rename source is in PUBLIC_EXCLUDE: {src}')
        if src in tracked_set or (src.startswith('export/') and (ROOT / src).is_file()):
            chosen.pop(src, None)  # renamed, do not also copy under the original name
            chosen[f'{src} -> {dst}'] = dst
        else:
            missing_inc.append(src)
    pairs = []
    for key, dst in chosen.items():
        src = key.split(' -> ', 1)[0] if ' -> ' in key else key
        pairs.append((src, dst))
    summary = dict(include_rules=len(inc), exclude_rules=len(exc), renames=len(ren), excluded_by_public_exclude=excluded_by_public,
                   excluded_by_manifest=excluded_by_manifest, missing_sources=missing_inc)
    return pairs, summary


def copy_tree(pairs: list[tuple[str, str]], dest_root: Path) -> list[dict]:
    rows = []
    for src, dst in pairs:
        s = ROOT / src
        d = dest_root / dst
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(s, d)
        rows.append(dict(src=src, dst=dst, bytes=d.stat().st_size))
    return rows


def is_text_candidate(p: Path) -> bool:
    return p.suffix.lower() not in BINARY_EXT


def read_text_forms(p: Path) -> list[str]:
    """Return decoded text views of a file: the file itself; for .xlsx every zip member (raw + XML-unescaped)."""
    if p.suffix.lower() == '.xlsx':
        forms = []
        try:
            with zipfile.ZipFile(p) as z:
                for name in z.namelist():
                    if name.endswith(('.xml', '.rels')):
                        raw = z.read(name).decode('utf-8', errors='replace')
                        forms.append(raw)
                        forms.append(html.unescape(raw))
        except zipfile.BadZipFile:
            pass
        return forms
    if not is_text_candidate(p):
        return []
    return [p.read_bytes().decode('utf-8', errors='replace')]


def redact_paths(dest_root: Path, files: list[dict]) -> list[dict]:
    changed = []
    for row in files:
        p = dest_root / row['dst']
        if not is_text_candidate(p) or p.suffix.lower() == '.xlsx':
            continue
        raw = p.read_bytes()
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            continue
        new, n_total = text, 0
        for rx, repl in REDACT_PATTERNS:
            new, n = rx.subn(repl, new)
            n_total += n
        if n_total:
            p.write_bytes(new.encode('utf-8'))
            changed.append(dict(file=row['dst'], replacements=n_total))
    return changed


# ---------------------------------------------------------------- checks
def withheld_texts() -> dict[str, list[str]]:
    """id -> [controller_text variants] for the 162 withheld records, read from the internal originals."""
    m = json.loads(WITHHELD_MANIFEST.read_text(encoding='utf-8'))
    wanted: dict[str, set[str]] = {}
    for rec in m['records']:
        for f in rec['files']:
            wanted.setdefault(f['file'], set()).add(rec['id'])
    texts: dict[str, list[str]] = {}
    for rel, ids in wanted.items():
        p = ROOT / rel
        if not p.is_file():
            continue
        with open(p, encoding='utf-8') as fh:
            for line in fh:
                if not line.strip():
                    continue
                r = json.loads(line)
                if r.get('id') in ids:
                    t = r.get('controller_text') or ''
                    if t.strip():
                        texts.setdefault(r['id'], [])
                        if t not in texts[r['id']]:
                            texts[r['id']].append(t)
    return texts


def search_forms(text: str) -> list[str]:
    forms = {text, text.strip(), json.dumps(text, ensure_ascii=False)[1:-1], json.dumps(text, ensure_ascii=True)[1:-1]}
    return [f for f in forms if len(f) >= 20]


def check_withheld(dest_root: Path, files: list[dict], texts: dict[str, list[str]]) -> dict:
    needles = []  # (id, form)
    long_lines = []  # (id, line) warnings
    for rid, variants in texts.items():
        for t in variants:
            for f in search_forms(t):
                needles.append((rid, f))
            for ln in {l.strip() for l in t.splitlines() if len(l.strip()) >= 80}:
                long_lines.append((rid, ln))
                long_lines.append((rid, json.dumps(ln, ensure_ascii=False)[1:-1]))
    hits, line_hits = [], []
    for row in files:
        p = dest_root / row['dst']
        for view in read_text_forms(p):
            found = sorted({rid for rid, f in needles if f in view})
            if found:
                hits.append(dict(file=row['dst'], ids=found))
            lfound = sorted({rid for rid, l in long_lines if l in view})
            lfound = [r for r in lfound if r not in found]
            if lfound:
                line_hits.append(dict(file=row['dst'], ids=lfound))
            if found or lfound:
                break
    return dict(withheld_ids=len(texts), needles=len(needles), full_text_hits=hits, long_line_hits_warning=line_hits)


def check_public_exclude(dest_root: Path, files: list[dict], originals: list[str]) -> dict:
    paths = set(originals)
    names = {Path(o).name: o for o in originals}
    hashes = {}
    for o in originals:
        p = ROOT / o
        if p.is_file():
            hashes[sha256_file(p)] = o
    name_hits, hash_hits, basename_warn = [], [], []
    for row in files:
        p = dest_root / row['dst']
        if row['dst'] in paths:  # same relative path as an excluded original
            name_hits.append(row['dst'])
        elif p.name in names:  # same basename in another directory — informational
            basename_warn.append(dict(file=row['dst'], excluded_original=names[p.name]))
        h = sha256_file(p)
        row['sha256'] = h
        if h in hashes:
            hash_hits.append(dict(file=row['dst'], same_as=hashes[h]))
    return dict(originals=len(originals), originals_hashed=len(hashes), name_hits=name_hits, hash_hits=hash_hits, basename_only_warning=basename_warn)


def check_secrets(dest_root: Path, files: list[dict], author_emails: set[str]) -> dict:
    file_hits = []  # blocking by filename
    pattern_hits: dict[str, list[dict]] = {}
    email_block, email_warn = [], {}
    for row in files:
        p = dest_root / row['dst']
        name = p.name.lower()
        if (name == '.env' or (name.startswith('.env.') and name != '.env.example') or name.endswith(('.db', '.sqlite', '.sqlite3', '.pem', '.key'))):
            file_hits.append(row['dst'])
        forms = read_text_forms(p)
        for view in (['\n'.join(forms)] if forms else []):
            for cat, rx, blocking in SECRET_PATTERNS:
                ms = rx.findall(view)
                if cat == 'jwt_secret_assignment':
                    ms = [m for m in ms if m.lower() not in PLACEHOLDER_SECRETS]
                if ms:
                    samples = sorted({(m if isinstance(m, str) else m[0]) for m in ms})[:3]
                    pattern_hits.setdefault(cat, []).append(dict(file=row['dst'], count=len(ms), blocking=blocking,
                                                                 samples=[s[:12] + '…' if cat in ('jwt_token', 'openai_key', 'github_token', 'aws_key', 'slack_token', 'google_key', 'huggingface_token', 'bearer_token') else s[:120] for s in samples]))
            for em in set(EMAIL_RE.findall(view)):
                dom = em.rsplit('@', 1)[1].lower()
                if em.lower() in author_emails or dom in PERSONAL_EMAIL_DOMAINS:
                    email_block.append(dict(file=row['dst'], email=em))
                else:
                    email_warn.setdefault(em, set()).add(row['dst'])
    blocking_categories = sorted({c for c, hs in pattern_hits.items() if any(h['blocking'] for h in hs)})
    warn_emails = sorted(((em, len(fs)) for em, fs in email_warn.items()), key=lambda x: -x[1])
    return dict(file_name_hits=file_hits, pattern_hits=pattern_hits, blocking_categories=blocking_categories,
                personal_email_hits=email_block, other_emails_warning=[dict(email=e, files=n) for e, n in warn_emails])


def check_sizes(dest_root: Path, files: list[dict]) -> dict:
    big = [dict(file=r['dst'], bytes=r['bytes']) for r in files if r['bytes'] > SIZE_LIMIT]
    return dict(limit_bytes=SIZE_LIMIT, hits=big)


def run_detect_secrets(exe: Path, dest_root: Path) -> dict:
    cmd = [str(exe), 'scan', '--all-files', '--disable-plugin', 'HexHighEntropyString', '--disable-plugin', 'Base64HighEntropyString', '.']
    r = subprocess.run(cmd, cwd=str(dest_root), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0 and not r.stdout.strip():
        return dict(error=r.stderr[-2000:])
    data = json.loads(r.stdout)
    results = data.get('results', {})
    by_type: dict[str, int] = {}
    rows = []
    for f, items in results.items():
        for it in items:
            by_type[it['type']] = by_type.get(it['type'], 0) + 1
            rows.append(dict(file=f.replace('\\', '/').lstrip('./'), type=it['type'], line=it.get('line_number')))
    blocking = [r_ for r_ in rows if r_['type'] != 'Secret Keyword']
    return dict(version=data.get('version'), plugins=[p.get('name') for p in data.get('plugins_used', [])], by_type=by_type,
                findings=rows, blocking_findings=blocking)


# ---------------------------------------------------------------- git
def git_identity() -> tuple[str, str]:
    name = subprocess.run(['git', 'config', 'user.name'], cwd=str(ROOT), capture_output=True, text=True).stdout.strip()
    email = subprocess.run(['git', 'config', 'user.email'], cwd=str(ROOT), capture_output=True, text=True).stdout.strip()
    return name, email


def git_init_commit(dest_root: Path, repo_key: str, source_commit: str, message_extra: str) -> str:
    name, email = git_identity()
    env = dict(os.environ, GIT_AUTHOR_NAME=name, GIT_AUTHOR_EMAIL=email, GIT_COMMITTER_NAME=name, GIT_COMMITTER_EMAIL=email)
    run = lambda *a: subprocess.run(['git', *a], cwd=str(dest_root), env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', check=True)
    run('init', '-q', '-b', 'main')
    run('config', 'core.autocrlf', 'false')
    run('add', '-A')
    msg = (f'Initial public export ({REPOS[repo_key]["dirname"]}) from internal commit {source_commit[:12]}\n\n'
           f'Built by scripts/export_public.py with export/{repo_key}_manifest.txt. License-restricted code excerpts are withheld '
           f'(see datasets/blade/processed/public/withheld_manifest.json). {message_extra}\n')
    run('commit', '-q', '-m', msg)
    return run('rev-parse', 'HEAD').stdout.strip()


# ---------------------------------------------------------------- report
def md_list(items: list, limit: int = 60) -> str:
    if not items:
        return '- (없음)\n'
    out = ''.join(f'- {json.dumps(i, ensure_ascii=False) if not isinstance(i, str) else i}\n' for i in items[:limit])
    if len(items) > limit:
        out += f'- … 외 {len(items) - limit}건 (JSON 보고서 참조)\n'
    return out


def write_report(out_root: Path, report: dict) -> None:
    (out_root / 'export_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    lines = [f"# 공개 저장소 export 보고서 ({report['built_utc']})", '', f"내부 커밋: `{report['source_commit']}` · 출력 루트: `{report['out_root']}`", '']
    for key, rep in report['repos'].items():
        lines += [f"## {key} → `{rep['dest']}`", '',
                  f"- 파일 {rep['file_count']}개, {rep['total_bytes']:,} bytes ({rep['total_bytes'] / 1048576:.1f} MiB)",
                  f"- PUBLIC_EXCLUDE로 자동 제외: {len(rep['selection']['excluded_by_public_exclude'])}개 · manifest 제외 규칙으로 제외: {len(rep['selection']['excluded_by_manifest'])}개 · 누락 원본: {rep['selection']['missing_sources']}",
                  f"- 경로 redaction: {len(rep.get('redactions', []))}개 파일" + (' (옵션 미사용)' if not rep.get('redact_enabled') else ''),
                  f"- 판정: **{'CLEAN' if rep['clean'] else 'BLOCKED'}** · git 커밋: {rep.get('commit') or '(없음)'}", '',
                  '### a. PUBLIC_EXCLUDE 이름·해시 대조', md_list(rep['checks']['a_public_exclude']['name_hits'] + rep['checks']['a_public_exclude']['hash_hits']),
                  f"### b. 제한 코드 162건 본문 대조 (id {rep['checks']['b_withheld']['withheld_ids']}개, 대조 문자열 {rep['checks']['b_withheld']['needles']}개)",
                  md_list(rep['checks']['b_withheld']['full_text_hits']),
                  '긴 줄(80자 이상) 단위 경고(차단 아님):', md_list(rep['checks']['b_withheld']['long_line_hits_warning']),
                  '### c. 비밀값·개인정보']
        c = rep['checks']['c_secrets']
        lines += ['파일 이름 기준(.env, *.db, *.pem, *.key):', md_list(c['file_name_hits'])]
        for cat, hs in sorted(c['pattern_hits'].items()):
            lines += [f"`{cat}` ({'차단' if hs[0]['blocking'] else '경고'}, {len(hs)}개 파일):", md_list([dict(file=h['file'], count=h['count'], samples=h['samples']) for h in hs])]
        lines += ['개인 이메일(차단):', md_list(c['personal_email_hits']), '그 외 이메일(경고, 상위 30):', md_list(c['other_emails_warning'][:30], 30)]
        ds = rep['checks'].get('detect_secrets')
        if ds:
            lines += ['detect-secrets:', (f"- 오류: {ds['error']}" if 'error' in ds else f"- 유형별: {ds['by_type']} · 차단 후보 {len(ds['blocking_findings'])}건"), md_list(ds.get('blocking_findings', []), 40)]
        lines += ['### d. 50MB 초과', md_list(rep['checks']['d_size']['hits']), '']
    (out_root / 'export_report.md').write_text('\n'.join(lines), encoding='utf-8')


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', choices=['project', 'dataset', 'all'], default='all')
    ap.add_argument('--out', type=Path, default=DEFAULT_OUT)
    ap.add_argument('--clean', action='store_true', help='remove the target repo directory first')
    ap.add_argument('--redact-paths', action='store_true', help='rewrite personal Windows paths in the copies (off by default)')
    ap.add_argument('--detect-secrets', type=Path, default=None, help='path to a detect-secrets executable (optional)')
    ap.add_argument('--commit-anyway', action='store_true', help='git init + commit even when a blocking check hit')
    ap.add_argument('--no-git', action='store_true')
    ap.add_argument('--allow', action='append', default=[], metavar='CATEGORY',
                    help='waive a blocking secret category after review (e.g. jwt_token, jwt_secret_assignment, personal_email); repeatable')
    ap.add_argument('--allow-path', action='append', default=[], metavar='GLOB',
                    help='waive every blocking finding in files matching this glob (repo-relative); repeatable')
    args = ap.parse_args()

    tracked = tracked_files()
    always_exclude = load_public_exclude()
    source_commit = git('rev-parse', 'HEAD').strip()
    author_emails = {e.strip().lower() for e in git('log', '--format=%ae').splitlines() if e.strip()}
    author_emails.add(git_identity()[1].lower())
    texts = withheld_texts()
    args.out.mkdir(parents=True, exist_ok=True)
    report = dict(built_utc=datetime.now(timezone.utc).isoformat(), source_commit=source_commit, out_root=str(args.out), repos={})

    for key in (['project', 'dataset'] if args.repo == 'all' else [args.repo]):
        spec = REPOS[key]
        dest = args.out / spec['dirname']
        if dest.exists():
            if not args.clean:
                raise SystemExit(f'{dest} exists; pass --clean to rebuild it')
            assert dest.resolve().parent == args.out.resolve(), dest
            # git marks pack files read-only; clear the bit before unlinking (Windows raises PermissionError otherwise)
            shutil.rmtree(dest, onexc=lambda fn, p, e: (os.chmod(p, 0o666), fn(p)))
        dest.mkdir(parents=True)
        pairs, selection = select_files(ROOT / spec['manifest'], tracked, always_exclude)
        files = copy_tree(pairs, dest)
        redactions = redact_paths(dest, files) if args.redact_paths else []
        checks = dict(
            a_public_exclude=check_public_exclude(dest, files, always_exclude),
            b_withheld=check_withheld(dest, files, texts),
            c_secrets=check_secrets(dest, files, author_emails),
            d_size=check_sizes(dest, files),
        )
        if args.detect_secrets:
            checks['detect_secrets'] = run_detect_secrets(args.detect_secrets, dest)
        a, b, c, d = checks['a_public_exclude'], checks['b_withheld'], checks['c_secrets'], checks['d_size']
        waived_path = lambda f: any(fnmatch.fnmatchcase(f, g) for g in args.allow_path)
        blocking_cats = [cat for cat in c['blocking_categories'] if cat not in args.allow
                         and any(not waived_path(h['file']) for h in c['pattern_hits'][cat])]
        email_block = [] if 'personal_email' in args.allow else [h for h in c['personal_email_hits'] if not waived_path(h['file'])]
        waived_types = {DETECT_SECRETS_TYPE_OF[c_] for c_ in args.allow if c_ in DETECT_SECRETS_TYPE_OF}
        ds_block = [] if 'detect_secrets' in args.allow else [f for f in checks.get('detect_secrets', {}).get('blocking_findings', [])
                                                              if not waived_path(f['file']) and f['type'] not in waived_types]
        checks['waivers'] = dict(allow=args.allow, allow_path=args.allow_path, blocking_categories_after_waiver=blocking_cats,
                                 personal_email_after_waiver=len(email_block), detect_secrets_after_waiver=len(ds_block))
        blocked = bool(a['name_hits'] or a['hash_hits'] or b['full_text_hits'] or c['file_name_hits'] or blocking_cats or email_block or d['hits'] or ds_block)
        rep = dict(dest=str(dest), manifest=spec['manifest'], file_count=len(files), total_bytes=sum(r['bytes'] for r in files), selection=selection,
                   redact_enabled=args.redact_paths, redactions=redactions, checks=checks, clean=not blocked, files=files)
        if not args.no_git and (not blocked or args.commit_anyway):
            rep['commit'] = git_init_commit(dest, key, source_commit, 'Checks: ' + ('clean' if not blocked else 'BLOCKED (committed with --commit-anyway)'))
        report['repos'][key] = rep
        print(f"[{key}] files={len(files)} bytes={rep['total_bytes']:,} clean={not blocked} commit={rep.get('commit')}")
    write_report(args.out, report)
    print(f"report: {args.out / 'export_report.md'}")
    sys.exit(0 if all(r['clean'] for r in report['repos'].values()) else 3)


if __name__ == '__main__':
    main()
