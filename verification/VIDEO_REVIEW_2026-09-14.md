# 영상 검토 — 2026-09-14 11-28-25

대상: `2026-09-14 11-28-25.mp4` (약 2분 44초, 1920×1032).
영상의 명령·응답 장면을 COMMANDS.md와 비교했다. 기존 SQLite는 읽기 전용으로 조회하여 영상의 request_id와 대조했다. 코드·정책·서비스는 변경하지 않았다.

## 결론

차단 시연의 핵심은 제대로 실행됐다. 다만 **step4 URL 오타**, **이미 완료된 생성/승인의 반복**, **탐지 로그의 화면 가독성**은 발표 영상에서 보완할 필요가 있다.

| 대략적 구간 | 항목 | 영상에서 확인한 내용 | 판정 |
|---|---|---|---|
| 00:00~00:05 | 토큰 변수 | TOKEN99, TOKEN77, FORGED 설정 | 준비 장면 확인 |
| 00:05~00:23 | step1 생성 | 409, Generated policy ids collide or already exist | 기존 정책 중복. 새 생성 성공 장면은 아님 |
| 00:24~01:05 | step2 승인 | ACTIVE cannot transition to ACTIVE, 409 반복 | 이미 승인됨. 새 승인 성공 장면은 아님 |
| 약 01:06~01:12 | ACTIVE 조회 | 활성 정책 목록 출력 | 기존 정책 상태 확인 |
| 약 01:13~01:20 | step3 타인 조회 | TOKEN99 → /orders/1042 → 403 | 확인 |
| 약 01:22~01:40 | step4 소유자 조회 | TOKEN77 → **/orders/104** → 404 | 명령 오타. 기대했던 /orders/1042가 아님 |
| 약 01:40~01:46 | step5 타인 DELETE | TOKEN99 → DELETE /orders/1042 → 403 | 확인 |
| 약 01:46~01:53 | step5 소유자 재조회 | TOKEN77 → /orders/1042 → 200, id=1042/user_id=user_77 | 삭제 방지와 정상 소유자 조회 확인 |
| 약 01:53~01:57 | step6 무토큰 | Authorization 없이 → 403 | 확인 |
| 약 01:57~02:03 | step7 탐지 조회 | 긴 JSON 출력, 화면 하단에는 전날 로그가 주로 노출 | 이번 요청 3건의 request_id 대조는 화면에서 명확하지 않음 |
| 약 02:03~02:08 | break1 | FORGED → 403 | 확인. 영상은 변수 사용과 차단 결과를 보여줌 |
| 약 02:08~02:14 | break2 | /nothing/here → 404 | non-5xx 확인 |
| 약 02:14~02:25 | break2 로그 조회 | 긴 JSON 출력, 해당 OBSERVE 행을 특정해 보여주지는 않음 | OBSERVE 시각적 증거 보완 권장 |
| 약 02:26~02:44 | 백엔드 미도달 | wc -l 470 → TOKEN99 요청 403 → wc -l 470 | 로그 줄 수 불변 확인 |

409는 기존 상태에 대한 정상 거절이다. COMMANDS.md에 이미 생성·승인 완료 및 녹화는 step3부터 진행하도록 적혀 있었다.
따라서 앞부분을 시스템 오류로 설명해서도 안 되고, 정책 생성·승인 성공 장면으로 설명해서도 안 된다.

## 영상과 DB의 교차 확인

영상 응답의 request_id와 기존 DB 기록이 일치했다. [읽기 전용 조회 결과](video-review/db-corroboration.json).

- `38ba1b4c-...`: user_99 GET /orders/1042, BLOCK / policy_mismatch.
- `4ba000dd-...`: user_77 GET /orders/104, PASS / object_not_found. 백엔드가 404 처리한 것으로 오타와 일치한다.
- `d94f79e4-...`: user_99 DELETE /orders/1042, BLOCK.
- `632c5e8b-...`: user_77 GET /orders/1042, PASS.
- `ad4a4447-...`: 무토큰 GET, BLOCK / no_token.
- `fec7490a-...`: FORGED 요청, BLOCK / no_token (JWT 검증 실패 시 claims=None으로 처리하는 기존 설계).
- `6e195b29-...`: /nothing/here, OBSERVE / no_policy.
- `8872ce20-...`: 마지막 미도달 확인용 GET, BLOCK.

즉 해당 BLOCK/OBSERVE가 저장되지 않은 것은 아니다. 긴 JSON의 앞부분이 화면 위로 밀려, 영상만으로 이번 요청과 로그를 대조하기 어려운 점이 문제다.

## 최소 재촬영 권장

1. 이미 생성된 ACTIVE 정책으로 시연한다는 안내 후 step3부터 시작한다. 새 생성/승인을 재현하려고 데이터를 초기화할 필요는 없다.
2. 소유자 조회는 아래 정확한 URL로 입력하고 200을 2~3초 보여준다.

```bash
curl -i -H "Authorization: Bearer $TOKEN77" http://localhost:8080/orders/1042
```

3. 차단·무토큰·위조·미매칭 요청 뒤 로그는 한 행에 하나씩 보여주고, 응답의 request_id와 대조한다. 아래는 표시 방식만 줄이며 서비스/코드는 바꾸지 않는다.

```bash
curl -s 'http://localhost:8100/detections?limit=10' | ./.python/python.exe -c "import json,sys; [print(r['request_id'], r['method'], r['path'], r['verdict'], r['reason']) for r in json.load(sys.stdin)]"
```

4. 마지막 470 → 470 장면은 그대로 사용 가능하다. 이는 access log 기준 증거이며 패킷 캡처 증거는 아니다.

전체를 다시 찍기 어렵다면 앞부분 409 구간은 사전 준비 완료 설명으로 대체하고, step4의 정확한 요청 및 간결한 로그 대조 장면만 추가하면 된다.
영상 하단 검은 여백이 크므로 녹화 영역을 터미널에 맞추면 발표 화면에서 글자가 더 잘 보인다.

## 장면 증거

- [step4 URL 오타](video-review/0090.png)
- [소유자 200 및 주문 유지](video-review/0110.png)
- [무토큰 403](video-review/0114.png)
- [위조 토큰 403](video-review/0126.png)
- [미매칭 경로 404](video-review/0132.png)
- [470 → 470](video-review/0160.png)
