"""Аналитика графа Graff: хотспоты, мёртвый код, циклические импорты.

Графовые алгоритмы поверх GraphStore (без внешних зависимостей).
"""
from __future__ import annotations

from .graph import GraphStore

# имена-«точки входа» — без входящих вызовов, но НЕ мёртвые
ENTRY_NAMES = {
    "main", "parse", "start_requests", "start", "process_item", "handler",
    "default", "handle", "run", "setup", "__init__", "errback",
    "open_spider", "close_spider", "from_crawler",
}
ENTRY_PREFIX = ("test_", "parse_", "handle_", "cmd_", "rule_", "_")


def hotspots(store: GraphStore, limit: int = 20) -> dict:
    """Самые зависимые символы (высокий in-degree) = высокий риск при изменении."""
    rows = store.conn.execute(
        "SELECT dst_uid, count(*) deg FROM edges "
        "WHERE dst_uid IS NOT NULL AND type IN ('CALLS','IMPORTS','INHERITS','HTTP_CALL') "
        "GROUP BY dst_uid ORDER BY deg DESC LIMIT ?", (limit,)
    ).fetchall()
    out = []
    for r in rows:
        n = store.get_node(r["dst_uid"])
        if n and n["kind"] in ("Function", "Method", "Class", "Route"):
            out.append({"uid": n["uid"], "name": n["name"], "kind": n["kind"],
                        "filePath": n["file_path"], "line": n["start_line"],
                        "dependents": r["deg"]})
    return {"hotspots": out}


def dead_code(store: GraphStore, limit: int = 50) -> dict:
    """Функции/методы без входящих вызовов (кандидаты в мёртвый код). Точки входа
    (parse/handler/main/test_/route-хендлеры) исключены."""
    rows = store.conn.execute(
        "SELECT n.uid, n.name, n.kind, n.file_path, n.start_line, n.language FROM nodes n "
        "WHERE n.kind IN ('Function','Method') AND n.language='python' AND NOT EXISTS ("
        "  SELECT 1 FROM edges e WHERE e.dst_uid=n.uid AND e.type IN ('CALLS','HTTP_CALL'))"
    ).fetchall()
    out = []
    for r in rows:
        name = r["name"]
        if name in ENTRY_NAMES or name.startswith(ENTRY_PREFIX):
            continue
        if "/api/" in r["file_path"]:
            continue
        out.append({"uid": r["uid"], "name": name, "kind": r["kind"],
                    "filePath": r["file_path"], "line": r["start_line"]})
    out.sort(key=lambda x: x["filePath"])
    # advisory: кросс-язык (Python↔TS) и динамические вызовы не отслеживаются
    return {"candidateCount": len(out), "advisory": "кандидаты; кросс-язык/динамика не учтены",
            "deadCandidates": out[:limit]}


def _module_to_file(store: GraphStore) -> dict[str, str]:
    mod2file: dict[str, str] = {}
    for r in store.conn.execute(
        "SELECT file_path FROM nodes WHERE kind='File' AND language='python'"
    ):
        parts = r["file_path"][:-3].split("/")
        for i in range(len(parts)):
            mod2file.setdefault(".".join(parts[i:]), r["file_path"])
        mod2file.setdefault(parts[-1], r["file_path"])
    return mod2file


def cycles(store: GraphStore, limit: int = 20) -> dict:
    """Циклические импорты между Python-файлами (DFS по file→file графу импортов)."""
    mod2file = _module_to_file(store)
    graph: dict[str, set[str]] = {}
    for r in store.conn.execute("SELECT file_path, module FROM imports"):
        src = r["file_path"]
        if not src.endswith(".py"):
            continue
        mod = r["module"]
        dst = mod2file.get(mod) or mod2file.get(mod.split(".")[-1])
        if dst and dst != src:
            graph.setdefault(src, set()).add(dst)

    found: list[list[str]] = []
    WHITE, GREY, BLACK = 0, 1, 2
    color: dict[str, int] = {}
    stack: list[str] = []

    def dfs(u: str):
        color[u] = GREY
        stack.append(u)
        for v in graph.get(u, ()):
            if color.get(v, WHITE) == GREY:
                # цикл: от v до конца стека
                if v in stack:
                    cyc = stack[stack.index(v):] + [v]
                    if len(found) < limit:
                        found.append(cyc)
            elif color.get(v, WHITE) == WHITE:
                dfs(v)
        stack.pop()
        color[u] = BLACK

    for node in list(graph.keys()):
        if color.get(node, WHITE) == WHITE:
            dfs(node)

    # дедуп циклов по множеству файлов
    uniq = []
    seen = set()
    for c in found:
        key = frozenset(c)
        if key not in seen:
            seen.add(key)
            uniq.append(c)
    return {"cycleCount": len(uniq), "cycles": uniq}
