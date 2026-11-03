#!/bin/bash
# 완료된 이메일 검증, 결정이 필요한 계정 잠금 로직, 관계없는 README 오타 수정이 섞인 작업 브랜치를 만든다.
set -e
git init -q -b main
git config user.name "eval"
git config user.email "eval@example.com"
printf '# demo\n\n## Instalation\n\nnpm install\n' > README.md
git add README.md
git commit -q -m "initial commit"
git switch -q -c feat/login-email-validation
mkdir -p src/auth
printf 'export const validateEmail = (email: string) => /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(email);\n' > src/auth/validateEmail.ts
cat > src/auth/lockout.ts <<'TS'
import { validateEmail } from "./validateEmail";
// TODO: 잠금 횟수 미정
const MAX_ATTEMPTS = 5;
export const shouldLock = (email: string, attempts: number) => validateEmail(email) && attempts >= MAX_ATTEMPTS;
TS
sed -i.bak 's/Instalation/Installation/' README.md && rm README.md.bak
