"""Мульти-язычный парсер Graff через tree-sitter.

Универсальный обход дерева: узлы-определения (класс/функция/метод) → Node +
структурная связь; call_expression внутри них → CALLS; import → IMPORTS.
Конфиги по языкам — DEF_TYPES / CALL_TYPES / IMPORT_TYPES.
"""
from __future__ import annotations

from typing import Optional

from ..graph import Node, Edge

# расширение → язык tree-sitter
ext_to_lang = {
    ".ts": "typescript", ".tsx": "tsx", ".js": "javascript", ".jsx": "javascript",
    ".mjs": "javascript", ".cjs": "javascript",
    ".go": "go", ".rs": "rust", ".java": "java", ".rb": "ruby", ".php": "php",
    ".c": "c", ".h": "c", ".cpp": "cpp", ".cc": "cpp", ".hpp": "cpp",
    ".cs": "c_sharp", ".kt": "kotlin", ".scala": "scala", ".swift": "swift",
    ".lua": "lua", ".sh": "bash", ".bash": "bash",
}
TS_LANGS = set(ext_to_lang.values())

# Типы узлов-определений по языку: ts_node_type → наш kind.
# Имя берём через field 'name' либо первый identifier-потомок.
DEF_TYPES = {
    "default": {
        "class_declaration": "Class", "class_definition": "Class",
        "class_specifier": "Class", "struct_specifier": "Class",
        "interface_declaration": "Class", "struct_item": "Class",
        "enum_declaration": "Class", "enum_item": "Class", "trait_item": "Class",
        "type_alias_declaration": "Class",
        "function_declaration": "Function", "function_definition": "Function",
        "function_item": "Function", "function_signature": "Function",
        "method_definition": "Method", "method_declaration": "Method",
        "public_field_definition": "Variable",
    },
}
CALL_TYPES = {"call_expression", "call", "function_call_expression",
              "method_invocation", "invocation_expression"}
IMPORT_TYPES = {"import_statement", "import_declaration", "import_from_statement",
                "import_spec", "use_declaration", "preproc_include", "import_header"}
# узлы-контейнеры функций (внутри них считаем CALLS)
FUNC_KINDS = {"Function", "Method"}


def _node_text(node, src: bytes) -> str:
    return src[node.start_byte:node.end_byte].decode("utf-8", "replace")


def _name_of(node, src: bytes) -> Optional[str]:
    n = node.child_by_field_name("name")
    if n is not None:
        return _node_text(n, src)
    for c in node.children:
        if c.type in ("identifier", "type_identifier", "field_identifier",
                      "property_identifier", "name"):
            return _node_text(c, src)
    return None


def _callee_name(call_node, src: bytes) -> Optional[str]:
    fn = call_node.child_by_field_name("function")
    if fn is None:
        for c in call_node.children:
            if c.type in ("identifier", "member_expression", "selector_expression",
                          "field_expression", "scoped_identifier"):
                fn = c
                break
    if fn is None:
        return None
    if fn.type == "identifier":
        return _node_text(fn, src)
    # member/selector: взять последний идентификатор (имя метода)
    last = None
    for c in fn.children:
        if c.type in ("identifier", "property_identifier", "field_identifier"):
            last = c
    if last is not None:
        return _node_text(last, src)
    txt = _node_text(fn, src)
    return txt.split(".")[-1].split("::")[-1] if txt else None


def parse_treesitter(rel_path: str, source: str, lang: str
                     ) -> tuple[list[Node], list[Edge], list]:
    from tree_sitter_languages import get_parser
    try:
        parser = get_parser(lang)
    except Exception:
        return ([Node(f"File:{rel_path}", "File", rel_path.split("/")[-1],
                      rel_path, language=lang)], [], [])

    src = source.encode("utf-8", "replace")
    tree = parser.parse(src)
    defmap = DEF_TYPES.get(lang, DEF_TYPES["default"])

    nodes: list[Node] = []
    edges: list[Edge] = []
    file_uid = f"File:{rel_path}"
    nodes.append(Node(file_uid, "File", rel_path.split("/")[-1], rel_path,
                      start_line=1, language=lang))
    seen: set[str] = {file_uid}

    def uniq(uid: str) -> str:
        if uid not in seen:
            seen.add(uid)
            return uid
        i = 2
        while f"{uid}#{i}" in seen:
            i += 1
        u = f"{uid}#{i}"
        seen.add(u)
        return u

    def visit(node, parent_uid: str, container_kind: str, class_name: Optional[str]):
        for child in node.children:
            t = child.type
            # const Foo = () => {} / const Bar = function(){} — React-компоненты и хелперы
            if t == "variable_declarator":
                val = child.child_by_field_name("value")
                if val is not None and val.type in ("arrow_function", "function",
                                                    "function_expression"):
                    name = _name_of(child, src)
                    if name:
                        uid = uniq(f"Function:{rel_path}:{name}")
                        nodes.append(Node(uid, "Function", name, rel_path,
                                          start_line=child.start_point[0] + 1,
                                          end_line=child.end_point[0] + 1,
                                          parent_uid=parent_uid, language=lang))
                        edges.append(Edge(parent_uid, "CONTAINS", dst_uid=uid,
                                          file_path=rel_path, line=child.start_point[0] + 1))
                        visit(val, uid, "Function", class_name)
                        continue
                visit(child, parent_uid, container_kind, class_name)
            elif t in defmap:
                kind = defmap[t]
                name = _name_of(child, src)
                if not name:
                    visit(child, parent_uid, container_kind, class_name)
                    continue
                if kind in ("Function",) and class_name:
                    kind = "Method"
                qual = f"{class_name}.{name}" if (kind == "Method" and class_name) else name
                uid = uniq(f"{kind}:{rel_path}:{qual}")
                nodes.append(Node(uid, kind, name, rel_path,
                                  start_line=child.start_point[0] + 1,
                                  end_line=child.end_point[0] + 1,
                                  parent_uid=parent_uid, language=lang))
                rel = "HAS_METHOD" if kind == "Method" else "CONTAINS"
                edges.append(Edge(parent_uid, rel, dst_uid=uid,
                                  file_path=rel_path, line=child.start_point[0] + 1))
                new_class = name if kind == "Class" else class_name
                visit(child, uid, kind, new_class)
            elif t in CALL_TYPES and container_kind in FUNC_KINDS:
                cn = _callee_name(child, src)
                if cn:
                    edges.append(Edge(parent_uid, "CALLS", dst_name=cn,
                                      confidence=0.8, file_path=rel_path,
                                      line=child.start_point[0] + 1))
                visit(child, parent_uid, container_kind, class_name)
            elif t in IMPORT_TYPES:
                txt = _node_text(child, src).replace("\n", " ")[:120]
                edges.append(Edge(file_uid, "IMPORTS", dst_name=_import_target(txt),
                                  confidence=0.6, file_path=rel_path,
                                  line=child.start_point[0] + 1))
            else:
                visit(child, parent_uid, container_kind, class_name)

    visit(tree.root_node, file_uid, "File", None)
    return nodes, edges, []


def _import_target(text: str) -> str:
    # вытащить из "import x from 'mod'" / "use a::b" примерный таргет
    for kw in (" from ", "import ", "use ", "require"):
        if kw in text:
            tail = text.split(kw)[-1]
            return tail.strip(" ;'\"`()").split()[0] if tail.strip() else text.strip()
    return text.strip(" ;'\"`")[:80]
