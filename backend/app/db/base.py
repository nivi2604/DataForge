from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all persistence models."""

    pass


class BaseModel(Base):
    """Compatibility alias for the previous persistence base type."""

    __abstract__ = True
