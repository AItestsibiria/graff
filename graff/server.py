"""Graff SaaS — HTTP сервер: лендинг + REST API + MCP-over-SSE + Stripe.

Env:
  GRAFF_PORT=8765
  GRAFF_DATA=/var/graff-saas
  STRIPE_SECRET_KEY=sk_live_...
  STRIPE_WEBHOOK_SECRET=whsec_...
  STRIPE_PRICE_PRO=price_...
  STRIPE_PRICE_TEAM=price_...
  GRAFF_BASE_URL=https://72-56-247-149.sslip.io/graff
"""
# Copyright (c) 2025 BAI / AItestsibiria. Business Source License 1.1.
# Commercial SaaS use requires a commercial license: egnovoselov@gmail.com

from __future__ import annotations

import asyncio
import json
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import AsyncGenerator

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

from .auth import PLANS, add_repo, count_repos, get_key, register, set_stripe_customer, touch, upgrade_plan

DATA_DIR = Path(os.environ.get("GRAFF_DATA", "/var/graff-saas"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = os.environ.get("GRAFF_BASE_URL", "https://72-56-247-149.sslip.io/graff")
STRIPE_SECRET     = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK    = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# in-memory: token → entry
_repos: dict[str, dict] = {}
# SSE-очереди
_sse_queues: dict[str, list[asyncio.Queue]] = {}

app = FastAPI(title="Graff SaaS", version="0.1.0", docs_url="/graff/docs")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


# ─── auth dep ────────────────────────────────────────────────────────────────

def _require_key(x_api_key: str | None = Header(default=None)) -> dict:
    if not x_api_key:
        raise HTTPException(401, "Требуется заголовок X-Api-Key")
    row = get_key(x_api_key)
    if not row:
        raise HTTPException(401, "Неверный или неактивный ключ")
    touch(x_api_key)
    return dict(row)


# ─── helpers ─────────────────────────────────────────────────────────────────

def _repo_token(url: str) -> str:
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


# ─── лендинг ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
@app.get("/graff", response_class=HTMLResponse)
@app.get("/graff/", response_class=HTMLResponse)
async def landing():
    from .landing import HTML
    return HTML


# ─── auth / регистрация ──────────────────────────────────────────────────────

class RegisterIn(BaseModel):
    email: str
    plan: str = "free"


@app.post("/graff/api/register")
@app.post("/api/register")
async def api_register(payload: RegisterIn):
    email = payload.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(400, "Некорректный email")
    plan = payload.plan if payload.plan in PLANS else "free"
    result = register(email, plan)
    return result


# ─── Stripe checkout ─────────────────────────────────────────────────────────

class UpgradeIn(BaseModel):
    plan: str


@app.post("/graff/api/upgrade")
@app.post("/api/upgrade")
async def api_upgrade(payload: UpgradeIn, key_data: dict = Depends(_require_key)):
    if not STRIPE_SECRET:
        raise HTTPException(503, "Stripe не настроен")
    import stripe
    stripe.api_key = STRIPE_SECRET
    plan = payload.plan if payload.plan in ("pro", "team") else "pro"
    price_id = PLANS[plan]["price_id"]
    if not price_id:
        raise HTTPException(503, f"Stripe price для '{plan}' не настроен")

    customer_id = key_data.get("stripe_customer_id")
    if not customer_id:
        customer = stripe.Customer.create(email=key_data["email"],
                                          metadata={"api_key": key_data["key"]})
        customer_id = customer.id
        set_stripe_customer(key_data["key"], customer_id)

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{BASE_URL}/?upgraded=1",
        cancel_url=f"{BASE_URL}/",
        metadata={"plan": plan, "api_key": key_data["key"]},
    )
    return {"checkout_url": session.url}


@app.post("/graff/webhooks/stripe")
@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    if not STRIPE_SECRET:
        raise HTTPException(503, "Stripe не настроен")
    import stripe
    stripe.api_key = STRIPE_SECRET
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK)
    except Exception as e:
        raise HTTPException(400, str(e))

    if event["type"] in ("checkout.session.completed",
                          "customer.subscription.updated"):
        obj = event["data"]["object"]
        customer_id = obj.get("customer")
        plan = (obj.get("metadata") or {}).get("plan", "pro")
        sub_id = obj.get("subscription") or obj.get("id", "")
        if customer_id:
            upgrade_plan(customer_id, plan, sub_id)
    return {"ok": True}


