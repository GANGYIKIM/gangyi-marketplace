<!-- git-kit:report -->
<!-- git-kit:decisions -->
> [!NOTE]
> 결정 완료 (2026-10-22).
> Draft 유지: 아래 PR 머지 대기
> 머지 순서: #1 → #2 (이 PR)

## Decisions resolved
### D1. 로그인 실패 시 계정을 잠글지
- 결정: 잠금 · 반영 커밋 [{{short:origin/feat/account-lockout}}](https://github.com/test/demo/commit/{{rev:origin/feat/account-lockout}})
- [x] 잠금 (추천): 무차별 대입 방어. 오타 잦은 사용자는 불편
- [ ] 잠그지 않음: 사용성 좋음. 방어는 지연 시간에 의존
<!-- /git-kit:decisions -->

## Decisions made
- 잠금 판단을 어디에 두나
  - 정한 것: **로그인 처리와 떼어 lockout.ts의 함수 하나로 둠** [`src/auth/lockout.ts:3`](https://github.com/test/demo/blob/{{rev:origin/feat/account-lockout}}/src/auth/lockout.ts#L3)
  - 버린 안: 로그인 처리 안에 조건문으로 둠(결정이 바뀔 때 고칠 곳이 흩어짐)
