from typing import Any

from fastapi import APIRouter, Depends, Header, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=dict[str, Any])
def register(payload: RegisterRequest) -> dict[str, Any]:
    created_user = auth_service.register_user(payload)
    return {
        "id": created_user.id,
        "first_name": created_user.first_name,
        "last_name": created_user.last_name,
        "email": created_user.email,
        "status": created_user.status,
        "created_at": created_user.created_at,
    }


@router.post("/login", response_model=dict[str, Any])
def login(payload: LoginRequest) -> dict[str, Any]:
    return auth_service.login_user(payload)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(refresh_token: str) -> TokenResponse:
    # TODO: Implement refresh token flow.
    raise NotImplementedError


@router.post("/logout")
def logout() -> dict[str, str]:
    # TODO: Implement logout flow.
    raise NotImplementedError


def get_current_user_dependency(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> User:
    return get_current_user(authorization, auth_service.user_repository)


@router.get("/me", response_model=dict[str, Any])
def get_authenticated_user(current_user: User = Depends(get_current_user_dependency)) -> dict[str, Any]:
    return {
        "id": current_user.id,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "created_at": current_user.created_at,
    }
