from uuid import uuid4

from sqlalchemy import func

from app.db.session import SessionLocal
from app.models.user import User


class UserRepository:
    """SQLAlchemy-backed repository for user persistence."""

    def list_users(self) -> list[User]:
        with SessionLocal() as session:
            return list(session.query(User).all())

    def get_user(self, user_id: str) -> User | None:
        with SessionLocal() as session:
            return session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        normalized_email = email.lower().strip()
        with SessionLocal() as session:
            return session.query(User).filter(func.lower(User.email) == normalized_email).first()

    def create_user(self, user: User) -> User:
        if not user.id:
            user.id = str(uuid4())
        with SessionLocal() as session:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def update_user(self, user_id: str, user: User) -> User:
        with SessionLocal() as session:
            existing_user = session.get(User, user_id)
            if not existing_user:
                raise KeyError(user_id)

            for field in ["first_name", "last_name", "email", "password_hash", "avatar", "status", "updated_at"]:
                value = getattr(user, field, None)
                if value is not None:
                    setattr(existing_user, field, value)

            session.commit()
            session.refresh(existing_user)
            return existing_user

    def delete_user(self, user_id: str) -> None:
        with SessionLocal() as session:
            user = session.get(User, user_id)
            if not user:
                raise KeyError(user_id)
            session.delete(user)
            session.commit()
