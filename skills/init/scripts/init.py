# -*- coding: utf-8 -*-
"""zettel vault 구축: 템플릿 복사(멱등) → zettel.json → git init·첫 커밋 → (선택) GitHub 비공개 저장소 → Obsidian 보관소 등록.
GitHub 단계 실패는 요약에 남기고 종료 코드를 올리지 않는다."""
from __future__ import annotations
import argparse, json, os, secrets, shutil, subprocess, sys, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_DIR = PLUGIN_ROOT / "templates" / "personal"

def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 180) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except FileNotFoundError:
        return 127, f"{cmd[0]} not found"
    except subprocess.TimeoutExpired:
        return 124, "timeout"

def copy_templates(root: Path, today: str) -> tuple[list[str], list[str]]:
    created, skipped = [], []
    for src in sorted(TEMPLATE_DIR.rglob("*")):
        rel = src.relative_to(TEMPLATE_DIR)
        dst = root / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True); continue
        if dst.exists():
            skipped.append(str(rel).replace("\\", "/")); continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix in (".md", ".json") or src.name in (".gitignore", ".gitkeep"):
            text = src.read_text(encoding="utf-8").replace("{{date}}", today)
            dst.write_text(text, encoding="utf-8", newline="\n")
        else:
            shutil.copy2(src, dst)
        created.append(str(rel).replace("\\", "/"))
    return created, skipped

def git_init(root: Path) -> dict:
    out = {"initialized": False, "first_commit": False, "detail": ""}
    if not (root / ".git").exists():
        rc, msg = _run(["git", "init", "-b", "main"], root)
        if rc != 0:
            out["detail"] = msg; return out
    out["initialized"] = True
    _run(["git", "config", "core.autocrlf", "false"], root)
    rc, _ = _run(["git", "rev-parse", "HEAD"], root)
    if rc != 0:
        _run(["git", "add", "-A"], root)
        rc, msg = _run(["git", "-c", "user.name=zettel", "-c", "user.email=zettel@local", "commit", "-m", "init: zettel vault"], root)
        out["first_commit"] = rc == 0; out["detail"] = msg[-300:]
    else:
        out["first_commit"] = True
    return out

def _normalize_origin(root: Path, full: str) -> str:
    """origin 을 https 주소로 고정하고 그 주소를 돌려준다. 이미 https 면 그대로 둔다.
    저장된 값을 봐야 하므로 `git remote get-url` 대신 `git config --get` 을 쓴다(get-url 은 url.insteadOf 치환을 적용한 주소를 돌려줘 ssh 원격이 보이지 않는다)."""
    https = f"https://github.com/{full}.git"
    rc, url = _run(["git", "config", "--get", "remote.origin.url"], root)
    url = url.strip()
    if rc != 0 or not url:
        _run(["git", "remote", "add", "origin", https], root)
        return https
    if url.startswith(("git@github.com:", "ssh://git@github.com/", "ssh://github.com/")):
        rc, _ = _run(["git", "remote", "set-url", "origin", https], root)
        return https if rc == 0 else url
    return url

def github_setup(root: Path, repo: str) -> dict:
    """비공개 저장소를 만들고 https 원격으로 push 한다. 저장소가 이미 있으면 push 만 한다."""
    out = {"status": "", "repo": "", "pushed": False, "remote_url": ""}
    rc, _ = _run(["gh", "--version"])
    if rc != 0:
        out["status"] = "skipped: gh not found"; return out
    _run(["gh", "config", "set", "git_protocol", "https"])  # 22번 포트(SSH)가 막힌 망을 대비해 https 로 고정
    rc, _ = _run(["gh", "auth", "status"])
    if rc != 0:
        out["status"] = "skipped: not logged in"; return out
    _run(["gh", "auth", "setup-git"])  # git credential helper 를 gh 로 붙인다(https push 인증). 실패해도 진행한다
    rc, login = _run(["gh", "api", "user", "-q", ".login"])
    if rc != 0:
        out["status"] = "skipped: cannot read user"; return out
    full = f"{login.strip()}/{repo}"
    rc, _ = _run(["gh", "repo", "view", full])
    if rc != 0:
        rc, msg = _run(["gh", "repo", "create", repo, "--private", "--source", str(root), "--remote", "origin", "--push"], root, timeout=300)
        if rc != 0:
            out["status"] = "failed: repo create"; out["detail"] = msg[-300:]; return out
        out["pushed"] = True; out["remote_url"] = _normalize_origin(root, full)
    else:
        out["remote_url"] = _normalize_origin(root, full)
        rc, _ = _run(["git", "push", "-u", "origin", "main"], root, timeout=300)
        out["pushed"] = rc == 0
    out["repo"] = full
    out["status"] = "ok" if out["pushed"] else "partial"
    return out

