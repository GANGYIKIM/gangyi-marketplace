#!/usr/bin/env python3
"""profile-cleaner 도우미 스크립트. 파이썬 기본 라이브러리만 쓴다.

  show    클리핑 전용 Chrome 프로필의 위치, 크기, 데이터를 남긴 사이트 수, 사용 중인지
  clear   프로필을 지운다. 클리핑 전용 경로가 아니거나 Chrome이 쓰는 중이면 거부한다

모든 명령은 결과를 JSON 한 줄로 출력한다.
환경 변수(테스트용): CLIPPER_PROFILE_DIR. link-clipper의 clipper.py와 같은 기본 경로를 써야 한다.
"""
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

DEFAULT_PROFILE = Path.home() / ".cache" / "link-clipper" / "chrome-profile"
PROFILE_DIR = Path(os.environ.get("CLIPPER_PROFILE_DIR") or DEFAULT_PROFILE)
# Chrome이 프로필을 쓰는 동안 프로필 폴더에 만들어 두는 잠금 표시
LOCK_NAMES = ("SingletonLock", "SingletonCookie", "SingletonSocket")
# 평소 쓰는 Chrome 프로필 위치. 이 아래는 어떤 경우에도 지우지 않는다
PERSONAL_CHROME = [Path.home() / "Library" / "Application Support" / "Google" / "Chrome",
                   Path.home() / ".config" / "google-chrome",
                   Path.home() / "AppData" / "Local" / "Google" / "Chrome"]


def out(data, code=0):
    print(json.dumps(data, ensure_ascii=False))
    sys.exit(code)


def folder_size(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += (Path(root) / f).lstat().st_size
            except OSError:
                pass
    return total


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024


def in_use(path):
    return any((path / name).exists() or (path / name).is_symlink() for name in LOCK_NAMES)


def site_count(path):
    """쿠키를 남긴 사이트 수. Chrome이 잠근 파일을 건드리지 않으려고 복사본을 읽는다."""
    for db in (path / "Default" / "Network" / "Cookies", path / "Default" / "Cookies"):
        if db.exists():
            with tempfile.TemporaryDirectory() as tmp:
                copy = Path(tmp) / "Cookies"
                try:
                    shutil.copy2(db, copy)
                    con = sqlite3.connect(str(copy))
                    hosts = {r[0].lstrip(".") for r in con.execute("SELECT host_key FROM cookies")}
                    con.close()
                    return len(hosts)
                except Exception:
                    return None
    return 0


def is_clip_profile(path):
    """지워도 되는 경로인지 본다: 기본 클리핑 프로필이거나, 이름에 link-clipper가 들어간 전용 폴더."""
    p = path.resolve()
    if any(p == c.resolve() or c.resolve() in p.parents for c in PERSONAL_CHROME):
        return False
    return p == DEFAULT_PROFILE.resolve() or "link-clipper" in p.as_posix() or bool(os.environ.get("CLIPPER_PROFILE_DIR"))


def cmd_show():
    p = PROFILE_DIR
    if not p.exists():
        out({"exists": False, "profile_dir": str(p)})
    size = folder_size(p)
    out({"exists": True, "profile_dir": str(p), "size_bytes": size, "size": human(size),
         "sites": site_count(p), "in_use": in_use(p)})


def cmd_clear():
    p = PROFILE_DIR
    if not p.exists():
        out({"ok": True, "removed": False, "profile_dir": str(p), "detail": "지울 프로필이 없음"})
    if not is_clip_profile(p):
        out({"ok": False, "error": "not_clip_profile", "profile_dir": str(p),
             "detail": "클리핑 전용 프로필이 아니라서 지우지 않음"}, 1)
    if in_use(p):
        out({"ok": False, "error": "in_use", "profile_dir": str(p),
             "detail": "Chrome이 이 프로필을 쓰는 중. 클리핑용 Chrome 창을 닫고 다시 시도"}, 1)
    shutil.rmtree(p, ignore_errors=True)
    out({"ok": not p.exists(), "removed": True, "profile_dir": str(p)})


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "show":
        cmd_show()
    elif cmd == "clear":
        cmd_clear()
    out({"ok": False, "error": "usage", "detail": "profile.py show | clear"}, 2)
