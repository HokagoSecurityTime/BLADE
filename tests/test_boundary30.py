import ast
import pytest
from training.experiments.boundary30 import extract,CONTRACTS


def test_rejection_negation_preserves_or():
    source='def access(a,b):\n    if not (a or b):\n        return False\n    return True\n'
    assert extract(source)=='a or b'


def test_de_morgan_does_not_drop_condition():
    source='def access(a,b):\n    if not a or not b:\n        return False\n    return True\n'
    assert extract(source)=='a and b'


def test_aliases_expand_without_label_advice():
    source="def access(actor, resource, memberships):\n    m = (actor['id'], resource['group_id']) in memberships\n    t = actor['tenant_id'] == resource['tenant_id']\n    return m and t\n"
    result=extract(source)
    assert 'membership_required' not in result and 'tenant_match' not in result
    assert ' and ' in result and ' in memberships' in result


def test_unknown_flow_rejected():
    with pytest.raises(ValueError):extract('def access(a):\n    for x in a:\n        return x\n')


def test_contract_has_six_patterns_and_abstention():
    assert len(CONTRACTS)==15
    assert len({label for _,label in CONTRACTS})==7
