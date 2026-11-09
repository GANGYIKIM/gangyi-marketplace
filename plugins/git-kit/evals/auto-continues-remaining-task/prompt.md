---
description: 요청에 커밋 뒤의 일이 함께 있으면 스킬의 마무리 안내 뒤에 그 일을 이어서 하는지 확인 (--scaffold 필요)
max_turns: 15
allowed_tools: [Read, Write, Edit, Glob, Grep, Skill, Bash]
---

/git-kit:commit-writer --auto 커밋하고 그 커밋 해시를 notes.md에 적어줘