# ─── REST: репо ───────────────────────────────────────────────────────────────

class RepoIn(BaseModel):
    url: str


@app.post("/graff/api/repos")
@app.post("/api/repos")
async def submit_repo(payload: RepoIn, bg: BackgroundTasks,
                      key_data: dict = Depends(_require_key)):
    url = payload.url.strip().rstrip("/")
    if not url.startswith("https://github.com/"):
        raise HTTPException(400, "Поддерживается только https://github.com/...")

    api_key = key_data["key"]
    tok = _repo_token(url)

    if tok not in _repos:
        used = count_repos(api_key)
        if used >= key_data["repos_limit"]:
            raise HTTPException(403,
                f"Лимит репозиториев для плана '{key_data['plan']}': "
                f"{key_data['repos_limit']}. Обновите план: POST /api/upgrade")
        _repos[tok] = {"token": tok, "url": url,
                        "status": "queued", "created_at": time.time()}
        add_repo(api_key, tok, url)
        bg.add_task(_index, tok, url)

    mcp_url = f"{BASE_URL}/mcp/{tok}"
    return {
        "token": tok,
        "status": _repos[tok]["status"],
        "mcp_url": mcp_url,
        "mcp_config": {"mcpServers": {"graff": {"url": mcp_url}}},
    }


@app.get("/graff/api/repos")
@app.get("/api/repos")
async def list_repos(key_data: dict = Depends(_require_key)):
    return [{"token": e["token"], "url": e["url"], "status": e["status"],
             "nodes": e.get("nodes", 0), "edges": e.get("edges", 0)}
            for e in _repos.values()]


@app.get("/graff/api/repos/{tok}")
@app.get("/api/repos/{tok}")
async def get_repo(tok: str, key_data: dict = Depends(_require_key)):
    e = _repos.get(tok)
    if not e:
        raise HTTPException(404, "токен не найден")
    return {k: v for k, v in e.items() if k != "db"}


# ─── MCP over HTTP+SSE ───────────────────────────────────────────────────────

async def _sse_stream(token: str, q: asyncio.Queue) -> AsyncGenerator[str, None]:
    session_id = uuid.uuid4().hex
    yield f"event: endpoint\ndata: {BASE_URL}/mcp/{token}/message?sessionId={session_id}\n\n"
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


@app.get("/graff/mcp/{tok}/sse")
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


@app.post("/graff/mcp/{tok}/message")
@app.post("/mcp/{tok}/message")
async def mcp_message(tok: str, request: Request):
    e = _repos.get(tok)
    if not e or e["status"] != "ready":
        raise HTTPException(404, "репо не готово")
    db_path = e.get("db", "")
    if not db_path or not os.path.exists(db_path):
        raise HTTPException(503, "граф недоступен")
    try:
        req_obj = json.loads(await request.body())
    except json.JSONDecodeError:
        raise HTTPException(400, "invalid JSON")
    resp = _handle(req_obj, db_path)
    if resp is None:
        return JSONResponse({})
    _push(tok, resp)
    return JSONResponse(resp)


# ─── MCP dispatch ────────────────────────────────────────────────────────────

def _handle(req: dict, db_path: str) -> dict | None:
    from . import __version__
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
            from .graph import GraphStore
            store = GraphStore(db_path)
            result = _dispatch(name, args, store)
            return {"jsonrpc": "2.0", "id": rid,
                    "result": {"content": [{"type": "text",
                               "text": json.dumps(result, ensure_ascii=False, indent=2)}]}}
        except Exception as ex:
            return {"jsonrpc": "2.0", "id": rid,
                    "result": {"content": [{"type": "text", "text": f"graff error: {ex}"}],
                               "isError": True}}
    if rid is not None:
        return {"jsonrpc": "2.0", "id": rid,
                "error": {"code": -32601, "message": f"unknown: {method}"}}
    return None


def _dispatch(name: str, args: dict, store) -> dict:
    from . import analytics, queries, rules
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
        return rules.run_rules(store, store.get_meta("repo_path") or ".",
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


# ─── entrypoint ──────────────────────────────────────────────────────────────

def main():
    import uvicorn
    uvicorn.run("graff.server:app",
                host=os.environ.get("GRAFF_HOST", "0.0.0.0"),
                port=int(os.environ.get("GRAFF_PORT", "8765")),
                reload=False)


if __name__ == "__main__":
    main()
