# tests/test_linker.py
# -*- coding: utf-8 -*-
import os, shutil
from pathlib import Path
import pytest
from linker import parse_index, next_number, insert_entry, new_category, check_index, parse_number

FIX = Path(__file__).parent / "fixtures/mini_wiki/3.Permanent_Notes/SlipBox/index.md"

def test_parse_number_grammar():
    assert parse_number("1A1") == (1, "A", [1])
    assert parse_number("1A1a") == (1, "A", [1, "a"])
    assert parse_number("6A57") == (6, "A", [57])
    assert parse_number("1A1a2") == (1, "A", [1, "a", 2])
    assert parse_number("abc") is None

def test_parse_roundtrip_is_byte_identical():
    text = FIX.read_text(encoding="utf-8")
    idx = parse_index(text)
    assert idx.render() == text
    assert idx.count_notes() == 10

def test_parse_sections_and_entries():
    idx = parse_index(FIX.read_text(encoding="utf-8"))
    assert [c.number for c in idx.categories] == [1, 2]
    assert [s.code for s in idx.categories[0].sections] == ["1A", "1B"]
    e = idx.find("1A1")
    assert e.title == "니클라스 루만의 제텔카스텐 시스템" and e.depth == 0
    assert idx.find("1A1b").depth == 1

def test_next_sequential_and_branch():
    idx = parse_index(FIX.read_text(encoding="utf-8"))
    assert next_number(idx, parent="1A1", relation="sequential") == "1A4"
    assert next_number(idx, parent="1A1", relation="branch") == "1A1c"
    assert next_number(idx, parent="1A2", relation="branch") == "1A2a"
    assert next_number(idx, parent="1A1a", relation="branch") == "1A1a1"
    assert next_number(idx, parent="1A1a", relation="sequential") == "1A1c"
    assert next_number(idx, section="2A", relation="sequential") == "2A2"

def test_insert_branch_after_last_child_and_updates_stats(tmp_path):
    p = tmp_path / "index.md"; shutil.copy(FIX, p)
    insert_entry(p, number="1A1c", title="새 노트", relation="branch", parent="1A1", today="2026-09-07")
    lines = p.read_text(encoding="utf-8").splitlines()
    i = lines.index("  - 1A1b [[임시메모의 본질과 루만의 실천]] ↳")
    assert lines[i + 1] == "  - 1A1c [[새 노트]] ↳"
    assert "**통계**: 총 11 노트 | 최근 업데이트: 2026-09-07" in lines

def test_insert_sequential_after_parent_subtree(tmp_path):
    p = tmp_path / "index.md"; shutil.copy(FIX, p)
    insert_entry(p, number="1A4", title="대등 노트", relation="sequential", parent="1A3", today="2026-09-07")
    lines = p.read_text(encoding="utf-8").splitlines()
    i = lines.index("- 1A3 [[이질적인 아이디어의 연결이 새로운 발견을 만든다]] →")
    assert lines[i + 1] == "- 1A4 [[대등 노트]] →"

def test_insert_rejects_duplicate(tmp_path):
    p = tmp_path / "index.md"; shutil.copy(FIX, p)
    with pytest.raises(ValueError):
        insert_entry(p, number="1A2", title="중복", relation="sequential", parent="1A1", today="2026-09-07")

def test_new_category_appends_and_returns_section(tmp_path):
    p = tmp_path / "index.md"; shutil.copy(FIX, p)
    code = new_category(p, title="화학공학 기초", description="물질수지, 열역학")
    assert code == "3A"
    text = p.read_text(encoding="utf-8")
    assert text.rstrip().endswith("### 3A 화학공학 기초")
    assert "## 3. 화학공학 기초" in text

def test_check_reports_orphan_parent():
    idx = parse_index(FIX.read_text(encoding="utf-8"))
    rep = check_index(idx)
    assert "1B4a" in rep["missing_parent"]
    assert rep["duplicates"] == []

@pytest.mark.skipif(not os.environ.get("ZETTEL_REAL_INDEX"), reason="실제 vault index 경로 미지정")
def test_real_index_roundtrip():
    text = Path(os.environ["ZETTEL_REAL_INDEX"]).read_text(encoding="utf-8")
    idx = parse_index(text)
    assert idx.render() == text
    assert idx.count_notes() >= 260
