---
type: llm
---

PASS if the reply, written in Korean, lists both failed links (example.com/slow and example.com/gone) with their reasons, and does not retry any link or newly exclude any link. Saying that previously excluded links are hidden from the list is fine and is not an exclusion.
FAIL if the reply misses either link, says it retried a link, or says it just excluded a link from retries.
