#!/bin/bash
set -e
mkdir -p clips
cat > clips/clip-log.md << 'LOG'
# 클리핑 기록

| 날짜 | 링크 | 결과 | 실패 사유 |
|---|---|---|---|
| 2026-10-15 | https://example.com/slow | 실패 | 네트워크: 시간 초과 (재시도 가능) |
| 2026-10-15 | https://example.com/gone | 실패 | 페이지 없음: 404 (재시도 불가) |
LOG
