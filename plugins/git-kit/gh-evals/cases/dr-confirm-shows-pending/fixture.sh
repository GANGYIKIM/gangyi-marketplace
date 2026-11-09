#!/bin/bash
set -e
source "$GK_CASE/../_shared/lockout.sh"
lockout_branch
{ record_head; d1_block 대기; d2_block; } | gk_record feat/account-lockout
