from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GithubPRValidation(Base):
    """Persisted record of a DataForge pipeline validation triggered by a GitHub PR event."""

    __tablename__ = "github_pr_validations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)

    # GitHub delivery de-duplication key
    delivery_id: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True, index=True)

    # Identifies which GithubConnection this belongs to
    repository_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    pr_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    head_branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    base_branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pr_html_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # DataForge pipeline file detected in the PR
    pipeline_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Validation + execution result
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)  # pending, running, passed, failed, skipped
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Reference to the pipeline execution record (if executed)
    execution_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[str | None] = mapped_column(String(100), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(100), nullable=True)
