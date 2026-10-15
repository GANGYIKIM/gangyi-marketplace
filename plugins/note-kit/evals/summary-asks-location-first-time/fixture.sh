#!/bin/bash
# summaries/ 폴더가 없는 상태에서 원본만 만든다.
set -e
mkdir -p notes
printf '# 10월 15일 회의록\n\n다음 분기 목표를 정하고, 신규 기능 우선순위를 세 가지로 좁혔다.\n' > notes/회의록_1015.md
