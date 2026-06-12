"""Анализатор Graff: обходит репозиторий, парсит файлы, наполняет граф.

analyze(repo_path) → парсит Python (ast) и прочие языки (tree-sitter),
батч-вставка nodes/edges, 2-й проход разрешения связей по имени, регистрация
в глобальном реестре. Граф пишется в <repo>/.graff/graph.db.
"""
# Copyright (c) 2025 BAI / AItestsibiria. Business Source License 1.1.
# Commercial SaaS use requires a commercial license: egnovoselov@gmail.com

from __future__ import annotations

import os
import time
from typing import Optional

from . import registry
from .crossstack import build_crossstack
from .graph import GraphStore
from .parsers import ext_to_lang, parse_python, parse_treesitter

IGNORE_DIRS = {
    ".git", ".graff", "node_modules", ".venv", "venv", "__pycache__",
    "dist", "build", ".next", ".cache", "vendor", "coverage", ".pytest_cache",
    "site-packages", ".mypy_cache", ".tox", "target", "out", ".idea", ".vscode",
}
IGNORE_SUFFIX = (".min.js", ".min.css", ".map", ".lock", ".pyc", ".d.ts")
MAX_FILE_BYTES = int(os.environ.get("GRAFF_MAX_FILE_KB", "800")) * 1024


def _iter_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]
        for fn in filenames:
            if fn.endswith(IGNORE_SUFFIX):
                continue
            full = os.path.join(dirpath, fn)
            yield full


def _lang_for(path: str) -> Optional[str]:
    if path.endswith(".py"):
        return "python"
    ext = os.path.splitext(path)[1].lower()
    return ext_to_lang.get(ext)


def _parse_one(repo_path: str, full: str, lang: str):
    """Распарсить один файл → (rel, nodes, edges, imports) либо None."""
    try:
        if os.path.getsize(full) > MAX_FILE_BYTES:
            return None
        with open(full, encoding="utf-8", errors="replace") as f:
            src = f.read()
    except OSError:
        return None
    rel = os.path.relpath(full, repo_path)
    try:
        if lang == "python":
            nodes, edges, imports = parse_python(rel, src)
        else:
            nodes, edges, imports = parse_treesitter(rel, src, lang)
    except Exception:
        return None
    return rel, nodes, edges, imports


