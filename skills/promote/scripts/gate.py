# -*- coding: utf-8 -*-
"""승격 게이트: 자기 말로 재작성(8-gram 중복률) · 관련 노트 링크 수 · 주제 태그 를 스크립트가 판정한다.
LLM 점수와 무관하게 HOLD 면 승격하지 않는다. 판정은 _meta/promotion-log.jsonl 에 기록한다."""
from __future__ import annotations
import argparse, json, re, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared" / "scripts"))
from mdnote import parse_frontmatter, wikilinks  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

GROWTH = {"seed", "growing", "evergreen"}
_QUOTE = re.compile(r"[\"“][^\"”]{4,}[\"”]\s*\(\[\[[^\]]+\]\]\)")   # "인용"([[원본]])
_CONN = re.compile(r"^###\s*연결.*$", re.M)
KST = timezone(timedelta(hours=9))

def _body_for_overlap(text: str) -> str:
    _, body = parse_frontmatter(text)
    m = _CONN.search(body)
    if m:
        body = body[:m.start()]
    body = _QUOTE.sub(" ", body)
    body = re.sub(r"\[\[[^\]]+\]\]", " ", body)
    return re.sub(r"\s+", " ", body).strip().lower()

def _ngrams(s: str, n: int) -> set:
    s = re.sub(r"\s+", "", s)
    return {s[i:i + n] for i in range(max(0, len(s) - n + 1))}

def overlap_ratio(draft_text: str, source_text: str, n: int = 8) -> float:
    d = _ngrams(_body_for_overlap(draft_text), n)
    s = _ngrams(re.sub(r"\s+", " ", parse_frontmatter(source_text)[1]).lower(), n)
    return 0.0 if not d else len(d & s) / len(d)

def count_links(draft_text: str, source_stem: str) -> int:
    _, body = parse_frontmatter(draft_text)
    return len([t for t in wikilinks(body) if t != source_stem])

def topic_tags(draft_text: str) -> list[str]:
    fm, _ = parse_frontmatter(draft_text)
    tags = fm.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.strip("[]").split(",") if t.strip()]
    return [t.lstrip("#") for t in tags if t.lstrip("#") not in GROWTH]

def check(draft: Path, source: Path, min_links: int, max_overlap: float, n: int, cold_start: bool) -> dict:
    dt = Path(draft).read_text(encoding="utf-8")
    st = Path(source).read_text(encoding="utf-8")
    ov = overlap_ratio(dt, st, n)
    links = count_links(dt, Path(source).stem)
    if cold_start:
        links += 1 if Path(source).stem in wikilinks(parse_frontmatter(dt)[1]) else 0
    need = 1 if cold_start else min_links
    tags = topic_tags(dt)
    reasons = []
    if ov > max_overlap:
        reasons.append("자기 말로 재작성 안 됨")
    if links < need:
        reasons.append("연결 부족")
    if not tags:
        reasons.append("태그 없음")
    return {"verdict": "PASS" if not reasons else "HOLD", "reasons": reasons,
            "overlap": round(ov, 3), "links": links, "links_required": need, "tags": tags, "cold_start": cold_start}

def append_log(log_path: Path, row: dict, ts: str | None = None) -> None:
    log_path = Path(log_path); log_path.parent.mkdir(parents=True, exist_ok=True)
    row = {"ts": ts or datetime.now(KST).isoformat(timespec="seconds"), **row}
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("--draft", required=True); c.add_argument("--source", required=True)
    c.add_argument("--links-min", type=int, default=2); c.add_argument("--overlap-max", type=float, default=0.20)
    c.add_argument("--ngram", type=int, default=8); c.add_argument("--cold-start", action="store_true")
    lg = sub.add_parser("log"); lg.add_argument("--log", required=True); lg.add_argument("--source", required=True)
    lg.add_argument("--title", required=True); lg.add_argument("--verdict", required=True, choices=["PASS", "HOLD", "DROP"])
    lg.add_argument("--scores", default="{}"); lg.add_argument("--gate", default="{}"); lg.add_argument("--luhmann", default="")
    lg.add_argument("--model", default=""); lg.add_argument("--profile", default="personal")
    a = ap.parse_args(argv)
    if a.cmd == "check":
        print(json.dumps(check(a.draft, a.source, a.links_min, a.overlap_max, a.ngram, a.cold_start), ensure_ascii=False, indent=2))
    else:
        scores = json.loads(a.scores); vals = [v for v in scores.values() if isinstance(v, (int, float))]
        append_log(a.log, {"source": a.source, "title": a.title, "scores": scores,
                           "avg": round(sum(vals) / len(vals), 2) if vals else None, "gate": json.loads(a.gate),
                           "verdict": a.verdict, "luhmann": a.luhmann, "model": a.model, "profile": a.profile})
        print(json.dumps({"logged": True}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
