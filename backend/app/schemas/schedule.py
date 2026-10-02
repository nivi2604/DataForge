from dataclasses import dataclass


@dataclass
class ScheduleCreate:
    schedule_expression: str
    enabled: bool | None = True


@dataclass
class ScheduleUpdate:
    schedule_expression: str | None = None
    enabled: bool | None = None


@dataclass
class ScheduleResponse:
    id: str
    pipeline_id: str | None = None
    schedule_expression: str | None = None
    enabled: bool | None = None
    next_run_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
