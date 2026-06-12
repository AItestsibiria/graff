"""Инструменты запросов Graff: find / context / impact / flows.

Работают поверх GraphStore. Возвращают сериализуемые dict (для CLI-JSON и MCP).
"""
from __future__ import annotations

from typing import Optional

from .graph import GraphStore


def _row_brief(r) -> dict:
    return {
        "uid": r["uid"], "name": r["name"], "kind": r["kind"],
        "filePath": r["file_path"], "line": r["start_line"],
    }


def _resolve(store: GraphStore, target: str, kind: Optional[str] = None):
    """Вернуть (node_row, candidates). Если node_row — нашли однозначно;
    если candidates — неоднозначно/нашли похожие."""
    # явный uid
    if ":" in target:
        n = store.get_node(target)
        if n:
            return n, None
    exact = store.find_by_name(target, kind=kind)
    if len(exact) == 1:
        return exact[0], None
    if len(exact) > 1:
        return None, exact
    # фаззи-поиск
    fuzzy = store.search(target, limit=10)
    if len(fuzzy) == 1:
        return fuzzy[0], None
    return None, fuzzy


def find(store: GraphStore, query: str, kind: Optional[str] = None, limit: int = 25) -> dict:
    rows = store.search(query, limit=limit)
    if kind:
        rows = [r for r in rows if r["kind"] == kind]
    return {
        "query": query,
        "count": len(rows),
        "results": [_row_brief(r) for r in rows],
    }


def context(store: GraphStore, target: str, kind: Optional[str] = None) -> dict:
    node, cands = _resolve(store, target, kind)
    if node is None:
        return {
            "status": "ambiguous" if cands else "not_found",
            "message": (f"Найдено {len(cands)} символов '{target}'. Уточни uid/kind."
                        if cands else f"Символ '{target}' не найден."),
            "candidates": [_row_brief(c) for c in (cands or [])],
        }
    uid = node["uid"]

    # входящие связи (кто ссылается на символ)
    incoming: dict[str, list] = {}
    for e in store.edges_to(uid):
        src = store.get_node(e["src_uid"])
        if src:
            incoming.setdefault(e["type"], []).append({
                **_row_brief(src), "line": e["line"], "confidence": e["confidence"],
            })

    # исходящие связи (на что ссылается символ)
    outgoing: dict[str, list] = {}
    for e in store.edges_from(uid):
        if e["dst_uid"]:
            dst = store.get_node(e["dst_uid"])
            tgt = _row_brief(dst) if dst else {"uid": e["dst_uid"]}
        else:
            tgt = {"name": e["dst_name"], "unresolved": True}
        tgt = {**tgt, "line": e["line"], "confidence": e["confidence"]}
        outgoing.setdefault(e["type"], []).append(tgt)

    # родитель и дети
    parent = store.get_node(node["parent_uid"]) if node["parent_uid"] else None
    children = [_row_brief(c) for c in store.children(uid)]

    return {
        "status": "found",
        "symbol": {
            "uid": uid, "name": node["name"], "kind": node["kind"],
            "filePath": node["file_path"], "startLine": node["start_line"],
            "endLine": node["end_line"], "signature": node["signature"],
            "language": node["language"],
        },
        "parent": _row_brief(parent) if parent else None,
        "children": children,
        "incoming": incoming,
        "outgoing": outgoing,
        "summary": {
            "callers": len(incoming.get("CALLS", [])),
            "callees": len(outgoing.get("CALLS", [])),
            "inherited_by": len(incoming.get("INHERITS", [])),
        },
    }


# веса риска по типам входящих связей
_RISK_TYPES = ("CALLS", "IMPORTS", "INHERITS", "HAS_METHOD", "CONTAINS", "REFERENCES")


