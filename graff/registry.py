"""Глобальный реестр репозиториев Graff (~/.graff/registry.json).

Позволяет одному MCP-серверу обслуживать несколько проектов: каждый
проиндексированный репо регистрируется (путь, алиас, расположение graph.db,
статистика). Граф репо лежит в <repo>/.graff/graph.db.
"""
from __future__ import annotations

import json
import os
import time
from typing import Optional

GRAFF_HOME = os.environ.get("GRAFF_HOME") or os.path.expanduser("~/.graff")
REGISTRY = os.path.join(GRAFF_HOME, "registry.json")


def _ensure_home():
    os.makedirs(GRAFF_HOME, exist_ok=True)


def db_path_for(repo_path: str) -> str:
    return os.path.join(os.path.abspath(repo_path), ".graff", "graph.db")


def load() -> dict:
    if not os.path.exists(REGISTRY):
        return {"repos": {}}
    try:
        with open(REGISTRY, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"repos": {}}


def save(data: dict):
    _ensure_home()
    tmp = REGISTRY + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, REGISTRY)


def register(repo_path: str, alias: Optional[str], stats: dict):
    repo_path = os.path.abspath(repo_path)
    data = load()
    data["repos"][repo_path] = {
        "alias": alias or os.path.basename(repo_path),
        "db": db_path_for(repo_path),
        "indexed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "nodes": stats.get("nodes", 0),
        "edges": stats.get("edges", 0),
    }
    save(data)


def unregister(target: str) -> bool:
    data = load()
    entry = resolve(target)
    if not entry:
        return False
    path = entry["_path"]
    if path in data["repos"]:
        del data["repos"][path]
        save(data)
        return True
    return False


def list_repos() -> list[dict]:
    data = load()
    out = []
    for path, meta in data["repos"].items():
        m = dict(meta)
        m["_path"] = path
        out.append(m)
    return out


def resolve(target: Optional[str]) -> Optional[dict]:
    """Найти репо по абсолютному пути, алиасу или basename. Без target —
    единственный репо (если он один) или текущий каталог."""
    repos = list_repos()
    if target is None:
        cwd = os.path.abspath(os.getcwd())
        for r in repos:
            if r["_path"] == cwd:
                return r
        return repos[0] if len(repos) == 1 else None
    target_abs = os.path.abspath(target)
    for r in repos:
        if r["_path"] == target_abs or r["alias"] == target or \
           os.path.basename(r["_path"]) == target:
            return r
    return None
