from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.health_service import HealthService

router = APIRouter(prefix="/health", tags=["health"])
health_service = HealthService()


@router.get("", response_model=HealthResponse)
def get_health() -> HealthResponse:
    # TODO: Implement full health aggregation.
    return health_service.get_health()


@router.get("/live", response_model=HealthResponse)
def get_liveness() -> HealthResponse:
    # TODO: Implement liveness probe.
    return health_service.get_liveness()


@router.get("/ready", response_model=HealthResponse)
def get_readiness() -> HealthResponse:
    # TODO: Implement readiness probe.
    return health_service.get_readiness()
