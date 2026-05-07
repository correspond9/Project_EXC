"""
Redis subscriber for the `orders.simulation` channel.

Receives order messages published by order-service and routes them to the
correct handler (market / limit / stop-loss).
"""
import asyncio
import json
import logging

import redis.asyncio as aioredis

from ..services.limit_handler import LimitOrderHandler
from ..services.market_handler import handle_market_order
from ..services.order_book_mirror import OrderBookMirror
from ..services.stop_loss_handler import StopLossHandler

log = logging.getLogger(__name__)

CHANNEL = "orders.simulation"


async def run_order_subscriber(
    redis_client: aioredis.Redis,
    mirror: OrderBookMirror,
    limit_handler: LimitOrderHandler,
    stop_loss_handler: StopLossHandler,
) -> None:
    """Infinite loop: subscribe to orders.simulation and dispatch each order."""
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(CHANNEL)
    log.info("order_subscriber: listening on '%s'", CHANNEL)

    async for raw in pubsub.listen():
        if raw["type"] != "message":
            continue
        try:
            msg: dict = json.loads(raw["data"])
        except Exception as exc:
            log.warning("order_subscriber: invalid JSON — %s", exc)
            continue

        order_type: str = msg.get("order_type", "MARKET").upper()
        exec_mode: str = msg.get("execution_mode", "SIMULATION").upper()

        if exec_mode != "SIMULATION":
            continue  # live orders handled elsewhere

        log.info(
            "order_subscriber: received %s %s order %s",
            order_type, msg.get("side"), msg.get("order_id"),
        )

        try:
            if order_type == "MARKET":
                asyncio.create_task(handle_market_order(msg, mirror, redis_client))

            elif order_type == "LIMIT":
                asyncio.create_task(limit_handler.register(msg, mirror, redis_client))

            elif order_type in ("STOP_LOSS", "TAKE_PROFIT"):
                asyncio.create_task(stop_loss_handler.register(msg, mirror, redis_client))

            else:
                log.warning("order_subscriber: unknown order_type '%s'", order_type)

        except Exception as exc:
            log.exception("order_subscriber: error dispatching order %s: %s", msg.get("order_id"), exc)
