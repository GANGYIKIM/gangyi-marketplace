---
type: regex
pattern: '♻\S* refactor: [a-z][\s\S]*✨ feat: [a-z]'
target: { source: file, path: .git/logs/HEAD }
---
