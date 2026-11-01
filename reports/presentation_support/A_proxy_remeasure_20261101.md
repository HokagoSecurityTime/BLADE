# A. 프록시 집행 성능 재측정 — 2026-11-01 (현재 코드 기준, 커밋 7b857e2)

Phase 1 측정(2026-09-13)과 같은 스크립트(`verification/measure_presentation.py` → `scripts/attack_sim.py -n 20 --prepare-demo`)·같은 인자로 다시 측정했다. 코드·데이터·동결 파일은 수정하지 않았고 커밋하지 않았다. 2026-10-31에 같은 절차의 재측정이 한 번 더 있었으므로(커밋 92a2bdc, verification/remeasure_20261031.md) 세 번의 결과를 나란히 둔다.

## A-1. 백업

| 항목 | 내용 |
|---|---|
| Phase 1 원본 | `verification/phase1_20260913/`(METRICS.md, metrics-*.json, metrics-attack-sim.log, SHA256SUMS). 2026-10-31 커밋 92a2bdc에 이미 보존돼 있었고 이번에 `sha256sum -c`로 6개 파일 모두 OK 확인(mtime 2026-09-13 유지). |
| 2026-10-31 재측정본 | 측정 직전 `verification/METRICS.md`·metrics-*.json·metrics-attack-sim.log(= 커밋 92a2bdc·HEAD 내용)를 `verification/remeasure_20261031/`에 복사하고 SHA256SUMS 기록(untracked). 이번 측정이 verification/ 원본을 덮어썼다. |
| 이번(2026-11-01) 결과 | `verification/METRICS.md`·metrics-*.json(수정됨, git status M) 및 사본 `reports/presentation_support/A_remeasure_20261101/`(SHA256SUMS 포함) |

## A-2. 측정 조건

| 항목 | 값 |
|---|---|
| 커밋 | `7b857e2283b3dcc47e14720e4e4c406384b28328` (feat/lora-pipeline, 작업 트리 clean). 10-31 재측정(92a2bdc 시점 코드 51dff137) 이후 `proxy/ admin_api/ demo_backend/ common/ pipeline/ scripts/attack_sim.py measure_presentation.py docker-compose.yml Dockerfile`에 변경 없음(`git diff --stat 92a2bdc 7b857e2` 빈 결과). |
| 측정 시각 | 2026-10-31T17:48:10 UTC (= 2026-11-01 02:48 KST) |
| BLADE_PHASE2_ENABLED | 관리 API `/features` 응답 `phase2=false`(mode·observability·alerts·explain·rag·reanalysis 모두 false). `.env`에 해당 키 없음(코드 기본값 false, `.env.example`도 false). 프록시 컨테이너의 환경변수 직접 조회는 docker CLI가 60초 안에 응답하지 않아 **미확인**(10-31과 같은 상태). |
| 서비스 실행 방식 | Docker Desktop 컨테이너: 9000·8100·8080·3000을 `com.docker.backend`(PID 15060, 시작 2026-10-15 14:21)가 수신. `docker ps`·`docker inspect`가 응답하지 않아 **이미지 빌드 시각·컨테이너 시작 시각은 미확인**. 10-31 재측정과 같은 컨테이너로 추정(그 사이 재시작 기록 없음). |
| 스크립트 | attack_sim.py SHA-256 `e84571c7…`(Phase 1·10-31·이번 동일, 실행 전후 불변 확인), measure_presentation.py 미수정 |
| 정책 | 측정 전: public만 ACTIVE, 6건 PENDING → 6건 approve(200) → 7초 대기 → 측정 → 6건 rollback(200) → 측정 전과 동일(public ACTIVE·6건 PENDING) 확인. `--prepare-demo`의 users 정책 임시 변경도 복원(policies_restored=true). |
| 오류 | 프록시 280건·직접 280건 모두 HTTP/연결 오류 0, 비-200 0 |

