# -*- coding: utf-8 -*-
"""frontmatter(제한된 YAML 부분집합)와 [[위키링크]] 파서, 그리고 정본 frontmatter 생성기. 외부 의존성 없음.

파서 지원 범위: 스칼라, 인라인 리스트 [a, b], 중첩 키 아래 블록 리스트(- 항목). 그 외 형식은 문자열로 보존.
정본 규칙은 설계서 §3(zettel 설계 260919)을 따른다.
- 키 순서 고정: CANONICAL_KEYS 의 순서 그대로. 값이 없으면 빈 값으로 두되 키는 남긴다
- 날짜는 따옴표 없이, 리스트는 인라인 [a, b], [[링크]] 값은 따옴표로 감싼다
- connections 는 internal / cross 두 블록에 인라인 리스트로 쓴다
"""
from __future__ import annotations
import re

_FM = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.S)
_LINK = re.compile(r"\[\[([^\]\|#]+)(?:[#\|][^\]]*)?\]\]")

# 설계서 §3 의 유형별 정본 키 순서. 이 순서가 이관·정규화의 기준이다.
CANONICAL_KEYS: dict[str, list[str]] = {
    "permanent": ["type", "platform", "source-type", "title", "author",
                  "literature-note", "date", "tags", "luhmann", "connections"],
    "literature": ["type", "subtype", "title", "author", "source", "platform",
                   "date", "tags", "processed", "permanent-notes"],
    "fleeting": ["type", "created", "processed", "tags", "source"],
    "raw": ["type", "source", "date", "processed"],
}

# 키별 빈 값. 여기에 없는 키의 빈 값은 빈 문자열이다.
_EMPTY_BY_KEY: dict = {
    "tags": list,
    "permanent-notes": list,
    "processed": bool,
    "connections": "connections",
}

_CONNECTION_KEYS = ("internal", "cross")


def _scalar(v: str):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [] if not inner else [_scalar(x) for x in inner.split(",")]
    if v in ("true", "false"):
        return v == "true"
    return v


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = _FM.match(text)
    if not m:
        return {}, text
    fm: dict = {}
    stack: list[tuple[int, dict]] = [(-1, fm)]
    cur_list_owner: dict | None = None
    cur_list_key = None
    for raw in m.group(1).splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if line.startswith("- "):
            if cur_list_key is None or cur_list_owner is None:
                continue
            existing = cur_list_owner.get(cur_list_key)
            if not isinstance(existing, list):
                # 값이 비어 dict 로 열렸던 키였다면 그 자리표시자를 리스트로 되돌린다
                if len(stack) > 1 and stack[-1][1] is existing:
                    stack.pop()
                cur_list_owner[cur_list_key] = []
            cur_list_owner[cur_list_key].append(_scalar(line[2:]))
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        if val.strip() == "":
            # 값이 비었다: 중첩 dict 이거나 블록 리스트다. 우선 dict 로 열어 두고,
            # 다음 줄이 '- ' 항목이면 그때 리스트로 바꾼다.
            child: dict = {}
            parent[key] = child
            stack.append((indent, child))
            cur_list_owner = parent
            cur_list_key = key
            continue
        parent[key] = _scalar(val)
        cur_list_owner = None
        cur_list_key = None
    _fix_empty_dicts(fm)
    return fm, text[m.end():]


def _fix_empty_dicts(d: dict):
    for k, v in list(d.items()):
        if isinstance(v, dict):
            if not v:
                d[k] = ""
            else:
                _fix_empty_dicts(v)


def wikilinks(text: str) -> list[str]:
    out, seen = [], set()
    for t in _LINK.findall(text):
        t = t.strip()
        if t and t not in seen:
            seen.add(t); out.append(t)
    return out


# ---------------------------------------------------------------- 정본 frontmatter

def _empty_value(key: str):
    kind = _EMPTY_BY_KEY.get(key)
    if kind is list:
        return []
    if kind is bool:
        return False
    if kind == "connections":
        return {k: [] for k in _CONNECTION_KEYS}
    return ""


def _is_blank(v) -> bool:
    """값이 '없는 것'인지 판정한다. False 와 0 은 값이 있는 것으로 본다."""
    if v is None:
        return True
    if isinstance(v, str):
        return v.strip() == ""
    if isinstance(v, dict):
        return not v
    return False


