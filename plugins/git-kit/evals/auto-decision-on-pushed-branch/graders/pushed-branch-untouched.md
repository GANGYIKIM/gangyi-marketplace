---
type: regex
pattern: '\tcommit[^\n]*\n[\s\S]*\tcommit'
match: not_contains
target: { source: file, path: .git/logs/refs/heads/feat/login-failure-tracking }
---
