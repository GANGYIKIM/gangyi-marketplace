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
# main에 push 안 된 커밋 하나를 만든다.
printf 'export const greet = (name: string) => `Hello, ${name}`;\n' > greet.ts
git add greet.ts
git commit -q -m "✨ feat: add greeting util"
