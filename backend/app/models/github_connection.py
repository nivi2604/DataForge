from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GithubConnection(Base):
    __tablename__ = "github_connections"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    repository_name: Mapped[str] = mapped_column(String(255))
    encrypted_token: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[str | None] = mapped_column(String(100), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(100), nullable=True)
