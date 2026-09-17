"""One logging setup for every process.

Two jobs:
  * make OUR lines readable on a projector
  * silence pika, which logs every socket event at INFO and would otherwise
    bury the demo output the audience is supposed to read
"""
import logging

from app import config

_CONFIGURED = False


def setup(name: str | None = None) -> logging.Logger:
    global _CONFIGURED
    if not _CONFIGURED:
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
            format="%(asctime)s  %(name)-12s  %(message)s",
            datefmt="%H:%M:%S",
        )
        logging.getLogger("pika").setLevel(logging.WARNING)
        logging.getLogger("psycopg").setLevel(logging.WARNING)
        logging.getLogger("psycopg.pool").setLevel(logging.WARNING)
        _CONFIGURED = True
    return logging.getLogger(name or config.SERVICE_NAME)