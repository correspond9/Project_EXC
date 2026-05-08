"""
Admin-service — Options contracts management.
Allows admins to create, view, and toggle options contracts.
These write to the options_contracts table owned by order-service (shared DB).
"""
import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies.auth import require_admin

router = APIRouter(prefix="/api/admin/options", tags=["Admin — Options Contracts"])

VALID_OPTION_TYPES = ("CALL", "PUT")


class ContractCreate(BaseModel):
    underlying_symbol: str
    option_type: str
    strike_price: Decimal
    expiry_date: date
    implied_volatility: Decimal = Decimal("0.60")


class ContractOut(BaseModel):
    id: str
    underlying_symbol: str
    option_type: str
    strike_price: str
    expiry_date: str
    implied_volatility: str
    is_active: bool


@router.post("/contracts", response_model=ContractOut, status_code=201)
async def create_contract(
    body: ContractCreate,
    _admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new options contract that users can trade."""
    symbol = body.underlying_symbol.upper()
    opt_type = body.option_type.upper()

    if opt_type not in VALID_OPTION_TYPES:
        raise HTTPException(status_code=400, detail="option_type must be CALL or PUT")
    if body.strike_price <= 0:
        raise HTTPException(status_code=400, detail="strike_price must be > 0")
    if body.expiry_date <= date.today():
        raise HTTPException(status_code=400, detail="expiry_date must be in the future")
    if not (Decimal("0.01") <= body.implied_volatility <= Decimal("5.0")):
        raise HTTPException(status_code=400, detail="implied_volatility must be between 0.01 and 5.0")

    new_id = uuid.uuid4()
    await db.execute(
        text("""
            INSERT INTO options_contracts
                (id, underlying_symbol, option_type, strike_price, expiry_date, implied_volatility, is_active, created_at)
            VALUES
                (:id, :sym, :otype::option_type, :strike, :expiry, :iv, true, now())
        """),
        {
            "id": new_id,
            "sym": symbol,
            "otype": opt_type,
            "strike": body.strike_price,
            "expiry": body.expiry_date,
            "iv": body.implied_volatility,
        },
    )
    await db.commit()

    return ContractOut(
        id=str(new_id),
        underlying_symbol=symbol,
        option_type=opt_type,
        strike_price=str(body.strike_price),
        expiry_date=str(body.expiry_date),
        implied_volatility=str(body.implied_volatility),
        is_active=True,
    )


@router.get("/contracts", response_model=list[ContractOut])
async def list_contracts(
    _admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all options contracts (active and inactive)."""
    result = await db.execute(
        text("""
            SELECT id, underlying_symbol, option_type, strike_price, expiry_date,
                   implied_volatility, is_active
            FROM options_contracts
            ORDER BY expiry_date ASC, underlying_symbol ASC
        """)
    )
    rows = result.mappings().all()
    return [
        ContractOut(
            id=str(r["id"]),
            underlying_symbol=r["underlying_symbol"],
            option_type=r["option_type"],
            strike_price=str(r["strike_price"]),
            expiry_date=str(r["expiry_date"]),
            implied_volatility=str(r["implied_volatility"]),
            is_active=r["is_active"],
        )
        for r in rows
    ]


@router.patch("/contracts/{contract_id}/toggle", response_model=ContractOut)
async def toggle_contract(
    contract_id: uuid.UUID,
    _admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Enable or disable an options contract."""
    result = await db.execute(
        text("SELECT * FROM options_contracts WHERE id = :id"),
        {"id": contract_id},
    )
    row = result.mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Contract not found")

    new_active = not row["is_active"]
    await db.execute(
        text("UPDATE options_contracts SET is_active = :active WHERE id = :id"),
        {"active": new_active, "id": contract_id},
    )
    await db.commit()

    return ContractOut(
        id=str(row["id"]),
        underlying_symbol=row["underlying_symbol"],
        option_type=str(row["option_type"]),
        strike_price=str(row["strike_price"]),
        expiry_date=str(row["expiry_date"]),
        implied_volatility=str(row["implied_volatility"]),
        is_active=new_active,
    )
