"""CLI Graff: analyze / find / context / impact / flows / list / status / mcp.

Мульти-репо: команды запросов открывают граф нужного репо через реестр
(--repo алиас|путь). `graff mcp` поднимает MCP-сервер на все репо.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import __version__, registry
from .analyzer import analyze, update, detect_changes
from .graph import GraphStore
from . import queries


def _open(repo: str | None) -> GraphStore:
    entry = registry.resolve(repo)
    if not entry:
        # фолбэк: путь напрямую
        if repo and os.path.isdir(repo):
            db = registry.db_path_for(repo)
            if os.path.exists(db):
                return GraphStore(db)
        sys.exit(f"graff: репо не найдено ('{repo or 'текущий'}'). Сначала: graff analyze <путь>")
    db = entry["db"]
    if not os.path.exists(db):
        sys.exit(f"graff: граф отсутствует ({db}). Переиндексируй: graff analyze {entry['_path']}")
    return GraphStore(db)


def _print(obj, as_json: bool):
    if as_json:
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(obj, ensure_ascii=False, indent=2))


def cmd_analyze(a):
    path = os.path.abspath(a.path)
    if not os.path.isdir(path):
        sys.exit(f"graff: не каталог: {path}")
    print(f"graff: индексирую {path} …", file=sys.stderr)
    res = analyze(path, alias=a.alias, verbose=a.verbose)
    print(f"\n  Репо проиндексирован ({res['elapsed_s']}s)\n")
    print(f"  {res['nodes']:,} узлов | {res['edges']:,} связей | "
          f"{res['files_ok']} файлов | связей разрешено: {res['edges_resolved']:,}")
    print(f"  языки: {', '.join(f'{k}={v}' for k, v in sorted(res['by_lang'].items()))}")
    print(f"  по типам: {', '.join(f'{k}={v}' for k, v in sorted(res['by_kind'].items()))}")
    print(f"  {res['db']}")


def cmd_update(a):
    res = update(os.path.abspath(a.path))
    if "changed" in res:
        print(f"  обновлено: {res['changed']} файлов, удалено: {res['deleted']} "
              f"({res['elapsed_s']}s)")
        print(f"  {res['nodes']:,} узлов | {res['edges']:,} связей | "
              f"разрешено: {res['edges_resolved']:,}")
    else:
        print(f"  полный реиндекс: {res.get('nodes',0):,} узлов")


def cmd_detect(a):
    _print(detect_changes(os.path.abspath(a.path), ref=a.ref), a.json)


def cmd_find(a):
    store = _open(a.repo)
    _print(queries.find(store, a.query, kind=a.kind, limit=a.limit), a.json)


def cmd_context(a):
    store = _open(a.repo)
    _print(queries.context(store, a.name, kind=a.kind), a.json)


def cmd_impact(a):
    store = _open(a.repo)
    _print(queries.impact(store, a.name, kind=a.kind, direction=a.direction,
                          max_depth=a.depth), a.json)


def cmd_flows(a):
    store = _open(a.repo)
    _print(queries.flows(store, a.query, max_depth=a.depth), a.json)


def cmd_routemap(a):
    store = _open(a.repo)
    _print(queries.route_map(store, query=a.query), a.json)


def cmd_check(a):
    from . import rules
    store = _open(a.repo)
    res = rules.run_rules(store, store.get_meta("repo_path") or ".",
                          min_severity=a.min_severity)
    if a.json:
        _print(res, True)
        return
    print(f"  нарушений: {res['total']}  ({', '.join(f'{k}={v}' for k,v in res['bySeverity'].items()) or 'нет'})")
    for v in res["violations"][:40]:
        print(f"  [{v['severity']:8s}] {v['file']}:{v['line']}  {v['message']}")


def cmd_roles(a):
    from . import rules
    store = _open(a.repo)
    res = rules.detect_roles(store)
    if a.json:
        _print(res, True)
        return
    print("  роли:", ", ".join(f"{k}={v}" for k, v in res["roleCounts"].items()))
    if res["anomalies"]:
        print("  аномалии:")
        for an in res["anomalies"]:
            print(f"  [{an['severity']}] {an['file']} ({an['class']}): {an['message']}")
    else:
        print("  аномалий нет")


def cmd_hotspots(a):
    from . import analytics
    store = _open(a.repo)
    res = analytics.hotspots(store, limit=a.limit)
    if a.json:
        _print(res, True); return
    print("  хотспоты (самые зависимые символы):")
    for h in res["hotspots"]:
        print(f"  {h['dependents']:>4} ← {h['filePath']}:{h['line']} {h['kind']} {h['name']}")


def cmd_deadcode(a):
    from . import analytics
    store = _open(a.repo)
    res = analytics.dead_code(store, limit=a.limit)
    if a.json:
        _print(res, True); return
    print(f"  кандидатов в мёртвый код: {res['candidateCount']}")
    for d in res["deadCandidates"]:
        print(f"  {d['filePath']}:{d['line']} {d['kind']} {d['name']}")


def cmd_cycles(a):
    from . import analytics
    store = _open(a.repo)
    res = analytics.cycles(store)
    if a.json:
        _print(res, True); return
    print(f"  циклических импортов: {res['cycleCount']}")
    for c in res["cycles"]:
        print("  " + " → ".join(p.split("/")[-1] for p in c))


def cmd_list(a):
    repos = registry.list_repos()
    if not repos:
        print("graff: нет проиндексированных репо. graff analyze <путь>")
        return
    for r in repos:
        print(f"  {r['alias']:20s} {r.get('nodes',0):>7,} узлов  {r.get('edges',0):>7,} связей  {r['_path']}")


def cmd_status(a):
    store = _open(a.repo)
    c = store.counts()
    print(f"  узлов: {c['nodes']:,}  связей: {c['edges']:,}")
    print(f"  путь: {store.get_meta('repo_path')}")
    print(f"  индекс: {store.get_meta('indexed_at')}  файлов: {store.get_meta('files')}")
    print(f"  языки: {store.get_meta('languages')}")
    print(f"  по типам: {', '.join(f'{k}={v}' for k, v in sorted(c['by_kind'].items()))}")


def cmd_remove(a):
    ok = registry.unregister(a.target)
    print("удалён из реестра" if ok else "не найдено в реестре")


def cmd_mcp(a):
    from .mcp_server import serve
    serve()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="graff", description="Graff — граф кода + MCP")
    p.add_argument("-V", "--version", action="version", version=f"graff {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("analyze", help="проиндексировать репозиторий")
    pa.add_argument("path", nargs="?", default=".", help="путь к репо (по умолч. текущий)")
    pa.add_argument("--alias", help="короткое имя репо в реестре")
    pa.add_argument("--verbose", action="store_true")
    pa.set_defaults(func=cmd_analyze)

    pu = sub.add_parser("update", help="инкрементальный реиндекс (только изменённые файлы)")
    pu.add_argument("path", nargs="?", default=".")
    pu.set_defaults(func=cmd_update)

    pd = sub.add_parser("detect-changes", help="git-diff → затронутые символы + blast radius")
    pd.add_argument("path", nargs="?", default=".")
    pd.add_argument("--ref", default="HEAD", help="git ref для сравнения (по умолч. HEAD)")
    pd.add_argument("--json", action="store_true")
    pd.set_defaults(func=cmd_detect)

    pf = sub.add_parser("find", help="поиск символов (BM25)")
    pf.add_argument("query")
    pf.add_argument("--repo")
    pf.add_argument("--kind")
    pf.add_argument("--limit", type=int, default=25)
    pf.add_argument("--json", action="store_true")
    pf.set_defaults(func=cmd_find)

    pc = sub.add_parser("context", help="360° по символу: кто вызывает/что вызывает")
    pc.add_argument("name")
    pc.add_argument("--repo")
    pc.add_argument("--kind")
    pc.add_argument("--json", action="store_true")
    pc.set_defaults(func=cmd_context)

    pi = sub.add_parser("impact", help="blast radius: что сломается при изменении")
    pi.add_argument("name")
    pi.add_argument("--repo")
    pi.add_argument("--kind")
    pi.add_argument("--direction", choices=["upstream", "downstream"], default="upstream")
    pi.add_argument("--depth", type=int, default=3)
    pi.add_argument("--json", action="store_true")
    pi.set_defaults(func=cmd_impact)

    pl = sub.add_parser("flows", help="трассировка потоков выполнения (CALLS-цепочки)")
    pl.add_argument("query")
    pl.add_argument("--repo")
    pl.add_argument("--depth", type=int, default=6)
    pl.add_argument("--json", action="store_true")
    pl.set_defaults(func=cmd_flows)

    prm = sub.add_parser("route-map", help="кросс-стек: API-роуты и их вызовы с фронта")
    prm.add_argument("query", nargs="?", default=None, help="фильтр по подстроке роута")
    prm.add_argument("--repo")
    prm.add_argument("--json", action="store_true")
    prm.set_defaults(func=cmd_routemap)

    pch = sub.add_parser("check", help="rule guard: проверка правил проекта (security и др.)")
    pch.add_argument("--repo")
    pch.add_argument("--min-severity", default="INFO",
                     help="порог: CRITICAL|HIGH|MEDIUM|LOW|INFO")
    pch.add_argument("--json", action="store_true")
    pch.set_defaults(func=cmd_check)

    prl = sub.add_parser("roles", help="роли файлов (паук/пайплайн/роут) + аномалии")
    prl.add_argument("--repo")
    prl.add_argument("--json", action="store_true")
    prl.set_defaults(func=cmd_roles)

    phs = sub.add_parser("hotspots", help="самые зависимые символы (риск изменения)")
    phs.add_argument("--repo")
    phs.add_argument("--limit", type=int, default=20)
    phs.add_argument("--json", action="store_true")
    phs.set_defaults(func=cmd_hotspots)

    pdc = sub.add_parser("deadcode", help="кандидаты в мёртвый код (без входящих вызовов)")
    pdc.add_argument("--repo")
    pdc.add_argument("--limit", type=int, default=50)
    pdc.add_argument("--json", action="store_true")
    pdc.set_defaults(func=cmd_deadcode)

    pcy = sub.add_parser("cycles", help="циклические импорты (Python)")
    pcy.add_argument("--repo")
    pcy.add_argument("--json", action="store_true")
    pcy.set_defaults(func=cmd_cycles)

    sub.add_parser("list", help="список проиндексированных репо").set_defaults(func=cmd_list)

    ps = sub.add_parser("status", help="статус графа репо")
    ps.add_argument("--repo")
    ps.set_defaults(func=cmd_status)

    pr = sub.add_parser("remove", help="убрать репо из реестра")
    pr.add_argument("target")
    pr.set_defaults(func=cmd_remove)

    sub.add_parser("mcp", help="запустить MCP-сервер (stdio)").set_defaults(func=cmd_mcp)
    return p


def main(argv=None):
    p = build_parser()
    a = p.parse_args(argv)
    a.func(a)


if __name__ == "__main__":
    main()
