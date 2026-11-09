---
description: 기록 없는 push된 브랜치에 결정 대기 변경만 있으면 지금 브랜치에 커밋하지 않고 그 위에 새 결정 대기 브랜치를 따는지 확인 (--scaffold 필요)
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill, Bash]
---

/git-kit:commit-writer --auto 잠금 기준 횟수는 아직 결정 안 됐어
