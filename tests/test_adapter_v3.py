import pytest
from training.experiments import adapter_v3 as a

def test_shared_guard(tmp_path):
    (tmp_path/'guards.py').write_text('def require_admin(user):\n    if not user.is_superuser:\n        raise HTTPException(status_code=403)\n    return user\n')
    (tmp_path/'routes.py').write_text('from guards import require_admin\n@router.get("/", dependencies=[Depends(require_admin)])\ndef renamed_handler():\n    return something()\n')
    hashes={p.name:a.sha(p) for p in tmp_path.glob('*.py')}
    result=a.analyze(tmp_path,'routes.py','renamed_handler',hashes)
    assert result['necessary_conditions']==['admin']
    assert not result['complete_context']
    assert a.verify(dict(label='owner_or_admin'),result)['reason']=='violates_proven_necessary_condition'
    assert not a.verify(dict(label='role_required'),result)['semantic_candidate_pass']
    (tmp_path/'guards.py').write_text('changed')
    with pytest.raises(a.IntegrityError,match='unverified'):a.analyze(tmp_path,'routes.py','renamed_handler',hashes)

def test_filter_is_not_complete(tmp_path):
    p=tmp_path/'r.py';p.write_text('def f():\n    return select(Item).where(Item.owner_id == user.id)\n')
    result=a.analyze(tmp_path,'r.py','f',{'r.py':a.sha(p)})
    assert result['status']=='unresolved'
    assert result['evidence'][0]['kind']=='orm_filter_candidate'
