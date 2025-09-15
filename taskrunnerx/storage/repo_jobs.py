"""Job repository."""

from typing import List, Optional
from sqlalchemy.orm import Session

from ..domain.entities import JobEntity
from ..domain.errors import JobNotFound
from .models import Job


class JobRepository:
    """Job data access layer."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def create(self, job: JobEntity) -> JobEntity:
        """Create new job."""
        db_job = Job(
            id=job.id,
            task_name=job.task_name,
            args=job.args,
            kwargs=job.kwargs,
            status=job.status,
            queue=job.queue,
            priority=job.priority,
            max_retries=job.max_retries,
            retry_count=job.retry_count,
            timeout=job.timeout,
            created_at=job.created_at
        )
        self.db.add(db_job)
        self.db.commit()
        self.db.refresh(db_job)
        return self._to_entity(db_job)
        
    def get_by_id(self, job_id: str) -> JobEntity:
        """Get job by ID."""
        db_job = self.db.query(Job).filter(Job.id == job_id).first()
        if not db_job:
            raise JobNotFound(f"Job {job_id} not found")
        return self._to_entity(db_job)
        
    def update_status(
        self,
        job_id: str,
        status: str,
        result: Optional[any] = None,
        error: Optional[str] = None
    ) -> JobEntity:
        """Update job status."""
        db_job = self.db.query(Job).filter(Job.id == job_id).first()
        if not db_job:
            raise JobNotFound(f"Job {job_id} not found")
            
        db_job.status = status
        if result is not None:
            db_job.result = result
        if error is not None:
            db_job.error = error
            
        self.db.commit()
        self.db.refresh(db_job)
        return self._to_entity(db_job)
        
    def list_jobs(
        self,
        queue: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[JobEntity]:
        """List jobs with filters."""
        query = self.db.query(Job)
        
        if queue:
            query = query.filter(Job.queue == queue)
        if status:
            query = query.filter(Job.status == status)
            
        db_jobs = query.order_by(Job.created_at.desc()).limit(limit).all()
        return [self._to_entity(job) for job in db_jobs]
        
    def _to_entity(self, db_job: Job) -> JobEntity:
        """Convert ORM model to entity."""
        return JobEntity(
            id=db_job.id,
            task_name=db_job.task_name,
            args=db_job.args,
            kwargs=db_job.kwargs,
            status=db_job.status,
            queue=db_job.queue,
            priority=db_job.priority,
            max_retries=db_job.max_retries,
            retry_count=db_job.retry_count,
            timeout=db_job.timeout,
            created_at=db_job.created_at,
            started_at=db_job.started_at,
            completed_at=db_job.completed_at,
            result=db_job.result,
            error=db_job.error
        )
