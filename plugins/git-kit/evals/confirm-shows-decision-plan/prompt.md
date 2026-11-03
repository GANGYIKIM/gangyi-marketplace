---
description: 확인 모드에서 결정 대기 변경이 있으면 분할안에 결정 대기 묶음을 넣고, 확인 전에는 커밋, 브랜치 생성, 기록 쓰기를 하지 않는지 확인 (--scaffold 필요)
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill, Bash]
---

커밋해줘. 계정 잠금 정책(로그인 몇 회 실패 시 잠글지)은 아직 결정 안 됐어. 결정 대기 브랜치 이름은 feat/login-lockout-policy로 해줘
