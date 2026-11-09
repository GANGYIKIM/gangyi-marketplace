---
description: 자동 모드에서 넘겨받은 확신 못한 점을 읽어서 확인할 수 있으면 PR 전에 확인해 결과를 Testing에 쓰고 Please check에는 남기지 않으며, 문제가 없으니 보류하지 않는지 확인 (--scaffold 필요)
max_turns: 30
allowed_tools: [Read, Glob, Grep, Skill, Bash]
---

/git-kit:pr-writer --auto greet 유틸 추가 작업이야. README 사용법 예시에 적힌 결과값이 greet의 실제 반환값과 같은지는 확인 못했어.
