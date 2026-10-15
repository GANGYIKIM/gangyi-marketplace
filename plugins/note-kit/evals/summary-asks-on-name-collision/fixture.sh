#!/bin/bash
# 다른 원본(notes/a/정리.md)의 요약이 이미 있는 상태를 만든다.
set -e
mkdir -p notes/a notes/b summaries
printf '# 정리\n\n지난주 스터디에서 다룬 타입스크립트 제네릭 내용.\n' > notes/a/정리.md
printf '# 정리\n\n이번 주 팀 회고에서 나온 개선 아이디어 목록.\n' > notes/b/정리.md
cat > summaries/정리.md << 'DOC'
# 정리

- 원본 파일: `notes/a/정리.md`
- 요약일: 2026-10-10
- 작성: AI 요약 (원문과 다를 수 있음)

> 타입스크립트 제네릭 스터디 내용 요약

## 핵심 내용
- 제네릭으로 타입을 매개변수처럼 다루는 방법을 다뤘다.
DOC
