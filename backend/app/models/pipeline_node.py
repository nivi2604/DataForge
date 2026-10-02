from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PipelineNode(Base):
    __tablename__ = "pipeline_nodes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    pipeline_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("pipelines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    node_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    configuration: Mapped[str | None] = mapped_column(
        String(4000),
        nullable=True,
    )
    sequence_index: Mapped[int | None] = mapped_column(
        Integer,
        default=0,
        nullable=True,
    )
    position_x: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    position_y: Mapped[int | None] = mapped_column(
        Integer,
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
