# 프록시 집행 성능 재측정 — 2026-10-31 (현재 코드 기준)

Phase 1 측정(2026-09-13)과 같은 스크립트·같은 인자로 다시 측정했다. 코드·데이터는 수정하지 않았다. 기존 증거는 `verification/phase1_20260913/`(SHA256SUMS 포함)에 복사해 두었고, 이번 결과가 `verification/METRICS.md`, `metrics-*.json`, `metrics-attack-sim.log`를 덮어썼다.

## 측정 조건

| 항목 | Phase 1 (2026-09-13 12:40 UTC) | 재측정 (2026-10-30 17:01 UTC = 10-31 02:01 KST) |
|---|---|---|
| 커밋 | 없음(저장소는 2026-10-21 스냅샷으로 시작) | `51dff137` (feat/lora-pipeline) |
| 스크립트 | scripts/attack_sim.py `e84571c7…`, measure_presentation.py | 동일 파일, 동일 해시(실행 전후 변경 없음 확인) |
| 실행 인자 | `-n 20 --prepare-demo --proxy 127.0.0.1:8080 --admin 127.0.0.1:8100` | 동일 |
| 서비스 실행 방식 | 로컬 백그라운드 프로세스(verification/SUMMARY.md: Docker 컨테이너는 중지) | Docker Compose 컨테이너(8080·8100·9000을 com.docker.backend가 수신) |
| BLADE_PHASE2_ENABLED | 해당 없음(Phase 2 코드 이전) | 관리 API `/features` 응답 `phase2=false`(mode·observability·alerts·explain·rag·reanalysis 모두 false). compose 기본값 false, .env에 설정 없음. 프록시 컨테이너 환경변수 직접 조회는 docker CLI 무응답으로 **미확인** |
| 컨테이너 이미지 빌드 시점 | 해당 없음 | **미확인**(docker CLI 무응답). 현재 코드가 이미지에 반영됐는지는 확인하지 못함 |
| 정책 | 7건 ACTIVE | 측정 전 public만 ACTIVE·6건 PENDING → 6건 approve → 측정 → 6건 rollback(PENDING) 복원 확인. `--prepare-demo`의 users 정책 임시 변경도 복원됨(policies_restored=true) |
| 오류 | 프록시·직접 모두 0 | 프록시·직접 모두 0 |

## 탐지 결과 비교 (label별 정상 20·공격 20)

| label | Phase 1 TP/FP/FN | 재측정 TP/FP/FN | 탐지율 | 오탐율 |
|---|---:|---:|---:|---:|
| public | -/0/- | -/0/- | 해당 없음 | 0% → 0% |
| role_required | 20/0/0 | 20/0/0 | 100% → 100% | 0% → 0% |
| membership_required | 20/0/0 | 20/0/0 | 100% → 100% | 0% → 0% |
| tenant_match | 20/0/0 | 20/0/0 | 100% → 100% | 0% → 0% |
| owner_match | 20/0/0 | 20/0/0 | 100% → 100% | 0% → 0% |
| owner_or_admin | 20/0/0 | 20/0/0 | 100% → 100% | 0% → 0% |
| manual_review_required | 0/0/20 | 0/0/20 | 0% → 0% (OBSERVE) | 0% → 0% |

| 집계 | Phase 1 | 재측정 |
|---|---:|---:|
| 탐지율 5종 기준(집행 label, 공격 100건) | 100/100 = 100% | 100/100 = 100% |
| 탐지율 6종 기준(public 제외 공격 120건, manual 포함) | 100/120 = 83.33% | 100/120 = 83.33% |
| 오탐율(비차단 대상 160건 = 정상 140 + public 공격 형태 20) | 0/160 = 0% | 0/160 = 0% |
| 요청별 verdict | PASS 140 · BLOCK 100 · OBSERVE 40 | 동일 |

혼동 행렬은 요청 단위까지 Phase 1과 같다. LLM 분류 정답률 표(6/7)는 step1_policies.md를 그대로 쓰므로 변화 없다.

## 지연 비교 (ms, nearest-rank)

