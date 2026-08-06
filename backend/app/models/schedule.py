from dataclasses import dataclass


@dataclass
class Schedule:
    id: str | None = None
    pipeline_id: str | None = None
    cron_expression: str | None = None
    enabled: bool | None = None
    next_run: str | None = None
    last_run: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
