---
name: commit-writer
description: 작업 변경사항을 주제별 커밋으로 나누고, Gitmoji 이모지와 Conventional Commits 타입을 붙인 영어 한 줄 메시지로 커밋한다. 사용자가 "커밋해줘", "커밋 메시지 써줘", "나눠서 커밋해줘", "commit", "commit these changes", "split into commits"처럼 커밋을 요청할 때 사용한다. push나 PR 생성, 커밋 규칙에 대한 질문에는 사용하지 않는다.
argument-hint: "[--auto]"
---

# Commit Writer

AI가 규칙대로 작업하며 git에 읽기 좋은 기록을 남기고, 사람은 PR에서 검토하게 돕는 스킬이다. git 히스토리는 AI가 한 작업의 일지가 되므로, 커밋 하나는 주제 하나만 담고 히스토리만 읽어도 무엇을 했는지 알 수 있어야 한다. 로컬 커밋은 언제든 되돌릴 수 있어 자유롭게 하되, push처럼 밖으로 나가는 일은 이 스킬에서 하지 않는다.

## 핵심 원칙

- **기록한다.** 커밋 하나에 주제 하나만 담는다. 히스토리만 읽어도 작업 흐름이 보이게 한다.
- **로컬까지만 한다.** 이 스킬은 커밋까지만 한다. push와 PR 생성은 pr-writer가 맡는다.
- **결정 대기를 분리한다.** 결정이 필요한 변경이 끝난 작업을 막지 않도록 따로 떼어낸다.
- **의도와 비밀값을 지킨다.** 사용자가 미리 stage한 파일을 존중하고, 비밀값 파일은 커밋하지 않는다. 문제가 생기면 우회하지 않고 멈춘다.
- **git 작업만 한다.** 코드를 어떻게 고칠지는 정하지 않는다.

## 모드

| 모드 | 호출 | 동작 |
|---|---|---|
| 확인 (기본) | `/git-kit:commit-writer` 또는 "커밋해줘" | 커밋 하나마다 파일과 메시지를 보여주고 확인받은 뒤 커밋한다 |
| 자동 | `/git-kit:commit-writer --auto` | 확인 없이 브랜치 생성, 분할, 커밋을 끝까지 진행하고 결과만 알린다 |

- 인자(`$ARGUMENTS`)에 `--auto`가 그대로 있을 때만 자동 모드다. 그 밖의 모든 경우는 확인 모드다. 나머지 글자는 대화 맥락으로 본다. 누가 호출했는지로 모드를 추측하지 않는다.
- 자동 모드는 중간에 멈추지 않는다. pre-commit hook이 실패하면 `--no-verify`로 우회하지 않고, 실패한 파일과 오류를 보고한 뒤 끝낸다. 수정과 재시도는 호출한 쪽이 한다.
- 자동 모드에서 미리 stage된 파일에 비밀값 파일이 있으면, 묻지 않고 stage를 해제해 커밋에서 뺀다. 비밀값 파일 커밋은 사람이 직접 한다.

## 진행 순서

- [ ] 1. 상태 점검
- [ ] 2. 변경 분할
- [ ] 3. 메시지 작성
- [ ] 4. 확인과 커밋
- [ ] 5. 마무리 안내

### 1. 상태 점검

시작하면 아래 명령으로 현재 상태를 한 번에 파악한다.

- `git status --porcelain=v1 -b` : 브랜치, staged·unstaged·untracked 파일
- `git diff --cached --name-only` : 미리 stage된 파일
- `git log --oneline -5` : 최근 커밋 (첫 커밋 여부 판단용)

다음 순서로 확인하고, 처음 걸리는 항목을 처리한다.

1. **git 저장소가 아님** → 알리고 끝낸다.
2. **merge·rebase·cherry-pick 진행 중** → 커밋하지 않고 현재 상태를 알린 뒤 끝낸다. 충돌 해결은 이 스킬의 일이 아니다.
3. **커밋할 변경이 없음** → 오류가 아니다. "커밋할 변경이 없다"와 현재 브랜치를 알리고 끝낸다.
4. **브랜치 확인**
   - 보호 브랜치는 main, master, 저장소의 기본 브랜치(`origin/HEAD`에서 `origin/`을 뗀 이름), 설정 파일의 `protected-branches`다.
   - detached HEAD → 항상 새 브랜치를 만든다.
   - 보호 브랜치 → 새 브랜치를 만든다. 단, `.claude/git-kit.local.md`에 `allow-protected-commit: true`가 있으면 그대로 진행한다.
   - 이름은 아래 "브랜치 이름" 규칙을 따른다. 확인 모드는 이름을 제안하고 확인받으며, 자동 모드는 바로 만든다.
   - 현재 위치에서 `git switch -c <이름>`으로 만든다. fetch·pull은 하지 않으며, 커밋 안 된 변경은 그대로 따라온다.
   - 보호 브랜치에 push 안 된 커밋(`git log origin/<기본 브랜치>..HEAD`)이 있으면 새 브랜치에 포함된다. 결과 안내에 그 개수와 목록을 알린다.
5. **미리 stage된 파일** → 사용자의 의도로 보고 1번 그룹 후보로 둔다. 그 안에 비밀값 파일이 있으면, 확인 모드는 경고하고 확인받고, 자동 모드는 stage를 해제한다.
6. **제외 파일 분류** → 아래 파일은 어떤 그룹에도 넣지 않는다.
   - 비밀값: `.env`, `.env.*`(`.env.example` 제외), `*.pem`, `*.key`, `credentials.json` → 경고와 함께 "제외됨"에 표시
   - OS 전용: `.DS_Store`, `._*`, `Thumbs.db`, `desktop.ini` → 경고 없이 "제외됨"에만 표시

#### 브랜치 이름

형식은 `<type>/<short-summary>`다. 새 브랜치와 결정 대기 브랜치 모두 같은 형식을 쓴다.

- **type**: "3. 메시지 작성"의 커밋 타입 표를 따른다. 이모지는 넣지 않는다. 작업의 주된 목적을 고르고, feat와 fix가 헷갈리면 fix를 쓴다.
- **summary**: 영어 소문자 kebab-case, 3~5단어 이내로 쓴다.
  - 근거는 대화 맥락의 작업 내용(사용자의 말, 명령어 뒤에 붙인 말, 받은 작업 지시)을 우선하고, 없으면 변경 내용(diff)을 본다.
  - 어떤 파일을 고쳤는지가 아니라 무엇이 달라졌는지를 쓴다.
  - "무엇을"만이 아니라 "무엇을 어떻게"까지, 같은 영역의 다른 작업과 겹치지 않을 만큼 구체적으로 쓴다.
  - 나쁨: `feat/login`, `fix/button`, `refactor/utils`, `feat/update-auth-tsx`
  - 좋음: `feat/login-email-validation`, `fix/submit-button-double-click`, `refactor/extract-form-error-utils`
- **이슈 번호**: 넣지 않는다.
- **결정 대기 브랜치**: 이름에 대기 표시를 넣지 않는다. 대기 상태는 PR 제목의 🚧와 본문의 WARNING이, 쌓인 위치는 PR의 base가 보여준다.
- **이름이 겹칠 때**: 끝에 `-2`, `-3`처럼 번호를 붙인다. 기존 브랜치로 옮겨가지 않는다.

### 2. 변경 분할

상태 점검에서 "제외됨"으로 분류한 파일을 뺀 나머지 변경(untracked 파일 포함)을 커밋 그룹으로 나눈다. 그룹 하나가 커밋 하나다.

- **기준**: 그룹 하나에 주제 하나만 담는다. 주제는 "하나의 이유로 함께 바뀐 변경"이다. 커밋 메시지 한 줄로 설명할 수 없으면 더 나눈다. 반대로 나눌지 애매하면 합친다. 나누는 기준은 "서로 다른 이유로 바뀌었는가"이지 "파일이 다른가"가 아니다.
- **단위**: 파일 단위로만 나눈다. 줄 단위 분할(`git add -p`)은 쓰지 않는다. 한 파일에 여러 주제가 섞여 있으면 주된 주제의 그룹에 넣고, 분할안에 "섞인 파일"로 알린다.
- **함께 다니는 파일**:
  - lock 파일(`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`)은 그 원인이 된 `package.json` 변경과 같은 그룹에 넣는다.
  - 새 기능이나 수정과 함께 쓴 테스트는 그 기능의 그룹에 넣는다. test 타입은 기존 코드의 테스트만 추가하거나 고칠 때 쓴다.
