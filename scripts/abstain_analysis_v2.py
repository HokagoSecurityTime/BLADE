"""LoRA v2 over-abstention analysis (part 1). Uses only the existing final-adapter prediction files (seed 42/43/44) on test_v30 and train_v2 records.
Read-only: data-v1/data-v2 hashes asserted at start and end; no training, no API calls.
Outputs: reports/eval/lora_v2/abstain_analysis.md, reports/eval/lora_v2/abstain_intersection.csv"""
from __future__ import annotations
import csv, json, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'scripts'))
from data_v1_guard import assert_data_v1
from data_v2_guard import assert_data_v2
from eval_v30 import segments, L, MANUAL, table
D = ROOT / 'reports/eval/lora_v2'; SEEDS = (42, 43, 44); CONDS = ('oas', 'oas_code'); SEGS = ('route_only', 'repository_spec', 'synthetic')
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]

# authorization-check patterns in handler code (the user's kinds: 403/Forbidden, owner/user-id comparison, role/admin check; authentication-only kept apart)
PAT = {
    'status_403': re.compile(r'\b403\b|FORBIDDEN|[Ff]orbidden|AccessDenied|access_denied|PermissionDenied|permission[ _]denied|[Nn]ot [Aa]llowed|NotAllowed|HTTP_403'),
    'owner_cmp': re.compile(r'(user_?[iI]d|owner_?[iI]d|author_?[iI]d|created_?[bB]y|\.owner\b|\.user\b|ctx\.Doer\.ID|Doer\.ID|\.UserID|\.OwnerID|PosterID|AssigneeID|\.author\b)\s*(==|!=|===|!==|\.equals\(|<>|\bis\s+not\b|\bis\b(?!\s*(None|null)))'
                            r'|(==|!=|===|!==)\s*(req\.user\b|request\.user\b|current_?[uU]ser\b|ctx\.Doer\.ID|Doer\.ID|user_?[iI]d|owner_?[iI]d|principal\.(id|getId|user|username)|caller\.(id|user))'
                            r'|(filter|where|find\w*|get\w*|query\w*)\s*\([^)]*\b(user_?[iI]d|owner_?[iI]d|author_?[iI]d)\b'
                            r'|\b(IsOwner|isOwner|is_owner|checkOwner|check_owner|owner_filter)\b'),
    'role_admin': re.compile(r'\b(role|roles|is_?admin|isAdmin|hasRole|has_role|PreAuthorize|Secured|RolesAllowed|permission|permissions|is_staff|is_superuser|require_role|checkAdmin|only_admin|IsAdminUser|IsSiteAdmin|Permission|Perm|AccessMode|CanWrite|CanRead|HasAccess)\b'
                            r'|req(Admin|SiteAdmin|OrgOwnership|OrgMembership|TeamMembership|RepoWriter|RepoReader|AnyRepoReader|RepoAdmin|PackageAccess|SelfOrAdmin|ToolsAccess|Owner|WebhooksEnabled)\b'
                            r'|IsOrg(Member|Owner)|IsUserRepoAdmin|IsUserOrgOwner|\badmin\b'),
    'auth_only': re.compile(r'\b(login_required|jwt_required|requireAuth|ensureAuthenticated|passport\.authenticate|verifyToken|verify_token|authenticate|isAuthenticated|IsAuthenticated|reqToken|get_jwt_identity|Depends\(get_current_user\)|current_user|401|UNAUTHORIZED|Unauthorized)\b'),
}
RAT = {  # rationale clusters (model text, seed 42 first available)
    'relation_unspecified': re.compile(r'관계가 (명시|명확|불확실|정의)|관계나 접근 조건'),
    'condition_unclear': re.compile(r'접근 조건이 (명확|확정|불확실|정의|복합)|조건이 명확하지|명시되지 않아 보류'),
    'multi_condition': re.compile(r'단일 라벨|여러 (독립 )?조건|복합'),
    'auth_only_noted': re.compile(r'인증만|인증 후|인증이 필요하지만|인증 과정'),
    'memorized_synthetic': re.compile(r'Conflicting|denyAll|deliberately unresolved|external authorization|external policy', re.I),
}

