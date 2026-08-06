from app.models.schedule import Schedule
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate


class SchedulerService:
    """Placeholder scheduler service."""

    def list_schedules(self) -> list[Schedule]:
        # TODO: Implement listing schedules.
        raise NotImplementedError

    def get_schedule(self, schedule_id: str) -> Schedule:
        # TODO: Implement fetching a schedule.
        raise NotImplementedError

    def create_schedule(self, payload: ScheduleCreate) -> Schedule:
        # TODO: Implement creating a schedule.
        raise NotImplementedError

    def update_schedule(self, schedule_id: str, payload: ScheduleUpdate) -> Schedule:
        # TODO: Implement updating a schedule.
        raise NotImplementedError

    def delete_schedule(self, schedule_id: str) -> None:
        # TODO: Implement deleting a schedule.
        raise NotImplementedError

    def enable_schedule(self, schedule_id: str) -> Schedule:
        # TODO: Implement enabling a schedule.
        raise NotImplementedError

    def disable_schedule(self, schedule_id: str) -> Schedule:
        # TODO: Implement disabling a schedule.
        raise NotImplementedError