## A-3. 비교표 (근거: A_comparison.json, 생성 스크립트는 scratchpad a_compare.py — 각 run의 metrics-proxy.json·metrics-direct.json·metrics-details.json에서 집계)

### 표 A-1. label별 TP / FP / FN (각 run: label당 정상 20 + 공격 20)

| label | Phase 1 (2026-09-13) TP/FP/FN | 재측정 1 (2026-10-31) TP/FP/FN | 재측정 2 (2026-11-01, 이번) TP/FP/FN |
|---|---:|---:|---:|
| public | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| role_required | 20 / 0 / 0 | 20 / 0 / 0 | 20 / 0 / 0 |
| membership_required | 20 / 0 / 0 | 20 / 0 / 0 | 20 / 0 / 0 |
| tenant_match | 20 / 0 / 0 | 20 / 0 / 0 | 20 / 0 / 0 |
| owner_match | 20 / 0 / 0 | 20 / 0 / 0 | 20 / 0 / 0 |
| owner_or_admin | 20 / 0 / 0 | 20 / 0 / 0 | 20 / 0 / 0 |
| manual_review_required | 0 / 0 / 20 | 0 / 0 / 20 | 0 / 0 / 20 |

public의 공격 형태 20건은 인가 제한이 없어 TN, manual_review_required의 타인 조회 20건은 OBSERVE 통과라 FN이다(시뮬레이터 정의).

### 표 A-2. 탐지율·오탐율·지연

| 지표 | Phase 1 (2026-09-13) | 재측정 1 (2026-10-31) | 재측정 2 (2026-11-01, 이번) |
|---|---:|---:|---:|
| 탐지율 5종 기준 (manual 제외, TP/(TP+FN)) | 100.00% (100/100) | 100.00% (100/100) | 100.00% (100/100) |
| 탐지율 6종 기준 (manual FN 포함) | 83.33% (100/120) | 83.33% (100/120) | 83.33% (100/120) |
| 오탐율 정상 140건 기준 (403/정상 요청) | 0.00% (0/140) | 0.00% (0/140) | 0.00% (0/140) |
| 오탐율 시뮬레이터 정의 FP/(FP+TN) (public 공격형 20건을 TN에 포함) | 0.00% (0/160) | 0.00% (0/160) | 0.00% (0/160) |
| 프록시 p50 (ms) | 3.056 | 4.079 | 4.010 |
| 프록시 p95 (ms) | 4.741 | 6.659 | 6.045 |
| 백엔드 직접 p50 (ms) | 1.957 | 3.082 | 2.901 |
| 백엔드 직접 p95 (ms) | 3.142 | 4.014 | 4.013 |
| **p95 차이 (프록시 − 직접, ms)** | **+1.599** | **+2.644** | **+2.033** |
| 프록시 요청 수 / 오류 | 280 / 0 | 280 / 0 | 280 / 0 |
| 직접 요청 수 / 비-200 | 280 / 0 | 280 / 0 | 280 / 0 |
| LLM 분류 정답률 (step1 기록 기준, 재생성 아님) | 6/7 | 6/7 | 6/7 |
| attack_sim.py SHA-256 앞 12자리 / 정책 복원 | e84571c73319 / True | e84571c73319 / True | e84571c73319 / True |
| 측정 시각 UTC | 2026-09-13T12:40:06 | 2026-10-30T17:01:13 | 2026-10-31T17:48:10 |

## A-4. 차이와 원인 후보 (확정 아님)