def _as_list(v) -> list:
    if isinstance(v, list):
        return [x for x in v]
    if _is_blank(v):
        return []
    if isinstance(v, str):
        s = v.strip().strip("[]")
        return [x.strip().strip("\"'") for x in s.split(",") if x.strip()]
    return [v]


def _as_connections(v) -> dict:
    out = {k: [] for k in _CONNECTION_KEYS}
    if isinstance(v, dict):
        for k in _CONNECTION_KEYS:
            out[k] = _as_list(v.get(k))
    elif isinstance(v, list):
        out["internal"] = _as_list(v)
    return out


def _coerce(key: str, value, kind: str):
    if key == "connections":
        return _as_connections(value)
    if _EMPTY_BY_KEY.get(key) is list:
        return _as_list(value)
    if key == "processed":
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.strip().lower() in ("true", "false"):
            return value.strip().lower() == "true"
        return False
    if key == "type" and _is_blank(value):
        return kind
    if _is_blank(value):
        return ""
    return value


def canonical_frontmatter(kind: str, data: dict,
                          allow_extra: tuple = ("aliases", "updated")) -> tuple[dict, dict]:
    """유형별 정본 키를 §3 순서대로 채운 dict 와, 버린 키를 돌려준다.

    - 없는 키는 빈 값(문자열 ""·리스트 []·불린 false·connections 두 블록)으로 채우되 키는 남긴다
    - `type` 이 비어 있으면 kind 로 채운다
    - `allow_extra` 의 키는 정본 키 뒤에 순서대로 붙여 보존한다
    - 반환하는 둘째 값은 {버린 키: 버린 값} dict 다. 키만 필요하면 그대로 순회하면 되고,
      이관 보고서에 값을 적어야 할 때는 값도 꺼낼 수 있다
    """
    if kind not in CANONICAL_KEYS:
        raise ValueError(f"알 수 없는 노트 유형입니다: {kind} (가능: {', '.join(CANONICAL_KEYS)})")
    src = dict(data or {})
    out: dict = {}
    for key in CANONICAL_KEYS[kind]:
        out[key] = _coerce(key, src.pop(key, None), kind)
    for key in allow_extra:
        if key in src:
            v = src.pop(key)
            if not _is_blank(v):
                out[key] = v
    return out, src


# ---------------------------------------------------------------- 출력

_YAML_HEAD = set("[]{}>|*&!%@`#,?-")


def _needs_quote(s: str) -> bool:
    if s == "":
        return False
    if "[[" in s:
        return True            # 위키링크 값은 따옴표로 감싼다 (§3 공통 원칙)
    if s != s.strip():
        return True
    if s[0] in _YAML_HEAD or s[0] in "\"'":
        return True
    if ": " in s or s.endswith(":"):
        return True
    return False


def _quote(s: str) -> str:
    if '"' not in s:
        return f'"{s}"'
    if "'" not in s:
        return f"'{s}'"
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _scalar_out(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    s = str(v)
    return _quote(s) if _needs_quote(s) else s


def _inline_list(items: list) -> str:
    return "[" + ", ".join(_scalar_out(x) for x in items) + "]"


def dump_frontmatter(fm: dict) -> str:
    """정본 규칙대로 frontmatter 문자열(--- 포함)을 만든다.

    날짜는 따옴표 없이, 리스트는 인라인 `[a, b]`, `[[링크]]` 값은 따옴표,
    `connections` 는 `internal`·`cross` 블록에 인라인 리스트, 빈 값은 키만 남긴다.
    `luhmann` 만은 기존 템플릿 관례대로 늘 따옴표로 감싼다.
    """
    lines = ["---"]

    def emit(d: dict, ind: int):
        pad = " " * ind
        for k, v in d.items():
            if isinstance(v, dict):
                lines.append(f"{pad}{k}:")
                emit(v, ind + 2)
            elif isinstance(v, list):
                lines.append(f"{pad}{k}: {_inline_list(v)}")
            elif k == "luhmann":
                lines.append(f'{pad}{k}: "{v}"')
            elif isinstance(v, bool):
                lines.append(f"{pad}{k}: {'true' if v else 'false'}")
            elif v is None or (isinstance(v, str) and v.strip() == ""):
                lines.append(f"{pad}{k}:")
            else:
                lines.append(f"{pad}{k}: {_scalar_out(v)}")

    emit(fm, 0)
    lines.append("---")
    return "\n".join(lines) + "\n"
