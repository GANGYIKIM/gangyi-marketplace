#!/bin/bash
# clips/ 폴더와, canonical 주소가 있는 저장 HTML 파일을 만든다.
set -e
mkdir -p clips downloads
body=$(printf 'This saved article explains how teams review pull requests and keep feedback short and kind. %.0s' {1..10})
printf '<html><head><title>Kind Code Review</title><link rel="canonical" href="https://example.com/kind-code-review"></head><body><article><h1>Kind Code Review</h1><p>%s</p></article></body></html>' "$body" > downloads/kind-code-review.html
