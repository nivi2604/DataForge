from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    execution_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("pipeline_executions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    pipeline_node_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    level: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    message: Mapped[str | None] = mapped_column(
        String(4000),
        nullable=True,
    )
    created_at: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
