#!/bin/bash
# 화면이 없는 TypeScript CLI 프로젝트. 셋업의 설정을 모두 갖췄다.
# 패키지는 설치돼 있지 않다(eval sandbox에 네트워크가 없어 node_modules를 만들 수 없다).
set -e
git init -q -b main
git config user.name "eval"
git config user.email "eval@example.com"
cat > package.json <<'JSON'
{
  "name": "csv-tool",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "bin": { "csv-tool": "dist/index.js" },
  "scripts": {
    "build": "tsc -p tsconfig.build.json",
    "lint": "eslint",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "format": "prettier --write .",
    "prepare": "husky"
  },
  "devDependencies": {
    "@eslint/js": "^9",
    "@types/node": "^22",
    "eslint": "^9",
    "eslint-config-prettier": "^10",
    "husky": "^9",
    "lint-staged": "^16",
    "prettier": "^3",
    "typescript": "^5",
    "typescript-eslint": "^8",
    "vitest": "^4"
  }
}
JSON
printf '{\n  "name": "csv-tool",\n  "version": "0.1.0",\n  "lockfileVersion": 3,\n  "requires": true,\n  "packages": {}\n}\n' > package-lock.json
cat > tsconfig.json <<'JSON'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "nodenext",
    "moduleResolution": "nodenext",
    "strict": true,
    "noEmit": true,
    "skipLibCheck": true
  },
  "include": ["src", "*.ts", "*.mjs"]
}
JSON
printf '{\n  "extends": "./tsconfig.json",\n  "compilerOptions": { "noEmit": false, "outDir": "dist" },\n  "include": ["src"],\n  "exclude": ["src/**/*.test.ts"]\n}\n' > tsconfig.build.json
cat > eslint.config.js <<'JS'
import js from "@eslint/js";
import prettier from "eslint-config-prettier/flat";
import { defineConfig, globalIgnores } from "eslint/config";
import tseslint from "typescript-eslint";

export default defineConfig([
  js.configs.recommended,
  ...tseslint.configs.recommended,
  prettier,
  globalIgnores(["dist/**"]),
]);
JS
printf '{}\n' > .prettierrc.json
printf 'import { defineConfig } from "vitest/config";\n\nexport default defineConfig({\n  test: { environment: "node" },\n});\n' > vitest.config.ts
cat > lint-staged.config.mjs <<'JS'
export default {
  "*.{js,mjs,cjs,ts}": [
    "prettier --write",
    "eslint --no-warn-ignored",
    () => "tsc --noEmit",
    "vitest related --run --passWithNoTests",
  ],
  "*.{json,md,yml,yaml}": "prettier --write",
};
JS
mkdir -p src
printf 'export function sum(a: number, b: number): number {\n  return a + b;\n}\n' > src/sum.ts
printf 'import { sum } from "./sum.js";\n\nconsole.log(sum(1, 2));\n' > src/index.ts
printf 'node_modules\ndist\n' > .gitignore
printf 'import { expect, test } from "vitest";\nimport { sum } from "./sum.js";\n\ntest("sum", () => {\n  expect(sum(1, 2)).toBe(3);\n});\n' > src/sum.test.ts

# husky가 설치한 것과 같은 모양
mkdir -p .husky/_
printf 'npx lint-staged\n' > .husky/pre-commit
printf '*\n' > .husky/_/.gitignore
printf '#!/usr/bin/env sh\n. "$(dirname "$0")/h"\n' > .husky/_/pre-commit
printf '#!/usr/bin/env sh\nn=$(basename "$0")\ns=$(dirname "$(dirname "$0")")/$n\n[ ! -f "$s" ] && exit 0\nexport PATH="node_modules/.bin:$PATH"\nsh -e "$s" "$@"\n' > .husky/_/h
chmod +x .husky/_/pre-commit

# Claude 설정: 건너뛰는 커밋을 막는 훅과 검사 설정 보호
mkdir -p .claude/hooks
cp "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/skills/harness-builder/assets/block-hook-bypass.mjs" .claude/hooks/block-hook-bypass.mjs
cat > .claude/settings.json <<'JSON'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "node \"$CLAUDE_PROJECT_DIR/.claude/hooks/block-hook-bypass.mjs\""
          }
        ]
      }
    ]
  },
  "permissions": {
    "ask": [
      "Edit(/eslint.config.*)",
      "Edit(/.prettierrc*)",
      "Edit(/prettier.config.*)",
      "Edit(/tsconfig*.json)",
      "Edit(/vitest.config.*)",
      "Edit(/lint-staged.config.*)",
      "Edit(/.husky/**)",
      "Edit(/.claude/settings.json)",
      "Edit(/.claude/hooks/**)"
    ]
  }
}
JSON
git add . && git commit -q -m "initial commit"
# 훅 경로는 첫 커밋 뒤에 건다. 먼저 걸면 이 커밋에서 커밋 전 검사가 돌아 패키지를 내려받으려 한다.
git config core.hooksPath .husky/_
