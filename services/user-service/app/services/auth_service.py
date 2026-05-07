import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import redis.asyncio as aioredis
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..models.user import AuditLog

settings = get_settings()

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

REFRESH_TOKEN_PREFIX = "refresh:"


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(user_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# ── Refresh token (stored in Redis) ──────────────────────────────────────────

async def create_refresh_token(user_id: str, redis: aioredis.Redis) -> str:
    token = str(uuid.uuid4())
    key = f"{REFRESH_TOKEN_PREFIX}{token}"
    ttl_seconds = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400
    await redis.setex(key, ttl_seconds, str(user_id))
    return token


async def get_user_id_from_refresh_token(
    token: str, redis: aioredis.Redis
) -> Optional[str]:
    key = f"{REFRESH_TOKEN_PREFIX}{token}"
    value = await redis.get(key)
    if value is None:
        return None
    return value.decode() if isinstance(value, bytes) else value


async def revoke_refresh_token(token: str, redis: aioredis.Redis) -> None:
    key = f"{REFRESH_TOKEN_PREFIX}{token}"
    await redis.delete(key)


# ── Audit logging ─────────────────────────────────────────────────────────────

async def write_audit_log(
    db: AsyncSession,
    action: str,
    user_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    extra_data: Optional[dict] = None,
) -> None:
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        extra_data=extra_data,
    )
    db.add(log)
