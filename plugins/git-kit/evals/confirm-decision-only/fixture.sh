#!/bin/bash
# 이메일 검증이 이미 커밋된 작업 브랜치에, 결정이 필요한 계정 잠금 로직만 커밋 안 된 채로 둔다. 원격은 없다(push 전).
set -e
git init -q -b main
git config user.name "eval"
git config user.email "eval@example.com"
printf '# demo\n' > README.md
git add README.md
git commit -q -m "initial commit"
git switch -q -c feat/login-lockout
mkdir -p src/auth
printf 'export const validateEmail = (email: string) => /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(email);\n' > src/auth/validateEmail.ts
git add src/auth/validateEmail.ts
git commit -q -m "✨ feat: add email validation"
cat > src/auth/lockout.ts <<'TS'
import { validateEmail } from "./validateEmail";
// TODO: 잠금 횟수 미정
const MAX_ATTEMPTS = 5;
export const shouldLock = (email: string, attempts: number) => validateEmail(email) && attempts >= MAX_ATTEMPTS;
TS
