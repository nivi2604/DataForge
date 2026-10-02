import asyncio
import logging
from app.services.scheduler_service import SchedulerService
from app.core.config import settings

logger = logging.getLogger(__name__)

class SchedulerWorker:
    def __init__(self):
        self.scheduler_service = SchedulerService()
        self.task: asyncio.Task | None = None
        self.running = False

    async def _loop(self):
        logger.info(f"Scheduler worker started with interval {settings.scheduler_polling_interval}s")
        while self.running:
            try:
                # Need to run synchronous service method in thread pool or just directly
                # if it's very fast. Since it's DB operations, it's safer to use run_in_executor
                # to avoid blocking the event loop.
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self.scheduler_service.trigger_due_schedules)
                logger.debug("Scheduler polling cycle completed")
            except Exception as e:
                logger.error(f"Unexpected error in scheduler worker: {e}")
            
            if not self.running:
                break
                
            try:
                await asyncio.sleep(settings.scheduler_polling_interval)
            except asyncio.CancelledError:
                break

    def start(self):
        if self.running:
            return
        self.running = True
        self.task = asyncio.create_task(self._loop())

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.task:
            self.task.cancel()
            self.task = None
        logger.info("Scheduler worker stopped")

worker = SchedulerWorker()
