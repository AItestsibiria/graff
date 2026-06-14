"""Rule guard Graff: жёсткие правила проекта как граф/контент-проверки.

Каждое правило — функция check(store, repo_path) → список нарушений. Кодифицирует
повторяющиеся требования (для Бизнесметра — правила CLAUDE.md: запрет
bai_no_proxy, секреты только в .env, прокси к таргету и т.п.). Правила — данные,
расширяются при выявлении новых паттернов.
"""
from __future__ import annotations

import os
import re
import subprocess

from .graph import GraphStore

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}

# секрет-паттерны (литералы с явным значением)
SECRET_PATTERNS = [
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{32,}")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("aws_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("generic_secret", re.compile(
        r"(?i)(password|passwd|api[_-]?key|secret|token)\s*[=:]\s*"
        r"['\"][A-Za-z0-9_\-/+]{12,}['\"]")),
]
SECRET_ALLOW_SUFFIX = (".example", ".sample", ".md", ".lock")


def _git_tracked(repo_path: str) -> list[str]:
    try:
        out = subprocess.run(["git", "-C", repo_path, "ls-files"],
                             capture_output=True, text=True, timeout=20)
        return [l for l in out.stdout.splitlines() if l.strip()]
    except Exception:
        return []


def _scan_file(full: str):
    try:
        with open(full, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


# ---------------- правила ----------------

def rule_no_bai_no_proxy(store, repo_path) -> list[dict]:
    """ПРАВИЛО: ни один паук не должен иметь bai_no_proxy=True (кроме FilesPipeline CDN)."""
    viol = []
    rx = re.compile(r"bai_no_proxy\s*[:=]\s*True")
    for r in store.conn.execute(
        "SELECT DISTINCT file_path FROM nodes WHERE language='python'"
    ):
        rel = r["file_path"]
        text = _scan_file(os.path.join(repo_path, rel))
        for m in rx.finditer(text):
            line = _line_of(text, m.start())
            # FilesPipeline (CDN-фото) — легальное исключение
            sev = "INFO" if "FilesPipeline" in text or "download_photos" in rel else "HIGH"
            viol.append({"rule": "no_bai_no_proxy", "severity": sev,
                         "file": rel, "line": line,
                         "message": "bai_no_proxy=True — запрос к таргету в обход прокси"})
    return viol


def rule_secrets_in_git(store, repo_path) -> list[dict]:
    """ПРАВИЛО: секреты только в .env (600, не в git). Скан git-tracked файлов."""
    viol = []
    for rel in _git_tracked(repo_path):
        if rel.endswith(SECRET_ALLOW_SUFFIX):
            continue
        full = os.path.join(repo_path, rel)
        if not os.path.isfile(full) or os.path.getsize(full) > 512 * 1024:
            continue
        text = _scan_file(full)
        for kind, rx in SECRET_PATTERNS:
            m = rx.search(text)
            if m:
                viol.append({"rule": "secrets_in_git", "severity": "CRITICAL",
                             "file": rel, "line": _line_of(text, m.start()),
                             "message": f"секрет в git-tracked файле ({kind})"})
                break
    return viol


def rule_secrets_in_bus(store, repo_path) -> list[dict]:
    """ПРАВИЛО: docs/bus/* коммитится в git → секретов там быть НЕ должно."""
    viol = []
    bus = os.path.join(repo_path, "docs", "bus")
    if not os.path.isdir(bus):
        return viol
    for root, _, files in os.walk(bus):
        for fn in files:
            full = os.path.join(root, fn)
            if os.path.getsize(full) > 512 * 1024:
                continue
            text = _scan_file(full)
            for kind, rx in SECRET_PATTERNS:
                m = rx.search(text)
                if m:
                    rel = os.path.relpath(full, repo_path)
                    viol.append({"rule": "secrets_in_bus", "severity": "CRITICAL",
                                 "file": rel, "line": _line_of(text, m.start()),
                                 "message": f"секрет в канале docs/bus ({kind}) — канал в git!"})
                    break
    return viol


def rule_env_in_git(store, repo_path) -> list[dict]:
    """ПРАВИЛО: .env (с значениями) не должен быть в git (только .env.example)."""
    viol = []
    for rel in _git_tracked(repo_path):
        base = os.path.basename(rel)
        if base == ".env" or base.startswith(".env."):
            if base.endswith((".example", ".sample")):
                continue
            viol.append({"rule": "env_in_git", "severity": "HIGH",
                         "file": rel, "line": 1,
                         "message": ".env с секретами под контролем git"})
    return viol


def rule_proxyhandler_to_target(store, repo_path) -> list[dict]:
    """ПРАВИЛО №1: ProxyHandler({})/--noproxy к таргету запрещён. Инфра (ipify,
    ip-api, ads-api, localhost) — легально. Флагуем без пометки infra рядом."""
    viol = []
    rx = re.compile(r"ProxyHandler\(\{\}\)")
    for r in store.conn.execute(
        "SELECT DISTINCT file_path FROM nodes WHERE language='python'"
    ):
        rel = r["file_path"]
        text = _scan_file(os.path.join(repo_path, rel))
        lines = text.splitlines()
        for m in rx.finditer(text):
            line = _line_of(text, m.start())
            ctx = " ".join(lines[max(0, line - 3):line]).lower()
            is_infra = any(w in ctx for w in
                           ("infra", "ipify", "ip-api", "ads-api", "localhost",
                            "claude-mem", "dadata", "deepseek"))
            viol.append({"rule": "proxyhandler_to_target",
                         "severity": "INFO" if is_infra else "MEDIUM",
                         "file": rel, "line": line,
                         "message": "ProxyHandler({}) — прямой запрос без прокси"
                                    + (" (infra, ок)" if is_infra else " — проверь, не таргет ли")})
    return viol


ALL_RULES = [
    rule_no_bai_no_proxy,
    rule_secrets_in_git,
    rule_secrets_in_bus,
    rule_env_in_git,
    rule_proxyhandler_to_target,
]


def detect_roles(store: GraphStore) -> dict:
    """Распознать роли файлов по структуре графа (паук/пайплайн/api-роут/компонент)
    и выявить аномалии (отклонение от паттерна роли)."""
    roles: dict[str, list[str]] = {}
    anomalies: list[dict] = []

    # методы по классу
    methods_by_class: dict[str, set[str]] = {}
    for r in store.conn.execute(
        "SELECT n.parent_uid pu, n.name nm FROM nodes n WHERE n.kind='Method'"
    ):
        if r["pu"]:
            methods_by_class.setdefault(r["pu"], set()).add(r["nm"])
    # наследование по классу
    inherits: dict[str, list[str]] = {}
    for e in store.conn.execute(
        "SELECT src_uid, dst_name FROM edges WHERE type='INHERITS'"
    ):
        inherits.setdefault(e["src_uid"], []).append(e["dst_name"] or "")

    for c in store.conn.execute(
        "SELECT uid, name, file_path FROM nodes WHERE kind='Class' AND language='python'"
    ):
        meths = methods_by_class.get(c["uid"], set())
        bases = inherits.get(c["uid"], [])
        is_spider = (any("Spider" in b for b in bases)
                     or c["name"].endswith("Spider")
                     or "/spiders/" in c["file_path"])
        is_pipeline = "process_item" in meths or c["name"].endswith("Pipeline")
        if is_spider:
            roles.setdefault("spider", []).append(c["file_path"])
            if "parse" not in meths and "start_requests" not in meths and "start" not in meths:
                anomalies.append({"role": "spider", "file": c["file_path"],
                                  "class": c["name"], "severity": "MEDIUM",
                                  "message": "паук без parse/start_requests — отклонение от паттерна"})
        if is_pipeline and "process_item" not in meths:
            anomalies.append({"role": "pipeline", "file": c["file_path"],
                              "class": c["name"], "severity": "MEDIUM",
                              "message": "пайплайн без process_item"})
        elif is_pipeline:
            roles.setdefault("pipeline", []).append(c["file_path"])

    routes = store.conn.execute("SELECT count(*) c FROM nodes WHERE kind='Route'").fetchone()["c"]
    return {
        "roles": {k: sorted(set(v)) for k, v in roles.items()},
        "roleCounts": {k: len(set(v)) for k, v in roles.items()} | {"api_route": routes},
        "anomalies": anomalies,
    }


def run_rules(store: GraphStore, repo_path: str, min_severity: str = "INFO") -> dict:
    min_rank = SEVERITY_ORDER.get(min_severity, 4)
    violations = []
    for rule in ALL_RULES:
        try:
            violations.extend(rule(store, repo_path))
        except Exception as e:
            violations.append({"rule": rule.__name__, "severity": "INFO",
                               "file": "", "line": 0, "message": f"правило упало: {e}"})
    violations = [v for v in violations
                  if SEVERITY_ORDER.get(v["severity"], 4) <= min_rank]
    violations.sort(key=lambda v: SEVERITY_ORDER.get(v["severity"], 4))
    by_sev: dict[str, int] = {}
    for v in violations:
        by_sev[v["severity"]] = by_sev.get(v["severity"], 0) + 1
    return {"total": len(violations), "bySeverity": by_sev, "violations": violations}
