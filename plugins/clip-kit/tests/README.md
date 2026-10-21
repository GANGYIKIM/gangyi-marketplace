# clip-kit 스크립트 테스트

스킬의 도우미 스크립트가 제대로 동작하는지 확인합니다. Claude 사용량이 들지 않습니다. Claude의 판단을 확인하는 평가 케이스는 `evals/`에 있습니다.

clip-kit 플러그인 폴더에서 실행합니다.

```bash
python3 tests/test_tools.py -v     # finder, retry-clipper, profile-cleaner (몇 초)
python3 tests/test_clipper.py -v   # link-clipper (로컬 테스트 서버, 약 1분)
```

- `test_clipper.py`는 clip-kit README의 필요한 프로그램이 설치되어 있어야 합니다. Google Chrome이 없거나 화면을 띄울 수 없으면 Chrome 창이 필요한 테스트는 건너뜁니다.
- Chrome 창이 떠 있는 동안에는 키보드를 건드리지 마세요. 새 창이 입력을 가져가 테스트 페이지가 다른 곳으로 이동할 수 있습니다.
- 테스트는 임시 폴더만 쓰므로 실제 클립이나 클리핑 전용 프로필에는 영향을 주지 않습니다.
