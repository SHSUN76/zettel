# -*- coding: utf-8 -*-
import json, shutil
from pathlib import Path
from report import build_report, write_report

FIX = Path(__file__).parent / "fixtures/mini_wiki"

def test_counts_and_inbound(tmp_path):
    w = tmp_path / "w"; shutil.copytree(FIX, w)
    r = build_report(w)
    assert r["counts"]["permanent"] == 4          # SlipBox/index.md 는 세지 않는다
    assert set(r["counts"]) == {"raw", "fleeting", "literature", "permanent"}
    assert r["growth"]["seed"] >= 1
    assert isinstance(r["avg_links"], float)
    assert set(r["orphans"]) <= {n["title"] for n in r["notes"]}

def test_promotion_log_summary(tmp_path):
    w = tmp_path / "w"; shutil.copytree(FIX, w)
    r = build_report(w)
    assert r["promotions"]["PASS"] == 2 and r["promotions"]["HOLD"] == 1
    assert r["hold_reasons"][0][0] == "연결 부족"

def test_growth_candidates_use_config_thresholds(tmp_path):
    w = tmp_path / "w"; shutil.copytree(FIX, w)
    cfg = json.loads((w / "zettel.json").read_text(encoding="utf-8"))
    cfg["growth"]["growing_inbound"] = 1
    (w / "zettel.json").write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    r = build_report(w)
    assert r["growth_candidates"]["growing"]  # 인바운드 1 이상인 seed 노트가 후보

def test_write_report_creates_status_md_and_json(tmp_path):
    w = tmp_path / "w"; shutil.copytree(FIX, w)
    md, js = write_report(w, today="2026-10-05")
    assert md.name == "status_261005.md" and js.name == "status_261005.json" and js.exists()
    assert "노트 수" in md.read_text(encoding="utf-8")
