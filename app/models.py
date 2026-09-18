"""Request and response shapes.

Validation at the edge is part of the story: a malformed order is rejected
with a 422 before anything is published, so nothing invalid ever reaches a
queue where a worker would choke on it three times and dead-letter it.
"""
from pydantic import BaseModel, Field


class OrderIn(BaseModel):
    customer: str = Field(..., min_length=1, max_length=80, examples=["Aung"])
    restaurant: str = Field(..., min_length=1, max_length=120,
                            examples=["Shan Noodle House"])
    items: list[str] = Field(..., min_length=1, max_length=50,
                             examples=[["Shan noodles", "Iced tea"]])
    total: float = Field(..., gt=0, le=100_000, examples=[180.0])


class OrderAccepted(BaseModel):
    order_id: str
    status: str
    api_time_ms: float
    track: str


class OrderCompleted(BaseModel):
    order_id: str
    status: str
    api_time_ms: float


class Health(BaseModel):
    ok: bool
    broker: bool
    database: bool
    service: str
