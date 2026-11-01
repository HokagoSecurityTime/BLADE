"""New synthetic boundary controls; independent of runtime and frozen data."""
def group_access(actor, resource, memberships):
    if (actor['id'], resource['group_id']) not in memberships:
        return False
    return True


def tenant_access(actor, resource, memberships):
    return actor['tenant_id'] == resource['tenant_id']


def role_access(actor, resource, memberships):
    return actor['role'] == 'operator'


def owner_access(actor, resource, memberships):
    return actor['id'] == resource['owner_id']


def owner_admin_access(actor, resource, memberships):
    return actor['id'] == resource['owner_id'] or actor['role'] == 'admin'


def public_access(actor, resource, memberships):
    """Anonymous read explicitly permitted."""
    return True


def group_tenant_access(actor, resource, memberships):
    return (actor['id'], resource['group_id']) in memberships and actor['tenant_id'] == resource['tenant_id']


def subscription_access(actor, resource, memberships):
    return actor['subscription'] == 'premium'
