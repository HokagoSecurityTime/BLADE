"""Summarize matched predictions and provenance without claiming accuracy."""
import json
from collections import Counter
from pathlib import Path
from training.experiments.run_source_pilot import OUT, RAW, ROOT
from training.data.label_v6 import engine


def main():
    packets = engine.read(OUT / "inputs.jsonl")
    ids = {r["id"] for r in packets}
    collection = json.loads((OUT / "collection.json").read_text())
    sources = json.loads((RAW / "manifest.json").read_text())
    for f in sources["files"]:
        assert engine.digest(RAW / f["path"]) == f["sha256"]
    assert engine.digest(ROOT / "datasets/blade/processed/test.jsonl") == "bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa"
    results, metrics = {}, {}
    for v in ("26", "27", "28"):
        folder = OUT / ("v" + v)
        records = engine.read(folder / "predictions.jsonl")
        assert len(records) == len(ids) and {r["id"] for r in records} == ids
        manifest = json.loads((folder / "manifest.json").read_text())
        assert manifest["input_sha256"] == engine.digest(OUT / "inputs.jsonl")
        results[v] = {r["id"]: r for r in records}
        usage = [r["usage"] for r in engine.read(folder / "usage.jsonl")]
        metrics[v] = dict(labels=dict(Counter(r.get("label") for r in records)),
            errors=sum(bool(r["meta"].get("label_error")) for r in records),
            evidence_invalid=sum(bool(r["meta"].get("evidence_invalid")) for r in records),
            flag_review=sum(bool(r["meta"].get("flag_review")) for r in records),
            input_tokens=sum(u.get("input_tokens", u.get("prompt_tokens", 0)) for u in usage),
            output_tokens=sum(u.get("output_tokens", u.get("completion_tokens", 0)) for u in usage),
            response_count=len(usage))
    engine.dump(OUT / "comparison.json", dict(metrics=metrics, accuracy=None,
        changed_26_27=sum(results["26"][i]["label"] != results["27"][i]["label"] for i in ids),
        changed_27_28=sum(results["27"][i]["label"] != results["28"][i]["label"] for i in ids)))
    lines = ["# 코드·스펙 기반 새 표본: 세 버전 비교", "",
             "WFD(구 EMB)의 서로 다른 서비스 3개에서 정적으로 추출했다. 기존 APIs.guru 표본과 다른 개발 실험이며 정확도 비교가 아니다.",
             f"저장소 커밋: `{collection['commit']}`. 소스 파일 해시 및 기존 고정 test 해시 검증 완료.",
             "", "| 서비스 | 건수 |", "|---|---:|"]
    lines += [f"| {s} | {n} |" for s, n in collection["services"].items()]
    lines += ["", f"핸들러 매핑 미확정으로 제외한 후보: {len(collection['skipped'])}건.",
              "서비스당 최대 20건, seed 42. features-service는 매핑된 10건을 사용했다.",
              "", "## 비교 조건", "",
              "- OpenAI gpt-4o-mini 계열, temperature 0, 동일 50개 ID와 동일 입력 해시.",
              "- 실제 OAS의 method·path·설명·보안 선언에 핸들러 전체 파일, 연결된 프로젝트 타입·서비스 구현, 확보된 전역 보안 설정을 description으로 추가했다.",
              "- 코드 위치는 파일별 줄번호와 SHA-256을 보존했다. 완전한 호출 그래프 분석이나 실제 인가 동작 검증은 아니다.",
              "- OAS에서 보안 선언이 없다는 이유로 explicitly_anonymous를 만들지 않았다. 코드를 실행하지 않았다.",
              "- 실제 DB ERD를 생성했다고 주장하지 않는다. schema_fields와 후보 컬럼은 빈 배열이며 모델 코드는 소스 문맥에 포함될 수 있다.",
              "- 학습 정답이나 AI 제안 라벨을 입력에 넣지 않았다. 동일 파일의 다른 핸들러도 포함되므로 method별 근거 적용 여부는 후속 검토 대상이다.",
              "- 이번 범위는 B 유형의 WFD 파일럿이다. RealWorld·SwaggerHub·Postman·gapbench 전체 수집은 하지 않았다.",
              "", "## 라벨 분포", "", "| label | v2.6 | v2.7 | v2.8 |", "|---|---:|---:|---:|"]
    for label in engine.LABELS:
        lines.append("| " + label + " | " + " | ".join(str(metrics[v]["labels"].get(label, 0)) for v in results) + " |")
    lines += ["", "| 항목 | v2.6 | v2.7 | v2.8 |", "|---|---:|---:|---:|"]
    for key in ("errors", "evidence_invalid", "flag_review", "input_tokens", "output_tokens", "response_count"):
        lines.append("| " + key + " | " + " | ".join(str(metrics[v][key]) for v in results) + " |")
    lines += ["", "## 서비스별 분포", "",
              "| 서비스 | 버전 | label 건수 |", "|---|---|---|"]
    for service in collection["services"]:
        for v in results:
            counts = Counter(r["label"] for r in results[v].values() if r["service"] == service)
            lines.append(f"| {service} | v{v[0]}.{v[1]} | {dict(counts)} |")
    lines += ["", "API 응답의 실제 토큰 사용량이다. 청구 비용은 별도로 확인해야 하며 단가를 임의 적용하지 않았다.",
              "", "## 해석과 다음 확인", "",
              "코드가 있어도 검사 미발견은 의도된 public 정책의 증명이 아니다. 사용자 관리 서비스의 RBAC 객체 관리 기능과 호출자 역할 검사를 구분해야 한다.",
              "기존 OAS-only 100건과는 서비스·표본·입력이 모두 달라 점수나 분포 차이를 코드 추가의 인과 효과로 해석할 수 없다.",
              "이 표본의 독립 정답 또는 AI 코드 검수 기준은 아직 생성하지 않았다. 따라서 현재 가장 정확한 버전을 선정하지 않는다.",
              "", "## 요청별 결과", "",
              "| service | method | path | v2.6 | v2.7 | v2.8 | 핸들러 |",
              "|---|---|---|---|---|---|---|"]
    for p in packets:
        cells = [p["service"], p["input"]["method"], p["input"]["path"]]
        cells += [str(results[v][p["id"]]["label"]) for v in results]
        cells += [p["handler"]]
        lines.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
    (OUT / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    print(json.dumps(metrics))


if __name__ == "__main__":
    main()
