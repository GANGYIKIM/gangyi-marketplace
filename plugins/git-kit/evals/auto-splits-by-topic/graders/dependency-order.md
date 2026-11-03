---
type: regex
pattern: '^(?![\s\S]*✨ feat: [\s\S]*♻\S* refactor: )[\s\S]*✨ feat: [a-z]'
target: { source: file, path: .git/logs/HEAD }
---
