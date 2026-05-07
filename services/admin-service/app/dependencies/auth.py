import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from ..config import settings

_bearer = HTTPBearer()


async def require_admin(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> uuid.UUID:
    """Require ADMIN or SUPER_ADMIN role. Returns admin's UUID."""
    token = credentials.credentials
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
        return uuid.UUID(sub)
    except HTTPException:
        raise
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )
