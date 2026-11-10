
"""Intentionally vulnerable demo: no authentication or authorization checks.

The documented policies describe intended enforcement by the future BLADE proxy.
This backend deliberately permits BOLA, admin, tenant and membership bypasses.
"""

import sqlite3
from collections.abc import Iterator
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException


def create_app(db_path: str | Path = "demo.db") -> FastAPI:
    database = Path(db_path)

    @contextmanager
    def connection() -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(database)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        with connection() as conn:
            conn.executescript(Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))
            conn.executemany("INSERT OR IGNORE INTO orgs(id) VALUES (?)", [("org_1",), ("org_2",)])
            conn.executemany(
                "INSERT OR IGNORE INTO users(id, org_id, role, membership) VALUES (?, ?, ?, ?)",
                [("user_77", "org_1", "user", "basic"),
                 ("user_99", "org_2", "user", "basic"),
                 ("admin_1", "org_1", "admin", "premium")],
            )
            conn.executemany("INSERT OR IGNORE INTO orders(id, user_id) VALUES (?, ?)",
                             [(1042, "user_77"), (2001, "user_99")])
        yield

    app = FastAPI(title="BLADE vulnerable demo", lifespan=lifespan,
                  description="Intentionally performs no authentication or authorization checks.")

    def fetch_one(query: str, identifier: str | int) -> dict[str, Any]:
        with connection() as conn:
            row = conn.execute(query, (identifier,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Resource not found")
        return dict(row)

    # Intentionally NO authorization in any endpoint below, even with a JWT header.
    @app.get("/public/health", description="Intended policy: public")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/orders/{orderId}", description="Intended policy: owner_match; orders.user_id")
    def get_order(orderId: int) -> dict[str, Any]:
        return fetch_one("SELECT * FROM orders WHERE id = ?", orderId)

    @app.delete("/orders/{orderId}", description="Intended policy: owner_match; orders.user_id")
    def delete_order(orderId: int) -> dict[str, Any]:
        with connection() as conn:
            cursor = conn.execute("DELETE FROM orders WHERE id = ?", (orderId,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Resource not found")
        return {"deleted": orderId}

    @app.get("/users/{userId}", description="Intended policy: owner_or_admin; users.id")
    def get_user(userId: str) -> dict[str, Any]:
        return fetch_one("SELECT * FROM users WHERE id = ?", userId)

    @app.get("/admin/reports", description="Intended policy: role_required; roles: [admin]")
    def reports() -> dict[str, int]:
        with connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        return {"order_count": count}

    @app.get("/orgs/{orgId}/docs", description="Intended policy: tenant_match; orgs.id")
    def org_docs(orgId: str) -> dict[str, Any]:
        org = fetch_one("SELECT * FROM orgs WHERE id = ?", orgId)
        return {"org_id": org["id"], "docs": [{"title": f"Internal documentation for {orgId}"}]}

    @app.get("/premium/content", description="Intended policy: membership_required; allowed_membership: [premium]")
    def premium_content() -> dict[str, str]:
        return {"content": "Premium members content"}

    return app


app = create_app()
