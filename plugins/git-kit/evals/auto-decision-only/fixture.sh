#!/bin/bash
# 결정이 필요한 변경 하나만 있는 작업 브랜치를 만든다. 결정과 무관한 변경은 없다.
set -e
git init -q -b main
git config user.name "eval"
git config user.email "eval@example.com"
echo "# demo" > README.md
git add README.md
git commit -q -m "initial commit"
git switch -q -c feat/login-failure-tracking
mkdir -p src/auth
cat > src/auth/loginFailures.ts <<'TS'
// TODO: 잠금 기준 횟수 미정
export const MAX_LOGIN_FAILURES = 5;
export const shouldLock = (failures: number) => failures >= MAX_LOGIN_FAILURES;
TS
