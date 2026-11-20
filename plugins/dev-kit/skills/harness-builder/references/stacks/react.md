---
name: react
kind: library
base: js-ts
when: package.json의 의존성에 react가 있음. 새 프로젝트는 고른 프레임워크가 React를 쓸 때
verified: 2026-11-16 (Next.js 16과 Vite 8의 새 프로젝트에 설치)
---

# React

## 조건

### UI

| 조건 | 추천 도구 |
|---|---|
| 접근성 | 린터의 jsx-a11y 규칙 |

조건마다 꼭 지켜야 하는 것:

- **접근성**: jsx-a11y의 recommended 규칙 전체가 error 수준이어야 한다.

### Recommended

| 조건 | 추천 도구 |
|---|---|
| 토큰만 쓰기 | eslint-plugin-better-tailwindcss, React 린트 플러그인 |

조건마다 꼭 지켜야 하는 것:

- **토큰만 쓰기**: 경고할 것은 임의 값 클래스(`text-[#fff]`)와 `style` 속성이다. Tailwind의 기본 색(`text-red-500` 등)은 경고하지 않고, 기본 색을 비우지도 않는다.
