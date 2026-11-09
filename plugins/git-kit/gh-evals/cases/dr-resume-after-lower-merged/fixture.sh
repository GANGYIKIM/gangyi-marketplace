#!/bin/bash
set -e
source "$GK_CASE/../_shared/lockout.sh"
gk_init_repo
lower_branch
lockout_commit
reflect_commit
# 아래 PR(#1)이 main에 머지됨
git switch -q main
git merge -q --no-ff feat/count-login-failures -m "Merge pull request #1 from test/feat/count-login-failures"
git push -q origin main
# 다른 컴퓨터: main만 받은 상태. 결정 기록 없음
git branch -q -D feat/account-lockout feat/count-login-failures