def impact(store: GraphStore, target: str, kind: Optional[str] = None,
           direction: str = "upstream", max_depth: int = 3) -> dict:
    """Blast radius: что сломается при изменении символа. upstream = кто от него
    зависит (входящие связи), транзитивно по глубине."""
    node, cands = _resolve(store, target, kind)
    if node is None:
        return {
            "status": "ambiguous" if cands else "not_found",
            "message": (f"Найдено {len(cands)} символов '{target}'. Уточни uid/kind."
                        if cands else f"Символ '{target}' не найден."),
            "candidates": [_row_brief(c) for c in (cands or [])],
        }
    uid = node["uid"]
    visited: set[str] = {uid}
    by_depth: dict[int, list] = {}

    frontier = [uid]
    for depth in range(1, max_depth + 1):
        nxt = []
        for cur in frontier:
            edges = (store.edges_to(cur) if direction == "upstream"
                     else store.edges_from(cur))
            for e in edges:
                other = e["src_uid"] if direction == "upstream" else e["dst_uid"]
                if not other or other in visited:
                    continue
                visited.add(other)
                onode = store.get_node(other)
                if not onode:
                    continue
                by_depth.setdefault(depth, []).append({
                    **_row_brief(onode),
                    "relationType": e["type"],
                    "confidence": e["confidence"],
                    "depth": depth,
                })
                nxt.append(other)
        frontier = nxt
        if not frontier:
            break

    impacted = sum(len(v) for v in by_depth.values())
    # уникальные затронутые файлы
    files = {item["filePath"] for items in by_depth.values() for item in items}
    risk = "LOW" if impacted <= 3 else "MEDIUM" if impacted <= 15 else "HIGH"

    return {
        "status": "found",
        "target": {"uid": uid, "name": node["name"], "kind": node["kind"],
                   "filePath": node["file_path"]},
        "direction": direction,
        "impactedCount": impacted,
        "filesAffected": len(files),
        "risk": risk,
        "byDepthCounts": {str(d): len(v) for d, v in sorted(by_depth.items())},
        "byDepth": {str(d): v for d, v in sorted(by_depth.items())},
    }


def route_map(store: GraphStore, query: Optional[str] = None, limit: int = 40) -> dict:
    """Кросс-стек карта: API-роуты и кто их вызывает с фронта (HTTP_CALL)."""
    q = "SELECT uid, name, file_path FROM nodes WHERE kind='Route'"
    args: list = []
    if query:
        q += " AND name LIKE ?"
        args.append(f"%{query}%")
    q += " ORDER BY name LIMIT ?"
    args.append(limit)
    routes = []
    for r in store.conn.execute(q, args):
        callers = []
        for e in store.edges_to(r["uid"], "HTTP_CALL"):
            src = store.get_node(e["src_uid"])
            if src:
                callers.append({**_row_brief(src), "line": e["line"]})
        routes.append({
            "route": r["name"], "handler": r["file_path"],
            "callers": callers, "callerCount": len(callers),
        })
    return {"routeCount": len(routes), "routes": routes}


def flows(store: GraphStore, query: str, max_depth: int = 6, limit: int = 5) -> dict:
    """Трассировка потоков выполнения: от символов, совпавших с запросом, идём по
    CALLS-цепочкам. Возвращает несколько цепочек (последовательностей символов)."""
    entries = store.search(query, limit=8)
    entries = [e for e in entries if e["kind"] in ("Function", "Method")]
    chains = []
    for entry in entries:
        chain = []
        cur = entry["uid"]
        seen = set()
        for _ in range(max_depth):
            n = store.get_node(cur)
            if not n or cur in seen:
                break
            seen.add(cur)
            chain.append(_row_brief(n))
            outs = [e for e in store.edges_from(cur, "CALLS") if e["dst_uid"]]
            if not outs:
                break
            cur = outs[0]["dst_uid"]
        if len(chain) >= 2:
            chains.append({
                "entry": entry["name"],
                "steps": len(chain),
                "chain": chain,
            })
        if len(chains) >= limit:
            break
    return {"query": query, "flowCount": len(chains), "flows": chains}
