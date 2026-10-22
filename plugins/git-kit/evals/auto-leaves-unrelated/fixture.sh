#!/bin/bash
# 작업 대상인 새 UserCard와, 관련 없는 About 페이지 문구 변경이 섞인 작업 브랜치를 만든다.
set -e
git init -q -b main
git config user.name "eval"
git config user.email "eval@example.com"
mkdir -p src/pages
echo "# demo" > README.md
printf 'export const About = () => <p>We build tools.</p>;\n' > src/pages/About.tsx
git add . && git commit -q -m "initial commit"
git switch -q -c feat/add-user-card
mkdir -p src/components
printf 'export const UserCard = ({ name }: { name: string }) => <div>{name}</div>;\n' > src/components/UserCard.tsx
printf 'export const About = () => <p>We build friendly tools for small teams.</p>;\n' > src/pages/About.tsx