def analyze(repo_path: str, alias: Optional[str] = None, verbose: bool = False) -> dict:
    repo_path = os.path.abspath(repo_path)
    db_path = registry.db_path_for(repo_path)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    store = GraphStore(db_path)
    store.reset()

    t0 = time.time()
    files_ok = 0
    files_skip = 0
    by_lang: dict[str, int] = {}
    node_batch = []
    edge_batch = []

    for full in _iter_files(repo_path):
        lang = _lang_for(full)
        if not lang:
            continue
        res = _parse_one(repo_path, full, lang)
        if res is None:
            files_skip += 1
            continue
        rel, nodes, edges, imports = res
        node_batch.extend(nodes)
        edge_batch.extend(edges)
        store.add_imports(rel, imports)
        store.set_file(rel, os.path.getmtime(full), lang)
        files_ok += 1
        by_lang[lang] = by_lang.get(lang, 0) + 1
        if len(node_batch) > 5000:
            store.add_nodes(node_batch)
            store.add_edges(edge_batch)
            node_batch, edge_batch = [], []

    if node_batch:
        store.add_nodes(node_batch)
        store.add_edges(edge_batch)
    store.commit()

    resolved = store.resolve_edges_by_name()
    resolved += store.resolve_imports_python()
    cross = build_crossstack(store, repo_path)
    counts = store.counts()
    elapsed = round(time.time() - t0, 1)

    store.set_meta("repo_path", repo_path)
    store.set_meta("indexed_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    store.set_meta("files", str(files_ok))
    store.set_meta("languages", ",".join(f"{k}:{v}" for k, v in sorted(by_lang.items())))
    store.set_meta("elapsed_s", str(elapsed))
    store.commit()
    store.close()

    registry.register(repo_path, alias, counts)

    return {
        "repo": repo_path,
        "db": db_path,
        "files_ok": files_ok,
        "files_skip": files_skip,
        "by_lang": by_lang,
        "nodes": counts["nodes"],
        "edges": counts["edges"],
        "by_kind": counts["by_kind"],
        "edges_resolved": resolved,
        "routes": cross["routes"],
        "http_calls": cross["http_calls"],
        "elapsed_s": elapsed,
    }


def update(repo_path: str) -> dict:
    """Инкрементальный реиндекс: переписать только изменённые/новые файлы
    (по mtime), удалить исчезнувшие. Полный реиндекс если граф ещё не создан."""
    repo_path = os.path.abspath(repo_path)
    db_path = registry.db_path_for(repo_path)
    if not os.path.exists(db_path):
        return analyze(repo_path)

    store = GraphStore(db_path)
    known = store.get_files()  # path → mtime
    seen: set[str] = set()
    changed = 0
    t0 = time.time()

    for full in _iter_files(repo_path):
        lang = _lang_for(full)
        if not lang:
            continue
        rel = os.path.relpath(full, repo_path)
        seen.add(rel)
        try:
            mtime = os.path.getmtime(full)
        except OSError:
            continue
        if rel in known and abs(known[rel] - mtime) < 1e-6:
            continue  # не менялся
        res = _parse_one(repo_path, full, lang)
        if res is None:
            continue
        _, nodes, edges, imports = res
        store.delete_file_subgraph(rel)
        store.add_nodes(nodes)
        store.add_edges(edges)
        store.add_imports(rel, imports)
        store.set_file(rel, mtime, lang)
        changed += 1

    deleted = [p for p in known if p not in seen]
    for rel in deleted:
        store.delete_file_subgraph(rel)
    store.commit()

    resolved = store.resolve_edges_by_name()
    resolved += store.resolve_imports_python()
    build_crossstack(store, repo_path)
    counts = store.counts()
    store.set_meta("indexed_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    store.commit()
    store.close()
    registry.register(repo_path, None, counts)

    return {
        "repo": repo_path,
        "changed": changed,
        "deleted": len(deleted),
        "nodes": counts["nodes"],
        "edges": counts["edges"],
        "edges_resolved": resolved,
        "elapsed_s": round(time.time() - t0, 2),
    }


def detect_changes(repo_path: str, ref: str = "HEAD") -> dict:
    """Сопоставить git-diff (рабочее дерево vs ref) с символами графа и оценить
    blast radius каждого затронутого символа."""
    import subprocess
    from . import queries

    repo_path = os.path.abspath(repo_path)
    db_path = registry.db_path_for(repo_path)
    if not os.path.exists(db_path):
        return {"error": "репо не проиндексирован: graff analyze"}

    try:
        out = subprocess.run(
            ["git", "-C", repo_path, "diff", "--name-only", ref],
            capture_output=True, text=True, timeout=20,
        )
        changed_files = [f for f in out.stdout.splitlines() if f.strip()]
    except Exception as e:
        return {"error": f"git diff не удался: {e}"}

    store = GraphStore(db_path)
    affected_symbols = []
    for rel in changed_files:
        rows = store.conn.execute(
            "SELECT uid,name,kind,file_path,start_line FROM nodes "
            "WHERE file_path=? AND kind IN ('Class','Function','Method')", (rel,)
        ).fetchall()
        for r in rows:
            imp = queries.impact(store, r["uid"], max_depth=2)
            affected_symbols.append({
                "uid": r["uid"], "name": r["name"], "kind": r["kind"],
                "filePath": r["file_path"], "line": r["start_line"],
                "impactedCount": imp.get("impactedCount", 0),
                "risk": imp.get("risk", "LOW"),
            })
    store.close()
    affected_symbols.sort(key=lambda x: -x["impactedCount"])
    overall = ("HIGH" if any(s["risk"] == "HIGH" for s in affected_symbols)
               else "MEDIUM" if any(s["risk"] == "MEDIUM" for s in affected_symbols)
               else "LOW")
    return {
        "ref": ref,
        "changedFiles": len(changed_files),
        "affectedSymbols": len(affected_symbols),
        "overallRisk": overall,
        "symbols": affected_symbols[:30],
    }
