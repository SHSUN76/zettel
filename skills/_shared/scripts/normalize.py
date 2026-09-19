# -*- coding: utf-8 -*-
"""영구노트 본문을 정본(스타일 A)으로 옮기고, 옮기면서 글자를 잃지 않았는지 검사한다.

설계서 §3.1 의 변환 표를 그대로 구현한다.

| 원 헤더 | 정본 |
|---|---|
| 핵심 아이디어 · 메모 | `>[!메모]` 콜아웃 |
| 상세 설명 · 예시/사례 | `### 원문 (출처)` 뒤 `**상세 설명**`·`**예시/사례**` 소제목 |
| 출처/참고 | `### 원문 (출처)` |
| 추가 질문 · 개인적 질문 · 나의 생각과 질문 · 질문 | `### 생각 (질문)` |
| 연결된 아이디어 · 관련 노트 | `### 연결 (이유)` (마지막 절) |
| (없음) | `### 추천 (주제)` 는 만들지 않음. `### 연결 (이유)` 가 없으면 빈 절로 추가 |

표에 없는 헤더는 `### 생각 (질문)` 아래 `**원헤더**` 소제목으로 보존한다.
`### 날짜`·`### 태그` 줄은 frontmatter(meta)에서 다시 만든다.

절 순서 정본은 **날짜 → 태그 → 메모 → 원문 (출처) → 생각 (질문) → [추천 (주제)] → 연결 (이유)** 이며
`추천 (주제)` 는 선택 절이다. 이미 스타일 A 인 노트는 **절 순서를 재배열하지 않는다** — 날짜·태그 줄을
meta 값으로 보정하고 빠진 `연결 (이유)` 빈 절을 끝에 붙이는 것이 전부다.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mdnote import parse_frontmatter  # noqa: E402

_HEADER = re.compile(r"^(#{1,6})(?:\s+(.*))?$")
_MEMO_CALLOUT = re.compile(r"^>\s*\[!\s*메모\s*\]")
_BOLD_ONLY = re.compile(r"^\*\*[^*]+\*\*$")
_RULE = "---"

SLOT_ORDER = ("memo", "source", "thought", "recommend", "link")
SLOT_HEADERS = {
    "source": "### 원문 (출처)",
    "thought": "### 생각 (질문)",
    "recommend": "### 추천 (주제)",
    "link": "### 연결 (이유)",
}
# `### 연결 (이유)` 가 없는 노트에 붙이는 빈 절. 사용자 템플릿과 같은 두 줄이다.
CONNECTION_PLACEHOLDER = ("- 🔗 내부 연결:", "- ⚡ 횡단 연결:")

# 원 헤더 → (정본 슬롯, 소제목). 소제목이 None 이면 절 본문에 바로 붙인다.
_HEADER_MAP: dict[str, tuple[str, str | None]] = {
    "메모": ("memo", None),
    "핵심 아이디어": ("memo", None),
    "원문 (출처)": ("source", None),
    "원문": ("source", None),
    "출처/참고": ("source", None),
    "출처·참고": ("source", None),
    "출처": ("source", None),
    "참고": ("source", None),
    "상세 설명": ("source", "**상세 설명**"),
    "예시/사례": ("source", "**예시/사례**"),
    "예시·사례": ("source", "**예시/사례**"),
    "예시": ("source", "**예시/사례**"),
    "사례": ("source", "**예시/사례**"),
    "생각 (질문)": ("thought", None),
    "생각": ("thought", None),
    "추가 질문": ("thought", None),
    "개인적 질문": ("thought", None),
    "나의 생각과 질문": ("thought", None),
    "질문": ("thought", None),
    "연결 (이유)": ("link", None),
    "연결": ("link", None),
    "연결된 아이디어": ("link", None),
    "관련 노트": ("link", None),
    "추천 (주제)": ("recommend", None),
    "추천": ("recommend", None),
}

_DROP_HEADS = ("날짜", "태그")

_A_HEADS = {"날짜", "태그", "원문 (출처)", "생각 (질문)", "연결 (이유)", "추천 (주제)"}
_B_HEADS = {"핵심 아이디어", "상세 설명", "예시/사례", "예시·사례",
            "연결된 아이디어", "추가 질문", "출처/참고", "출처·참고", "관련 노트"}
_C_HEADS = {"메모", "개인적 질문", "나의 생각과 질문", "출처/참고", "출처·참고", "질문"}


def _norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _head_key(raw: str) -> str:
    """헤더 문구에서 비교용 키를 뽑는다. `날짜 : 2026-01-01` 처럼 값이 붙은 줄은 앞부분만 쓴다."""
    return _norm_space(raw.split(":", 1)[0])


def _is_header(line: str) -> bool:
    m = _HEADER.match(line.rstrip())
    return bool(m)


def _scan_heads(body: str) -> tuple[set, bool]:
    heads, callout = set(), False
    for raw in body.splitlines():
        line = raw.rstrip()
        if _MEMO_CALLOUT.match(line.lstrip()):
            callout = True
            continue
        m = _HEADER.match(line)
        if m and m.group(2):
            heads.add(_head_key(m.group(2)))
    return heads, callout


def detect_style(body: str) -> str:
    """본문이 어느 서식인지 판정한다. A(정본) · B · C · other."""
    heads, callout = _scan_heads(body)
    score = {
        "A": len(heads & _A_HEADS) + (1 if callout else 0),
        "B": len(heads & _B_HEADS),
        "C": len(heads & _C_HEADS),
    }
    best = max(score.values())
    if best == 0:
        return "other"
    for k in ("A", "B", "C"):          # 동점이면 정본 쪽을 고른다
        if score[k] == best:
            return k
    return "other"


# ---------------------------------------------------------------- 본문 변환

def _strip_quote(line: str) -> str:
    s = line.rstrip()
    if s.lstrip().startswith(">"):
        s = s.lstrip()[1:]
        if s.startswith(" "):
            s = s[1:]
    return s


def _trim(lines: list[str]) -> list[str]:
    out = list(lines)
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return out


def _split_footer(lines: list[str]) -> tuple[list[str], list[str]]:
    """본문 끝의 `---` 뒤 꼬리말(생성일 표기·태그 줄 등)을 떼어 낸다. 없으면 빈 목록."""
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == _RULE:
            tail = lines[i + 1:]
            if any(t.strip() for t in tail) and not any(_is_header(t) for t in tail):
                return lines[:i], lines[i:]
            return lines, []
    return lines, []


def _split_blocks(lines: list[str]) -> list[tuple[str | None, int, list[str]]]:
    """(헤더 문구 | None, 헤더 레벨, 내용 줄) 목록으로 쪼갠다. 첫 블록의 헤더는 None(머리말)."""
    blocks: list[tuple[str | None, int, list[str]]] = []
    head: str | None = None
    level = 0
    buf: list[str] = []
    for raw in lines:
        line = raw.rstrip("\n")
        if _MEMO_CALLOUT.match(line.lstrip()):
            blocks.append((head, level, buf))
            head, level, buf = "메모", 0, []
            continue
        m = _HEADER.match(line.rstrip())
        if m:
            blocks.append((head, level, buf))
            head, level, buf = (m.group(2) or "").strip(), len(m.group(1)), []
            continue
        buf.append(line)
    blocks.append((head, level, buf))
    return [b for b in blocks if b[0] is not None or any(x.strip() for x in b[2])]


def _date_line(meta: dict) -> str:
    return f"### 날짜 : {str(meta.get('date') or '').strip()}".rstrip()


def _tag_line(meta: dict) -> str:
    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.strip("[]").split(",") if t.strip()]
    marked = " ".join("#" + str(t).lstrip("#") for t in tags if str(t).strip())
    return f"### 태그 : {marked}".rstrip()


def _has_value(meta: dict, key: str) -> bool:
    v = meta.get(key)
    return bool(v) if not isinstance(v, str) else bool(v.strip())


def _find_head(lines: list[str], match) -> int | None:
    """조건에 맞는 헤더 줄의 위치. match 는 (키, 원문) 을 받아 bool 을 낸다."""
    for i, raw in enumerate(lines):
        m = _HEADER.match(raw.rstrip())
        if m and m.group(2) and match(_head_key(m.group(2)), m.group(2).strip()):
            return i
    return None


def _find_link_section(lines: list[str]) -> int | None:
    return _find_head(lines, lambda key, raw: (_HEADER_MAP.get(key) or (None, None))[0] == "link")


def _lstrip_blank(lines: list[str]) -> list[str]:
    out = list(lines)
    while out and not out[0].strip():
        out.pop(0)
    return out


def normalize_permanent_body(body: str, meta: dict | None = None) -> str:
    """영구노트 본문을 정본(스타일 A)으로 바꾼다. 헤더만 바꾸고 텍스트 줄은 버리지 않는다.

    이미 스타일 A 인 본문은 절 순서를 건드리지 않고 날짜·태그 줄 보정과
    빠진 `### 연결 (이유)` 빈 절 추가만 한다.
    """
    meta = meta or {}
    lines = body.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if detect_style(body) == "A":
        return _touch_style_a(lines, meta)
    return _convert_to_style_a(lines, meta)


def _touch_style_a(lines: list[str], meta: dict) -> str:
    """스타일 A 본문: 절을 재배열하지 않는다. 날짜·태그 줄 보정 + 연결 절 보강뿐."""
    out = list(lines)
    i_date = _find_head(out, lambda key, raw: key == "날짜")
    i_tag = _find_head(out, lambda key, raw: key == "태그")
    if i_date is not None:
        if _has_value(meta, "date"):           # meta 에 값이 없으면 기존 줄을 지우지 않는다
            out[i_date] = _date_line(meta)
    if i_tag is not None:
        if _has_value(meta, "tags"):
            out[i_tag] = _tag_line(meta)
    if i_tag is None:
        out = [_tag_line(meta), ""] + _lstrip_blank(out)
    if i_date is None:
        out = [_date_line(meta), ""] + _lstrip_blank(out)
    if _find_link_section(out) is None:
        out = _trim(out) + ["", SLOT_HEADERS["link"], *CONNECTION_PLACEHOLDER]
    return "\n".join(_trim(out)) + "\n"


def _convert_to_style_a(lines: list[str], meta: dict) -> str:
    """스타일 B·C·기타 본문을 정본 절 순서로 옮긴다. `추천 (주제)` 는 내용이 있을 때만 쓴다."""
    lines, footer = _split_footer(lines)
    buckets: dict[str, list[tuple[str | None, list[str]]]] = {s: [] for s in SLOT_ORDER}

    for head, level, content in _split_blocks(lines):
        if head is None:                       # 머리말은 메모 콜아웃으로 올린다
            buckets["memo"].append((None, content))
            continue
        key = _head_key(head)
        if key in _DROP_HEADS:                 # 날짜·태그 줄은 meta 에서 다시 만든다
            if any(x.strip() for x in content):
                buckets["thought"].append((f"**{_norm_space(head)}**", content))
            continue
        mapped = _HEADER_MAP.get(key) or _HEADER_MAP.get(_norm_space(head))
        if mapped:
            slot, sub = mapped
            if slot == "memo":
                content = [_strip_quote(x) for x in content]
            buckets[slot].append((sub, content))
        elif level == 1:                       # 본문 첫 줄의 제목 헤더
            buckets["memo"].append((None, content))
        else:
            buckets["thought"].append((f"**{_norm_space(head)}**", content))

    out: list[str] = [_date_line(meta), "", _tag_line(meta), ""]
    out += _render_memo(buckets["memo"])
    for slot in ("source", "thought"):
        out.append("")
        out.append(SLOT_HEADERS[slot])
        out += _render_section(buckets[slot])
    recommend = _render_section(buckets["recommend"])
    if recommend:                              # 선택 절: 원절이 없으면 만들지 않는다
        out.append("")
        out.append(SLOT_HEADERS["recommend"])
        out += recommend
    out.append("")                             # 연결 (이유) 는 필수이며 마지막 절이다
    out.append(SLOT_HEADERS["link"])
    out += _render_section(buckets["link"]) or list(CONNECTION_PLACEHOLDER)
    if footer:
        out.append("")
        out += _trim(footer)
    return "\n".join(out).rstrip() + "\n"


def _render_memo(entries: list[tuple[str | None, list[str]]]) -> list[str]:
    body: list[str] = []
    for _sub, content in entries:
        content = _trim(content)
        if not content:
            continue
        if body:
            body.append("")
        body += content
    out = [">[!메모]"]
    for ln in body:
        out.append(">" if not ln.strip() else f"> {ln}")
    return out


def _render_section(entries: list[tuple[str | None, list[str]]]) -> list[str]:
    ordered = sorted(range(len(entries)), key=lambda i: (entries[i][0] is not None, i))
    body: list[str] = []
    for i in ordered:
        sub, content = entries[i][0], _trim(entries[i][1])
        if sub is None and not content:
            continue
        if body:
            body.append("")
        if sub:
            body.append(sub)
        body += content
    return body


# ---------------------------------------------------------------- 보존 검사

def text_lines(md: str) -> set:
    """헤더·빈 줄·콜아웃 접두 `> `·소제목 굵은 글씨 마커·빈 절 자리표시를 제외한 텍스트 줄 집합.

    자리표시(`- 🔗 내부 연결:` · `- ⚡ 횡단 연결:` 와 내용 없는 `-`)는 구조이지 글이 아니므로
    양쪽에서 함께 빠진다. 그래서 빠진 `연결 (이유)` 빈 절을 채워 넣어도 보존 검사를 통과한다.
    """
    out: set = set()
    for raw in md.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        s = raw.strip()
        while s.startswith(">"):
            s = s[1:].strip()
        if not s:
            continue
        if _HEADER.match(s):
            continue
        if s.startswith("[!"):
            continue
        if _BOLD_ONLY.match(s):
            continue
        if s in CONNECTION_PLACEHOLDER or s in ("-", "*", "•"):
            continue
        out.add(s)
    return out


def assert_text_preserved(before: str, after: str) -> None:
    """변환 전후의 텍스트 줄 집합이 같지 않으면 AssertionError 를 낸다."""
    a, b = text_lines(before), text_lines(after)
    lost, added = sorted(a - b), sorted(b - a)
    if lost or added:
        raise AssertionError(
            "본문 텍스트가 보존되지 않았습니다. "
            f"사라진 줄 {len(lost)}개: {lost[:5]} / 생긴 줄 {len(added)}개: {added[:5]}")


# ---------------------------------------------------------------- CLI

def check_file(path: Path) -> dict:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    fm, body = parse_frontmatter(text)
    style = detect_style(body)
    row = {"file": str(path), "style": style, "preserved": None, "error": ""}
    try:
        after = normalize_permanent_body(body, fm)
        assert_text_preserved(body, after)
        row["preserved"] = True
    except AssertionError as e:
        row["preserved"] = False
        row["error"] = str(e)
    return row


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="영구노트 본문 서식 판정·보존 검사")
    ap.add_argument("--check", nargs="+", required=True, metavar="파일")
    a = ap.parse_args(argv)
    rows = [check_file(Path(p)) for p in a.check]
    summary: dict = {"total": len(rows), "styles": {}, "not_preserved": 0}
    for r in rows:
        summary["styles"][r["style"]] = summary["styles"].get(r["style"], 0) + 1
        if not r["preserved"]:
            summary["not_preserved"] += 1
    print(json.dumps({"files": rows, "summary": summary}, ensure_ascii=False, indent=2))
    return 1 if summary["not_preserved"] else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    sys.exit(main())
