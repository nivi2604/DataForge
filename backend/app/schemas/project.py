from dataclasses import dataclass


@dataclass
class ProjectCreate:
    workspace_id: str
    name: str
    description: str | None = None
    status: str | None = None


@dataclass
class ProjectUpdate:
    workspace_id: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None


@dataclass
class ProjectResponse:
    id: str
    workspace_id: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
