from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PipelineVersion(Base):
    __tablename__ = "pipeline_versions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    pipeline_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("pipelines.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    version_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    created_by: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    pipeline_snapshot: Mapped[str | None] = mapped_column(
        String(10000), # large enough for JSON snapshot
        nullable=True,
    )
    created_at: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    github_branch: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    github_commit_sha: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    github_pr_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
