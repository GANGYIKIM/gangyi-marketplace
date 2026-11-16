#!/bin/bash
# create-next-app이 만든 것과 비슷한 Next.js 프로젝트. 셋업은 아직 안 했다.
# 있는 것: ESLint 기본 설정, tsconfig strict, Tailwind
# 없는 것: 포매터, 테스트 도구, 커밋 전 검사, 컴포넌트·데이터 자리, Claude 설정
set -e
git init -q -b main
git config user.name "eval"
git config user.email "eval@example.com"
cat > package.json <<'JSON'
{
  "name": "shop-front",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint"
  },
  "dependencies": {
    "next": "16.2.4",
    "react": "19.2.4",
    "react-dom": "19.2.4"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4",
    "@types/node": "^20",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "eslint": "^9",
    "eslint-config-next": "16.2.4",
    "tailwindcss": "^4",
    "typescript": "^5"
  }
}
JSON
printf '{\n  "name": "shop-front",\n  "version": "0.1.0",\n  "lockfileVersion": 3,\n  "requires": true,\n  "packages": {}\n}\n' > package-lock.json
cat > tsconfig.json <<'JSON'
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "react-jsx",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
JSON
cat > eslint.config.mjs <<'JS'
import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts"]),
]);

export default eslintConfig;
JS
printf 'import type { NextConfig } from "next";\n\nconst nextConfig: NextConfig = {};\n\nexport default nextConfig;\n' > next.config.ts
printf 'const config = {\n  plugins: {\n    "@tailwindcss/postcss": {},\n  },\n};\n\nexport default config;\n' > postcss.config.mjs
printf 'node_modules\n.next\nout\nnext-env.d.ts\n' > .gitignore
mkdir -p app
printf '@import "tailwindcss";\n' > app/globals.css
cat > app/layout.tsx <<'TSX'
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = { title: "Shop" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
TSX
cat > app/page.tsx <<'TSX'
export default function Home() {
  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold">Shop</h1>
    </main>
  );
}
TSX
git add . && git commit -q -m "initial commit"
# eval sandbox는 git 전역 설정으로 훅 경로를 /dev/null로 둔다. 보통 저장소처럼 보이게 기본 경로로 돌려놓는다.
git config core.hooksPath .git/hooks
