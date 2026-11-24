#!/bin/bash
# 화면이 없는 Python CLI 프로젝트. 이 스택의 스택 파일은 없다.
# 패키지 매니저는 이 컴퓨터에 있는 pip를 쓴다. 없는 도구를 쓰면 셋업이 설치를 안내하고 멈춘다.
set -e
git init -q -b main
git config user.name "eval"
git config user.email "eval@example.com"
cat > pyproject.toml <<'TOML'
[project]
name = "weather-cli"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = ["httpx"]

[project.scripts]
weather = "weather_cli.main:main"

[dependency-groups]
dev = ["pytest"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
TOML
printf 'httpx\npytest\n' > requirements.txt
mkdir -p src/weather_cli tests
printf '' > src/weather_cli/__init__.py
printf 'def describe(temperature: float) -> str:\n    return "warm" if temperature >= 20 else "cold"\n\n\ndef main() -> None:\n    print(describe(21.5))\n' > src/weather_cli/main.py
printf 'from weather_cli.main import describe\n\n\ndef test_describe() -> None:\n    assert describe(25) == "warm"\n' > tests/test_main.py
printf '__pycache__\n.venv\n' > .gitignore
git add . && git commit -q -m "initial commit"
# eval sandbox는 git 전역 설정으로 훅 경로를 /dev/null로 둔다. 보통 저장소처럼 보이게 기본 경로로 돌려놓는다.
git config core.hooksPath .git/hooks
