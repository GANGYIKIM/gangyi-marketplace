#!/bin/bash
set -e
source "$GK_CASE/../_shared/lockout.sh"
gk_init_repo
lower_branch
lockout_commit
{ record_head feat/count-login-failures; d1_decided; } | gk_record feat/account-lockout
reflect_commit
