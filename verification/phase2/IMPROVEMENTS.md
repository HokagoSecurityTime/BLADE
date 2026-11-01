# 2026-10-12 개선 및 재검증

**최신 후속 상태는 [FINAL_STATUS.md](FINAL_STATUS.md)를 우선한다.** 묶음 전송, 로그 전용 AOF Redis, 192개 회귀 테스트, 실제 Docker 적용까지 완료했다. 아래는 직전 개선 회차의 측정·배포 전 기록으로 보존한다.

사용자의 후속 요청에 따라 기존 '프로파일만 수행' 범위를 확장해 런타임을 개선했다. 원본 측정과 실패 기록은 보존한다.

## 변경

- Redis 비동기 조회 병합, TTL 보존, 서버 무효화 통지를 이용한 로컬 캐시와 비동기 쓰기. 캐시 키 목록은 상한을 넘으면 빠른 부재 판단을 끄고 Redis 조회로 돌아간다.
- 같은 시점의 소유권 DB 조회를 읽기 전용 연결 하나로 묶는다. 잘못된 조회 하나가 다른 요청까지 실패시키지 않는다.
- 탐지 로그는 백그라운드 Redis Stream → SQLite/JSONL 묶음 저장으로 전달한다. 커밋 후 Stream에서 제거하고 재전송은 request_id로 중복 제거한다. Redis 장애 시 기존 HTTP 저장 API로 우회한다.
- 큐가 가득 차면 Phase 2는 대기하여 부하를 제한한다. Phase 1 동작은 유지한다.
- 모순된 LLM 차단 설명은 실제 verdict에 맞는 결정적 문구로 교체한다. 모델 출력 자체의 정확성을 보장한다는 의미는 아니다.
- 컨테이너별 DB 경로 차이와 무관하게 프록시/관리 API가 같은 Stream을 쓰도록 Phase 2 Compose에 공통 namespace를 지정했다.

## 성능

[30초 원본 및 전체 표](load-final-process-30s.md). 클라이언트·프록시·관리 API·백엔드를 별도 프로세스로 실행한 Windows 개발 환경이다. 이전 단일 프로세스 결과와 직접적인 개선 배수로 비교하지 않는다. 최종 측정 후 namespace, 캐시 목록 상한, 오류 조회 격리 보완이 추가됐으며 그 이후 전체 성능 재측정은 하지 않았다.

| 동시 요청 | 캐시 | Phase 2 − Phase 1 p95 | +5ms 기준 |
|---|---|---|---|
| 50 | cold | -5.90ms | PASS |
| 50 | warm | +2.12ms | PASS |
| 100 | cold | -6.14ms | PASS |
| 100 | warm | +57.12ms | FAIL |
| 200 | cold | -165.84ms | PASS |
| 200 | warm | +7.75ms | FAIL |

전 조건 HTTP 오류 0건. Phase 2 탐지 로그는 129,572 / 129,572건 저장됐다. Phase 1은 로그가 크게 누락되므로 지연 수치만으로 동등한 일을 수행했다고 해석할 수 없다. **7번 성능 기준 전체 통과는 아직 아니다.**

## 기능·장애 검증

- [전용 Redis 중단·복구](stage2-improved-result.json): 5/5 PASS. 정책 전파 0.093초, 중단 중 OBSERVE 200 및 탐지 저장, 폴링으로 enforce 403 반영, 재시작 후 200 복구. 고정 컨테이너 ID·검증 라벨·16382 포트 확인 후 그 컨테이너만 조작했다.
- [실제 Redis 캐시·Stream](cache-stream-20261012-193941/results.json): 원격 수정/교차 캐시 삭제/TTL, DB 일시 장애 후 재시도, 200건 재전송에서 고유 100건 저장 및 Stream 잔여 0건.
- [실제 Slack](slack-live-20261012-184110/results.json): #blade-alert에 observe/enforce 각각 한 건 도착, 사용자 확인 완료. observe 미차단·enforce 차단 문구 일치.
- 회귀 검증: [최종 pytest 출력](improvement-pytest-final.txt).

## 남은 제한

warm 100/200 성능 기준 미달은 미해결이다. 메모리 큐는 프로세스 강제 종료에 내구성이 없으며, 현재 Redis Compose는 persistence를 꺼 두므로 Redis 강제 중단 전에 미저장된 Stream 항목까지 보장하지 않는다. Redis와 HTTP 저장 API가 동시에 실패하는 경우 로그 전달도 보장하지 않는다. DB 장애 재시도 중 Stream 적체량에 운영 상한이 없다.

이 문서는 소스 수정과 격리된 검증 결과다. 실행 중인 기존 Docker 애플리케이션의 이미지 재빌드·배포 완료를 뜻하지 않는다.
