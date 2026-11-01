from collections import Counter
from pathlib import Path
from pipeline.classifier.evaluate import load_dataset, score, summarize
from pipeline.classifier.schema import manual_review, ClassificationResult
from pipeline.classifier.prompt import build_user_prompt
from pipeline.parsers.erd import parse_erd

DATA = Path(__file__).resolve().parents[1]/'verification/classifier-holdout-v1.json'


def test_dataset_balanced_and_answers_excluded() -> None:
    dataset = load_dataset(DATA)
    assert len(dataset.cases) == 14
    assert set(Counter(c.expected_label for c in dataset.cases).values()) == {2}
    for case in dataset.cases:
        text = build_user_prompt(case.endpoint, parse_erd(case.ddl), case.controller_text)
        assert 'expected_label' not in text and 'expected_params' not in text and case.rationale not in text


def test_metrics_include_abstention_and_parameter_errors() -> None:
    dataset = load_dataset(DATA)
    public = ClassificationResult(label='public', confidence=1., evidence='test',
        object_param=None, owner_lookup=None, roles=[], allowed_membership=[])
    rows = [score(dataset.cases[0], public, 1), score(dataset.cases[6], manual_review('test'), 3)]
    summary = summarize(rows)
    assert summary['accuracy'] == .5
    assert summary['manual_review_rate'] == .5
    assert summary['automatic_accuracy'] == 1
    assert summary['full_policy_accuracy'] == .5
    assert summary['mean_seconds'] == 2
    assert summary['p95_seconds'] == 3
    assert summary['confusion_matrix']['owner_match']['manual_review_required'] == 1
    assert summary['per_label']['owner_match']['recall'] == 0


def test_empty_summary_is_not_perfect_score() -> None:
    summary = summarize([])
    assert summary['accuracy'] is None and summary['automatic_accuracy'] is None
