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
# 작업 브랜치: greet 유틸과 테스트 스크립트, 결과값이 적힌 README 사용법 예시
git switch -q -c feat/add-greeting-util
mkdir -p src
printf 'export const greet = (name: string) => `Hello, ${name}`;\n' > src/greet.ts
cat > test.sh <<'SH'
#!/bin/sh
# greet가 "Hello, <이름>"을 돌려주는지 확인한다.
if grep -q 'Hello, ${name}' src/greet.ts; then echo "1 passed"; else echo "1 failed"; exit 1; fi
SH
chmod +x test.sh
git add src/greet.ts test.sh
git commit -q -m "✨ feat: add greeting util"
cat >> README.md <<'MD'

## Usage

```ts
greet("Kim") // "Hello, Kim"
```
MD
git add README.md
git commit -q -m "📝 docs: add greeting usage to readme"
