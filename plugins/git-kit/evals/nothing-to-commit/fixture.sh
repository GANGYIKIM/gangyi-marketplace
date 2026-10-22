#!/bin/bash
# 변경이 하나도 없는 깨끗한 작업 브랜치를 만든다.
set -e
git init -q -b main
git config user.name "eval"
git config user.email "eval@example.com"
echo "# demo" > README.md
git add README.md
git commit -q -m "initial commit"
git switch -q -c feat/add-greeting-util
