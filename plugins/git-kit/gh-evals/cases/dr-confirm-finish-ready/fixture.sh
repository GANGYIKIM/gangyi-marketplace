#!/bin/bash
set -e
source "$GK_CASE/../_shared/lockout.sh"
lockout_branch
{ record_head; d1_decided; } | gk_record feat/account-lockout
reflect_commit
