from dataclasses import dataclass


@dataclass
class WorkspaceCreate:
    organization_id: str
    name: str
    description: str | None = None


@dataclass
class WorkspaceUpdate:
    organization_id: str | None = None
    name: str | None = None
    description: str | None = None


@dataclass
class WorkspaceResponse:
    id: str
    organization_id: str | None = None
    name: str | None = None
    description: str | None = None
    created_at: str | None = None