- **탐지·오탐은 세 번 모두 요청 단위까지 동일하다**(TP 100 · FN 20 · FP 0 · TN 160). 5종 기준 100%, 6종 기준 83.33%, 정상 140건 기준 오탐 0%.
- **지연만 다르다.** p95 추가 지연은 Phase 1 +1.60 ms → 10-31 +2.64 ms → 이번 +2.03 ms. 이번과 10-31은 같은 Docker 구성이고 코드 변경이 없는데도 0.6 ms 차이가 나므로, 이 폭은 측정 잡음 범위로 봐야 한다.
  1. **실행 환경(로컬 프로세스 vs Docker)** — Phase 1은 로컬 백그라운드 프로세스, 10-31·이번은 Docker 컨테이너다. 프록시를 거치지 않는 백엔드 직접 호출도 p50 1.96 → 3.08 / 2.90 ms, p95 3.14 → 4.01 / 4.01 ms로 느려졌으므로 Docker 포트 포워딩(com.docker.backend → wslrelay)이 모든 요청에 더해진 것이 가장 유력하다. 프록시 경로는 호스트→프록시 컨테이너→백엔드 컨테이너로 홉이 하나 더 있다.
  2. **표본 크기·워밍업 없음** — label당 20건, 순차 280건, 워밍업 없음이라 p95는 상위 몇 건의 스파이크에 흔들린다. 같은 환경·같은 코드인 10-31과 이번의 프록시 p95 차이(6.66 → 6.05)가 그 예다.
  3. **Phase 2 이후 추가된 코드의 플래그-off 비용**(캐시 generation·Redis 분기 판정·관측 카운터·탐지 큐) — 403 차단 건은 백엔드를 부르지 않는데도 10-31에 p50이 Phase 1보다 1 ms 느렸다(remeasure_20261031.md). 실행 중인 이미지가 현재 코드인지 미확인이라 코드 원인을 특정할 수 없다.
  4. **호스트 부하** — 측정 중 Docker Desktop·Ollama(ollama.exe 상주)·IDE가 함께 떠 있었다. 부하 측정은 하지 않았다.
- 분리하려면 같은 커밋을 로컬 프로세스(verification/launch_presentation.py 방식)로 띄워 재측정하거나, 동일 환경에서 n을 늘려(예: -n 100) 반복해야 한다. 이번 범위 밖이라 하지 않았다.

## A-5. 발표 수치 (사용자 결정 2026-11-01)

- **지연: 현재 코드·Docker 기준 p95 추가 지연 +2.0 ms(2026-11-01 측정)를 쓴다.** Phase 1 +1.6 ms(2026-09-13, 로컬 프로세스)는 주석으로 병기한다.
- verification/METRICS.md·metrics-*.json·metrics-attack-sim.log는 11-01 측정 결과로 확정(커밋). verification/phase1_20260913/(Phase 1 원본)·verification/remeasure_20261031/(10-31 본)은 보존(커밋).

### (결정 전 제안 원문)

- 탐지율·오탐율: "5종 100% / 6종(manual 보류 포함) 83.3% / 오탐 0%(정상 140건)" — 세 측정 모두 동일하므로 그대로 쓴다.
- 추가 지연: 현재 코드·Docker 기준 **p95 +2.0 ms(2026-11-01)**. +1.6 ms를 쓰려면 "2026-09-13 로컬 프로세스 측정"임을 밝힌다. 10-31 값(+2.6 ms)과의 차이는 같은 환경·같은 코드의 반복 측정 편차다.
- 분류 정답률 6/7은 2026-09-13 step1(qwen2.5:7b, BLADE_CLASSIFIER=llm) 기록이며 이번에 재생성하지 않았다. LoRA v5 경로의 demo 정책 결과는 reports/eval/lora_v5_gguf/pipeline_compare.md(의도 일치 6/7, premium은 manual)를 쓴다.

## 파일

- 이번 결과 사본: reports/presentation_support/A_remeasure_20261101/{METRICS.md, metrics-proxy.json, metrics-direct.json, metrics-details.json, metrics-policies-before.json, metrics-attack-sim.log, SHA256SUMS}
- 비교 집계: reports/presentation_support/A_comparison.json, A_comparison_tables.md
- 10-31 재측정본: verification/remeasure_20261031/ (untracked 사본) · 설명 verification/remeasure_20261031.md (커밋됨)
- Phase 1 원본: verification/phase1_20260913/ (SHA256SUMS OK)
