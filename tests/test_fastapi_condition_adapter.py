import ast
from types import SimpleNamespace
import pytest
from training.experiments.fastapi_condition_adapter import Adapter, Unsupported, evaluate


@pytest.fixture
def project(tmp_path):
    def put(name,text):
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf8');return p
    put('app/services/policy.py','def allowed(resource, caller):\n    return resource.author.username == caller.username\n')
    put('app/api/dependencies/policy.py', '''from fastapi import Depends, HTTPException
from starlette import status
from app.api.dependencies.authentication import get_current_user_authorizer
from app.services.policy import allowed as verify
def guard(document=Depends(fetch_document), user=Depends(get_current_user_authorizer())):
    if not verify(document, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
''')
    route=put('app/routes.py','''from fastapi import Depends
from app.api.dependencies.policy import guard as enforce
@router.delete('/{id}', dependencies=[Depends(enforce)])
async def remove_record():
    await database.delete()
''')
    return tmp_path,route,put


def test_async_import_aliases_and_binding(project):
    root,path,_=project;a=Adapter(root)
    result=a.route(path,a.module(path)[1]['remove_record'])
    assert result['endpoint_final_label'] is None
    guard=result['guards'][0]
    assert guard['condition_label_proposal']=='owner_match'
    assert guard['condition']['left']==['document','author','username']
    assert guard['condition']['right']==['user','username']
    assert guard['guard_ref']['start']>0


def test_missing_import_does_not_guess(project):
    root,path,put=project
    put('app/api/dependencies/policy.py','from unknown import something\n')
    a=Adapter(root);result=a.route(path,a.module(path)[1]['remove_record'])
    assert not result['guards'] and result['unresolved']


def test_404_is_not_authorization(project):
    root,path,put=project
    p=root/'app/api/dependencies/policy.py'
    p.write_text(p.read_text().replace('HTTP_403_FORBIDDEN','HTTP_404_NOT_FOUND'),encoding='utf8')
    a=Adapter(root);assert not a.route(path,a.module(path)[1]['remove_record'])['guards']


def test_boolean_expression_preserves_or_and_not(project):
    root,path,put=project
    put('app/services/policy.py','def allowed(resource, caller):\n    return resource.author.username == caller.username or not (resource.tenant == caller.tenant)\n')
    a=Adapter(root);r=a.route(path,a.module(path)[1]['remove_record'])['guards'][0]
    assert r['condition_label_proposal'] is None
    bindings={'document':SimpleNamespace(author=SimpleNamespace(username='alice'),tenant='one'),
              'user':SimpleNamespace(username='bob',tenant='two')}
    assert evaluate(r['condition'],bindings)
    bindings['user'].tenant='one'
    assert not evaluate(r['condition'],bindings)


def test_predicate_with_side_effect_rejected(project):
    root,path,put=project
    put('app/services/policy.py','def allowed(resource, caller):\n    audit()\n    return resource.author.username == caller.username\n')
    a=Adapter(root);assert not a.route(path,a.module(path)[1]['remove_record'])['guards']


def test_source_root_boundary(project):
    root,path,_=project
    with pytest.raises(Unsupported):Adapter(root).module(root.parent/'outside.py')
