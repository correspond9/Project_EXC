from typing import Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models.user import User, UserProfile
from ..redis_client import get_redis
from ..schemas.user import LoginRequest, RefreshResponse, RegisterRequest, TokenResponse
from ..services.auth_service import (
    create_access_token,
    create_refresh_token,
    get_user_id_from_refresh_token,
    hash_password,
    revoke_refresh_token,
    verify_password,
    write_audit_log,
)

settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Authentication"])

_REFRESH_COOKIE = "refresh_token"
_COOKIE_KWARGS = {
    "httponly": True,
    "secure": True,
    "samesite": "strict",
    "max_age": settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    "path": "/api/auth",
}


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ── POST /api/auth/register ───────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(User).where(User.email == body.email.lower())
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
    )
    db.add(user)
    await db.flush()  # Assigns user.id before creating dependent records

    profile = UserProfile(user_id=user.id)
    db.add(profile)

    await write_audit_log(
        db,
        action="USER_REGISTERED",
        user_id=str(user.id),
        entity_type="User",
        entity_id=str(user.id),
        ip_address=_client_ip(request),
    )

    return {"message": "Account created successfully. You can now log in."}


# ── POST /api/auth/login ──────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> TokenResponse:
    result = await db.execute(
        select(User).where(User.email == body.email.lower())
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        await write_audit_log(
            db,
            action="LOGIN_FAILED",
            ip_address=_client_ip(request),
            extra_data={"email": body.email.lower()},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact support.",
        )

    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token = await create_refresh_token(str(user.id), redis)

    response.set_cookie(key=_REFRESH_COOKIE, value=refresh_token, **_COOKIE_KWARGS)

    await write_audit_log(
        db,
        action="LOGIN_SUCCESS",
        user_id=str(user.id),
        entity_type="User",
        entity_id=str(user.id),
        ip_address=_client_ip(request),
    )

    return TokenResponse(access_token=access_token)


# ── POST /api/auth/refresh ────────────────────────────────────────────────────

@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    refresh_token: Optional[str] = Cookie(default=None, alias=_REFRESH_COOKIE),
) -> RefreshResponse:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided.",
        )

    user_id = await get_user_id_from_refresh_token(refresh_token, redis)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or has expired. Please log in again.",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or has been deactivated.",
        )

    access_token = create_access_token(str(user.id), user.role.value)
    return RefreshResponse(access_token=access_token)


# ── POST /api/auth/logout ─────────────────────────────────────────────────────

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
    refresh_token: Optional[str] = Cookie(default=None, alias=_REFRESH_COOKIE),
) -> None:
    if refresh_token:
        await revoke_refresh_token(refresh_token, redis)

    response.delete_cookie(key=_REFRESH_COOKIE, path="/api/auth")

    await write_audit_log(
        db,
        action="LOGOUT",
        user_id=str(current_user.id),
        entity_type="User",
        entity_id=str(current_user.id),
        ip_address=_client_ip(request),
    )
