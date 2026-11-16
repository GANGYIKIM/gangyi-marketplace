#!/bin/bash
# 화면이 없는 TypeScript 라이브러리. tsconfig에 엄격 모드를 꺼 둔 줄이 있다.
set -e
git init -q -b main
git config user.name "eval"
git config user.email "eval@example.com"
cat > package.json <<'JSON'
{
  "name": "price-lib",
  "version": "0.1.0",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc"
  },
  "devDependencies": {
    "typescript": "^5"
  }
}
JSON
printf '{\n  "name": "price-lib",\n  "version": "0.1.0",\n  "lockfileVersion": 3,\n  "requires": true,\n  "packages": {}\n}\n' > package-lock.json
cat > tsconfig.json <<'JSON'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "nodenext",
    "moduleResolution": "nodenext",
    "strict": false,
    "outDir": "dist",
    "skipLibCheck": true
  },
  "include": ["src"]
}
JSON
mkdir -p src
printf 'export function sum(a: number, b: number): number {\n  return a + b;\n}\n' > src/sum.ts
printf 'import { sum } from "./sum.js";\n\nconsole.log(sum(1, 2));\n' > src/index.ts
printf 'node_modules\ndist\n' > .gitignore
git add . && git commit -q -m "initial commit"
# eval sandbox는 git 전역 설정으로 훅 경로를 /dev/null로 둔다. 보통 저장소처럼 보이게 기본 경로로 돌려놓는다.
git config core.hooksPath .git/hooks
