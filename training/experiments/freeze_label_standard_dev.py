"""Write new decision artifacts only; refuse overwriting existing artifacts."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'reports/eval/classification_quality'


def main():
    source = OUT/'review_decisions.json'
    protected = [source, OUT/'label_decisions.md', ROOT/'AGENTS.md',
        ROOT/'datasets/blade/processed/test.jsonl',ROOT/'training/data/human_corrections_v5.jsonl']
    def hashes():
        return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    before = hashes()
    targets = [OUT/'label_decisions_dev_v1.jsonl', OUT/'label_decisions_dev_v1.md',OUT/'label_standard_dev_v1.manifest.json']
    assert not any(p.exists() for p in targets), 'New artifacts already exist; refusing overwrite'
    records = []
    for old in json.loads(source.read_text(encoding='utf8'))['decisions']:
        ident = old['id']
        confirmed = 'manual_review_required' if any(s in ident for s in ['microsoft.com','gerermesaffaires.com']) else None
        if 'zoom.us' in ident:
            status, candidate = 'needs_get_policy_evidence', None
            reason = 'GET 자체에 적용되는 역할 및 플랜 조건을 추가 확인해야 함'
        elif confirmed:
            status, candidate = 'confirmed_retained', confirmed
            reason = '사용자 승인: 기존 보류 유지'
        else:
            status, candidate = 'conditional_review', 'manual_review_required'
            reason = '사용자 승인: 협업 멤버십/ACL만으로 기존 라벨을 확정하지 않음. 다른 정책 근거가 없으면 보류. 추가 근거 확인은 미완료'
        records.append(dict(id=ident, previous_human_label=old['human_label'],
            standard_version='dev-v1',status=status, candidate_label=candidate,
            confirmed_label=confirmed,reason=reason,previous_diagnosis=old['diagnosis'],
            approval_scope='label standard and handling direction; not new source verification'))
    assert len(records)==9
    targets[0].write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf8')
    lines = ['# 개발용 라벨 결정 v1', '',
        '기존 파일 보존. 승인된 처리 방향과 최종 라벨 확정을 분리한다. 유지 확정 3건, 조건부 검수 5건, GET 근거 확인 1건.', '',
        '| id | 기존 사람 label | 상태 | 조건부 후보 | 확정 label | 사유 |','|---|---|---|---|---|---|']
    for r in records:
        lines.append('| '+' | '.join(str(r[k] or '').replace('|','\\|') for k in ['id','previous_human_label','status','candidate_label','confirmed_label','reason'])+' |')
    targets[1].write_text('\n'.join(lines)+'\n',encoding='utf8')
    assert before==hashes()
    targets[2].write_text(json.dumps(dict(preserved_sha256=before,
        standard_sha256=hashlib.sha256((ROOT/'training/data/LABEL_STANDARD_DEV_V1.md').read_bytes()).hexdigest(),
        records=9,confirmed=3,conditional=5,pending_get=1),ensure_ascii=False,indent=2),encoding='utf8')
    print('Created new artifacts: 9 records; 3 confirmed retained, 5 conditional, 1 pending. Existing hashes unchanged.')


if __name__=='__main__':
    main()
