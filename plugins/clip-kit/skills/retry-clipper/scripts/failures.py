#!/usr/bin/env python3
"""retry-clipper 도우미 스크립트. 파이썬 기본 라이브러리만 쓴다.

  status --root CLIPS [--include-excluded]   링크별 마지막 상태로 실패 현황을 분류해 보여준다
  exclude --root CLIPS --url URL [--url ...]  실패한 링크를 재시도 대상에서 제외한다(clip-log에 한 줄 추가)

clip-log.md는 link-clipper가 쓰는 표 형식(| 날짜 | 링크 | 결과 | 실패 사유 |)을 그대로 따른다.
기록은 고치지 않고 더하기만 하며, 링크별 마지막 줄이 지금 상태다.
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

LOG_NAME = "clip-log.md"
REASON_RE = re.compile(r"^(?P<category>[^:]+):\s*(?P<detail>.*?)\s*\((?P<retry>재시도 가능|재시도 불가)\)\s*$")


def out(data, code=0):
    print(json.dumps(data, ensure_ascii=False))
    sys.exit(code)


def read_rows(log):
    rows = []
    for line in log.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and cells[1].startswith("http"):
            rows.append({"date": cells[0], "url": cells[1], "result": cells[2], "reason": cells[3]})
    return rows


def latest_by_url(rows):
    latest = {}
    for r in rows:  # 표가 시간순이므로 마지막 줄이 최신 상태
        latest[r["url"]] = r
    return latest


def describe(r):
    m = REASON_RE.match(r["reason"])
    return {**r, "category": m.group("category").strip() if m else "기타",
            "detail": m.group("detail") if m else r["reason"],
            "retryable": bool(m) and m.group("retry") == "재시도 가능"}


def cmd_status(a):
    log = Path(a.root) / LOG_NAME
    if not log.exists():
        out({"exists": False, "log": str(log), "counts": {"retryable": 0, "not_retryable": 0, "excluded": 0}})
    latest = latest_by_url(read_rows(log))
    failed = [describe(r) for r in latest.values() if r["result"] == "실패"]
    excluded = [describe(r) for r in latest.values() if r["result"] == "제외"]
    retryable = [r for r in failed if r["retryable"]]
    not_retryable = [r for r in failed if not r["retryable"]]
    by_category = {}
    for r in failed:
        key = f'{r["category"]}: {r["detail"]}'
        by_category[key] = by_category.get(key, 0) + 1
    data = {"exists": True, "log": str(log), "retryable": retryable, "not_retryable": not_retryable,
            "by_category": by_category,
            "counts": {"retryable": len(retryable), "not_retryable": len(not_retryable), "excluded": len(excluded)}}
    if a.include_excluded:
        data["excluded"] = excluded
    out(data)


def cmd_exclude(a):
    log = Path(a.root) / LOG_NAME
    if not log.exists():
        out({"ok": False, "error": "no_log", "log": str(log)}, 1)
    latest = latest_by_url(read_rows(log))
    done, skipped = [], []
    today = dt.date.today().isoformat()
    with log.open("a", encoding="utf-8") as f:
        for url in a.url:
            r = latest.get(url)
            if not r or r["result"] != "실패":
                skipped.append({"url": url, "why": "실패 상태가 아님" if r else "기록에 없음"})
                continue
            f.write(f'| {today} | {url} | 제외 | {r["reason"]} |\n')
            done.append(url)
    out({"ok": True, "excluded": done, "skipped": skipped})


def main():
    ap = argparse.ArgumentParser(description="retry-clipper helper")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("status"); p.add_argument("--root", required=True)
    p.add_argument("--include-excluded", action="store_true")
    p = sub.add_parser("exclude"); p.add_argument("--root", required=True)
    p.add_argument("--url", action="append", required=True)
    a = ap.parse_args()
    {"status": cmd_status, "exclude": cmd_exclude}[a.cmd](a)


if __name__ == "__main__":
    main()
