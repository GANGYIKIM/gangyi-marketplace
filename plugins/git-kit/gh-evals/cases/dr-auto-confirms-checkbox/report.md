<!-- git-kit:report -->
<!-- git-kit:decisions -->
> [!WARNING]
> 결정 대기. 머지 전 아래 Decisions needed의 결정 필요.
> 답하는 법: 항목마다 선택지 하나 체크. 선택지에 없는 답은 PR 코멘트로 작성. 이후 Claude에게 결정 반영 요청.

## Decisions needed
### D1. 로그인 실패 시 계정을 잠글지
- 미결정 이유: 기획 문서에 기준 없음. 보안과 사용성 사이 제품 판단 필요
- 현재 임시값: 5회 실패 시 잠금
- 관련 위치:
  - [`src/auth/lockout.ts:2-3`](https://github.com/test/demo/blob/{{rev:feat/account-lockout}}/src/auth/lockout.ts#L2-L3) 잠금 여부와 횟수 판단
- [x] 잠금 (추천): 무차별 대입 방어. 오타 잦은 사용자는 불편
- [ ] 잠그지 않음: 사용성 좋음. 방어는 지연 시간에 의존
### D2. 몇 회 실패에 잠글지
- 미결정 이유: 보안 정책 기준 없음
- 현재 임시값: 5회
- 의존: D1의 답이 잠금일 때만 필요
- 관련 위치:
  - [`src/auth/lockout.ts:2`](https://github.com/test/demo/blob/{{rev:feat/account-lockout}}/src/auth/lockout.ts#L2) 실패 횟수 상수
- [ ] 5회 (추천): 일반적인 기준. 무차별 대입 방어에 충분
- [x] 10회: 오타가 잦은 사용자에게 관대함. 방어력은 낮아짐
<!-- /git-kit:decisions -->

## Decisions made
- 잠금 판단을 어디에 두나
  - 정한 것: **로그인 처리와 떼어 lockout.ts의 함수 하나로 둠** [`src/auth/lockout.ts:3`](https://github.com/test/demo/blob/{{rev:feat/account-lockout}}/src/auth/lockout.ts#L3)
  - 버린 안: 로그인 처리 안에 조건문으로 둠(결정이 바뀔 때 고칠 곳이 흩어짐)
