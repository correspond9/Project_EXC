from datetime import datetime

import json

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import get_settings
from ..database import get_db
from ..dependencies.auth import get_current_user, require_role
from ..models.user import KYCDocument, KYCDocumentStatus, KYCStatus, User, UserRole
from ..redis_client import get_redis_pool
from ..schemas.user import (
    KYCDecisionRequest,
    KYCProviderWebhookRequest,
    KYCQueueItem,
    KYCStatusResponse,
    KYCSubmissionResponse,
    KYCSubmitRequest,
)
from ..services.auth_service import write_audit_log
from ..services.compliance_service import aml_screen_user

router = APIRouter(prefix="/kyc", tags=["KYC"])
settings = get_settings()


async def _publish_kyc_event(event: str, user_id: str, email: str, reason: str = "") -> None:
    """Fire-and-forget: publish a KYC lifecycle event to Redis for notification-service."""
    try:
        redis = await get_redis_pool()
        payload = json.dumps({"event": event, "user_id": user_id, "email": email, "reason": reason})
        channel = f"kyc.{event.lower().removeprefix('kyc_')}.{user_id}"
        await redis.publish(channel, payload)
    except Exception:
        pass  # Email notification failure must never block the main KYC action


@router.post("/submit", response_model=KYCSubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_kyc(
    body: KYCSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KYCSubmissionResponse:
    # Replace previous pending/rejected submission payload with the latest one.
    await db.execute(delete(KYCDocument).where(KYCDocument.user_id == current_user.id))

    for doc in body.documents:
        db.add(
            KYCDocument(
                user_id=current_user.id,
                document_type=doc.document_type,
                file_reference=doc.file_reference,
            )
        )

    current_user.kyc_status = KYCStatus.SUBMITTED

    await write_audit_log(
        db,
        action="KYC_SUBMITTED",
        user_id=str(current_user.id),
        entity_type="User",
        entity_id=str(current_user.id),
        extra_data={"submitted_documents": len(body.documents)},
    )

    await _publish_kyc_event("KYC_SUBMITTED", str(current_user.id), current_user.email)

    return KYCSubmissionResponse(
        message="KYC submission received.",
        kyc_status=current_user.kyc_status,
        submitted_documents=len(body.documents),
    )


@router.get("/status", response_model=KYCStatusResponse)
async def get_kyc_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KYCStatusResponse:
    result = await db.execute(select(User.kyc_status).where(User.id == current_user.id))
    kyc_status = result.scalar_one()
    return KYCStatusResponse(kyc_status=kyc_status)


@router.get("/admin/queue", response_model=list[KYCQueueItem])
async def get_kyc_queue(
    queue_status: KYCStatus = Query(default=KYCStatus.SUBMITTED, alias="status"),
    db: AsyncSession = Depends(get_db),
    _admin_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
) -> list[KYCQueueItem]:
    result = await db.execute(
        select(User)
        .options(selectinload(User.kyc_documents))
        .where(User.kyc_status == queue_status)
        .order_by(User.updated_at.desc())
    )
    users = result.scalars().all()

    queue_items: list[KYCQueueItem] = []
    for user in users:
        submitted_at: datetime | None = None
        if user.kyc_documents:
            submitted_at = max(doc.created_at for doc in user.kyc_documents)

        queue_items.append(
            KYCQueueItem(
                user_id=user.id,
                email=user.email,
                role=user.role,
                kyc_status=user.kyc_status,
                submitted_at=submitted_at,
                documents=user.kyc_documents,
            )
        )

    return queue_items


@router.post("/admin/{user_id}/approve", response_model=KYCStatusResponse)
async def approve_kyc(
    user_id: str,
    body: KYCDecisionRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
) -> KYCStatusResponse:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        aml_result = await aml_screen_user(
            user_id=str(user.id),
            email=user.email,
            stage="KYC_APPROVAL",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"AML screening failed: {exc}",
        ) from exc

    await write_audit_log(
        db,
        action="AML_CHECK_COMPLETED",
        user_id=str(admin_user.id),
        entity_type="User",
        entity_id=str(user.id),
        extra_data={
            "stage": "KYC_APPROVAL",
            "provider_name": aml_result.provider_name,
            "decision": aml_result.decision,
            "risk_score": aml_result.risk_score,
            "matched_entities": aml_result.matched_entities,
        },
    )

    if aml_result.requires_review:
        await write_audit_log(
            db,
            action="AML_REVIEW_REQUIRED",
            user_id=str(admin_user.id),
            entity_type="User",
            entity_id=str(user.id),
            extra_data={
                "stage": "KYC_APPROVAL",
                "decision": aml_result.decision,
                "risk_score": aml_result.risk_score,
                "reason": body.reason,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="AML review required before KYC can be approved.",
        )

    user.kyc_status = KYCStatus.APPROVED

    docs_result = await db.execute(select(KYCDocument).where(KYCDocument.user_id == user.id))
    for doc in docs_result.scalars().all():
        doc.verification_status = KYCDocumentStatus.VERIFIED

    await write_audit_log(
        db,
        action="KYC_APPROVED",
        user_id=str(admin_user.id),
        entity_type="User",
        entity_id=str(user.id),
        extra_data={"reason": body.reason},
    )

    await db.flush()
    await _publish_kyc_event("KYC_APPROVED", str(user.id), user.email)
    return KYCStatusResponse(kyc_status=user.kyc_status)


@router.post("/admin/{user_id}/reject", response_model=KYCStatusResponse)
async def reject_kyc(
    user_id: str,
    body: KYCDecisionRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
) -> KYCStatusResponse:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.kyc_status = KYCStatus.REJECTED

    docs_result = await db.execute(select(KYCDocument).where(KYCDocument.user_id == user.id))
    for doc in docs_result.scalars().all():
        doc.verification_status = KYCDocumentStatus.REJECTED

    await write_audit_log(
        db,
        action="KYC_REJECTED",
        user_id=str(admin_user.id),
        entity_type="User",
        entity_id=str(user.id),
        extra_data={"reason": body.reason},
    )

    await db.flush()
    await _publish_kyc_event("KYC_REJECTED", str(user.id), user.email, reason=body.reason or "")
    return KYCStatusResponse(kyc_status=user.kyc_status)


@router.post("/webhook/provider", response_model=KYCStatusResponse)
async def provider_webhook(
    body: KYCProviderWebhookRequest,
    x_kyc_webhook_secret: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> KYCStatusResponse:
    if settings.KYC_WEBHOOK_SECRET and x_kyc_webhook_secret != settings.KYC_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    result = await db.execute(select(User).where(User.id == body.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.kyc_status = body.status

    await write_audit_log(
        db,
        action="KYC_PROVIDER_UPDATED",
        user_id=str(user.id),
        entity_type="User",
        entity_id=str(user.id),
        extra_data={
            "provider_reference": body.provider_reference,
            "status": body.status.value,
            "reason": body.reason,
        },
    )

    await db.flush()

    # Notify user via notification-service when provider delivers a final decision
    if body.status == KYCStatus.APPROVED:
        await _publish_kyc_event("KYC_APPROVED", str(user.id), user.email)
    elif body.status == KYCStatus.REJECTED:
        await _publish_kyc_event("KYC_REJECTED", str(user.id), user.email, reason=body.reason or "")

    return KYCStatusResponse(kyc_status=user.kyc_status)
