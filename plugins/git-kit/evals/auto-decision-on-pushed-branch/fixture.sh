#!/bin/bash
# 가짜 원격 저장소(.git/fake-origin.git)에 이미 push한 작업 브랜치를 만든다. 결정 기록은 없다.
set -e
git init -q -b main
git config user.name "eval"
git config user.email "eval@example.com"
echo "# demo" > README.md
git add README.md
git commit -q -m "initial commit"
git init -q --bare .git/fake-origin.git
git remote add origin https://github.com/test/demo.git
git config url."$PWD/.git/fake-origin.git".insteadOf https://github.com/test/demo.git
git push -q origin main
git remote set-head origin main
git switch -q -c feat/login-failure-tracking
mkdir -p src/auth
cat > src/auth/loginFailures.ts <<'TS'
const failures = new Map<string, number>();
export const recordFailure = (email: string) => failures.set(email, (failures.get(email) ?? 0) + 1);
export const getFailures = (email: string) => failures.get(email) ?? 0;
TS
git add src/auth/loginFailures.ts
git commit -q -m "✨ feat: track failed login attempts per email"
git push -q -u origin feat/login-failure-tracking
# push 뒤에 결정이 필요한 변경만 생긴다.
cat > src/auth/lockout.ts <<'TS'
import { getFailures } from "./loginFailures";
// TODO: 잠금 기준 횟수 미정
export const MAX_LOGIN_FAILURES = 5;
export const isLocked = (email: string) => getFailures(email) >= MAX_LOGIN_FAILURES;
TS
