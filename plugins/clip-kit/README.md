# clip-kit

웹 링크의 원문을 본문 HTML과 전체 캡처로 저장하고, 저장한 클립을 찾고 실패를 관리하는 스킬 모음입니다. 브라우저와 파이썬 스크립트를 쓰므로 Claude Code에서 동작합니다.

## 스킬

| 스킬 | 설명 | 호출 |
|---|---|---|
| link-clipper | 링크나 브라우저에서 저장한 HTML 파일을 본문 HTML과 전체 캡처(PNG)로 저장하고 `clip-log.md`에 기록합니다 | `/clip-kit:link-clipper` 또는 "이 링크 클리핑해줘" |
| finder | 저장한 클립의 내용을 검색하고, 날짜·사이트·요약 여부로 찾고, 실패한 링크를 보여줍니다. 클립이 적어도 이 스킬로 찾습니다. 읽기만 합니다 | `/clip-kit:finder` 또는 "리액트 다룬 클립 찾아줘" |
| retry-clipper | 실패한 링크를 분류해 보여주고, 골라서 다시 클리핑하거나 재시도 대상에서 제외합니다 | `/clip-kit:retry-clipper` 또는 "실패한 클립 다시 해줘" |
| profile-cleaner | 클리핑 전용 Chrome 프로필을 지웁니다. 확인 화면이 계속 반복될 때만 쓰는 비상용입니다 | `/clip-kit:profile-cleaner` (직접 호출만) |

## 설치

```
/plugin install clip-kit --marketplace GANGYIKIM/gangyi-marketplace
```

요약 기능을 위해 `note-kit`이 함께 설치됩니다. link-clipper에는 다음 프로그램이 필요합니다. 없으면 처음 클리핑할 때 Claude가 설치할지 묻습니다.

```bash
python3 -m pip install --user playwright readability-lxml lxml_html_clean
python3 -m playwright install chromium
```

[Google Chrome](https://www.google.com/chrome/)도 설치해 두기를 권합니다. 막힌 사이트를 Chrome 창으로 다시 열 때 씁니다.

## 사용할 때 알아 둘 것

- 막힌 사이트를 다시 열 때 Chrome 창이 뜹니다. 확인 버튼이 보이면 직접 눌러 주시고, 그 창에서 다른 입력은 하지 마세요.
- 그래도 막히면 브라우저에서 페이지를 저장(⌘+S)한 HTML 파일을 주거나 `clips/inbox/`에 넣으면 클리핑할 수 있습니다.
- Chrome 창은 클리핑 전용 프로필(`~/.cache/link-clipper/chrome-profile`)을 써서 확인을 통과한 쿠키가 남습니다. 평소에는 지우지 않는 편이 좋습니다.
- 스크립트는 자동화된 브라우저라는 표시를 줄여서 페이지를 엽니다. 사이트에 따라 이용 약관에 어긋날 수 있으니, 직접 볼 수 있는 페이지를 개인 보관용으로 클리핑하는 데만 쓰세요.

## 테스트

플러그인 폴더에서 실행합니다.

```bash
claude plugin eval . --scaffold --allow-tools Bash Write --ablation none   # Claude의 판단 (사용량 차감)
python3 tests/test_tools.py && python3 tests/test_clipper.py              # 스크립트 동작
```

평가는 스킬이 실행됐는지를 각 스킬의 스크립트(`clipper.py`, `finder.py`, `failures.py`)를 실행했는지로 판단합니다. 평가 환경의 Claude가 스킬을 `Skill` 도구 대신 SKILL.md 파일을 직접 읽어 불러오기 때문입니다. Claude Code가 바뀌면 이 방식이 맞는지 다시 확인하세요.
