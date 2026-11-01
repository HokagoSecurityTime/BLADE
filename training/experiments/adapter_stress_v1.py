"""No-API adversarial parser experiment, not external holdout performance."""
from __future__ import annotations
import hashlib
import itertools
import json
from types import SimpleNamespace
from training.experiments import external_binding_adapter as adapter

OUT=adapter.ROOT/'reports/eval/classification_quality/adapter_stress_v1'


def run() -> None:
    from markdown_it import MarkdownIt
    source_path=adapter.Path(adapter.__file__)
    frozen=adapter.digest(source_path)
    cases={
        'owner_or_admin': 'if not current_user.is_superuser and item.owner_id != current_user.id:\n    raise Denied(status_code=403)',
        'owner_and_admin': 'if not current_user.is_superuser or item.owner_id != current_user.id:\n    raise Denied(status_code=403)',
        'owner_not_admin': 'if current_user.is_superuser or item.owner_id != current_user.id:\n    raise Denied(status_code=403)',
        'admin_early_return': 'if current_user.is_superuser:\n    return item\nif item.owner_id != current_user.id:\n    raise Denied(status_code=403)',
        'masked_404': 'if item.owner_id != current_user.id:\n    raise Denied(status_code=404)',
        'helper_guard': 'require_owner(current_user, item)',
        'assert_guard': 'assert item.owner_id == current_user.id',
        'unknown_tenant': 'if item.tenant_id != current_user.tenant_id:\n    raise Denied(status_code=403)',
        'alias_owner': 'caller = current_user\nif item.owner_id != caller.id:\n    raise Denied(status_code=403)',
        'nested_guard': 'if not current_user.is_superuser:\n    if item.owner_id != current_user.id:\n        raise Denied(status_code=403)',
    }
    sources={name:'def access(current_user, item):\n'+''.join('    '+line+'\n' for line in body.splitlines())+'    return item\n' for name,body in cases.items()}
    OUT.mkdir(exist_ok=True)
    protocol=dict(adapter_sha256=frozen,cases=sources,scope='synthetic mutation development; no external repository changes',api_calls=0)
    protocol_path=OUT/'protocol.json'
    if protocol_path.exists():assert json.loads(protocol_path.read_text(encoding='utf8'))==protocol
    else:protocol_path.write_text(json.dumps(protocol,indent=2),encoding='utf8')
    class Denied(Exception):
        def __init__(self,status_code: int):self.status_code=status_code
    def require_owner(user: object,item: object) -> None:
        if item.owner_id != user.id:raise Denied(403)
    results=[]
    for name,source in sources.items():
        namespace=dict(Denied=Denied,require_owner=require_owner)
        exec(compile(source,name,'exec'),namespace)
        try:formula=adapter.symbolic(source,'item');error=None
        except ValueError as exc:formula=None;error=str(exc)
        states=[]
        for owner,admin,tenant in itertools.product([False,True],repeat=3):
            user=SimpleNamespace(id='u',is_superuser=admin,tenant_id='t')
            item=SimpleNamespace(owner_id='u' if owner else 'other',tenant_id='t' if tenant else 'other')
            try:namespace['access'](user,item);actual=True
            except (Denied,AssertionError):actual=False
            predicted=adapter.boolean(formula,dict(owner=owner,admin=admin)) if formula else None
            states.append(dict(owner=owner,admin=admin,tenant=tenant,actual=actual,extracted=predicted))
        mismatch=[s for s in states if s['extracted'] is not None and s['actual']!=s['extracted']]
        results.append(dict(id=name,status='unsupported' if formula is None else 'incorrect' if mismatch else 'equivalent',formula=formula,error=error,states=states,counterexamples=mismatch))
    counts={k:sum(r['status']==k for r in results) for k in ['equivalent','incorrect','unsupported']}
    assert adapter.digest(source_path)==frozen
    (OUT/'results.json').write_text(json.dumps(dict(counts=counts,results=results),indent=2),encoding='utf8')
    text='# 외부 어댑터 v1 조건 보존 스트레스 실험\n\n'
    text+='기존 어댑터를 수정하지 않고 합성 변형 10개 × 상태 8개를 실행했다. 실제 Python 함수의 허용/거부와 추출 조건을 비교했다. 새로운 외부 프로젝트 성능 평가가 아니라 파서 확장 위험을 확인하는 개발 실험이다.\n\n'
    text+=f'조건 일치 {counts["equivalent"]}개, 잘못 추출 {counts["incorrect"]}개, 미지원 거부 {counts["unsupported"]}개. API 호출 0회.\n\n| 사례 | 결과 | 추출 조건 |\n|---|---|---|\n'
    for r in results:text+=f'| {r["id"]} | {r["status"]} | `{r["formula"] or r["error"]}` |\n'
    text+='\n## 발견 사항\n\n권한 거부를 404로 숨기는 검사, 별도 helper 호출, assert 검사는 현재 파서가 누락한다. 따라서 알 수 없는 코드에 이 파서를 직접 적용해서는 안 된다. 기존 전체 실행은 원본 해시와 검토한 핸들러 목록으로 제한되므로 이번 변형을 운영에서 처리했다는 뜻은 아니다. extract() 단독 호출에는 자체 해시 검사가 없다는 점도 호출 경계의 약점이다.\n\n## 다음 조치\n\n외부 프로젝트 확대보다 먼저 별도 v2 어댑터에서 미지원 문장·호출을 보류하고, 404를 객체 부재 검사로만 인정하며, 호출 진입점마다 소스 무결성을 확인해야 한다. 이번 v1 결과와 해시는 보존했다. 모델 라벨·기존 test·런타임은 변경하지 않았다. 자동 적용은 계속 금지 상태다.\n'
    (OUT/'report.md').write_text(text,encoding='utf8')
    (OUT/'report.htm').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>어댑터 스트레스 실험</title><style>body{max-width:1100px;margin:40px auto;font:16px/1.7 system-ui}td,th{border:1px solid #bbb;padding:8px}table{border-collapse:collapse}</style>'+MarkdownIt().enable('table').render(text)+'</html>',encoding='utf8')
    print(counts)


if __name__=='__main__':run()
