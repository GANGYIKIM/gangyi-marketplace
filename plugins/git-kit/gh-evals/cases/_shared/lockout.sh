#!/bin/bash
# 공통 시나리오: feat/account-lockout에 결정 대기 커밋이 있다.
# D1은 계정을 잠글지, D2는 몇 회 실패에 잠글지이고, D2는 D1에 의존한다.
source "$GK_LIB/setup.sh"

# lockout_commit: 지금 HEAD에서 feat/account-lockout을 만들고 결정 대기 코드를 커밋해 push
lockout_commit() {
  git switch -q -c feat/account-lockout
  gk_commit src/auth/lockout.ts "✨ feat: add account lockout after failed logins" <<'TS'
// TODO: 잠금 여부와 횟수 미정
const MAX_ATTEMPTS = 5;
export const shouldLock = (attempts: number) => attempts >= MAX_ATTEMPTS;
TS
  gk_push feat/account-lockout
}

lockout_branch() {
  gk_init_repo
  lockout_commit
}

# lockout_update_scenario: lockout_branch 뒤 기록(D1 대기, D2)을 쓰고, push 안 한 테스트 커밋을
# 더하고, main을 한 커밋 앞서게 한다 (기존 PR을 갱신하는 pr-writer 케이스)
lockout_update_scenario() {
  lockout_branch
  { record_head; d1_block 대기; d2_block; } | gk_record feat/account-lockout
  gk_commit src/auth/lockout.test.ts "✅ test: cover lockout threshold" <<'TS'
import { shouldLock } from "./lockout";
if (shouldLock(4) || !shouldLock(5)) { throw new Error("threshold"); }
TS
  git switch -q main
  gk_commit docs/security.md "📝 docs: add security policy note" <<'MD'
# Security policy
Lock accounts after repeated failed logins.
MD
  git push -q origin main
  git switch -q feat/account-lockout
}

# lower_branch: main에서 feat/count-login-failures를 만들어 push (쌓인 PR의 아래 PR)
lower_branch() {
  git switch -q -c feat/count-login-failures
  gk_commit src/auth/attempts.ts "✨ feat: count failed login attempts" <<'TS'
export const countFailures = (log: boolean[]) => log.filter((ok) => !ok).length;
TS
  gk_push feat/count-login-failures
}

# reflect_commit: 결정 대기 코드에 "잠금"을 반영해 커밋하고 push
reflect_commit() {
  gk_commit src/auth/lockout.ts "✨ feat: lock accounts after five failed logins" <<'TS'
const MAX_ATTEMPTS = 5;
export const shouldLock = (attempts: number) => attempts >= MAX_ATTEMPTS;
TS
  git push -q origin feat/account-lockout
}

# record_head [따온 브랜치]
record_head() {
  printf '%s\n' "따온 브랜치: ${1:-main}" '기록한 날: 2026-10-21'
}

# d1_block <상태> [답 덩어리 줄...]
d1_block() {
  local state="$1"; shift
  printf '%s\n' '' 'D1. 로그인 실패 시 계정을 잠글지' "상태: $state" '관련 파일: src/auth/lockout.ts' '' \
    '미결정 이유: 기획 문서에 기준 없음. 보안과 사용성 사이 제품 판단 필요.' '선택지:' \
    '- 잠금 (추천): 무차별 대입 방어. 오타 잦은 사용자는 불편.' \
    '- 잠그지 않음: 사용성 좋음. 방어는 지연 시간에 의존.'
  if [ $# -gt 0 ]; then printf '\n'; printf '%s\n' "$@"; fi
}

d2_block() {
  printf '%s\n' '' 'D2. 몇 회 실패에 잠글지' '상태: 대기' '의존: D1의 답이 잠금일 때만 필요' \
    '관련 파일: src/auth/lockout.ts' '' '미결정 이유: 보안 정책 기준 없음.' '선택지:' \
    '- 5회 (추천): 일반적인 기준. 무차별 대입 방어에 충분.' \
    '- 10회: 오타가 잦은 사용자에게 관대함. 방어력은 낮아짐.'
}

# d1_decided: 지금 HEAD를 결정 시점으로 D1을 "잠금"으로 결정한 블록 (reflect_commit 전에 부른다)
d1_decided() {
  d1_block 결정됨 '고른 답: 잠금' '답한 곳: PR 체크박스' '결정한 때: 2026-10-21T11:00+09:00' \
    "결정 시점: $(git rev-parse --short HEAD)"
}
