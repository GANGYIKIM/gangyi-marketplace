#!/bin/bash
# 가짜 원격 저장소(.git/fake-origin.git)를 https://github.com/test/demo.git 주소로 연결한다.
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
# 결정 대기 브랜치: 잠금 여부와 횟수가 정해지지 않은 임시 구현과, 결정 의존이 있는 결정 대기 기록(새 형식)을 만든다.
git switch -q -c feat/account-lockout
mkdir -p src/auth
cat > src/auth/lockout.ts <<'TS'
// TODO: 잠금 여부와 횟수 미정
const MAX_ATTEMPTS = 5;
export const shouldLock = (attempts: number) => attempts >= MAX_ATTEMPTS;
TS
git add src/auth/lockout.ts
git commit -q -m "✨ feat: add account lockout after failed logins"
printf '%s\n' \
  '따온 브랜치: main' \
  '기록한 날: 2026-10-21' \
  '' \
  'D1. 로그인 실패 시 계정을 잠글지' \
  '상태: 대기' \
  '' \
  '미결정 이유: 기획 문서에 기준 없음. 보안과 사용성 사이 제품 판단 필요.' \
  '선택지:' \
  '- 잠금 (추천): 무차별 대입 방어. 오타 잦은 사용자는 불편.' \
  '- 잠그지 않음: 사용성 좋음. 방어는 지연 시간에 의존.' \
  '' \
  'D2. 몇 회 실패에 잠글지' \
  '상태: 대기' \
  '의존: D1이 잠금일 때만 필요' \
  '' \
  '미결정 이유: 보안 정책 기준 없음.' \
  '선택지:' \
  '- 5회 (추천): 일반적인 기준. 무차별 대입 방어에 충분.' \
  '- 10회: 오타가 잦은 사용자에게 관대함. 방어력은 낮아짐.' \
  | git hash-object -w --stdin \
  | xargs git update-ref refs/git-kit/decisions/feat/account-lockout
