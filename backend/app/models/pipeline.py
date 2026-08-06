from dataclasses import dataclass


@dataclass
class Pipeline:
    id: str | None = None
    project_id: str | None = None
    name: str | None = None
    description: str | None = None
    version: str | None = None
    status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
