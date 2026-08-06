from dataclasses import dataclass


@dataclass
class PipelineExecution:
    id: str | None = None
    pipeline_id: str | None = None
    status: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    duration: int | None = None
    triggered_by: str | None = None
    created_at: str | None = None
