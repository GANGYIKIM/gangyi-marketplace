---
name: profile-cleaner
description: link-clipper가 막힌 사이트를 다시 열 때 쓰는 클리핑 전용 Chrome 프로필(쿠키, 캐시)을 확인하고 지운다. 사용자가 /clip-kit:profile-cleaner로 직접 부를 때만 쓴다.
disable-model-invocation: true
---

# Profile Cleaner

link-clipper는 막힌 사이트를 Chrome 창으로 다시 열 때 클리핑 전용 프로필을 쓴다. 확인을 통과한 쿠키가 쌓여 다음부터 바로 열리게 하려는 것이라, 평소에는 지우지 않는 편이 낫다. 이 스킬은 확인 화면이 계속 반복되거나, 그 창에서 한 로그인을 지우고 싶거나, 용량이 커졌을 때 쓰는 비상용이다.

## 원칙

- **클리핑 전용 프로필만 다룬다.** 평소 쓰는 Chrome 프로필은 어떤 경우에도 지우지 않는다. 스크립트도 그런 경로는 거부한다.
- **승인받기 전에는 지우지 않는다.** 되돌릴 수 없는 삭제다.
- **지울 때는 스크립트만 쓴다.** `rm` 같은 명령으로 직접 지우지 않는다.

## 진행 순서

`${CLAUDE_SKILL_DIR}/scripts/profile.py`를 실행한다. 결과는 JSON 한 줄이다.

1. `python3 ${CLAUDE_SKILL_DIR}/scripts/profile.py show`를 실행한다.
   - `exists`가 false면 "지울 프로필이 없어요"라고 알리고 끝낸다.
2. 위치, 크기, 데이터를 남긴 사이트 수를 보여주고, 지우면 무엇이 사라지는지 알린 뒤 묻는다.
   > 클리핑 전용 프로필(`<profile_dir>`, `<size>`, 사이트 `<sites>`곳)을 지우면 쿠키와 그 창에서 한 로그인이 사라지고, 다음 클리핑 때 확인 화면을 다시 통과해야 할 수 있어요. 지울까요?
   - `in_use`가 true면 먼저 클리핑용 Chrome 창을 닫아 달라고 안내한다.
3. 그렇다고 하면 `python3 ${CLAUDE_SKILL_DIR}/scripts/profile.py clear`를 실행하고 결과를 알린다.
   - `in_use` 오류면 창을 닫고 다시 부르도록 안내한다.
   - `not_clip_profile` 오류면 지우지 않은 이유를 그대로 알린다.
