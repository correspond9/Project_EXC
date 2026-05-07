from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models.user import User, UserProfile
from ..schemas.user import UpdateProfileRequest, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


# ── GET /api/users/me ─────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    result = await db.execute(
        select(User)
        .options(selectinload(User.profile))
        .where(User.id == current_user.id)
    )
    return result.scalar_one()


# ── PUT /api/users/me ─────────────────────────────────────────────────────────

@router.put("/me", response_model=UserResponse)
async def update_me(
    body: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    result = await db.execute(
        select(User)
        .options(selectinload(User.profile))
        .where(User.id == current_user.id)
    )
    user = result.scalar_one()

    # Create profile if it doesn't exist (defensive — register always creates it)
    if user.profile is None:
        user.profile = UserProfile(user_id=user.id)
        db.add(user.profile)

    update_data = body.model_dump(exclude_unset=True)

    # language_preference lives on the User table, not UserProfile
    if "language_preference" in update_data:
        user.language_preference = update_data.pop("language_preference")

    for field, value in update_data.items():
        setattr(user.profile, field, value)

    await db.flush()
    return user
