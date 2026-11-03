#!/bin/bash
# 한 파일(format.ts)에 두 주제가 섞인 작업 브랜치를 만든다.
# - fix: formatPrice 반올림 자릿수 수정과 그 테스트 수정 (format.ts, format.test.ts)
# - feat: 새 formatDate와 그것을 쓰는 DateLabel 컴포넌트 (format.ts, DateLabel.tsx)
set -e
git init -q -b main
git config user.name "eval"
git config user.email "eval@example.com"
mkdir -p src/utils
echo "# demo" > README.md
printf 'export const formatPrice = (n: number) => `$${n.toFixed(1)}`;\n' > src/utils/format.ts
cat > src/utils/format.test.ts <<'TS'
import { formatPrice } from "./format";
test("formatPrice", () => expect(formatPrice(3.456)).toBe("$3.5"));
TS
git add . && git commit -q -m "initial commit"
git switch -q -c feat/add-date-label
cat > src/utils/format.ts <<'TS'
export const formatPrice = (n: number) => `$${n.toFixed(2)}`;
export const formatDate = (d: Date) => d.toISOString().slice(0, 10);
TS
cat > src/utils/format.test.ts <<'TS'
import { formatPrice } from "./format";
test("formatPrice", () => expect(formatPrice(3.456)).toBe("$3.46"));
TS
mkdir -p src/components
cat > src/components/DateLabel.tsx <<'TSX'
import { formatDate } from "../utils/format";
export const DateLabel = ({ date }: { date: Date }) => <time>{formatDate(date)}</time>;
TSX
