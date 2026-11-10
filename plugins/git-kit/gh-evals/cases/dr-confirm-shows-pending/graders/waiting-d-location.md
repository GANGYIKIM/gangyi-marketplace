---
type: regex
target: last_message
match: contains
pattern: '- D1\. 로그인 실패 시 계정을 잠글지: \[대기\]\n(?:[ \t]+[^\n]*\n)*?[ \t]+- 관련 위치: src/auth/lockout\.ts:\d'
---
