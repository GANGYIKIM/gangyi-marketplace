# git-kit

AI가 규칙대로 작업하며 git에 읽기 좋은 기록을 남기고, 사람은 PR에서 검토하도록 돕는 git 스킬 모음입니다.

## 스킬

| 스킬 | 설명 | 호출 |
|---|---|---|
| commit-writer | 변경사항을 주제별 커밋으로 나누고, Gitmoji와 Conventional Commits 타입을 붙인 영어 한 줄 메시지로 커밋합니다. 기본은 커밋마다 확인하고, `--auto`면 확인 없이 진행합니다 | `/git-kit:commit-writer` 또는 "커밋해줘" |
| pr-writer | 브랜치의 커밋 전체로 PR 제목과 본문을 쓰고, AI가 판단한 것과 사람이 확인할 것을 PR 첫 코멘트에 보고서로 남깁니다. 기본은 push 전에 한 번 확인하고, `--auto`면 확인 없이 push하고 Draft PR로 만듭니다 | `/git-kit:pr-writer` 또는 "PR 만들어줘" |

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

### commit-writer

- AI가 작업 중에 커밋할 때는 프로젝트 `CLAUDE.md`에 "커밋은 `/git-kit:commit-writer --auto`로 한다"처럼 적어 두면 확인 없이 커밋합니다. push는 하지 않습니다.
- 결정이 필요한 변경은 별도 브랜치로 떼어내고, 그 기록을 git ref(`refs/git-kit/decisions/<브랜치>`)에 남깁니다. 원격에는 올라가지 않습니다. 목록은 `git for-each-ref refs/git-kit/decisions`로 볼 수 있습니다.
- commit-writer는 기본으로 커밋에 서명 줄(`Co-Authored-By` 등)을 붙이지 않습니다. 서명을 남기고 싶다면 `skills/commit-writer/SKILL.md`의 "3. 메시지 작성"에 있는 서명 규칙을 바꾸세요.

### pr-writer

- GitHub에는 gh CLI → GitHub MCP 순서로 접근합니다. 둘 다 없으면 push한 뒤 PR 만들기 링크와 제목, 본문, 보고서 코멘트를 복사할 수 있게 보여줍니다. gh 설치와 로그인(`gh auth login`)이나 [GitHub MCP](https://github.com/github/github-mcp-server) 연결을 추천합니다.
- PR 본문은 Summary와 Changes만 씁니다. 저장소에 PR 템플릿이 있으면 템플릿을 따릅니다.
- 보고서는 `<!-- git-kit:report -->`로 시작하는 PR 첫 코멘트입니다. 다시 실행하면 새 코멘트를 달지 않고 이 코멘트를 고칩니다.
- 결정 대기 브랜치의 PR은 제목이 🚧로 시작하고 항상 Draft로 만들어집니다. 보고서의 Decisions needed에서 선택지를 체크해 답합니다.
- `--auto`로 만든 PR도 Draft입니다. Draft 해제는 사람이 합니다.
- force push는 하지 않습니다. 기본 브랜치보다 뒤처졌으면 확인 모드는 먼저 머지할지 묻고, 자동 모드는 보고서의 Please check에 적습니다.
- PR 본문과 코멘트에도 서명 줄(`Generated with Claude Code` 등)을 붙이지 않습니다.

## 테스트

`evals/`에 [claude plugin eval](https://code.claude.com/docs/en/plugin-evals) 형식의 평가 케이스가 있습니다. 플러그인 폴더에서 실행합니다(사용량 차감).

```bash
claude plugin eval . --scaffold --allow-tools Bash
```

- `--scaffold`: 케이스마다 테스트용 git 저장소를 만듭니다.
- `--allow-tools Bash`: 커밋과 push에 필요합니다.
- 한 케이스만 돌리려면 `--case <케이스 이름>`을 붙입니다. 스킬이 있을 때만 돌리려면 `--ablation none`을 붙입니다(비용 절반).
- pr-writer 케이스는 가짜 원격 저장소로 push하고, gh 로그인이 없어 링크 안내로 끝납니다. 실제 PR 생성, 보고서 코멘트, Draft, 갱신은 테스트용 GitHub 저장소에서 직접 확인하세요.
- pre-commit hook 실패 처리는 평가 환경이 hook을 끄고 실행해서 확인할 수 없습니다. 실제 저장소에서 직접 확인하세요.
