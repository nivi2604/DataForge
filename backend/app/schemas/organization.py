from dataclasses import dataclass


@dataclass
class OrganizationCreate:
    name: str
    description: str | None = None
    owner_id: str | None = None


@dataclass
class OrganizationUpdate:
    name: str | None = None
    description: str | None = None
    owner_id: str | None = None


@dataclass
class OrganizationResponse:
    id: str
    name: str | None = None
    description: str | None = None
    owner_id: str | None = None
    created_at: str | None = None
