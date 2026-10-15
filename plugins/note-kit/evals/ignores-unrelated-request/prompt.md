---
description: 코드 수정 같은 일반 작업 요청에는 idea-writer가 끼어들지 않는지 확인
tags: [smoke]
max_turns: 5
allowed_tools: [Read, Glob, Grep, Skill]
---

이 함수 이름을 getUser에서 fetchUser로 바꾼 코드를 보여줘: function getUser(id) { return db.find(id) }
