from dataclasses import dataclass


@dataclass
class ExecutionLog:
    id: str | None = None
    execution_id: str | None = None
    level: str | None = None
    message: str | None = None
    timestamp: str | None = None
