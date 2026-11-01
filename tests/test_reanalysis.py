from dataclasses import asdict
from pathlib import Path
from unittest.mock import Mock

from fastapi.testclient import TestClient
import pytest

from admin_api.main import create_app
from admin_api.proposals import Proposals
from admin_api.workers.reanalysis import run_once, summarize, trigger
from common.schema import policy_from_yaml
from pipeline.classifier.schema import ClassificationResult
from pipeline.classifier import classify, llm
from common.schema import EvidenceRef
from pipeline.parsers.erd import parse_erd
from pipeline.parsers.oas import parse_oas
from tests.test_alerts import record
from tests.test_proxy import policy


@pytest.fixture
def setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv('BLADE_PHASE2_ENABLED','true')
    monkeypatch.setenv('BLADE_REDIS_ENABLED','false')
    monkeypatch.setenv('BLADE_RAG_ENABLED','false')
    app = create_app(tmp_path/'blade.db',tmp_path/'policies',tmp_path/'logs.jsonl')
    with TestClient(app) as client:
        p=policy('manual_review_required')
        p.params.owner_lookup=None; p.params.object_param=None
        ep=next(e for e in parse_oas(Path('demo_backend/openapi.json').read_text()) if e.path=='/orders/{orderId}' and e.method=='GET')
        context=dict(endpoint=asdict(ep),erd={k:asdict(v) for k,v in parse_erd(Path('demo_backend/schema.sql').read_text()).items()},controller=None)
        app.state.store.insert_many([p],{p.id:context})
        yield app.state.store,client,p


def test_threshold_proposal_accept_and_pending_dedup(setup,monkeypatch: pytest.MonkeyPatch) -> None:
    store,client,p=setup
    result=ClassificationResult(label='owner_match',confidence=.95,evidence='orders.user_id FK',object_param='orderId',
        owner_lookup=dict(table='orders',id_col='id',owner_col='user_id'),roles=[],allowed_membership=[])
    complete=Mock(return_value=result)
    monkeypatch.setattr('admin_api.workers.reanalysis.classify',complete)
    for i in range(19):
        store.append_detection(record('OBSERVE').model_copy(update={'policy_id':p.id,'request_id':str(i)}))
    assert run_once(store)==[]
    store.append_detection(record('OBSERVE').model_copy(update={'policy_id':p.id,'request_id':'20'}))
    proposal=run_once(store)[0]
    assert store.get(p.id).label=='manual_review_required'  # never auto-apply
    assert run_once(store)==[] and complete.call_count==1
    assert client.get('/policies/'+p.id+'/proposals').json()[0]['id']==proposal['id']
    accepted=client.post(f'/proposals/{proposal["id"]}/accept')
    assert accepted.status_code==200,accepted.text
    assert accepted.json()['version']==2 and accepted.json()['mode']=='observe'
    assert accepted.json()['source']=='reanalysis' and accepted.json()['status']=='ACTIVE'
    assert client.post(f'/proposals/{proposal["id"]}/accept').status_code==409
    assert policy_from_yaml((store.policy_dir/(p.id+'.yaml')).read_text()).version==2


def test_rollback_and_high_ratio_and_fingerprints(setup) -> None:
    store,client,p=setup
    assert client.post('/policies/'+p.id+'/rollback').status_code==200
    proposals=Proposals(store)
    rows,_,event=proposals.inputs(p.id)
    assert trigger(store.get(p.id),rows,proposals.rollback_pending(p.id,event))=='rollback'
    object_policy=policy()
    rows=[record('OBSERVE').model_copy(update={'sub':f'private_user_{u}','would_block':True}).model_dump(mode='json',context={'storage':True}) for u in range(3) for _ in range(5)]
    assert trigger(object_policy,rows)=='high_would_block_ratio'
    assert trigger(object_policy,rows[:5]) is None
    summary=summarize(object_policy,rows)
    assert summary['unique_patterns']==3 and summary['distinct_object_ids']==1
    assert 'private_user' not in str(summary) and '1042' not in str(summary)


def test_stale_dismiss_and_feature_off(setup,monkeypatch: pytest.MonkeyPatch) -> None:
    store,client,p=setup
    proposals=Proposals(store)
    item=proposals.create(p,p.model_copy(update={'version':2}), 'test')
    assert client.post('/policies/'+p.id+'/mode',json={'mode':'enforce'}).status_code==200
    assert client.post(f'/proposals/{item["id"]}/accept').status_code==409
    assert client.post(f'/proposals/{item["id"]}/dismiss').json()['status']=='DISMISSED'
    monkeypatch.setenv('BLADE_REANALYSIS_ENABLED','false')
    assert run_once(store)==[]
    assert client.get('/policies/'+p.id+'/proposals').status_code==404


def test_rejected_policy_cannot_be_revived(setup) -> None:
    store,client,p=setup
    assert client.post('/policies/'+p.id+'/rollback').status_code==200
    pending=store.get(p.id)
    item=Proposals(store).create(pending,pending,'test')
    assert client.post('/policies/'+p.id+'/reject').status_code==200
    assert client.post(f'/proposals/{item["id"]}/accept').status_code==409


def test_compact_output_restores_actual_citation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('BLADE_PHASE2_ENABLED','true')
    monkeypatch.setenv('BLADE_RAG_ENABLED','true')
    endpoint=next(e for e in parse_oas(Path('demo_backend/openapi.json').read_text()) if e.path=='/public/health')
    ref=EvidenceRef(kind='code',ref='health.py:health',snippet='def health(): return {"status": "ok"}')
    mock=Mock(return_value='{"label":"public","confidence":0.9,"evidence":"Unrestricted health check","object_param":null,"owner_lookup":null,"roles":[],"allowed_membership":[],"evidence_refs":[{"kind":"code","ref":"health.py:health","snippet":""}]}')
    monkeypatch.setattr(llm,'complete',mock)
    result=classify(endpoint,{},evidence_refs=[ref],analysis_context={'traffic_summary':{}})
    assert result.evidence_refs==[ref]
    assert mock.call_args.kwargs['response_schema']['$defs']['EvidenceRef']['properties']['snippet']['const']==''
    assert mock.call_args.kwargs['response_schema']['$defs']['EvidenceRef']['properties']['ref']['enum']==[ref.ref]
