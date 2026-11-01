"""Probe only local synthetic containers and save framework-generated schemas."""
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SERVICES = ['quill_blog','orbit_tickets','folio_wiki','copper_wallet','campus_records','beacon_iot']

def get(url, token=None):
    request=urllib.request.Request(url,headers={'Authorization':'Bearer '+token} if token else {})
    try:
        with urllib.request.urlopen(request,timeout=5) as response:
            return response.status,response.read()
    except urllib.error.HTTPError as error:
        return error.code,error.read()

def main():
    rows=[json.loads(line) for line in (ROOT/'verification/synthetic_review_records.jsonl').read_text(encoding='utf-8').splitlines()]
    report={'services':{},'checks':0,'failures':[]}
    for index,name in enumerate(SERVICES):
        base=f'http://127.0.0.1:{18080+index}'
        schema_url=base+('/v3/api-docs' if name=='campus_records' else '/openapi.json')
        for attempt in range(30):
            try:
                status,body=get(schema_url)
                if status==200: break
            except (OSError,TimeoutError): pass
            time.sleep(1)
        else: raise RuntimeError(f'{name} not ready')
        schema=yaml.safe_load(body)
        (ROOT/f'datasets/blade/raw/synthetic/{name}/openapi.json').write_text(json.dumps(schema,indent=2),encoding='utf-8')
        selected=[row for row in rows if row['service']==name]
        for row in selected:
            row['oas_snippet'] = json.dumps({'openapi':schema['openapi'], 'paths':{row['path']:schema['paths'][row['path']]}},ensure_ascii=False)
        missing=[r['path'] for r in selected if r['path'] not in schema['paths']]
        assert not missing,(name,missing)
        for row in selected:
            path=row['path'].replace('{item_id}','1')
            for token in (None,'alice','bob','admin'):
                label=row['proposed_label']
                expected=200
                if label!='public':
                    if token is None: expected=401
                    elif not row['vulnerable']:
                        if label=='manual_review_required': expected=403
                        elif label=='owner_match' and token!='alice': expected=403
                        elif label=='owner_or_admin' and token=='bob': expected=403
                        elif label=='tenant_match' and token=='bob': expected=403
                        elif label=='role_required' and token!='admin': expected=403
                        elif label=='membership_required' and token=='bob': expected=403
                actual,_=get(base+path,token)
                report['checks']+=1
                if actual!=expected: report['failures'].append({'id':row['id'],'token':token,'actual':actual,'expected':expected})
        report['services'][name]={'endpoints':len(selected),'schema_paths':len(schema['paths']),'framework_export':True}
    (ROOT/'verification/synthetic_smoke_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (ROOT/'verification/synthetic_review_records.jsonl').write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows),encoding='utf-8')
    generation_path=ROOT/'verification/synthetic_generation_report.json'
    generation=json.loads(generation_path.read_text(encoding='utf-8'))
    generation['runtime_validation']={'docker_builds':6,'framework_exports':6,'http_checks':report['checks'],'failures':len(report['failures'])}
    generation['known_biases']=['All endpoints are GET handlers.', 'Six domains share the same seven authorization templates.', 'Fixed in-memory objects and fixture bearer tokens; not production authentication.', 'DDL is generated from the shared dataclass model, not native ORM migration tooling.']
    generation_path.write_text(json.dumps(generation,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    assert not report['failures']

if __name__=='__main__': main()
