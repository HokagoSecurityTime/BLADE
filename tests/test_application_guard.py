import copy
import pytest
from training.experiments.application_guard import ATOMS, verify


def source(formula):
    return 'def access(actor, resource, memberships):\n' + ''.join(f'    {k} = {v}\n' for k, v in ATOMS.items()) + f'    return {formula}\n'


@pytest.mark.parametrize('formula,label,reason', [
    ('m and t', 'membership_required', 'missing_required_condition'),
    ('o and a', 'owner_or_admin', 'missing_required_condition'),
    ('o', 'role_required', 'missing_required_condition'),
    ('m', 'membership_required', 'equivalent'),
    ('o or a', 'owner_match', 'overrestriction'),
    ('True', 'public', 'equivalent'),
])
def test_gate(formula, label, reason):
    pred = dict(label=label, confidence=.8)
    before = copy.deepcopy(pred)
    result = verify(pred, source(formula), complete_context=True, fixture_bindings=True)
    assert result['reason'] == reason
    assert result['original_label'] == label and pred == before
    assert result['auto_apply_allowed'] is False
    assert result['semantic_candidate_pass'] == (reason == 'equivalent')


def test_unverified_and_unknown():
    pred = dict(label='owner_match')
    assert verify(pred, source('o'))['reason'] == 'context_or_binding_unverified'
    assert verify(pred, source('unknown()'), complete_context=True, fixture_bindings=True)['reason'] == 'unsupported_code'


def test_rebinding_fail_closed():
    assert verify(dict(label='public'), "def access(actor, resource, memberships):\n    actor = True\n    return True", complete_context=True, fixture_bindings=True)['reason'] == 'unsupported_code'


def test_manual_preserved():
    result = verify(dict(label='manual_review_required', confidence=.3), source('True'), complete_context=True, fixture_bindings=True)
    assert result['original_label'] == 'manual_review_required'
    assert not result['semantic_candidate_pass']
