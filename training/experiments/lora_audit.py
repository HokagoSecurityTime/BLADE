"""Inventory only: prepared data is not evidence that training occurred."""
from __future__ import annotations
import json, random, hashlib
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[2]

def run() -> None:
    p=ROOT/'datasets/blade/processed/train.jsonl'
    rows=[json.loads(s) for s in p.read_text(encoding='utf8').splitlines()]
    sample=random.Random(42).sample([r for r in rows if r['label']=='membership_required'],20)
    # Manual source review of the deterministic sample, not keyword auto-labeling.
    findings=[('불일치','Business/Enterprise 플랜'),('미확정','READ_CONVERSATIONS는 그룹 구성원 검사 아님'),
      ('불일치','subscription tier 명시'),('미확정','API 키·토큰만 명시'),('미확정','문서 read ACL, 그룹 관계 미명시'),
      ('미확정','인증·노드 ACL, 그룹 관계 미명시'),('일치','이미 해당 conversation 구성원인 사용자만 허용'),
      ('미확정','conference 조회 scope만 명시'),('미확정','조회 대상이 멤버 목록이지 요청자 구성원 요구가 아님'),
      ('미확정','조회 scope만 명시'),('미확정','teamId 필드만 있음'),('미확정','문서 변환 설명만 있음'),
      ('미확정','기능 permission, 그룹 관계 미명시'),('불일치','Pro 이상 유료 계정'),('미확정','메시지 검색 설명만 있음'),
      ('미확정','room 접근 ACL, 그룹 구성원 관계 미명시'),('미확정','CreateCall/ReadChannel 기능 권한'),
      ('미확정','your account는 그룹 구성원 검사 아님'),('불일치','합성 premium plan 조건'),('미확정','teamId 필드만 있음')]
    text='# A. LoRA 산출물·준비 데이터 점검\n\nLoRA 가중치/adapter_config/trainer_state를 찾지 못했다. Ollama에는 기본 qwen2.5:7b(Q4_K_M)만 있다. 아래는 학습 완료 데이터가 아니라 현재 준비된 train.jsonl 점검이다.\n\n'
    text+='- 실제 학습 베이스 모델·어댑터 경로·하이퍼파라미터·학습 프롬프트: 미확인(학습 산출물 없음).\n- 계획된 베이스: Qwen2.5-7B. 사용자 후속 지시로 신규 학습이 승인됐으나 아직 실행하지 않았다.\n'
    text+=f'- 준비 데이터: `{p.relative_to(ROOT)}`\n- SHA-256: `{hashlib.sha256(p.read_bytes()).hexdigest()}`\n- 준비 건수: {len(rows)}\n\n| label | 건수 |\n|---|---:|\n'
    for k,v in Counter(r['label'] for r in rows).items():text+=f'| {k} | {v} |\n'
    text+='\n## 라벨 의미\n\n484건은 policy-label-v2.5, 28건은 프롬프트 버전이 없는 합성 intended label이다. v2.5 membership은 구독·플랜·등급 기준이다. 실제 레코드에는 오라벨/불충분한 근거가 섞여 있어 전부 구독 정책이라고 단정하지 않는다.\n\nseed 42, membership 84건 중 20건 표본: v2.9 일치 1/20(5%), 명시적 의미 불일치 4/20(20%), 미확정 15/20(75%). 미확정을 불일치로 합산하지 않는다. v2.9 적합성이 확인되지 않은 비율은 19/20(95%)다. 실제 학습 샘플이 아닌 준비 데이터 표본이다.\n\n| id | path | v2.9 판정 | 근거 |\n|---|---|---|---|\n'
    audit=[]
    for r,(decision,reason) in zip(sample,findings):
        text+=f'| {r["id"]} | {r["path"]} | {decision} | {reason} |\n'
        audit.append(dict(id=r['id'],decision=decision,reason=reason,rationale=r.get('rationale'),description=r.get('enrichment',{}).get('operation',{}).get('description')))
    text+='\n## 입력 형식\n\n준비 데이터 512건 모두 OAS·ERD 필드가 있다. 원문 controller_text는 0/512(0%), 비어 있지 않은 controller_signals는 28/512(5.47%)다. 484/512(94.53%)에는 controller 신호도 없다. 따라서 정확히 OAS만이라고 부를 수 없고 OAS+ERD/설명 중심이다. 실제 학습용 chat template/tokenization 기록은 없으므로 학습 모델에 무엇을 보냈는지는 확인 불가다.\n\n## 신규 학습 환경\n\n현재 PyTorch 2.6.0+cpu, CUDA 빌드 없음, torch CUDA 장치 0개. nvidia-smi는 일반 실행과 권한 확대 실행 모두 접근 권한 오류. C: 여유 약 6.3GB. 이 조건에서는 Qwen 7B 원본 가중치와 CUDA 학습 환경을 내려받아 LoRA를 학습할 공간/장치를 확인하지 못했다. 기존 파일 삭제나 유료 원격 GPU 임대는 수행하지 않는다.\n'
    out=ROOT/'reports/eval';(out/'lora_audit.md').write_text(text,encoding='utf8')
    (out/'lora_membership_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
    print('A report written')

if __name__=='__main__':run()
