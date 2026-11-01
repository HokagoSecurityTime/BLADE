import asyncio,json
import httpx
from training.data import label_v5 as v5

def test_low_confidence_label_is_preserved(tmp_path,monkeypatch):
    monkeypatch.setattr(v5,'payload',lambda row:{'security_state':'unknown'})
    async def handler(request):
        value={'label':'owner_match','confidence':.4,'rationale':'path: /notes/{id}','evidence_fields':['path']}
        return httpx.Response(200,json={'id':'test','status':'completed','model':'fake','usage':{},'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(value)}]}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await v5.request({'id':'test','method':'GET','meta':{}},'JSON',v5.llm.Settings('openai','gpt-4o-mini','fake'),client,tmp_path/'usage.jsonl')
    result=asyncio.run(run())
    assert result['label']=='owner_match' and not result['meta']['confidence_label_overridden']

def test_anonymous_mutation_allowed_no_public_rate_gate():
    rows=[{'id':str(i),'label':'public','confidence':(.6 if i<100 else .9),'method':'POST','security_state':'explicitly_anonymous','meta':{}} for i in range(200)]
    old={r['id']:r for r in rows}
    assert not v5.summary(rows,old)['stop_reasons']
    rows[0]['security_state']='unknown'
    assert not v5.summary(rows,old)['stop_reasons']
    assert v5.review_flag(rows[0])

def test_manual_threshold():
    rows=[{'id':str(i),'label':('manual_review_required' if i<71 else 'owner_match'),'confidence':(.4 if i<71 else .75),'method':'GET','meta':{}} for i in range(200)]
    assert 'manual_review_above_35_percent' not in v5.summary(rows,{r['id']:r for r in rows})['stop_reasons']

def test_prompt_removes_old_confidence_conversion():
    text=v5.PROMPT.read_text(encoding='utf8')
    assert '0.5 이하는 반드시 manual_review_required' not in text
    assert '낮은 confidence를 이유로 label을 manual_review_required로 바꾸지 않는다' in text
    assert '0.75' in text and '0.6' in text and '0.4' in text
