#!/bin/bash
# 커밋할 변경 하나가 있는 작업 브랜치를 만든다.
set -e
git init -q -b main
git config user.name "eval"
git config user.email "eval@example.com"
echo "# demo" > README.md
git add README.md
git commit -q -m "initial commit"
git switch -q -c feat/add-greeting-util
mkdir -p src
printf 'export const greet = (name: string) => `Hello, ${name}`;\n' > src/greet.ts
