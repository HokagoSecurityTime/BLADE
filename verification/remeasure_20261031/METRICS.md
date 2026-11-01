# 발표용 측정 결과

**실행 방식:** 기존 `scripts/attack_sim.py`를 수정 없이 정상/공격 각각 20회 실행했다. 종료 코드 0이며 수동 curl 대체는 사용하지 않았다.

## 표1. Label별 탐지 결과

| Label | 요청 수 | TP | FP | TN | FN | 탐지율 | 오탐율 |
|---|---:|---:|---:|---:|---:|---:|---:|
| public | 40 | 0 | 0 | 40 | 0 | 해당 없음 | 0.00% |
| role_required | 40 | 20 | 0 | 20 | 0 | 100.00% | 0.00% |
| membership_required | 40 | 20 | 0 | 20 | 0 | 100.00% | 0.00% |
| tenant_match | 40 | 20 | 0 | 20 | 0 | 100.00% | 0.00% |
| owner_match | 40 | 20 | 0 | 20 | 0 | 100.00% | 0.00% |
| owner_or_admin | 40 | 20 | 0 | 20 | 0 | 100.00% | 0.00% |
| manual_review_required | 40 | 0 | 0 | 20 | 20 | 0.00% | 0.00% |
| **전체** | **280** | **100** | **0** | **160** | **20** | **83.33%** | **0.00%** |

각 label은 정상 20회 + 공격 형태 요청 20회다. public은 인가 제한이 없어 공격 형태 요청도 TN으로 집계한다. manual_review_required의 타인 조회는 공격 정답이지만 OBSERVE로 통과하므로 FN이다. 분모가 0인 탐지율은 0%가 아닌 해당 없음으로 표기했다.

## 표2. 전체 지표와 지연 비교

| 지표 | 측정값 |
|---|---:|
| 전체 탐지율 TP/(TP+FN) | 83.33% |
| 전체 오탐율 FP/(FP+TN) | 0.00% |
| 프록시 요청 수 | 280 |
| 프록시 HTTP/연결 오류 | 0 |
| 프록시 p50 | 4.079 ms |
| 프록시 p95 | 6.659 ms |
| 백엔드 직접 요청 수 | 280 |
| 백엔드 직접 비-200/연결 오류 | 0 |
| 백엔드 직접 p50 | 3.082 ms |
| 백엔드 직접 p95 | 4.014 ms |

**프록시 추가 지연 p95 +2.644 ms**

같은 PC의 현재 로컬 서비스에서 순차 GET 요청으로 측정했다. 프록시 280회 후 동일한 label/정상·공격/경로/호출자/횟수 구성으로 백엔드에 280회를 직접 보냈다. 각 실험은 별도 HTTP 클라이언트의 연결을 재사용했고, 별도 워밍업은 하지 않았다. p50/p95는 nearest-rank 방식이다. 토큰 생성·정책 갱신 대기·탐지 로그 확인 시간은 요청 지연에서 제외했다.

**해석 제한:** 위 추가 지연은 두 표본의 p95 차이다. 프록시는 공격을 403으로 단축 처리하지만 직접 호출은 백엔드까지 실행되므로, 같은 업무를 모두 수행한 요청에 대한 순수 프록시 처리 비용이나 동시 부하 성능을 뜻하지 않는다.

## 표3. LLM 분류 정답률

| Method | 경로 | 실제 생성 label (step1) | 데모 의도 label | 정답 |
|---|---|---|---|---|
| GET | /admin/reports | role_required | role_required | O |
| DELETE | /orders/{orderId} | owner_match | owner_match | O |
| GET | /orders/{orderId} | owner_match | owner_match | O |
| GET | /orgs/{orgId}/docs | tenant_match | tenant_match | O |
| GET | /premium/content | membership_required | membership_required | O |
| GET | /public/health | public | public | O |
| GET | /users/{userId} | manual_review_required | owner_or_admin | X |

**LLM 분류 정답률 6/7 (85.71%)**

분류 비교는 `step1_policies.md`의 실제 생성 라벨과 `demo_backend/main.py`에 명시된 Intended policy를 사용했다. 수동 검토 탈출은 정답으로 계산하지 않았다.

**분류 정확도와 런타임 평가를 구분:** 7종 label 평가를 위해 기존 시뮬레이터의 `--prepare-demo`가 사용자 조회 정책을 owner_or_admin / manual_review_required로 일시 변경한다. 이는 생성된 정책을 그대로 사용한 종단 간 탐지율이 아니라 7종 평가 동작 시험이다. 종료 후 원본 정책을 복원했으며 분류 정확도 표에는 변경 전 step1의 결과만 사용했다.

## 재현과 증거

```bash
python scripts/attack_sim.py --prepare-demo -n 20 --proxy http://127.0.0.1:8080 --admin http://127.0.0.1:8100 --output verification/metrics-proxy.json
```

환경변수 BLADE_JWT_SECRET, BLADE_POLICY_POLL_SEC는 실행 중 서비스와 동일하게 설정해야 한다.

- 측정 시각(UTC): 2026-10-30T17:01:13.679100+00:00
- 기존 스크립트 해시 동일: True; 원본 정책 복원 확인: True
- [시뮬레이터 출력](metrics-attack-sim.log) · [프록시 요청별 결과](metrics-proxy.json) · [백엔드 직접 요청별 결과](metrics-direct.json)
- [실행 정보·분류 비교 근거](metrics-details.json) · [측정 전 정책](metrics-policies-before.json)
- 기존 JWT 시크릿 길이 경고는 발생했으며 수정하지 않았다.
