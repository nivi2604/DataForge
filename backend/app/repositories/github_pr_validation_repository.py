import uuid
from datetime import datetime, timezone
from sqlalchemy import or_
from app.db.session import SessionLocal
from app.models.github_pr_validation import GithubPRValidation


class GithubPRValidationRepository:
    """CRUD for GithubPRValidation records."""

    def create(self, record: GithubPRValidation) -> GithubPRValidation:
        if not record.id:
            record.id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        if not record.created_at:
            record.created_at = now
        record.updated_at = now
        with SessionLocal() as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def get_by_delivery_id(self, delivery_id: str) -> GithubPRValidation | None:
        with SessionLocal() as session:
            return (
                session.query(GithubPRValidation)
                .filter(GithubPRValidation.delivery_id == delivery_id)
                .first()
            )

    def get_by_id(self, record_id: str) -> GithubPRValidation | None:
        with SessionLocal() as session:
            return session.get(GithubPRValidation, record_id)

    def list_for_repository(self, repository_name: str, limit: int = 20) -> list[GithubPRValidation]:
        with SessionLocal() as session:
            return (
                session.query(GithubPRValidation)
                .filter(GithubPRValidation.repository_name == repository_name)
                .order_by(GithubPRValidation.created_at.desc())
                .limit(limit)
                .all()
            )

    def list_all(self, limit: int = 50) -> list[GithubPRValidation]:
        with SessionLocal() as session:
            return (
                session.query(GithubPRValidation)
                .order_by(GithubPRValidation.created_at.desc())
                .limit(limit)
                .all()
            )

    def update(self, record_id: str, **kwargs) -> GithubPRValidation | None:
        with SessionLocal() as session:
            record = session.get(GithubPRValidation, record_id)
            if not record:
                return None
            for k, v in kwargs.items():
                setattr(record, k, v)
            record.updated_at = datetime.now(timezone.utc).isoformat()
            session.commit()
            session.refresh(record)
            return record
