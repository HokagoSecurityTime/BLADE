import itertools
import pytest
from training.experiments.external_orm_adapter import extract, normalize
from training.experiments.external_binding_adapter import boolean
from training.experiments.external_binding_adapter_v2 import symbolic

@pytest.mark.parametrize('ident,expected',[
 ('items.read_item','owner or admin'),('items.update_item','owner or admin'),('items.delete_item','owner or admin'),
 ('users.read_user_by_id','owner or admin'),('users.read_user_me','owner'),('login.test_token','owner'),
 ('users.delete_user_me','owner and not admin'),('users.delete_user','admin and not owner')])
def test_original_conditions(ident,expected):
    e=extract(ident)
    assert e['status']=='extracted'
    for owner,admin in itertools.product([False,True],repeat=2):
        state=dict(owner=owner,admin=admin)
        assert boolean(e['allow'],state)==boolean(expected,state)

def test_unknown_call_held():
    normalized,binding,_=normalize('def f(current_user, session, id):\n    item = session.get(Item, id)\n    hidden_guard(item)\n    return item')
    with pytest.raises(ValueError,match='unresolved call'):symbolic(normalized,binding['target'])

def test_404_owner_not_removed():
    normalized,binding,_=normalize('def f(current_user, session, id):\n    item = session.get(Item, id)\n    if item.owner_id != current_user.id:\n        raise HTTPException(status_code=404)\n    return item')
    formula=symbolic(normalized,binding['target'])
    assert not boolean(formula,dict(owner=False))

def test_entry_integrity(monkeypatch):
    def fail():raise ValueError('changed source')
    monkeypatch.setattr('training.experiments.external_orm_adapter.base.check_snapshot',fail)
    with pytest.raises(ValueError,match='changed source'):extract('items.read_item')
