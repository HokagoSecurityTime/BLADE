"""Build a standalone Korean HTML report and source-pilot AI review."""
import html
import json
from collections import Counter
from pathlib import Path
from training.experiments.run_source_pilot import OUT, RAW, ROOT
from training.data.label_v6 import engine

BASE = OUT.parent
PUBLIC = {0, 1, 3, 4, 6, 8, 9, 14, 17, 19}
ROLE = {11, 13}
COMPOUND = {2, 5, 7, 10, 12, 15, 16, 18}


def table(headers, rows):
    esc = lambda v: html.escape(str(v))
    return '<div class="scroll"><table><thead><tr>' + "".join(
        f"<th>{esc(h)}</th>" for h in headers) + "</tr></thead><tbody>" + "".join(
        "<tr>" + "".join(f"<td>{esc(c)}</td>" for c in row) + "</tr>"
        for row in rows) + "</tbody></table></div>"


def excerpt(service, filename, start, end):
    root = RAW / f"jdk_8_maven/cs/rest/original/{service}"
    files = list(root.rglob(filename))
    assert len(files) == 1
    p = files[0]
    lines = p.read_text(encoding="utf8").splitlines()
    assert 1 <= start <= end <= len(lines)
    return dict(path=p.relative_to(RAW).as_posix(), sha256=engine.digest(p),
                start=start, end=end,
                code="\n".join(f"{i}: {lines[i-1]}" for i in range(start, end+1)))


