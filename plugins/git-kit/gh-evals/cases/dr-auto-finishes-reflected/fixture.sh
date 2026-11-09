#!/bin/bash
set -e
source "$GK_CASE/../_shared/lockout.sh"
lockout_branch
decided=$(git rev-parse --short HEAD)
{ record_head; d1_block 결정됨 '고른 답: 잠금' '답한 곳: PR 체크박스' '결정한 때: 2026-10-21T11:00+09:00' "결정 시점: $decided"; } \
  | gk_record feat/account-lockout
gk_commit src/auth/lockout.ts "✨ feat: lock accounts after five failed logins" <<'TS'
const MAX_ATTEMPTS = 5;
export const shouldLock = (attempts: number) => attempts >= MAX_ATTEMPTS;
TS
git push -q origin feat/account-lockout
