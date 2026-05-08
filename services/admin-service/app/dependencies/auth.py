import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from ..config import settings

_bearer = HTTPBearer()


@dataclass
class AdminContext:
    """Carries the admin caller's identity and role for downstream filtering."""
    user_id: uuid.UUID
    role: str  # "ADMIN" or "SUPER_ADMIN"

    @property
    def is_super_admin(self) -> bool:
        return self.role == "SUPER_ADMIN"


def _decode_admin_token(token: str) -> AdminContext:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub: str = payload.get("sub", "")
        role: str = payload.get("role", "")
        if not sub:
            raise ValueError("Missing sub")
        if role not in ("ADMIN", "SUPER_ADMIN"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )
        return AdminContext(user_id=uuid.UUID(sub), role=role)
    except HTTPException:
        raise
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )


async def require_admin(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> uuid.UUID:
    """Require ADMIN or SUPER_ADMIN role. Returns admin's UUID."""
    ctx = _decode_admin_token(credentials.credentials)
    return ctx.user_id


async def require_admin_context(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> AdminContext:
    """Like require_admin but returns full AdminContext (includes role) for caller-aware filtering."""
    return _decode_admin_token(credentials.credentials)


async def require_super_admin(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> uuid.UUID:
    """Require exactly SUPER_ADMIN role. Returns admin's UUID."""
    ctx = _decode_admin_token(credentials.credentials)
    if not ctx.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin access required",
        )
    return ctx.user_id
