# git-kit

AI가 규칙대로 작업하며 git에 읽기 좋은 기록을 남기고, 사람은 PR에서 검토하도록 돕는 git 스킬 모음입니다.

## 스킬

| 스킬 | 설명 | 호출 |
|---|---|---|
| commit-writer | 변경사항을 주제별 커밋으로 나누고, Gitmoji와 Conventional Commits 타입을 붙인 영어 한 줄 메시지로 커밋합니다. 기본은 커밋마다 확인하고, `--auto`면 확인 없이 진행합니다 | `/git-kit:commit-writer` 또는 "커밋해줘" |

## 설치

```
/plugin install git-kit --marketplace GANGYIKIM/gangyi-marketplace
```

## 설정

저장소마다 `.claude/git-kit.local.md`로 기본 동작을 바꿀 수 있습니다. 개인 설정이니 `.gitignore`에 `.claude/*.local.md`를 넣어 두세요.

```markdown
---
allow-protected-commit: true   # 보호 브랜치(main 등)에서도 새 브랜치 없이 바로 커밋
protected-branches: [develop]  # main, master, 기본 브랜치 외에 보호할 브랜치
---
```

## 사용할 때 알아 둘 것

- AI가 작업 중에 커밋할 때는 프로젝트 `CLAUDE.md`에 "커밋은 `/git-kit:commit-writer --auto`로 한다"처럼 적어 두면 확인 없이 커밋합니다. push는 하지 않습니다.
- 결정이 필요한 변경은 별도 브랜치로 떼어내고, 그 기록을 git ref(`refs/git-kit/decisions/<브랜치>`)에 남깁니다. 원격에는 올라가지 않습니다. 목록은 `git for-each-ref refs/git-kit/decisions`로 볼 수 있습니다.
- commit-writer는 기본으로 커밋에 서명 줄(`Co-Authored-By` 등)을 붙이지 않습니다. 서명을 남기고 싶다면 `skills/commit-writer/SKILL.md`의 "3. 메시지 작성"에 있는 서명 규칙을 바꾸세요.

## 테스트

`evals/`에 [claude plugin eval](https://code.claude.com/docs/en/plugin-evals) 형식의 평가 케이스가 있습니다. 플러그인 폴더에서 실행합니다(사용량 차감).

```bash
claude plugin eval . --scaffold --allow-tools Bash
```

- `--scaffold`: 케이스마다 테스트용 git 저장소를 만듭니다.
- `--allow-tools Bash`: 커밋에 필요합니다.
- pre-commit hook 실패 처리는 평가 환경이 hook을 끄고 실행해서 확인할 수 없습니다. 실제 저장소에서 직접 확인하세요.
