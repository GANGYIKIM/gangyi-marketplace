#!/usr/bin/env python3
"""link-clipper 도우미 스크립트.

모든 하위 명령은 결과를 JSON 한 줄로 출력한다. Claude는 이 출력만 보고 다음 단계를 정한다.

  check                              필요한 패키지와 브라우저가 있는지 확인
  links FILE                         파일에서 링크를 뽑아 중복 없이 나열
  find URL --root CLIPS              같은 원문 주소의 클립이 이미 있는지 찾기
  fetch URL --out TMPDIR [--headed]  페이지를 열어 본문 HTML(clip.html)과 전체 캡처(clip.png) 저장.
                                     챌린지 화면이면 풀릴 때까지 기다리고, 403·봇 차단이면
                                     설치된 Chrome 창(전용 프로필)으로 한 번 더 시도.
                                     --headed는 처음부터 Chrome 창으로 연다
  fetch-file FILE --out TMPDIR [--url URL]
                                     브라우저에서 저장한 HTML 파일로 같은 결과물을 만든다
  inbox --root CLIPS                 <root>/inbox/의 HTML 파일과 파일별 원문 주소 나열
  discard FILE                       처리한 파일과 함께 저장된 <이름>_files 폴더를 지운다
  place --tmp TMPDIR --root CLIPS --name NAME
                                     임시 결과를 <root>/<slug>/로 옮기고, 같은 원문의 이전 클립은 archive/로 보관
  log --root CLIPS --url URL --result 성공|실패|갱신|제외 [--reason TEXT]
                                     <root>/clip-log.md에 한 줄 추가

의존성: playwright(+ chromium), readability-lxml, lxml_html_clean. 권장: Google Chrome
환경 변수(테스트용): CLIPPER_PROFILE_DIR, CLIPPER_CHALLENGE_WAIT_MS, CLIPPER_MANUAL_CHALLENGE_WAIT_MS
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import time
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "assets" / "clip-template.html"
LOG_NAME = "clip-log.md"
LOG_HEADER = "| 날짜 | 링크 | 결과 | 실패 사유 |\n|---|---|---|---|\n"

# 페이지 로드 제한 시간. 느린 사이트도 대부분 30초 안에 첫 화면을 그린다.
NAV_TIMEOUT_MS = 30_000
# 본문이 이 글자 수보다 짧으면 "본문 없음"으로 본다. 짧은 공지 한 문단 정도가 200자 안팎이다.
MIN_TEXT_LENGTH = 200
# 원래 제목이 이 길이를 넘으면 Claude가 20자 안팎으로 요약한 이름을 정한다.
MAX_NAME_LENGTH = 50
# 지연 로딩 이미지를 불러오기 위해 스크롤하는 최대 횟수. 아주 긴 페이지에서 끝없이 돌지 않게 막는다.
MAX_SCROLL_STEPS = 40
# 스타일시트·이미지가 모두 로드되는 load 이벤트를 기다리는 시간. 느린 CDN도 대부분 이 안에 끝난다.
LOAD_TIMEOUT_MS = 20_000
# 통신이 잠잠해질 때까지 기다리는 시간. 광고·분석 스크립트처럼 계속 통신하는 페이지가 있어 상한을 둔다.
IDLE_TIMEOUT_MS = 10_000
# 캡처 직전 마지막으로 기다리는 시간. 폰트 교체나 애니메이션이 자리 잡을 여유다.
SETTLE_MS = 800

URL_RE = re.compile(r"https?://[^\s<>\"'()\[\]{}|]+")
LOGIN_PATH_RE = re.compile(r"/(login|log-in|signin|sign-in|sign_in|auth|sso|accounts?/login|session)(/|$|\?)", re.I)
BOT_MARKERS = ("cf-chl", "just a moment", "attention required", "captcha", "are you a robot", "access denied")

# 브라우저 환경. 실제 사용 환경(한국, 서울 시간대)과 맞춘다.
VIEWPORT = {"width": 1280, "height": 900}
LOCALE = "ko-KR"
TIMEZONE = "Asia/Seoul"
# Chrome 창 전용 프로필. 확인을 통과한 쿠키가 실행 사이에 남는다.
# 평소 쓰는 Chrome 프로필은 Chrome이 켜져 있으면 잠기므로 쓰지 않는다.
PROFILE_DIR = Path(os.environ.get("CLIPPER_PROFILE_DIR") or Path.home() / ".cache" / "link-clipper" / "chrome-profile")

# 기다리면 풀리는 챌린지 화면의 표지. "access denied" 같은 확정 차단은 넣지 않는다.
CHALLENGE_MARKERS = ("just a moment", "checking your browser", "cf-chl", "challenge-platform",
                     "verify you are human", "잠시만 기다려", "브라우저를 확인")
# 챌린지 화면과 함께 오는 첫 응답 코드.
CHALLENGE_STATUSES = (403, 429, 503)
# 화면 없는 브라우저에서 자동 JS 챌린지가 풀리기를 기다리는 시간. 보통 5초 안에 끝난다.
# 아래 두 값의 환경 변수는 테스트에서 대기 시간을 줄이려는 용도다.
CHALLENGE_WAIT_MS = int(os.environ.get("CLIPPER_CHALLENGE_WAIT_MS", 15_000))
# Chrome 창에서 사용자가 직접 확인 버튼을 누를 때까지 기다리는 시간.
MANUAL_CHALLENGE_WAIT_MS = int(os.environ.get("CLIPPER_MANUAL_CHALLENGE_WAIT_MS", 90_000))
# 챌린지가 풀렸는지 확인하는 간격.
CHALLENGE_POLL_MS = 500


def out(data, code=0):
    print(json.dumps(data, ensure_ascii=False))
    sys.exit(code)


_TMP = None  # fetch가 만든 임시 폴더. 실패하면 지운다.


def fail(category, detail, retryable, **extra):
    if _TMP is not None:
        shutil.rmtree(_TMP, ignore_errors=True)
    data = {"ok": False, "category": category, "detail": detail, "retryable": retryable,
            "reason": f"{category}: {detail} ({'재시도 가능' if retryable else '재시도 불가'})"}
    data.update({k: v for k, v in extra.items() if v is not None})
    out(data)


def today():
    return dt.date.today().isoformat()


# ---------------------------------------------------------------- check
def cmd_check(_):
    missing = []
    try:
        import readability  # noqa: F401
        import lxml_html_clean  # noqa: F401
    except ImportError:
        missing.append("readability-lxml lxml_html_clean")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        missing.append("playwright")
        sync_playwright = None
    browser_ok = chrome_ok = False
    if sync_playwright:
        try:
            with sync_playwright() as p:
                p.chromium.launch().close()
                browser_ok = True
                try:
                    p.chromium.launch(channel="chrome").close()
                    chrome_ok = True
                except Exception:
                    pass
        except Exception:
            pass
    out({"ok": not missing and browser_ok, "missing_packages": missing, "browser_installed": browser_ok,
         "chrome_installed": chrome_ok,
         "profile_dir": str(PROFILE_DIR),
         "chrome_note": None if chrome_ok else
         "막힌 사이트를 Chrome 창으로 다시 시도하려면 Google Chrome이 필요함 (https://www.google.com/chrome/)",
         "install": ["python3 -m pip install --user playwright readability-lxml lxml_html_clean",
                     "python3 -m playwright install chromium"]})


# ---------------------------------------------------------------- links
def cmd_links(a):
    text = Path(a.file).read_text(encoding="utf-8", errors="replace")
    seen, urls = set(), []
    for m in URL_RE.finditer(text):
        u = m.group(0).rstrip(".,;:!?")
        if u not in seen:
            seen.add(u)
            urls.append(u)
    out({"file": a.file, "count": len(urls), "urls": urls})


# ---------------------------------------------------------------- find
def clip_meta(path):
    """클립 HTML에서 원문 주소와 저장일을 읽는다."""
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:4000]
    except OSError:
        return None, None
    src = re.search(r'<meta name="clip:source" content="([^"]*)"', head)
    saved = re.search(r'<meta name="clip:saved" content="([^"]*)"', head)
    return (html.unescape(src.group(1)) if src else None), (saved.group(1) if saved else None)


def norm_url(u):
    return u.strip().rstrip("/")


def find_clip(root, url):
    root = Path(root)
    if not root.is_dir():
        return None
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        main = folder / f"{folder.name}.html"
        if main.exists():
            src, _ = clip_meta(main)
            if src and norm_url(src) == norm_url(url):
                return folder
    return None


def cmd_find(a):
    folder = find_clip(a.root, a.url)
    out({"found": bool(folder), "folder": str(folder) if folder else None})


# ---------------------------------------------------------------- fetch
class ClipFail(Exception):
    """클리핑 실패. blocked=True면 화면 없는 브라우저만 막혔을 수 있어 Chrome으로 다시 시도할 만하다."""

    def __init__(self, category, detail, retryable, blocked=False):
        super().__init__(detail)
        self.category, self.detail, self.retryable, self.blocked = category, detail, retryable, blocked


def classify_exception(msg):
    m = msg.upper()
    if "ERR_NAME_NOT_RESOLVED" in m:
        raise ClipFail("주소 오류", "존재하지 않는 도메인", False)
    if "TIMEOUT" in m:
        raise ClipFail("네트워크", "시간 초과", True)
    if any(k in m for k in ("ERR_CONNECTION", "ERR_INTERNET_DISCONNECTED", "ERR_ADDRESS_UNREACHABLE",
                            "ERR_TUNNEL_CONNECTION_FAILED", "ERR_NETWORK", "ERR_SSL", "ERR_CERT")):
        raise ClipFail("네트워크", "연결 실패", True)
    if "ERR_INVALID_URL" in m or "ERR_FILE_NOT_FOUND" in m:
        raise ClipFail("주소 오류", "잘못된 형식의 주소", False)
    raise ClipFail("도구 오류", f"페이지 열기 실패: {msg.splitlines()[0][:120]}", True)


def classify_status(status, page_text):
    if status in (404, 410):
        raise ClipFail("페이지 없음", str(status), False)
    if status == 401:
        raise ClipFail("접근 제한", "로그인 필요 (401)", False)
    if status == 403:
        low = page_text.lower()
        if any(k in low for k in BOT_MARKERS):
            raise ClipFail("접근 제한", "봇 차단 (403)", False, blocked=True)
        raise ClipFail("접근 제한", "권한 없음 또는 봇 차단 (403)", False, blocked=True)
    if status == 429:
        raise ClipFail("서버 오류", "요청 과다 (429)", True)
    if status >= 500:
        raise ClipFail("서버 오류", str(status), True)
    if status >= 400:
        raise ClipFail("접근 제한", f"HTTP {status}", False)


def wait_for_render(page):
    """스타일시트, 이미지, 웹폰트가 다 로드될 때까지 기다린다. 시간을 넘겨도 그 시점의 화면으로 진행한다."""
    for state, ms in (("load", LOAD_TIMEOUT_MS), ("networkidle", IDLE_TIMEOUT_MS)):
        try:
            page.wait_for_load_state(state, timeout=ms)
        except Exception:
            pass
    try:
        page.evaluate("document.fonts ? document.fonts.ready.then(() => true) : true")
    except Exception:
        pass


def auto_scroll(page):
    """지연 로딩되는 이미지를 불러오려고 페이지 끝까지 천천히 스크롤한 뒤 맨 위로 돌아간다.
    스크롤 도중 페이지가 이동하면 스크롤을 멈추고 새 페이지가 로드되기를 기다린다."""
    try:
        last = -1
        for _ in range(MAX_SCROLL_STEPS):
            height = page.evaluate("document.documentElement.scrollHeight")
            page.evaluate("window.scrollBy(0, window.innerHeight)")
            page.wait_for_timeout(250)
            pos = page.evaluate("window.scrollY + window.innerHeight")
            if pos >= height or pos == last:
                break
            last = pos
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
    except Exception:
        wait_for_render(page)


def read_page(page, fn):
    """페이지가 이동하는 중이면 로드를 기다렸다가 다시 읽는다. 세 번 안에 못 읽으면 예외를 그대로 낸다."""
    for attempt in range(3):
        try:
            return fn()
        except Exception:
            if attempt == 2:
                raise
            wait_for_render(page)


def open_context(p, use_chrome):
    """브라우저 컨텍스트를 연다. (context, closer)를 돌려주며, 다 쓰면 closer.close()를 부른다.

    - Chrome: 설치된 Google Chrome 창을 전용 프로필로 연다. 통과 쿠키가 다음 실행에도 남는다.
    - headless: Playwright의 화면 없는 Chromium. User-Agent의 HeadlessChrome을 Chrome으로 바꾼다.
    둘 다 자동화 표시를 줄이고, 언어·시간대를 실제 사용 환경에 맞춘다.
    """
    common = {"viewport": VIEWPORT, "locale": LOCALE, "timezone_id": TIMEZONE}
    if use_chrome:
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        ctx = p.chromium.launch_persistent_context(
            str(PROFILE_DIR), channel="chrome", headless=False,
            ignore_default_args=["--enable-automation"],
            args=["--disable-blink-features=AutomationControlled"], **common)
        return ctx, ctx
    browser = p.chromium.launch()
    probe = browser.new_page()
    ua = probe.evaluate("navigator.userAgent")
    probe.close()
    ctx = browser.new_context(user_agent=ua.replace("HeadlessChrome", "Chrome"), **common)
    return ctx, browser


def site_of(url):
    """주소의 사이트를 비교용으로 단순화한다. 앞의 www.만 떼고 호스트를 소문자로 쓴다."""
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def same_site(url, base):
    """url이 base와 같은 사이트(또는 그 하위 도메인)인지 본다. file:// 주소는 file:// 끼리만 같다."""
    if base.startswith("file:"):
        return url.startswith("file:")
    a, b = site_of(url), site_of(base)
    return bool(a) and (a == b or a.endswith("." + b) or b.endswith("." + a))


