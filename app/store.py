"""Every SQL statement in the project lives here.

Keeping queries out of the API and the workers means the handlers read like
business steps ("mark it paid") rather than plumbing, and there is exactly one
place to look when the schema changes.
"""
import json

from app import db


def create_order(order_id: str, customer: str, restaurant: str,
                 items: list[str], total: float, status: str = "PENDING") -> None:
    with db.cursor() as cur:
        cur.execute(
            """
            INSERT INTO orders (id, customer, restaurant, items, total, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (order_id, customer, restaurant, json.dumps(items), total, status),
        )
        cur.execute(
            """
            INSERT INTO order_events (order_id, stage, detail, worker)
            VALUES (%s, %s, %s, %s)
            """,
            (order_id, status, "order accepted", "api"),
        )


def set_status(order_id: str, status: str, detail: str | None = None,
               worker: str | None = None) -> None:
    """Move the ticket to a new state and record the transition."""
    with db.cursor() as cur:
        cur.execute(
            "UPDATE orders SET status = %s, updated_at = now() WHERE id = %s",
            (status, order_id),
        )
        cur.execute(
            """
            INSERT INTO order_events (order_id, stage, detail, worker)
            VALUES (%s, %s, %s, %s)
            """,
            (order_id, status, detail, worker),
        )


def add_event(order_id: str, stage: str, detail: str | None = None,
              worker: str | None = None) -> None:
    """Record a step that is not itself a status change."""
    with db.cursor() as cur:
        cur.execute(
            """
            INSERT INTO order_events (order_id, stage, detail, worker)
            VALUES (%s, %s, %s, %s)
            """,
            (order_id, stage, detail, worker),
        )


def get_order(order_id: str) -> dict | None:
    with db.cursor(commit=False) as cur:
        cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
        order = cur.fetchone()
        if order is None:
            return None
        cur.execute(
            """
            SELECT stage, detail, worker, at
              FROM order_events
             WHERE order_id = %s
             ORDER BY id
            """,
            (order_id,),
        )
        events = cur.fetchall()

    out = dict(order)
    out["total"] = float(out["total"])
    out["created_at"] = out["created_at"].isoformat()
    out["updated_at"] = out["updated_at"].isoformat()
    out["timeline"] = [
        {**dict(e), "at": e["at"].isoformat()} for e in events
    ]
    return out


def counts_by_status() -> dict[str, int]:
    with db.cursor(commit=False) as cur:
        cur.execute("SELECT status, COUNT(*) AS n FROM orders GROUP BY status")
        return {r["status"]: r["n"] for r in cur.fetchall()}


def truncate_all() -> None:
    """Used only by scripts/reset.py before a rehearsal."""
    with db.cursor() as cur:
        cur.execute("TRUNCATE order_events, orders")
