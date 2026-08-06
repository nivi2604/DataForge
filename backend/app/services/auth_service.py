from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest


class AuthService:
    """Authentication service for registration and related account operations."""

    def __init__(self, user_repository: UserRepository | None = None) -> None:
        self.user_repository = user_repository or UserRepository()

    def register_user(self, user_data: dict | RegisterRequest) -> User:
        if isinstance(user_data, RegisterRequest):
            payload = {
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "email": user_data.email,
                "password": user_data.password,
            }
        else:
            payload = dict(user_data)

        first_name = (payload.get("first_name") or "").strip()
        last_name = (payload.get("last_name") or "").strip()
        email = (payload.get("email") or "").strip().lower()
        password = (payload.get("password") or "").strip()

        if not first_name or not last_name or not email or not password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="All fields are required")

        if self.user_repository.get_by_email(email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        hashed_password = hash_password(password)
        now = datetime.now(timezone.utc).isoformat()
        user = User(
            id=str(uuid4()),
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=hashed_password,
            status="active",
            created_at=now,
            updated_at=now,
        )

        return self.user_repository.create_user(user)

    def register(self, data: dict) -> dict:
        user = self.register_user(data)
        return {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "status": user.status,
            "created_at": user.created_at,
        }

    def login_user(self, credentials: dict | LoginRequest) -> dict:
        if isinstance(credentials, LoginRequest):
            payload = {"email": credentials.email, "password": credentials.password}
        else:
            payload = dict(credentials)

        email = (payload.get("email") or "").strip().lower()
        password = (payload.get("password") or "").strip()

        if not email or not password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email and password are required")

        user = self.user_repository.get_by_email(email)
        if not user or not user.password_hash:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        access_token = create_access_token(str(user.id))
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "status": user.status,
                "created_at": user.created_at,
            },
        }

    def login(self, data: dict) -> dict:
        return self.login_user(data)

    def refresh_token(self, refresh_token: str) -> dict:
        raise NotImplementedError
