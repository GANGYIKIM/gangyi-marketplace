---
type: regex
pattern: 'checkout: moving from feat/login-failure-tracking to (feat|fix|refactor|style|docs|test|chore)/[a-z0-9-]+\n[\s\S]*commit: [^\n]*\n[\s\S]*checkout: moving from (feat|fix|refactor|style|docs|test|chore)/[a-z0-9-]+ to feat/login-failure-tracking'
target: { source: file, path: .git/logs/HEAD }
---
