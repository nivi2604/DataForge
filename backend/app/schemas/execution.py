from dataclasses import dataclass


@dataclass
class ExecutePipelineRequest:
    triggered_by: str | None = None


@dataclass
class ExecutionResponse:
    id: str
    pipeline_id: str | None = None
    status: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    duration: int | None = None
    triggered_by: str | None = None
    created_at: str | None = None


@dataclass
class ExecutionLogResponse:
    id: str
    execution_id: str | None = None
    level: str | None = None
    message: str | None = None
    timestamp: str | None = None
