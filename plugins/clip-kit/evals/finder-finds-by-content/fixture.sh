#!/bin/bash
set -e
mk(){ mkdir -p "clips/$1"; printf '<!DOCTYPE html><html><head><meta name="clip:source" content="%s"><meta name="clip:title" content="%s"><meta name="clip:saved" content="%s"></head><body><article><p>%s</p></article></body></html>' "$2" "$3" "$4" "$5" > "clips/$1/$1.html"; }
mk react-19-stable-release https://react.dev/blog/react-19 "React 19 Stable Release" 2026-10-15 "Server Components are now stable and Actions handle pending states."
mk kind-code-review https://example.com/kind-code-review "Kind Code Review" 2026-10-12 "Keep code review feedback short and kind."
