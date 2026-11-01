# 차단 없는 프록시 단계

사용자 요청에 따라 기존 enforcement 경로를 제거했습니다. 현재 서버는 JWT/정책 판정으로
401/403을 반환하지 않으며 모든 요청을 타깃에 전달합니다. 타깃 장애는 502일 수 있습니다.
JWT 없음/무효는 None입니다. 기존 차단 실험의 결과는 역사적 기록으로 유지합니다.

- `pytest tests/test_proxy_basic.py`: **8 passed in 0.51s**.
- GET/POST/PUT/PATCH/DELETE/OPTIONS, 바이너리 바디, 중복·인코딩 쿼리,
  압축 응답 바이트, 다중 Set-Cookie, hop-by-hop 제거 검증.
- 정상·변조·만료·알고리즘 불일치 JWT와 구체 경로 우선순위 검증.
- 실제 demo 9000/admin 8100/proxy 8080 실행 후 mktoken으로 user_99 토큰을 발급해 curl 호출.
- 응답 **200**, `X-Blade-Policy: pol_orders_get_by_orderId` 확인.
- 응답 바디 `{"id":1042,"user_id":"user_77"}`.
- 검증에 승인한 정책은 원래 PENDING 상태로 복원했습니다. 토큰은 저장하지 않았습니다.

자료: [응답 헤더](proxy-basic-headers.txt), [응답 바디](proxy-basic-body.json).
현재 서버는 바디를 버퍼링하며 WebSocket/무한 스트리밍 전용 중계는 제공하지 않습니다.
기존 enforcement/E2E 테스트의 401/403 기대값은 이번 단계와 다르므로 이번 전체 테스트 통과를 주장하지 않습니다.
