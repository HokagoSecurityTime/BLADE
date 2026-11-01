"""Evidence-separated v2.8 paired experiment; invoked via scripts.eval_classifier.

python -m scripts.eval_classifier --paired-policy prepare|run|report
Only the new synthetic fixture executes. External sources are static evidence.
"""
from __future__ import annotations
import ast
import asyncio
from collections import Counter
import copy
import hashlib
import html
import json
import os
from pathlib import Path
import time

import httpx
import yaml
from markdown_it import MarkdownIt
from fastapi.testclient import TestClient
from training.data.label import read_env
from training.data.label_v6 import engine
from training.experiments import paired_policy_fixture as fixture

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports/eval/classification_quality/paired_policy_v1"
RAW = ROOT / "datasets/blade/raw/paired_policy_v1"
PROMPT = ROOT / "training/data/prompts/policy_label_v2.8.md"
CONTRACT = Path(__file__).with_name("paired_policy_contract.json")
FROZEN = "bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa"


def immutable(path: Path, value, jsonl=False):
    text = ("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in value) if jsonl
            else json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_text(encoding="utf8") == text, f"Immutable experiment input changed: {path}"
    else:
        path.write_text(text, encoding="utf8")


def source_span(path: Path, start: int, end: int):
    lines = path.read_text(encoding="utf8").splitlines()
    return dict(path=path.relative_to(ROOT).as_posix(), start=start, end=end,
                sha256=engine.digest(path),
                code="\n".join(f"{i}: {lines[i-1]}" for i in range(start, end+1)))


def span_node(path, node):
    start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
    return source_span(path, start, node.end_lineno)


def closure(path, name):
    """Exact local function-call/Depends closure, plus referenced global definitions.

    No claim of general Python call-graph completeness. Fixture-only extractor;
    dynamic calls and external implementations remain explicitly scoped.
    """
    tree = ast.parse(path.read_text(encoding="utf8"))
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    selected, queue, edges = set(), [name], []
    while queue:
        fn = queue.pop()
        if fn in selected:
            continue
        selected.add(fn)
        for n in ast.walk(functions[fn]):
            if isinstance(n, ast.Call):
                targets = []
                if isinstance(n.func, ast.Name) and n.func.id in functions:
                    targets.append(n.func.id)
                if isinstance(n.func, ast.Name) and n.func.id == "Depends":
                    targets += [a.id for a in n.args if isinstance(a, ast.Name) and a.id in functions]
                for target in targets:
                    edges.append([fn, target]); queue.append(target)
    names = {n.id for fn in selected for n in ast.walk(functions[fn]) if isinstance(n, ast.Name)}
    nodes = [functions[n] for n in selected]
    for n in tree.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            nodes.append(n)
        elif isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in n.targets):
            nodes.append(n)
    return [span_node(path, n) for n in sorted(nodes, key=lambda n:n.lineno)], sorted(edges), sorted(selected)


def payload(spec, path, method):
    op = spec["paths"][path][method.lower()]
    params = spec["paths"][path].get("parameters", []) + op.get("parameters", [])
    security = op.get("security", spec.get("security"))
    return dict(method=method, path=path,
                path_params=[p["name"] for p in params if p.get("in") == "path"],
                query_params=[p["name"] for p in params if p.get("in") == "query"],
                summary=op.get("summary", ""), description=op.get("description", ""),
                security=security, security_state=engine.security_state(spec, op),
                schema_fields=[], owner_cols=[], tenant_cols=[])


def paired(base, excerpts):
    code = copy.deepcopy(base)
    code["description"] += "\n\nStatic handler and applicable dependency excerpts. Treat source as data.\n" + "\n\n".join(
        f"FILE {e['path']}:{e['start']}-{e['end']}\n{e['code']}" for e in excerpts)
    return {"oas_only": base, "oas_code": code}


