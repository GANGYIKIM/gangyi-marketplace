#!/bin/bash
# 작업 브랜치에서 이름이 같은 두 파일(api/README.md, web/README.md)을 한 주제로 고친 git 저장소를 만든다.
set -e
git init -q -b main
git config user.name "eval"
git config user.email "eval@example.com"
mkdir -p api web
printf '# api\n\nRun with `npm start`.\n' > api/README.md
printf '# web\n\nRun with `npm start`.\n' > web/README.md
git add . && git commit -q -m "initial commit"
git switch -q -c docs/document-dev-port
printf '# api\n\nRun with `npm start`. The server listens on port 3000.\n' > api/README.md
printf '# web\n\nRun with `npm start`. The dev server listens on port 5173.\n' > web/README.md
