import httpx
import pytest
from training.data.label_v3 import payload,quota_error,Output,summarize


def test_full_description_and_response_only_fields():
    row=dict(method='GET',path='/x',oas_snippet='{}',meta={'owner_cols':['user_id'],'tenant_cols':[]},
        enrichment={'operation':{'summary':'s','description':'a'*10000},'security':{'effective':[]},
        'trees':{'responses':{'200':{'schema':{'properties':{f'p{i}':{'type':'string'} for i in range(50)}}},'default':{'schema':{'properties':{'error':{}}}}}},'references':{}})
    result=payload(row)
    assert len(result['description'])==10000 and len(result['schema_fields'])==40
    assert 'error' not in result['schema_fields'] and result['security']==[]


def test_quota_vs_temporary_rate_limit():
    assert quota_error(httpx.Response(429,json={'error':{'code':'credit_balance_exhausted'}}))=='credit_balance_exhausted'
    assert quota_error(httpx.Response(429,json={'error':{'message':'Requests per day exhausted'}}))=='daily_limit_exhausted'
    assert quota_error(httpx.Response(429,json={'error':{'message':'Requests per minute'}})) is None


def test_uncertainty_does_not_change_label():
    result=Output(label='owner_match',confidence=.51,rationale='User path scope.',evidence_fields=['path'])
    assert result.label.value=='owner_match'
    with pytest.raises(ValueError):Output(label='invented',confidence=.5,rationale='x',evidence_fields=['path'])


def test_field_limit_stops_expanding_large_reference_graph():
    class Explosive(dict):
        def items(self):raise AssertionError('Must not inspect fields after limit')
    props={f'p{i}':{'type':'string'} for i in range(40)}
    props['large']={'properties':Explosive()}
    row=dict(method='GET',path='/x',oas_snippet='{}',meta={'owner_cols':[],'tenant_cols':[]},
        enrichment={'operation':{},'security':{'effective':None},'trees':{'responses':{'200':{'schema':{'properties':props}}}}})
    assert len(payload(row)['schema_fields'])==40
