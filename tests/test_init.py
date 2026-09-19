# -*- coding: utf-8 -*-
import json, subprocess
from pathlib import Path
import init
from init import run_init

STRUCTURE = ["zettel.json", "CLAUDE.md", "README.md",
             "_raw/README.md",
             "1.Fleeting_Notes/_template.md",
             "2.Literature_Notes/_template.md",
             "2.Literature_Notes/Journals", "2.Literature_Notes/Books",
             "2.Literature_Notes/Seminars", "2.Literature_Notes/Lectures",
             "2.Literature_Notes/Datas",
             "3.Permanent_Notes/_template.md",
             "3.Permanent_Notes/SlipBox/index.md",
             "_meta/gate-rules.md", "_meta/rubric.md", "_reports"]

def test_init_creates_structure_and_git(tmp_path):
    root = tmp_path / "zettel"
    r = run_init(root=root, register_obsidian=False)
    for rel in STRUCTURE:
        assert (root / rel).exists(), rel
    cfg = json.loads((root / "zettel.json").read_text(encoding="utf-8"))
    assert cfg["profile"] == "personal"
    assert cfg["paths"]["index"] == "3.Permanent_Notes/SlipBox/index.md"
    assert cfg["paths"]["raw"] == "_raw"
    assert "{{date}}" not in (root / "3.Permanent_Notes/SlipBox/index.md").read_text(encoding="utf-8")
    assert r["git"]["initialized"] is True and r["git"]["first_commit"] is True
    assert r["github"]["status"].startswith("skipped")
    log = subprocess.run(["git", "log", "--oneline"], cwd=root, capture_output=True, text=True).stdout
    assert "init: zettel vault" in log

def test_init_is_idempotent(tmp_path):
    root = tmp_path / "zettel"
    run_init(root=root, register_obsidian=False)
    (root / "CLAUDE.md").write_text("내가 고친 규칙", encoding="utf-8")
    r = run_init(root=root, register_obsidian=False)
    assert (root / "CLAUDE.md").read_text(encoding="utf-8") == "내가 고친 규칙"
    assert "CLAUDE.md" in r["skipped"]

def test_obsidian_registration_writes_vault_entry(tmp_path, monkeypatch):
    appdata = tmp_path / "AppData"; monkeypatch.setenv("APPDATA", str(appdata))
    monkeypatch.setattr(init.sys, "platform", "win32")
    root = tmp_path / "zettel"
    r = run_init(root=root, register_obsidian=True)
    data = json.loads((appdata / "obsidian" / "obsidian.json").read_text(encoding="utf-8"))
    assert any(v["path"] == str(root) for v in data["vaults"].values())
    assert r["obsidian"]["registered"] is True

def test_normalize_origin_rewrites_ssh_remote(tmp_path, monkeypatch):
    calls = []
    def fake_run(cmd, cwd=None, timeout=180):
        calls.append(list(cmd))
        if cmd[:3] == ["git", "config", "--get"]:
            return 0, "git@github.com:SHSUN76/zettel-vault.git"
        return 0, ""
    monkeypatch.setattr(init, "_run", fake_run)
    url = init._normalize_origin(tmp_path, "SHSUN76/zettel-vault")
    assert url == "https://github.com/SHSUN76/zettel-vault.git"
    assert ["git", "remote", "set-url", "origin", url] in calls

def test_normalize_origin_keeps_https_remote(tmp_path, monkeypatch):
    calls = []
    def fake_run(cmd, cwd=None, timeout=180):
        calls.append(list(cmd))
        if cmd[:3] == ["git", "config", "--get"]:
            return 0, "https://github.com/SHSUN76/zettel-vault.git"
        return 0, ""
    monkeypatch.setattr(init, "_run", fake_run)
    url = init._normalize_origin(tmp_path, "SHSUN76/zettel-vault")
    assert url == "https://github.com/SHSUN76/zettel-vault.git"
    assert not any(c[:3] == ["git", "remote", "set-url"] or c[:3] == ["git", "remote", "add"] for c in calls)

def test_normalize_origin_adds_remote_when_missing(tmp_path, monkeypatch):
    calls = []
    def fake_run(cmd, cwd=None, timeout=180):
        calls.append(list(cmd))
        if cmd[:3] == ["git", "config", "--get"]:
            return 1, ""
        return 0, ""
    monkeypatch.setattr(init, "_run", fake_run)
    url = init._normalize_origin(tmp_path, "SHSUN76/zettel-vault")
    assert url == "https://github.com/SHSUN76/zettel-vault.git"
    assert ["git", "remote", "add", "origin", url] in calls
