from datetime import datetime, timezone
from uuid import uuid4

from app.db.session import SessionLocal
from app.models.pipeline_schedule import PipelineSchedule


class SchedulerRepository:
    """Scheduler repository."""

    def list_schedules(self, pipeline_id: str) -> list[PipelineSchedule]:
        with SessionLocal() as session:
            return list(
                session.query(PipelineSchedule)
                .filter(PipelineSchedule.pipeline_id == pipeline_id)
                .all()
            )

    def get_schedule(self, schedule_id: str) -> PipelineSchedule | None:
        with SessionLocal() as session:
            return session.get(PipelineSchedule, schedule_id)

    def create_schedule(self, schedule: PipelineSchedule) -> PipelineSchedule:
        if not schedule.id:
            schedule.id = str(uuid4())
        if not schedule.created_at:
            schedule.created_at = datetime.now(timezone.utc).isoformat()

        with SessionLocal() as session:
            session.add(schedule)
            session.commit()
            session.refresh(schedule)
            return schedule

    def update_schedule(self, schedule_id: str, schedule: PipelineSchedule) -> PipelineSchedule:
        with SessionLocal() as session:
            existing = session.get(PipelineSchedule, schedule_id)
            if not existing:
                raise KeyError(schedule_id)

            for field in ["schedule_expression", "enabled", "next_run_at", "updated_at"]:
                value = getattr(schedule, field, None)
                if value is not None:
                    setattr(existing, field, value)

            session.commit()
            session.refresh(existing)
            return existing

    def delete_schedule(self, schedule_id: str) -> None:
        with SessionLocal() as session:
            existing = session.get(PipelineSchedule, schedule_id)
            if not existing:
                raise KeyError(schedule_id)
            session.delete(existing)
            session.commit()
