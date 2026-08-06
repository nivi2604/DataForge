from dataclasses import dataclass


@dataclass
class DataSourceCreate:
    project_id: str
    name: str
    type: str
    connection_details: str | None = None
    status: str | None = None


@dataclass
class DataSourceUpdate:
    project_id: str | None = None
    name: str | None = None
    type: str | None = None
    connection_details: str | None = None
    status: str | None = None


@dataclass
class DataSourceResponse:
    id: str
    project_id: str | None = None
    name: str | None = None
    type: str | None = None
    connection_details: str | None = None
    status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class TestConnectionRequest:
    connection_details: str | None = None


@dataclass
class TestConnectionResponse:
    success: bool
    message: str | None = None
