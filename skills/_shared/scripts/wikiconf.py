# -*- coding: utf-8 -*-
"""zettel.json 을 현재 폴더에서 위로 올라가며 찾고, 경로를 절대경로로 해석한다."""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_NAME = "zettel.json"

class WikiConfigError(RuntimeError):
    pass

def find_root(start: Path | str | None = None) -> Path:
    p = Path(start or Path.cwd()).resolve()
    for cand in [p, *p.parents]:
        if (cand / CONFIG_NAME).is_file():
            return cand
    raise WikiConfigError(f"{CONFIG_NAME} 을 찾지 못했습니다. zettel vault 안에서 실행하세요. (시작 위치: {p})")

@dataclass
class WikiConfig:
    root: Path
    raw: dict
    profile: str = "personal"
    paths: dict = field(default_factory=dict)
    gate: dict = field(default_factory=dict)
    growth: dict = field(default_factory=dict)
    fleeting_types: dict = field(default_factory=dict)

    def path(self, key: str) -> Path:
        if key not in self.paths:
            raise WikiConfigError(f"paths.{key} 가 설정에 없습니다")
        return (self.root / self.paths[key]).resolve()

def load(start: Path | str | None = None) -> WikiConfig:
    root = find_root(start)
    try:
        raw = json.loads((root / CONFIG_NAME).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise WikiConfigError(f"{CONFIG_NAME} 이 올바른 JSON 이 아닙니다: {e}")
    if raw.get("schema") != 1:
        raise WikiConfigError("지원하지 않는 schema 버전입니다 (1 이어야 함)")
    return WikiConfig(root=root, raw=raw, profile=raw.get("profile", "personal"),
                      paths=raw.get("paths", {}), gate=raw.get("gate", {}),
                      growth=raw.get("growth", {}), fleeting_types=raw.get("fleeting_types", {}))

if __name__ == "__main__":
    import sys as _s
    try:
        _s.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    try:
        c = load(); print(json.dumps({"root": str(c.root), **c.raw}, ensure_ascii=False, indent=2))
    except WikiConfigError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False)); _s.exit(2)
