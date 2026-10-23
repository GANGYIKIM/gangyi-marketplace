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
# 커밋이 없는 작업 브랜치를 만든다.
git switch -q -c feat/add-greeting-util
