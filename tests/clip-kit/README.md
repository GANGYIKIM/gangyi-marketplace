# clip-kit 스크립트 테스트

link-clipper의 도우미 스크립트(`clipper.py`)를 확인하는 개발용 테스트입니다. 로컬 테스트 서버를 띄워 상황별로 스크립트를 실행하므로, 실제 웹사이트에 접속하지 않고 Claude 사용량도 들지 않습니다.

플러그인 폴더 밖에 있어서 플러그인을 설치하는 사람에게는 전달되지 않습니다. Claude의 행동을 채점하는 평가 케이스는 `plugins/clip-kit/evals/`에 따로 있습니다.

## 실행

저장소 최상단에서 실행합니다.

```bash
python3 tests/clip-kit/test_clipper.py -v
```

clip-kit README의 "필요한 프로그램"이 설치되어 있어야 합니다. `clipper.py`를 고친 뒤에는 커밋하기 전에 한 번 돌려 보세요.

## 확인하는 상황

| 테스트 | 확인하는 것 |
|---|---|
| plain article / 404 | 정상 페이지는 화면 없는 브라우저로 끝나고, 404는 재시도 없이 실패 |
| short redirect / wander | 서버 리다이렉트로 다른 사이트에 도착하는 건 정상, 열린 뒤 다른 사이트로 이동하면 실패 |
| UA block | User-Agent만 보고 막는 사이트가 화면 없는 브라우저로 열림 |
| auto challenge | 자동 JS 챌린지가 풀릴 때까지 기다렸다가 진짜 페이지를 저장 |
| stuck challenge | 풀리지 않는 챌린지는 "확인 시간 초과"로 실패하고 저장한 HTML 경로를 안내 |
| denied | "Access denied" 같은 확정 차단은 챌린지로 보지 않고 기다리지 않음 |
| webdriver flag | Chrome 창에서 자동화 표시(`navigator.webdriver`)가 꺼져 있음 |
| profile cookies | Chrome 전용 프로필에 쿠키가 남아 다음 실행에서 재방문으로 인식됨 |
| clear profile | 비상용 `clear-profile`이 프로필을 지움 |
| saved file / inbox | 저장한 HTML의 원문 주소 찾기, 주소가 없을 때 알림, inbox 목록과 삭제 |

Chrome 창이 필요한 두 테스트(webdriver flag, profile cookies)는 Google Chrome이 없거나 화면을 띄울 수 없는 환경에서 건너뜁니다. 실행 중에 Chrome 창이 잠깐 떴다가 닫히는데, **창이 떠 있는 동안 키보드를 건드리지 마세요.** 새로 뜬 창이 입력을 가져가서 테스트 페이지가 다른 곳으로 이동할 수 있습니다.

테스트는 임시 폴더의 프로필을 쓰므로 평소 클리핑에 쓰는 프로필(`~/.cache/link-clipper/chrome-profile`)에는 영향을 주지 않습니다.
