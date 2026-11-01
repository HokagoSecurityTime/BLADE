"""Generate separate API predictions for blind human review; no accuracy claims."""
import asyncio
from collections import Counter
import json
import os
from pathlib import Path
import httpx
from training.data.label import read_env
from training.data.label_v6 import engine

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/eval/classification_quality/fresh_review_v1'
OUT=ROOT/'reports/eval/classification_quality/fresh_review_v27'


async def main():
    read_env(ROOT/'.env')
    model=os.getenv('BLADE_LABEL_MODEL','gpt-4o-mini')
    assert os.getenv('BLADE_LABEL_PROVIDER','openai')=='openai' and model in {'gpt-4o-mini','gpt-4o-mini-2024-07-18'}
    settings=engine.llm.Settings('openai',model,os.environ['OPENAI_API_KEY'])
    packets=engine.read(BASE/'blind_inputs.jsonl')
    assert len(packets)==len({r['id'] for r in packets})==100
    byid={r['id']:r for r in packets}
    prompt=ROOT/'training/data/prompts/policy_label_v2.7.md'
    system=prompt.read_text(encoding='utf8')
    OUT.mkdir(exist_ok=True)
    review=OUT/'review_100_v27.md'
    if not review.exists():
        old=(BASE/'review_100.md').read_text(encoding='utf8')
        review.write_text(old.replace('training/data/LABEL_STANDARD_DEV_V1.md','training/data/LABEL_STANDARD_V2.7.md').replace('# 새 개발 검수표 100건','# v2.7 사람 검수표 100건'),encoding='utf8')
    def payload(row):
        value=dict(byid[row['id']]['input'])
        details=value.pop('security_details',None)
        if details:
            value['description']+='\n\nSource OAS security definitions (not operation description):\n'+json.dumps(details,ensure_ascii=False)
        return value
    engine.payload=payload
    engine.VERSION='policy-label-v2.7'
    manifest=dict(ids=list(byid),model=model,prompt_sha256=engine.digest(prompt),
        input_sha256=engine.digest(BASE/'blind_inputs.jsonl'),implementation_sha256=engine.digest(Path(__file__)),
        standard_sha256=engine.digest(ROOT/'training/data/LABEL_STANDARD_V2.7.md'),temperature=0,human_labels_available=False)
    stamp=OUT/'predictions.manifest.json'
    if stamp.exists():assert json.loads(stamp.read_text(encoding='utf8'))==manifest
    else:engine.dump(stamp,manifest)
    path=OUT/'model_predictions.jsonl'
    results=engine.read(path);done={r['id'] for r in results}
    assert len(done)==len(results) and done<=set(byid)
    semaphore=asyncio.Semaphore(4)
    async with httpx.AsyncClient(timeout=180) as client:
        async def one(packet):
            async with semaphore:
                row=dict(id=packet['id'],service=packet['service'],method=packet['input']['method'],path=packet['input']['path'],meta={})
                return await engine.request(row,system,settings,client,OUT/'usage.jsonl')
        tasks=[asyncio.create_task(one(p)) for p in packets if p['id'] not in done]
        try:
            for task in asyncio.as_completed(tasks):
                r=await task;engine.append(path,r);results.append(r)
                print(f'{len(results)}/100',flush=True)
        finally:
            for task in tasks:
                if not task.done():task.cancel()
            await asyncio.gather(*tasks,return_exceptions=True)
    good=[r for r in results if not r['meta'].get('label_error')]
    labels=Counter(r['label'] for r in good)
    report=dict(records=len(results),labels=dict(labels),label_errors=len(results)-len(good),
        evidence_invalid=sum(bool(r['meta'].get('evidence_invalid')) for r in good),
        manual_count=labels['manual_review_required'],accuracy=None,human_review_pending=True)
    engine.dump(OUT/'summary.json',report)
    lines=['# v2.7 100건 예측 실행 결과','','사람 검수 전이므로 정확도·F1은 미측정이다. 모델 예측은 검수표와 분리해 저장했다.','','| label | 건수 |','|---|---:|']
    lines += [f'| {label} | {labels[label]} |' for label in engine.LABELS]
    lines += ['',f"오류 {report['label_errors']}건; evidence_invalid {report['evidence_invalid']}건.",'','입력 ID와 사람 검수 근거는 기존 100건과 동일하다. security_details는 허용 근거 필드인 description에 출처를 표시해 전달했다. 기존 라벨·고정 test·런타임·학습 데이터는 수정하지 않았다.']
    (OUT/'run_report.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps(report))


if __name__=='__main__':asyncio.run(main())
