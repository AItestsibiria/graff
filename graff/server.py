"""Graff SaaS — HTTP сервер: REST API + MCP-over-SSE.

Использование:
  graff-server                        # порт 8765
  GRAFF_PORT=9000 graff-server

Клиент:
  POST /api/repos {"url": "https://github.com/user/repo"}  → {"token": "...", "mcp_url": "/mcp/TOKEN"}
  GET  /api/repos/{token}                                   → {"status": "ready", "nodes": N}
  MCP: {"mcpServers": {"graff": {"url": "https://graff.sh/mcp/TOKEN"}}}
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

DATA_DIR = Path(os.environ.get("GRAFF_DATA", "/var/graff-saas"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# API-ключи: GRAFF_API_KEYS=key1,key2 (пусто = auth отключён, dev-режим)
_API_KEYS: set[str] = set(
    k.strip() for k in os.environ.get("GRAFF_API_KEYS", "").split(",") if k.strip()
)


def _auth(x_api_key: str | None = Header(default=None)):
    if not _API_KEYS:
        return  # dev-режим без auth
    if not x_api_key or x_api_key not in _API_KEYS:
        raise HTTPException(401, "Требуется X-Api-Key")

# token → {status, url, db, nodes, edges, created_at, error?}
_repos: dict[str, dict] = {}
# SSE-очереди: token → [asyncio.Queue, ...]
_sse_queues: dict[str, list[asyncio.Queue]] = {}

app = FastAPI(title="Graff SaaS", version="0.1.0",
              description="Code graph + MCP server as a service")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


# ─── helpers ────────────────────────────────────────────────────────────────

def _token(url: str) -> str:
    import hashlib
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def _push(token: str, msg: dict):
    for q in _sse_queues.get(token, []):
        q.put_nowait(msg)


async def _index(token: str, url: str):
    entry = _repos[token]
    repo_dir = DATA_DIR / token / "repo"
    try:
        entry["status"] = "cloning"
        _push(token, {"status": "cloning"})
        if repo_dir.exists():
            shutil.rmtree(repo_dir)
        repo_dir.parent.mkdir(parents=True, exist_ok=True)

        proc = await asyncio.create_subprocess_exec(
            "git", "clone", "--depth=1", url, str(repo_dir),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, err = await asyncio.wait_for(proc.communicate(), timeout=120)
        if proc.returncode != 0:
            entry.update({"status": "error", "error": err.decode()[-300:]})
            _push(token, {"status": "error"})
            return

        entry["status"] = "indexing"
        _push(token, {"status": "indexing"})
        from .analyzer import analyze
        res = analyze(str(repo_dir))
        entry.update({"status": "ready", "nodes": res["nodes"],
                       "edges": res["edges"], "db": res["db"]})
        _push(token, {"status": "ready", "nodes": res["nodes"],
                       "edges": res["edges"]})
    except Exception as e:
        entry.update({"status": "error", "error": str(e)})
        _push(token, {"status": "error"})


# ─── REST API ────────────────────────────────────────────────────────────────

class RepoIn(BaseModel):
    url: str


@app.get("/")
async def root():
    return {"service": "Graff SaaS", "version": "0.1.0",
            "usage": "POST /api/repos {url} → token → /mcp/{token}/sse", "tools": 14}


@app.post("/api/repos")
async def submit_repo(payload: RepoIn, bg: BackgroundTasks, _=Depends(_auth)):
    url = payload.url.strip().rstrip("/")
    if not url.startswith("https://github.com/"):
        raise HTTPException(400, "Поддерживается только https://github.com/...")
    tok = _token(url)
    if tok not in _repos:
        _repos[tok] = {"token": tok, "url": url,
                       "status": "queued", "created_at": time.time()}
        bg.add_task(_index, tok, url)
    return {"token": tok, "status": _repos[tok]["status"],
            "mcp_url": f"/mcp/{tok}",
            "mcp_config": {"mcpServers": {"graff": {"url": f"/mcp/{tok}"}}}}


@app.get("/api/repos")
async def list_repos(_=Depends(_auth)):
    return [{"token": e["token"], "url": e["url"], "status": e["status"],
             "nodes": e.get("nodes", 0), "edges": e.get("edges", 0)}
            for e in _repos.values()]


@app.get("/api/repos/{tok}")
async def get_repo(tok: str):
    e = _repos.get(tok)
    if not e:
        raise HTTPException(404, "токен не найден")
    return {k: v for k, v in e.items() if k != "db"}


# ─── MCP over HTTP+SSE ───────────────────────────────────────────────────────

async def _sse_stream(token: str, q: asyncio.Queue) -> AsyncGenerator[str, None]:
    session_id = uuid.uuid4().hex
    yield f"event: endpoint\ndata: /mcp/{token}/message?sessionId={session_id}\n\n"
    try:
        while True:
            try:
                msg = await asyncio.wait_for(q.get(), timeout=25)
                yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
            except asyncio.TimeoutError:
                yield ": ping\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        try:
            _sse_queues[token].remove(q)
        except (KeyError, ValueError):
            pass


@app.get("/mcp/{tok}/sse")
async def mcp_sse(tok: str):
    e = _repos.get(tok)
    if not e or e["status"] != "ready":
        raise HTTPException(404, "репо не готово — дождитесь status=ready")
    q: asyncio.Queue = asyncio.Queue()
    _sse_queues.setdefault(tok, []).append(q)
    return StreamingResponse(
        _sse_stream(tok, q),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/mcp/{tok}/message")
async def mcp_message(tok: str, request: Request):
    e = _repos.get(tok)
    if not e or e["status"] != "ready":
        raise HTTPException(404, "репо не готово")
    db_path = e.get("db", "")
    if not db_path or not os.path.exists(db_path):
        raise HTTPException(503, "граф недоступен")

    body = await request.body()
    try:
        req_obj = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(400, "invalid JSON")

    resp = _handle(req_obj, db_path)
    if resp is None:
        return JSONResponse({})
    _push(tok, resp)
    return JSONResponse(resp)


def _handle(req: dict, db_path: str) -> dict | None:
    from . import __version__, queries, analytics, rules
    from .graph import GraphStore
    from .mcp_server import TOOLS

    method = req.get("method")
    rid = req.get("id")

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "graff", "version": __version__},
        }}
    if method in ("notifications/initialized",):
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = req.get("params", {})
        name = params.get("name", "")
        args = params.get("arguments", {})
        try:
            store = GraphStore(db_path)
            result = _dispatch(name, args, store)
            text = json.dumps(result, ensure_ascii=False, indent=2)
            return {"jsonrpc": "2.0", "id": rid,
                    "result": {"content": [{"type": "text", "text": text}]}}
        except Exception as ex:
            return {"jsonrpc": "2.0", "id": rid,
                    "result": {"content": [{"type": "text",
                               "text": f"graff error: {ex}"}], "isError": True}}
    if rid is not None:
        return {"jsonrpc": "2.0", "id": rid,
                "error": {"code": -32601, "message": f"unknown: {method}"}}
    return None


def _dispatch(name: str, args: dict, store) -> dict:
    from . import queries, analytics, rules
    if name == "graff_find":
        return queries.find(store, args["query"], kind=args.get("kind"),
                            limit=args.get("limit", 25))
    if name == "graff_context":
        return queries.context(store, args["name"], kind=args.get("kind"))
    if name == "graff_impact":
        return queries.impact(store, args["name"], kind=args.get("kind"),
                              direction=args.get("direction", "upstream"),
                              max_depth=args.get("depth", 3))
    if name == "graff_flows":
        return queries.flows(store, args["query"], max_depth=args.get("depth", 6))
    if name == "graff_route_map":
        return queries.route_map(store, query=args.get("query"))
    if name == "graff_hotspots":
        return analytics.hotspots(store, limit=args.get("limit", 20))
    if name == "graff_deadcode":
        return analytics.dead_code(store, limit=args.get("limit", 50))
    if name == "graff_cycles":
        return analytics.cycles(store)
    if name == "graff_check":
        repo_path = store.get_meta("repo_path") or "."
        return rules.run_rules(store, repo_path,
                               min_severity=args.get("min_severity", "INFO"))
    if name == "graff_roles":
        return rules.detect_roles(store)
    if name == "graff_status":
        c = store.counts()
        return {"nodes": c["nodes"], "edges": c["edges"], "by_kind": c["by_kind"],
                "repo_path": store.get_meta("repo_path"),
                "indexed_at": store.get_meta("indexed_at")}
    if name == "graff_list_repos":
        from . import registry
        return {"repos": registry.list_repos()}
    raise ValueError(f"неизвестный инструмент: {name}")


# ─── entrypoint ─────────────────────────────────────────────────────────────

def main():
    import uvicorn
    uvicorn.run("graff.server:app",
                host=os.environ.get("GRAFF_HOST", "0.0.0.0"),
                port=int(os.environ.get("GRAFF_PORT", "8765")),
                reload=False)


if __name__ == "__main__":
    main()
