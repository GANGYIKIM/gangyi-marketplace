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
# 저장소 PR 템플릿을 main에 둔다.
mkdir -p .github
cat > .github/pull_request_template.md <<'MD'
## 변경 사항
<!-- 무엇을 왜 바꿨는지 적어 주세요 -->

## 스크린샷

## 체크리스트
- [ ] 테스트 추가
- [ ] 문서 수정
MD
git add .github/pull_request_template.md
git commit -q -m "chore: add pull request template"
git push -q origin main
git remote set-head origin main
# 작업 브랜치에 커밋 2개를 만든다.
git switch -q -c feat/add-greeting-util
mkdir -p src
printf 'export const greet = (name: string) => `Hello, ${name}`;\n' > src/greet.ts
git add src/greet.ts
git commit -q -m "✨ feat: add greeting util"
printf '\n## Usage\n\ngreet("Kim")\n' >> README.md
git add README.md
git commit -q -m "📝 docs: add greeting usage to readme"
printf 'import { greet } from "./greet";\ntest("greet", () => expect(greet("Kim")).toBe("Hello, Kim"));\n' > src/greet.test.ts
git add src/greet.test.ts
git commit -q -m "✅ test: add greeting util test"
