#!/usr/bin/env python3
"""진짜 gh로 git-kit 스킬을 시험하기 위한 가짜 GitHub API 서버.

gh 설정에 `http_unix_socket: <경로>`가 있으면 gh는 모든 HTTP 요청을 그 unix 소켓으로
보낸다. 이 서버는 그 소켓에서 요청을 받아, PR과 코멘트를 JSON 상태 파일에 두고 gh가
보내는 REST와 GraphQL 요청에 답한다. 받은 요청은 모두 기록해 스킬이 무엇을 했는지
채점할 수 있게 한다. 모르는 요청에는 501로 답하고 기록에 unsupported로 남긴다.

usage: fake_github.py <소켓 경로> <state.json> <calls.jsonl>

상태 파일:
  {"repo": "owner/name", "user": "eval", "defaultBranch": "main",
   "pulls": [{"number", "title", "state": OPEN|CLOSED|MERGED, "isDraft",
              "baseRefName", "headRefName", "body", "mergedAt"}],
   "comments": [{"id", "issue", "body", "user", "author_association",
                 "created_at"}],
   "reviewComments": [{"pull", ...}], "reviews": [{"pull", ...}]}  (없으면 빈 목록)
"""
import json
import os
import re
import socketserver
import sys
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gql  # noqa: E402

LOCK = threading.Lock()


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class NotFound(Exception):
    pass


class Unsupported(Exception):
    pass


