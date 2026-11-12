---
description: 부른 쪽이 바뀐 것, 이유, 알아둘 것을 길게 넘겨도 Summary 첫 문장은 하나이고 Why·Notes는 3개 이하로 고르는지 확인 (--scaffold 필요)
max_turns: 30
allowed_tools: [Read, Glob, Grep, Skill, Bash]
---

/git-kit:pr-writer --auto greet 유틸 추가 작업이야. 바뀐 것: src/greet.ts에 greet(name) 함수를 추가함, 반환값은 "Hello, <name>" 형식임, 이름이 비어 있으면 그대로 "Hello, "를 돌려줌, test.sh로 반환 형식을 확인함, README에 Usage 절을 더함, Usage 예시에 결과값을 주석으로 적음. 이유: 인사말을 만드는 코드가 화면마다 따로 있었음, 문구가 화면마다 조금씩 달랐음, 새 화면을 만들 때마다 복사해 썼음, 문구를 바꾸려면 여러 곳을 고쳐야 했음. 알아둘 것: 함수 이름은 greet로 정함(makeGreeting, hello도 생각했음), 빈 이름을 거르지 않음, 다국어는 다루지 않음, README 예시는 한 줄뿐임. 확인: test.sh를 돌려 1 passed.
