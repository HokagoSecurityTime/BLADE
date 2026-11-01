"""Offline semantic gate. Never changes a model label or activates a policy."""
import ast
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ATOMS = {
    'm': "(actor['id'], resource['group_id']) in memberships",
    't': "actor['tenant_id'] == resource['tenant_id']",
    'o': "actor['id'] == resource['owner_id']",
    'r': "'operator' in actor['roles']",
    'a': "'admin' in actor['roles']",
    'p': "actor['subscription'] == 'premium'",
}
PATTERNS = dict(public='True', membership_required='m', tenant_match='t',
                owner_match='o', role_required='r', owner_or_admin='o or a')


def dump_ast(node):
    return ast.dump(node, include_attributes=False)


def condition(source):
    """Accept only the audited fixture grammar; unknown statements fail closed."""
    module = ast.parse(source)
    if len(module.body) != 1 or not isinstance(module.body[0], ast.FunctionDef):
        raise ValueError('unsupported function')
    fn = module.body[0]
    if fn.decorator_list or [a.arg for a in fn.args.args] != ['actor', 'resource', 'memberships']:
        raise ValueError('unsupported binding')
    aliases = {}
    atom_nodes = {dump_ast(ast.parse(v, mode='eval').body): k for k, v in ATOMS.items()}

    def parse(n):
        key = dump_ast(n)
        if key in atom_nodes:
            return ('atom', atom_nodes[key])
        if isinstance(n, ast.Name) and n.id in aliases:
            return aliases[n.id]
        if isinstance(n, ast.Constant) and type(n.value) is bool:
            return ('constant', n.value)
        if isinstance(n, ast.BoolOp) and isinstance(n.op, (ast.And, ast.Or)):
            return ('and' if isinstance(n.op, ast.And) else 'or', [parse(v) for v in n.values])
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
            return ('not', parse(n.operand))
        raise ValueError('unknown condition or binding')

    body = list(fn.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body.pop(0)
    while body and isinstance(body[0], ast.Assign):
        stmt = body.pop(0)
        if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
            raise ValueError('unsupported assignment')
        name = stmt.targets[0].id
        if name in aliases or name in ('actor', 'resource', 'memberships'):
            raise ValueError('rebound input')
        aliases[name] = parse(stmt.value)
    if len(body) == 1 and isinstance(body[0], ast.Return):
        return parse(body[0].value)
    if len(body) == 2 and isinstance(body[0], ast.If):
        branch, tail = body
        if (not branch.orelse and len(branch.body) == 1
                and isinstance(branch.body[0], ast.Return)
                and dump_ast(branch.body[0].value) == dump_ast(ast.Constant(False))
                and isinstance(tail, ast.Return)
                and dump_ast(tail.value) == dump_ast(ast.Constant(True))):
            return ('not', parse(branch.test))
    raise ValueError('unsupported control flow')


def evaluate(tree, state):
    op, value = tree
    if op == 'atom': return state[value]
    if op == 'constant': return value
    if op == 'not': return not evaluate(value, state)
    if op == 'and': return all(evaluate(v, state) for v in value)
    if op == 'or': return any(evaluate(v, state) for v in value)
    raise ValueError(op)


def verify(prediction, source, *, complete_context=False, fixture_bindings=False):
    """No gold labels accepted. Semantic pass alone never authorizes deployment."""
    result = dict(original_label=prediction.get('label'), original_confidence=prediction.get('confidence'),
                  semantic_candidate_pass=False, auto_apply_allowed=False,
                  deployment_reason='enforcement_binding_not_verified', counterexample=None)
    label = prediction.get('label')
    if label not in PATTERNS:
        return dict(result, reason='manual_or_invalid_label')
    if not complete_context or not fixture_bindings:
        return dict(result, reason='context_or_binding_unverified')
    if any(prediction.get('meta', {}).get(k) for k in ('label_error', 'evidence_invalid', 'flag_review')):
        return dict(result, reason='prediction_validation_failed')
    try:
        actual = condition(source)
    except (ValueError, SyntaxError, TypeError):
        return dict(result, reason='unsupported_code')
    # Pattern trees are constants defined by the experiment, never model code.
    pattern_source = 'def access(actor, resource, memberships):\n'
    pattern_source += ''.join(f'    {k} = {v}\n' for k, v in ATOMS.items())
    pattern_source += '    return ' + PATTERNS[label] + '\n'
    proposed = condition(pattern_source)
    broader, stricter = [], []
    for bits in itertools.product((False, True), repeat=6):
        state = dict(zip('mtorap', bits))
        expected, selected = evaluate(actual, state), evaluate(proposed, state)
        if selected and not expected: broader.append(state)
        if expected and not selected: stricter.append(state)
    return dict(result, semantic_candidate_pass=not broader and not stricter,
                reason='missing_required_condition' if broader else 'overrestriction' if stricter else 'equivalent',
                counterexample=broader[0] if broader else stricter[0] if stricter else None,
                broadened_states=len(broader), overrestricted_states=len(stricter))


def run():
    from markdown_it import MarkdownIt
    origin = ROOT / 'reports/eval/classification_quality/boundary30_v29'
    out = ROOT / 'reports/eval/classification_quality/application_guard_v1'
    out.mkdir(exist_ok=True)
    paths = [origin/'inputs.jsonl', origin/'contracts.json'] + [origin/c/'predictions.jsonl' for c in ('code', 'code_conditions')]
    paths += [ROOT/'datasets/blade/processed/test.jsonl']
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    before = {str(p.relative_to(ROOT)): digest(p) for p in paths}
    rows = {r['id']: r for r in map(json.loads, paths[0].read_text(encoding='utf8').splitlines())}
    all_results, metrics = [], {}
    for c in ('code', 'code_conditions'):
        predictions = [json.loads(s) for s in (origin/c/'predictions.jsonl').read_text(encoding='utf8').splitlines()]
        results = []
        for pred in predictions:
            description = rows[pred['case_id']]['inputs']['code']['description']
            source = description[description.index('def access('):]
            guard = verify(pred, source, complete_context=True, fixture_bindings=True)
            results.append(dict(id=pred['case_id'], condition=c, prediction=pred, guard=guard))
        all_results.extend(results)
        metrics[c] = {reason: sum(r['guard']['reason'] == reason for r in results) for reason in
                      ('equivalent', 'missing_required_condition', 'overrestriction', 'unsupported_code', 'manual_or_invalid_label')}
        # Gold is read only after every gate decision, for evaluation only.
        gold = {r['id']: r['target'] for r in json.loads((origin/'contracts.json').read_text(encoding='utf8'))}
        correct = [r for r in results if r['prediction']['label'] == gold[r['id']] and gold[r['id']] in PATTERNS]
        metrics[c]['correct_concrete'] = len(correct)
        metrics[c]['correct_concrete_blocked'] = sum(not r['guard']['semantic_candidate_pass'] for r in correct)
        metrics[c]['wrong_concrete_passed'] = sum(r['guard']['semantic_candidate_pass'] and r['prediction']['label'] != gold[r['id']] for r in results)
    text = '# 원래 라벨 보존 · 자동 적용 검증기\n\n기존 30건 × 두 입력 조건의 예측을 재사용했다. API 호출 0회. 라벨·confidence는 변경하지 않고 별도 guard 필드에 결과를 기록한다.\n\n'
    text += '| 입력 | 의미 일치 | 필수 조건 누락/허용 확대 | 과도한 제한 | 보류/비정상 라벨 | 올바른 구체 라벨 오차단 | 틀린 구체 라벨 통과 |\n|---|---:|---:|---:|---:|---:|---:|\n'
    for c, m in metrics.items():
        text += f"| {c} | {m['equivalent']} | {m['missing_required_condition']} | {m['overrestriction']} | {m['manual_or_invalid_label']} | {m['correct_concrete_blocked']}/{m['correct_concrete']} | {m['wrong_concrete_passed']} |\n"
    text += '\n## 판정 방식과 한계\n\n코드에서 허용 조건을 제한된 AST 문법으로 추출하고, 라벨이 나타내는 조건과 64개 상태에서 비교한다. 제안은 허용하지만 코드가 거부하는 상태를 반례로 저장한다. 코드가 허용하지만 제안이 거부하는 경우도 별도로 차단한다. 정답 라벨은 차단 판정에 사용하지 않는다.\n\n이 결과는 15개 합성 정책 × 두 문법 변형의 개발 실험이다. 모든 조건이 확보되었다는 fixture 전제와 operator/admin 역할·소유자·그룹 바인딩을 사용한다. 외부 코드의 전체 호출 경로 확보나 실제 정책 파라미터 검증을 증명하지 않는다. 미지원 코드·확인되지 않은 입력 바인딩은 통과시키지 않는다.\n\nsemantic_candidate_pass는 의미 동등성 검사 결과일 뿐이다. 실제 집행 바인딩을 검증하지 않았으므로 auto_apply_allowed는 전부 false다. 특히 현재 런타임의 membership 등급 비교는 대상 그룹 구성원 검사를 구현하지 않는다. 런타임 연결·정책 활성화는 하지 않았다. 구현된 검사와 의도된 정책의 일치도 별도 검증이 필요하다.\n\n## 차단 반례\n\nm=그룹 구성원, t=동일 테넌트, o=소유자, r=operator, a=admin, p=premium. 인증된 요청 상태의 비교이며 public은 별도의 명시적 익명 fixture이다.\n\n| 입력 | ID | 원래 라벨 | 차단 사유 | 반례 |\n|---|---|---|---|---|\n'
    for r in all_results:
        g = r['guard']
        if g['counterexample'] is not None:
            text += f"| {r['condition']} | {r['id']} | {g['original_label']} | {g['reason']} | {json.dumps(g['counterexample'])} |\n"
    (out/'decisions.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in all_results), encoding='utf8')
    (out/'metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf8')
    (out/'report.md').write_text(text, encoding='utf8')
    (out/'report.htm').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>자동 적용 검증기</title><style>body{max-width:1200px;margin:40px auto;font:16px/1.7 system-ui}table{border-collapse:collapse}td,th{border:1px solid #bbb;padding:8px}</style>'+MarkdownIt().enable('table').render(text)+'</html>', encoding='utf8')
    assert before == {str(p.relative_to(ROOT)): digest(p) for p in paths}
    assert digest(paths[-1]) == 'bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa'
    (out/'manifest.json').write_text(json.dumps(dict(api_calls=0, source_hashes=before, verifier_sha256=digest(Path(__file__)), fixture_bindings=ATOMS, runtime_modified=False), indent=2), encoding='utf8')
    print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    run()
