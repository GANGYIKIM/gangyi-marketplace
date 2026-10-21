#!/usr/bin/env python3
"""finder, retry-clipper, profile-cleaner의 도우미 스크립트 테스트.

브라우저나 네트워크 없이 임시 폴더에 클립과 기록을 만들어 확인한다. 몇 초 안에 끝난다.

    python3 tests/test_tools.py -v
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
SKILLS = PLUGIN / "skills"
CLIPPER = SKILLS / "link-clipper" / "scripts" / "clipper.py"
FINDER = SKILLS / "finder" / "scripts" / "finder.py"
FAILURES = SKILLS / "retry-clipper" / "scripts" / "failures.py"
PROFILE = SKILLS / "profile-cleaner" / "scripts" / "profile.py"


def run(script, *args, env_extra=None, cwd=None):
    env = dict(os.environ)
    env.pop("CLIPPER_PROFILE_DIR", None)
    env.update(env_extra or {})
    p = subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, env=env, cwd=cwd)
    return json.loads(p.stdout.strip().splitlines()[-1])


def make_clip(root, slug, url, title, saved, body):
    folder = root / slug
    folder.mkdir(parents=True)
    (folder / f"{slug}.html").write_text(
        f'<!DOCTYPE html><html><head><meta name="clip:source" content="{url}">'
        f'<meta name="clip:title" content="{title}"><meta name="clip:saved" content="{saved}"></head>'
        f'<body><dl class="clip-meta"><dd>{title}</dd></dl><article><p>{body}</p></article></body></html>',
        encoding="utf-8")


class ToolsTest(unittest.TestCase):
    def setUp(self):
        self.work = Path(tempfile.mkdtemp(prefix="clip-tools-"))
        self.clips = self.work / "clips"
        make_clip(self.clips, "react-19", "https://react.dev/blog/react-19", "React 19", "2026-10-15",
                  "Server Components are now stable.")
        make_clip(self.clips, "kind-review", "https://www.wanted.co.kr/wd/1", "Kind Review", "2026-10-12",
                  "Keep code review feedback short and kind.")
        (self.work / "summaries").mkdir()
        (self.work / "summaries" / "react-19.md").write_text(
            "# React 19\n\n- 원본 파일: `clips/react-19/react-19.html`\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.work, ignore_errors=True)

    def log(self, *rows):
        lines = ["# 클리핑 기록", "", "| 날짜 | 링크 | 결과 | 실패 사유 |", "|---|---|---|---|"]
        lines += [f"| {d} | {u} | {r} | {why} |" for d, u, r, why in rows]
        (self.clips / "clip-log.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ---------------------------------------------------------------- finder
    def test_finder_keyword_any_match(self):
        r = run(FINDER, "search", "--root", "clips", "--keyword", "서버 컴포넌트", "--keyword", "Server Components",
                "--summaries", "summaries", cwd=self.work)
        self.assertEqual(r["count"], 1)
        self.assertEqual(r["results"][0]["title"], "React 19")
        self.assertTrue(r["results"][0]["summary"])

    def test_finder_site_and_date(self):
        self.assertEqual(run(FINDER, "search", "--root", "clips", "--site", "wanted", cwd=self.work)["count"], 1)
        self.assertEqual(run(FINDER, "search", "--root", "clips", "--since", "2026-10-14", cwd=self.work)["count"], 1)

    def test_finder_no_summary(self):
        r = run(FINDER, "search", "--root", "clips", "--summaries", "summaries", "--no-summary", cwd=self.work)
        self.assertEqual([x["title"] for x in r["results"]], ["Kind Review"])

    def test_finder_failures_hide_excluded(self):
        self.log(("2026-10-15", "https://x.com/a", "실패", "네트워크: 시간 초과 (재시도 가능)"),
                 ("2026-10-16", "https://x.com/b", "제외", "페이지 없음: 404 (재시도 불가)"))
        self.assertEqual(run(FINDER, "failures", "--root", "clips", cwd=self.work)["count"], 1)
        self.assertEqual(run(FINDER, "failures", "--root", "clips", "--include-excluded", cwd=self.work)["count"], 2)

    # ---------------------------------------------------------------- retry-clipper
    def test_status_uses_latest_row(self):
        self.log(("2026-10-15", "https://x.com/a", "실패", "네트워크: 시간 초과 (재시도 가능)"),
                 ("2026-10-15", "https://x.com/b", "실패", "페이지 없음: 404 (재시도 불가)"),
                 ("2026-10-15", "https://x.com/c", "실패", "서버 오류: 503 (재시도 가능)"),
                 ("2026-10-16", "https://x.com/c", "성공", ""))
        r = run(FAILURES, "status", "--root", "clips", cwd=self.work)
        self.assertEqual(r["counts"], {"retryable": 1, "not_retryable": 1, "excluded": 0})

    def test_exclude_appends_and_skips_non_failures(self):
        self.log(("2026-10-15", "https://x.com/a", "실패", "페이지 없음: 404 (재시도 불가)"),
                 ("2026-10-15", "https://x.com/b", "성공", ""))
        r = run(FAILURES, "exclude", "--root", "clips", "--url", "https://x.com/a", "--url", "https://x.com/b",
                cwd=self.work)
        self.assertEqual(r["excluded"], ["https://x.com/a"])
        self.assertEqual(len(r["skipped"]), 1)
        status = run(FAILURES, "status", "--root", "clips", "--include-excluded", cwd=self.work)
        self.assertEqual(status["counts"]["excluded"], 1)

    def test_clipper_log_is_readable_by_failures(self):
        # link-clipper가 쓴 기록을 retry-clipper가 그대로 읽을 수 있어야 한다
        run(CLIPPER, "log", "--root", "clips", "--url", "https://x.com/z", "--result", "실패",
            "--reason", "네트워크: 시간 초과 (재시도 가능)", cwd=self.work)
        r = run(FAILURES, "status", "--root", "clips", cwd=self.work)
        self.assertEqual([x["url"] for x in r["retryable"]], ["https://x.com/z"])

    # ---------------------------------------------------------------- profile-cleaner
    def test_profile_paths_match_clipper(self):
        # 두 스크립트가 같은 기본 프로필을 가리켜야 profile-cleaner가 엉뚱한 곳을 지우지 않는다
        code = ("import importlib.util as u, sys\n"
                "def load(p):\n"
                "    s = u.spec_from_file_location('m', p); m = u.module_from_spec(s); s.loader.exec_module(m); return m\n"
                "print(load(sys.argv[1]).PROFILE_DIR == load(sys.argv[2]).PROFILE_DIR)")
        env = {k: v for k, v in os.environ.items() if k != "CLIPPER_PROFILE_DIR"}
        p = subprocess.run([sys.executable, "-c", code, str(CLIPPER), str(PROFILE)],
                           capture_output=True, text=True, env=env)
        self.assertEqual(p.stdout.strip(), "True", p.stderr)

    def test_profile_show_and_clear(self):
        prof = self.work / "link-clipper" / "chrome-profile"
        (prof / "Default").mkdir(parents=True)
        (prof / "Default" / "marker").write_text("x")
        env = {"CLIPPER_PROFILE_DIR": str(prof)}
        shown = run(PROFILE, "show", env_extra=env)
        self.assertTrue(shown["exists"])
        self.assertFalse(shown["in_use"])
        cleared = run(PROFILE, "clear", env_extra=env)
        self.assertTrue(cleared["ok"] and cleared["removed"], cleared)
        self.assertFalse(prof.exists())

    def test_profile_refuses_when_in_use(self):
        prof = self.work / "link-clipper" / "chrome-profile"
        prof.mkdir(parents=True)
        (prof / "SingletonLock").write_text("")
        r = run(PROFILE, "clear", env_extra={"CLIPPER_PROFILE_DIR": str(prof)})
        self.assertEqual(r.get("error"), "in_use")
        self.assertTrue(prof.exists())

    def test_profile_refuses_personal_chrome(self):
        # 진짜 Chrome 프로필을 건드리지 않도록 가짜 홈 폴더 안에서만 확인한다
        home = self.work / "fake-home"
        personal = home / "Library" / "Application Support" / "Google" / "Chrome"
        personal.mkdir(parents=True)
        r = run(PROFILE, "clear", env_extra={"HOME": str(home), "CLIPPER_PROFILE_DIR": str(personal)})
        self.assertEqual(r.get("error"), "not_clip_profile")
        self.assertTrue(personal.exists())


if __name__ == "__main__":
    unittest.main()
