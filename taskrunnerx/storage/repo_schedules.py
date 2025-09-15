"""Schedule repository."""

from typing import List, Optional
from sqlalchemy.orm import Session

from ..domain.entities import ScheduleEntity
from ..domain.errors import ScheduleNotFound
from .models import Schedule


class ScheduleRepository:
    """Schedule data access layer."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def create(self, schedule: ScheduleEntity) -> ScheduleEntity:
        """Create new schedule."""
        db_schedule = Schedule(
            id=schedule.id,
            name=schedule.name,
            cron_expression=schedule.cron_expression,
            task_name=schedule.task_name,
            args=schedule.args,
            kwargs=schedule.kwargs,
            queue=schedule.queue,
            is_active=schedule.is_active,
            created_at=schedule.created_at,
            next_run_at=schedule.next_run_at
        )
        self.db.add(db_schedule)
        self.db.commit()
        self.db.refresh(db_schedule)
        return self._to_entity(db_schedule)
        
    def get_by_id(self, schedule_id: str) -> ScheduleEntity:
        """Get schedule by ID."""
        db_schedule = self.db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not db_schedule:
            raise ScheduleNotFound(f"Schedule {schedule_id} not found")
        return self._to_entity(db_schedule)
        
    def get_active_schedules(self) -> List[ScheduleEntity]:
        """Get all active schedules."""
        db_schedules = self.db.query(Schedule).filter(Schedule.is_active == True).all()
        return [self._to_entity(s) for s in db_schedules]
        
    def _to_entity(self, db_schedule: Schedule) -> ScheduleEntity:
        """Convert ORM model to entity."""
        return ScheduleEntity(
            id=db_schedule.id,
            name=db_schedule.name,
            cron_expression=db_schedule.cron_expression,
            task_name=db_schedule.task_name,
            args=db_schedule.args,
            kwargs=db_schedule.kwargs,
            queue=db_schedule.queue,
            is_active=db_schedule.is_active,
            created_at=db_schedule.created_at,
            last_run_at=db_schedule.last_run_at,
            next_run_at=db_schedule.next_run_at
        )
