# skills/_shared/scripts/linker.py
# -*- coding: utf-8 -*-
"""slipbox/index.md 를 원문 줄 단위로 보존하며 파싱하고, 다음 루만 번호를 계산하고, 한 줄만 삽입한다.
번호 문법: <카테고리 숫자><섹션 대문자><순번>( <소문자> <숫자>? )*   예: 1A1, 1A1a, 1A1a2, 6A57
줄 형식:  '- 1A1 [[제목]] (Entry)' / '  - 1A1a [[제목]] ↳' / '- 1A2 [[제목]] →'  (들여쓰기 2칸 = 깊이 1)
"""
from __future__ import annotations
import argparse, json, re, sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None

_NUM = re.compile(r"^(\d+)([A-Z])(\d+)((?:[a-z]\d*)*)$")
_ENTRY = re.compile(r"^(?P<ind>(?:  )*)- (?P<num>\d+[A-Z]\d+(?:[a-z]\d*)*) \[\[(?P<title>[^\]]+)\]\](?P<tail>.*)$")
_CAT = re.compile(r"^## (?P<n>\d+)\. (?P<title>.+?)\s*$")
_SEC = re.compile(r"^### (?P<code>\d+[A-Z]) (?P<title>.+?)\s*$")
_STATS = re.compile(r"^\*\*통계\*\*: 총 (\d+) 노트 \| 최근 업데이트: (\d{4}-\d{2}-\d{2})\s*$")

def parse_number(s: str):
    m = _NUM.match(s or "")
    if not m:
        return None
    cat, sec, first, rest = int(m.group(1)), m.group(2), int(m.group(3)), m.group(4)
    parts: list = [first]
    for tok in re.findall(r"[a-z]\d*", rest):
        parts.append(tok[0])
        if len(tok) > 1:
            parts.append(int(tok[1:]))
    return cat, sec, parts

def format_number(cat: int, sec: str, parts: list) -> str:
    return f"{cat}{sec}" + "".join(str(p) for p in parts)

def _write(path, text: str) -> None:
    """줄끝 변환 없이 그대로 기록한다(Windows 의 write_text 는 \n 을 \r\n 으로 바꾼다)."""
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)

@dataclass
class Entry:
    line_no: int
    number: str
    title: str
    depth: int
    tail: str
    section: str

@dataclass
class Section:
    code: str
    title: str
    line_no: int
    entries: list = field(default_factory=list)

@dataclass
class Category:
    number: int
    title: str
    line_no: int
    sections: list = field(default_factory=list)

@dataclass
class Index:
    lines: list
    categories: list
    stats_line: int | None

    def render(self) -> str:
        return "".join(self.lines)

    def entries(self):
        for c in self.categories:
            for s in c.sections:
                yield from s.entries

    def count_notes(self) -> int:
        return sum(1 for _ in self.entries())

    def find(self, number: str):
        for e in self.entries():
            if e.number == number:
                return e
        return None

    def section(self, code: str):
        for c in self.categories:
            for s in c.sections:
                if s.code == code:
                    return s
        return None

def parse_index(text: str) -> Index:
    lines = text.splitlines(keepends=True)
    cats: list[Category] = []
    stats = None
    cur_cat = cur_sec = None
    for i, raw in enumerate(lines):
        line = raw.rstrip("\r\n")
        if stats is None and _STATS.match(line):
            stats = i
        m = _CAT.match(line)
        if m:
            cur_cat = Category(int(m.group("n")), m.group("title"), i); cats.append(cur_cat); cur_sec = None; continue
        m = _SEC.match(line)
        if m and cur_cat is not None:
            cur_sec = Section(m.group("code"), m.group("title"), i); cur_cat.sections.append(cur_sec); continue
        m = _ENTRY.match(line)
        if m and cur_sec is not None:
            depth = len(m.group("ind")) // 2
            cur_sec.entries.append(Entry(i, m.group("num"), m.group("title"), depth, m.group("tail"), cur_sec.code))
    return Index(lines, cats, stats)

def _parent_number(number: str) -> str | None:
    cat, sec, parts = parse_number(number)
    return format_number(cat, sec, parts[:-1]) if len(parts) > 1 else None

def _children(idx: Index, parent: str) -> list[Entry]:
    return [e for e in idx.entries() if _parent_number(e.number) == parent]

def _siblings(idx: Index, number: str) -> list[Entry]:
    cat, sec, parts = parse_number(number)
    depth = len(parts)
    par = _parent_number(number)
    out = []
    for e in idx.entries():
        pn = parse_number(e.number)
        if pn and pn[0] == cat and pn[1] == sec and len(pn[2]) == depth and _parent_number(e.number) == par:
            out.append(e)
    return out

def _bump(part):
    return part + 1 if isinstance(part, int) else chr(ord(part) + 1)

def next_number(idx: Index, parent: str | None = None, section: str | None = None, relation: str = "sequential") -> str:
    if parent is None:
        if not section:
            raise ValueError("parent 또는 section 이 필요합니다")
        m = re.match(r"^(\d+)([A-Z])$", section)
        if not m:
            raise ValueError(f"섹션 코드 형식 오류: {section}")
        cat, sec = int(m.group(1)), m.group(2)
        tops = [parse_number(e.number)[2][0] for e in idx.entries()
                if parse_number(e.number)[:2] == (cat, sec) and len(parse_number(e.number)[2]) == 1]
        return format_number(cat, sec, [max(tops) + 1 if tops else 1])
    pn = parse_number(parent)
    if pn is None:
        raise ValueError(f"번호 형식 오류: {parent}")
    cat, sec, parts = pn
    if relation == "branch":
        kids = _children(idx, parent)
        if isinstance(parts[-1], int):          # 1A1 -> 1A1a
            last = max((parse_number(k.number)[2][-1] for k in kids), default=None)
            return format_number(cat, sec, parts + [_bump(last) if last else "a"])
        last = max((parse_number(k.number)[2][-1] for k in kids), default=0)   # 1A1a -> 1A1a1
        return format_number(cat, sec, parts + [last + 1])
    if relation == "sequential":
        sibs = _siblings(idx, parent)
        last = max((parse_number(s.number)[2][-1] for s in sibs), default=parts[-1])
        return format_number(cat, sec, parts[:-1] + [_bump(last)])
    raise ValueError("relation 은 sequential 또는 branch")

