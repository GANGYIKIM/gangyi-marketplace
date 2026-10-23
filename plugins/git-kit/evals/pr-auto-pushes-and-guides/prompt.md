---
description: 자동 모드에서 묻지 않고 push하고, gh가 없으면 링크 안내로 제목과 본문을 보여주는지 확인 (--scaffold 필요)
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill, Bash]
---

/git-kit:pr-writer --auto
