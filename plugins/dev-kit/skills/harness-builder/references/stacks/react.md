---
name: react
kind: library
base: js-ts
when: package.json의 의존성에 react가 있음. 새 프로젝트는 고른 프레임워크가 React를 쓸 때
verified: 2026-11-16 (Next.js 16과 Vite 8의 새 프로젝트에 설치. dependency-cruiser 17은 TypeScript 7을 읽지 못함)
---

# React

## 고르기의 선택지

| 항목 | 추천값 (이유) | 대안 |
|---|---|---|
| 스타일 | Tailwind CSS (토큰을 CSS 한 곳에 두고 클래스에 검사를 걸 수 있음) | CSS Modules |
| 컴포넌트 자리와 데이터 자리 | `components/`와 `data/` (프로젝트에 `src/`가 있거나 뼈대가 `src/`를 만들면 그 안) | 사람이 말한 폴더 이름 |
| 미리 볼 자리 | 미리 보기 페이지 (설치할 것이 없고 주소만 열면 찍을 수 있음) | Storybook |

## 조건

### UI

| 조건 | 추천 도구 |
|---|---|
| 컴포넌트의 서버 호출·저장 금지 | 린터의 제한 규칙 (`no-restricted-*`) |
| 컴포넌트와 데이터의 분리 | dependency-cruiser |
| 접근성 | 린터의 jsx-a11y 규칙 |
| 화면 찍기 | Playwright의 CLI |

조건마다 꼭 지켜야 하는 것:

- **컴포넌트의 서버 호출·저장 금지**: 막을 것은 세 가지다.
  - 서버 호출 (`fetch` 같은 네트워크 전역)
  - 브라우저 저장소 (`localStorage`, 쿠키 등)
  - 프로젝트가 쓰는 HTTP·DB·데이터 가져오기 라이브러리의 import
- **접근성**: jsx-a11y의 recommended 규칙 전체가 error 수준이어야 한다.
- **미리 볼 자리**: 배포한 앱에서는 열리지 않아야 한다.

### Recommended

| 조건 | 추천 도구 |
|---|---|
| 토큰만 쓰기 | eslint-plugin-better-tailwindcss, React 린트 플러그인 |

조건마다 꼭 지켜야 하는 것:

- **토큰만 쓰기**: 경고할 것은 임의 값 클래스(`text-[#fff]`)와 `style` 속성이다. Tailwind의 기본 색(`text-red-500` 등)은 경고하지 않고, 기본 색을 비우지도 않는다.

## 확인 방법

| 조건 | 위반 예시가 꼭 담아야 하는 것 | 나와야 하는 것 |
|---|---|---|
| 컴포넌트와 데이터의 분리 | 컴포넌트가 데이터 자리의 파일에서 타입만 가져옴. 프로젝트가 경로 별칭을 쓰면 별칭으로 | 실패. 출력에 분리 규칙의 이름 |
