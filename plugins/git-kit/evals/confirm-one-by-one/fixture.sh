#!/bin/bash
# 작업 브랜치에 서로 관계없는 두 주제의 변경을 만든다.
# - feat: 새 greet 유틸
# - docs: README 오타 수정
set -e
git init -q -b main
git config user.name "eval"
git config user.email "eval@example.com"
printf '# demo\n\n## Instalation\n\nnpm install\n' > README.md
git add README.md && git commit -q -m "initial commit"
git switch -q -c feat/add-greeting-util
mkdir -p src
printf 'export const greet = (name: string) => `Hello, ${name}`;\n' > src/greet.ts
sed -i.bak 's/Instalation/Installation/' README.md && rm README.md.bak
