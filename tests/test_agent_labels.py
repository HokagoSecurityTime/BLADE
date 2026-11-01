import pytest
from training.data.merge_agent_labels import validate_decision


def sample():
    source = dict(id='test', path='/items/{itemId}', oas_snippet='{"path_params":["itemId"]}',
        erd_snippet='CREATE TABLE items (\n  id TEXT,\n  owner_id TEXT\n);')
    decision = dict(id='test', label='owner_match', confidence=.7, rationale='Explicit fixture ownership evidence',
        object_param='itemId', owner_lookup=dict(table='items',id_col='id',owner_col='owner_id',tenant_col=None),
        roles=[],allowed_membership=[])
    return source, decision


def test_agent_decision_does_not_remap_low_confidence():
    source, decision = sample()
    decision['confidence'] = .4
    assert validate_decision(source, decision).label.value == 'owner_match'


@pytest.mark.parametrize('field,value', [('table','invented'),('id_col','unknown'),('owner_col','absent')])
def test_agent_decision_rejects_invented_lookup(field,value):
    source, decision = sample()
    decision['owner_lookup'][field] = value
    with pytest.raises(ValueError):
        validate_decision(source, decision)


def test_agent_decision_rejects_uninspected_missing_label():
    source, decision = sample()
    decision.pop('label')
    with pytest.raises(KeyError):
        validate_decision(source, decision)


def test_agent_decision_rejects_unknown_parameter():
    source, decision = sample()
    decision['object_param'] = 'userId'
    with pytest.raises(ValueError):
        validate_decision(source, decision)
