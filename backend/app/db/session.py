from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base

engine = create_engine(settings.database_url, pool_pre_ping=True, echo=settings.database_echo)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class DatabaseSessionManager:
    """Simple session manager wrapper for the SQLAlchemy session factory."""

    def __init__(self) -> None:
        self._session: Session | None = None

    def get_session(self) -> Generator[Session | None, None, None]:
        if self._session is None:
            with SessionLocal() as session:
                yield session
        else:
            yield self._session


session_manager = DatabaseSessionManager()


def get_db_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


def init_db() -> None:
    from app.models.data_source import DataSource
    from app.models.organization import Organization
    from app.models.project import Project
    from app.models.user import User
    from app.models.workspace import Workspace

    Base.metadata.create_all(bind=engine)
