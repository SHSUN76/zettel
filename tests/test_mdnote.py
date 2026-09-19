# -*- coding: utf-8 -*-
import pytest
from mdnote import (CANONICAL_KEYS, canonical_frontmatter, dump_frontmatter,
                    parse_frontmatter, wikilinks)

NOTE = '''---
type: permanent
title: 글쓰기는 사고의 매체
tags: [글쓰기, 사고]
luhmann: "1B1"
connections:
  internal:
    - "[[상향식 글쓰기와 창발적 구조]]"
  cross:
    - "[[지식의 연금술은 정보를 연결하고 변환하여 지혜를 만드는 것이다]]"
---
본문 [[니클라스 루만의 제텔카스텐 시스템]] 과 [[글쓰기는 실천적 기술이다|별칭]] 그리고 [[상향식 글쓰기와 창발적 구조]].
'''

def test_parse_scalars_and_inline_list():
    fm, body = parse_frontmatter(NOTE)
    assert fm["type"] == "permanent"
    assert fm["tags"] == ["글쓰기", "사고"]
    assert fm["luhmann"] == "1B1"
    assert body.startswith("본문")

def test_parse_nested_block_lists():
    fm, _ = parse_frontmatter(NOTE)
    assert fm["connections"]["internal"] == ["[[상향식 글쓰기와 창발적 구조]]"]
    assert len(fm["connections"]["cross"]) == 1

def test_wikilinks_distinct_targets_without_alias():
    _, body = parse_frontmatter(NOTE)
    assert wikilinks(body) == ["니클라스 루만의 제텔카스텐 시스템", "글쓰기는 실천적 기술이다", "상향식 글쓰기와 창발적 구조"]

def test_no_frontmatter():
    fm, body = parse_frontmatter("그냥 본문")
    assert fm == {} and body == "그냥 본문"

def test_dump_roundtrip_simple():
    fm, body = parse_frontmatter(NOTE)
    text = dump_frontmatter(fm) + body
    fm2, _ = parse_frontmatter(text)
    assert fm2 == fm

# ------------------------------------------------------------ 정본 frontmatter

def test_canonical_keeps_key_order_and_empty_keys():
    fm, _ = parse_frontmatter(NOTE)
    out, dropped = canonical_frontmatter("permanent", fm)
    assert list(out) == CANONICAL_KEYS["permanent"]
    assert out["platform"] == "" and out["author"] == "" and out["literature-note"] == ""
    assert out["date"] == "" and dropped == {}

def test_canonical_returns_unknown_keys_with_values():
    data = {"type": "permanent", "title": "t", "number": 7, "created": "2026-03-15", "aliases": ["별명"]}
    out, dropped = canonical_frontmatter("permanent", data)
    assert dropped == {"number": 7, "created": "2026-03-15"}
    assert out["aliases"] == ["별명"]          # 허용 키는 정본 키 뒤에 남는다
    assert list(out)[:len(CANONICAL_KEYS["permanent"])] == CANONICAL_KEYS["permanent"]

def test_canonical_fills_type_and_empty_containers_per_kind():
    out, _ = canonical_frontmatter("literature", {"title": "논문"})
    assert list(out) == CANONICAL_KEYS["literature"]
    assert out["type"] == "literature" and out["tags"] == [] and out["permanent-notes"] == []
    assert out["processed"] is False
    perm, _ = canonical_frontmatter("permanent", {})
    assert perm["connections"] == {"internal": [], "cross": []}
    assert list(canonical_frontmatter("fleeting", {})[0]) == CANONICAL_KEYS["fleeting"]
    assert list(canonical_frontmatter("raw", {})[0]) == CANONICAL_KEYS["raw"]

def test_canonical_rejects_unknown_kind():
    with pytest.raises(ValueError):
        canonical_frontmatter("daily", {})

def test_dump_formats_dates_lists_links_and_empty_values():
    out, _ = canonical_frontmatter("permanent", {
        "title": "연결 없는 노트는 다시 안 읽는다", "date": "2026-09-19",
        "tags": ["지식관리", "seed"], "luhmann": "1A1a",
        "literature-note": "[[제텔카스텐 독서노트]]",
        "connections": {"internal": ["[[외부 기억은 대화 상대다]]"], "cross": []}})
    text = dump_frontmatter(out)
    assert "date: 2026-09-19" in text                       # 날짜는 따옴표 없음
    assert "tags: [지식관리, seed]" in text                  # 리스트는 인라인
    assert 'literature-note: "[[제텔카스텐 독서노트]]"' in text  # 링크는 따옴표
    assert 'luhmann: "1A1a"' in text
    assert "connections:\n  internal: [\"[[외부 기억은 대화 상대다]]\"]\n  cross: []" in text
    assert "\nplatform:\n" in text                          # 빈 값은 키만
    assert parse_frontmatter(text + "본문")[0] == out        # 왕복해도 같다

def test_dump_roundtrips_link_titles_containing_commas():
    title = "[[도구 선택은 물리에 따른다 — 분자는 ORCA, 결정 표면은 QE, 빠른 탐색은 MLIP]]"
    out, _ = canonical_frontmatter("permanent", {"connections": {"internal": [title], "cross": []}})
    back, _ = parse_frontmatter(dump_frontmatter(out) + "본문")
    assert back["connections"]["internal"] == [title]        # 제목 속 쉼표가 항목을 가르지 않는다
