# -*- coding: utf-8 -*-
"""교재 파일에서 텍스트를 뽑는다. .pptx 는 슬라이드별로, .md/.txt 는 통째로 통과시킨다.
표준 라이브러리만 쓴다(zipfile + xml.etree.ElementTree). .pdf 는 다루지 않는다 — Read 도구로 직접 읽는다."""
from __future__ import annotations
import json, re, sys, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"  # DrawingML: <a:p> 문단, <a:t> 텍스트
SLIDE_RE = re.compile(r"^ppt/slides/slide(\d+)\.xml$")

def slide_text(xml_bytes: bytes) -> str:
    """슬라이드 XML 한 장에서 <a:p> 문단마다 <a:t> 조각을 이어 붙여 줄 단위 텍스트로 만든다."""
    root = ET.fromstring(xml_bytes)
    lines: list[str] = []
    for para in root.iter(f"{A}p"):
        line = "".join(t.text or "" for t in para.iter(f"{A}t")).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)

def pptx_slides(path: Path | str) -> list[dict]:
    """.pptx 의 슬라이드를 번호 오름차순으로 돌려준다. 정렬 키는 문자열이 아니라 숫자다(slide10 이 slide2 앞에 오지 않게)."""
    found: list[tuple[int, str]] = []
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            m = SLIDE_RE.match(name)
            if m:
                found.append((int(m.group(1)), name))
        return [{"n": n, "text": slide_text(z.read(name))} for n, name in sorted(found)]

def extract(path: Path | str) -> dict:
    """확장자로 갈라 JSON 으로 낼 dict 를 만든다. 지원하지 않는 형식은 ValueError 로 알린다."""
    p = Path(path)
    if not p.is_file():
        raise ValueError(f"파일을 찾지 못했습니다: {p}")
    ext = p.suffix.lower()
    if ext == ".pptx":
        return {"kind": "pptx", "path": str(p), "slides": pptx_slides(p)}
    if ext in (".md", ".txt"):
        return {"kind": "text", "path": str(p), "text": p.read_text(encoding="utf-8", errors="replace")}
    if ext == ".pdf":
        raise ValueError("pdf 는 이 스크립트로 파싱하지 않습니다. Read 도구로 파일을 직접 읽으세요.")
    raise ValueError(f"지원하지 않는 형식입니다: {ext or '(확장자 없음)'}. pptx·md·txt 만 다루고 pdf 는 Read 도구로 읽으세요.")

def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1:
        print(json.dumps({"error": "사용법: python doc_text.py <파일>"}, ensure_ascii=False)); return 2
    try:
        print(json.dumps(extract(argv[0]), ensure_ascii=False))
    except (ValueError, zipfile.BadZipFile, ET.ParseError, OSError) as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False)); return 2
    return 0

if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # 한글이 콘솔 코드페이지에 깨지지 않게
    except (AttributeError, ValueError):
        pass
    sys.exit(main())
