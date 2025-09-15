"""Job management service."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4

from ..adapters.redis_streams import RedisStreams
from ..domain.entities import JobEntity
from ..domain.models import JobCreate
from ..storage.repo_jobs import JobRepository
from ..logging import get_logger
from ..metrics import metrics

logger = get_logger(__name__)


class JobService:
    """Job management business logic."""
    
    def __init__(self, job_repo: JobRepository, redis_streams: RedisStreams):
        self.job_repo = job_repo
        self.redis_streams = redis_streams
        
    def submit_job(self, job_create: JobCreate, idempotency_key: Optional[str] = None) -> JobEntity:
        """Submit new job to queue."""
        job_id = str(uuid4())
        
        # Create job entity
        job = JobEntity(
            id=job_id,
            task_name=job_create.task_name,
            args=job_create.args,
            kwargs=job_create.kwargs,
            status="pending",
            queue=job_create.queue,
            priority=job_create.priority,
            max_retries=job_create.max_retries,
            retry_count=0,
            timeout=job_create.timeout,
            created_at=datetime.utcnow()
        )
        
        # Save to database
        job = self.job_repo.create(job)
        
        # Add to Redis stream
        job_data = {
            "id": job.id,
            "task_name": job.task_name,
            "args": job.args,
            "kwargs": job.kwargs,
            "queue": job.queue,
            "priority": job.priority,
            "timeout": job.timeout,
            "idempotency_key": idempotency_key
        }
        
        self.redis_streams.add_job(job_data)
        
        metrics.increment("jobs.submitted")
        logger.info(f"Job submitted: {job.id}")
        
        return job
        
    def get_job(self, job_id: str) -> JobEntity:
        """Get job by ID."""
        return self.job_repo.get_by_id(job_id)
        
    def list_jobs(
        self,
        queue: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[JobEntity]:
        """List jobs with filters."""
        return self.job_repo.list_jobs(queue=queue, status=status, limit=limit)
        
    def retry_job(self, job_id: str) -> JobEntity:
        """Retry failed job."""
        job = self.job_repo.get_by_id(job_id)
        
        if job.retry_count >= job.max_retries:
            raise ValueError("Job has exceeded max retries")
            
        # Update job status
        job = self.job_repo.update_status(job_id, "pending")
        
        # Re-add to queue
        job_data = {
            "id": job.id,
            "task_name": job.task_name,
            "args": job.args,
            "kwargs": job.kwargs,
            "queue": job.queue,
            "priority": job.priority,
            "timeout": job.timeout,
            "retry": True
        }
        
        self.redis_streams.add_job(job_data)
        
        metrics.increment("jobs.retried")
        logger.info(f"Job retried: {job.id}")
        
        return job
