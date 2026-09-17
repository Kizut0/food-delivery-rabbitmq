-- Initial schema.
--
-- Two tables, on purpose:
--   orders        the current state of the ticket  (one row per order)
--   order_events  the append-only history          (many rows per order)
--
-- The history is what makes the demo legible: GET /orders/{id} returns the
-- whole journey, so the audience watches PENDING -> PAID -> COMPLETED instead
-- of staring at one field that changes silently.

CREATE TABLE IF NOT EXISTS orders (
    id           TEXT PRIMARY KEY,
    customer     TEXT        NOT NULL,
    restaurant   TEXT        NOT NULL,
    items        JSONB       NOT NULL,
    total        NUMERIC(10, 2) NOT NULL CHECK (total > 0),
    status       TEXT        NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS order_events (
    id        BIGSERIAL PRIMARY KEY,
    order_id  TEXT        NOT NULL REFERENCES orders (id) ON DELETE CASCADE,
    stage     TEXT        NOT NULL,
    detail    TEXT,
    worker    TEXT,
    at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- The timeline is always read per order, in insertion order.
CREATE INDEX IF NOT EXISTS order_events_order_id_idx
    ON order_events (order_id, id);

-- /stats groups by status, and the chaos demo filters on it.
CREATE INDEX IF NOT EXISTS orders_status_idx ON orders (status);