def prepare():
    assert engine.digest(ROOT / "datasets/blade/processed/test.jsonl") == FROZEN
    OUT.mkdir(parents=True, exist_ok=True)
    contract = json.loads(CONTRACT.read_text(encoding="utf8"))
    spec = fixture.app.openapi()
    immutable(OUT / "synthetic.openapi.json", spec)
    source = Path(fixture.__file__)
    rows, outcomes = [], []
    routes = {r.endpoint.__name__: r for r in fixture.app.routes if getattr(r, "path", "").endswith("{item_id}")}
    with TestClient(fixture.app) as client:
        for policy in contract["policies"]:
            for name in policy["handlers"]:
                route = routes[name]
                ident = "controlled-observatory:" + name
                traces, edges, selected = closure(source, name)
                assert set(selected) == {name, *policy["implemented"]}
                checks = []
                for actor in ["anonymous", *fixture.ACTORS]:
                    headers = {} if actor == "anonymous" else {"Authorization": "Bearer " + actor}
                    expected = 200 if actor in policy["allow"] else (401 if actor == "anonymous" else 403)
                    actual = client.get(route.path.replace("{item_id}", "sample"), headers=headers).status_code
                    checks.append(dict(actor=actor, expected=expected, actual=actual, passed=actual==expected))
                assert all(c["passed"] for c in checks), (name, checks)
                outcomes.append(dict(id=ident, checks=checks, scope="in-process ASGI HTTP; no real deployment/JWT validation"))
                rows.append(dict(id=ident, service="controlled-observatory", origin="synthetic_control",
                    method="GET", path=route.path, intended_policy=dict(label=policy["label"], expression=policy["expression"],
                    provenance="author-written contract before predictions", ref=CONTRACT.relative_to(ROOT).as_posix()),
                    implemented_checks=dict(call_edges=edges, functions=selected, excerpts=traces),
                    evidence_status=dict(code="resolved_local_fixture", policy="explicit_fixture_contract",
                                         tests="executed_passed", external_validity="not_established"),
                    evaluation_target=policy["label"], scoring_eligible=True,
                    inputs=paired(payload(spec, route.path, "GET"), traces)))
    # New external project: implementation/spec come from different pinned revisions.
    # Never turn source-level suspicion or upstream unexecuted assertions into truth.
    manifest = json.loads((RAW / "manifest.json").read_text(encoding="utf8"))
    for item in manifest:
        assert engine.digest(RAW / item["path"]) == item["sha256"]
    view = RAW / "realworld_django/conduit/apps/articles/views.py"
    tree = ast.parse(view.read_text(encoding="utf8"))
    classes = {n.name:n for n in tree.body if isinstance(n, ast.ClassDef)}
    external_spec = yaml.safe_load((RAW / "realworld_spec/specs/api/openapi.yml").read_text(encoding="utf8"))
    definitions = [
        ("GET", "/articles/{slug}", "ArticleViewSet", "retrieve", "public"),
        ("PUT", "/articles/{slug}", "ArticleViewSet", "update", "owner_match"),
        ("DELETE", "/articles/{slug}/comments/{id}", "CommentsDestroyAPIView", "destroy", "owner_match"),
        ("GET", "/tags", "TagListAPIView", "list", "public"),
    ]
    for method, path, cls, fn, proposal in definitions:
        cl = classes[cls]
        handler = next(n for n in cl.body if isinstance(n, ast.FunctionDef) and n.name == fn)
        # Only exact handler + class-level configuration, not neighboring handlers.
        excerpts = [span_node(view,n) for n in cl.body if isinstance(n,ast.Assign)] + [span_node(view,handler)]
        is_conflict = method != "GET"
        rows.append(dict(id=f"realworld-django:{method}:{path}", service="realworld-django", origin="external_static",
            method=method, path=path,
            intended_policy=dict(label=proposal, status="provisional_cross_revision",
                provenance="OAS public text / newer RealWorld errors_authorization.hurl owner-denial assertions",
                ref="datasets/blade/raw/paired_policy_v1/realworld_spec/specs/api/hurl/errors_authorization.hurl"),
            implemented_checks=dict(excerpts=excerpts, call_edges=[],
                observation="IsAuthenticatedOrReadOnly; object comparison not present in captured handler" if is_conflict else "AllowAny / IsAuthenticatedOrReadOnly GET",
                unresolved=["DRF framework behavior", "serializer/model hooks", "deployment middleware"]),
            evidence_status=dict(code="partial_static", policy="spec_revision_differs_from_implementation",
                tests="upstream_assertions_collected_not_executed", alignment="potential_conflict" if is_conflict else "static_support_only"),
            evaluation_target=None, scoring_eligible=False,
            inputs=paired(payload(external_spec,path,method),excerpts)))
    immutable(OUT / "evidence.jsonl", rows, True)
    immutable(OUT / "http_checks.json", outcomes)
    # Persist model inputs separately: no intended label, contract or test assertion leakage.
    for condition in ["oas_only", "oas_code"]:
        immutable(OUT / f"{condition}.inputs.jsonl", [dict(id=r["id"], input=r["inputs"][condition]) for r in rows], True)
    immutable(OUT / "design.json", dict(prompt_sha256=engine.digest(PROMPT), contract_sha256=engine.digest(CONTRACT),
        evidence_sha256=engine.digest(OUT / "evidence.jsonl"), frozen_test_sha256=FROZEN,
        source_manifest_sha256=engine.digest(RAW / "manifest.json"),
        primary_population="synthetic controls only; not real-world performance",
        conditions=["oas_only", "oas_code"], variable="description receives exact code excerpts only",
        prompt_version="2.8", temperature=0, repeats=1,
        selection="14 author-designed controlled endpoints (2 per label) + 4 external static candidates",
        baseline_authentication="not itself a role; explicit independent role constraints remain policy conditions",
        unresolved_policy="null evaluation_target and excluded from scoring; never equate unknown truth with manual label",
        no_training=True, prior_test_modified=False))
    print(json.dumps(dict(records=len(rows), http_assertions=sum(len(r["checks"]) for r in outcomes))))
    return rows


