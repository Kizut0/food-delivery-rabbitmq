"""Apply SQL migrations, once each, in filename order.

Run as its own one-shot container before the API and workers start:

    python -m scripts.migrate

Why a migration runner and not "CREATE TABLE IF NOT EXISTS" inside the app:
five processes racing to create the same tables at boot is how you get
deadlocks that only happen on the demo machine. One process owns the schema.
"""
import pathlib
import sys

from app import db, logs

log = logs.setup("migrate")

MIGRATIONS = pathlib.Path(__file__).resolve().parent.parent / "migrations"

LEDGER = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename    TEXT PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""


def main() -> int:
    db.wait_for_db()
    with db.cursor() as cur:
        cur.execute(LEDGER)
        cur.execute("SELECT filename FROM schema_migrations")
        done = {r["filename"] for r in cur.fetchall()}

    files = sorted(MIGRATIONS.glob("*.sql"))
    if not files:
        log.error("no .sql files found in %s", MIGRATIONS)
        return 1

    applied = 0
    for path in files:
        if path.name in done:
            log.info("skip    %s (already applied)", path.name)
            continue
        sql = path.read_text()
        with db.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "INSERT INTO schema_migrations (filename) VALUES (%s)",
                (path.name,),
            )
        log.info("applied %s", path.name)
        applied += 1

    log.info("schema up to date (%s newly applied, %s total)", applied, len(files))
    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())