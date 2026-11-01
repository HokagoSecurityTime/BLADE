"""Package agent-authored reviews, then compare existing predictions (no API)."""
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "reports/eval/classification_quality"
MANUAL = "manual_review_required"
LABELS = ["public", "role_required", "membership_required", "tenant_match",
          "owner_match", "owner_or_admin", MANUAL]


def read(path):
    return [json.loads(x) for x in path.read_text(encoding="utf8").splitlines()]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = BASE / "fresh_review_v1/blind_inputs.jsonl"
    packets = read(source)
    notes_path = BASE / "ai_review_v28_notes.tsv"
    notes = list(csv.DictReader(notes_path.read_text(encoding="utf8").splitlines(), delimiter="\t"))
    assert [int(n["index"]) for n in notes] == list(range(100))
    assert len(packets) == 100 and len({p["id"] for p in packets}) == 100
    # Ambiguous public/authenticated-reference-data boundary and account ontology.
    standard_ambiguous = {4, 7, 12, 13, 14, 19, 50, 56, 88}
    weak_proposals = {20, 61}
    reviews = []
    for n, p in zip(notes, packets):
        assert n["label"] in LABELS
        idx = int(n["index"])
        reviews.append(dict(id=p["id"], service=p["service"],
                            method=p["input"]["method"], path=p["input"]["path"],
                            ai_label=n["label"], rationale=n["reason"],
                            review_status=("standard_ambiguity" if idx in standard_ambiguous
                                           else "weak_proposal" if idx in weak_proposals
                                           else "input_insufficient" if n["label"] == MANUAL
                                           else "supported_proposal"),
                            human_confirmed=False, reviewer="Codex agent",
                            standard_version="v2.8"))
    # Persist judgments before opening the three prediction files.
    out = BASE / "ai_review_v28.jsonl"
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in reviews), encoding="utf8")
    folders = {"v2.6": "fresh_review_v26_control", "v2.7": "fresh_review_v27", "v2.8": "fresh_review_v28"}
    predictions, metrics = {}, {}
    for version, folder in folders.items():
        records = read(BASE / folder / "model_predictions.jsonl")
        pred = {r["id"]: r for r in records}
        assert len(records) == len(pred) == 100 and set(pred) == {p["id"] for p in packets}
        predictions[version] = pred
        agreed = sum(pred[r["id"]].get("label") == r["ai_label"] for r in reviews)
        subset = [r for r in reviews if r["review_status"] == "supported_proposal"]
        metrics[version] = dict(
            agreement_count=agreed, total=100,
            supported_subset_count=len(subset),
            supported_subset_agreement=sum(pred[r["id"]].get("label") == r["ai_label"] for r in subset),
            concrete_on_insufficient=sum(pred[r["id"]].get("label") != MANUAL
                                        for r in reviews if r["review_status"] == "input_insufficient"),
            label_errors=sum(bool(r.get("meta", {}).get("label_error")) for r in records))
    summary = dict(metrics=metrics, ai_distribution=dict(Counter(r["ai_label"] for r in reviews)),
                   review_status=dict(Counter(r["review_status"] for r in reviews)),
                   ground_truth_metrics=None)
    (BASE / "ai_review_v28_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf8")
    manifest = dict(created_at=datetime.now(timezone.utc).isoformat(),
                    input_sha256=digest(source), notes_sha256=digest(notes_path),
                    review_sha256=digest(out),
                    prompt_sha256=digest(ROOT / "training/data/prompts/policy_label_v2.8.md"),
                    prediction_sha256={v: digest(BASE / f / "model_predictions.jsonl") for v, f in folders.items()},
                    reviewer="Codex agent; exact backend model identifier unavailable",
                    api_calls=0, human_confirmed=False,
                    blinding="Individual predictions not opened during this review before notes were saved; prior aggregate distributions and conversation were visible. Not a fully blinded independent evaluation.",
                    comparison_standard="v2.8 for all versions; not performance under each historical standard")
    (BASE / "ai_review_v28_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
    lines = ["# 동일 100건 AI 검수 및 v2.6·v2.7·v2.8 대조", "",
             "추가 API 호출 0회. 기존 세 버전 예측을 재사용하고 Codex가 입력을 읽어 작성한 AI 검수안과 비교했다.",
             "사람 정답·실제 서비스 정책·학습 라벨이 아니다. 기존 라벨과 고정 test는 유지했다.",
             "개별 예측 대조 전에 검수안을 저장했다. 이전 집계와 대화는 이미 보았으므로 완전한 블라인드 검수는 아니다.",
             "모든 버전을 v2.8 기준으로 대조했다. 과거 버전 자체 기준의 정확도 평가가 아니다.", "",
             "| 버전 | AI 검수안 일치 / 100 | 근거 지지 구체 제안 일치 | 입력 부족 사례에서 구체 선택 |",
             "|---|---:|---:|---:|"]
    for v, m in metrics.items():
        lines.append(f"| {v} | {m['agreement_count']} | {m['supported_subset_agreement']}/{m['supported_subset_count']} | {m['concrete_on_insufficient']} |")
    lines += ["", "## 검수안 구성", "", f"- 라벨 분포: `{summary['ai_distribution']}`",
              f"- 상태 분포: `{summary['review_status']}`",
              "- standard_ambiguity: 인증된 참조 데이터의 public 의미 또는 계정의 개인/조직 경계. 확정 오답으로 계산하지 않는다.",
              "- weak_proposal: NFT URI·환전업체 참조 정보의 public 추정 2건. 실제 공개 허용이 검증된 것은 아니다.",
              "- input_insufficient: 제공 입력으로 단일 구체 정책을 지지하지 못함. 서비스가 실제로 무정책이라는 뜻이 아니다.",
              "- supported_proposal: 입력에 정책을 지지하는 근거가 있는 구체 제안. 사람 확정은 아니다.",
              "", "## 판단", "",
              "보류가 많은 검수안이므로 전체 일치율은 보류를 많이 낸 버전에 유리하다. 이를 정확도나 모델 우열로 해석하지 않는다.",
              "주요 검토 대상은 전역 scope 사전의 역할을 operation 요구로 전용하는 것, 관계 필드를 접근 조건으로 확정하는 것, 공개 콘텐츠와 익명 API를 혼동하는 것이다.",
              "현재 표본의 부족한 정책 근거는 프롬프트 재수정만으로 복구할 수 없다. 근거 있는 구체 사례와 부족 사례를 분리해 후속 코드 기반 표본으로 검증한다.",
              "", "## 개별 검수 100건", "",
              "| id | method·path | v2.6 | v2.7 | v2.8 | AI 제안 | 상태 | 근거·수정 방향 |",
              "|---|---|---|---|---|---|---|---|"]
    for r in reviews:
        cells = [r["id"], r["method"] + " " + r["path"]]
        cells += [predictions[v][r["id"]].get("label", "ERROR") for v in folders]
        cells += [r["ai_label"], r["review_status"], r["rationale"]]
        lines.append("| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in cells) + " |")
    (BASE / "ai_review_v26_v27_v28.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
