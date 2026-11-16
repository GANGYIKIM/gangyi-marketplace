// 실행 (저장소 루트에서): node --test "plugins/dev-kit/tests/*.test.mjs"
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { after, test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { MARK, noopWriteMessage } from '../hooks/report-noop-write.mjs';

const SCRIPT = fileURLToPath(new URL('../hooks/report-noop-write.mjs', import.meta.url));
const HOOKS_JSON = fileURLToPath(new URL('../hooks/hooks.json', import.meta.url));

const dir = mkdtempSync(join(tmpdir(), 'dev-kit-noop-write-'));
after(() => rmSync(dir, { recursive: true, force: true }));

const FILE = join(dir, '.prettierrc.json');
writeFileSync(FILE, '{}\n');

const write = (content, extra = {}) => ({
  hook_event_name: 'PermissionRequest',
  permission_mode: 'auto',
  tool_name: 'Write',
  tool_input: { file_path: FILE, content },
  ...extra,
});

test('내용이 같은 Write는 표시와 권한 모드를 돌려준다', () => {
  const message = noopWriteMessage(write('{}\n'));
  assert.ok(message.startsWith(MARK));
  assert.match(message, /권한 모드: auto/);
});

test('권한 모드가 default면 그대로 알린다', () => {
  assert.match(noopWriteMessage(write('{}\n', { permission_mode: 'default' })), /권한 모드: default/);
});

test('내용이 다른 Write는 손대지 않는다', () => {
  assert.equal(noopWriteMessage(write('{ "semi": false }\n')), null);
  assert.equal(noopWriteMessage(write('{}')), null);
});

test('없는 파일에 쓰는 Write는 손대지 않는다', () => {
  const input = write('{}\n');
  input.tool_input.file_path = join(dir, 'missing.json');
  assert.equal(noopWriteMessage(input), null);
});

test('Write가 아닌 도구는 손대지 않는다', () => {
  assert.equal(noopWriteMessage(write('{}\n', { tool_name: 'Edit' })), null);
  assert.equal(noopWriteMessage(write('{}\n', { tool_name: 'Bash' })), null);
});

test('입력이 모자라면 손대지 않는다', () => {
  assert.equal(noopWriteMessage(null), null);
  assert.equal(noopWriteMessage({ tool_name: 'Write' }), null);
  assert.equal(noopWriteMessage({ tool_name: 'Write', tool_input: { file_path: FILE } }), null);
});

const runHook = (stdin) => spawnSync('node', [SCRIPT], { input: stdin, encoding: 'utf8' });

test('훅: 내용이 같은 Write는 멈추지 않는 거절을 낸다', () => {
  const result = runHook(JSON.stringify(write('{}\n')));
  assert.equal(result.status, 0);
  const { hookSpecificOutput } = JSON.parse(result.stdout);
  assert.equal(hookSpecificOutput.hookEventName, 'PermissionRequest');
  assert.equal(hookSpecificOutput.decision.behavior, 'deny');
  assert.equal(hookSpecificOutput.decision.interrupt, false);
  assert.ok(hookSpecificOutput.decision.message.startsWith(MARK));
  assert.equal(readFileSync(FILE, 'utf8'), '{}\n');
});

test('훅: 내용이 다른 Write는 아무것도 내지 않는다', () => {
  const result = runHook(JSON.stringify(write('{ "semi": false }\n')));
  assert.equal(result.status, 0);
  assert.equal(result.stdout, '');
});

test('훅: 읽을 수 없는 입력은 아무것도 내지 않는다', () => {
  const result = runHook('not json');
  assert.equal(result.status, 0);
  assert.equal(result.stdout, '');
});

test('hooks.json: Write의 PermissionRequest에 있는 스크립트를 건다', () => {
  const { hooks } = JSON.parse(readFileSync(HOOKS_JSON, 'utf8'));
  const [entry] = hooks.PermissionRequest;
  assert.equal(entry.matcher, 'Write');
  const [, relative] = entry.hooks[0].command.match(/\$\{CLAUDE_PLUGIN_ROOT\}\/([^"]+)/);
  assert.ok(existsSync(fileURLToPath(new URL(`../${relative}`, import.meta.url))));
});
