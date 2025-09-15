"""Schedule management service."""

from datetime import datetime
from typing import List
from uuid import uuid4

from ..domain.entities import ScheduleEntity
from ..domain.models import ScheduleCreate
from ..storage.repo_schedules import ScheduleRepository
from ..logging import get_logger
from .cron_parser import CronParser

logger = get_logger(__name__)


class ScheduleService:
    """Schedule management business logic."""
    
    def __init__(self, schedule_repo: ScheduleRepository):
        self.schedule_repo = schedule_repo
        self.cron_parser = CronParser()
        
    def create_schedule(self, schedule_create: ScheduleCreate) -> ScheduleEntity:
        """Create new schedule."""
        schedule_id = str(uuid4())
        
        # Parse next run time
        next_run = self.cron_parser.get_next_run(schedule_create.cron_expression)
        
        schedule = ScheduleEntity(
            id=schedule_id,
            name=schedule_create.name,
            cron_expression=schedule_create.cron_expression,
            task_name=schedule_create.task_name,
            args=schedule_create.args,
            kwargs=schedule_create.kwargs,
            queue=schedule_create.queue,
            is_active=schedule_create.is_active,
            created_at=datetime.utcnow(),
            next_run_at=next_run
        )
        
        schedule = self.schedule_repo.create(schedule)
        logger.info(f"Schedule created: {schedule.id}")
        
        return schedule
        
    def get_schedule(self, schedule_id: str) -> ScheduleEntity:
        """Get schedule by ID."""
        return self.schedule_repo.get_by_id(schedule_id)
        
    def get_due_schedules(self) -> List[ScheduleEntity]:
        """Get schedules that are due for execution."""
        schedules = self.schedule_repo.get_active_schedules()
        now = datetime.utcnow()
        
        due_schedules = []
        for schedule in schedules:
            if schedule.next_run_at and schedule.next_run_at <= now:
                due_schedules.append(schedule)
                
        return due_schedules
