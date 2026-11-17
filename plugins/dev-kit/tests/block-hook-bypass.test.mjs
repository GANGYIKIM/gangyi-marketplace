// 실행 (저장소 루트에서): node --test "plugins/dev-kit/tests/*.test.mjs"
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { findBypass } from '../skills/harness-builder/assets/block-hook-bypass.mjs';

const SCRIPT = fileURLToPath(new URL('../skills/harness-builder/assets/block-hook-bypass.mjs', import.meta.url));

const HEREDOC_COMMIT = [
  `git commit -m "$(cat <<'EOF'`,
  `docs: don't use "-n" or --no-verify`,
  ``,
  `git commit -n is blocked :)`,
  `EOF`,
  `)"`,
].join('\n');

const BLOCKED_NO_VERIFY = [
  'git commit --no-verify -m "x"',
  'git commit -n -m "x"',
  'git commit -m "x" -n',
  'git commit -nm "x"',
  'git commit -anm "x"',
  'git commit --no-veri -m "x"',
  'git add . && git commit -m "x" --no-verify',
  'cd app; git commit -n',
  'git -C packages/app commit -n',
  'git -c user.name=x commit --no-verify',
  '/usr/bin/git commit -n',
  'bash -c "git commit -n -m x"',
  'bash -lc \'git commit --no-verify\'',
  'eval "git commit -n"',
  'echo $(git commit -n)',
  `${HEREDOC_COMMIT} --no-verify`,
];

const BLOCKED_HUSKY_OFF = [
  'HUSKY=0 git commit -m "x"',
  'HUSKY="0" git commit -m "x"',
  'export HUSKY=0 && git commit -m "x"',
  'export HUSKY=0\ngit add .\ngit commit -m "x"',
  'env HUSKY=0 git commit -m x',
  'FOO=1 HUSKY=0 git -C app commit',
];

const ALLOWED = [
  'git commit -m "x"',
  'git commit -am "x"',
  'git commit',
  'git commit -m "docs: explain --no-verify"',
  'git commit -m "fix -n flag"',
  'git commit -m -n',
  'git commit -mn',
  'git commit --message --no-verify',
  'git commit -uno -m "x"',
  'git commit -m "x" -- -n',
  'git commit -m "x" # -n',
  HEREDOC_COMMIT,
  'git log -n 5',
  'git push -n',
  'git push --no-verify',
  'git clean -n',
  'git merge --no-verify feature',
  'grep -rn "git commit --no-verify" .',
  'echo "git commit -n"',
  'HUSKY=0 npm ci',
  'echo HUSKY=0',
  'HUSKY=1 git commit -m "x"',
  'npm test && git commit -m "x"',
  'cat <<<"git commit -n"',
];

for (const command of BLOCKED_NO_VERIFY) {
  test(`막음(no-verify): ${command.split('\n')[0]}`, () => {
    assert.equal(findBypass(command), 'no-verify');
  });
}

for (const command of BLOCKED_HUSKY_OFF) {
  test(`막음(husky-off): ${command.split('\n')[0]}`, () => {
    assert.equal(findBypass(command), 'husky-off');
  });
}

for (const command of ALLOWED) {
  test(`통과: ${command.split('\n')[0]}`, () => {
    assert.equal(findBypass(command), null);
  });
}

test('문자열이 아니면 통과', () => {
  assert.equal(findBypass(undefined), null);
  assert.equal(findBypass(null), null);
  assert.equal(findBypass(42), null);
});

const runHook = (stdin) => spawnSync('node', [SCRIPT], { input: stdin, encoding: 'utf8' });
const bashInput = (command) => JSON.stringify({ tool_name: 'Bash', tool_input: { command } });

test('훅: 건너뛰는 커밋은 종료 코드 2와 이유', () => {
  const result = runHook(bashInput('git commit -n -m "x"'));
  assert.equal(result.status, 2);
  assert.match(result.stderr, /--no-verify, -n/);
});

test('훅: HUSKY=0 커밋은 종료 코드 2와 이유', () => {
  const result = runHook(bashInput('HUSKY=0 git commit -m "x"'));
  assert.equal(result.status, 2);
  assert.match(result.stderr, /HUSKY=0/);
});

test('훅: 보통 커밋은 종료 코드 0', () => {
  const result = runHook(bashInput('git commit -m "x"'));
  assert.equal(result.status, 0);
  assert.equal(result.stderr, '');
});

test('훅: Bash가 아닌 도구는 통과', () => {
  const result = runHook(JSON.stringify({ tool_name: 'Write', tool_input: { content: 'git commit -n' } }));
  assert.equal(result.status, 0);
});

test('훅: 읽을 수 없는 입력은 통과', () => {
  assert.equal(runHook('not json').status, 0);
  assert.equal(runHook('').status, 0);
});