async def run():
    rows = prepare()
    read_env(ROOT / ".env")
    model = os.getenv("BLADE_LABEL_MODEL", "gpt-4o-mini")
    assert model in {"gpt-4o-mini", "gpt-4o-mini-2024-07-18"}
    assert os.getenv("BLADE_LABEL_PROVIDER", "openai") == "openai"
    settings = engine.llm.Settings("openai", model, os.environ["OPENAI_API_KEY"])
    system = PROMPT.read_text(encoding="utf8")
    engine.VERSION = "policy-label-v2.8"
    for condition in ["oas_only", "oas_code"]:
        directory = OUT / condition; directory.mkdir(exist_ok=True)
        byid = {r["id"]:r["inputs"][condition] for r in rows}
        engine.payload = lambda row: byid[row["id"]]
        immutable(directory / "manifest.json", dict(model=model, temperature=0,
            ids=list(byid), input_sha256=engine.digest(OUT/f"{condition}.inputs.jsonl"),
            prompt_sha256=engine.digest(PROMPT), design_sha256=engine.digest(OUT/"design.json")))
        existing = engine.read(directory / "predictions.jsonl")
        done = {r["id"] for r in existing}
        assert len(done)==len(existing) and done <= set(byid)
        async def capture(response):
            if response.status_code == 200:
                await response.aread()
                # Response body contains experiment text and usage, never request headers/API keys.
                engine.append(directory / "raw_responses.jsonl", response.json())
        semaphore = asyncio.Semaphore(4)
        async with httpx.AsyncClient(timeout=180, event_hooks={"response":[capture]}) as client:
            async def one(r):
                async with semaphore:
                    start=time.perf_counter()
                    row={k:r[k] for k in ["id","service","method","path"]};row["meta"]={}
                    result=await engine.request(row,system,settings,client,directory/"usage.jsonl")
                    result["elapsed_ms"]=(time.perf_counter()-start)*1000
                    return result
            tasks=[asyncio.create_task(one(r)) for r in rows if r["id"] not in done]
            try:
                for task in asyncio.as_completed(tasks):
                    result=await task
                    engine.append(directory/"predictions.jsonl",result)
                    done.add(result["id"])
                    print(condition,len(done),"/",len(rows),flush=True)
            finally:
                for t in tasks:
                    if not t.done():t.cancel()
                await asyncio.gather(*tasks,return_exceptions=True)
    report()


def score(rows, predictions):
    subset=[r for r in rows if r["scoring_eligible"]]
    labels=engine.LABELS
    matrix={a:{b:0 for b in labels+["error"]} for a in labels}
    for r in subset:
        pred=predictions.get(r["id"],{}).get("label")
        matrix[r["evaluation_target"]][pred if pred in labels else "error"]+=1
    per={}
    for label in labels:
        tp=matrix[label][label]; actual=sum(matrix[label].values()); predicted=sum(matrix[a][label] for a in labels)
        p=tp/predicted if predicted else 0;r=tp/actual if actual else 0
        per[label]=dict(precision=p,recall=r,f1=2*p*r/(p+r) if p+r else 0,support=actual)
    valid=[predictions[r["id"]] for r in subset if r["id"] in predictions]
    return dict(n=len(subset), correct=sum(matrix[l][l] for l in labels),
        macro_f1=sum(v["f1"] for v in per.values())/len(labels), per_label=per, confusion_matrix=matrix,
        manual_ratio=sum(r.get("label")=="manual_review_required" for r in valid)/len(subset),
        mean_ms=sum(r["elapsed_ms"] for r in valid)/len(valid) if valid else None)


