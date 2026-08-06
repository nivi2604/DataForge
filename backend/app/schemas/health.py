from dataclasses import dataclass


@dataclass
class HealthResponse:
    status: str
    version: str | None = None
    uptime: str | None = None
    timestamp: str | None = None
