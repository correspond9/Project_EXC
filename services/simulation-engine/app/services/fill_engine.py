"""
Core fill engine: depth-walk algorithm.

Takes an order book snapshot and consumes levels to produce a list of FillRecord
objects.  Does NOT touch the database or Redis — pure computation.
"""
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class FillRecord:
    fill_price: Decimal
    fill_quantity: Decimal
    fee: Decimal          # in quote currency (USDT)
    fee_currency: str


def depth_walk(
    book: dict,
    side: str,              # "BUY" or "SELL"
    remaining_qty: Decimal,
    fee_rate: Decimal,
    limit_price: Decimal | None = None,
) -> tuple[list[FillRecord], Decimal]:
    """
    Walk the order book depth and generate fill records.

    For BUY  orders: consume asks[] lowest-first.
    For SELL orders: consume bids[] highest-first.

    Args:
        book:          Snapshot {"bids": [["price","qty"],...], "asks": [...]}
        side:          "BUY" or "SELL"
        remaining_qty: How much quantity remains to be filled (Decimal).
        fee_rate:      e.g. Decimal("0.001") for 0.1 %.
        limit_price:   For LIMIT orders — refuse fills beyond this price.

    Returns:
        (fills, leftover_qty)
        fills        — list of FillRecord objects produced this walk.
        leftover_qty — quantity still unfilled (0 = fully filled).
    """
    levels = book.get("asks" if side == "BUY" else "bids", [])
    fills: list[FillRecord] = []

    for level in levels:
        if remaining_qty <= Decimal("0"):
            break

        level_price = Decimal(str(level[0]))
        level_qty = Decimal(str(level[1]))

        # Limit-price gate
        if limit_price is not None:
            if side == "BUY" and level_price > limit_price:
                break
            if side == "SELL" and level_price < limit_price:
                break

        fill_qty = min(remaining_qty, level_qty)
        fee = fill_qty * level_price * fee_rate

        fills.append(
            FillRecord(
                fill_price=level_price,
                fill_quantity=fill_qty,
                fee=fee,
                fee_currency="USDT",
            )
        )
        remaining_qty -= fill_qty

    return fills, remaining_qty