def strip_summary_comments(code: str) -> str:
    # Gitea extracts carry explanatory '//' comments for summarized middleware (the sudo() note mentions 403). Keep only the chain line with middleware names.
    return '\n'.join(l for l in (code or '').split('\n') if not l.lstrip().startswith('//') or 'route middleware chain' in l)

def authz(code: str):
    code = strip_summary_comments(code)
    hits = {k: bool(p.search(code or '')) for k, p in PAT.items()}
    hits['authz_any'] = hits['status_403'] or hits['owner_cmp'] or hits['role_admin']
    return hits

def sig(r):
    s = r.get('controller_signals') or {}
    if isinstance(s, str):
        try: s = json.loads(s.replace("'", '"').replace('None', 'null').replace('True', 'true').replace('False', 'false'))
        except Exception: s = {}
    return s if isinstance(s, dict) else {}

def excerpt(code, n=260):
    code = re.sub(r'\s+', ' ', (code or '').strip()); return code[:n] + ('…' if len(code) > n else '')

def rationale(pred_rows, i):
    for s in SEEDS:
        p = pred_rows[s].get(i)
        if p and p.get('prediction'): return s, (p['prediction'].get('rationale') or '')[:220]
    return None, ''

def rat_cluster(text):
    for k, p in RAT.items():
        if p.search(text or ''): return k
    return 'other' if text else 'unparsed'

def rate_table(I, pop, keyf, cats, header0):
    rows = []
    for c in cats:
        n = sum(keyf(i) == c for i in I); m = sum(keyf(i) == c for i in pop)
        if m or n: rows.append([c, n, m, f'{n / m:.0%}' if m else '-'])
    return table(rows, [header0, '교집합 보류', '모집단(정답 구체)', '보류율'])

