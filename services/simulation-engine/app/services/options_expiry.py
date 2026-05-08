"""
Options Expiry Worker — settlement of expired options contracts.

Runs as a background task in simulation-engine. Every 60 seconds:
  1. Finds all OPEN options_positions where expiry_date <= today (UTC).
  2. Looks up settlement price (current underlying price from Redis ticker).
  3. For CALL: if settlement_price > strike → payout = (settlement - strike) × qty
  4. For PUT:  if settlement_price < strike → payout = (strike - settlement) × qty
  5. Credits payout to user's simulation wallet.
  6. Marks position EXPIRED_ITM or EXPIRED_OTM.
  7. Publishes fill event to fills.{user_id} so notification-service picks it up.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal

import redis.asyncio as aioredis
import sqlalchemy as sa

from ..database import AsyncSessionLocal

log = logging.getLogger(__name__)

SETTLE_INTERVAL_SECONDS = 60


class OptionsExpiryWorker:
    """Background worker that settles expired options positions."""

    async def start(self, redis_client: aioredis.Redis) -> None:
        log.info("OptionsExpiryWorker: started")
        while True:
            try:
                await self._settle_expired(redis_client)
            except asyncio.CancelledError:
                log.info("OptionsExpiryWorker: cancelled")
                return
            except Exception as exc:
                log.exception("OptionsExpiryWorker error: %s", exc)
            await asyncio.sleep(SETTLE_INTERVAL_SECONDS)

    async def _settle_expired(self, redis_client: aioredis.Redis) -> None:
        today = datetime.now(timezone.utc).date()

        async with AsyncSessionLocal() as db:
            # Fetch all open positions that have expired
            q = sa.text(
                """
                SELECT id, user_id, underlying_symbol, option_type,
                       strike_price, quantity
                  FROM options_positions
                 WHERE status = 'OPEN'
                   AND expiry_date <= :today
                """
            )
            rows = (await db.execute(q, {"today": today})).fetchall()

        if not rows:
            return

        log.info("OptionsExpiryWorker: settling %d expired position(s)", len(rows))

        for row in rows:
            pos_id = row.id
            user_id = row.user_id
            symbol = row.underlying_symbol
            opt_type = row.option_type
            strike = Decimal(str(row.strike_price))
            quantity = Decimal(str(row.quantity))

            # Get settlement price from Redis
            settlement_price = await self._get_price(redis_client, symbol)
            if settlement_price is None:
                log.warning(
                    "OptionsExpiryWorker: no price for %s, skipping position %s",
                    symbol, pos_id,
                )
                continue

            # Calculate payout
            if opt_type == "CALL":
                intrinsic = max(settlement_price - strike, Decimal("0"))
            else:  # PUT
                intrinsic = max(strike - settlement_price, Decimal("0"))

            payout = (intrinsic * quantity).quantize(Decimal("0.00000001"))
            new_status = "EXPIRED_ITM" if payout > 0 else "EXPIRED_OTM"

            async with AsyncSessionLocal() as db:
                # Update position
                await db.execute(
                    sa.text(
                        """
                        UPDATE options_positions
                           SET status           = :status,
                               settlement_price = :price,
                               payout           = :payout,
                               settled_at       = now()
                         WHERE id = :pos_id
                        """
                    ),
                    {
                        "status": new_status,
                        "price": settlement_price,
                        "payout": payout,
                        "pos_id": pos_id,
                    },
                )

                # Credit payout if in-the-money
                if payout > 0:
                    await db.execute(
                        sa.text(
                            """
                            UPDATE simulation_wallets
                               SET balance    = balance + :payout,
                                   updated_at = now()
                             WHERE user_id = :uid
                               AND asset   = 'USDT'
                            """
                        ),
                        {"payout": payout, "uid": user_id},
                    )

                await db.commit()

            log.info(
                "OptionsExpiryWorker: settled %s pos=%s status=%s payout=%s",
                symbol, pos_id, new_status, payout,
            )

            # Publish fill event for notification-service
            fill_event = {
                "type": "fill",
                "user_id": str(user_id),
                "symbol": f"{symbol}-{opt_type}-{strike}-SETTLED",
                "side": "EXPIRY",
                "quantity": str(quantity),
                "price": str(settlement_price),
                "market_type": "OPTIONS",
                "payout": str(payout),
                "options_status": new_status,
            }
            await redis_client.publish(f"fills.{user_id}", json.dumps(fill_event))

    async def _get_price(
        self, redis_client: aioredis.Redis, symbol: str
    ) -> Decimal | None:
        raw = await redis_client.hget(f"ticker:{symbol.upper()}", "c")
        if raw is None:
            return None
        try:
            return Decimal(raw.decode() if isinstance(raw, bytes) else raw)
        except Exception:
            return None
