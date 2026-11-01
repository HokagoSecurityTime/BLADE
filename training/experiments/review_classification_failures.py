"""Build human decision sheet and paired model error audit, without inference."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'reports/eval/classification_quality'


def issue(ident):
    if any(x in ident for x in ['appcenter.ms','bitbucket.org','circuitsandbox.net']):
        return ('membership 의미', '구독 등급과 리소스 참여·멤버십을 같은 라벨로 볼지 결정',
                '현재 plan/tier 중심 정의와 사람의 협업 멤버십 해석을 먼저 일치시킬 것. 근거가 없는 멤버십은 자동 추론하지 않음')
    if 'microsoft.com' in ident or 'gerermesaffaires' in ident:
        return ('manual 허용 범위', '역할/프로젝트 단서는 있지만 정책을 특정할 수 없는 경우 보류를 허용할지 결정',
                '정책을 구분할 근거가 부족한 경우 보류 허용을 권고. 객체 ID 존재만으로 구체 라벨을 강제하지 않음')
    if 'zoom.us' in ident:
        return ('복수 정책 단일 라벨', '계정 관리자·계정 소유자·유료 플랜이 함께 있는 요청의 대표 라벨 결정',
                '계정 owner를 개인 객체 owner와 동일시하지 않음. 역할 제한이 핵심이라는 해석은 가능하나 사람 확정 필요')
    return ('ACL과 소유권', '편집 권한 보유자를 소유자라고 볼 수 있는지 재검수',
            'ACL write/edit 권한만으로 owner_match를 확정하지 않음. 역할 또는 리소스별 ACL 중 무엇인지 소스 근거 확인')


def main():
    diagnoses = json.loads((OUT/'diagnosis.json').read_text(encoding='utf8'))
    paired = [json.loads(s) for s in (OUT/'paired_results.jsonl').read_text(encoding='utf8').splitlines()]
    latest = {r['id']:r for r in paired if r['_condition']=='supplemented'}
    old = {r['id']:r for r in paired if r['_condition']=='original'}
    decision, errors = [], []
    for row in diagnoses:
        common = dict(**row, current_original=old[row['id']]['label'], current_supplemented=latest[row['id']]['label'],
                      current_rationale=latest[row['id']]['rationale'])
        if row['category'] in {'규칙·라벨 기준 충돌','사람 라벨 재확인'}:
            group,question,recommendation = issue(row['id'])
            decision.append(dict(**common, group=group, decision_question=question, recommendation=recommendation,
                                 confirmed_label='', decision_reason=''))
        elif row['category']=='모델 판단 오류':
            errors.append(common)
    assert len(decision)==9 and len(errors)==9
    def cell(v):
        return str(v).replace('|','\\|').replace('\n','<br>')
    lines = ['# 라벨 기준 결정 및 재검수', '',
        '자동 라벨 수정 없음. 아래 권고는 확정 라벨이 아니다. 모델 응답은 이번 보충 입력 측정 결과다.', '',
        '| id | 쟁점 | 기존 사람 라벨 | 최신 모델 라벨 | 결정할 질문 | 권고 | 확정 라벨 | 사유 |',
        '|---|---|---|---|---|---|---|---|']
    for r in decision:
        lines.append('| '+' | '.join(cell(r[k]) for k in ['id','group','human_label','current_supplemented','decision_question','recommendation','confirmed_label','decision_reason'])+' |')
    lines += ['', '## 검수 원칙', '',
        '- 서비스 이름만으로 접근 정책을 가정하지 않는다. 기존 사람 라벨도 검토 대상이며 모델의 불일치가 항상 모델 오류라는 뜻은 아니다.',
        '- 한 요청에 여러 조건이 있으면 실제 근거와 대표 라벨 선택 이유를 함께 기록한다. 모든 API에 일률적인 우선순위를 적용하지 않는다.',
        '- 기준이 확정되면 개발 예제와 라벨 지침에 반영하고, 기존에 분석하지 않은 사람 검수 표본에서 평가한다. 이번 31건은 진단용 회귀 표본이다.']
    (OUT/'label_decisions.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    lines = ['# 보충 입력 이후 모델 오판 추적', '',
        '기존 분석에서 모델 오판으로 분류한 9건을 최신 API 응답으로 대조했다. 이 범주 역시 분석 가설이며 새 정답 판정이 아니다.', '',
        '| id | 사람 라벨 | 기존 입력 응답 | 보충 입력 응답 | 최신 rationale | 이전 진단 |', '|---|---|---|---|---|---|']
    for r in errors:
        lines.append('| '+' | '.join(cell(r[k]) for k in ['id','human_label','current_original','current_supplemented','current_rationale','diagnosis'])+' |')
    counts = Counter(r['current_supplemented'] for r in errors)
    lines += ['', f'보충 입력 응답 분포: {dict(counts)}. 사람 라벨 일치 0/9.', '',
        '## 다음 비교 실험에 필요한 조건', '',
        '- OAuth/API key 요구를 role_required로 판정하는 오류: 인증과 역할 제한을 구분하는 명시 근거 검증이 필요하다.',
        '- 회사·조직·payor 단서를 membership_required로 판정하는 오류: 모델이 인용한 근거가 선택한 라벨 정의를 실제로 지지하는지 확인해야 한다.',
        '- 개인·조직 스코프 혼동 및 근거가 있어도 보류하는 사례: 필드 존재 검증만으로 잡을 수 없다.',
        '- 자동 사후 라벨 교체는 하지 않는다. 정답 라벨을 모델 입력에 주는 수정도 하지 않는다.',
        '- 먼저 label_decisions.md의 의미 충돌을 확정한 뒤, 고정 프롬프트·입력에서 다른 모델과 비교하거나 별도 승인된 프롬프트 실험을 설계한다. 현재 결과만으로 학습/전체 재라벨링을 재개하지 않는다.']
    (OUT/'model_error_followup.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    (OUT/'review_decisions.json').write_text(json.dumps(dict(decisions=decision,model_errors=errors),ensure_ascii=False,indent=2),encoding='utf8')
    print('Decision rows: 9; model error rows: 9; API calls: 0; labels modified: 0')


if __name__ == '__main__':
    main()
