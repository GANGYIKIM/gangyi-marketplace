---
description: 결정이 필요한 변경을 새 브랜치로 떼어내고, 결정 대기 기록 파일을 남기고, 자동 모드라 대기 변경도 커밋하는지 확인 (--scaffold 필요)
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill, Bash]
---

/git-kit:commit-writer --auto 계정 잠금 정책(로그인 몇 회 실패 시 잠글지)은 아직 결정 안 됐어. 결정 대기 브랜치 이름은 feat/login-lockout-policy로 해줘
