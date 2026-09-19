# -*- coding: utf-8 -*-
import json
from pathlib import Path
from gate import overlap_ratio, count_links, topic_tags, check, append_log

SOURCE = "회의가 길어지는 이유는 참석자 수가 아니라 결정 권한의 소재가 흐린 데 있다. 결정할 사람이 없는 회의는 정보 공유로 미끄러진다. 안건마다 권한 소재를 먼저 적어 두면 회의 길이가 아니라 회의 종류가 바뀐다."

COPIED = '''---
type: permanent
tags: [회의, seed]
---
회의가 길어지는 이유는 참석자 수가 아니라 결정 권한의 소재가 흐린 데 있다. 결정할 사람이 없는 회의는 정보 공유로 미끄러진다. [[2026-08-14]] [[의사결정]]
'''

OWN = '''---
type: permanent
tags: [회의, seed]
---
긴 회의의 원인을 사람 수에서 찾는 것은 헛다리다. 원문은 이 상태를 "결정할 사람이 없는 회의는 정보 공유로 미끄러진다"([[2026-08-14]])라고 적었다. 내가 보기에 핵심은 안건별로 누가 결정하는지를 먼저 못 박는 습관이며, 이는 [[의사결정]]과 [[회의 설계]]에 닿는다.
'''

def test_overlap_high_for_copy():
    assert overlap_ratio(COPIED, SOURCE, n=8) > 0.5

def test_overlap_low_for_own_words_with_quote_excluded():
    assert overlap_ratio(OWN, SOURCE, n=8) < 0.2

def test_count_links_excludes_source_and_dedups():
    assert count_links(OWN, source_stem="2026-08-14") == 2
    assert count_links(COPIED, source_stem="2026-08-14") == 1

def test_topic_tags_exclude_growth_tags():
    assert topic_tags(OWN) == ["회의"]

def test_check_verdicts(tmp_path):
    s = tmp_path / "2026-08-14.md"; s.write_text(SOURCE, encoding="utf-8")
    d1 = tmp_path / "own.md"; d1.write_text(OWN, encoding="utf-8")
    d2 = tmp_path / "copied.md"; d2.write_text(COPIED, encoding="utf-8")
    r1 = check(d1, s, min_links=2, max_overlap=0.2, n=8, cold_start=False)
    assert r1["verdict"] == "PASS" and r1["reasons"] == []
    r2 = check(d2, s, min_links=2, max_overlap=0.2, n=8, cold_start=False)
    assert r2["verdict"] == "HOLD"
    assert "자기 말로 재작성 안 됨" in r2["reasons"] and "연결 부족" in r2["reasons"]

def test_cold_start_relaxes_links(tmp_path):
    s = tmp_path / "2026-08-14.md"; s.write_text(SOURCE, encoding="utf-8")
    d = tmp_path / "d.md"
    d.write_text(OWN.replace("[[회의 설계]]", "").replace("[[의사결정]]", ""), encoding="utf-8")
    assert check(d, s, 2, 0.2, 8, cold_start=True)["verdict"] == "PASS"   # 원본 링크 1개 인정
    assert check(d, s, 2, 0.2, 8, cold_start=False)["verdict"] == "HOLD"

def test_append_log_writes_jsonl(tmp_path):
    log = tmp_path / "_meta" / "promotion-log.jsonl"
    append_log(log, {"title": "t", "verdict": "PASS", "scores": {"독립성": 4}, "luhmann": "1A1"}, ts="2026-09-07T10:00:00+09:00")
    rows = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["ts"].startswith("2026-09-07") and rows[0]["luhmann"] == "1A1"
