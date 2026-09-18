## Performance Baseline

### Synchronous Processing — Before RabbitMQ

The synchronous order endpoint processes payment, restaurant notification,
inventory reservation, and customer notification sequentially inside the
HTTP request.

Test endpoint:

`POST /orders/sync`

Measured result:

- Order ID: `SYN-B6EB22FD`
- Status: `COMPLETED`
- API response time: **2084.2 ms (~2.08 seconds)**
- Processing flow: `PENDING → PAID → RESTAURANT_NOTIFIED → INVENTORY_RESERVED → COMPLETED`

This measurement is the **before** baseline. It will later be compared with
the asynchronous RabbitMQ implementation.
