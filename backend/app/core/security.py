from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError
from passlib.context import CryptContext

from app.core.config import settings
from app.models.user import User
from app.repositories.user_repository import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(password, hashed_password)


def create_access_token(user_id: str) -> str:
    """Create a signed JWT access token for a user identifier."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def verify_access_token(token: str) -> dict[str, Any]:
    """Validate and decode a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={"require": ["sub", "exp", "iat", "type"]},
        )
    except ExpiredSignatureError as exc:
        raise exc
    except JWTClaimsError as exc:
        raise exc
    except JWTError as exc:
        raise exc

    if payload.get("type") != "access":
        raise JWTClaimsError("Token type is invalid")

    return payload


def get_current_user(authorization: str | None, user_repository: UserRepository | None = None) -> User:
    """Resolve the authenticated user from an Authorization header token."""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        payload = verify_access_token(token)
    except ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from exc
    except (JWTClaimsError, JWTError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    repository = user_repository or UserRepository()
    user = repository.get_user(str(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user




class PasswordHasher:
    """Compatibility wrapper for password hashing utilities."""

    def hash_password(self, password: str) -> str:
        return hash_password(password)

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return verify_password(password, hashed_password)


class TokenManager:
    """JWT token utilities with access token helpers."""

    def create_access_token(self, subject: str, expires_in_minutes: int = 60) -> str:
        if expires_in_minutes != settings.access_token_expire_minutes:
            settings.access_token_expire_minutes = expires_in_minutes
        return create_access_token(subject)

    def create_refresh_token(self, subject: str, expires_in_days: int = 7) -> str:
        raise NotImplementedError

    def validate_token(self, token: str) -> dict[str, Any]:
        return verify_access_token(token)
