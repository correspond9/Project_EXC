"""
Options trading router — list contracts, get live pricing, buy options.

Black-Scholes pricing uses the Python standard library only (math + statistics).
"""
import math
import statistics
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_DOWN
from typing import Annotated

import redis.asyncio as aioredis
import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..database import AsyncSessionLocal
from ..dependencies.auth import get_current_user_id
from ..models.options import OptionType, OptionsContract, OptionsPosition, OptionsPositionStatus
from ..redis_client import get_redis_pool

router = APIRouter(prefix="/api/options", tags=["options"])

RISK_FREE_RATE = 0.05          # 5 % annualised — used in Black-Scholes
QUANTISE = Decimal("0.00000001")


# ──────────────────────────────────────────────────────────────────────────────
# Black-Scholes helpers
# ──────────────────────────────────────────────────────────────────────────────

def _norm_cdf(x: float) -> float:
    """Standard normal CDF using Python stdlib."""
    return statistics.NormalDist(0, 1).cdf(x)


def black_scholes(
    S: float,      # current underlying price
    K: float,      # strike price
    T: float,      # time to expiry in years (> 0)
    r: float,      # risk-free rate
    sigma: float,  # implied volatility
    option_type: OptionType,
) -> dict:
    """
    Returns dict with keys: premium, delta, gamma, theta
    Returns zeros if T <= 0 (expired / at expiry).
    """
    if T <= 0 or S <= 0 or K <= 0 or sigma <= 0:
        intrinsic = max(S - K, 0) if option_type == OptionType.CALL else max(K - S, 0)
        return {"premium": intrinsic, "delta": 0.0, "gamma": 0.0, "theta": 0.0}

    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    nd1 = _norm_cdf(d1)
    nd2 = _norm_cdf(d2)
    nd1_neg = _norm_cdf(-d1)
    nd2_neg = _norm_cdf(-d2)
    n_d1_pdf = math.exp(-0.5 * d1 ** 2) / math.sqrt(2 * math.pi)  # φ(d1)

    disc = math.exp(-r * T)

    if option_type == OptionType.CALL:
        premium = S * nd1 - K * disc * nd2
        delta = nd1
        theta = (
            -(S * n_d1_pdf * sigma) / (2 * math.sqrt(T))
            - r * K * disc * nd2
        ) / 365
    else:  # PUT
        premium = K * disc * nd2_neg - S * nd1_neg
        delta = nd1 - 1
        theta = (
            -(S * n_d1_pdf * sigma) / (2 * math.sqrt(T))
            + r * K * disc * nd2_neg
        ) / 365

    gamma = n_d1_pdf / (S * sigma * math.sqrt(T))

    return {
        "premium": max(premium, 0.0),
        "delta": delta,
        "gamma": gamma,
        "theta": theta,
    }


def _years_to_expiry(expiry: date) -> float:
    today = datetime.now(timezone.utc).date()
    delta = (expiry - today).days
    return max(delta / 365.0, 0.0)


async def _get_ticker_price(redis: aioredis.Redis, symbol: str) -> Decimal | None:
    """Fetch latest close price from Redis ticker hash."""
    raw = await redis.hget(f"ticker:{symbol.upper()}", "c")
    if raw is None:
        return None
    try:
        return Decimal(raw.decode() if isinstance(raw, bytes) else raw)
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/contracts")
async def list_contracts(
    underlying: str | None = Query(None, description="Filter by symbol e.g. BTCUSDT"),
):
    """List all active option contracts."""
    async with AsyncSessionLocal() as db:
        q = sa.select(OptionsContract).where(OptionsContract.is_active == True)  # noqa
        if underlying:
            q = q.where(
                OptionsContract.underlying_symbol == underlying.upper()
            )
        q = q.order_by(OptionsContract.expiry_date, OptionsContract.strike_price)
        rows = (await db.execute(q)).scalars().all()

    return [
        {
            "id": str(c.id),
            "underlying_symbol": c.underlying_symbol,
            "option_type": c.option_type.value,
            "strike_price": str(c.strike_price),
            "expiry_date": c.expiry_date.isoformat(),
            "implied_volatility": str(c.implied_volatility),
        }
        for c in rows
    ]


@router.get("/price")
async def get_option_price(
    contract_id: uuid.UUID,
    redis: Annotated[aioredis.Redis, Depends(get_redis_pool)],
):
    """Return Black-Scholes theoretical price + Greeks for a contract."""
    async with AsyncSessionLocal() as db:
        contract = await db.get(OptionsContract, contract_id)
    if contract is None or not contract.is_active:
        raise HTTPException(status_code=404, detail="Contract not found or inactive")

    spot = await _get_ticker_price(redis, contract.underlying_symbol)
    if spot is None:
        raise HTTPException(status_code=503, detail="Underlying price unavailable")

    T = _years_to_expiry(contract.expiry_date)
    result = black_scholes(
        S=float(spot),
        K=float(contract.strike_price),
        T=T,
        r=RISK_FREE_RATE,
        sigma=float(contract.implied_volatility),
        option_type=contract.option_type,
    )

    return {
        "contract_id": str(contract_id),
        "underlying_price": str(spot),
        "strike_price": str(contract.strike_price),
        "expiry_date": contract.expiry_date.isoformat(),
        "option_type": contract.option_type.value,
        "premium_per_unit": round(result["premium"], 8),
        "delta": round(result["delta"], 6),
        "gamma": round(result["gamma"], 8),
        "theta_per_day": round(result["theta"], 8),
    }


