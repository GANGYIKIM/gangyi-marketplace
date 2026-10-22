---
description: 자동 모드에서 미리 stage된 .env는 stage를 해제하고 .DS_Store는 제외한 채 나머지만 커밋하는지 확인 (--scaffold 필요)
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill, Bash]
---

/git-kit:commit-writer --auto
