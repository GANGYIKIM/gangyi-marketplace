#!/bin/bash
# ssh 대신 쓴다. git이 git@github.com:<owner>/<repo>.git에 네트워크 없이 push, fetch하게 한다.
# git이 부르는 모양: fake_ssh.sh <원격 폴더> [ssh 옵션] <호스트> "<git 명령> '<경로>'"
# 명령은 로컬 bare 저장소인 <원격 폴더>/<경로>에서 돈다.
root="$1"; shift
cmd="${!#}"
prog="${cmd%% *}"
path="${cmd#* }"; path="${path//\'/}"; path="${path#/}"
case "$prog" in
  git-upload-pack|git-receive-pack|git-upload-archive) exec "$prog" "$root/$path" ;;
  *) echo "fake ssh: unsupported command: $cmd" >&2; exit 1 ;;
esac
