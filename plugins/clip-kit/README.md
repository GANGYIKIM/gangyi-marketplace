# clip-kit

웹 링크의 원문을 본문 HTML과 전체 캡처로 저장하고 기록하는 스킬 모음입니다. 브라우저와 파이썬 스크립트를 쓰므로 Claude Code에서 동작합니다.

## 스킬

| 스킬 | 설명 | 호출 |
|---|---|---|
| link-clipper | 링크의 원문을 본문만 추린 HTML과 페이지 전체 캡처(PNG)로 저장하고, 결과를 `clip-log.md`에 기록합니다 | `/clip-kit:link-clipper` 또는 "이 링크 클리핑해줘" |

## 설치

```
/plugin install clip-kit --marketplace GANGYIKIM/gangyi-marketplace
```

요약 기능을 쓰기 위해 `note-kit`이 함께 설치됩니다.

### 필요한 프로그램

Python 3과 아래 패키지가 필요합니다. 처음 클리핑할 때 설치되어 있지 않으면 Claude가 설치 명령을 보여주고 설치할지 묻습니다. 직접 설치하려면 다음을 실행하세요.

```bash
python3 -m pip install --user playwright readability-lxml lxml_html_clean
python3 -m playwright install chromium
```

- `playwright`: 브라우저로 페이지를 열고 전체 캡처를 찍습니다. Homebrew 없이 pip로 설치되고, 두 번째 명령이 브라우저(Chromium)를 내려받습니다.
- `readability-lxml`, `lxml_html_clean`: 페이지에서 본문만 추립니다.

## 저장 구조

```
clips/
├── clip-log.md                  ← 클리핑 기록 (날짜, 링크, 결과, 실패 사유)
├── links.md                     ← 클리핑할 링크 대기열 (처리 후 삭제)
└── react-19-stable-release/
    ├── react-19-stable-release.html
    ├── react-19-stable-release.png
    └── archive/                 ← 갱신할 때 이전 클립을 저장일과 함께 보관
```

기본 위치는 `clips/`이며, 요청에서 위치를 말하거나 프로젝트 CLAUDE.md에 규칙을 적으면 그 위치를 씁니다.

## 테스트

`evals/`에 [claude plugin eval](https://code.claude.com/docs/en/plugin-evals) 형식의 평가 케이스가 있습니다. 플러그인 폴더에서 실행합니다.

```bash
claude plugin eval . --scaffold --allow-tools Bash Write
```

`clip-saves-and-logs` 케이스는 실제 웹페이지에 접속하므로 인터넷 연결과 위 패키지가 필요합니다.
