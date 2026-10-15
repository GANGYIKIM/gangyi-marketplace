#!/bin/bash
# 원본 클립과 이미 있는 summaries/ 폴더를 만든다. --scaffold 옵션을 줄 때만 실행된다.
set -e
mkdir -p clips summaries
cat > clips/react19_출시.md << 'DOC'
---
source: https://example.com/react-19
---
# React 19 is now stable

React 19 is now available. This release adds Actions, a way to handle pending
states, errors, and optimistic updates for async work such as form submissions.
Server Components are now stable and can be used in production frameworks.
Some legacy APIs were removed, so read the upgrade guide before updating.
DOC
