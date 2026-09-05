from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import get_or_create_dev_keypair
from app.core.security import decode_access_token
from app.db.session import get_db  # re-exported
from app.models.user import User

_cached_keys: tuple[str, str] | None = None


def get_signing_keys() -> tuple[str, str]:
    global _cached_keys
    if _cached_keys is None:
        _cached_keys = get_or_create_dev_keypair()
    return _cached_keys


_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Protects operation-submission endpoints. Requires a valid,
    unexpired JWT issued by POST /auth/login."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists")

    return user


__all__ = ["get_db", "get_signing_keys", "get_current_user"]
