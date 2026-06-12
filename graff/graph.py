"""Графовое хранилище Graff на SQLite.

Граф = nodes (символы: File/Class/Function/Method/Variable) + edges (связи:
IMPORTS/CALLS/HAS_METHOD/INHERITS/CONTAINS/REFERENCES). Поиск по именам — через
FTS5 (BM25). Хранится в <repo>/.graff/graph.db.
"""
# Copyright (c) 2025 BAI / AItestsibiria. Business Source License 1.1.
# Commercial SaaS use requires a commercial license: egnovoselov@gmail.com

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Iterable, Optional

# Типы узлов и связей (канон — держать синхронно с парсерами и запросами)
NODE_KINDS = ("File", "Module", "Class", "Function", "Method", "Variable")
EDGE_TYPES = ("IMPORTS", "CALLS", "HAS_METHOD", "INHERITS", "CONTAINS", "REFERENCES")

SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
  uid        TEXT PRIMARY KEY,
  kind       TEXT NOT NULL,
  name       TEXT NOT NULL,
  file_path  TEXT NOT NULL,
  start_line INTEGER,
  end_line   INTEGER,
  parent_uid TEXT,
  language   TEXT,
  signature  TEXT
);
CREATE INDEX IF NOT EXISTS idx_nodes_name   ON nodes(name);
CREATE INDEX IF NOT EXISTS idx_nodes_file   ON nodes(file_path);
CREATE INDEX IF NOT EXISTS idx_nodes_parent ON nodes(parent_uid);
CREATE INDEX IF NOT EXISTS idx_nodes_kind   ON nodes(kind);

CREATE TABLE IF NOT EXISTS edges (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  src_uid    TEXT NOT NULL,
  dst_uid    TEXT,
  dst_name   TEXT,
  type       TEXT NOT NULL,
  confidence REAL DEFAULT 1.0,
  file_path  TEXT,
  line       INTEGER
);
CREATE INDEX IF NOT EXISTS idx_edges_src  ON edges(src_uid);
CREATE INDEX IF NOT EXISTS idx_edges_dst  ON edges(dst_uid);
CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(type);
CREATE INDEX IF NOT EXISTS idx_edges_dstname ON edges(dst_name);

CREATE TABLE IF NOT EXISTS meta (
  key   TEXT PRIMARY KEY,
  value TEXT
);

CREATE TABLE IF NOT EXISTS files (
  path  TEXT PRIMARY KEY,
  mtime REAL,
  lang  TEXT
);

