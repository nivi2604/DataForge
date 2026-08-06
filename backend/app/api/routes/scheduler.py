from fastapi import APIRouter

from app.models.schedule import Schedule
from app.schemas.schedule import ScheduleCreate, ScheduleResponse, ScheduleUpdate
from app.services.scheduler_service import SchedulerService

router = APIRouter(prefix="/schedules", tags=["schedules"])
scheduler_service = SchedulerService()


@router.get("", response_model=list[ScheduleResponse])
def list_schedules() -> list[ScheduleResponse]:
    # TODO: Implement listing schedules.
    raise NotImplementedError


@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(schedule_id: str) -> ScheduleResponse:
    # TODO: Implement fetching a schedule.
    raise NotImplementedError


@router.post("", response_model=ScheduleResponse)
def create_schedule(payload: ScheduleCreate) -> ScheduleResponse:
    # TODO: Implement creating a schedule.
    raise NotImplementedError


@router.put("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(schedule_id: str, payload: ScheduleUpdate) -> ScheduleResponse:
    # TODO: Implement updating a schedule.
    raise NotImplementedError


@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: str) -> dict[str, str]:
    # TODO: Implement deleting a schedule.
    raise NotImplementedError


@router.patch("/{schedule_id}/enable", response_model=ScheduleResponse)
def enable_schedule(schedule_id: str) -> ScheduleResponse:
    # TODO: Implement enabling a schedule.
    raise NotImplementedError


@router.patch("/{schedule_id}/disable", response_model=ScheduleResponse)
def disable_schedule(schedule_id: str) -> ScheduleResponse:
    # TODO: Implement disabling a schedule.
    raise NotImplementedError
