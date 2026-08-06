from datetime import datetime, timezone
from uuid import uuid4

from app.db.session import SessionLocal
from app.models.data_source import DataSource


class DataSourceRepository:
    """SQLAlchemy-backed repository for data sources."""

    def list_data_sources(self) -> list[DataSource]:
        with SessionLocal() as session:
            return list(session.query(DataSource).all())

    def get_data_source(self, data_source_id: str) -> DataSource | None:
        with SessionLocal() as session:
            return session.get(DataSource, data_source_id)

    def get_data_source_by_id(self, data_source_id: str) -> DataSource | None:
        return self.get_data_source(data_source_id)

    def create_data_source(self, data_source: DataSource) -> DataSource:
        if not data_source.id:
            data_source.id = str(uuid4())
        if not data_source.created_at:
            data_source.created_at = datetime.now(timezone.utc).isoformat()
        if not data_source.updated_at:
            data_source.updated_at = data_source.created_at
        with SessionLocal() as session:
            session.add(data_source)
            session.commit()
            session.refresh(data_source)
            return data_source

    def update_data_source(self, data_source_id: str, data_source: DataSource) -> DataSource:
        with SessionLocal() as session:
            existing_data_source = session.get(DataSource, data_source_id)
            if not existing_data_source:
                raise KeyError(data_source_id)

            for field in ["project_id", "name", "type", "connection_details", "status"]:
                value = getattr(data_source, field, None)
                if value is not None:
                    setattr(existing_data_source, field, value)

            existing_data_source.updated_at = datetime.now(timezone.utc).isoformat()
            session.commit()
            session.refresh(existing_data_source)
            return existing_data_source

    def delete_data_source(self, data_source_id: str) -> None:
        with SessionLocal() as session:
            data_source = session.get(DataSource, data_source_id)
            if not data_source:
                raise KeyError(data_source_id)
            session.delete(data_source)
            session.commit()
