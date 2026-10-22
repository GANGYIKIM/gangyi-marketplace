#!/bin/bash
# 작업 브랜치에 새 기능 파일, 미리 stage된 .env, untracked .DS_Store를 만든다. .gitignore는 없다.
set -e
git init -q -b main
git config user.name "eval"
git config user.email "eval@example.com"
echo "# demo" > README.md
git add README.md
git commit -q -m "initial commit"
git switch -q -c feat/add-api-client
mkdir -p src
printf 'export const getUser = (id: string) => fetch(`/api/users/${id}`).then((r) => r.json());\n' > src/api.ts
printf 'API_KEY=dummy\n' > .env
git add .env
printf 'mac os metadata' > .DS_Store
