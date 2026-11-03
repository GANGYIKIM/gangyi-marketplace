---
type: regex
pattern: 'ref: refs/heads/feat/[a-z0-9]+(-[a-z0-9]+){2,4}\s*$'
target: { source: file, path: .git/HEAD }
---