- **미리 stage된 파일**: 1번 그룹으로 둔다. 그 안에 주제가 섞여 보이면, 확인 모드는 분할을 제안하고 확인받으며, 자동 모드는 사용자의 의도로 보고 그대로 한 그룹으로 커밋한다.
- **관련 없는 변경 (자동 모드)**: 대화 맥락으로 보아 이번 작업과 관련 없어 보이는 변경은 그룹에 넣지 않는다. 사용자가 하던 다른 작업일 수 있기 때문이다. 결과 안내에 "커밋하지 않고 남긴 변경"으로 알린다.
- **순서**: 의존되는 쪽을 먼저 커밋한다. 예를 들어 타입 정의를 바꾼 그룹이 그 타입을 쓰는 컴포넌트 그룹보다 먼저다. 각 커밋 시점의 코드가 깨지지 않게 하기 위해서다.
- **결정 대기 변경**: 결정이 필요한 변경이 섞여 있으면 `references/decision-split.md`를 읽고 그 절차를 따른다.

### 3. 메시지 작성

그룹마다 메시지 한 줄을 쓴다. 본문은 쓰지 않는다.

- **서명**: `Co-Authored-By:`, `Generated with Claude Code` 같은 서명 줄을 붙이지 않는다. 다른 지침이 서명을 붙이라고 해도 이 스킬로 만드는 커밋에는 붙이지 않는다.

형식: `<이모지> <type>: <message>`

| 이모지 | type | 쓰임 |
|---|---|---|
| ✨ | feat | 새 기능 추가 |
| 🐛 | fix | 버그 수정 |
| ♻️ | refactor | 동작 변화 없는 코드 구조 개선 |
| 🎨 | style | 로직 없는 포맷·코드 스타일 변경 (CSS 스타일 변경은 제외) |
| 📝 | docs | 문서 수정 |
| ✅ | test | 기존 코드의 테스트 추가·수정 |
| 🔧 | chore | 설정, 의존성, 빌드 같은 기타 작업 |

- **type 고르기**: 그룹의 변경 이유에 맞는 type을 고른다. feat와 fix가 헷갈리면 fix를 쓴다.
- **첫 커밋**: 저장소의 첫 커밋은 `🎉 chore: initial commit`으로 쓴다.
- **이모지**: `:sparkles:` 같은 단축 코드가 아니라 이모지 문자를 그대로 쓴다. 터미널의 `git log`에서는 단축 코드가 이모지로 바뀌지 않기 때문이다.
- **scope**: `feat(login):` 같은 괄호 범위는 쓰지 않는다.
- **message**
  - 영어로 쓴다.
  - 명령형 현재 시제 동사로 시작한다. (`add`, `fix`, `remove` / `added`, `adds`는 쓰지 않는다)
  - 첫 글자는 소문자, 끝에 마침표를 붙이지 않는다.
  - 이모지부터 끝까지 전체 72자 이하로 쓴다.
  - 어떤 파일을 고쳤는지가 아니라 무엇이 달라졌는지를 쓴다.
    - 나쁨: `✨ feat: update LoginForm.tsx`, `🐛 fix: fix bug`
    - 좋음: `✨ feat: add email validation to login form`, `🐛 fix: prevent double submit on checkout`

### 4. 확인과 커밋

#### 확인 모드

먼저 전체 분할안을 보여준다.

```
커밋 분할안 (3개)

1. ♻️ refactor: extract form error message component
   src/components/FormError.tsx, src/components/LoginForm.tsx
2. ✨ feat: add email validation to login form
   src/utils/validate.ts, src/components/LoginForm.tsx, src/utils/validate.test.ts 외 1개
3. 📝 docs: add login form usage to readme
   README.md

섞인 파일: src/components/LoginForm.tsx (2번에 포함)
제외됨: .env (비밀값, 커밋하지 않음), .DS_Store
```