def is_challenge(page):
    """지금 화면이 기다리면 풀리는 챌린지인지 본다. 이동 중이라 읽을 수 없으면 아직 챌린지로 본다."""
    try:
        head = (page.title() + " " + page.content()[:5000]).lower()
    except Exception:
        return True
    return any(k in head for k in CHALLENGE_MARKERS)


def wait_out_challenge(page, timeout_ms, manual):
    """챌린지가 풀릴 때까지 기다린다. 풀리면 True. 안내는 stdout의 JSON을 해치지 않게 stderr로만 낸다."""
    if manual:
        print(f"Chrome 창에 확인 화면이 떴어요. 확인 버튼이 보이면 직접 눌러 주세요 (최대 {timeout_ms // 1000}초).",
              file=sys.stderr, flush=True)
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        try:
            page.wait_for_timeout(CHALLENGE_POLL_MS)
        except Exception:
            time.sleep(CHALLENGE_POLL_MS / 1000)  # 페이지가 바뀌는 중이면 잠시 쉬고 다시 본다
        if not is_challenge(page):
            return True
    return False


def capture(p, target, tmp, use_chrome, from_file=False):
    """target을 열어 렌더링이 끝난 HTML과 전체 캡처(tmp/clip.png)를 얻는다. 실패하면 ClipFail."""
    try:
        ctx, closer = open_context(p, use_chrome)
    except Exception as e:
        what = "Chrome 실행 실패 (Google Chrome이 없거나 창을 띄울 수 없음)" if use_chrome else "브라우저 실행 실패"
        raise ClipFail("도구 오류", f"{what}: {str(e).splitlines()[0][:80]}", True)
    try:
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        base_url = None
        failed_css = []
        nav_statuses = []

        def on_nav_response(res):
            try:
                if res.request.is_navigation_request() and res.frame == page.main_frame:
                    nav_statuses.append(res.status)
            except Exception:
                pass

        def on_css_failed(req):
            if req.resource_type == "stylesheet" and req.url not in failed_css:
                failed_css.append(req.url)

        def on_css_response(res):
            if res.request.resource_type == "stylesheet" and res.status >= 400 and res.url not in failed_css:
                failed_css.append(res.url)

        page.on("requestfailed", on_css_failed)
        page.on("response", on_css_response)
        page.on("response", on_nav_response)
        try:
            resp = page.goto(target, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
        except Exception as e:
            classify_exception(str(e))
        wait_for_render(page)
        # 서버 리다이렉트(짧은 주소 등)를 거쳐 처음 도착한 주소를 기준 사이트로 삼는다
        base_url = resp.url if resp else target
        status = resp.status if resp else 0
        passed_challenge = False
        if not from_file and status in CHALLENGE_STATUSES and is_challenge(page):
            # 챌린지 화면이면 첫 응답으로 판정하지 않고 풀릴 때까지 기다린다
            limit = MANUAL_CHALLENGE_WAIT_MS if use_chrome else CHALLENGE_WAIT_MS
            if not wait_out_challenge(page, limit, manual=use_chrome):
                raise ClipFail("접근 제한", "봇 차단: 확인 시간 초과", True, blocked=True)
            passed_challenge = True
            wait_for_render(page)
            status = nav_statuses[-1] if nav_statuses else status
        if not from_file and not passed_challenge:
            # 챌린지를 통과했다면 마지막 응답 코드가 남아 있어도 화면은 정상이므로 상태로 판정하지 않는다
            body_text = page.inner_text("body") if page.query_selector("body") else ""
            classify_status(status, body_text)
            if LOGIN_PATH_RE.search(urlparse(page.url).path) and not LOGIN_PATH_RE.search(urlparse(target).path):
                raise ClipFail("접근 제한", "로그인 페이지로 이동함", False)
        has_password = read_page(page, lambda: page.query_selector('input[type="password"]')) is not None
        auto_scroll(page)
        wait_for_render(page)  # 스크롤로 새로 불러온 이미지까지 기다린다
        page.wait_for_timeout(SETTLE_MS)
        if not same_site(page.url, base_url):
            # Chrome 창에서 다른 입력을 했거나 스크립트가 다른 사이트로 보냈다. 엉뚱한 페이지를 저장하지 않는다
            raise ClipFail("도구 오류", "클리핑 중 페이지가 다른 사이트로 이동함", True)
        rendered = read_page(page, page.content)
        page_title = read_page(page, page.title)
        lang = read_page(page, lambda: page.evaluate("document.documentElement.lang")) or ""
        if not same_site(page.url, base_url):  # 읽는 사이에 이동했을 수도 있다
            raise ClipFail("도구 오류", "클리핑 중 페이지가 다른 사이트로 이동함", True)
        try:
            page.screenshot(path=str(tmp / "clip.png"), full_page=True)
        except Exception as e:
            raise ClipFail("도구 오류", f"캡처 실패: {str(e).splitlines()[0][:100]}", True)
        return {"rendered": rendered, "page_title": page_title, "lang": lang, "final_url": page.url,
                "status": status, "has_password": has_password, "failed_css": failed_css}
    except ClipFail:
        raise
    except Exception as e:
        # 예상하지 못한 브라우저 오류도 JSON 한 줄 규약을 지키도록 실패로 바꾼다
        try:
            moved = base_url and not same_site(page.url, base_url)
        except Exception:
            moved = False
        if moved:
            raise ClipFail("도구 오류", "클리핑 중 페이지가 다른 사이트로 이동함", True)
        raise ClipFail("도구 오류", f"페이지 처리 실패: {str(e).splitlines()[0][:100]}", True)
    finally:
        closer.close()


def build_clip(tmp, url, cap):
    """렌더링 결과에서 본문을 추려 tmp/clip.html을 만든다. 본문이 없거나 로그인 화면이면 ClipFail."""
    from readability import Document
    doc = Document(cap["rendered"], url=url)
    content = doc.summary(html_partial=True)
    title = (doc.short_title() or cap["page_title"] or urlparse(url).netloc).strip()
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", content)).strip()
    if cap["has_password"] and len(text) < 1500:
        raise ClipFail("접근 제한", "로그인 필요 (로그인 화면)", False)
    if len(text) < MIN_TEXT_LENGTH:
        raise ClipFail("본문 없음", "본문을 거의 뽑지 못함", True)
    saved = today()
    tpl = TEMPLATE.read_text(encoding="utf-8")
    page_html = (tpl.replace("{lang}", html.escape(cap["lang"] or ""))
                    .replace("{title}", html.escape(title))
                    .replace("{url}", html.escape(url))
                    .replace("{saved}", saved)
                    .replace("{content}", content))
    (tmp / "clip.html").write_text(page_html, encoding="utf-8")
    failed = cap["failed_css"]
    return {"ok": True, "url": url, "final_url": cap["final_url"], "status": cap["status"], "title": title,
            "lang": cap["lang"], "title_too_long": len(title) > MAX_NAME_LENGTH,
            "text_length": len(text), "text_preview": text[:300],
            "style_warning": (f"스타일시트 {len(failed)}개를 불러오지 못해 캡처의 모양이 원본과 다를 수 있음"
                              if failed else None),
            "failed_stylesheets": failed[:5],
            "html": str(tmp / "clip.html"), "png": str(tmp / "clip.png")}


def report_fail(e, **extra):
    fail(e.category, e.detail, e.retryable, **extra)


def cmd_fetch(a):
    url = a.url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        fail("주소 오류", "잘못된 형식의 주소", False)
    try:
        from playwright.sync_api import sync_playwright
        import readability  # noqa: F401
    except ImportError:
        fail("도구 오류", "필요한 패키지가 설치되지 않음 (check 명령으로 확인)", True)

    global _TMP
    tmp = Path(a.out)
    tmp.mkdir(parents=True, exist_ok=True)
    _TMP = tmp
    # 평소에는 화면 없는 브라우저로 열고, 403·봇 차단이면 설치된 Chrome 창으로 한 번 더 연다.
    methods = ["chrome"] if a.headed else ["headless", "chrome"]
    block, chrome_error, chrome_tried = None, None, False
    with sync_playwright() as p:
        for method in methods:
            chrome_tried = chrome_tried or method == "chrome"
            try:
                cap = capture(p, url, tmp, use_chrome=(method == "chrome"))
                result = build_clip(tmp, url, cap)
                result["method"] = method
                out(result)
            except ClipFail as e:
                if method == "headless" and e.blocked:
                    block = e
                    continue
                if method == "chrome" and e.category == "도구 오류" and block:
                    chrome_error = e.detail  # Chrome을 띄우지 못하면 원래 막힌 사유를 그대로 알린다
                    break
                block = e  # Chrome으로 시도한 결과가 가장 최근 상태다
                break
    report_fail(block, blocked=block.blocked or None, chrome_tried=chrome_tried or None,
                chrome_error=chrome_error,
                hint=("브라우저에서 페이지를 저장(⌘+S)한 HTML 파일을 주거나 inbox/에 넣으면 클리핑할 수 있음"
                      if block.blocked else None))


# ---------------------------------------------------------------- fetch-file
SAVED_FROM_RE = re.compile(r"<!--\s*saved from url=\(\d+\)(\S+?)\s*-->", re.I)


def detect_source(text):
    """저장한 HTML에서 원문 주소를 찾는다: Chrome의 saved from url 주석 → canonical → og:url."""
    m = SAVED_FROM_RE.search(text[:2000])
    if m and m.group(1).startswith("http"):
        return html.unescape(m.group(1))
    try:
        import lxml.html
        tree = lxml.html.fromstring(text)
        for xp in ('//link[@rel="canonical"]/@href', '//meta[@property="og:url"]/@content'):
            v = tree.xpath(xp)
            if v and v[0].strip().startswith("http"):
                return v[0].strip()
    except Exception:
        pass
    return None


def assets_dir(path):
    """브라우저가 '웹페이지, 전체'로 저장할 때 함께 만드는 이미지·CSS 폴더."""
    return path.with_name(f"{path.stem}_files")


def cmd_fetch_file(a):
    src = Path(a.file).expanduser()
    if not src.is_file() or src.suffix.lower() not in (".html", ".htm"):
        out({"ok": False, "error": "not_html", "detail": "HTML 파일(.html, .htm)이 아님", "file": str(src)}, 1)
    text = src.read_text(encoding="utf-8", errors="replace")
    url = (a.url or "").strip() or detect_source(text)
    if not url:
        out({"ok": False, "error": "url_missing", "detail": "원문 주소를 찾지 못함. --url로 알려 줄 것",
             "file": str(src)}, 1)
    try:
        from playwright.sync_api import sync_playwright
        import readability  # noqa: F401
    except ImportError:
        fail("도구 오류", "필요한 패키지가 설치되지 않음 (check 명령으로 확인)", True)

    global _TMP
    tmp = Path(a.out)
    tmp.mkdir(parents=True, exist_ok=True)
    _TMP = tmp
    if assets_dir(src).is_dir():
        target = src.resolve().as_uri()  # 함께 저장된 이미지·CSS를 상대 경로로 그대로 쓴다
    else:
        # HTML만 저장된 경우: 원래 사이트 주소를 기준으로 이미지·CSS를 불러오도록 <base>를 넣는다
        with_base = re.sub(r"(<head[^>]*>)", lambda m: m.group(1) + f'<base href="{html.escape(url)}">',
                           text, count=1, flags=re.I) if "<base" not in text.lower() else text
        staged = tmp / "source.html"
        staged.write_text(with_base, encoding="utf-8")
        target = staged.resolve().as_uri()
    with sync_playwright() as p:
        try:
            cap = capture(p, target, tmp, use_chrome=False, from_file=True)
            result = build_clip(tmp, url, cap)
        except ClipFail as e:
            report_fail(e)
    (tmp / "source.html").unlink(missing_ok=True)
    result.update({"method": "file", "source_file": str(src)})
    out(result)


# ---------------------------------------------------------------- inbox / discard
def cmd_inbox(a):
    box = Path(a.root) / "inbox"
    files = sorted(f for f in box.glob("*") if f.is_file() and f.suffix.lower() in (".html", ".htm")) \
        if box.is_dir() else []
    items, missing = [], []
    for f in files:
        url = detect_source(f.read_text(encoding="utf-8", errors="replace"))
        items.append({"file": str(f), "url": url})
        if not url:
            missing.append(str(f))
    out({"inbox": str(box), "count": len(items), "files": items, "missing_url": missing})


def cmd_discard(a):
    f = Path(a.file).expanduser()
    if f.suffix.lower() not in (".html", ".htm", ".md", ".txt", ".csv"):
        out({"ok": False, "error": "지울 수 있는 형식이 아님", "file": str(f)}, 1)
    removed = []
    if f.is_file():
        f.unlink()
        removed.append(str(f))
    d = assets_dir(f)
    if d.is_dir():
        shutil.rmtree(d)
        removed.append(str(d))
    out({"ok": True, "removed": removed})


# ---------------------------------------------------------------- place
def slugify(name):
    s = re.sub(r'[\\/:*?"<>|#%{}^~\[\]`]', "", name.strip())
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-.")
    return "".join(c.lower() if c.isascii() else c for c in s)


def archive_existing(folder, slug):
    """폴더의 현재 클립(html, png)을 archive/<slug>-<저장일>[-n].*로 옮긴다."""
    main = folder / f"{slug}.html"
    if not main.exists():
        return []
    _, saved = clip_meta(main)
    saved = saved or dt.date.fromtimestamp(main.stat().st_mtime).isoformat()
    arch = folder / "archive"
    arch.mkdir(exist_ok=True)
    base, n = f"{slug}-{saved}", 1
    while (arch / f"{base}.html").exists() or (arch / f"{base}.png").exists():
        n += 1
        base = f"{slug}-{saved}-{n}"
    moved = []
    for ext in ("html", "png"):
        src = folder / f"{slug}.{ext}"
        if src.exists():
            dst = arch / f"{base}.{ext}"
            shutil.move(str(src), str(dst))
            moved.append(str(dst))
    return moved


def cmd_place(a):
    tmp, root = Path(a.tmp), Path(a.root)
    new_html = tmp / "clip.html"
    if not new_html.exists():
        out({"ok": False, "error": "임시 클립이 없음. fetch를 먼저 실행할 것"}, 1)
    slug = slugify(a.name)
    if not slug:
        out({"ok": False, "error": "이름이 비어 있음"}, 1)
    folder = root / slug
    new_src, _ = clip_meta(new_html)
    main = folder / f"{slug}.html"
    if main.exists():
        old_src, _ = clip_meta(main)
        if old_src and new_src and norm_url(old_src) != norm_url(new_src):
            out({"ok": False, "error": "name-conflict", "slug": slug, "existing_source": old_src,
                 "hint": "다른 원문의 클립이 같은 이름을 쓰고 있음. 이름 뒤에 도메인을 붙여 다시 place할 것"}, 1)
    folder.mkdir(parents=True, exist_ok=True)
    archived = archive_existing(folder, slug)
    shutil.move(str(new_html), str(folder / f"{slug}.html"))
    if (tmp / "clip.png").exists():
        shutil.move(str(tmp / "clip.png"), str(folder / f"{slug}.png"))
    shutil.rmtree(tmp, ignore_errors=True)
    out({"ok": True, "slug": slug, "folder": str(folder), "html": str(folder / f"{slug}.html"),
         "png": str(folder / f"{slug}.png"), "archived": archived, "refreshed": bool(archived)})


# ---------------------------------------------------------------- log
def cmd_log(a):
    root = Path(a.root)
    root.mkdir(parents=True, exist_ok=True)
    log = root / LOG_NAME
    if not log.exists():
        log.write_text(f"# 클리핑 기록\n\n{LOG_HEADER}", encoding="utf-8")
    reason = (a.reason or "").replace("|", "/")
    with log.open("a", encoding="utf-8") as f:
        f.write(f"| {today()} | {a.url} | {a.result} | {reason} |\n")
    out({"ok": True, "log": str(log)})


def main():
    ap = argparse.ArgumentParser(description="link-clipper helper")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    p = sub.add_parser("links"); p.add_argument("file")
    p = sub.add_parser("find"); p.add_argument("url"); p.add_argument("--root", required=True)
    p = sub.add_parser("fetch"); p.add_argument("url"); p.add_argument("--out", required=True)
    p.add_argument("--headed", action="store_true", help="처음부터 설치된 Chrome 창으로 연다")
    p = sub.add_parser("fetch-file"); p.add_argument("file"); p.add_argument("--out", required=True)
    p.add_argument("--url", default="", help="원문 주소. 파일 안에서 찾지 못할 때 지정")
    p = sub.add_parser("inbox"); p.add_argument("--root", required=True)
    p = sub.add_parser("discard"); p.add_argument("file")
    p = sub.add_parser("place"); p.add_argument("--tmp", required=True); p.add_argument("--root", required=True); p.add_argument("--name", required=True)
    p = sub.add_parser("log"); p.add_argument("--root", required=True); p.add_argument("--url", required=True)
    p.add_argument("--result", required=True, choices=["성공", "실패", "갱신", "제외"]); p.add_argument("--reason", default="")
    a = ap.parse_args()
    {"check": cmd_check, "links": cmd_links, "find": cmd_find, "fetch": cmd_fetch, "fetch-file": cmd_fetch_file,
     "inbox": cmd_inbox, "discard": cmd_discard, "place": cmd_place,
     "log": cmd_log}[a.cmd](a)


if __name__ == "__main__":
    main()
