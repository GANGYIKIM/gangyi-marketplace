#!/usr/bin/env python3
"""finder 도우미 스크립트. 클립을 읽기만 하고, 파이썬 기본 라이브러리만 쓴다.

  search --root CLIPS [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--site DOMAIN]
         [--keyword K ...] [--summaries DIR] [--no-summary] [--limit N]
      클립을 저장일, 사이트, 본문 키워드, 요약 여부로 찾는다. 키워드는 하나라도 맞으면 찾은 것으로 본다
  failures --root CLIPS [--include-excluded]
      clip-log에서 링크별 마지막 상태가 실패인 링크를 나열한다

Claude는 클립 본문을 직접 읽지 않고 이 스크립트의 결과만 본다. 결과는 JSON 한 줄이다.
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

LOG_NAME = "clip-log.md"
META_RE = {k: re.compile(rf'<meta name="clip:{k}" content="([^"]*)"') for k in ("source", "title", "saved")}
ARTICLE_RE = re.compile(r"<article[^>]*>(.*)</article>", re.S | re.I)
SUMMARY_SOURCE_RE = re.compile(r"^- 원본 파일:\s*`([^`]+)`", re.M)
DEFAULT_LIMIT = 20


def out(data, code=0):
    print(json.dumps(data, ensure_ascii=False))
    sys.exit(code)


def clip_text(page):
    """클립 HTML에서 본문(<article>) 텍스트만 뽑는다. 정보 영역과 스타일은 제외한다."""
    m = ARTICLE_RE.search(page)
    body = m.group(1) if m else page
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", body, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body))).strip()


def site_of(url):
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def summary_index(summaries):
    """요약 파일의 '원본 파일' 줄로 {원본 절대 경로: 요약 경로}를 만든다."""
    index = {}
    if summaries and Path(summaries).is_dir():
        for md in Path(summaries).glob("*.md"):
            m = SUMMARY_SOURCE_RE.search(md.read_text(encoding="utf-8", errors="replace"))
            if m:
                index[str(Path(m.group(1)).resolve())] = str(md)
    return index


def cmd_search(a):
    root = Path(a.root)
    if not root.is_dir():
        out({"exists": False, "root": str(root), "count": 0, "results": []})
    keywords = [k.lower() for k in (a.keyword or []) if k.strip()]
    summaries = summary_index(a.summaries)
    results = []
    for folder in sorted(p for p in root.iterdir() if p.is_dir() and p.name not in ("inbox", "archive")):
        main = folder / f"{folder.name}.html"
        if not main.exists():
            continue
        page = main.read_text(encoding="utf-8", errors="replace")
        meta = {k: html.unescape(r.search(page).group(1)) if r.search(page) else "" for k, r in META_RE.items()}
        if a.since and meta["saved"] < a.since:
            continue
        if a.until and meta["saved"] > a.until:
            continue
        if a.site and a.site.lower().removeprefix("www.") not in site_of(meta["source"]):
            continue
        summary = summaries.get(str(main.resolve()))
        if a.no_summary and summary:
            continue
        matched, hits = [], 0
        if keywords:
            text = (meta["title"] + " " + clip_text(page)).lower()
            for k in keywords:
                n = text.count(k)
                if n:
                    matched.append(k)
                    hits += n
            if not matched:
                continue
        results.append({"title": meta["title"], "saved": meta["saved"], "url": meta["source"],
                        "site": site_of(meta["source"]), "folder": str(folder), "html": str(main),
                        "png": str(folder / f"{folder.name}.png"), "matched": matched, "hits": hits,
                        "summary": summary})
    # 맞은 검색어가 많은 것, 그다음 최근에 저장한 것부터
    results.sort(key=lambda r: (len(r["matched"]), r["hits"], r["saved"]), reverse=True)
    out({"exists": True, "root": str(root), "count": len(results), "results": results[:a.limit],
         "truncated": len(results) > a.limit})


def cmd_failures(a):
    log = Path(a.root) / LOG_NAME
    if not log.exists():
        out({"exists": False, "log": str(log), "count": 0, "failures": []})
    latest = {}
    for line in log.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and cells[1].startswith("http"):
            latest[cells[1]] = {"date": cells[0], "url": cells[1], "result": cells[2], "reason": cells[3]}
    wanted = ("실패", "제외") if a.include_excluded else ("실패",)
    rows = [r for r in latest.values() if r["result"] in wanted]
    out({"exists": True, "log": str(log), "count": len(rows), "failures": rows})


def main():
    ap = argparse.ArgumentParser(description="finder helper")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("search"); p.add_argument("--root", required=True)
    p.add_argument("--since"); p.add_argument("--until"); p.add_argument("--site")
    p.add_argument("--keyword", action="append"); p.add_argument("--summaries")
    p.add_argument("--no-summary", action="store_true"); p.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    p = sub.add_parser("failures"); p.add_argument("--root", required=True)
    p.add_argument("--include-excluded", action="store_true")
    a = ap.parse_args()
    {"search": cmd_search, "failures": cmd_failures}[a.cmd](a)


if __name__ == "__main__":
    main()
