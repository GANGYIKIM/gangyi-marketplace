#!/bin/bash
# 화면이 없는 TypeScript CLI 프로젝트. 패키지 매니저로 pnpm을 쓴다.
# 이 케이스는 pnpm이 깔려 있지 않은 컴퓨터를 전제로 한다.
set -e
git init -q -b main
git config user.name "eval"
git config user.email "eval@example.com"
cat > package.json <<'JSON'
{
  "name": "id-gen",
  "version": "0.1.0",
  "private": true,
  "packageManager": "pnpm@10.0.0",
  "bin": { "id-gen": "dist/index.js" },
  "scripts": {
    "build": "tsc"
  },
  "devDependencies": {
    "typescript": "^5"
  }
}
JSON
printf "lockfileVersion: '9.0'\n\nsettings:\n  autoInstallPeers: true\n  excludeLinksFromLockfile: false\n\nimporters:\n\n  .:\n    devDependencies:\n      typescript:\n        specifier: ^5\n        version: 5.9.3\n" > pnpm-lock.yaml
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
printf 'export function makeId(prefix: string, n: number): string {\n  return `${prefix}-${n}`;\n}\n' > src/id.ts
printf 'import { makeId } from "./id";\n\nconsole.log(makeId("id", 1));\n' > src/index.ts
printf 'node_modules\ndist\n' > .gitignore
git add . && git commit -q -m "initial commit"
# eval sandbox는 git 전역 설정으로 훅 경로를 /dev/null로 둔다. 보통 저장소처럼 보이게 기본 경로로 돌려놓는다.
git config core.hooksPath .git/hooks
