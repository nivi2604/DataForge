from fastapi import APIRouter

from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])
user_service = UserService()


@router.get("", response_model=list[UserResponse])
def list_users() -> list[UserResponse]:
    # TODO: Implement list users.
    raise NotImplementedError


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str) -> UserResponse:
    # TODO: Implement get user by id.
    raise NotImplementedError


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, payload: UserUpdate) -> UserResponse:
    # TODO: Implement update user.
    raise NotImplementedError


@router.delete("/{user_id}")
def delete_user(user_id: str) -> dict[str, str]:
    # TODO: Implement delete user.
    raise NotImplementedError
