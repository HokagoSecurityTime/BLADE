"""In-memory contract experiment, not production enforcement or model training."""
import json
from pathlib import Path


def apply(mode, subject, records, *, object_id=None, body=None, adapter=False):
    # subject and adapter are trusted deployment inputs, never client assertions.
    if not isinstance(subject, str) or not subject:
        return {'status': 'deny'}
    if mode == 'object_lookup':
        item = records.get(object_id)
        return {'status': 'allow' if item and item.get('principal') == subject else 'deny'}
    if not adapter:
        return {'status': 'unsupported'}
    if mode == 'subject_resource':
        item = records.get(subject)
        return {'status': 'allow' if item and item.get('principal') == subject else 'deny'}
    if mode == 'create_owner':
        body = dict(body or {})
        if 'principal' in body and body['principal'] != subject:
            return {'status': 'deny'}
        return {'status': 'allow', 'write': {**body, 'principal': subject}}
    if mode == 'owner_collection':
        return {'status': 'allow', 'result': [dict(v) for v in records.values() if v.get('principal') == subject]}
    return {'status': 'unsupported'}


def main():
    records = {'alice': {'principal': 'alice'}, 'bob': {'principal': 'bob'}, 'missing': {}}
    cases = []
    def check(name, mode, expected, subject='alice', **kwargs):
        result = apply(mode, subject, records, **kwargs)
        assert result['status'] == expected, name
        if mode == 'create_owner' and expected == 'allow':
            assert result['write']['principal'] == subject
        if mode == 'owner_collection' and expected == 'allow':
            assert result['result'] == [{'principal': 'alice'}]
        cases.append(dict(name=name, mode=mode, expected=expected, actual=result))
    check('owned object', 'object_lookup', 'allow', object_id='alice')
    check('other object', 'object_lookup', 'deny', object_id='bob')
    check('missing id', 'object_lookup', 'deny')
    check('missing owner', 'object_lookup', 'deny', object_id='missing')
    check('own subject resource', 'subject_resource', 'allow', adapter=True)
    check('missing subject resource', 'subject_resource', 'deny', subject='absent', adapter=True)
    check('create assigns owner', 'create_owner', 'allow', body={'title':'draft'}, adapter=True)
    check('create matching owner', 'create_owner', 'allow', body={'principal':'alice'}, adapter=True)
    check('create forged owner', 'create_owner', 'deny', body={'principal':'bob'}, adapter=True)
    check('create null owner', 'create_owner', 'deny', body={'principal':None}, adapter=True)
    check('collection excludes other/missing owner', 'owner_collection', 'allow', adapter=True)
    for mode in ['object_lookup','subject_resource','create_owner','owner_collection']:
        check(mode+' unauthenticated', mode, 'deny', subject=None, adapter=True)
    for mode in ['subject_resource','create_owner','owner_collection']:
        check(mode+' no backend adapter', mode, 'unsupported')
    out = Path(__file__).resolve().parents[2]/'reports/eval'
    (out/'ownership_modes_experiment.json').write_text(json.dumps(dict(api_calls=0,cases=cases),indent=2),encoding='utf-8')
    lines = ['# 소유권 처리 방식 개발 실험', '',
        f'독립 개발 예제 {len(cases)}건 통과. API 호출·학습 없음. 고정 test 성능 실험이 아니다.', '',
        '| 처리 방식 | 검증한 계약 | 제품 적용에 필요한 기능 |', '|---|---|---|',
        '| object_lookup | 요청 ID로 조회 후 소유자 비교 | 신뢰 가능한 DB 조회·실행 시점 일관성 |',
        '| subject_resource | 검증된 주체로 자기 리소스 선택 | 백엔드의 주체 기반 조회를 보장하는 어댑터 |',
        '| create_owner | 타인 소유자 지정 거부·주체로 소유자 확정 | 저장 트랜잭션까지 소유자 연결 보장 |',
        '| owner_collection | 주체 소유 데이터만 반환 | DB 쿼리 제한·페이지네이션/집계 누출 방지 |', '',
        '새 방식은 백엔드 어댑터가 없으면 unsupported이다. JWT 존재만으로 허용하거나 lookup에 가짜 ID를 넣지 않는다.', '',
        '| 예제 | 기대 | 결과 |', '|---|---|---|']
    lines += [f"| {r['name']} | {r['expected']} | {r['actual']['status']} |" for r in cases]
    lines += ['', '## 해석', '',
        '- 의미 라벨 owner_match와 집행 방식을 분리하면 ID 없는 요청의 요구사항을 표현할 수 있다. 라벨은 기존 7종을 유지한다.',
        '- 메모리 객체로 계약을 검증했을 뿐 실제 HTTP/JWT/DB/동시성/중첩 body/응답 스트리밍은 구현하지 않았다. 제품 보안이나 성능 향상을 입증한 결과가 아니다.',
        '- 고정 test의 18건을 자동으로 새 방식에 배정하거나 보류를 해제하지 않았다. 실제 데이터 흐름 검증이 필요하다.',
        '- 다음 구현은 별도 개발 서비스 및 실제 백엔드 어댑터 통합 검증이다. 현재 런타임 변경 금지 규약 때문에 제품 코드는 수정하지 않았다.']
    (out/'ownership_modes_experiment.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'{len(cases)} scenarios passed; external API calls: 0')


if __name__ == '__main__':
    main()
