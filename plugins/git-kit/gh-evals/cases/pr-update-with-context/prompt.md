---
description: 맥락이 있을 때 기존 PR 갱신 — 보고서 코멘트 하나만 고쳐 쓰고, 결정 부분은 그대로 두고, 예전 형식 Decisions made는 새 템플릿으로 다시 쓰고, 옛 상태 항목은 Status로 다시 계산하는지 확인
timeout_seconds: 600
allow: [push]
---

/git-kit:pr-writer --auto lockout 테스트를 더한 작업이야. shouldLock의 경계값(4회는 false, 5회는 true)을 다루는 테스트 파일을 추가함. 확신 못한 점 없음.
