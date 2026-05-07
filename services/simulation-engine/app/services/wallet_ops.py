"""
Wallet operations performed by the simulation engine after fills.

All functions accept an open SQLAlchemy AsyncSession and do NOT commit —
the caller is responsible for committing.
"""
import uuid
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.wallet import SimulationWallet


async def _get_or_create_wallet(
    db: AsyncSession, user_id: uuid.UUID, currency: str
) -> SimulationWallet:
    result = await db.execute(
        sa.select(SimulationWallet).where(
            SimulationWallet.user_id == user_id,
            SimulationWallet.currency == currency,
        )
    )
    wallet = result.scalar_one_or_none()
    if wallet is None:
        wallet = SimulationWallet(user_id=user_id, currency=currency)
        db.add(wallet)
        await db.flush()
    return wallet


async def apply_buy_fill(
    db: AsyncSession,
    user_id: uuid.UUID,
    base_currency: str,
    quote_currency: str,
    fill_price: Decimal,
    fill_quantity: Decimal,
    fee: Decimal,
) -> None:
    """
    For a BUY fill:
      - Deduct fill_quantity * fill_price + fee from quote locked_balance
      - Credit fill_quantity to base balance
    """
    cost = fill_quantity * fill_price + fee

    quote_wallet = await _get_or_create_wallet(db, user_id, quote_currency)
    quote_wallet.locked_balance = Decimal(str(quote_wallet.locked_balance)) - cost
    if quote_wallet.locked_balance < Decimal("0"):
        quote_wallet.locked_balance = Decimal("0")

    base_wallet = await _get_or_create_wallet(db, user_id, base_currency)
    base_wallet.balance = Decimal(str(base_wallet.balance)) + fill_quantity


async def apply_sell_fill(
    db: AsyncSession,
    user_id: uuid.UUID,
    base_currency: str,
    quote_currency: str,
    fill_price: Decimal,
    fill_quantity: Decimal,
    fee: Decimal,
) -> None:
    """
    For a SELL fill:
      - Deduct fill_quantity from base locked_balance
      - Credit fill_quantity * fill_price - fee to quote balance
    """
    proceeds = fill_quantity * fill_price - fee

    base_wallet = await _get_or_create_wallet(db, user_id, base_currency)
    base_wallet.locked_balance = Decimal(str(base_wallet.locked_balance)) - fill_quantity
    if base_wallet.locked_balance < Decimal("0"):
        base_wallet.locked_balance = Decimal("0")

    quote_wallet = await _get_or_create_wallet(db, user_id, quote_currency)
    quote_wallet.balance = Decimal(str(quote_wallet.balance)) + proceeds


async def release_locked_balance(
    db: AsyncSession,
    user_id: uuid.UUID,
    currency: str,
    amount: Decimal,
) -> None:
    """
    Return any over-reserved locked balance back to available balance.
    Called when a BUY market order fills at a price below the estimated reserve.
    """
    wallet = await _get_or_create_wallet(db, user_id, currency)
    release = min(amount, Decimal(str(wallet.locked_balance)))
    wallet.locked_balance = Decimal(str(wallet.locked_balance)) - release
    wallet.balance = Decimal(str(wallet.balance)) + release
