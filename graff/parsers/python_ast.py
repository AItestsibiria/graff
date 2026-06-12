"""Python-парсер Graff через встроенный ast (полная точность).

Извлекает: File/Class/Function/Method/Variable узлы и связи
CONTAINS / HAS_METHOD / INHERITS / IMPORTS / CALLS.
"""
from __future__ import annotations

import ast
from typing import Optional

from ..graph import Node, Edge


def _uid(kind: str, rel: str, qual: str) -> str:
    return f"{kind}:{rel}:{qual}" if qual else f"{kind}:{rel}"


def parse_python(rel_path: str, source: str
                 ) -> tuple[list[Node], list[Edge], list[tuple[str, str]]]:
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        # битый/несовместимый файл — отдаём только File-узел
        return ([Node(_uid("File", rel_path, ""), "File", rel_path.split("/")[-1],
                      rel_path, language="python")], [], [])

    nodes: list[Node] = []
    edges: list[Edge] = []
    imports: list[tuple[str, str]] = []  # (имя в файле, модуль-источник)
    file_uid = _uid("File", rel_path, "")
    nodes.append(Node(file_uid, "File", rel_path.split("/")[-1], rel_path,
                      start_line=1, language="python"))

    seen_uids: set[str] = {file_uid}

    def uniq(uid: str) -> str:
        if uid not in seen_uids:
            seen_uids.add(uid)
            return uid
        i = 2
        while f"{uid}#{i}" in seen_uids:
            i += 1
        u = f"{uid}#{i}"
        seen_uids.add(u)
        return u

    def sig_of(fn: ast.AST) -> str:
        try:
            args = [a.arg for a in fn.args.args]  # type: ignore[attr-defined]
            return f"{fn.name}({', '.join(args)})"  # type: ignore[attr-defined]
        except Exception:
            return getattr(fn, "name", "")

    def walk_calls(body_node: ast.AST, owner_uid: str, class_name: Optional[str]):
        """Найти ast.Call внутри тела функции/метода → CALLS-связи."""
        for n in ast.walk(body_node):
            if not isinstance(n, ast.Call):
                continue
            f = n.func
            if isinstance(f, ast.Name):
                edges.append(Edge(owner_uid, "CALLS", dst_name=f.id,
                                  file_path=rel_path, line=getattr(n, "lineno", 0)))
            elif isinstance(f, ast.Attribute):
                # self.method() — внутрикласс; иначе obj.method()
                if (class_name and isinstance(f.value, ast.Name)
                        and f.value.id in ("self", "cls")):
                    dst = _uid("Method", rel_path, f"{class_name}.{f.attr}")
                    edges.append(Edge(owner_uid, "CALLS", dst_uid=dst, dst_name=f.attr,
                                      confidence=1.0, file_path=rel_path,
                                      line=getattr(n, "lineno", 0)))
                else:
                    edges.append(Edge(owner_uid, "CALLS", dst_name=f.attr,
                                      confidence=0.8, file_path=rel_path,
                                      line=getattr(n, "lineno", 0)))

    def handle_function(fn, parent_uid: str, class_name: Optional[str]):
        kind = "Method" if class_name else "Function"
        qual = f"{class_name}.{fn.name}" if class_name else fn.name
        uid = uniq(_uid(kind, rel_path, qual))
        nodes.append(Node(uid, kind, fn.name, rel_path,
                          start_line=fn.lineno, end_line=getattr(fn, "end_lineno", fn.lineno),
                          parent_uid=parent_uid, language="python", signature=sig_of(fn)))
        rel = "HAS_METHOD" if class_name else "CONTAINS"
        edges.append(Edge(parent_uid, rel, dst_uid=uid, file_path=rel_path, line=fn.lineno))
        walk_calls(fn, uid, class_name)
        # вложенные определения (функции внутри функций)
        for child in fn.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                handle_function(child, uid, None)
            elif isinstance(child, ast.ClassDef):
                handle_class(child, uid)

    def handle_class(cls: ast.ClassDef, parent_uid: str):
        uid = uniq(_uid("Class", rel_path, cls.name))
        nodes.append(Node(uid, "Class", cls.name, rel_path,
                          start_line=cls.lineno, end_line=getattr(cls, "end_lineno", cls.lineno),
                          parent_uid=parent_uid, language="python"))
        edges.append(Edge(parent_uid, "CONTAINS", dst_uid=uid, file_path=rel_path, line=cls.lineno))
        for base in cls.bases:
            bname = base.id if isinstance(base, ast.Name) else (
                base.attr if isinstance(base, ast.Attribute) else None)
            if bname:
                edges.append(Edge(uid, "INHERITS", dst_name=bname,
                                  file_path=rel_path, line=cls.lineno))
        for child in cls.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                handle_function(child, uid, cls.name)
            elif isinstance(child, ast.ClassDef):
                handle_class(child, uid)

    # верхний уровень модуля
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            handle_function(node, file_uid, None)
        elif isinstance(node, ast.ClassDef):
            handle_class(node, file_uid)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name.split(".")[0]
                edges.append(Edge(file_uid, "IMPORTS", dst_name=alias.name,
                                  file_path=rel_path, line=node.lineno))
                imports.append((local, alias.name))
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                local = alias.asname or alias.name
                edges.append(Edge(file_uid, "IMPORTS",
                                  dst_name=alias.name, confidence=0.9,
                                  file_path=rel_path, line=node.lineno))
                if mod:
                    edges.append(Edge(file_uid, "IMPORTS", dst_name=mod,
                                      confidence=0.6, file_path=rel_path, line=node.lineno))
                    imports.append((local, mod))  # name N ← from module M

    return nodes, edges, imports
