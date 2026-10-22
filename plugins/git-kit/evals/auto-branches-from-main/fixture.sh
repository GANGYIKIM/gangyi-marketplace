#!/bin/bash
# main 브랜치에 커밋 안 된 변경 하나가 있는 git 저장소를 만든다.
set -e
git init -q -b main
git config user.name "eval"
git config user.email "eval@example.com"
echo "# demo" > README.md
git add README.md
git commit -q -m "initial commit"
mkdir -p src
printf 'export const greet = (name: string) => `Hello, ${name}`;\n' > src/greet.ts
