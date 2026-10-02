from fastapi import APIRouter, Header, status, Response

from app.api.routes.auth import auth_service
from app.core.security import get_current_user
from app.models.pipeline_schedule import PipelineSchedule
from app.models.user import User
from app.schemas.schedule import ScheduleCreate, ScheduleResponse, ScheduleUpdate
from app.services.scheduler_service import SchedulerService
from app.services.authorization_service import AuthorizationService

router = APIRouter(tags=["schedules"])
scheduler_service = SchedulerService()


def _require_authentication(authorization: str | None) -> User:
    return get_current_user(authorization, auth_service.user_repository)


def _to_schedule_response(schedule: PipelineSchedule) -> ScheduleResponse:
    return ScheduleResponse(
        id=schedule.id or "",
        pipeline_id=schedule.pipeline_id,
        schedule_expression=schedule.schedule_expression,
        enabled=schedule.enabled,
        next_run_at=schedule.next_run_at,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


@router.get("/pipelines/{pipeline_id}/schedules", response_model=list[ScheduleResponse])
def list_schedules(
    pipeline_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> list[ScheduleResponse]:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)
    schedules = scheduler_service.list_schedules(pipeline_id)
    return [_to_schedule_response(s) for s in schedules]


@router.get("/pipelines/{pipeline_id}/schedules/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(
    pipeline_id: str,
    schedule_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ScheduleResponse:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)
    schedule = scheduler_service.get_schedule(pipeline_id, schedule_id)
    return _to_schedule_response(schedule)


@router.post("/pipelines/{pipeline_id}/schedules", response_model=ScheduleResponse, status_code=201)
def create_schedule(
    pipeline_id: str,
    payload: ScheduleCreate,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ScheduleResponse:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)
    schedule = scheduler_service.create_schedule(pipeline_id, payload)
    return _to_schedule_response(schedule)


@router.put("/pipelines/{pipeline_id}/schedules/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    pipeline_id: str,
    schedule_id: str,
    payload: ScheduleUpdate,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ScheduleResponse:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)
    schedule = scheduler_service.update_schedule(pipeline_id, schedule_id, payload)
    return _to_schedule_response(schedule)


@router.delete("/pipelines/{pipeline_id}/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    pipeline_id: str,
    schedule_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> Response:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)
    scheduler_service.delete_schedule(pipeline_id, schedule_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
