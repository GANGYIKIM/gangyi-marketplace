#!/bin/bash
set -e
source "$GK_CASE/../_shared/lockout.sh"
lockout_branch
{ record_head; d1_block 대기
  printf '%s\n' '' 'D2. 잠긴 계정을 어떻게 풀지' '상태: 대기' '관련 파일: src/auth/lockout.ts' '' \
    '미결정 이유: 해제 방식 기준 없음. 고객 지원 정책 확인 필요.'
} | gk_record feat/account-lockout
