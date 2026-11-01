"""Experimental data separation, local call slicing, and HTTP policy boundaries."""
import json
from pathlib import Path

from fastapi.testclient import TestClient
from training.experiments import paired_policy_fixture as fixture
from training.experiments.paired_policy import CONTRACT, closure, paired, payload


def test_call_slice_excludes_unrelated_handlers_and_policies():
    spans, edges, names = closure(Path(fixture.__file__), "observations")
    assert names == ["actor", "guard_a", "load", "observations"]
    assert ["observations", "guard_a"] in edges
    text = "\n".join(s["code"] for s in spans)
    assert "def guard_b" not in text
    assert "def forecasts" not in text
    assert "owner_match" not in text


def test_pair_only_changes_code_description():
    spec = fixture.app.openapi()
    spans, _, _ = closure(Path(fixture.__file__), "observations")
    conditions = paired(payload(spec, "/observations/{item_id}", "GET"), spans)
    a, b = conditions["oas_only"], conditions["oas_code"]
    assert {k:v for k,v in a.items() if k != "description"} == {k:v for k,v in b.items() if k != "description"}
    assert b["description"].startswith(a["description"])
    for forbidden in ["evaluation_target", "intended_policy", "scoring_eligible", "expected", "contract"]:
        assert forbidden not in a and forbidden not in b


def test_owner_and_tenant_are_not_interchangeable():
    with TestClient(fixture.app) as client:
        bob = {"Authorization":"Bearer bob"}
        alice_south = {"Authorization":"Bearer alice_south"}
        assert client.get("/observations/sample", headers=bob).status_code == 403
        assert client.get("/allocations/sample", headers=bob).status_code == 200
        assert client.get("/observations/sample", headers=alice_south).status_code == 200
        assert client.get("/allocations/sample", headers=alice_south).status_code == 403
        assert client.get("/transfers/sample", headers=alice_south).status_code == 403


def test_admin_bypass_is_not_universal():
    with TestClient(fixture.app) as client:
        admin={"Authorization":"Bearer dana"}
        assert client.get("/captures/sample",headers=admin).status_code == 200
        for path in ["observations", "allocations", "spectra", "queues"]:
            assert client.get(f"/{path}/sample",headers=admin).status_code == 403


def test_contract_covers_six_concrete_labels_and_compound_abstentions():
    contract=json.loads(CONTRACT.read_text(encoding="utf8"))
    labels={r["label"] for r in contract["policies"]}
    assert len(labels)==7
    assert sum(len(r["handlers"]) for r in contract["policies"])==14
