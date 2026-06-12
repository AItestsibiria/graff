"""Graff — standalone-граф кода (символы + связи) с MCP-сервером.

Индексирует ЛЮБОЙ репозиторий (Python через ast, остальные языки через
tree-sitter), строит граф в SQLite (nodes + edges + FTS5 BM25) и отдаёт
инструменты find / context / impact / flows как CLI и как MCP-сервер.

Мульти-репо: глобальный реестр ~/.graff/registry.json, граф каждого репо в
<repo>/.graff/graph.db. Один MCP-сервер обслуживает все зарегистрированные репо
— подключается к любому проекту.
"""
__version__ = "0.1.0"
