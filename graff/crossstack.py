"""Кросс-стек связи Graff: фронтенд-вызов fetch('/api/..') → бэкенд-роут.

Создаёт узлы kind='Route' (по конвенциям Next.js pages/api и app/api) и связи
HTTP_CALL от вызывающей функции к роуту. Это даёт full-stack поток: где во
фронте дёргают эндпоинт ↔ какой файл его обслуживает.
"""
from __future__ import annotations

import os
import re

from .graph import GraphStore, Node, Edge

# строковый литерал пути /api/... (в fetch/axios/ky и т.п.)
RE_API_LITERAL = re.compile(r"""['"`](/api/[A-Za-z0-9_\-/\[\].]+)""")
SRC_EXT = (".ts", ".tsx", ".js", ".jsx", ".mjs")


def _route_from_path(rel: str) -> str | None:
    """Вернуть route-путь из файла Next.js или None."""
    p = rel.replace("\\", "/")
    for marker in ("/pages/api/", "/app/api/"):
        if marker in p:
            tail = p.split(marker, 1)[1]
            tail = re.sub(r"\.(ts|tsx|js|jsx|mjs)$", "", tail)
            if marker.endswith("app/api/"):
                tail = re.sub(r"/route$", "", tail)
            tail = re.sub(r"/index$", "", tail)
            # [id] → :id (динамические сегменты)
            tail = re.sub(r"\[(\.{3})?([^\]]+)\]", r":\2", tail)
            return "/api/" + tail if tail else "/api"
    return None


def build_routes(store: GraphStore) -> dict[str, str]:
    """Создать Route-узлы по api-файлам. Вернуть {route_path: route_uid}."""
    routes: dict[str, str] = {}
    new_nodes, new_edges = [], []
    files = store.conn.execute(
        "SELECT uid, file_path FROM nodes WHERE kind='File'"
    ).fetchall()
    for f in files:
        route = _route_from_path(f["file_path"])
        if not route:
            continue
        uid = f"Route:{route}"
        if uid in routes:
            continue
        routes[uid] = route
        new_nodes.append(Node(uid, "Route", route, f["file_path"],
                              parent_uid=f["uid"], language="http"))
        new_edges.append(Edge(f["uid"], "CONTAINS", dst_uid=uid,
                              file_path=f["file_path"], line=1))
    store.add_nodes(new_nodes)
    store.add_edges(new_edges)
    return {route: uid for uid, route in routes.items()}


def _match_route(literal: str, route_index: dict[str, str]) -> str | None:
    """Сопоставить /api/.. литерал с роутом. Точное совпадение → иначе самый
    длинный статический префикс динамического роута."""
    lit = literal.split("?")[0].rstrip("/")
    if lit in route_index:
        return route_index[lit]
    best = None
    best_len = -1
    for route, uid in route_index.items():
        static = route.split(":")[0].rstrip("/")  # префикс до первого :param
        if static and lit.startswith(static) and len(static) > best_len:
            best, best_len = uid, len(static)
    return best


def _enclosing_func(store: GraphStore, file_path: str, line: int):
    rows = store.conn.execute(
        "SELECT uid FROM nodes WHERE file_path=? AND kind IN ('Function','Method') "
        "AND start_line<=? AND end_line>=? ORDER BY start_line DESC LIMIT 1",
        (file_path, line, line),
    ).fetchone()
    return rows["uid"] if rows else None


def link_http_calls(store: GraphStore, repo_path: str, route_index: dict[str, str]) -> int:
    """Просканировать фронт-исходники на /api/.. литералы, связать вызывающую
    функцию с роутом (HTTP_CALL)."""
    if not route_index:
        return 0
    files = store.conn.execute(
        "SELECT DISTINCT file_path FROM nodes WHERE language IN "
        "('typescript','tsx','javascript')"
    ).fetchall()
    edges = []
    for f in files:
        rel = f["file_path"]
        # сам роут-файл пропускаем (он обслуживает, а не зовёт)
        if "/api/" in rel:
            continue
        full = os.path.join(repo_path, rel)
        try:
            with open(full, encoding="utf-8", errors="replace") as fp:
                text = fp.read()
        except OSError:
            continue
        if "/api/" not in text:
            continue
        for m in RE_API_LITERAL.finditer(text):
            route_uid = _match_route(m.group(1), route_index)
            if not route_uid:
                continue
            line = text.count("\n", 0, m.start()) + 1
            src_uid = _enclosing_func(store, rel, line) or f"File:{rel}"
            edges.append(Edge(src_uid, "HTTP_CALL", dst_uid=route_uid,
                              confidence=0.9, file_path=rel, line=line))
    store.add_edges(edges)
    return len(edges)


def build_crossstack(store: GraphStore, repo_path: str) -> dict:
    # очистить прежние кросс-стек артефакты (для реиндекса)
    store.conn.execute("DELETE FROM edges WHERE type='HTTP_CALL'")
    store.conn.execute("DELETE FROM nodes WHERE kind='Route'")
    route_index = build_routes(store)
    links = link_http_calls(store, repo_path, route_index)
    store.commit()
    return {"routes": len(route_index), "http_calls": links}
