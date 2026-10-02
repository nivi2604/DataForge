from datetime import datetime, timedelta, timezone
from croniter import croniter, CroniterBadCronError

from fastapi import HTTPException, status

from app.models.pipeline_schedule import PipelineSchedule
from app.repositories.pipeline_repository import PipelineRepository
from app.repositories.scheduler_repository import SchedulerRepository
from app.schemas.execution import ExecutePipelineRequest
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.services.execution_service import ExecutionService


class SchedulerService:
    """Scheduler service."""

    def __init__(self) -> None:
        self.scheduler_repository = SchedulerRepository()
        self.pipeline_repository = PipelineRepository()
        self.execution_service = ExecutionService()

    def _calculate_next_run(self, expression: str, base_time: datetime) -> str:
        expr = (expression or "").strip().lower()
        if expr == "hourly":
            expr = "0 * * * *"
        elif expr == "daily":
            expr = "0 0 * * *"
        elif expr == "weekly":
            expr = "0 0 * * 0"

        try:
            # Ensure base_time is in UTC and naive for croniter if needed, or just let croniter handle it.
            # croniter handles tz-aware datetimes correctly if base_time is tz-aware.
            itr = croniter(expr, base_time)
            next_time = itr.get_next(datetime)
            return next_time.isoformat()
        except CroniterBadCronError:
            raise ValueError(f"Invalid cron expression: {expression}")

    def _verify_pipeline(self, pipeline_id: str) -> None:
        if not self.pipeline_repository.get_pipeline_by_id(pipeline_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")

    def _verify_schedule_ownership(self, pipeline_id: str, schedule: PipelineSchedule | None) -> None:
        if not schedule or schedule.pipeline_id != pipeline_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found for this pipeline")

    def list_schedules(self, pipeline_id: str) -> list[PipelineSchedule]:
        self._verify_pipeline(pipeline_id)
        return self.scheduler_repository.list_schedules(pipeline_id)

    def get_schedule(self, pipeline_id: str, schedule_id: str) -> PipelineSchedule:
        self._verify_pipeline(pipeline_id)
        schedule = self.scheduler_repository.get_schedule(schedule_id)
        self._verify_schedule_ownership(pipeline_id, schedule)
        return schedule

    def create_schedule(self, pipeline_id: str, payload: ScheduleCreate) -> PipelineSchedule:
        self._verify_pipeline(pipeline_id)

        now = datetime.now(timezone.utc)
        try:
            next_run = self._calculate_next_run(payload.schedule_expression, now)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        schedule = PipelineSchedule(
            pipeline_id=pipeline_id,
            schedule_expression=payload.schedule_expression,
            enabled=payload.enabled if payload.enabled is not None else True,
            next_run_at=next_run,
        )
        return self.scheduler_repository.create_schedule(schedule)

    def update_schedule(self, pipeline_id: str, schedule_id: str, payload: ScheduleUpdate) -> PipelineSchedule:
        self._verify_pipeline(pipeline_id)
        existing = self.scheduler_repository.get_schedule(schedule_id)
        self._verify_schedule_ownership(pipeline_id, existing)

        schedule = PipelineSchedule()
        if payload.schedule_expression is not None:
            schedule.schedule_expression = payload.schedule_expression
            now = datetime.now(timezone.utc)
            try:
                schedule.next_run_at = self._calculate_next_run(payload.schedule_expression, now)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        if payload.enabled is not None:
            schedule.enabled = payload.enabled

        schedule.updated_at = datetime.now(timezone.utc).isoformat()

        return self.scheduler_repository.update_schedule(schedule_id, schedule)

    def delete_schedule(self, pipeline_id: str, schedule_id: str) -> None:
        self._verify_pipeline(pipeline_id)
        existing = self.scheduler_repository.get_schedule(schedule_id)
        self._verify_schedule_ownership(pipeline_id, existing)
        self.scheduler_repository.delete_schedule(schedule_id)

    def trigger_due_schedules(self, current_time: datetime | None = None) -> None:
        """Trigger all enabled schedules whose next_run_at is <= current_time."""
        now = current_time or datetime.now(timezone.utc)
        now_iso = now.isoformat()

        from app.db.session import SessionLocal
        with SessionLocal() as session:
            due_schedules = session.query(PipelineSchedule).filter(
                PipelineSchedule.enabled == True,
                PipelineSchedule.next_run_at <= now_iso
            ).all()

            for schedule in due_schedules:
                if schedule.pipeline_id:
                    try:
                        self.execution_service.execute_pipeline(
                            schedule.pipeline_id,
                            ExecutePipelineRequest(triggered_by="scheduler")
                        )
                    except Exception:
                        pass # Continue with other schedules

                    # Update next run
                    try:
                        next_time = self._calculate_next_run(schedule.schedule_expression or "hourly", now)
                    except ValueError:
                        # Fallback for heavily corrupted expressions so worker loop doesn't block forever
                        next_time = (now + timedelta(hours=1)).isoformat()

                    update_obj = PipelineSchedule(next_run_at=next_time)
                    self.scheduler_repository.update_schedule(schedule.id, update_obj)
