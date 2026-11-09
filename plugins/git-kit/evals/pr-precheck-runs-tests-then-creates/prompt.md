---
description: 자동 모드에서 넘겨받은 확신 못한 점이 실행해서 확인할 수 있는 것(테스트)이면 PR 전에 돌려 결과를 Testing에 쓰는지 확인 (--scaffold 필요)
max_turns: 30
allowed_tools: [Read, Glob, Grep, Skill, Bash]
---

/git-kit:pr-writer --auto greet 유틸 추가 작업이야. 테스트(./test.sh)는 아직 안 돌렸어.