CREATE TABLE IF NOT EXISTS imports (
  file_path TEXT,
  name      TEXT,
  module    TEXT
);
CREATE INDEX IF NOT EXISTS idx_imports_file ON imports(file_path);
"""


@dataclass
class Node:
    uid: str
    kind: str
    name: str
    file_path: str
    start_line: int = 0
    end_line: int = 0
    parent_uid: Optional[str] = None
    language: str = ""
    signature: str = ""


@dataclass
class Edge:
    src_uid: str
    type: str
    dst_uid: Optional[str] = None
    dst_name: Optional[str] = None
    confidence: float = 1.0
    file_path: str = ""
    line: int = 0


class GraphStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.executescript(SCHEMA)
        self._init_fts()

    def _init_fts(self):
        # FTS5 для BM25-поиска по именам/сигнатурам. Если FTS5 нет — деградируем
        # к LIKE-поиску (флаг self.has_fts).
        try:
            self.conn.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5("
                "uid UNINDEXED, name, signature, file_path, tokenize='unicode61')"
            )
            self.has_fts = True
        except sqlite3.OperationalError:
            self.has_fts = False

    # ---- запись ----
    def reset(self):
        """Очистить граф (полная переиндексация)."""
        self.conn.executescript(
            "DELETE FROM nodes; DELETE FROM edges; DELETE FROM meta;"
        )
        if self.has_fts:
            self.conn.execute("DELETE FROM nodes_fts")
        self.conn.commit()

    def add_nodes(self, nodes: Iterable[Node]):
        rows = [
            (n.uid, n.kind, n.name, n.file_path, n.start_line, n.end_line,
             n.parent_uid, n.language, n.signature)
            for n in nodes
        ]
        self.conn.executemany(
            "INSERT OR REPLACE INTO nodes"
            "(uid,kind,name,file_path,start_line,end_line,parent_uid,language,signature)"
            " VALUES(?,?,?,?,?,?,?,?,?)", rows
        )
        if self.has_fts:
            self.conn.executemany(
                "INSERT INTO nodes_fts(uid,name,signature,file_path) VALUES(?,?,?,?)",
                [(n.uid, n.name, n.signature, n.file_path) for n in nodes],
            )

    def add_edges(self, edges: Iterable[Edge]):
        rows = [
            (e.src_uid, e.dst_uid, e.dst_name, e.type, e.confidence, e.file_path, e.line)
            for e in edges
        ]
        self.conn.executemany(
            "INSERT INTO edges(src_uid,dst_uid,dst_name,type,confidence,file_path,line)"
            " VALUES(?,?,?,?,?,?,?)", rows
        )

    def set_meta(self, key: str, value: str):
        self.conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)", (key, value))

    # ---- учёт файлов (для инкрементального реиндекса) ----
    def set_file(self, path: str, mtime: float, lang: str):
        self.conn.execute("INSERT OR REPLACE INTO files(path,mtime,lang) VALUES(?,?,?)",
                          (path, mtime, lang))

    def get_files(self) -> dict[str, float]:
        return {r["path"]: r["mtime"]
                for r in self.conn.execute("SELECT path, mtime FROM files")}

    def delete_file_subgraph(self, rel_path: str):
        """Удалить все узлы и связи файла (для переиндексации одного файла)."""
        self.conn.execute("DELETE FROM edges WHERE file_path=?", (rel_path,))
        self.conn.execute("DELETE FROM nodes WHERE file_path=?", (rel_path,))
        if self.has_fts:
            self.conn.execute("DELETE FROM nodes_fts WHERE file_path=?", (rel_path,))
        self.conn.execute("DELETE FROM files WHERE path=?", (rel_path,))
        self.conn.execute("DELETE FROM imports WHERE file_path=?", (rel_path,))

    def add_imports(self, file_path: str, imports: list[tuple[str, str]]):
        if imports:
            self.conn.executemany(
                "INSERT INTO imports(file_path,name,module) VALUES(?,?,?)",
                [(file_path, n, m) for n, m in imports],
            )

    def resolve_imports_python(self) -> int:
        """Import-aware резолв: для неразрешённых CALLS из Python-файла, если имя
        вызова импортировано (from M import N), привязать к определению N в файле
        модуля M. Снимает неоднозначность по голому имени."""
        # карта суффикс-модуля → file_uid для Python-файлов
        mod2file: dict[str, str] = {}
        for r in self.conn.execute(
            "SELECT uid, file_path FROM nodes WHERE kind='File' AND language='python'"
        ):
            parts = r["file_path"][:-3].split("/")  # без .py
            for i in range(len(parts)):
                suffix = ".".join(parts[i:])
                mod2file.setdefault(suffix, r["uid"])
                mod2file.setdefault(parts[-1], r["uid"])
        # имя+файл определения → uid
        def_idx: dict[tuple[str, str], str] = {}
        for r in self.conn.execute(
            "SELECT uid, name, file_path FROM nodes WHERE kind IN ('Function','Class')"
        ):
            def_idx[(r["name"], r["file_path"])] = r["uid"]
        file_of = {r["uid"]: r["file_path"]
                   for r in self.conn.execute("SELECT uid, file_path FROM nodes WHERE kind='File'")}
        # импорты по файлу: name → module
        imp_by_file: dict[str, dict[str, str]] = {}
        for r in self.conn.execute("SELECT file_path, name, module FROM imports"):
            imp_by_file.setdefault(r["file_path"], {})[r["name"]] = r["module"]

        updates = []
        for e in self.conn.execute(
            "SELECT id, src_uid, dst_name, file_path FROM edges "
            "WHERE dst_uid IS NULL AND type='CALLS'"
        ):
            mod = imp_by_file.get(e["file_path"], {}).get(e["dst_name"])
            if not mod:
                continue
            target_file_uid = mod2file.get(mod) or mod2file.get(mod.split(".")[-1])
            if not target_file_uid:
                continue
            tfile = file_of.get(target_file_uid, "")
            duid = def_idx.get((e["dst_name"], tfile))
            if duid:
                updates.append((duid, 0.95, e["id"]))
        self.conn.executemany(
            "UPDATE edges SET dst_uid=?, confidence=? WHERE id=?", updates
        )
        self.conn.commit()
        return len(updates)

    def commit(self):
        self.conn.commit()

    # ---- разрешение связей (CALLS/IMPORTS по имени → uid) ----
    def resolve_edges_by_name(self):
        """2-й проход: связи с dst_name без dst_uid — привязка к определению по
        имени. КОНСЕРВАТИВНО (избегаем кросс-язык/кросс-файл ложных совпадений):
          • только определения ТОГО ЖЕ языка, что и источник связи;
          • тот же файл → confidence 1.0;
          • ровно один кандидат в языке → 0.9;
          • несколько → НЕ угадываем (оставляем неразрешённым)."""
        # язык каждого узла-источника
        lang_of: dict[str, str] = {
            r["uid"]: r["language"]
            for r in self.conn.execute("SELECT uid, language FROM nodes")
        }
        # индекс: имя → список (uid, file_path, language)
        name_idx: dict[str, list[tuple]] = {}
        for r in self.conn.execute(
            "SELECT uid, name, file_path, language FROM nodes "
            "WHERE kind IN ('Function','Method','Class')"
        ):
            name_idx.setdefault(r["name"], []).append(
                (r["uid"], r["file_path"], r["language"])
            )

        unresolved = self.conn.execute(
            "SELECT id, src_uid, dst_name, file_path, confidence FROM edges "
            "WHERE dst_uid IS NULL AND dst_name IS NOT NULL"
        ).fetchall()

        updates = []
        for e in unresolved:
            cands = name_idx.get(e["dst_name"])
            if not cands:
                continue
            src_lang = lang_of.get(e["src_uid"], "")
            cands = [c for c in cands if c[2] == src_lang]  # тот же язык
            if not cands:
                continue
            same_file = [c for c in cands if c[1] == e["file_path"]]
            if same_file:
                updates.append((same_file[0][0], 1.0, e["id"]))
            elif e["confidence"] < 1.0:
                # вызов obj.method() — имя метода неуникально, не угадываем вне файла
                continue
            elif len(cands) == 1:
                updates.append((cands[0][0], 0.9, e["id"]))
            # несколько кандидатов в языке → не угадываем
        self.conn.executemany(
            "UPDATE edges SET dst_uid=?, confidence=? WHERE id=?", updates
        )
        self.conn.commit()
        return len(updates)

    # ---- чтение ----
    def get_node(self, uid: str) -> Optional[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM nodes WHERE uid=?", (uid,)).fetchone()

    def find_by_name(self, name: str, kind: Optional[str] = None, limit: int = 25):
        q = "SELECT * FROM nodes WHERE name=?"
        args = [name]
        if kind:
            q += " AND kind=?"
            args.append(kind)
        q += " LIMIT ?"
        args.append(limit)
        return self.conn.execute(q, args).fetchall()

    def search(self, query: str, limit: int = 25):
        """Поиск символов. FTS5 BM25 если есть, иначе LIKE."""
        if self.has_fts:
            try:
                # экранируем спецсимволы FTS, оборачиваем в кавычки + префикс
                safe = '"' + query.replace('"', '""') + '"'
                rows = self.conn.execute(
                    "SELECT n.*, bm25(nodes_fts) AS score FROM nodes_fts "
                    "JOIN nodes n ON n.uid = nodes_fts.uid "
                    "WHERE nodes_fts MATCH ? ORDER BY score LIMIT ?",
                    (safe, limit),
                ).fetchall()
                if rows:
                    return rows
            except sqlite3.OperationalError:
                pass
        like = f"%{query}%"
        return self.conn.execute(
            "SELECT * FROM nodes WHERE name LIKE ? ORDER BY length(name) LIMIT ?",
            (like, limit),
        ).fetchall()

    def edges_from(self, uid: str, etype: Optional[str] = None):
        q = "SELECT * FROM edges WHERE src_uid=?"
        args = [uid]
        if etype:
            q += " AND type=?"
            args.append(etype)
        return self.conn.execute(q, args).fetchall()

    def edges_to(self, uid: str, etype: Optional[str] = None):
        q = "SELECT * FROM edges WHERE dst_uid=?"
        args = [uid]
        if etype:
            q += " AND type=?"
            args.append(etype)
        return self.conn.execute(q, args).fetchall()

    def children(self, parent_uid: str):
        return self.conn.execute(
            "SELECT * FROM nodes WHERE parent_uid=?", (parent_uid,)
        ).fetchall()

    def counts(self) -> dict:
        n = self.conn.execute("SELECT count(*) c FROM nodes").fetchone()["c"]
        e = self.conn.execute("SELECT count(*) c FROM edges").fetchone()["c"]
        by_kind = {
            r["kind"]: r["c"]
            for r in self.conn.execute("SELECT kind, count(*) c FROM nodes GROUP BY kind")
        }
        return {"nodes": n, "edges": e, "by_kind": by_kind}

    def get_meta(self, key: str) -> Optional[str]:
        r = self.conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return r["value"] if r else None

    def close(self):
        self.conn.close()
