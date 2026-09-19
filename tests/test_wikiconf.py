# -*- coding: utf-8 -*-
import json
from pathlib import Path
import pytest
from wikiconf import find_root, load, WikiConfigError, CONFIG_NAME

def make_vault(tmp: Path, **over):
    cfg = json.loads((Path(__file__).parents[1] / "templates/personal/zettel.json").read_text(encoding="utf-8"))
    cfg.update(over)
    (tmp / CONFIG_NAME).write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    return tmp

def test_config_name_is_zettel_json():
    assert CONFIG_NAME == "zettel.json"

def test_find_root_walks_up(tmp_path):
    make_vault(tmp_path)
    deep = tmp_path / "3.Permanent_Notes" / "SlipBox"; deep.mkdir(parents=True)
    assert find_root(deep) == tmp_path

def test_missing_config_raises(tmp_path):
    with pytest.raises(WikiConfigError):
        load(tmp_path)

def test_paths_are_resolved_absolute(tmp_path):
    make_vault(tmp_path)
    c = load(tmp_path)
    assert c.path("index") == tmp_path / "3.Permanent_Notes" / "SlipBox" / "index.md"
    assert c.path("raw") == tmp_path / "_raw"
    assert c.gate["min_links"] == 2 and c.profile == "personal"
