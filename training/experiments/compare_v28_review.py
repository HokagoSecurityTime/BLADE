"""Compare predictions on the same inputs; no ground-truth metrics."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "reports/eval/classification_quality"
LABELS = ["public", "role_required", "membership_required", "tenant_match",
          "owner_match", "owner_or_admin", "manual_review_required"]


def main():
    folders = {"v2.6": "fresh_review_v26_control", "v2.7": "fresh_review_v27",
               "v2.8": "fresh_review_v28"}
    rows, manifests = {}, {}
    for version, folder in folders.items():
        records = [json.loads(line) for line in
                   (BASE / folder / "model_predictions.jsonl").read_text(encoding="utf8").splitlines()]
        rows[version] = {r["id"]: r for r in records}
        assert len(records) == len(rows[version]) == 100
        manifests[version] = json.loads((BASE / folder / "predictions.manifest.json").read_text(encoding="utf8"))
    for key in ("ids", "input_sha256", "model", "temperature"):
        assert all(m[key] == manifests["v2.8"][key] for m in manifests.values()), key
    assert all(set(r) == set(rows["v2.8"]) for r in rows.values())
    counts = {v: Counter(r.get("label") for r in records.values()
                         if not r.get("meta", {}).get("label_error")) for v, records in rows.items()}
    errors = {v: sum(bool(r.get("meta", {}).get("label_error")) for r in records.values())
              for v, records in rows.items()}
    invalid = {v: sum(bool(r.get("meta", {}).get("evidence_invalid")) for r in records.values())
               for v, records in rows.items()}
    transitions = Counter((rows["v2.7"][i].get("label"), r.get("label"))
                          for i, r in rows["v2.8"].items())
    changed = sum(a != b for i, r in rows["v2.8"].items()
                  for a, b in [(rows["v2.7"][i].get("label"), r.get("label"))])
    lines = ["# v2.6·v2.7·v2.8 동일 100건 예측 비교", "",
             "사람 정답이 미확정이므로 정확도와 macro-F1은 측정하지 않았다.",
             "동일 ID 순서·입력 해시·모델·temperature를 manifest로 확인했다. 코드 근거를 새로 추가하지 않은 기존 OAS 표본이다.",
             "", "| label | v2.6 | v2.7 | v2.8 |", "|---|---:|---:|---:|"]
    lines += [f"| {label} | " + " | ".join(str(counts[v][label]) for v in folders) + " |" for label in LABELS]
    lines += ["", "| 검증 | v2.6 | v2.7 | v2.8 |", "|---|---:|---:|---:|",
              "| 출력 오류 | " + " | ".join(str(errors[v]) for v in folders) + " |",
              "| evidence_invalid | " + " | ".join(str(invalid[v]) for v in folders) + " |",
              "", f"v2.7 대비 라벨 변경 {changed}건, 유지 {100-changed}건.",
              "", "## v2.7 → v2.8 전이", "",
              "예측 간 전이이며 사람 정답 기준 혼동행렬이 아니다.",
              "", "| v2.7 / v2.8 | " + " | ".join(LABELS) + " |",
              "|---|" + "---:|" * len(LABELS)]
    lines += ["| " + a + " | " + " | ".join(str(transitions[a, b]) for b in LABELS) + " |" for a in LABELS]
    lines += ["", "## 해석 범위", "",
              "- v2.8은 대상·관계·조건·구현·출처 확인, 구현과 의도 구분, 인접 라벨 배제 이유를 추가했다.",
              "- 이 실행은 프롬프트 변경 실험이다. 새 코드 데이터의 효과나 코드 기반 판단 성능을 측정하지 않았다.",
              "- 보류율 감소나 역할 라벨 감소만으로 정확도 개선을 주장하지 않는다.",
              "- evidence_invalid는 필드 인용 검사이며 근거의 의미적 타당성을 보증하지 않는다.",
              "- 여러 규칙을 함께 바꾼 단일 실행이므로 개별 규칙의 인과 효과를 분리하지 않는다.",
              "- 기존 test·학습 데이터·런타임은 변경하지 않았다.",
              "", "재현 자료: 각 fresh_review 폴더의 predictions.manifest.json, model_predictions.jsonl, usage.jsonl.",
              "v2.8 사람 검수표: [review_100_v28.md](fresh_review_v28/review_100_v28.md).", ""]
    (BASE / "v26_vs_v27_vs_v28_fresh100.md").write_text("\n".join(lines), encoding="utf8")
    report = dict(counts={v: dict(c) for v, c in counts.items()}, errors=errors,
                  evidence_invalid=invalid, changed_from_v27=changed, accuracy=None)
    (BASE / "v26_vs_v27_vs_v28_fresh100.json").write_text(json.dumps(report, indent=2), encoding="utf8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
