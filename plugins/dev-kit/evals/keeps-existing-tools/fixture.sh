#!/bin/bash
# 화면이 없는 TypeScript CLI 프로젝트. 스택 파일의 추천과 다른 도구를 이미 쓴다.
# 린터와 포매터는 Biome, 테스트 도구는 Jest.
set -e
git init -q -b main
git config user.name "eval"
git config user.email "eval@example.com"
cat > package.json <<'JSON'
{
  "name": "log-parser",
  "version": "0.1.0",
  "private": true,
  "bin": { "log-parser": "dist/index.js" },
  "scripts": {
    "build": "tsc",
    "lint": "biome lint .",
    "format": "biome format --write .",
    "test": "jest"
  },
  "devDependencies": {
    "@biomejs/biome": "^2",
    "@types/jest": "^30",
    "jest": "^30",
    "ts-jest": "^29",
    "typescript": "^5"
  }
}
JSON
printf '{\n  "name": "log-parser",\n  "version": "0.1.0",\n  "lockfileVersion": 3,\n  "requires": true,\n  "packages": {}\n}\n' > package-lock.json
cat > biome.json <<'JSON'
{
  "formatter": { "enabled": true },
  "linter": {
    "enabled": true,
    "rules": { "recommended": true }
  }
}
JSON
printf '/** @type {import("jest").Config} */\nmodule.exports = {\n  preset: "ts-jest",\n  testEnvironment: "node",\n};\n' > jest.config.js
cat > tsconfig.json <<'JSON'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "strict": true,
    "outDir": "dist",
    "skipLibCheck": true
  },
  "include": ["src"]
}
JSON
mkdir -p src
printf 'export function sum(a: number, b: number): number {\n  return a + b;\n}\n' > src/sum.ts
printf 'import { sum } from "./sum";\n\nconsole.log(sum(1, 2));\n' > src/index.ts
printf 'node_modules\ndist\n' > .gitignore
printf 'import { sum } from "./sum";\n\ntest("sum", () => {\n  expect(sum(1, 2)).toBe(3);\n});\n' > src/sum.test.ts
git add . && git commit -q -m "initial commit"
# eval sandbox는 git 전역 설정으로 훅 경로를 /dev/null로 둔다. 보통 저장소처럼 보이게 기본 경로로 돌려놓는다.
git config core.hooksPath .git/hooks
