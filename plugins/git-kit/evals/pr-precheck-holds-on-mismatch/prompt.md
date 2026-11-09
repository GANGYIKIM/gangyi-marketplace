---
description: PR 전 확인에서 README 예시와 코드가 다르면 고치지 않고 push 없이 "확인에서 문제 발견"으로 보류하는지 확인 (--scaffold 필요)
max_turns: 30
allowed_tools: [Read, Glob, Grep, Skill, Bash]
---

/git-kit:pr-writer --auto greet 유틸 추가 작업이야. README 사용법 예시에 적힌 결과값이 greet의 실제 반환값과 같은지는 확인 못했어.
