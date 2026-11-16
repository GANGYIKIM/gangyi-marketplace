#!/usr/bin/env node
// Claude Code PermissionRequest 훅. 확인 창을 띄우기 직전에 돈다.
//
// 쓰려는 내용이 지금 파일과 같은 Write면 사람 대신 거절하고, 표시와 권한 모드를 Claude에게 돌려준다.
// 그 밖의 호출에는 아무것도 하지 않아 평소처럼 확인 창이 뜬다.
//
// harness-builder가 "검사 설정 보호"를 확인하는 데 쓴다. 허용한 것과 창이 뜨지 않은 것은
// 도구 결과가 같아서, 창이 뜰 자리였는지를 이 훅이 알려 준다.

import { readFileSync, realpathSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

export const MARK = '[dev-kit:noop-write]';

const readText = (path) => readFileSync(path, 'utf8');

// 거절할 때 Claude에게 돌려줄 말. 거절하지 않으면 null.
export function noopWriteMessage(input, read = readText) {
  if (input?.tool_name !== 'Write') return null;
  const { file_path: filePath, content } = input.tool_input ?? {};
  if (typeof filePath !== 'string' || typeof content !== 'string') return null;

  let current;
  try {
    current = read(filePath);
  } catch {
    return null;
  }
  if (current !== content) return null;

  const mode = typeof input.permission_mode === 'string' ? input.permission_mode : '알 수 없음';
  return `${MARK} 확인 창이 뜰 자리입니다 (권한 모드: ${mode}). 쓰려는 내용이 지금 파일과 같아서 쓰지 않았습니다.`;
}

function main() {
  let input;
  try {
    input = JSON.parse(readFileSync(0, 'utf8'));
  } catch {
    process.exit(0);
  }

  const message = noopWriteMessage(input);
  if (!message) process.exit(0);

  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PermissionRequest',
        decision: { behavior: 'deny', message, interrupt: false },
      },
    }),
  );
}

const isMain = process.argv[1] && realpathSync(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) main();
