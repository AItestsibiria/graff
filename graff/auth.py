"""API-ключи + планы + Stripe. SQLite в GRAFF_DATA/auth.db."""
# Copyright (c) 2025 BAI / AItestsibiria. Business Source License 1.1.
# Commercial SaaS use requires a commercial license: egnovoselov@gmail.com

from __future__ import annotations

import os
import secrets
import sqlite3
import time
from pathlib import Path

DATA_DIR = Path(os.environ.get("GRAFF_DATA", "/var/graff-saas"))

PLANS = {
    "free":  {"price_id": "",               "repos": 1,  "label": "Free",  "usd": 0},
    "pro":   {"price_id": os.environ.get("STRIPE_PRICE_PRO",  ""), "repos": 5,  "label": "Pro",   "usd": 20},
    "team":  {"price_id": os.environ.get("STRIPE_PRICE_TEAM", ""), "repos": 999,"label": "Team",  "usd": 50},
}


def _db() -> sqlite3.Connection:
    db = sqlite3.connect(str(DATA_DIR / "auth.db"), timeout=10)
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY,
            key TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            plan TEXT DEFAULT 'free',
            repos_limit INTEGER DEFAULT 1,
            stripe_customer_id TEXT,
            stripe_sub_id TEXT,
            active INTEGER DEFAULT 1,
            created_at REAL,
            last_used REAL
        );
        CREATE TABLE IF NOT EXISTS repo_usage (
            key TEXT NOT NULL,
            token TEXT NOT NULL,
            url TEXT,
            created_at REAL,
            PRIMARY KEY (key, token)
        );
    """)
    return db


def generate_key() -> str:
    return "grff_" + secrets.token_urlsafe(32)


def register(email: str, plan: str = "free") -> dict:
    key = generate_key()
    limit = PLANS.get(plan, PLANS["free"])["repos"]
    with _db() as db:
        db.execute(
            "INSERT INTO api_keys (key, email, plan, repos_limit, active, created_at) "
            "VALUES (?,?,?,?,1,?)",
            (key, email.lower().strip(), plan, limit, time.time()),
        )
    return {"key": key, "plan": plan, "repos_limit": limit}


def get_key(key: str) -> sqlite3.Row | None:
    return _db().execute(
        "SELECT * FROM api_keys WHERE key=? AND active=1", (key,)
    ).fetchone()


def touch(key: str):
    _db().execute("UPDATE api_keys SET last_used=? WHERE key=?", (time.time(), key))


def count_repos(key: str) -> int:
    return _db().execute(
        "SELECT count(*) FROM repo_usage WHERE key=?", (key,)
    ).fetchone()[0]


def add_repo(key: str, token: str, url: str):
    with _db() as db:
        db.execute(
            "INSERT OR IGNORE INTO repo_usage (key,token,url,created_at) VALUES (?,?,?,?)",
            (key, token, url, time.time()),
        )


def upgrade_plan(stripe_customer_id: str, plan: str, stripe_sub_id: str):
    limit = PLANS.get(plan, PLANS["free"])["repos"]
    with _db() as db:
        db.execute(
            "UPDATE api_keys SET plan=?, repos_limit=?, stripe_customer_id=?, "
            "stripe_sub_id=?, active=1 WHERE stripe_customer_id=? OR email=("
            "  SELECT email FROM api_keys WHERE stripe_customer_id=?)",
            (plan, limit, stripe_customer_id, stripe_sub_id,
             stripe_customer_id, stripe_customer_id),
        )


def set_stripe_customer(key: str, customer_id: str):
    with _db() as db:
        db.execute("UPDATE api_keys SET stripe_customer_id=? WHERE key=?",
                   (customer_id, key))
