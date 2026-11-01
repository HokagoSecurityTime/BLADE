from training.experiments.policy_conditions import extract, map_label


def parse(body):
    code='@app.get("/x")\ndef endpoint(user, item):\n'+''.join('    '+x+'\n' for x in body.splitlines())
    excerpt=dict(path='fixture.py',sha256='test',start=1,code=code)
    return extract([excerpt],'GET','/x')


def test_data_owner_is_not_a_guard():
    result=parse('return {"owner": "alice"}')
    assert result['conditions'] is None
    assert map_label(result)[0]=='manual_review_required'


def test_negated_and_is_allow_or():
    result=parse('if user["sub"] != item["owner"] and user["role"] != "admin":\n    raise HTTPException(403)\nreturn item')
    assert result['conditions']['op']=='or'
    assert map_label(result)[0]=='owner_or_admin'


def test_negated_or_is_allow_and_not_admin_bypass():
    result=parse('if user["sub"] != item["owner"] or user["role"] != "admin":\n    raise HTTPException(403)\nreturn item')
    assert result['conditions']['op']=='and'
    assert map_label(result)[0]=='manual_review_required'


def test_independent_checks_preserved():
    result=parse('if user["sub"] != item["owner"]:\n    raise HTTPException(403)\nif user["tenant"] != item["tenant"]:\n    raise HTTPException(403)\nreturn item')
    assert result['conditions']['op']=='and'
    assert len(result['conditions']['args'])==2
    assert map_label(result)[0]=='manual_review_required'


def test_unknown_call_and_early_return_fail_closed():
    for body in ['authorize(user)\nreturn item','db.authorize(user)\nreturn item','return item\nif user["role"] != "admin":\n    raise HTTPException(403)']:
        assert map_label(parse(body),positive_public=True)[0]=='manual_review_required'


def test_no_auth_evidence_is_not_public_evidence():
    result=parse('return item')
    assert map_label(result)[0]=='manual_review_required'
    assert map_label(result,positive_public=True)[0]=='public'


def test_unknown_field_relationship_abstains():
    result=parse('if user["account"] != item["account"]:\n    raise HTTPException(403)\nreturn item')
    assert map_label(result)[0]=='manual_review_required'