def main():
    packets = engine.read(OUT / "inputs.jsonl")
    reviews = []
    specifics = {
        2: ("CommentServiceImpl.java", 119, 125),
        5: ("TodoServiceImpl.java", 40, 52),
        7: ("TodoServiceImpl.java", 56, 66),
        10: ("UserServiceImpl.java", 98, 115),
        12: ("TodoServiceImpl.java", 70, 79),
        15: ("UserServiceImpl.java", 48, 51),
        16: ("AlbumServiceImpl.java", 90, 105),
        18: ("CategoryServiceImpl.java", 59, 68)}
    for i, p in enumerate(packets):
        service = p["service"]
        evidence = []
        if i in PUBLIC:
            label, status = "public", "supported"
            reason = "GET /api/** permitAll과 해당 조회 핸들러를 대조했다. 해당 메서드에 별도 역할 검사나 요청자 소유 필터가 보이지 않는다. 실제 배포 동작을 실행 검증한 것은 아니다."
            evidence = [excerpt(service, "SecutiryConfig.java", 25, 28),
                        excerpt(service, "SecutiryConfig.java", 52, 59)]
        elif i in ROLE:
            label, status = "role_required", "supported"
            reason = "생성 메서드의 hasRole('USER')가 명시적 진입 조건이다. 생성자 기록 자체는 기존 객체에 대한 소유자 비교와 구분한다."
            evidence = [excerpt(service, "CommentController.java" if i == 11 else "TagController.java",
                                43 if i == 11 else 42, 49)]
        elif i in COMPOUND:
            label, status = "manual_review_required", "compound_boundary"
            reason = "역할 진입 조건과 자기 자원 선택·소유자 검사(일부 ADMIN 우회)가 함께 있다. USER를 단순 인증 기반 역할로 정규화할지 독립 정책으로 볼지 확정되지 않아 단일 라벨 우열 집계에서 제외한다. 객체 조건만의 부분 일치와 전체 정책 표현을 혼동하지 않는다."
            evidence = [excerpt(service, *specifics[i])]
        elif i in {36, 48}:
            label, status = None, "standard_conflict"
            reason = "등록·로그인이라는 인증 이전 기능은 public 의미 후보이나, v2.8의 mutation public은 explicitly_anonymous만 허용한다는 기존 제한과 충돌한다. 보안 선언을 임의 보충하거나 확정 오답으로 채점하지 않는다."
            evidence = [excerpt(service, "RegisterRestController.java" if i == 36 else "LoginRestController.java",
                                21 if i == 36 else 23, 25 if i == 36 else 27)]
        else:
            label, status = "manual_review_required", "intent_unestablished"
            reason = ("상품·구성 DAO 호출은 확인되지만 요청자 권한을 결정하는 정책 근거는 확보되지 않았다. 검사 미발견을 공개 의도로 간주하지 않는다."
                      if service == "features-service" else
                      "사용자·역할·permission 객체를 관리하는 코드와 호출자의 인가 검사는 다르다. 확보한 구현만으로 의도된 public·관리자·개인 소유 정책을 확정하지 않는다.")
            if service == "features-service":
                evidence = [excerpt(service, "ProductsService.java", 30, 54),
                            excerpt(service, "ProductsConfigurationsService.java", 29, 41)]
            else:
                evidence = [excerpt(service, "RBACRestController.java", 29, 39),
                            excerpt(service, "UserService.java", 342, 359)]
        # Every row also retains its exact matched handler, with the complete source
        # as evidence rather than claiming that a shared service excerpt is its call.
        handler = RAW / p["handler"]
        evidence.append(dict(path=p["handler"], sha256=engine.digest(handler),
                             start=1, end=len(handler.read_text().splitlines()),
                             code=handler.read_text(encoding="utf8")))
        reviews.append(dict(id=p["id"], service=service, method=p["input"]["method"],
                            path=p["input"]["path"], ai_label=label, status=status,
                            rationale=reason, evidence=evidence, human_confirmed=False,
                            evidence_in_model_input=all(e["path"] in p["input"]["description"] for e in evidence)))
    assert len(reviews) == 50
    engine.dump(OUT / "ai_code_review.json", dict(
        reviewer="Codex agent", standard="v2.8", api_calls=0,
        blinding="Previous aggregate predictions were visible; not an independent blinded ground truth.",
        reviews=reviews))
    predictions = {v: {r["id"]: r for r in engine.read(OUT / f"v{v}/predictions.jsonl")}
                   for v in ("26", "27", "28")}
    metrics = {}
    for v, preds in predictions.items():
        assert set(preds) == {r["id"] for r in reviews}
        definite = [r for r in reviews if r["status"] == "supported" and r["evidence_in_model_input"]]
        comparable = [r for r in reviews if r["status"] in {"supported", "intent_unestablished"}]
        metrics[v] = dict(supported_n=len(definite),
            supported_agreement=sum(preds[r["id"]]["label"] == r["ai_label"] for r in definite),
            comparable_n=len(comparable),
            comparable_agreement=sum(preds[r["id"]]["label"] == r["ai_label"] for r in comparable))
    engine.dump(OUT / "ai_code_review_metrics.json", metrics)
    old = json.loads((BASE / "ai_review_v28_summary.json").read_text(encoding="utf8"))
    new = json.loads((OUT / "comparison.json").read_text(encoding="utf8"))
    rows = []
    for v in metrics:
        m = metrics[v]; o = old["metrics"][f"v{v[0]}.{v[1]}"]
        rows.append([f"v{v[0]}.{v[1]}", f"{o['agreement_count']}/100",
                     f"{o['supported_subset_agreement']}/10",
                     f"{m['supported_agreement']}/{m['supported_n']}",
                     f"{m['comparable_agreement']}/{m['comparable_n']}"])
    body = """<header><span class="eyebrow">BLADE · EXPERIMENT REVIEW</span>
<h1>분류 품질 실험 종합</h1><p>기존 OAS 100건 + 코드·스펙 50건 · v2.6 / v2.7 / v2.8</p></header>
<main><section class="notice"><h2>결론을 읽는 방법</h2>
<p>아래는 AI 검수안과의 일치도다. 사람 정답 기준 정확도나 실제 배포 정책 검증 결과가 아니다.
표본·입력·보류 기준이 달라 단순 합산한 종합 점수로 버전 순위를 확정하지 않는다.</p>
<p>기존 100건에서는 v2.6이 더 잘 맞았다. 새 코드 표본은 아래의 근거 지지 부분집합 결과를 별도로 본다.
보류를 많이 선택하는 효과와 구체 정책을 올바르게 읽는 능력을 분리해야 한다.</p></section>"""
    body += "<section><h2>01 · 세 버전 검수 대조</h2>" + table(
        ["버전", "OAS 100건 전체", "OAS 근거 지지 10건", "코드 근거 지지 사례", "코드 비교 가능 사례"], rows)
    body += """<p>코드 비교 가능 사례는 근거 지지 사례와 의도 미확보 사례를 포함한다.
복합 조건 8건과 기준 충돌 2건은 제외했다. 보류를 포함한 열과 구체 사례 열은 서로 다른 지표다.
이 비교는 모두 v2.8 검수 관점을 사용하며 과거 버전 기준의 성능 재현이 아니다.</p></section>"""
    body += "<section><h2>02 · 새 50건 코드 검수</h2>" + table(
        ["구분", "건수"], Counter(r["status"] for r in reviews).items())
    body += """<p><strong>핵심 발견:</strong> 블로그 GET에는 명시적인 permitAll이 있지만 Todo·me에는 메서드 역할 검사가 있다.
소유자 OR ADMIN 검사도 실제 존재한다. 그러나 역할 검사까지 함께 표현해야 하는 경우 단일 라벨로의 축약에 주의해야 한다.
사용자 관리의 RoleService는 역할 객체를 CRUD하는 서비스이지 그 자체로 호출자 역할 검사기는 아니다.</p>
<p>새 표본도 모두 좋은 정답 데이터는 아니다. 3개 서비스·Java 편중이며 tenant/membership 정책을 충분히 검증하지 못한다.
50건은 호출 연결을 정적으로 수집했고 실행하지 않았다. 외부 인가 계층이나 완전한 호출 그래프는 확보하지 않았다.</p></section>"""
    body += "<section><h2>03 · 코드 표본 예측 분포</h2>" + table(
        ["label", "v2.6", "v2.7", "v2.8"],
        [[label] + [new["metrics"][v]["labels"].get(label, 0) for v in metrics] for label in engine.LABELS])
    body += "<p>모두 출력 오류 0건. 근거 필드 검증 실패는 0 / 1 / 0건. 검토 플래그는 0 / 2 / 2건이다. 구체 선택률은 정확도가 아니다.</p></section>"
    body += """<section><h2>04 · 버전 변화와 실험 흐름</h2>""" + table(
        ["단계", "변경·목적", "해석"],
        [["v2.0 베이스라인", "고정 test 253건, GPT와 Qwen 및 문맥 설정 비교", "최종 런타임 정책 출력 평가. 새 라벨링 표본과 직접 비교 불가"],
         ["평가 기록 보완", "모델 원문·검증 전후 단계 분리", "기존 원문 미저장 결과의 원시 F1은 복원 불가"],
         ["ERD·소스 문맥 보완", "실제 소스의 스키마·핸들러 신호 보충", "입력 문맥 변화와 검증 보류를 함께 추적"],
         ["소유권 집행 실험", "/me·생성·목록 등 객체 조회 외 집행 방식", "의미 라벨 품질과 집행 가능성은 별도 문제"],
         ["v2.6", "v2.5 규칙과 사람 교정 예시", "기존 OAS 검수 일치도 우세지만 보류 편향"],
         ["v2.7", "보류·ACL·복합 조건 통합, 예시 제거", "동시에 여러 요소 변경; 역할 집중 발생"],
         ["v2.8", "객체·관계·조건·구현·출처와 인접 라벨 구분", "코드 기반 설계이나 OAS-only 실험으로 코드 효과를 주장할 수 없음"],
         ["WFD 50건", "같은 코드+OAS 입력으로 3버전 실행", "OAS 100건과 다른 모집단. paired 코드 제거 실험은 미실시"]])
    body += """<p>기존 결과는 원문 부록에서 확인할 수 있다. AI 검수안을 학습 정답이나 고정 test에 반영하지 않았다.</p></section>
<section><h2>05 · 다음 우선순위</h2><ol>
<li>전체 파일 대신 해당 핸들러·인가 호출·전역 규칙을 정확히 연결해 문맥 혼입을 줄인다.</li>
<li>USER 역할과 소유 조건의 복합 표현, 코드상 익명 허용과 mutation 규칙의 충돌을 별도 기록한다. 이번에는 프롬프트를 바꾸지 않았다.</li>
<li>명시적 정책 근거가 있는 프로젝트를 추가 선정하고 tenant·membership 사례를 확보한다.</li>
<li>동일 새 표본에서 코드 포함/제외 조건을 비교해야 코드 입력 효과를 판단할 수 있다.</li>
</ol></section><section><h2>06 · 50건 상세 AI 검수</h2>
<label>검색 <input id="query" placeholder="경로·서비스·라벨 검색" aria-label="검수 검색"></label>
<p>펼치면 세 버전 예측과 코드 근거를 확인할 수 있다. 근거는 정적 분석 범위이며 사람 확정이 아니다.</p>"""
    for r in reviews:
        title = f"{r['service']} · {r['method']} {r['path']} · {r['status']}"
        body += '<details class="review"><summary>' + html.escape(title) + "</summary><p>" + html.escape(r["rationale"]) + "</p>"
        body += table(["AI 제안", "v2.6", "v2.7", "v2.8"],
                      [[r["ai_label"] or "미확정"] + [predictions[v][r["id"]]["label"] for v in metrics]])
        for e in r["evidence"]:
            body += "<details><summary>" + html.escape(f"{e['path']}:{e['start']}-{e['end']}") + "</summary><pre>" + html.escape(e["code"]) + "</pre></details>"
        body += "</details>"
    body += "</section><section><h2>07 · 기존 실험 원문 부록</h2>"
    docs = [
        ROOT / "reports/eval/baseline_summary.md",
        ROOT / "reports/eval/runtime_validation_audit.md",
        ROOT / "reports/eval/context_comparison.md",
        ROOT / "reports/eval/ownership_backend_experiment.md",
        BASE / "v26_vs_v27_vs_v28_fresh100.md",
        BASE / "ai_review_v26_v27_v28.md",
        OUT / "comparison.md"]
    for p in docs:
        if p.exists():
            body += "<details><summary>" + html.escape(str(p.relative_to(ROOT))) + "</summary><pre>" + html.escape(p.read_text(encoding="utf8")) + "</pre></details>"
    body += "</section><footer>추가 API 호출 0회 · 기존 라벨·런타임·고정 test 보존 · 검수 원본: source_pilot/ai_code_review.json</footer></main>"
    css = """body{margin:0;background:#f3f5f9;color:#182437;font:16px/1.7 system-ui,'Malgun Gothic',sans-serif}
header{padding:52px max(24px,calc((100vw - 1120px)/2));background:#10243b;color:white}
h1{font-size:38px;line-height:1.3;margin:12px 0}h2{font-size:23px}.eyebrow{color:#8ed4e2;letter-spacing:2px;font-size:12px}
main{max-width:1120px;margin:30px auto;padding:0 20px}section{background:white;padding:26px;margin:24px 0;border-radius:12px;border:1px solid #dce2eb}
.notice{border-left:6px solid #16889c}table{width:100%;border-collapse:collapse;font-size:14px}
th,td{padding:12px;border-bottom:1px solid #e0e5ed;text-align:left;vertical-align:top}th{background:#edf3f8}.scroll{overflow:auto}
details{border:1px solid #dce2eb;padding:12px;margin:10px 0;border-radius:6px}summary{cursor:pointer;font-weight:600;overflow-wrap:anywhere}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f7fa;padding:16px;font-size:12px}
input{padding:10px;border:1px solid #bcc9d6;border-radius:6px;width:min(500px,80%)}footer{color:#53657b;padding:25px 0}
@media print{header{background:white;color:black}section{break-inside:avoid}input{display:none}}"""
    script = """document.getElementById('query').addEventListener('input',e=>{
const q=e.target.value.toLowerCase();document.querySelectorAll('.review').forEach(d=>{d.hidden=!d.textContent.toLowerCase().includes(q)})});"""
    target = BASE / "EXPERIMENT_OVERVIEW.htm"
    target.write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                      '<title>BLADE 실험 종합 보고서</title><style>' + css + "</style>" + body + "<script>" + script + "</script></html>", encoding="utf8")
    assert engine.digest(ROOT / "datasets/blade/processed/test.jsonl") == "bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa"
    print(json.dumps(metrics))
    print(target)


if __name__ == "__main__":
    main()
