---
description: 부른 쪽이 "리뷰어가 보면 된다"고 넘긴 확신 못한 점도 AI가 확인할 수 있으면 PR 전에 확인해 Testing에 쓰고 Please check에는 남기지 않는지 확인 (--scaffold 필요)
max_turns: 30
allowed_tools: [Read, Glob, Grep, Skill, Bash]
---

/git-kit:pr-writer --auto greet 유틸 추가 작업이야. 확신 못한 것: README 사용법 예시에 적힌 결과값이 greet의 실제 반환값과 같은지. 리뷰어가 PR에서 보면 될 것 같아.
