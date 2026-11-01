# 외부 FastAPI 추출 어댑터와 다음 단계 검증

전체 라우트 19건을 스캔해 3건에서 연결된 인가 조건을 자동 추출했다. 기존 수동 지정 3건만 검색한 것이 아니며, 나머지는 지원하지 못하거나 구체 조건이 미확보된 상태다.

| 단계 | 결과 |
|---|---|
| 모듈 import → Depends → 비교 함수 자동 연결 | 3 라우트 |
| 연결된 조건의 라벨 제안 | owner_match 3건 |
| 추출식 vs 원본 거부 함수 | 12/12 |
| 원본 거부 함수를 의존성으로 실행한 격리 HTTP 검사 | 12/12 |
| 전체 엔드포인트 정답 확정 | 0건 |

## 구현

비동기 라우트, 데코레이터 dependencies 및 인자 Depends, 절대 import의 함수 연결, `if not predicate: raise HTTPException(403)`, 속성 동등 비교를 지원한다. 실제 인자 바인딩을 반영하고 AND/OR/NOT 구조를 보존한다. 요청자 의존성과 author.username 비교를 확인한 경우에만 owner 조건 후보를 만든다. 전체 요청의 나머지 검사가 해결되지 않았으므로 후보를 최종 라벨로 승격하지 않는다.

## 검증 해석

이전에는 순수 비교 함수만 실행했다. 이번에는 원본 거부 함수 본문도 실행하고 FastAPI의 Depends 경로로 HTTP 200/403을 확인했다. 단, 원본 JWT·DB·원본 비즈니스 핸들러를 실행한 통합 테스트가 아니다. 인자에는 대역 객체를 제공하고 인증 헤더는 테스트용이다. article 검사 두 라우트가 같은 함수를 공유하므로 12건이 독립 정책 12개인 것은 아니다.

## 남은 제한

인증 factory, DB 객체 조회, 전역 middleware, include_router prefix는 완전 분석하지 않는다. 이 소스를 보고 어댑터를 확장했으므로 독립 외부 정확도로 주장하지 않는다. 역할·tenant·구독 조건의 외부 검증은 여전히 별도 필요하다. 미지원 라우트를 public으로 바꾸지 않는다. 원본 소스·기존 보고서·런타임·고정 test를 유지한다.

## 전체 라우트 상태

| 메서드 | 상대 경로 | 핸들러 | 추출 조건 수 |
|---|---|---|---:|
| GET | /feed | get_articles_for_user_feed | 0 |
| POST | /{slug}/favorite | mark_article_as_favorite | 0 |
| DELETE | /{slug}/favorite | remove_article_from_favorites | 0 |
| GET |  | list_articles | 0 |
| POST |  | create_new_article | 0 |
| GET | /{slug} | retrieve_article_by_slug | 0 |
| PUT | /{slug} | update_article_by_slug | 1 |
| DELETE | /{slug} | delete_article_by_slug | 1 |
| POST | /login | login | 0 |
| POST |  | register | 0 |
| GET |  | list_comments_for_article | 0 |
| POST |  | create_comment_for_article | 0 |
| DELETE | /{comment_id} | delete_comment_from_article | 1 |
| GET | /{username} | retrieve_profile_by_username | 0 |
| POST | /{username}/follow | follow_for_user | 0 |
| DELETE | /{username}/follow | unsubscribe_from_user | 0 |
| GET |  | get_all_tags | 0 |
| GET |  | retrieve_current_user | 0 |
| PUT |  | update_current_user | 0 |

출처: https://github.com/nsidnev/fastapi-realworld-example-app/tree/029eb7781c60d5f563ee8990a0cbfb79b244538c
