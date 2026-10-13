"""Проверка PR через GitHub REST API (без ручных проверок).

Токен: GH_TOKEN / GITHUB_TOKEN из окружения (.env.local) или `gh auth token --user <владелец репо>` (затем активный аккаунт gh).
Репозиторий: HW_GH_REPO=owner/name, иначе — из `git remote origin` каталога проекта.
PR: HW_GH_PR=номер, иначе — PR текущей ветки, иначе — последний PR автора токена.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from settings import section

S = section("gh_api")


def get_token(owner: str | None = None) -> str | None:
    """Токен из окружения; иначе из gh — сначала аккаунта владельца репозитория (приватный репо чужого аккаунта даёт 404), затем активного."""
    for k in ("GH_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(k):
            return os.environ[k]
    if shutil.which("gh"):
        for extra in ([["--user", owner]] if owner else []) + [[]]:
            try:
                r = subprocess.run(["gh", "auth", "token", *extra], capture_output=True, text=True, timeout=S["cmd_timeout_s"])
                if r.returncode == 0 and r.stdout.strip():
                    return r.stdout.strip()
            except Exception:  # noqa: BLE001
                pass
    return None


def _git(args: list[str], cwd: Path) -> str:
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=S["cmd_timeout_s"])
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:  # noqa: BLE001
        return ""


def detect_repo(project_dir: Path) -> str | None:
    if os.environ.get("HW_GH_REPO"):
        return os.environ["HW_GH_REPO"].strip()
    url = _git(["remote", "get-url", "origin"], project_dir)
    m = re.search(S["regex"]["repo_from_remote"], url)
    return f"{m.group(1)}/{m.group(2)}" if m else None


def api(path: str, token: str | None):
    req = urllib.request.Request(S["api_url"] + path if path.startswith("/") else path)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", S["user_agent"])
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=S["http_timeout_s"]) as r:
        return json.loads(r.read().decode("utf-8"))


def find_pr(repo: str, token: str | None, project_dir: Path) -> dict | None:
    if os.environ.get("HW_GH_PR"):
        return api(f"/repos/{repo}/pulls/{int(os.environ['HW_GH_PR'])}", token)
    owner = repo.split("/")[0]
    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], project_dir)
    if branch and branch not in S["default_branches"]:
        prs = api(f"/repos/{repo}/pulls?state=all&head={owner}:{branch}&per_page={S['per_page']['branch_pr']}", token)
        if prs:
            return prs[0]
    if token:
        me = api("/user", token)["login"]
        prs = api(f"/repos/{repo}/pulls?state=all&per_page={S['per_page']['author_prs']}&sort=created&direction=desc", token)
        for pr in prs:
            if pr["user"]["login"] == me:
                return pr
    prs = api(f"/repos/{repo}/pulls?state=all&per_page={S['per_page']['latest_pr']}&sort=created&direction=desc", token)
    return prs[0] if prs else None


def clean_body(body: str) -> str:
    """Тело PR без HTML-комментариев, пустых чекбоксов и заголовков шаблона."""
    b = re.sub(r"<!--.*?-->", "", body or "", flags=re.S)
    b = re.sub(r"^\s*[-*]\s*\[ \].*$", "", b, flags=re.M)
    b = re.sub(r"^\s*#{1,6}\s.*$", "", b, flags=re.M)
    return re.sub(r"\s+", " ", b).strip()


def ci_state(repo: str, sha: str, token: str | None) -> tuple[str, str]:
    """('success'|'failure'|'none'|'pending', пояснение) по запускам Actions для head-коммита PR."""
    runs = api(f"/repos/{repo}/actions/runs?head_sha={sha}&per_page={S['per_page']['actions_runs']}", token).get("workflow_runs", [])
    if not runs:
        return "none", "запусков GitHub Actions для коммита PR нет"
    latest: dict[str, dict] = {}
    me = os.environ.get("GITHUB_RUN_ID")
    for r in runs:                      # API отдаёт новые первыми
        if me and str(r["id"]) == me:   # сам запуск проверки не считаем
            continue
        latest.setdefault(r["name"], r)
    bad = [n for n, r in latest.items() if r["status"] == "completed" and r["conclusion"] not in S["ok_conclusions"]]
    pend = [n for n, r in latest.items() if r["status"] != "completed"]
    ok = [n for n, r in latest.items() if r["conclusion"] == "success"]
    if bad:
        return "failure", f"не прошли: {', '.join(bad)}"
    if pend and not ok:
        return "pending", f"ещё идут: {', '.join(pend)}"
    return ("success", f"успешно: {', '.join(ok)}") if ok else ("none", "нет успешных запусков")


def pr_report(project_dir: Path) -> dict:
    """Единый отчёт для чекера. Ключи: error | repo, pr{...}, ci(state, msg)."""
    repo = detect_repo(project_dir)
    if not repo:
        return {"error": "репозиторий не определён: задайте HW_GH_REPO=owner/name (или git remote origin)"}
    token = get_token(repo.split("/")[0])
    if not token:
        return {"error": "нет токена GitHub: запустите `just wizard` (или gh auth login)", "repo": repo}
    try:
        pr = find_pr(repo, token, project_dir)
    except urllib.error.HTTPError as e:
        return {"error": f"GitHub API {e.code}: {e.reason} (репозиторий {repo})", "repo": repo}
    except Exception as e:  # noqa: BLE001
        return {"error": f"GitHub API недоступен: {type(e).__name__}: {str(e)[:100]}", "repo": repo}
    if not pr:
        return {"repo": repo, "pr": None}
    body = pr.get("body") or ""
    out = {"repo": repo, "pr": {
        "number": pr["number"], "url": pr["html_url"], "title": pr.get("title") or "", "state": pr["state"],
        "merged": bool(pr.get("merged_at")), "body_len": len(clean_body(body)),
        "has_image": bool(re.search(S["regex"]["pr_image"], body, flags=re.I)),
        "has_versions": bool(re.search(S["regex"]["pr_versions"], body, flags=re.I)),
        "has_ci_link": bool(re.search(S["regex"]["pr_ci_link"], body)),
        "sha": pr["head"]["sha"]}}
    try:
        out["ci"] = ci_state(repo, pr["head"]["sha"], token)
    except Exception as e:  # noqa: BLE001
        out["ci"] = ("unknown", f"не удалось получить запуски Actions: {str(e)[:80]}")
    return out
