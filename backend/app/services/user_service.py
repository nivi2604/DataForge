from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Placeholder user service."""

    def list_users(self) -> list[User]:
        # TODO: Implement list users.
        raise NotImplementedError

    def get_user(self, user_id: str) -> User:
        # TODO: Implement get user by id.
        raise NotImplementedError

    def create_user(self, payload: UserCreate) -> User:
        # TODO: Implement create user.
        raise NotImplementedError

    def update_user(self, user_id: str, payload: UserUpdate) -> User:
        # TODO: Implement update user.
        raise NotImplementedError

    def delete_user(self, user_id: str) -> None:
        # TODO: Implement delete user.
        raise NotImplementedError
