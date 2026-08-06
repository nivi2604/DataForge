from dataclasses import dataclass


@dataclass
class ScheduleCreate:
    pipeline_id: str
    cron_expression: str
    enabled: bool | None = None


@dataclass
class ScheduleUpdate:
    pipeline_id: str | None = None
    cron_expression: str | None = None
    enabled: bool | None = None


@dataclass
class ScheduleResponse:
    id: str
    pipeline_id: str | None = None
    cron_expression: str | None = None
    enabled: bool | None = None
    next_run: str | None = None
    last_run: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
