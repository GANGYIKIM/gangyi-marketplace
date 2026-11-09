#!/bin/bash
# gh-evals fixture 도우미. 실행기가 GK_LIB, GK_REMOTES를 정하고 빈 작업 폴더에서
# fixture를 돌린다.
#
#   gk_init_repo                 커밋 하나가 있는 main을 git@github.com:test/demo.git에
#                                push한다 (가짜 ssh로 닿는 로컬 bare 저장소)
#   gk_commit <파일> <메시지>    stdin의 내용으로 파일을 쓰고 커밋한다
#   gk_push <브랜치>             push하고 upstream을 정한다
#   gk_record <브랜치>           stdin의 내용으로 결정 기록을 쓴다
set -e

gk_init_repo() {
  git init -q -b main
  git config user.name "eval"
  git config user.email "eval@example.com"
  mkdir -p "$GK_REMOTES/test"
  git init -q --bare "$GK_REMOTES/test/demo.git"
  git remote add origin git@github.com:test/demo.git
  git config core.sshCommand "$GK_LIB/fake_ssh.sh $GK_REMOTES"
  echo "# demo" > README.md
  git add README.md
  git commit -q -m "initial commit"
  git push -q origin main
  git remote set-head origin main
}

gk_commit() {
  mkdir -p "$(dirname "$1")"
  cat > "$1"
  git add "$1"
  git commit -q -m "$2"
}

gk_push() {
  git push -q -u origin "$1"
}

gk_record() {
  git hash-object -w --stdin | xargs git update-ref "refs/git-kit/decisions/$1"
}
