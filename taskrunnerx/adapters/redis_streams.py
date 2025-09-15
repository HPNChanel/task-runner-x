"""Redis Streams adapter for job queue."""

import json
from typing import Any, Dict, List, Optional, Tuple

import redis

from ..config import config
from ..logging import get_logger

logger = get_logger(__name__)


class RedisStreams:
    """Redis Streams job queue adapter."""
    
    def __init__(self, redis_url: str = config.REDIS_URL):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.stream_name = config.STREAM_NAME
        self.consumer_group = config.CONSUMER_GROUP
        
    def add_job(self, job_data: Dict[str, Any]) -> str:
        """Add job to stream."""
        message_id = self.redis.xadd(
            self.stream_name,
            {"job": json.dumps(job_data)}
        )
        logger.info(f"Added job to stream: {message_id}")
        return message_id
        
    def create_consumer_group(self, consumer_name: str) -> None:
        """Create consumer group if not exists."""
        try:
            self.redis.xgroup_create(
                self.stream_name,
                consumer_name,
                id="0",
                mkstream=True
            )
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
                
    def read_jobs(
        self,
        consumer_name: str,
        block: int = 1000,
        count: int = 1
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Read jobs from stream."""
        messages = self.redis.xreadgroup(
            self.consumer_group,
            consumer_name,
            {self.stream_name: ">"},
            count=count,
            block=block
        )
        
        jobs = []
        for stream_name, stream_messages in messages:
            for message_id, fields in stream_messages:
                job_data = json.loads(fields["job"])
                jobs.append((message_id, job_data))
                
        return jobs
        
    def ack_job(self, message_id: str) -> None:
        """Acknowledge job completion."""
        self.redis.xack(self.stream_name, self.consumer_group, message_id)
        logger.info(f"Acknowledged job: {message_id}")
        
    def claim_jobs(
        self,
        consumer_name: str,
        min_idle_time: int = 60000
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Claim abandoned jobs."""
        pending = self.redis.xpending_range(
            self.stream_name,
            self.consumer_group,
            min="-",
            max="+",
            count=10
        )
        
        if not pending:
            return []
            
        message_ids = [info["message_id"] for info in pending
                      if info["time_since_delivered"] > min_idle_time]
        
        if not message_ids:
            return []
            
        claimed = self.redis.xclaim(
            self.stream_name,
            self.consumer_group,
            consumer_name,
            min_idle_time,
            message_ids
        )
        
        jobs = []
        for message_id, fields in claimed:
            job_data = json.loads(fields["job"])
            jobs.append((message_id, job_data))
            
        logger.info(f"Claimed {len(jobs)} abandoned jobs")
        return jobs
