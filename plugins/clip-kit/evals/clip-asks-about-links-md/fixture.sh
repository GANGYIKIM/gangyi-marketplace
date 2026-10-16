#!/bin/bash
# clips/ 폴더와 링크 3개가 담긴 links.md를 만든다.
set -e
mkdir -p clips
printf '# 읽을거리\n- https://example.com/a\n- https://example.com/b\n- https://example.com/c\n' > clips/links.md
