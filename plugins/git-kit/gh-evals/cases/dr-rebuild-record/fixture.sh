#!/bin/bash
set -e
source "$GK_CASE/../_shared/lockout.sh"
# 다른 컴퓨터에서 만든 결정 대기 PR: 이 저장소에는 결정 기록이 없음
lockout_branch
