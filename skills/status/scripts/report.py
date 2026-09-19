# -*- coding: utf-8 -*-
"""vault 통계·성장 태그·승격 로그를 집계해 _reports/status_YYMMDD.{md,json} 을 쓴다."""
from __future__ import annotations
import argparse, json, subprocess, sys
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared" / "scripts"))
from mdnote import parse_frontmatter, wikilinks  # noqa: E402
from wikiconf import load  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

GROWTH = ("seed", "growing", "evergreen")
COUNTED = ("raw", "fleeting", "literature", "permanent")

def _index_dir(cfg) -> str:
    """paths.index 가 든 폴더 이름(예: SlipBox). 노트 수에서 이 폴더를 뺀다."""
    parts = Path(cfg.paths.get("index", "")).parts
    return parts[-2].lower() if len(parts) >= 2 else ""

def _md_files(d: Path, skip_dir: str = ""):
    if not d.exists():
        return []
    return [p for p in d.rglob("*.md")
            if not p.name.startswith("_") and (not skip_dir or skip_dir not in [x.lower() for x in p.parts])]

def build_report(root: Path) -> dict:
    cfg = load(root)
    skip = _index_dir(cfg)
    perm_dir = cfg.path("permanent")
    notes, out_links = [], {}
    for p in _md_files(perm_dir, skip):
        fm, body = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        tags = fm.get("tags", []) if isinstance(fm.get("tags"), list) else []
        growth = next((t.lstrip("#") for t in tags if t.lstrip("#") in GROWTH), "seed")
        links = wikilinks(body)
        out_links[p.stem] = links
        notes.append({"title": p.stem, "luhmann": fm.get("luhmann", ""), "growth": growth, "out": len(links)})
    inbound = Counter()
    for src, links in out_links.items():
        for t in links:
            if t in out_links and t != src:
                inbound[t] += 1
    for n in notes:
        n["in"] = inbound.get(n["title"], 0)
    counts = {k: len(_md_files(cfg.path(k), skip)) for k in COUNTED if k in cfg.paths}
    processed = sum(1 for p in _md_files(cfg.path("fleeting"), skip)
                    if parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))[0].get("processed") is True)
    log_path = cfg.path("meta") / "promotion-log.jsonl"
    rows = [json.loads(l) for l in log_path.read_text(encoding="utf-8").splitlines() if l.strip()] if log_path.exists() else []
    verdicts = Counter(r.get("verdict") for r in rows)
    hold_reasons = Counter(x for r in rows if r.get("verdict") == "HOLD" for x in (r.get("gate") or {}).get("reasons", []))
    by_day = Counter(r["ts"][:10] for r in rows if r.get("verdict") == "PASS")
    g_in, e_in = cfg.growth.get("growing_inbound", 3), cfg.growth.get("evergreen_inbound", 5)
    cands = {"growing": [n["title"] for n in notes if n["growth"] == "seed" and n["in"] >= g_in],
             "evergreen": [n["title"] for n in notes if n["growth"] != "evergreen" and n["in"] >= e_in]}
    try:
        last_commit = subprocess.run(["git", "log", "-1", "--format=%cI"], cwd=root, capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        last_commit = ""
    return {"root": str(root), "counts": counts, "fleeting_processed": processed,
            "growth": dict(Counter(n["growth"] for n in notes)),
            "avg_links": round(sum(n["out"] + n["in"] for n in notes) / len(notes), 2) if notes else 0.0,
            "orphans": [n["title"] for n in notes if n["in"] == 0],
            "promotions": {k: verdicts.get(k, 0) for k in ("PASS", "HOLD", "DROP")},
            "hold_reasons": hold_reasons.most_common(3), "pass_by_day": dict(sorted(by_day.items())),
            "growth_candidates": cands, "last_commit": last_commit, "notes": notes}

def render_md(r: dict, today: str) -> str:
    c = r["counts"]
    note_counts = " / ".join(str(c.get(k, 0)) for k in COUNTED)
    L = [f"# zettel 현황 보고서 ({today})", "",
         "| 항목 | 값 |", "|---|---|",
         f"| 노트 수 (원자료/임시/문헌/영구) | {note_counts} |",
         f"| 임시노트 처리 완료 | {r['fleeting_processed']} |",
         f"| 성장 단계 (seed/growing/evergreen) | {r['growth'].get('seed',0)} / {r['growth'].get('growing',0)} / {r['growth'].get('evergreen',0)} |",
         f"| 노트당 평균 링크 수 | {r['avg_links']} |",
         f"| 고아 노트 | {len(r['orphans'])} |",
         f"| 승격 판정 (PASS/HOLD/DROP) | {r['promotions']['PASS']} / {r['promotions']['HOLD']} / {r['promotions']['DROP']} |",
         f"| 마지막 commit | {r['last_commit'] or '없음'} |", ""]
    if r["hold_reasons"]:
        L += ["## HOLD 사유 상위", *[f"- {k}: {v}건" for k, v in r["hold_reasons"]], ""]
    if r["growth_candidates"]["growing"] or r["growth_candidates"]["evergreen"]:
        L += ["## 성장 태그 승급 후보", *[f"- growing 후보: [[{t}]]" for t in r["growth_candidates"]["growing"]],
              *[f"- evergreen 후보: [[{t}]]" for t in r["growth_candidates"]["evergreen"]], ""]
    if r["orphans"]:
        L += ["## 고아 노트 (들어오는 링크 0)", *[f"- [[{t}]]" for t in r["orphans"]], ""]
    return "\n".join(L)

def write_report(root: Path, today: str | None = None):
    today = today or date.today().isoformat()
    r = build_report(root)
    cfg = load(root); out = cfg.path("reports"); out.mkdir(parents=True, exist_ok=True)
    stem = f"status_{today[2:4]}{today[5:7]}{today[8:10]}"
    md = out / f"{stem}.md"; js = out / f"{stem}.json"
    md.write_text(render_md(r, today), encoding="utf-8", newline="\n")
    js.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return md, js

def main(argv=None):
    ap = argparse.ArgumentParser(description="zettel 현황 보고서")
    ap.add_argument("--root", default="."); ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    md, js = write_report(Path(a.root).resolve())
    print(json.dumps({"md": str(md), "json": str(js)}, ensure_ascii=False) if a.json else f"보고서: {md}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
