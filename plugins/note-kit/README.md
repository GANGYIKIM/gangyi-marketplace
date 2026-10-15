# note-kit

아이디어, 초안, 요약 등 문서와 노트 작성을 돕는 스킬 모음입니다.

## 스킬

| 스킬 | 설명 | 호출 |
|---|---|---|
| idea-writer | 질문을 하나씩 주고받으며 아이디어를 구체화하고, 사람과 AI가 모두 읽기 쉬운 문서로 정리합니다 | `/note-kit:idea-writer` 또는 "아이디어 정리하고 싶어" |
| summary-writer | 문서를 한국어로 새로 풀어 쓴 요약본을 `summaries/`에 원본과 같은 이름으로 저장합니다 | `/note-kit:summary-writer` 또는 "요약본 만들어줘" |

## 설치

```
/plugin install note-kit --marketplace GANGYIKIM/gangyi-marketplace
```

## 테스트

`evals/`에 [claude plugin eval](https://code.claude.com/docs/en/plugin-evals) 형식의 평가 케이스가 있습니다. 플러그인 폴더에서 실행합니다.

```bash
claude plugin eval . --scaffold --allow-tools Write
```

- `--scaffold`: 기존 문서나 원본 파일을 미리 만들어 두는 케이스(`tags: [fixture]`)에 필요합니다.
- `--allow-tools Write`: summary-writer가 요약 파일을 저장하는 케이스에 필요합니다.
