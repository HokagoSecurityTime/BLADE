import json
import pytest

from scripts.eval_classifier import endpoint_input, controller_source, metrics
from scripts.eval_classifier import classify_recorded, diagnostic_metrics
from pipeline.classifier import llm
from pipeline.parsers.oas import Endpoint


@pytest.mark.parametrize('label,confidence,lookup,event,final', [
    ('public', .9, None, None, 'public'),
    ('public', .6, None, 'confidence_below_0.7', 'manual_review_required'),
    ('manual_review_required', .9, None, None, 'manual_review_required'),
    ('invented', .9, None, 'unknown_label', 'manual_review_required'),
    ('owner_match', .9, {'table':'things','id_col':'id','owner_col':'user_id','tenant_col':None},
     'Unknown lookup table or id column', 'manual_review_required'),
])
def test_raw_trace_preserves_response_and_runtime_decision(monkeypatch, label, confidence, lookup, event, final):
    monkeypatch.setenv('BLADE_RAG_ENABLED', 'false')
    raw = json.dumps(dict(label=label, confidence=confidence, evidence='test evidence',
        object_param='id' if lookup else None, owner_lookup=lookup, roles=[], allowed_membership=[]))
    calls = []
    def complete(*a, **kw):
        calls.append(1)
        return raw
    monkeypatch.setattr(llm, 'complete', complete)
    result, trace = classify_recorded(Endpoint('GET', '/things/{id}', ['id'], [], None, [], None), {})
    assert calls == [1]
    assert llm.complete is complete
    assert trace['raw_response'] == raw and trace['raw_label'] == label
    assert trace['raw_confidence'] == confidence
    assert result.label.value == final
    assert trace['validation_events'] == ([event] if event else [])


@pytest.mark.parametrize('failure', ['json', 'schema', 'transport'])
def test_failed_output_is_recorded_without_second_call(monkeypatch, failure):
    monkeypatch.setenv('BLADE_RAG_ENABLED', 'false')
    def complete(*a, **kw):
        if failure == 'transport':
            raise llm.LLMError('test failure')
        return '{' if failure == 'json' else '{"label":"public"}'
    monkeypatch.setattr(llm, 'complete', complete)
    result, trace = classify_recorded(Endpoint('GET', '/health', [], [], None, [], None), {})
    assert result.label.value == 'manual_review_required'
    assert llm.complete is complete
    assert trace['validation_events'] == (['LLM unavailable: test failure'] if failure == 'transport' else ['json_or_schema_invalid'])


def test_diagnostic_metrics_count_invalid_raw_as_error_and_track_score_loss():
    def row(expected, raw, final):
        return dict(expected=expected, prediction=final, inference_ms=1, error=None,
                    controller_status='disabled', retrieved=[], trace=dict(raw_label=raw,
                    label_changed=raw != final, validation_events=[]))
    result = diagnostic_metrics([
        row('public', 'public', 'manual_review_required'),
        row('manual_review_required', None, 'manual_review_required'),
    ])
    assert result['correct_to_wrong'] == 1 and result['wrong_to_correct'] == 1
    assert result['invalid_raw_labels'] == 1
    assert result['raw']['per_label']['manual_review_required']['recall'] == 0
    assert result['raw']['confusion_matrix']['manual_review_required']['__invalid__'] == 1
    assert diagnostic_metrics([]) is None


def test_evaluation_metrics_include_false_positive_and_missing_labels():
    rows = [dict(expected='public', prediction='public', inference_ms=10, error=None,
                 controller_status='disabled', retrieved=[]),
            dict(expected='owner_match', prediction='public', inference_ms=30,
                 error='invalid_model_output_schema', controller_status='disabled', retrieved=[])]
    result = metrics(rows)
    assert result['per_label']['public']['precision'] == .5
    assert result['per_label']['owner_match']['recall'] == 0
    assert result['macro_f1'] == (2/3)/7
    assert result['mean_inference_ms'] == 20
    assert result['errors'] == {'invalid_model_output_schema': 1}


def test_evaluation_inputs_do_not_include_human_annotations():
    row = dict(id='sample', source='vuln', service='example', method='GET', path='/things/{thingId}',
               label='owner_match', rationale='SECRET HUMAN ANSWER', proposed_label='owner_match',
               oas_snippet='invalid', erd_snippet='', controller_text='def handler(): return 1')
    endpoint, erd, warnings = endpoint_input(row)
    assert endpoint.path_params == ['thingId']
    assert endpoint.summary is None and erd == {}
    assert warnings == ['oas_parser_fallback_to_route_metadata']
    assert controller_source(row) == ('def handler(): return 1', 'dataset_controller_text')


def test_malformed_erd_is_explicit_missing_context():
    row = dict(method='GET', path='/health', oas_snippet=json.dumps({'openapi':'3.0.0',
               'paths':{'/health':{'get':{}}}}), erd_snippet='DROP TABLE things;')
    _, tables, warnings = endpoint_input(row)
    assert tables == {}
    assert warnings == ['erd_parser_failed_empty_context']
