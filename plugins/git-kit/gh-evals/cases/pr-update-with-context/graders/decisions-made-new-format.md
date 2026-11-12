---
type: regex
target: github
match: contains
pattern: '## Decisions made\n- [^\n]*함수 하나로 둠[^\n]*\[`src/auth/lockout\.ts:\d+`\]\(https://github\.com/test/demo/blob/[0-9a-f]{40}/src/auth/lockout\.ts#L\d+\)\n(?:[^\n]*\n)*?\s*<details><summary>이유와 버린 안</summary>\n\n(?:[^\n]*\n)*?\s*- 버린 안: [^\n]*조건문[^\n]*\n\s*</details>'
---
