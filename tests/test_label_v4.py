from training.data import label_v4 as v4
import asyncio
import json
import httpx

def test_security_preserves_explicit_empty_override():
    assert v4.security_state({'security':[{'key':[]}]},{'security':[]})=='explicitly_anonymous'
    assert v4.security_state({}, {'security':[]})=='declared'
    assert v4.security_state({'components':{'securitySchemes':{'key':{}}}}, {})=='unknown'
    assert v4.security_state({'security':[{'key':[]}]},{})=='declared'

def test_evidence_checks_actual_names_not_substrings():
    data={'path':'/me/notes/{id}','path_params':[{'name':'id'}],'query_params':[], 'schema_fields':['owner_id'],'owner_cols':['owner_id'],'tenant_cols':[]}
    assert not v4.invalid_evidence(['path_segment:me','path_params:id','schema_fields:owner_id','description'],data)
    assert v4.invalid_evidence(['path_segment:admin','schema_fields:owner','query_params:id'],data)==['path_segment:admin','schema_fields:owner','query_params:id']

def test_stratified_pilot_and_boundaries():
    old=[{'id':label+str(i),'label':label} for label in v4.LABELS for i in range(40)]
    ids=v4.select(old)
    assert ids==v4.select(old) and len(set(ids))==200
    assert sum(x.startswith('membership_required') for x in ids)==20
    assert [v4.bin_index(x) for x in [.5,.6,.7,.9,1]]==[0,1,2,3,3]

def test_gate_counts_patch_and_exact_thresholds():
    rows=[{'id':str(i),'method':'GET','label':'owner_match','confidence':(.6 if i<140 else .9),'meta':{}} for i in range(200)]
    old={r['id']:dict(r) for r in rows}
    assert 'confidence_bin_at_least_70_percent' in v4.summary(rows,old)['stop_reasons']
    rows[0].update(method='PATCH',label='public')
    result=v4.summary(rows,old)
    assert result['mutation_public']==1 and 'mutation_public_present' in result['stop_reasons']

def test_invalid_evidence_one_reask_retains_label_and_counts_usage(tmp_path,monkeypatch):
    value={'path':'/me/notes/{id}','path_params':[], 'query_params':[], 'schema_fields':[], 'owner_cols':[], 'tenant_cols':[], 'security_state':'declared'}
    monkeypatch.setattr(v4,'payload',lambda row:value)
    calls=[]
    async def handler(request):
        calls.append(json.loads(request.content))
        out={'label':'owner_match','confidence':.6,'rationale':'path: /me/notes/{id}','evidence_fields':['schema_fields:invented']}
        return httpx.Response(200,json={'id':str(len(calls)),'status':'completed','model':'fake','usage':{'input_tokens':10,'output_tokens':5},'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(out)}]}]})
    async def execute():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await v4.request({'id':'x','meta':{}},'JSON',v4.llm.Settings('openai','gpt-4o-mini','fake'),client,tmp_path/'usage.jsonl')
    result=asyncio.run(execute())
    assert len(calls)==2 and result['label']=='owner_match'
    assert result['meta']['evidence_invalid'] and result['meta']['evidence_correction_requested']
    assert len(v4.read(tmp_path/'usage.jsonl'))==2

def test_quota_stops_without_retries(tmp_path,monkeypatch):
    import pytest
    monkeypatch.setattr(v4,'payload',lambda row:{'security_state':'unknown'})
    calls=[]
    async def handler(request):
        calls.append(request)
        return httpx.Response(429,json={'error':{'code':'insufficient_quota'}})
    async def execute():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            await v4.request({'id':'x','meta':{}},'JSON',v4.llm.Settings('openai','gpt-4o-mini','fake'),client,tmp_path/'usage.jsonl')
    with pytest.raises(v4.StopRun):asyncio.run(execute())
    assert len(calls)==1

def test_reporting_does_not_mutate_gate_result(tmp_path,monkeypatch):
    monkeypatch.setattr(v4,'HERE',tmp_path)
    monkeypatch.setattr(v4,'costs',lambda:{'api_responses':0})
    result={'transitions':{a:{b:0 for b in v4.LABELS} for a in v4.LABELS},'stop_reasons':['test']}
    v4.report('test_report',result)
    assert 'usage' not in result
