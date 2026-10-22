---
type: llm
focus: { source: file, path: .git/logs/HEAD }
---

Look only at commit lines added after the initial commit.
PASS if every such commit message has the form `<emoji> <type>: <message>`, the message is English, starts with a lowercase imperative present-tense verb (add, fix, extract…), has no trailing period, is 72 characters or fewer in total, and there is no signature such as Co-Authored-By.
FAIL if any commit breaks one of these rules.
