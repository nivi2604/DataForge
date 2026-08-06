from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    owner_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[str | None] = mapped_column(String(100), nullable=True)