| 지표 | Phase 1 | 재측정 | 차이 |
|---|---:|---:|---:|
| 프록시 p50 (280) | 3.056 | 4.079 | +1.02 |
| 프록시 p95 (280) | 4.741 | 6.659 | +1.92 |
| 백엔드 직접 p50 (280) | 1.957 | 3.082 | +1.13 |
| 백엔드 직접 p95 (280) | 3.142 | 4.014 | +0.87 |
| **추가 지연 p95(프록시 − 직접)** | **+1.599** | **+2.644** | +1.05 |
| 프록시 403 차단 건(100) p50 / p95 | 0.99 / 1.83 | 2.07 / 5.00 | +1.08 / +3.17 |
| 프록시 200 전달 건(180) p50 / p95 | 3.35 / 5.00 | 4.34 / 7.44 | +0.99 / +2.44 |
| 전달 건만 같은 케이스로 비교: 프록시 p95 − 직접 p95 | +1.85 | +3.44 | +1.59 |
| 최대값 프록시 / 직접 | 22.5 / 13.6 | 32.2 / 21.1 | |

label별 p95(프록시): membership_required normal 4.17 → 11.19, attack 1.67 → 7.66, tenant_match normal 4.25 → 8.21이 가장 크게 늘었고, role_required normal은 6.15 → 4.77로 줄었다. 20건 표본의 p95는 상위 1건(두 번째 큰 값)이라 단발 지연에 크게 흔들린다.

## 차이의 원인 후보 (확정 아님)

1. **실행 환경 차이가 가장 유력하다.** Phase 1은 로컬 프로세스, 이번은 Docker 컨테이너다. 프록시를 거치지 않는 백엔드 직접 호출도 p50 +1.13 ms·p95 +0.87 ms 느려졌으므로 Docker 포트 포워딩(com.docker.backend → WSL relay)이 모든 요청에 더해진 것으로 보인다. 프록시 경로는 호스트→프록시 컨테이너→백엔드 컨테이너로 홉이 하나 더 있어 가산분이 더 클 수 있다.
2. **백엔드를 부르지 않는 403 차단 건도 p50 +1.08 ms 느려졌다.** 이 구간은 JWT 검증·정책 매칭·(owner/tenant는) SQLite 조회만 하므로, Docker 홉 외에 프록시 자체 처리 비용 증가 가능성을 완전히 배제할 수 없다. 후보: Phase 2 이후 추가된 코드(캐시 generation·Redis 분기 판정·관측 카운터·탐지 큐 처리)가 플래그 off 상태에서 남기는 비용, 컨테이너 내 SQLite 읽기 전용 볼륨(`/data`, mode=ro) 접근 비용. 실행 중인 이미지가 현재 코드인지 미확인이라 코드 원인을 특정할 수 없다.
3. **호스트 부하·표본 크기.** 두 측정 모두 워밍업 없는 순차 280건이고 label당 20건이라 p95가 단일 지연 스파이크에 민감하다. 최대값이 22 → 32 ms로 커진 것도 같은 맥락이다.
4. 분리 측정을 하려면 같은 코드를 로컬 프로세스로 띄워 재측정하거나(환경 요인 분리), Docker에서 Phase 1 스냅샷 이미지와 비교해야 한다. 이번 작업 범위 밖이라 수행하지 않았다.

## 결론

- 탐지율·오탐율은 Phase 1과 요청 단위까지 동일하다(5종 100%, 6종 83.33%, 오탐 0/160).
- 추가 지연 p95는 +1.6 ms → +2.6 ms. 발표 카드에 +1.6 ms를 쓰려면 "2026-09-13 로컬 프로세스 측정"임을 밝혀야 하고, 현재 Docker 구성 기준은 +2.6 ms다.

## 파일

- 이번 결과: verification/METRICS.md, metrics-proxy.json, metrics-direct.json, metrics-details.json, metrics-policies-before.json(승인 후 ACTIVE 상태), metrics-attack-sim.log
- Phase 1 보존본: verification/phase1_20260913/ (SHA256SUMS)
