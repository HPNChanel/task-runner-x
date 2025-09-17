"""Worker for processing jobs."""

import time
from datetime import datetime
from typing import Any, Dict

from ..app.config import settings
from ..app.db import SessionLocal
from ..adapters.redis_streams import RedisStreams
from ..storage.repo_jobs import JobRepository
from ..services.executor import TaskExecutor
from ..logging import get_logger, setup_logging
from ..metrics import metrics

logger = get_logger(__name__)


class Worker:
    """Job processing worker."""
    
    def __init__(self, worker_id: str = None):
        self.worker_id = worker_id or settings.CONSUMER_NAME
        self.redis_streams = RedisStreams()
        self.executor = TaskExecutor()
        
    def run(self):
        """Start worker loop."""
        setup_logging()
        logger.info(f"Worker {self.worker_id} starting...")
        
        # Create consumer group
        self.redis_streams.create_consumer_group(self.worker_id)
        
        while True:
            try:
                # Get database session
                db = SessionLocal()
                job_repo = JobRepository(db)
                
                # Read jobs from stream
                jobs = self.redis_streams.read_jobs(self.worker_id)
                
                for message_id, job_data in jobs:
                    self._process_job(job_repo, message_id, job_data)
                    
                # Claim abandoned jobs
                abandoned = self.redis_streams.claim_jobs(self.worker_id)
                for message_id, job_data in abandoned:
                    self._process_job(job_repo, message_id, job_data, claimed=True)
                    
                db.close()
                
            except Exception as e:
                logger.error(f"Worker error: {e}")
                time.sleep(5)
                
    def _process_job(
        self,
        job_repo: JobRepository,
        message_id: str,
        job_data: Dict[str, Any],
        claimed: bool = False
    ):
        """Process individual job."""
        job_id = job_data["id"]
        
        try:
            # Update job status to running
            job_repo.update_status(job_id, "running")
            
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
                job_repo.update_status(job_id, "completed", result=result.result)
                metrics.increment("jobs.completed")
                logger.info(f"Job completed: {job_id}")
            else:
                job_repo.update_status(job_id, "failed", error=result.error)
                metrics.increment("jobs.failed")
                logger.error(f"Job failed: {job_id}")
                
            # Acknowledge message
            self.redis_streams.ack_job(message_id)
            metrics.timer("job.duration", duration)
            
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}")
            job_repo.update_status(job_id, "failed", error=str(e))


if __name__ == "__main__":
    worker = Worker()
    worker.run()
