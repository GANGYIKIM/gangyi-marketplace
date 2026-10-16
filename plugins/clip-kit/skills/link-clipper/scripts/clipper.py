#!/usr/bin/env python3
"""link-clipper 도우미 스크립트.

모든 하위 명령은 결과를 JSON 한 줄로 출력한다. Claude는 이 출력만 보고 다음 단계를 정한다.

  check                              필요한 패키지와 브라우저가 있는지 확인
  links FILE                         파일에서 링크를 뽑아 중복 없이 나열
  find URL --root CLIPS              같은 원문 주소의 클립이 이미 있는지 찾기
  fetch URL --out TMPDIR             페이지를 열어 본문 HTML(clip.html)과 전체 캡처(clip.png) 저장
  place --tmp TMPDIR --root CLIPS --name NAME
                                     임시 결과를 <root>/<slug>/로 옮기고, 같은 원문의 이전 클립은 archive/로 보관
  log --root CLIPS --url URL --result 성공|실패|갱신 [--reason TEXT]
                                     <root>/clip-log.md에 한 줄 추가
  retry-list --root CLIPS            링크별 마지막 기록이 "재시도 가능" 실패인 링크 나열

의존성: playwright(+ chromium), readability-lxml, lxml_html_clean
"""
import argparse
import datetime as dt
import html
import json
import re
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


def out(data, code=0):
    print(json.dumps(data, ensure_ascii=False))
    sys.exit(code)


_TMP = None  # fetch가 만든 임시 폴더. 실패하면 지운다.


