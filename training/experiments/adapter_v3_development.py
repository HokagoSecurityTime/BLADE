from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from training.experiments import external_binding_adapter as old
from training.experiments import external_orm_adapter as orm
from training.experiments import adapter_v3 as new

OUT=old.ROOT/'reports/eval/classification_quality/adapter_v3_development'
GROUPS={
 'collection_semantics':['items.read_items'],
 'creation_semantics':['items.create_item'],
 'authentication_entry':['login.login_access_token','login.recover_password','users.register_user'],
 'capability_semantics':['login.reset_password'],
 'deployment_scope':['private.create_user'],
 'shared_role_dependency':['login.recover_password_html_content','users.read_users','users.create_user','users.update_user','utils.test_email'],
 'self_binding_and_validation':['users.update_user_me','users.update_password_me'],
 'anonymous_health':['utils.health_check']}


def run() -> None:
    from markdown_it import MarkdownIt
    old.check_snapshot()
    hashes={r['path']:r['sha256'] for r in json.loads((old.INPUT/'sources.json').read_text(encoding='utf8'))['files']}
    rows=json.loads((old.INPUT/'inputs.json').read_text(encoding='utf8'))
    records=[]
    for row in rows:
        module,name=row['id'].split('.')
        partial=new.analyze(old.RAW,f'backend/app/api/routes/{module}.py',name,hashes)
        legacy=orm.extract(row['id'])
        records.append(dict(id=row['id'],complete=legacy,partial=partial))
    categories=[dict(id=ident,category=group,analysis_gap=group in ['shared_role_dependency','self_binding_and_validation','anonymous_health','authentication_entry'],
                     label_semantics_gap=group in ['collection_semantics','creation_semantics','capability_semantics'],scope_gap=group=='deployment_scope') for group,ids in GROUPS.items() for ident in ids]
    assert len(categories)==15
    OUT.mkdir(exist_ok=True)
    for name,value in [('evidence',records),('unsupported_categories',categories)]:
        (OUT/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
    text='# 어댑터 v3 개발 결과\n\n전체 의미 분석 8/23건을 유지하고, 공통 역할 의존성의 필수 조건만 추가로 5건 추출했다. 부분 조건을 전체 검증 성공으로 세지 않는다. 나머지 10건은 의미·호출 연결·배포 범위가 미확정이다.\n\n| 미지원 분류 | 건수 |\n|---|---:|\n'
    for k,v in GROUPS.items():text+=f'| {k} | {len(v)} |\n'
    text+='\n엔드포인트 이름을 추가하지 않고 Depends import→함수→역할 거부 조건 구조를 분석한다. ORM where 및 반환 인자도 위치와 함께 추출하지만, 라이브러리·인증 바인딩이 검증되지 않으면 후보 근거로만 남긴다. 목록 행 필터링·생성자 바인딩·reset token을 억지로 6종에 매핑하지 않는다.\n\n새 프로젝트 평가 전에 adapter_v3.py와 기존 완전 분석 경로·프롬프트 해시를 고정한다. 기존 프로젝트는 개발셋이다.\n'
    (OUT/'report.md').write_text(text,encoding='utf8')
    (OUT/'report.htm').write_text('<!doctype html><html lang="ko"><meta charset="utf-8">'+MarkdownIt().enable('table').render(text)+'</html>',encoding='utf8')
    print(Counter(r['partial']['status'] for r in records))

if __name__=='__main__':run()