class World:
    """상태 파일을 바탕으로 한 GitHub 데이터."""

    def __init__(self, state):
        self.s = state
        self.changed = False
        self.owner, self.name = state["repo"].split("/")

    # --- 객체 ---------------------------------------------------------------
    def user(self, login):
        return {"__typename": "User", "login": login, "id": f"U_{login}", "name": login}

    def conn(self, nodes):
        return {"nodes": nodes, "edges": [{"node": n} for n in nodes], "totalCount": len(nodes),
                "issueCount": len(nodes), "pageInfo": {"hasNextPage": False, "endCursor": None}}

    def repo(self):
        s = self.s
        return {
            "__typename": "Repository",
            "id": "R_1",
            "name": self.name,
            "nameWithOwner": s["repo"],
            "owner": self.user(self.owner),
            "url": f"https://github.com/{s['repo']}",
            "defaultBranchRef": {"name": s.get("defaultBranch", "main")},
            "viewerPermission": "ADMIN",
            "isPrivate": False,
            "isFork": False,
            "hasIssuesEnabled": True,
            "parent": None,
            "mergeCommitAllowed": True,
            "rebaseMergeAllowed": True,
            "squashMergeAllowed": True,
            "pullRequest": lambda a: self.pr(self.find(a.get("number"))),
            "pullRequests": lambda a: self.conn([self.pr(p) for p in self.filter(a)]),
        }

    def pr(self, p):
        if p is None:
            raise NotFound("Could not resolve to a PullRequest")
        st = p.get("state", "OPEN")
        empty = self.conn([])
        return {
            "__typename": "PullRequest",
            "id": f"PR_{p['number']}",
            "number": p["number"],
            "title": p["title"],
            "body": p.get("body", ""),
            "state": st,
            "closed": st != "OPEN",
            "isDraft": p.get("isDraft", False),
            "merged": st == "MERGED",
            "mergedAt": p.get("mergedAt"),
            "closedAt": p.get("closedAt"),
            "createdAt": p.get("createdAt", "2026-10-21T00:00:00Z"),
            "updatedAt": p.get("updatedAt", "2026-10-21T00:00:00Z"),
            "url": f"https://github.com/{self.s['repo']}/pull/{p['number']}",
            "baseRefName": p["baseRefName"],
            "headRefName": p["headRefName"],
            "headRefOid": p.get("headRefOid", "0" * 40),
            "baseRefOid": "0" * 40,
            "isCrossRepository": False,
            "maintainerCanModify": True,
            "author": self.user(p.get("author", self.s.get("user", "eval"))),
            "headRepositoryOwner": self.user(self.owner),
            "headRepository": {"id": "R_1", "name": self.name, "nameWithOwner": self.s["repo"],
                               "owner": self.user(self.owner)},
            "baseRepository": {"id": "R_1", "name": self.name, "nameWithOwner": self.s["repo"],
                               "owner": self.user(self.owner)},
            "repository": {"id": "R_1", "name": self.name, "nameWithOwner": self.s["repo"],
                           "owner": self.user(self.owner)},
            "mergeable": "MERGEABLE",
            "mergeStateStatus": "CLEAN",
            "reviewDecision": None,
            "additions": 0,
            "deletions": 0,
            "changedFiles": 0,
            "isInMergeQueue": False,
            "autoMergeRequest": None,
            "milestone": None,
            "labels": empty, "assignees": empty, "reviewRequests": empty, "projectCards": empty,
            "projectItems": empty, "reviews": empty, "latestReviews": empty,
            "commits": empty, "files": empty, "closingIssuesReferences": empty,
            "statusCheckRollup": empty, "participants": empty,
            # REST의 PR 코멘트(issues/<번호>/comments)와 같은 코멘트를 GraphQL로도 돌려준다.
            # `gh pr view --json comments`가 이 경로를 쓴다.
            "comments": self.conn([self.comment(c) for c in self.s["comments"]
                                   if c["issue"] == p["number"]]),
        }

    def comment(self, c):
        return {
            "__typename": "IssueComment",
            "id": f"IC_{c['id']}",
            "author": self.user(c.get("user", self.s.get("user", "eval"))),
            "authorAssociation": c.get("author_association", "OWNER"),
            "body": c["body"],
            "createdAt": c.get("created_at", "2026-10-21T00:00:00Z"),
            "updatedAt": c.get("updated_at", c.get("created_at", "2026-10-21T00:00:00Z")),
            "url": f"https://github.com/{self.s['repo']}/pull/{c['issue']}#issuecomment-{c['id']}",
            "includesCreatedEdit": False,
            "isMinimized": False,
            "minimizedReason": None,
            "reactionGroups": [],
            "viewerDidAuthor": c.get("user", self.s.get("user", "eval")) == self.s.get("user", "eval"),
        }

    def find(self, number):
        for p in self.s["pulls"]:
            if p["number"] == number:
                return p
        return None

    def filter(self, a):
        states = a.get("states")
        if isinstance(states, str):
            states = [states]
        out = []
        for p in self.s["pulls"]:
            if a.get("headRefName") and p["headRefName"] != a["headRefName"]:
                continue
            if a.get("baseRefName") and p["baseRefName"] != a["baseRefName"]:
                continue
            if states and p.get("state", "OPEN") not in states:
                continue
            out.append(p)
        return sorted(out, key=lambda p: -p["number"])

    def search(self, a):
        q = a.get("query") or ""
        out = []
        for p in self.s["pulls"]:
            ok = True
            for tok in q.split():
                low = tok.lower()
                st = p.get("state", "OPEN")
                if low in ("is:draft", "draft:true") and not p.get("isDraft"):
                    ok = False
                elif low == "draft:false" and p.get("isDraft"):
                    ok = False
                elif low in ("is:open", "state:open") and st != "OPEN":
                    ok = False
                elif low in ("is:closed", "state:closed") and st == "OPEN":
                    ok = False
                elif low == "is:merged" and st != "MERGED":
                    ok = False
                elif low.startswith("head:") and p["headRefName"] != tok[5:]:
                    ok = False
                elif low.startswith("base:") and p["baseRefName"] != tok[5:]:
                    ok = False
                elif low.startswith("repo:") and tok[5:] != self.s["repo"]:
                    ok = False
            if ok:
                out.append(p)
        return self.conn([self.pr(p) for p in sorted(out, key=lambda p: -p["number"])])

    def type_info(self, a):
        enums = {
            "SearchType": ["ISSUE", "ISSUE_ADVANCED", "REPOSITORY", "USER", "DISCUSSION"],
            "PullRequestState": ["OPEN", "CLOSED", "MERGED"],
        }
        name = a.get("name")
        return {"name": name, "enumValues": [{"name": n} for n in enums.get(name, [])],
                "fields": [], "inputFields": []}

    # --- GraphQL 루트 --------------------------------------------------------
    def query_root(self):
        return {
            "viewer": self.user(self.s.get("user", "eval")),
            "repository": lambda a: self.repo(),
            "search": self.search,
            "__type": self.type_info,
            "node": lambda a: self.pr(self.find(int(str(a.get("id", "")).split("_")[-1] or 0))),
        }

    def mutation_root(self):
        def pr_from_input(a):
            pid = str((a.get("input") or {}).get("pullRequestId", ""))
            p = self.find(int(pid.split("_")[-1])) if pid.startswith("PR_") else None
            if p is None:
                raise NotFound(f"Could not resolve to a node with the global id of '{pid}'")
            return p

        def update(a):
            p, inp = pr_from_input(a), a.get("input") or {}
            for key in ("title", "body", "baseRefName"):
                if inp.get(key) is not None:
                    p[key] = inp[key]
            self.changed = True
            return {"pullRequest": self.pr(p)}

        def ready(a):
            p = pr_from_input(a)
            p["isDraft"] = False
            self.changed = True
            return {"pullRequest": self.pr(p)}

        def draft(a):
            p = pr_from_input(a)
            p["isDraft"] = True
            self.changed = True
            return {"pullRequest": self.pr(p)}

        return {"updatePullRequest": update, "markPullRequestReadyForReview": ready,
                "convertPullRequestToDraft": draft}