def _subtree_end(idx: Index, e: Entry) -> int:
    """e 와 그 후손이 차지하는 마지막 줄 번호"""
    end = e.line_no
    sec = idx.section(e.section)
    for other in sec.entries:
        if other.line_no > e.line_no:
            if other.depth <= e.depth:
                break
            end = other.line_no
    return end

def insert_entry(path: Path, number: str, title: str, relation: str, parent: str | None, today: str | None = None, section: str | None = None) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    idx = parse_index(text)
    if idx.find(number):
        raise ValueError(f"번호 {number} 가 이미 있습니다")
    nl = "\r\n" if "\r\n" in text else "\n"
    if parent:
        pe = idx.find(parent)
        if pe is None:
            raise ValueError(f"부모 {parent} 가 index 에 없습니다")
        if relation == "branch":
            kids = _children(idx, parent)
            anchor = _subtree_end(idx, kids[-1]) if kids else pe.line_no
            depth = pe.depth + 1; marker = "↳"
        else:
            anchor = _subtree_end(idx, pe); depth = pe.depth; marker = "→"
    else:
        s = idx.section(section or "")
        if s is None:
            raise ValueError(f"섹션 {section} 이 없습니다")
        anchor = _subtree_end(idx, s.entries[-1]) if s.entries else s.line_no
        depth = 0; marker = "(Entry)" if not s.entries else "→"
    new_line = f"{'  ' * depth}- {number} [[{title}]] {marker}{nl}"
    lines = idx.lines[:]
    lines.insert(anchor + 1, new_line)
    if idx.stats_line is not None:
        n = idx.count_notes() + 1
        lines[idx.stats_line] = f"**통계**: 총 {n} 노트 | 최근 업데이트: {today or date.today().isoformat()}{nl}"
    _write(path, "".join(lines))
    return {"inserted": new_line.strip(), "after_line": anchor + 1, "total": idx.count_notes() + 1}

def new_category(path: Path, title: str, description: str = "") -> str:
    text = Path(path).read_text(encoding="utf-8")
    idx = parse_index(text)
    nl = "\r\n" if "\r\n" in text else "\n"
    n = max((c.number for c in idx.categories), default=0) + 1
    code = f"{n}A"
    block = f"{nl}---{nl}{nl}## {n}. {title}{nl}" + (f"{description}{nl}" if description else "") + f"{nl}### {code} {title}{nl}"
    _write(path, text.rstrip("\r\n") + nl + block)
    return code

def check_index(idx: Index) -> dict:
    seen, dups, missing = set(), [], []
    for e in idx.entries():
        if e.number in seen:
            dups.append(e.number)
        seen.add(e.number)
    for e in idx.entries():
        p = _parent_number(e.number)
        if p and p not in seen:
            missing.append(e.number)
    return {"total": idx.count_notes(), "duplicates": dups, "missing_parent": missing}

class _Parser(argparse.ArgumentParser):
    """인자 오류도 JSON + 종료코드 1 로 통일한다(기본 argparse 는 stderr + 2)."""

    def error(self, message):
        print(json.dumps({"error": message}, ensure_ascii=False))
        raise SystemExit(1)


def main(argv=None):
    ap = _Parser(description="slipbox index 도우미")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("parse", "next", "insert", "new-category", "check"):
        sp = sub.add_parser(name); sp.add_argument("--index", required=True)
        if name == "next":
            sp.add_argument("--parent"); sp.add_argument("--section"); sp.add_argument("--relation", default="sequential")
        if name == "insert":
            sp.add_argument("--number", required=True); sp.add_argument("--title", required=True)
            sp.add_argument("--relation", default="sequential"); sp.add_argument("--parent"); sp.add_argument("--section")
        if name == "new-category":
            sp.add_argument("--title", required=True); sp.add_argument("--description", default="")
    a = ap.parse_args(argv)
    p = Path(a.index)
    try:
        if a.cmd == "parse":
            idx = parse_index(p.read_text(encoding="utf-8"))
            out = {"categories": [{"number": c.number, "title": c.title, "sections": [{"code": s.code, "title": s.title,
                    "entries": [{"number": e.number, "title": e.title, "depth": e.depth} for e in s.entries]} for s in c.sections]} for c in idx.categories],
                   "total": idx.count_notes()}
        elif a.cmd == "next":
            idx = parse_index(p.read_text(encoding="utf-8"))
            out = {"next": next_number(idx, a.parent, a.section, a.relation)}
        elif a.cmd == "insert":
            out = insert_entry(p, a.number, a.title, a.relation, a.parent, section=a.section)
        elif a.cmd == "new-category":
            out = {"section": new_category(p, a.title, a.description)}
        else:
            out = check_index(parse_index(p.read_text(encoding="utf-8")))
    except (ValueError, FileNotFoundError) as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False)); return 1
    print(json.dumps(out, ensure_ascii=False, indent=2)); return 0

if __name__ == "__main__":
    sys.exit(main())
