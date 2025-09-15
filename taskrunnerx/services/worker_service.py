"""Worker service for job processing."""

import time
from datetime import datetime
from typing import Any, Dict, Optional

from ..adapters.redis_streams import RedisStreams
from ..domain.models import ExecutionResult
from ..storage.repo_jobs import JobRepository
from ..logging import get_logger
from ..metrics import metrics
from .executor import TaskExecutor

logger = get_logger(__name__)


class WorkerService:
    """Worker business logic."""
    
    def __init__(
        self,
        job_repo: JobRepository,
        redis_streams: RedisStreams,
        executor: TaskExecutor,
        worker_id: str
    ):
        self.job_repo = job_repo
        self.redis_streams = redis_streams
        self.executor = executor
        self.worker_id = worker_id
        
    def process_jobs(self) -> None:
        """Main worker loop."""
        logger.info(f"Worker {self.worker_id} started")
        
        # Create consumer group
        self.redis_streams.create_consumer_group(self.worker_id)
        
        while True:
            try:
                # Read jobs from stream
                jobs = self.redis_streams.read_jobs(self.worker_id)
                
                for message_id, job_data in jobs:
                    self._process_job(message_id, job_data)
                    
                # Claim abandoned jobs
                abandoned = self.redis_streams.claim_jobs(self.worker_id)
                for message_id, job_data in abandoned:
                    self._process_job(message_id, job_data, claimed=True)
                    
            except Exception as e:
                logger.error(f"Worker error: {e}")
                time.sleep(5)
                
    def _process_job(
        self,
        message_id: str,
        job_data: Dict[str, Any],
        claimed: bool = False
    ) -> None:
        """Process individual job."""
        job_id = job_data["id"]
        
        try:
            # Update job status to running
            self.job_repo.update_status(job_id, "running")
            
            start_time = time.time()
            
            # Execute task
            result = self.executor.execute(
                job_data["task_name"],
                job_data.get("args", {}),
                job_data.get("kwargs", {}),
                timeout=job_data.get("timeout", 300)
            )
            
            duration = time.time() - start_time
            
            if result.success:
                # Mark as completed
                self.job_repo.update_status(job_id, "completed", result=result.result)
                metrics.increment("jobs.completed")
                logger.info(f"Job completed: {job_id}")
            else:
                # Handle failure
                self._handle_job_failure(job_id, job_data, result.error)
                
            # Acknowledge message
            self.redis_streams.ack_job(message_id)
            
            # Record metrics
            metrics.timer("job.duration", duration)
            
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}")
            self._handle_job_failure(job_id, job_data, str(e))
            
    def _handle_job_failure(
        self,
        job_id: str,
        job_data: Dict[str, Any],
        error: str
    ) -> None:
        """Handle job failure with retry logic."""
        job = self.job_repo.get_by_id(job_id)
        
        if job.retry_count < job.max_retries:
            # Retry job
            self.job_repo.update_status(job_id, "retrying", error=error)
            
            # Re-add to queue with delay
            retry_job_data = job_data.copy()
            retry_job_data["retry_count"] = job.retry_count + 1
            
            self.redis_streams.add_job(retry_job_data)
            
            metrics.increment("jobs.retried")
            logger.info(f"Job retrying: {job_id}")
            
        else:
            # Move to failed
            self.job_repo.update_status(job_id, "failed", error=error)
            metrics.increment("jobs.failed")
            logger.error(f"Job failed: {job_id}")