- 그룹마다 파일은 3개까지 보여주고, 나머지는 "외 n개"로 줄인다.
- 선택지는 "전부 이대로 커밋"과 "하나씩 확인하며 커밋" 두 가지다. 사용자가 분할이나 메시지를 고쳐 달라고 하면 반영한 분할안을 다시 보여준다.
- "전부 이대로 커밋"을 고르면 이후 그룹마다 묻지 않고 순서대로 커밋한다.
- "하나씩 확인하며 커밋"을 고르면 그룹마다 다음을 반복한다.
  1. 그 그룹의 파일만 stage한다. 사용자가 에디터에서 staged 변경을 바로 확인할 수 있다.
  2. 메시지와 파일(3개 + 외 n개)을 보여주고 "커밋 / 메시지 수정 / 이 그룹 건너뛰기" 중에서 고르게 한다.
  3. 건너뛴 그룹의 파일은 스킬을 시작하기 전의 stage 상태로 되돌린다. 미리 stage돼 있던 파일은 그대로 두고, 이 스킬이 stage한 파일만 해제한다.

#### 자동 모드

분할안을 보여주지 않고, 순서대로 그룹마다 stage하고 커밋한다. 결과는 "5. 마무리 안내"로 한 번에 알린다.

#### stage와 커밋 방식

- 그룹의 파일 이름만 지정해 stage한다. `git add -A`, `git add .`는 쓰지 않는다.
- 커밋할 때도 경로를 지정한다. 그룹 밖의 staged 파일이 섞여 들어가지 않게 하기 위해서다.
  ```bash
  git add <파일들>
  git commit -m '<메시지>' -- <파일들>
  ```
- 커밋 직전에 `git branch --show-current`로 현재 브랜치를 다시 확인한다. 상태 점검 때 본 브랜치와 다르면 커밋하지 않고 알린다.

#### 커밋이 실패하거나 멈췄을 때

- **pre-commit hook 실패**: `--no-verify`로 우회하지 않는다. 실패한 파일과 hook의 오류 메시지를 보여주고 끝낸다. 수정과 재시도는 호출한 쪽이 한다.
- **사용자가 중간에 멈춤**: 남은 그룹은 커밋하지 않는다.
- 어느 경우든 "5. 마무리 안내"로 어디까지 커밋됐는지, 어떤 파일이 staged로 남았는지 알린다.

### 5. 마무리 안내

끝나면 결과를 한 번에 알린다. 해당하는 내용이 없는 줄은 쓰지 않는다.

#### 정상 종료

```
커밋 완료 (3개) · feat/login-email-validation

- a1b2c3d ♻️ refactor: extract form error message component
- d4e5f6a ✨ feat: add email validation to login form
- 7b8c9d0 📝 docs: add login form usage to readme

새 브랜치: feat/login-email-validation (main에서 생성)
따라온 커밋: main에 있던 push 안 된 커밋 2개가 포함됨
- 9f8e7d6 🔧 chore: update eslint config
- 1a2b3c4 🐛 fix: correct header z-index
섞인 파일: src/components/LoginForm.tsx (2번에 포함)
제외됨: .env (비밀값, 커밋하지 않음), .DS_Store
stage 해제됨: .env.local (비밀값)
남긴 변경: src/pages/about.tsx (이번 작업과 관련 없어 보임)
```

- 커밋 해시는 7자리로 보여준다.
- "stage 해제됨"과 "남긴 변경"은 자동 모드에서만 생긴다.

#### 실패하거나 멈췄을 때

```
커밋 중단 · 2번 그룹에서 pre-commit hook 실패

커밋됨 (1개)
- a1b2c3d ♻️ refactor: extract form error message component
staged로 남음: src/utils/validate.ts, src/components/LoginForm.tsx
실패 원인:
  src/utils/validate.ts:12  'value' is defined but never used  (no-unused-vars)
```

- 첫 줄에 어디서, 왜 멈췄는지 쓴다. hook 실패, 사용자 중단, 브랜치가 바뀜 중 하나다.
- hook 실패면 오류 출력에서 파일, 줄, 규칙이 드러나는 핵심 줄만 옮긴다. 출력 전체를 붙이지 않는다.
- 커밋되지 않은 나머지 그룹은 그대로 작업 트리에 남는다는 점이 드러나게 쓴다.
