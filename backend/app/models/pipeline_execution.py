from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PipelineExecution(Base):
    __tablename__ = "pipeline_executions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    pipeline_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("pipelines.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    started_at: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    completed_at: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    duration: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    triggered_by: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    created_at: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
