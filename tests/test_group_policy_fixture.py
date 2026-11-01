from training.experiments import group_policy_fixture as f


def test_tenant_and_subscription_do_not_imply_group_membership():
    actor=dict(id='bob',tenant_id='north',subscription='premium')
    resource=dict(group_id='a',tenant_id='north')
    relations={('bob','b')}
    assert f.tenant_access(actor,resource,relations)
    assert f.subscription_access(actor,resource,relations)
    assert not f.group_access(actor,resource,relations)


def test_cross_tenant_group_member_and_independent_and():
    actor=dict(id='carol',tenant_id='south')
    resource=dict(group_id='a',tenant_id='north')
    relations={('carol','a')}
    assert f.group_access(actor,resource,relations)
    assert not f.tenant_access(actor,resource,relations)
    assert not f.group_tenant_access(actor,resource,relations)


def test_admin_not_universal_group_bypass():
    actor=dict(id='admin-user',role='admin')
    resource=dict(group_id='a',owner_id='someone-else')
    assert f.owner_admin_access(actor,resource,set())
    assert not f.owner_access(actor,resource,set())
    assert not f.group_access(actor,resource,set())


def test_explicit_public_allows_anonymous():
    assert f.public_access(None,{},set())
