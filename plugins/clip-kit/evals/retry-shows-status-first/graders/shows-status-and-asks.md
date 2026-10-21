---
type: llm
---

PASS if the reply, written in Korean, groups the failures into retryable (timeout) and not retryable (404), and asks the user what to do next, such as retrying or excluding, without having retried anything yet.
FAIL if the reply says it already retried or clipped the links, does not separate retryable from not retryable, or does not ask what to do.
