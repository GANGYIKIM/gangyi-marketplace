# note-kit

아이디어, 초안, 요약 등 문서와 노트 작성을 돕는 스킬 모음입니다.

## 스킬

| 스킬 | 설명 | 호출 |
|---|---|---|
| idea-writer | 질문을 하나씩 주고받으며 아이디어를 구체화하고, 사람과 AI가 모두 읽기 쉬운 문서로 정리합니다 | `/note-kit:idea-writer` 또는 "아이디어 정리하고 싶어" |

## 설치

```
/plugin install note-kit --marketplace GANGYIKIM/gangyi-marketplace
```

## 테스트

`evals/`에 [claude plugin eval](https://code.claude.com/docs/en/plugin-evals) 형식의 평가 케이스가 있습니다. 플러그인 폴더에서 실행합니다.

```bash
claude plugin eval . --scaffold
```

`update-reads-latest-version` 케이스는 기존 문서를 미리 만들어 두는 스크립트를 쓰므로 `--scaffold`가 필요합니다.
