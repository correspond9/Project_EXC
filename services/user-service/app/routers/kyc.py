from fastapi import APIRouter, Depends, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models.user import KYCDocument, KYCStatus, User
from ..schemas.user import KYCStatusResponse, KYCSubmissionResponse, KYCSubmitRequest
from ..services.auth_service import write_audit_log

router = APIRouter(prefix="/kyc", tags=["KYC"])


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
