import uuid
from typing import Annotated

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status

from ..database import get_db, AsyncSessionLocal
from ..dependencies import get_current_user_id
from ..models.notification import Notification

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    limit: int = 30,
    unread_only: bool = False,
):
    """Return recent notifications for the authenticated user."""
    async with AsyncSessionLocal() as db:
        q = sa.select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            q = q.where(Notification.is_read == False)  # noqa: E712
        q = q.order_by(Notification.created_at.desc()).limit(limit)
        result = await db.execute(q)
        rows = result.scalars().all()

    return [
        {
            "id": str(n.id),
            "type": n.type.value,
            "title": n.title,
            "body": n.body,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in rows
    ]


@router.put("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(
    notification_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            sa.select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notif = result.scalar_one_or_none()
        if notif is None:
            raise HTTPException(status_code=404, detail="Notification not found")
        notif.is_read = True
        await db.commit()


@router.put("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
):
    async with AsyncSessionLocal() as db:
        await db.execute(
            sa.update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
            .values(is_read=True)
        )
        await db.commit()
