import pytest
from pydantic import ValidationError

from common.labels import Label
from common.schema import JWTClaims, policy_from_yaml, policy_to_yaml


def test_policy_yaml_round_trip() -> None:
    policy = policy_from_yaml('''
id: pol_orders_get_by_id
endpoint: {method: GET, path: '/orders/{orderId}'}
label: owner_match
params:
  object_param: orderId
  owner_lookup: {table: orders, id_col: id, owner_col: user_id, tenant_col: null}
  roles: []
  allowed_membership: []
confidence: 0.91
evidence: "orders.user_id FK → users.id"
status: PENDING
created_at: "2026-09-08T10:00:00Z"
''')
    assert policy.label is Label.OWNER_MATCH
    assert policy_from_yaml(policy_to_yaml(policy)) == policy
    with pytest.raises(ValidationError):
        policy_from_yaml(policy_to_yaml(policy).replace("0.91", "1.5"))


def test_jwt_claims_documented_shape() -> None:
    claims = {"sub": "user_99", "roles": ["user"], "tenant_id": "org_1",
              "membership": "basic", "exp": 0}
    assert JWTClaims.model_validate(claims).model_dump() == claims
    assert len(Label) == 7
