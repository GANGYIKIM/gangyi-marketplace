#!/usr/bin/env node
// Claude Code PreToolUse 훅. 커밋 전 검사를 건너뛰는 git commit을 막는다.
//
// 막는 것
// - git commit --no-verify, git commit -n (-nm, -anm처럼 묶어 쓴 것 포함)
// - HUSKY=0을 건 git commit (앞에 붙인 것, export, env)
//
// 종료 코드 2는 막음(stderr가 Claude에게 전달됨), 0은 통과.
// 명령 글자를 읽어 판단하므로 AI가 보통 쓰는 방식만 막는다. 보안 경계가 아니다.

import { readFileSync, realpathSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const MESSAGES = {
  'no-verify':
    '커밋 전 검사를 건너뛰는 커밋(--no-verify, -n)은 이 프로젝트에서 막혀 있습니다. ' +
    '옵션을 빼고 다시 커밋하세요. 검사가 실패하면 원인을 고치고, 고칠 수 없으면 사람에게 알리세요.',
  'husky-off':
    'HUSKY=0으로 커밋 전 검사를 끄는 커밋은 이 프로젝트에서 막혀 있습니다. ' +
    'HUSKY=0을 빼고 다시 커밋하세요. 검사가 실패하면 원인을 고치고, 고칠 수 없으면 사람에게 알리세요.',
};

const ASSIGNMENT = /^[A-Za-z_][A-Za-z0-9_]*=/;
const SHELLS = new Set(['sh', 'bash', 'zsh', 'dash']);

// git <여기> commit 자리에 오는 옵션 중 값을 따로 받는 것
const GIT_OPTIONS_WITH_VALUE = new Set(['-C', '-c', '--git-dir', '--work-tree', '--namespace', '--config-env']);

// git commit의 옵션 중 값을 따로 받는 것. 값 자리의 글자는 옵션으로 읽지 않는다.
const COMMIT_LONG_WITH_VALUE = new Set([
  '--message',
  '--file',
  '--author',
  '--date',
  '--reuse-message',
  '--reedit-message',
  '--fixup',
  '--squash',
  '--template',
  '--cleanup',
  '--trailer',
  '--pathspec-from-file',
]);
const COMMIT_SHORT_WITH_VALUE = 'mFCct'; // 값은 묶음의 나머지이거나 다음 토큰
const COMMIT_SHORT_WITH_ATTACHED_VALUE = 'Su'; // 값은 묶음의 나머지 (-uno, -S<키>)

// heredoc 본문(커밋 메시지 등)은 명령이 아니므로 뺀다.
function stripHeredocBodies(command) {
  const kept = [];
  const waiting = [];
  for (const line of command.split('\n')) {
    if (waiting.length > 0) {
      if (line.trim() === waiting[0]) waiting.shift();
      continue;
    }
    kept.push(line);
    for (const match of line.matchAll(/(?<!<)<<(?!<)-?\s*(['"]?)([A-Za-z_][A-Za-z0-9_]*)\1/g)) {
      waiting.push(match[2]);
    }
  }
  return kept.join('\n');
}

// 명령을 단순 명령(토큰 배열)들로 나눈다. 따옴표 안의 글자는 한 토큰으로 묶인다.
function splitSegments(command) {
  const segments = [];
  let tokens = [];
  let current = '';
  let hasToken = false;
  let quote = null;

  const pushToken = () => {
    if (hasToken) tokens.push(current);
    current = '';
    hasToken = false;
  };
  const pushSegment = () => {
    pushToken();
    if (tokens.length > 0) segments.push(tokens);
    tokens = [];
  };

  for (let i = 0; i < command.length; i++) {
    const ch = command[i];
    if (quote === "'") {
      if (ch === "'") quote = null;
      else current += ch;
      continue;
    }
    if (quote === '"') {
      if (ch === '"') quote = null;
      else if (ch === '\\' && i + 1 < command.length) current += command[++i];
      else current += ch;
      continue;
    }
    if (ch === "'" || ch === '"') {
      quote = ch;
      hasToken = true;
      continue;
    }
    if (ch === '\\' && i + 1 < command.length) {
      i++;
      if (command[i] !== '\n') {
        current += command[i];
        hasToken = true;
      }
      continue;
    }
    if (ch === '#' && !hasToken) {
      while (i + 1 < command.length && command[i + 1] !== '\n') i++;
      continue;
    }
    if (ch === ' ' || ch === '\t') {
      pushToken();
      continue;
    }
    if ('\n;|&()`'.includes(ch)) {
      pushSegment();
      continue;
    }
    if (ch === '$' && command[i + 1] === '(') {
      pushSegment();
      i++;
      continue;
    }
    current += ch;
    hasToken = true;
  }
  pushSegment();
  return segments;
}

const commandName = (token) => token.slice(token.lastIndexOf('/') + 1);

// git 뒤의 토큰에서 하위 명령이 commit이면 그 뒤의 인자를, 아니면 null을 돌려준다.
function commitArgs(afterGit) {
  let i = 0;
  while (i < afterGit.length && afterGit[i].startsWith('-')) {
    i += GIT_OPTIONS_WITH_VALUE.has(afterGit[i]) ? 2 : 1;
  }
  return afterGit[i] === 'commit' ? afterGit.slice(i + 1) : null;
}

function skipsVerify(args) {
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--') return false;
    if (arg.startsWith('--')) {
      // git은 겹치지 않는 앞부분만 써도 받는다 (--no-veri)
      if (arg.length >= '--no-veri'.length && '--no-verify'.startsWith(arg)) return true;
      if (COMMIT_LONG_WITH_VALUE.has(arg)) i++;
      continue;
    }
    if (!arg.startsWith('-')) continue;
    for (let j = 1; j < arg.length; j++) {
      const flag = arg[j];
      if (flag === 'n') return true;
      if (COMMIT_SHORT_WITH_ATTACHED_VALUE.includes(flag)) break;
      if (COMMIT_SHORT_WITH_VALUE.includes(flag)) {
        if (j === arg.length - 1) i++;
        break;
      }
    }
  }
  return false;
}

// 건너뛰는 커밋이면 'no-verify'나 'husky-off'를, 아니면 null을 돌려준다.
export function findBypass(command, depth = 0) {
  if (typeof command !== 'string' || depth > 3) return null;

  let huskyOff = false; // 앞에서 export HUSKY=0을 했는가
  for (const tokens of splitSegments(stripHeredocBodies(command))) {
    let start = 0;
    let segmentHuskyOff = false;
    while (start < tokens.length && ASSIGNMENT.test(tokens[start])) {
      if (tokens[start] === 'HUSKY=0') segmentHuskyOff = true;
      start++;
    }
    if (start === tokens.length) continue;

    const name = commandName(tokens[start]);
    if (name === 'export') {
      if (tokens.slice(start + 1).includes('HUSKY=0')) huskyOff = true;
      continue;
    }
    if (SHELLS.has(name) || name === 'eval') {
      const rest = tokens.slice(start + 1);
      const flagIndex = rest.findIndex((token) => /^-[a-z]*c$/.test(token));
      const script = name === 'eval' ? rest.join(' ') : flagIndex === -1 ? null : rest[flagIndex + 1];
      const inner = findBypass(script, depth + 1);
      if (inner) return inner;
      continue;
    }

    const gitIndex = tokens.findIndex((token, index) => index >= start && commandName(token) === 'git');
    if (gitIndex === -1) continue;
    const args = commitArgs(tokens.slice(gitIndex + 1));
    if (!args) continue;

    if (name === 'env' && tokens.slice(start + 1, gitIndex).includes('HUSKY=0')) segmentHuskyOff = true;
    if (segmentHuskyOff || huskyOff) return 'husky-off';
    if (skipsVerify(args)) return 'no-verify';
  }
  return null;
}

function main() {
  let input;
  try {
    input = JSON.parse(readFileSync(0, 'utf8'));
  } catch {
    process.exit(0);
  }
  if (input?.tool_name !== 'Bash') process.exit(0);

  const found = findBypass(input?.tool_input?.command);
  if (!found) process.exit(0);

  process.stderr.write(`${MESSAGES[found]}\n`);
  process.exit(2);
}

const isMain = process.argv[1] && realpathSync(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) main();
