from sqlalchemy import ForeignKey, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PipelineSchedule(Base):
    __tablename__ = "pipeline_schedules"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    pipeline_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("pipelines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    schedule_expression: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    enabled: Mapped[bool | None] = mapped_column(
        Boolean,
        default=True,
        nullable=True,
    )
    next_run_at: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    created_at: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    updated_at: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
