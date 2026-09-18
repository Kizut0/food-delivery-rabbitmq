import time
import uuid

from fastapi import FastAPI

from app import config, store
from app.models import OrderCompleted, OrderIn

app = FastAPI(title="Food Delivery API")


@app.post("/orders/sync", response_model=OrderCompleted)
def create_order_sync(order: OrderIn):
    started = time.perf_counter()
    order_id = f"SYN-{uuid.uuid4().hex[:8].upper()}"

    store.create_order(
        order_id,
        order.customer,
        order.restaurant,
        order.items,
        order.total,
        status="PENDING",
    )

    time.sleep(config.T_PAYMENT)
    store.set_status(order_id, "PAID", "charged inline", "sync")

    time.sleep(config.T_RESTAURANT)
    store.add_event(order_id, "RESTAURANT_NOTIFIED", "inline", "sync")

    time.sleep(config.T_INVENTORY)
    store.add_event(order_id, "INVENTORY_RESERVED", "inline", "sync")

    time.sleep(config.T_NOTIFICATION)
    store.set_status(order_id, "COMPLETED", "notified inline", "sync")

    return OrderCompleted(
        order_id=order_id,
        status="COMPLETED",
        api_time_ms=round((time.perf_counter() - started) * 1000, 1),
    )