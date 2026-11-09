"""가짜 GitHub 서버가 쓰는 작은 GraphQL 실행기.

gh가 보내는 질의(operation, fragment, alias, 인자, inline fragment)를 읽고, 인자를
변수로 풀어, 질의가 고른 필드만 돌려준다. gh는 일부 응답을 엄격하게 읽어서 고르지
않은 필드가 섞이면 오류를 내기 때문이다.

데이터는 dict 나무로 준다. 값이 함수면 그 필드의 풀린 인자를 받아 값을 돌려준다.
"""
import json
import re

TOKEN = re.compile(r'\.\.\.|"(?:[^"\\]|\\.)*"|-?\d+(?:\.\d+)?|[A-Za-z_][A-Za-z0-9_]*|\$|[{}()\[\]:!=,@]')


class GQLError(Exception):
    pass


def tokenize(src):
    src = re.sub(r"#[^\n]*", "", src)
    return TOKEN.findall(src)


class Parser:
    def __init__(self, src):
        self.t = tokenize(src)
        self.i = 0

    def peek(self, k=0):
        j = self.i + k
        return self.t[j] if j < len(self.t) else None

    def take(self, expect=None):
        tok = self.peek()
        if expect is not None and tok != expect:
            raise GQLError(f"expected {expect!r}, got {tok!r} at token {self.i}")
        self.i += 1
        return tok

    def document(self):
        ops, frags = [], {}
        while self.peek() is not None:
            tok = self.peek()
            if tok == "fragment":
                self.take()
                name = self.take()
                self.take("on")
                self.take()  # 타입 이름
                frags[name] = self.selection_set()
            elif tok in ("query", "mutation", "subscription"):
                kind = self.take()
                if self.peek() not in ("(", "{", "@"):
                    self.take()  # operation 이름
                if self.peek() == "(":
                    self.skip_group("(", ")")
                self.directives()
                ops.append((kind, self.selection_set()))
            elif tok == "{":
                ops.append(("query", self.selection_set()))
            else:
                raise GQLError(f"unexpected token {tok!r}")
        return ops, frags

    def skip_group(self, open_, close):
        depth = 0
        while True:
            tok = self.take()
            if tok == open_:
                depth += 1
            elif tok == close:
                depth -= 1
                if depth == 0:
                    return

    def directives(self):
        while self.peek() == "@":
            self.take()
            self.take()
            if self.peek() == "(":
                self.skip_group("(", ")")

    def selection_set(self):
        self.take("{")
        sels = []
        while self.peek() != "}":
            if self.peek() == "...":
                self.take()
                if self.peek() == "on":
                    self.take()
                    typ = self.take()
                    self.directives()
                    sels.append(("inline", typ, self.selection_set()))
                else:
                    name = self.take()
                    self.directives()
                    sels.append(("spread", name))
                continue
            name = self.take()
            alias = name
            if self.peek() == ":":
                self.take()
                name = self.take()
            args = {}
            if self.peek() == "(":
                args = self.arguments()
            self.directives()
            sub = self.selection_set() if self.peek() == "{" else None
            sels.append(("field", alias, name, args, sub))
            if self.peek() == ",":
                self.take()
        self.take("}")
        return sels

    def arguments(self):
        self.take("(")
        args = {}
        while self.peek() != ")":
            key = self.take()
            self.take(":")
            args[key] = self.value()
            if self.peek() == ",":
                self.take()
        self.take(")")
        return args

    def value(self):
        tok = self.take()
        if tok == "$":
            return ("var", self.take())
        if tok == "[":
            items = []
            while self.peek() != "]":
                items.append(self.value())
                if self.peek() == ",":
                    self.take()
            self.take("]")
            return ("list", items)
        if tok == "{":
            obj = {}
            while self.peek() != "}":
                k = self.take()
                self.take(":")
                obj[k] = self.value()
                if self.peek() == ",":
                    self.take()
            self.take("}")
            return ("obj", obj)
        if tok.startswith('"'):
            return ("lit", json.loads(tok))
        if re.fullmatch(r"-?\d+", tok):
            return ("lit", int(tok))
        if tok in ("true", "false"):
            return ("lit", tok == "true")
        if tok == "null":
            return ("lit", None)
        return ("lit", tok)  # enum 값


def resolve_value(v, variables):
    kind, x = v
    if kind == "var":
        return variables.get(x)
    if kind == "list":
        return [resolve_value(i, variables) for i in x]
    if kind == "obj":
        return {k: resolve_value(i, variables) for k, i in x.items()}
    return x


def expand(sels, frags, typename):
    out = []
    for s in sels:
        if s[0] == "field":
            out.append(s)
        elif s[0] == "inline":
            if typename is None or s[1] == typename:
                out.extend(expand(s[2], frags, typename))
        elif s[0] == "spread":
            if s[1] not in frags:
                raise GQLError(f"unknown fragment {s[1]}")
            out.extend(expand(frags[s[1]], frags, typename))
    return out


def project(sels, source, frags, variables):
    if source is None:
        return None
    if isinstance(source, list):
        return [project(sels, item, frags, variables) for item in source]
    typename = source.get("__typename") if isinstance(source, dict) else None
    out = {}
    for _, alias, name, args, sub in expand(sels, frags, typename):
        val = source.get(name) if isinstance(source, dict) else None
        if callable(val):
            val = val({k: resolve_value(a, variables) for k, a in args.items()})
        if sub is not None:
            out[alias] = project(sub, val, frags, variables)
        else:
            out[alias] = val
    return out


def execute(query, variables, root_query, root_mutation):
    ops, frags = Parser(query).document()
    if not ops:
        raise GQLError("no operation")
    kind, sels = ops[0]
    root = root_mutation if kind == "mutation" else root_query
    return project(sels, root, frags, variables or {})
