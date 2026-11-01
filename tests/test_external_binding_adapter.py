import copy
import itertools
import pytest
from training.experiments.external_binding_adapter import extract, boolean, verify, check_snapshot, symbolic


@pytest.mark.parametrize('ident,formula',[
 ('items.read_item','owner or admin'),('items.update_item','owner or admin'),
 ('items.delete_item','owner or admin'),('users.read_user_by_id','owner or admin'),
 ('users.read_user_me','owner'),('login.test_token','owner'),
 ('users.delete_user_me','owner and not admin'),('users.delete_user','admin and not owner')])
def test_conditions(ident,formula):
    check_snapshot()
    e=extract(ident)
    for owner,admin in itertools.product([False,True],repeat=2):
        state=dict(owner=owner,admin=admin)
        assert boolean(e['allow'],state)==boolean(formula,state)


@pytest.mark.parametrize('ident,label',[
 ('users.delete_user_me','owner_match'),('users.delete_user','owner_or_admin'),
 ('users.read_user_me','membership_required'),('login.test_token','membership_required')])
def test_four_errors_blocked(ident,label):
    p=dict(label=label,confidence=.9);before=copy.deepcopy(p)
    g=verify(p,extract(ident))
    assert g['reason']=='missing_required_condition'
    assert not g['auto_apply_allowed'] and g['counterexample']
    assert p==before


def test_unknown_and_role_binding():
    assert extract('items.create_item')['status']=='unresolved'
    assert verify(dict(label='role_required'),extract('items.read_item'))['reason']=='role_parameter_unresolved'
    with pytest.raises(ValueError):symbolic('def f():\n    if arbitrary():\n        return True\n    return False',None)


def test_correct_and_stricter():
    e=extract('items.read_item')
    assert verify(dict(label='owner_or_admin'),e)['semantic_candidate_pass']
    assert verify(dict(label='owner_match'),e)['reason']=='overrestriction'
