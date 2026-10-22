#!/bin/bash
# 작업 브랜치에 세 주제가 섞인 변경을 만든다.
# - refactor: Profile.tsx 안의 formatName을 utils로 추출
# - feat: 추출한 formatName을 쓰는 새 UserCard 컴포넌트 (refactor에 의존)
# - docs: README 오타 수정
set -e
git init -q -b main
git config user.name "eval"
git config user.email "eval@example.com"
mkdir -p src/components
printf '# demo\n\n## Instalation\n\nnpm install\n' > README.md
cat > src/components/Profile.tsx <<'TSX'
const formatName = (first: string, last: string) => `${last} ${first}`;
export const Profile = ({ first, last }: { first: string; last: string }) => <p>{formatName(first, last)}</p>;
TSX
git add . && git commit -q -m "initial commit"
git switch -q -c feat/add-user-card
mkdir -p src/utils
printf 'export const formatName = (first: string, last: string) => `${last} ${first}`;\n' > src/utils/formatName.ts
cat > src/components/Profile.tsx <<'TSX'
import { formatName } from "../utils/formatName";
export const Profile = ({ first, last }: { first: string; last: string }) => <p>{formatName(first, last)}</p>;
TSX
cat > src/components/UserCard.tsx <<'TSX'
import { formatName } from "../utils/formatName";
export const UserCard = ({ first, last }: { first: string; last: string }) => <div>{formatName(first, last)}</div>;
TSX
sed -i.bak 's/Instalation/Installation/' README.md && rm README.md.bak
