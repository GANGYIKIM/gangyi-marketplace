#!/usr/bin/env python3
"""link-clipper 도우미 스크립트(clipper.py) 테스트.

로컬 테스트 서버를 띄워 상황별로 clipper.py를 실행하고 결과 JSON을 확인한다.
실제 웹사이트에 접속하지 않으므로 사용량이 들지 않고 결과가 매번 같다.

    python3 tests/clip-kit/test_clipper.py        # 전체
    python3 tests/clip-kit/test_clipper.py -v     # 케이스 이름까지 출력

Chrome 창이 필요한 테스트는 Google Chrome이 없거나 화면을 띄울 수 없으면 건너뛴다.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLIPPER = ROOT / "plugins" / "clip-kit" / "skills" / "link-clipper" / "scripts" / "clipper.py"

# 테스트에서는 대기 시간을 줄여 풀리지 않는 챌린지도 빨리 끝나게 한다.
TEST_WAIT_MS = "6000"
BODY = " ".join(["This article body is long enough to pass the minimum length check of the clipper."] * 10)


def article(title, extra=""):
    return (f'<html lang="en"><head><title>{title}</title></head><body><article><h1>{title}</h1>'
            f'<p>{extra}</p><p>{BODY}</p></article></body></html>').encode()


CHALLENGE_AUTO = b"""<html><head><title>Just a moment...</title></head><body><p>Checking your browser</p>
<script>setTimeout(function(){document.cookie='cleared=1; path=/'; location.reload();}, 1500);</script>
</body></html>"""
CHALLENGE_STUCK = b"<html><head><title>Just a moment...</title></head><body><p>Checking your browser</p></body></html>"
DENIED = b"<html><head><title>Access denied</title></head><body><p>Access denied</p></body></html>"
WEBDRIVER_PAGE = (b"""<html><head><title>Webdriver Check</title></head><body><article><h1>Webdriver Check</h1>
<p id="w"></p><p>""" + BODY.encode() + b"""</p></article>
<script>document.getElementById('w').textContent = 'webdriver=' + navigator.webdriver;</script></body></html>""")


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body, headers=None):
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        ua = self.headers.get("User-Agent", "")
        cookie = self.headers.get("Cookie", "")
        path = self.path.split("?")[0]
        if path == "/article":
            return self.send(200, article("Plain Article"))
        if path == "/gone":
            return self.send(404, b"not found")
        if path == "/ua-block":  # User-Agent만 보고 화면 없는 브라우저를 막는 사이트
            return self.send(403, DENIED) if "HeadlessChrome" in ua else self.send(200, article("UA Gate"))
        if path == "/challenge-auto":  # 자동 JS 챌린지: 쿠키를 받으면 통과
            return self.send(200, article("Challenge Passed")) if "cleared=1" in cookie \
                else self.send(503, CHALLENGE_AUTO)
        if path == "/challenge-stuck":  # 사람이 눌러야 하는 챌린지(테스트에서는 아무도 누르지 않음)
            return self.send(403, CHALLENGE_STUCK)
        if path == "/denied":  # 기다려도 풀리지 않는 확정 차단
            return self.send(403, DENIED)
        if path == "/remember":  # 쿠키가 남아 있으면 재방문으로 알아봄
            if "seen=1" in cookie:
                return self.send(200, article("Remember Page", "returning visitor"))
            return self.send(200, article("Remember Page", "first visit"),
                             {"Set-Cookie": "seen=1; Path=/; Max-Age=3600"})
        if path == "/webdriver":
            return self.send(200, WEBDRIVER_PAGE)
        port = self.server.server_address[1]
        if path == "/short":  # 짧은 주소처럼 서버가 다른 사이트로 보내는 리다이렉트
            self.send_response(302)
            self.send_header("Location", f"http://localhost:{port}/article")
            self.end_headers()
            return
        if path == "/wander":  # 열린 뒤 스크립트가 다른 사이트로 이동시키는 페이지
            hop = (f"<script>setTimeout(function(){{location.href='http://localhost:{port}/article';}}, 800);"
                   "</script>").encode()
            return self.send(200, article("Wander Page").replace(b"</body>", hop + b"</body>"))
        return self.send(404, b"unknown")

    def log_message(self, *a):
        pass


def chrome_usable():
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        return False
    res = run_clipper("check")
    return bool(res.get("chrome_installed"))


def run_clipper(*args, env_extra=None, timeout=240):
    env = dict(os.environ, CLIPPER_CHALLENGE_WAIT_MS=TEST_WAIT_MS, CLIPPER_MANUAL_CHALLENGE_WAIT_MS=TEST_WAIT_MS)
    env.update(env_extra or {})
    proc = subprocess.run([sys.executable, str(CLIPPER), *args], capture_output=True, text=True,
                          timeout=timeout, env=env)
    line = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "{}"
    return json.loads(line)


class ClipperTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.work = Path(tempfile.mkdtemp(prefix="clipper-test-"))
        cls.profile = cls.work / "profile"
        cls.chrome = chrome_usable()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        shutil.rmtree(cls.work, ignore_errors=True)

    def fetch(self, path, *extra):
        out_dir = tempfile.mkdtemp(dir=self.work)
        return run_clipper("fetch", self.base + path, "--out", out_dir, *extra,
                           env_extra={"CLIPPER_PROFILE_DIR": str(self.profile)})

    # ---------------------------------------------------------------- 기본
    def test_plain_article_uses_headless(self):
        r = self.fetch("/article")
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["method"], "headless")

    def test_404_fails_without_retry(self):
        r = self.fetch("/gone")
        self.assertFalse(r["ok"])
        self.assertEqual(r["category"], "페이지 없음")
        self.assertNotIn("chrome_tried", r)

    # ---------------------------------------------------------------- 다른 사이트로 이동
    def test_server_redirect_to_other_site_is_allowed(self):
        r = self.fetch("/short")
        self.assertTrue(r["ok"], r)
        self.assertIn("localhost", r["final_url"])

    def test_wandering_to_other_site_fails(self):
        r = self.fetch("/wander")
        self.assertFalse(r["ok"], r)
        self.assertIn("다른 사이트로 이동", r["detail"])
        self.assertTrue(r["retryable"])

    # ---------------------------------------------------------------- D3: User-Agent
    def test_ua_block_passes_in_headless(self):
        r = self.fetch("/ua-block")
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["method"], "headless")

    # ---------------------------------------------------------------- D1: 챌린지 대기
    def test_auto_challenge_is_waited_out(self):
        r = self.fetch("/challenge-auto")
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["method"], "headless")
        self.assertEqual(r["title"], "Challenge Passed")

    def test_stuck_challenge_times_out(self):
        r = self.fetch("/challenge-stuck")
        self.assertFalse(r["ok"])
        self.assertIn("확인 시간 초과", r["detail"])
        self.assertTrue(r["retryable"])
        self.assertIn("hint", r)

    def test_denied_is_not_treated_as_challenge(self):
        started = time.monotonic()
        r = self.fetch("/denied")
        self.assertFalse(r["ok"])
        self.assertIn("403", r["detail"])
        self.assertNotIn("확인 시간 초과", r["detail"])
        if not self.chrome:  # Chrome 재시도가 없으면 기다리지 않고 바로 끝나야 한다
            self.assertLess(time.monotonic() - started, int(TEST_WAIT_MS) / 1000)

    # ---------------------------------------------------------------- D2, D3: Chrome 창
    def test_chrome_hides_webdriver_flag(self):
        if not self.chrome:
            self.skipTest("Google Chrome이 없거나 화면을 띄울 수 없음")
        r = self.fetch("/webdriver", "--headed")
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["method"], "chrome")
        self.assertIn("webdriver=false", r["text_preview"])

    def test_chrome_profile_keeps_cookies(self):
        if not self.chrome:
            self.skipTest("Google Chrome이 없거나 화면을 띄울 수 없음")
        first = self.fetch("/remember", "--headed")
        second = self.fetch("/remember", "--headed")
        self.assertIn("first visit", first["text_preview"], first)
        self.assertIn("returning visitor", second["text_preview"], second)

    def test_clear_profile(self):
        self.profile.mkdir(parents=True, exist_ok=True)
        (self.profile / "marker").write_text("x")
        r = run_clipper("clear-profile", env_extra={"CLIPPER_PROFILE_DIR": str(self.profile)})
        self.assertTrue(r["ok"] and r["removed"], r)
        self.assertFalse(self.profile.exists())

    # ---------------------------------------------------------------- 저장한 HTML 파일
    def test_saved_file_with_canonical(self):
        f = self.work / "saved.html"
        f.write_text(f'<html><head><title>Saved</title><link rel="canonical" href="{self.base}/article">'
                     f'</head><body><article><p>{BODY}</p></article></body></html>')
        r = run_clipper("fetch-file", str(f), "--out", tempfile.mkdtemp(dir=self.work))
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["url"], f"{self.base}/article")

    def test_saved_file_without_url_asks(self):
        f = self.work / "nourl.html"
        f.write_text(f"<html><head><title>No URL</title></head><body><p>{BODY}</p></body></html>")
        r = run_clipper("fetch-file", str(f), "--out", tempfile.mkdtemp(dir=self.work))
        self.assertEqual(r.get("error"), "url_missing", r)

    def test_inbox_and_discard(self):
        root = self.work / "clips"
        box = root / "inbox"
        (box / "page_files").mkdir(parents=True)
        (box / "page.html").write_text('<!-- saved from url=(0021)https://example.com/ -->\n<html></html>')
        (box / "page_files" / "a.css").write_text("body{}")
        listed = run_clipper("inbox", "--root", str(root))
        self.assertEqual(listed["count"], 1)
        self.assertEqual(listed["files"][0]["url"], "https://example.com/")
        removed = run_clipper("discard", str(box / "page.html"))
        self.assertEqual(len(removed["removed"]), 2)
        self.assertFalse((box / "page_files").exists())


if __name__ == "__main__":
    unittest.main()
