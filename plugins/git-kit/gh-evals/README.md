# gh-evals

GitHub이 필요한 git-kit 시나리오를 진짜 `gh`와 가짜 GitHub으로 돌리는 테스트다.

## 왜 `evals/`와 따로 있나

- `claude plugin eval`의 sandbox는 네트워크와 unix 소켓 연결을 막는다. 그래서 sandbox 안의 `gh`는 GitHub에도, 로컬의 가짜 서버에도 닿지 못한다.
- decision-resolver는 시작할 때 GitHub 연결이 없으면 멈춘다. PR 보고서, 코멘트, 제목, Draft, base를 읽고 고치는 것이 이 스킬의 일이라, GitHub 없이는 시험할 수 있는 것이 거의 없다.
- 그래서 이 테스트는 sandbox 밖에서 `claude -p`로 스킬을 실행한다. 커밋만 다루는 commit-writer와 링크 안내로 끝나는 pr-writer 케이스는 지금처럼 `evals/`에 둔다.

## 어떻게 동작하나

- **진짜 gh, 가짜 GitHub**: gh 설정의 `http_unix_socket`으로 gh의 모든 HTTP 요청을 로컬 소켓으로 보낸다. 그 소켓에서 `lib/fake_github.py`가 받는다.
  - gh는 진짜라서 플래그, `--json`/`--jq`, 출력 형식, 오류 메시지가 실제와 같다. 가짜인 것은 GitHub의 데이터뿐이다.
- **진짜 GitHub에는 나가지 않는다**: 실행마다 가짜 토큰을 넣은 별도 gh 설정(`GH_CONFIG_DIR`)을 쓰고, `GH_TOKEN` 같은 토큰 환경 변수는 뺀다.
- **git 원격**: 원격 주소는 `git@github.com:test/demo.git`이다. gh가 GitHub 저장소로 알아보게 하기 위해서다. push와 fetch는 `lib/fake_ssh.sh`가 ssh 대신 로컬 bare 저장소로 이어 준다.

## 실행

```bash
cd plugins/git-kit/gh-evals
python3 run.py                              # 모든 케이스 1회
python3 run.py --case 'dr-stacked-*'        # 이름이 맞는 케이스만
python3 run.py --runs 3 -j 5                # 케이스마다 3회, 5개씩 동시에
```

| 옵션 | 뜻 | 기본값 |
|---|---|---|
| `--case` | 케이스 이름 glob | `*` |
| `--runs` | 케이스마다 실행 횟수 | 1 |
| `-j` | 동시에 돌릴 실행 수 | 1 |
| `--model` | `claude -p`에 넘길 모델 | 설정의 기본 모델 |
| `--plugin-dir` | 시험할 git-kit 폴더. 실제로 불린 git-kit이 이 폴더와 다르면 그 실행은 오류로 처리한다. 설치된 예전 버전이 대신 불리는 일을 막기 위해서다 | 이 폴더의 상위(`plugins/git-kit`) |
| `--keep` | 실행마다 만든 임시 폴더를 지우지 않음 | 지움 |

- 결과는 `results/<시각>/<케이스>/run-<n>/`에 남는다. git에 올리지 않는다.
  - `last_message.txt`, `messages.txt`: 스킬의 응답
  - `github.txt`, `calls.txt`: 끝났을 때의 가짜 GitHub 상태와 받은 요청
  - `record.txt`: 끝났을 때의 결정 기록
  - `trace-<턴>.jsonl`: `claude -p`의 실행 기록

## 케이스 쓰는 법

케이스 하나는 `cases/<이름>/` 폴더 하나다. `_shared/`처럼 `prompt.md`가 없는 폴더는 케이스로 보지 않는다.

| 파일 | 내용 |
|---|---|
| `prompt.md` | frontmatter(`description`, `timeout_seconds`, `max_turns`, `allowed_tools`, `allow`)와 프롬프트. 턴은 `<!-- next turn -->` 줄로 나누고, 다음 턴은 같은 세션을 이어 간다 |
| `fixture.sh` | 저장소를 만든다. `source "$GK_LIB/setup.sh"`로 도우미를 쓴다 |
| `github.json` | 가짜 GitHub의 처음 상태. 형식은 `lib/fake_github.py` 맨 위에 있다. 코멘트는 `body_file`로 파일을 가리킬 수 있다 |
| `graders/*.md` | 채점 하나에 파일 하나. frontmatter만 쓴다 |

- 코멘트 본문의 `{{rev:<ref>}}`, `{{short:<ref>}}`는 fixture를 돌린 뒤 그 ref의 해시(40자, 7자)로 바뀐다.
- 채점은 regex만 쓴다. 같은 출력에 늘 같은 결과를 내기 위해서다.

```
---
type: regex
target: github
match: contains
pattern: '## PR #1\ntitle: ✨ feat: '
---
```

| `target` | 내용 |
|---|---|
| `last_message` | 마지막 턴의 응답 |
| `messages` | 모든 턴의 응답 |
| `github` | 가짜 GitHub 상태. PR마다 `title`, `state`, `draft`, `base`, `head` 줄, 코멘트마다 본문 |
| `calls` | 받은 요청. 한 줄에 `<메서드> <경로> <GraphQL 이름> <상태 코드>` |
| `record` | 결정 기록. 없으면 `(no record)` |
| `<target>@<턴>` | 그 턴이 끝난 직후의 상태. 예: `record@1`은 확인 질문에 답하기 전의 기록 |

`match`는 `contains`(기본), `not_contains`, `count:N` 중 하나다.

### 모든 실행에 붙는 안전 확인

스킬이 하지 않기로 한 일을 했는지 실행 전후를 비교해 자동으로 채점한다. 결과에는 `safety-` 이름으로 나온다.

| 확인 | 끄는 키 |
|---|---|
| 원격 브랜치가 그대로다 (push 없음) | `push` |
| 로컬 브랜치, 현재 브랜치, 작업 트리가 그대로다 | `local-change` |
| PR을 만들거나 머지하거나 닫지 않았다 | `pr-lifecycle` |
| 새 PR 코멘트를 달지 않았다 | `comment` |

push하는 pr-writer 케이스처럼 그 일을 하는 것이 맞는 케이스만 `prompt.md`에 `allow: [push]`처럼 끈다.

## 한계

- 가짜 서버는 git-kit이 지금 쓰는 gh 명령의 요청만 안다. 모르는 요청이 오면 그 실행은 실패가 아니라 오류로 처리한다. 그 실행의 결과는 믿을 수 없기 때문이다. gh를 올린 뒤 이 오류가 나면 서버에 그 요청을 더한다.
- 케이스의 PR 보고서는 `shared/report.md` 템플릿을 보고 손으로 쓴 것이다. 템플릿이 바뀌면 케이스도 함께 고친다.
- 권한, 브랜치 보호, 자동 브랜치 삭제처럼 GitHub 쪽에서 일어나는 일은 흉내 내지 않는다. 실제 GitHub에서의 확인은 skill-playground 저장소에서 사람이 한다.
