"""Graff schema-guard (идея из graphify — интроспекция схемы, нативно по DDL репо).
Ловит класс ошибки 42P10: `INSERT ... ON CONFLICT (cols)` без matching UNIQUE-constraint
на целевой таблице. Сканирует .sql/.ts/.py/.js. Без живой БД — по исходникам.

Запуск:  python -m graff.schema_guard <repo>   (или из graff CLI)
"""
import os
import re
import sys

SCAN_EXT = (".sql", ".ts", ".tsx", ".js", ".py")
SKIP_DIRS = {"node_modules", ".next", ".git", "__pycache__", ".venv", "dist", "build"}
# Плейсхолдеры из примеров/доков — не реальные таблицы.
PLACEHOLDERS = {"table", "cols", "tablename", "your_table", "t", "x"}


def _norm_cols(s: str) -> frozenset:
    return frozenset(c.strip().strip('"').strip("`").lower() for c in s.split(",") if c.strip())


def _read_all(root: str) -> str:
    chunks = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if f.endswith(SCAN_EXT) and f != "schema_guard.py":  # не сканируем сам гард (его примеры)
                try:
                    chunks.append(open(os.path.join(dp, f), encoding="utf-8", errors="ignore").read())
                except Exception:
                    pass
    return "\n".join(chunks)


def collect_unique(text: str):
    """Множество (table, frozenset(cols)) уникальных ограничений + список partial-индексов."""
    uniq = set()
    partial = []  # (table, cols) — частичный unique-индекс (WHERE) → НЕ годится для ON CONFLICT без WHERE
    # CREATE [UNIQUE] INDEX ... ON table (cols) [WHERE ...]
    for m in re.finditer(r"CREATE\s+UNIQUE\s+INDEX[^;]*?\bON\s+(\w+)\s*\(([^)]*)\)([^;]*)", text, re.I):
        table, cols, tail = m.group(1).lower(), _norm_cols(m.group(2)), m.group(3)
        if re.search(r"\bWHERE\b", tail, re.I):
            partial.append((table, cols))
        else:
            uniq.add((table, cols))
    # ALTER TABLE table ADD [CONSTRAINT x] UNIQUE (cols) / PRIMARY KEY (cols)
    for m in re.finditer(r"ALTER\s+TABLE\s+(\w+)\s+ADD\s+(?:CONSTRAINT\s+\w+\s+)?(?:UNIQUE|PRIMARY\s+KEY)\s*\(([^)]*)\)", text, re.I):
        uniq.add((m.group(1).lower(), _norm_cols(m.group(2))))
    # CREATE TABLE table ( ... ) — инлайн UNIQUE(...)/PRIMARY KEY(...) и колоночные UNIQUE/PRIMARY KEY
    for m in re.finditer(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\(", text, re.I):
        table = m.group(1).lower()
        body = _balanced(text, text.index("(", m.end() - 1))
        if not body:
            continue
        for cm in re.finditer(r"(?:UNIQUE|PRIMARY\s+KEY)\s*\(([^)]*)\)", body, re.I):
            uniq.add((table, _norm_cols(cm.group(1))))
        # колоночные: `col type ... UNIQUE` / `... PRIMARY KEY`
        for line in body.split(","):
            cm = re.match(r"\s*\"?(\w+)\"?\s+[^,]*\b(?:UNIQUE|PRIMARY\s+KEY)\b", line, re.I)
            if cm:
                uniq.add((table, frozenset({cm.group(1).lower()})))
    return uniq, partial


def _balanced(text: str, start: int):
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[start + 1:i]
    return None


def collect_conflicts(text: str):
    """Список (table, frozenset(cols)) из INSERT INTO table ... ON CONFLICT (cols)."""
    out = []
    for m in re.finditer(r"INSERT\s+INTO\s+(\w+)\b[\s\S]{0,1200}?ON\s+CONFLICT\s*\(([^)]*)\)", text, re.I):
        table = m.group(1).lower()
        if table in PLACEHOLDERS:
            continue
        out.append((table, _norm_cols(m.group(2))))
    return out


def check(root: str):
    text = _read_all(root)
    uniq, partial = collect_unique(text)
    conflicts = collect_conflicts(text)
    issues = []
    for table, cols in conflicts:
        if (table, cols) in uniq:
            continue
        if (table, cols) in partial:
            issues.append(f"ON CONFLICT ({','.join(sorted(cols))}) на {table} — только ЧАСТИЧНЫЙ unique-индекс (WHERE) → 42P10 без того же WHERE")
        else:
            issues.append(f"ON CONFLICT ({','.join(sorted(cols))}) на {table} — НЕТ matching UNIQUE-constraint → 42P10 на проде")
    return issues, len(conflicts), len(uniq)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    issues, nc, nu = check(root)
    print(f"schema-guard: ON CONFLICT={nc}, unique-constraints={nu}, проблем={len(issues)}")
    for i in issues:
        print("  [42P10] " + i)
    sys.exit(1 if issues else 0)


if __name__ == "__main__":
    main()