class BuyOptionRequest(BaseModel):
    contract_id: uuid.UUID
    quantity: Decimal = Field(gt=0, description="Number of contracts (1 contract = 1 unit of underlying)")


@router.post("/buy", status_code=status.HTTP_201_CREATED)
async def buy_option(
    body: BuyOptionRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    redis: Annotated[aioredis.Redis, Depends(get_redis_pool)],
):
    """
    Buy an options contract at Black-Scholes theoretical premium.

    Deducts total_cost = premium × quantity from the user's USDT simulation wallet.
    Creates an OptionsPosition record.
    """
    # Load contract
    async with AsyncSessionLocal() as db:
        contract = await db.get(OptionsContract, body.contract_id)
    if contract is None or not contract.is_active:
        raise HTTPException(status_code=404, detail="Contract not found or inactive")
    if contract.expiry_date <= datetime.now(timezone.utc).date():
        raise HTTPException(status_code=400, detail="Contract has already expired")

    # Get current underlying price for premium calculation
    spot = await _get_ticker_price(redis, contract.underlying_symbol)
    if spot is None:
        raise HTTPException(
            status_code=503,
            detail="Underlying price unavailable. Please try again.",
        )

    T = _years_to_expiry(contract.expiry_date)
    bs = black_scholes(
        S=float(spot),
        K=float(contract.strike_price),
        T=T,
        r=RISK_FREE_RATE,
        sigma=float(contract.implied_volatility),
        option_type=contract.option_type,
    )
    premium_per_unit = Decimal(str(round(bs["premium"], 8)))
    total_cost = (premium_per_unit * body.quantity).quantize(QUANTISE, rounding=ROUND_DOWN)

    if total_cost <= 0:
        raise HTTPException(status_code=400, detail="Option premium is zero — contract likely at expiry")

    # Deduct from simulation wallet
    async with AsyncSessionLocal() as db:
        wallet_q = sa.text(
            """
            UPDATE simulation_wallets
               SET balance = balance - :cost,
                   updated_at = now()
             WHERE user_id = :uid
               AND asset = 'USDT'
               AND balance >= :cost
            RETURNING id
            """
        )
        result = await db.execute(wallet_q, {"cost": total_cost, "uid": user_id})
        row = result.fetchone()
        if row is None:
            raise HTTPException(
                status_code=400,
                detail="Insufficient USDT balance to purchase this option",
            )

        # Create options position
        pos = OptionsPosition(
            user_id=user_id,
            contract_id=contract.id,
            underlying_symbol=contract.underlying_symbol,
            option_type=contract.option_type,
            strike_price=contract.strike_price,
            expiry_date=contract.expiry_date,
            quantity=body.quantity,
            premium_paid=total_cost,
            status=OptionsPositionStatus.OPEN,
        )
        db.add(pos)
        await db.commit()
        await db.refresh(pos)

    # Publish fill event so notification-service records it
    fill_payload = {
        "type": "fill",
        "user_id": str(user_id),
        "symbol": f"{contract.underlying_symbol}-{contract.option_type.value}-{contract.strike_price}-{contract.expiry_date}",
        "side": "BUY",
        "quantity": str(body.quantity),
        "price": str(premium_per_unit),
        "market_type": "OPTIONS",
    }
    await redis.publish(f"fills.{user_id}", __import__("json").dumps(fill_payload))

    return {
        "options_position_id": str(pos.id),
        "contract_id": str(contract.id),
        "underlying_symbol": contract.underlying_symbol,
        "option_type": contract.option_type.value,
        "strike_price": str(contract.strike_price),
        "expiry_date": contract.expiry_date.isoformat(),
        "quantity": str(body.quantity),
        "premium_per_unit": str(premium_per_unit),
        "total_cost": str(total_cost),
        "underlying_price_at_purchase": str(spot),
    }


@router.get("/positions")
async def my_options_positions(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    status_filter: str | None = Query(None, alias="status"),
):
    """Return the authenticated user's options positions."""
    async with AsyncSessionLocal() as db:
        q = sa.select(OptionsPosition).where(OptionsPosition.user_id == user_id)
        if status_filter:
            try:
                sf = OptionsPositionStatus(status_filter.upper())
                q = q.where(OptionsPosition.status == sf)
            except ValueError:
                pass
        q = q.order_by(OptionsPosition.created_at.desc())
        rows = (await db.execute(q)).scalars().all()

    return [
        {
            "id": str(p.id),
            "underlying_symbol": p.underlying_symbol,
            "option_type": p.option_type.value,
            "strike_price": str(p.strike_price),
            "expiry_date": p.expiry_date.isoformat(),
            "quantity": str(p.quantity),
            "premium_paid": str(p.premium_paid),
            "status": p.status.value,
            "payout": str(p.payout) if p.payout is not None else None,
            "settlement_price": str(p.settlement_price) if p.settlement_price is not None else None,
            "settled_at": p.settled_at.isoformat() if p.settled_at else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in rows
    ]