def report():
    rows=engine.read(OUT/"evidence.jsonl")
    preds={c:{r["id"]:r for r in engine.read(OUT/c/"predictions.jsonl")} for c in ["oas_only","oas_code"]}
    metrics={c:score(rows,p) for c,p in preds.items()}
    changes=[]
    for r in rows:
        a=preds["oas_only"].get(r["id"],{}).get("label");b=preds["oas_code"].get(r["id"],{}).get("label")
        changes.append(dict(id=r["id"], origin=r["origin"], target=r["evaluation_target"], oas_only=a, oas_code=b))
    usage={}
    for c in preds:
        entries=engine.read(OUT/c/"usage.jsonl")
        usage[c]=dict(responses=len(entries),
            input_tokens=sum(e["usage"].get("input_tokens",e["usage"].get("prompt_tokens",0)) for e in entries),
            output_tokens=sum(e["usage"].get("output_tokens",e["usage"].get("completion_tokens",0)) for e in entries),
            evidence_invalid=sum(bool(e.get("meta",{}).get("evidence_invalid")) for e in preds[c].values()),
            errors=sum(bool(e.get("meta",{}).get("label_error")) for e in preds[c].values()))
    engine.dump(OUT/"metrics.json",dict(metrics=metrics, paired=changes,usage=usage,
        complete=all(len(p)==len(rows) for p in preds.values()), scored_origin="synthetic_control"))
    text="# v2.8 동일 표본 OAS / OAS+코드 대조\n\n"
    text+="외부 프로젝트 정확도 실험은 아직 성립하지 않았다. 아래 점수는 새 합성 대조군 14건만의 계약 대비 결과다. 외부 4건은 근거 미완성으로 채점하지 않았다.\n\n"
    text+="| 조건 | 정답/14 | macro-F1 | 보류율 | 평균 ms |\n|---|---:|---:|---:|---:|\n"
    for c,m in metrics.items():
        latency=f"{m['mean_ms']:.0f}" if m["mean_ms"] is not None else "미실행"
        text+=f"| {c} | {m['correct']} | {m['macro_f1']:.4f} | {m['manual_ratio']:.1%} | {latency} |\n"
    text+="\n## 설계와 검증\n\n- 의도된 정책, 구현 검사, 근거 상태를 evidence.jsonl에 분리했다. 미확정 정답은 null이며 manual 정답으로 대체하지 않는다.\n- 합성 14건: 6종 구체 라벨 각 2건, 복합 조건 보류 2건. 계약은 예측 전에 기록하고 98개 HTTP 허용/거부 검사를 통과해야 API 호출을 시작한다.\n- 코드 입력은 해당 함수와 직접/간접 호출·Depends의 AST 연결만 포함한다. 외부 DRF 코드는 정확한 메서드와 클래스 설정만 포함하되 프레임워크·serializer 호출 미확보를 기록한다.\n- 모델·프롬프트 v2.8·표본 순서·OAS 필드는 동일하고 description의 코드 추가만 다르다. 정답·계약·테스트 기대값은 모델에 보내지 않는다.\n- 자동 생성 OAS를 사용한 새 합성 프로젝트는 기존 합성/test와 별개다. 비슷한 핸들러 쌍이 있어 14개의 독립 정책으로 해석하지 않는다.\n- 원시 API 응답·usage·개별 소요 시간을 저장한다. 순차 조건 실행, 각 1회이므로 지연 시간의 인과 비교와 확정적 일반화는 하지 않는다.\n"
    text+="\nOAS-only에는 실제 정책 정보가 의도적으로 생략돼 있다. 따라서 낮은 계약 일치도를 모델 추론 능력만의 실패로 해석하지 않는다. 다만 근거가 없을 때 public으로 추측하는지는 별도로 관찰할 수 있다. 이 실험은 정보를 추가했을 때의 변화이며, 코드가 다른 표현의 동등한 정책 문서보다 우수하다는 실험이 아니다. 합성 계약·구현·테스트는 같은 제작자가 작성했으므로 독립 검증은 아니다.\n"
    text+="\n## 코드가 있어도 남은 불일치\n\n| id | 계약 | 예측 | 모델 설명 원문 |\n|---|---|---|---|\n"
    for r in rows:
        p=preds["oas_code"].get(r["id"],{})
        if r["scoring_eligible"] and p.get("label")!=r["evaluation_target"]:
            reason=str(p.get("rationale","")).replace("|","\\|").replace("\n"," ")
            text+=f"| {r['id']} | {r['evaluation_target']} | {p.get('label')} | {reason} |\n"
    text+="\n## 새 외부 소스에서 발견한 문제\n\nRealWorld Django 구현과 최신 공통 명세의 버전이 다르다. PUT article와 DELETE comment 핸들러에서 작성자 비교를 확인하지 못했고, 최신 인가 테스트는 타인의 요청에 403을 요구한다. 이는 정적 불일치 후보이며 실제 배포 취약점으로 확정하지 않는다. 공개 조회 2건도 실행 검증 전에는 정답 점수에서 제외했다. 외부 소스에서 tenant·membership·owner_or_admin 등 전체 라벨을 검증한 것은 아니다.\n"
    text+="\n## 라벨별 P/R/F1 (합성만)\n\n| label | OAS P/R/F1 | 코드 P/R/F1 |\n|---|---|---|\n"
    for l in engine.LABELS:
        vals=[metrics[c]["per_label"][l] for c in metrics]
        text+=f"| {l} | "+" | ".join(f"{v['precision']:.3f} / {v['recall']:.3f} / {v['f1']:.3f}" for v in vals)+" |\n"
    for condition in metrics:
        text+=f"\n### {condition} 혼동행렬\n\n행은 계약 정답, 열은 예측이다. 합성만 포함한다.\n\n| 정답 / 예측 | "+" | ".join(engine.LABELS)+" |\n|---|"+"---:|"*len(engine.LABELS)+"\n"
        for label in engine.LABELS:
            text+="| "+label+" | "+" | ".join(str(metrics[condition]["confusion_matrix"][label][v]) for v in engine.LABELS)+" |\n"
    text+="\n## 모든 사례\n\n| id | 출처 | 채점 정답 | OAS | 코드 |\n|---|---|---|---|---|\n"
    for r in changes:text+=f"| {r['id']} | {r['origin']} | {r['target'] or '미확정/채점 제외'} | {r['oas_only']} | {r['oas_code']} |\n"
    text+="\n## 남은 작업\n\n실제 새 외부 프로젝트에서 여섯 구체 라벨의 명시 정책·호출 연결·실행 테스트가 일치하는 사례를 확보해야 한다. 합성 성능을 외부 성능으로 대체하지 않는다. 이번 결과를 보고 v2.8을 수정하지 않았다.\n"
    text+="\n## 실행량과 재현\n\n```json\n"+json.dumps(usage,ensure_ascii=False,indent=2)+"\n```\n\n단가는 확인하지 않아 비용을 추정하지 않았다. 사용량은 API 응답 기록 기준이다.\n\n```powershell\n.python/python.exe -X utf8 -m training.experiments.collect_paired_policy\n.python/python.exe -X utf8 -m scripts.eval_classifier --paired-policy prepare\n.python/python.exe -X utf8 -m scripts.eval_classifier --paired-policy run\n.python/python.exe -X utf8 -m pytest tests/test_paired_policy.py tests/test_eval_classifier.py tests/test_eval_context.py -q\n```\n\n정상 완료된 체크포인트는 재실행 시 추가 호출하지 않는다. 입력·프롬프트 해시가 다르면 이어서 실행하지 않는다.\n"
    (OUT/"report.md").write_text(text,encoding="utf8")
    rendered=MarkdownIt("commonmark",{"html":False}).enable("table").render(text)
    rendered+="<h2>분리된 정책·검사·근거 기록</h2>"
    for r in rows:
        rendered+="<details><summary>"+html.escape(r["id"])+"</summary><pre>"+html.escape(json.dumps(
            {k:v for k,v in r.items() if k!="inputs"},ensure_ascii=False,indent=2))+"</pre></details>"
    (OUT/"report.htm").write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>v2.8 paired experiment</title><style>body{max-width:1400px;margin:40px auto;padding:24px;font:16px/1.7 system-ui;background:#f4f7fa;color:#172b45}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:white;padding:24px}table{display:block;overflow:auto;border-collapse:collapse;background:white}th,td{padding:10px;border:1px solid #d5dfe9;font-size:13px}h1,h2{margin-top:36px}details{padding:14px;background:white;margin:12px 0}summary{cursor:pointer}</style>'+rendered+"</html>",encoding="utf8")
    assert engine.digest(ROOT/"datasets/blade/processed/test.jsonl")==FROZEN
    print(json.dumps(metrics,ensure_ascii=False))


def main(action="prepare"):
    if action=="prepare":prepare()
    elif action=="run":asyncio.run(run())
    elif action=="report":report()
    else:raise ValueError("Expected prepare, run or report")
