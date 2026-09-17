"""PostgreSQL connection pool, shared by the API and every worker.

A pool rather than a connection per query: the load test opens dozens of
requests at once and a new TCP + TLS + auth handshake per order would show up
in the very latency numbers we are trying to measure.

The pool is created lazily and waits for the database, because in Docker the
API container starts at the same moment as Postgres.
"""
import time
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app import config, logs

log = logs.setup("db")

_pool: ConnectionPool | None = None


def pool() -> ConnectionPool:
    """Return the process-wide pool, creating and warming it on first use."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=config.DATABASE_URL,
            min_size=1,
            max_size=10,
            kwargs={"row_factory": dict_row},
            open=False,
        )
        _pool.open()
        wait_for_db()
    return _pool


def wait_for_db(retries: int | None = None, delay: float | None = None) -> None:
    """Block until the database answers, or give up with a clear message."""
    retries = retries if retries is not None else config.CONNECT_RETRIES
    delay = delay if delay is not None else config.CONNECT_DELAY
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with psycopg.connect(config.DATABASE_URL, connect_timeout=5) as conn:
                conn.execute("SELECT 1")
            return
        except Exception as exc:
            last = exc
            log.warning(
                "database not ready (%s/%s), retrying in %ss",
                attempt, retries, delay
            )
            time.sleep(delay)
    raise RuntimeError(f"could not reach PostgreSQL: {last}")


@contextmanager
def cursor(commit: bool = True):
    """Borrow a connection, hand back a dict-row cursor, always return it."""
    with pool().connection() as conn:
        with conn.cursor() as cur:
            yield cur
        if commit:
            conn.commit()


def healthy() -> bool:
    try:
        with cursor(commit=False) as cur:
            cur.execute("SELECT 1")
        return True
    except Exception:
        return False


def close() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None