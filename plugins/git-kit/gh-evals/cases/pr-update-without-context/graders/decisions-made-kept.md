---
type: regex
target: github
match: contains
pattern: '## Decisions made\n- 잠금 판단을 어디에 두나\n  - 정한 것: \*\*로그인 처리와 떼어 lockout\.ts의 함수 하나로 둠\*\* \[`src/auth/lockout\.ts:3`\]\(https://github\.com/test/demo/blob/[0-9a-f]{40}/src/auth/lockout\.ts#L3\)\n  - 버린 안: 로그인 처리 안에 조건문으로 둠\(결정이 바뀔 때 고칠 곳이 흩어짐\)\n'
---
