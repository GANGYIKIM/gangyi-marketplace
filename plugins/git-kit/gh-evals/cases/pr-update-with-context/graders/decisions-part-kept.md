---
type: regex
target: github
match: contains
pattern: '<!-- git-kit:decisions -->\n> \[!WARNING\]\n> 결정 대기\. 머지 전 아래 Decisions needed의 결정 필요\.\n> 답하는 법: 항목마다 선택지 하나 체크\. 선택지에 없는 답은 PR 코멘트로 작성\. 이후 Claude에게 결정 반영 요청\.\n\n## Decisions needed\n### D1\. 로그인 실패 시 계정을 잠글지\n- 미결정 이유: 기획 문서에 기준 없음\. 보안과 사용성 사이 제품 판단 필요\n- 현재 임시값: 5회 실패 시 잠금\n- 관련 위치:\n  - \[`src/auth/lockout\.ts:2-3`\]\(https://github\.com/test/demo/blob/[0-9a-f]{40}/src/auth/lockout\.ts#L2-L3\) 잠금 여부와 횟수 판단\n- \[ \] 잠금 \(추천\): 무차별 대입 방어\. 오타 잦은 사용자는 불편\n- \[ \] 잠그지 않음: 사용성 좋음\. 방어는 지연 시간에 의존\n### D2\. 몇 회 실패에 잠글지\n- 미결정 이유: 보안 정책 기준 없음\n- 현재 임시값: 5회\n- 의존: D1의 답이 잠금일 때만 필요\n- 관련 위치:\n  - \[`src/auth/lockout\.ts:2`\]\(https://github\.com/test/demo/blob/[0-9a-f]{40}/src/auth/lockout\.ts#L2\) 실패 횟수 상수\n- \[ \] 5회 \(추천\): 일반적인 기준\. 무차별 대입 방어에 충분\n- \[ \] 10회: 오타가 잦은 사용자에게 관대함\. 방어력은 낮아짐\n<!-- /git-kit:decisions -->'
---
