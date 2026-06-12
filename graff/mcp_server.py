"""MCP-сервер Graff (stdio, JSON-RPC 2.0).

Обслуживает ВСЕ репо из реестра ~/.graff. Инструменты: graff_find, graff_context,
graff_impact, graff_flows, graff_list_repos, graff_status. Каждый (кроме list)
принимает опциональный repo (алиас|путь) — без него берётся единственный/текущий.
"""
# Copyright (c) 2025 BAI / AItestsibiria. Business Source License 1.1.
# Commercial SaaS use requires a commercial license: egnovoselov@gmail.com

from __future__ import annotations

import json
import os
import sys

from . import __version__, registry
from .graph import GraphStore
from . import queries

PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {
        "name": "graff_find",
        "description": "Поиск символов кода (классы/функции/методы) по имени/концепту "
                       "через BM25. Возвращает точные файл+строку. Замена grep+glob.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "имя или концепт для поиска"},
                "repo": {"type": "string", "description": "алиас/путь репо (опц.)"},
                "kind": {"type": "string", "description": "фильтр: Class|Function|Method|File"},
                "limit": {"type": "integer", "description": "макс. результатов (по умолч. 25)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "graff_context",
        "description": "360° по символу: где определён, КТО его вызывает (callers), "
                       "ЧТО он вызывает (callees), родитель, дети. Замена цепочки "
                       "grep→read нескольких файлов.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "имя символа или его uid"},
                "repo": {"type": "string"},
                "kind": {"type": "string"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "graff_impact",
        "description": "Blast radius: ЧТО СЛОМАЕТСЯ при изменении символа. Транзитивно "
                       "по входящим связям (кто зависит), с уровнем риска и списком "
                       "затронутых файлов. Замена ручного чтения всех потребителей.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "имя символа или его uid"},
                "repo": {"type": "string"},
                "kind": {"type": "string"},
                "direction": {"type": "string", "description": "upstream (по умолч.) | downstream"},
                "depth": {"type": "integer", "description": "глубина обхода (по умолч. 3)"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "graff_flows",
        "description": "Трассировка потоков выполнения: CALLS-цепочки от символов, "
                       "совпавших с запросом. Показывает последовательность вызовов.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "repo": {"type": "string"},
                "depth": {"type": "integer"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "graff_route_map",
        "description": "Кросс-стек: API-роуты (Next.js) и КТО их вызывает с фронта "
                       "(fetch). Full-stack поток фронт↔бэк. Опц. query — фильтр роута.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}, "repo": {"type": "string"}},
        },
    },
    {
        "name": "graff_detect_changes",
        "description": "git-diff (рабочее дерево vs ref) → затронутые символы + blast "
                       "radius каждого + общий риск. Использовать ПЕРЕД коммитом.",
        "inputSchema": {
            "type": "object",
            "properties": {"repo": {"type": "string"},
                           "ref": {"type": "string", "description": "git ref (по умолч. HEAD)"}},
        },
    },
    {
        "name": "graff_check",
        "description": "Rule guard: проверка жёстких правил проекта (секреты в git, "
                       "bai_no_proxy, .env в git, ProxyHandler к таргету). Возвращает "
                       "нарушения с severity. Запускать перед коммитом/деплоем.",
        "inputSchema": {
            "type": "object",
            "properties": {"repo": {"type": "string"},
                           "min_severity": {"type": "string",
                               "description": "CRITICAL|HIGH|MEDIUM|LOW|INFO"}},
        },
    },
    {
        "name": "graff_roles",
        "description": "Роли файлов по структуре (паук/пайплайн/api-роут) + аномалии "
                       "(отклонения от паттерна роли, напр. паук без parse).",
        "inputSchema": {"type": "object", "properties": {"repo": {"type": "string"}}},
    },
    {
        "name": "graff_hotspots",
        "description": "Самые зависимые символы (высокий in-degree) = наибольший риск "
                       "при изменении. Ранжированный список.",
        "inputSchema": {
            "type": "object",
            "properties": {"repo": {"type": "string"}, "limit": {"type": "integer"}},
        },
    },
    {
        "name": "graff_deadcode",
        "description": "Кандидаты в мёртвый код (Python-функции без входящих вызовов). "
                       "Advisory: кросс-язык/динамика не учтены.",
        "inputSchema": {
            "type": "object",
            "properties": {"repo": {"type": "string"}, "limit": {"type": "integer"}},
        },
    },
    {
        "name": "graff_cycles",
        "description": "Циклические импорты между Python-файлами (риск архитектуры).",
        "inputSchema": {"type": "object", "properties": {"repo": {"type": "string"}}},
    },
    {
        "name": "graff_update",
        "description": "Инкрементальный реиндекс репо (только изменённые файлы по mtime). "
                       "Держит граф свежим после правок.",
        "inputSchema": {"type": "object", "properties": {"repo": {"type": "string"}}},
    },
    {
        "name": "graff_list_repos",
        "description": "Список проиндексированных репозиториев (алиас, путь, размер графа).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "graff_status",
        "description": "Статус графа репо: число узлов/связей, языки, время индексации.",
        "inputSchema": {
            "type": "object",
            "properties": {"repo": {"type": "string"}},
        },
    },
]


def _open(repo):
    entry = registry.resolve(repo)
    if not entry:
        raise ValueError(f"репо не найдено: '{repo or 'текущий'}'. Сначала: graff analyze <путь>")
    db = entry["db"]
    if not os.path.exists(db):
        raise ValueError(f"граф отсутствует: {db}")
    return GraphStore(db)


def _dispatch(name: str, args: dict) -> dict:
    if name == "graff_list_repos":
        return {"repos": registry.list_repos()}
    if name == "graff_find":
        s = _open(args.get("repo"))
        return queries.find(s, args["query"], kind=args.get("kind"),
                            limit=args.get("limit", 25))
    if name == "graff_context":
        s = _open(args.get("repo"))
        return queries.context(s, args["name"], kind=args.get("kind"))
    if name == "graff_impact":
        s = _open(args.get("repo"))
        return queries.impact(s, args["name"], kind=args.get("kind"),
                              direction=args.get("direction", "upstream"),
                              max_depth=args.get("depth", 3))
    if name == "graff_flows":
        s = _open(args.get("repo"))
        return queries.flows(s, args["query"], max_depth=args.get("depth", 6))
    if name == "graff_route_map":
        s = _open(args.get("repo"))
        return queries.route_map(s, query=args.get("query"))
    if name == "graff_detect_changes":
        from .analyzer import detect_changes
        entry = registry.resolve(args.get("repo"))
        if not entry:
            raise ValueError("репо не найдено")
        return detect_changes(entry["_path"], ref=args.get("ref", "HEAD"))
    if name == "graff_check":
        from . import rules
        s = _open(args.get("repo"))
        return rules.run_rules(s, s.get_meta("repo_path") or ".",
                               min_severity=args.get("min_severity", "INFO"))
    if name == "graff_roles":
        from . import rules
        s = _open(args.get("repo"))
        return rules.detect_roles(s)
    if name == "graff_hotspots":
        from . import analytics
        s = _open(args.get("repo"))
        return analytics.hotspots(s, limit=args.get("limit", 20))
    if name == "graff_deadcode":
        from . import analytics
        s = _open(args.get("repo"))
        return analytics.dead_code(s, limit=args.get("limit", 50))
    if name == "graff_cycles":
        from . import analytics
        s = _open(args.get("repo"))
        return analytics.cycles(s)
    if name == "graff_update":
        from .analyzer import update
        entry = registry.resolve(args.get("repo"))
        if not entry:
            raise ValueError("репо не найдено")
        return update(entry["_path"])
    if name == "graff_status":
        s = _open(args.get("repo"))
        c = s.counts()
        return {"nodes": c["nodes"], "edges": c["edges"], "by_kind": c["by_kind"],
                "repo_path": s.get_meta("repo_path"), "indexed_at": s.get_meta("indexed_at"),
                "languages": s.get_meta("languages"), "files": s.get_meta("files")}
    raise ValueError(f"неизвестный инструмент: {name}")


def _handle(req: dict):
    """Вернуть ответ-dict или None (для нотификаций)."""
    method = req.get("method")
    rid = req.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "graff", "version": __version__},
        }}
    if method == "notifications/initialized" or method is None:
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = req.get("params", {})
        name = params.get("name", "")
        args = params.get("arguments", {})
        try:
            result = _dispatch(name, args)
            text = json.dumps(result, ensure_ascii=False, indent=2)
            return {"jsonrpc": "2.0", "id": rid,
                    "result": {"content": [{"type": "text", "text": text}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": rid,
                    "result": {"content": [{"type": "text",
                               "text": f"graff error: {type(e).__name__}: {e}"}],
                               "isError": True}}
    if rid is not None:
        return {"jsonrpc": "2.0", "id": rid,
                "error": {"code": -32601, "message": f"method not found: {method}"}}
    return None


def serve():
    """stdio-цикл: построчно читаем JSON-RPC, пишем ответы в stdout."""
    out = sys.stdout
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = _handle(req)
        if resp is not None:
            out.write(json.dumps(resp, ensure_ascii=False) + "\n")
            out.flush()


if __name__ == "__main__":
    serve()