def fail(category, detail, retryable):
    if _TMP is not None:
        shutil.rmtree(_TMP, ignore_errors=True)
    out({"ok": False, "category": category, "detail": detail, "retryable": retryable,
         "reason": f"{category}: {detail} ({'재시도 가능' if retryable else '재시도 불가'})"})


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
    browser_ok = False
    if sync_playwright:
        try:
            with sync_playwright() as p:
                p.chromium.launch().close()
            browser_ok = True
        except Exception:
            pass
    out({"ok": not missing and browser_ok, "missing_packages": missing, "browser_installed": browser_ok,
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
def classify_exception(msg):
    m = msg.upper()
    if "ERR_NAME_NOT_RESOLVED" in m:
        fail("주소 오류", "존재하지 않는 도메인", False)
    if "TIMEOUT" in m:
        fail("네트워크", "시간 초과", True)
    if any(k in m for k in ("ERR_CONNECTION", "ERR_INTERNET_DISCONNECTED", "ERR_ADDRESS_UNREACHABLE",
                            "ERR_TUNNEL_CONNECTION_FAILED", "ERR_NETWORK", "ERR_SSL", "ERR_CERT")):
        fail("네트워크", "연결 실패", True)
    if "ERR_INVALID_URL" in m:
        fail("주소 오류", "잘못된 형식의 주소", False)
    fail("도구 오류", f"페이지 열기 실패: {msg.splitlines()[0][:120]}", True)


def classify_status(status, page_text):
    if status in (404, 410):
        fail("페이지 없음", str(status), False)
    if status == 401:
        fail("접근 제한", "로그인 필요 (401)", False)
    if status == 403:
        low = page_text.lower()
        if any(k in low for k in BOT_MARKERS):
            fail("접근 제한", "봇 차단 (403)", False)
        fail("접근 제한", "권한 없음 (403)", False)
    if status == 429:
        fail("서버 오류", "요청 과다 (429)", True)
    if status >= 500:
        fail("서버 오류", str(status), True)
    if status >= 400:
        fail("접근 제한", f"HTTP {status}", False)


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
    """지연 로딩되는 이미지를 불러오려고 페이지 끝까지 천천히 스크롤한 뒤 맨 위로 돌아간다."""
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


def cmd_fetch(a):
    url = a.url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        fail("주소 오류", "잘못된 형식의 주소", False)
    try:
        from playwright.sync_api import sync_playwright
        from readability import Document
    except ImportError:
        fail("도구 오류", "필요한 패키지가 설치되지 않음 (check 명령으로 확인)", True)

    global _TMP
    tmp = Path(a.out)
    tmp.mkdir(parents=True, exist_ok=True)
    _TMP = tmp
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch()
            except Exception as e:  # 브라우저 미설치 등
                fail("도구 오류", f"브라우저 실행 실패: {str(e).splitlines()[0][:100]}", True)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            failed_css = []

            def on_css_failed(req):
                if req.resource_type == "stylesheet" and req.url not in failed_css:
                    failed_css.append(req.url)

            def on_css_response(res):
                if res.request.resource_type == "stylesheet" and res.status >= 400 and res.url not in failed_css:
                    failed_css.append(res.url)

            page.on("requestfailed", on_css_failed)
            page.on("response", on_css_response)
            try:
                resp = page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
                wait_for_render(page)
            except Exception as e:
                browser.close()
                classify_exception(str(e))
            status = resp.status if resp else 0
            body_text = page.inner_text("body") if page.query_selector("body") else ""
            classify_status(status, body_text)

            final_url = page.url
            if LOGIN_PATH_RE.search(urlparse(final_url).path) and not LOGIN_PATH_RE.search(parsed.path):
                browser.close()
                fail("접근 제한", "로그인 페이지로 이동함", False)
            has_password = page.query_selector('input[type="password"]') is not None

            auto_scroll(page)
            wait_for_render(page)  # 스크롤로 새로 불러온 이미지까지 기다린다
            page.wait_for_timeout(SETTLE_MS)
            rendered = page.content()
            page_title = page.title()
            lang = page.evaluate("document.documentElement.lang") or ""
            try:
                page.screenshot(path=str(tmp / "clip.png"), full_page=True)
            except Exception as e:
                browser.close()
                fail("도구 오류", f"캡처 실패: {str(e).splitlines()[0][:100]}", True)
            browser.close()
    except SystemExit:
        raise
    except Exception as e:
        fail("도구 오류", str(e).splitlines()[0][:120], True)

    doc = Document(rendered, url=final_url)
    content = doc.summary(html_partial=True)
    title = (doc.short_title() or page_title or parsed.netloc).strip()
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", content)).strip()

    if has_password and len(text) < 1500:
        (tmp / "clip.png").unlink(missing_ok=True)
        fail("접근 제한", "로그인 필요 (로그인 화면)", False)
    if len(text) < MIN_TEXT_LENGTH:
        (tmp / "clip.png").unlink(missing_ok=True)
        fail("본문 없음", "본문을 거의 뽑지 못함", True)

    saved = today()
    tpl = TEMPLATE.read_text(encoding="utf-8")
    page_html = (tpl.replace("{lang}", html.escape(lang or ""))
                    .replace("{title}", html.escape(title))
                    .replace("{url}", html.escape(url))
                    .replace("{saved}", saved)
                    .replace("{content}", content))
    (tmp / "clip.html").write_text(page_html, encoding="utf-8")
    out({"ok": True, "url": url, "final_url": final_url, "status": status, "title": title,
         "lang": lang, "title_too_long": len(title) > MAX_NAME_LENGTH,
         "text_length": len(text), "text_preview": text[:300],
         "style_warning": (f"스타일시트 {len(failed_css)}개를 불러오지 못해 캡처의 모양이 원본과 다를 수 있음"
                           if failed_css else None),
         "failed_stylesheets": failed_css[:5],
         "html": str(tmp / "clip.html"), "png": str(tmp / "clip.png")})


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


def read_log_rows(root):
    log = Path(root) / LOG_NAME
    if not log.exists():
        return []
    rows = []
    for line in log.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and cells[1].startswith("http"):
            rows.append({"date": cells[0], "url": cells[1], "result": cells[2], "reason": cells[3]})
    return rows


def cmd_retry_list(a):
    latest = {}
    for r in read_log_rows(a.root):
        latest[r["url"]] = r  # 표가 시간순이므로 마지막 줄이 최신 상태
    urls = [u for u, r in latest.items() if r["result"] == "실패" and "재시도 가능" in r["reason"]]
    out({"count": len(urls), "urls": urls,
         "details": [{"url": u, "reason": latest[u]["reason"], "date": latest[u]["date"]} for u in urls]})


def main():
    ap = argparse.ArgumentParser(description="link-clipper helper")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    p = sub.add_parser("links"); p.add_argument("file")
    p = sub.add_parser("find"); p.add_argument("url"); p.add_argument("--root", required=True)
    p = sub.add_parser("fetch"); p.add_argument("url"); p.add_argument("--out", required=True)
    p = sub.add_parser("place"); p.add_argument("--tmp", required=True); p.add_argument("--root", required=True); p.add_argument("--name", required=True)
    p = sub.add_parser("log"); p.add_argument("--root", required=True); p.add_argument("--url", required=True)
    p.add_argument("--result", required=True, choices=["성공", "실패", "갱신"]); p.add_argument("--reason", default="")
    p = sub.add_parser("retry-list"); p.add_argument("--root", required=True)
    a = ap.parse_args()
    {"check": cmd_check, "links": cmd_links, "find": cmd_find, "fetch": cmd_fetch, "place": cmd_place,
     "log": cmd_log, "retry-list": cmd_retry_list}[a.cmd](a)


if __name__ == "__main__":
    main()
