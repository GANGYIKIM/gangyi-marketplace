#!/bin/bash
# clips/inbox/에 저장 HTML 파일 2개를 만든다.
set -e
mkdir -p clips/inbox
for n in a b; do
  printf '<html><head><title>Saved %s</title><link rel="canonical" href="https://example.com/%s"></head><body><p>saved page %s</p></body></html>' "$n" "$n" "$n" > "clips/inbox/saved-$n.html"
done
