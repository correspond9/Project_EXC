"""Compliance and fee reporting endpoints for admin.

Routes:
  GET  /api/admin/fees/ledger                  — fee revenue with filters
  GET  /api/admin/compliance/report            — CSV export of deposits/withdrawals/trades
  POST /api/admin/compliance/sar/{user_id}     — flag user for SAR review
  GET  /api/admin/compliance/sar               — list SAR-flagged users
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import date, datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies.auth import require_admin, require_super_admin

router = APIRouter(prefix="/api/admin", tags=["Compliance"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class SARFlagRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=1000)
    reference_tx_id: Optional[str] = Field(default=None, max_length=100)


# ── Fee Ledger ────────────────────────────────────────────────────────────────

@router.get("/fees/ledger")
async def fee_ledger(
    admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Optional[uuid.UUID] = Query(default=None),
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
):
    """List fee ledger entries with optional user/date filters. Paginated."""
    conditions = ["1=1"]
    params: dict = {}
    if user_id:
        conditions.append("user_id = :user_id")
        params["user_id"] = str(user_id)
    if from_date:
        conditions.append("created_at >= :from_date")
        params["from_date"] = datetime(from_date.year, from_date.month, from_date.day, tzinfo=timezone.utc)
    if to_date:
        conditions.append("created_at < :to_date_excl")
        params["to_date_excl"] = datetime(to_date.year, to_date.month, to_date.day + 1 if to_date.day < 28 else to_date.day, tzinfo=timezone.utc)

    where = " AND ".join(conditions)
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    rows = await db.execute(
        text(
            f"SELECT id, user_id, order_id, currency, fee_amount, fee_rate, "
            f"fill_value, fill_quantity, fill_price, created_at "
            f"FROM fee_ledger WHERE {where} "
            f"ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        ),
        params,
    )

    count_row = await db.execute(
        text(f"SELECT COUNT(*) FROM fee_ledger WHERE {where}"),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    )
    total = count_row.scalar_one()

    entries = [
        {
            "id": str(r.id),
            "user_id": str(r.user_id),
            "order_id": str(r.order_id) if r.order_id else None,
            "currency": r.currency,
            "fee_amount": float(r.fee_amount),
            "fee_rate": float(r.fee_rate),
            "fill_value": float(r.fill_value),
            "fill_quantity": float(r.fill_quantity),
            "fill_price": float(r.fill_price),
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]

    return {"total": total, "page": page, "page_size": page_size, "entries": entries}


# ── Compliance CSV Export ─────────────────────────────────────────────────────

@router.get("/compliance/report")
async def compliance_report(
    admin_id: Annotated[uuid.UUID, Depends(require_super_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    from_date: date = Query(...),
    to_date: date = Query(...),
):
    """Export all deposits, withdrawals, and LIVE trades as CSV (streaming)."""
    from_dt = datetime(from_date.year, from_date.month, from_date.day, tzinfo=timezone.utc)
    to_dt = datetime(to_date.year, to_date.month, to_date.day + 1 if to_date.day < 28 else to_date.day, tzinfo=timezone.utc)
    params = {"from_dt": from_dt, "to_dt": to_dt}

    # Deposits and Withdrawals from balance_ledger
    ledger_rows = await db.execute(
        text(
            "SELECT bl.created_at, u.email, bl.currency, bl.amount, bl.balance_after, "
            "bl.tx_type, bl.reference_id, bl.note "
            "FROM balance_ledger bl "
            "LEFT JOIN users u ON u.id = bl.user_id "
            "WHERE bl.created_at >= :from_dt AND bl.created_at < :to_dt "
            "ORDER BY bl.created_at ASC"
        ),
        params,
    )

    # LIVE trade fills
    fill_rows = await db.execute(
        text(
            "SELECT f.filled_at, u.email, o.symbol, o.side, f.fill_price, "
            "f.fill_quantity, f.fee, f.fee_currency, o.market_type "
            "FROM order_fills f "
            "JOIN orders o ON o.id = f.order_id "
            "LEFT JOIN users u ON u.id = o.user_id "
            "WHERE f.execution_mode = 'LIVE' "
            "AND f.filled_at >= :from_dt AND f.filled_at < :to_dt "
            "ORDER BY f.filled_at ASC"
        ),
        params,
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # Section: Balance Ledger
    writer.writerow(["=== Balance Ledger ==="])
    writer.writerow(["Date", "User Email", "Currency", "Amount", "Balance After", "Type", "Reference", "Note"])
    for r in ledger_rows:
        writer.writerow([
            r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            r.email or "",
            r.currency,
            float(r.amount),
            float(r.balance_after),
            r.tx_type,
            r.reference_id or "",
            r.note or "",
        ])

    writer.writerow([])
    # Section: Trade Fills
    writer.writerow(["=== LIVE Trade Fills ==="])
    writer.writerow(["Date", "User Email", "Symbol", "Side", "Fill Price", "Fill Qty", "Fee", "Fee Currency", "Market"])
    for r in fill_rows:
        writer.writerow([
            r.filled_at.strftime("%Y-%m-%d %H:%M:%S"),
            r.email or "",
            r.symbol,
            r.side,
            float(r.fill_price),
            float(r.fill_quantity),
            float(r.fee),
            r.fee_currency,
            r.market_type,
        ])

    output.seek(0)
    filename = f"compliance_{from_date}_{to_date}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── SAR Flagging ──────────────────────────────────────────────────────────────

@router.post("/compliance/sar/{user_id}", status_code=201)
async def flag_sar(
    user_id: uuid.UUID,
    body: SARFlagRequest,
    admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Flag a user for Suspicious Activity Report (SAR) review."""
    # Verify user exists
    row = await db.execute(text("SELECT id FROM users WHERE id = :uid"), {"uid": str(user_id)})
    if not row.fetchone():
        raise HTTPException(status_code=404, detail="User not found")

    await db.execute(
        text(
            "INSERT INTO sar_flags (id, user_id, flagged_by, reason, reference_tx_id) "
            "VALUES (gen_random_uuid(), :uid, :admin, :reason, :ref)"
        ),
        {
            "uid": str(user_id),
            "admin": str(admin_id),
            "reason": body.reason,
            "ref": body.reference_tx_id,
        },
    )
    await db.commit()
    return {"status": "flagged", "user_id": str(user_id)}


@router.get("/compliance/sar")
async def list_sar_flags(
    admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Optional[uuid.UUID] = Query(default=None),
):
    """List SAR-flagged users."""
    if user_id:
        rows = await db.execute(
            text(
                "SELECT s.id, s.user_id, u.email, s.reason, s.reference_tx_id, s.created_at "
                "FROM sar_flags s LEFT JOIN users u ON u.id = s.user_id "
                "WHERE s.user_id = :uid ORDER BY s.created_at DESC"
            ),
            {"uid": str(user_id)},
        )
    else:
        rows = await db.execute(
            text(
                "SELECT s.id, s.user_id, u.email, s.reason, s.reference_tx_id, s.created_at "
                "FROM sar_flags s LEFT JOIN users u ON u.id = s.user_id "
                "ORDER BY s.created_at DESC LIMIT 200"
            )
        )
    return [
        {
            "id": str(r.id),
            "user_id": str(r.user_id),
            "email": r.email,
            "reason": r.reason,
            "reference_tx_id": r.reference_tx_id,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
