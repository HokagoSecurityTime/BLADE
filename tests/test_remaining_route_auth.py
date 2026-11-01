"""Pinned-source auth traversal regression; no network or app startup."""
import pytest
from training.experiments.audit_remaining_routes import RAW, auth_dependencies
from training.experiments.fastapi_condition_adapter import Adapter

pytestmark=pytest.mark.skipif(not (RAW/'manifest.json').exists(),reason='external source snapshot not collected')


@pytest.mark.parametrize('file,handler,expected',[
    ('articles/articles_resource.py','retrieve_article_by_slug',{'optional'}),
    ('profiles.py','retrieve_profile_by_username',{'optional'}),
    ('users.py','update_current_user',{'required'}),
    ('authentication.py','login',set()),
    ('tags.py','get_all_tags',set()),
])
def test_auth_dependency_transitivity(file,handler,expected):
    path=RAW/'app/api/routes'/file;a=Adapter(RAW)
    found=auth_dependencies(a,path,a.module(path)[1][handler])
    assert {v['state'] for v in found}==expected
