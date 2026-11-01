# 남은 16개 라우트의 코드 기반 분류

분석 미지원 16건을 모두 같은 문제로 다루지 않고 요청 의미와 인증 의존성을 분리했다. 이것은 최종 7종 라벨 확정이 아니라 후속 추출 범위 결정이다.

| 유형 | 건수 | 해석 |
|---|---:|---|
| caller_relation | 5 | 요청자의 즐겨찾기·팔로우 관계 또는 피드를 조작한다. 대상 글이나 다른 프로필의 소유자여야 한다는 뜻이 아니다. |
| public_read_candidate | 5 | 공개 조회 후보. optional 인증 또는 인증 의존성 없음과 핸들러를 대조했다. 실제 배포 공개 접근은 미확정. |
| creator_binding | 2 | 인증된 요청자를 새 레코드 작성자로 기록한다. 기존 객체 소유자 일치 검사와 구분한다. |
| authentication_entry | 2 | 기존 토큰 없이 로그인 자격 증명 검증 또는 가입을 수행한다. 인증 전 진입과 무조건 요청 성공은 다르다. |
| self_account | 2 | 인증된 사용자 객체를 응답·수정 대상으로 사용한다. 임의 대상 ID 비교와 다른 요청자 고정 방식이다. |

## 라우트별 상태

| 메서드 | 상대 경로 | 핸들러 | 인증 | 유형 |
|---|---|---|---|---|
| GET | /feed | get_articles_for_user_feed | required | caller_relation |
| POST | /{slug}/favorite | mark_article_as_favorite | required | caller_relation |
| DELETE | /{slug}/favorite | remove_article_from_favorites | required | caller_relation |
| GET |  | list_articles | optional | public_read_candidate |
| POST |  | create_new_article | required | creator_binding |
| GET | /{slug} | retrieve_article_by_slug | optional | public_read_candidate |
| POST | /login | login | none_found | authentication_entry |
| POST |  | register | none_found | authentication_entry |
| GET |  | list_comments_for_article | optional | public_read_candidate |
| POST |  | create_comment_for_article | required | creator_binding |
| GET | /{username} | retrieve_profile_by_username | optional | public_read_candidate |
| POST | /{username}/follow | follow_for_user | required | caller_relation |
| DELETE | /{username}/follow | unsubscribe_from_user | required | caller_relation |
| GET |  | get_all_tags | none_found | public_read_candidate |
| GET |  | retrieve_current_user | required | self_account |
| PUT |  | update_current_user | required | self_account |

## 핵심 발견

- 인증만으로 역할 요구를 만들지 않는다. 생성자 기록은 기존 객체 소유권 검사와 다르다.
- 본인 계정은 대상 객체를 인증 사용자로 고정하는 방식이다. 직접 비교문만 찾는 기존 추출기는 이를 놓친다.
- 즐겨찾기·팔로우는 요청자의 관계 레코드가 보호 대상이다. 글·프로필 소유권으로 치환하면 의미가 바뀐다.
- 공개 후보 5건 중 4건은 직접·간접 optional 인증 경로가 있고, tags는 인증 의존성이 발견되지 않았다. tags를 공개라고 확정하는 근거는 아직 부족하다.
- login/register에는 기존 토큰 요구가 없지만 login은 비밀번호를 검사한다. public이 모든 입력을 성공시킨다는 뜻은 아니다.

## 다음 구현 우선순위

1. self_account 2건의 요청자→수정 대상 바인딩을 추출하고 타인 ID 주입 차단을 격리 테스트한다.
2. creator_binding 2건의 작성자 강제 귀속을 확인한다. 기존 객체 조건과 별도 저장한다.
3. caller_relation 5건은 repository→SQL에서 요청자 키가 WHERE/INSERT에 어떻게 쓰이는지 추적한다. 대상 객체 소유권으로 자동 매핑하지 않는다.
4. 공개 후보는 실제 익명 요청과 유효·무효 토큰을 구분해 통합 검증한다.

현재 단계에서 전체 서버·JWT·DB를 실행하지 않았다. 위 요청 의미 분류는 소스 검토이며, 지원되지 않는 모든 호출이 해소됐다는 뜻이 아니다. 라벨·데이터셋·런타임은 변경하지 않았다.

출처: https://github.com/nsidnev/fastapi-realworld-example-app/tree/029eb7781c60d5f563ee8990a0cbfb79b244538c
