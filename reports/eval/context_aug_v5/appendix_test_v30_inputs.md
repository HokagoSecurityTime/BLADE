# 부록: test_v30 207건 문맥 보강 입력 (ctx4096 · ctx6144) — 2026-11-04

취약 API 5개 저장소(juice-shop TS, Pixi JS, DVWS-node JS, VAmPI Python, crAPI Java·Go·Python)의 oas_code 207건에 같은 분석기를 적용했다. 합성 58건은 코드 출처가 없어 건너뛴다(주지표 207건에도 없음). 권한 정의 파일 규칙은 test_v5 세 프로젝트 전용이라 여기서는 import 추적 헬퍼만 해당한다.

## 프로젝트별 통계

| 예산 | project | n | 블록 1개 이상 | 헬퍼 추가 | 블록 발견/유지 평균 | 미해석 건수 | 제외 사유 | 토큰 전/후 평균 | 후 최대 |
|---|---|---:|---:|---:|---|---:|---|---|---:|
| ctx4096 | VAmPI | 12 | 0 | 0 | 0 / 0 | 3 |  | 3054 / 3065 | 3224 |
| ctx4096 | crAPI | 53 | 1 | 1 | 0.02 / 0.02 | 22 | authentication 1 | 3060 / 3077 | 3470 |
| ctx4096 | juice-shop | 69 | 12 | 12 | 0.19 / 0.19 | 33 | authentication 11, no_authz_signal 16 | 3067 / 3085 | 3666 |
| ctx4096 | Pixi | 48 | 0 | 0 | 0 / 0 | 4 | authentication 2 | 3149 / 3160 | 3852 |
| ctx4096 | DVWS-node | 25 | 0 | 0 | 0 / 0 | 5 |  | 3029 / 3040 | 3194 |
| ctx6144 | VAmPI | 12 | 0 | 0 | 0 / 0 | 3 |  | 3054 / 3065 | 3224 |
| ctx6144 | crAPI | 53 | 1 | 1 | 0.02 / 0.02 | 22 | authentication 1 | 3060 / 3077 | 3470 |
| ctx6144 | juice-shop | 69 | 12 | 12 | 0.19 / 0.19 | 33 | authentication 11, no_authz_signal 16 | 3067 / 3085 | 3666 |
| ctx6144 | Pixi | 48 | 0 | 0 | 0 / 0 | 4 | authentication 2 | 3149 / 3160 | 3852 |
| ctx6144 | DVWS-node | 25 | 0 | 0 | 0 / 0 | 5 |  | 3029 / 3040 | 3194 |

블록이 붙은 건은 13/207(juice-shop 12, crAPI 1)이고 나머지 194건은 `[관련 권한 코드]
(없음)` 표식만 추가됐다(기존 입력 대비 +11 토큰 안팎). 두 예산의 입력은 207건 모두 동일하다(잘림 0). 이유: 취약 API 핸들러는 인가를 인라인(req.user.admin, user.admin 비교)으로 하거나 토큰 검증 헬퍼(token_validator, isAuthorized, checkToken)만 호출하며, 토큰 검증 헬퍼는 인증 전용 규칙으로 제외된다(authentication 14, no_authz_signal 16). 따라서 test_v30 207은 문맥 효과보다 "표식 추가"에 대한 회귀 확인이다.

## 샘플 5건 (언어별 1건 이상, seed 42)

### eef733c4cdf73432c9bc — juice-shop POST /rest/products/reviews

발견 1 / 유지 1 · 토큰 3198 → 3238 · 미해석 1: Unauthorized [unresolved] · 제외 {'no_authz_signal': 1, 'helper_cap': 0}

```
[관련 권한 코드]
FILE lib/insecurity.ts:52-52 [helper isAuthorized]
export const isAuthorized = () => expressJwt(({ secret: publicKey }) as any)
```

### 25fd1086a6999340c575 — Pixi POST /api/user/register

발견 0 / 유지 0 · 토큰 3101 → 3112 · 미해석 0:  · 제외 {'helper_cap': 0}

```
[관련 권한 코드]
(없음)
```

### 06ba24e97fdcb059ad92 — DVWS-node GET /api/v2/notes

발견 0 / 유지 0 · 토큰 2978 → 2989 · 미해석 0:  · 제외 {'helper_cap': 0}

```
[관련 권한 코드]
(없음)
```

### ff8c5eda79000fa6687f — VAmPI POST /books/v1

발견 0 / 유지 0 · 토큰 3140 → 3151 · 미해석 0:  · 제외 {'helper_cap': 0}

```
[관련 권한 코드]
(없음)
```

### 15af38ebe8faf15c930f — crAPI GET /workshop/api/management/users/all

발견 1 / 유지 1 · 토큰 3164 → 3470 · 미해석 6: Admin [unresolved], authorised [unresolved], jwt_auth_required [unresolved], jwt_auth_required (depth2 in views.py) [external:utils/jwt], Admin (depth2 in views.py) [not imported / not defined in file] · 제외 {'helper_cap': 0}

```
[관련 권한 코드]
FILE services/workshop/crapi/user/views.py:35-72 [helper AdminUserView]
class AdminUserView(APIView, LimitOffsetPagination):
    """
    View for admin user to fetch user details
    """
    @jwt_auth_required
    def get(self, request, user=None):
        """
        Admin user view to fetch user details
        :param request: http request for the view
            method allowed: GET
            http request should be authorised by the jwt token of the user
            mandatory fields: []
        :returns Response object with
            user details and 200 status if no error
            message and corresponding status if error
        """
        userdetails = UserDetails.objects.all().order_by("id")
        if not userdetails:
            return Response(
                {"message": messages.NO_USER_DETAILS}, status=status.HTTP_404_NOT_FOUND
            )
        paginated = self.paginate_queryset(userdetails, request)
        serializer = UserDetailsSerializer(paginated, many=True)
        response_data = dict(
            users=serializer.data,
            next_offset=(
                self.offset + self.limit
                if self.offset + self.limit < self.count
                else None
            ),
            previous_offset=(
                self.offset - self.limit if self.offset - self.limit >= 0 else None
            ),
            count=self.get_count(paginated),
        )
        return Response(response_data, status=status.HTTP_200_OK)
```

ctx4096과 ctx6144 입력 동일 여부: True.