def obsidian_config_path() -> tuple[Path | None, str]:
    """OS별 Obsidian vault 목록 파일 위치. (경로, 실패 사유) 를 돌려준다."""
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "obsidian" / "obsidian.json", ""
    if sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        if not appdata:
            return None, "APPDATA 없음"
        return Path(appdata) / "obsidian" / "obsidian.json", ""
    return Path.home() / ".config" / "obsidian" / "obsidian.json", ""

def register_obsidian_vault(root: Path) -> dict:
    cfg, why = obsidian_config_path()
    if cfg is None:
        return {"registered": False, "detail": why}
    try:
        data = json.loads(cfg.read_text(encoding="utf-8")) if cfg.exists() else {}
        vaults = data.setdefault("vaults", {})
        if any(Path(v.get("path", "")) == root for v in vaults.values()):
            return {"registered": True, "detail": "이미 등록됨"}
        vaults[secrets.token_hex(8)] = {"path": str(root), "ts": int(time.time() * 1000), "open": True}
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8", newline="\n")
        return {"registered": True, "detail": "추가됨"}
    except Exception as e:  # noqa: BLE001
        return {"registered": False, "detail": str(e)[:200]}

def run_init(root: Path, github_private: str | None = None, register_obsidian: bool = True) -> dict:
    root = Path(root).resolve(); root.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone(timedelta(hours=9))).date().isoformat()  # KST
    created, skipped = copy_templates(root, today)
    summary = {"root": str(root), "created": created, "skipped": skipped, "git": git_init(root)}
    summary["github"] = github_setup(root, github_private) if github_private else {"status": "skipped: --github-private 없음"}
    summary["obsidian"] = register_obsidian_vault(root) if register_obsidian else {"registered": False, "detail": "skipped"}
    steps = []
    if github_private and summary["github"].get("status") != "ok":
        steps.append("GitHub 연결이 안 됐습니다. `gh auth login` 후 `/zettel:init --github-private <이름>` 을 다시 실행하세요.")
    steps.append("Obsidian 을 열어 보관소를 확인하세요.")
    steps.append("`/zettel:capture <한 줄 생각>` 으로 첫 임시노트를 남겨 보세요.")
    summary["next_steps"] = steps
    return summary

def main(argv=None):
    ap = argparse.ArgumentParser(description="zettel vault 초기화")
    ap.add_argument("--root", default=".", help="vault 를 만들 폴더 (기본: 현재 폴더)")
    ap.add_argument("--github-private", metavar="이름", help="이 이름으로 GitHub 비공개 저장소를 만들고 push 한다")
    ap.add_argument("--no-obsidian", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    s = run_init(Path(a.root), github_private=a.github_private, register_obsidian=not a.no_obsidian)
    if a.json:
        print(json.dumps(s, ensure_ascii=False, indent=2))
    else:
        print(f"zettel: {s['root']}  생성 {len(s['created'])}개, 유지 {len(s['skipped'])}개")
        print(f"git: {s['git']}"); print(f"GitHub: {s['github']}"); print(f"Obsidian: {s['obsidian']}")
        for n in s["next_steps"]: print(" -", n)
    return 0

if __name__ == "__main__":
    sys.exit(main())
