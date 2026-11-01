import pytest
from training.experiments.external_binding_adapter_v2 import symbolic, extract
from training.experiments.external_binding_adapter import boolean

def test_masked_denial():
    f=symbolic('def f(current_user,item):\n    if item.owner_id != current_user.id:\n        raise Denied(status_code=404)\n    return item')
    assert not boolean(f,dict(owner=False,admin=False))
    assert boolean(f,dict(owner=True,admin=False))

def test_assert_mode():
    s='def f(current_user,item):\n    assert item.owner_id == current_user.id\n    return item'
    with pytest.raises(ValueError):symbolic(s)
    assert not boolean(symbolic(s,assertions_enabled=True),dict(owner=False))

def test_unknown_call():
    with pytest.raises(ValueError):symbolic('def f(current_user,item):\n    check(item)\n    return item')

def test_helper():
    f=symbolic('def f(current_user,item):\n    guard(current_user,item)\n    return item',helpers={'guard':'def guard(u,o):\n    if o.owner_id != u.id:\n        raise Denied(status_code=403)'})
    assert not boolean(f,dict(owner=False))
    assert boolean(f,dict(owner=True))

def test_integrity_entry(monkeypatch):
    def fail():raise ValueError('hash changed')
    monkeypatch.setattr('training.experiments.external_binding_adapter_v2.v1.check_snapshot',fail)
    with pytest.raises(ValueError,match='hash changed'):extract('users.read_user_me')
