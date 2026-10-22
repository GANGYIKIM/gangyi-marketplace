---
description: 자동 모드에서 main이면 묻지 않고 규칙에 맞는 브랜치를 만들어 커밋하고 push는 하지 않는지 확인 (--scaffold 필요)
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill, Bash]
---

/git-kit:commit-writer --auto
