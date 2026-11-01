"""Source-grounded agent review proposals; never overwrite human labels."""
import hashlib
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'reports/eval/classification_quality'
SOURCE = ROOT/'datasets/blade/raw/openapi-directory/APIs'
REASONS = {
 'appcenter.ms': ('근거 부족', 'Cancels a build와 API token만으로 개인 소유·역할·구독·조직 일치 조건을 판별할 수 없다. owner_name 경로는 계정/조직 이름일 수 있으며 소유권 비교의 증거가 아니다.'),
 'appwrite.io': ('리소스별 ACL', 'Only users with write permissions는 접근 권한 조건이다. 파일 소유자만 허용한다거나 특정 역할만 허용한다는 조건은 명시되지 않는다. Project 헤더도 조직 일치 검사 증거가 아니다.'),
 'bitbucket.org': ('근거 부족', 'annotation 생성/수정 설명과 workspace/repository 경로가 있으나 이 요청의 접근 허용 조건은 명세에 특정되지 않는다. 협업 멤버십·tenant 일치·개인 소유를 경로만으로 확정하지 않는다. security 미선언도 public 근거가 아니다.'),
 'circuitsandbox.net': ('사용자 범위와 소유권 구별 필요', 'WRITE_CONVERSATIONS 설명은 authenticated user의 conversations를 명시한다. 그러나 사용자의 대화는 참여한 대화일 수도 있어 생성자/소유자 일치로 단정할 수 없다. MANAGE_CONVERSATIONS는 기능 권한이며 특정 관리자 역할 또는 구독 등급 조건은 아니다.'),
 'shutterstock.com': ('리소스별 편집 권한', 'collections.edit는 collection 수정 권한을 부여하지만 요청자가 소유자여야 한다는 조건은 없다. 편집 가능 사용자와 소유자는 동일하지 않으므로 owner_match로 확정하지 않는다.'),
 'zoom.us': ('독립 복수 조건', '해당 GET 설명 자체에 account:read:admin scope와 Pro 이상 유료 계정 prerequisite가 모두 명시된다. 개발 기준 v1의 독립 필수 조건 규칙에 따라 role_required 또는 membership_required 하나로 축약하지 않고 보류를 제안한다. 계정 owner의 설정 변경 설명은 GET의 개인 소유권 근거로 사용하지 않는다.'),
}


def main():
    previous = OUT/'label_decisions_dev_v1.jsonl'
    pending = {r['id']:r for r in map(json.loads,previous.read_text(encoding='utf8').splitlines()) if r['confirmed_label'] is None}
    dataset = ROOT/'datasets/blade/processed/apisguru_enriched_v2.jsonl'
    protected = [previous, dataset, ROOT/'datasets/blade/processed/test.jsonl', ROOT/'training/data/human_corrections_v5.jsonl']
    def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
    before = {str(p.relative_to(ROOT)):digest(p) for p in protected}
    results = []
    for row in map(json.loads,dataset.read_text(encoding='utf8').splitlines()):
        if row['id'] not in pending: continue
        path = SOURCE/row['enrichment']['source_file']
        assert digest(path)==row['enrichment']['source_sha256']
        text = path.read_text(encoding='utf8')
        spec = yaml.safe_load(text)
        path_item = spec['paths'][row['path']]
        op = path_item[row['method'].lower()]
        pointer = '/paths/'+row['path'].replace('~','~0').replace('/','~1')+'/'+row['method'].lower()
        category, reason = REASONS[row['service']]
        results.append(dict(id=row['id'],previous_human_label=pending[row['id']]['previous_human_label'],
            proposed_label='manual_review_required',confirmed_label=None,status='agent_review_pending_human_confirmation',
            reviewer='agent_source_review',standard='dev-v1',category=category,reason=reason,
            source_file=path.relative_to(ROOT).as_posix(),source_sha256=digest(path),operation_pointer=pointer,
            operation=op,path_parameters=path_item.get('parameters',[]),
            security=op.get('security',spec.get('security')),security_schemes=spec.get('components',{}).get('securitySchemes',spec.get('securityDefinitions',{}))))
    assert len(results)==6
    json_path=OUT/'remaining_label_review_dev_v1.json'
    md_path=OUT/'remaining_label_review_dev_v1.md'
    assert not json_path.exists() and not md_path.exists(), 'Preserve prior review output'
    json_path.write_text(json.dumps(dict(records=results,preserved_sha256=before),ensure_ascii=False,indent=2),encoding='utf8')
    lines=['# 남은 6건 원본 명세 검수', '',
        '원본 로컬 OAS의 해당 operation과 security 정의를 확인했다. 6건 모두 저장된 추출 원본 해시와 일치한다. 최신 온라인 동작이나 서버 구현을 검증한 것은 아니다.', '',
        '개발 기준 v1에 따른 에이전트 권고는 모두 manual_review_required이다. 사람이 확정한 새 정답이 아니며 confirmed_label은 비워 둔다. 이전 3건 보류 유지 확정과 이번 6건 권고는 구분한다.', '',
        '| id | 기존 사람 label | 제안 label | 판단 근거 | 확정 label |', '|---|---|---|---|---|']
    for r in results:
        lines.append('| '+' | '.join(str(r[k]).replace('|','\\|').replace('\n',' ') for k in ['id','previous_human_label','proposed_label','reason'])+' | |')
    for r in results:
        lines += ['', '## '+r['id'], '', '원본: `'+r['source_file']+'`', '',
            'operation JSON pointer: `'+r['operation_pointer']+'`', '',
            '해당 요청 설명:', '', r['operation'].get('description','설명 없음'), '', '판단: '+r['reason']]
    lines += ['', '## 평가 시 주의', '',
        '이 6건은 충돌 사례를 의도적으로 모은 표본이다. 전부 보류라는 결과를 전체 데이터의 보류 정책으로 일반화하지 않는다. 변경된 기준으로 정답을 재정의해 생긴 점수 상승을 모델 성능 향상이라고 보고하지 않는다.',
        'API 호출·학습·기존 라벨 수정은 수행하지 않았다. 원본 전체 operation과 보안 정의는 JSON 산출물에 보존했다.']
    md_path.write_text('\n'.join(lines)+'\n',encoding='utf8')
    assert before=={str(p.relative_to(ROOT)):digest(p) for p in protected}
    print('6 source reviews; 6 verified hashes; proposals only; previous files unchanged')


if __name__=='__main__': main()
