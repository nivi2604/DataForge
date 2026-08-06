from dataclasses import dataclass


@dataclass
class PipelineCreate:
    project_id: str
    name: str
    description: str | None = None
    version: str | None = None
    status: str | None = None


@dataclass
class PipelineUpdate:
    project_id: str | None = None
    name: str | None = None
    description: str | None = None
    version: str | None = None
    status: str | None = None


@dataclass
class PipelineResponse:
    id: str
    project_id: str | None = None
    name: str | None = None
    description: str | None = None
    version: str | None = None
    status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class PipelineNodeCreate:
    node_type: str
    configuration: str | None = None
    position_x: int | None = None
    position_y: int | None = None


@dataclass
class PipelineNodeResponse:
    id: str
    pipeline_id: str | None = None
    node_type: str | None = None
    configuration: str | None = None
    position_x: int | None = None
    position_y: int | None = None
