from collections.abc import Iterator
from pathlib import Path
import time

import jwt
import pytest
from fastapi.testclient import TestClient

from demo_backend.main import create_app


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    with TestClient(create_app(tmp_path / "demo.db")) as test_client:
        yield test_client


@pytest.mark.parametrize(("method", "path"), [
    ("GET", "/public/health"),
    ("GET", "/orders/1042"),
    ("DELETE", "/orders/1042"),
    ("GET", "/users/user_77"),
    ("GET", "/admin/reports"),
    ("GET", "/orgs/org_1/docs"),
    ("GET", "/premium/content"),
])
def test_endpoints_return_200(client: TestClient, method: str, path: str) -> None:
    assert client.request(method, path).status_code == 200
    if method == "DELETE":
        assert client.get(path).status_code == 404


def test_bola_user_99_can_read_user_77_order(client: TestClient) -> None:
    # Deliberately proves the vulnerability; backend ignores authorization.
    token = jwt.encode({"sub": "user_99", "roles": ["user"], "tenant_id": "org_2",
                        "membership": "basic", "exp": int(time.time()) + 3600},
                       "demo-test-secret-at-least-32-bytes", algorithm="HS256")
    response = client.get("/orders/1042", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"id": 1042, "user_id": "user_77"}
