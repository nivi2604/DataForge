from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[str | None] = mapped_column(String(100), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(100), nullable=True)