def main():
    g1, g2 = assert_data_v1('start'), assert_data_v2('start')
    test = rd(ROOT / 'datasets/blade/processed/test_v30.jsonl'); T = {r['id']: r for r in test}; meta, seg = segments()
    segname = {i: 'synthetic' if i in set(seg['synthetic']) else ('route_only' if i in set(seg['vuln_route_only']) else 'repository_spec') for i in seg['all']}
    code_hits = {i: authz(T[i].get('controller_text') or '') for i in T}; has_code = {i: bool((T[i].get('controller_text') or '').strip()) for i in T}
    azname = lambda i: ('인가 검사 있음' if code_hits[i]['authz_any'] else ('인증만' if code_hits[i]['auth_only'] else '인가·인증 없음')) if has_code[i] else '코드 없음'
    out = '# LoRA v2 과보류(over-abstention) 원인 분석 — final 어댑터 seed 42·43·44, test_v30, 기존 예측 파일만 사용\n\n'
    out += "data-v1·data-v2 해시 assert 통과(시작·종료). 학습·API 호출 없음. test_v30 불변. '과보류' = 예측 manual_review_required ∧ 정답이 구체 label. 코드 인가 검사 판정은 controller_text 정규식(403/Forbidden·owner/user id 비교·role/admin 검사; 인증만 있는 패턴은 '인증만'으로 분리)이며 Gitea 미들웨어 이름(reqAdmin·reqOrgOwnership 등)은 role/admin으로, reqToken은 인증만으로 센다. Gitea 발췌의 설명 주석(sudo 403 문구 등)은 제거 후 판정. 정규식은 scripts/abstain_analysis_v2.py PAT. '보류율' = 교집합 보류 건수 / 그 범주의 정답 구체 모집단(해당 조건 채점 대상).\n\n"
    csv_rows = []; summary = {}; facts = {}
    for cond in CONDS:
        preds = {s: {r['id']: r for r in rd(D / f'lora_v2_seed{s}/eval/predictions_{cond}_lora_v2_s{s}_final.jsonl')} for s in SEEDS}
        lab = lambda r: r['prediction']['label'] if r.get('prediction') else 'output_error'
        pop = [i for i in preds[42] if meta[i]['label'] != MANUAL]  # concrete-truth population scored in this condition
        over = {s: {i for i, r in preds[s].items() if lab(r) == MANUAL and meta[i]['label'] != MANUAL} for s in SEEDS}
        inter = set.intersection(*over.values()); union = set.union(*over.values()); n_conc = len(pop)
        main_ids = set(seg['oas_main_v2']) if cond == 'oas' else set(preds[42])
        out += f'## {cond}: 과보류 건수\n\n'
        out += table([[f'seed {s}', len(over[s]), f"{len(over[s]) / n_conc:.1%}", len(over[s] & main_ids)] for s in SEEDS] + [['교집합(3 seed 모두)', len(inter), f'{len(inter) / n_conc:.1%}', len(inter & main_ids)], ['합집합(1개 이상)', len(union), f'{len(union) / n_conc:.1%}', len(union & main_ids)]],
                     ['집합', '건수', '정답 구체 대비', '주지표 구간 내']) + f'\n정답 구체 label 건수 {n_conc}(채점 대상 {len(preds[42])}). 주지표 구간: oas는 route_only 제외 160건, oas_code는 265건 전체. 교집합/합집합 = {len(inter) / len(union):.0%}.\n\n'
        summary[cond] = dict(per_seed={s: len(over[s]) for s in SEEDS}, inter=len(inter), union=len(union), n_concrete=n_conc)
        I = sorted(inter)
        out += f'### {cond}: 교집합 {len(I)}건 교차표 (보류율 = 범주별 교집합/모집단)\n\n'
        out += '**구간별**\n\n' + rate_table(I, pop, lambda i: segname[i], SEGS, '구간') + '\n'
        out += '**서비스별**\n\n' + rate_table(I, pop, lambda i: T[i]['service'], [s for s, _ in Counter(T[i]['service'] for i in pop).most_common()], 'service') + '\n'
        out += '**정답 label별**\n\n' + rate_table(I, pop, lambda i: meta[i]['label'], [l for l in L if l != MANUAL], '정답 label') + '\n'
        out += '**코드 인가 검사 유무별** (oas 조건에서는 모델이 코드를 보지 않음; 레코드 성격 참고용)\n\n' + rate_table(I, pop, azname, ['인가 검사 있음', '인증만', '인가·인증 없음', '코드 없음'], '코드 상태') + '\n'
        out += '**구간 × 코드 인가 검사** (교집합 건수 / 모집단)\n\n' + table([[sg] + [f"{sum(segname[i] == sg and azname(i) == a for i in I)} / {sum(segname[i] == sg and azname(i) == a for i in pop)}" for a in ('인가 검사 있음', '인증만', '인가·인증 없음', '코드 없음')] for sg in SEGS], ['구간', '인가 검사 있음', '인증만', '인가·인증 없음', '코드 없음']) + '\n'
        out += '**정답 label × 코드 인가 검사** (교집합 건수 / 모집단; 패턴 열은 교집합 내 건수)\n\n' + table([[l] + [f"{sum(meta[i]['label'] == l and azname(i) == a for i in I)} / {sum(meta[i]['label'] == l and azname(i) == a for i in pop)}" for a in ('인가 검사 있음', '인증만', '인가·인증 없음')] + [sum(meta[i]['label'] == l and code_hits[i][k] for i in I) for k in ('owner_cmp', 'role_admin', 'status_403')] for l in L if l != MANUAL and any(meta[i]['label'] == l for i in pop)],
                                             ['정답 label', '인가 검사 있음', '인증만', '인가·인증 없음', 'owner/user id 비교', 'role/admin', '403/Forbidden']) + '\n'
        cs = Counter((bool(sig(T[i]).get('has_auth_check')), code_hits[i]['authz_any']) for i in I)
        out += '**추출 시그널(controller_signals.has_auth_check) 대조(교집합)**: ' + ', '.join(f'has_auth_check={a} ∧ 정규식 인가={b}: {n}' for (a, b), n in sorted(cs.items(), key=lambda x: -x[1])) + '\n\n'
        rc = Counter(rat_cluster(rationale(preds, i)[1]) for i in I)
        out += '**모델 rationale 유형(교집합, seed 42 기준)**\n\n' + table(rc.most_common(), ['유형', '건수']) + '\n'
        facts[cond] = dict(rate_by_az={a: (sum(azname(i) == a for i in I), sum(azname(i) == a for i in pop)) for a in ('인가 검사 있음', '인증만', '인가·인증 없음', '코드 없음')}, rate_by_seg={sg: (sum(segname[i] == sg for i in I), sum(segname[i] == sg for i in pop)) for sg in SEGS},
                           rate_by_label={l: (sum(meta[i]['label'] == l for i in I), sum(meta[i]['label'] == l for i in pop)) for l in L if l != MANUAL}, rate_by_service={s: (sum(T[i]['service'] == s for i in I), sum(T[i]['service'] == s for i in pop)) for s in {T[i]['service'] for i in pop}}, rat=rc)
        out += f'### {cond}: 유형별 대표 5건 (구간 × 인가 검사 유무; id 정렬 상위 5)\n\n'
        for sg in SEGS:
            for az in (True, False):
                ids = [i for i in I if segname[i] == sg and code_hits[i]['authz_any'] == az]
                if not ids: continue
                out += f'**{sg} · 인가 검사 {"있음" if az else "없음"} ({len(ids)}건)**\n\n'
                for i in ids[:5]:
                    s, rat = rationale(preds, i); hits = [k for k in ('status_403', 'owner_cmp', 'role_admin', 'auth_only') if code_hits[i][k]]
                    out += f"- `{i}` {T[i]['service']} {T[i]['method']} {T[i]['path']} — 정답 **{meta[i]['label']}** · 패턴 {hits or '없음'}\n  - 코드: `{excerpt(T[i].get('controller_text')) or '(없음)'}`\n  - 모델 rationale(seed {s}): {rat or '(파싱 실패)'}\n"
                out += '\n'
        for i in I:
            s, rat = rationale(preds, i)
            csv_rows.append(dict(condition=cond, id=i, service=T[i]['service'], method=T[i]['method'], path=T[i]['path'], truth=meta[i]['label'], segment=segname[i], security_state=meta[i]['security_state'], code_state=azname(i), **{k: code_hits[i][k] for k in ('status_403', 'owner_cmp', 'role_admin', 'auth_only', 'authz_any')}, has_auth_check_signal=sig(T[i]).get('has_auth_check'), rationale_cluster=rat_cluster(rat), rationale_seed=s, rationale=rat))
        only = {s: over[s] - inter for s in SEEDS}
        out += f'seed별로만 보류된 건(합집합−교집합 {len(union - inter)}건): ' + ', '.join(f'seed {s} {len(only[s])}' for s in SEEDS) + '.\n\n'
    # test overall: code x truth
    code_ids = [i for i in T if has_code[i]]
    out += '## test_v30 전체: 코드 인가 검사 × 정답 (코드 있는 265건)\n\n' + table([[sg] + [f"{sum(segname[i] == sg and azname(i) == a for i in code_ids)} (manual {sum(segname[i] == sg and azname(i) == a and meta[i]['label'] == MANUAL for i in code_ids)})" for a in ('인가 검사 있음', '인증만', '인가·인증 없음')] for sg in SEGS], ['구간', '인가 검사 있음 (정답 manual)', '인증만 (정답 manual)', '인가·인증 없음 (정답 manual)']) + '\n'
    # train_v2 comparison
    train = rd(ROOT / 'datasets/blade/processed/train_v2.jsonl'); tr = []
    for r in train:
        src = 'gitea' if r['id'].startswith('gitea:') else ('synthetic' if r['meta'].get('source') == 'synthetic' else 'apisguru')
        code = r.get('controller_text') if src == 'gitea' else (sig(r).get('raw_snippet') if src == 'synthetic' else '')
        if not (code or '').strip(): continue
        h = authz(code); rel = (r['meta'].get('v2_relabel') or {}).get('rule_id'); reason = rel or ('visibility_dependent' if r['meta'].get('visibility_dependent') else ('subscription_relabel' if r['meta'].get('v30_relabel_reason') else 'model_v301/intended'))
        tr.append(dict(src=src, state='인가 검사 있음' if h['authz_any'] else ('인증만' if h['auth_only'] else '인가·인증 없음'), manual=r['label'] == MANUAL, label=r['label'], reason=reason, rationale=r.get('rationale') or ''))
    states = ('인가 검사 있음', '인증만', '인가·인증 없음')
    out += f'## train_v2 대조: 코드 있는 train 레코드 {len(tr)}건(gitea {sum(r["src"] == "gitea" for r in tr)} + 합성 {sum(r["src"] == "synthetic" for r in tr)}) — 코드 상태별 manual 비율\n\n'
    rows = []
    for src in ('gitea', 'synthetic', '합계'):
        sub = [r for r in tr if src == '합계' or r['src'] == src]
        rows.append([src, len(sub)] + [f"{sum(r['manual'] for r in sub if r['state'] == a)} / {sum(r['state'] == a for r in sub)} ({sum(r['manual'] for r in sub if r['state'] == a) / max(1, sum(r['state'] == a for r in sub)):.0%})" for a in states])
    te_rows = [['test_v30 정답(코드 265건)', len(code_ids)] + [f"{sum(azname(i) == a and meta[i]['label'] == MANUAL for i in code_ids)} / {sum(azname(i) == a for i in code_ids)} ({sum(azname(i) == a and meta[i]['label'] == MANUAL for i in code_ids) / max(1, sum(azname(i) == a for i in code_ids)):.0%})" for a in states]]
    out += table(rows + te_rows, ['출처', '건수'] + [f'{a}: manual / 전체' for a in states]) + '\n'
    out += '**train_v2 "인가·인증 없음 또는 인증만 + manual" 사유별**\n\n' + table(sorted(Counter((r['src'], r['state'], r['reason']) for r in tr if r['state'] != '인가 검사 있음' and r['manual']).items(), key=lambda x: -x[1]), ['(출처, 코드 상태, 사유)', '건수']) + '\n'
    out += '**train_v2 "인가 검사 있음 + manual" 사유별**\n\n' + table(sorted(Counter((r['src'], r['reason']) for r in tr if r['state'] == '인가 검사 있음' and r['manual']).items(), key=lambda x: -x[1]), ['(출처, 사유)', '건수']) + '\n'
    out += '**train_v2 코드 상태 × label**\n\n' + table([[a] + [sum(r['state'] == a and r['label'] == l for r in tr) for l in L] for a in states], ['코드 상태'] + L) + '\n'
    out += '**test_v30 코드 상태 × 정답 label (코드 265건)**\n\n' + table([[a] + [sum(azname(i) == a and meta[i]['label'] == l for i in code_ids) for l in L] for a in states], ['코드 상태'] + L) + '\n'
    dist = lambda rows_, a: ', '.join(f'{l} {n}' for l, n in Counter(x for x in rows_ if x).most_common(4) for _ in [0]) if False else ', '.join(f'{l} {n}' for l, n in Counter(rows_).most_common(4))
    tr_noauth = dist([r['label'] for r in tr if r['state'] == '인가·인증 없음'], None); te_noauth = dist([meta[i]['label'] for i in code_ids if azname(i) == '인가·인증 없음'], None)
    # interpretation from computed facts
    fo, fc = facts['oas'], facts['oas_code']; r = lambda t: f'{t[0]}/{t[1]}' + (f' ({t[0] / t[1]:.0%})' if t[1] else '')
    tr_man = {a: (sum(x['manual'] for x in tr if x['state'] == a), sum(x['state'] == a for x in tr)) for a in states}
    te_man = {a: (sum(azname(i) == a and meta[i]['label'] == MANUAL for i in code_ids), sum(azname(i) == a for i in code_ids)) for a in states}
    out += '## 해석 (계산값 기준)\n\n'
    out += f"- **oas**: 교집합 {summary['oas']['inter']}/{summary['oas']['n_concrete']} 중 route_only {r(fo['rate_by_seg']['route_only'])}는 명세가 없어 모델 입력에 정보가 없는 구간이며 eval-def v2에서는 주지표 제외·보조지표에서 manual을 인정한다. 문제는 repository_spec {r(fo['rate_by_seg']['repository_spec'])}이다. 합성은 {r(fo['rate_by_seg']['synthetic'])}로 보류가 없다(템플릿 공유).\n"
    svc_txt = ', '.join(s + ' ' + r(fc['rate_by_service'][s]) for s, _ in sorted(fc['rate_by_service'].items(), key=lambda x: -(x[1][0] / max(1, x[1][1]))))
    lab_txt = ', '.join(l + ' ' + r(fc['rate_by_label'][l]) for l in ('role_required', 'owner_match', 'public', 'owner_or_admin') if fc['rate_by_label'][l][1])
    rat_txt = ', '.join(k + ' ' + str(n) for k, n in fc['rat'].most_common(4))
    out += f"- **oas_code**: 교집합 {summary['oas_code']['inter']}/{summary['oas_code']['n_concrete']}. 코드 상태별 보류율은 인가 검사 있음 {r(fc['rate_by_az']['인가 검사 있음'])}, 인증만 {r(fc['rate_by_az']['인증만'])}, 인가·인증 없음 {r(fc['rate_by_az']['인가·인증 없음'])}로, 인가 검사 유무는 보류를 구분하는 축이 아니다. 구분 축은 서비스({svc_txt})와 정답 label({lab_txt})이다. 합성은 보류 0.\n"
    out += f"- **train 대조**: train_v2 코드 레코드의 manual 비율은 인가 검사 있음 {r(tr_man['인가 검사 있음'])}, 인증만 {r(tr_man['인증만'])}, 인가·인증 없음 {r(tr_man['인가·인증 없음'])}; test_v30 정답은 각각 {r(te_man['인가 검사 있음'])}, {r(te_man['인증만'])}, {r(te_man['인가·인증 없음'])}. '인가 검사 없는 코드 → manual'을 train이 가르쳤다는 가설은 빈도상 뒷받침되지 않는다(train에서도 그 유형의 대부분은 구체 label). 오히려 train manual은 '인가 코드가 있으나 단일 라벨로 안 떨어지는' Gitea VIS·합성 disputed/extauth에 몰려 있고, 교집합 rationale 유형도 {rat_txt}로 '인가 코드는 있으나 요청자-객체 관계가 명시되지 않음/조건 불확정' 서술이 지배적이다. 즉 모델은 test 코드에서 관계 조건을 읽어내지 못할 때 train의 보류 서술 패턴으로 수렴한다.\n"
    out += f"- **분포 불일치**: train_v2 '인가·인증 없음' 코드는 {sum(r['state'] == '인가·인증 없음' for r in tr)}건뿐이고 label은 {tr_noauth}(R4 public 중심). test_v30 같은 유형 {sum(azname(i) == '인가·인증 없음' for i in code_ids)}건의 정답은 {te_noauth}. 인증·인가 코드가 보이지 않는 핸들러에서 경로·스키마로 owner_match·role_required를 읽는 사례가 train에 거의 없다(합성 variant 27건 외). 이 유형은 oas_code 교집합의 {fc['rate_by_az']['인가·인증 없음'][0]}/{summary['oas_code']['inter']}건을 차지한다.\n"
    out += "- rationale 중 'Conflicting owner and tenant requirements are deliberately unresolved; denyAll()…'은 합성 train(campus_records_disputed) rationale의 축자 재생이다. 합성 rationale 템플릿이 test 취약 API 코드에까지 전이되므로 합성 manual 레코드의 rationale 다양성·비중을 점검할 필요가 있다.\n"
    out += f"- 과보류는 seed 간 공통(교집합/합집합 oas {summary['oas']['inter'] / summary['oas']['union']:.0%}, oas_code {summary['oas_code']['inter'] / summary['oas_code']['union']:.0%})으로 체계적이다. 다음 단계는 (2부) label 조건부 로그확률에 manual 감점 b를 적용하는 사후 문턱 조정으로, b는 val_v2 oas_code에서만 고른다(training/lora/lora_v2_abstain_calib.ipynb, scripts/calib_abstain.py). 데이터 측 조치(manual 쿼터·합성 manual rationale)는 별도 승인 사항이다.\n\n"
    out += '## 2부 준비 상태 (문턱 조정)\n\n- training/lora/lora_v2_abstain_calib.ipynb(생성: build_notebook_calib.py): seed별 final 어댑터 × val_v2(oas 52·oas_code 46) + test_v30(oas 269·oas_code 265)에서 7 label 조건부 로그확률을 teacher forcing으로 계산해 `runs/lora_v2_seed<N>/calib/scores_*.jsonl`에 저장. 생성·학습 없음. Colab **미실행**(사용자 실행 필요, README_colab_calib.md).\n- scripts/calib_abstain.py: 감점 b 스윕(0~40, 0.25), val_v2 지표, 선택 규칙(val_v2 oas_code에서 public 오판 0 유지 범위 안 구체 재현율 최대, 동률은 최소 b; seed별 선택), 선택 b를 test_v30에 1회 적용해 eval-def v2 채점, test b 곡선은 참고용 표기. 스크래치패드의 가짜 점수로 실행 경로만 검증했고(산출물은 저장소 밖), 실제 점수 파일이 오기 전까지 결과는 없다.\n- 검증 포인트: 점수 파일의 b=0 argmax가 기존 생성 예측 label과 얼마나 일치하는지(스코어링 타당성)를 보고서에 포함한다.\n- **1차 Colab 실행(2026-10-24 회수) 결과: 무효.** 회수 파일은 s43 4개·s44 4개(중복 2벌)이고 s42가 없음(다운로드 폴더 이름과 파일 tag 불일치). 모두 mode=full(왼쪽 패딩)이며 최고 label 로그확률 중앙값 −19.5~−21.9 nat(정상은 0 근처), test oas_code에서 b=0 argmax와 생성 예측 일치율 55~62%(oas는 89~92%). val oas_code b=0에서 public 오판>0이라 선택 규칙도 적용 불가. 잠정 보고서 reports/eval/lora_v2/abstain_calib_provisional_s43_s44.md는 참고용이며 결정에 쓰지 않는다. 노트북을 rev 2(for_inference, 오른쪽 패딩, greedy 일치 자가 검증·중단)로 수정했고 재실행이 필요하다.\n\n'
    out += f'원자료: reports/eval/lora_v2/abstain_intersection.csv(교집합 전체, 조건별, rationale 유형 포함), lora_v2_seed*/eval/predictions_*_final.jsonl. 해시 가드: data-v1 {", ".join(v for v in g1.values())} / data-v2 {", ".join(v for v in g2.values())}.\n'
    with open(D / 'abstain_intersection.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys())); w.writeheader(); w.writerows(csv_rows)
    assert_data_v1('end'); assert_data_v2('end')
    (D / 'abstain_analysis.md').write_text(out, encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False)); print('train manual by state', tr_man, '| test', te_man); print('oas_code by az', fc['rate_by_az'], 'rat', fc['rat'])

if __name__ == '__main__': main()