def comment_rest(s, c):
    return {
        "id": c["id"], "node_id": f"IC_{c['id']}", "body": c["body"],
        "user": {"login": c.get("user", s.get("user", "eval")), "type": "User"},
        "author_association": c.get("author_association", "OWNER"),
        "created_at": c.get("created_at", "2026-10-21T00:00:00Z"),
        "updated_at": c.get("updated_at", c.get("created_at", "2026-10-21T00:00:00Z")),
        "html_url": f"https://github.com/{s['repo']}/pull/{c['issue']}#issuecomment-{c['id']}",
        "issue_url": f"https://api.github.com/repos/{s['repo']}/issues/{c['issue']}",
    }


def pr_rest(s, p):
    st = p.get("state", "OPEN")
    return {"number": p["number"], "title": p["title"], "body": p.get("body", ""),
            "state": "open" if st == "OPEN" else "closed", "draft": p.get("isDraft", False),
            "merged": st == "MERGED", "merged_at": p.get("mergedAt"),
            "html_url": f"https://github.com/{s['repo']}/pull/{p['number']}",
            "base": {"ref": p["baseRefName"]}, "head": {"ref": p["headRefName"]}}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def send_json(self, code, obj):
        out = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("X-Oauth-Scopes", "repo, read:org, workflow")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def handle_any(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n).decode("utf-8") if n else ""
        entry = {"t": now(), "method": self.command, "path": self.path}
        with LOCK:
            with open(self.server.state_path, encoding="utf-8") as f:
                state = json.load(f)
            world = World(state)
            try:
                code, obj = self.route(world, self.path.split("?")[0], raw, entry)
            except Unsupported as e:
                code, obj = 501, {"message": f"fake github: unsupported {e}"}
                entry["unsupported"] = str(e)
            except gql.GQLError as e:
                code, obj = 400, {"message": f"fake github: graphql parse error: {e}"}
                entry["unsupported"] = f"graphql parse: {e}"
            if world.changed:
                tmp = self.server.state_path + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(state, f, ensure_ascii=False, indent=2)
                os.replace(tmp, self.server.state_path)
        entry["status"] = code
        with open(self.server.calls_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self.send_json(code, obj)

    def route(self, world, path, raw, entry):
        s = world.s
        repo = s["repo"]
        if path == "/graphql":
            body = json.loads(raw or "{}")
            query, variables = body.get("query", ""), body.get("variables") or {}
            m = re.search(r"\b(query|mutation)\s+(\w+)", query)
            entry["op"] = m.group(2) if m else "anonymous"
            entry["variables"] = variables
            entry["query"] = " ".join(query.split())
            is_mut = query.lstrip().startswith("mutation")
            try:
                data = gql.execute(query, variables, world.query_root(), world.mutation_root())
            except NotFound as e:
                return 200, {"data": None, "errors": [{"type": "NOT_FOUND", "message": str(e)}]}
            if is_mut:
                entry["mutation"] = True
            return 200, {"data": data}
        if path in ("/", ""):
            return 200, {"current_user_url": "https://api.github.com/user"}
        if path == "/user":
            return 200, {"login": s.get("user", "eval"), "type": "User"}
        if path == f"/repos/{repo}":
            return 200, {"full_name": repo, "name": world.name, "owner": {"login": world.owner},
                         "default_branch": s.get("defaultBranch", "main"),
                         "html_url": f"https://github.com/{repo}"}
        m = re.fullmatch(rf"/repos/{re.escape(repo)}/issues/(\d+)/comments", path)
        if m:
            num = int(m.group(1))
            if self.command == "GET":
                return 200, [comment_rest(s, c) for c in s["comments"] if c["issue"] == num]
            if self.command == "POST":
                body = json.loads(raw or "{}")
                cid = max([c["id"] for c in s["comments"]] + [100]) + 1
                c = {"id": cid, "issue": num, "body": body.get("body", ""), "user": s.get("user", "eval"),
                     "author_association": "OWNER", "created_at": now()}
                s["comments"].append(c)
                world.changed = True
                entry["body"] = c["body"]
                return 201, comment_rest(s, c)
        m = re.fullmatch(rf"/repos/{re.escape(repo)}/issues/comments/(\d+)", path)
        if m:
            c = next((c for c in s["comments"] if c["id"] == int(m.group(1))), None)
            if c is None:
                return 404, {"message": "Not Found"}
            if self.command == "GET":
                return 200, comment_rest(s, c)
            if self.command == "PATCH":
                body = json.loads(raw or "{}")
                c["body"] = body.get("body", c["body"])
                c["updated_at"] = now()
                world.changed = True
                entry["body"] = c["body"]
                return 200, comment_rest(s, c)
        m = re.fullmatch(rf"/repos/{re.escape(repo)}/pulls/(\d+)/(comments|reviews)", path)
        if m and self.command == "GET":
            # 코드 줄에 단 리뷰 코멘트와 리뷰. 상태 파일에 없으면 빈 목록
            key = "reviewComments" if m.group(2) == "comments" else "reviews"
            return 200, [x for x in s.get(key, []) if x.get("pull") == int(m.group(1))]
        m = re.fullmatch(rf"/repos/{re.escape(repo)}/(pulls|issues)/(\d+)", path)
        if m:
            p = world.find(int(m.group(2)))
            if p is None:
                return 404, {"message": "Not Found"}
            if self.command == "GET":
                return 200, pr_rest(s, p)
            if self.command == "PATCH":
                body = json.loads(raw or "{}")
                for src, dst in (("title", "title"), ("body", "body"), ("base", "baseRefName")):
                    if src in body:
                        p[dst] = body[src]
                world.changed = True
                entry["body"] = body
                return 200, pr_rest(s, p)
        m = re.fullmatch(rf"/repos/{re.escape(repo)}/pulls", path)
        if m and self.command == "GET":
            return 200, [pr_rest(s, p) for p in sorted(s["pulls"], key=lambda p: -p["number"])]
        raise Unsupported(f"{self.command} {path}")

    do_GET = do_POST = do_PATCH = do_PUT = do_DELETE = handle_any

    def log_message(self, *args):
        pass


class Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True

    def get_request(self):
        req, _ = super().get_request()
        return req, ("unix", 0)


def main():
    sock, state_path, calls_path = sys.argv[1:4]
    if os.path.exists(sock):
        os.remove(sock)
    srv = Server(sock, Handler)
    srv.state_path, srv.calls_path = state_path, calls_path
    srv.serve_forever()


if __name__ == "__main__":
    main()
