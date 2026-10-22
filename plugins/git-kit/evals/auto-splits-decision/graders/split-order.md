---
type: regex
pattern: 'commit: [^\n]*(feat|fix): [a-z][^\n]*\n[\s\S]*checkout: moving from feat/login-email-validation to [a-z]+/[a-z0-9-]+\n[\s\S]*commit: '
target: { source: file, path: .git/logs/HEAD }
---
